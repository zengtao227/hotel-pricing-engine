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
   - 支持下载 Excel 报表

3. **数据预览**
   - 订单数据
   - 库存数据
   - 当前价格数据

## 技术实现

- `src/i18n.py`：集中保存多语言文案、字段名映射、推荐原因和风险提示翻译。
- `app/streamlit_app.py`：负责页面布局、语言选择、销售演示看板和表格展示。

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
- Excel 报表后续也可以根据当前语言导出多语言字段名。
- 如果要面向客户演示，可以再加入首页欢迎页、产品卖点卡片、案例说明和联系入口。
