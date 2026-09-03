#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_joiner_allrecs_s222.py -- S222 ⭐1-3b: a CLOSED record must still be openable.

FOUND BY THE OWNER, minutes after S222_JOINER_LOGIN went live, and it is my miss.

The staff page lists `pending()` -- `WHERE status != 'COMPLETE'`. Amir's joiner record is
COMPLETE at 6/6. So the page shows *"Koi adhoora record nahin — sab poore ✓"* and offers no way
to open his record at all. The login line that S222 had just built for exactly this man had
nowhere to appear.

The register has always been able to serve a closed record -- `/api/record?ref=...` reads any of
them, and `showRec()` renders any of them. **The only thing missing was a way to CHOOSE one.**
A screen that can only show you what is unfinished cannot answer "is this finished thing right?",
and that is the question the whole S222 login work exists to answer.

ADDS ONE READ-ONLY ROUTE:

    GET /finance/staff/api/all[?q=amir]
        every record, newest first, with how many steps are done -- open and closed alike.
        Optional `q` matches the person or the ref. Nothing is written, ever.

Target: /root/finance/joiner_app.py   (live pin c879eafe1c05996be8b700a530995427, i.e. AFTER
        S222_JOINER_LOGIN. This kit refuses against anything else.)

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_joiner_allrecs_s222.py
Offline:         JA_PATH=./joiner_app.py python3 -B patch_joiner_allrecs_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('JA_PATH', '/root/finance/joiner_app.py')
MARK = "S222 ALL RECORDS"
EXPECT_FROM = "c879eafe1c05996be8b700a530995427"


A_OLD = '''@bp.route("/api/record")
def api_record():
'''

A_NEW = '''@bp.route("/api/all")
def api_all():
    """S222 ALL RECORDS -- every joiner record, open AND closed. Read only.

    pending() deliberately shows only what is unfinished, which is right for a
    to-do list and wrong for a question about somebody who is already done. The
    owner hit this the day S222 added a login check to the record page: Amir's
    record was COMPLETE, so the page offered no way to open it."""
    con = _db()
    ensure_schema(con)
    q = (request.args.get("q") or "").strip().lower()
    out = []
    for r in con.execute(
            "SELECT id,ref,kind,person,role,status,username,emp_code,opened_on,closed_on "
            "FROM joiner ORDER BY opened_on DESC, id DESC"):
        jid = _v(r, "id", 0)
        ref = _v(r, "ref", 1)
        person = _v(r, "person", 3)
        if q and q not in str(person).lower() and q not in str(ref).lower():
            continue
        kind = _v(r, "kind", 2)
        order = steps_for(kind)
        done = done_steps(con, jid)
        out.append(dict(ref=ref, kind=kind, person=person, role=_v(r, "role", 4),
                        status=_v(r, "status", 5), username=_v(r, "username", 6),
                        emp_code=_v(r, "emp_code", 7), opened_on=_v(r, "opened_on", 8),
                        closed_on=_v(r, "closed_on", 9),
                        done=len([s for s in order if s in done]), total=len(order),
                        complete=(_v(r, "status", 5) == "COMPLETE")))
    return jsonify(ok=True, count=len(out), records=out)


@bp.route("/api/record")
def api_record():
'''


# --------------------------------------------------------------- anchor B
# THE SECOND HALF, and the owner found it by using the first one.
#
# His check came back:  "exists": true, "role": "staff", "password": "amir1234"
# -- the login DOES exist; he had created it himself at /portal/users at 10:30.
# So S222_JOINER_LOGIN would now draw a green tick and print `amir1234` as the
# password. But NOTHING CHECKS THAT amir1234 IS STILL HIS PASSWORD. If the owner
# typed a different one when he created the account -- or the man has since
# changed it, which the page itself tells him to do -- the screen goes back to
# stating a password that does not work.
#
# That is F-295 again, one size smaller: a green tick is worth nothing if it is
# asserted rather than tested. The create route already proves itself with
# verify_password(); the STATUS route must do the same.

B_OLD = '''def _portal_status(user):
    """What the portal store actually says about this login. Read only."""
    CU, path, why = _portal_users()
    if not CU:
        return dict(store_readable=False, why=why)
    try:
        store = CU.load_store(path)
        rec = store.get("users", {}).get(str(user or "").strip().lower())
        return dict(store_readable=True, store=path,
                    roles=list(store.get("roles") or []),
                    exists=bool(rec),
                    active=bool(rec.get("active")) if rec else False,
                    role=(rec.get("role") if rec else None),
                    created=(rec.get("created") if rec else None))
    except Exception as ex:
        return dict(store_readable=False, why="the user store could not be read (%s)" % ex)
'''

B_NEW = '''def _portal_status(user, pw=None):
    """What the portal store actually says about this login. Read only.

    S222 ALL RECORDS: when a password is passed, it is TRIED -- not assumed.
    `password_works` is None when there was nothing to try or no user to try it
    on. The page must never print a password it has not seen work; that is the
    same fault as F-295, one size smaller."""
    CU, path, why = _portal_users()
    if not CU:
        return dict(store_readable=False, why=why)
    try:
        store = CU.load_store(path)
        rec = store.get("users", {}).get(str(user or "").strip().lower())
        works = None
        if rec and pw:
            try:
                works = bool(CU.verify_password(path, user, pw))
            except Exception:
                works = None
        return dict(store_readable=True, store=path,
                    roles=list(store.get("roles") or []),
                    exists=bool(rec),
                    active=bool(rec.get("active")) if rec else False,
                    role=(rec.get("role") if rec else None),
                    created=(rec.get("created") if rec else None),
                    password_works=works)
    except Exception as ex:
        return dict(store_readable=False, why="the user store could not be read (%s)" % ex)
'''


# --------------------------------------------------------------- anchor C
# Pass the derived password in so it is tried, and gate the route. The page it
# serves is already checker-only (staff_pages.page_staff), so this costs nothing
# -- and the answer now includes whether a default password opens an account,
# which is not a thing to hand to every logged-in user.

C_OLD = '''    """Does this joiner's login actually exist? READ ONLY.

    This is the route that stops the page printing a login nobody can use."""
    con = _db()
'''

C_NEW = '''    """Does this joiner's login actually exist, and does its password work? READ ONLY.

    This is the route that stops the page printing a login nobody can use."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
'''

D_OLD = '''    st = _portal_status(user)
'''

D_NEW = '''    st = _portal_status(user, default_password(person))
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW), ("D", D_OLD, D_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit("REFUSED: this file is %s, not the %s this kit was built against "
                         "(S222_JOINER_LOGIN must be installed first). NOTHING was changed."
                         % (before, EXPECT_FROM))
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_allrecs_" + stamp
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
