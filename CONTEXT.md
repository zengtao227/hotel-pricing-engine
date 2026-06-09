---
project: hotel-pricing-engine
status: mvp-running
owner: zengtao227
language: zh-CN
primary_goal: 酒店房间动态定价与收益优化
created_at: 2026-06-08
updated_at: 2026-06-09
---

# Project Context

`hotel-pricing-engine` 是一个酒店动态定价与收益优化项目。当前阶段已经是可运行的 Streamlit MVP，支持销售演示、候选价收益模拟、价格弹性回测、价格审批与发布模拟。它仍然不是成熟商用软件，真实客户试用前需要继续加强数据导入、数据质量报告、访问保护和审计存储。

沟通时优先使用以下术语：

- `入住日期`: 客人实际入住的日期
- `预订日期`: 客人下单或创建订单的日期
- `提前期`: 预订日期距离入住日期的天数，也称 booking lead time
- `间夜`: 一间房入住一晚
- `房型`: 标准间、大床房、套房等可售产品单位
- `可售库存`: 某入住日期和房型还可以售卖的间夜数
- `成交价`: 客人实际支付或确认的房价，不是挂牌价
- `挂牌价 / 基准价`: 酒店内部审批和管理的基础价格
- `渠道展示价`: Booking、携程、官网等渠道最终展示给客人的价格
- `渠道净收益`: 扣除折扣、佣金和渠道成本后的酒店实际收益
- `ADR`: 平均每日房价，房费收入 / 售出间夜数
- `RevPAR`: 每间可售房收入，房费收入 / 可售间夜数
- `Pickup`: 某一观察窗口内新增预订量
- `取消率`: 已确认订单后续取消的比例
- `推荐价`: 系统建议人工审核的价格
- `候选价`: 系统在约束范围内枚举比较的一组可执行价格
- `价格弹性`: 价格变化时未来未成交需求变化的估计

## 当前状态（2026-06-09）

MVP 已可运行。Streamlit 应用部署在 Frankfurt VPS，通过 systemd 托管，并由 Caddy 反代提供 HTTPS 访问。
详细部署说明见 `docs/deployment.md`。

访问地址：`https://hotel.zengsg.dpdns.org`
域名：zengsg.dpdns.org（DigitalPlat，有效期至 2027-06-08，Cloudflare 托管）
认证：当前未启用 HTTP Basic Auth；如需公开演示外的长期开放访问，应补充更完整的认证机制。

当前功能：

- demo / CSV 数据加载
- 每日房型级 Occupancy、ADR、RevPAR、Pickup 指标
- 可解释调价建议
- 候选价收益模拟
- 价格弹性基线
- 价格弹性收益回测
- 候选价收益曲线
- 静态实际销量对照
- 多语言销售演示看板
- 酒店配置：房型、基准价、最低价、最高价、周末加价
- 价格审批与发布模拟
- 审批和推送日志 CSV 持久化
- 多语言 Excel 导出

## 当前目标

先建立清晰的需求、数据口径和建模路线，再逐步进入真实数据试用。第一版应是“辅助人工调价”的决策支持系统，而不是自动改价系统。

## 产品原则

- 收益优化优先于单纯房价预测。
- 推荐结果必须能解释原因，不能只给一个数字。
- 先做可验证的简单模型，再逐步增加复杂度。
- 初期默认人工确认调价，避免自动化带来的业务风险。
- 每个价格建议都要带上数据依据、置信度和异常提醒。
- 当前模型输出的是“预期收益最高的候选价”，不是保证真实世界最高收益。
- 当前推荐价默认是酒店内部审批用的基准挂牌价；真实发布到 OTA 时，还需要渠道折扣、佣金和促销规则。

## 非目标

- 当前不直接做 OTA/PMS 自动写价能力。
- 当前不做多酒店集团级复杂权限系统。
- 当前不把模型输出当成不可质疑的最终价格。
- 当前不承诺使用特定机器学习框架。
- 当前不硬编码 Booking、携程、Expedia、Agoda 等平台的固定折扣或固定佣金。

## 演示和模型说明应该使用哪些文件

### 做演示文稿时优先使用

- `docs/demo-presentation-script.md`
  - 演示文稿主文稿。
  - 已按页组织：标题、酒店定价问题、100% 入住不一定最高收益、剩余库存如何定价、价格弹性、渠道折扣、回测、审批发布、下一步计划。
  - 适合转换成 HTML 演示页或 PPT。

- `README.md`
  - 项目总览。
  - 适合提炼“当前系统已完成什么”。

- `docs/i18n-dashboard.md`
  - 多语言销售看板、回测页、审批发布页、VPS 更新说明。
  - 适合解释界面结构。

### 讲模型细节和价格形成逻辑时优先使用

- `docs/revenue-optimization-model.md`
  - 最重要的模型说明文档。
  - 解释为什么不是追求 100% 入住率，剩余 30 间房如何通过候选价收益模拟定价，旧数据如何进入模型，价格弹性如何起作用。
  - 也包含挂牌价、OTA 折扣价、渠道净价之间的关系。

- `docs/modeling-approach.md`
  - 原始建模路线和建模假设。
  - 适合补充长期模型升级方向。

- `src/revenue_simulation.py`
  - 候选价收益模拟、价格弹性估计和候选价收益曲线的核心代码。

- `src/pricing_engine.py`
  - 调用收益模拟并生成推荐价、推荐原因、风险提示和收益字段。

### 讲 OTA 渠道折扣和调价频率时使用

- `docs/ota-channel-pricing-notes.md`
  - 说明挂牌价、渠道展示价、渠道净收益、OTA 佣金 / 折扣、价格更新频率。
  - 适合后续设计 `Channel Pricing Rules` 模块。

## 项目文件夹结构说明

### 根目录

- `README.md`
  - 项目介绍、当前能力、快速启动、问题定义和 MVP 范围。

- `CONTEXT.md`
  - 项目上下文、术语、当前状态、文件地图和协作约定。

- `requirements.txt`
  - Python 依赖。

- `.gitignore`
  - 忽略虚拟环境、缓存、原始数据、生成的 Excel 和审计日志 CSV。

### `app/`

- `app/streamlit_app.py`
  - 主 Streamlit 应用。
  - 负责页面布局、语言选择、侧边栏配置、销售看板、调价建议、回测分析、审批发布、酒店配置和数据预览。

### `src/`

- `src/data_loader.py`
  - 加载 demo 数据或用户上传 CSV。
  - 统一解析日期字段。

- `src/sample_data.py`
  - 生成内置 demo 数据。
  - 当前 demo 定位为中国二线城市四星商务酒店价格场景。

- `src/validation.py`
  - 基础数据校验。
  - 检查必要字段、日期、非正价格、非正房间数、重复库存等。

- `src/metrics.py`
  - 把订单展开为 room nights。
  - 计算每日房型级 sold_rooms、room_revenue、occupancy、ADR、RevPAR、pickup 等指标。

- `src/revenue_simulation.py`
  - 候选价收益模拟核心。
  - 估计需求、价格弹性、候选价收益和推荐价。

- `src/pricing_engine.py`
  - 推荐引擎。
  - 将 metrics、bookings、current_prices 输入收益模拟，输出推荐价、动作、收益字段、置信度、原因和风险提示。

- `src/price_rounding.py`
  - 价格尾数规则。
  - 支持中国酒店 6 / 8 / 9 尾数、按 5 取整、按 1 取整。

- `src/hotel_config.py`
  - 酒店配置。
  - 管理房型、基准价、最低价、最高价、周末加价。

- `src/backtesting.py`
  - 回测分析页面和逻辑。
  - 包括价格弹性收益回测、候选价收益曲线、静态实际销量对照和回测 Excel 导出。

- `src/approval_workflow.py`
  - 价格审批与发布模拟。
  - 支持最终批准价、人工修改、批量采纳、模拟推送、样式标记和审计日志导出。

- `src/audit_log_store.py`
  - 审批和推送日志持久化。
  - 当前保存到 `data/audit_logs/price_approval_publishing_log.csv`。

- `src/report_export.py`
  - 多语言 Excel 报表导出。

- `src/i18n.py`
  - 多语言文案、字段名、房型名称、推荐原因、风险提示翻译。

- `src/ui_help.py`
  - 页面中的指标解释、tooltip 和字段说明。

### `docs/`

- `docs/requirements.md`
  - 产品需求和 MVP 验收标准。

- `docs/data-requirements.md`
  - 数据字段、口径和质量要求。

- `docs/modeling-approach.md`
  - 原始建模路线。

- `docs/revenue-optimization-model.md`
  - 当前最重要的模型说明文档。
  - 解释收益最大化、剩余库存定价、价格弹性、候选价收益模拟、回测和渠道价。

- `docs/ota-channel-pricing-notes.md`
  - OTA 渠道价格、折扣、佣金和更新频率说明。

- `docs/demo-presentation-script.md`
  - 演示文稿文稿。
  - 后续生成 HTML 演示页优先使用这个文件。

- `docs/price-approval-and-publishing.md`
  - 价格审批与发布使用手册。

- `docs/i18n-dashboard.md`
  - 多语言界面、销售看板、回测、审批发布和部署更新说明。

- `docs/deployment.md`
  - VPS、systemd、Caddy、HTTPS 部署说明。

- `docs/mvp-implementation.md`
  - MVP 实现说明。

- `docs/kaggle-adapter.md`
  - Kaggle Hotel Booking Demand 数据转换说明。

- `docs/roadmap.md`
  - 阶段路线图和下一步优先级。

- `docs/open-questions.md`
  - 待确认问题。

### `scripts/`

- `scripts/create_demo_data.py`
  - 将外部数据或 Kaggle 数据转换为 MVP 所需 CSV 格式。

### `sample_data/`

- `sample_data/bookings.csv`
  - 演示订单数据。

- `sample_data/inventory.csv`
  - 演示库存数据。

- `sample_data/current_prices.csv`
  - 演示当前价格数据。

### `data/`

- `data/raw/`
  - 原始外部数据目录，通常不提交 Git。

- `data/processed/`
  - 处理中间数据目录，通常不提交 Git。

- `data/audit_logs/`
  - 审批和推送日志目录，生成的 CSV 不提交 Git。

## 建议仓库约定

- 需求和业务定义放在 `docs/`。
- 数据口径变更必须同步更新 `docs/data-requirements.md`。
- 建模假设变更必须同步更新 `docs/modeling-approach.md` 或 `docs/revenue-optimization-model.md`。
- OTA 渠道折扣、佣金、价格发布频率相关设计同步更新 `docs/ota-channel-pricing-notes.md`。
- 演示文稿文案同步更新 `docs/demo-presentation-script.md`。
- 重大产品边界变化记录到 `docs/open-questions.md` 或后续决策文档。

## 验证标准

当前 MVP 的完成标准是：

- 项目目标、用户、输入、输出和非目标清晰。
- MVP 的验收标准可以被逐项检查。
- 数据字段有定义、有来源、有质量要求。
- 建模路线能解释为什么不是简单预测房价。
- 回测页面可以解释推荐价形成逻辑。
- 价格审批与发布过程有日志可查。
- 演示文稿可以用 `docs/demo-presentation-script.md` 直接生成。
