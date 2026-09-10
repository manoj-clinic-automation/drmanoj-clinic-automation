#!/usr/bin/env python3
"""august_nets.py -- kit S238_RECONCILE_AUG2. READ-ONLY. Prints the month exactly as
the salary page computes it: the INSTALLED /root/staff_register/salary_policy.py,
loaded from its own folder (its settings and hold ledger live beside it), with the
service's environment. Per person: Advance, what happened to last month's hold, net.
   usage: august_nets.py [YYYY-MM]"""
import os, sys, shlex, subprocess
ym = sys.argv[1] if len(sys.argv) > 1 else "2026-08"
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
        sys.path.insert(0, d) if d == app else sys.path.append(d)
import salary_policy as M
r = M.compute(ym)
print("  %-11s %10s  %-52s %10s" % ("staff", "Advance", "last month's hold", "net"))
for s in r["staff"]:
    note = s.get("release_note") or "-"
    print("  %-11s %10.2f  %-52s %10.2f" % (s["name"], s["adv_ded"], note[:52], s["net"]))
print("  (improvement needed to cancel a hold: %s%%)" % M.load_settings().get("improve_pct"))
