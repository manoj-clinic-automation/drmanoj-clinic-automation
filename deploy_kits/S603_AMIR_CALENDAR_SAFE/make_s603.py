#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s603.py -- kit S603_AMIR_CALENDAR_SAFE: the builder. Anchored edits on the LIVE bytes of four finance files and the clone's duty map;
no new file placed, no new setting, no new table, no data step.

    python3 -B make_s603.py --finance /root/finance --briefs /root/deploy/repo/claude_code_briefs --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes amir_day.py, stock_app.py, stock_watch.py, amir_salts.py, DUTY_MAP.json and DUTY_MAP.md into DIR and prints each md5 -- the
installer compares them with PINS.sh. The brief: claude_code_briefs/S603_AMIR_CALENDAR_SAFE.md (v2, 20-Oct-2026, Sanjeevni session 333).
F-952: the re-export band clears on the server's receipt, never on his tap. F-953: a GET of /api/readiness never judges a start capture.
F-769: the drift page's purchase sentences read purchase_cover_how, not the calendar. F-786: the owner's waiting words say when Marg's closing
does not print the item. F-726 a: a salt the owner answered becomes a tickable line on Amir's SALT KAAM sheet; duty amir.salt_tasks (v16)."""
import argparse
import hashlib
import json
import os
import re
import sys

FROM = {
    "amir_day.py": "3af992d9e6b6c6050b1427e34757ca78",
    "stock_app.py": "4f73d0b02a167289d9439af7a35b5fa0",
    "stock_watch.py": "299c3ef76b73a10e4af1cd15974c7a3f",
    "amir_salts.py": "d8d9ba772650a4d804add6953790d14d",
    "DUTY_MAP.json": "c2ef9c6c5adb8c930b21bff5441cc017",
}
DUE_SQL = ("SELECT COUNT(*) AS n, MIN(substr(COALESCE(answer_at, pushed_at, ''), 1, 10)) AS since FROM purchase_salt_task WHERE COALESCE(done, 0) = 0 "
           "AND (section IN ('rename','create','change','cleanup') OR (section = 'waiting' AND answer IS NOT NULL AND TRIM(answer) <> ''))")
DOOR_MARKER = "Salt aur naye item: list kholiye, Marg mein sudhaar kijiye, tick lagaiye"

# =============================================================================================================== amir_day.py (3.1 - 3.3)
AD = []
AD.append(("A1 the module history", '''  * D712: Amir's bill line comes from the scan ("Scan hua bill Marg mein baaki: N"), never from a reception tap; an arrival with
    nothing scanned is the owner's line only.
"""
''', '''  * D712: Amir's bill line comes from the scan ("Scan hua bill Marg mein baaki: N"), never from a reception tap; an arrival with
    nothing scanned is the owner's line only.

S603_AMIR_CALENDAR_SAFE (20-Oct-2026; F-952, F-786, F-726 a; rule (c) of 05-Oct):
  * ONE EXPORT FACT.  _export_fact(cx, day) = the server's own receipts of a purchase export (mi_file / purchase_export) after the visit's
    first bill-entry tap; the re-export band (_reexport_due) and the owner's 48-hour line (_s603_export_lines) read it -- never his step-3 tap.
  * Step 4 reads the export that COVERS the 1st..today first (then the newest): a month-end export taken second no longer hides the covering
    one.  A pair that did not arrive says since when (his tap's hh:mm in the reason).
  * The owner's ending for a proof whose items Marg's closing does not print under their name: 'absent' (stock_app._s488_why, F-786).
"""
'''))
AD.append(("A2 the kit line", '''KIT = "S587_MORNING_FLOW"                                  # the kit that last placed this file (S533 built the page; S584 named it; S587: the export step last, the re-export line)
''', '''KIT = "S603_AMIR_CALENDAR_SAFE"                           # the kit that last placed this file (S533 built the page; S584 named it; S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner's 48-hour line)
'''))
AD.append(("A3 S488_WHYS gains absent", '''S488_WHYS = ("no_closing", "no_figure", "pur_behind", "no_before", "rebased")
''', '''S488_WHYS = ("no_closing", "no_figure", "pur_behind", "no_before", "rebased", "absent")   # S603 (F-786): absent = Marg's closing does not print them
'''))
AD.append(("A4 _export_state docstring", '''        none  he has not said he exported yet -- nothing is expected
    `wait_since` is the newest step-3 row''', '''        none  he has not said he exported yet -- nothing is expected
    S603: of the day's exports the one that COVERS the 1st..today is read first, then the newest (a month-end export taken second no longer
    hides the covering one); a pair that did not arrive carries since = his tap's hh:mm in its reason.
    `wait_since` is the newest step-3 row'''))
AD.append(("A5 _export_state: covers first, then newest; bound (kind, day, first, day)", '''             ORDER BY COALESCE(export_stamp, received_at) DESC
                LIMIT 1""",
            (kind, day),
''', '''             ORDER BY CASE WHEN substr(COALESCE(period_from,''),1,10) <= ? AND substr(COALESCE(period_to,''),1,10) >= ? THEN 0 ELSE 1 END,
                      COALESCE(export_stamp, received_at) DESC
                LIMIT 1""",
            (kind, day, first, day),
'''))
AD.append(("A6 _export_state: the bad pair says since when", '''        if row is None:
            if wait_since is None:
                state, why, en = "none", "abhi nikaali nahi gayi", "not received"
            elif within:
                state, why, en = "wait", "file ban gayi hai, aa rahi hai", "still arriving"
            else:
                state, why, en = "bad", "aaj ki nahi aayi", "today's has not arrived"
            out.append({"kind": kind, "label": label, "have": False, "state": state, "waited": waited, "reason": why, "reason_en": en})
            continue
''', '''        if row is None:
            since = None
            if wait_since is None:
                state, why, en = "none", "abhi nikaali nahi gayi", "not received"
            elif within:
                state, why, en = "wait", "file ban gayi hai, aa rahi hai", "still arriving"
            else:
                since = _hhmm(wait_since)                      # S603: since when -- the moment of his tap rides in the reason
                state, why, en = "bad", "%s baje se nahi aayi" % since, "not received since %s (his tap)" % since
            out.append({"kind": kind, "label": label, "have": False, "state": state, "waited": waited, "reason": why, "reason_en": en, "since": since})
            continue
'''))
AD.append(("A7 _export_fact and the rewritten _reexport_due", '''def _reexport_due(cx, day, ticks):
    """S587 (F-926 / D737 D): (due, since) -- True when the day's newest step-2 tap ('Sab bill daal diye') is later than the newest export fact of
    the day: his newest step-3 tap ('Dono report nikaal di'), or the newest VERIFIED purchase export that LANDED in mi_file that day (received_at;
    a fresh export landing after the tap clears it too -- the fact, not the tap, as S584's E).  False while nothing of either kind exists (then
    the step-4 gate says the report is not taken).  Rests on HIS taps (D712).  since = the step-2 tap's moment."""
    t2 = _norm_ts((ticks.get(2) or {}).get("done_at"))
    if not t2:
        return False, None
    marks = [_norm_ts((ticks.get(3) or {}).get("done_at"))]
    try:
        if _table_exists(cx, "mi_file"):
            r = cx.execute("SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file WHERE verdict='VERIFIED' "
                           "AND type IN ('PURCHASE_BILLWISE','PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,10)=?",
                           (day,)).fetchone()
            marks.append(_norm_ts(r[0]) if r and r[0] else None)
    except Exception:                                                  # noqa: BLE001
        pass
    marks = [m for m in marks if m]
    if not marks:
        return False, None
    return (t2 > max(marks)), t2
''', '''def _export_fact(cx, day):
    """S603 (F-952): THE export fact of a visit day, in one place -- (lo, fact, t2).  lo = the day's OLDEST step-2 tap ('Sab bill daal diye'),
    t2 = its newest; fact = the newest moment the SERVER received a purchase export after lo: a VERIFIED mi_file of the pair's families (the
    collector) or a purchase_export row of them (the pusher; superseded or not -- a receipt is a receipt), any day (a file landing after midnight
    counts).  Every moment through _norm_ts.  (None, None, None) when the day has no step-2 tap.  Read by _reexport_due (his band) and by
    _s603_export_lines (the owner's line) -- never his step-3 tap."""
    if not _table_exists(cx, "amir_step_log"):
        return None, None, None
    r = cx.execute("SELECT MIN(done_at), MAX(done_at) FROM amir_step_log WHERE day=? AND step=2", (day,)).fetchone()
    lo = _norm_ts(r[0]) if (r and r[0]) else None
    t2 = _norm_ts(r[1]) if (r and r[1]) else None
    if not lo or not t2:
        return None, None, None
    facts = []
    for table, sql in (("mi_file", "SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file WHERE verdict='VERIFIED' "
                                   "AND type IN ('PURCHASE_BILLWISE','PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,19) > ?"),
                       ("purchase_export", "SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM purchase_export "
                                           "WHERE type IN ('BILLWISE','ITEMWISE','BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,19) > ?")):
        try:
            if _table_exists(cx, table):
                x = cx.execute(sql, (lo,)).fetchone()
                f = _norm_ts(x[0]) if (x and x[0]) else None
                if f:
                    facts.append(f)
        except Exception:                                                  # noqa: BLE001
            pass
    return lo, (max(facts) if facts else None), t2


def _reexport_due(cx, day, ticks):
    """S587 (F-926 / D737 D), rewritten by S603 (F-952): (due, since) -- True when the day's newest step-2 tap ('Sab bill daal diye') is later
    than the day's export FACT (_export_fact: the server's newest receipt of a purchase export after the day's first step-2 tap).  Rests on his
    step-2 taps and the server's own receipts -- never on his step-3 tap (F-952: on 18-Oct the tap cleared the band and no file ever came).
    (False, None) while no fact exists yet (then the step-4 gate says the report is not taken; no band before the visit's first file).
    `ticks` is kept for the callers and is unused here.  since = the newest step-2 tap's moment."""
    _lo, fact, t2 = _export_fact(cx, day)
    if not t2 or not fact:
        return False, None
    return (t2 > fact), t2
'''))
AD.append(("A8 _s488_ending: the absent ending", '''    if why == "pur_behind":
        return head + "waiting for a purchase export that reaches that day (Amir)"
''', '''    if why == "absent":                                    # S603 (F-786): the closing came; the items are not printed under their name
        names = [str(x) for x in (pr.get("absent") or [])]
        return head + "%d item(s) not printed under their name in it: %s (still wrong in Marg — the hub's correction list; Amir)" % (
            len(names), ", ".join(names[:3]) + (" …" if len(names) > 3 else ""))
    if why == "pur_behind":
        return head + "waiting for a purchase export that reaches that day (Amir)"
'''))
AD.append(("A9 _s603_export_lines before needs_you_lines", '''

def needs_you_lines(con):
    """The owner's Needs-you lines: settle first; then (a) the salt list, (b) his own correction, (c) Darpan's claims, the count's
    stage line and verdict lines, the orthotics verified, (d) the count's vouchers, the proof's wait, D712's arrivals, the one-time
    jobs, Sarvam, the duty map's orphans and the refused reports."""
''', '''

def _s603_export_lines(cx):
    """S603 (rule (c) of 05-Oct; F-952): the owner's one line per OPEN visit day of the last 7 days (start_capture_lines's window) whose newest
    step-3 tap ('Dono report nikaal di') is amir.proof_wait_hours old or more: no export fact after the visit's first bill-entry tap -> 'never
    reached the server'; a step-2 tap after the fact -> 're-export owed'.  The fact is _export_fact's -- never _export_state (a past day's live
    pair is superseded by the next export).  Gone by itself when the fact lands.  English; a closed day (state()'s rule: the newest step-7 row
    is the close) is never named."""
    out = []
    try:
        if not _table_exists(cx, "amir_step_log"):
            return out
        lo_day = (_now() - timedelta(days=7)).strftime("%Y-%m-%d")
        wait_min = _setting(cx, "amir.proof_wait_hours") * 60
        for (day,) in cx.execute("SELECT DISTINCT day FROM amir_step_log WHERE day >= ? ORDER BY day", (lo_day,)).fetchall():
            rows = cx.execute("SELECT step, done_at, note FROM amir_step_log WHERE day=? ORDER BY id", (day,)).fetchall()
            t7 = [r for r in rows if int(r[0]) == 7]
            if t7 and t7[-1][2] == "close":
                continue
            t3s = [r[1] for r in rows if int(r[0]) == 3]
            t3 = _norm_ts(t3s[-1]) if t3s else None
            m = _mins_since(t3) if t3 else None
            if m is None or m < wait_min:
                continue
            lo, fact, t2 = _export_fact(cx, day)
            if not lo:
                continue
            ddmm = _dm_hm(day, time=False)
            if not fact:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Amir's purchase export of %s never reached the server — he tapped 'nikaal di' at %s; the day stays open until the pair lands (Amir)"
                                     % (ddmm, _dm_hm(t3))))
            elif t2 > fact:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Amir entered a bill at %s on %s after that day's export and no purchase export has landed since — re-export owed (Amir)"
                                     % (_hhmm(t2), ddmm)))
    except Exception:                                                  # noqa: BLE001
        return out
    return out


def needs_you_lines(con):
    """The owner's Needs-you lines: settle first; then (a) the salt list, (b) his own correction, (c) Darpan's claims, the count's
    stage line and verdict lines, the orthotics verified, (d) the count's vouchers, the proof's wait, D712's arrivals, S603's export
    waits (never reached / re-export owed, after amir.proof_wait_hours), the one-time jobs, Sarvam, the duty map's orphans and the
    refused reports."""
'''))
AD.append(("A10 needs_you_lines: the S603 lines after D712's", '''        out.extend(_d712_owner_lines(con, S))
        out.extend(_s494_owner_lines(con, S))
''', '''        out.extend(_d712_owner_lines(con, S))
        out.extend(_s603_export_lines(con))                    # S603 (F-952): a visit's export that never came / a re-export owed, after 48 h
        out.extend(_s494_owner_lines(con, S))
'''))

# =============================================================================================================== stock_app.py (3.4)
SA = []
SA.append(("S1 _r_stock: a read-only Ctx (F-953)", '''        ctx = _sf.Ctx(con, sp)
        cap = _sf.capture_at(sp, None, ctx)
        if cap is None:
            return out
        n_items = int(''', '''        ctx = _sf.Ctx(con, sp, read_only=True)                # S603 (F-953): a read never judges a start capture
        cap = _sf.capture_at(sp, None, ctx)
        if cap is None:
            return out
        n_items = int('''))
SA.append(("S2 the S603 helpers before readiness()", '''

def readiness(con):
    """The four data-readiness blocks, and the plain lines that print them.
''', '''

def _s603_stamp_dm(stamp):
    """A Marg export stamp (YYYYMMDD-HHMMSS) as 'dd-mm hh:mm' for the owner's sentence; 'none yet' when absent."""
    s = _sf.stamp_iso(stamp)
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if s else "none yet"


def _s603_newest_stamps(sp):
    """(bill-wise, item-wise): the newest purchase export stamp of each family, read as purchase_cover's clause (b) reads them
    (stock_figure.purchase_cover_how: sp_export ok=1 per family)."""
    try:
        b = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family='PURCHASE_BILLWISE'") or [{"s": ""}])[0]["s"] or "")
        i = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')") or [{"s": ""}])[0]["s"] or "")
    except Exception:                                          # noqa: BLE001
        b, i = "", ""
    return b, i


def _s603_purchase_wait(con):
    """S603 (F-769 / F-953): readiness()'s stock-ahead sentence by the one rule -- None when the newest usable capture (the one _r_stock names)
    is covered by a purchase export (stock_figure.purchase_cover_how: the reach, the newest exports after it, or Amir's visit cover), when the
    spine is not ready or when there is no capture (fail-soft, as before).  A read-only Ctx: this read never judges a start capture."""
    try:
        sp = _s524_spine()
        if not _sf.ready(sp):
            return None
        ctx = _sf.Ctx(con, sp, read_only=True)
        c = _sf.capture_at(sp, None, ctx)
        if c is None:
            return None
        how = _sf.purchase_cover_how(con, sp, c, _sf.reach(sp), ctx)
        if how is not None:
            return None
        nb, ni = _s603_newest_stamps(sp)
        return ("No purchase export has been taken since the closing stock of %s was captured (%s); the newest purchase exports reach %s "
                "(bill-wise) and %s (item-wise). Amir's next export settles it — count after it, not before."
                % (_r_dmy(c["as_on"]), _s603_stamp_dm(c["stamp"]), _s603_stamp_dm(nb), _s603_stamp_dm(ni)))
    except Exception:                                          # noqa: BLE001
        return None


def readiness(con):
    """The four data-readiness blocks, and the plain lines that print them.
'''))
SA.append(("S3 readiness: the purchase sentences by the one rule (F-769)", '''    if pur.get("days_behind") is not None and pur["days_behind"] > 1:
        warn.append("Purchases are %d days behind today -- anything entered into "
                    "Marg after %s is not in any figure on this page."
                    % (pur["days_behind"], _r_dmy(pur["bill_date"])))
    reach = _s488_purchase_reach(con) or str(pur.get("bill_date") or "")[:10]   # S488 (F-753): the exports' reach, as a date
    if stk.get("marg") and reach and \\
            _dmy_to_iso(stk["marg"]["as_on"])[:10] > reach:
        warn.append("The stock figure is for %s but purchases are known only to "
                    "%s. Count after the purchase export, not before it."
                    % (_r_dmy(stk["marg"]["as_on"]), _r_dmy(reach)))
''', '''    # S603 (F-769): the purchase "days behind" sentence is gone (a quiet day is not "behind"); the stock-ahead sentence reads the one rule,
    # stock_figure.purchase_cover_how over the newest usable capture (_s603_purchase_wait; a read-only Ctx -- F-953, a read never judges).
    s603 = _s603_purchase_wait(con)
    if s603:
        warn.append(s603)
'''))
SA.append(("S4 _s488_purchase_reach deleted (no other caller)", '''def _s488_purchase_reach(con):
    """The day the purchase exports in force reach (ISO), or '' when none is known."""
    try:
        r = con.execute("SELECT MAX(substr(period_to,1,10)) FROM purchase_export WHERE superseded_by IS NULL").fetchone()
        return str((r[0] if r else "") or "")
    except Exception:                                          # noqa: BLE001
        return ""


''', ''))
SA.append(("S5 _s488_why: the unseen keyword", '''def _s488_why(con, sp, closings, R, after, last_at):
    """{since, why, closing_day, closing_at} for a proof in state export -- the REASON, never the decision; {} when it cannot be had.
''', '''def _s488_why(con, sp, closings, R, after, last_at, unseen=None):
    """{since, why, closing_day, closing_at} for a proof in state export -- the REASON, never the decision; {} when it cannot be had.
    S603 (F-786): `unseen` = the verdict's unseen rows; when a clean closing came, its purchase half is not short and EVERY unseen row is
    absent_at_try (the closing does not print the item under its name) the reason is absent and out['absent'] names the items.
'''))
SA.append(("S6 _s488_why: absent when every unseen row is absent_at_try", '''        elif after:
            c = after[0]
            _ok, short = _s524_tryable(c, _s524_reach(sp), con, _sf.Ctx(con, sp))   # S587: the purchase half is purchase_cover
            why = "pur_behind" if short == "pur" else "no_figure"
''', '''        elif after:
            c = after[0]
            _ok, short = _s524_tryable(c, _s524_reach(sp), con, _sf.Ctx(con, sp))   # S587: the purchase half is purchase_cover
            if short == "pur":
                why = "pur_behind"
            elif unseen and all((u or {}).get("why") == "absent_at_try" for u in unseen):   # S603 (F-786): only absent_at_try -- absent_before is R's lack
                why = "absent"
                out["absent"] = [str((u or {}).get("item") or "") for u in unseen]
            else:
                why = "no_figure"
'''))
SA.append(("S7 _s524_verdict passes unseen", '''        res.update(_s488_why(con, sp, T["closings"], R, ([T["N"]] if (pend and T.get("N")) else after), last_at))   # S528: the newest capture is what it waits for
''', '''        res.update(_s488_why(con, sp, T["closings"], R, ([T["N"]] if (pend and T.get("N")) else after), last_at, unseen=unseen))   # S528: the newest capture is what it waits for; S603: the unseen rows
'''))

# =============================================================================================================== stock_watch.py (3.5)
SW = []
SW.append(("W1 the S603 helper and the docstring of start_capture_lines", '''def start_capture_lines(con, sp=None):
    """S587 (D740, §3.1): the owner's English lines for the start-of-day closings (stock_figure's record stock_start_capture): one per capture
    SET ASIDE in the last 7 days, naming the items that decided it by their printed names; one for a capture still PENDING more than a day after
    its day's sale report landed ('waits for Amir's purchase export'). Nobody is asked to re-print; Darpan and Shavez see nothing. Fail-soft."""
''', '''def _s603_newest(sp):
    """S603: ('dd-mm hh:mm' bill-wise, 'dd-mm hh:mm' item-wise) -- the newest purchase export stamp of each family, read as purchase_cover's
    clause (b) reads them (stock_figure.purchase_cover_how: sp_export ok=1 per family); 'none yet' when absent."""
    SF = _sf()

    def dm(stamp):
        s = SF.stamp_iso(stamp)
        return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if s else "none yet"
    try:
        b = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family='PURCHASE_BILLWISE'") or [{"s": ""}])[0]["s"] or "")
        i = str((sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')") or [{"s": ""}])[0]["s"] or "")
    except Exception:                                         # noqa: BLE001
        b, i = "", ""
    return dm(b), dm(i)


def start_capture_lines(con, sp=None):
    """S587 (D740, §3.1): the owner's English lines for the start-of-day closings (stock_figure's record stock_start_capture): one per capture
    SET ASIDE in the last 7 days, naming the items that decided it by their printed names; one for a capture still PENDING whose day's sale
    report has landed and which no purchase export covers yet (S603: stock_figure.purchase_cover_how over the capture as the judge builds it,
    end_day from the row, a read-only Ctx -- F-953; the line names the newest export of each family). Nobody is asked to re-print; Darpan and
    Shavez see nothing. Fail-soft."""
'''))
SW.append(("W2 the SELECT carries md5 and end_day", '''        for as_on, si, verdict, reason, detail in con.execute("SELECT as_on, stamp_iso, verdict, reason, detail FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso", (lo,)):
''', '''        for md5, as_on, si, end_day, verdict, reason, detail in con.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, detail FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso", (lo,)):
'''))
SW.append(("W3 the pending branch: purchase_cover_how, never a day count", '''            elif verdict == "pending" and R and str(R.get("last_sale") or "") >= str(as_on):
                landed = SF.sale_landed(sp, as_on)
                if landed and (today() - dt.date.fromisoformat(landed)).days > 1:
                    out.append(dict(cls="info", target="stock", text="Closing stock of %s waits for Amir's purchase export" % when))
''', '''            elif verdict == "pending" and R and str(R.get("last_sale") or "") >= str(as_on):
                # S603 (R1-B4): the capture as start_ready builds it -- the spine's dict with end_day from the row (a pending start capture's own
                # dict carries none) -- judged by the one rule, purchase_cover_how; a read-only Ctx (F-953). No line once an export covers it.
                ctx = SF.Ctx(con, sp, read_only=True)
                c = dict(SF.capture_of(sp, md5, ctx) or {}, md5=md5, end_day=end_day, stamp_iso=si)
                if not c.get("stamp"):
                    c["stamp"] = str(si or "")[:19].replace("-", "").replace(":", "").replace("T", "-")
                how = SF.purchase_cover_how(con, sp, c, R, ctx)
                if how is None:
                    nb, ni = _s603_newest(sp)
                    out.append(dict(cls="info", target="stock", text="Closing stock printed %s waits for a purchase export taken after it (newest: bill-wise %s, item-wise %s)"
                                    % (when, nb, ni)))
'''))

# =============================================================================================================== amir_salts.py (3.6)
AS = []
AS.append(("L1 the module docstring", '''The ticks are written into `purchase_salt_task` -- the SAME table his existing
salts page ticks -- so the two can never disagree.
"""
''', '''The ticks are written into `purchase_salt_task` -- the SAME table his existing
salts page ticks -- so the two can never disagree.

S603_AMIR_CALENDAR_SAFE (20-Oct-2026, F-726 a): a salt the owner ANSWERED (section
'waiting', answer filled) is his work too -- it rides on tab 1 as "Item ka salt
badliye -- Dr sahab ka jawab" with the answer as the exact text to copy, ticked by
id like any other line; tab 2 keeps only the unanswered ones. Duty amir.salt_tasks.
"""
'''))
AS.append(("L2 SECTIONS gains waiting", '''    "cleanup": ("Safai ka kaam",             "b"),
}
# 'waiting' is the doctor's to answer, never Amir's -- it rides along read-only.
''', '''    "cleanup": ("Safai ka kaam",             "b"),
    "waiting": ("Item ka salt badliye — Dr sahab ka jawab", "answer"),   # S603 (F-726 a): once the owner has answered, his to copy
}
# 'waiting' with no answer yet is the doctor's to answer, never Amir's -- it rides along read-only (tab 2).
'''))
AS.append(("L3 _open_tasks: the answered waiting rows, last", '''    rows = cx.execute(
        """SELECT id, section, seq, a, b, c, done
             FROM purchase_salt_task
            WHERE section IN ('rename','create','change','cleanup')
              AND COALESCE(done, 0) = 0
         ORDER BY CASE section WHEN 'rename' THEN 1 WHEN 'create' THEN 2
                               WHEN 'change' THEN 3 ELSE 4 END, seq, id"""
    ).fetchall()
''', '''    rows = cx.execute(
        """SELECT id, section, seq, a, b, c, done, answer
             FROM purchase_salt_task
            WHERE (section IN ('rename','create','change','cleanup')
                   OR (section = 'waiting' AND answer IS NOT NULL AND TRIM(answer) <> ''))
              AND COALESCE(done, 0) = 0
         ORDER BY CASE section WHEN 'rename' THEN 1 WHEN 'create' THEN 2
                               WHEN 'change' THEN 3 WHEN 'cleanup' THEN 4 ELSE 5 END, seq, id"""
    ).fetchall()
'''))
AS.append(("L4 _waiting: the unanswered only", '''        """SELECT id, a, b, c, answer FROM purchase_salt_task
            WHERE section='waiting' ORDER BY seq, id""").fetchall()]
''', '''        """SELECT id, a, b, c, answer FROM purchase_salt_task
            WHERE section='waiting' AND (answer IS NULL OR TRIM(answer) = '')
            ORDER BY seq, id""").fetchall()]
'''))
AS.append(("L5 tab 1: ABHI KYA HAI for change and waiting", '''        sh.text(r, 3, t.get("b") if t["section"] == "change" else "")
''', '''        sh.text(r, 3, t.get("b") if t["section"] in ("change", "waiting") else "")
'''))
AS.append(("L6 _apply: the SELECT carries answer", '''        cur = cx.execute("SELECT id, a, b, c, section, COALESCE(done,0) AS done "
                         "FROM purchase_salt_task WHERE id=?", (row["id"],)).fetchone()
''', '''        cur = cx.execute("SELECT id, a, b, c, section, answer, COALESCE(done,0) AS done "
                         "FROM purchase_salt_task WHERE id=?", (row["id"],)).fetchone()
'''))

EDITS = {"amir_day.py": AD, "stock_app.py": SA, "stock_watch.py": SW, "amir_salts.py": AS}

NOTE_ADD = (" S603 (20-Oct-2026; F-952, F-953, F-769, F-786, F-726 a): amir.salt_tasks added -- the open lines of his SALT KAAM sheet (rename / "
            "create / change / cleanup, and a salt the owner answered, which now rides on tab 1 as 'Item ka salt badliye -- Dr sahab ka jawab' with "
            "the answer as the exact text to copy); the door is step 6's 'Salt aur naye item' card (shown while _open_tasks is non-empty); no owner "
            "line is raised (door, no raise) -- the owner's salts page counts them; allowed_days 10 mirrors amir.marg_jobs. The sheet's open tasks "
            "had no duty row before (D648 rule 1) -- closed here. Nothing else in the map moves.")
NEW_DUTY = {
    "id": "amir.salt_tasks",
    "person": "amir",
    "duty": "Salt corrections on his SALT KAAM sheet (rename / create / change / cleanup, and a salt the owner answered -- F-726 a), each ticked with Y and uploaded",
    "duty_hi": "Salt ka kaam -- sheet download, Y likhiye, upload",
    "tile": "Amir ka kaam",
    "door": "/finance/amir/step/6",
    "door_marker": DOOR_MARKER,
    "due_sql": DUE_SQL,
    "allowed_days": 10,
    "owner_line": "Amir's salt sheet: {n} line(s) not ticked -- since {since}",
    "coded": None,
    "note": ("S603: no owner line is raised today (door, no raise -- _s444_duty_lines skips a duty with a door unless it carries raise true); the "
             "owner's salts page counts them. allowed_days 10 mirrors amir.marg_jobs (amir.job_wait_days), the one comparable duty. The "
             "parked_orthotic_S237 rows are not counted."),
}
MD_ANCHOR = "`DUTY_MAP.json` is v15.\n"
MD_ADD = ("\n**20-Oct-2026 · kit S603_AMIR_CALENDAR_SAFE (F-952, F-953, F-769, F-786, F-726 a):** `[amir.salt_tasks]` added — the open lines of "
          "his SALT KAAM sheet (rename / create / change / cleanup, and since this kit a salt the owner answered, which rides on tab 1 as \"Item ka salt "
          "badliye — Dr sahab ka jawab\" with the answer as the exact text to copy; the seven he ticked in October on the owner's page stay ticked). "
          "The door is step 6's \"Salt aur naye item: list kholiye, Marg mein sudhaar kijiye, tick lagaiye\" card; no owner line is raised (door, no "
          "raise) — the owner's salts page counts them. The sheet's open tasks had no duty row before (D648 rule 1) — closed here. No other "
          "login's list changes. `DUTY_MAP.json` is v16.\n")


def apply(src, edits, label, pin):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != pin:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, pin))
        return None
    t = raw.decode("utf-8")
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def build_duty_map(path):
    raw = open(path, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM["DUTY_MAP.json"]:
        print("STOP: %s is %s, not the FROM pin %s (v15) -- nothing built" % (path, m, FROM["DUTY_MAP.json"]))
        return None
    j = json.loads(raw.decode("utf-8"))
    if (json.dumps(j, indent=1, ensure_ascii=False) + "\n").encode("utf-8") != raw:
        print("STOP: DUTY_MAP.json does not round-trip byte-equal (indent=1) -- nothing built")
        return None
    if j.get("version") != 15 or any(d.get("id") == "amir.salt_tasks" for d in j["duties"]):
        print("STOP: DUTY_MAP.json is not v15 without amir.salt_tasks -- nothing built")
        return None
    ids = [d["id"] for d in j["duties"]]
    at = ids.index("amir.marg_jobs") + 1
    j["duties"].insert(at, dict(NEW_DUTY))
    j["version"] = 16
    j["kit"] = "S603_AMIR_CALENDAR_SAFE"
    j["_note"] = j["_note"] + NOTE_ADD
    out = (json.dumps(j, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    back = json.loads(out.decode("utf-8"))
    d = [x for x in back["duties"] if x["id"] == "amir.salt_tasks"][0]
    assert d["due_sql"] == DUE_SQL and d["door_marker"] == DOOR_MARKER and back["version"] == 16 and len(back["duties"]) == len(ids) + 1
    print("edit DUTY_MAP.json: amir.salt_tasks inserted after amir.marg_jobs; v15 -> v16")
    return out


def build_duty_md(path):
    raw = open(path, "rb").read()
    t = raw.decode("utf-8")
    if t.count(MD_ANCHOR) != 1 or "S603_AMIR_CALENDAR_SAFE" in t:
        print("STOP: DUTY_MAP.md anchor (the S593 line's end) occurs %d times, or the S603 line is already there -- nothing built" % t.count(MD_ANCHOR))
        return None
    t = t.replace(MD_ANCHOR, MD_ANCHOR + MD_ADD, 1)
    print("edit DUTY_MAP.md: the one dated S603 line after the S593 line")
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--briefs", required=True, help="the folder holding DUTY_MAP.json and DUTY_MAP.md (the clone's claude_code_briefs)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(os.path.join(a.finance, label), edits, label, FROM[label])
        if out is None:
            return 2
        built[label] = out
    dm = build_duty_map(os.path.join(a.briefs, "DUTY_MAP.json"))
    if dm is None:
        return 2
    built["DUTY_MAP.json"] = dm
    md = build_duty_md(os.path.join(a.briefs, "DUTY_MAP.md"))
    if md is None:
        return 2
    built["DUTY_MAP.md"] = md
    ad = built["amir_day.py"].decode("utf-8")
    sa = built["stock_app.py"].decode("utf-8")
    sw = built["stock_watch.py"].decode("utf-8")
    sl = built["amir_salts.py"].decode("utf-8")
    old_sa = open(os.path.join(a.finance, "stock_app.py"), "rb").read().decode("utf-8")
    # ---- the grep proofs of the brief's section 3.7, on the built text
    assert ad.count("def _export_fact(") == 1 and ad.count("= _export_fact(cx, ") == 2, "_export_fact: defined once, called twice"
    rd = ad[ad.find("def _reexport_due("):ad.find("def state(")]
    assert "ticks.get(3)" not in rd and "substr(replace(received_at,'T',' '),1,10)=?" not in rd, "_reexport_due: no step-3 mark, no same-day cut"
    assert ad.count("ORDER BY CASE WHEN substr(COALESCE(period_from,''),1,10) <= ?") == 1, "the covering ORDER BY once"
    assert ad.count("baje se nahi aayi") == 1, "baje se nahi aayi once"
    assert ad.count("def _s603_export_lines(") == 1 and ad.count("_s603_export_lines(con)") == 1, "_s603_export_lines: defined once, called once"
    assert ad.count('"absent"') == 3 and 'KIT = "S603_AMIR_CALENDAR_SAFE"' in ad, "S488_WHYS and _s488_ending (the test, the names) carry absent; the kit line"
    assert sa.count("days behind today") == 1 and "_s488_purchase_reach" not in sa, "the sale sentence stays; the dead reach is gone"
    assert sa.count('"absent"') == 2 and sa.count("last_at, unseen=unseen)") == 1 and sa.count("unseen=None") == 1, "absent in _s488_why only (the why, the names); the call passes unseen"
    assert sa.count("read_only=True") == 2 and sa.count("purchase_cover_how(") == 1, "readiness and _r_stock read-only; purchase_cover_how once"
    assert sa.count("_sf.Ctx(") == old_sa.count("_sf.Ctx(") + 1, "one Ctx added in stock_app (readiness's read-only one), none removed"
    assert sw.count("read_only=True") == 1 and sw.count("purchase_cover_how(") == 1 and "waits for Amir's purchase export" not in sw, "start_capture_lines"
    assert sl.count('"waiting": ("Item ka salt badliye') == 1 and sl.count("TRIM(answer)") == 2, "amir_salts: the section and the two filters"
    assert built["DUTY_MAP.json"].decode("utf-8").count('"amir.salt_tasks"') == 1, "amir.salt_tasks once in the JSON"
    for label, out in built.items():
        assert not re.search(rb"\d{10}", out), "a run of ten digits in %s" % label
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM.get(label, "-")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
