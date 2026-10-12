# Irvine House Market Analysis

尔湾及周边住房市场独立研究。研究需求、供给、资产定价，覆盖 Orange County、Irvine 全市、北尔湾及 Lake Forest、Tustin、Aliso Viejo 等替代地区。

## 项目状态

2026-10-11启动。已完成县级历史人口／净迁移、城市家庭数量分解及官方长期预测的阶段研究；已补城市ACS结构及重点社区边界／统计代理区诊断；成交可行性、实际买家购买力、完整需求／供给／定价研究尚未完成，尚未形成买入／等待结论。

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

已完成DOF人口住房35行、DOF／Census人口组成60行，以及家庭／官方预测五表175行提取与复算，并建立社区—PA对应11行。20–30笔成交试样本、全市学校和项目覆盖、社区层家庭结构及实际买家购买力、完整需求／供给／定价结论均未完成。成交模板为空，验证器会如实拒绝将其视为完成。

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

先完成阶段三ACS批量表下载。阶段四另需约130MB来源缓存；官方动态服务变化会使冻结指纹核对失败，应恢复已归档快照或明确登记新版本。公开地图只含Census几何；原市政几何及详细叠加图按来源权利状态保留指定资料档案。下一步20–30笔实际成交／租赁字段试采集，当前仍为0笔。
