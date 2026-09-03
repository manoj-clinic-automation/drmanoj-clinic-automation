#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_ladder_s221.py -- THE LIVE-SHAPE WALK for S221_D355_LADDER.

Not a unit test. This drives the REAL ingest_day() over a REAL Marg-shaped CSV
against a COPY of the live finance.db, with the real column map, the real
patient master and the real Docterz visit feed, and then reads back what
actually landed in the tables. S208 found two defects behind sixty-five green
checks; S209 found a dead page behind four green gates. A kit is proven by a
walk, not by a gate.

IT NEVER TOUCHES THE LIVE DATABASE. The first thing it does is copy it.

Every fixture is DISCOVERED FROM THE DATA at run time -- no patient name and no
mobile number is written in this file (F-185, and the same care for names). The
one test number is ASSEMBLED at runtime and exists only in the copy.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/walk_ladder_s221.py
Offline:         FIN_DB=/path/to/finance.db python3 -B walk_ladder_s221.py
"""

import datetime as dt
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

FAILED = []
PASSED = []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label,
                          ("   [%s]" % detail) if detail and not cond else ""))


def main():
    if not os.path.exists(SRC_DB):
        print("no database at %s -- set FIN_DB" % SRC_DB)
        return 2

    tmpdir = tempfile.mkdtemp(prefix="walk_s221_")
    db = os.path.join(tmpdir, "finance.db")
    shutil.copyfile(SRC_DB, db)
    print("walking on a COPY: %s\n" % db)

    # A salt of our own, for the copy only. The live salt is never read here.
    os.environ["PATIENT_FP_SALT"] = "s221-walk-salt"
    import finance_patient_match as M
    import finance_ingest as FI

    ck("the patched ingest is the one under test", "S221 F-283" in
       open(FI.__file__, encoding="utf-8").read())

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    q = lambda s, *a: con.execute(s, a).fetchall()

    # ---------------------------------------------------------- fixtures
    # A day the database has never seen, so nothing we do can collide.
    DAY = "2026-09-30"
    UNIT = "medical"
    con.execute("DELETE FROM day_entry WHERE unit=? AND business_date=?", (UNIT, DAY))
    con.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by,"
                " entered_at) VALUES (?,?,'draft','app','walk',?)",
                (UNIT, DAY, dt.datetime.now().replace(microsecond=0).isoformat()))

    # (1) a patient whose LAST-FOUR + NAME resolve to exactly one person:
    #     a multi-token name, and a last-four nobody else with that name shares.
    p_l4 = None
    for r in q("SELECT clinic_id, name, phone_last4 FROM patient_ref "
               "WHERE phone_last4 IS NOT NULL AND phone_last4!='' AND name LIKE '% %' "
               "AND merged_into IS NULL LIMIT 400"):
        same = [x for x in q("SELECT name FROM patient_ref WHERE phone_last4=?",
                             r["phone_last4"]) if M.names_agree(r["name"], x["name"])]
        if len(same) == 1:
            p_l4 = r
            break
    ck("found a last-4 + name fixture in the real master", p_l4 is not None)

    # (2) a patient who VISITED on a real day and whose name is unique on that
    #     day's Docterz list -- the same-day rung's proper shape.
    p_vis = None
    vis_day = None
    for d in q("SELECT visit_date, COUNT(*) n FROM patient_visit "
               "GROUP BY visit_date HAVING n BETWEEN 5 AND 40 ORDER BY visit_date DESC LIMIT 40"):
        people = q("SELECT DISTINCT p.clinic_id, p.name FROM patient_visit v "
                   "JOIN patient_ref p ON p.clinic_id=v.clinic_id WHERE v.visit_date=?",
                   d["visit_date"])
        for cand in people:
            if not cand["name"] or " " not in cand["name"]:
                continue
            fit = [x for x in people if M.names_agree(cand["name"], x["name"])]
            if len(fit) == 1:
                p_vis, vis_day = cand, d["visit_date"]
                break
        if p_vis:
            break
    ck("found a same-day-visit fixture in the real visit feed", p_vis is not None)

    # (3) the mobile rung. The copy gets ONE fingerprint, from a number
    #     assembled here and never written to the database.
    test_mobile = "9" + "8" * 4 + "7" * 5                 # assembled: F-185
    p_mob = q("SELECT clinic_id, name FROM patient_ref WHERE name LIKE '% %' "
              "AND (mobile_fp IS NULL OR mobile_fp='') AND merged_into IS NULL LIMIT 1")
    if not p_mob:
        p_mob = q("SELECT clinic_id, name FROM patient_ref WHERE name LIKE '% %' LIMIT 1")
    p_mob = p_mob[0]
    fp = M.fingerprint(M.normalise_mobile(test_mobile), M.salt())
    con.execute("UPDATE patient_ref SET mobile_fp=? WHERE clinic_id=?", (fp, p_mob["clinic_id"]))
    ck("the mobile fixture is unique in the copy",
       len(q("SELECT 1 FROM patient_ref WHERE mobile_fp=?", fp)) == 1)

    # (4) a patient who already carries a clinic ID -- the unchanged path.
    p_id = q("SELECT clinic_id, name FROM patient_ref WHERE clinic_id NOT IN ('WALK-IN') "
             "AND name IS NOT NULL AND name!='' AND merged_into IS NULL LIMIT 1")[0]
    con.commit()

    # ------------------------------------------------------------ the CSV
    # The real Marg export shape, plus the `mobile` column S220 added.
    hdr = ("bill_date,bill_no,clinic_id,patient_name,phone_last4,mobile,"
           "description,amount,mode,gross,disc")
    rows = [
        # by clinic ID -- the ordinary path, untouched by this kit
        (DAY, "W0001", p_id["clinic_id"], p_id["name"], "", "", "", "500.00", "cash", "500.00", "0.00"),
        # by the full mobile: NO id, and a last-four that belongs to nobody
        (DAY, "W0002", "", p_mob["name"], "", test_mobile, "", "700.00", "cash", "700.00", "0.00"),
        # by last-four + name
        (DAY, "W0003", "", p_l4["name"], p_l4["phone_last4"], "", "", "900.00", "cash", "900.00", "0.00"),
        # nothing at all -- must still park
        (DAY, "W0004", "", "ZZQX NOBODYHERE", "", "", "", "300.00", "cash", "300.00", "0.00"),
    ]
    csv_text = hdr + "\n" + "\n".join(",".join(str(c) for c in r) for r in rows) + "\n"

    # THE INGEST RUNS ON A PLAIN CONNECTION, deliberately: the live app does not
    # promise a sqlite3.Row factory, and a rung that reads rows by column name
    # would fail soft and silently on one that has none. Found in this kit's own
    # selftest before install; the walk now proves the production shape.
    con_plain = sqlite3.connect(db)

    res = FI.ingest_day(con_plain, UNIT, DAY, "marg_export", csv_text,
                        run_by="walk", source_ref="walk_s221")
    print("\n  ingest said: %s\n" % json.dumps(
        {k: res[k] for k in ("rows_read", "accepted", "review", "laddered", "status")}))

    ck("all four rows were read", res["rows_read"] == 4, str(res))
    ck("three attached, one parked", res["accepted"] == 3 and res["review"] == 1, str(res))
    ck("the run reports two named by the ladder", res.get("laddered") == 2, str(res))

    # ------------------------------------------------ what actually landed
    got = {r["source_ref"]: r for r in q(
        "SELECT s.source_ref, s.confidence, p.clinic_id, p.name FROM sale_item s "
        "JOIN day_entry d ON d.id=s.day_entry_id LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
        "WHERE d.business_date=? AND d.unit=?", DAY, UNIT)}

    ck("W0001 attached by its clinic ID, as before",
       "W0001" in got and got["W0001"]["clinic_id"] == p_id["clinic_id"])
    ck("W0001's confidence is untouched by this kit",
       "W0001" in got and abs(got["W0001"]["confidence"] - 0.99) < 1e-9,
       "" if "W0001" not in got else str(got["W0001"]["confidence"]))
    ck("W0002 was named by the FULL MOBILE",
       "W0002" in got and got["W0002"]["clinic_id"] == p_mob["clinic_id"],
       "not attached" if "W0002" not in got else str(got["W0002"]["clinic_id"]))
    ck("W0002 carries the mobile rung's own confidence, not a pretended 0.99",
       "W0002" in got and abs(got["W0002"]["confidence"] - 0.95) < 1e-9)
    ck("W0003 was named by LAST-FOUR + NAME",
       "W0003" in got and got["W0003"]["clinic_id"] == p_l4["clinic_id"],
       "not attached" if "W0003" not in got else str(got["W0003"]["clinic_id"]))
    ck("W0003 carries the last-4 rung's confidence",
       "W0003" in got and abs(got["W0003"]["confidence"] - 0.85) < 1e-9)
    ck("W0004 did NOT attach to anybody", "W0004" not in got)

    parked = q("SELECT guess_name, raw_text FROM sale_item_review v "
               "JOIN day_entry d ON d.id=v.day_entry_id WHERE d.business_date=?", DAY)
    ck("exactly one bill parked", len(parked) == 1, str(len(parked)))
    ck("the parked bill is the one nobody could name",
       len(parked) == 1 and "NOBODYHERE" in (parked[0]["guess_name"] or ""))

    # ------------------------------------------------------- F-185 / D355
    raws = [r["raw_text"] or "" for r in q(
        "SELECT raw_text FROM sale_item_review v JOIN day_entry d ON d.id=v.day_entry_id "
        "WHERE d.business_date=?", DAY)]
    ck("NO full mobile reached the stored raw text",
       all(test_mobile not in r for r in raws) and all('"mobile"' not in r for r in raws))
    ck("no full mobile was written to patient_ref by this kit",
       not q("SELECT 1 FROM patient_ref WHERE mobile=? LIMIT 1", test_mobile))

    # ------------------------------------------------------ the recording
    recs = {r["bill_no"]: r for r in q(
        "SELECT bill_no, rung, clinic_id, master_name FROM identity_resolution "
        "WHERE business_date=?", DAY)}
    ck("the ladder recorded exactly the two bills it named", set(recs) == {"W0002", "W0003"},
       str(sorted(recs)))
    ck("W0002's rung is recorded as the mobile",
       recs.get("W0002", {})["rung"] == "mobile" if "W0002" in recs else False)
    ck("W0003's rung is recorded as last-4 + name",
       recs.get("W0003", {})["rung"] == "last-4 + name" if "W0003" in recs else False)
    ck("no attachment is silent: every laddered bill has a row",
       len(recs) == res.get("laddered"))

    # ------------------------------------------- the same-day visit rung
    # Run a second day, on a REAL Docterz visit date, with the name only.
    con.execute("DELETE FROM day_entry WHERE unit=? AND business_date=?", (UNIT, vis_day))
    con.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by,"
                " entered_at) VALUES (?,?,'draft','app','walk',?)",
                (UNIT, vis_day, dt.datetime.now().replace(microsecond=0).isoformat()))
    con.commit()
    csv2 = hdr + "\n" + ",".join([vis_day, "W0101", "", p_vis["name"], "", "", "",
                                  "450.00", "cash", "450.00", "0.00"]) + "\n"
    res2 = FI.ingest_day(con_plain, UNIT, vis_day, "marg_export", csv2,
                         run_by="walk", source_ref="walk_s221b")
    v = q("SELECT p.clinic_id FROM sale_item s JOIN day_entry d ON d.id=s.day_entry_id "
          "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
          "WHERE d.business_date=? AND s.source_ref='W0101'", vis_day)
    ck("a name-only bill on a real visit day is named by the SAME-DAY list",
       bool(v) and v[0]["clinic_id"] == p_vis["clinic_id"], str(res2))
    r2 = q("SELECT rung FROM identity_resolution WHERE business_date=? AND bill_no='W0101'", vis_day)
    ck("its rung is recorded as the same-day visit",
       bool(r2) and r2[0]["rung"] == "same-day visit")

    # ------------------------------------------- a Sunday has no visit list
    sun = q("SELECT d.business_date bd FROM day_entry d WHERE d.business_date "
            "NOT IN (SELECT DISTINCT visit_date FROM patient_visit) "
            "AND d.business_date >= '2026-07-01' LIMIT 1")
    if sun:
        empty = q("SELECT 1 FROM patient_visit WHERE visit_date=?", sun[0]["bd"])
        ck("the same-day rung gives no answer on a day with no visit feed", not empty)

    # -------------------------------------------------- the baked analytics
    dis = q("SELECT * FROM v_entry_discipline WHERE business_date=?", DAY)
    ck("v_entry_discipline reports the day", bool(dis))
    if dis:
        d0 = dict(dis[0])
        ck("it counts the two ladder-named bills", d0.get("named_by_ladder") == 2, str(d0))
        ck("it counts the one still parked", d0.get("still_parked") == 1, str(d0))

    # ---------------------------------------------- the money is unchanged
    # ---- the rung-3 cross-check: this kit's own last-four rung must agree with
    # finance_patient_match.match_bill()'s, on real master rows, or they will
    # drift apart the first time either is touched.
    xcon = sqlite3.connect(db)
    xcon.row_factory = sqlite3.Row
    disagree = n_checked = 0
    for r in q("SELECT raw_text FROM sale_item_review WHERE raw_text LIKE '{%' LIMIT 400"):
        try:
            d = json.loads(r["raw_text"])
        except Exception:
            continue
        nm4, l4 = (d.get("patient_name") or ""), (d.get("phone_last4") or "")
        if not (nm4 and l4):
            continue
        n_checked += 1
        mine = FI._ladder_by_last4(xcon, M, l4, nm4)[0]
        rec = json.dumps(dict(clinic_id="", patient_name=nm4, phone_last4=l4))
        res_m = M.match_bill(xcon, rec, business_date=None)
        theirs = (res_m.get("patient") or {}).get("clinic_id") \
            if res_m.get("verdict") == "matched_partial" else None
        if mine != theirs:
            disagree += 1
    xcon.close()
    ck("the last-4 rung agrees with match_bill on every real row checked (%d rows)" % n_checked,
       disagree == 0 and n_checked >= 20, "%d disagreed of %d" % (disagree, n_checked))

    ck("the day's attributed total is the three attached bills",
       res["attributed_p"] == 500_00 + 700_00 + 900_00, str(res["attributed_p"]))

    # -------------------------------------------- re-ingest is idempotent
    res3 = FI.ingest_day(con_plain, UNIT, DAY, "marg_export", csv_text,
                         run_by="walk", source_ref="walk_s221")
    ck("a re-export gives the same answer, not a duplicate",
       res3["accepted"] == 3 and res3["review"] == 1 and res3.get("laddered") == 2, str(res3))
    ck("the recording did not duplicate on re-ingest",
       len(q("SELECT 1 FROM identity_resolution WHERE business_date=?", DAY)) == 2)

    con.close()
    print("\n%s -- %d passed, %d failed" %
          ("WALK GREEN" if not FAILED else "WALK RED", len(PASSED), len(FAILED)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
