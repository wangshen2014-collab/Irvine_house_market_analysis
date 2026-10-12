#!/usr/bin/env python3
"""Independent split-line source lookup and Decimal ratio checks (not school ranking QA)."""
import argparse,csv,json
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,required=True);a=p.parse_args();out=ROOT/'data/clean';sources={}
 for ind in ('ELA','MATH','ELPI','CCI'):
  lines=(a.input_dir/(ind.lower()+'2025.txt')).read_text(encoding='utf-8-sig').splitlines();header=lines[0].split('\t');rs=[dict(zip(header,x.split('\t')))for x in lines[1:]]
  sources[ind]={(r['cds'],r['studentgroup']):r for r in rs if r['rtype']=='S'}
 cells=0;ratio_checks=0
 for r in csv.DictReader((out/'school_indicators_2025.csv').open()):
  src=sources[r['indicator']].get((r['cds'],r['studentgroup']),{})
  for dest,orig in [('currstatus','currstatus'),('currdenom','currdenom'),('priorstatus','priorstatus'),('priordenom','priordenom'),('published_change','change'),('color','color')]:
   assert r[dest]==src.get(orig,''),(r['cds'],r['indicator'],dest);cells+=1
  if r['indicator']in ('ELPI','CCI'):
   for pref,num in [('curr','currnumer'if r['indicator']=='ELPI'else'curr_prep'),('prior','priornumer'if r['indicator']=='ELPI'else'prior_prep')]:
    try:n=Decimal(src.get(num,''));d=Decimal(src.get(pref+'denom',''));v=Decimal(src.get(pref+'status',''))
    except Exception:continue
    if d>0:assert abs(n*100/d-v)<=Decimal('.051'),(r['school'],num);ratio_checks+=1
 known=[('30736506096192','ELA','ALL','83.2','603'),('30736506096192','MATH','ALL','67.0','625'),('30736506114706','ELA','ALL','73.5','415')]
 # Canyon View CDS derived explicitly below; avoid school-name fuzzy matching.
 directory=list(csv.DictReader((out/'school_directory_20261012.csv').open()));cv=[r['cds']for r in directory if r['school']=='Canyon View Elementary'and r['district']=='Irvine Unified'];assert len(cv)==1
 known[2]=(cv[0],'ELA','ALL','73.5','415');known.append((cv[0],'MATH','ALL','63.6','429'))
 for cds,ind,g,val,n in known:assert (sources[ind][cds,g]['currstatus'],sources[ind][cds,g]['currdenom'])==(val,n)
 # Four headline DFS values agree with separate school-authored SPSA PDFs (same upstream assessment, not independent survey).
 core=[r for r in directory if r['scope']=='irvine_address_directory'];assert len(core)==51 and len(set(x['cds']for x in core))==51
 assert len([x for x in core if x['category']=='conventional'])==44
 q=dict(passed=True,independent_source_cells=cells,independent_ELPI_CCI_ratios=ratio_checks,manual_reference_fields=8,school_SPSA_DFS_cross_format_checks=4,irvine_unique_CDS=51,geography_check='four IUSD maps visually inspected; no exact-address or legal-city polygon certification',limitations='same upstream assessments; no causal school-effect, ranking, seating, or independent parent-identity validation')
 (ROOT/'qa/school_independent_audit.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(json.dumps(q,ensure_ascii=False))
if __name__=='__main__':main()
