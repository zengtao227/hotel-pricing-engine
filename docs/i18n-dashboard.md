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
   - 房费收入、入住率、ADR、RevPAR
   - 需调价日期数量
   - 高置信度建议数量
   - 风险提示数量
   - 调价动作分布图
   - RevPAR 趋势图
   - 重点机会与风险列表

2. **调价建议**
   - 支持按上调、下调、保持筛选
   - 表格字段已按当前语言翻译
   - 推荐原因和风险提示已做多语言映射
   - 支持选择 Excel 导出语言
   - Excel 默认导出语言跟随当前界面语言，也可以手动改为中文、英文、德文或法文

3. **数据预览**
   - 订单数据
   - 库存数据
   - 当前价格数据

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
- `src/report_export.py`：负责生成多语言 Excel 报表。
- `app/streamlit_app.py`：负责页面布局、语言选择、销售演示看板、表格展示和导出语言选择。

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
