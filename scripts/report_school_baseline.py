#!/usr/bin/env python3
"""Generate Chinese report, native-Docs content plan and hand-curated registers."""
import argparse,csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(n):return list(csv.DictReader((R/'data/clean'/n).open()))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--private-out',type=Path,required=True);a=ap.parse_args();a.private_out.mkdir(parents=True,exist_ok=True)
 c=json.loads((R/'data/school_research_notes_20261012.json').read_text());q=json.loads((R/'qa/school_baseline_qa.json').read_text());audit=json.loads((R/'qa/school_independent_audit.json').read_text());directory=read('school_directory_20261012.csv');matrix=read('school_comparison_matrix_2025.csv');ix={r['school']:r for r in matrix if r['city_field']=='Irvine'and r['school']!='Excel Academy Charter'}
 for name,rs in [('school_boundary_register_202627',c['boundaries']),('school_program_register_202627',c['programs']),('school_experience_register_20261012',c['experiences']),('school_capacity_context_2026',c['capacity'])]:
  with (R/'data/clean'/(name+'.csv')).open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
 coverage=json.loads((R/'data/school_parent_search_coverage_20261012.json').read_text())
 with (R/'data/clean/school_parent_search_coverage_20261012.csv').open('w',newline='')as f:
  rs=[dict(cds=x['cds'],school=x['school'],district=x['district'],query=x['query'],searched_date=x['searched_date'],candidate_urls=' | '.join(x['candidate_urls']),stage=x['stage'],limits=x['limit'])for x in coverage];w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
 items=[]
 def p(t):items.append({'kind':'paragraph','text':t})
 def h(t):items.append({'kind':'heading','text':t})
 def table(title,headers,rows):items.append({'kind':'table','title':title,'rows':[headers]+[[str(v)for v in row]for row in rows]})
 h('学校：2026–27官方基线与入学限制')
 p('截至2026-10-12。公共市场B阶段九，基于阶段五至八独立审阅后的来源补修。学校官方基线已建立，完整学校验收仍受限：单址分配、逐年级余位、全市项目与家长体验覆盖没有全部完成；不构成公共B完成、学校总排名或买入／等待结论。')
 h('本轮可支持的判断')
 p('Stonegate社区级地图对应Stonegate Elementary—Sierra Vista—Northwood；Orchard Hills中IUSD部分的官方表对应Canyon View—Sierra Vista—Northwood。Reserve具体门牌没有取得官方定位器结果，因此后一个链条只是候选路径。整个Orchard Hills跨学区，不能用同名学校或营销社区名称替代地址分配。两条路径若单址最终成立，中学与高中相同，不能把高中声誉当作两个社区之间的独立价差解释。')
 p('Stonegate和Canyon View的已发布英语／数学指标均高于州标准，但Stonegate当期变动为下降、Canyon View为上升。水平、年度变化、英语学习支持、校园体验与名额风险需要一起看，不能从一个分数推出孩子的适配性或住房溢价。2026州Dashboard及评估结果计划10月15日发布，本轮没有使用尚未发布数据，也未创建定时任务。')
 h('覆盖边界与版本')
 table('目录口径',['范围','记录数','含义'],[['Irvine地址字段','51','IUSD44、TUSD4、OCDE1、Helendale1、Warner1'],['Irvine常规／特许／虚拟替代','44／4／3','CDE虚拟代码C=以课堂为主，不能误归为虚拟校'],['Tustin／Lake Forest／Aliso Viejo地址字段','36','比较城市目录；另含部分charter，不能直接当片区学校'],['六学区其余参考校','144','仅学区背景，不表示都服务Irvine或可申请'],['全部目录／指标槽位','231／2,310','每校ELA、Math各4群体，ELPI与CCI各1；含缺失槽位'],['Irvine已发布ALL或EL指标','ELA51；Math51；ELPI49；CCI10','ELPI用EL群体；CCI只适用相应高中／K-12 cohort']])
 p('目录为CDE动态行政地址字段快照，已排除学区汇总、学前、成人和专门成人过渡记录；没有把邮政City字段认证为市界内校园，也没有把特许学校办公室当常规校园。两所Excel Academy同名但CDS不同，分别保留。六个参考学区为IUSD、TUSD、SVUSD、CUSD、SAUSD、LBUSD；后两者用于边缘排漏背景。市政府明确Irvine由IUSD、TUSD、SVUSD、SAUSD四学区服务；LBUSD相邻不等于它是Irvine服务学区。')
 p('目录检索日2026-10-12；边界2026–27；IUSD当前地图标2026-03-02，2028–29高中图标2026-06-16。Dashboard reportingyear=2025，主要反映2024–25，prior=2023–24；2025 ELA/Math下载页更新2026-03-24。SARC标题2025与发布2026、学校计划2026–27及调查年份分别保存，绝不统一改成“2026成绩”。')
 h('边界、容量与已批准变化')
 table('重点路径（均未通过门牌结果确认）',['社区／区域','小学','中学／高中','证据与限制'],[[x['area'],x['elementary'],x['middle']+'／'+x['high'],x['evidence']+'；'+x['limit']]for x in c['boundaries'][:5]])
 p('其余官方分配表已纳入15行边界登记：Luna Park须区分Bosque以西与Chinon／Treble以东；Rise、Solis只覆盖IUSD部分；Portola Springs仅4、5区明确为Loma Ridge—Jeffrey Trail—Portola。IBC的IUSD部分为Culverdale／Westpark—South Lake，高中依具体位置为University或Woodbridge。Culverdale／Westpark共用Super Attendance Area，全年历与空间安排是实际约束。')
 p('Woodbury高中改界已获批准，从2028–29学年新入9年级起由Portola转Irvine High，小学与中学不变。官方公告的“当前6年级及以下／7–12不受影响”是公告当时的年级，不按本检索日重新套用；同时在Portola就读的兄弟姐妹可于2028年1月申请School Choice，不能把可申请写成保证录取。未来地图与批准文字交叉核对一致；未发现证据支持Stonegate或Reserve在该次调整中改界。')
 p('IUSD明确片区学校可能满额并安排其他学校；现有安排的延续与申请返校规则需要结合注册时间。官方地址定位器在本轮浏览器返回“不支持当前浏览器”，没有产生任何门牌结果。已为32条既有交易记录建立私有登记，官方逐址确认数为0；保留原营销学校信息与社区地图提示的证据等级，不静默覆盖成确认值。TUSD／SVUSD／CUSD也没有完成门牌确认或当年级余位。')
 table('IUSD 2026开发费研究的容量背景',['学段','测算容量','居住学区学生数','算术差额'],[[x['level'],x['capacity'],x['residence_students'],x['difference']]for x in c['capacity']])
 p('以上Table1采用2025年10月School of Residence口径及开发费研究的加载标准；总计39,439−37,706=1,733。它不是2026–27实时空位，不等于每个学校有富余，也不应与SARC实际就读人数直接相减。地理、项目、年级和高中目标规模会产生局部压力。Portola未来拥挤与Woodbury改界正说明全区总差额不能保证热点片区入学。')
 h('统一学业矩阵如何读')
 p('ELA／Math采用Dashboard距离标准分数（DFS，单位分），不是达标百分比；表内括号为该指标有效分母，不是全校人数。ELA与Math分母可以不同。参与率不足95%时存在最低分惩罚，公开长表另存参与率、惩罚计数和未加惩罚指标；空白仍为空白。ELPI是合资格英语学习者进步比例；CCI是满足州定义的大学／职业准备比例，不是大学录取率或名校去向。颜色组合当前水平与变动、受最小样本限制，不转成星级。')
 p('K–6、K–8、7–8与高中11年级测试组合不同；选择性、语言、特殊教育和经济条件影响校际构成。长表单列ALL、EL、SED、SWD，仅在同指标／同学年／同年级构成可比时解释；不对小群体缺失填零。当前值与前期值都经四舍五入，不能强行把已发布change改为两者显示值之差；年度学校均值变化也不是同一批学生的因果增值。')
 names=['Stonegate Elementary','Canyon View Elementary','Sierra Vista Middle','Northwood High','Eastwood Elementary','Portola Springs Elementary','Loma Ridge Elementary','Cypress Village Elementary','Woodbury Elementary','Jeffrey Trail Middle','Portola High','Irvine High','University High','Woodbridge High','Orchard Hills','Hicks Canyon Elementary','Myford Elementary','Arnold O. Beckman High']
 def score(x,i):return f"{x[i+'_currstatus']} (n={x[i+'_currdenom']})"if x[i+'_currstatus']else'未发布／不适用'
 table('重点及替代路径候选：2025 Dashboard',['学校／年级','英语DFS（n）','数学DFS（n）','ELPI%／CCI%（n）'],[[n+' '+ix[n]['grades_served'],score(ix[n],'ela'),score(ix[n],'math'),score(ix[n],'elpi')+'／'+score(ix[n],'cci')]for n in names])
 p('重点反例：Stonegate ELA83.2分、变化−7.0；Math67.0分、变化−3.8。Canyon View分别73.5、+5.9与63.6、+2.0。Stonegate水平较高并不意味着趋势较好，Canyon View改善也不能证明房屋增值。Northwood ELA82.3、CCI81.4%；University ELA35.1、CCI77.3%；两指标回答不同问题，不能用传统声誉替换当年数据，也不能用单年DFS否定整所学校。')
 comps=['El Toro High','Trabuco Hills High','Laguna Hills High','Tustin High','Foothill High','Aliso Niguel High','Aliso Viejo Middle','Don Juan Avila Middle','Portola Hills Elementary','Lake Forest Elementary']
 table('跨市同口径候选（不代表房源分配）',['学校／年级','英语DFS（n）','数学DFS（n）','CCI%（n）'],[[n+' '+x['grades_served'],score(x,'ela'),score(x,'math'),score(x,'cci')]for n in comps for x in matrix if x['school']==n])
 h('项目与实际进入条件')
 table('已核项目和待补领域',['项目','适用年级','进入条件','重要限制'],[[x['program'],x['grades'],x['entry'],x['limits']]for x in c['programs']])
 p('GATE识别与APAAS选拔是两条流程，APAAS不要求先获得GATE资格。官网2027–28申请窗口为2027-01-04至02-12 16:00，属于未来招生窗口。住房位置、项目录取、交通和课后照护四项需要分别验证。中文沉浸与英语学习支持亦不能互相代替；居住在华人较多的社区不会自动获得中文项目。')
 h('家长与学生体验：证据与分母')
 table('体验证据登记',['来源／年份','发现','分母与局限'],[[x['source']+'；'+x['period'],x['finding'],x['limits']]for x in c['experiences']])
 p('以上同时保留正面与负面材料。SPSA／LCAP是学校或学区发布的调查汇总，与匿名公开自述的偏差不同；两者都不能冒充独立随机访谈。Stonegate表中49%按原文登记为答题者自报经历，不能写成经调查认定的事件发生率；Canyon View Year3表未对齐明确公历学年和样本量，不能与其作学校安全排名。公开自述只提供后续核查问题，未认证发帖身份。已对51个CDS逐校完成公开家长／校园体验检索并保存查询及候选链接；候选页可能只是学校介绍或评论入口，也可能混入邻校评论。其余49所尚未完成与重点两校同等的全文、年份和语境核验；检索覆盖51/51不等于体验验证51/51，IUSD区级调查不能填充这些缺口。')
 h('复算、公开范围和下一验收')
 p(f"5份数值输入先校验SHA-256；独立分隔行解析核对{audit['independent_source_cells']:,}个字段；ELPI／CCI以Decimal按分子分母核对{audit['independent_ELPI_CCI_ratios']}组当年／前期比例；两校SPSA另核4个DFS数字。51个Irvine CDS唯一；同名charter不合并，Virtual C按官方定义分类。四张IUSD地图已目视核对。复算证明提取／算术一致，不证明教育因果、单址分配或未来座位。")
 p('公开仓库发布原创分析、事实性有限摘取、来源链接、校级公开统计及代码，不公开完整网页／地图／PDF、教师姓名联系方式或逐屋MLS底稿。CDE版权页的正文访问受机器人验证阻断，仅有索引摘要，未据此宣称所有材料可任意再分发；原始资料留研究档案。来源失败项与没有保存网页原件的检索笔记分开登记。')
 p('剩余学校验收：官方逐地址结果和年级注册／overflow记录；CDE行政目录与城市／服务边界最终排漏；全市AP／IB／CTE／艺术、照护等项目年级与门槛；各校家長体验及可比问卷分母；2026数据正式发布后再更新。已知缺项不阻断公共B其他模块。下一串行动作是住宅供给项目、审批／建设／交付与目标产品库存；然后补租赁全成本、定价和最终独立审阅。尚不进入家庭A/C。')
 h('Irvine目录完整附表')
 table('按CDS保留的51条Irvine地址记录',['学校','学区／类别','年级','英语／数学DFS'],[[x['school']+' ['+x['cds']+']',x['district']+'；'+x['category'],x['grades_served'],x['ela_currstatus']+'／'+x['math_currstatus']]for x in matrix if x['scope']=='irvine_address_directory'])
 h('主要官方入口与证据链接')
 urls=[('CDE目录及字段','https://www.cde.ca.gov/ds/si/ds/pubschls.asp'),('2026发布日程','https://www.cde.ca.gov/ta/ac/cm/alignrelease.asp'),('ELA下载','https://www.cde.ca.gov/ta/ac/cm/eladatafiles.asp'),('Math下载','https://www.cde.ca.gov/ta/ac/cm/mathdatafiles.asp'),('ELPI下载','https://www.cde.ca.gov/ta/ac/cm/elpidatafiles.asp'),('CCI下载','https://www.cde.ca.gov/ta/ac/cm/ccidatafiles.asp'),('IUSD边界／容量分配规则','https://iusd.org/about/iusd-enrollment/school-boundaries-assignments'),('Woodbury已批准变更',c['boundaries'][10]['source_url']),('Irvine服务学区',c['boundaries'][-1]['source_url'])]
 urls+= [(x['program'],x['source_url'])for x in c['programs']]+[(x['source'],x['source_url'])for x in c['experiences']]
 seen=set()
 for title,u in urls:
  if u not in seen:p(title+'：'+u);seen.add(u)
 p('完整来源、直接访问失败及指纹见data/sources.csv、data/school_source_manifest.json；正式文档对应的代码提交由交付记录补记。')
 md=[]
 for x in items:
  if x['kind']=='table':
   md.extend(['### '+x['title'],'','| '+' | '.join(x['rows'][0])+' |','| '+' | '.join(['---']*len(x['rows'][0]))+' |']);md.extend('| '+' | '.join(v.replace('|','／').replace('\n','；')for v in row)+' |'for row in x['rows'][1:]);md.append('')
  else:md.extend([('## 'if x['kind']=='heading'else'')+x['text'],''])
 (R/'reports/2026-10-12_schools_phase9.md').write_text('\n'.join(md));(a.private_out/'school_doc_plan.json').write_text(json.dumps(items,ensure_ascii=False,indent=2));print('items',len(items),'tables',sum(x['kind']=='table'for x in items),'cells',sum(sum(len(r)for r in x['rows'])for x in items if x['kind']=='table'))
if __name__=='__main__':main()
