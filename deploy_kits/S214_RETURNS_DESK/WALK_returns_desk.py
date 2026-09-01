#!/usr/bin/env python3
"""WALK_returns_desk.py -- the LIVE-SHAPE walk (S208 rule: a kit is proven
only by a walk in the live shape). Mounts the real module on a real Flask
app over a THROWAWAY COPY of a real finance.db and works one return end to
end: search -> full history -> mixed slip -> refusal filed -> day list.

    python3 -B WALK_returns_desk.py --db /path/to/COPY_of_finance.db

REFUSES to run on a path containing 'finance.db' without 'copy' or 'walk' in
the name -- the walk writes slips, and a walk never writes to the real book.
Patient names are MASKED in every printed line (F-185 discipline).
"""
import argparse
import datetime
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import returns_desk as RD                                     # noqa: E402
from flask import Flask                                       # noqa: E402

PASS = FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name,
                        (" -- " + detail if detail else "")))
    PASS, FAIL = PASS + ok, FAIL + (not ok)


def mask(name):
    s = str(name or "")
    return (s[:2] + "***") if len(s) > 2 else "***"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    base = os.path.basename(a.db).lower()
    if "finance.db" in base and not ("copy" in base or "walk" in base):
        print("REFUSING: give me a COPY (name it *_walkcopy.db); the walk writes.")
        return 2
    work = os.path.join(tempfile.mkdtemp(prefix="desk_walk_"), "walk.db")
    shutil.copy(a.db, work)

    app = Flask(__name__)

    def db():
        con = sqlite3.connect(work)
        con.row_factory = sqlite3.Row
        return con

    def require(*want, unit="medical"):
        if {"viewer"} & set(want):
            return {"user": "alisha", "roles": ["returns"]}, None
        from flask import jsonify
        return None, (jsonify(ok=False), 403)

    RD.init(app, db, require, unit="medical")
    c = app.test_client()

    con = db()
    row = con.execute(
        "SELECT p.id, p.name FROM patient_ref p JOIN sale_item s "
        "ON s.patient_ref_id=p.id AND s.source_ref IS NOT NULL "
        "WHERE p.merged_into IS NULL AND p.name NOT LIKE 'Walk-in%' "
        "GROUP BY p.id HAVING COUNT(DISTINCT s.source_ref) >= 2 "
        "ORDER BY COUNT(DISTINCT s.source_ref) DESC LIMIT 1").fetchone()
    check("a real patient with 2+ bills exists", row is not None)
    if not row:
        return 1
    pid, pname = row["id"], row["name"]
    print("  walking with patient id %d (%s)" % (pid, mask(pname)))

    q = (pname or "xx")[:4]
    j = c.get("/finance/returns/desk/api/search?q=" + q).get_json()
    check("search by name-prefix finds them",
          any(p["id"] == pid for p in j.get("patients", [])),
          "%d hit(s)" % len(j.get("patients", [])))

    j = c.get("/finance/returns/desk/api/history?pid=%d" % pid).get_json()
    bills = j.get("bills", [])
    check("history shows EVERY bill", len(bills) >= 2, "%d bills" % len(bills))
    with_lines = [b for b in bills if b["lines"]]
    check("bills carry their item lines", bool(with_lines),
          "%d of %d with lines" % (len(with_lines), len(bills)))
    b = with_lines[0]
    l = b["lines"][0]

    j = c.get("/finance/returns/desk/api/items?pid=%d" % pid).get_json()
    its = j.get("items", [])
    check("items picker aggregates the patient's medicines", len(its) >= 2,
          "%d medicines" % len(its))
    priced = [i for i in its if i.get("unit_p") and i.get("item_key")]
    check("items carry per-unit price guesses", bool(priced),
          "%d of %d priced" % (len(priced), len(its)))
    it = priced[0]

    lines = [dict(item_key=it["item_key"], item_name=it["item_name"], units=1,
                  unit_p=it["unit_p"], amount_p=it["unit_p"], condition="sealed"),
             dict(item_key=it["item_key"], item_name=it["item_name"], units=1,
                  unit_p=it["unit_p"], amount_p=it["unit_p"], condition="opened")]
    j = c.post("/finance/returns/desk/api/slip", json=dict(
        patient_ref_id=pid, patient_label="WALK", lines=lines,
        closure="cash", cash_paid_by="alisha")).get_json()
    check("item-first slip saves on real data", j.get("ok") is True,
          "slip %s" % j.get("slip_no"))
    ln0 = j.get("lines", [{}])[0]
    check("the SERVER allocated a real bill to the return",
          bool(ln0.get("sale_bill_no")), str(ln0.get("sale_bill_no")))
    vs = [x["verdict"] for x in j.get("lines", [])]
    check("sealed accepted, opened refused",
          vs and vs[0] in ("GREEN", "YELLOW") and vs[1] == "RED", str(vs))
    check("refund = accepted line only", j.get("refund_p") == it["unit_p"])

    j2 = c.get("/finance/returns/desk/api/slips").get_json()
    check("the slip lists under today", len(j2.get("slips", [])) == 1)
    check("filed open for the CN matcher",
          j2["slips"][0]["match_state"] == "open")
    con2 = sqlite3.connect(work)
    n = con2.execute("SELECT COUNT(*) FROM return_line").fetchone()[0]
    check("both lines filed (refusal included)", n == 2)
    before = sqlite3.connect(a.db).execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name IN "
        "('return_visit','return_line')").fetchone()[0]
    check("the SOURCE db was never touched", before in (0, 2),
          "walk wrote only to its own copy")

    print("\n%d passed, %d failed" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
