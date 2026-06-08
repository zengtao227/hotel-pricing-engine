# 数据需求

## 1. 数据原则

动态定价依赖历史订单、价格、库存和日历信息。MVP 不要求一开始接入所有外部数据，但必须保证核心字段口径清晰，否则模型会把业务噪声当成规律。

## 2. 最小数据集

### 2.1 历史订单表

每一行代表一个订单或一个订单房晚明细。

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `booking_id` | string | 订单唯一标识 |
| `hotel_id` | string | 酒店标识，单酒店 MVP 可固定为一个值 |
| `room_type` | string | 房型 |
| `booking_date` | date | 预订日期 |
| `check_in_date` | date | 入住日期 |
| `check_out_date` | date | 离店日期 |
| `nights` | integer | 入住晚数 |
| `rooms` | integer | 房间数 |
| `gross_room_revenue` | number | 房费总收入 |
| `net_room_revenue` | number | 扣除取消或退款后的房费收入 |
| `daily_rate` | number | 每间夜成交价 |
| `channel` | string | 预订渠道 |
| `status` | string | confirmed、cancelled、no_show、stayed |
| `cancelled_at` | date | 取消日期，可为空 |

### 2.2 库存表

每一行代表某酒店、某房型、某入住日期的可售库存。

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `hotel_id` | string | 酒店标识 |
| `room_type` | string | 房型 |
| `stay_date` | date | 入住日期 |
| `available_rooms` | integer | 可售房间数 |
| `out_of_order_rooms` | integer | 维修或不可售房间数 |

### 2.3 价格快照表

每一行代表某个观察时间点看到的价格。

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `hotel_id` | string | 酒店标识 |
| `room_type` | string | 房型 |
| `stay_date` | date | 入住日期 |
| `observed_at` | datetime | 价格被记录的时间 |
| `listed_price` | number | 当时挂牌价 |
| `channel` | string | 渠道 |
| `rate_plan` | string | 价格计划，可为空 |

### 2.4 日历特征表

每一行代表一个日期。

建议字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `date` | date | 日期 |
| `day_of_week` | integer | 星期几 |
| `is_weekend` | boolean | 是否周末 |
| `is_holiday` | boolean | 是否节假日 |
| `holiday_name` | string | 节假日名称，可为空 |
| `season` | string | 淡季、平季、旺季等 |
| `local_event_score` | number | 当地活动强度，MVP 可为空 |

## 3. 派生字段

建模时建议生成以下派生字段：

- `lead_time_days`: 入住日期减预订日期
- `stay_month`: 入住月份
- `stay_day_of_week`: 入住日期星期几
- `booking_day_of_week`: 预订日期星期几
- `length_of_stay`: 入住晚数
- `pickup_7d`: 过去 7 天新增预订量
- `pickup_14d`: 过去 14 天新增预订量
- `remaining_inventory`: 剩余可售库存
- `pace_ratio`: 当前预订进度与历史同期对比

## 4. 数据质量要求

必须检查：

- `check_out_date` 晚于 `check_in_date`
- `booking_date` 不晚于 `check_in_date`
- `daily_rate` 大于 0
- `rooms` 和 `nights` 大于 0
- 同一房型命名保持一致
- 取消订单不应计入最终入住间夜，但可用于取消率建模
- 库存不能为负数
- 历史价格快照的观察时间不能晚于对应入住日期太久

## 5. 数据粒度选择

MVP 推荐使用“每日 + 房型”粒度：

```text
hotel_id + room_type + stay_date
```

这个粒度足够支持第一版定价建议，同时避免一开始陷入订单级、渠道级和价格计划级的复杂度。

## 6. 外部数据扩展

后续可加入：

- 竞品酒店价格
- 当地大型活动
- 天气
- 航班或交通热度
- 搜索热度
- OTA 排名或曝光数据

这些数据可以提升模型效果，但不是 MVP 的前置条件。
