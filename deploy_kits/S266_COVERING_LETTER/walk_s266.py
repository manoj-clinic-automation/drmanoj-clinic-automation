# -*- coding: utf-8 -*-
"""S266 LIVE-SHAPE WALK -- the covering letter, held to the letter that has
always been sent, and to the advice it must agree with.

    python3 walk_s266.py --file <patched> --before <backup> --db <copy.db>
"""
import argparse
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

OK = BAD = 0
MUST = [
    "The Manager", "YES Bank Limited", "Rampur Garden,", "Bareilly.",
    "Sub : Authorization to execute Multiple NEFT/RTGS transactions.",
    "towards NEFT/RTGS request",
    "Please process the request as per the enclosed/attached annexure.",
    "For Authorized Signatory:-", "For SANJEEVNI MEDICOS",
]


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("    ok    %s" % name)
    else:
        BAD += 1
        print("    FAIL  %s   %s" % (name, str(detail)[:260]))


def load(path, dbpath, name):
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    import flask
    app = flask.Flask(name)
    holder = {}

    def db():
        if "con" not in holder:
            c = sqlite3.connect(dbpath)
            c.row_factory = sqlite3.Row
            holder["con"] = c
        return holder["con"]

    def require(*roles):
        return {"user": "walk", "role": "checker", "roles": ["checker"]}, None

    mod.init(app, db, require, unit="medical", url_prefix="/finance/purchase")
    return mod, app, db


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args(argv)
    tmp = tempfile.mkdtemp(prefix="s266_")
    db_b, db_a = os.path.join(tmp, "b.db"), os.path.join(tmp, "a.db")
    shutil.copy(a.db, db_b)
    shutil.copy(a.db, db_a)
    old, app0, dbf0 = load(a.before, db_b, "pa_before")
    new, app1, dbf1 = load(a.file, db_a, "pa_after")
    c0, c1 = app0.test_client(), app1.test_client()
    with app1.test_request_context("/"):
        months = new._months(dbf1(), 6)
    ck("the database has months of purchases", bool(months), months)
    if not months:
        print("\n%d ok, %d failed" % (OK, BAD))
        return 1
    m = months[0]

    ck("BEFORE: there was no covering letter anywhere",
       "letter_s266" not in c0.get("/finance/purchase/page/pay/" + m).get_data(as_text=True)
       and c0.get("/finance/purchase/page/pay/%s/letter" % m).status_code == 404)

    h = c1.get("/finance/purchase/page/pay/" + m).get_data(as_text=True)
    ck("the letter is previewed on the sheet", 'id="letter_s266"' in h)
    r = c1.get("/finance/purchase/page/pay/%s/letter" % m)
    ck("the letter has a page of its own", r.status_code == 200, r.status_code)
    lp = r.get_data(as_text=True)

    # ---- word for word ------------------------------------------------------
    for line in MUST:
        ck("  the letter still says: %s" % line[:52], line in lp)
    ck("the two typos in the original are gone",
       "SEPTEMBAR" not in lp and "transactions.S<" not in lp and "transactions.S " not in lp)

    # ---- the amount is the advice's, never retyped --------------------------
    with app1.test_request_context("/"):
        rows, total, missing, paise = new._advice_rows_s265(dbf1(), m)
    ck("the amount is the advice's own total, to the rupee",
       ("Rs. %d/" % total) in lp, total)
    ck("and the same figure stands on the sheet's preview", ("Rs. %d/" % total) in h)
    ck("the amount is written the bank's way -- plain digits, no separators",
       ("Rs. %d/" % total) in lp and ("Rs. {:,}".format(total)) not in lp,
       "{:,}".format(total))
    ck("and the advice's own column is plain too, as the July file is",
       all((">%d<" % r["rupees"]) in h for r in rows[:4]) and
       not any((">{:,}<".format(r["rupees"])) in h for r in rows if r["rupees"] >= 1000),
       [r["rupees"] for r in rows[:4]])

    # ---- the three things that are filled in, not typed ---------------------
    with app1.test_request_context("/"):
        date_text, cheque = new._letter_values_s266(dbf1(), m)
    ck("the date defaults to today in IST, in the letter's own form",
       date_text == new._letter_today_s266() and re.match(r"^[A-Z]+ \d{1,2}, \d{4}$", date_text),
       date_text)
    ck("with no cheque number, a blank line is printed to fill by hand",
       (cheque == "" and "____" in lp) or cheque in lp)

    # ---- typing a cheque number ---------------------------------------------
    rp = c1.post("/finance/purchase/api/pay-letter",
                 data=json.dumps({"month": m, "date_text": "SEPTEMBER 14, 2026",
                                  "cheque_no": "115258"}),
                 content_type="application/json")
    ck("a cheque number can be saved", rp.status_code == 200
       and (json.loads(rp.get_data(as_text=True)).get("ok") is True), rp.get_data(as_text=True)[:120])
    lp2 = c1.get("/finance/purchase/page/pay/%s/letter" % m).get_data(as_text=True)
    ck("and it is on the letter, with the date given", "115258" in lp2
       and "SEPTEMBER 14, 2026" in lp2)
    ck("it is kept, not just shown once",
       sqlite3.connect(db_a).execute(
           "SELECT cheque_no FROM purchase_pay_letter WHERE month=?", (m,)).fetchone()[0] == "115258")
    ck("and the change is in the audit trail",
       sqlite3.connect(db_a).execute(
           "SELECT COUNT(*) FROM purchase_audit WHERE action='pay_letter'").fetchone()[0] >= 1)

    # ---- the amount can never be set from the browser -----------------------
    c1.post("/finance/purchase/api/pay-letter",
            data=json.dumps({"month": m, "amount": 1, "total": 1, "cheque_no": "115258"}),
            content_type="application/json")
    lp3 = c1.get("/finance/purchase/page/pay/%s/letter" % m).get_data(as_text=True)
    ck("the amount cannot be set from the browser -- it is still the advice's",
       ("Rs. %d/" % total) in lp3)

    # ---- printing ------------------------------------------------------------
    ck("the letter's own page prints PORTRAIT", "size:A4 portrait" in lp)
    ck("and the payment sheet still prints the advice LANDSCAPE",
       "size:A4 landscape" in h and "size:A4 portrait" not in h)
    ck("the buttons and the boxes are not printed", "noprint" in lp and ".noprint" in lp)

    # ---- a final month does not move ----------------------------------------
    with app1.test_request_context("/"):
        final = new._month_status(dbf1(), m)["status"] == "final"
    if final:
        rp2 = c1.post("/finance/purchase/api/pay-letter",
                      data=json.dumps({"month": m, "cheque_no": "999"}),
                      content_type="application/json")
        ck("a FINAL month refuses a new cheque number", rp2.status_code != 200
           or json.loads(rp2.get_data(as_text=True)).get("ok") is not True)
    else:
        ck("this month is not final, so the letter is editable (said out loud)", True)

    # ---- nothing else moved --------------------------------------------------
    for page in ("hub", "scans", "orders", "book", "month/" + m):
        r1, r0 = (c1.get("/finance/purchase/page/" + page),
                  c0.get("/finance/purchase/page/" + page))
        ck("/%s is byte-identical to before" % page,
           r1.status_code == 200 and r1.get_data() == r0.get_data(), r1.status_code)
    h0 = c0.get("/finance/purchase/page/pay/" + m).get_data(as_text=True)

    def advice(x):
        i = x.index('id="advice_s265"')
        return x[i:x.index("</table>", i)]
    plain = re.sub(r"(?<=\d),(?=\d\d\d)", "", advice(h0))
    ck("the advice block is unchanged apart from the separators coming out",
       advice(h) == plain,
       [i for i, (x, y) in enumerate(zip(advice(h), plain)) if x != y][:1])
    ck("and that really was the only change -- the before block HAD separators",
       advice(h0) != plain)

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d ok, %d failed" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
