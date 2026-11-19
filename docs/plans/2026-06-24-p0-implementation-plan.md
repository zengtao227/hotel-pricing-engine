# P0 淡旺季日历 + Pickup 速度基准 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为定价引擎添加淡旺季日历（按入住日期应用需求系数）和 Pickup 速度基准（当前预订速度与历史同期对比），使推荐更准确、可解释。

**Architecture:** 季节系数在 `hotel_config.py` 配置和校验，通过 `generate_recommendations()` 新增 `seasons` 参数传入，在推荐循环里调整 `baseline_occupancy`。历史 Pickup 基准在 `metrics.py` 新增函数计算，`pricing_engine.py` 用 velocity ratio 替换现有基于绝对值的打分条件。

**Tech Stack:** Python, pandas, Streamlit, pytest

---

### Task 1: hotel_config.py — seasons 字段校验与查询

**Files:**
- Modify: `src/hotel_config.py`
- Test: `tests/test_hotel_config.py`

**Step 1: 写失败测试**

在 `tests/test_hotel_config.py` 末尾添加：

```python
def test_normalize_seasons_valid():
    config = normalize_hotel_config({
        "seasons": [
            {"name": "国庆", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0},
        ]
    })
    assert len(config["seasons"]) == 1
    assert config["seasons"][0]["demand_multiplier"] == 2.0


def test_normalize_seasons_invalid_date_raises():
    with pytest.raises(ValueError, match="invalid date"):
        normalize_hotel_config({"seasons": [
            {"name": "X", "start": "bad-date", "end": "2026-10-07", "demand_multiplier": 1.5}
        ]})


def test_normalize_seasons_start_after_end_raises():
    with pytest.raises(ValueError, match="start > end"):
        normalize_hotel_config({"seasons": [
            {"name": "X", "start": "2026-10-08", "end": "2026-10-01", "demand_multiplier": 1.5}
        ]})


def test_normalize_seasons_multiplier_out_of_range_raises():
    with pytest.raises(ValueError, match="demand_multiplier"):
        normalize_hotel_config({"seasons": [
            {"name": "X", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 10.0}
        ]})


def test_normalize_seasons_empty_is_valid():
    config = normalize_hotel_config({"seasons": []})
    assert config["seasons"] == []


def test_normalize_seasons_default_is_empty():
    config = normalize_hotel_config({})
    assert config["seasons"] == []
```

**Step 2: 运行测试确认失败**

```bash
cd hotel-pricing-engine   # repository root
python -m pytest tests/test_hotel_config.py::test_normalize_seasons_valid -v
```
Expected: FAIL — `normalize_hotel_config` 不认识 `seasons` 字段

**Step 3: 在 `src/hotel_config.py` 实现**

1. 在文件顶部加 import：
```python
from datetime import date as _date
```

2. 在 `DEFAULT_HOTEL_CONFIG` 里加：
```python
"seasons": [],
```

3. 在 `normalize_hotel_config()` 的 `normalized["room_types"] = rooms` 之后加：

```python
raw_seasons = config.get("seasons", [])
if not isinstance(raw_seasons, list):
    raise ValueError("Invalid hotel config: `seasons` must be a list")
if len(raw_seasons) > 50:
    raise ValueError("Invalid hotel config: `seasons` exceeds 50 entries")

normalized_seasons: list[dict] = []
for season in raw_seasons:
    if not isinstance(season, dict):
        raise ValueError("Invalid hotel config: season entries must be objects")
    name = str(season.get("name", "")).strip()
    if not name:
        raise ValueError("Invalid hotel config: each season needs a `name`")
    if len(name) > 40:
        raise ValueError("Invalid hotel config: season name exceeds 40 characters")
    try:
        s_start = _date.fromisoformat(str(season.get("start", "")))
        s_end = _date.fromisoformat(str(season.get("end", "")))
    except ValueError:
        raise ValueError(f"Invalid hotel config: invalid date in season `{name}`")
    if s_start > s_end:
        raise ValueError(f"Invalid hotel config: start > end in season `{name}`")
    multiplier = _finite_non_negative_float(season.get("demand_multiplier", 1.0), "demand_multiplier")
    if multiplier < 0.1 or multiplier > 5.0:
        raise ValueError(f"Invalid hotel config: demand_multiplier must be 0.1–5.0 in season `{name}`")
    normalized_seasons.append({
        "name": name,
        "start": s_start.isoformat(),
        "end": s_end.isoformat(),
        "demand_multiplier": round(multiplier, 4),
    })
normalized["seasons"] = normalized_seasons
```

4. 在文件末尾（`render_hotel_configuration` 之前）添加查询函数：

```python
def get_season_multiplier(stay_date: _date, seasons: list[dict]) -> tuple[float, str]:
    """Return (highest demand_multiplier, season_name) for stay_date, or (1.0, '') if no match."""
    best_multiplier: float = 1.0
    best_name: str = ""
    for season in seasons:
        try:
            s_start = _date.fromisoformat(season["start"])
            s_end = _date.fromisoformat(season["end"])
        except (KeyError, ValueError):
            continue
        if s_start <= stay_date <= s_end:
            m = float(season.get("demand_multiplier", 1.0))
            if m > best_multiplier:
                best_multiplier = m
                best_name = str(season.get("name", ""))
    return best_multiplier, best_name
```

注意：当多个季节重叠时，取最高 multiplier（旺季优先原则）。淡季（multiplier < 1.0）只在无其他旺季覆盖时生效——如果需要淡季能覆盖旺季，改为"取最后匹配"，但当前设计取最高更安全。

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_hotel_config.py -v
```
Expected: 全部 PASS

**Step 5: 给 `get_season_multiplier` 加专项测试，写完后运行**

在 `tests/test_hotel_config.py` 末尾添加：

```python
from src.hotel_config import get_season_multiplier
from datetime import date


def test_get_season_multiplier_match():
    seasons = [{"name": "国庆", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0}]
    m, name = get_season_multiplier(date(2026, 10, 3), seasons)
    assert m == 2.0
    assert name == "国庆"


def test_get_season_multiplier_no_match():
    seasons = [{"name": "国庆", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0}]
    m, name = get_season_multiplier(date(2026, 9, 30), seasons)
    assert m == 1.0
    assert name == ""


def test_get_season_multiplier_overlapping_takes_max():
    seasons = [
        {"name": "旺季A", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 1.8},
        {"name": "旺季B", "start": "2026-10-03", "end": "2026-10-10", "demand_multiplier": 2.1},
    ]
    m, name = get_season_multiplier(date(2026, 10, 5), seasons)
    assert m == 2.1
    assert name == "旺季B"


def test_get_season_multiplier_empty_seasons():
    m, name = get_season_multiplier(date(2026, 10, 3), [])
    assert m == 1.0
    assert name == ""
```

```bash
python -m pytest tests/test_hotel_config.py -v
```
Expected: 全部 PASS

**Step 6: Commit**

```bash
git add src/hotel_config.py tests/test_hotel_config.py
git commit -m "feat: add seasons calendar to hotel config with demand multiplier"
```

---

### Task 2: metrics.py — 历史 Pickup 基准计算

**Files:**
- Modify: `src/metrics.py`
- Test: `tests/test_metrics.py`

**Step 1: 写失败测试**

在 `tests/test_metrics.py` 末尾添加：

```python
from src.metrics import calculate_historical_pickup_baseline


def _make_historical_bookings() -> pd.DataFrame:
    """Hotel H1, room Standard Double, 3 historical stay dates, some booked within 14d."""
    return pd.DataFrame({
        "booking_id": ["B1", "B2", "B3", "B4", "B5"],
        "hotel_id": ["H1"] * 5,
        "room_type": ["Standard Double"] * 5,
        # stay dates all before observation 2026-03-01
        "check_in_date": pd.to_datetime(["2026-01-10", "2026-01-10", "2026-01-20", "2026-01-20", "2026-02-15"]),
        "check_out_date": pd.to_datetime(["2026-01-11", "2026-01-11", "2026-01-21", "2026-01-21", "2026-02-16"]),
        "booking_date": pd.to_datetime([
            "2026-01-05",   # 5 days before Jan 10 → within 14d
            "2026-12-20",   # 21 days before Jan 10 → NOT within 14d (this is actually months before - wait, let me recalculate)
            "2026-01-15",   # 5 days before Jan 20 → within 14d
            "2026-01-01",   # 19 days before Jan 20 → NOT within 14d
            "2026-02-10",   # 5 days before Feb 15 → within 14d
        ]),
        "nights": [1] * 5,
        "rooms": [2, 1, 3, 2, 1],
        "gross_room_revenue": [800, 400, 1200, 800, 400],
        "net_room_revenue": [800, 400, 1200, 800, 400],
        "daily_rate": [400] * 5,
        "channel": ["direct"] * 5,
        "status": ["stayed"] * 5,
    })


def test_calculate_historical_pickup_baseline_returns_median():
    bookings = _make_historical_bookings()
    observation_date = pd.to_datetime("2026-03-01")
    result = calculate_historical_pickup_baseline(bookings, observation_date)

    # H1 / Standard Double / weekday rows
    # Jan 10 (Saturday=weekend): pickup_14d = 2 (B1 booked 5d before)
    # Jan 20 (Tuesday=weekday): pickup_14d = 3 (B3 booked 5d before)
    # Feb 15 (Sunday=weekend): pickup_14d = 1 (B5 booked 5d before)
    # is_weekend=False median = 3.0 (only Jan 20)
    # is_weekend=True median = median(2,1) = 1.5
    row = result[(result["hotel_id"] == "H1") & (result["room_type"] == "Standard Double") & (~result["is_weekend"])]
    assert len(row) == 1
    assert row.iloc[0]["baseline_pickup_14d"] == pytest.approx(3.0)


def test_calculate_historical_pickup_baseline_empty_bookings():
    result = calculate_historical_pickup_baseline(pd.DataFrame(columns=[
        "booking_id", "hotel_id", "room_type", "check_in_date", "check_out_date",
        "booking_date", "nights", "rooms", "gross_room_revenue", "net_room_revenue",
        "daily_rate", "channel", "status"
    ]), pd.to_datetime("2026-03-01"))
    assert result.empty
```

**Step 2: 运行确认失败**

```bash
python -m pytest tests/test_metrics.py::test_calculate_historical_pickup_baseline_returns_median -v
```
Expected: FAIL — `calculate_historical_pickup_baseline` not defined

**Step 3: 在 `src/metrics.py` 实现**

在 `calculate_pickup` 函数之后添加：

```python
def calculate_historical_pickup_baseline(bookings: pd.DataFrame, observation_date) -> pd.DataFrame:
    """Compute median pickup_14d per (hotel_id, room_type, is_weekend) from historical stay dates.

    For each historical stay date, counts rooms booked within 14 days before that stay date.
    Returns a DataFrame with columns: hotel_id, room_type, is_weekend, baseline_pickup_14d.
    """
    if bookings.empty:
        return pd.DataFrame(columns=["hotel_id", "room_type", "is_weekend", "baseline_pickup_14d"])

    b = bookings.copy()
    b["booking_date"] = pd.to_datetime(b["booking_date"]).dt.normalize()
    b["check_in_date"] = pd.to_datetime(b["check_in_date"]).dt.normalize()
    observation_date = pd.to_datetime(observation_date).normalize()

    active = b["status"].astype(str).str.lower().isin(ACTIVE_STATUSES)
    historical = b["check_in_date"] < observation_date
    mask = active & historical
    if not mask.any():
        return pd.DataFrame(columns=["hotel_id", "room_type", "is_weekend", "baseline_pickup_14d"])

    h = b.loc[mask].copy()
    h["days_before"] = (h["check_in_date"] - h["booking_date"]).dt.days
    h14 = h[h["days_before"].between(0, 14)].copy()
    if h14.empty:
        return pd.DataFrame(columns=["hotel_id", "room_type", "is_weekend", "baseline_pickup_14d"])

    h14["nights"] = pd.to_numeric(h14.get("nights", 1), errors="coerce").fillna(1).clip(lower=1, upper=365).astype(int)
    rep = h14.loc[h14.index.repeat(h14["nights"])].copy()
    rep["_offset"] = rep.groupby(level=0).cumcount()
    rep["stay_date"] = (rep["check_in_date"] + pd.to_timedelta(rep["_offset"], unit="D")).dt.normalize()

    per_date = (
        rep.groupby(["hotel_id", "room_type", "stay_date"], as_index=False)
        .agg(hist_pickup_14d=("rooms", "sum"))
    )
    per_date["is_weekend"] = pd.to_datetime(per_date["stay_date"]).dt.weekday >= 5

    return (
        per_date.groupby(["hotel_id", "room_type", "is_weekend"], as_index=False)
        .agg(baseline_pickup_14d=("hist_pickup_14d", "median"))
    )
```

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_metrics.py -v
```
Expected: 全部 PASS

**Step 5: Commit**

```bash
git add src/metrics.py tests/test_metrics.py
git commit -m "feat: add calculate_historical_pickup_baseline to metrics"
```

---

### Task 3: i18n.py — 新增文案

**Files:**
- Modify: `src/i18n.py`

**Step 1: 在 `TRANSLATIONS` 字典末尾添加以下条目**

找到最后一个条目的 `},` 之后，在关闭 `}` 前插入：

```python
    "season_peak_reason": {
        "zh": "入住日期在旺季（{name}），需求预期高于历史均值",
        "en": "stay date falls in peak season ({name}), demand above historical average",
        "de": "Aufenthaltsdatum liegt in der Hochsaison ({name}), Nachfrage über historischem Durchschnitt",
        "fr": "la date de séjour est en haute saison ({name}), demande supérieure à la moyenne historique",
    },
    "season_low_reason": {
        "zh": "入住日期在淡季（{name}），需求预期低于历史均值",
        "en": "stay date falls in low season ({name}), demand below historical average",
        "de": "Aufenthaltsdatum liegt in der Nebensaison ({name}), Nachfrage unter historischem Durchschnitt",
        "fr": "la date de séjour est en basse saison ({name}), demande inférieure à la moyenne historique",
    },
    "pickup_velocity_high": {
        "zh": "近期预订速度高于历史同期（{ratio:.0%}）",
        "en": "recent booking pace above historical average ({ratio:.0%})",
        "de": "aktuelles Buchungstempo über historischem Durchschnitt ({ratio:.0%})",
        "fr": "rythme de réservation récent supérieur à la moyenne historique ({ratio:.0%})",
    },
    "pickup_velocity_low": {
        "zh": "近期预订速度低于历史同期（{ratio:.0%}）",
        "en": "recent booking pace below historical average ({ratio:.0%})",
        "de": "aktuelles Buchungstempo unter historischem Durchschnitt ({ratio:.0%})",
        "fr": "rythme de réservation récent inférieur à la moyenne historique ({ratio:.0%})",
    },
    "seasons_config": {
        "zh": "季节日历",
        "en": "Season Calendar",
        "de": "Saisonkalender",
        "fr": "Calendrier des saisons",
    },
    "seasons_intro": {
        "zh": "配置旺季和淡季的需求倍率。入住日期匹配时，基准需求会按倍率调整。多段重叠时取最高倍率。",
        "en": "Configure demand multipliers for peak and low seasons. When a stay date matches, the baseline demand is scaled accordingly. Highest multiplier wins when ranges overlap.",
        "de": "Nachfragemultiplikatoren für Hoch- und Nebensaisons konfigurieren. Bei Überschneidungen gilt der höchste Multiplikator.",
        "fr": "Configurez les multiplicateurs de demande pour les hautes et basses saisons. En cas de chevauchement, le multiplicateur le plus élevé s'applique.",
    },
    "season_name": {"zh": "季节名称", "en": "Season name", "de": "Saisonname", "fr": "Nom de la saison"},
    "season_start": {"zh": "开始日期", "en": "Start date", "de": "Startdatum", "fr": "Date de début"},
    "season_end": {"zh": "结束日期", "en": "End date", "de": "Enddatum", "fr": "Date de fin"},
    "season_multiplier": {"zh": "需求倍率", "en": "Demand multiplier", "de": "Nachfragemultiplikator", "fr": "Multiplicateur de demande"},
    "season_add": {"zh": "添加季节段", "en": "Add season", "de": "Saison hinzufügen", "fr": "Ajouter une saison"},
    "season_save": {"zh": "保存季节配置", "en": "Save seasons", "de": "Saisons speichern", "fr": "Enregistrer les saisons"},
```

**Step 2: 验证 Python 语法**

```bash
python -m py_compile src/i18n.py && echo "OK"
```
Expected: `OK`

**Step 3: Commit**

```bash
git add src/i18n.py
git commit -m "feat: add i18n strings for seasons and pickup velocity"
```

---

### Task 4: pricing_engine.py — 季节系数 + Pickup Velocity

**Files:**
- Modify: `src/pricing_engine.py`
- Test: `tests/test_pricing_engine.py`

**Step 1: 写失败测试**

在 `tests/test_pricing_engine.py` 末尾添加（先找到现有的 helper 函数 `_metrics`, `_bookings`, `_prices`，在文件末尾添加）：

```python
def _prices(stay_dates=None, hotel_id="H1", room_type="Standard Double"):
    if stay_dates is None:
        stay_dates = ["2024-02-01", "2024-02-02", "2024-02-03"]
    return pd.DataFrame([{
        "hotel_id": hotel_id,
        "room_type": room_type,
        "stay_date": pd.to_datetime(d),
        "current_price": 400.0,
    } for d in stay_dates])


def test_peak_season_increases_recommendation():
    """A peak season multiplier should push the recommended price up vs no season."""
    metrics = _metrics(["2024-02-01", "2024-02-02", "2024-02-03"])
    bookings = _bookings()
    prices = _prices(["2024-02-01"])
    
    recs_no_season = generate_recommendations(
        metrics, bookings, prices,
        observation_date=pd.to_datetime("2024-02-01"),
        seasons=[],
    )
    recs_peak = generate_recommendations(
        metrics, bookings, prices,
        observation_date=pd.to_datetime("2024-02-01"),
        seasons=[{"name": "旺季", "start": "2024-02-01", "end": "2024-02-28", "demand_multiplier": 2.0}],
    )
    # Peak season should not produce a lower recommended price
    price_no_season = recs_no_season.iloc[0]["recommended_price"]
    price_peak = recs_peak.iloc[0]["recommended_price"]
    assert price_peak >= price_no_season


def test_peak_season_reason_included():
    """Peak season name must appear in main_reasons."""
    metrics = _metrics(["2024-02-01", "2024-02-02", "2024-02-03"])
    bookings = _bookings()
    prices = _prices(["2024-02-01"])
    
    recs = generate_recommendations(
        metrics, bookings, prices,
        observation_date=pd.to_datetime("2024-02-01"),
        seasons=[{"name": "春节", "start": "2024-01-01", "end": "2024-02-28", "demand_multiplier": 1.8}],
    )
    assert "春节" in recs.iloc[0]["main_reasons"]


def test_low_season_reason_included():
    """Low season name must appear in main_reasons."""
    metrics = _metrics(["2024-02-01", "2024-02-02", "2024-02-03"])
    bookings = _bookings()
    prices = _prices(["2024-02-01"])
    
    recs = generate_recommendations(
        metrics, bookings, prices,
        observation_date=pd.to_datetime("2024-02-01"),
        seasons=[{"name": "11月淡季", "start": "2024-01-01", "end": "2024-02-28", "demand_multiplier": 0.6}],
    )
    assert "11月淡季" in recs.iloc[0]["main_reasons"]


def test_no_season_match_no_season_reason():
    """When stay date is outside all seasons, no season text in reasons."""
    metrics = _metrics(["2024-02-01", "2024-02-02", "2024-02-03"])
    bookings = _bookings()
    prices = _prices(["2024-02-01"])
    
    recs = generate_recommendations(
        metrics, bookings, prices,
        observation_date=pd.to_datetime("2024-02-01"),
        seasons=[{"name": "春节", "start": "2024-03-01", "end": "2024-03-31", "demand_multiplier": 1.8}],
    )
    assert "春节" not in recs.iloc[0]["main_reasons"]
```

**Step 2: 运行确认失败**

```bash
python -m pytest tests/test_pricing_engine.py::test_peak_season_increases_recommendation -v
```
Expected: FAIL — `generate_recommendations` 不接受 `seasons` 参数

**Step 3: 修改 `src/pricing_engine.py`**

3a. 在顶部 import 加入：
```python
from .hotel_config import get_season_multiplier
from .metrics import calculate_historical_pickup_baseline
```

3b. `generate_recommendations` 函数签名加入 `seasons` 参数：
```python
def generate_recommendations(
    metrics: pd.DataFrame,
    bookings: pd.DataFrame,
    current_prices: pd.DataFrame,
    observation_date=None,
    horizon_days: int = 30,
    max_change_pct: float = 0.15,
    price_rounding_strategy: str = "chinese_lucky",
    room_price_bounds: dict | None = None,
    seasons: list[dict] | None = None,
) -> pd.DataFrame:
```

3c. 在 `baselines` 计算之后（约 `recs = future.merge(baselines, ...)` 之前），加入 pickup baseline 计算：

```python
pickup_baseline = calculate_historical_pickup_baseline(bookings, observation_date)
recs = future.merge(baselines, how="left", on=["hotel_id", "room_type", "is_weekend"])
recs = recs.merge(pickup_baseline, how="left", on=["hotel_id", "room_type", "is_weekend"])
```

注意：原来的 `recs = future.merge(baselines, ...)` 这行要保留，只是在它之后加 pickup_baseline merge。实际上需要把原来那一行改成先 merge baselines，再 merge pickup_baseline，参考：

```python
recs = future.merge(baselines, how="left", on=["hotel_id", "room_type", "is_weekend"])
recs = recs.merge(pickup_baseline, how="left", on=["hotel_id", "room_type", "is_weekend"])
recs["baseline_occupancy"] = recs["baseline_occupancy"].fillna(historical["occupancy"].median())
recs["baseline_adr"] = recs["baseline_adr"].fillna(historical["adr"].median())
recs["baseline_revpar"] = recs["baseline_revpar"].fillna(historical["revpar"].median())
recs["baseline_pickup_14d"] = recs["baseline_pickup_14d"].fillna(0.0)
```

3d. 在 for 循环里，`baseline_occupancy = float(row.baseline_occupancy or 0)` 之后，加季节系数逻辑：

```python
baseline_pickup_14d = float(getattr(row, "baseline_pickup_14d", 0) or 0)
active_seasons = seasons or []
season_multiplier, season_name = get_season_multiplier(row.stay_date.date(), active_seasons)
adjusted_baseline_occupancy = baseline_occupancy * season_multiplier
```

然后把后续所有用到 `baseline_occupancy` 传入 `simulate_revenue_maximizing_price` 的地方改为 `adjusted_baseline_occupancy`：
```python
simulation: RevenueSimulationResult = simulate_revenue_maximizing_price(
    ...
    baseline_occupancy=adjusted_baseline_occupancy,   # 改这里
    ...
)
```

3e. 季节 reason：在 `score = 0` / `reasons = []` 之后，加：

```python
if season_multiplier > 1.05:
    score += 1
    reasons.append(f"入住日期在旺季（{season_name}），需求预期高于历史均值")
elif season_multiplier < 0.95:
    score -= 1
    reasons.append(f"入住日期在淡季（{season_name}），需求预期低于历史均值")
```

3f. Pickup velocity 逻辑：找到现有的两段 pickup 打分代码：

```python
if pickup_14d >= 4:
    score += 1
    reasons.append("recent 14-day pickup is strong")
elif days_to_arrival <= 14 and pickup_14d <= 1:
    score -= 1
    reasons.append("weak recent pickup close to arrival")
```

替换为（保留原有逻辑作为 fallback）：

```python
if baseline_pickup_14d > 0:
    pickup_velocity_ratio = pickup_14d / baseline_pickup_14d
    if pickup_velocity_ratio >= 1.3:
        score += 1
        reasons.append(f"近期预订速度高于历史同期（{pickup_velocity_ratio:.0%}）")
    elif pickup_velocity_ratio <= 0.7:
        score -= 1
        reasons.append(f"近期预订速度低于历史同期（{pickup_velocity_ratio:.0%}）")
else:
    pickup_velocity_ratio = None
    if pickup_14d >= 4:
        score += 1
        reasons.append("recent 14-day pickup is strong")
    elif days_to_arrival <= 14 and pickup_14d <= 1:
        score -= 1
        reasons.append("weak recent pickup close to arrival")
```

3g. 在 `estimate_price_elasticity` 调用中，velocity ratio 也影响弹性。找到 `revenue_simulation.py` 里的弹性计算用的是 `pickup_14d` 绝对值，这里不改 `revenue_simulation.py`（保持接口不变），而是在传参前做一个修正：如果有 velocity ratio，当 ratio >= 1.3 时把 `pickup_14d` 乘以一个 boost，当 ratio <= 0.7 时降低。

实际上不需要——`revenue_simulation.py` 的弹性调整也用 `pickup_14d`，而 `pickup_14d` 是真实值不变。已经通过 velocity ratio 在 score 和 reasons 里表达了，不需要再改弹性参数。保持 `simulate_revenue_maximizing_price` 传参不变即可。

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_pricing_engine.py -v
```
Expected: 全部 PASS

**Step 5: Commit**

```bash
git add src/pricing_engine.py tests/test_pricing_engine.py
git commit -m "feat: apply season multiplier and pickup velocity to recommendations"
```

---

### Task 5: hotel_config.py — 季节日历 UI

**Files:**
- Modify: `src/hotel_config.py`

**Step 1: 在 `render_hotel_configuration` 函数里，`st.subheader(label("room_config", lang))` 之前，添加季节日历区块**

```python
with st.expander(t("seasons_config", lang), expanded=False):
    st.caption(t("seasons_intro", lang))
    seasons = config.get("seasons", [])
    season_rows = [
        {
            "name": s.get("name", ""),
            "start": s.get("start", ""),
            "end": s.get("end", ""),
            "demand_multiplier": float(s.get("demand_multiplier", 1.0)),
        }
        for s in seasons
    ]
    season_df = pd.DataFrame(season_rows) if season_rows else pd.DataFrame(
        columns=["name", "start", "end", "demand_multiplier"]
    )
    edited_seasons = st.data_editor(
        season_df,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn(t("season_name", lang), max_chars=40),
            "start": st.column_config.TextColumn(t("season_start", lang), help="YYYY-MM-DD"),
            "end": st.column_config.TextColumn(t("season_end", lang), help="YYYY-MM-DD"),
            "demand_multiplier": st.column_config.NumberColumn(
                t("season_multiplier", lang),
                min_value=0.1,
                max_value=5.0,
                step=0.1,
                format="%.2f",
                help="1.0 = 无调整，2.0 = 需求翻倍，0.5 = 需求减半",
            ),
        },
        key="seasons_editor",
    )
    try:
        new_seasons = []
        for _, row in edited_seasons.iterrows():
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            new_seasons.append({
                "name": name,
                "start": str(row.get("start", "")),
                "end": str(row.get("end", "")),
                "demand_multiplier": float(row.get("demand_multiplier", 1.0)),
            })
        # Validate via normalize — surfaces errors inline
        normalize_hotel_config({"seasons": new_seasons})
        config["seasons"] = new_seasons
    except ValueError as exc:
        st.error(str(exc))
```

注意：需要在文件顶部确认 `from .i18n import LANGUAGES, t, translate_room_type` 已存在（已有）。

**Step 2: 语法验证**

```bash
python -m py_compile src/hotel_config.py && echo "OK"
```
Expected: `OK`

**Step 3: Commit**

```bash
git add src/hotel_config.py
git commit -m "feat: add season calendar UI to hotel configuration page"
```

---

### Task 6: Streamlit app — 传入 seasons 参数

**Files:**
- Modify: `app/streamlit_app.py`

**Step 1: 找到 `generate_recommendations(` 调用位置，加入 `seasons` 参数**

在 `app/streamlit_app.py` 里搜索 `generate_recommendations(`，找到调用位置，在现有参数后加：

```python
seasons=hotel_config.get("seasons", []),
```

**Step 2: 语法验证**

```bash
python -m py_compile app/streamlit_app.py && echo "OK"
```
Expected: `OK`

**Step 3: 运行全量测试**

```bash
python -m pytest tests/ -v --ignore=tests/test_auth.py 2>&1 | tail -20
```
Expected: 全部 PASS（auth 测试可能需要额外依赖，先 ignore）

**Step 4: Commit**

```bash
git add app/streamlit_app.py
git commit -m "feat: wire seasons config into recommendation pipeline"
```

---

### Task 7: 验证与收尾

**Step 1: 运行完整测试套件**

```bash
python -m pytest tests/ -v 2>&1 | tail -30
```
Expected: 全部 PASS

**Step 2: 检查 default_hotel_config 包含示例 seasons**

在 `src/hotel_config.py` 的 `DEFAULT_HOTEL_CONFIG` 里，把 `"seasons": []` 改为包含中国酒店常见旺季的示例，方便 demo 演示：

```python
"seasons": [
    {"name": "春节黄金周", "start": "2026-01-25", "end": "2026-02-08", "demand_multiplier": 1.8},
    {"name": "国庆黄金周", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0},
    {"name": "清明小长假", "start": "2026-04-03", "end": "2026-04-06", "demand_multiplier": 1.3},
    {"name": "劳动节黄金周", "start": "2026-05-01", "end": "2026-05-05", "demand_multiplier": 1.5},
    {"name": "暑期旺季",   "start": "2026-07-01", "end": "2026-08-31", "demand_multiplier": 1.3},
],
```

注意：`DEFAULT_HOTEL_CONFIG` 更新后，`default_hotel_config()` 的 deepcopy 会自动带上这些默认值。

**Step 3: 语法 + 测试**

```bash
python -m py_compile src/hotel_config.py && python -m pytest tests/test_hotel_config.py -v
```
Expected: `OK` + 全部 PASS

**Step 4: Final commit**

```bash
git add src/hotel_config.py
git commit -m "feat: add default Chinese holiday seasons to demo config"
```

---

## 验收标准

- [ ] `pytest tests/` 全部 PASS
- [ ] 酒店配置页出现"季节日历"区块，可增删行，保存后应用到当前会话
- [ ] 调价建议的 `main_reasons` 在旺季/淡季日期显示季节名称
- [ ] `main_reasons` 在预订速度明显高于/低于历史同期时显示 velocity 信息
- [ ] `generate_recommendations` 的 `seasons=[]` 时行为与改动前完全一致（无回归）
