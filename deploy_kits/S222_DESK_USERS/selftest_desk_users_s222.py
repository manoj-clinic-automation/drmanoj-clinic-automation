#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_desk_users_s222.py -- proves the F-296 gate OFFLINE, before the box.

It does not test a copy of the logic. It takes a real returns_desk.py, runs the
real patcher over it, imports the patched file, and calls the real `_auth()`
through a stub `require()` shaped exactly like finance_app's -- which returns
(u, None) with u = dict(user=..., role=..., roles=[...]), or (None, (body, 403)).

flask is stubbed to Blueprint/jsonify/request because this runs where flask is
not installed. Nothing else about the file is faked.

    python -B selftest_desk_users_s222.py [path-to-a-returns_desk.py]

Default source: ../S214_RETURNS_DESK/returns_desk.py (the base file; the gate
lives in _auth(), which S220/S221 did not touch). Point it at a copy of the LIVE
file when one is at hand and the same test proves the live shape.
"""
import importlib.util
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.join(HERE, "..", "S214_RETURNS_DESK", "returns_desk.py")
PATCHER = os.path.join(HERE, "patch_desk_users_s222.py")

FAILS = []
N = 0


def check(name, got, want):
    global N
    N += 1
    if got == want:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s   got=%r want=%r" % (name, got, want))
        FAILS.append(name)


def _stub_flask():
    m = types.ModuleType("flask")

    class Blueprint(object):
        def __init__(self, *a, **k):
            pass

        def route(self, *a, **k):
            def deco(fn):
                return fn
            return deco

    def jsonify(**kw):
        return dict(kw)

    class _Req(object):
        args = {}

        def get_json(self, *a, **k):
            return {}
    m.Blueprint = Blueprint
    m.jsonify = jsonify
    m.request = _Req()
    sys.modules["flask"] = m


def main(src=None):
    src = src or DEFAULT_SRC
    if not os.path.exists(src):
        raise SystemExit("no source file at %s" % src)
    tmp = tempfile.mkdtemp(prefix="s222_desk_")
    target = os.path.join(tmp, "returns_desk.py")
    shutil.copyfile(src, target)
    # the html need not exist; no route is called here.

    env = dict(os.environ, RD_PATH=target)
    p = subprocess.run([sys.executable, "-B", PATCHER], env=env,
                       capture_output=True, text=True)
    print(p.stdout.strip())
    if p.returncode != 0:
        print(p.stderr.strip())
        raise SystemExit("the patcher refused -- selftest cannot continue")

    _stub_flask()
    spec = importlib.util.spec_from_file_location("rd_s222", target)
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)

    db = os.path.join(tmp, "t.db")
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.commit()

    def getdb():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    people = {
        "amir":    dict(user="amir",    role="staff",  roles=["viewer"]),
        "alisha":  dict(user="alisha",  role="staff",  roles=["viewer"]),
        "shivani": dict(user="shivani", role="staff",  roles=["viewer"]),
        "shavez":  dict(user="shavez",  role="staff",  roles=["viewer"]),
        "darpan":  dict(user="darpan",  role="staff",  roles=["maker", "viewer"]),
        "manoj":   dict(user="manoj",   role="doctor", roles=["checker"]),
        "ghost":   dict(user="ghost",   role="staff",  roles=["viewer"]),
    }
    who = {"name": "amir"}

    def require(*roles, **kw):
        u = people[who["name"]]
        if not set(u["roles"]).intersection(roles):
            return None, ({"ok": False, "error": "not_permitted"}, 403)
        return dict(u), None

    rd.init.__globals__  # noqa -- init is not called; wire the globals directly
    rd._db = getdb
    rd._require = require
    rd._unit = "medical"

    def allowed(name):
        who["name"] = name
        u, err = rd._auth()
        return err is None

    def refusal(name):
        who["name"] = name
        u, err = rd._auth()
        if err is None:
            return None
        body, code = err
        return (body.get("error"), code)

    def setrow(val):
        c = sqlite3.connect(db)
        c.execute("DELETE FROM setting WHERE key='returns.desk_users'")
        if val is not None:
            c.execute("INSERT INTO setting (key, value) VALUES ('returns.desk_users', ?)",
                      (val,))
        c.commit()
        c.close()

    print("\n-- 1  UNSET: nothing changes (the owner's constraint) ------------")
    setrow(None)
    for n in ("amir", "alisha", "shivani", "shavez", "darpan", "manoj", "ghost"):
        check("unset: %s reaches the desk" % n, allowed(n), True)

    print("\n-- 2  BLANK is also unset ----------------------------------------")
    setrow("")
    check("blank: amir reaches the desk", allowed("amir"), True)
    setrow("   ")
    check("spaces: amir reaches the desk", allowed("amir"), True)

    print("\n-- 3  SET: the desk is named -------------------------------------")
    setrow("darpan,shavez,alisha,shivani")
    check("AMIR IS REFUSED", allowed("amir"), False)
    check("amir's refusal is not_desk_user/403", refusal("amir"),
          ("not_desk_user", 403))
    for n in ("alisha", "shivani", "shavez", "darpan"):
        check("%s still reaches the desk" % n, allowed(n), True)
    check("manoj (checker, NOT in the list) reaches the desk", allowed("manoj"), True)
    check("ghost (a future viewer, not listed) IS REFUSED", allowed("ghost"), False)

    print("\n-- 4  the owner may type the row any way he likes -----------------")
    setrow(" Alisha ; SHAVEZ , shivani  darpan ")
    check("case and spacing tolerated: alisha in", allowed("alisha"), True)
    check("case and spacing tolerated: shavez in", allowed("shavez"), True)
    check("case and spacing tolerated: amir still out", allowed("amir"), False)

    print("\n-- 5  a maker is never locked out by the list ---------------------")
    setrow("nobody")
    check("darpan (maker) reaches the desk", allowed("darpan"), True)
    check("manoj (checker) reaches the desk", allowed("manoj"), True)
    check("alisha (viewer, not listed) is refused", allowed("alisha"), False)

    print("\n-- 6  a broken database ALLOWS (deliberate, see the header) -------")
    setrow("darpan")
    def broken():
        raise sqlite3.OperationalError("no such table: setting")
    rd._db = broken
    check("db error: alisha reaches the desk", allowed("alisha"), True)
    check("db error: amir reaches the desk", allowed("amir"), True)
    rd._db = getdb

    print("\n-- 7  a caller who is not even a viewer is still refused first ----")
    setrow("darpan,shavez,alisha,shivani")
    people["outsider"] = dict(user="outsider", role="staff", roles=["nobody"])
    who["name"] = "outsider"
    u, err = rd._auth()
    check("outsider gets not_permitted (not not_desk_user)",
          (err[0].get("error"), err[1]) if err else None, ("not_permitted", 403))

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s  %d checks, %d failed" %
          ("SELFTEST GREEN" if not FAILS else "SELFTEST RED", N, len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
