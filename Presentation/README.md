# Presentation

这个目录用于放置对外演示用的静态 HTML 演示文稿。

## 文件

- `index.html`: 给酒店老板看的精简版演示文稿。适合直接部署到静态网站或 VPS。
- `assets/`: 后续可放产品截图，例如销售看板、调价建议、回测分析、审批流程截图。

## 如何部署

可以把整个 `Presentation/` 目录同步到 VPS 的静态站点目录，例如：

```bash
rsync -av Presentation/ user@server:/var/www/hotel-presentation/
```

然后通过 Caddy / Nginx 配置一个公开链接，例如：

```text
https://hotel.zengsg.dpdns.org/presentation/
```

## 图片如何加入

如果后续要使用产品截图，建议放在：

```text
Presentation/assets/
```

推荐文件名：

```text
01-sales-dashboard.png
02-recommendations.png
03-backtesting.png
04-approval-workflow.png
05-channel-pricing.png
```

目前 `index.html` 是纯 HTML/CSS 版本，不依赖截图也可以完整展示。

## 你如何把图片给 ChatGPT

有三种方式：

1. 直接在聊天里上传 PNG / JPG 截图。
2. 你自己把图片放进 GitHub 的 `Presentation/assets/` 后告诉我文件名。
3. 你把图片放在本地项目目录，再自己 `git add` / `git push`，然后让我修改 HTML 引用路径。

如果只是第一次给酒店老板演示，当前无截图版本已经可以使用。加入真实产品截图后，会更像正式销售材料。

## 建议使用方式

第一次见老板建议使用精简版：

- 问题：酒店每天都要判断价格
- 方法：系统自动生成建议，但不自动改价
- 模型：不是追求满房，而是收益最大化
- 数据：三张 CSV + 业务规则
- 试点：2–4 周跑通完整流程

完整 30 页版可以作为后续深入沟通材料。
