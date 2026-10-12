#!/usr/bin/env python3
"""Phase 11: private rental facts, public diagnostics and synthetic arithmetic only."""
import argparse,csv,json,hashlib
from pathlib import Path
from decimal import Decimal,getcontext
from collections import Counter
from datetime import date
getcontext().prec=40
ROOT=Path(__file__).resolve().parents[1]
D=lambda x:Decimal(str(x))
def mortgage(principal,rate,months=360):
 p,r=D(principal),D(rate)/12
 payment=p/months if r==0 else p*r/(1-(1+r)**(-months))
 bal=p;interest=D(0)
 for _ in range(12):
  i=bal*r;interest+=i;bal-=payment-i
 return dict(payment=payment,interest_month_avg=interest/12,principal_month_avg=(p-bal)/12,balance_after12=bal)
def hoa(parts):
 if not parts:return None
 factors={'monthly':D(1),'quarterly':D(1)/3,'annual':D(1)/12}
 return sum((D(x['amount'])*factors[x['frequency']]for x in parts),D(0))
def money(x):return None if x is None else str(D(x).quantize(D('.01')))
def csvout(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def jsout(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--evidence-dir',type=Path,required=True);a.add_argument('--public-out',type=Path,default=ROOT);a.add_argument('--private-out',type=Path,required=True);args=a.parse_args();W=args.evidence_dir;O=args.public_out;P=args.private_out
 manifest=json.loads((ROOT/'data/rental_source_manifest.json').read_text())
 for x in manifest['files']:
  if x.get('sha256'):
   p=W/x['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],f"Input fingerprint mismatch: {x['path']}"
 d=json.loads((W/'private/rental_notes.json').read_text());ls=d['leases'];sales={r['record_id']:r for r in d['sales']};leases={r['record_id']:r for r in ls};cn={r['record_id']:r for r in d['cost_notes']}
 assert len({r['record_id']for r in ls})==len(ls)
 for r in ls:
  assert r['status'] in {'MLS_closed_reported','asking_active_reported'} and r['source_urls']
  assert date.fromisoformat(r['event_date'])<=date.fromisoformat(d['as_of'])
  assert r['bedrooms'] in (3,4) and r['living_area_sqft']>1650 and r['year_built']>2010
  assert r['effective_all_in_rent'] is None and not r['signed_lease_verified']
 rows=[]
 for r in ls:
  dep=[r.get(k)for k in ['deposit','key_deposit','other_deposit']];known=sum(x for x in dep if x is not None)
  rows.append(dict(record_id=r['record_id'],address=r['address'],city=r['city'],community=r['community_claimed'],bedrooms=r['bedrooms'],sqft=r['living_area_sqft'],year_built=r['year_built'],status=r['status'],event_date=r['event_date'],date_basis=r['date_basis'],observed_date=r['observed_date'],headline_monthly_usd=r['amount'],lease_term=r['lease_term'],furnished=r['furnished'],rent_includes=r['rent_includes'],advertised_deposit=r['deposit'],known_deposits_excluding_pets=known if any(x is not None for x in dep)else None,first_month_plus_known_deposits=r['amount']+known if r['deposit'] is not None else None,effective_all_in_rent=None,available_date=r.get('available_date'),notes=r['notes'],source_urls=' | '.join(r['source_urls'])))
 csvout(P/'rental_observations.csv',rows)
 matches=[]
 for m in d['matches']:
  s,l=sales[m['sale_id']],leases[m['lease_id']];h=hoa(cn.get(s['record_id'],{}).get('hoa_override')or s['hoa_components']);mo=mortgage(D(s['amount'])*D('.8'),'.06');base=D(s['amount'])*D('.01')/12
  cash=None if h is None else mo['payment']+base+h;econ=None if h is None else mo['interest_month_avg']+base+h
  matches.append(dict(**m,sale_address=s['address'],lease_address=l['address'],sale_date=s['close_date'],lease_reference_date=l['event_date'],date_gap_days=abs((date.fromisoformat(s['close_date'])-date.fromisoformat(l['event_date'])).days),bedrooms_sale=s['bedrooms'],bedrooms_lease=l['bedrooms'],area_gap_pct=money((D(l['living_area_sqft'])/s['living_area_sqft']-1)*100),sale_price_usd=s['amount'],rent_headline_usd_month=l['amount'],hoa_mls_usd_month=money(h),model_rate='0.06',model_down_payment_share='0.20',model_term_months=360,model_pi=money(mo['payment']),model_interest_y1_month_avg=money(mo['interest_month_avg']),model_principal_y1_month_avg=money(mo['principal_month_avg']),model_base_tax_month=money(base),model_cash_partial=money(cash),model_economic_partial=money(econ),partial_cash_minus_headline_rent=money(None if cash is None else cash-l['amount']),full_cash_total=None,full_economic_total=None,unknown_additions='voted_debt;MR;other_assessments;insurance;maintenance;utilities_difference;fees;one_off_costs',school_assignment_official=False,quality_equivalence_verified=False))
 csvout(P/'rental_purchase_matches.csv',matches)
 upgrades=[]
 for u in d['upgrade_pairs']:
  x,y=leases[u['from_id']],leases[u['to_id']]
  upgrades.append(dict(**u,observed_headline_difference=y['amount']-x['amount'],area_change_pct=money((D(y['living_area_sqft'])/x['living_area_sqft']-1)*100),pure_bedroom_premium=None))
 csvout(P/'rental_service_upgrades.csv',upgrades)
 costs=[]
 for n in d['cost_notes']:
  r=sales[n['record_id']];h=hoa(n.get('hoa_override')or r['hoa_components'])
  costs.append(dict(record_id=r['record_id'],address=r['address'],community=r['community_claimed'],hoa_mls_monthly=money(h),verified_newbuyer_tax=None,mello_roos=None,insurance=None,maintenance=None,hoa_special_assessment=None,official_parcel_fire_zone=None,complete_cost=False,hoa_basis='historical_MLS_not_current_HOA_certificate',source_url=n['source_url']))
 csvout(P/'property_cost_gaps.csv',costs)
 counts=Counter((r['city'],r['community_claimed'].replace('Reserve at Orchard Hills','Reserve'),r['bedrooms'],r['status'])for r in ls)
 csvout(O/'data/clean/rental_coverage_20261012.csv',[dict(city=c,community=g,bedrooms=b,status=s,observations=n,sampling='purposive_not_market_inventory')for(c,g,b,s),n in sorted(counts.items())])
 sr=[]
 for r in ls:
  for url in r['source_urls']:sr.append(dict(record_id=r['record_id'],source_url=url,observed_date=r['observed_date'],access='individual_public_page_review',upstream='CRMLS_syndication_not_independent_signed_lease',publication='link_only'))
 csvout(O/'data/rental_source_index.csv',sr)
 synthetic=[]
 for rate in ['.04','.06','.08']:
  for maint in ['.005','.01']:
   mo=mortgage(800000,rate);tax=D(1000000)*D('.011')/12;h=D(250);mt=D(1000000)*D(maint)/12
   synthetic.append(dict(scenario='synthetic_not_quote_or_household',price_usd=1000000,down_payment_share='.20',rate=rate,term_months=360,ad_valorem_assumption='.011',HOA_assumption=250,maintenance_fraction_of_price=maint,pi=money(mo['payment']),interest_y1_month_avg=money(mo['interest_month_avg']),principal_y1_month_avg=money(mo['principal_month_avg']),tax_assumption_month=money(tax),maintenance_allowance_month=money(mt),partial_cash_reserve_budget=money(mo['payment']+tax+h+mt),partial_economic_cost=money(mo['interest_month_avg']+tax+h+mt),insurance=None,special_assessments=None,full_cost=None))
 csvout(O/'data/clean/rental_cost_synthetic_sensitivity.csv',synthetic)
 q=dict(as_of=d['as_of'],observations=len(ls),new_observations=11,historical_observations=7,closed_reported=sum(r['status']=='MLS_closed_reported'for r in ls),asking_reported=sum(r['status']=='asking_active_reported'for r in ls),signed_leases=0,renewals=0,full_effective_rents=0,official_school_assignments=0,excluded_candidates=len(d['excluded']),candidate_matches=len(matches),same_address_pairs=sum(m['classification'].startswith('same_address')for m in matches),strict_same_quality_matches=0,known_lease_terms=sum(r['lease_term'] is not None for r in ls),unfurnished_consistent=sum(r['furnished']=='Unfurnished_mls_reported'for r in ls),future_advertised_availability=sum(bool(r.get('available_date')and r['available_date']>d['as_of'])for r in ls),cost_properties=len(costs),complete_property_costs=0,input_fingerprints_verified=sum(bool(x.get('sha256'))for x in manifest['files']),unknowns_not_zero=True)
 jsout(O/'qa/rental_baseline_qa.json',q);jsout(P/'build_log.json',q);print(json.dumps(q))
if __name__=='__main__':main()
