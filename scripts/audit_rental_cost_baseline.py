#!/usr/bin/env python3
"""Independent closed-form arithmetic and substantive missing-data gates."""
import argparse,csv,json,math
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def main():
 a=argparse.ArgumentParser();a.add_argument('--private-out',type=Path,required=True);args=a.parse_args();checks=[];anchors=json.loads((args.private_out.parent/'audit_anchors.json').read_text())
 for r in read(args.private_out/'rental_purchase_matches.csv'):
  loan=float(r['sale_price_usd'])*.8;i=.06/12;n=360;k=12
  pay=loan*i*(1+i)**n/((1+i)**n-1)
  balance=loan*(1+i)**k-pay*((1+i)**k-1)/i
  principal=(loan-balance)/k;interest=pay-principal
  assert abs(pay-float(r['model_pi']))<.006
  assert abs(principal-float(r['model_principal_y1_month_avg']))<.006
  assert abs(interest-float(r['model_interest_y1_month_avg']))<.006
  assert r['full_cash_total']==r['full_economic_total']==''
  assert r['school_assignment_official']==r['quality_equivalence_verified']=='False'
  checks.append(r['match_id']+'_closed_form_matches_cent_rounding')
 obs=read(args.private_out/'rental_observations.csv');o={r['record_id']:r for r in obs}
 assert o['L013']['headline_monthly_usd']==str(anchors['refreshed_rent'])and o['L013']['status']=='asking_active_reported'
 assert o['L011']['status']==o['L015']['status']=='MLS_closed_reported'
 assert o['L015']['first_month_plus_known_deposits']==str(anchors['deposit_cash_anchor'])
 assert all(r['effective_all_in_rent']==''for r in obs)
 checks+=['refreshed_price_and_status_not_cached_search','deposit_not_recurring_rent','unknown_rental_total_remains_blank']
 c={r['record_id']:r for r in read(args.private_out/'property_cost_gaps.csv')}
 assert Decimal(c['T025']['hoa_mls_monthly'])==Decimal(anchors['mixed_hoa_anchor'])
 assert all(r['complete_cost']=='False'and r['insurance']==''and r['mello_roos']==''for r in c.values())
 checks+=['mixed_HOA_frequency_independent_anchor','insurance_and_MR_missing_gate']
 u=read(args.private_out/'rental_service_upgrades.csv');assert [r['observed_headline_difference']for r in u]==anchors['upgrade_anchors'];assert all(r['pure_bedroom_premium']==''for r in u)
 checks+=['service_upgrade_not_causal_bedroom_premium']
 q=json.loads((ROOT/'qa/rental_baseline_qa.json').read_text());assert q['closed_reported']+q['asking_reported']==q['observations']==18
 assert q['signed_leases']==q['renewals']==q['full_effective_rents']==q['complete_property_costs']==0
 checks+=['status_counts_and_completion_boundary']
 result=dict(status='passed',checks=checks,independent_method='Float closed-form balance vs Decimal month-by-month amortization; serial audit, not second-model review')
 (ROOT/'qa/rental_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
