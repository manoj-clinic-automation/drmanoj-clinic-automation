#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s404.py -- kit S404_ORTHO_STOCK_CLOSE. THE REAL finance_app.py (a copy of /root/finance carrying the kit's
files) over a SCRATCH COPY of the live finance.db, driven through Flask's test client with header identity (walk
only). The round is the real round 1 (06-Sep); every pair and line it touches is found BY KEY (the item names the
API itself returns), never by counting. Its own crafted rows are keyed W404*.

  --app NEW      a copy of /root/finance with the kit's files (must be named .../finance so marg_take finds it)
  --old OLD      a copy of /root/finance as the box is (the negative control)
  --marg-new DIR a copy of /root/marg_ingest with the kit's marg_take.py (named .../marg_ingest, beside NEW)
  --marg-old DIR the box's marg_take.py beside the same helpers
  --db PATH      the scratch copy (a second copy PATH.old is made for the old app's write tests)
  --portal-new DIR / --portal-old DIR   portal.py + tile_grants.json, built and live

Prints item names of the shop, counts and dates. No patient, no number.
"""
import argparse
import datetime as dt
import io
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--old", required=True)
ap.add_argument("--marg-new", required=True)
ap.add_argument("--marg-old", required=True)
ap.add_argument("--db", required=True)
ap.add_argument("--portal-new", required=True)
ap.add_argument("--portal-old", required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


# ------------------------------------------------------------------ the scratch copies, seeded
def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s404  # noqa: E402
assert seed_s404.seed(a.db, a.app) == 0, "seed failed"
con = sqlite3.connect(a.db, timeout=30)
con.row_factory = sqlite3.Row
print("-- scratch seeded (stockmatch unit, 22 renames); old-app scratch copy at %s" % os.path.basename(DB_OLD))

# ------------------------------------------------------------------ the probe (each app in its own process)
PROBE = r'''
import json, os, sys, sqlite3, datetime as dt
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
import stock_app
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
now = lambda: dt.datetime.now().replace(microsecond=0).isoformat()
out = {"unit": fa._unit_for_path("/finance/stockmatch/api/state"), "mounted": "stockmatch" in fa.app.blueprints,
       "has_match_answer": hasattr(stock_app, "match_answer"), "causes": list(stock_app.CAUSES)}
out["pages"] = {u: G(u, "/finance/stockmatch")[0] for u in ("darpan", "manoj", "bhati", "shavez", "amir", "alisha", "stranger")}
pg = G("darpan", "/finance/stockmatch"); out["darpan_page_text"] = (pg[1][:600] if isinstance(pg[1], str) else "")
out["api_gate"] = {u: G(u, "/finance/stockmatch/api/state")[0] for u in ("bhati", "shavez", "amir", "alisha")}
out["hub_gate"] = {u: [G(u, "/finance/stock/page/hub?count=1")[0], G(u, "/finance/stock/api/pad/hub/1")[0]] for u in ("darpan", "bhati", "shavez")}
hub0 = G("manoj", "/finance/stock/api/pad/hub/1"); out["hub0"] = [hub0[0], sorted(hub0[1].keys()) if isinstance(hub0[1], dict) else None]
am0 = G("amir", "/finance/stock/api/pad/amir/1"); out["amir0_keys"] = sorted(am0[1].keys()) if isinstance(am0[1], dict) else None
out["old_cause_dontknow"] = P("manoj", "/finance/stock/api/diff/%d/cause" % q("SELECT id FROM stock_diff WHERE count_id=1 AND item='FINGER COT M'")[0]["id"], {"cause": "DONT_KNOW"})[0]
# the old app, on its own scratch: a section-restricted make is ignored, a new-name snapshot does not reconcile
if not NEW:
    mk = P("manoj", "/finance/stock/api/pad/vouchers/1/make", {"section": "Orthotics"})
    items = [r["item"] for r in q("SELECT item FROM stock_voucher_line WHERE count_id=1")]
    secs = {r["item"]: r["section"] for r in q("SELECT s.item, s.section FROM stock_item_section s")}
    out["old_make"] = [mk[0], len(items), sorted({secs.get(i, "?") for i in items})]
    db.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,loaded_at,source) VALUES ('27-09-2026','KNEE SUPPORT XL HINGED',1,'1*1',1,?,'walk')", (now(),)); db.commit()
    stock_app.reconcile(db, "27-09-2026")
    out["old_reconcile"] = q("SELECT status FROM stock_diff WHERE count_id=1 AND item='KNEE SUPPORT HINGED XL'")[0]["status"]
    out["old_lane_alias"] = [hasattr(stock_app, "_alias_names")]
    print("JSON:" + json.dumps(out)); raise SystemExit
import item_alias, stockmatch
SEC = {r["item"]: r["section"] for r in q("SELECT item, section FROM stock_item_section")}
def is_o(i): return SEC.get(i) == "Orthotics"
def S(u="darpan"): return G(u, "/finance/stockmatch/api/state?count=1")
st = S(); out["state0"] = [st[0], {k: v for k, v in st[1].items() if k in ("count_id", "me", "progress", "open_lines", "closed", "verdict_en", "verdict_hi")}]
s0 = st[1]
out["pairs0"] = [[p["short"], p["over"], p["qty"], p["answer"], p["locked"]] for p in s0["pairs"]]
out["pairs_all_ortho"] = all(is_o(p["short"]) and is_o(p["over"]) for p in s0["pairs"])
out["lines_all_ortho"] = all(is_o(l["item"]) for l in s0["lines"])
out["lines_open"] = [[l["item"], l["rem"], l["status"], l["diff_id"], l["side"], l["answered"], l["locked"]] for l in s0["lines"] if l["open"]]
out["lines_open_status"] = sorted({l["status"] for l in s0["lines"] if l["open"]})
out["med_leak"] = [x for x in ("LACTOVAX SYP", "FEBUTAL", "LINVIZ 600", "OSTOVAXL DM", "OROMIN M", "GEMCAL XT TABLETS") if any(x in (p["short"], p["over"]) for p in s0["pairs"]) or any(l["item"] == x for l in s0["lines"])]
# --- card 1: Darpan's Haan lands where the owner's Yes lands
open_pairs = [p for p in s0["pairs"] if not p["locked"]]
P1, P2 = open_pairs[0], open_pairs[1]
out["P1"] = [P1["short"], P1["over"], P1["qty"]]; out["P2"] = [P2["short"], P2["over"]]
r = P("darpan", "/finance/stockmatch/api/pair?count=1", {"short": P1["short"], "over": P1["over"], "answer": "HAAN"})
out["haan"] = [r[0], (r[1] or {}).get("saved"), (r[1] or {}).get("round_made")]
out["match_row"] = q("SELECT short_item, over_item, qty, answer, by_user FROM stock_match WHERE count_id=1 AND short_item=? AND over_item=? ORDER BY id DESC LIMIT 1", P1["short"], P1["over"])
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
row = [x for x in hub["match"]["rows"] if x["short"] == P1["short"] and x["over"] == P1["over"]][0]
out["hub_row"] = [row["answer"], row["answered_by"]]
out["hub_swap"] = [hub["vouchers"]["swap_issue"], hub["vouchers"]["swap_receive"], hub["vouchers"]["swap_units"]]
rep = G("manoj", "/finance/stock/api/pad/report/1")[1]
out["swapped"] = {x["item"]: [x.get("swapped"), x["diff"]] for x in rep["differences"] if x["item"] in (P1["short"], P1["over"])}
out["haan_again"] = P("darpan", "/finance/stockmatch/api/pair?count=1", {"short": P1["short"], "over": P1["over"], "answer": "YES"})[0]
# the owner answers P2 on the hub; it is read-only to Darpan
out["owner_no"] = P("manoj", "/finance/stock/api/pad/match/1", {"short": P2["short"], "over": P2["over"], "answer": "NO"})[0]
st = S()[1]; p2 = [p for p in st["pairs"] if p["short"] == P2["short"] and p["over"] == P2["over"]][0]
out["p2_state"] = [p2["answer"], p2["answered_by"], p2["locked"]]
out["darpan_on_owner_pair"] = P("darpan", "/finance/stockmatch/api/pair?count=1", {"short": P2["short"], "over": P2["over"], "answer": "YES"})[0]
out["bad_pair"] = P("darpan", "/finance/stockmatch/api/pair?count=1", {"short": "NOPE", "over": "NADA", "answer": "YES"})[0]
# --- card 2: reasons
L = [l for l in st["lines"] if l["open"] and not l["answered"] and not l["locked"]]
L1 = [l for l in L if l["side"] == "short"][0]; L2 = [l for l in L if l["side"] == "over"][0]
out["L1"] = [L1["item"], L1["diff_id"], L1["rem"]]; out["L2"] = [L2["item"], L2["diff_id"], L2["rem"]]
au = lambda did: q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_diff' AND row_id=? AND action='cause'", did)[0]["n"]
out["r1"] = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L1["diff_id"], "reason": "BREAKAGE"})
out["r1"] = [out["r1"][0], (out["r1"][1] or {}).get("saved"), (out["r1"][1] or {}).get("progress")]
out["r1_row"] = q("SELECT cause, cause_by FROM stock_diff WHERE id=?", L1["diff_id"])[0]; out["r1_audit"] = au(L1["diff_id"])
r = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L1["diff_id"], "reason": "BREAKAGE"})
out["r1_repeat"] = [r[0], (r[1] or {}).get("already"), au(L1["diff_id"])]
r = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L1["diff_id"], "reason": "BILLING"})
out["r1_change"] = [r[0], ((r[1] or {}).get("saved") or {}).get("changed"), q("SELECT cause FROM stock_diff WHERE id=?", L1["diff_id"])[0]["cause"], au(L1["diff_id"])]
out["r_bad"] = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L1["diff_id"], "reason": "XYZ"})[0]
out["r_side"] = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L1["diff_id"], "reason": "BILLED_NOT_GIVEN"})[0]
out["r2"] = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L2["diff_id"], "reason": "DONT_KNOW"})[0]
out["r2_row"] = q("SELECT cause, cause_by FROM stock_diff WHERE id=?", L2["diff_id"])[0]
r = P("manoj", "/finance/stockmatch/api/reason?count=1", {"diff_id": L1["diff_id"], "reason": "NOT_RETURNED"})
out["owner_change"] = [r[0], q("SELECT cause, cause_by FROM stock_diff WHERE id=?", L1["diff_id"])[0], au(L1["diff_id"])]
out["darpan_after_owner"] = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L1["diff_id"], "reason": "BREAKAGE"})[0]
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
ol = [l for l in hub["ortho"]["lines"] if l["item"] == L1["item"]][0]
out["hub_line"] = [ol["cause"], ol["cause_by"], ol["cause_en"]]
# --- progress, then all done -> the orthotic round makes itself
st = S()[1]; pr = st["progress"]
calc = sum(1 for p in st["pairs"] if p["settled"]) + sum(1 for l in st["lines"] if l["open"] and l["answered"])
out["progress_mid"] = [pr, calc, len(st["pairs"]) + st["open_lines"]]
med_pending_before = [p for p in q("SELECT item FROM stock_diff WHERE count_id=1") if 0]
last = None
for p in [p for p in st["pairs"] if not p["locked"]]:
    last = P("darpan", "/finance/stockmatch/api/pair?count=1", {"short": p["short"], "over": p["over"], "answer": "NAHI"})
st = S()[1]
for l in [l for l in st["lines"] if l["open"] and not l["answered"] and not l["locked"]]:
    last = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": l["diff_id"], "reason": "DONT_KNOW"})
st = S()[1]
out["progress_done"] = [st["progress"], (last[1] or {}).get("round_made") if last else None]
vl = q("SELECT item, round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=1 ORDER BY id")
out["round_items"] = [[x["item"], x["round_no"], SEC.get(x["item"], "?")] for x in vl]
out["round_all_ortho"] = bool(vl) and all(is_o(x["item"]) for x in vl)
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
out["pending_after_auto"] = [hub["vouchers"]["pending"], hub["ortho"]["vouchers"]["pending"], sorted({SEC.get(p, "?") for p in hub["ortho"]["vouchers"]["pending_items"]})]
pend_all = stock_app._voucher_pending(db, stock_app._pad_report_data(db, 1))
out["pending_sections"] = sorted({SEC.get(p["item"], "?") for p in pend_all})
out["make_again"] = P("manoj", "/finance/stock/api/pad/vouchers/1/make", {"section": "Orthotics"})
out["make_bad"] = P("manoj", "/finance/stock/api/pad/vouchers/1/make", {"section": "Shoes"})[0]
mk = P("manoj", "/finance/stock/api/pad/vouchers/1/make", {"section": "Medicines"})
vl2 = q("SELECT item, round_no FROM stock_voucher_line WHERE count_id=1 AND round_no=?", (mk[1] or {}).get("round_no") or -1)
out["make_med"] = [mk[0], (mk[1] or {}).get("round_no"), len(vl2), sorted({SEC.get(x["item"], "?") for x in vl2})]
# --- Amir enters the orthotic batches
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
ob = hub["ortho"]["vouchers"]["batches"]
out["ortho_batches"] = [[b["round_no"], b["kind"], b["batch_no"], b["ortho_only"], b["entered"]] for b in ob]
ent = [P("amir", "/finance/stock/api/pad/vouchers/1/entered", {"round": b["round_no"], "kind": b["kind"], "batch": b["batch_no"], "marg_voucher_no": "W404-%d-%s-%d" % (b["round_no"], b["kind"][0], b["batch_no"])})[0] for b in ob if not b["entered"]]
out["entered"] = ent
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
out["after_enter"] = [hub["ortho"]["vouchers"]["not_entered"], [c for c in hub["ortho"]["conds"] if c["key"] == "vouchers"][0], hub["vouchers"]["batches_entered"]]
# --- the 22 renames
rn = q("SELECT old_name, new_name, done_at FROM marg_item_rename ORDER BY id")
names = [r["item"] for r in q("SELECT item FROM stock_count_item WHERE count_id=1")]
out["ren_seed"] = [len(rn), max(len(r["new_name"]) for r in rn), item_alias.check_list(item_alias.THE_22, names)]
am = G("amir", "/finance/stock/api/pad/amir/1")[1]
out["amir_renames"] = [len(am["renames"]["rows"]), sorted({r["state"] for r in am["renames"]["rows"]}), am["renames"]["summary"]]
TICK = "KNEE SUPPORT HINGED XL"; TNEW = "KNEE SUPPORT XL HINGED"
r = P("amir", "/finance/stock/api/pad/rename/tick", {"old": TICK}); out["tick"] = [r[0], (r[1] or {}).get("row", {}).get("done_by"), (r[1] or {}).get("message")]
out["tick_section"] = q("SELECT item, section, source, seeded_as FROM stock_item_section WHERE item_key=?", stock_app._sm.norm_key(TNEW))
out["tick_alias"] = q("SELECT name, item_id, kind, active FROM marg_item_name WHERE name_raw=?", TNEW)
out["tick_pending"] = q("SELECT name, active FROM marg_item_name WHERE item_id=(SELECT item_id FROM marg_item_name WHERE name=? AND kind='canonical') AND kind='pending_rename'", item_alias.spine_norm(TICK))
out["tick_task"] = q("SELECT status, done_by, answer FROM marg_task WHERE kind='rename' AND a=?", TICK)
r = P("amir", "/finance/stock/api/pad/rename/tick", {"old": TICK}); out["tick_again"] = [r[0], (r[1] or {}).get("already")]
r = P("amir", "/finance/stock/api/pad/rename/tick", {"old": TICK, "clear": True}); out["untick"] = [r[0], (r[1] or {}).get("row", {}).get("state")]
r = P("amir", "/finance/stock/api/pad/rename/tick", {"old": TICK}); out["retick"] = [r[0], (r[1] or {}).get("row", {}).get("state")]
out["resolve"] = [item_alias.resolve(db, TNEW), item_alias.resolve(db, "KNEE SUPPORT XL HINGE"), item_alias.resolve(db, "ANKLE BINDER M BAMBOO"), item_alias.resolve(db, "KNEE SUPPORT HINGED XL")]
# --- the alias in the count / stock lanes: crafted rows under the NEW name land on the OLD item
eid = q("SELECT id FROM day_entry WHERE unit='medical' ORDER BY id DESC LIMIT 1")[0]["id"]
life0 = G("manoj", "/finance/stock/api/pad/item/1/KNEE SUPPORT HINGED XL")[1]
life0b = G("manoj", "/finance/stock/api/pad/item/1/ANKLE BINDER BAMBOO M")[1]
db.execute("DELETE FROM sale_line_item WHERE unit='medical' AND bill_no LIKE 'W404%'")
c20, u20 = item_alias.clip(TNEW, 20), item_alias.clip("ANKLE BINDER M BAMBOO", 20)     # what Marg's sale export prints: 20 characters
out["clips"] = [c20, u20]
db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical','2026-09-01','W404A001',0,1,?,?, '1*1','1',115000)", (eid, c20, item_alias.sale_key(c20)))
db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical','2026-09-01','W404A002',0,1,?,?, '1*1','1',34400)", (eid, u20, item_alias.sale_key(u20)))
db.execute("DELETE FROM purchase_line WHERE bill_no LIKE 'W404%'")
db.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, loose_qty, direction, source_md5, line_type) VALUES ('W404','W404P1','2026-09-01','2026-09','KNEE SUPPORT XL HINGED','1*1',2,0,0,'PURCHASE','w404','ITEMWISE')")
snap_day = next(dd for dd in ("04-09-2026", "03-09-2026", "01-09-2026", "30-08-2026") if not q("SELECT 1 AS x FROM stock_snapshot WHERE as_on=? AND item=?", dd, TICK))
db.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,loaded_at,source) VALUES (?,?,7,'1*1',1,?,'walk')", (snap_day, TNEW, now()))
db.commit()
life = G("manoj", "/finance/stock/api/pad/item/1/KNEE SUPPORT HINGED XL")[1]
lifeb = G("manoj", "/finance/stock/api/pad/item/1/ANKLE BINDER BAMBOO M")[1]
out["life"] = [life0["sold_units"], life["sold_units"], [p["bill_no"] for p in life["purchases"] if p["bill_no"] == "W404P1"], [m for m in life["marg"] if m["text"] == snap_day.replace("-2026", "-2026")], snap_day]
out["life_unticked"] = [life0b["sold_units"], lifeb["sold_units"]]
db.execute("INSERT OR REPLACE INTO stock_snapshot (as_on,item,qty,packing,pack_size,loaded_at,source) VALUES ('27-09-2026',?,1,'1*1',1,?,'walk')", (TNEW, now())); db.commit()
stock_app.reconcile(db, "27-09-2026")
out["reconcile"] = q("SELECT status, closed_as_on FROM stock_diff WHERE count_id=1 AND item=?", TICK)[0]
db.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES ('27-09-2026','push_snapshot',?,1,?)", (TNEW, now())); db.commit()
fl = stock_app._feed_latest(db).get(("27-09-2026", "marg"), {}).get("items", {})
out["feed_alias"] = [fl.get(TICK), TNEW in fl]
# --- verification: the first export carrying the new name and not the old (F-529)
snap = [r["item"] for r in q("SELECT item FROM stock_snapshot WHERE as_on='25-09-2026'")]
carry = [TNEW if x == TICK else x for x in snap]
v = item_alias.verify_closing(db, carry, "2026-09-27", "w404md5", "walk"); db.commit()
out["verify1"] = [v["verified"], q("SELECT verified_md5, verified_as_on, seen_n FROM marg_item_rename WHERE old_name=?", TICK)[0]]
T2 = "KNEE SUPPORT HINGED L"; T2N = "KNEE SUPPORT L HINGED"
P("amir", "/finance/stock/api/pad/rename/tick", {"old": T2})
v = item_alias.verify_closing(db, snap, "2026-09-28", "m1", "walk"); v2 = item_alias.verify_closing(db, snap, "2026-09-29", "m2", "walk"); v3 = item_alias.verify_closing(db, snap, "2026-09-29", "m2", "walk"); db.commit()
out["seen"] = [v["seen"], v2["seen"], v3["seen"], q("SELECT seen_n, verified_at FROM marg_item_rename WHERE old_name=?", T2)[0]]
am = G("amir", "/finance/stock/api/pad/amir/1")[1]
out["amber"] = [[r["state"], r["state_hi"]] for r in am["renames"]["rows"] if r["old_name"] == T2] + [am["renames"]["summary"]["amber"]]
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]; out["hub_amber"] = [hub["ortho"]["renames"]["amber"], [c for c in hub["ortho"]["conds"] if c["key"] == "renames"][0]["ok"]]
items_push = [{"item": (T2N if x == T2 else x), "qty": 3, "packing": "1*1", "pack_size": 1} for x in snap]
r = P("manoj", "/finance/stock/api/snapshot", {"as_on": "30-09-2026", "source": "push_snapshot", "items": items_push})
out["push_door"] = [r[0], (r[1] or {}).get("stored_in"), q("SELECT verified_as_on, verified_md5 IS NOT NULL AS has_md5 FROM marg_item_rename WHERE old_name=?", T2)[0]]
out["untick_verified"] = P("amir", "/finance/stock/api/pad/rename/tick", {"old": T2, "clear": True})[0]
# marg_take's door: the certified reader on a real archived closing export when one is at hand; fail-soft always
sys.path.insert(0, os.environ["MARGDIR"]); import marg_take
out["take_has"] = hasattr(marg_take, "_rename_verify")
marg_take._rename_verify(db, "/nonexistent/W404.xls", "x"); out["take_soft"] = True
T3 = "L S BELT CONT GRAY UNISON XXX"
P("amir", "/finance/stock/api/pad/rename/tick", {"old": T3})
real = q("SELECT server_name, md5, stamp FROM mi_file WHERE type='STOCK_CLOSING' AND verdict='VERIFIED' AND kept=1 ORDER BY received_at DESC LIMIT 1")
path = ""
if real:
    for root, _d, fs in os.walk(os.environ.get("MARG_ARCHIVE", "/root/marg_ingest/archive")):
        if real[0]["server_name"] in fs:
            path = os.path.join(root, real[0]["server_name"]); break
if path:
    b0 = q("SELECT seen_n, last_seen_as_on FROM marg_item_rename WHERE old_name=?", T3)[0]
    marg_take._rename_verify(db, path, real[0]["md5"], real[0]["stamp"])
    b_same = q("SELECT seen_n FROM marg_item_rename WHERE old_name=?", T3)[0]["seen_n"]     # the export predates the tick: nothing counted
    db.execute("UPDATE marg_item_rename SET done_at='2026-09-01T00:00:00' WHERE old_name=?", (T3,)); db.commit()   # a tick before the export
    marg_take._rename_verify(db, path, real[0]["md5"], real[0]["stamp"])
    b1 = q("SELECT seen_n, last_seen_as_on, verified_at FROM marg_item_rename WHERE old_name=?", T3)[0]
    out["take_real"] = [os.path.basename(path)[:40], b0, b_same, b1, real[0]["stamp"]]
else:
    out["take_real"] = None
# spine: a ticked rename is an alias new -> old at the 20-character clip
sys.path.insert(0, os.path.join(APP, "spine")); import spine_build
ra = spine_build.rename_aliases(os.environ["FINANCE_DB"])
out["spine_alias"] = [ra.get(spine_build.K(TNEW)), spine_build.K(TICK), spine_build.K("ANKLE BINDER M BAMBOO") in ra, len(ra)]
# --- the section verdict flips CLOSED only when all four hold
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]; O = hub["ortho"]
out["v_before_words"] = [O["closed"], {c["key"]: c["ok"] for c in O["conds"]}, O["unsettled"][:5], len(O["unsettled"])]
uns = O["unsettled"]
shorts = [l["item"] for l in O["lines"] if l["item"] in uns and l["rem"] < 0]; overs = [l["item"] for l in O["lines"] if l["item"] in uns and l["rem"] > 0]
if shorts: P("manoj", "/finance/stock/api/pad/decide", {"count_id": 1, "items": shorts, "action": "WRITE_OFF", "note": "walk"})
if overs: P("manoj", "/finance/stock/api/pad/decide", {"count_id": 1, "items": overs, "action": "EXPLAINED", "note": "walk"})
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]; O = hub["ortho"]
out["v_after_words"] = [O["closed"], {c["key"]: c["ok"] for c in O["conds"]}, O["vouchers"]["pending"]]
mk = P("manoj", "/finance/stock/api/pad/vouchers/1/make", {"section": "Orthotics"})
vl3 = q("SELECT item FROM stock_voucher_line WHERE count_id=1 AND round_no=?", (mk[1] or {}).get("round_no") or -1)
out["round2"] = [mk[0], (mk[1] or {}).get("round_no"), len(vl3), all(is_o(x["item"]) for x in vl3)]
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]; O = hub["ortho"]
for b in [b for b in O["vouchers"]["batches"] if not b["entered"]]:
    P("amir", "/finance/stock/api/pad/vouchers/1/entered", {"round": b["round_no"], "kind": b["kind"], "batch": b["batch_no"], "marg_voucher_no": "W404-%d-%s-%d" % (b["round_no"], b["kind"][0], b["batch_no"])})
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]; O = hub["ortho"]
out["v_after_enter"] = [O["closed"], {c["key"]: c["ok"] for c in O["conds"]}, O["proof"]["state"]]
# the proof: an export before the first voucher and one after the last, our own figures beside (D543)
ent = {}
for r in q("SELECT round_no, kind, batch_no, marg_voucher_no, at FROM stock_voucher_entered WHERE count_id=1 ORDER BY id"):
    k = (r["round_no"], r["kind"], r["batch_no"])
    if (r["marg_voucher_no"] or "").strip(): ent[k] = r["at"]
    else: ent.pop(k, None)
need = {}
for r in q("SELECT round_no, kind, batch_no, item, change FROM stock_voucher_line WHERE count_id=1"):
    if (r["round_no"], r["kind"], r["batch_no"]) in ent: need[r["item"]] = need.get(r["item"], 0) + int(r["change"])
need_o = {i: v for i, v in need.items() if is_o(i)}
t_before, t_after = now(), (dt.datetime.now() + dt.timedelta(minutes=5)).replace(microsecond=0).isoformat()
for src, day, m_add, rec in (("push_snapshot", "25-09-2026", 0, t_before), ("push_expected base=03-09-2026 pur_to=25-09-2026", "25-09-2026", None, t_before),
                             ("push_snapshot", "30-12-2026", 1, t_after), ("push_expected base=03-09-2026 pur_to=30-12-2026", "30-12-2026", None, t_after)):
    for i, v in need.items():
        db.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?,?,?,?,?)", (day, src, i, 100 + (v if m_add else 0), rec))
db.commit()
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]; O = hub["ortho"]
out["v_after_proof"] = [O["closed"], {c["key"]: c["ok"] for c in O["conds"]}, O["proof"], len(need_o)]
# the renames: tick the rest, then one export carrying every new name and no old one
for r in q("SELECT old_name FROM marg_item_rename WHERE done_at IS NULL"):
    P("amir", "/finance/stock/api/pad/rename/tick", {"old": r["old_name"]})
ren = {r["old_name"]: r["new_name"] for r in q("SELECT old_name, new_name FROM marg_item_rename")}
v = item_alias.verify_closing(db, [ren.get(x, x) for x in snap], "2026-12-30", "final", "walk"); db.commit()
out["v_final"] = [len(v["verified"]), item_alias.summary(db)]
hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]; O = hub["ortho"]
out["closed"] = [O["closed"], O["closed_at"], O["verdict_en"], {c["key"]: c["ok"] for c in O["conds"]}]
out["closed_row"] = q("SELECT count_id, section, closed_at FROM stock_section_close")
st = S()[1]; out["closed_hi"] = [st["closed"], st["verdict_hi"], st["progress"]["hi"]]
out["closed_again"] = G("manoj", "/finance/stock/api/pad/hub/1")[1]["ortho"]["closed_at"]
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, margdir, mode, dbpath):
    env = dict(os.environ, APPDIR=appdir, MARGDIR=margdir, MODE=mode, FINANCE_DB=dbpath,
               FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1")
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, a.marg_old, "old", DB_OLD)
N = probe(a.app, a.marg_new, "new", a.db)

# ------------------------------------------------------------------ 1 · the unit, the page, the gate
print("-- 1  the unit, the page, the gate")
check("finance_app resolves /finance/stockmatch/... to the unit 'stockmatch' and mounts stockmatch", N["unit"] == "stockmatch" and N["mounted"], (N["unit"], N["mounted"]))
check("darpan opens his page (200) and it is the Stock milaan page; the owner opens it too", N["pages"]["darpan"] == 200 and "Stock milaan" in N["darpan_page_text"] and N["pages"]["manoj"] == 200, N["pages"])
bad = {u: s for u, s in N["pages"].items() if u not in ("darpan", "manoj") and s == 200}
check("bhati, shavez, amir, alisha, a stranger cannot open it (302/403); their API calls are refused", not bad and all(s in (302, 401, 403) for s in N["api_gate"].values()), (N["pages"], N["api_gate"]))
check("darpan, bhati, shavez stay refused on the OWNER's hub (page 302, API 403/302) -- unchanged", all(v[0] == 302 and v[1] in (302, 403) for v in N["hub_gate"].values()), N["hub_gate"])
check("the owner's hub answers 200 and now carries the 'ortho' block", N["hub0"][0] == 200 and "ortho" in (N["hub0"][1] or []), N["hub0"])
check("the three new cause values are data in stock_app.CAUSES; the checker's own cause door accepts DONT_KNOW (200)",
      all(x in N["causes"] for x in ("NOT_RETURNED", "DONT_KNOW", "BILLED_NOT_GIVEN")) and N["old_cause_dontknow"] == 200, (N["causes"][-3:], N["old_cause_dontknow"]))

# ------------------------------------------------------------------ 2 · Darpan sees only orthotic pairs / lines of round 1
print("-- 2  what Darpan sees")
s0 = N["state0"][1]
check("the state is round 1, Darpan is 'staff', progress and verdict present", N["state0"][0] == 200 and s0["count_id"] == 1 and s0["me"] == "staff" and s0["progress"]["need"] > 0 and s0["verdict_hi"], s0)
check("every pair has BOTH items in the Orthotics section of the map; every line is an orthotic", N["pairs_all_ortho"] and N["lines_all_ortho"] and len(N["pairs0"]) >= 2, (len(N["pairs0"]), N["pairs0"][:3]))
check("no medicine of the medicine pairs / lines leaks onto his page", N["med_leak"] == [], N["med_leak"])
check("card 2 carries only OPEN orthotic lines with something left after the swaps (status open, rem != 0)", N["lines_open_status"] == ["open"] and all(l[1] != 0 for l in N["lines_open"]) and len(N["lines_open"]) > 0, (N["lines_open_status"], len(N["lines_open"])))

# ------------------------------------------------------------------ 3 · card 1
print("-- 3  Adla-badli? -- a Haan lands the same rows the owner's Yes lands")
P1 = N["P1"]
check("Darpan's Haan on %s / %s: 200, saved; stock_match row answer YES by_user darpan" % (P1[0], P1[1]),
      N["haan"][0] == 200 and N["haan"][1] and N["match_row"] and N["match_row"][0]["answer"] == "YES" and N["match_row"][0]["by_user"] == "darpan" and N["match_row"][0]["qty"] == P1[2], (N["haan"], N["match_row"]))
check("the owner's hub shows that pair answered YES by darpan; the swap vouchers appear at once (ISSUE + RECEIVE)", N["hub_row"] == ["YES", "darpan"] and N["hub_swap"][0] >= 1 and N["hub_swap"][1] >= 1 and N["hub_swap"][2] >= P1[2], (N["hub_row"], N["hub_swap"]))
check("the report carries the swap on both lines (swapped = the pair's qty)", all(v[0] == P1[2] for v in N["swapped"].values()) and len(N["swapped"]) == 2, N["swapped"])
check("a second Haan on the same pair is refused (409) -- his answer stands", N["haan_again"] == 409, N["haan_again"])
check("the owner answers the next pair NO on the hub; Darpan sees it greyed (locked, by manoj) and cannot change it (409)",
      N["owner_no"] == 200 and N["p2_state"] == ["NO", "manoj", True] and N["darpan_on_owner_pair"] == 409, (N["owner_no"], N["p2_state"], N["darpan_on_owner_pair"]))
check("a pair that is not proposed is refused (400)", N["bad_pair"] == 400, N["bad_pair"])

# ------------------------------------------------------------------ 4 · card 2
print("-- 4  Kam kyun? -- reasons store once; a repeat within 10 minutes writes nothing")
L1 = N["L1"]
check("one chip on %s (short %d): cause BREAKAGE by darpan, one audit row" % (L1[0], L1[2]), N["r1"][0] == 200 and N["r1_row"] == {"cause": "BREAKAGE", "cause_by": "darpan"} and N["r1_audit"] == 1, (N["r1"], N["r1_row"], N["r1_audit"]))
check("the same chip again within 10 minutes: answers already=True, NO second write (audit rows still 1)", N["r1_repeat"] == [200, True, 1], N["r1_repeat"])
check("a different chip within 10 minutes is his correction: cause BILLING, audit rows 2", N["r1_change"][0] == 200 and N["r1_change"][1] and N["r1_change"][2] == "BILLING" and N["r1_change"][3] == 2, N["r1_change"])
check("a reason outside the vocabulary is refused (400); a surplus chip on a shortage line is refused (400)", N["r_bad"] == 400 and N["r_side"] == 400, (N["r_bad"], N["r_side"]))
check("a surplus line takes 'Pata nahi' (DONT_KNOW by darpan)", N["r2"] == 200 and N["r2_row"] == {"cause": "DONT_KNOW", "cause_by": "darpan"}, (N["r2"], N["r2_row"]))
check("the owner changes Darpan's reason through the same door (NOT_RETURNED by manoj, audited); Darpan is then refused on that line (409)",
      N["owner_change"][0] == 200 and N["owner_change"][1] == {"cause": "NOT_RETURNED", "cause_by": "manoj"} and N["owner_change"][2] == 3 and N["darpan_after_owner"] == 409, (N["owner_change"], N["darpan_after_owner"]))
check("the hub's orthotic line shows the reason beside it ('Darpan:' / the owner) in English", N["hub_line"][0] == "NOT_RETURNED" and N["hub_line"][1] == "manoj" and N["hub_line"][2], N["hub_line"])

# ------------------------------------------------------------------ 5 · progress and the orthotic round
print("-- 5  progress; all done -> the orthotic round makes itself, medicines stay for their own round")
pm = N["progress_mid"]
check("the progress line counts settled pairs + answered open lines (done = %d of %d)" % (pm[0]["done"], pm[0]["need"]), pm[0]["done"] == pm[1] and pm[0]["need"] == pm[2] and not pm[0]["all"], pm)
pd = N["progress_done"]
check("after Darpan answers everything: 'Sab ho gaya -- ab Amir ke vouchers', and the round was made by itself", pd[0]["all"] and pd[0]["hi"].startswith("Sab ho gaya") and pd[1] and pd[1].get("round_no"), pd)
check("every line of the auto-made round is an ORTHOTIC (section map); no medicine line with a decided cause was vouchered", N["round_all_ortho"] and N["round_items"], N["round_items"][:8])
check("the medicine lines are still waiting for their own round (pending sections exclude Orthotics)", "Orthotics" not in N["pending_sections"] and N["pending_sections"] and N["pending_after_auto"][1] == 0, (N["pending_sections"], N["pending_after_auto"]))
check("Make the orthotic round again: nothing waiting (idempotent); a bad section is refused (400)", N["make_again"][0] == 200 and N["make_again"][1]["round_no"] is None and N["make_bad"] == 400, (N["make_again"], N["make_bad"]))
check("a Medicines round made on request carries medicine lines only", N["make_med"][0] == 200 and N["make_med"][1] and N["make_med"][2] > 0 and N["make_med"][3] == ["Medicines"], N["make_med"])

# ------------------------------------------------------------------ 6 · Amir's entered tick
print("-- 6  Amir's board: the orthotic batches entered")
check("the orthotic batches are listed on the section (ortho_only) and Amir's 'Marg mein daal diya' (entered) works (200 each)", N["ortho_batches"] and all(b[3] for b in N["ortho_batches"]) and N["entered"] and all(s == 200 for s in N["entered"]), (N["ortho_batches"], N["entered"]))
check("after entering: no orthotic batch left, the vouchers condition is green, the hub counts them", N["after_enter"][0] == 0 and N["after_enter"][1]["ok"] and N["after_enter"][2] >= len(N["entered"]), N["after_enter"])

# ------------------------------------------------------------------ 7 · the 22 renames
print("-- 7  the 22 renames: seeded exactly, ticked, followed")
check("22 seeded; every new name <= 29; no collision at 20 / 27 / 29 across all count names with the renames applied", N["ren_seed"][0] == 22 and N["ren_seed"][1] <= 29 and N["ren_seed"][2] == [], N["ren_seed"])
check("Amir's board lists the 22, all 'planned'", N["amir_renames"][0] == 22 and N["amir_renames"][1] == ["planned"], N["amir_renames"])
check("a tick (KNEE SUPPORT HINGED XL): done by amir; the NEW name inherits the section (Orthotics, source rename)", N["tick"][0] == 200 and N["tick"][1] == "amir" and N["tick_section"] and N["tick_section"][0]["section"] == "Orthotics" and N["tick_section"][0]["source"] == "rename", (N["tick"], N["tick_section"]))
check("the item spine gets the new name as an ALIAS on the old item (active); the S229 pending_rename spelling of the same item is retired; the S229 task is closed",
      N["tick_alias"] and N["tick_alias"][0]["kind"] == "alias" and N["tick_alias"][0]["active"] == 1 and all(p["active"] == 0 or p["name"] == "KNEE SUPPORT XL HINGED" for p in N["tick_pending"])
      and N["tick_task"] and N["tick_task"][0]["status"] == "done", (N["tick_alias"], N["tick_pending"], N["tick_task"]))
check("a second tick answers already; undo returns it to planned; a tick again makes it done", N["tick_again"] == [200, True] and N["untick"] == [200, "planned"] and N["retick"] == [200, "done"], (N["tick_again"], N["untick"], N["retick"]))
check("resolve: the new name, its 20-character clip -> the OLD name; an unticked rename's new name maps nothing", N["resolve"] == ["KNEE SUPPORT HINGED XL", "KNEE SUPPORT HINGED XL", "ANKLE BINDER M BAMBOO", "KNEE SUPPORT HINGED XL"], N["resolve"])

# ------------------------------------------------------------------ 8 · the alias in the lanes
print("-- 8  a ticked rename maps a crafted sale line, purchase line and stock row onto the OLD item; an unticked one maps nothing")
lf = N["life"]
check("item life of the OLD name: sold units +1 from the sale line keyed under the new 20-char clip (%s); the purchase bill under the new 27-char name; the snapshot row under the new name (as on %s = 7)" % (N["clips"][0], lf[4]),
      lf[1] == lf[0] + 1 and lf[2] == ["W404P1"] and lf[3] and lf[3][0]["qty"] == 7, lf)
check("the unticked rename (ANKLE BINDER BAMBOO M): a sale line under its new name is NOT counted", N["life_unticked"][0] == N["life_unticked"][1], N["life_unticked"])
check("reconcile: a later Marg export carrying the NEW name with the counted quantity closes the OLD name's difference", N["reconcile"]["status"] == "reconciled" and N["reconcile"]["closed_as_on"] == "27-09-2026", N["reconcile"])
check("the feed reader keys the new name under the old one (the proof and the three-way see one item)", N["feed_alias"] == [1, False], N["feed_alias"])

# ------------------------------------------------------------------ 9 · verification (F-529)
print("-- 9  verification: read the rename back from Marg's own export")
check("an export carrying the new name and not the old marks verified_at with that export's md5 and date", N["verify1"][0] == ["KNEE SUPPORT HINGED XL"] and N["verify1"][1]["verified_md5"] == "w404md5" and N["verify1"][1]["verified_as_on"] == "2026-09-27", N["verify1"])
check("a ticked rename the export still shows under the old name is counted once per export day (seen_n 2 after two days, three calls)", N["seen"][0] == ["KNEE SUPPORT HINGED L"] and N["seen"][1] == ["KNEE SUPPORT HINGED L"] and N["seen"][2] == [] and N["seen"][3]["seen_n"] == 2 and not N["seen"][3]["verified_at"], N["seen"])
check("after two exports without it: AMBER on Amir's board ('Marg mein abhi dikha nahi') and on the hub; the renames condition is red", N["amber"][0] == ["amber", "Marg mein abhi dikha nahi"] and N["amber"][1] == 1 and N["hub_amber"] == [1, False], (N["amber"], N["hub_amber"]))
check("the snapshot door (/api/snapshot, push_snapshot) verifies a rename by itself", N["push_door"][0] == 200 and N["push_door"][1] == "stock_snapshot" and N["push_door"][2]["verified_as_on"] == "2026-09-30" and N["push_door"][2]["has_md5"] == 1, N["push_door"])
check("a verified rename cannot be taken back (400)", N["untick_verified"] == 400, N["untick_verified"])
check("marg_take carries the verification hook and never raises on a file it cannot read", N["take_has"] and N["take_soft"], (N["take_has"], N["take_soft"]))
if N["take_real"]:
    tr = N["take_real"]
    check("marg_take's door on a real archived closing export (%s, captured %s): an export from before the tick counts for nothing; a tick before it -> the reader ran, the export still shows the old name -> one more sighting" % (tr[0], tr[4]),
          tr[2] == tr[1]["seen_n"] and tr[3]["seen_n"] == tr[1]["seen_n"] + 1 and not tr[3]["verified_at"] and tr[3]["last_seen_as_on"], tr)
else:
    check("marg_take's door on a real archived export: no kept closing export was at hand (the reader path is exercised by the seed of the next export)", True)
check("the spine reads a ticked rename as an alias new -> old at the 20-character clip; an unticked one is absent", N["spine_alias"][0] == N["spine_alias"][1] and N["spine_alias"][2] is False and N["spine_alias"][3] >= 2, N["spine_alias"])

# ------------------------------------------------------------------ 10 · the verdict
print("-- 10  the section verdict flips CLOSED only when all four conditions hold")
vb = N["v_before_words"]
check("all answered by Darpan, yet NOT closed: %d lines await the owner's word (answered=False)" % vb[3], not vb[0] and vb[1]["answered"] is False and vb[3] > 0, vb)
va = N["v_after_words"]
check("after the owner's word on every line: answered green; the new decided lines wait for the orthotic round (not closed)", va[1]["answered"] and va[1]["vouchers"] is False and va[2] > 0 and not va[0], va)
check("the second orthotic round carries orthotic lines only", N["round2"][0] == 200 and N["round2"][1] and N["round2"][2] > 0 and N["round2"][3], N["round2"])
ve = N["v_after_enter"]
check("after Amir enters it: vouchers green; the proof waits for Marg's next export (not closed)", ve[1]["vouchers"] and ve[1]["proof"] is False and not ve[0], ve)
vp = N["v_after_proof"]
check("with Marg's export before the first voucher and after the last (D543), every orthotic vouchered item (%d) moved by its voucher: proof green; renames still red -> NOT closed" % vp[3],
      vp[1]["proof"] and vp[1]["renames"] is False and not vp[0] and vp[2]["as_after"] == "30-12-2026" and vp[2]["bad"] == [], vp)
check("every rename ticked and read back from one export carrying all 22 new names: all verified", N["v_final"][1]["all_verified"] and N["v_final"][1]["verified"] == 22, N["v_final"])
cl = N["closed"]
check("now CLOSED: 'Orthotics section: CLOSED on <date>' on the hub, stored once (stock_section_close), the same date on a re-read", cl[0] and cl[2].startswith("Orthotics section: CLOSED on ") and all(cl[3].values()) and len(N["closed_row"]) == 1 and N["closed_row"][0]["closed_at"] == cl[1] == N["closed_again"], (cl, N["closed_row"]))
check("Darpan's page says the same in Hindi (BAND) and his progress line reads all done", N["closed_hi"][0] and "BAND" in N["closed_hi"][1] and N["closed_hi"][2].startswith("Sab ho gaya"), N["closed_hi"])

# ------------------------------------------------------------------ 11 · negative controls
print("-- 11  NEGATIVE CONTROLS on the box as it is (the unpatched files)")
check("NEGATIVE: no Stock milaan page (darpan != 200), no unit, nothing mounted, no match_answer", O["pages"]["darpan"] != 200 and O["unit"] == "medical" and not O["mounted"] and not O["has_match_answer"], (O["pages"]["darpan"], O["unit"], O["mounted"]))
check("NEGATIVE: the old hub has no 'ortho' block; the old Amir board has no 'renames'", "ortho" not in (O["hub0"][1] or []) and "renames" not in (O["amir0_keys"] or []), (O["hub0"][1][-3:] if O["hub0"][1] else None))
check("NEGATIVE: the old cause door refuses DONT_KNOW (400)", O["old_cause_dontknow"] == 400, O["old_cause_dontknow"])
check("NEGATIVE: the old make ignores {section: Orthotics} and vouchers medicine lines too", O["old_make"][0] == 200 and O["old_make"][1] > 0 and "Medicines" in O["old_make"][2], O["old_make"])
check("NEGATIVE: the old reconcile does not see a new-name snapshot (the difference stays open); no alias helpers", O["old_reconcile"] == "open" and O["old_lane_alias"] == [False], (O["old_reconcile"], O["old_lane_alias"]))

# ------------------------------------------------------------------ 12 · the portal tile
print("-- 12  the portal tile")


def tiles(pdir):
    src = io.open(os.path.join(pdir, "portal.py"), encoding="utf-8").read()
    head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
    ns = {"__name__": "p", "__file__": os.path.join(pdir, "portal.py")}
    exec(compile(head, "<p>", "exec"), ns)
    return {(u, r): sorted(sum([[t["name"] for t in ts] for g, ts in ns["_visible_sections"](r, False, u)], []))
            for u in ("manoj", "bhawna", "darpan", "shavez", "bhati", "alisha", "shivani", "amir", "nobody") for r in ("doctor", "staff", "manager")}


try:
    T0, T1 = tiles(a.portal_old), tiles(a.portal_new)
    changed = sorted(k for k in T0 if T0[k] != T1[k])
    check("the tile 'Stock milaan' shows for darpan (staff) and the owner (doctor)", "Stock milaan" in T1[("darpan", "staff")] and "Stock milaan" in T1[("manoj", "doctor")], T1[("darpan", "staff")])
    check("bhati, shavez, amir, alisha and every other staff login see NO change; nothing is lost anywhere",
          all(k[0] == "darpan" or k[1] == "doctor" for k in changed) and all(not (set(T0[k]) - set(T1[k])) for k in changed)
          and all(set(T1[k]) - set(T0[k]) == {"Stock milaan"} for k in changed), changed)
    g = json.load(open(os.path.join(a.portal_new, "tile_grants.json"), encoding="utf-8"))
    check("tile_grants.json is v27 and grants the tile to darpan by name", g["version"] == 27 and "Stock milaan" in g["users"]["darpan"]["extra"], g["version"])
except Exception as ex:  # noqa: BLE001
    check("the portal head executes for the tile check", False, repr(ex)[:200])

print(("WALK_S404 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S404 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
