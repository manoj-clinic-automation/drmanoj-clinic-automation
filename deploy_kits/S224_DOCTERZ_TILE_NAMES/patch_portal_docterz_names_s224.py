#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_docterz_names_s224.py -- S224: the Docterz tiles say "Docterz".

THE OWNER (04-Sep-2026): "the Docterz tiles' titles should be clear -- 'Day', 'Daily',
'Clinic' replace with 'Docterz'; keep the descriptions; in the Day Revenue tile replace
'takings' with 'collection'; the Daily Register tile -> 'Docterz daily collection', and in its
description replace 'The counters' with 'Reception'."

TWO tiles are renamed, nothing is added and nothing moves:

    Day Revenue      ->  Docterz Revenue
        desc  "Clinic takings by day -- from Docterz"      ->  "Clinic collection by day -- from Docterz"
    Daily Register   ->  Docterz daily collection
        desc  "The counter's day totals -- cash, UPI, card" ->  "Reception's day totals -- cash, UPI, card"

_TILE_GROUP is keyed by tile NAME, and the portal asserts at import that every tile is grouped,
so the two group-map keys are renamed in the same edit (a rename of the tile alone would 503 the
portal at the restart). tile_grants.json v6 grants both tiles BY NAME to the five people the owner
listed; v7 ships beside this patcher with the same two names renamed and NOTHING else changed --
install both together, or the four staff logins silently lose the two tiles (a stale name in
"extra" matches no tile; the doctor keeps them by role either way).

NOT touched: Daily Collection (/finance/clinic/entry) and Clinic (/finance/clinic/review) -- the
S182 manual clinic-entry tiles, not Docterz-fed -- and every other tile.

THE PIN. portal.py on the box is ahead of the repo, so the expected md5 is passed in, not
hard-coded. Three anchors are exact and each must match exactly once; anything else REFUSES and
changes nothing. Idempotent by the MARK. Timestamped backup, compile-with-restore.

Run on the box:
    md5sum /root/portal/portal.py
    /root/wa/venv/bin/python3 -B /root/portal/patch_portal_docterz_names_s224.py <that md5>
Offline:
    PORTAL_PATH=./portal.py python3 -B patch_portal_docterz_names_s224.py <md5 of that copy>
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
MARK = '"name": "Docterz Revenue"'

# A -- the Day Revenue tile: name and description (the comment lines between are untouched)
A_OLD = '''    {"icon": "\\U0001F4C8", "name": "Day Revenue",'''
A_NEW = '''    {"icon": "\\U0001F4C8", "name": "Docterz Revenue",'''
B_OLD = '''     "desc": "Clinic takings by day \\u2014 from Docterz",'''
B_NEW = '''     "desc": "Clinic collection by day \\u2014 from Docterz",'''

# C -- the Daily Register tile: name and description
C_OLD = '''    {"icon": "\\U0001F4D2", "name": "Daily Register",'''
C_NEW = '''    {"icon": "\\U0001F4D2", "name": "Docterz daily collection",'''
D_OLD = '''     "desc": "The counter's day totals \\u2014 cash, UPI, card",'''
D_NEW = '''     "desc": "Reception's day totals \\u2014 cash, UPI, card",'''

# E -- the group map, keyed by tile name (S223 CLINIC_DAY + REGISTER_CARD + S224 purchase rows)
E_OLD = '''    "Corrections": "Money & Accounts", "Day Revenue": "Money & Accounts",
    "Daily Register": "Money & Accounts", "Marg Purchases": "Money & Accounts",'''
E_NEW = '''    "Corrections": "Money & Accounts", "Docterz Revenue": "Money & Accounts",
    "Docterz daily collection": "Money & Accounts", "Marg Purchases": "Money & Accounts",'''

PAIRS = (("Day Revenue tile name", A_OLD, A_NEW),
         ("Day Revenue tile desc", B_OLD, B_NEW),
         ("Daily Register tile name", C_OLD, C_NEW),
         ("Daily Register tile desc", D_OLD, D_NEW),
         ("group map rows", E_OLD, E_NEW))


def main():
    if len(sys.argv) < 2 or len(sys.argv[1]) != 32:
        sys.exit("USAGE: patch_portal_docterz_names_s224.py <md5 of the portal.py you are patching>\n"
                 "       read it with:  md5sum /root/portal/portal.py")
    from_md5 = sys.argv[1].lower()
    if not os.path.exists(PORTAL):
        sys.exit("REFUSING: %s not found" % PORTAL)
    src = io.open(PORTAL, encoding="utf-8").read()
    cur = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != from_md5:
        sys.exit("REFUSING: %s is %s, you said %s. Read the box's pin again." % (PORTAL, cur, from_md5))
    for label, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, n))
    new = src
    for _label, old, rep in PAIRS:
        new = new.replace(old, rep, 1)
    bak = PORTAL + ".bak_S224_dznames_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(PORTAL, bak)
    io.open(PORTAL, "w", encoding="utf-8", newline="\n").write(new)
    try:
        import py_compile
        import tempfile
        _fd, _cf = tempfile.mkstemp(suffix=".pyc")
        os.close(_fd)
        try:
            py_compile.compile(PORTAL, cfile=_cf, doraise=True)
        finally:
            try:
                os.remove(_cf)
            except OSError:
                pass
    except Exception as e:
        shutil.copy2(bak, PORTAL)
        sys.exit("REFUSING: compile failed (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    print("current pin  %s" % from_md5)
    print("patched  %s" % PORTAL)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     put tile_grants.json (v7) beside it, then restart clinic-portal")


if __name__ == "__main__":
    main()
