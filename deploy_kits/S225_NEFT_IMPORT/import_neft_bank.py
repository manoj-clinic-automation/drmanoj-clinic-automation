#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_neft_bank.py -- S225, owner's ruling of 04-Sep-2026 (S225_OWNER_RULINGS §5):
"all existing bank details already accepted as decided; it's for the future part."

Runs ON THE VPS. Reads a plain CSV (vendor, acct_no, ifsc, status, note) produced by
export_neft_csv.py on manojz, and writes into purchase_vendor_contact -- ONLY for
vendors that already exist in the phone book (a bank-only row with no phone is never
created here; that is a separate decision). Matches by the exact same supplier_key()
used everywhere else in purchase_app.py.

Rows whose source status is VERIFIED are written with bank_status='VERIFIED' directly --
this is the one deliberate, logged exception to D370 (a machine write normally drops to
UNVERIFIED); it exists because the owner's ruling above already IS the verification, made
in writing, dated. bank_verified_by records that ruling, not a person clicking Verify.
Rows whose source status is UNVERIFIED go in as UNVERIFIED, unchanged, flagged separately --
never auto-approved.

No account numbers are ever printed -- only last-4. The CSV is real financial data and must
never be committed to git; it lives beside this script only for the run and should be deleted
(--delete-source does that) once the import is confirmed.

Usage (both from the deploy_kits/S225_NEFT_IMPORT folder on the VPS):
    python3 -B import_neft_bank.py --csv /root/finance/_import/neft_bank_export_S225.csv
        (dry run: reports every match/mismatch, writes nothing -- the default)
    python3 -B import_neft_bank.py --csv /root/finance/_import/neft_bank_export_S225.csv --apply --delete-source
        (writes, after taking a timestamped backup of finance.db; deletes the CSV on success)
"""
import argparse
import csv
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys

DEF_DB = "/root/finance/finance.db"
_CITY_TAILS = ("BAREILLY", "BAREILL", "BAREIL", "BAREI", "BARE", "BAR", "BA")
BOOK_COLS = (("phone2", "TEXT"), ("acct_name", "TEXT"), ("acct_no", "TEXT"), ("ifsc", "TEXT"),
             ("bank_branch", "TEXT"), ("upi_id", "TEXT"), ("bank_status", "TEXT"),
             ("bank_verified_by", "TEXT"), ("bank_verified_at", "TEXT"), ("source", "TEXT"),
             ("added_by", "TEXT"))
BANK_FIELDS = ("acct_name", "acct_no", "ifsc", "bank_branch", "upi_id")


def norm(s):
    s = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", s)


def supplier_key(s):
    parts = norm(s).split(" ")
    while len(parts) > 1 and parts[-1] in _CITY_TAILS:
        parts.pop()
    return " ".join(parts)


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def last4(s):
    s = re.sub(r"\D", "", s or "")
    return ("*" * max(0, len(s) - 4)) + s[-4:] if s else ""


def ensure_book(con):
    have = {r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")}
    for col, typ in BOOK_COLS:
        if col not in have:
            con.execute("ALTER TABLE purchase_vendor_contact ADD COLUMN %s %s" % (col, typ))
    con.commit()


def read_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            v = (r.get("vendor") or "").strip()
            if not v:
                continue
            rows.append(dict(vendor=v, acct_no=(r.get("acct_no") or "").strip(),
                              ifsc=(r.get("ifsc") or "").strip().upper(),
                              status=(r.get("status") or "").strip().upper(),
                              note=(r.get("note") or "").strip()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--db", default=DEF_DB)
    ap.add_argument("--apply", action="store_true", help="write changes (default is dry-run)")
    ap.add_argument("--delete-source", action="store_true", help="delete the CSV after a successful --apply")
    a = ap.parse_args()

    if not os.path.exists(a.csv):
        print("import_neft_bank: CSV not found: %s" % a.csv)
        return 2
    if not os.path.exists(a.db):
        print("import_neft_bank: database not found: %s" % a.db)
        return 2

    rows = read_csv(a.csv)
    print("import_neft_bank: %d row(s) in CSV (%d VERIFIED, %d UNVERIFIED)" %
          (len(rows), sum(1 for r in rows if r["status"] == "VERIFIED"),
           sum(1 for r in rows if r["status"] == "UNVERIFIED")))

    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    ensure_book(con)

    matched, unmatched, unchanged = [], [], []
    for r in rows:
        key = supplier_key(r["vendor"])
        row = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (key,)).fetchone()
        if row is None:
            unmatched.append(r)
            continue
        new_status = r["status"] if r["status"] in ("VERIFIED", "UNVERIFIED") else (row["bank_status"] or "")
        same = ((row["acct_no"] or "") == r["acct_no"] and (row["ifsc"] or "") == r["ifsc"]
                and (row["bank_status"] or "") == new_status)
        if same:
            unchanged.append(r)
            continue
        matched.append((row, r, key, new_status))

    print("\nmatched (will change): %d" % len(matched))
    for row, r, key, new_status in matched:
        print("  %-35s acct ..%s  ifsc %s  -> %s%s" %
              (r["vendor"][:35], last4(r["acct_no"])[-4:], r["ifsc"], new_status,
               "  [%s]" % r["note"][:60] if r["note"] else ""))
    print("\nalready correct, no change: %d" % len(unchanged))
    for r in unchanged:
        print("  %-35s (already on file, unchanged)" % r["vendor"][:35])
    print("\nnot in the phone book yet -- NOT written, needs a phone number first: %d" % len(unmatched))
    for r in unmatched:
        print("  %-35s acct ..%s" % (r["vendor"][:35], last4(r["acct_no"])[-4:]))

    if not a.apply:
        print("\nimport_neft_bank: DRY RUN -- nothing written. Re-run with --apply to write.")
        con.close()
        return 0

    if not matched:
        print("\nimport_neft_bank: nothing to write.")
        con.close()
        return 0

    bak = a.db + ".bak_s225_neft_%s" % dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(a.db, bak)
    print("\nimport_neft_bank: backed up database -> %s" % bak)

    try:
        for row, r, key, new_status in matched:
            verified_by = "owner (NEFT import, S225 ruling 04-Sep-2026)" if new_status == "VERIFIED" else (row["bank_verified_by"] or "")
            verified_at = now_iso() if new_status == "VERIFIED" else (row["bank_verified_at"] or "")
            con.execute(
                "UPDATE purchase_vendor_contact SET acct_no=?, ifsc=?, bank_status=?, bank_verified_by=?, "
                "bank_verified_at=?, source='neft_import', updated_at=? WHERE vendor_norm=?",
                (r["acct_no"], r["ifsc"], new_status, verified_by, verified_at, now_iso(), key))
            con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                        (now_iso(), "neft_import_s225", "book_bank_neft_import", key,
                         '{"vendor": %r, "acct_last4": %r, "ifsc": %r, "bank_status": %r}' %
                         (r["vendor"], last4(r["acct_no"]), r["ifsc"], new_status)))
        con.commit()
    except Exception as e:  # noqa: BLE001
        con.rollback()
        print("\nimport_neft_bank: FAILED, rolled back, database untouched: %s" % e)
        con.close()
        return 1

    print("\nimport_neft_bank: wrote %d vendor(s). Verify on the live page:" % len(matched))
    print("  https://followup.dr-manoj.in/finance/purchase/page/book")
    con.close()

    if a.delete_source:
        os.remove(a.csv)
        print("import_neft_bank: source CSV deleted (%s)" % a.csv)
    else:
        print("import_neft_bank: source CSV left in place -- delete it once you've checked the page:")
        print("  %s" % a.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
