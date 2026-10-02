#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s449.py -- kit S449_RECEPTION_UPLOAD. Four anchored edits on EXACT bytes to /root/finance/finance_app.py
(ac24fc5e..., read whole lines 244-300, 11787-11830, 12225-12625 and 12960-12985 from the 02-Oct 01:35 bundle):

  E1  PUBLIC_PATHS gains the two reception paths -- reception_door.py authenticates every request itself (Ed25519);
  E2  reception_door is mounted, guarded like every later mount (S209, S425);
  E3  /finance/health gains one row, "Reception PC", placed before the mounts row;
  E4  the mounts row counts 26 parts and names reception_door.

    python3 -B apply_s449.py <path to finance_app.py>      # edits in place; refuses unless the file is the FROM bytes
"""
import hashlib
import sys

FROM = "ac24fc5e4e312b0bf3718b42380d5e64"

E1_OLD = b'''                "/finance/api/supplier-msg/done",          # S407
'''
E1_NEW = b'''                "/finance/api/supplier-msg/done",          # S407
                "/finance/api/reception/heartbeat",        # S449: the reception PC's door; reception_door.py verifies its signature
                "/finance/api/reception/report",           # S449
'''
E2_OLD = b'''    print("marg_door NOT mounted: %s" % _ex_m, file=sys.stderr)
# --- S240_MARG_DOOR end ---
'''
E2_NEW = E2_OLD + b'''# --- S449_RECEPTION_UPLOAD begin -- the reception PC posts its heartbeat and the two Docterz reports straight here (D659) ---
# The owner, 02-Oct-2026: "direct upload from the reception PC to server". Until now both travelled through Google Drive
# on that PC alone. Signed with a key made on that PC (Ed25519); this box holds only the public half, reception_keys.txt.
# A report goes through docterz_pickup.take() -- the same door the Drive pickup uses -- so two roads count it once.
try:                                                          # S425: guarded, as every later mount (S209)
    import reception_door                                         # noqa: E402
    reception_door.init(app, db)
except Exception as _ex_m:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('reception_door', repr(_ex_m)[:200]))
    print("reception_door NOT mounted: %s" % _ex_m, file=sys.stderr)
# --- S449_RECEPTION_UPLOAD end ---
'''
E3_OLD = b'''    # ---- S425: PARTS OF THE FINANCE APP THAT DID NOT LOAD -------------------
'''
E3_NEW = b'''    # ---- S449: THE RECEPTION PC -----------------------------------------------
    # Its agent posts a heartbeat straight to this box every 5 minutes (reception_door.py). The age is measured on THIS
    # box's clock from when it ARRIVED; in the clinic day a silent PC is amber at 15 minutes and red at 45.
    try:
        sys.modules["reception_door"].health_row(add, setting, con)
    except Exception as ex:                                       # noqa: BLE001
        add("reception", "Reception PC", "info", "could not be read (%s)" % ex)

''' + E3_OLD
E4_OLD = b''''sale_check', 'stockmatch', 'porders', 'packs') if m not in sys.modules and m not in _mf]
        _all = 25
'''
E4_NEW = b''''sale_check', 'stockmatch', 'porders', 'packs', 'reception_door') if m not in sys.modules and m not in _mf]
        _all = 26
'''


def main(path):
    raw = open(path, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        print("REFUSED: %s is %s, not the FROM bytes %s" % (path, hashlib.md5(raw).hexdigest(), FROM))
        return 1
    for name, old, new in (("E1", E1_OLD, E1_NEW), ("E2", E2_OLD, E2_NEW), ("E3", E3_OLD, E3_NEW), ("E4", E4_OLD, E4_NEW)):
        if raw.count(old) != 1:
            print("REFUSED: anchor %s occurs %d times, not once" % (name, raw.count(old)))
            return 1
        raw = raw.replace(old, new)
    with open(path, "wb") as fh:
        fh.write(raw)
    print("applied E1-E4 -> %s" % hashlib.md5(raw).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
