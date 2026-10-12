#!/usr/bin/env python3
"""Audit manually reviewed, private listing-event notes; never scrape listing sites.

Run with the three frozen inputs from the designated research archive. Public
outputs contain original QA and source links only; row-level fields stay private.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Empty output requires an explicit schema")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def delta_percent(closed, asking):
    """Property negotiation difference, not a market return."""
    return float((Decimal(closed) / Decimal(asking) - 1) * 100)


def run(args):
    checks = []

    def check(name, condition):
        checks.append({"check": name, "passed": bool(condition)})
        if not condition:
            raise ValueError("Audit failed: " + name)

    paths = {"pilot_notes": args.pilot_notes, "history_notes": args.history_notes,
             "source_map": args.source_map}
    manifest = read_json(args.manifest)
    for name, path in paths.items():
        raw = Path(path).read_bytes()
        spec = manifest["inputs"][name]
        check("frozen_bytes_" + name, len(raw) == spec["bytes"])
        check("frozen_sha256_" + name, hashlib.sha256(raw).hexdigest() == spec["sha256"])

    pilot = read_json(args.pilot_notes)
    notes = read_json(args.history_notes)
    source_map = read_json(args.source_map)
    start, end = date.fromisoformat(notes["window_start"]), date.fromisoformat(notes["window_end"])
    records = {r["record_id"]: r for r in pilot["records"] if r["transaction_type"] == "sale"}
    check("fixed_sale_cohort_25", len(records) == 25)
    check("history_covers_exact_frozen_cohort", set(records) == set(notes["cases"]))
    members = [m for g in notes["product_groups"] for m in g["members"]]
    check("groups_partition_cohort_once", len(members) == len(set(members)) == 25 and set(members) == set(records))
    group_map = {m: g for g in notes["product_groups"] for m in g["members"]}
    excluded_profile = set(notes["rules"]["stable_profile_exclusions"])
    excluded_price = set(notes["rules"]["price_material_conflict_exclusions"])
    event_types = {"sale_listed", "sale_relisted", "sale_price", "sale_removed",
                   "sale_expired", "sale_cancelled", "sale_pending", "sale_contingent",
                   "sale_closed", "reported_public_sale", "lease_listed", "lease_price",
                   "lease_removed", "lease_closed"}
    listing_events = {"sale_listed", "sale_relisted"}
    ask_events = listing_events | {"sale_price"}
    events, source_rows, summaries, leases = [], {}, [], []

    def source(rid, ref, fallback=None):
        found = source_map.get(ref)
        url = fallback or (found or {}).get("url")
        check(rid + "_source_" + ref, bool(url and url.startswith("https://")))
        source_rows[rid, url] = {
            "record_id": rid, "source_url": url, "retrieved_date": notes["as_of_local"],
            "access": "individual_page_or_search_field_review", "public_storage": "link_only",
            "upstream": "published_listing_or_third_party_record_claim_not_independent_deed",
        }
        return url

    def flatten(rid, blocks):
        rows = []
        for bi, b in enumerate(blocks):
            url = source(rid, b["ref"], b.get("source_url"))
            for ei, (dt, kind, amount) in enumerate(b["events"]):
                day = date.fromisoformat(dt)
                check(f"{rid}_event_{bi}_{ei}_type", kind in event_types)
                check(f"{rid}_event_{bi}_{ei}_not_future", day <= end)
                check(f"{rid}_event_{bi}_{ei}_amount", amount is None or (type(amount) is int and amount > 0))
                check(f"{rid}_event_{bi}_{ei}_boundary", day >= start or (rid == "T024" and dt == "2024-08-15"))
                rows.append({
                    "event_id": f"{rid}-B{bi+1:02d}-E{ei+1:02d}", "record_id": rid,
                    "date": dt, "event_type": kind, "amount": amount,
                    "amount_unit": "USD/month" if kind.startswith("lease_") else "USD",
                    "mls_or_channel_id": b["mls"], "canonical_for_calculation": b.get("canonical", True),
                    "window_role": "in_window" if start <= day <= end else "prior_context",
                    "source_ref": b["ref"], "source_url": url,
                })
        events.extend(rows)
        return rows

    for rid, r in sorted(records.items()):
        c = notes["cases"][rid]
        blocks = list(c["blocks"])
        if not any(e[1] == "sale_closed" for b in blocks if b.get("canonical", True) for e in b["events"]):
            blocks.append({"ref": r["source_ref"], "source_url": r["source_url"], "mls": r["mls_id"],
                           "events": [[r["close_date"], "sale_closed", r["amount"]]]})
        ev = flatten(rid, blocks)
        selected = [e for e in ev if e["canonical_for_calculation"]]
        closures = {(e["date"], e["amount"]) for e in selected if e["event_type"] == "sale_closed"}
        check(rid + "_same_baseline_close", closures == {(r["close_date"], r["amount"])})
        closed = date.fromisoformat(r["close_date"])
        check(rid + "_close_in_window", start <= closed <= end)
        listing = sorted([e for e in selected if e["event_type"] in listing_events and e["date"] <= r["close_date"]], key=lambda e: e["date"])
        asks = sorted([e for e in selected if e["event_type"] in ask_events and e["amount"] is not None and e["date"] <= r["close_date"]], key=lambda e: e["date"])
        current = [e for e in listing if e["mls_or_channel_id"] == r["mls_id"]]
        check(rid + "_observed_listing_and_current_mls", bool(listing and current and asks))
        first, last = asks[0], asks[-1]
        all_span = (closed - date.fromisoformat(listing[0]["date"])).days
        current_span = (closed - date.fromisoformat(current[0]["date"])).days
        relist_span = (closed - date.fromisoformat(listing[-1]["date"])).days
        check(rid + "_calendar_span_order", 0 <= relist_span <= current_span <= all_span)
        stable_profile = bool(r.get("target_filter_match")) and rid not in excluded_profile
        price_eligible = stable_profile and rid not in excluded_price
        first_delta = last_delta = None
        if rid not in excluded_price:
            first_delta = delta_percent(r["amount"], first["amount"])
            last_delta = delta_percent(r["amount"], last["amount"])
            for label, ask, calculated in [("first", first["amount"], first_delta), ("last", last["amount"], last_delta)]:
                rational = float((Fraction(r["amount"], ask) - 1) * 100)
                check(rid + "_independent_fraction_" + label, abs(calculated - rational) < 1e-9)
        check(rid + "_partial_not_complete", c["full_mls_history_verified"] is False)
        summaries.append({
            "record_id": rid, "address": r["address"], "community": r["community_claimed"],
            "group_id": group_map[rid]["group_id"], "bedrooms": r["bedrooms"],
            "living_area_sqft": r["living_area_sqft"], "year_built": r["year_built"],
            "close_date_mls": r["close_date"], "close_price_mls_baseline": r["amount"],
            "observed_first_listing_date": listing[0]["date"], "observed_first_ask": first["amount"],
            "current_mls_first_listing_date": current[0]["date"],
            "observed_last_ask_date": last["date"], "observed_last_ask": last["amount"],
            "first_listing_to_close_calendar_days": all_span,
            "current_mls_listing_to_close_calendar_days": current_span,
            "last_listing_or_relisting_to_close_calendar_days": relist_span,
            "closed_vs_first_observed_ask_pct": first_delta,
            "closed_vs_last_observed_ask_pct": last_delta,
            "named_sale_mls_count": len({e["mls_or_channel_id"] for e in selected if e["event_type"].startswith("sale_") and re.fullmatch(r"[A-Z]{2}\d{8}", e["mls_or_channel_id"])}),
            "stable_profile_candidate": stable_profile, "profile_and_price_candidate": price_eligible,
            "true_dom": None, "complete_mls_history_verified": False,
            "quality_match_verified": False, "flags": ";".join(c["flags"]), "notes": c["notes"],
        })

    for r in notes["new_leases"]:
        rid = r["record_id"]
        check(rid + "_lease_not_sale", r["transaction_type"] == "lease" and r["amount_unit"] == "USD/month")
        check(rid + "_profile", r["bedrooms"] == 3 and r["shared_wall_status"] == "no_common_walls_mls_reported")
        check(rid + "_scope", r["whole_home_scope"] == "whole_home_mls_description" and r["furnished"] == "Unfurnished_mls_reported" and r["lease_term_months"] == 12)
        check(rid + "_net_rent_unknown", r["effective_rent_usd_month"] is None and r["concessions"] is None and not r["signed_lease_verified"])
        ev = flatten(rid, r["blocks"])
        for ref in r["field_refs"]:
            source(rid, ref)
        closures = {(e["date"], e["amount"]) for e in ev if e["event_type"] == "lease_closed"}
        check(rid + "_closure_event", closures == {(r["close_date"], r["amount"])})
        check(rid + "_close_in_window", start <= date.fromisoformat(r["close_date"]) <= end)
        asks = sorted([e for e in ev if e["event_type"] in {"lease_listed", "lease_price"}], key=lambda e: e["date"])
        check(rid + "_asking_precedes_close", bool(asks) and max(e["date"] for e in asks) <= r["close_date"])
        leases.append({
            "record_id": rid, "address": r["address"], "community": r["community_claimed"],
            "mls_id": r["mls_id"], "bedrooms": 3, "living_area_sqft": r["living_area_sqft"],
            "year_built": r["year_built"], "close_date_mls": r["close_date"],
            "closed_rent_usd_month": r["amount"], "first_observed_ask": asks[0]["amount"],
            "first_observed_listing_date": asks[0]["date"], "last_observed_ask": asks[-1]["amount"],
            "calendar_days_first_listing_to_reported_close": (date.fromisoformat(r["close_date"]) - date.fromisoformat(asks[0]["date"])).days,
            "lease_term_months_reported": 12, "furnished": "Unfurnished_mls_reported",
            "shared_walls": r["shared_wall_status"], "geography_basis": r["geography_verification"],
            "effective_net_rent": None, "signed_lease_verified": False,
            "flags": ";".join(r["flags"]), "notes": r["notes"],
        })

    for x in notes["excluded_lease_candidates"]:
        for ref in x["refs"]:
            source(x["record_id"], ref)
    check("four_new_three_bed_leases", len(leases) == 4)
    check("unique_new_leases", len({r["record_id"] for r in leases}) == 4 and not ({r["record_id"] for r in leases} & {r["record_id"] for r in pilot["records"]}))
    check("unique_event_rows", len({e["event_id"] for e in events}) == len(events))
    check("21_stable_profile_candidates", sum(r["stable_profile_candidate"] for r in summaries) == 21)
    check("20_profile_and_price_candidates", sum(r["profile_and_price_candidate"] for r in summaries) == 20)
    check("all_actual_dom_remain_missing", all(r["true_dom"] is None for r in summaries))
    check("no_quality_index_claim", all(not r["quality_match_verified"] for r in summaries))
    byid = {r["record_id"]: r for r in summaries}
    # Independent hand-calendar expectations for relisting resets and boundary handling.
    for rid, first_days, current_days in [("T007", 259, 27), ("T020", 118, 55), ("T021", 117, 18), ("T024", 277, 45)]:
        check(rid + "_calendar_reference", (byid[rid]["first_listing_to_close_calendar_days"], byid[rid]["current_mls_listing_to_close_calendar_days"]) == (first_days, current_days))
    check("price_conflict_suppresses_ratios", byid["T003"]["closed_vs_first_observed_ask_pct"] is None and byid["T003"]["closed_vs_last_observed_ask_pct"] is None)
    check("new_bed_conflict_excluded", not byid["T021"]["stable_profile_candidate"])
    check("public_record_claims_not_extra_closes", len(summaries) == 25)
    check("one_prior_boundary_event", sum(e["window_role"] == "prior_context" for e in events) == 1)

    quarters = Counter(r["close_date_mls"][:4] + "Q" + str((int(r["close_date_mls"][5:7]) - 1) // 3 + 1) for r in summaries)
    metrics = {
        "sale_cases": len(summaries), "candidate_product_strata": len(notes["product_groups"]),
        "stable_profile_candidates": 21, "profile_and_price_candidates": 20,
        "event_rows": len(events), "sale_cohort_event_rows": sum(e["record_id"].startswith("T") for e in events),
        "in_window_event_rows": sum(e["window_role"] == "in_window" for e in events),
        "prior_context_event_rows": 1, "event_type_counts": dict(sorted(Counter(e["event_type"] for e in events).items())),
        "sale_cases_by_observed_close_quarter": dict(sorted(quarters.items())),
        "quarter_count_interpretation": "fixed_nonrandom_sample_only_not_market_volume",
        "sale_date_min": min(r["close_date_mls"] for r in summaries), "sale_date_max": max(r["close_date_mls"] for r in summaries),
        "multiple_named_sale_mls_cases": sum(r["named_sale_mls_count"] > 1 for r in summaries),
        "new_three_bed_closed_leases": 4, "prior_four_bed_closed_leases": sum(r["transaction_type"] == "lease" for r in pilot["records"]),
        "excluded_lease_candidates": len(notes["excluded_lease_candidates"]),
        "complete_mls_history_verified": 0, "actual_contract_dom_verified": 0,
        "signed_new_leases_verified": 0, "effective_net_new_rents_verified": 0,
        "source_record_url_pairs": len(source_rows), "distinct_source_urls": len({u for _, u in source_rows}),
    }
    qa = {"version": notes["version"], "as_of_local": notes["as_of_local"],
          "timezone": notes["retrieval_timezone"], "window_start": start.isoformat(), "window_end": end.isoformat(),
          "status": "passed_with_source_and_coverage_limitations", "metrics": metrics,
          "checks_passed": len(checks), "checks_failed": 0,
          "independent_model_review_performed": False, "checks": checks}
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "listing_events.csv", events)
    write_csv(out / "sale_case_summary.csv", summaries)
    write_csv(out / "three_bed_closed_leases.csv", leases)
    write_json(out / "reviewed_history.json", {"notes": notes, "sale_summaries": summaries, "leases": leases, "metrics": metrics, "sources": list(source_rows.values())})
    write_json(out / "history_qa.json", qa)
    write_json(args.public_qa, qa)
    write_csv(args.source_index, [source_rows[k] for k in sorted(source_rows)])
    print(json.dumps({"status": qa["status"], "checks_passed": len(checks), "metrics": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ["pilot-notes", "history-notes", "source-map", "manifest", "outdir", "public-qa", "source-index"]:
        p.add_argument("--" + name, required=True, type=Path)
    run(p.parse_args())
