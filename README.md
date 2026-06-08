# hotel-pricing-engine

酒店动态定价与收益优化项目。

本项目目标不是简单预测“房价应该是多少”，而是建立一个可以根据历史订房、价格、库存和市场信号，推荐酒店房间价格的定价引擎。推荐结果应服务于收益最大化，同时兼顾入住率、取消风险、渠道差异和人工可解释性。

## 当前状态

项目已经从纯需求定义推进到 **Streamlit MVP 原型**：

- 可以加载酒店订单、库存和当前价格 CSV
- 可以自动生成 demo 数据
- 可以计算 Occupancy、ADR、RevPAR 等核心指标
- 可以生成未来日期的规则型调价建议
- 可以导出 Excel 调价建议报表
- 可以转换 Kaggle Hotel Booking Demand 数据集为 MVP 格式

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

第一阶段只做决策支持，不做自动改价：

- 汇总历史订房、成交价格、入住日期、取消状态和房型数据
- 预测指定入住日期、房型和提前期下的未来需求
- 估计不同价格下的成交概率或预计销量
- 对候选价格做收益模拟，输出推荐价
- 给出推荐理由、置信度和人工复核提示
- 生成每日或每周的调价建议报表

## 暂不做

- 不直接连接 PMS、OTA 或支付系统
- 不自动发布价格到 Booking、携程、官网等渠道
- 不承诺一开始就使用复杂深度学习模型
- 不使用无法解释的黑箱结果直接替代人工判断

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

## 商业化方向

优先验证两个方向：

1. **一次性部署 / 咨询版**：为中小酒店或民宿部署轻量收益管理助手。
2. **教学 / 实训工具版**：用于酒店管理与数字化运营课程，学生上传或使用模拟数据完成收益管理实训。
