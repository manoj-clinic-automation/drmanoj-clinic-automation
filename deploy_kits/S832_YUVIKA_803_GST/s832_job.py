#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s832_job.py -- S832_YUVIKA_803_GST (14-Nov-2026, Sanjeevni session 459; the owner's 'Ok' of 18:05 IST): puts ONE tap job on Amir's card
(amir_job, kind 'tap'): Yuvika Surgicals' bill 803 of 06-11-2026 -- Marg holds XL 1 + XXL 2 (the revised paper, scan B-0272, Rs 1,410) but
its XXL line carries no GST, so Marg's total is Rs 1,364. The paper charges 5% on both lines. Data only; idempotent (the key is unique).
    python3 -B s832_job.py <finance.db> [--dry]"""
import datetime as dt
import sqlite3
import sys

KEY = "fix:S832:YUVIKA 803"
SUBJ = "YUVIKA SURGICALS"
TEXT = "YUVIKA SURGICALS bill 803 (06-11) — XXL line par GST 5% lagaiye; bill ₹1,410 hona chahiye (abhi Marg mein ₹1,364)"
SUB = "Naya bill (scan B-0272): XL 1 + XXL 2, dono par 5% GST. Theek karke 'Kar diya' dabaiye."


def main(db, dry):
    con = sqlite3.connect(db, timeout=30)
    try:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='amir_job'").fetchone():
            print("S832: amir_job is not on this server -- nothing written")
            return 2
        if con.execute("SELECT 1 FROM amir_job WHERE key=?", (KEY,)).fetchone():
            print("S832: ALREADY ON HIS CARD (%s) -- nothing written" % KEY)
            return 0
        if dry:
            print("S832: DRY -- would add one tap job: %s" % TEXT)
            return 0
        now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S")
        with con:
            con.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                        (KEY, "tap", SUBJ, TEXT, SUB, now, "S832 (the owner's word, 14-Nov 18:05)", now))
        r = con.execute("SELECT id, kind, show_from FROM amir_job WHERE key=?", (KEY,)).fetchone()
        print("S832: added job %d (%s, shown from %s): %s" % (r[0], r[1], r[2], TEXT))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--dry" in sys.argv[2:]) if len(sys.argv) > 1 else 2)
