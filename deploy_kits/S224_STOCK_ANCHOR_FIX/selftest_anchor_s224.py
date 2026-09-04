#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_anchor_s224.py -- PROVENANCE (F-299): the kit's two full files are
exactly what the two patchers produce from the LIVE bytes, and nothing else.

The live bytes are reproduced from the repo's own chain, every link md5-checked:
  returns_desk.py    S214 afc8b0d0 -> S221_JAANKARI 1dc1fd62 -> S222_DESK_USERS 3296eca0 (LIVE)
  returns_desk.html  S214 32c4b8cc -> S221_JAANKARI 6d98e1b0 (LIVE, unchanged by S222)
then this kit's patchers run over them, and the result must equal the kit copy
byte for byte. Also: both patchers say "already patched" on a second run and
REFUSE (exit 2, file untouched) on a file that is not the live one.

    KITS=/path/to/deploy_kits python3 -B selftest_anchor_s224.py
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.environ.get("KITS", os.path.dirname(HERE))
N = {"pass": 0, "fail": 0}


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def check(name, got, want=True):
    ok = got == want
    N["pass" if ok else "fail"] += 1
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "   got=%r want=%r" % (got, want)))


def run(patcher, env):
    p = subprocess.run([sys.executable, "-B", patcher], env=dict(os.environ, **env),
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def main():
    tmp = tempfile.mkdtemp(prefix="s224prov_")
    try:
        py = os.path.join(tmp, "returns_desk.py")
        html = os.path.join(tmp, "returns_desk.html")
        shutil.copy(os.path.join(KITS, "S214_RETURNS_DESK", "returns_desk.py"), py)
        shutil.copy(os.path.join(KITS, "S214_RETURNS_DESK", "returns_desk.html"), html)
        check("S214 base returns_desk.py afc8b0d0", md5(py)[:8], "afc8b0d0")
        check("S214 base returns_desk.html 32c4b8cc", md5(html)[:8], "32c4b8cc")
        run(os.path.join(KITS, "S221_JAANKARI", "patch_desk_jaankari_s221.py"), {"RD_PATH": py})
        check("after S221_JAANKARI returns_desk.py 1dc1fd62", md5(py)[:8], "1dc1fd62")
        run(os.path.join(KITS, "S221_JAANKARI", "patch_deskpage_jaankari_s221.py"), {"RDP_PATH": html})
        check("after S221_JAANKARI returns_desk.html 6d98e1b0 == LIVE", md5(html)[:8], "6d98e1b0")
        run(os.path.join(KITS, "S222_DESK_USERS", "patch_desk_users_s222.py"), {"RD_PATH": py})
        check("after S222_DESK_USERS returns_desk.py 3296eca0 == LIVE", md5(py)[:8], "3296eca0")

        # a wrong base is refused, untouched
        wrong = os.path.join(tmp, "wrong.py")
        shutil.copy(os.path.join(KITS, "S214_RETURNS_DESK", "returns_desk.py"), wrong)
        rc, out = run(os.path.join(HERE, "patch_desk_anchor_s224.py"), {"RD_PATH": wrong})
        check("server patcher REFUSES a non-live base (exit 2)", rc, 2)
        check("...and leaves it untouched", md5(wrong)[:8], "afc8b0d0")

        rc, out = run(os.path.join(HERE, "patch_desk_anchor_s224.py"), {"RD_PATH": py})
        check("server patcher runs on the live bytes (exit 0)", rc, 0)
        check("KIT returns_desk.py == patched live bytes", md5(py), md5(os.path.join(HERE, "returns_desk.py")))
        rc, out = run(os.path.join(HERE, "patch_desk_anchor_s224.py"), {"RD_PATH": py})
        check("server patcher is idempotent", (rc, "already patched" in out), (0, True))

        rc, out = run(os.path.join(HERE, "patch_deskpage_anchor_s224.py"), {"RDP_PATH": html})
        check("page patcher runs on the live bytes (exit 0)", rc, 0)
        check("KIT returns_desk.html == patched live bytes", md5(html), md5(os.path.join(HERE, "returns_desk.html")))
        rc, out = run(os.path.join(HERE, "patch_deskpage_anchor_s224.py"), {"RDP_PATH": html})
        check("page patcher is idempotent", (rc, "already patched" in out), (0, True))

        for f in ("returns_desk.py", "returns_desk.html", "patch_desk_anchor_s224.py",
                  "patch_deskpage_anchor_s224.py", "RENDER_TEST_anchor_s224.py"):
            with open(os.path.join(HERE, f), "rb") as fh:
                b = fh.read()
            check("%s is LF-only" % f, b"\r" not in b)
        import py_compile
        cf = os.path.join(tmp, "c.pyc")
        py_compile.compile(os.path.join(HERE, "returns_desk.py"), cfile=cf, doraise=True)
        check("kit returns_desk.py compiles", True)
        with open(os.path.join(HERE, "returns_desk.html"), encoding="utf-8") as fh:
            h = fh.read()
        check("page: exactly one anchor box builder", h.count("function jkAnchorBox"), 1)
        check("page: the box sits under the spot heading", "if(groups[g][0]==='spot')pend+=jkAnchorBox();" in h)
        check("page: script tags balanced", h.count("<script"), h.count("</script"))
        print("\nKIT PINS (predicted):")
        for f in ("returns_desk.py", "returns_desk.html"):
            print("  %s  /root/finance/%s" % (md5(os.path.join(HERE, f)), f))
        print("\n%s  %d passed, %d failed" % ("SELFTEST GREEN" if not N["fail"] else "SELFTEST RED", N["pass"], N["fail"]))
        return 0 if not N["fail"] else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
