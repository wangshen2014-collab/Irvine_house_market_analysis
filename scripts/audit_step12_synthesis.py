#!/usr/bin/env python3
"""Selected raw-source checks for step 12; no household inputs or model verdict.

Python standard library only. Private input layout is documented in the review pack.
This checks arithmetic and source identity, not representativeness or causality.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        yield from csv.DictReader(handle)


def numeric(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def workbook_cells(path, sheet):
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        rel_id = next(s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                      for s in workbook.find('m:sheets', NS) if s.get('name') == sheet)
        target = next(r.get('Target') for r in relationships if r.get('Id') == rel_id)
        target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        shared = [''.join(t.text or '' for t in s.iter('{'+NS['m']+'}t'))
                  for s in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        output = {}
        for cell in ET.fromstring(archive.read(target)).findall('.//m:c', NS):
            v = cell.find('m:v', NS)
            if v is not None:
                output[cell.get('r')] = shared[int(v.text)] if cell.get('t') == 's' else numeric(v.text)
        return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'qa/step12_checks.json')
    args = parser.parse_args()
    # Every original below is already fingerprinted at the frozen input commit.
    inputs = [
        ('purchasing', 'purchasing/raw/hmda_2025_purchase_oc.csv'),
        ('supply', 'supply/raw/irvine_apr2025.xlsm'),
        ('pricing', 'pricing2/raw/Neighborhood_zhvi_bdrmcnt_4_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'),
        ('pricing', 'pricing3/raw/realtor_county_history.csv'),
        ('scenario', 'scenario/raw/schoolsfirst_purchase.html'),
        ('scenario', 'scenario/raw/cusocal_rates.html'),
    ]
    checks, fingerprints = [], []

    def check(name, actual, expected, tolerance=0):
        passed = abs(actual - expected) <= tolerance if isinstance(actual, (int, float)) else actual == expected
        checks.append({'name': name, 'actual': actual, 'expected': expected, 'passed': passed})
        if not passed:
            raise AssertionError(checks[-1])

    for family, relative in inputs:
        file = args.evidence_root / relative
        manifest = json.loads((ROOT / 'data' / f'{family}_source_manifest.json').read_text())
        records = manifest.get('inputs', manifest.get('files', []))
        record = next(r for r in records if Path(r.get('path', r.get('filename', r.get('file', '')))).name == file.name)
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        check('sha256:' + file.name, digest, record['sha256'])
        fingerprints.append({'file': file.name, 'sha256': digest, 'bytes': file.stat().st_size,
                             'source_url': record.get('url'), 'manifest': f'data/{family}_source_manifest.json'})

    core = {r['tract_geoid'] for r in rows(ROOT / 'data/clean/hmda_tract_city_crosswalk.csv')
            if r['city'] == 'Irvine' and r['core_99999'] == 'True'}
    check('Irvine_core_tracts', len(core), 43)
    filters = {'action_taken': '1', 'loan_purpose': '1', 'occupancy_type': '1', 'lien_status': '1',
               'construction_method': '1', 'total_units': '1', 'reverse_mortgage': '2',
               'open-end_line_of_credit': '2', 'business_or_commercial_purpose': '2'}
    strict, selected, raw_count = [], [], 0
    for r in rows(args.evidence_root / inputs[0][1]):
        raw_count += 1
        if all(r[k] == v for k, v in filters.items()):
            strict.append(r)
            if r['census_tract'] in core:
                selected.append(r)
    check('HMDA_2025_OC_purchase_raw_rows', raw_count, 28853)
    check('HMDA_2025_OC_strict_rows', len(strict), 12367)
    check('HMDA_2025_Irvine_core_strict_rows', len(selected), 1002)
    groups = {'all': selected, 'value_2m_to_under_3m': [r for r in selected
              if numeric(r['property_value']) is not None and 2000000 <= float(r['property_value']) < 3000000]}
    hmda = {}
    for name, group in groups.items():
        # Nonpositive reported incomes are observations, not missing values.
        income = [float(r['income']) * 1000 for r in group if numeric(r['income']) is not None]
        cltv = [float(r['loan_to_value_ratio']) for r in group if numeric(r['loan_to_value_ratio']) is not None]
        hmda[name] = {'loans': len(group), 'income_valid': len(income), 'income_median_usd': statistics.median(income),
                      'cltv_valid': len(cltv), 'cltv_median_pct': statistics.median(cltv)}
    for name, expected in [('income_valid', 915), ('income_median_usd', 326000)]:
        check('HMDA_all_' + name, hmda['all'][name], expected)
    for name, expected in [('loans', 159), ('income_valid', 139), ('income_median_usd', 463000), ('cltv_valid', 156), ('cltv_median_pct', 69.816)]:
        check('HMDA_2m_3m_' + name, hmda['value_2m_to_under_3m'][name], expected, .00001)

    workbook = args.evidence_root / inputs[1][1]
    summary = workbook_cells(workbook, 'Summary')
    detail = workbook_cells(workbook, 'Table A2')
    supply = {}
    for col, cell, label, expected in [('T', 'C29', 'entitled', 4835), ('AG', 'D29', 'permitted', 1411), ('AT', 'E29', 'completed', 1052)]:
        values = {kind: sum(detail.get(f'{col}{n}', 0) or 0 for n in range(13, 2000) if detail.get(f'F{n}') == kind)
                  for kind in ['SFD', 'SFA', '2 to 4', '5+', 'ADU', 'MH']}
        # Type spelling is read from actual source; count every nonempty type, without dropping categories.
        all_types = {detail.get(f'F{n}') for n in range(13, 2000)} - {None, ''}
        total = sum(detail.get(f'{col}{n}', 0) or 0 for n in range(13, 2000) if detail.get(f'F{n}') in all_types)
        check('APR_' + label + '_Summary', summary[cell], expected)
        check('APR_' + label + '_detail', total, expected)
        supply[label] = {'all': int(total), 'SFD': int(values['SFD'])}
    check('APR_SFD_permitted', supply['permitted']['SFD'], 360)
    check('APR_SFD_completed', supply['completed']['SFD'], 600)

    price = {}
    for r in rows(args.evidence_root / inputs[2][1]):
        if r['RegionName'] not in {'Stonegate', 'Orchard Hills', 'Woodbury', 'Portola Springs'} or r['State'] != 'CA' or r['City'] != 'Irvine':
            continue
        latest = max(k for k in r if k[:4].isdigit() and r[k])
        check('ZHVI_last_date_' + r['RegionName'], latest, '2026-08-31')
        now = float(r[latest]); peak = max(float(v) for k, v in r.items() if '2024-01-01' <= k <= '2025-12-31' and v)
        price[r['RegionName']] = {'region_id': r['RegionID'], 'yoy_pct': (now/float(r['2025-08-31'])-1)*100,
                                 'two_year_pct': (now/float(r['2024-08-31'])-1)*100, 'change_from_2024_2025_peak_pct': (now/peak-1)*100}
    check('ZHVI_SG_yoy', price['Stonegate']['yoy_pct'], -1.081997, .00001)
    check('ZHVI_OH_yoy', price['Orchard Hills']['yoy_pct'], -2.667886, .00001)

    county = {r['month_date_yyyymm']: r for r in rows(args.evidence_root / inputs[3][1]) if r['county_fips'].zfill(5) == '06059'}
    check('Realtor_last_month', max(county), '202609')
    realtor = {}
    for field in ['active_listing_count', 'new_listing_count', 'pending_listing_count', 'median_days_on_market', 'median_listing_price', 'median_square_feet', 'median_listing_price_per_square_foot']:
        now, old = float(county['202609'][field]), float(county['202509'][field])
        realtor[field] = {'current': now, 'prior_year': old, 'level_based_yoy_pct': (now/old-1)*100,
                          'source_yoy_pct': float(county['202609'][field+'_yy'])*100}
    check('OC_active', realtor['active_listing_count']['current'], 4735)
    check('OC_pending', realtor['pending_listing_count']['current'], 1655)
    check('OC_DOM_shorter', realtor['median_days_on_market']['current'] < realtor['median_days_on_market']['prior_year'], True)
    realtor['active_vs_2019sep_pct'] = (4735/float(county['201909']['active_listing_count'])-1)*100

    # Solve fixed-payment principal by discounting every monthly cash flow.
    def pv(rate):
        return sum((1+rate/1200)**(-m) for m in range(1, 361))
    current_payment = 100000/pv(7.375)
    future_payment = 100000/pv(6.5)
    same_cash_index = 40 + 60*pv(6.5)/pv(7.375)
    fixed_ratio_index = 100*pv(6.5)/pv(7.375)
    check('PI_7_375_per_100k', current_payment, 690.6751475973392, .000001)
    check('fixed_cash_equal_PI_index', same_cash_index, 105.56336868115834, .000001)
    check('fixed_ratio_equal_PI_index', fixed_ratio_index, 109.27228113526392, .000001)
    financing = {'synthetic_only': True, 'price_index_base': 100, 'cash_index_base': 40,
                 'rate_from_pct': 7.375, 'rate_to_pct': 6.5, 'PI_per_100k_from': current_payment,
                 'PI_per_100k_to': future_payment, 'fixed_cash_equal_PI_price_index': same_cash_index,
                 'fixed_fraction_equal_PI_price_index': fixed_ratio_index,
                 'price_plus_10pct_PI_change_pct_fixed_cash': ((70/pv(6.5))/(60/pv(7.375))-1)*100}
    check('ACS_renter_share_of_point_increase', 9997/13810*100, 72.38957277335264, .000001)
    parameters_path = ROOT / 'data/step12_a_parameter_interface.json'
    if parameters_path.exists():
        params = json.loads(parameters_path.read_text())
        required = {'id','region','product','observation_window','forecast_horizon','unit','price_basis','tax_basis',
                    'evidence_kind','base_value','stress_value','source','confidence','update_rule','adoption'}
        for r in params['parameters']:
            check('parameter_schema:' + r['id'], required <= r.keys(), True)
            if r['evidence_kind'] == 'missing':
                check('missing_stays_null:' + r['id'], r['base_value'] is None, True)
        for identity in ['target_purchase_price','same_product_effective_rent','equity_total_return_expected','personal_mortgage_rate']:
            check('not_ready_for_A:' + identity, next(r for r in params['parameters'] if r['id'] == identity)['adoption'], 'blocked_pending_evidence')
    result = {'status': 'pass_selected_arithmetic_with_source_differences_retained', 'as_of_local': '2026-10-12',
              'timezone': 'America/Los_Angeles', 'input_commit': 'c2ad6899d8a3aa5a41fd36afa54e3b9a7f76e716',
              'same_agent_serial_check': True, 'independent_step13_review': False, 'checks_count': len(checks),
              'fingerprints': fingerprints, 'hmda_2025': hmda, 'apr_2025': supply, 'zhvi_four_bedroom': price,
              'realtor_oc_202609': realtor, 'financing': financing, 'checks': checks,
              'limitations': ['Selected sources only; no new census geometry audit', 'No target-product matched price/rent index',
                              'No personal loan estimate or household A/C input', 'QA pass is not an adequacy or forecast verdict']}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['status','checks_count','hmda_2025','apr_2025','zhvi_four_bedroom','realtor_oc_202609','financing']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
