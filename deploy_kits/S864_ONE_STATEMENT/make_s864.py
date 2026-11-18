#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s864.py -- S864_ONE_STATEMENT (18-Nov-2026, Sanjeevni session 479; the owner's 'go' 08:21 IST on claude/S479_MARG_EXPORTS_ANALYSIS.md).

Builds the kit's purchase_app.py and export_watch.py from the live bytes (the 18-Nov bundle) by EXACT anchored replacements -- every anchor must
occur exactly once, or nothing is written (F-472). amir_day.py gets one tail block (no anchor inside old text). month_asks.py is a whole file.

    python3 make_s864.py <src dir with the four live files> <out dir>

THE RULE (D1000 reshaped): Marg's bill-wise and supplier-wise purchase statements carry the same five figures per bill (supplier, bill no, date,
cash, credit) -- they are ONE family. The newest statement of either kind is the month's figure; an incoming statement retires every older one
of either kind whose period it contains (the containment rule of rev 4, across the family). No 'bill-wise vs supplier-wise' disagreement can
exist. The month needs TWO reports after it ends -- a statement covering the 1st..the last day and the item lines -- not three; the supplier-wise
is never asked (accepted as a statement when it comes). The cross-check keeps every test it had: the bills the statement carries, and its own
printed grand total against the sheet. A Wrong mark whose paper figure the newest statement shows resolves itself (S371's rule, now reading the
newest statement, not the supplier-wise first).
"""
import hashlib
import os
import sys

FROM = {"purchase_app.py": "1ac9d1efae26a8b3bd6e61d4cb9a0324", "export_watch.py": "f6845ec5ae1dc8fe200ebf5f4c3ad173",
        "amir_day.py": "97e56bc73a047ed1fe4fd3ef93dec5f6"}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def patch(text, pairs, name):
    for i, (old, new) in enumerate(pairs):
        n = text.count(old)
        if n != 1:
            raise SystemExit("!! %s anchor %d occurs %d times (must be 1):\n%s" % (name, i + 1, n, old[:200]))
        text = text.replace(old, new, 1)
    return text


# ============================================================================ purchase_app.py
PA = [
# A1 -- the part guard reads the family
(
'''            "SELECT md5, COALESCE(n_rows, 0) FROM purchase_export WHERE type=? AND period_from>=? AND period_to<=? "
            "AND superseded_by IS NULL AND export_stamp<? ORDER BY COALESCE(n_rows, 0) DESC, export_stamp DESC LIMIT 1",
            (typ, pf, pt, stamp)).fetchone()''',
'''            "SELECT md5, COALESCE(n_rows, 0) FROM purchase_export WHERE type IN (%s) AND period_from>=? AND period_to<=? "
            "AND superseded_by IS NULL AND export_stamp<? ORDER BY COALESCE(n_rows, 0) DESC, export_stamp DESC LIMIT 1" % _s864_in(typ),
            _s864_family(typ) + (pf, pt, stamp)).fetchone()'''),
# A2 -- the push: an incoming statement retires the older contained ones of EITHER kind (S864)
(
'''    rivals = con.execute(
        "SELECT md5, export_stamp FROM purchase_export WHERE type=? AND period_from>=? "
        "AND period_to<=? AND superseded_by IS NULL AND export_stamp<?", (typ, pf, pt, stamp)).fetchall()
    newer = con.execute(
        "SELECT md5, export_stamp FROM purchase_export WHERE type=? AND period_from<=? "
        "AND period_to>=? AND superseded_by IS NULL AND export_stamp>?", (typ, pf, pt, stamp)).fetchall()''',
'''    # S864 (18-Nov-2026): BILLWISE and SUPPLIERWISE are one family -- the same five figures per bill -- so a statement of either
    # kind retires the older contained statements of either kind, and is itself superseded by a newer containing one of either kind.
    rivals = con.execute(
        "SELECT md5, export_stamp FROM purchase_export WHERE type IN (%s) AND period_from>=? "
        "AND period_to<=? AND superseded_by IS NULL AND export_stamp<?" % _s864_in(typ), _s864_family(typ) + (pf, pt, stamp)).fetchall()
    newer = con.execute(
        "SELECT md5, export_stamp FROM purchase_export WHERE type IN (%s) AND period_from<=? "
        "AND period_to>=? AND superseded_by IS NULL AND export_stamp>?" % _s864_in(typ), _s864_family(typ) + (pf, pt, stamp)).fetchall()'''),
# A3 -- the money view of a bill: the NEWER live statement is the figure; no disagreement bucket
(
'''    for r in con.execute(
            "SELECT b.*, EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL "
            "AND e.md5=b.bw_md5) bw_live, EXISTS (SELECT 1 FROM purchase_export e WHERE "
            "e.superseded_by IS NULL AND e.md5=b.sw_md5) sw_live FROM purchase_bill b WHERE "
            "b.month=? AND " + EFF_BILL + " ORDER BY b.supplier, b.bill_date, b.bill_no", (month,)):
        b = dict(r)
        bw = (b["bw_amount_p"] if b["bw_amount_p"] is not None else b["amount_p"]) if b["bw_live"] else None
        sw = (b["sw_amount_p"] if b["sw_amount_p"] is not None else b["amount_p"]) if b["sw_live"] else None
        b["bw_p"], b["sw_p"] = bw, sw
        b["marg_p"] = sw if sw is not None else (bw if bw is not None else b["amount_p"])
        b["basis"] = "supplier-wise" if sw is not None else "bill-wise"
        b["disagree_p"] = (sw - bw) if (sw is not None and bw is not None and abs(sw - bw) > AGREE_P) else 0
        out.append(b)''',
'''    for r in con.execute(
            "SELECT b.*, EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL "
            "AND e.md5=b.bw_md5) bw_live, EXISTS (SELECT 1 FROM purchase_export e WHERE "
            "e.superseded_by IS NULL AND e.md5=b.sw_md5) sw_live, "
            "(SELECT e.export_stamp FROM purchase_export e WHERE e.md5=b.bw_md5) bw_stamp, "
            "(SELECT e.export_stamp FROM purchase_export e WHERE e.md5=b.sw_md5) sw_stamp FROM purchase_bill b WHERE "
            "b.month=? AND " + EFF_BILL + " ORDER BY b.supplier, b.bill_date, b.bill_no", (month,)):
        b = dict(r)
        bw = (b["bw_amount_p"] if b["bw_amount_p"] is not None else b["amount_p"]) if b["bw_live"] else None
        sw = (b["sw_amount_p"] if b["sw_amount_p"] is not None else b["amount_p"]) if b["sw_live"] else None
        b["bw_p"], b["sw_p"] = bw, sw
        # S864: the NEWEST live statement of either kind is the figure (the two carry the same figures; a difference between them is
        # only Marg edited between the exports -- the newer is right). No disagreement bucket.
        b["marg_p"], b["basis"] = _s864_newest(bw, sw, b.get("bw_stamp"), b.get("sw_stamp"), b["amount_p"])
        b["disagree_p"] = 0
        out.append(b)'''),
# A4 -- the month's basis words and the head line
(
'''    if not bills or n_sw == len(bills):
        basis, basis_note = "supplier-wise", ""
    elif n_sw == 0:
        basis, basis_note = "bill-wise", "supplier-wise not exported yet for this month \\u2014 bill-wise stands in"
    else:
        basis, basis_note = "supplier-wise", "%s so far only in bill-wise" % _plural(len(bills) - n_sw, "bill")
    month_disagree_p = sum(b["sw_p"] - b["bw_p"] for b in bills
                           if b["sw_p"] is not None and b["bw_p"] is not None)''',
'''    # S864: the figure is the newest statement of either kind; "final for month-end" once a statement covers the whole month
    full_stmt = _s864_statement(con, month)
    n_bw = sum(1 for b in bills if b["basis"] == "bill-wise")
    basis = "bill-wise" if (n_bw >= len(bills) - n_bw or not bills) else "supplier-wise"
    if full_stmt is not None or not bills:
        basis_note = ""
    elif dt.datetime.now(IST).date() > dt.date.fromisoformat(_s604_last_day(month)):
        basis_note = "no statement covers the whole month yet \\u2014 the pair over the finished month is asked of Amir"
    else:
        basis_note = "month to date \\u2014 the whole month's statement comes with Amir's first visit after the month ends"
    month_disagree_p = 0'''),
(
'''    head = "%s: %s (%s%s)" % (short_mn, _r(marg), basis,
                              ", final for month-end" if basis == "supplier-wise" and bills else "")''',
'''    head = "%s: %s (%s%s)" % (short_mn, _r(marg), basis,
                              ", final for month-end" if full_stmt is not None and bills else "")'''),
# A5 -- two reports after month end, not three
(
'''_S604_REPORTS = (
    ("SUPPLIERWISE", ("SUPPLIERWISE",), "supplier-wise statement", "SUPPLIER WISE PURCHASE STATEMENT"),
    ("BILLWISE", ("BILLWISE",), "bill-wise statement", "BILL WISE PURCHASE STATEMENT"),
    ("ITEMS", ("ITEMWISE", "BILLITEMWISE"), "item lines", "SUPPLIER/ITEM WISE PURCHASE STATEMENT"),
)''',
'''_S604_REPORTS = (                                                 # S864: ONE statement (bill-wise, or supplier-wise if that is what came) + the lines
    ("STATEMENT", ("BILLWISE", "SUPPLIERWISE"), "bill statement", "BILL WISE PURCHASE STATEMENT"),
    ("ITEMS", ("ITEMWISE", "BILLITEMWISE"), "item lines", "SUPPLIER/ITEM WISE PURCHASE STATEMENT"),
)'''),
# A6 -- the gate's words
(
'''            reasons.append("the cross-check against the supplier-wise statement does not agree: %s"''',
'''            reasons.append("the cross-check against Marg's statement does not agree: %s"'''),
# A7 -- the month-end reports card
(
'''            if e["key"] == "SUPPLIERWISE" and x["grand_amount_p"]:''',
'''            if e["key"] == "STATEMENT" and x["grand_amount_p"]:'''),
(
'''        lines.append('<div class="ok" style="margin:8px 0"><b>All three reports are in and agree \\u2014 the month can be '
                     'locked.</b></div>')''',
'''        lines.append('<div class="ok" style="margin:8px 0"><b>Both reports are in and agree \\u2014 the month can be '
                     'locked.</b></div>')'''),
# A8 -- the cross-check reads the newest statement of either kind
(
'''    sw = con.execute(
        "SELECT md5, file, export_stamp, n_rows, grand_amount_p FROM purchase_export "
        "WHERE type='SUPPLIERWISE' AND superseded_by IS NULL AND period_from<=? AND period_to>=? "
        "ORDER BY export_stamp DESC LIMIT 1", (month + "-01", _s604_last_day(month))).fetchone()
    if sw is None:
        problems.append("No supplier-wise purchase statement for this month has reached the server. "
                        "Take it out of Marg — supplier, bill number, bill date, amount — "
                        "and it will arrive by itself within about ten minutes.")
        return {"ok": False, "problems": problems, "notes": notes, "export": None,
                "n_bills": len(bills), "total_p": s["marg_p"], "printed_p": None}

    without = [b for b in bills if b["sw_p"] is None]
    if without:
        problems.append("%s on the sheet %s not carried by that statement: %s."
                        % (_plural(len(without), "bill"), "is" if len(without) == 1 else "are",
                           _name_some(without, lambda b: "%s (%s)" % (b["bill_no"], b["supplier"]))))
    dis = [b for b in bills if b["disagree_p"]]
    if dis:
        problems.append("%s where bill-wise and supplier-wise disagree: %s."
                        % (_plural(len(dis), "bill"),
                           _name_some(dis, lambda b: "%s %s vs %s"
                                      % (b["bill_no"], _r(b["bw_p"]), _r(b["sw_p"])))))''',
'''    sw = _s864_statement(con, month)                           # S864: the newest statement of either kind covering the whole month
    if sw is None:
        problems.append("No purchase statement covering the whole of this month has reached the server yet. "
                        "It comes with Amir's visit pair over the finished month (bill-wise, FROM the 1st TO the last day) — "
                        "asked on his card by itself; it arrives within about a quarter of an hour of the export.")
        return {"ok": False, "problems": problems, "notes": notes, "export": None,
                "n_bills": len(bills), "total_p": s["marg_p"], "printed_p": None}

    without = [b for b in bills if b.get("bw_md5") != sw["md5"] and b.get("sw_md5") != sw["md5"]]
    if without:
        problems.append("%s on the sheet %s not carried by that statement: %s."
                        % (_plural(len(without), "bill"), "is" if len(without) == 1 else "are",
                           _name_some(without, lambda b: "%s (%s)" % (b["bill_no"], b["supplier"]))))'''),
(
'''    """STEP 2 -- the supplier-wise statement as the cross-check.

    Not a tick-box: it reads Marg's own supplier-wise export of this month and
    holds the prepared sheet against it three ways -- every bill carried by it,
    the per-bill amounts where bill-wise and supplier-wise both exist, and the
    export's OWN PRINTED GRAND TOTAL. Anything that does not line up is named."""''',
'''    """STEP 2 -- Marg's statement as the cross-check (S864: the newest bill-wise or supplier-wise covering the whole month).

    Not a tick-box: it reads Marg's own export of this month and holds the prepared
    sheet against it two ways -- every bill on the sheet is carried by it, and the
    export's OWN PRINTED GRAND TOTAL equals the sheet. Anything that does not line up is named."""'''),
# A9 -- S371's self-resolution reads the newest statement
(
'''        sw = r["sw_amount_p"] if (r["sw_md5"] in live and r["sw_amount_p"] is not None) else None
        bw = r["bw_amount_p"] if (r["bw_md5"] in live and r["bw_amount_p"] is not None) else None
        now_p = sw if sw is not None else (bw if bw is not None else r["amount_p"])''',
'''        sw = r["sw_amount_p"] if (r["sw_md5"] in live and r["sw_amount_p"] is not None) else None
        bw = r["bw_amount_p"] if (r["bw_md5"] in live and r["bw_amount_p"] is not None) else None
        now_p = _s864_newest(bw, sw, _s864_stamp_of(con, r["bw_md5"]), _s864_stamp_of(con, r["sw_md5"]), r["amount_p"])[0]   # S864'''),
# A10 -- the hub's words
(
'''    months = ('<div class="card"><h2>Months</h2><div class="muted">The Marg total is the supplier-wise '
              'report, final for month-end. Item-wise is NET (after discount), each bill\\'s lines counted '
              'once; a bill whose lines add up to more than the bill carries a purchase return, as Marg '
              'reports it.</div>'
              '<div class="scroll"><table><tr><th>Month</th>'
              '<th class="n">Marg total (supplier-wise)</th><th class="n">Item-wise net</th><th class="n">Bills</th>\'''',
'''    months = ('<div class="card"><h2>Months</h2><div class="muted">The Marg total is Marg\\'s newest purchase statement '
              '(bill-wise), final for month-end once it covers the whole month. Item-wise is NET (after discount), each bill\\'s lines counted '
              'once; a bill whose lines add up to more than the bill carries a purchase return, as Marg '
              'reports it.</div>'
              '<div class="scroll"><table><tr><th>Month</th>'
              '<th class="n">Marg total (statement)</th><th class="n">Item-wise net</th><th class="n">Bills</th>\''''),
(
'''                       "" if s["basis"] == "supplier-wise" else '<div class="muted">bill-wise</div>',''',
'''                       "" if s.get("basis_note", "") == "" else '<div class="muted">month to date</div>',           # S864'''),
# A11 -- the month page's explainer and head
(
'''                ", final for month-end" if s["basis"] == "supplier-wise" else "", basis_line,''',
'''                ", final for month-end" if s.get("basis_note", "") == "" and s["bills"] else "", basis_line,       # S864'''),
(
'''            'supplier-wise figure (bill-wise while supplier-wise is not yet exported). Item-wise is the NET \'''',
'''            'newest purchase statement (bill-wise; final once a statement covers the whole month). Item-wise is the NET \''''),
# A13 -- a byte-identical re-export of a LIVE statement moves its stamp forward (review S3: an ask waiting for a newer statement must clear)
(
'''    if con.execute("SELECT 1 FROM purchase_export WHERE md5=?", (md5,)).fetchone():
        return jsonify(ok=True, stored=False, reason="duplicate")''',
'''    dup = con.execute("SELECT superseded_by, export_stamp FROM purchase_export WHERE md5=?", (md5,)).fetchone()
    if dup:
        # S864: the same bytes exported again (Marg unchanged) -- a LIVE row takes the newer capture stamp, so an ask that waits for 'a statement
        # newer than X' clears and Amir's step 4 sees today's export; a superseded row is left as it is.
        if dup[0] is None and str(dup[1] or "") < stamp:
            con.execute("UPDATE purchase_export SET export_stamp=?, received_at=? WHERE md5=? AND superseded_by IS NULL", (stamp, now_iso(), md5))
            _audit(con, "push_purchases", "push_again", md5, dict(type=typ, period=[pf, pt], stamp=stamp, was=dup[1]))
            con.commit()
            return jsonify(ok=True, stored=False, reason="duplicate_restamped")
        return jsonify(ok=True, stored=False, reason="duplicate")'''),
# A14 -- the month page's purchase-returns note
(
'''            'the bill\\'s item lines add up to more than the bill. Nothing to mark \\u2014 the supplier-wise '
            'figure already carries it.''',
'''            'the bill\\'s item lines add up to more than the bill. Nothing to mark \\u2014 Marg\\'s own '
            'figure already carries it.'''),
# A12 -- the verify card's words (S749)
(
'''        body = ('<div class="muted">Waiting for Marg\\'s supplier-wise statement of this month. The moment it arrives the server holds the sheet '
                'against it -- every bill it carries, the per-bill amounts and its own printed grand total -- and says here whether they agree.</div>')''',
'''        body = ('<div class="muted">Waiting for a Marg statement covering the whole of this month (Amir\\'s bill-wise, FROM the 1st TO the last day). '
                'The moment it arrives the server holds the sheet against it -- every bill it carries and its own printed grand total -- and says here whether they agree.</div>')'''),
(
'''        body = ('<div class="ok"><b>Verified against Marg\\'s supplier-wise statement</b> — %s agrees, %s.</div>%s\'''',
'''        body = ('<div class="ok"><b>Verified against Marg\\'s statement</b> — %s agrees, %s.</div>%s\''''),
(
'''    return ('<div class="card"><h2>2 &middot; Verified against the supplier-wise statement</h2>'
            '<div class="muted">Run by the server, not by a tap: Marg\\'s own supplier-wise export of this month is read and the sheet is held '
            'against it three ways.</div>%s</div>' % body)''',
'''    return ('<div class="card"><h2>2 &middot; Verified against Marg\\'s statement</h2>'
            '<div class="muted">Run by the server, not by a tap: Marg\\'s own newest statement covering this month (bill-wise, or supplier-wise '
            'if that is what came) is read and the sheet is held against it two ways.</div>%s</div>' % body)'''),
]

PA_TAIL = r'''

# ---- S864_ONE_STATEMENT (18-Nov-2026, Sanjeevni session 479; the owner's 'go' 08:21 on claude/S479_MARG_EXPORTS_ANALYSIS.md) -------------------
#  Marg's bill-wise and supplier-wise purchase statements carry the same five figures per bill: ONE family. The newest statement of either kind is
#  the month's figure (the containment rule of rev 4 applied across the family at the push); the month needs a statement covering the whole month
#  and the item lines -- two reports, not three; the supplier-wise is never asked. The helpers the patched places call, and the one-off.
_S864_FAMILY = ("BILLWISE", "SUPPLIERWISE")


def _s864_family(typ):
    """The export types that are 'the same report' as typ, as a tuple for an IN (...)."""
    return _S864_FAMILY if typ in _S864_FAMILY else (typ,)


def _s864_in(typ):
    return ",".join("?" * len(_s864_family(typ)))


def _s864_newest(bw, sw, bw_stamp, sw_stamp, fallback):
    """(figure, basis) -- the live statement with the NEWER Marg stamp; one live: that one; none: the stored amount."""
    if bw is not None and sw is not None:
        if (str(sw_stamp or "")) > (str(bw_stamp or "")):
            return sw, "supplier-wise"
        return bw, "bill-wise"
    if sw is not None:
        return sw, "supplier-wise"
    if bw is not None:
        return bw, "bill-wise"
    return fallback, "bill-wise"


def _s864_stamp_of(con, md5):
    if not md5:
        return ""
    try:
        r = con.execute("SELECT export_stamp FROM purchase_export WHERE md5=?", (md5,)).fetchone()
    except sqlite3.Error:
        return ""
    return str(r[0] or "") if r else ""


def _s864_statement(con, month):
    """The newest LIVE statement of either kind whose period covers the 1st..the last day of the month, as a dict, or None."""
    try:
        r = con.execute(
            "SELECT md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p FROM purchase_export "
            "WHERE type IN ('BILLWISE','SUPPLIERWISE') AND superseded_by IS NULL AND period_from<=? AND period_to>=? "
            "ORDER BY export_stamp DESC, received_at DESC LIMIT 1", (month + "-01", _s604_last_day(month))).fetchone()
    except sqlite3.Error:
        return None
    return dict(r) if r else None


def s864_one_off(con, who="S864 one statement", dry=False):
    """At the install: the family rule applied to what is already stored -- for every month that is not FINAL, a live statement of either kind
    whose period is contained in a NEWER live statement of either kind is superseded by it (exactly what the push now does), then S371's
    self-resolution runs over the Wrong marks (the newest statement read). Counted months only (purchase.register_from); FINAL months untouched; idempotent; audited.
    The S795 part guard holds here as at the push (a small part list never retires a fuller statement).
    -> dict(superseded=[(old md5, by md5, month, old rows, new rows, bills carried only by the old)], resolved=[(bill id, supplier, bill no, amount_p)])."""
    out = dict(superseded=[], resolved=[])
    try:                                                      # counted months only (purchase.register_from, S749): the parked months are his, untouched
        r0 = con.execute("SELECT value FROM setting WHERE key='purchase.register_from'").fetchone()
        reg_from = str(r0[0])[:7] if r0 and r0[0] else "2026-10"
    except sqlite3.Error:
        reg_from = "2026-10"
    rows = [dict(r) for r in con.execute(
        "SELECT md5, type, period_from, period_to, export_stamp, n_rows FROM purchase_export WHERE type IN ('BILLWISE','SUPPLIERWISE') "
        "AND superseded_by IS NULL ORDER BY export_stamp")]
    for old in rows:
        m = str(old["period_from"] or "")[:7]
        if m < reg_from:
            continue
        try:
            if _month_status(con, m)["status"] == "final":
                continue
        except Exception:                                      # noqa: BLE001
            continue
        for new in rows:
            if new["md5"] == old["md5"] or str(new["export_stamp"] or "") <= str(old["export_stamp"] or ""):
                continue
            if not (new["period_from"] <= old["period_from"] and new["period_to"] >= old["period_to"]):
                continue
            n_new, n_old = int(new["n_rows"] or 0), int(old["n_rows"] or 0)
            if n_new < S795_HALF * n_old and n_old - n_new > S795_GAP:  # the S795 part guard, as at the push: a part list retires nothing --
                out["superseded"].append((new["md5"], old["md5"], m, n_new, n_old, 0))   # it is itself kept and not counted (part_of), as the push does
                if not dry:
                    con.execute("UPDATE purchase_export SET superseded_by=? WHERE md5=? AND superseded_by IS NULL", (old["md5"], new["md5"]))
                    _audit(con, who, "s864_part_retired", new["md5"], dict(part_of=old["md5"], part_type=new["type"], fuller_type=old["type"], month=m,
                                                                           part_rows=n_new, fuller_rows=n_old))
                continue
            only = con.execute("SELECT COUNT(*) FROM purchase_bill b WHERE (b.bw_md5=? OR b.sw_md5=?) AND NOT EXISTS (SELECT 1 FROM purchase_export e "
                               "WHERE e.superseded_by IS NULL AND e.md5<>? AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))", (old["md5"], old["md5"], old["md5"])).fetchone()[0]
            out["superseded"].append((old["md5"], new["md5"], m, n_old, n_new, only))
            if not dry:
                con.execute("UPDATE purchase_export SET superseded_by=? WHERE md5=? AND superseded_by IS NULL", (new["md5"], old["md5"]))
                _audit(con, who, "s864_superseded", old["md5"], dict(by=new["md5"], old_type=old["type"], new_type=new["type"], month=m,
                                                                    old_rows=n_old, new_rows=n_new, bills_only_in_old=only))
            break
    if not dry:
        out["resolved"] = _resolve_wrong(con, who=who)
        con.commit()
    else:
        try:
            con.rollback()
        except sqlite3.Error:
            pass
    return out
# ---- S864 end ---------------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================ export_watch.py (the owner's own words of 11-Sep: never a report nobody needs)
EW = [
(
'''    and ONLY on the 1st-5th:  PURCHASE SUPPLIER WISE for the whole previous month (month-end, D368)''',
'''    and ONLY on the 1st-5th:  a PURCHASE statement covering the whole previous month -- BILL WISE (or SUPPLIER WISE) FROM the 1st TO the
                              last day (month-end; S864: the two statements are one family, the supplier-wise is never asked)'''),
(
'''LABEL = {"BILLWISE": "PURCHASE BILL WISE", "SUPPLIERWISE": "PURCHASE SUPPLIER WISE for last month (month-end)",''',
'''LABEL = {"BILLWISE": "PURCHASE BILL WISE", "SUPPLIERWISE": "PURCHASE BILL WISE for the whole of last month (month-end)",'''),
(
'''        r = con.execute("SELECT export_stamp, period_from, period_to FROM purchase_export WHERE type='SUPPLIERWISE' "
                        "AND period_from<=? AND period_to>=? AND substr(export_stamp,1,8)>=? "''',
'''        r = con.execute("SELECT export_stamp, period_from, period_to FROM purchase_export WHERE type IN ('SUPPLIERWISE','BILLWISE') "
                        "AND period_from<=? AND period_to>=? AND substr(export_stamp,1,8)>=? "'''),
(
'''        r = con.execute("SELECT stamp, date_from, date_to FROM mi_file WHERE verdict='VERIFIED' AND type='PURCHASE_SUPPLIERWISE' "''',
'''        r = con.execute("SELECT stamp, date_from, date_to FROM mi_file WHERE verdict='VERIFIED' AND type IN ('PURCHASE_SUPPLIERWISE','PURCHASE_BILLWISE') "'''),
]


def main(src, out):
    os.makedirs(out, exist_ok=True)
    for f, want in FROM.items():
        got = md5(os.path.join(src, f))
        if got != want:
            raise SystemExit("!! %s in %s is %s, expected %s (F-472: read the live bytes)" % (f, src, got[:8], want[:8]))
    pa = open(os.path.join(src, "purchase_app.py"), encoding="utf-8").read()
    pa = patch(pa, PA, "purchase_app.py")
    if "S864_ONE_STATEMENT" in pa:
        raise SystemExit("!! purchase_app.py already carries S864")
    pa = pa.rstrip("\n") + "\n" + PA_TAIL
    open(os.path.join(out, "purchase_app.py"), "w", encoding="utf-8", newline="\n").write(pa)
    ew = open(os.path.join(src, "export_watch.py"), encoding="utf-8").read()
    ew = patch(ew, EW, "export_watch.py")
    open(os.path.join(out, "export_watch.py"), "w", encoding="utf-8", newline="\n").write(ew)
    ad = open(os.path.join(src, "amir_day.py"), encoding="utf-8").read()
    if "S864_ONE_STATEMENT" in ad:
        raise SystemExit("!! amir_day.py already carries S864")
    here = os.path.dirname(os.path.abspath(__file__))
    tail = open(os.path.join(here, "amir_day_tail_s864.py"), encoding="utf-8").read()
    for anchor in ("<div class=card><h2>Do report nikaaliye</h2>", "<div class=card><h2>Do report</h2>"):
        if ad.count(anchor) != 1:
            raise SystemExit("!! amir_day.py: the render anchor %r occurs %d times (must be 1)" % (anchor, ad.count(anchor)))
    ad = ad.rstrip("\n") + "\n" + tail
    open(os.path.join(out, "amir_day.py"), "w", encoding="utf-8", newline="\n").write(ad)
    for f in ("purchase_app.py", "export_watch.py", "amir_day.py"):
        print("%s %s" % (md5(os.path.join(out, f)), f))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
