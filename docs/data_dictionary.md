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
