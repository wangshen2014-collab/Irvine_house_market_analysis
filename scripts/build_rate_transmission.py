#!/usr/bin/env python3
"""Step 10: reproducible frozen-source analysis; source histories remain private."""
import argparse,csv,hashlib,html,json,math,pathlib,re,statistics,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def csvout(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def fred(p):
 s=p.read_text();rows=[]
 for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>',s,re.S):
  c=[html.unescape(re.sub('<[^>]*>','',x)).strip() for x in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',tr,re.S)]
  if len(c)==2 and re.fullmatch(r'\d{4}-\d{2}-\d{2}',c[0]):rows.append(c)
 # FRED's displayed table stops at 1,000, but the public HTML contains remaining rows.
 rows+=re.findall(r'#(\d{4}-\d\d-\d\d)\|\s*([^\s<]+)',s)
 out={d:None if v=='.' else float(v.replace(',',''))for d,v in rows}
 if len(out)!=len(rows):raise ValueError('Duplicate date '+p.name)
 declared=re.search(r'(\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d)',s)
 if not declared or (min(out),max(out))!=declared.groups():raise ValueError('Truncated source '+p.name)
 return out
def monthly(d):
 bins=collections.defaultdict(list)
 for k,v in d.items():
  if v is not None:bins[k[:7]].append(v)
 return {k:statistics.mean(v)for k,v in bins.items()}
def shift(m,n):
 y,z=map(int,m.split('-'));j=y*12+z-1+n;return f'{j//12:04d}-{j%12+1:02d}'
def factor(r):
 m=r/1200
 return m/(1-(1+m)**-360) if m else 1/360
def change(a,b):return 100*(a/b-1)
def correlation(x,y):
 if len(x)<12:return None
 mx=statistics.mean(x);my=statistics.mean(y);ssx=sum((v-mx)**2 for v in x);ssy=sum((v-my)**2 for v in y)
 return sum((a-mx)*(b-my)for a,b in zip(x,y))/math.sqrt(ssx*ssy) if ssx and ssy else None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=pathlib.Path,required=True);ap.add_argument('--private-out',type=pathlib.Path,required=True);ap.add_argument('--public-out',type=pathlib.Path,default=ROOT);a=ap.parse_args()
 manifest=read(ROOT/'data/rate_source_manifest.json');design=read(ROOT/'data/rate_analysis_design.json')
 for f in manifest['inputs']:
  if hashlib.sha256((a.evidence_dir/f['path']).read_bytes()).hexdigest()!=f['sha256']:raise ValueError('Frozen input changed: '+f['path'])
 source={f['series']:fred(a.evidence_dir/f['path'])for f in manifest['inputs']if 'series'in f}
 mm={k:monthly(v)for k,v in source.items()};mort=mm['MORTGAGE30US'];base=read(a.evidence_dir/'private/frozen/pricing_analysis.json')
 prices={s['geography']+'|'+s['product']:{k[:7]:v for k,v in s['values'].items()}for s in base['series']}
 coverage=[dict(series=k,first=min(v),last=max(v),observations=len(v),nonmissing=sum(x is not None for x in v.values()),frequency='quarterly'if k.startswith('ATNHPI')or k=='USSTHPI' else ('weekly'if k=='MORTGAGE30US'else 'daily'if k in ['DFII10','T10YIE','SP500']else 'monthly'))for k,v in source.items()]
 cycles=[]
 for window,start,end in design['windows']:
  r0,r1=mort[start],mort[end];q=factor(r0)/factor(r1)
  for key,vals in prices.items():
   valid=start in vals and end in vals
   p=vals[end]/vals[start] if valid else None
   cycles.append(dict(window=window,start=start,end=end,series=key,rate_start_pct=r0,rate_end_pct=r1,rate_change_pp=r1-r0,nominal_price_change_pct=100*(p-1)if valid else None,real_price_change_pct=100*(p*mm['CPIAUCSL'][start]/mm['CPIAUCSL'][end]-1)if valid else None,equal_PI_fixed_percent_change_pct=100*(q-1),equal_PI_fixed_dollars_20pct_change_pct=100*(.2+.8*q-1),same_LTV_PI_change_pct=100*(p/q-1)if valid else None))
 corr=[]
 for window,start,end in design['windows']:
  for key,vals in prices.items():
   for lag in design['lag_months']:
    pairs=[]
    for t in sorted(mort):
     prior=shift(t,-1);target=shift(t,lag);prev=shift(target,-1)
     if not(start<=prior<t<=end and start<=prev<target<=end):continue
     if prior in mort and target in vals and prev in vals:pairs.append((mort[t]-mort[prior],100*math.log(vals[target]/vals[prev])))
    corr.append(dict(window=window,series=key,lag_months=lag,n=len(pairs),correlation=correlation([x[0]for x in pairs],[x[1]for x in pairs])))
 synthetic=[]
 for r0,r1 in design['synthetic_rate_pairs_percent']:
  for d in design['synthetic_downpayment_fractions']:
   q=factor(r0)/factor(r1);P=100;B=P*(1-d)*factor(r0)
   synthetic.append(dict(synthetic_only=True,start_rate_pct=r0,end_rate_pct=r1,initial_price_index=P,down_fraction=d,monthly_PI_index=B,fixed_percent_price_index=100*q,fixed_dollars_price_index=100*(d+(1-d)*q)))
 county={r['month_date_yyyymm'][:4]+'-'+r['month_date_yyyymm'][4:]:r for r in base['county']}
 annual=[]
 for year in range(2017,2027):
  cut='08' if year==2026 else '12';rows=[r for m,r in county.items()if m[:4]==str(year)and m[5:]<=cut]
  if len(rows)!=int(cut):raise ValueError('Missing county month')
  pending=[float(r['pending_listing_count'])for r in rows if r['pending_listing_count']];flags=[float(r['quality_flag'])for r in rows if r['quality_flag']]
  annual.append(dict(year=year,months=len(rows),new_listings_sum=sum(int(r['new_listing_count'])for r in rows),active_listings_monthly_mean=statistics.mean(int(r['active_listing_count'])for r in rows),pending_stock_monthly_mean=statistics.mean(pending)if pending else None,pending_observed_months=len(pending),quality_flag_max=max(flags)if flags else None,quality_flag_observed_months=len(flags)))
 county_comp=[]
 for start,end in [('2021-12','2023-12'),('2019-08','2026-08'),('2025-08','2026-08')]:
  z=dict(start=start,end=end)
  for f in ['active_listing_count','new_listing_count','pending_listing_count']:
   p0=county[start].get(f);p1=county[end].get(f);z[f+'_change_pct']=change(float(p1),float(p0))if p0 and p1 and float(p0)else None
  county_comp.append(z)
 quarters=[]
 for series in ['ATNHPIUS11244Q','USSTHPI']:
  for start,end in [('2006-10-01','2012-10-01'),('2019-10-01','2021-10-01'),('2021-10-01','2023-10-01'),('2023-04-01','2026-04-01')]:
   quarters.append(dict(series=series,start_quarter=start,end_quarter=end,change_pct=change(source[series][end],source[series][start])))
 lock=read(a.evidence_dir/'private/fhfa_selected.json');locklatest=[]
 for geo,rows in lock.items():
  r=rows[-1];locklatest.append(dict(geography={'Overall':'US','State':'CA','County':'Orange County, CA (06059)'}[geo],year=r['Year'],quarter=r['Quarter'],fixed_rate_pct=r['Fixed_Rate'],predicted_new_rate_pct=r['New_Rate'],rate_delta_pp=r['Rate_Delta'],share_new_rate_over_old_by_gt2_pct=100*(r['Delta_lt_neg3']+r['Delta_neg3_neg2']),reorigination_PI_change_pct=100*r['Payment_Change_Percent'],model_relative_sale_probability_change_pct=100*r['Lock_In_Effect'],model_cumulative_sales_change=r['Sales_Change_Since_2022Q2'],source_vintage='FHFA WP24-03 August 2024 developmental aggregates',not_current_observation=True))
 latest={k:dict(date=max(v),value=v[max(v)])for k,v in source.items()};snapshots=[]
 for month in ['2006-12','2012-12','2019-12','2021-12','2023-12','2026-08','2026-09']:
  z={'month':month}
  for k,v in mm.items():z[k]=v.get(month)
  z['mortgage_minus_10y_pp']=z['MORTGAGE30US']-z['GS10'];snapshots.append(z)
 quality_sensitivity=[]
 for y0,y1,stop in [(2021,2023,12),(2019,2026,8),(2025,2026,8)]:
  good=[m for m in range(1,stop+1)if all(county[f'{y}-{m:02d}']['quality_flag'] in ['0','0.0']for y in [y0,y1])]
  a0=sum(int(county[f'{y0}-{m:02d}']['new_listing_count'])for m in good);a1=sum(int(county[f'{y1}-{m:02d}']['new_listing_count'])for m in good)
  quality_sensitivity.append(dict(start_year=y0,end_year=y1,matched_month_numbers=','.join(map(str,good)),months=len(good),new_listings_start_sum=a0,new_listings_end_sum=a1,new_listings_change_pct=change(a1,a0),method='both years quality_flag zero and same calendar months; no fill'))
 method_break=[]
 for key,vals in prices.items():
  for lag in design['lag_months']:
   pairs=[]
   for t in sorted(mort):
    prev=shift(t,-1);u=shift(t,lag);v=shift(u,-1)
    if not('2021-12'<=prev<t<='2023-12'and '2021-12'<=v<u<='2023-12'):continue
    if any('2022-10'<=z<='2022-12'for z in [prev,t,v,u]):continue
    if u in vals and v in vals:pairs.append((mort[t]-mort[prev],100*math.log(vals[u]/vals[v])))
   method_break.append(dict(window='hiking_excluding_2022Q4_touched_pairs',series=key,lag_months=lag,n=len(pairs),correlation=correlation([x[0]for x in pairs],[x[1]for x in pairs])))
 out=dict(coverage=coverage,monthly=mm,prices=prices,cycles=cycles,correlations=corr,synthetic=synthetic,county_annual=annual,county_comparisons=county_comp,county_quality_sensitivity=quality_sensitivity,method_break_sensitivity=method_break,quarterly_comparisons=quarters,lockin=locklatest,latest=latest,snapshots=snapshots)
 save(a.private_out/'analysis.json',out)
 for n in ['coverage','cycles','correlations','synthetic','county_annual','county_comparisons','county_quality_sensitivity','method_break_sensitivity','quarterly_comparisons','lockin','snapshots']:csvout(a.private_out/(n+'.csv'),out[n])
 # Only self-authored calculations/coverage plus explicitly reusable FHFA aggregate extract.
 csvout(a.public_out/'data/clean/rate_coverage_20261012.csv',coverage);csvout(a.public_out/'data/clean/rate_synthetic_buying_power.csv',synthetic);csvout(a.public_out/'data/clean/rate_fhfa_lockin_2024q2.csv',locklatest)
 save(a.public_out/'qa/rate_build_checks.json',dict(frozen_inputs=len(manifest['inputs']),fred_series=len(source),fred_date_ranges_verified=True,zhvi_series=len(prices),cycle_rows=len(cycles),correlation_rows=len(corr),synthetic_rows=len(synthetic),county_months=len(county),causal_elasticity_estimated=False,monthly_cutoff='2026-08',quarterly_hpi_end='2026Q2',lockin_vintage='August 2024',missing_imputed=False))
 print(json.dumps(dict(cycles=len(cycles),correlations=len(corr),frozen_inputs=len(manifest['inputs']))))
if __name__=='__main__':main()
