#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_account_s263.py -- write ONE vendor's bank account into the database.

The account number is never in the repository and never in this file: it is
handed in on the command line, printed back MASKED (last 4 only), and written
straight to purchase_vendor_contact.

It will NEVER overwrite an account that is already there. If the vendor already
has a number, this says so and changes nothing -- replacing a live account is a
decision, not an install step.

    python3 seed_account_s263.py --db /root/finance/finance.db \
        --vendor "DAANSHI PHARMA" --acct <no> --ifsc <code> --by "owner"
"""
import argparse
import datetime as dt
import sqlite3
import sys


def mask(s):
    s = (s or "").strip()
    return ("*" * max(0, len(s) - 4)) + s[-4:] if s else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--vendor", required=True)
    ap.add_argument("--acct", required=True)
    ap.add_argument("--ifsc", required=True)
    ap.add_argument("--by", default="owner")
    a = ap.parse_args()
    vn = " ".join(a.vendor.split()).upper()
    acct = a.acct.strip()
    ifsc = a.ifsc.strip().upper()
    if not acct or not ifsc:
        sys.exit("REFUSING: an account number and an IFSC are both required")
    now = dt.datetime.now().isoformat(timespec="seconds")
    con = sqlite3.connect(a.db)
    cols = {r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")}
    need = {"vendor_norm", "vendor", "acct_no", "ifsc", "bank_status", "updated_at"}
    missing = need - cols
    if missing:
        sys.exit("REFUSING: purchase_vendor_contact has no %s" % ", ".join(sorted(missing)))
    row = con.execute("SELECT COALESCE(acct_no,'') FROM purchase_vendor_contact "
                      "WHERE vendor_norm=?", (vn,)).fetchone()
    if row is not None and (row[0] or "").strip():
        if (row[0] or "").strip() == acct:
            print("   %s already carries this account (%s) -- nothing to do" % (vn, mask(acct)))
        else:
            print("   %s ALREADY HAS A DIFFERENT ACCOUNT (%s) -- left untouched, "
                  "change it on the Book page" % (vn, mask(row[0])))
        return
    extra = {}
    for c, v in (("acct_name", a.vendor), ("bank_verified_by", a.by),
                 ("bank_verified_at", now), ("source", "owner")):
        if c in cols:
            extra[c] = v
    keys = ["vendor_norm", "vendor", "acct_no", "ifsc", "bank_status", "updated_at"] + list(extra)
    vals = [vn, a.vendor.strip(), acct, ifsc, "VERIFIED", now] + [extra[k] for k in extra]
    if row is None:
        con.execute("INSERT INTO purchase_vendor_contact (%s) VALUES (%s)"
                    % (", ".join(keys), ", ".join("?" * len(keys))), vals)
        what = "added"
    else:
        sets = [k for k in keys if k != "vendor_norm"]
        con.execute("UPDATE purchase_vendor_contact SET %s WHERE vendor_norm=?"
                    % ", ".join("%s=?" % k for k in sets),
                    [vals[keys.index(k)] for k in sets] + [vn])
        what = "filled in"
    con.commit()
    print("   %s %s, VERIFIED, account %s, IFSC %s" % (vn, what, mask(acct), ifsc))


if __name__ == "__main__":
    main()
