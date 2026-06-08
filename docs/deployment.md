# 部署说明

## 当前运行环境

- **服务器**：Frankfurt VPS（89.168.80.38，Oracle Cloud ARM A1）
- **项目路径**：`/data/projects/hotel-pricing-engine`
- **访问地址**：`https://frank-hotel.mooo.com`（需完成 DNS 配置，见下文）
- **认证**：HTTP Basic Auth，账号 `admin`，密码 `hotel2026`

## 启动 Streamlit

```bash
cd /data/projects/hotel-pricing-engine
nohup python3 -m streamlit run app/streamlit_app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.headless true > /tmp/hotel-pricing.log 2>&1 &
```

查看日志：`tail -f /tmp/hotel-pricing.log`

## DNS 配置（首次部署需操作）

`frank-hotel.mooo.com` 需要在 changeip.com / mooo.com 控制台手动添加，指向 89.168.80.38。

配置好 DNS 后，Caddy 会自动申请 HTTPS 证书（Let's Encrypt），无需手动操作。

## Caddy 配置

配置文件：`/etc/caddy/Caddyfile`

```
frank-hotel.mooo.com {
    basic_auth {
        admin $2a$14$tRsftEhi4qOCg4AeKZpGI.fJ2klpzVHrwSC/guFhyHXnNOsDcYl3.
    }
    reverse_proxy localhost:8501
}
```

修改密码：
```bash
caddy hash-password --plaintext 新密码
# 将输出的哈希替换 Caddyfile 中的旧哈希
sudo systemctl reload caddy
```

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
- Basic Auth 提供基本的访问保护，适合演示阶段；正式产品应换成更完善的认证机制
- 不要将 `.env` 或包含真实客户数据的文件提交到 GitHub

### 3. 竞品参考

- **Atomize**：AI 酒店收益管理，含 Autopilot 自动定价、竞品数据、多物业支持
- **PriceLabs**：动态定价，支持 Booking/Airbnb/VRBO 同步，覆盖 150+ 国家 600,000+ 物业
- **Lighthouse**：酒店定价技术独角兽

本项目定位：**轻量级智能调价助手**，面向中小酒店、精品酒店、民宿，以及酒店管理教学场景。不与上述产品正面竞争，核心差异在于：决策支持而非全自动调价，推荐结果可解释，部署简单。

---

## 下一步计划

1. 配置 DNS（frank-hotel.mooo.com → 89.168.80.38）
2. 验证 HTTPS 访问正常
3. 用 Demo 数据完成第一次完整演示验证
4. 确认是否有真实酒店数据可接入，或继续使用模拟数据
5. 如需向中国客户演示，评估是否迁移到 Tokyo VPS 或国内服务器
