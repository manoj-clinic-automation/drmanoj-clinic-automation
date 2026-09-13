#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_watchdog_s243.py -- parses the new clinic_watchdog.py (AST, no execution,
no network, no systemctl) and asserts:
  * the 11 original units are still present, exactly once each
  * the 3 new units are present, exactly once each
  * SERVICES has exactly 14 entries, all 3-tuples of strings
  * nothing outside the SERVICES list changed versus the base (if base is given)
Usage: python3 selftest_watchdog_s243.py [NEW_FILE] [BASE_FILE]
"""
import sys, ast, os, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
NEW  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "clinic_watchdog.py")
BASE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/kbv/deploy_kits/S204_VPS_LIVE/root__wa__clinic_watchdog.py"

ORIGINAL_11 = [
    "wa-receiver.service", "wa-send-api.service", "wa-notifier.service",
    "call-api.service", "call-hook.service", "clinic-portal.service",
    "gutlog.service", "clinic-followup-receiver.service",
    "attendance-dashboard.service", "attlistener.service", "staff-ledger.service",
]
NEW_3 = ["clinic-finance.service", "staff-register.service", "assetapp.service"]

def services_from(path):
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "SERVICES" for t in node.targets):
            vals = ast.literal_eval(node.value)
            return vals
    raise AssertionError("SERVICES not found in %s" % path)

fails = 0
def check(cond, msg):
    global fails
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        fails += 1

svc = services_from(NEW)
units = [s[0] for s in svc]
check(len(svc) == 14, "SERVICES has 14 entries (got %d)" % len(svc))
check(all(isinstance(s, tuple) and len(s) == 3 and all(isinstance(x, str) for x in s) for s in svc),
      "every entry is a (unit, label, fix) tuple of strings")
for u in ORIGINAL_11:
    check(units.count(u) == 1, "original unit present once: %s" % u)
for u in NEW_3:
    check(units.count(u) == 1, "new unit present once: %s" % u)
check(units[:11] == ORIGINAL_11, "original 11 keep their order at the top of the list")
check(len(set(units)) == len(units), "no duplicate units")

if os.path.exists(BASE):
    a = open(BASE, encoding="utf-8").read().splitlines()
    b = open(NEW,  encoding="utf-8").read().splitlines()
    added = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l.startswith("-") and not l.startswith("---")]
    check(len(removed) == 0, "no lines removed versus base (removed=%d)" % len(removed))
    check(len(added) == 4, "exactly 4 lines added versus base (added=%d)" % len(added))
    check(all(("S243" in l) or any(u in l for u in NEW_3) for l in added),
          "every added line is the S243 comment or one of the 3 new units")
else:
    print("SKIP  base file not present; diff check skipped")

check(b"\r\n" not in open(NEW, "rb").read(), "LF line endings")
print("RESULT: %s (%d failures)" % ("OK" if fails == 0 else "FAILED", fails))
sys.exit(1 if fails else 0)
