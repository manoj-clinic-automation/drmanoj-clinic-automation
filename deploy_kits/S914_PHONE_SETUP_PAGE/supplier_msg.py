#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""supplier_msg.py -- S407 (26-Sep-2026, D623). NEFT done in one tap; suppliers told by WhatsApp from the reception phone,
automatically. Mounted from purchase_app.init (fail-soft); reads purchase_app's own sheet, phone book and cheque register
in process, never a copy.

THE OWNER (25/26-Sep): "The bulk NEFT goes by cheque to Yes Bank 2-3 days after the papers; the SMS comes from Yes Bank. A
provisional entry visible to Amir and the staff; suppliers told by WhatsApp with the full account number and IFSC. All
messages from the reception mobile. Per-supplier taps are too taxing. I log the provisional once; then maximum automated."

  1  NEFT done, one tap (owner) on the pay page of a FINALISED month: writes purchase_neft_event (S405's table) kind
     provisional source owner -- or confirms S405's pending SMS event for that month; never two live events for one month.
     A repeat within 10 minutes answers already. Undo within 24 h (audited; refused once the bank has confirmed).
  2  Confirmed by bank: a Yes Bank statement line (bank_statement_line, the NEFT narration, a debit equal to the NEFT portion
     within setting neft.stmt_tolerance_p, default 0, within -3..+15 days of the date) sets bank_line_id -> green. A statement
     that covers the date and holds a different NEFT debit -> red with the difference (and a Needs-you line). Checked on every
     page read (the statement loader is not touched: the next read after a load is the check).
  3  The message queue (server): on the provisional, ONE supplier_msg row per NEFT supplier -- to_number the phone book's first
     number, body EXACTLY 'Sanjeevni Medicos, Bareilly: ₹<amount> for <Month YYYY> purchases transferred by NEFT on <dd-Mon-yyyy>
     to your account <full account number>, IFSC <IFSC>. Thank you.' (amount from the sheet line; account and IFSC as the advice
     file uses them). No number -> status skipped 'number nahi'. A cheque supplier gets its row when purchase_cheque.handed_at is
     set: '... paid by cheque no <n> dated <date> for <Month YYYY> purchases. Thank you.'
  4  The reception phone (MacroDroid): GET /finance/api/supplier-msg/next -> the oldest queued row {id, to, text} or {};
     POST /finance/api/supplier-msg/done {id, ok, error}. Both token-gated (setting supplier_msg.phone_token, made at install,
     shown ONCE on the setup page /finance/purchase/page/phone-setup). A failure -> failed, attempts+1, retried after 30 minutes.
  5  Backup, one tap: a row queued > 30 minutes shows 'Pending — <vendor>' with Bhejo (a sender's login: setting
     supplier_msg.senders, default manoj,shavez); the wa.me link opens on whatever phone taps, and the row is marked sent (who, when).
  6  Where it shows: the pay page (owner English / staff Hindi), Amir's board card, Needs you.

NUMBERS RULE (absolute): supplier phone numbers, account numbers and IFSCs live only in the database; they go into a message
body built here for the reception phone (the token door) or into a wa.me link answered ONLY to a sender's login -- never into a
page, a log, the audit, or any other response. Every page lists vendors, statuses and times, nothing else.
"""
import datetime as dt
import hmac
import os
import re
import secrets
import sys
from urllib.parse import quote

from flask import Blueprint, jsonify, request

bp = Blueprint("supplier_msg", __name__)
_db = _require = None
_unit = "medical"
_prefix = "/finance/purchase"
FIRM = "Sanjeevni Medicos, Bareilly"
REPEAT_MIN = 10
UNDO_H = 24
RETRY_MIN = 30
PENDING_MIN = 30
MAX_ATTEMPTS = 5

DDL = (
    "CREATE TABLE IF NOT EXISTS supplier_msg ("
    " id INTEGER PRIMARY KEY, month TEXT NOT NULL, vendor_norm TEXT NOT NULL, vendor TEXT NOT NULL,"
    " kind TEXT NOT NULL DEFAULT 'neft', ref INTEGER, channel TEXT NOT NULL DEFAULT 'whatsapp',"
    " to_number TEXT, body TEXT NOT NULL,"
    " status TEXT NOT NULL CHECK (status IN ('queued','sent','failed','skipped')),"
    " queued_at TEXT NOT NULL, sent_at TEXT, sent_by TEXT, attempts INTEGER NOT NULL DEFAULT 0,"
    " last_error TEXT, last_try_at TEXT,"
    " UNIQUE (month, vendor_norm, kind, ref))",
    # S405's table, made here too so a fresh box has it before the first bank SMS
    "CREATE TABLE IF NOT EXISTS purchase_neft_event ("
    " id INTEGER PRIMARY KEY, month TEXT NOT NULL, kind TEXT NOT NULL, source TEXT NOT NULL,"
    " amount_p INTEGER NOT NULL, sms_date TEXT, utr TEXT, yes_id INTEGER, bank_line_id INTEGER,"
    " created_at TEXT NOT NULL, created_by TEXT, confirmed_by TEXT, confirmed_at TEXT, note TEXT)",
)
SETTINGS = {
    "supplier_msg.senders": ("manoj,shavez", "S407 D623 -- logins that may open a supplier message's wa.me link (the backup Bhejo)"),
    "neft.stmt_tolerance_p": ("0", "S407 D623 -- paise of tolerance when the Yes Bank statement confirms the month's NEFT"),
}


def init(app, db_getter, require_fn, unit="medical", url_prefix="/finance/purchase"):
    global _db, _require, _unit, _prefix
    _db, _require, _unit, _prefix = db_getter, require_fn, unit, (url_prefix or "/finance/purchase")
    app.register_blueprint(bp)
    return bp


# ---------------------------------------------------------------- small things
def _now():
    return dt.datetime.now().replace(microsecond=0)


def _iso():
    return _now().isoformat()


def _pa():
    import purchase_app as pa                                  # noqa: PLC0415
    return pa


def ensure(con):
    for d in DDL:
        con.execute(d)
    _s454_cols(con)                                            # S454 (F-702): handed_at
    con.commit()


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r and r[0] is not None else default)
    except Exception:                                          # noqa: BLE001
        return default


def _int(con, key, default):
    try:
        return int(str(_setting(con, key, str(default))).strip())
    except (TypeError, ValueError):
        return default


def seed(con):
    """The settings and the phone token (made once, random; never printed here)."""
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, (v, note) in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    if not _setting(con, "supplier_msg.phone_token", ""):
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    ("supplier_msg.phone_token", secrets.token_hex(24), "S407 D623 -- the reception phone's token; shown once on the setup page"))
    con.commit()


def _who(u):
    return (u or {}).get("user") or (u or {}).get("username") or ""


def _is_owner(u):
    try:
        return bool(_pa()._is_doctor(u))
    except Exception:                                          # noqa: BLE001
        return False


def _is_sender(con, u):
    if _is_owner(u):
        return True
    names = {w.strip().lower() for w in _setting(con, "supplier_msg.senders", "manoj,shavez").split(",") if w.strip()}
    return _who(u).lower() in names


def _inr(p):
    v = str(int(round(abs(int(p or 0)) / 100.0)))
    if len(v) > 3:
        head, tail = v[:-3], v[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        v = ",".join(parts) + "," + tail
    return "₹" + v


def _dmy(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%b-%Y")
    except (TypeError, ValueError):
        return str(iso or "")


def _month_name(ym):
    try:
        return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except (TypeError, ValueError):
        return ym


def _esc(s):
    return (str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _good_month(m):
    return bool(re.match(r"^\d{4}-\d{2}$", str(m or "")))


# ---------------------------------------------------------------- the sheet, read in process
def sheet(con, month):
    """(neft_p, neft_groups, final) from purchase_app's own _pay_rows."""
    pa = _pa()
    s, groups = pa._pay_rows(con, month)
    neft = [g for g in groups if g["route"] == "NEFT" and g["payable_p"] > 0]
    return int(sum(g["payable_p"] for g in neft)), neft, (s["status"]["status"] == "final")


def live_event(con, month):
    ensure(con)
    r = con.execute("SELECT * FROM purchase_neft_event WHERE month=? AND kind<>'rejected' ORDER BY id DESC LIMIT 1", (month,)).fetchone()
    return dict(r) if r else None


# ---------------------------------------------------------------- the bank
def _stmt_ref(con):
    try:
        acct = str(_pa()._pay_config_s265(con, "debit_account", "") or "")
    except Exception:                                          # noqa: BLE001
        acct = ""
    return re.sub(r"\D", "", acct)[-4:]


def bank_check(con, ev):
    """Confirm or contradict the event against the Yes Bank statement. Returns (status, line, diff_p):
    'confirmed' | 'mismatch' | 'awaiting' | 'nostmt'."""
    if not ev:
        return "none", None, None
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='bank_statement_line'").fetchone():
        return "awaiting", None, None
    date = str(ev.get("sms_date") or ev.get("created_at") or "")[:10]
    tol = _int(con, "neft.stmt_tolerance_p", 0)
    if ev.get("bank_line_id"):
        r = con.execute("SELECT id, txn_date, withdrawal_p FROM bank_statement_line WHERE id=?", (ev["bank_line_id"],)).fetchone()
        return "confirmed", (dict(r) if r else None), 0
    try:
        d0 = dt.date.fromisoformat(date)
    except ValueError:
        return "awaiting", None, None
    lo, hi = (d0 - dt.timedelta(days=3)).isoformat(), (d0 + dt.timedelta(days=15)).isoformat()
    ref = _stmt_ref(con)
    rows = [dict(r) for r in con.execute(
        "SELECT id, account_ref, txn_date, withdrawal_p, description FROM bank_statement_line WHERE withdrawal_p>0 "
        "AND UPPER(description) LIKE '%NEFT%' AND txn_date BETWEEN ? AND ? ORDER BY txn_date, id", (lo, hi))]
    if ref and any(str(r["account_ref"] or "").endswith(ref) for r in rows):
        rows = [r for r in rows if str(r["account_ref"] or "").endswith(ref)]
    amt = int(ev["amount_p"])
    hit = next((r for r in rows if abs(int(r["withdrawal_p"]) - amt) <= tol), None)
    if hit:
        con.execute("UPDATE purchase_neft_event SET bank_line_id=? WHERE id=?", (hit["id"], ev["id"]))
        con.commit()
        return "confirmed", hit, 0
    covered = con.execute("SELECT 1 FROM bank_statement_period WHERE period_to>=? LIMIT 1", (date,)).fetchone() if \
        con.execute("SELECT 1 FROM sqlite_master WHERE name='bank_statement_period'").fetchone() else None
    if not covered:
        return "awaiting", None, None
    if rows:
        near = min(rows, key=lambda r: abs(int(r["withdrawal_p"]) - amt))
        return "mismatch", near, int(near["withdrawal_p"]) - amt
    return "mismatch", None, None


# ---------------------------------------------------------------- the queue
def _digits(con, vendor):
    try:
        pa = _pa()
        return pa._wa_digits(pa.book_number(con, vendor, "pay"))     # S574: the Payment message number
    except Exception:                                          # noqa: BLE001
        return ""


def _neft_body(amount_p, month, date_iso, acct, ifsc):
    return ("%s: %s for %s purchases transferred by NEFT on %s to your account %s, IFSC %s. Thank you."
            % (FIRM, _inr(amount_p), _month_name(month), _dmy(date_iso), acct, ifsc))


def _cheque_body(amount_p, month, cheque_no, cheque_date):
    return ("%s: %s for %s purchases paid by cheque no %s dated %s. Thank you."
            % (FIRM, _inr(amount_p), _month_name(month), cheque_no, _dmy(cheque_date)))


def _queue_row(con, month, vendor_norm, vendor, kind, ref, to_number, body, skip_why=None):
    st = "skipped" if skip_why else "queued"
    con.execute("INSERT OR IGNORE INTO supplier_msg (month, vendor_norm, vendor, kind, ref, to_number, body, status, queued_at, last_error) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)", (month, vendor_norm, vendor, kind, ref, to_number or None, body, st, _iso(), skip_why))


def queue_neft(con, month, ev):
    """ONE row per NEFT supplier of the month, from the sheet and the phone book. Idempotent."""
    ensure(con)
    pa = _pa()
    _p, groups, _f = sheet(con, month)
    acc = pa._advice_accounts_s265(con)
    date = str(ev.get("sms_date") or ev.get("created_at") or "")[:10]
    n = 0
    for g in groups:
        a = acc.get(g["norm"])
        if not a:
            _queue_row(con, month, g["norm"], g["name"], "neft", ev["id"], None, "(no confirmed account)", "account nahi")
            continue
        body = _neft_body(g["payable_p"], month, date, a["acct"], a["ifsc"])
        to = _digits(con, g["name"])
        _queue_row(con, month, g["norm"], g["name"], "neft", ev["id"], to, body, None if to else "number nahi")
        if to:
            n += 1
    con.commit()
    return n


def queue_cheques(con, month):
    """A cheque supplier gets its row the moment its cheque is marked handed over (read on every page read)."""
    ensure(con)
    pa = _pa()
    try:
        rows = pa._cheque_rows_s270(con, month)
    except Exception:                                          # noqa: BLE001
        return 0
    n = 0
    for c in rows:
        if c["voided_at"] or not c["handed_at"]:
            continue
        if con.execute("SELECT 1 FROM supplier_msg WHERE kind='cheque' AND ref=?", (c["id"],)).fetchone():
            continue
        body = _cheque_body(c["amount_p"], month, c["cheque_no"], c["cheque_date"])
        to = _digits(con, c["vendor"])
        _queue_row(con, month, c["vendor_norm"], c["vendor"], "cheque", c["id"], to, body, None if to else "number nahi")
        n += 1
    con.commit()
    return n


def messages(con, month=None):
    ensure(con)
    sql = ("SELECT id, month, vendor_norm, vendor, kind, ref, status, queued_at, sent_at, sent_by, attempts, last_error, last_try_at, handed_at FROM supplier_msg"   # S664: + handed_at
           " WHERE kind IN ('neft','cheque')")                # S454: the payment messages only -- an order message is the order screen's
    args = ()
    if month:
        sql += " AND month=?"
        args = (month,)
    return [dict(r) for r in con.execute(sql + " ORDER BY id", args)]         # never to_number, never body


def _age_min(iso):
    try:
        return int((_now() - dt.datetime.fromisoformat(str(iso))).total_seconds() // 60)
    except (TypeError, ValueError):
        return 0


def pending(con, month=None):
    """Rows queued (or failed) for more than PENDING_MIN minutes -- the backup's list and the Needs-you count."""
    return [m for m in messages(con, month) if m["status"] in ("queued", "failed") and _age_min(m["queued_at"]) >= PENDING_MIN]


# ---------------------------------------------------------------- the state of a month
def state(con, month):
    ensure(con)
    try:
        neft_p, groups, final = sheet(con, month)
    except Exception:                                          # noqa: BLE001
        neft_p, groups, final = 0, [], False
    ev = live_event(con, month)
    bank, line, diff = bank_check(con, ev)
    if ev:
        ev = live_event(con, month)                       # bank_check may have set bank_line_id
        queue_cheques(con, month)
    msgs = messages(con, month)
    can_undo = bool(ev and bank != "confirmed" and _age_min(ev["created_at"]) < UNDO_H * 60)
    return dict(month=month, final=final, neft_p=neft_p, vendors=[g["name"] for g in groups],
                event=(dict(id=ev["id"], kind=ev["kind"], source=ev["source"], amount_p=ev["amount_p"], date=ev.get("sms_date"),
                            utr=ev.get("utr"), created_at=ev["created_at"], created_by=ev.get("created_by"),
                            confirmed_by=ev.get("confirmed_by"), bank_line_id=ev.get("bank_line_id")) if ev else None),
                status=("none" if not ev else bank), bank_line=(dict(id=line["id"], date=line["txn_date"], amount_p=line["withdrawal_p"]) if line else None),
                diff_p=diff, can_undo=can_undo,
                messages=[dict(m, pending=(m["status"] in ("queued", "failed") and _age_min(m["queued_at"]) >= PENDING_MIN)) for m in msgs],
                counts=dict(sent=sum(1 for m in msgs if m["status"] == "sent"), queued=sum(1 for m in msgs if m["status"] in ("queued", "failed")),
                            skipped=sum(1 for m in msgs if m["status"] == "skipped")))


def neft_done(con, u, month, date_iso, utr):
    """The owner's one tap. Returns (body, code)."""
    ensure(con)
    pa = _pa()
    if not _good_month(month):
        return dict(ok=False, error="bad_month"), 400
    try:
        d = dt.date.fromisoformat(str(date_iso or "")[:10]) if date_iso else _now().date()
    except ValueError:
        return dict(ok=False, error="bad_date", message="the date reads dd-mm-yyyy"), 400
    if d > _now().date():
        return dict(ok=False, error="bad_date", message="a future date"), 400
    neft_p, groups, final = sheet(con, month)
    if not final:
        return dict(ok=False, error="not_final", message="%s is not finalised; lock the month first." % _month_name(month)), 409
    if neft_p <= 0:
        return dict(ok=False, error="no_neft", message="nothing is payable by NEFT this month"), 409
    ev = live_event(con, month)
    who = _who(u)
    if ev:
        if ev.get("source") == "sms" and not ev.get("confirmed_by"):
            con.execute("UPDATE purchase_neft_event SET confirmed_by=?, confirmed_at=?, utr=COALESCE(utr,?) WHERE id=?",
                        (who, _iso(), (utr or None), ev["id"]))
            con.commit()
            ev = live_event(con, month)
            n = queue_neft(con, month, ev)
            pa._audit(con, who, "neft_done", month, dict(event=ev["id"], confirmed_sms=True, queued=n))
            con.commit()
            return dict(ok=True, event_id=ev["id"], confirmed_sms=True, queued=n, already=False), 200
        return dict(ok=True, already=True, event_id=ev["id"], within_10min=(_age_min(ev["created_at"]) < REPEAT_MIN)), 200
    cur = con.execute("INSERT INTO purchase_neft_event (month, kind, source, amount_p, sms_date, utr, created_at, created_by, confirmed_by, confirmed_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?)", (month, "provisional", "owner", neft_p, d.isoformat(), (utr or "").strip()[:40] or None, _iso(), who, who, _iso()))
    ev = live_event(con, month)
    n = queue_neft(con, month, ev)
    pa._audit(con, who, "neft_done", month, dict(event=cur.lastrowid, amount_p=neft_p, date=d.isoformat(), queued=n))
    con.commit()
    return dict(ok=True, event_id=cur.lastrowid, queued=n, already=False, amount_p=neft_p), 200


def neft_undo(con, u, month):
    ensure(con)
    ev = live_event(con, month)
    if not ev:
        return dict(ok=False, error="no_event"), 404
    bank, _l, _d = bank_check(con, ev)
    if bank == "confirmed":
        return dict(ok=False, error="bank_confirmed", message="the bank has confirmed this NEFT; it cannot be undone here"), 409
    if _age_min(ev["created_at"]) >= UNDO_H * 60:
        return dict(ok=False, error="too_late", message="an undo is allowed for 24 hours"), 409
    who = _who(u)
    con.execute("UPDATE purchase_neft_event SET kind='rejected', note=? WHERE id=?", ("undone by %s, %s" % (who, _iso()), ev["id"]))
    n = con.execute("UPDATE supplier_msg SET status='skipped', last_error='undone' WHERE kind='neft' AND ref=? AND status IN ('queued','failed')", (ev["id"],)).rowcount
    _pa()._audit(con, who, "neft_undo", month, dict(event=ev["id"], cancelled=n))
    con.commit()
    return dict(ok=True, event_id=ev["id"], cancelled=n), 200


# ---------------------------------------------------------------- routes: the owner / staff
def _person(*roles):
    u, err = _require(*roles)
    return (None, err) if err else (u, None)


@bp.route("/finance/purchase/api/neft-state")
def api_neft_state():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    m = request.args.get("month") or ""
    if not _good_month(m):
        return jsonify(ok=False, error="bad_month"), 400
    con = _db()
    st = state(con, m)
    st["ok"], st["me"] = True, ("owner" if _is_owner(u) else ("sender" if _is_sender(con, u) else "viewer"))
    return jsonify(st)


@bp.route("/finance/purchase/api/neft-done", methods=["POST"])
def api_neft_done():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_owner(u):
        return jsonify(ok=False, error="owner_only", message="Only the doctor records the NEFT."), 403
    b = request.get_json(silent=True) or {}
    body, code = neft_done(_db(), u, str(b.get("month") or ""), b.get("date"), b.get("utr"))
    return jsonify(**body), code


@bp.route("/finance/purchase/api/neft-undo", methods=["POST"])
def api_neft_undo():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_owner(u):
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    m = str(b.get("month") or "")
    if not _good_month(m):
        return jsonify(ok=False, error="bad_month"), 400
    body, code = neft_undo(_db(), u, m)
    return jsonify(**body), code


@bp.route("/finance/purchase/api/supplier-msg/send", methods=["POST"])
def api_msg_send():
    """The backup Bhejo: the wa.me link, to a sender's login only; the row is marked sent (who, when)."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    if not _is_sender(con, u):
        return jsonify(ok=False, error="not_a_sender", message="Shavez or Dr Manoj sends these."), 403
    b = request.get_json(silent=True) or {}
    try:
        mid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        mid = 0
    ensure(con)
    r = con.execute("SELECT id, status, to_number, body, vendor FROM supplier_msg WHERE id=?", (mid,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_message"), 404
    if r["status"] == "sent":
        return jsonify(ok=True, already=True, id=mid), 200
    if not r["to_number"]:
        return jsonify(ok=False, error="no_number", message="no WhatsApp number in the phone book for %s" % r["vendor"]), 409
    con.execute("UPDATE supplier_msg SET status='sent', sent_at=?, sent_by=? WHERE id=?", (_iso(), _who(u), mid))
    _pa()._audit(con, _who(u), "supplier_msg_sent", str(mid), dict(vendor=r["vendor"], via="wa.me (backup)"))
    con.commit()
    return jsonify(ok=True, id=mid, wa_url="https://wa.me/%s?text=%s" % (r["to_number"], quote(r["body"], safe=""))), 200


# ---------------------------------------------------------------- routes: the reception phone (token)
def _token_ok(con):
    tok = _setting(con, "supplier_msg.phone_token", "")
    given = request.headers.get("X-Phone-Token", "") or request.values.get("token", "")
    return bool(tok and given and hmac.compare_digest(str(given), tok))


@bp.route("/finance/api/supplier-msg/next")
def api_next():
    con = _db()
    if not _token_ok(con):
        _s452_phone_seen(con, 401)                       # S452: the setup page says when the phone last asked, and the answer
        return jsonify(ok=False, error="bad_token"), 401
    _s452_phone_seen(con, 200)
    ensure(con)
    cut = (_now() - dt.timedelta(minutes=RETRY_MIN)).isoformat()
    gap = (_now() - dt.timedelta(minutes=_s454_gap(con))).isoformat()      # S454 (F-702): the owner's test only, since S605
    r = con.execute("SELECT id, to_number, body FROM supplier_msg WHERE to_number IS NOT NULL AND attempts<? AND "
                    "((status='queued' AND (handed_at IS NULL OR (kind='test' AND handed_at<=?))) OR "      # S605 (F-960): handed ONCE -- never again
                    "(status='failed' AND kind NOT IN ('order','test','check') AND (handed_at IS NULL OR handed_at<=?) AND (last_try_at IS NULL OR last_try_at<=?))) "
                    "ORDER BY (kind='test') DESC, queued_at, id LIMIT 1",          # S454 P1C: the owner's test first; a failed test is never retried
                    (MAX_ATTEMPTS, gap, gap, cut)).fetchone()                       # a payment message the phone said it could not send: after RETRY_MIN
    if not r:
        return jsonify({}), 200
    con.execute("UPDATE supplier_msg SET handed_at=? WHERE id=?", (_iso(), r["id"]))
    con.commit()
    return jsonify(id=r["id"], to=r["to_number"], text=r["body"]), 200


@bp.route("/finance/api/supplier-msg/done", methods=["POST"])
def api_done():
    con = _db()
    if not _token_ok(con):
        _s452_phone_seen(con, 401)                       # S452
        return jsonify(ok=False, error="bad_token"), 401
    _s452_phone_seen(con, 200)
    ensure(con)
    js = request.get_json(silent=True) or {}
    try:
        mid = int(js.get("id") or request.values.get("id") or 0)
    except (TypeError, ValueError):
        mid = 0
    okv = js.get("ok") if "ok" in js else request.values.get("ok")
    ok = str(okv).lower() in ("1", "true", "yes", "ok")
    errt = str(js.get("error") or request.values.get("error") or "")[:200]
    r = con.execute("SELECT id, status FROM supplier_msg WHERE id=?", (mid,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_message"), 404
    if ok:
        con.execute("UPDATE supplier_msg SET status='sent', sent_at=?, sent_by='reception-phone', attempts=attempts+1, last_try_at=? WHERE id=?", (_iso(), _iso(), mid))
    else:
        con.execute("UPDATE supplier_msg SET status='failed', attempts=attempts+1, last_error=?, last_try_at=? WHERE id=?", (errt or "phone said no", _iso(), mid))
    con.commit()
    _s898_done_seen(con)                                 # S898: the phone's 'sent' report arrived -- when, for the silent-phone line
    _s454_done(con, mid, ok, errt)                       # S454: an order message sent makes its supplier ORDERED; one failed is withdrawn
    return jsonify(ok=True, id=mid, status=("sent" if ok else "failed")), 200


# ---------------------------------------------------------------- the pay-page card (owner English / staff Hindi)
def _chip_text(st, owner):
    s = st["status"]
    ev = st["event"] or {}
    if s == "confirmed":
        return ("ok", ("Confirmed by bank %s" if owner else "Bank ne confirm kiya %s") % _dmy((st["bank_line"] or {}).get("date")))
    if s == "mismatch":
        d = st["diff_p"]
        if d is None:
            return ("bad", "Statement covers the date — no NEFT debit found" if owner else "Statement mein NEFT nahi mila")
        return ("bad", ("Bank shows %s, sheet %s — differs by %s" % (_inr((st["bank_line"] or {}).get("amount_p")), _inr(ev.get("amount_p")), _inr(abs(d)))) if owner
                else ("Bank mein %s, sheet mein %s — %s ka farak" % (_inr((st["bank_line"] or {}).get("amount_p")), _inr(ev.get("amount_p")), _inr(abs(d)))))
    if s in ("awaiting", "nostmt"):
        return ("warn", ("Sent %s — awaiting bank statement" if owner else "Bheja %s — bank statement ka intezaar") % _dmy(ev.get("date")))
    return ("", "")


def chip(st, g):
    """The amber / green / red chip beside a NEFT vendor on the sheet; '' when nothing has been recorded."""
    if not st or not st.get("event") or g.get("route") != "NEFT":
        return ""
    cls, text = _chip_text(st, True)
    return ' <span class="chip %s">%s</span>' % (cls, _esc(text)) if text else ""


def pay_card(con, u, month, prefix, final, groups):
    st = state(con, month)
    owner, sender = _is_owner(u), _is_sender(con, u)
    saved = request.args.get("saved") or ""
    h = ['<div class="card" id="neftcard_s407">']
    if saved in ("neft", "undo", "msg"):
        h.append('<div class="ok" style="background:#e9f6e9;border-left:6px solid #2f6b45;padding:10px 14px;margin-bottom:10px;font-size:18px"><b>%s</b></div>'
                 % {"neft": "Saved — NEFT recorded; the suppliers' messages are queued for the reception phone.",
                    "undo": "Undone — the NEFT entry is withdrawn and its unsent messages cancelled.",
                    "msg": "Sent — marked with your name and the time."}[saved] if owner else
                 {"neft": "Ho gaya.", "undo": "Wapas ho gaya.", "msg": "Bhej diya — aapke naam se likh liya."}[saved])
    h.append('<h2>%s</h2>' % ("NEFT — done, told, confirmed" if owner else "NEFT — bank aur supplier"))
    ev = st["event"]
    cls, text = _chip_text(st, owner)
    if ev:
        h.append('<div style="margin:6px 0"><span class="chip %s" style="font-size:14px">%s</span> <span class="muted">%s %s by %s%s</span></div>'
                 % (cls, _esc(text), "recorded" if owner else "likha", _esc(_dmy(ev["created_at"])), _esc(ev.get("created_by") or ev.get("source")),
                    (" · UTR %s" % _esc(ev["utr"])) if ev.get("utr") else ""))
    elif owner:
        if final and st["neft_p"] > 0:
            h.append('<div class="muted">The NEFT portion of this sheet is <b>%s</b> (%d suppliers). When the bank SMS has come, record it here — '
                     'every NEFT line turns amber until the Yes Bank statement confirms it, and the suppliers are told by WhatsApp from the reception phone.</div>'
                     '<div class="noprint" style="margin-top:8px"><label>Date <input class="pin" id="nd_date" type="date" value="%s" style="width:150px"></label> '
                     '<label>UTR (optional) <input class="pin" id="nd_utr" style="width:180px;text-align:left" placeholder="from the SMS"></label> '
                     '<button class="p" onclick="neftDone407()">NEFT done (bank SMS received)</button></div>'
                     % (_inr(st["neft_p"]), len(st["vendors"]), _now().date().isoformat()))
        elif not final:
            h.append('<div class="muted">Recorded once the month is finalised.</div>')
        else:
            h.append('<div class="muted">Nothing is payable by NEFT this month.</div>')
    else:
        h.append('<div class="muted">%s</div>' % ("Doctor sahab NEFT hone par yahan likhenge; tab supplier ko message jaayega." if final
                                                    else "Mahina lock hone ke baad."))
    if ev and owner and ev.get("source") == "sms" and not ev.get("confirmed_by"):       # S638 (F-1014): an SMS-seen NEFT, unconfirmed
        h.append('<div class="noprint" style="margin:8px 0"><div class="muted">The bank\'s SMS showed this NEFT on %s; it is not confirmed yet, so the '
                 'suppliers have not been told.</div><button class="p" onclick="neftDone407()">Seen in bank SMS — confirm and tell the suppliers</button></div>'
                 % _esc(_dmy(ev.get("date") or ev.get("created_at"))))
    if ev and owner and st["can_undo"]:
        h.append('<div class="noprint muted" style="margin:6px 0"><button class="sm" onclick="neftUndo407()">Undo (within 24 h)</button></div>')
    msgs = st["messages"]
    if msgs:
        rows = []
        for m in msgs:
            when = m["sent_at"] or m["queued_at"]
            if m["status"] == "sent":
                stt = '<span class="ok">%s</span> <span class="muted">%s · %s</span>' % ("told" if owner else "bata diya", _esc(_dmy(when)), _esc(m["sent_by"] or ""))
            elif m["status"] == "skipped":
                stt = '<span class="warn">%s</span> <span class="muted">%s%s</span>' % ("not sent" if owner else "nahi bheja", _esc(m["last_error"] or ""),
                                                                                       (' — <a href="%s/page/book">add the number</a>' % prefix) if (m["last_error"] or "").startswith("number") else "")
            elif m["pending"]:
                stt = ('<span class="bad">%s</span> ' % ("Pending" if owner else "Pending — baaki")) + (
                    '<button class="sm" onclick="msgSend407(%d,this)"%s>Bhejo</button>' % (m["id"], _s664_handed(m, owner)) if sender else
                    '<span class="muted">(Shavez / doctor sahab bhejenge)</span>')
            else:
                stt = '<span class="muted">%s</span>' % ("queued for the reception phone" if owner else "reception phone bhejega")
            rows.append('<tr><td>%s%s</td><td>%s</td></tr>' % (_esc(m["vendor"]), ' <span class="chip">cheque</span>' if m["kind"] == "cheque" else "", stt))
        h.append('<div class="scroll"><table><tr><th>%s</th><th>%s</th></tr>%s</table></div>'
                 % ("Supplier" if owner else "Supplier", "Message" if owner else "Message", "".join(rows)))
        h.append('<div class="muted">%d told · %d waiting · %d not sent%s</div>'
                 % (st["counts"]["sent"], st["counts"]["queued"], st["counts"]["skipped"],
                    (' · <a href="%s/page/phone-setup">the reception phone\'s setup</a>' % prefix) if owner else ""))   # S452 (F-687): the setup page is the owner's
    h.append("""<script>
function neftDone407(){var d=document.getElementById('nd_date'),u=document.getElementById('nd_utr');
 fetch(P+'/api/neft-done',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({month:'%s',date:d?d.value:'',utr:u?u.value:''})})
 .then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error||'could not save');return;}
 if(j.already){alert('Already recorded for this month.');return;} location.href=location.pathname+'?saved=neft#neftcard_s407';})
 .catch(function(){alert('could not save just now');});}
function neftUndo407(){if(!confirm('Undo the NEFT entry for this month? Unsent supplier messages are cancelled.'))return;
 fetch(P+'/api/neft-undo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({month:'%s'})})
 .then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error||'could not undo');return;} location.href=location.pathname+'?saved=undo#neftcard_s407';})
 .catch(function(){alert('could not undo just now');});}
function msgSend407(id,b){var t=b&&b.getAttribute('data-handed');if(t&&!confirm(t))return;fetch(P+'/api/supplier-msg/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})})
 .then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error||'could not send');return;}
 if(j.wa_url){window.open(j.wa_url,'_blank');} location.href=location.pathname+'?saved=msg#neftcard_s407';})
 .catch(function(){alert('could not send just now');});}
</script></div>""" % (month, month))
    return "".join(h)


# ---------------------------------------------------------------- Amir's card, Needs you
def amir_card(con):
    """S452 (the owner, 02-Oct): one line per month whose NEFT is confirmed, and the paid sheet as a PDF -- nothing before that, no
    supplier names, no 'baaki'. Shavez's and the owner's pages keep the list (pay_card)."""
    return s452_amir_card(con)


def _amir_card_s407(con):
    """S407's card -- 'NEFT <Month>: bheja <date> — bank se confirm baaki / ho gaya' + the suppliers told (bata diya). Kept for the
    record; Amir no longer sees it (S452)."""
    ensure(con)
    since = (_now() - dt.timedelta(days=45)).isoformat()
    evs = [dict(r) for r in con.execute("SELECT * FROM purchase_neft_event WHERE kind<>'rejected' AND created_at>=? ORDER BY id DESC LIMIT 3", (since,))]
    if not evs:
        return ""
    out = []
    for ev in evs:
        bank, line, diff = bank_check(con, ev)
        if bank == "confirmed":
            word = "bank se confirm <b class=good>ho gaya</b> (%s)" % _esc(_dmy(line["txn_date"]) if line else "")
        elif bank == "mismatch":
            word = "<b class=bad>bank mein farak</b>%s" % ((" (%s)" % _esc(_inr(abs(diff)))) if diff is not None else "")
        else:
            word = "bank se confirm <b>baaki</b>"
        msgs = [m for m in messages(con, ev["month"]) if m["kind"] == "neft"]
        told = "".join("<div class=line>%s: <b>%s</b></div>" % (_esc(m["vendor"]), "bata diya &#10003;" if m["status"] == "sent" else ("number nahi" if m["status"] == "skipped" else "baaki"))
                       for m in msgs)
        out.append("<div class=card><h2>NEFT %s</h2><p>bheja %s — %s</p>%s</div>"
                   % (_esc(_month_name(ev["month"])), _esc(_dmy(ev.get("sms_date") or ev["created_at"])), word, told))
    return "".join(out)


def needs_you_lines(con):
    ensure(con)
    lines = []
    p = pending(con)
    if p:
        lines.append(dict(cls="warn", target="bank", text="%d supplier message%s unsent (%d min or more)" % (len(p), "" if len(p) == 1 else "s", PENDING_MIN)))
    sil = s898_silent_line(con)                          # S898: the phone takes messages but its 'sent' reports stopped
    if sil:
        lines.append(sil)
    for ev in [dict(r) for r in con.execute("SELECT * FROM purchase_neft_event WHERE kind<>'rejected' AND bank_line_id IS NULL ORDER BY id DESC LIMIT 6")]:
        bank, line, diff = bank_check(con, ev)
        if bank == "mismatch":
            if diff is None:
                lines.append(dict(cls="bad", target="bank", text="NEFT of %s: the statement covers %s but shows no NEFT debit" % (_month_name(ev["month"]), _dmy(ev.get("sms_date")))))
            else:
                lines.append(dict(cls="bad", target="bank", text="NEFT of %s: bank shows %s, sheet %s — differs by %s"
                                  % (_month_name(ev["month"]), _inr(line["withdrawal_p"]), _inr(ev["amount_p"]), _inr(abs(diff)))))
    return lines


# ---------------------------------------------------------------- the setup page (staff, Hindi)
SETUP_CSS = ("body{margin:0;padding:14px;background:#dfe5e9;color:#14181c;font:17px/1.55 'Segoe UI',system-ui,sans-serif}"
             "h1{font-size:22px;color:#14456e;margin:0 0 12px}h2{font-size:19px;color:#14456e;margin:0 0 8px}"
             ".card{background:#fffdf7;border:2px solid #8a9aa6;border-radius:10px;padding:14px;margin:0 0 14px}"
             ".mut{color:#3c464e;font-size:15px}code{background:#eef2f5;padding:1px 5px;border-radius:4px;word-break:break-all}"
             ".key{font:18px monospace;background:#fffbe6;border:2px dashed #14456e;padding:12px;word-break:break-all;user-select:all}"
             "ol li{margin:6px 0}.warn{background:#fdf3d7;border-left:6px solid #8a6100;padding:8px 12px}")


# S914_PHONE_SETUP_PAGE (21-Nov-2026, D1029): the steps as the phone now stands -- screen lock None, the macro with NO
#   constraints, Screen On + Wait 2 s after JSON Parse, the POST unconstrained (F-1516); the 10:00 daily check (S909) proves it.
@bp.route("/finance/purchase/page/phone-setup")
def page_phone_setup():
    u, err = _person("checker")                          # S452 (F-687): the owner and a checker -- a maker / viewer gets the gate's refusal
    if err:
        return err
    con = _db()
    ensure(con)
    tok = _setting(con, "supplier_msg.phone_token", "")
    key_html = ('<p class="key">%s</p>' % _esc(tok)) if tok else '<div class="warn">Token abhi bana nahi.</div>'
    if tok:
        _s452_token_shown(con, u)                         # S452: every showing audited (who, when); "shown once" retired
    body = _s452_phone_state_line(con) + """<h1>Reception phone — supplier message ka setup (MacroDroid)</h1>
<div class="card"><h2>Yeh kya hai</h2><p>Doctor sahab jab NEFT "done" karte hain, server har supplier ke liye ek WhatsApp message tayyar rakhta hai
(poora account number aur IFSC ke saath). Reception ka phone har minute (screen band ho tab bhi) server se poochta hai "koi message hai?", milta hai to
WhatsApp mein khol kar bhej deta hai, aur server ko bata deta hai "ho gaya". Aapko kuch type nahi karna.</p>
<p>S454: supplier ko <b>medicine ka order</b> bhi isi raste se jaata hai (Purchase orders par "Sab ko WhatsApp bhejo"). Phone ek minute mein ek message bhejta hai.</p>
<div class="warn">Yeh ek WhatsApp ko automation se chalata hai. WhatsApp ki screen badle to macro mein chhota sa sudhaar lag sakta hai.
Neeche wala <b>Bhejo</b> button (Vendor payments page par, 30 minute baad) hamesha kaam karta hai.</div></div>
<div class="card"><h2>Har din apne aap jaanch</h2>
<p>Har subah <b>10:00 baje</b> server is phone se clinic ke apne WhatsApp par ek jaanch message bhejwata hai. Message clinic inbox mein pahunch gaya to setup sahi hai. Na pahunche to server khud dhoondta hai ki kahan ruka, aur Doctor sahab ko batata hai. Aapko kuch nahi karna.</p></div>
<div class="card"><h2>Phone ki settings (ek baar)</h2>
<ul>
<li><b>Screen lock: None</b> (Settings &rarr; Lock screen &rarr; Screen lock type &rarr; None). Pattern, PIN ya password nahi &mdash; warna andhere phone par WhatsApp nahi khulta.</li>
<li><b>Phone par sirf ek WhatsApp:</b> <b>WhatsApp Business</b>. Uske saath doosra (bina register kiya) WhatsApp Messenger pada ho to link ek box par ruk jaata hai aur kuch nahi jaata &mdash; use hata dijiye. Phone WhatsApp mein login rahe.</li>
<li>MacroDroid &rarr; Battery &rarr; <b>Unrestricted</b>; Accessibility &rarr; MacroDroid <b>on</b>; <i>Display over other apps</i> <b>on</b>.</li>
</ul></div>
<div class="card"><h2>Macro: <i>Sanjeevni Whatsapp</i> (MacroDroid)</h2>
<p><b>Trigger:</b> <i>Regular Interval</i> &middot; har <b>1 minute</b>. Koi loop nahi.</p>
<p><b>Constraints: koi nahi</b> &mdash; na macro par, na kisi action par (na <i>Device Unlocked</i>, na <i>Screen On</i>, na <i>App foreground</i>). Phone andhera ho tab bhi har minute poochta hai; screen macro khud jagata hai.</p>
<p><b>Actions, isi kram mein:</b></p>
<ol>
<li><b>HTTP Request</b> &middot; GET &middot; URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/next</code> &middot; Header ka naam bilkul <code>X-Phone-Token</code> &mdash; beech mein ya aakhir mein koi space nahi (keyboard khud ek space jod deta hai, tab request phone se nikalti hi nahi) &middot; value = neeche wala token &middot; Response ko variable <code>resp</code> mein save karein.</li>
<li><b>If</b> <code>resp</code> contains <code>text</code>:</li>
<li>&nbsp;&nbsp;<b>JSON Parse</b>: <code>resp</code> ko dictionary <code>msg</code> mein.</li>
<li>&nbsp;&nbsp;<b>Screen On/Off</b> &rarr; <b>Screen On</b>.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 2 second.</li>
<li>&nbsp;&nbsp;<b>Open Website</b>: address haath se type kijiye, chat se kabhi paste nahi: <code>https://wa.me/{lv=msg[to]}?text={lv=msg[text]}</code> (<code>lv</code> mein chhota <b>L</b> hai, ank 1 nahi) &middot; <i>URL encode parameters</i> par tick.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 6 second.</li>
<li>&nbsp;&nbsp;<b>UI Interaction</b> &rarr; <i>Click</i> &rarr; text <code>Send</code>.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 3 second.</li>
<li>&nbsp;&nbsp;<b>HTTP Request</b> &middot; POST &middot; URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/done</code> &middot; content type <code>application/json</code> &middot; Body: <code>{"id": {lv=msg[id]}, "ok": true}</code>. Yeh request <b>pehli request ko copy karke</b> banaiye &mdash; tab key uske saath aa jaati hai. <b>Is action par koi constraint nahi.</b></li>
<li><b>End If</b>.</li>
</ol>
<p><b>Pehli baar:</b> macro ko ek baar <i>Test actions</i> se chalaiye aur phone ki screen dekhte rahiye. Bina dekhe dobara mat chalaiye.</p>
<p class="mut">Ek message server ek hi baar deta hai. Agar Send nahi dab paaya: POST body <code>{"id": {lv=msg[id]}, "ok": false, "error": "send not clicked"}</code> bhejein &mdash; server 30 minute baad phir se dega, aur 30 minute baad Vendor payments page par <b>Bhejo</b> button dikhne lagega.</p>
<p class="mut">Poora macro, key ke saath, ek file mein Doctor sahab ke <i>Clinic PCs</i> page par hai (sirf unke liye).</p></div>
<div class="card"><h2>Token (sirf is phone ke liye)</h2>%s<p class="mut">Yeh token kisi ko WhatsApp / chat par na bhejein.</p></div>
<p class="mut"><a href="/finance/purchase/page/pay">← Vendor payments</a> · <a href="/portal">Portal</a></p>""" % key_html
    html = ('<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Reception phone setup</title><style>%s</style></head><body>%s</body></html>' % (SETUP_CSS, body))
    return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}


# ==========================================================================================================================================
# S452_AMIR_PANEL_FIXES (02-Oct-2026, F-687 and the owner's rulings of 02-Oct evening) -- the reception phone's key; NEFT for Amir.
#   * The setup page is the owner's and a checker's: a maker or viewer gets the login gate's refusal. The key shows to them EVERY time,
#     each showing audited (purchase_audit 'phone_token_shown': who, when). "Shown once" is retired: it handed the key to whoever opened
#     the page FIRST, and the page admitted every staff login (on 02-Oct 19:46 IST the first opener was Amir's login).
#   * s452_new_token(con): a new key, made by the install; the old one answers 401 from that moment. The key is never printed or logged.
#   * The page's first line, in Hindi: when the phone last asked the queue door, with which answer (200 / 401), how many messages wait.
#   * NEFT for Amir. A month's NEFT is CONFIRMED when the bank's SMS for it has been read (purchase_neft_event source 'sms', S405) or a
#     Yes Bank statement line confirms it (bank_line_id, S407) -- "bank ka kaam ho gaya, <dd-mm>" -- or when the owner has entered it
#     himself (source 'owner'; provisional counts) -- "payment <dd-mm> ko ho gaya (Doctor sahab ne darj kiya)". Before that nothing of the
#     month reaches him: no line, no sheet. After: one line and the paid NEFT sheet as a PDF (NEFT_paid_<yyyy-mm>.pdf; the rows of
#     packs.build_neft_paid_sheet, S408, and their total). No supplier names, no "baaki". Shavez's and the owner's pages keep theirs.
# ==========================================================================================================================================
S452_PHONE_KEY = "supplier_msg.phone_last"
S452_ACCESS_LOG = os.environ.get("FINANCE_ACCESS_LOG", "/root/finance/access.log")


def s452_new_token(con):
    """A new reception-phone key (the install's data step). Returns the key's LENGTH only."""
    ensure(con)
    tok = secrets.token_hex(24)
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                ("supplier_msg.phone_token", tok, "S452 (F-687) -- the reception phone's key, renewed at S452 because the old one was readable by "
                 "a staff login; shown to the owner / a checker on the setup page, every showing audited"))
    con.execute("UPDATE setting SET note=? WHERE key='supplier_msg.token_shown'",
                ("S452 -- retired: the key is shown to the owner / a checker each time, audited (the once-rule gave it to the first opener)",))
    try:
        _pa()._audit(con, "S452 install", "phone_token_renewed", "phone-setup", dict(kit="S452_AMIR_PANEL_FIXES", length=len(tok)))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return len(tok)


def _s452_phone_seen(con, code):
    """The queue door was asked: when, and with which answer (one settings row; rewritten at most once a minute per answer)."""
    try:
        old = _setting(con, S452_PHONE_KEY, "")
        at, _sp, c = str(old).partition(" ")
        if at and c == str(code) and _age_min(at) < 1:
            return
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (S452_PHONE_KEY, "%s %d" % (_iso(), int(code)), "S452 -- when the reception phone last asked the queue door, and the answer"))
        con.commit()
    except Exception:                                          # noqa: BLE001 -- the phone's door never fails for its own record
        pass


def _s452_phone_from_log():
    """Before S452 nothing recorded the phone's asks: the newest queue-door line of the app's access log -> (iso, code) or ('', '')."""
    try:
        with open(S452_ACCESS_LOG, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 4 * 1024 * 1024))
            tail = fh.read().decode("utf-8", "replace")
    except (IOError, OSError):
        return "", ""
    for ln in reversed(tail.splitlines()):
        if "/finance/api/supplier-msg/next" not in ln:
            continue
        m = re.search(r"\[(\d{2})/(\w{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})[^\]]*\]\s+\"[^\"]*\"\s+(\d{3})", ln)
        if not m:
            continue
        try:
            t = dt.datetime.strptime("%s %s %s %s:%s:%s" % m.groups()[:6], "%d %b %Y %H:%M:%S")
        except ValueError:
            continue
        return t.isoformat(), m.group(7)
    return "", ""


def _s452_phone_state_line(con):
    """The setup page's first line (Hindi): the phone's last ask, its answer, the messages waiting."""
    at, _sp, code = str(_setting(con, S452_PHONE_KEY, "")).partition(" ")
    if not at:
        at, code = _s452_phone_from_log()
    try:
        wait = int(con.execute("SELECT COUNT(*) FROM supplier_msg WHERE status IN ('queued','failed') AND to_number IS NOT NULL AND kind IN ('neft','cheque')").fetchone()[0])   # S454
    except Exception:                                          # noqa: BLE001
        wait = 0
    if at:
        try:
            when = dt.datetime.fromisoformat(at).strftime("%d-%m-%Y %H:%M")
        except ValueError:
            when = at
        ans = {"200": "200 (theek)", "401": "401 (galat key)"}.get(code, code or "?")
        txt = "Phone ne aakhri baar %s ko poocha — jawab %s · %d message intezaar mein" % (when, ans, wait)
    else:
        txt = "Phone ne abhi tak nahi poocha · %d message intezaar mein" % wait
    return '<div class="warn" id="s452phone" style="margin:0 0 12px"><b>%s</b></div>' % _esc(txt)


def _s452_token_shown(con, u):
    try:
        _pa()._audit(con, _who(u), "phone_token_shown", "phone-setup", dict(kit="S452"))
        con.commit()
    except Exception:                                          # noqa: BLE001
        pass


# ---------------------------------------------------------------- NEFT for Amir
def _s452_ddmm(iso):
    s = str(iso or "")[:10]
    return ("%s-%s" % (s[8:10], s[5:7])) if len(s) == 10 else s


def s452_neft_confirmed(con, month):
    """None until the month's NEFT is confirmed; then {month, kind 'bank' | 'owner', date}. Reads S405's / S407's rows only."""
    if not _good_month(month):
        return None
    ensure(con)
    ev = live_event(con, month)
    if not ev:
        return None
    if ev.get("source") == "sms":                              # S405: the bank's SMS, read by the system
        return dict(month=month, kind="bank", date=str(ev.get("sms_date") or ev.get("created_at") or "")[:10], event=ev["id"])
    try:
        bank, line, _d = bank_check(con, ev)                   # S407: a Yes Bank statement line confirms it
    except Exception:                                          # noqa: BLE001
        bank, line = None, None
    if bank == "confirmed" and line:
        return dict(month=month, kind="bank", date=str(line.get("txn_date") or "")[:10], event=ev["id"])
    if ev.get("source") == "owner":                            # S407: the owner's own "NEFT done" (provisional counts)
        return dict(month=month, kind="owner", date=str(ev.get("sms_date") or ev.get("created_at") or "")[:10], event=ev["id"])
    return None


def s452_amir_line(conf):
    m = _month_name(conf["month"])
    if conf["kind"] == "bank":
        return "NEFT %s — bank ka kaam ho gaya, %s" % (m, _s452_ddmm(conf["date"]))
    return "NEFT %s — payment %s ko ho gaya (Doctor sahab ne darj kiya)" % (m, _s452_ddmm(conf["date"]))


def s452_amir_card(con):
    """Amir's NEFT block, every step: per month with a live NEFT event of the last 45 days, one line and the PDF -- once confirmed."""
    ensure(con)
    since = (_now() - dt.timedelta(days=45)).isoformat()
    months = [r[0] for r in con.execute("SELECT month FROM purchase_neft_event WHERE kind<>'rejected' AND created_at>=? GROUP BY month "
                                        "ORDER BY month DESC LIMIT 3", (since,))]
    out = []
    for m in months:
        c = s452_neft_confirmed(con, m)
        if not c:
            continue
        out.append("<div class=line><span class=big>%s</span><p><a class='btn plain' href='/finance/amir/pack/%s/neft'>Paid NEFT sheet (PDF)</a></p></div>"
                   % (_esc(s452_amir_line(c)), _esc(m)))
    if not out:
        return ""
    return "<div class=card id=s452neft><h2>NEFT</h2>%s</div>" % "".join(out)


def s452_neft_rows(con, month):
    """The paid NEFT sheet's rows, exactly as packs.build_neft_paid_sheet (S408) writes them, with the payable in paise."""
    pa = _pa()
    _s, groups = pa._pay_rows(con, month)
    st = state(con, month)
    ev = st.get("event") or {}
    bank = st.get("bank_line") or {}
    rows = []
    for g in groups:
        paid = "paid" if (g["route"] == "NEFT" and ev) else ("cheque" if g["route"] != "NEFT" else "not yet")
        rows.append((g["name"], int(g["payable_p"]), g["route"], paid, _dmy(ev.get("date")) if (g["route"] == "NEFT" and ev) else "",
                     _dmy(bank.get("date")) if (g["route"] == "NEFT" and bank) else ""))
    return rows


def _s452_rs(p):
    """Paise -> '1,23,456.00' (Indian grouping)."""
    p = int(p or 0)
    neg, p = p < 0, abs(p)
    whole, paise = divmod(p, 100)
    v = str(whole)
    if len(v) > 3:
        head, tail = v[:-3], v[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        v = ",".join(parts) + "," + tail
    return ("-" if neg else "") + v + ".%02d" % paise


def s452_neft_pdf(con, month):
    """The paid NEFT sheet as an A4 PDF -- the same rows as the S408 sheet, then the total; Amir cannot change a PDF."""
    import clinic_day_pdf as cdp                               # noqa: PLC0415 -- the estate's dependency-free PDF writer
    rows = s452_neft_rows(con, month)
    p = cdp._PDF("NEFT paid %s" % month)
    xs = (40, 330, 345, 395, 445, 510)
    head = ("Vendor", "Payable Rs", "Route", "Paid", "NEFT date", "Bank date")

    def page(first):
        p.new_page()
        y = 800
        if first:
            p.text(40, y, "Sanjeevni Medicos -- paid NEFT sheet -- %s" % _month_name(month), 13, bold=True)
            y -= 16
            p.text(40, y, "Printed %s. The same rows as the paid NEFT sheet of the vendor payments." % _now().strftime("%d-%m-%Y %H:%M"), 8.5, gray=0.35)
            y -= 20
        for i, h in enumerate(head):
            p.text(xs[i], y, h, 9, bold=True, align=("r" if i == 1 else "l"))
        p.line(40, y - 4, 555, y - 4, 0.6)
        return y - 17

    y = page(True)
    tot = neft = 0
    for r in rows:
        if y < 70:
            y = page(False)
        p.text(xs[0], y, cdp._fit(str(r[0]), 9, 280), 9)
        p.text(xs[1], y, _s452_rs(r[1]), 9, align="r")
        for i in (2, 3, 4, 5):
            p.text(xs[i], y, str(r[i] or ""), 9)
        tot += r[1]
        neft += r[1] if r[2] == "NEFT" else 0
        y -= 14
    if y < 90:
        y = page(False)
    p.line(40, y + 8, 555, y + 8, 0.6)
    p.text(xs[0], y - 4, "Total (%d vendors)" % len(rows), 9.5, bold=True)
    p.text(xs[1], y - 4, _s452_rs(tot), 9.5, bold=True, align="r")
    p.text(xs[0], y - 20, "of which by NEFT", 9)
    p.text(xs[1], y - 20, _s452_rs(neft), 9, align="r")
    return p.build()


def s452_amir_neft_pdf(con, month):
    """Amir's NEFT route (/finance/amir/pack/<month>/neft, packs.py): the PDF once the month's NEFT is confirmed, else the login gate's
    refusal. He gets no .xlsx by this address."""
    from flask import Response                                 # noqa: PLC0415
    if not _good_month(month):
        return "bad month", 400
    if not s452_neft_confirmed(con, month):
        return jsonify(ok=False, error="not_permitted", message="Your login is not permitted to do this."), 403
    return Response(s452_neft_pdf(con, month), mimetype="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="NEFT_paid_%s.pdf"' % month, "Cache-Control": "no-store"})
# ---- S452_AMIR_PANEL_FIXES end ----------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, D666 / F-702): THE ORDER MESSAGES RIDE THE SAME QUEUE, AS THEIR OWN KIND.
#   * kind 'order' (ref = the purchase order): queued by order_sheet when reception taps "Sab ko WhatsApp bhejo". Every reader that counts
#     payment messages counts only the payment kinds (neft, cheque): the pay card, its pending line, the owner's line, the phone's state line.
#   * F-702: a message handed to the phone is not handed out again for supplier_msg.handout_gap_min minutes (handed_at) -- this protects the
#     payment notices too. The phone is told on its setup page to ask again at once after each message, until the answer is empty.
#     S605 (F-960): a message once handed is NEVER handed again (the owner's test apart, after the gap); a payment message the phone said it
#     could not send is retried after RETRY_MIN; an order message handed and never confirmed is the owner's line (order_sheet.withdraw_late).
#   * The phone's "sent" on an order message makes its supplier ORDERED; "could not send" withdraws it at once (order_sheet.on_message_done).
# ==========================================================================================================================================
def _s454_cols(con):
    try:
        have = {r[1] for r in con.execute("PRAGMA table_info(supplier_msg)")}
        if "handed_at" not in have:
            con.execute("ALTER TABLE supplier_msg ADD COLUMN handed_at TEXT")
    except Exception:                                          # noqa: BLE001
        pass


def _s454_gap(con):
    try:
        return max(1, int(str(_setting(con, "supplier_msg.handout_gap_min", "10")).strip() or 10))
    except (TypeError, ValueError):
        return 10


def _s454_done(con, mid, ok, err):
    try:
        import order_sheet                                     # noqa: PLC0415
        order_sheet.on_message_done(con, mid, ok, err)
    except Exception:                                          # noqa: BLE001 -- the phone's door never fails for the order screen
        pass


# ==========================================================================================================================================
# S454_BILL_REGISTER part 1C (03-Oct-2026, S454 17.7-17.10): THE OWNER'S "RECEPTION PHONE" CARD AND ITS TEST MESSAGE.
#   * kind 'test' (month 'test', vendor 'Test message'): one message the owner queues to his own saved number (setting supplier_msg.test_to,
#     shown masked to its last four, never written to a log, an audit detail or a page in full). Two lines, to prove the line break and the
#     encoding. It is handed out FIRST (the owner is testing now), once per gap (F-702), and a failed test is never retried. It is counted
#     nowhere else: every payment reader reads kinds neft/cheque, every order reader kind 'order'.
#   * s454_card_facts(con): when the phone last asked, the order and payment messages waiting, the masked number, the last test's times.
#     The key is never in it.
# ==========================================================================================================================================
S454_TEST_KEY = "supplier_msg.test_to"


def s454_test_to(con):
    return re.sub(r"\D", "", str(_setting(con, S454_TEST_KEY, "") or ""))


def s454_mask(d):
    d = re.sub(r"\D", "", str(d or ""))
    return ("•" * max(0, len(d) - 4) + d[-4:]) if d else ""


def s454_save_test_to(con, who, raw):
    """(ok, message): the owner's own number for test messages; the number never reaches the audit."""
    d = _pa()._wa_digits(raw)
    if not d:
        return False, "Not a phone number (10 digits, or with 91 in front)."
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (S454_TEST_KEY, d, "S454 17.7 -- the owner's own number for the reception phone's test message (never printed in full)"))
    try:
        _pa()._audit(con, who, "s454_test_number_saved", "reception-phone", dict(kit="S454 P1C", digits=len(d)))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return True, "Saved: %s" % s454_mask(d)


def s454_test_body(at=None):
    at = at or _now()
    return "Sanjeevni test · %s\nYeh sirf jaanch hai — ₹ 1,234.50" % at.strftime("%d-%m %H:%M")


def s454_queue_test(con, who):
    """(ok, message_id or the reason) -- one message of kind 'test' to the saved number."""
    ensure(con)
    to = s454_test_to(con)
    if not to:
        return False, "No test number saved."
    ref = int(con.execute("SELECT COALESCE(MAX(ref), 0) + 1 FROM supplier_msg WHERE kind='test'").fetchone()[0])
    cur = con.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, to_number, body, status, queued_at) VALUES (?,?,?,?,?,?,?,?,?)",
                      ("test", "TEST", "Test message", "test", ref, to, s454_test_body(), "queued", _iso()))
    try:
        _pa()._audit(con, who, "s454_test_queued", "reception-phone", dict(kit="S454 P1C", message=cur.lastrowid))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return True, cur.lastrowid


def s454_card_facts(con):
    """The "Reception phone" card's facts (never the key, never a full number)."""
    ensure(con)
    at, _sp, code = str(_setting(con, S452_PHONE_KEY, "")).partition(" ")
    if not at:
        at, code = _s452_phone_from_log()

    def n(sql):
        try:
            return int(con.execute(sql).fetchone()[0])
        except Exception:                                      # noqa: BLE001
            return 0
    t = con.execute("SELECT id, status, queued_at, handed_at, sent_at, last_try_at, last_error FROM supplier_msg WHERE kind='test' ORDER BY id DESC LIMIT 1").fetchone()
    return dict(last_ask=at or "", code=code or "",
                orders_wait=n("SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND status IN ('queued','failed') AND to_number IS NOT NULL"),
                pay_wait=n("SELECT COUNT(*) FROM supplier_msg WHERE kind IN ('neft','cheque') AND status IN ('queued','failed') AND to_number IS NOT NULL"),
                test_to=s454_mask(s454_test_to(con)),
                last_test=(dict(id=t[0], status=t[1], queued_at=t[2], handed_at=t[3], sent_at=t[4], tried_at=t[5], error=t[6]) if t else None))
# ---- S454 part 1C end -------------------------------------------------------------------------------------------------------------------


# ---- S664 (F-702's residue, 26-Oct-2026): the backup Bhejo asks first when the message was already handed to the reception phone ----
def _s664_handed(m, owner):
    """' data-handed="..."' -- the question the Bhejo button asks before sending -- when the reception phone was handed this message; else ''."""
    h = m.get("handed_at") if hasattr(m, "get") else None
    if not h:
        return ""
    when = "%s %s" % (_dmy(h), str(h)[11:16])
    q = ("This message was handed to the reception phone on %s and may still go from there. Send it from here as well?" % when if owner
         else "Yeh message %s ko reception phone ko diya gaya tha — wahan se bhi ja sakta hai. Phir bhi yahan se bhejein?" % when)
    return ' data-handed="%s"' % _esc(q)


# ==========================================================================================================================================
# S898_PHONE_STUCK_AND_SILENT (20-Nov-2026, Sanjeevni session 490; the owner 17:35-17:49 IST). From 12-Nov the reception phone's MacroDroid
# sent every message but its last step ('sent' report, POST /done) was refused on the phone by an action constraint (App foreground,
# WhatsApp Business) -- no report reached the server for eight days, and the only sign was a line per order 'never confirmed'.
#   * the phone's last 'sent' report is kept (setting supplier_msg.phone_done_last);
#   * ONE Needs-you line when the phone took messages (15 min to 24 h ago, none reported) and its last report is older than them;
#   * the messages the phone took and never reported (payment notices, month-summary reminders) are listed on the owner's Reception
#     phone card with 'Send again' (handed to the phone once more) and 'Remove' (marked skipped, kept) -- per message and for all.
# Never the key, never a number or a body on any page or line.
# ==========================================================================================================================================
S898_DONE_KEY = "supplier_msg.phone_done_last"
S898_KINDS_HI = {"neft": "payment notice", "cheque": "payment notice", "summary": "month-summary reminder"}


def _s898_done_seen(con):
    try:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (S898_DONE_KEY, _iso(), "S898 -- when the reception phone's 'sent' report last reached the server"))
        con.commit()
    except Exception:                                          # noqa: BLE001 -- the door never fails for its own record
        pass


def _s898_ddmm(iso):
    s = str(iso or "")
    return ("%s-%s %s" % (s[8:10], s[5:7], s[11:16])) if len(s) >= 16 else (s or "never")


def s898_last_done(con):
    a = str(_setting(con, S898_DONE_KEY, "") or "")
    try:
        r = con.execute("SELECT MAX(sent_at) FROM supplier_msg WHERE sent_by='reception-phone'").fetchone()
        b = str(r[0] or "") if r else ""
    except Exception:                                          # noqa: BLE001
        b = ""
    return max(a, b)


def s898_silent_line(con):
    """One Needs-you line, or None: messages handed to the phone 15 min - 24 h ago, none reported since, and no report newer than them."""
    try:
        now = _now()
        lo, hi = (now - dt.timedelta(hours=24)).isoformat(), (now - dt.timedelta(minutes=15)).isoformat()
        r = con.execute("SELECT COUNT(*), MIN(handed_at), MAX(handed_at) FROM supplier_msg WHERE handed_at>=? AND handed_at<=? AND status<>'sent' AND kind<>'check'",
                        (lo, hi)).fetchone()
        n, first, last = int(r[0] or 0), r[1], r[2]
        if not n:
            return None
        done = s898_last_done(con)
        if done and done >= str(last):
            return None
        return dict(cls="bad", target="bank",
                    text="The reception phone took %d message%s since %s but its 'sent' report has not reached the server since %s -- the messages may "
                         "well have gone. On the reception phone: MacroDroid > System Log, the last step (HTTP Request POST) of 'Sanjeevni Whatsapp'."
                         % (n, "" if n == 1 else "s", _s898_ddmm(first), _s898_ddmm(done)))
    except Exception:                                          # noqa: BLE001
        return None


def s898_stuck(con, older_min=30):
    """The messages the phone took and never reported (not orders -- they settle themselves -- and not tests): id, kind, vendor, times."""
    cut = (_now() - dt.timedelta(minutes=older_min)).isoformat()
    rows = con.execute("SELECT id, kind, month, vendor, queued_at, handed_at FROM supplier_msg WHERE handed_at IS NOT NULL AND handed_at<=? "
                       "AND status IN ('queued','failed') AND kind NOT IN ('order','test','check') AND to_number IS NOT NULL AND attempts<? "
                       "ORDER BY handed_at, id", (cut, MAX_ATTEMPTS)).fetchall()
    return [dict(id=r[0], kind=r[1], what=S898_KINDS_HI.get(r[1], r[1]), month=r[2], vendor=str(r[3] or "").strip(),
                 queued=_s898_ddmm(r[4]), handed=_s898_ddmm(r[5])) for r in rows]


def _s898_ids(con, ids):
    ok = {x["id"] for x in s898_stuck(con, 0)}
    out = []
    for v in ids or []:
        try:
            i = int(v)
        except (TypeError, ValueError):
            continue
        if i in ok:
            out.append(i)
    return out


def s898_resend(con, who, ids):
    """Handed to the phone once more (its 'handed' mark cleared). Only messages still on the stuck list."""
    good = _s898_ids(con, ids)
    for i in good:
        con.execute("UPDATE supplier_msg SET handed_at=NULL, status='queued' WHERE id=? AND status IN ('queued','failed')", (i,))
    try:
        _pa()._audit(con, who, "s898_resend", "supplier_msg", dict(ids=good))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return len(good)


def s898_remove(con, who, ids):
    """Taken off every list (status skipped, the row kept with who and when). Only messages still on the stuck list."""
    good = _s898_ids(con, ids)
    for i in good:
        con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=? AND status IN ('queued','failed')",
                    ("removed by %s %s (S898): taken by the phone, never reported" % (str(who)[:40], _iso()[:16].replace("T", " ")), i))
    try:
        _pa()._audit(con, who, "s898_remove", "supplier_msg", dict(ids=good))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return len(good)



# ==========================================================================================================================================
# S909_PHONE_DAILY_CHECK (20-Nov-2026, Sanjeevni session 494; D1026). The reception phone's daily delivery check (phone_check.py) puts ONE
# message of kind 'check' on this road each morning. Here: a check message is handed to the phone once and never retried (the failed-retry
# rule leaves it out), it is never on the stuck list nor counted by the silent-phone line (phone_check says its own result), and the
# check's own Needs-you line joins this file's lines. Every other reader here reads named kinds only.
# ==========================================================================================================================================
_needs_you_lines_before_s909 = needs_you_lines


def needs_you_lines(con):                                      # noqa: F811 -- S909: + the daily phone check's line (fail-soft)
    lines = _needs_you_lines_before_s909(con)
    try:
        import phone_check                                     # noqa: PLC0415
        lines.extend(phone_check.needs_you_lines(con))
    except Exception:                                          # noqa: BLE001 -- the Hub never waits on the check
        pass
    return lines
# ---- S909 end ---------------------------------------------------------------------------------------------------------------------------
