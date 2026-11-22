#!/usr/bin/env python3
"""walk_s925.py -- kit S925 walked on a COPY of finance.db (never the live one). argv: <code dir with the kit's files> <copy.db> [control]
Checks, through the real porders blueprint (and order_flow mounted by its own init) in a Flask test app:
the owner's plain /finance/porders (his tile) lands on /finance/porders/flow; ?home=1 still gives him the one-task screen; ?old=1 the old
page; a sender (reception) and Shavez are NOT moved; the flow page carries the link to reception's screen. CONTROL (the FROM files) red."""
import os
import shutil
import sys

CODE, SRC = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["PORDERS_SOURCE"] = "tables"
os.environ["NEEDS_YOU_WITHOUT_S408"] = "1"
DB = SRC + ".walk925"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import sqlite3                                                    # noqa: E402
from flask import Flask                                           # noqa: E402
import porders as P                                               # noqa: E402

WHO = {"u": None}
USERS = {"manoj": ["checker"], "alisha": ["maker"], "shavez": ["maker"], "amir": ["maker"]}


_CON = {}


def db_getter():                                                  # one connection for the walk, as the app's per-request one
    if "c" not in _CON:
        _CON["c"] = sqlite3.connect(DB, timeout=5, check_same_thread=False)
        _CON["c"].row_factory = sqlite3.Row
    return _CON["c"]


def require_fn(*roles, unit=None):
    u = WHO["u"]
    return dict(user=u, login=u, roles=USERS[u]), None


app = Flask(__name__)
P.init(app, db_getter, require_fn)
import purchase_app as PA                                         # noqa: E402
PA.init(app, db_getter, require_fn)
cl = app.test_client()


def get(who, url):
    WHO["u"] = who
    return cl.get(url)


r = get("manoj", "/finance/porders")
ok(r.status_code == 302 and r.headers.get("Location", "").endswith("/finance/porders/flow"), "the owner's tile lands on his grouped flow page (%s %s)" % (r.status_code, r.headers.get("Location")))
r = get("manoj", "/finance/porders?home=1")
ok(r.status_code == 200 and b"<html" in r.data.lower() and b"porders/flow" not in r.headers.get("Location", "").encode(), "?home=1 still gives him the one-task screen (%s)" % r.status_code)
r = get("manoj", "/finance/porders?old=1")
ok(r.status_code == 200, "?old=1 still gives the old page (%s)" % r.status_code)
r = get("alisha", "/finance/porders")
ok(r.status_code == 200, "reception's screen is not moved (%s)" % r.status_code)
r = get("shavez", "/finance/porders")
ok(r.status_code == 200, "Shavez's screen is not moved (%s)" % r.status_code)
r = get("manoj", "/finance/porders/flow")
ok(r.status_code == 200 and b"/finance/porders?home=1" in r.data, "the flow page links to reception's screen (%s)" % r.status_code)
for path in ("/finance/purchase/page/orders", "/finance/purchase/page/staff"):
    r = get("manoj", path)
    ok(r.status_code == 302 and r.headers.get("Location", "").endswith("/finance/porders"), "%s retired: the owner goes to the purchase orders page (%s %s)" % (path, r.status_code, r.headers.get("Location")))
r = get("amir", "/finance/purchase/page/orders")
ok(r.status_code == 302 and r.headers.get("Location", "").endswith("/finance/purchase/page/hub"), "a login with no purchase-orders role (Amir) goes to the purchase hub (%s %s)" % (r.status_code, r.headers.get("Location")))
r = get("manoj", "/finance/purchase/page/hub")
ok(r.status_code == 200 and b"/page/orders" not in r.data and b"Open the purchase orders page" in r.data, "the purchase hub renders; its Orders card opens the purchase orders page (%s)" % r.status_code)
with app.test_request_context("/finance/purchase/page/hub"):
    WHO["u"] = "manoj"
    nav = str(PA._page("t", "x"))
ok("/page/orders" not in nav and "/page/staff" not in nav and "/finance/porders" in nav, "the purchase top bar: Orders and Order medicines gone, Purchase orders there")
ok("finance_app" not in sys.modules, "the walk never loaded the whole app (no path to the live database)")
_CON.get("c") and _CON["c"].close()
os.remove(DB)
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
