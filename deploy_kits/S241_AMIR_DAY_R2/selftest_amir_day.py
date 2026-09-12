"""
selftest_amir_day.py -- a LIVE-SHAPE walk of Amir's seven steps, offline.

It builds a temporary sqlite database with the real shapes of purchase_export
and purchase_bill, mounts amir_day on a real Flask app, and walks the day the
way Amir would: nothing is stubbed at the HTTP layer.

Run:  /root/wa/venv/bin/python3 selftest_amir_day.py
Exit: 0 = all ok, 1 = something failed (the failing check is named).
"""

import os
import re
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, g                                    # noqa: E402
import amir_day                                               # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
TODAY = datetime.now(IST).strftime("%Y-%m-%d")
FIRST = TODAY[:8] + "01"
YDAY = (datetime.now(IST) - timedelta(days=1)).strftime("%Y-%m-%d")

OK = []
BAD = []


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print(("   ok   " if cond else "   FAIL ") + name + (("  -- " + detail) if detail and not cond else ""))


def build_db(path):
    cx = sqlite3.connect(path)
    cx.executescript("""
    CREATE TABLE purchase_export(
        md5 TEXT PRIMARY KEY, type TEXT, file TEXT, period_from TEXT, period_to TEXT,
        export_stamp TEXT, received_at TEXT, n_rows INTEGER, grand_amount_p INTEGER,
        superseded_by TEXT);
    CREATE TABLE purchase_bill(
        id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_norm TEXT, supplier TEXT,
        bill_no TEXT, bill_date TEXT, month TEXT, cash_p INTEGER, credit_p INTEGER,
        amount_p INTEGER, source_md5 TEXT, bw_md5 TEXT, sw_md5 TEXT, date_src TEXT,
        UNIQUE(supplier_norm, bill_no, bill_date));
    """)
    cx.commit()
    return cx


def add_export(cx, md5, kind, stamp_day, pfrom=None, pto=None, rows=100):
    cx.execute("""INSERT OR REPLACE INTO purchase_export
                  (md5,type,period_from,period_to,export_stamp,received_at,n_rows,superseded_by)
                  VALUES(?,?,?,?,?,?,?,NULL)""",
               (md5, kind, pfrom or FIRST, pto or stamp_day,
                stamp_day + " 09:40:00", stamp_day + " 09:41:00", rows))
    cx.commit()


def add_bill(cx, norm, supplier, no, date, amount_p, bw):
    cx.execute("""INSERT OR REPLACE INTO purchase_bill
                  (supplier_norm,supplier,bill_no,bill_date,month,amount_p,bw_md5)
                  VALUES(?,?,?,?,?,?,?)""",
               (norm, supplier, no, date, date[:7], amount_p, bw))
    cx.commit()


def make_app(dbpath, allow=True):
    app = Flask(__name__)
    app.config["TESTING"] = True

    def db():
        if "cx" not in g:
            g.cx = sqlite3.connect(dbpath)
            g.cx.row_factory = sqlite3.Row
        return g.cx

    seen_roles = []

    def require(*roles, **kw):
        seen_roles.append((roles, kw.get("unit")))
        if not allow:
            return None, ({"error": "no_role_here"}, 403)
        return {"username": "amir"}, None

    @app.teardown_appcontext
    def _close(exc):
        cx = g.pop("cx", None)
        if cx is not None:
            cx.commit()
            cx.close()

    amir_day.init(app, db, require, unit="medical")
    app.seen_roles = seen_roles
    return app


def body(resp):
    return resp.get_data(as_text=True)


def follow(c, url):
    return c.get(url, follow_redirects=True)


def main():
    tmp = tempfile.mkdtemp(prefix="amirday_")
    dbp = os.path.join(tmp, "t.db")
    cx = build_db(dbp)

    app = make_app(dbp)
    c = app.test_client()

    print("-- 1. an empty day")
    r = follow(c, "/finance/amir")
    check("home opens and lands on step 1", "Punch" in body(r) and "Step 1 of 7" in body(r))
    check("the 1 to 7 banner is drawn", body(r).count("class=steps") == 1 and "6<br>" in body(r))

    print("-- 2. the punch never blocks")
    r = c.post("/finance/amir/step/1", data={"tick": "1", "go": "1"}, follow_redirects=True)
    check("after the punch tick it moves to step 2", "Step 2 of 7" in body(r))
    r = c.post("/finance/amir/step/2", data={"tick": "2", "go": "2"}, follow_redirects=True)
    check("step 2 leads to step 3", "Step 3 of 7" in body(r))
    r = c.post("/finance/amir/step/3", data={"tick": "3", "go": "3"}, follow_redirects=True)
    check("step 3 leads to the check", "Step 4 of 7" in body(r))

    print("-- 3. the check TELLS him, and names the open Excel")
    t = body(r)
    check("both reports reported missing", t.count("&#10007;") == 2)
    check("it says dobara banaiye", "Dobara banaiye" in t)
    check("it names the open Excel", "Excel band kijiye" in t)
    check("he is not asked whether a report arrived", "?" not in t.split("Server ne")[1][:400])

    print("-- 4. one report only -- still not done")
    add_export(cx, "m_item_1", "ITEMWISE", TODAY)
    r = follow(c, "/finance/amir/step/4")
    t = body(r)
    check("one verified, one not", t.count("&#10003;") == 1 and t.count("&#10007;") == 1)

    print("-- 5. a report with the wrong period is refused by reason")
    add_export(cx, "m_bill_bad", "BILLWISE", TODAY, pfrom=YDAY, pto=TODAY)
    r = follow(c, "/finance/amir/step/4")
    check("wrong period named, not just missing", "tareekh galat" in body(r))

    print("-- 6. the right pair verifies")
    cx.execute("UPDATE purchase_export SET superseded_by='x' WHERE md5='m_bill_bad'")
    cx.commit()
    add_export(cx, "m_bill_1", "BILLWISE", TODAY, rows=141)
    add_bill(cx, "yuvika", "Yuvika Pharma", "B-101", TODAY, 452000, "m_bill_1")
    add_bill(cx, "arora", "Arora & Sons", "A-77", TODAY, 118050, "m_bill_1")
    r = follow(c, "/finance/amir/step/4")
    check("both verified", body(r).count("&#10003;") == 2)
    r = c.post("/finance/amir/step/4", data={"go": "4"}, follow_redirects=True)
    check("verified pair leads to the bills", "Step 5 of 7" in body(r))

    print("-- 7. the bill list fills itself")
    r = follow(c, "/finance/amir/step/5")
    t = body(r)
    check("both bills are listed", "B-101" in t and "A-77" in t)
    check("he types no bill number", "<input type=text" not in t and "type=number" not in t)
    check("every reason is offered", all(lbl in t for _c, lbl in amir_day.REASONS))
    check("the choice is forced on every option of every bill",
          t.count("required") == 2 * len(amir_day.REASONS),
          "required=%d" % t.count("required"))

    print("-- 8. a half-answered form writes the half and keeps the rest")
    r = c.post("/finance/amir/step/5",
               data={"n": "2", "k_0": "yuvika|B-101|" + TODAY, "r_0": "ok",
                     "k_1": "arora|A-77|" + TODAY, "go": "5"},
               follow_redirects=True)
    t = body(r)
    check("the unanswered bill is still on the list", "A-77" in t)
    check("the answered bill is gone", "B-101" not in t)
    check("it did not move past step 5", "Step 5 of 7" in t)

    print("-- 9. a deficiency raises exactly one claim; 'theek hai' raises none")
    r = c.post("/finance/amir/step/5",
               data={"n": "1", "k_0": "arora|A-77|" + TODAY, "r_0": "short", "go": "5"},
               follow_redirects=True)
    n = cx.execute("SELECT COUNT(*) FROM amir_claim").fetchone()[0]
    check("one claim raised, not two", n == 1, "claims=%d" % n)
    row = cx.execute("SELECT supplier, reason, state, amount_p FROM amir_claim").fetchone()
    check("the claim carries supplier, reason, amount and state open",
          row[0] == "Arora & Sons" and row[1] == "short" and row[2] == "open" and row[3] == 118050)
    check("no claim for the bill answered theek hai",
          cx.execute("SELECT COUNT(*) FROM amir_claim WHERE bill_no='B-101'").fetchone()[0] == 0)
    check("the list is now empty", "Koi bill baaki nahi" in body(r) or "Step 6 of 7" in body(r))

    print("-- 10. re-answering the same bill does not raise a second claim")
    cx.execute("DELETE FROM amir_bill_disposition WHERE bill_no='A-77'")
    cx.commit()
    c.post("/finance/amir/step/5",
           data={"n": "1", "k_0": "arora|A-77|" + TODAY, "r_0": "short", "go": "5"},
           follow_redirects=True)
    n = cx.execute("SELECT COUNT(*) FROM amir_claim").fetchone()[0]
    check("still one claim", n == 1, "claims=%d" % n)

    print("-- 11. the day will not close while something is left")
    r = c.post("/finance/amir/step/7", data={"go": "7"}, follow_redirects=True)
    check("close refused, and it says what is left", "Abhi kuch baaki" in body(r))
    check("nothing was written", cx.execute(
        "SELECT COUNT(*) FROM amir_day WHERE closed_at IS NOT NULL").fetchone()[0] == 0)

    print("-- 12. the salt tick, then the close")
    c.post("/finance/amir/step/6", data={"tick": "6", "go": "6"}, follow_redirects=True)
    r = c.post("/finance/amir/step/7", data={"go": "7"}, follow_redirects=True)
    check("DIN BAND shown", "DIN BAND" in body(r))
    check("the close is recorded with a name", cx.execute(
        "SELECT closed_by FROM amir_day WHERE day=?", (TODAY,)).fetchone()[0] == "amir")

    print("-- 13. yesterday's unanswered bill returns as pichhla baaki")
    add_export(cx, "m_bill_y", "BILLWISE", YDAY, pfrom=FIRST, pto=YDAY)
    add_bill(cx, "oldco", "Old Co", "O-9", YDAY, 90000, "m_bill_y")
    r = follow(c, "/finance/amir/step/5")
    check("the carried bill is shown under pichhla baaki",
          "Pichhla baaki" in body(r) and "O-9" in body(r))

    print("-- 14. a hostile supplier name cannot inject markup")
    add_bill(cx, "evil", "<script>alert(1)</script>", "X-1", TODAY, 100, "m_bill_1")
    r = follow(c, "/finance/amir/step/5")
    check("the script tag is escaped", "<script>alert" not in body(r)
          and "&lt;script&gt;" in body(r))

    print("-- 15. no phone-shaped digits anywhere on his screens (F-185)")
    pages = [body(follow(c, "/finance/amir/step/%d" % i)) for i in range(1, 8)]
    pages.append(body(follow(c, "/finance/amir/day")))
    phone = re.compile(r"(?<!\d)[6-9]\d{9}(?!\d)")
    hits = [p for p in pages if phone.search(re.sub(r"<[^>]+>", " ", p))]
    check("no ten-digit phone-shaped number rendered", not hits)

    print("-- 16. the owner's view is English and counts the claims")
    t = body(follow(c, "/finance/amir/day"))
    check("owner page is English", "Claims for Darpan" in t and "The daily pair" in t)
    check("owner page has no Hinglish leaking in", "kijiye" not in t and "baaki" not in t)
    check("it reports the open claim", ">1<" in t or "Open: <b>1</b>" in t)

    print("-- 17. the tables are created once and survive a second call")
    before = cx.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    follow(c, "/finance/amir/step/1")
    after = cx.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    check("schema creation is idempotent", before == after, "%d -> %d" % (before, after))

    print("-- 18. an out-of-range step does not explode")
    r = follow(c, "/finance/amir/step/99")
    check("step 99 falls back to step 1", "Step 1 of 7" in body(r))

    # LAST, deliberately: init() sets module-level globals (the house pattern,
    # same as marg_door.py), so mounting a second app rebinds them for the
    # whole process.  One app per process in production; last here.
    print("-- 19. a user without the role is refused, and nothing is written")
    app2 = make_app(dbp, allow=False)
    c2 = app2.test_client()
    r = c2.get("/finance/amir/step/1")
    check("refused with 403", r.status_code == 403)
    check("the refusal is readable, not a stack trace", "Yeh page aapke liye nahin hai" in body(r))
    check("nothing new was written by the refused user", cx.execute(
        "SELECT COUNT(*) FROM amir_claim").fetchone()[0] == 1)

    print("-- 20. the gate lets a viewer in (Amir is not a maker on this unit)")
    roles, unit = app.seen_roles[-1]
    check("viewer is inside the gate", "viewer" in roles, "roles=%s" % (roles,))
    check("maker and checker are still inside it",
          "maker" in roles and "checker" in roles)
    check("it is gated on the medical unit", unit == "medical", "unit=%s" % unit)

    print("")
    print("%d ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        for b in BAD:
            print("  FAILED: " + b)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
