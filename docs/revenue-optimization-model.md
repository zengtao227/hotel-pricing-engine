# 收益最大化定价模型

本文档解释系统为什么不是“预测一个房价”，而是用收益管理模型计算更可能带来最大收益的推荐价。

当前代码实现的是 **v1 可解释候选价收益模拟模型**。它不是黑盒机器学习模型，而是一个透明、可审计、可逐步升级的数学优化框架：

```text
需求预测 -> 价格弹性 -> 候选价收益模拟 -> 约束下选择预期收益最高价格
```

## 1. 业务问题的数学形式

酒店房间是典型的易逝库存：某个入住日期过去后，没卖出去的间夜不能再售卖。因此每个 `入住日期 x 房型` 都可以看成一个有限库存收益最大化问题。

对某个入住日期和房型，定义：

| 符号 | 含义 |
|---|---|
| `p0` | 当前价 |
| `p` | 候选推荐价 |
| `N` | 可售库存 |
| `S0` | 观察日已经售出的间夜 |
| `R0` | 观察日已经锁定的房费收入 |
| `C = max(N - S0, 0)` | 剩余可售库存 |
| `D0` | 当前价不变时的最终需求预测 |
| `epsilon` | 价格弹性，通常为负数 |

系统的目标不是最大化房价，也不是最大化入住率，而是最大化预期房费收入：

```text
p* = argmax ExpectedRevenue(p)
```

## 2. 已知订单和未来需求分开处理

已经成交的订单不应该因为今天改价而消失，所以模型把收入拆成两部分：

```text
总预期收益 = 已锁定订单收入 + 未来新增订单预期收入
```

也就是：

```text
ExpectedRevenue(p) = R0 + p * ExpectedNewSoldRooms(p)
```

其中 `R0` 是观察日已经知道的订单收入，只有未来尚未成交的需求会受到候选价 `p` 影响。这个设计可以避免一个常见错误：把已经售出的房间也当成会随价格变化而重新成交。

## 3. 当前价下的需求预测

v1 用两个信号估计当前价不变时的最终需求 `D0`：

1. 历史类似日期的基准入住率
2. 当前预订进度和最近 14 天 `Pickup`

公式如下：

```text
HistoricalDemand = baseline_occupancy * N
PaceProjection = S0 + pickup_14d * lead_time_factor
D0 = clip(
    w * PaceProjection + (1 - w) * HistoricalDemand,
    lower = S0,
    upper = N
)
```

其中：

- 离入住日期越近，`w` 越高，因为当前预订进度更可信。
- 离入住日期越远，历史基准占比更高，因为未来还有较长销售窗口。
- `clip` 保证预测需求不会低于已售间夜，也不会超过可售库存。

## 4. 价格弹性模型

价格弹性描述“价格变化 1% 时，需求大约变化多少百分比”。经济学中常用定义是：

```text
price_elasticity = % change in quantity demanded / % change in price
```

酒店定价里弹性通常为负数。例如 `epsilon = -1.2` 表示价格提高 1%，未来未成交需求大约下降 1.2%。

v1 使用常数弹性需求函数：

```text
FutureDemand(p) = max(D0 - S0, 0) * (p / p0) ^ epsilon
```

最终预计售出间夜为：

```text
ExpectedSoldRooms(p) = S0 + min(C, FutureDemand(p))
```

于是候选价 `p` 的预期收益为：

```text
ExpectedRevenue(p) = R0 + p * min(C, max(D0 - S0, 0) * (p / p0) ^ epsilon)
```

### 弹性如何估计

当前阶段没有足够真实实验数据，所以系统先采用透明规则估计弹性：

- 默认弹性：`-1.25`
- 周末、入住率高、剩余库存少、近期 pickup 强时，需求更刚性，弹性绝对值降低
- 入住率低、临近入住但剩余库存高、近期 pickup 弱时，需求更敏感，弹性绝对值提高
- 最终限制在 `[-2.20, -0.60]`，避免模型给出极端反应

这不是最终的机器学习模型，而是可解释的 v1 基线。它的价值是：每一个推荐价都能说明“为什么涨价或降价会影响收益”。

## 5. 候选价集合和约束优化

真实酒店价格不是任意连续数字，必须满足业务约束：

- 单次最大调价幅度
- 房型最低价和最高价
- 市场友好的尾数规则，例如中国酒店常用 6/8/9 尾数
- 人工审批前不自动写价
- 小幅收益提升不足以覆盖运营摩擦时保持当前价

所以系统不直接求连续闭式解，而是生成一组可执行候选价：

```text
CandidatePrices = rounded prices within:
[
    p0 * (1 - max_change_pct),
    p0 * (1 + max_change_pct)
]
and price_floor <= p <= price_ceiling
```

然后枚举每个候选价：

```text
for p in CandidatePrices:
    revenue[p] = ExpectedRevenue(p)

p* = price with max revenue[p]
```

如果最佳候选价相对当前价的收益提升低于 `0.5%`，系统会建议 `hold`，避免频繁微调价格。

这种离散优化方式更适合早期产品，因为它和酒店真实操作一致：收益经理最终关心的是“今天可不可以从 388 调到 428”，而不是一个无法上架的理论价格 `421.37`。

## 6. 推荐输出如何解释

每条推荐现在会输出：

- `current_expected_revenue`: 当前价下的预期收益
- `recommended_expected_revenue`: 推荐价下的预期收益
- `expected_revenue_delta`: 两者差值
- `demand_forecast_at_current_price`: 当前价不变时的最终需求预测
- `expected_sold_rooms`: 推荐价下预计最终售出间夜
- `expected_new_sold_rooms`: 推荐价下预计新增成交间夜
- `demand_elasticity`: 本条建议使用的价格弹性
- `candidate_price_count`: 实际比较过的候选价数量

客户可以用这些字段追问模型：

```text
为什么建议涨价？
因为当前 pickup 强、剩余库存低，模型判断需求更刚性。
在当前价 388 下，预期收益是 X；
在候选价 428 下，虽然预计成交间夜略低，但单间收入提升后，总预期收益更高。
```

这比只说“系统建议上调 10%”更可信，也更容易被收益经理复核。

## 7. 当前回测如何使用收益模拟

当前 Backtest 页面已经升级为双口径：

1. 价格弹性收益回测：使用历史观察日以前已知订单生成推荐，并汇总当时模型估计的当前价预期收益、推荐价预期收益和预期收益变化。
2. 静态实际销量对照：用最终真实售出间夜做保守 sanity check，观察如果销量不变，推荐价相对当前价的收入差。

静态对照口径为：

```text
基准收入 = 当前价 * 最终实际售出房间数
推荐价静态收入 = 推荐价 * 最终实际售出房间数
```

它适合检查推荐方向和数据泄漏问题，但它假设销量不随价格变化，所以不能严格证明收益最大化。

价格弹性收益回测使用的是动态收益模拟：

```text
推荐价改变 -> 未来需求改变 -> 预计售出间夜改变 -> 预期收益改变
```

页面还会展示一条样本的候选价收益曲线，帮助客户看到“为什么推荐价是这一组候选价中的收益最高点”。这仍然是模型预期值，不是已经证明的真实因果收益；真实客户数据积累后，应继续做更严格的 holdout 回测、审批后表现追踪和实验验证。

## 8. 生产级模型升级路线

v1 模型适合演示和早期人工复核。真实客户数据积累后，可以升级为更强的统计模型。

### 8.1 需求到达模型

可以把未来新增预订视为随机变量：

```text
Y(p) ~ Poisson(lambda(p))
```

其中：

```text
lambda(p) = exp(beta0 + beta_x * features + beta_p * log(p))
```

`features` 可以包括星期、月份、节假日、提前期、渠道、房型、竞品价格、活动日和历史 pickup。

### 8.2 成交概率模型

如果有曝光、询价或搜索数据，可以建成交概率：

```text
Pr(book | p, x) = sigmoid(beta0 + beta_x * x + beta_p * log(p))
```

再计算：

```text
ExpectedBookings(p) = traffic_forecast * Pr(book | p, x)
```

### 8.3 有限库存截断

因为最多只能卖 `C` 间夜，所以生产模型应计算：

```text
ExpectedNewSoldRooms(p) = E[min(Y(p), C)]
```

这比简单 `min(E[Y], C)` 更严谨，尤其适合高需求日期。

### 8.4 分层价格弹性

当真实数据足够后，弹性不应只有一个全局值，而应按层级估计：

```text
epsilon = global + room_type_effect + day_of_week_effect + season_effect + lead_time_effect + channel_effect
```

这样可以让标准间、套房、周末、淡季、临近入住等场景拥有不同的价格敏感度。

## 9. 科学依据

本方案参考了收益管理和价格弹性两个成熟方向：

- Gallego and van Ryzin, 1994, [*Optimal Dynamic Pricing of Inventories with Stochastic Demand over Finite Horizons*](https://pubsonline.informs.org/doi/10.1287/mnsc.40.8.999). 该论文讨论了有限库存、有限销售周期、随机且价格敏感需求下的动态定价问题，并明确提到酒店房间这类到期后失去价值的库存。
- OpenStax, *Principles of Economics 3e*, [“Price Elasticity of Demand and Price Elasticity of Supply”](https://openstax.org/books/principles-economics-3e/pages/5-1-price-elasticity-of-demand-and-price-elasticity-of-supply). 该教材给出价格弹性的标准定义，即需求量变化百分比与价格变化百分比之比。

v1 的重点不是宣称已经得到完美最优解，而是把推荐价从“经验规则”提升为“可解释的约束收益优化”。这为后续接入真实 PMS / Channel Manager 数据、学习真实价格弹性、做收益回测和自动化审批打下基础。

## 10. 当前实现文件

- `src/revenue_simulation.py`: 候选价收益模拟和价格弹性估计
- `src/pricing_engine.py`: 调用收益模拟并生成推荐价、解释、风险提示和收益字段
- `src/i18n.py`: 推荐结果字段的多语言标签
- `src/ui_help.py`: 页面中的指标解释和字段提示
