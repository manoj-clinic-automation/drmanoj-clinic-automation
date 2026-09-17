#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s284.py -- offline proof for S284_SHAVEZ_MAKER. Nothing live is touched.

    python3 -B selftest_s284.py --live /path/to/a/copy/of/purchase_app.py --s282 /path/to/S282_LINE_OWNER

The live copy is first brought to the S282 state (the pin S284 installs on), then
the S284 patcher is applied to it. Then the helper is lifted out of the patched file
together with the real _is_viewer_only and _who, and asked the questions that
matter: a maker writes, a checker writes, a viewer named in the setting writes, a
viewer not named does not, no setting admits nobody, no table admits nobody, a
name matches regardless of case and spacing. The seed script is run on a fixture.
"""
import argparse
import ast
import hashlib
import io
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("ok " if ok else "FAIL", name, ("  -- " + str(detail)) if detail else ""))
    if not ok:
        FAILS.append(name)


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def lift(path, names):
    src = io.open(path, "r", encoding="utf-8").read()
    tree = ast.parse(src)
    body = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in names) or
            (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in names for t in n.targets))]
    mod = ast.Module(body=body, type_ignores=[])
    import re
    ns = {"re": re}
    exec(compile(mod, path, "exec"), ns)
    return ns


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True)
    ap.add_argument("--s282", required=True, help="the S282_LINE_OWNER kit folder")
    a = ap.parse_args(argv)
    py = sys.executable
    tmp = tempfile.mkdtemp(prefix="s284_")
    try:
        work = os.path.join(tmp, "purchase_app.py")
        shutil.copy2(a.live, work)
        print("part 1 -- bring the copy to the S282 state, then patch")
        r = subprocess.run([py, "-B", os.path.join(a.s282, "patch_line_owner_s282.py"), "--file", work],
                           capture_output=True, text=True)
        check("S282 applied first (the pin S284 installs on)", r.returncode == 0, r.stdout.strip()[-80:])
        before = md5(work)
        print("  S282 state pin: %s" % before)
        import patch_cheque_writer_s284 as pm
        src = io.open(work, "r", encoding="utf-8").read()
        for i, (old, _new) in enumerate(pm.EDITS):
            check("anchor %s present exactly once" % "ABCD"[i], src.count(old) == 1, src.count(old))
        patcher = os.path.join(HERE, "patch_cheque_writer_s284.py")
        r = subprocess.run([py, "-B", patcher, "--file", work, "--from", "0" * 32], capture_output=True, text=True)
        check("wrong --from is refused, nothing written", r.returncode != 0 and md5(work) == before)
        r = subprocess.run([py, "-B", patcher, "--file", work, "--from", before], capture_output=True, text=True)
        check("patch applies", r.returncode == 0, (r.stdout + r.stderr).strip()[-120:])
        after = md5(work)
        print("  S284 pin: %s" % after)
        try:
            py_compile.compile(work, doraise=True)
            check("patched file compiles", True)
        except Exception as e:  # noqa: BLE001
            check("patched file compiles", False, e)
        src2 = io.open(work, "r", encoding="utf-8").read()
        check("helper used at four sites and defined once",
              src2.count("_cheque_writer_s284(") == 5 and src2.count("def _cheque_writer_s284(") == 1,
              src2.count("_cheque_writer_s284("))
        check("the four old anchors are gone (each replaced, none left behind)",
              all(src2.count(old) == 0 for old, _n in pm.EDITS) and
              all(src2.count(new) == 1 for _o, new in pm.EDITS))
        check("the sheet's own editable flag is untouched (carry-forward stays maker/checker)",
              "editable = (not final) and (not _is_viewer_only(u))" in src2)
        check("the phone book gate is untouched", "def _book_allowed(u, con):" in src2)
        r = subprocess.run([py, "-B", patcher, "--file", work, "--from", after], capture_output=True, text=True)
        check("second run says ALREADY PATCHED, pin unchanged", "ALREADY" in r.stdout and md5(work) == after)

        print("part 2 -- the helper, lifted out of the patched file with the real _is_viewer_only and _who")
        ns = lift(work, {"_cheque_writer_s284", "_is_viewer_only", "_who", "CHEQUE_USERS_KEY"})
        fn = ns.get("_cheque_writer_s284")
        check("helper lifted", fn is not None)
        db = os.path.join(tmp, "f.db")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
        con.commit()
        maker = {"user": "darpan", "role": "maker", "roles": ["maker"]}
        checker = {"user": "manoj", "role": "checker", "roles": ["checker"]}
        shavez = {"user": "shavez", "role": "viewer", "roles": ["viewer"]}
        shivani = {"user": "shivani", "role": "viewer", "roles": ["viewer"]}
        check("no setting row: a viewer is refused", fn(shavez, con) is False)
        check("no setting row: a maker still writes", fn(maker, con) is True)
        check("no setting row: the checker still writes", fn(checker, con) is True)
        r = subprocess.run([py, "-B", os.path.join(HERE, "seed_setting_s284.py"), "--db", db, "--value", "shavez"],
                           capture_output=True, text=True)
        check("seed writes the row", r.returncode == 0 and "now 'shavez'" in r.stdout, r.stdout.strip())
        check("named viewer writes", fn(shavez, con) is True)
        check("unnamed viewer does not", fn(shivani, con) is False)
        check("a maker is unaffected by the list", fn(maker, con) is True)
        con.execute("UPDATE setting SET value=' Shavez ,amir' WHERE key='purchase.cheque_users'"); con.commit()
        check("case and spacing do not matter; two names work", fn(shavez, con) is True and
              fn({"user": "AMIR", "role": "viewer", "roles": ["viewer"]}, con) is True)
        check("a login with no name is refused", fn({"user": "", "role": "viewer", "roles": ["viewer"]}, con) is False)
        r = subprocess.run([py, "-B", os.path.join(HERE, "seed_setting_s284.py"), "--db", db, "--value", ""],
                           capture_output=True, text=True)
        check("the undo (empty list) writes", r.returncode == 0)
        check("after the undo the viewer is refused again", fn(shavez, con) is False)
        con.close()
        con2 = sqlite3.connect(os.path.join(tmp, "empty.db"))
        check("no setting TABLE at all: refused, not a crash", fn(shavez, con2) is False)
        con2.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n = len(FAILS)
    print("S284 selftest: %d check(s) failed%s" % (n, (": " + ", ".join(FAILS)) if n else ""))
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
