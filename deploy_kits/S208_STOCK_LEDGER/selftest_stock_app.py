#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_stock_app.py — hit the ACTUAL routes, on a throwaway database.

Runs as an install gate, so it must never touch the live store: it builds its
own temp db, exercises every route through Flask's test client, and deletes it.

    python3 selftest_stock_app.py        exit 0 = all passed, 1 = a check failed
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, jsonify           # noqa: E402
import stock_app                            # noqa: E402

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


# --------------------------------------------------------------- harness
tmp = tempfile.mkdtemp(prefix="stock_selftest_")
DB = os.path.join(tmp, "t.db")
CON = sqlite3.connect(DB)
CON.row_factory = sqlite3.Row

ROLE = {"user": "darpan", "roles": ["maker"]}       # swapped per test


def db():
    return CON


def require(*roles):
    have = set(ROLE.get("roles") or [])
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(ROLE), None


app = Flask(__name__)
stock_app.init(app, db, require, unit="medical")
c = app.test_client()

print("[1] schema and health")
r = c.get("/finance/stock/api/healthz")
ck("healthz answers", r.status_code == 200, r.status_code)
j = r.get_json()
ck("it creates its own tables on first touch", j["ok"] and j["counts"] == 0)
ck("the causes are published so the UI never invents one",
   "UNEXPLAINED" in j["causes"] and "EXPIRY" in j["causes"] and "BREAKAGE" in j["causes"])
ck("calling it twice does not fall over on the schema",
   c.get("/finance/stock/api/healthz").status_code == 200)

print("\n[2] a count MUST be pinned to a bill")
r = c.post("/finance/stock/api/count", json={"marg_as_on": "2026-08-27", "items": [{"item": "X"}]})
ck("a count with no bill number is refused", r.status_code == 400, r.status_code)
ck("and it says why", "pinned to a bill" in (r.get_json().get("message") or ""))

print("\n[3] load the expected stock")
snap = {"as_on": "2026-08-27", "source": "STOCK_CLOSING_TOTALS", "items": [
    {"item": "ACILOC 300", "qty": 77, "packing": "1*20", "pack_size": 20, "rate_p": 500},
    {"item": "ARSEODEO", "qty": 117, "packing": "1*10", "pack_size": 10, "rate_p": 1200},
    {"item": "ALGESIA CR", "qty": 0, "packing": "1*1", "pack_size": 1},
]}
r = c.post("/finance/stock/api/snapshot", json=snap)
ck("a maker may load a snapshot", r.status_code == 200, r.status_code)
ck("three items landed", r.get_json()["items"] == 3)
ck("nothing to reconcile yet", r.get_json()["reconciled"] == 0)

print("\n[4] submit the count — differences are raised once")
cnt = {"marg_as_on": "2026-08-27", "bill_no": "a003195", "bill_date": "2026-08-27",
       "items_total": 376, "items": [
           {"item": "ACILOC 300", "marg_qty": 77, "counted_qty": 77, "pack_size": 20,
            "counted_by": "Darpan", "entered_by": "Darpan"},
           {"item": "ARSEODEO", "marg_qty": 117, "counted_qty": 23, "pack_size": 10,
            "counted_by": "Darpan", "entered_by": "Alisha",
            "batches": {"VT114": 23}},
           {"item": "ALGESIA CR", "marg_qty": 0, "counted_qty": 5, "pack_size": 1,
            "counted_by": "Darpan", "entered_by": "Darpan"},
       ]}
r = c.post("/finance/stock/api/count", json=cnt)
ck("the count is accepted", r.status_code == 200, r.get_json())
j = r.get_json()
ck("three items recorded", j["items"] == 3)
ck("two differences raised, not three", j["differences"] == 2, j)
CID = j["count_id"]
ck("the bill number is stored upper-cased",
   CON.execute("SELECT bill_no FROM stock_count WHERE id=?", (CID,)).fetchone()[0] == "A003195")
ck("the batch detail survived",
   json.loads(CON.execute("SELECT batches FROM stock_count_item WHERE item='ARSEODEO'"
                          ).fetchone()[0]) == {"VT114": 23})
ck("who counted and who typed are BOTH kept",
   tuple(CON.execute("SELECT counted_by,entered_by FROM stock_count_item "
                     "WHERE item='ARSEODEO'").fetchone()) == ("Darpan", "Alisha"))

print("\n[5] the difference is priced from the last purchase rate")
row = CON.execute("SELECT diff,value_p FROM stock_diff WHERE item='ARSEODEO'").fetchone()
ck("short by 94", row["diff"] == -94, row["diff"])
ck("valued at -94 x 1200 paise", row["value_p"] == -112800, row["value_p"])
row2 = CON.execute("SELECT value_p FROM stock_diff WHERE item='ALGESIA CR'").fetchone()
ck("an item with no known rate is recorded anyway, unpriced",
   row2["value_p"] is None, row2["value_p"])

print("\n[6] naming the door is the checker's job")
r = c.get("/finance/stock/api/open")
ck("both differences are open", r.get_json()["open"] == 2)
DID = [x for x in r.get_json()["items"] if x["item"] == "ARSEODEO"][0]["id"]
ROLE.update(user="darpan", roles=["maker"])
r = c.post("/finance/stock/api/diff/%d/cause" % DID, json={"cause": "EXPIRY"})
ck("a maker may NOT set the cause", r.status_code == 403, r.status_code)
ROLE.update(user="drmanoj", roles=["checker"])
r = c.post("/finance/stock/api/diff/%d/cause" % DID, json={"cause": "nonsense"})
ck("an invented cause is refused", r.status_code == 400)
r = c.post("/finance/stock/api/diff/%d/cause" % DID,
           json={"cause": "expiry", "note": "removed 12-Aug, no voucher"})
ck("a checker may, and case does not matter", r.status_code == 200, r.get_json())
ck("it is stored with who and when",
   CON.execute("SELECT cause,cause_by FROM stock_diff WHERE id=?", (DID,)
               ).fetchone()["cause_by"] == "drmanoj")

print("\n[7] AUTO-RECONCILE — the step nobody has to remember")
later = {"as_on": "2026-08-28", "items": [
    {"item": "ARSEODEO", "qty": 23, "pack_size": 10},        # fixed in Marg
    {"item": "ALGESIA CR", "qty": 2, "pack_size": 1},        # partly fixed only
]}
r = c.post("/finance/stock/api/snapshot", json=later)
ck("one difference closed by itself", r.get_json()["reconciled"] == 1, r.get_json())
ck("the fixed one is reconciled",
   CON.execute("SELECT status FROM stock_diff WHERE item='ARSEODEO'"
               ).fetchone()["status"] == "reconciled")
ck("and it records WHICH export agreed",
   CON.execute("SELECT closed_as_on FROM stock_diff WHERE item='ARSEODEO'"
               ).fetchone()["closed_as_on"] == "2026-08-28")
ck("a PARTLY fixed item stays open — 'closer' is not 'correct'",
   CON.execute("SELECT status FROM stock_diff WHERE item='ALGESIA CR'"
               ).fetchone()["status"] == "open")
ck("only one difference is left open", c.get("/finance/stock/api/open").get_json()["open"] == 1)

print("\n[8] where the stock actually goes")
r = c.get("/finance/stock/api/losses")
j = r.get_json()
causes = {x["cause"]: x for x in j["by_cause"]}
ck("the shortage is filed under EXPIRY", "EXPIRY" in causes, list(causes))
ck("94 units lost to it", causes["EXPIRY"]["units"] == 94)
ck("worth Rs 1128", causes["EXPIRY"]["value_p"] == 112800)
ck("the surplus is reported SEPARATELY, never netted off the loss",
   j["surplus"]["n"] == 1 and j["surplus"]["units"] == 5, j["surplus"])
ck("ARSEODEO leads the by-item list", j["by_item"][0]["item"] == "ARSEODEO")
ck("a date window filters it out",
   c.get("/finance/stock/api/losses?from=2027-01-01&to=2027-12-31"
         ).get_json()["by_cause"] == [])

print("\n[9] a second count on the same item builds the history")
c.post("/finance/stock/api/snapshot", json={"as_on": "2026-09-27", "items": [
    {"item": "ARSEODEO", "qty": 40, "pack_size": 10, "rate_p": 1200}]})
c.post("/finance/stock/api/count", json={
    "marg_as_on": "2026-09-27", "bill_no": "A004000", "bill_date": "2026-09-27",
    "items": [{"item": "ARSEODEO", "marg_qty": 40, "counted_qty": 31,
               "pack_size": 10, "counted_by": "Shavez", "entered_by": "Shavez"}]})
j = c.get("/finance/stock/api/losses").get_json()
rep = {x["item"]: x["times"] for x in j["repeat_offenders"]}
ck("ARSEODEO is now a repeat offender", rep.get("ARSEODEO") == 2, rep)
ck("and the earlier reconciled loss is still counted in the totals",
   {x["cause"]: x["units"] for x in j["by_cause"]}.get("EXPIRY") == 94)
ck("the new one sits under UNEXPLAINED until somebody names it",
   {x["cause"]: x["units"] for x in j["by_cause"]}.get("UNEXPLAINED") == 9)

print("\n[10] the sender's door — S208, the fault that made this kit unusable")
# A SECOND app, mounted the way finance_app.py mounts it in production: with
# the pharmacy sender's token injected. Nobody is signed in for any of this.
TOK = "test-marg-token-not-a-real-secret"
app2 = Flask(__name__)
stock_app.init(app2, db, require, unit="medical", marg_token=TOK)
c2 = app2.test_client()
ROLE.update(user=None, roles=[])                       # NOBODY is signed in

r = c2.post("/finance/stock/api/snapshot",
            json={"as_on": "2026-10-01", "items": [{"item": "ACILOC 300", "qty": 77,
                                                    "pack_size": 20}]},
            headers={"X-Finance-Marg": TOK})
ck("the sender's token loads a snapshot with nobody signed in",
   r.status_code == 200, r.status_code)
r = c2.post("/finance/stock/api/snapshot", json={"as_on": "2026-10-01", "items": [{"item": "X"}]},
            headers={"X-Finance-Marg": "wrong"})
ck("a WRONG token is refused", r.status_code == 403, r.status_code)
r = c2.post("/finance/stock/api/snapshot", json={"as_on": "2026-10-01", "items": [{"item": "X"}]})
ck("NO token and nobody signed in is refused", r.status_code == 403, r.status_code)

# and it opens exactly one door -- this is the whole safety argument
r = c2.post("/finance/stock/api/count",
            json={"marg_as_on": "2026-10-01", "bill_no": "A1", "items": []},
            headers={"X-Finance-Marg": TOK})
ck("the same token may NOT submit a count", r.status_code == 403, r.status_code)
r = c2.post("/finance/stock/api/diff/1/cause", json={"cause": "EXPIRY"},
            headers={"X-Finance-Marg": TOK})
ck("the same token may NOT name a cause", r.status_code == 403, r.status_code)
r = c2.get("/finance/stock/api/losses", headers={"X-Finance-Marg": TOK})
ck("the same token may NOT read the losses", r.status_code == 403, r.status_code)

# and with no token configured, the header means nothing at all
app3 = Flask(__name__)
stock_app.init(app3, db, require, unit="medical")       # marg_token not set
r = app3.test_client().post("/finance/stock/api/snapshot",
                            json={"as_on": "2026-10-01", "items": [{"item": "X"}]},
                            headers={"X-Finance-Marg": TOK})
ck("with no token configured the header grants nothing", r.status_code == 403, r.status_code)
ROLE.update(user="drmanoj", roles=["checker"])

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
CON.close()
import shutil
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if _fail else 0)
