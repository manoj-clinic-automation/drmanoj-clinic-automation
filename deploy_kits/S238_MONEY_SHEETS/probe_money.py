#!/usr/bin/env python3
"""probe_money.py -- S238_MONEY_SHEETS. Run by the installer BEFORE anything is
replaced. Computes the month with the LIVE salary_policy.py and with the NEW one,
side by side, using the service's own environment -- exactly what opening the
salary page does (read-only) -- and renders every sheet from the new result.
Prints, per person, the Advance deduction before and after, and what the staff
ledger itself recorded for the month. Fails if the new Advance differs from the
ledger's record for anyone, or if any sheet fails to render.
   usage: probe_money.py <new salary_policy.py> <live salary_policy.py> <YYYY-MM>"""
import os, sys, shlex, subprocess, importlib.util, json
new_p, live_p, ym = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    envtxt = subprocess.run(["systemctl", "show", "-p", "Environment", "--value", "staff-register"],
                            capture_output=True, text=True, timeout=10).stdout.strip()
    for kv in shlex.split(envtxt):
        if "=" in kv:
            k, v = kv.split("=", 1); os.environ.setdefault(k, v)
except Exception:
    pass
app_dir = "/root/staff_register"
os.environ.setdefault("ATT_REGISTER_DB", os.environ.get("SR_DB_PATH", os.path.join(app_dir, "staff_register.db")))
for d in (app_dir, "/root", os.environ.get("SALARY_ATT_DIR", "")):
    if d and os.path.isdir(d) and d not in sys.path:
        sys.path.append(d)
def load(p, n):
    spec = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
fails = []
NEW = load(new_p, "salary_policy_new")
if os.environ.get("S238_WALK"):
    print("walk mode: compute skipped (offline); module loaded"); sys.exit(0)
OLD = load(live_p, "salary_policy_live")
r_old, r_new = OLD.compute(ym), NEW.compute(ym)
import staff_ledger as L
rows = L.load_ledger()
rec = {}
for x in rows:
    if (x.get("closed_month") == ym and x.get("status") == "APPROVED"
            and x.get("category") in ("ADVANCE_INSTALMENT", "LOAN_INTEREST")):
        rec[x["staff"]] = rec.get(x["staff"], 0) - float(x["amount"])
old_by = {s["name"]: s for s in r_old["staff"]}
print("  %-10s %14s %14s %14s   %10s %10s" % ("staff", "Advance NOW", "Advance NEW", "ledger says", "net NOW", "net NEW"))
for s in r_new["staff"]:
    o = old_by.get(s["name"], {})
    led = round(rec.get(s["name"], 0), 2)
    flag = "" if abs(s["adv_ded"] - led - float(s.get("manual_adv") or 0)) < 0.01 else "   <-- DIFFERS FROM THE LEDGER"
    if flag: fails.append(s["name"])
    print("  %-10s %14s %14s %14s   %10s %10s%s" % (s["name"], NEW.money(o.get("adv_ded", 0)), NEW.money(s["adv_ded"]),
          NEW.money(led), NEW.money(o.get("net", 0)), NEW.money(s["net"]), flag))
print("  ledger closed for %s: %s" % (ym, "yes" if r_new.get("ledger_closed") else "NO — the Lock will refuse until it is"))
try:
    NEW.sheet1_html(r_new, print_=True); NEW.sheet2_html(r_new, doors=True)
    for sep in getattr(NEW, "SEPARATE_PAGES", []):
        NEW.sheet2_html(r_new, doors=True, staff=sep)
    NEW.sheets34_html(r_new)
    print("  every sheet renders from the new result")
except Exception as e:
    fails.append("render: %s: %s" % (type(e).__name__, e))
for f in fails: print("  FAIL: " + str(f))
print("money probe: %d failures" % len(fails))
sys.exit(1 if fails else 0)
