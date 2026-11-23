#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s934.py -- kit S934_COUNT_NOW (23-Nov-2026, Sanjeevni session 505). Exact anchors on the live bytes (the 23-Nov bundle):
    python3 -B make_s934.py <from dir> <to dir>
stock_watch.py 0dd0a40a, stock_figure.py 5d15e77d, stock_check.py bf68c55b, stock_check.html 4d6cbc6f, stockmatch.py 57d04d3e,
stockmatch.html 0ec2e32d. Every anchor must occur exactly once; any miss stops the build and writes nothing."""
import hashlib
import os
import sys

FROM = {"stock_watch.py": "0dd0a40a", "stock_figure.py": "5d15e77d", "stock_check.py": "bf68c55b", "stock_check.html": "4d6cbc6f",
        "stockmatch.py": "57d04d3e", "stockmatch.html": "0ec2e32d"}
EDITS = {}

# ====================================================================== stock_watch.py
SW_BLOCK = r'''
# ------------------------------------------------------------------ S934 (23-Nov-2026): COUNT NOW, placed to the bill
#  THE OWNER'S WORD (23-Nov 08:16-08:22): his Count button offers 'Count now' or 'Next list'. A Count now reaches Darpan's screen at once
#  ('Abhi ginti', above the morning list) and Darpan keys the LAST SALE BILL number with his count, so the count is placed to the bill:
#  the sales billed up to that number left the shelf before he counted, the rest after. Such a point is saved at once and JUDGED when the
#  day's sale report is in (status 'awaits_sales'): expected = the figure at the END of the count day (the shelf figure for a counted
#  item, Marg's for an uncounted one; the point itself left out) + that day's sales billed AFTER the number. Carried forward
#  (stock_figure.shelf) the count day's sales up to the number are not taken off again. No number keyed -> the time rule, as any spot
#  count. A Next-list ask is the morning roster's, as before. His open asks can be withdrawn (a rostered row not yet counted leaves that
#  day's list). The installer withdraws every ask open at the install (his word 08:22: "clear whatever counts I have raised").
S934_BILL_SPAN = 300                                          # a number further than this past the last known bill is refused as a typo


def _s934_columns(con):
    """S934: stock_watch_ask.mode ('now' | 'next'; NULL = 'next') and .closed_how ('counted' | 'withdrawn'); stock_point.last_bill (the
    sale bill number a Count now was placed to) and .ask_id. Additive."""
    for t, c, ty in (("stock_watch_ask", "mode", "TEXT"), ("stock_watch_ask", "closed_how", "TEXT"),
                     ("stock_point", "last_bill", "TEXT"), ("stock_point", "ask_id", "INTEGER")):
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(%s)" % t).fetchall()}
            if cols and c not in cols:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (t, c, ty))
        except sqlite3.Error:
            pass


def _s934_bill_no(text):
    """'4951' / 'A004951' / 'a 4951' -> 4951; None when there is no number (or more than 7 digits)."""
    d = "".join(re.findall(r"\d+", str(text or "")))
    if not d or len(d.lstrip("0") or "0") > 7:
        return None
    return int(d)


def _s934_last_known(con, day=None):
    """(day, last sale bill number) of the newest day BEFORE `day` (today) in Marg's bill chain, series A; (None, None) when unread."""
    d = day or today().isoformat()
    try:
        r = con.execute("SELECT day, last_no FROM mi_bill_chain WHERE series='A' AND last_no IS NOT NULL AND day<? ORDER BY day DESC LIMIT 1", (d,)).fetchone()
        return (r[0], int(r[1])) if r else (None, None)
    except sqlite3.Error:
        return (None, None)


def _s934_check_bill(con, text, day=None):
    """(ok, number, Hindi message). Refused: no number; a number BEFORE the last bill of the last day known (yesterday's report); a
    number more than S934_BILL_SPAN past it (a typo). Unknown chain -> accepted."""
    n = _s934_bill_no(text)
    if n is None or n <= 0:
        return False, None, "Aakhri bill ka number likhiye (jaise 4951)."
    ld, last = _s934_last_known(con, day)
    if last is not None:
        t_ = today()
        if n < last and t_.month == 4 and t_.day <= 7 and n < 1000:   # a new financial year: Marg's A series starts again
            return True, n, ""
        if n < last:
            return False, None, "Yeh number %s ke aakhri bill (%d) se peechhe hai. Aaj ka aakhri bill number dobara dekhiye." % (dmy(ld), last)
        if n > last + S934_BILL_SPAN:
            return False, None, "Yeh number bahut aage hai (%s ka aakhri bill %d tha). Dobara dekhiye." % (dmy(ld), last)
    return True, n, ""


def _s934_unroster(con, item, who, ask_id, ask_at):
    """Every roster row of THIS ask for the item that Darpan has not answered -- the row it was put on AND any copy carried onto a later
    list (a carried row is a new row the ask's roster_id never points to): reason 'you asked for it...', on or after the ask's own day (an
    older ask's rows are history). A system pick is never touched."""
    rows = con.execute("SELECT id, day FROM stock_spot_roster WHERE item_norm=? AND answered_at IS NULL AND reason LIKE 'you asked for it%' AND day>=?",
                       (norm_name(item), str(ask_at or "")[:10])).fetchall()
    for rid, day in rows:
        con.execute("DELETE FROM stock_spot_roster WHERE id=?", (rid,))
        _audit(con, "roster_row_withdrawn", dict(roster_id=rid, day=day, item=item, ask_id=ask_id), who, rid)
    return len(rows)


def withdraw_ask(con, ask_id, who):
    """The owner withdraws an open ask (S934). A rostered row Darpan has not answered leaves that day's list; nothing is deleted from a
    count. Returns (ok, message, code)."""
    ensure(con)
    try:
        aid = int(ask_id)
    except (TypeError, ValueError):
        return False, "Which ask?", 400
    r = con.execute("SELECT id, item, roster_id, at FROM stock_watch_ask WHERE id=? AND done_at IS NULL", (aid,)).fetchone()
    if not r:
        return False, "That ask is no longer open.", 404
    _s934_unroster(con, r[1], who, r[0], r[3])
    con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='withdrawn' WHERE id=?", (now_iso(), r[0]))
    _audit(con, "ask_withdrawn", dict(ask_id=r[0], item=r[1]), who, r[0])
    con.commit()
    return True, "%s withdrawn -- off Darpan's list." % r[1], 200


def withdraw_all_open(con, who):
    """The installer's one-off (his word 08:22): every ask open now, withdrawn. Returns the items."""
    ensure(con)
    out = []
    for (aid,) in con.execute("SELECT id FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id").fetchall():
        ok, msg, _c = withdraw_ask(con, aid, who)
        if ok:
            out.append(msg.split(" withdrawn")[0])
    return out


def now_view(con, sp=None):
    """Darpan's 'Abhi ginti' card: the open Count-now asks, oldest first, with the last bill known (a hint, never a default)."""
    try:
        ensure(con)
        sp = sp or Spine()
        items = []
        for aid, item, at in con.execute("SELECT id, item, at FROM stock_watch_ask WHERE done_at IS NULL AND mode='now' ORDER BY id").fetchall():
            info = item_info(con, sp, item)
            pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
            name = info.get("item") or item
            items.append(dict(id=aid, item=name, pack=pack, packing=packing, whole_hi=_qwm().whole_word(packing, None, name, pack, "hi"),
                              at=at, at_text=stamp(at)))
        ld, last = _s934_last_known(con)
        return dict(items=items, last_day=(dmy(ld) if ld else ""), last_no=last)
    except Exception:                                         # noqa: BLE001
        return dict(items=[], last_day="", last_no=None)


def answer_now(con, ask_id, qty_units, last_bill, who, sp=None):
    """Darpan answers a Count now: the shelf quantity and the last sale bill number. With a number the point waits for that day's sale
    report ('awaits_sales') and is judged to the bill (_s934_settle); without one it is judged now by its time, as any spot count.
    Returns (ok, message_hi, code, point)."""
    ensure(con)
    sp = sp or Spine()
    try:
        aid = int(ask_id)
    except (TypeError, ValueError):
        aid = 0
    r = con.execute("SELECT id, item FROM stock_watch_ask WHERE id=? AND done_at IS NULL AND mode='now'", (aid,)).fetchone()
    if not r:
        return False, "Yeh ginti ab khuli nahi hai.", 404, None
    n = None
    if str(last_bill or "").strip():
        ok, n, msg = _s934_check_bill(con, last_bill)
        if not ok:
            return False, msg, 400, None
    if n is None:
        P = write_point(con, r[1], qty_units, "darpan", who, sp=sp, note="Count now (no bill number -- placed by its time)", commit=False)
    else:
        P = write_point(con, r[1], qty_units, "darpan", who, sp=sp, note="Count now, to bill %d" % n, expected=None, commit=False)
        con.execute("UPDATE stock_point SET status='awaits_sales', settled_at=NULL, last_bill=?, expected_units=NULL, gap_units=NULL WHERE id=?",
                    (str(n), P["id"]))
        P.update(status="awaits_sales", expected=None, gap=None, last_bill=n,
                 verdict="counted to bill %d -- judged when that day's sale report is in" % n,
                 verdict_hi="Bill %d tak ki ginti -- kal ki sale report aane par milaan hoga." % n)
    con.execute("UPDATE stock_point SET ask_id=? WHERE id=?", (r[0], P["id"]))
    con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='counted' WHERE id=?", (now_iso(), r[0]))
    _audit(con, "count_now", dict(ask_id=r[0], item=P["item"], qty=float(qty_units), last_bill=n), who, P["id"])
    con.commit()
    _s928_count_day(con, sp)
    tail = "" if n is not None else " Bill number nahi likha -- samay se milaan hua."
    return True, ("Likh liya: %s -- %s. %s%s" % (P["item"], P["qty_hi"], P["verdict_hi"], tail)).rstrip(), 200, P


def _s934_sales_in(con, sp, day):
    """True only when the SPINE holds a sale report covering `day` to its end: an accepted SALE_BILLWISE export whose date_to is on or after
    the day and that was taken AFTER the day (its stamp's date later than the day). Marg's bill chain is never enough: it is rebuilt the
    moment the report lands, the spine minutes to hours later (cold review, MUST 1)."""
    try:
        for r in sp.q("SELECT stamp, date_to FROM sp_export WHERE family='SALE_BILLWISE' AND ok=1 AND date_to>=? AND COALESCE(date_from,'')<=?", day, day):   # second look A: the report must COVER the day
            st = str(r.get("stamp") or "")[:8]
            if len(st) == 8 and st.isdigit() and "%s-%s-%s" % (st[:4], st[4:6], st[6:8]) > day:
                return True
    except Exception:                                         # noqa: BLE001
        pass
    return False


def _s934_settle(con, sp=None):
    """Judge every 'awaits_sales' point whose day's sales are in: expected = the figure at the END of the count day (shelf for a counted
    item, Marg's for an uncounted one; the point itself left out) + that day's sales billed AFTER its last bill; a family figure is not
    judged. A short beyond the allowance is a loss line by name, as write_point. Fail-soft per point. Returns the number judged."""
    try:
        ensure(con)
        rows = con.execute("SELECT id, item, at, qty_units, last_bill FROM stock_point WHERE status='awaits_sales' ORDER BY at, id").fetchall()
    except sqlite3.Error:
        return 0
    if not rows:
        return 0
    sp = sp or Spine()
    if not getattr(sp, "ok", False):
        return 0
    SF = _sf()
    n, days = 0, set()
    for pid, item, at, q, lb in rows:
        D = str(at)[:10]
        try:
            if not _s934_sales_in(con, sp, D):
                continue
            ctx = SF.Ctx(con, sp)
            N = _s934_bill_no(lb)
            b0 = SF.base(con, item, ctx, exclude_id=pid)
            if b0 is not None and str(b0.get("at") or "") > str(at):      # SHOULD 3: a later count of the item already stands
                con.execute("UPDATE stock_point SET status='settled', settled_at=?, note=COALESCE(note,'') || ? WHERE id=?",
                            (now_iso(), " · a later count stands -- not judged", pid))
                _audit(con, "point_not_judged_later_count", dict(point_id=pid, item=item, later_at=b0.get("at")), "system", pid)
                con.commit()
                n += 1
                days.add(D)
                continue
            Sh = SF.shelf(con, sp, item, D, ctx, exclude_id=pid)
            M = SF.marg(con, sp, item, D, ctx)
            k = Sh.get("key") or SF.key_of(sp, item, ctx)
            after = float(SF.day_sales_cut(sp, k, D, N, after=True)) if (k and N is not None) else 0.0
            late = float(SF.taps(con, sp, item, at, ctx) or 0) + float(SF.scan_arrivals(con, sp, item, at, ctx) or 0)   # MUST 2: arrivals AFTER the count
            pr_d = (sp.q("SELECT COUNT(*) AS n FROM sp_move WHERE k20=? AND date=? AND kind='PURCHASE'", k, D) or [{"n": 0}])[0]["n"] if k else 0
            if Sh.get("approx") or (M and M.get("approx")):
                basis, exp = "approx", None
            elif Sh.get("shelf") is not None:
                basis, exp = "shelf", float(Sh["shelf"]) + after - late
            elif M is not None:
                sa = float(SF.scan_arrivals(con, sp, item, M["closing"]["stamp_iso"], ctx) or 0)   # SHOULD 5: as expect_for_point
                basis, exp = "marg", float(M["figure"]) + float(M.get("taps") or 0) + sa + after - late
            else:
                basis, exp = "marg", None
            gap = None if exp is None else round(float(q) - exp, 3)
            note_add = " · a purchase is dated that day (its time is not known) -- the gap is shown, never a loss" if pr_d else ""
            con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, status='settled', settled_at=?, basis=?, note=COALESCE(note,'') || ? WHERE id=?",
                        (exp, gap, now_iso(), basis, note_add, pid))
            if gap is not None and gap < 0 and basis != "approx" and not pr_d:
                info = item_info(con, sp, item)
                pr = con.execute("SELECT at FROM stock_point WHERE item_norm=? AND id<>? AND at<? AND COALESCE(status,'')<>'superseded' ORDER BY at DESC LIMIT 1",
                                 (norm_name(item), pid, at)).fetchone()
                since = str(pr[0])[:10] if pr else (dt.date.fromisoformat(D) - dt.timedelta(days=30)).isoformat()
                allow, _sold = allowance_units(con, item, info["pack"], since, sp)
                if abs(gap) > allow:
                    mrp = sp.mrp_p(item) if sp.ok else None
                    per = (mrp / max(1, info["pack"])) if mrp else None
                    con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p, point_id) VALUES (?,?,?,?,?,?,?)",
                                (at, item, abs(gap), info["pack"], info["packing"], (int(round(per * abs(gap))) if per else None), pid))
                    try:
                        open_trace(con, item, "point", gap, "system", sp=sp, point_id=pid)
                    except Exception:                         # noqa: BLE001
                        pass
            _audit(con, "point_judged_to_bill", dict(point_id=pid, item=item, day=D, last_bill=N, sold_after=after, arrived_after=late, purchase_that_day=bool(pr_d),
                                                     expected=exp, gap=gap, basis=basis), "system", pid)
            con.commit()
            n += 1
            days.add(D)
        except Exception:                                     # noqa: BLE001
            try:
                con.rollback()
            except Exception:                                 # noqa: BLE001
                pass
    for D in sorted(days):
        _s928_count_day(con, sp, D)
    return n

'''

EDITS["stock_watch.py"] = [
    ('KIT = "S928_STOCK_ONE_RULE"                                   # v1.9 S928',
     'KIT = "S934_COUNT_NOW"                                        # v1.10 S934 (Count now, placed to the bill), v1.9 S928'),
    ('VERSION = "1.9"\n', 'VERSION = "1.10"\n'),
    ("    _s502_columns(con)\n    _s577_columns(con)\n", "    _s502_columns(con)\n    _s577_columns(con)\n    _s934_columns(con)\n"),
    ('    for r in con.execute("SELECT id, item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL ORDER BY id").fetchall():',
     '    for r in con.execute("SELECT id, item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL AND COALESCE(mode,\'next\')<>\'now\' ORDER BY id").fetchall():   # S934: a Count now is never the morning list\'s'),
    ('    for r in con.execute("SELECT item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL ORDER BY id"):',
     '    for r in con.execute("SELECT item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL AND COALESCE(mode,\'next\')<>\'now\' ORDER BY id"):   # S934'),
    # ask(): mode-aware
    ('''def ask(con, item, who, sp=None):
    """The owner's 'Count this' -> the head of the next roster."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    if not info["item"]:
        return False, "Name the item.", 400
    if con.execute("SELECT id FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL", (norm_name(info["item"]),)).fetchone():
        return True, "%s is already on the next list." % info["item"], 200
    con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at) VALUES (?,?,?,?)", (norm_name(info["item"]), info["item"], who, now_iso()))
    _audit(con, "ask", dict(item=info["item"]), who)
    con.commit()
    return True, "%s goes at the head of Darpan's next morning list." % info["item"], 200
''',
     '''def ask(con, item, who, sp=None, mode=None):
    """The owner's 'Count this'. S934: mode 'now' -> Darpan's screen at once ('Abhi ginti', with the last sale bill number); 'next' -> the
    head of the next morning roster, as before. An open ask of the other mode is moved (a rostered row not yet counted leaves its list).
    mode None (an older caller, e.g. the Loss desk's Count this) -> 'next' for a new ask, and an open ask is never moved."""
    ensure(con)
    sp = sp or Spine()
    given = str(mode or "").strip().lower()
    mode = "now" if given == "now" else "next"
    info = item_info(con, sp, item)
    if not info["item"]:
        return False, "Name the item.", 400
    nm = norm_name(info["item"])
    r = con.execute("SELECT id, COALESCE(mode,'next'), roster_id, at FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL ORDER BY id LIMIT 1", (nm,)).fetchone()
    if r and (r[1] == mode or given not in ("now", "next")):
        return True, ("%s is already on Darpan's screen (Count now)." if r[1] == "now" else "%s is already on the next list.") % info["item"], 200
    if r:
        _s934_unroster(con, info["item"], who, r[0], r[3])
        con.execute("UPDATE stock_watch_ask SET mode=?, roster_id=NULL WHERE id=?", (mode, r[0]))
        _audit(con, "ask_mode", dict(item=info["item"], mode=mode), who, r[0])
    else:
        con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at, mode) VALUES (?,?,?,?,?)", (nm, info["item"], who, now_iso(), mode))
        _audit(con, "ask", dict(item=info["item"], mode=mode), who)
    con.commit()
    if mode == "now":
        return True, "%s is on Darpan's screen now -- he counts it today with the last bill number." % info["item"], 200
    return True, "%s goes at the head of Darpan's next morning list." % info["item"], 200
'''),
    # darpan_view: settle to the bill + the Abhi ginti card
    ('''        S = settings(con)
        sp = Spine()
        R = build_roster(con, today(), S, sp)
        P = plan_state(con, S)
''', '''        S = settings(con)
        sp = Spine()
        _s934_settle(con, sp)                                  # S934: a Count now judged to its bill once its day's sales are in
        R = build_roster(con, today(), S, sp)
        P = plan_state(con, S)
'''),
    ('''                    notices=notices(con, "darpan"), is_spot_day=R["is_spot_day"])''',
     '''                    notices=notices(con, "darpan"), is_spot_day=R["is_spot_day"], now=now_view(con, sp))   # S934: Abhi ginti'''),
    # settle_provisional -> also the bill-placed points
    ('''        n += 1
    if n:
        con.commit()
    return n


def tap_vs_bill_lines(con):''', '''        n += 1
    if n:
        con.commit()
    _s934_settle(con, sp)                                      # S934: the Count-now points whose day's sales are in
    return n


def tap_vs_bill_lines(con):'''),
    # the day's count line: any day; a point waiting for its sale report said so
    ('def _s928_count_day(con, sp=None):', 'def _s928_count_day(con, sp=None, day=None):'),
    ('''        d = today().isoformat()
        rows = con.execute("SELECT item, qty_units, expected_units, gap_units, basis, by FROM stock_point WHERE substr(at,1,10)=? AND source IN ('spot','darpan') "''',
     '''        d = str(day or today().isoformat())[:10]            # S934: the day of a point judged later
        rows = con.execute("SELECT item, qty_units, expected_units, gap_units, basis, by, status FROM stock_point WHERE substr(at,1,10)=? AND source IN ('spot','darpan') "'''),
    ('''        for item, q, _e, g, basis, by in rows:
            info = item_info(con, sp, item)
            pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
            name = info.get("item") or item
            if basis == "approx" or g is None:''', '''        for item, q, _e, g, basis, by, st_ in rows:
            info = item_info(con, sp, item)
            pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
            name = info.get("item") or item
            if st_ == "awaits_sales":                          # S934: placed to the bill, judged when the day's sale report is in
                w = "%s (judged to the bill when that day's sale report is in)" % qw(float(q), pack, packing, name)
            elif basis == "approx" or g is None:'''),
    # the S934 block, before the job
    ("# ------------------------------------------------------------------ the job (cron 06:30 IST)\n",
     SW_BLOCK + "\n# ------------------------------------------------------------------ the job (cron 06:30 IST)\n"),
]

# ====================================================================== stock_figure.py
EDITS["stock_figure.py"] = [
    ('KIT = "S933_STOCK_OF_RECORD"                             # v1.7 S933',
     'KIT = "S934_COUNT_NOW"                                   # v1.8 S934 (a Count now placed to its last sale bill), v1.7 S933'),
    ('''            bcol = "basis" if "basis" in cols else "NULL"
            for nm, item, at, qty, src, bs, pid in con.execute("SELECT item_norm, item, at, qty_units, source, %s, id FROM stock_point WHERE source<>? AND COALESCE(status,'')<>'superseded' "
                                                               "ORDER BY at, id" % bcol, (FULL,)):
                if exclude_id is not None and int(pid) == int(exclude_id):
                    continue
                out[nm] = dict(qty=float(qty or 0), at=str(at), source=src, item=item, basis=bs)''',
     '''            bcol = "basis" if "basis" in cols else "NULL"
            lcol = "last_bill" if "last_bill" in cols else "NULL"      # S934: a Count now's last sale bill
            for nm, item, at, qty, src, bs, pid, lb in con.execute("SELECT item_norm, item, at, qty_units, source, %s, id, %s FROM stock_point WHERE source<>? AND COALESCE(status,'')<>'superseded' "
                                                                   "ORDER BY at, id" % (bcol, lcol), (FULL,)):
                if exclude_id is not None and int(pid) == int(exclude_id):
                    continue
                out[nm] = dict(qty=float(qty or 0), at=str(at), source=src, item=item, basis=bs, last_bill=(str(lb) if lb not in (None, "") else None))'''),
    ('''            best = dict(qty=p["qty"], kind=p["source"], day=p["at"][:10], at=p["at"], count_id=None, fixed=False, marg0=None, item=p["item"])''',
     '''            best = dict(qty=p["qty"], kind=p["source"], day=p["at"][:10], at=p["at"], count_id=None, fixed=False, marg0=None, item=p["item"],
                        last_bill=p.get("last_bill"))                   # S934'''),
    ('''    ev = mine["kind"] != "count" and evening_count(mine.get("at"), _s928_settings(ctx)[1], mine["day"])''',
     '''    ev = mine["kind"] != "count" and not mine.get("last_bill") and evening_count(mine.get("at"), _s928_settings(ctx)[1], mine["day"])   # S934: a count placed to its bill is never 'the end of its day\''''),
    ('''        sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=not ev)   # S928: the count day's sales in only for a count before the evening hour
''', '''        sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=not ev)   # S928: the count day's sales in only for a count before the evening hour
        if mine.get("last_bill"):                             # S934: the count day's sales billed up to its last bill left before he counted
            cut = day_sales_cut(sp, k, mine["day"], _bill_n(mine.get("last_bill")), after=False)
            sold -= cut
            ret -= day_returns(sp, k, mine["day"])          # the count day's sale returns are taken as made BEFORE the count (credit notes carry no A number)
            out["bill_cut"] = round(cut, 2)
'''),
    ('''def figures(con, sp, names, at=None, ctx=None):''', '''def _bill_n(text):
    """S934: a sale bill number's digits as an int ('A004951' -> 4951); None when it carries none."""
    d = "".join(re.findall(r"\\d+", str(text or "")))
    return int(d) if d else None


def day_sales_cut(sp, k20, day, bill_no, after=True):
    """S934: units SOLD of the key on `day` billed AFTER (after=True) or UP TO (after=False) the sale bill number -- the spine's SALE rows
    carry their bill in ref. A row whose ref carries no number counts as after (never taken off as before). 0 when the number is None."""
    if sp is None or not getattr(sp, "ok", False) or bill_no is None or not k20:
        return 0.0
    tot = 0.0
    for r in (sp.q("SELECT ref, units FROM sp_move WHERE k20=? AND date=? AND kind='SALE'", k20, day) or []):
        n = _bill_n(r["ref"])
        is_after = (n is None) or (n > int(bill_no))
        if is_after == bool(after):
            tot += -float(r["units"] or 0)
    return tot


def day_returns(sp, k20, day):
    """S934: units RETURNED by patients (SALE_RETURN) of the key on `day` -- taken as before a bill-placed count of that day."""
    if sp is None or not getattr(sp, "ok", False) or not k20:
        return 0.0
    r = sp.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date=? AND kind='SALE_RETURN'", k20, day)
    return float(r[0]["u"] or 0) if r else 0.0


def figures(con, sp, names, at=None, ctx=None):'''),
]

# ====================================================================== stock_check.py
EDITS["stock_check.py"] = [
    ('VERSION = "1.2"                                             # v1.2 S933',
     'VERSION = "1.3"                                             # v1.3 S934: Count now / Next list, withdraw, a count placed to its bill; v1.2 S933'),
    ('''    """Count this -- any item, at the head of Darpan's next list (stock_watch.ask)."""''',
     '''    """Count this -- S934: {item, mode: 'now' | 'next'} -- now: Darpan's screen at once; next: the head of his next morning list (stock_watch.ask)."""'''),
    ('''    ok, msg, code = SW.ask(con, item, (u or {}).get("user") or "", sp=SW.Spine())
    if ok:
        _CACHE["rec"] = None                                 # the next list moved: the page rebuilds on its next read
    return jsonify(ok=ok, message=msg), code
''', '''    mode = str(b.get("mode") or "").strip().lower()                                    # S934: now | next | (none: an open ask is never moved)
    mode = mode if mode in ("now", "next") else None
    ok, msg, code = SW.ask(con, item, (u or {}).get("user") or "", sp=SW.Spine(), mode=mode)
    if ok:
        _CACHE["rec"] = None                                 # the next list moved: the page rebuilds on its next read
    return jsonify(ok=ok, message=msg), code


@bp.route("/api/withdraw", methods=["POST"])
def r_withdraw():
    """S934: withdraw one of his open asks {ask_id} (stock_watch.withdraw_ask)."""
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    con = _db()
    ok, msg, code = _SW().withdraw_ask(con, b.get("ask_id"), (u or {}).get("user") or "")
    if ok:
        _CACHE["rec"] = None
    return jsonify(ok=ok, message=msg), code
'''),
    ('''        asked = {}
        if _has(con, "stock_spot_roster"):''', '''        asked = {}
        try:
            SW._s934_settle(con, sp)                          # S934: a Count now judged to its bill once its day's sales are in
        except Exception:                                     # noqa: BLE001
            pass
        if _has(con, "stock_spot_roster"):'''),
    ('''                               by=(by or "").title(), asked=("you asked" in reason.lower()), reason=reason, note=_note_word(note), provisional=(status == "provisional"),''',
     '''                               by=(by or "").title(), asked=("you asked" in reason.lower()), reason=reason, note=_note_word(note), provisional=(status == "provisional"),
                               awaits=(status == "awaits_sales"),                      # S934'''),
    ("""evening=SF.evening_count(at, S.get("evening_hour", 17), str(at)[:10]) if hasattr(SF, "evening_count") else False))""",
     """evening=(not str(note or "").startswith("Count now, to bill")) and SF.evening_count(at, S.get("evening_hour", 17), str(at)[:10]) if hasattr(SF, "evening_count") else False))   # S934: a bill-placed count is never 'the end of its day'"""),
    ('''        asks = [dict(item=r[0], at=stamp(r[1]), by=(r[2] or "").title()) for r in con.execute("SELECT item, at, by FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")]''',
     '''        try:                                                  # S934: each ask with its id and mode (now | next), withdrawable
            asks = [dict(id=r[3], item=r[0], at=stamp(r[1]), by=(r[2] or "").title(), mode=r[4]) for r in
                    con.execute("SELECT item, at, by, id, COALESCE(mode,'next') FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")]
        except sqlite3.Error:
            asks = [dict(id=r[3], item=r[0], at=stamp(r[1]), by=(r[2] or "").title(), mode="next") for r in
                    con.execute("SELECT item, at, by, id FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")]'''),
]

# ====================================================================== stock_check.html
EDITS["stock_check.html"] = [
    ('''function cntBtn(item){return '<td><button class="cb" type="button" data-item="'+esc(item)+'" onclick="countThis(this,this.dataset.item)">Count</button></td>';}
function countThis(btn,item){
  btn.disabled=true;
  fetch('/finance/stockcheck/api/count',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item:item})})
   .then(function(r){return r.json();}).then(function(j){var m=document.createElement('span');m.className='msg'+(j.ok?'':' err');m.textContent=j.message||(j.ok?'On his next list.':'Not done.');btn.parentNode.appendChild(m);if(!j.ok)btn.disabled=false;})
   .catch(function(){btn.disabled=false;});
}''', '''function cntBtn(item){return '<td><button class="cb" type="button" data-item="'+esc(item)+'" onclick="countThis(this,this.dataset.item)">Count</button></td>';}
/* S934 (23-Nov): Count opens two choices -- Count now (Darpan's screen at once, with the last bill number) or Next list (his next morning list). */
function countThis(btn,item){
  if(!item||!String(item).trim())return;
  var host=btn.parentNode, old=host.querySelector('.chooser'); if(old){old.remove();return;}
  var c=document.createElement('span');c.className='chooser';c.style.cssText='display:inline-flex;gap:6px;margin-left:6px;flex-wrap:wrap';
  var a=document.createElement('button');a.type='button';a.className='cb';a.textContent='Count now';a.style.fontWeight='700';
  var b=document.createElement('button');b.type='button';b.className='cb';b.textContent='Next list';
  a.onclick=function(){doCount(btn,item,'now',c);}; b.onclick=function(){doCount(btn,item,'next',c);};
  c.appendChild(a);c.appendChild(b);host.appendChild(c);
}
function doCount(btn,item,mode,c){
  btn.disabled=true; c.querySelectorAll('button').forEach(function(x){x.disabled=true;});
  fetch('/finance/stockcheck/api/count',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item:item,mode:mode})})
   .then(function(r){return r.json();}).then(function(j){c.remove();var m=document.createElement('span');m.className='msg'+(j.ok?'':' err');m.textContent=j.message||(j.ok?'Done.':'Not done.');btn.parentNode.appendChild(m);if(!j.ok)btn.disabled=false;})
   .catch(function(){btn.disabled=false;c.remove();});
}
var WD={};
function withdraw(el,id){
  if(!WD[id]){WD[id]=1;el.textContent='Sure? Withdraw';el.style.fontWeight='700';setTimeout(function(){if(WD[id]===1){WD[id]=0;el.textContent='Withdraw';el.style.fontWeight='';}},5000);return;}
  WD[id]=2;el.disabled=true;
  fetch('/finance/stockcheck/api/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ask_id:id})})
   .then(function(r){return r.json();}).then(function(j){el.textContent=j.ok?'withdrawn':(j.message||'Not done');if(j.ok){var p=el.closest('.ask');if(p)p.style.opacity='.45';}else{el.disabled=false;WD[id]=0;}})
   .catch(function(){el.disabled=false;WD[id]=0;});
}'''),
    ('''Count this — any item, at the head of Darpan\\'s next list:</label>''', '''Count this — any item, now or on Darpan\\'s next list:</label>'''),
    ('''  if(D.asks&&D.asks.length) h+='<div class="note" style="margin-bottom:4px">Waiting for his next list: '+D.asks.map(function(a){return '<b>'+esc(a.item)+'</b> (asked '+esc(a.at)+')';}).join(' · ')+'</div>';''',
     '''  if(D.asks&&D.asks.length) h+='<div class="note" style="margin-bottom:4px">Your open asks: '+D.asks.map(function(a){return '<span class="ask"><b>'+esc(a.item)+'</b> ('+(a.mode==='now'?'<b>count now</b>':'next list')+', asked '+esc(a.at)+') <button class="cb" type="button" style="min-height:26px;padding:0 8px;font-size:12px" onclick="withdraw(this,'+(+a.id)+')">Withdraw</button></span>';}).join(' · ')+'</div>';'''),
    ('''if(c.provisional)n.push('provisional: a delivery waits for Marg');''',
     '''if(c.provisional)n.push('provisional: a delivery waits for Marg');if(c.awaits)n.push('<b>counted now, to the bill</b> — judged when that day\\'s sale report is in');'''),
]

# ====================================================================== stockmatch.py (Darpan)
EDITS["stockmatch.py"] = [
    ("""    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
""", """    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    print("S934 stockmatch mounted v%s" % VERSION, file=sys.stderr, flush=True)   # the service log proves the mount (F-1554)
"""),
    ('VERSION = "1.2"\nKIT = "S502_STOCK_MILAAN_TODAY"                               # v1.1 was S436_STAFF_PAGES_CLEAN',
     'VERSION = "1.3"\nKIT = "S934_COUNT_NOW"                                        # v1.3 S934 (Abhi ginti), v1.2 S502_STOCK_MILAAN_TODAY, v1.1 S436_STAFF_PAGES_CLEAN'),
    ('''@bp.route("/finance/stockmatch/api/gadbad", methods=["POST"])''', '''@bp.route("/finance/stockmatch/api/now", methods=["POST"])
def api_now():
    """S934: Abhi ginti -- a Count now the doctor asked: {ask_id, strips, loose} or {ask_id, pcs}, and last_bill (the last sale bill number)."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    sw = _sw()
    try:
        aid = int(b.get("ask_id") or 0)
    except (TypeError, ValueError):
        aid = 0
    r = con.execute("SELECT item FROM stock_watch_ask WHERE id=? AND done_at IS NULL", (aid,)).fetchone() if aid else None
    if not r:
        return jsonify(ok=False, error="not_found", message="Yeh ginti ab khuli nahi hai."), 404
    info = sw.item_info(con, sw.Spine(), r[0])
    try:
        q = _qty_from(b, info["pack"])
    except (TypeError, ValueError):
        q = None
    if q is None or q < 0 or q > 100000:
        return jsonify(ok=False, error="bad_request", message="Ginti likhiye."), 400
    ok, msg, code, P = sw.answer_now(con, aid, q, str(b.get("last_bill") or "").strip(), (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), code
    return _sw_state(con, u, kind, dict(kind="now", message=msg, point=P))


@bp.route("/finance/stockmatch/api/gadbad", methods=["POST"])'''),
]

# ====================================================================== stockmatch.html (Darpan, Hindi)
EDITS["stockmatch.html"] = [
    ('''function s428Top(s){
 const W=s.watch; if(!W||!W.ok) return '';
 let h='';
 const R=W.roster||{items:[]};''', '''function s428Top(s){
 const W=s.watch; if(!W||!W.ok) return '';
 let h='';
 const NW=W.now||{items:[]};                                  // S934: Abhi ginti -- the doctor's Count now, with the last bill number
 if(NW.items&&NW.items.length){
  h+='<div class="card" style="border:2px solid #b4541a"><h2>Abhi ginti <span class="tag">'+NW.items.length+'</span></h2><div class="muted">Doctor sahab ne abhi ginne ko kaha hai. Shelf par jitna hai utna likhiye, aur us waqt ka <b>aakhri sale bill number</b> (Marg mein dekhiye)'+(NW.last_no?' &middot; '+esc(NW.last_day)+' ka aakhri bill '+NW.last_no+' tha':'')+'.</div>';
  NW.items.forEach(r=>{
   h+='<div class="line"><div class="nm">'+esc(r.item)+'</div><div class="muted">'+esc(r.packing||'')+(r.pack>1?' &middot; ek patte mein '+r.pack:'')+' &middot; kaha '+esc(r.at_text)+'</div>'
    +'<div class="row" style="justify-content:flex-start;flex-wrap:wrap">'+boxes(r.pack,r.whole_hi,"n"+r.id)
    +' <label>Aakhri bill no. <input id="nb'+r.id+'" inputmode="numeric" style="width:6em;font-size:17px;padding:8px"></label>'
    +'<span class="btn ok" onclick="nowSave('+r.id+','+r.pack+')">Bhej do</span></div></div>';
  });
  h+='</div>';
 }
 const R=W.roster||{items:[]};'''),
    ('''async function spotFix(rid, pack){''', '''async function nowSave(aid, pack){
 if(BUSY)return; const body={ask_id:aid};
 if(!readBoxes(pack,"n"+aid,body)){MSG={kind:"err",title:"Ginti likhiye",lines:[]};render();return;}
 const nb=el("nb"+aid); body.last_bill=(nb&&nb.value)||"";
 BUSY=true;
 try{const j=await post("/finance/stockmatch/api/now"+Q,body); after(j,"\\u2713 Save ho gaya",[esc(j.saved.message)]);}
 catch(e){MSG={kind:"err",title:"Nahi hua",lines:[esc(e.message)]};render();window.scrollTo(0,0);}
 BUSY=false;
}
async function spotFix(rid, pack){'''),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    src, dst = sys.argv[1], sys.argv[2]
    out = {}
    bad = []
    for fn, edits in EDITS.items():
        raw = open(os.path.join(src, fn), "rb").read()
        if md5(raw)[:8] != FROM[fn]:
            bad.append("%s FROM %s, expected %s" % (fn, md5(raw)[:8], FROM[fn]))
            continue
        t = raw.decode("utf-8")
        for i, (a, b) in enumerate(edits):
            c = t.count(a)
            if c != 1:
                bad.append("%s anchor %d found %d times: %r" % (fn, i, c, a[:90]))
                continue
            t = t.replace(a, b)
        out[fn] = t.encode("utf-8")
    if bad:
        print("STOP -- nothing written:\n  " + "\n  ".join(bad))
        sys.exit(1)
    os.makedirs(dst, exist_ok=True)
    for fn, b in out.items():
        open(os.path.join(dst, fn), "wb").write(b)
        print("%-18s %s -> %s" % (fn, FROM[fn], md5(b)[:8]))


if __name__ == "__main__":
    main()
