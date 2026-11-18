#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s890_portal.py -- S890: the folder tile on the owner's home draws its inside tiles as bold lines, the Renewals line takes the
red count. The real portal.py (TO, or the live one for the CONTROL) imported in a scratch copy of /root/portal with made-up secrets
and the live tile_grants.json; the home rendered for the owner and for a staff login through the portal's own functions. The
count script is checked by node --check (where node is absent the walk says so; --box lets it stand). Nothing leaves the process.

    python3 -B walk_s890_portal.py --live <the portal folder> --files <folder holding portal.py> [--expect-red] [--box]
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES = opt("--live", "/root/portal"), opt("--files")
EXPECT_RED = "--expect-red" in ARGS
GREEN_BOTH = ("A0", "C1", "C2", "B4", "Z1")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s890portal_")
    try:
        app = os.path.join(work, "portal")
        shutil.copytree(LIVE, app, ignore=shutil.ignore_patterns("*.pyc", "__pycache__", "*BACKUP*"))
        if FILES and os.path.isfile(os.path.join(FILES, "portal.py")):
            shutil.copy(os.path.join(FILES, "portal.py"), os.path.join(app, "portal.py"))
        env = dict(os.environ, PORTAL_PIN_HASH="x", PORTAL_PIN_SALT="walk-salt", PORTAL_TOKEN_SEED="walk-seed", CLINIC_SSO_SECRET="walk-sso",
                   TILE_GRANTS_FILE=os.path.join(app, "tile_grants.json"), PORTAL_FORMS_DIR=os.path.join(work, "forms"))
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        if r.returncode not in (0, 1) or os.environ.get("S890_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

APPD = ARGS[ARGS.index("--inner") + 1]
WORK = ARGS[ARGS.index("--inner") + 2]
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (_me, os.path.abspath("."))]
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:400]) if (d and not ok) else ""))


import portal as po                                                  # noqa: E402
from flask import render_template_string                             # noqa: E402

ck("A0 the real portal loads", lambda: po.app is not None)


def home_for(user, role):
    with po.app.test_request_context("/portal"):
        sections = po._visible_sections(role, False, user)
        blocks = po._home_blocks(sections, po._folders_for(user))
        who = {"user": user, "role": role}
        return render_template_string(po.PORTAL_HTML, sections=sections, blocks=blocks, sso=True, who=who, role=role, pc=False, s444_nowork=False), blocks


h, blocks = home_for("manoj", "doctor")
folded = [b for b in blocks if b[2]]
acc = [b for b in folded if b[0] == "Accounts & month-end"]
names = [t["name"] for t in acc[0][1]] if acc else []
ck("C1 the owner's home has folded groups, 'Accounts & month-end' among them, holding Month-end packs and Renewals",
   lambda: folded and acc and "Renewals" in names and "Month-end packs" in names, lambda: (len(folded), names))
tile = re.search(r'<button class="tile grp"[^>]*id="gt-[^"]*"[^>]*>.*?</button>', h, re.S)
tiles = re.findall(r'<button class="tile grp".*?</button>', h, re.S)
acc_tile = [t for t in tiles if "Accounts" in t]
ck("B1 the folder tile draws one bold line per inside tile (class gll) -- the Accounts tile carries %d lines, Renewals among them, no muted one-liner" % len(names),
   lambda: acc_tile and acc_tile[0].count('class="gll"') + acc_tile[0].count("class=\"gll\" ") >= len(names) - 1 and "Renewals" in acc_tile[0]
   and "Packs · month checklist" not in acc_tile[0], lambda: acc_tile[0][:600] if acc_tile else "no Accounts tile")
ck("B2 the Renewals line carries the data-s890-renewals mark (the count lands there), exactly once on the home",
   lambda: h.count(" data-s890-renewals>") == 1, lambda: h.count(" data-s890-renewals>"))
ck("B3 every folder tile on the home is drawn the same way (each has lines, none keeps the old description line)",
   lambda: tiles and all('class="gll"' in t for t in tiles) and all('<div class="ds">' not in t for t in tiles), lambda: [t[:200] for t in tiles if 'class="gll"' not in t][:2])
ck("B4 the panel header (the open folder) still carries the description line -- unchanged", lambda: '<div class="gph">' in h and h.count('class="ds">{{') == 0 and "gpanel" in h)
css_ok = ".tile.grp .gll{" in h and ".s890n{" in h
ck("B5 the CSS for the lines and the red count is on the page", lambda: css_ok)
js = re.search(r"/\* S890 \(D1017\).*?\n(\(function\(\)\{\n  var ls=document\.querySelectorAll\('\[data-s890-renewals\]'\);.*?\n\}\)\(\);)", h, re.S)
jsok, jsmsg = False, "no script"
if js:
    jp = os.path.join(WORK, "s890.js")
    open(jp, "w", encoding="utf-8").write(js.group(1))
    try:
        rr = subprocess.run(["node", "--check", jp], capture_output=True, text=True, timeout=60)
        jsok, jsmsg = rr.returncode == 0, rr.stderr[-300:]
    except FileNotFoundError:
        jsok, jsmsg = ("--box" in ARGS), "node is not here"
ck("B6 the count script is on the page, asks /scanapp/renewals/one/api/count with the login's cookie, and is valid JavaScript (node --check)",
   lambda: js and "/scanapp/renewals/one/api/count" in js.group(1) and "credentials:'same-origin'" in js.group(1) and jsok, lambda: jsmsg)
hs, bs = home_for("shavez", "staff")
ck("C2 a staff login's home still renders, with no Renewals mark on it (his month checklist tile stands flat, as before)",
   lambda: len(hs) > 1000 and " data-s890-renewals>" not in hs and "</html>" in hs, lambda: len(hs))
ck("Z1 the old S657 scripts (the Expiry watch box, the group panels) are still on the page", lambda: "S657: the Expiry watch box" in h and "groupGrid" in h)
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in GREEN_BOTH if not RES.get(k)] + [k for k, v in RES.items() if v and k not in GREEN_BOTH]
    print("WALK S890 PORTAL CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad_ else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S890 PORTAL: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
