#!/usr/bin/env python3
"""selftest for S214_RETURNS_DESK -- invariants on a SYNTHETIC db + a real
Flask app, driving the real routes with a fake require(). No frozen real
snapshot (the S212 rule)."""
import datetime
import json
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import returns_desk as RD                                     # noqa: E402
from flask import Flask                                       # noqa: E402

PASS = FAIL = 0


def check(name, ok):
    global PASS, FAIL
    print("%s  %s" % ("PASS" if ok else "FAIL", name))
    PASS, FAIL = PASS + ok, FAIL + (not ok)


TODAY = datetime.date.today()
OLD = (TODAY - datetime.timedelta(days=90)).isoformat()
RECENT = (TODAY - datetime.timedelta(days=5)).isoformat()
GOOD_EXP = "%04d-%02d" % (TODAY.year + 1, TODAY.month)
DEAD_EXP = "2024-01"


def build_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT,
      phone_last4 TEXT, first_seen TEXT, merged_into INTEGER, note TEXT);
    CREATE TABLE sale_item (id INTEGER PRIMARY KEY, patient_ref_id INT,
      source_ref TEXT, amount_p INT, mode TEXT, gross_p INT, disc_p INT);
    CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, business_date TEXT,
      bill_no TEXT, is_return INT DEFAULT 0, seq INT, item_name TEXT,
      item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INT, expiry_ym TEXT,
      batch TEXT);
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
    CREATE TABLE unit_role (id INTEGER PRIMARY KEY, unit TEXT, username TEXT,
      role TEXT NOT NULL CHECK (role IN ('maker','checker','viewer')),
      active INT, note TEXT);
    """)
    con.execute("INSERT INTO patient_ref VALUES (1,'C-101','RAM TEST','1234',NULL,NULL,NULL)")
    con.execute("INSERT INTO sale_item (patient_ref_id,source_ref,amount_p,mode,gross_p,disc_p) "
                "VALUES (1,'B001',45000,'cash',50000,5000)")
    con.execute("INSERT INTO sale_item (patient_ref_id,source_ref,amount_p,mode) "
                "VALUES (1,'B000',30000,'cash')")
    con.execute("INSERT INTO sale_item (patient_ref_id,source_ref,amount_p,mode) "
                "VALUES (1,'CN001',-30000,'cash')")
    rows = [
        (RECENT, "B001", 0, 1, "GOOD TAB", "good", "1*10", "0:2", 10000, GOOD_EXP),
        (RECENT, "B001", 0, 2, "DEAD OINT", "dead", "", "1.0", 5000, DEAD_EXP),
        (OLD,    "B000", 0, 1, "OLD SYRUP", "old", "", "1.0", 30000, GOOD_EXP),
        (RECENT, "CN001", 1, 1, "OLD SYRUP", "old", "", "1.0", 30000, GOOD_EXP),
    ]
    con.executemany("INSERT INTO sale_line_item (business_date,bill_no,is_return,"
                    "seq,item_name,item_key,pack,qty_raw,amount_p,expiry_ym) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


def make_app(db_path, user="alisha", roles=("viewer",)):
    app = Flask(__name__)

    def db():
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        return con

    def require(*want, unit="medical"):
        if set(roles) & set(want):
            return {"user": user, "roles": sorted(roles)}, None
        from flask import jsonify
        return None, (jsonify(ok=False, error="not_permitted"), 403)

    RD.init(app, db, require, unit="medical")
    return app


def main():
    tmp = tempfile.mkdtemp(prefix="desk_selftest_")
    dbp = os.path.join(tmp, "t.db")
    build_db(dbp)
    app = make_app(dbp)
    c = app.test_client()

    r = c.get("/finance/returns/desk/api/search?q=RAM")
    check("search finds the patient by name", r.get_json()["patients"][0]["id"] == 1)
    r = c.get("/finance/returns/desk/api/search?q=1234")
    check("search finds by phone last-4", len(r.get_json()["patients"]) == 1)

    r = c.get("/finance/returns/desk/api/history?pid=1")
    j = r.get_json()
    check("history returns EVERY bill, not the last one", len(j["bills"]) == 2)
    b001 = [b for b in j["bills"] if b["bill_no"] == "B001"][0]
    dead = [l for l in b001["lines"] if l["item_key"] == "dead"][0]
    check("an expired sold line is marked expired in history", dead["expired"] is True)

    r = c.get("/finance/returns/desk/api/items?pid=1")
    j = r.get_json()
    keys = {i["item_key"]: i for i in j["items"]}
    check("items API aggregates one row per medicine", len(j["items"]) == 3)
    check("bought units converted through the pack (0:2 of 1*10 = 2)",
          keys["good"]["bought_units"] == 2)
    check("items carry a per-unit price guess", keys["good"]["unit_p"] > 0)
    check("net unit price honours the bill's own discount (10% off 1000 -> 900)",
          keys["good"]["unit_net_p"] == 900 and keys["good"]["discounted"])
    check("a Marg credit note reduces the returnable cap (bought 1 - CN 1 = 0)",
          keys["old"]["cap_units"] == 0 and keys["old"]["returned_units"] == 1)
    check("previous returns listed with source and date",
          keys["old"]["returns"] and keys["old"]["returns"][0]["src"] == "CN")
    check("an untouched item's cap equals its bought units",
          keys["good"]["cap_units"] == keys["good"]["bought_units"])
    check("items carry their bills inline",
          keys["good"]["bills"] and keys["good"]["bills"][0]["bill_no"] == "B001")
    check("bill entries carry purchased qty and the discount given",
          keys["good"]["bills"][0]["units"] == 2
          and keys["good"]["bills"][0]["disc_pct"] == 10)
    r = c.get("/finance/returns/desk/api/catalog?q=syr")
    cat = r.get_json()["items"]
    check("catalog type-ahead finds shop items by fragment, priced",
          any(i["item_key"] == "old" and i["unit_p"] > 0 for i in cat))

    # v2 slip: ITEM-level lines; the SERVER allocates bills
    lines = [
        dict(item_key="good", item_name="GOOD TAB", units=1, unit_p=1000,
             amount_p=1000, condition="sealed"),
        dict(item_key="dead", item_name="DEAD OINT", units=1, unit_p=5000,
             amount_p=5000, condition="sealed"),
        dict(item_key="old", item_name="OLD SYRUP", units=1, unit_p=30000,
             amount_p=30000, condition="sealed"),
        dict(item_key="good", item_name="GOOD TAB", units=1, unit_p=1000,
             amount_p=1000, condition="opened"),
    ]
    r = c.post("/finance/returns/desk/api/slip", json=dict(
        patient_ref_id=1, patient_label="RAM TEST", lines=lines,
        closure="nothing"))
    j = r.get_json()
    check("slip saves", j.get("ok") is True)
    v = {(l["item_name"], l["condition"]): l for l in j["lines"]}
    check("clean recent item is GREEN", v[("GOOD TAB", "sealed")]["verdict"] == "GREEN")
    check("the SERVER found its bill", v[("GOOD TAB", "sealed")]["sale_bill_no"] == "B001")
    check("expired item is RED", v[("DEAD OINT", "sealed")]["verdict"] == "RED")
    check("opened item is RED", v[("GOOD TAB", "opened")]["verdict"] == "RED")
    check(">60-day return is YELLOW, accepted",
          v[("OLD SYRUP", "sealed")]["verdict"] == "YELLOW"
          and v[("OLD SYRUP", "sealed")]["accepted"] == 1)
    check("refund counts ONLY accepted lines (1000+30000)", j["refund_p"] == 31000)
    check("late flag on the visit", "late_over_2_months" in j["flags"])
    check("slip number minted", j["slip_no"].startswith("R-"))
    r = c.post("/finance/returns/desk/api/slip", json=dict(
        patient_ref_id=1, patient_label="RAM TEST",
        lines=[dict(item_key="good", item_name="GOOD TAB", units=50,
                    unit_p=1000, condition="sealed")],
        closure="nothing"))
    j = r.get_json()
    check("returning more than ever bought flags qty_over_bought, accepted",
          j["lines"][0]["verdict"] == "YELLOW"
          and "qty_over_bought" in j["lines"][0]["reasons"])

    r = c.post("/finance/returns/desk/api/slip", json=dict(
        lines=[dict(item_name="X", units=1, amount_p=1000, condition="sealed")]))
    first_slip = r.get_json()["slip_no"]
    check("slip saves with NO money choice (v8: counter settles)",
          r.get_json()["ok"] is True)
    r = c.post("/finance/returns/desk/api/slip/settle",
               json=dict(slip_no=first_slip, how="cash"))
    check("settle cash without a named payer is refused", r.status_code == 400)
    r = c.post("/finance/returns/desk/api/slip/settle",
               json=dict(slip_no=first_slip, how="cash", cash_paid_by="shivani"))
    check("counter settles cash, payer logged", r.get_json()["ok"] is True)
    r = c.post("/finance/returns/desk/api/slip/settle",
               json=dict(slip_no=first_slip, how="cash", cash_paid_by="x"))
    check("double settlement refused", r.status_code == 400)
    r = c.post("/finance/returns/desk/api/slip/void",
               json=dict(slip_no=first_slip, reason="matra_galat"))
    check("staff cannot Cancel a SETTLED slip (owner's rule)",
          r.status_code == 403)

    r = c.post("/finance/returns/desk/api/slip", json=dict(
        patient_ref_id=1, patient_label="RAM TEST",
        lines=[dict(item_name="Y", units=1, amount_p=1000, condition="sealed")],
        closure="nothing"))
    check("bill-not-traced line is YELLOW and accepted",
          r.get_json()["lines"][0]["verdict"] == "YELLOW")
    r = c.post("/finance/returns/desk/api/slip", json=dict(
        patient_ref_id=1, patient_label="RAM TEST",
        lines=[dict(item_name="Z", units=1, amount_p=1000, condition="sealed")],
        closure="nothing"))
    check("3rd visit in 30 days flags frequent_returner",
          "frequent_returner" in r.get_json()["flags"])
    r = c.post("/finance/returns/desk/api/slip", json=dict(
        patient_ref_id=1, patient_label="RAM TEST",
        lines=[dict(item_name="BIG", units=1, amount_p=250000, condition="sealed")],
        closure="nothing"))
    check("Rs 2,500 refund flags big_refund, never blocks",
          r.get_json()["ok"] and "big_refund" in r.get_json()["flags"])

    r = c.get("/finance/returns/desk/api/slips")
    j = r.get_json()
    check("the day's slips list back (6 saved)", len(j["slips"]) == 6)
    check("every slip is filed open for the CN matcher",
          all(s["match_state"] == "open" for s in j["slips"]))
    con = sqlite3.connect(dbp)
    nred = con.execute("SELECT COUNT(*) FROM return_line WHERE accepted=0").fetchone()[0]
    check("refused lines are FILED, not vanished", nred == 2)

    import seed_desk_roles as SEED
    rc = SEED.main(dbp)
    con = sqlite3.connect(dbp)
    n = con.execute("SELECT COUNT(*) FROM unit_role WHERE role='viewer' "
                    "AND active=1").fetchone()[0]
    check("seeder writes schema-legal viewer rows (the CHECK lesson)",
          rc == 0 and n == 3)
    rc2 = SEED.main(dbp)
    n2 = con.execute("SELECT COUNT(*) FROM unit_role").fetchone()[0]
    check("seeder is idempotent", rc2 == 0 and n2 == n)

    r = c.post("/finance/returns/desk/api/slip", json=dict(
        patient_ref_id=1, patient_label="RAM TEST",
        lines=[dict(item_name="V", units=1, amount_p=500, condition="sealed")]))
    vslip = r.get_json()["slip_no"]
    r = c.post("/finance/returns/desk/api/slip/void", json=dict(slip_no=vslip))
    check("Cancel without a reason from the list is refused", r.status_code == 400)
    r = c.post("/finance/returns/desk/api/slip/void",
               json=dict(slip_no=vslip, reason="irada_badla"))
    check("same-day un-settled slip Cancels", r.get_json()["ok"] is True)
    r = c.post("/finance/returns/desk/api/slip/void",
               json=dict(slip_no=vslip, reason="anya"))
    check("double Cancel refused", r.status_code == 400)
    r = c.post("/finance/returns/desk/api/slip/settle",
               json=dict(slip_no=vslip, how="cash", cash_paid_by="a"))
    check("a Cancelled slip cannot be settled", r.status_code == 400)
    r = c.get("/finance/returns/desk/api/slips?open=1")
    check("Cancelled slips leave the CN-pending list",
          all(x["slip_no"] != vslip for x in r.get_json()["slips"]))

    j = c.get("/finance/returns/desk/api/items?pid=1").get_json()
    good_now = {i["item_key"]: i for i in j["items"]}["good"]
    check("accepted desk slips reduce the cap on the next visit",
          good_now["cap_units"] < good_now["bought_units"])

    app2 = make_app(dbp, user="lab_person", roles=("labmaker",))
    r = app2.test_client().get("/finance/returns/desk/api/slips")
    check("a login without the desk roles is refused", r.status_code == 403)

    print("\n%d passed, %d failed" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
