#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline proof for import_neft_bank.py, against a synthetic DB and CSV -- no real data, and no
digit-string stands in for a phone or account number here (F-185: no number at all, unmasked)."""
import csv, os, sqlite3, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "import_neft_bank.py")
sys.path.insert(0, HERE)
from import_neft_bank import supplier_key  # noqa: E402 -- exact same key as the script under test

PHONE_A, PHONE_B, PHONE_C = "PHONE-STUB-A", "PHONE-STUB-B", "PHONE-STUB-C"
ACCT_A, ACCT_B_OLD, ACCT_B_NEW, ACCT_C = "ACCTSTUBAQ", "WRONGSTUB", "ACCTSTUBBR", "ACCTSTUBCS"
ACCT_D = "ACCTSTUBDT"
IFSC_WRONG, IFSC_B, IFSC_C = "WRONGSTUB0", "SBINSTUBE1", "ABCDSTUBF2"


def make_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE purchase_vendor_contact (vendor_norm TEXT PRIMARY KEY, vendor TEXT NOT NULL, "
                "phone TEXT, phone2 TEXT, acct_name TEXT, acct_no TEXT, ifsc TEXT, bank_branch TEXT, upi_id TEXT, "
                "bank_status TEXT, bank_verified_by TEXT, bank_verified_at TEXT, source TEXT, added_by TEXT, "
                "updated_at TEXT NOT NULL)")
    con.execute("CREATE TABLE purchase_audit (id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT NOT NULL, "
                "action TEXT NOT NULL, ref TEXT, detail TEXT)")
    # A: already in the book, no bank yet -> should be written VERIFIED
    con.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, updated_at) VALUES (?,?,?,?)",
                (supplier_key("A.A. Pharmaceuticals"), "A.A. Pharmaceuticals", PHONE_A, "2026-01-01T00:00:00"))
    # B: in the book, source CSV names it with a BAREILLY city tail, existing bank details WRONG -> should update
    con.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, acct_no, ifsc, bank_status, "
                "updated_at) VALUES (?,?,?,?,?,?,?)",
                (supplier_key("Surya Surgicals"), "Surya Surgicals", PHONE_B, ACCT_B_OLD, IFSC_WRONG, "", "2026-01-01T00:00:00"))
    # C: already correct and VERIFIED -> should be reported unchanged, not rewritten
    con.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, acct_no, ifsc, bank_status, "
                "bank_verified_by, bank_verified_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (supplier_key("Correct Already"), "Correct Already", PHONE_C, ACCT_C, IFSC_C,
                 "VERIFIED", "someone", "2026-01-01T00:00:00", "2026-01-01T00:00:00"))
    con.commit()
    con.close()


def make_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("vendor", "acct_no", "ifsc", "status", "note"))
        w.writerow(("A.A. Pharmaceuticals", ACCT_A, "KARBSTUBG3", "VERIFIED", ""))
        w.writerow(("Surya Surgicals Bareilly", ACCT_B_NEW, IFSC_B, "VERIFIED", ""))
        w.writerow(("Correct Already", ACCT_C, IFSC_C, "VERIFIED", ""))
        w.writerow(("Nobody Yet Pharma", ACCT_D, "HDFCSTUBH4", "UNVERIFIED", "NOT PAID THIS FY"))


def run(args):
    return subprocess.run([sys.executable, "-B", SCRIPT] + args, capture_output=True, text=True)


def main():
    tmp = tempfile.mkdtemp(prefix="neft_selftest_")
    db, csvp = os.path.join(tmp, "test.db"), os.path.join(tmp, "test.csv")
    make_db(db)
    make_csv(csvp)

    ok = True

    # dry run: must not change the db
    before = open(db, "rb").read()
    r = run(["--csv", csvp, "--db", db])
    if open(db, "rb").read() != before:
        print("FAIL: dry run modified the database"); ok = False
    if "matched (will change): 2" not in r.stdout:
        print("FAIL: expected 2 to change in dry run\n" + r.stdout); ok = False
    if "already correct, no change: 1" not in r.stdout:
        print("FAIL: expected 1 unchanged\n" + r.stdout); ok = False
    if "not in the phone book yet -- NOT written, needs a phone number first: 1" not in r.stdout:
        print("FAIL: expected 1 unmatched\n" + r.stdout); ok = False

    # apply
    r = run(["--csv", csvp, "--db", db, "--apply"])
    if "wrote 2 vendor(s)" not in r.stdout:
        print("FAIL: expected apply to write 2\n" + r.stdout); ok = False
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    a = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (supplier_key("A.A. Pharmaceuticals"),)).fetchone()
    if not (a["acct_no"] == ACCT_A and a["bank_status"] == "VERIFIED" and a["bank_verified_by"]):
        print("FAIL: row A not written correctly: %s" % dict(a)); ok = False
    b = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (supplier_key("Surya Surgicals"),)).fetchone()
    if not (b["acct_no"] == ACCT_B_NEW and b["ifsc"] == IFSC_B and b["bank_status"] == "VERIFIED"):
        print("FAIL: row B (city-tail match) not updated: %s" % dict(b)); ok = False
    c = con.execute("SELECT * FROM purchase_vendor_contact WHERE vendor_norm=?", (supplier_key("Correct Already"),)).fetchone()
    if c["bank_verified_by"] != "someone":
        print("FAIL: row C was rewritten though it was already correct: %s" % dict(c)); ok = False
    n = con.execute("SELECT COUNT(*) c FROM purchase_vendor_contact WHERE vendor LIKE '%Nobody%'").fetchone()
    if n["c"] != 0:
        print("FAIL: unmatched vendor D was inserted -- must never happen"); ok = False
    aud = con.execute("SELECT COUNT(*) c FROM purchase_audit").fetchone()
    if aud["c"] != 2:
        print("FAIL: expected 2 audit rows, got %d" % aud["c"]); ok = False
    bak_files = [f for f in os.listdir(tmp) if f.startswith("test.db.bak_s225_neft_")]
    if len(bak_files) != 1:
        print("FAIL: expected exactly 1 backup file, found %d" % len(bak_files)); ok = False
    con.close()

    # re-run (idempotency): second apply should report 0 to change
    r = run(["--csv", csvp, "--db", db, "--apply"])
    if "nothing to write" not in r.stdout:
        print("FAIL: second apply was not a no-op\n" + r.stdout); ok = False

    print("PASS -- all checks ok" if ok else "SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
