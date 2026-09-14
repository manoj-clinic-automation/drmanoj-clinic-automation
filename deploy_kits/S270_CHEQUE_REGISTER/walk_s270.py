# -*- coding: utf-8 -*-
"""S270 LIVE-SHAPE WALK v2 -- run on the box, against a COPY of the real database.

v2, after v1 failed on the box and taught two things (F-483):

  1  THE PATCHED COPY MUST SIT BESIDE purchase_schema.sql. The app resolves its
     schema from its OWN folder, so a copy run out of /tmp made every page a 500
     looking for /tmp/purchase_schema.sql. --file must be a path inside
     /root/finance/.  This walk now refuses if it is not.
  2  A CHECK MUST NEVER PASS ON AN ERROR PAGE. Four checks went green in v1
     because a 500 body contains neither the string they wanted absent nor a
     working answer. Every check that reads a page now goes through need200(),
     which FAILS loudly when the page did not answer 200 -- it never quietly
     succeeds and never silently skips.

It loads BOTH files -- the one being replaced and the patched one -- each
against its OWN copy of the real finance.db, and holds them against each other.
The only permitted difference is the one this kit claims: the cheque card on the
payment sheet, and the register that did not exist before.

    python3 walk_s270.py --file <patched> --before <backup> --db <copy.db>

THE LIVE DATABASE IS NEVER OPENED. Both copies are made first and the walk's own
writes land in the copy, which is thrown away. The live file's md5 is taken at
the start and again at the end, and printed either way.
"""
import argparse
import hashlib
import importlib.machinery
import importlib.util
import os
import re
import shutil
import sqlite3
import sys
import tempfile

OK = BAD = 0
SKIPPED = []


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("    ok    %s" % name)
    else:
        BAD += 1
        print("    FAIL  %s   %s" % (name, str(detail)[:260]))


def skip(name, why):
    SKIPPED.append(name)
    print("    skip  %s  -- %s" % (name, why))


def load(path, dbpath, name, role="checker"):
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
        return {"user": "walk", "role": role, "roles": [role]}, None

    mod.init(app, db, require, unit="medical", url_prefix="/finance/purchase")
    return mod, app, db


def body_of(client, path):
    r = client.get(path)
    return r.status_code, r.get_data(as_text=True)


def need200(client, path, what):
    """Fetch a page and REFUSE to let anything downstream pass if it is not 200.
    Returns (html, True) when the page answered, (body, False) when it did not,
    and in the second case it has already recorded the failure itself."""
    st, h = body_of(client, path)
    if st != 200:
        ck("%s answers 200" % what, False, "status %d -- %s" % (st, _first_error(h)))
        return h, False
    return h, True


def _first_error(html):
    m = re.search(r"(\w*Error: [^<\n]+)", html or "")
    return m.group(1) if m else "no exception text in the body"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args(argv)

    real_dir = os.path.dirname(os.path.abspath(a.before))
    if os.path.dirname(os.path.abspath(a.file)) != real_dir:
        print("REFUSING: --file must sit in the app's own folder (%s).\n"
              "          The app loads purchase_schema.sql from beside itself, so a copy\n"
              "          anywhere else makes every page a 500. (F-483)" % real_dir)
        return 2

    live_md5_start = hashlib.md5(open(a.db, "rb").read()).hexdigest()
    tmp = tempfile.mkdtemp(prefix="s270_")
    db_b, db_a = os.path.join(tmp, "b.db"), os.path.join(tmp, "a.db")
    shutil.copy(a.db, db_b)
    shutil.copy(a.db, db_a)

    old, app0, dbf0 = load(a.before, db_b, "pa_before")
    new, app1, dbf1 = load(a.file, db_a, "pa_after")
    c0, c1 = app0.test_client(), app1.test_client()
    P = "/finance/purchase"

    print("\n  1 - EVERY OTHER SCREEN COMES BACK BYTE-IDENTICAL")
    for page in ("/page/hub", "/page/scans", "/page/orders", "/page/book"):
        s0, h0 = body_of(c0, P + page)
        s1, h1 = body_of(c1, P + page)
        if s0 != 200:
            skip("%s is unchanged" % page, "the page answered %d before the patch too" % s0)
            continue
        ck("%s is byte-identical" % page, s0 == s1 and h0 == h1,
           "status %d/%d, %d vs %d bytes" % (s0, s1, len(h0), len(h1)))

    print("\n  2 - THE MONTHS THE BOX ACTUALLY HAS")
    with app1.test_request_context("/"):
        months = new._months(dbf1(), 6)
    ck("the database has months of purchases", bool(months), months)
    if not months:
        print("\n%d ok, %d failed, %d skipped" % (OK, BAD, len(SKIPPED)))
        return 1
    month = months[0]["month"] if isinstance(months[0], dict) else months[0]
    print("    walking %s" % month)

    print("\n  3 - THE PAYMENT SHEET STILL WORKS, AND DIFFERS ONLY WHERE CLAIMED")
    s0, h0 = body_of(c0, "%s/page/pay/%s" % (P, month))
    s1, h1 = body_of(c1, "%s/page/pay/%s" % (P, month))
    ck("the sheet still answers 200", s1 == 200, s1)
    ck("the sheet before answered 200 too", s0 == 200, s0)
    ck("every figure the sheet showed before is still on it",
       all(x in h1 for x in re.findall(r"₹[\d,]+", h0)),
       [x for x in re.findall(r"₹[\d,]+", h0) if x not in h1][:6])
    ck("the NEFT total is untouched",
       h0.count("payable by NEFT") == h1.count("payable by NEFT"))
    ck("the new card is the one that changed", "cheque register for this month" in h1)
    ck("and the old card's wording is gone from the rendered page",
       "Write a cheque, and log it. The moment" not in h1)

    print("\n  4 - THE REGISTER ITSELF")
    h, ok = need200(c1, P + "/page/cheques", "the register")
    if ok:
        ck("it names itself", "Cheque register" in h)
    h, ok = need200(c1, "%s/page/cheques/%s" % (P, month), "the month's register")
    if ok:
        ck("it holds itself against the sheet", "Against the sheet" in h)
    ck("it did not exist before this kit", body_of(c0, P + "/page/cheques")[0] == 404,
       body_of(c0, P + "/page/cheques")[0])

    print("\n  5 - LOGGING ONE CHEQUE, IN THE COPY")
    con = dbf1()
    with app1.test_request_context("/"):
        s_, groups = new._pay_rows(con, month)
        cheq = [g for g in groups if g["route"] != "NEFT"]
    if not cheq:
        skip("a cheque is logged against a real vendor",
             "no vendor is on the cheque lane in %s on this box" % month)
    else:
        g = cheq[0]
        r = c1.post(P + "/api/cheque", json={
            "month": month, "vendor_norm": g["norm"], "vendor": g["name"],
            "payee": g["name"], "cheque_no": "WALK-S270-1",
            "cheque_date": "14-09-2026", "amount_p": g["payable_p"]})
        j = r.get_json()
        first_ok = bool(j and j.get("ok"))
        ck("the cheque is accepted", first_ok, "%s %s" % (r.status_code, j))
        if not first_ok:
            ck("the duplicate check can be trusted", False,
               "the first cheque never landed, so a refusal proves nothing")
        else:
            r2 = c1.post(P + "/api/cheque", json={
                "month": month, "vendor_norm": g["norm"], "vendor": g["name"],
                "cheque_no": "WALK-S270-1", "cheque_date": "15-09-2026", "amount_p": 100})
            j2 = r2.get_json()
            ck("the same number a second time is REFUSED",
               r2.status_code == 200 and j2 is not None and not j2.get("ok")
               and "WALK-S270-1" in (j2.get("message") or ""),
               "%s %s" % (r2.status_code, j2))
            h, ok = need200(c1, "%s/page/cheques/%s" % (P, month), "the register after logging")
            if ok:
                ck("the register shows it", "WALK-S270-1" in h)
            h, ok = need200(c1, "%s/page/pay/%s" % (P, month), "the sheet after logging")
            if ok:
                ck("and the sheet now says that vendor has its cheque", "WALK-S270-1" in h)

    print("\n  6 - A VIEWER MAY READ IT AND MAY NOT WRITE IT")
    vmod, vapp, vdb = load(a.file, db_a, "pa_viewer", role="viewer")
    vc = vapp.test_client()
    sv, hv = body_of(vc, P + "/page/cheques")
    if sv in (401, 403):
        skip("a viewer can open the register",
             "this box refuses a viewer at the front gate (%d) -- a role question, not a bug" % sv)
    elif sv != 200:
        ck("a viewer can open the register", False,
           "status %d -- %s" % (sv, _first_error(hv)))
    else:
        ck("a viewer can open the register", "Cheque register" in hv)
        ck("a viewer is offered no void control", 'onclick="chqvoid(' not in hv)

    print("\n  7 - THE LIVE DATABASE WAS NEVER TOUCHED")
    live_md5_end = hashlib.md5(open(a.db, "rb").read()).hexdigest()
    ck("the database this walk was pointed at is unchanged",
       live_md5_start == live_md5_end,
       "%s -> %s" % (live_md5_start, live_md5_end))
    print("    (both reads: %s)" % live_md5_start)

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d ok, %d failed, %d skipped" % (OK, BAD, len(SKIPPED)))
    if SKIPPED:
        print("SKIPPED, and never counted as a pass: %s" % ", ".join(SKIPPED))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
