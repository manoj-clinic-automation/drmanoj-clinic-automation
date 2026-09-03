#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_scanapp_tiles_s222.py -- S222: point the two scan-app tiles at the same origin.

Both tiles already exist and both already reach the right people. Neither one's role list, icon,
description or position changes here. Only the URL, from a foreign host to a path — which is the
whole difference between opening INSIDE the portal PWA and being thrown out of it into a browser
tab, because the app's scope is "/" on followup.dr-manoj.in.

    Scan Purchase   staff, manager    https://assets.dr-manoj.in/intake  ->  /scanapp/intake
    Asset Register  doctor, manager   https://assets.dr-manoj.in         ->  /scanapp

THE ONE THAT MATTERS IS THE FIRST. "Photograph a new bill -> get a stamp number" is the owner's
own description of what reception does all day -- *"they scan anything, a number is generated,
they write on scanned doc and everything is documented in backend"* -- and it is one of only two
tiles a staff member has that left the app. (The other is Attendance, parked by the owner
because its app pulls punches from the biometric machine.)

REQUIRES the app-side prefix patch to be live first: without it /scanapp is not a thing the scan
app answers to, and these tiles would point at nothing. The installer for the vhost refuses
unless the backend answers /scanapp/healthz, so the ordering is enforced there rather than here
-- but install this LAST all the same.

Target: /root/portal/portal.py   (live pin c89ffa9f619712929c2b81d6e1d98c17, the
        S222_PORTAL_ENTRY result)
Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/patch_portal_scanapp_tiles_s222.py
Offline:         PORTAL_PATH=./portal.py python3 -B patch_portal_scanapp_tiles_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('PORTAL_PATH', '/root/portal/portal.py')
MARK = "S222 SCANAPP TILES"
EXPECT_FROM = "c89ffa9f619712929c2b81d6e1d98c17"


A_OLD = '''    {"icon": "\\U0001F4E6", "name": "Asset Register",
     "desc": "Clinic assets & AMC", "live": True,
     "url": "https://assets.dr-manoj.in",
     "roles": ["doctor", "manager"]},
'''

A_NEW = '''    {"icon": "\\U0001F4E6", "name": "Asset Register",
     "desc": "Clinic assets & AMC", "live": True,
     # S222 SCANAPP TILES -- same origin, so it opens inside the app window
     # instead of throwing the user out to a browser tab. The subdomain still
     # works; nothing was retired.
     "url": "/scanapp",
     "roles": ["doctor", "manager"]},
'''

B_OLD = '''    {"icon": "\\U0001F4F7", "name": "Scan Purchase",
     "desc": "Photograph a new bill \\u2192 get a stamp number", "live": True,
     "url": "https://assets.dr-manoj.in/intake",
     "roles": ["staff", "manager"]},
'''

B_NEW = '''    {"icon": "\\U0001F4F7", "name": "Scan Purchase",
     "desc": "Photograph a new bill \\u2192 get a stamp number", "live": True,
     # S222 SCANAPP TILES -- THE ONE THAT MATTERS. This is what reception does
     # all day, and it was one of only two staff tiles that left the app.
     "url": "/scanapp/intake",
     "roles": ["staff", "manager"]},
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit("REFUSED: this file is %s, not the %s this kit was built against. "
                         "NOTHING was changed. This is the login system -- send me that hash "
                         "rather than forcing it." % (before, EXPECT_FROM))
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_scantiles_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s."
                         % (ex, bak))
    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    print("next     systemctl restart clinic-portal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
