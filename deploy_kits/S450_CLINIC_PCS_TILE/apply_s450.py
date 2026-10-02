#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s450.py -- kit S450_CLINIC_PCS_TILE. Anchored edits on EXACT bytes, one file per run:

  finance   /root/finance/finance_app.py   022a9b0e (S449)  F1 the two pc-kit api paths in PUBLIC_PATHS (pc_kits.py
                                                            checks its own one-time code) · F2 the guarded mount ·
                                                            F3 the mounts row counts 27 parts
  portal    /root/portal/portal.py         ba61e35a (S444)  P1 the tile "Clinic PCs" (roles [], like Manage Users) ·
                                                            P2 its section, Admin · P3 the code fallback grant to manoj
  grants    /root/portal/tile_grants.json  392e6d89 (v31)   G1 "Clinic PCs" in manoj's extra · G2 version 32

    python3 -B apply_s450.py finance|portal|grants <path>     # edits in place; refuses unless the file is the FROM bytes
"""
import hashlib
import sys

SETS = {
    "finance": ("022a9b0e3b0b22e748a1283d53c2c201", [
        (b'''                "/finance/api/reception/report",           # S449
''', b'''                "/finance/api/reception/report",           # S449
                "/finance/api/pc-kit/fetch",               # S450: a PC's setup file fetches its kit; pc_kits.py checks its one-time code
                "/finance/api/pc-kit/enroll",              # S450
'''),
        (b'''    print("reception_door NOT mounted: %s" % _ex_m, file=sys.stderr)
# --- S449_RECEPTION_UPLOAD end ---
''', b'''    print("reception_door NOT mounted: %s" % _ex_m, file=sys.stderr)
# --- S449_RECEPTION_UPLOAD end ---
# --- S450_CLINIC_PCS_TILE begin -- the PC kits on the server, one card and one button per clinic PC (D660) ---
# The owner, 02-Oct-2026: "a server and a tile on my portal for all these kits ... by a very simple click, run and install
# the agent in that PC." /finance/pcs is his alone (the medical checker). The button hands the browser one small file
# with a one-time code; the file fetches the kit from this box and enrols that PC's new upload key (reception_door.py).
try:                                                          # S425: guarded, as every later mount (S209)
    import pc_kits                                                # noqa: E402
    pc_kits.init(app, db, require, _health_state)
except Exception as _ex_m:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('pc_kits', repr(_ex_m)[:200]))
    print("pc_kits NOT mounted: %s" % _ex_m, file=sys.stderr)
# --- S450_CLINIC_PCS_TILE end ---
'''),
        (b''''porders', 'packs', 'reception_door') if m not in sys.modules and m not in _mf]
        _all = 26
''', b''''porders', 'packs', 'reception_door', 'pc_kits') if m not in sys.modules and m not in _mf]
        _all = 27
'''),
    ]),
    "portal": ("ba61e35a9a2a2722d19304d791e255ca", [
        (b'''     "url": "https://followup.dr-manoj.in/portal/users",
     "roles": []},   # manoj-only: shown via USER_TILE_EXTRA + guarded by the route
''', b'''     "url": "https://followup.dr-manoj.in/portal/users",
     "roles": []},   # manoj-only: shown via USER_TILE_EXTRA + guarded by the route

    {"icon": "\\U0001F5A5\\uFE0F", "name": "Clinic PCs",
     # S450 NEW (owner, 02-Oct-2026, D660). Every clinic PC on one page: is it working, and one button that sets it
     # up again after a Windows reinstall -- the kit comes from this server, not from a Drive folder. Granted BY NAME
     # to manoj, like Manage Users; the page itself (/finance/pcs) is the medical checker's, so nobody else gets in.
     "desc": "Is each PC working \\u00b7 set one up again after a Windows reinstall", "live": True,
     "url": "/finance/pcs",
     "roles": []},
'''),
        (b'''    "Manage Users": "Admin",
}
''', b'''    "Manage Users": "Admin",
    "Clinic PCs": "Admin",
}
'''),
        (b'''    "manoj": {"Manage Users"},
''', b'''    "manoj": {"Manage Users", "Clinic PCs"},
'''),
    ]),
    "grants": ("392e6d89b09bcc7127cc541224771206", [
        (b'''    "manoj": {
      "extra": [
        "Clinic",
''', b'''    "manoj": {
      "extra": [
        "Clinic",
        "Clinic PCs",
'''),
        (b'''  "version": 31,
''', b'''  "version": 32,
'''),
    ]),
}


def main(which, path):
    frm, edits = SETS[which]
    raw = open(path, "rb").read()
    if hashlib.md5(raw).hexdigest() != frm:
        print("REFUSED: %s is %s, not the FROM bytes %s" % (path, hashlib.md5(raw).hexdigest(), frm))
        return 1
    for i, (old, new) in enumerate(edits, 1):
        if raw.count(old) != 1:
            print("REFUSED: %s anchor %d occurs %d times, not once" % (which, i, raw.count(old)))
            return 1
        raw = raw.replace(old, new)
    with open(path, "wb") as fh:
        fh.write(raw)
    print("applied %d edit(s) to %s -> %s" % (len(edits), which, hashlib.md5(raw).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
