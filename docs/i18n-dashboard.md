# 多语言界面与销售演示看板

## 当前支持语言

Streamlit 页面右上角提供语言选择：

- 中文
- English
- Deutsch
- Français

默认语言为中文。语言切换只影响前端展示，不改变底层数据、指标计算和推荐算法。

## 页面结构

当前界面分为三个标签页：

1. **销售演示看板**
   - 管理层摘要
   - 参数和指标解释折叠说明
   - 房费收入、入住率、ADR、RevPAR
   - 需调价日期数量
   - 高置信度建议数量
   - 风险提示数量
   - 调价动作分布图
   - RevPAR 趋势图
   - 重点机会与风险列表
   - 重点表格列带有可悬停说明

2. **调价建议**
   - 支持按上调、下调、保持筛选
   - 表格字段已按当前语言翻译
   - 推荐原因和风险提示已做多语言映射
   - 关键列带有可悬停说明
   - 支持选择 Excel 导出语言
   - Excel 默认导出语言跟随当前界面语言，也可以手动改为中文、英文、德文或法文

3. **数据预览**
   - 订单数据
   - 库存数据
   - 当前价格数据

## 参数说明

侧边栏中的关键参数现在带有 Streamlit help tooltip：

- **推荐周期**：系统为未来多少天生成调价建议。默认 30 天适合演示和日常查看；7–14 天适合关注短期销售压力；45–60 天适合月度计划，但不确定性更高。
- **单次最大调价幅度**：限制系统单次建议的最大涨跌幅。保守建议 10%–15%；价格敏感场景可用 5%–10%；旺季或库存紧张时可临时提高到 20%–30%，但仍应人工复核。

## 指标解释

销售演示看板和调价建议页都包含“如何解读这些指标”的折叠说明。重点解释：

- **剩余库存比例**：还没卖出的可售房间比例。接近 0 表示库存紧张；接近 1 表示库存充足；负值通常意味着超售或库存/订单数据不一致。
- **预计收益变化**：正值表示推荐价可能增加收益；负值表示为了提高成交或降低风险，系统建议接受一定收入下降。
- **14天 Pickup**：最近 14 天新增的预订量，用来判断近期需求强弱。
- **置信度**：系统对建议的把握程度。
- **风险提示**：提醒人工复核的原因，例如临近入住、库存异常或历史基准不足。

## Excel 导出

`调价建议` 标签页中有独立的 Excel 导出语言选择器：

- 默认值：当前界面语言
- 可选语言：中文、English、Deutsch、Français
- 导出文件名格式：`hotel_pricing_recommendations_<language>.xlsx`

Excel 工作簿包含两个 sheet：

1. 调价建议 / Price Recommendations / Preisempfehlungen / Recommandations
2. 每日指标 / Daily Metrics / Tageskennzahlen / Indicateurs journaliers

调价建议 sheet 会本地化字段名、建议动作、置信度、推荐原因和风险提示。每日指标 sheet 会本地化字段名。

## 技术实现

- `src/i18n.py`：集中保存多语言文案、字段名映射、推荐原因和风险提示翻译。
- `src/ui_help.py`：集中保存多语言参数说明、指标解释和表格列 help 配置。
- `src/report_export.py`：负责生成多语言 Excel 报表。
- `app/streamlit_app.py`：负责页面布局、语言选择、销售演示看板、表格展示、导出语言选择和 tooltip 接入。

## VPS 更新步骤

```bash
cd /data/projects/hotel-pricing-engine
git pull

# 如果已经用 nohup 运行，需要先停旧进程
pkill -f "streamlit run app/streamlit_app.py" || true

nohup python3 -m streamlit run app/streamlit_app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.headless true > /tmp/hotel-pricing.log 2>&1 &
```

查看日志：

```bash
tail -f /tmp/hotel-pricing.log
```

## 后续建议

- 把 Streamlit 启动方式从 `nohup` 改为 systemd service。
- 如果要面向客户演示，可以再加入首页欢迎页、产品卖点卡片、案例说明和联系入口。
