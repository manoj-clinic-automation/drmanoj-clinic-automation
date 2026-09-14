# -*- coding: utf-8 -*-
"""S265 LIVE-SHAPE WALK -- the advice is checked against the bank's own sheets.

The point of this card is that it is IDENTICAL in shape to the NEFT ADVICE files
sent to the bank from April to July 2026, so the walk holds it to that shape:
the same seven columns in the same order, the same wording, alphabetical by the
name on the account, a total in the Amount column -- and every figure equal to
the payable the sheet above it shows, to the rupee.

    python3 walk_s265.py --file <patched> --before <backup> --db <copy.db>
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
COLS = ["Sr. No.", "Txn. type", "Credit Account Number", "Credit Account Name",
        "IFSC", "Amount", "Narration"]


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
    tmp = tempfile.mkdtemp(prefix="s265_")
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

    h0 = c0.get("/finance/purchase/page/pay/" + months[0]).get_data(as_text=True)
    ck("BEFORE: the sheet showed no advice at all", "advice_s265" not in h0)

    for m in months[:3]:
        r = c1.get("/finance/purchase/page/pay/" + m)
        ck("%s: the page answers 200" % m, r.status_code == 200, r.status_code)
        h = r.get_data(as_text=True)
        ck("%s: the advice is on the page" % m, 'id="advice_s265"' in h)
        blk = h[h.index('id="advice_s265"'):]
        blk = blk[:blk.index("</table>")]

        # ---- the bank's own seven columns, in the bank's own order ----------
        ths = [re.sub("<[^>]+>", "", x).replace("&nbsp;", " ").strip()
               for x in re.findall(r"<th[^>]*>.*?</th>", blk, re.S)]
        ck("%s: the seven columns are the bank's, in its order" % m, ths == COLS, ths)

        # ---- the letterhead, as it is printed -------------------------------
        head = h[h.index('id="advice_s265"'):h.index('<table class="adv"')]
        ck("%s: the letterhead carries the firm, the address, the GSTIN and the DL" % m,
           "SANJEEVNI MEDICOS" in head and "Rampur Bagh" in head
           and "GSTIN" in head and "DL NO." in head)

        # ---- every line agrees with the sheet above it, to the rupee --------
        with app1.test_request_context("/"):
            rows, total, missing, paise = new._advice_rows_s265(dbf1(), m)
            s, groups = new._pay_rows(dbf1(), m)
        neft = {g["norm"]: g for g in groups if g["route"] == "NEFT" and g["payable_p"] > 0}
        ck("%s: every NEFT vendor with a payable is on the advice, and no other" % m,
           len(rows) + len(missing) == len(neft),
           "%d rows + %d missing vs %d NEFT" % (len(rows), len(missing), len(neft)))
        ck("%s: each amount is that vendor's payable, to the rupee" % m,
           all(r["rupees"] == int(round(neft[vn]["payable_p"] / 100.0))
               for r in rows for vn in [next(k for k, g in neft.items()
                                              if g["name"] == r["vendor"])]),
           [(r["vendor"], r["rupees"]) for r in rows[:2]])
        ck("%s: the total equals the sum of its own lines" % m,
           total == sum(r["rupees"] for r in rows), total)
        ck("%s: the total is printed under the Amount column" % m,
           ('<tr class="tot"><td colspan="5" class="n">Total</td><td class="n">%s</td>'
            % "{:,}".format(total)) in h)
        ck("%s: the lines are alphabetical by the name on the account" % m,
           [r["name"].upper() for r in rows] == sorted(r["name"].upper() for r in rows))
        ck("%s: every line carries an account number and an IFSC" % m,
           all(r["acct"] and r["ifsc"] for r in rows),
           [r["name"] for r in rows if not (r["acct"] and r["ifsc"])])
        ck("%s: every line says NEFT and Vendor Payment, as the bank file does" % m,
           blk.count(">NEFT<") == len(rows) and blk.count(">Vendor Payment<") == len(rows),
           "%d / %d vs %d" % (blk.count(">NEFT<"), blk.count(">Vendor Payment<"), len(rows)))

        # ---- a cheque vendor must never reach the bank ----------------------
        cheq = [g for g in groups if g["route"] != "NEFT"]
        ck("%s: no cheque vendor appears in the advice (%s)" % (m, len(cheq)),
           all(new._esc(g["name"]) not in blk for g in cheq),
           [g["name"] for g in cheq if new._esc(g["name"]) in blk])

        # ---- it must not print as if it were signed off ---------------------
        final = s["status"]["status"] == "final"
        ck("%s: %s" % (m, "locked, so no DRAFT mark" if final
                       else "not locked, so it is marked DRAFT"),
           ("DRAFT" in h) != final)

    # ---- printing gives the advice and nothing else -------------------------
    h = c1.get("/finance/purchase/page/pay/" + months[0]).get_data(as_text=True)
    ck("printing hides the rest of the page", "@media print" in h and "visibility:hidden" in h)
    ck("printing is set to A4 landscape", "size:A4 landscape" in h)
    ck("the Print button is not itself printed", 'class="p noprint" onclick="window.print()"' in h)

    # ---- nothing else moved --------------------------------------------------
    for page in ("hub", "scans", "orders", "book", "month/" + months[0]):
        r1, r0 = (c1.get("/finance/purchase/page/" + page),
                  c0.get("/finance/purchase/page/" + page))
        ck("/%s is byte-identical to before" % page,
           r1.status_code == 200 and r1.get_data() == r0.get_data(), r1.status_code)
    with app1.test_request_context("/"):
        g1 = new._pay_rows(dbf1(), months[0])[1]
    with app0.test_request_context("/"):
        g0 = old._pay_rows(dbf0(), months[0])[1]
    ck("the sheet's own figures are untouched",
       [(g["norm"], g["payable_p"], g["route"]) for g in g1] ==
       [(g["norm"], g["payable_p"], g["route"]) for g in g0])

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d ok, %d failed" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
