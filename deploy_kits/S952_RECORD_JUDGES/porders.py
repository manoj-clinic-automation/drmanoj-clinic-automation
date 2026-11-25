#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  porders.py  ·  v1.1  ·  kit S410_MEDICINE_ORDERING  ·  Session 283 (Sanjeevni)  ·  D626
#
#  v1.1 (S410, D626, 26-Sep-2026): mounts order_rules (the medicine buying rules as settings, fixed order days, the ordering
#  team's day); state() carries 'today' (the day's proposals, the freeze, the contextual text); send_med refuses while frozen.
#
#  S593 (D743, 19-Oct-2026): detect_supplies asks THE ONE arrivals rule (stock_figure.carried, rules c / d, on the spine by the spine's key)
#  which Marg bill carries an open order line and writes the packs of that bill's own line -- its table read (purchase_line) and 20-letter
#  clip are gone; send_med refuses outright on order.source = darpan (F-738: that door bypasses Darpan's pakka).
#
#  S417 (F-636, 26-Sep-2026): the stock beside an order reads in the order's own unit -- the plan lines and the day's proposals carry
#  stock_text ('12 strips + 4', '3 bottles', '5 units', from purchase_app.stock_text), the orthotic lines carry shelf_text in pieces.
#  Every figure stays as it was; the words are added beside it.
#
#  S440 (D640, F-662, 30-Sep-2026): section 3 is "Scan ka kaam" -- ONE list, a tap per line: Scan karo / Yahi bill hai? / Supplier chuno /
#  Amount milao / Marg ka intezaar (the block at the foot of this file). state() carries 'kaam'; 'scans' stays as S403 built it
#  (unscanned_bills() is unchanged: the month-end checklist still counts every bill with no link).
#
#  ONE SCREEN -- "Purchase orders" (the owner, 26-Sep-2026): the shortage comes, the WhatsApp message goes,
#  the purchase arrives, the bill is scanned, and what was ordered / supplied / billed is on record. Hindi,
#  phone-first, every section collapsed until tapped; no typing except the supplied quantity on 'Kam aaya'.
#  Orthotics first (supplier Yuvika, from the 06-Sep count); medicines wait for the owner's buying rules.
#
#  REUSES, never a second ordering system: purchase_app (S225) -- the order book (purchase_order /
#  purchase_order_line), _staff_send (the 04-Sep WhatsApp text, wa.me link built server-side, SENT by
#  whom / when), _arrive (S225 rev 8: supplied / short per line, the short carried), the scan match
#  (_rematch_if_changed), the vendor phone (never in any page: only inside the wa.me link, only to a sender).
#
#  WHAT THIS FILE IS
#    * the page      GET  /finance/porders                       (porders.html; the owner sees it in English)
#    * its API       GET  /finance/porders/api/state              the four sections
#                    POST /finance/porders/api/send   {lines:[{item, qty}]}       one order to the orthotic vendor -> wa.me
#                    POST /finance/porders/api/send_med {vendor}                   a medicine order (only once the rules are approved)
#                    POST /finance/porders/api/arrive {order_id, line_id, how, supplied} | {order_id, all:true}
#                    POST /finance/porders/api/keep   {item, delta}               the owner's keep-in-stock +/- (audited)
#                    POST /finance/porders/api/rules/approve                      the owner approves the medicine buying rules
#    * read helpers the other pages call in-process, every one fail-soft:
#                    shortage_summary(con)   needs_you_lines(con)   unscanned_bills(con)
#
#  THE RULES (D618)
#    shelf now (orthotics) = 06-Sep counted qty + purchases since (the vendor, 27-char exact) - sales since + returns,
#    the rename memory (item_alias) applied; Marg's closing shown beside it as a cross-check, never the base.
#    A family whose names Marg clips to one 20-character key: the FAMILY shelf is exact, the per-size split is
#    'approx' (in proportion to the count) until its renames are verified; a short family orders the size with the
#    lowest count and the sender can switch the size before sending.
#    keep-in-stock per orthotic: seed 2 if >= 3 units sold in 90 days, 1 if sold at least once in 180 days, else 0;
#    a re-seed never overwrites an owner-set number.  on order = units on SENT orders not yet received.
#    shortage = keep - shelf - on order, when > 0.  keep 0 never shows.
#    Sales and purchases come from the spine's read door when its gate is green and its build is fresh, else from
#    the tables -- the payload says which.
# =============================================================================
import datetime as dt
import json
import os
import re
import sqlite3
import sys

from flask import Blueprint, jsonify, request, send_file
_SHARED_S441 = os.environ.get("SHARED_LIB_DIR", "/root/shared")       # S441: scan_checks_s441 lives there (the asset app imports it too)
if _SHARED_S441 and _SHARED_S441 not in sys.path:
    sys.path.append(_SHARED_S441)
try:
    import scan_checks_s441 as S441
except Exception:                                             # noqa: BLE001 -- the screen never waits on it
    S441 = None

VERSION = "1.3"   # S952 (D1065): detect_supplies -- the order's own scanned bill (rule 0), a missing line never takes a bill, the scan repair first; S441 (parent, declared on board/_numbers): the shared Reception login names who works; Scan ka kaam carries "Dobara scan? / Galat lane?"
KIT = "S410_MEDICINE_ORDERING"
bp = Blueprint("porders", __name__)
_db = _require = None
_unit = "medical"
ACCESS_UNIT = "porders"
SECTION = "Orthotics"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
PAGE = os.path.join(HERE, "porders.html")
REPEAT_MIN = 10
SCAN_RED_DAYS = 3
SPINE_DIR = os.path.join(HERE, "spine")
SPINE_FRESH_HOURS = 36
DEFAULTS = {"porders.senders": "manoj,darpan,shavez,shivani,alisha,reception", "porders.viewers": "bhati",
            "porders.ortho_vendor": "YUVIKA SURGICALS"}
DDL = (
    "CREATE TABLE IF NOT EXISTS porder_keep ("
    " item TEXT PRIMARY KEY, keep INTEGER NOT NULL, source TEXT NOT NULL, seed_keep INTEGER,"
    " sold90 INTEGER, sold180 INTEGER, set_by TEXT, set_at TEXT NOT NULL)",
)
S628_COLS = (("purchase_order_line", "billed_units", "INTEGER"), ("purchase_order_line", "other_supplier", "TEXT"),   # S628 (D761)
             ("purchase_order_line", "other_bill_no", "TEXT"), ("purchase_order_line", "other_date", "TEXT"), ("purchase_order_line", "other_qty", "INTEGER"))
LINE_COLS = (("purchase_order_line", "missing", "INTEGER NOT NULL DEFAULT 0"), ("purchase_order_line", "billed_qty", "INTEGER"),
             ("purchase_order_line", "billed_bill_no", "TEXT"), ("purchase_order_line", "billed_date", "TEXT"),
             ("purchase_order_line", "detected_at", "TEXT"), ("purchase_order_line", "arrived_by", "TEXT"),
             ("purchase_order_line", "arrived_at", "TEXT"), ("purchase_order", "section", "TEXT")) + S628_COLS


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    # S410 (D626): the medicine buying rules as settings ride on this screen's unit; fail-soft -- the screen never waits for them
    try:
        import order_rules                                    # noqa: PLC0415
        order_rules.init(app, db_getter, require_fn, unit=ACCESS_UNIT)
    except Exception as _ex_or:                               # noqa: BLE001
        print("order_rules NOT mounted: %s" % _ex_or, file=sys.stderr)
    try:                                                      # S454 (D666 / D668): the one-task reception screens; fail-soft
        import porders_s454                                   # noqa: PLC0415
        porders_s454.init(app)
    except Exception as _ex_s454:                             # noqa: BLE001
        print("porders_s454 NOT mounted: %s" % _ex_s454, file=sys.stderr)
    return bp


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _pa():
    import purchase_app                                       # noqa: PLC0415 -- beside this file, mounted first
    return purchase_app


def _ia():
    import item_alias                                         # noqa: PLC0415
    return item_alias


def ensure_schema(con):
    for ddl in DDL:
        con.execute(ddl)
    for table, col, typ in LINE_COLS:
        try:
            have = {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}
            if col not in have:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, typ))
        except sqlite3.Error:
            pass
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, v in DEFAULTS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, "S403 D618 -- a data edit changes it"))


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r and (r[0] or "").strip() else default)
    except sqlite3.Error:
        return default


def _names(con, key):
    return [p.strip().lower() for p in re.split(r"[,;\s]+", _setting(con, key, DEFAULTS.get(key, ""))) if p.strip()]


def vendor_of(con):
    return _setting(con, "porders.ortho_vendor", DEFAULTS["porders.ortho_vendor"]).strip()


def _rules_ok(con):
    raw = _setting(con, "porders.rules_approved", "")
    try:
        j = json.loads(raw) if raw else None
    except ValueError:
        j = None
    return j if (j and j.get("by") and j.get("at")) else None


def _audit(con, who, action, ref="", detail=None):
    try:
        _pa()._audit(con, who, action, ref, detail)
    except Exception:                                         # noqa: BLE001 -- the row itself is the record
        pass


def _stamp(ts):
    try:
        return dt.datetime.fromisoformat(str(ts)[:19]).strftime("%d-%m-%Y %H:%M") + " IST"
    except (TypeError, ValueError):
        return str(ts or "")


def _dmy(iso):
    s = str(iso or "")[:10]
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else s


def _within(ts, minutes=REPEAT_MIN):
    try:
        return (dt.datetime.now() - dt.datetime.fromisoformat(str(ts)[:19])) <= dt.timedelta(minutes=minutes)
    except (TypeError, ValueError):
        return False


# ------------------------------------------------------------------ the count and the items
def count_info(con):
    """The 06-Sep count: its id and ISO date (the sales/purchases window starts there)."""
    r = con.execute("SELECT id, marg_as_on FROM stock_count WHERE unit=? AND status='submitted' AND id NOT IN "
                    "(SELECT count_id FROM stock_count_part) ORDER BY id LIMIT 1", (_unit,)).fetchone()
    if not r:
        return 1, "2026-09-06"
    s = str(r[1] or "")
    iso = "%s-%s-%s" % (s[6:10], s[3:5], s[0:2]) if re.fullmatch(r"\d{2}-\d{2}-\d{4}", s) else s
    return int(r[0]), iso


def _newest_as_on(con):
    rows = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    if not rows:
        return ""
    return max(rows, key=lambda d: (str(d)[6:], str(d)[3:5], str(d)[:2]))


def ortho_items(con):
    """The orthotic items of the section map with the count, the newest Marg figure (alias applied), packing,
    the family (the 20-character clip Marg's sale export prints) and the rename memory's word on each."""
    ia = _ia()
    cid, _iso = count_info(con)
    counted = {r[0]: int(r[1] or 0) for r in con.execute("SELECT item, counted_qty FROM stock_count_item WHERE count_id=?", (cid,))}
    as_on = _newest_as_on(con)
    snap = {}
    if as_on:
        for r in con.execute("SELECT item, qty, packing, pack_size FROM stock_snapshot WHERE as_on=?", (as_on,)):
            snap[r[0]] = (int(r[1] or 0), r[2] or "", int(r[3] or 1))
    ren = {r["old_name"]: r for r in ia.rows(con)}
    newnames = {r["new_name"] for r in ren.values() if r["done_at"]}   # a ticked rename's NEW name is an alias, never a second item
    out = []
    for r in con.execute("SELECT item FROM stock_item_section WHERE section=? ORDER BY item", (SECTION,)):
        name = r[0]
        if name in newnames:
            continue
        forms = [name] + ia.aliases_of(con, name)
        m = None
        for f in forms:
            if f in snap:
                m = (snap[f][0] if m is None else m + snap[f][0])
        packing = next((snap[f][1] for f in forms if f in snap), "1*1")
        rr = ren.get(name)
        out.append(dict(item=name, counted=counted.get(name, 0), marg=m, packing=packing or "1*1",
                        family=ia.clip(name, ia.SALE_CLIP), key20=ia.sale_key(ia.clip(name, ia.SALE_CLIP)),
                        keys_sale={ia.sale_key(ia.clip(name, ia.SALE_CLIP))} | ({ia.sale_key(ia.clip(rr["new_name"], ia.SALE_CLIP))} if rr and rr["done_at"] else set()),
                        keys_pur={ia.pad_norm(ia.clip(name, ia.PURCHASE_CLIP))} | ({ia.pad_norm(ia.clip(rr["new_name"], ia.PURCHASE_CLIP))} if rr and rr["done_at"] else set()),
                        rename=(dict(new=rr["new_name"], state=rr["state"]) if rr else None),
                        verified=bool(rr and rr["verified_at"])))
    fam = {}
    for it in out:
        fam.setdefault(it["family"], []).append(it)
    for it in out:
        it["family_n"] = len(fam[it["family"]])
        it["sizes"] = [x["item"] for x in fam[it["family"]] if x["item"] != it["item"]]
    return out, as_on, cid


# ------------------------------------------------------------------ sales and purchases: the spine or the tables
def _spine_fresh():
    if os.environ.get("PORDERS_SOURCE", "").lower() == "tables":      # the walk pins the source; the service never sets it
        return None
    try:
        st = json.load(open(os.path.join(SPINE_DIR, "spine_state.json")))
        if not st.get("passed"):
            return None
        built = dt.datetime.fromisoformat(str(st.get("last_success_iso") or "")[:19])
        if dt.datetime.now() - built > dt.timedelta(hours=SPINE_FRESH_HOURS):
            return None
        if SPINE_DIR not in sys.path:
            sys.path.insert(0, SPINE_DIR)
        import spine_read                                     # noqa: PLC0415
        return spine_read.Spine(os.path.join(SPINE_DIR, "spine.db"))
    except Exception:                                         # noqa: BLE001
        return None


def _movements(con, since_iso, vendor_norm, upto_iso=None):
    """{sale key: (sold, returned)}, {purchase key: units}, and the source name. Keys are the printed
    clips' keys (sales: finance_returns.norm of the 20-char name; purchases: _pad_norm of the 27-char name)."""
    ia = _ia()
    upto = upto_iso or dt.date.today().isoformat()
    sp = _spine_fresh()
    sales, purch = {}, {}
    if sp is not None:
        try:
            for r in sp.q("SELECT name20, units, bill FROM sp_sale_line WHERE date>=? AND date<=?", since_iso, upto):
                k = ia.sale_key(r["name20"])
                ret = str(r["bill"] or "").startswith("CN")
                s, t = sales.get(k, (0, 0))
                u = abs(float(r["units"] or 0))
                sales[k] = (s, t + u) if ret else (s + u, t)
            supkey = re.sub(r"[^A-Z]", "", vendor_norm.upper())[:8]
            for r in sp.q("SELECT name27, units, direction FROM sp_purchase_line WHERE supkey=? AND date>? AND date<=?", supkey, since_iso, upto):
                k = ia.pad_norm(r["name27"])
                purch[k] = purch.get(k, 0) + (abs(float(r["units"] or 0)) * (-1 if r["direction"] == "RETURN" else 1))
            return sales, purch, "spine"
        except Exception:                                     # noqa: BLE001 -- the tables are the fallback
            sales, purch = {}, {}
    pa = _pa()
    for r in con.execute("SELECT item_name, item_key, qty_raw, pack, is_return FROM sale_line_item WHERE unit=? "
                         "AND business_date>=? AND business_date<=?", (_unit, since_iso, upto)):
        k = ia.sale_key(r[0]) or r[1]
        u = pa._units(r[2], 1)                                # an orthotic is pack 1: a plain figure is pieces
        s, t = sales.get(k, (0, 0))
        sales[k] = (s, t + u) if r[4] else (s + u, t)
    for r in con.execute("SELECT l.item, l.qty, l.free, l.direction FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_date>? "
                         "AND l.bill_date<=? AND " + pa.EFF_LINE, (vendor_norm, since_iso, upto)):
        k = ia.pad_norm(r[0])
        u = float(r[1] or 0) + float(r[2] or 0)
        purch[k] = purch.get(k, 0) + (-u if str(r[3] or "").upper().startswith("RET") else u)
    return sales, purch, "tables"


def _apportion(items, sales, purch):
    """Per item: exact and pooled sales / purchases, the shelf, the approx flag."""
    own_s, own_p = {}, {}
    for it in items:
        for k in it["keys_sale"]:
            own_s.setdefault(k, []).append(it["item"])
        for k in it["keys_pur"]:
            own_p.setdefault(k, []).append(it["item"])
    fam = {}
    for it in items:
        fam.setdefault(it["family"], []).append(it)
    for members in fam.values():
        pool_s = pool_r = pool_p = 0.0
        seen_s, seen_p = set(), set()
        for it in members:
            it["sold"] = it["ret"] = it["pur"] = 0.0
            for k in it["keys_sale"]:
                s, t = sales.get(k, (0, 0))
                if len(own_s.get(k, [])) == 1:
                    it["sold"] += s
                    it["ret"] += t
                elif k not in seen_s:
                    pool_s += s
                    pool_r += t
                    seen_s.add(k)
            for k in it["keys_pur"]:
                u = purch.get(k, 0)
                if len(own_p.get(k, [])) == 1:
                    it["pur"] += u
                elif k not in seen_p:
                    pool_p += u
                    seen_p.add(k)
        tot_c = sum(it["counted"] for it in members)
        n = len(members)
        pooled = bool(pool_s or pool_r or pool_p)
        fam_shelf = sum(it["counted"] + it["pur"] - it["sold"] + it["ret"] for it in members) + pool_p - pool_s + pool_r
        for it in members:
            share = (it["counted"] / float(tot_c)) if tot_c > 0 else 1.0 / n
            it["pool_sold"], it["pool_ret"], it["pool_pur"] = round(share * pool_s, 2), round(share * pool_r, 2), round(share * pool_p, 2)
            it["shelf"] = int(round(it["counted"] + it["pur"] - it["sold"] + it["ret"] + share * (pool_p - pool_s + pool_r)))
            it["family_shelf"] = int(round(fam_shelf))
            it["approx"] = bool(n > 1 and pooled and not it["verified"])
            it["sold_all"] = it["sold"] + it["pool_sold"]
    return items


def _keep_seed(con, items, sales90, sales180):
    """Seed the keep numbers where absent; a re-seed never overwrites the owner's word."""
    now = now_iso()
    for it in items:
        s90 = int(round(it.get("_s90") or 0))
        s180 = int(round(it.get("_s180") or 0))
        seed = 2 if s90 >= 3 else (1 if s180 >= 1 else 0)
        r = con.execute("SELECT keep, source FROM porder_keep WHERE item=?", (it["item"],)).fetchone()
        if r is None:
            con.execute("INSERT INTO porder_keep (item, keep, source, seed_keep, sold90, sold180, set_by, set_at) VALUES (?,?,?,?,?,?,?,?)",
                        (it["item"], seed, "seed", seed, s90, s180, "seed", now))
            it["keep"], it["keep_source"] = seed, "seed"
        else:
            if r[1] == "seed" and int(r[0]) != seed:
                con.execute("UPDATE porder_keep SET keep=?, seed_keep=?, sold90=?, sold180=?, set_at=? WHERE item=?", (seed, seed, s90, s180, now, it["item"]))
                it["keep"], it["keep_source"] = seed, "seed"
            else:
                con.execute("UPDATE porder_keep SET seed_keep=?, sold90=?, sold180=? WHERE item=?", (seed, s90, s180, it["item"]))
                it["keep"], it["keep_source"] = int(r[0]), r[1]
        it["seed_keep"], it["sold90"], it["sold180"] = seed, s90, s180
    con.commit()


def _on_order(con, vendor):
    """{item: units on SENT orders of the vendor whose line nobody has answered yet}."""
    out = {}
    ren = {}                                                  # S932 (F-1579): {ticked NEW name: OLD name}, EXACT names only -- a line ordered under
    try:                                                      # Marg's current name counts for the lane's own (old) key; a clip never folds (siblings
        olds = set()                                          # share it); a chain's middle name (X->Y and Y->Z) folds nothing
        rows = [x for x in _ia().done_rows(con) if x.get("old_name") and x.get("new_name")]
        olds = {str(x["old_name"]) for x in rows}
        ren = {str(x["new_name"]): str(x["old_name"]) for x in rows if str(x["new_name"]) not in olds}
    except Exception:                                         # noqa: BLE001
        ren = {}
    try:
        for r in con.execute("SELECT l.item, l.packs FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE (o.status='sent'" + _s454_or_arrived(con) + ") AND o.vendor=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",
                             (vendor,)):                   # S454 (4.4): arrived by its bill's scan = counted until Marg answers
            k = ren.get(r[0], r[0])
            out[k] = out.get(k, 0) + int(r[1] or 0)
    except sqlite3.Error:
        pass
    return out


def shelf(con):
    """The whole orthotic picture: every item with shelf, Marg, keep, on order, shortage."""
    ensure_schema(con)
    items, as_on, cid = ortho_items(con)
    _cid, since = count_info(con)
    vendor = vendor_of(con)
    vnorm = _pa().supplier_key(vendor)
    sales, purch, source = _movements(con, since, vnorm)
    _apportion(items, sales, purch)
    today = dt.date.today()
    s90, _p90, _src = _movements(con, (today - dt.timedelta(days=90)).isoformat(), vnorm)
    s180, _p180, _src2 = _movements(con, (today - dt.timedelta(days=180)).isoformat(), vnorm)
    for it in items:
        own = {}
        for k in it["keys_sale"]:
            own[k] = sum(1 for x in items if k in x["keys_sale"])
        n = it["family_n"]

        def tot(sm):
            t = 0.0
            for k in it["keys_sale"]:
                s, _r = sm.get(k, (0, 0))
                t += s if own[k] == 1 else s / float(max(1, n))
            return t
        it["_s90"], it["_s180"] = tot(s90), tot(s180)
    _keep_seed(con, items, s90, s180)
    onord = _on_order(con, vendor)
    for it in items:
        it["on_order"] = onord.get(it["item"], 0)
        it["short"] = max(0, int(it["keep"]) - int(it["shelf"]) - int(it["on_order"])) if int(it["keep"]) > 0 else 0
        for k in ("keys_sale", "keys_pur"):
            it[k] = sorted(it[k])
    # a short family orders the size with the lowest count first: the family's own shortage lands on that size
    fam = {}
    for it in items:
        fam.setdefault(it["family"], []).append(it)
    for members in fam.values():
        if len(members) < 2 or not any(m["approx"] for m in members):
            continue
        keep_sum = sum(int(m["keep"]) for m in members)
        if keep_sum <= 0:
            continue
        fam_short = max(0, keep_sum - members[0]["family_shelf"] - sum(m["on_order"] for m in members))
        given = sum(m["short"] for m in members)
        if fam_short > given:
            low = min((m for m in members if int(m["keep"]) > 0), key=lambda m: (m["shelf"], m["item"]))
            low["short"] += fam_short - given
            low["family_topup"] = fam_short - given
    return dict(items=items, as_on=as_on, count_id=cid, since=since, vendor=vendor, vendor_norm=vnorm, source=source)


# ------------------------------------------------------------------ orders: sent, arrival, detection
def _orders(con):
    """Every SENT or RECEIVED order, newest first, each line with its state: open | ok | short | missing."""
    out = []
    q = "SELECT * FROM purchase_order WHERE status IN ('sent','received') ORDER BY id DESC LIMIT 60"
    for o in con.execute(q):
        o = dict(o)
        lines = [dict(l) for l in con.execute("SELECT * FROM purchase_order_line WHERE order_id=? ORDER BY id", (o["id"],))]
        for l in lines:
            l["state"] = ("missing" if l.get("missing") else ("ok" if (l.get("supplied") is not None and int(l["supplied"]) >= int(l["packs"])) else
                          ("short" if l.get("supplied") is not None else "open")))
        o["lines"] = lines
        o["open_lines"] = sum(1 for l in lines if l["state"] == "open")
        o["sent_text"] = _stamp(o["created_at"])
        o["received_text"] = _stamp(o["received_at"]) if o.get("received_at") else ""
        out.append(o)
    return out


def _s628_cols(con):
    """S628: the five columns of S628_COLS, added when absent (ensure_schema adds them too; detect_supplies does not wait for a page)."""
    for table, col, typ in S628_COLS:
        try:
            if col not in {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, typ))
        except sqlite3.Error:
            pass


def _s628_packs(hit, ps):
    """S628 (D761, LINVIZ 600): the order's packs that a matched bill line brings -> (packs, units or None). When the bill line's packing and the
    order line's pack size are both read (1*N) and differ, the tablets decide: floor(tablets / the order's pack size), the tablets kept beside it;
    else qty + free as S598 (two batches of one item on one bill summed by carried())."""
    q = float(hit.get("qty") or 0) + float(hit.get("free") or 0)
    try:
        import med_names                                      # noqa: PLC0415
        nb = med_names.packn(hit.get("packing"))
    except Exception:                                         # noqa: BLE001
        nb = None
    try:
        ps = int(ps or 1)
    except (TypeError, ValueError):
        ps = 1
    if nb and ps > 1 and nb != ps:
        units = int(round(q * nb))
        return units // ps, units
    return int(round(q)), None


def detect_supplies(con):
    """Marg's purchase that carries an open order line marks the line billed (qty in PACKS, bill no, date) -- and supplied, when nobody
    tapped. S593 (D743; S583's 'two copies' closed): WHICH bill carries the line is THE ONE RULE, stock_figure.carried() on the spine by the
    spine's key -- accepted here only by rule (c) (the order's own vendor, dated up to arrival.back_days before the order day) or (d) (the own
    vendor on or after the order day); (a) cannot occur (billed_bill_no is NULL here); (e), another supplier's bill, counts for stock only and
    never marks this line billed. The packs are THE MATCHED BILL LINE's own: qty + free as carried() returns them (S598, F-942: the line of
    the order line's own printed name, never the family's sum for the key; two batches of one item on one bill arrive summed; never
    units / pack_size: a 'whole' key's units are its qty). A fresh Ctx per row, so rule (b) sees each write (two lines of one key, two bills).
    The spine unread (sw.ok False): nothing written, one stderr line. The tables (purchase_line) and the 20-letter clip are read no more. Idempotent.
    S628 (D761): (0) the one name list learns first (med_names.learn, fail-soft) -- so a Marg item that is the ordered medicine under another name
    (THIO Q AP TAB for THIO Q AP) carries the line through carried(); (1) the packs by tablets when the bill's packing differs from the order's
    pack size (_s628_packs; billed_units kept); (2) a billed line below its packs is read again by rule (a) on every pass and RAISED when the bill's
    matching lines now give more (F-990: the two ZUPRINOR 5 lines of JP23217), never lowered, audited line_redetected; (3) after every own-dealer
    line is marked, a line still unbilled whose medicine came on ANOTHER dealer's bill (rule e) dated within names.window_days of the order day
    gets other_supplier / other_bill_no / other_date / other_qty (F-991) -- it is NOT marked billed (D743 stands: stock only), audited
    line_other_dealer. Returns the count of lines marked or raised."""
    n = 0
    _s628_cols(con)
    try:                                                      # S952 (D1065): the answers made before rule 0 righted by each order's scanned bill
        import record_judges                                  # noqa: PLC0415
        if record_judges.pair_on(con) and record_judges.repair_due(con):   # only when a link, a tie, an answer or the spine moved
            n += int(record_judges.scan_repair(con).get("done") or 0)
    except Exception as _ex_rj:                               # noqa: BLE001 -- never blocks the pass
        print("porders.detect_supplies: the S952 scan repair failed (%s) -- the pass runs on" % _ex_rj, file=sys.stderr)
    try:                                                      # S628 (0): the one name list first -- never blocks the pass
        import med_names                                      # noqa: PLC0415
        med_names.learn(con)
    except Exception as _ex_mn:                               # noqa: BLE001
        print("porders.detect_supplies: med_names.learn failed (%s) -- the pass runs on the list as it stands" % _ex_mn, file=sys.stderr)
    try:
        rows = con.execute("SELECT l.id, l.item, l.packs, l.supplied, l.missing, o.vendor, o.created_at, l.pack_size FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN ('sent','received') AND l.billed_qty IS NULL").fetchall()
        again = con.execute("SELECT l.id, l.item, l.packs, l.supplied, l.missing, o.vendor, o.created_at, l.pack_size, l.billed_qty, l.billed_bill_no, "
                            "l.billed_date, l.arrived_by FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                            "WHERE o.status IN ('sent','received') AND l.billed_qty IS NOT NULL AND COALESCE(l.billed_bill_no,'')<>'' "
                            "AND l.billed_qty < l.packs").fetchall()
    except sqlite3.Error:
        return 0
    if not rows and not again:
        return 0
    import stock_figure as SF                                 # noqa: PLC0415 -- beside this file: the one stock function (S577 / S583 / S587)
    import stock_watch as SW                                  # noqa: PLC0415
    sw = SW.Spine()
    if not getattr(sw, "ok", False):
        print("porders.detect_supplies: the spine could not be read -- no order line marked billed (S593)", file=sys.stderr)
        return 0
    try:
        win = int(float(_setting(con, "names.window_days", "7") or 7))
    except (TypeError, ValueError):
        win = 7
    try:
        for r in rows:
            lid, item, packs, supplied, missing, vendor, created, ps = r[0], r[1], int(r[2] or 0), r[3], r[4], r[5], str(r[6] or ""), r[7]
            line = dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=None, own_only=True)   # S628: the own dealer first
            ctx = SF._ctx(con, sw, None)                      # R1-C10: a fresh context per row -- the per-key taken-bills cache must see each write
            if missing:
                continue                                      # S952: reception marked it missing -- it never came; it never takes a bill
            hit = SF.carried(con, sw, line, ctx)
            if not hit or hit.get("how") not in ("c", "d", "s"):   # S952: 's' -- the order's own scanned bill (rule 0)
                continue
            q, units = _s628_packs(hit, ps)                   # S598: the matched bill LINE's packs; S628: by tablets when the packings differ
            if q <= 0 and not units:
                continue
            bno, bdate = hit["bill"], hit["date"]
            con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_bill_no=?, billed_date=?, detected_at=?, billed_units=? WHERE id=?",
                        (q, str(bno or ""), bdate, now_iso(), units, lid))
            if supplied is None and not missing:
                con.execute("UPDATE purchase_order_line SET supplied=?, short=?, arrived_by='marg', arrived_at=? WHERE id=?",
                            (q, 1 if q < packs else 0, now_iso(), lid))
                _audit(con, "marg", "line_detected", lid, dict(item=item, ordered=packs, billed=q, bill=str(bno or ""), units=units))
            n += 1
        for r in again:                                       # S628 (2): F-990 -- a billed line read again by rule (a); raised, never lowered
            lid, item, packs, supplied, missing, vendor, created, ps, bq, bno, bdate, aby = (r[0], r[1], int(r[2] or 0), r[3], r[4], r[5], str(r[6] or ""),
                                                                                         r[7], int(r[8] or 0), r[9], r[10], r[11])
            ctx = SF._ctx(con, sw, None)
            hit = SF.carried(con, sw, dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=bno, billed_date=bdate), ctx)
            if not hit or hit.get("how") != "a" or hit.get("qty") is None or str(hit.get("supkey") or "") != SW.supkey(vendor):
                continue                                      # rule (a) reads a bill number across dealers: only the order's own dealer's bill raises
            q, units = _s628_packs(hit, ps)
            if q <= bq:
                continue                                      # never lowered (LINVIZ: 6 strips of 6 read by tablets stays 3)
            con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_units=COALESCE(?, billed_units) WHERE id=?", (q, units, lid))
            if str(aby or "") == "marg":                      # Marg wrote supplied / short itself: both follow (a tap's answer is the person's)
                con.execute("UPDATE purchase_order_line SET supplied=?, short=? WHERE id=?", (q, 1 if q < packs else 0, lid))
            _audit(con, "marg", "line_redetected", lid, dict(item=item, ordered=packs, was=bq, billed=q, bill=str(bno or ""), kit="S628"))
            n += 1
        if n:
            con.commit()
        since = str(_setting(con, "order.track_since", "2026-10-12") or "2026-10-12")[:10]     # the order list's own window (S619)
        rows2 = con.execute("SELECT l.id, l.item, l.packs, o.vendor, o.created_at, l.pack_size FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                            "WHERE o.status IN ('sent','received') AND l.billed_qty IS NULL AND COALESCE(l.other_bill_no,'')='' "
                            "AND substr(o.created_at,1,10)>=?", (since,)).fetchall()
        m = 0
        for r in rows2:                                       # S628 (3): F-991 -- another dealer's bill, after every own-dealer line is marked
            lid, item, packs, vendor, created, ps = r[0], r[1], int(r[2] or 0), r[3], str(r[4] or ""), r[5]
            ctx = SF._ctx(con, sw, None)
            hit = SF.carried(con, sw, dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=None), ctx)
            if not hit or hit.get("how") != "e":
                continue
            try:
                late = (dt.date.fromisoformat(str(hit["date"])[:10]) - dt.date.fromisoformat(created[:10])).days > win
            except ValueError:
                late = True
            if late:
                continue
            q, units = _s628_packs(hit, ps)
            if q <= 0:
                continue
            con.execute("UPDATE purchase_order_line SET other_supplier=?, other_bill_no=?, other_date=?, other_qty=? WHERE id=? AND COALESCE(other_bill_no,'')=''",
                        (str(hit.get("supplier") or hit.get("supkey") or ""), str(hit["bill"] or ""), str(hit["date"])[:10], q, lid))
            _audit(con, "marg", "line_other_dealer", lid, dict(item=item, ordered=packs, came=q, dealer=str(hit.get("supplier") or ""), bill=str(hit["bill"] or ""), kit="S628"))
            m += 1
        if m:
            con.commit()
        n += m
    finally:
        try:
            sw.con.close()
        except Exception:                                     # noqa: BLE001
            pass
    if n:
        con.commit()
        _close_complete_orders(con, "marg")
    return n


def _close_complete_orders(con, who):
    """A SENT order whose every line is answered (supplied or missing) becomes RECEIVED, by S225's own door."""
    pa = _pa()
    for o in con.execute("SELECT id, vendor FROM purchase_order WHERE status='sent'").fetchall():
        lines = con.execute("SELECT id, packs, supplied, missing FROM purchase_order_line WHERE order_id=?", (o[0],)).fetchall()
        if not lines or any(l[2] is None and not l[3] for l in lines):
            continue
        given = [dict(id=l[0], supplied=(0 if l[3] else int(l[2])), short=bool(l[3] or int(l[2] or 0) < int(l[1] or 0))) for l in lines]
        try:
            pa._arrive(con, {"user": who}, {"action": "arrive_diff", "id": o[0], "lines": given})
        except Exception:                                     # noqa: BLE001
            con.execute("UPDATE purchase_order SET status='received', received_at=?, received_by=? WHERE id=?", (now_iso(), who, o[0]))
            con.commit()


# ------------------------------------------------------------------ the bill scans
def _scan_from(con):
    """S409 (D625): the owner's ruling -- pharmacy bill scanning starts from setting porders.scan_from (01-Sep-2026)."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='porders.scan_from'").fetchone()
        v = str(r[0]).strip() if r and r[0] else ""
        return v if re.match(r"^\d{4}-\d{2}-\d{2}$", v) else "2026-09-01"
    except sqlite3.Error:
        return "2026-09-01"


def unscanned_bills(con):
    """Marg purchase bills since porders.scan_from (S409; was 17-Aug) with no scan link, oldest first; red after SCAN_RED_DAYS."""
    pa = _pa()
    try:
        pa._rematch_if_changed(con, "porders")
    except Exception:                                         # noqa: BLE001
        pass
    linked = set()
    try:
        linked = {r[0] for r in con.execute("SELECT bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        pass
    today = dt.date.today()
    out = []
    try:
        rows = con.execute("SELECT b.id, b.supplier, b.supplier_norm, b.bill_no, b.bill_date, b.amount_p, b.month FROM purchase_bill b WHERE b.bill_date>=? AND "
                           + pa.EFF_BILL + " ORDER BY b.bill_date, b.supplier", (_scan_from(con),)).fetchall()
    except sqlite3.Error:
        return out
    for r in rows:
        if r[0] in linked:
            continue
        try:
            age = (today - dt.date.fromisoformat(str(r[4])[:10])).days
        except ValueError:
            age = 0
        out.append(dict(bill_id=r[0], vendor=r[1] or r[2], vendor_norm=r[2], bill_no=str(r[3] or ""), bill_date=str(r[4] or ""),
                        date_text=_dmy(r[4]), amount_p=int(r[5] or 0), amount=pa._r(r[5]), month=r[6], age=age, red=(age > SCAN_RED_DAYS),
                        intake=_intake_url(r[1] or r[2], r[3], r[4], r[5])))
    return out


def _intake_url(vendor, bill_no=None, bill_date=None, amount_p=None):
    from urllib.parse import urlencode
    q = dict(lane="pharmacy", vendor=str(vendor or "")[:120])
    if bill_no:
        q["bill_no"] = str(bill_no)[:40]
    if bill_date:
        q["bill_date"] = str(bill_date)[:10]
    if amount_p:
        q["amount"] = "%.2f" % (int(amount_p) / 100.0)
    q["from"] = "/finance/porders"                           # S440: the intake's BACK and its Save card return here
    return "/scanapp/intake?" + urlencode(q)


def received_unbilled(con, bills):
    """Received orders whose vendor has no Marg bill on or after the receipt yet (the bill is still to be keyed AND scanned)."""
    out = []
    today = dt.date.today()
    byv = {}
    for b in bills:
        byv.setdefault(b["vendor_norm"], []).append(b["bill_date"])
    pa = _pa()
    tied = _s454_tied(con)                                    # S454 (D668): an order whose bill's scan is tied to it asks for no scan
    for o in con.execute("SELECT id, vendor, received_at, total_p FROM purchase_order WHERE status='received' ORDER BY id DESC LIMIT 40"):
        if o[0] in tied:
            continue
        vn = pa.supplier_key(o[1])
        rec = str(o[2] or "")[:10]
        if any(d >= rec for d in byv.get(vn, [])):
            continue
        has_bill = con.execute("SELECT 1 FROM purchase_bill b WHERE b.supplier_norm=? AND b.bill_date>=? AND " + pa.EFF_BILL + " LIMIT 1", (vn, rec)).fetchone()
        if has_bill:
            continue
        try:
            age = (today - dt.date.fromisoformat(rec)).days
        except ValueError:
            age = 0
        out.append(dict(order_id=o[0], vendor=o[1], received=rec, received_text=_dmy(rec), age=age, red=(age > SCAN_RED_DAYS), intake=_intake_url(o[1])))
    return out


# ------------------------------------------------------------------ the state
def _plan_meds(con, ortho_names):
    pa = _pa()
    try:
        as_on, vendors = pa._staff_plan(con)
    except Exception as e:                                    # noqa: BLE001
        return dict(as_on="", vendors=[], error=str(e)[:120])
    out = []
    for v in vendors:
        lines = [dict(item=l["item"], on_hand=l["on_hand"], stock_text=l.get("stock_text"), qty=l["qty"], unit=l["unit"], pack_size=l["pack_size"], packing=l["packing"], rate_p=l["rate_p"],
                      per_day=l["per_day"], cover_after=l["cover_after"]) for l in v["lines"] if l["item"] not in ortho_names]
        if lines:
            out.append(dict(vendor=v["vendor"], has_phone=bool(v["has_phone"]), no_vendor=bool(v["no_vendor"]), lines=lines))
    return dict(as_on=as_on, vendors=out)


def _pcs(n):
    """S417 (F-636): an orthotic's stock in pieces -- the unit it is ordered in."""
    try:
        return _pa().stock_text(n, 1, "", ortho=True)
    except Exception:                                         # noqa: BLE001
        return "%s pcs" % n


def _stock_texts_s417(con, d):
    """S417: each proposed line carries its stock in the order's own unit (strips + loose / bottles / units) for the screen."""
    try:
        pa = _pa()
        orth = pa._ortho_set(con)
        for p in (d or {}).get("proposals") or []:
            for l in p.get("lines") or []:
                if isinstance(l, dict) and "on_hand" in l:
                    l["stock_text"] = pa.stock_text(l.get("on_hand"), l.get("pack_size"), l.get("packing"), pa.norm(l.get("item") or "") in orth)
    except Exception:                                         # noqa: BLE001 -- the screen never waits for a word
        pass
    return d


def _day_s410(con):
    """S410 (D626): the day's proposals (fixed + interim), the freeze, the contextual text -- read from order_rules, fail-soft."""
    try:
        import order_rules                                    # noqa: PLC0415
        return _stock_texts_s417(con, order_rules.day_state(con))     # S417
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, n=0, sent=0, unsent=0, text="", proposals=[], frozen=None, error=str(e)[:80])


def _frozen_s410(con):
    try:
        import order_rules                                    # noqa: PLC0415
        return order_rules._frozen(con)
    except Exception:                                         # noqa: BLE001
        return None


def _order_source_s593(con):
    """order.source as order_sheet reads it (marg_sheet | system | darpan); marg_sheet when it cannot be read."""
    try:
        import order_sheet                                    # noqa: PLC0415
        return order_sheet.source(con)
    except Exception:                                         # noqa: BLE001
        return "marg_sheet"


def state(con, u=None, kind="viewer"):
    ensure_schema(con)
    detect_supplies(con)
    sh = shelf(con)
    items = sh["items"]
    shortages = [it for it in items if it["short"] > 0]
    shortages.sort(key=lambda it: (-it["short"], it["item"]))
    orders = [o for o in _orders(con)]
    sent_open = [o for o in orders if o["status"] == "sent"]
    recent = next((o for o in orders if o["vendor"] == sh["vendor"] and _within(o["created_at"])), None)
    bills = unscanned_bills(con)
    rec = received_unbilled(con, bills)
    rules = _rules_ok(con)
    meds = _plan_meds(con, {it["item"] for it in items})
    lines_out = [dict(item=it["item"], short=it["short"], shelf=it["shelf"], shelf_text=_pcs(it["shelf"]), marg=it["marg"], keep=it["keep"], keep_source=it["keep_source"],
                      on_order=it["on_order"], approx=it["approx"], family=it["family"], family_shelf=it["family_shelf"], sizes=it["sizes"],
                      sizes_shelf={s: next((x["shelf"] for x in items if x["item"] == s), None) for s in it["sizes"]},
                      rename=it["rename"], packing=it["packing"], topup=it.get("family_topup", 0)) for it in shortages]
    allrows = [dict(item=it["item"], counted=it["counted"], pur=int(round(it["pur"] + it["pool_pur"])), sold=int(round(it["sold_all"])),
                    ret=int(round(it["ret"] + it["pool_ret"])), shelf=it["shelf"], shelf_text=_pcs(it["shelf"]), marg=it["marg"], keep=it["keep"], keep_source=it["keep_source"],
                    seed_keep=it["seed_keep"], sold90=it["sold90"], sold180=it["sold180"], on_order=it["on_order"], short=it["short"],
                    approx=it["approx"], family=it["family"], family_n=it["family_n"], rename=it["rename"]) for it in items]
    return dict(ok=True, kit=KIT, me=kind, user=(u or {}).get("user") or "", vendor=sh["vendor"], as_on=sh["as_on"], since=sh["since"],
                since_text=_dmy(sh["since"]), source=sh["source"], count_id=sh["count_id"],
                ortho=dict(n=len(shortages), lines=lines_out, recent=(dict(order_id=recent["id"], sent_text=recent["sent_text"], by=recent["sent_by"] or recent["created_by"],
                                                                           lines=len(recent["lines"])) if recent else None)),
                orders=dict(n=len(sent_open), open=sent_open, received=[o for o in orders if o["status"] == "received"][:20]),
                scans=dict(n=len(bills) + len(rec), bills=bills, received=rec, red=sum(1 for b in bills if b["red"]) + sum(1 for r in rec if r["red"])),
                kaam=_s440_kaam(con),                                  # S440 (D640): Scan ka kaam -- the five groups
                meds=dict(rules_ok=bool(rules), rules=rules, plan=meds),
                today=_day_s410(con),                                   # S410 (D626)
                all=allrows, keep_total=sum(int(it["keep"]) for it in items))


# ------------------------------------------------------------------ read helpers for the other pages (fail-soft)
def shortage_summary(con):
    try:
        ensure_schema(con)
        sh = shelf(con)
        s = [it for it in sh["items"] if it["short"] > 0]
        s.sort(key=lambda it: (-it["short"], it["item"]))
        recent = None
        for o in con.execute("SELECT id, created_at, sent_by, created_by FROM purchase_order WHERE vendor=? AND status='sent' ORDER BY id DESC LIMIT 1", (sh["vendor"],)):
            recent = dict(order_id=o[0], sent_text=_stamp(o[1]), by=o[2] or o[3])
        return dict(ok=True, n=len(s), vendor=sh["vendor"], source=sh["source"],
                    items=[dict(item=it["item"], short=it["short"], shelf=it["shelf"], keep=it["keep"], approx=it["approx"]) for it in s],
                    sent=recent, url="/finance/porders")
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, n=0, items=[], error=str(e)[:120])


def needs_you_lines(con):
    out = []
    try:
        ensure_schema(con)
        s = shortage_summary(con)
        if s.get("ok") and s["n"]:
            sent = con.execute("SELECT 1 FROM purchase_order WHERE vendor=? AND status='sent' LIMIT 1", (s["vendor"],)).fetchone()
            out.append(dict(cls="warn", target="porders", text="Orthotic shortages: %d item%s -- order not sent" % (s["n"], "" if s["n"] == 1 else "s")
                            if not sent else "Orthotic shortages: %d item%s -- an order is out, more still short" % (s["n"], "" if s["n"] == 1 else "s")))
        out.extend(_s454_scan_lines(con))                        # S454 P2 (7.3): the bill-scan line only after purchase.scan_wait_days; paper not found;
                                                                  # a read scan not in Marg after purchase.entry_wait_days (counted months)
        if not _rules_ok(con):
            out.append(dict(cls="info", target="porders", text="Buying rules for medicines await your approval"))
        out.extend(_s440_owner_lines(con))                        # S440 (D640): a paper amount reception could not settle
        out.extend(_s454_owner_lines(con))                        # S454 (7.3): the owner's lines about ordering
    except Exception:                                         # noqa: BLE001
        pass
    return out


# ------------------------------------------------------------------ auth
def _auth():
    u, err = _require("maker", "checker", "viewer", unit=ACCESS_UNIT)
    if err:
        return None, None, None, err
    con = _db()
    ensure_schema(con)
    roles = set(u.get("roles") or [])
    login = str(u.get("user") or "").lower()
    if "checker" in roles:
        kind = "owner"
    elif "maker" in roles and login in _names(con, "porders.senders"):
        kind = "sender"
    else:
        kind = "viewer"
    if S441 is not None and S441.is_shared_login(login):          # S441 (D643): every order sent / arrival marked carries the person
        name = S441.who_name(request.cookies)
        if name:
            u = dict(u, user="%s (Reception)" % name, login=login)
        elif request.method == "POST":
            return None, None, None, (jsonify(ok=False, error="who_needed", message="Pehle apna naam chuniye (Kaun kaam kar raha hai?)."), 428)
    return u, con, kind, None


def _forbid_view(kind):
    return jsonify(ok=False, error="view_only", message="Aap sirf dekh sakte hain."), 403


@bp.route("/finance/porders")
def page():
    u, con, kind, err = _auth()
    if err:
        return err
    login = str(u.get("login") or u.get("user") or "").lower()
    if kind == "owner" and not request.args:                  # S925 (the owner, 22-Nov 08:59): his Purchase orders tile opens his
        from flask import redirect                            # noqa: PLC0415 -- grouped flow page; ?home=1 is the one-task screen
        return redirect("/finance/porders/flow", code=302)
    if _s454_simple(con) and request.args.get("old") != "1" and kind in ("owner", "sender"):    # S454: the one-task screens; ?old=1 = this page
        import porders_s454                                   # noqa: PLC0415
        return porders_s454.home()
    with open(PAGE, encoding="utf-8") as fh:
        html = fh.read()
    html = _s454_old_page(con, kind, html)                    # S454: the owner's ordering cards and the settings card, above the old page
    html = html.replace('<span id="ttl">Purchase orders</span></div>',                     # S444 (D647): who is signed in, one quiet
                        '<span id="ttl">Purchase orders</span><span id="s444who" style="margin-left:10px;font-size:12px;'   # line,
                        'opacity:.85;white-space:nowrap">Signed in: %s</span></div>'                   # in the S440 BACK bar only
                        % login.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), 1)
    if S441 is not None and S441.is_shared_login(login):          # S441: "Kaun kaam kar raha hai?" -- once per sitting
        return html.replace("</body>", S441.who_script(login) + "</body>", 1), 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}
    return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


@bp.route("/finance/porders/api/healthz")
def api_healthz():
    u, con, kind, err = _auth()
    if err:
        return err
    return jsonify(ok=True, module="porders", version=VERSION, kit=KIT)


@bp.route("/finance/porders/api/state")
def api_state():
    u, con, kind, err = _auth()
    if err:
        return err
    return jsonify(**state(con, u, kind))


@bp.route("/finance/porders/api/summary")
def api_summary():
    u, con, kind, err = _auth()
    if err:
        return err
    sm = shortage_summary(con)
    try:                                                      # S440: the counts of Scan ka kaam beside the shortage count (fail-soft)
        k = scan_work(con)
        sm["scan_kaam"] = dict(n=k["n"], **k["counts"])
    except Exception:                                         # noqa: BLE001
        pass
    return jsonify(**sm)


@bp.route("/finance/porders/api/send", methods=["POST"])
def api_send():
    """S613 (F-959, the second door): RETIRED. Yuvika's order goes only from reception's order page (order_sheet), after Darpan's yes
    (S605, D749). Any login: 409 ortho_via_order_page, nothing written. (The purchase page's staff send -- purchase_app /api/order
    action 'staff_send' -- is a third door, named for a later build.)"""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind not in ("owner", "sender"):
        return _forbid_view(kind)
    msg = ("Yuvika's order now goes from reception's order page, after Darpan's yes." if kind == "owner"
           else "Yuvika ka order ab 'Order karna hai' se jaata hai, Darpan ki haan ke baad.")
    return jsonify(ok=False, error="ortho_via_order_page", message=msg), 409


@bp.route("/finance/porders/api/send_med", methods=["POST"])
def api_send_med():
    """A medicine order from the S225 plan -- only once the owner has approved the buying rules."""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind not in ("owner", "sender"):
        return _forbid_view(kind)
    if not _rules_ok(con):
        return jsonify(ok=False, error="rules_pending", message="Doctor sahab ke rules ka intezaar."), 403
    fr = _frozen_s410(con)                                    # S410 (D626): the owner's freeze
    if fr:
        return jsonify(ok=False, error="frozen", message="Medicine ordering band hai: %s" % (fr.get("reason") or "")), 423
    if _order_source_s593(con) == "darpan":                   # S593 (F-738, R1-C8): this door bypasses Darpan's pakka -- refused outright on darpan
        return jsonify(ok=False, error="not_confirmed", message="Darpan ki pakki list se hi order jaata hai"), 409
    pa = _pa()
    b = request.get_json(silent=True) or {}
    vendor = str(b.get("vendor") or "").strip()
    items, _as_on, _cid = ortho_items(con)
    plan = _plan_meds(con, {it["item"] for it in items})
    v = next((x for x in plan["vendors"] if x["vendor"] == vendor), None)
    if not v:
        return jsonify(ok=False, error="no_such_vendor", message="Is stockist ka order plan mein nahi hai."), 400
    recent = con.execute("SELECT id, created_at FROM purchase_order WHERE vendor=? AND status IN ('sent','received') ORDER BY id DESC LIMIT 1", (vendor,)).fetchone()
    if recent and _within(recent[1]):
        return jsonify(ok=False, error="already", already=True, order_id=recent[0], message="Yeh order abhi bheja ja chuka hai (%s)." % _stamp(recent[1])), 409
    resp = pa._staff_send(con, u, dict(vendor=vendor, lines=v["lines"]))
    r, code = (resp if isinstance(resp, tuple) else (resp, 200))
    j = r.get_json() or {}
    if code != 200 or not j.get("ok"):
        return jsonify(ok=False, error=j.get("error") or "send_failed", message=j.get("message") or "Order nahi bana."), code if code != 200 else 500
    con.execute("UPDATE purchase_order SET section='Medicines' WHERE id=?", (j["order_id"],))
    con.commit()
    return jsonify(ok=True, order_id=j["order_id"], wa_url=j["wa_url"], sent_text=_stamp(now_iso()))


@bp.route("/finance/porders/api/arrive", methods=["POST"])
def api_arrive():
    """Order aaya? -- per line 'Aa gaya' (all supplied) · 'Kam aaya' (the supplied quantity) · 'Nahi mila'; or 'Sab aa gaya'
    for the whole order. A short or missing line carries into the next order by itself (it is no longer on order)."""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind not in ("owner", "sender"):
        return _forbid_view(kind)
    b = request.get_json(silent=True) or {}
    try:
        oid = int(b.get("order_id") or 0)
    except (TypeError, ValueError):
        oid = 0
    o = con.execute("SELECT id, status, vendor FROM purchase_order WHERE id=?", (oid,)).fetchone()
    if not o:
        return jsonify(ok=False, error="no_such_order"), 404
    who = u.get("user") or ""
    if b.get("line_id") is not None:
        try:
            lid0 = int(b.get("line_id") or 0)
        except (TypeError, ValueError):
            lid0 = 0
        l0 = con.execute("SELECT supplied, missing FROM purchase_order_line WHERE id=? AND order_id=?", (lid0, oid)).fetchone()
        if l0 and (l0[0] is not None or l0[1]):
            return jsonify(ok=True, already=True, message="Is line ka jawab pehle hi darj hai.", line_id=lid0, order_status=o[1])
    if o[1] != "sent":
        return jsonify(ok=False, error="not_sent", message="Yeh order pehle hi aa chuka hai."), 409
    if b.get("all"):
        resp = _pa()._arrive(con, u, {"action": "arrive", "id": oid})
        r, code = (resp if isinstance(resp, tuple) else (resp, 200))
        j = r.get_json() or {}
        if j.get("ok"):
            con.execute("UPDATE purchase_order_line SET arrived_by=?, arrived_at=? WHERE order_id=? AND arrived_at IS NULL", (who, now_iso(), oid))
            con.commit()
        return jsonify(**j) if code == 200 else (jsonify(**j), code)
    try:
        lid = int(b.get("line_id") or 0)
    except (TypeError, ValueError):
        lid = 0
    l = con.execute("SELECT id, item, packs, supplied, missing FROM purchase_order_line WHERE id=? AND order_id=?", (lid, oid)).fetchone()
    if not l:
        return jsonify(ok=False, error="no_such_line"), 404
    how = str(b.get("how") or "").strip().lower()
    packs = int(l[2] or 0)
    if how == "ok":
        supplied, missing = packs, 0
    elif how == "short":
        try:
            supplied = int(b.get("supplied"))
        except (TypeError, ValueError):
            return jsonify(ok=False, error="bad_qty", message="Kitna aaya?"), 400
        if supplied < 0 or supplied >= packs:
            return jsonify(ok=False, error="bad_qty", message="Kam aaya = %d se kam." % packs), 400
        missing = 0
    elif how == "missing":
        supplied, missing = 0, 1
    else:
        return jsonify(ok=False, error="bad_how", message="Aa gaya / Kam aaya / Nahi mila"), 400
    if l[3] is not None or l[4]:
        return jsonify(ok=True, already=True, message="Is line ka jawab pehle hi darj hai.", line_id=lid)
    con.execute("UPDATE purchase_order_line SET supplied=?, short=?, missing=?, arrived_by=?, arrived_at=? WHERE id=?",
                (supplied, 1 if (missing or supplied < packs) else 0, missing, who, now_iso(), lid))
    _audit(con, who, "porders_line_" + how, lid, dict(order=oid, item=l[1], ordered=packs, supplied=supplied, missing=missing))
    con.commit()
    _close_complete_orders(con, who)
    st = con.execute("SELECT status FROM purchase_order WHERE id=?", (oid,)).fetchone()[0]
    return jsonify(ok=True, line_id=lid, order_id=oid, how=how, supplied=supplied, missing=missing, order_status=st,
                   saved=dict(item=l[1], hi={"ok": "Aa gaya", "short": "Kam aaya -- %d" % supplied, "missing": "Nahi mila"}[how]))


@bp.route("/finance/porders/api/keep", methods=["POST"])
def api_keep():
    """The owner's keep-in-stock +/- on one orthotic (audited); the seed never overwrites it again."""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    item = str(b.get("item") or "").strip()
    try:
        delta = int(b.get("delta") or 0)
        setv = int(b["keep"]) if b.get("keep") is not None else None
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    if not con.execute("SELECT 1 FROM stock_item_section WHERE item=? AND section=?", (item, SECTION)).fetchone():
        return jsonify(ok=False, error="not_orthotic", message="%s is not an orthotic on the map." % item), 400
    r = con.execute("SELECT keep, source FROM porder_keep WHERE item=?", (item,)).fetchone()
    old = int(r[0]) if r else 0
    new = setv if setv is not None else old + delta
    new = max(0, min(99, new))
    who = u.get("user") or ""
    con.execute("INSERT INTO porder_keep (item, keep, source, set_by, set_at) VALUES (?,?,'owner',?,?) ON CONFLICT(item) DO UPDATE SET "
                "keep=excluded.keep, source='owner', set_by=excluded.set_by, set_at=excluded.set_at", (item, new, who, now_iso()))
    _audit(con, who, "porders_keep", item, dict(before=old, after=new))
    con.commit()
    return jsonify(ok=True, item=item, keep=new, before=old)


@bp.route("/finance/porders/api/rules")
def api_rules():
    """The medicine buying rules as they stand: S225's settings and the S341 lists, for the owner's one sitting."""
    u, con, kind, err = _auth()
    if err:
        return err
    pa = _pa()
    rules = {}
    try:
        rules = json.load(open(os.path.join(SPINE_DIR, "order_rules.json")))
    except Exception as e:                                    # noqa: BLE001
        rules = dict(error=str(e)[:100])
    s225 = dict(pace_days=pa.PACE_DAYS, lead_days=pa.LEAD_DAYS, safety_days=pa.SAFETY_DAYS, max_cover_days=pa.MAX_COVER_DAYS,
                cadence_days=pa.CADENCE_DAYS, tier_weekly_rs=pa.TIER_WEEKLY_P // 100, tier_fortnight_rs=pa.TIER_FORTNIGHT_P // 100,
                min_line_rs=pa.MIN_LINE_P // 100, staff_round=pa.STAFF_ROUND, rounding="strips up to 10, then tens; other units as the engine's box")
    return jsonify(ok=True, approved=_rules_ok(con), s225=s225, lists=rules)


@bp.route("/finance/porders/api/rules/approve", methods=["POST"])
def api_rules_approve():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    cur = _rules_ok(con)
    if cur:
        return jsonify(ok=True, already=True, approved=cur)
    rec = dict(by=u.get("user") or "", at=now_iso())
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                ("porders.rules_approved", json.dumps(rec), "S403: the owner approved the medicine buying rules (S225 settings + S341 lists)"))
    _audit(con, rec["by"], "porders_rules_approved", "", rec)
    con.commit()
    return jsonify(ok=True, already=False, approved=rec)


# =====================================================================================================================
# S440_SCAN_FLOW (30-Sep-2026, session 283, D640, F-662) -- "SCAN KA KAAM": ONE LIST, A TAP PER LINE
#
# The owner, 30-Sep: "Whatever needs to be done should be clearly mentioned in the staff scan app -- as with 'Bill scan
# karo' and then 'Scan' and there they tap 'scanned'. The scans with no readable supplier should be flagged the same way."
# S439 taught the matcher to say WHY a scan has no link, but only the owner's page said it; reception's list still asked
# for six bills whose scan was already there. Here every line a person must decide carries its own buttons:
#   1 scan     Scan karo        a Marg bill with no scan and no near-match: the S403 pre-filled intake. Marg's double
#                               entry (the same number twice) shows ONCE and its extra row goes on the WRONG list (S371).
#   2 confirm  Yahi bill hai?   the matcher's likely bill for a scan (number or amount read differently): Haan links it
#                               (grade CONFIRMED, "reception confirmed", audited) -- or, when that bill already has a
#                               scan, marks this paper a second scan; Nahi clears the hint for good.
#   3 vendor   Supplier chuno   a scan whose vendor OCR could not read: the choice is kept for that scan and, when the
#                               OCR text is a real spelling (never the buyer's own name), learned in purchase_scan_alias.
#   4 amount   Amount milao     a linked scan and Marg disagree on the amount by more than 2%: the staff types the
#                               amount ON THE PAPER. = the scan -> Marg galat (the S371 WRONG mark on the bill);
#                               = Marg -> Scan galat padha (the link becomes EXACT, the paper amount is kept in
#                               purchase_scan_state, never in assets.db); neither -> a Needs-you line for the owner.
#   5 wait     Marg ka intezaar a scan of a bill Marg has not sent yet: no button.
# What a person decided lives in purchase_scan_state (additive columns) and rides every pass of the matcher
# (purchase_app._rematch). assets.db stays READ ONLY here; "Galat lane" is the asset app's own re-lane route.
# The read door /finance/porders/api/scan-status gives the asset app's list its status words -- on THIS unit, because
# the reception logins hold a role here and none on /finance/purchase (the brief named that path).
# =====================================================================================================================
S440_FROM = "/finance/porders"
S440_DOUBLE = "Marg mein do baar"
S440_WORDS = {"linked": "Marg se mil gaya", "wait": "Marg ka intezaar (Amir)", "you": "Aapka jawab chahiye → Scan ka kaam",
              "dup": "Doosri baar scan"}
S440_TOL_P = 100                  # a rupee: two amounts are "the same" within this
S440_ASK = ("number_differs", "amount_differs", "no_digits")     # the reasons that can name a likely bill: "Yahi bill hai?"


def _s440_rs(p):
    """Paise -> '₹1,424' or '₹842.70' (the paise shown only when there are any)."""
    if p is None:
        return "—"
    p = int(p)
    whole = _pa()._r(p - (p % 100) if p >= 0 else p)
    return whole if p % 100 == 0 else "%s.%02d" % (whole, abs(p) % 100)


def _s440_scans(con):
    """The pharmacy scans as the asset app holds them (READ ONLY): {id: dict}; None when its database is not reachable."""
    pa = _pa()
    acon = pa._assets_con()
    if acon is None:
        return None
    try:
        rows = acon.execute("SELECT id, vendor, bill_no, bill_date, total_amount, stamp_no, created_at FROM bills "
                            "WHERE kind='Pharmacy' AND COALESCE(status,'')<>'rejected' ORDER BY id DESC LIMIT 2000").fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        acon.close()
    out = {}
    today = dt.date.today()
    for r in rows:
        amt = pa._float_or_none(r["total_amount"])
        try:
            age = (today - dt.date.fromisoformat(str(r["created_at"] or "")[:10])).days
        except ValueError:
            age = 0
        out[r["id"]] = dict(id=r["id"], vendor=r["vendor"] or "", bill_no=str(r["bill_no"] or ""), bill_date=str(r["bill_date"] or ""),
                            amount_p=(int(round(amt * 100)) if amt is not None else None), stamp=r["stamp_no"] or ("#%d" % r["id"]),
                            age=max(0, age))
    return out


def _s440_state(con):
    try:
        return {r["asset_bill_id"]: dict(r) for r in con.execute("SELECT * FROM purchase_scan_state")}
    except sqlite3.Error:
        return {}


def _s440_bills(con):
    pa = _pa()
    try:
        return {b["id"]: dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL)}
    except sqlite3.Error:
        return {}


def _s440_month_final(con, month):
    try:
        r = con.execute("SELECT status FROM purchase_month WHERE month=?", (month or "",)).fetchone()
        return bool(r and r[0] == "final")
    except sqlite3.Error:
        return False


def _s440_doubles(con, bills, linked):
    """Marg's double entries since porders.scan_from: the same supplier, date and amount under one number typed in two
    cases. -> ({extra bill id: the row shown}, {shown id: [numbers]}, {ids of a group one of whose rows has a scan}).
    The extra row is marked WRONG (should be Rs 0) once -- the S371 list -- and the mark is lifted when its twin is gone."""
    since = _scan_from(con)
    groups = {}
    for b in bills.values():
        if str(b.get("bill_date") or "") >= since:
            groups.setdefault((b["supplier_norm"], str(b["bill_no"] or "").strip().lower(), b["bill_date"], b["amount_p"]), []).append(b)
    extra, shown, scanned, twins = {}, {}, set(), set()
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda b: (0 if b["id"] in linked else 1, b["id"]))      # the row a scan is linked to is the one kept
        first = members[0]
        shown[first["id"]] = [str(m["bill_no"]) for m in members]
        has_scan = any(m["id"] in linked for m in members)
        for m in members:
            twins.add(m["id"])
            if has_scan:
                scanned.add(m["id"])
        for m in members[1:]:
            extra[m["id"]] = first["id"]
            if not m.get("verdict") and not _s440_month_final(con, m.get("month")):
                why = "%s: bill %s aur %s (%s, %s) -- ek entry hatao" % (S440_DOUBLE, first["bill_no"], m["bill_no"], _pa().supplier_key(m["supplier"]), _dmy(m["bill_date"]))
                con.execute("UPDATE purchase_bill SET verdict='WRONG', verdict_by=?, verdict_at=?, wrong_amount_p=0, reason=? WHERE id=?",
                            ("S440 rule", now_iso(), why, m["id"]))
                _audit(con, "S440 rule", "double_entry", m["id"], dict(verdict="WRONG", wrong_amount_p=0, twin=first["id"], reason=why))
                con.commit()
    try:                                                          # the twin is gone from Marg: the mark has done its work
        for r in con.execute("SELECT id FROM purchase_bill WHERE verdict='WRONG' AND verdict_by='S440 rule' AND reason LIKE ?", (S440_DOUBLE + "%",)).fetchall():
            if r[0] in bills and r[0] not in twins:
                con.execute("UPDATE purchase_bill SET verdict=NULL, verdict_by=NULL, verdict_at=NULL, wrong_amount_p=NULL, reason=NULL WHERE id=?", (r[0],))
                _audit(con, "S440 rule", "double_resolved", r[0], dict(before="WRONG"))
                con.commit()
    except sqlite3.Error:
        pass
    return extra, shown, scanned


def _s440_differs(scan_p, marg_p, ym=None):
    """S726 (F-1140): beyond Rs 1 for a bill of a counted month; a parked month (September) keeps purchase.total_noise_rs -- no new
    question for it. ym: the bill's month (None: the old band)."""
    return bool(scan_p) and abs(int(scan_p) - int(marg_p)) > _s726_tol_p(ym)


_S726_SAID = []


def _s726_tol_p(ym):
    """Rs 1 for a bill of a counted month; the old noise band for a parked month, an unknown month (None) or any fault."""
    if ym is None:
        return _s454_noise_p()
    try:
        import scan_register                                   # noqa: PLC0415
        return S440_TOL_P if scan_register.month_class(_db(), str(ym or "")) == "counted" else _s454_noise_p()
    except Exception as e:                                    # noqa: BLE001 -- fail to the old band: nothing new is asked (S726 1)
        if not _S726_SAID:
            _S726_SAID.append(1)
            print("porders S726: the month of a bill could not be judged (%s) -- the old noise band is used" % str(e)[:160], file=sys.stderr)
        return _s454_noise_p()


def _s726_quiet(con):
    try:
        import scan_register                                   # noqa: PLC0415
        return scan_register.s726_quiet_bills(con)
    except Exception:                                         # noqa: BLE001
        return set()


def scan_work(con, run_pass=True):
    """The five groups of "Scan ka kaam" (the header above), as plain rows for the page. n = the lines a person must act
    on (groups 1-4); group 5 waits for Marg and carries no button."""
    pa = _pa()
    out = dict(ok=True, n=0, counts=dict(scan=0, confirm=0, vendor=0, amount=0, wait=0, dup=0, twin=0), scan=[], confirm=[], vendor=[], amount=[], wait=[],
               received=[], suppliers=[], reachable=True, twin=[], answered=[])
    unscanned = unscanned_bills(con)                              # first: it runs the matcher when the scans have changed (S225 rev 9)
    scans = _s440_scans(con)
    if scans is None:
        out["reachable"] = False
        scans = {}
    st = _s440_state(con)
    bills = _s440_bills(con)
    links, by_scan = {}, {}
    try:
        for r in con.execute("SELECT bill_id, asset_bill_id, grade, matched_on FROM purchase_scan_link"):
            links[r[0]] = (r[1], r[2], r[3])
            by_scan[r[1]] = (r[0], r[2], r[3])
    except sqlite3.Error:
        pass

    def pic(sid):
        return dict(thumb="/scanapp/bills/%d/thumb" % sid, pdf="/scanapp/bills/%d/file" % sid)

    def bill_row(b):
        return dict(bill_id=b["id"], vendor=pa.supplier_key(b["supplier"]), bill_no=str(b["bill_no"] or ""), date_text=_dmy(b["bill_date"]),
                    amount=_s440_rs(b["amount_p"]), amount_p=int(b["amount_p"] or 0))

    def scan_row(s):
        return dict(scan=s["id"], stamp=s["stamp"], scan_vendor=s["vendor"], scan_no=s["bill_no"], scan_date=_dmy(s["bill_date"]) if s["bill_date"] else "",
                    scan_amount=_s440_rs(s["amount_p"]), scan_amount_p=s["amount_p"], age=s["age"], **pic(s["id"]))

    pending_bills = set()                                         # a bill a near-match is waiting on is not asked for again
    for sid in sorted(scans):
        s, row = scans[sid], st.get(sid) or {}
        if sid in by_scan:                                        # 4 -- linked, the two amounts more than 2% apart, nobody has answered
            b = bills.get(by_scan[sid][0])
            sp = row.get("paper_amount") if row.get("paper_amount") is not None else s["amount_p"]
            if b is not None and not row.get("amount_state") and _s440_differs(sp, b["amount_p"], b.get("month") or str(b.get("bill_date") or "")[:7]):
                out["amount"].append(dict(scan_row(s), **bill_row(b)))
            continue
        why = row.get("why") or ""
        if why == "dup":
            out["counts"]["dup"] += 1
            continue
        lb = bills.get(row.get("likely_bill")) if why in S440_ASK else None
        if lb is not None:                                        # 2 -- the matcher's likely bill
            taken = links.get(lb["id"])
            if not taken:
                pending_bills.add(lb["id"])
            out["confirm"].append(dict(scan_row(s), why=why, taken_by=(taken[0] if taken else None),
                                       taken_stamp=((scans.get(taken[0]) or {}).get("stamp") if taken else None), **bill_row(lb)))
        elif why == "vendor_unknown" and not row.get("chosen_vendor"):
            out["vendor"].append(scan_row(s))                     # 3 -- nobody could read the supplier
        else:                                                     # 5 -- nothing for a person to do
            if _s454_unread(s, sid):                              # S454 (4.7, F-695): a paper with nothing read is a question, never "wait"
                continue
            note = ("Number / amount nahi padha gaya — dobara scan mat karo" if why == "no_digits"
                    else "Supplier list mein nahi — Marg ki entry ka intezaar" if row.get("chosen_vendor") == "-"
                    else "Amir ke entry ke baad khud jud jayega")
            out["wait"].append(dict(scan_row(s), note=note, note_en=("OCR read no number / amount" if why == "no_digits"
                                                                   else "waits for Marg's entry; it links by itself")))
    extra, shown, scanned_twin = _s440_doubles(con, bills, links)
    quiet726 = _s726_quiet(con)                                   # S726: a parked bill an undo freed asks nobody
    for x in unscanned:                                           # 1 -- a Marg bill nobody has scanned
        bid = x["bill_id"]
        if bid in pending_bills or bid in extra or bid in scanned_twin or bid in quiet726:
            continue
        out["scan"].append(dict(x, double=(bid in shown), double_nos=shown.get(bid) or []))
    try:                                                          # S403's received orders whose bill Marg has not got yet ride group 1
        out["received"] = received_unbilled(con, unscanned)
    except Exception:                                             # noqa: BLE001
        out["received"] = []
    for k in ("scan", "confirm", "vendor", "amount", "wait"):
        out["counts"][k] = len(out[k])
    out["counts"]["scan"] += len(out["received"])
    try:                                                          # S441 (D643): Dobara scan? / Galat lane? -- asked by the asset app, answered here
        out["twin"], out["answered"] = _s441_questions({x["scan"] for x in out["confirm"]})
    except Exception:                                             # noqa: BLE001
        out["twin"], out["answered"] = [], []
    out["counts"]["twin"] = len(out["twin"])
    out["n"] = out["counts"]["scan"] + out["counts"]["confirm"] + out["counts"]["vendor"] + out["counts"]["amount"] + out["counts"]["twin"]
    if out["vendor"]:
        out["suppliers"] = sorted({pa.supplier_key(b["supplier"]) for b in bills.values() if b.get("supplier")})
    return out


def _s441_questions(asking):
    """S441: the asset app's open questions (assets.db, READ ONLY) as lines for Scan ka kaam, and the answers of the last
    two days with who gave them. A pharmacy scan the S440 matcher is already asking about ("Yahi bill hai?") is not asked twice."""
    if S441 is None:
        return [], []
    acon = _pa()._assets_con()
    if acon is None:
        return [], []
    try:
        qs = S441.open_questions(acon)
        done = S441.answered_recent(acon)
    finally:
        acon.close()
    out = []
    for q in qs:
        b, c = q["bill"], q["cand"]
        if b["id"] in asking:
            continue
        row = dict(q=q["q"], kind=q["kind"], scan=b["id"], stamp=b["stamp"], scan_vendor=b["vendor"], scan_no=b["bill_no"],
                   scan_amount=_s440_rs(int(round(float(b["amount"]) * 100))) if b["amount"] not in (None, "") else "—",
                   by=b["by"], at=b["at"], lane=b["lane"], thumb="/scanapp/bills/%d/thumb" % b["id"], pdf="/scanapp/bills/%d/file" % b["id"])
        if c:
            row["cand"] = dict(scan=c["id"], stamp=c["stamp"], vendor=c["vendor"], bill_no=c["bill_no"], by=c["by"], at=c["at"],
                               amount=_s440_rs(int(round(float(c["amount"]) * 100))) if c["amount"] not in (None, "") else "—",
                               thumb="/scanapp/bills/%d/thumb" % c["id"], pdf="/scanapp/bills/%d/file" % c["id"])
        out.append(row)
    return out, done


def _s440_kaam(con):
    """state()'s 'kaam': the five groups; the rest of the screen never waits for them."""
    try:
        return scan_work(con)
    except Exception as e:                                        # noqa: BLE001
        return dict(ok=False, n=0, counts={}, scan=[], confirm=[], vendor=[], amount=[], wait=[], received=[], suppliers=[], error=str(e)[:120])


def _s440_put(con, sid, who, **cols):
    """One decision of a person on one scan: upsert its purchase_scan_state row (a linked scan has none until now)."""
    _pa()._ensure_s439(con)
    con.execute("INSERT OR IGNORE INTO purchase_scan_state (asset_bill_id, why, detail, checked_at) VALUES (?,?,?,?)", (sid, "linked", "linked", now_iso()))
    cols = dict(cols, confirmed_by=who, confirmed_at=now_iso())
    con.execute("UPDATE purchase_scan_state SET %s WHERE asset_bill_id=?" % ", ".join("%s=?" % k for k in sorted(cols)),
                [cols[k] for k in sorted(cols)] + [sid])


def _s440_write(u, kind):
    if kind not in ("owner", "sender"):
        return _forbid_view(kind)
    return None


def _s440_scan_arg(b):
    try:
        return int(b.get("scan") or 0)
    except (TypeError, ValueError):
        return 0


@bp.route("/finance/porders/api/scan/confirm", methods=["POST"])
def api_scan_confirm():
    """Yahi bill hai? -- Haan links the scan to the matcher's likely bill (or marks the paper a second scan when that
    bill already has one); Nahi clears the hint, and the bill goes back to Scan karo."""
    u, con, kind, err = _auth()
    if err:
        return err
    no = _s440_write(u, kind)
    if no:
        return no
    pa = _pa()
    b = request.get_json(silent=True) or {}
    sid = _s440_scan_arg(b)
    who = u.get("user") or ""
    pa._ensure_s439(con)
    row = _s440_state(con).get(sid)
    if not row or not row.get("likely_bill") or row.get("why") not in S440_ASK:
        return jsonify(ok=False, error="no_hint", message="Is scan ke liye ab koi sawaal nahi hai."), 409
    bid = int(row["likely_bill"])
    if int(b.get("bill") or 0) != bid:
        return jsonify(ok=False, error="stale", message="List badal gayi hai — dobara kholiye."), 409
    bill = con.execute("SELECT id, supplier, bill_no, month FROM purchase_bill WHERE id=?", (bid,)).fetchone()
    if not bill:
        return jsonify(ok=False, error="no_such_bill"), 404
    if not b.get("yes"):
        no_list = sorted({int(x) for x in str(row.get("hint_no") or "").split(",") if x.strip().isdigit()} | {bid})
        _s440_put(con, sid, who, hint_no=",".join(str(x) for x in no_list))
        _audit(con, who, "scan_hint_refused", bid, dict(scan=sid, kit="S440", note="reception: yeh bill nahi hai"))
        con.commit()
        pa._rematch(con, who)
        return jsonify(ok=True, scan=sid, linked=False, message="Theek hai — yeh bill nahi hai.")
    taken = con.execute("SELECT asset_bill_id FROM purchase_scan_link WHERE bill_id=?", (bid,)).fetchone()
    if taken and int(taken[0]) != sid:                            # the bill already has a scan: this paper is its second scan
        _s440_put(con, sid, who, dup_ok=int(taken[0]))
        _audit(con, who, "scan_dup_confirmed", bid, dict(scan=sid, dup_cand=int(taken[0]), kit="S440", note="reception confirmed"))
        con.commit()
        pa._rematch(con, who)
        return jsonify(ok=True, scan=sid, linked=False, second_scan=True, message="Theek hai — yeh kaagaz pehle scan ho chuka tha.")
    con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (bid, sid, "CONFIRMED", "reception confirmed", now_iso()))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, bid))
    _s440_put(con, sid, who)
    _audit(con, who, "scan_link", bid, dict(scan=sid, grade="CONFIRMED", rule="reception confirmed", supplier=pa.supplier_key(bill[1]), bill_no=bill[2], kit="S440"))
    con.commit()
    pa._rematch(con, who)
    return jsonify(ok=True, scan=sid, bill=bid, linked=True, message="Jud gaya — bill %s." % bill[2])


@bp.route("/finance/porders/api/scan/vendor", methods=["POST"])
def api_scan_vendor():
    """Supplier chuno -- the choice is kept for this scan; when the OCR text is a real spelling (not empty, not the
    buyer's own name) it is learned once in purchase_scan_alias. The matcher runs at once."""
    u, con, kind, err = _auth()
    if err:
        return err
    no = _s440_write(u, kind)
    if no:
        return no
    pa = _pa()
    b = request.get_json(silent=True) or {}
    sid = _s440_scan_arg(b)
    who = u.get("user") or ""
    pa._ensure_s439(con)
    scans = _s440_scans(con) or {}
    row = _s440_state(con).get(sid)
    if sid not in scans or not row or row.get("why") != "vendor_unknown":
        return jsonify(ok=False, error="no_such_line", message="Is scan ke liye supplier nahi poochha ja raha."), 409
    choice = str(b.get("vendor") or "").strip()
    suppliers = {pa.supplier_key(x["supplier"]) for x in _s440_bills(con).values() if x.get("supplier")}
    if choice != "-" and choice not in suppliers:
        return jsonify(ok=False, error="bad_vendor", message="List mein se supplier chuniye."), 400
    _s440_put(con, sid, who, chosen_vendor=choice)
    learned = False
    ocr = pa.supplier_key(scans[sid]["vendor"])
    toks = pa._vendor_tokens_s439(scans[sid]["vendor"])
    if choice != "-" and ocr and toks and not pa._is_buyer_s439(toks):
        cur = con.execute("INSERT OR IGNORE INTO purchase_scan_alias (ocr_norm, supplier_norm, scan_id, who, at) VALUES (?,?,?,?,?)",
                          (ocr, choice, sid, "S440 %s chose for scan %d" % (who, sid), now_iso()))
        learned = bool(cur.rowcount)
        if learned:
            _audit(con, who, "alias_learn", ocr, dict(supplier=choice, note="S440 %s chose for scan %d" % (who, sid)))
    _audit(con, who, "scan_vendor_chosen", sid, dict(scan=sid, vendor=choice, learned=learned, kit="S440"))
    con.commit()
    pa._rematch(con, who)
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    return jsonify(ok=True, scan=sid, vendor=choice, learned=learned, linked=bool(lk),
                   message=("Jud gaya." if lk else "Supplier likh liya — Marg ki entry ka intezaar."))


@bp.route("/finance/porders/api/scan/amount", methods=["POST"])
def api_scan_amount():
    """Amount milao -- the amount ON THE PAPER, typed. = the scan: Marg galat (the S371 WRONG mark, the link stays).
    = Marg: Scan galat padha (the link EXACT, the paper amount kept in purchase_scan_state). Neither: the owner's line."""
    u, con, kind, err = _auth()
    if err:
        return err
    no = _s440_write(u, kind)
    if no:
        return no
    pa = _pa()
    b = request.get_json(silent=True) or {}
    sid = _s440_scan_arg(b)
    who = u.get("user") or ""
    raw = str(b.get("paper") or "").replace(",", "").replace("₹", "").strip()
    if not re.fullmatch(r"\d{1,9}(\.\d{1,2})?", raw):
        return jsonify(ok=False, error="bad_amount", message="Sirf ank likhiye — jaise 14442"), 400
    paper = int(round(float(raw) * 100))
    pa._ensure_s439(con)
    lk = con.execute("SELECT bill_id, grade FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    scans = _s440_scans(con) or {}
    if not lk or sid not in scans:
        return jsonify(ok=False, error="no_such_line", message="Yeh scan kisi bill se juda nahi hai."), 409
    bill = con.execute("SELECT id, supplier, bill_no, amount_p, month, verdict, wrong_amount_p FROM purchase_bill WHERE id=?", (lk[0],)).fetchone()   # S662: + wrong_amount_p
    row = _s440_state(con).get(sid) or {}
    scan_p = row.get("paper_amount") if row.get("paper_amount") is not None else scans[sid]["amount_p"]
    marg_p = int(bill[3] or 0)
    ym726 = (con.execute("SELECT COALESCE(month, substr(bill_date,1,7)) FROM purchase_bill WHERE id=?", (bill[0],)).fetchone() or [""])[0] or ""
    if row.get("amount_state") or not _s440_differs(scan_p, marg_p, ym726):
        return jsonify(ok=False, error="settled", message="Is line ka jawab pehle hi darj hai."), 409
    sup = pa.supplier_key(bill[1])
    if abs(paper - marg_p) <= S440_TOL_P:                         # the paper agrees with Marg: OCR misread the scan
        con.execute("UPDATE purchase_scan_link SET grade='EXACT', matched_on=? WHERE bill_id=?", ("paper amount = Marg (reception)", bill[0]))
        _s440_put(con, sid, who, paper_amount=paper, amount_state="scan_wrong")
        _audit(con, who, "scan_amount", bill[0], dict(scan=sid, outcome="scan_wrong", paper_p=paper, scan_p=scan_p, marg_p=marg_p, grade="EXACT", kit="S440"))
        con.commit()
        out = dict(outcome="scan_wrong", message="Scan galat padha tha — theek kar diya.")
    elif abs(paper - int(scan_p)) <= S440_TOL_P and not bill[5] and not _s440_month_final(con, bill[4]):
        why = "bill %s %s: paper Rs %s, Marg Rs %s (Scan ka kaam, %s)" % (bill[2], sup, _s440_rs(paper)[1:], _s440_rs(marg_p)[1:], who)
        con.execute("UPDATE purchase_bill SET verdict='WRONG', verdict_by=?, verdict_at=?, wrong_amount_p=?, reason=? WHERE id=?",
                    (who, now_iso(), paper, why, bill[0]))
        _s440_put(con, sid, who, paper_amount=paper, amount_state="marg_wrong")
        _audit(con, who, "verdict", bill[0], dict(verdict="WRONG", wrong_amount_p=paper, reason=why, before=bill[5], via="Scan ka kaam"))
        _audit(con, who, "scan_amount", bill[0], dict(scan=sid, outcome="marg_wrong", paper_p=paper, scan_p=scan_p, marg_p=marg_p, kit="S440"))
        con.commit()
        out = dict(outcome="marg_wrong", message="Marg galat hai — Amir ki list par chala gaya.")
    elif bill[5] == "WRONG" and bill[6] is not None and abs(paper - int(bill[6])) <= S440_TOL_P:   # S662 (F-987's residual): a rescan of a
        # bill already marked WRONG at this very paper amount stands with that verdict -- nothing written to the bill, not the owner's line
        _s440_put(con, sid, who, paper_amount=paper, amount_state="marg_wrong")
        _audit(con, who, "scan_amount", bill[0], dict(scan=sid, outcome="marg_wrong", stands=True, paper_p=paper, scan_p=scan_p, marg_p=marg_p, kit="S662"))
        con.commit()
        out = dict(outcome="marg_wrong", message="Marg galat hai — yeh bill pehle se Amir ki list par hai.")
    else:                                                         # neither (or the bill already carries a person's verdict / a final month): the owner
        _s440_put(con, sid, who, paper_amount=paper, amount_state="owner")
        _audit(con, who, "scan_amount", bill[0], dict(scan=sid, outcome="owner", paper_p=paper, scan_p=scan_p, marg_p=marg_p, kit="S440"))
        con.commit()
        out = dict(outcome="owner", message="Dr sahab ko dikhao — unki list par chala gaya.")
    return jsonify(ok=True, scan=sid, bill=bill[0], **out)


def scan_status(con, ids):
    """The read door's answer: {scan id: {code, word, first}} in staff words. first = the scan this one repeats."""
    st = _s440_state(con)
    by_scan = {}
    try:
        by_scan = {r[0]: r[1] for r in con.execute("SELECT asset_bill_id, bill_id FROM purchase_scan_link")}
    except sqlite3.Error:
        pass
    bills, scans, out = None, {}, {}
    for sid in ids:
        row = st.get(sid) or {}
        if sid in by_scan:
            code = "linked"
            if not row.get("amount_state"):
                if bills is None:
                    bills = _s440_bills(con)
                    scans = _s440_scans(con) or {}
                b, s = bills.get(by_scan[sid]), scans.get(sid)
                sp = row.get("paper_amount") if row.get("paper_amount") is not None else (s or {}).get("amount_p")
                if b is not None and _s440_differs(sp, b["amount_p"], b.get("month") or str(b.get("bill_date") or "")[:7]):
                    code = "you"
        elif not row:
            continue                                              # not a pharmacy scan the matcher has seen: no word
        elif row.get("why") == "dup":
            code = "dup"
        elif (row.get("why") in S440_ASK and row.get("likely_bill")) or (row.get("why") == "vendor_unknown" and not row.get("chosen_vendor")):
            code = "you"
        else:
            code = "wait"
        out[str(sid)] = dict(code=code, word=S440_WORDS[code], first=(row.get("dup_cand") if code == "dup" else None))
    return out


@bp.route("/finance/porders/api/scan-status")
def api_scan_status():
    """READ ONLY, inside this unit's login gate: the asset app's list asks what each of its scans is waiting for."""
    u, con, kind, err = _auth()
    if err:
        return err
    ids = []
    for x in str(request.args.get("ids") or "").split(",")[:400]:
        if x.strip().isdigit():
            ids.append(int(x))
    return jsonify(ok=True, status=scan_status(con, ids), url=S440_FROM)


def _s440_owner_lines(con):
    """Needs you: the paper amount matched neither the scan nor Marg (or the bill already carried a verdict)."""
    out = []
    try:
        rows = con.execute("SELECT s.asset_bill_id, s.paper_amount, l.bill_id FROM purchase_scan_state s JOIN purchase_scan_link l "
                           "ON l.asset_bill_id=s.asset_bill_id WHERE s.amount_state='owner'").fetchall()
        for r in rows:
            b = con.execute("SELECT supplier, bill_no, amount_p, verdict FROM purchase_bill WHERE id=?", (r[2],)).fetchone()
            if b and not b[3] and abs(int(r[1] or 0) - int(b[2] or 0)) > S440_TOL_P:      # gone once the bill has a verdict, or Marg now says the paper's amount
                out.append(dict(cls="warn", target="porders", text="Scan amount to settle: bill %s %s — the paper reads %s, Marg %s (scan #%d)"
                                % (b[1], _pa().supplier_key(b[0]), _s440_rs(r[1]), _s440_rs(b[2]), r[0])))
    except sqlite3.Error:
        pass
    return out


# =====================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, D666 / D668 / D669) -- THE ONE-TASK RECEPTION SCREEN. porders_s454.py (beside this file)
# serves /finance/porders while porders.simple = 1 to the senders and the owner; ?old=1 (and a viewer) keeps this page, where the owner
# also finds his ordering cards and the S454 settings card. Owner lines about ordering join Needs you here; an order whose bill's scan
# is tied to it raises no "Scan karo" line for itself (received_unbilled); a paper with nothing read is a question, never "wait".
# =====================================================================================================================
def _s454_simple(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='porders.simple'").fetchone()
        return str(r[0]).strip() != "0" if (r and r[0] is not None and str(r[0]).strip() != "") else True
    except sqlite3.Error:
        return True


def _s454_old_page(con, kind, html):
    """The old page, for the owner: his S454 cards above it (English). Fail-soft: the page never waits on them."""
    if kind != "owner":
        return html
    try:
        import porders_s454                                   # noqa: PLC0415
        cards = porders_s454.owner_cards(con)
    except Exception as e:                                    # noqa: BLE001
        cards = '<div class="sub">S454 cards not available: %s</div>' % str(e)[:80].replace("<", "&lt;")
    return html.replace('<div class="sub" id="sub">', cards + '<div class="sub" id="sub">', 1)


def _s454_owner_lines(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        return order_sheet.owner_lines(con)
    except Exception:                                         # noqa: BLE001
        return []


def _s454_tied(con):
    try:
        return {r[0] for r in con.execute("SELECT order_id FROM order_scan_tie")}
    except sqlite3.Error:
        return set()


def _s454_unread(s, sid):
    """S454 4.7 (F-695): a pharmacy scan with neither a bill number nor an amount read, or read as an Estimate / Challan / Quotation."""
    head = re.search(r"\b(ESTIMATE|CHALLAN|QUOTATION)\b", "%s %s" % (s.get("vendor") or "", s.get("bill_no") or ""), re.I)
    return bool((not str(s.get("bill_no") or "").strip() and s.get("amount_p") is None) or head)


def _s454_or_arrived(con):
    """S454 (4.4): an order that arrived by its bill's scan keeps its open lines counted (as on the shelf) until Marg's bill answers them
    (detect_supplies) -- so S403's shortage does not ask for it again in the meantime. No tie table yet: nothing added."""
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " OR o.id IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)"
    except sqlite3.Error:
        return ""


def _s454_counted(con, bill_date):
    """A bill of a counted month (purchase.register_from, default 2026-10-01): the staff's work and the owner's alerts start there."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='purchase.register_from'").fetchone()
        frm = str(r[0]).strip()[:7] if (r and r[0]) else "2026-10"
    except sqlite3.Error:
        frm = "2026-10"
    return str(bill_date or "")[:7] >= frm



# ---- S454 part 2 (S454 5 / 7.3) ----------------------------------------------------------------------------------------------------------
def _s454_noise_p():
    """purchase.total_noise_rs in paise (Rs 10 when it cannot be read)."""
    try:
        import scan_register                                   # noqa: PLC0415
        return scan_register.noise_p(_db())
    except Exception:                                          # noqa: BLE001
        return 1000


def _s454_scan_lines(con):
    try:
        import scan_register                                   # noqa: PLC0415
        return scan_register.owner_lines(con)
    except Exception:                                          # noqa: BLE001
        return []
# ---- S454 part 2 end ---------------------------------------------------------------------------------------------------------------------



# ---- S749 (08-Nov-2026, Sanjeevni session 405, kit S749_ONE_SOURCE; D865, D866): reception's side follows the one source -------------------
#  (1) The amount question follows the new band: in a counted month a bill settles only to the rupee; a one-rupee difference (a round-off)
#      goes straight to Amir's card and asks reception nothing; beyond that reception types the paper's figure as before
#      (scan_register.s749_reception_asks). A parked month keeps the old band.
#  (2) An owner-confirmed supplier's bill (Ravi Medical Agency; setting purchase.owner_confirm_suppliers) is never on reception's Scan karo:
#      the owner confirms it himself on his step view -- unless he asked reception for that one paper (s749_confirm decision 'scan').
_s440_differs_before_s749 = _s440_differs


def _s440_differs(scan_p, marg_p, ym=None):                   # noqa: F811 -- S749: the one band
    if ym is None:
        return _s440_differs_before_s749(scan_p, marg_p, ym)
    try:
        import scan_register                                   # noqa: PLC0415
        return bool(scan_register.s749_reception_asks(_db(), scan_p, marg_p, ym))
    except Exception as e:                                    # noqa: BLE001 -- fail to the old reading: nothing new is asked
        if not _S726_SAID:
            _S726_SAID.append(1)
            print("porders S749: the band could not be read (%s) -- the old reading is used" % str(e)[:160], file=sys.stderr)
        return _s440_differs_before_s749(scan_p, marg_p, ym)


_unscanned_bills_before_s749 = unscanned_bills


def unscanned_bills(con):                                     # noqa: F811 -- S749: the owner-confirmed suppliers' bills are his, not reception's
    out = _unscanned_bills_before_s749(con)
    try:
        import scan_register                                   # noqa: PLC0415
        if not scan_register._s749_owner_sups(con):
            return out
        asked = scan_register.s749_scan_asked(con)
        return [x for x in out if x.get("bill_id") in asked or not scan_register.s749_owner_supplier(con, x.get("vendor") or x.get("vendor_norm"))]
    except Exception as e:                                    # noqa: BLE001 -- the list stands as it was
        print("porders S749: the owner's suppliers could not be read: %s" % str(e)[:160], file=sys.stderr)
        return out
_s440_owner_lines_before_s749 = _s440_owner_lines


def _s440_owner_lines(con):                                   # noqa: F811 -- S749 (D865 rule 3): the 'owner' amount state is Amir's correction now
    """Needs-you no longer carries 'Scan amount to settle' lines: a difference the paper and the scan could not settle is on Amir's card and on
    the owner's step view (row 2), read from the one register."""
    return []
# ---- S749 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S920 (21-Nov-2026, Sanjeevni session 499, kit S920_PURCHASE_FLOW_1; D1030): his Purchase orders page, grouped -----------------------
#  (1) init also mounts order_flow (the one reader of the purchase flow): /finance/porders/flow and /finance/porders/api/flow/act. Fail-soft.
#  (2) the owner's page (/finance/porders?old=1) opens on the grouped view of mock-up v4 FINAL -- Late · On the way · Arrived, not in Marg ·
#      medicines still missing · the team list (out of stock / substitutes) · Delivered and complete -- and the S454 cards, the settings and
#      the old ledger fold below it, unchanged. Any fault: the page exactly as before.
_init_before_s920 = init


def init(app, db_getter, require_fn, unit="medical"):         # noqa: F811 -- S920
    out = _init_before_s920(app, db_getter, require_fn, unit=unit)
    try:
        import order_flow                                     # noqa: PLC0415
        order_flow.init(app, _auth)
    except Exception as _ex_s920:                             # noqa: BLE001
        print("order_flow NOT mounted: %s" % _ex_s920, file=sys.stderr)
    return out


_s454_old_page_before_s920 = _s454_old_page


def _s454_old_page(con, kind, html):                          # noqa: F811 -- S920
    html = _s454_old_page_before_s920(con, kind, html)
    if kind != "owner":
        return html
    rf = con.row_factory
    try:
        import order_flow                                     # noqa: PLC0415
        con.row_factory = sqlite3.Row
        body = order_flow.owner_body(con)
    except Exception as e:                                    # noqa: BLE001 -- the page as before
        print("porders S920: the grouped view failed: %s" % str(e)[:200], file=sys.stderr)
        return html
    finally:
        con.row_factory = rf
    a = '<button id="s440up"'
    z = '<div id="body">loading&hellip;</div>'
    if html.count(a) != 1 or html.count(z) != 1 or html.index(a) > html.index(z):
        return html
    i = html.index(a)
    fold = ('<details style="background:#fff;border:1px solid #dde3e9;border-radius:12px;margin:16px auto;max-width:1080px">'
            '<summary style="padding:12px 16px;font-weight:700;cursor:pointer">Ordering cards, settings and the full ledger (as before) ▸</summary>')
    html = html[:i] + body + fold + html[i:]
    return html.replace(z, z + "</details>", 1)
# ---- S920 end ---------------------------------------------------------------------------------------------------------------------------
