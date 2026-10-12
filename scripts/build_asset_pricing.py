#!/usr/bin/env python3
"""Frozen public-market step 9; vendor/property rows are private outputs only."""
import argparse,csv,hashlib,json,math,pathlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
CITIES=['Irvine','Tustin','Lake Forest','Aliso Viejo']
NEIGHBORHOODS=['Stonegate','Orchard Hills','Portola Springs','Woodbury','Northwood','Stonegate East']
def read(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def csvout(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def pct(a,b):return (a/b-1)*100
def mortgage(price,ltv,rate):
 loan=price*ltv;m=rate/12;n=360;pmt=loan*m/(1-(1+m)**-n) if m else loan/n
 bal12=loan*(1+m)**12-pmt*((1+m)**12-1)/m if m else loan-pmt*12
 principal=loan-bal12;interest=12*pmt-principal
 return pmt,interest,principal
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',required=True,type=pathlib.Path);ap.add_argument('--private-out',required=True,type=pathlib.Path);ap.add_argument('--public-out',default=ROOT,type=pathlib.Path);a=ap.parse_args()
 manifest=read(ROOT/'data/pricing_source_manifest.json')
 for f in manifest['inputs']:
  p=a.evidence_dir/f['path']
  if hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:raise ValueError('Frozen input changed: '+f['path'])
 series=[];summary=[]
 for f in manifest['inputs']:
  if '_zhvi_' not in f['path']:continue
  product='four_bedroom' if 'bdrmcnt_4' in f['path'] else 'all_home'
  level='city' if pathlib.Path(f['path']).name.startswith('City') else 'neighborhood'
  with (a.evidence_dir/f['path']).open()as h:
   for r in csv.DictReader(h):
    if r.get('State')!='CA' or r['RegionName'] not in (CITIES if level=='city' else NEIGHBORHOODS):continue
    if level=='neighborhood' and r.get('City')!='Irvine':continue
    values={k:float(v) for k,v in r.items() if k[:4].isdigit() and v}
    dates=sorted(values);latest=dates[-1];ref=max((k for k in dates if '2024-01-01'<=k<='2025-12-31'),key=values.get)
    x=dict(geography=r['RegionName'],region_id=r['RegionID'],level=level,product=product,source_file=pathlib.Path(f['path']).name,values=values)
    series.append(x);v=values[latest]
    summary.append(dict(geography=x['geography'],level=level,product=product,latest=latest,value=v,aug2024=values['2024-08-31'],aug2025=values['2025-08-31'],yoy_pct=pct(v,values['2025-08-31']),two_year_pct=pct(v,values['2024-08-31']),reference_peak_date=ref,reference_peak_value=values[ref],change_from_2024_2025_peak_pct=pct(v,values[ref]),running_drawdown_pct=pct(v,max(values[k] for k in dates if k>='2024-01-01'))))
 county=[]
 with (a.evidence_dir/'raw/realtor_county_history.csv').open()as f:
  for r in csv.DictReader(f):
   if r['county_fips'].zfill(5)=='06059':county.append(r)
 county.sort(key=lambda x:x['month_date_yyyymm'])
 selected=[r for r in county if r['month_date_yyyymm'] in ['201909','202409','202509','202609']]
 assert len(series)==19 and len(selected)==4
 assert {s['latest'] for s in summary}=={'2026-08-31'}
 assert all(float(x['quality_flag'])==0 for x in selected)
 notes=read(a.evidence_dir/'private/pricing_notes.json');old=read(a.evidence_dir/'private/frozen/rental_notes.json');history=read(a.evidence_dir/'private/frozen/history_notes.json')
 timelines=[]
 for c in notes['cases']:
  events=[e for e in c['events'] if e[1] in ('listed','price','reported_sale','contingent','pending','removed') and e[0]>='2025-01-01']
  asks=[e for e in events if e[1] in ('listed','price')]
  end=next((e[0] for e in reversed(events) if e[1] in ('reported_sale','contingent','pending','removed')),notes['as_of'])
  if c['status']=='active':end=notes['as_of']
  timelines.append(dict(id=c['id'],address=c['address'],status=c['status'],first_ask=asks[0][2] if asks else None,last_ask=asks[-1][2]if asks else None,visible_ask_change_pct=pct(asks[-1][2],asks[0][2])if asks else None,first_visible_date=asks[0][0]if asks else None,end_date=end,calendar_span_days=(datetime.date.fromisoformat(end)-datetime.date.fromisoformat(asks[0][0])).days if asks else None,full_DOM=None,contract_price=None if c['status']!='sold' else next(e[2]for e in reversed(events)if e[1]=='reported_sale')))
 pairs=[]
 for spec in notes['comparison_specs']:
  row={k:spec[k]for k in ['id','current','comparison','restriction']}
  if 'denominator' in spec:row['delta_pct']=pct(spec['numerator'],spec['denominator'])
  else:row.update(delta_low_pct=pct(spec['numerator'],spec['denominator_high']),delta_high_pct=pct(spec['numerator'],spec['denominator_low']))
  pairs.append(row)
 rents=[]
 for spec in notes['rent_value_specs']:
  annual=12*spec['rent_monthly'];rents.append(dict(id=spec['id'],sale_id=spec['sale_id'],annual_rent=annual,price_low=spec['price_low'],price_high=spec['price_high'],gross_ratio_low_pct=annual/spec['price_high']*100,gross_ratio_high_pct=annual/spec['price_low']*100,rent_status=spec['rent_status'],full_net_yield=None))
 synthetic=[]
 # Every input fictional. First-year cost screen, not a DCF, forecast or household model.
 for rate in [.055,.065,.075]:
  P=1800000;rent=5500;ltv=.7;t=.011;maintenance=.005;k=.04;F=200*12+2500+3000;horizon=7;friction=.02+.05
  payment,interest,principal=mortgage(P,ltv,rate)
  recurring=t*P+maintenance*P+F;opp=(1-ltv)*P*k;amortized=P*friction/horizon
  cash=payment+recurring/12;economic=(interest+recurring+opp+amortized)/12
  coeff=interest/P+t+maintenance+(1-ltv)*k+friction/horizon
  for g in [0,.02,.04]:
   denominator=coeff-g;ceiling=(12*rent-F)/denominator if denominator>0 and 12*rent>F else None
   synthetic.append(dict(synthetic_only=True,price=P,rent_monthly=rent,ltv=ltv,mortgage_years=30,rate=rate,tax_rate=t,maintenance_rate=maintenance,hoa_monthly=200,MR_annual=2500,insurance_annual=3000,equity_opportunity_rate=k,friction_rate=friction,annualization_years=horizon,assumed_appreciation=g,payment_monthly=payment,first_year_interest=interest,first_year_principal=principal,recurring_cash_monthly=cash,economic_monthly_before_appreciation=economic,required_appreciation_at_input_price=(economic-rent)*12/P,conditional_price=ceiling,denominator=denominator))
 coverage=[dict(metric='downloaded_vendor_CSV',value=5,unit='files'),dict(metric='selected_ZHVI_series',value=len(series),unit='model_series_not_transactions'),dict(metric='county_months',value=len(county),unit='Orange_CA_months'),dict(metric='same_season_county_rows',value=len(selected),unit='September_cross_sections'),dict(metric='new_property_followups',value=len(notes['cases']),unit='purposively_selected_addresses'),dict(metric='old_sale_cohort_reused',value=len(old['sales']),unit='reported_closed_sales'),dict(metric='certified_2024_2025_to_2026_target_repeat_pairs',value=0,unit='pairs'),dict(metric='complete_target_inventory_denominator',value=0,unit='verified_denominators'),dict(metric='new_signed_leases',value=0,unit='documents'),dict(metric='real_complete_net_yield_cases',value=0,unit='cases')]
 for name,rows in [('zhvi_summary',summary),('county_same_season',selected),('listing_timelines',timelines),('synthetic',synthetic),('rent_value',rents)]:csvout(a.private_out/(name+'.csv'),rows)
 save(a.private_out/'analysis.json',dict(series=series,summary=summary,county=county,county_same_season=selected,timelines=timelines,pairs=pairs,rent_value=rents,synthetic=synthetic,new_cases=notes['cases'],prior_sales=old['sales']))
 csvout(a.public_out/'data/clean/pricing_coverage_20261012.csv',coverage)
 csvout(a.public_out/'data/clean/pricing_synthetic_conditions.csv',synthetic)
 save(a.public_out/'qa/pricing_build_checks.json',dict(input_fingerprints=len(manifest['inputs']),series_count=len(series),latest_zhvi='2026-08-31',latest_county=county[-1]['month_date_yyyymm'],selected_county_quality_flags=[float(r['quality_flag'])for r in selected],missing_is_not_zero=True,full_DOM_derived=False,absorption_rate_derived=False,real_net_yield_derived=False,synthetic_scenarios=len(synthetic)))
 print(json.dumps(dict(series=len(series),county_months=len(county),new_cases=len(notes['cases']),synthetic=len(synthetic))))
if __name__=='__main__':main()
