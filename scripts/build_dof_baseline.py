"""Rebuild the 35-row DOF baseline from the May 2026 official workbook."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://dof.ca.gov/media/docs/forecasting/Demographics/estimates/e-5-population-and-housing-estimates-for-cities-counties-and-the-state-2020-2026/E-5_2026_InternetVersion.xlsx'
EXPECTED_SHA = '7d179aa625f07d4e05c78e89ca348f064b5ada9eba77d5b48c41feb33fb6f306'
HEADERS = ['Total', 'Household', 'Group Quarters', 'Total', 'Single Detached', 'Single Attached', 'Two to Four', 'Five Plus', 'Mobile Homes', 'Occupied', 'Vacancy Rate', 'Persons per Household']
COLS = ['population_total', 'population_household', 'population_group_quarters', 'housing_units_total', 'single_detached_units', 'single_attached_units', 'two_to_four_units', 'five_plus_units', 'mobile_home_units', 'occupied_units', 'vacancy_fraction', 'persons_per_household']
CITIES = {'Irvine', 'Lake Forest', 'Tustin', 'Aliso Viejo'}


def build(path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError('Workbook fingerprint changed; inspect the source vintage before updating EXPECTED_SHA.')
    workbook = load_workbook(path, data_only=True, read_only=True)
    records = []
    failures = []
    for year in range(2020, 2027):
        for kind, targets in [('CityCounty', CITIES), ('CountyState', {'Orange'})]:
            sheet = workbook[f'E5{kind}{year}']
            rows = list(sheet.iter_rows(values_only=True))
            if [str(v).strip() for v in rows[3][1:13]] != HEADERS:
                raise ValueError(f'Unexpected headers in {sheet.title}')
            if f'{4 if year == 2020 else 1}/1/{year}' not in str(rows[0][0]):
                raise ValueError(f'Unexpected estimate date in {sheet.title}')
            found = set()
            for row_num, row in enumerate(rows, 1):
                name = str(row[0]).strip()
                if name not in targets:
                    continue
                if name in found:
                    raise ValueError(f'Duplicate geography {name} in {sheet.title}')
                found.add(name)
                rec = {'geography': 'Orange County' if kind == 'CountyState' else name,
                       'geography_type': 'county' if kind == 'CountyState' else 'city',
                       'estimate_date': f'{year}-04-01' if year == 2020 else f'{year}-01-01',
                       'publication_vintage': '2026-05', 'source_id': 'SRC-001',
                       'source_sheet': sheet.title, 'source_row': row_num}
                rec.update(dict(zip(COLS, row[1:13])))
                if any(rec[c] is None for c in COLS):
                    failures.append(f'Missing numeric field: {name}/{year}')
                if rec['population_total'] != rec['population_household'] + rec['population_group_quarters']:
                    failures.append(f'Population components: {name}/{year}')
                if rec['housing_units_total'] != sum(rec[c] for c in COLS[4:9]):
                    failures.append(f'Housing components: {name}/{year}')
                vacancy = 1 - rec['occupied_units'] / rec['housing_units_total']
                if abs(vacancy - rec['vacancy_fraction']) > 1e-10:
                    failures.append(f'Vacancy arithmetic: {name}/{year}')
                # Household population may be rounded to people in the published table.
                if abs(rec['population_household'] / rec['occupied_units'] - rec['persons_per_household']) > 1e-4:
                    failures.append(f'Household arithmetic: {name}/{year}')
                records.append(rec)
            if found != targets:
                raise ValueError(f'Missing target geography in {sheet.title}: {targets-found}')
    records.sort(key=lambda r: (r['geography'], r['estimate_date']))
    keys = {(r['geography'], r['estimate_date']) for r in records}
    if len(records) != 35 or len(keys) != 35:
        failures.append('Expected 35 unique geography/date records')
    qa = {'status': 'pass' if not failures else 'fail', 'rows': len(records),
          'unique_geography_date_keys': len(keys), 'source_sha256': digest,
          'checks_per_row': ['population_components', 'housing_components', 'vacancy_arithmetic', 'household_arithmetic', 'required_numeric_fields'],
          'failures': failures,
          'limits': ['2020 is April 1; other dates are January 1.',
                     'Population change is not net migration.',
                     'Housing Unit Method estimates are not independent proof of housing demand.',
                     'Single detached is an aggregate structure category, not a 4-bedroom/no-shared-wall legal classification.',
                     'Vacancy includes all housing stock, not active sale inventory.',
                     'This validates extraction and arithmetic, not source accuracy or causal conclusions.']}
    (ROOT / 'data/clean').mkdir(parents=True, exist_ok=True)
    (ROOT / 'qa').mkdir(exist_ok=True)
    (ROOT / 'qa/dof_qa.json').write_text(json.dumps(qa, indent=2, ensure_ascii=False) + '\n')
    if failures:
        raise ValueError(f'DOF validation failed: {failures}')
    with (ROOT / 'data/clean/dof_population_housing_v2026.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({'status': qa['status'], 'rows': len(records), 'sha256': digest}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=ROOT / 'data/raw/E-5_2026_InternetVersion.xlsx')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if args.download:
        args.input.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(URL, timeout=40) as response:
            raw = response.read()
        if not raw.startswith(b'PK'):
            raise ValueError('Download is not an XLSX; reject error or login HTML.')
        args.input.write_bytes(raw)
    build(args.input)
