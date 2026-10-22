#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s624.py -- S624_SCANAPP_SMALL_FIXES' walk: the three files (batteries.py, asset_machine.py, stationery.py) loaded into a
STAND-IN asset app (Flask's test client, no port, no live row: a fresh database made here; made-up papers 'B-9xxx', a made-up
machine, a made-up battery place 'WALK624'; nothing sent anywhere).

    python3 -B walk_s624.py --app <folder with the three files> [--expect-red]

--expect-red (the negative control, on the FROM files): exit 0 only when every check in MUST_RED is RED and every other is GREEN.
"""
import datetime
import importlib.util
import os
import re
import shutil
import sqlite3
import sys
import tempfile

from flask import Flask, g

ARGS = sys.argv[1:]
APPD = ARGS[ARGS.index("--app") + 1] if "--app" in ARGS else "/root/assetapp"
EXPECT_RED = "--expect-red" in ARGS
MUST_RED = ("B1", "M1", "M2", "M3", "M6", "M7", "S1", "S4", "S6", "S8", "M10")
RES = {}
TODAY = datetime.date(2026, 10, 22)


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:600]) if (d and not ok) else ""))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(APPD, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


work = tempfile.mkdtemp(prefix="s624walk_")
DB = os.path.join(work, "assets.db")
con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE desk_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT, action TEXT NOT NULL, detail TEXT);
CREATE TABLE bill_audit(id INTEGER PRIMARY KEY, bill_id INTEGER, action TEXT, detail TEXT);
CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT NOT NULL DEFAULT 'Consumable', vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')), stamp_no TEXT, status TEXT NOT NULL DEFAULT 'draft', lane TEXT, dup_of INTEGER, doc_kind TEXT,
  challan_state TEXT, challan_of INTEGER, subgroup TEXT, page_of INTEGER, source_stored TEXT);
CREATE TABLE bill_items(id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, item_name TEXT NOT NULL, pack_size TEXT, quantity REAL, rate REAL);
CREATE TABLE claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT);
CREATE TABLE assets(id INTEGER PRIMARY KEY, name TEXT NOT NULL, location_id INTEGER NOT NULL DEFAULT 1, category TEXT NOT NULL DEFAULT 'Other',
  purchase_date TEXT, price REAL, vendor TEXT, serial_no TEXT, status TEXT NOT NULL DEFAULT 'Active', contract_type TEXT NOT NULL DEFAULT 'None',
  provider TEXT, contract_cost REAL, hidden INTEGER NOT NULL DEFAULT 0, bill_id INTEGER, created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE expiries(id INTEGER PRIMARY KEY, entity TEXT NOT NULL, entity_id INTEGER NOT NULL, label TEXT NOT NULL, due_date TEXT NOT NULL,
  threshold_days INTEGER NOT NULL DEFAULT 60, resolved INTEGER NOT NULL DEFAULT 0);
CREATE TABLE service_logs(id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL, log_date TEXT NOT NULL, work TEXT NOT NULL, cost REAL, done_by TEXT,
  next_due TEXT, created_by INTEGER, created_at TEXT NOT NULL DEFAULT (datetime('now')), is_pm INTEGER, svc_type TEXT);
INSERT INTO assets(id, name, created_at) VALUES(1, 'WALK624 made-up machine', '2026-10-01 10:00:00');
INSERT INTO bills(id, vendor, created_at, stamp_no, lane, doc_kind, subgroup) VALUES(901, 'MADE-UP AMC', '2026-10-02 10:00:00', 'B-9901', 'clinic', 'bill', 'clinic_equipment');
INSERT INTO bills(id, vendor, created_at, stamp_no, lane, doc_kind, subgroup) VALUES(902, 'MADE-UP PART', '2026-10-02 11:00:00', 'B-9902', 'clinic', 'bill', 'clinic_equipment');
INSERT INTO bills(id, vendor, created_at, stamp_no, lane, doc_kind) VALUES(903, 'MADE-UP PHARMA', '2026-10-02 12:00:00', 'B-9903', 'pharmacy', 'bill');
INSERT INTO bills(id, vendor, created_at, stamp_no, lane, doc_kind, subgroup) VALUES(904, 'MADE-UP STATIONERS', '2026-10-03 10:00:00', 'B-9904', 'clinic', 'challan', 'stationery');
""")
con.commit()
con.close()

app = Flask("walk624")
app.secret_key = "walk-made-up"


class AR:                                                            # the stand-in for asset_register.py
    DB_PATH = DB
    app = app
    KIND_LANE = {}
    CATEGORIES = ["Other"]

    @staticmethod
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(DB)
            g.db.row_factory = sqlite3.Row
        return g.db

    login_required = staticmethod(lambda f: f)
    owner_required = staticmethod(lambda f: f)
    checker_required = staticmethod(lambda f: f)
    can_see_price = staticmethod(lambda a: True)
    _now_ist = staticmethod(lambda: "2026-10-22 15:00:00")
    _inr = staticmethod(lambda x: "%d" % round(float(x or 0)))
    _s559_paper_href = staticmethod(lambda b: "/bills/%d" % b["id"])

    @staticmethod
    def _audit_bill(db, bid, action, detail):
        db.execute("INSERT INTO bill_audit(bill_id, action, detail) VALUES(?,?,?)", (bid, action, str(detail)))

    @staticmethod
    def asset_or_403(aid):
        return AR.get_db().execute("SELECT * FROM assets WHERE id=?", (aid,)).fetchone()


ROLE = {"role": "owner"}


@app.before_request
def _user():
    g.user = {"id": 1, "role": ROLE["role"], "username": "walk", "display_name": "Walk"}


@app.teardown_appcontext
def _close(e):
    d = g.pop("db", None)
    if d is not None:
        d.close()


app.add_url_rule("/assets/<int:aid>", "asset_view", lambda aid: "machine page")
app.add_url_rule("/bills/<int:bid>", "bill_view", lambda bid: "paper")

bat = load("batteries")
mac = load("asset_machine")
sta = load("stationery")
bat.TODAY = mac.TODAY = TODAY
sta.TODAY = TODAY
with app.app_context():
    for m in (bat, mac, sta):
        m.init(AR) if m is not bat else None
    try:
        bat.init(AR)
    except Exception as e:                                           # noqa: BLE001
        print("  (batteries.init: %s -- its tables made by ensure)" % repr(e)[:120])
        bat.AR = AR
        c = sqlite3.connect(DB)
        bat.ensure(c)
        c.close()
cl = app.test_client()


def q(sql, *p):
    c = sqlite3.connect(DB)
    r = c.execute(sql, p).fetchall()
    c.close()
    return r


def ins(table, **kv):
    """An INSERT that fills every NOT NULL column without a default with '' or 0 (the walk's rows only)."""
    c = sqlite3.connect(DB)
    for _cid, name, typ, notnull, dflt, pk in c.execute("PRAGMA table_info(%s)" % table):
        if notnull and dflt is None and not pk and name not in kv:
            kv[name] = 0 if "INT" in (typ or "").upper() or "REAL" in (typ or "").upper() else ""
    cur = c.execute("INSERT INTO %s(%s) VALUES(%s)" % (table, ",".join(kv), ",".join("?" * len(kv))), tuple(kv.values()))
    c.commit()
    rid = cur.lastrowid
    c.close()
    return rid


# ====================================================================================== F-977: batteries
def badge(fitted, war_m, life_m):
    pid = ins("battery_place", grp="gen_inv", name="WALK624 place %s %s %s" % (fitted, war_m, life_m), supplier="Made-up batteries",
              warranty_months=war_m, life_months=life_m, owner_only=0, upkeep="", active=1, payer="clinic")
    ins("battery_fit", place_id=pid, fitted_on=fitted, warranty_months=war_m, supplier="Made-up batteries", voided_at="")
    with app.test_request_context("/"):
        g.user = {"id": 1, "role": "owner", "username": "walk", "display_name": "Walk"}
        db = AR.get_db()
        p = dict(db.execute("SELECT * FROM battery_place WHERE id=?", (pid,)).fetchone())
        return bat.place_view(db, p, TODAY)["badge"]


b = badge("2024-01-01", 12, 48)
ck("B1 a battery past its warranty (fitted 01-01-2024, 12 months) shows 'Out of warranty since 01-01-2025', not OK",
   lambda: b == ("Out of warranty since 01-01-2025", "none"), lambda: b)
ck("B2 a battery inside its warranty still shows OK", lambda: badge("2026-06-01", 24, 48) == ("OK", "ok"))
ck("B3 a battery past its usual life still shows Due for replacement", lambda: badge("2020-01-01", 12, 48)[0] == "Due for replacement")
ck("B4 a warranty ending within 30 days still shows its amber line", lambda: badge("2025-11-10", 12, 48)[1] == "amber")
ck("B5 a battery with no warranty months recorded stays OK (nothing to compare)", lambda: badge("2024-01-01", None, 48) == ("OK", "ok"))

# ====================================================================================== F-978: a cover's / a part's paper afterwards
c = sqlite3.connect(DB)
c.execute("INSERT INTO asset_cover(id, asset_id, kind, provider, till_day, asset_created_at, voided_at) VALUES(1, 1, 'amc', 'Made-up AMC', '2027-07-18', '2026-10-01 10:00:00', '')")
c.execute("INSERT INTO asset_cover(id, asset_id, kind, provider, till_day, asset_created_at, voided_at) VALUES(2, 1, 'warranty', 'Made-up', '2026-12-01', '2026-10-01 10:00:00', '2026-10-05 10:00:00')")
c.execute("INSERT INTO asset_part(id, asset_id, name, asset_created_at) VALUES(1, 1, 'WALK624 detector battery', '2026-10-01 10:00:00')")
c.commit()
c.close()


def folds():
    with app.test_request_context("/assets/1"):
        g.user = {"id": 1, "role": "owner", "username": "walk", "display_name": "Walk"}
        return str(mac.sections(AR.asset_or_403(1))[1])


f0 = folds()
ck("M1 the cover without its paper shows a 'link' box (B-____) to its paper", lambda: "/assets/1/covers/1/paper" in f0)
ck("M8 a voided cover shows no link box", lambda: "/assets/1/covers/2/paper" not in f0)
r = cl.post("/assets/1/covers/1/paper", data={"paper": "B-9901"})
ck("M2 linking B-9901 to the cover: stored with its fingerprint, the page then shows B-9901 as its paper",
   lambda: r.status_code == 302 and q("SELECT bill_id, bill_created_at FROM asset_cover WHERE id=1") == [(901, "2026-10-02 10:00:00")]
   and ">B-9901<" in folds() and "/assets/1/covers/1/paper" not in folds(), lambda: (r.status_code, q("SELECT bill_id FROM asset_cover WHERE id=1")))
r = cl.post("/assets/1/covers/1/paper", data={"paper": "B-9902"})
ck("M3 a second link on the same cover is refused; it keeps B-9901",
   lambda: r.status_code == 302 and q("SELECT bill_id FROM asset_cover WHERE id=1") == [(901,)])
r = cl.post("/assets/1/covers/2/paper", data={"paper": "B-9902"})
ck("M4 a voided cover refuses a paper", lambda: q("SELECT bill_id FROM asset_cover WHERE id=2") == [(None,)])
r = cl.post("/assets/1/parts/1/paper", data={"paper": "B-9903"})
ck("M5 a pharmacy paper is refused on a part (nothing saved)", lambda: q("SELECT bill_id FROM asset_part WHERE id=1") == [(None,)])
ck("M6 the part without its paper shows a 'link' box", lambda: "/assets/1/parts/1/paper" in folds())
r = cl.post("/assets/1/parts/1/paper", data={"paper": "B-9902"})
ck("M7 linking B-9902 to the part: stored with its fingerprint and audited on the paper",
   lambda: q("SELECT bill_id, bill_created_at FROM asset_part WHERE id=1") == [(902, "2026-10-02 11:00:00")]
   and q("SELECT COUNT(*) FROM bill_audit WHERE bill_id=902 AND action='machine_link'") == [(1,)])
c = sqlite3.connect(DB)
c.execute("INSERT INTO asset_part(id, asset_id, name, removed_on, asset_created_at) VALUES(2, 1, 'WALK624 old part', '2026-10-10', '2026-10-01 10:00:00')")
c.commit()
c.close()
r = cl.post("/assets/1/parts/2/paper", data={"paper": "B-9901"})
f9 = folds()
ck("M10 a removed part: no link box, and a forged link is refused (nothing saved); the route exists (302, not 404)",
   lambda: r.status_code == 302 and q("SELECT bill_id FROM asset_part WHERE id=2") == [(None,)] and "/assets/1/parts/2/paper" not in f9, lambda: r.status_code)
ck("M9 the spends' own link box is unchanged (still there for a spend with no paper)",
   lambda: "s557_spend_paper" in open(os.path.join(APPD, "asset_machine.py"), encoding="utf-8").read())

# ====================================================================================== F-979: stationery packets
with app.test_request_context("/"):
    g.user = {"id": 1, "role": "owner", "username": "walk", "display_name": "Walk"}
    db = AR.get_db()
    tok, _m = sta.add_item(db, "WALK624 Token", "packet of 100", 120, None, "walk")
    pen, _m = sta.add_item(db, "WALK624 Pen", "piece", 10, None, "walk")
    db.commit()
    b4 = db.execute("SELECT * FROM bills WHERE id=904").fetchone()
    w1 = sta.save_lines(db, b4, [{"no": 1, "name": "Token plain", "qty": "100", "unit": "", "rate": 120, "item": str(tok)},
                                  {"no": 2, "name": "Pen", "qty": "100", "unit": "", "rate": 10, "item": str(pen)}], "walk")
    db.commit()
    inv1 = {r["name"]: r for r in sta.inventory(db, "2026-10")["rows"]}
    w2 = sta.save_lines(db, b4, [{"no": 1, "name": "Token plain", "qty": "1", "unit": "", "rate": 120, "item": str(tok)},
                                  {"no": 2, "name": "Pen", "qty": "100", "unit": "", "rate": 10, "item": str(pen)}], "walk")
    db.commit()
    inv2 = {r["name"]: r for r in sta.inventory(db, "2026-10")["rows"]}
    w3 = sta.save_lines(db, b4, [{"no": 1, "name": "Token plain", "qty": "100", "unit": "packets", "rate": 120, "item": str(tok)}], "walk")
    db.rollback()
    w4 = sta.save_lines(db, b4, [{"no": 1, "name": "Token plain", "qty": "150", "unit": "", "rate": 120, "item": str(tok)}], "walk")
    db.rollback()
    w5 = sta.save_lines(db, b4, [{"no": 1, "name": "Token plain", "qty": "200", "unit": "pcs", "rate": 120, "item": str(tok)}], "walk")
    db.rollback()
ck("S1 a line of 100 for an item counted in packets of 100: the Save's words say 'type 1 instead'",
   lambda: "Check:" in w1[0] and "type 1 instead" in w1[0], lambda: w1)
ck("S2 corrected to 1: no check in the Save's words", lambda: "Check:" not in w2[0], lambda: w2)
ck("S3 a line that itself says packets is not questioned", lambda: "Check:" not in w3[0], lambda: w3)
ck("S4 the owner's Stationery page marks the item while the 100 stands ('check the quantity (B-9904)'), and only that item",
   lambda: inv1["WALK624 Token"].get("pack") == ["B-9904"] and not inv1["WALK624 Pen"].get("pack"), lambda: (inv1["WALK624 Token"].get("pack"),))
ck("S8 150 (not a whole number of packets) is not questioned; 200 'pcs' is (type 2)", lambda: "Check:" not in w4[0] and "type 2 instead" in w5[0], lambda: (w4, w5))
ck("S5 the mark goes once the line is 1", lambda: not inv2["WALK624 Token"].get("pack"))
ck("S6 the page's template carries the mark", lambda: "s624pack" in sta.STOCK_TPL)
ck("S7 the stock arithmetic is unchanged (the line still counts what was typed)", lambda: inv1["WALK624 Token"]["stock"] == 100 and inv2["WALK624 Token"]["stock"] == 1)

shutil.rmtree(work, ignore_errors=True)
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S624 CONTROL (FROM files): %d red; must-red red: %s; %s" % (len(red), all(not RES.get(k, True) for k in MUST_RED),
                                                                          "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S624: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
