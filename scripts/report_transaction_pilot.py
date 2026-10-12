"""Render the original public QA report; optionally prepare a personal Docs plan.

Individual property fields are deliberately absent from the public report.
The optional --doc-plan reads archived personal notes and emits private content.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def public_report(q):
    return f'''# 成交／租赁试采集与逐项核对｜阶段五

研究日期：2026-10-11，America/Los_Angeles。独立公共市场B；本轮完成公开字段可行性试采集，不接私人家庭A。来源许可未授权公开重发的房源明细留个人研究阅读版与指定档案；此处保存原创方法、验收状态和来源链接。

## 一、本轮完成与含义

形成{q['closed_sales_mls_reported']}笔MLS发布的已关闭售房记录及{q['closed_leases_mls_reported']}笔已关闭租赁记录；售房分布Stonegate 8、Reserve 8、Eastwood 4、Portola Springs 2，以及Lake Forest、Tustin、Aliso Viejo各1笔。完成{q['sale_source_reviews']}笔售房、{q['lease_source_reviews']}笔租赁重点逐项来源复核，满足至少5笔售房来源检查的目标。

检索窗口为2024-10-12至2026-10-11；实际售房观察日期{q['observed_sale_date_range'][0]}至{q['observed_sale_date_range'][1]}，租赁观察只有2025年末。样本由可检索且字段较完整的公开条目取得，并非全量或随机样本，不能据此计算两年涨跌幅、社区均价、真实DOM或市场热度。

25笔售房中，23笔按选择的MLS字段满足四卧、至少1650平方英尺、2010年及以后及无共墙筛选；其中1笔存在重要卧室／面积跨来源冲突，暂留22笔较稳定的字段候选。它们仍有面积、产品、地段和升级差异，未构成22笔同品质可比成交，也没有任何一笔已完成产权与现场尽调。

## 二、必须保留的区别

T015的共墙字段明确为1面，保留为排除对照；T013为三卧，不能混入四卧组。L001的页面标题使用Sold，但实为租赁关闭事件，不能把月租当房屋售价。Condominium和有共墙是两个不同维度；MLS房型也不能代替契据产权。

T001的页面DOM、T003的售房价格、T004的日期与社区标签、T009的卧室／面积、T019的跨日期同价事件、T022的旧Active缓存均保留问题记录。成交日、文书记录日、抓取日期及状态更新日期分列；同地址同价格不同来源日期不会自动增加一笔独立成交。

T016显示的每平方英尺价格与本次成交价／面积运算不一致，因此统一从原字段复算。T025存在月度与季度两项HOA，按频率换算后保留分项，不能只取展示页的第一项。没有把整个condo项目的地块面积当私人后院面积，也没有将二手网站转述Public Record视作本轮已经取得县原文。

## 三、字段取得率及核对层级

| 售房字段 | 本轮取得 | 解释 |
|---|---:|---|
| MLS关闭日期、价格、卧室、面积、建年 | 各25/25 | 已发布字段；存在来源冲突，不是契据／现场认证 |
| MLS房型及共墙字段 | 各25/25 | 共墙与法律产权分开；1笔共墙对照保留 |
| HOA月度等价及分项 | {q['sale_field_coverage']['hoa_monthly_equivalent']['observed']}/25 | 以相应挂牌时点费用为准，未核账单或特殊征费 |
| 买方专属MLS融资标签 | {q['sale_field_coverage']['buyer_specific_mls_financing']['observed']}/25 | Conventional或CashToNewLoan；未取得金额、LTV或贷款文书 |
| 已核产权、契据或贷款原文 | 0/25 | MLS类型不能填成已核法律产权 |
| 实际合同日期、完整挂牌史、实际让利、核实MR账单 | 各0/25 | 缺失，不填零；Partial历史不写成完整历史 |

卖方接受Cash／Conventional是可接受条款，不是买方实际融资。CashToNewLoan涉及新增贷款，不能归为全现金；没有融资字段也不能归为全现金。三笔租赁没有取得签署租约、有效净租金或优惠；尚无已核三卧关闭租赁基线。

## 四、社区归属与验收

23个唯一尔湾地址、24条交易记录匹配市政府建筑地址表与建筑面，并落入对应冻结HOA研究覆盖面；Stonegate 9.4、Reserve 1.3，补充Eastwood 5.2和Portola Springs 6.1。另4条跨市记录只有经纪社区描述，未完成市政空间对照。

地址表X/Y按EPSG2230（美制测量英尺）转换WGS84；距离按EPSG26911米制计算。官方建筑点与建筑面逐项一致，HOA范围继续只作覆盖诊断，不能认证完整村界、产权或学区。补充43个市政HOA要素，6份官方查询响应冻结完整SHA-256，原字节保留。

{q['checks_passed']}项脚本检查通过、{q['checks_failed']}项失败，覆盖记录唯一性、日期窗口、租售单位、金额与面积、筛选重算、缺失处理、地址点／建筑面及研究边界对应。脚本检查不能消除保留的源字段冲突。经纪／平台页面多数共享CRMLS，同源一致不等于独立确认；本轮串行执行，没有第二模型或第三方人工现场审查。

## 五、实际文件与接续

- `scripts/audit_transaction_pilot.py`：读取逐项研究笔记、核对冻结市政来源和地址／覆盖面，输出明细与公共QA；不提供房源网站爬虫。
- `scripts/report_transaction_pilot.py`：生成本报告；可选个人Docs计划明确留私有路径。
- `data/transaction_source_index.csv`：逐笔证据链接；不含价格、面积、贷款或个人身份字段。
- `data/transaction_geography_source_manifest.json`、`qa/transaction_pilot_qa.json`：来源指纹、方法与实际验收。
- 个人阅读版与指定档案：28条逐项记录、53条记录×来源链接、11笔复核、官方原字节、问题清单及固定版本入口。没有取得或公开完整MLS导出、照片或签署契据／租约。

复算需指定档案中的个人笔记和冻结几何；公开仓库不冒充包含了受限房源数据。示例：

```bash
python scripts/audit_transaction_pilot.py --notes /path/to/pilot_working.json --official-dir /path/to/archive --base-hoa /path/to/hoa_targets.geojson --outdir /path/to/reviewed --public-qa qa/transaction_pilot_qa.json --source-index data/transaction_source_index.csv
python scripts/report_transaction_pilot.py
```

`--download-official`只恢复manifest明示的官方查询；同URL字节换版会拒绝继续，不静默覆盖。房源笔记需要逐页复核后明确登记新版本，不能由脚本虚构实时抓取。

下一项：按明确产品小组重建近24个月成交与挂牌时间线，并补三卧关闭租赁基线。先处理价格／事件冲突，再区分面积、共墙、地段硬伤及升级；完整公共B和买入／等待结论仍未完成。
'''


def reading_plan(pack, q):
    rows = pack["records"]
    lookup = {r["record_id"]: r for r in rows}
    roles = {key: lookup[rid] for key, rid in pack["roles"].items()}
    items = []
    def paragraph(text, heading=False, title=False):
        items.append({"type": "title" if title else "heading" if heading else "paragraph", "text": text})
    def table(cells, widths, links=None):
        items.append({"type": "table", "cells": cells, "widths": widths, "links": links or []})
    def profile(r):
        return f"{r['bedrooms']}卧 / {r['living_area_sqft']:,} sqft\n{r['year_built']}年"
    def form(r):
        subtype = "Condo" if r["mls_property_subtype"] == "Condominium" else "SFR" if r["mls_property_subtype"] == "Single Family Residence" else "分类冲突"
        wall = "1面共墙" if r["shared_wall_status"] == "one_common_wall_mls_reported" else "无共墙"
        return subtype + "\n" + wall + "（MLS）"
    def action(r):
        if "material_bedroom_and_area_conflict" in r["issues"]: return "暂缓：卧室／面积冲突"
        if "outside_no_shared_wall_target" in r["issues"]: return "排除无共墙组"
        if "three_bedroom_control" in r["issues"]: return "三卧对照"
        return "字段候选"
    paragraph("成交与租赁：试采集与逐项核对", title=True)
    paragraph("研究日期：2026-10-11（America/Los_Angeles）。本轮独立公共B，按公开来源重新检索；25笔MLS关闭售房、3笔MLS关闭租赁，完成8笔售房及3笔租赁重点来源复核。这里的关闭状态与价格是发布字段；尚未取得契据、产权报告、贷款登记或签署租约。")
    paragraph("一、本轮改变判断的结果", heading=True)
    paragraph(f"不能直接把网页Sold当售房、把Condo当共墙、把卖方接受现金当买方全现金，也不能把县文书日期当MLS成交日。{roles['attached_control']['address']}有1面共墙；{roles['three_bed_control']['address']}为三卧；{roles['lease_sale_label_control']['address']}为租赁事件。25笔售房中23笔按选择的MLS字段符合四卧／1650 sqft以上／2010年及以后／无共墙，另有1笔重要卧室与面积冲突，暂留22笔较稳定的字段候选；仍不是22笔同品质可比成交或已尽调房源。")
    paragraph("窗口为2024-10-12至2026-10-11；取得的售房日期2025-02-05至2026-10-01，租赁仅2025年末。按可检索与字段可得性取样，不是完整或随机样本；本轮不据此报社区均价、两年涨跌幅、真实DOM或市场温度。具体价格可读，但可比关系须另外建立。")
    paragraph("二、25笔售房逐项记录", heading=True)
    paragraph("表中日期为选择的MLS发布成交日；价格为售房价。房型和无共墙均按发布字段，法律产权全数未核。主链接与补充链接、冲突来源及字段备注均在逐项档案中，部分同URL存在旧缓存。")
    groups = [("Stonegate（8笔）", [r for r in rows if r["transaction_type"] == "sale" and r["community_claimed"] == "Stonegate"]), ("Reserve覆盖面（8笔，含共墙／三卧对照）", [r for r in rows if r["transaction_type"] == "sale" and r["community_claimed"] == "Reserve"]), ("Eastwood、Portola Springs及跨市对照（9笔）", [r for r in rows if r["transaction_type"] == "sale" and r["community_claimed"] not in {"Stonegate", "Reserve"}])]
    for title, group in groups:
        paragraph(title, heading=True)
        cells = [["编号／地址（来源）", "MLS日期", "售价", "卧室／面积／建年", "MLS形态／共墙", "核对处理"]]
        links = []
        for n, r in enumerate(group, 1):
            cells.append([r["record_id"] + "\n" + r["address"], r["close_date"], f"${r['amount']:,}", profile(r), form(r), action(r)])
            links.append({"row": n, "col": 0, "url": r["source_url"]})
        table(cells, [90, 64, 68, 76, 74, 78], links)
    paragraph("24条尔湾交易记录涉及23个唯一地址，已逐项匹配市政府建筑地址／建筑面及HOA覆盖。Stonegate为9.4、Reserve为1.3；本轮补Eastwood 5.2与Portola Springs 6.1。4条跨市记录的社区归属只经经纪描述，未完成市政GIS对照。HOA面不认证完整法律村界或产权。")
    paragraph("三、3笔关闭租赁，单独记账", heading=True)
    cells = [["编号／地址（来源）", "MLS关闭日", "发布月租", "卧室／面积／建年", "MLS形态／共墙", "限制"]]
    links = []
    for n, r in enumerate([r for r in rows if r["transaction_type"] == "lease"], 1):
        cells.append([r["record_id"] + "\n" + r["address"], r["close_date"], f"${r['amount']:,}/月", profile(r), form(r), "租约与净优惠未核"])
        links.append({"row": n, "col": 0, "url": r["source_url"]})
    table(cells, [90, 64, 68, 76, 74, 78], links)
    paired_sale, paired_lease = roles["paired_sale"], roles["paired_lease"]
    paragraph(f"{paired_sale['address']}的MLS售房观察为${paired_sale['amount']:,}，随后关闭租赁观察${paired_lease['amount']:,}/月；是同址两类事件，不能据此确认买方投资身份、实际净租金或净回报。撤下挂牌不等于租赁关闭。三笔均为四卧，尚无已核三卧关闭租赁基线；租赁关闭日也不等于实际入住日。")
    paragraph("四、11笔重点来源复核与保留问题", heading=True)
    manual = [r for r in rows if r["manual_review"]]
    for group in [manual[:6], manual[6:]]:
        cells = [["记录", "逐项核对与处理", "审核层级"]]
        links = []
        for n, r in enumerate(group, 1):
            cells.append([r["record_id"] + "\n" + r["address"], r["manual_review"]["notes"], "公开来源复核\n契据／现场未核"])
            links.append({"row": n, "col": 0, "url": r["source_url"]})
        table(cells, [93, 275, 82], links)
    ratio_case, fee_case = roles["ppsf_display_conflict"], roles["hoa_frequency_case"]
    displayed = next(o["fields"]["reported_sale_ppsf"] for o in ratio_case["source_observations"] if "reported_sale_ppsf" in o["fields"])
    fee_parts = "、".join(f"${f['amount']:,.2f}/" + {"monthly": "月", "quarterly": "季", "annual": "年"}[f["frequency"]] for f in fee_case["hoa_components"])
    paragraph(f"{ratio_case['record_id']}网页每平方英尺显示${displayed:,.2f}，但${ratio_case['amount']:,}÷{ratio_case['living_area_sqft']:,}＝${ratio_case['sale_price_per_sqft_calculated']}；保留显示差异，使用原字段复算。{fee_case['record_id']}费用为{fee_parts}，月度等价${fee_case['hoa_monthly_equivalent']}；费用时点为MLS挂牌信息，未核最新账单或特殊征费。买方专属Conventional与CashToNewLoan标签保留；CashToNewLoan不能归为全现金，其他缺失不得归全现金。")
    paragraph("五、字段覆盖与实际验收", heading=True)
    coverage = [["售房字段", "取得／25", "解释"]]
    labels = {"close_date": "MLS发布成交日", "amount": "MLS发布售价", "bedrooms": "MLS卧室数", "living_area_sqft": "MLS居住面积", "year_built": "MLS建成年代", "mls_property_subtype": "MLS房型", "shared_wall_status": "MLS共墙字段", "hoa_monthly_equivalent": "HOA分项／月度等价", "buyer_specific_mls_financing": "买方专属MLS融资标签", "legal_title_verified": "已核法律产权", "recorded_deed_or_loan_verified": "已核契据／贷款原文", "actual_contract_date": "实际签约日", "complete_listing_history": "完整挂牌史", "actual_seller_concession": "实际卖方让利", "verified_mello_roos_bill": "核实MR账单"}
    for key, v in q["sale_field_coverage"].items():
        coverage.append([labels[key], f"{v['observed']}/25", "发布字段，有冲突；非文件认证" if v["observed"] else "未取得；不填零"])
    table(coverage, [150, 60, 240])
    paragraph(f"{q['checks_passed']}项脚本检查通过，{q['checks_failed']}项失败，检查记录唯一性、窗口、租售单位、金额与面积、筛选、缺失与空间对应。8笔售房、3笔租赁的逐页／字段复核已记录；不是外部真人现场验收。经纪与平台多数共享CRMLS，同源一致不等于独立文书确认。本轮串行执行，未运行第二模型。")
    paragraph("市政建筑地址X/Y使用EPSG2230（美制测量英尺）转换WGS84，距离使用EPSG26911米制；地址点与建筑面逐项对应。冻结6份官方查询响应及原字节，并补43个HOA要素；源值与原始笔记保留完整指纹。各表中的面积仍是MLS发布面积，建筑底图检查不能认证内部居住面积。")
    paragraph("六、复算与下一项", heading=True)
    paragraph("公开仓库保存脚本、53条记录×来源链接、原始指纹、公共QA与原创报告；房源字段、28条笔记、11笔复核、原市政几何保留指定档案，不重发完整MLS数据库、照片或文书。复算读取已冻结来源；新字节必须明确登记版本。")
    paragraph("python scripts/audit_transaction_pilot.py --notes /path/to/pilot_working.json --official-dir /path/to/archive --base-hoa /path/to/hoa_targets.geojson --outdir /path/to/reviewed --public-qa qa/transaction_pilot_qa.json --source-index data/transaction_source_index.csv")
    paragraph("下一轮按产品小组重建近24个月成交与挂牌时间线，先解决来源价格／事件冲突，并补三卧关闭租赁。不会把本轮不同面积、共墙、地段和升级的22条候选直接当同品质价格序列。完整公共B、供给／融资／定价与买入／等待结论仍未完成。")
    return {"title": "成交与租赁：试采集与逐项核对", "items": items}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--qa", type=Path, default=ROOT / "qa/transaction_pilot_qa.json")
    p.add_argument("--private-notes", type=Path)
    p.add_argument("--doc-plan", type=Path)
    a = p.parse_args()
    q = json.loads(a.qa.read_text())
    path = ROOT / "reports/2026-10-11_transaction_pilot_phase5.md"
    path.write_text(public_report(q))
    if a.doc_plan:
        if not a.private_notes:
            p.error("--doc-plan needs --private-notes; property fields must stay outside the public repository")
        pack = json.loads(a.private_notes.read_text())
        a.doc_plan.write_text(json.dumps(reading_plan(pack, q), ensure_ascii=False, indent=2))
    print(path.name)
