#!/usr/bin/env python3
"""Read-only extraction of frozen public sources. Never modifies the APR workbook.
Raw PDFs/HTML, map coordinates and individual builder inventory stay private.
"""
import argparse,csv,hashlib,json,re,subprocess
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import openpyxl
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
TOURS={'n-sPuyx6':'pending','n-bt6qOR':'approved','n-vGTVVA':'under_construction','n-CKWkiO':'completed'}
TYPES=['SFA','SFD','2 to 4','5+','ADU','MH']
def write(p,rows,fields=None):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def plain(s):return ' '.join(html.fromstring('<div>'+s+'</div>').text_content().split())
def verify(raw):
 m=json.loads((ROOT/'data/supply_source_manifest.json').read_text());verified={}
 for x in m['files']:
  if 'sha256' not in x:continue
  h=hashlib.sha256((raw/x['file']).read_bytes()).hexdigest()
  if h!=x['sha256']:raise ValueError('Frozen source mismatch: '+x['file'])
  verified[x['file']]=h
 return verified
def story(raw):
 d=json.loads((raw/'irvine_story_data.json').read_text());nodes=d['nodes'];out=[]
 for tid,stage in TOURS.items():
  for q in nodes[tid]['data']['places']:
   hidden=q.get('config',{}).get('isHidden',False) or q.get('config',{}).get('hidden',False)
   out.append(dict(id=q['id'],title=plain(nodes[q['title']]['data']['text']),stage=stage,hidden=hidden,content=[plain(nodes[n].get('data',{}).get('text',''))for n in q['contents']]))
 return out
def inventory(raw,fn):
 d=html.fromstring((raw/fn).read_bytes());rows={}
 for a in d.xpath('//a[contains(@href,"/Quick-Move-In/")]'):
  txt=plain(a.text_content());b=re.search(r'(\d+)Bedrooms',txt);s=re.search(r'([\d,]+)Sq Ft',txt);p=re.search(r'Priced at \$([\d,]+)',txt)
  if not (b and s and p):continue
  url='https://www.tollbrothers.com'+a.get('href').split('#')[0];coll=url.split('/Quick-Move-In/')[0].split('/')[-1]
  form='detached_condominium'if coll in ('Alder-Collection','Rowan-Collection')else('attached_townhome'if coll in ('Elm-Collection','Birch-Collection')else('single_family'if 'Summit' in fn or fn=='toll_summit.html' else'unverified'))
  r=dict(url=url,collection=coll,bedrooms=int(b[1]),sqft=int(s[1].replace(',','')),price=int(p[1].replace(',','')),building_form=form,availability='move_in_ready'if 'Move-In Ready'in txt else (re.search(r'Quick Move-In (\d+/\d+)',txt)[1]if re.search(r'Quick Move-In (\d+/\d+)',txt)else'unknown'),source_file=fn)
  if url in rows:assert rows[url]==r,'Conflicting duplicate inventory card'
  rows[url]=r
 return list(rows.values())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input-dir',type=Path,required=True);ap.add_argument('--output-dir',type=Path,default=ROOT/'data/clean');ap.add_argument('--qa-out',type=Path,default=ROOT/'qa/supply_baseline_qa.json');ap.add_argument('--private-out',type=Path,required=True);a=ap.parse_args();hashes=verify(a.input_dir)
 notes=json.loads((ROOT/'data/supply_research_notes_20261012.json').read_text());records=story(a.input_dir);visible=[x for x in records if not x['hidden']]
 assert len(records)==71 and len(visible)==68,(len(records),len(visible))
 projects=[];coverage=[]
 for x in visible:
  v=notes['story_housing'].get(x['id']);coverage.append(dict(source_record=x['id'],project=x['title'],source_stage=x['stage'],classification='housing_or_housing_modification'if v else'nonresidential',source='SUP_IRVINE_STORY_DATA'))
  if not v:continue
  text=' '.join(x['content']);pa=re.search(r'Planning Area:\s*(\d+)',text)
  projects.append(dict(project_id=x['id'],city='Irvine',project=x['title'],units_reported=v['units_reported'],stage=v.get('stage_override',x['stage']),source_stage=x['stage'],building_form=v['building_form'],tenure=v['tenure'],parent_id=v['parent_id'],count_caveat=v['count_caveat'],case_ids=';'.join(dict.fromkeys(re.findall(r'\d{8}-[A-Z]+',text))),planning_area=pa[1]if pa else'',source_file='irvine_story_data.json',additional_source=v.get('additional_source','')))
 for x in notes['additional_projects']:
  projects.append({**x,'source_stage':x['stage'],'planning_area':'','additional_source':''})
 for x in projects:
  x.update(as_of='2026-10-12',remaining_units=None,annual_deliveries=None,bedroom_mix='not_quantified',sqft_mix='not_quantified',fees='not_verified',incentives='not_verified',school_assignment='address_and_year_not_verified',geographic_coverage='listed_project_not_full_city_inventory',additive_city_total=False)
  x.update(approval_date='not_verified',permit_date='not_verified',construction_start='not_verified',sales_start='not_verified',completion_date='not_verified',occupancy_date='not_verified')
  detail={
   'n-aegbLk':dict(approval_date='2025-11-12',construction_start='land_development_2026-06; vertical_expected_2027-06',sales_start='expected_Fall2027; not_guaranteed_delivery',bedroom_mix='2–4BR; 4BR_detached_share_unknown',sqft_mix='1750–3250; June2026_FAQ'),
   'n-vYeODW':dict(approval_date='tract2021; masterplans2023',bedroom_mix='mix_not_quantified; builders_include5BR'),
   'n-QrQ8jQ':dict(approval_date='2024-07-18'),
   'n-UNETzX':dict(approval_date='NOT_APPROVED; process_ordinance_not_project_approval'),
   'tustin_ic':dict(approval_date='2025-02-04',bedroom_mix='1–3BR',sqft_mix='592–1513'),
   'tustin_cypress':dict(approval_date='2025-12-02'),
   'tustin_compass':dict(approval_date='2025-06',sqft_mix='1215–1719'),
   'av_argonaut15':dict(sqft_mix='1320–1827'),
   'av_argonaut95':dict(approval_date='2025-12-03',bedroom_mix='2–4BR'),
   'av_freedom':dict(bedroom_mix='3–4BR')}.get(x['project_id'],{})
  x.update(detail)
 write(a.output_dir/'supply_project_ledger_20261012.csv',projects,list(projects[0]));write(a.output_dir/'supply_irvine_map_coverage_20261012.csv',coverage)
 wb=openpyxl.load_workbook(a.input_dir/'irvine_apr2025.xlsm',read_only=True,data_only=True)
 totals=defaultdict(lambda:Counter());detailrows=0
 for row in wb['Table A2'].iter_rows(min_row=13,values_only=True):
  typ=row[5]
  if typ not in TYPES:continue
  detailrows+=1
  for k,idx in [('entitled',19),('permitted',32),('completed',45)]:totals[typ][k]+=row[idx]or 0
 annual=[]
 for n,t in enumerate(TYPES,23):
  row=dict(year=2025,geography='Irvine',building_type=t,**{k:int(totals[t][k])for k in ['entitled','permitted','completed']},source='SUP_IRVINE_APR2025')
  for col,k in [('C','entitled'),('D','permitted'),('E','completed')]:assert row[k]==wb['Summary'][f'{col}{n}'].value,(t,k,row[k])
  annual.append(row)
 write(a.output_dir/'supply_irvine_annual_activity_2025.csv',annual)
 hist=[]
 for col,period in [('D','2021-06-30_to_2021-10-14'),('E','2021-10-15_to_2021-12-31'),('F','2022'),('G','2023'),('H','2024'),('I','2025')]:
  hist.append(dict(period=period,permits=wb['Table B'][col+'25'].value,definition='RHNA_reported_units; 2021_split_periods; not deliveries',source='SUP_IRVINE_APR2025'))
 write(a.output_dir/'supply_irvine_permit_history.csv',hist)
 # Published case index, not a second supply count or independently adjudicated project universe.
 pdftext=subprocess.check_output(['pdftotext','-layout',str(a.input_dir/'irvine_discretionary_20261008.pdf'),'-'],text=True)
 cases=sorted(set(re.findall(r'\b\d{8}-[A-Z]{2,5}\b',pdftext)))
 linked={c:x['project_id']for x in projects for c in x['case_ids'].split(';') if c}
 caseout=[dict(case_id=c,linked_project=linked.get(c,''),status='linked_project'if c in linked else'not_individually_adjudicated; includes_nonresidential_and_ancillary')for c in cases]
 write(a.output_dir/'supply_irvine_pending_case_index_20261008.csv',caseout)
 lf=html.fromstring((a.input_dir/'lf_smartsheet.html').read_bytes());lfrows={}
 for tr in lf.xpath('//tr'):
  cells=[' '.join(e.text_content().split())for e in tr.xpath('./td|./th')]
  if len(cells)>=12 and cells[0].isdigit() and cells[2]:lfrows[cells[0]]=cells
 assert len(lfrows)==53,len(lfrows)
 write(a.output_dir/'supply_lakeforest_coverage_20261012.csv',[dict(source_row=i,project_case=c[2],classification='housing_proposal'if i in ['5','7','22']else'nonresidential_or_ancillary',source='SUP_LF_SMARTSHEET')for i,c in lfrows.items()])
 inv=inventory(a.input_dir,'toll_gpn.html')+inventory(a.input_dir,'toll_summit.html');a.private_out.mkdir(parents=True,exist_ok=True);write(a.private_out/'builder_inventory_private.csv',inv)
 # Source map geometry is retained only in the designated private evidence archive.
 nodes=json.loads((a.input_dir/'irvine_story_data.json').read_text())['nodes'];locations=[]
 for tid,stage in TOURS.items():
  td=nodes[tid]['data'];geoms=nodes[td['map']]['data']['geometries']
  for r in td['places']:
   if r['id'] not in notes['story_housing']:continue
   point=geoms[r['featureId']]['nodes'][0]
   locations.append(dict(project_id=r['id'],source_stage=stage,longitude=point['long'],latitude=point['lat']))
 write(a.private_out/'project_locations_private.csv',locations)
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(8.2,5.2),layout='constrained');colors={'pending':'#d79928','approved':'#5777a1','under_construction':'#168b81','completed':'#888888'}
 for st,col in colors.items():
  pts=[r for r in locations if r['source_stage']==st];ax.scatter([r['longitude']for r in pts],[r['latitude']for r in pts],s=42,c=col,label=st.replace('_',' '),alpha=.8,edgecolors='white',linewidths=.5)
 for i,label,offset in [('n-aegbLk','Gateway',(8,8)),('n-vYeODW','Summit',(-70,5)),('n-UNETzX','Oak Park',(10,6)),('n-QrQ8jQ','Andalucia',(-75,10))]:
  r=next(x for x in locations if x['project_id']==i);ax.annotate(label,(r['longitude'],r['latitude']),xytext=offset,textcoords='offset points',fontsize=9,bbox=dict(boxstyle='round,pad=.2',fc='white',alpha=.85,ec='none'))
 ax.set(xlabel='Longitude',ylabel='Latitude',title='Irvine: 46 visible housing / modification map entries');ax.grid(alpha=.18);ax.legend(loc='upper left',fontsize=8);fig.text(.5,-.035,'City of Irvine source map snapshot, 2026-10-12. Points only; no parcel or city boundary.\nSource stages may lag newer approvals; nearby parent / child entries can overlap.',ha='center',fontsize=8)
 fig.savefig(a.private_out/'supply_project_map.png',dpi=180,bbox_inches='tight');plt.close(fig)
 ag=[]
 for source in ['toll_gpn.html','toll_summit.html']:
  for form in sorted({x['building_form']for x in inv if x['source_file']==source}):
   rs=[x for x in inv if x['source_file']==source and x['building_form']==form];four=[x for x in rs if x['bedrooms']==4]
   ag.append(dict(source_file=source,building_form=form,unique_qmi=len(rs),exactly4br=len(four),fourbr_price_min=min([x['price']for x in four],default=None),fourbr_price_max=max([x['price']for x in four],default=None),fourbr_sqft_min=min([x['sqft']for x in four],default=None),fourbr_sqft_max=max([x['sqft']for x in four],default=None),fourbr_move_in_ready=sum(x['availability']=='move_in_ready'for x in four),coverage='selected_builder_pages_only; no city inventory inference'))
 write(a.output_dir/'supply_builder_inventory_aggregate_20261012.csv',ag)
 q=dict(input_sha256=hashes,visible_map_entries=len(visible),hidden_excluded=len(records)-len(visible),map_stage_counts=dict(Counter(x['stage']for x in visible)),map_housing_entries=len(notes['story_housing']),ledger_rows=len(projects),ledger_city_counts=dict(Counter(x['city']for x in projects)),pending_case_ids=len(cases),pending_cases_linked=sum(bool(x['linked_project'])for x in caseout),pending_case_universe_fully_adjudicated=False,lakeforest_current_entries=len(lfrows),lakeforest_housing_proposals=3,apr_detail_rows=detailrows,annual_totals={k:sum(x[k]for x in annual)for k in ['entitled','permitted','completed']},applications_workbook=wb['Summary']['E37'].value,units_applied=wb['Summary']['E38'].value,rhna_permitted=wb['Table B']['N25'].value,rhna_remaining=wb['Table B']['O25'].value,permit_change_2025_vs2024=hist[-1]['permits']/hist[-2]['permits']-1,permit_sfd_share=totals['SFD']['permitted']/sum(x['permitted']for x in annual),completed_sfd_share=totals['SFD']['completed']/sum(x['completed']for x in annual),builder_qmi_count=len(inv),great_park_qmi=sum(x['source_file']=='toll_gpn.html'for x in inv),fourbr_detached_qmi=sum(x['bedrooms']==4 and x['building_form']=='detached_condominium'for x in inv),full_target_stock=None,full_current_inventory=None,annual_delivery_forecast=None,module_status='restricted_baseline; not full supply completion')
 a.qa_out.parent.mkdir(parents=True,exist_ok=True);a.qa_out.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items()if k!='input_sha256'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
