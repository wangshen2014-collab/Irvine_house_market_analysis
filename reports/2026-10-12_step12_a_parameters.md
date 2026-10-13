# 步骤12：统一A参数接口

2026-10-12，America/Los_Angeles。仅提供公共B接口，没有读取或运行A；完整独立审阅及重大问题处理前不得自动导入。机器可读主表为 `data/step12_a_parameter_interface.json`，本文件为同值阅读版。

统一口径：每行注明地域／产品、观察窗口和前瞻期限、单位、名义／实际、税前／税后、证据类型、基准／压力、来源、信心和更新规则。null表示未知，不表示0。未给压力数值意味着尚未设定，不得自行继承旧数字。历史值、公开菜单和虚构敏感性均为 reference_only，不是获准家庭输入。

### 参数总表

| 参数与适用范围 | 基准／压力与证据类型 | 时间、单位与口径 | 来源、采用与更新 |
| --- | --- | --- | --- |
| 目标净购入价；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：需当期合同／净让利；期限：购入日；单位：USD/套；名义美元／名义比率；税前；不含个人税效 | E03,E07,E08；信心：未识别；blocked_pending_evidence；更新：合格可比成交、净让利与房屋条件齐全后 |
| 房价前瞻增速；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：历史代理截至2026-08；期限：6—12月、2—3年、3—5年、5—10年分开；单位：%/年；累计另标；名义美元／名义比率；税前；不含个人税效 | E07,E08；信心：低；blocked_pending_evidence；更新：固定品质净成交、数量与供给共同变化 |
| 房价条件网格；无地域；虚构标准房 | 基准：100；压力／替代：[90,100,110]；synthetic_sensitivity | 观察：2026-10-12设计；期限：单次未来购入时点；单位：价格指数，基期100；名义指数；不适用 | E11；信心：算术高；市场解释不赋值；reference_only；更新：获得真实报价后重新选择测试幅度 |
| Stonegate四卧历史变化；Stonegate供应商地域；SFR+condo四卧，无目标房龄／共墙筛选 | 基准：-1.0819972533501976；压力／替代：未定（null）；historical_statistic | 观察：2025-08至2026-08；2026-10-12下载修订版；期限：不用于预测；单位：同比%；名义模型价格变化；不适用 | E07；信心：源内高；目标外推低；reference_only；更新：同版本、同月份更新；保留旧版 |
| Orchard Hills四卧历史变化；Orchard Hills全区，非Reserve；SFR+condo四卧，无目标房龄／共墙筛选 | 基准：-2.6678856689451025；压力／替代：未定（null）；historical_statistic | 观察：2025-08至2026-08；2026-10-12下载修订版；期限：不用于预测；单位：同比%；名义模型价格变化；不适用 | E07；信心：源内高；Reserve外推低；reference_only；更新：同版本更新；不得改成Reserve |
| 同产品有效净租金；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核；整租／无家具／租期相同 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：当期；18笔旧观察非有效净租；期限：每月及完整租约期；单位：USD/月；名义美元／名义比率；税前；不含个人税效 | E12；信心：未识别；blocked_pending_evidence；更新：取得真实租约、优惠、租客承担费用及服务匹配 |
| 同产品租金增长；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：缺同品质续租或重复租约；期限：逐年，与持有期匹配；单位：%/年；名义美元／名义比率；税前；不含个人税效 | E12；信心：未识别；blocked_pending_evidence；更新：同产品净签约／续租资料可比后 |
| 三卧租／四卧买服务差异；四比较城市；面积、卧室、院子、通勤、学校、稳定性 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：当期候选清单；期限：每个比较期限；单位：USD/月或不货币化评分；名义美元／名义比率；税前；不含个人税效 | E03,E04,E12；信心：偏好尚待确认；blocked_pending_evidence；更新：A/C阶段由使用者核服务与价值 |
| 股票含股息历史总回报；待选投资市场／币种；待确认广泛指数或实际组合；含股息再投资 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：缺匹配总回报系列；期限：历史各完整持有窗口；单位：几何年化%及累计%；名义美元／名义比率；税前；不含个人税效 | E11；信心：未取得；blocked_pending_evidence；更新：取得一手总回报、股息再投资、费用与币种定义 |
| 股票含股息预期总回报；待选投资市场／币种；待确认组合；含股息再投资 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：没有本轮采用依据；期限：与买租共同终点匹配；单位：名义年化%；名义美元／名义比率；税前；不含个人税效 | E11；信心：未识别；blocked_pending_evidence；更新：独立确定基准、费用、估值与预测依据 |
| 股票税后收益转换；适用纳税地域待核；资本利得、股息、递延账户分别处理 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：未读取家庭税务；期限：逐年现金流及出售时点；单位：税后USD及%；名义美元／名义比率；税后值未知 | E11；信心：未识别；blocked_pending_evidence；更新：A阶段确认账户、税率、实现时点后 |
| 待购资金机会收益；美元；现金／短债等实际可持有资产待定 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：缺个人可实现收益；期限：等待6—12月；期限匹配；单位：税后年化%；名义美元／名义比率；税后值未知 | E09,E11；信心：未识别；blocked_pending_evidence；更新：确认工具、期限、流动性和税务后 |
| 名义／实际转换；与支出和投资相应地域；待选一致通胀指标 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：本轮未设长期通胀假设；期限：与现金流期限一致；单位：%/年；名义美元／名义比率；不适用 | E11；信心：未识别；blocked_pending_evidence；更新：明确指数和预测依据后 |
| 个人固定贷款利率；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核；贷款额度和资格待核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：须同日Loan Estimate与锁定条件；期限：实际贷款期；单位：票面%/年；APR另列；名义美元／名义比率；税前；不含个人税效 | E09；信心：未取得；blocked_pending_evidence；更新：合法取得同日个人LE、点数、费用、锁定期限 |
| 全国30年固定参考；美国全国；PMMS调查口径，非个人jumbo | 基准：7.4；压力／替代：未定（null）；historical_statistic | 观察：2026-10-08发布／观察；期限：历史周值；单位：%/年；名义美元／名义比率；税前；不含个人税效 | E09；信心：参考高；个人适用低；reference_only；更新：每周新版单独保存 |
| 公开jumbo零点菜单；SchoolsFirst公开样例；30年固定；125万美元／LTV60%／FICO740／45天锁 | 基准：7.375；压力／替代：{"plus_1_point_rate":7.125,"minus_1_point_rate":7.625}；observed_menu | 观察：2026-10-12网页及冻结HTML；期限：报价时点；非长期预测；单位：票面%/年；名义美元／名义比率；税前；不含个人税效 | E09；信心：提取高；能否获得未知；reference_only；更新：新日期、额度、信用、产权或点数变更时 |
| 未来固定利率条件网格；无地域；30年摊还虚构贷款 | 基准：未定（null）；压力／替代：[4.5,5.5,6.5,7.375,8.5]；synthetic_sensitivity | 观察：2026-10-12设计；期限：未来融资时点；单位：票面%/年；名义美元／名义比率；税前；不含个人税效 | E11；信心：算术高；概率未知；reference_only；更新：新的实际贷款环境或风险范围出现时 |
| 公开jumbo 5/1 ARM压力；CU SoCal公开样例；30年摊还／CLTV60%／FICO760+；1年CMT+2.5 | 基准：{"initial_rate":6.125,"caps":"2/2/6","initial_PI":607.6105}；压力／替代：{"month61_PI":727.0435,"month73_PI":852.0358,"month85_PI":981.1539}；observed_menu | 观察：冻结2026-10-12；新网页标10-13生效；期限：前60月、61／73／85月分开；单位：票面%及USD/月每初贷10万；名义美元／名义比率；税前；不含个人税效 | E09,E11；信心：菜单提取与算术高；个人条款未知；reference_only；更新：取得正式合同及重置指数日期后 |
| 再融资与费用；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核；未来资格未知 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：未来LE未取得；期限：发生月份与剩余期限分别建模；单位：票面%、USD、月份；名义美元／名义比率；税前；不含个人税效 | E11；信心：未识别；blocked_pending_evidence；更新：实际获批后更新费用、期限与余额 |
| 首付款／本金／摊还期；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：家庭参数未读取；期限：购入及实际持有期；单位：USD、LTV%、月；名义美元／名义比率；税前；不含个人税效 | E11；信心：本轮不设；blocked_pending_evidence；更新：A阶段确认资金、资格及期限 |
| 买入交易费用；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：逐屋与贷款结算待定；期限：购入时一次性；单位：USD及占价格/贷款比例分别标；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：LE／结算、产权、托管、检查及代理协议齐全后 |
| 出售交易费用；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：合同未定；期限：共同终点或出售时；单位：USD及占售价%；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：实际代理协议、托管与转让费用明确后 |
| 新买家房产税总额；Orange County逐地块；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：新税基、税率区与特别评估待核；期限：每税年；单位：USD/年；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：以预期新税基、当年税率区与官方账单核算 |
| Mello-Roos／CFD特别税；Irvine／Stonegate／Orchard Hills Reserve；逐屋；逐地块／CFD | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：当前账单、上限与到期安排待核；期限：逐年到期路径；单位：USD/年；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：官方特税报告、实际账单及升级率明确后 |
| HOA与特别征费；Irvine／Stonegate／Orchard Hills Reserve；逐屋；建筑形态和产权分开 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：主／子HOA及储备资料待核；期限：逐月及特别事件；单位：USD/月；特别征费USD；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：主子会费、预算、储备及征费文件齐全后 |
| 可获得的保险全成本；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：逐屋报价与承保未知；期限：至少首年及续保压力；单位：USD/年；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：保障范围、免赔额、灾害险、可保性核实后 |
| 维修／替换储备；Irvine／Stonegate／Orchard Hills Reserve；逐屋；房况、设备、院子与产权责任 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：检查与寿命表未取得；期限：逐年及大修年份；单位：USD/年和事件USD；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：检查、责任划分和报价后 |
| 水电、园艺及其他差额；Irvine／Stonegate／Orchard Hills Reserve；逐屋；相同住房服务 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：租约和HOA覆盖待核；期限：逐月；单位：USD/月差额；名义美元／名义比率；税前；不含个人税效 | E12；信心：未取得；blocked_pending_evidence；更新：双方承担范围与租约明确后 |
| 购房税收净效果；适用纳税辖区待核；扣除资格、上限与实际边际影响 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：未读取家庭税务；期限：逐税年；单位：税后USD/年；名义美元／名义比率；税后值未知 | E12；信心：未取得；blocked_pending_evidence；更新：A阶段合法核税务与具体适用规则后 |
| 共同比较终点／持有期；Irvine／Stonegate／Orchard Hills Reserve；逐屋；四卧；约1650sf以上；2010+；无共墙；detached condo产权另核 | 基准：未定（null）；压力／替代：未定（null）；missing | 观察：本轮未确认家庭期限；期限：6—12月等待与后续共同终点分开；单位：月／年；名义美元／名义比率；税前；不含个人税效 | E11,E12；信心：本轮不设；blocked_pending_evidence；更新：A阶段确认稳定性、退出计划与终点后 |

### 采用说明与防重复计数

1. 目标净购入价（target_purchase_price）：ZHVI、挂牌价和房产估值均不能代替。
2. 房价前瞻增速（housing_price_growth）：不得以最近一年涨跌直接外推多年。
3. 房价条件网格（housing_price_sensitivity）：±10%仅检验暴露，既非预测、分位数，也非所需折价。
4. Stonegate四卧历史变化（zhvi_stonegate_yoy）：不是同品质指数。
5. Orchard Hills四卧历史变化（zhvi_orchard_hills_yoy）：不能以此填Reserve精确变动。
6. 同产品有效净租金（same_product_effective_rent）：有效租金=(合同总租金+强制租客费用−已确认优惠)/租期月数；押金另列。
7. 同产品租金增长（rent_growth）：挂牌观察不作年度增长率。
8. 三卧租／四卧买服务差异（housing_service_difference）：不将偏好货币化为市场事实。
9. 股票含股息历史总回报（equity_total_return_historical）：既有S&P价格序列不适用；不得把价格回报直接当总回报。
10. 股票含股息预期总回报（equity_total_return_expected）：基准和压力均未定；以后需另测收入／RSU／股票共同下行，不能假设独立。
11. 股票税后收益转换（equity_after_tax_return）：未实现收益不能每年一律扣同一税率。
12. 待购资金机会收益（cash_opportunity_return）：国债某期限收益率不自动等于股票收益或个人存款收益。
13. 名义／实际转换（inflation_deflator）：实际收益=(1+名义收益)/(1+通胀)−1；税制通常按名义金额，不能重复扣。
14. 个人固定贷款利率（personal_mortgage_rate）：PMMS或银行菜单不得填成个人获批基准。
15. 全国30年固定参考（pmms_reference）：不用于与8月房价作同月因果回归。
16. 公开jumbo零点菜单（fixed_menu_reference）：零点APR7.42%；点数占贷款额；不把bank jumbo名称当FHFA监管边界。
17. 未来固定利率条件网格（future_rate_sensitivity）：没有中心预测；每条与价格、收入、股票和供给联合解释。
18. 公开jumbo 5/1 ARM压力（arm_reference）：压力为指数充分高且达到各次上限，不是预测；不假设能再融资。
19. 再融资与费用（refinancing_assumption）：默认不承诺发生；条件路径需设不获批情景，月供降不等于总利息省。
20. 首付款／本金／摊还期（down_payment_and_term）：归一化P100／现金40／360月只作公式演示，不是家庭建议。
21. 买入交易费用（acquisition_cost）：不套通用百分比；可退预付和不可回收费用分开，点数另列防重复。
22. 出售交易费用（disposition_cost）：不默认固定6%；与终值及未偿本金一致处理。
23. 新买家房产税总额（property_tax_total）：不使用卖家旧税单直接外推；补充税是过渡补计，不永久双算。
24. Mello-Roos／CFD特别税（mello_roos）：与property_tax_total明确含／不含关系，禁止重复计入。
25. HOA与特别征费（hoa）：不因detached就假定无HOA。
26. 可获得的保险全成本（insurance）：未知不填零；地址与承保限制可能直接改变行动。
27. 维修／替换储备（maintenance_capex）：简单房价百分比只能另行标敏感性，不能装成实测。
28. 水电、园艺及其他差额（owner_renter_cost_difference）：比较增量，避免将租买都承担的同一支出重复列为购买成本。
29. 购房税收净效果（tax_benefit）：不能以利息×最高边际税率直接默认抵扣。
30. 共同比较终点／持有期（holding_horizon）：不能拿1年租费与30年总利息直接比。

### 接口验收

完整字段不意味着数值已知。本表所有关键实盘值仍需对应证据；目标净价、有效租金、股票含息预期和个人固定利率被程序显式阻止自动采用。可继续做清楚标记的条件计算，但不得据此输出家庭买租最终结论。

后续A应比较共同终点的现金流和净资产，单列本金转权益、税费、买卖一次费用、净让利、住房服务差异和投资余额；名义与实际、税前与税后、几何收益与算术平均不能混用。联动压力至少包括收入与RSU／股票一起下降、融资资格收紧、房价／租金与就业共变及ARM无法再融资。

来源ID、原件／表格定位、版本和取用等级见 `reports/2026-10-12_step12_review_packet.md` 及证据索引。
