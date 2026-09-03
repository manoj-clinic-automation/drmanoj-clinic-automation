#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_grants_s222.py -- S222: per-person tiles stop being source code.

THE OWNER: "staff get same, but with their own required tiles… make it user friendly for them
for frequently switching between the works they do — vaapsi, some scanapp work, etc, place the
apps contextually and the ones needed more at higher level… attendance section is at lowest
level as its for personal use."

None of that is possible while the answer lives in Python. Today, giving one person one tile
means editing portal.py, publishing, and restarting the login system. And it is not one dict —
it is FIVE places that build the answer up imperatively:

    USER_TILE_MASK   = {...}                       the base masks
    USER_TILE_EXTRA  = {...}                       the base grants
    USER_TILE_MASK.setdefault("bhawna", ...)       S179, one more mask
    USER_TILE_MASK.setdefault("darpan", ...)       S179, three more masks
    for _u in (...): USER_TILE_EXTRA.setdefault    S182, two loops

WHAT THIS CHANGES, AND WHAT IT REFUSES TO CHANGE

The five places collapse into one JSON file the portal reads per request, and the code dicts stay
exactly where they are as the FALLBACK. If the file is missing, unreadable, or malformed, the
portal behaves precisely as it does today — a grants file that cannot be read must never be the
reason the owner's own tiles disappear. (The same fail-safe ruling as returns.desk_users and the
S222 corrections-page hide.)

The shipped seed reproduces TODAY, exactly, for every user — including the masks below that I
believe are wrong. The kit's gate proves that: it walks every user × every role × PC on and off
and asserts the visible sections are IDENTICAL with the file and without it. A move that changes
behaviour is not a move.

AND IT ADDS THE ORDERING HE ASKED FOR. Sections can be ordered per role and per person, so the
work someone does most sits highest and attendance sits last. This is DISPLAY ONLY — it reorders
what a person already sees and can grant or hide nothing.

⚠ ONE THING FOR THE OWNER TO RULE, SURFACED NOT FIXED

    USER_TILE_MASK["darpan"] = {"Attendance", "Staff Register", "Scan Purchase"}
    # S179: darpan is role=staff, which is shared. He only needs Daily Sale.

That reason is stale. Darpan has his own login and his own phone — the owner said so on 03-Sep —
and the owner also ruled that the basics everyone gets are "staff register scoped to their own
view to see advances and apply for more". **Darpan, who does more on this system than anyone, is
today the one person who cannot see his own attendance, his own register, or scan a bill.**
The seed keeps that mask so this kit changes nothing. Removing it is three deletions in a JSON
file once he says so.

Target: /root/portal/portal.py   (live pin 23824f92988621a38c1ae0cd7fb1314c, the
        S222_SCANAPP_INAPP result)
Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/patch_portal_grants_s222.py
Offline:         PORTAL_PATH=./portal.py python3 -B patch_portal_grants_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('PORTAL_PATH', '/root/portal/portal.py')
MARK = "S222 TILE GRANTS"
EXPECT_FROM = "23824f92988621a38c1ae0cd7fb1314c"


A_OLD = '''def _visible_sections(role, pc, user=""):
    """Ordered [(label, [tiles])] for this role/pc/user; empty sections dropped.
    A tile shows when the role matches OR the user is granted it (EXTRA), the user
    is not masked from it (MASK), and PC-gating passes."""
    mask = USER_TILE_MASK.get(user, set())
    extra = USER_TILE_EXTRA.get(user, set())
    out = []
    for _g in GROUP_ORDER:
        _items = [t for t in TILES
                  if t.get("group") == _g
                  and (role in t["roles"] or t["name"] in extra)
                  and t["name"] not in mask
                  and (not t.get("pc_only") or pc)]
        if _items:
            out.append((_g, _items))
    return out
'''

A_NEW = '''# ---- S222 TILE GRANTS ------------------------------------------------------
# Per-person tiles used to be five places in this file, built up imperatively.
# They are now ONE json file, read per request, with the dicts above kept as the
# fallback: if the file is missing, unreadable or malformed the portal behaves
# EXACTLY as it did before it existed. A grants file that cannot be read must
# never be the reason somebody's tiles vanish.
#
#   {"users": {"<login>": {"mask": [...], "extra": [...], "groups": [...]}},
#    "defaults": {"groups_by_role": {"staff": ["Clinic", ...]}}}
#
# `groups` / `groups_by_role` order the SECTIONS for that person or role — the
# owner's "the ones needed more at higher level, attendance at the lowest".
# Ordering is DISPLAY ONLY: it can grant nothing and hide nothing. Any section
# not named keeps its place after the ones that are.
TILE_GRANTS_FILE = os.environ.get("TILE_GRANTS_FILE",
                                  os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               "tile_grants.json"))
_GRANTS_CACHE = {"mtime": None, "data": None}


def _tile_grants():
    """The grants file, or None when there isn't a usable one. Never raises."""
    try:
        st = os.stat(TILE_GRANTS_FILE)
    except OSError:
        return None
    if _GRANTS_CACHE["mtime"] == st.st_mtime and _GRANTS_CACHE["data"] is not None:
        return _GRANTS_CACHE["data"]
    try:
        with open(TILE_GRANTS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or not isinstance(data.get("users"), dict):
            return None
    except Exception:
        return None
    _GRANTS_CACHE["mtime"] = st.st_mtime
    _GRANTS_CACHE["data"] = data
    return data


def _grants_for(user, role):
    """(mask, extra, group_order) for this login. Falls back to the code dicts."""
    g = _tile_grants()
    if not g:
        return (USER_TILE_MASK.get(user, set()),
                USER_TILE_EXTRA.get(user, set()),
                list(GROUP_ORDER))
    u = g.get("users", {}).get(user) or {}
    try:
        mask = set(u.get("mask") or [])
        extra = set(u.get("extra") or [])
    except Exception:
        mask, extra = USER_TILE_MASK.get(user, set()), USER_TILE_EXTRA.get(user, set())
    order = u.get("groups")
    if not order:
        order = ((g.get("defaults") or {}).get("groups_by_role") or {}).get(role)
    if not order:
        order = (g.get("defaults") or {}).get("groups")
    if not isinstance(order, list) or not order:
        order = list(GROUP_ORDER)
    # every known section still appears: named ones first, the rest after, and
    # nothing is dropped by an incomplete list
    seen, full = set(), []
    for _g in order:
        if _g in GROUP_ORDER and _g not in seen:
            full.append(_g); seen.add(_g)
    for _g in GROUP_ORDER:
        if _g not in seen:
            full.append(_g)
    return mask, extra, full


def _visible_sections(role, pc, user=""):
    """Ordered [(label, [tiles])] for this role/pc/user; empty sections dropped.
    A tile shows when the role matches OR the user is granted it (EXTRA), the user
    is not masked from it (MASK), and PC-gating passes.
    S222: the mask, the grant and the section order come from tile_grants.json
    when there is a usable one, and from the dicts above when there is not."""
    try:
        mask, extra, group_order = _grants_for(user, role)
    except Exception:
        mask = USER_TILE_MASK.get(user, set())
        extra = USER_TILE_EXTRA.get(user, set())
        group_order = list(GROUP_ORDER)
    out = []
    for _g in group_order:
        _items = [t for t in TILES
                  if t.get("group") == _g
                  and (role in t["roles"] or t["name"] in extra)
                  and t["name"] not in mask
                  and (not t.get("pc_only") or pc)]
        if _items:
            out.append((_g, _items))
    return out
'''


PAIRS = [("A", A_OLD, A_NEW)]


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
    if "\\nimport json" not in src and "import json" not in src:
        raise SystemExit("REFUSED: portal.py does not import json, which the new code needs. "
                         "NOTHING was changed.")
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_grants_" + stamp
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
    print("next     put tile_grants.json beside portal.py, then restart clinic-portal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
