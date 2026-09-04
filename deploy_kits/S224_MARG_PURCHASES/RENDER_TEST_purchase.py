#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_purchase.py -- S224: every page, as each of the three kinds of person, on the
REAL August/July exports -- then read as the owner will read them.

Checks, per page and role: it renders (200); it carries the words the owner will look for;
it carries NO ten-digit run anywhere (F-185 -- not a phone, not a token, not an id that
looks like one); nothing leaks as 'None'; no traceback; the print stylesheet and the
viewport tag are there; every internal link is a route this blueprint serves.

    python3 -B RENDER_TEST_purchase.py
"""
import glob
import os
import re
import sqlite3
import sys
import tempfile
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(KITS, "S206_SANJEEVNI_MARG_PURCHASE"))
ARCHIVE = os.environ.get("MARG_ARCHIVE", os.path.expanduser("~/mnt/Downloads/margsync/MargArchive"))

from flask import Flask, g, has_app_context, jsonify     # noqa: E402
import marg_purchase_rows as R                            # noqa: E402
import purchase_app as PA                                 # noqa: E402
import marg_purchase as MP                                # noqa: E402

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))


TMP = tempfile.mkdtemp(prefix="s224r_")
DB = os.path.join(TMP, "finance.db")
ASSETS = os.path.join(TMP, "assets.db")
TOKEN = "render-" + os.urandom(4).hex()
WHO = {"user": "manoj", "roles": {"checker"}}


def _db():
    if not has_app_context():
        raise RuntimeError("outside app context")
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


def _require(*roles, unit="medical"):
    have = set(WHO["roles"])
    if not have.intersection(roles):
        return None, (jsonify(ok=False), 403)
    return dict(user=WHO["user"], role="", roles=sorted(have)), None


c0 = sqlite3.connect(DB)
c0.executescript("""
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, bill_no TEXT, is_return INTEGER DEFAULT 0,
  seq INTEGER, item_name TEXT, item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INTEGER, expiry_ym TEXT, batch TEXT);
CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER, packing TEXT, pack_size INTEGER DEFAULT 1, loaded_at TEXT,
  source TEXT, PRIMARY KEY (as_on, item));
CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, as_on TEXT, source TEXT, item TEXT, qty INTEGER, received_at TEXT);
""")
c0.commit()
c0.close()
app = Flask(__name__)
PA.init(app, _db, _require, marg_token=TOKEN, assets_db=ASSETS, assets_url="https://assets.example")


@app.teardown_appcontext
def _close(_e):
    c = g.pop("db", None)
    if c is not None:
        c.close()


cl = app.test_client()
H = {"X-Finance-Marg": TOKEN}
P = "/finance/purchase"


def one(pat):
    got = sorted(glob.glob(os.path.join(ARCHIVE, pat)))
    return got[-1] if got else None


# the real exports, in the order the nights would send them
for typ, pat in (("BILLWISE", "PURCHASE_BILLWISE/2026-08/*_2026-08-01_to_2026-08-31__*.XLS"),
                 ("SUPPLIERWISE", "PURCHASE_SUPPLIERWISE/2026-08/*_2026-08-01_to_2026-08-31__*.XLS"),
                 ("BILLWISE", "PURCHASE_BILLWISE/2026-07/*.XLS"),
                 ("BILLITEMWISE", "PURCHASE_BILLITEMWISE/2026-08/*_2026-08-28_to_2026-08-31__*.XLS")):
    p = one(pat)
    r = cl.post(P + "/api/push", json=R.payload(p, typ), headers=H)
    ck("pushed %s %s" % (typ, os.path.basename(p)[-22:-4]), r.status_code == 200 and r.get_json()["stored"])
for pat in ("PURCHASE_ITEMWISE/2026-08/*_2026-08-01_to_2026-08-26__*.XLS",
            "PURCHASE_ITEMWISE/2026-08/*_2026-08-28_to_2026-08-29__*.XLS",
            "PURCHASE_ITEMWISE/2026-07/*.XLS"):
    p = one(pat)
    r = cl.post(P + "/api/push", json=R.payload(p, "ITEMWISE", MP.read_purchase), headers=H)
    ck("pushed ITEMWISE %s" % os.path.basename(p)[-22:-4], r.status_code == 200 and r.get_json()["stored"])
cl.post(P + "/api/feed", json=dict(pull_last="2026-09-04T06:40:21+05:30", pull_age_min=38, state="asleep", host="manojz"), headers=H)

# a scan store, with one exact match, so the link renders
c = sqlite3.connect(DB)
b = c.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE month='2026-08' ORDER BY id LIMIT 1").fetchone()
items = [r[0] for r in c.execute("SELECT DISTINCT item FROM purchase_line ORDER BY item LIMIT 6")]
today = dt.date.today()
for i, it in enumerate(items):
    c.execute("INSERT INTO stock_snapshot VALUES (?,?,?,?,?,?,?)", (today.strftime("%d-%m-%Y"), it, 3 * i, "1*10", 10, "t", "push_snapshot"))
    for d in range(20):
        c.execute("INSERT INTO sale_line_item (unit,business_date,bill_no,seq,item_name,item_key,qty_raw) VALUES (?,?,?,?,?,?,?)",
                  ("medical", (today - dt.timedelta(days=d)).isoformat(), "S%d" % d, 1, it, it.lower(), "1:2"))
c.commit()
c.close()
a = sqlite3.connect(ASSETS)
a.executescript("CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, "
                "status TEXT, ocr_status TEXT, created_at TEXT DEFAULT '');")
a.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,status,ocr_status) VALUES (?,?,?,?,?,?,?)",
          ("Pharmacy", b[0], b[1], b[2], b[3] / 100.0, "captured", "read"))
a.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,status,ocr_status) VALUES (?,?,?,?,?,?,?)",
          ("Pharmacy", "SOME OTHER SCAN", "77", "2026-08-20", 999.0, "captured", "empty"))
a.commit()
a.close()
r = cl.post(P + "/api/rematch", json={})
ck("rematch ran", r.status_code == 200 and r.get_json()["links"] >= 1)
cl.post(P + "/api/order", json=dict(action="create", vendor="ZZ RENDER VENDOR", lines=[dict(item=items[0], packs=2, pack_size=10, rate_p=5000)]))

TEN = re.compile(r"(?<!\d)\d{10}(?!\d)")
WORDS = {
    "hub": ["Marg Purchases", "August 2026", "July 2026", "Marg total (supplier-wise)", "Item-wise net", "Returns",
            "No lines", "Feed health", "pull asleep since 06:40 IST", "Stock verification", "Scan links", "Orders",
            "PROVISIONAL", "Make this week", "(supplier-wise, final for month-end)", "carry a purchase return",
            "ready to finalise"],
    "month/2026-08": ["August 2026", "Marg purchase, August 2026", "supplier-wise, final for month-end", "item-wise net",
                      "Scan", "Check", "PROVISIONAL", "cannot finalise yet", "no item lines yet", "export item-wise for"],
    "month/2026-07": ["July 2026", "Marg purchase, July 2026", "Purchase returns (2)", "(Marg)", "PROVISIONAL",
                      "ready to finalise"],
    "scans": ["Scan links", "Scans with no Marg bill", "Marg bills with no scan", "SOME OTHER SCAN", "https://assets.example/bills/"],
    "orders": ["Orders", "Order book", "Reorder plan", "PROVISIONAL until the stock verification has run a month",
               "ZZ RENDER VENDOR", "draft"],
}
ROLE_WORDS = {"doctor": {"month/2026-08": ["Correct", "Wrong", "Item lines missing"], "month/2026-07": ["FINALISE July 2026"],
                         "scans": ["Re-match now"], "orders": ["Save as order", "Copy this order"]},
              "maker": {"month/2026-08": ["Correct", "Wrong"], "scans": ["Re-match now"], "orders": ["Copy this order"]},
              "viewer": {"hub": ["(view only)"]}}
# rev 4: no page says "mark each" / "unverified" / "Differ"; a purchase return never gets a verdict button
NOT_FOR = {"viewer": {"month/2026-08": ['onclick="verdict('], "scans": ["Re-match now"],
                      "orders": ["Save as order", "Copy this order", "tel:"]},
           "maker": {"orders": ["Save as order"], "month/2026-08": ["onclick=\"finalise("]},
           "doctor": {"month/2026-07": ['onclick="verdict(']}}
NEVER = ["mark each", "Mark each", "unverified", ">Differ<", ">Agree<", "differs from", "Bill-wise total (Marg)"]
for role, roles in (("doctor", {"checker"}), ("maker", {"maker"}), ("viewer", {"viewer"})):
    WHO.update(user={"doctor": "manoj", "maker": "darpan", "viewer": "amir"}[role], roles=roles)
    for page, words in WORDS.items():
        r = cl.get(P + "/page/" + page)
        h = r.get_data(as_text=True)
        tag = "%s as %s" % (page, role)
        ck("%s renders 200" % tag, r.status_code == 200)
        ck("%s: no ten-digit run anywhere" % tag, not TEN.search(h))
        ck("%s: nothing leaks as None, no traceback" % tag, ">None<" not in h and "Traceback" not in h)
        ck("%s: viewport + print stylesheet" % tag, 'name="viewport"' in h and "@media print" in h)
        missing = [w for w in words + ROLE_WORDS.get(role, {}).get(page, []) if w not in h]
        ck("%s: carries the owner's words" % tag, not missing, "missing " + ", ".join(missing))
        bad = [w for w in NOT_FOR.get(role, {}).get(page, []) if w in h]
        ck("%s: shows nothing this role may not use" % tag, not bad, "found " + ", ".join(bad))
        never = [w for w in NEVER if w in h]
        ck("%s: none of the rev-4 banned wording" % tag, not never, "found " + ", ".join(never))
        links = set(re.findall(r'href="(/finance/purchase/[^"]+)"', h))
        # rev 3 (the owner's find): a link or the JS base that forgets the mount prefix 404s at the
        # portal root. Every own href and const P must start with /finance/purchase.
        bare = re.findall(r'href="(/(?:page|api)/[^"]*)"', h) + re.findall(r"const P=(\"[^\"]*\")", h)
        bare = [b for b in bare if not b.strip('"').startswith("/finance/purchase")]
        ck("%s: every own link carries the mount prefix (rev 3)" % tag, not bare, ", ".join(bare))
        dead = [l for l in links if cl.get(l).status_code != 200]
        ck("%s: every internal link answers 200" % tag, not dead, ", ".join(dead))
WHO.update(user="manoj", roles={"checker"})
r = cl.get(P + "/page/month/2026-08")
ck("the month page groups bills by supplier (a supplier heading row per group)", r.get_data(as_text=True).count('colspan="7"') >= 10)
ck("the source files' header lines (shop name, phone) never reach a page",
   "SANJEEVNI MEDICOS" not in cl.get(P + "/page/month/2026-08").get_data(as_text=True))

print("\n%d PASS  %d FAIL" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED: " + f)
sys.exit(1 if FAILED else 0)
