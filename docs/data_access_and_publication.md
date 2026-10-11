# 数据取得、版本与公开范围

## 存储分工

GitHub：脚本、非个人参数、来源索引、获准公开的标准统计数据、QA、报告底稿和STATUS。
Drive：官方原始工作簿、大文件、权利待核底稿、个人信息及家庭A/C，以及正式Docs/Sheets。

每类内容只有一个主版本。源文件保持原字节，记录SHA-256和取得日期；GitHub标准数据注明源文件、sheet、row、vintage。正式报告标记对应commit，修改计算参数后先复算再更新展示表。原任务书与私人目录的链接保留在私有入口，不在公开仓库发布。

## 已核对的取得条件

- DOF Conditions of Use的Ownership段允许依法复制一般的州自有信息，同时排除未获许可的第三方版权内容。本轮仅公开州统计表的35条结构化记录，并保留DOF机构、2026年5月版本和原链接；不复制照片或第三方图文。
- Redfin Terms 2.3列有限许可、再分发及自动抓取限制。本轮没有自动抓取房源或复制平台数据库；Data Center入口已读，但具体下载文件和各自使用条件待核对。
- Irvine GIS图层显示APNSource包括Assessor、OCPW、ParcelQuest等。原始要素先保存到Drive，仅在仓库登记方法、来源与可行性观察；不因为市政府托管就推定所有字段可自由再分发。
- RecorderWorks是公开索引，不是已取得的完整成交数据库；未查任何个人登记记录，未购买文书。
- Census API本轮返回HTTP200的Missing Key HTML，不计作成功数据下载。可使用已有授权API key或官方可下载表继续，不把key写进代码、仓库或STATUS。

来源中的public_storage分别为public_domain_state_owned、link_only、terms_reference；这些是本轮发布处理状态，不是对整个来源的统一法律认证。未来新增来源逐项核对。

## 私有内容

家庭收入资产、账户号码、私人访谈、个人贷款／保险报价、账号授权和A模型留在私有资料中。公开房源字段不包含买卖双方个人身份。授权MLS导出如有也不自动允许放到公开仓库。
