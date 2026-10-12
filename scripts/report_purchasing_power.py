"""Build phase-7 Chinese report and native-Docs table plan from checked aggregates."""
import argparse
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/clean'
CITIES=['Irvine','Lake Forest','Tustin','Aliso Viejo']

def read(n):
    with (DATA/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def money(x):return '—' if x=='' else f'{float(x)/10000:,.2f}'.rstrip('0').rstrip('.')
def percent(x):return '—' if x=='' else f'{float(x)*100:.1f}%'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--doc-plan',type=Path);a=ap.parse_args()
    ss=read('hmda_purchase_summary.csv');bb=read('hmda_value_bands.csv')
    def s(city,y='2025',mode=None):
        mode=mode or ('county' if city=='Orange County' else 'core_99999')
        return next(r for r in ss if r['year']==y and r['geography']==city and r['geography_scenario']==mode)
    items=[]
    def text(t,kind='p',page=False):items.append(dict(kind=kind,text=t,page_break_before=page))
    def table(headers,rows,widths):items.append(dict(kind='table',rows=[headers]+rows,widths=widths))
    text('实际购买力与城市分流：按揭实证','title')
    text('阶段七｜独立公共市场研究 B｜2026年10月11日（America/Los_Angeles）｜受限完成')
    text('结论：已获贷买家的高收入和较低贷款成数，为高价住房提供了可观察的承接证据；就业增量偏弱，支持力度不能外推为持续旺盛需求。现有数据尚未识别买家的原居城市、现金买家、股票财富或同品质跨市价差，因此“尔湾买家正在外流”仍未证实。')
    text('1 2025年获贷买家：不能用居民收入替代','h1')
    text('下表为购房、已发放、自住、首抵、现场建造、单套住宅，且明确非反向／非开放额度／非商业用途的贷款。城市只含统计区面积至少99.999%落入市界的“市内核心统计区”，不是全市。金额单位：万美元；收入为授信依赖的税前年收入；抵押物估值不是成交价。')
    rows=[]
    for city in ['Orange County']+CITIES:
        r=s(city);rows.append([city,r['originations'],r['income_usd_valid_n'],money(r['income_usd_median']),money(r['loan_usd_median']),money(r['property_value_usd_median'])])
    table(['地域','贷款笔数','收入有效n','收入中位','贷款中位','估值中位'],rows,[91,57,66,76,78,82])
    r=s('Irvine')
    text(f"Irvine：收入中间50%为{money(r['income_usd_p25'])}—{money(r['income_usd_p75'])}万美元；收入≥30万美元{r['income_ge300k_n']}/{r['income_usd_valid_n']}，≥50万美元{r['income_ge500k_n']}/{r['income_usd_valid_n']}。缺失收入87/1,002，不补零、不推定低收入或现金。各中位数独立计算，不能拼成一户典型家庭。")
    text('前阶段ACS 2020—2024五年表：Irvine全体家庭收入中位数13.6719万美元（90%误差±0.5709万），业主18.1961万、租客11.3008万，均为2024美元。与2025年贷款样本的地域、年份、收入定义和选样均不同；这里只说明居民存量不是边际获贷买家，不计算“购买力增长倍数”。')

    text('2 年份、筛选和字段逐项核对','h1',True)
    text('官方Data Browser采用每年最新静态版本：2023年One Year（冻结2025-05-19）、2024年One Year（2026-06-02）、2025年Snapshot（2026-06-02）。2025年发布稿另称截至6月1日收到的全国申报；保留两种日期表述。三年后续修订成熟度不同，不伪装成同一冻结批次。2026年度完整数据尚未取得。')
    acq=read('hmda_acquisition_checks.csv')
    table(['年度','购房全部记录','严格筛选贷款','有效贷款机构','统计区缺失'],[[r['year'],r['purchase_records'],r['strict_originations'],r['unique_lenders'],r['missing_tract_n']] for r in acq],[57,110,108,100,75])
    text('三年共87,002条购房记录，包含机构买入贷款、拒绝、撤回和未完成申请；本轮不把它们计作成交。三个年度CSV总笔数和贷款金额合计均与官方聚合接口完全一致。筛选后共38,303笔贷款，无公开字段完全相同的重复行；没有公开唯一贷款／家庭标识，不声称去重成独立家庭数。')
    ff=read('hmda_filter_funnel.csv')[-10:]
    labels=['购房用途全部记录','仅已发放 action=1','自住 occupancy=1','第一顺位 lien=1','现场建造 construction=1','1—4套住宅','限单套住宅 units=1','明确非反向贷款','明确非开放式额度','明确非商业用途']
    table(['2025筛选步骤','保留笔数','本步排除'],[[lab,r['records'],r['excluded_this_step']] for lab,r in zip(labels,ff)],[270,90,90])
    text('严格筛选排除字段豁免1111，不能将豁免理解为“否”。允许这些豁免后，橙县12,451笔、Irvine核心1,015笔；Irvine收入中位数仍32.6万。放宽至1—4套，橙县12,460笔，四城核心样本不变。单套仍可能是公寓、联排或独立屋，不能识别四卧、2010年后、无共墙或detached condo。')
    text('金额单位核验：loan_amount和property_value是美元，公开值为1万美元区间中点；income是千美元。API把综合贷款价值比列为loan_to_value_ratio，官方字段字典称combined_loan_to_value_ratio；已核对CFPB公开代码的导出列和对应字段，作为CLTV使用。DTI保留官方区间，不以中点伪造精确比率；仅统计可判定的≥43%。')
    text('原数据存在state=NA但county=06059：三年购房记录分别1/4/8条，严格样本0/1/6条；按明确县代码保留并登记缺失。统计区缺失只能保留县级，不能分配到城市。')

    text('3 城市边界：同一结果换四种范围','h1',True)
    text('使用同一份ACS2024 Census市界与2020编码的614个橙县统计区，投影面积叠加。只要交集超过1平方米就进入最宽情景；另外设99.999%、95%、50%面积阈值。面积只决定情景归类，不分配人口、贷款或收入。最大范围会包含邻市贷款，并在城市之间重叠；各情景都不是精确城市总量。')
    rr=[]
    for city in CITIES:
        vals=[s(city,mode=m) for m in ['core_99999','near_95','majority_50','overlap_gt1m2']]
        rr.append([city]+[f"{r['originations']}笔／{money(r['income_usd_median'])}万" for r in vals])
    table(['城市','≥99.999%','≥95%','≥50%','有交集'],rr,[80,94,92,92,92])
    text('2025年收入中位数范围：Irvine32.2—32.8万、Lake Forest22.7—23.6万、Tustin21.9—22.8万、Aliso Viejo20.3—23.3万。Irvine相对更高在四种边界情景下均成立；Aliso Viejo的核心仅3个统计区、81笔，不能把它的核心样本代表性当作与Irvine相同。没有据此排出全市购买力精确名次。')
    gg=read('hmda_geography_coverage.csv')
    table(['城市','核心统计区数','有交集统计区数','核心覆盖市界面积'],[[r['city'],r['core_tracts'],r['overlapping_tracts'],percent(r['core_area_share_of_city'])] for r in gg],[114,102,116,118])
    text('上述面积覆盖率不是住宅或贷款覆盖率。Irvine核心排除了524.37等混合统计区；新开发区与边界区可能系统性不同。固定边界适合本轮敏感性比较，不能覆盖2023—2025每年的市界调整或把“有交集”当作全市上限。')
    t=[]
    for tid in ['06059052429','06059052437']:
        r=s(tid,mode='whole_tract_proxy');t.append([tid[-6:],r['originations'],f"{r['income_usd_valid_n']}/{r['originations']}",money(r['income_usd_median']),money(r['property_value_usd_median'])])
    table(['整条统计区','贷款n','收入有效n','收入中位／万','估值中位／万'],t,[94,64,83,104,105])
    text('524.29只作Stonegate及周边统计代理；524.37包含Orchard Hills多个部分，且面积跨市界，绝不是Reserve独立画像。后者收入仅32/46可用，中位61.45万可能有非随机缺失偏差；未证明哪些借款人买了Reserve，也不能据此推断其国籍、雇主或财富来源。')

    text('4 资金结构、价格段与三年变化','h1',True)
    r=s('Irvine')
    text(f"Irvine核心2025年：CLTV有效{r['cltv_percent_valid_n']}/1,002，中位{float(r['cltv_percent_median']):.1f}%，≤60%的{r['cltv_le60_n']}/{r['cltv_percent_valid_n']}（{percent(r['cltv_le60_share_valid'])}）。这与部分借款人使用较大非按揭资金相容，资金可能来自储蓄、旧房净值、赠与或股票，具体来源未识别。DTI≥43%的{r['dti_ge43_n']}/{r['dti_valid_n']}（{percent(r['dti_ge43_share_valid'])}）；这是已获贷样本的债务负担，不能直接推断违约概率。")
    text('2025年核心样本按抵押物估值分段。下表每格为“贷款笔数／可用收入笔数／收入中位数（万美元）”。相同估值段是预算层面的粗比较，房型、房龄、面积、学校和总持有费未控制，因此不是同品质比较，也不是成交价分段。有效n<10不发布分位数。')
    rr=[]
    for city in CITIES:
        row=[city]
        for band in ['1_5m_to_lt2m','2m_to_lt3m']:
            r=next(r for r in bb if r['year']=='2025' and r['geography']==city and r['geography_scenario']=='core_99999' and r['property_value_band']==band)
            row.append(f"{r['originations']}／{r['income_usd_valid_n']}／{money(r['income_usd_median'])}")
        rr.append(row)
    table(['核心样本','估值150万—不足200万','估值200万—不足300万'],rr,[116,167,167])
    text('解释：更高价位通常要求更高收入和／或更低杠杆；同价位下Lake Forest的收入样本未必更低。不能从城市总体中位数推出“在Lake Forest同一房子便宜多少”，也不能据此认定其高端需求来自Irvine。')
    table(['Irvine核心','贷款n','收入有效n','收入中位／万','贷款中位／万','CLTV中位'],[[y,s('Irvine',y)['originations'],s('Irvine',y)['income_usd_valid_n'],money(s('Irvine',y)['income_usd_median']),money(s('Irvine',y)['loan_usd_median']),f"{float(s('Irvine',y)['cltv_percent_median']):.1f}%"] for y in ['2023','2024','2025']],[75,59,75,81,86,74])
    text('三年贷款笔数928→796→1,002、收入中位25.8→29.2→32.6万，均为名义值和固定地域中的不同借款人。橙县严格贷款12,911→13,025→12,367，与Irvine核心2025年回升方向不同。这可以反映产品、机构覆盖、新房交付或融资结构变化，不能解释成同一批人的加薪、同品质房价上涨或净迁移。')
    text('抵押物估值减本笔首抵贷款：Irvine核心2025年可计算986笔，差额中位45万美元。它包含估值与成交价差异且未扣其他贷款，不能命名为实际首付；更不能由HMDA贷款数与非完整MLS样本相减得到现金买家比例。')

    text('5 就业和工资：支撑与反证同时保留','h1',True)
    jobs=read('oc_employment_wages.csv');rr=[]
    for code,label in [('10','全部行业'),('51','信息业'),('52','金融与保险'),('54','专业／科技服务'),('55','企业管理'),('62','医疗与社会服务')]:
        own='all' if code=='10' else 'private';x=next(r for r in jobs if r['period']=='2025_annual' and r['naics']==code and r['ownership']==own);z=next(r for r in jobs if r['period']=='2026_Q1' and r['naics']==code and r['ownership']==own)
        rr.append([label,f"{int(x['employment']):,}",money(x['avg_annual_pay_usd']),z['employment_yoy_percent_unadjusted']+'%',z['wage_yoy_percent_unadjusted']+'%'])
    table(['橙县工作地','2025年均岗位','年均工资／万','2026/3岗位同比','2026Q1工资同比'],rr,[107,89,83,84,87])
    text('来源BLS QCEW；除总计外均为私营部门。年均工资是每个岗位的均值，包含兼职及高低工资分布，不是家庭中位收入；奖金、股票期权等可能已计入工资，不能再机械叠加一份股票收入。Q1同比为原始文件的未作单位调整数据，不把Q1周薪×52当作2026年实际收入。')
    text('橙县2026年3月岗位1,663,154，Q1平均周薪1,766美元。CSV原始同比为岗位+0.6%、周薪+4.2%；9月4日发布稿调整后同比为+0.7%、+4.3%。差异已核对，报告不混用，也不将发布稿的调整等同季节调整。')
    text('更新信号：BLS截至10月2日发布的2026年8月初值，Anaheim–Santa Ana–Irvine（橙县）非农岗位168.57万、同比+0.3%；信息业−5.3%、专业与商业服务−1.1%、教育医疗+3.5%，未季调失业率4.4%。QCEW与月度CES行业分类／调查不同；不把两个系列直接拼成长序列。整体就业尚有增长，高薪相关行业已有压力，不能只依据工资均值上升判断需求强劲。')
    text('雇主核查：Irvine 2025 ACFR第IV-19页列UCI 22,809人、Edwards 3,152人等。其2025列对Broadcom是横杠，2016列为1,900；横杠不是现有就业为零，Broadcom官网位置目录仍列Irvine。该表用165,600“城市劳动力”作比例分母，不能未经核对就当作全市工作地岗位集中度。公司在当地有办公室和授予股票，也不证明本轮房产买家来自该公司。')

    text('6 城市分流：可以说什么，仍缺什么','h1',True)
    table(['比较对象','已经观察到','尚不能推出'],[
        ['Irvine ↔ Lake Forest','同一严格贷款口径下，核心及边界情景有不同收入／估值组合；150—300万估值段两地均有贷款。','没有原居城市、同户型／同校区匹配或全成本；不能证明资金由Irvine流入。'],
        ['Irvine ↔ Tustin','Tustin核心收入中位21.9万；相近估值段存在贷款，但样本较少。','房龄、产权、地块、通勤、学校和税费差异尚未控制。'],
        ['Irvine ↔ Aliso Viejo','估值中位较低，但边界选择影响大；核心高价段有效收入不足10笔。','不能从全市或核心均价估算北尔湾四卧产品的可替代折价。'],
        ['购房 ↔ 继续租住','已有阶段六关闭租赁个案；本轮有真实按揭资金结构。','租约净有效租金、相同服务水平、税费／HOA／保险仍缺，尚不算租买盈亏平衡。']
    ],[97,170,183])
    text('机制判断（推断）：若保持品质、学校和通勤后，替代城市的总月成本确实更低，且已有买家选择记录，就能支持分流；若价差主要补偿较旧房龄、地块或学校差异，则不能视为纯Irvine溢价流失。观察到高收入获贷样本，不能排除低收入租客、现金买家或未能获贷家庭已转向其他市场。')
    text('用于后续同预算比较的融资尺子：30年固定摊还，每借100万美元，在5%／6%／7%示例利率下，每月本息分别5,368／5,996／6,653美元；少借10万美元分别少约537／600／665美元。只为统一算术基准，不是当前贷款报价、银行批准额或包含税费的总成本。')
    text('买家证据分层：按揭收入／CLTV／DTI＝直接申报统计；高薪行业岗位＝地区代理；旧房净值、储蓄、股票财富＝可能机制；现金占比、首次购房、租转买、原居城市、境外资金、本地雇主贡献＝未识别。没有用姓名、族裔、办公室人数或贷款缺失推断这些来源。')
    text('经纪人及案例缺口：本轮新增可核验买家来源访谈／公开观点0人，距任务书12—20人、至少6家机构及8—12位长期Irvine业务来源仍有缺口；此前MLS展示经纪人不自动算观点来源。未主动联系任何人。真实跨市买家选择案例与同品质全成本比较均未达验收，因此执行步骤5保持“受限完成”，不宣布城市分流研究结束。')
    text('下一动作：承接阶段五／六产品组，补跨市同品质成本与经纪人公开观点／可核验买家选择证据，逐项列可比与不可比；学校、供给和定价等后续模块保留。完整B结论与独立审阅前不接家庭A/C。')

    text('7 复算与证据定位','h1',True)
    q1=json.loads((ROOT/'qa/purchasing_power_qa.json').read_text());q2=json.loads((ROOT/'qa/purchasing_independent_audit.json').read_text())
    text(f"25份冻结输入合计49,515,862字节；三年官方CSV和聚合接口笔数／金额一致。主流程{q1['checks_passed']}项检查通过；另一条pandas／SQL路径及椭球面积算法{q2['checks_passed']}项通过，覆盖57组计数、有效分母和分位数、105条地域关系。等长改动贷款金额后，指纹核验在输出前拒绝继续。这里的‘另一条路径’是程序交叉复算，本轮没有第二模型独立审阅。")
    text('公开底稿：scripts/build_purchasing_power.py、audit_purchasing_power.py、report_purchasing_power.py；data/purchasing_source_manifest.json；data/clean下hmda_*、oc_employment_wages.csv、oc_recent_employment.csv、purchasing_financing_scenarios.csv。原始贷款行不导出到公开仓库，不与地址或身份重新识别。')
    text('复算：python scripts/build_purchasing_power.py --raw-dir /path/to/raw；python scripts/audit_purchasing_power.py --raw-dir /path/to/raw；python scripts/report_purchasing_power.py。恢复指定证据包的raw目录即可；公开下载可加--download，文件指纹变更必须登记新版，不能自动覆盖。')
    sources=[
      ('HMDA购房记录／2025','橙县；2023／2024以URL年份替换','https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?years=2025&counties=06059&loan_purposes=1'),
      ('HMDA静态版本FAQ','三年版本和冻结日期','https://ffiec.cfpb.gov/documentation/faq/static-dataset-faq'),
      ('公开LAR字段字典','收入、用途、CLTV、DTI和隐私字段','https://ffiec.cfpb.gov/documentation/publications/loan-level-datasets/lar-data-fields/'),
      ('HMDA隐私政策摘要','金额区间中点、地址／标识不公开','https://files-prod.consumerfinance.gov/f/documents/HMDA_Data_Disclosure_Policy_Guidance.Executive_Summary.FINAL.12212018.pdf'),
      ('Census 2024 TIGERweb','市界与统计区；完整查询见manifest','https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer'),
      ('FFIEC 2025 Census说明','2020统计区编码；本轮网页读取，未存PDF原字节','https://www.ffiec.gov/sites/default/files/data/census/cen2025_10JULY25.pdf'),
      ('BLS QCEW 2025年度','橙县工作地岗位／年薪CSV','https://data.bls.gov/cew/data/api/2025/a/area/06059.csv'),
      ('BLS QCEW 2026Q1','原始同比CSV','https://data.bls.gov/cew/data/api/2026/1/area/06059.csv'),
      ('BLS QCEW发布稿','2026-09-04调整后的同比','https://www.bls.gov/regions/west/news-release/2026/countyemploymentandwages_california_20260904.htm'),
      ('BLS橙县EAG','2026年8月初值；截至10月2日','https://www.bls.gov/eag/eag.ca_santaana_md.htm'),
      ('BLS QCEW方法','工资包含奖金等；岗位非家庭','https://www.bls.gov/cew/overview.htm'),
      ('Irvine 2025 ACFR','IV-19雇主表；PDF物理第252页','https://cityofirvine.gov/sites/default/files/legacy-documents/2025-annual-comprehensive-financial-report.pdf'),
      ('Broadcom官网目录','Irvine位置；检索可见，直取HTML为403','https://www.broadcom.com/company/contact/locations'),
      ('CFPB导出代码','固定commit中的CSV列名；完整映射见manifest','https://github.com/cfpb/hmda-platform/blob/94254a13e45795a4bdb3bbfe2c81098ae27a66a6/data-browser/src/main/scala/hmda/dataBrowser/models/ModifiedLarEntity.scala')]
    table(['证据入口','用途／版本'],[[name,desc] for name,desc,u in sources],[138,312])
    items[-1]['links']=[dict(row=i+1,column=0,url=u) for i,(_,_,u) in enumerate(sources)]
    text('来源处理：CFPB与BLS官方公开统计经原创汇总后发布，保留来源与版本；Census几何依既有联邦统计资料规则。市政ACFR原件和方法原文保留研究档案，公开报告引用事实与链接；403／502响应不保存为原文。代码、数据质量验证并不消除机构覆盖、漏报、估值偏差和地域代理误差。')
    lines=[]
    for item in items:
        if item['kind']=='table':
            rows=item['rows'];links={(x['row'],x['column']):x['url'] for x in item.get('links',[])}
            for i,row in enumerate(rows):
                rr=[f'[{v}]({links[i,j]})' if (i,j) in links else v for j,v in enumerate(row)]
                lines.append('| '+' | '.join(v.replace('|','／').replace('\n','<br>') for v in rr)+' |')
                if i==0:lines.append('| '+' | '.join('---' for _ in row)+' |')
            lines.append('')
        else:lines.extend([('# ' if item['kind']=='title' else '## ' if item['kind']=='h1' else '')+item['text'],''])
    path=ROOT/'reports/2026-10-11_purchasing_power_phase7.md';path.write_text('\n'.join(lines))
    if a.doc_plan:
        a.doc_plan.parent.mkdir(parents=True,exist_ok=True);a.doc_plan.write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(report=str(path),tables=sum(i['kind']=='table' for i in items),table_cells=sum(sum(len(r) for r in i['rows']) for i in items if i['kind']=='table'),paragraphs=sum(i['kind']!='table' for i in items)),ensure_ascii=False))

if __name__=='__main__':main()
