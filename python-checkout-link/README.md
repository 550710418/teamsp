# checkout-link-python

一个 Python 标准库版本的 ChatGPT Team 支付链接生成器，功能和原项目保持一致：

- 前端页面：`checkout-link.html`
  - 输入 `accessToken`
  - 配置 `workspace_name / seat_quantity / price_interval / promo_code / country / currency / cancel_url`
  - 生成 ChatGPT Team checkout URL
  - 一键打开、一键复制
- 后端服务：`server.py`
  - 提供 `/api/checkout` 中转接口，避免浏览器跨域问题
  - 自动清洗 token，支持粘贴 `Bearer xxx` 或包含 `accessToken` 的 JSON
  - 转发到 `https://chatgpt.com/backend-api/payments/checkout`

> 仅用于你自己的账号与合法授权场景。`accessToken` 是敏感凭证，请勿泄露或写入日志。

## 目录结构

```text
python-checkout-link/
├── checkout-link.html
├── README.md
└── server.py
```

## 环境要求

- Python 3.8 或更高版本
- 不需要安装第三方依赖

检查版本：

```bash
python --version
```

如果服务器上命令是 `python3`，后续命令也请把 `python` 替换为 `python3`。

## 本地运行

进入 Python 版本目录：

```bash
cd python-checkout-link
```

启动服务：

```bash
python server.py
```

默认监听：

```text
http://127.0.0.1:61314/checkout-link.html
```

服务实际绑定地址是 `0.0.0.0:61314`，所以局域网或服务器公网访问时可以使用对应主机 IP 或域名。

## 修改端口或监听地址

Linux/macOS：

```bash
PORT=61315 HOST=0.0.0.0 python server.py
```

Windows PowerShell：

```powershell
$env:PORT=61315
$env:HOST="0.0.0.0"
python server.py
```

然后访问：

```text
http://127.0.0.1:61315/checkout-link.html
```

## Linux 服务器部署

### 1. 安装 Python

Ubuntu/Debian：

```bash
sudo apt update
sudo apt install -y python3
python3 --version
```

### 2. 拉取代码

```bash
git clone https://github.com/550710418/teamsp.git
cd teamsp/python-checkout-link
```

### 3. 直接启动测试

```bash
python3 server.py
```

打开：

```text
http://服务器IP:61314/checkout-link.html
```

如果云服务器有安全组或防火墙，需要放行 TCP `61314` 端口。

### 4. 使用 systemd 常驻运行

创建服务文件：

```bash
sudo nano /etc/systemd/system/teamsp-python.service
```

写入以下内容，并把 `/opt/teamsp` 替换成你的实际项目路径：

```ini
[Unit]
Description=TeamSP Python Checkout Link Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/teamsp/python-checkout-link
Environment=HOST=127.0.0.1
Environment=PORT=61314
ExecStart=/usr/bin/python3 /opt/teamsp/python-checkout-link/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动并设置开机自启：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now teamsp-python
sudo systemctl status teamsp-python
```

查看日志：

```bash
journalctl -u teamsp-python -f
```

## Nginx 反向代理和 HTTPS

生产环境建议让 Python 服务只监听 `127.0.0.1`，再通过 Nginx 对外提供 HTTPS。

Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:61314;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置并重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

使用 Certbot 配置 HTTPS：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

最终访问：

```text
https://your-domain.com/checkout-link.html
```

## 使用步骤

1. 打开页面。
2. 粘贴你的 `accessToken`，可以直接粘贴纯 token，也可以粘贴 `Bearer xxx`。
3. 按需修改团队名称、席位数、付款周期、优惠码、国家和币种。
4. 点击「生成支付链接」。
5. 生成成功后点击「打开链接」或「复制链接」。

## 验证命令

语法检查：

```bash
python -m py_compile server.py
```

启动后检查页面：

```bash
curl -I http://127.0.0.1:61314/checkout-link.html
```

检查接口参数校验：

```bash
curl -s -X POST http://127.0.0.1:61314/api/checkout \
  -H "Content-Type: application/json" \
  -d "{}"
```

预期返回：

```json
{"error":"缺少 accessToken"}
```

## 安全提醒

- 不要把 `accessToken` 发给不可信的人。
- 不要把服务公开给陌生用户使用。
- 建议通过 HTTPS 访问页面。
- 建议在生产环境增加访问控制，例如 Nginx Basic Auth、IP 白名单或内网访问。
- 如果 token 已泄露，请立即重新登录并更换会话 token。
