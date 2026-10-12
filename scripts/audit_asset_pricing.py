#!/usr/bin/env python3
"""Serial independent arithmetic checks; not independent-agent or causal review."""
import argparse,csv,json,pathlib,decimal,datetime
D=decimal.Decimal;decimal.getcontext().prec=45
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence-dir',type=pathlib.Path,required=True);p.add_argument('--private-out',type=pathlib.Path,required=True);p.add_argument('--public-out',type=pathlib.Path,default=R);a=p.parse_args()
 x=json.loads((a.private_out/'analysis.json').read_text());checks=0
 by_file={}
 for s in x['summary']:
  v=next(z for z in x['series'] if z['geography']==s['geography'] and z['product']==s['product']);by_file.setdefault(v['source_file'],{})[v['region_id']]=s
 for filename,ids in by_file.items():
  with (a.evidence_dir/'raw'/filename).open()as f:
   for row in csv.DictReader(f):
    if row['RegionID'] not in ids:continue
    s=ids[row['RegionID']];now=D(row['2026-08-31']);prior=D(row['2025-08-31']);old=D(row['2024-08-31'])
    peak=max(D(v)for k,v in row.items()if '2024-01-01'<=k<='2025-12-31' and v)
    for key,expected in [('value',now),('yoy_pct',(now-prior)/prior*100),('two_year_pct',(now-old)/old*100),('change_from_2024_2025_peak_pct',(now-peak)/peak*100)]:
     assert abs(D(str(s[key]))-expected)<D('0.000001');checks+=1
    assert row['State']=='CA';checks+=1
 county={r['month_date_yyyymm']:r for r in x['county']}
 reconciliation=[]
 for key in ['active_listing_count','new_listing_count','pending_listing_count','price_reduced_count','median_listing_price','median_square_feet']:
  yy=(D(county['202609'][key])/D(county['202509'][key])-1)
  delta=abs(yy-D(county['202609'][key+'_yy']))
  reconciliation.append(dict(field=key,recomputed_ratio=str(yy),source_ratio=county['202609'][key+'_yy'],within_rounding_tolerance=delta<D('.00011')));checks+=1
 assert sum(not z['within_rounding_tolerance']for z in reconciliation)==1
 assert not reconciliation[-1]['within_rounding_tolerance']
 (a.private_out/'county_yoy_reconciliation.json').write_text(json.dumps(reconciliation,indent=2)+'\n')
 for s in x['synthetic']:
  loan=D(str(s['price']))*D(str(s['ltv']));m=D(str(s['rate']))/12
  payment=loan*m*(1+m)**360/((1+m)**360-1);balance=loan;interest=D(0)
  for month in range(12):
   i=balance*m;interest+=i;balance+=i-payment
  for key,expected in [('payment_monthly',payment),('first_year_interest',interest),('first_year_principal',loan-balance)]:
   assert abs(D(str(s[key]))-expected)<D('.01');checks+=1
  P=D(str(s['conditional_price']));fixed=D(7900);coeff=D(str(s['denominator']))
  assert abs(P*coeff+fixed-D(66000))<D('.01');checks+=1
  assert s['synthetic_only'] is True
 assert all(c['full_DOM']is None for c in x['timelines'])
 assert all(r['full_net_yield']is None for r in x['rent_value'])
 assert next(c for c in x['timelines']if c['id']=='P04')['contract_price']is None
 for c in x['timelines']:
  assert c['calendar_span_days']==(datetime.date.fromisoformat(c['end_date'])-datetime.date.fromisoformat(c['first_visible_date'])).days
 av=next(s for s in x['summary']if s['geography']=='Aliso Viejo'and s['product']=='four_bedroom')
 assert av['change_from_2024_2025_peak_pct']>0 and av['running_drawdown_pct']==0
 result=dict(status='pass_with_source_discrepancy_retained',independent_numerical_checks=checks,source_yoy_comparisons=6,source_yoy_beyond_rounding_tolerance=1,source_discrepancy_policy='median_square_feet YoY differs from current-vintage levels; use level-based calculation, retain source field, no fabricated reconciliation',controls=['CA geography','same August comparison','county September source YoY comparison','Decimal amortization versus closed-form balances','conditional price substituted into annual cost equation','contingent price stays unknown','calendar span not DOM','positive reference-peak change not negative drawdown','no real full net yield'],reviewer='same-agent serial arithmetic and evidence checks',independent_model_review=False)
 q=a.public_out/'qa/pricing_independent_arithmetic.json';q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
