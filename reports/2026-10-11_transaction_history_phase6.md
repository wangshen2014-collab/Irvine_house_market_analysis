# 产品分组、挂牌时间线与三卧租赁｜阶段六

研究观察截止：2026-10-11，America/Los_Angeles。检索窗口2024-10-12至2026-10-11。本轮延续阶段五的25笔非随机售房试样本，完成公开可见历史扩展及三卧租赁补采；完整公共B、全市场历史和买入／等待判断仍未完成。

## 完成与修正

- 25笔售房各有可追溯的挂牌与关闭字段。形成131条来源事件观察，其中130条在窗口内、1条窗口前置事件；包括重复关闭的冲突分支，不能把事件行数当交易数量。
- 暂分17个产品小组，按社区、卧室、面积、建年和共墙拆开。小组只是候选分层；相同面积不证明同户型，地段硬伤、景观和升级未核，尚无同品质价格指数。
- 新发现一笔卧室数跨字段冲突，前轮22条较稳定四卧无共墙候选修正为21条。再排除重大成交价冲突后为20条；这些仍不是已核可比成交。
- 新增4笔三卧、整租、无家具、至少12个月且发布无共墙的MLS关闭记录。另3笔候选因整租／单间、日期或租赁条件冲突排除。与前轮3笔四卧关闭记录合计7笔，不能混算全市场租金。

## 时间线定义

分别保存售房挂牌、重新挂牌、调价、撤牌、取消、到期、Contingent、Pending、MLS关闭、网站转述Public Record，以及租赁挂牌／撤牌／关闭。网站转述记录日不是已取得契据日，撤牌不等于成交。跨MLS按同一房屋串联，但旧挂牌结束日缺失时，不推断连续营销。

至少3个售房案例可见多个不同MLS编号；只按最新编号会缩短可见历史。程序同时给出最早可见挂牌、本次MLS首挂及最近一次重新上线至关闭的日历跨度。所有跨度均包含可能的下架及成交托管时间，不能认定实际在市天数或CDOM；25笔实际签约DOM及完整MLS史仍各0/25。

挂牌价差使用“关闭价／观察到的挂牌价－1”，分别对最初可见价和最后可见价计算。它衡量个案相对报价的差异，不是市场价格变动；最初可见价不保证真正初始价，最后可见价不保证完整历史中的最终价。重大价格冲突不计算价差，也不以多数网站表决消除矛盾。

实际售房关闭日期仍为2025-02-05至2026-10-01，没有2024年末的已核MLS关闭样本。季度统计只表示固定样本覆盖，缺样季度不表示当地无成交；不足以估计近24个月涨跌、市场成交量、库存、去化速度或因果机制。

## 租赁与品质限制

新增三卧记录是公开MLS关闭字段，不是签署租约、净有效租金或入住时间。家具、租期、整租范围、共墙和月租单位逐项核对；押金不当租金，同地址旧房间广告不并入整租。新增社区归属仅按经纪描述，本轮没有重做4个地址的市政GIS核对。三卧约2047平方英尺带Conservatory的同品质关闭样本仍缺。

地块面积、共墙、法律产权和居住面积分别保留；未核实的升级、硬伤、让利、税费、MR、融资及产权不填零。多站共享CRMLS不等于独立文书核验。本轮同一研究线程串行检查，没有第二模型、第三方现场或签署文书审阅。

## 实际文件与验证

- `scripts/build_transaction_history.py`：从冻结个人研究笔记整理来源事件、分组、日历跨度、挂牌价差和三卧租赁；不抓取房源网站。
- `scripts/report_transaction_history.py`：生成公开方法报告；可选生成个人阅读版表格计划。
- `data/transaction_history_source_index.csv`：45条记录×来源URL，公开链接及访问处理，不重发受限数值字段。
- `data/transaction_history_input_manifest.json`：3份输入的完整SHA-256；是研究笔记／索引指纹，不冒充房源HTML原字节。
- `qa/transaction_history_qa.json`：812项结构、日期、单位、窗口、筛选和算术检查通过。用Fraction与Decimal交叉复算价差，关键跨MLS日期有固定参考值。
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
