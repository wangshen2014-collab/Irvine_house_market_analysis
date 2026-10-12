#!/usr/bin/env python3
"""Separate original public synthesis from private per-property Google Docs tables."""
import argparse,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def main():
 a=argparse.ArgumentParser();a.add_argument('--evidence-dir',type=Path,required=True);args=a.parse_args();W=args.evidence_dir;P=W/'private';D=P/'derived';d=json.loads((P/'rental_notes.json').read_text());q=json.loads((ROOT/'qa/rental_baseline_qa.json').read_text());ls=d['leases'];look={r['record_id']:r for r in ls};mt=read(D/'rental_purchase_matches.csv');cost=read(D/'property_cost_gaps.csv');up=read(D/'rental_service_upgrades.csv');manifest=json.loads((ROOT/'data/rental_source_manifest.json').read_text());urls={x['path'].split('/')[-1]:x.get('url')for x in manifest['files']};B=[];prose=json.loads((P/'report_prose.json').read_text())
 def p(t):B.append(dict(type='paragraph',text=t))
 def h(t):B.append(dict(type='heading',text=t))
 def tab(rows):B.append(dict(type='table',rows=[[str(x)for x in r]for r in rows]))
 def link(t,u):B.append(dict(type='link',text=t,url=u))
 B.append(dict(type='title',text='租赁：同产品比较与持有全成本｜阶段十一'))
 p(prose['P01'])
 h('1. 本轮判断')
 p(prose['P02'])
 p(prose['P03'])
 h('2. 数据覆盖和证据等级')
 tab([['项目','本轮结果','能说明什么'],['观察记录','历史7＋新增11＝18','目的性抽样；不代表库存或城市分布'],['状态／日期','关闭12、挂牌6；18/18标日期和日期类型','MLS关闭≠已取得签署租约；挂牌≠成交'],['租住条款','租期有记录15；家具一致无家具15','其余缺失或冲突；所有净优惠和完整附费未知'],['匹配','候选8组；其中同址2组','严格同品质认证0；学校逐址确认0'],['成本','原8套持有费继续逐项核对','完整新买家税、MR、保险及特别征费均未齐'],['可入住性','2笔明确广告未来入住日期','其它日期已过也不等于确认现在可租']])
 h('3. 真实租赁观察：历史基线')
 p(prose['P04'])
 def lease_rows(items):
  rows=[['记录／地址','产品','名义租金与日期','条款／限制']]
  for r in items:
   status='MLS关闭'if r['status']=='MLS_closed_reported'else'挂牌'
   term=str(r['lease_term'])+'个月' if isinstance(r['lease_term'],int)else(r['lease_term'] or '租期未知')
   furnish='无家具'if r['furnished']=='Unfurnished_mls_reported'else('家具字段冲突'if r['furnished']=='conflicting_fields'else'家具未知')
   inc={'association_dues_mls_reported':'含HOA','gardener_mls_reported':'含园丁','association_dues_and_gardener_mls_reported':'含HOA和园丁'}.get(r['rent_includes'],'包费未核')
   detail=f'{term}；{furnish}；{inc}'
   if r.get('available_date') and r['available_date']>d['as_of']:detail+='；广告可入住'+r['available_date']
   if r['record_id']=='L012':detail+='；原四卧改三卧；来源更新较旧'
   if r['record_id']=='L014':detail+='；年建2015/2016冲突'
   rows.append([r['record_id']+' '+r['address']+'\n'+r['community_claimed'],f"{r['bedrooms']}卧｜{r['living_area_sqft']:,}sf\n{r['year_built']}年",f"${r['amount']:,}｜{status}\n{r['event_date']}\n"+{'MLS_reported_close':'报告关闭日','asking_price_change':'广告调价日','observation_date_no_price_event':'观察日；无调价事件日','source_last_update':'来源更新日'}[r['date_basis']],detail])
  return rows
 tab(lease_rows(ls[:7]))
 h('4. 本轮新增观察及状态修正')
 tab(lease_rows(ls[7:]))
 p(prose['P05'])
 p(prose['P06'])
 h('5. 同产品租购匹配：先看配对理由')
 tab([['组别／售房 ↔ 租房','匹配证据','剩余差异与用途']]+[[r['match_id']+' '+r['sale_address']+' ↔ '+r['lease_address'],f"{r['bedrooms_sale']}卧 ↔ {r['bedrooms_lease']}卧；面积差{r['area_gap_pct']}%\n事件相隔{r['date_gap_days']}天",r['reason']]for r in mt])
 p(prose['P07'])
 h('6. 租赁全成本：押金与费用分开')
 p(prose['P08'])
 p(prose['P09'])
 p(prose['P10'])
 h('7. 社区持有费用：个案报告值不当全社区统一报价')
 tab([['观察社区／个案','MLS HOA月等值','还缺什么']]+[[r['community']+'\n'+r['record_id']+' '+r['address'],'$'+r['hoa_mls_monthly'],'当年TRA与新买家重估税；MR/其它direct charge；HOA特别征费及主保单；可承保保费；维护/更换计划；逐址FHSZ']for r in cost])
 p(prose['P11'])
 p(prose['P12'])
 p(prose['P13'])
 h('8. 可复算的部分成本：本金、现金流和经济成本')
 p(prose['P14'])
 tab([['候选组／价格状态','现金部分／月','本金／经济部分','相对名义租金']]+[[r['match_id']+' 售$'+f"{int(r['sale_price_usd']):,}"+'\n租$'+f"{int(r['rent_headline_usd_month']):,}"+('（挂牌）'if r['match_id']=='M02'else'（MLS关闭）'),'$'+r['model_cash_partial']+'＋U','本金$'+r['model_principal_y1_month_avg']+'\n经济$'+r['model_economic_partial']+'＋U','部分现金差$'+r['partial_cash_minus_headline_rent']+'\n尚未调整租客附费']for r in mt[:3]])
 p(prose['P15'])
 p(prose['P16'])
 h('9. 三卧租房到四卧：服务升级单列')
 tab([['候选对照','名义月租差／面积变化','解释']]+[[u['pair_id']+' '+look[u['from_id']]['address']+' → '+look[u['to_id']]['address'],'$'+u['observed_headline_difference']+'／'+u['area_change_pct']+'%',u['reason']]for u in up])
 p(prose['P17'])
 h('10. 山火地图与保险可得性')
 p(prose['P18'])
 p(prose['P19'])
 h('11. 验收、缺口与下一步')
 p(prose['P20'])
 p(prose['P21'])
 h('官方费用与风险来源')
 for label,fn in [('OC新买家评估与税费','oc_assessor_newbuyer.html'),('OC当年direct-charge入口','oc_directcharge.html'),('IUSD CFD 09-1 FY2025审计','iusd_cfd091_fy2025.pdf'),('CDI 2026住宅保险指南','cdi_residential.html'),('CDI补充DIC产品名单','cdi_dic.html'),('加州司法部门押金指引','security_deposits.pdf'),('Irvine 2025火险图及生效说明','irvine_fire2025.html'),('Lake Forest 2025火险入口','lakeforest_fire2025.html'),('Tustin 2025火险入口','tustin_fire2025.html'),('Aliso Viejo 2025火险图','aliso_fire2025.pdf')]:
  if urls.get(fn):link(label,urls[fn])
 link('OSFM：hazard、risk与保险说明','https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones')
 link('公开来源索引与复算代码','https://github.com/wangshen2014-collab/Irvine_house_market_analysis/blob/main/data/rental_source_index.csv')
 h('逐条租赁来源（个案字段核验入口）')
 for r in ls:link(r['record_id']+' '+r['address'],r['source_urls'][0])
 (P/'doc_blocks.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
 public='''# 阶段十一：租赁替代与持有费用受限基线

截至2026-10-12；独立公共B，串行执行。18笔目的性租赁观察（新增11、冻结历史7）涵盖Irvine、Lake Forest、Tustin、Aliso Viejo及7个社区/片区；12笔MLS报告关闭、6笔广告挂牌。它们不是完整库存，也不是统计抽样。18笔状态、日期类型及来源已记录，租期信息15笔、家具一致无家具15笔。签署租约、真实续租、全费用有效租金均0，不能形成城市租金指数。

## 原创判断

租住替代存在，但同城同卧室不等于同品质。8组候选中2组同址，另有同面积年代、大小不同、旧售房和服务升级对照。官方学校逐址确认0，严格同品质认证0。跨站通常同属CRMLS上游，不能将两个网站算两份独立租约。

三卧到四卧的观察差额同时包含面积、装修、时间、家具、院子和条款；也有更大的三卧与较小四卧广告价相同的反例。将租三卧与买四卧混算，会把服务升级误当所有权代价。个案地址、租价及配对详表仅在已授权正式文档和私人证据包，公开只列来源URL、覆盖计数和原创方法，不转载完整MLS。

## 费用机制及边界

- 租赁：基础租金＋明确强制不退费用－已确认优惠，按合同期摊销，再计租客实际承担的服务与保险。可退押金属于现金占用，不是每月消费。包费/优惠未披露不等于0，历史关闭不代表当前可租。
- 税：可重估交易以转移时市场价值形成新税基；基础税、当地债务税和按地块/分类特别征费分列。旧业主税单不代表新买家预算。补充税是新旧税基差额及对应期间，不能在全年新税基预算之上重复加整年。
- HOA：历史挂牌费不等于当前认证账单；月、季、年频率统一，还需储备金、主保单与特别征费。本轮8套完整新买家持有费用仍0。CFD区级审计、税务入口及No Mello-Roos营销均不能替代当年APN明细。
- 保险：未知仍未知；FAIR Plan及DIC名单是产品路径，非可绑定报价。房屋无共墙不等于保险责任与普通独立屋相同，Condominium须核主保单与CC&R。
- 现金流：本息＋税＋HOA＋保险＋维护实际支出/储备安排；经济成本剔除本金转权益，再考虑可投资权益机会成本、交易费、税效应与净售出价值。同笔维护储备和支出不得重复累计。

Irvine采用2025 LRA火险图、2025-07-23生效；比较城市2025入口也已核。社区名不能替代逐址等级，未完成APN/建筑坐标叠置。OSFM的hazard不等于计入减灾的risk，也不等于保险商风险模型，不能按地图颜色推算保费。官方资料入口见下。

## 可复算与缺失值保护

私有比较示例统一20%首付、30年固定、6%利率，以售房报告价作示例税基并按1%基础税，加历史MLS HOA。仅展示部分现金/经济合计，完整保险、债务税/MR、维护等仍留空；不称最低总成本，不称每月投资损失，6%不是现行报价。

公开敏感性表为完全虚构的$100万、20%首付、HOA $250、按价值税1.1%，配4/6/8%利率与0.5%/1%价格口径维护预算。仅验证机制；不推断真实房屋维护率、保费或家庭能力。所有保险、特别征费和完整总成本字段留空。

Decimal逐期摊还与独立闭式余额公式交叉核到美分；混频HOA、押金归类、旧摘要/新正文状态、缺失数据保护均通过。隔离复跑和指纹拒绝结果另见qa/rental_reproducibility.json。算术一致不证明品质相同或市场代表性，不冒充第二模型审阅。

## 下一项动作

步骤8形成受限基线，未通过完整成本验收；步骤9资产定价接续，沿用真实租售状态与未完成费用，不用低保险假设补空。后续利率机制、联合情景、独立B总结和独立审阅尚待进行，未进入家庭A/C。

'''
 for label,fn in [('OC新买家税','oc_assessor_newbuyer.html'),('OC direct-charge','oc_directcharge.html'),('IUSD CFD审计','iusd_cfd091_fy2025.pdf'),('CDI住宅保险','cdi_residential.html'),('CDI DIC','cdi_dic.html'),('司法部门押金','security_deposits.pdf'),('Irvine地图','irvine_fire2025.html'),('Lake Forest地图入口','lakeforest_fire2025.html'),('Tustin地图入口','tustin_fire2025.html'),('Aliso地图','aliso_fire2025.pdf')]:
  if urls.get(fn):public+=f'- [{label}]({urls[fn]})\n'
 public+='- [OSFM分区和保险说明](https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones)\n'
 (ROOT/'reports/2026-10-12_rental_cost_phase11.md').write_text(public)
 print(json.dumps(dict(blocks=len(B),tables=sum(b['type']=='table'for b in B),cells=sum(len(r)for b in B if b['type']=='table'for r in b['rows']),text_chars=sum(len(b.get('text',''))for b in B))))
if __name__=='__main__':main()
