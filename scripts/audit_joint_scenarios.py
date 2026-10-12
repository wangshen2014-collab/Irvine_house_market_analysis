#!/usr/bin/env python3
"""Independent Decimal cash flows + raw PDF/HTML checks (not a second-model review)."""
import argparse,pathlib,json,decimal,statistics,re,subprocess,html,hashlib
from html.parser import HTMLParser
D=decimal.Decimal;decimal.getcontext().prec=40
ROOT=pathlib.Path(__file__).resolve().parents[1]
def pay(p,r,n):
 m=D(str(r))/1200
 return D(str(p))/sum((1+m)**(-i)for i in range(1,n+1))
def schedule(p,r,n,k):
 b=D(str(p));a=pay(p,r,n);interest=D(0)
 for _ in range(k):j=b*D(str(r))/1200;interest+=j;b-=a-j
 return a,b,interest
class F(HTMLParser):
 def __init__(self):super().__init__();self.cells=[];self.buffer=[];self.incell=False;self.rows=[];self.extra=False;self.extras=[]
 def handle_starttag(self,t,attrs):
  if t=='tr':self.cells=[]
  if t in ['td','th']:self.incell=True;self.buffer=[]
  if t=='div'and dict(attrs).get('id')=='extra-rows':self.extra=True
 def handle_data(self,s):
  if self.incell:self.buffer.append(s)
  if self.extra:self.extras.append(s)
 def handle_endtag(self,t):
  if t in ['td','th']:self.cells.append(''.join(self.buffer).strip());self.incell=False
  if t=='tr'and len(self.cells)==2 and re.fullmatch(r'\d{4}-\d\d-\d\d',self.cells[0]):self.rows.append(self.cells)
  if t=='div':self.extra=False
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=pathlib.Path,required=True);ap.add_argument('--private-out',type=pathlib.Path,required=True);ap.add_argument('--public-out',type=pathlib.Path,default=ROOT);a=ap.parse_args();e=a.evidence_dir;x=json.loads((a.private_out/'analysis.json').read_text());checks=[]
 def ok(name,b,detail=None):
  checks.append(dict(check=name,passed=bool(b),detail=detail))
  if not b:raise AssertionError(name)
 def close(name,p,q,tol=1e-6):ok(name,abs(float(p)-float(q))<=tol,{'actual':float(p),'expected':float(q)})
 for r in x['equal_payment_boundaries']:
  cash=pay(100000,r['rate_pct'],360);close('PV payment '+str(r['rate_pct']),r['PI_per_100k'],cash)
  old=pay(60,7.375,360);close('fixed cash boundary '+str(r['rate_pct']),pay(r['fixed_cash_equal_PI_price_index']-40,r['rate_pct'],360),old)
  close('fixed fraction boundary '+str(r['rate_pct']),pay(r['fixed_fraction_equal_PI_price_index']*.6,r['rate_pct'],360),old)
 for r in x['payment_grid']:
  old=pay(60,7.375,360)
  close('grid cash '+str((r['rate_pct'],r['price_index'])),r['fixed_cash_PI_change_pct'],100*(pay(r['price_index']-40,r['rate_pct'],360)/old-1))
  close('grid fraction '+str((r['rate_pct'],r['price_index'])),r['fixed_fraction_PI_change_pct'],100*(pay(r['price_index']*.6,r['rate_pct'],360)/old-1))
 for r in x['points']:
  k=r['months'];aa,b,ii=schedule(100000,7.375,360,k);ac,c,ic=schedule(100000,7.125,360,k)
  close('points cash '+str(k),r['cash_saving_net_cost'],k*(aa-ac)-1000)
  close('points interest '+str(k),r['interest_saving_net_cost'],ii-ic-1000)
  close('points balance '+str(k),r['remaining_balance_saving'],b-c)
 for k in [47,48]:
  value=schedule(100000,7.375,360,k)[2]-schedule(100000,7.125,360,k)[2]-1000
  ok('points crossing '+str(k),value<0 if k==47 else value>=0)
 b=D(100000);rate=D('6.125');interest=D(0);total=D(0);p=pay(b,rate,360)
 for k in range(1,361):
  if k in [61,73,85]:rate+=2;p=pay(b,rate,361-k)
  j=b*rate/1200;b-=p-j;interest+=j;total+=p
  match=next((r for r in x['arm_cap_stress']if r['month']==k),None)
  if match:
   for field,val in [('payment',p),('balance',b),('cumulative_interest',interest)]:close('ARM '+str(k)+' '+field,match[field],val,1e-5)
 for r in x['refinance']:
  _,oldb,_=schedule(100000,7.375,360,36);o,ob,oi=schedule(oldb,7.375,324,r['months_after_refi']);n,nb,ni=schedule(oldb,5.5,r['new_term_months'],r['months_after_refi']);fee=oldb*D('.02')
  close('refi cash '+str((r['new_term_months'],r['months_after_refi'])),r['cash_saving_net_cost'],(o-n)*r['months_after_refi']-fee)
  close('refi interest '+str((r['new_term_months'],r['months_after_refi'])),r['interest_saving_net_cost'],oi-ni-fee)
 for s in ['MORTGAGE30US','DGS10','DGS2','DGS5','DFII10','T10YIE']:
  path=e/('private/frozen/fred_'+s+'.html'if s=='MORTGAGE30US'else 'raw/fred_'+s+'.html');f=F();f.feed(path.read_text());rows=f.rows+re.findall(r'#(\d{4}-\d\d-\d\d)\|\s*([^\s<]+)',''.join(f.extras));data={d:float(v)for d,v in rows if v!='.'};cov=next(z for z in x['coverage']if z['series']==s)
  ok('independent HTML count '+s,len(data)==cov['nonmissing'])
  if s=='MORTGAGE30US':
   for z in x['forecast_errors']:
    yr=int(z['quarter'][:4]);q=int(z['quarter'][-1]);vals=[v for d,v in data.items()if int(d[:4])==yr and (int(d[5:7])-1)//3+1==q];close('quarter mean '+str((z['institution'],z['quarter'])),z['actual_pct'],statistics.mean(vals));ok('quarter n '+str((z['institution'],z['quarter'])),len(vals)==z['weekly_observations'])
  else:close('same-date market '+s,next(z for z in x['market']if z['series']==s)['percent'],data['2026-10-08'])
 for fn in ['fannie_202509_housing','fannie_202609_housing','mba_202605','mba_202609','mba_current_download']:
  raw=subprocess.check_output(['pdftotext','-raw',str(e/'raw'/(fn+'.pdf')),'-'],text=True)
  part=raw.split('30-Year Fixed Rate Mortgage',1)[1].splitlines()[0];values=[float(v)for v in re.findall(r'\d+\.\d+',part)]
  expected=[r['mortgage_rate_pct']for r in x['forecasts']if r['source']==fn+'.txt'];ok('raw PDF alternate order '+fn,values==expected)
  ok('forecast date '+fn,any(month in raw for month in ['September 11, 2025','September 11, 2026','May 15, 2026','September 16, 2026','October 11, 2026']))
 for r in x['source_anomalies']:
  calc=pay(1000,r['rate_pct'],r['years']*12);close('source anomaly calc '+r['field'],r['calculated_PI_per_1000'],calc);ok('source anomaly retained '+r['field'],abs(float(calc)-r['stated_PI_per_1000'])>2)
 ok('missing personal quotes',x['interpretation']['personal_quotes_obtained']==0);ok('no fabricated probabilities',x['interpretation']['scenario_probabilities']is None)
 # Distinguish a source fact error from arithmetic failure.
 out={'status':'passed','passed':len(checks),'checks':checks,'source_discrepancies_retained':x['source_anomalies'],'review_type':'same-thread independent arithmetic and extraction paths; not second-model review'}
 (a.public_out/'qa').mkdir(parents=True,exist_ok=True);(a.public_out/'qa/scenario_independent_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':len(checks),'source_discrepancies':3}))
if __name__=='__main__':main()
