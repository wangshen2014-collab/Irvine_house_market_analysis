# Irvine House Market Analysis

尔湾及周边住房市场独立研究。研究需求、供给、资产定价，覆盖 Orange County、Irvine 全市、北尔湾及 Lake Forest、Tustin、Aliso Viejo 等替代地区。

## 项目状态

2026-10-11启动。已完成县级历史人口／净迁移、城市家庭数量分解及官方长期预测的阶段研究；已补城市ACS结构、重点社区统计代理诊断、成交字段试采集，以及25笔售房的公开挂牌时间线和4笔三卧关闭租赁。已补2023—2025年HMDA按揭购买力与BLS工资就业；真实买家来源、城市分流及完整需求／供给／定价研究仍未完成，尚未形成买入／等待结论。

## 工作方式

- Codex 执行检索、清洗、计算、图表与报告；按模块串行推进。
- GitHub 保存可公开的代码、参数、标准数据、来源索引、报告底稿和交接记录。
- Google Drive 保存原始资料、大文件、受限底稿和供阅读批注的正式报告。
- 每轮更新 `STATUS.md`，明确完成、限制、真实产物和下一动作。
- 公共市场研究 B 先独立完成；家庭模型 A 和具体房源尽调 C 在后续单独衔接。

## 公开内容边界

公开可访问不自动等于允许再分发。按来源条款处理；未经确认的原始数据只登记链接和取得方法，不上传原文、照片、完整 MLS 导出或平台数据库。家庭收入、资产、账户、私人访谈和个人融资报价不进入本公开仓库。具体官方数据的使用范围在来源索引中逐项记录。

本仓库不发布家庭任务书全文或私人 Drive 链接。代码的存在不代表研究已完成；验收以证据覆盖、定义准确、反例和可复算性为准。

## 当前底稿与复算

2026-10-12新增[阶段十供给基线](reports/2026-10-12_supply_phase10.md)：76行项目／母子期／修订登记、7份标准表，区分全市年度活动、建筑形态、剩余量与目标库存；目前为受限完成。下一项为租赁全成本，详见STATUS。

```bash
# 从指定私人证据包解压取得 raw/，不将原始文件提交到仓库。
# 系统依赖：Poppler pdftotext；Python依赖沿用 requirements.txt。
python scripts/build_supply_baseline.py --input-dir /path/to/raw --private-out /path/to/private-workpapers
python scripts/audit_supply_baseline.py --input-dir /path/to/raw
python scripts/report_supply_baseline.py --private-out /path/to/private-workpapers
```

供给计算先核38份原件SHA-256；同URL换版会停止。另3项下载403如实登记。APR工作簿仅读取不修改；openpyxl对原件条件格式／验证的读取警告不表示原始文件被另存。市政点位图和逐套建商记录只输出到private-out。公开CSV的空值不是0，项目套数整列不能求和；替换研究注释前先核来源和版本。

- [启动及可行性报告](reports/2026-10-11_startup_feasibility.md)
- [最新状态与下一动作](STATUS.md)
- [范围卡](docs/research_scope.md)
- [来源索引](data/sources.csv)
- [DOF标准数据](data/clean/dof_population_housing_v2026.csv)
- [QA记录](qa/dof_qa.json)

```bash
pip install -r requirements.txt
python scripts/build_dof_baseline.py --download
```

已完成DOF人口住房35行、DOF／Census人口组成60行，以及家庭／官方预测五表175行提取与复算，并建立社区—PA对应11行。成交试采集已在阶段五取得25笔MLS关闭售房和3笔关闭租赁；源字段与文书验收分层。全市学校／项目、精确社区买家画像与完整需求／供给／定价仍未完成。旧模板用于输入检查，不代表原始房源已公开。

## 需求阶段一更新

[橙县人口净迁移与社区口径报告](reports/2026-10-11_population_migration_phase1.md)：60条官方组成记录已复算；新增社区—PA对应11行。未来预测已在后续阶段二补充，城市／社区买家需求仍待验证。

```bash
python scripts/build_demographic_components.py --download
python scripts/plot_migration.py
```

## 需求阶段二更新

[家庭增长与官方预测](reports/2026-10-11_households_forecast_phase2.md)：DOF 2026人口、2025家庭、SCAG 2024正式版与2026草案分别保留；四城312个TAZ合计通过。人口持平可伴随家庭数增加；规划增长含住房容量和政策假设，不能直接视为目标产品的新增买家。

```bash
python scripts/build_forecast_baseline.py --download
python scripts/plot_forecast.py
```

复算先生成E-5基础表。下载脚本固定SHA-256；若官方文件换版会停止并要求登记新Vintage。公开仅非商业署名统计摘取、原创分析与代码，原始SCAG地图和资料包留在私有底稿。

## 需求阶段三更新

[ACS家庭结构与购买力代理指标](reports/2026-10-11_acs_household_structure_phase3.md)：四城共同使用2020–2024五年窗口，一年表另列；2015–2019为不重叠历史对照。Irvine户数增加主要是租客存量变化，不能等同新增买家。高收入存量与购房意愿／首付／目标产品交集尚未识别。

```bash
python scripts/build_acs_household_structure.py --download
python scripts/refine_acs_moe.py --download
python scripts/build_acs_history.py --download
python scripts/report_acs_structure.py
```

首次批量下载约需数百MB，使用3个下载线程，不使用多智能体；后续使用缓存并核对完整指纹。2024／2019细项共4,506行；195个关键单元在另一份官方发布格式一致，25个比例使用80次SDR重复估计。VRE文件没有的指标仍明确使用近似MOE。脚本拒绝变更的源文件指纹，不把特殊值或未发布的城市／表填成零。公开指标与源表可复算，但统计QA不代表市场结论成立。

## 需求阶段四更新

[社区边界与ACS统计代理区](reports/2026-10-11_community_boundaries_phase4.md)：Stonegate与Stonegate East分别冻结HOA覆盖范围；Reserve共用BG5且混入Groves部分，不能取得精确社区收入。39条空间对应、1,452个ACS细项、276个指标记录；429组E/M跨格式一致，65项SDR指标。HOA范围不认证法律村界，面积占比不作人口权重。

```bash
python scripts/build_community_geography.py --download
python scripts/build_community_acs.py --download
python scripts/report_community.py
```

先完成阶段三ACS批量表下载。阶段四另需约130MB来源缓存；官方动态服务变化会使冻结指纹核对失败，应恢复已归档快照或明确登记新版本。公开地图只含Census几何；原市政几何及详细叠加图按来源权利状态保留指定资料档案。本阶段之后的成交／租赁试采集已在下方阶段五完成公开字段部分。

## 成交／租赁阶段五更新

[试采集与逐项核对](reports/2026-10-11_transaction_pilot_phase5.md)：25笔MLS关闭售房、3笔关闭租赁；8笔售房与3笔租赁重点来源复核。23个唯一尔湾地址、24条交易记录匹配官方建筑点／面与HOA覆盖；跨市4条仅经纪社区描述。394项检查通过，源字段冲突保留。四卧无共墙字段筛选23条，另1条重要卧室／面积冲突留待核，暂有22条较稳定的字段候选；不是同品质价格序列或已尽调房源。

公开保存代码、来源链接与原创QA；逐项房源字段、笔记、原市政响应和复核表保留指定个人研究档案。没有公开完整MLS导出或照片，也没有把未取得的产权、贷款、让利或完整挂牌史填零。复算需指定档案中的输入，入口见本轮报告。

```bash
python scripts/audit_transaction_pilot.py --notes /path/to/pilot_working.json --official-dir /path/to/archive --base-hoa /path/to/hoa_targets.geojson --outdir /path/to/reviewed --public-qa qa/transaction_pilot_qa.json --source-index data/transaction_source_index.csv
python scripts/report_transaction_pilot.py
```

上述下一项已在下方阶段六完成公开可见历史与三卧补采部分。源格式一致不等于独立文书核验，完整公共B仍未完成。

## 成交／租赁阶段六更新

[产品分组、挂牌时间线与三卧租赁](reports/2026-10-11_transaction_history_phase6.md)：延续25笔非随机售房，整理131条来源事件观察、17个候选产品组，新增4笔三卧关闭租赁。跨MLS重新挂牌、旧缓存、日期与价格冲突分别保留；22条较稳定字段候选因新增卧室冲突修正为21条，再排除重大成交价冲突为20条。均未认证同品质关系，不能形成两年价格指数。

812项程序检查通过，等长金额改动的负向指纹核验在输出前拒绝继续。公开45条来源链接及原创方法，逐项字段保留指定研究档案。3份输入的指纹是研究笔记和索引指纹，不是假称取得房源HTML或完整MLS导出。

```bash
python scripts/build_transaction_history.py --pilot-notes /path/to/pilot_working.json --history-notes /path/to/history_notes.json --source-map /path/to/used_source_references.json --manifest data/transaction_history_input_manifest.json --outdir /path/to/reviewed --public-qa qa/transaction_history_qa.json --source-index data/transaction_history_source_index.csv
python scripts/report_transaction_history.py
```

下一项：实际购买力与城市分流，先核对HMDA公开数据年份、用途和地理覆盖，再结合工资／就业及已有家庭结构。完整挂牌史、实际DOM、净租金和产权仍缺；学校、供给与定价模块继续保留，家庭A暂不接入。

## 实际购买力阶段七更新

[按揭实证与城市分流边界](reports/2026-10-11_purchasing_power_phase7.md)：取得三年87,002条橙县购房记录，严格筛选38,303笔自住、单套、现场建造、首抵、非商业／非反向／非开放额度贷款；四城使用四种统计区覆盖情景，另列两个重点统计区。2025年Irvine核心收入中位32.6万美元，四种边界情景32.2—32.8万美元；不能识别现金买家、原居城市、雇主或股票财富，不能将估值差额称为首付。

BLS 2025年度、2026Q1及2026年8月资料分别保留；岗位与家庭、原始同比与发布稿调整同比不混用。716项主流程检查、1,287项SQL／pandas与椭球面积交叉检查通过；等长改动负向核验在输出前失败。隔离目录11份输出与QA逐字节一致。公开11表682行、25份输入指纹及28项新增来源；原始贷款行不公开。

```bash
pip install -r requirements.txt
python scripts/build_purchasing_power.py --raw-dir /path/to/archive/raw
python scripts/audit_purchasing_power.py --raw-dir /path/to/archive/raw
python scripts/report_purchasing_power.py
```

恢复指定证据包中的raw目录；可加`--download`取得尚缺的官方文件，若指纹不同则停止并登记新版本。复用阶段三ACS标准表需从证据包或本仓库相应版本恢复。

步骤5仍受限完成：跨市同品质全成本、原居城市／选择案例及12—20位经纪人覆盖未达到验收。本轮未启动第二模型。下一项为跨市可比成本与买家来源补证；全市学校、供给和定价模块保持在后续计划。

## 跨市品质与成本阶段八更新

[跨市品质、持有成本与买家选择](reports/2026-10-11_crosscity_costs_phase8.md)：固定25笔成交基线中20笔符合轮廓；51组候选跨市配对有4组通过面积、房龄及成交时间门槛，仅涉及2套外市房。日期收紧至90天仅2组，完整品质认证0组，不估计城市溢价。

8套房屋的HOA及成本缺口单列；季度HOA折月，不把未知特别收费、保险或新买家税单填零。3个利率输入与2组纯演示费用情景由公式及高精度逐月余额迭代交叉核对。13位个人／品牌公开文章、6个机构品牌、3条匿名客户自述登记；长期Irvine来源不足，独立核验的完整买家流向0条。未进行访谈、第二模型审阅或多智能体工作。

```bash
python scripts/build_crosscity_comparison.py --input-dir /path/to/phase8/inputs --private-out /path/to/phase8/reviewed
python scripts/report_crosscity_comparison.py
# 若需指定个人研究阅读版的原生表计划：
python scripts/report_crosscity_comparison.py --private-dir /path/to/phase8/reviewed --doc-plan /path/to/phase8/doc_plan.json
```

恢复指定阶段八证据包的`inputs`目录（5份冻结笔记／基线），以`data/crosscity_source_manifest.json`校验后运行；`data/crosscity_scenario_config.json`为显式研究参数。两份脚本仅用Python标准库，第三条命令会生成含逐屋数据的私有报告计划，不能加入公共仓库。官方7份成功下载、3项失败状态分别登记；SHA256未被用于冒充未下载网页的原件。公开6表和QA，隔离输出及私有诊断共11份逐字节一致；等长输入篡改在写出前被拒绝。

下一项：全市学校与2026—27地址边界、教育项目和容量规则，之后继续供给、租赁全成本、定价及独立审阅。步骤5仍受限完成，完整公共B和买入／等待结论未完成，家庭A/C尚未接入。

## 阶段五至八独立审阅处理

[2026-10-12处理报告](reports/2026-10-12_review_remediation.md)及[八项状态](qa/review_disposition_20261012.csv)。B58-001当前网页版本已补，原冻结笔记不改；B58-007区分登记与独立认证，其余缺口保留。阶段八原命令自动应用来源版本补记，五张数值／覆盖表不变。学校模块可继续，完整品质／全成本／分流仍未识别。

## 阶段九：学校官方基线（2026-10-12）

[学校报告](reports/2026-10-12_schools_phase9.md)：51条Irvine地址目录、36条比较城市目录、144条学区背景记录；2025 Dashboard统一矩阵及2,310个群体指标槽位。IUSD当前与未来官方地图、15行边界登记、8项项目／待补领域、5组深读体验来源及51校检索登记分别记录。单址分配0条、年级实时余位0条；全市项目与家长体验仍未完整，不能称学校或整个B全部验收。

从指定私有证据包恢复`schools/raw`为`$SCHOOL_INPUT_DIR`。脚本先核5个文件SHA-256，拒绝静默换版；公开仓库不附原PDF、原网页或逐屋底稿。

```bash
python scripts/build_school_baseline.py --input-dir "$SCHOOL_INPUT_DIR"
python scripts/audit_school_baseline.py --input-dir "$SCHOOL_INPUT_DIR"
python scripts/report_school_baseline.py --private-out /tmp/school-report
```

标准库即可。公开`school_research_notes_20261012.json`是逐项来源支持的原创研究笔记，不是原件；报告脚本重建边界、项目、体验、容量四表及原生Docs内容计划。CDE行政City字段不等于市界覆盖；Virtual C指以课堂为主。ELA/Math为距离标准分数，不是百分比；各字段分母保留，缺失不是零。`qa/school_independent_audit.json`记录13,860字段核对、490个比例复算及两校SPSA四个数值跨格式核对；这些不认证学校因果效果或入学资格。

## 阶段十一：租赁与持有成本（2026-10-12）

受限基线：18笔租赁观察、8组候选匹配；没有已取得签署租约、完整净租金或完整新买家持有成本。见[阶段十一报告](reports/2026-10-12_rental_cost_phase11.md)。个案事实与原始官方文件从已授权私人证据包取得，目录保留 `raw/` 和 `private/`；不要将这些输入推送公开仓库。

```bash
python scripts/build_rental_cost_baseline.py --evidence-dir /path/to/rental-evidence --private-out /path/to/rental-evidence/private/derived
python scripts/audit_rental_cost_baseline.py --private-out /path/to/rental-evidence/private/derived
python scripts/report_rental_cost_baseline.py --evidence-dir /path/to/rental-evidence
```

仅依赖Python标准库。构建先核 `data/rental_source_manifest.json` 中18份已取得输入的SHA-256；失败下载不当原件。公开产物只包括来源链接、覆盖计数和明确虚构的计算情景；逐址价格、实际费用、配对详表和正式文档段落留私有。`--public-out`可指定隔离输出目录；`qa/rental_reproducibility.json`记录复跑与篡改输入拒绝检查。真实保险、MR、附费缺失时完整成本为空，不补零。

## 阶段十二：步骤9市场状态与条件估值（2026-10-12）

[定价报告](reports/2026-10-12_asset_pricing_phase12.md)：19条全房型／四卧模型序列、123个月橙县库存、旧25笔成交与9个新增跟进地址。证据支持议价改善与产品分化；严格目标重复成交、全量新签约及完整租购成本仍缺，不能宣称普遍低估。Zillow实际最后列为2026年8月，县级为9月。

从已授权本轮私人证据包恢复 `raw/`、`private/pricing_notes.json` 与 `private/frozen/`。先核8份输入指纹；变版需重新登记，不静默刷新。

```bash
python scripts/build_asset_pricing.py --evidence-dir /path/to/pricing-evidence --private-out /path/to/pricing-evidence/private/derived
python scripts/audit_asset_pricing.py --evidence-dir /path/to/pricing-evidence --private-out /path/to/pricing-evidence/private/derived
python scripts/chart_asset_pricing.py --private-out /path/to/pricing-evidence/private/derived
```

前两支只需标准库，图形需requirements中的matplotlib。build／audit可加 `--public-out /tmp/pricing-public` 隔离复跑。公开只有覆盖计数与9个虚构条件，私人输出含供应商和逐屋数值，不得提交。137项独立算术核对保留一项来源同比字段差异；11份复跑输出逐字节相同，变更输入在输出前被拒。下一步为步骤10利率历史传导；没有进入A/C。
