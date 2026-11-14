#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s829_job.py -- S829_SEPT_COUNT_KTROS (14-Nov-2026, Sanjeevni session 457; F-1232, the owner's word D976): puts ONE tap job on Amir's
card (amir_job, kind 'tap'): the 6-Sep count's lot-3 STOCK ISSUE of KT ROS DT (6:11) never reached Marg -- Marg's closing of 13-11 still
holds it. Data only; idempotent (the key is unique). VINBACTUM DS (the other line the proof names) is not added: the expiry write-off of
its 25 already on his card moves Marg the same way.
    python3 -B s829_job.py <finance.db> [--dry]"""
import datetime as dt
import sqlite3
import sys

KEY = "S829:ktros:sept-count-lot3"
TEXT = "KT ROS DT — STOCK ISSUE 6:11 (strip:tab) Marg mein daaliye"
SUB = "6 September ki ginti ka voucher (lot 3) — Marg mein abhi tak nahi aaya. Daal kar 'Kar diya' dabaiye."


def main(db, dry):
    con = sqlite3.connect(db, timeout=30)
    try:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='amir_job'").fetchone():
            print("S829: amir_job is not on this server -- nothing written")
            return 2
        if con.execute("SELECT 1 FROM amir_job WHERE key=?", (KEY,)).fetchone():
            print("S829: ALREADY ON HIS CARD (%s) -- nothing written" % KEY)
            return 0
        if dry:
            print("S829: DRY -- would add one tap job: %s" % TEXT)
            return 0
        now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S")
        with con:
            con.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                        (KEY, "tap", "KT ROS DT", TEXT, SUB, now, "S829 (the owner's word, D976)", now))
        r = con.execute("SELECT id, kind, show_from FROM amir_job WHERE key=?", (KEY,)).fetchone()
        print("S829: added job %d (%s, shown from %s): %s" % (r[0], r[1], r[2], TEXT))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--dry" in sys.argv[2:]) if len(sys.argv) > 1 else 2)
