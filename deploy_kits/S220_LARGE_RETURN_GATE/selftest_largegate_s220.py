#!/usr/bin/env python3
"""
selftest_largegate_s220.py -- S220 item 1: the large-return gate + the spot-count
list, proved LIVE-SHAPE on a COPY of finance.db with the three PATCHED files:
the real escalate_day(), the real darpan blueprint on a bare Flask app (the
selftest_darpan pattern), the real September returns.

  offline:  FIN_DIR=/dir/with/patched/files  FIN_DB=/path/finance.db  python3 selftest_largegate_s220.py
  the box:  /root/wa/venv/bin/python3 -B /root/finance/selftest_largegate_s220.py
No patient name or number is printed. Exit code = failures.
"""
import os
import shutil
import sqlite3
import sys
import tempfile

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
FIN_DB = os.environ.get("FIN_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)
from flask import Flask, jsonify                                    # noqa: E402
import darpan_app                                                   # noqa: E402
import finance_returns_escalate as fre                              # noqa: E402

fails = 0


def check(name, ok, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail and not ok else ""))
    if not ok:
        fails += 1


tmp = tempfile.mkdtemp(prefix="s220_large_")
db = os.path.join(tmp, "finance.db")
shutil.copyfile(FIN_DB, db)
CON = sqlite3.connect(db, check_same_thread=False)
CON.row_factory = sqlite3.Row
BIG = fre.large_p(CON)
check("G0 patched files present (spot_list_day · _spot_checks · large_p)",
      hasattr(fre, "spot_list_day") and hasattr(darpan_app, "_spot_checks") and BIG >= 1000, BIG)
act = fre.act_from(CON)

# a day on/after the cutover that has a LARGE return, and a historical day that has one
day = CON.execute("SELECT d.business_date FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
                  "WHERE s.service='pharmacy_return' AND d.business_date>=? AND s.amount_p>=? "
                  "ORDER BY d.business_date DESC LIMIT 1", (act, BIG)).fetchone()
hist = CON.execute("SELECT d.business_date FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
                   "WHERE s.service='pharmacy_return' AND d.business_date<? AND s.amount_p>=? "
                   "ORDER BY d.business_date DESC LIMIT 1", (act, BIG)).fetchone()
# On a fresh box there may be no Rs 1,000+ return since the cutover yet. Then the
# walk makes one: a synthetic day (2099-01-01 -- no export will ever carry it),
# a credit note of Rs 1,500 on a real patient, two real-shaped item lines. The
# copy is destroyed with the temp dir; the live db is never touched.
WALK = "2099-01-01"
if day is None:
    pid = CON.execute("SELECT id FROM patient_ref WHERE clinic_id GLOB '[0-9]*' ORDER BY id DESC LIMIT 1").fetchone()[0]
    CON.execute("INSERT INTO day_entry (unit, business_date, status) VALUES ('medical', ?, 'draft')", (WALK,))
    eid = CON.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (WALK,)).fetchone()[0]
    CON.execute("INSERT INTO ingest_batch (day_entry_id, unit, adapter, source_ref, rows_read, status, run_by, run_at) "
                "VALUES (?, 'medical', 'marg_export', 'walk_s220.csv', 1, 'ok', 'selftest', ?)", (eid, WALK + "T00:00:00"))
    bid = CON.execute("SELECT id FROM ingest_batch WHERE day_entry_id=?", (eid,)).fetchone()[0]
    CON.execute("INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, service, description, "
                "amount_p, mode, source, source_ref, confidence) VALUES (?,?,?,?,'pharmacy_return','walk',150000,'cash','manual','CNW2299',1.0)",
                (eid, bid, "medical", pid))
    for seq, (nm, q, pk, rate) in enumerate([("WALK ITEM A", "1:0", "1*10", 100000), ("WALK ITEM B", "0:5", "1*10", 50000)], 1):
        CON.execute("INSERT INTO sale_line_item (day_entry_id, ingest_batch_id, unit, business_date, bill_no, is_return, seq, "
                    "item_name, item_key, pack, qty_raw, amount_p, expiry_ym, batch) VALUES (?,?,?,?,?,1,?,?,?,?,?,?,?,?)",
                    (eid, bid, "medical", WALK, "CNW2299", seq, nm, nm, pk, q, rate, "2028-01", "WALKB%d" % seq))
    CON.commit()
    day = (WALK,)
    print("info  no Rs 1,000+ return since the cutover on this db -- walking on a synthetic one (%s)" % WALK)
check("G1 a large return exists on/after the cutover, and one before it", day is not None and hist is not None)
day, hist = day[0], hist[0]

# ---------------------------------------------------------------- the escalation writes the list
n0 = CON.execute("SELECT COUNT(*) FROM stock_spot_check").fetchone()[0] if CON.execute(
    "SELECT name FROM sqlite_master WHERE name='stock_spot_check'").fetchone() else 0
r1 = fre.escalate_day(CON, day, "medical")
CON.commit()
due = CON.execute("SELECT bill_no, item_key, reason, status FROM stock_spot_check WHERE business_date=?", (day,)).fetchall()
check("E1 escalate_day on the cutover-side day lists that return's items, status due",
      due and all(d["status"] == "due" for d in due) and any("large return" in d["reason"] for d in due), (r1, len(due)))
lines = CON.execute("SELECT COUNT(*) FROM sale_line_item l JOIN sale_item s ON s.source_ref=l.bill_no "
                    "JOIN day_entry d ON d.id=s.day_entry_id WHERE l.is_return=1 AND d.business_date=? "
                    "AND s.service='pharmacy_return' AND s.amount_p>=?", (day, BIG)).fetchone()[0]
check("E2 ... one row per item line of the large return(s), no more",
      len([d for d in due if "large return" in d["reason"]]) == lines, (len(due), lines))
n1 = CON.execute("SELECT COUNT(*) FROM stock_spot_check").fetchone()[0]
fre.escalate_day(CON, day, "medical")
CON.commit()
check("E3 a second escalation adds nothing (UNIQUE per bill + item)",
      CON.execute("SELECT COUNT(*) FROM stock_spot_check").fetchone()[0] == n1)
r2 = fre.escalate_day(CON, hist, "medical")
check("E4 a historical day is 'historical' and lists nothing (D361)",
      r2 == "historical" and CON.execute("SELECT COUNT(*) FROM stock_spot_check WHERE business_date=?", (hist,)).fetchone()[0] == 0, r2)
check("E5 the escalation's MONEY_FLAGS are unchanged -- size is not a money finding",
      fre.MONEY_FLAGS == ("NEVER BOUGHT", "REFUNDED MORE THAN PAID", "RETURNED MORE THAN SOLD", "DISCOUNTED RETURN"))

# ---------------------------------------------------------------- the owner's card (the real blueprint)
ROLE = {"user": "manoj", "roles": ["checker", "maker"]}


def dbget():
    return CON


def require(*roles):
    have = set(ROLE.get("roles") or [])
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(ROLE), None


app = Flask(__name__)


@app.route("/finance/api/day", methods=["POST"])
def fake_filing():
    return jsonify(ok=True)


darpan_app.init(app, dbget, require, unit="medical")
c = app.test_client()
month = day[:7]
j = c.get("/finance/darpan/api/cn-detail?month=" + month).get_json()
check("C1 cn-detail answers ok and carries large_p and spot_checks", j.get("ok") and j.get("large_p") == BIG and isinstance(j.get("spot_checks"), list), (j.get("large_p"), type(j.get("spot_checks"))))
big_rows = [n for n in j["notes"] if n.get("large")]
small = [n for n in j["notes"] if not n.get("large") and not n.get("historical")]
check("C2 every row at/above the line is marked large; none below it",
      big_rows and all(n["amount_p"] >= BIG for n in big_rows) and all(n["amount_p"] < BIG for n in small), (len(big_rows), len(small)))
target = [n for n in big_rows if n.get("verdict") == "ok" and (n.get("approval") is None or n["approval"]["status"] == "pending")]
target = target or big_rows
check("C3 a large return NEEDS the owner's decision even when its verdict is ok",
      all(n["needs_approval"] for n in big_rows))
check("C4 ... and it counts as PENDING (NEED YOU), not as flagged",
      j["pending_approval"] >= len([n for n in big_rows if n.get("approval") is None or n["approval"]["status"] == "pending"]))
check("C5 the spot-count list reaches the card with the items to count",
      any(s["status"] == "due" for s in j["spot_checks"]))
bill = target[0]["bill"]
r = c.post("/finance/darpan/api/cn-approve", json=dict(bill=bill, decision="approved", note="selftest")).get_json()
j2 = c.get("/finance/darpan/api/cn-detail?month=" + month).get_json()
check("C6 the owner's OK through the existing approve flow clears that return from pending",
      r.get("ok") and j2["pending_approval"] == j["pending_approval"] - 1, (r, j["pending_approval"], j2["pending_approval"]))
sid = [s for s in j2["spot_checks"] if s["status"] == "due"][0]["id"]
r = c.post("/finance/darpan/api/spot-check", json=dict(id=sid, status="done")).get_json()
check("C7 a count without a quantity is refused", not r.get("ok") and r.get("error") == "qty_required", r)
r = c.post("/finance/darpan/api/spot-check", json=dict(id=sid, status="done", counted_qty="2:5", note="shelf B")).get_json()
row = CON.execute("SELECT status, counted_qty, counted_by, note FROM stock_spot_check WHERE id=?", (sid,)).fetchone()
check("C8 a count is recorded as typed, by name, with the note",
      r.get("ok") and tuple(row) == ("done", "2:5", "manoj", "shelf B"), tuple(row) if row else r)
ROLE["user"] = "darpan"
r = c.post("/finance/darpan/api/spot-check", json=dict(id=sid, status="skipped")).get_json()
check("C9 a non-owner cannot record a count (owner only, like approvals)", r.get("error") == "owner_only")
ROLE["user"] = "manoj"
j3 = c.get("/finance/darpan/api/cn-detail?month=" + month).get_json()
check("C10 the card now shows that item counted", any(s["id"] == sid and s["status"] == "done" for s in j3["spot_checks"]))

# ---------------------------------------------------------------- the page
hub = open(os.path.join(FIN_DIR, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
check("P1 the hub carries the gate line, the row badge, the spot-count list and its action",
      hub.count("S220 LARGE-RETURN GATE") == 1 and "your OK" in hub and "Spot-count list" in hub and hub.count("function spotCount(") == 1)
check("P2 the hub carries no Hindi (owner: all English)", not any("ऀ" <= ch <= "ॿ" for ch in hub))

CON.close()
shutil.rmtree(tmp, ignore_errors=True)
print("\n%s -- %d check(s) failed" % ("ALL GREEN" if fails == 0 else "RED", fails))
sys.exit(fails)
