#!/usr/bin/env python3
"""
antigravity-bambu-bridge: Local loopback bridge for seamless Bambu Studio handoff.
Runs as a lightweight background daemon to open 3D models with 0 LLM token cost.
"""

import http.server
import socketserver
import subprocess
import urllib.parse
import json
import os
import sys
import time
import platform

PORT = int(os.environ.get("BAMBU_BRIDGE_PORT", 48921))
DEFAULT_SLICER = os.environ.get("BAMBU_SLICER_APP", "/Applications/BambuStudio.app")
LAST_OPEN = {}

class BambuBridgeHandler(http.server.BaseHTTPRequestHandler):
    def end_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_cors_headers()

    def do_GET(self):
        global LAST_OPEN
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_cors_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "service": "bambu-bridge",
                "port": PORT,
                "slicer": DEFAULT_SLICER,
                "os": platform.system()
            }).encode('utf-8'))
            return

        if parsed.path == '/open':
            raw_path = params.get('file', [None])[0]
            if not raw_path:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_cors_headers()
                self.wfile.write(b'{"error": "Missing file parameter"}\n')
                return

            file_path = os.path.abspath(os.path.expanduser(urllib.parse.unquote(raw_path)))
            if not os.path.exists(file_path):
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_cors_headers()
                self.wfile.write(json.dumps({"error": f"File not found: {file_path}"}).encode('utf-8'))
                return

            # Debounce: prevent duplicate launches within 2 seconds
            now = time.time()
            last_time = LAST_OPEN.get(file_path, 0)
            if (now - last_time) < 2.0:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_cors_headers()
                self.wfile.write(b'{"status": "ok", "debounced": true}\n')
                return

            LAST_OPEN[file_path] = now

            # Cross-platform execution
            system = platform.system()
            ret_code = 0
            try:
                if system == "Darwin":
                    # macOS LaunchServices
                    res = subprocess.run(['/usr/bin/open', '-a', DEFAULT_SLICER, file_path], capture_output=True, text=True)
                    ret_code = res.returncode
                elif system == "Linux":
                    res = subprocess.run(['xdg-open', file_path], capture_output=True, text=True)
                    ret_code = res.returncode
                elif system == "Windows":
                    os.startfile(file_path)
                    ret_code = 0
                else:
                    ret_code = -1
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_cors_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_cors_headers()
            resp = {
                "status": "ok" if ret_code == 0 else "error",
                "file": file_path,
                "returncode": ret_code
            }
            self.wfile.write(json.dumps(resp).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Quiet background daemon logging
        pass

def main():
    socketserver.TCPServer.allow_reuse_address = True
    server_address = ('127.0.0.1', PORT)
    with socketserver.TCPServer(server_address, BambuBridgeHandler) as httpd:
        print(f"[bambu-bridge] Listening on http://127.0.0.1:{PORT}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[bambu-bridge] Shutting down cleanly.", flush=True)

if __name__ == '__main__':
    main()
