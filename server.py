#!/usr/bin/env python3
"""
Local dev server for index.html
- Static file serving (HTML, CSV, etc.)
- Reverse proxy for Naver Geocoding API (bypasses CORS)
"""

import http.server
import urllib.request
import urllib.parse
import json
import sys
from http import HTTPStatus

# ====================================================
# Naver Geocoding API Credentials
# ====================================================
NAVER_CLIENT_ID     = '1r1kquageh'
NAVER_CLIENT_SECRET = 'zCFOuX6i1yzDoGaoPkDy7Ri6Xl6qTGBQgJFVuZGz'

PORT = 8080

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # ── Geocode proxy endpoint ──────────────────
        if parsed.path == '/api/geocode':
            params = urllib.parse.parse_qs(parsed.query)
            query  = params.get('q', [''])[0]

            if not query:
                self.send_error(400, 'Missing query parameter: q')
                return

            naver_url = (
                'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode'
                f'?query={urllib.parse.quote(query)}'
            )
            req = urllib.request.Request(naver_url, headers={
                'X-NCP-APIGW-API-KEY-ID': NAVER_CLIENT_ID,
                'X-NCP-APIGW-API-KEY':    NAVER_CLIENT_SECRET,
            })

            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    body = r.read()
            except Exception as e:
                print(f'[Geocode ERROR] {query}: {e}', flush=True)
                self.send_error(502, str(e))
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)

        # ── Static file serving ─────────────────────
        else:
            # 브라우저가 기본적으로 요청하는 favicon.ico가 없을 때 서버가 터지지 않게 무시
            if parsed.path == '/favicon.ico':
                self.send_response(204) # No Content
                self.end_headers()
                return
            super().do_GET()

    # 로그 출력 포맷 버그 수정
    def log_message(self, format, *args):
        # 파이썬 3.12+ 에서는 args[0]이 HTTPStatus 객체로 넘어올 수 있어 에러가 발생하므로, 문자열 변환 처리
        try:
            msg = format % args
            if '/api/' in msg:
                super().log_message(format, *args)
        except Exception:
            pass # 로그 출력 시 에러가 나더라도 서버는 다운되지 않게 패스

if __name__ == '__main__':
    server = http.server.HTTPServer(('', PORT), ProxyHandler)
    print(f'✅  Serving at  http://localhost:{PORT}/index.html')
    print(f'🌐  Geocode API at http://localhost:{PORT}/api/geocode?q=주소')
    print('Press Ctrl+C to stop.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')