#!/usr/bin/env python3
"""probe_sheet2_cover.py -- kit S239_SHEET2_COVER1. Run by the installer BEFORE anything is replaced.
Computes the month with the LIVE salary_policy.py and with the NEW one, each in its own process
(F-414), with the LIVE settings, and renders Sheet 2's all-staff table from both. v1.13 is DISPLAY
ONLY: every number the engine computes must be identical; the two Cover duty columns (days, Rs)
become one ("Rs (days)"); every other cell must match.
   usage: probe_sheet2_cover.py <new salary_policy.py> <live salary_policy.py> <YYYY-MM>"""
import os, sys, shlex, subprocess, importlib.util, json

def _env():
    try:
        t = subprocess.run(["systemctl", "show", "-p", "Environment", "--value", "staff-register"],
                           capture_output=True, text=True, timeout=10).stdout.strip()
        for kv in shlex.split(t):
            if "=" in kv:
                k, v = kv.split("=", 1); os.environ.setdefault(k, v)
    except Exception:
        pass
    app = "/root/staff_register"
    os.environ.setdefault("ATT_REGISTER_DB", os.environ.get("SR_DB_PATH", os.path.join(app, "staff_register.db")))
    for d in (app, "/root", os.environ.get("SALARY_ATT_DIR", "")):
        if d and os.path.isdir(d) and d not in sys.path:
            sys.path.append(d)

import re

def _table(h):
    i = h.find("All fines, leaves")
    if i < 0:
        return None, []
    sec = h[i:]; sec = sec[:sec.index("</table>")]
    rows = re.findall(r"<tr>(.*?)</tr>", sec, re.S)[2:]
    return sec, [[re.sub("<[^>]+>", "", c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r)] for r in rows]

if len(sys.argv) > 1 and sys.argv[1] == "--one":
    _env()
    p, ym = sys.argv[2], sys.argv[3]
    spec = importlib.util.spec_from_file_location("salary_policy_probe", p)
    M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    LIVE = "/root/staff_register"
    if os.path.dirname(os.path.abspath(p)) != LIVE:
        M.BASE = LIVE
        M.SETTINGS_PATH = os.path.join(LIVE, "salary_policy_settings.json")
        M.SETTINGS_AUDIT = os.path.join(LIVE, "salary_policy_settings_audit.jsonl")
        M.HOLD_LEDGER = os.path.join(LIVE, "hold_ledger.jsonl")
    r = M.compute(ym)
    num = lambda st: {k: round(float(v), 2) for k, v in st.items()
                      if isinstance(v, (int, float)) and not isinstance(v, bool)}
    sec, rows = _table(M.sheet2_html(r, doors=True))
    for sep in getattr(M, "SEPARATE_PAGES", []):
        M.sheet2_html(r, doors=True, staff=sep)
    M.sheet1_html(r, print_=True); M.sheets34_html(r)
    print("@@" + json.dumps({"staff": {s["name"]: num(s) for s in r["staff"]},
                             "two": bool(sec and "<th>days</th>" in sec),
                             "one": bool(sec and "Cover duty (+)<br>" in sec),
                             "rows": rows}))
    sys.exit(0)

new_p, live_p, ym = sys.argv[1], sys.argv[2], sys.argv[3]
def run(p):
    cp = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--one", p, ym],
                        capture_output=True, text=True, timeout=240)
    line = [l for l in cp.stdout.splitlines() if l.startswith("@@")]
    if not line:
        print(cp.stdout[-800:], cp.stderr[-800:]); sys.exit("probe: an engine failed to compute or render")
    return json.loads(line[-1][2:])
old, new = run(live_p), run(new_p)
fails = []
for n, s in new["staff"].items():
    o = old["staff"].get(n)
    if o != s:
        fails.append("%s: a computed figure changed" % n)
if not old["two"] or old["one"]:
    fails.append("the LIVE table is not the shape this kit was built against (v1.13)")
if new["two"] or not new["one"]:
    fails.append("the NEW table did not merge Cover duty into one column")
if len(old["rows"]) != len(new["rows"]):
    fails.append("row count differs")
print("  %-12s %14s" % ("staff", "cover Rs (days)"))
for a, b in zip(old["rows"], new["rows"]):
    exp = "-" if a[-1] == "-" else "%s (%s)" % (a[-1], a[-2])
    if a[:-2] != b[:-1] or b[-1] != exp:
        fails.append("%s: a cell changed" % a[0])
    print("  %-12s %14s" % (b[0], b[-1]))
if fails:
    print("PROBE RED:"); [print("   " + f) for f in fails]; sys.exit(1)
print("PROBE GREEN: display only -- every figure identical; Cover duty is one column")
