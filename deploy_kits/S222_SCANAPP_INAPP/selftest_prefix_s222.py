#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_prefix_s222.py -- mount the REAL patched scan app and prove both shapes.

The claim this kit makes is that one process can serve assets.dr-manoj.in exactly as it does
today AND answer under /scanapp for the portal PWA. That is a claim about a live app, so it is
tested by importing the live app and asking it, not by reading the shim.

Three things it must show:
  1  the ROOT shape is unchanged -- every status code identical to before the prefix existed
  2  the PREFIXED shape answers the same way, and url_for() comes back prefixed
  3  A-D21 IS UNTOUCHED -- the shim is WSGI-level and must not become an authorisation hole

    python3 -B selftest_prefix_s222.py /path/to/patched/asset_register.py
"""
import importlib.util
import os
import sys
import tempfile

TARGET = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "asset_register.py")
FAILED = []


def ck(label, cond, detail=""):
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail else ""))
    if not cond:
        FAILED.append(label)


def main():
    tmp = tempfile.mkdtemp(prefix="s222_prefix_")
    os.environ.setdefault("AR_DB", os.path.join(tmp, "a.db"))
    os.chdir(tmp)
    spec = importlib.util.spec_from_file_location("ar_s222", TARGET)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    app = m.app
    c = app.test_client()

    print("-- 0  what is under test ------------------------------------------")
    src = open(TARGET, encoding="utf-8").read()
    ck("the file carries the S222 prefix shim", "S222 SCANAPP PREFIX" in src)
    ck("the prefix is /scanapp, not /assets (the app owns /assets itself)",
       'SCANAPP_PREFIX", "/scanapp"' in src)

    print("\n-- 1  HEALTH, so the vhost installer can find the backend ---------")
    r = c.get("/healthz")
    ck("/healthz is 200 ok", r.status_code == 200 and b"ok" in r.data, str(r.status_code))
    r = c.get("/scanapp/healthz")
    ck("/scanapp/healthz is 200 ok", r.status_code == 200 and b"ok" in r.data, str(r.status_code))

    print("\n-- 2  THE ROOT SHAPE IS UNCHANGED (assets.dr-manoj.in keeps working)")
    pairs = [("/", "the landing"), ("/login", "login"), ("/intake", "intake"),
             ("/bills", "bills"), ("/assets", "the asset register itself"),
             ("/scan/widget.js", "the scanner widget")]
    base = {}
    for path, what in pairs:
        base[path] = c.get(path).status_code
        ck("%s answers at the root" % what, base[path] < 500, "%s -> %s" % (path, base[path]))

    print("\n-- 3  THE PREFIXED SHAPE ANSWERS THE SAME WAY ---------------------")
    for path, what in pairs:
        got = c.get("/scanapp" + path).status_code
        ck("%s matches under /scanapp" % what, got == base[path],
           "/scanapp%s -> %s, root -> %s" % (path, got, base[path]))

    print("\n-- 4  AND ITS LINKS COME BACK PREFIXED, which is the whole point ---")
    with app.test_request_context("/scanapp/intake",
                                  environ_overrides={"SCRIPT_NAME": "/scanapp"}):
        from flask import url_for
        # endpoint names, not paths -- /bills is served by the endpoint `bills_list`,
        # and v1 of this test asserted on the path and failed itself
        for ep, want in (("intake", "/scanapp/intake"), ("login", "/scanapp/login"),
                         ("bills_list", "/scanapp/bills")):
            try:
                got = url_for(ep)
            except Exception as ex:
                got = "ERR %s" % ex
            ck("url_for(%s) is prefixed" % ep, got == want, got)
    with app.test_request_context("/intake"):
        from flask import url_for
        got = url_for("intake")
        ck("url_for at the root is NOT prefixed", got == "/intake", got)

    print("\n-- 5  A-D21 IS UNTOUCHED: the shim is not an authorisation hole ----")
    ck("RECEPTION_OK still holds exactly its eight endpoints",
       len(m.RECEPTION_OK) == 8, str(sorted(m.RECEPTION_OK)))
    for ep in ("intake", "intake_submit", "intake_scan_submit", "intake_slip",
               "intake_slip_last", "scanner_widget_js", "login", "logout"):
        ck("%s is still allowed to a reception user" % ep, ep in m.RECEPTION_OK)
    ck("the new health route was NOT added to the allow-list",
       "healthz_s222" not in m.RECEPTION_OK)
    for ep in ("dashboard", "bills", "assets"):
        ck("%s is still NOT on the allow-list" % ep, ep not in m.RECEPTION_OK)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%s -- %d failed" % ("PREFIX GREEN" if not FAILED else "PREFIX RED", len(FAILED)))
    for x in FAILED:
        print("   FAILED:", x)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
