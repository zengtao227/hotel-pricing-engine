# 部署说明

## 当前运行环境

- **服务器**：Frankfurt VPS（89.168.80.38，Oracle Cloud ARM A1）
- **项目路径**：`/data/projects/hotel-pricing-engine`
- **访问地址**：`https://hotel.zengsg.dpdns.org`
- **运行方式**：systemd 服务 `hotel-pricing-engine.service`
- **认证**：当前未启用 HTTP Basic Auth

## systemd 服务

服务文件：`/etc/systemd/system/hotel-pricing-engine.service`

当前启动命令：

```bash
/usr/bin/python3 -m streamlit run app/streamlit_app.py \
  --server.port 8501 \
  --server.address 127.0.0.1 \
  --server.headless true
```

常用操作：

```bash
sudo systemctl status hotel-pricing-engine --no-pager
sudo systemctl restart hotel-pricing-engine
sudo journalctl -u hotel-pricing-engine -n 80 --no-pager
```

开机自启：

```bash
sudo systemctl enable hotel-pricing-engine
```

服务设置了 `Restart=always`，进程异常退出后会自动拉起。Streamlit 只监听 `127.0.0.1:8501`，不直接暴露公网。

## 域名与 DNS 配置

### 域名信息

| 项目 | 内容 |
|------|------|
| 主域名 | `zengsg.dpdns.org` |
| 注册商 | DigitalPlat FreeDomain |
| 有效期 | 2027 年 6 月 8 日 |
| DNS 托管 | Cloudflare |
| NS 记录 | andronicus.ns.cloudflare.com / gail.ns.cloudflare.com |

### 已规划子域名

在 Cloudflare DNS 面板添加 A 记录，指向 89.168.80.38：

| 子域名 | 用途 | 状态 |
|--------|------|------|
| `hotel.zengsg.dpdns.org` | 酒店定价 MVP | 已启用 |

> 其他项目子域名（如 `panel.zengsg.dpdns.org`、`audit.zengsg.dpdns.org`）可按需在 Cloudflare 添加，不需要重新注册域名。

### 在 Cloudflare 添加 A 记录步骤

1. 登录 Cloudflare → 选择 `zengsg.dpdns.org`
2. DNS → Records → Add record
3. Type: A，Name: `hotel`，IPv4: `89.168.80.38`，Proxy: 建议开启（橙色云朵）
4. 保存

## Caddy 配置

配置文件：`/etc/caddy/Caddyfile`

当前 hotel 条目：

```
hotel.zengsg.dpdns.org {
    reverse_proxy localhost:8501
}
```

更新 Caddyfile 域名后执行：
```bash
sudo systemctl reload caddy
```

如未来需要重新启用访问保护，优先评估完整认证方案；短期演示保护可使用 Caddy `basic_auth`，但密码本身不要写进文档或提交到 GitHub。

---

## 数据对接要求

> 每次接入一家新酒店，对方最常问的第一个问题是"需要提供什么数据"。本节是标准答案，可以直接发给酒店 IT 或管理层。

### 概述

系统需要三张表。酒店 PMS（物业管理系统，即前台每天用的订单和房间管理软件）通常都能导出这三张报表，格式为 Excel 或 CSV。

> **PMS** 指酒店用于管理订单、库存和价格的核心系统，常见软件包括西软、中软云、飞象科技（国内），以及 Cloudbeds、Opera Cloud、Mews（国际）。

---

### 表 1：订单表（bookings）

每条记录 = 一笔预订（或一个入住房型×晚数组合）。

| 字段名 | 类型 | 是否必填 | 含义 | PMS 常见对应字段名 |
|--------|------|----------|------|------------------|
| `booking_id` | 文本 | 是 | 订单唯一编号 | 订单号、ReservationID、FolioNo |
| `hotel_id` | 文本 | 是 | 酒店标识（单店可固定填写酒店缩写） | HotelCode、PropertyID |
| `room_type` | 文本 | 是 | 房型名称，须与库存表和价格表保持一致 | RoomType、RoomCategory、房型 |
| `booking_date` | 日期 | 是 | 预订创建日期（客人下单那天） | BookingDate、ReservationDate、创建时间 |
| `check_in_date` | 日期 | 是 | 入住日期 | ArrivalDate、CheckIn、到店日期 |
| `check_out_date` | 日期 | 是 | 退房日期 | DepartureDate、CheckOut、离店日期 |
| `nights` | 整数 | 是 | 住宿晚数（= 退房日期 - 入住日期） | Nights、LOS |
| `rooms` | 整数 | 是 | 本次预订间数 | Rooms、Units、间数 |
| `daily_rate` | 数字 | 是 | 每晚实收房价（税前，单间单晚） | RoomRate、ADR、日均价 |
| `gross_room_revenue` | 数字 | 是 | 订单总客房收入（= daily_rate × rooms × nights） | GrossRevenue、TotalRevenue |
| `net_room_revenue` | 数字 | 是 | 扣除取消损失后净收入（取消订单填 0） | NetRevenue |
| `channel` | 文本 | 是 | 预订来源渠道 | BookingChannel、Source、来源 |
| `status` | 文本 | 是 | 订单状态：`confirmed`（已确认）、`stayed`（已入住）、`cancelled`（已取消） | Status |
| `cancelled_at` | 日期 | 否 | 取消时间（未取消留空） | CancellationDate、取消时间 |

**日期格式**：统一使用 `YYYY-MM-DD`，例如 `2026-03-15`。

**渠道字段建议值**：`Direct`（官网/前台直订）、`Booking.com`、`携程`、`美团`、`Expedia`、`Corporate`（协议客户）。名字可以自定义，保持与酒店自身叫法一致即可。

---

### 表 2：库存表（inventory）

每条记录 = 某房型在某天的可售间数。每天每房型一行。

| 字段名 | 类型 | 是否必填 | 含义 | PMS 常见对应字段名 |
|--------|------|----------|------|------------------|
| `hotel_id` | 文本 | 是 | 酒店标识（与订单表保持一致） | HotelCode |
| `room_type` | 文本 | 是 | 房型名称（与订单表保持一致） | RoomType |
| `stay_date` | 日期 | 是 | 日期（每天一行） | Date、StayDate |
| `available_rooms` | 整数 | 是 | 该日期该房型可售总间数（含已售和未售） | AvailableRooms、Availability、总间数 |
| `out_of_order_rooms` | 整数 | 否 | 维修停售间数（没有可填 0） | OutOfOrder、OOO |

**建议导出范围**：过去 90 天 + 未来 60 天，以支持历史分析和未来推荐。

---

### 表 3：当前价格表（current_prices）

每条记录 = 某房型在某天的当前挂牌基准价。每天每房型一行。

| 字段名 | 类型 | 是否必填 | 含义 | PMS / Channel Manager 常见对应字段名 |
|--------|------|----------|------|--------------------------------------|
| `hotel_id` | 文本 | 是 | 酒店标识（与订单表保持一致） | HotelCode |
| `room_type` | 文本 | 是 | 房型名称（与订单表保持一致） | RoomType |
| `stay_date` | 日期 | 是 | 日期（每天一行） | Date、StayDate |
| `current_price` | 数字 | 是 | 当前内部审批挂牌价（税前，不是 OTA 展示价） | RackRate、ListedPrice、BaseRate、挂牌价 |

> **说明**：`current_price` 是酒店内部审批和管理用的基础价格，不是 OTA 平台（携程/Booking）最终展示给客人的折扣价。OTA 展示价由系统根据渠道折扣规则自动计算，不需要酒店额外提供。

**建议导出范围**：未来 60 天（今天到今天后 60 天）。

---

### 导出格式要求

| 项目 | 要求 |
|------|------|
| 文件格式 | CSV（UTF-8 编码）或 Excel（.xlsx） |
| 日期格式 | `YYYY-MM-DD`（如 `2026-03-15`） |
| 数字格式 | 纯数字，不含货币符号，不含千位分隔符（即 `388` 而非 `¥388` 或 `388.00元`） |
| 空值 | 非必填字段无值时留空，不填 `N/A`、`-`、`null` |
| 房型名称 | 三张表的房型名称必须完全一致（区分大小写） |
| 文件名规范 | `bookings_YYYYMMDD.csv`、`inventory_YYYYMMDD.csv`、`current_prices_YYYYMMDD.csv` |

---

### 常见 PMS 导出路径参考

| PMS | 导出路径（参考，以实际版本为准） |
|-----|-------------------------------|
| 西软 PMS | 报表中心 → 营业日报 → 自定义字段导出 CSV |
| 中软云 | 数据中心 → 订单报表 → 按日期范围导出 |
| 飞象科技 | 运营报表 → 入住数据 → 导出 Excel |
| Cloudbeds | Reports → Reservations → Export CSV |
| Opera Cloud | Reports → Reservation Activity → Export |
| Mews | Reporting → Reservations → CSV export |
| 无 PMS（Excel 管理） | 直接按三张表的字段整理成 CSV 发送即可 |

> 如果酒店 PMS 导出的字段名与上述不同，只需提供一份样例文件，我们会制作一份字段映射配置，后续导入全自动处理。

---

### 数据更新频率

| 阶段 | 更新方式 | 更新频率 |
|------|----------|---------|
| 试用阶段（手动） | 酒店 IT 手动导出并发送 CSV | 每周或每天一次 |
| 正式运行（自动） | PMS 定时导出 → SFTP 推送到服务器 | 每天凌晨 2:00 自动运行 |
| 规模化阶段 | PMS API 直连 | 实时或每 15 分钟一次 |

自动同步配置方法见 `docs/roadmap.md` Phase 5A 节。

---

## 注意事项

### 1. 向中国大陆酒店演示时的限制

**访问速度**：VPS 在法兰克福，中国大陆到欧洲的延迟约 200–300ms，页面加载会明显偏慢。正式商业演示建议迁移到：
- Tokyo VPS（161.33.188.233，延迟更低）
- 国内云服务器（阿里云/腾讯云）

**数据合规**：酒店历史订单数据属于商业敏感数据。将真实数据上传到境外服务器，在国内合规层面存在顾虑（尤其规模较大的酒店）。建议：
- 演示阶段统一使用系统内置的 Demo 数据，不上传真实数据
- 正式落地时，优先部署在国内服务器，或帮客户本地部署

### 2. 服务器安全规范

- Streamlit 只监听 `127.0.0.1:8501`，不直接对外暴露
- 对外访问统一通过 Caddy（80/443 端口）
- 当前未启用 Basic Auth；正式产品应补充更完善的认证机制
- 应用由 systemd 托管，VPS 重启后会自动恢复
- 不要将 `.env` 或包含真实客户数据的文件提交到 GitHub

### 3. 竞品参考

- **Atomize**：AI 酒店收益管理，含 Autopilot 自动定价、竞品数据、多物业支持
- **PriceLabs**：动态定价，支持 Booking/Airbnb/VRBO 同步，覆盖 150+ 国家 600,000+ 物业
- **Lighthouse**：酒店定价技术独角兽

本项目定位：**轻量级智能调价助手**，面向中小酒店、精品酒店、民宿，以及酒店管理教学场景。不与上述产品正面竞争，核心差异在于：决策支持而非全自动调价，推荐结果可解释，部署简单。

---

## 下一步计划

1. 用 Demo 数据完成第一次完整演示验证
2. 确认是否有真实酒店数据可接入，或继续使用模拟数据
3. 如需向中国客户演示，评估是否迁移到 Tokyo VPS 或国内服务器
4. 为长期开放访问补充正式认证机制
