#!/usr/bin/env python3
"""Independent cash-flow PV, source-row and statistical checks; no causal claim."""
import argparse,csv,decimal,hashlib,html.parser,json,pathlib,re,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
class TableParser(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.cell=False;self.row=[];self.text='';self.rows=[]
 def handle_starttag(self,t,a):
  if t=='tr':self.row=[]
  if t in ('td','th'):self.cell=True;self.text=''
 def handle_data(self,d):
  if self.cell:self.text+=d
 def handle_endtag(self,t):
  if t in ('td','th'):self.row.append(self.text.strip());self.cell=False
  if t=='tr'and len(self.row)==2 and re.fullmatch(r'\d{4}-\d\d-\d\d',self.row[0]):self.rows.append(self.row)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=pathlib.Path,required=True);ap.add_argument('--analysis',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,default=ROOT/'qa/rate_independent_audit.json');a=ap.parse_args();x=json.loads(a.analysis.read_text());checks=[]
 def ck(name,value):
  checks.append({'check':name,'pass':bool(value)})
  if not value:raise AssertionError(name)
 s=(a.evidence_dir/'raw/MORTGAGE30US.html').read_text();p=TableParser();p.feed(s);rows=p.rows[:]
 extra=s.split('<div id="extra-rows">')[1].split('</div>')[0]
 for line in extra.splitlines():
  if line.strip().startswith('#'):rows.append(line.strip()[1:].split('|'))
 rates={d:float(v)for d,v in rows};ck('full mortgage date span',min(rates)=='1971-04-02'and max(rates)=='2026-10-08'and len(rates)==2898)
 release=json.loads((a.evidence_dir/'private/pmms_release_checks.json').read_text())
 for r in release:ck('PMMS original-release '+r['date'],rates[r['date']]==r['value'])
 for month in ['2000-01','2006-12','2012-12','2019-12','2021-12','2023-12','2026-08']:
  vals=[v for k,v in rates.items()if k.startswith(month)];ck('independent monthly mean '+month,abs(sum(vals)/len(vals)-x['monthly']['MORTGAGE30US'][month])<1e-12)
 D=decimal.Decimal;decimal.getcontext().prec=42
 def pv(payment,rate):
  m=D(str(rate))/1200;return sum(D(str(payment))/(1+m)**i for i in range(1,361))
 for i,r in enumerate(x['synthetic']):
  new_loan=pv(r['monthly_PI_index'],r['end_rate_pct']);fixed_cash=D(str(r['down_fraction']))*100+new_loan;fixed_fraction=new_loan/(1-D(str(r['down_fraction'])))
  ck(f'360 discounted payments fixed dollars {i}',abs(float(fixed_cash)-r['fixed_dollars_price_index'])<1e-8)
  ck(f'360 discounted payments fixed ratio {i}',abs(float(fixed_fraction)-r['fixed_percent_price_index'])<1e-8)
 # Re-read the earlier original vendor CSV, not the reused selected derivative.
 upstream=json.loads((a.evidence_dir/'private/frozen/pricing_source_manifest.json').read_text());name='raw/City_zhvi_bdrmcnt_4_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv';target=next(f for f in upstream['inputs']if f['path']==name)
 ck('upstream original city four-bedroom hash',hashlib.sha256((a.evidence_dir/name).read_bytes()).hexdigest()==target['sha256'])
 with (a.evidence_dir/name).open()as f:r=next(z for z in csv.DictReader(f)if z['RegionID']=='52650'and z['State']=='CA')
 for c in x['cycles']:
  if c['series']!='Irvine|four_bedroom':continue
  vals={k[:7]:float(v)for k,v in r.items()if re.fullmatch(r'\d{4}-\d\d-\d\d',k)and v};actual=(vals[c['end']]/vals[c['start']]-1)*100;ck('original CSV cycle '+c['window'],abs(actual-c['nominal_price_change_pct'])<1e-10)
 for c in x['correlations']:
  if c['series']!='Irvine|four_bedroom':continue
  spec=next(w for w in json.loads((ROOT/'data/rate_analysis_design.json').read_text())['windows']if w[0]==c['window']);_,start,end=spec;ms=x['monthly']['MORTGAGE30US'];price=x['prices'][c['series']];keys=sorted(k for k in ms if start<=k<=end);pairs=[]
  import math
  for j in range(1,len(keys)-c['lag_months']):
   t,prev=keys[j],keys[j-1];u,v=keys[j+c['lag_months']],keys[j+c['lag_months']-1]
   if u in price and v in price:pairs.append((ms[t]-ms[prev],100*math.log(price[u]/price[v])))
  ck('correlation sample '+c['window']+'/'+str(c['lag_months']),len(pairs)==c['n'])
  ck('statistics.correlation '+c['window']+'/'+str(c['lag_months']),abs(statistics.correlation(*zip(*pairs))-c['correlation'])<1e-12)
 county=json.loads((a.evidence_dir/'private/frozen/pricing_analysis.json').read_text())['county'];flags=[r['month_date_yyyymm']for r in county if r['quality_flag']in ['1','1.0']]
 ck('five flagged county months retained',flags==['201902','202210','202211','202212','202301'])
 local=x['lockin'][-1];ck('exact county and historical vintage',local['geography']=='Orange County, CA (06059)'and local['year']==2024 and local['quarter']==2)
 ck('rate gap direction',abs(local['fixed_rate_pct']-local['predicted_new_rate_pct']-local['rate_delta_pp'])<.011)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps({'checks':checks,'passed':len(checks),'all_passed':True,'source_rate_crosscheck':'4 original Freddie release dates; Dallas chart not treated as identical PMMS series','causal_validation':False},indent=2)+'\n');print(len(checks),'passed')
if __name__=='__main__':main()
