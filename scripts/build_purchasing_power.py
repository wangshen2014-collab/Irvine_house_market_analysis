"""Reproduce phase-7 public aggregates from frozen official HMDA/BLS/Census inputs.

Loan-level records are never exported. City groups are tract coverage scenarios,
not citywide totals or inferred borrower moves. No race/nationality inference.
"""
import argparse
import csv
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import statistics
import urllib.request
from collections import Counter

from lxml import html
from pyproj import Transformer
from shapely import make_valid, transform
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
CITIES = ['Irvine', 'Lake Forest', 'Tustin', 'Aliso Viejo']
YEARS = [2023, 2024, 2025]
FOCUS = ['06059052429', '06059052437']
STRICT = {'action_taken': '1', 'loan_purpose': '1', 'occupancy_type': '1',
          'lien_status': '1', 'construction_method': '1', 'total_units': '1',
          'reverse_mortgage': '2', 'open-end_line_of_credit': '2',
          'business_or_commercial_purpose': '2'}
DTI = {'<20%': False, '20%-<30%': False, '30%-<36%': False,
       **{str(i): i >= 43 for i in range(36, 50)},
       '50%-60%': True, '>60%': True}


def records(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        raise ValueError(f'empty output: {path.name}')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def number(s):
    if s in ('', 'NA', 'Exempt'):
        return None
    x = Decimal(s)
    if not x.is_finite():
        raise ValueError(f'Nonfinite public numeric value: {s}')
    return float(x)


def matches(r, conditions):
    return all(r[k] in v if isinstance(v, tuple) else r[k] == v
               for k, v in conditions.items())


def summarize(rows, year, geography, scenario, band='all'):
    """Keep zero/negative reported incomes; publish valid/missing denominators.

    Quartiles use linearly interpolated order statistics (type 7). All dollar
    measures remain nominal. Distribution statistics require >=10 valid rows.
    """
    out = dict(year=year, geography=geography, geography_scenario=scenario,
               property_value_band=band, originations=len(rows),
               lender_count=len({r['lei'] for r in rows}))
    for raw, name, multiplier in [('income', 'income_usd', 1000),
            ('loan_amount', 'loan_usd', 1), ('property_value', 'property_value_usd', 1),
            ('loan_to_value_ratio', 'cltv_percent', 1)]:
        v = sorted(number(r[raw]) * multiplier for r in rows if number(r[raw]) is not None)
        out[name + '_valid_n'] = len(v)
        out[name + '_missing_n'] = len(rows) - len(v)
        for q, label in [(0.25, 'p25'), (0.5, 'median'), (0.75, 'p75')]:
            ix = (len(v) - 1) * q
            value = v[math.floor(ix)] + (ix % 1) * (v[math.ceil(ix)] - v[math.floor(ix)]) if len(v) >= 10 else ''
            out[name + '_' + label] = round(value, 6) if value != '' else ''
    inc = [number(r['income']) for r in rows if number(r['income']) is not None]
    out['income_nonpositive_n'] = sum(x <= 0 for x in inc)
    for threshold in [200, 300, 500]:
        n = sum(x >= threshold for x in inc)
        out[f'income_ge{threshold}k_n'] = n
        out[f'income_ge{threshold}k_share_valid'] = round(n / len(inc), 8) if inc else ''
    cltv = [number(r['loan_to_value_ratio']) for r in rows if number(r['loan_to_value_ratio']) is not None]
    out['cltv_le60_n'] = sum(x <= 60 for x in cltv)
    out['cltv_le60_share_valid'] = round(out['cltv_le60_n'] / len(cltv), 8) if cltv else ''
    out['cltv_nonpositive_n'] = sum(x <= 0 for x in cltv)
    out['cltv_above100_n'] = sum(x > 100 for x in cltv)
    dti = [DTI[r['debt_to_income_ratio']] for r in rows if r['debt_to_income_ratio'] in DTI]
    unknown = set(r['debt_to_income_ratio'] for r in rows) - set(DTI) - {'NA', 'Exempt', ''}
    if unknown:
        raise ValueError(f'Unmapped DTI category {unknown}')
    out.update(dti_valid_n=len(dti), dti_missing_n=len(rows)-len(dti),
               dti_ge43_n=sum(dti), dti_ge43_share_valid=round(sum(dti)/len(dti), 8) if dti else '')
    # Difference is an appraisal/credit-value gap, NEVER actual down payment.
    gaps = [number(r['property_value']) - number(r['loan_amount']) for r in rows
            if number(r['property_value']) is not None]
    out['value_minus_first_loan_valid_n'] = len(gaps)
    out['value_minus_first_loan_median_usd'] = statistics.median(gaps) if len(gaps) >= 10 else ''
    out['value_minus_first_loan_negative_n'] = sum(x < 0 for x in gaps)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-dir', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, default=ROOT/'data/purchasing_source_manifest.json')
    ap.add_argument('--outdir', type=Path, default=ROOT/'data/clean')
    ap.add_argument('--qa', type=Path, default=ROOT/'qa/purchasing_power_qa.json')
    ap.add_argument('--download', action='store_true')
    a = ap.parse_args(); raw = a.raw_dir
    manifest = json.loads(a.manifest.read_text())
    checks = []
    def check(name, ok, **details):
        checks.append(dict(check=name, status='pass' if ok else 'fail', **details))
        if not ok:
            raise ValueError(f'{name}: {details}')
    # Validate ALL inputs before producing any output. Never silently refreeze.
    for rec in manifest['files']:
        f = raw/rec['filename']
        if not f.exists() and a.download and rec.get('downloadable', True):
            with urllib.request.urlopen(rec['url'], timeout=120) as response:
                content = response.read()
            check('download_fingerprint', hashlib.sha256(content).hexdigest()==rec['sha256'], filename=f.name)
            f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(content)
        check('input_fingerprint', f.exists() and hashlib.sha256(f.read_bytes()).hexdigest()==rec['sha256'], filename=f.name)
    tf = Transformer.from_crs(4326, 26911, always_xy=True)
    def features(name):
        obj = json.loads((raw/name).read_text())
        check('valid_geojson', obj.get('type')=='FeatureCollection' and not obj.get('exceededTransferLimit'), filename=name)
        return obj['features']
    def geom(f):
        g = shape(f['geometry'])
        check('valid_source_geometry', g.is_valid, id=f['properties']['GEOID'])
        return transform(g, tf.transform, interleaved=False)
    tract_features = features('oc_tracts_2024.geojson')
    tracts = {f['properties']['GEOID']: geom(f) for f in tract_features}
    check('unique_oc_tracts', len(tracts)==len(tract_features)==614)
    places = {f['properties']['BASENAME']: geom(f) for f in features('places2024.geojson')}
    check('four_city_names', set(places)==set(CITIES))
    cross = []; groups = {}; geo_checks = []
    for city in CITIES:
        g = places[city]
        for tid, t in tracts.items():
            area = t.intersection(g).area
            if area <= 1:
                continue
            share = area / t.area
            # Fixed diagnostic thresholds; never use area as household weight.
            row = dict(city=city, tract_geoid=tid, tract_area_m2=round(t.area, 4),
                       intersection_area_m2=round(area, 4), tract_area_share_in_city=round(share, 12),
                       core_99999=share>=.99999, majority_50=share>=.5,
                       near_95=share>=.95, overlap_gt1m2=True)
            cross.append(row)
        cg = [r for r in cross if r['city']==city]
        for mode in ['core_99999', 'near_95', 'majority_50', 'overlap_gt1m2']:
            groups[(city, mode)] = {r['tract_geoid'] for r in cg if r[mode]}
        check('nested_geography_scenarios', groups[city,'core_99999'] <= groups[city,'near_95'] <= groups[city,'majority_50'] <= groups[city,'overlap_gt1m2'], city=city)
        geo_checks.append(dict(city=city, core_tracts=len(groups[city,'core_99999']),
            near95_tracts=len(groups[city,'near_95']), majority_tracts=len(groups[city,'majority_50']),
            overlapping_tracts=len(cg), core_area_share_of_city=round(sum(r['intersection_area_m2'] for r in cg if r['core_99999'])/g.area, 8),
            geographic_vintage='ACS2024 TIGERweb; 2020 tract coding; constant across loan years',
            warning='area not population/household/loan coverage; not citywide totals'))
    for i, city in enumerate(CITIES):
        for other in CITIES[i+1:]:
            check('core_tract_sets_disjoint', not groups[city,'core_99999'] & groups[other,'core_99999'], city=city, other=other)
    summary = []; bands = []; funnel = []; sensitivity = []; field_quality = []; audits = []
    for y in YEARS:
        rows = records(raw/f'hmda_{y}_purchase_oc.csv')
        aggregate = json.loads((raw/f'hmda_{y}_aggregate_purchase.json').read_text())['aggregations']
        check('api_count_matches_csv', sum(r['count'] for r in aggregate)==len(rows), year=y, count=len(rows))
        loansum = sum(Decimal(r['loan_amount']) for r in rows)
        check('api_amount_matches_csv', sum(Decimal(str(r['sum'])) for r in aggregate)==loansum, year=y, sum_usd=str(loansum))
        check('request_filters_verified', all(r['activity_year']==str(y) and r['county_code']=='06059' and r['state_code'] in ('CA','NA') and r['loan_purpose']=='1' for r in rows), year=y)
        selected = rows
        funnel.append(dict(year=y, filter_step='all_purchase_records', records=len(selected), excluded_this_step=0))
        for field, values in [('action_taken','1'),('occupancy_type','1'),('lien_status','1'),
                ('construction_method','1'),('total_units',('1','2','3','4')),('total_units','1'),
                ('reverse_mortgage','2'),('open-end_line_of_credit','2'),('business_or_commercial_purpose','2')]:
            prior=len(selected); selected=[r for r in selected if matches(r,{field:values})]
            funnel.append(dict(year=y, filter_step=f'{field}={values}', records=len(selected), excluded_this_step=prior-len(selected)))
        check('direct_vs_staged_filter', len(selected)==sum(matches(r,STRICT) for r in rows),year=y)
        duplicate_n=len(selected)-len({tuple(r.values()) for r in selected})
        missing_tract=sum(r['census_tract'] in ('NA','') for r in selected)
        unmatched={r['census_tract'] for r in selected if r['census_tract'] not in tracts and r['census_tract'] not in ('NA','')}
        check('all_nonmissing_tracts_match', not unmatched, year=y, unknown_tracts=sorted(unmatched))
        check('loan_dollar_midpoints', all(Decimal(r['loan_amount'])%10000==5000 for r in rows),year=y)
        check('property_dollar_midpoints', all(Decimal(r['property_value'])%10000==5000 for r in rows if r['property_value'] not in ('NA','Exempt','')),year=y)
        audits.append(dict(year=y, purchase_records=len(rows), purchase_loan_amount_sum_usd=str(loansum),
            strict_originations=len(selected), exact_public_row_duplicates_retained=duplicate_n,
            missing_tract_n=missing_tract, missing_state_all_n=sum(r['state_code']=='NA' for r in rows),
            missing_state_strict_n=sum(r['state_code']=='NA' for r in selected), unique_lenders=len({r['lei'] for r in selected}),
            unique_loan_or_household_identifier_available=False))
        group_rows={('Orange County','county'):selected}
        for key, ids in groups.items():
            group_rows[key]=[r for r in selected if r['census_tract'] in ids]
        for tid in FOCUS:
            group_rows[(tid,'whole_tract_proxy')]=[r for r in selected if r['census_tract']==tid]
        for (geo, mode), rr in group_rows.items():
            summary.append(summarize(rr,y,geo,mode))
            if mode in ('core_99999','whole_tract_proxy','county'):
                for key in ['income','property_value','loan_to_value_ratio','debt_to_income_ratio']:
                    counts=Counter(r[key] for r in rr)
                    field_quality.append(dict(year=y,geography=geo,scenario=mode,field=key,total_n=len(rr),
                        blank_n=counts[''],not_applicable_n=counts['NA'],exempt_n=counts['Exempt'],
                        available_n=len(rr)-counts['']-counts['NA']-counts['Exempt']))
            if mode in ('core_99999','majority_50','county'):
                assigned=[]
                for lo, hi, label in [(0,1000000,'below_1m'),(1000000,1500000,'1m_to_lt1_5m'),
                        (1500000,2000000,'1_5m_to_lt2m'),(2000000,3000000,'2m_to_lt3m'),(3000000,float('inf'),'3m_plus')]:
                    bb=[r for r in rr if number(r['property_value']) is not None and lo<=number(r['property_value'])<hi]
                    bands.append(summarize(bb,y,geo,mode,label));assigned.extend(bb)
                check('value_bands_partition_valid', len(assigned)==sum(number(r['property_value']) is not None for r in rr),year=y,geography=geo,mode=mode)
        # Exempt is unknown, not false. Explicitly include it only in sensitivity.
        base={k:v for k,v in STRICT.items() if k not in ('reverse_mortgage','open-end_line_of_credit','business_or_commercial_purpose')}
        relaxed=dict(base,**{k:('2','1111') for k in ('reverse_mortgage','open-end_line_of_credit','business_or_commercial_purpose')})
        units14=dict(STRICT,total_units=('1','2','3','4'))
        for label, cond in [('strict',STRICT),('allow_partial_exemption',relaxed),('one_to_four_units',units14)]:
            rr=[r for r in rows if matches(r,cond)]
            for city in ['Orange County']+CITIES:
                cc=rr if city=='Orange County' else [r for r in rr if r['census_tract'] in groups[city,'core_99999']]
                sensitivity.append(dict(filter_scenario=label,**summarize(cc,y,city,'county' if city=='Orange County' else 'core_99999')))
    # BLS workplace payroll measures; annual pay is per job, NOT household income.
    jobs=[]
    names={'10':'All industries','31-33':'Manufacturing','51':'Information','52':'Finance and insurance',
           '54':'Professional scientific and technical services','55':'Management of companies',
           '62':'Health care and social assistance','334':'Computer and electronic product manufacturing'}
    for filename,period in [('qcew_2025_a_oc.csv','2025_annual'),('qcew_2026_1_oc.csv','2026_Q1')]:
        rr=records(raw/filename)
        check('qcew_area',all(r['area_fips']=='06059' for r in rr),filename=filename)
        for r in rr:
            if r['industry_code'] not in names or r['own_code'] not in ('0','5') or (r['own_code']=='0' and r['industry_code']!='10'):
                continue
            disclose=r['disclosure_code'] != 'N'
            jobs.append(dict(period=period,geography='Orange County workplace',ownership='all' if r['own_code']=='0' else 'private',
                naics=r['industry_code'],industry=names[r['industry_code']],disclosure_code=r['disclosure_code'],
                employment=int(r['annual_avg_emplvl'] if period=='2025_annual' else r['month3_emplvl']) if disclose else '',
                employment_measure='annual_average_jobs' if period=='2025_annual' else 'March_jobs',
                avg_annual_pay_usd=int(r['avg_annual_pay']) if period=='2025_annual' and disclose else '',
                avg_weekly_wage_usd=int(r['avg_wkly_wage']) if period!='2025_annual' and disclose else '',
                employment_yoy_percent_unadjusted=r.get('oty_month3_emplvl_pct_chg','') if disclose else '',
                wage_yoy_percent_unadjusted=r.get('oty_avg_wkly_wage_pct_chg','') if disclose else ''))
    doc=html.fromstring((raw/'bls_eag.html').read_bytes()); eag=[]; prior=''
    for tr in doc.xpath('//tr'):
        cells=[' '.join(x.text_content().split()) for x in tr.xpath('./th|./td')]
        if len(cells)!=8 or cells[0]=='Data Series': continue
        title=cells[0]
        if title=='12-month % change': title=prior+' | year_over_year_percent'
        else: prior=title
        for month,text in zip(['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08'],cells[2:]):
            eag.append(dict(period=month,geography='Anaheim-Santa Ana-Irvine MD',series=title,
                value=float(text.replace('(p)','').replace(',','')),preliminary='(p)' in text,seasonally_adjusted=False))
    # Pure financing arithmetic; not current lender quotes, approval, or full cost.
    financing=[]
    for loan in [1000000,1500000,2000000]:
        for rate in [5,6,7]:
            r=Decimal(rate)/Decimal(1200);n=360
            payment=Decimal(loan)*r/(1-(1+r)**(-n))
            ordinary=loan*(rate/1200)/(1-(1+rate/1200)**-n)
            check('decimal_vs_float_payment',abs(float(payment)-ordinary)<1e-6,loan=loan,rate=rate)
            financing.append(dict(loan_usd=loan,annual_rate_percent=rate,months=n,
                monthly_principal_interest_usd=str(payment.quantize(Decimal('.01'))),
                status='illustrative_only; excludes tax HOA MR insurance maintenance other debts'))
    outputs={'hmda_tract_city_crosswalk.csv':cross,'hmda_geography_coverage.csv':geo_checks,
             'hmda_filter_funnel.csv':funnel,'hmda_purchase_summary.csv':summary,
             'hmda_value_bands.csv':bands,'hmda_filter_sensitivity.csv':sensitivity,
             'hmda_field_completeness.csv':field_quality,'hmda_acquisition_checks.csv':audits,
             'oc_employment_wages.csv':jobs,'oc_recent_employment.csv':eag,
             'purchasing_financing_scenarios.csv':financing}
    for name, rr in outputs.items(): write_csv(a.outdir/name,rr)
    a.qa.parent.mkdir(parents=True,exist_ok=True)
    a.qa.write_text(json.dumps(dict(status='pass',checks_passed=len(checks),checks=checks,
        output_rows={k:len(v) for k,v in outputs.items()},
        limitations=['No borrower identity, address, prior city, cash buyer, bedroom, built year, floor area or HOA.',
        'Statistical QA is not causal identification or independent model review.',
        'Exact public-row duplicates are retained; privacy modifications can make distinct loans identical.',
        'City core excludes mixed growth tracts; overlapping scenarios are not additive city totals.']),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'checks_passed':len(checks),'output_rows':{k:len(v) for k,v in outputs.items()}},ensure_ascii=False))


if __name__=='__main__': main()
