#!/usr/bin/env python3
"""
REHEARSAL_dailygaps.py -- the walk for the daily gap report.

Seeds a throwaway database with a real day's worth of shapes and checks that the
report says the true thing about each. Writes nothing outside a temp folder.
"""
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import finance_daily_gaps as G                                # noqa: E402

SALT = "walk-salt"
ENV = {"PATIENT_FP_SALT": SALT}
import finance_patient_match as M                             # noqa: E402
OK = BAD = 0


def check(name, cond, detail=""):
    global OK, BAD
    if cond: OK += 1
    else: BAD += 1
    print(("  ok   " if cond else "  FAIL ") + name + (("   " + detail) if detail else ""))


SCHEMA = """
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL UNIQUE,
    name TEXT, phone_last4 TEXT, first_seen TEXT, merged_into INTEGER, note TEXT,
    mobile_fp TEXT, patient_uid TEXT, mobile TEXT, last_seen TEXT,
    mobile_dup_count INTEGER,
    admin_cc_p INTEGER, admin_pd_pct INTEGER, admin_bid_pct INTEGER,
    is_vip INTEGER, concession_scheme TEXT);
CREATE TABLE patient_visit (visit_id TEXT PRIMARY KEY, visit_date TEXT NOT NULL,
    clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure TEXT);
CREATE TABLE patient_id_collision (clinic_id TEXT, kept_uid TEXT, other_uid TEXT,
    other_name TEXT, first_noted TEXT, PRIMARY KEY (clinic_id, other_uid));
CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT NOT NULL,
    business_date TEXT NOT NULL);
CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL,
    unit TEXT, patient_ref_id INTEGER, service TEXT, description TEXT,
    amount_p INTEGER NOT NULL CHECK (amount_p >= 0), gross_p INTEGER,
    disc_p INTEGER, mode TEXT, source TEXT, source_ref TEXT, confidence REAL);
CREATE TABLE upi_statement (id INTEGER PRIMARY KEY, merchant_id TEXT,
    unit TEXT, statement_date TEXT, parsed_total_p INTEGER, txn_count INTEGER);
CREATE TABLE day_line (id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL,
    service TEXT NOT NULL, mode TEXT NOT NULL, amount_p INTEGER NOT NULL);
"""

DAY = "2026-08-26"
OLD = "2026-05-01"


def main():
    tmp = tempfile.mkdtemp(prefix="gapwalk_")
    db = os.path.join(tmp, "finance.db")
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)

    fp_solo = M.fingerprint("9999999999", SALT)
    fp_fam = M.fingerprint("8888888888", SALT)
    con.executemany("INSERT INTO patient_ref (clinic_id,name,mobile_fp) VALUES (?,?,?)",
                    [("4471", "RAMESH KUMAR", fp_solo),
                     ("4472", "SITA DEVI", fp_fam),
                     ("4473", "GEETA DEVI", fp_fam)])
    con.execute("INSERT INTO day_entry (id,unit,business_date) VALUES (1,'medical',?)", (DAY,))
    con.execute("INSERT INTO day_entry (id,unit,business_date) VALUES (2,'medical',?)", (OLD,))
    bills = [
        # complete -> matched, must NOT appear as a gap
        (1, "9999999999 RAMESH KUMAR 4471", 50000, "cash", "A001"),
        # a family mobile, no name -> ambiguous
        (1, "8888888888", 30000, "cash", "A002"),
        # nothing usable -> the counter gap
        (1, "PROSIJER", 20000, "cash", "A003"),
        # a cash bill the bank shortfall could account for
        (1, "9999999999 RAMESH KUMAR 4471", 12500, "cash", "A004"),
    ]
    for de, desc, amt, mode, ref in bills:
        con.execute("INSERT INTO sale_item (day_entry_id,unit,description,amount_p,"
                    "mode,source,source_ref) VALUES (?,'medical',?,?,?,'manual',?)",
                    (de, desc, amt, mode, ref))
    con.execute("INSERT INTO sale_item (day_entry_id,unit,description,amount_p,mode,"
                "source,source_ref) VALUES (2,'medical','PROSIJER',9900,'cash','manual','OLD1')")
    # THE REAL SHAPE OF A LIVE PHARMACY ROW, measured on the box at S211:
    # description EMPTY, patient_ref_id SET at ingest. Three cases.
    con.execute("INSERT INTO patient_ref (clinic_id,name,mobile_fp,patient_uid,mobile) "
                "VALUES ('5001','MASTER PATIENT','fp_zzz','U-REAL','9999999999')")
    con.execute("INSERT INTO patient_ref (clinic_id,name) VALUES ('5002','BILL STUB')")
    # THE SANCTIONED DISCOUNT CASES -- sanctioned 10%: exact, rounding, short,
    # none at all, and over.
    con.execute("INSERT INTO patient_ref (clinic_id,name,patient_uid,admin_pd_pct) "
                "VALUES ('6001','PD PATIENT','U-PD',10)")
    pid = "(SELECT id FROM patient_ref WHERE clinic_id='6001')"
    for ref, gross, disc in (("D001",100000,10000),   # exact 10%
                             ("D002",100000, 9600),   # within Rs 5 -> rounding
                             ("D003",100000, 4000),   # short
                             ("D004",100000,    0),   # none at all
                             ("D005",100000,20000)):  # over
        con.execute("INSERT INTO sale_item (day_entry_id,unit,description,amount_p,"
                    "gross_p,disc_p,mode,source,source_ref,service,patient_ref_id) "
                    "VALUES (1,'medical','',?,?,?,'cash','manual',?,'pharmacy',%s)" % pid,
                    (gross - disc, gross, disc, ref))
    con.execute("INSERT INTO sale_item (day_entry_id,unit,description,amount_p,mode,"
                "source,source_ref,patient_ref_id) VALUES "
                "(1,'medical','',11100,'cash','manual','B001',"
                "(SELECT id FROM patient_ref WHERE clinic_id='5001'))")
    import json as _j
    _rec = _j.dumps({"bill_date":"2026-08-26","bill_no":"A00742","clinic_id":"",
                     "patient_name":"ZZQX UNKNOWNPERSON","phone_last4":"4321",
                     "description":"","amount":"222.00","mode":"cash"})
    con.execute("INSERT INTO sale_item (day_entry_id,unit,description,amount_p,mode,"
                "source,source_ref,patient_ref_id) VALUES "
                "(1,'medical',?,22200,'cash','manual','S186-F104-394',"
                "(SELECT id FROM patient_ref WHERE clinic_id='5002'))", (_rec,))
    con.execute("INSERT INTO sale_item (day_entry_id,unit,description,amount_p,mode,"
                "source,source_ref,patient_ref_id) VALUES "
                "(1,'medical','',33300,'cash','manual','B003',NULL)")
    con.execute("INSERT INTO upi_statement (merchant_id,unit,statement_date,"
                "parsed_total_p,txn_count) VALUES ('M1','medical',?,12500,1)", (DAY,))
    # WHAT DARPAN DECLARED for the day -- this, not sale_item.mode, is what the
    # bank is judged against. Here he declared 10,000 paise of UPI and the bank
    # settled 12,500, so the day is short by 2,500.
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) "
                "VALUES (1,'pharmacy_sale','upi',10000)")
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) "
                "VALUES (1,'pharmacy_sale','cash',40000)")
    con.commit()

    punches = os.path.join(tmp, "punches.csv")
    staff = os.path.join(tmp, "staff_master.csv")
    open(staff, "w", encoding="utf-8").write("user_id,name\n7,Darpan\n9,Vinay\n")
    open(punches, "w", encoding="utf-8").write(
        "user_id,datetime\n7,%s 09:12:00\n" % DAY)

    r = G.day_report(con, DAY, "medical", ENV, punches, staff)

    check("the day counted every bill", r["totals"]["bills"] == 12,
          str(r["totals"]))
    byref = {g["bill_no"]: g["verdict"] for g in r["identity_gaps"]}
    check("a bill linked at ingest to a MASTER patient is matched, not a gap",
          "B001" not in byref)
    check("a bill linked to a stub the bill itself created IS the counter gap",
          byref.get("A00742") == "unmatched")
    # THE OWNER'S CORRECTION: source_ref held S186-F104-394; the real bill number
    # is in the structured record and that is what a row must show.
    row742 = [g for g in r["identity_gaps"] if g["bill_no"] == "A00742"]
    check("the row shows the REAL bill number, not the ingest reference",
          len(row742) == 1 and not any(g["bill_no"] == "S186-F104-394"
                                       for g in r["identity_gaps"]))
    check("  ...and carries the patient name beside it",
          row742 and row742[0]["name"] == "ZZQX UNKNOWNPERSON")
    check("  ...and a number that can be dialled, or a masked one if not stored",
          row742 and row742[0]["mobile"] == "xxxxxx4321")
    check("a bill never linked to anyone is the counter gap too",
          byref.get("B003") == "unmatched")
    check("  ...and each says WHY, in its own words",
          all(any("master" in str(st.get("detail","")).lower()
                  or "never linked" in str(st.get("detail","")).lower()
                  for st in g["steps"])
              for g in r["identity_gaps"] if g["bill_no"] in ("B002","B003")))
    check("matched bills are NOT listed as gaps",
          all(g["verdict"] != "matched_clinic_id" for g in r["identity_gaps"])
          and len(r["identity_gaps"]) == 4)
    kinds = sorted(g["verdict"] for g in r["identity_gaps"])
    # one ambiguous (the family mobile) and three counter gaps: the junk bill,
    # the bill linked to a stub, and the bill never linked at all.
    check("the family mobile is AMBIGUOUS and the rest are counter gaps",
          kinds == ["ambiguous", "unmatched", "unmatched", "unmatched"], str(kinds))
    check("a gap row carries its working, step by step",
          all(len(g["steps"]) >= 2 for g in r["identity_gaps"]))
    check("an ambiguous row shows the candidates rather than picking",
          any(g["verdict"] == "ambiguous" and len(g["candidates"]) == 2
              for g in r["identity_gaps"]))

    # attribution
    check("Darpan punched -> Darpan, decided by rule",
          r["counter"]["seller"] == "darpan" and r["counter"]["decided_by"] == "rule")
    open(punches, "w", encoding="utf-8").write("user_id,datetime\n9,%s 09:12:00\n" % DAY)
    r2 = G.day_report(con, DAY, "medical", ENV, punches, staff)
    check("no punch for Darpan -> Vinay, and it SAYS it is a rule",
          r2["counter"]["seller"] == "vinay" and r2["counter"]["decided_by"] == "rule")
    r3 = G.day_report(con, DAY, "medical", ENV, punches, staff,
                      override_seller="darpan")
    check("the owner's selector overrides the rule and is recorded as his",
          r3["counter"]["seller"] == "darpan" and r3["counter"]["decided_by"] == "owner")
    r4 = G.day_report(con, DAY, "medical", ENV, os.path.join(tmp, "nope.csv"), staff)
    check("unreadable punches -> attribution PENDING, never a guess",
          r4["counter"]["seller"] is None and r4["counter"]["decided_by"] == "unknown")

    drows, dtal = r["discounts"]
    byb = {x["bill"]: x for x in drows}
    check("a discount matching the sanction exactly is not a breach",
          byb["D001"]["verdict"] == "matches" and not byb["D001"]["rounding_exempt"])
    check("a discount inside the rounding tolerance is EXEMPT but RECORDED",
          byb["D002"]["verdict"] == "matches" and byb["D002"]["rounding_exempt"]
          and byb["D002"]["diff_p"] == -400)
    check("a short discount is named short, with the shortfall",
          byb["D003"]["verdict"] == "short" and byb["D003"]["diff_p"] == -6000)
    check("no discount at all is its own verdict, not lumped with short",
          byb["D004"]["verdict"] == "none given")
    check("MORE than sanctioned is its own bucket, and carries what was given",
          byb["D005"]["verdict"] == "over" and byb["D005"]["given_pct"] == 20.0)
    check("  ...and the tally counts each kind",
          dtal.get("matches") == 2 and dtal.get("short") == 1
          and dtal.get("none given") == 1 and dtal.get("over") == 1)

    # THE CORRECTED PAYMENT CHECK -- declared, not sale_item.mode
    dv = r["declared"]
    check("the bank is judged against what DARPAN DECLARED, not sale_item.mode",
          dv["declared_digital_p"] == 10000 and dv["bank_settled_p"] == 12500
          and dv["difference_p"] == 2500, str(dv["note"]))
    check("  ...and the declared cash is carried alongside it",
          dv["declared_cash_p"] == 40000)
    check("  ...and sale_item.mode is kept only as a SECONDARY signal",
          r["payment"]["modes"] and r["payment"]["modes"] != dv)

    # payment
    p = r["payment"]
    check("the bank is compared against what the bills declare",
          p["bank_settled_p"] == 12500 and p["entered_digital_p"] == 0
          and p["difference_p"] == 12500)
    check("cash bills that could account for the difference are SUGGESTED",
          any(c["amount_p"] == 12500 for c in p["could_account_for_it"]))
    check("  ...and nothing was changed by suggesting it",
          con.execute("SELECT COUNT(*) c FROM sale_item WHERE mode='cash'").fetchone()["c"] == 13)

    # the backfill boundary
    r5 = G.day_report(con, OLD, "medical", ENV, punches, staff)
    check("a day before the three-identifier era reports NO gap, and says why",
          r5["identity_gaps"] == [] and r5["before_identity_era"])

    # read-only
    before = con.execute("SELECT COUNT(*) c FROM sale_item").fetchone()["c"]
    G.day_report(con, DAY, "medical", ENV, punches, staff)
    check("the whole report is READ-ONLY",
          con.execute("SELECT COUNT(*) c FROM sale_item").fetchone()["c"] == before)
    con.close()

    print("\nREHEARSAL: %d/%d %s" % (OK, OK + BAD, "ALL PASS" if BAD == 0 else "-- FAILED"))
    return 0 if BAD == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
