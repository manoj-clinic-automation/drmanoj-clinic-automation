#!/usr/bin/env python3
"""walk_s937.py -- kit S937 walked on a COPY of finance.db (never the live one). argv: <code dir with the kit's files> <copy.db> [control]
Through the real porders blueprint (porders_s454 mounted by its own init) in a Flask test app: the WhatsApp-all confirm screen's list,
read back exactly as the browser's JSON.stringify sends it, EQUALS the server's list for made-up dealers whose names carry '&', an
apostrophe, '<' / '>' and '</script>'; the press then queues every one (200, not 409); a '</script>' in a name cannot end the script.
The order door and the phone are stubbed (nothing reaches a phone); the real screen also renders on the copy as it stands.
Half 2: his Purchase orders page (/finance/porders/flow) carries the 'Today's order sheet' button to reception's To-order screen, which
opens for him. CONTROL (the FROM files) goes red on the list checks and the button."""
import json
import os
import re
import shutil
import sys

CODE, SRC = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["NEEDS_YOU_WITHOUT_S408"] = "1"
DB = SRC + ".walk937"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import sqlite3                                                    # noqa: E402
from flask import Flask                                           # noqa: E402
import porders as P                                               # noqa: E402

WHO = {"u": "manoj"}
USERS = {"manoj": ["checker"]}
_CON = {}


def db_getter():
    if "c" not in _CON:
        _CON["c"] = sqlite3.connect(DB, timeout=5, check_same_thread=False)
        _CON["c"].row_factory = sqlite3.Row
    return _CON["c"]


def require_fn(*roles, unit=None):
    u = WHO["u"]
    return dict(user=u, login=u, roles=USERS[u]), None


app = Flask(__name__)
P.init(app, db_getter, require_fn)
cl = app.test_client()
import order_sheet as OS                                          # noqa: E402
import order_rules                                                # noqa: E402

frozen = bool(order_rules._frozen(db_getter()))
print("INFO ordering frozen on the copy: %s" % frozen)

# 1 -- the real screen on the copy as it stands (no stubs)
r = cl.get("/finance/porders/s454/order/whatsapp")
ok(r.status_code == 200 and b"<html" in r.data.lower(), "the WhatsApp-all confirm screen renders on the copy (%s)" % r.status_code)

r = cl.get("/finance/porders/flow")
ok(r.status_code == 200 and b'id="s937sheet" href="/finance/porders/s454/order"' in r.data, "his Purchase orders page carries the order-sheet button (%s)" % r.status_code)
r = cl.get("/finance/porders/s454/order")
ok(r.status_code == 200 and b"<html" in r.data.lower(), "the order sheet screen opens for him (%s)" % r.status_code)

# 2 -- made-up dealers whose names carry the characters html.escape changes
NAMES = ["WALKTEST MEDICAL & SCIENTIFIC", "WALKTEST D'SOUZA PHARMA", "WALKTEST A<B> TRADERS", "WALKTEST X </script> Y", "WALKTEST PLAIN AGENCIES"]
Q = [dict(sn=n, vendor=n, lines=[dict(item="WALKTEST TAB", qty=1)], sources=["sheet"], state="pending", has_phone=True, phone=None, wa=None)
     for n in NAMES]
REAL = (OS.phone_state, OS.wa_plan, OS.order_supplier, order_rules._frozen)
CALLED = []
OS.phone_state = lambda con: (True, "")
OS.wa_plan = lambda con: (list(Q), [], [])
OS.order_supplier = lambda con, who, sn, via: (CALLED.append(sn) or ({"ok": True}, 200))
order_rules._frozen = lambda con: None
try:
    r = cl.get("/finance/porders/s454/order/whatsapp")
    page = r.data.decode("utf-8")
    ok(r.status_code == 200, "the confirm screen renders with the made-up dealers (%s)" % r.status_code)
    scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
    s605 = [s for s in scripts if "s605wa" in s]
    ok(len(s605) == 1, "the screen's send script is one whole script element (found %d)" % len(s605))
    m = re.search(r"JSON\.stringify\(\{sns:(\[.*?\])\}\)", s605[0] if s605 else "", re.S)
    sent = None
    if m:
        try:
            sent = json.loads(m.group(1))                     # what JSON.stringify sends: JS string literals read as JSON
        except ValueError as e:
            print("INFO the list literal is not JSON: %s" % e)
    ok(sent == NAMES, "the list the screen sends equals the server's list, name for name (%s)" % ("equal" if sent == NAMES else repr(sent)[:160]))
    ok("&amp;" not in (s605[0] if s605 else "") and "&#x27;" not in (s605[0] if s605 else ""), "no html entity inside the send script")
    WHO["u"] = "manoj"
    r = cl.post("/finance/porders/api/s454/whatsapp", json={"sns": sent if sent is not None else []})
    j = r.get_json(silent=True) or {}
    ok(r.status_code == 200 and j.get("ok") and j.get("queued") == len(NAMES), "the press queues every dealer (%s, queued %s, %s)" % (r.status_code, j.get("queued"), j.get("error") or ""))
    ok(sorted(CALLED) == sorted(NAMES), "each dealer's order door called once (%d)" % len(CALLED))
    r = cl.post("/finance/porders/api/s454/whatsapp", json={"sns": NAMES[:-1]})
    ok(r.status_code == 409 and (r.get_json(silent=True) or {}).get("error") == "list_changed", "a list that truly moved is still refused (%s)" % r.status_code)
finally:
    OS.phone_state, OS.wa_plan, OS.order_supplier, order_rules._frozen = REAL
ok("finance_app" not in sys.modules, "the walk never loaded the whole app (no path to the live database)")
_CON.get("c") and _CON["c"].close()
os.remove(DB)
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
