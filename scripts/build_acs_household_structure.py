"""Build a traceable ACS household baseline from official bulk files, without API keys.

2024 5-year tables are the common four-city window; 2024 1-year is separate.
The manifest freezes full decompressed source SHA-256 values. Raw bytes are kept
under data/raw and excluded from publication. Derived MOEs are approximations,
not replicate-weight estimates; neither sampling MOE nor QA identifies causality.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF'
TABLES = ['B01001', 'B01002', 'B11001', 'B11005', 'B25003', 'B25007',
          'B25115', 'B19001', 'B19013', 'B25118', 'B25119', 'B07001',
          'B07010', 'B07011']
GEOS = {'0500000US06059': 'Orange County', '1600000US0636770': 'Irvine',
        '1600000US0639496': 'Lake Forest', '1600000US0680854': 'Tustin',
        '1600000US0600947': 'Aliso Viejo'}
RETRIEVED = '2026-10-11'


def dump_csv(path, rows):
    assert rows
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def load_source(raw, filename):
    return gzip.open(raw / (filename + '.gz'), 'rt', encoding='utf-8-sig', newline='')


def numeric(value):
    try:
        n = float(value)
        return n if n >= 0 else None
    except ValueError:
        return None


def margin_numeric(value):
    # Official Census guidance explicitly permits zero sampling MOE for this
    # controlled-estimate sentinel; it is not an unavailable data cell.
    return 0.0 if value == '-555555555' else numeric(value)


def acquire(raw, filename, url, expected, download):
    p = raw / (filename + '.gz')
    if not p.exists():
        if not download:
            raise FileNotFoundError(f'{p}; rerun with --download')
        tmp = p.with_suffix('.gz.part')
        try:
            with urllib.request.urlopen(url, timeout=90) as r, gzip.open(tmp, 'wb') as out:
                ctype = r.headers.get('Content-Type', '')
                if 'html' in ctype.lower() and not filename.endswith('.html'):
                    raise ValueError(f'{filename}: unexpected HTML response')
                while True:
                    block = r.read(1024 * 1024)
                    if not block:
                        break
                    out.write(block)
            tmp.replace(p)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
    h = hashlib.sha256()
    size = 0
    with gzip.open(p, 'rb') as f:
        while block := f.read(1024 * 1024):
            h.update(block)
            size += len(block)
    digest = h.hexdigest()
    if expected and expected['sha256'] != digest:
        raise ValueError(f'{filename}: source changed; register the new vintage explicitly')
    result = dict(filename=filename, url=url, sha256=digest, source_bytes=size,
                  archive_bytes=p.stat().st_size, retrieved_date=RETRIEVED)
    if expected and expected.get('source_id'):
        result['source_id'] = expected['source_id']
    return result


def labels(raw, product):
    with load_source(raw, f'ACS2024{product}_Table_Shells.txt') as f:
        allrows = list(csv.DictReader(f, delimiter='|'))
    out = {}
    stacks = {}
    for r in allrows:
        if r['Table ID'] not in TABLES or not r['Unique ID']:
            continue
        tb = r['Table ID']
        indent = int(float(r['Indent']))
        stack = stacks.setdefault(tb, {})
        stack[indent] = r['Label']
        for key in list(stack):
            if key > indent:
                del stack[key]
        out[r['Unique ID']] = dict(label=' > '.join(stack[k] for k in sorted(stack)),
                                  table_title=r['Title'], universe=r['Universe'])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--download', action='store_true')
    ap.add_argument('--raw-dir', type=Path, default=ROOT / 'data/raw/acs')
    args = ap.parse_args()
    raw = args.raw_dir
    raw.mkdir(parents=True, exist_ok=True)
    mp = ROOT / 'data/acs_source_manifest.json'
    old = json.loads(mp.read_text()) if mp.exists() else {'files': []}
    expected = {r['filename']: r for r in old['files']}
    jobs = []
    for product in ['1YR', '5YR']:
        for filename in [f'ACS2024{product}_Table_Shells.txt', f'Geos2024{product}.txt']:
            jobs.append((filename, BASE + '/documentation/' + filename))
        for tb in TABLES:
            filename = f'acsdt{product[0]}y2024-{tb.lower()}.dat'
            jobs.append((filename, BASE + f'/data/{product}Data/' + filename))
    files = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(acquire, raw, fn, url, expected.get(fn), args.download): fn
                   for fn, url in jobs}
        for future in as_completed(futures):
            rec = future.result()
            files.append(rec)
            print(f"Source verified: {rec['filename']} ({rec['source_bytes']:,} bytes)", flush=True)
    files.sort(key=lambda r: r['filename'])
    mp.write_text(json.dumps(dict(retrieved_date=RETRIEVED, files=files), indent=2) + '\n')
    source_by_name = {r['filename']: r for r in files}
    records, rawrows, geo_records, coverage = [], [], [], []
    for product in ['1YR', '5YR']:
        dataset = f'ACS2024_{product}'
        metadata = labels(raw, product)
        geo_names = {}
        with load_source(raw, f'Geos2024{product}.txt') as f:
            for r in csv.DictReader(f, delimiter='|'):
                gid = r.get('GEO_ID', r.get('GEOID', ''))
                if gid in GEOS:
                    geo_names[gid] = r['NAME']
                    geo_records.append(dict(dataset=dataset, geo_id=gid, geography=GEOS[gid],
                                            official_name=r['NAME'], sumlevel=r['SUMLEVEL'],
                                            state=r['STATE'], place=r['PLACE'], county=r['COUNTY']))
        expected_geos = set(GEOS) - ({'1600000US0600947'} if product == '1YR' else set())
        assert set(geo_names) == expected_geos, (product, geo_names)
        for tb in TABLES:
            filename = f'acsdt{product[0]}y2024-{tb.lower()}.dat'
            seen = set()
            with load_source(raw, filename) as f:
                reader = csv.DictReader(f, delimiter='|')
                header = reader.fieldnames
                rawrows.append(dict(dataset=dataset, filename=filename, geo_id='HEADER',
                                    source_line=1, raw_line='|'.join(header)))
                for lineno, r in enumerate(reader, 2):
                    gid = r['GEO_ID']
                    if gid not in GEOS:
                        continue
                    assert gid not in seen
                    seen.add(gid)
                    rawrows.append(dict(dataset=dataset, filename=filename, geo_id=gid,
                                        source_line=lineno, raw_line='|'.join(r[k] for k in header)))
                    for k, val in r.items():
                        if not k.startswith(tb + '_E'):
                            continue
                        var = tb + '_' + k[-3:]
                        mraw = r[tb + '_M' + k[-3:]]
                        meta = metadata[var]
                        rec = dict(dataset=dataset, period_start='2024-01-01' if product == '1YR' else '2020-01-01',
                                   period_end='2024-12-31', release_date='2025-09-11' if product == '1YR' else '2026-01-29',
                                   geography=GEOS[gid], geo_id=gid, table_id=tb, variable_id=var,
                                   **meta, estimate=numeric(val), moe90=margin_numeric(mraw), estimate_raw=val,
                                   moe_raw=mraw, confidence_level=0.90,
                                   moe_status='controlled_sampling_moe_treated_as_zero' if mraw=='-555555555' else 'published' if numeric(mraw) is not None else 'unavailable_or_not_applicable',
                                   dollars_basis='2024_inflation_adjusted' if tb in ['B19001','B19013','B25118','B25119','B07010','B07011'] else '',
                                   source_filename=filename, source_line=lineno,
                                   source_id=source_by_name[filename].get('source_id', 'unregistered'),
                                   source_url=source_by_name[filename]['url'],
                                   source_sha256=source_by_name[filename]['sha256'], retrieved_date=RETRIEVED)
                        records.append(rec)
            assert seen <= expected_geos, (product, tb, seen)
            if not tb.startswith('B070'):
                assert seen == expected_geos, (product, tb, seen)
            coverage.append(dict(dataset=dataset, table_id=tb, geography_count=len(seen),
                                 expected_geography_count=len(expected_geos), status='pass' if seen == expected_geos else 'partial_official_availability',
                                 missing_geographies=';'.join(GEOS[g] for g in sorted(expected_geos-seen))))
    dump_csv(ROOT / 'data/clean/acs_2024_detailed.csv', records)
    assert len({(r['dataset'],r['geo_id'],r['variable_id']) for r in records})==len(records)
    dump_csv(ROOT / 'data/clean/acs_geography_crosscheck.csv', geo_records)
    dump_csv(raw / 'selected_source_rows.csv', rawrows)
    lookup = {(r['dataset'], r['geography'], r['variable_id']): r for r in records}
    derived, checks = [], []
    for product in ['1YR', '5YR']:
        ds = f'ACS2024_{product}'
        for geo in GEOS.values():
            if (ds, geo, 'B25003_001') not in lookup:
                continue

            def cell(tb, i):
                return lookup[ds, geo, f'{tb}_{i:03d}']

            def add(name, tb, indices, den=None, den_tb=None, note=''):
                rs = [cell(tb, i) for i in indices]
                if any(r['estimate'] is None for r in rs):
                    n = m = None
                else:
                    n = sum(r['estimate'] for r in rs)
                    m = math.sqrt(sum(r['moe90'] ** 2 for r in rs)) if all(r['moe90'] is not None for r in rs) else None
                method = 'published' if len(rs) == 1 else 'sum_RSS_MOE_approximation'
                d, dm = None, None
                if den is not None:
                    dr = cell(den_tb or tb, den)
                    d, dm = dr['estimate'], dr['moe90']
                    if n is not None and d:
                        p = n / d
                        if m is not None and dm is not None:
                            radicand = m * m - p * p * dm * dm
                            m = math.sqrt(radicand if radicand >= 0 else m*m + p*p*dm*dm) / d
                            method += '+subset_proportion_MOE' if radicand >= 0 else '+ratio_fallback_MOE'
                        else:
                            m = None
                        n = p
                    else:
                        n = m = None
                cv = (m/1.645/n) if n and m is not None else None
                r0 = rs[0]
                derived.append(dict(dataset=ds, period_start=r0['period_start'], period_end=r0['period_end'],
                                    geography=geo, geo_id=r0['geo_id'], metric=name, estimate=n, moe90=m,
                                    unit='fraction' if den is not None else ('2024_USD' if 'income' in name and 'median' in name else 'years' if name=='median_age' else 'persons' if name.startswith('population_') or name.startswith('movers_') else 'households'),
                                    source_variables='+'.join(r['variable_id'] for r in rs),
                                    denominator_variable=f'{den_tb or tb}_{den:03d}' if den else '',
                                    denominator_estimate=d, denominator_moe90=dm, moe_method=method,
                                    cv=cv, high_uncertainty=(cv is not None and cv > 0.30),
                                    note=note))

            def eq(name, tb, lhs, rhs):
                a=cell(tb,lhs)['estimate'];b=sum(cell(tb,i)['estimate'] for i in rhs)
                assert a==b,(ds,geo,name,a,b)
                checks.append(dict(dataset=ds,geography=geo,check=name,status='pass'))

            eq('family_nonfamily_total','B11001',1,[2,7])
            eq('presence_under18_total','B11005',1,[2,11])
            eq('owner_renter_total','B25003',1,[2,3])
            eq('population_sex_total','B01001',1,[2,26])
            eq('tenure_family_owner_renter','B25115',1,[2,15])
            eq('owner_age_total','B25007',2,list(range(3,12)))
            eq('renter_age_total','B25007',12,list(range(13,22)))
            eq('income_brackets_total','B19001',1,list(range(2,18)))
            eq('owner_income_total','B25118',2,list(range(3,14)))
            eq('renter_income_total','B25118',14,list(range(15,26)))
            if (ds,geo,'B07001_001') in lookup:
                eq('mobility_categories_total','B07001',1,[17,33,49,65,81])
            assert cell('B11001',1)['estimate']==cell('B25003',1)['estimate']==cell('B19001',1)['estimate']==cell('B25115',1)['estimate']
            assert cell('B25003',2)['estimate']==cell('B25115',2)['estimate']==cell('B25118',2)['estimate']
            assert cell('B25003',3)['estimate']==cell('B25115',15)['estimate']==cell('B25118',14)['estimate']
            checks.append(dict(dataset=ds,geography=geo,check='cross_table_household_total',status='pass'))
            assert sum(cell('B25115',i)['estimate'] for i in [18,22,25])<=cell('B25003',3)['estimate']
            for name in ['cross_table_owner_tenure','cross_table_renter_tenure','own_children_subset_of_renters']:
                checks.append(dict(dataset=ds,geography=geo,check=name,status='pass'))
            add('households_total','B25003',[1])
            add('family_share','B11001',[2],1)
            add('households_under18','B11005',[2])
            add('households_under18_share','B11005',[2],1,note='Any person under18; not necessarily own child')
            add('owner_households','B25003',[2])
            add('renter_households','B25003',[3])
            add('owner_share','B25003',[2],1)
            add('renter_share','B25003',[3],1)
            add('householders25_44','B25007',[4,5,14,15])
            add('householders25_44_share','B25007',[4,5,14,15],1)
            add('renter_householders25_44','B25007',[14,15])
            add('renter_householders25_44_share','B25007',[14,15],12)
            add('householders65plus_share','B25007',[9,10,11,19,20,21],1)
            add('owner_with_own_children','B25115',[5,9,12],note='Own child under18; excludes some grandchildren/foster relationships')
            add('renter_with_own_children','B25115',[18,22,25],note='Own child under18; not the same numerator as B11005')
            add('renter_with_own_children_share','B25115',[18,22,25],15)
            add('households_income200kplus','B19001',[17])
            add('households_income200kplus_share','B19001',[17],1,note='Open top bracket, no 300k/500k subdivision')
            add('households_income150kplus_share','B19001',[16,17],1)
            add('renter_income150kplus','B25118',[25])
            add('renter_income150kplus_share','B25118',[25],14,note='Joint tenure-income table; not 200k threshold')
            add('median_household_income','B19013',[1])
            add('median_owner_income','B25119',[2])
            add('median_renter_income','B25119',[3])
            add('median_age','B01002',[1])
            add('population_under18_share','B01001',[3,4,5,6,27,28,29,30],1)
            if (ds,geo,'B07001_001') in lookup:
                add('movers_within_county','B07001',[33],note='Persons age1+ currently resident, may include moves within same city')
                add('movers_other_CA_county','B07001',[49],note='Gross arrivals, no outbound subtraction')
                add('movers_other_state','B07001',[65],note='Persons age1+, not households')
                add('movers_abroad','B07001',[81],note='Prior residence abroad; not equivalent to immigration status')
                add('movers_outside_county_share','B07001',[49,65,81],1,note='Not a net migration rate')
            if (ds,geo,'B07011_001') in lookup:
                add('median_person_income_same_home','B07011',[2],note='Personal income age15+ with income; not household income')
                add('median_person_income_other_CA_county','B07011',[4],note='Not household purchasing power')
                add('median_person_income_other_state','B07011',[5],note='Not household purchasing power')
                add('median_person_income_abroad','B07011',[6],note='High uncertainty and different universe')
    dump_csv(ROOT / 'data/clean/acs_household_metrics_2024.csv', derived)
    qa=dict(status='pass',retrieved_date=RETRIEVED,raw_files_verified=len(files),
            detailed_rows=len(records),derived_rows=len(derived),arithmetic_checks=len(checks),
            table_coverage=coverage,checks=checks,known_unavailable=[dict(dataset='ACS2024_1YR',geography='Aliso Viejo',reason='Not present in standard 1-year geography file; never filled with zero')],
            sentinel_cells=[dict(dataset=r['dataset'],geography=r['geography'],variable_id=r['variable_id'],estimate_raw=r['estimate_raw'],moe_raw=r['moe_raw'],moe_status=r['moe_status']) for r in records if numeric(r['estimate_raw']) is None or numeric(r['moe_raw']) is None],
            unique_cell_keys=True,
            scope='Arithmetic/extraction and geography identity; no independent buyer-demand validation')
    (ROOT/'qa/acs_household_structure_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:qa[k] for k in ['status','raw_files_verified','detailed_rows','derived_rows','arithmetic_checks']},indent=2))


if __name__ == '__main__':
    main()
