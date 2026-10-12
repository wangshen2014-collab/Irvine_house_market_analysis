"""Phase 8: deterministic proxy matches, explicit cost scenarios, evidence coverage.

Private inputs are frozen research notes, not an MLS data redistribution. All
fingerprints are checked before output directories are created. Public outputs
contain original diagnostics, synthetic arithmetic and brief professional opinions.
"""
import argparse
import csv
import hashlib
import json
from datetime import date
from decimal import Decimal, getcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
getcontext().prec = 45

def read_csv(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write_csv(p, rows):
    if not rows:
        raise ValueError('Output schema cannot be inferred from empty rows')
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')

def payment(loan, annual_rate, years):
    r = annual_rate / 12
    n = years * 12
    return loan/n if r == 0 else loan*r/(1-(1+r)**(-n))

def audit_payment(loan, annual_rate, years):
    """Independent Decimal monthly-balance simulation and payment bisection."""
    p, r = Decimal(str(loan)), Decimal(str(annual_rate))/12
    lo, hi = Decimal(0), p*(1+r)
    for _ in range(160):
        mid = (lo+hi)/2
        bal = p
        for _ in range(years*12):
            bal = bal*(1+r)-mid
        if bal > 0:
            lo = mid
        else:
            hi = mid
    return float((lo+hi)/2)

def hoa_monthly(components):
    if not components:
        return None
    factors = {'monthly': Decimal(1), 'quarterly': Decimal(1)/3, 'annual': Decimal(1)/12}
    return float(sum((Decimal(str(c['amount']))*factors[c['frequency']] for c in components), Decimal(0)))

def flag(v):
    return v is True or v == 'True'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input-dir', type=Path, required=True)
    ap.add_argument('--public-out', type=Path, default=ROOT/'data/clean')
    ap.add_argument('--private-out', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, default=ROOT/'data/crosscity_source_manifest.json')
    ap.add_argument('--config', type=Path, default=ROOT/'data/crosscity_scenario_config.json')
    a = ap.parse_args()
    manifest = json.loads(a.manifest.read_text())
    cfg = json.loads(a.config.read_text())
    paths = {}
    for rec in manifest['inputs']:
        p = a.input_dir/rec['filename']
        b = p.read_bytes()
        if len(b) != rec['bytes'] or hashlib.sha256(b).hexdigest() != rec['sha256']:
            raise ValueError('Input fingerprint mismatch: '+rec['key'])
        paths[rec['key']] = p
    pilot = json.loads(paths['pilot'].read_text())
    hist = read_csv(paths['history_summary'])
    broker = json.loads(paths['broker_notes'].read_text())
    # Review supplement changes publication metadata only; frozen notes stay immutable.
    versions = json.loads((ROOT/'data/crosscity_source_versions_20261012.json').read_text())
    for b in broker:
        b['historical_page_status'] = '旧版本未独立核验；冻结研究笔记不是网页原件'
        if b['broker_id'] == 'B13':
            b['evidence_limit'] = '冻结笔记记8月25日更新；2026-10-12原HTML回查显示7月10日发布、10月11日更新，页末资料截止7月10日。旧版本未独立核验；不作库存序列。'
            b['current_page_review_date'] = '2026-10-12'
            b['current_page_updated'] = versions['visible_updated']
            b['current_page_data_as_of'] = versions['footer_data_as_of']
        else:
            b['current_page_review_date'] = ''
            b['current_page_updated'] = ''
            b['current_page_data_as_of'] = ''
    buyers = json.loads(paths['buyer_notes'].read_text())
    notes = json.loads(paths['property_notes'].read_text())
    raw = {r['record_id']: r for r in pilot['records'] if r['transaction_type']=='sale'}
    assert len(raw) == len(hist) == 25 and len({r['record_id'] for r in hist}) == 25
    assert len({r['broker_id'] for r in broker}) == len(broker)
    assert len({r['case_id'] for r in buyers}) == len(buyers)
    m = cfg['matching']
    eligible = []
    for r in hist:
        b = raw[r['record_id']]
        if (flag(r['profile_and_price_candidate']) and int(r['bedrooms'])==m['bedrooms']
            and int(r['year_built'])>=m['min_year'] and int(r['living_area_sqft'])>=m['min_area_sqft']
            and b['shared_wall_status']=='no_common_walls_mls_reported'):
            eligible.append(dict(r,city=b['city']))
    left = [r for r in eligible if r['city']=='Irvine']
    right = [r for r in eligible if r['city']!='Irvine']
    assert len(eligible) == 20 and len(left) == 17 and len(right) == 3
    pairs = []
    for i in left:
        for o in right:
            ar = max(int(i['living_area_sqft']), int(o['living_area_sqft']))/min(int(i['living_area_sqft']), int(o['living_area_sqft']))
            yg = abs(int(i['year_built'])-int(o['year_built']))
            dg = abs((date.fromisoformat(i['close_date_mls'])-date.fromisoformat(o['close_date_mls'])).days)
            passed = ar<=m['area_ratio_max'] and yg<=m['year_gap_max'] and dg<=m['close_gap_days_max']
            ip,op = float(i['close_price_mls_baseline']),float(o['close_price_mls_baseline'])
            pairs.append(dict(irvine_id=i['record_id'],other_id=o['record_id'],irvine_address=i['address'],other_address=o['address'],other_city=o['city'],area_ratio=ar,year_gap=yg,close_gap_days=dg,proxy_pass=passed,full_quality_verified=False,irvine_price_usd=ip,other_price_usd=op,raw_price_gap_pct=(ip/op-1)*100,remaining='legal/exclusive lot; layout/upgrades; official schools; commute; exact tax/insurance; time adjustment'))
    selected = [p for p in pairs if p['proxy_pass']]
    assert {(p['irvine_id'],p['other_id'])for p in selected} == {('T002','T024'),('T012','T023'),('T016','T023'),('T018','T024')}
    sensitivity = []
    for sid, ar, yg, dg in cfg['sensitivity']:
        pp=[p for p in pairs if p['area_ratio']<=ar and p['year_gap']<=yg and p['close_gap_days']<=dg]
        sensitivity.append(dict(scenario=sid,area_ratio_max=ar,year_gap_max=yg,close_gap_days_max=dg,candidate_pairs=len(pairs),proxy_pairs=len(pp),unique_irvine_homes=len({p['irvine_id']for p in pp}),unique_other_homes=len({p['other_id']for p in pp}),full_quality_pairs=0))
    costs=[]
    for n in notes:
        b=raw[n['record_id']]
        components=n['hoa_override'] if n['hoa_override'] is not None else b.get('hoa_components',[])
        costs.append(dict(record_id=n['record_id'],address=b['address'],city=b['city'],hoa_monthly_usd=hoa_monthly(components),hoa_basis='MLS listing-era; not current HOA ledger',hoa_source=n['source_url'],annual_special_assessments_usd=n['annual_special_assessments_usd'],insurance_annual_usd=n['insurance_annual_usd'],verified_new_buyer_tax_usd=n['verified_new_buyer_tax_usd'],all_in_monthly_usd=None,quality_note=n['quality_note'],school_note=n['school_note'],tax_conflict=n.get('tax_conflict','')))
    cm={r['record_id']:r for r in costs}
    assert abs(cm['T025']['hoa_monthly_usd']-332.32)<1e-10 and cm['T024']['hoa_monthly_usd']==325.33
    assert all(r['all_in_monthly_usd'] is None for r in costs)
    f=cfg['financing']; marginal=[]; audit=[]
    for rate in f['annual_rates']:
        pi=payment(f['price_delta_usd']*f['ltv'],rate,f['years'])
        independent=audit_payment(f['price_delta_usd']*f['ltv'],rate,f['years'])
        assert abs(pi-independent)<1e-7
        tax=f['price_delta_usd']*f['uniform_assumed_advalorem']/12
        row=dict(annual_rate_assumption=rate,ltv_assumption=f['ltv'],years=f['years'],price_delta_usd=f['price_delta_usd'],extra_downpayment_usd=round(f['price_delta_usd']*(1-f['ltv']),2),extra_monthly_pi=round(pi,2),extra_monthly_uniform_tax=round(tax,2),extra_monthly_selected_cashflow=round(pi+tax,2),scope='PI plus assumed uniform 1.1% value tax only; not total economic cost')
        for fee in f['fee_deltas_monthly_usd']:
            row[f'price_offset_for_{fee}_monthly_usd']=round(fee/(pi+tax)*f['price_delta_usd'],2)
        marginal.append(row)
        audit.append(dict(rate=rate,closed_formula_pi=pi,decimal_simulation_pi=independent,abs_difference=abs(pi-independent)))
    synthetic=[]
    for s in cfg['synthetic_scenarios']:
        pi=payment(s['price_usd']*s['ltv'],s['rate'],s['years'])
        independent=audit_payment(s['price_usd']*s['ltv'],s['rate'],s['years'])
        assert abs(pi-independent)<1e-6
        tx=s['price_usd']*s['uniform_assumed_advalorem']/12
        monthly=pi+tx+s['hoa_monthly']+(s['special_annual']+s['insurance_annual']+s['maintenance_annual'])/12
        synthetic.append(dict(s,monthly_pi=round(pi,2),monthly_assumed_tax=round(tx,2),monthly_selected_cashflow=round(monthly,2),all_in_economic_cost_usd=None,warning=cfg['scenario_warning']))
    cases=[]
    for b in buyers:
        gates=dict(known_exact_origin_city=bool(b['origin']) and 'unknown' not in b['origin'],known_destination_city=bool(b['destination']),known_year=bool(b['year']),independent_transaction=bool(b['independent_transaction']),known_price_product=b['price'] is not None and b['product'] is not None)
        cases.append(dict(case_id=b['case_id'],**gates,verified_flow_case=all(gates.values())))
    assert sum(c['verified_flow_case']for c in cases)==0
    coverage=[
        dict(metric='frozen_sale_records',value=len(hist),denominator='',meaning='非随机方便样本'),
        dict(metric='eligible_profiles',value=len(eligible),denominator=len(hist),meaning='四卧、无共墙、2010年以后、面积至少1650；价格/卧室严重冲突排除'),
        dict(metric='candidate_crosscity_pairs',value=len(pairs),denominator='',meaning='17个Irvine与3个外市房屋的笛卡尔积'),
        dict(metric='base_proxy_pairs',value=len(selected),denominator=len(pairs),meaning='仅面积/房龄/日期；重复使用2个外市样本'),
        dict(metric='quality_verified_pairs',value=0,denominator=len(selected),meaning='地块、学校、装修、通勤等尚未控制'),
        dict(metric='property_cost_reviews',value=len(costs),denominator='',meaning='6套配对房屋加2套额外对照'),
        dict(metric='complete_property_costs',value=0,denominator=len(costs),meaning='实际新买家税单、特别收费及保险未齐'),
        dict(metric='broker_public_sources',value=len(broker),denominator='target_12_to_20',meaning='人或个人品牌文章；不是13次访谈'),
        dict(metric='firm_families',value=len({b['firm_family']for b in broker if b['firm_family']}),denominator='target_at_least_6',meaning='机构品牌归组，不能视为独立上游数据'),
        dict(metric='long_irvine_self_claims',value=sum(b['long_irvine_self_claim']for b in broker),denominator=len(broker),meaning='自述十年以上Irvine业务；尚非连续执业审核'),
        dict(metric='dated_irvine_activity_evidence',value=sum(b['dated_irvine_evidence']for b in broker),denominator='long_source_target_8_to_12',meaning='1人另有十年前第三方成交页；仍不是逐年连续执业验证'),
        dict(metric='independent_broker_interviews',value=0,denominator=len(broker),meaning='未联系或访谈任何人'),
        dict(metric='anonymous_buyer_leads',value=len(cases),denominator='',meaning='2个经纪网站的客户自述去重'),
        dict(metric='verified_buyer_flow_cases',value=0,denominator=len(cases),meaning='缺完整起終城市、年份、产品/价格及独立成交佐证')]
    public_brokers=[]
    for b in broker:
        public_brokers.append({k:('; '.join(v)if isinstance(v,list)else v) for k,v in b.items() if k!='shared_upstream_warning'})
    out=a.public_out; priv=a.private_out
    write_csv(out/'crosscity_match_sensitivity.csv',sensitivity)
    write_csv(out/'crosscity_cost_marginal_scenarios.csv',marginal)
    write_csv(out/'crosscity_cost_synthetic_scenarios.csv',synthetic)
    write_csv(out/'crosscity_evidence_coverage.csv',coverage)
    write_csv(out/'crosscity_broker_opinions.csv',public_brokers)
    write_csv(out/'crosscity_buyer_evidence_gates.csv',cases)
    write_csv(priv/'all_candidate_pairs.csv',pairs)
    write_csv(priv/'proxy_pairs.csv',selected)
    write_csv(priv/'property_cost_review.csv',costs)
    save(priv/'buyer_leads.json',buyers)
    qa=dict(fingerprints_verified=len(paths),frozen_sales=25,eligible_sales=20,candidate_pairs=len(pairs),proxy_pairs=len(selected),full_quality_pairs=0,hoa_normalization_verified=True,unknown_costs_kept_missing=True,loan_formula_independent_decimal_checks=audit,synthetic_payment_checks=2,broker_authors=len(broker),firm_families=len({b['firm_family']for b in broker if b['firm_family']}),verified_flow_cases=0,source_snapshot_warning='Notes are not raw page bytes',review_model='same-thread independent arithmetic path; no second model or subagents')
    save(out/'crosscity_qa.json',qa)
    print(json.dumps(dict(public_tables=6,proxy_pairs=len(selected),complete_costs=0,verified_flow_cases=0),ensure_ascii=False))

if __name__=='__main__':
    main()
