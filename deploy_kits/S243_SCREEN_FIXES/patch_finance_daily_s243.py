#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_finance_daily_s243.py -- S243: /finance/daily is the MAKER's day-entry form
(Darpan). Its handler turned the 403 from require("maker") into a bare redirect to
/portal, so the doctor -- medical's CHECKER, never its maker (S179) -- who opens the
Daily Sale tile is bounced to the portal with no explanation. The maker gate is NOT
widened (owner's decision, S243): a signed-in CHECKER is sent to his Review console
instead; everyone else is refused exactly as before.

Designed to run ON THE BOX against the live file, which is not in the repository:

    /root/wa/venv/bin/python3 -B patch_finance_daily_s243.py
        reads  FA_PATH (default /root/finance/finance_app.py)
        writes FA_PATH.new  (never the live file itself)
        prints the md5 before and after

Refuses unless (a) the live md5 starts with the S243_AUTOAPPLY pin f002defb and
(b) the anchor occurs exactly once in the live bytes. Prints ALREADY PATCHED and
exits 0 when the marker is already present.
"""
import hashlib
import io
import os
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
FROM_PIN8 = os.environ.get("FA_FROM_PIN8", "f002defb")     # S243_AUTOAPPLY pin, 13-Sep (history 81db4854 -> 72bc8323 -> f002defb)
MARK = "S243: a checker (the doctor) lands on his Review console"

OLD = ('    u, err = require("maker")\n'
       '    if err:\n'
       '        return redirect(PORTAL_LOGIN, code=302)\n'
       '    return send_file(os.path.join(UI_DIR, "finance_daily.html"))\n')
NEW = ('    u, err = require("maker")\n'
       '    if err:\n'
       '        # S243: a checker (the doctor) lands on his Review console, not the\n'
       '        # portal. The maker gate is unchanged; only the destination of the\n'
       '        # refusal moved, and only for a login that holds checker here.\n'
       '        u0 = current_user()\n'
       '        if "checker" in roles_for(db(), UNIT, u0["user"], u0["role"]):\n'
       '            return redirect("/finance/review", code=302)\n'
       '        return redirect(PORTAL_LOGIN, code=302)\n'
       '    return send_file(os.path.join(UI_DIR, "finance_daily.html"))\n')


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    out = TARGET + ".new"
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    print("source %s md5 %s" % (TARGET, md5(raw)))
    if MARK in src:
        print("ALREADY PATCHED -- nothing to do")
        return 0
    if FROM_PIN8 and not md5(raw).startswith(FROM_PIN8):
        print("REFUSED: source pin is not %s... -- the live file moved since this patch was built" % FROM_PIN8)
        return 2
    n = src.count(OLD)
    if n != 1:
        print("REFUSED: anchor occurs %d times, need exactly 1" % n)
        return 2
    if src.count('@app.route("/finance/daily")\ndef page_daily():') != 1:
        print("REFUSED: the /finance/daily route is not where this patch expects it")
        return 2
    new = src.replace(OLD, NEW, 1)
    compile(new, TARGET, "exec")
    io.open(out, "w", encoding="utf-8", newline="\n").write(new)
    print("wrote %s md5 %s" % (out, md5(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
