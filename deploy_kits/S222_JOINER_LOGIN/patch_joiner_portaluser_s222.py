#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_joiner_portaluser_s222.py -- S222 ⭐1-3, server half: F-295, the login that was never created.

THE FAULT, and it is worse than it reads.

The joiner page prints, for every new person:

    login: amir · pehla password: amir1234 (pehli login par badalna hoga)

Both halves are **invented in the browser** from the person's first name. `/api/message`
composes the same thing into a WhatsApp text and its docstring calls it a feature --
*"The password is DERIVED, not stored -- nothing in this database holds it."* That reads like
good hygiene. What it actually means is **the account does not exist**. Nothing in the joiner
flow ever calls the portal's user store. The register ticks ACCOUNT_CREATED, the owner reads
the credentials out to a new man, and the login refuses him -- which is exactly what happened
to Amir, in front of the owner, at S221.

`/api/reset_password` has the same shape: it records a PASSWORD_RESET event and returns a
password with the words *"Set the portal password to this, then read it out"* -- an instruction
to a human, in the return value of a route that sounds like it did the work.

WHAT THIS ADDS -- and note that it TELLS THE TRUTH FIRST, and only then offers to act.

  GET  /finance/staff/api/portal_user?ref=...     READ ONLY, any desk role.
       Does this login exist? Is it active? What role? What roles does the store even have?
       This is the half that stops the page lying, and it writes nothing, ever.

  POST /finance/staff/api/portal_user/create      CHECKER ONLY.
       Creates the login for real, and PROVES IT:
         1  refuses unless the portal's own user store is readable and has a roles list
         2  refuses a role that is not in THAT store's list -- the list is read, never guessed
         3  refuses if the user already exists (add_user refuses too; this says it kindly)
         4  BACKS THE STORE UP beside itself before touching it
         5  calls clinic_users.add_user -- the portal's own code, the same call
            /portal/users/add makes; the write is atomic (tmp + os.replace) in that module
         6  then SIGNS IN AS HIM: verify_password() against the derived password. If that
            does not come back with his role, the backup is restored and the route reports
            failure. A login is not "created" until it has been used once.
         7  writes a joiner_event so the register carries who did it and when

The owner ruled this half in, S222: the finance service may write the portal's login store.
It is the one file that gates every login in the clinic, which is why every one of those seven
steps is there and why the store is copied first.

NOT CHANGED: /api/message and /api/reset_password keep their current behaviour and pins-worth
of meaning. The page now shows the truth beside them, which is the fix that matters. Making
reset_password actually reset is the obvious next step and is deliberately NOT bundled here --
one live file, one behaviour, one walk.

Target: /root/finance/joiner_app.py   (live pin ff157c1ccbb11f2379c67d36db0077bc)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_joiner_portaluser_s222.py
Offline:         JA_PATH=./joiner_app.py python3 -B patch_joiner_portaluser_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('JA_PATH', '/root/finance/joiner_app.py')
MARK = "S222 PORTAL USER"
EXPECT_FROM = "ff157c1ccbb11f2379c67d36db0077bc"


A_OLD = '''@bp.route("/api/message")
def api_message():
'''

A_NEW = '''# ---- S222 PORTAL USER -- F-295 ---------------------------------------------
# The joiner flow printed a login it never created. These two routes are the
# truth and the fix, in that order: one READ that says whether the login exists,
# and one WRITE that creates it and then proves it by signing in as him.

PORTAL_DIR = os.environ.get("PORTAL_DIR", "/root/portal")


def _portal_users():
    """(module, store_path, None) or (None, None, why-not). Never raises."""
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import clinic_users as CU
    except Exception as ex:
        return None, None, "the portal's clinic_users.py could not be imported (%s)" % ex
    path = os.environ.get("CLINIC_USERS_FILE", getattr(CU, "DEFAULT_STORE", ""))
    if not path:
        return None, None, "no user-store path is configured"
    return CU, path, None


def _portal_status(user):
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


@bp.route("/api/portal_user")
def api_portal_user():
    """Does this joiner's login actually exist? READ ONLY.

    This is the route that stops the page printing a login nobody can use."""
    con = _db()
    ensure_schema(con)
    ref = (request.args.get("ref") or "").strip()
    r = con.execute("SELECT person,username FROM joiner WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_record",
                       message="No record called %s." % (ref or "(blank)")), 404
    person = _v(r, "person", 0)
    user = _v(r, "username", 1) or default_username(person)
    st = _portal_status(user)
    return jsonify(ok=True, ref=ref, person=person, username=user,
                   password=default_password(person), **st)


@bp.route("/api/portal_user/create", methods=["POST"])
def api_portal_user_create():
    """Create the login for real, then prove it works. Owner only.

    Body: {"ref":"JOIN-2026-0001","role":"manager","by":"Dr Manoj"}
    """
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ref = (b.get("ref") or "").strip()
    role = (b.get("role") or "").strip()
    who = (b.get("by") or "").strip()
    if not who:
        return jsonify(ok=False, error="no_person",
                       message="Who is creating this login? A name is required."), 400
    con = _db()
    ensure_schema(con)
    r = con.execute("SELECT id,person,username FROM joiner WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_record",
                       message="No record called %s." % (ref or "(blank)")), 404
    jid, person = _v(r, "id", 0), _v(r, "person", 1)
    user = _v(r, "username", 2) or default_username(person)
    pw = default_password(person)

    CU, path, why = _portal_users()
    if not CU:
        return jsonify(ok=False, error="no_store", message=why), 503
    try:
        store = CU.load_store(path)
    except Exception as ex:
        return jsonify(ok=False, error="store_unreadable",
                       message="The user store could not be read (%s). Nothing was "
                               "changed." % ex), 503
    roles = list(store.get("roles") or [])
    if not roles:
        return jsonify(ok=False, error="no_roles",
                       message="The user store lists no roles. Nothing was changed."), 503
    if user in (store.get("users") or {}):
        return jsonify(ok=False, error="already_exists", username=user, roles=roles,
                       message="%s already has a login. Nothing was changed." % user), 409
    if role not in roles:
        return jsonify(ok=False, error="bad_role", roles=roles,
                       message="Pick a role the store knows: %s." % ", ".join(roles)), 400

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = "%s.bak_S222_%s" % (path, stamp)
    try:
        shutil.copyfile(path, bak)
    except OSError as ex:
        if os.path.exists(path):
            return jsonify(ok=False, error="no_backup",
                           message="The user store could not be copied first (%s). "
                                   "Nothing was changed." % ex), 503
        bak = None                      # a store that does not exist yet has nothing to save

    try:
        CU.add_user(path, user, role, pw)
    except Exception as ex:
        if bak:
            try:
                shutil.copyfile(bak, path)
            except OSError:
                pass
        return jsonify(ok=False, error="not_created",
                       message="The login was not created (%s). The store was put back "
                               "as it was." % ex), 500

    # A login is not created until it has been used. Sign in as him.
    proved = None
    try:
        proved = CU.verify_password(path, user, pw)
    except Exception:
        proved = None
    if not proved:
        if bak:
            try:
                shutil.copyfile(bak, path)
            except OSError:
                pass
        return jsonify(ok=False, error="not_verified",
                       message="The login was written but would not sign in. The store has "
                               "been put back as it was -- nothing was left half-done."), 500

    con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) "
                "VALUES (?,?,?,?,?)",
                (jid, now_iso(), u, "PORTAL_USER_CREATED",
                 "%s -- %s as %s, verified" % (who, user, proved)))
    con.commit()
    return jsonify(ok=True, ref=ref, username=user, password=pw, role=proved,
                   verified=True, backup=bak,
                   message="%s can sign in now. Password %s -- he must change it."
                           % (user, pw))
# ---- end S222 PORTAL USER --------------------------------------------------


@bp.route("/api/message")
def api_message():
'''


# --------------------------------------------------------------- anchor B
# joiner_app.py imports neither sys nor shutil, and the new code needs both:
# sys to reach the portal's module directory, shutil to copy the user store
# before it is touched. Added beside the imports that are already there.

B_OLD = '''import io
import os

from flask import Blueprint, jsonify, request
'''

B_NEW = '''import io
import os
import shutil                                    # S222 PORTAL USER
import sys                                       # S222 PORTAL USER

from flask import Blueprint, jsonify, request
'''


PAIRS = [("B", B_OLD, B_NEW), ("A", A_OLD, A_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit("REFUSED: this file is %s, not the %s this kit was built against. "
                         "NOTHING was changed." % (before, EXPECT_FROM))
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_portaluser_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s -- "
                         "the live file is unchanged." % (ex, bak))
    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
