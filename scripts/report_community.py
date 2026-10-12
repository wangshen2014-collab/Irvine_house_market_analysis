"""Create a Chinese phase report, exact tables, and GIS/statistical figures.

The detailed municipal overlay stays private; public maps contain Census shapes.
Optional --doc-plan writes a structured plan for scoped native Google Docs edits.
"""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as MPath
from shapely import make_valid, transform, union_all
from shapely.geometry import shape
from pyproj import Transformer

from build_community_geography import ROOT, RAW, MASTER, features

SG='1400000US06059052429';OH='1400000US06059052437'
MIX='1500000US060590524294';RES='1500000US060590524375';CORE='CUSTOM_SG_BG123'


def readcsv(p):return list(csv.DictReader(p.open()))


def charts(metrics):
    tf=Transformer.from_crs(4326,26911,always_xy=True)
    def proj(f):return transform(make_valid(shape(f['geometry'])),tf.transform,interleaved=False)
    bg={f['properties']['GEOID']:proj(f) for f in features('target_bgs_2024.geojson')}
    hoa=features('hoa_targets.geojson')
    masks={mid:union_all([proj(f) for f in hoa if f['properties']['MASTER_ID']==mid]) for mid in MASTER}
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':False,
                         'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False})
    def paint(ax,g,face,edge,lw=.9,alpha=1):
        # Compound paths preserve interior holes rather than painting over them.
        for p in getattr(g,'geoms',[g]):
            if p.geom_type!='Polygon':continue
            vertices=[];codes=[]
            for ring in [p.exterior,*p.interiors]:
                xy=list(ring.coords);vertices+=xy;codes += [MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY]
            ax.add_patch(PathPatch(MPath(vertices,codes),facecolor=face,edgecolor=edge,lw=lw,alpha=alpha))
    def base(ax,t):
        for gid,g in bg.items():
            if gid[:11]!=t:continue
            paint(ax,g,'#f1f3f5','#73808d')
        ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
        ax.annotate('N',xy=(.95,.94),xytext=(.95,.82),xycoords='axes fraction',ha='center',
                    arrowprops=dict(arrowstyle='-|>',color='#43515e'),fontsize=10,color='#43515e')
    def bar(ax,x,y,n,label):
        ax.plot([x,x+n],[y,y],color='#34434e',lw=2);ax.text(x+n/2,y-70,label,ha='center',va='top',fontsize=8)
    for private in [False,True]:
        fig,axs=plt.subplots(1,2,figsize=(12,7),gridspec_kw={'width_ratios':[1,1.15]})
        fig.subplots_adjust(top=.78,bottom=.21,left=.045,right=.985,wspace=.10)
        title='Neighborhood names do not equal Census boundaries'
        fig.text(.045,.95,title,fontsize=17,fontweight='bold',color='#183746')
        fig.text(.045,.899,'Frozen municipal HOA coverage + ACS 2024 Census geography' if private else
                 'Census-only public map: exact statistical units, explicitly limited proxies',fontsize=10,color='#516573')
        for ax,t in zip(axs,['06059052429','06059052437']):base(ax,t)
        if private:
            colors={'9.4':'#239a8d','9.3':'#e4a94c','1.1':'#5982ba','1.2':'#95a84c','1.3':'#bc648b'}
            for mid,g in masks.items():paint(axs[0 if mid.startswith('9') else 1],g,colors[mid],colors[mid],alpha=.5)
            legend=[Patch(facecolor=c,alpha=.6,label=MASTER[m]) for m,c in colors.items()]
            fig.legend(handles=legend,loc='lower center',bbox_to_anchor=(.5,.08),ncol=3,frameon=False,fontsize=9)
        else:
            for gid,g in bg.items():
                c='#a7d8cf' if gid in ['06059052429'+str(i) for i in [1,2,3]] else '#f7dca7' if gid=='060590524294' else '#e7bccf' if gid=='060590524375' else '#e7ebef'
                paint(axs[0 if gid[:11]=='06059052429' else 1],g,c,'#73808d')
            fig.legend(handles=[Patch(facecolor='#a7d8cf',label='Stonegate core proxy: BGs 1-3'),
                Patch(facecolor='#f7dca7',label='Mixed southern BG4'),Patch(facecolor='#e7bccf',label='BG5: Reserve + other areas')],
                loc='lower center',bbox_to_anchor=(.5,.09),ncol=3,frameon=False,fontsize=9)
        for gid,g in bg.items():
            if gid.startswith('06059052437') and gid[-1]!='5':continue
            ax=axs[0 if gid[:11]=='06059052429' else 1]
            p=g.representative_point()
            if gid=='060590524375':x,y=432850,3736800
            else:x,y=p.x,p.y
            ax.text(x,y,'BG'+gid[-1],fontsize=10,fontweight='bold',ha='center',color='#233f4f',
                    bbox=dict(facecolor='white',alpha=.75,edgecolor='none',pad=1.5))
        axs[1].annotate('BG1-4',xy=(429650,3733000),xytext=(429150,3730750),ha='center',fontsize=9,
                        arrowprops=dict(arrowstyle='-',color='#43515e'),color='#233f4f')
        axs[0].set_xlim(430250,432550);axs[0].set_ylim(3728450,3731350)
        axs[1].set_xlim(428550,435650);axs[1].set_ylim(3730550,3739700)
        axs[0].set_title('Tract 524.29\nStonegate + Stonegate East context',fontsize=11,loc='left',pad=10)
        axs[1].set_title('Tract 524.37\nOrchard Hills context; Reserve lies within mixed BG5',fontsize=11,loc='left',pad=10)
        bar(axs[0],430400,3728750,500,'500 m');bar(axs[1],433900,3731150,1000,'1 km')
        fig.text(.045,.035,'Sources: U.S. Census Bureau TIGERweb ACS2024; City of Irvine HOA snapshot 2026-10-11 (private overlay only).\nEach panel has its own scale. HOA coverage omits some roads/open land; it is not a certified legal village boundary.',fontsize=8,color='#53636e')
        dest=RAW/'community_hoa_overlay' if private else ROOT/'figures/community_census_scope'
        fig.savefig(dest.with_suffix('.png'),dpi=180,facecolor='white')
        if not private:fig.savefig(dest.with_suffix('.svg'),facecolor='white')
        plt.close(fig)
    # Detailed Reserve inset makes the residential mixing visible at legible scale.
    fig,ax=plt.subplots(figsize=(10,7));fig.subplots_adjust(left=.05,right=.97,top=.78,bottom=.16)
    fig.text(.05,.94,'Reserve shares BG5 with part of Groves',fontsize=17,fontweight='bold',color='#183746')
    fig.text(.05,.89,'The ACS estimate for BG5 cannot be assigned solely to Reserve',fontsize=11,color='#53636e')
    base(ax,'06059052437')
    for mid,c in [('1.1','#5982ba'),('1.2','#95a84c'),('1.3','#bc648b')]:paint(ax,masks[mid],c,c,alpha=.45)
    for gid,g in bg.items():
        if gid[:11]=='06059052437':paint(ax,g,'none','#42596c',1.2)
    for mid,offset in [('1.1',(-50,0)),('1.2',(0,0)),('1.3',(0,0))]:
        p=masks[mid].representative_point();ax.text(p.x+offset[0],p.y+offset[1],{'1.1':'Groves','1.2':'Village II','1.3':'Reserve'}[mid],ha='center',fontsize=12,fontweight='bold')
    ax.text(431000,3735700,'BG5 continues north / east into open land',fontsize=10,ha='center')
    ax.set_xlim(428800,432500);ax.set_ylim(3731800,3736000);bar(ax,428980,3732020,500,'500 m')
    fig.text(.05,.05,'City of Irvine HOA geometry and Census ACS2024 BGs. For research verification; not legal boundary certification.\nBG5 includes 2020 housing blocks associated with both communities. No area-based income allocation is used.',fontsize=9,color='#53636e')
    fig.savefig(RAW/'reserve_boundary_detail.png',dpi=180,facecolor='white');plt.close(fig)
    labels=['Stonegate core proxy\nBG1-3 only','Tract 524.29\nStonegate + East context',
            'BG4 of 524.29\nMixed southern area','BG5 of 524.37\nReserve + other areas','Tract 524.37\nOrchard Hills context']
    ids=[CORE,SG,MIX,RES,OH]
    fig,axs=plt.subplots(1,3,figsize=(12,5),sharey=True);fig.subplots_adjust(left=.22,right=.98,top=.76,bottom=.21,wspace=.13)
    fig.text(.04,.94,'Boundary choice changes the household profile',fontsize=17,fontweight='bold',color='#183746')
    for ax,name,title in zip(axs,['owner_share','households_under18_share','households_income200kplus_share'],['Owner-occupied','Any household member <18','Household income >= $200k']):
        for y,gid in enumerate(ids):
            r=metrics[gid,name];n=float(r['estimate'])*100;m=float(r['moe90'])*100
            ax.errorbar(n,y,xerr=m,fmt='o',color='#167f79',capsize=3,ms=6,lw=1.5)
            ax.text(n,y-.17,f'{n:.1f}%',fontsize=9,ha='center',color='#214151')
        ax.set_xlim(0,100);ax.set_xticks([0,25,50,75,100]);ax.set_title(title,fontsize=10,pad=18)
        ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.set_xlabel('Percent',fontsize=9)
    axs[0].set_yticks(range(len(ids)),labels);axs[0].invert_yaxis()
    fig.text(.04,.065,'Source: ACS 2020-2024, B25003 / B11005 / B19001. Error bars: 90% MOE using 80 SDR replicates.\nThese are overlapping statistical geographies, not five independent communities. Sampling MOE does not measure boundary bias.',fontsize=9,color='#53636e')
    fig.savefig(ROOT/'figures/community_scope_metrics.svg',facecolor='white');fig.savefig(RAW/'community_scope_metrics.png',dpi=180,facecolor='white');plt.close(fig)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--doc-plan',type=Path);a=ap.parse_args()
    rr=readcsv(ROOT/'data/clean/acs_community_metrics_2024.csv');m={(r['geo_id'],r['metric']):r for r in rr}
    charts(m)
    def fmt(g,k):
        r=m[g,k]
        if r['display']:return '$'+r['display'] if 'income' in k else r['display']
        if not r['estimate']:return '不发布／不合成'
        n=float(r['estimate']);e=float(r['moe90']) if r['moe90'] else None
        if r['unit']=='fraction':return f'{n*100:.1f}% ± {e*100:.1f}pp' if e is not None else f'{n*100:.1f}%'
        if r['unit']=='years':return f'{n:.1f} ± {e:.1f}'
        return (f'${n:,.0f} ± ${e:,.0f}' if r['unit']=='2024_USD' else f'{n:,.0f} ± {e:,.0f}') if e is not None else f'{n:,.0f}'
    geo_table=[['对象','冻结口径','Census 对应','可解释范围'],
        ['Stonegate','MASTER_ID 9.4；9个HOA要素合并','06059052429；BG1–4','有独立覆盖范围；BG4与Stonegate East混合'],
        ['Stonegate East','MASTER_ID 9.3；4个要素合并','060590524294','独立保留，不能随PA9一并当Stonegate'],
        ['Orchard Hills','父PA1；另列Groves与Village II','主体在06059052437，PA1还跨其他tract','父规划区、市场社区、已建住宅覆盖范围不同'],
        ['Reserve','MASTER_ID 1.3；OBJECTID 336','060590524375','全部落入BG5；BG5同时含Groves部分，不能单独识别Reserve']]
    metric_table=[['统计范围（不是精确社区）','家庭户数','自有住房占比','有未成年人家庭','收入≥$200k家庭']]
    for gid,label in [(CORE,'Stonegate主体代理：BG1–3'),(SG,'524.29混合tract'),(MIX,'524.29的混合BG4'),(RES,'524.37的混合BG5'),(OH,'524.37整体tract')]:
        metric_table.append([label,*[fmt(gid,k) for k in ['households_total','owner_share','households_under18_share','households_income200kplus_share']]])
    age_table=[['统计范围','户主25–44岁占比¹','年龄中位数','家庭收入中位数²']]
    for gid,label in [(CORE,'Stonegate主体代理：BG1–3'),(SG,'524.29混合tract'),(RES,'524.37混合BG5'),(OH,'524.37整体tract')]:
        age_table.append([label,fmt(gid,'householders25_44_share'),fmt(gid,'median_age'),fmt(gid,'median_household_income')])
    items=[]
    def para(text,style='NORMAL_TEXT'):items.append(dict(kind='paragraph',text=text,style=style))
    def table(rows):items.append(dict(kind='table',rows=rows))
    def img(path,caption):items.append(dict(kind='image',path=str(path),caption=caption))
    para('需求：社区边界与画像｜阶段四','TITLE')
    para('研究日期：2026-10-11（America/Los_Angeles）。独立公共市场B；只使用公开来源。本轮完成可复算的空间口径与统计代理区诊断，尚未取得精确Reserve家庭画像或买入／等待结论。')
    para('一、最重要的结果','HEADING_1')
    para('已经取得Stonegate、Stonegate East、Groves、Orchard Hills Village II与Reserve的市政府HOA覆盖多边形，并与Census地理单元匹配。冻结的是可追溯的研究覆盖范围，不是对产权、法律边界或完整市场社区的认证。HOA图层包含公寓子区，也可能排除公路、学校、空地及未纳入范围。')
    para('不能把整个524.37 tract或其BG5的收入贴给Reserve。Reserve覆盖范围全部位于BG5，但BG5同时覆盖Groves部分及大片其他土地；2020住房街区也显示两个社区的住宅混在这个单元内。继续缩小到人口普查block仍无法取得同尺度的ACS收入。')
    para('Stonegate可使用完整BG1–3作为明确命名的主体代理区，同时另列BG4混合区。主体代理自有住房占比63.5%±9.7pp，有未成年人家庭58.9%±8.3pp；混合tract对应为50.2%±9.7pp和44.9%±8.7pp。差异说明口径敏感，不能择取更合偏好的边界来代表整个Stonegate。')
    para('二、社区名称与统计边界','HEADING_1');table(geo_table)
    para('修正前轮PA对照的使用方式：规划文件把9B与9C2列在Stonegate名称下，但本轮市政府HOA属性明确区分Stonegate Village（9.4）与Stonegate East（9.3）。原PA映射只作规划父区索引，不能据此把两者合为市场社区。实际查询属性是依据，图层旧图例名称不能替代当前要素属性。')
    para('HOA快照取得于2026-10-11；Reserve要素EditDate为2025-06-11 UTC，Stonegate选中要素的最新编辑为2026-09-29 UTC。PA图层描述仍写2021年，数据编辑时间是2022-08-24 UTC，不能把检索日当作边界生效日。Census采用2020 tract/BG定义在ACS2024服务中的几何；两处目标tract的2020与2024边界已用对称差核查。')
    img(RAW/'community_hoa_overlay.png','图1｜市政府HOA覆盖范围与Census tract/BG。左右比例尺不同；彩色HOA面不代表完整法律村界。')
    img(RAW/'reserve_boundary_detail.png','图2｜Reserve局部核查。Reserve与Groves部分共用BG5，空地面积占比不能转化为家庭权重。')
    para('三、可使用的家庭结构数字','HEADING_1');table(metric_table)
    para('全部为2020–2024 ACS五年期间估计，±为90%抽样误差；比例的误差单位是百分点。户数是有人居住的住房单元／家庭户，不是新迁入户数、目标房型买家或2026年实时户数。三个占比及主体代理聚合户数使用80次SDR重复估计，包含可计算的协方差。')
    para('有未成年人家庭按B11005定义为家中有任何18岁以下成员，不等于有自己孩子的家庭。收入≥$200k是税前现金收入代理，顶档无法细分$300k或$500k；不识别资产、首付、购房意愿或四卧无共墙交集。')
    img(RAW/'community_scope_metrics.png','图3｜边界选择的影响。各行统计区相互包含或重叠，不能作为五个相互独立的社区排名。')
    table(age_table)
    para('¹ 户主年龄比例使用RSS与子集比例近似MOE，未宣称为SDR。² 524.37 BG5家庭收入中位数约$197,679±$107,511，相对误差很大，而且是混合区；不支持“Reserve收入约20万美元”的精确表述。不能平均BG中位数得到Stonegate主体中位数，所以保留不合成。')
    para('524.29 BG3的家庭收入中位数和524.29 tract的业主收入中位数落在开放顶档，源数据代码250001、MOE为-333333333；只显示$250,000+，不写成精确$250,001，也不把缺失误差当零。')
    para('官方B25115（租买×自有子女）、B25118（租买×收入）、B25119（租买×收入中位数）在本次完整批量文件中只有目标tract行，没有9个目标BG行。缺项逐表登记；不下推父tract值，不把边际占比相乘伪造高收入有孩租客。')
    para('四、为什么拒绝面积加权与旧住房权重','HEADING_1')
    para('Reserve的HOA覆盖面约102.9公顷，占混合BG5总几何面积约4.29%；这是土地几何比例，不是家庭比例。BG5中住宅集中在局部，大片山地和空地没有同等人口。')
    para('2020街区诊断进一步显示分配不稳：以Census内部点落入Reserve覆盖面计，关联236个住房单元；改为街区面积多数落入则为353；只要求任何面积相交则为445。这三个数字都是规则敏感性诊断，不是Reserve真实户数的置信区间或已确认上下界，且住房单元包含空置。内部点也不是住宅坐标。')
    para('Stonegate主体BG1–3的2020住房单元合计2,588，在内部点和多数面积两种规则下均落入Stonegate覆盖面，支持把它们作为较贴近主体的代理。但BG4仍包含Stonegate的南侧住宅；因此BG1–3既不是完整Stonegate，也不能用于对全部社区总量作确定性上下界。2020分布无法假定代表2024或2026，尤其Reserve在建与入住阶段变化明显。')
    para('2020年6月市规划材料把Fresco明确定位为Orchard Hills Neighborhood 3内的Tract 18018，并给出与母地块16530的关系；该开发登记编号不是Census tract。相关位置图与PA1地址图作人工空间交叉核查，审批数量不当作本轮已建、已售或入住统计。')
    para('五、验收与剩余误差','HEADING_1')
    para('本轮新冻结21份原始数据／元数据文件，并复核13份此前取得的ACS批量表及元数据指纹。614个橙县tract用于覆盖检查，重点核对2个tract、9个BG、195个2020街区；产出39条空间对应、975条社区×街区诊断、45条BG住房诊断、1,452个ACS细项和276个指标记录。')
    para('空间47项检查通过：完整街区人口／住房合计等于2020父tract发布总数，街区与BG几何合并还原父区，目标2020／2024 tract一致性检查，以及UTM投影面积与椭球面积交叉核对。原始几何有2个HOA面和1个Census街区自交，make_valid修复面积变化低于0.000001平方米；原始字节保留。Village II与Reserve图层间约1.52平方米的接缝重叠保留登记，不冒充严格互斥产权边界。')
    para('统计765项检查通过，其中包含429组Summary File与VRE发布E/M逐项一致；这是同一调查的不同发布格式交叉核对，不是独立人口调查。65项派生指标使用SDR，其他近似MOE明示；55条指标按CV>30%的研究提示线标为高不确定性。未运行第二模型或多智能体审阅，不能把脚本复算写成已完成Astra独立审查。')
    para('抽样MOE没有覆盖社区边界差异、当前HOA与历史ACS时点错位、缺失地块、非抽样误差或目标产品筛选误差。小区域的精确收入、年龄或持有意愿不能因检验通过而视为已知。完整北尔湾边界、全市候选、学校、供给兑现、融资与定价仍待后续模块。')
    para('六、下一项工作与复算入口','HEADING_1')
    para('下一轮推进20–30笔跨社区实际成交／租赁试采集，至少5笔人工核对，用本轮HOA覆盖范围辅助归属，边界附近与未覆盖地址人工保留待核。逐笔区分建筑共墙、法律产权、面积、卧室、房龄、成交日期和租售口径，先验证字段可得性及使用条件。当前成交0/20–30、人工成交核对0/5；本轮195个街区不是成交样本。')
    para('公开仓库保存代码、标准统计摘取、来源索引、QA、Census底图和本报告；市政府原始多边形及含其边界的详细图留指定资料档案。公开可访问不自动等于允许整份再分发。复算：python scripts/build_community_geography.py --download；python scripts/build_community_acs.py --download；python scripts/report_community.py。官方同URL数据变更时脚本拒绝静默覆盖。')
    para('主要证据入口','HEADING_1')
    for label,url in [
        ('市政府HOA实际要素查询与图层','https://gis.cityofirvine.org/arcgis/rest/services/Parcel_Pro/MapServer/9'),
        ('市政府Planning Areas版本与说明','https://www.arcgis.com/home/item.html?id=6a83e6acf99843d992802a12840b6454'),
        ('Census ACS2024 tract几何','https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/8'),
        ('Census ACS2024 block group几何','https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/10'),
        ('2020 Census街区与人口／住房','https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer/10'),
        ('2024 ACS地理定义及边界变更注释','https://www.census.gov/programs-surveys/acs/geography-acs/geography-boundaries-by-year/2024.html'),
        ('官方ACS批量数据与元数据','https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/'),
        ('2024五年VRE文件及文档','https://www2.census.gov/programs-surveys/acs/replicate_estimates/2024/'),
        ('ACS开放区间／特殊值说明','https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html'),
        ('Fresco官方规划材料（2020-06-04）','https://irvine.granicus.com/MetaViewer.php?event_id=1634&meta_id=105426&view_id='),
        ('开发商Reserve社区名称与配套参考','https://www.villagesofirvine.com/homes/reserve-at-orchard-hills')]:
        items.append(dict(kind='link',text=label,url=url))
    md=[]
    for it in items:
        if it['kind']=='paragraph':md.append(('# ' if it['style']=='TITLE' else '## ' if it['style']=='HEADING_1' else '')+it['text'])
        elif it['kind']=='table':
            rows=it['rows'];md.append('\n'.join(['| '+' | '.join(rows[0])+' |','|'+'---|'*len(rows[0])]+['| '+' | '.join(row)+' |' for row in rows[1:]]))
        elif it['kind']=='link':md.append('['+it['text']+']('+it['url']+')')
        elif 'community_scope_metrics' in it['path']:md.append('![指标及误差](../figures/community_scope_metrics.svg)\n\n'+it['caption'])
        else:md.append(it['caption']+'（详细叠加图保存在正式阅读版；公开统计区底图见下方。）')
    md.insert(7,'![Census统计区与代理范围](../figures/community_census_scope.svg)')
    (ROOT/'reports/2026-10-11_community_boundaries_phase4.md').write_text('\n\n'.join(md)+'\n')
    if a.doc_plan:a.doc_plan.write_text(json.dumps(dict(title='需求：社区边界与画像',items=items),ensure_ascii=False,indent=2))
    print('Report, 3 figures + private detail, and structured tables generated.')


if __name__=='__main__':main()
