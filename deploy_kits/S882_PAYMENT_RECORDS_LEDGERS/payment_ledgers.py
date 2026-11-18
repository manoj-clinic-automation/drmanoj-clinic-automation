# -*- coding: utf-8 -*-
"""payment_ledgers.py -- S882 (the parent, S486, 18-Nov-2026). Two running ledgers on his login, from his own papers.

  /finance/ledgers                 the two ledgers and the receipts on the box (counts)
  /finance/ledgers/agilus          NK Pathology's Agilus ledger: every Agilus invoice in order, its amount and the
                                   running total (deposits are made from the bank -- the accountants match them)
  /finance/ledgers/myoperator      MyOperator: invoices raised, payments made, and each monthly statement's usage and
                                   MyOperator's own pre-paid balance
  /finance/ledgers/file/<id>       one paper, opened in place (PDF)
His login alone (the Patients page's gate). Mounted by owner_console.init beside the Patients page; touches no
database at mount (F-303). Server-rendered, no dialogs (F-1464). No patient data, no secret, no number here (F-185).
"""
import html
import re
import os
import sys

VERSION = "S882-LEDGERS-1.1"
FIN = os.environ.get("FIN_DIR", os.path.dirname(os.path.abspath(__file__)))

DENIED = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
          "<title>Ledgers</title><body style='font-family:system-ui;margin:40px 20px;color:#1d211f'>"
          "<h2>This page is the owner's.</h2><p>Your login does not open it.</p><p><a href='/portal'>Back to the Clinic app</a></p>")

CSS = ("body{font-family:system-ui,Segoe UI,Arial;margin:0;color:#1d211f;background:#f6f7f5}"
       "header{background:#24443a;color:#fff;padding:14px 18px}header a{color:#cfe7dc}"
       "main{padding:14px 18px;max-width:1100px}h1{font-size:20px;margin:0}h2{font-size:17px;margin:22px 0 8px}"
       "table{border-collapse:collapse;width:100%;background:#fff;font-size:14px}"
       "th,td{border-bottom:1px solid #e3e6e1;padding:7px 8px;text-align:left;vertical-align:top}"
       "th{background:#eef1ec;position:sticky;top:0}td.n,th.n{text-align:right;white-space:nowrap}"
       ".note{color:#4d5651;font-size:13px;margin:6px 0 12px}.card{background:#fff;border:1px solid #e3e6e1;"
       "border-radius:8px;padding:12px 14px;margin:10px 0}.muted{color:#7a837e}a.btn{display:inline-block;"
       "padding:6px 10px;border:1px solid #24443a;border-radius:6px;text-decoration:none;color:#24443a;margin:4px 6px 0 0}")


def _pr():
    if FIN not in sys.path:
        sys.path.insert(0, FIN)
    import payment_records                                             # noqa: PLC0415 -- beside this file
    return payment_records


def rs(paise):
    if paise is None:
        return ""
    neg = paise < 0
    r = abs(int(paise))
    whole, frac = divmod(r, 100)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "Rs " + s + ("" if frac == 0 else ".%02d" % frac)


def dmy(iso):
    if not iso or len(iso) < 10:
        return iso or ""
    m = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[int(iso[5:7]) - 1]
    return "%s-%s-%s" % (iso[8:10], m, iso[:4])


def page(title, body):
    e = html.escape
    return ("<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>%s</style></head><body><header><h1>%s</h1>"
            "<div style='font-size:13px;margin-top:4px'><a href='/finance/ledgers'>Ledgers</a> &middot; "
            "<a href='/portal'>Clinic app</a></div></header><main>%s</main></body></html>") % (e(title), CSS, e(title), body)


def flink(fid, label="open"):
    return "<a href='/finance/ledgers/file/%d' target='_self'>%s</a>" % (int(fid), html.escape(label))


def index_html(con):
    pr = _pr()
    e = html.escape
    st = pr.state_read()
    files = pr.files_for(con)
    by = {}
    for f in files:
        by[f["vendor"]] = by.get(f["vendor"], 0) + 1
    ok = st.get("ok")
    last = st.get("run_at") or "not yet run"
    head = ("<div class=card><b>Receipts on the server:</b> %d papers from your Payment Records folder "
            "(copied each night at 02:20; last copy %s%s).</div>") % (
        len(files), e(last), "" if ok or not st else " &mdash; <b>did not finish:</b> " + e(st.get("error", "")))
    rows = "".join("<tr><td>%s</td><td class=n>%d</td></tr>" % (e(v), c) for v, c in sorted(by.items()))
    left = "".join("<li>%d &mdash; %s</li>" % (c, e(w)) for w, c in sorted((st.get("skipped") or {}).items()))
    return page("Ledgers", head +
                "<a class=btn href='/finance/ledgers/agilus'>Agilus ledger (NK Pathology)</a>"
                "<a class=btn href='/finance/ledgers/myoperator'>MyOperator ledger</a>"
                "<h2>Papers by sender</h2><table><tr><th>Sender (Payment Records folder)</th><th class=n>Papers</th></tr>%s</table>"
                "<p class=note>Only payment papers are copied: receipts and invoices (Agilus's invoices, MyOperator's "
                "statements). Reports, exports, pictures, bills, policy papers and personal orders stay in Drive.</p>"
                "%s" % (rows or "<tr><td colspan=2 class=muted>none yet</td></tr>",
                        ("<h2>Left in Drive at the last copy</h2><ul class=note>%s</ul>" % left) if left else ""))


def agilus_html(con):
    pr = _pr()
    rows = pr.agilus_rows(con)
    e = html.escape
    tr = []
    for r in reversed(rows):
        tr.append("<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=muted>%s</td><td class=n>%s</td></tr>" % (
            dmy(r["date"]), flink(r["file"], "Invoice"), rs(r["amount"]) or "<span class=muted>see the invoice</span>",
            e(r["source"]), rs(r["running"])))
    unread = sum(1 for r in rows if r["amount"] is None)
    head = ("<p class=note>Every Agilus invoice that came by mail, newest first, with the running total of what Agilus "
            "has charged NK Pathology. Deposits to Agilus are made from the bank; the accountants match them for now. "
            "The patient lines of each invoice (name, test, date, amount) come in the next update.</p>"
            "<div class=card><b>%d invoices</b>, %s in all%s.</div>") % (
        len(rows), rs(rows[-1]["running"]) if rows else "Rs 0",
        (" &mdash; %d without a figure (open the invoice)" % unread) if unread else "")
    return page("Agilus ledger — NK Pathology", head +
                "<table><tr><th>Date</th><th>Paper</th><th class=n>Amount</th><th>Figure from</th>"
                "<th class=n>Running total</th></tr>%s</table>" % ("".join(tr) or "<tr><td colspan=5 class=muted>no invoice on the server yet</td></tr>"))


def myoperator_html(con):
    pr = _pr()
    rows = pr.myoperator_rows(con)
    tr = []
    for r in reversed(rows):
        links = " ".join(flink(f, "paper") for f in r["files"]) or "<span class=muted>no PDF</span>"
        tr.append("<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
                  "<td class=n>%s</td><td>%s</td></tr>" % (
                      dmy(r["date"]), html.escape(r["what"]), rs(r.get("charged")) or rs(r.get("usage")),
                      rs(r.get("paid")), rs(r["running"]), rs(r.get("balance")), links))
    head = ("<p class=note>MyOperator charges in two ways: a plan invoice you pay at once, and a pre-paid balance its "
            "calls and messages are drawn from each month. Invoices and payments come from the mails; each monthly "
            "statement gives the month's usage (without tax) and MyOperator's own pre-paid balance after it. "
            "\"Paid less charged\" is the running difference of payments and invoices only.</p>")
    return page("MyOperator ledger", head +
                "<table><tr><th>Date</th><th>What</th><th class=n>Charged / usage</th><th class=n>Paid</th>"
                "<th class=n>Paid less charged</th><th class=n>Pre-paid balance (MyOperator)</th><th>Paper</th></tr>%s</table>"
                % ("".join(tr) or "<tr><td colspan=7 class=muted>nothing yet</td></tr>"))


def init(app, db_getter, require_fn, unit="packs"):
    """Mount only; touches no database (F-303). Called by owner_console.init."""
    from flask import Blueprint, Response, send_file                  # noqa: PLC0415
    bp = Blueprint("payment_ledgers", __name__)

    def _gate():
        return require_fn("checker", unit=unit)

    def _html(fn):
        _u, err = _gate()
        if err:
            return Response(DENIED, status=403, mimetype="text/html")
        try:
            body = fn(db_getter())
        except Exception as ex:                                        # noqa: BLE001 -- one line, never a trace
            body = page("Ledgers", "<div class=card>This page could not be built (%s). Tell Claude.</div>"
                        % html.escape(type(ex).__name__))
        r = Response(body, mimetype="text/html")
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/ledgers")
    def ledgers_index():
        return _html(index_html)

    @bp.route("/finance/ledgers/agilus")
    def ledgers_agilus():
        return _html(agilus_html)

    @bp.route("/finance/ledgers/myoperator")
    def ledgers_myoperator():
        return _html(myoperator_html)

    @bp.route("/finance/ledgers/file/<int:fid>")
    def ledgers_file(fid):
        _u, err = _gate()
        if err:
            return Response(DENIED, status=403, mimetype="text/html")
        pr = _pr()
        con = db_getter()
        row = con.execute("SELECT local_path, name FROM payment_record_file WHERE id=?", (fid,)).fetchone() \
            if pr.table_ready(con) else None
        store = os.path.realpath(pr.STORE)
        if not row or not os.path.realpath(row["local_path"]).startswith(store + os.sep) or not os.path.isfile(row["local_path"]):
            return Response("That paper is not on the server.", status=404, mimetype="text/plain")
        r = send_file(row["local_path"], mimetype="application/pdf", as_attachment=False,
                      download_name=re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(row["name"]) or "paper.pdf")[:80])
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/ledgers/agilus/layout")
    def ledgers_agilus_layout():                                       # the masked layout: shape only, rare words X'd (D656)
        _u, err = _gate()
        if err:
            return Response(DENIED, status=403, mimetype="text/html")
        con = db_getter()
        txt = _pr().masked_layout(con) if _pr().table_ready(con) else "no paper on the server yet"
        r = Response(txt, mimetype="text/plain; charset=utf-8")
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/ledgers/healthz")
    def ledgers_healthz():
        return {"ok": True, "version": VERSION}

    app.register_blueprint(bp)
