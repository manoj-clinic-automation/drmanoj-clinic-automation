#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_purchase_root_s243.py -- the S243 purchase_app.py mounted on a real Flask app
the way the S224/S240 selftests mount it (same init signature as finance_app's
S224 mount: init(app, db, require, unit=, marg_token=, assets_db=)), on a temp
finance.db built from purchase_schema.sql plus the four tables the pages read.

Asserts: GET /finance/purchase and /finance/purchase/ -> 302 to /finance/purchase/page/hub
for a signed-in checker; /page/hub, /page/salts and /api/healthz answer as they did
on the unpatched rev 13 (same status, same bytes for hub and salts).

    PA_DIR=<folder with purchase_app.py + purchase_schema.sql> python3 -B walk_purchase_root_s243.py
Set BASE_PA=<path to the unpatched rev 13> to prove the pages did not change.
"""
import hashlib
import io
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PA_DIR = os.environ.get("PA_DIR", HERE)
BASE_PA = os.environ.get("BASE_PA", "")
TMP = tempfile.mkdtemp(prefix="walk_s243_")
DB = os.path.join(TMP, "finance.db")
PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))


def build_db():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript("""
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, ingest_batch_id INTEGER,
  unit TEXT NOT NULL, business_date TEXT NOT NULL, bill_no TEXT NOT NULL, is_return INTEGER NOT NULL DEFAULT 0,
  seq INTEGER, item_name TEXT NOT NULL, item_key TEXT NOT NULL, pack TEXT, qty_raw TEXT, amount_p INTEGER,
  expiry_ym TEXT, batch TEXT);
CREATE TABLE stock_snapshot (as_on TEXT NOT NULL, item TEXT NOT NULL, qty INTEGER NOT NULL, packing TEXT,
  pack_size INTEGER NOT NULL DEFAULT 1, loaded_at TEXT NOT NULL, source TEXT, PRIMARY KEY (as_on, item));
CREATE TABLE stock_rate (item TEXT PRIMARY KEY, rate_p INTEGER NOT NULL, pack_size INTEGER NOT NULL DEFAULT 1,
  as_of TEXT, source TEXT);
CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, as_on TEXT NOT NULL, source TEXT NOT NULL, item TEXT NOT NULL,
  qty INTEGER NOT NULL, received_at TEXT NOT NULL);
""")
    con.commit()
    con.close()


def mount(pa_path):
    """Import the given purchase_app.py fresh under a private module name and mount it."""
    import importlib.util
    from flask import Flask, g, has_app_context, jsonify
    work = tempfile.mkdtemp(prefix="pa_")
    shutil.copyfile(pa_path, os.path.join(work, "purchase_app.py"))
    for cand in (os.path.join(PA_DIR, "purchase_schema.sql"),
                 os.path.join(os.environ.get("FINANCE_DIR", "/root/finance"), "purchase_schema.sql")):
        if os.path.exists(cand):
            shutil.copyfile(cand, os.path.join(work, "purchase_schema.sql"))
            break
    else:
        raise SystemExit("purchase_schema.sql not found beside purchase_app.py nor in FINANCE_DIR")
    spec = importlib.util.spec_from_file_location("purchase_app_walk_%d" % len(sys.modules),
                                                  os.path.join(work, "purchase_app.py"))
    PA = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(PA)
    WHO = {"user": "manoj", "role": "doctor", "roles": {"checker"}}

    def _db():
        if not has_app_context():
            raise RuntimeError("Working outside of application context")
        if "db" not in g:
            g.db = sqlite3.connect(DB)
            g.db.row_factory = sqlite3.Row
        return g.db

    def _require(*roles, unit="medical"):
        if not WHO["user"]:
            return None, (jsonify(ok=False, error="not_signed_in"), 401)
        have = set(WHO["roles"])
        if not have.intersection(roles):
            return None, (jsonify(ok=False, error="not_permitted"), 403)
        return dict(user=WHO["user"], role=WHO["role"], roles=sorted(have)), None

    app = Flask("walk_" + os.path.basename(work))
    PA.init(app, _db, _require, unit="medical", marg_token="walk-tok",
            assets_db=os.path.join(TMP, "absent.db"), assets_url="https://assets.example")

    @app.teardown_appcontext
    def _close(_e):
        c = g.pop("db", None)
        if c is not None:
            c.close()

    return app, WHO


def pages(app, who):
    c = app.test_client()
    out = {}
    for p in ("/finance/purchase/page/hub", "/finance/purchase/page/salts",
              "/finance/purchase/api/healthz"):
        r = c.get(p)
        out[p] = (r.status_code, r.get_data())
    who["user"] = ""
    out["anon-hub"] = c.get("/finance/purchase/page/hub").status_code
    who["user"] = "manoj"
    return out


P = "/finance/purchase"
new_path = os.path.join(PA_DIR, "purchase_app.py")
print("walking %s (md5 %s) on a temp db at %s" % (new_path, hashlib.md5(open(new_path, "rb").read()).hexdigest(), DB))
build_db()
app, who = mount(new_path)
c = app.test_client()
for u in (P, P + "/"):
    r = c.get(u)
    ck("GET %s -> 302" % u, r.status_code == 302, str(r.status_code))
    ck("GET %s Location is %s/page/hub" % (u, P), r.headers.get("Location", "").endswith(P + "/page/hub"),
       r.headers.get("Location", ""))
who["user"] = ""
r = c.get(P + "/")
ck("root with nobody signed in still redirects to the hub (the app gate, not this rule, refuses strangers)",
   r.status_code == 302 and r.headers.get("Location", "").endswith(P + "/page/hub"))
who["user"] = "manoj"
newp = pages(app, who)
ck("hub answers 200 for the checker", newp[P + "/page/hub"][0] == 200, str(newp[P + "/page/hub"][0]))
ck("hub is marked (doctor)", b"(doctor)" in newp[P + "/page/hub"][1])
ck("salts page answers 200 for the checker", newp[P + "/page/salts"][0] == 200, str(newp[P + "/page/salts"][0]))
ck("api/healthz answers 200 ok", newp[P + "/api/healthz"][0] == 200 and b'"ok"' in newp[P + "/api/healthz"][1])
ck("hub with nobody signed in -> 401 from the mounted require (fail closed)", newp["anon-hub"] == 401,
   str(newp["anon-hub"]))
ck("no page carries a phone-shaped number",
   not any(__import__("re").search(rb"\b\d{10}\b", v[1]) for k, v in newp.items() if isinstance(v, tuple)))

if BASE_PA and os.path.exists(BASE_PA):
    build_db()
    app0, who0 = mount(BASE_PA)
    c0 = app0.test_client()
    ck("unpatched rev 13: GET %s -> 404 (the symptom)" % (P + "/"), c0.get(P + "/").status_code == 404)
    base = pages(app0, who0)
    for p in (P + "/page/hub", P + "/page/salts", P + "/api/healthz"):
        same = base[p][0] == newp[p][0] and base[p][1] == newp[p][1]
        if not same and p.endswith("healthz"):
            same = base[p][0] == newp[p][0]      # healthz carries a timestamp-free payload, but be safe
        ck("%s: same status and same bytes as the unpatched rev 13" % p, same,
           "%s vs %s" % (base[p][0], newp[p][0]))
    ck("unpatched rev 13 has no page_root", "page_root" not in open(BASE_PA, encoding="utf-8").read())
else:
    print("  (BASE_PA not given: the byte-identity legs were skipped)")

print("RESULT: %d passed, %d failed" % (len(PASSED), len(FAILED)))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILED else 0)
