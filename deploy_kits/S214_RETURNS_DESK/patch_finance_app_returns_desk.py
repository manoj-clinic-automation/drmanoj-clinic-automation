#!/usr/bin/env python3
"""patch_finance_app_returns_desk.py -- S214: mount the Vaapsi Desk.

Inserts ONE guarded block into the live finance_app.py (the S208 stock-mount
mechanism, reused verbatim in shape): exact-anchor insert before __main__,
single-occurrence checks on everything relied upon, timestamped backup,
py_compile with automatic restore on failure. Refuses rather than guesses.

    /root/wa/venv/bin/python3 -B patch_finance_app_returns_desk.py /root/finance/finance_app.py
"""
import datetime
import io
import os
import py_compile
import shutil
import sys

BEGIN = "# --- S214_RETURNS_DESK begin -- the counter return flow, mounted here ---"
END = "# --- S214_RETURNS_DESK end ---"

MOUNT = BEGIN + """
# Two lines, at IMPORT time (gunicorn never reaches __main__). returns_desk
# owns its own tables inside the same finance.db, behind the same SSO gate.
# Reception staff reach it through the dedicated `returns` unit role
# (seed_desk_roles.py); the desk page sits at /finance/returns/desk.
import returns_desk                                           # noqa: E402
returns_desk.init(app, db, require, unit=UNIT)
""" + END + "\n\n"

MAIN_ANCHOR = '\nif __name__ == "__main__":'
REQUIRED = ("\ndef require(", "\ndef db(", "\nUNIT = ", "\napp = Flask(")


def main(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    if BEGIN in src:
        print("ALREADY MOUNTED -- nothing to do.")
        return 0
    for r in REQUIRED:
        n = src.count(r)
        if n != 1:
            print("REFUSING: %r occurs %d times (need exactly 1)." % (r, n))
            return 2
    if src.count(MAIN_ANCHOR) != 1:
        print("REFUSING: __main__ anchor not unique.")
        return 2
    bak = "%s.bak_S214_desk_%s" % (path, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(path, bak)
    out = src.replace(MAIN_ANCHOR, "\n" + MOUNT + MAIN_ANCHOR[1:], 1)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    try:
        py_compile.compile(path, doraise=True)
    except Exception as exc:                                   # noqa: BLE001
        shutil.copy2(bak, path)
        print("COMPILE FAILED -- original restored from %s\n%s" % (bak, exc))
        return 1
    print("MOUNTED. backup: %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/root/finance/finance_app.py"))
