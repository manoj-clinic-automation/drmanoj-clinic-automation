#!/usr/bin/env python3
"""
walk_namecheck_s220.py -- S220 F-277: the LIVE-SHAPE WALK (S208 rule: a kit is
proven only by one). Not a unit test: the REAL entry point `ingest_day`, the
REAL `marg_export` source and column map read from the database, a REAL clinic
ID taken from the live master, and the REAL audit afterwards -- on a COPY of
finance.db, never the live file.

  offline:  FIN_DIR=/dir/with/patched/files  FIN_DB=/path/finance.db  python3 walk_namecheck_s220.py
  the box:  /root/wa/venv/bin/python3 -B /root/finance/walk_namecheck_s220.py

The walk day is 2099-01-01 -- a date no export will ever carry -- created in
the copy and destroyed with it. No patient number is printed (F-185).
"""
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
import finance_ingest as fi                                        # noqa: E402
import finance_returns_audit as fra                                # noqa: E402

fails = 0


def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok:
        fails += 1


tmp = tempfile.mkdtemp(prefix="s220_walk_")
db = os.path.join(tmp, "finance.db")
shutil.copyfile(FIN_DB, db)
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
DAY = "2099-01-01"

# a real patient from the live master: an all-digit clinic ID with a name
p = con.execute("SELECT clinic_id, name FROM patient_ref WHERE clinic_id GLOB '[0-9]*' "
                "AND name IS NOT NULL AND length(name) > 3 AND merged_into IS NULL "
                "ORDER BY id DESC LIMIT 1").fetchone()
check("W0 a real master row exists to walk with", p is not None)
cid, master = p["clinic_id"], p["name"]
stranger = "Zeenat Zzzstranger"          # a name the master cannot hold
con.execute("INSERT INTO day_entry (unit, business_date, status) VALUES ('medical', ?, 'draft')", (DAY,))
con.commit()

# the export, in the live column map's own words (bill_no, bill_date, clinic_id, patient_name, description, amount, mode)
csv = ("bill_no,bill_date,clinic_id,patient_name,description,amount,mode\n"
       "W220001,%s,%s,%s,Tab Test,450,cash\n"          # the ID's own name -> agrees
       "W220002,%s,%s,%s,Tab Test,300,cash\n"          # a STRANGER on that ID -> dispute
       "CNW2201,%s,%s,%s,Tab Test,-300,cash\n"         # the stranger RETURNS it -> the verdict
       "W220003,%s,,Walk in customer,Bandage,120,cash\n"
       % (DAY, cid, master, DAY, cid, stranger, DAY, cid, stranger, DAY))
res = fi.ingest_day(con, "medical", DAY, "marg_export", csv, run_by="walk_s220",
                    source_ref="walk_s220.csv")
check("W1 ingest_day ran ok on the real adapter", res.get("ok") is True, res)
check("W2 four rows read, none dropped (accepted + review == 4)",
      res.get("rows_read") == 4 and res.get("accepted", 0) + res.get("review", 0) == 4, res)

pid_master = con.execute("SELECT id FROM patient_ref WHERE clinic_id=?", (cid,)).fetchone()[0]
rows = con.execute("SELECT source_ref, patient_ref_id, amount_p, service FROM sale_item "
                   "WHERE ingest_batch_id=? ORDER BY source_ref", (res["batch_id"],)).fetchall()
byref = {r["source_ref"]: r for r in rows}
check("W3 the stranger's bill is STILL attached by ID (money path unchanged)",
      "W220002" in byref and byref["W220002"]["patient_ref_id"] == pid_master)
check("W4 the stranger's RETURN is attached by ID too, as a pharmacy_return",
      "CNW2201" in byref and byref["CNW2201"]["patient_ref_id"] == pid_master
      and byref["CNW2201"]["service"] == "pharmacy_return")
disp = con.execute("SELECT bill_no, kind, status FROM identity_dispute WHERE business_date=? "
                   "ORDER BY bill_no", (DAY,)).fetchall()
check("W5 exactly TWO disputes recorded -- the stranger's sale and her return",
      [(d["bill_no"], d["kind"], d["status"]) for d in disp]
      == [("CNW2201", "return", "open"), ("W220002", "sale", "open")],
      [tuple(d) for d in disp])
check("W6 the agreeing bill and the walk-in raised NO dispute",
      con.execute("SELECT COUNT(*) FROM identity_dispute WHERE bill_no IN ('W220001','W220003')")
      .fetchone()[0] == 0)

audit, summary = fra.returns_for_day(con, DAY, "medical")
cn = [a for a in audit if a["bill"] == "CNW2201"]
check("W7 the audit gives the return 'identity disputed' -- not NEVER BOUGHT",
      cn and cn[0]["verdict"] == "identity disputed", cn and cn[0]["verdict"])
check("W8 ... and its note carries both names", cn and stranger in cn[0]["note"] and master in cn[0]["note"])
check("W9 ... and the money is counted (amount 300.00)", cn and cn[0]["amount_p"] == 30000, cn and cn[0]["amount_p"])

# the counter corrects the bill and the day is re-exported: the dispute closes itself
csv2 = csv.replace("W220002,%s,%s,%s" % (DAY, cid, stranger), "W220002,%s,%s,%s" % (DAY, cid, master))
res2 = fi.ingest_day(con, "medical", DAY, "marg_export", csv2, run_by="walk_s220", source_ref="walk_s220b.csv")
st = dict((d["bill_no"], d["status"]) for d in
          con.execute("SELECT bill_no, status FROM identity_dispute WHERE business_date=?", (DAY,)))
check("W10 re-export with the corrected sale CLOSES that dispute, leaves the return's open",
      st == {"W220002": "resolved", "CNW2201": "open"}, st)
check("W11 re-ingest superseded the batch without duplicating disputes",
      con.execute("SELECT COUNT(*) FROM identity_dispute WHERE business_date=?", (DAY,)).fetchone()[0] == 2)

con.close()
shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("WALK GREEN" if fails == 0 else "WALK RED", fails))
sys.exit(fails)
