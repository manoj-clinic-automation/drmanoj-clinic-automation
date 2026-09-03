#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_desk_users_s222.py -- S222 star-1-1: CLOSE F-296, THE VAAPSI DESK OVER-GRANT.

THE FAULT, in the owner's words at the S221 close:

    "Why have you added him to the medicine return vaapsi desk?"

He had not been added. `viewer` IS the desk's key, and has been since S214 --
so giving Amir `viewer` for his corrections desk and his stock count also handed
a purchase man the power to issue cash refunds. The cause is older than Amir:
S214's ruling was "the desk is worked by NAMED reception staff", and the name was
never written into code. The desk asks *are you a viewer?* and never *are you one
of them?*. ANYONE EVER GIVEN VIEWER GETS THE RETURNS DESK.

The S214 file even says so, in its own docstring, as a reason to feel safe:

    "and NO other finance route accepts viewer, so it grants THIS desk and
     nothing else"

That sentence was true when it was written and false by S221, when darpan_app.py
and stock_app.py both learned to accept a viewer. A comment that states a
guarantee the code does not enforce is how this happened. This patch enforces it
and corrects the sentence.

THE FIX, as the owner approved it -- OPT-IN, AND FAIL-SAFE BY DESIGN:

  setting `returns.desk_users`
      SET   -> only those logins, PLUS maker/checker, may open the desk
      UNSET -> NOTHING CHANGES. Every viewer reaches the desk exactly as today.

  The unset case is not laziness, it is the owner's own constraint: reception
  (Darpan . Shavez . Alisha . Shivani) must not be lockable out by a half-applied
  change. For the same reason a DATABASE ERROR while reading the setting ALLOWS.
  This gate exists to keep a purchase man out of a cash-refund screen; it is not
  a lock on the front door, and it must never be the reason the counter stops
  working at 8 p.m. That is a deliberate ruling, written here so it is never
  mistaken for an oversight.

  maker/checker always pass: Darpan is a maker and the owner is a checker, and
  neither should ever depend on a list.

ONE CHOKE POINT. Every route in returns_desk.py -- the page, /api/search,
/api/history, /api/items, /api/catalog, /api/slip, /api/slip/settle,
/api/slip/void, /api/slips, and the S221 /api/jaankari pair -- calls `_auth()`
and returns its error unchanged. `_auth()` is the only door, so the gate goes
there and nowhere else. Verified by reading every route, not assumed.

ANCHORS
  A (REQUIRED) the four-line body of `_auth()`. If it does not match exactly
    once, NOTHING is written.
  B (OPTIONAL) the stale docstring sentence quoted above. A comment is not
    behaviour, so if S220/S221 reworded it the patch still applies and says so.

Target: /root/finance/returns_desk.py   (live pin 1dc1fd62... at the S221 close)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_desk_users_s222.py
Offline:         RD_PATH=./returns_desk.py python3 -B patch_desk_users_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('RD_PATH', '/root/finance/returns_desk.py')
MARK = "S222 star-1-1"


# --------------------------------------------------------------- anchor A
# REQUIRED. The four-line body of _auth(). The gate goes in after _require()
# has already decided the caller is at least a viewer.

A_OLD = '''    u, err = _require(*DESK_ROLES)
    if err:
        return None, err
    return u, None
'''

A_NEW = '''    u, err = _require(*DESK_ROLES)
    if err:
        return None, err
    if not _desk_allowed(u):
        return None, (jsonify(
            ok=False, error="not_desk_user",
            message="Vaapsi desk aapke naam par nahin hai. "
                    "Apne incharge se kahein."), 403)
    return u, None


# ---- S222 star-1-1: F-296, the viewer over-grant --------------------------
# `viewer` opens this desk. Since S221 it also opens the corrections desk and
# the stock count, so `viewer` no longer means "reception". This is the list
# that makes the S214 ruling -- NAMED staff -- true in code.
#
# Empty or missing list = NOT CONFIGURED = nothing changes. A read error also
# allows. See the patcher header: keeping the counter working outranks this
# gate, which exists to keep a purchase man out of cash refunds.

DESK_USERS_KEY = "returns.desk_users"


def _desk_users(con):
    """The allow-list as a set of lower-case logins. Empty set = not set.

    Accepts commas, semicolons or spaces so the owner can type the row by hand
    in any shape he likes."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?",
                        (DESK_USERS_KEY,)).fetchone()
    except Exception:
        return set()
    raw = ""
    if r is not None:
        try:
            raw = r["value"] or ""
        except Exception:
            raw = r[0] or ""
    return set(p.strip().lower() for p in re.split(r"[,;\\s]+", str(raw)) if p.strip())


def _desk_allowed(u):
    """May this login work the Vaapsi desk?"""
    roles = set((u or {}).get("roles") or [])
    one = (u or {}).get("role")
    if one:
        roles.add(str(one))          # every caller shape, not just finance_app's
    if roles.intersection(("maker", "checker")):
        return True                      # Darpan, and the owner. Never listed.
    try:
        allow = _desk_users(_con())
    except Exception:
        return True                      # deliberate: see the header
    if not allow:
        return True                      # not configured -> nothing changes
    who = str((u or {}).get("user") or (u or {}).get("username") or "").strip().lower()
    return bool(who) and who in allow
# ---- end S222 star-1-1 -----------------------------------------------------
'''


# --------------------------------------------------------------- anchor B
# OPTIONAL. The sentence that made this fault feel safe.

B_OLD = '''    and NO other finance route accepts viewer, so it grants THIS desk and
    nothing else; makers and checkers can always work the desk. Seeded by
    seed_desk_roles.py at install -- visible rows, not code."""
'''

B_NEW = '''    S222 (F-296): that WAS true at S214 and is FALSE since S221 -- the
    corrections desk and the stock count both accept a viewer now, so viewer no
    longer means reception. `returns.desk_users` is what names them. Makers and
    checkers can always work the desk. Seeded by seed_desk_roles.py (the roles)
    and seed_desk_users_s222.py (the names) -- visible rows, not code."""
'''


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0

    n = src.count(A_OLD)
    if n != 1:
        raise SystemExit("REFUSED: anchor A matches %d times (need exactly 1). "
                         "NOTHING was changed." % n)
    nb = src.count(B_OLD)
    if nb > 1:
        raise SystemExit("REFUSED: anchor B matches %d times (need 0 or 1). "
                         "NOTHING was changed." % nb)

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_deskusers_" + stamp
    shutil.copyfile(TARGET, bak)

    out = src.replace(A_OLD, A_NEW, 1)
    if nb == 1:
        out = out.replace(B_OLD, B_NEW, 1)

    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s -- the live file is unchanged." % (ex, bak))

    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    print("anchor A applied (the gate)")
    print("anchor B %s" % ("applied (the stale sentence corrected)" if nb == 1
                           else "NOT FOUND -- the docstring was reworded since S214; "
                                "the gate is in, the comment is not. Say so at the close."))
    print("next     seed the names, then the walk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
