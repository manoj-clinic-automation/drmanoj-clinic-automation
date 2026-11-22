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

VERSION = "2.0"   # S926: one shortage per medicine, the identity check (Marg renames, dead names), the substitute flow, Stock & ledger inline
KIT = "S926_SHORTAGES_AND_RENAMES"
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
    try:
        ensure_words(con)                                         # S926
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
    out["team"] = team(con, na, mk, out)                           # S926: the shortages read the groups just made
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


def team(con, na=None, mk=None, G=None):
    """S926: the shortages, one per medicine and dealer (team_s926); the S920 list on any fault."""
    return team_s926(con, na, mk, G)


def team_s920(con, na=None, mk=None):
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
    r926 = act_s926(con, who, b, do)                              # S926: the shortage doors (same / two / sub_by / other2 / again_sh / wait2 / not_now / stop / came)
    if r926 is not None:
        return r926
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


def team_table_s920(rows, mode="you"):
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
    h.append('<details class="grp"%s><summary><span class="chip c-amb">%d</span> Not delivered, out of stock and substitutes — one row per medicine (Darpan and reception see it too)%s</summary>'
             '<div style="padding:6px 16px 12px">%s</div></details></details>' % (" open" if c["team"] else "", c["team"], AR, team_table_s926(con, G["team"], "you", G)))
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
                '<a href="/portal" style="font-weight:600;text-decoration:none">← BACK</a>'
                '<a href="/finance/porders?home=1" style="float:right;font-size:14px;text-decoration:none">Reception\'s screen →</a>'   # S925
                '</div>%s</body></html>') % body
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

    @bp.route(P + "/api/flow/items")
    def flow_items():                                             # S926: his substitute picker
        u, con, kind, err = _auth()
        if err:
            return err
        if not _may(u, kind):
            return jsonify(ok=False, error="owner_only"), 403
        return jsonify(ok=True, rows=items_like(con, request.args.get("q", "")))

    @bp.route(P + "/api/flow/dealers")
    def flow_dealers():                                           # S926: his dealer picker
        u, con, kind, err = _auth()
        if err:
            return err
        if not _may(u, kind):
            return jsonify(ok=False, error="owner_only"), 403
        return jsonify(ok=True, rows=dealers_like(con, request.args.get("q", "")))

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
        h += ('<div class="tm"><b>%s</b><div class="small">%s · %s · %s%s</div><span class="chip %s">%s</span> '
              '<span class="chip c-amb">%s</span></div>') % (
            esc(t["item"]), esc(_short(t["vendor"])), esc(t["qty"]) or "—", esc(ddmm(t["at"])),
            (" · Marg stock %s" % esc(t["marg_stock"])) if t.get("marg_stock") else "", cls, esc(word),
            esc(t.get("word_hi") or "Doctor sahab ka faisla baaki"))                  # S926: his word as an instruction
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
                      wait=(ddmm(t["wait"]) if t.get("wait") else ""), word=t.get("word_dev") or "", stock=t.get("marg_stock") or "",
                      n=t.get("n_orders") or 0) for t in G["team"]]                  # S926: his word, the Marg stock, the times ordered
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
    try:                                                          # S926: what waits for his word, by kind (Row rows, as groups() had them)
        rf2 = con.row_factory
        con.row_factory = sqlite3.Row
        try:
            sc = sh_counts(shortages(con, G, now))
        finally:
            con.row_factory = rf2
        if sc["rename"]:
            parts.append("%d medicine%s Marg renamed — your one tap" % (sc["rename"], "" if sc["rename"] == 1 else "s"))
        if sc["keeps"]:
            parts.append("%d a dealer keeps not sending" % sc["keeps"])
        if sc["oos"]:
            parts.append("%d out of stock for your word" % sc["oos"])
        if sc["sub"]:
            parts.append("%d substitute%s" % (sc["sub"], "" if sc["sub"] == 1 else "s"))
    except Exception as e:                                        # noqa: BLE001
        print("S926 sh_counts failed: %r" % (e,), file=__import__("sys").stderr)
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


# ====================================================================== S926 (kit S926_SHORTAGES_AND_RENAMES, Session 502, 22-Nov-2026 -- D1039 + his words 10:06-10:37)
#  ONE SHORTAGE PER MEDICINE, start to end -- and the identity check before anyone calls a medicine missing.
#
#  identity(con)   -- the names Marg prints today (the newest closing in stock_snapshot), the DEAD names (seen in an older closing, gone from
#                     the newest: a Marg rename), their partners: the ticked renames (item_alias), the Marg watch's detected pairs
#                     (marg_hand_change kind 'rename', open), the one name list (med_names 'marg' pairs). A dead name is never a shortage and never
#                     ordered (order_s778.hidden reads dead_norms); its partner's stock is the medicine's stock.
#  shortages(con)  -- from groups(): the run of a dealer's newest orders of one medicine that did NOT come in full, read as ONE thing --
#                     first missed order, how many times re-ordered, what came, the taps (who, when), his words -- and its state:
#                     rename (the identity question) · keeps (re-ordered twice or more, nothing came: to him by itself) · oos (a staff tap:
#                     the dealer says out of stock) · sub_way / sub_arr (his substitute, on its way / arrived) · wait · short (one miss; staff's).
#  act_s926        -- his doors on a shortage (keyed by the medicine and the dealer, never by a tap): same / two (the rename question),
#                     sub_by (substitute: name + dealer), other2 (order from a chosen dealer), again_sh, wait2, not_now, stop, came,
#                     sub_by_ok / sub_by_return. Every word is a row of order_flow_word (new table; the old marks table's CHECK stays).
#  The team list on every page (his, reception's, Darpan's) comes from shortages(); staff read his word as an instruction.
#  Writes: order_flow_word; order_s778's own doors (na, na_answer); item_alias + med_names + marg_hand_change for 'same' (their shape);
#  order_s778_again rows (the dealer's next order carries the substitute / the other dealer). Never Marg, purchase_line, stock.
# ======================================================================
WORD_DDL = ("CREATE TABLE IF NOT EXISTS order_flow_word (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, item TEXT NOT NULL, item_norm TEXT NOT NULL, "
            "sn TEXT NOT NULL DEFAULT '', vendor TEXT, order_id INTEGER, line_id INTEGER, na_id INTEGER, sub_item TEXT, to_sn TEXT, to_vendor TEXT, "
            "pair TEXT, until TEXT, note TEXT, by TEXT NOT NULL, at TEXT NOT NULL, undone_at TEXT)")
NOT_NOW_DAYS = 30
KEEPS_AFTER = 2                                                   # re-ordered this many times with nothing come -> to him by itself
D8 = "substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2)"   # stock_snapshot.as_on is DD-MM-YYYY


def ensure_words(con):
    con.execute(WORD_DDL)
    con.execute("CREATE INDEX IF NOT EXISTS order_flow_word_item ON order_flow_word (item_norm, sn)")


def words(con):
    ensure_words(con)
    return [dict(r) for r in con.execute("SELECT * FROM order_flow_word WHERE undone_at IS NULL ORDER BY id")]


def _word(con, who, kind, item, sn, **kw):
    ensure_words(con)
    cols = ["kind", "item", "item_norm", "sn", "by", "at"] + list(kw)
    cur = con.execute("INSERT INTO order_flow_word (%s) VALUES (%s)" % (", ".join(cols), ",".join("?" * len(cols))),
                      [kind, item, _norm(item), sn or "", who, now_iso()] + list(kw.values()))
    try:
        _os().audit(con, who, "s926_" + kind, cur.lastrowid, dict(kw, item=item, sn=sn, kit="S926"))
    except Exception:                                             # noqa: BLE001
        pass
    con.commit()
    return cur.lastrowid


# ---------------------------------------------------------------- identity
def _stock_fmt(qty, ps):
    try:
        q, p = int(float(qty or 0)), int(ps or 1)
    except (TypeError, ValueError):
        return str(qty or "")
    if p > 1:
        return "%d:%d" % (q // p, q % p)
    return str(q)


def identity(con):
    """dict(as_on, live={norm: (name, qty, ps)}, dead={norm: name}, partner={norm: [names...]}, pairs=[open rename pairs], answered={norm: 'same'|'two'})."""
    out = dict(as_on="", live={}, dead={}, partner={}, pairs=[], answered={}, dead_list=[], partial=False)
    try:
        days = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot ORDER BY %s DESC LIMIT 2" % D8)]
        if not days:
            return out
        out["as_on"] = days[0]
        for it, q, ps in con.execute("SELECT item, qty, pack_size FROM stock_snapshot WHERE as_on=? AND item IS NOT NULL", (days[0],)):
            out["live"][_norm(it)] = (it, q, ps)
        n_prev = con.execute("SELECT count(*) FROM stock_snapshot WHERE as_on=?", (days[1],)).fetchone()[0] if len(days) > 1 else len(out["live"])
        out["partial"] = len(out["live"]) < 0.8 * int(n_prev or 0)
        if not out["partial"]:                                    # a short closing (a cut export) names NO dead name: nothing is held off ordering by it
            for (it,) in con.execute("SELECT DISTINCT item FROM stock_snapshot WHERE item IS NOT NULL"):
                k = _norm(it)
                if k not in out["live"]:
                    out["dead"][k] = it
    except sqlite3.Error:
        return out
    pt = {}

    def link(a, b):
        for x, y in ((a, b), (b, a)):
            pt.setdefault(_norm(x), [])
            if y not in pt[_norm(x)] and _norm(y) != _norm(x):
                pt[_norm(x)].append(y)
    try:                                                          # the ticked renames (item_alias): old <-> new
        for o, n in con.execute("SELECT old_name, new_name FROM marg_item_rename WHERE undone_at IS NULL AND (done_at IS NOT NULL OR verified_at IS NOT NULL)"):
            link(o, n)
    except sqlite3.Error:
        pass
    try:                                                          # the one name list: Marg partners
        for f, i in con.execute("SELECT form, item FROM med_name WHERE kind='marg' AND state IN ('sure','yes')"):
            link(f, i)
    except sqlite3.Error:
        pass
    for w in words(con):
        if w["kind"] in ("same", "two") and w.get("pair"):
            out["answered"][w["item_norm"]] = w["kind"]
            for p in str(w["pair"]).split("|"):
                out["answered"][_norm(p)] = w["kind"]
            if w["kind"] == "same":
                for p in str(w["pair"]).split("|"):
                    link(w["item"], p)
    try:                                                          # the Marg watch's detected pairs, not yet answered
        seen = set()
        for r in con.execute("SELECT id, item, pair_item, day_from, status FROM marg_hand_change WHERE kind='rename' AND pair_item IS NOT NULL ORDER BY id"):
            a, b = str(r[1]), str(r[2])
            key = tuple(sorted((_norm(a), _norm(b))))
            if key in seen or _norm(a) == _norm(b):
                continue
            seen.add(key)
            ans = out["answered"].get(_norm(a)) or out["answered"].get(_norm(b))
            if ans:
                continue
            old = a if _norm(a) in out["dead"] else (b if _norm(b) in out["dead"] else a)
            new = b if old == a else a
            out["pairs"].append(dict(id=int(r[0]), old=old, new=new, day=str(r[3] or "")[:10], status=r[4],
                                     new_stock=_stock_fmt(*(out["live"].get(_norm(new), ("", 0, 1))[1:])) if _norm(new) in out["live"] else ""))
    except sqlite3.Error:
        pass
    out["partner"] = pt
    out["dead_list"] = sorted(out["dead"].values())
    return out


def dead_norms(con):
    """{item_norm} of names Marg no longer prints AND that no identity joins to a live name -- never suggested on an order (order_s778.hidden
    unions this). A dead name whose partner is known (a ticked rename, the name list, his 'same') stays orderable: the ordering lane keys the
    22 orthotic renames by their old names by design, and the stock lane reads the partner. A pair he called 'two items' is dead for good.
    Fail-soft: set()."""
    try:
        idn = identity(con)
        out = set()
        for k in idn["dead"]:
            joined = any(_norm(p) in idn["live"] for p in idn["partner"].get(k, []))
            if not joined or idn["answered"].get(k) == "two":
                out.add(k)
        return out
    except Exception:                                             # noqa: BLE001
        return set()


def _pair_for(idn, item):
    """The open rename pair naming this item (either side), else None."""
    k = _norm(item)
    for p in idn["pairs"]:
        if _norm(p["old"]) == k or _norm(p["new"]) == k:
            return p
    return None


def _live_qty(idn, name):
    try:
        return int(float(idn["live"].get(_norm(name), ("", 0, 1))[1] or 0))
    except (TypeError, ValueError):
        return 0


def _marg_stock(idn, item):
    """(name Marg prints, 'strips:tabs', dead) for the medicine -- its own name when live, else its live partner's."""
    k = _norm(item)
    if k in idn["live"]:
        n, q, ps = idn["live"][k]
        return n, _stock_fmt(q, ps), False
    for p in idn["partner"].get(k, []):
        if _norm(p) in idn["live"]:
            n, q, ps = idn["live"][_norm(p)]
            return n, _stock_fmt(q, ps), True
    pr = _pair_for(idn, item)
    if pr and _norm(pr["new"]) in idn["live"]:
        n, q, ps = idn["live"][_norm(pr["new"])]
        return n, _stock_fmt(q, ps), True
    return (idn["dead"].get(k) or item), "", k in idn["dead"]


# ---------------------------------------------------------------- shortages
def _line_rows(con, G):
    """Every order line of the flow's window (all groups, done included) with its order: for the chains."""
    out = []
    for g in GROUPS:
        for r in G[g]:
            if r.get("orderless") or not r.get("id"):
                continue
            for l in r["lines"]:
                if not l.get("id"):
                    continue
                out.append(dict(oid=r["id"], lid=l["id"], vendor=r["vendor"], sn=r["sn"], day=r["day"], item=l["item"], qty=l["qty"], came=int(l.get("came") or 0),
                                packs=int(l.get("packs") or 0), state=l["state"], how=l.get("how") or "", group=g, scans=r.get("scans") or [], via=r.get("via") or ""))
    return out


def shortages(con, G=None, now=None):
    """[dict] one per (medicine, dealer) whose newest orders did not come in full. Fields: key, item, sn, vendor, state, n_orders, n_reorders,
    first_day, last_day, came_total, ordered_total, orders=[{day, oid, lid, qty, packs, came, bill, scan}], na (the staff tap row or None),
    word (his newest word row or None), marg_name, marg_stock, dead, pair (open rename question or None), lid/oid (the newest line), suggest
    (a substitute bought meanwhile), other (another dealer who billed it)."""
    now = now or dt.datetime.now()
    if G is not None and isinstance(G.get("_s926"), list):
        return G["_s926"]                                         # computed once per reading of the groups (his page, the Hub line, the staff pages)
    G = G if G is not None else groups(con, now)
    idn = identity(con)
    na = _na_all(con)
    ws = words(con)
    by_ms = {}
    for l in _line_rows(con, G):
        k = (_norm(l["item"]), l["sn"])
        by_ms.setdefault(k, []).append(l)
    mks = marks(con)
    done_sub = {int(m["sub_id"]) for m in mks if m["kind"] in ("sub_ok", "sub_return") and m.get("sub_id")}
    marks_sub = {int(m["line_id"]): m for m in mks if m["kind"] == "sub" and m.get("line_id") and int(m["id"]) not in done_sub}
    settled_lines = {int(m["line_id"]) for m in mks if m["kind"] in ("sub_ok", "sub_return", "closed") and m.get("line_id")}
    wait_marks = {int(m["na_id"]): m for m in mks if m["kind"] == "wait" and m.get("na_id")}
    today = now.date().isoformat()
    out = []
    for (k, sn), ls in by_ms.items():
        ls.sort(key=lambda x: (x["day"], x["oid"]))
        mine = [w for w in ws if w["item_norm"] == k and (w["sn"] in ("", sn))]
        flow_word = any(w["kind"] in ("sub_by", "wait2", "not_now") for w in mine)     # these words settle the hold, not the shortage
        tail = []
        for l in reversed(ls):
            if l["state"] == "came" or (l["packs"] and l["came"] >= l["packs"]):
                break
            if l["state"] == "settled" and not str(l["how"]).startswith("ordered again") and not (flow_word and str(l["how"]) in ("stopped by you", "your word given", "your word: keep ordering")):
                break                                             # a line he settled (closed, came later, substitute OK): the run ends there
            tail.insert(0, l)
        if not tail:
            continue
        newest = tail[-1]
        if int(newest["lid"]) in settled_lines:
            continue                                              # his word on the newest line (substitute OK / to go back / closed): settled
        item = newest["item"]
        word = mine[-1] if mine else None                         # his newest word on this medicine+dealer
        if word and word["kind"] in ("stop", "came", "other2", "sub_by_ok", "sub_by_return", "two") and word["at"] >= newest["day"]:
            if word["kind"] not in ("two",):
                continue                                          # settled by his word after the newest order: gone from every list
        if word and word["kind"] == "not_now" and (word.get("until") or "") >= today:
            continue
        if newest["state"] == "settled" and newest["how"].startswith("ordered again") and len(tail) == 1:
            pass                                                  # a single miss carried onto a later order: the later order's line is the newest
        # the staff tap on the newest line / any line of the run
        n_hit = None
        fs = _forms(con, item, sn)
        for r in na:
            if r["item_norm"] in fs and str(r["at"])[:10] >= tail[0]["day"] and r["status"] == "asked" and not r.get("cleared_at"):
                n_hit = r
        mname, mstock, dead = _marg_stock(idn, item)
        pair = _pair_for(idn, item)
        if dead and not pair and idn["answered"].get(k) == "same" and _live_qty(idn, mname) > 0:
            continue                                              # one medicine under its new name, on the shelf: the box re-reads the orders; not a shortage
        orders = [dict(day=l["day"], oid=l["oid"], lid=l["lid"], qty=l["qty"], packs=l["packs"], came=l["came"], via=l["via"],
                       scan=(l["scans"][0]["scan"] if l["scans"] else None), stamp=(l["scans"][0].get("stamp") if l["scans"] else ""),
                       state=l["state"], how=l["how"], group=l["group"]) for l in tail]
        n_orders = len(tail)
        n_re = n_orders - 1
        sub_mark = marks_sub.get(int(newest["lid"]))
        # state
        if pair:
            st = "rename"
        elif word and word["kind"] == "sub_by":
            st = "sub_arr" if _sub_arrived(con, word) else "sub_way"
        elif word and word["kind"] == "wait2" and (word.get("until") or "") > today:
            st = "wait"
        elif n_hit is not None and (wait_marks.get(int(n_hit["id"])) or {}).get("until", "") > today:
            st = "wait"                                           # the S920 door's wait on the tap row itself
            word = dict(kind="wait", until=wait_marks[int(n_hit["id"])]["until"], at=wait_marks[int(n_hit["id"])]["at"])
        elif sub_mark:
            st = "sub_arr"
        elif newest["state"] == "settled" and str(newest["how"]).startswith("ordered again"):
            st = "wait"                                           # ordered again: on the dealer's next order (today's card); the new order's line takes over
            word = dict(kind="again", until="", at=newest["day"], how=newest["how"])
        elif n_hit is not None:
            st = "oos"
        elif n_re >= KEEPS_AFTER and all(l["came"] == 0 for l in tail[1:]) and _failed(newest):
            st = "keeps"                                          # the newest re-order has failed too (late, short, or carried again) -- not one still on the way
        elif newest["state"] in ("short", "part", "open", "awaiting") and newest["group"] in ("late", "arr", "gap"):
            st = "short"
        else:
            continue                                              # the newest line is settled / on the way: nothing for the list
        if st == "short" and n_re == 0 and not dead:
            continue                                              # one miss: staff's row on the order itself, not his list
        out.append(dict(key="%s|%s" % (k, sn), item=item, sn=sn, vendor=newest["vendor"], state=st, n_orders=n_orders, n_reorders=n_re,
                        first_day=tail[0]["day"], last_day=newest["day"], came_total=sum(l["came"] for l in tail), ordered_total=sum(l["packs"] for l in tail),
                        qty=newest["qty"], orders=orders, na=n_hit, word=word, marg_name=mname, marg_stock=mstock, dead=dead, pair=pair,
                        lid=newest["lid"], oid=newest["oid"], sub_mark=sub_mark,
                        last=(n_hit.get("last_bought") if n_hit else _last_bought(con, item)),
                        other=_other_dealer(con, item, sn), suggest=_suggest_sub(con, item, sn, tail[0]["day"], idn),
                        at=(n_hit["at"] if n_hit else newest["day"]), by=(n_hit.get("by") if n_hit else "")))
    order = {"rename": 0, "keeps": 1, "oos": 2, "sub_arr": 3, "sub_way": 4, "short": 5, "wait": 6}
    out.sort(key=lambda s: (order.get(s["state"], 9), s["first_day"]))
    try:
        G["_s926"] = out
    except Exception:                                             # noqa: BLE001
        pass
    return out


def _failed(l):
    """The order line has failed: did not come / came less / open past its due day / carried onto a later order. Not: on the way, or arrived and
    waiting for Marg's confirmation."""
    if l["state"] in ("short", "part", "oos"):
        return True
    return l["state"] == "open" and l["group"] == "late"


def _last_bought(con, item):
    try:
        return _s7().last_bought(con, item)
    except Exception:                                             # noqa: BLE001
        return ""


def _sub_arrived(con, word):
    """A purchase line of the substitute, from the chosen dealer (or any), dated on/after his word -> its (bill, date), else None."""
    try:
        sub = str(word.get("sub_item") or "")
        fs = _forms(con, sub, word.get("to_sn") or None)
        for it, bill, day, supn in con.execute("SELECT item, bill_no, bill_date, supplier_norm FROM purchase_line WHERE bill_date>=? AND "
                                                "UPPER(COALESCE(direction,'PURCHASE'))='PURCHASE' ORDER BY bill_date DESC, id DESC LIMIT 5000", (str(word["at"])[:10],)):
            if _norm(it) in fs:
                return (bill, day)
    except sqlite3.Error:
        pass
    return None


def _suggest_sub(con, item, sn, since, idn):
    """A medicine bought from the same dealer since the shortage began that was never bought before it -- the substitute in practice (TOLIVANT for TOLTRIS)."""
    try:
        k = _norm(item)
        news = {}
        for it, day in con.execute("SELECT item, MIN(bill_date) FROM purchase_line WHERE supplier_norm=? AND UPPER(COALESCE(direction,'PURCHASE'))='PURCHASE' "
                                   "GROUP BY item", (sn,)):
            news[_norm(it)] = (it, str(day or "")[:10])
        for nk, (it, first) in news.items():
            if nk == k or first < str(since)[:10] or nk in idn["partner"].get(k, []):
                continue
            if nk in idn["dead"]:
                continue
            # same first word (the molecule family as the shop names it) -- a cheap, honest hint; he decides
            if str(it).split(" ")[0][:3].upper() == str(item).split(" ")[0][:3].upper():
                return dict(item=it, first=first)
        return None
    except sqlite3.Error:
        return None


# ---------------------------------------------------------------- his words (the doors)
def _ensure_na(con, who, sh):
    """The 'asked' row for this shortage (a staff tap, or made now by the doctor's own word) -> na id."""
    if sh.get("na"):
        return int(sh["na"]["id"])
    k = _norm(sh["item"])
    r = con.execute("SELECT id FROM order_s778_na WHERE item_norm=? AND status='asked' AND cleared_at IS NULL ORDER BY id DESC LIMIT 1", (k,)).fetchone()
    if r:
        return int(r[0])
    lc = _line_ctx(con, sh["oid"], sh["lid"])
    if not lc:
        return None
    res, st = _na_direct(con, who, lc, sh["lid"])
    return int(res.get("id") or 0) or int(con.execute("SELECT id FROM order_s778_na WHERE item_norm=? ORDER BY id DESC LIMIT 1", (k,)).fetchone()[0])


def _find_sh(con, b):
    item, sn = str(b.get("item") or ""), str(b.get("sn") or "")
    if not item:
        return None
    for s in shortages(con):
        if _norm(s["item"]) == _norm(item) and s["sn"] == sn:
            return s
    return None


def _again_row(con, who, item, qty, to_sn, to_vendor, ref):
    if con.execute("SELECT 1 FROM order_s778_again WHERE kind='s926' AND ref=? AND cleared_at IS NULL AND done_at IS NULL", (ref,)).fetchone():
        return False
    con.execute("INSERT INTO order_s778_again (supplier_norm, vendor, item, qty, pack_size, packing, rate_p, kind, ref, src_day, from_sn, at, by) "
                "VALUES (?,?,?,?,1,'',0,'s926',?,?,?,?,?)", (to_sn, to_vendor, item, max(_int(qty), 1), ref, dt.date.today().isoformat(), to_sn, now_iso(), who))
    return True


def _vendor_of(con, sn):
    r = con.execute("SELECT vendor FROM purchase_order WHERE supplier_norm=? ORDER BY id DESC LIMIT 1", (sn,)).fetchone()
    if r:
        return r[0]
    r = con.execute("SELECT supplier FROM purchase_line WHERE supplier_norm=? ORDER BY id DESC LIMIT 1", (sn,)).fetchone()
    return r[0] if r else sn


def act_s926(con, who, b, do):
    """His doors on a shortage. Returns (dict, status) or None when `do` is not ours."""
    if do not in ("same", "two", "sub_by", "other2", "again_sh", "wait2", "not_now", "stop", "came", "sub_by_ok", "sub_by_return"):
        return None
    ensure_words(con)
    item, sn = str(b.get("item") or ""), str(b.get("sn") or "")
    if not item:
        return dict(ok=False, error="bad_request", message="Which medicine?"), 400
    if do in ("same", "two"):
        return _answer_pair(con, who, b, do)
    sh = _find_sh(con, b)
    if not sh:
        return dict(ok=False, error="gone", message="This shortage is no longer open."), 409
    S7 = _s7()
    if do == "sub_by":
        sub, to_sn = str(b.get("sub_item") or "").strip(), str(b.get("to_sn") or sn)
        if not sub:
            return dict(ok=False, error="bad_request", message="Name the substitute."), 400
        tv = _vendor_of(con, to_sn)
        _again_row(con, who, sub, sh["qty"], to_sn, tv, "sub:%s|%s" % (_norm(item), sn))
        nid = _ensure_na(con, who, sh)
        if nid:
            r = con.execute("SELECT status FROM order_s778_na WHERE id=?", (nid,)).fetchone()
            if r and r[0] == "asked":
                S7.na_answer(con, who, nid, "stop")           # the old medicine: never suggested again until a bill brings it back
        try:
            con.execute("UPDATE order_item_rule SET note=COALESCE(note,'')||' | substituted by '||? WHERE item_norm=?", (sub, _norm(item)))
        except sqlite3.Error:
            pass
        _word(con, who, "sub_by", item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"], na_id=nid, sub_item=sub, to_sn=to_sn, to_vendor=tv)
        return dict(ok=True, item=item, sub=sub, vendor=tv), 200
    if do == "other2":
        to_sn = str(b.get("to_sn") or "")
        if not to_sn or to_sn == sn:
            return dict(ok=False, error="bad_request", message="Pick the other dealer."), 400
        tv = _vendor_of(con, to_sn)
        _again_row(con, who, item, sh["qty"], to_sn, tv, "other:%s|%s" % (_norm(item), sn))
        nid = _ensure_na(con, who, sh)
        if nid:
            r = con.execute("SELECT status FROM order_s778_na WHERE id=?", (nid,)).fetchone()
            if r and r[0] == "asked":
                S7.na_answer(con, who, nid, "keep")
        _word(con, who, "other2", item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"], na_id=nid, to_sn=to_sn, to_vendor=tv)
        return dict(ok=True, item=item, vendor=tv), 200
    if do == "again_sh":
        r, st = act(con, who, dict(do="again", oid=sh["oid"], lid=sh["lid"]))
        if st == 200:
            _word(con, who, "again_sh", item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"])
        return r, st
    if do == "wait2":
        nid = _ensure_na(con, who, sh)
        until = (dt.date.today() + dt.timedelta(days=WAIT_DAYS)).isoformat()
        if nid:
            _mark(con, who, "wait", na_id=nid, item=item, vendor=sh["vendor"], until=until)
        _word(con, who, "wait2", item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"], na_id=nid, until=until)
        return dict(ok=True, until=until), 200
    if do == "not_now":
        nid = _ensure_na(con, who, sh)                            # the hold stays 'asked': off the order sheet AND off his list for 30 days, then back to him
        until = (dt.date.today() + dt.timedelta(days=NOT_NOW_DAYS)).isoformat()
        _word(con, who, "not_now", item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"], na_id=nid, until=until)
        return dict(ok=True, until=until), 200
    if do == "stop":
        nid = _ensure_na(con, who, sh)
        if not nid:
            return dict(ok=False, error="gone"), 409
        r = con.execute("SELECT status FROM order_s778_na WHERE id=?", (nid,)).fetchone()
        if r and r[0] == "asked":
            res, st = S7.na_answer(con, who, nid, "stop")
            if st != 200:
                return res, st
        _word(con, who, "stop", item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"], na_id=nid)
        return dict(ok=True, item=item), 200
    if do == "came":
        note = str(b.get("note") or "")[:200]
        t = now_iso()
        nid = sh["na"]["id"] if sh.get("na") else None
        if nid:
            con.execute("UPDATE order_s778_na SET status=CASE WHEN status='asked' THEN 'came' ELSE status END, cleared_at=?, cleared_why=? WHERE id=?",
                        (t, "owner: %s" % (note or "it came / we have it"), int(nid)))
        for o in sh["orders"]:
            con.execute("UPDATE order_carry SET dropped_at=?, dropped_by='owner_came' WHERE from_line_id=? AND done_at IS NULL AND dropped_at IS NULL", (t, int(o["lid"])))
        _word(con, who, "came", item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"], na_id=nid, note=note)
        return dict(ok=True, item=item), 200
    if do in ("sub_by_ok", "sub_by_return"):
        w = sh.get("word")
        if not w or w["kind"] != "sub_by":
            return dict(ok=False, error="gone", message="No substitute waits here."), 409
        if do == "sub_by_ok":
            try:                                                  # the substitute inherits the old medicine's ordering rule, if one stood
                old = con.execute("SELECT rule, value FROM order_s778_na n JOIN order_item_rule r ON r.item_norm=n.item_norm WHERE n.id=?", (int(w.get("na_id") or 0),)).fetchone()
                pr = con.execute("SELECT prev_rule, prev_value FROM order_s778_na WHERE id=?", (int(w.get("na_id") or 0),)).fetchone()
                if pr and pr[0] and pr[0] != "never":
                    con.execute("INSERT INTO order_item_rule (item_norm, item, rule, value, set_by, set_at, note) VALUES (?,?,?,?,?,?,?) ON CONFLICT(item_norm) DO NOTHING",
                                (_norm(w["sub_item"]), w["sub_item"], pr[0], pr[1], who, now_iso(), "S926: inherited from %s" % item))
            except sqlite3.Error:
                pass
        _word(con, who, do, item, sn, vendor=sh["vendor"], order_id=sh["oid"], line_id=sh["lid"], na_id=w.get("na_id"), sub_item=w.get("sub_item"), to_sn=w.get("to_sn"))
        return dict(ok=True), 200
    return None


def _answer_pair(con, who, b, do):
    """The identity question: 'same' joins the two names everywhere (item_alias, the one name list, the hand-change rows; then the order lines
    re-read against the bills and the out-of-stock holds cleared by them); 'two' remembers them as two items."""
    idn = identity(con)
    item = str(b.get("item") or "")
    pr = None
    for p in idn["pairs"]:
        if int(b.get("pair") or 0) == p["id"] or _norm(p["old"]) == _norm(item) or _norm(p["new"]) == _norm(item):
            pr = p
            break
    if not pr:
        return dict(ok=False, error="gone", message="No open rename question for this medicine."), 409
    old, new = pr["old"], pr["new"]
    t = now_iso()
    notes = []
    if do == "same":
        try:
            import item_alias as IA                               # noqa: PLC0415 -- beside this file; its shape, our row
            IA.ensure(con)
            if not con.execute("SELECT 1 FROM marg_item_rename WHERE old_name=? AND new_name=? AND undone_at IS NULL", (old, new)).fetchone():
                con.execute("INSERT INTO marg_item_rename (old_name, new_name, old20, old27, new20, new27, family, planned_by, planned_at, done_by, done_at, "
                            "verified_at, verified_as_on, verified_k20, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (old, new, IA.clip(old, IA.SALE_CLIP), IA.clip(old, IA.PURCHASE_CLIP), IA.clip(new, IA.SALE_CLIP), IA.clip(new, IA.PURCHASE_CLIP),
                             "", "marg watch", pr["day"] or t, "marg", t, t, pr["day"] or t[:10], IA._Kf(new),
                             "S926: renamed in Marg %s, found by the Marg watch, the owner's 'same medicine' %s" % (pr["day"], t[:10])))
                rid = con.execute("SELECT id FROM marg_item_rename WHERE old_name=? AND new_name=? ORDER BY id DESC LIMIT 1", (old, new)).fetchone()[0]
                try:
                    IA._event(con, rid, "accepted", who, t, seen_name=new, as_on=pr["day"], note="S926 owner: same medicine")
                except Exception:                                 # noqa: BLE001
                    pass
                try:
                    notes += IA._follow(con, {"old_name": old, "new_name": new}, who, t)
                except Exception as e:                            # noqa: BLE001
                    notes.append("follow: %s" % str(e)[:60])
        except Exception as e:                                    # noqa: BLE001
            notes.append("item_alias: %s" % str(e)[:80])
        try:
            import med_names as MN                                # noqa: PLC0415
            MN.ensure(con)
            MN._put(con, "marg", "", new, old, "yes", dict(kit="S926", by=who, why="owner: same medicine, renamed in Marg %s" % pr["day"]), dt.datetime.now())
        except Exception as e:                                    # noqa: BLE001
            notes.append("med_names: %s" % str(e)[:80])
    try:
        con.execute("UPDATE marg_hand_change SET status='closed', status_at=?, rec_kind=?, rec_note=? WHERE kind='rename' AND status='open' AND "
                    "((item=? AND pair_item=?) OR (item=? AND pair_item=?))",
                    (t, "rename_same" if do == "same" else "two_items", "S926 owner %s: %s" % (who, "same medicine" if do == "same" else "two items"), old, new, new, old))
    except sqlite3.Error as e:
        notes.append("hand change: %s" % str(e)[:60])
    _word(con, who, do, old, "", pair="%s|%s" % (old, new), note="; ".join(notes)[:400])
    con.commit()
    done = dict(lines=0, holds=0)
    if do == "same":
        try:
            import porders as PO                                  # noqa: PLC0415 -- the order lines re-read against the bills, under the joined name
            done["lines"] = int(PO.detect_supplies(con) or 0)
        except Exception as e:                                    # noqa: BLE001
            notes.append("detect: %s" % str(e)[:60])
        try:
            done["holds"] = int(_s7().clear_by_bills(con) or 0)
        except Exception as e:                                    # noqa: BLE001
            notes.append("clear: %s" % str(e)[:60])
        try:                                                      # an out-of-stock ask on either name, while the live name holds stock: not a shortage
            idn2 = identity(con)
            nm_, stock, _dead = _marg_stock(idn2, old)
            qty = 0
            try:
                qty = int(float(idn2["live"].get(_norm(nm_), ("", 0, 1))[1] or 0))
            except (TypeError, ValueError):
                qty = 0
            if qty > 0:
                for k in (_norm(old), _norm(new)):
                    n = con.execute("UPDATE order_s778_na SET status='came', cleared_at=?, cleared_why=? "
                                    "WHERE item_norm=? AND cleared_at IS NULL AND status='asked'",             # a 'stop' is his own word: left standing
                                    (t, "owner: same medicine as %s, Marg stock %s (S926)" % (nm_, stock), k)).rowcount
                    done["holds"] += int(n or 0)
                con.execute("UPDATE order_carry SET dropped_at=?, dropped_by='owner_came' WHERE done_at IS NULL AND dropped_at IS NULL AND item IN (?,?)", (t, old, new))
                con.commit()
        except sqlite3.Error as e:
            notes.append("asks: %s" % str(e)[:60])
        try:
            if hasattr(_s7(), "forms") and _g() is not None:      # the per-request forms memo must forget the old answer
                setattr(_g(), "s778_forms", {})
        except Exception:                                         # noqa: BLE001
            pass
    return dict(ok=True, old=old, new=new, lines=done["lines"], holds=done["holds"], notes=notes), 200


def _g():
    try:
        from flask import g as _fg                                # noqa: PLC0415
        return _fg
    except Exception:                                             # noqa: BLE001
        return None


# ---------------------------------------------------------------- the pickers (his substitute / another dealer)
def items_like(con, q, limit=12):
    """Medicines the shop buys or holds whose name contains q: [{item, stock, last}] -- the newest closing's names first, then purchase lines."""
    q = str(q or "").strip().upper()
    idn = identity(con)
    out, seen = [], set()
    for k, (name, qty, ps) in sorted(idn["live"].items(), key=lambda kv: str(kv[1][0] or "")):
        name = str(name or "")
        if not name or (q and q not in name.upper()):
            continue
        out.append(dict(item=name, stock=_stock_fmt(qty, ps), last=""))
        seen.add(k)
        if len(out) >= limit:
            return out
    try:
        for it, day in con.execute("SELECT item, MAX(bill_date) FROM purchase_line WHERE UPPER(item) LIKE ? AND UPPER(COALESCE(direction,'PURCHASE'))='PURCHASE' "
                                   "GROUP BY item ORDER BY 2 DESC LIMIT 40", ("%" + q + "%",)):
            if _norm(it) in seen or _norm(it) in idn["dead"]:
                continue
            out.append(dict(item=it, stock="", last=str(day or "")[:10]))
            seen.add(_norm(it))
            if len(out) >= limit:
                break
    except sqlite3.Error:
        pass
    return out


def dealers_like(con, q, limit=12):
    q = str(q or "").strip().upper()
    out, seen = [], set()
    try:
        for sn, v, d in con.execute("SELECT supplier_norm, vendor, MAX(created_at) FROM purchase_order GROUP BY supplier_norm ORDER BY 3 DESC"):
            if not sn or sn in seen or (q and q not in str(v or "").upper() and q not in sn.upper()):
                continue
            out.append(dict(sn=sn, vendor=v, short=_short(v), last=str(d or "")[:10]))
            seen.add(sn)
            if len(out) >= limit:
                break
    except sqlite3.Error:
        pass
    return out


# ---------------------------------------------------------------- his page: the section (English), per mock-up v1.1 (22-Nov 10:3x, his OK 10:37)
SH_TITLE = {"rename": ("c-blue", "Marg renamed it? — your one tap"), "keeps": ("c-red", "Dealer keeps not sending — came to you by itself"),
            "oos": ("c-amb", "Dealer says out of stock — your word"), "sub_arr": ("c-blue", "Substitute arrived — OK it or send it back"),
            "sub_way": ("c-grey", "Substitute on its way"), "short": ("c-amb", "Came short, carried once — staff's row"), "wait": ("c-grey", "Waiting on your word's date")}
SH_ORDER = ("rename", "keeps", "oos", "sub_arr", "sub_way", "wait", "short")


def _b926(label, body, cls=""):
    import json as _j                                             # noqa: PLC0415
    return '<button class="%s" onclick=\'ofTwo(this,%s)\'>%s</button>' % (cls, esc(_j.dumps(body)), esc(label))


def _ledger_box(name, idn_partner=None):
    """Stock & ledger inline: the Item ledger page in a frame of the row (same origin), loaded when opened; the link to the full page beside."""
    import urllib.parse as _u                                     # noqa: PLC0415
    u = "/finance/sanjeevni/ledger?k=" + _u.quote(str(name))
    extra = ""
    if idn_partner:
        u2 = "/finance/sanjeevni/ledger?k=" + _u.quote(str(idn_partner))
        extra = ' · <a href="%s" target="_blank" rel="noopener">the old name\'s ledger →</a>' % esc(u2)
    return ('<details class="ledg" ontoggle="ofLedg(this)"><summary><b>Stock &amp; ledger — %s</b> ▸ <span class="small">opens here; '
            '<a href="%s" target="_blank" rel="noopener" onclick="event.stopPropagation()">open the full page →</a>%s</span></summary>'
            '<iframe data-src="%s" title="Item ledger" style="width:100%%;height:560px;border:1px solid #dde3e9;border-radius:8px;background:#fff"></iframe></details>') % (
        esc(name), esc(u), extra, esc(u))


def _sh_fact(s):
    days = ", ".join(ddmm(o["day"]) for o in s["orders"])
    came = "nothing came on any bill" if s["came_total"] == 0 else "%d of %d came" % (s["came_total"], s["ordered_total"])
    if s["n_orders"] == 1:
        head = "Ordered %s — %s." % (days, came)
    else:
        head = "Ordered %d times (%s) — %s." % (s["n_orders"], days, came)
    tap = ""
    if s.get("na"):
        tap = ' <span class="who">%s %s: dealer says out of stock.</span>' % (esc((s["na"].get("by") or "staff").title()), esc(_hm(s["na"]["at"])))
    stock = ""
    if s["marg_stock"]:
        stock = " Marg stock <b>%s</b>%s." % (esc(s["marg_stock"]), (" (as <b>%s</b> — Marg no longer prints the ordered name)" % esc(s["marg_name"])) if s["dead"] else "")
    return head + tap + stock


def _sh_history(s):
    h = "<table><tr><th>Order</th><th>Ordered</th><th>Came (bill)</th><th>Bill</th><th>What happened</th></tr>"
    for o in s["orders"]:
        bill = ('<a href="/scanapp/bills/%d/file" target="_blank" rel="noopener"><img loading="lazy" src="/scanapp/bills/%d/thumb" alt="" style="width:36px;height:46px;object-fit:cover;border-radius:3px;vertical-align:middle"></a> %s'
                % (int(o["scan"]), int(o["scan"]), esc(o.get("stamp") or ""))) if o.get("scan") else '<span class="small">no scan</span>'
        what = o["how"] or {"short": "did not come", "part": "came less", "open": "awaited", "awaiting": "arrived — Marg will confirm", "oos": "out of stock (tap)", "sub": "substitute came"}.get(o["state"], o["state"])
        h += "<tr><td>%s · %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(ddmm(o["day"])), esc(o["via"] or "—"), esc(o["qty"]), o["came"], bill, esc(what))
    return h + "</table>"


def _sh_buttons(s):
    b = dict(item=s["item"], sn=s["sn"])
    st = s["state"]
    if st == "rename":
        p = s["pair"]
        return ('<div class="sugg">⚠ The Marg watch saw <b>%s</b> renamed to <b>%s</b> in Marg on %s%s. If it is the same medicine, this row is not a shortage: '
                'the orders are re-read against the bills under the new name, the two ledgers are joined, and the ordering list stops suggesting the old name.</div>'
                '<div class="btns">%s%s</div>') % (esc(p["old"]), esc(p["new"]), esc(ddmm(p["day"])),
                                                   (" — stock today <b>%s</b>" % esc(p["new_stock"])) if p.get("new_stock") else "",
                                                   _b926("Yes — same medicine", dict(b, do="same", pair=p["id"]), "p"), _b926("No — two items", dict(b, do="two", pair=p["id"])))
    if st == "sub_way":
        w = s["word"]
        return '<div class="word">Your word %s: substitute <b>%s</b> from %s — on that dealer\'s next order. %s is not suggested again.</div>' % (
            esc(ddmm(w["at"])), esc(w.get("sub_item") or ""), esc(_short(w.get("to_vendor") or w.get("to_sn") or "")), esc(s["item"]))
    if st == "sub_arr":
        if s.get("word") and s["word"]["kind"] == "sub_by":
            w = s["word"]
            return ('<div class="word">Your word %s: substitute <b>%s</b>. It has come on a bill.</div><div class="btns">%s%s</div>' % (
                esc(ddmm(w["at"])), esc(w.get("sub_item") or ""), _b926("OK — keep as the substitute", dict(b, do="sub_by_ok"), "p"),
                _b926("Not OK — return it", dict(b, do="sub_by_return"), "w")))
        m = s.get("sub_mark") or {}
        return '<div class="btns">%s%s</div>' % (_b926("Substitute OK", dict(do="sub_ok", sub=m.get("id")), "p"), _b926("Not OK — return", dict(do="sub_return", sub=m.get("id")), "w"))
    if st == "wait":
        w = s["word"] or {}
        if w.get("kind") == "again":
            return '<div class="small">Ordered again — on the dealer\'s next order (%s). The new order\'s line takes over from here.</div>' % esc(w.get("how") or "")
        return '<div class="small">Waiting until %s, then back to you by itself.</div>' % esc(ddmm(w.get("until") or ""))
    h = ""
    if s.get("suggest"):
        h += '<div class="sugg">💡 <b>%s</b> was first bought from this dealer on %s, while this was missing — the substitute? Pick it under <b>Substitute</b>.</div>' % (
            esc(s["suggest"]["item"]), esc(ddmm(s["suggest"]["first"])))
    h += '<div class="btns">'
    h += _b926("Order again from %s" % _short(s["vendor"]), dict(b, do="again_sh"), "p")
    h += '<button class="s" onclick="ofPick(this,%s,\'sub\')">Substitute: choose…</button>' % esc(__import__("json").dumps(b))
    if s.get("other"):
        h += _b926("Order from %s" % _short(s["other"][1]), dict(b, do="other2", to_sn=s["other"][0]), "p")
    h += '<button onclick="ofPick(this,%s,\'dealer\')">Order from another dealer…</button>' % esc(__import__("json").dumps(b))
    h += _b926("Wait — ask again next week", dict(b, do="wait2"))
    h += _b926("Not needed now (30 days)", dict(b, do="not_now"))
    h += _b926("Stop ordering it", dict(b, do="stop"), "w")
    h += '<button onclick="ofCame(this,%s)">It came / we have it…</button>' % esc(__import__("json").dumps(b))
    h += '</div><div class="pick" style="display:none"></div>'
    return h


def _sh_row(s, open_=False):
    chip = {"rename": ('c-blue', "Marg renamed it?"), "keeps": ('c-red', "not delivered %d times" % s["n_orders"]), "oos": ('c-amb', "%s missing" % (
        ("%d of %d" % (s["ordered_total"] - s["came_total"], s["ordered_total"])) if s["came_total"] else "not delivered %d time%s" % (s["n_orders"], "" if s["n_orders"] == 1 else "s"))),
            "sub_arr": ('c-blue', "substitute arrived"), "sub_way": ('c-grey', "substitute on its way"), "short": ('c-amb', "came short"), "wait": ('c-grey', "waiting")}[s["state"]]
    need = {"rename": "your one tap", "keeps": "your word needed", "oos": "your word needed", "sub_arr": "OK the substitute", "sub_way": "", "short": "", "wait": ""}[s["state"]]
    dd = "%s · %s a time · since %s · last bought %s" % (esc(_short(s["vendor"])), esc(s["qty"] or "—"), esc(ddmm(s["first_day"])), esc(ddmm(s["last"]) if s["last"] else "—"))
    return ('<details class="row sh"%s><summary><div><div class="dn">%s <span class="chip %s">%s</span>%s</div><div class="dd">%s</div><div class="fact">%s</div></div>'
            '<div>%s</div></summary><div class="body" style="grid-template-columns:1fr">%s%s%s</div></details>') % (
        " open" if open_ else "", esc(s["item"]), chip[0], esc(chip[1]), (' <span class="chip c-amb">%s</span>' % esc(need)) if need else "", dd, _sh_fact(s),
        "", _sh_history(s), _ledger_box(s["marg_name"] if s["marg_stock"] else s["item"], s["item"] if s["dead"] else None), _sh_buttons(s))


SH_CSS = """<style>
.of .sh>summary{grid-template-columns:1fr auto}.of .fact{font-size:13.5px;margin-top:2px}.of .who{color:#8a5a00}
.of .sugg{background:#ece4ff;border:1px solid #c9b8f3;border-radius:8px;padding:6px 10px;font-size:13.5px;margin-top:6px}
.of .word{background:#e3f6ec;border-radius:8px;padding:6px 10px;font-size:13.5px;margin-top:6px}
.of button.s{background:#5a2ea6;color:#fff;border-color:#5a2ea6}
.of .pick{margin-top:8px;background:#fff;border:1px solid #b8c1cb;border-radius:8px;padding:8px 10px;max-width:560px}
.of .pick input{font:inherit;width:100%;box-sizing:border-box;padding:6px 8px;border:1px solid #b8c1cb;border-radius:6px}
.of .pick .opt{padding:5px 6px;border-radius:6px;cursor:pointer;display:flex;justify-content:space-between;font-size:13.5px}.of .pick .opt:hover{background:#eef3fb}.of .pick .opt.sel{background:#dbe9ff}
.of .ledg{margin-top:8px}.of .ledg>summary{font-size:13.5px}
</style>"""

SH_JS = """<script>
function ofLedg(d){var f=d.querySelector('iframe');if(d.open&&f&&!f.src)f.src=f.dataset.src;}
function ofPick(b,body,kind){var box=b.closest('.body').querySelector('.pick');box.style.display='block';
 box.innerHTML='<div class="small">'+(kind=='sub'?'Substitute for '+body.item+' — a medicine we buy or hold; type to search':'Order '+body.item+' from — type the dealer')+'</div><input placeholder="type…"><div class="opts"></div><div class="btns"><button class="p" disabled>Yes</button><button onclick="this.closest(\\'.pick\\').style.display=\\'none\\'">No</button></div>';
 var inp=box.querySelector('input'),opts=box.querySelector('.opts'),yes=box.querySelector('button.p'),sel=null,t=null;
 function load(){var q=inp.value;fetch('%s/api/flow/'+(kind=='sub'?'items':'dealers')+'?q='+encodeURIComponent(q),{credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){
  opts.innerHTML=(j.rows||[]).map(function(o){return '<div class="opt" data-v="'+(kind=='sub'?o.item:o.sn).replace(/"/g,'&quot;')+'"><span>'+(kind=='sub'?o.item:o.vendor)+'</span><span class="small">'+(kind=='sub'?(o.stock?'stock '+o.stock:(o.last?'bought '+o.last:'')):(o.last?'last order '+o.last:''))+'</span></div>'}).join('')||'<div class="small">nothing matches — '+(kind=='sub'?'type the full new name and press Yes':'no such dealer')+'</div>';
  opts.querySelectorAll('.opt').forEach(function(o){o.onclick=function(){opts.querySelectorAll('.opt').forEach(function(x){x.classList.remove('sel')});o.classList.add('sel');sel=o.dataset.v;yes.disabled=false;yes.textContent='Yes — '+(kind=='sub'?'substitute with ':'order from ')+o.children[0].textContent;}});
  if(kind=='sub'&&q.trim().length>=3){yes.disabled=false;if(!sel){yes.textContent='Yes — substitute with "'+q.trim().toUpperCase()+'" (new name)';}}});}
 inp.oninput=function(){sel=null;yes.disabled=true;yes.textContent='Yes';clearTimeout(t);t=setTimeout(load,250)};load();inp.focus();
 yes.onclick=function(){var v=sel||(kind=='sub'?inp.value.trim().toUpperCase():'');if(!v)return;var payload=kind=='sub'?Object.assign({},body,{do:'sub_by',sub_item:v}):Object.assign({},body,{do:'other2',to_sn:v});
  if(kind=='sub'){if(box.querySelector('select'))return;var ask=document.createElement('div');ask.className='small';ask.style.marginTop='6px';ask.innerHTML='From which dealer? <select></select> <button class="p">Yes, place it</button>';box.appendChild(ask);var s=ask.querySelector('select');
   fetch('%s/api/flow/dealers?q=',{credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){(j.rows||[]).forEach(function(o){var op=document.createElement('option');op.value=o.sn;op.textContent=o.vendor;if(o.sn==body.sn)op.selected=true;s.appendChild(op)})});
   ask.querySelector('button').onclick=function(){payload.to_sn=s.value;ofTwo(this,payload);};return;}
  ofTwo(yes,payload);};}
function ofCame(b,body){var box=b.closest('.body').querySelector('.pick');box.style.display='block';box.innerHTML='<div class="small">It came / we have it — where? (one line)</div><input placeholder="e.g. came on bill 4100 as V FER 500 · counted 25 on the shelf"><div class="btns"><button class="p">Yes — close it</button><button onclick="this.closest(\\'.pick\\').style.display=\\'none\\'">No</button></div>';
 var inp=box.querySelector('input');box.querySelector('button.p').onclick=function(){ofTwo(this,Object.assign({},body,{do:'came',note:inp.value}));};inp.focus();}
</script>""" % (P, P)


def team_table_s926(con, rows, mode="you", G=None):
    """His section: the shortages grouped by state (rename · keeps · oos · substitute · waiting · short). mode 'staff' -> the staff words."""
    if mode != "you":
        return team_table_s920(rows, mode)
    try:
        sh = shortages(con, G)
    except Exception as e:                                        # noqa: BLE001 -- his page must render; the S920 list is the fallback
        print("S926 team_table failed: %r -- the S920 team list" % (e,), file=__import__("sys").stderr)
        return team_table_s920(rows, mode)
    h = [SH_CSS]
    if not sh:
        h.append('<div class="small" style="padding:8px 0">Nothing waits for your word. A medicine re-ordered twice and still not come comes here by itself.</div>')
    for st in SH_ORDER:
        rs = [s for s in sh if s["state"] == st]
        if not rs and st in ("sub_way", "short", "wait"):
            continue
        cls, title = SH_TITLE[st]
        h.append('<details class="grp"%s><summary><span class="chip %s">%d</span> %s%s</summary>%s</details>' % (
            " open" if rs and st in ("rename", "keeps", "oos", "sub_arr") else "", cls, len(rs), esc(title), AR,
            "".join(_sh_row(s, open_=(st in ("rename",))) for s in rs) or '<div class="small" style="padding:8px 16px">None.</div>'))
    h.append(SH_JS)
    return "".join(h)


def sh_counts(sh):
    c = dict(need=0, rename=0, keeps=0, oos=0, sub=0, wait=0, total=len(sh))
    for s in sh:
        if s["state"] == "rename":
            c["rename"] += 1
        elif s["state"] == "keeps":
            c["keeps"] += 1
        elif s["state"] == "oos":
            c["oos"] += 1
        elif s["state"] in ("sub_arr", "sub_way"):
            c["sub"] += 1
        elif s["state"] == "wait":
            c["wait"] += 1
    c["need"] = c["rename"] + c["keeps"] + c["oos"] + sum(1 for s in sh if s["state"] == "sub_arr")
    return c


# ---------------------------------------------------------------- staff: his word as an instruction (Roman Hindi for reception, Devanagari for Darpan)
def staff_word(s, dev=False):
    """One line the staff read on the team row: what the doctor decided, or that his word is awaited."""
    st, w = s["state"], s.get("word") or {}
    if st == "rename":
        return ("Doctor sahab se naam ka sawaal baaki (%s / %s)" % (s["pair"]["old"], s["pair"]["new"])) if not dev else ("डॉक्टर साहब से नाम का सवाल बाकी (%s / %s)" % (s["pair"]["old"], s["pair"]["new"]))
    if st == "sub_way":
        return ("Doctor sahab: substitute %s — %s ke agle order pe (ab %s order nahi karna)" % (w.get("sub_item"), _short(w.get("to_vendor") or ""), s["item"])) if not dev else (
            "डॉक्टर साहब: substitute %s — %s के अगले ऑर्डर पर (अब %s ऑर्डर नहीं करना)" % (w.get("sub_item"), _short(w.get("to_vendor") or ""), s["item"]))
    if st == "sub_arr":
        return "Substitute aa gaya — Doctor sahab ki OK baaki" if not dev else "Substitute आ गया — डॉक्टर साहब की OK बाकी"
    if st == "wait":
        if w.get("kind") == "again":
            return "Dobara order ho gaya — dealer ke agle order pe" if not dev else "दोबारा ऑर्डर हो गया — डीलर के अगले ऑर्डर पर"
        return ("Doctor sahab: %s tak intezaar, phir list pe wapas" % ddmm(w.get("until") or "")) if not dev else ("डॉक्टर साहब: %s तक इंतज़ार, फिर लिस्ट पर वापस" % ddmm(w.get("until") or ""))
    if st in ("keeps", "oos"):
        return "Doctor sahab ka faisla baaki" if not dev else "डॉक्टर साहब का फ़ैसला बाकी"
    return ""


def team_s926(con, na=None, mk=None, G=None):
    """The team list every page reads (his, reception's, Darpan's): one row per shortage, the old row shape + state, word, marg_stock, n_orders."""
    try:
        sh = shortages(con, G)
    except Exception as e:                                        # noqa: BLE001
        print("S926 shortages failed: %r -- the S920 team list" % (e,), file=__import__("sys").stderr)
        return team_s920(con, na, mk)
    out = []
    for s in sh:
        if s["state"] == "short":
            continue
        out.append(dict(kind=("sub" if s["state"] in ("sub_arr", "sub_way") else "oos"), id=(s["na"]["id"] if s.get("na") else 0), item=s["item"], vendor=s["vendor"],
                        sn=s["sn"], qty=(s["na"].get("qty") if s.get("na") else s["qty"]) or "", at=s["at"], last=s["last"] or "", by=s["by"] or "",
                        wait=(s["word"].get("until") if s["state"] == "wait" else ""), other=s["other"], state=s["state"], n_orders=s["n_orders"],
                        marg_stock=s["marg_stock"], marg_name=s["marg_name"], word_hi=staff_word(s), word_dev=staff_word(s, dev=True),
                        first_day=s["first_day"], line=s["lid"]))
    return out
