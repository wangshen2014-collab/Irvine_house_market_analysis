# STATUS

最后更新：2026-10-11，America/Los_Angeles；第三轮需求阶段二。

## 当前阶段

县级历史人口／迁移、城市家庭数量及官方长期预测已有阶段判断。公共B整体未完成，家庭A未接入，成交可行性未通过。

## 已完成与关键判断

- E-5人口住房35行、DOF/Census历史组成60行、社区—PA对应11行延续前轮。
- 本轮DOF人口51快照、组成50期、家庭31快照；SCAG正式／草案33行；城市家庭分解10行，共175行。来源增至36项。
- Irvine 2025→2026人口+92，已入住户+1,177；户均人数从2.5245降至2.5004。会计分解成立，不能当作独立需求证据。
- 当前DOF情景橙县2050人口3,151,816，比2025低0.56%；SCAG2024正式规划2050为3,439,000。保留约28.7万人差异，不平均、不当置信区间。
- DOF P-4家庭情景2040比2025多78,133户（7.06%）；January1、Vintage2025，不同于人口July1/Vintage2026。
- SCAG2026 LDX四城为Preliminary；反馈截止2026-11-20，预计2028春正式采纳。Irvine家庭2024/2035/2050=116,683/126,586/132,986，岗位同期净变化−8,451。
- SCAG家庭规划包含住房容量、Housing Element及空间政策；不是北尔湾四卧无共墙买家数量预测。2024正式表的城市未来人口列不属正式采纳文件、未经地方审核。
- DOF人口方法原字节确为2024 Baseline；搜索服务同URL旧缓存仍写2023，按下载版本登记。首发09-20/09-30的元数据差异保留，不影响当前2026-03-13版本。

## 本轮实际产物与验收

- reports/2026-10-11_households_forecast_phase2.md
- data/clean/dof_oc_population_projection_v2026.csv（51行）
- data/clean/dof_oc_projected_components_v2026.csv（50行）
- data/clean/dof_oc_households_projection_v2025.csv（31行）
- data/clean/scag_city_county_forecast_vintages.csv（33行）
- data/clean/city_household_growth_decomposition.csv（10行）
- data/forecast_source_manifest.json；data/sources.csv（36项）
- scripts/build_forecast_baseline.py；scripts/plot_forecast.py
- qa/forecast_households_qa.json（pass）：8数值原文件指纹；51快照与50组成等式；10历史分解；Irvine/LF/Tustin/Aliso 173/62/54/23个TAZ汇总等于PDF32页图表。
- figures/orange_county_forecast.svg；图表PNG及14个原始来源文件的私有包，真实链接在V2正式tab登记。
- 正式V2新增「需求：家庭与未来预测」，保留原方案及既有报告tab。前轮QA仍保留，不因本轮而改写历史快照。

## 缺口与覆盖

成交0/20–30、人工0/5；完整公共B未完成。家庭数量不等于购房家庭，缺ACS年龄／租买／有孩／收入结构及MOE、迁入购买力、HMDA融资、IRS流向核对；社区精细polygon与Census tract/GEOID叠加未完。学校仍为GIS候选地块，项目供给及定价模块未验收。

县级历史迁移方向仍是两系列五年国内净流出、总净迁移仅2023–2024为正。DOF与Census非完全独立；Riverside最新国内方向有差异。未来净迁移转正是模型假设，不是观察结果。P4未随2026人口更新；城市2024 LDX与现行E5不同起点不拼接。

## 下一项具体动作

取得官方ACS可下载数据，对Irvine及三替代城市的家庭类型、租买、有孩、年龄、收入与迁移分层；登记1-year/5-year窗口、MOE与可比性。API无key返回MissingKey HTML未解决，优先官方bulk／下载表替代。然后把社区边界与Census tract叠加验收，再进入目标买家购买力及供给项目兑现率。

## 接续规则

先读本文件、AGENTS、范围卡及本轮来源。只接续独立研究，不读旧宏观／旧市场结论锚定判断。先完成公共B再接家庭A；私人A/C、私人链接、账号信息不进入公开仓库。按真实产物和commit保存；阶段报告不等于全项目完成。
