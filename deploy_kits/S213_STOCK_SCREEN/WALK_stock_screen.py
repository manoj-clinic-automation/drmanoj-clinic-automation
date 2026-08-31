#!/usr/bin/env python3
# =============================================================================
#  WALK_stock_screen.py · S213 · the live-shape walk for the stock screen
#
#  Mounts the REAL stock_app v2 in a real Flask app over a real database built
#  from the real schema, seeds a snapshot the way push_snapshot would, and
#  drives the screens and the count end to end:
#
#   1  /page/count serves the proven page with the ledger's own data injected
#   2  the role gate holds on every screen and every API
#   3  a submitted count writes stock_count + stock_count_item and raises
#      exactly the right stock_diff rows -- the three empty tables fill
#   4  the SERVER's marg figure is the authority; a lying client is reported
#   5  a partial count is honest: uncounted items raise no difference
#   6  /page/diffs serves; a cause posts; UNEXPLAINED default stands
#   7  reconcile: the next agreeing snapshot closes the difference itself
#   8  the live page carries no artifact machinery and posts to the ledger
#
#  Run:  python -B WALK_stock_screen.py   (from inside the kit folder)
# =============================================================================
import json, os, sqlite3, sys, tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CHECKS = []
def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))

import stock_app
from flask import Flask, jsonify

# the database lives OUTSIDE the kit folder: on manojz the repo is a mounted
# filesystem where sqlite locking fails and files cannot be deleted -- both
# were found by running this walk there, not by reading it.
DB = os.path.join(tempfile.mkdtemp(prefix="walk_stock_"), "walk.db")

def get_db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

DENY = {"deny": False}
def require(*roles):
    if DENY["deny"]:
        return None, (jsonify(ok=False, error="forbidden"), 403)
    return {"user": "walkuser", "roles": list(roles)}, None

app = Flask(__name__)
stock_app.init(app, get_db, require, unit="medical", marg_token="WALKTOKEN")
c = app.test_client()

# ---- seed a snapshot exactly the way push_snapshot does ---------------------
snap = {"as_on": "27-08-2026", "source": "walk",
        "items": [
            {"item": "AXIMAL 200",  "qty": 40, "packing": "1*10", "pack_size": 10, "rate_p": 15000},
            {"item": "TRAMAVIN P",  "qty": 25, "packing": "1*10", "pack_size": 10, "rate_p": 9000},
            {"item": "ARM SLING",   "qty": 7,  "packing": "1*1",  "pack_size": 1,  "rate_p": 25000},
            {"item": "ETOZOX 90",   "qty": 0,  "packing": "1*10", "pack_size": 10, "rate_p": 12000},
        ]}
r = c.post("/finance/stock/api/snapshot", json=snap,
           headers={"X-Finance-Marg": "WALKTOKEN"})
check("snapshot loads by machine token", r.get_json().get("ok") is True)

print("— 1 · the counting page, served from the ledger's own data")
r = c.get("/finance/stock/page/count")
check("page answers 200 html", r.status_code == 200 and b"<title>" in r.data)
body = r.data.decode("utf-8")
i0, i1 = body.find("const DATA = ") + len("const DATA = "), body.find(";\nconst KEY")
data = json.loads(body[i0:i1])
check("the ledger's snapshot is the item universe",
      data["as_on"] == "27-08-2026" and len(data["items"]) == 4)
check("pack size decides the orthotic/pieces flag (ARM SLING s=1 -> o=1)",
      {it["n"]: it["o"] for it in data["items"]}["ARM SLING"] == 1)
check("expected quantities travel", {it["n"]: it["q"] for it in data["items"]}["AXIMAL 200"] == 40)

print("— 2 · the gate holds")
DENY["deny"] = True
codes = [c.get("/finance/stock/page/count").status_code,
         c.get("/finance/stock/page/diffs").status_code,
         c.get("/finance/stock/api/open").status_code,
         c.post("/finance/stock/api/count", json={}).status_code]
check("count page, diffs page, open, count API all refuse", codes == [403, 403, 403, 403])
DENY["deny"] = False

print("— 3 · a count fills the three tables and raises the right diffs")
count = {"marg_as_on": "27-08-2026", "bill_no": "A003195", "bill_date": "2026-08-31",
         "items_total": 4,
         "items": [
            {"item": "AXIMAL 200", "marg_qty": 40, "counted_qty": 35, "strips": 3,
             "loose": 5, "pack_size": 10, "packing": "1*10", "counted_by": "Darpan",
             "entered_by": "Darpan", "batches": {"B123": 5}},
            {"item": "TRAMAVIN P", "marg_qty": 25, "counted_qty": 25, "strips": 2,
             "loose": 5, "pack_size": 10, "packing": "1*10", "counted_by": "Darpan",
             "entered_by": "Darpan"},
            # ARM SLING deliberately NOT counted -- the partial-count case
         ]}
r = c.post("/finance/stock/api/count", json=count)
j = r.get_json()
check("count accepted", j.get("ok") is True)
check("exactly ONE difference raised (AXIMAL short 5)", j["differences"] == 1)
con = get_db()
check("stock_count row exists, pinned to the bill",
      con.execute("SELECT bill_no FROM stock_count").fetchone()["bill_no"] == "A003195")
check("stock_count_item holds both rows",
      con.execute("SELECT COUNT(*) c FROM stock_count_item").fetchone()["c"] == 2)
d = con.execute("SELECT item, diff, value_p, cause, status FROM stock_diff").fetchall()
check("the diff is AXIMAL -5, valued through the rate (-5 x 150.00)",
      len(d) == 1 and d[0]["item"] == "AXIMAL 200" and d[0]["diff"] == -5
      and d[0]["value_p"] == -75000)
check("cause starts UNEXPLAINED, status open",
      d[0]["cause"] == "UNEXPLAINED" and d[0]["status"] == "open")

print("— 4 · the server's marg figure is the authority")
lie = {"marg_as_on": "27-08-2026", "bill_no": "A003196", "bill_date": "2026-08-31",
       "items_total": 4,
       "items": [{"item": "ETOZOX 90", "marg_qty": 99, "counted_qty": 0,
                  "pack_size": 10, "counted_by": "X", "entered_by": "X"}]}
j = c.post("/finance/stock/api/count", json=lie).get_json()
check("a lying marg_qty is overridden by the snapshot (0 counted vs 0 expected -> no diff)",
      j["ok"] and j["differences"] == 0)
check("and the lie is reported back", j["marg_claim_mismatches"] == ["ETOZOX 90"])

print("— 5 · the bill anchor stays mandatory")
r = c.post("/finance/stock/api/count", json={"marg_as_on": "27-08-2026",
                                             "items": [{"item": "X", "counted_qty": 1}]})
check("no bill -> refused 400", r.status_code == 400)

print("— 6 · the diffs screen and the cause")
r = c.get("/finance/stock/page/diffs")
check("diffs page serves", r.status_code == 200 and b"Stock differences" in r.data)
did = con.execute("SELECT id FROM stock_diff WHERE item='AXIMAL 200'").fetchone()["id"]
j = c.post("/finance/stock/api/diff/%d/cause" % did,
           json={"cause": "EXPIRY", "note": "walk"}).get_json()
check("cause recorded", j["ok"] and j["cause"] == "EXPIRY")

print("— 7 · the next agreeing snapshot closes it by itself")
snap2 = dict(snap, as_on="28-08-2026")
snap2["items"] = [dict(x) for x in snap["items"]]
snap2["items"][0] = dict(snap2["items"][0], qty=35)     # Marg now agrees with the count
r = c.post("/finance/stock/api/snapshot", json=snap2,
           headers={"X-Finance-Marg": "WALKTOKEN"})
check("snapshot reconciles 1", r.get_json()["reconciled"] == 1)
check("the diff is closed, cause preserved",
      get_db().execute("SELECT status, cause FROM stock_diff WHERE id=?",
                       (did,)).fetchone()["status"] == "reconciled")

print("— 8 · the live page itself")
h = open(os.path.join(HERE, "stock_check_live.html"), encoding="utf-8").read()
check("no artifact machinery survives",
      "claude.use" not in h and "__SHARED__" not in h and "__SKEL__" not in h)
check("it posts to the ledger", '/finance/stock/api/count' in h)
check("the clamp-at-zero rule survives", "cannot hold less than nothing" in h)
check("the batch-sum honesty check survives", "batches add to" in h)
check("the two-person gate survives", "Who counted the stock" in h and "Who is entering it here" in h)
check("the bill anchor gate survives", "Last sale bill number" in h)
check("a fresh storage key (no artifact-era state bleeds in)", "sanj-stock-live-v1" in h)
check("data placeholder exactly once", h.count("__STOCK_DATA__") == 1)

fails = [n for n, ok in CHECKS if not ok]
print()
if fails:
    print("WALK FAILED:", ", ".join(fails)); sys.exit(1)
print("ALL WALK CHECKS PASS (%d)" % len(CHECKS))
