"""Independent pandas/SQL/statistical and geodesic checks for phase 7.

This is a second computational path, not another model or an independent survey.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

import pandas as pd
from pyproj import Geod
from shapely.geometry import shape

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw-dir',type=Path,required=True)
    ap.add_argument('--clean-dir',type=Path,default=ROOT/'data/clean')
    ap.add_argument('--out',type=Path,default=ROOT/'qa/purchasing_independent_audit.json')
    a=ap.parse_args(); checks=[]
    def check(name,ok,**detail):
        checks.append(dict(check=name,status='pass' if ok else 'fail',**detail))
        if not ok: raise ValueError((name,detail))
    def read(path):return pd.read_csv(path,dtype=str,keep_default_na=False)
    cross=read(a.clean_dir/'hmda_tract_city_crosswalk.csv')
    published=read(a.clean_dir/'hmda_purchase_summary.csv')
    for year in (2023,2024,2025):
        raw=read(a.raw_dir/f'hmda_{year}_purchase_oc.csv')
        connection=sqlite3.connect(':memory:');raw.to_sql('lar',connection,index=False)
        q='''SELECT * FROM lar WHERE action_taken='1' AND loan_purpose='1'
             AND occupancy_type='1' AND lien_status='1' AND construction_method='1'
             AND total_units='1' AND reverse_mortgage='2'
             AND "open-end_line_of_credit"='2' AND business_or_commercial_purpose='2' '''
        eligible=pd.read_sql_query(q,connection);connection.close()
        for _,r in published[published.year==str(year)].iterrows():
            if r.geography=='Orange County':subset=eligible
            elif r.geography_scenario=='whole_tract_proxy':subset=eligible[eligible.census_tract==r.geography]
            else:
                ids=set(cross.loc[(cross.city==r.geography)&(cross[r.geography_scenario]=='True'),'tract_geoid'])
                subset=eligible[eligible.census_tract.isin(ids)]
            check('SQL_count_matches',len(subset)==int(r.originations),year=year,geography=r.geography,mode=r.geography_scenario)
            for raw_field,prefix,scale in [('income','income_usd',1000),('loan_amount','loan_usd',1),
                    ('property_value','property_value_usd',1),('loan_to_value_ratio','cltv_percent',1)]:
                numeric=pd.to_numeric(subset[raw_field],errors='coerce').dropna()*scale
                check('pandas_valid_count',len(numeric)==int(r[prefix+'_valid_n']),year=year,geography=r.geography,field=raw_field,mode=r.geography_scenario)
                for quantile,label in [(0.25,'p25'),(.5,'median'),(.75,'p75')]:
                    val=r[prefix+'_'+label]
                    check('pandas_quantile',val=='' if len(numeric)<10 else abs(float(val)-numeric.quantile(quantile))<1e-5,
                          year=year,geography=r.geography,mode=r.geography_scenario,field=raw_field,quantile=quantile)
    # Independently classify via ellipsoidal WGS84 area rather than UTM area.
    tr={x['properties']['GEOID']:shape(x['geometry']) for x in json.loads((a.raw_dir/'oc_tracts_2024.geojson').read_text())['features']}
    ci={x['properties']['BASENAME']:shape(x['geometry']) for x in json.loads((a.raw_dir/'places2024.geojson').read_text())['features']}
    gd=Geod(ellps='WGS84')
    for _,r in cross.iterrows():
        t=tr[r.tract_geoid];g=ci[r.city];area=abs(gd.geometry_area_perimeter(t.intersection(g))[0]);total=abs(gd.geometry_area_perimeter(t)[0])
        for field,threshold in [('core_99999',.99999),('near_95',.95),('majority_50',.5)]:
            check('geodesic_vs_utm_membership',(area/total>=threshold)==(r[field]=='True'),city=r.city,tract=r.tract_geoid,mode=field)
    # A source changed without changing byte count must fail before writing.
    with tempfile.TemporaryDirectory() as temp:
        tmp=Path(temp);rawcopy=tmp/'raw';rawcopy.mkdir()
        mf=json.loads((ROOT/'data/purchasing_source_manifest.json').read_text())
        target='hmda_2025_purchase_oc.csv'
        for rec in mf['files']:
            n=rec['filename'];src=a.raw_dir/n
            if n==target:
                b=src.read_bytes();old=b'1055000.0';new=b'1065000.0'
                check('negative_fixture_token_exists',old in b)
                changed=b.replace(old,new,1);check('negative_fixture_same_length',len(changed)==len(b));(rawcopy/n).write_bytes(changed)
            else:(rawcopy/n).symlink_to(src.resolve())
        result=subprocess.run([sys.executable,str(ROOT/'scripts/build_purchasing_power.py'),'--raw-dir',str(rawcopy),
            '--outdir',str(tmp/'out'),'--qa',str(tmp/'qa.json')],capture_output=True,text=True)
        check('changed_input_rejected_before_output',result.returncode!=0 and 'input_fingerprint' in result.stderr and not (tmp/'out').exists())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(dict(status='pass',checks_passed=len(checks),checks=checks,
        scope='57 aggregates; all valid denominators and quartiles by pandas/SQL; all 105 tract-city pairs by geodesic area; negative fingerprint test',
        independent_model_review=False),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(checks_passed=len(checks),status='pass')))


if __name__=='__main__':main()
