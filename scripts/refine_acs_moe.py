"""Independently check core cells and compute 80-replicate 2024 5-year MOEs.

Published single-cell MOEs remain authoritative. User-derived proportions use
the documented SDR method, accounting for covariance, where VRE tables exist.
Other metrics retain explicitly labeled approximation MOEs.
"""
import argparse
import csv
import gzip
import io
import json
import math
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from build_acs_household_structure import acquire, dump_csv, GEOS, ROOT, RETRIEVED

BASE='https://www2.census.gov/programs-surveys/acs/replicate_estimates/2024/data/5-year'
TABLES=['B25003','B11005','B19001']


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--download',action='store_true');args=ap.parse_args()
    raw=ROOT/'data/raw/acs_vre';raw.mkdir(exist_ok=True)
    mp=ROOT/'data/acs_vre_source_manifest.json'
    old=json.loads(mp.read_text()) if mp.exists() else {'files':[]};expected={r['filename']:r for r in old['files']}
    jobs=[(f'{level}_{tb}.csv.zip',f'{BASE}/{level}/{tb}.csv.zip') for level in ['050','160'] for tb in TABLES]
    files=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        fs=[pool.submit(acquire,raw,fn,u,expected.get(fn),args.download) for fn,u in jobs]
        for fut in as_completed(fs):
            r=fut.result();files.append(r);print('VRE source verified:',r['filename'],flush=True)
    files.sort(key=lambda r:r['filename']);mp.write_text(json.dumps(dict(retrieved_date=RETRIEVED,files=files),indent=2)+'\n')
    with (ROOT/'data/clean/acs_2024_detailed.csv').open() as f:base={(r['geography'],r['variable_id']):r for r in csv.DictReader(f) if r['dataset']=='ACS2024_5YR'}
    cells={};source_rows=[];checks=[]
    for fn,_ in jobs:
        with gzip.open(raw/(fn+'.gz'),'rb') as f:z=zipfile.ZipFile(io.BytesIO(f.read()))
        assert len(z.namelist())==1
        with io.TextIOWrapper(z.open(z.namelist()[0]),encoding='cp1252',newline='') as f:
            reader=csv.DictReader(f)
            for line,r in enumerate(reader,2):
                if r['GEOID'] not in GEOS:continue
                geo=GEOS[r['GEOID']];tb=r['TBLID'];order=int(r['ORDER']);var=f'{tb}_{order:03d}'
                b=base[geo,var]
                assert float(r['ESTIMATE'])==float(b['estimate'])
                assert float(r['MOE'])==float(b['moe90'])
                cells[geo,var]=r
                source_rows.append(dict(filename=fn,member=z.namelist()[0],source_line=line,**r))
                checks.append(dict(geography=geo,variable_id=var,estimate_match=True,published_moe_match=True))
    assert len(cells)==len(GEOS)*39
    dump_csv(raw/'selected_replicate_rows.csv',source_rows)
    out=[]
    specs=[('owner_share','B25003',[2],1),('renter_share','B25003',[3],1),
           ('households_under18_share','B11005',[2],1),
           ('households_income200kplus_share','B19001',[17],1),
           ('households_income150kplus_share','B19001',[16,17],1)]
    for geo in GEOS.values():
        for name,tb,indices,den in specs:
            ns=[cells[geo,f'{tb}_{i:03d}'] for i in indices];d=cells[geo,f'{tb}_{den:03d}']
            p=sum(float(r['ESTIMATE']) for r in ns)/float(d['ESTIMATE'])
            reps=[]
            for i in range(1,81):
                rd=float(d[f'Var_Rep{i}']);assert rd>0
                reps.append(sum(float(r[f'Var_Rep{i}']) for r in ns)/rd)
            variance=(4/80)*sum((r-p)**2 for r in reps);moe=1.645*math.sqrt(variance)
            out.append(dict(dataset='ACS2024_5YR',geography=geo,metric=name,estimate=p,moe90=moe,
                            moe_method='80_replicates_SDR_covariance_included',replicate_count=80,
                            source_variables='+'.join(f'{tb}_{i:03d}' for i in indices),denominator_variable=f'{tb}_{den:03d}'))
    dump_csv(ROOT/'data/clean/acs_replicate_metrics_2024.csv',out)
    qa=dict(status='pass',raw_files_verified=len(files),independent_core_cell_checks=len(checks),
            derived_replicate_metrics=len(out),checks=checks,
            limitation='Same ACS survey, independent publication/extraction check, not independent measurement of households; VRE unavailable for B25007/B25115/B25118 in this geography list')
    (ROOT/'qa/acs_replicate_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k!='checks'},indent=2))


if __name__=='__main__':main()
