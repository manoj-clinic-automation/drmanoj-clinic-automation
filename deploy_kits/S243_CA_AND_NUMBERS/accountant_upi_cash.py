#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""accountant_upi_cash.py -- the MONTHLY accountant report: UPI booked as cash.

THE RULING (the chartered accountant, relayed by the owner, 13-Sep-2026)
    No UPI <-> cash correction is to be made in Marg any more. Correcting a
    bill's payment mode re-opens a closed sale bill to unauthorised edits, and
    the sale register must stay as it was printed. The SYSTEM keeps the record
    -- which bills the bank proves were paid by UPI though Marg rang them as
    cash -- and that record becomes part of the MONTHLY accountant pack.

    So `/finance/darpan/corrections` is no longer a task list (its page says so,
    in Hindi, and its tick controls are hidden -- the route and the API stand),
    the health page's red "Correction checklist" is an informational line, and
    THIS module is where the data goes: one English page per month for the
    owner and the accountant, a print view, and a real .xlsx written with the
    standard library (padwriter.py, already beside the finance app).

WHAT IT READS (read-only; it creates nothing and writes nothing)
    upi_match        status='cash' -- bank_match.py's per-bill verdict: a settled
                     UPI transaction whose amount matches a bill Marg rang as
                     CASH. date / bill / amount / bank ref (RRN) / matched-on,
                     plus Darpan's answer (resolution) where he gave one.
    darpan_correction  the historic ticks ("done in Marg") from before the
                     ruling -- shown as history, never asked for again.
    mode_change_log  bills whose payment mode flipped when a day was re-imported
                     (the hub card "Cash <-> UPI reclassified bills").
    marg_correction  the S195 day-level checklist: books vs bank per day. Kept
                     as the day-level view of the same disagreement.
    Any of these tables may be absent on a fresh database: each section then
    reads as empty, never as an error.

ROUTES (all checker only -- the owner and the accountant's login)
    /finance/accountant/upi-cash                -> this month
    /finance/accountant/upi-cash/<yyyy-mm>      the page   (?print=1 = print view)
    /finance/accountant/upi-cash/<yyyy-mm>.xlsx the workbook (three sheets)
    /finance/accountant/api/upi-cash/<yyyy-mm>  the same as JSON

INSTALL: mounted from finance_app.py by patch_ca_and_numbers_s243.py, guarded --
a fault here is printed to the journal and every other page keeps serving.
Flask and the standard library only. No patient identity is read or shown:
bill numbers, amounts, bank references and dates -- an accountant's columns.
"""
import datetime as dt
import json
import os
import re
import sqlite3
from html import escape

from flask import Blueprint, Response, jsonify, redirect, request

HERE = os.path.dirname(os.path.abspath(__file__))
bp = Blueprint("accountant_upi_cash", __name__)

_db = None
_require = None
_unit = "medical"
_login = "/portal"

RULING_LINE = ("Per the chartered accountant's ruling of 13-Sep-2026 these bills are NOT "
               "corrected in Marg: the sale register stays as printed (Marg shows CASH), the "
               "bank statement shows the payment as UPI, and this report is the month's "
               "reconciliation record between the two.")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def init(app, db_getter, require_fn, unit="medical", login=None):
    global _db, _require, _unit, _login
    _db, _require, _unit = db_getter, require_fn, unit
    if login:
        _login = login
    app.register_blueprint(bp)
    return bp


# ------------------------------------------------------------------ helpers
def rupees(p):
    """Indian grouping, two decimals, as the finance app prints money."""
    if p is None:
        return ""
    sign = "-" if p < 0 else ""
    p = abs(int(p))
    whole, frac = divmod(p, 100)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return "%s%s.%02d" % (sign, s, frac)


def _has(con, table):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                           (table,)).fetchone() is not None
    except sqlite3.Error:
        return False


def _rows(con, sql, args=()):
    try:
        return [dict(zip([d[0] for d in cur.description], r))
                for cur in (con.execute(sql, args),) for r in cur.fetchall()]
    except sqlite3.Error:
        return []


def month_label(ym):
    try:
        return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except ValueError:
        return ym


def this_month():
    return dt.date.today().strftime("%Y-%m")


# ------------------------------------------------------------------ the data
def month_report(con, ym, unit=None):
    """Everything the page, the workbook and the JSON show. Pure read."""
    unit = unit or _unit
    out = dict(ok=True, month=ym, label=month_label(ym), unit=unit, ruling=RULING_LINE,
               generated_at=dt.datetime.now().replace(microsecond=0).isoformat(),
               bills=[], reclass=[], days=[], months=[],
               totals=dict(bills_n=0, bills_p=0, answered_n=0, ticked_before_ruling_n=0,
                           reclass_n=0, reclass_to_upi_p=0, reclass_to_cash_p=0,
                           days_n=0, days_upi_as_cash_p=0, days_cash_as_upi_p=0))
    months = set()

    # A -- the bank proves UPI, Marg rang cash (bank_match.py, per bill)
    if _has(con, "upi_match"):
        ticks = {}
        if _has(con, "darpan_correction"):
            for t in _rows(con, "SELECT match_id, ticked_by, ticked_at, note FROM darpan_correction"):
                ticks[t["match_id"]] = t
        for r in _rows(con,
                       "SELECT id, business_date, bill_no, bill_amount_p, txn_amount_p, rrn, "
                       "txn_time, txn_mode, off_by_p, resolved, resolved_at, resolution, matched_at "
                       "FROM upi_match WHERE unit=? AND status='cash' "
                       "AND substr(business_date,1,7)=? "
                       "ORDER BY business_date, txn_time, id", (unit, ym)):
            t = ticks.get(r["id"]) or {}
            amt = int(r["txn_amount_p"] if r["txn_amount_p"] is not None else (r["bill_amount_p"] or 0))
            out["bills"].append(dict(
                id=r["id"], date=r["business_date"], bill=r["bill_no"] or "",
                amount_p=amt, amount=rupees(amt),
                bill_amount_p=r["bill_amount_p"], bank_ref=r["rrn"] or "",
                bank_time=r["txn_time"] or "", bank_mode=r["txn_mode"] or "UPI",
                off_by_p=int(r["off_by_p"] or 0),
                matched_on=(r["matched_at"] or "")[:16].replace("T", " "),
                answer=r["resolution"] or "", answered_by=r["resolved"] or "",
                answered_at=(r["resolved_at"] or "")[:16].replace("T", " "),
                ticked_by=t.get("ticked_by") or "", ticked_at=(t.get("ticked_at") or "")[:16].replace("T", " ")))
        out["totals"]["bills_n"] = len(out["bills"])
        out["totals"]["bills_p"] = sum(b["amount_p"] for b in out["bills"])
        out["totals"]["answered_n"] = sum(1 for b in out["bills"] if b["answered_by"])
        out["totals"]["ticked_before_ruling_n"] = sum(1 for b in out["bills"] if b["ticked_by"])
        months.update(r["m"] for r in _rows(
            con, "SELECT DISTINCT substr(business_date,1,7) m FROM upi_match "
                 "WHERE unit=? AND status='cash'", (unit,)))

    # B -- the payment mode flipped on a re-import (finance_ingest, S194 star-3)
    if _has(con, "mode_change_log"):
        for r in _rows(con,
                       "SELECT business_date, source_ref, amount_p, old_mode, new_mode, changed_at "
                       "FROM mode_change_log WHERE unit=? AND substr(business_date,1,7)=? "
                       "ORDER BY business_date, id", (unit, ym)):
            amt = int(r["amount_p"] or 0)
            out["reclass"].append(dict(
                date=r["business_date"], bill=r["source_ref"] or "", amount_p=amt, amount=rupees(amt),
                from_mode=(r["old_mode"] or "").upper(), to_mode=(r["new_mode"] or "").upper(),
                changed_on=(r["changed_at"] or "")[:16].replace("T", " ")))
            if (r["new_mode"] or "").lower() == "upi":
                out["totals"]["reclass_to_upi_p"] += amt
            elif (r["new_mode"] or "").lower() == "cash":
                out["totals"]["reclass_to_cash_p"] += amt
        out["totals"]["reclass_n"] = len(out["reclass"])
        months.update(r["m"] for r in _rows(
            con, "SELECT DISTINCT substr(business_date,1,7) m FROM mode_change_log WHERE unit=?", (unit,)))

    # C -- the day-level disagreement, books vs bank (the S195 checklist rows)
    if _has(con, "marg_correction"):
        for r in _rows(con,
                       "SELECT business_date, diff_p, direction, status, note, created_at, resolved_at "
                       "FROM marg_correction WHERE unit=? AND substr(business_date,1,7)=? "
                       "ORDER BY business_date", (unit, ym)):
            d = int(r["diff_p"] or 0)
            says = "UPI booked as cash" if r["direction"] == "upi_as_cash" else "cash booked as UPI"
            out["days"].append(dict(date=r["business_date"], diff_p=d, diff=rupees(abs(d)),
                                    direction=r["direction"] or "", says=says,
                                    status=r["status"] or "", note=r["note"] or "",
                                    noted_on=(r["created_at"] or "")[:10]))
            if r["direction"] == "upi_as_cash":
                out["totals"]["days_upi_as_cash_p"] += abs(d)
            else:
                out["totals"]["days_cash_as_upi_p"] += abs(d)
        out["totals"]["days_n"] = len(out["days"])
        months.update(r["m"] for r in _rows(
            con, "SELECT DISTINCT substr(business_date,1,7) m FROM marg_correction WHERE unit=?", (unit,)))

    months.add(ym)
    months.add(this_month())
    out["months"] = sorted((m for m in months if m and MONTH_RE.match(m)), reverse=True)
    out["totals"]["bills_total"] = rupees(out["totals"]["bills_p"])
    out["totals"]["reclass_to_upi"] = rupees(out["totals"]["reclass_to_upi_p"])
    out["totals"]["reclass_to_cash"] = rupees(out["totals"]["reclass_to_cash_p"])
    out["totals"]["days_upi_as_cash"] = rupees(out["totals"]["days_upi_as_cash_p"])
    out["totals"]["days_cash_as_upi"] = rupees(out["totals"]["days_cash_as_upi_p"])
    return out


def month_count(con, ym=None, unit=None):
    """(count, paise) of section A for the health line. Never raises."""
    ym = ym or this_month()
    unit = unit or _unit
    if not _has(con, "upi_match"):
        return 0, 0
    r = _rows(con, "SELECT COUNT(*) n, COALESCE(SUM(txn_amount_p),0) p FROM upi_match "
                   "WHERE unit=? AND status='cash' AND substr(business_date,1,7)=?", (unit, ym))
    return (int(r[0]["n"] or 0), int(r[0]["p"] or 0)) if r else (0, 0)


# ------------------------------------------------------------------ the workbook
def workbook(rep):
    """Three sheets through padwriter (stdlib). Raises ImportError when
    padwriter.py is not beside this file -- the route turns that into a 503."""
    import padwriter as PW                                   # noqa: PLC0415

    def head(sh, title, sub):
        sh.text(1, 0, title, PW.TITLE)
        sh.text(2, 0, sub, PW.NOTE)
        sh.text(3, 0, RULING_LINE, PW.NOTE)
        sh.text(4, 0, "Generated", PW.BOLD)
        sh.text(4, 1, rep["generated_at"].replace("T", " "), PW.NORMAL)

    def table(sh, r0, cols, widths, rows, num_cols=()):
        for i, c in enumerate(cols):
            sh.text(r0, i, c, PW.HEADER)
        r = r0 + 1
        for row in rows:
            for i, v in enumerate(row):
                if i in num_cols:
                    sh.num(r, i, v, PW.BOX)
                else:
                    sh.text(r, i, v, PW.BOX)
            r += 1
        sh.widths.update(widths)
        sh.freeze = "A%d" % (r0 + 1)
        if rows:
            sh.filter = "A%d:%s%d" % (r0, PW._colname(len(cols) - 1), r - 1)
        sh.print_title_rows = (r0, r0)
        return r

    T = rep["totals"]
    # sheet 1 -- the bills
    s1 = PW.Sheet()
    head(s1, "UPI booked as cash -- %s" % rep["label"],
         "Sanjeevni Medicos (unit %s). Bills the bank statement settles by UPI that Marg rang as CASH. "
         "Amounts in rupees." % rep["unit"])
    s1.text(6, 0, "Bills", PW.BOLD); s1.num(6, 1, T["bills_n"], PW.BOLD)
    s1.text(6, 3, "Total (Rs)", PW.BOLD); s1.num(6, 4, T["bills_p"] / 100.0, PW.BOLD)
    s1.text(7, 0, "With Darpan's answer", PW.BOLD); s1.num(7, 1, T["answered_n"], PW.BOLD)
    s1.text(7, 3, "Corrected in Marg before the ruling", PW.BOLD); s1.num(7, 4, T["ticked_before_ruling_n"], PW.BOLD)
    r = table(s1, 9,
              ["Bill date", "Bill no", "Amount (Rs)", "Bank ref (RRN)", "Bank time", "Bank mode",
               "Matched on", "Darpan's answer", "Answered by", "Corrected in Marg (pre-ruling)"],
              {0: 12, 1: 12, 2: 13, 3: 18, 4: 10, 5: 10, 6: 17, 7: 16, 8: 12, 9: 26},
              [(b["date"], b["bill"], b["amount_p"] / 100.0, b["bank_ref"], b["bank_time"], b["bank_mode"],
                b["matched_on"], b["answer"], b["answered_by"],
                ("%s %s" % (b["ticked_by"], b["ticked_at"])).strip()) for b in rep["bills"]],
              num_cols=(2,))
    if rep["bills"]:
        s1.text(r, 1, "TOTAL", PW.BOLD)
        s1.formula(r, 2, "SUM(C10:C%d)" % (r - 1), PW.BOLDBOX)
    else:
        s1.text(r, 0, "No such bill this month.", PW.NOTE)

    # sheet 2 -- mode changed on re-import
    s2 = PW.Sheet()
    head(s2, "Payment mode changed on re-import -- %s" % rep["label"],
         "A bill seen earlier with one payment mode and later re-loaded from Marg with the other. "
         "Recorded by the ingest; nobody is asked to act.")
    s2.text(6, 0, "Changes", PW.BOLD); s2.num(6, 1, T["reclass_n"], PW.BOLD)
    s2.text(6, 3, "Now UPI (Rs)", PW.BOLD); s2.num(6, 4, T["reclass_to_upi_p"] / 100.0, PW.BOLD)
    s2.text(7, 3, "Now CASH (Rs)", PW.BOLD); s2.num(7, 4, T["reclass_to_cash_p"] / 100.0, PW.BOLD)
    r = table(s2, 9, ["Bill date", "Bill no", "Amount (Rs)", "Was", "Now", "Changed on"],
              {0: 12, 1: 12, 2: 13, 3: 8, 4: 8, 5: 17},
              [(x["date"], x["bill"], x["amount_p"] / 100.0, x["from_mode"], x["to_mode"], x["changed_on"])
               for x in rep["reclass"]], num_cols=(2,))
    if not rep["reclass"]:
        s2.text(r, 0, "No payment-mode change this month.", PW.NOTE)

    # sheet 3 -- day-level split difference
    s3 = PW.Sheet()
    head(s3, "Day-level cash / UPI difference, books vs bank -- %s" % rep["label"],
         "Per day: the non-cash the books carry against what the bank settled. The record of the "
         "S195 checklist, kept -- no longer worked in Marg.")
    s3.text(6, 0, "Days", PW.BOLD); s3.num(6, 1, T["days_n"], PW.BOLD)
    s3.text(6, 3, "UPI booked as cash (Rs)", PW.BOLD); s3.num(6, 4, T["days_upi_as_cash_p"] / 100.0, PW.BOLD)
    s3.text(7, 3, "Cash booked as UPI (Rs)", PW.BOLD); s3.num(7, 4, T["days_cash_as_upi_p"] / 100.0, PW.BOLD)
    r = table(s3, 9, ["Day", "Difference (Rs)", "Which way", "Checklist status (historic)", "Note", "First noted"],
              {0: 12, 1: 15, 2: 20, 3: 26, 4: 30, 5: 12},
              [(d["date"], abs(d["diff_p"]) / 100.0, d["says"], d["status"], d["note"], d["noted_on"])
               for d in rep["days"]], num_cols=(1,))
    if not rep["days"]:
        s3.text(r, 0, "No day-level difference this month.", PW.NOTE)

    return PW.workbook_bytes_multi([("UPI booked as cash", s1), ("Mode changed", s2), ("Day level", s3)])


# ------------------------------------------------------------------ the page
CSS = """
:root{--page:#f3f2ee;--card:#fbfaf8;--line:#e6e3dc;--t1:#23272f;--t2:#5d6470;--t3:#8a8f99;--acc:#1c5cab}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--t1);
font:14.5px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-variant-numeric:tabular-nums}
.wrap{max-width:980px;margin:0 auto;padding:16px 14px 80px}
h1{font-size:21px;margin:4px 0 2px}h2{font-size:16px;margin:0 0 8px}
.kick{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--t3)}
.sub{color:var(--t2);font-size:13px;margin-bottom:12px}
.ruling{background:#fff8e6;border:1px solid #efd9a3;border-radius:10px;padding:10px 14px;margin:10px 0 16px;font-size:13.5px}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:8px 0 14px}
.bar a,.bar button,.bar select{font:inherit;font-size:13.5px;padding:7px 12px;border:1px solid var(--line);
border-radius:9px;background:#fff;color:var(--acc);text-decoration:none;cursor:pointer}
.stats{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0 12px}
.stat{background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px 14px;min-width:150px}
.stat .l{font-size:11.5px;color:var(--t3)}.stat .v{font-size:19px;font-weight:700}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:14px 0}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.5px}
th,td{padding:7px 8px;border-bottom:1px solid #eee;text-align:left;vertical-align:top}
th{background:#efece7;font-weight:600}td.r,th.r{text-align:right}
tfoot td{font-weight:700;border-top:2px solid var(--line)}
.mut{color:var(--t3)}.empty{color:var(--t3);padding:8px 0}
.foot{color:var(--t3);font-size:12px;margin-top:20px}
@media print{body{background:#fff}.bar,.noprint{display:none!important}.card{border:0;padding:0;margin:18px 0;page-break-inside:avoid}
.wrap{max-width:none;padding:0}table{font-size:12px}}
"""


def _page(rep, print_view=False):
    e = escape
    T = rep["totals"]
    ym = rep["month"]
    opts = "".join('<option value="%s"%s>%s</option>'
                   % (e(m), ' selected' if m == ym else '', e(month_label(m))) for m in rep["months"])
    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width, initial-scale=1">'
         '<title>UPI booked as cash -- %s -- accountant report</title><style>%s</style></head><body>'
         '<div class="wrap">' % (e(rep["label"]), CSS),
         '<div class="kick">Sanjeevni Medicos &middot; accountant pack &middot; unit %s</div>' % e(rep["unit"]),
         '<h1>UPI booked as cash &mdash; %s</h1>' % e(rep["label"]),
         '<div class="sub">Bills the bank statement settles by UPI that Marg rang as CASH, with the bank '
         'reference for each. Generated %s.</div>' % e(rep["generated_at"].replace("T", " ")),
         '<div class="ruling"><b>Why nothing is corrected in Marg.</b> %s</div>' % e(RULING_LINE),
         '<div class="bar noprint"><label for="m">Month</label> <select id="m" onchange="location.href='
         '\'/finance/accountant/upi-cash/\'+this.value">%s</select>'
         '<a href="/finance/accountant/upi-cash/%s.xlsx">Download .xlsx</a>'
         '<a href="/finance/accountant/upi-cash/%s?print=1" target="_blank">Print view</a>'
         '<button onclick="window.print()">Print</button>'
         '<a href="/finance/approvals#reclassCard">Hub &#8599;</a>'
         '<a href="/finance/darpan/corrections">Record page (Hindi) &#8599;</a></div>' % (opts, e(ym), e(ym)),
         '<div class="stats">'
         '<div class="stat"><div class="l">Bills, UPI rung as cash</div><div class="v">%d</div></div>'
         '<div class="stat"><div class="l">Total &#8377;</div><div class="v">%s</div></div>'
         '<div class="stat"><div class="l">With Darpan\'s answer</div><div class="v">%d</div></div>'
         '<div class="stat"><div class="l">Mode changed on re-import</div><div class="v">%d</div></div>'
         '<div class="stat"><div class="l">Days differing, books vs bank</div><div class="v">%d</div></div>'
         '</div>' % (T["bills_n"], e(T["bills_total"]), T["answered_n"], T["reclass_n"], T["days_n"])]

    # A
    h.append('<div class="card"><div class="kick">Section A &middot; per bill</div>'
             '<h2>Bank proves UPI, Marg rang cash</h2>')
    if rep["bills"]:
        h.append('<div style="overflow-x:auto"><table><thead><tr><th>Bill date</th><th>Bill no</th>'
                 '<th class="r">Amount &#8377;</th><th>Bank ref (RRN)</th><th>Bank time</th><th>Matched on</th>'
                 '<th>Darpan\'s answer</th><th>Corrected in Marg (pre-ruling)</th></tr></thead><tbody>')
        for b in rep["bills"]:
            h.append('<tr><td>%s</td><td><b>%s</b></td><td class="r">%s</td><td>%s</td><td>%s</td><td>%s</td>'
                     '<td>%s</td><td>%s</td></tr>'
                     % (e(b["date"]), e(b["bill"] or "?"), e(b["amount"]), e(b["bank_ref"]), e(b["bank_time"]),
                        e(b["matched_on"]),
                        ("%s &middot; %s" % (e(b["answered_by"]), e(b["answer"] or "—"))) if b["answered_by"]
                        else '<span class="mut">not asked / no answer</span>',
                        ('&#10003; %s %s' % (e(b["ticked_by"]), e(b["ticked_at"]))) if b["ticked_by"]
                        else '<span class="mut">&mdash;</span>'))
        h.append('</tbody><tfoot><tr><td></td><td>TOTAL &middot; %d bill(s)</td><td class="r">%s</td>'
                 '<td colspan="5"></td></tr></tfoot></table></div>' % (T["bills_n"], e(T["bills_total"])))
    else:
        h.append('<div class="empty">No such bill this month.</div>')
    h.append('</div>')

    # B
    h.append('<div class="card"><div class="kick">Section B &middot; per bill</div>'
             '<h2>Payment mode changed when a day was re-imported</h2>')
    if rep["reclass"]:
        h.append('<div style="overflow-x:auto"><table><thead><tr><th>Bill date</th><th>Bill no</th>'
                 '<th class="r">Amount &#8377;</th><th>Was</th><th>Now</th><th>Changed on</th></tr></thead><tbody>')
        for x in rep["reclass"]:
            h.append('<tr><td>%s</td><td><b>%s</b></td><td class="r">%s</td><td>%s</td><td><b>%s</b></td><td>%s</td></tr>'
                     % (e(x["date"]), e(x["bill"]), e(x["amount"]), e(x["from_mode"]), e(x["to_mode"]), e(x["changed_on"])))
        h.append('</tbody><tfoot><tr><td></td><td>%d change(s)</td><td class="r"></td><td colspan="3">'
                 'now UPI %s &middot; now CASH %s</td></tr></tfoot></table></div>'
                 % (T["reclass_n"], e(T["reclass_to_upi"]), e(T["reclass_to_cash"])))
    else:
        h.append('<div class="empty">No payment-mode change this month.</div>')
    h.append('</div>')

    # C
    h.append('<div class="card"><div class="kick">Section C &middot; per day</div>'
             '<h2>Day-level cash / UPI difference, books vs bank</h2>')
    if rep["days"]:
        h.append('<table><thead><tr><th>Day</th><th class="r">Difference &#8377;</th><th>Which way</th>'
                 '<th>Checklist status (historic)</th><th>Note</th></tr></thead><tbody>')
        for d in rep["days"]:
            h.append('<tr><td>%s</td><td class="r">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                     % (e(d["date"]), e(d["diff"]), e(d["says"]), e(d["status"]), e(d["note"])))
        h.append('</tbody><tfoot><tr><td>%d day(s)</td><td class="r"></td><td colspan="3">UPI booked as cash %s'
                 ' &middot; cash booked as UPI %s</td></tr></tfoot></table>'
                 % (T["days_n"], e(T["days_upi_as_cash"]), e(T["days_cash_as_upi"])))
    else:
        h.append('<div class="empty">No day-level difference this month.</div>')
    h.append('</div>')

    h.append('<div class="foot">Source: upi_match (bank_match.py), mode_change_log (ingest), marg_correction '
             '(S195). Read-only; nothing on this page changes a book. The Hindi record page for staff is '
             '/finance/darpan/corrections (read-only since the ruling).</div>')
    if print_view:
        h.append('<script>window.addEventListener("load",function(){setTimeout(function(){window.print()},300)})</script>')
    h.append('</div></body></html>')
    return "".join(h)


# ------------------------------------------------------------------ routes
def _month_or_400(ym):
    ym = (ym or "").strip()
    if not MONTH_RE.match(ym):
        return None
    return ym


@bp.route("/finance/accountant/upi-cash")
def page_this_month():
    u, err = _require("checker")
    if err:
        return redirect(_login, code=302)
    return redirect("/finance/accountant/upi-cash/%s" % this_month(), code=302)


@bp.route("/finance/accountant/upi-cash/<ym>")
def page_month(ym):
    u, err = _require("checker")
    if err:
        return redirect(_login, code=302)
    ym = _month_or_400(ym)
    if not ym:
        return Response("month must look like 2026-09", status=400, mimetype="text/plain")
    rep = month_report(_db(), ym)
    html = _page(rep, print_view=str(request.args.get("print") or "") in ("1", "yes"))
    return Response(html, mimetype="text/html", headers={"Cache-Control": "no-store"})


@bp.route("/finance/accountant/upi-cash/<ym>.xlsx")
def xlsx_month(ym):
    u, err = _require("checker")
    if err:
        return err
    ym = _month_or_400(ym)
    if not ym:
        return jsonify(ok=False, error="bad_month", message="month must look like 2026-09"), 400
    rep = month_report(_db(), ym)
    try:
        data = workbook(rep)
    except ImportError:
        return jsonify(ok=False, error="padwriter_missing",
                       message="padwriter.py is not beside the finance app; the page and the JSON still work."), 503
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="UPI_booked_as_cash_%s.xlsx"' % ym,
                             "Cache-Control": "no-store"})


@bp.route("/finance/accountant/api/upi-cash/<ym>")
def api_month(ym):
    u, err = _require("checker")
    if err:
        return err
    ym = _month_or_400(ym)
    if not ym:
        return jsonify(ok=False, error="bad_month", message="month must look like 2026-09"), 400
    return jsonify(**month_report(_db(), ym))


# ------------------------------------------------------------------ offline selftest
if __name__ == "__main__":
    import sys
    import tempfile
    import zipfile
    tmp = tempfile.mkdtemp(prefix="acu_")
    con = sqlite3.connect(os.path.join(tmp, "t.db"))
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE upi_match (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, status TEXT, rrn TEXT,
      txn_amount_p INTEGER, txn_mode TEXT, txn_time TEXT, bill_no TEXT, bill_amount_p INTEGER, bill_mode TEXT,
      off_by_p INTEGER, resolved TEXT, resolved_at TEXT, resolution TEXT, matched_at TEXT);
    INSERT INTO upi_match VALUES (1,'medical','2026-09-03','cash','RRNWALK1',62000,'UPI','10:12','A3',62000,'cash',0,
      'darpan','2026-09-04T09:00:00','was_upi','2026-09-04T08:45:00');
    INSERT INTO upi_match VALUES (2,'medical','2026-09-05','cash','RRNWALK2',21000,'UPI','17:40','A9',21000,'cash',0,
      NULL,NULL,NULL,'2026-09-06T08:45:00');
    INSERT INTO upi_match VALUES (3,'medical','2026-09-05','agreed','RRNWALK3',50000,'UPI','11:00','A8',50000,'upi',0,
      NULL,NULL,NULL,'2026-09-06T08:45:00');
    INSERT INTO upi_match VALUES (4,'medical','2026-08-30','cash','RRNOLD',10000,'UPI','11:00','Z1',10000,'cash',0,
      NULL,NULL,NULL,'2026-08-31T08:45:00');
    """)
    rep = month_report(con, "2026-09", "medical")
    ok = (rep["totals"]["bills_n"] == 2 and rep["totals"]["bills_p"] == 83000
          and rep["totals"]["answered_n"] == 1 and rep["months"][:2] == sorted({"2026-09", "2026-08", this_month()}, reverse=True)[:2]
          and rep["reclass"] == [] and rep["days"] == [])
    print("selftest month_report:", "PASS" if ok else "FAIL", json.dumps(rep["totals"]))
    html = _page(rep)
    print("selftest page:", "PASS" if ("RRNWALK1" in html and "830.00" in html and "A9" in html) else "FAIL")
    try:
        sys.path.insert(0, HERE)
        sys.path.insert(0, os.environ.get("PADWRITER_DIR", "/root/finance"))
        data = workbook(rep)
        z = zipfile.ZipFile(__import__("io").BytesIO(data))
        names = z.namelist()
        s1 = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        print("selftest xlsx:", "PASS" if ("xl/worksheets/sheet3.xml" in names and "RRNWALK1" in s1 and "SUM(C10:C11)" in s1) else "FAIL", len(data), "bytes")
    except ImportError as ex:
        print("selftest xlsx: SKIP (padwriter not importable here: %s)" % ex)
    sys.exit(0 if ok else 1)
