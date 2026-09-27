#!/usr/bin/env python3
"""Serve a directory under an arbitrary CSP + CORP header set so you can
determine what a target render origin will allow BEFORE publishing megabytes.

Why this exists: the DRA Content render origin (view.content.ahfl.in) serves
artifacts with a `sandbox` CSP directive (no allow-same-origin => opaque origin)
plus `Cross-Origin-Resource-Policy: same-site`. Under that combination, external
stylesheets, external scripts and self-hosted images are ALL blocked while inline
<style> and data: URIs still work. Probing locally with the exact headers turned
a 3-MB republish gamble into a 30-second deterministic answer.

Usage:
  python3 csp_probe.py [DIR] [--port 8901]

Defaults:
  DIR        = ./csp_test   (generates a small probe page there unless
                             CSP_GENERATE=0 is set, in which case it serves the
                             directory as-is -- use this for a real build dir)
  headers    = the DRA Content set by default; override with env vars:
               CSP_HEADER  (full CSP string)
               CORP_HEADER (e.g. "same-site" or empty to disable)

Then load http://127.0.0.1:PORT/index.html in a browser and read:
  - body background color        -> external CSS applied? (probe uses #004400)
  - #jsmark text                 -> external JS ran? (expected JS_RAN)
  - #inlinemark color            -> inline <style> applied? (expected green)
  - #imgdata naturalWidth        -> data: URI image? (expected 2)
  - #imgself naturalWidth        -> self-hosted image? (expected 2, 0 = blocked)
or run in a headless context and evaluate getComputedStyle() values.

Stdlib only. Prints no credentials. Test page generation is guarded so it can
never clobber a real build's index.html -- set CSP_GENERATE=0 when DIR is a
build directory.
"""
import http.server
import socketserver
import os
import sys

DEFAULT_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; font-src 'self'; media-src 'self'; "
    "connect-src 'self' https://content.ahfl.in; form-action 'none'; "
    "base-uri 'none'; object-src 'none'; frame-ancestors 'self'; "
    "sandbox allow-scripts allow-popups allow-downloads allow-modals"
)

CSP = os.environ.get("CSP_HEADER", DEFAULT_CSP)
CORP = os.environ.get("CORP_HEADER", "same-site")  # "" disables

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "csp_test")
PORT = int(os.environ.get("PORT", os.environ.get("PROBE_PORT", "8901")))
os.makedirs(ROOT, exist_ok=True)

GENERATE = os.environ.get("CSP_GENERATE", "1") == "1"
if GENERATE:
    TINY = ("data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR4nGP8z8DA"
            "wMDAwMDEAAASZgHhCJvS6AAAAABJRU5ErkJggg==")
    open(f"{ROOT}/ext.css", "w").write("/* external css probe */ body{background:#004400}")
    open(f"{ROOT}/ext.js", "w").write(
        "document.addEventListener('DOMContentLoaded',function(){"
        "document.getElementById('jsmark').textContent='JS_RAN';});"
    )
    import base64
    open(f"{ROOT}/self.png", "wb").write(base64.b64decode(TINY.split(",", 1)[1]))
    open(f"{ROOT}/index.html", "w").write(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<link rel='stylesheet' href='ext.css'>"
        "<style>body{font-family:monospace;padding:20px}#inlinemark{color:#00ff00}"
        ".box{border:3px solid #ff0;padding:6px;margin:6px 0}</style>"
        "</head><body><div class='box'>TEST PAGE</div>"
        "<p>external css applied (body bg #004400)?</p>"
        "<p id='inlinemark'>INLINE_STYLE_TARGET</p>"
        "<p id='jsmark'>JS_DID_NOT_RUN</p>"
        f"<p>img data uri: <img id='imgdata' src='{TINY}' width='40' height='40'></p>"
        "<p>img self: <img id='imgself' src='self.png' width='40' height='40'></p>"
        "<script src='ext.js'></script></body></html>"
    )


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        if CORP:
            self.send_header("Cross-Origin-Resource-Policy", CORP)
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, *a):
        pass


print(f"serving {ROOT} on :{PORT}")
print(f"CSP:  {CSP}")
print(f"CORP: {CORP or '(disabled)'}")
with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
    httpd.serve_forever()