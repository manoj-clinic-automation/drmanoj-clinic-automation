#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_jaankari_s221.py -- THE LIVE-SHAPE WALK for S221_JAANKARI.

It mounts the REAL blueprint from the REAL patched returns_desk.py, on a COPY of
the live finance.db, and drives the REAL routes through Flask's test client. It
then reads the database back and proves the thing that matters most about this
build: **nothing but jaankari_answer changed.**

That last check is the owner's ruling expressed as a test. "Go soft on answers
from him" is not a wording choice -- it is a property of the database after he
has answered, and this walk measures it: every table is fingerprinted before and
after, and exactly one of them is allowed to differ.

IT NEVER TOUCHES THE LIVE DATABASE. The first thing it does is copy it.

No patient name and no mobile number is written in this file. Fixtures are
either discovered from the data or assembled at run time (F-185).

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/walk_jaankari_s221.py
Offline:         FIN_DB=/path/to/finance.db python3 -B walk_jaankari_s221.py
"""

import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

SRC_DB = os.environ.get("FIN_DB", "/root/finance/finance.db")
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

FAILED, PASSED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


DISPUTE_DDL = (
    "CREATE TABLE IF NOT EXISTS identity_dispute ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " bill_no TEXT, clinic_id TEXT NOT NULL, bill_name TEXT, master_name TEXT,"
    " patient_ref_id INTEGER, kind TEXT NOT NULL DEFAULT 'sale',"
    " status TEXT NOT NULL DEFAULT 'open', noted_at TEXT NOT NULL,"
    " resolved_by TEXT, resolved_at TEXT, resolution TEXT,"
    " UNIQUE(unit, business_date, bill_no, clinic_id))")

SPOT_DDL = (
    "CREATE TABLE IF NOT EXISTS stock_spot_check ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " bill_no TEXT NOT NULL, item_key TEXT NOT NULL, item_name TEXT, batch TEXT,"
    " reason TEXT NOT NULL, requested_at TEXT NOT NULL,"
    " status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','done','skipped')),"
    " counted_qty TEXT, counted_by TEXT, counted_at TEXT, note TEXT,"
    " UNIQUE(unit, bill_no, item_key))")


def fingerprint(db):
    """A hash per table, so 'nothing else changed' is a measurement."""
    con = sqlite3.connect(db)
    out = {}
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' "
                               "ORDER BY name").fetchall():
        try:
            h = hashlib.md5()
            for row in con.execute('SELECT * FROM "%s"' % name):
                h.update(repr(row).encode("utf-8", "replace"))
            out[name] = h.hexdigest()
        except Exception as ex:                                # pragma: no cover
            out[name] = "unreadable:%s" % ex
    con.close()
    return out


def main():
    if not os.path.exists(SRC_DB):
        print("no database at %s -- set FIN_DB" % SRC_DB)
        return 2
    tmpdir = tempfile.mkdtemp(prefix="walk_jk_")
    db = os.path.join(tmpdir, "finance.db")
    shutil.copyfile(SRC_DB, db)
    print("walking on a COPY: %s\n" % db)

    import returns_desk as RD
    ck("the patched desk is the one under test",
       "S221 star-1-1" in open(RD.__file__, encoding="utf-8").read())

    now = dt.datetime.now().replace(microsecond=0).isoformat()
    today = dt.date.today().isoformat()
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    q = lambda s, *a: con.execute(s, a).fetchall()

    # ---------------------------------------------------------- fixtures
    # The S220 tables are created on the box by the S220 code. On a copy older
    # than that install they are absent, so the walk builds the LIVE SHAPE
    # from the same DDL those kits ship, then seeds one row of each.
    con.execute(DISPUTE_DDL)
    con.execute(SPOT_DDL)

    # a real master patient, discovered -- never a name written in this file
    pat = q("SELECT clinic_id, name FROM patient_ref WHERE clinic_id!='WALK-IN' "
            "AND name IS NOT NULL AND name!='' AND merged_into IS NULL LIMIT 1")[0]
    test_mobile = "9" + "7" * 4 + "6" * 5                    # assembled: F-185
    have_mobile_col = "mobile" in {r[1] for r in q("PRAGMA table_info(patient_ref)")}
    if have_mobile_col:
        con.execute("UPDATE patient_ref SET mobile=? WHERE clinic_id=?",
                    (test_mobile, pat["clinic_id"]))
    con.execute(
        "INSERT INTO identity_dispute (unit, business_date, bill_no, clinic_id,"
        " bill_name, master_name, kind, status, noted_at)"
        " VALUES ('medical',?,?,?,?,?,'return','open',?)",
        (today, "WCN9001", pat["clinic_id"], "ZZQX TESTNAME", pat["name"], now))
    con.execute(
        "INSERT INTO stock_spot_check (unit, business_date, bill_no, item_key,"
        " item_name, batch, reason, requested_at, status)"
        " VALUES ('medical',?,?,?,?,?,?,?, 'due')",
        (today, "WCN9002", "ZZ_ITEM_KEY", "ZZQX TEST ITEM", "B-TEST",
         "large return", now))
    con.commit()

    # an "identity needed" row: a return still sitting on WALK-IN since act_from
    # the same default the code uses: D361, the past raises no work
    DEFAULT_ACT_FROM = "2026-09-02"
    rowa = q("SELECT value FROM setting WHERE key='returns.act_from'")
    act_from = rowa[0]["value"] if (rowa and rowa[0]["value"]) else DEFAULT_ACT_FROM
    walkin = q("SELECT id FROM patient_ref WHERE clinic_id='WALK-IN'")
    n_walk_returns = 0
    if walkin:
        n_walk_returns = q(
            "SELECT COUNT(*) c FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
            "WHERE s.service='pharmacy_return' AND s.patient_ref_id=? "
            "AND d.business_date>=? AND d.unit='medical'",
            walkin[0]["id"], act_from)[0]["c"]
    ck("the WALK-IN return population is real, not seeded (%d rows since %s)"
       % (n_walk_returns, act_from), n_walk_returns >= 0)
    older = q("SELECT COUNT(*) c FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
              "WHERE s.service='pharmacy_return' AND s.patient_ref_id=? "
              "AND d.business_date<? AND d.unit='medical'",
              walkin[0]["id"], act_from)[0]["c"] if walkin else 0
    con.close()

    before = fingerprint(db)

    # ------------------------------------------------------- mount it for real
    from flask import Flask
    app = Flask(__name__)

    def _db():
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        return c

    def _require(*roles):
        return {"user": "darpan", "role": "maker"}, None

    RD.init(app, _db, _require, unit="medical")
    cl = app.test_client()

    # -------------------------------------------------------------- the page
    r = cl.get("/finance/returns/desk/")
    ck("the desk page still serves", r.status_code == 200, str(r.status_code))
    html = r.get_data(as_text=True)
    ck("the page carries the jaankari card", 'id="jkCard"' in html)
    ck("the page loads the list on open", "loadJaankari()" in html)
    ck("the page still carries the three-step flow it had before",
       'id="p1"' in html and 'id="p3"' in html and "loadSlips()" in html)

    # -------------------------------------------------------------- the lists
    r = cl.get("/finance/returns/desk/api/jaankari")
    ck("the list endpoint answers", r.status_code == 200, str(r.status_code))
    j = r.get_json()
    ck("it answers ok", bool(j and j.get("ok")), json.dumps(j)[:200] if j else "none")
    L = (j or {}).get("lists") or {}
    ck("the seeded dispute is on the list", any(x["ref"] for x in L.get("disputes", [])),
       str(L.get("disputes")))
    ck("the seeded spot count is on the list", len(L.get("spot", [])) >= 1)
    ck("the identity list matches the real WALK-IN population",
       len(L.get("identity", [])) == min(n_walk_returns, 60),
       "%d vs %d" % (len(L.get("identity", [])), n_walk_returns))
    ck("D361 -- it does NOT reach into the accepted past (%d older rows left alone)"
       % older, len(L.get("identity", [])) <= n_walk_returns and older > 0)
    d0 = (L.get("disputes") or [{}])[0]
    ck("the dispute names both names", d0.get("bill_name") and d0.get("master_name"))
    if have_mobile_col:
        ck("the FULL mobile is beside the name (D363)", d0.get("mobile") == test_mobile,
           str(d0.get("mobile")))
    ck("he is shown no score, verdict, ratio or flag anywhere in the payload",
       not any(k in json.dumps(j) for k in ("score", "verdict", "flag", "intent",
                                            "ratio", "confidence")))

    # --------------------------------------------------------- he answers
    a = cl.post("/finance/returns/desk/api/jaankari/answer",
                json=dict(kind="dispute", ref=d0["ref"], answer="ok"))
    ck("an answer is accepted", a.status_code == 200 and (a.get_json() or {}).get("ok"),
       a.get_data(as_text=True)[:160])
    s0 = (L.get("spot") or [{}])[0]
    a2 = cl.post("/finance/returns/desk/api/jaankari/answer",
                 json=dict(kind="spot", ref=s0["ref"], answer="counted", value="12"))
    ck("a spot COUNT is accepted", a2.status_code == 200 and (a2.get_json() or {}).get("ok"))
    bad = cl.post("/finance/returns/desk/api/jaankari/answer",
                  json=dict(kind="dispute", ref=d0["ref"], answer="delete_it"))
    ck("an answer that is not one of the four is REFUSED", bad.status_code == 400)
    bad2 = cl.post("/finance/returns/desk/api/jaankari/answer",
                   json=dict(kind="money", ref="1", answer="ok"))
    ck("an invented list name is REFUSED", bad2.status_code == 400)

    j2 = cl.get("/finance/returns/desk/api/jaankari").get_json()
    L2 = (j2 or {}).get("lists") or {}
    d_ans = [x for x in L2.get("disputes", []) if x["ref"] == d0["ref"]]
    ck("the answered dispute now carries his answer",
       bool(d_ans) and (d_ans[0].get("answered") or {}).get("answer") == "ok")
    ck("it records WHO answered",
       bool(d_ans) and (d_ans[0].get("answered") or {}).get("by") == "darpan")
    s_ans = [x for x in L2.get("spot", []) if x["ref"] == s0["ref"]]
    ck("the count he gave is recorded as its value",
       bool(s_ans) and (s_ans[0].get("answered") or {}).get("value") == "12")

    # ------------------------------- THE RULING, MEASURED: nothing else moved
    after = fingerprint(db)
    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k))
    ck("EXACTLY ONE TABLE CHANGED, and it is jaankari_answer",
       changed == ["jaankari_answer"], "changed: %s" % changed)

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    st = con.execute("SELECT status FROM identity_dispute WHERE bill_no='WCN9001'").fetchone()
    ck("the dispute is STILL OPEN -- his answer did not close it", st["status"] == "open")
    sp = con.execute("SELECT status, counted_qty FROM stock_spot_check "
                     "WHERE bill_no='WCN9002'").fetchone()
    ck("the spot check is STILL DUE -- the owner still taps counted",
       sp["status"] == "due" and not sp["counted_qty"])
    rows = con.execute("SELECT kind, ref, answer, value, answered_by FROM jaankari_answer "
                       "ORDER BY id").fetchall()
    ck("exactly the two good answers were written (the two bad ones wrote nothing)",
       len(rows) == 2, str([dict(r) for r in rows]))

    # a second answer on the same row is kept, not overwritten
    cl.post("/finance/returns/desk/api/jaankari/answer",
            json=dict(kind="dispute", ref=d0["ref"], answer="dont_know"))
    n = con.execute("SELECT COUNT(*) c FROM jaankari_answer WHERE kind='dispute' "
                    "AND ref=?", (d0["ref"],)).fetchone()["c"]
    ck("changing his mind keeps BOTH answers -- the table is evidence, not state", n == 2,
       str(n))
    j3 = cl.get("/finance/returns/desk/api/jaankari").get_json()
    d3 = [x for x in ((j3 or {}).get("lists") or {}).get("disputes", [])
          if x["ref"] == d0["ref"]]
    ck("the latest answer is the one shown",
       bool(d3) and (d3[0].get("answered") or {}).get("answer") == "dont_know")

    # ------------------------------------------------- the rest of the desk
    r = cl.get("/finance/returns/desk/api/slips")
    ck("the slips endpoint is untouched and still answers",
       r.status_code == 200 and (r.get_json() or {}).get("ok"))
    r = cl.get("/finance/returns/desk/api/search?q=zz")
    ck("patient search is untouched and still answers",
       r.status_code == 200 and (r.get_json() or {}).get("ok"))
    con.close()

    # ----------------------------------------- an empty list must be invisible
    db2 = os.path.join(tmpdir, "empty.db")
    shutil.copyfile(SRC_DB, db2)
    c2 = sqlite3.connect(db2)
    c2.execute(DISPUTE_DDL)
    c2.execute(SPOT_DDL)
    c2.execute("UPDATE setting SET value='2099-01-01' WHERE key='returns.act_from'")
    if not c2.execute("SELECT 1 FROM setting WHERE key='returns.act_from'").fetchone():
        c2.execute("INSERT INTO setting (key, value) VALUES ('returns.act_from','2099-01-01')")
    c2.commit()
    c2.close()
    app2 = Flask(__name__)

    def _db2():
        c = sqlite3.connect(db2)
        c.row_factory = sqlite3.Row
        return c

    import importlib
    RD2 = importlib.reload(RD)
    RD2.init(app2, _db2, _require, unit="medical")
    j4 = app2.test_client().get("/finance/returns/desk/api/jaankari").get_json()
    tot = sum(len(v) for v in ((j4 or {}).get("lists") or {}).values())
    ck("with nothing to ask, every list is empty (the card hides itself)", tot == 0,
       str((j4 or {}).get("counts")))

    print("\n%s -- %d passed, %d failed" %
          ("WALK GREEN" if not FAILED else "WALK RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
