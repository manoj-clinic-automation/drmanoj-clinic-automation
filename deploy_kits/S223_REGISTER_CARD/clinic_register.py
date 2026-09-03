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

SECTIONS = (("cons", "Consultation"), ("xray", "X-ray"), ("proc", "Procedures"),
            ("dress", "Dressing"))
TENDERS = (("cash", "Cash"), ("upi", "UPI"), ("card", "Card"))
FIELDS = ["%s_%s_p" % (s, t) for s, _ in SECTIONS for t, _ in TENDERS]

# Physiotherapy is kept at reception, is NOT a Docterz billing head, and -- the owner confirmed on
# 04-Sep -- takes its UPI on a SEPARATE CHANNEL. So it settles on its own rail and never reaches
# the clinic merchant feed. It lives in its own table, is shown on its own line, and is kept OUT
# of the bank arithmetic entirely: folding it in would invent a difference on every day physio
# took a payment. It is a fifth money channel, and like card it cannot be reconciled here.
PHYSIO_FIELDS = ["physio_cash_p", "physio_upi_p"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS clinic_register_day (
  business_date TEXT PRIMARY KEY,
  cons_cash_p INTEGER NOT NULL DEFAULT 0, cons_upi_p INTEGER NOT NULL DEFAULT 0,
  cons_card_p INTEGER NOT NULL DEFAULT 0,
  xray_cash_p INTEGER NOT NULL DEFAULT 0, xray_upi_p INTEGER NOT NULL DEFAULT 0,
  xray_card_p INTEGER NOT NULL DEFAULT 0,
  proc_cash_p INTEGER NOT NULL DEFAULT 0, proc_upi_p INTEGER NOT NULL DEFAULT 0,
  proc_card_p INTEGER NOT NULL DEFAULT 0,
  dress_cash_p INTEGER NOT NULL DEFAULT 0, dress_upi_p INTEGER NOT NULL DEFAULT 0,
  dress_card_p INTEGER NOT NULL DEFAULT 0,
  note TEXT NOT NULL DEFAULT '', entered_by TEXT NOT NULL DEFAULT '',
  entered_at TEXT NOT NULL DEFAULT '', updated_by TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS clinic_physio_day (
  business_date TEXT PRIMARY KEY,
  cash_p INTEGER NOT NULL DEFAULT 0,
  upi_p  INTEGER NOT NULL DEFAULT 0,
  note TEXT NOT NULL DEFAULT '', entered_by TEXT NOT NULL DEFAULT '',
  entered_at TEXT NOT NULL DEFAULT '', updated_by TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT ''
);
"""

# The dressing columns arrived after the table did, so an existing box needs them added.
MIGRATE = ["ALTER TABLE clinic_register_day ADD COLUMN dress_cash_p INTEGER NOT NULL DEFAULT 0",
           "ALTER TABLE clinic_register_day ADD COLUMN dress_upi_p INTEGER NOT NULL DEFAULT 0",
           "ALTER TABLE clinic_register_day ADD COLUMN dress_card_p INTEGER NOT NULL DEFAULT 0"]


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
    for stmt in MIGRATE:
        try:
            con.execute(stmt)
        except Exception:                        # noqa: BLE001
            pass                                 # the column is already there; that is the norm
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


def physio_row(con, d):
    try:
        return con.execute("SELECT * FROM clinic_physio_day WHERE business_date=?", (d,)).fetchone()
    except Exception:                            # noqa: BLE001
        return None


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
    phy = physio_row(con, d)
    bank, bank_known = bank_upi(con, d)
    r_cash = r_upi = r_card = None
    if reg is not None:
        # DRESSING clubs into PROCEDURES -- the owner's ruling. It is entered and stored on its
        # own line so the counter's register is reproduced exactly, and added here because that
        # is the head Docterz bills it under.
        r_cash = sum(reg["%s_cash_p" % s] for s, _ in SECTIONS)
        r_upi = sum(reg["%s_upi_p" % s] for s, _ in SECTIONS)
        r_card = sum(reg["%s_card_p" % s] for s, _ in SECTIONS)
    p_cash = phy["cash_p"] if phy is not None else None
    p_upi = phy["upi_p"] if phy is not None else None
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
        # PHYSIO IS NOT IN THIS COMPARISON. The owner, 04-Sep: "physio seperate upi channel used."
        # It settles on its own rail, so it never reaches the clinic merchant feed -- adding it to
        # our side would manufacture a difference on every day physio took a UPI payment. It is
        # recorded, shown on its own line, and left out of the arithmetic.
        rd = r_upi == doc["upi"]
        rb = r_upi == bank
        db_ = doc["upi"] == bank
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
    return dict(reg=reg, doc=doc, phy=phy, bank=bank, bank_known=bank_known,
                r_cash=r_cash, r_upi=r_upi, r_card=r_card,
                p_cash=p_cash, p_upi=p_upi, verdict=verdict, why=why)


# ---------------------------------------------------------------- pages
@bp.route("/finance/clinic/register")
def register_index():
    """MINIMUM TAPS: this does not show a list first. It opens the most recent day that has not
    been filled in, because that is what the person opening it came to do. The list is underneath."""
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Register", _denied())
    con = _db()
    _ensure(con)
    days = [r[0] for r in con.execute(
        "SELECT business_date FROM clinic_day_revenue ORDER BY business_date DESC LIMIT 45")]
    if not days:
        today = dt.date.today()
        days = [(today - dt.timedelta(days=i)).isoformat() for i in range(21)]
    done = {r[0] for r in con.execute("SELECT business_date FROM clinic_register_day")}
    todo = [d for d in days if d not in done]
    if todo:
        return redirect("/finance/clinic/register/%s" % todo[0])
    return _shell("Daily register", _list_html(con, days, only_todo=True))


@bp.route("/finance/clinic/register/list")
def register_list():
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Register", _denied())
    con = _db()
    _ensure(con)
    days = [r[0] for r in con.execute(
        "SELECT business_date FROM clinic_day_revenue ORDER BY business_date DESC LIMIT 45")]
    return _shell("Daily register", _list_html(con, days, only_todo=False))


def _list_html(con, days, only_todo=True):
    """A DONE DAY DISAPPEARS. The owner's instruction: the list is a to-do, not an archive, so a
    day that has been filled leaves it. `all days` brings the finished ones back when someone
    needs to correct one."""
    done = {r[0] for r in con.execute("SELECT business_date FROM clinic_register_day")}
    if only_todo:
        days = [d for d in days if d not in done]
        if not days:
            return """<div class="card"><h2>Nothing left to fill</h2>
              <p>Every day the clinic has a record for has been entered. Well done.</p>
              <p class="navrow"><a class="btn" href="/finance/clinic/register/list">see all days</a>
              </p></div>"""
    body = ['<div class="card"><h2>%s</h2>' % ("Days still to fill" if only_todo else "Every day"),
            """<table class="grid"><thead><tr><th>Day</th><th class="r">Register</th>
      <th>Status</th><th></th></tr></thead><tbody>"""]
    for d in days:
        t = three_way(con, d)
        reg_tot = None if t["reg"] is None else (t["r_cash"] + t["r_upi"] + t["r_card"])
        body.append(
            "<tr><td class='d'>%s</td><td class='r'>%s</td>"
            "<td><span class='pill %s'>%s</span></td>"
            "<td class='noprint'><a class='btn' href='/finance/clinic/register/%s'>%s</a></td></tr>"
            % (_human(d), _r(reg_tot) if reg_tot is not None else "—",
               t["verdict"].replace(" ", "_"), _esc(t["verdict"] or "—"), d,
               "edit" if t["reg"] is not None else "FILL"))
    body.append("</tbody></table>")
    body.append('<p class="navrow noprint"><a class="btn" href="/finance/clinic/register/%s">%s</a>'
                '</p></div>' % ("list" if only_todo else "", "all days" if only_todo
                                else "back to what is left"))
    return "".join(body)


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
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        who = u.get("user", "")
        if request.form.get("clear") == "yes":
            # An empty day saved by accident is worse than an unfilled one: it looks answered.
            # One tap undoes it, and the removal is audited like any other change.
            before = register_row(con, date)
            con.execute("DELETE FROM clinic_register_day WHERE business_date=?", (date,))
            con.execute("DELETE FROM clinic_physio_day WHERE business_date=?", (date,))
            con.commit()
            if _audit and before is not None:
                try:
                    _audit(con, "clinic_register_day", date, "delete",
                           before={k: before[k] for k in FIELDS}, after=None, who=who)
                    con.commit()
                except Exception:                # noqa: BLE001
                    pass
            msg = ("<div class='ok'>Cleared. This day is back to not entered, and the removal is "
                   "in the audit log.</div>")
        else:
            vals, bad = {}, []
            for f in FIELDS + PHYSIO_FIELDS:
                p, e = _paise(request.form.get(f))
                if e:
                    bad.append("%s — %s" % (f.replace("_p", "").replace("_", " "), e))
                else:
                    vals[f] = p
            if bad:
                msg = ("<div class='bad'><b>Nothing was saved.</b><br>Fix these and press Save "
                       "again:<br>%s</div>" % "<br>".join(_esc(x) for x in bad))
            else:
                note = (request.form.get("note") or "").strip()[:300]
                before = register_row(con, date)
                if before is None:
                    con.execute("INSERT INTO clinic_register_day (business_date, %s, note, "
                                "entered_by, entered_at, updated_by, updated_at) "
                                "VALUES (?,%s,?,?,?,?,?)"
                                % (",".join(FIELDS), ",".join("?" * len(FIELDS))),
                                [date] + [vals[f] for f in FIELDS] + [note, who, now, who, now])
                else:
                    con.execute("UPDATE clinic_register_day SET %s, note=?, updated_by=?, "
                                "updated_at=? WHERE business_date=?"
                                % ",".join("%s=?" % f for f in FIELDS),
                                [vals[f] for f in FIELDS] + [note, who, now, date])
                pb = physio_row(con, date)
                if pb is None:
                    con.execute("INSERT INTO clinic_physio_day (business_date, cash_p, upi_p, "
                                "entered_by, entered_at, updated_by, updated_at) "
                                "VALUES (?,?,?,?,?,?,?)",
                                (date, vals["physio_cash_p"], vals["physio_upi_p"],
                                 who, now, who, now))
                else:
                    con.execute("UPDATE clinic_physio_day SET cash_p=?, upi_p=?, updated_by=?, "
                                "updated_at=? WHERE business_date=?",
                                (vals["physio_cash_p"], vals["physio_upi_p"], who, now, date))
                con.commit()
                if _audit:
                    try:
                        _audit(con, "clinic_register_day", date,
                               "update" if before is not None else "insert",
                               before=({k: before[k] for k in FIELDS}
                                       if before is not None else None),
                               after=vals, who=who)
                        con.commit()
                    except Exception:            # noqa: BLE001
                        pass
                msg = "<div class='ok'><b>Saved.</b> %s</div>" % _esc(three_way(con, date)["why"])
    return _shell("Register — %s" % _human(date), _card_html(con, date, u, msg))


def _card_html(con, date, u, msg):
    reg = register_row(con, date)
    phy = physio_row(con, date)
    t = three_way(con, date)

    def box(name, val):
        v = "" if not val else "%d" % int(round(val / 100.0))
        return ("<td><input name='%s' value='%s' inputmode='numeric' pattern='[0-9]*' "
                "autocomplete='off' class='amt'></td>" % (name, _esc(v)))

    rows = []
    for sec, label in SECTIONS:
        cells = "".join(box("%s_%s_p" % (sec, tn), None if reg is None else reg["%s_%s_p" % (sec, tn)])
                        for tn, _ in TENDERS)
        extra = " <span class='hint'>(counts with Procedures)</span>" if sec == "dress" else ""
        rows.append("<tr><th class='sec'>%s%s</th>%s</tr>" % (label, extra, cells))

    phys = ("<tr><th class='sec'>Physiotherapy</th>%s%s<td class='none'>—</td></tr>"
            % (box("physio_cash_p", None if phy is None else phy["cash_p"]),
               box("physio_upi_p", None if phy is None else phy["upi_p"])))

    who = ""
    if reg is not None:
        who = ("<p class='mut'>last saved by <b>%s</b> at %s</p>"
               % (_esc(reg["updated_by"] or reg["entered_by"]),
                  _esc(reg["updated_at"] or reg["entered_at"])))
    clear = ""
    if reg is not None:
        clear = ("<form method='post' class='clearf' "
                 "onsubmit='return confirm(\"Clear this day completely?\")'>"
                 "<input type='hidden' name='clear' value='yes'>"
                 "<button type='submit' class='clear'>Clear this day</button></form>")
    return """
      <div class="card"><h2>%s</h2>
        <p class="mut">What the counter register says. Leave a box empty for nothing.</p>
        %s
        <form method="post">
        <table class="grid entry"><thead><tr><th></th><th>Cash</th><th>UPI</th><th>Card</th>
          </tr></thead><tbody>%s
          <tr class="sep"><td colspan="4">kept separately at reception</td></tr>
          %s</tbody></table>
        <p><label class="mut" for="note">Note (optional)</label><br>
           <input id="note" name="note" class="note" value="%s" maxlength="300"></p>
        <button type="submit" class="save">Save this day</button>
        </form>
        %s%s
        <p class="noprint navrow"><a class="btn" href="/finance/clinic/register">next unfilled day</a>
        <a class="btn" href="/finance/clinic/register/list">all days</a>
        <a class="btn" href="/finance/clinic/day/%s">the day&#8217;s entries</a></p>
      </div>%s""" % (_human(date), msg, "".join(rows), phys,
                     _esc("" if reg is None else (reg["note"] or "")), clear, who,
                     date, _compare_html(t, date))


def _compare_html(t, date):
    doc, bank = t["doc"], t["bank"]

    def line(label, reg_v, doc_v, bank_v, note=""):
        return ("<tr><th class='sec'>%s</th><td class='r'>%s</td><td class='r'>%s</td>"
                "<td class='r'>%s</td><td class='mut'>%s</td></tr>"
                % (label, _r(reg_v) if reg_v is not None else "—",
                   _r(doc_v) if doc_v is not None else "—",
                   _r(bank_v) if bank_v is not None else "—", note))

    upi_note = "" if t["bank_known"] else "statement not arrived"
    body = [line("Cash", t["r_cash"], doc["cash"] if doc["known"] else None, None,
                 "no bank feed exists for cash"),
            line("UPI", t["r_upi"], doc["upi"] if doc["known"] else None,
                 bank if t["bank_known"] else None, upi_note),
            line("Card", t["r_card"], doc["card"] if doc["known"] else None, None,
                 "the bank feed carries no card"),
            line("Physiotherapy", t["p_upi"] if t["p_upi"] is not None else None, None, None,
                 "its own UPI channel — not in the bank line above")]
    return """
      <div class="card"><h2>The three records, side by side</h2>
        <table class="grid"><thead><tr><th></th><th class="r">Register</th>
          <th class="r">Docterz</th><th class="r">Bank</th><th></th></tr></thead>
          <tbody>%s</tbody></table>
        <p class="verdict %s">%s</p>
        <p class="mut">This screen states what the three records say. It does not decide who is
        right, and it never accuses anyone. Where two agree and one differs, that is the one to
        look at first.</p>
      </div>""" % ("".join(body), t["verdict"].replace(" ", "_"), _esc(t["why"]))


def _denied():
    return """<div class="card"><h2>Not permitted</h2><p>The daily register belongs to the clinic
      desk. Your login is not on it. If that is wrong, ask Dr Manoj.</p></div>"""


def _shell(title, body):
    """LARGE TYPE, HIGH CONTRAST, VISIBLE BOXES. The owner, 04-Sep: "your smallest font is very eye
    straining for me, background hurts the eyes, boxes are barely visible."

    So: nothing on this screen is below 16px, the body sits on a soft grey rather than a bright
    white, every input has a 2px border and a 54px tap target, and the type is near-black on warm
    off-white. It is used on a phone, at the counter, early in the morning."""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#3c464e;--line:#8a9aa6;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;
      --entry:#fffbe6}
*{box-sizing:border-box}
body{margin:0;padding:14px;background:var(--bg);color:var(--ink);
 font:18px/1.6 "Segoe UI",system-ui,-apple-system,sans-serif;-webkit-text-size-adjust:100%%}
h1{font-size:23px;margin:0 0 12px;color:var(--accent);font-weight:700}
h2{font-size:20px;margin:0 0 10px;color:var(--accent)}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:16px;
 margin:0 0 16px}
.mut{color:var(--mut);font-size:16px}
.hint{color:var(--mut);font-size:15px;font-weight:400}
table.grid{width:100%%;border-collapse:collapse;font-size:18px}
.grid th,.grid td{border:2px solid var(--line);padding:10px}
.grid thead th{background:#cfdae3;font-size:17px;color:var(--ink)}
.r{text-align:right;white-space:nowrap}.d{white-space:nowrap;font-weight:600}
.sec{text-align:left;background:#eef2f5;width:33%%;font-size:18px}
.none{text-align:center;color:var(--mut)}
tr.sep td{background:#eef2f5;color:var(--mut);font-size:16px;text-align:center;padding:8px}
.entry input.amt{width:100%%;min-height:54px;font-size:22px;padding:10px 12px;
 border:2px solid #5b6b76;border-radius:8px;text-align:right;background:var(--entry);color:var(--ink)}
.entry input.amt:focus{border-color:var(--accent);background:#fff;outline:3px solid #9dc0e0}
.note{width:100%%;min-height:50px;padding:10px;border:2px solid #5b6b76;border-radius:8px;
 font-size:18px;background:var(--entry)}
button.save{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:16px 26px;
 font-size:20px;font-weight:600;cursor:pointer;width:100%%;margin-top:6px}
button.clear{background:var(--paper);color:#8c2f2f;border:2px solid #8c2f2f;border-radius:9px;
 padding:11px 18px;font-size:17px;cursor:pointer}
.clearf{margin-top:14px}
a.btn{display:inline-block;border:2px solid var(--accent);color:var(--accent);border-radius:9px;
 padding:11px 16px;text-decoration:none;font-size:17px;margin:6px 8px 0 0;background:var(--paper)}
.navrow{margin-top:14px}
.ok{background:#dff0d8;border-left:6px solid #2c6e2f;padding:13px 15px;margin-bottom:14px;
 font-size:18px}
.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:13px 15px;margin-bottom:14px;
 font-size:18px}
.pill{font-size:16px;padding:4px 11px;border-radius:12px;background:#e3e8eb;white-space:nowrap;
 border:1px solid var(--line)}
.pill.all_agree{background:#dff0d8}.pill.not_entered{background:#eceff1;color:var(--mut)}
.pill.docterz_differs,.pill.register_differs,.pill.all_differ{background:#fadbd8}
.pill.bank_differs,.pill.waiting_bank{background:#fdeecd}
.verdict{font-weight:700;margin:14px 0 6px;font-size:19px}
@media (max-width:620px){
 body{padding:10px;font-size:19px}
 .card{padding:12px}
 .grid th,.grid td{padding:8px 6px}
 .sec{width:30%%;font-size:17px}
 .entry input.amt{font-size:23px;min-height:58px}
 a.btn{display:block;text-align:center;margin:10px 0 0}
}
@media print{@page{size:A4 portrait;margin:12mm}.noprint,form{display:none!important}
 body{background:#fff;padding:0;font-size:12pt}.card{border:none;padding:0}}
</style></head><body><h1>Dr. Manoj Agarwal Clinic — daily register</h1>
%s</body></html>""" % (_esc(title), body)
