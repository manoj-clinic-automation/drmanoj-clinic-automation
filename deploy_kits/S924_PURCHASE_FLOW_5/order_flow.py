#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_flow.py  ·  v1.0  ·  kit S920_PURCHASE_FLOW_1  ·  Session 499 (Sanjeevni)  ·  D1030 (the owner's mock-up v4 FINAL, 21-Nov 19:20 IST)
#
#  ONE READER FOR THE PURCHASE FLOW -- every page (his Purchase orders, reception, Darpan's tab, the Purchase bills page) groups the
#  orders through groups() so "Arrived" is the same list, the same count, everywhere (his word, 21-Nov 19:01: "11, not 5").
#
#    late  -- not arrived, past its due day (order_track: the order's day + order.deliver_days, Sundays not counted, 18:00)
#    way   -- not arrived, inside the due day
#    arr   -- arrived (a tap, a scan or the bill), not yet in Marg -- plus each scanned bill of the month that came with no order
#    gap   -- in Marg, a medicine still missing (short, came less, or out of stock / substitute waiting for his word)
#    done  -- in Marg and every line came or was settled (ordered again, closed by him, his word on out of stock / substitute)
#    team  -- out of stock (reception's / Darpan's 'Ab nahi milta', order_s778_na) and substitutes (order_flow_mark 'sub'):
#             one list, his buttons; Darpan and reception read it.
#
#  It builds on order_track.light_all (the five steps, unchanged) and order_s778 (the red box, 'Ab nahi milta', the doctor's answer).
#  WRITES only through act(): its own table order_flow_mark, and the doors order_s778 already has (again / na / na_answer) and
#  order_carry's dropped_at (his 'Close: never came'). It never writes Marg, purchase_line, purchase_bill or stock.
#  Every name it prints is the item as ordered; no phone number is read here beyond the last four the cards already show.
#
#  v1.1 (21-Nov-2026, kit S921_PURCHASE_FLOW_2, Session 500 -- D1030 / D1034, mock-up v4 FINAL tab "Reception"):
#    rec_body()  -- reception's grouped strip (Roman Hindi), drawn from groups() -- never a second grouping: Late (Call kiya -- aa raha
#                   hai · Out of stock · Nahi bhejenge), Raste mein (Maal aa gaya = the S454 arrival screen), Aaya (Bill scan karo =
#                   the scan app's intake; a short line: Dobara order karo · Out of stock · Substitute aaya), Purane order, the team list
#                   (read only). The dealer's call number is on the row (reception's own call screen).
#    rec_act()   -- reception's doors (POST /finance/porders/api/flow/rec, the senders and the owner): again / oos through act(); sub
#                   writes order_flow_mark kind 'sub'; called / refused write the new table order_flow_rec; oosrow = Out of stock on
#                   every line of a late order that did not come. His late row reads reception's word.
#    /finance/porders/flow?rec=1 -- his preview of the strip as reception's home carries it.
#    F-1551      -- his team list prints the quantity in English (qty_en: the Hindi unit words of qty_words read back).
#    A substitute with no name reads "<item> → substitute".
#  v1.2 (21-Nov-2026, kit S922_PURCHASE_FLOW_3, Session 500): her strip laid out for a phone (the owner, 21:00: "optimise it for mobile
#    screen also") -- a small scan, a line's buttons on their own row under it, the team list as short blocks; dar_view() -- Darpan's
#    order tab: what each dealer has still to send (late / arrived short / old / on the way) and the team list, read only.
#  v1.3 (21-Nov-2026, kit S923_PURCHASE_FLOW_4): two doors for his Purchase bills page (provisional_s781 holds the logic) --
#    POST /finance/porders/api/flow/scan {scan, do: count|aside|undo, why} and /api/flow/scanset {rs, pct} (the round-off allowance).
#  v1.4 (21-Nov-2026, kit S924_PURCHASE_FLOW_5): his Hub's Needs-you speaks of the purchase flow in ONE line from groups() --
#    "Purchase orders: N late · M medicines still missing · K out of stock / substitute for your word" -> his grouped page. It takes
#    the place of order_track.owner_line (its own late rule said "2 late" where the orders page said 0) and of order_s778's line per
#    out-of-stock tap (eleven lines on 21-Nov); the wrong-dealer note stays. Mounted by init; any fault: the old lines.
# =============================================================================
import datetime as dt
import html as _html
import re
import sqlite3

VERSION = "1.4"
KIT = "S924_PURCHASE_FLOW_5"
P = "/finance/porders"
WAIT_DAYS = 7                                                     # 'Wait — order next week'
DDL = ("CREATE TABLE IF NOT EXISTS order_flow_mark (id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN "
       "('closed','chase','sub','sub_ok','sub_return','wait','other')), order_id INTEGER, line_id INTEGER, na_id INTEGER, sub_id INTEGER, "
       "item TEXT, vendor TEXT, sub_item TEXT, until TEXT, to_sn TEXT, by TEXT NOT NULL, at TEXT NOT NULL, undone_at TEXT)",
       "CREATE TABLE IF NOT EXISTS order_flow_rec (id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN ('called','refused')), "   # S921
       "order_id INTEGER NOT NULL, by TEXT NOT NULL, at TEXT NOT NULL, undone_at TEXT)")
GROUPS = ("late", "way", "arr", "gap", "done")


def _ot():
    import order_track                                            # noqa: PLC0415 -- beside this file
    return order_track


def _s7():
    import order_s778                                             # noqa: PLC0415
    return order_s778


def _os():
    import order_sheet                                            # noqa: PLC0415
    return order_sheet


def esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def ensure(con):
    for d in DDL:
        try:
            con.execute(d)
        except sqlite3.Error:
            pass


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _norm(item):
    try:
        return _s7().norm(item)
    except Exception:                                             # noqa: BLE001
        return re.sub(r"[^A-Z0-9]+", "", str(item or "").upper())


def _forms(con, item, sn=None):
    try:
        return set(_s7().forms(con, item, sn))
    except Exception:                                             # noqa: BLE001
        return {_norm(item)}


def marks(con):
    ensure(con)
    return [dict(r) for r in con.execute("SELECT * FROM order_flow_mark WHERE undone_at IS NULL ORDER BY id")]


def _carries_by_line(con):
    try:
        _ot()._ensure_carry(con)
        return {int(r["from_line_id"]): dict(r) for r in con.execute("SELECT * FROM order_carry")}
    except sqlite3.Error:
        return {}


def _na_all(con):
    try:
        _s7().ensure(con)
        return [dict(r) for r in con.execute("SELECT * FROM order_s778_na ORDER BY id")]
    except sqlite3.Error:
        return []


def _na_for(na, fs, sn, day):
    """The 'Ab nahi milta' row that answers this line: the same medicine, tapped on or after the order's day (newest)."""
    hit = None
    for r in na:
        if r["item_norm"] in fs and str(r["at"])[:10] >= str(day)[:10]:
            hit = r
    return hit


def _settle(con, s, x, carry, na, mk_line, ordered_since):
    """A SHORT / PART line's state for the flow: (state, how). state in short | part | oos | sub | settled."""
    m = mk_line.get(x["id"]) or {}
    if m.get("closed"):
        return "settled", "closed by you"
    if m.get("sub_ok"):
        return "settled", "substitute OK"
    if m.get("sub_return"):
        return "settled", "substitute to go back"
    if m.get("sub"):
        return "sub", "substitute came: %s" % (m["sub"].get("sub_item") or "")
    if ordered_since(s["sn"], x["item"], s["created_at"], s["id"]):
        return "settled", "ordered again"                       # a later order of the dealer carries it: the newest line answers
    n = _na_for(na, _forms(con, x["item"], s["sn"]), s["sn"], s["day"])
    if n is not None:
        if n["status"] == "asked" and not n.get("cleared_at"):
            return "oos", "out of stock, tapped %s" % ddmm(n["at"])
        if n["status"] == "came" or n.get("cleared_at"):
            return "settled", "came later on a bill"
        return "settled", ("stopped by you" if n["status"] == "stop" else "your word: keep ordering")
    if carry:
        if carry.get("done_order_id"):
            return "settled", "ordered again %s" % ddmm(carry.get("done_at"))
        db = str(carry.get("dropped_by") or "")
        if carry.get("dropped_at"):
            if db == "came":
                return "settled", "came later"
            if db == "marg_order":
                return "settled", "on Marg's order"
            if db == "s778_moved":
                return "settled", "moved to another dealer"
            if db == "owner_closed":
                return "settled", "closed by you"
            if db == "s778_na":
                return "oos", "out of stock"
            return "settled", "removed"
    return ("part" if int(x.get("came") or 0) > 0 else "short"), ""


def ddmm(iso):
    try:
        return _os().ddmm(iso)
    except Exception:                                             # noqa: BLE001
        s = str(iso or "")[:10]
        return "%s-%s" % (s[8:10], s[5:7]) if len(s) == 10 else s


def groups(con, now, ctx=None, month=None, with_bills=True):
    """The one reading of the purchase flow. dict(late, way, arr, gap, done, team, counts, orderless). Writes nothing."""
    con.row_factory = sqlite3.Row
    ensure(con)
    OT = _ot()
    rows = OT.light_all(con, now)
    carries = _carries_by_line(con)
    na = _na_all(con)
    mk = marks(con)
    recm = rec_marks(con)                                         # S921: reception's word on a late row (Call kiya / Nahi bhejenge)
    mk_line, mk_order = {}, {}
    for m in mk:
        if m.get("line_id"):
            d = mk_line.setdefault(int(m["line_id"]), {})
            d[m["kind"]] = m
        if m.get("order_id") and not m.get("line_id"):
            mk_order.setdefault(int(m["order_id"]), {})[m["kind"]] = m
    memo = {}
    again_rows = {}
    try:
        for r in con.execute("SELECT kind, ref, at FROM order_s778_again WHERE cleared_at IS NULL"):
            again_rows[(str(r[0]), str(r[1]))] = str(r[2] or "")
    except sqlite3.Error:
        pass

    def on_card(oid, lid, carry):
        """An open 'Order again' already given for this line (his, Darpan's or reception's): its day, else ''."""
        a = again_rows.get(("late", "%d:%d" % (int(oid), int(lid))))
        if a is None and carry:
            a = again_rows.get(("carry", str(carry.get("id"))))
        return a or ""

    def ordered_since(sn, item, at, oid):
        k = (sn, item, at, oid)
        if k not in memo:
            try:
                memo[k] = OT._ordered_since(con, sn, item, at, exclude=oid)
            except Exception:                                     # noqa: BLE001
                memo[k] = None
        return memo[k]

    out = {g: [] for g in GROUPS}
    for s in rows:
        om = mk_order.get(s["id"]) or {}
        flines = []
        for x in s["lines"]:
            st, how = x["state"], ""
            oc = on_card(s["id"], x["id"], carries.get(int(x["id"])))
            if st in ("short", "part", "open") and oc and not (mk_line.get(int(x["id"])) or {}).get("closed"):
                st, how = "settled", "ordered again %s" % ddmm(oc)
            elif st in ("short", "part"):
                st, how = _settle(con, s, x, carries.get(int(x["id"])), na, mk_line, ordered_since)
            if x["state"] in ("open", "awaiting") and st != "settled":
                m = mk_line.get(int(x["id"])) or {}
                n = _na_for(na, _forms(con, x["item"], s["sn"]), s["sn"], s["day"]) if (s["late"] or not s["arrived"]) else None
                again = ordered_since(s["sn"], x["item"], s["created_at"], s["id"]) if (s["late"] or not s["arrived"]) else None
                if m.get("closed") or om.get("closed"):
                    st, how = "settled", "closed by you"
                elif again:
                    st, how = "settled", "ordered again %s (order %s)" % (ddmm(again[1]), again[0])
                elif n is not None and n["status"] == "asked" and not n.get("cleared_at"):
                    st, how = "oos", "out of stock, tapped %s" % ddmm(n["at"])
                elif n is not None:
                    st, how = "settled", "your word given"
                else:
                    st = "awaiting" if (x["state"] == "awaiting" or (s["arrived"] and not s["late"])) else "open"
            c = carries.get(int(x["id"]))
            flines.append(dict(id=x["id"], item=x["item"], qty=x.get("qty_text") or "", came=int(x.get("came") or 0), state=st, how=how,
                               short_text=x.get("short_text") or "", carry=(c["id"] if c and not c.get("done_at") and not c.get("dropped_at") else None),
                               packs=x["packs"]))
        unresolved = [l for l in flines if l["state"] in ("short", "part", "open", "awaiting")]
        waiting = [l for l in flines if l["state"] in ("oos", "sub")]
        missing = [l for l in flines if l["state"] in ("short", "part", "oos", "sub")] + \
                  ([l for l in flines if l["state"] == "open"] if (s["late"] and not s["arrived"]) else [])
        if not s["arrived"]:
            g = ("late" if s["late"] else "way") if [l for l in flines if l["state"] in ("open", "awaiting")] else ("gap" if waiting else "done")
        elif not s["in_marg"]:
            g = "arr" if [l for l in flines if l["state"] != "settled"] else "done"     # every line settled by his word / a later order
        else:
            g = "gap" if (unresolved or waiting) else "done"
        out[g].append(dict(id=s["id"], vendor=s["vendor"], sn=s["sn"], day=s["day"], created_at=s["created_at"], via=s.get("via") or "",
                           lines=flines, missing=missing, group=g, late=s["late"], due_at=s["due_at"], arrived_how=s["arrived_how"],
                           arrived_at=s["arrived_at"], in_marg=s["in_marg"], bills=s["bills"], scans=s["scans"],
                           chase=bool(om.get("chase")), rec=recm.get(int(s["id"])), age=(now.date() - dt.date.fromisoformat(s["day"])).days))
    orderless = []
    if with_bills:
        orderless = _orderless(con, now, [r for g in GROUPS for r in out[g]], month)
        for b in orderless:
            out["arr"].append(b)
    out["team"] = team(con, na, mk)
    for g in GROUPS:
        out[g].sort(key=lambda r: (r["day"] or "", r["vendor"] or ""), reverse=(g in ("done", "arr", "way")))
    out["counts"] = dict(late=len(out["late"]), way=len(out["way"]), arr=len(out["arr"]), gap=len(out["gap"]), done=len(out["done"]),
                         team=len(out["team"]), arr_short=sum(1 for r in out["arr"] if r["missing"]),
                         gap_meds=sum(len(r["missing"]) for r in out["gap"]),
                         oldest=max([r["age"] for g in ("late", "way", "arr", "gap") for r in out[g]] or [0]))
    out["orderless"] = orderless
    return out


def _orderless(con, now, open_rows, month=None):
    """The month's scanned pharmacy bills that wait for their Marg bill (provisional_s781's own list -- the Purchase bills page's) and are
    not the bill of an order shown above: a scan tied to an order, or the first scan of the order's dealer after the order (until its next
    order) when the order has none. Each becomes an 'arrived, no order in the system' row. Fail-soft: [] without assets.db."""
    try:
        import provisional_s781 as PV                             # noqa: PLC0415
        month = month or now.strftime("%Y-%m")
        prov = PV.provisional(con, month)
    except Exception:                                             # noqa: BLE001
        return []
    tied = set()
    for r in open_rows:
        for x in r.get("scans") or []:
            tied.add(int(x["scan"]))
    try:
        tied |= {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM order_scan_tie")}
    except sqlite3.Error:
        pass
    need = {}
    for r in open_rows:
        if r["group"] == "arr" and not r.get("scans"):
            need.setdefault(r["sn"], []).append(r)
    out = []
    for x in prov:
        if int(x["id"]) in tied:
            continue
        hit = None
        for r in need.get(x["dealer"], []):
            if str(x.get("day") or "") >= r["day"]:
                hit = r
                break
        if hit is not None:
            hit["scans"] = [dict(scan=int(x["id"]), stamp=x["stamp"], via="dealer")]
            need[x["dealer"]].remove(hit)
            continue
        out.append(dict(id=None, scan=int(x["id"]), stamp=x.get("stamp") or "", vendor=(x.get("dealer") or "supplier not read"),
                        sn=x["dealer"], day=(x.get("day") or x.get("date") or "")[:10], created_at=x.get("day") or "", via="—",
                        lines=[dict(id=None, item=str(l.get("name") or ""), qty=str(l.get("qty") or ""), came=0, state="came", how="as read",
                                    short_text="", carry=None, packs=0) for l in (x.get("lines") or [])],
                        missing=[], group="arr", late=False, due_at=None, arrived_how="scan", arrived_at=None, in_marg=False, bills=[],
                        scans=[dict(scan=int(x["id"]), stamp=x["stamp"], via="no order")], chase=False, orderless=True,
                        age=max((now.date() - (dt.date.fromisoformat(str(x.get("day") or now.date().isoformat())[:10]))).days, 0)))
    return out


def team(con, na=None, mk=None):
    """Out of stock (asked, not yet answered, not cleared by a bill) and substitutes (not yet answered): one list, oldest first."""
    na = _na_all(con) if na is None else na
    mk = marks(con) if mk is None else mk
    done_sub = {int(m["sub_id"]) for m in mk if m["kind"] in ("sub_ok", "sub_return") and m.get("sub_id")}
    waits = {int(m["na_id"]): m for m in mk if m["kind"] == "wait" and m.get("na_id")}
    out = []
    for r in na:
        if r["status"] != "asked" or r.get("cleared_at"):
            continue
        w = waits.get(int(r["id"]))
        out.append(dict(kind="oos", id=r["id"], item=r["item"], vendor=r.get("vendor") or "", sn=r.get("supplier_norm") or "", qty=r.get("qty") or "",
                        at=r["at"], last=r.get("last_bought") or "", by=r.get("by") or "", wait=(w["until"] if w else ""),
                        other=_other_dealer(con, r["item"], r.get("supplier_norm") or "")))
    for m in mk:
        if m["kind"] == "sub" and int(m["id"]) not in done_sub:
            out.append(dict(kind="sub", id=m["id"], item="%s → %s" % (m.get("item") or "", m.get("sub_item") or "substitute"), vendor=m.get("vendor") or "",
                            sn="", qty="", at=m["at"], last="", by=m.get("by") or "", wait="", other=None, line=m.get("line_id")))
    out.sort(key=lambda t: t["at"])
    return out


def _other_dealer(con, item, sn):
    """The dealer who billed this medicine most recently, other than the one it was ordered from -> (sn, vendor), else None."""
    try:
        fs = _forms(con, item, sn)
        best = None
        for sup, supn, day, it in con.execute("SELECT supplier, supplier_norm, bill_date, item FROM purchase_line WHERE "
                                               "UPPER(COALESCE(direction,'PURCHASE'))='PURCHASE' ORDER BY bill_date DESC, id DESC LIMIT 20000"):
            if supn and supn != sn and _norm(it) in fs:
                best = (supn, sup)
                break
        return best
    except sqlite3.Error:
        return None


# ------------------------------------------------------------------ the doors (his buttons; each returns (dict, status))
def _line_ctx(con, oid, lid):
    r = con.execute("SELECT o.id, o.vendor, o.supplier_norm, o.created_at, l.item FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id "
                    "WHERE o.id=? AND l.id=?", (int(oid), int(lid))).fetchone()
    return dict(r) if r else None


def _red_ref(con, oid, lid, item, sn):
    """The red-box line (kind, ref) the old doors know for this order line: its open carry, else the late line."""
    c = con.execute("SELECT id FROM order_carry WHERE from_line_id=? AND done_at IS NULL AND dropped_at IS NULL", (int(lid),)).fetchone()
    if c:
        return "carry", str(c[0])
    return "late", "%d:%d" % (int(oid), int(lid))


def _mark(con, who, kind, **kw):
    ensure(con)
    cols = ["kind", "by", "at"] + list(kw)
    cur = con.execute("INSERT INTO order_flow_mark (%s) VALUES (%s)" % (", ".join(cols), ",".join("?" * len(cols))),
                      [kind, who, now_iso()] + list(kw.values()))
    try:
        _os().audit(con, who, "s920_" + kind, cur.lastrowid, dict(kw, kit=KIT))
    except Exception:                                             # noqa: BLE001
        pass
    con.commit()
    return cur.lastrowid


def act(con, who, b):
    """His buttons. b: dict(do, oid, lid, na, sub). do: again | oos | close | chase | other | wait | drop | sub_ok | sub_return."""
    ensure(con)
    if not isinstance(b, dict):
        return dict(ok=False, error="bad_request"), 400
    try:
        b = dict(b, **{k: int(b.get(k) or 0) for k in ("oid", "lid", "na", "sub")})
    except (TypeError, ValueError):
        return dict(ok=False, error="bad_request"), 400
    do = str(b.get("do") or "")
    S7 = _s7()
    if do in ("again", "oos", "close"):
        lc = _line_ctx(con, b.get("oid") or 0, b.get("lid") or 0)
        if not lc:
            return dict(ok=False, error="gone", message="This line is no longer there."), 409
        kind, ref = _red_ref(con, lc["id"], b["lid"], lc["item"], lc["supplier_norm"])
        if do == "close":
            t = now_iso()
            if kind == "carry":
                con.execute("UPDATE order_carry SET dropped_at=?, dropped_by='owner_closed' WHERE id=? AND done_at IS NULL AND dropped_at IS NULL", (t, int(ref)))
            _mark(con, who, "closed", order_id=int(lc["id"]), line_id=int(b["lid"]), item=lc["item"], vendor=lc["vendor"])
            return dict(ok=True, item=lc["item"]), 200
        if do == "again":
            r, st = S7.again(con, who, kind, ref)
            if st == 409 and kind == "late":                       # not in the red box yet (under 3 working days): straight onto today's card
                r, st = _again_direct(con, who, lc, b["lid"])
            return r, st
        r, st = S7.na(con, who, dict(kind=kind, ref=ref))
        if st == 409 and kind == "late":
            r, st = _na_direct(con, who, lc, b["lid"])
        return r, st
    if do == "chase":
        oid = int(b.get("oid") or 0)
        if not con.execute("SELECT 1 FROM purchase_order WHERE id=?", (oid,)).fetchone():
            return dict(ok=False, error="gone"), 409
        _mark(con, who, "chase", order_id=oid)
        return dict(ok=True), 200
    if do in ("drop", "wait", "other"):
        nid = int(b.get("na") or 0)
        r = con.execute("SELECT * FROM order_s778_na WHERE id=?", (nid,)).fetchone()
        if not r:
            return dict(ok=False, error="gone"), 404
        r = dict(r)
        if do == "drop":
            return S7.na_answer(con, who, nid, "stop")
        if do == "wait":
            until = (dt.date.today() + dt.timedelta(days=WAIT_DAYS)).isoformat()
            _mark(con, who, "wait", na_id=nid, item=r["item"], vendor=r.get("vendor") or "", until=until)
            return dict(ok=True, until=until), 200
        od = _other_dealer(con, r["item"], r.get("supplier_norm") or "")
        if not od:
            return dict(ok=False, error="no_dealer", message="No other dealer has billed this medicine."), 409
        res, st = S7.na_answer(con, who, nid, "keep")
        if st != 200:
            return res, st
        con.execute("INSERT INTO order_s778_again (supplier_norm, vendor, item, qty, pack_size, packing, rate_p, kind, ref, src_day, from_sn, at, by) "
                    "VALUES (?,?,?,?,1,'',0,'s920_other',?,?,?,?,?)", (od[0], od[1], r["item"], max(_int(r.get("qty")), 1), "na:%d" % nid,
                                                                     str(r["at"])[:10], r.get("supplier_norm") or "", now_iso(), who))
        _mark(con, who, "other", na_id=nid, item=r["item"], vendor=r.get("vendor") or "", to_sn=od[0])
        return dict(ok=True, item=r["item"], vendor=od[1]), 200
    if do in ("sub_ok", "sub_return"):
        sid = int(b.get("sub") or 0)
        m = con.execute("SELECT * FROM order_flow_mark WHERE id=? AND kind='sub' AND undone_at IS NULL", (sid,)).fetchone()
        if not m:
            return dict(ok=False, error="gone"), 404
        _mark(con, who, do, sub_id=sid, order_id=m["order_id"], line_id=m["line_id"], item=m["item"], vendor=m["vendor"])
        return dict(ok=True), 200
    return dict(ok=False, error="bad_do"), 400


def _int(v):
    m = re.match(r"\s*(\d+)", str(v or ""))
    return int(m.group(1)) if m else 1


def _again_direct(con, who, lc, lid):
    ref = "%d:%d" % (int(lc["id"]), int(lid))
    if con.execute("SELECT 1 FROM order_s778_again WHERE kind='late' AND ref=? AND cleared_at IS NULL", (ref,)).fetchone():
        return dict(ok=True, already=True, item=lc["item"]), 200
    l = con.execute("SELECT packs, pack_size, supplied, billed_qty FROM purchase_order_line WHERE id=?", (int(lid),)).fetchone()
    came = int(l[3] if l[3] is not None else (l[2] or 0))
    cur = con.execute("INSERT INTO order_s778_again (supplier_norm, vendor, item, qty, pack_size, packing, rate_p, kind, ref, src_day, from_sn, at, by) "
                      "VALUES (?,?,?,?,?,'',0,'late',?,?,?,?,?)", (lc["supplier_norm"], lc["vendor"], lc["item"], max(int(l[0] or 1) - came, 1), int(l[1] or 1),
                                                                 "%d:%d" % (int(lc["id"]), int(lid)), str(lc["created_at"])[:10], lc["supplier_norm"], now_iso(), who))
    con.commit()
    return dict(ok=True, id=cur.lastrowid, item=lc["item"]), 200


def _na_direct(con, who, lc, lid):
    k = _norm(lc["item"])
    if con.execute("SELECT 1 FROM order_s778_na WHERE item_norm=? AND status IN ('asked','stop') AND cleared_at IS NULL", (k,)).fetchone():
        return dict(ok=True, already=True, item=lc["item"]), 200
    mx = con.execute("SELECT COALESCE(MAX(id),0) FROM purchase_line").fetchone()[0]
    cur = con.execute("INSERT INTO order_s778_na (item_norm, item, supplier_norm, vendor, kind, ref, qty, by, at, last_bought, max_line) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (k, lc["item"], lc["supplier_norm"], lc["vendor"], "late", "%d:%d" % (int(lc["id"]), int(lid)), "", who, now_iso(), _s7().last_bought(con, lc["item"]), int(mx or 0)))
    con.commit()
    return dict(ok=True, id=cur.lastrowid, item=lc["item"]), 200


def wait_pass(con, today=None):
    """A 'Wait — order next week' whose day has come: his word becomes 'keep ordering' (the medicine goes back on the list). Keyed, idempotent."""
    ensure(con)
    today = (today or dt.date.today()).isoformat()
    n = t = 0
    for m in [dict(r) for r in con.execute("SELECT * FROM order_flow_mark WHERE kind='wait' AND undone_at IS NULL AND until<=?", (today,))]:
        t += 1
        r = con.execute("SELECT status, cleared_at FROM order_s778_na WHERE id=?", (int(m["na_id"]),)).fetchone()
        if r and r[0] == "asked" and not r[1]:
            _s7().na_answer(con, "wait (%s)" % m["by"], int(m["na_id"]), "keep")
            n += 1
        con.execute("UPDATE order_flow_mark SET undone_at=? WHERE id=?", (now_iso(), m["id"]))
    if t:
        con.commit()
    return n


def table(G):
    """The walk's table: one line per row (no phone, no patient)."""
    out = []
    for g in GROUPS:
        for r in G[g]:
            out.append("%-4s %-5s %-24s %s %s miss=[%s]" % (g, r["id"] or "-", str(r["vendor"])[:24], r["day"], "/".join(l["state"] for l in r["lines"]),
                                                           ", ".join(l["item"] for l in r["missing"])))
    return out


# ------------------------------------------------------------------ his page (English): "Purchase orders" grouped, per mock-up v4
CSS = """<style>
.of{max-width:1080px;margin:0 auto;padding:10px 12px;font:15px/1.5 "Segoe UI",system-ui,sans-serif;color:#16202a}
.of h2{font-size:20px;margin:6px 0 2px}.of .sub2{color:#6b7785;font-size:13px}
.of .leg{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:#6b7785;margin:4px 0}.of .leg i{display:inline-block;width:14px;height:8px;border-radius:4px;margin-right:4px;vertical-align:middle}
.of details>summary{list-style:none;cursor:pointer}.of details>summary::-webkit-details-marker{display:none}
.of .strip{background:#fff;border-radius:12px;border:1px solid #dde3e9;margin:12px 0;overflow:hidden}
.of .strip>summary{padding:12px 16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}.of .big{font-weight:700;font-size:16px}
.of .chip{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:14px;font-size:13px;font-weight:600;white-space:nowrap}
.of .c-red{background:#fde8e8;color:#a61b1b}.of .c-amb{background:#fff3d6;color:#8a5a00}.of .c-grey{background:#eef1f4;color:#45505c}.of .c-green{background:#e3f6ec;color:#11683a}.of .c-blue{background:#e6eefc;color:#1d4fae}
.of .arrow{margin-left:auto;color:#6b7785;font-size:13px}.of details[open]>summary .arrow .o{display:none}.of details:not([open])>summary .arrow .c{display:none}
.of .grp{border-top:1px solid #dde3e9}.of .grp>summary{padding:10px 16px;font-weight:700;display:flex;gap:10px;align-items:center;background:#f8fafb}
.of .row{border-top:1px solid #dde3e9}.of .row>summary{padding:10px 16px;display:grid;grid-template-columns:minmax(170px,1.3fr) 120px minmax(230px,1.4fr) auto;gap:12px;align-items:center}
.of .dn{font-weight:600}.of .dd{color:#6b7785;font-size:13px}.of .mm{font-size:13px;color:#a61b1b;margin-top:2px}
.of .bar{display:flex;gap:3px}.of .bar span{flex:1;height:8px;border-radius:4px;background:#c5ccd4}.of .bar .g{background:#1f9d55}.of .bar .a{background:#e3a008}.of .bar .r{background:#d64545}
.of .barlab{display:flex;justify-content:space-between;font-size:10.5px;color:#6b7785;margin-top:2px}
.of .body{padding:4px 16px 14px;display:grid;grid-template-columns:220px 1fr;gap:16px}
@media(max-width:720px){.of .row>summary{grid-template-columns:1fr auto}.of .row>summary .pb{grid-column:1/-1}.of .body{grid-template-columns:1fr}}
.of .scan{border:1px solid #dde3e9;border-radius:8px;padding:6px;text-align:center;font-size:12px;color:#6b7785}.of .scan img{width:100%;border-radius:4px}
.of .noscan{border:1px dashed #c5ccd4;border-radius:8px;padding:30px 8px;text-align:center;color:#6b7785;font-size:13px}
.of table{border-collapse:collapse;width:100%;font-size:14px}.of th,.of td{text-align:left;padding:5px 8px;border-bottom:1px solid #dde3e9;vertical-align:top}.of th{color:#6b7785;font-weight:600;font-size:12.5px}
.of .btns{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.of button{font:inherit;font-size:13.5px;padding:6px 12px;border-radius:8px;border:1px solid #dde3e9;background:#fff;cursor:pointer;min-height:36px}
.of button.p{background:#2f6fde;color:#fff;border-color:#2f6fde}.of button.w{border-color:#e8b3b3;color:#a61b1b}
.of button.arm{background:#fff3d6;border-color:#e3a008;color:#6b4500}.of button.done{background:#e3f6ec;border-color:#9fd8b6;color:#11683a}
.of .tip{background:#e6eefc;border-radius:8px;padding:6px 10px;font-size:13px;color:#1d3f86;margin-top:8px}
.of .small{font-size:12.5px;color:#6b7785}.of .call{font-size:13px;color:#2f6fde;font-weight:600;text-decoration:none}
.of .oldfold{background:#fff;border:1px solid #dde3e9;border-radius:12px;margin:16px 0}.of .oldfold>summary{padding:12px 16px;font-weight:700}
</style>"""

JS = """<script>
function ofTwo(b,body){if(b.classList.contains("done")||b.dataset.busy)return;
 if(!b.classList.contains("arm")){b.dataset.t=b.dataset.t||b.textContent;b.classList.add("arm");b.textContent=b.dataset.t+" — tap again";
  setTimeout(function(){if(b.classList.contains("arm")){b.classList.remove("arm");b.textContent=b.dataset.t;}},4000);return;}
 b.classList.remove("arm");b.dataset.busy="1";b.textContent="…";
 fetch("%s/api/flow/act",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})
 .then(function(r){return r.json().then(function(j){return [r.status,j];});}).then(function(x){delete b.dataset.busy;
  if(x[1]&&x[1].ok){b.classList.add("done");b.textContent="✓ "+b.dataset.t;var row=b.closest(".btns");if(row)row.querySelectorAll("button").forEach(function(o){if(o!==b)o.disabled=true;});}
  else{b.textContent=b.dataset.t+" — "+((x[1]&&(x[1].message||x[1].error))||"not saved");}})
 .catch(function(){delete b.dataset.busy;b.textContent=b.dataset.t+" — not saved";});}
</script>""" % P

LBL = {"came": ("c-green", "came"), "short": ("c-red", "did not come"), "part": ("c-amb", "came less"), "open": ("c-grey", "awaited"),
       "awaiting": ("c-grey", "arrived — Marg will confirm"), "oos": ("c-red", "out of stock"), "sub": ("c-blue", "substitute came"),
       "settled": ("c-green", "settled")}
AR = '<span class="arrow"><span class="o">▸ open</span><span class="c">▾ close</span></span>'


def _btn(label, body, cls=""):
    import json as _j                                             # noqa: PLC0415
    return '<button class="%s" onclick=\'ofTwo(this,%s)\'>%s</button>' % (cls, esc(_j.dumps(body)), esc(label))


def _steps(r):
    g = r["group"]
    if g == "late":
        c = ["g", "g", "r", "", ""]
    elif g == "way":
        c = ["g", "g", "a", "", ""]
    elif g == "arr":
        c = ["g", "g" if r.get("id") else "", "r" if r["missing"] else "g", "g" if r.get("scans") else "a", "a"]
    elif g == "gap":
        c = ["g", "g", "r", "g" if r.get("scans") else "a", "g"]
    else:
        c = ["g"] * 5
    lab = ["Ordered", "Sent", "Arrived", "Scanned", "In Marg"]
    return ('<div class="pb"><div class="bar">' + "".join('<span class="%s"></span>' % x for x in c) + '</div><div class="barlab">' +
            "".join("<span>%s</span>" % l for l in lab) + "</div></div>")


def _age(r):
    g = r["group"]
    if g == "late":
        return '<span class="chip c-red">%d days — late</span>' % r["age"]
    if g == "way":
        return '<span class="chip c-grey">on the way</span>'
    if g == "arr":
        if r.get("orderless"):
            return '<span class="chip c-blue">bill, no order</span>'
        return '<span class="chip c-amb">arrived, short</span>' if r["missing"] else '<span class="chip c-blue">arrived</span>'
    if g == "gap":
        return '<span class="chip c-red">medicine missing</span>'
    return '<span class="chip c-green">complete</span>'


def _scan_box(r):
    sc = r.get("scans") or []
    if not sc:
        return '<div class="noscan">No bill scanned yet</div>'
    sid = int(sc[0].get("head") or sc[0]["scan"])
    stamp = sc[0].get("stamp") or "#%d" % sid
    return ('<div class="scan"><a href="/scanapp/bills/%d/file" target="_blank" rel="noopener"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="">'
            '</a>%s · <a href="/scanapp/bills/%d/file" target="_blank" rel="noopener">open full size</a></div>') % (sid, sid, esc(stamp), sid)


def _line_btns(r, l):
    if r.get("orderless") or not r.get("id") or not l.get("id"):
        return ""
    b = dict(oid=r["id"], lid=l["id"])
    if l["state"] in ("short", "part") or (r["group"] == "late" and l["state"] == "open"):
        return (_btn("Order again", dict(b, do="again"), "p") + _btn("Out of stock", dict(b, do="oos")) +
                _btn("Close: never came", dict(b, do="close"), "w"))
    if l["state"] == "oos":
        return '<span class="small">in the team list below</span>'
    if l["state"] == "sub":
        return '<span class="small">substitute — in the team list below</span>'
    if l["state"] == "settled" and l.get("how"):
        return '<span class="small">%s</span>' % esc(l["how"])
    return ""


def _lines(r):
    if r.get("orderless"):
        h = '<div class="small">This bill came with no order in the system. Its read lines show here; Amir enters it in Marg as usual.</div>'
        if r["lines"]:
            h += "<table><tr><th>Line read</th><th>Qty</th></tr>" + "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(l["item"]), esc(l["qty"])) for l in r["lines"]) + "</table>"
        return h
    h = "<table><tr><th>Medicine</th><th>Ordered</th><th>Came</th><th></th><th></th></tr>"
    for l in r["lines"]:
        st = "short" if (l["state"] == "open" and r["group"] == "late") else l["state"]
        cls, word = LBL.get(st, ("c-grey", st))
        came = "—" if l["state"] in ("open", "awaiting") else str(l["came"])
        h += "<tr><td>%s</td><td>%s</td><td>%s</td><td><span class=\"chip %s\">%s</span></td><td>%s</td></tr>" % (
            esc(l["item"]), esc(l["qty"]), esc(came), cls, esc(word), ('<div class="btns">%s</div>' % _line_btns(r, l)))
    return h + "</table>"


def _row_acts(r):
    if r.get("orderless") or not r.get("id"):
        return ""
    g = r["group"]
    if g == "late":
        rw = _rec_word_en(r.get("rec"))                         # S921: reception's word, when she has given one
        if r.get("chase"):
            return '<span class="small">Chase sent to reception.</span>' + rw
        return _btn("Chase now (to reception)", dict(do="chase", oid=r["id"]), "p") + rw
    if g == "way":
        return '<span class="small">Due %s</span>' % esc(r["due_at"].strftime("%d-%b %H:%M") if r.get("due_at") else "")
    if g == "arr":
        return '<span class="small">Amir enters it in Marg on his next visit.</span>'
    return ""


def _phone(con, vendor):
    try:
        call = _os().book_card(con, vendor)[0]
        d = re.sub(r"\D", "", str(call or ""))[-10:]
        if len(d) == 10:
            return '<a class="call" href="tel:+91%s">📞 %s %s</a>' % (esc(d), esc(d[:5]), esc(d[5:]))
    except Exception:                                             # noqa: BLE001
        pass
    return ""


def order_row(con, r):
    mm = ('<div class="mm">Not come: %s</div>' % esc(", ".join(l["item"] for l in r["missing"]))) if r["missing"] else ""
    if r.get("orderless"):
        dd = "%s · no order · bill %s" % (ddmm(r["day"]), r["scans"][0]["stamp"] if r.get("scans") else "")
    else:
        n = len(r["lines"])
        dd = "%s%s · %d medicine%s" % (ddmm(r["day"]), (" · " + r["via"]) if r.get("via") else "", n, "" if n == 1 else "s")
    return ('<details class="row"><summary><div><div class="dn">%s</div><div class="dd">%s</div>%s</div><div>%s</div>%s<div>%s</div></summary>'
            '<div class="body">%s<div>%s<div class="btns">%s</div></div></div></details>') % (
        esc(r["vendor"]), esc(dd), mm, _age(r), _steps(r), _phone(con, r["vendor"]) if not r.get("orderless") else "", _scan_box(r), _lines(r), _row_acts(r))


def _grp(con, title, chip, rows, open_=False):
    return ('<details class="grp"%s><summary>%s %s%s</summary>%s</details>' % (" open" if open_ else "", chip, esc(title), AR,
                                                                         "".join(order_row(con, r) for r in rows) or '<div class="small" style="padding:8px 16px">None.</div>'))


def team_table(rows, mode="you"):
    h = "<table><tr><th>Medicine</th><th>Dealer</th><th>Qty</th><th>Tapped</th><th>Last bought</th><th></th><th></th></tr>"
    for t in rows:
        if mode == "you":
            if t["kind"] == "sub":
                a = _btn("Substitute OK", dict(do="sub_ok", sub=t["id"]), "p") + _btn("Not OK — return", dict(do="sub_return", sub=t["id"]), "w")
            elif t.get("wait"):
                a = '<span class="small">waiting until %s, then back on the list</span>' % esc(ddmm(t["wait"]))
            else:
                a = (_btn("Order from %s" % _short(t["other"][1]), dict(do="other", na=t["id"]), "p") if t.get("other") else "") + \
                    _btn("Wait — order next week", dict(do="wait", na=t["id"])) + _btn("Drop it", dict(do="drop", na=t["id"]), "w")
        else:
            a = '<span class="chip c-amb">waiting for the doctor</span>'
        cls, word = LBL["oos" if t["kind"] == "oos" else "sub"]
        h += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><span class=\"chip %s\">%s</span></td><td><div class=\"btns\">%s</div></td></tr>" % (
            esc(t["item"]), esc(_short(t["vendor"])), esc(qty_en(t["qty"]) if mode == "you" else t["qty"]), esc(ddmm(t["at"])),
            esc(ddmm(t["last"]) if t["last"] else "—"), cls, esc(word), a)
    return h + "</table>"


def _short(v):
    try:
        return _s7().short(v)
    except Exception:                                             # noqa: BLE001
        return str(v or "").split(" ")[0].title()


def owner_body(con, now=None, G=None):
    """The grouped page's body (English): the Not complete strip (open), Delivered and complete (folded, by order day, newest first)."""
    now = now or dt.datetime.now()
    try:
        wait_pass(con, now.date())
    except Exception:                                             # noqa: BLE001
        pass
    G = G or groups(con, now)
    c = G["counts"]
    nc = c["late"] + c["way"] + c["arr"] + c["gap"]
    h = ['<div class="of">', CSS, '<h2>Purchase orders</h2><div class="sub2">%s · the orders since %s, grouped</div>' % (
        esc(now.strftime("%A %d-%b-%Y")), esc(ddmm(_ot().since(con)))),
        '<div class="leg"><span><i style="background:#1f9d55"></i>done</span><span><i style="background:#e3a008"></i>waiting</span>'
        '<span><i style="background:#d64545"></i>late / missing</span><span><i style="background:#c5ccd4"></i>not yet</span> · steps: Ordered · Sent · Arrived · Bill scanned · In Marg</div>']
    h.append('<details class="strip" open><summary><span class="big">Not complete: %d orders · oldest %d days</span>'
             '<span class="chip c-red">🔴 Late %d</span><span class="chip c-grey">⚪ On the way %d</span><span class="chip c-blue">📦 Arrived, not in Marg %d</span>'
             '<span class="chip c-red">💊 Medicines still missing %d</span><span class="chip c-amb">✋ Out of stock / substitute %d</span>%s</summary>' % (
                 nc, c["oldest"], c["late"], c["way"], c["arr"], c["gap_meds"], c["team"], AR))
    h.append(_grp(con, "Late — nothing came by the due day", '<span class="chip c-red">%d</span>' % c["late"], G["late"], True))
    h.append(_grp(con, "On the way — inside the %s days" % _days(con), '<span class="chip c-grey">%d</span>' % c["way"], G["way"]))
    h.append(_grp(con, "Arrived, not yet in Marg — %d came short (named on the row)" % c["arr_short"], '<span class="chip c-blue">%d</span>' % c["arr"], G["arr"]))
    h.append(_grp(con, "In Marg, but medicines still missing", '<span class="chip c-red">%d</span>' % c["gap"], G["gap"]))
    h.append('<details class="grp"%s><summary><span class="chip c-amb">%d</span> Out of stock and substitutes — the team list (Darpan and reception see it too)%s</summary>'
             '<div style="padding:6px 16px 12px">%s</div></details></details>' % (" open" if c["team"] else "", c["team"], AR, team_table(G["team"], "you")))
    days = []
    for r in G["done"]:
        if r["day"] not in days:
            days.append(r["day"])
    h.append('<details class="strip"><summary><span class="big">Delivered and complete: %d</span><span class="chip c-green">newest first</span>%s</summary>' % (c["done"], AR))
    for d in days:
        rs = [r for r in G["done"] if r["day"] == d]
        h.append(_grp(con, "Ordered %s" % ddmm(d), '<span class="chip c-green">%d</span>' % len(rs), rs))
    h.append("</details>")
    h.append(JS)
    h.append("</div>")
    return "".join(h)


def _days(con):
    try:
        return str(_ot().deliver_days(con))
    except Exception:                                             # noqa: BLE001
        return "2"


# ------------------------------------------------------------------ the doors on the server (mounted by porders.init, fail-soft)
_auth = None


def init(app, auth):
    """Mount /finance/porders/flow (the grouped page alone) and /finance/porders/api/flow/act (his buttons). auth = porders._auth."""
    global _auth
    from flask import Blueprint, jsonify, request                 # noqa: PLC0415
    _auth = auth
    bp = Blueprint("order_flow_s920", __name__)

    def _who(u):
        return str(u.get("user") or u.get("login") or "")

    def _may(u, kind):
        return kind == "owner" or str(u.get("login") or u.get("user") or "").lower() == "shavez"

    @bp.route(P + "/flow")
    def flow_page():
        u, con, kind, err = _auth()
        if err:
            return err
        if not _may(u, kind):
            return jsonify(ok=False, error="owner_only"), 403
        con.row_factory = sqlite3.Row
        if request.args.get("rec") == "1":                        # S921: the strip on reception's home, for him to see as she sees it
            try:
                import porders_s454 as _S                         # noqa: PLC0415
                css = "<style>%s</style>" % _S.CSS
            except Exception:                                     # noqa: BLE001
                css = ""
            body = ('<div style="max-width:480px;margin:0 auto;padding:0 12px">%s<h1>Aaj ka kaam (reception)</h1>%s</div>'
                    % (css, (rec_body(con) or "<p>Nothing open.</p>").replace("onclick='recTwo(", "disabled title='preview' onclick='return;recTwo(")))
        else:
            body = owner_body(con)
        html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                '<title>Purchase orders</title></head><body style="margin:0;background:#eef1f4"><div style="max-width:1080px;margin:0 auto;padding:8px 12px">'
                '<a href="/portal" style="font-weight:600;text-decoration:none">← BACK</a></div>%s</body></html>') % body
        return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}

    @bp.route(P + "/api/flow/act", methods=["POST"])
    def flow_act():
        u, con, kind, err = _auth()
        if err:
            return err
        if not _may(u, kind):
            return jsonify(ok=False, error="owner_only", message="Only the doctor (or Shavez) decides these."), 403
        con.row_factory = sqlite3.Row
        b = request.get_json(silent=True) or {}
        r, st = act(con, _who(u), b)
        return jsonify(**r), st

    @bp.route(P + "/api/flow/rec", methods=["POST"])
    def flow_rec():                                               # S921: reception's buttons (the senders and the owner)
        u, con, kind, err = _auth()
        if err:
            return err
        if kind not in ("owner", "sender"):
            return jsonify(ok=False, error="view_only", message="Aap sirf dekh sakte hain."), 403
        b = request.get_json(silent=True)
        if not isinstance(b, dict):
            return jsonify(ok=False, error="bad_request"), 400
        con.row_factory = sqlite3.Row
        if str(b.get("do") or "") in ("again", "oos", "oosrow", "sub"):
            try:
                import order_rules                                # noqa: PLC0415
                fr = order_rules._frozen(con)
                if fr:
                    return jsonify(ok=False, error="frozen", message="Medicine ordering band hai: %s" % (fr.get("reason") or "")), 423
            except Exception:                                     # noqa: BLE001
                pass
        r, st = rec_act(con, _who(u), b)
        return jsonify(**r), st

    @bp.route(P + "/api/flow/scan", methods=["POST"])
    def flow_scan():                                              # S923: his word on a doubtful scan (the Purchase bills page)
        u, con, kind, err = _auth()
        if err:
            return err
        if kind != "owner":
            return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
        b = request.get_json(silent=True)
        if not isinstance(b, dict):
            return jsonify(ok=False, error="bad_request"), 400
        import provisional_s781 as PV                             # noqa: PLC0415
        r, st = PV.scan_word(con, _who(u), b.get("scan"), str(b.get("do") or ""), str(b.get("why") or ""))
        return jsonify(**r), st

    @bp.route(P + "/api/flow/scanset", methods=["POST"])
    def flow_scanset():                                           # S923: the round-off allowance, his setting on the same page
        u, con, kind, err = _auth()
        if err:
            return err
        if kind != "owner":
            return jsonify(ok=False, error="owner_only", message="Only the doctor changes this."), 403
        b = request.get_json(silent=True)
        if not isinstance(b, dict):
            return jsonify(ok=False, error="bad_request"), 400
        import provisional_s781 as PV                             # noqa: PLC0415
        r, st = PV.set_tol(con, _who(u), b.get("rs"), b.get("pct"))
        return jsonify(**r), st

    @bp.route(P + "/api/flow/healthz")
    def flow_healthz():
        return jsonify(ok=True, module="order_flow", version=VERSION, kit=KIT)

    app.register_blueprint(bp)
    hub_lines_install()                                           # S924: the Hub's one purchase line
    return bp


# ------------------------------------------------------------------ S921 (kit S921_PURCHASE_FLOW_2): reception's page, from groups() alone
_QEN = {"patte": "strip", "goli": "tab", "nag": "pc", "botal": "bottle", "tube": "tube", "vial": "vial", "jar": "jar", "pudiya": "sachet"}


def qty_en(t):
    """F-1551: a quantity stored in the staff's words ('50 patte', '1 nag') read back in English ('50 strips', '1 pc') -- qty_words' pairs."""
    def _r(m):
        n, w = m.group(1), _QEN[m.group(2).lower()]
        return "%s %s%s" % (n, w, "" if n.lstrip("-") == "1" else "s")
    return re.sub(r"(-?\d+(?:\.\d+)?)\s*(patte|goli|nag|botal|tube|vial|jar|pudiya)\b", _r, str(t or ""), flags=re.I)


def rec_marks(con):
    """{order id: reception's newest word} -- order_flow_rec, not undone."""
    ensure(con)
    out = {}
    try:
        for r in con.execute("SELECT * FROM order_flow_rec WHERE undone_at IS NULL ORDER BY id"):
            out[int(r["order_id"])] = dict(r)
    except sqlite3.Error:
        pass
    return out


def _hm(iso):
    try:
        return dt.datetime.fromisoformat(str(iso)[:19]).strftime("%d-%m %H:%M")
    except (TypeError, ValueError):
        return ddmm(iso)


def _rec_word_en(m):
    if not m:
        return ""
    if m["kind"] == "called":
        return '<div class="small">Reception called %s — the dealer says it is coming (%s).</div>' % (esc(_hm(m["at"])), esc(m.get("by") or ""))
    return '<div class="small" style="color:#a61b1b">Reception %s: the dealer will not send it (%s). Your call: Out of stock or Close.</div>' % (
        esc(_hm(m["at"])), esc(m.get("by") or ""))


def _rec_word_hi(m):
    if not m:
        return ""
    if m["kind"] == "called":
        return '<div class="small grn">✓ Call kiya %s — dealer ne kaha maal aa raha hai</div>' % esc(_hm(m["at"]))
    return '<div class="small red">✓ %s — dealer nahi bhejega (Doctor sahab ko bata diya)</div>' % esc(_hm(m["at"]))


def rec_act(con, who, b):
    """Reception's buttons. b: dict(do, oid, lid). do: again | oos | sub | called | refused | oosrow."""
    ensure(con)
    if not isinstance(b, dict):
        return dict(ok=False, error="bad_request"), 400
    try:
        oid, lid = int(b.get("oid") or 0), int(b.get("lid") or 0)
    except (TypeError, ValueError):
        return dict(ok=False, error="bad_request"), 400
    do = str(b.get("do") or "")
    if do in ("again", "oos"):
        return act(con, who, dict(do=do, oid=oid, lid=lid))
    if do == "sub":
        lc = _line_ctx(con, oid, lid)
        if not lc:
            return dict(ok=False, error="gone", message="Yeh line ab nahi hai."), 409
        if con.execute("SELECT 1 FROM order_flow_mark WHERE kind='sub' AND line_id=? AND undone_at IS NULL", (lid,)).fetchone():
            return dict(ok=True, already=True, item=lc["item"]), 200
        _mark(con, who, "sub", order_id=oid, line_id=lid, item=lc["item"], vendor=lc["vendor"], sub_item="")
        return dict(ok=True, item=lc["item"]), 200
    if do in ("called", "refused"):
        if not con.execute("SELECT 1 FROM purchase_order WHERE id=?", (oid,)).fetchone():
            return dict(ok=False, error="gone", message="Yeh order ab nahi hai."), 409
        cur = con.execute("INSERT INTO order_flow_rec (kind, order_id, by, at) VALUES (?,?,?,?)", (do, oid, who, now_iso()))
        try:
            _os().audit(con, who, "s921_" + do, cur.lastrowid, dict(order=oid, kit=KIT))
        except Exception:                                         # noqa: BLE001
            pass
        con.commit()
        return dict(ok=True), 200
    if do == "oosrow":
        try:
            rows = _ot().light_all(con, dt.datetime.now(), oids=[oid])
        except Exception:                                         # noqa: BLE001
            rows = []
        if not rows:
            return dict(ok=False, error="gone", message="Yeh order ab nahi hai."), 409
        n = 0
        for x in rows[0]["lines"]:
            if x["state"] in ("open", "awaiting", "short", "part"):
                r, st = act(con, who, dict(do="oos", oid=oid, lid=int(x["id"])))
                if st == 200:
                    n += 1
        if not n:
            return dict(ok=False, error="none", message="Is order mein koi dawa baaki nahi."), 409
        return dict(ok=True, n=n), 200
    return dict(ok=False, error="bad_do"), 400


REC_CSS = """<style>
.of.rec{padding:0;max-width:none}.of.rec .row>summary{grid-template-columns:1fr auto}.of.rec .row>summary .pb{grid-column:1/-1}
.of.rec .body{grid-template-columns:1fr}.of.rec .strip>summary .big{font-size:17px}.of.rec button,.of.rec a.lk{min-height:44px;font-size:15px}
.of a.lk{display:inline-flex;align-items:center;justify-content:center;padding:6px 14px;border-radius:8px;text-decoration:none;font-weight:600}
.of a.lk.p{background:#2f6fde;color:#fff}
.of .bar{position:static;z-index:auto;display:flex;gap:3px;background:none;color:inherit;margin:0;padding:0}.of .bar span{border:0}
.of .grp{font-size:inherit;font-weight:inherit;margin-top:0}.of .grp>summary{font-weight:700}
.of.rec .strip>summary,.of.rec .grp>summary,.of.rec .row>summary{padding:10px 10px}.of.rec .body{padding:4px 10px 12px;gap:8px}
.of.rec .scan{max-width:150px}.of.rec .scan img{max-height:170px;object-fit:contain}.of.rec .noscan{padding:8px;max-width:150px}
.of.rec table{table-layout:fixed;font-size:14px}.of.rec th,.of.rec td{padding:5px 4px;word-break:break-word}
.of.rec th:nth-child(1),.of.rec td:nth-child(1){width:40%}.of.rec th:nth-child(2),.of.rec td:nth-child(2){width:20%}
.of.rec th:nth-child(3),.of.rec td:nth-child(3){width:11%}.of.rec tr.lb td{width:auto}
.of.rec .chip{white-space:normal;word-break:normal;overflow-wrap:normal;font-size:12px;padding:2px 7px}
.of.rec tr.lb td{border-bottom:2px solid #dde3e9;padding-top:0}.of.rec .btns{gap:6px}.of.rec .btns button,.of.rec .btns a.lk{flex:1 1 auto}
.of.rec .tm{padding:8px 0;border-bottom:1px solid #dde3e9}.of.rec .tm b{font-size:15px}
.of .grn{color:#11683a}.of .red{color:#a61b1b}.of .note{background:#fff3d6;border-radius:8px;padding:6px 10px;font-size:13.5px;color:#6b4500;margin-top:6px}
</style>"""

REC_JS = """<script>
function recTwo(b,body){if(b.classList.contains("done")||b.dataset.busy)return;
 if(!b.classList.contains("arm")){b.dataset.t=b.dataset.t||b.textContent;b.classList.add("arm");b.textContent=b.dataset.t+" — dobara dabaiye";
  setTimeout(function(){if(b.classList.contains("arm")){b.classList.remove("arm");b.textContent=b.dataset.t;}},4000);return;}
 b.classList.remove("arm");b.dataset.busy="1";b.textContent="…";
 fetch("%s/api/flow/rec",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})
 .then(function(r){return r.json().then(function(j){return [r.status,j];});}).then(function(x){delete b.dataset.busy;
  if(x[1]&&x[1].ok){b.classList.add("done");b.textContent="✓ "+b.dataset.t;var row=b.closest(".btns");if(row)row.querySelectorAll("button").forEach(function(o){if(o!==b)o.disabled=true;});}
  else{b.textContent=b.dataset.t+" — "+((x[1]&&(x[1].message||x[1].error))||"nahi hua");}})
 .catch(function(){delete b.dataset.busy;b.textContent=b.dataset.t+" — nahi hua";});}
</script>""" % P

LBL_HI = {"came": ("c-green", "aaya"), "short": ("c-red", "nahi aaya"), "part": ("c-amb", "kam aaya"), "open": ("c-grey", "intezaar"),
          "awaiting": ("c-grey", "aaya — Marg mein aayega"), "oos": ("c-red", "out of stock"), "sub": ("c-blue", "substitute aaya"),
          "settled": ("c-green", "ho gaya")}
ARH = '<span class="arrow"><span class="o">▸ kholo</span><span class="c">▾ band</span></span>'


def _rbtn(label, body, cls=""):
    import json as _j                                             # noqa: PLC0415
    return '<button class="%s" onclick=\'recTwo(this,%s)\'>%s</button>' % (cls, esc(_j.dumps(body)), esc(label))


def _rsteps(r):
    c = _steps(r)
    for en, hi in (("Ordered", "Order"), ("Sent", "Bheja"), ("Arrived", "Aaya"), ("Scanned", "Scan"), ("In Marg", "Marg")):
        c = c.replace("<span>%s</span>" % en, "<span>%s</span>" % hi, 1)
    return c


def _rage(r):
    g = r["group"]
    if g == "late":
        return '<span class="chip c-red">%d din — late</span>' % r["age"]
    if g == "way":
        return '<span class="chip c-grey">raste mein</span>'
    if g == "arr":
        if r.get("orderless"):
            return '<span class="chip c-blue">bill, bina order</span>'
        return '<span class="chip c-amb">aaya, kuch kam</span>' if r["missing"] else '<span class="chip c-blue">aaya</span>'
    if g == "gap":
        return '<span class="chip c-red">dawa baaki</span>'
    return '<span class="chip c-green">poora</span>'


def _rscan_box(r):
    sc = r.get("scans") or []
    if not sc:
        return '<div class="noscan">Bill abhi scan nahi hua</div>'
    sid = int(sc[0].get("head") or sc[0]["scan"])
    stamp = sc[0].get("stamp") or "#%d" % sid
    return ('<div class="scan"><a href="/scanapp/bills/%d/file" target="_blank" rel="noopener"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="">'
            '</a>%s · <a href="/scanapp/bills/%d/file" target="_blank" rel="noopener">poora dekhiye</a></div>') % (sid, sid, esc(stamp), sid)


def _rline_btns(r, l):
    if r.get("orderless") or not r.get("id") or not l.get("id"):
        return ""
    b = dict(oid=r["id"], lid=l["id"])
    if l["state"] in ("short", "part"):
        return (_rbtn("Dobara order karo", dict(b, do="again"), "p") + _rbtn("Out of stock", dict(b, do="oos")) +
                _rbtn("Substitute aaya", dict(b, do="sub")))
    if l["state"] in ("oos", "sub"):
        return '<span class="small">team list mein</span>'
    return ""


def _rlines(r):
    if r.get("orderless"):
        h = '<div class="small">Is bill ka koi order system mein nahi tha.</div>'
        if r["lines"]:
            h += "<table><tr><th>Bill par</th><th>Maatra</th></tr>" + "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(l["item"]), esc(l["qty"])) for l in r["lines"]) + "</table>"
        return h
    h = "<table><tr><th>Dawa</th><th>Order</th><th>Aaya</th><th></th></tr>"
    for l in r["lines"]:
        st = "short" if (l["state"] == "open" and r["group"] == "late") else l["state"]
        cls, word = LBL_HI.get(st, ("c-grey", st))
        came = "—" if l["state"] in ("open", "awaiting") else str(l["came"])
        bt = _rline_btns(r, l)
        h += '<tr><td>%s</td><td>%s</td><td>%s</td><td><span class="chip %s">%s</span></td></tr>' % (
            esc(l["item"]), esc(l["qty"]), esc(came), cls, esc(word))
        if bt:                                                    # S922: the line's buttons on their own row, the full width
            h += '<tr class="lb"><td colspan="4"><div class="btns">%s</div></td></tr>' % bt
    return h + "</table>"


def _rrow_acts(r):
    if r.get("orderless") or not r.get("id"):
        return ""
    g = r["group"]
    if g == "late":
        return (_rbtn("Call kiya — aa raha hai", dict(do="called", oid=r["id"]), "p") + _rbtn("Out of stock", dict(do="oosrow", oid=r["id"])) +
                _rbtn("Nahi bhejenge", dict(do="refused", oid=r["id"]), "w"))
    if g == "way":
        return '<a class="lk p" href="%s/s454/maal/%d">Maal aa gaya</a>' % (P, int(r["id"]))
    if g == "arr" and not r.get("scans"):
        try:
            import porders_s454 as S                              # noqa: PLC0415
            href = S.intake(r["vendor"], back=P)
        except Exception:                                         # noqa: BLE001
            href = "/scanapp/intake?lane=pharmacy&from=" + P
        return '<a class="lk p" href="%s">📷 Bill scan karo</a>' % esc(href)
    return ""


def rec_row(con, r):
    mm = ('<div class="mm">Nahi aaya: %s</div>' % esc(", ".join(l["item"] for l in r["missing"]))) if r["missing"] else ""
    if r.get("orderless"):
        dd = "%s · bina order · bill %s" % (ddmm(r["day"]), r["scans"][0]["stamp"] if r.get("scans") else "")
    else:
        dd = "%s%s · %d dawa" % (ddmm(r["day"]), (" · " + r["via"]) if r.get("via") else "", len(r["lines"]))
    note = ""
    if r["group"] == "late" and r.get("chase"):
        note = '<div class="note">Doctor sahab: is dealer ko call kijiye</div>'
    note += _rec_word_hi(r.get("rec")) if r["group"] == "late" else ""
    acts = _rrow_acts(r)
    return ('<details class="row"><summary><div><div class="dn">%s</div><div class="dd">%s</div>%s</div><div>%s</div>%s<div>%s</div></summary>'
            '<div class="body">%s<div>%s%s%s</div></div></details>') % (
        esc(r["vendor"]), esc(dd), mm, _rage(r), _rsteps(r), _phone(con, r["vendor"]) if not r.get("orderless") else "", _rscan_box(r), _rlines(r), note,
        ('<div class="btns">%s</div>' % acts) if acts else "")


def _rgrp(con, title, chip, rows, open_=False):
    return ('<details class="grp"%s><summary>%s %s%s</summary>%s</details>' % (" open" if open_ else "", chip, esc(title), ARH,
                                                                         "".join(rec_row(con, r) for r in rows) or '<div class="small" style="padding:8px 16px">Koi nahi.</div>'))


def rec_team(rows):
    h = ""
    for t in rows:                                                # S922: a short block each (a phone has no room for five columns)
        cls, word = LBL_HI["oos" if t["kind"] == "oos" else "sub"]
        h += ('<div class="tm"><b>%s</b><div class="small">%s · %s · %s</div><span class="chip %s">%s</span> '
              '<span class="chip c-amb">Doctor sahab ka faisla baaki</span></div>') % (
            esc(t["item"]), esc(_short(t["vendor"])), esc(t["qty"]) or "—", esc(ddmm(t["at"])), cls, esc(word))
    return h or '<div class="small">Koi nahi.</div>'


def rec_body(con, now=None, G=None):
    """Reception's strip (Roman Hindi), the same groups as his page; '' when nothing is open."""
    now = now or dt.datetime.now()
    G = G or groups(con, now)
    c = G["counts"]
    nc = c["late"] + c["way"] + c["arr"] + c["gap"]
    if not nc and not c["team"]:
        return ""
    h = ['<div class="of rec">', CSS, REC_CSS,
         '<details class="strip" open id="s921strip"><summary><span class="big">Maal baaki: %d order</span>'
         '<span class="chip c-red">🔴 Late %d</span><span class="chip c-grey">⚪ Raste mein %d</span><span class="chip c-blue">📦 Aaya %d</span>'
         '<span class="chip c-red">💊 Dawa baaki %d</span>%s</summary>' % (nc, c["late"], c["way"], c["arr"], c["gap_meds"], ARH)]
    if c["late"]:
        h.append(_rgrp(con, "Late — Order ka maal nahi aaya, dealer ko call kijiye", '<span class="chip c-red">%d</span>' % c["late"], G["late"], True))
    h.append(_rgrp(con, "Raste mein — maal aaye to 'Maal aa gaya' dabaiye", '<span class="chip c-grey">%d</span>' % c["way"], G["way"]))
    h.append(_rgrp(con, "Aaya — kam aayi dawa ke saamne button", '<span class="chip c-blue">%d</span>' % c["arr"], G["arr"]))
    h.append(_rgrp(con, "Purane order — dawa abhi baaki", '<span class="chip c-red">%d</span>' % c["gap"], G["gap"]))
    h.append('<details class="grp"><summary><span class="chip c-amb">%d</span> Out of stock / substitute — team list%s</summary>'
             '<div style="padding:6px 16px 12px">%s</div></details></details>' % (c["team"], ARH, rec_team(G["team"])))
    h.append(REC_JS)
    h.append("</div>")
    return "".join(h)


# ------------------------------------------------------------------ S922 (kit S922_PURCHASE_FLOW_3): Darpan's order tab, from groups() alone
_DEV = {"patte": "पत्ते", "goli": "गोली", "nag": "नग", "botal": "बोतल", "tube": "ट्यूब", "vial": "वायल", "jar": "जार", "pudiya": "पुड़िया"}


def _qty_dev(t):
    """A quantity in the staff's Roman words ('10 patte') in Darpan's script ('10 पत्ते') -- his page is Devanagari."""
    return re.sub(r"\b(patte|goli|nag|botal|tube|vial|jar|pudiya)\b", lambda m: _DEV[m.group(1).lower()], str(t or ""), flags=re.I)


def dar_view(con, now=None, G=None):
    """Darpan's read-only view (mock-up v4 FINAL, tab "Darpan"): each order's medicines still to come -- late, arrived short, in Marg
    still missing, on the way -- and the team list with the doctor's word. Writes nothing. A medicine ordered again on a later order is
    settled by groups() and so leaves this list by itself. Its only write is the due 'Wait -- next week' pass his own page runs too."""
    now = now or dt.datetime.now()
    try:
        wait_pass(con, now.date())                                # a 'next week' whose day has come is back on the list, not shown stale
    except Exception:                                             # noqa: BLE001
        pass
    G = G or groups(con, now, with_bills=False)                   # the orderless bills are not his
    rows = []
    for g in ("late", "arr", "gap", "way"):
        for r in G[g]:
            if r.get("orderless") or not r.get("id"):
                continue
            ls = [l for l in r["lines"] if l["state"] in ("open", "awaiting")] if g == "way" else r["missing"]
            if not ls:
                continue
            rows.append(dict(vendor=_short(r["vendor"]), day=ddmm(r["day"]), status=g,
                             items=[dict(item=l["item"], qty=_qty_dev(l["qty"]), state=l["state"]) for l in ls]))
    team_rows = [dict(item=t["item"], vendor=_short(t["vendor"]), qty=_qty_dev(t["qty"]), at=ddmm(t["at"]), kind=t["kind"],
                      wait=(ddmm(t["wait"]) if t.get("wait") else "")) for t in G["team"]]
    return dict(ok=True, rows=rows, team=team_rows)


# ------------------------------------------------------------------ S924 (kit S924_PURCHASE_FLOW_5): the Hub's Needs-you line, from groups() alone
def needs_you_line(con, now=None):
    """dict(cls, target, href, text) for his Hub -- the purchase flow in one line, the counts of his grouped page; None when nothing waits."""
    now = now or dt.datetime.now()
    rf = con.row_factory
    con.row_factory = sqlite3.Row
    try:
        try:
            wait_pass(con, now.date())
        except Exception:                                         # noqa: BLE001
            pass
        G = groups(con, now, with_bills=False)
    finally:
        con.row_factory = rf
    c = G["counts"]
    parts = []
    if c["late"]:
        parts.append("%d late" % c["late"])
    if c["gap_meds"]:
        parts.append("%d medicine%s still missing" % (c["gap_meds"], "" if c["gap_meds"] == 1 else "s"))
    if c["team"]:
        parts.append("%d out of stock / substitute for your word" % c["team"])
    if not parts:
        return None
    return dict(cls="warn", target="porders", href=P + "/flow", text="Purchase orders: %s — your grouped page" % " · ".join(parts))


_HUB = {}


def hub_lines_install():
    """Once per process: order_track.owner_line answers with needs_you_line; order_s778.owner_lines drops its line per out-of-stock tap
    (the team count is in the one line). Each wrapper falls back to the old line on any fault."""
    if _HUB.get("on"):
        return
    try:
        OT, S7 = _ot(), _s7()
    except Exception as e:                                        # noqa: BLE001
        print("S924 hub lines not installed: %r" % (e,), file=__import__("sys").stderr)
        return
    ot_before, s7_before = OT.owner_line, S7.owner_lines

    def owner_line(con, now):
        try:
            return needs_you_line(con, now)
        except Exception as e:                                    # noqa: BLE001
            print("S924 needs_you_line failed: %r" % (e,), file=__import__("sys").stderr)
            return ot_before(con, now)

    def owner_lines(con):
        out = s7_before(con)
        try:
            return [l for l in out if not (l.get("cls") == "warn" and str(l.get("href") or "").endswith("/s454/abnahi"))]
        except Exception:                                         # noqa: BLE001
            return out
    OT.owner_line, S7.owner_lines = owner_line, owner_lines
    _HUB.update(on=True, ot_before=ot_before, s7_before=s7_before)
