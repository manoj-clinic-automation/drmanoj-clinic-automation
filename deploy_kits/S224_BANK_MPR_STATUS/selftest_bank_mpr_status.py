#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_bank_mpr_status.py -- S224: every state of bank_mpr_status on a THROWAWAY sqlite db.

Seeds: an APPLIED day (ingested before the expected time), a LATE day (ingested at 22:54, the
real 31-Aug shape), a REJECTED day (data_flag UPI_STATEMENT_REJECTED naming the mail-day file),
a NO-ROWS day (raw file in a temp store, no upi_statement row), a WAITING day (now is before
12:20 on D+1) and a NOT-RECEIVED day (now is after).  Then the two routes through a bare Flask
app with a stub require.  The real gate is the walk's job, not this file's.

    python3 -B selftest_bank_mpr_status.py          (from the kit folder)
"""
import datetime as dt
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bank_mpr_status as M                                  # noqa: E402

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))


TMP = tempfile.mkdtemp(prefix="mpr_selftest_")
DB = os.path.join(TMP, "f.db")
STORE = os.path.join(TMP, "upi_statements")
os.makedirs(STORE)
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
con.executescript("""
CREATE TABLE upi_statement (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, unit TEXT,
  statement_date TEXT NOT NULL, source_msg_id TEXT, filename TEXT, sha256 TEXT,
  parsed_total_p INTEGER, txn_count INTEGER, ingested_at TEXT, UNIQUE (merchant_id, statement_date));
CREATE TABLE data_flag (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, day_entry_id INTEGER,
  code TEXT NOT NULL, severity TEXT NOT NULL DEFAULT 'info', detail TEXT);
""")
MID = "999999999999999"                                      # synthetic; no real merchant id here
con.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, "
            "txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
            (MID, "clinic", "2026-09-01", MID + "_02092026_ICICI_POS_CD.xlsx", 1234500, 17,
             "2026-09-02T12:03:11"))
con.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, "
            "txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
            (MID, "clinic", "2026-08-31", MID + "_01092026_ICICI_POS_CD.xlsx", 560000, 6,
             "2026-09-01T22:54:02"))
con.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) VALUES (NULL, NULL, "
            "'UPI_STATEMENT_REJECTED', 'high', ?)",
            (MID + "_30082026_ICICI_POS_CD.xlsx: sum of rows 100.00 != Grand Total 200.00",))
open(os.path.join(STORE, "abcdef0123_" + MID + "_28082026_ICICI_POS_CD.xlsx"), "wb").write(b"x")
con.commit()

M._upi_dir = STORE
M._unit = "clinic"

# --- states ------------------------------------------------------------------------------
r = M.mpr_state(con, "2026-09-01", now=dt.datetime(2026, 9, 4, 10, 45))
ck("applied: state", r["state"] == "applied", r["state"])
ck("applied: line names time, rows, rupees", "APPLIED at 02-Sep 12:03 IST" in r["line"]
   and "17 rows" in r["line"] and "₹12,345" in r["line"], r["line"])

r = M.mpr_state(con, "2026-08-31", now=dt.datetime(2026, 9, 4, 10, 45))
ck("late: state", r["state"] == "late", r["state"])
ck("late: line says LATE with the time and the expectation", "LATE" in r["line"]
   and "01-Sep 22:54" in r["line"] and "12:20" in r["line"] and "₹5,600" in r["line"], r["line"])

r = M.mpr_state(con, "2026-08-29", now=dt.datetime(2026, 9, 4, 10, 45))
ck("rejected: state", r["state"] == "rejected", r["state"])
ck("rejected: RECEIVED, NOT APPLIED with the parser's reason",
   "RECEIVED, NOT APPLIED" in r["line"] and "Grand Total" in r["line"], r["line"])

r = M.mpr_state(con, "2026-08-27", now=dt.datetime(2026, 9, 4, 10, 45))
ck("no_rows: state (raw file for the mail day, no row)", r["state"] == "no_rows", r["state"])
ck("no_rows: line says RECEIVED and NO UPI", "RECEIVED at" in r["line"] and "NO Clinic UPI" in r["line"], r["line"])

# 03-Sep at 10:45 on 04-Sep: the owner's exact moment
r = M.mpr_state(con, "2026-09-03", now=dt.datetime(2026, 9, 4, 10, 45))
ck("waiting: 03-Sep seen at 04-Sep 10:45", r["state"] == "waiting", r["state"])
ck("waiting: line names the mail time and the expected-by",
   "WAITING" in r["line"] and "11:15" in r["line"] and "12:20" in r["line"] and "04-Sep" in r["line"], r["line"])
ck("waiting: expected_by is 12:20 on D+1", r["expected_by"] == "2026-09-04T12:20:00", r["expected_by"])

r = M.mpr_state(con, "2026-09-03", now=dt.datetime(2026, 9, 4, 13, 0))
ck("not_received: 03-Sep seen at 04-Sep 13:00 (before the shout)", r["state"] == "not_received"
   and "NOT RECEIVED" in r["line"] and "still missing at 15:00" in r["line"], r["line"])
r = M.mpr_state(con, "2026-09-03", now=dt.datetime(2026, 9, 4, 16, 0))
ck("not_received: after the 15:00 shout, the line says the shout should have come",
   r["state"] == "not_received" and "should have mailed" in r["line"], r["line"])

r = M.mpr_state(con, "2026-13-40", now=dt.datetime(2026, 9, 4))
ck("bad date refused", r["state"] == "bad_date" and not r["ok"])
r = M.mpr_state(con, "2026-09-01", unit="medical", now=dt.datetime(2026, 9, 4, 10, 45))
ck("other unit is independent (medical 01-Sep: nothing seeded -> not_received)", r["state"] == "not_received")

# no upi_statement table at all -> never a 500
con2 = sqlite3.connect(":memory:")
con2.row_factory = sqlite3.Row
r = M.mpr_state(con2, "2026-09-03", now=dt.datetime(2026, 9, 4, 10, 45))
ck("missing tables: still answers (waiting), never raises", r["state"] == "waiting" and "store_error" in r)

frag = M.fragment(M.mpr_state(con, "2026-09-01", now=dt.datetime(2026, 9, 4, 10, 45)))
ck("fragment has no <script> and carries data-state", "<script" not in frag and 'data-state="applied"' in frag)
_f = M.fragment(dict(state="waiting", line="a<b"))
ck("fragment escapes html", "a&lt;b" in _f and "a<b" not in _f)

# --- routes through a bare app with a stub require -------------------------------------------
from flask import Flask                                      # noqa: E402
app = Flask("t")
GRANT = {"ok": True}


def _db():
    return con


def _require(*roles, unit=None):
    if GRANT["ok"]:
        return {"user": "t"}, None
    from flask import jsonify                                # noqa: PLC0415
    return None, (jsonify(ok=False, error="not_permitted"), 403)


M.init(app, _db, _require, unit="clinic", upi_dir=STORE)
c = app.test_client()
rv = c.get("/finance/clinic/bank/mpr/2026-09-01")
ck("GET /finance/clinic/bank/mpr/<date> -> 200 html fragment", rv.status_code == 200
   and b"APPLIED" in rv.data and rv.headers["Content-Type"].startswith("text/html"))
rv = c.get("/finance/clinic/bank/mpr/2026-09-01.json")
ck("GET .json -> json with state", rv.status_code == 200 and rv.get_json()["state"] == "applied")
rv = c.get("/finance/clinic/bank/mpr/2026-09-01?json=1")
ck("?json=1 -> json", rv.is_json and rv.get_json()["rows"] == 17)
rv = c.get("/finance/clinic/bank/mpr/2026-09-01?unit=medical&json=1")
ck("?unit=medical honoured", rv.get_json()["unit"] == "medical")
rv = c.get("/finance/clinic/bank/mpr/nonsense")
ck("bad date -> 400", rv.status_code == 400)
rv = c.get("/finance/clinic/bank/mpr?days=3")
ck("GET /finance/clinic/bank/mpr -> 200 page with 3 lines", rv.status_code == 200 and rv.data.count(b'class="mpr-status"') == 3)
GRANT["ok"] = False
ck("no role -> 403 from require", c.get("/finance/clinic/bank/mpr/2026-09-01").status_code == 403
   and c.get("/finance/clinic/bank/mpr").status_code == 403)
GRANT["ok"] = True

con.close()
shutil.rmtree(TMP, ignore_errors=True)
print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
if FAILED:
    print("FAILED: " + "; ".join(FAILED))
sys.exit(1 if FAILED else 0)
