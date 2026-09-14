# -*- coding: utf-8 -*-
"""S264 LIVE-SHAPE WALK -- run against a COPY of the real database.

The complaint was navigation, so the walk navigates: it opens the sheet the way
the tile does, follows the month strip by the links the page itself prints, and
checks that the audit page and the payment sheet each name the other.

    python3 walk_s264.py --file <patched> --before <backup> --db <copy.db>
"""
import argparse
import importlib.machinery
import importlib.util
import os
import re
import shutil
import sqlite3
import sys
import tempfile

OK = BAD = 0


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

    tmp = tempfile.mkdtemp(prefix="s264_")
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

    # ---- 1. THE COMPLAINT: the tile lands somewhere with no way out ---------
    r = c0.get("/finance/purchase/page/pay")
    loc = (r.headers.get("Location") or "")
    h_before = c0.get("/finance/purchase/page/pay/" + months[0]).get_data(as_text=True)
    other = [m for m in months if m != months[0]]
    ck("BEFORE: the sheet offered no way to any other month",
       all(("/page/pay/" + m) not in h_before for m in other),
       [m for m in other if ("/page/pay/" + m) in h_before])

    # ---- 2. the fix, followed the way a finger follows it ------------------
    r = c1.get("/finance/purchase/page/pay")
    ck("the tile still lands on the newest month",
       r.status_code in (301, 302) and months[0] in (r.headers.get("Location") or ""),
       "%s %s" % (r.status_code, r.headers.get("Location")))
    h = c1.get("/finance/purchase/page/pay/" + months[0]).get_data(as_text=True)
    ck("the sheet now carries a month strip", 'data-s264="months"' in h)
    for m in other:
        ck("  %s is one tap away" % m, ('/page/pay/' + m) in h)
    ck("the month being read is NOT a link to itself",
       ('href="/finance/purchase/page/pay/%s"' % months[0]) not in h)

    # follow every link in the strip and open what it points at
    hrefs = set(re.findall(r'href="([^"]*/page/pay/\d{4}-\d{2})"', h))
    ck("every month in the strip actually opens", bool(hrefs) and all(
        c1.get(u).status_code == 200 for u in sorted(hrefs)),
       sorted((u, c1.get(u).status_code) for u in sorted(hrefs)))
    for m in months:
        hm = c1.get("/finance/purchase/page/pay/" + m).get_data(as_text=True)
        ck("%s: its sheet names the month it is showing" % m,
           ("Vendor payments" in hm) and (new._month_name(m) in hm))
        ck("%s: and the strip is on that page too" % m, 'data-s264="months"' in hm)

    # ---- 3. the two screens name each other --------------------------------
    ha = c1.get("/finance/purchase/page/month/" + months[0]).get_data(as_text=True)
    ck("the purchase audit page points at that month's PAYMENT SHEET",
       ('/page/pay/' + months[0]) in ha and "the payment sheet for" in ha)
    ck("and it says out loud which job it is ('This is the purchase audit')",
       "This is the purchase audit" in ha)
    ck("the payment sheet points back, in a sentence that reads",
       ('/page/month/' + months[0]) in h
       and "To check the bills themselves, open" in h
       and "the same month, bill by bill" not in h)
    ha0 = c0.get("/finance/purchase/page/month/" + months[0]).get_data(as_text=True)
    ck("BEFORE: the audit page said nothing about a payment sheet",
       "payment sheet" not in ha0)

    # ---- 4. nothing else moved ---------------------------------------------
    for page in ("hub", "scans", "orders", "book"):
        r1 = c1.get("/finance/purchase/page/" + page)
        r0 = c0.get("/finance/purchase/page/" + page)
        ck("the existing page /%s still renders" % page, r1.status_code == 200, r1.status_code)
        ck("  and /%s is byte-identical to before" % page,
           r1.get_data() == r0.get_data())
    with app1.test_request_context("/"):
        s1, g1 = new._pay_rows(dbf1(), months[0])
    with app0.test_request_context("/"):
        s0, g0 = old._pay_rows(dbf0(), months[0])
    ck("the sheet's own figures are untouched",
       [(g["norm"], g["payable_p"], g["route"]) for g in g1] ==
       [(g["norm"], g["payable_p"], g["route"]) for g in g0])
    stripped = ha.replace(
        u'This is the purchase audit \u2014 one row per Marg bill. To pay the month, open ', "", 1)
    stripped = re.sub(r'<b><a href="[^"]*/page/pay/[^"]*">[^<]*</a></b>\. ',
                      "One row per Marg bill. ", stripped, count=1)
    ck("the audit page is otherwise byte-identical -- one sentence added, nothing else",
       stripped == ha0,
       [i for i, (x, y) in enumerate(zip(stripped, ha0)) if x != y][:1])

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d ok, %d failed" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
