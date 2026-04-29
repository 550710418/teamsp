import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const PORT = Number(process.env.PORT || 61314);
const HOST = '0.0.0.0';
const root = '/root/.openclaw/workspace-main';
const htmlPath = path.join(root, 'checkout-link.html');

function sendHtmlPage(res) {
  const html = fs.readFileSync(htmlPath);
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Content-Length': html.length,
    'Cache-Control': 'no-store'
  });
  res.end(html);
}

function sendJson(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store'
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk;
      if (data.length > 1024 * 1024) {
        reject(new Error('Body too large'));
        req.destroy();
      }
    });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function normalizeAccessToken(input) {
  if (input == null) return '';
  let raw = String(input).trim();

  // 如果用户粘贴了完整 JSON，优先提取 accessToken
  if (raw.startsWith('{') && raw.includes('accessToken')) {
    try {
      const parsed = JSON.parse(raw);
      if (parsed?.accessToken) raw = String(parsed.accessToken).trim();
    } catch {
      // ignore
    }
  }

  // 允许粘贴 "Bearer xxx"
  raw = raw.replace(/^Bearer\s+/i, '').trim();

  // 去掉常见多余字符（引号、逗号、分号）
  raw = raw.replace(/^["']+|["',;\s]+$/g, '').trim();

  return raw;
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', `http://${req.headers.host}`);

    if (req.method === 'GET' || req.method === 'HEAD') {
      // 节点/WebView 可能先发 HEAD 探测，再决定是否加载页面
      // 对所有 GET/HEAD 统一返回 200，避免 net::ERR_HTTP_RESPONSE_CODE_FAILURE
      if (req.method === 'HEAD') {
        const html = fs.readFileSync(htmlPath);
        res.writeHead(200, {
          'Content-Type': 'text/html; charset=utf-8',
          'Content-Length': html.length,
          'Cache-Control': 'no-store'
        });
        res.end();
        return;
      }

      sendHtmlPage(res);
      return;
    }

    if (req.method === 'POST' && url.pathname === '/api/checkout') {
      const raw = await readBody(req);
      let parsed;
      try {
        parsed = JSON.parse(raw || '{}');
      } catch {
        sendJson(res, 400, { error: '请求体不是合法 JSON' });
        return;
      }

      const accessToken = normalizeAccessToken(parsed.accessToken || '');
      const payload = parsed.payload;

      if (!accessToken) {
        sendJson(res, 400, { error: '缺少 accessToken' });
        return;
      }
      if (!payload || typeof payload !== 'object') {
        sendJson(res, 400, { error: '缺少 payload' });
        return;
      }

      const upstream = await fetch('https://chatgpt.com/backend-api/payments/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
          'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
          'Origin': 'https://chatgpt.com',
          'Referer': 'https://chatgpt.com/'
        },
        body: JSON.stringify(payload)
      });

      const text = await upstream.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { raw: text };
      }

      if (!upstream.ok) {
        sendJson(res, upstream.status, {
          error: data?.error || data?.message || `上游返回 HTTP ${upstream.status}`,
          upstreamStatus: upstream.status,
          upstreamBody: data
        });
        return;
      }

      sendJson(res, 200, data);
      return;
    }

    sendJson(res, 404, { error: 'Not Found' });
  } catch (err) {
    sendJson(res, 500, { error: err?.message || String(err) });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`checkout server listening on http://${HOST}:${PORT}`);
});
