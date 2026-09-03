#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_desk_users_s222.py -- THE LIVE-SHAPE WALK for S222_DESK_USERS (F-296).

It mounts the REAL, patched /root/finance/returns_desk.py on a COPY of the live
finance.db, reads the REAL unit_role rows and the REAL `returns.desk_users`
setting, and then asks the two questions the owner asked:

    is Amir refused the Vaapsi desk?
    are Darpan, Shavez, Alisha and Shivani still on it?

Every desk route is walked as Amir, not just the page -- a gate on the front
door that leaves an API open is not a gate. And the walk then TURNS THE SETTING
OFF on the copy and proves the fail-safe is real: with the row blank, Amir
reaches the desk again, exactly as before this kit. A claim in a comment is not
evidence.

IT NEVER TOUCHES THE LIVE DATABASE. The first thing it does is copy it.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/walk_desk_users_s222.py
Offline:         FIN_DB=/path/to/finance.db RD_DIR=/path/to/dir python3 -B walk_desk_users_s222.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile

SRC_DB = os.environ.get("FIN_DB", "/root/finance/finance.db")
RD_DIR = os.environ.get("RD_DIR", "/root/finance")
if RD_DIR not in sys.path:
    sys.path.insert(0, RD_DIR)

PREFIX = "/finance/returns/desk"
KEY = "returns.desk_users"

FAILED, PASSED = [], []
NOTES = []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail else ""))


# every route the desk serves. GETs and POSTs both -- a POST that 403s on the
# gate never reaches its own body checks, which is the point.
GETS = ["", "/", "/api/search?q=ab", "/api/history?pid=1", "/api/items?pid=1",
        "/api/catalog?q=ab", "/api/slips", "/api/jaankari"]
POSTS = ["/api/slip", "/api/slip/settle", "/api/slip/void", "/api/jaankari/answer"]


def main():
    if not os.path.exists(SRC_DB):
        print("no database at %s -- set FIN_DB" % SRC_DB)
        return 2
    tmp = tempfile.mkdtemp(prefix="walk_s222_")
    db = os.path.join(tmp, "finance.db")
    shutil.copyfile(SRC_DB, db)
    print("walking on a COPY: %s\n" % db)

    import returns_desk as RD
    src = open(RD.__file__, encoding="utf-8").read()

    print("-- 0  what is under test ------------------------------------------")
    ck("the file under test is the LIVE one", os.path.abspath(RD.__file__)
       .startswith(os.path.abspath(RD_DIR)), RD.__file__)
    ck("it carries the S222 gate", "S222 star-1-1" in src)
    ck("it still carries the S221 jaankari lists", "S221 star-1-1" in src)
    ck("_auth() is still the only door",
       src.count("_require(*DESK_ROLES)") == 1,
       "_require(*DESK_ROLES) appears %d times" % src.count("_require(*DESK_ROLES)"))

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
    seeded = (row["value"] if row else "") or ""
    print("\n-- 1  the list, as the live database holds it ---------------------")
    print("      %s = %r" % (KEY, seeded))
    have = set(p.strip().lower() for p in seeded.replace(";", ",").replace(" ", ",").split(",") if p.strip())
    for n in ("darpan", "shavez", "alisha", "shivani"):
        ck("the owner's list names %s" % n, n in have)
    ck("the list does NOT name amir", "amir" not in have)

    print("\n-- 2  the roles, as the live database holds them ------------------")
    roles = {}
    for r in con.execute("SELECT lower(username) AS u, role FROM unit_role "
                         "WHERE unit='medical' AND active=1"):
        roles.setdefault(r["u"], set()).add(r["role"])
    for n in sorted(roles):
        print("      %-10s %s" % (n, ",".join(sorted(roles[n]))))
    ck("amir carries viewer on the medical unit (the S221 grant is intact)",
       "viewer" in roles.get("amir", set()))
    con.close()

    from flask import Flask, jsonify
    app = Flask(__name__)
    WHO = {"user": "amir"}

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def _require(*want, **kw):
        """finance_app's require(), same shape: (u, None) or (None, (body, 403)).
        The roles come from the COPY's own unit_role rows, not from this file."""
        u = WHO["user"]
        have_r = set(roles.get(u, set())) | set(WHO.get("extra", ()))
        if not have_r.intersection(want):
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        return dict(user=u, role="staff", roles=sorted(have_r)), None

    RD.init(app, _db, _require, unit="medical", url_prefix=PREFIX)
    cl = app.test_client()

    def status(path, post=False):
        r = cl.post(PREFIX + path, json={}) if post else cl.get(PREFIX + path)
        return r.status_code, (r.get_json(silent=True) or {})

    def as_(user, extra=()):
        WHO["user"] = user
        WHO["extra"] = tuple(extra)

    print("\n-- 3  AS AMIR: every desk route must refuse -----------------------")
    as_("amir")
    for p in GETS:
        c, j = status(p)
        ck("amir refused GET %s" % (p or "(the page)"),
           c == 403 and j.get("error") == "not_desk_user", "%s %s" % (c, j.get("error")))
    for p in POSTS:
        c, j = status(p, post=True)
        ck("amir refused POST %s" % p,
           c == 403 and j.get("error") == "not_desk_user", "%s %s" % (c, j.get("error")))

    print("\n-- 4  AS THE FOUR: the desk still opens ---------------------------")
    for n in ("darpan", "shavez", "alisha", "shivani"):
        as_(n)
        c, j = status("")
        ck("%s opens the desk" % n, c == 200, "%s %s" % (c, j.get("error")))
        c, j = status("/api/slips")
        ck("%s reads the slips list" % n, c == 200, "%s %s" % (c, j.get("error")))

    print("\n-- 5  the owner is never on a list --------------------------------")
    as_("manoj", extra=("checker",))
    c, j = status("")
    ck("a checker not named in the list opens the desk", c == 200,
       "%s %s" % (c, j.get("error")))
    as_("someone_new", extra=("maker",))
    c, j = status("")
    ck("a maker not named in the list opens the desk", c == 200,
       "%s %s" % (c, j.get("error")))

    print("\n-- 6  A FUTURE VIEWER IS OUT BY DEFAULT ---------------------------")
    as_("future_viewer", extra=("viewer",))
    c, j = status("")
    ck("a viewer granted tomorrow does NOT get the desk", c == 403
       and j.get("error") == "not_desk_user", "%s %s" % (c, j.get("error")))

    print("\n-- 7  THE FAIL-SAFE, PROVEN ON THE COPY ---------------------------")
    c2 = sqlite3.connect(db)
    c2.execute("UPDATE setting SET value='' WHERE key=?", (KEY,))
    c2.commit()
    c2.close()
    as_("amir")
    c, j = status("")
    ck("with the row BLANK, amir reaches the desk again (nothing changed)",
       c == 200, "%s %s" % (c, j.get("error")))
    as_("alisha")
    c, j = status("")
    ck("with the row BLANK, alisha reaches the desk", c == 200,
       "%s %s" % (c, j.get("error")))
    c2 = sqlite3.connect(db)
    c2.execute("DELETE FROM setting WHERE key=?", (KEY,))
    c2.commit()
    c2.close()
    as_("amir")
    c, j = status("")
    ck("with the row DELETED, amir reaches the desk again", c == 200,
       "%s %s" % (c, j.get("error")))

    print("\n-- 8  AMIR KEEPS WHAT S221 GAVE HIM -------------------------------")
    # These two are NOT touched by this kit, and the walk proves it rather than
    # asserting it. THE PATHS AND SIGNATURES BELOW ARE S221's OWN, copied from
    # walk_amir_access_s221.py -- v1 of this walk GUESSED them ("/finance/stock/count",
    # and a url_prefix darpan_app does not take), could not run this section
    # offline, and so shipped a guess to the box, where it produced a FALSE FAIL
    # on a screen nothing had changed. Recorded here, not quietly corrected.
    as_("amir")
    try:
        import stock_app as SA
        a2 = Flask("s222_stock")
        SA.init(a2, _db, _require, unit="medical",
                url_prefix="/finance/stock", marg_token="t")
        c2 = a2.test_client()
        for path, label in (("/finance/stock/page/count", "the stock count screen"),
                            ("/finance/stock/page/diffs", "the stock differences list"),
                            ("/finance/stock/api/open", "the open-differences data")):
            r = c2.get(path)
            ck("amir still opens %s" % label, r.status_code == 200,
               "%s -> %s" % (path, r.status_code))
    except Exception as ex:
        NOTES.append("could not walk the stock screens (%s) -- check by hand" % ex)
        print("  NOTE  could not walk the stock screens: %s" % ex)
    try:
        import darpan_app as DA
        a3 = Flask("s222_darpan")
        DA.init(a3, _db, _require, unit="medical")
        r = a3.test_client().get("/finance/darpan/corrections")
        ck("amir still opens his corrections desk", r.status_code == 200,
           "/finance/darpan/corrections -> %s" % r.status_code)
    except Exception as ex:
        NOTES.append("could not walk the corrections desk (%s) -- check by hand" % ex)
        print("  NOTE  could not walk the corrections desk: %s" % ex)

    shutil.rmtree(tmp, ignore_errors=True)
    n = len(PASSED) + len(FAILED)
    print("\n%s  %d/%d" % ("WALK GREEN" if not FAILED else "WALK RED", len(PASSED), n))
    for x in FAILED:
        print("  FAILED: %s" % x)
    for x in NOTES:
        print("  NOTE:   %s" % x)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
