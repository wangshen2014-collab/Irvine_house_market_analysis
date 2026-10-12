#!/usr/bin/env python3
"""Step 11: frozen-vintage forecasts and explicitly synthetic loan boundaries."""
import argparse, pathlib, json, hashlib, csv, re, html, statistics, collections, subprocess
from html.parser import HTMLParser
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
  cells=[html.unescape(re.sub('<[^>]*>','',c)).strip()for c in re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>',tr,re.S)]
  if len(cells)==2 and re.fullmatch(r'\d{4}-\d{2}-\d{2}',cells[0]):rows.append(cells)
 rows+=re.findall(r'#(\d{4}-\d\d-\d\d)\|\s*([^\s<]+)',s)
 out={d:None if v=='.'else float(v.replace(',',''))for d,v in rows}
 span=re.search(r'(\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d)',s)
 assert len(rows)==len(out) and span and (min(out),max(out))==span.groups(),p
 return out
def groupmean(v,key):
 d=collections.defaultdict(list)
 for date,value in v.items():
  if value is not None:d[key(date)].append(value)
 return {k:statistics.mean(a)for k,a in d.items()}
def quarter(s):return s[:4]+'Q'+str((int(s[5:7])-1)//3+1)
def factor(rate,n=360):
 m=rate/1200
 return m/(1-(1+m)**-n)if m else 1/n
def balance(p,rate,n,k):
 m=rate/1200;a=p*factor(rate,n)
 return p*(1+m)**k-a*((1+m)**k-1)/m if m else p-a*k
def loan(p,rate,n,k):
 a=p*factor(rate,n);b=balance(p,rate,n,k)
 return dict(payment=a,balance=b,cumulative_payments=k*a,cumulative_interest=k*a-(p-b))
def forecastrow(path,label):
 lines=path.read_text().splitlines();line=next(x for x in lines if label in x)
 return [float(x.replace(',',''))for x in re.findall(r'-?\d[\d,]*\.?\d*',line.split(label,1)[1])]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',required=True,type=pathlib.Path);ap.add_argument('--private-out',required=True,type=pathlib.Path);ap.add_argument('--public-out',type=pathlib.Path,default=ROOT);a=ap.parse_args();e=a.evidence_dir;out=a.private_out;pub=a.public_out
 manifest=read(ROOT/'data/scenario_source_manifest.json');design=read(ROOT/'data/scenario_analysis_design.json')
 for f in manifest['inputs']:
  assert hashlib.sha256((e/f['path']).read_bytes()).hexdigest()==f['sha256'],'Frozen input changed: '+f['path']
 mort=fred(e/'private/frozen/fred_MORTGAGE30US.html');gs10=fred(e/'private/frozen/fred_GS10.html');mm=groupmean(mort,lambda d:d[:7]);qm=groupmean(mort,quarter)
 daily={s:fred(e/f'raw/fred_{s}.html')for s in ['DGS1','DGS2','DGS5','DGS10','DGS3MO','DFII10','T10YIE']}
 common=sorted(set.intersection(*[{k for k,v in vs.items()if v is not None}for vs in daily.values()]));date=common[-1]
 market=[{'series':s,'date':date,'percent':vs[date],'type':'market constant maturity yield; not forward forecast'}for s,vs in daily.items()]
 coverage=[dict(series=s,first=min(v),last=max(v),observations=len(v),nonmissing=sum(x is not None for x in v.values()))for s,v in dict(MORTGAGE30US=mort,GS10=gs10,**daily).items()]
 forecasts=[]
 for fn,inst,vintage,cutoff,periods in [
 ('fannie_202509_housing.txt','Fannie Mae','2025-09-11','2025-08-29',[f'{y}Q{q}'for y in [2024,2025,2026]for q in range(1,5)]+['2024 annual','2025 annual','2026 annual']),
 ('fannie_202609_housing.txt','Fannie Mae','2026-09-11','2026-08-31',[f'{y}Q{q}'for y in [2025,2026,2027]for q in range(1,5)]+['2025 annual','2026 annual','2027 annual']),
 ('mba_202605.txt','MBA','2026-05-15',None,[f'{y}Q{q}'for y in [2025,2026,2027]for q in range(1,5)]+['2025 Q4','2026 Q4','2027 Q4','2028 Q4']),
 ('mba_202609.txt','MBA','2026-09-16',None,[f'{y}Q{q}'for y in [2025,2026,2027]for q in range(1,5)]+['2025 Q4','2026 Q4','2027 Q4','2028 Q4']),
 ('mba_current_download.txt','MBA','2026-10-11',None,[f'{y}Q{q}'for y in [2026,2027,2028]for q in range(1,5)]+['2025 Q4','2026 Q4','2027 Q4','2028 Q4','2029 Q4'])]:
  vals=forecastrow(e/'private'/fn,'30-Year Fixed Rate Mortgage');assert len(vals)==len(periods),(fn,len(vals))
  for i,(period,value)in enumerate(zip(periods,vals)):
   forecasts.append(dict(institution=inst,vintage=vintage,rate_information_cutoff=cutoff,period=period,mortgage_rate_pct=value,annual_column_basis='annual average'if inst=='Fannie Mae'else 'Q4 average',column=i,source=fn))
 errors=[]
 for cohort in design['forecast_error_cohorts']:
  for q in cohort['quarters']:
   r=next(x for x in forecasts if x['institution']==cohort['institution']and x['vintage']==cohort['vintage']and x['period']==q)
   qs=q[:4]+'-'+str((int(q[-1])-1)*3+1).zfill(2)+'-01';assert r['vintage']<qs
   vals=[v for d,v in mort.items()if quarter(d)==q and v is not None]
   errors.append(dict(institution=r['institution'],vintage=r['vintage'],quarter=q,forecast_pct=r['mortgage_rate_pct'],actual_pct=qm[q],error_pp=qm[q]-r['mortgage_rate_pct'],weekly_observations=len(vals),forecast_precedes_quarter=True))
 history=[{'month':m,'mortgage_pct':v,'ten_year_pct':gs10[m+'-01'],'spread_pp':v-gs10[m+'-01']}for m,v in mm.items()if '2000-01'<=m<='2026-09'and 4<=v<5]
 hist_summary={'months':len(history),'first':min(x['month']for x in history),'last':max(x['month']for x in history),'ten_year_range':[min(x['ten_year_pct']for x in history),max(x['ten_year_pct']for x in history)],'spread_range':[min(x['spread_pp']for x in history),max(x['spread_pp']for x in history)],'not_forward_probability':True}
 grid=[]
 for y in design['four_handle_condition']['ten_year_grid_pct']:
  for s in design['four_handle_condition']['spread_grid_pp']:grid.append(dict(synthetic_only=True,ten_year_pct=y,spread_pp=s,mortgage_pct=y+s,in_four_handle=4<=y+s<5))
 z=design['payment_sensitivity'];r0=z['initial_rate_pct'];d=z['initial_down_fraction'];p0=z['initial_price_index'];base=(1-d)*p0*factor(r0)
 sensitive=[];boundaries=[]
 for rate in z['future_rates_pct']:
  for price in z['future_price_indices']:
   sensitive.append(dict(synthetic_only=True,rate_pct=rate,price_index=price,fixed_cash_PI_change_pct=100*((price-d*p0)*factor(rate)/base-1),fixed_fraction_PI_change_pct=100*((1-d)*price*factor(rate)/base-1)))
  ratio=factor(r0)/factor(rate);boundaries.append(dict(synthetic_only=True,rate_pct=rate,PI_per_100k=100000*factor(rate),fixed_cash_equal_PI_price_index=p0*(d+(1-d)*ratio),fixed_fraction_equal_PI_price_index=p0*ratio))
 l=design['loan_math'];p=l['normalization_principal_usd'];rr=l['fixed_rate_pct'];point_rate=l['points_lower_rate_pct'];cost=p*l['points_fraction'];points=[]
 for k in l['horizons_months']:
  x,y=loan(p,rr,360,k),loan(p,point_rate,360,k)
  points.append(dict(synthetic_normalization=True,months=k,upfront_extra_cost=cost,monthly_PI_saving=x['payment']-y['payment'],cash_saving_net_cost=k*(x['payment']-y['payment'])-cost,remaining_balance_saving=x['balance']-y['balance'],interest_saving_net_cost=x['cumulative_interest']-y['cumulative_interest']-cost))
 points_be={'simple_cash_months':cost/(p*(factor(rr)-factor(point_rate))),'undiscounted_interest_break_even_first_month':next(k for k in range(1,361)if loan(p,rr,360,k)['cumulative_interest']-loan(p,point_rate,360,k)['cumulative_interest']>=cost),'not_full_APR_or_NPV':True}
 arm=[];b=p;cumulative=0;intcum=0;rate=l['arm_initial_rate_pct'];initial=rate;payment=p*factor(rate)
 for month in range(1,361):
  if month>60 and (month-61)%12==0:rate=min(initial+l['arm_caps_pp'][2],rate+2);payment=b*factor(rate,361-month)
  interest=b*rate/1200;b-=payment-interest;cumulative+=payment;intcum+=interest
  if month in [1,60,61,72,73,84,85,96,120,360]:arm.append(dict(synthetic_cap_stress=True,month=month,rate_pct=rate,payment=payment,balance=b,cumulative_payments=cumulative,cumulative_interest=intcum))
 k=l['refinance_at_month'];old=loan(p,rr,360,k);bal=old['balance'];fee=bal*l['refinance_cost_fraction'];refi=[]
 for n in l['refinance_new_term_months']:
  nr=l['refinance_rate_pct'];pay=bal*factor(nr,n)
  for months_after in [12,24,60]:
   new=loan(bal,nr,n,months_after);kept=loan(bal,rr,360-k,months_after)
   refi.append(dict(synthetic_only=True,months_after_refi=months_after,new_term_months=n,refi_balance=bal,upfront_cash_fee=fee,old_payment=old['payment'],new_payment=pay,cash_saving_net_cost=(old['payment']-pay)*months_after-fee,interest_saving_net_cost=kept['cumulative_interest']-new['cumulative_interest']-fee,remaining_balance_extra=new['balance']-kept['balance'],new_lifetime_interest=pay*n-bal,old_remaining_lifetime_interest=old['payment']*(360-k)-bal))
 anomalies=[]
 for name,rate,years,stated in [('CU SoCal high balance 30y',8.625,30,9.92),('CU SoCal high balance 15y',7.25,15,6.82),('CU SoCal jumbo 15y',6.75,15,6.49)]:
  calculated=1000*factor(rate,12*years);anomalies.append(dict(source='cusocal_rates.html',field=name,rate_pct=rate,years=years,stated_PI_per_1000=stated,calculated_PI_per_1000=calculated,difference=stated-calculated,status='unresolved_source_discrepancy; not corrected silently'))
 result=dict(as_of=design['as_of'],market=market,coverage=coverage,forecasts=forecasts,forecast_errors=errors,four_handle_history_summary=hist_summary,four_handle_history=history,four_handle_grid=grid,payment_grid=sensitive,equal_payment_boundaries=boundaries,points=points,points_break_even=points_be,arm_cap_stress=arm,refinance=refi,source_anomalies=anomalies,interpretation={'personal_quotes_obtained':0,'local_causal_price_elasticity':None,'scenario_probabilities':None,'timing_advantage':None})
 save(out/'analysis.json',result)
 for key in ['market','coverage','forecasts','forecast_errors','four_handle_history','four_handle_grid','payment_grid','equal_payment_boundaries','points','arm_cap_stress','refinance','source_anomalies']:csvout(out/(key+'.csv'),result[key])
 for key in ['four_handle_grid','payment_grid','equal_payment_boundaries','points','arm_cap_stress','refinance']:csvout(pub/'data/clean'/('scenario_'+key+'.csv'),result[key])
 save(pub/'qa/scenario_build_checks.json',{'status':'passed','frozen_inputs':len(manifest['inputs']),'coverage':coverage,'forecast_error_rows':len(errors),'forecasts_extracted':len(forecasts),'source_discrepancies':len(anomalies),'personal_quotes':0,'not_independent_model_review':True})
 print(json.dumps({k:result[k]for k in ['market','forecast_errors','four_handle_history_summary','equal_payment_boundaries','points_break_even','arm_cap_stress','refinance']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
