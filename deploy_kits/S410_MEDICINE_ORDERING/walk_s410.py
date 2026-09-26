#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s410.py -- kit S410_MEDICINE_ORDERING. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over a
SCRATCH COPY of finance.db; its own suppliers and items keyed W410*; 'today' is set (ORDER_TODAY = Monday 28-Sep-2026); the Web Push
goes to a stub file (ORDER_PUSH_STUB), never to a phone; no WhatsApp opens (the wa.me link is only returned). The real 90 days are
read as a read-only check. Never the live database.

  --app NEW --old OLD --db PATH
"""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []
W = os.path.dirname(os.path.abspath(a.db))
TODAY = dt.date(2026, 9, 28)                                  # a Monday
PUSH = os.path.join(W, "push410.jsonl")
for f in (PUSH,):
    if os.path.exists(f):
        os.remove(f)


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:420] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


# the SCRATCH copy starts as the box BEFORE S410 whatever the box holds now (a re-run after the install): the kit's tables, its
# settings and S403's approval row are cleared here -- the seed below rebuilds them exactly as a first install would
db = sqlite3.connect(a.db)
db.row_factory = sqlite3.Row
for t in ("order_supplier_rule", "order_rule_audit", "order_holiday", "order_item_rule", "order_proposal", "order_notice"):
    db.execute("DROP TABLE IF EXISTS %s" % t)
db.execute("DELETE FROM setting WHERE key LIKE 'order.%' OR key='porders.rules_approved'")
db.commit()
db.close()
copydb(a.db, a.db + ".old")
os.environ["ORDER_TODAY"] = TODAY.isoformat()
os.environ["PORDERS_SOURCE"] = "tables"
sys.path.insert(0, a.app)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FINANCE_DIR"] = a.app
os.environ["FINANCE_DB"] = a.db

# ---------------------------------------------------------------- the fixture (own rows, by key)
db = sqlite3.connect(a.db)
db.row_factory = sqlite3.Row
D = lambda k: (TODAY - dt.timedelta(days=k)).isoformat()      # noqa: E731
NOW = dt.datetime.now().replace(microsecond=0).isoformat()
for t, col in (("purchase_bill", "bill_no"), ("purchase_line", "bill_no"), ("sale_line_item", "bill_no")):
    db.execute("DELETE FROM %s WHERE %s LIKE 'W410%%'" % (t, col))
db.execute("DELETE FROM stock_snapshot WHERE item LIKE 'W410%'")
db.execute("DELETE FROM purchase_vendor_contact WHERE vendor_norm LIKE 'W410%'")
db.execute("DELETE FROM purchase_export WHERE md5 LIKE 'w410%'")
for oid, in db.execute("SELECT id FROM purchase_order WHERE vendor LIKE 'W410%'").fetchall():
    db.execute("DELETE FROM purchase_order_line WHERE order_id=?", (oid,))
db.execute("DELETE FROM purchase_order WHERE vendor LIKE 'W410%'")
db.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES ('w410exp','ITEMWISE','w410','2026-06-01','2026-09-30','w410',?,0,0)", (NOW,))
db.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES ('w410bw','BILLWISE','w410','2026-06-01','2026-09-30','w410',?,0,0)", (NOW,))
SUP = {"W410 WEEKLY CO": [(k, 300000) for k in (85, 75, 65, 55, 45, 35, 25, 15, 5)] + [(6, 800000), (3, 800000)],
       "W410 FORT CO": [(k, 100000) for k in (60, 46, 32, 18)],
       "W410 RARE CO": [(70, 1500000), (20, 1500000)],
       "W410 SMALL CO": [(k, 50000) for k in (85, 75, 65, 55, 45, 35, 25, 15, 5)],
       "W410 MONTH CO": [(65, 500000), (35, 500000), (5, 500000)]}
bn = 0
for sup, bills in SUP.items():
    for k, amt in bills:
        bn += 1
        db.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, date_src) VALUES (?,?,?,?,?,?,?,?)",
                   (sup, sup, "W410B%03d" % bn, D(k), D(k)[:7], amt, "w410bw", "BILLWISE"))
    db.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, phone, updated_at, source) VALUES (?,?,?,?,?)", (sup, sup, "9" + "8" * 9, NOW, "walk"))
LINES = [  # item, supplier, days ago, qty strips, rate_p per strip
    ("W410 ITEM A", "W410 RARE CO", 20, 20, 5000), ("W410 ITEM A", "W410 WEEKLY CO", 5, 20, 5000),
    ("W410 ITEM B", "W410 RARE CO", 70, 10, 4000), ("W410 ITEM B", "W410 FORT CO", 18, 10, 4000),
    ("W410 KEDAR K", "KEDAR PHARMACEUTICAL", 5, 10, 8000),
    ("W410 ITEM C", "W410 MONTH CO", 5, 10, 6000),
    ("W410 ITEM D", "W410 WEEKLY CO", 5, 5, 100),
    ("W410 ITEM E", "W410 SMALL CO", 5, 10, 2000),
    ("W410 ITEM F", "W410 WEEKLY CO", 40, 5, 3000),
    ("W410 ITEM G", "W410 WEEKLY CO", 40, 2, 30000),
    ("W410 NEW ITEM", "W410 WEEKLY CO", 8, 3, 12000),
    ("W410 OOS ITEM", "W410 WEEKLY CO", 40, 2, 3000),
]
for i, (item, sup, k, qty, rate) in enumerate(LINES, 1):
    db.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, rate_p, amount_p, net_rate_p, net_amount_p, loose_qty, purchase_rate_p, direction, source_md5, line_type) "
               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (sup, "W410L%03d" % i, D(k), D(k)[:7], item, "1*10", qty, 0, rate, qty * rate, rate // 10, qty * rate, qty * 10, rate, "PURCHASE", "w410exp", "ITEMWISE"))
AS_ON = max({r[0] for r in db.execute("SELECT DISTINCT as_on FROM stock_snapshot")}, key=lambda s: (s[6:], s[3:5], s[:2]))
for item, qty in (("W410 ITEM A", 30), ("W410 ITEM B", 40), ("W410 KEDAR K", 10), ("W410 ITEM C", 20), ("W410 ITEM D", 1), ("W410 ITEM E", 5), ("W410 ITEM F", 12), ("W410 ITEM G", 3), ("W410 NEW ITEM", 10), ("W410 OOS ITEM", 0)):
    db.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,?)", (AS_ON, item, qty, "1*10", 10, NOW, "walk"))
eid = db.execute("SELECT id FROM day_entry WHERE unit='medical' ORDER BY business_date DESC LIMIT 1").fetchone()[0]
sn = 0
for item, raw in (("W410 ITEM A", "5:0"), ("W410 ITEM B", "2:0"), ("W410 KEDAR K", "1:0"), ("W410 ITEM C", "1:0"), ("W410 ITEM D", "0:1"), ("W410 ITEM E", "1:0")):
    for k in range(1, 28):
        sn += 1
        db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical',?,?,0,1,?,?,'1*10',?,1000)",
                   (eid, D(k), "W410S%04d" % sn, item, item, raw))
db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical',?,'W410SG',0,1,'W410 ITEM G','W410 ITEM G','1*10','1:0',30000)", (eid, D(10)))
db.execute("INSERT OR REPLACE INTO purchase_salt_marg (item_norm, item, salt, as_on, source_md5) VALUES ('W410 NEW ITEM','W410 NEW ITEM','W410 SALT',?, 'w410exp')", (D(8),))
cur = db.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note, total_p, received_at, received_by, sent_by, section) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (D(3) + "T10:00:00", "darpan", "W410 WEEKLY CO", "received", "whatsapp", 6000, D(2) + "T18:00:00", "darpan", "darpan", "Medicines"))
db.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units, rate_p, value_p, on_hand, supplied, short, missing, arrived_by, arrived_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
           (cur.lastrowid, "W410 OOS ITEM", 2, 10, 20, 3000, 6000, 0, 0, 1, 1, "darpan", D(2) + "T18:00:00"))
db.commit()
db.close()
import seed_s410  # noqa: E402
assert seed_s410.seed(a.db) == 0, "seed failed"
print("-- scratch copies made; %d crafted bills, %d lines, %d sale rows, 10 snapshot rows, 5 suppliers with a runtime phone; seeded (go-live %s)" % (bn, len(LINES), sn + 1, TODAY))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
T = dt.date(2026, 9, 28)
def today(d): os.environ["ORDER_TODAY"] = d.isoformat()
out = {"mounted": "order_rules" in fa.app.blueprints}
out["rules_state_gate"] = {u: G(u, "/finance/porders/api/rules/state")[0] for u in ("manoj", "darpan", "bhati", "amir")}
out["day_gate"] = {u: G(u, "/finance/porders/api/day")[0] for u in ("shavez", "bhati", "amir")}
st = G("darpan", "/finance/porders/api/state")[1]
out["state_today"] = ("today" in st, (st.get("today") or {}).get("ok"), bool(st.get("meds")))
out["tables"] = {t: has(t) for t in ("order_supplier_rule", "order_proposal", "order_holiday", "order_item_rule", "order_notice")}
out["needs0"] = [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", [])]
kal = G("darpan", "/finance/darpan/kal/api/day?date=2026-09-25")[1]
out["kal0"] = [kal.get("ok"), "orders_today" in kal]
if not NEW:
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
import order_rules as orr, purchase_app as pa
# --- the seed: the rhythm, the tiers, Kedar, the real 90 days
R = {r["supplier_norm"]: r for r in q("SELECT * FROM order_supplier_rule")}
out["seed"] = {k: [R[k]["cadence"], R[k]["order_days"], R[k]["blocked_days"], R[k]["lead_days"], R[k]["cover_cap_days"], R[k]["single_source_extra"], (R[k]["cadence_how"] or "")[:12]] for k in ("W410 WEEKLY CO", "W410 FORT CO", "W410 RARE CO", "W410 SMALL CO", "W410 MONTH CO", "KEDAR PHARMACEUTICAL") if k in R}
out["seed_real"] = {k: [R[k]["cadence"], R[k]["order_days"]] for k in ("L.K. DRUG HOUSE", "GUNINA PHARMACEUTICALS PVT LTD", "KEDAR PHARMACEUTICAL") if k in R}
out["seed_n"] = len(R); out["yuvika"] = "YUVIKA SURGICALS" in R
out["kedar_review_on"] = R["KEDAR PHARMACEUTICAL"]["review_on"]
out["settings"] = q("SELECT key, value FROM setting WHERE key IN ('order.go_live','order.interim_from','order.blocked_days','order.min_order_p')")
out["words_kedar"] = orr.rule_words(db, R["KEDAR PHARMACEUTICAL"]); out["words_weekly"] = orr.rule_words(db, R["W410 WEEKLY CO"])
# an owner-set cadence survives a re-seed
out["set_fort"] = P("manoj", "/finance/porders/api/rules/set", {"supplier": "W410 FORT CO", "field": "cadence", "value": "monthly"})
out["set_darpan"] = P("darpan", "/finance/porders/api/rules/set", {"supplier": "W410 FORT CO", "field": "cadence", "value": "weekly"})[0]
orr.reseed(db, T, "walk-reseed")
out["fort_after_reseed"] = q("SELECT cadence, owner_fields FROM order_supplier_rule WHERE supplier_norm='W410 FORT CO'")[0]
P("manoj", "/finance/porders/api/rules/set", {"supplier": "W410 FORT CO", "field": "cadence", "value": "fortnightly"})
out["audit_n"] = q("SELECT COUNT(*) AS n FROM order_rule_audit WHERE supplier_norm='W410 FORT CO'")[0]["n"]
# --- the calendar
R = {r["supplier_norm"]: r for r in q("SELECT * FROM order_supplier_rule")}
D2 = lambda ds: [d.isoformat() for d in ds]
out["cal_weekly"] = D2(orr.order_days_between(db, R["W410 WEEKLY CO"], T, T + dt.timedelta(days=14)))
out["cal_kedar"] = D2(orr.order_days_between(db, R["KEDAR PHARMACEUTICAL"], T, T + dt.timedelta(days=14)))
out["cal_fort"] = D2(orr.order_days_between(db, R["W410 FORT CO"], T, T + dt.timedelta(days=28)))
out["cal_month"] = D2(orr.order_days_between(db, R["W410 MONTH CO"], T, T + dt.timedelta(days=40)))
thu = dict(R["W410 SMALL CO"], order_days="THU"); out["cal_thu_blocked"] = D2(orr.order_days_between(db, thu, T, T + dt.timedelta(days=6)))
thuk = dict(R["KEDAR PHARMACEUTICAL"], order_days="THU"); out["cal_thu_kedar"] = D2(orr.order_days_between(db, thuk, T, T + dt.timedelta(days=6)))
sun = dict(R["W410 SMALL CO"], order_days="SUN", blocked_days=""); out["cal_sun"] = D2(orr.order_days_between(db, sun, T, T + dt.timedelta(days=6)))
out["hol_add"] = P("shavez", "/finance/porders/api/rules/holiday", {"day": "2026-10-05", "note": "walk chhutti"})[0]
out["hol_bhati"] = P("bhati", "/finance/porders/api/rules/holiday", {"day": "2026-10-06", "note": "x"})[0]
out["cal_weekly_hol"] = D2(orr.order_days_between(db, R["W410 WEEKLY CO"], T, T + dt.timedelta(days=14)))
out["next_month_hol"] = orr.next_order_day(db, R["W410 MONTH CO"], T).isoformat()
P("shavez", "/finance/porders/api/rules/holiday", {"day": "2026-10-05", "remove": True})
out["cover"] = [orr.cover_days(db, R["W410 WEEKLY CO"], False), orr.cover_days(db, R["W410 WEEKLY CO"], True), orr.cover_days(db, R["KEDAR PHARMACEUTICAL"], True), orr.cover_days(db, R["W410 FORT CO"], False), orr.cover_days(db, R["W410 FORT CO"], True), orr.gap_days(R["KEDAR PHARMACEUTICAL"])]
# --- the plan on Monday 28-Sep; interim from the start for the walk
db.execute("UPDATE setting SET value='2026-09-01' WHERE key='order.interim_from'"); db.commit()
pl = orr.plan(db, T)
def L(v, item):
    x = pl["vendors"].get(v); return next((l for l in (x["lines"] if x else []) if l["item"] == item), None)
def q10(per_day, cov, on_hand, pack=10):
    import math
    need = per_day * cov - on_hand
    return 0 if need <= 0 else max(10, int(math.ceil(math.ceil(need / float(pack)) / 10.0)) * 10)
A, B, K, Dd, E = L("W410 WEEKLY CO", "W410 ITEM A"), L("W410 FORT CO", "W410 ITEM B"), L("KEDAR PHARMACEUTICAL", "W410 KEDAR K"), L("W410 WEEKLY CO", "W410 ITEM D"), L("W410 SMALL CO", "W410 ITEM E")
out["plan_A"] = [A and A["cover_days"], A and A["qty"], A and q10(A["per_day"], A["cover_days"], A["on_hand"]), A and A["per_day"]]
out["plan_B"] = [B and B["cover_days"], B and B["qty"], B and q10(B["per_day"], B["cover_days"], B["on_hand"])]
out["plan_K"] = [K and K["cover_days"], K and K["qty"], K and q10(K["per_day"], K["cover_days"], K["on_hand"])]
out["plan_D"] = Dd
out["plan_small"] = [E and E["qty"], (pl["vendors"].get("W410 SMALL CO") or {}).get("held"), (pl["vendors"].get("W410 SMALL CO") or {}).get("total_p")]
out["plan_carried"] = [l["item"] for l in pl["vendors"]["W410 WEEKLY CO"]["lines"] if "carried" in " ".join(l["why"])]
out["plan_yuvika"] = any(v.get("vendor_norm") == "YUVIKA SURGICALS" for v in pl["vendors"].values())
ip = orr.interim_plan(db, T)
Cc = next((l for l in (ip["vendors"].get("W410 MONTH CO") or {}).get("lines", []) if l["item"] == "W410 ITEM C"), None)
out["interim_C"] = [Cc and Cc["qty"], Cc and Cc["cover_days"], (ip["vendors"].get("W410 MONTH CO") or {}).get("next_order_day"), sorted(ip["vendors"].keys())]
db.execute("UPDATE setting SET value='2026-10-10' WHERE key='order.interim_from'"); db.commit()
out["interim_off_before"] = orr.interim_plan(db, T).get("off")
db.execute("UPDATE setting SET value='2026-09-01' WHERE key='order.interim_from'"); db.commit()
out["interim_thu"] = sorted(orr.interim_plan(db, dt.date(2026, 10, 1))["vendors"].keys())
out["interim_sun"] = sorted(orr.interim_plan(db, dt.date(2026, 10, 4))["vendors"].keys())
out["interim_sat"] = sorted(orr.interim_plan(db, dt.date(2026, 10, 3))["vendors"].keys())
out["interim_wed"] = sorted(orr.interim_plan(db, dt.date(2026, 9, 30))["vendors"].keys())
# --- 09:00: the day prepared, the first notice; the reminders; sending
os.environ["ORDER_TICK"] = "prepare"; tk = orr.tick(db); out["tick_prepare"] = [tk["slot"], tk["made"], (tk.get("notice") or {}).get("text"), sorted(((tk.get("notice") or {}).get("sent") or {}).keys())]
props = q("SELECT id, supplier_norm, kind, status, reason, total_p FROM order_proposal WHERE day=? ORDER BY id", T.isoformat())
out["props"] = [[p["supplier_norm"], p["kind"], p["status"]] for p in props]
pid = {p["supplier_norm"] + "/" + p["kind"]: p["id"] for p in props}
os.environ["ORDER_TICK"] = "remind12"; out["remind12"] = (orr.tick(db).get("notice") or {}).get("text")
d0 = G("shavez", "/finance/porders/api/day")[1]; out["day_api"] = [d0["n"], d0["sent"], d0["unsent"], d0["text"], [p["kind_hi"] for p in d0["proposals"] if p["kind"] == "interim"]]
wk = pid["W410 WEEKLY CO/fixed"]
lines0 = json.loads(q("SELECT lines FROM order_proposal WHERE id=?", wk)[0]["lines"])
edit = [dict(item=l["item"], qty=(l["qty"] - 10 if l["item"] == "W410 ITEM A" else l["qty"])) for l in lines0 if l["item"] != "W410 ITEM G"]
out["send_before_rules"] = P("darpan", "/finance/porders/api/day/send", {"proposal_id": wk, "lines": edit})
out["send_before_rules"] = [out["send_before_rules"][0], (out["send_before_rules"][1] or {}).get("error")]
out["approve"] = P("manoj", "/finance/porders/api/rules/approve")[0]
out["send_bhati"] = P("bhati", "/finance/porders/api/day/send", {"proposal_id": wk, "lines": edit})[0]
s1 = P("darpan", "/finance/porders/api/day/send", {"proposal_id": wk, "lines": edit}); out["send1"] = [s1[0], bool((s1[1] or {}).get("wa_url")), (s1[1] or {}).get("by"), (s1[1] or {}).get("lines")]
oid = (s1[1] or {}).get("order_id")
out["order1"] = q("SELECT vendor, status, section, sent_by FROM purchase_order WHERE id=?", oid) + q("SELECT item, packs FROM purchase_order_line WHERE order_id=? ORDER BY item", oid)
out["prop1"] = q("SELECT status, sent_by, sent_order_id FROM order_proposal WHERE id=?", wk)
out["send_again"] = P("darpan", "/finance/porders/api/day/send", {"proposal_id": wk, "lines": edit}); out["send_again"] = [out["send_again"][0], (out["send_again"][1] or {}).get("already")]
ia_ = orr.interim_plan(db, dt.date(2026, 9, 30))["vendors"]
out["interim_after_send"] = [sorted(x for x in ia_ if x.startswith("W410")), sorted(l["item"] for l in (ia_.get("W410 WEEKLY CO") or {}).get("lines", []))]
out["plan_after_send"] = [l["why"][-1] for l in orr.plan(db, dt.date(2026, 9, 30))["vendors"].get("W410 WEEKLY CO", {}).get("lines", []) if l["item"] == "W410 ITEM A"]
os.environ["ORDER_TICK"] = "remind15"; out["remind15"] = (orr.tick(db).get("notice") or {}).get("text")
kal = G("darpan", "/finance/darpan/kal/api/day?date=2026-09-25")[1]; out["kal_card"] = kal.get("orders_today")
# the freeze
out["freeze_on"] = P("manoj", "/finance/porders/api/rules/freeze", {"on": True, "reason": "walk: stock count chal raha hai"})
out["send_frozen"] = P("shavez", "/finance/porders/api/day/send", {"proposal_id": pid["KEDAR PHARMACEUTICAL/fixed"]})
out["send_frozen"] = [out["send_frozen"][0], (out["send_frozen"][1] or {}).get("error"), (out["send_frozen"][1] or {}).get("message")]
out["send_med_frozen"] = P("darpan", "/finance/porders/api/send_med", {"vendor": "W410 WEEKLY CO"})[0]
st = G("shavez", "/finance/porders/api/state")[1]; out["state_frozen"] = ((st.get("today") or {}).get("frozen") or {}).get("reason")
out["needs_frozen"] = [l["text"] for l in G("manoj", "/finance/sanjeevni/api/needs-you")[1]["lines"] if "frozen" in l["text"]]
out["freeze_off"] = P("manoj", "/finance/porders/api/rules/freeze", {"on": False})[1]
out["send_kedar"] = P("shivani", "/finance/porders/api/day/send", {"proposal_id": pid["KEDAR PHARMACEUTICAL/fixed"]})[0]
out["send_interim"] = P("alisha", "/finance/porders/api/day/send", {"proposal_id": pid["W410 MONTH CO/interim"]})
out["send_interim"] = [out["send_interim"][0], q("SELECT note, section FROM purchase_order WHERE id=?", (out["send_interim"][1] or {}).get("order_id") or -1)]
os.environ["ORDER_TICK"] = "remind17"; r17 = orr.tick(db); out["remind17"] = [(r17.get("notice") or {}).get("text"), (r17.get("notice") or {}).get("silent")]
out["notices"] = q("SELECT slot, text FROM order_notice WHERE day=? ORDER BY slot", T.isoformat())
pushes = [json.loads(x) for x in open(os.environ["ORDER_PUSH_STUB"], encoding="utf-8") if x.strip()]
out["pushes"] = [len(pushes), sorted({p["user"] for p in pushes}), pushes[0]["payload"]["url"] if pushes else None, pushes[0]["payload"]["body"][:40] if pushes else None, any(re.search(r"\b[6-9]\d{9}\b", json.dumps(p)) for p in pushes)]
# the silence: every proposal of the day marked sent (in the scratch), the 17:00 row cleared, the slot ticked again -> silent, no push
os.environ["ORDER_TICK"] = "remind12"; out["already12"] = (orr.tick(db).get("notice") or {}).get("already")
still = [r["id"] for r in q("SELECT id FROM order_proposal WHERE day=? AND status='open'", T.isoformat())]
db.execute("UPDATE order_proposal SET status='sent' WHERE day=? AND status='open'", (T.isoformat(),)); db.execute("DELETE FROM order_notice WHERE day=? AND slot='1700'", (T.isoformat(),)); db.commit()
os.environ["ORDER_TICK"] = "remind17"; s17 = orr.tick(db).get("notice") or {}
out["silent17"] = [s17.get("silent"), len(q("SELECT id FROM order_notice WHERE day=? AND slot='1700'", T.isoformat())), len([1 for x in open(os.environ["ORDER_PUSH_STUB"], encoding="utf-8") if x.strip()])]
for i in still:
    db.execute("UPDATE order_proposal SET status='open' WHERE id=?", (i,))
db.commit()
# FORT CO is left unsent: the merge, the Needs-you line on its next order day, the carry into that day's proposal
os.environ.pop("ORDER_TICK", None)
out["nightly"] = orr.nightly(db, dt.date(2026, 9, 29), "walk")
out["merged"] = q("SELECT status, merged_into FROM order_proposal WHERE id=?", pid["W410 FORT CO/fixed"])
today(dt.date(2026, 10, 5)); out["needs_oct5"] = [l["text"] for l in G("manoj", "/finance/sanjeevni/api/needs-you")[1]["lines"] if l["text"].startswith("Order not sent: W410 Fort")]
today(dt.date(2026, 10, 12)); out["needs_oct12"] = [l["text"] for l in G("manoj", "/finance/sanjeevni/api/needs-you")[1]["lines"] if l["text"].startswith("Order not sent: W410 Fort")]
orr.prepare_day(db, dt.date(2026, 10, 12), "walk")
p12 = q("SELECT id, carried_from, status FROM order_proposal WHERE day='2026-10-12' AND supplier_norm='W410 FORT CO'")
out["carried_into"] = p12
if p12:
    P("darpan", "/finance/porders/api/day/send", {"proposal_id": p12[0]["id"]})
out["merged_after_send"] = q("SELECT status FROM order_proposal WHERE id=?", pid["W410 FORT CO/fixed"])
out["needs_oct12b"] = [l["text"] for l in G("manoj", "/finance/sanjeevni/api/needs-you")[1]["lines"] if l["text"].startswith("Order not sent: W410 Fort")]
today(T)
# --- Needs you: the month above pace; the Kedar review with the boxes figure and the one tap; nothing else
NL = lambda: [l for l in G("manoj", "/finance/sanjeevni/api/needs-you")[1]["lines"]]
out["spend"] = [l["text"] for l in NL() if "above its 90-day pace" in l["text"]]
db.execute("UPDATE order_supplier_rule SET review_on='2026-09-28' WHERE supplier_norm='KEDAR PHARMACEUTICAL'"); db.execute("UPDATE setting SET value='2026-09-01' WHERE key='order.go_live'"); db.commit()
rv = [l for l in NL() if l.get("review_supplier")]
out["review_line"] = [len(rv), rv[0]["text"] if rv else None, rv[0].get("review_target") if rv else None, int(re.search(r"peak of (\d+) boxes", rv[0]["text"]).group(1)) if rv and re.search(r"peak of (\d+) boxes", rv[0]["text"]) else None]
out["move_weekly"] = P("manoj", "/finance/porders/api/rules/set", {"supplier": "KEDAR PHARMACEUTICAL", "field": "move_to", "value": "weekly"})[1]
out["kedar_after"] = q("SELECT cadence, order_days, review_on FROM order_supplier_rule WHERE supplier_norm='KEDAR PHARMACEUTICAL'")
out["review_gone"] = [l["text"] for l in NL() if l.get("review_supplier")]
P("manoj", "/finance/porders/api/rules/set", {"supplier": "KEDAR PHARMACEUTICAL", "field": "move_to", "value": "custom"})
out["kedar_back"] = q("SELECT cadence, order_days FROM order_supplier_rule WHERE supplier_norm='KEDAR PHARMACEUTICAL'")
out["needs_other"] = [l["text"] for l in NL() if l.get("target") == "porders" and not any(w in l["text"] for w in ("Order not sent", "above its 90-day pace", "Kedar review", "frozen", "This week", "Orthotic", "Bill scan", "Buying rules"))]
# --- Out of stock both ends; New items; the candidates and the tick
o1 = G("manoj", "/finance/porders/api/oos")[1]; oo = next((x for x in o1["items"] if x["item"] == "W410 OOS ITEM"), None)
out["oos1"] = [o1["n"] >= 1, oo and oo["qty"], oo and oo["vendor_short"], oo and oo["said_no"]]
db.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, rate_p, amount_p, loose_qty, purchase_rate_p, direction, source_md5, line_type) VALUES ('W410 FORT CO','W410LX',?,?,'W410 OOS ITEM','1*10',2,0,3000,6000,20,3000,'PURCHASE','w410exp','ITEMWISE')", (T.isoformat(), T.isoformat()[:7])); db.commit()
o2 = G("manoj", "/finance/porders/api/oos")[1]; out["oos2"] = any(x["item"] == "W410 OOS ITEM" for x in o2["items"])
out["oos_gate"] = G("darpan", "/finance/porders/api/oos")[0]
ni = G("manoj", "/finance/porders/api/new-items?month=2026-09")[1]; nw = next((x for x in ni["items"] if x["item"] == "W410 NEW ITEM"), None)
out["new_items"] = [ni["n"] >= 1, nw and [nw["salt"], nw["supplier_short"], nw["manufacturer"], nw["mrp"], nw["rate_rs"], nw["first_text"]], any(x["item"] == "W410 ITEM F" for x in ni["items"]), any(x["manufacturer"] not in ("", "not in export") for x in ni["items"])]
rs = G("manoj", "/finance/porders/api/rules/state")[1]
out["cands"] = [any(x["item"] == "W410 ITEM F" for x in rs["candidates"]["never"]), any(x["item"] == "W410 ITEM G" for x in rs["candidates"]["on_demand"]), rs["oos_n"], rs["new_items_n"], len(rs["rules"]), rs["rules"][0]["supplier_norm"]]
RJ = os.path.join(APP, "spine", "order_rules.json"); rj0 = open(RJ, "rb").read()          # restored below: the walk dir is shared with the earlier kits' walks
out["tick_A"] = P("manoj", "/finance/porders/api/rules/item", {"item": "W410 ITEM A", "rule": "never", "on": True})[0]
lists = json.load(open(RJ)); out["lists"] = ["W410 ITEM A" in lists["never_reorder"], lists["version"], lists.get("orthotics_cycle"), sorted(lists.keys())]
pl2 = orr.plan(db, dt.date(2026, 10, 19))
out["A_held"] = [any(l["item"] == "W410 ITEM A" for v in pl2["vendors"].values() for l in v["lines"]), any(h["item"] == "W410 ITEM A" for h in pl2["held_items"])]
P("manoj", "/finance/porders/api/rules/item", {"item": "W410 ITEM A", "rule": "never", "on": False})
lists2 = json.load(open(RJ)); out["lists2"] = "W410 ITEM A" in lists2["never_reorder"]
open(RJ, "wb").write(rj0)
out["keep"] = P("manoj", "/finance/porders/api/rules/item", {"item": "W410 ITEM F", "rule": "keep", "on": True, "value": 50})[0]
out["item_gate"] = P("darpan", "/finance/porders/api/rules/item", {"item": "W410 ITEM F", "rule": "never", "on": True})[0]
# --- the pages
out["staff_page"] = ("sendDay" in G("darpan", "/finance/porders")[1], "Aaj ke order" in G("darpan", "/finance/porders")[1])
op = G("manoj", "/finance/approvals")[1]; out["owner_page"] = ("oosBar" in op, "loadPOOos" in op, "New items this month" in op, "Approve rules" in op)
out["leak"] = bool(re.search(r"\b[6-9]\d{9}\b", json.dumps([out["day_api"], out["send1"], out["kal_card"], op[:200000]])))
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1",
               ORDER_PUSH_STUB=PUSH, ORDER_TODAY=TODAY.isoformat(), PORDERS_SOURCE="tables")
    env.pop("ORDER_TICK", None)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, "old", a.db + ".old")
N = probe(a.app, "new", a.db)

print("-- 1  the module, the gates, the seed (the rhythm, the tiers, Kedar's row, an owner-set value survives)")
check("order_rules is mounted under the porders unit; the owner reads the rules state (200), darpan / bhati / amir cannot; the staff read the day (shavez 200; bhati and amir hold no porders row, refused); state() carries today",
      N["mounted"] and N["rules_state_gate"]["manoj"] == 200 and N["rules_state_gate"]["darpan"] == 403 and N["rules_state_gate"]["bhati"] in (302, 403) and N["rules_state_gate"]["amir"] in (302, 403)
      and N["day_gate"]["shavez"] == 200 and N["day_gate"]["bhati"] in (302, 403) and N["day_gate"]["amir"] in (302, 403) and N["state_today"] == [True, True, True], (N["rules_state_gate"], N["day_gate"], N["state_today"]))
s = N["seed"]
check("cadence from the shop's rhythm: 9 bill days 10 apart -> weekly; 4 bill days 14 apart -> fortnightly (nearest, not up); 2 bills -> the money tier (₹10,000 a month -> fortnightly); 3 bills 30 apart -> monthly; blocked SUN,THU; lead 1",
      s["W410 WEEKLY CO"][0] == "weekly" and s["W410 FORT CO"][0] == "fortnightly" and s["W410 FORT CO"][6] == "rhythm: 4 bi" and s["W410 RARE CO"][0] == "fortnightly" and s["W410 RARE CO"][6] == "money tier (" and s["W410 MONTH CO"][0] == "monthly"
      and s["W410 SMALL CO"][0] == "weekly" and all(v[2] == "SUN,THU" and v[3] == 1 for k, v in s.items() if k != "KEDAR PHARMACEUTICAL"), s)
check("Kedar's row (D626): custom Mon + Fri, Sunday only blocked (Thursday open), single-source extra waived, cap 14, review 4 weeks after go-live (%s); Yuvika (orthotics) has no row; %d suppliers seeded from the real 90 days -- L.K. weekly, Gunina weekly" % (N["kedar_review_on"], N["seed_n"]),
      s["KEDAR PHARMACEUTICAL"][:6] == ["custom", "MON,FRI", "SUN", 1, 14, 0] and N["kedar_review_on"] == "2026-10-26" and not N["yuvika"] and N["seed_n"] >= 15
      and N["seed_real"].get("L.K. DRUG HOUSE", [None])[0] == "weekly" and N["seed_real"].get("GUNINA PHARMACEUTICALS PVT LTD", [None])[0] == "weekly", (s["KEDAR PHARMACEUTICAL"], N["seed_real"], N["seed_n"]))
check("the words: '%s' · '%s'" % (N["words_kedar"], N["words_weekly"]), N["words_kedar"].startswith("Kedar — Mon & Fri, delivered same evening, cover 8 days, cap 14, Thursday ok, single-source extra waived; review 26-Oct-2026 → weekly")
      and N["words_weekly"].startswith("W410 Weekly — Mondays, delivered same evening") and "cover 11 days, cap 14, Thursday blocked" in N["words_weekly"], (N["words_kedar"], N["words_weekly"]))
check("the owner sets Fort Co to monthly (darpan cannot, 403); a re-seed leaves it monthly (owner_fields carries it); the audit has the rows",
      N["set_fort"][0] == 200 and N["set_darpan"] == 403 and N["fort_after_reseed"]["cadence"] == "monthly" and "cadence" in N["fort_after_reseed"]["owner_fields"] and N["audit_n"] >= 2, (N["set_fort"], N["set_darpan"], N["fort_after_reseed"], N["audit_n"]))

print("-- 2  the calendar: fixed order days, Thursday for all but Kedar, Sunday for all, a holiday moves the day earlier")
check("weekly -> Mondays 28-Sep, 05-Oct, 12-Oct; Kedar -> Mon + Fri (28-Sep, 02-Oct, 05-Oct, 09-Oct, 12-Oct); fortnightly -> alternate Mondays (28-Sep, 12-Oct, 26-Oct); monthly -> first Monday (05-Oct, 02-Nov)",
      N["cal_weekly"] == ["2026-09-28", "2026-10-05", "2026-10-12"] and N["cal_kedar"] == ["2026-09-28", "2026-10-02", "2026-10-05", "2026-10-09", "2026-10-12"] and N["cal_fort"] == ["2026-09-28", "2026-10-12", "2026-10-26"]
      and N["cal_month"] == ["2026-10-05", "2026-11-02"], (N["cal_weekly"], N["cal_kedar"], N["cal_fort"], N["cal_month"]))
check("a Thursday order day moves to Wednesday for everyone (30-Sep) but stands for Kedar (01-Oct); a Sunday order day moves to Saturday (03-Oct)",
      N["cal_thu_blocked"] == ["2026-09-30"] and N["cal_thu_kedar"] == ["2026-10-01"] and N["cal_sun"] == ["2026-10-03"], (N["cal_thu_blocked"], N["cal_thu_kedar"], N["cal_sun"]))
check("Shavez adds a holiday on Mon 05-Oct (bhati cannot): the weekly order moves to Sat 03-Oct (Sunday skipped); the monthly supplier's next order day is 03-Oct too",
      N["hol_add"] == 200 and N["hol_bhati"] in (302, 403) and N["cal_weekly_hol"] == ["2026-09-28", "2026-10-03", "2026-10-12"] and N["next_month_hol"] == "2026-10-03", (N["hol_add"], N["hol_bhati"], N["cal_weekly_hol"], N["next_month_hol"]))
check("cover per order: weekly 7+1+3 = 11 (single-source 14, at the cap); Kedar 4+1+3 = 8, extra waived; fortnightly 14+1+3 = 18 (single-source 21, the cap)", N["cover"] == [11, 14, 8, 18, 21, 4], N["cover"])

print("-- 3  the plan on Monday 28-Sep: the engine's rails under the rules; the interim orders")
check("Item A (weekly, two suppliers): cover 11 and the quantity = the shortfall to 11 days, rounded 10-then-tens; Item B (fortnightly): cover 18; Kedar's item (single source, waived): cover 8",
      N["plan_A"][0] == 11 and N["plan_A"][1] == N["plan_A"][2] and N["plan_A"][1] > 0 and N["plan_B"][0] == 18 and N["plan_B"][1] == N["plan_B"][2] and N["plan_K"][0] == 8 and N["plan_K"][1] == N["plan_K"][2] and N["plan_K"][1] > 0, (N["plan_A"], N["plan_B"], N["plan_K"]))
check("a ₹1 line with stock on the shelf is dropped (min line ₹50); Small Co's ₹400 proposal is HELD under the ₹500 minimum order; the short-supplied line rides in as 'carried'; Yuvika is never in the medicine plan",
      N["plan_D"] is None and N["plan_small"][0] and "waits for the next order day" in (N["plan_small"][1] or "") and N["plan_small"][2] < 50000 and N["plan_carried"] == ["W410 OOS ITEM"] and N["plan_yuvika"] is False, (N["plan_D"], N["plan_small"], N["plan_carried"], N["plan_yuvika"]))
WN = lambda names: [x for x in names if x.startswith("W410")]  # noqa: E731 -- the real suppliers on the copied data raise their own; the walk reads its own
check("interim: Item C (cover 2 days, monthly supplier, next order day 05-Oct) raises exactly one interim order for Month Co -- the shortfall to that day + lead + safety (11 days -> 10 strips); no other W410 supplier",
      N["interim_C"][0] == 10 and N["interim_C"][1] == 11 and N["interim_C"][2] == "2026-10-05" and WN(N["interim_C"][3]) == ["W410 MONTH CO"], N["interim_C"])
check("interim is off before order.interim_from; not raised on a Thursday (blocked -- only Kedar, whose Thursday is open, may raise one) nor on a Sunday; raised on the Saturday and the Wednesday for every thin W410 supplier except Small Co (under the ₹500 minimum)",
      "start" in (N["interim_off_before"] or "") and WN(N["interim_thu"]) == [] and all(x == "KEDAR PHARMACEUTICAL" for x in N["interim_thu"]) and N["interim_sun"] == []
      and WN(N["interim_sat"]) == ["W410 FORT CO", "W410 MONTH CO", "W410 WEEKLY CO"] and WN(N["interim_wed"]) == ["W410 FORT CO", "W410 MONTH CO", "W410 WEEKLY CO"], (N["interim_off_before"], N["interim_thu"], N["interim_sun"], WN(N["interim_sat"]), WN(N["interim_wed"])))

print("-- 4  09:00 prepared + the first notice; the reminders count sent / unsent and go silent; bhejo through the S403 wa.me flow")
PR = {p[0]: p for p in N["props"] if p[0].startswith("W410") or p[0] == "KEDAR PHARMACEUTICAL"}
check("09:00 prepares one proposal per supplier due -- Weekly, Fort, Kedar fixed and open; Small held; Month interim (the real Monday suppliers on the copied data ride along) -- and notices the four senders: '%s'" % N["tick_prepare"][2],
      N["tick_prepare"][0] == "prepare" and N["tick_prepare"][1]["fixed"] >= 3 and N["tick_prepare"][1]["held"] >= 1 and N["tick_prepare"][1]["interim"] >= 1
      and PR["W410 WEEKLY CO"][1:] == ["fixed", "open"] and PR["W410 FORT CO"][1:] == ["fixed", "open"] and PR["KEDAR PHARMACEUTICAL"][1:] == ["fixed", "open"] and PR["W410 SMALL CO"][1:] == ["fixed", "held"] and PR["W410 MONTH CO"][1:] == ["interim", "open"]
      and re.match(r"^Aaj \d+ order tayyar — .*W410 Weekly.*\(\d+ beech ka\)\. Purchase orders kholiye\.$", N["tick_prepare"][2] or "") and N["tick_prepare"][3] == ["alisha", "darpan", "shavez", "shivani"], (N["tick_prepare"], PR))
check("12:00 before any send: 'Aaj N order: 0 bheja, N baaki — …' naming W410 Weekly; the staff day API carries n = sent + unsent and 'Beech ka order'",
      re.match(r"^Aaj (\d+) order: 0 bheja, \1 baaki — ", N["remind12"] or "") and "W410 Weekly" in N["remind12"] and N["day_api"][0] == N["day_api"][1] + N["day_api"][2] and N["day_api"][1] == 0 and "Beech ka order" in N["day_api"][4], (N["remind12"], N["day_api"]))
check("a send before the owner's approval is refused (rules_pending); after Approve rules, bhati (no porders row) is refused; darpan sends Weekly Co with an edit (A −10, G removed): one SENT order, section Medicines, the wa.me link returned, the lines as edited",
      N["send_before_rules"] == [403, "rules_pending"] and N["approve"] == 200 and N["send_bhati"] in (302, 403) and N["send1"][0] == 200 and N["send1"][1] and N["send1"][2] == "darpan"
      and not any(l["item"] == "W410 ITEM G" for l in N["send1"][3]) and N["order1"][0]["status"] == "sent" and N["order1"][0]["section"] == "Medicines" and N["prop1"][0]["status"] == "sent" and N["prop1"][0]["sent_by"] == "darpan"
      and N["send_again"] == [200, True], (N["send_before_rules"], N["approve"], N["send_bhati"], N["send1"], N["order1"], N["prop1"], N["send_again"]))
check("once Weekly Co's Monday order is SENT, the Wednesday interim check counts Item A's units as on the way: A raises no interim (Item G, removed from that order, still may); Fort and Month still do",
      "W410 FORT CO" in N["interim_after_send"][0] and "W410 MONTH CO" in N["interim_after_send"][0] and "W410 ITEM A" not in N["interim_after_send"][1] and (not N["plan_after_send"] or "on order #" in N["plan_after_send"][0]), (N["interim_after_send"], N["plan_after_send"]))
check("15:00 reads 'Aaj N order: 1 bheja, N-1 baaki — …' without W410 Weekly; Darpan's card carries the count line", re.match(r"^Aaj (\d+) order: 1 bheja, \d+ baaki — ", N["remind15"] or "") and "W410 Weekly" not in N["remind15"]
      and N["kal_card"]["ok"] and N["kal_card"]["n"] == N["day_api"][0] and N["kal_card"]["sent"] == 1, (N["remind15"], N["kal_card"]))
check("the freeze: send 423 with the reason (and S403's send_med too); the staff state and Needs you carry it; unfreeze; Kedar and the interim are sent by shivani and alisha (order note names the kind)",
      N["freeze_on"][0] == 200 and N["send_frozen"][0] == 423 and "stock count" in (N["send_frozen"][2] or "") and N["send_med_frozen"] == 423 and "stock count" in (N["state_frozen"] or "") and N["needs_frozen"]
      and N["freeze_off"]["frozen"] is None and N["send_kedar"] == 200 and N["send_interim"][0] == 200 and "interim" in N["send_interim"][1][0]["note"], (N["freeze_on"], N["send_frozen"], N["send_med_frozen"], N["state_frozen"], N["needs_frozen"], N["send_kedar"], N["send_interim"]))
check("17:00 with Fort Co still unsent speaks ('3 bheja', W410 Fort named, W410 Weekly not): '%s'; the notice log holds 0900/1200/1500/1700 once each; the pushes went to the four senders with the text and the screen's url; no number in any push" % N["remind17"][0],
      "3 bheja" in (N["remind17"][0] or "") and "W410 Fort" in N["remind17"][0] and "W410 Weekly" not in N["remind17"][0] and [x["slot"] for x in N["notices"]] == ["0900", "1200", "1500", "1700"] and N["pushes"][0] == 16 and N["pushes"][1] == ["alisha", "darpan", "shavez", "shivani"]
      and N["pushes"][2] == "/finance/porders" and N["pushes"][4] is False, (N["remind17"], N["notices"], N["pushes"]))
check("once every proposal of the day is sent the reminder is SILENT (no notice row, no push); a repeat of a slot already sent answers already", N["silent17"] == [True, 0, 16] and N["already12"] is True, (N["silent17"], N["already12"]))

print("-- 5  unsent after the day: the merge into the next order day, the owner's line, one order never two")
check("the nightly merges Fort Co's unsent proposal into its next order day (12-Oct); Needs you says nothing of Fort Co on 05-Oct and 'Order not sent: W410 Fort — due 28-Sep, still open on 12-Oct' on the 12th",
      N["nightly"]["merged"] >= 1 and N["merged"] == [{"status": "merged", "merged_into": "2026-10-12"}] and N["needs_oct5"] == [] and len(N["needs_oct12"]) == 1 and "W410 Fort" in N["needs_oct12"][0] and "28-Sep-2026" in N["needs_oct12"][0], (N["nightly"], N["merged"], N["needs_oct5"], N["needs_oct12"]))
check("the 12-Oct proposal carries '28-Sep ka order bhi isme' (carried_from) -- ONE order; sending it closes the merged row and the line leaves Needs you",
      N["carried_into"] and N["carried_into"][0]["carried_from"] == "2026-09-28" and N["merged_after_send"] == [{"status": "sent"}] and N["needs_oct12b"] == [], (N["carried_into"], N["merged_after_send"], N["needs_oct12b"]))

print("-- 6  the owner's Needs you: a month above its 90-day pace; the Kedar review with the boxes figure and the one tap; nothing else about ordering")
check("Weekly Co (₹25,000 this month against a ₹14,333 pace) is named; Month Co (on pace) is not; Rare Co (2 bills, no pace) is not; the orthotics vendor never is",
      any(t.startswith("W410 Weekly this month: ₹25,000 so far, 87% above") for t in N["spend"]) and not any(("W410 Month" in t) or ("W410 Rare" in t) or ("Yuvika" in t) for t in N["spend"]), N["spend"])
check("on the review date the line reads what twice-weekly held (peak of N boxes of the big four, N > 0) with the one tap; 'Move Kedar to weekly' makes it weekly / Mondays and clears the review; the line is gone; back to custom = Mon + Fri",
      N["review_line"][0] == 1 and (N["review_line"][3] or 0) > 0 and N["review_line"][2] == "weekly" and N["move_weekly"]["ok"] and N["kedar_after"] == [{"cadence": "weekly", "order_days": "MON", "review_on": None}]
      and N["review_gone"] == [] and N["kedar_back"] == [{"cadence": "custom", "order_days": "MON,FRI"}], (N["review_line"], N["move_weekly"], N["kedar_after"], N["review_gone"], N["kedar_back"]))
check("nothing else about ordering reaches the owner's line list", N["needs_other"] == [], N["needs_other"])

print("-- 7  Out of stock both ends; New items this month; the candidates and the tick")
check("the OOS item (shelf 0, Weekly Co said Nahi mila on %s) fires; a purchase of it from another supplier clears it; darpan cannot read the block" % (N["oos1"][3],),
      N["oos1"][0] and N["oos1"][1] == 0 and N["oos1"][2] == "W410 Weekly" and N["oos2"] is False and N["oos_gate"] == 403, (N["oos1"], N["oos2"], N["oos_gate"]))
check("New items: the first-ever item lists salt · supplier · 'not in export' for manufacturer and MRP (no Marg fact for it) · rate ₹120 · first bill 20-Sep; an item first bought in August is absent; real September first-evers show a manufacturer from the item master",
      N["new_items"][0] and N["new_items"][1] == ["W410 SALT", "W410 Weekly", "not in export", "not in export", "₹120", "20-Sep-2026"] and N["new_items"][2] is False and N["new_items"][3] is True, N["new_items"])
check("candidates: Item F (in stock, never sold) under never-reorder; Item G (1 sale in 180 days, ₹300 a strip) under on-demand; the state carries oos_n (0 after the clear above), new_items_n and Kedar first",
      N["cands"][0] and N["cands"][1] and N["cands"][2] == 0 and N["cands"][3] >= 1 and N["cands"][5] == "KEDAR PHARMACEUTICAL", N["cands"])
check("the owner ticks Item A never-reorder: it lands in order_rules.json (version bumped, orthotics_cycle empty, S341's key set unchanged) and the live plan holds A back; untick removes it; keep-in-stock stores; darpan cannot tick",
      N["tick_A"] == 200 and N["lists"][0] is True and N["lists"][1] >= 2 and N["lists"][2] == [] and N["lists"][3] == ["_about", "internal_use", "never_reorder", "on_demand", "orthotics_cycle", "version"]
      and N["A_held"] == [False, True] and N["lists2"] is False and N["keep"] == 200 and N["item_gate"] == 403, (N["tick_A"], N["lists"], N["A_held"], N["lists2"], N["keep"], N["item_gate"]))

print("-- 8  the pages; no number anywhere")
check("the staff page carries the day's section; the owner's page the red bar, the new-items fold and Approve rules; no 10-digit number in the day API, the send answer, Darpan's card or the owner's page",
      N["staff_page"] == [True, True] and N["owner_page"] == [True, True, True, True] and N["leak"] is False, (N["staff_page"], N["owner_page"], N["leak"]))

print("-- 9  NEGATIVE CONTROLS on the box as it is (the unpatched files)")
check("NEGATIVE: order_rules not mounted, the rules state 404, state() without today, no tables, Needs you without the ordering lines, Darpan's payload without orders_today",
      not O["mounted"] and O["rules_state_gate"]["manoj"] == 404 and O["state_today"][0] is False and not any(O["tables"].values())
      and not any(t.startswith("Order not sent") or "90-day pace" in t or t.startswith("Kedar review") for t in O["needs0"]) and O["kal0"] == [True, False], (O["mounted"], O["rules_state_gate"], O["state_today"], O["tables"], O["kal0"]))

print(("WALK_S410 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S410 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
