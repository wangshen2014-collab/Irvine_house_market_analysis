# 初始数据字典

## DOF人口住房标准表

一行是一地理单元／估计日期，共5个地理单元×7个日期=35行。vintage均为2026-05；2020为4月1日，其余为1月1日，不能直接称连续等长年度间隔。

population_total / population_household / population_group_quarters：人数。
housing_units_total / single_detached_units / single_attached_units / two_to_four_units / five_plus_units / mobile_home_units / occupied_units：住房单位数。
vacancy_fraction：0–1小数，展示百分比需乘100；不是待售库存率。
persons_per_household：每个已入住单位的家庭人口。不能用人口与住房增长视为独立需求证据。
source_sheet / source_row：原工作簿位置；source_id=SRC-001。

Single Detached不是四卧或法律SFH／detached condo的完整分类。没有净迁移字段。2020基准在DOF系列中可能包含学生住房口径调整，不能默认为未经修改的Census原始计数。

## 成交试采集模板

record_id：独立记录ID；address/APN用于去重与串联。同地址重复成交与撤牌重挂分别记录。
close_date、contract_date、listing_date：交割／签约／挂牌不同日期，ISO格式，缺项为空。
sale_price：实际成交价USD，不拿挂牌价代替。seller_concession：实际补贴USD，未知为空，不能补零。
bedrooms、living_area_sqft、year_built：数值，记录定义和来源。
legal_property_type：经核对的法律产权；shared_wall_status单独登记yes/no/unknown。
complete_listing_history、financing_evidence：事实与推断分开；无贷款记录不等于现金。
hoa_monthly、mello_roos_annual、comparable_rent：各自单位与日期；租金需在源表区分挂牌与签约。
source_id/source_url/retrieved_at：逐行追溯。
redistribution_status：approved/link_only/restricted/pending。未确认批准的原始成交行不进入公开仓库。

模板当前只有列头、0笔实际成交。验证器只做格式、重复和覆盖检查，不替代地理、产权与原来源人工验收。

## 人口组成与地理对应（第二轮）

county_components_2020_2025.csv有60行：DOF与Census各6地理单元×5完整年度。period_end_exclusive为所示年7月1日，实际覆盖截至6月30日。人数为有符号整数。residual在Census保留，DOF本轮组成相加为零残差；不把两系列拼接或平均。

community_pa_crosswalk_v0_2.csv有11行，父PA和子区分别记录。不同社区共享父PA不重复加总；Reserve与Orchard Hills有包含关系。城市GIS的TRACT／TR.编号是登记／开发tract，不是11位Census statistical tract GEOID，不得直接join。

## ACS城市家庭结构（阶段三）

acs_2024_detailed.csv一行是dataset／GEOID／variable，2,781行；acs_2019_detailed.csv为同类细项1,725行。2024的1YR仅2024期间、5YR为2020–2024；2019_5YR为2015–2019。年份是观测窗口，不是下载年份或年末快照。GEOID、原文件行／列、旧LOGRECNO、完整SHA256、source_id及source_url均保留。

estimate与moe90为估计与90%抽样MOE；原字符estimate_raw／moe_raw不能丢弃。-666666666等未计算单元为空，不补零；只有官方定义为受控制估计的MOE代码-555555555，可按官方说明视为零抽样误差，并保留受控制状态。它不表示没有非抽样误差。负的重复估计值是方差计算伪估计，可正常用于SDR；不可与实质性的负人数混为一谈。

人口／个人／家庭／已入住住房单位按表的Universe区分。B11005为家中任何未成年人，B25115为户主自己的未成年子女；两者不可替代。B07001是现居居民的过去一年居住地，只有迁入侧，非净迁移，也非买房家庭。B07011为个人收入中位数，非家庭收入。B19001最高档≥$200k，B25118最高档≥$150k，不能细分≥$300k／500k家庭。

acs_household_metrics_2024.csv为305项常规指标（包含近似MOE）；acs_replicate_metrics_2024.csv为25项同指标的SDR MOE优先覆盖，报告生成时采用该覆盖。acs_household_metrics_2019.csv为60项历史结构指标；acs_household_window_changes.csv为60项不重叠窗口差值。unit=fraction的展示百分比乘100，差值展示pp也乘100。SDR指标按4/80×平方差之和、再乘1.645计算MOE。无VRE的合计用RSS、子集比例用Census近似公式，并记录方法及负根号时的保守ratio fallback。

差值显著性仅90%名义检验，未经多重比较调整，不能替代实际重要性；城市边界／人口控制变化与非抽样误差另列限制。2019与2024收入保留各自美元基准，本轮不计算实际收入增长。高收入、租买、年龄、有孩边际占比不能相乘构造买家数量。
