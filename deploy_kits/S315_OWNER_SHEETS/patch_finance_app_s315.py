#!/usr/bin/env python3
"""patch_finance_app_s315.py -- mounts owner_sheets in /root/finance/finance_app.py, in the same
guarded shape as S289's petty book and S290's bank door, immediately after the S290 block (an anchor
read from the live file, never inferred). Idempotent. Usage: patch_finance_app_s315.py FINANCE_APP_PY"""
import io
import sys

ANCHOR = "# --- S290_BANK_SMS end ---\n"
BLOCK = """

# --- S315_OWNER_SHEETS begin -- the doctor's own two sheets (18-Sep-2026, D546) ---
# The X-ray price list and the procedure -> consumables map, at /finance/clinic/sheets, inside the
# CLINIC namespace so the front gate resolves the unit without a change to _unit_for_path. Its own
# two tables (owner_service, owner_service_item), created on first request (F-303). It reads
# clinic_day_line and the pharmacy item master READ-ONLY and writes neither.
# GUARDED (S209): a fault inside the module is printed and every other page keeps serving.
try:
    import owner_sheets                                        # noqa: E402
    owner_sheets.init(app, db, require, audit, unit=CLINIC_UNIT)
except Exception as _ex_os:                                    # noqa: BLE001
    print("owner_sheets NOT mounted: %s" % _ex_os, file=sys.stderr)
# --- S315_OWNER_SHEETS end ---
"""


def apply(text):
    if "S315_OWNER_SHEETS begin" in text:
        return text, 0
    if text.count(ANCHOR) != 1:
        raise SystemExit("!! the S290 anchor is not unique in this file - nothing written")
    return text.replace(ANCHOR, ANCHOR + BLOCK), 1


def main():
    path = sys.argv[1]
    src = io.open(path, encoding="utf-8").read()
    out, done = apply(src)
    if done:
        io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("finance_app patched: %d edit(s)%s" % (done, "" if done else " - already in place"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
