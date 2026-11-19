# P0 设计文档：淡旺季日历 + Pickup 速度基准

**日期**: 2026-06-24  
**状态**: 已批准，待实施

## 背景

与酒店销售经理沟通后确认，当前定价模型只考虑房态和提前期，缺少两个关键需求信号：
1. 淡旺季对需求基线的影响
2. 当前预订速度是否高于/低于历史同期

## P0.1 淡旺季日历

### 数据结构

在 `hotel_config` 的 JSON 里新增顶层字段 `seasons`：

```json
"seasons": [
  {"name": "春节黄金周", "start": "2026-01-25", "end": "2026-02-08", "demand_multiplier": 1.8},
  {"name": "国庆黄金周", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0},
  {"name": "暑期旺季",   "start": "2026-07-01", "end": "2026-08-31", "demand_multiplier": 1.3},
  {"name": "11月淡季",   "start": "2026-11-01", "end": "2026-11-30", "demand_multiplier": 0.7}
]
```

字段约束：
- `name`: 非空字符串，最长 40 字符
- `start` / `end`: ISO 日期字符串，start ≤ end
- `demand_multiplier`: 0.1 ～ 5.0 的正数
- 日期段允许重叠，多个匹配时取最高 multiplier（旺季优先原则）
- 最多 50 条

### 作用点

`pricing_engine.py` 的推荐循环里：

```python
season_multiplier = _get_season_multiplier(stay_date, seasons)
adjusted_baseline_occupancy = baseline_occupancy * season_multiplier
```

`adjusted_baseline_occupancy` 替代原来的 `baseline_occupancy` 传入 `simulate_revenue_maximizing_price()`。

如果 season_multiplier ≠ 1.0，在 `reasons` 里加入 season name（如"春节黄金周需求旺季"或"11月淡季"）。

### UI

酒店配置页新增"季节日历"区块（expander），可增删行，每行：名称、开始日期、结束日期、需求倍率。

---

## P0.2 Pickup 速度基准

### 计算方式

在 `pricing_engine.py` 的历史 baselines groupby 里新增 `baseline_pickup_14d`（历史同类日期中位 pickup_14d）：

```python
baselines = historical.groupby(["hotel_id", "room_type", "is_weekend"], as_index=False).agg(
    baseline_occupancy=("occupancy", "median"),
    baseline_pickup_14d=("pickup_14d", "median"),   # 新增
    ...
)
```

注意：`pickup_14d` 在历史数据中需要和 metrics 一同保留，或从 bookings 中重算。

### Velocity Ratio 逻辑

```python
pickup_velocity_ratio = pickup_14d / baseline_pickup_14d  # baseline > 0 时
```

打分规则：
- ratio > 1.3 → score +1，reason: "近期预订速度高于历史同期"
- ratio < 0.7 → score -1，reason: "近期预订速度低于历史同期"

elasticity 微调（替代原有基于绝对值的条件）：
- `days_to_arrival <= 14 and pickup >= 4` → 改为 `days_to_arrival <= 14 and pickup_velocity_ratio >= 1.3`
- `days_to_arrival <= 14 and pickup <= 1` → 改为 `days_to_arrival <= 14 and pickup_velocity_ratio <= 0.5`
- 原有绝对值条件保留作为 fallback（baseline_pickup_14d 为零或缺失时）

---

## 改动文件清单

| 文件 | 改动 |
|------|------|
| `src/hotel_config.py` | 新增 `seasons` 字段：校验、`normalize_hotel_config`、`default_hotel_config`、UI 渲染 |
| `src/pricing_engine.py` | `_get_season_multiplier()` 函数；baselines 加 `baseline_pickup_14d`；velocity ratio 逻辑 |
| `src/i18n.py` | 季节推荐原因、velocity 原因的中英德法文案 |

**不改动** `revenue_simulation.py`——其接口不变，只是输入的 `baseline_occupancy` 改变了。

---

## 不在本次范围内

- per-room-type 季节系数（留待后续真实数据验证后按需添加）
- 竞品价格（P1，手动录入方案后续单独设计）
- OTA 流量信号（需平台授权，暂缓）
