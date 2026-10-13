# 步骤12：冻结审阅包

版本B12-20261012-v1；洛杉矶时间2026-10-12。研究输入冻结于main `c2ad6899d8a3aa5a41fd36afa54e3b9a7f76e716`。本次产物的内容SHA-256见 `qa/step12_artifact_manifest.json`；发布commit和PR见随后提交的 `qa/step12_delivery_receipt.json`。采用“内容先冻结、回执后引用”以避免文件自含自身commit的循环。

审阅对象是本轮三件套：`reports/2026-10-12_step12_independent_synthesis.md`、`data/step12_a_parameter_interface.json`（阅读版 `reports/2026-10-12_step12_a_parameters.md`）、本审阅包。初步判断单独保留。不是phase12定价，也不是旧步骤13前置验收。

正式V2新增tab标题必须是“独立公共B：综合结论”。完整文档ID、tabId、写入前后版本、既有正文指纹及私人证据包入口仅在私人交接回执中；公共仓库不放私人链接。正式tab与执行tab最终交接列内容commit及main合并commit，可唯一定位版本。

## 1　步骤、阶段文件与输入commit映射

| 执行步骤 | 对应阶段／材料 | 本轮冻结基线中的来源提交 |
| --- | --- | --- |
| 0—1、3 | 范围、边界、字典；阶段四空间代理；数据表随模块递增 | 8cf22d1、52bba4f及后续模块；统一以c2ad689取文件 |
| 2 | phase5试采集／phase6挂牌时间线 | 04537dc、cb57478 |
| 4 | phase1人口／phase2家庭预测／phase3 ACS | 4dd375c、8111ef3、f8fd439 |
| 5 | phase7购买力／phase8跨市及审阅补修 | 593d6fd、ebe9bdc、5079cf2 |
| 6 | phase9学校 | 0e00466；发布merge 9ce18b5 |
| 7 | phase10供给 | 7b199bc；merge 3a56507 |
| 8 | phase11租赁成本 | daea0b3；merge 509f680 |
| 9 | phase12定价 | 134fe86、9bfd0c7；merge 0dade02 |
| 10 | phase13利率传导 | 3b0c671；merge b2a5ada |
| 11 | phase14联合情景 | 4fe3a70；merge ff33e18 |
| 13旧前置验收 | step13_independent_review；只审缺件和四类融资算术 | 4ecdb0f；merge c2ad689 |
| 12本轮 | step12三件套、参数和QA | 内容commit见本轮发布回执；之后另启完整步骤13 |

短SHA只是阅读索引；机器可读索引和固定输入commit均为完整SHA。仓库的历史状态文案描述当时完成边界，不是本轮状态。原S13-001现在为“补件已提交，待独立验收”，不由作者修改旧审阅结论或自签关闭；S13-002通过此映射继续处理。

## 2　高影响证据定位与可复算范围

每组的原URL、字节指纹、版本和读取等级见 `data/step12_evidence_index.json`；其引用的旧manifest均从固定输入commit读取。以下不含任何微观贷款记录、逐屋价格表或完整供应商历史。

| ID／判断 | 原件或标准表精确位置 | 本轮实际核验及边界 |
| --- | --- | --- |
| E01／D1需求 | county_components_2020_2025：县06059、2025、DOF/Census分别；ACS window_changes：Irvine、total/owner/renter及MOE | 标准表／方法／版本；9,997÷13,810=72.3896%；未重读全部人口原件 |
| E02／D2购买力 | 原HMDA2025 CSV；crosswalk Irvine/core_99999；严格字段和单位见索引 | 6层以上筛选重新计数；1,002／915／326,000；200万—不足300万159／139／463,000；CLTV156／69.816%；没有现金或目标四卧识别 |
| E03／D3替代 | crosscity_evidence_coverage、match_sensitivity及buyer_evidence_gates；V2“需求：跨市成本与买家选择” | 51候选、4代理配对、2外市房；完整匹配0、真实分流0；非抽样总体估计 |
| E04／D3学校 | school_directory、boundary_register、parent_search_coverage；V2“学校：官方基线与入学限制” | 51+36+144目录及2深读；地址／年级确认0；没有逐所重读原件 |
| E05／D4供给 | APR2025 Summary C29/D29/E29；A2从13行起，F类型、T批准、AG许可、AT完工 | 从XLSM XML独立加总至4,835／1,411／1,052；SFD360／600；不是同一队列 |
| E06／D4时点 | Gateway June2026 FAQ的计划数量、户型及construction timeline问答 | 2027-06 vertical、秋季样板房／首销；不是交付；851／854分配差保留 |
| E07／D5价格 | 社区四卧CSV：CA/Irvine；RegionID775702、403127、403197、403196；2026-08-31等列 | 重算同比、两年和2024—25峰值；非严格目标／Reserve序列 |
| E08／D5数量 | Realtor县级CSV：06059、202609/202509/201909；active/new/pending/DOM及构成 | 重算7项；保留DOM与面积源同比差异；pending是存量 |
| E09／D6融资 | SF HTML Jumbo；CU HTML Jumbo ARM；当前PMMS和DGS10官方页 | 6份原字节指纹含两家菜单；CU新页下一日标示单列；LE0 |
| E10／D6前瞻 | Fannie2026-09与MBA2026-10-11 PDF第一页Mortgage Rates列；预测日期早于目标季度 | 本轮复读原PDF文字；期末／均值分开；没有重做所有旧预测误差或赋概率 |
| E11／D6恒等式 | scenario_equal_payment_boundaries的6.5%行；scenario设计；旧step13融资QA | 本轮360期付款现值求和得105.5634／109.2723；旧点数、ARM、再融资抽核复用，未冒充新增全量审核 |
| E12／租买 | rental_coverage；V2租赁tab及冻结字段笔记 | 18观察、12关闭／6挂牌，8配对、2同址；净有效租金0，完整成本0/8；非净收益样本 |

来源时钟：ACS2020—2024不当2026年度流量；HMDA2025不当2026当前成交；价格模型止2026-08，县级挂牌止09，全国按揭周值与国债日值止10-08，现行页面检索日另列。检索服务内容保存为“工具读取记录”，不假称网站原始HTML；当前网页不能反向认证先前冻结版本。

官方入口包括[CFPB HMDA](https://ffiec.cfpb.gov/data-browser/)、[Irvine APR原表](https://cityofirvine.gov/sites/default/files/legacy-documents/civica-34702-2025-housing-element-annual-progress-report.xlsm)、[Gateway FAQ](https://cityofirvine.gov/sites/default/files/legacy-documents/gateway-village-residential-project_faq_june-2026.pdf)、[Zillow Research](https://www.zillow.com/research/data/)、[Realtor Economic Research](https://www.realtor.com/research/data/)、[Freddie PMMS](https://www.freddiemac.com/pmms)、[FRED DGS10](https://fred.stlouisfed.org/series/DGS10)。具体数据URL及SHA应以冻结索引为准，不用更新后的网页悄悄替换。

## 3　V2覆盖与缺口：按会不会改变行动排序

优先级A＝可能改变行动或关键参数；B＝主要改变精度／置信度；C＝背景补充。未完成的V2要求继续保留；优先级不等于免验收。

| 领域／验收 | 已有覆盖 | 缺口、影响与最小补件 | 优先级 |
| --- | --- | --- | --- |
| 目标交易／库存 | 25非随机售房试样本；20稳定候选；19模型序列；县123个月 | 严格品质重复成交0对、全量库存分母0；获合法目标成交／签约／撤牌清单并核净价，决定降温是否扩散 | A |
| 租赁／持有全成本 | 18观察，租期与无家具字段各15；8配对2同址 | 签署租约、净有效租金均0；完整逐屋费用0/8。选有代表性同服务候选核租金／税MR／HOA／保险／维修，可能反转买租排序 | A |
| 融资资格与期限 | 2家公开菜单；固定／ARM／点数／再融资算术 | 个人LE0、持有期与首付未确认；实际条款与无法再融资路径，后续私有阶段取得 | A |
| 股票含息／税后口径 | 联动风险机制与价格序列背景 | 总回报历史和可采用预期均缺，账户／税务未知；先定基准与再投资、费用、税制，不能填旧收益率 | A |
| 入学与住房服务 | 231目录、2310指标槽位；社区候选链 | 逐址逐年级余位0；资格与通勤／服务若不符直接改变候选，后续官方核定 | A |
| 目标供给时点／净吸收 | 76登记行，Irvine地图68可见/46住宅，在审163/39关联；LF53/3住宅新项目 | 非全市排漏；四卧无共墙存量、剩余、交付和吸收未知。优先核近期可能交付的直接竞品，不能推库存月数 | A |
| 真实购买力／跨市分流 | HMDA3年；4城及边界敏感性；4代理配对 | 现金及来源未识别、完整品质配对0、真实买家0/3；如要量化溢价／净外流则升级为必补，当前只保留机制 | A（量化主张时）；否则B |
| 人口／家庭／预测 | 双县级版本、城市ACS及社区代理 | Reserve精确画像未识别，2025ACS一年表发布时间待定；新增可比官方版本时更新，不以更多背景替目标数据 | B |
| 学校全面深读 | 51本市地址统一基线；51检索、2深读 | 49家长材料未全文、项目覆盖不全；逐校补全文可提升比较，不能把检索标成深读 | B；具体孩子需求适配可升A |
| 独立经纪人长期覆盖 | 13作者／品牌、6机构家族，1条有日期长期线索 | 8—12位独立且长期记录要求未达；共享MLS不算独立。无联系授权时只补合法公开史料 | B |
| 更多预测机构／更长历史 | Fannie／MBA／Fed与多周期机制 | 不增加概率识别；只在实质新冲突时补，避免为数量无限搜索 | C |

不应为了把A表填满而强行补到一个伪精确数字。A类未知可以以明确条件和无法量化的方向保留，但不得产出依赖它们的无条件家庭行动建议。

## 4　初步判断与阶段结论对照

| 初步主张 | 对照后的结果 | 本轮增量／需挑战之处 |
| --- | --- | --- |
| 居住需求有基础，非普遍净流入 | 与人口、ACS、HMDA阶段一致 | 复算2025原CSV，保留获贷选择和67%土地覆盖限制 |
| 净溢价和真正分流未识别 | 与阶段八补修、学校和租赁一致 | 相同中高中不能重复解释社区间溢价；三卧升级与同服务比较分开 |
| 不支持半年目标供给洪峰 | 与APR和Gateway原件一致 | 首销不等于交付；母子分配分歧不自填；短期净吸收仍缺 |
| 选择性降温而非普遍崩跌 | 与定价阶段总体一致 | 新增DOM同比字段差异，短DOM／低库存保留为反证 |
| 有期限等待且条件买入 | 前序阶段只到机制，本轮新增综合排序 | 最容易受真实房源／全成本反驳；不是先前步骤13已审结论 |
| 不把菜单变个人利率 | 与利率和情景阶段一致 | 当前CU网页次日生效单列；不混conforming与jumbo APR |

本轮脚本首跑把非正HMDA收入误排除，源内定义检查发现有效数906不应替915；代码已改为保留所有有限报告数，最终复算一致。此为本轮检查代码错误及修复记录，不是前序数据错误。没有把程序修正掩盖成额外独立证据。

## 5　自我反证与步骤13应独立回答的问题

1. **等待是否只是“未知很多所以拖延”？** 请检验本报告是否清楚承认信息价值与未证实的择时收益。若已存在品质、净价和成本占优的房源，默认等待应让位于条件买入。
2. **是否低估稀缺性与现金／资产买家？** 检验低于2019的县级库存、Irvine获贷量相对强和重点社区两年模型仍正，是否足以提高稳定降息时反弹风险；不能把未观测现金当零。
3. **是否高估供给冲击？** 逐项核Gateway首销／交付、SFD／detached condo／四卧，以及母子重叠；任何新的2027目标交付证据都可能改等待期限。
4. **是否仍把代理价格升级成目标结论？** 检验Reserve、房龄、共墙、品质、县／社区界线；主张“降温”的范围是否过宽。DOM源字段差异是否只影响精度而非方向？
5. **参数是否可被误导入？** 30项是否全部有口径，null、菜单和敏感性是否阻止成为默认值；股票是否真的含股息，税后与实际是否分开；未知保险有没有被计算成0？
6. **联合情景是否双重计分？** 检验家庭增长与住房容量、工资与股票／RSU、低息买家与解锁卖家、本金现金流与成本、MR含税与另列是否重复。
7. **停止规则是否可执行而非强迫买？** 检验2027-04-12／10-12的管理日期、一次延期的具体项目依据与成本预算；没有合格房源时应能明确转长期租住。
8. **三条选择是否公平？** 现在买有长期服务价值、等待有选择权、长期租住有流动性但有投资及续租风险；是否有未有依据的年化回报或偏好替用户决定？

步骤13需在新线程先读范围／来源／计算和必要原件，保存自身初步意见，再读B结论。复用输入未变的融资算术；集中复核全部最终行动和关键参数，不全量重跑只为增加QA数量。结论应区分“可用但有限”“需重大修改”“证据不足”，重大问题处理并复核后才允许进入A/C。

## 6　复算与验证命令

本轮脚本仅用Python标准库，不导入前阶段生产代码。解压已授权证据形成以下私有目录（不是公开下载脚本，不自动访问MLS）：

```text
<evidence-root>/purchasing/raw/hmda_2025_purchase_oc.csv
<evidence-root>/supply/raw/irvine_apr2025.xlsm
<evidence-root>/pricing2/raw/Neighborhood_zhvi_bdrmcnt_4_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv
<evidence-root>/pricing3/raw/realtor_county_history.csv
<evidence-root>/scenario/raw/schoolsfirst_purchase.html
<evidence-root>/scenario/raw/cusocal_rates.html
```

```bash
python scripts/audit_step12_synthesis.py --evidence-root /path/to/evidence-root --out /tmp/step12_checks.json
git diff --no-index qa/step12_checks.json /tmp/step12_checks.json
```

最终96项检查覆盖6份原件指纹、选择性原始计数／算术、30项接口字段和未知保护；不是96项市场结论通过。关键局限仍是产品识别、非随机样本、原始原件读取范围及个人条件未知。另在发布前检查公开差异不含私人入口／微观原件，并核对原生Docs表格、正文读回与一页决策卡版式。实际交付结果在回执记录，尚未完成的不能预先记pass。
