"""ACS 2020-2024 tract/BG context; never fabricate exact HOA statistics.

Counts may be summed across complete, disjoint BGs. Component medians may not.
Core shares and core count aggregates use Census 80-replicate SDR variances.
Municipal polygon area and 2020 block counts are not used as ACS weights.
"""
import argparse
import csv
import io
import json
import math
import zipfile

from build_acs_household_structure import (
    ROOT, acquire, labels, load_source, numeric, margin_numeric, dump_csv)
from build_community_geography import RAW, acquire as acquire_spatial

TABLES=['B01001','B01002','B11001','B11005','B25003','B25007','B25115',
        'B19001','B19013','B25118','B25119']
TRACTS=['06059052429','06059052437']
GIDS=['1400000US'+t for t in TRACTS]+['1500000US'+t+str(i)
    for t in TRACTS for i in range(1,5 if t.endswith('29') else 6)]
CORE='CUSTOM_SG_BG123'
CORE_GIDS=['1500000US06059052429'+str(i) for i in [1,2,3]]
MEDIANS={'B01002','B19013','B25119'}
TRACT_ONLY={'B25115','B25118','B25119'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--download',action='store_true');a=ap.parse_args()
    acquire_spatial(a.download)
    raw=ROOT/'data/raw/acs'
    allsources=json.loads((ROOT/'data/acs_source_manifest.json').read_text())['files']
    byfile={r['filename']:r for r in allsources}
    used=[f'acsdt5y2024-{tb.lower()}.dat' for tb in TABLES]+['Geos20245YR.txt','ACS20245YR_Table_Shells.txt']
    for fn in used:
        s=byfile[fn];acquire(raw,fn,s['url'],s,a.download)
    meta=labels(raw,'5YR');geos={};gcheck=[]
    with load_source(raw,'Geos20245YR.txt') as f:
        for r in csv.DictReader(f,delimiter='|'):
            gid=r['GEO_ID']
            if gid not in GIDS:continue
            assert r['STATE']=='06' and r['COUNTY']=='059'
            assert r['SUMLEVEL']==gid[:3]
            assert r['TRACT'] in ['052429','052437']
            geos[gid]=r['NAME']
            gcheck.append(dict(geo_id=gid,official_name=r['NAME'],sumlevel=r['SUMLEVEL'],
                state=r['STATE'],county=r['COUNTY'],tract=r['TRACT'],block_group=r.get('BLKGRP',''),
                geography_basis='ACS2024;2020 statistical definitions',status='pass'))
    assert set(geos)==set(GIDS)
    details=[];look={};source_rows=[];coverage=[]
    for tb in TABLES:
        fn=f'acsdt5y2024-{tb.lower()}.dat';source=byfile[fn];seen=set()
        with load_source(raw,fn) as f:
            reader=csv.reader(f,delimiter='|');header=next(reader)
            source_rows.append(dict(filename=fn,geo_id='HEADER',source_line=1,raw_line='|'.join(header)))
            for lineno,arr in enumerate(reader,2):
                if arr[0] not in GIDS:continue
                r=dict(zip(header,arr));gid=r['GEO_ID'];assert gid not in seen;seen.add(gid)
                source_rows.append(dict(filename=fn,geo_id=gid,source_line=lineno,raw_line='|'.join(arr)))
                for key,val in r.items():
                    if not key.startswith(tb+'_E'):continue
                    var=tb+'_'+key[-3:];mr=r[tb+'_M'+key[-3:]]
                    est=numeric(val);moe=margin_numeric(mr)
                    status='published' if est is not None else 'unavailable'
                    if mr=='-333333333':status='open_ended_median;not_exact_value'
                    # Preserve raw code 250001 without reporting it as an exact $250001 median.
                    display='250,000+' if tb in ['B19013','B25119'] and val=='250001' and mr=='-333333333' else val
                    rec=dict(dataset='ACS2024_5YR',period='2020-2024',geo_id=gid,geography=geos[gid],
                        table_id=tb,variable_id=var,**meta[var],estimate=est,moe90=moe,
                        estimate_raw=val,moe_raw=mr,estimate_status=status,display=display,
                        source_filename=fn,source_line=lineno,source_sha256=source['sha256'],source_url=source['url'])
                    details.append(rec);look[gid,var]=rec
        expected={g for g in GIDS if g.startswith('140')} if tb in TRACT_ONLY else set(GIDS)
        assert seen==expected,(tb,seen)
        coverage.append(dict(table_id=tb,available_geographies=len(seen),
            missing_geographies=';'.join(sorted(set(GIDS)-seen)),
            status='tract_only_no_BG_rows_in_official_file' if tb in TRACT_ONLY else 'complete'))
        print('Extracted',tb,flush=True)
    assert len(look)==len(details)
    checks=[]
    def check(name,ok,**kw):
        checks.append(dict(check=name,status='pass' if ok else 'fail',**kw));assert ok,(name,kw)
    # Every published additive variable should reconcile over all BGs to its tract.
    for t in TRACTS:
        parent='1400000US'+t;kids=[g for g in GIDS if g.startswith('150') and g[9:20]==t]
        assert len(kids)==(4 if t.endswith('29') else 5)
        for (gid,var),r in list(look.items()):
            if gid!=parent or r['table_id'] in MEDIANS:continue
            if any((k,var) not in look for k in kids):continue
            vals=[look[k,var]['estimate'] for k in kids]
            if r['estimate'] is not None and all(v is not None for v in vals):
                check('BG_sum_to_tract',sum(vals)==r['estimate'],geo_id=gid,variable=var)
    # Aggregate complete BGs, not polygon fractions.
    geos[CORE]='Stonegate core proxy: full BGs 1-3 of tract 524.29 (excludes mixed BG4)'
    for (gid,var),r in list(look.items()):
        if gid!=CORE_GIDS[0] or r['table_id'] in MEDIANS:continue
        rr=[look[g,var] for g in CORE_GIDS]
        assert all(x['estimate'] is not None for x in rr)
        m=math.sqrt(sum(x['moe90']**2 for x in rr)) if all(x['moe90'] is not None for x in rr) else None
        look[CORE,var]={**r,'geo_id':CORE,'geography':geos[CORE],
            'estimate':sum(x['estimate'] for x in rr),'moe90':m,'estimate_status':'sum_complete_BGs'}

    for gid in geos:
        def e(tb,i):return look[gid,f'{tb}_{i:03d}']['estimate']
        for name,tb,lhs,idx in [('tenure','B25003',1,[2,3]),('children','B11005',1,[2,11]),
            ('family','B11001',1,[2,7]),('population','B01001',1,[2,26]),
            ('income','B19001',1,list(range(2,18))),('owner_age','B25007',2,list(range(3,12))),
            ('renter_age','B25007',12,list(range(13,22))),('owner_income','B25118',2,list(range(3,14))),
            ('renter_income','B25118',14,list(range(15,26)))]:
            if (gid,f'{tb}_{lhs:03d}') not in look:continue
            check(name,e(tb,lhs)==sum(e(tb,i) for i in idx),geo_id=gid)
        totals=[e(tb,1) for tb in ['B25003','B11001','B11005','B19001','B25115','B25118'] if (gid,tb+'_001') in look]
        check('cross_table_HH_total',len(set(totals))==1,geo_id=gid)

    vre={};vre_rows=[];vre_checks=[]
    for level in ['140','150']:
        for tb in ['B25003','B11005','B19001']:
            fn=f'vre_{level}_{tb}_06.csv.zip'
            with zipfile.ZipFile(RAW/fn) as z:
                assert len(z.namelist())==1
                with io.TextIOWrapper(z.open(z.namelist()[0]),encoding='cp1252',newline='') as f:
                    for line,r in enumerate(csv.DictReader(f),2):
                        if r['GEOID'] not in GIDS:continue
                        var=f'{tb}_{int(r["ORDER"]):03d}';gid=r['GEOID'];b=look[gid,var]
                        check('VRE_published_E_M_match',float(r['ESTIMATE'])==b['estimate'] and float(r['MOE'])==b['moe90'],geo_id=gid,variable=var)
                        vre[gid,var]=[float(r[f'Var_Rep{i}']) for i in range(1,81)]
                        vre_rows.append(dict(filename=fn,member=z.namelist()[0],source_line=line,**r))
                        vre_checks.append((gid,var))
    assert len(vre)==11*39
    for var in [v for g,v in vre if g==CORE_GIDS[0]]:
        vre[CORE,var]=[sum(vre[g,var][i] for g in CORE_GIDS) for i in range(80)]
    # Refine aggregate count MOEs for the full-BG custom region using covariance.
    for (gid,var),reps in vre.items():
        if gid==CORE:
            est=look[gid,var]['estimate']
            look[gid,var]['moe90']=1.645*math.sqrt(4/80*sum((x-est)**2 for x in reps))

    specs=[('households_total','B25003',[1],None),('owner_households','B25003',[2],None),
        ('renter_households','B25003',[3],None),('owner_share','B25003',[2],1),
        ('renter_share','B25003',[3],1),('households_under18','B11005',[2],None),
        ('households_under18_share','B11005',[2],1),('family_share','B11001',[2],1),
        ('householders25_44_share','B25007',[4,5,14,15],1),
        ('householders65plus_share','B25007',[9,10,11,19,20,21],1),
        ('renter_with_own_children','B25115',[18,22,25],None),
        ('renter_with_own_children_share','B25115',[18,22,25],15),
        ('households_income200kplus','B19001',[17],None),
        ('households_income200kplus_share','B19001',[17],1),
        ('households_income150kplus_share','B19001',[16,17],1),
        ('renter_income150kplus','B25118',[25],None),
        ('renter_income150kplus_share','B25118',[25],14),
        ('median_household_income','B19013',[1],None),('median_owner_income','B25119',[2],None),
        ('median_renter_income','B25119',[3],None),('median_age','B01002',[1],None),
        ('population_total','B01001',[1],None),
        ('population_under18_share','B01001',[3,4,5,6,27,28,29,30],1)]
    metrics=[];sdr=0;replicate_nonpositive=[]
    for gid in geos:
        for name,tb,idx,den in specs:
            unit='fraction' if den else '2024_USD' if name.startswith('median_') and name.endswith('income') else 'years' if name=='median_age' else 'persons' if name=='population_total' else 'households'
            method='published';n=m=d=None;status='published';cv=None
            display=''
            if gid==CORE and tb in MEDIANS:
                status='unavailable;component_medians_not_additive';method='not_computed'
            elif (gid,f'{tb}_{idx[0]:03d}') not in look:
                status='not_published_at_BG_level';method='not_computed'
            else:
                rr=[look[gid,f'{tb}_{i:03d}'] for i in idx]
                if all(r['estimate'] is not None for r in rr):
                    n=sum(r['estimate'] for r in rr)
                    m=math.sqrt(sum(r['moe90']**2 for r in rr)) if all(r['moe90'] is not None for r in rr) else None
                    method='published' if len(rr)==1 and gid!=CORE else 'sum_RSS_approximation'
                    if len(rr)==1 and 'open_ended' in rr[0]['estimate_status']:
                        status='open_ended_median';n=None;m=None;display=rr[0]['display']
                    if den:
                        dr=look[gid,f'{tb}_{den:03d}'];d=dr['estimate'];dm=dr['moe90']
                        if d and n is not None:
                            n=n/d
                            if m is not None and dm is not None:
                                rad=m*m-n*n*dm*dm
                                m=math.sqrt(rad if rad>=0 else m*m+n*n*dm*dm)/d
                                method+=';subset_proportion_approx' if rad>=0 else ';ratio_fallback_approx'
                        else:n=m=None;status='unavailable_zero_denominator'
                    use_sdr=tb in ['B25003','B11005','B19001'] and (den or gid==CORE)
                    if use_sdr and n is not None:
                        reps=[]
                        for j in range(80):
                            v=sum(vre[gid,f'{tb}_{i:03d}'][j] for i in idx)
                            if den:
                                rd=vre[gid,f'{tb}_{den:03d}'][j]
                                if rd<=0:replicate_nonpositive.append(dict(geo_id=gid,metric=name,replicate=j+1,value=rd))
                                if rd==0:raise ValueError('Zero replicate denominator; statistic undefined')
                                v/=rd
                            reps.append(v)
                        m=1.645*math.sqrt(4/80*sum((v-n)**2 for v in reps));method='80_replicates_SDR';sdr+=1
                else:status='unavailable'
            cv=m/1.645/abs(n) if n and m is not None else None
            metrics.append(dict(dataset='ACS2024_5YR',period='2020-2024',geo_id=gid,geography=geos[gid],
                metric=name,estimate=n,moe90=m,unit=unit,status=status,display=display,
                source_variables='+'.join(f'{tb}_{i:03d}' for i in idx),denominator_variable=f'{tb}_{den:03d}' if den else '',
                denominator_estimate=d,moe_method=method,cv=cv,high_uncertainty=cv is not None and cv>0.30,
                interpretation='census_area_context_or_explicit_proxy;not_exact_HOA_or_buyer_demand'))
    dump_csv(ROOT/'data/clean/acs_community_detailed_2024.csv',details)
    dump_csv(ROOT/'data/clean/acs_community_metrics_2024.csv',metrics)
    dump_csv(ROOT/'data/clean/acs_community_geography_check.csv',gcheck)
    dump_csv(ROOT/'data/clean/acs_community_table_coverage.csv',coverage)
    dump_csv(RAW/'selected_acs_source_rows.csv',source_rows)
    dump_csv(RAW/'selected_vre_rows.csv',vre_rows)
    qa=dict(status='pass',detailed_rows=len(details),metric_rows=len(metrics),
        geo_count=11,custom_complete_BG_regions=1,reused_bulk_files_verified=len(used),
        VRE_E_M_cell_pairs_checked=len(vre_checks),SDR_metric_rows=sdr,
        checks=checks,replicate_nonpositive_denominators=replicate_nonpositive,
        open_ended_cells=[dict(geo_id=r['geo_id'],variable_id=r['variable_id'],raw=r['estimate_raw'],display=r['display']) for r in details if 'open_ended' in r['estimate_status']],
        high_uncertainty_metric_count=sum(r['high_uncertainty'] for r in metrics),table_coverage=coverage,
        limitation='Same ACS survey across formats; no exact Reserve estimates; no spatial allocation, causal inference or independent model review')
    (ROOT/'qa/community_acs_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items() if k not in ['checks','open_ended_cells']},ensure_ascii=False))


if __name__=='__main__':main()
