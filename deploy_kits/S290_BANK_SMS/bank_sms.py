#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bank_sms.py -- S290 (17-Sep-2026). The bank's morning settlement SMS, straight from the owner's phone.

THE OWNER, 17-Sep-2026: the bank sends an SMS early next morning with the UPI amount settled into
the Sanjeevni and clinic ICICI accounts. His personal Apps Script log of it "needs to be discarded";
"we need our own MacroDroid to make it proper". So MacroDroid on his phone posts each matching SMS
here, and the day's bank figure is known hours before the MPR report.

WHAT WAS PROVED BEFORE A LINE WAS WRITTEN (his shared sheet, read at S265): every settlement SMS on
day D equals, to the rupee, the bank MPR total (upi_txn) of day D-1 -- Sanjeevni 15 of 15 days,
clinic 8 of 8, 22-Aug to 17-Sep. So business_date = credit date - 1 day.

THE MESSAGE (ICICI's own words, one per settlement):
  ICICI Bank Account XX000 credited:Rs. 1,234.00 on 17-Sep-26. Info EZY*ICICIPOS_SET_10XX123456_.
  Available Balance is Rs. 1,00,000.00.            (illustration -- not a real figure)
The merchant id's last six digits (the digits after 10XX) name the unit through business_unit.
merchant_id -- the same table the MPR reader uses -- so nothing is hard-coded to an account.

PRIVACY AND SAFETY
  * Only a message that parses as an ICICI POS settlement credit is stored. Anything else -- an OTP,
    a debit, a personal message -- is answered "ignored" and NOTHING of it is written, not even a
    count by sender. The phone filters first; the server filters again.
  * The door is one address, opened only by the key in /root/finance/bank_sms.key (created by the
    installer, 0600). The owner copies it from his own signed-in check page onto the phone -- it is
    never printed to a terminal, a log or a chat. At most 60 posts an hour are accepted.
  * The figure is an EARLY SIGNAL. The MPR stays the record; this page shows the two side by side and
    says loudly when they differ. A day with no SMS reads "no SMS", never zero.

NO JAVASCRIPT. Tables on first request (F-303).
"""
import datetime as dt
import hmac
import os
import re
import time

from flask import Blueprint, jsonify, request

bp = Blueprint("bank_sms", __name__)
_db = None
_require = None
_audit = None
APP_VERSION = "S290-BANK-SMS-1.0"
_schema_done = False
_hits = []

KEY_FILE = os.environ.get("BANK_SMS_KEY_FILE", "/root/finance/bank_sms.key")
RATE_PER_HOUR = 60

SCHEMA = """
CREATE TABLE IF NOT EXISTS bank_sms_settlement (
    id            INTEGER PRIMARY KEY,
    unit          TEXT NOT NULL,
    credit_date   TEXT NOT NULL,           -- the date in the SMS
    business_date TEXT NOT NULL,           -- credit_date - 1 day (proved on 23 days)
    amount_p      INTEGER NOT NULL,
    balance_p     INTEGER,
    acct_tail     TEXT NOT NULL,
    ref           TEXT NOT NULL,
    sms_text      TEXT NOT NULL,
    phone_sender  TEXT NOT NULL DEFAULT '',
    received_at   TEXT NOT NULL,           -- the server's clock (IST)
    seen          INTEGER NOT NULL DEFAULT 1,
    UNIQUE (unit, credit_date, amount_p, ref)
);
CREATE INDEX IF NOT EXISTS bank_sms_bdate ON bank_sms_settlement(business_date);
"""

SMS_RE = re.compile(
    r"ICICI\s+Bank\s+Account\s+XX(?P<acct>\d{3,4})\s+credited\s*:?\s*Rs\.?\s*(?P<amt>[\d,]+(?:\.\d{1,2})?)"
    r"\s+on\s+(?P<date>\d{1,2}-[A-Za-z]{3}-\d{2,4})\.?\s+Info\s+(?P<info>.+?)\.\s+"
    r"Available\s+Balance\s+is\s+Rs\.?\s*(?P<bal>[\d,]+(?:\.\d{1,2})?)", re.I | re.S)
MID_RE = re.compile(r"ICICIPOS[\s_*]*SET[\s_]*10XX(?P<mid>\d{6})", re.I)


def _ensure(con):
    global _schema_done
    if _schema_done:
        return
    con.executescript(SCHEMA)
    con.commit()
    _schema_done = True


def init(app, db_getter, require_fn, audit_fn=None, url_prefix=""):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit
    _db, _require, _audit = db_getter, require_fn, audit_fn
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


def _now():
    v = os.environ.get("BANK_SMS_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now().replace(microsecond=0)


def _paise(s):
    try:
        return int(round(float(str(s).replace(",", "")) * 100))
    except (TypeError, ValueError):
        return None


def _date(s):
    for fmt in ("%d-%b-%y", "%d-%b-%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse(text):
    """The settlement fields, or None when the text is not an ICICI POS settlement credit."""
    m = SMS_RE.search(text or "")
    if not m:
        return None
    mid = MID_RE.search(m.group("info"))
    d = _date(m.group("date"))
    amt = _paise(m.group("amt"))
    if not mid or d is None or not amt or amt <= 0:
        return None
    return dict(acct_tail=m.group("acct"), amount_p=amt, balance_p=_paise(m.group("bal")),
                credit_date=d.isoformat(), business_date=(d - dt.timedelta(days=1)).isoformat(),
                mid_tail=mid.group("mid"), ref=m.group("info").strip()[:80])


def unit_for_mid(con, tail):
    for r in con.execute("SELECT code, merchant_id FROM business_unit WHERE merchant_id IS NOT NULL"):
        if str(r["merchant_id"] or "").endswith(tail):
            return r["code"]
    return None


def _key():
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def _rate_ok():
    now = time.time()
    while _hits and now - _hits[0] > 3600:
        _hits.pop(0)
    if len(_hits) >= RATE_PER_HOUR:
        return False
    _hits.append(now)
    return True


@bp.route("/finance/api/bank-sms", methods=["POST"])
def post_sms():
    """The phone's door. The front gate lets this one path through; the key is checked HERE."""
    key = _key()
    given = request.headers.get("X-Bank-Sms-Key", "") or request.values.get("key", "")
    if not key or not given or not hmac.compare_digest(str(given), key):
        return jsonify(ok=False, error="bad_key"), 401
    if not _rate_ok():
        return jsonify(ok=False, error="too_many"), 429
    js = request.get_json(silent=True) or {}          # MacroDroid may send form, query or JSON
    text = (request.values.get("text") or js.get("text") or "")[:600]
    sender = (request.values.get("sender") or js.get("sender") or "")[:40]
    p = parse(text)
    if p is None:
        return jsonify(ok=True, stored=False, ignored=True), 200       # nothing of it is kept
    con = _db()
    _ensure(con)
    unit = unit_for_mid(con, p["mid_tail"])
    if unit is None:
        return jsonify(ok=True, stored=False, ignored=True, why="unknown merchant"), 200
    stamp = _now().strftime("%Y-%m-%d %H:%M:%S")
    cur = con.execute(
        "INSERT INTO bank_sms_settlement (unit, credit_date, business_date, amount_p, balance_p, acct_tail, ref, "
        "sms_text, phone_sender, received_at) VALUES (?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(unit, credit_date, amount_p, ref) DO UPDATE SET seen = seen + 1",
        (unit, p["credit_date"], p["business_date"], p["amount_p"], p["balance_p"], p["acct_tail"], p["ref"],
         text.strip(), sender, stamp))
    con.commit()
    return jsonify(ok=True, stored=True, unit=unit, business_date=p["business_date"],
                   amount=p["amount_p"] // 100), 200


# ---------------------------------------------------------------- the owner's page
def sms_total_p(con, unit, business_date):
    """For other screens: the SMS figure for a unit's business day, or None when no SMS came."""
    try:
        _ensure(con)
        r = con.execute("SELECT SUM(amount_p) s, COUNT(*) n FROM bank_sms_settlement WHERE unit=? AND business_date=?",
                        (unit, business_date)).fetchone()
        return int(r["s"]) if r and r["n"] else None
    except Exception:                            # noqa: BLE001
        return None


def _mpr_p(con, unit, d):
    try:
        r = con.execute("SELECT SUM(amount_p) s, COUNT(*) n FROM upi_txn WHERE unit=? AND txn_date=?", (unit, d)).fetchone()
        return int(r["s"]) if r and r["n"] else None
    except Exception:                            # noqa: BLE001
        return None


def _r(p):
    return "—" if p is None else "{:,}".format(int(round(p / 100.0)))


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


@bp.route("/finance/bank-sms")
def page():
    u, err = _require("checker", unit="medical")
    if err:
        u, err = _require("checker", unit="clinic")
    if err:
        return _shell("<div class='card'><h2>Not permitted</h2><p>This page is the doctors'.</p></div>"), 403
    con = _db()
    _ensure(con)
    today = _now().date()
    out = []
    last = con.execute("SELECT MAX(received_at) m FROM bank_sms_settlement").fetchone()["m"]
    late = today.isoformat() + " 10:00:00"
    got_today = con.execute("SELECT COUNT(*) n FROM bank_sms_settlement WHERE credit_date=?", (today.isoformat(),)).fetchone()["n"]
    if _now().strftime("%Y-%m-%d %H:%M:%S") >= late and not got_today:
        out.append("<div class='bad'>No settlement SMS has reached the server today, and it is past 10:00. "
                   "Check that MacroDroid is running on the phone.</div>")
    out.append("<div class='card'><h2>Bank settlement SMS</h2><p class='mut'>The morning SMS is the early figure; the MPR "
               "is the record. Last SMS received: <b>%s</b>.</p></div>" % _esc(last or "none yet"))
    rows = []
    for i in range(1, 31):
        d = (today - dt.timedelta(days=i)).isoformat()
        cells = []
        any_ = False
        for unit, label in (("medical", "Sanjeevni"), ("clinic", "Clinic")):
            s, m = sms_total_p(con, unit, d), _mpr_p(con, unit, d)
            if s is None and m is None:
                cells.append("<td class='mut'>—</td>")
                continue
            any_ = True
            if s is None:
                st = "no SMS"
            elif m is None:
                st = "MPR not yet"
            elif s == m:
                st = "✓ matches MPR"
            else:
                st = "<b class='bad'>differs by ₹ %s</b>" % _r(abs(s - m))
            cells.append("<td>SMS ₹ %s · MPR ₹ %s<br><span class='mut'>%s</span></td>" % (_r(s), _r(m), st))
        if any_:
            rows.append("<tr><td class='d'>%s</td>%s</tr>" % (dt.date.fromisoformat(d).strftime("%d-%b"), "".join(cells)))
    out.append("<div class='card'><table class='grid'><thead><tr><th>Business day</th><th>Sanjeevni</th><th>Clinic</th></tr></thead>"
               "<tbody>%s</tbody></table></div>" % ("".join(rows) or "<tr><td colspan='3'>Nothing yet.</td></tr>"))
    key = _key()
    out.append("""<details class="card"><summary><b>Phone setup — MacroDroid</b> (one time)</summary>
<ol>
<li>Trigger: <b>SMS Received</b> · any sender · message content <b>contains</b> <code>ICICIPOS</code></li>
<li>Action: <b>HTTP Request</b> · method <b>POST</b> · URL <code>https://followup.dr-manoj.in/finance/api/bank-sms</code></li>
<li>Header: name <code>X-Bank-Sms-Key</code> · value — long-press the key below on this phone, copy, paste:</li>
</ol>
<p class="key">%s</p>
<ol start="4">
<li>Body: content type <b>form</b> · field <code>text</code> = <code>[sms_message]</code> · field <code>sender</code> = <code>[sms_number]</code></li>
<li>Android settings: MacroDroid → Battery → <b>Unrestricted</b>.</li>
</ol></details>""" % (_esc(key) if key else "— the key file is missing; re-run the installer —"))
    return _shell("".join(out))


def _shell(body):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5"><title>Bank SMS</title><style>
body{margin:0;padding:14px;background:#dfe5e9;color:#14181c;font:17px/1.55 "Segoe UI",system-ui,sans-serif}
h1{font-size:22px;color:#14456e;margin:0 0 12px}h2{font-size:19px;color:#14456e;margin:0 0 8px}
.card{background:#fffdf7;border:2px solid #8a9aa6;border-radius:10px;padding:14px;margin:0 0 14px;overflow-x:auto}
.mut{color:#3c464e;font-size:15px}.bad{color:#9c2a20}div.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:10px 14px;margin-bottom:12px}
table.grid{width:100%%;border-collapse:collapse}.grid th,.grid td{border:1px solid #8a9aa6;padding:8px;vertical-align:top}
.d{white-space:nowrap;font-weight:600}code{background:#eef2f5;padding:1px 5px;border-radius:4px}
.key{font:20px monospace;background:#fffbe6;border:2px dashed #14456e;padding:12px;word-break:break-all;user-select:all}
</style></head><body><h1>Dr. Manoj Agarwal Clinic — Bank SMS</h1>%s<p class="mut"><a href="/portal">← Portal</a></p></body></html>""" % body
