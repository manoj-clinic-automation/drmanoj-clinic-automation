#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_s358.py -- S358_CASH_LOG: the doctors' cash log and the month table, on a scratch database.

Builds a scratch finance database in the live shape (tables and the three cash views copied from
the 20-Sep nightly finance.db, the kal schema from the kit's .sql), imports the kit's darpan_kal.py
with Flask stubbed, files four counter days the way the autofile does, and proves:
  the pending list (unlogged days with expected cash; a day typed by Darpan but not received),
  the owner logging one day at the expected amount (row created, landed as cash out of the drawer,
  received stamped, state complete), a different amount (the difference recorded), the backlog in one
  call, a recipient stamping Darpan's handover (and refused for the other doctor's day), a day already
  received refused, a future date refused, the month rows and the day rows adding up, and the
  grants edit producing v24 with Bhawna's tile.
    python3 -B selftest_s358.py [--python PY]
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
import types

HERE = os.path.dirname(os.path.abspath(__file__))
U = "medical"

TABLES = """
CREATE TABLE business_unit (code TEXT PRIMARY KEY); INSERT INTO business_unit VALUES ('medical');
CREATE TABLE staff_ref (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft', manned_by INTEGER, manned_source TEXT, source TEXT NOT NULL DEFAULT 'app',
  entered_by TEXT, entered_at TEXT, approved_by TEXT, approved_at TEXT, legacy_ref TEXT, UNIQUE (unit, business_date));
CREATE TABLE day_line (id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL, service TEXT NOT NULL, mode TEXT NOT NULL,
  amount_p INTEGER NOT NULL, line_kind TEXT, note TEXT);
CREATE TABLE day_noncash_bill (id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL, unit TEXT NOT NULL, bill_date TEXT NOT NULL,
  head TEXT NOT NULL, head_text TEXT, bill_no TEXT NOT NULL, amount_p INTEGER NOT NULL, patient_ref_id INTEGER,
  status TEXT NOT NULL DEFAULT 'open', settled_ref TEXT, settled_at TEXT, note TEXT, entered_by TEXT, entered_at TEXT, noncash_uid TEXT,
  UNIQUE (unit, bill_no, bill_date));
CREATE TABLE day_expense (id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL, amount_p INTEGER NOT NULL, amount_known INTEGER DEFAULT 1,
  category_fixed TEXT, category_kind TEXT, staff_id INTEGER, category_text TEXT, expense_uid TEXT);
CREATE TABLE cash_adjustment (id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL, amount_p INTEGER NOT NULL, reason TEXT NOT NULL,
  source TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', explanation TEXT, approved_by TEXT, approved_at TEXT);
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, row_id INTEGER, action TEXT NOT NULL,
  before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT NOT NULL);
CREATE TABLE upi_statement (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, unit TEXT, statement_date TEXT NOT NULL,
  source_msg_id TEXT, filename TEXT, sha256 TEXT, parsed_total_p INTEGER, txn_count INTEGER, ingested_at TEXT, UNIQUE (merchant_id, statement_date));
CREATE TABLE upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT, unit TEXT, txn_date TEXT, amount_p INTEGER, rrn TEXT, mode TEXT, txn_time TEXT, source_sha TEXT, ingested_at TEXT);
CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, unit TEXT, patient_ref_id INTEGER, service TEXT, description TEXT,
  amount_p INTEGER, mode TEXT, source TEXT, source_ref TEXT, confidence REAL, home_med INTEGER DEFAULT 0);
CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
INSERT INTO setting (key, value) VALUES ('darpan_kal.recipients', 'manoj:dr_manoj,bhawna:dr_bhawna');
"""


def load_views():
    """The three cash views + cash_movement, as the nightly finance.db defines them (views.sql beside this file)."""
    p = os.path.join(HERE, "views_s358.sql")
    return open(p, encoding="utf-8").read()


def file_day(con, iso, net_p, upi_p, status="submitted"):
    cur = con.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) "
                      "VALUES (?,?,?,'app','app','2026-09-19T01:00:00')", (U, iso, status))
    eid = cur.lastrowid
    con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','cash',?)", (eid, net_p - upi_p))
    con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','upi',?)", (eid, upi_p))
    con.execute("INSERT INTO sale_item (day_entry_id, unit, service, amount_p, mode, source_ref) VALUES (?,?,'pharmacy_sale',?,'cash',?)",
                (eid, U, net_p, "B" + iso[-2:]))
    con.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, parsed_total_p, txn_count) VALUES ('M1',?,?,?,1)", (U, iso, upi_p))
    if upi_p:
        con.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, mode, txn_time) VALUES ('M1',?,?,?,'UPI','10:00')", (U, iso, upi_p))
    return eid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="s358_")
    ok = n = 0

    def check(name, cond):
        nonlocal ok, n
        n += 1
        ok += 1 if cond else 0
        print("  %s %s" % ("ok  " if cond else "FAIL", name))

    try:
        for f in ("darpan_kal.py", "darpan_kal.html", "darpan_month.html", "darpan_kal_schema.sql"):
            shutil.copy(os.path.join(HERE, f), tmp)
        # Flask stubbed: the module's functions are exercised directly
        fl = types.ModuleType("flask")

        class BP:
            def __init__(self, *a, **k):
                pass

            def route(self, *a, **k):
                return lambda f: f
        fl.Blueprint = BP
        fl.jsonify = lambda **k: k
        fl.request = None
        fl.send_file = lambda p: p
        sys.modules["flask"] = fl
        sys.path.insert(0, tmp)
        import darpan_kal as k  # noqa: E402
        db = os.path.join(tmp, "walk.db")
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        con.executescript(TABLES)
        con.executescript(load_views())
        k._unit = U
        k.ensure_schema(con)
        e1 = file_day(con, "2026-09-01", 999300, 64300)        # expected 9350
        e2 = file_day(con, "2026-09-02", 1764400, 974400)      # expected 7900
        file_day(con, "2026-09-03", 1000000, 0)                # expected 10000, Darpan types 9000 to bhawna
        file_day(con, "2026-09-04", 500000, 100000)            # expected 4000
        con.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p, entered_by) "
                    "VALUES (?, ?, '2026-09-02', 'home_medicine', 'H1', 100000, 'day_resync')", (e2, U))
        con.execute("INSERT INTO cash_adjustment (day_entry_id, amount_p, reason, source, status) VALUES (?, 50000, 'walk', 'manual', 'explained')", (e2,))
        con.commit()
        OWNER, BHAWNA = ("owner", "dr_manoj"), ("recipient", "dr_bhawna")
        um, ub, ud = {"user": "manoj"}, {"user": "bhawna"}, {"user": "darpan"}
        # Darpan types 03 to Dr Bhawna (the ordinary path, through the same row + decide)
        con.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, state, created_by, created_at, updated_at) "
                    "VALUES (?, '2026-09-03', 900000, 'dr_bhawna', 'open', 'darpan', '2026-09-04T09:00:00', '2026-09-04T09:00:00')", (U,))
        k._decide(con, "2026-09-03", k.compute_day(con, "2026-09-03"), k._row(con, "2026-09-03"), "darpan")
        con.commit()

        # a 'yesterday' inside the walk: the pending window ends at real yesterday, so the four days (Sept 2026) are in it
        pend = k._pending_days(con, OWNER)
        kinds = {d["date"]: d["kind"] for d in pend}
        check("owner's pending list: three unlogged days + Darpan's unreceived 03",
              kinds == {"2026-09-01": "unlogged", "2026-09-02": "unlogged", "2026-09-03": "unreceived", "2026-09-04": "unlogged"})
        exp = {d["date"]: d["expected_p"] for d in pend}
        check("expected cash: 01 = 9350 (net - UPI), 02 = 7900 - 1000 home + 500 adjustment = 7400",
              exp["2026-09-01"] == 935000 and exp["2026-09-02"] == 740000)
        pb = k._pending_days(con, BHAWNA)
        check("Dr Bhawna's list carries the three unlogged days and Darpan's 03 handed to her",
              {d["date"] for d in pb} == {"2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04"})

        r = k._log_one(con, um, OWNER, "2026-09-01", None, "dr_manoj")
        con.commit()
        row = k._row(con, "2026-09-01")
        check("owner logs 01 as expected: row 9350 -> Dr Manoj, complete, received by manoj",
              r["ok"] and row["handed_p"] == 935000 and row["handed_to"] == "dr_manoj" and row["state"] == "complete"
              and row["received_by"] == "manoj" and row["created_by"] == "manoj")
        mv = con.execute("SELECT direction, party, amount_p FROM cash_movement WHERE day_entry_id=?", (e1,)).fetchone()
        check("01 landed as cash OUT of the drawer to dr_manoj", mv is not None and tuple(mv) == ("out", "dr_manoj", 935000))
        led = con.execute("SELECT net_p FROM v_cash_ledger WHERE business_date='2026-09-01'").fetchone()[0]
        check("the ledger's net for 01 is now 0 (cash in 9350, cash out 9350)", led == 0)

        r = k._log_one(con, um, OWNER, "2026-09-02", 700000, "dr_bhawna")
        con.commit()
        row = k._row(con, "2026-09-02")
        check("owner logs 02 at 7000 to Dr Bhawna: difference -400 recorded, state open (a reason is Darpan's)",
              r["ok"] and row["handed_p"] == 700000 and row["handed_to"] == "dr_bhawna" and row["diff_p"] == -40000 and row["state"] == "open")

        r = k._log_one(con, ub, BHAWNA, "2026-09-03", None, "dr_bhawna")
        con.commit()
        row = k._row(con, "2026-09-03")
        check("Dr Bhawna stamps Darpan's 03: amount kept (9000, typed by darpan), received by bhawna",
              r["ok"] and row["handed_p"] == 900000 and row["received_by"] == "bhawna" and r["typed_by"] == "darpan")
        r = k._log_one(con, ub, BHAWNA, "2026-09-03", None, "dr_bhawna")
        check("a day already received is refused", not r["ok"] and r["error"] == "already_received")
        r = k._log_one(con, ub, BHAWNA, "2026-09-02", None, "dr_bhawna")
        check("Dr Bhawna cannot re-log 02 (already received by the owner's log)", not r["ok"])
        con.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, state, created_by, created_at, updated_at) "
                    "VALUES (?, '2026-09-04', 400000, 'dr_manoj', 'open', 'darpan', '2026-09-05T09:00:00', '2026-09-05T09:00:00')", (U,))
        con.commit()
        r = k._log_one(con, ub, BHAWNA, "2026-09-04", None, "dr_bhawna")
        check("Dr Bhawna cannot stamp a day Darpan handed to Dr Manoj", not r["ok"] and r["error"] == "not_yours")
        r = k._log_one(con, ub, BHAWNA, "2026-09-04", 350000, "dr_bhawna")
        check("a recipient cannot change Darpan's amount", not r["ok"] and r["error"] in ("not_yours", "amount_differs"))
        r = k._log_one(con, um, OWNER, "2026-09-04", None, "dr_manoj")
        con.commit()
        check("the owner stamps Darpan's 04 as received", r["ok"] and k._row(con, "2026-09-04")["received_by"] == "manoj")
        r = k._log_one(con, um, OWNER, "2099-01-01", None, "dr_manoj")
        check("a future date is refused", not r["ok"] and r["error"] == "future_date")
        check("pending list now empty for the owner", k._pending_days(con, OWNER) == [])
        au = con.execute("SELECT COUNT(*) FROM darpan_kal_audit WHERE action='cash_logged'").fetchone()[0]
        check("one audit line per successful log (4)", au == 4)

        ms = k._month_rows(con)
        m = [x for x in ms if x["ym"] == "2026-09"][0]
        check("month row: sale 42,637 · UPI 11,387 · cash 31,250 · home 1,000 · adj +500 · net 30,750",
              (m["sale_p"], m["upi_p"], m["cash_p"], m["home_p"], m["adjust_p"], m["net_cash_p"]) == (4263700, 1138700, 3125000, 100000, 50000, 3075000))
        check("month row: handed Dr Manoj 13,350 · Dr Bhawna 16,000 (the sum of the four logs)",
              m["to_manoj_p"] == 935000 + 400000 and m["to_bhawna_p"] == 700000 + 900000)
        ds = k._month_days(con, "2026-09")
        d2 = [x for x in ds if x["date"] == "2026-09-02"][0]
        check("day row 02: cash 7,900 · home 1,000 · adj 500 · net 7,400 · handed 7,000 to Dr Bhawna, received",
              (d2["cash_p"], d2["home_p"], d2["adjust_p"], d2["net_cash_p"], d2["handed_p"], d2["handed_to"], d2["received"]) ==
              (790000, 100000, 50000, 740000, 700000, "dr_bhawna", True))
        check("the days of the month add up to the month row", sum(x["net_cash_p"] for x in ds) == m["net_cash_p"])
        con.close()

        # the grants edit, on a v23 shaped file
        g = os.path.join(tmp, "tg23.json")
        json.dump({"_note": "n", "version": 23, "users": {"bhawna": {"extra": ["Clinic"], "mask": ["X"]}, "darpan": {"extra": ["Kal ka hisaab"]}},
                   "defaults": {}}, open(g, "w"), indent=2)
        out = os.path.join(tmp, "tg24.json")
        r = subprocess.run([a.python, "-B", os.path.join(HERE, "grant_kal_s358.py"), g, out], capture_output=True, text=True)
        j = json.load(open(out)) if os.path.exists(out) else {}
        check("grants: v23 -> v24, bhawna gains 'Kal ka hisaab', darpan untouched",
              r.returncode == 0 and j.get("version") == 24 and j["users"]["bhawna"]["extra"] == ["Clinic", "Kal ka hisaab"]
              and j["users"]["darpan"]["extra"] == ["Kal ka hisaab"] and "v24 (S358" in j["_note"])
        r2 = subprocess.run([a.python, "-B", os.path.join(HERE, "grant_kal_s358.py"), out, out + ".x"], capture_output=True, text=True)
        check("grants: a v24 file is refused (not v23)", r2.returncode != 0 and not os.path.exists(out + ".x"))
        html = open(os.path.join(HERE, "darpan_kal.html"), encoding="utf-8").read()
        check("the page carries the log block and the month link",
              "api/pending" in html and "api/log" in html and "/finance/darpan/kal/month" in html and 'VIEW!=="staff"' in html)
        mh = open(os.path.join(HERE, "darpan_month.html"), encoding="utf-8").read()
        check("the month page reads api/month and shows the two heads", "api/month" in mh and "Procedure med." in mh and "Home med." in mh)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("selftest: %d/%d" % (ok, n))
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
