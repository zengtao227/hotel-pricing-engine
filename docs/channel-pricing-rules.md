# Channel Pricing Rules 设计

本文档定义如何把系统推荐并审批通过的“基准挂牌价”转换成各个渠道的展示价和净收益估算。

## 1. 为什么需要 Channel Pricing Rules

当前收益模型推荐的是酒店内部审批用的基准挂牌价，例如：

```text
Standard Double, 2026-07-15, Approved Base Price = 468
```

但真实发布时，不同渠道可能有不同规则：

- 官网直销无佣金
- 官网会员价有会员折扣
- Booking.com 可能有 Genius / 会员折扣和佣金
- 携程可能有促销折扣或活动价
- 企业协议价可能是固定合同价

如果不考虑渠道规则，只看基准价，可能会高估某些渠道的实际收益。

所以系统需要一层转换：

```text
Approved Base Price
        ↓
Channel Pricing Rules
        ↓
Channel Display Price
        ↓
Estimated Net Revenue
```

## 2. 第一版规则字段

第一版规则应包含以下字段：

| 字段 | 含义 | 示例 |
|---|---|---|
| `channel_name` | 渠道名称 | Booking.com Genius |
| `rate_plan_code` | 价格计划代码 | BAR / MEMBER / PROMO |
| `commission_rate` | 渠道佣金率 | 0.15 |
| `discount_rate` | 普通渠道折扣 | 0.00 |
| `member_discount_rate` | 会员折扣 | 0.10 |
| `promotion_discount_rate` | 促销折扣 | 0.08 |
| `mobile_discount_rate` | 移动端折扣 | 0.05 |
| `channel_cost_fixed` | 固定渠道成本 | 0 |
| `min_display_price` | 渠道最低展示价 | 328 |
| `max_display_price` | 渠道最高展示价 | 688 |
| `rounding_strategy` | 尾数规则 | chinese_lucky |
| `update_frequency` | 推荐检查频率 | daily / high_frequency |
| `requires_manual_approval` | 是否必须人工审批 | true |
| `enabled` | 是否启用该渠道规则 | true |

## 3. 折扣叠加方式

多个折扣不建议简单相加，而应使用乘法叠加。

例如：

```text
会员折扣 10%
移动端折扣 5%
```

如果简单相加就是 15%，但更合理的叠加方式是：

```text
combined_discount = 1 - (1 - 0.10) × (1 - 0.05)
                  = 14.5%
```

这样可以避免多个折扣叠加时过度降低价格。

## 4. 计算公式

对于某个渠道：

```text
raw_display_price = approved_base_price × (1 - combined_discount)
display_price = round_and_clip(raw_display_price)
commission_amount = display_price × commission_rate
estimated_net_revenue = display_price - commission_amount - channel_cost_fixed
```

其中 `round_and_clip` 会应用：

- 价格尾数规则
- 渠道最低展示价
- 渠道最高展示价

## 5. 示例

假设基准挂牌价为 468：

| 渠道 | 折扣 | 佣金 | 展示价 | 估算净收益 |
|---|---:|---:|---:|---:|
| 官网直销 | 0% | 0% | 468 | 468 |
| 官网会员 | 5% | 0% | 445 | 445 |
| 携程促销 | 8% | 0% | 431 | 431 |
| Booking.com Genius | 10% | 15% | 421 | 358 |

这说明：同一个基准价，在不同渠道上的净收益可能差异明显。

## 6. 与自动发布的关系

Channel Pricing Rules 不只是为了展示不同渠道价格，也会影响自动发布判断。

例如：

```text
基准价看起来合理，但 Booking Genius 折扣 + 佣金后净收益太低。
```

这种情况下，系统应提示人工审批，而不是自动发布。

建议自动发布前检查：

- 渠道展示价是否低于最低展示价
- 渠道净收益是否低于净收益底线
- 折扣叠加是否过高
- 是否触发渠道合同限制
- 是否需要人工审批

## 7. 当前代码实现

第一版代码已放在：

```text
src/channel_pricing_rules.py
```

核心对象：

```python
ChannelPricingRule
```

核心函数：

```python
apply_channel_rule(approved_base_price, rule)
generate_channel_prices(approved_prices, rules)
default_channel_pricing_rules()
```

## 8. 下一步 UI 设计

后续可以在 Streamlit 中新增一个标签页或放进“价格审批与发布”页：

```text
渠道价预览 / Channel Prices
```

功能：

1. 选择已批准价格。
2. 选择启用的渠道规则。
3. 显示每个渠道的展示价和估算净收益。
4. 标记净收益过低或需要人工审批的渠道。
5. 导出 Channel Manager CSV 模板。

## 9. 后续数据结构

未来可以把规则保存在：

```text
data/config/channel_pricing_rules.json
```

示例：

```json
[
  {
    "channel_name": "Booking.com Genius",
    "rate_plan_code": "GENIUS",
    "commission_rate": 0.15,
    "member_discount_rate": 0.10,
    "rounding_strategy": "chinese_lucky",
    "requires_manual_approval": true,
    "enabled": true
  }
]
```

## 10. 产品路线

建议实现顺序：

1. 规则计算模块：已开始。
2. 规则 JSON 导入 / 导出。
3. 审批页增加渠道价预览。
4. 渠道价 Excel / CSV 导出。
5. 自动发布护栏检查。
6. 接入具体 Channel Manager API。
