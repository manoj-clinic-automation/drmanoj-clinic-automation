#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_cheque_writer_s284.py -- S284 / D524: Shavez may WRITE the cheque register.

THE RULING (board line F5, 15-Sep): "make him maker". THE SCOPE (the S262 note, the
Book §1.2): "Shavez as maker on the cheque register" -- the register, not the medical
unit. A unit_role row 'maker' would also let him file the day, give verdicts on
purchase bills, type carry-forwards on the payment sheet and read the vendor phone
book as of right. So the grant is the house pattern already used twice in this file
(`purchase.phonebook_users`, `purchase.salt_users`): a NAMED list in the `setting`
table, `purchase.cheque_users`, read fail-closed. A maker or checker writes as
before; a viewer writes only if named there. Everything else he sees stays read-only.

FOUR anchored edits and one block appended. Nothing else is touched:

  A  /api/cheque       -- any medical login may reach it; a non-writer is refused
  B  /api/cheque-mark  -- the same
  C  /page/cheques     -- the register's forms show for a writer
  D  the payment sheet's cheque card -- the log-a-cheque form shows for a writer
  E  CHEQUE_USERS_KEY and _cheque_writer_s284() appended at the end of the file

    python3 -B patch_cheque_writer_s284.py --file /root/finance/purchase_app.py --from <md5>
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

MARK = "_cheque_writer_s284"

EDITS = [
    # A -- log one cheque
    ('''    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    vendor_norm = str(b.get("vendor_norm") or "").strip()''',
     '''    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _cheque_writer_s284(u, _db()):
        return _refuse("Only a cheque writer may log a cheque.")
    b = request.get_json(silent=True) or {}
    month = str(b.get("month") or "")
    vendor_norm = str(b.get("vendor_norm") or "").strip()'''),
    # B -- handed over / voided
    ('''    u, err = _person("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    cid = _int_or_none(b.get("id"))''',
     '''    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _cheque_writer_s284(u, _db()):
        return _refuse("Only a cheque writer may mark a cheque.")
    b = request.get_json(silent=True) or {}
    cid = _int_or_none(b.get("id"))'''),
    # C -- the register page
    ('''    editable = not _is_viewer_only(u)

    months = _cheque_months_s271(con)''',
     '''    editable = _cheque_writer_s284(u, con)

    months = _cheque_months_s271(con)'''),
    # D -- the cheque card on the payment sheet
    ('''_cheque_card_s270(con, month, prefix, groups, not _is_viewer_only(u)),''',
     '''_cheque_card_s270(con, month, prefix, groups, _cheque_writer_s284(u, con)),'''),
]

APPEND = '''

CHEQUE_USERS_KEY = "purchase.cheque_users"


def _cheque_writer_s284(u, con):
    """D524: who may WRITE the cheque register -- log a cheque, mark it handed over,
    void it. A maker or checker of the medical unit, exactly as before. Otherwise
    ONLY a login named in setting purchase.cheque_users (Shavez, by the owner's word
    of 15-Sep). Fail-closed: a missing or unreadable setting admits no viewer. This
    grants nothing else -- the sheet's carry-forward, the verification, the lock and
    the phone book keep their own gates."""
    if not _is_viewer_only(u):
        return True
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (CHEQUE_USERS_KEY,)).fetchone()
    except Exception:
        return False
    raw = (r[0] if r else "") or ""
    names = set(p.strip().lower() for p in re.split(r"[,;\\s]+", str(raw)) if p.strip())
    who = str(_who(u) or "").strip().lower()
    return bool(who) and who in names
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(a.file):
        sys.exit("REFUSING: %s not found" % a.file)
    raw = io.open(a.file, "rb").read()
    cur = md5(raw)
    src = raw.decode("utf-8")

    if MARK in src:
        print("ALREADY PATCHED (%s present); pin %s -- nothing to do" % (MARK, cur))
        return 0
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))
    for need in ("_cheque_card_s270", "_cheque_months_s271", "def _is_viewer_only(u):", "def _who(u):"):
        if need not in src:
            sys.exit("REFUSING: %s is not in this file. S284 has nothing to patch." % need)
    for i, (old, _new) in enumerate(EDITS):
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %s matched %d times, expected exactly 1.\n"
                     "          Nothing was written. The file is at %s." % ("ABCD"[i], n, cur))

    out = src
    for old, new in EDITS:
        out = out.replace(old, new)
    out = out.rstrip("\n") + "\n" + APPEND
    new = out.encode("utf-8")
    if a.check:
        print("would write %s -> %s  (+%d bytes)" % (cur, md5(new), len(new) - len(raw)))
        return 0
    bak = "%s.bak_S284_%s" % (a.file, cur[:8])
    if not os.path.exists(bak):
        shutil.copy2(a.file, bak)
    io.open(a.file, "wb").write(new)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s   <-- READ BACK FROM DISK. This is the pin." % back)
    print("   backup %s" % bak)
    return 0 if back == md5(new) else 4


if __name__ == "__main__":
    sys.exit(main())
