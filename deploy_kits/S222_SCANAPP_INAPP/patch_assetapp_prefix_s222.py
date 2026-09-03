#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_assetapp_prefix_s222.py -- S222: let the scan app answer under a prefix, so it
stops throwing staff out of the portal app window.

THE PROBLEM, stated exactly.

The portal PWA declares scope "/" on followup.dr-manoj.in. Every tile that points at a path
under that host opens INSIDE the app window; every tile that points at another host opens with
browser chrome and the staff member is dropped out of the app. The portal's own comment says so.

Only two tiles still do that, and they are the two things EVERY staff login carries by default:
Attendance (parked by the owner -- its app pulls punches from the biometric machine) and this
one, the scan app at assets.dr-manoj.in.

WHY THE PROVEN S200 PATTERN DOES NOT TRANSFER

S200 brought the staff register in with one LiteSpeed context, `/register` -> 127.0.0.1:8044,
and it worked cleanly because THAT app's routes were already namespaced: /register/health,
/register/review, /register/salary. Nothing had to be rewritten.

The scan app's routes are FLAT at the root -- /, /login, /intake, /bills, /assets, /files,
/scan, /drafts, /staff, /vendors, /renewals, /purchases, /admin, /account, /api/due. Ten route
families. A single context cannot cover them, and ten contexts would claim ten top-level paths
on the portal's own domain -- including /assets, which means something different to each app.

So the app itself has to understand a prefix. That is this patch, and it is nine lines.

WHAT IT DOES, AND WHAT IT DELIBERATELY DOES NOT

A WSGI shim ahead of Flask. When a request arrives WITH the prefix it strips it and records it
in SCRIPT_NAME, so Flask routes normally and url_for(), redirect() and every link in every
template come back prefixed on their own. When a request arrives WITHOUT the prefix -- which is
every request assets.dr-manoj.in serves today -- the shim does nothing at all.

  ONE PROCESS, BOTH SHAPES. assets.dr-manoj.in/intake keeps working exactly as it does now;
  followup.dr-manoj.in/scanapp/intake starts working. Nothing is moved, no port changes, and
  the subdomain is not retired.

The prefix is /scanapp and not /assets ON PURPOSE: the app already has its own /assets route
for the asset register, and a prefix by that name would read as a collision to every future
reader even though the shim would handle it.

IT IS NOT AN AUTH BYPASS. The shim runs before Flask and only edits PATH_INFO and SCRIPT_NAME.
Every route still reaches login_required, and A-D21's RECEPTION_OK allow-list is untouched --
a reception user is refused /bills under the prefix exactly as at the root. The kit's gate
asserts that in both shapes rather than assuming it.

It also adds /healthz -- two lines, unauthenticated, returning the word ok and nothing else --
because the installer must not wire a dead backend into the vhost and this app had nothing to
ask. The portal's PWA icon and manifest routes are unauthenticated for the same kind of reason.

Target: /root/assetapp/asset_register.py   (live pin 958c7fb71d716ae82d50efa77ac0fbdc,
        reproduced offline: repo assetapp/asset_register.py 0cd8fc3b + the S219 pharma-lane
        patcher = that exact pin.)
Run on the box:  /root/wa/venv/bin/python3 -B /root/assetapp/patch_assetapp_prefix_s222.py
Offline:         AR_PATH=./asset_register.py python3 -B patch_assetapp_prefix_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('AR_PATH', '/root/assetapp/asset_register.py')
MARK = "S222 SCANAPP PREFIX"
EXPECT_FROM = "958c7fb71d716ae82d50efa77ac0fbdc"


A_OLD = '''# ---------------------------------------------------------------- main
if __name__ == "__main__":
'''

A_NEW = '''# ---------------------------------------------------------------- S222 SCANAPP PREFIX
# The portal PWA has scope "/" on followup.dr-manoj.in, so a tile pointing at
# another host drops the staff member out of the app window. This app's routes
# are flat at the root, so one LiteSpeed context cannot reach them the way
# S200's /register context reached the staff register. The app learns the
# prefix instead.
#
# WITH the prefix   -> strip it, record it in SCRIPT_NAME, and Flask's url_for,
#                      redirects and template links all come back prefixed.
# WITHOUT it        -> untouched. assets.dr-manoj.in keeps working exactly as
#                      it does today; nothing moves and no port changes.
SCANAPP_PREFIX = (os.environ.get("SCANAPP_PREFIX", "/scanapp") or "").rstrip("/")


class _ScanappPrefix(object):
    """Serve the same app at the root AND under a prefix. WSGI-level, so it
    cannot change authorisation: it edits PATH_INFO and SCRIPT_NAME and hands
    the request on. login_required and the A-D21 allow-list are unaffected."""

    def __init__(self, wsgi, prefix):
        self.wsgi = wsgi
        self.prefix = prefix

    def __call__(self, environ, start_response):
        p = environ.get("PATH_INFO", "") or ""
        if self.prefix and (p == self.prefix or p.startswith(self.prefix + "/")):
            environ["SCRIPT_NAME"] = (environ.get("SCRIPT_NAME", "") or "") + self.prefix
            environ["PATH_INFO"] = p[len(self.prefix):] or "/"
        return self.wsgi(environ, start_response)


if SCANAPP_PREFIX:
    app.wsgi_app = _ScanappPrefix(app.wsgi_app, SCANAPP_PREFIX)


@app.route("/healthz")
def healthz_s222():
    """So the vhost installer can refuse to wire a dead backend. Says one word."""
    return "ok", 200, {"Content-Type": "text/plain"}


# ---------------------------------------------------------------- main
if __name__ == "__main__":
'''


PAIRS = [("A", A_OLD, A_NEW)]


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
    bak = TARGET + ".bak_S222_prefix_" + stamp
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
    print("next     systemctl restart assetapp.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
