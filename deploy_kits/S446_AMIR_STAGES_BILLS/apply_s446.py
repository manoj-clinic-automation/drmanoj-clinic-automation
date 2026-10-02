#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s446.py -- kit S446_AMIR_STAGES_BILLS: the data step, run AFTER the files are placed (and, in the walk, on a scratch copy).

  1. the settings (INSERT OR IGNORE -- a value already set is never moved): amir.vouchers_per_visit = 5;
     purchase.sarvam_trial_until = the install date + 2 months; purchase.scan_file_users = amir;
  2. the first Sarvam-against-Marg comparison of every linked scan (purchase_sarvam_check);
  3. the figures: Amir's card as he sees it, his board's count, the bills to put into Marg, the Sarvam comparison, the owner's lines
     from this kit -- counts, suppliers and bill numbers only.

    apply_s446.py --finance DIR --db PATH [--figures-only]
"""
import argparse
import datetime as dt
import os
import re
import sqlite3
import sys


def plus_months(d, n):
    y, m = d.year, d.month + n
    while m > 12:
        y, m = y + 1, m - 12
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(y, m, day)
        except ValueError:
            continue
    return dt.date(y, m, 28)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--figures-only", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    os.chdir(a.finance)
    os.environ.setdefault("FINANCE_DB", a.db)
    import amir_day                                                   # noqa: E402 -- the PLACED files (or the walk's copies)
    import purchase_app                                               # noqa: E402
    import stock_app                                                  # noqa: E402
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    if not a.figures_only:
        until = plus_months(dt.date.today(), 2).isoformat()
        rows = (("amir.vouchers_per_visit", "5", "S446 D649: medicine/consumable vouchers released to Amir per lot (Stage C)"),
                ("purchase.sarvam_trial_until", until, "S446 D650: Sarvam is compared with Marg, and Marg overrules, until this date"),
                ("purchase.scan_file_users", "amir", "S446 D650: logins (besides the medical checker) that may download the scanned bills"))
        n = 0
        for k, v, note in rows:
            n += con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note)).rowcount or 0
        con.commit()
        print("S446 settings: %d added (%s)" % (n, ", ".join("%s=%s" % (r[0], r[1]) for r in con.execute(
            "SELECT key, value FROM setting WHERE key IN ('amir.vouchers_per_visit','purchase.sarvam_trial_until','purchase.scan_file_users') ORDER BY key"))))
        print("S446 Sarvam comparison: %d linked scan(s) compared" % purchase_app.sarvam_compare(con))
    # ---- the figures
    w = amir_day._work(con, amir_day._today())
    card = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", amir_day._s446_card(w))).replace("&mdash;", "--").replace("&#10003;", "(ok)").strip()
    print("Amir's card: %s" % (card or "(nothing open -- no card)"))
    st = (w.get("s446") or {}).get("stage") or {}
    if st:
        A = st.get("A") or {}
        print("   count #%d: stage %s · Stage A %d/%d orthotic vouchers entered · his board lists %d (numbered 1..%d)"
              % (st["count_id"], st["stage"], A.get("entered", 0), A.get("total", 0), len(st.get("visible") or []), len(st.get("visible") or [])))
    bills = (w.get("s446") or {}).get("bills") or []
    print("Bills to put into Marg (step 2): %d · today's %d · oldest %s" % (len(bills), sum(1 for b in bills if b.get("today")),
                                                                       (bills[0]["stamp"] + " " + (bills[0]["created_at"] or "")[:10]) if bills else "-"))
    print("Packs in his card: %s" % (", ".join((w.get("s446") or {}).get("packs") or []) or "none"))
    con.execute(purchase_app.S446_SARVAM_DDL)
    for m in sorted({r[0] for r in con.execute("SELECT DISTINCT month FROM purchase_sarvam_check") if r[0]}):
        s = purchase_app.sarvam_summary(con, m)
        print("Sarvam vs Marg -- %s" % purchase_app._s446_sarvam_text(m, s))
    lines = amir_day._s446_owner_lines(con)
    print("Owner's lines from S446: %d" % len(lines))
    for l in lines:
        print("   - %s" % l["text"])
    con.close()
    print("S446 apply done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
