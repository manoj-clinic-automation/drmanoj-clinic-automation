#!/usr/bin/env python3
"""probe_parttime_pay.py -- kit S239_PARTTIME_PAY. Run by the installer BEFORE anything is
replaced. Computes the month with the LIVE salary_policy.py and the NEW one, each in its own
process (F-414), with the live settings. v1.16: part-time staff (dates_only_staff) pay no leave
charge. Every figure of every other person must be identical; for part-time staff only the leave
amount, the two absence fines, the deductions and the net may move -- and the net by exactly the
charges removed. Prints the part-time person's net before and after.
   usage: probe_parttime_pay.py <new salary_policy.py> <live salary_policy.py> <YYYY-MM>"""
import os, sys, shlex, subprocess, importlib.util, json, re

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

def _table(h):
    i = h.find("All fines, leaves")
    if i < 0:
        return []
    sec = h[i:]; sec = sec[:sec.index("</table>")]
    rows = re.findall(r"<tr>(.*?)</tr>", sec, re.S)[2:]
    return [[re.sub("<[^>]+>", "", c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r)] for r in rows]

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
    h = M.sheet2_html(r, doors=True)
    for sep in getattr(M, "SEPARATE_PAGES", []):
        M.sheet2_html(r, doors=True, staff=sep)
    s1 = M.sheet1_html(r, print_=True); M.sheets34_html(r)
    pt = sorted(M.dates_only_names(r["settings"]))
    print("@@" + json.dumps({"staff": {s["name"]: num(s) for s in r["staff"]}, "rows": _table(h),
                             "pt": pt, "sec": "Part-time staff" in h,
                             "ptrows": len(re.findall(r"<tr><td>\d\d-[A-Z][a-z]{2}</td>", h))}))
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
MAY = {"leave_amt", "fine_uninf", "fine_exc", "deductions", "net"}
if not new["pt"]:
    fails.append("no part-time staff named in the setting dates_only_staff")
for n, s in new["staff"].items():
    o = old["staff"].get(n, {})
    if n.strip().lower() not in new["pt"]:
        if s != o:
            fails.append("%s: a figure changed (only part-time staff may move)" % n)
        continue
    moved = sorted(k for k in set(s) | set(o) if abs(s.get(k, 0) - o.get(k, 0)) > 0.005)
    bad = [k for k in moved if k not in MAY]
    if bad:
        fails.append("%s: unexpected change in %s" % (n, ", ".join(bad)))
    if s.get("leave_amt", 0) or s.get("fine_uninf", 0) or s.get("fine_exc", 0):
        fails.append("%s: a leave charge is still there" % n)
    removed = o.get("leave_amt", 0) + o.get("fine_uninf", 0) + o.get("fine_exc", 0)
    if abs((s.get("net", 0) - o.get("net", 0)) - removed) > 0.01:
        fails.append("%s: the net did not rise by exactly the charges removed" % n)
    print("  %s: leave charge %.2f -> 0 · net %.2f -> %.2f (base %.2f)"
          % (n, removed, o.get("net", 0), s.get("net", 0), s.get("base", 0)))
if fails:
    print("PROBE RED:"); [print("   " + f) for f in fails]; sys.exit(1)
print("PROBE GREEN: only part-time pay moved, by exactly the leave charge removed")
