#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finance_clinic_day.py -- S223: the clinic's day revenue, on a screen.

THE OWNER, launching it: view for himself, Dr Bhawna, Shavez, Shivani and Alisha, "with a pdf
print feature also".

WHERE THE FIGURES COME FROM -- D367, his ruling of this session:
    "if totalling error is on docterz, sort it out, from individual entries, its their
     reporting method which is fixed, we can fix our side only"
Every number on this page was computed from the itemised lines of the Day Revenue sheet by
`docterz_ingest.py` and stored in `clinic_day_revenue`. The sheet's own SUMMARY, Cash and
Online/UPI lines are recorded in that table and are NOT DISPLAYED HERE, deliberately: on 18 of
the first 68 days they disagree with the sheet's own total, and he ruled that showing two
numbers and a difference gives everyone something to decipher instead of something to use.
The disagreement lives in `variance_note`, for whoever is fixing it.

WHO SEES IT. `require("maker", "checker", unit="clinic")` -- the clinic roles that already
exist. That is exactly the five people he named and nobody else, with no new list to drift.

NO JAVASCRIPT. The page is rendered server-side and prints as it stands: Ctrl-P, or the Print
button, and the browser's own "Save as PDF". A page with no script cannot fail a render test for
a reason the server never sees (F-289, F-293).

READ-ONLY. Every route here is a SELECT. This module writes nothing, anywhere, ever.
"""
import calendar
import datetime as dt
import json

from flask import Blueprint, request

bp = Blueprint("clinic_day", __name__)
_db = None
_require = None
_unit = "clinic"
TABLE = "clinic_day_revenue"

# The tender buckets we know how to name, in the order they are shown. Anything else the
# ingester found is appended under its own name rather than folded into one of these.
KNOWN = [("Cash", "cash"), ("Online Payment", "online"), ("Debit Card", "card"),
         ("Credit Card", "card"), ("Net Banking", "online"), ("Patient APP", "online"),
         ("Wallet", "online"), ("Split Payment", "split")]


def init(app, db_getter, require_fn, unit="clinic", url_prefix=""):
    """Mount at IMPORT time, like every other module in this app: gunicorn imports
    finance_app:app and never reaches __main__."""
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


def _rupees(p):
    if p is None:
        return "—"
    return "{:,}".format(int(round(p / 100.0)))


def _table_exists(con):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (TABLE,)).fetchone() is not None


def _rows(con, first, last):
    return list(con.execute(
        "SELECT * FROM %s WHERE business_date BETWEEN ? AND ? ORDER BY business_date DESC"
        % TABLE, (first, last)))


def _tender(row):
    """{'cash':p,'online':p,'card':p,'split':p,'other':[(label,p)]} from the stored json."""
    out = {"cash": 0, "online": 0, "card": 0, "split": 0, "other": []}
    try:
        raw = json.loads(row["tender_json"] or "{}")
    except (ValueError, TypeError):
        return out
    known = {k: v for k, v in KNOWN}
    for label, p in sorted(raw.items()):
        b = known.get(label.strip())
        if b:
            out[b] += int(p)
        else:
            out["other"].append((label, int(p)))
    return out


@bp.route("/finance/clinic/day")
def clinic_day_page():
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Clinic — Day Revenue", """
          <div class="card"><h2>Not permitted</h2>
          <p>This screen shows the clinic's daily takings. Your login is not on the clinic
          desk, so it is not open to you. If that is wrong, ask Dr Manoj.</p></div>""")
    con = _db()
    if not _table_exists(con):
        return _shell("Clinic — Day Revenue", """
          <div class="card"><h2>Nothing read yet</h2>
          <p>The day-revenue reader has not run on this machine yet, so there is nothing to
          show. This page is not broken — it is empty, and it says so.</p></div>""")

    ym = (request.args.get("m") or "").strip()
    today = dt.date.today()
    try:
        y, m = int(ym[:4]), int(ym[5:7])
        dt.date(y, m, 1)
    except (ValueError, IndexError):
        y, m = today.year, today.month
    first = dt.date(y, m, 1)
    last = dt.date(y, m, calendar.monthrange(y, m)[1])
    rows = _rows(con, first.isoformat(), last.isoformat())

    latest = list(con.execute(
        "SELECT * FROM %s ORDER BY business_date DESC LIMIT 2" % TABLE))
    span = con.execute("SELECT MIN(business_date) a, MAX(business_date) b, COUNT(*) n FROM %s"
                       % TABLE).fetchone()

    prev = (first - dt.timedelta(days=1))
    nxt = (last + dt.timedelta(days=1))
    body = [_headline(latest),
            _month_table(rows, first, prev, nxt, y, m),
            _foot(span, u)]
    return _shell("Clinic — Day Revenue · %s %s" % (calendar.month_name[m], y), "".join(body))


def _headline(latest):
    if not latest:
        return '<div class="card"><h2>No days stored yet.</h2></div>'
    out = ['<div class="heads">']
    for i, r in enumerate(latest):
        t = _tender(r)
        out.append("""
          <div class="head %s">
            <div class="hd">%s</div>
            <div class="big">₹ %s</div>
            <div class="sub">%d bills · %s morning · %s evening</div>
            <table class="mini">
              <tr><td>Consultations</td><td class="n">%d</td><td class="r">₹ %s</td></tr>
              <tr><td>X-ray</td><td class="n">%d</td><td class="r">₹ %s</td></tr>
              <tr><td>Procedures</td><td class="n">%d</td><td class="r">₹ %s</td></tr>
            </table>
            <div class="tend">%s</div>
          </div>""" % (
            "today" if i == 0 else "prev", _human(r["business_date"]),
            _rupees(r["total_amount_p"]), r["total_count"],
            r["morning"] if r["morning"] is not None else "—",
            r["evening"] if r["evening"] is not None else "—",
            r["cons_count"], _rupees(r["cons_amount_p"]),
            r["xray_count"], _rupees(r["xray_amount_p"]),
            r["proc_count"], _rupees(r["proc_amount_p"]),
            _tender_line(t)))
    out.append("</div>")
    return "".join(out)


def _tender_line(t):
    bits = []
    for label, key in (("Cash", "cash"), ("Online", "online"), ("Card", "card")):
        if t[key]:
            bits.append("%s ₹%s" % (label, _rupees(t[key])))
    if t["split"]:
        bits.append('<span class="split" title="a split bill; the legs are in the bill itself">'
                    "Split ₹%s</span>" % _rupees(t["split"]))
    for label, p in t["other"]:
        bits.append("%s ₹%s" % (_esc(label), _rupees(p)))
    return " · ".join(bits) or "—"


def _month_table(rows, first, prev, nxt, y, m):
    head = """
      <div class="card">
        <div class="bar">
          <h2>%s %s</h2>
          <div class="nav noprint">
            <a href="?m=%04d-%02d">‹ previous</a>
            <a href="?m=%04d-%02d">next ›</a>
            <a class="btn" href="javascript:window.print()">Print / Save as PDF</a>
          </div>
        </div>""" % (calendar.month_name[m], y, prev.year, prev.month, nxt.year, nxt.month)
    if not rows:
        return head + "<p>No days stored for this month.</p></div>"
    tot = dict(n=0, total=0, cons=0, xray=0, proc=0, cash=0, online=0, card=0, split=0)
    body = []
    for r in rows:
        t = _tender(r)
        for k, v in (("n", r["total_count"]), ("total", r["total_amount_p"]),
                     ("cons", r["cons_amount_p"]), ("xray", r["xray_amount_p"]),
                     ("proc", r["proc_amount_p"]), ("cash", t["cash"]),
                     ("online", t["online"]), ("card", t["card"]), ("split", t["split"])):
            tot[k] += v or 0
        body.append(
            "<tr><td class='d'>%s</td><td class='n'>%d</td>"
            "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='r tot'>%s</td>"
            "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='n'>%s / %s</td></tr>" % (
                _human(r["business_date"]), r["total_count"],
                _rupees(r["cons_amount_p"]), _rupees(r["xray_amount_p"]),
                _rupees(r["proc_amount_p"]), _rupees(r["total_amount_p"]),
                _rupees(t["cash"]) if t["cash"] else "—",
                _rupees(t["online"]) if t["online"] else "—",
                _rupees(t["card"]) if t["card"] else "—",
                _rupees(t["split"]) if t["split"] else "—",
                r["morning"] if r["morning"] is not None else "—",
                r["evening"] if r["evening"] is not None else "—"))
    return head + """
        <table class="grid">
          <thead><tr>
            <th>Day</th><th class="n">Bills</th>
            <th class="r">Consult</th><th class="r">X-ray</th><th class="r">Proc</th>
            <th class="r">Total</th>
            <th class="r">Cash</th><th class="r">Online</th><th class="r">Card</th>
            <th class="r">Split</th><th class="n">M / E</th>
          </tr></thead>
          <tbody>%s</tbody>
          <tfoot><tr><td>%d days</td><td class="n">%d</td>
            <td class="r">%s</td><td class="r">%s</td><td class="r">%s</td>
            <td class="r tot">%s</td>
            <td class="r">%s</td><td class="r">%s</td><td class="r">%s</td><td class="r">%s</td>
            <td></td></tr></tfoot>
        </table>
      </div>""" % (
        "".join(body), len(rows), tot["n"],
        _rupees(tot["cons"]), _rupees(tot["xray"]), _rupees(tot["proc"]),
        _rupees(tot["total"]), _rupees(tot["cash"]), _rupees(tot["online"]),
        _rupees(tot["card"]), _rupees(tot["split"]))


def _foot(span, u):
    return """
      <p class="foot">Every figure on this page is computed from the itemised lines of the day's
      own Docterz sheet, never from its summary block — Dr Manoj's ruling of 04-Sep-2026.
      A <b>Split</b> figure is a bill paid by more than one method; the breakdown is on the bill.
      <br>%s days stored, %s to %s. Signed in as <b>%s</b>.</p>""" % (
        span["n"] if span else 0, _human(span["a"]) if span and span["a"] else "—",
        _human(span["b"]) if span and span["b"] else "—", _esc(u.get("user", "")))


def _human(iso):
    try:
        return dt.date(int(iso[:4]), int(iso[5:7]), int(iso[8:10])).strftime("%d-%b-%Y")
    except (ValueError, TypeError, IndexError):
        return iso or "—"


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _shell(title, body):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title><style>
:root{--ink:#111;--mut:#666;--line:#dcdcdc;--accent:#1F4E79;--soft:#eef4fb;--good:#e8f3e8}
*{box-sizing:border-box}
body{margin:0;padding:16px;font:14px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;color:var(--ink);background:#fafafa}
h1{font-size:19px;margin:0 0 2px;color:var(--accent)}
h2{font-size:15px;margin:0}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px;margin:12px 0}
.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.nav a{margin-left:10px;color:var(--accent);text-decoration:none;font-size:13px}
.nav a.btn{border:1px solid var(--accent);border-radius:5px;padding:4px 10px}
.heads{display:flex;gap:12px;flex-wrap:wrap}
.head{flex:1 1 260px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px}
.head.today{border-color:var(--accent);background:var(--soft)}
.hd{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px}
.big{font-size:30px;font-weight:700;margin:2px 0 2px;color:var(--accent)}
.sub{font-size:12.5px;color:var(--mut);margin-bottom:8px}
.mini{width:100%%;border-collapse:collapse;font-size:13px}
.mini td{padding:2px 0;border-bottom:1px dotted var(--line)}
.tend{margin-top:8px;font-size:13px}
.split{background:#fff5e0;padding:1px 5px;border-radius:4px}
table.grid{width:100%%;border-collapse:collapse;font-size:13px}
.grid th,.grid td{border:1px solid var(--line);padding:5px 7px}
.grid th{background:var(--soft);font-weight:600;font-size:12.5px}
.grid tfoot td{background:var(--good);font-weight:700}
.r{text-align:right;white-space:nowrap}.n{text-align:center;white-space:nowrap}
.d{white-space:nowrap}.tot{font-weight:700}
.foot{color:var(--mut);font-size:12.5px;margin:10px 2px}
@media print{body{background:#fff;padding:0;font-size:11.5px}
 .noprint{display:none!important}.card,.head{border-color:#999;break-inside:avoid}
 .grid th{background:#eee!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style></head><body>
<h1>Advanced Orthopaedic Surgery Centre — Day Revenue</h1>
%s
</body></html>""" % (_esc(title), body)
