#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s936_v1.py -- kit S936_RECOUNT_SITTING (23-Nov-2026, Sanjeevni session 506).
    python3 -B make_s936_v1.py <from dir> <to dir>
Reads the LIVE FROM bytes (S934's TO: stock_watch 048b51df, stock_figure d7fac10c, stockmatch.py e459af2a, stockmatch.html 2a985d94) and writes
the TO files by EXACT anchors -- each anchor must occur exactly the stated number of times, or nothing is written.
  D1046 (the owner, 23-Nov 11:18): a count short of the expected figure by about a delivery received in the days before it is HELD as a recount
        (status 'recount'): never the shelf base (stock_figure.points), no loss line, no trace, out of the month's leakage and the watch, put on
        Count now by itself with the question "was the carton of bill N on the shelf?"; the count that answers it closes it ('recounted') and is
        judged as any count -- never held itself.
  D1047 (the owner, 23-Nov 11:41): one bill number per sitting -- Darpan's Abhi ginti card takes the last sale bill ONCE at the top, carries it
        to every item saved in it, asks again only on his tap 'Sale hui?'; the server takes the sitting's bill when an item comes without one."""
import hashlib
import os
import sys

FROM_PINS = {"stock_watch.py": "048b51df91a5dc8babbbc6bca983d5de", "stock_figure.py": "d7fac10cec56b0db170da3d40326a0c6",
             "stockmatch.py": "e459af2a05a0451d81e6c6fc0c62082f", "stockmatch.html": "2a985d94217b05cdb9b5e657db3b1290"}


def rep(text, old, new, n=1, label=""):
    c = text.count(old)
    if c != n:
        raise SystemExit("ANCHOR %s: found %d time(s), expected %d:\n%s" % (label, c, n, old[:300]))
    return text.replace(old, new)


# ============================================================================================================== stock_figure.py
def make_figure(t):
    t = rep(t, 'KIT = "S934_COUNT_NOW"', 'KIT = "S936_RECOUNT_SITTING"', 1, "F1 kit")
    t = rep(t, "# v1.8 S934 (a Count now placed to its last sale bill)",
            "# v1.9 S936 (a count held for a recount is never a base), v1.8 S934 (a Count now placed to its last sale bill)", 1, "F1b kit note")
    t = rep(t, """            for nm, item, at, qty, src, bs, pid, lb in con.execute("SELECT item_norm, item, at, qty_units, source, %s, id, %s FROM stock_point WHERE source<>? AND COALESCE(status,'')<>'superseded' "
                                                                   "ORDER BY at, id" % (bcol, lcol), (FULL,)):""",
            """            for nm, item, at, qty, src, bs, pid, lb in con.execute("SELECT item_norm, item, at, qty_units, source, %s, id, %s FROM stock_point WHERE source<>? "
                                                                   "AND COALESCE(status,'') NOT IN ('superseded','recount','recounted') "   # S936 (D1046): a count held for a recount is never a base
                                                                   "ORDER BY at, id" % (bcol, lcol), (FULL,)):""", 1, "F2 points")
    return t


# ============================================================================================================== stock_watch.py
SETTINGS_NEW = '''    dict(key="count.recount_tol_pct", label="Recount: a count short by about a fresh delivery (tolerance, % of the delivery)", kind="pct", default="25", seed=None,
         lo=5, hi=50,                                          # S936 (D1046)
         hint="S936, the owner 23-Nov: a count short of the expected figure by about a delivery received in the days before it is more likely a missed "
              "carton than a loss -- it is HELD for a recount (not the shelf figure, no loss line, nothing on the order list) and put on Darpan's Count now "
              "with the question whether that carton was on the shelf. 'About' = the shortfall within this share of the delivery."),
    dict(key="count.recount_days", label="Recount: a delivery counts as fresh for (days)", kind="int", default="5", seed=None, lo=1, hi=15,
         hint="S936: a delivery tapped, scanned or dated within this many days before a count is a fresh delivery for the recount rule."),
    dict(key="count.sitting_minutes", label="Count now: one bill number for a sitting of (minutes)", kind="int", default="60", seed=None, lo=5, hi=240,
         hint="S936, the owner 23-Nov: Darpan keys the last sale bill once for a sitting; an item he saves within this many minutes of his last "
              "Count now with a bill takes that bill unless he taps 'Sale hui?' for a new one."),
    dict(key="count.evening_hour",'''

HELPERS = r'''

# ------------------------------------------------------------------ S936 (23-Nov-2026): THE RECOUNT RULE (D1046) and ONE BILL PER SITTING (D1047)
#  THE OWNER, 23-Nov 11:18 (TRAMATEE P: Saturday's 9:4 counted without Mannat's 40 strips became the shelf, booked a false loss line and put 50
#  strips on Monday's order list on "on hand 4:0"): "confusing ... might also spoil the purchase order generation". A count is evidence, not the
#  truth. A count short of the expected figure by ABOUT A FRESH DELIVERY (an arrival tapped or scan-tied, its scanned bill's quantity, or a Marg
#  purchase line, within count.recount_days before the count; the shortfall within count.recount_tol_pct of the delivery) is HELD: status
#  'recount' -- never the shelf base (stock_figure.points leaves it out, so the order engine, the stock of record and every judgment never see
#  it), no loss line, no trace, out of the month's leakage and the watch list; ONE Count-now ask is opened by itself (by 'system', recount_of =
#  the held point) with the question for Darpan. The next count of the item answers it: the held point becomes 'recounted' (any line or trace
#  of it voided) and the new count is judged as any count -- never held itself (a recount that is short again is a loss by name).
#  THE OWNER, 23-Nov 11:41: "one bill per sitting" -- Darpan counts many items at one bill. The card takes the bill once and carries it; the
#  server takes the sitting's bill (_s936_sitting_bill: his newest Count now with a bill today within count.sitting_minutes) when an item comes
#  with none and the page did not say 'no bill' (a page from before the kit, or a lost field).
RECOUNT_ST = ("recount", "recounted")


def _s936_columns(con):
    """S936: stock_watch_ask.recount_of (the held point a system recount asks about), .why (English), .why_hi (Darpan's question);
    stock_point.recount_for (the held point this count answered -- such a count, and any correction of it, is never held). Additive."""
    for t, c, ty in (("stock_watch_ask", "recount_of", "INTEGER"), ("stock_watch_ask", "why", "TEXT"), ("stock_watch_ask", "why_hi", "TEXT"),
                     ("stock_point", "recount_for", "INTEGER")):
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(%s)" % t).fetchall()}
            if cols and c not in cols:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (t, c, ty))
        except sqlite3.Error:
            pass


def _s936_recount_for(con, pid):
    """The held point a count answered (stock_point.recount_for), or None."""
    try:
        r = con.execute("SELECT recount_for FROM stock_point WHERE id=?", (int(pid),)).fetchone()
        return int(r[0]) if (r and r[0] is not None) else None
    except sqlite3.Error:
        return None


def _s936_open_recount_ask(con, item):
    """(ask id, held point id) of the item's open recount, or None."""
    try:
        r = con.execute("SELECT id, recount_of FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL AND recount_of IS NOT NULL ORDER BY id LIMIT 1",
                        (norm_name(item),)).fetchone()
        return (int(r[0]), int(r[1])) if r else None
    except sqlite3.Error:
        return None


def _s936_hm(ts):
    s = str(ts or "")
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if len(s) >= 16 else dmy(s)


def _s936_close_recount(con, rc, pid, ts, who):
    """The count `pid` answers the open recount rc = (ask, held point): the ask closed as counted; the held point 'recounted' (its note names
    the new point); any loss line of it voided and any trace of it closed. Inside the caller's transaction (no commit)."""
    aid, held = rc
    con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='counted' WHERE id=? AND done_at IS NULL", (ts, aid))
    r0 = con.execute("SELECT item_norm FROM stock_point WHERE id=?", (int(pid),)).fetchone()
    if r0:                                                     # any other open RECOUNT of the item is answered too; his own asks close by their callers (his notice stays, review 2 finding 3)
        con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='counted' WHERE item_norm=? AND done_at IS NULL AND recount_of IS NOT NULL", (ts, r0[0]))
    con.execute("UPDATE stock_point SET recount_for=? WHERE id=?", (held, int(pid)))
    _s936_touch(con)
    r = con.execute("SELECT note FROM stock_point WHERE id=?", (held,)).fetchone()
    con.execute("UPDATE stock_point SET status='recounted', note=? WHERE id=? AND status IN ('recount','recounted')",
                ("recounted %s -- %s" % (_s936_hm(ts), str((r[0] if r else "") or "")), held))
    con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why='recounted' WHERE point_id=? AND void_at IS NULL", (ts, held))
    con.execute("UPDATE stock_trace SET status='fixed', seen_by='S936 recount', seen_at=? WHERE status<>'fixed' AND json_extract(findings_json,'$.point_id')=?",
                (ts, held))
    _audit(con, "recount_answered", dict(ask_id=aid, held_point=held, new_point=pid), who, pid)


def _s936_withdraw_for(con, held_pid, who):
    """A recount asked about a count that is being CORRECTED (correct_roster) is not the correction's to answer: withdrawn. No commit."""
    for (aid,) in con.execute("SELECT id FROM stock_watch_ask WHERE recount_of=? AND done_at IS NULL", (int(held_pid),)).fetchall():
        con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='withdrawn' WHERE id=?", (now_iso(), aid))
        _audit(con, "recount_withdrawn", dict(ask_id=aid, held_point=int(held_pid), why="the count was corrected"), who, aid)


def _s936_is_recount_point(con, pid):
    """True when the point answered a recount (stock_point.recount_for, or its ask_id is a system recount) -- such a count is never held."""
    if _s936_recount_for(con, pid) is not None:
        return True
    try:
        r = con.execute("SELECT a.recount_of FROM stock_point p JOIN stock_watch_ask a ON a.id=p.ask_id WHERE p.id=?", (int(pid),)).fetchone()
        return bool(r and r[0])
    except sqlite3.Error:
        return False


def _s936_match(con, sp, item, at_iso, short_units, pack=1, pid=None):
    """The fresh delivery a shortfall is about the size of, or None. Deliveries: the item's arrivals tapped from count.recount_days before the
    count -- and never before the base count the point is judged on (a delivery the last count already saw is no missed carton) -- up to its
    moment (the tapped quantity AND its bill's, when known), and Marg's purchase lines of the item dated in those days (the spine). 'About':
    |shortfall - delivery| within count.recount_tol_pct of the delivery (at least half a strip / pc of slack). The closest wins. A shortfall
    under one strip / pc is never a carton. Fail-soft: None."""
    try:
        short = float(short_units or 0)
        pk = max(1, int(pack or 1))
        if short < pk:
            return None
        S = settings(con)
        tol, days = float(S["recount_tol_pct"]) / 100.0, int(S["recount_days"])
        at = str(at_iso or now_iso())[:19]
        lo = (dt.datetime.fromisoformat(at) - dt.timedelta(days=days)).replace(microsecond=0).isoformat()
        base_day = None
        try:                                                   # the review (S506, finding 7): the window starts no earlier than the base count
            SF = _sf()
            b = SF.base(con, item, SF.Ctx(con, sp), exclude_id=pid)
            if b is not None:
                base_day = str(b.get("day") or b.get("at") or "")[:10] or None
                if str(b.get("at") or "")[:19] > lo:
                    lo = str(b["at"])[:19]
        except Exception:                                     # noqa: BLE001
            pass
        cands = []
        keys = {pad_norm(item[:27]), pad_norm(item)}
        try:
            rows = con.execute("SELECT l.item, l.supplied, l.pack_size, l.arrived_at, l.billed_qty, l.billed_bill_no, l.billed_date, o.vendor FROM purchase_order_line l "
                               "JOIN purchase_order o ON o.id=l.order_id WHERE l.arrived_at IS NOT NULL AND l.arrived_at>=? AND l.arrived_at<=? AND l.supplied>0",
                               (lo, at)).fetchall()
        except sqlite3.Error:
            rows = []
        for nm, supplied, ps, arrived, bq, bno, bdate, vendor in rows:
            if pad_norm(str(nm)[:27]) not in keys and pad_norm(nm) not in keys:
                continue
            ps_ = float(ps or 1)
            for u in sorted({float(supplied or 0) * ps_, float(bq or 0) * ps_}):
                if u > 0:
                    cands.append(dict(units=u, bill=str(bno or ""), vendor=str(vendor or ""), day=str(bdate or arrived or "")[:10]))
        if sp is not None and getattr(sp, "ok", False):
            for p in sp.purchases(item, lo[:10], at[:10], incl_from=True):
                if p.get("direction") == "RETURN":
                    continue
                if base_day and str(p.get("date") or "")[:10] <= base_day:   # review 2 (MUST 2): a Marg line dated the base count's day is in that count
                    continue
                u = float(p.get("units") or 0)
                if u > 0:
                    cands.append(dict(units=u, bill=str(p.get("bill") or ""), vendor=str(p.get("supkey") or ""), day=str(p.get("date") or "")[:10]))
        best = None
        for c in cands:
            d = abs(short - c["units"])
            if d <= max(tol * c["units"], float(pk) / 2.0) and (best is None or d < best[0]):
                best = (d, c)
        if best is None:
            return None
        c = dict(best[1])
        bill = re.sub(r"^[Aa]0*", "", c["bill"].strip()) if c["bill"].strip() else ""
        day = dmy(c["day"])[:5] if c["day"] else ""
        who_when = ", ".join(x for x in (c["vendor"], day) if x)
        if bill:
            c["what"] = "bill %s (%s)" % (bill, who_when) if who_when else "bill %s" % bill
            c["what_hi"] = "bill %s (%s) ka maal" % (bill, who_when) if who_when else "bill %s ka maal" % bill
        else:
            c["what"] = "the delivery of %s" % (who_when or "these days")
            c["what_hi"] = "%s ka naya maal" % (who_when or "abhi aaya")
        c["why"] = "recount: was the carton of %s on the shelf?" % c["what"]
        c["why_hi"] = "Dobara giniye: pichhli ginti mein %s shayad gina nahi gaya. Uska carton bhi dekhkar poori ginti likhiye." % c["what_hi"]
        c["bill"] = bill
        return c
    except Exception:                                         # noqa: BLE001 -- the count is never refused for it
        return None


def _s936_hold_row(con, pid, H, note=None):
    """The point HELD for a recount: status 'recount', its note says why (first, so the owner's page shows it). No commit."""
    txt = "held for a recount -- short by about %s, not a loss" % H["what"]
    if note and str(note).startswith("Count now, to bill"):  # S934's prefix stays first (stock_check reads it)
        txt = str(note) + " · " + txt
    elif note:
        txt += " · " + str(note)
    con.execute("UPDATE stock_point SET status='recount', settled_at=NULL, note=? WHERE id=?", (txt, int(pid)))
    _s936_touch(con)
    _audit(con, "point_held_for_recount", dict(point_id=int(pid), delivery=dict(units=H.get("units"), bill=H.get("bill"), vendor=H.get("vendor"), day=H.get("day"))),
           "system", pid)
    return txt


def _s936_open_recount(con, P, who):
    """After a held count: ONE Count-now ask by itself (by 'system', recount_of the held point, the question for Darpan) -- unless one is
    already open for the item. Called by each caller AFTER its own ask closing (answer_roster, darpan_point, correct_roster, answer_now) and
    by _s934_settle. No commit. Fail-soft."""
    try:
        if not P or P.get("status") != "recount" or not P.get("hold"):
            return None
        if _s936_open_recount_ask(con, P["item"]) is not None:
            return None
        H = P["hold"]
        cur = con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at, mode, recount_of, why, why_hi) VALUES (?,?,?,?,?,?,?,?)",
                          (norm_name(P["item"]), P["item"], "system", now_iso(), "now", int(P["id"]), H.get("why") or "", H.get("why_hi") or ""))
        _audit(con, "recount_asked", dict(item=P["item"], held_point=int(P["id"]), why=H.get("why")), who or "system", cur.lastrowid)
        return int(cur.lastrowid)
    except sqlite3.Error:
        return None


def _s936_touch(con):
    """A held or recounted count changes a row's status, not stock_point's newest id: one 'count.' setting row is touched so the stock of
    record's fingerprint (it reads the count.% rows) rebuilds the record. Not a setting anyone sets: settings() never reads it. No commit."""
    try:
        con.execute("INSERT INTO setting (key, value, note) VALUES ('count._s936_held_at', ?, 'S936: moves when a count is held or recounted (the record rebuilds)') "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (dt.datetime.now().isoformat(),))
    except sqlite3.Error:
        pass


def _s936_sitting(con, who):
    """D1047: (bill, seconds since it was keyed) of the sitting -- the last sale bill `who` keyed with a Count now TODAY, within
    count.sitting_minutes of now; (None, None) otherwise (another person, another day, an older sitting)."""
    try:
        if not who:
            return None, None
        S = settings(con)
        lo = (dt.datetime.now() - dt.timedelta(minutes=int(S["sitting_minutes"]))).replace(microsecond=0).isoformat()
        r = con.execute("SELECT last_bill, at FROM stock_point WHERE by=? AND at>=? AND substr(at,1,10)=? AND COALESCE(last_bill,'')<>'' ORDER BY at DESC, id DESC LIMIT 1",
                        (who, lo, today().isoformat())).fetchone()
        if not r:
            return None, None
        try:
            age = max(0, int((dt.datetime.now() - dt.datetime.fromisoformat(str(r[1])[:19])).total_seconds()))
        except ValueError:
            age = int(S["sitting_minutes"]) * 60
        return _s934_bill_no(r[0]), age
    except sqlite3.Error:
        return None, None


def _s936_sitting_bill(con, who):
    """D1047: the sitting's bill number, or None."""
    return _s936_sitting(con, who)[0]
'''

NOW_VIEW_OLD_START = "def now_view(con, sp=None):\n"
NOW_VIEW_OLD_END = "        return dict(items=[], last_day=\"\", last_no=None)\n"
NOW_VIEW_NEW = '''def now_view(con, sp=None, who=None):
    """Darpan's 'Abhi ginti' card: the open Count-now asks, oldest first, with the last bill known (a hint, never a default). S936: a recount
    ask carries its question (recount, why_hi); sitting_bill = the bill this person keyed in this sitting (D1047), carried to every item."""
    try:
        ensure(con)
        sp = sp or Spine()
        items = []
        for aid, item, at, rof, why_hi in con.execute("SELECT id, item, at, recount_of, why_hi FROM stock_watch_ask WHERE done_at IS NULL AND mode='now' ORDER BY id").fetchall():
            info = item_info(con, sp, item)
            pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
            name = info.get("item") or item
            items.append(dict(id=aid, item=name, pack=pack, packing=packing, whole_hi=_qwm().whole_word(packing, None, name, pack, "hi"),
                              at=at, at_text=stamp(at), recount=bool(rof), why_hi=(why_hi or "")))
        ld, last = _s934_last_known(con)
        S = settings(con)
        sb, age = _s936_sitting(con, who)
        return dict(items=items, last_day=(dmy(ld) if ld else ""), last_no=last, sitting_bill=sb, sitting_age_s=age, sitting_minutes=int(S["sitting_minutes"]))
    except Exception:                                         # noqa: BLE001
        return dict(items=[], last_day="", last_no=None, sitting_bill=None, sitting_age_s=None, sitting_minutes=60)
'''


def make_watch(t):
    t = rep(t, 'VERSION = "1.10"\nKIT = "S934_COUNT_NOW"', 'VERSION = "1.11"\nKIT = "S936_RECOUNT_SITTING"', 1, "W1 kit")
    t = rep(t, "# v1.10 S934 (Count now, placed to the bill)",
            "# v1.11 S936 (a count short by a fresh delivery held for a recount; one bill per sitting), v1.10 S934 (Count now, placed to the bill)", 1, "W1b kit note")
    t = rep(t, '    dict(key="count.evening_hour",', SETTINGS_NEW, 1, "W2 settings")
    t = rep(t, '                evening_hour=max(0, min(23, num("count.evening_hour", 17, int))),\n',
            '                evening_hour=max(0, min(23, num("count.evening_hour", 17, int))),\n'
            '                recount_tol_pct=max(5.0, min(50.0, num("count.recount_tol_pct", 25.0))),            # S936 (D1046)\n'
            '                recount_days=max(1, min(15, num("count.recount_days", 5, int))),\n'
            '                sitting_minutes=max(5, min(240, num("count.sitting_minutes", 60, int))),             # S936 (D1047)\n', 1, "W3 settings()")
    t = rep(t, "    _s934_columns(con)\n\n\ndef _audit(", "    _s934_columns(con)\n    _s936_columns(con)\n\n\ndef _audit(", 1, "W4 ensure")
    t = rep(t, """    q += " AND status<>'superseded'"                          # S502: a replaced count is never picked""",
            """    q += " AND status NOT IN ('superseded','recount','recounted')"   # S502: a replaced count is never picked; S936: nor a count held for a recount""", 1, "W5 last_point")
    t = rep(t, "                expected=_UNSET, expected_as_on=None, commit=True, basis=None):\n",
            "                expected=_UNSET, expected_as_on=None, commit=True, basis=None, hold=True):\n", 1, "W6 write_point sig")
    t = rep(t, "    info = item_info(con, sp, item)\n    item = info[\"item\"]\n    if expected is _UNSET:\n",
            "    info = item_info(con, sp, item)\n    item = info[\"item\"]\n"
            "    rc = _s936_open_recount_ask(con, item)                    # S936 (D1046): this count answers the item's open recount -- and is never held itself\n"
            "    if rc is not None:\n        hold = False\n"
            "    if expected is _UNSET:\n", 1, "W7 write_point rc")
    t = rep(t, "    pid = int(cur.lastrowid)\n    P = dict(id=pid, item=item, pack=info[\"pack\"],",
            "    pid = int(cur.lastrowid)\n"
            "    if rc is not None:\n"
            "        _s936_close_recount(con, rc, pid, ts, who)            # S936: the held count it answers -- 'recounted', any line of it voided\n"
            "    P = dict(id=pid, item=item, pack=info[\"pack\"],", 1, "W8 write_point close rc")
    t = rep(t, """    else:
        lp = last_point(con, norm_name(item))
        since = (lp["at"][:10] if lp and lp["id"] != pid else (E["as_on"] or (today() - dt.timedelta(days=30)).isoformat()))
        allow, sold = allowance_units(con, item, info["pack"], since, sp)
        if abs(gap) <= allow:
""", """    else:
        H = _s936_match(con, sp, item, ts, -gap, info["pack"], pid) if (hold and basis in ("shelf", "marg")) else None   # S936 (D1046)
        lp = last_point(con, norm_name(item))
        since = (lp["at"][:10] if lp and lp["id"] != pid else (E["as_on"] or (today() - dt.timedelta(days=30)).isoformat()))
        allow, sold = allowance_units(con, item, info["pack"], since, sp)
        if H is not None and abs(gap) > allow:                 # S936: short by about a fresh delivery -- HELD for a recount: no base, no loss line, no trace
            _s936_hold_row(con, pid, H, note)
            P.update(status="recount", hold=H)
            P["verdict"] = "%s short -- about %s: held for a recount, not a loss" % (P["gap_text"], H["what"])
            P["verdict_hi"] = "%s kam -- %s shayad gina nahi gaya. Dobara ginti 'Abhi ginti' mein aayegi." % (P["gap_hi"], H["what_hi"])
            _s936_open_recount(con, P, who)                    # in the same transaction as the held count (the review, finding 8)
        elif abs(gap) <= allow:
""", 1, "W9 write_point hold")
    t = rep(t, """    _audit(con, "point", dict(item=item, qty=float(qty_units), source=source, expected=E["expected"], gap=gap, status=status,""",
            """    P["answered_recount"] = rc[0] if rc is not None else None   # S936
    _audit(con, "point", dict(item=item, qty=float(qty_units), source=source, expected=E["expected"], gap=gap, status=P.get("status") or status,""", 1, "W10 write_point audit")
    t = rep(t, """    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE roster_id=? AND done_at IS NULL", (now_iso(), r[0]))
    con.commit()
""", """    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE roster_id=? AND done_at IS NULL AND recount_of IS NULL", (now_iso(), r[0]))   # S936: a fresh recount stays
    _s936_open_recount(con, P, who)                            # S936: idempotent (write_point opened it)
    con.commit()
""", 1, "W11 answer_roster")
    t = rep(t, """        con.execute("UPDATE stock_point SET status='superseded' WHERE id=?", (old[0],))
        P = write_point(""", """        _s936_withdraw_for(con, old[0], who)                   # S936: a recount asked about the old count is not this correction's to answer
        rf = _s936_recount_for(con, old[0])                    # S936 (the review, finding 2): the old count answered a recount -- its correction is never held
        con.execute("UPDATE stock_point SET status='superseded' WHERE id=?", (old[0],))
        P = write_point(""", 1, "W12 correct_roster withdraw")
    t = rep(t, "commit=False, silent=True, basis=(old[7] or (\"marg\" if old[3] is not None else None)))",
            "commit=False, silent=True, hold=(rf is None), basis=(old[7] or (\"marg\" if old[3] is not None else None)))", 1, "W12b correct_roster hold")
    t = rep(t, """        con.execute("UPDATE stock_spot_roster SET qty_units=?, point_id=?, answered_at=? WHERE id=?", (q, P["id"], ts, r[0]))
""", """        con.execute("UPDATE stock_spot_roster SET qty_units=?, point_id=?, answered_at=? WHERE id=?", (q, P["id"], ts, r[0]))
        if rf is not None:
            con.execute("UPDATE stock_point SET recount_for=? WHERE id=?", (rf, P["id"]))
        _s936_open_recount(con, P, who)                        # S936: idempotent
""", 1, "W13 correct_roster recount")
    t = rep(t, """    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), norm_name(info["item"])))
    con.commit()
""", """    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL AND recount_of IS NULL", (now_iso(), norm_name(info["item"])))   # S936
    _s936_open_recount(con, P, who)                            # S936: idempotent (write_point opened it)
    con.commit()
""", 1, "W14 darpan_point")
    t = rep(t, """        if not con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL", (nm,)).fetchone():""",
            """        if not con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL AND recount_of IS NULL", (nm,)).fetchone():   # S936""", 1, "W14b s894 select")
    t = rep(t, """        con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), nm))""",
            """        con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL AND recount_of IS NULL", (now_iso(), nm))   # S936""", 1, "W14c s894 close")
    t = rep(t, """P = write_point(con, info["item"], qty_units, "darpan", who, note="gadbad: " + t, sp=sp, silent=True)""",
            """P = write_point(con, info["item"], qty_units, "darpan", who, note="gadbad: " + t, sp=sp, silent=True, hold=False)   # S936: his flag is never held""", 1, "W15 gadbad")
    t = rep(t, """WHERE substr(at,1,7)=? AND gap_units<0 AND source<>'full_count' AND status<>'superseded'", (ym,)):   # S502""",
            """WHERE substr(at,1,7)=? AND gap_units<0 AND source<>'full_count' AND status NOT IN ('superseded','recount','recounted')", (ym,)):   # S502; S936""", 1, "W16 month_leak")
    t = rep(t, "FROM stock_point WHERE item_norm=? AND status<>'superseded' ORDER BY at DESC LIMIT 3\"",
            "FROM stock_point WHERE item_norm=? AND status NOT IN ('superseded','recount','recounted') ORDER BY at DESC LIMIT 3\"", 1, "W17 watch pts")
    t = rep(t, "WHERE item_norm=? AND at>=? AND at<? AND status<>'superseded'\"",
            "WHERE item_norm=? AND at>=? AND at<? AND status NOT IN ('superseded','recount','recounted')\"", 1, "W18 watch trend")
    t = rep(t, """            if st_ == "awaits_sales":""", """            if st_ == "recount":                               # S936 (D1046)
                w = "%s -- short by about a fresh delivery, held for a recount (not a loss)" % qw(float(q), pack, packing, name)
            elif st_ == "recounted":
                w = "%s -- was held, recounted since" % qw(float(q), pack, packing, name)
            elif st_ == "awaits_sales":""", 1, "W19 count_day")
    t = rep(t, "notices=notices(con, \"darpan\"), is_spot_day=R[\"is_spot_day\"], now=now_view(con, sp))",
            "notices=notices(con, \"darpan\"), is_spot_day=R[\"is_spot_day\"], now=now_view(con, sp, who))", 1, "W20 darpan_view")
    a = t.find(NOW_VIEW_OLD_START)
    b = t.find(NOW_VIEW_OLD_END, a)
    if a < 0 or b < 0 or t.count(NOW_VIEW_OLD_START) != 1:
        raise SystemExit("ANCHOR W21 now_view")
    t = t[:a] + NOW_VIEW_NEW + t[b + len(NOW_VIEW_OLD_END):]
    t = rep(t, "def answer_now(con, ask_id, qty_units, last_bill, who, sp=None):\n",
            "def answer_now(con, ask_id, qty_units, last_bill, who, sp=None, no_bill=False):\n", 1, "W22 answer_now sig")
    t = rep(t, """    n = None
    if str(last_bill or "").strip():
        ok, n, msg = _s934_check_bill(con, last_bill)""", """    n = None
    sitting = False
    if not str(last_bill or "").strip() and not no_bill:      # S936 (D1047): an item saved without a bill in a sitting takes the sitting's bill
        sb = _s936_sitting_bill(con, who)
        if sb is not None:
            last_bill, sitting = str(sb), True
    if str(last_bill or "").strip():
        ok, n, msg = _s934_check_bill(con, last_bill)""", 1, "W23 answer_now sitting")
    t = rep(t, """    _audit(con, "count_now", dict(ask_id=r[0], item=P["item"], qty=float(qty_units), last_bill=n), who, P["id"])
    con.commit()
""", """    _audit(con, "count_now", dict(ask_id=r[0], item=P["item"], qty=float(qty_units), last_bill=n, sitting=sitting), who, P["id"])
    _s936_open_recount(con, P, who)                            # S936: a count by its time held for a recount
    con.commit()
""", 1, "W24 answer_now recount")
    t = rep(t, """    tail = "" if n is not None else " Bill number nahi likha -- samay se milaan hua."
""", """    tail = (" (is baithak ka bill %d)" % n if sitting else "") if n is not None else " Bill number nahi likha -- samay se milaan hua."   # S936
""", 1, "W25 answer_now tail")
    t = rep(t, """                if abs(gap) > allow:
                    mrp = sp.mrp_p(item) if sp.ok else None""", """                H = None if _s936_is_recount_point(con, pid) else _s936_match(con, sp, item, at, -gap, info["pack"], pid)   # S936 (D1046)
                if abs(gap) > allow and H is not None:       # a bill-placed count short by about a fresh delivery: HELD, a recount by itself
                    _s936_hold_row(con, pid, H, (con.execute("SELECT note FROM stock_point WHERE id=?", (pid,)).fetchone() or [None])[0])
                    _s936_open_recount(con, dict(id=pid, item=item, status="recount", hold=H), "system")
                elif abs(gap) > allow:
                    mrp = sp.mrp_p(item) if sp.ok else None""", 1, "W26 _s934_settle")
    t = rep(t, """    r = con.execute("SELECT id, COALESCE(mode,'next'), roster_id, at FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL ORDER BY id LIMIT 1", (nm,)).fetchone()
""", """    if _s936_open_recount_ask(con, info["item"]) is not None:   # S936 (review 2, note 7): a recount stays on Abhi ginti with its question
        return True, "%s is already on Darpan's screen (a recount the system asked for)." % info["item"], 200
    r = con.execute("SELECT id, COALESCE(mode,'next'), roster_id, at FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL ORDER BY id LIMIT 1", (nm,)).fetchone()
""", 1, "W28 ask recount guard")
    t = rep(t, """    r = con.execute("SELECT id, item, roster_id, at FROM stock_watch_ask WHERE id=? AND done_at IS NULL", (aid,)).fetchone()
    if not r:
        return False, "That ask is no longer open.", 404
""", """    r = con.execute("SELECT id, item, roster_id, at FROM stock_watch_ask WHERE id=? AND done_at IS NULL", (aid,)).fetchone()
    if not r:
        return False, "That ask is no longer open.", 404
    rof = con.execute("SELECT recount_of FROM stock_watch_ask WHERE id=?", (aid,)).fetchone()
    if rof and rof[0] is not None:                             # S936 (review 2, finding 6): the held count would stay held for good
        return False, "%s is a recount the system asked for -- Darpan's next count of it settles it." % r[1], 409
""", 1, "W29 withdraw recount guard")
    t = rep(t, "\n\nif __name__ == \"__main__\":\n", HELPERS + "\n\nif __name__ == \"__main__\":\n", 1, "W27 helpers")
    return t


# ============================================================================================================== stockmatch.py
def make_sm(t):
    t = rep(t, 'VERSION = "1.3"\nKIT = "S934_COUNT_NOW"', 'VERSION = "1.4"\nKIT = "S936_RECOUNT_SITTING"', 1, "M0 kit")
    t = rep(t, "# v1.3 S934 (Abhi ginti)", "# v1.4 S936 (one bill per sitting; a recount's question), v1.3 S934 (Abhi ginti)", 1, "M0b kit note")
    t = rep(t, 'print("S934 stockmatch mounted v%s"', 'print("S936 stockmatch mounted v%s"', 1, "M0c mount line")
    t = rep(t, """def _sw_view(con):
    try:
        return _sw().darpan_view(con)""", """def _sw_view(con, who=None):
    try:
        return _sw().darpan_view(con, who or "darpan")            # S936 (D1047): the person -- his sitting's bill""", 1, "M1 _sw_view")
    t = rep(t, """    st["watch"] = _sw_view(con)  """, """    st["watch"] = _sw_view(con, me)  """, 1, "M2 state")
    t = rep(t, """    ok, msg, code, P = sw.answer_now(con, aid, q, str(b.get("last_bill") or "").strip(), (u or {}).get("user") or "")""",
            """    ok, msg, code, P = sw.answer_now(con, aid, q, str(b.get("last_bill") or "").strip(), (u or {}).get("user") or "", no_bill=bool(b.get("no_bill")))   # S936""",
            1, "M3 api_now")
    return t


# ============================================================================================================== stockmatch.html
CARD_OLD_A = """  h+='<div class="card" style="border:2px solid #b4541a"><h2>Abhi ginti <span class="tag">'+NW.items.length+'</span></h2><div class="muted">Doctor sahab ne abhi ginne ko kaha hai. Shelf par jitna hai utna likhiye, aur us waqt ka <b>aakhri sale bill number</b> (Marg mein dekhiye)'+(NW.last_no?' &middot; '+esc(NW.last_day)+' ka aakhri bill '+NW.last_no+' tha':'')+'.</div>';
  NW.items.forEach(r=>{
   h+='<div class="line"><div class="nm">'+esc(r.item)+'</div><div class="muted">'+esc(r.packing||'')+(r.pack>1?' &middot; ek patte mein '+r.pack:'')+' &middot; kaha '+esc(r.at_text)+'</div>'
    +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(r.pack,r.whole_hi,"n"+r.id)
    +' <label>Aakhri bill no. <input id="nb'+r.id+'" inputmode="numeric" style="width:6em;font-size:17px;padding:8px"></label>'
    +'<span class="btn ok" onclick="nowSave('+r.id+','+r.pack+')">Bhej do</span></div></div>';
  });"""
CARD_NEW_A = """  if(SB===null) SB=sbLoad(NW.sitting_bill,NW.sitting_minutes,NW.sitting_age_s);   // S936 (D1047): ONE bill for the sitting, carried to every item
  if(SB&&!sbFresh()) SB='';                                     // the sitting is over: the old bill is never shown or sent again (the review, MUST 1)
  h+='<div class="card" style="border:2px solid #b4541a"><h2>Abhi ginti <span class="tag">'+NW.items.length+'</span></h2><div class="muted">Doctor sahab ne abhi ginne ko kaha hai. Shelf par jitna hai utna likhiye.</div>'
   +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap;margin:8px 0"><label><b>Aakhri sale bill no.</b> (Marg mein dekhiye) <input id="nbS" inputmode="numeric" value="'+esc(SB||'')+'" oninput="sbSet(this.value)" style="width:6em;font-size:17px;padding:8px"></label>'
   +(NW.last_no?' <span class="muted">'+esc(NW.last_day)+' ka aakhri bill '+NW.last_no+' tha</span>':'')
   +' <span class="btn" onclick="sbSale()">Sale hui? Naya bill likhiye</span></div>'
   +'<div class="muted">Yeh bill number is baithak ki har ginti ke saath jayega. Beech mein sale ho jaye to upar ka button dabaiye.</div>';
  NW.items.forEach(r=>{
   h+='<div class="line"><div class="nm">'+esc(r.item)+(r.recount?' <span class="tag">dobara ginti</span>':'')+'</div>'
    +(r.recount&&r.why_hi?'<div class="muted" style="color:#b4541a"><b>'+esc(r.why_hi)+'</b></div>':'')
    +'<div class="muted">'+esc(r.packing||'')+(r.pack>1?' &middot; ek patte mein '+r.pack:'')+' &middot; kaha '+esc(r.at_text)+'</div>'
    +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(r.pack,r.whole_hi,"n"+r.id)
    +' <span class="muted">Bill: <b class="sbShow">'+esc(SB||'\\u2014')+'</b></span>'
    +'<span class="btn ok" onclick="nowSave('+r.id+','+r.pack+')">Bhej do</span></div></div>';
  });"""
SAVE_OLD = """async function nowSave(aid, pack){
 if(BUSY)return; const body={ask_id:aid};
 if(!readBoxes(pack,"n"+aid,body)){MSG={kind:"err",title:"Ginti likhiye",lines:[]};render();return;}
 const nb=el("nb"+aid); body.last_bill=(nb&&nb.value)||"";
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/now"+Q,body); after(j,"\\u2713 Save ho gaya",[esc(j.saved.message)]);}"""
SAVE_NEW = """let SB=null, SBM=60, SBT=0;                                    // S936 (D1047): the sitting's bill on this phone, with the time it was last set or used
function sbKey(){const d=new Date();return 's936_bill_'+d.getFullYear()+'-'+(d.getMonth()+1)+'-'+d.getDate();}
function sbLoad(srv,mins,age){SBM=+mins||60;let o=null;try{o=JSON.parse(sessionStorage.getItem(sbKey())||'null');}catch(e){o=null;}
 if(o&&typeof o==='object'&&(Date.now()-(+o.t||0))<=SBM*60000){SBT=+o.t||0;return o.b==='-'?'':String(o.b||'');}
 SBT=Date.now()-Math.max(0,(+age||0))*1000;return srv?String(srv):'';}   // review 2 (MUST 1): the server's bill keeps the clock of when it was keyed
function sbFresh(){return (Date.now()-SBT)<=SBM*60000;}
function sbSet(v){SB=String(v||'').replace(/\\D/g,'');SBT=Date.now();try{sessionStorage.setItem(sbKey(),JSON.stringify({b:(SB||'-'),t:SBT}));}catch(e){}
 document.querySelectorAll('.sbShow').forEach(x=>{x.textContent=SB||'\\u2014';});}
function sbSale(){sbSet('');const i=el('nbS');if(i){i.value='';i.focus();}}
async function nowSave(aid, pack){
 if(BUSY)return; const body={ask_id:aid};
 if(!readBoxes(pack,"n"+aid,body)){MSG={kind:"err",title:"Ginti likhiye",lines:[]};render();return;}
 const nb=el("nbS"); const v=String((nb&&nb.value)||SB||"").replace(/\\D/g,'');
 if(v&&!sbFresh()){sbSet('');if(nb)nb.value='';MSG={kind:"err",title:"Aakhri bill dobara likhiye",lines:["Pichhla bill number purana ho gaya — nayi baithak hai."]};render();window.scrollTo(0,0);return;}   // the review, MUST 1
 body.last_bill=v; if(!v) body.no_bill=1;                      // S936: the sitting's bill, once
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/now"+Q,body); if(v) sbSet(v); after(j,"\\u2713 Save ho gaya",[esc(j.saved.message)]);}"""


def make_html(t):
    t = rep(t, CARD_OLD_A, CARD_NEW_A, 1, "H1 card")
    t = rep(t, SAVE_OLD, SAVE_NEW, 1, "H2 nowSave")
    return t


def main():
    src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    os.makedirs(dst, exist_ok=True)
    data = {}
    for f, pin in FROM_PINS.items():
        b = open(os.path.join(src, f), "rb").read()
        got = hashlib.md5(b).hexdigest()
        if got != pin:
            raise SystemExit("FROM %s is %s, not the live pin %s -- stop" % (f, got, pin))
        data[f] = b.decode("utf-8")
    out = {"stock_figure.py": make_figure(data["stock_figure.py"]), "stock_watch.py": make_watch(data["stock_watch.py"]),
           "stockmatch.py": make_sm(data["stockmatch.py"]), "stockmatch.html": make_html(data["stockmatch.html"])}
    for f, t in out.items():
        with open(os.path.join(dst, f), "wb") as fh:
            fh.write(t.encode("utf-8"))
        print("%s  %s" % (hashlib.md5(t.encode("utf-8")).hexdigest(), f))


if __name__ == "__main__":
    main()
