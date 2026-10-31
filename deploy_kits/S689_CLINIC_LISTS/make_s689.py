#!/usr/bin/env python3
"""make_s689.py -- kit S689_CLINIC_LISTS (01-Nov-2026, the parent, session 373). Builds the TO files from the FROM files.

    python3 -B make_s689.py <root> <outdir>     -> <outdir>/finance/{finance_app.py, clinic_lists.py}, <outdir>/portal/portal.py

<root> holds finance/finance_app.py and portal/portal.py as they are on the box (their md5 must be FROM below, or STOP).
finance/clinic_lists.py is NOT there yet. Every edit is anchored on text found EXACTLY once, or nothing is written:
  finance_app.py   1 edit  -- the clinic_lists mount block, after the S688_XRAY_FILM_LOG block (nothing else)
  portal.py        2 edits -- the tile "X-ray & procedures" before "Kal ke procedures"; its group (Patients) in _TILE_GROUP
  clinic_lists.py  NEW     -- copied from the kit beside this script
tile_grants.json is NOT changed: the tile is roles ['doctor']; Dr Bhawna's "only" list keeps it off her home, and the page
itself refuses every login but manoj.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"finance/finance_app.py": "2f604fee8ae7e69af670c55a13592fce",
        "portal/portal.py": "1a9b3a1b7460cf11171d5f6b6e376a48"}
NEW = "finance/clinic_lists.py"

MOUNT_ANCHOR = "# --- S688_XRAY_FILM_LOG end ---\n"
MOUNT = MOUNT_ANCHOR + '''
# --- S689_CLINIC_LISTS begin -- the owner's X-ray & procedures page: two lists from 1-Oct, search, Excel (owner, 01-Nov-2026, D812) ---
# PARENT. Paths /finance/slips/lists... -- unit 'slips' by _unit_for_path; inside, ONLY the login manoj (every other login 403).
# Writes nothing (no table, no audit row); reads slip / slip_item / owner_service / clinic_day_line, patient names by slip_log,
# film sizes by xray_film. GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import clinic_lists                                        # noqa: E402
    clinic_lists.init(app, db, require, audit, unit="slips")
except Exception as _ex_cl:                                    # noqa: BLE001
    _MOUNT_FAILED.append(('clinic_lists', repr(_ex_cl)[:200]))
    print("clinic_lists NOT mounted: %s" % _ex_cl, file=sys.stderr)
# --- S689_CLINIC_LISTS end ---
'''

TILE_ANCHOR = '    {"icon": "\\U0001FA79", "name": "Kal ke procedures",\n'
TILE = '''    {"icon": "\\U0001F4CA", "name": "X-ray & procedures",
     # S689 NEW (owner, 01-Nov-2026, D812). His own X-ray list and procedures list from 1-Oct-2026: amounts, a month or a
     # from-to range, a search box (patient, clinic ID, slip no., procedure), Docterz-only charges, Excel. The page is his alone:
     # the server refuses every other login. Dr Bhawna's "only" list in tile_grants.json keeps it off her home.
     "desc": "X-ray & procedure lists \\u00b7 search \\u00b7 Excel",
     "live": True,
     "url": "/finance/slips/lists",
     "roles": ["doctor"]},
''' + TILE_ANCHOR

GROUP_ANCHOR = '    "Patient records": "Patients", "Check karein": "Patients", "Report baaki": "Patients",\n'
GROUP = GROUP_ANCHOR + '    "X-ray & procedures": "Patients",                                                        # S689 (D812)\n'


def md5b(b):
    return hashlib.md5(b).hexdigest()


def rep(text, old, new, what, edits):
    n = text.count(old)
    if n != 1:
        raise SystemExit("make_s689: %s: anchor found %d times (must be exactly once) -- STOP, nothing written" % (what, n))
    edits.append(what)
    print("edit ok: %s" % what)
    return text.replace(old, new)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, outdir = sys.argv[1], sys.argv[2]
    got = {}
    for f, want in FROM.items():
        b = open(os.path.join(root, f), "rb").read()
        if md5b(b) != want:
            raise SystemExit("make_s689: %s is %s, not the FROM %s -- STOP, nothing written" % (f, md5b(b), want))
        got[f] = b.decode("utf-8")
    if os.path.exists(os.path.join(root, NEW)):
        raise SystemExit("make_s689: %s already exists on the root -- STOP" % NEW)
    cl = open(os.path.join(HERE, "clinic_lists.py"), "rb").read()
    edits = []
    a = got["finance/finance_app.py"]
    if "S689_CLINIC_LISTS" in a or "import clinic_lists" in a:
        raise SystemExit("make_s689: finance_app.py already names clinic_lists -- STOP")
    a = rep(a, MOUNT_ANCHOR, MOUNT, "finance_app.py: the mount block after S688", edits)
    compile(a, "finance_app.py", "exec")
    p = got["portal/portal.py"]
    if '"X-ray & procedures"' in p:
        raise SystemExit("make_s689: portal.py already has the tile -- STOP")
    p = rep(p, TILE_ANCHOR, TILE, "portal.py: the tile before Kal ke procedures", edits)
    p = rep(p, GROUP_ANCHOR, GROUP, "portal.py: the tile's group (Patients)", edits)
    compile(p, "portal.py", "exec")
    compile(cl.decode("utf-8"), "clinic_lists.py", "exec")
    outs = {"finance/finance_app.py": a.encode("utf-8"), "portal/portal.py": p.encode("utf-8"), NEW: cl}
    for f, b in outs.items():
        dst = os.path.join(outdir, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(b)
        print("built %s %s" % (f, md5b(b)))
    print("make_s689: %d counted edits, each anchor found exactly once; %d files written" % (len(edits), len(outs)))


if __name__ == "__main__":
    main()
