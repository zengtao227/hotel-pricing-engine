# OTA 渠道价格、折扣和更新频率说明

本文档用于记录 Booking.com、携程 / Trip.com、Expedia、Agoda 等卖房网站相关的价格策略假设。当前阶段用于产品设计和演示，不等同于任何具体酒店与 OTA 的正式合同条款。

## 1. 折扣和佣金要分开理解

酒店在 OTA 上看到的“折扣”通常不是一个单一概念，而是几种价格机制叠加：

| 机制 | 谁决定 | 对酒店收益的影响 |
|---|---|---|
| 平台佣金 | OTA 与酒店合同约定 | 酒店到手收入减少，但展示价不一定变化 |
| 会员折扣 | OTA 会员体系或酒店参加的会员计划 | 客人看到的价格降低 |
| 促销折扣 | 酒店或平台活动规则 | 客人看到的价格降低，可能换取曝光和转化 |
| 移动端折扣 | App 专属价或移动端促销 | 移动端展示价降低 |
| 套餐 / 打包价 | 酒店 + 机票 / 其他产品组合 | 对客价格可能被隐藏或打包展示 |
| 企业协议价 | 酒店与公司客户签订 | 与公开 OTA 价格不同 |

因此，模型里应区分：

```text
Approved Base Price = 酒店内部批准的基准挂牌价
Display Price = 渠道对客展示价
Net Revenue = 扣除佣金、折扣和渠道成本后的酒店净收入
```

## 2. 公开资料能确认的大致折扣区间

不同 OTA、国家、城市、酒店规模和合同不同，真实佣金和折扣需要以酒店后台合同为准。公开资料能支持的只是“设计假设”。

### Booking.com

- Genius / 会员折扣常见公开口径为 10% / 15% / 20% 三档。
- 其他促销活动可能要求 15% 或更高折扣。
- Preferred / Preferred Plus 等曝光项目可能涉及更高佣金或更高商业贡献。
- 瑞士监管机构曾认为 Booking.com 向瑞士酒店收取的佣金过高，并要求降低近四分之一；Booking.com 表示会申诉。

### Expedia / Hotels.com

- Expedia Group 有 One Key 会员体系，Hotels.com 等品牌有会员价和奖励体系。
- 具体酒店参加的会员折扣、促销价和佣金需要看 Partner Central 或合同。

### 携程 / Trip.com、飞猪、美团、Agoda

- 具体佣金、折扣和活动规则高度依赖地区、酒店合同、活动报名和渠道政策。
- 不能在产品里硬编码固定折扣。
- 更适合做成可配置的 `Channel Pricing Rules`。

## 3. 产品设计建议

第一阶段不要让模型直接推荐每个 OTA 的最终展示价，而是推荐酒店内部审批的基准挂牌价。

然后通过渠道价格策略层转换：

```text
Approved Base Price
        ↓
Channel Pricing Rules
        ↓
Booking.com Display Price / Ctrip Display Price / Direct Website Price
        ↓
Net Revenue After Commission
```

示例：

| 渠道 | 规则 | 展示价 | 净收益计算 |
|---|---|---:|---|
| 官网直销 | 无折扣 | 468 | 468 |
| 官网会员 | 95 折 | 445 | 445 |
| 携程促销 | 92 折 | 431 | 431 - 渠道成本 |
| Booking.com Genius | 90 折 | 421 | 421 - 佣金 |
| Booking.com 普通价 | 无会员折扣 | 468 | 468 - 佣金 |

## 4. 价格可以多频繁更新？

技术上，现代 OTA 和 Channel Manager 都支持频繁更新未来日期的价格与库存。Booking.com 官方开发者文档中有 `Rates & Availability API`、`Promotions API` 等接口类别，说明平台本身支持通过连接系统管理价格、库存和促销。

产品上应按三个阶段设计：

### 阶段 1：每日生成建议，人工审批后发布

推荐节奏：每天一次。

```text
每天早上系统生成未来 30 / 60 天价格建议
收益经理审核
导出 CSV 或模拟发布
```

这是当前 MVP 最适合的演示和试用节奏。

### 阶段 2：高需求日期更高频监控

对于节假日、会展、演唱会、周末和库存紧张日期，可以每天多次检查 pickup 和剩余库存。

```text
普通日期：每日 1 次
重点日期：每日 2-4 次检查
临近入住且库存异常：触发提醒
```

### 阶段 3：自动化发布，但保留限制和审计

只有在有足够回测、权限、日志、回滚和人工护栏后，才考虑半自动发布。

建议限制：

- 每个房型 / 入住日期一天最多自动改价 1-2 次
- 单次最大涨跌幅受控
- 低置信度建议必须人工审批
- 已推送价格保留审计日志
- 可回滚到上一次批准价

## 5. 对本项目的意义

如果未来可以每天自动读取订单 pickup 和库存，并每天更新未来日期的推荐价，那么项目价值会明显提高。

原因是：

```text
越接近入住日，已售房数、剩余库存和 pickup 都会变化；
同一个入住日期的最佳价格不是固定的；
每天重新计算未来价格，可以让酒店更及时地捕捉涨价机会或降价清库存机会。
```

这也是本项目从“静态报表”变成“收益管理助手”的关键。

## 6. 后续功能建议

建议新增一个 `Channel Pricing Rules` 模块，字段包括：

```text
channel_name
base_price_source
commission_rate
discount_rate
member_discount_rate
promotion_discount_rate
mobile_discount_rate
min_display_price
max_display_price
rounding_strategy
net_revenue_formula
update_frequency
requires_manual_approval
```

后续可以在“价格审批与发布”页面中增加：

- 下载渠道价 CSV
- Booking.com 价
- 携程价
- 官网会员价
- 渠道净收益估算
- 每个渠道的推送状态

## 7. 公开资料来源

- Booking.com Connectivity Developer Docs: Rates & Availability API, Promotions API, API reference.
- Reuters, 2025-05-21: Swiss price watchdog ordered Booking.com to lower commission rates for Swiss hotels by almost a quarter, while Booking.com planned to appeal.
- Wired / Condé Nast Traveler public summaries of Booking.com Genius member discounts: commonly described as 10% / 15% / 20% tiers.
- Expedia Group public information on One Key loyalty programme and Hotels.com member-only discounts.
