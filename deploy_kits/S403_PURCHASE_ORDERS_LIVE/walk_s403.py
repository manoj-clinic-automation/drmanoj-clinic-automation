#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s403.py -- kit S403_PURCHASE_ORDERS_LIVE. THE REAL finance_app.py (a copy of /root/finance carrying the kit's
files) and THE REAL asset app (a copy carrying the patched intake) over SCRATCH COPIES of finance.db and assets.db,
driven through Flask's test client with header identity (walk only). The orthotic items are the real 69; every item it
touches is found BY NAME from what the API returns; its own rows are keyed W403*. It never opens wa.me and sends no
real order: the wa.me link is checked as text and its number is never printed.

  --app NEW  --old OLD  (copies of /root/finance: the kit's files / the box as it is)
  --assets-new DIR --assets-old DIR  (copies of /root/assetapp: the patched intake / the box as it is)
  --db PATH  (the scratch finance.db; PATH.old is made for the old app)   --assets-db PATH  (the scratch assets.db; PATH.old likewise)
  --portal-new DIR / --portal-old DIR   portal.py + tile_grants.json, built and live
"""
import argparse
import datetime as dt
import io
import json
import os
import re
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--assets-new", "--assets-old", "--db", "--assets-db", "--portal-new", "--portal-old"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
assert a.assets_db.startswith("/tmp") or "walk" in a.assets_db, "refusing a non-scratch assets database"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


copydb(a.db, a.db + ".old")
copydb(a.assets_db, a.assets_db + ".old")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s403  # noqa: E402
assert seed_s403.seed(a.db) == 0, "seed failed"
con = sqlite3.connect(a.db, timeout=30)
con.row_factory = sqlite3.Row
print("-- scratch seeded (porders unit, settings); old-app scratch copies made")

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, io, re
from urllib.parse import urlparse, parse_qs, unquote
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
now = lambda: dt.datetime.now().replace(microsecond=0).isoformat()
NUM = re.compile(r"\d{10,}")
out = {"unit": fa._unit_for_path("/finance/porders/api/state"), "mounted": "porders" in fa.app.blueprints}
out["pages"] = {u: G(u, "/finance/porders")[0] for u in ("darpan", "shavez", "shivani", "alisha", "manoj", "bhati", "amir", "bhawna")}
out["needs0"] = G("manoj", "/finance/sanjeevni/api/needs-you")
out["kal0"] = G("darpan", "/finance/darpan/kal/api/day?date=2026-09-25")
out["sc0"] = G("bhati", "/finance/salecheck/api/days")
out["month0"] = G("manoj", "/finance/purchase/page/month/2026-09")[1]
out["scans0"] = G("manoj", "/finance/purchase/page/scans")[1]
out["approvals_page"] = G("manoj", "/finance/approvals")[1]
sys.path.insert(0, os.environ["ASSETSDIR"])
import asset_register as ar
out["ar_prefill"] = hasattr(ar, "_intake_prefill")
if not NEW:
    out["month0"] = ["no scan —" in out["month0"], "no scan</span>" in out["month0"]]
    out["scans0"] = "Unscanned 3 days after arrival" in out["scans0"]
    out["approvals_page"] = "pordersShortCard" in out["approvals_page"]
    out["kal0"] = [out["kal0"][0], "ortho_short" in (out["kal0"][1] if isinstance(out["kal0"][1], dict) else {})]
    out["sc0"] = [out["sc0"][0], "ortho_short" in (out["sc0"][1] if isinstance(out["sc0"][1], dict) else {})]
    out["needs0"] = [l["text"] for l in (out["needs0"][1] or {}).get("lines", [])]
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
import porders, item_alias, purchase_app as pa
out["month0"] = ["no scan —" in out["month0"] and " days</span>" in out["month0"]]
out["scans0"] = "Unscanned 3 days after arrival" in out["scans0"]
out["approvals_page"] = ["pordersShortCard" in out["approvals_page"], "loadPORules" in out["approvals_page"], "poKeep" in out["approvals_page"]]
S = lambda u="darpan": G(u, "/finance/porders/api/state")
out["state_roles"] = {u: [S(u)[0], (S(u)[1] or {}).get("me") if isinstance(S(u)[1], dict) else None] for u in ("darpan", "shavez", "shivani", "alisha", "manoj")}
out["api_gate"] = {u: S(u)[0] for u in ("bhati", "amir", "bhawna")}
st = S()[1]
out["spine_fresh"] = bool(porders._spine_fresh()); out["source0"] = st["source"]
out["state_head"] = {k: st[k] for k in ("vendor", "as_on", "since", "since_text", "count_id", "keep_total")}
out["n_all"] = len(st["all"]); out["n_ortho_map"] = q("SELECT COUNT(*) AS n FROM stock_item_section WHERE section='Orthotics'")[0]["n"]
# the newest as-on by a real date, never by text (the max()-of-text bug)
dates = [r["as_on"] for r in q("SELECT DISTINCT as_on FROM stock_snapshot")]
proper = max(dates, key=lambda d: (d[6:], d[3:5], d[:2])); textmax = max(dates)
out["as_on_check"] = [st["as_on"], proper, textmax]
exact = [x for x in st["all"] if x["family_n"] == 1]
out["shelf_identity"] = [[x["item"], x["shelf"], x["counted"], x["pur"], x["sold"], x["ret"]] for x in exact if abs(x["shelf"] - (x["counted"] + x["pur"] - x["sold"] + x["ret"])) > 1][:5]
fams = {}
for x in st["all"]:
    fams.setdefault(x["family"], []).append(x)
big = {k: v for k, v in fams.items() if len(v) > 1}
out["families"] = {k: [len(v), sum(1 for m in v if m["approx"]), [m["shelf"] for m in v]] for k, v in big.items()}
out["approx_any"] = any(m["approx"] for v in big.values() for m in v)
out["keep_rows"] = q("SELECT COUNT(*) AS n, SUM(source='seed') AS seeded FROM porder_keep")[0]
bad_tier = [r for r in q("SELECT item, keep, seed_keep, sold90, sold180, source FROM porder_keep") if r["seed_keep"] != (2 if r["sold90"] >= 3 else (1 if r["sold180"] >= 1 else 0)) or (r["source"] == "seed" and r["keep"] != r["seed_keep"])]
out["keep_tiers"] = bad_tier[:5]
out["keep0_hidden"] = all(x["short"] == 0 for x in st["all"] if x["keep"] == 0)
out["darpan_json_digits"] = bool(NUM.search(json.dumps(st)))
# the owner's keep: set, survives a re-seed
X = exact[0]["item"]; Y = exact[1]["item"]; Z = exact[2]["item"]
Xs = exact[0]["shelf"]
out["X"] = [X, Xs, Y, Z]
out["keep_set"] = P("manoj", "/finance/porders/api/keep", {"item": X, "keep": Xs + 3})
out["keep_darpan"] = P("darpan", "/finance/porders/api/keep", {"item": X, "delta": 1})[0]
st = S()[1]
xl = [l for l in st["ortho"]["lines"] if l["item"] == X]
out["short_X"] = [xl[0]["short"], xl[0]["keep"], xl[0]["keep_source"], xl[0]["on_order"]] if xl else None
out["keep_survives"] = q("SELECT keep, source, seed_keep FROM porder_keep WHERE item=?", X)[0]
W = next(x for x in st["all"] if x["family_n"] > 1)
Wsz = next(s for s in [m["item"] for m in fams[W["family"]] if m["item"] != W["item"]])
P("manoj", "/finance/porders/api/keep", {"item": W["item"], "keep": W["shelf"] + 2})
st = S()[1]
wl = [l for l in st["ortho"]["lines"] if l["item"] == W["item"]]
out["W"] = [W["item"], Wsz, wl[0]["sizes"] if wl else None, wl[0]["short"] if wl else None, wl[0]["approx"] if wl else None]
out["needs_before"] = [l["text"] for l in G("manoj", "/finance/sanjeevni/api/needs-you")[1]["lines"]]
# --- send: one order, the 04-Sep text, no rate; the number only inside the link
n0 = q("SELECT COUNT(*) AS n FROM purchase_order")[0]["n"]
r = P("darpan", "/finance/porders/api/send", {"lines": [{"item": X, "qty": 3}, {"item": Wsz, "qty": 1}]})
out["send"] = [r[0], (r[1] or {}).get("already"), (r[1] or {}).get("order_id"), (r[1] or {}).get("by")]
wa = (r[1] or {}).get("wa_url") or ""
m = re.match(r"^https://wa\.me/(\d+)\?text=(.*)$", wa)
text = unquote(m.group(2)) if m else ""
out["wa"] = [bool(m), len(m.group(1)) if m else 0, text == "Sanjeevni Medicos, G 15 Rampur Garden, Bareilly\n\n%s — 3 units\n%s — 1 unit" % (X, Wsz), "₹" not in text and "rate" not in text.lower(), text[:60]]
oid1 = (r[1] or {}).get("order_id")
out["order1"] = q("SELECT id, status, sent_by, vendor, section, total_p FROM purchase_order WHERE id=?", oid1)
out["order1_lines"] = q("SELECT item, packs, units, pack_size, supplied, short, missing FROM purchase_order_line WHERE order_id=? ORDER BY id", oid1)
out["orders_n"] = q("SELECT COUNT(*) AS n FROM purchase_order")[0]["n"] - n0
st = S()[1]
xl = [l for l in st["ortho"]["lines"] if l["item"] == X]
out["after_send"] = [[x["on_order"], x["short"]] for x in st["all"] if x["item"] == X][0] + [bool(xl), st["ortho"]["recent"] and st["ortho"]["recent"]["by"]]
r2 = P("darpan", "/finance/porders/api/send", {"lines": [{"item": X, "qty": 3}]})
out["repeat"] = [r2[0], (r2[1] or {}).get("already"), (r2[1] or {}).get("order_id") == oid1, q("SELECT COUNT(*) AS n FROM purchase_order")[0]["n"] - n0]
out["send_bhati"] = P("bhati", "/finance/porders/api/send", {"lines": [{"item": X, "qty": 1}]})[0]
out["send_bad"] = P("darpan", "/finance/porders/api/send", {"lines": [{"item": "NOT AN ITEM", "qty": 1}]})[0]
# --- arrival: Kam aaya, Nahi mila, carry; Sab aa gaya
l1 = q("SELECT id, item FROM purchase_order_line WHERE order_id=? ORDER BY id", oid1)
out["arr_short"] = P("darpan", "/finance/porders/api/arrive", {"order_id": oid1, "line_id": l1[0]["id"], "how": "short", "supplied": 1})
out["arr_short"] = [out["arr_short"][0], (out["arr_short"][1] or {}).get("saved"), (out["arr_short"][1] or {}).get("order_status")]
out["arr_bad"] = P("darpan", "/finance/porders/api/arrive", {"order_id": oid1, "line_id": l1[1]["id"], "how": "short", "supplied": 9})[0]
out["arr_bhati"] = P("bhati", "/finance/porders/api/arrive", {"order_id": oid1, "line_id": l1[1]["id"], "how": "ok"})[0]
out["arr_missing"] = P("shavez", "/finance/porders/api/arrive", {"order_id": oid1, "line_id": l1[1]["id"], "how": "missing"})
out["arr_missing"] = [out["arr_missing"][0], (out["arr_missing"][1] or {}).get("order_status")]
out["arr_again"] = P("darpan", "/finance/porders/api/arrive", {"order_id": oid1, "line_id": l1[0]["id"], "how": "ok"})[1]
out["order1_after"] = q("SELECT status, received_by FROM purchase_order WHERE id=?", oid1) + q("SELECT item, packs, supplied, short, missing, arrived_by FROM purchase_order_line WHERE order_id=? ORDER BY id", oid1)
out["carried"] = pa.norm(X) in pa._carried_shorts(db)
st = S()[1]
out["after_arrival_X"] = [[x["on_order"], x["short"]] for x in st["all"] if x["item"] == X][0]
db.execute("UPDATE purchase_order SET created_at=? WHERE id=?", ((dt.datetime.now() - dt.timedelta(minutes=11)).replace(microsecond=0).isoformat(), oid1)); db.commit()
r3 = P("shivani", "/finance/porders/api/send", {"lines": [{"item": Y, "qty": 2}]}); oid2 = (r3[1] or {}).get("order_id")
out["send2"] = [r3[0], oid2 != oid1, (r3[1] or {}).get("by")]
out["arr_all"] = P("alisha", "/finance/porders/api/arrive", {"order_id": oid2, "all": True})[0]
out["order2_after"] = q("SELECT status, received_by FROM purchase_order WHERE id=?", oid2) + q("SELECT item, packs, supplied, short FROM purchase_order_line WHERE order_id=?", oid2)
# --- detection: a Marg purchase line for an ordered item after the send date
db.execute("UPDATE purchase_order SET created_at=? WHERE id=?", ((dt.datetime.now() - dt.timedelta(minutes=11)).replace(microsecond=0).isoformat(), oid2)); db.commit()
r4 = P("darpan", "/finance/porders/api/send", {"lines": [{"item": Z, "qty": 2}]}); oid3 = (r4[1] or {}).get("order_id")
md5 = q("SELECT md5 FROM purchase_export WHERE superseded_by IS NULL LIMIT 1")[0]["md5"]
db.execute("DELETE FROM purchase_line WHERE bill_no LIKE 'W403%'")
db.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, free, loose_qty, direction, source_md5, line_type) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
           ("YUVIKA SURGICALS", "W403B1", dt.date.today().isoformat(), dt.date.today().isoformat()[:7], item_alias.clip(Z, 27), "1*1", 2, 0, 0, "PURCHASE", md5, "ITEMWISE"))
db.commit()
st = S()[1]
out["detected"] = q("SELECT item, packs, supplied, billed_qty, billed_bill_no, arrived_by FROM purchase_order_line WHERE order_id=?", oid3) + q("SELECT status, received_by FROM purchase_order WHERE id=?", oid3)
# --- scans: the red list, the pre-filled intake, a crafted scan through the REAL intake code, the link
st = S()[1]
B = next((b for b in st["scans"]["bills"] if b["vendor_norm"] == "YUVIKA SURGICALS" and b["red"]), None) or (st["scans"]["bills"][0] if st["scans"]["bills"] else None)
out["scan_bill"] = [B["bill_no"], B["date_text"], B["amount"], B["age"], B["red"], B["intake"]] if B else None
out["scans_n"] = [st["scans"]["n"], st["scans"]["red"]]
month = G("manoj", "/finance/purchase/page/month/" + (B["month"] if B else "2026-09"))[1]
out["month_red"] = ("no scan — %d days" % B["age"]) in month if B else None
out["scans_red"] = "Unscanned 3 days after arrival" in G("manoj", "/finance/purchase/page/scans")[1]
with ar.app.test_request_context("/intake?lane=pharmacy&vendor=YUVIKA%20SURGICALS&bill_no=" + (B["bill_no"] if B else "1") + "&amount=" + (("%.2f" % (B["amount_p"] / 100.0)) if B else "1.00") + "&junk=x&lane_x=y"):
    out["prefill"] = ar._intake_prefill()
with ar.app.test_request_context("/intake?lane=nonsense&vendor=A"):
    out["prefill_badlane"] = ar._intake_prefill()
from werkzeug.datastructures import FileStorage
with ar.app.test_request_context("/intake/submit", method="POST"):
    ar.g.user = {"display_name": "walk-reception", "role": "reception"}
    fs = FileStorage(stream=io.BytesIO(b"%PDF-1.4\n% W403 walk\n"), filename="w403.pdf")
    bid = ar._create_intake_bill(fs, "walk", "pharmacy", {"vendor": "YUVIKA SURGICALS", "bill_no": (B["bill_no"] if B else "1"), "bill_date": (B["bill_date"] if B else "2026-09-18"), "amount": ("%.2f" % (B["amount_p"] / 100.0)) if B else "1.00"})
adb = sqlite3.connect(os.environ["ASSETS_DB"]); adb.row_factory = sqlite3.Row
out["scan_row"] = [dict(r) for r in adb.execute("SELECT id, kind, status, vendor, bill_no, bill_date, total_amount, stamp_no FROM bills WHERE id=?", (bid,))]
st = S()[1]
out["linked"] = q("SELECT bill_id, asset_bill_id, grade, matched_on FROM purchase_scan_link WHERE asset_bill_id=?", bid)
out["scan_gone"] = (B is None) or not any(b["bill_no"] == B["bill_no"] and b["vendor_norm"] == B["vendor_norm"] for b in st["scans"]["bills"])
month2 = G("manoj", "/finance/purchase/page/month/" + (B["month"] if B else "2026-09"))[1]
out["month_linked"] = ("scan exact" in month2) if B else None
# --- medicines: shown, send refused until the owner approves the rules, then allowed
st = S()[1]
out["meds0"] = [st["meds"]["rules_ok"], len(st["meds"]["plan"]["vendors"]), any(l["item"] in {x["item"] for x in st["all"]} for v in st["meds"]["plan"]["vendors"] for l in v["lines"])]
mv = next((v["vendor"] for v in st["meds"]["plan"]["vendors"] if v["has_phone"]), None)
out["med_send_before"] = P("darpan", "/finance/porders/api/send_med", {"vendor": mv})[0] if mv else None
out["rules_get"] = G("manoj", "/finance/porders/api/rules")
out["rules_get"] = [out["rules_get"][0], out["rules_get"][1].get("approved"), sorted((out["rules_get"][1].get("lists") or {}).keys()), (out["rules_get"][1].get("s225") or {}).get("staff_round")]
out["approve_darpan"] = P("darpan", "/finance/porders/api/rules/approve")[0]
out["approve"] = P("manoj", "/finance/porders/api/rules/approve")
out["approve"] = [out["approve"][0], (out["approve"][1] or {}).get("already"), ((out["approve"][1] or {}).get("approved") or {}).get("by")]
out["approve_again"] = (P("manoj", "/finance/porders/api/rules/approve")[1] or {}).get("already")
r5 = P("darpan", "/finance/porders/api/send_med", {"vendor": mv}) if mv else [None, None]
out["med_send_after"] = [r5[0], (r5[1] or {}).get("order_id"), q("SELECT section, status FROM purchase_order WHERE id=?", (r5[1] or {}).get("order_id") or -1)]
# --- the other pages: Darpan's card, Bhati's card, the owner's lines
kal = G("darpan", "/finance/darpan/kal/api/day?date=2026-09-25")[1]
out["kal_card"] = [kal.get("ok"), (kal.get("ortho_short") or {}).get("ok"), (kal.get("ortho_short") or {}).get("n"), (kal.get("ortho_short") or {}).get("url")]
sc = G("bhati", "/finance/salecheck/api/days")[1]
out["sc_card"] = [sc.get("ok"), (sc.get("ortho_short") or {}).get("ok"), (sc.get("ortho_short") or {}).get("n"), bool(NUM.search(json.dumps(sc)))]
st = S()[1]
out["cards_n"] = st["ortho"]["n"]
out["needs_after"] = [l["text"] for l in G("manoj", "/finance/sanjeevni/api/needs-you")[1]["lines"]]
out["summary_owner"] = G("manoj", "/finance/porders/api/summary")[0]
# --- the alias in the shelf (tables as the source): an un-aliased new name maps nothing; a ticked rename maps it
os.environ["PORDERS_SOURCE"] = "tables"
X2 = "SHOULDER IMMOBILISE UNISON L"; X2N = "SHOULDER IMMOB L UNISON"
st = S()[1]; out["source_tables"] = st["source"]
b0 = [x for x in st["all"] if x["item"] == X2][0]
eid = q("SELECT id FROM day_entry WHERE unit='medical' ORDER BY id DESC LIMIT 1")[0]["id"]
db.execute("DELETE FROM sale_line_item WHERE unit='medical' AND bill_no LIKE 'W403%'")
c20 = item_alias.clip(X2N, 20)
db.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical',?,'W403S1',0,1,?,?,'1*1','1',112000)", (eid, dt.date.today().isoformat(), c20, item_alias.sale_key(c20)))
db.commit()
st = S()[1]; b1 = [x for x in st["all"] if x["item"] == X2][0]
item_alias.tick(db, X2, "walk"); db.commit()
st = S()[1]; b2 = [x for x in st["all"] if x["item"] == X2][0]
out["alias"] = [c20, [b0["sold"], b0["shelf"]], [b1["sold"], b1["shelf"]], [b2["sold"], b2["shelf"]], b2["rename"]]
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, assetsdir, mode, dbpath, adb):
    up = os.path.join(os.path.dirname(dbpath), "uploads_" + mode)
    os.makedirs(up, exist_ok=True)
    env = dict(os.environ, APPDIR=appdir, ASSETSDIR=assetsdir, MODE=mode, FINANCE_DB=dbpath, ASSETS_DB=adb, ASSETS_UPLOADS=up,
               FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1")
    env.pop("SARVAM_API_KEY", None)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, a.assets_old, "old", a.db + ".old", a.assets_db + ".old")
N = probe(a.app, a.assets_new, "new", a.db, a.assets_db)

print("-- 1  the unit, the page, the gate")
check("finance_app resolves /finance/porders/... to the unit 'porders' and mounts porders", N["unit"] == "porders" and N["mounted"], (N["unit"], N["mounted"]))
check("darpan, shavez, shivani, alisha and the owner open the page (200); bhati, amir, bhawna cannot (302/403)",
      all(N["pages"][u] == 200 for u in ("darpan", "shavez", "shivani", "alisha", "manoj")) and all(N["pages"][u] in (302, 403) for u in ("bhati", "amir", "bhawna")), N["pages"])
check("the four are 'sender' on the API, the owner 'owner'; bhati, amir, bhawna refused on the API", all(v == [200, "sender"] for k, v in N["state_roles"].items() if k != "manoj")
      and N["state_roles"]["manoj"] == [200, "owner"] and all(s in (302, 401, 403) for s in N["api_gate"].values()), (N["state_roles"], N["api_gate"]))
check("the approvals page carries the owner's Purchase orders section (keep ±, the rules sitting)", all(N["approvals_page"]), N["approvals_page"])

print("-- 2  the shelf: the 06-Sep count + purchases − sales + returns, the spine or the tables, never a text-max date")
check("the state names the vendor, the count date and its source (%s); all 69 orthotics of the map are there" % N["source0"], N["state_head"]["vendor"] == "YUVIKA SURGICALS"
      and N["state_head"]["since"] == "2026-09-06" and N["n_all"] == N["n_ortho_map"] == 69 and N["source0"] in ("spine", "tables"), (N["state_head"], N["n_all"]))
check("the source is the spine when its gate is green and the build fresh (here: fresh=%s)" % N["spine_fresh"], N["source0"] == ("spine" if N["spine_fresh"] else "tables"), N["source0"])
check("NEGATIVE CONTROL (the text-max date bug): the newest Marg closing is picked by its real date (%s), not by text (%s)" % (N["as_on_check"][1], N["as_on_check"][2]),
      N["as_on_check"][0] == N["as_on_check"][1], N["as_on_check"])
check("for every exact item shelf = counted + purchases − sales + returns", N["shelf_identity"] == [], N["shelf_identity"])
check("the 8 clipped families are read as families: the family shelf is exact, the per-size split approx", len(N["families"]) == 8 and N["approx_any"], N["families"])

print("-- 3  keep-in-stock: the seed tiers, the owner's word survives a re-seed, keep 0 hidden")
check("69 keep rows seeded; every seed_keep follows the tiers (2 if ≥3 sold in 90 days, 1 if sold in 180, else 0)", N["keep_rows"]["n"] == 69 and N["keep_tiers"] == [], (N["keep_rows"], N["keep_tiers"]))
check("keep 0 never shows a shortage", N["keep0_hidden"])
check("the owner sets keep on %s to shelf+3: the item is short 3 (source owner, nothing on order); darpan cannot set keep (403)" % N["X"][0],
      N["keep_set"][0] == 200 and N["short_X"] and N["short_X"][0] == 3 and N["short_X"][2] == "owner" and N["short_X"][3] == 0 and N["keep_darpan"] == 403, (N["keep_set"], N["short_X"], N["keep_darpan"]))
check("a re-seed (the next state read) keeps the owner's number", N["keep_survives"]["source"] == "owner" and N["keep_survives"]["keep"] == N["X"][1] + 3, N["keep_survives"])
check("a family item (%s) offers its other size to switch to (%s)" % (N["W"][0], N["W"][1]), N["W"][2] and N["W"][1] in N["W"][2] and N["W"][3] > 0, N["W"])
check("the sender's state JSON carries no 10-digit number (the vendor's phone is never in a page)", N["darpan_json_digits"] is False, N["darpan_json_digits"])

print("-- 4  send: ONE order, the 04-Sep text, no rate, the number only inside the wa.me link; repeat within 10 minutes refused")
check("darpan sends: 200, one purchase_order (sent, by darpan, section Orthotics) with the two lines (3 and the switched size 1)",
      N["send"][0] == 200 and not N["send"][1] and N["send"][3] == "darpan" and N["order1"] and N["order1"][0]["status"] == "sent" and N["order1"][0]["sent_by"] == "darpan"
      and N["order1"][0]["section"] == "Orthotics" and [l["packs"] for l in N["order1_lines"]] == [3, 1] and N["orders_n"] == 1, (N["send"], N["order1"], N["order1_lines"]))
check("the wa.me link carries the vendor's number (%d digits, not printed) and EXACTLY the 04-Sep text: header, blank line, 'Item — qty unit'; no rate, no rupee" % N["wa"][1],
      N["wa"][0] and 12 <= N["wa"][1] <= 15 and N["wa"][2] and N["wa"][3], N["wa"][2:])
check("after the send the item reads on order 3 and short 0; the screen shows 'Order bheja — <time>, darpan'", N["after_send"][0] == 3 and N["after_send"][1] == 0 and N["after_send"][3] == "darpan", N["after_send"])
check("a repeat within 10 minutes returns the same order (already=True), no second order", N["repeat"][0] == 200 and N["repeat"][1] and N["repeat"][2] and N["repeat"][3] == 1, N["repeat"])
check("bhati cannot send (302/403); an unknown item is refused (400)", N["send_bhati"] in (302, 403) and N["send_bad"] == 400, (N["send_bhati"], N["send_bad"]))

print("-- 5  Order aaya?: Kam aaya · Nahi mila · Aa gaya · Sab aa gaya; the short carries")
check("'Kam aaya 1' on the 3-line: stored supplied 1 short 1; the order stays sent while a line is open", N["arr_short"][0] == 200 and N["arr_short"][1] and N["arr_short"][2] == "sent", N["arr_short"])
check("a supplied quantity not below the ordered one is refused (400); bhati is refused (302/403)", N["arr_bad"] == 400 and N["arr_bhati"] in (302, 403), (N["arr_bad"], N["arr_bhati"]))
check("'Nahi mila' on the other line (by shavez): the order is RECEIVED by itself through S225's own door", N["arr_missing"][0] == 200 and N["arr_missing"][1] == "received", N["arr_missing"])
check("a second answer on an answered line writes nothing (already)", (N["arr_again"] or {}).get("already") is True, N["arr_again"])
check("ordered / supplied / missing stored per line; the received order names who received it", N["order1_after"][0]["status"] == "received" and N["order1_after"][0]["received_by"]
      and N["order1_after"][1]["supplied"] == 1 and N["order1_after"][1]["short"] == 1 and N["order1_after"][2]["missing"] == 1 and N["order1_after"][2]["supplied"] == 0, N["order1_after"])
check("the short line carries into the next order (S225 rev 8) and the item is short again (nothing on order)", N["carried"] and N["after_arrival_X"][0] == 0 and N["after_arrival_X"][1] > 0, (N["carried"], N["after_arrival_X"]))
check("a later order (shivani) and 'Sab aa gaya' (alisha): received, every line supplied as ordered", N["send2"][0] == 200 and N["send2"][1] and N["send2"][2] == "shivani" and N["arr_all"] == 200
      and N["order2_after"][0]["status"] == "received" and N["order2_after"][0]["received_by"] == "alisha" and N["order2_after"][1]["supplied"] == N["order2_after"][1]["packs"], (N["send2"], N["arr_all"], N["order2_after"]))
check("DETECTED: a Marg purchase line from the vendor for the ordered item after the send date marks the line billed (qty, bill no) and supplied by 'marg'; the order is received",
      N["detected"] and N["detected"][0]["billed_qty"] == 2 and N["detected"][0]["billed_bill_no"] == "W403B1" and N["detected"][0]["supplied"] == 2 and N["detected"][0]["arrived_by"] == "marg"
      and N["detected"][1]["status"] == "received", N["detected"])

print("-- 6  Bill scan karo: the red list, the pre-filled intake, a crafted scan through the real intake, the link")
sb = N["scan_bill"]
check("the Marg bills with no scan are listed, oldest first, red after 3 days; the intake link carries lane=pharmacy, the vendor, the bill no and the amount",
      sb and sb[4] and "lane=pharmacy" in sb[5] and "vendor=YUVIKA" in sb[5] and ("bill_no=%s" % sb[0]) in sb[5] and "amount=" in sb[5] and N["scans_n"][1] >= 1, sb)
check("the owner's month page marks that bill red ('no scan — N days'); the scan-links page carries the same red list", N["month_red"] and N["scans_red"], (N["month_red"], N["scans_red"]))
check("the intake reads lane / vendor / bill no / amount from the link and drops an unknown lane", N["prefill"].get("lane") == "pharmacy" and N["prefill"].get("vendor") == "YUVIKA SURGICALS"
      and N["prefill"].get("bill_no") == (sb[0] if sb else "1") and "junk" not in N["prefill"] and "lane" not in N["prefill_badlane"], (N["prefill"], N["prefill_badlane"]))
check("a scan through the REAL intake code lands as kind Pharmacy, status captured, with the vendor, bill no and amount on the row, and a stamp",
      N["scan_row"] and N["scan_row"][0]["kind"] == "Pharmacy" and N["scan_row"][0]["status"] == "captured" and N["scan_row"][0]["vendor"] == "YUVIKA SURGICALS"
      and str(N["scan_row"][0]["bill_no"]) == (sb[0] if sb else "1") and N["scan_row"][0]["stamp_no"], N["scan_row"])
check("the next read of the screen matches it EXACT (vendor+bill+amount) and the bill leaves the list; the month page reads 'scan exact'",
      N["linked"] and N["linked"][0]["grade"] == "EXACT" and N["scan_gone"] and N["month_linked"], (N["linked"], N["scan_gone"], N["month_linked"]))

print("-- 7  medicines: shown, send refused until the owner approves the buying rules, then allowed")
check("the medicine proposals (S225 engine) are shown, no orthotic among them; the rules are not yet approved", N["meds0"][0] is False and N["meds0"][1] > 0 and N["meds0"][2] is False, N["meds0"])
check("a medicine send is refused (403) before the approval; darpan cannot approve (403)", N["med_send_before"] == 403 and N["approve_darpan"] == 403, (N["med_send_before"], N["approve_darpan"]))
check("the rules page shows S225's settings and the S341 lists", N["rules_get"][0] == 200 and N["rules_get"][1] is None and N["rules_get"][2] == ["_about", "internal_use", "never_reorder", "on_demand", "orthotics_cycle", "version"] and N["rules_get"][3] == 10, N["rules_get"])
check("the owner approves once (who, when); a second approval answers already", N["approve"][0] == 200 and not N["approve"][1] and N["approve"][2] == "manoj" and N["approve_again"] is True, (N["approve"], N["approve_again"]))
check("then a medicine order goes (section Medicines, sent)", N["med_send_after"][0] == 200 and N["med_send_after"][2] and N["med_send_after"][2][0]["section"] == "Medicines", N["med_send_after"])

print("-- 8  the other places: Darpan's card, Bhati's card (view only), the owner's Needs-you lines")
check("Darpan's 'Kal ka hisaab' carries 'Orthotic kam hai — N' with the button to the screen", N["kal_card"][0] and N["kal_card"][1] and N["kal_card"][3] == "/finance/porders" and N["kal_card"][2] == N["cards_n"], N["kal_card"])
check("Bhati's list carries the same card, view only, no number in it", N["sc_card"][0] and N["sc_card"][1] and N["sc_card"][2] == N["cards_n"] and N["sc_card"][3] is False, N["sc_card"])
nb = N["needs_before"]
check("the owner's Needs you: 'Orthotic shortages: N items — order not sent', 'Bill scan pending on N purchase bills', 'Buying rules for medicines await your approval'",
      any(t.startswith("Orthotic shortages:") and "order not sent" in t for t in nb) and any(t.startswith("Bill scan pending on") for t in nb) and any(t.startswith("Buying rules for medicines") for t in nb), nb)
check("after the approval the rules line is gone; the summary door answers the owner", not any(t.startswith("Buying rules") for t in N["needs_after"]) and N["summary_owner"] == 200, N["needs_after"])

print("-- 9  the rename memory in the shelf (tables as the source)")
al = N["alias"]
check("with the source pinned to the tables, a sale line under an UN-TICKED rename's new name (%s) maps nothing" % al[0], N["source_tables"] == "tables" and al[2] == al[1], al)
check("once the rename is ticked the same line counts for the old item: sold +1, shelf −1", al[3][0] == al[1][0] + 1 and al[3][1] == al[1][1] - 1 and (al[4] or {}).get("state") == "done", al)

print("-- 10  NEGATIVE CONTROLS on the box as it is (the unpatched files)")
check("NEGATIVE: no Purchase orders page for darpan (%s), unit medical, nothing mounted" % O["pages"]["darpan"], O["pages"]["darpan"] != 200 and O["unit"] == "medical" and not O["mounted"], (O["unit"], O["mounted"]))
check("NEGATIVE: the old Needs you has none of the three lines", not any(t.startswith(("Orthotic shortages", "Bill scan pending", "Buying rules")) for t in O["needs0"]), O["needs0"])
check("NEGATIVE: the old day payload of Darpan and the old list of Bhati carry no orthotic card", O["kal0"][1] is False and O["sc0"][1] is False, (O["kal0"], O["sc0"]))
check("NEGATIVE: the old month page has plain 'no scan' (no day count); the old scan-links page has no red list", O["month0"] == [False, True] and O["scans0"] is False, (O["month0"], O["scans0"]))
check("NEGATIVE: the old approvals page has no Purchase orders section; the old intake has no prefill", O["approvals_page"] is False and O["ar_prefill"] is False, (O["approvals_page"], O["ar_prefill"]))

print("-- 11  the portal tile")


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
    four = ("darpan", "shavez", "shivani", "alisha")
    check("the tile 'Purchase orders' shows for darpan, shavez, shivani, alisha (staff) and the owner (doctor)", all("Purchase orders" in T1[(u, "staff")] for u in four) and "Purchase orders" in T1[("manoj", "doctor")], T1[("alisha", "staff")])
    check("bhati, amir and every other login see NO change; nothing is lost anywhere", all(k[0] in four or k[1] == "doctor" for k in changed) and all(not (set(T0[k]) - set(T1[k])) for k in changed)
          and all(set(T1[k]) - set(T0[k]) == {"Purchase orders"} for k in changed), changed)
    g = json.load(open(os.path.join(a.portal_new, "tile_grants.json"), encoding="utf-8"))
    check("tile_grants.json is v28 and grants the tile to the four by name, not to bhati", g["version"] == 28 and all("Purchase orders" in g["users"][u]["extra"] for u in four) and "Purchase orders" not in g["users"]["bhati"]["extra"], g["version"])
except Exception as ex:  # noqa: BLE001
    check("the portal head executes for the tile check", False, repr(ex)[:200])

print(("WALK_S403 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S403 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
