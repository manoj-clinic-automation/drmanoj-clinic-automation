#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_diffs_role_s224.py -- provenance of the shipped stock_app.py.

Proves, offline, that the kit's stock_app.py IS the live 4e929d0b bytes plus
this one patch and nothing else: the patcher run on a copy of the live-shape
file must produce byte-for-byte the shipped file; a second run must refuse
(already patched); a run on any other base must refuse and leave it untouched.

    LIVE_SA=/path/to/stock_app.py@4e929d0b python3 -B selftest_diffs_role_s224.py
    (default LIVE_SA: $HOME/s224_diffs_work/stock_app.py.LIVE_4e929d0b)
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.environ.get("LIVE_SA", os.path.join(os.path.expanduser("~"), "s224_diffs_work",
                                              "stock_app.py.LIVE_4e929d0b"))
N = {"pass": 0, "fail": 0}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def check(name, got, want=True):
    ok = got == want
    N["pass" if ok else "fail"] += 1
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "   got=%r want=%r" % (got, want)))


def run(target):
    p = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_diffs_role_s224.py")],
                       env=dict(os.environ, SA_PATH=target), capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    tmp = tempfile.mkdtemp(prefix="s224prov_")
    try:
        t = os.path.join(tmp, "stock_app.py")
        shutil.copy(LIVE, t)
        check("the base is the live pin 4e929d0b", md5(t)[:8], "4e929d0b")
        rc, out = run(t)
        check("the patcher runs clean on the live base", rc, 0)
        check("and produces exactly the shipped stock_app.py", md5(t), md5(os.path.join(HERE, "stock_app.py")))
        check("one dated backup was left beside it",
              len([f for f in os.listdir(tmp) if f.startswith("stock_app.py.bak_S224_diffsrole_")]), 1)
        rc2, out2 = run(t)
        check("a second run refuses (already patched)", (rc2, "already patched" in out2), (0, True))
        check("and leaves the file unchanged", md5(t), md5(os.path.join(HERE, "stock_app.py")))
        w = os.path.join(tmp, "wrong.py")
        open(w, "w").write("print('not the stock app')\n")
        before = md5(w)
        rc3, out3 = run(w)
        check("a wrong base is refused", (rc3, "REFUSING" in out3), (1, True))
        check("and untouched", md5(w), before)
        src = open(os.path.join(HERE, "stock_app.py"), encoding="utf-8").read()
        check("the shipped file has the three S224 anchors",
              (src.count("S224 DIFFS ROLE"), "def _has_role(u, role):" in src, "may_answer=" in src),
              (3, True, True))
        check("no server gate was relaxed: /cause, /decision and /rate still _require(\"checker\") alone",
              src.count('_require("checker")\n'), 3)
        check("no 10-digit run in the shipped files",
              any(__import__("re").search(r"\d{10}", open(os.path.join(HERE, f), encoding="utf-8").read())
                  for f in ("stock_app.py", "stock_diffs.html", "patch_diffs_role_s224.py")), False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d PASS  %d FAIL" % (N["pass"], N["fail"]))
    return 0 if N["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
