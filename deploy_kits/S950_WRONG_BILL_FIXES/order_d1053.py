#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_d1053.py  ·  v1.0  ·  kit S939_ORDER_FINAL  ·  Session 509 (Sanjeevni)  ·  D1053 (the owner's "Mockup okay" 23-Nov 18:52 IST)
#
#  THE PURCHASE ORDER FLOW, PART 1 -- DARPAN MAKES THE DAY'S LIST FINAL (the logic; porders_s454.py and darpan_kal.py mount it):
#   (a) THE OLD-LINE STEP. The old lines (order_s778.red_lines: ordered and not come -- carries, late lines, Marg's old group) are
#       put to Darpan on his own tab as questions: आज के ऑर्डर में जोड़ो (order_s778.again / Marg's reorder) · आउट ऑफ़ स्टॉक →
#       डॉक्टर साहब (order_s778.na: the line leaves the order AT ONCE, the doctor's word follows and never holds the flow) · अभी नहीं
#       चाहिए (asked again on the next Marg sheet). A line that HAS COME leaves by itself (F-1623): a Marg purchase line of the medicine
#       from that dealer after the order (Amir's export), or -- for a line of Marg's open order ordered here -- the order's bill scan.
#       A line whose order is still within its delivery days is never asked (red_lines' own age rule); it surfaces when late.
#   (b) RECEPTION ONLY RAISES. On a card line reception has "Dealer ke paas nahi → Darpan ko" (no Out of stock, no remove): Darpan
#       answers रहने दो, ऑर्डर में · आउट ऑफ़ स्टॉक → डॉक्टर साहब · इस बार हटाओ (the S619 'dealer_no' removal, lifted by a newer sheet).
#   (c) ONE LIST. On order.source = marg_sheet Darpan's tab shows the same cards reception orders from (order_sheet.entries), never the
#       engine's proposals beside them (F-1624).
#   (d) सूची पक्की करो. Darpan makes the list final once every question is answered (the doctor may too). Until then reception's
#       WhatsApp all and its confirm door are LOCKED; Call and Order done stay open always. Final is per Marg sheet.
#   (e) THE SENT RECORD. Each dealer ordered keeps its line -- "WhatsApp gaya hh:mm · phone ne report kiya" / "Call se order hh:mm
#       (name)" / "WhatsApp line mein" -- with the day its goods are due, until its goods come (order_track's own arrival).
#  The switch: setting order.d1053 ('1' on; anything else: every screen and door exactly as before this kit).
#  Tables (its own): order_d1053_q (each raise and each decision) · order_d1053_later · order_d1053_final.
#  It writes only through the doors that already exist (order_s778.again / na, the reorder of a Marg line, the S619 removal); every
#  wrapper is fail-soft.
# =============================================================================
import datetime as dt
import html as _html
import json
import re
import sqlite3
import sys

VERSION = "1.0"
KIT = "S939_ORDER_FINAL"
P = "/finance/porders"

DDL = (
    "CREATE TABLE IF NOT EXISTS order_d1053_q (id INTEGER PRIMARY KEY, sheet_key TEXT NOT NULL, kind TEXT NOT NULL, ref TEXT NOT NULL,"
    " sn TEXT, vendor TEXT, item TEXT, qty_text TEXT, src TEXT, raised_by TEXT, raised_at TEXT, said TEXT,"
    " answer TEXT, answered_by TEXT, answered_at TEXT, gone_at TEXT)",
    "CREATE TABLE IF NOT EXISTS order_d1053_later (kind TEXT NOT NULL, ref TEXT NOT NULL, sheet_key TEXT NOT NULL, by TEXT, at TEXT,"
    " PRIMARY KEY (kind, ref, sheet_key))",
    "CREATE TABLE IF NOT EXISTS order_d1053_final (sheet_key TEXT PRIMARY KEY, day TEXT, at TEXT NOT NULL, by TEXT, counts TEXT)",
)

# Darpan's Devanagari · reception's Roman Hindi · the doctor's English
DEV = {"patte": "पत्ते", "patta": "पत्ता", "goli": "गोली", "nag": "नग", "botal": "बोतल", "tube": "ट्यूब", "vial": "वायल", "jar": "जार",
       "pudiya": "पुड़िया"}


def esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def _s7():
    import order_s778                                          # noqa: PLC0415
    return order_s778


def _os():
    import order_sheet                                         # noqa: PLC0415
    return order_sheet


def _ot():
    import order_track                                         # noqa: PLC0415
    return order_track


def log(where, e):
    print("S939 %s failed: %r" % (where, e), file=sys.stderr)


def ensure(con):
    for s in DDL:
        con.execute(s)


def on(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='order.d1053'").fetchone()
        return bool(r) and str(r[0]).strip() == "1"
    except sqlite3.Error:
        return False


def live(con):
    """The flow applies: switched on and the order made from Marg's sheet."""
    try:
        return on(con) and _os().source(con) == "marg_sheet"
    except Exception:                                          # noqa: BLE001
        return False


def now_iso():
    return _os().now_iso()


def hm(iso):
    s = str(iso or "")
    return s[11:16] if len(s) >= 16 else ""


def ddmm(iso):
    s = str(iso or "")
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) >= 10 else ""


def dev(t):
    """A staff quantity ('10 patte') in Darpan's script ('10 पत्ते')."""
    return re.sub(r"\b(patte|patta|goli|nag|botal|tube|vial|jar|pudiya)\b", lambda m: DEV[m.group(1).lower()], str(t or ""), flags=re.I)


def who_name(s):
    return _s7().who_name(s)


def short(v):
    return _s7().short(v)


# ------------------------------------------------------------------ the sheet a decision belongs to
def sheet_now(con):
    """(key, sheet row or None): the newest Marg sheet decides -- 'sheet:<id>'; with no sheet, the day."""
    ns = _os().newest_sheet(con)
    if ns:
        return "sheet:%d" % int(ns["id"]), ns
    return "day:" + _os().today().isoformat(), None


def final_row(con, key=None):
    ensure(con)
    key = key or sheet_now(con)[0]
    r = con.execute("SELECT * FROM order_d1053_final WHERE sheet_key=?", (key,)).fetchone()
    return dict(r) if r else None


def locked(con):
    """WhatsApp all waits: the flow is live, a Marg sheet is in, and Darpan has not made it final."""
    if not live(con):
        return False
    key, ns = sheet_now(con)
    return bool(ns) and final_row(con, key) is None


# ------------------------------------------------------------------ (a) F-1623: an old line that has come leaves by itself
def _order_bills(con, oid):
    out = set()
    if not oid:
        return out
    try:
        for r in con.execute("SELECT billed_bill_no FROM purchase_order_line WHERE order_id=? AND billed_bill_no IS NOT NULL", (int(oid),)):
            if str(r[0] or "").strip():
                out.add(str(r[0]).strip())
    except sqlite3.Error:
        pass
    return out


def _marg_bought(con, sn, day):
    """[(norm item, bill, date)] of Marg's purchase lines from dealer `sn` dated on or after `day` (Amir's export) -- the effective
    lines only (porders' EFF_LINE, as order_sheet._marg_hit reads them: a superseded export's lines do not count)."""
    S = _s7()
    eff = ""
    try:
        eff = " AND " + _os()._pa().EFF_LINE
    except Exception:                                          # noqa: BLE001
        eff = ""
    try:
        return [(S.norm(r[0]), str(r[1] or "").strip(), str(r[2] or "")) for r in con.execute(
            "SELECT l.item, l.bill_no, l.bill_date FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_date>=? "
            "AND UPPER(COALESCE(l.direction,'PURCHASE'))='PURCHASE'" + eff, (sn, str(day or "")[:10]))]
    except sqlite3.Error:
        return []


def arrived(con, c, cache=None):
    """None, or how an old line came: ('marg', bill, date) -- a Marg purchase of the medicine from its dealer on or after the line's
    day, on a bill that is not the one its own order was billed on (that bill is why a carry is short) -- or ('scan', stamp) -- a
    line of Marg's open order ordered here whose order has its bill scan tied."""
    cache = {} if cache is None else cache
    fs = set(c.get("fs") or _s7().forms(con, c["item"], c["sn"]))
    k = (c["sn"], c["day"])
    if k not in cache:
        cache[k] = _marg_bought(con, c["sn"], c["day"])
    own = _order_bills(con, c.get("from_order")) if c.get("kind") in ("carry", "late") else set()
    for n, bill, day in cache[k]:
        if c.get("kind") == "late" and day[:10] <= str(c["day"])[:10]:
            continue                                           # a late line: a bill of its own order's day is an earlier delivery
        if n in fs and bill and bill not in own:
            return ("marg", bill, day)
    if c.get("kind") == "old" and c.get("from_order"):
        try:
            r = con.execute("SELECT stamp FROM order_scan_tie WHERE order_id=?", (int(c["from_order"]),)).fetchone()
        except sqlite3.Error:
            r = None
        if r:
            return ("scan", str(r[0] or ""))
    return None


def split_arrived(con, lines):
    """(still open, came) of red_lines' list."""
    cache, keep, came = {}, [], []
    for c in lines:
        try:
            a = arrived(con, c, cache)
        except Exception as e:                                 # noqa: BLE001 -- a line we cannot judge stays asked
            log("arrived", e)
            a = None
        if a:
            came.append(dict(c, came=a))
        else:
            keep.append(c)
    return keep, came


# ------------------------------------------------------------------ the questions on Darpan's tab
def _later_keys(con, key):
    return {(r[0], r[1]) for r in con.execute("SELECT kind, ref FROM order_d1053_later WHERE sheet_key=?", (key,))}


def _raises(con, key, open_only=True):
    """The raises of this sheet (card lines), and every open raise of an order (whatever sheet it came under: it lives until the
    order's lines are settled)."""
    q = "SELECT * FROM order_d1053_q WHERE raised_at IS NOT NULL AND gone_at IS NULL AND (sheet_key=? OR kind='order')"
    if open_only:
        q += " AND answer IS NULL"
    return [dict(r) for r in con.execute(q + " ORDER BY id", (key,))]


def _olines(con, key, oraises, red, later):
    """An order raised by reception whose open lines are not in the red lines yet (under OLD_AFTER working days): each open line is
    Darpan's question itself (kind 'oline', ref 'oid:lid'). A raise whose order has no open line left is gone."""
    OS, OT, S = _os(), _ot(), _s7()
    out = []
    t = now_iso()
    decided = {r[0] for r in con.execute("SELECT ref FROM order_d1053_q WHERE kind='oline' AND answer IN ('add','na')")}
    in_red = {(str(c.get("from_order") or ""), S.norm(c["item"])) for c in red}
    for r in oraises:
        try:
            s = (OT.light_all(con, OS.now(), oids=[int(r["ref"])]) or [None])[0]
        except Exception as e:                                 # noqa: BLE001
            log("oline light", e)
            s = None
        ls = [x for x in (s or {}).get("lines") or [] if x["state"] in ("open", "part", "short")]
        if not ls:
            con.execute("UPDATE order_d1053_q SET gone_at=? WHERE id=? AND gone_at IS NULL", (t, r["id"]))
            continue
        for x in ls:
            ref = "%s:%d" % (r["ref"], int(x["id"]))
            if ref in decided or ("oline", ref) in later or (str(r["ref"]), S.norm(x["item"])) in in_red:
                continue
            try:                                               # a medicine of the order that came on another bill is not asked
                if arrived(con, dict(kind="late", sn=s["sn"], item=x["item"], day=s["day"], from_order=int(r["ref"]))):
                    continue
            except Exception as e:                             # noqa: BLE001
                log("oline arrived", e)
            out.append(dict(kind="oline", ref=ref, item=x["item"], qty=dev(x.get("qty_text") or ""), qty_en=x.get("qty_text") or "",
                            vendor=short(s["vendor"]), day=ddmm(s["day"]), age=int(S.workdays(s["day"]) or 0), note="",
                            said=dict(by=who_name(r["raised_by"]), at=hm(r["raised_at"]))))
    con.commit()
    return out


def _card_line(cards, sn, src, ref, item):
    for e in cards:
        if e["sn"] != sn:
            continue
        for l in e["lines"]:
            if l["src"] == src and str(l["ref"]) == str(ref) and l["item"] == item:
                return e, l
    return None, None


def questions(con, cards=None):
    """dict(old=[...], raised=[...], came_n, transit_n, pending, key). Writes only a raise whose line has left today's cards (gone)."""
    ensure(con)
    S, OS = _s7(), _os()
    key, _ns = sheet_now(con)
    cards = OS.entries(con) if cards is None else cards
    al = S.red_lines(con, False, cards)                        # the wrapped reader: lines that came are already out
    came_n = 0
    try:
        came_n = int(getattr(_g(), "d1053_came_n", 0) or 0) if _g() is not None else 0
    except Exception:                                          # noqa: BLE001
        came_n = 0
    later = _later_keys(con, key)
    notes = {}
    raises = _raises(con, key)
    for r in raises:
        if r["kind"] == "order":
            notes.setdefault((r["kind"], r["ref"]), r)
    old = []
    for c in al:
        if c.get("on_card"):
            continue                                           # already on today's card: it is ordered with it
        if (c["kind"], c["ref"]) in later:
            continue
        n = notes.get((c["kind"], c["ref"])) or (notes.get(("order", str(c.get("from_order")))) if c.get("from_order") else None)
        old.append(dict(kind=c["kind"], ref=c["ref"], item=c["item"], qty=dev(c["qty_text"]), qty_en=c["qty_text"], vendor=short(c["vendor"]),
                        day=ddmm(c["day"]), age=int(c.get("age") or 0), note=dev(c.get("note") or ""),
                        said=(dict(by=who_name(n["raised_by"]), at=hm(n["raised_at"])) if n else None)))
    try:
        old += _olines(con, key, [r for r in raises if r["kind"] == "order"], al, later)
    except Exception as e:                                     # noqa: BLE001 -- the raise waits; the red lines stand
        log("olines", e)
    raised = []
    t = now_iso()
    gone = False
    for r in raises:
        if r["kind"] != "card":
            continue
        e, l = _card_line(cards, r["sn"], r["src"], r["ref"], r["item"])
        if not l:
            con.execute("UPDATE order_d1053_q SET gone_at=? WHERE id=? AND gone_at IS NULL", (t, r["id"]))
            gone = True
            continue
        raised.append(dict(id=r["id"], item=r["item"], qty=dev(r["qty_text"]), qty_en=r["qty_text"], vendor=short(r["vendor"]),
                           by=who_name(r["raised_by"]), at=hm(r["raised_at"]), sn=r["sn"]))
    if gone:
        con.commit()
    transit_n = 0
    try:
        for s in _ot().awaited(con, OS.now()):
            transit_n += sum(1 for x in s["lines"] if x["state"] in ("open", "awaiting"))
    except Exception as e:                                     # noqa: BLE001
        log("transit", e)
    return dict(old=old, raised=raised, came_n=came_n, transit_n=transit_n, pending=len(old) + len(raised), key=key)


def _g():
    try:
        from flask import g, has_app_context                  # noqa: PLC0415
        return g if has_app_context() else None
    except Exception:                                          # noqa: BLE001
        return None


def clear_cache():
    """After a write: the request's cached red lines (order_s778's and this kit's) are read again."""
    g = _g()
    if g is None:
        return
    for k in ("s778_red_0", "s778_red_1", "d1053_red_0", "d1053_red_1"):
        try:
            setattr(g, k, None)
        except Exception:                                      # noqa: BLE001
            pass


def red_lines_filter(con, out):
    """order_s778.red_lines with the lines that came taken out (F-1623); their count kept for the tab's line."""
    if not live(con):
        return out
    keep, came = split_arrived(con, out)
    g = _g()
    if g is not None:
        try:
            g.d1053_came_n = len(came)
        except Exception:                                      # noqa: BLE001
            pass
    return keep


# ------------------------------------------------------------------ the doors' work (each returns (dict, status))
def raise_line(con, who, b):
    """Reception: 'Dealer ke paas nahi → Darpan ko' on a card line (sn, src, ref, item) or on an order of the flow strip (oid)."""
    ensure(con)
    OS = _os()
    key, _ns = sheet_now(con)
    t = now_iso()
    if b.get("oid"):
        try:
            oid = int(b.get("oid"))
        except (TypeError, ValueError):
            return dict(ok=False, error="bad_request"), 400
        o = con.execute("SELECT vendor, supplier_norm FROM purchase_order WHERE id=?", (oid,)).fetchone()
        if not o:
            return dict(ok=False, error="gone", message="Yeh order ab nahi hai."), 409
        if con.execute("SELECT 1 FROM order_d1053_q WHERE kind='order' AND ref=? AND gone_at IS NULL AND answer IS NULL", (str(oid),)).fetchone():
            return dict(ok=True, already=True), 200
        cur = con.execute("INSERT INTO order_d1053_q (sheet_key, kind, ref, sn, vendor, raised_by, raised_at, said) VALUES (?,?,?,?,?,?,?,?)",
                          (key, "order", str(oid), o[1], o[0], who, t, "dealer_no"))
        OS.audit(con, who, "d1053_raise", cur.lastrowid, dict(order=oid, kit=KIT))
        con.commit()
        clear_cache()
        return dict(ok=True, id=cur.lastrowid), 200
    sn, src, ref, item = (str(b.get(k) or "") for k in ("sn", "src", "ref", "item"))
    if src not in ("sheet", "proposal", "ortho", "carry", "s778"):
        return dict(ok=False, error="bad_line"), 400
    e, l = _card_line(OS.entries(con), sn, src, ref, item)
    if not l:
        return dict(ok=False, error="gone", message="Yeh line ab order mein nahi hai."), 409
    if e.get("draft") or e.get("state") != "pending":
        return dict(ok=False, error="has_draft", message="Is supplier ka order ban chuka hai."), 409
    if con.execute("SELECT 1 FROM order_d1053_q WHERE sheet_key=? AND kind='card' AND sn=? AND src=? AND ref=? AND item=? AND answer IS NULL AND gone_at IS NULL",
                   (key, sn, src, ref, item)).fetchone():
        return dict(ok=True, already=True, item=item), 200
    cur = con.execute("INSERT INTO order_d1053_q (sheet_key, kind, ref, sn, vendor, item, qty_text, src, raised_by, raised_at, said) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (key, "card", ref, sn, e["vendor"], item, OS.qty_of(l, False, con=con), src, who, t, "dealer_no"))
    OS.audit(con, who, "d1053_raise", cur.lastrowid, dict(sn=sn, src=src, ref=ref, item=item, kit=KIT))
    con.commit()
    clear_cache()
    return dict(ok=True, id=cur.lastrowid, item=item), 200


def raised_on_card(con, sn):
    """{(src, ref, item): (by, hh:mm)} of the card's lines raised to Darpan and not yet answered -- the card's note."""
    try:
        key, _ns = sheet_now(con)
        return {(r["src"], r["ref"], r["item"]): (who_name(r["raised_by"]), hm(r["raised_at"])) for r in _raises(con, key)
                if r["kind"] == "card" and r["sn"] == sn}
    except Exception as e:                                     # noqa: BLE001
        log("raised_on_card", e)
        return {}


def _record(con, key, kind, ref, c, answer, who):
    con.execute("INSERT INTO order_d1053_q (sheet_key, kind, ref, sn, vendor, item, qty_text, answer, answered_by, answered_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (key, kind, str(ref), c.get("sn"), c.get("vendor"), c.get("item"), c.get("qty_text"), answer, who, now_iso()))


def decide(con, who, b):
    """Darpan (or the doctor): an old line -- {kind, ref, act: add | na | later} -- or a raised card line -- {qid, act: keep | na | remove}."""
    ensure(con)
    S, OS = _s7(), _os()
    key, _ns = sheet_now(con)
    act = str(b.get("act") or "")
    if b.get("qid"):
        try:
            qid = int(b.get("qid"))
        except (TypeError, ValueError):
            return dict(ok=False, error="bad_request"), 400
        r = con.execute("SELECT * FROM order_d1053_q WHERE id=? AND kind='card'", (qid,)).fetchone()
        if not r:
            return dict(ok=False, error="gone"), 404
        r = dict(r)
        if r["answer"] or r["gone_at"]:
            return dict(ok=True, already=True, item=r["item"]), 200
        if act == "keep":
            pass
        elif act == "na":
            body, code = S.na(con, who, dict(sn=r["sn"], src=r["src"], ref=r["ref"], item=r["item"]))
            if code != 200:
                return body, code
        elif act == "remove":
            e, l = _card_line(OS.entries(con), r["sn"], r["src"], r["ref"], r["item"])
            if not l:
                con.execute("UPDATE order_d1053_q SET gone_at=? WHERE id=?", (now_iso(), qid))
                con.commit()
                return dict(ok=True, already=True, item=r["item"]), 200
            if e.get("draft") or e.get("state") != "pending":
                return dict(ok=False, error="has_draft", message="इस सप्लायर का ऑर्डर बन चुका है।"), 409
            con.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at, reason) VALUES (?,?,?,NULL,1,?,?,'dealer_no') "
                        "ON CONFLICT(src, ref, item) DO UPDATE SET removed=1, by=excluded.by, at=excluded.at, reason=excluded.reason",
                        (r["src"], r["ref"], r["item"], who, now_iso()))
            if r["src"] == "carry":
                con.execute("UPDATE order_carry SET dropped_at=?, dropped_by=? WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (now_iso(), who, int(r["ref"])))
        else:
            return dict(ok=False, error="bad_act"), 400
        con.execute("UPDATE order_d1053_q SET answer=?, answered_by=?, answered_at=? WHERE id=?", (act, who, now_iso(), qid))
        OS.audit(con, who, "d1053_" + act, qid, dict(item=r["item"], kit=KIT))
        con.commit()
        clear_cache()
        return dict(ok=True, item=r["item"], act=act), 200
    kind, ref = str(b.get("kind") or ""), str(b.get("ref") or "")
    if kind == "oline":
        return _decide_oline(con, who, key, ref, act)
    if kind not in ("carry", "late", "old"):
        return dict(ok=False, error="bad_line"), 400
    c = S.find_line(con, kind, ref)
    if not c:
        return dict(ok=True, already=True, gone=True), 200        # answered meanwhile, or it came
    if act == "add":
        if c.get("marg_line"):                                 # a line of Marg's open order never ordered here: Marg's own line again
            lid = int(c["marg_line"])
            l = next((x for x in OS.open_order(con)["lines"] if x["id"] == lid), None)
            if l is None or not OS.can_reorder(l):
                return dict(ok=False, error="not_old", message="यह लाइन अब पुराने ऑर्डर में नहीं है।"), 409
            con.execute("UPDATE order_sheet_line SET state='to_order', reorder_day=?, marg_date=NULL, marg_bill=NULL, marg_seen_at=NULL, updated_at=? WHERE id=?",
                        (OS.today().isoformat(), now_iso(), lid))
            OS.audit(con, who, "s454_reorder", lid, dict(item=c["item"], by_d1053=True))
        else:
            body, code = S.again(con, who, kind, ref)
            if code != 200:
                return body, code
    elif act == "na":
        body, code = S.na(con, who, dict(kind=kind, ref=ref))
        if code != 200:
            return body, code
    elif act == "later":
        con.execute("INSERT OR IGNORE INTO order_d1053_later (kind, ref, sheet_key, by, at) VALUES (?,?,?,?,?)", (kind, ref, key, who, now_iso()))
    else:
        return dict(ok=False, error="bad_act"), 400
    _record(con, key, kind, ref, c, act, who)
    OS.audit(con, who, "d1053_" + act, ref, dict(kind=kind, item=c["item"], kit=KIT))
    con.commit()
    clear_cache()
    return dict(ok=True, item=c["item"], act=act), 200


def _decide_oline(con, who, key, ref, act):
    """A line of an order reception raised, not yet among the red lines: add -> order_flow's 'again' (onto today's card), na ->
    its 'oos' (out of stock, to the doctor), later -> asked again on the next sheet."""
    try:
        oid, lid = (int(x) for x in str(ref).split(":", 1))
    except (TypeError, ValueError):
        return dict(ok=False, error="bad_line"), 400
    row = con.execute("SELECT l.item, o.vendor, o.supplier_norm FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.id=? AND o.id=?",
                      (lid, oid)).fetchone()
    if not row:
        return dict(ok=False, error="gone"), 409
    c = dict(item=row[0], vendor=row[1], sn=row[2], qty_text="")
    if act in ("add", "na"):
        import order_flow                                      # noqa: PLC0415 -- beside this file
        body, code = order_flow.act(con, who, dict(do=("again" if act == "add" else "oos"), oid=oid, lid=lid))
        if code != 200:
            return body, code
    elif act == "later":
        con.execute("INSERT OR IGNORE INTO order_d1053_later (kind, ref, sheet_key, by, at) VALUES ('oline',?,?,?,?)", (ref, key, who, now_iso()))
    else:
        return dict(ok=False, error="bad_act"), 400
    _record(con, key, "oline", ref, c, act, who)
    _os().audit(con, who, "d1053_" + act, ref, dict(kind="oline", item=c["item"], kit=KIT))
    con.commit()
    clear_cache()
    return dict(ok=True, item=c["item"], act=act), 200


def make_final(con, who):
    """सूची पक्की करो -- once every question is answered; one row per Marg sheet."""
    ensure(con)
    key, ns = sheet_now(con)
    if not ns:
        return dict(ok=False, error="no_sheet", message="आज की Marg सूची अभी नहीं आई।"), 409
    if final_row(con, key):
        return dict(ok=True, already=True), 200
    q = questions(con)
    if q["pending"]:
        return dict(ok=False, error="pending", message="पहले ऊपर के %d फ़ैसले।" % q["pending"], pending=q["pending"]), 409
    counts = {}
    for r in con.execute("SELECT answer, COUNT(*) FROM order_d1053_q WHERE sheet_key=? AND answer IS NOT NULL GROUP BY answer", (key,)):
        counts[r[0]] = r[1]
    con.execute("INSERT OR IGNORE INTO order_d1053_final (sheet_key, day, at, by, counts) VALUES (?,?,?,?,?)",
                (key, _os().today().isoformat(), now_iso(), who, json.dumps(counts)))
    _os().audit(con, who, "d1053_final", key, dict(counts=counts, kit=KIT))
    con.commit()
    return dict(ok=True, key=key), 200


# ------------------------------------------------------------------ (e) the sent record: each dealer ordered, until its goods come
def sent_record(con, days=7):
    """[{id, vendor, sn, via, at, word_hi, word_en, word_dev, due, items, msg}] -- the flow's orders sent in the last `days` days whose
    goods have not come (order_track's arrival), newest first."""
    OS, OT = _os(), _ot()
    since = (OS.today() - dt.timedelta(days=days)).isoformat()
    rows = [dict(r) for r in con.execute("SELECT * FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') AND COALESCE(order_via,'')<>'paper' "
                                         "AND created_at>=? ORDER BY created_at DESC, id DESC", (since,))]
    if not rows:
        return []
    try:
        light = {s["id"]: s for s in OT.light_all(con, OS.now(), oids=[r["id"] for r in rows])}
    except Exception as e:                                     # noqa: BLE001
        log("sent light", e)
        light = {}
    out = []
    for o in rows:
        s = light.get(o["id"])
        if s is None or s.get("arrived"):
            continue
        m = None
        try:
            m = con.execute("SELECT status, sent_at, queued_at FROM supplier_msg WHERE kind='order' AND ref=? ORDER BY id DESC LIMIT 1", (o["id"],)).fetchone()
        except sqlite3.Error:
            m = None
        via = str(o.get("order_via") or "")
        by = who_name(o.get("created_by"))
        at = hm(o["created_at"])
        if via.startswith("whatsapp") and m and m[0] == "sent":
            at = hm(m[1]) or at
            hi, en, dv = ("✓ WhatsApp gaya %s · phone ne report kiya" % at, "✓ WhatsApp sent %s · the phone reported it" % at,
                          "✓ WhatsApp गया %s · फ़ोन ने बताया" % at)
        elif via.startswith("whatsapp"):
            hi, en, dv = ("WhatsApp line mein (%s)" % at, "WhatsApp waiting for the phone (%s)" % at, "WhatsApp लाइन में (%s)" % at)
        else:
            hi, en, dv = ("✓ Call se order %s (%s)" % (at, by), "✓ Ordered by call %s (%s)" % (at, by), "✓ कॉल से ऑर्डर %s (%s)" % (at, by))
        due = s.get("due_at")
        dd = due.strftime("%d-%m") if due else ""
        items = [x["item"] for x in s.get("lines") or []]
        out.append(dict(id=o["id"], vendor=o["vendor"], sn=s.get("sn"), via=via, day=str(o["created_at"])[:10], word_hi=hi, word_en=en, word_dev=dv,
                        due=dd, late=bool(s.get("late")), items=items))
    return out


# ------------------------------------------------------------------ Darpan's tab: the payload (one list on marg_sheet)
def darpan_payload(con):
    """What the tab draws on order.source = marg_sheet with the flow on: the sheet, the questions, the one list, the final, the sent record."""
    ensure(con)
    OS = _os()
    cards = OS.entries(con)
    oo = OS.open_order(con)
    key, ns = sheet_now(con)
    q = questions(con, cards)
    fr = final_row(con, key)
    raised = {}
    for r in q["raised"]:
        raised.setdefault(r["sn"], []).append(r["item"])
    lst = []
    for e in cards:
        lst.append(dict(vendor=short(e["vendor"]), full=e["vendor"], n=len(e["lines"]), state=e.get("state") or "pending",
                        lines=[dict(item=l["item"], qty=dev(OS.qty_of(l, False, con=con)), raised=(l["item"] in raised.get(e["sn"], []))) for l in e["lines"]]))
    sent = [dict(vendor=short(s["vendor"]), word=s["word_dev"], due=s["due"], late=s["late"], n=len(s["items"])) for s in sent_record(con)]
    return dict(on=True, sheet=dict(at=oo.get("stamp_text") or "", suppliers=int(oo.get("suppliers") or 0), count=int(oo.get("count") or 0), key=key,
                                    present=bool(ns)),
                old=q["old"], raised=q["raised"], came_n=q["came_n"], transit_n=q["transit_n"], pending=q["pending"],
                final=(dict(at=hm(fr["at"]), by=("पहले से" if fr["by"] == "install" else who_name(fr["by"]))) if fr else None), cards=lst, sent=sent,
                wrong=_s950_wrong(con))


def _s950_wrong(con):
    """S950 (F-1658): the open wrong-bill lines for Darpan's tab (order_d1053_msg beside this file); [] on any fault."""
    try:
        import order_d1053_msg                                 # noqa: PLC0415
        return order_d1053_msg.darpan_wrong(con)
    except Exception as e:                                     # noqa: BLE001
        log("S950 wrong", e)
        return []


# ------------------------------------------------------------------ reception's words (Roman Hindi; the doctor's English)
def banner_html(con, en):
    """The line over reception's cards: waiting for Darpan (WhatsApp locked) / Darpan made it final hh:mm."""
    if not live(con):
        return ""
    key, ns = sheet_now(con)
    if not ns:
        return ""
    fr = final_row(con, key)
    if fr and fr.get("by") == "install":
        return ""                                              # the sheet that was in at the install: ordered before this flow
    if fr:
        t = ("Darpan made the list final %s — WhatsApp is open" % hm(fr["at"])) if en else ("Darpan ne list pakki ki %s — WhatsApp bhej sakte hain" % hm(fr["at"]))
        return '<div class="ok" id="d1053final"><div class="t">%s</div></div>' % esc(t)
    q = questions(con)
    n = q["pending"]
    if en:
        t, s = "Waiting for Darpan to make the list final", ("%d old medicine%s wait for his decision. " % (n, "" if n == 1 else "s") if n else "") + \
            "WhatsApp all is locked until then, so no wrong medicine goes to a dealer. Calls are open."
    else:
        t, s = "Darpan ke pakka karne ka intezaar", ("%d purani dawa par Darpan ka faisla baaki. " % n if n else "") + \
            "Tab tak WhatsApp band hai — galat dawa dealer ko na jaaye. Call karna kabhi bhi chalu hai."
    return ('<div id="d1053wait" style="background:#fff6e0;border:2px solid #8a5a00;border-radius:14px;padding:12px;margin:8px 0">'
            '<div style="font-weight:700;color:#6b4500;font-size:16px">%s</div><div style="font-size:14px">%s</div></div>' % (esc(t), esc(s)))


def sent_html(con, en):
    rows = sent_record(con)
    if not rows:
        return ""
    h = ['<div class="mut" id="d1053senthead" style="font-weight:700;color:#2f6b45;margin-top:8px">%s</div>'
         % esc("SENT — shown here until the goods come" if en else "BHEJA GAYA — maal aane tak yahin dikhega")]
    for s in rows:
        due = ("Goods due %s evening" % s["due"] if en else "Maal %s shaam tak" % s["due"]) if s["due"] else ""
        if s["late"]:
            due = ("Late — due %s" % s["due"]) if en else ("Late — %s tak aana tha" % s["due"])
        h.append('<div class="ln d1053sent" data-oid="%d"><div class="t"><div class="a">%s</div><div class="s grn">%s</div><div class="s">%s%s</div></div></div>'
                 % (s["id"], esc(s["vendor"]), esc(s["word_en"] if en else s["word_hi"]),
                    esc(due), (" · " + esc(", ".join(s["items"][:4]) + (" +%d" % (len(s["items"]) - 4) if len(s["items"]) > 4 else ""))) if s["items"] else ""))
    return "".join(h)


def raise_button(e, l):
    """Reception's one button on a card line (with the flow on): send it up to Darpan -- or the note that it went."""
    if l.get("src") == "draft" or e.get("draft") or e.get("state") != "pending":
        return ""
    return ('<button class="s778na d1053raise" onclick="%s">%s</button>'
            % (_s7().js_call(P + "/api/d1053/raise", dict(sn=e["sn"], src=l["src"], ref=str(l["ref"]), item=l["item"]), "null"),
               esc("Dealer ke paas nahi → Darpan ko")))


def raised_note(by_at, item="", en=False):
    by, at = by_at
    if en:
        t = "%sSent to Darpan %s — the dealer does not have it%s" % ((item + " — ") if item else "", at, (" (%s)" % by) if by else "")
    else:
        t = "%sDarpan ko bheja %s — \"dealer ke paas nahi\"%s" % ((item + " — ") if item else "", at, (" (%s)" % by) if by else "")
    return '<div class="nt d1053sent2" style="font-size:13px;color:#1f5f99;font-weight:600">%s</div>' % esc(t)
