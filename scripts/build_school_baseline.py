#!/usr/bin/env python3
"""Frozen CDE directory + 2025 Dashboard, no inferred address assignments."""
import argparse,csv,hashlib,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
DISTRICTS={'Irvine Unified','Tustin Unified','Saddleback Valley Unified','Capistrano Unified','Santa Ana Unified','Laguna Beach Unified'}
CITIES={'Irvine','Tustin','Lake Forest','Aliso Viejo'}
GROUPS={'ELA':('ALL','EL','SED','SWD'),'MATH':('ALL','EL','SED','SWD'),'ELPI':('EL',),'CCI':('ALL',)}
EXCLUDE={'Preschool','Adult Education Centers','Special Education Schools (Public)'}
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write(path,rs,fields=None):
 with path.open('w',encoding='utf-8',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input-dir',type=Path,required=True);ap.add_argument('--output-dir',type=Path,default=ROOT/'data/clean');ap.add_argument('--qa-out',type=Path,default=ROOT/'qa/school_baseline_qa.json');a=ap.parse_args()
 manifest=json.loads((ROOT/'data/school_source_manifest.json').read_text());needed=['cde_directory.txt','ela2025.txt','math2025.txt','elpi2025.txt','cci2025.txt'];hashes={}
 for n in needed:
  specs=[x for x in manifest['files']if x['filename']==n and 'sha256'in x];assert len(specs)==1,n
  b=(a.input_dir/n).read_bytes();h=hashlib.sha256(b).hexdigest();assert h==specs[0]['sha256'],f'Frozen source mismatch: {n}';hashes[n]=h
 directory=[];excluded=[]
 for x in rows(a.input_dir/'cde_directory.txt'):
  if x['StatusType']!='Active' or x['School']=='No Data':continue
  if x['District']not in DISTRICTS and x['City']not in CITIES:continue
  if x['SOCType']in EXCLUDE or x['CDSCode'].endswith('0000000'):
   excluded.append({k:x[k]for k in ('CDSCode','District','School','City','SOCType','GSserved')});continue
  scope='irvine_address_directory'if x['City']=='Irvine'else('comparison_city_address_directory'if x['City']in CITIES else'district_context_only')
  category='charter'if x['Charter']=='Y'else('virtual_or_alternative'if x['Virtual']in ('V','F')or x['SOCType']in ('Alternative Schools of Choice','Continuation High Schools')else'conventional')
  directory.append(dict(cds=x['CDSCode'],school=x['School'],district=x['District'],city_field=x['City'],scope=scope,category=category,school_type=x['SOCType'],grades_offered=x['GSoffered'],grades_served=x['GSserved'],virtual=x['Virtual'],charter=x['Charter'],year_round=x['YearRoundYN'],website=x['WebSite'],last_directory_update=x['LastUpDate'],geography_limit='CDE address City field; not municipal polygon or residential eligibility',assignment_year='2026-27',address_assignment='not_verified',grade_seats='not_published_or_not_verified',parent_experience='school_specific_not_reviewed'))
 directory.sort(key=lambda x:(x['scope'],x['district'],x['school'],x['cds']));ids={x['cds']for x in directory};assert len(ids)==len(directory)
 for x in directory:
  if x['scope']=='irvine_address_directory':x['parent_experience']='public_search_completed; source_candidates_unverified'
  if x['school']in ('Stonegate Elementary','Canyon View Elementary'):x['parent_experience']='official_SPSA_and_unverified_public_reviews; denominators_missing'
 observations=[];maps={}
 for indicator,groups in GROUPS.items():
  data=[r for r in rows(a.input_dir/(indicator.lower()+'2025.txt'))if r['rtype']=='S'and r['cds']in ids and r['studentgroup']in groups]
  index={(r['cds'],r['studentgroup']):r for r in data};assert len(index)==len(data);maps[indicator]=index
  for d in directory:
   for g in groups:
    r=index.get((d['cds'],g),{});value=r.get('currstatus','')
    observations.append(dict(cds=d['cds'],school=d['school'],scope=d['scope'],indicator=indicator,studentgroup=g,reportingyear='2025',observation_year='2024-25',unit='points_distance_from_standard'if indicator in ('ELA','MATH')else'percent',status='published'if value not in ('','*','-')else('row_absent_not_zero'if not r else'suppressed_or_unreported'),currdenom=r.get('currdenom',''),currstatus=value,priordenom=r.get('priordenom',''),priorstatus=r.get('priorstatus',''),published_change=r.get('change',''),color=r.get('color',''),currnsizemet=r.get('currnsizemet',''),currnumer=r.get('currnumer',r.get('curr_prep','')),participation_enrolled=r.get('currprate_enrolled',''),participation_tested=r.get('currprate_tested',''),participation_pct=r.get('currprate',''),participation_penalty_n=r.get('currnumPRLOSS',''),denom_without_penalty=r.get('currdenom_withoutPRLOSS',''),status_without_penalty=r.get('currstatus_withoutPRLOSS',''),denominator_definition='continuously_enrolled_tested_plus_participation_penalty'if indicator in ('ELA','MATH')else('ELPI_eligible_EL_cohort'if indicator=='ELPI'else'CCI_eligible_cohort; not_admission_rate')))
 matrix=[]
 for d in directory:
  m={k:d[k]for k in ('cds','school','district','city_field','scope','category','grades_served','address_assignment','grade_seats','parent_experience')}
  for i in GROUPS:
   r=maps[i].get((d['cds'],'EL'if i=='ELPI'else'ALL'),{})
   for k in ('currstatus','currdenom','change','color'):m[i.lower()+'_'+k]=r.get(k,'')
  matrix.append(m)
 out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
 write(out/'school_directory_20261012.csv',directory);write(out/'school_directory_exclusions_20261012.csv',excluded)
 write(out/'school_indicators_2025.csv',observations);write(out/'school_comparison_matrix_2025.csv',matrix)
 q=dict(input_sha256=hashes,directory_rows=len(directory),scope_counts=dict(Counter(x['scope']for x in directory)),irvine_category_counts=dict(Counter(x['category']for x in directory if x['scope']=='irvine_address_directory')),irvine_district_counts=dict(Counter(x['district']for x in directory if x['scope']=='irvine_address_directory')),excluded_rows=len(excluded),indicator_rows=len(observations),published_rows=sum(x['status']=='published'for x in observations),irvine_published_ALL_or_EL_by_indicator={i:sum(x['scope']=='irvine_address_directory'and x['indicator']==i and x['studentgroup']==('EL'if i=='ELPI'else'ALL')and x['status']=='published'for x in observations)for i in GROUPS},exact_address_assignments_verified=0,grade_specific_seat_availability_verified=0,municipal_polygon_coverage='not_verified; directory scope explicit',whole_school_module_complete=False)
 a.qa_out.parent.mkdir(parents=True,exist_ok=True);a.qa_out.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(json.dumps(q,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
