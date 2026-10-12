"""Freeze public GIS snapshots and audit community/ACS spatial correspondence.

HOA polygons are operational coverage masks, not certified legal village limits.
Area shares are spatial diagnostics only: NEVER household/income weights.
Raw municipal geometry and detailed overlay maps stay in data/raw (private archive).
"""
import argparse
import csv
import hashlib
import json
import platform
import urllib.request
from pathlib import Path

import pyproj
import shapely
from pyproj import Geod, Transformer
from shapely import make_valid, transform, union_all
from shapely.geometry import Point, shape, mapping

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/community'
MASTER = {'9.4': 'Stonegate', '9.3': 'Stonegate East',
          '1.1': 'Groves at Orchard Hills', '1.2': 'Orchard Hills Village II',
          '1.3': 'Reserve at Orchard Hills'}
TARGET_TRACTS = {'06059052429', '06059052437'}
CRS = 'EPSG:26911'  # NAD83 / UTM zone 11N, metres


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def acquire(download=False):
    manifest = json.loads((ROOT / 'data/community_source_manifest.json').read_text())
    RAW.mkdir(parents=True, exist_ok=True)
    for rec in manifest['files']:
        path = RAW / rec['filename']
        if not path.exists():
            if not download:
                raise FileNotFoundError(f'{path}; restore archive or use --download')
            with urllib.request.urlopen(rec['url'], timeout=120) as r:
                data = r.read()
            assert hashlib.sha256(data).hexdigest() == rec['sha256'], (
                rec['filename'], 'source changed; register new vintage, do not silently replace')
            path.write_bytes(data)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == rec['sha256'], rec['filename']
    return manifest


def features(name):
    obj = json.loads((RAW / name).read_text())
    assert not obj.get('error') and not obj.get('exceededTransferLimit'), name
    assert obj['type'] == 'FeatureCollection'
    return obj['features']


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--download', action='store_true')
    args = ap.parse_args(); manifest = acquire(args.download)
    tf = Transformer.from_crs(4326, CRS, always_xy=True)
    repairs = []

    def project(f, source):
        original = shape(f['geometry'])
        fixed = make_valid(original)
        before = transform(original, tf.transform, interleaved=False)
        after = transform(fixed, tf.transform, interleaved=False)
        if not original.is_valid:
            repairs.append(dict(source=source, object_id=f['properties'].get('OBJECTID',f['properties'].get('GEOID')),
                                reason=shapely.is_valid_reason(original),
                                area_before_m2=before.area, area_after_m2=after.area,
                                area_change_m2=after.area-before.area,
                                method='shapely.make_valid; no buffer/simplification'))
        assert after.is_valid
        assert not after.is_empty
        return after

    h = features('hoa_targets.geojson')
    assert len(h) == 17
    assert len({f['properties']['OBJECTID'] for f in h}) == len(h)
    communities = {}
    source_records = []
    for mid, name in MASTER.items():
        ff = [f for f in h if f['properties']['MASTER_ID'] == mid]
        assert ff and all(name.split(' at ')[0].lower() in f['properties']['MASTER_HOA'].lower()
                          or mid == '1.2' for f in ff)
        gs = [project(f, 'HOA') for f in ff]
        u = union_all(gs)
        communities[name] = u
        dates = sorted({f['properties']['EditDate'] for f in ff})
        source_records.append(dict(community=name, boundary_kind='municipal_HOA_coverage_mask',
            master_id=mid, object_ids=';'.join(str(f['properties']['OBJECTID']) for f in ff),
            features=len(ff), union_area_ha=u.area/10000,
            sum_minus_union_area_m2=sum(g.area for g in gs)-u.area,
            edit_timestamp_min_ms=dates[0], edit_timestamp_max_ms=dates[-1],
            status='frozen_operational_mask;not_certified_legal_or_full_market_boundary',
            population_weighting='prohibited_without_validated_residential_allocation',
            source_id='SRC-097'))
    pa = features('pa_1_9.geojson')
    for f in pa:
        name = 'PA' + str(f['properties']['PLANAREA'])
        communities[name] = project(f, 'PA')
        source_records.append(dict(community=name, boundary_kind='municipal_planning_area',
            master_id='', object_ids=str(f['properties']['OBJECTID']), features=1,
            union_area_ha=communities[name].area/10000, sum_minus_union_area_m2=0,
            edit_timestamp_min_ms=1661376854632, edit_timestamp_max_ms=1661376854632,
            status='2022_data_edit;2021_description;context_not_market_village',
            population_weighting='prohibited',source_id='SRC-098'))
    tc = features('oc_tracts_2024.geojson')
    assert len(tc) == 614 and len({f['properties']['GEOID'] for f in tc}) == 614
    tract = {f['properties']['GEOID']: project(f, 'ACS2024_tract') for f in tc}
    assert all(g.startswith('06059') and len(g)==11 for g in tract)
    bgs = features('target_bgs_2024.geojson')
    assert len(bgs)==9
    bg = {f['properties']['GEOID']: project(f, 'ACS2024_BG') for f in bgs}
    blocks = features('target_blocks_2020.geojson')
    assert len(blocks)==195
    assert len({f['properties']['GEOID'] for f in blocks})==195
    assert all(len(f['properties']['GEOID'])==15 and
               f['properties']['GEOID'][:11] in TARGET_TRACTS and
               f['properties']['GEOID'][11]==f['properties']['BLKGRP']
               for f in blocks)
    b20 = [(f['properties'], project(f, 'Census2020_block')) for f in blocks]
    t20 = features('tracts_2020_targets.geojson')
    checks = []
    def check(name, ok, **detail):
        checks.append(dict(check=name,status='pass' if ok else 'fail',**detail))
        assert ok, (name,detail)

    for f in t20:
        gid=f['properties']['GEOID']; g20=project(f,'Census2020_tract')
        selected=[(p,g) for p,g in b20 if p['GEOID'][:11]==gid]
        for field in ['HU100','POP100']:
            s=sum(p[field] for p,g in selected)
            check('block_sum_equals_2020_tract_'+field,s==f['properties'][field],geoid=gid,
                  block_sum=s,tract_published=f['properties'][field])
        ub=union_all([g for p,g in selected])
        delta=ub.symmetric_difference(g20).area
        check('block_union_equals_2020_tract',delta<1,geoid=gid,symmetric_difference_m2=delta)
        delta24=g20.symmetric_difference(tract[gid]).area
        check('2020_vs_ACS2024_tract_boundary',delta24/g20.area<1e-5,geoid=gid,
              symmetric_difference_m2=delta24,relative_difference=delta24/g20.area)
        ubg=union_all([g for k,g in bg.items() if k[:11]==gid])
        delta_bg=ubg.symmetric_difference(tract[gid]).area
        check('ACS2024_BG_union_equals_tract',delta_bg<1,geoid=gid,symmetric_difference_m2=delta_bg)

    rows=[]
    for name,c in communities.items():
        for level,geoms in [('tract',tract),('block_group',bg)]:
            total=0
            for gid,g in geoms.items():
                a=c.intersection(g).area
                if a<=1: continue  # retain all intersections larger than 1 sq metre
                total+=a
                rows.append(dict(community=name,census_level=level,census_geoid=gid,
                    intersection_area_m2=a,community_mask_area_m2=c.area,census_polygon_area_m2=g.area,
                    share_of_community_area=a/c.area,share_of_census_area=a/g.area,
                    relationship='partial;area_not_population_weight',
                    geometry_vintage='2020_tract_BG_definitions_in_ACS2024_service',
                    projection=CRS,source_ids='SRC-097;SRC-098;SRC-099;SRC-100'))
            if level=='tract':check('county_tracts_cover_mask',abs(total-c.area)<5,
                                    community=name,uncovered_m2=c.area-total)
    # Independent area check: ellipsoidal geodesic area of WGS84 geometries,
    # distinct from UTM planar area. This checks projection, not source truth.
    geod=Geod(ellps='GRS80'); area_checks=[]
    for f in h:
        wg=make_valid(shape(f['geometry'])); projected=transform(wg,tf.transform,interleaved=False)
        def geodarea(g):
            if g.geom_type=='Polygon':
                out=abs(geod.polygon_area_perimeter(*g.exterior.xy)[0])
                return out-sum(abs(geod.polygon_area_perimeter(*ring.xy)[0]) for ring in g.interiors)
            return sum(geodarea(x) for x in g.geoms if x.geom_type in ['Polygon','MultiPolygon'])
        ga=geodarea(wg); rd=abs(projected.area-ga)/ga
        check('UTM_vs_ellipsoidal_area',rd<0.001,object_id=f['properties']['OBJECTID'],relative_difference=rd)
        area_checks.append(dict(object_id=f['properties']['OBJECTID'],geodesic_m2=ga,UTM_m2=projected.area))

    # Census internal points are NOT house addresses. Record ambiguity rather
    # than applying their 2020 counts as weights to 2020-24 ACS income/tenure.
    block_rows=[]
    for name,c in communities.items():
        if name.startswith('PA'):continue
        for p,g in b20:
            frac=c.intersection(g).area/g.area
            point=Point(tf.transform(float(p['INTPTLON']),float(p['INTPTLAT'])))
            block_rows.append(dict(community=name,block_geoid=p['GEOID'],bg_geoid=p['GEOID'][:12],
                census2020_population=p['POP100'],census2020_housing_units=p['HU100'],
                block_area_fraction_in_mask=frac,internal_point_in_mask=c.covers(point),
                area_majority_in_mask=frac>0.5,inside_with_10m_tolerance=c.buffer(10).covers(g),
                allocation_status='diagnostic_only;no_ACS_weighting',source_ids='SRC-097;SRC-101'))
    summaries=[]
    for name in MASTER.values():
        for gid in sorted(bg):
            rr=[r for r in block_rows if r['community']==name and r['bg_geoid']==gid]
            summaries.append(dict(community=name,bg_geoid=gid,blocks=len(rr),
                total_2020_housing_units=sum(r['census2020_housing_units'] for r in rr),
                housing_internal_point_in_mask=sum(r['census2020_housing_units'] for r in rr if r['internal_point_in_mask']),
                housing_area_majority_in_mask=sum(r['census2020_housing_units'] for r in rr if r['area_majority_in_mask']),
                housing_with_any_overlap=sum(r['census2020_housing_units'] for r in rr if r['block_area_fraction_in_mask']>1e-6),
                housing_blocks_cross_mask=sum(1 for r in rr if r['census2020_housing_units']>0 and 1e-6<r['block_area_fraction_in_mask']<1-1e-6),
                note='housing_units_not_households;2020_location_audit_not_current_allocation'))
    for a in MASTER.values():
        for b in MASTER.values():
            if a<b:
                inter=communities[a].intersection(communities[b]).area
                smaller=min(communities[a].area,communities[b].area)
                check('cross_HOA_overlap_below_10m2_and_0.001pct',inter<10 and inter/smaller<0.00001,
                      first=a,second=b,overlap_m2=inter,
                      note='Positive seam overlap retained; this is not proof of disjoint legal boundaries')
    for r in repairs:
        check('repair_preserves_area',abs(r['area_change_m2'])<1,source=r['source'],object_id=r['object_id'],delta_m2=r['area_change_m2'])
    write_csv(ROOT/'data/clean/community_boundary_registry.csv',source_records)
    write_csv(ROOT/'data/clean/community_census_crosswalk.csv',rows)
    write_csv(ROOT/'data/clean/community_block_diagnostics.csv',block_rows)
    write_csv(ROOT/'data/clean/community_bg_housing_audit.csv',summaries)
    # Census geometry is public-domain federal data. No municipal polygons here.
    fc=dict(type='FeatureCollection',features=[f for f in tc if f['properties']['GEOID'] in TARGET_TRACTS]+bgs)
    (ROOT/'data/clean/community_census_geometries.geojson').write_text(json.dumps(fc,separators=(',',':'))+'\n')
    qa=dict(status='pass',checks=checks,repairs=repairs,source_snapshots=len(manifest['files']),
            tract_count=len(tc),target_BG_count=len(bg),block_count=len(blocks),
            crosswalk_rows=len(rows),block_diagnostic_rows=len(block_rows),
            projection=CRS,area_unit='square_metres',intersection_floor_m2=1,
            environment=dict(python=platform.python_version(),shapely=shapely.__version__,pyproj=pyproj.__version__),
            inference_limit='HOA masks incomplete as legal village limits; census area shares never population weights')
    (ROOT/'qa/community_geography_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k not in ['checks','repairs']},ensure_ascii=False))
    print('Checks:',len(checks),'repairs:',len(repairs))


if __name__=='__main__':main()
