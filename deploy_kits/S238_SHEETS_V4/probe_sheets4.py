#!/usr/bin/env python3
"""probe_sheets4.py -- kit S238_SHEETS_V4 (the F-414 fix: the copy under test reads the
LIVE settings, hold ledger and owner advance records, not its own empty folder). Run by the installer BEFORE anything
is replaced. Computes the month with the LIVE salary_policy.py and with the NEW one
-- EACH IN ITS OWN PROCESS (F-414: two versions of one module inside one process
gave false differences) -- using the service's own environment, read-only, exactly
as opening the salary page does. Prints each person's Advance and net, live and new.
v1.9 changes wording and print only, so the Advance must be identical and any net
difference must be the hold threshold alone; renders every sheet from the new result.
   v1.11 pays overtime (the net may rise by exactly the OT paid) and trims cover-day OT:
   every field must match except the new OT fields, and every net must be identical.
   usage: probe_sheets4.py <new salary_policy.py> <live salary_policy.py> <YYYY-MM>
   (internal: probe_sheets4.py --one <salary_policy.py> <YYYY-MM> <render 0|1>)"""
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
    LIVE = "/root/staff_register"          # F-414: BASE is the module's own folder
    if os.path.dirname(os.path.abspath(p)) != LIVE:
        M.BASE = LIVE
        M.SETTINGS_PATH = os.path.join(LIVE, "salary_policy_settings.json")
        M.SETTINGS_AUDIT = os.path.join(LIVE, "salary_policy_settings_audit.jsonl")
        M.HOLD_LEDGER = os.path.join(LIVE, "hold_ledger.jsonl")
    r = M.compute(ym)
    num = lambda st: {k: round(float(v), 2) for k, v in st.items()
                      if isinstance(v, (int, float)) and not isinstance(v, bool)}
    out = {"staff": {s["name"]: num(s) for s in r["staff"]},
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
NEWF = {"ot_min", "ot_rs", "ot_paid"}
print("  %-11s %11s %11s   %11s %11s   %7s %11s" % ("staff", "Advance NOW", "Advance NEW",
                                                  "net NOW", "net NEW", "OT min", "OT payable"))
for n, s in new["staff"].items():
    o = old["staff"].get(n, {})
    diff = sorted(k for k in set(s) | set(o) if k not in NEWF | {"net"}
                  and abs(s.get(k, 0) - o.get(k, 0)) > 0.01)
    # v1.11: overtime is PAID -- the net may rise by exactly the new OT paid, nothing else
    if abs((s.get("net", 0) - o.get("net", 0)) - (s.get("ot_paid", 0) - o.get("ot_paid", 0))) > 0.01:
        diff.append("net (by more than the overtime paid)")
    flag = ""
    if diff:
        flag = "   <-- CHANGED: " + ", ".join(diff); fails.append(n)
    print("  %-11s %11.2f %11.2f   %11.2f %11.2f   %7d %11.2f%s" % (
        n, o.get("adv_ded", 0), s.get("adv_ded", 0), o.get("net", 0), s.get("net", 0),
        s.get("ot_min", 0), s.get("ot_rs", 0), flag))
print("  every sheet renders from the new result" if new["render"] == "ok" else "  RENDER FAILED: " + new["render"])
if new["render"] != "ok": fails.append("render")
print("sheets probe: %d failures" % len(fails))
sys.exit(1 if fails else 0)
