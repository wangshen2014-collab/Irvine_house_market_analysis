# Irvine House Market Analysis

尔湾及周边住房市场独立研究。研究需求、供给、资产定价，覆盖 Orange County、Irvine 全市、北尔湾及 Lake Forest、Tustin、Aliso Viejo 等替代地区。

## 项目状态

2026-10-11 启动。当前处于范围登记、来源核验和数据可行性阶段；尚未形成买入／等待结论。

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

当前只完成DOF官方统计模块的35行提取与复算。20–30笔成交试样本、全市学校和项目覆盖、需求／供给／定价结论均未完成。成交模板为空，验证器会如实拒绝将其视为完成。
