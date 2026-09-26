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
        return pa._wa_digits(pa._phone_for(con, vendor))
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
    sql = "SELECT id, month, vendor_norm, vendor, kind, ref, status, queued_at, sent_at, sent_by, attempts, last_error, last_try_at FROM supplier_msg"
    args = ()
    if month:
        sql += " WHERE month=?"
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
        return jsonify(ok=False, error="bad_token"), 401
    ensure(con)
    cut = (_now() - dt.timedelta(minutes=RETRY_MIN)).isoformat()
    r = con.execute("SELECT id, to_number, body FROM supplier_msg WHERE to_number IS NOT NULL AND attempts<? AND "
                    "(status='queued' OR (status='failed' AND (last_try_at IS NULL OR last_try_at<=?))) ORDER BY queued_at, id LIMIT 1",
                    (MAX_ATTEMPTS, cut)).fetchone()
    if not r:
        return jsonify({}), 200
    return jsonify(id=r["id"], to=r["to_number"], text=r["body"]), 200


@bp.route("/finance/api/supplier-msg/done", methods=["POST"])
def api_done():
    con = _db()
    if not _token_ok(con):
        return jsonify(ok=False, error="bad_token"), 401
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
                    '<button class="sm" onclick="msgSend407(%d)">Bhejo</button>' % m["id"] if sender else
                    '<span class="muted">(Shavez / doctor sahab bhejenge)</span>')
            else:
                stt = '<span class="muted">%s</span>' % ("queued for the reception phone" if owner else "reception phone bhejega")
            rows.append('<tr><td>%s%s</td><td>%s</td></tr>' % (_esc(m["vendor"]), ' <span class="chip">cheque</span>' if m["kind"] == "cheque" else "", stt))
        h.append('<div class="scroll"><table><tr><th>%s</th><th>%s</th></tr>%s</table></div>'
                 % ("Supplier" if owner else "Supplier", "Message" if owner else "Message", "".join(rows)))
        h.append('<div class="muted">%d told · %d waiting · %d not sent · <a href="%s/page/phone-setup">the reception phone\'s setup</a></div>'
                 % (st["counts"]["sent"], st["counts"]["queued"], st["counts"]["skipped"], prefix))
    if not owner:
        h.append('<div class="muted" style="margin-top:6px"><a href="%s/page/phone-setup">Reception phone ka setup (MacroDroid)</a></div>' % prefix)
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
function msgSend407(id){fetch(P+'/api/supplier-msg/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})})
 .then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error||'could not send');return;}
 if(j.wa_url){window.open(j.wa_url,'_blank');} location.href=location.pathname+'?saved=msg#neftcard_s407';})
 .catch(function(){alert('could not send just now');});}
</script></div>""" % (month, month))
    return "".join(h)


# ---------------------------------------------------------------- Amir's card, Needs you
def amir_card(con):
    """'NEFT <Month>: bheja <date> — bank se confirm baaki / ho gaya' + the suppliers told (bata diya). Events of the last 45 days."""
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


@bp.route("/finance/purchase/page/phone-setup")
def page_phone_setup():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure(con)
    owner = _is_owner(u)
    shown = _setting(con, "supplier_msg.token_shown", "")
    tok = _setting(con, "supplier_msg.phone_token", "")
    show = bool(tok) and (not shown or owner)
    if show and not shown:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('supplier_msg.token_shown', ?, 'S407 -- the setup page showed the token once')", (_iso(),))
        con.commit()
    key_html = ('<p class="key">%s</p>' % _esc(tok)) if show else (
        '<div class="warn">Token ek baar dikha diya gaya tha (%s). Dobara chahiye to doctor sahab apne login se yeh page kholein.</div>' % _esc(shown[:16]))
    body = """<h1>Reception phone — supplier message ka setup (MacroDroid)</h1>
<div class="card"><h2>Yeh kya hai</h2><p>Doctor sahab jab NEFT "done" karte hain, server har supplier ke liye ek WhatsApp message tayyar rakhta hai
(poora account number aur IFSC ke saath). Reception ka phone har 5 minute mein server se poochta hai "koi message hai?", milta hai to
WhatsApp mein khol kar bhej deta hai, aur server ko bata deta hai "ho gaya". Aapko kuch type nahi karna.</p>
<div class="warn">Yeh ek personal WhatsApp ko automation se chalata hai. WhatsApp ki screen badle to macro mein chhota sa sudhaar lag sakta hai.
Neeche wala <b>Bhejo</b> button (Vendor payments page par, 30 minute baad) hamesha kaam karta hai.</div></div>
<div class="card"><h2>Ek baar ka kaam — MacroDroid mein macro banaiye</h2>
<p><b>Trigger:</b> <i>Regular Interval</i> · har <b>5 minute</b> · sirf jab phone unlocked ho (Constraint: <i>Device Unlocked</i>; aur <i>WiFi/Data connected</i>).</p>
<p><b>Actions, isi kram mein:</b></p>
<ol>
<li><b>HTTP Request</b> · GET · URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/next</code> · Header: naam <code>X-Phone-Token</code>, value = neeche wala token (long-press, copy, paste) · Response ko variable <code>resp</code> mein save karein.</li>
<li><b>If</b> <code>resp</code> contains <code>"id"</code> (yaani message hai):</li>
<li>&nbsp;&nbsp;<b>JSON Parse</b> (ya <i>Text Manipulation</i>): <code>resp</code> se <code>id</code>, <code>to</code>, <code>text</code> nikaalein.</li>
<li>&nbsp;&nbsp;<b>Open Website / Launch URL</b>: <code>https://wa.me/{to}?text={text}</code> (text ko URL-encode karein — MacroDroid ka <i>Encode URL</i> option).</li>
<li>&nbsp;&nbsp;<b>Wait</b> 6 second.</li>
<li>&nbsp;&nbsp;<b>UI Interaction</b> → <i>Click</i> → text <code>Send</code> (WhatsApp ka Send button; Accessibility permission chahiye).</li>
<li>&nbsp;&nbsp;<b>Wait</b> 3 second.</li>
<li>&nbsp;&nbsp;<b>HTTP Request</b> · POST · URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/done</code> · wahi header · Body (JSON): <code>{"id": {id}, "ok": true}</code>.</li>
<li><b>End If</b>.</li>
</ol>
<p class="mut">Agar Send nahi dab paaya: POST body <code>{"id": {id}, "ok": false, "error": "send not clicked"}</code> bhejein — server 30 minute baad phir se dega, aur 30 minute baad Vendor payments page par <b>Bhejo</b> button dikhne lagega.</p>
<p class="mut">Android settings: MacroDroid → Battery → <b>Unrestricted</b>; Accessibility → MacroDroid <b>on</b>. Phone WhatsApp mein login rahe.</p>
<p class="mut">MacroDroid ki .macro file yahan nahi di gayi — uska format bharosemand tarike se nahi banaya ja saka; upar likhe steps hi record hain.</p></div>
<div class="card"><h2>Token (sirf is phone ke liye)</h2>%s<p class="mut">Yeh token kisi ko WhatsApp / chat par na bhejein.</p></div>
<p class="mut"><a href="/finance/purchase/page/pay">← Vendor payments</a> · <a href="/portal">Portal</a></p>""" % key_html
    html = ('<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Reception phone setup</title><style>%s</style></head><body>%s</body></html>' % (SETUP_CSS, body))
    return html, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}
