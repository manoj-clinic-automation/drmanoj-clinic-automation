#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_bankmatch.py — the matcher, proven on the shape of the real 27-Aug.

The fixture reproduces the day that started all of this, from the real MPR and
the real Marg export: 10 bank transactions, 5 bills entered non-cash, 3 rung
as cash, 2 settled payments with no bill. The expected answers are the ones
measured by hand on 29-Aug and confirmed by the owner.

    python3 selftest_bankmatch.py      exit 0 = all passed, 1 = a check failed

Needs no live data and touches nothing: it builds its own temp database.
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bank_match as BM                    # noqa: E402

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


tmp = tempfile.mkdtemp(prefix="bankmatch_")
DB = os.path.join(tmp, "t.db")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# ---- the minimum of the real schema this touches ----
con.execute("CREATE TABLE upi_statement (merchant_id TEXT, unit TEXT, "
            "statement_date TEXT, parsed_total_p INT, txn_count INT, "
            "UNIQUE(merchant_id, statement_date))")
con.execute("CREATE TABLE upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT, "
            "unit TEXT, txn_date TEXT, amount_p INT, rrn TEXT, mode TEXT, "
            "txn_time TEXT, source_sha TEXT, ingested_at TEXT)")
con.execute("CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT, "
            "business_date TEXT, status TEXT)")
con.execute("CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INT, "
            "unit TEXT, service TEXT, amount_p INT, mode TEXT, source_ref TEXT)")
con.execute("CREATE TABLE marg_push_staging (id INTEGER PRIMARY KEY, unit TEXT, "
            "parsed_json TEXT)")
con.execute("CREATE TABLE data_flag (id INTEGER PRIMARY KEY, unit TEXT, "
            "business_date TEXT, code TEXT, severity TEXT, detail TEXT)")

D = "2026-08-27"

# ---- the real bank day: 10 UPI transactions, Rs 11,170 ----
BANK = [(41300, "100709217019"), (105000, "110535071270"), (81200, "189758852271"),
        (164000, "357714965733"), (50000, "623919469893"), (73500, "660516828945"),
        (153000, "660528471228"), (110000, "660555514794"), (250000, "660560826894"),
        (89000, "703164760816")]
for amt, rrn in BANK:
    con.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, "
                "rrn, mode) VALUES ('100000000312505','medical',?,?,?,'UPI')",
                (D, amt, rrn))
con.execute("INSERT INTO upi_statement VALUES ('100000000312505','medical',?,?,10)",
            (D, sum(a for a, _ in BANK)))

# ---- the real Marg day, as an APPLIED day in sale_item ----
con.execute("INSERT INTO day_entry (id, unit, business_date, status) "
            "VALUES (1,'medical',?, 'approved')", (D,))
BILLS = [  # bill, amount_p, mode  (5 entered non-cash, 3 rung cash but settled,
           #                        the rest genuinely cash)
    ("A003228", 41300, "upi"), ("A003240", 110000, "upi"),
    ("A003241", 105000, "upi"), ("A003244", 164000, "upi"),
    ("A003249", 153000, "upi"),
    ("A003230", 250000, "cash"), ("A003242", 89000, "cash"),
    ("A003235", 73500, "cash"),
    ("A003216", 200, "cash"), ("A003217", 150000, "cash"),
    ("A003218", 93000, "cash"), ("A003219", 104000, "cash"),
]
for b, p, m in BILLS:
    con.execute("INSERT INTO sale_item (day_entry_id, unit, service, amount_p, "
                "mode, source_ref) VALUES (1,'medical','pharmacy',?,?,?)",
                (p, m, b))
# a return row must be ignored
con.execute("INSERT INTO sale_item (day_entry_id, unit, service, amount_p, mode, "
            "source_ref) VALUES (1,'medical','pharmacy_return', 40000,'cash','CN123')")
con.commit()

print("[1] the real 27-Aug shape")
code, msg = BM.run_day(con, "medical", D)
ck("exit 0", code == 0, (code, msg))
row = con.execute("SELECT * FROM upi_match_day WHERE business_date=?", (D,)).fetchone()
ck("day matched", row["status"] == "matched")
ck("bank total Rs 11,170", row["bank_p"] == 1117000, row["bank_p"])
ck("5 agreed", row["n_agreed"] == 5, row["n_agreed"])
ck("3 RUNG AS CASH", row["n_cash"] == 3, row["n_cash"])
ck("2 bank orphans (the 812 and the 500)", row["n_bank_orphan"] == 2)
ck("0 bill orphans", row["n_bill_orphan"] == 0)
cashrows = {r["bill_no"]: r for r in con.execute(
    "SELECT * FROM upi_match WHERE business_date=? AND status='cash'", (D,))}
ck("Sureshi Devi's 2500 is on the list with its RRN",
   cashrows.get("A003230") and cashrows["A003230"]["rrn"] == "660560826894")
ck("the orphans carry their amounts",
   sorted(r["txn_amount_p"] for r in con.execute(
       "SELECT txn_amount_p FROM upi_match WHERE status='bank_orphan'")) ==
   [50000, 81200])
ck("the CN row was ignored", con.execute(
    "SELECT COUNT(*) FROM upi_match WHERE bill_no='CN123'").fetchone()[0] == 0)

print("\n[2] running it again replaces, never doubles")
code, _ = BM.run_day(con, "medical", D)
ck("still exit 0", code == 0)
ck("row count unchanged (10 = 8 matched + 2 orphans)", con.execute(
    "SELECT COUNT(*) FROM upi_match WHERE business_date=?", (D,)).fetchone()[0]
   == 10)

print("\n[3] a pending (not yet applied) day reads from the staged payload")
D2 = "2026-08-28"
lines = "bill_date,bill_no,clinic_id,patient_name,phone_last4,description,amount,mode\n" \
        "%s,A003250,,X,,,%0.2f,cash\n%s,A003251,,Y,,,%0.2f,upi\n" \
        "%s,CN0009,,Z,,,%0.2f,cash\n" % (D2, 420.0, D2, 999.0, D2, -50.0)
con.execute("INSERT INTO marg_push_staging (unit, parsed_json) VALUES ('medical',?)",
            (json.dumps({"days": [{"business_date": D2, "lines_csv": lines}]}),))
con.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode) "
            "VALUES ('100000000312505','medical',?,42000,'RRNP1','UPI')", (D2,))
con.execute("INSERT INTO upi_statement VALUES ('100000000312505','medical',?,42000,1)",
            (D2,))
con.commit()
code, msg = BM.run_day(con, "medical", D2)
ck("exit 0", code == 0, msg)
r = con.execute("SELECT * FROM upi_match WHERE business_date=? AND rrn='RRNP1'",
                (D2,)).fetchone()
ck("the 420 settled payment matched the CASH bill", r and r["status"] == "cash"
   and r["bill_no"] == "A003250", dict(r) if r else None)
ck("the entered-upi bill with no settlement is a bill orphan", con.execute(
    "SELECT COUNT(*) FROM upi_match WHERE business_date=? AND status='bill_orphan' "
    "AND bill_no='A003251'", (D2,)).fetchone()[0] == 1)

print("\n[4] waiting and closing")
D3 = "2026-08-29"
code, msg = BM.run_day(con, "medical", D3)
ck("neither feed yet -> exit 3 (retry)", code == 3, (code, msg))
code, msg = BM.run_day(con, "medical", D3, final=True)
ck("neither feed at noon -> no_business, exit 0", code == 0 and "no business" in msg)
con.execute("INSERT INTO upi_statement VALUES ('100000000312505','medical',?,0,0)",
            (D3,))
con.commit()
code, msg = BM.run_day(con, "medical", D3)
ck("bank in, sales missing -> exit 3 naming the sale report",
   code == 3 and "sale report" in msg, msg)
code, msg = BM.run_day(con, "medical", D3, final=True)
ck("at noon that becomes FEEDS INCOMPLETE, exit 1", code == 1)
ck("and a data_flag row exists", con.execute(
    "SELECT COUNT(*) FROM data_flag WHERE code='BANKMATCH_FEED_MISSING' "
    "AND business_date=?", (D3,)).fetchone()[0] == 1)

print("\n[5] a quiet day with a statement is matched, not 'waiting'")
D4 = "2026-08-30"
con.execute("INSERT INTO upi_statement VALUES ('100000000312505','medical',?,0,0)",
            (D4,))
con.execute("INSERT INTO day_entry (id, unit, business_date, status) "
            "VALUES (4,'medical',?, 'approved')", (D4,))
con.execute("INSERT INTO sale_item (day_entry_id, unit, service, amount_p, mode, "
            "source_ref) VALUES (4,'medical','pharmacy', 10000,'cash','A003260')")
con.commit()
code, msg = BM.run_day(con, "medical", D4)
ck("zero bank txns + bills -> matched, nothing flagged", code == 0 and
   con.execute("SELECT status FROM upi_match_day WHERE business_date=?",
               (D4,)).fetchone()["status"] == "matched")

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
con.close()
import shutil                                # noqa: E402
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if _fail else 0)
