#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_track.py  ·  v1.0  ·  kit S619_ORDER_TRACKER  ·  22-Oct-2026 (Sanjeevni session 335)
#
#  ONE ORDER, FIVE STEPS, THE SAME ON EVERY SCREEN: Ordered -> Arrived -> Bill scanned -> In Marg -> All lines came. The owner, 22-Oct-2026:
#  "called, arrived, scanned, goods not arrived, need these to be visible ... for all the concerned stakeholders ... not messy and very easy
#  to understand"; late = two days after ordering (Sunday not counted, a setting), at 18:00; a medicine that did not come goes back on that
#  dealer's next order by itself ("System, automatically"); a part-arrived order is followed up by reception or Shavez ("either to do").
#
#  TWO HALVES, ONE MODULE. Both take `now` (a walk passes a synthetic clock) and WRITE NOTHING -- except carry_pass, the one keyed step that
#  writes order_carry (called by order_sheet.cron_pass and by the walk).
#    light_all(con, now) / order_state_light(con, oid, now) -- finance.db ONLY (no spine, no assets.db): reception's call row and Maal aaya
#        list, Darpan's line and his order tab, the owner's Needs-you line and the duty map's SQL read this half.
#    order_state(con, oid, now, ctx) / full_all(con, now) -- the light half plus the scan half (assets.db READ ONLY): the head of a set-aside
#        scan, a paper of another dealer (a conflict note; it lights nothing), each scan's moment, and the SOFT NOTE of section 3.2 (a scan
#        never makes a line short, never moves a count, never feeds the carry). The owner's and Shavez's track page read it.
#
#  THE RULES (brief S619 v2, section 3.1):
#    * Ordered: created_at; sent_at = the WhatsApp message's sent_at; via; by -- normalised from every shape (who_name).
#    * Arrived: the earliest of a TAP (a line's arrived_at whose arrived_by is not 'marg', or received_at when received_by is a person), a SCAN
#      (the order's own tie, or any scan linked to a Marg bill that carries one of the order's lines), Marg's detection (detected_at) last.
#    * In Marg: the order's lines' billed_bill_no (never stock_figure.carried here).
#    * Lines came: Marg's billed_qty (below packs = SHORT by the difference; above = came as billed) -> the tap (supplied / missing) -> none.
#      Once Marg has billed any line of the order, a line it did not bill is SHORT (Marg's bill came without it). A line tapped 'Nahi mila' is
#      SHORT. A line tapped 'Kam aaya' with Marg not in yet is PART (the rest still awaited). An untapped line of an order that has not
#      arrived, or of an order with another line tapped, is OPEN; an untapped line of an order that arrived by its bill's scan alone waits for
#      Marg (AWAITING -- the bill came: not late).
#    * Due: the order's day + order.deliver_days days, not counting the days in order.deliver_skip (an order made on a skip day counts from
#      the next day), at DUE_HOUR. LATE = past due and a line OPEN or PART -- nothing arrived, or a part order.
#    * Outside hours: only the moment of a TAP against order.deliver_window (a scan or Marg's time never sets it).
#  The duty map's reception.order_arrival due_sql says LATE in one SELECT; the walk proves it equal to late_count() on the copy.
#  No phone number is read or printed by this file.
# =============================================================================
import datetime as dt
import difflib
import json
import re
import sqlite3

VERSION = "1.0"
KIT = "S619_ORDER_TRACKER"
DUE_HOUR = (18, 0)
DAYS3 = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")       # datetime.weekday() order
CARRY_DDL = ("CREATE TABLE IF NOT EXISTS order_carry (id INTEGER PRIMARY KEY, vendor TEXT NOT NULL, supplier_norm TEXT NOT NULL, item TEXT NOT NULL,"
             " from_order_id INTEGER NOT NULL, from_line_id INTEGER NOT NULL UNIQUE, qty INTEGER NOT NULL, pack_size INTEGER, reason TEXT NOT NULL"
             " CHECK (reason IN ('marg_short','tapped_missing')), at TEXT NOT NULL, done_order_id INTEGER, done_at TEXT, dropped_at TEXT, dropped_by TEXT)")
WORDS = {   # (owner English, Shavez / staff Roman Hindi)
    "soft_no": ("not seen on the scanned bill — Marg will confirm", "scan kiye bill par nahi dikha — Marg batayega"),
    "soft_on": ("on bill %s", "bill %s par"),
    "tapped_no": ("tapped Nahi mila; Marg billed %s", "Nahi mila tap hua tha; Marg mein %s aaya"),
    "tapped_kam": ("tapped Kam aaya (%s); Marg billed %s", "Kam aaya tap hua tha (%s); Marg mein %s aaya"),
    "two_orders": ("Marg's bill %s line also answers order %s", "Marg ka bill %s ki yeh line order %s par bhi gini gayi"),
    "other_dealer": ("its scan %s is a paper of another dealer (%s)", "iska scan %s kisi aur dealer (%s) ka kaagaz hai"),
    "set_aside": ("tied scan %s was set aside; its first scan is %s", "joda gaya scan %s hata diya gaya; asli scan %s hai"),
}


def _os():
    import order_sheet                                        # noqa: PLC0415 -- beside this file
    return order_sheet


def _pa():
    return _os()._pa()


def W(key, en, *a):
    s = WORDS[key][0 if en else 1]
    return (s % a) if a else s


# ------------------------------------------------------------------ small things
def _dtm(s):
    return _os()._dtm(s)


def _date(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def ddmm(iso):
    return _os().ddmm(iso)


def hm(d):
    return d.strftime("%H:%M") if d else ""


def setting(con, key):
    return _os().setting(con, key)


def since(con):
    v = setting(con, "order.track_since")
    return v[:10] if re.match(r"^\d{4}-\d\d-\d\d", v or "") else "2026-10-12"


def deliver_days(con):
    try:
        return max(0, min(14, int(float(setting(con, "order.deliver_days")))))
    except (TypeError, ValueError):
        return 2


def skip_days(con):
    return {x.strip().upper()[:3] for x in str(setting(con, "order.deliver_skip") or "").split(",") if x.strip().upper()[:3] in DAYS3}


def due_at(con, created, days=None, skip=None):
    """The order's day + order.deliver_days days not counting the skip days (an order made on a skip day counts from the next day), at DUE_HOUR."""
    d = _date(created)
    if d is None:
        return None
    days = deliver_days(con) if days is None else days
    skip = skip_days(con) if skip is None else skip
    k = 0
    while k < days:
        d += dt.timedelta(days=1)
        if DAYS3[d.weekday()] not in skip:
            k += 1
    return dt.datetime(d.year, d.month, d.day, DUE_HOUR[0], DUE_HOUR[1])


def windows(con):
    """order.deliver_window '15:00-18:00,-11:00' -> [(minute from, minute to)]; an empty side is the day's edge."""
    out = []
    for part in str(setting(con, "order.deliver_window") or "").split(","):
        m = re.match(r"^\s*(\d{1,2}:\d\d)?\s*-\s*(\d{1,2}:\d\d)?\s*$", part)
        if not m:
            continue
        a = m.group(1) or "00:00"
        b = m.group(2) or "24:00"
        out.append((int(a.split(":")[0]) * 60 + int(a.split(":")[1]), int(b.split(":")[0]) * 60 + int(b.split(":")[1])))
    return out


def outside(con, t, wins=None):
    """True when the moment t falls outside every delivery window (no window set: never outside)."""
    if t is None:
        return False
    wins = windows(con) if wins is None else wins
    if not wins:
        return False
    m = t.hour * 60 + t.minute
    return not any(a <= m <= b for a, b in wins)


def who_name(s):
    """Every created_by / sent_by / received_by shape -> a name: 'Alisha (Reception)' / 'alisha' -> 'Alisha'; 'Darpan (Marg sheet, on paper)' ->
    'Darpan'; 'shavez (WhatsApp)' -> 'Shavez'; 'reception-phone' -> 'reception phone'; 'marg' -> 'Marg'; 'bill scan B-0161' kept."""
    t = str(s or "").strip()
    if not t:
        return ""
    if t.lower().startswith("bill scan"):
        return t
    if t.lower() == "marg":
        return "Marg"
    if t.lower() == "reception-phone":
        return "reception phone"
    t = re.sub(r"\s*\((WhatsApp[^)]*|Reception|Marg sheet[^)]*)\)\s*", " ", t, flags=re.I).strip()
    return t[:1].upper() + t[1:] if t else ""


def is_person(s):
    t = str(s or "").strip().lower()
    return bool(t) and t != "marg" and not t.startswith("bill scan")


def short_name(v):
    try:
        import order_rules                                    # noqa: PLC0415
        return order_rules._short(v)
    except Exception:                                         # noqa: BLE001
        return str(v or "").split(" ")[0].title()


# ------------------------------------------------------------------ the light half (finance.db only)
def _ensure_carry(con):
    try:
        con.execute(CARRY_DDL)
    except sqlite3.Error:
        pass


def _orders(con, since_d):
    return [dict(r) for r in con.execute("SELECT * FROM purchase_order WHERE status IN ('sent','received') AND substr(created_at,1,10)>=? "
                                         "ORDER BY created_at, id", (since_d,))]


def light_all(con, now, oids=None, since_d=None):
    """[order state] of every order sent or received since order.track_since (or of the ids given), oldest first. finance.db only; writes nothing."""
    con.row_factory = sqlite3.Row
    pa = _pa()
    since_d = since_d or since(con)
    os_ = _orders(con, since_d) if oids is None else [dict(r) for r in con.execute(
        "SELECT * FROM purchase_order WHERE id IN (%s) ORDER BY created_at, id" % ",".join("?" * len(oids)), list(oids))] if oids else []
    if not os_:
        return []
    ids = [o["id"] for o in os_]
    q = ",".join("?" * len(ids))
    lines = {}
    for l in con.execute("SELECT * FROM purchase_order_line WHERE order_id IN (%s) ORDER BY id" % q, ids):
        lines.setdefault(l["order_id"], []).append(dict(l))
    ties = {}
    tie_by_scan = {}
    for t in con.execute("SELECT order_id, asset_bill_id, stamp, scan_at, arrived, how FROM order_scan_tie"):
        tie_by_scan[int(t[1])] = dict(order_id=t[0], scan=int(t[1]), stamp=t[2] or "", scan_at=t[3] or "")
        ties[t[0]] = dict(scan=int(t[1]), stamp=t[2] or "", scan_at=t[3] or "", arrived=int(t[4] or 0), how=t[5] or "", via="tie")
    links = {}
    try:
        for b in con.execute("SELECT b.supplier_norm, b.bill_no, k.asset_bill_id FROM purchase_bill b JOIN purchase_scan_link k ON k.bill_id=b.id"):
            links.setdefault((b[0], str(b[1] or "")), []).append(int(b[2]))
    except sqlite3.Error:
        pass
    msgs = {}
    try:
        for m in con.execute("SELECT ref, status, sent_at, handed_at FROM supplier_msg WHERE kind='order' AND CAST(ref AS TEXT) IN (%s) ORDER BY id" % q,
                             [str(i) for i in ids]):
            msgs[int(m[0])] = dict(status=m[1], sent_at=m[2] or "", handed_at=m[3] or "")
    except sqlite3.Error:
        pass
    others = {}                                                # (bill no, item) -> the orders whose line Marg credited with it
    try:
        for r in con.execute("SELECT l.order_id, l.item, l.billed_bill_no, o.supplier_norm FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE COALESCE(l.billed_bill_no,'')<>''"):
            others.setdefault((r[3], str(r[2]), r[1]), set()).add(int(r[0]))
    except sqlite3.Error:
        pass
    days, skip, wins = deliver_days(con), skip_days(con), windows(con)
    out = []
    for o in os_:
        out.append(_one(con, o, lines.get(o["id"], []), ties.get(o["id"]), tie_by_scan, links, msgs.get(o["id"]), others, now, days, skip, wins, pa))
    return out


def order_state_light(con, oid, now):
    r = light_all(con, now, oids=[int(oid)])
    return r[0] if r else None


def _qw(con, n, pack_size, item):
    """A quantity through qty_words (strips + tabs for strip items; pcs / bottles otherwise) -- never 'units'."""
    try:
        qw = _os().whole_units(con)
        ps = int(pack_size or 1)
        if qw is None:
            return "%d" % int(n)
        return qw.words(int(n) * (ps if ps > 1 else 1), pack=ps, name=item)
    except Exception:                                         # noqa: BLE001
        return "%d" % int(n)


def _one(con, o, lines, tie, tie_by_scan, links, msg, others, now, days, skip, wins, pa):
    sn = o.get("supplier_norm") or pa.supplier_key(o["vendor"])
    created = _dtm(o["created_at"])
    billed = [l for l in lines if l.get("billed_qty") is not None and str(l.get("billed_bill_no") or "").strip()]
    in_marg = bool(billed)

    def tapped(l):
        return (l.get("supplied") is not None or int(l.get("missing") or 0) == 1) and str(l.get("arrived_by") or "") != "marg"
    any_tap = any(tapped(l) for l in lines)
    # -- arrival: tap, scan (tie or a linked Marg bill), Marg
    taps = [_dtm(l.get("arrived_at")) for l in lines if tapped(l) and l.get("arrived_at")]
    if is_person(o.get("received_by")) and o.get("received_at"):
        taps.append(_dtm(o["received_at"]))
    taps = [t for t in taps if t]
    tap_at = min(taps) if taps else None
    scans = []
    if tie:
        scans.append(dict(tie))
    for l in billed:
        for sid in links.get((sn, str(l["billed_bill_no"])), []):
            if not any(x["scan"] == sid for x in scans):
                t = tie_by_scan.get(sid) or {}
                scans.append(dict(scan=sid, stamp=t.get("stamp") or "", scan_at=t.get("scan_at") or "", via="bill", bill=str(l["billed_bill_no"])))
    scan_at = min([_dtm(x["scan_at"]) for x in scans if _dtm(x.get("scan_at"))] or [None])
    det = min([_dtm(l.get("detected_at")) for l in billed if _dtm(l.get("detected_at"))] or [None])
    arrived = bool(any_tap or tap_at or scans or in_marg)
    cand = [(t, p, k) for t, p, k in ((tap_at, 0, "tap"), (scan_at, 1, "scan")) if t]   # the same minute: the tap (a scan follows the goods)
    if cand:
        arrived_at, _p, how = min(cand)
    elif scans:
        arrived_at, how = None, "scan"
    elif det:
        arrived_at, how = det, "marg"
    else:
        arrived_at, how = None, ""
    # -- each line
    L = []
    for l in lines:
        packs = int(l.get("packs") or 0)
        ps = int(l.get("pack_size") or 1)
        x = dict(id=l["id"], item=l["item"], packs=packs, pack_size=ps, state="", came=0, short=0, how="", reason="", notes=[],
                 bill=str(l.get("billed_bill_no") or ""))
        if l in billed:
            q = int(l["billed_qty"])
            x.update(came=q, how="marg")
            if q < packs:
                x.update(state="short", short=packs - q, reason="marg_short")
            else:
                x["state"] = "came"
            if tapped(l) and int(l.get("missing") or 0):
                x["notes"].append(("tapped_no", (_qw(con, q, ps, l["item"]),)))
            elif tapped(l) and l.get("supplied") is not None and int(l["supplied"]) < packs:
                x["notes"].append(("tapped_kam", (_qw(con, int(l["supplied"]), ps, l["item"]), _qw(con, q, ps, l["item"]))))
            two = sorted((others.get((sn, x["bill"], l["item"])) or set()) - {o["id"]})
            if two:
                x["notes"].append(("two_orders", (x["bill"], ", ".join(str(i) for i in two))))
        elif in_marg:
            x.update(state="short", short=packs, how="marg", reason=("tapped_missing" if tapped(l) and int(l.get("missing") or 0) else "marg_short"))
        elif tapped(l):
            x["how"] = "tap"
            if int(l.get("missing") or 0):
                x.update(state="short", short=packs, reason="tapped_missing")
            elif int(l.get("supplied") or 0) >= packs:
                x.update(state="came", came=int(l["supplied"]))
            else:
                x.update(state="part", came=int(l.get("supplied") or 0), short=packs - int(l.get("supplied") or 0))
        else:
            x["state"] = "open" if (any_tap or not arrived) else "awaiting"
        x["qty_text"] = _qw(con, packs, ps, l["item"])
        x["short_text"] = _qw(con, x["short"], ps, l["item"]) if x["short"] else ""
        L.append(x)
    due = due_at(con, o["created_at"], days, skip)
    open_ = [x for x in L if x["state"] in ("open", "part")]
    late = bool(due and now > due and open_)
    shorts = [x for x in L if x["state"] == "short"]
    came = [x for x in L if x["state"] == "came"]
    if not arrived:
        key = "not_arrived"
    elif open_:
        key = "part"
    elif not in_marg and len(shorts) < len(L):
        key = "awaiting"                                      # arrived (scan or tap), not in Marg yet
    elif shorts:
        key = "short"
    else:
        key = "complete"                                      # in Marg, every line came
    m = msg or {}
    return dict(id=o["id"], vendor=o["vendor"], sn=sn, created_at=o["created_at"], created=created, day=str(o["created_at"])[:10],
                via=o.get("order_via") or "", by=who_name(o.get("created_by")), sent_by=who_name(o.get("sent_by")), sent_at=m.get("sent_at") or "",
                msg_status=m.get("status") or "", status=o.get("status"), ext_ref=o.get("ext_ref") or "",
                arrived=arrived, arrived_at=arrived_at, arrived_how=how, tap_at=tap_at, scans=scans, scan_at=scan_at, in_marg=in_marg,
                detected_at=det, bills=sorted({x["bill"] for x in L if x["bill"]}), lines=L, n=len(L), came=len(came), open=len(open_),
                short=len(shorts), due_at=due, late=late, part=(key == "part"), key=key,
                outside=(tap_at.strftime("%H:%M") if (tap_at and outside(con, tap_at, wins)) else ""),
                complete=(key == "complete"), received_by=o.get("received_by") or "")


def late_orders(con, now, rows=None):
    return [s for s in (rows if rows is not None else light_all(con, now)) if s["late"]]


def late_count(con, now):
    return len(late_orders(con, now))


def awaited(con, now, rows=None):
    """The Maal aaya list: orders not arrived and not late (the call row has the late ones)."""
    return [s for s in (rows if rows is not None else light_all(con, now)) if not s["arrived"] and not s["late"]]


# ------------------------------------------------------------------ the carry (section 3.4): one keyed, idempotent step
def _marg_items(con):
    """{supplier_norm: {norm(item)}} of Marg's newest open order (the lines its newest export prints)."""
    pa = _pa()
    out = {}
    try:
        for l in _os().marg_lines(con):
            out.setdefault(l["supplier_norm"], set()).add(pa.norm(l["item"]))
    except Exception:                                         # noqa: BLE001
        pass
    return out


def _ordered_since(con, sn, item, at, exclude=None):
    """An order of the supplier (draft, sent or received) made at or after `at` carries the item -> its (id, created_at), else None."""
    pa = _pa()
    for r in con.execute("SELECT o.id, o.created_at, l.item FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id "
                         "WHERE o.supplier_norm=? AND o.status IN ('draft','sent','received') AND o.created_at>=? ORDER BY o.created_at, o.id", (sn, at)):
        if exclude and r[0] == exclude:
            continue
        if pa.norm(r[2]) == pa.norm(item):
            return r[0], r[1]
    return None


def carry_pass(con, now, who="carry"):
    """Every SHORT line of an order since order.track_since (Marg's bill without it or below it, or tapped Nahi mila) gets ONE order_carry row
    (keyed by its line) -- unless Marg's newest open order already carries the item for that dealer, or a later order of that dealer already
    carried it. Then each open carry closes: an order of the dealer carrying the item made at or after the carry (done_order_id), Marg's newest
    open order carrying it (dropped_by 'marg_order'), or the line no longer short (dropped_by 'came'). Never written from a scan.
    Returns dict(written, done, dropped)."""
    _ensure_carry(con)
    pa = _pa()
    rows = light_all(con, now)
    marg = _marg_items(con)
    t = now.replace(microsecond=0).isoformat()
    have = {r[0]: r for r in con.execute("SELECT from_line_id, id FROM order_carry")}
    short_now = {}
    written = done = dropped = 0
    for s in rows:
        for x in s["lines"]:
            if x["state"] != "short":
                continue
            short_now[x["id"]] = (s, x)
            if x["id"] in have:
                continue
            if pa.norm(x["item"]) in marg.get(s["sn"], set()):
                continue                                      # still on Marg's open order: not carried twice
            if _ordered_since(con, s["sn"], x["item"], s["created_at"], exclude=s["id"]):
                continue                                      # a later order of the dealer already carried it
            cur = con.execute("INSERT OR IGNORE INTO order_carry (vendor, supplier_norm, item, from_order_id, from_line_id, qty, pack_size, reason, at) "
                              "VALUES (?,?,?,?,?,?,?,?,?)", (s["vendor"], s["sn"], x["item"], s["id"], x["id"], int(x["short"]), int(x["pack_size"]),
                                                            x["reason"] or "marg_short", t))
            if cur.rowcount:
                written += 1
                _os().audit(con, who, "s619_carry", s["id"], dict(item=x["item"], line=x["id"], qty=int(x["short"]), reason=x["reason"], kit=KIT))
    for c in [dict(r) for r in con.execute("SELECT * FROM order_carry WHERE done_at IS NULL AND dropped_at IS NULL")]:
        hit = _ordered_since(con, c["supplier_norm"], c["item"], c["at"], exclude=c["from_order_id"])
        if hit:
            con.execute("UPDATE order_carry SET done_order_id=?, done_at=? WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (hit[0], t, c["id"]))
            done += 1
            continue
        why = None
        if pa.norm(c["item"]) in marg.get(c["supplier_norm"], set()):
            why = "marg_order"
        elif c["from_line_id"] not in short_now:
            r = con.execute("SELECT o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.id=?", (c["from_line_id"],)).fetchone()
            if r and str(r[0])[:10] >= since(con):
                why = "came"
        if why:
            con.execute("UPDATE order_carry SET dropped_at=?, dropped_by=? WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (t, why, c["id"]))
            dropped += 1
    if written or done or dropped:
        con.commit()
    return dict(written=written, done=done, dropped=dropped)


def carries_plan(con, now):
    """What carry_pass would write now (read only): [(order id, vendor, item, short text, reason)] -- the install's live facts."""
    _ensure_carry(con)
    pa = _pa()
    marg = _marg_items(con)
    have = {r[0] for r in con.execute("SELECT from_line_id FROM order_carry")}
    out = []
    for s in light_all(con, now):
        for x in s["lines"]:
            if x["state"] != "short" or x["id"] in have:
                continue
            if pa.norm(x["item"]) in marg.get(s["sn"], set()) or _ordered_since(con, s["sn"], x["item"], s["created_at"], exclude=s["id"]):
                continue
            out.append((s["id"], s["vendor"], x["item"], x["short_text"], x["reason"]))
    return out


def open_carries(con, sn=None):
    _ensure_carry(con)
    q = "SELECT c.*, o.created_at AS from_at FROM order_carry c LEFT JOIN purchase_order o ON o.id=c.from_order_id WHERE c.done_at IS NULL AND c.dropped_at IS NULL"
    a = ()
    if sn:
        q += " AND c.supplier_norm=?"
        a = (sn,)
    return [dict(r) for r in con.execute(q + " ORDER BY c.id", a)]


def carry_word(c, en=False):
    return ("back from the order of %s" if en else "pichhle order se baaki (%s)") % ddmm(c.get("from_at") or c.get("at"))


def short_words(con, s, x, en, marg=None, carries=None):
    """What a SHORT line says: back on the next order by itself / already on Marg's order / re-ordered dd-mm / removed."""
    pa = _pa()
    c = (carries or {}).get(x["id"])
    if c is None:
        r = con.execute("SELECT * FROM order_carry WHERE from_line_id=?", (x["id"],)).fetchone() if _has(con, "order_carry") else None
        c = dict(r) if r else None
    if c and c.get("done_order_id"):
        return ("re-ordered on %s (order %s)" if en else "%s ko dobara order hua (order %s)") % (ddmm(c.get("done_at")), c["done_order_id"])
    if c and c.get("dropped_at"):
        db = str(c.get("dropped_by") or "")
        if db == "marg_order":
            return "already on Marg's order" if en else "Marg ke order mein pehle se hai"
        if db == "came":
            return "came after all" if en else "baad mein aa gaya"
        return ("removed by %s" if en else "%s ne hataya") % who_name(db)
    if c:
        return "back on the next order by itself" if en else "agle order mein khud jud jayega"
    marg = _marg_items(con) if marg is None else marg
    if pa.norm(x["item"]) in marg.get(s["sn"], set()):
        return "already on Marg's order" if en else "Marg ke order mein pehle se hai"
    return "ordered again since" if en else "dobara order ho chuka"


def _has(con, t):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone() is not None
    except sqlite3.Error:
        return False


# ------------------------------------------------------------------ Darpan's one line (Kal ka hisaab) and his order tab
def last_order_day(con, iso):
    r = con.execute("SELECT MAX(substr(created_at,1,10)) FROM purchase_order WHERE status IN ('sent','received') AND substr(created_at,1,10)<=? "
                    "AND substr(created_at,1,10)>=?", (str(iso)[:10], since(con))).fetchone()
    return r[0] if r and r[0] else ""


def darpan_line(con, iso, now):
    """One read-only line for the last order day on or before the viewed date, dated (never 'Kal'). dict(ok, day, text, lines, state)."""
    d = last_order_day(con, iso)
    if not d:
        return dict(ok=True, day="", text="", lines=[])
    rows = [s for s in light_all(con, now, since_d=d) if s["day"] == d]
    by = {}
    for s in rows:
        by.setdefault(s["sn"], []).append(s)
    came, waiting, late, due = [], [], [], []
    nshort = 0
    for sn, ss in by.items():
        nshort += sum(s["short"] for s in ss)
        if any(s["late"] for s in ss):
            late.append(short_name(ss[0]["vendor"]))
        elif any(s["key"] in ("not_arrived", "part") for s in ss):
            waiting.append(sn)
            due += [s["due_at"] for s in ss if s["due_at"]]
        else:
            came.append(sn)
    D = ddmm(d)
    lines = []
    if late:
        lines.append("%s ke order: %d supplier ka maal der se — %s. Reception call kar raha hai." % (D, len(late), ", ".join(late)))
    elif waiting and came:
        lines.append("%s ke order: %d supplier ka maal aa gaya, %d ka aana baaki — %s shaam tak" % (D, len(came), len(waiting), ddmm(min(due).isoformat()) if due else D))
    elif waiting:
        lines.append("%s ke order: %d supplier ka maal aana baaki — %s shaam tak" % (D, len(waiting), ddmm(min(due).isoformat()) if due else D))
    elif not nshort:
        lines.append("%s ke order: saara maal aa gaya ✓" % D)
    if nshort:
        lines.append("%s ke order: %d dawa nahi aayi — agle order mein khud jud gayi." % (D, nshort))
    state = "late" if late else ("waiting" if waiting else ("short" if nshort else "all"))
    return dict(ok=True, day=d, text=" ".join(lines), lines=lines, state=state)


def yesterday_state(con, oid, now):
    """Darpan's order tab: 'arrived' when the light half says the goods came (any way), else 'ordered'."""
    s = order_state_light(con, oid, now)
    return "arrived" if (s and s["arrived"]) else "ordered"


# ------------------------------------------------------------------ the owner's Needs-you line (the one the other two voices do not say)
def owner_line(con, now):
    n = late_count(con, now)
    m = len(open_carries(con))
    if not n and not m:
        return None
    return dict(cls="warn", target="porders", text="Orders: %d late, %d medicine%s came short (back on the next order) — the order list"
                % (n, m, "" if m == 1 else "s"))


# ------------------------------------------------------------------ the scan half (assets.db READ ONLY): set-aside heads, other dealers, soft notes
def _num_runs(s):
    return sorted(re.findall(r"\d+(?:\.\d+)?", str(s or "")))


def _nm(s):
    return re.sub(r"[^A-Z0-9]+", "", str(s or "").upper())


def _letters(s):
    return re.sub(r"[^A-Z]+", "", str(s or "").upper())


def name_score(form, read):
    """1.0 an exact name (punctuation and spacing apart); else the strict fuzzy rule: the numbers in the names agree (never a sibling size) and
    the letters are at least 0.8 alike (difflib); else 0. Quantities are never compared."""
    a, b = _nm(form), _nm(read)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if _num_runs(form) != _num_runs(read):
        return 0.0
    la, lb = _letters(form), _letters(read)
    if not la or not lb:
        return 0.0
    if lb.startswith(la) or la.startswith(lb):
        r = min(len(la), len(lb)) / float(max(len(la), len(lb)))
        if r >= 0.6:
            return 0.9
    r = difflib.SequenceMatcher(None, la, lb).ratio()
    return r if r >= 0.8 else 0.0


def forms_of(con, sn, item, ctx=None):
    """The item's printed forms (stock_figure.printed_forms) and the scan spellings learnt for it from that dealer (s454_item_name)."""
    out = [item]
    try:
        import stock_figure as SF                             # noqa: PLC0415
        out = list(SF.printed_forms(con, item, ctx))
    except Exception:                                         # noqa: BLE001
        pass
    try:
        out += [r[0] for r in con.execute("SELECT scan_name FROM s454_item_name WHERE supplier_norm=? AND marg_item=?", (sn, item)) if r[0]]
    except sqlite3.Error:
        pass
    seen, res = set(), []
    for f in out:
        if _nm(f) and _nm(f) not in seen:
            seen.add(_nm(f))
            res.append(f)
    return res


def match_lines(con, sn, items, reads, ctx=None):
    """One-to-one: {item: (read name, stamp)} for the order items found among the scans' read names [(name, stamp)]."""
    pairs = []
    for it in items:
        fs = forms_of(con, sn, it, ctx)
        for j, (rn, st) in enumerate(reads):
            sc = max(name_score(f, rn) for f in fs)
            if sc > 0:
                pairs.append((-sc, it, j))
    pairs.sort()
    used_i, used_j, out = set(), set(), {}
    for sc, it, j in pairs:
        if it in used_i or j in used_j:
            continue
        used_i.add(it)
        used_j.add(j)
        out[it] = reads[j]
    return out


class Ctx(object):
    """What the scan half reads once per page: assets.db's pharmacy scans, their readings, the scans to redo, scan_register's supplier test."""

    def __init__(self, con):
        OS = _os()
        self.ok = False
        self.scans, self.read, self.bad, self.sr_cx = {}, {}, set(), None
        self.sf = None
        acon = OS._assets()
        if acon is None:
            return
        try:
            cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
            sel = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "total_amount", "submitted_at", "created_at", "ocr_status", "dup_of",
                               "lane", "status", "kind", "page_of", "rescan_of", "source_stored") if c in cols]
            for r in acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND substr(created_at,1,10)>=?" % ", ".join(sel),
                                  ((dt.date.fromisoformat(since(con)) - dt.timedelta(days=3)).isoformat(),)):
                d = dict(r)
                d["at"] = OS.scan_moment(d)
                self.scans[int(d["id"])] = d
            try:
                for r in acon.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1 ORDER BY at"):
                    try:
                        self.read[int(r[0])] = json.loads(r[1]) if r[1] else None
                    except ValueError:
                        pass
            except sqlite3.Error:
                pass
            self.ok = True
        except sqlite3.Error:
            self.ok = False
        finally:
            acon.close()
        try:
            import porders_s454 as P4                         # noqa: PLC0415 -- S618's reader: the scans to redo (one list)
            x = P4.rescan_list(con)
            self.bad = {int(r["scan"]) for r in x.get("redo") or []} | {int(a["scan"]) for a in x.get("asks") or []}
            self.redo = x
        except Exception:                                     # noqa: BLE001
            self.redo = dict(asks=[], redo=[], ok=False)
        try:
            import scan_register as SR                        # noqa: PLC0415
            self.sr = SR
            self.sr_cx = SR.Ctx(con)
        except Exception:                                     # noqa: BLE001
            self.sr = None
        try:
            import stock_figure as SF                         # noqa: PLC0415
            self.sf = SF._ctx(con, None, None)
        except Exception:                                     # noqa: BLE001
            self.sf = None

    def head(self, sid):
        """A set-aside scan's head (dup_of), else the scan itself."""
        s = self.scans.get(int(sid)) or {}
        return int(s["dup_of"]) if s.get("dup_of") else int(sid)

    def reading_vendor(self, sid):
        return ((self.read.get(int(sid)) or {}).get("vendor") or "")

    def other_dealer(self, sid, supplier):
        """The paper's own vendor (its reading) differs from the dealer it was saved under / tied to -> that vendor, else ''."""
        if self.sr is None or self.sr_cx is None:
            return ""
        rv = self.reading_vendor(sid)
        if not rv:
            return ""
        try:
            return rv if self.sr.supplier(self.sr_cx, rv, supplier) == "differ" else ""
        except Exception:                                     # noqa: BLE001
            return ""

    def names(self, sid):
        return [str(i.get("name") or "") for i in ((self.read.get(int(sid)) or {}).get("items") or []) if isinstance(i, dict) and i.get("name")]

    def usable(self, sid):
        s = self.scans.get(int(sid)) or {}
        return bool(s) and str(s.get("lane") or "pharmacy") == "pharmacy" and str(s.get("status") or "") != "rejected" and not s.get("dup_of") \
            and not s.get("page_of") and int(sid) not in self.bad


def wrong_dealer(con, ctx):
    """The captured pharmacy scans since order.track_since whose paper names another dealer than the one they were saved under."""
    out = []
    for sid, s in sorted(ctx.scans.items()):
        if str(s.get("lane") or "") != "pharmacy" or str(s.get("status") or "") == "rejected" or s.get("dup_of") or s.get("page_of"):
            continue
        if str(s.get("created_at") or "")[:10] < since(con):
            continue
        ov = ctx.other_dealer(sid, s.get("vendor") or "")
        if ov:
            out.append(dict(scan=sid, stamp=s.get("stamp_no") or "#%d" % sid, saved=s.get("vendor") or "", paper=ov,
                            date=str(s.get("bill_date") or "")[:10] or (s["at"].date().isoformat() if s.get("at") else "")))
    return out


def _supplier_scans(con, ctx, s, nxt):
    """Every usable pharmacy scan of the order's dealer from the order moment until its next order (the resolver of order_sheet)."""
    OS = _os()
    if not hasattr(ctx, "_sup"):
        ctx._sup = OS._resolver(con)
    out = []
    for sid, sc in sorted(ctx.scans.items()):
        if not ctx.usable(sid) or not sc.get("at") or not s["created"]:
            continue
        if sc["at"] < s["created"] or (nxt and sc["at"] >= nxt):
            continue
        try:
            if ctx._sup(sc) != s["sn"]:
                continue
        except Exception:                                     # noqa: BLE001
            continue
        out.append(sid)
    return out


def soft_notes(con, s, ctx, en, nxt=None, lines=None):
    """{line id: (key, text)} for each line not answered by Marg or a tap -- 'not seen on the scanned bill' / 'on bill B-xxxx'. A note only."""
    want = [x for x in (lines if lines is not None else s["lines"]) if x["state"] in ("open", "awaiting", "part")]
    if not want or not ctx.ok:
        return {}
    sids = _supplier_scans(con, ctx, s, nxt)
    if not sids:
        return {}
    reads = [(n, ctx.scans[sid].get("stamp_no") or "#%d" % sid) for sid in sids for n in ctx.names(sid)]
    hit = match_lines(con, s["sn"], [x["item"] for x in want], reads, ctx.sf)
    out = {}
    for x in want:
        if x["item"] in hit:
            out[x["id"]] = ("on", W("soft_on", en, hit[x["item"]][1]))
        else:
            out[x["id"]] = ("no", W("soft_no", en))
    return out


def full_all(con, now, en=True, ctx=None, rows=None):
    """The light half of every tracked order plus the scan half (stamps, moments, heads, other dealers, soft notes). Counts never move."""
    rows = rows if rows is not None else light_all(con, now)
    ctx = ctx or Ctx(con)
    nexts = {}
    by = {}
    for s in rows:
        by.setdefault(s["sn"], []).append(s)
    for sn, ss in by.items():
        ss = sorted(ss, key=lambda z: (z["created_at"], z["id"]))
        for i, s in enumerate(ss):
            nexts[s["id"]] = ss[i + 1]["created"] if i + 1 < len(ss) else None
    for s in rows:
        s["notes"] = []
        for x in s["scans"]:
            sc = ctx.scans.get(int(x["scan"])) or {}
            x["stamp"] = x.get("stamp") or sc.get("stamp_no") or "#%d" % int(x["scan"])
            if not x.get("scan_at") and sc.get("at"):
                x["scan_at"] = sc["at"].isoformat()
            h = ctx.head(x["scan"])
            x["head"] = h
            if h != int(x["scan"]):
                hs = ctx.scans.get(h) or {}
                s["notes"].append(W("set_aside", en, x["stamp"], hs.get("stamp_no") or "#%d" % h))
            ov = ctx.other_dealer(h, s["vendor"])
            x["other"] = ov
            if ov:
                s["notes"].append(W("other_dealer", en, x["stamp"], ov))
        good = [x for x in s["scans"] if not x.get("other")]
        s["scan_ok"] = bool(good)
        s["scan_conflict"] = bool(s["scans"]) and not good
        sat = [_dtm(x["scan_at"]) for x in good if _dtm(x.get("scan_at"))]
        s["scan_at"] = min(sat) if sat else s.get("scan_at")
        s["thumb"] = ("/scanapp/bills/%d/thumb" % good[0]["head"]) if good else ""
        s["file"] = ("/scanapp/bills/%d/file" % good[0]["head"]) if good else ""
        s["soft"] = soft_notes(con, s, ctx, en, nexts.get(s["id"])) if s["arrived"] else {}
    return rows


def order_state(con, oid, now, ctx=None, en=True):
    s = order_state_light(con, oid, now)
    if s is None:
        return None
    return full_all(con, now, en=en, ctx=ctx, rows=[s])[0]


def tiles(rows, redo_n=0):
    """The track page's tiles -- from the light half only (a note never moves a count)."""
    return dict(orders=len(rows), not_arrived=sum(1 for s in rows if not s["arrived"]), late=sum(1 for s in rows if s["late"]),
                short=sum(1 for s in rows if s["short"]), not_in_marg=sum(1 for s in rows if s["key"] == "awaiting"), redo=int(redo_n or 0),
                part=sum(1 for s in rows if s["part"]))


def dots(s):
    """The five steps' states: done | wait | late | short | conflict."""
    arr = "done" if s["arrived"] else ("late" if s["late"] else "wait")
    if s.get("scan_conflict") and s["arrived_how"] == "scan" and not s["in_marg"] and not s["tap_at"]:
        arr = "conflict"
    bill = "conflict" if s.get("scan_conflict") else ("done" if s["scans"] else "wait")
    marg = "done" if s["in_marg"] else "wait"
    if s["short"]:
        allc = "short"
    elif s["complete"]:
        allc = "done"
    elif s["late"]:
        allc = "late"
    else:
        allc = "wait"
    return [("Ordered", "done"), ("Arrived", arr), ("Bill scanned", bill), ("In Marg", marg), ("All lines came", allc)]


def table_row(s):
    """One line of the walk's / install's section 4.1 table (no number, no phone)."""
    sh = ", ".join("%s %s" % (x["item"], x["short_text"]) for x in s["lines"] if x["state"] == "short")
    op = ", ".join(x["item"] for x in s["lines"] if x["state"] in ("open", "part"))
    return ("%3d %-22s %s %-9s arr=%-5s(%s%s) scan=%s marg=%s lines %d came %d short %d open %d due %s%s%s%s" % (
        s["id"], str(s["vendor"])[:22], ddmm(s["created_at"]), s["key"], "yes" if s["arrived"] else "no", s["arrived_how"] or "-",
        (" " + s["arrived_at"].strftime("%d-%m %H:%M")) if s["arrived_at"] else "", "+".join(x.get("stamp") or "#%s" % x["scan"] for x in s["scans"]) or "-",
        "yes" if s["in_marg"] else "no", s["n"], s["came"], s["short"], s["open"], s["due_at"].strftime("%d-%m %H:%M") if s["due_at"] else "-",
        " LATE" if s["late"] else "", (" short: " + sh) if sh else "", (" open: " + op) if op else ""))
