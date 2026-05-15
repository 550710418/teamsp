#!/usr/bin/env python3
import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PORT = int(os.environ.get("PORT", "61314"))
HOST = os.environ.get("HOST", "0.0.0.0")
ROOT = Path(__file__).resolve().parent
HTML_PATH = ROOT / "checkout-link.html"
MAX_BODY_BYTES = 1024 * 1024
UPSTREAM_URL = "https://chatgpt.com/backend-api/payments/checkout"


def normalize_access_token(value):
    if value is None:
        return ""

    raw = str(value).strip()

    # If the user pasted a full JSON object, prefer the embedded accessToken.
    if raw.startswith("{") and "accessToken" in raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and parsed.get("accessToken"):
                raw = str(parsed["accessToken"]).strip()
        except json.JSONDecodeError:
            pass

    raw = re.sub(r"^Bearer\s+", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"^[\"']+|[\"',;\s]+$", "", raw).strip()
    return raw


def parse_json_text(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


class CheckoutHandler(BaseHTTPRequestHandler):
    server_version = "CheckoutLinkPython/1.0"

    def do_HEAD(self):
        self.send_html(include_body=False)

    def do_GET(self):
        self.send_html(include_body=True)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/checkout":
            self.send_json(404, {"error": "Not Found"})
            return

        try:
            body = self.read_request_body()
        except ValueError as exc:
            self.send_json(413, {"error": str(exc)})
            return

        try:
            parsed = json.loads(body.decode("utf-8") if body else "{}")
        except json.JSONDecodeError:
            self.send_json(400, {"error": "请求体不是合法 JSON"})
            return

        if not isinstance(parsed, dict):
            self.send_json(400, {"error": "请求体不是合法 JSON"})
            return

        access_token = normalize_access_token(parsed.get("accessToken", ""))
        payload = parsed.get("payload")

        if not access_token:
            self.send_json(400, {"error": "缺少 accessToken"})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "缺少 payload"})
            return

        self.forward_checkout_request(access_token, payload)

    def read_request_body(self):
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return b""

        try:
            size = int(content_length)
        except ValueError:
            raise ValueError("Content-Length 不合法")

        if size > MAX_BODY_BYTES:
            raise ValueError("Body too large")

        return self.rfile.read(size)

    def forward_checkout_request(self, access_token, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            UPSTREAM_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(access_token),
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                ),
                "Origin": "https://chatgpt.com",
                "Referer": "https://chatgpt.com/",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status = response.status
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            status = exc.code
            text = exc.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            self.send_json(502, {"error": "上游请求失败", "detail": str(exc.reason)})
            return

        data = parse_json_text(text)

        if status < 200 or status >= 300:
            error_message = None
            if isinstance(data, dict):
                error_message = data.get("error") or data.get("message")
            self.send_json(
                status,
                {
                    "error": error_message or "上游返回 HTTP {}".format(status),
                    "upstreamStatus": status,
                    "upstreamBody": data,
                },
            )
            return

        self.send_json(200, data)

    def send_html(self, include_body=True):
        try:
            body = HTML_PATH.read_bytes()
        except OSError as exc:
            self.send_json(500, {"error": str(exc)})
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), CheckoutHandler)
    print("checkout server listening on http://{}:{}".format(HOST, PORT), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
