"""Read 2015-2019 sequence-format ACS and compare disjoint 5-year windows.

Only count, age and tenure changes are interpreted here. Historical income
cells retain their own dollar basis and are NOT treated as real-income growth.
The geography join validates FIPS/name/SUMLEVEL/COMPONENT, never row order.
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
from build_acs_household_structure import acquire, dump_csv, GEOS, TABLES, ROOT, RETRIEVED, numeric, margin_numeric

BASE = 'https://www2.census.gov/programs-surveys/acs/summary_file/2019'
STATE = BASE + '/data/5_year_seq_by_state/California/All_Geographies_Not_Tracts_Block_Groups/'


def textfile(raw, fn):
    return gzip.open(raw/(fn+'.gz'),'rt',encoding='cp1252',newline='')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--download',action='store_true')
    ap.add_argument('--raw-dir',type=Path,default=ROOT/'data/raw/acs_history')
    args=ap.parse_args();raw=args.raw_dir;raw.mkdir(parents=True,exist_ok=True)
    mp=ROOT/'data/acs_history_source_manifest.json'
    old=json.loads(mp.read_text()) if mp.exists() else {'files':[]}
    expected={r['filename']:r for r in old['files']};files=[]
    jobs=[('ACS_5yr_Seq_Table_Number_Lookup.txt',BASE+'/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt'),
          ('g20195ca.csv',STATE+'g20195ca.csv')]
    for fn,u in jobs:files.append(acquire(raw,fn,u,expected.get(fn),args.download))
    with textfile(raw,jobs[0][0]) as f:lookup=list(csv.DictReader(f))
    table_spec={r['Table ID']:r for r in lookup if r['Table ID'] in TABLES and r['Start Position'] and not r['Line Number']}
    assert set(table_spec)==set(TABLES)
    seqs=sorted({r['Sequence Number'] for r in table_spec.values()})
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(acquire,raw,f'20195ca{s}000.zip',STATE+f'20195ca{s}000.zip',expected.get(f'20195ca{s}000.zip'),args.download) for s in seqs]
        for fut in as_completed(futures):
            r=fut.result();files.append(r);print(f"History source verified: {r['filename']}",flush=True)
    files.sort(key=lambda r:r['filename']);mp.write_text(json.dumps(dict(retrieved_date=RETRIEVED,files=files),indent=2)+'\n')
    hashes={r['filename']:r['sha256'] for r in files}
    source_records={r['filename']:r for r in files}
    geo_map={};georows=[]
    with textfile(raw,'g20195ca.csv') as f:
        for line,row in enumerate(csv.reader(f),1):
            if row[2] not in ['050','160'] or row[3]!='00':continue
            gid=row[48][:3]+'00'+row[48][3:]
            if gid not in GEOS:continue
            assert row[9]=='06' and ('County' if row[2]=='050' else 'city') in row[49]
            assert GEOS[gid] in row[49]
            geo_map[row[4]]=gid
            georows.append(dict(geo_id=gid,geography=GEOS[gid],official_geo_id=row[48],official_name=row[49],logical_record_number=row[4],source_line=line))
    assert set(geo_map.values())==set(GEOS)
    records=[];selected=[]
    for seq in seqs:
        fn=f'20195ca{seq}000.zip'
        with gzip.open(raw/(fn+'.gz'),'rb') as f:z=zipfile.ZipFile(io.BytesIO(f.read()))
        by_type={}
        for typ in ['e','m']:
            names=[n for n in z.namelist() if Path(n).name.startswith(typ+'20195ca') and n.endswith('.txt')]
            assert len(names)==1
            rs={}
            with io.TextIOWrapper(z.open(names[0]),encoding='cp1252',newline='') as f:
                for lineno,row in enumerate(csv.reader(f),1):
                    if row[5] not in geo_map:continue
                    assert row[5] not in rs and row[4]==seq
                    rs[row[5]]=(lineno,row)
                    selected.append(dict(source_filename=fn,member=names[0],source_line=lineno,logical_record_number=row[5],geo_id=geo_map[row[5]],raw_line=','.join(row)))
            assert set(rs)==set(geo_map);by_type[typ]=rs
        for tb,spec in table_spec.items():
            if spec['Sequence Number']!=seq:continue
            start=int(spec['Start Position'])-1;n=int(spec['Total Cells in Table'].split()[0])
            row_labels={int(float(r['Line Number'])):r['Table Title'] for r in lookup if r['Table ID']==tb and r['Line Number'] and float(r['Line Number']).is_integer()}
            for logical,gid in geo_map.items():
                eline,erow=by_type['e'][logical];mline,mrow=by_type['m'][logical]
                for j in range(n):
                    ev,mv=erow[start+j],mrow[start+j]
                    records.append(dict(dataset='ACS2019_5YR',period_start='2015-01-01',period_end='2019-12-31',
                                        geography=GEOS[gid],geo_id=gid,table_id=tb,variable_id=f'{tb}_{j+1:03d}',
                                        label=row_labels[j+1],table_title=spec['Table Title'],estimate=numeric(ev),moe90=margin_numeric(mv),
                                        estimate_raw=ev,moe_raw=mv,dollars_basis='2019_inflation_adjusted' if tb in ['B19001','B19013','B25118','B25119','B07010','B07011'] else '',
                                        source_filename=fn,sequence=seq,source_column_one_based=start+j+1,
                                        estimate_source_line=eline,moe_source_line=mline,logical_record_number=logical,
                                        source_sha256=hashes[fn],retrieved_date=RETRIEVED))
                    records[-1].update(source_id=source_records[fn].get('source_id','unregistered'),source_url=source_records[fn]['url'])
    dump_csv(ROOT/'data/clean/acs_2019_detailed.csv',records)
    dump_csv(ROOT/'data/clean/acs_2019_geography_crosscheck.csv',georows)
    dump_csv(raw/'selected_source_rows.csv',selected)
    cells={(r['geography'],r['variable_id']):r for r in records}
    specs=[('households_total','B25003',[1],None),('owner_households','B25003',[2],None),
           ('renter_households','B25003',[3],None),('owner_share','B25003',[2],1),
           ('family_share','B11001',[2],1),('households_under18','B11005',[2],None),
           ('households_under18_share','B11005',[2],1),('householders25_44','B25007',[4,5,14,15],None),
           ('householders25_44_share','B25007',[4,5,14,15],1),
           ('householders65plus_share','B25007',[9,10,11,19,20,21],1),
           ('renter_with_own_children','B25115',[18,22,25],None),
           ('renter_with_own_children_share','B25115',[18,22,25],15)]
    metrics=[];checks=[]
    for geo in GEOS.values():
        def e(tb,i):return cells[geo,f'{tb}_{i:03d}']['estimate']
        for name,tb,lhs,rhs in [('owner_renter','B25003',1,[2,3]),('under18','B11005',1,[2,11]),('family','B11001',1,[2,7]),('owner_age','B25007',2,list(range(3,12))),('renter_age','B25007',12,list(range(13,22)))]:
            assert e(tb,lhs)==sum(e(tb,i) for i in rhs);checks.append(dict(geography=geo,check=name,status='pass'))
        assert e('B11001',1)==e('B25003',1)==e('B19001',1)==e('B25115',1)
        checks.append(dict(geography=geo,check='cross_table_total',status='pass'))
        for name,tb,indices,den in specs:
            rs=[cells[geo,f'{tb}_{i:03d}'] for i in indices]
            n=sum(r['estimate'] for r in rs)
            m=math.sqrt(sum(r['moe90']**2 for r in rs)) if all(r['moe90'] is not None for r in rs) else None
            if den:
                dr=cells[geo,f'{tb}_{den:03d}'];p=n/dr['estimate']
                if m is not None and dr['moe90'] is not None:
                    rad=m*m-p*p*dr['moe90']**2
                    m=math.sqrt(rad if rad>=0 else m*m+p*p*dr['moe90']**2)/dr['estimate']
                else:m=None
                n=p
            metrics.append(dict(dataset='ACS2019_5YR',period_start='2015-01-01',period_end='2019-12-31',geography=geo,metric=name,estimate=n,moe90=m,unit='fraction' if den else 'households',moe_method='published_or_RSS_and_subset_approximation'))
    dump_csv(ROOT/'data/clean/acs_household_metrics_2019.csv',metrics)
    with (ROOT/'data/clean/acs_household_metrics_2024.csv').open() as f:new={(r['geography'],r['metric']):r for r in csv.DictReader(f) if r['dataset']=='ACS2024_5YR'}
    rp=ROOT/'data/clean/acs_replicate_metrics_2024.csv'
    if rp.exists():
        with rp.open() as f:
            for r in csv.DictReader(f):
                new[r['geography'],r['metric']].update(estimate=r['estimate'],moe90=r['moe90'],moe_method=r['moe_method'])
    changes=[]
    for r in metrics:
        nr=new[r['geography'],r['metric']];a,b=r['estimate'],float(nr['estimate']);ma,mb=r['moe90'],float(nr['moe90']) if nr['moe90'] else None
        diff=b-a;md=math.hypot(ma,mb) if ma is not None and mb is not None else None
        changes.append(dict(geography=r['geography'],metric=r['metric'],old_window='2015-2019',new_window='2020-2024',old_estimate=a,old_moe90=ma,new_estimate=b,new_moe90=mb,change=diff,change_moe90=md,significant90=(abs(diff)>md) if md is not None else None,
                            change_unit='fraction_points' if r['unit']=='fraction' else 'households',
                            moe_method='disjoint_window_difference_RSS;old_MOE_approximation;new_MOE='+nr.get('moe_method','approximation'),
                            warning='Nominal significance; not multiple-comparison adjusted; boundaries/controls and nonsampling error remain'))
    dump_csv(ROOT/'data/clean/acs_household_window_changes.csv',changes)
    qa=dict(status='pass',raw_files_verified=len(files),sequence_count=len(seqs),detailed_rows=len(records),derived_rows=len(metrics),comparison_rows=len(changes),arithmetic_checks=checks,
            income_change_interpreted=False,nonoverlapping_windows=True,geography_join='validated GEOID+name+SUMLEVEL+COMPONENT; 2019 ID padded to current format explicitly')
    (ROOT/'qa/acs_history_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k!='arithmetic_checks'},indent=2))


if __name__=='__main__':main()
