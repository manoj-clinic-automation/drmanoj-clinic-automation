"""
t_liveconfig.py -- S219: the widget under the configurations that ACTUALLY drive
it in production, not the test host's defaults.

Why this exists. Every one of the seven live callers sets
`allowIdCard: false, allowBatch: false`:

    asset_register.py  /intake                     (reception bill scan)
    finance_app.py     day scan · noncash · expense · clinic day · clinic expense

...and the S207 suite ran with host.html's defaults, where BOTH are on. So the
whole of t_detect / t_hard / t_regress / t_layout proved a configuration no live
surface uses. A green selftest proves the kit, not the join (S208/S209).

This drives the real shapes and asserts the widget still comes up whole, on a
phone, with nothing thrown and every control thumb-sized.

USAGE: python3 -B t_liveconfig.py [scanner_widget.js]
"""
from playwright.sync_api import sync_playwright
import json
import pathlib as _pl
import sys

HERE = _pl.Path(__file__).resolve().parent
WIDGET = sys.argv[1] if len(sys.argv) > 1 else "scanner_widget.js"

FAKE_CAM = (HERE / "t_layout.py").read_text(encoding="utf-8").split('FAKE_CAM = r"""')[1].split('"""')[0]

# the live configurations, copied from the callers
LIVE = [
    ("asset intake (reception)", {
        "title": "\U0001F4F7 Scan the bill", "uploadUrl": "/intake/scan_submit",
        "fileField": "bill_scan", "uploadFields": {}, "nameBase": "bill",
        "backUrl": "/intake/slip/last", "allowIdCard": False, "allowBatch": False}),
    ("finance day scan", {
        "title": "\U0001F4F7 Scan", "uploadUrl": "/finance/api/day/2026-09-02/scan/marg",
        "fileField": "file", "uploadFields": {}, "nameBase": "day",
        "backUrl": "/finance/daily", "allowIdCard": False, "allowBatch": False}),
    ("finance expense scan", {
        "title": "\U0001F4F7 Scan the bill", "uploadUrl": "/finance/api/day/2026-09-02/expense-scan/7",
        "fileField": "file", "uploadFields": {}, "nameBase": "expense",
        "backUrl": "/finance/daily", "allowIdCard": False, "allowBatch": False}),
    ("clinic day scan", {
        "title": "\U0001F4F7 Scan", "uploadUrl": "/finance/clinic/api/day/2026-09-02/scan/bank",
        "fileField": "file", "uploadFields": {}, "nameBase": "clinic",
        "backUrl": "/finance/clinic/daily", "allowIdCard": False, "allowBatch": False}),
]

HOST = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>body{font-family:system-ui,Arial;margin:0;background:#f4f6fb;color:#222}
main{padding:12px}.card{background:#fff;border:1px solid #d5deee;border-radius:6px;padding:12px;margin-bottom:12px}
button,.btn{background:#1f3864;color:#fff;border:0;padding:8px 16px;border-radius:4px;cursor:pointer;display:inline-block;font-size:14px}
.btn.small{padding:3px 9px;font-size:12px}.muted{color:#888;font-size:12px}</style></head><body>
<main><div id=scanroot></div></main>
<script>window.jspdf={jsPDF:function(){return{addImage:function(){},addPage:function(){},save:function(){},
output:function(){return new Blob(["pdf"],{type:"application/pdf"});},
internal:{pageSize:{getWidth:function(){return 210;},getHeight:function(){return 297;}}}};}};</script>
<script>window.SCANNER_CONFIG = __CFG__;</script>
<script src="__W__"></script></body></html>"""

checks = []
def ck(n, c):
    checks.append((n, bool(c)))

with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-fake-ui-for-media-stream"])
    for label, cfg in LIVE:
        page_html = HOST.replace("__CFG__", json.dumps(cfg)).replace("__W__", WIDGET)
        f = HERE / ("_lc_%s.html" % abs(hash(label)))
        f.write_text(page_html, encoding="utf-8")
        pg = b.new_page(viewport={"width": 390, "height": 780})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f.as_uri())
        pg.wait_for_timeout(350)
        ck("%s — widget rendered" % label,
           pg.evaluate("document.querySelector('#scanroot').children.length > 0"))
        ck("%s — nothing threw" % label, not errs)
        # the disallowed modes must NOT be offered
        modes = pg.evaluate("""() => Array.from(document.querySelectorAll('input[type=radio]'))
                                     .map(r => r.value)""")
        ck("%s — id-card mode not offered" % label, "idcard" not in modes)
        ck("%s — batch mode not offered" % label, "batch" not in modes)
        # every control still thumb-sized
        small = pg.evaluate("""() => Array.from(document.querySelectorAll('#scanroot button, #scanroot .btn, #scanroot label'))
            .filter(e => { const r = e.getBoundingClientRect();
                           return r.height > 0 && r.height < 44 && e.offsetParent !== null; })
            .map(e => (e.textContent||'').trim().slice(0,24))""")
        ck("%s — no control under 44px (%s)" % (label, small or "none"), not small)
        # the config the caller set must survive into the widget
        ck("%s — uploadUrl preserved" % label,
           pg.evaluate("window.SCANNER_CONFIG.uploadUrl") == cfg["uploadUrl"])
        ck("%s — fileField preserved" % label,
           pg.evaluate("window.SCANNER_CONFIG.fileField") == cfg["fileField"])
        # the page-injected extra field pattern (how the Note reaches the server)
        pg.evaluate("window.SCANNER_CONFIG.uploadFields.note='2 boxes'")
        ck("%s — page can inject an upload field (the Note pattern)" % label,
           pg.evaluate("window.SCANNER_CONFIG.uploadFields.note") == "2 boxes")
        pg.close()
        f.unlink()
    b.close()

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print("  %s  %s" % ("ok  " if ok else "FAIL", n))
print("\n%d/%d checks passed" % (len(checks) - len(bad), len(checks)))
print("LIVE-CONFIG " + ("GREEN" if not bad else "RED"))
sys.exit(1 if bad else 0)
