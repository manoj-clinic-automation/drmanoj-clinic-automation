#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_lengths_s225.py -- proves the import wrote FULL account numbers and IFSC codes, not
truncated ones, WITHOUT ever printing a number. Compares the character length of what is stored
in the database against length_manifest_S225.json (built from the source workbook -- lengths
only, no digits of any real number, safe by construction: F-185 does not apply to a length)."""
import os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from import_neft_bank import supplier_key  # noqa: E402

DEF_DB = "/root/finance/finance.db"


def read_manifest(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        vendor, a, i = line.rsplit("|", 2)
        out[vendor] = {"acct_len": int(a), "ifsc_len": int(i)}
    return out


def main():
    db = sys.argv[1] if len(sys.argv) > 1 else DEF_DB
    manifest = read_manifest(os.path.join(HERE, "length_manifest_S225.txt"))
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    ok = True
    checked = 0
    for vendor, want in manifest.items():
        key = supplier_key(vendor)
        row = con.execute("SELECT acct_no, ifsc FROM purchase_vendor_contact WHERE vendor_norm=?", (key,)).fetchone()
        if row is None:
            print("MISSING  %-35s -- no row in the database at all" % vendor[:35])
            ok = False
            continue
        got_a, got_i = len(row["acct_no"] or ""), len(row["ifsc"] or "")
        checked += 1
        if got_a != want["acct_len"] or got_i != want["ifsc_len"]:
            print("MISMATCH %-35s account chars %d (want %d), IFSC chars %d (want %d)" %
                  (vendor[:35], got_a, want["acct_len"], got_i, want["ifsc_len"]))
            ok = False
    con.close()
    print("\n%d of %d vendors checked, lengths match exactly (no truncation)." % (checked, len(manifest)) if ok
          else "\nMISMATCHES FOUND -- see above. Nothing printed is a real number, only counts.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
