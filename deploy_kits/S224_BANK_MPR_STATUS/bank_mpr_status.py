#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bank_mpr_status.py  ·  S224  ·  "Where is the bank MPR for <date>?" — stated in one line.

WHY (owner, 04-Sep-2026 10:45): "there is no mention of the bank MPR that was supposed to land
in the morning; the Sept 3 statement doesn't mention it — it should say applied, waiting etc.
clearly."  No screen said it. The Day Revenue page (`finance_clinic_day.py`) never names the
bank at all; the register card says only "statement not arrived", with no time and no reason.

WHAT THE MPR IS.  ICICI Merchant Solutions mails one .xlsx per merchant per day
(`<MID>_<DDMMYYYY>_ICICI_POS_CD.xlsx`).  A file mailed on day D carries business day D-1.
Since 31-Aug the mail lands ~11:15 IST; the clinic-Gmail Apps Script (VPS_Push_UPI.gs v3, S217)
pushes it HOURLY to POST /finance/api/upi-statement and shouts by mail at 15:00 if the day's
mails never came.  On the VPS `finance_upi.ingest_statement` writes one `upi_statement` row per
(merchant, business day) — `ingested_at` is the moment it was APPLIED — plus the per-payment
`upi_txn` rows (S208) and the raw file under FINANCE_UPI_DIR.  A file that fails its own
Grand-Total check is refused whole and leaves a `data_flag` row `UPI_STATEMENT_REJECTED`.

THE STATES this module computes, from the store, never from memory:
  APPLIED       upi_statement row exists, applied on or before the expected time
  LATE          upi_statement row exists, applied AFTER the expected time (still applied)
  REJECTED      no row, but a UPI_STATEMENT_REJECTED flag names the mail-day file (received,
                NOT applied — the reason is the parser's own message)
  NO ROWS       no row, but the raw file for that mail day IS in the store: the bank sent the
                file and it holds no clinic UPI for that date (a genuinely zero-UPI day)
  WAITING       nothing yet and the expected time has not passed
  NOT RECEIVED  nothing yet and the expected time HAS passed

EXPECTED TIME.  Mail ~11:15 on D+1, hourly push → on the VPS by ~12:20 IST on D+1.  These
constants are the S217 schedule; change them here if the bank or the trigger moves again.

ROUTES (login: maker/checker on the clinic unit, like the Day Revenue page).  They live under
/finance/clinic/ because the app's front gate resolves the unit FROM THE PATH (_unit_for_path):
outside that prefix a clinic-only login is redirected to the portal before any route runs.
  GET /finance/clinic/bank/mpr/<date>          one HTML line (a fragment, embeddable), ?json=1 for JSON
  GET /finance/clinic/bank/mpr/<date>.json     the same as JSON
  GET /finance/clinic/bank/mpr                 the last 8 business days, one line each (tiny page)
  Optional ?unit=medical for the Sanjeevni merchant (default: the clinic).

It creates no table and writes nothing.  Mounted from finance_app.py by init(app, db, require).
"""
import datetime as dt
import glob
import html
import os

from flask import Blueprint, jsonify, request

bp = Blueprint("bank_mpr_status", __name__)
_db = None
_require = None
_unit = "clinic"
_upi_dir = None

# --- the S217 schedule (IST, the box's clock) ---------------------------------------------
MAIL_HHMM = "11:15"        # ICICI's mail for business day D lands about here on D+1
EXPECT_HHMM = "12:20"      # hourly GAS push -> on the VPS by about here on D+1
SHOUT_HHMM = "15:00"       # GAS checkUpiArrival mails the owner if the mails never came

UNIT_LABEL = {"clinic": "Clinic", "medical": "Sanjeevni", "lab": "NK Pathology"}


def init(app, db_getter, require_fn, unit="clinic", upi_dir=None, url_prefix=""):
    """Mount at IMPORT time, like every other module in this app (gunicorn never reaches
    __main__).  No db call here (F-303)."""
    global _db, _require, _unit, _upi_dir
    _db, _require, _unit, _upi_dir = db_getter, require_fn, unit, upi_dir
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ------------------------------------------------------------------ the computation

def _iso_ok(s):
    try:
        return dt.date(int(s[:4]), int(s[5:7]), int(s[8:10])).isoformat() == s
    except (ValueError, IndexError, TypeError):
        return False


def _hhmm(s):
    h, m = s.split(":")
    return int(h), int(m)


def _mid_for(unit):
    """The merchant id for a unit, from finance_upi.MIDS when it is importable (it is, on the
    box — the module sits beside this one).  None when unknown: the filename tests then match
    on the date tag alone."""
    try:
        import finance_upi                                   # noqa: PLC0415
        for mid, u in getattr(finance_upi, "MIDS", {}).items():
            if u == unit:
                return mid
    except Exception:                                        # noqa: BLE001
        pass
    return None


def _fmt_ts(iso):
    """'2026-09-04T12:21:07' -> '04-Sep 12:21'."""
    try:
        t = dt.datetime.fromisoformat(iso)
        return t.strftime("%d-%b %H:%M")
    except (ValueError, TypeError):
        return str(iso or "?")


def _human(iso):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%a %d-%b-%Y")


def mpr_state(con, date, unit=None, now=None, upi_dir=None):
    """The one honest answer for (unit, business date).  Pure: reads, never writes.
    Returns a dict with 'state' in
      applied | late | rejected | no_rows | waiting | not_received | bad_date
    and 'line' — the English sentence the owner asked for."""
    unit = unit or _unit
    now = now or dt.datetime.now().replace(microsecond=0)
    upi_dir = upi_dir if upi_dir is not None else _upi_dir
    label = UNIT_LABEL.get(unit, unit)
    if not _iso_ok(date):
        return dict(ok=False, state="bad_date", date=date, unit=unit, line="Not a date.")

    d = dt.date.fromisoformat(date)
    mail_day = d + dt.timedelta(days=1)
    eh, em = _hhmm(EXPECT_HHMM)
    expected_at = dt.datetime(mail_day.year, mail_day.month, mail_day.day, eh, em)
    sh, sm = _hhmm(SHOUT_HHMM)
    shout_at = dt.datetime(mail_day.year, mail_day.month, mail_day.day, sh, sm)
    tag = mail_day.strftime("%d%m%Y")
    base = dict(ok=True, date=date, unit=unit, unit_label=label,
                expected_by=expected_at.isoformat(), mail_day=mail_day.isoformat())

    # 1. APPLIED / LATE -- the upi_statement row is the store's own word.
    try:
        st = con.execute(
            "SELECT ingested_at, txn_count, parsed_total_p, filename FROM upi_statement "
            "WHERE unit=? AND statement_date=?", (unit, date)).fetchone()
    except Exception as ex:                                  # noqa: BLE001  (no table yet)
        st = None
        base["store_error"] = str(ex)[:120]
    if st is not None:
        applied = st["ingested_at"] or ""
        try:
            late = dt.datetime.fromisoformat(applied) > expected_at
        except (ValueError, TypeError):
            late = False
        rows = int(st["txn_count"] or 0)
        total_p = int(st["parsed_total_p"] or 0)
        rup = "{:,}".format(int(round(total_p / 100.0)))
        if late:
            line = ("Bank MPR for %s (%s): LATE — received and applied at %s IST "
                    "(expected by ~%s on %s) · %d rows, ₹%s"
                    % (_human(date), label, _fmt_ts(applied), EXPECT_HHMM,
                       mail_day.strftime("%d-%b"), rows, rup))
        else:
            line = ("Bank MPR for %s (%s): APPLIED at %s IST · %d rows, ₹%s"
                    % (_human(date), label, _fmt_ts(applied), rows, rup))
        return dict(base, state=("late" if late else "applied"), applied_at=applied,
                    rows=rows, total_p=total_p, total_rupees=rup, filename=st["filename"],
                    line=line)

    mid = _mid_for(unit)

    # 2. REJECTED -- received, refused whole by the parser; never applied.
    try:
        flags = list(con.execute(
            "SELECT id, detail FROM data_flag WHERE code='UPI_STATEMENT_REJECTED' "
            "AND detail LIKE ? ORDER BY id DESC", ("%%_%s_%%" % tag,)))
    except Exception:                                        # noqa: BLE001
        flags = []
    for f in flags:
        det = f["detail"] or ""
        if mid and not det.startswith(mid):
            continue
        reason = det.split(":", 1)[1].strip() if ":" in det else det
        line = ("Bank MPR for %s (%s): RECEIVED, NOT APPLIED — the file for %s was refused: %s"
                % (_human(date), label, mail_day.strftime("%d-%b"), reason[:160]))
        return dict(base, state="rejected", reason=reason[:300], flag_id=f["id"], line=line)

    # 3. NO ROWS -- the raw file for the mail day is in the store, but held nothing for this
    #    date under this merchant: the bank witnessed a zero-UPI day.
    if upi_dir and os.path.isdir(upi_dir):
        pat = os.path.join(upi_dir, "*_%s_%s_*" % (mid, tag) if mid else "*_%s_*" % tag)
        hits = sorted(glob.glob(pat), key=os.path.getmtime)
        if hits:
            got = dt.datetime.fromtimestamp(os.path.getmtime(hits[-1])).replace(microsecond=0)
            line = ("Bank MPR for %s (%s): RECEIVED at %s IST — the bank's file for %s holds NO "
                    "%s UPI on this date (a zero-UPI day, or the day was closed)"
                    % (_human(date), label, _fmt_ts(got.isoformat()),
                       mail_day.strftime("%d-%b"), label))
            return dict(base, state="no_rows", received_at=got.isoformat(),
                        filename=os.path.basename(hits[-1]), line=line)

    # 4. WAITING / NOT RECEIVED -- nothing in the store at all.
    if now < expected_at:
        line = ("Bank MPR for %s (%s): WAITING — ICICI mails it ~%s on %s and the hourly push "
                "lands it by ~%s IST; not received yet"
                % (_human(date), label, MAIL_HHMM, mail_day.strftime("%d-%b"), EXPECT_HHMM))
        return dict(base, state="waiting", line=line)
    if now < shout_at:
        tail = ("if it is still missing at %s the Gmail script mails Dr Manoj" % SHOUT_HHMM)
    else:
        tail = ("the Gmail script's %s check should have mailed Dr Manoj; if no such mail came, "
                "the check itself needs looking at" % SHOUT_HHMM)
    line = ("Bank MPR for %s (%s): NOT RECEIVED — expected by ~%s IST on %s; %s"
            % (_human(date), label, EXPECT_HHMM, mail_day.strftime("%d-%b"), tail))
    return dict(base, state="not_received", line=line)


# ------------------------------------------------------------------------- HTML

_COLOUR = {"applied": "#1b7f3b", "late": "#b36b00", "rejected": "#b00020", "no_rows": "#555",
           "waiting": "#1a5fb4", "not_received": "#b00020", "bad_date": "#b00020"}


def fragment(res):
    """One line, safe to drop into any page.  No <script>."""
    col = _COLOUR.get(res.get("state"), "#333")
    return ('<div class="mpr-status" data-state="%s" style="margin:6px 0;padding:6px 10px;'
            'border-left:4px solid %s;background:#fafafa;font:14px/1.4 system-ui,sans-serif">'
            '%s</div>' % (html.escape(res.get("state", "")), col, html.escape(res["line"])))


def _guard():
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return None, err
    return u, None


@bp.route("/finance/clinic/bank/mpr/<date>")
def mpr_one(date):
    _, err = _guard()
    if err:
        return err
    want_json = date.endswith(".json") or request.args.get("json") == "1" \
        or "application/json" in (request.headers.get("Accept") or "")
    date = date[:-5] if date.endswith(".json") else date
    unit = request.args.get("unit") or _unit
    res = mpr_state(_db(), date, unit=unit)
    if want_json:
        return jsonify(res), (200 if res.get("ok") else 400)
    return fragment(res), (200 if res.get("ok") else 400), {"Content-Type": "text/html; charset=utf-8"}


@bp.route("/finance/clinic/bank/mpr")
def mpr_recent():
    _, err = _guard()
    if err:
        return err
    unit = request.args.get("unit") or _unit
    try:
        n = max(1, min(31, int(request.args.get("days", "8"))))
    except ValueError:
        n = 8
    con = _db()
    today = dt.date.today()
    rows = [fragment(mpr_state(con, (today - dt.timedelta(days=i)).isoformat(), unit=unit))
            for i in range(n)]
    body = ("<!doctype html><meta charset='utf-8'><title>Bank MPR — last %d days</title>"
            "<div style='max-width:900px;margin:18px auto;font-family:system-ui,sans-serif'>"
            "<h2 style='margin:0 0 4px'>Bank MPR — %s, last %d days</h2>"
            "<p style='color:#555;margin:0 0 12px'>A day's ICICI statement is mailed the NEXT "
            "morning (~%s) and reaches the VPS by ~%s IST. Each line is computed from the "
            "statement store at the moment you opened this page.</p>%s"
            "<p style='color:#777;font-size:12px'>One day: /finance/clinic/bank/mpr/&lt;YYYY-MM-DD&gt; "
            "(add ?json=1 for JSON).</p></div>"
            % (n, html.escape(UNIT_LABEL.get(unit, unit)), n, MAIL_HHMM, EXPECT_HHMM, "".join(rows)))
    return body, 200, {"Content-Type": "text/html; charset=utf-8"}
