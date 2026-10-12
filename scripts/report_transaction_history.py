#!/usr/bin/env python3
"""Build original public methods report and optional private Google Docs plan."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def public_report(q):
    m = q["metrics"]
    return f"""# 产品分组、挂牌时间线与三卧租赁｜阶段六

研究观察截止：2026-10-11，America/Los_Angeles。检索窗口2024-10-12至2026-10-11。本轮延续阶段五的25笔非随机售房试样本，完成公开可见历史扩展及三卧租赁补采；完整公共B、全市场历史和买入／等待判断仍未完成。

## 完成与修正

- 25笔售房各有可追溯的挂牌与关闭字段。形成{m['event_rows']}条来源事件观察，其中{m['in_window_event_rows']}条在窗口内、1条窗口前置事件；包括重复关闭的冲突分支，不能把事件行数当交易数量。
- 暂分{m['candidate_product_strata']}个产品小组，按社区、卧室、面积、建年和共墙拆开。小组只是候选分层；相同面积不证明同户型，地段硬伤、景观和升级未核，尚无同品质价格指数。
- 新发现一笔卧室数跨字段冲突，前轮22条较稳定四卧无共墙候选修正为{m['stable_profile_candidates']}条。再排除重大成交价冲突后为{m['profile_and_price_candidates']}条；这些仍不是已核可比成交。
- 新增{m['new_three_bed_closed_leases']}笔三卧、整租、无家具、至少12个月且发布无共墙的MLS关闭记录。另3笔候选因整租／单间、日期或租赁条件冲突排除。与前轮3笔四卧关闭记录合计7笔，不能混算全市场租金。

## 时间线定义

分别保存售房挂牌、重新挂牌、调价、撤牌、取消、到期、Contingent、Pending、MLS关闭、网站转述Public Record，以及租赁挂牌／撤牌／关闭。网站转述记录日不是已取得契据日，撤牌不等于成交。跨MLS按同一房屋串联，但旧挂牌结束日缺失时，不推断连续营销。

至少3个售房案例可见多个不同MLS编号；只按最新编号会缩短可见历史。程序同时给出最早可见挂牌、本次MLS首挂及最近一次重新上线至关闭的日历跨度。所有跨度均包含可能的下架及成交托管时间，不能认定实际在市天数或CDOM；25笔实际签约DOM及完整MLS史仍各0/25。

挂牌价差使用“关闭价／观察到的挂牌价－1”，分别对最初可见价和最后可见价计算。它衡量个案相对报价的差异，不是市场价格变动；最初可见价不保证真正初始价，最后可见价不保证完整历史中的最终价。重大价格冲突不计算价差，也不以多数网站表决消除矛盾。

实际售房关闭日期仍为{m['sale_date_min']}至{m['sale_date_max']}，没有2024年末的已核MLS关闭样本。季度统计只表示固定样本覆盖，缺样季度不表示当地无成交；不足以估计近24个月涨跌、市场成交量、库存、去化速度或因果机制。

## 租赁与品质限制

新增三卧记录是公开MLS关闭字段，不是签署租约、净有效租金或入住时间。家具、租期、整租范围、共墙和月租单位逐项核对；押金不当租金，同地址旧房间广告不并入整租。新增社区归属仅按经纪描述，本轮没有重做4个地址的市政GIS核对。三卧约2047平方英尺带Conservatory的同品质关闭样本仍缺。

地块面积、共墙、法律产权和居住面积分别保留；未核实的升级、硬伤、让利、税费、MR、融资及产权不填零。多站共享CRMLS不等于独立文书核验。本轮同一研究线程串行检查，没有第二模型、第三方现场或签署文书审阅。

## 实际文件与验证

- `scripts/build_transaction_history.py`：从冻结个人研究笔记整理来源事件、分组、日历跨度、挂牌价差和三卧租赁；不抓取房源网站。
- `scripts/report_transaction_history.py`：生成公开方法报告；可选生成个人阅读版表格计划。
- `data/transaction_history_source_index.csv`：{m['source_record_url_pairs']}条记录×来源URL，公开链接及访问处理，不重发受限数值字段。
- `data/transaction_history_input_manifest.json`：3份输入的完整SHA-256；是研究笔记／索引指纹，不冒充房源HTML原字节。
- `qa/transaction_history_qa.json`：{q['checks_passed']}项结构、日期、单位、窗口、筛选和算术检查通过。用Fraction与Decimal交叉复算价差，关键跨MLS日期有固定参考值。
- `qa/transaction_history_negative_check.json`：同长度改动一个金额后，SHA-256核验在输出前拒绝继续。

公共仓库没有个人文档链接、买卖双方身份、照片、完整MLS导出或逐房价格。指定档案保留输入、131条事件观察、25笔售房摘要、4笔新增租赁、3笔排除说明及复算代码；公开可运行代码需要这些已授权研究输入。

```bash
python scripts/build_transaction_history.py --pilot-notes /path/to/pilot_working.json --history-notes /path/to/history_notes.json --source-map /path/to/used_source_references.json --manifest data/transaction_history_input_manifest.json --outdir /path/to/reviewed --public-qa qa/transaction_history_qa.json --source-index data/transaction_history_source_index.csv
python scripts/report_transaction_history.py
# 可选个人阅读版，不写入公开仓库：
python scripts/report_transaction_history.py --private-reviewed /path/to/reviewed/reviewed_history.json --doc-plan /path/to/history_doc_plan.json
```

## 下一项

进入实际购买力与城市分流：先核对HMDA可下载年份、地理与用途范围，再结合工资／就业和现有城市家庭结构，区分贷款购房者、非贷款覆盖和目标产品。HMDA不能单独估计现金买家或精确社区买家，也不接入家庭A。学校全市筛查、供给项目、持有成本与定价模块继续保留；公开历史缺项形成集中补件表，不反复采样到出现预设结论。
"""


def reading_plan(pack, qa):
    n = pack["notes"]
    sales = pack["sale_summaries"]
    byid = {r["record_id"]: r for r in sales}
    items = []

    def p(text, heading=False, page=False):
        items.append({"type": "heading" if heading else "paragraph", "text": text, "page_break_before": page})

    def table(cells, widths, links=None):
        items.append({"type": "table", "cells": cells, "widths": widths, "links": links or []})

    def url_for(rid):
        return next(x["source_url"] for x in pack["sources"] if x["record_id"] == rid)

    def case_note(*rids):
        return " ".join(rid+"（"+byid[rid]['address']+"）："+n['cases'][rid]['notes'] for rid in rids)

    items.append({"type": "title", "text": "产品分组、挂牌时间线与三卧租赁"})
    p("阶段六｜观察截止2026-10-11，America/Los_Angeles｜独立公共市场B")
    p("本轮完成25笔售房的公开可见事件扩展，新增4笔三卧关闭租赁。重要修正是：同地址重新挂牌会改变看到的营销跨度；一笔卧室数冲突使稳定四卧候选由22条降到21条。本轮没有形成同品质价格指数、真实DOM或买入／等待结论。")
    p("一、本轮实际完成", True)
    table([["项目", "结果", "验收边界"],
           ["售房与来源事件", "25笔／131行", "131行为来源观察，含冲突分支；130行在窗口内，1行为前置背景"],
           ["产品分层", "17个候选小组", "未核同户型、地段硬伤、景观和升级；不能直接平均价格"],
           ["较稳定字段候选", "21条；其中20条无重大价冲突", "3卧、1面共墙、2笔重要卧室／面积冲突分开"],
           ["新增关闭租赁", "三卧4笔", "发布整租、无家具、12个月、无共墙；签署租约和净租金均未核"],
           ["完整MLS／实际DOM", "均0/25", "仅可见事件，不将撤牌日或自然日跨度当签约日"],
           ["脚本验证", f"{qa['checks_passed']}项通过", "指纹、日期、单位、筛选、算术；不替代来源／现场认证"]], [115,90,245])
    p("检索窗口2024-10-12至2026-10-11，但售房关闭只覆盖2025-02-05至2026-10-01。固定非随机样本缺少2024年末关闭记录，没有市场成交量／库存分母；不能据此报告两年涨跌幅或市场热度。")
    p("来源处理：同源CRMLS在多个网站出现不算独立证据。MLS关闭、网站转述Public Record、租赁关闭及撤牌分别记账；没有取得契据、签署租约或新的产权认证。本轮串行完成，未进行第二模型独立审阅。")

    p("二、候选产品小组", True, True)
    p("按社区、卧室、面积、建年与共墙预分层。下面的尺数为sqft、年份为建年；小组内仍须核实楼层／户型、硬伤、景观与升级。不能用小组名宣称已控制品质差异。")
    cells = [["社区／产品", "记录", "较稳定候选", "额外处理"]]
    for g in n["product_groups"]:
        rs = [byid[rid] for rid in g["members"]]
        exceptions = []
        for r in rs:
            if r["record_id"] == "T003": exceptions.append("T003价格冲突")
            if r["record_id"] in {"T009","T021"}: exceptions.append(r["record_id"]+"卧室冲突")
            if r["record_id"] == "T013": exceptions.append("三卧对照")
            if r["record_id"] == "T015": exceptions.append("共墙对照")
        if any(r["year_built"] >= 2024 for r in rs): exceptions.append("新建年代单列")
        cells.append([g["label"], "、".join(g["members"]), str(sum(r["stable_profile_candidate"] for r in rs)), "；".join(exceptions) or "品质待核"])
    table(cells,[185,95,55,115])
    p("前轮22条候选的修正："+case_note('T021')+" T009原有卧室／面积冲突继续排除。T003物理字段仍候选，但成交价重大冲突，所有挂牌价差留空。")

    groups = [("三、Stonegate：8笔时间线", sales[:8]), ("四、Reserve：8笔时间线", sales[8:16]), ("五、其他社区与跨市：9笔时间线", sales[16:])]
    for title, rows in groups:
        p(title, True, True)
        p("金额单位：万美元；首挂＝本次检索最早可见售房挂牌，末价＝关闭前最后可见挂牌价。跨度栏为“最早可见首挂／本次MLS首挂→MLS关闭”的自然日数，含撤牌间隔及托管，均不是DOM。地址链接打开本轮来源，完整事件及冲突链接见档案。")
        cells = [["编号／地址", "最早可见首挂\nMLS关闭日", "首价→末价\n关闭价", "跨度（天）\n最早／本MLS", "价差%\n首价／末价", "处理"]]
        links=[]
        for r in rows:
            rid=r["record_id"]
            treatment = []
            if not r["stable_profile_candidate"]: treatment.append("移出四卧稳组")
            if rid == "T003": treatment.append("价格冲突")
            if r["named_sale_mls_count"]>1: treatment.append(str(r["named_sale_mls_count"])+"个MLS")
            if "dom_conflict" in r["flags"]: treatment.append("DOM有分歧")
            if "multi_period_gap" in r["flags"]: treatment.append("撤牌间隔")
            if "left_boundary_context" in r["flags"]: treatment.append("首挂在窗外")
            if "new_build_special" in r["flags"]: treatment.append("新建／地块特殊")
            if "close_date_public_record_conflict" in r["flags"]: treatment.append("日期口径分开")
            if "stale_status" in r["flags"]: treatment.append("旧状态缓存")
            delta = "留空／留空" if r['closed_vs_first_observed_ask_pct'] is None else f"{r['closed_vs_first_observed_ask_pct']:+.2f}／{r['closed_vs_last_observed_ask_pct']:+.2f}"
            close = f"{r['close_price_mls_baseline']/10000:.2f}" + ("*" if rid=="T003" else "")
            cells.append([rid+"\n"+r['address'],r['observed_first_listing_date']+"\n"+r['close_date_mls'],f"{r['observed_first_ask']/10000:.2f}→{r['observed_last_ask']/10000:.2f}\n"+close,f"{r['first_listing_to_close_calendar_days']}／{r['current_mls_listing_to_close_calendar_days']}",delta,"；".join(treatment) or "部分历史"])
            links.append({"row":len(cells)-1,"col":0,"url":url_for(rid)})
        table(cells,[85,74,86,62,68,75],links)
        if rows[0]['record_id']=="T001":
            r=byid['T001']
            p(case_note('T007')+f" {r['address']}相对最初可见报价为{r['closed_vs_first_observed_ask_pct']:+.2f}%，相对最后可见报价为{r['closed_vs_last_observed_ask_pct']:+.2f}%，都不是社区房价跌幅。")
            p("*"+case_note('T003','T002')+" 未取得契据／结算文件，不裁决为确定成交价。")
        elif rows[0]['record_id']=="T009":
            r=byid['T009'];claims=[f"{e[0]}为{e[2]/10000:.2f}万" for b in n['cases']['T009']['blocks'] for e in b['events'] if e[1]=='reported_public_sale']
            special=byid['T014']
            p(f"{r['address']}的网站转述："+"、".join(claims)+f"；MLS关闭为{r['close_date_mls']}。卧室、面积、新建及景观条件均不能视为恒定，不计算重复成交涨幅。{special['address']}相对观察报价的{special['closed_vs_first_observed_ask_pct']:+.2f}%只是本房挂牌差异，不能认作市场跌幅。")
            p("T013为三卧、T015为1面共墙对照；保留时间线但不进入目标四卧无共墙小组。T006及T013的部分历史网页仍旧Active，关闭字段沿用前轮已核MLS来源；旧网页不覆盖更新状态。")
        else:
            r=byid['T021'];other=byid['T020']
            dates=[e[0] for b in n['cases']['T021']['blocks'] for e in b['events'] if e[1]=='sale_listed']
            p(f"{r['address']}可见{r['named_sale_mls_count']}个MLS："+"、".join(dates)+f"依次首挂，{r['close_date_mls']}关闭；观察跨度{r['first_listing_to_close_calendar_days']}天，最后一个MLS为{r['current_mls_listing_to_close_calendar_days']}天。{other['address']}两个MLS对应{other['first_listing_to_close_calendar_days']}天与{other['current_mls_listing_to_close_calendar_days']}天。不能把重新挂牌后的短周期当需求突然增强。")
            p(case_note('T022','T024','T019'))

    p("六、新增三卧关闭租赁", True, True)
    p("以下4笔均为发布的整租、无家具、12个月、无共墙、Condominium；月租包括协会费按挂牌字段。没有签署租约、净优惠、实际入住或新市政空间核对，社区按经纪描述。下架不是租赁关闭，押金不计租金。")
    cells=[["编号／地址", "社区／面积／建年", "MLS关闭日", "关闭月租\n美元/月", "首挂→关闭\n自然日"]];links=[]
    for r in pack['leases']:
        cells.append([r['record_id']+"\n"+r['address'],r['community']+f"\n{r['living_area_sqft']}尺／{r['year_built']}",r['close_date_mls'],f"${r['closed_rent_usd_month']:,}",str(r['calendar_days_first_listing_to_reported_close'])])
        # Select the explicit closing source, not an asking-price source.
        source_ref = next(b['ref'] for x in n['new_leases'] if x['record_id']==r['record_id'] for b in x['blocks'] if any(e[1]=='lease_closed' for e in b['events']))
        links.append({'row':len(cells)-1,'col':0,'source_ref':source_ref})
    table(cells,[90,110,82,82,86],links)
    rentals={r['record_id']:r for r in pack['leases']};a,b=rentals['L004'],rentals['L005'];c,d=rentals['L007'],rentals['L006']
    p(f"{a['address']}与{b['address']}同为{a['living_area_sqft']}尺，但建年、时点与装修仍不同；{c['address']}为{c['living_area_sqft']}尺，{d['address']}为Reserve的{d['living_area_sqft']}尺，不能四笔取平均后称同品质市场租金。{b['address']}的{b['last_observed_ask']}是广告／撤牌价，MLS关闭为{b['closed_rent_usd_month']}。{c['address']}：{c['notes']}")
    cells=[["排除候选", "发现的冲突", "处理"]];links=[]
    for x in n['excluded_lease_candidates']:
        cells.append([x['record_id']+"\n"+x['address'],x['reason'],"不入三卧基线"])
        links.append({'row':len(cells)-1,'col':0,'url':url_for(x['record_id'])})
    table(cells,[88,292,70],links)
    p("三卧约2047尺带Conservatory的同品质关闭样本仍未取得。前轮四卧租赁3笔与本轮三卧4笔各自保存；三卧租住与四卧购买之间的服务升级，留待持有成本模块分开估值。")

    p("七、验收、集中补件与下一项", True, True)
    p(f"{qa['checks_passed']}项检查通过：25笔固定队列覆盖、17组互斥归类、131条事件观察、单位／窗口、候选排除、日历跨度和价差。Decimal与Fraction交叉复算；修改同长度金额后指纹核验在输出前失败。源字段冲突没有因脚本通过而消失。")
    table([["缺项", "影响", "下一次有相应授权资料时核对"],
           ["完整MLS状态史／签约日", "不能估计真实DOM、去化率及跨MLS连续营销", "按地块串联全部MLS，取得状态变更及合同日期"],
           ["T003价格／T009、T021卧室", "改变价格比较或目标组资格", "契据／结算信息；平面图、许可与实际使用"],
           ["产权／地段／升级", "17组不是同品质匹配", "产权、共墙、噪音／道路、景观、户型及升级证据"],
           ["净租金与特定三卧产品", "4笔不是可直接代入的市场租金", "签署租约、租期、家具、优惠；2047尺产品关闭样本"],
           ["全市场样本与分母", "不能求24个月涨幅、库存和成交量", "同口径全量交易／在售／撤牌及新品交付范围"]], [113,165,172])
    p("公共仓库保存45条证据链接、原创方法、3份输入指纹及QA；逐项房源笔记、事件表和4笔租赁留指定研究档案，没有再分发照片或完整MLS库。指纹对应本次研究记录，不是假称下载了房源HTML原文。")
    p("下一项：实际购买力与城市分流。先核对HMDA年份、购买用途、自住和地理覆盖，再结合工资／就业及已有家庭结构解释承接能力；贷款样本不能代表现金买家或精确社区所有买家。全市学校、供给、持有成本与定价仍待推进，家庭A暂不接入。")
    return {"title":"成交与租赁：产品分组与挂牌时间线","items":items}


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--qa',type=Path,default=ROOT/'qa/transaction_history_qa.json')
    p.add_argument('--private-reviewed',type=Path)
    p.add_argument('--doc-plan',type=Path)
    a=p.parse_args();q=json.loads(a.qa.read_text())
    out=ROOT/'reports/2026-10-11_transaction_history_phase6.md'
    out.write_text(public_report(q),encoding='utf-8')
    if a.doc_plan:
        if not a.private_reviewed: p.error('--doc-plan needs --private-reviewed')
        pack=json.loads(a.private_reviewed.read_text())
        plan=reading_plan(pack,q)
        source_map=json.loads((a.private_reviewed.parent.parent/'used_source_references.json').read_text())
        for item in plan['items']:
            for link in item.get('links',[]):
                if 'source_ref' in link: link['url']=source_map[link.pop('source_ref')]['url']
        a.doc_plan.parent.mkdir(parents=True,exist_ok=True)
        a.doc_plan.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(out.name)
