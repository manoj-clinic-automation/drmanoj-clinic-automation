#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_watchdog_s243.py -- S243_WATCHDOG_FINANCE
Reads the S204 base copy of /root/wa/clinic_watchdog.py (byte-identical to the
live pin 01ca6591...) and adds THREE units to the SERVICES list:
  clinic-finance.service, staff-register.service, assetapp.service
Nothing else changes. The watchdog's only check is `systemctl is-active`;
it has no HTTP-probe framework, so none is invented (see README).

Usage:  python3 patch_watchdog_s243.py [BASE] [OUT]
  BASE default: /tmp/kbv/deploy_kits/S204_VPS_LIVE/root__wa__clinic_watchdog.py
  OUT  default: ./clinic_watchdog.py
"""
import sys, hashlib, os

BASE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/kbv/deploy_kits/S204_VPS_LIVE/root__wa__clinic_watchdog.py"
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "clinic_watchdog.py")

EXPECTED_BASE_MD5 = "01ca6591a74ec8009bf9748fb7f480c2"

def md5(b):
    return hashlib.md5(b).hexdigest()

raw = open(BASE, "rb").read()
assert b"\r\n" not in raw, "base has CRLF; refusing"
old_md5 = md5(raw)
assert old_md5 == EXPECTED_BASE_MD5, "base md5 %s != expected %s" % (old_md5, EXPECTED_BASE_MD5)
src = raw.decode("utf-8")

# --- edit 1: append the three new units at the end of SERVICES ---
old = '    ("staff-ledger.service",             "Staff ledger (salary/money app)",  "systemctl restart staff-ledger"),\n]\n'
new = ('    ("staff-ledger.service",             "Staff ledger (salary/money app)",  "systemctl restart staff-ledger"),\n'
       '    # S243: three web apps added to the guard (finance / register / asset). Liveness only.\n'
       '    ("clinic-finance.service",           "Clinic finance app (port 8106)",   "systemctl restart clinic-finance"),\n'
       '    ("staff-register.service",           "Staff register app (port 8044)",   "systemctl restart staff-register"),\n'
       '    ("assetapp.service",                 "Asset register app (port 8030)",   "systemctl restart assetapp"),\n'
       ']\n')
assert src.count(old) == 1, "edit-1 anchor count != 1"
src = src.replace(old, new, 1)

for u in ("clinic-finance.service", "staff-register.service", "assetapp.service"):
    assert src.count('"%s"' % u) == 1, "%s should appear exactly once" % u

out = src.encode("utf-8")
assert b"\r\n" not in out
with open(OUT, "wb") as f:
    f.write(out)
new_md5 = md5(out)
print("base : %s  %s" % (old_md5, BASE))
print("new  : %s  %s" % (new_md5, OUT))
