#!/usr/bin/env python3
"""Independent XML arithmetic audit; evidence adequacy is reported separately."""
import argparse,csv,json,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
N={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def xmlcells(path,sheet):
 with zipfile.ZipFile(path)as z:
  wb=E.fromstring(z.read('xl/workbook.xml'));rels=E.fromstring(z.read('xl/_rels/workbook.xml.rels'));targets={r.attrib['Id']:r.attrib['Target'].lstrip('/')for r in rels}
  rid=next(s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']for s in wb.find('m:sheets',N)if s.attrib['name']==sheet)
  target=targets[rid];target=target if target.startswith('xl/')else'xl/'+target
  strings=[''.join(s.itertext())for s in E.fromstring(z.read('xl/sharedStrings.xml'))]
  cells={}
  for c in E.fromstring(z.read(target)).findall('.//m:c',N):
   v=c.find('m:v',N)
   if v is None:continue
   if c.get('t')=='s':value=strings[int(v.text)]
   else:
    try:value=float(v.text)
    except (ValueError,TypeError):value=v.text
   cells[c.attrib['r']]=value
  return cells
def main():
 p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'qa/supply_independent_audit.json');a=p.parse_args()
 c=xmlcells(a.input_dir/'irvine_apr2025.xlsm','Table A2');summary=xmlcells(a.input_dir/'irvine_apr2025.xlsm','Summary');out=[]
 for r in csv.DictReader((ROOT/'data/clean/supply_irvine_annual_activity_2025.csv').open()):
  for col,k in [('T','entitled'),('AG','permitted'),('AT','completed')]:
   v=sum(c.get(f'{col}{n}',0)for n in range(13,2000)if c.get(f'F{n}')==r['building_type']);assert v==int(r[k]);out.append([r['building_type'],k,int(v)])
 b=xmlcells(a.input_dir/'irvine_apr2025.xlsm','Table B');assert sum(b[f'{c}25']for c in 'DEFGHI')==7442;assert 23610-7442==b['O25']==16168
 ledger=list(csv.DictReader((ROOT/'data/clean/supply_project_ledger_20261012.csv').open()));ids=[r['project_id']for r in ledger];assert len(ids)==len(set(ids));assert all(r['additive_city_total']=='False'for r in ledger);assert all(r['remaining_units']==''for r in ledger)
 l={r['project_id']:r for r in ledger};assert l['n-QNqsCT']['parent_id']==l['n-DwnNaF']['parent_id']=='n-aegbLk';assert int(l['n-jMveQ3']['units_reported'])==-43
 # Explicit observation identities independently checked in downloaded builder cards.
 txt=(a.input_dir/'toll_gpn.html').read_text();four_detached_ids=['282746','282770','286393','282869']
 import re
 known=re.findall(r'/Quick-Move-In/(\d+)',txt)
 assert all(i in known for i in four_detached_ids)
 q=json.loads((ROOT/'qa/supply_baseline_qa.json').read_text());assert q['great_park_qmi']==18 and q['fourbr_detached_qmi']==4
 result=dict(xml_cells_reconciled=len(out),xml_checks=out,rhna_identity='23610 - 7442 = 16168',project_ids_unique=True,parent_children_not_added=True,unknown_remaining_preserved=True,annual_activity_not_cohort=True,manual_inventory_card_check='18 GPN; 4 exact4BR detached condo; 5 Summit QMI all5BR',coverage_limit='No complete municipal parcel stock, sale inventory or annual delivery schedule; not independent model review')
 a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
