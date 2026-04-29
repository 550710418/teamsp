# checkout-link-open-source

一个最小可用的页面 + Node 服务：输入 `accessToken`，生成 ChatGPT Team 的 checkout URL。

## 功能

- 前端页面：`checkout-link.html`
  - 输入 `accessToken`
  - 配置 `workspace_name / seat_quantity / promo_code / country / currency`
  - 生成支付链接
  - 一键打开、一键复制
- 后端服务：`checkout-server.mjs`
  - 提供 `/api/checkout` 中转，避免浏览器跨域问题
  - 自动清洗 token（支持粘贴 `Bearer xxx` 或包含 `accessToken` 的 JSON）

## 运行

```bash
node checkout-server.mjs
```

默认端口 `61314`。可通过环境变量覆盖：

```bash
PORT=61315 node checkout-server.mjs
```

然后打开：

- `http://127.0.0.1:61314/checkout-link.html`

## 免责声明

- 仅用于你自己的账号与合法授权场景。
- `accessToken` 属于敏感凭证，请勿泄露。
- 若 token 已泄露，请立即重新登录并更换会话 token。
