#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_stub_s502.py -- the BUILD-TIME rendered check's stub server (the brief's section 4.6), run on the PC, never on the server.

    python -B render_stub_s502.py --html stockmatch.html --json state_darpan.json --port 8502

Serves Darpan's page at /finance/stockmatch and the walk's scratch-copy JSON at /finance/stockmatch/api/state (any query); everything
else 404; every POST 404 (nothing is written anywhere). A headless browser then renders the page at phone width and desktop and the
RENDERED TEXT is read -- not the source, whose head comment and CSS keep the old words on purpose.
"""
import argparse
import http.server
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--port", type=int, default=8502)
    a = ap.parse_args()
    html = open(a.html, "rb").read()
    body = json.dumps(json.load(open(a.json, encoding="utf-8"))).encode("utf-8")

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):                                             # noqa: N802
            p = self.path.split("?", 1)[0]
            if p == "/finance/stockmatch":
                data, ct = html, "text/html; charset=utf-8"
            elif p == "/finance/stockmatch/api/state":
                data, ct = body, "application/json"
            else:
                self.send_response(404); self.end_headers(); return
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):                                            # noqa: N802
            self.send_response(404); self.end_headers()

        def log_message(self, *args):
            pass
    print("render stub on http://127.0.0.1:%d/finance/stockmatch" % a.port)
    sys.stdout.flush()
    http.server.HTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
