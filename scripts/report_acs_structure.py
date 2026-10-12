"""Generate the stage report and plot from the checked, versioned ACS tables."""
import argparse
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
CITIES=['Irvine','Lake Forest','Tustin','Aliso Viejo']


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--doc-plan',type=Path);args=ap.parse_args()
    with (ROOT/'data/clean/acs_household_metrics_2024.csv').open() as f:metrics={(r['dataset'],r['geography'],r['metric']):r for r in csv.DictReader(f)}
    with (ROOT/'data/clean/acs_replicate_metrics_2024.csv').open() as f:
        for r in csv.DictReader(f):metrics[r['dataset'],r['geography'],r['metric']].update(moe90=r['moe90'],moe_method=r['moe_method'])
    with (ROOT/'data/clean/acs_household_window_changes.csv').open() as f:changes={(r['geography'],r['metric']):r for r in csv.DictReader(f)}
    def cell(g,name,ds='ACS2024_5YR'):return metrics[ds,g,name]
    def fmt(g,name,ds='ACS2024_5YR'):
        r=cell(g,name,ds);e,m=float(r['estimate']),float(r['moe90']) if r['moe90'] else None
        if r['unit']=='fraction':return f'{100*e:.1f}%'+(f' ±{100*m:.1f}pp' if m is not None else '（MOE不适用／未提供）')
        if r['unit']=='2024_USD':return f'${e:,.0f}'+(f' ±${m:,.0f}' if m is not None else '')
        if r['unit']=='years':return f'{e:.1f} ±{m:.1f}'
        return f'{e:,.0f}'+(f' ±{m:,.0f}' if m is not None else '')
    blocks=[]
    def text(kind,s):blocks.append(dict(kind=kind,text=s))
    def table(rows):blocks.append(dict(kind='table',rows=rows))
    text('title','需求：家庭结构与购买力｜阶段三')
    text('body','研究日期：2026-10-11（America/Los_Angeles）。独立公共市场B；本轮为城市家庭结构及购买力代理指标，不含私人家庭财务，也未形成完整买入／等待结论。')
    text('heading','一、目前最支持的判断')
    text('body','Irvine有规模可观的高收入家庭和高收入租客；但两个不重叠ACS窗口之间，家庭数量增加主要体现为租客存量增加。四城有未成年人家庭的占比均约三分之一，Irvine的点估计并没有明显高于替代城市。人口／家庭增长、高收入居民存量、准备购买高价四卧的家庭，是三件不同的事。')
    text('body','这些证据支持继续检验租转买、换房和外来买家承接能力；不足以证明目标房型会长期供不应求，也不能由城市中位收入反推某套房的公允价格。后续须接入社区边界、目标产品、实际成交与融资证据。')
    text('heading','二、版本与可比性先冻结')
    text('body','2025 ACS一年数据尚未发布：Census当前更新页仍列发布日期待确定。本轮取得2024一年表（2025-09-11发布）、2020–2024五年表（2026-01-29发布），以及2015–2019五年表。四城统一比较采用五年表；一年表另列，不与五年表相减。五年表是期间估计，不是2024-12-31快照，也不代表五年累计迁入／累计成交。')
    text('body','Aliso Viejo未出现在标准一年地理文件中。Lake Forest和Tustin虽有标准一年表，本次B07001／B07010全国官方下载文件中仍没有这两城对应行；记录为表级不可得，不补零，不拿五年值冒充一年值。2019旧格式GEOID按明确规则补齐当前格式，再用地理名称、州、Summary Level、Component和LOGRECNO核对。城市代码相同不保证历年边界完全不变；边界统一和控制人口修订仍是历史解释限制。')
    text('heading','三、四城家庭结构：共同五年窗口')
    table([['城市','家庭总数','业主占比','有未成年人家庭','收入≥$200k家庭']]+[[g,fmt(g,'households_total'),fmt(g,'owner_share'),fmt(g,'households_under18_share'),fmt(g,'households_income200kplus_share')] for g in CITIES])
    text('body','所有“±”为90%抽样误差范围；pp为百分点。家庭总数使用发布的MOE，后三列比例使用80次方差重复估计SDR计算，纳入分子与分母的协方差。有未成年人表示家中至少一人未满18岁，包含非亲生子女等关系；与后文“户主自己的子女”口径不同。')
    text('body','Irvine业主占比约44.5%，低于Lake Forest约70.5%；这首先描述住房存量和居住结构，不能单独解释为买家不足。Irvine≥$200k家庭占比约32.3%，与Lake Forest约31.3%、Aliso Viejo约30.1%的差距较小，误差范围重叠；不能排列出确定的购买力名次。Irvine年轻户主及租客较多，学生、职业流动、住房供给形态都可能参与形成这种结构。')
    table([['城市','年龄中位数','25–44岁户主占比','业主收入中位数','租客收入中位数']]+[[g,fmt(g,'median_age'),fmt(g,'householders25_44_share'),fmt(g,'median_owner_income'),fmt(g,'median_renter_income')] for g in CITIES])
    text('body','Irvine年龄中位数34.0岁，25–44岁户主占比42.3%（近似MOE±1.7pp）。这是一种居住结构，并不等于对应家庭正在形成首付或准备买房。收入均为2024通胀调整美元，属于ACS现金收入口径，不是资产净值、可动用首付或银行核定收入；资本利得、借款、资产变现等不能由此完整推断。已有业主还可能持有低利率贷款与长期房屋净值，不能用其收入直接代表今天首次购入所需的收入。')
    text('heading','四、家庭增量：租客、业主、有孩分别看')
    table([['城市','家庭总数变化','业主户数变化','租客户数变化','有未成年人家庭变化']]+[[g]+[f"{float(changes[g,k]['change']):+,.0f} ±{float(changes[g,k]['change_moe90']):,.0f}" for k in ['households_total','owner_households','renter_households','households_under18']] for g in CITIES])
    text('body','比较2015–2019与2020–2024两个不重叠窗口。Irvine总户数98,281→112,091，增加13,810±1,945；租客52,264→62,261，增加9,997±2,112；业主46,017→49,830，增加3,813±1,793。点估计中，租客户数变化约占总户数变化72.4%。这是两个期间存量的变化贡献，不是新增家庭流入比例、年度增长率、租转买概率，也不是新建住房的租赁比例。')
    text('image','acs_irvine_household_windows.png')
    text('caption','图：Irvine租客和业主家庭存量，两个不重叠ACS五年窗口。原始统计来源：U.S. Census Bureau，B25003；窗口不能视为年末快照。')
    text('body','Irvine有未成年人家庭34,612→37,661，增加3,049±1,525；占比35.2%→33.6%，点估计下降1.62pp，差值MOE约±1.50pp，属于边缘的90%名义显著结果，不能据此断言稳定的结构性下滑。家庭户占比及65岁以上户主占比的变化没有足够证据排除抽样波动。多个比较未经多重检验校正，不用单个接近门槛的p值决定购房。')
    text('body','Aliso Viejo租客点估计增加1,116户，业主仅增加2户，后者远小于误差；不能写成业主实际没有增长。Lake Forest有未成年人家庭增加136±685户，未能排除零变化。ACS与DOF的时点、期间、控制和估计方式不同，不能以其中一表强行覆盖另一表；这也说明上一轮DOF已入住户近乎固定的城市仍需要独立核对。')
    text('heading','五、购买力：可见收入存量，买家交集尚未识别')
    text('body',f"Irvine五年窗口约有{fmt('Irvine','households_income200kplus')}户收入≥$200k；收入≥$150k的租客{fmt('Irvine','renter_income150kplus')}户，占租客{fmt('Irvine','renter_income150kplus_share')}。有户主自己的未成年子女的租客{fmt('Irvine','renter_with_own_children')}户，占租客{fmt('Irvine','renter_with_own_children_share')}。后两项来自已交叉的租买／收入、租买／子女表，误差采用标注的近似法。")
    text('body','不能把收入占比、租客占比、孩子占比与年龄占比相乘来制造“目标买家数量”：它们不是独立变量。这些表没有给出“高收入＋租客＋有孩＋首付充足＋愿意买指定房型”的联合交集；B19001最高收入档为≥$200k，B25118最高档为≥$150k，也无法分出$300k或$500k收入家庭。不得把所有高收入家庭视为新增买家：其中包括已有业主、长期选择租住者、不同房型需求及同一家庭重复出现在不同边际统计中。')
    text('body',f"2024一年表另显示Irvine家庭{fmt('Irvine','households_total','ACS2024_1YR')}户，≥$200k收入占比{fmt('Irvine','households_income200kplus_share','ACS2024_1YR')}。该结果可补充较近时期的结构，但不能与五年点估计相减得出最近一年新增买家。未以不同美元基准的2019与2024收入直接计算实际购买力增长。")
    text('heading','六、迁入结构：不等于净迁移，也不等于富裕买家')
    text('body','Irvine 2024一年表中，现居居民上一年从加州其他县迁来14,791±2,655人，从其他州迁来7,241±2,901人，从境外迁来8,535±2,401人；这里是1岁及以上的人，不是家庭。县内搬家包括同一城市内换住处，不能全部当成外来需求。境外原居地不等于移民身份；以上都是当前居民的迁入侧，没有迁出侧，不能计算城市净迁移。五年表同类字段仍是期间内“过去一年居住地”估计，不把它乘五当五年总量。')
    text('body','B07011收入是15岁以上且有收入者的个人收入，不是家庭收入。Irvine一年表中，原居加州其他县的人个人收入中位数$11,402±$4,085，从其他州迁来者$72,343±$13,791，从境外迁来者$26,348±$12,910。未分层学生、就业、年龄与家庭成员，也不测资产，不能据此声称迁入者更富裕或更贫穷。Lake Forest／Aliso Viejo部分境外迁入收入单元被官方标注不可计算，保留空值。')
    text('heading','七、验收、限制与下一动作')
    text('body','本轮49个官方数值／地理／元数据来源文件均保存完整字节指纹：2024为32份，2019为11份，VRE为6份。标准细项2024为2,781行、2019为1,725行，共4,506行；常规指标305＋60行、跨窗口比较60行、重复估计指标25行。195个关键E／MOE单元在另一份官方发布格式中逐项一致。表级缺失、特殊值和误差口径均已登记。验证算术、地理身份和提取一致，不验证调查无误或市场因果。')
    text('body','缺口仍包括：社区精细边界与Census tract叠加；高收入、有孩、年龄、资产与买房意愿的联合交集；流入／流出、实际购房融资与目标产品承接；成交试样本仍0/20–30、人工成交核对0/5。HMDA、IRS流向、学校、项目兑现与资产定价未验收。此阶段未冒充完整公共B或独立Astra复核。')
    text('body','下一动作：完成Stonegate、Orchard Hills及Reserve子区的社区边界与2020 Census tract/GEOID叠加，登记整块／部分重合及人口分配误差，不能把PA9或跨城市PUMA全部当作Stonegate。随后再把目标产品成交与融资数据接到购买力分析。')
    text('heading','八、主要来源与复算')
    sources=[('Census 2026 ACS更新与2025发布状态','https://www.census.gov/programs-surveys/acs/news/updates.html'),
             ('2024官方Summary File与下载入口','https://www.census.gov/programs-surveys/acs/data/summary-file.2024.html'),
             ('2019官方Sequence-Based Summary File','https://www.census.gov/programs-surveys/acs/data/summary-file/sequence-based/2019.html'),
             ('2024数据比较规则','https://www.census.gov/programs-surveys/acs/guidance/comparing-acs-data/2024.html'),
             ('2024方差重复估计及技术说明','https://www.census.gov/programs-surveys/acs/data/variance-tables/2024.html'),
             ('ACS收入概念','https://www2.census.gov/programs-surveys/acs/tech_docs/subject_definitions/2024_ACSSubjectDefinitions.pdf')]
    for label,url in sources:blocks.append(dict(kind='link',text=label,url=url))
    text('body','复算顺序：python scripts/build_acs_household_structure.py --download；python scripts/refine_acs_moe.py --download；python scripts/build_acs_history.py --download；python scripts/report_acs_structure.py。原始文件指纹变化时停止并登记新版本；下载首次耗时较长，后续使用已核对的缓存。公开仅统计摘取、指纹、脚本、QA与原创分析，原始文件包及私人入口不写进公开仓库。')
    md=[]
    for b in blocks:
        k=b['kind']
        if k=='table':
            rs=b['rows'];md.append('| '+' | '.join(rs[0])+' |\n| '+' | '.join(['---']*len(rs[0]))+' |\n'+'\n'.join('| '+' | '.join(row)+' |' for row in rs[1:]))
        elif k=='title':md.append('# '+b['text'])
        elif k=='heading':md.append('## '+b['text'])
        elif k=='image':md.append('![Irvine households across ACS windows](../figures/acs_irvine_household_windows.svg)')
        elif k=='link':md.append(f"[{b['text']}]({b['url']})")
        elif k=='caption':md.append('*'+b['text']+'*')
        else:md.append(b['text'])
    (ROOT/'reports/2026-10-11_acs_household_structure_phase3.md').write_text('\n\n'.join(md)+'\n')
    if args.doc_plan:args.doc_plan.write_text(json.dumps(dict(blocks=blocks),ensure_ascii=False,indent=2)+'\n')
    a=changes['Irvine','owner_households'];b=changes['Irvine','renter_households']
    fig,ax=plt.subplots(figsize=(7.7,4.9))
    owners=[float(a['old_estimate']),float(a['new_estimate'])];renters=[float(b['old_estimate']),float(b['new_estimate'])]
    x=[0,1];ax.bar(x,owners,color='#476c8f',width=.52,label='Owner households');ax.bar(x,renters,bottom=owners,color='#89b7bd',width=.52,label='Renter households')
    for i in x:
        ax.text(i,owners[i]/2,f'{owners[i]:,.0f}',ha='center',va='center',color='white',fontsize=12)
        ax.text(i,owners[i]+renters[i]/2,f'{renters[i]:,.0f}',ha='center',va='center',color='#183942',fontsize=12)
        ax.text(i,owners[i]+renters[i]+2200,f'{owners[i]+renters[i]:,.0f}',ha='center',va='bottom',fontsize=12,fontweight='bold')
    ax.set_xticks(x,['2015–2019','2020–2024']);ax.set_ylim(0,127000);ax.set_ylabel('Occupied households');ax.set_title('Irvine: two non-overlapping ACS windows',loc='left',fontsize=14,pad=18)
    ax.spines[['top','right']].set_visible(False);ax.yaxis.grid(True,alpha=.15);ax.set_axisbelow(True);ax.legend(loc='upper left',frameon=False,bbox_to_anchor=(1.02,1))
    fig.text(.12,.015,'Source: U.S. Census Bureau, ACS 5-year B25003. Period estimates, not year-end snapshots.',fontsize=8.5,color='#555555');fig.tight_layout(rect=(0,.05,1,1))
    for ext in ['svg','png']:fig.savefig(ROOT/f'figures/acs_irvine_household_windows.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    print('Stage report, native-doc content plan and plot generated.')


if __name__=='__main__':main()
