# 多语言界面与销售演示看板

## 当前支持语言

Streamlit 页面右上角提供语言选择：

- 中文
- English
- Deutsch
- Français

默认语言为中文。语言切换只影响前端展示，不改变底层数据、指标计算和推荐算法。

## 页面结构

当前界面分为六个标签页：

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
   - 房型名称已按当前语言翻译，例如中文显示为“标准大床房 / 高级大床房 / 家庭房”
   - 推荐原因和风险提示已做多语言映射
   - 关键列带有可悬停说明
   - 支持选择 Excel 导出语言
   - Excel 默认导出语言跟随当前界面语言，也可以手动改为中文、英文、德文或法文

3. **回测分析**
   - 只使用历史观察日以前已知订单生成推荐，避免使用观察日之后才产生的订单
   - 使用最终实际售出房间数做静态销量回测
   - 展示基准收入、推荐价静态收入、静态收益变化和变化率
   - 展示每日静态收益变化图
   - 支持导出回测明细 Excel

4. **价格审批与发布**
   - 支持最终批准价人工修改
   - 审批表中的房型名称按当前语言翻译
   - 人工修改、已推送、已拒绝行会有颜色提示
   - 支持模拟一键推送和下载审批日志
   - 已推送行再次点击推送不会重复写入日志
   - 审批与推送日志会持久化到 `data/audit_logs/price_approval_publishing_log.csv`

5. **酒店配置**
   - 配置酒店名称、城市、市场定位、货币
   - 配置房型、基准价、最低价、最高价、周末加价
   - 只覆盖配置中存在的房型；上传数据里的未知房型会保留原始 current_price
   - 支持下载和上传酒店配置 JSON

6. **数据预览**
   - 订单数据
   - 库存数据
   - 当前价格数据

## 参数说明

侧边栏中的关键参数现在带有 Streamlit help tooltip：

- **推荐周期**：系统为未来多少天生成调价建议。默认 30 天适合演示和日常查看；7–14 天适合关注短期销售压力；45–60 天适合月度计划，但不确定性更高。
- **单次最大调价幅度**：限制系统单次建议的最大涨跌幅。保守建议 10%–15%；价格敏感场景可用 5%–10%；旺季或库存紧张时可临时提高到 20%–30%，但仍应人工复核。

## 房型翻译

内置 demo 房型目前支持中英德法翻译：

- `Standard Double`：标准大床房 / Standard Double / Standard-Doppelzimmer / Chambre double standard
- `Superior Double`：高级大床房 / Superior Double / Superior-Doppelzimmer / Chambre double supérieure
- `Family Room`：家庭房 / Family Room / Familienzimmer / Chambre familiale

如果将来客户上传自定义房型，系统会优先保留客户原始房型名称。可以在 `src/i18n.py` 中扩展 `ROOM_TYPES` 映射。

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

调价建议 sheet 会本地化字段名、房型名称、建议动作、置信度、推荐原因和风险提示。每日指标 sheet 会本地化字段名和房型名称。

## 技术实现

- `src/i18n.py`：集中保存多语言文案、房型名称映射、字段名映射、推荐原因和风险提示翻译。
- `src/ui_help.py`：集中保存多语言参数说明、指标解释和表格列 help 配置。
- `src/report_export.py`：负责生成多语言 Excel 报表。
- `src/backtesting.py`：负责静态销量回测分析和回测明细导出。
- `src/audit_log_store.py`：负责审批与推送日志持久化。
- `src/approval_workflow.py`：负责价格审批与发布流程，并在审批表中显示本地化房型名称。
- `src/hotel_config.py`：负责酒店配置、房型价格上下限和周末加价设置。
- `app/streamlit_app.py`：负责页面布局、语言选择、销售演示看板、表格展示、导出语言选择和 tooltip 接入。

## VPS 更新步骤

当前 VPS 已使用 systemd 服务 `hotel-pricing-engine.service`。

```bash
cd /data/projects/hotel-pricing-engine
git pull
sudo systemctl restart hotel-pricing-engine
sudo systemctl status hotel-pricing-engine --no-pager
```

查看日志：

```bash
sudo journalctl -u hotel-pricing-engine -n 80 --no-pager
```

## 后续建议

- 把审批日志从 CSV 升级为 SQLite。
- 把回测从静态销量回测升级为带价格弹性的收益回测，并展示候选价收益曲线。
- 增加 Channel Manager 导入模板导出。
- 为长期公网访问补充基础认证或访问保护。
