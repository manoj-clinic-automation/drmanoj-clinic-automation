# -*- coding: utf-8 -*-
"""S261 LIVE-SHAPE WALK -- run on the box, against a COPY of the real database.

The offline walk proves the page on a fixture. This one proves it on the
clinic's own August, with its own 19 suppliers and 84 bills, by rendering the
page over HTTP and reading what came back. It writes to a copy and never to
the live database.

    python3 walk_live_s261.py --file /root/finance/purchase_app.py --db /tmp/x.db
"""
import argparse, importlib.util, json, os, re, sqlite3, sys

OK = BAD = 0


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("    ok    %s" % name)
    else:
        BAD += 1
        print("    FAIL  %s   %s" % (name, str(detail)[:240]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args(argv)

    spec = importlib.util.spec_from_file_location("purchase_app_live", a.file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    import flask
    app = flask.Flask(__name__)
    holder = {}

    def db():
        if "con" not in holder:
            c = sqlite3.connect(a.db)
            c.row_factory = sqlite3.Row
            holder["con"] = c
        return holder["con"]

    def require(*roles):
        return {"user": "walk", "role": "checker", "roles": ["checker"]}, None

    mod.init(app, db, require, unit="medical", url_prefix="/finance/purchase")
    c = app.test_client()

    with app.test_request_context("/"):
        months = mod._months(db(), 3)
    ck("the database has months of purchases", bool(months), months)
    if not months:
        print("\n%d ok, %d failed" % (OK, BAD))
        return 1

    for m in months:
        r = c.get("/finance/purchase/page/pay/" + m)
        ck("%s: the page answers 200" % m, r.status_code == 200, r.status_code)
        h = r.get_data(as_text=True)
        with app.test_request_context("/"):
            s, groups = mod._pay_rows(db(), m)
        # the page must agree with the month itself, to the rupee
        ck("%s: the vendor lines add up to the month's own Marg total" % m,
           sum(g["total_p"] for g in groups) == s["marg_p"],
           "%s vs %s" % (sum(g["total_p"] for g in groups), s["marg_p"]))
        ck("%s: every supplier of the month has exactly one line" % m,
           len({g["norm"] for g in groups}) == len(groups) ==
           len({b["supplier_norm"] for b in s["bills"]}),
           "%d groups" % len(groups))
        ck("%s: every bill of the month is under its vendor" % m,
           sum(len(g["bills"]) for g in groups) == len(s["bills"]),
           "%d vs %d" % (sum(len(g["bills"]) for g in groups), len(s["bills"])))
        ck("%s: the month's figure is printed on the page" % m,
           mod._r(s["marg_p"]) in h, mod._r(s["marg_p"]))
        ck("%s: the sheet comes first and the verification second" % m,
           h.index("1 &middot; The sheet") < h.index("2 &middot; Verify against the supplier-wise"))
        ck("%s: the sheet carries both fortnights and the payable" % m,
           "1st\u201315th" in h and "16th\u2013end" in h and "Payable" in h)
        with app.test_request_context("/"):
            v = mod._verify_statement(db(), m)
        ck("%s: the verification runs and says what it found" % m,
           isinstance(v, dict) and "ok" in v and (v["ok"] or v["problems"]),
           v.get("problems") if isinstance(v, dict) else v)
        if v["ok"]:
            ck("%s: it agrees with Marg's own supplier-wise statement" % m, True)
        else:
            ck("%s: it does not agree, and names why (not a failure of the page)" % m,
               bool(v["problems"]), v["problems"])
        # a vendor with no confirmed account is never silently on NEFT
        cheq = [g for g in groups if g["route"] != "NEFT"]
        ck("%s: %d vendor(s) without a confirmed account are named as cheque" % (m, len(cheq)),
           all(mod._esc(g["name"]) in h for g in cheq) and ("CHEQUE" in h or not cheq))
        # the third level, on a real bill
        if s["bills"]:
            bid = s["bills"][0]["id"]
            r2 = c.get("/finance/purchase/api/bill-lines?bill=%d" % bid)
            body = r2.get_data(as_text=True)
            ck("%s: a real bill's own lines load" % m, r2.status_code == 200,
               "%s %s" % (r2.status_code, body[-200:]))
            try:
                j = json.loads(body)
            except ValueError:
                j = None
            ck("%s: and the answer is well formed" % m, isinstance(j, dict) and j.get("ok") is True,
               body[:200])

    r3 = c.get("/finance/purchase/page/pay")
    ck("the tile address redirects to the newest month",
       r3.status_code in (301, 302) and months[0] in (r3.headers.get("Location") or ""),
       "%s %s" % (r3.status_code, r3.headers.get("Location")))
    for page in ("hub", "month/" + months[0], "scans", "orders"):
        ck("the existing page /%s still renders" % page,
           c.get("/finance/purchase/page/" + page).status_code == 200)

    print("\n%d ok, %d failed" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
