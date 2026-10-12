"""Render phase-8 public report and optional private native-Docs content plan."""
import argparse, csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(p):
    with p.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--private-dir',type=Path);ap.add_argument('--doc-plan',type=Path);a=ap.parse_args()
    data=ROOT/'data/clean'
    br=read(data/'crosscity_broker_opinions.csv');ss=read(data/'crosscity_match_sensitivity.csv')
    mc=read(data/'crosscity_cost_marginal_scenarios.csv');sy=read(data/'crosscity_cost_synthetic_scenarios.csv')
    cov=read(data/'crosscity_evidence_coverage.csv')
    items=[]
    def text(t,kind='p',page=False,private=False):items.append(dict(kind=kind,text=t,page_break_before=page,private=private))
    def table(h,rows,w,private=False):items.append(dict(kind='table',rows=[h]+rows,widths=w,private=private))
    text('跨市品质、持有成本与买家选择','title')
    text('阶段八｜独立公共市场研究 B｜2026年10月11日（America/Los_Angeles）｜受限完成')
    text('本轮结论：Lake Forest／Tustin确有与北尔湾四卧住宅在面积、房龄和成交时间上接近的公开样本，但目前无法把价差拆成城市溢价、学校、产权、地块和装修的各自贡献。没有证据支持直接宣布“尔湾买家持续外流”或给出同品质固定折价。')
    table(['核对项目','完成情况','可用边界'],[
        ['房屋比较','25笔基线，20笔合格轮廓；51个跨市候选配对中4组通过代理筛选。','4组只涉及2套外市房；完整品质匹配0组。'],
        ['持有成本','8套房补核HOA／成本缺口；官方税费机制与演示情景可复算。','完整逐屋税费及保险组合0套；缺失保留为空。'],
        ['经纪人来源','13位个人／个人品牌，6个机构品牌；2位自述长期Irvine业务。','仅1位另有十年前业务记录；不等于完成连续执业核验。'],
        ['买家选择','2个经纪网站，3条去重且匿名化客户自述。','满足起终城市、年份、价格／产品及独立成交佐证的案例0条。'],
    ],[83,184,183])
    text('工作方式：串行公开研究，没有访谈或联系经纪人、学校、银行；未进入家庭A/C；没有启动第二模型或多智能体。计算使用同一线程的独立算术路径交叉检查。推荐模型分工不代表已执行模型审阅。')
    text('阶段结论与反证','h1')
    text('城市中位数差异同时包含不同房龄、房型、产权和地段组成。较低城市中位数既可能提供替代空间，也可能只是样本产品不同；较大的房子或更低总价不能自动视为同等学校、通勤和居住品质。市内较老社区也是替代选择，不能只寻找“离开尔湾”的叙事。')

    text('1 跨市配对：先控制轮廓，再识别缺口','h1',True)
    text('沿用阶段五／六固定25笔非随机成交笔记，不另挑便宜房。先排除卧室／面积／价格重大冲突、三卧及共墙对照；保留4卧、MLS报无共墙、2010年及以后、至少1,650平方尺的20笔。17笔Irvine与3笔外市形成51个候选对。')
    text('基础门槛：较大面积÷较小面积≤1.10；建成年份差≤5年；MLS关闭日期差≤180天。这里是透明的代理筛选，不是统计匹配估计或估价。没有控制季节／行情变化，复用同一外市房不视为独立观测。')
    if a.private_dir:
        pairs=read(a.private_dir/'proxy_pairs.csv')
        table(['Irvine ↔ 外市房','面积差¹','房龄／天差','原始总价差²'],[[r['irvine_address']+' ↔ '+r['other_address'],f"{(float(r['area_ratio'])-1)*100:.2f}%",r['year_gap']+'年／'+r['close_gap_days']+'天',f"{float(r['raw_price_gap_pct']):+.1f}%"]for r in pairs],[175,70,110,95],True)
        text('¹ 面积差以较小者为分母；² 为MLS报告价的Irvine÷外市−1，未作质量和时间调整，不能命名为尔湾溢价。41 Somerton另有400美元来源差异，按冻结MLS价格保留，非契据核实。',private=True)
    table(['门槛情景','配对数','Irvine房数','外市房数'],[[{'base':'基础：10%／5年／180天','area_5pct':'面积收紧至5%','close_90days':'成交时间收紧至90天','close_365days':'成交时间放宽至365天','year_10years':'建成年份放宽至10年'}[r['scenario']],r['proxy_pairs'],r['unique_irvine_homes'],r['unique_other_homes']]for r in ss],[213,79,79,79])
    text('面积收紧到5%仍有4组；日期收紧到90天仅2组，且共用1套Lake Forest房。房龄放宽到10年增至6组，但仍无完整品质配对。Aliso Viejo现有样本较大且有私人泳池，没有强行纳入小面积组。')
    text('尚缺：独享地块与产权、户型／朝向／噪声、改造与维护、当年官方地址学区、同一目的地与时段通勤、具体税单／保险、实际让利。缺失不能用主观“同品质”标签填补，亦不发布配对价差均值或城市排名。')

    text('2 逐屋成本：HOA可核，完整账单仍缺','h1',True)
    text('HOA按原挂牌披露口径记录，并非已取得的当前业主账单；没有默认各HOA覆盖相同服务。按月、季度、年度分别除以1、3、12。未取得保险、特别收费或新基准税单的项目保留为空，不补零。')
    if a.private_dir:
        costs=read(a.private_dir/'property_cost_review.csv')
        short={
        'T001':'地块12,610平方尺未证实为独享院子；市政AD与学校收费另核。',
        'T002':'独享地块未知；保留阶段六浴室及小额价格冲突。',
        'T012':'独立Condominium、门禁及改造不同；独享院子面积未核。',
        'T016':'0.2491英亩来源字段不代表独享院子；产权未核。',
        'T018':'本轮未取得新的地块、装修或地址保险资料。',
        'T023':'地块3,711／3,920字段冲突；无MR宣传不能替代当期逐屋账单。',
        'T024':'详细HOA325.33，摘要325为取整；MLS披露CFD／特别评估，金额缺。',
        'T025':'230/月＋306.96/季＝332.32/月；私人泳池维护另外计算。'}
        table(['房屋','披露HOA／月','仍需核对'],[[r['address'],f"${float(r['hoa_monthly_usd']):,.2f}",short[r['record_id']]]for r in costs],[105,90,255],True)
        text('91 Barnes网页的2025税额15,007美元与1,581,000美元估值拼接会得出低于1%的比例，年度／税基不一致尚未解释，不能用于预测新买家税负。税表字段冲突保留为待核，不擅自纠正源数据。',private=True)
    text('Condominium法律分类与无共墙建筑形态可以同时成立。网页lot size可能涉及共有地块、登记口径或错误；在独享产权和使用面积未确认前，不按它计算庭院单价或大院子溢价。')
    text('学校与通勤','h1')
    text('Irvine市界不等于IUSD；Tustin Legacy部分地区也在IUSD范围。具体房屋不能因“Tustin有IUSD”就替换原有学区字段。IUSD 2026—27边界和容量溢出规则已登记，但本轮未完成八套房的官方地址分配。通勤须指定目的地、工作日和时段，本轮没有把城市到市中心的距离当逐屋通勤时间。')

    text('3 税费和保险：按收费项目拆开','h1',True)
    table(['项目','已核实规则','计算处理'],[
        ['新买家基础税','符合重估条件的转移通常形成新市场价值基准；卖方旧税单不是买家预算。','购价仅作演示税基代理；最终由Assessor认定。'],
        ['从价税','Prop 13基本税率1%另加批准债务等；不同税项可能使用不同税基。','实际须逐项Σ（税基×税率），不把1.1%或1.25%说成所有房屋真实税率。'],
        ['CFD与AD','Irvine列Stonegate 07-22及Orchard Hills再评估05-21为1913/1915 AD。','市政AD与CFD/Mello-Roos分开；学校、水务及其他机构收费不能漏算或重复。'],
        ['Tustin再融资','2025-05-20材料为提案；涉及Greenwood CFD2014-1等的Tax A。','预计节省不等于最终逐户金额；Tax B服务费不在该减免范围。'],
        ['补充税单','反映重估与旧评估差额及当财年时点；某些时间可能两张。','单列交割后现金时点，不再永久加到已充分重估的年税上。'],
        ['保险','FAIR Plan保障有限，可能需要DIC等补充；价格须同保障条件比较。','未取得逐址报价、免赔额、重建限额及生效条件，不用城市平均数。'],
    ],[77,188,185])
    text('“Baker Ranch无Mello-Roos”有经纪文章支持，但本轮官方逐地块账单入口失败，旧市政刊物正文亦未取得。保留为待核项目，不把它输入为0美元特别收费；无某一项税不意味着总税、HOA或其他评估费用为零。')
    text('Monica Carr的2026年9月税费文章声称检查3,524个地块及84个税率样本，并讨论水务债券不同税基。本轮未取得其原始查询及逐项税基，因此保留方法线索，不复用其税率／抽样结论作为官方复核结果。')

    text('4 可复算成本情景：明确哪些是输入','h1',True)
    text('演示按30年固定摊还、80%贷款成数，购价代理统一1.1%从价税。利率5%／6%／7%是敏感性输入，均非当前贷款报价。每增加10万美元价格，首付另增加2万美元；下表只计算新增本息与假设从价税，不包含其他费用或资本机会成本。')
    table(['利率假设','新增本息／月','新增税／月','两项合计／月','每月多$500相当价格'],[[f"{float(r['annual_rate_assumption'])*100:.0f}%",'$'+r['extra_monthly_pi'],'$'+r['extra_monthly_uniform_tax'],'$'+r['extra_monthly_selected_cashflow'],f"${float(r['price_offset_for_500_monthly_usd']):,.0f}"]for r in mc],[57,96,82,94,121])
    text('6%示例：每多10万美元价格，两项月现金支出多571.31美元；每月多250／500美元其他收费，在该单一融资假设下分别相当于约4.38／8.75万美元价格差。它是代数换算，不能估计市场会按此金额调整成交价。表格按未取整结果计算，显示列相加可能差1美分。')
    table(['纯演示输入','基本情景','较高费用情景'],[
        ['购价／利率／LTV','200万／6%／80%','相同'],['统一从价税／HOA','1.1%／300每月','1.1%／500每月'],
        ['特别费用／保险／维护（每年）','3,000／3,000／10,000','6,000／6,000／20,000'],
        ['所列项目月现金支出',f"${float(sy[0]['monthly_selected_cashflow']):,.2f}",f"${float(sy[1]['monthly_selected_cashflow']):,.2f}"],
    ],[190,130,130])
    text('这两组数值没有对应具体房屋，亦非市场常见区间或上限／下限。维护按指定年额输入；有泳池、共有部分保障和大修项目应另估。本金属于现金流出，但形成权益，不能全当消费成本；完整租买比较还需交易费用、资本机会成本、税务条件、保险保障、维修、通勤和持有期。本轮不作家庭预算或买入／等待建议。')

    text('5 经纪人观点登记（1／2）','h1',True)
    text('按可识别个人或个人品牌去重；网站文章可能由团队编辑，未一律标为本人署名。Coldwell Banker、Real、Realty ONE、First Team、Keller Williams、L3合计6个机构品牌；Alex Gagnon机构信息冲突排除在机构计数外。')
    def broker_rows(rows):
        return [[r['name']+'\n'+(r['firm_family'] or '机构待核'),r['opinion_summary'],r['evidence_limit']]for r in rows]
    table(['来源／机构','观点摘要','核验限制'],broker_rows(br[:7]),[110,162,178])
    text('这些来源是可核对的公开观点样本，不是经纪人总体的概率抽样。共用Redfin、Zillow、CRMLS等上游时，不能把多篇文章当作多份独立市场证据。具体日期、署名方式、主页、限制和文章链接在来源矩阵保留。')

    text('6 经纪人观点登记（2／2）','h1',True)
    table(['来源／机构','观点摘要','核验限制'],broker_rows(br[7:]),[110,162,178])
    text('2026年10月12日审阅处理：B13当前HTML的显示发布日期为7月10日、更新日为10月11日，页末资料截止仍为7月10日；两组结构化更新时间在小时上不同。冻结笔记中的8月25日记录保留为历史观察，旧版本未独立核验。13条经纪来源统一增加历史版本状态，不继承为学校或库存事实。')
    text('长期来源验收','h1')
    text('任务书的12—20位、至少6家机构数量门槛，本轮按公开个人／品牌来源口径达到；若要求独立访谈，则仍为0。8—12位长期Irvine来源目标未达：Monica Carr及Debbie Sagorin自述十年以上Irvine业务，原研究另登记Monica的2015年Irvine成交页，但独立审阅未能读取该第三方网页，因此登记1人、此次独立认证0人；这不是持续每年执业的审计。其余“橙县二十年”“南加州居住多年”不能替代Irvine长期业务。')
    text('2016年Woodbridge刊物仅取得可检索文本，直接下载403；未完成广告图像辨认，因此不把这条线索登记成Debbie的历史独立验证。机构主页与执照展示用于辨识来源，未进行全体执照当前状态审查。')

    text('7 买家选择：有线索，尚无可核验分流案例','h1',True)
    table(['匿名线索','自述的选择过程','关键缺口'],[
        ['C001｜Kwon网站','租客看过Irvine、Tustin、Lake Forest等多城，3月起找房、8月成交。','年份、原居市、最终城市、价格／产品及独立成交记录未知。'],
        ['C002｜Kwon网站','从湾区远程购买Irvine新开发项目并交付。','确切原城市、年份、价格／产品未知；经纪网站客户自述。'],
        ['C003｜Regina网站','从北卡返回加州，比较Tustin及Irvine后成交。','最终城市和年份未知，起点只有州；没有独立合同或文书佐证。'],
    ],[96,177,177])
    text('同一网页展开／折叠或重复出现的证词只算一条；客户姓名不进入研究输出。案例通过门槛需要确切起终城市、成交年份、价格与产品，以及可独立核验的成交证据。本轮3条均未全部满足，不能推算迁移率、尔湾流失人数、首次购房占比或资金来源。C002还提示：当前材料同时存在进入Irvine的叙述，不能只挑外流方向。')
    text('阶段八验收与下一步','h1')
    text('完成：冻结输入与指纹、51组全候选诊断、5组门槛敏感性、8套成本字段复核、3个利率情景和2个纯费用情景、13位公开观点及3条匿名线索登记。计算可复算不代表因果结论成立；完整品质价差、逐屋全成本、长期经纪覆盖及真实分流仍留缺。')
    text('下一模块：全市学校与地址边界。以2026—27官方校区／学校分配为起点，比较教育项目、入学与容量规则、学业指标及数据限制；分清IUSD、TUSD及相邻城市学区，不给出单一“最好学校”排名。之后继续供给、租赁全成本、定价及独立审阅；公共B独立结论完成后再进入家庭A/C。')

    text('8 来源与复算说明','h1',True)
    links=[('California BOE｜Property Tax','https://boe.ca.gov/proptaxes/pdf/pub29.pdf'),('OC Assessor｜Buying / Selling','https://www.ocassessor.gov/real-property-assessments/buying-or-selling-property'),('Irvine｜CFD and AD','https://www.cityofirvine.gov/administrative-services-department/community-facilities-district-and-19131915-act-assessment'),('Tustin｜2025再融资提案','https://tustin.granicus.com/MetaViewer.php?clip_id=2732&meta_id=164909&view_id=5'),('Tustin｜IUSD范围','https://www.tustinca.org/772/Irvine-Unified-School-District'),('IUSD｜2026—27边界与分配','https://iusd.org/about/iusd-enrollment/school-boundaries-assignments'),('CDI｜FAIR Plan','https://www.insurance.ca.gov/01-consumers/200-wrr/California-FAIR-Plan.cfm'),('Kwon｜客户自述','https://kwonhomegroup.com/testimonials.html'),('Regina｜客户自述','https://reginachengroup.com/testimonials')]
    for label,url in links:items.append(dict(kind='link',text=label,url=url,page_break_before=False,private=False))
    text('来源登记截至2026-10-11。data/sources.csv本轮新增45项至240项；原件下载成功7份，失败3项另列，绝不为未取得文件编造指纹。IUSD地图已下载但不作逐地址分配认证；部分官网仅获得页面文本，按实际访问形式登记。来源索引不是再分发许可。')
    text('5份冻结输入包括阶段五／六基线及本轮研究笔记；网页筆记的SHA256标识人工整理版本，不是网页原始快照。房源数值和逐屋诊断留指定研究阅读版，公开仓库保存6张原创表、QA、公开观点摘要、来源链接和代码。公开文章短摘要不包含客户身份或经纪联系方式。')
    text('复算命令见README。主程序先核5份指纹，再生成输出；房贷本息用公式及高精度逐月余额迭代交叉验证。隔离复算、篡改拒绝与文档展示核验结果在本轮QA中登记。',kind='p')
    public=[]
    for x in items:
        if x['private']:continue
        if x['kind']=='table':
            rows=x['rows'];public+=['| '+' | '.join(r.replace('\n',' / ')for r in rows[0])+' |','|'+'|'.join(['---']*len(rows[0]))+'|']
            public+=['| '+' | '.join(str(c).replace('\n',' / ')for c in r)+' |'for r in rows[1:]]
        elif x['kind']=='link':public.append(f"[{x['text']}]({x['url']})")
        else:public.append(('# 'if x['kind']=='title'else '## 'if x['kind']=='h1'else '')+x['text'])
        public.append('')
    (ROOT/'reports/2026-10-11_crosscity_costs_phase8.md').write_text('\n'.join(public))
    if a.doc_plan:
        assert a.private_dir,'Private report tables require --private-dir'
        a.doc_plan.write_text(json.dumps(dict(title='需求：跨市成本与买家选择',items=items),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(report_sections=8,doc_items=len(items),tables=sum(x['kind']=='table'for x in items)),ensure_ascii=False))

if __name__=='__main__':main()
