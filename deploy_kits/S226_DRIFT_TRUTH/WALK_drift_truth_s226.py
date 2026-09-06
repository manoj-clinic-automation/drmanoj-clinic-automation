"""LIVE-SHAPE WALK -- S226_DRIFT_TRUTH.

It reproduces the exact morning of 06-Sep-2026 that the owner saw on the first
live screen:

  * three pushes of the SAME day's Marg export and two of ours -- because
    `stock_feed` is append-only and every push writes a whole set of rows;
  * a duplicate item merged in Marg between two of those pushes;
  * a day that has been compared only once.

What he saw: "746 items" and "1,492 items" in the readiness header for a
373-item shop; a drift table that did not change after the merge; and the
reading "look at the shelf" on a day that had been compared once.
Every check below fails on the code he was looking at and passes on this kit.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
# The readiness walk (and its schema finder) lives in the S226_READINESS kit.
# APPENDED, never inserted: that folder also holds the PREVIOUS stock_app.py,
# and putting it first silently tests the old file. It did, once.
_sib = os.path.join(os.path.dirname(HERE), "S226_READINESS")
if os.path.isdir(_sib) and _sib not in sys.path:
    sys.path.append(_sib)
from flask import Flask                                       # noqa: E402
import stock_app                                              # noqa: E402
import WALK_readiness_s226 as R   # its builder -- the schemas stay one copy

OK, BAD = [], []
CON = None
ITEMS = ["ACILOC 300", "BIO D3 MAX", "LACTOVAX SYP 200ML", "LACTOVAX SYP 200ML."]
D4 = {"ACILOC 300": 40, "BIO D3 MAX": 82,
      "LACTOVAX SYP 200ML": 5, "LACTOVAX SYP 200ML.": 0}


def chk(n, c, d=""):
    (OK if c else BAD).append(n + (("  -- " + str(d)) if d and not c else ""))
    print(("  ok   " if c else "  FAIL ") + n + (("   " + str(d)) if d else ""))


def push(kind, as_on, at, qty, items=None):
    """One push of one feed for one day -- a whole set of rows, exactly as
    push_snapshot.py and push_expected.py write them."""
    src = ("push_snapshot.py as on %s" % as_on) if kind == "marg" \
        else ("push_expected.py pur_to=03-09-2026 run %s" % at)
    for it in (items or ITEMS):
        CON.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at)"
                    " VALUES (?,?,?,?,?)", (as_on, src, it, qty[it], at))
    CON.commit()


def day4():
    push("marg", "2026-09-04", "2026-09-05T09:11:17", D4)
    push("expected", "2026-09-04", "2026-09-05T09:20:00", D4)


def setup(dbname="_walk226b.db"):
    global CON
    R.DB = os.path.join(HERE, dbname)
    con = R.build(); R.fill(con); CON = con
    con.execute("DELETE FROM stock_feed"); con.commit()

    day4()                                     # both feeds agree everywhere
    # 05-Sep 01:26 -- Marg's first push, LACTOVAX still split in two
    push("marg", "2026-09-05", "2026-09-06T01:26:19",
         {"ACILOC 300": 38, "BIO D3 MAX": 58,
          "LACTOVAX SYP 200ML": -2, "LACTOVAX SYP 200ML.": 7})
    # 05-Sep 02:50 and 02:59 -- ours, twice, as the pull cycle sends it
    for at in ("2026-09-06T02:50:47", "2026-09-06T02:59:12"):
        push("expected", "2026-09-05", at,
             {"ACILOC 300": 38, "BIO D3 MAX": 65,
              "LACTOVAX SYP 200ML": 5, "LACTOVAX SYP 200ML.": 0})
    # 05-Sep 03:10 -- Marg AFTER the merge: one item fewer, and it agrees
    push("marg", "2026-09-05", "2026-09-06T03:10:46",
         {"ACILOC 300": 38, "BIO D3 MAX": 58, "LACTOVAX SYP 200ML": 5},
         items=["ACILOC 300", "BIO D3 MAX", "LACTOVAX SYP 200ML"])

    app = Flask(__name__)
    stock_app.init(app, lambda: con,
                   lambda *r: ({"user": "walk", "roles": ["medical.checker"],
                                "role": "checker"}, None), unit="medical")
    return con, app


def main():
    con, app = setup()
    c = app.test_client()
    print("== S226_DRIFT_TRUTH -- live-shape walk ==")

    # --------------------------------------- 1 the counts he actually saw
    st = c.get("/finance/stock/api/readiness").get_json()["stock"]
    chk("Marg's count is ITEMS, not rows (he saw 746)", st["marg"]["items"] == 3,
        st["marg"]["items"])
    chk("our count is ITEMS, not rows (he saw 1,492)", st["expected"]["items"] == 4,
        st["expected"]["items"])
    chk("the NEWEST Marg push is reported (03:10, not 01:26)",
        st["marg"]["processed_at"].endswith("03:10:46"), st["marg"]["processed_at"])
    chk("the newest push of ours is reported (02:59, not 02:50)",
        st["expected"]["processed_at"].endswith("02:59:12"),
        st["expected"]["processed_at"])

    # --------------------------------------- 2 a re-export must reach the table
    by = {r["item"]: r for r in c.get("/finance/stock/api/drift").get_json()["items"]}
    chk("the merged LACTOVAX now AGREES -- the re-export reached the table",
        by["LACTOVAX SYP 200ML"]["last"] == 0, by.get("LACTOVAX SYP 200ML"))
    chk("the merged-away duplicate stops on the day it was merged",
        by["LACTOVAX SYP 200ML."]["days"] == ["2026-09-04"],
        by["LACTOVAX SYP 200ML."]["days"])
    chk("...and its history is not rewritten either",
        by["LACTOVAX SYP 200ML."]["runs"] == 1)
    chk("BIO D3 MAX still shows its real 7 -- nothing was papered over",
        by["BIO D3 MAX"]["last"] == 7, by.get("BIO D3 MAX"))
    chk("ACILOC agrees on both days", by["ACILOC 300"]["disagreed"] == 0)

    # --------------------------------------- 3 the reading, said honestly
    chk("two days compared, so a series exists", by["BIO D3 MAX"]["runs"] == 2)
    chk("'runs' is now spoken of as DAYS", "day" in by["ACILOC 300"]["verdict"],
        by["ACILOC 300"]["verdict"])
    chk("a gap on some days points at the shelf",
        by["BIO D3 MAX"]["verdict"] == "gap on some days -- look at the shelf",
        by["BIO D3 MAX"]["verdict"])
    chk("the day-by-day series is in date order",
        by["BIO D3 MAX"]["days"] == ["2026-09-04", "2026-09-05"])

    con.execute("DELETE FROM stock_feed WHERE as_on='2026-09-04'"); con.commit()
    one = {r["item"]: r for r in c.get("/finance/stock/api/drift").get_json()["items"]}
    chk("ONE day never claims to know which -- the overclaim he read",
        one["BIO D3 MAX"]["verdict"] == "first day compared -- too early to say which",
        one["BIO D3 MAX"]["verdict"])
    day4()

    # --------------------------------------- 4 "where do I see the latest stock"
    n = c.get("/finance/stock/api/now").get_json()
    chk("/api/now answers", n.get("ok") is True)
    chk("it shows the NEWEST day", n["as_on"] == "2026-09-05", n["as_on"])
    rows = {r["item"]: r for r in n["rows"]}
    chk("ours and Marg's side by side",
        rows["BIO D3 MAX"]["ours"] == 65 and rows["BIO D3 MAX"]["marg"] == 58,
        rows.get("BIO D3 MAX"))
    chk("the gap is ours minus Marg's", rows["BIO D3 MAX"]["gap"] == 7)
    chk("an item only one feed has is not called a gap",
        rows["LACTOVAX SYP 200ML."]["gap"] is None)
    chk("the biggest gap sorts first", n["rows"][0]["item"] == "BIO D3 MAX",
        n["rows"][0]["item"])
    t = n["totals"]
    chk("totals: items / agree / differ",
        (t["items"], t["agree"], t["differ"]) == (4, 2, 1),
        (t["items"], t["agree"], t["differ"]))
    chk("the readiness header rides along", n["readiness"]["ok"] is True)

    con.execute("UPDATE stock_feed SET qty=-45 WHERE item='ACILOC 300' "
                "AND as_on='2026-09-05'"); con.commit()
    chk("BELOW ZERO is counted and named",
        c.get("/finance/stock/api/now").get_json()["totals"]["below_zero"] == 1)
    con.execute("UPDATE stock_feed SET qty=38 WHERE item='ACILOC 300' "
                "AND as_on='2026-09-05'"); con.commit()

    # --------------------------------------- 5 the pages themselves
    h = c.get("/finance/stock/page/now").get_data(as_text=True)
    chk("the stock page serves", "<h1>Stock as we hold it</h1>" in h)
    chk("it opens with the readiness card too",
        h.index('id="rdy-card"') < h.index("<h1>Stock as we hold it</h1>"))
    chk("it says plainly this is not a count", "It is not a count" in h)

    hd = c.get("/finance/stock/page/drift").get_data(as_text=True)
    chk("the drift headers say what they mean",
        "Gap on the<br>last day" in hd and "Day by day (oldest &rarr; newest)" in hd)
    chk("'Runs' and 'Recent' are gone from the headers",
        ">Runs<" not in hd and ">Recent<" not in hd)
    chk("the gap is explained above the table", "our figure minus Marg" in hd)
    chk("the day-by-day column is a numeric column", 'class="spark n"' in hd)

    # --------------------------------------- 6 nothing may kill a page
    con.execute("DROP TABLE stock_feed"); con.commit()
    chk("a missing feed table does not kill /page/now",
        c.get("/finance/stock/page/now").status_code == 200)
    chk("...nor /api/now", c.get("/finance/stock/api/now").get_json().get("ok") is True)

    print("\n%d ok, %d FAILED" % (len(OK), len(BAD)))
    for b in BAD:
        print("   FAILED: " + b)
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()
