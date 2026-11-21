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
# =============================================================================
import datetime as dt
import html as _html
import re
import sqlite3

VERSION = "1.0"
KIT = "S920_PURCHASE_FLOW_1"
P = "/finance/porders"
WAIT_DAYS = 7                                                     # 'Wait — order next week'
DDL = ("CREATE TABLE IF NOT EXISTS order_flow_mark (id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN "
       "('closed','chase','sub','sub_ok','sub_return','wait','other')), order_id INTEGER, line_id INTEGER, na_id INTEGER, sub_id INTEGER, "
       "item TEXT, vendor TEXT, sub_item TEXT, until TEXT, to_sn TEXT, by TEXT NOT NULL, at TEXT NOT NULL, undone_at TEXT)",)
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
                           chase=bool(om.get("chase")), age=(now.date() - dt.date.fromisoformat(s["day"])).days))
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
            out.append(dict(kind="sub", id=m["id"], item="%s → %s" % (m.get("item") or "", m.get("sub_item") or ""), vendor=m.get("vendor") or "",
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
        if r.get("chase"):
            return '<span class="small">Chase sent to reception.</span>'
        return _btn("Chase now (to reception)", dict(do="chase", oid=r["id"]), "p")
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
            esc(t["item"]), esc(_short(t["vendor"])), esc(t["qty"]), esc(ddmm(t["at"])), esc(ddmm(t["last"]) if t["last"] else "—"), cls, esc(word), a)
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

    @bp.route(P + "/api/flow/healthz")
    def flow_healthz():
        return jsonify(ok=True, module="order_flow", version=VERSION, kit=KIT)

    app.register_blueprint(bp)
    return bp
