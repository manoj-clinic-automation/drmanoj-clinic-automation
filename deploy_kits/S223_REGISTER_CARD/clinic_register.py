#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clinic_register.py -- S223: the counter's physical register, entered on the box.

THE OWNER, 04-Sep-2026: "wont add in tracker folder for data discipline reasons, and add a card
column, solves the issue, put the sheet on vps as a day entry card, easy to fill, less errors,
automatic matching by your setup"

WHY THIS EXISTS, AND WHY IT IS WORTH A SCREEN

Until now the clinic has had TWO records of a day's money: what Docterz says, and what the bank
settled. When they disagree there is no way to adjudicate -- you can only guess, and the guessing
has gone both ways: sometimes the POS is believed, sometimes the physical entry is accepted with
nobody checking the MPR.

The register is a THIRD, INDEPENDENT record, and three is categorically better than two:

    register agrees with bank, Docterz differs  ->  the entry was mis-keyed
    register agrees with Docterz, bank differs  ->  look at the feed, not at the counter
    all three differ                            ->  that day needs a person, not a formula

Two-way checks produce arguments. Three-way checks produce answers.

WHAT IS ENTERED. Nine numbers: consultation / x-ray / procedures, each as cash, UPI and CARD.
Nothing else -- no names, no bills, no patients. It is the register's own daily totals and it
takes under a minute.

WHY CARD IS HERE. The owner added it, and it closes a hole: the ICICI feed carries no card at all
(measured -- all 1,115 ingested transactions read UPI), so card money is invisible to the bank
side. Without a card column the counter would have had to bury it inside UPI, and the comparison
would have inherited that error and blamed the counter for it.

WHO MAY WRITE. `require("maker", "checker", unit="clinic")` -- the clinic desk, the same people
who already do the day entry. Every save is audited: who, when, and what changed.

THIS SCREEN NEVER JUDGES. It shows the three records side by side and says which two agree. It
does not decide who is right, and it never says anyone is short.
"""
import datetime as dt
import json

from flask import Blueprint, redirect, request

bp = Blueprint("clinic_register", __name__)
_db = None
_require = None
_audit = None
_unit = "clinic"

SECTIONS = (("cons", "Consultation"), ("xray", "X-ray"), ("proc", "Procedures"))
TENDERS = (("cash", "Cash"), ("upi", "UPI"), ("card", "Card"))
FIELDS = ["%s_%s_p" % (s, t) for s, _ in SECTIONS for t, _ in TENDERS]

SCHEMA = """
CREATE TABLE IF NOT EXISTS clinic_register_day (
  business_date TEXT PRIMARY KEY,
  cons_cash_p INTEGER NOT NULL DEFAULT 0, cons_upi_p INTEGER NOT NULL DEFAULT 0,
  cons_card_p INTEGER NOT NULL DEFAULT 0,
  xray_cash_p INTEGER NOT NULL DEFAULT 0, xray_upi_p INTEGER NOT NULL DEFAULT 0,
  xray_card_p INTEGER NOT NULL DEFAULT 0,
  proc_cash_p INTEGER NOT NULL DEFAULT 0, proc_upi_p INTEGER NOT NULL DEFAULT 0,
  proc_card_p INTEGER NOT NULL DEFAULT 0,
  note TEXT NOT NULL DEFAULT '', entered_by TEXT NOT NULL DEFAULT '',
  entered_at TEXT NOT NULL DEFAULT '', updated_by TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT ''
);
"""


_schema_done = False


def _ensure(con):
    """Create the table on FIRST USE, inside a request -- never at import.

    THIS COST AN OUTAGE. The first version of init() called db_getter() to create the table while
    the module was being imported. finance_app's db() lives on flask.g, which only exists inside an
    application context, so it raised at import, the import failed, and gunicorn went down with it:
    the whole finance app 503'd, not just this screen.

    stock_app has done it correctly since S213 -- `ensure_schema(con)` at the top of each route,
    never in init(). Its init() was read for the MOUNT signature and not for this, which is reading
    half a pattern and assuming the other half.
    """
    global _schema_done
    if _schema_done:
        return
    con.executescript(SCHEMA)
    con.commit()
    _schema_done = True


def init(app, db_getter, require_fn, audit_fn=None, unit="clinic", url_prefix=""):
    """Mount only. It touches no database and opens no connection: at import time there is no
    application context to open one in."""
    global _db, _require, _audit, _unit
    _db, _require, _audit, _unit = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ---------------------------------------------------------------- helpers
def _r(p):
    return "—" if p is None else "{:,}".format(int(round(p / 100.0)))


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _iso_ok(d):
    try:
        dt.date(int(d[:4]), int(d[5:7]), int(d[8:10]))
        return True
    except (ValueError, IndexError, TypeError):
        return False


def _human(iso):
    return (dt.date(int(iso[:4]), int(iso[5:7]), int(iso[8:10])).strftime("%d-%b-%Y")
            if _iso_ok(iso) else iso)


def _paise(v):
    """A rupee figure typed by a human. Blank is zero. Anything not a number is REFUSED, never
    silently read as zero -- a typo must not become a quiet 0 in a money record."""
    s = str(v or "").replace(",", "").replace("₹", "").strip()
    if s == "":
        return 0, None
    try:
        f = float(s)
    except ValueError:
        return None, "%r is not a number" % s[:12]
    if f < 0:
        return None, "a negative amount (%s)" % s[:12]
    if f > 10_000_000:
        return None, "%s looks far too large" % s[:12]
    return int(round(f * 100)), None


def register_row(con, d):
    return con.execute("SELECT * FROM clinic_register_day WHERE business_date=?", (d,)).fetchone()


def docterz_day(con, d):
    """What Docterz says, split by tender, with split bills resolved into their legs."""
    out = {"cash": 0, "upi": 0, "card": 0, "other": 0, "known": False}
    try:
        split_ids, legs = set(), {"cash": 0, "upi": 0, "card": 0}
        for r in con.execute("SELECT clinic_id, tender, amount_p FROM clinic_day_tender "
                             "WHERE business_date=?", (d,)):
            split_ids.add(r["clinic_id"])
            t = r["tender"]
            k = ("cash" if t == "Cash" else
                 "card" if t in ("Debit Card", "Credit Card") else "upi")
            legs[k] += r["amount_p"]
        rows = list(con.execute("SELECT clinic_id, mode, amount_p FROM clinic_day_line "
                                "WHERE business_date=? AND section IN (?,?,?)",
                                (d, "consult", "xray", "proc")))
    except Exception:                                  # noqa: BLE001
        return out
    if not rows:
        return out
    out["known"] = True
    for k in ("cash", "upi", "card"):
        out[k] += legs[k]
    for r in rows:
        if r["clinic_id"] in split_ids:
            continue
        m, p = (r["mode"] or "").strip(), r["amount_p"] or 0
        if m == "Cash":
            out["cash"] += p
        elif m in ("Debit Card", "Credit Card"):
            out["card"] += p
        elif m in ("Online Payment", "Net Banking", "Patient APP", "Wallet"):
            out["upi"] += p
        else:
            out["other"] += p
    return out


def bank_upi(con, d):
    """(amount, known). known=False means the statement for that date has not arrived -- which is
    not the same as zero, and must never be shown as zero."""
    try:
        upto = con.execute("SELECT MAX(txn_date) m FROM upi_txn WHERE unit=?",
                           (_unit,)).fetchone()["m"]
        if not upto or d > upto:
            return None, False
        r = con.execute("SELECT COALESCE(SUM(amount_p),0) s FROM upi_txn "
                        "WHERE unit=? AND txn_date=?", (_unit, d)).fetchone()
        return r["s"], True
    except Exception:                                  # noqa: BLE001
        return None, False


def three_way(con, d):
    """The three records of one day, and which two agree. It states; it does not accuse."""
    reg = register_row(con, d)
    doc = docterz_day(con, d)
    bank, bank_known = bank_upi(con, d)
    r_cash = r_upi = r_card = None
    if reg is not None:
        r_cash = reg["cons_cash_p"] + reg["xray_cash_p"] + reg["proc_cash_p"]
        r_upi = reg["cons_upi_p"] + reg["xray_upi_p"] + reg["proc_upi_p"]
        r_card = reg["cons_card_p"] + reg["xray_card_p"] + reg["proc_card_p"]
    verdict, why = "", ""
    if reg is None:
        verdict, why = "not entered", "the register has not been filled in for this day"
    elif not doc["known"]:
        verdict, why = "no docterz", "no Docterz day has been read for this date"
    elif not bank_known:
        verdict = "waiting_bank"
        why = ("the bank statement for this date has not arrived. Register and Docterz %s on UPI."
               % ("agree" if r_upi == doc["upi"] else "do NOT agree"))
    else:
        rd, rb, db_ = r_upi == doc["upi"], r_upi == bank, doc["upi"] == bank
        if rd and rb:
            verdict, why = "all agree", "all three records agree on UPI"
        elif rd:
            verdict, why = "bank differs", ("the register and Docterz agree; the BANK differs. "
                                            "Look at the feed, not at the counter.")
        elif rb:
            verdict, why = "docterz differs", ("the register and the bank agree; DOCTERZ differs. "
                                               "The entry was most likely mis-keyed.")
        elif db_:
            verdict, why = "register differs", ("Docterz and the bank agree; the REGISTER differs. "
                                                "Most likely the register total was written wrong.")
        else:
            verdict, why = "all differ", "all three differ — this day needs a person, not a formula"
    return dict(reg=reg, doc=doc, bank=bank, bank_known=bank_known,
                r_cash=r_cash, r_upi=r_upi, r_card=r_card, verdict=verdict, why=why)


# ---------------------------------------------------------------- pages
@bp.route("/finance/clinic/register")
def register_index():
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Register", _denied())
    con = _db()
    _ensure(con)
    days = [r[0] for r in con.execute(
        "SELECT business_date FROM clinic_day_revenue ORDER BY business_date DESC LIMIT 45")]
    if not days:
        today = dt.date.today()
        days = [(today - dt.timedelta(days=i)).isoformat() for i in range(30)]
    body = ["""<div class="card"><h2>Daily register — which days are done</h2>
      <p class="mut">Tap a day to enter what the physical register says. Nine numbers, under a
      minute. Nothing here asks for a patient or a bill.</p>
      <table class="grid"><thead><tr><th>Day</th><th class="r">Register</th>
      <th class="r">Docterz</th><th class="r">Bank UPI</th><th>Status</th><th></th></tr></thead>
      <tbody>"""]
    for d in days:
        t = three_way(con, d)
        reg_tot = None if t["reg"] is None else (t["r_cash"] + t["r_upi"] + t["r_card"])
        doc_tot = (t["doc"]["cash"] + t["doc"]["upi"] + t["doc"]["card"] + t["doc"]["other"]
                   if t["doc"]["known"] else None)
        body.append(
            "<tr class='%s'><td class='d'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
            "<td class='r'>%s</td><td><span class='pill %s'>%s</span></td>"
            "<td class='noprint'><a class='btn' href='/finance/clinic/register/%s'>%s</a></td></tr>"
            % ("done" if t["reg"] is not None else "todo", _human(d),
               _r(reg_tot) if reg_tot is not None else "—",
               _r(doc_tot) if doc_tot is not None else "—",
               _r(t["bank"]) if t["bank_known"] else "not arrived",
               t["verdict"].replace(" ", "_"), _esc(t["verdict"] or "—"), d,
               "edit" if t["reg"] is not None else "fill"))
    body.append("</tbody></table></div>")
    return _shell("Daily register", "".join(body))


@bp.route("/finance/clinic/register/<date>", methods=["GET", "POST"])
def register_card(date):
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Register", _denied())
    if not _iso_ok(date):
        return _shell("Register", '<div class="card"><h2>Not a date.</h2></div>')
    con = _db()
    _ensure(con)
    msg = ""
    if request.method == "POST":
        vals, bad = {}, []
        for f in FIELDS:
            p, e = _paise(request.form.get(f))
            if e:
                bad.append("%s: %s" % (f.replace("_p", "").replace("_", " "), e))
            else:
                vals[f] = p
        if bad:
            # NOTHING is written when any field is wrong. A part-saved money row is worse than
            # an unsaved one, because it looks finished.
            msg = ("<div class='bad'>Nothing was saved. Fix these and submit again:<br>%s</div>"
                   % "<br>".join(_esc(b) for b in bad))
        else:
            now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            before = register_row(con, date)
            note = (request.form.get("note") or "").strip()[:300]
            if before is None:
                con.execute("INSERT INTO clinic_register_day (business_date, %s, note, "
                            "entered_by, entered_at, updated_by, updated_at) VALUES (?,%s,?,?,?,?,?)"
                            % (",".join(FIELDS), ",".join("?" * len(FIELDS))),
                            [date] + [vals[f] for f in FIELDS] + [note, u.get("user", ""), now,
                                                                  u.get("user", ""), now])
            else:
                con.execute("UPDATE clinic_register_day SET %s, note=?, updated_by=?, updated_at=? "
                            "WHERE business_date=?"
                            % ",".join("%s=?" % f for f in FIELDS),
                            [vals[f] for f in FIELDS] + [note, u.get("user", ""), now, date])
            con.commit()
            if _audit:
                try:
                    _audit(con, "clinic_register_day", date,
                           "update" if before is not None else "insert",
                           before=({k: before[k] for k in FIELDS} if before is not None else None),
                           after=vals, who=u.get("user", ""))
                    con.commit()
                except Exception:                       # noqa: BLE001
                    pass
            msg = "<div class='ok'>Saved. %s</div>" % _esc(three_way(con, date)["why"])
    return _shell("Register — %s" % _human(date), _card_html(con, date, u, msg))


def _card_html(con, date, u, msg):
    reg = register_row(con, date)
    t = three_way(con, date)
    rows = []
    for s, slabel in SECTIONS:
        cells = []
        for tn, tlabel in TENDERS:
            f = "%s_%s_p" % (s, tn)
            v = "" if reg is None else ("" if not reg[f] else "%d" % int(round(reg[f] / 100.0)))
            cells.append("<td><input name='%s' value='%s' inputmode='numeric' "
                         "autocomplete='off' class='amt'></td>" % (f, _esc(v)))
        rows.append("<tr><th class='sec'>%s</th>%s</tr>" % (slabel, "".join(cells)))
    who = ""
    if reg is not None:
        who = ("<p class='mut'>last saved by <b>%s</b> at %s%s</p>"
               % (_esc(reg["updated_by"] or reg["entered_by"]),
                  _esc(reg["updated_at"] or reg["entered_at"]),
                  (" · first entered by %s" % _esc(reg["entered_by"]))
                  if reg["entered_by"] and reg["entered_by"] != reg["updated_by"] else ""))
    form = """
      <div class="card"><h2>%s — what the register says</h2>
        %s
        <form method="post">
        <table class="grid entry"><thead><tr><th></th><th>Cash</th><th>UPI</th><th>Card</th>
          </tr></thead><tbody>%s</tbody></table>
        <p class="mut">Leave a box empty for nothing. Put 0 only if you mean a real zero.</p>
        <p><label class="mut">Note (optional)</label><br>
           <input name="note" class="note" value="%s" maxlength="300"></p>
        <button type="submit" class="save">Save the day</button>
        <a class="btn" href="/finance/clinic/register">back to the list</a>
        </form>%s
      </div>""" % (_human(date), msg,
                   "".join(rows), _esc("" if reg is None else (reg["note"] or "")), who)
    return form + _compare_html(t, date)


def _compare_html(t, date):
    doc, bank = t["doc"], t["bank"]
    def line(label, reg_v, doc_v, bank_v, note=""):
        return ("<tr><th class='sec'>%s</th><td class='r'>%s</td><td class='r'>%s</td>"
                "<td class='r'>%s</td><td class='mut'>%s</td></tr>"
                % (label, _r(reg_v) if reg_v is not None else "—",
                   _r(doc_v) if doc_v is not None else "—",
                   _r(bank_v) if bank_v is not None else "—", note))
    body = [line("Cash", t["r_cash"], doc["cash"] if doc["known"] else None, None,
                 "no bank feed exists for cash"),
            line("UPI", t["r_upi"], doc["upi"] if doc["known"] else None,
                 bank if t["bank_known"] else None,
                 "" if t["bank_known"] else "statement not arrived"),
            line("Card", t["r_card"], doc["card"] if doc["known"] else None, None,
                 "the bank feed carries no card at all")]
    return """
      <div class="card"><h2>The three records, side by side</h2>
        <table class="grid"><thead><tr><th></th><th class="r">Register</th>
          <th class="r">Docterz</th><th class="r">Bank</th><th></th></tr></thead>
          <tbody>%s</tbody></table>
        <p class="verdict %s">%s</p>
        <p class="mut">This screen states what the three records say. It does not decide who is
        right, and it never accuses anyone. Where two agree and one differs, that is the one to
        look at first.</p>
        <p class="noprint"><a class="btn" href="/finance/clinic/day/%s">the day's entries</a></p>
      </div>""" % ("".join(body), t["verdict"].replace(" ", "_"),
                   _esc(t["why"]), date)


def _denied():
    return """<div class="card"><h2>Not permitted</h2><p>The daily register belongs to the clinic
      desk. Your login is not on it. If that is wrong, ask Dr Manoj.</p></div>"""


def _shell(title, body):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title><style>
:root{--ink:#111;--mut:#666;--line:#dcdcdc;--accent:#1F4E79;--soft:#eef4fb}
*{box-sizing:border-box}
body{margin:0;padding:14px;font:15px/1.55 "Segoe UI",system-ui,-apple-system,sans-serif;
 color:var(--ink);background:#fafafa}
h1{font-size:18px;margin:0 0 8px;color:var(--accent)}h2{font-size:15px;margin:0 0 8px}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px;margin:0 0 12px}
.mut{color:var(--mut);font-size:13px}
table.grid{width:100%%;border-collapse:collapse;font-size:14px}
.grid th,.grid td{border:1px solid var(--line);padding:7px 8px}
.grid thead th{background:var(--soft);font-size:13px}
.r{text-align:right;white-space:nowrap}.d{white-space:nowrap}
.sec{text-align:left;background:#fafafa;width:34%%}
.entry input.amt{width:100%%;font:16px "Segoe UI",system-ui,sans-serif;padding:9px 8px;
 border:1px solid #bbb;border-radius:6px;text-align:right}
.entry input.amt:focus{border-color:var(--accent);outline:2px solid #cfe0f2}
.note{width:100%%;padding:8px;border:1px solid #bbb;border-radius:6px;font:14px inherit}
button.save{background:var(--accent);color:#fff;border:0;border-radius:6px;padding:11px 20px;
 font-size:15px;cursor:pointer;margin-right:10px}
a.btn{display:inline-block;border:1px solid var(--accent);color:var(--accent);border-radius:6px;
 padding:5px 12px;text-decoration:none;font-size:13px}
.ok{background:#e8f3e8;border-left:4px solid #2e7d32;padding:9px 12px;margin-bottom:10px}
.bad{background:#fdecea;border-left:4px solid #c62828;padding:9px 12px;margin-bottom:10px}
.pill{font-size:12px;padding:2px 8px;border-radius:10px;background:#eee;white-space:nowrap}
.pill.all_agree{background:#e8f3e8}.pill.not_entered{background:#f4f4f4;color:#777}
.pill.docterz_differs,.pill.register_differs,.pill.all_differ{background:#fdecea}
.pill.bank_differs,.pill.waiting_bank{background:#fff5e0}
.verdict{font-weight:600;margin:10px 0 4px}
tr.todo .d{font-weight:700}
@media print{@page{size:A4 portrait;margin:12mm}.noprint{display:none!important}
 body{background:#fff;padding:0}.card{border:none;padding:0}}
</style></head><body><h1>Dr. Manoj Agarwal Clinic — daily register</h1>
%s</body></html>""" % (_esc(title), body)
