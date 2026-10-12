#!/usr/bin/env python3
"""Read-only extraction of FHFA published aggregates and a separate Dallas series."""
import argparse,json,pathlib,openpyxl
from build_rate_transmission import fred,save
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=pathlib.Path,required=True);a=ap.parse_args();w=a.evidence_dir
 b=openpyxl.load_workbook(w/'raw/fhfa_lockin_data.xlsx',read_only=True,data_only=True);out={}
 for sheet,pred in [('Overall',lambda d:True),('State',lambda d:d['State']=='CA'),('County',lambda d:str(d['FIPS_Code'])=='06059')]:
  rows=b[sheet].values;h=next(rows);out[sheet]=[]
  for r in rows:
   d=dict(zip(h,r))
   if pred(d):out[sheet].append(d)
   if sheet=='County'and out[sheet]and str(d['FIPS_Code'])>'06059':break
  assert len(out[sheet])==106
 # Match original extraction's exact formatting; the build verifies its frozen hash.
 (w/'private/fhfa_selected.json').write_text(json.dumps(out,indent=2))
 rates=fred(w/'raw/MORTGAGE30US.html');b=openpyxl.load_workbook(w/'raw/dallas_chart_data.xlsx',read_only=True,data_only=True);rows=[]
 for dt,v,ff,*_ in list(b['Data1'].values)[1:]:
  if dt and dt.strftime('%Y-%m-%d')in rates:
   d=dt.strftime('%Y-%m-%d');rows.append(dict(date=d,dallas=v,fred=rates[d],delta_bp=100*(v-rates[d])))
 (w/'private/pmms_crosscheck.json').write_text(json.dumps(rows,indent=2));print('FHFA 318 rows; distinct Dallas/Freddie overlap',len(rows))
if __name__=='__main__':main()
