---
project: hotel-pricing-engine
status: mvp-running
owner: zengtao227
language: zh-CN
primary_goal: 酒店房间动态定价与收益优化
created_at: 2026-06-08
updated_at: 2026-06-10
---

# Project Context

`hotel-pricing-engine` 是一个酒店动态定价与收益优化项目。当前阶段已经是可运行的 Streamlit MVP，支持销售演示、候选价收益模拟、价格弹性回测、价格审批与发布模拟。它仍然不是成熟商用软件，真实客户试用前需要继续加强数据导入、数据质量报告、访问保护、审计存储、渠道价规则和自动监控任务。

## 术语

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
- `RevPAR`: Revenue Per Available Room，每间可售房平均收入，房费收入 / 可售间夜数
- `Pickup`: 某一观察窗口内新增预订量
- `取消率`: 已确认订单后续取消的比例
- `推荐价`: 系统建议人工审核的价格
- `候选价`: 系统在约束范围内枚举比较的一组可执行价格
- `价格弹性`: 价格变化时未来未成交需求变化的估计
- `自动检查`: 定时或事件触发读取新订单、库存和价格状态
- `自动计算`: 数据变化后自动重新运行推荐模型
- `自动发布`: 满足低风险护栏后把价格写入渠道或导出发布文件

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
- 多语言销售看板
- 酒店配置：房型、基准价、最低价、最高价、周末加价
- 价格审批与发布模拟
- 审批和推送日志 CSV 持久化
- 多语言 Excel 导出
- Channel Pricing Rules 初始设计和计算模块
- 自动价格监控设计文档

## 当前目标

建立清晰的数据口径、建模路线、渠道价规则和自动监控路线，再逐步进入真实数据试用。当前推荐形态应是：

```text
自动检查 -> 自动计算 -> 人工审批 / 低风险自动发布候选 -> 审计日志
```

第一阶段仍默认人工确认调价，避免自动写价带来的业务风险；但系统应朝自动监控和自动重新计算方向设计。

## 产品原则

- 收益优化优先于单纯房价预测。
- 推荐结果必须能解释原因，不能只给一个数字。
- 先做可验证的简单模型，再逐步增加复杂度。
- 初期默认人工确认调价，避免自动化带来的业务风险。
- 每个价格建议都要带上数据依据、置信度和异常提醒。
- 当前模型输出的是“预期收益最高的候选价”，不是保证真实世界最高收益。
- 当前推荐价默认是酒店内部审批用的基准挂牌价；真实发布到 OTA 时，还需要渠道折扣、佣金和促销规则。
- 自动化要拆成自动检查、自动计算、自动发布三个层级，不能一开始无护栏全自动写价。
- 渠道折扣和佣金必须配置化，不能硬编码某个平台固定折扣。

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

### 讲 OTA 渠道折扣、渠道价和自动化频率时使用

- `docs/ota-channel-pricing-notes.md`
  - 说明挂牌价、渠道展示价、渠道净收益、OTA 佣金 / 折扣、价格更新频率。

- `docs/channel-pricing-rules.md`
  - Channel Pricing Rules 的字段、计算公式、示例和 UI 设计。

- `docs/automated-pricing-monitoring.md`
  - 说明为什么要自动化、自动检查 / 自动计算 / 自动发布三层设计、调价频率和自动发布护栏。

- `src/channel_pricing_rules.py`
  - Channel Pricing Rules 的第一版计算模块。

## 项目文件夹结构说明

### 根目录

- `README.md`
  - 项目介绍、当前能力、快速启动、问题定义、MVP 范围和文档索引。

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

- `src/channel_pricing_rules.py`
  - 渠道价格规则。
  - 把内部批准基准价转换为不同渠道展示价，并估算佣金和渠道净收益。

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
  - 当前保存到 `data/audit_logs/price_approval_publishing_log.sqlite`（SQLite，原子写；清空操作为软删除归档，不会删除文件；旧 CSV 首次加载时自动迁移）。

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
  - 建模路线。
  - 作为长期模型演进和建模假设的入口，详细数学模型以 `docs/revenue-optimization-model.md` 为准。

- `docs/revenue-optimization-model.md`
  - 当前最重要的模型说明文档。
  - 解释收益最大化、剩余库存定价、价格弹性、候选价收益模拟、回测和渠道价。

- `docs/ota-channel-pricing-notes.md`
  - OTA 渠道价格、折扣、佣金和更新频率说明。

- `docs/channel-pricing-rules.md`
  - Channel Pricing Rules 的字段、公式、示例、自动发布关系和 UI 设计。

- `docs/automated-pricing-monitoring.md`
  - 自动价格监控、自动计算、自动发布护栏和任务调度设计。

- `docs/demo-presentation-script.md`
  - 演示文稿文稿。
  - 后续生成 HTML 演示页优先使用这个文件。

- `docs/price-approval-and-publishing.md`
  - 价格审批与发布使用手册。

- `docs/i18n-dashboard.md`
  - 多语言界面、销售看板、回测、审批发布和部署更新说明。

- `docs/deployment.md`
  - VPS、systemd、Caddy、HTTPS 部署说明。


- `docs/roadmap.md`
  - 阶段路线图和下一步优先级。

- `docs/open-questions.md`
  - 待确认问题和后续决策记录入口。

- `docs/hotel-configuration.md`
  - 酒店配置功能说明。

- `docs/marketing-and-product-roadmap.md`
  - 商业化、客户定位和长期产品路线思考。

### `scripts/`

- `scripts/create_demo_data.py`
  - 将外部数据或 Kaggle 数据转换为 MVP 所需 CSV 格式。


### `Presentation/`

- `Presentation/index.html`
  - 落地页，链接决策版和培训版。

- `Presentation/decision/index.html`
  - 决策版演示文稿（Reveal.js，15 张），面向酒店老板 / 管理层。

- `Presentation/training/index.html`
  - 培训版演示文稿（Reveal.js，30 张），面向员工 / 操作人员。

- `Presentation/assets/`
  - 共享截图素材（PNG），供两个版本共用，已加入 `.gitignore` 不提交 Git。

### `data/`

- `data/raw/`
  - 原始外部数据目录，通常不提交 Git。

- `data/processed/`
  - 处理中间数据目录，通常不提交 Git。

- `data/audit_logs/`
  - 审批和推送日志目录，生成的 CSV 不提交 Git。

## 清理决定

- `docs/mvp-implementation.md` 已过时，内容被 `README.md`、`CONTEXT.md`、`docs/i18n-dashboard.md`、`docs/revenue-optimization-model.md` 覆盖，已经删除。
- `docs/modeling-approach.md` 保留为建模路线入口，但不再承载最完整数学说明。
- `docs/marketing-and-product-roadmap.md` 保留为商业化和产品路线思考，不与技术 Roadmap 合并。

## 建议仓库约定

- 需求和业务定义放在 `docs/`。
- 数据口径变更必须同步更新 `docs/data-requirements.md`。
- 建模假设变更必须同步更新 `docs/modeling-approach.md` 或 `docs/revenue-optimization-model.md`。
- OTA 渠道折扣、佣金、价格发布频率相关设计同步更新 `docs/ota-channel-pricing-notes.md`。
- Channel Pricing Rules 字段或计算逻辑变化同步更新 `docs/channel-pricing-rules.md` 和 `src/channel_pricing_rules.py`。
- 自动价格监控、自动计算、自动发布护栏同步更新 `docs/automated-pricing-monitoring.md`。
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
- 渠道价规则能说明基准挂牌价如何转换为 OTA / 官网展示价和净收益。
- 演示文稿可以用 `docs/demo-presentation-script.md` 直接生成。

## 演示文稿部署（2026-06-10）

演示文稿以静态文件形式挂载在 `hotel.zengsg.dpdns.org/deck/` 路径下，由 Caddy 对外提供 HTTPS 访问，无需独立子域名。

### 目录结构

```
Presentation/
├── assets/          ← 共享截图（01-04，供两个版本共用，不提交 Git）
├── decision/
│   └── index.html   ← 决策版（15 张，Reveal.js）
├── training/
│   └── index.html   ← 培训版（30 张，Reveal.js）
└── index.html       ← 落地页，链接两个版本
```

### 访问地址

- 落地页：`https://hotel.zengsg.dpdns.org/deck/`
- 决策版：`https://hotel.zengsg.dpdns.org/deck/decision/index.html`
- 培训版：`https://hotel.zengsg.dpdns.org/deck/training/index.html`

### 版本说明

- **决策版**：面向酒店老板 / 管理层，促成试点合作决策，15 张
- **培训版**：面向员工 / 操作人员，讲解系统使用方法，30 张

### 截图素材

截图统一放在 `Presentation/assets/`，已加入 `.gitignore`，不随 GitHub 推送。直接在 VPS 对应 index.html 编辑演示文稿即可。

### Caddy 配置

挂载在已有的 `hotel.zengsg.dpdns.org` 块内，无需额外子域名或 DNS 记录：

```caddyfile
hotel.zengsg.dpdns.org {
    handle_path /deck/* {
        root * /data/projects/hotel-pricing-engine/Presentation
        file_server
        encode gzip
    }
    reverse_proxy localhost:8501
}
```

**SELinux 注意**：`Presentation/` 目录已通过 `semanage fcontext` 设置为 `httpd_sys_content_t`，
允许 Caddy（`httpd_t` 上下文）读取。若新增文件后出现 403，运行：

```bash
sudo restorecon -Rv /data/projects/hotel-pricing-engine/Presentation
```
