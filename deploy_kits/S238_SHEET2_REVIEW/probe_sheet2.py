#!/usr/bin/env python3
"""probe_sheet2.py -- kit S238_SHEET2_REVIEW. Run by the installer BEFORE anything
is replaced. Computes the month with the LIVE salary_policy.py and with the NEW one
-- EACH IN ITS OWN PROCESS (F-414: two versions of one module inside one process
gave false differences) -- using the service's own environment, read-only, exactly
as opening the salary page does. Prints each person's Advance and net, live and new.
v1.9 changes wording and print only, so the Advance must be identical and any net
difference must be the hold threshold alone; renders every sheet from the new result.
   usage: probe_sheet2.py <new salary_policy.py> <live salary_policy.py> <YYYY-MM>
   (internal: probe_sheet2.py --one <salary_policy.py> <YYYY-MM> <render 0|1>)"""
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

if len(sys.argv) > 1 and sys.argv[1] == "--one":
    _env()
    p, ym, render = sys.argv[2], sys.argv[3], sys.argv[4] == "1"
    spec = importlib.util.spec_from_file_location("salary_policy_probe", p)
    M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    r = M.compute(ym)
    out = {"staff": {s["name"]: {"adv": s["adv_ded"], "net": s["net"], "held": s.get("held", 0),
                                 "prior": s.get("prior_collect", 0), "release": s.get("release", 0)}
                     for s in r["staff"]},
           "closed": bool(r.get("ledger_closed")), "render": ""}
    if render:
        try:
            M.sheet1_html(r, print_=True); M.sheet2_html(r, doors=True)
            for sep in getattr(M, "SEPARATE_PAGES", []):
                M.sheet2_html(r, doors=True, staff=sep)
            M.sheets34_html(r)
            out["render"] = "ok"
        except Exception as e:
            out["render"] = "%s: %s" % (type(e).__name__, e)
    print("@@" + json.dumps(out))
    sys.exit(0)

new_p, live_p, ym = sys.argv[1], sys.argv[2], sys.argv[3]
if os.environ.get("S238_WALK"):
    print("walk mode: compute skipped (offline)"); sys.exit(0)
def run(p, render):
    cp = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--one", p, ym, render],
                        capture_output=True, text=True, timeout=240)
    line = [l for l in cp.stdout.splitlines() if l.startswith("@@")]
    if not line:
        print(cp.stdout[-800:], cp.stderr[-800:]); sys.exit("probe: an engine failed to compute")
    return json.loads(line[-1][2:])
old, new = run(live_p, "0"), run(new_p, "1")
fails = []
print("  %-11s %11s %11s   %11s %11s" % ("staff", "Advance NOW", "Advance NEW", "net NOW", "net NEW"))
for n, s in new["staff"].items():
    o = old["staff"].get(n, {})
    flag = ""
    if abs(s["adv"] - o.get("adv", 0)) > 0.01:
        flag = "   <-- ADVANCE CHANGED"; fails.append(n)
    elif abs(s["net"] - o.get("net", 0)) > 0.01:
        flag = "   (hold threshold 30%->20%: last month's hold now %s)" % (
            "cancelled" if s["release"] > o.get("release", 0) else "deducted")
    print("  %-11s %11.2f %11.2f   %11.2f %11.2f%s" % (n, o.get("adv", 0), s["adv"], o.get("net", 0), s["net"], flag))
print("  every sheet renders from the new result" if new["render"] == "ok" else "  RENDER FAILED: " + new["render"])
if new["render"] != "ok": fails.append("render")
print("sheet2 probe: %d failures" % len(fails))
sys.exit(1 if fails else 0)
