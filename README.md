# hotel-pricing-engine

酒店动态定价与收益优化项目。

本项目目标不是简单预测“房价应该是多少”，而是建立一个可以根据历史订房、价格、库存和市场信号，推荐酒店房间价格的定价引擎。推荐结果应服务于收益最大化，同时兼顾入住率、取消风险、渠道差异和人工可解释性。

## 当前状态

项目已经推进到 **Streamlit MVP 原型**：

- 可以加载酒店订单、库存和当前价格 CSV
- 可以自动生成 demo 数据
- 可以计算 Occupancy、ADR、RevPAR、Pickup 等核心指标
- 可以生成未来日期的规则型调价建议
- 可以导出多语言 Excel 调价建议报表
- 可以转换 Kaggle Hotel Booking Demand 数据集为 MVP 格式
- 支持中文、英文、德文、法文界面切换
- 支持销售演示版 Dashboard
- 支持中国酒店演示用 6/8/9 价格尾数规则
- 支持酒店配置：房型、基准价、最低价、最高价、周末加价
- 支持价格审批与发布演示：最终批准价、人工修改标记、模拟推送、审计日志
- 支持审批与推送日志持久化到本地 CSV
- 支持静态销量回测分析，并可导出回测明细 Excel

## 快速启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

默认情况下，App 会使用内置 demo 数据。也可以在侧边栏关闭 demo 模式，上传自己的 CSV。

## 问题定义

酒店定价不是单一预测问题，而是一个收益管理问题：

```text
预期收益 = 推荐价格 * 预计成交间夜数
```

价格升高可能提高单间收入，但会降低成交概率；价格降低可能提高入住率，但会牺牲 ADR。系统需要在价格、需求、剩余库存和时间压力之间找到更优平衡。

## MVP 范围

当前阶段采用 human-in-the-loop 路线：系统生成建议，人工复核最终批准价，再进入发布或导出流程。

- 汇总历史订房、成交价格、入住日期、取消状态和房型数据
- 计算房型和日期级收益指标
- 生成可解释的当前价、推荐价和建议动作
- 给出推荐理由、置信度和人工复核提示
- 支持价格尾数规则和价格上下限
- 支持销售总监或店长审核最终批准价
- 支持模拟推送和审计日志
- 支持静态销量回测

## 核心指标

- `Room Revenue`: 房费收入
- `Occupancy`: 入住率
- `ADR`: 平均每日房价
- `RevPAR`: 每间可售房收入
- `Cancellation Rate`: 取消率
- `Pickup`: 某一时间窗口内新增预订量

`RevPAR` 是第一阶段最重要的优化参考指标，因为它同时考虑价格和入住率。

## Kaggle 数据转换

下载 Kaggle Hotel Booking Demand 的 `hotel_bookings.csv` 后，可以转换成 MVP 所需格式：

```bash
mkdir -p data/raw
# 把 hotel_bookings.csv 放到 data/raw/ 目录
python scripts/create_demo_data.py --source data/raw/hotel_bookings.csv --output-dir sample_data --hotel "City Hotel"
```

转换后会生成：

- `sample_data/bookings.csv`
- `sample_data/inventory.csv`
- `sample_data/current_prices.csv`

说明：Kaggle 数据有订单和 ADR，但没有真实库存快照和当前挂牌价快照，所以 adapter 会生成演示用库存和当前价格。真实客户场景下，应替换为 PMS、Channel Manager 或 Excel 导出的真实文件。

## 文档结构

- [CONTEXT.md](CONTEXT.md): 项目上下文、术语和协作规则
- [docs/requirements.md](docs/requirements.md): 产品需求与 MVP 验收标准
- [docs/data-requirements.md](docs/data-requirements.md): 数据字段、口径和质量要求
- [docs/modeling-approach.md](docs/modeling-approach.md): 建模路线与优化思路
- [docs/roadmap.md](docs/roadmap.md): 阶段计划
- [docs/open-questions.md](docs/open-questions.md): 待确认问题
- [docs/mvp-implementation.md](docs/mvp-implementation.md): MVP 运行和实现说明
- [docs/deployment.md](docs/deployment.md): VPS 部署说明
- [docs/i18n-dashboard.md](docs/i18n-dashboard.md): 多语言界面和销售演示看板说明
- [docs/price-approval-and-publishing.md](docs/price-approval-and-publishing.md): 价格审批与发布使用手册

## 商业化方向

优先验证两个方向：

1. **一次性部署 / 咨询版**：为中小酒店或民宿部署轻量收益管理助手。
2. **教学 / 实训工具版**：用于酒店管理与数字化运营课程，学生上传或使用模拟数据完成收益管理实训。
