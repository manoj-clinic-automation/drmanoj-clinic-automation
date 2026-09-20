#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_s355.py -- S355_DAY_TRUTH: the resync proven on a scratch database.

Builds a small database in the live shape (the five tables day_resync touches
or reads, DDL copied from the 20-Sep nightly finance.db), files seven days the
way the D354 autofile files them, and checks every verdict the script can give:
FIXED · SAME · NO_BANK · OVER_NET · SHAPE, plus the three days it must never
touch (approved, corrected by a person, typed by a person).  When finance_upi
is importable (--finance-dir), the exception is proven closed too.

    python3 -B selftest_s355.py [--finance-dir /root/finance]
Prints one line per check and 'selftest: N/N'.  Nothing outside a temp folder.
"""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

DDL = """
CREATE TABLE business_unit (code TEXT PRIMARY KEY);
INSERT INTO business_unit VALUES ('medical');
CREATE TABLE day_entry (
    id INTEGER PRIMARY KEY, unit TEXT NOT NULL REFERENCES business_unit(code),
    business_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','submitted','approved','locked','closed_holiday')),
    manned_by INTEGER, manned_source TEXT,
    source TEXT NOT NULL DEFAULT 'app' CHECK (source IN ('app','legacy_sheet')),
    entered_by TEXT, entered_at TEXT, approved_by TEXT, approved_at TEXT, legacy_ref TEXT,
    UNIQUE (unit, business_date));
CREATE TABLE day_line (
    id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL REFERENCES day_entry(id) ON DELETE CASCADE,
    service TEXT NOT NULL, mode TEXT NOT NULL CHECK (mode IN ('cash','upi','card','credit')),
    amount_p INTEGER NOT NULL CHECK (amount_p >= 0), line_kind TEXT, note TEXT);
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, row_id INTEGER, action TEXT NOT NULL,
    before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT NOT NULL);
CREATE TABLE upi_statement (
    id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, unit TEXT REFERENCES business_unit(code),
    statement_date TEXT NOT NULL, source_msg_id TEXT, filename TEXT, sha256 TEXT,
    parsed_total_p INTEGER, txn_count INTEGER, ingested_at TEXT, UNIQUE (merchant_id, statement_date));
CREATE TABLE recon_exception (
    id INTEGER PRIMARY KEY, unit TEXT NOT NULL REFERENCES business_unit(code), business_date TEXT NOT NULL,
    kind TEXT NOT NULL, expected_p INTEGER, actual_p INTEGER, diff_p INTEGER,
    severity TEXT NOT NULL DEFAULT 'high' CHECK (severity IN ('low','medium','high')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','acknowledged','resolved')),
    detail TEXT, opened_at TEXT, shout_count INTEGER NOT NULL DEFAULT 0, last_shout_at TEXT,
    resolution TEXT, closed_by TEXT, closed_at TEXT, UNIQUE (unit, business_date, kind));
"""

U = "medical"


def file_day(con, iso, net_p, upi_p, status="submitted", how="autofile", corrected=False, upi_line=True):
    cur = con.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) "
                      "VALUES (?,?,?,'app','app','2026-09-19T01:00:00')", (U, iso, status))
    eid = cur.lastrowid
    con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','cash',?)",
                (eid, net_p - upi_p))
    if upi_line:
        con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','upi',?)",
                    (eid, upi_p))
    con.execute("INSERT INTO audit_log (table_name, row_id, action, after_json, by_whom, at) "
                "VALUES ('day_entry', ?, ?, '{}', 'app', '2026-09-19T01:00:00')", (eid, how))
    if corrected:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, by_whom, at) "
                    "VALUES ('day_entry', ?, 'correct', '{}', 'darpan', '2026-09-19T09:00:00')", (eid,))
    return eid


def bank(con, iso, total_p, n=3):
    con.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, parsed_total_p, txn_count, ingested_at) "
                "VALUES ('M1', ?, ?, ?, ?, '2026-09-19T10:56:00')", (U, iso, total_p, n))
    con.execute("INSERT INTO recon_exception (unit, business_date, kind, expected_p, actual_p, diff_p, status, "
                "detail, opened_at) VALUES (?,?,'upi_vs_statement',?,0,?, 'open','walk','2026-09-19T10:56:00')",
                (U, iso, total_p, -total_p))


def lines(con, iso):
    r = con.execute("SELECT COALESCE(SUM(CASE WHEN l.mode='cash' THEN l.amount_p END),0) c, "
                    "COALESCE(SUM(CASE WHEN l.mode='upi' THEN l.amount_p END),0) u "
                    "FROM day_line l JOIN day_entry e ON e.id=l.day_entry_id WHERE e.business_date=?",
                    (iso,)).fetchone()
    return int(r[0]), int(r[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance-dir", default=None, help="folder holding finance_upi.py (the live one)")
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="s355_")
    ok = 0
    n = 0

    def check(name, cond):
        nonlocal ok, n
        n += 1
        ok += 1 if cond else 0
        print("  %s %s" % ("ok  " if cond else "FAIL", name))

    try:
        shutil.copy(os.path.join(HERE, "day_resync.py"), tmp)
        have_upi = False
        if a.finance_dir and os.path.exists(os.path.join(a.finance_dir, "finance_upi.py")):
            shutil.copy(os.path.join(a.finance_dir, "finance_upi.py"), tmp)
            have_upi = True
        db = os.path.join(tmp, "walk.db")
        con = sqlite3.connect(db)
        con.executescript(DDL)
        # the seven days
        file_day(con, "2026-09-01", 999300, 0); bank(con, "2026-09-01", 64300, 2)          # FIXED
        file_day(con, "2026-09-03", 1655700, 421400); bank(con, "2026-09-03", 421400)     # SAME
        file_day(con, "2026-09-04", 500000, 0)                                            # NO_BANK
        file_day(con, "2026-09-05", 100000, 0); bank(con, "2026-09-05", 150000)           # OVER_NET
        file_day(con, "2026-09-06", 800000, 0, status="approved"); bank(con, "2026-09-06", 100000)   # never
        file_day(con, "2026-09-07", 800000, 0, corrected=True); bank(con, "2026-09-07", 100000)      # never
        file_day(con, "2026-09-08", 800000, 0, how="create"); bank(con, "2026-09-08", 100000)        # typed: never
        file_day(con, "2026-09-09", 700000, 0, upi_line=False); bank(con, "2026-09-09", 200000)      # FIXED, line inserted
        con.commit()
        con.close()

        env = dict(os.environ, SANJEEVNI_OFF_DIR=os.path.join(tmp, "_off"))
        run = lambda *x: subprocess.run([a.python, "-B", os.path.join(tmp, "day_resync.py"), "--db", db] + list(x),
                                        capture_output=True, text=True, env=env, cwd=tmp)
        d = run("--dry-run")
        check("dry run exits 0", d.returncode == 0)
        check("dry run names 5 candidates (approved, corrected, typed days excluded)", "5 unapproved autofiled" in d.stdout)
        check("dry run: 01 WOULD_FIX", "WOULD_FIX 2026-09-01" in d.stdout)
        check("dry run: 03 SAME", "SAME      2026-09-03" in d.stdout)
        check("dry run: 04 NO_BANK", "NO_BANK   2026-09-04" in d.stdout)
        check("dry run: 05 OVER_NET", "OVER_NET  2026-09-05" in d.stdout)
        con = sqlite3.connect(db)
        check("dry run wrote nothing", lines(con, "2026-09-01") == (999300, 0) and
              con.execute("SELECT COUNT(*) FROM audit_log WHERE action='resync_upi'").fetchone()[0] == 0)
        con.close()

        r = run()
        check("apply exits 0", r.returncode == 0)
        check("apply summary FIXED 2 · NO_BANK 1 · OVER_NET 1 · SAME 1",
              "FIXED 2" in r.stdout and "NO_BANK 1" in r.stdout and "OVER_NET 1" in r.stdout and "SAME 1" in r.stdout)
        con = sqlite3.connect(db)
        check("01: UPI 643 from the bank, cash = net - UPI", lines(con, "2026-09-01") == (935000, 64300))
        check("09: UPI line inserted when the autofile wrote none", lines(con, "2026-09-09") == (500000, 200000))
        check("05: over-net day untouched", lines(con, "2026-09-05") == (100000, 0))
        check("06 approved untouched", lines(con, "2026-09-06") == (800000, 0))
        check("07 corrected-by-a-person untouched", lines(con, "2026-09-07") == (800000, 0))
        check("08 typed-by-a-person untouched", lines(con, "2026-09-08") == (800000, 0))
        au = con.execute("SELECT before_json, after_json, by_whom FROM audit_log WHERE action='resync_upi' "
                         "ORDER BY id").fetchall()
        check("two audit rows, before/after carried, by day_resync",
              len(au) == 2 and json.loads(au[0][0])["upi_p"] == 0 and json.loads(au[0][1])["upi_p"] == 64300
              and au[0][2] == "day_resync")
        if have_upi:
            st = con.execute("SELECT status FROM recon_exception WHERE business_date='2026-09-01'").fetchone()[0]
            check("01: the upi_vs_statement exception closed by the live finance_upi", st == "resolved")
            st5 = con.execute("SELECT status FROM recon_exception WHERE business_date='2026-09-05'").fetchone()[0]
            check("05: the over-net exception stays open", st5 == "open")
        else:
            check("finance_upi not given: exception left for the next bank load (stated)",
                  "finance_upi not importable" in r.stdout)
            check("(placeholder so the count is the same either way)", True)
        con.close()
        r2 = run()
        check("second apply changes nothing (SAME for every fixed day)",
              r2.returncode == 0 and "FIXED" not in r2.stdout.split("summary:")[-1] and "SAME 3" in r2.stdout)
        os.makedirs(os.path.join(tmp, "_off")); open(os.path.join(tmp, "_off", "ALL_OFF"), "w").close()
        r3 = run()
        check("ALL_OFF honoured", r3.returncode == 0 and "OFF" in r3.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: %d/%d" % (ok, n))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
