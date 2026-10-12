"""Audit manually reviewed property notes and frozen municipal address snapshots.

No listing-site crawler is provided. The notes and municipal geometries are kept
in the designated research archive; public outputs contain QA and source links.
This audits field feasibility, not title, a physical inspection, or market value.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

from pyproj import Transformer
from shapely import make_valid, transform
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union


COMMUNITY_ID = {"Stonegate": "9.4", "Reserve": "1.3", "Eastwood": "5.2", "Portola Springs": "6.1"}
UNKNOWN = {None, "", "unverified", "not_available", "not_verified", "not_acquired"}
SALE_FIELDS = ["close_date", "amount", "bedrooms", "living_area_sqft", "year_built", "mls_property_subtype", "shared_wall_status"]


def fingerprint(path):
    b = path.read_bytes()
    return {"filename": path.name, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def normal_address(address):
    return " ".join(address.upper().split()).replace(" ROAD", " RD").replace(" LANE", " LN").replace(" TRAIL", " TRL").replace(" PLACE", " PL")


def verify_snapshots(directory, download=False):
    manifest = json.loads((directory / "official_query_manifest.json").read_text())
    for item in manifest:
        path = directory / item["filename"]
        if not path.exists() and download:
            with urlopen(item["url"], timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError("Source changed; restore frozen archive or register a new vintage: " + path.name)
            path.write_bytes(data)
        fp = fingerprint(path)
        if fp["sha256"] != item["sha256"] or fp["bytes"] != item["bytes"]:
            raise ValueError("Frozen municipal source fingerprint mismatch: " + path.name)
    return manifest


def run(args):
    pack = json.loads(args.notes.read_text())
    rows = pack["records"]
    manifest = verify_snapshots(args.official_dir, args.download_official)
    args.outdir.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, passed):
        checks.append({"check": name, "pass": bool(passed)})

    sales = [r for r in rows if r["transaction_type"] == "sale"]
    leases = [r for r in rows if r["transaction_type"] == "lease"]
    check("closed_sale_feasibility_count_20_to_30", 20 <= len(sales) <= 30)
    check("combined_trial_count_at_most_30", len(rows) <= 30)
    check("unique_record_ids", len({r["record_id"] for r in rows}) == len(rows))
    events = [(normal_address(r["address"]), r["transaction_type"], r["close_date"]) for r in rows]
    check("unique_address_type_event_dates", len(set(events)) == len(rows))
    check("no_sale_lease_identifier_overlap", not ({r["mls_id"] for r in sales} & {r["mls_id"] for r in leases}))
    check("at_least_three_communities", len({r["community_claimed"] for r in sales}) >= 3)
    manual_sales = [r for r in sales if r["manual_review"]]
    check("at_least_five_sale_source_reviews", len(manual_sales) >= 5)

    hoa_features = json.loads(args.base_hoa.read_text())["features"]
    hoa_features += json.loads((args.official_dir / "hoa_eastwood_portola.geojson").read_text())["features"]
    groups = {}
    invalid_hoa = 0
    for feature in hoa_features:
        geo = shape(feature["geometry"])
        invalid_hoa += not geo.is_valid
        groups.setdefault(str(feature["properties"]["MASTER_ID"]), []).append(make_valid(geo))
    masks = {key: unary_union(value) for key, value in groups.items()}
    point_transform = Transformer.from_crs(2230, 4326, always_xy=True)
    area_transform = Transformer.from_crs(4326, 26911, always_xy=True)
    metric_masks = {key: transform(value, area_transform.transform, interleaved=False) for key, value in masks.items()}
    address_features, building_features = [], []
    for stem in ["city_target_buildings", "city_124_imagination"]:
        address_features.extend(json.loads((args.official_dir / f"{stem}_layer19.json").read_text())["features"])
        building_features.extend(json.loads((args.official_dir / f"{stem}_layer1.json").read_text())["features"])
    addresses, buildings = {}, {}
    for f in address_features:
        a = f["attributes"]
        key = normal_address(a["ADDRESS"] + " " + a["NAME"])
        addresses.setdefault(key, []).append(a)
    for f in building_features:
        a = f["attributes"]
        # ArcGIS JSON returns rings rather than GeoJSON type/coordinates.
        # Even/odd ring containment preserves islands and interior holes.
        rings = [Polygon(ring) for ring in f["geometry"]["rings"]]
        footprint = rings[0]
        for ring in rings[1:]:
            footprint = footprint.symmetric_difference(ring)
        buildings.setdefault(a["BIN"], []).append(make_valid(footprint))

    geography = []
    for r in rows:
        rid = r["record_id"]
        check(rid + ":closed_reported_type", r["status"] == "MLS_closed_reported" and r["transaction_type"] in {"sale", "lease"})
        check(rid + ":positive_amount", r["amount"] > 0)
        check(rid + ":valid_bedrooms_area_year", r["bedrooms"] > 0 and r["living_area_sqft"] > 0 and 1800 <= r["year_built"] <= 2026)
        check(rid + ":dated_observation_window", date.fromisoformat(pack["window_start"]) <= date.fromisoformat(r["close_date"]) <= date.fromisoformat(pack["as_of_local"]))
        check(rid + ":linked_provenance", all(o["source_url"].startswith("https://") for o in r["source_observations"]))
        check(rid + ":title_not_inferred_from_mls", r["legal_property_type"] == "unverified" and r["legal_title_status"] == "not_verified")
        check(rid + ":missing_concession_not_zero", r["seller_concession"] is None)
        check(rid + ":recorded_loan_not_inferred", r["recorded_deed_status"] == "not_acquired")
        amount, area = Decimal(str(r["amount"])), Decimal(str(r["living_area_sqft"]))
        ratio = amount / area
        if r["transaction_type"] == "sale":
            r["sale_price_per_sqft_calculated"] = str(ratio.quantize(Decimal("0.01")))
            r["rent_per_sqft_month_calculated"] = ""
        else:
            r["sale_price_per_sqft_calculated"] = ""
            r["rent_per_sqft_month_calculated"] = str(ratio.quantize(Decimal("0.0001")))
        check(rid + ":unit_separated_price_ratio", not (r["sale_price_per_sqft_calculated"] and r["rent_per_sqft_month_calculated"]))
        fees = Decimal(0)
        for fee in r["hoa_components"]:
            factor = {"monthly": Decimal(1), "quarterly": Decimal(3), "annual": Decimal(12)}[fee["frequency"]]
            fees += Decimal(str(fee["amount"])) / factor
        r["hoa_monthly_equivalent"] = str(fees.quantize(Decimal("0.01"))) if r["hoa_components"] else ""
        candidate = r["transaction_type"] == "sale" and r["bedrooms"] == 4 and r["living_area_sqft"] >= 1650 and r["year_built"] >= 2010 and r["shared_wall_status"] == "no_common_walls_mls_reported"
        check(rid + ":target_filter_recalculated", candidate == r["target_filter_match"])
        check(rid + ":conflicted_profile_not_stable", r["stable_profile_candidate"] == (candidate and "material_bedroom_and_area_conflict" not in r["issues"]))

        if r["city"] != "Irvine":
            geography.append({"record_id": rid, "geography_status": "broker_community_description_only", "city": r["city"], "community": r["community_claimed"]})
            continue
        a = addresses.get(normal_address(r["address"]), [])
        check(rid + ":unique_municipal_address", len(a) == 1)
        if len(a) != 1:
            continue
        a = a[0]
        lon, lat = point_transform.transform(a["X_COORD"], a["Y_COORD"])
        pt = Point(lon, lat)
        matching = [k for k, v in masks.items() if v.covers(pt)]
        expected = COMMUNITY_ID[r["community_claimed"]]
        check(rid + ":hoa_research_mask_match", matching == [expected])
        footprint = unary_union(buildings.get(a["BIN"], []))
        metric_point = transform(pt, area_transform.transform, interleaved=False)
        distance = transform(footprint, area_transform.transform, interleaved=False).distance(metric_point) if not footprint.is_empty else None
        check(rid + ":address_point_building_agreement", distance is not None and distance <= 1)
        geography.append({"record_id": rid, "geography_status": "official_address_point_in_frozen_hoa_mask", "city": r["city"], "community": r["community_claimed"], "master_id": expected, "municipal_bin": a["BIN"], "longitude": lon, "latitude": lat, "boundary_distance_m": metric_masks[expected].boundary.distance(metric_point), "address_point_to_footprint_m": distance, "legal_boundary_verified": False})

    # Independently reviewed anchors stay with the personal notes, not in code.
    lookup = {r["record_id"]: r for r in rows}
    for anchor in pack["review_assertions"]:
        check(anchor["check"], lookup[anchor["record_id"]][anchor["field"]] == anchor["expected"])

    sale_coverage = {field: {"observed": sum(r[field] not in UNKNOWN for r in sales), "denominator": len(sales), "basis": "reported_field_not_document_certification"} for field in SALE_FIELDS}
    sale_coverage.update({
        "hoa_monthly_equivalent": {"observed": sum(bool(r["hoa_components"]) for r in sales), "denominator": len(sales)},
        "buyer_specific_mls_financing": {"observed": sum(r["buyer_financing_mls"] is not None for r in sales), "denominator": len(sales)},
        "legal_title_verified": {"observed": 0, "denominator": len(sales)},
        "recorded_deed_or_loan_verified": {"observed": 0, "denominator": len(sales)},
        "actual_contract_date": {"observed": 0, "denominator": len(sales)},
        "complete_listing_history": {"observed": 0, "denominator": len(sales)},
        "actual_seller_concession": {"observed": 0, "denominator": len(sales)},
        "verified_mello_roos_bill": {"observed": 0, "denominator": len(sales)},
    })
    qa = {
        "version": pack["version"], "status": "field_feasibility_pilot_with_unresolved_items",
        "as_of_local": pack["as_of_local"], "search_window_start": pack["window_start"],
        "observed_sale_date_range": [min(r["close_date"] for r in sales), max(r["close_date"] for r in sales)],
        "closed_sales_mls_reported": len(sales), "closed_leases_mls_reported": len(leases),
        "communities": dict(Counter(r["community_claimed"] for r in sales)),
        "sale_source_reviews": len(manual_sales), "lease_source_reviews": sum(bool(r["manual_review"]) for r in leases),
        "human_third_party_review_or_site_inspection": False, "second_model_review": False,
        "reported_target_filter_matches": sum(r["target_filter_match"] for r in sales),
        "stable_reported_profile_candidates": sum(r["stable_profile_candidate"] for r in sales),
        "verified_purchase_ready_properties": 0,
        "official_geography_records": sum(g["geography_status"].startswith("official") for g in geography),
        "official_geography_unique_addresses": len(addresses), "broker_only_geography_records": sum(g["geography_status"].startswith("broker") for g in geography),
        "hoa_geometries_repaired_before_point_checks": invalid_hoa,
        "sale_field_coverage": sale_coverage,
        "issues_by_record_id": {r["record_id"]: r["issues"] for r in rows if r["issues"]},
        "checks": checks, "checks_passed": sum(c["pass"] for c in checks), "checks_failed": sum(not c["pass"] for c in checks),
        "input_fingerprints": [fingerprint(args.notes), fingerprint(args.base_hoa)] + [{k: x[k] for k in ["filename", "bytes", "sha256"]} for x in manifest],
        "publication": "source_links_and_original_QA_only; individual_listing_fields_remain_in_personal_research_archive",
        "limitations": ["Syndicated pages often share CRMLS; agreement is not independent confirmation.", "MLS closed date differs from recorded document dates; no deed or escrow file acquired.", "HOA polygons are research coverage masks, not legal village or ownership certification.", "Purposive feasibility sample cannot identify community price trends, DOM, cash share, or buyer motives.", "Missing financing or concession is not zero; seller acceptable terms are not buyer financing.", "No three-bedroom closed-lease baseline or effective rent was verified."],
    }
    args.public_qa.parent.mkdir(parents=True, exist_ok=True)
    args.public_qa.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n")
    (args.outdir / "pilot_enriched.json").write_text(json.dumps({**pack, "records": rows, "geography": geography}, ensure_ascii=False, indent=2) + "\n")
    flat = [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in r.items()} for r in rows]
    write_csv(args.outdir / "transaction_pilot.csv", flat, list(flat[0]))
    write_csv(args.outdir / "transaction_geography.csv", geography, sorted({k for g in geography for k in g}))
    write_csv(args.outdir / "manual_source_reviews.csv", [{"record_id": r["record_id"], "transaction_type": r["transaction_type"], **r["manual_review"]} for r in rows if r["manual_review"]], ["record_id", "transaction_type", "reviewer", "date", "status", "notes", "onsite_inspection", "title_or_escrow_documents_verified"])
    source_rows, seen = [], set()
    for r in rows:
        for o in r["source_observations"]:
            key = (r["record_id"], o["source_url"])
            if key in seen:
                continue
            seen.add(key)
            source_rows.append({"record_id": r["record_id"], "source_url": o["source_url"], "retrieved_date": pack["as_of_local"], "access": o["access"], "public_storage": "link_only", "upstream": o.get("upstream", "third_party_record_claim_or_published_page")})
    write_csv(args.source_index, source_rows, ["record_id", "source_url", "retrieved_date", "access", "public_storage", "upstream"])
    print(json.dumps({"sale_records": len(sales), "lease_records": len(leases), "source_reviews": len(manual_sales), "official_geography_records": qa["official_geography_records"], "checks_passed": qa["checks_passed"], "checks_failed": qa["checks_failed"]}, ensure_ascii=False))
    return 1 if qa["checks_failed"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--official-dir", type=Path, required=True)
    parser.add_argument("--base-hoa", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--public-qa", type=Path, required=True)
    parser.add_argument("--source-index", type=Path, required=True)
    parser.add_argument("--download-official", action="store_true", help="Restore only explicitly frozen official query responses; fail if bytes changed.")
    raise SystemExit(run(parser.parse_args()))
