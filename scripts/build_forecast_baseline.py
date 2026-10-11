"""Extract versioned public forecasts; compare them without blending vintages.

Run build_dof_baseline.py first. Raw downloads are ignored by git.
LDX Exhibit 12 is a raster chart: totals below were visually read on PDF page 32,
then independently checked against every text-based TAZ table in Appendix 1.
These checks establish extraction consistency, not a market forecast's validity.
"""
import argparse
import csv
import hashlib
import json
import re
import urllib.request
from pathlib import Path

import fitz
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'P2A_County_Total.xlsx': ('SRC-024', 'https://dof.ca.gov/media/docs/forecasting/Demographics/projections/P2A_County_Total.xlsx', '6caa2c639c8fc9571c0cb483848b3d74ec996c41075ebb5ae3fd0a4071574cad'),
    'PCC_Components_of_Change.xlsx': ('SRC-025', 'https://dof.ca.gov/media/docs/forecasting/Demographics/projections/PCC_Components_of_Change.xlsx', '3ac720a26dfe39969dc1da6bfc9a496af1b59e5588cc7f2409aa8734b26cea2f'),
    'P4_HHProjections_B2024.xlsx': ('SRC-026', 'https://dof.ca.gov/media/docs/forecasting/Demographics/projections/P4_HHProjections_B2024.xlsx', '6e61fe9f9f0ad2ee33982639412ef921d996513f030757c36bf3beee26300022'),
    'scag2024-frtp-sed.xlsx': ('SRC-029', 'https://scag.ca.gov/sites/default/files/2024-05/scag2024-frtp-sed.xlsx', '4e10e75c41df0b76df43c44703824fef577946fd25d14ee52a8cb2d8227b3393'),
}
CITY_FILES = {'Irvine': 'Irvine', 'Lake Forest': 'Lake-Forest', 'Tustin': 'Tustin', 'Aliso Viejo': 'Aliso-Viejo'}
LDX_HASHES = {
    'Irvine': '61472d79273337cdf8258cf381843aaead5b15a36444eb3110ebf8d6fb421521',
    'Lake Forest': 'aab1064c5bdb45e6cd53393abbb2706c0792234567c98ac14db4f3d21113c47b',
    'Tustin': '86838d91b6116096f9b95cd40a5c99647f1218e9468c718ba612d3eb7e5d3a49',
    'Aliso Viejo': '2896b0e946e62bcb8a9f1dbf7ad715907425ce275043883ea8ed7f110a4ff778',
}
# Chart data ordered HH2024/2035/2050, workplace employment2024/2035/2050.
CHART_TOTALS = {
    'Irvine': [116683, 126586, 132986, 316671, 319247, 308220],
    'Lake Forest': [30981, 32632, 32530, 42007, 42072, 41962],
    'Tustin': [27527, 32213, 31880, 53490, 54430, 50969],
    'Aliso Viejo': [19428, 19990, 20073, 22373, 22470, 22428],
}


def write_csv(name, rows):
    p = ROOT / 'data/clean' / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def read_rows(path, sheet):
    w = openpyxl.load_workbook(path, data_only=True, read_only=True)
    return list(w[sheet].iter_rows(values_only=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--raw-dir', type=Path, default=ROOT / 'data/raw/forecast')
    args = parser.parse_args()
    raw = args.raw_dir
    raw.mkdir(parents=True, exist_ok=True)
    for i, (city, slug) in enumerate(CITY_FILES.items(), 31):
        FILES[f'ldx2026_{slug}.pdf'] = (f'SRC-{i:03d}', f'https://scag.ca.gov/sites/default/files/2026-04/26-416-RDPLDX-0056-{slug}.pdf', LDX_HASHES[city])
    fingerprints = {}
    for filename, (sid, url, expected) in FILES.items():
        p = raw / filename
        if args.download and not p.exists():
            with urllib.request.urlopen(url, timeout=90) as response:
                p.write_bytes(response.read())
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'{filename}: version fingerprint differs; register new vintage before updating outputs')
        fingerprints[filename] = {'sha256': actual, 'bytes': p.stat().st_size, 'source_id': sid}

    pop = []
    data = read_rows(raw / 'P2A_County_Total.xlsx', 'Data')
    for rn, row in enumerate(data, 1):
        if row[1] == 'ORANGE':
            for year, value in zip(data[1][5:], row[5:]):
                pop.append(dict(geography='Orange County', fips='06059', year=int(year), snapshot_date=f'{year}-07-01', population_total=int(value), row_type='estimate' if int(year) <= 2025 else 'projection', baseline='2024', vintage='2026-03-13', source_id='SRC-024', source_sheet='Data', source_row=rn))
    pop_by_year = {r['year']: r['population_total'] for r in pop}
    components = []
    for rn, row in enumerate(read_rows(raw / 'PCC_Components_of_Change.xlsx', 'Counties Components of Change'), 1):
        if row[1] == 'ORANGE':
            fips, name, start, start_pop, births, deaths, net, end, end_pop = row
            assert int(start_pop) + int(births) - int(deaths) + int(net) == int(end_pop)
            assert pop_by_year[int(start)] == int(start_pop) and pop_by_year[int(end)] == int(end_pop)
            components.append(dict(geography='Orange County', fips='06059', start_year=int(start), end_year=int(end), period_start=f'{start}-07-01', period_end_exclusive=f'{end}-07-01', population_start=int(start_pop), births=int(births), deaths=int(deaths), natural_change=int(births-deaths), net_migration=int(net), population_end=int(end_pop), population_change=int(end_pop-start_pop), row_type='estimate' if int(end) <= 2025 else 'projection', baseline='2024', vintage='2026-03-13', source_id='SRC-025', source_sheet='Counties Components of Change', source_row=rn))
    hh = []
    data = read_rows(raw / 'P4_HHProjections_B2024.xlsx', 'Household Projections')
    for rn, row in enumerate(data, 1):
        if row[1] == 'ORANGE':
            for year, value in zip(data[1][2:], row[2:]):
                if not isinstance(year, int):
                    continue
                hh.append(dict(geography='Orange County', fips='06059', year=year, snapshot_date=f'{year}-01-01', households=int(value), row_type='estimate' if year <= 2025 else 'projection', baseline='2024', vintage='2025-11-17', source_id='SRC-026', source_sheet='Household Projections', source_row=rn))

    scag = []
    data = read_rows(raw / 'scag2024-frtp-sed.xlsx', 'Jurisdiction')
    for rn, row in enumerate(data, 1):
        if rn <= 6 or not isinstance(row[1], str):
            continue
        city = row[1].strip().removesuffix(' city')
        if city not in CITY_FILES:
            continue
        for k, year in enumerate([2019, 2035, 2050]):
            scag.append(dict(geography=city, geography_type='city', series='Connect SoCal 2024', status='adopted_HH_employment_population_supplement_unreviewed', year=year, households=int(row[6+k]), workplace_employment=int(row[9+k]), population_supplement=int(row[3+k]), population_status='not_part_of_adopted_plan_not_locally_reviewed', source_id='SRC-029', source_location=f'Jurisdiction row {rn}', vintage='2024-04-04', baseline_year=2019))
    data = read_rows(raw / 'scag2024-frtp-sed.xlsx', 'County')
    # County header rows 4/14/24; Orange rows 7/17/27, all rounded to thousands.
    for col, year in enumerate([1990, 2019, 2020, 2025, 2030, 2035, 2040, 2045, 2050], 1):
        scag.append(dict(geography='Orange County', geography_type='county', series='Connect SoCal 2024', status='adopted', year=year, households=int(data[16][col]), workplace_employment=int(data[26][col]), population_supplement=int(data[6][col]), population_status='adopted_county_total', source_id='SRC-029', source_location='County rows 7/17/27', vintage='2024-04-04', baseline_year=2019))

    taz_checks = []
    for i, (city, slug) in enumerate(CITY_FILES.items(), 31):
        sums = [0] * 6
        seen = set()
        d = fitz.open(raw / f'ldx2026_{slug}.pdf')
        for page_index in range(33, len(d)):
            text = d[page_index].get_text()
            if 'Preliminary Transportation Analysis Zone-Level Growth Forecast' not in text:
                continue
            # Eight-digit TAZ plus six integer values on separate lines.
            pattern = r'(?m)^(\d{8})\s*\n((?:[\d,]+\s*\n){6})'
            for match in re.finditer(pattern, text):
                key = match.group(1)
                assert key not in seen, (city, key)
                seen.add(key)
                values = [int(v.replace(',', '')) for v in match.group(2).split()]
                assert len(values) == 6
                sums = [a+b for a, b in zip(sums, values)]
        assert sums == CHART_TOTALS[city], (city, sums, CHART_TOTALS[city])
        taz_checks.append({'city': city, 'TAZ_count': len(seen), 'sums': sums, 'chart_match': True})
        for k, year in enumerate([2024, 2035, 2050]):
            scag.append(dict(geography=city, geography_type='city', series='Connect SoCal 2050 LDX 2026', status='preliminary_for_local_review', year=year, households=sums[k], workplace_employment=sums[3+k], population_supplement='', population_status='not_supplied', source_id=f'SRC-{i:03d}', source_location='PDF page 32 Exhibit 12; independently summed Appendix 1', vintage='2026-04', baseline_year=2024))

    with (ROOT / 'data/clean/dof_population_housing_v2026.csv').open() as f:
        estimates = list(csv.DictReader(f))
    growth = []
    for city in ['Orange County', *CITY_FILES]:
        series = {r['estimate_date']: r for r in estimates if r['geography'] == city}
        for start in ['2020-04-01', '2025-01-01']:
            a, b = series[start], series['2026-01-01']
            h0, h1 = int(a['occupied_units']), int(b['occupied_units'])
            p0, p1 = int(a['population_household']), int(b['population_household'])
            q0, q1 = p0/h0, p1/h1
            dh, dq = h1-h0, q1-q0
            h_effect = ((q0+q1)/2)*dh
            q_effect = ((h0+h1)/2)*dq
            gq_change = int(b['population_group_quarters'])-int(a['population_group_quarters'])
            pop_change = int(b['population_total'])-int(a['population_total'])
            assert abs(h_effect+q_effect+gq_change-pop_change) < 1e-6
            growth.append(dict(geography=city, start_date=start, end_date='2026-01-01', population_change=pop_change, occupied_units_start=h0, occupied_units_end=h1, occupied_units_change=dh, occupied_units_growth_fraction=dh/h0, persons_per_household_start=q0, persons_per_household_end=q1, household_count_effect_on_population=h_effect, household_size_effect_on_population=q_effect, group_quarters_change=gq_change, decomposition_error=h_effect+q_effect+gq_change-pop_change, source_id='SRC-001', vintage='2026-05', method='symmetric_accounting_identity_not_causal_model'))

    for r in scag:
        r['snapshot_reference'] = 'July 1' if r['geography_type'] == 'county' else 'year only; exact day not specified in extracted city table'
    outputs = {'dof_oc_population_projection_v2026.csv': pop, 'dof_oc_projected_components_v2026.csv': components, 'dof_oc_households_projection_v2025.csv': hh, 'scag_city_county_forecast_vintages.csv': scag, 'city_household_growth_decomposition.csv': growth}
    for name, rows in outputs.items():
        assert rows and all(v is not None for r in rows for v in r.values())
        write_csv(name, rows)
    assert len(pop) == 51 and len(components) == 50 and len(hh) == 31 and len(scag) == 33 and len(growth) == 10
    assert len({(r['series'], r['geography'], r['year']) for r in scag}) == len(scag)
    result = {'status': 'pass', 'output_rows': {name: len(rows) for name, rows in outputs.items()}, 'fingerprints': fingerprints, 'checks': ['fixed_vintage_SHA256', 'P2A_PCC_51_snapshots_match', 'PCC_50_component_equalities', 'SCAG_unique_keys', 'LDX_all_TAZ_sums_equal_visually_read_charts', '10_population_household_accounting_equalities'], 'LDX_TAZ_checks': taz_checks, 'limits': ['Population July 1 and households January 1 are separate clocks.', 'P4 Vintage 2025 is not updated to population Vintage 2026.', '2024 city population supplements are unreviewed and outside adopted plan.', '2026 LDX is preliminary, not approved.', 'Households include renters and owners; jobs are counted at workplace.', 'Housing Unit Method and accounting identity do not independently establish demand.', 'TAZ sums validate extraction, not assumptions or original source accuracy.']}
    (ROOT / 'qa/forecast_households_qa.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'output_rows': result['output_rows'], 'LDX_TAZ_checks': taz_checks}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
