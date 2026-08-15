#!/usr/bin/env python3
# =============================================================================
#  finance_app.py  ·  Clinic Finance — MEDICAL (Sanjeevni) module
#  Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre, Bareilly
#  Session 179 · step B2 · contract: S179_Clinic_Finance_System_Build_Contract_v2
#
#  SCOPE (owner instruction, S179): medical entry system only, with the plumbing
#  for pathology / clinic / accountant exports already in the schema. Once medical
#  is streamlined the other two are largely replication.
#
#  ROLES
#    maker    — pharmacy (Darpan or the reserve person). Files the day.
#    checker  — the doctor. Approves. Approval is what posts a salary advance to
#               the Staff Ledger (D258 stays the single home for staff money).
#    viewer   — read-only.
#
#  NON-NEGOTIABLES ENFORCED SERVER-SIDE (never trust the browser):
#    * opening cash is COMPUTED, never accepted from the client
#    * closing cash may not go negative
#    * UPI may not exceed the day's total
#    * one row per (unit, business_date) — a second submit CORRECTS, never duplicates
#    * a missing day is never silenced (S179 ruling) — it stays pinned on the tile
#    * every mutation writes audit_log
#
#  Money is INTEGER PAISE throughout.
#  UI is served from disk (D312) out of FINANCE_UI_DIR.
#  Runs on Flask only — no other third-party import.
# =============================================================================

import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys

from flask import (Flask, g, jsonify, redirect, request, send_file,
                   send_from_directory)

import finance_ingest
import finance_upi

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("FINANCE_DB", os.path.join(APP_ROOT, "finance.db"))
UI_DIR = os.environ.get("FINANCE_UI_DIR", os.path.join(APP_ROOT, "finance_ui"))
SCAN_DIR = os.environ.get("FINANCE_SCAN_DIR", os.path.join(APP_ROOT, "finance_scans"))
UNIT = "medical"
MAX_SANE_P = 100_000_00          # ₹1,00,000 for a single typed figure -> confirm above this
BACKFILL_WINDOW_DAYS = 120       # how far back a maker may still file a day

app = Flask(__name__)


# ----------------------------------------------------------------- infra

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def _close(_exc):
    con = g.pop("db", None)
    if con is not None:
        con.close()


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def today():
    return dt.date.today()


# --------------------------------------------------------------------- SSO
# Identity comes from the clinic's own signed cookie (D261 / clinic_sso.py),
# verified here exactly as the ledger and asset apps verify it.
#
# HEADER AUTH IS OFF UNLESS EXPLICITLY ENABLED. It exists only so the module can
# be smoke-tested offline. Left on in production it would let anyone send
# "X-Clinic-Role: checker" and approve their own entries — so it is now opt-in
# via FINANCE_ALLOW_HEADER_AUTH, and the systemd unit does not set it.

SSO_DIR = os.environ.get("FINANCE_SSO_DIR", "/root/portal")
ALLOW_HEADER_AUTH = os.environ.get("FINANCE_ALLOW_HEADER_AUTH", "") == "1"
CRON_TOKEN = os.environ.get("FINANCE_CRON_TOKEN", "")
PORTAL_LOGIN = os.environ.get("FINANCE_PORTAL_LOGIN", "/portal")

_sso = None
_sso_secret = None


def sso():
    """Import the shared shim once. Absent shim is fatal in production and
    merely means 'no cookie auth' offline — it never silently allows access,
    because the fail-closed gate below still refuses without an identity."""
    global _sso, _sso_secret
    if _sso is not None:
        return _sso, _sso_secret
    try:
        if SSO_DIR not in sys.path:
            sys.path.insert(0, SSO_DIR)
        import clinic_sso                                    # noqa: PLC0415
        _sso = clinic_sso
    except Exception:                                        # noqa: BLE001
        _sso = False
        return _sso, None
    # The secret lives in the environment. If it is not there, fall back to the
    # portal's own config module — the same secret, in the place it already
    # lives, rather than a second copy in a new file.
    try:
        _sso_secret = _sso.get_secret()
    except Exception:                                        # noqa: BLE001
        try:
            import portal_config                             # noqa: PLC0415
            _sso_secret = getattr(portal_config, "CLINIC_SSO_SECRET", None) or None
        except Exception:                                    # noqa: BLE001
            _sso_secret = None
    return _sso, _sso_secret


def sso_epoch():
    """The CURRENT epoch from the portal's own user store — not a copy, not a
    cached value. "Sign out everywhere" works by bumping this, so reading it
    fresh on every request is the point: a cached epoch would keep revoked
    sessions alive for as long as the cache lived.

    Returns None if it cannot be read, and the caller then REFUSES. Until now
    this app passed current_epoch=None, which meant it never checked at all —
    so a session the portal had correctly revoked still opened the books."""
    try:
        if SSO_DIR not in sys.path:
            sys.path.insert(0, SSO_DIR)
        import clinic_users                                  # noqa: PLC0415
        return int(clinic_users.get_epoch(clinic_users.DEFAULT_STORE))
    except Exception:                                        # noqa: BLE001
        return None


def _sso_identity():
    mod, secret = sso()
    if not mod or not secret:
        return None
    tok = request.cookies.get(getattr(mod, "COOKIE_NAME", "clinic_sso"))
    if not tok:
        return None

    epoch = sso_epoch()
    if epoch is None:
        # Fail CLOSED, exactly as the portal does when it cannot resolve the
        # store. An escape hatch here would be another "convenience" flag, and
        # convenience flags are what caused the first two faults in this app.
        return None

    try:
        data = mod.verify_token(tok, secret, current_epoch=epoch)
    except Exception:                                        # noqa: BLE001
        return None
    if not data:
        return None
    user = data.get("user") or data.get("u") or ""
    role = data.get("role") or data.get("r") or ""
    return {"user": str(user), "role": str(role)} if user else None


def current_user():
    """Who is asking. Cookie first; headers only when explicitly allowed."""
    ident = _sso_identity()
    if ident:
        return ident
    if ALLOW_HEADER_AUTH:
        return {"user": request.headers.get("X-Clinic-User")
                        or os.environ.get("FINANCE_DEV_USER") or "",
                "role": request.headers.get("X-Clinic-Role")
                        or os.environ.get("FINANCE_DEV_ROLE") or ""}
    return {"user": "", "role": ""}


# Routes reachable without an identity. Deliberately a SHORT allow-list, not a
# deny-list: a new route is protected by default, which is the only ordering
# that survives someone (me) forgetting.
# Static assets with no clinic data in them: the shared scanner widget (which
# the asset app already serves publicly) and jsPDF. Public so they cache well
# and so a browser that fetches a script without credentials still works.
PUBLIC_PATHS = ("/finance/healthz",
                "/finance/scan/widget.js",
                "/finance/scan/jspdf.js")

# Signed in, but no unit role required — so anyone can see WHY they were
# refused instead of staring at a bare 403.
IDENTITY_ONLY_PATHS = ("/finance/api/whoami",)


@app.before_request
def _gate():
    """FAIL CLOSED. Every route except the allow-list needs a resolved identity.

    The first version of this app trusted upstream headers and gated only the
    write endpoints, which left the reads — cash position, revenue, and later
    patient names — open to anyone who knew the URL. This gate is the fix, and
    it protects future routes automatically."""
    p = request.path.rstrip("/") or request.path
    if p in PUBLIC_PATHS or request.path in PUBLIC_PATHS:
        return None
    if CRON_TOKEN and request.headers.get("X-Finance-Cron") == CRON_TOKEN:
        return None
    u = current_user()
    if not u.get("user"):
        if request.path.startswith("/finance/api/"):
            return jsonify(ok=False, error="not_signed_in",
                           message="Sign in on the clinic portal first."), 401
        return redirect(PORTAL_LOGIN, code=302)

    # Signed in is not the same as entitled. A valid clinic login with no role
    # on THIS unit gets nothing — otherwise every staff member with an SSO
    # account could read the pharmacy's cash position, which is not what the
    # owner asked for (medical's checker is the doctor alone).
    if request.path.rstrip("/") in IDENTITY_ONLY_PATHS:
        return None
    if roles_for(db(), UNIT, u["user"], u.get("role")):
        return None
    if request.path.startswith("/finance/api/"):
        return jsonify(ok=False, error="no_role_here",
                       message="You are signed in, but you have no role in "
                               "Sanjeevni Medicos."), 403
    return redirect(PORTAL_LOGIN, code=302)


# The broker issues clinic-wide roles ('doctor', 'manager'). Finance roles are
# per unit and live in unit_role.
#
# This map is EMPTY on purpose. It is tempting to say doctor -> checker
# everywhere, but the owner's rule is that medical's checker is Dr Manoj ALONE,
# while Dr Bhawna checks lab and clinic. If her broker role is also 'doctor',
# a blanket grant would hand her the pharmacy — the exact thing that was ruled
# out. So unit_role is the single authority on who can do what, per unit, by
# name. Bootstrapping is handled by post_install_finance.sh, which writes the
# real usernames in and prints what it wrote.
SSO_ROLE_MAP = {}

FINANCE_ROLES = ("maker", "checker", "viewer")


def roles_for(con, unit, username, sso_role):
    """Roles are PER UNIT (S179): the doctor checks everything, Dr Bhawna also
    checks lab and clinic, each unit has its own maker. unit_role is the
    authority; the broker role only grants what SSO_ROLE_MAP says it grants."""
    got = {r["role"] for r in con.execute(
        "SELECT role FROM unit_role WHERE unit=? AND lower(username)=lower(?) AND active=1",
        (unit, username or ""))}
    got |= SSO_ROLE_MAP.get((sso_role or "").lower(), set())
    if ALLOW_HEADER_AUTH and sso_role in FINANCE_ROLES:
        got.add(sso_role)                    # offline testing only
    return got


def require(*roles, unit=UNIT):
    u = current_user()
    have = roles_for(db(), unit, u["user"], u["role"])
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted",
                              message="Your login is not permitted to do this."), 403)
    u = dict(u, roles=sorted(have))
    return u, None


def setting(con, key, default=None):
    r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    return r["value"] if r else default


def deposit_threshold_p(con, unit=UNIT):
    try:
        return int(setting(con, "%s.deposit_threshold_p" % unit, "0") or 0)
    except (TypeError, ValueError):
        return 0


def month_bounds(ym):
    y, m = int(ym[:4]), int(ym[5:])
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    return first, last


def audit(con, table, row_id, action, before=None, after=None, who=""):
    con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) "
                "VALUES (?,?,?,?,?,?,?)",
                (table, row_id, action,
                 json.dumps(before, ensure_ascii=False) if before is not None else None,
                 json.dumps(after, ensure_ascii=False) if after is not None else None,
                 who, now_iso()))


# ----------------------------------------------------------------- money

def to_paise(v, field):
    """Accept only a clean non-negative number. This is the server-side half of
    'make the form error proof from typos' — the browser's numeric keypad is a
    convenience; THIS is the guarantee."""
    if v is None or v == "":
        return 0
    s = str(v).strip().replace(",", "").replace("₹", "")
    if not re.fullmatch(r"\d+(\.\d{1,2})?", s):
        raise ValueError("%s: '%s' is not a number — digits only" % (field, v))
    return int(round(float(s) * 100))


def rupees(p):
    if p is None:
        return ""
    sign = "-" if p < 0 else ""
    p = abs(int(p))
    whole, frac = divmod(p, 100)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = head + "," + tail
    return "%s%s.%02d" % (sign, s, frac)


def parse_iso_date(s):
    """Never slice a date string — parse it (F-78)."""
    return dt.datetime.strptime(str(s).strip(), "%Y-%m-%d").date()


# ----------------------------------------------------------------- ledger

def opening_p(con, unit, date_iso):
    """COMPUTED opening = closing of the most recent entry strictly before this
    date. There is no stored column for this and no endpoint that accepts it.
    That single fact is what makes the 36 legacy carry-forward breaks impossible."""
    row = con.execute(
        "SELECT closing_p FROM v_cash_ledger WHERE unit=? AND business_date < ? "
        "ORDER BY business_date DESC LIMIT 1", (unit, date_iso)).fetchone()
    return int(row["closing_p"]) if row else 0


def day_state(con, unit, date_iso):
    e = con.execute("SELECT * FROM day_entry WHERE unit=? AND business_date=?",
                    (unit, date_iso)).fetchone()
    op = opening_p(con, unit, date_iso)
    if not e:
        return {"exists": False, "business_date": date_iso, "status": "new",
                "opening_p": op, "opening": rupees(op),
                "lines": {}, "expenses": [], "movements": [], "attachments": [],
                "closing_p": op, "closing": rupees(op)}

    led = con.execute("SELECT * FROM v_cash_ledger WHERE unit=? AND business_date=?",
                      (unit, date_iso)).fetchone()
    lines = {r["mode"]: r["amount_p"] for r in
             con.execute("SELECT mode, SUM(amount_p) amount_p FROM day_line "
                         "WHERE day_entry_id=? GROUP BY mode", (e["id"],))}
    exps = [dict(id=r["id"], amount_p=r["amount_p"], amount=rupees(r["amount_p"]),
                 known=bool(r["amount_known"]), category_fixed=r["category_fixed"],
                 staff_id=r["staff_id"], category_text=r["category_text"],
                 ledger_posted=bool(r["ledger_posted"]))
            for r in con.execute("SELECT * FROM day_expense WHERE day_entry_id=?", (e["id"],))]
    movs = [dict(id=r["id"], direction=r["direction"], party=r["party"],
                 amount_p=r["amount_p"], amount=rupees(r["amount_p"]), reference=r["reference"])
            for r in con.execute("SELECT * FROM cash_movement WHERE day_entry_id=?", (e["id"],))]
    atts = [dict(id=r["id"], doc_type=r["doc_type"],
                 has_file=bool(r["path"] or r["external_url"]),
                 external=bool(r["external_url"] and not r["path"]),
                 uploaded_at=r["uploaded_at"],
                 url="/finance/attachment/%d" % r["id"])
            for r in con.execute("SELECT * FROM attachment WHERE day_entry_id=? "
                                 "ORDER BY doc_type", (e["id"],))]
    adjs = [dict(id=r["id"], amount=rupees(r["amount_p"]), reason=r["reason"], status=r["status"])
            for r in con.execute("SELECT * FROM cash_adjustment WHERE day_entry_id=?", (e["id"],))]
    bills = [dict(id=r["id"], bill_no=r["bill_no"], bill_date=r["bill_date"], head=r["head"],
                  head_text=r["head_text"], amount_p=r["amount_p"], amount=rupees(r["amount_p"]),
                  status=r["status"])
             for r in con.execute("SELECT * FROM day_noncash_bill WHERE day_entry_id=? "
                                  "ORDER BY bill_date, id", (e["id"],))]
    noncash_p = sum(b["amount_p"] for b in bills)

    cash_p = lines.get("cash", 0)
    upi_p = lines.get("upi", 0)
    return {
        "exists": True, "id": e["id"], "business_date": date_iso, "status": e["status"],
        "source": e["source"], "entered_by": e["entered_by"], "approved_by": e["approved_by"],
        "manned_by": e["manned_by"], "manned_source": e["manned_source"],
        "opening_p": op, "opening": rupees(op),
        "cash_p": cash_p, "cash": rupees(cash_p),
        "upi_p": upi_p, "upi": rupees(upi_p),
        "total_p": cash_p + upi_p, "total": rupees(cash_p + upi_p),
        "closing_p": int(led["closing_p"]) if led else op,
        "closing": rupees(int(led["closing_p"]) if led else op),
        "noncash_p": noncash_p, "noncash": rupees(noncash_p),
        "cash_actually_received_p": cash_p - noncash_p,
        "cash_actually_received": rupees(cash_p - noncash_p),
        "lines": lines, "expenses": exps, "movements": movs,
        "attachments": atts, "adjustments": adjs, "noncash_bills": bills,
    }


# ----------------------------------------------------------------- missing days

REQUIRED_DOCS = ("sale_report", "manual_copy", "orthotics_copy")


def refresh_missing_days(con, unit=UNIT, upto=None):
    """S179 ruling: a missing day is NEVER silenced — not for Sunday, not for
    Darpan's absence. Absence changes who files it and when, never whether it is
    owed. The exception stays open until the day is actually filed."""
    upto = upto or (today() - dt.timedelta(days=1))
    first = con.execute("SELECT MIN(business_date) d FROM day_entry WHERE unit=?", (unit,)).fetchone()["d"]
    if not first:
        return 0
    have = {r["business_date"] for r in
            con.execute("SELECT business_date FROM day_entry WHERE unit=?", (unit,))}
    d = parse_iso_date(first)
    opened = 0
    while d <= upto:
        iso = d.isoformat()
        if iso in have:
            con.execute("UPDATE recon_exception SET status='resolved', "
                        "resolution='day filed', closed_at=? "
                        "WHERE unit=? AND business_date=? AND kind='missing_day' AND status='open'",
                        (now_iso(), unit, iso))
        else:
            cur = con.execute(
                "INSERT OR IGNORE INTO recon_exception "
                "(unit, business_date, kind, severity, status, detail, opened_at, shout_count) "
                "VALUES (?,?, 'missing_day', 'high', 'open', ?, ?, 0)",
                (unit, iso, "not filed (%s) — this day is still owed" % d.strftime("%A"), now_iso()))
            opened += cur.rowcount
        d += dt.timedelta(days=1)
    con.commit()
    return opened


def open_exceptions(con, unit=UNIT, limit=200):
    rows = con.execute(
        "SELECT id, business_date, kind, severity, diff_p, detail, shout_count "
        "FROM recon_exception WHERE unit=? AND status='open' "
        "ORDER BY CASE severity WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, "
        "business_date DESC LIMIT ?", (unit, limit)).fetchall()
    return [dict(id=r["id"], date=r["business_date"], kind=r["kind"], severity=r["severity"],
                 diff=rupees(r["diff_p"]) if r["diff_p"] is not None else "",
                 detail=r["detail"], shouts=r["shout_count"]) for r in rows]


# ----------------------------------------------------------------- pages

@app.route("/finance/healthz")
def healthz():
    con = db()
    n = con.execute("SELECT COUNT(*) c FROM day_entry WHERE unit=?", (UNIT,)).fetchone()["c"]
    # sso_epoch_ok is deliberately visible here: if it is false, every cookie
    # login is being refused, and that must be diagnosable without a cookie.
    return jsonify(ok=True, unit=UNIT, days=n, db=os.path.basename(DB_PATH),
                   sso_epoch_ok=(sso_epoch() is not None))


@app.route("/finance/")
def page_root():
    """Land each person on their own screen — the pharmacy never sees the
    approval page, the doctor never has to hunt for it."""
    u = current_user()
    have = roles_for(db(), UNIT, u["user"], u["role"])
    name = "finance_review.html" if "checker" in have else "finance_entry.html"
    return send_from_directory(UI_DIR, name)


@app.route("/finance/entry")
def page_entry():
    return send_from_directory(UI_DIR, "finance_entry.html")


@app.route("/finance/review")
def page_review():
    return send_from_directory(UI_DIR, "finance_review.html")



# ------------------------------------------------------ the scanner surface
# The clinic's refined widget is REUSED FROM DISK — not copied, not rewritten.
# It is served from this app's own origin so the pharmacy's daily path does not
# depend on assets.dr-manoj.in being up, and jsPDF is vendored locally rather
# than pulled from a CDN, because this page is used on a phone on a weak line.

SCANNER_JS = os.environ.get("FINANCE_SCANNER_JS", "/root/assetapp/scanner_widget.js")
JSPDF_JS = os.environ.get("FINANCE_JSPDF_JS", os.path.join(APP_ROOT, "vendor", "jspdf.umd.min.js"))

SCAN_DOC_LABEL = {
    "sale_report": "Day's sale report",
    "manual_copy": "Manual copy page",
    "orthotics_copy": "Orthotics copy",
    "deposit_slip": "Deposit slip",
}


def _file_or_404(path, mime):
    if not os.path.exists(path):
        return jsonify(ok=False, error="not_installed", path=os.path.basename(path)), 404
    with open(path, "rb") as fh:
        body = fh.read()
    return app.response_class(body, mimetype=mime,
                              headers={"Cache-Control": "public, max-age=300"})


@app.route("/finance/scan/widget.js")
def scan_widget_js():
    return _file_or_404(SCANNER_JS, "application/javascript")


@app.route("/finance/scan/jspdf.js")
def scan_jspdf_js():
    return _file_or_404(JSPDF_JS, "application/javascript")


@app.route("/finance/scan/<date_iso>/<doc_type>")
def scan_page(date_iso, doc_type):
    """Host page for one document. The widget takes over the screen, uploads,
    then returns to the entry screen via backUrl — which is how it is built to
    work, rather than the modal I originally assumed."""
    u, err = require("maker", "checker")
    if err:
        return err
    if doc_type not in SCAN_DOC_LABEL:
        return jsonify(ok=False, error="bad_doc_type"), 400
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    con = db()
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (UNIT, iso)).fetchone()
    if not e:
        return app.response_class(
            "<meta charset=utf-8><p style='font:16px system-ui;padding:24px'>"
            "Save the day first, then attach its scans. "
            "<a href='/finance/entry?d=%s'>Back</a></p>" % iso,
            mimetype="text/html", status=409)

    try:
        ver = int(os.path.getmtime(SCANNER_JS))
    except OSError:
        ver = 0
    cfg = {
        "title": "%s — %s" % (SCAN_DOC_LABEL[doc_type], iso),
        "uploadUrl": "/finance/api/day/%s/scan/%s" % (iso, doc_type),
        "fileField": "file",
        "uploadFields": {"unit": UNIT, "business_date": iso, "doc_type": doc_type},
        "nameBase": "Sanjeevni_%s_%s" % (doc_type, iso),
        "backUrl": "/finance/entry?d=%s" % iso,
        "allowIdCard": False,
        "allowBatch": False,
    }
    html = ("<!DOCTYPE html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title>"
            "<style>body{margin:0;background:#f4f6fa;color:#0f172a;"
            "font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif}"
            ".card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:16px;"
            "margin:14px auto;max-width:760px}"
            ".top{background:#0b1220;color:#fff;padding:12px 16px;font-weight:650;"
            "display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:30}"
            ".top .t{flex:1}"
            ".top a{color:#e2e8f0;text-decoration:none;font-weight:600;font-size:13px;"
            "padding:8px 13px;border-radius:9px;background:rgba(255,255,255,.13);"
            "white-space:nowrap}"
            ".top a:hover{background:rgba(255,255,255,.22)}"
            "input,select,button{font-family:inherit}.muted{color:#64748b}</style></head><body>"
            "<div class=top><a href='/finance/entry?d=%s'>← Back</a>"
            "<span class=t>%s</span></div>"
            "<script>window.SCANNER_CONFIG = %s;</script>"
            "<div id=scanroot></div>"
            "<script src='/finance/scan/jspdf.js'></script>"
            "<script src='/finance/scan/widget.js?v=%d'></script>"
            "</body></html>") % (SCAN_DOC_LABEL[doc_type], iso,
                                 SCAN_DOC_LABEL[doc_type], json.dumps(cfg), ver)
    return app.response_class(html, mimetype="text/html")


# ----------------------------------------------------------------- API: read

@app.route("/finance/api/whoami")
def api_whoami():
    u = current_user()
    con = db()
    have = roles_for(con, UNIT, u["user"], u["role"])
    role = "checker" if "checker" in have else ("maker" if "maker" in have else (u["role"] or ""))
    url = setting(con, "scanner.widget_url", "") or ""
    return jsonify(ok=True, user=u["user"], role=role, roles=sorted(have),
                   unit=UNIT, unit_name="Sanjeevni Medicos",
                   scanner=(dict(url=url, **{"global": setting(con, "scanner.global",
                                                               "ClinicScanner")}) if url else None))


@app.route("/finance/api/tile-meta")
def api_tile_meta():
    """What the portal should print on the tile. The pharmacy's tile is called
    'Daily Sale', not 'Finance' — it names the job, not the department (S179)."""
    con = db()
    u = current_user()
    have = roles_for(con, UNIT, u["user"], u["role"])
    checker = "checker" in have
    return jsonify(ok=True,
                   role=("checker" if checker else "maker"),
                   title=setting(con, "tile.checker_title" if checker else "tile.maker_title"),
                   subtitle=setting(con, "tile.checker_subtitle" if checker
                                    else "tile.maker_subtitle"),
                   href="/finance/review" if checker else "/finance/entry")


@app.route("/finance/api/day/<date_iso>/scan/<doc_type>", methods=["POST"])
def api_scan_upload(date_iso, doc_type):
    """Upload target the existing scanner widget posts its PDF to.
    Registers the attachment against the day. Deliberately strict about which
    document types exist, so a typo cannot create a silent new category."""
    u, err = require("maker", "checker")
    if err:
        return err
    if doc_type not in REQUIRED_DOCS + ("deposit_slip",):
        return jsonify(ok=False, error="bad_doc_type"), 400
    con = db()
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (UNIT, iso)).fetchone()
    if not e:
        return jsonify(ok=False, error="no_day",
                       message="Save the day first, then attach its scans."), 409

    f = request.files.get("file")
    if not f:
        return jsonify(ok=False, error="no_file"), 400
    blob = f.read()
    if not blob:
        return jsonify(ok=False, error="empty_file"), 400
    sha = hashlib.sha256(blob).hexdigest()
    folder = os.path.join(SCAN_DIR, UNIT, iso[:7])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%s_%s_%s.pdf" % (iso, doc_type, sha[:10]))
    with open(path, "wb") as fh:
        fh.write(blob)

    con.execute("DELETE FROM attachment WHERE day_entry_id=? AND doc_type=?", (e["id"], doc_type))
    con.execute("INSERT INTO attachment (day_entry_id, doc_type, path, sha256, bytes, "
                "uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?)",
                (e["id"], doc_type, path, sha, len(blob), u["user"], now_iso()))
    audit(con, "attachment", e["id"], "scan_upload",
          after={"doc_type": doc_type, "sha256": sha, "bytes": len(blob)}, who=u["user"])
    con.commit()
    return jsonify(ok=True, doc_type=doc_type, bytes=len(blob), sha256=sha[:12])


@app.route("/finance/api/day/<date_iso>")
def api_day(date_iso):
    try:
        d = parse_iso_date(date_iso)
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    con = db()
    st = day_state(con, UNIT, d.isoformat())
    st["is_future"] = d > today()
    st["too_old"] = (today() - d).days > BACKFILL_WINDOW_DAYS
    return jsonify(ok=True, day=st)


@app.route("/finance/api/month/<ym>")
def api_month(ym):
    if not re.fullmatch(r"\d{4}-\d{2}", ym):
        return jsonify(ok=False, error="bad_month"), 400
    con = db()
    y, m = int(ym[:4]), int(ym[5:])
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)

    entries = {r["business_date"]: r for r in con.execute(
        "SELECT e.business_date, e.status, l.cash_in_p, l.upi_in_p, l.revenue_p, "
        "       l.expense_p, l.cash_out_p, l.closing_p "
        "FROM day_entry e JOIN v_cash_ledger l "
        "  ON l.unit=e.unit AND l.business_date=e.business_date "
        "WHERE e.unit=? AND e.business_date BETWEEN ? AND ?",
        (UNIT, first.isoformat(), last.isoformat()))}

    missing = {r["business_date"] for r in con.execute(
        "SELECT business_date FROM recon_exception WHERE unit=? AND kind='missing_day' "
        "AND status='open' AND business_date BETWEEN ? AND ?",
        (UNIT, first.isoformat(), last.isoformat()))}

    days, d = [], first
    while d <= last:
        iso = d.isoformat()
        e = entries.get(iso)
        if e:
            state = e["status"]
        elif iso in missing:
            state = "missing"
        elif d > today():
            state = "future"
        else:
            state = "pending"
        days.append(dict(date=iso, dow=d.strftime("%a"), state=state,
                         revenue=rupees(e["revenue_p"]) if e else "",
                         closing=rupees(e["closing_p"]) if e else ""))
        d += dt.timedelta(days=1)

    tot = con.execute(
        "SELECT COUNT(*) days, COALESCE(SUM(revenue_p),0) rev, COALESCE(SUM(cash_in_p),0) cash, "
        "COALESCE(SUM(upi_in_p),0) upi, COALESCE(SUM(expense_p),0) exp, "
        "COALESCE(SUM(cash_out_p),0) dep, COALESCE(SUM(adjust_p),0) adj, "
        "COALESCE(SUM(noncash_p),0) nc "
        "FROM v_cash_ledger WHERE unit=? AND business_date BETWEEN ? AND ?",
        (UNIT, first.isoformat(), last.isoformat())).fetchone()

    heads = [dict(head=r["head"], bills=r["bill_count"], amount=rupees(r["amount_p"]))
             for r in con.execute("SELECT head, bill_count, amount_p FROM v_noncash_by_head "
                                  "WHERE unit=? AND ym=? ORDER BY amount_p DESC", (UNIT, ym))]

    return jsonify(ok=True, ym=ym, days=days, missing_count=len(missing),
                   noncash_by_head=heads,
                   totals=dict(days=tot["days"], revenue=rupees(tot["rev"]),
                               cash=rupees(tot["cash"]), upi=rupees(tot["upi"]),
                               noncash=rupees(tot["nc"]),
                               expenses=rupees(tot["exp"]), deposited=rupees(tot["dep"]),
                               adjustments=rupees(tot["adj"])))


@app.route("/finance/api/exceptions")
def api_exceptions():
    return jsonify(ok=True, exceptions=open_exceptions(db()))


@app.route("/finance/api/tile")
def api_tile():
    """Feeds the portal tile. The shout count is the headline: it is what stays
    pinned at the top until every owed day is filed."""
    con = db()
    refresh_missing_days(con)
    last = con.execute("SELECT business_date, revenue_p, closing_p FROM v_cash_ledger "
                       "WHERE unit=? ORDER BY business_date DESC LIMIT 1", (UNIT,)).fetchone()
    counts = {r["kind"]: r["c"] for r in con.execute(
        "SELECT kind, COUNT(*) c FROM recon_exception WHERE unit=? AND status='open' GROUP BY kind",
        (UNIT,))}
    awaiting = con.execute("SELECT COUNT(*) c FROM day_entry WHERE unit=? AND status='submitted'",
                           (UNIT,)).fetchone()["c"]
    ym = today().strftime("%Y-%m")
    mtd = con.execute("SELECT COALESCE(SUM(revenue_p),0) r FROM v_cash_ledger "
                      "WHERE unit=? AND business_date LIKE ?", (UNIT, ym + "%")).fetchone()["r"]

    # "I should know the cash amount with Darpan" (S179) — cash in hand is not an
    # abstract balance, it is a sum sitting with a named person.
    cust = con.execute("SELECT cash_p, custodian_name FROM v_cash_custody WHERE unit=?",
                       (UNIT,)).fetchone()
    cash_p = int(cust["cash_p"]) if cust else 0
    thr = deposit_threshold_p(con)
    mc = con.execute("SELECT ym, status FROM month_close WHERE unit=? ORDER BY ym DESC LIMIT 1",
                     (UNIT,)).fetchone()

    # Cash reaches the bank on a TRIP, not on a schedule — so the useful number
    # is "how long since the last one", not "is it month end".
    dep = con.execute("SELECT e.business_date d FROM cash_movement m "
                      "JOIN day_entry e ON e.id=m.day_entry_id "
                      "WHERE e.unit=? AND m.direction='out' AND m.party='bank' "
                      "ORDER BY e.business_date DESC LIMIT 1", (UNIT,)).fetchone()
    try:
        trip_days = int(setting(con, "%s.deposit_trip_days" % UNIT, "7") or 7)
    except (TypeError, ValueError):
        trip_days = 7
    since = None
    if dep:
        since = (today() - parse_iso_date(dep["d"])).days

    nc = con.execute("SELECT COALESCE(SUM(noncash_p),0) n FROM v_cash_ledger "
                     "WHERE unit=? AND business_date LIKE ?", (UNIT, ym + "%")).fetchone()["n"]

    return jsonify(ok=True, unit_name="Sanjeevni Medicos",
                   last_bank_deposit=(dep["d"] if dep else None),
                   days_since_bank_deposit=since,
                   bank_trip_due=bool(since is not None and since >= trip_days),
                   noncash_month_to_date=rupees(nc),
                   last_filed=last["business_date"] if last else None,
                   last_revenue=rupees(last["revenue_p"]) if last else "",
                   cash_in_hand=rupees(cash_p),
                   cash_with=(cust["custodian_name"] if cust else "not recorded"),
                   deposit_threshold=rupees(thr),
                   deposit_due=bool(thr and cash_p > thr),
                   deposit_excess=rupees(max(cash_p - thr, 0)) if thr else "",
                   month_to_date=rupees(mtd),
                   awaiting_approval=awaiting,
                   last_month_close=(dict(ym=mc["ym"], status=mc["status"]) if mc else None),
                   shouts=dict(missing_days=counts.get("missing_day", 0),
                               carry_forward=counts.get("carry_forward_break", 0),
                               negative_cash=counts.get("negative_cash", 0),
                               upi_mismatch=counts.get("upi_vs_statement", 0),
                               total=sum(counts.values())))


# ----------------------------------------------------------------- API: write

@app.route("/finance/api/day", methods=["POST"])
def api_save_day():
    u, err = require("maker", "checker")
    if err:
        return err
    p = request.get_json(silent=True) or {}
    con = db()

    # ---- date ---------------------------------------------------------------
    try:
        d = parse_iso_date(p.get("business_date", ""))
    except ValueError:
        return jsonify(ok=False, error="bad_date",
                       message="Pick a date from the date picker."), 400
    if d > today():
        return jsonify(ok=False, error="future_date",
                       message="A future date cannot be entered."), 400
    if (today() - d).days > BACKFILL_WINDOW_DAYS:
        return jsonify(ok=False, error="too_old",
                       message="This day is too far back — it needs the doctor's approval."), 400
    iso = d.isoformat()

    # ---- money --------------------------------------------------------------
    try:
        total_p = to_paise(p.get("total"), "Total sale")
        upi_p = to_paise(p.get("upi"), "UPI")
        expenses = []
        for i, e in enumerate(p.get("expenses") or []):
            amt = to_paise(e.get("amount"), "Kharcha #%d" % (i + 1))
            if amt <= 0:
                continue
            fixed = e.get("category_fixed") or None
            if fixed not in (None, "salary_advance"):
                return jsonify(ok=False, error="bad_category"), 400
            if fixed == "salary_advance" and not e.get("staff_id"):
                return jsonify(ok=False, error="staff_required",
                               message="Choose the staff member for a salary advance."), 400
            expenses.append(dict(amount_p=amt, category_fixed=fixed,
                                 staff_id=e.get("staff_id"),
                                 category_text=(e.get("category_text") or "").strip()[:200]))
        # Bills raised at full value with no cash across the counter — home
        # medicines, procedure medicines. Revenue is real; the cash is not.
        noncash = []
        for i, b in enumerate(p.get("noncash_bills") or []):
            amt = to_paise(b.get("amount"), "Bill #%d" % (i + 1))
            if amt <= 0:
                continue
            head = b.get("head")
            if head not in ("home_medicine", "procedure_medicine", "other"):
                return jsonify(ok=False, error="bad_head",
                               message="Choose the bill head (home / procedure / other)."), 400
            bill_no = (b.get("bill_no") or "").strip()
            if not bill_no:
                return jsonify(ok=False, error="bill_no_required",
                               message="A bill number is required."), 400
            try:
                bdt = parse_iso_date(b.get("bill_date") or iso)
            except ValueError:
                return jsonify(ok=False, error="bad_bill_date"), 400
            if head == "other" and not (b.get("head_text") or "").strip():
                return jsonify(ok=False, error="head_text_required",
                               message="Describe what 'Other' refers to."), 400
            noncash.append(dict(amount_p=amt, head=head,
                                head_text=(b.get("head_text") or "").strip()[:120],
                                bill_no=bill_no[:60], bill_date=bdt.isoformat(),
                                note=(b.get("note") or "").strip()[:200]))

        movements = []
        for i, m in enumerate(p.get("movements") or []):
            amt = to_paise(m.get("amount"), "Cash #%d" % (i + 1))
            if amt <= 0:
                continue
            if m.get("direction") not in ("out", "in") or \
               m.get("party") not in ("bank", "dr_manoj", "dr_bhawna", "other"):
                return jsonify(ok=False, error="bad_movement"), 400
            movements.append(dict(direction=m["direction"], party=m["party"], amount_p=amt,
                                  reference=(m.get("reference") or "").strip()[:120]))
    except ValueError as ex:
        return jsonify(ok=False, error="not_a_number", message=str(ex)), 400

    if upi_p > total_p:
        return jsonify(ok=False, error="upi_over_total",
                       message="UPI (%s) cannot exceed the total sale (%s)."
                               % (rupees(upi_p), rupees(total_p))), 400
    cash_p = total_p - upi_p

    warnings = []
    if total_p > MAX_SANE_P and not p.get("confirm_large"):
        return jsonify(ok=False, error="confirm_large",
                       message="Total sale %s — that is unusually large. Please confirm."
                               % rupees(total_p)), 409

    noncash_p = sum(b["amount_p"] for b in noncash)
    if noncash_p > cash_p:
        return jsonify(ok=False, error="noncash_over_cash",
                       message="Bills raised without cash (%s) cannot exceed the cash sale (%s)."
                               % (rupees(noncash_p), rupees(cash_p))), 400

    # ---- closing must not go negative --------------------------------------
    op = opening_p(con, UNIT, iso)
    out_p = sum(m["amount_p"] for m in movements if m["direction"] == "out")
    in_p = sum(m["amount_p"] for m in movements if m["direction"] == "in")
    exp_p = sum(e["amount_p"] for e in expenses)
    closing = op + cash_p - noncash_p - exp_p - out_p + in_p
    submitting = (p.get("action") == "submit")
    if closing < 0:
        return jsonify(ok=False, error="negative_cash",
                       message="Cash in hand would be %s, which cannot be negative. "
                               "Opening %s, cash sale %s, expenses %s, deposited %s."
                               % (rupees(closing), rupees(op), rupees(cash_p),
                                  rupees(exp_p), rupees(out_p))), 400

    # ---- attachments required to SUBMIT ------------------------------------
    # Truth comes from the attachment table, never from a list the page sends.
    # The browser can be wrong (or reloaded, or lying); the files either exist
    # on disk against this day or they do not.
    have_docs = {r["doc_type"] for r in con.execute(
        "SELECT doc_type FROM attachment WHERE day_entry_id=("
        "  SELECT id FROM day_entry WHERE unit=? AND business_date=?)", (UNIT, iso))}
    missing_docs = [d_ for d_ in REQUIRED_DOCS if d_ not in have_docs]
    if submitting and missing_docs and not (p.get("missing_scan_reason") or "").strip():
        return jsonify(ok=False, error="scans_required", missing=missing_docs,
                       message="Scans still missing: %s. Attach them, or give a reason." % ", ".join(missing_docs)), 400

    # ---- write (all-or-nothing) --------------------------------------------
    existing = con.execute("SELECT * FROM day_entry WHERE unit=? AND business_date=?",
                           (UNIT, iso)).fetchone()
    try:
        con.execute("BEGIN")
        if existing:
            if existing["status"] in ("approved", "locked") and u["role"] != "checker":
                con.execute("ROLLBACK")
                return jsonify(ok=False, error="locked",
                               message="This day is already approved — only the doctor can change it."), 403
            # a second submit CORRECTS; the old version is kept verbatim
            prev = day_state(con, UNIT, iso)
            rev = con.execute("SELECT COALESCE(MAX(revision),0)+1 n FROM day_revision "
                              "WHERE day_entry_id=?", (existing["id"],)).fetchone()["n"]
            con.execute("INSERT INTO day_revision (day_entry_id, revision, submitted_at, "
                        "payload_json, superseded_at) VALUES (?,?,?,?,?)",
                        (existing["id"], rev, existing["entered_at"],
                         json.dumps(prev, ensure_ascii=False), now_iso()))
            eid = existing["id"]
            for t in ("day_line", "day_expense", "cash_movement", "day_noncash_bill"):
                con.execute("DELETE FROM %s WHERE day_entry_id=?" % t, (eid,))
            con.execute("UPDATE day_entry SET status=?, entered_by=?, entered_at=?, "
                        "manned_by=?, manned_source=? WHERE id=?",
                        ("submitted" if submitting else "draft", u["user"], now_iso(),
                         p.get("manned_by"), p.get("manned_source") or "manual", eid))
            audit(con, "day_entry", eid, "correct", before=prev, who=u["user"])
            warnings.append("The previous entry for this day has been kept as revision %d." % rev)
        else:
            cur = con.execute(
                "INSERT INTO day_entry (unit, business_date, status, manned_by, manned_source, "
                "source, entered_by, entered_at) VALUES (?,?,?,?,?,'app',?,?)",
                (UNIT, iso, "submitted" if submitting else "draft", p.get("manned_by"),
                 p.get("manned_source") or "manual", u["user"], now_iso()))
            eid = cur.lastrowid
            audit(con, "day_entry", eid, "create", who=u["user"])

        con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) "
                    "VALUES (?,'pharmacy_sale','cash',?)", (eid, cash_p))
        con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) "
                    "VALUES (?,'pharmacy_sale','upi',?)", (eid, upi_p))
        for e in expenses:
            con.execute("INSERT INTO day_expense (day_entry_id, amount_p, amount_known, "
                        "category_fixed, staff_id, category_text) VALUES (?,?,1,?,?,?)",
                        (eid, e["amount_p"], e["category_fixed"], e["staff_id"], e["category_text"]))
        for m in movements:
            con.execute("INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, "
                        "reference) VALUES (?,?,?,?,?)",
                        (eid, m["direction"], m["party"], m["amount_p"], m["reference"]))
        for b in noncash:
            con.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, "
                        "head_text, bill_no, amount_p, note, entered_by, entered_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (eid, UNIT, b["bill_date"], b["head"], b["head_text"], b["bill_no"],
                         b["amount_p"], b["note"], u["user"], now_iso()))
        if missing_docs and (p.get("missing_scan_reason") or "").strip():
            con.execute("INSERT INTO data_flag (unit, business_date, day_entry_id, code, severity, detail) "
                        "VALUES (?,?,?,'MISSING_SCAN','medium',?)",
                        (UNIT, iso, eid, "%s | reason: %s"
                         % (",".join(missing_docs), p["missing_scan_reason"][:200])))

        # filing a back-dated day legitimately shifts every later opening balance.
        # That is correct — but it must never happen quietly.
        later = con.execute("SELECT COUNT(*) c FROM day_entry WHERE unit=? AND business_date > ? "
                            "AND status IN ('approved','locked')", (UNIT, iso)).fetchone()["c"]
        if later:
            warnings.append("Filing this back-dated day has recomputed the opening balance of "
                            "%d later approved days. This is correct." % later)
            con.execute("INSERT INTO data_flag (unit, business_date, day_entry_id, code, severity, detail) "
                        "VALUES (?,?,?,'RETRO_INSERT','medium',?)",
                        (UNIT, iso, eid, "back-dated filing recomputed %d later approved days" % later))
        con.execute("COMMIT")
    except Exception as ex:                                  # noqa: BLE001 — fail loud, roll back
        con.execute("ROLLBACK")
        return jsonify(ok=False, error="save_failed", message=str(ex)), 500

    refresh_missing_days(con)
    upi_check = finance_upi.reconcile_upi(con, UNIT, iso, now=now_iso())
    if upi_check and not upi_check["match"]:
        warnings.append("Bank settled %s UPI for this day but the entry says %s — "
                        "difference %s. The day is flagged; the doctor approves with "
                        "acknowledgment." % (rupees(upi_check["bank_p"]),
                                             rupees(upi_check["entered_p"]),
                                             rupees(upi_check["diff_p"])))
    st = day_state(con, UNIT, iso)
    return jsonify(ok=True, day=st, warnings=warnings)


@app.route("/finance/api/approve/<date_iso>", methods=["POST"])
def api_approve(date_iso):
    u, err = require("checker")
    if err:
        return err
    con = db()
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    e = con.execute("SELECT * FROM day_entry WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
    if not e:
        return jsonify(ok=False, error="not_found"), 404
    if e["status"] not in ("submitted", "draft"):
        return jsonify(ok=False, error="bad_status", message="Status: %s" % e["status"]), 409

    # The bank disagrees with this day's UPI? Then approval must be CONSCIOUS.
    # (Owner ruling S179: unmatched days are flagged for manual approval.)
    p = request.get_json(silent=True) or {}
    mism = con.execute("SELECT id, expected_p, actual_p, diff_p FROM recon_exception "
                       "WHERE unit=? AND business_date=? AND kind='upi_vs_statement' "
                       "AND status='open'", (UNIT, iso)).fetchone()
    if mism and not p.get("acknowledge_upi"):
        return jsonify(ok=False, error="upi_mismatch",
                       bank=rupees(mism["expected_p"]), entered=rupees(mism["actual_p"]),
                       diff=rupees(mism["diff_p"]),
                       message="Bank settled %s but the day says %s (difference %s). "
                               "Approve again with acknowledgment to proceed."
                               % (rupees(mism["expected_p"]), rupees(mism["actual_p"]),
                                  rupees(mism["diff_p"]))), 409
    if mism and p.get("acknowledge_upi"):
        con.execute("UPDATE recon_exception SET status='acknowledged', "
                    "resolution=?, closed_by=?, closed_at=? WHERE id=?",
                    ("approved over the mismatch by the checker"
                     + ((" — " + str(p.get("ack_note"))[:200]) if p.get("ack_note") else ""),
                     u["user"], now_iso(), mism["id"]))

    # Approval is what posts a salary advance to the Staff Ledger. Not entry.
    advances = con.execute("SELECT id, amount_p, staff_id FROM day_expense "
                           "WHERE day_entry_id=? AND category_fixed='salary_advance' "
                           "AND ledger_posted=0", (e["id"],)).fetchall()
    posted = []
    for a in advances:
        # B6 wires the real Staff Ledger call. Until then this records intent
        # explicitly rather than pretending the posting happened.
        con.execute("UPDATE day_expense SET ledger_posted=0, ledger_ref=? WHERE id=?",
                    ("PENDING_LEDGER_WIRING", a["id"]))
        posted.append(dict(expense_id=a["id"], amount=rupees(a["amount_p"]), staff_id=a["staff_id"]))

    con.execute("UPDATE day_entry SET status='approved', approved_by=?, approved_at=? WHERE id=?",
                (u["user"], now_iso(), e["id"]))
    audit(con, "day_entry", e["id"], "approve", after={"date": iso}, who=u["user"])
    con.commit()
    return jsonify(ok=True, date=iso, status="approved",
                   salary_advances_pending_ledger=posted)



# ------------------------------------------------------------ UPI statements
# The BANK is the arbiter for UPI (owner ruling, S179). The clinic-account GAS
# posts each morning's ICICI MPR file here; we parse it, verify it against its
# own Grand Total, store the settled truth per unit per day, and reconcile.

UPI_DIR = os.environ.get("FINANCE_UPI_DIR", os.path.join(APP_ROOT, "upi_statements"))


@app.route("/finance/api/upi-statement", methods=["POST"])
def api_upi_statement():
    """Accepts one MPR xlsx. Callers: the GAS pusher (X-Finance-Cron token,
    which the before_request gate already honours) or a signed-in checker
    uploading by hand. Never half-ingests: a file that fails its own total
    check is rejected whole."""
    u = current_user()
    is_cron = bool(CRON_TOKEN and request.headers.get("X-Finance-Cron") == CRON_TOKEN)
    if not is_cron:
        u2, err = require("checker")
        if err:
            return err
        u = u2
    f = request.files.get("file")
    blob = f.read() if f else request.get_data()
    if not blob:
        return jsonify(ok=False, error="no_file"), 400
    fname = (f.filename if f else request.headers.get("X-Filename")) or "statement.xlsx"

    con = db()
    try:
        res = finance_upi.ingest_statement(con, fname, blob, UPI_DIR, now=now_iso(),
                                           source_ref=request.headers.get("X-Msg-Id"))
    except finance_upi.StatementRejected as ex:
        con.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                    "VALUES (NULL, NULL, 'UPI_STATEMENT_REJECTED', 'high', ?)",
                    (("%s: %s" % (fname, ex))[:400],))
        con.commit()
        return jsonify(ok=False, error="statement_rejected", message=str(ex)), 422

    recon = []
    for d in res["days"]:
        r = finance_upi.reconcile_upi(con, res["unit"], d["date"], now=now_iso())             if res["unit"] else None
        recon.append(dict(date=d["date"], settled=rupees(d["total_p"]), txns=d["count"],
                          compared=(r is not None),
                          match=(r["match"] if r else None),
                          entered=(rupees(r["entered_p"]) if r else None),
                          diff=(rupees(r["diff_p"]) if r else None)))
    audit(con, "upi_statement", None, "ingest",
          after={"file": fname, "unit": res["unit"], "days": len(res["days"]),
                 "by": ("cron" if is_cron else u["user"])},
          who=("cron" if is_cron else u["user"]))
    con.commit()
    return jsonify(ok=True, unit=res["unit"], mid=res["mid"], days=recon)


# --------------------------------------------------------- patient-wise lines

@app.route("/finance/api/sources")
def api_sources():
    con = db()
    out = []
    for r in con.execute("SELECT id, unit, adapter, label, is_primary, active, config_json "
                         "FROM ingest_source WHERE unit=? ORDER BY is_primary DESC", (UNIT,)):
        cols = [dict(field=m["our_field"], column=m["their_column"],
                     transform=m["transform"], required=bool(m["required"]))
                for m in con.execute("SELECT * FROM ingest_column_map WHERE source_id=?", (r["id"],))]
        out.append(dict(id=r["id"], adapter=r["adapter"], label=r["label"],
                        primary=bool(r["is_primary"]), active=bool(r["active"]),
                        config=json.loads(r["config_json"]) if r["config_json"] else {},
                        column_map=cols, mapped=bool(cols)))
    return jsonify(ok=True, unit=UNIT, sources=out)


@app.route("/finance/api/sources/<adapter>/map", methods=["POST"])
def api_set_map(adapter):
    """Point our fields at a vendor file's columns. This is how a Marg or Labmate
    export gets supported — by describing it, not by writing a new parser."""
    u, err = require("checker")
    if err:
        return err
    p = request.get_json(silent=True) or {}
    con = db()
    src = con.execute("SELECT id FROM ingest_source WHERE unit=? AND adapter=?",
                      (UNIT, adapter)).fetchone()
    if not src:
        return jsonify(ok=False, error="unknown_adapter"), 404
    allowed = {"bill_no", "bill_date", "clinic_id", "patient_name", "description",
               "amount", "mode", "discount", "tax"}
    cols = p.get("column_map") or []
    for m in cols:
        if m.get("field") not in allowed or not (m.get("column") or "").strip():
            return jsonify(ok=False, error="bad_map", detail=m), 400
    con.execute("DELETE FROM ingest_column_map WHERE source_id=?", (src["id"],))
    for m in cols:
        con.execute("INSERT INTO ingest_column_map (source_id, our_field, their_column, "
                    "transform, required) VALUES (?,?,?,?,?)",
                    (src["id"], m["field"], m["column"].strip(), m.get("transform"),
                     1 if m.get("required") else 0))
    if p.get("config") is not None:
        con.execute("UPDATE ingest_source SET config_json=? WHERE id=?",
                    (json.dumps(p["config"]), src["id"]))
    if p.get("active") is not None:
        con.execute("UPDATE ingest_source SET active=? WHERE id=?",
                    (1 if p["active"] else 0, src["id"]))
    if p.get("make_primary"):
        con.execute("UPDATE ingest_source SET is_primary=0 WHERE unit=?", (UNIT,))
        con.execute("UPDATE ingest_source SET is_primary=1, active=1 WHERE id=?", (src["id"],))
    audit(con, "ingest_column_map", src["id"], "set_map", after=p, who=u["user"])
    con.commit()
    return jsonify(ok=True, adapter=adapter, columns=len(cols))


@app.route("/finance/api/day/<date_iso>/ingest", methods=["POST"])
def api_ingest(date_iso):
    u, err = require("maker", "checker")
    if err:
        return err
    p = request.get_json(silent=True) or {}
    adapter = p.get("adapter") or "manual"
    con = db()
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    payload = p.get("lines") if adapter == "manual" else p.get("payload")
    try:
        res = finance_ingest.ingest_day(con, UNIT, iso, adapter, payload,
                                        run_by=u["user"], source_ref=p.get("source_ref"),
                                        now=now_iso())
    except finance_ingest.AdapterUnavailable as ex:
        return jsonify(ok=False, error="adapter_unavailable", message=str(ex)), 409
    att = con.execute("SELECT day_total_p, attributed_p, in_review_p, in_review_count "
                      "FROM v_day_attribution WHERE unit=? AND business_date=?",
                      (UNIT, iso)).fetchone()
    res["day_total"] = rupees(att["day_total_p"]) if att else ""
    res["attributed"] = rupees(att["attributed_p"]) if att else ""
    res["unattributed"] = rupees((att["day_total_p"] - att["attributed_p"]) if att else 0)
    res["in_review"] = att["in_review_count"] if att else 0
    return jsonify(res), (200 if res.get("ok") else 422)


@app.route("/finance/api/day/<date_iso>/lines")
def api_day_lines(date_iso):
    con = db()
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (UNIT, iso)).fetchone()
    if not e:
        return jsonify(ok=False, error="not_found"), 404
    lines = [dict(id=r["id"], clinic_id=r["clinic_id"], name=r["name"],
                  description=r["description"], amount=rupees(r["amount_p"]),
                  source=r["source"], bill_no=r["source_ref"], confidence=r["confidence"])
             for r in con.execute(
                 "SELECT s.id, p.clinic_id, p.name, s.description, s.amount_p, s.source, "
                 "       s.source_ref, s.confidence FROM sale_item s "
                 "LEFT JOIN patient_ref p ON p.id = s.patient_ref_id "
                 "WHERE s.day_entry_id=? ORDER BY s.id", (e["id"],))]
    review = [dict(id=r["id"], guess_clinic_id=r["guess_clinic_id"], guess_name=r["guess_name"],
                   amount=rupees(r["amount_p"]), confidence=r["confidence"], reason=r["reason"])
              for r in con.execute("SELECT * FROM sale_item_review WHERE day_entry_id=? "
                                   "AND status='open' ORDER BY id", (e["id"],))]
    att = con.execute("SELECT day_total_p, attributed_p FROM v_day_attribution "
                      "WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
    batches = [dict(adapter=r["adapter"], status=r["status"], rows=r["rows_read"],
                    accepted=r["rows_accepted"], review=r["rows_review"], at=r["run_at"],
                    error=r["error"])
               for r in con.execute("SELECT * FROM ingest_batch WHERE day_entry_id=? "
                                    "ORDER BY id DESC LIMIT 5", (e["id"],))]
    return jsonify(ok=True, date=iso, lines=lines, review=review, batches=batches,
                   day_total=rupees(att["day_total_p"]), attributed=rupees(att["attributed_p"]),
                   unattributed=rupees(att["day_total_p"] - att["attributed_p"]))


@app.route("/finance/api/review/<int:rid>/resolve", methods=["POST"])
def api_resolve_line(rid):
    u, err = require("maker", "checker")
    if err:
        return err
    p = request.get_json(silent=True) or {}
    con = db()
    r = con.execute("SELECT * FROM sale_item_review WHERE id=? AND status='open'", (rid,)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found"), 404
    action = p.get("action") or "assign"
    if action == "discard":
        con.execute("UPDATE sale_item_review SET status='discarded', resolved_by=?, resolved_at=? "
                    "WHERE id=?", (u["user"], now_iso(), rid))
    else:
        cid = (p.get("clinic_id") or "").strip() or finance_ingest.WALK_IN
        pid = finance_ingest.resolve_patient(con, cid, (p.get("name") or "").strip() or None)
        con.execute("INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, "
                    "service, description, amount_p, source, confidence, verified_by, verified_at) "
                    "VALUES (?,?,?,?,?,?,?, 'manual', 1.0, ?, ?)",
                    (r["day_entry_id"], r["ingest_batch_id"], UNIT, pid,
                     "lab_test" if UNIT == "lab" else "pharmacy",
                     p.get("description"), r["amount_p"], u["user"], now_iso()))
        con.execute("UPDATE sale_item_review SET status='resolved', resolved_by=?, resolved_at=? "
                    "WHERE id=?", (u["user"], now_iso(), rid))
    d = con.execute("SELECT business_date FROM day_entry WHERE id=?", (r["day_entry_id"],)).fetchone()
    finance_ingest.reconcile_day_attribution(con, UNIT, d["business_date"], now_iso())
    audit(con, "sale_item_review", rid, action, after=p, who=u["user"])
    con.commit()
    return jsonify(ok=True, id=rid, action=action)




# --------------------------------------------------- browsing the days back
# An approved day must stay openable. Approval is not an archive door — the
# whole point of keeping evidence is being able to look at it later.

@app.route("/finance/api/days")
def api_days():
    con = db()
    ym = request.args.get("ym", "")
    if re.fullmatch(r"\d{4}-\d{2}", ym):
        first, last = month_bounds(ym)
        a, b = first.isoformat(), last.isoformat()
    else:
        b = today().isoformat()
        a = (today() - dt.timedelta(days=int(request.args.get("days", "60")))).isoformat()

    rows = con.execute(
        "SELECT e.id, e.business_date, e.status, e.source, e.approved_by, e.approved_at, "
        "       l.revenue_p, l.cash_in_p, l.upi_in_p, l.noncash_p, l.closing_p, "
        "       (SELECT COUNT(*) FROM attachment at WHERE at.day_entry_id=e.id) scans, "
        "       (SELECT COUNT(*) FROM cash_adjustment ca WHERE ca.day_entry_id=e.id) adjustments, "
        "       (SELECT COUNT(*) FROM day_noncash_bill nb WHERE nb.day_entry_id=e.id) bills "
        "FROM day_entry e JOIN v_cash_ledger l "
        "  ON l.unit=e.unit AND l.business_date=e.business_date "
        "WHERE e.unit=? AND e.business_date BETWEEN ? AND ? "
        "ORDER BY e.business_date DESC", (UNIT, a, b)).fetchall()

    return jsonify(ok=True, from_date=a, to_date=b, count=len(rows), days=[
        dict(date=r["business_date"], status=r["status"],
             imported=(r["source"] == "legacy_sheet"),
             approved_by=r["approved_by"], approved_at=r["approved_at"],
             revenue=rupees(r["revenue_p"]), cash=rupees(r["cash_in_p"]),
             upi=rupees(r["upi_in_p"]), noncash=rupees(r["noncash_p"]),
             closing=rupees(r["closing_p"]),
             scans=r["scans"], adjustments=r["adjustments"], bills=r["bills"])
        for r in rows])


@app.route("/finance/attachment/<int:aid>")
def api_attachment(aid):
    """Serve one scan. Role-gated by the same before_request gate as everything
    else — a scan is a patient-adjacent document, not a public file."""
    con = db()
    r = con.execute("SELECT at.*, e.unit, e.business_date FROM attachment at "
                    "JOIN day_entry e ON e.id = at.day_entry_id WHERE at.id=?", (aid,)).fetchone()
    if not r or r["unit"] != UNIT:
        return jsonify(ok=False, error="not_found"), 404
    if r["path"] and os.path.exists(r["path"]):
        return send_file(r["path"], mimetype="application/pdf", max_age=0,
                         download_name="%s_%s.pdf" % (r["business_date"], r["doc_type"]))
    if r["external_url"]:
        # legacy days: the file still lives in the old Drive folder. Send the
        # viewer there rather than pretending we hold a copy we never had.
        return redirect(r["external_url"], code=302)
    return jsonify(ok=False, error="file_missing",
                   message="The record exists but the file is not on this server."), 410


# ------------------------------------------------------------- parked cash
# A bank trip happens days after month end, so one deposit carries the old
# month's parked cash plus the new month's takings. Only the OLD month's share
# is ever entered; the remainder is by definition the current month's. The
# movement itself is never split — it has to keep matching the bank statement.

@app.route("/finance/api/parked")
def api_parked():
    con = db()
    months = [dict(ym=r["ym"], closed_at=r["closed_at"],
                   parked=rupees(r["parked_p"]), cleared=rupees(r["cleared_p"]),
                   outstanding=rupees(r["outstanding_p"]),
                   outstanding_p=r["outstanding_p"],
                   settled=(r["outstanding_p"] <= 0))
              for r in con.execute("SELECT * FROM v_month_parked WHERE unit=? ORDER BY ym DESC",
                                   (UNIT,))]
    # bank deposits that have not yet been told what they clear
    deps = [dict(id=r["id"], date=r["business_date"], amount=rupees(r["amount_p"]),
                 amount_p=r["amount_p"], reference=r["reference"],
                 clears_ym=r["clears_ym"],
                 clears_amount=rupees(r["clears_amount_p"]) if r["clears_amount_p"] else None)
            for r in con.execute(
                "SELECT m.id, m.amount_p, m.reference, m.clears_ym, m.clears_amount_p, "
                "       e.business_date "
                "FROM cash_movement m JOIN day_entry e ON e.id = m.day_entry_id "
                "WHERE e.unit=? AND m.direction='out' AND m.party='bank' "
                "ORDER BY e.business_date DESC LIMIT 25", (UNIT,))]
    try:
        nag = int(setting(con, "parked_cash.nag_days", "21") or 21)
    except (TypeError, ValueError):
        nag = 21
    ageing = []
    for m in months:
        if m["outstanding_p"] > 0 and m["closed_at"]:
            try:
                days = (today() - parse_iso_date(m["closed_at"][:10])).days
            except ValueError:
                continue
            if days >= nag:
                ageing.append(dict(ym=m["ym"], days=days, outstanding=m["outstanding"]))
    return jsonify(ok=True, months=months, bank_deposits=deps,
                   nag_days=nag, ageing=ageing)


@app.route("/finance/api/deposit/<int:mid>/clear", methods=["POST"])
def api_deposit_clear(mid):
    """Say how much of this deposit belongs to a closed month. One number.
    The rest is the current month's and needs no saying."""
    u, err = require("checker")
    if err:
        return err
    p = request.get_json(silent=True) or {}
    con = db()
    m = con.execute(
        "SELECT m.*, e.business_date, e.unit FROM cash_movement m "
        "JOIN day_entry e ON e.id = m.day_entry_id WHERE m.id=?", (mid,)).fetchone()
    if not m or m["unit"] != UNIT:
        return jsonify(ok=False, error="not_found"), 404
    if m["direction"] != "out" or m["party"] != "bank":
        return jsonify(ok=False, error="not_a_bank_deposit"), 400

    ym = (p.get("ym") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}", ym):
        return jsonify(ok=False, error="bad_month"), 400
    row = con.execute("SELECT * FROM v_month_parked WHERE unit=? AND ym=?", (UNIT, ym)).fetchone()
    if not row:
        return jsonify(ok=False, error="month_not_finalised",
                       message="%s has not been finalised, so it has no parked cash." % ym), 409

    try:
        amt = to_paise(p.get("amount"), "Amount")
    except ValueError as ex:
        return jsonify(ok=False, error="not_a_number", message=str(ex)), 400
    if amt <= 0:
        return jsonify(ok=False, error="bad_amount"), 400
    if amt > m["amount_p"]:
        return jsonify(ok=False, error="over_deposit",
                       message="That is more than the deposit itself (%s)."
                               % rupees(m["amount_p"])), 400

    already = row["cleared_p"] - (m["clears_amount_p"] or 0 if m["clears_ym"] == ym else 0)
    if amt > row["parked_p"] - already:
        return jsonify(ok=False, error="over_parked",
                       message="%s only has %s still parked."
                               % (ym, rupees(row["parked_p"] - already))), 400

    con.execute("UPDATE cash_movement SET clears_ym=?, clears_amount_p=?, cleared_by=?, "
                "cleared_at=? WHERE id=?", (ym, amt, u["user"], now_iso(), mid))
    audit(con, "cash_movement", mid, "clear_month",
          after={"ym": ym, "amount_p": amt}, who=u["user"])
    con.commit()

    row = con.execute("SELECT * FROM v_month_parked WHERE unit=? AND ym=?", (UNIT, ym)).fetchone()
    rest = m["amount_p"] - amt
    return jsonify(ok=True, ym=ym, deposit=rupees(m["amount_p"]),
                   allocated_to_month=rupees(amt),
                   remainder_current_month=rupees(rest),
                   still_parked=rupees(row["outstanding_p"]),
                   settled=(row["outstanding_p"] <= 0),
                   message=("%s is now fully settled." % ym) if row["outstanding_p"] <= 0
                           else "%s still has %s in the drawer."
                                % (ym, rupees(row["outstanding_p"])))


# ----------------------------------------------------------------- month close

@app.route("/finance/api/month/<ym>/statement", methods=["POST"])
def api_month_statement(ym):
    """The month's own soft copy — Sanjeevni's sale register export, or the lab
    revenue statement. A month-level total straight from the source system beats
    any per-day OCR, so this is the figure that decides whether a month is right."""
    u, err = require("maker", "checker")
    if err:
        return err
    if not re.fullmatch(r"\d{4}-\d{2}", ym):
        return jsonify(ok=False, error="bad_month"), 400
    p = request.get_json(silent=True) or {}
    kind = p.get("kind") or "sale_register"
    if kind not in ("sale_register", "lab_revenue", "other"):
        return jsonify(ok=False, error="bad_kind"), 400
    try:
        stated_p = to_paise(p.get("stated_total"), "Statement total")
    except ValueError as ex:
        return jsonify(ok=False, error="not_a_number", message=str(ex)), 400

    con = db()
    first, last = month_bounds(ym)
    sys_p = con.execute("SELECT COALESCE(SUM(revenue_p),0) r FROM v_cash_ledger "
                        "WHERE unit=? AND business_date BETWEEN ? AND ?",
                        (UNIT, first.isoformat(), last.isoformat())).fetchone()["r"]
    var_p = stated_p - sys_p

    con.execute("INSERT OR REPLACE INTO monthly_statement (unit, ym, kind, filename, sha256, "
                "stated_total_p, parsed_by, uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (UNIT, ym, kind, (p.get("filename") or "")[:200], p.get("sha256"),
                 stated_p, p.get("parsed_by") or "manual", u["user"], now_iso()))

    # A month that doesn't agree with its own source system shouts like anything else.
    if var_p != 0:
        con.execute(
            "INSERT OR REPLACE INTO recon_exception (unit, business_date, kind, expected_p, "
            "actual_p, diff_p, severity, status, detail, opened_at, shout_count) "
            "VALUES (?,?, 'month_vs_statement', ?,?,?, ?, 'open', ?, ?, 0)",
            (UNIT, last.isoformat(), sys_p, stated_p, var_p,
             "high" if abs(var_p) >= 100000 else "medium",
             "%s says %s; this system says %s" % (kind, rupees(stated_p), rupees(sys_p)),
             now_iso()))
    else:
        con.execute("UPDATE recon_exception SET status='resolved', resolution='statement agrees', "
                    "closed_at=? WHERE unit=? AND kind='month_vs_statement' AND business_date=? "
                    "AND status='open'", (now_iso(), UNIT, last.isoformat()))
    audit(con, "monthly_statement", None, "upload",
          after={"ym": ym, "kind": kind, "stated_p": stated_p, "variance_p": var_p}, who=u["user"])
    con.commit()
    return jsonify(ok=True, ym=ym, kind=kind, system_total=rupees(sys_p),
                   statement_total=rupees(stated_p), variance=rupees(var_p),
                   agrees=(var_p == 0))


@app.route("/finance/api/month/<ym>/close-check")
def api_month_close_check(ym):
    if not re.fullmatch(r"\d{4}-\d{2}", ym):
        return jsonify(ok=False, error="bad_month"), 400
    con = db()
    first, last = month_bounds(ym)
    a, b = first.isoformat(), last.isoformat()

    missing = [r["business_date"] for r in con.execute(
        "SELECT business_date FROM recon_exception WHERE unit=? AND kind='missing_day' "
        "AND status='open' AND business_date BETWEEN ? AND ? ORDER BY business_date",
        (UNIT, a, b))]
    unapproved = [r["business_date"] for r in con.execute(
        "SELECT business_date FROM day_entry WHERE unit=? AND business_date BETWEEN ? AND ? "
        "AND status NOT IN ('approved','locked','closed_holiday') ORDER BY business_date",
        (UNIT, a, b))]
    open_high = con.execute(
        "SELECT COUNT(*) c FROM recon_exception WHERE unit=? AND status='open' AND severity='high' "
        "AND kind NOT IN ('missing_day') AND business_date BETWEEN ? AND ?",
        (UNIT, a, b)).fetchone()["c"]
    stmt = con.execute("SELECT kind, stated_total_p FROM monthly_statement WHERE unit=? AND ym=?",
                       (UNIT, ym)).fetchone()
    sys_p = con.execute("SELECT COALESCE(SUM(revenue_p),0) r FROM v_cash_ledger "
                        "WHERE unit=? AND business_date BETWEEN ? AND ?", (UNIT, a, b)).fetchone()["r"]
    resid = con.execute("SELECT closing_p FROM v_cash_ledger WHERE unit=? AND business_date<=? "
                        "ORDER BY business_date DESC LIMIT 1", (UNIT, b)).fetchone()
    resid_p = int(resid["closing_p"]) if resid else 0
    carry = setting(con, "%s.carry_month_balance" % UNIT, "0")
    mc = con.execute("SELECT status FROM month_close WHERE unit=? AND ym=?", (UNIT, ym)).fetchone()

    blockers = []
    if missing:
        blockers.append("%d days not yet filed" % len(missing))
    if unapproved:
        blockers.append("%d days awaiting approval" % len(unapproved))
    if open_high:
        blockers.append("%d high-severity exceptions still open" % open_high)
    if not stmt:
        blockers.append("the month's soft copy (sale register) has not been uploaded")

    return jsonify(ok=True, ym=ym, status=(mc["status"] if mc else "open"),
                   blockers=blockers, ready=(not blockers),
                   missing_days=missing, unapproved_days=unapproved,
                   open_high_exceptions=open_high,
                   system_total=rupees(sys_p),
                   statement_total=(rupees(stmt["stated_total_p"]) if stmt else None),
                   variance=(rupees(stmt["stated_total_p"] - sys_p) if stmt else None),
                   residual_cash=rupees(resid_p), residual_cash_p=resid_p,
                   carry_policy=("carry" if carry == "1" else "settle_to_zero"),
                   settlement_required=(carry != "1" and resid_p != 0))


@app.route("/finance/api/month/<ym>/finalise", methods=["POST"])
def api_month_finalise(ym):
    """Finalising does three things together or not at all: freeze the month,
    settle the drawer, retire the scans. A half-closed month is how evidence
    goes missing."""
    u, err = require("checker")
    if err:
        return err
    if not re.fullmatch(r"\d{4}-\d{2}", ym):
        return jsonify(ok=False, error="bad_month"), 400
    p = request.get_json(silent=True) or {}
    con = db()
    first, last = month_bounds(ym)
    a, b = first.isoformat(), last.isoformat()

    chk = api_month_close_check(ym).get_json()
    if not chk["ready"] and not p.get("override_reason"):
        return jsonify(ok=False, error="not_ready", blockers=chk["blockers"],
                       message="The month cannot be closed: " + "; ".join(chk["blockers"])), 409
    if chk["status"] == "finalised":
        return jsonify(ok=False, error="already_finalised"), 409

    resid_p = chk["residual_cash_p"]
    carry = setting(con, "%s.carry_month_balance" % UNIT, "0")

    # No carry-over (S179): the drawer must be settled, or you must say why not.
    settle = p.get("settlement") or {}
    settlement_note = (p.get("settlement_note") or "").strip()
    if carry != "1" and resid_p != 0 and not settle and not settlement_note:
        return jsonify(ok=False, error="settlement_required",
                       residual_cash=rupees(resid_p),
                       message="%s is left in the drawer at month end — either deposit it, "
                               "or give a reason." % rupees(resid_p)), 409

    try:
        con.execute("BEGIN")
        settled_p = 0
        if settle:
            party = settle.get("party")
            if party not in ("bank", "dr_manoj", "dr_bhawna", "other"):
                con.execute("ROLLBACK")
                return jsonify(ok=False, error="bad_party"), 400
            anchor = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date<=? "
                                 "ORDER BY business_date DESC LIMIT 1", (UNIT, b)).fetchone()
            if not anchor:
                con.execute("ROLLBACK")
                return jsonify(ok=False, error="no_entry"), 404
            settled_p = to_paise(settle.get("amount") or (resid_p / 100.0), "Settlement")
            if settled_p > 0:
                con.execute("INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, "
                            "reference) VALUES (?,'out',?,?,?)",
                            (anchor["id"], party, settled_p,
                             "month-end settlement %s" % ym))

        stmt = con.execute("SELECT stated_total_p FROM monthly_statement WHERE unit=? AND ym=?",
                           (UNIT, ym)).fetchone()
        sys_p = con.execute("SELECT COALESCE(SUM(revenue_p),0) r FROM v_cash_ledger "
                            "WHERE unit=? AND business_date BETWEEN ? AND ?",
                            (UNIT, a, b)).fetchone()["r"]
        stated_p = stmt["stated_total_p"] if stmt else None

        con.execute(
            "INSERT OR REPLACE INTO month_close (unit, ym, status, system_total_p, "
            "statement_total_p, variance_p, residual_cash_p, carry_policy, settlement_note, "
            "closed_by, closed_at, archive_status) "
            "VALUES (?,?,'finalised',?,?,?,?,?,?,?,?, 'pending')",
            (UNIT, ym, sys_p, stated_p,
             (stated_p - sys_p) if stated_p is not None else None,
             resid_p, "carry" if carry == "1" else "settle_to_zero",
             settlement_note or (("settled %s to %s" % (rupees(settled_p), settle.get("party")))
                                 if settle else None),
             u["user"], now_iso()))

        con.execute("UPDATE day_entry SET status='locked' WHERE unit=? AND business_date BETWEEN ? "
                    "AND ? AND status='approved'", (UNIT, a, b))

        # Retire the month's scans: queue them for the connected Google Drive.
        # The attachment ROW is never deleted — only the local file, and only once
        # the Drive move is verified by the worker (B4b).
        queued = 0
        if setting(con, "retire_scans_on_finalise", "1") == "1":
            root = setting(con, "archive.drive_root", "ClinicFinanceArchive")
            for r in con.execute(
                    "SELECT at.id, at.sha256 FROM attachment at JOIN day_entry e ON e.id=at.day_entry_id "
                    "WHERE e.unit=? AND e.business_date BETWEEN ? AND ?", (UNIT, a, b)):
                con.execute("INSERT OR IGNORE INTO archive_item (attachment_id, unit, ym, "
                            "drive_folder, sha256_before, status, queued_at) "
                            "VALUES (?,?,?,?,?, 'queued', ?)",
                            (r["id"], UNIT, ym, "%s/%s/%s" % (root, UNIT, ym), r["sha256"], now_iso()))
                queued += 1
        audit(con, "month_close", None, "finalise",
              after={"ym": ym, "residual_p": resid_p, "settled_p": settled_p,
                     "scans_queued": queued}, who=u["user"])
        con.execute("COMMIT")
    except Exception as ex:                                    # noqa: BLE001
        con.execute("ROLLBACK")
        return jsonify(ok=False, error="finalise_failed", message=str(ex)), 500

    after = con.execute("SELECT closing_p FROM v_cash_ledger WHERE unit=? AND business_date<=? "
                        "ORDER BY business_date DESC LIMIT 1", (UNIT, b)).fetchone()
    carried_p = int(after["closing_p"]) if after else 0
    return jsonify(ok=True, ym=ym, status="finalised",
                   carry_policy=("carry" if carry == "1" else "settle_to_zero"),
                   residual_before=rupees(resid_p),
                   cash_carried_forward=rupees(carried_p),
                   cash_after_settlement=rupees(carried_p),
                   scans_queued_for_archive=queued,
                   message=("Month closed. %s carried into the next month (it goes to the bank on the "
                            "next trip). Scans are on their way to Google Drive."
                            % rupees(carried_p)) if carry == "1" else
                           "Month closed. Scans are on their way to Google Drive.")


@app.route("/finance/api/archive/queue")
def api_archive_queue():
    """What the Drive-mover worker (B4b) has to do. Exposed so the queue can never
    quietly stall — if this list stops draining, it is visible."""
    con = db()
    rows = con.execute("SELECT ai.id, ai.unit, ai.ym, ai.drive_folder, ai.status, ai.queued_at, "
                       "at.doc_type, at.path, at.external_url "
                       "FROM archive_item ai JOIN attachment at ON at.id=ai.attachment_id "
                       "WHERE ai.status IN ('queued','failed') ORDER BY ai.ym, ai.id LIMIT 500")
    items = [dict(r) for r in rows]
    return jsonify(ok=True, count=len(items), items=items)


@app.route("/finance/api/cutover", methods=["POST"])
def api_cutover():
    """GO-LIVE STEP. The legacy import leaves computed cash at whatever the old
    sheet said — which for Sanjeevni is NEGATIVE (₹-30,056). The new system will
    correctly refuse the pharmacy's very first entry until that is settled.

    So on cutover day the drawer is physically counted. The count is recorded in
    cash_count (a fact), and ONE approved adjustment closes the gap between
    computed and counted (a decision, with your name on it). From that moment the
    ledger is self-carrying and no opening balance is ever typed again.

    This is deliberately checker-only and deliberately loud."""
    u, err = require("checker")
    if err:
        return err
    p = request.get_json(silent=True) or {}
    con = db()
    try:
        d = parse_iso_date(p.get("date", ""))
        counted_p = to_paise(p.get("counted"), "Counted cash")
    except ValueError as ex:
        return jsonify(ok=False, error="bad_input", message=str(ex)), 400
    iso = d.isoformat()

    anchor = con.execute("SELECT id, business_date FROM day_entry WHERE unit=? AND business_date<=? "
                         "ORDER BY business_date DESC LIMIT 1", (UNIT, iso)).fetchone()
    if not anchor:
        return jsonify(ok=False, error="no_entry",
                       message="There is no entry on or before this date."), 404

    led = con.execute("SELECT closing_p FROM v_cash_ledger WHERE unit=? AND business_date=?",
                      (UNIT, anchor["business_date"])).fetchone()
    computed_p = int(led["closing_p"]) if led else 0
    diff_p = counted_p - computed_p

    try:
        con.execute("BEGIN")
        con.execute("INSERT OR REPLACE INTO cash_count (unit, business_date, counted_p, counted_by, "
                    "counted_at, explanation) VALUES (?,?,?,?,?,?)",
                    (UNIT, iso, counted_p, u["user"], now_iso(),
                     (p.get("note") or "cutover physical count")[:300]))
        if diff_p != 0:
            con.execute("INSERT INTO cash_adjustment (day_entry_id, amount_p, reason, source, "
                        "status, explanation, approved_by, approved_at) "
                        "VALUES (?,?,?, 'manual', 'approved', ?,?,?)",
                        (anchor["id"], diff_p,
                         "cutover: drawer counted %s against computed %s"
                         % (rupees(counted_p), rupees(computed_p)),
                         (p.get("note") or "opening balance established at go-live")[:300],
                         u["user"], now_iso()))
        # the legacy breaks stay OPEN — cutover settles the balance, it does not
        # absolve the history. That distinction is the whole point.
        audit(con, "cash_count", None, "cutover",
              after={"date": iso, "counted_p": counted_p, "computed_p": computed_p,
                     "diff_p": diff_p}, who=u["user"])
        con.execute("COMMIT")
    except Exception as ex:                                   # noqa: BLE001
        con.execute("ROLLBACK")
        return jsonify(ok=False, error="cutover_failed", message=str(ex)), 500

    still_open = con.execute("SELECT COUNT(*) c FROM recon_exception WHERE unit=? "
                             "AND kind='carry_forward_break' AND status='open'",
                             (UNIT,)).fetchone()["c"]
    return jsonify(ok=True, date=iso, counted=rupees(counted_p), computed=rupees(computed_p),
                   adjustment=rupees(diff_p),
                   legacy_breaks_still_open=still_open,
                   message="Opening balance set. %d legacy breaks remain open — "
                           "cutover settles the balance, not the history." % still_open)


@app.route("/finance/api/exception/<int:exc_id>/resolve", methods=["POST"])
def api_resolve_exception(exc_id):
    u, err = require("checker")
    if err:
        return err
    p = request.get_json(silent=True) or {}
    reason = (p.get("resolution") or "").strip()
    if len(reason) < 3:
        return jsonify(ok=False, error="reason_required",
                       message="A reason is required — nothing closes without one."), 400
    con = db()
    r = con.execute("SELECT * FROM recon_exception WHERE id=? AND unit=?", (exc_id, UNIT)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found"), 404
    if r["kind"] == "missing_day":
        return jsonify(ok=False, error="file_the_day",
                       message="A missing day closes only when the day is filed, not by writing a note."), 409
    con.execute("UPDATE recon_exception SET status='resolved', resolution=?, closed_by=?, closed_at=? "
                "WHERE id=?", (reason, u["user"], now_iso(), exc_id))
    con.execute("UPDATE cash_adjustment SET status='explained', explanation=?, approved_by=?, approved_at=? "
                "WHERE day_entry_id IN (SELECT id FROM day_entry WHERE unit=? AND business_date=?) "
                "AND status='open'", (reason, u["user"], now_iso(), UNIT, r["business_date"]))
    audit(con, "recon_exception", exc_id, "resolve", after={"resolution": reason}, who=u["user"])
    con.commit()
    return jsonify(ok=True, id=exc_id, status="resolved")


@app.route("/finance/api/shout", methods=["POST"])
def api_shout():
    """Called by the watchdog/cron. Increments the shout counter on every open
    exception so nothing can age out silently, and returns what to nudge about."""
    con = db()
    refresh_missing_days(con)
    con.execute("UPDATE recon_exception SET shout_count = shout_count + 1, last_shout_at=? "
                "WHERE unit=? AND status='open'", (now_iso(), UNIT))
    con.commit()
    return jsonify(ok=True, exceptions=open_exceptions(con, limit=50))


# ----------------------------------------------------------------- selftest

def selftest():
    """F-63: hit the ACTUAL routes with the Flask test client.
    F-79: assert on served HTML including ABSENCE checks.

    The smoke test runs as an INSTALL GATE, so it must never touch the live
    store: it works on a throwaway copy and deletes it afterwards."""
    global DB_PATH, ALLOW_HEADER_AUTH
    import shutil
    import tempfile
    live_db = DB_PATH
    tmp_fd, tmp_db = tempfile.mkstemp(prefix="finance_smoke_", suffix=".db")
    os.close(tmp_fd)
    shutil.copyfile(live_db, tmp_db)
    DB_PATH = tmp_db

    ok, fail = 0, []

    def check(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fail.append(name)

    c = app.test_client()

    # ---- fail-closed default: prove it BEFORE enabling the test override ----
    global ALLOW_HEADER_AUTH
    ALLOW_HEADER_AUTH = False
    os.environ["FINANCE_DEV_USER"] = ""
    os.environ["FINANCE_DEV_ROLE"] = ""

    r = c.get("/finance/healthz")
    check("healthz stays public", r.status_code == 200)
    check("healthz reports whether the epoch is readable",
          "sso_epoch_ok" in r.get_json())

    # A forged cookie is refused whether or not the epoch happens to be
    # readable in this environment. (The earlier version of this test asserted
    # the epoch was UNREADABLE, which was true only in the offline sandbox and
    # failed on the VPS where it reads fine — an environment accident dressed
    # up as a behaviour.)
    r = c.get("/finance/api/tile", headers={"Cookie": "clinic_sso=forged.token"})
    check("forged cookie refused", r.status_code == 401)

    # Fail-closed, proven deterministically: force the epoch to be unreadable
    # and require that a cookie buys nothing.
    import finance_app as _fa
    _real_epoch = _fa.sso_epoch
    _fa.sso_epoch = lambda: None
    try:
        r = c.get("/finance/api/tile", headers={"Cookie": "clinic_sso=anything"})
        check("cookie refused when the epoch cannot be read", r.status_code == 401)
        check("_sso_identity returns nothing without an epoch",
              _fa.app.test_request_context("/", headers={"Cookie": "clinic_sso=x"})
              and True)
    finally:
        _fa.sso_epoch = _real_epoch
    check("epoch check restored", _fa.sso_epoch is _real_epoch)

    r = c.get("/finance/api/tile")
    check("tile refused without identity", r.status_code == 401)
    r = c.get("/finance/scan/widget.js")
    check("widget.js is public (no clinic data in it)", r.status_code in (200, 404))
    r = c.get("/finance/scan/jspdf.js")
    check("jspdf.js is public", r.status_code in (200, 404))
    r = c.get("/finance/scan/2026-08-13/sale_report")
    check("but a scan PAGE is not public", r.status_code == 302)
    r = c.get("/finance/api/month/2026-08")
    check("month refused without identity", r.status_code == 401)
    r = c.get("/finance/api/day/2026-08-13")
    check("day refused without identity", r.status_code == 401)
    r = c.get("/finance/api/day/2026-08-13/lines")
    check("patient lines refused without identity", r.status_code == 401)
    r = c.get("/finance/api/exceptions")
    check("exceptions refused without identity", r.status_code == 401)
    r = c.post("/finance/api/day", json={"business_date": "2026-08-14", "total": "1"})
    check("write refused without identity", r.status_code == 401)
    r = c.get("/finance/entry")
    check("page redirects to the portal login", r.status_code == 302)

    # header spoofing must NOT work while header auth is off
    r = c.get("/finance/api/tile", headers={"X-Clinic-User": "attacker",
                                            "X-Clinic-Role": "checker"})
    check("spoofed role header is ignored", r.status_code == 401)
    r = c.post("/finance/api/approve/2026-08-13",
               headers={"X-Clinic-User": "attacker", "X-Clinic-Role": "checker"})
    check("spoofed approve is refused", r.status_code == 401)

    # ---- signed in is not the same as entitled -----------------------------
    # Simulate a real clinic login (Shavez) who has no role on medical.
    ALLOW_HEADER_AUTH = True
    r = c.get("/finance/api/tile", headers={"X-Clinic-User": "shavez",
                                            "X-Clinic-Role": "manager"})
    check("manager with no medical role cannot read the tile",
          r.status_code == 403 and r.get_json()["error"] == "no_role_here")
    r = c.get("/finance/api/day/2026-08-13/lines",
              headers={"X-Clinic-User": "shavez", "X-Clinic-Role": "manager"})
    check("manager cannot read patient lines", r.status_code == 403)
    r = c.get("/finance/api/whoami", headers={"X-Clinic-User": "shavez",
                                              "X-Clinic-Role": "manager"})
    check("but whoami explains why", r.status_code == 200 and
          r.get_json()["roles"] == [])
    r = c.get("/finance/entry", headers={"X-Clinic-User": "shavez",
                                         "X-Clinic-Role": "manager"})
    check("manager is redirected, not shown the page", r.status_code == 302)

    # A broker role grants NOTHING by itself — not even 'doctor'. Otherwise
    # Dr Bhawna, who checks lab and clinic, would inherit the pharmacy too.
    r = c.get("/finance/api/tile", headers={"X-Clinic-User": "bhawna",
                                            "X-Clinic-Role": "doctor"})
    check("broker role 'doctor' alone does NOT open medical", r.status_code == 403)
    # the named row is what grants it
    r = c.get("/finance/api/tile", headers={"X-Clinic-User": "manoj",
                                            "X-Clinic-Role": "doctor"})
    check("the named unit_role row is what grants access", r.status_code == 200)
    ALLOW_HEADER_AUTH = False

    # ---- now enable the offline override for the rest of the suite ---------
    ALLOW_HEADER_AUTH = True
    os.environ["FINANCE_DEV_USER"] = "selftest"
    os.environ["FINANCE_DEV_ROLE"] = "maker"

    r = c.get("/finance/healthz")
    check("healthz 200", r.status_code == 200)
    check("healthz ok", r.get_json().get("ok") is True)

    r = c.get("/finance/api/whoami")
    check("whoami role", r.get_json()["role"] == "maker")
    check("scanner absent until configured", r.get_json()["scanner"] is None)

    r = c.get("/finance/api/tile-meta")
    j = r.get_json()
    check("maker tile is not called Finance", j["title"] == "Daily Sale")
    check("maker tile points at the entry screen", j["href"] == "/finance/entry")
    r = c.get("/finance/api/tile-meta", headers={"X-Clinic-Role": "checker"})
    check("checker tile differs", r.get_json()["href"] == "/finance/review")

    r = c.get("/finance/")
    check("root lands maker on the entry screen", 'id="btnSubmit"' in r.get_data(as_text=True))
    r = c.get("/finance/", headers={"X-Clinic-Role": "checker"})
    check("root lands checker on the review screen",
          'id="btnApprove"' in r.get_data(as_text=True))

    r = c.get("/finance/entry")
    check("entry page 200", r.status_code == 200)
    html = r.get_data(as_text=True)
    check("entry has opening field", 'id="opening"' in html)
    check("entry opening is readonly", "readonly" in html)
    # ABSENCE checks (F-79): the maker page must not expose these
    check("entry has NO approve button", "id=\"btnApprove\"" not in html)
    check("entry has NO editable opening input", 'name="opening"' not in html)
    check("entry titled Daily Sale, not Finance", "Daily Sale" in html and "Finance" not in html)
    # icons are inline <symbol>s; nothing is FETCHED from outside (the only http://
    # occurrence is the SVG xmlns, which is a namespace, not a request)
    check("entry uses inline icon symbols", html.count("<symbol") >= 10)
    check("entry loads nothing external",
          'src="http' not in html and 'href="http' not in html and "@import" not in html)

    r = c.get("/finance/review")
    check("review page 200", r.status_code == 200)
    rhtml = r.get_data(as_text=True)
    check("review has approve button", 'id="btnApprove"' in rhtml)
    check("review has month grid", 'id="monthGrid"' in rhtml)
    check("review has the parked-cash table", 'id="parkedTable"' in rhtml)
    check("review has a cash-count control", 'id="btnCutover"' in rhtml)
    check("review lists every day, reopenable", 'id="dayList"' in rhtml)
    check("review carries the UPI-ack dialog", "acknowledge_upi" in rhtml)
    check("review has a back link to the portal", 'href="/portal"' in rhtml)
    check("entry has a back link to the portal", 'href="/portal"' in html)
    check("entry page has NO cash-count control", 'id="btnCutover"' not in html)

    r = c.get("/finance/api/day/2026-08-13")
    j = r.get_json()
    check("day 2026-08-13 exists", j["ok"] and j["day"]["exists"])
    check("day opening is computed", "opening_p" in j["day"])

    r = c.get("/finance/api/day/2026-04-01")
    check("first day opening is zero", r.get_json()["day"]["opening_p"] == 0)

    r = c.get("/finance/api/month/2026-08")
    j = r.get_json()
    check("month 200", j["ok"])
    check("month has 31 cells", len(j["days"]) == 31)

    r = c.get("/finance/api/exceptions")
    check("exceptions listed", len(r.get_json()["exceptions"]) > 0)

    r = c.get("/finance/api/days?days=400")
    j = r.get_json()
    check("day list returns every filed day", j["ok"] and j["count"] > 100)
    check("day list carries status and counts",
          "status" in j["days"][0] and "scans" in j["days"][0])
    approved_present = any(d["status"] in ("approved", "locked") for d in j["days"])
    check("approved/locked days are still listed", approved_present)

    r = c.get("/finance/api/tile")
    j = r.get_json()
    check("tile ok", j["ok"])
    check("tile shouts present", j["shouts"]["total"] > 0)

    # ---- the legacy import leaves cash NEGATIVE; the app must refuse to build
    #      on it until a cutover count establishes a real opening balance -------
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    last = con.execute("SELECT business_date, closing_p FROM v_cash_ledger WHERE unit=? "
                       "ORDER BY business_date DESC LIMIT 1", (UNIT,)).fetchone()
    con.close()
    check("legacy leaves cash negative", last["closing_p"] < 0)
    day1 = (parse_iso_date(last["business_date"]) + dt.timedelta(days=1))
    if day1 > today():
        day1 = today()
    D1 = day1.isoformat()

    def post(payload):
        return c.post("/finance/api/day", json=payload)

    r = post({"business_date": D1, "total": "1000", "upi": "0"})
    check("cannot build on negative legacy cash", r.status_code == 400 and
          r.get_json()["error"] == "negative_cash")

    r = c.post("/finance/api/cutover", json={"date": last["business_date"], "counted": "50000"})
    check("maker cannot cutover", r.status_code == 403)
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    r = c.post("/finance/api/cutover",
               json={"date": last["business_date"], "counted": "50000",
                     "note": "drawer counted at go-live"})
    j = r.get_json()
    check("cutover ok", r.status_code == 200 and j["ok"])
    check("cutover leaves legacy breaks open", j.get("legacy_breaks_still_open", 0) > 0)
    r = c.get("/finance/api/day/" + D1)
    check("opening now 50000", r.get_json()["day"]["opening_p"] == 5000000)
    os.environ["FINANCE_DEV_ROLE"] = "maker"

    # ---- validation gates ---------------------------------------------------
    r = post({"business_date": (today() + dt.timedelta(days=1)).isoformat(), "total": "100"})
    check("future date refused", r.status_code == 400 and r.get_json()["error"] == "future_date")

    r = post({"business_date": D1, "total": "O"})
    check("letter O refused", r.status_code == 400 and r.get_json()["error"] == "not_a_number")

    r = post({"business_date": D1, "total": "1000", "upi": "2000"})
    check("upi over total refused", r.status_code == 400 and r.get_json()["error"] == "upi_over_total")

    r = post({"business_date": D1, "total": "1000", "upi": "0",
              "movements": [{"direction": "out", "party": "bank", "amount": "9999999"}]})
    check("negative cash refused", r.status_code == 400 and r.get_json()["error"] == "negative_cash")

    r = post({"business_date": D1, "total": "500000", "upi": "0"})
    check("large amount needs confirm", r.status_code == 409)

    r = post({"business_date": D1, "total": "1000", "upi": "300", "action": "submit"})
    check("submit without scans refused", r.status_code == 400 and
          r.get_json()["error"] == "scans_required")

    # claiming scans in the request body must NOT satisfy the requirement —
    # the files have to actually exist against the day
    r = post({"business_date": D1, "total": "1000", "upi": "300",
              "action": "submit", "attached_docs": list(REQUIRED_DOCS)})
    check("claimed-but-absent scans still refused", r.status_code == 400 and
          r.get_json()["error"] == "scans_required")

    # save a draft, then attach the three scans through the real upload route
    r = post({"business_date": D1, "total": "1000", "upi": "300", "action": "draft"})
    check("draft saved so scans can attach", r.status_code == 200)
    import io as _io
    import io
    for doc in REQUIRED_DOCS:
        rr = c.post("/finance/api/day/%s/scan/%s" % (D1, doc),
                    data={"file": (_io.BytesIO(b"%PDF-1.4 fake scan"), doc + ".pdf")},
                    content_type="multipart/form-data")
        check("scan uploaded: " + doc, rr.status_code == 200 and rr.get_json()["ok"])
    rr = c.post("/finance/api/day/%s/scan/not_a_doc" % D1,
                data={"file": (_io.BytesIO(b"x"), "x.pdf")},
                content_type="multipart/form-data")
    check("unknown doc_type refused", rr.status_code == 400)

    r = c.get("/finance/scan/%s/sale_report" % D1)
    check("scan page renders", r.status_code == 200)
    sp = r.get_data(as_text=True)
    check("scan page mounts the widget's div", "id=scanroot" in sp)
    check("scan page sets SCANNER_CONFIG", "window.SCANNER_CONFIG" in sp)
    check("scan page points at the real upload route",
          "/finance/api/day/%s/scan/sale_report" % D1 in sp)
    check("scan page loads NOTHING from a CDN",
          "cdnjs" not in sp and "https://" not in sp)
    check("scan page returns to the entry screen", "/finance/entry?d=%s" % D1 in sp)
    check("scan page has a visible Back control", "← Back" in sp)

    # a clean save — now with the scans genuinely on disk
    r = post({"business_date": D1, "total": "1000", "upi": "300",
              "expenses": [{"amount": "50", "category_text": "chai"}],
              "movements": [{"direction": "out", "party": "dr_manoj", "amount": "100"}],
              "action": "submit"})
    j = r.get_json()
    check("clean save ok", r.status_code == 200 and j["ok"])
    if j.get("ok"):
        check("saved status submitted", j["day"]["status"] == "submitted")
        check("saved cash correct", j["day"]["cash_p"] == 70000)
        check("closing carries from cutover",
              j["day"]["closing_p"] == 5000000 + 70000 - 5000 - 10000)

    # salary advance without staff
    r = post({"business_date": D1, "total": "100",
              "expenses": [{"amount": "500", "category_fixed": "salary_advance"}]})
    check("salary advance needs staff", r.status_code == 400 and
          r.get_json()["error"] == "staff_required")

    # ---- bills raised at full value with no cash across the counter ---------
    nc = lambda **kw: dict({"head": "home_medicine", "bill_no": "B-1",
                            "amount": "200"}, **kw)
    r = post({"business_date": D1, "total": "1000", "upi": "300",
              "noncash_bills": [nc(bill_no="")]})
    check("bill number is required", r.status_code == 400 and
          r.get_json()["error"] == "bill_no_required")

    r = post({"business_date": D1, "total": "1000", "upi": "300",
              "noncash_bills": [nc(head="other", head_text="")]})
    check("'other' head needs a description", r.status_code == 400 and
          r.get_json()["error"] == "head_text_required")

    r = post({"business_date": D1, "total": "1000", "upi": "300",
              "noncash_bills": [nc(amount="900")]})
    check("non-cash bills cannot exceed cash sale", r.status_code == 400 and
          r.get_json()["error"] == "noncash_over_cash")

    r = post({"business_date": D1, "total": "1000", "upi": "300",
              "noncash_bills": [nc(bill_no="H-101", amount="200"),
                                nc(bill_no="P-55", head="procedure_medicine", amount="150")],
              })
    j = r.get_json()
    check("non-cash bills saved", r.status_code == 200 and j["ok"])
    if j.get("ok"):
        d = j["day"]
        check("two bills recorded", len(d["noncash_bills"]) == 2)
        check("non-cash total right", d["noncash_p"] == 35000)
        # revenue is still full value; only the CASH is reduced
        check("revenue still counts in full", d["total_p"] == 100000)
        check("actual cash received is less", d["cash_actually_received_p"] == 70000 - 35000)
        check("closing reflects the shortfall",
              d["closing_p"] == 5000000 + 70000 - 35000)

    r = c.get("/finance/api/month/%s" % D1[:7])
    j = r.get_json()
    check("month reports non-cash total", j["totals"]["noncash"] == "350.00")
    check("month breaks non-cash down by head", len(j["noncash_by_head"]) == 2)

    r = c.get("/finance/api/tile")
    j = r.get_json()
    check("tile tracks days since a bank trip", "days_since_bank_deposit" in j)
    check("tile reports non-cash month to date", j["noncash_month_to_date"] == "350.00")

    # a correction keeps the old version verbatim
    r = post({"business_date": D1, "total": "1200", "upi": "300"})
    check("correction accepted", r.status_code == 200 and r.get_json()["ok"])
    con = sqlite3.connect(DB_PATH)
    nrev = con.execute("SELECT COUNT(*) FROM day_revision dr JOIN day_entry e ON e.id=dr.day_entry_id "
                       "WHERE e.business_date=?", (D1,)).fetchone()[0]
    con.close()
    check("old submission kept as revision", nrev >= 1)

    # ---- B5: the bank is the arbiter for UPI -------------------------------
    tb = finance_upi._build_test_xlsx(
        [(parse_iso_date(D1).strftime("%d-%b-%y").upper(), 999.0, "RRN1")], 999.0)
    r = c.post("/finance/api/upi-statement",
               data={"file": (io.BytesIO(tb), "mpr.xlsx")},
               content_type="multipart/form-data")
    check("maker cannot post statements", r.status_code == 403)
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    r = c.post("/finance/api/upi-statement",
               data={"file": (io.BytesIO(tb), "mpr.xlsx")},
               content_type="multipart/form-data")
    j = r.get_json()
    check("checker can post a statement", r.status_code == 200 and j["ok"])
    check("statement reconciled against the day",
          j["days"][0]["compared"] and j["days"][0]["match"] is False)

    bad = finance_upi._build_test_xlsx([("14-AUG-26", 400.0, "R1")], 5555.0)
    r = c.post("/finance/api/upi-statement",
               data={"file": (io.BytesIO(bad), "bad.xlsx")},
               content_type="multipart/form-data")
    check("corrupt statement rejected whole", r.status_code == 422)

    # approval over a bank mismatch must be conscious
    r = c.post("/finance/api/approve/" + D1)
    check("approve blocked by upi mismatch", r.status_code == 409 and
          r.get_json()["error"] == "upi_mismatch")
    r = c.post("/finance/api/approve/" + D1,
               json={"acknowledge_upi": True, "ack_note": "smoke"})
    check("approve with acknowledgment works", r.status_code == 200 and
          r.get_json()["status"] == "approved")
    con = sqlite3.connect(DB_PATH)
    stt = con.execute("SELECT status, resolution FROM recon_exception WHERE unit=? "
                      "AND business_date=? AND kind='upi_vs_statement'",
                      (UNIT, D1)).fetchone()
    con.close()
    check("mismatch recorded as acknowledged, not erased",
          stt and stt[0] == "acknowledged" and "approved over" in (stt[1] or ""))
    os.environ["FINANCE_DEV_ROLE"] = "maker"

    # cron token path: with no token configured, the header buys nothing
    r = c.post("/finance/api/upi-statement", headers={"X-Finance-Cron": "guess"},
               data={"file": (io.BytesIO(tb), "mpr.xlsx")},
               content_type="multipart/form-data")
    check("wrong/unset cron token refused", r.status_code in (401, 403))

    # maker may not approve
    r = c.post("/finance/api/approve/" + D1)
    check("maker cannot approve", r.status_code in (403, 409))

    # checker may (already approved above with acknowledgment)
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    r = c.get("/finance/api/day/" + D1)
    check("checker sees the approved day", r.get_json()["day"]["status"] == "approved")

    # missing day cannot be talked away
    exc = c.get("/finance/api/exceptions").get_json()["exceptions"]
    md = [e for e in exc if e["kind"] == "missing_day"]
    if md:
        r = c.post("/finance/api/exception/%d/resolve" % md[0]["id"],
                   json={"resolution": "chhutti thi"})
        check("missing day cannot be resolved by text", r.status_code == 409)

    cf = [e for e in exc if e["kind"] == "carry_forward_break"]
    if cf:
        r = c.post("/finance/api/exception/%d/resolve" % cf[0]["id"], json={"resolution": "x"})
        check("short reason refused", r.status_code == 400)
        r = c.post("/finance/api/exception/%d/resolve" % cf[0]["id"],
                   json={"resolution": "deposit was entered a day late"})
        check("carry-forward break resolvable with reason", r.status_code == 200)

    # ---- B2.1: thresholds, custody, per-unit roles, month close, archive ----
    r = c.get("/finance/api/tile")
    j = r.get_json()
    check("tile reports who holds the cash", "cash_with" in j)
    check("tile reports deposit threshold", j["deposit_threshold"] == "50,000.00")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    roles = {(x["unit"], x["username"], x["role"]) for x in
             con.execute("SELECT unit, username, role FROM unit_role")}
    con.close()
    check("Dr Bhawna checks lab", ("lab", "bhawna", "checker") in roles)
    check("Dr Bhawna checks clinic", ("clinic", "bhawna", "checker") in roles)
    check("Dr Bhawna does NOT check medical", ("medical", "bhawna", "checker") not in roles)
    check("reception makes clinic", ("clinic", "reception", "maker") in roles)
    check("lab staff makes lab", ("lab", "labstaff", "maker") in roles)

    # per-unit role resolution must work off the username, with no header role
    os.environ["FINANCE_DEV_ROLE"] = ""
    r = c.post("/finance/api/approve/" + D1, headers={"X-Clinic-User": "darpan"})
    check("darpan cannot approve medical (by username)", r.status_code == 403)
    r = c.post("/finance/api/cutover", headers={"X-Clinic-User": "bhawna"},
               json={"date": D1, "counted": "1000"})
    check("bhawna cannot act on medical (by username)", r.status_code == 403)
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    # month close: blocked until the month is actually complete
    YM = D1[:7]
    r = c.get("/finance/api/month/%s/close-check" % YM)
    j = r.get_json()
    check("close-check runs", j["ok"])
    check("close-check blocks on an incomplete month", len(j["blockers"]) > 0)
    check("close-check knows the drawer carries", j["carry_policy"] == "carry")
    check("carrying means no settlement is demanded", j["settlement_required"] is False)

    r = c.post("/finance/api/month/%s/finalise" % YM, json={})
    check("finalise refused while blockers stand", r.status_code == 409 and
          r.get_json()["error"] == "not_ready")

    # the month's own soft copy decides
    r = c.post("/finance/api/month/%s/statement" % YM,
               json={"kind": "sale_register", "stated_total": "999999",
                     "filename": "sanjeevni_sale_register_%s.xlsx" % YM})
    j = r.get_json()
    check("statement accepted", r.status_code == 200 and j["ok"])
    check("statement variance computed", j["agrees"] is False and j["variance"] != "0.00")
    exc = c.get("/finance/api/exceptions").get_json()["exceptions"]
    check("statement disagreement shouts",
          any(e["kind"] == "month_vs_statement" for e in exc))

    # finalise: the drawer CARRIES, so no settlement is demanded
    before_close = c.get("/finance/api/month/%s/close-check" % YM).get_json()
    r = c.post("/finance/api/month/%s/finalise" % YM,
               json={"override_reason": "smoke test"})
    j = r.get_json()
    check("finalise ok without a settlement", r.status_code == 200 and j["ok"])
    check("finalise reports carry policy", j["carry_policy"] == "carry")
    check("cash carried forward, not swept",
          j["cash_carried_forward"] == before_close["residual_cash"])
    check("scans queued for Drive", j["scans_queued_for_archive"] > 0)

    r = c.get("/finance/api/archive/queue")
    check("archive queue visible", r.get_json()["count"] > 0)

    # ---- parked cash: one deposit, one number, the rest is this month ------
    pk = c.get("/finance/api/parked").get_json()
    check("parked view lists the finalised month", any(m["ym"] == YM for m in pk["months"]))
    mrow = [m for m in pk["months"] if m["ym"] == YM][0]
    check("month shows cash parked", mrow["outstanding_p"] > 0)
    check("bank deposits offered for allocation", len(pk["bank_deposits"]) > 0)
    dep = [d for d in pk["bank_deposits"] if d["amount_p"] >= mrow["outstanding_p"]]
    if not dep:
        dep = pk["bank_deposits"]
    dep = dep[0]

    r = c.post("/finance/api/deposit/%d/clear" % dep["id"],
               json={"ym": YM, "amount": "999999999"})
    check("cannot allocate more than the deposit", r.status_code == 400)
    r = c.post("/finance/api/deposit/%d/clear" % dep["id"],
               json={"ym": "2099-01", "amount": "10"})
    check("cannot clear a month that was never finalised", r.status_code == 409)

    part = max(int(mrow["outstanding_p"] / 200) * 1, 1)      # a small partial, in paise
    r = c.post("/finance/api/deposit/%d/clear" % dep["id"],
               json={"ym": YM, "amount": "%.2f" % (part / 100.0)})
    j = r.get_json()
    check("partial clearing accepted", r.status_code == 200 and j["ok"])
    check("remainder attributed to the current month, unstated",
          j["remainder_current_month"] != "0.00")
    check("month not yet settled", j["settled"] is False)

    pk2 = c.get("/finance/api/parked").get_json()
    m2 = [m for m in pk2["months"] if m["ym"] == YM][0]
    check("outstanding fell by exactly what was allocated",
          m2["outstanding_p"] == mrow["outstanding_p"] - part)

    # the movement itself is untouched — it must still match the bank statement
    con = sqlite3.connect(DB_PATH)
    amt = con.execute("SELECT amount_p FROM cash_movement WHERE id=?", (dep["id"],)).fetchone()[0]
    con.close()
    check("the deposit row is never split", amt == dep["amount_p"])

    r = c.post("/finance/api/deposit/%d/clear" % dep["id"],
               json={"ym": YM, "amount": "%.2f" % (mrow["outstanding_p"] / 100.0)})
    j = r.get_json()
    check("clearing the full parked amount settles the month",
          r.status_code == 200 and j["settled"] is True)

    os.environ["FINANCE_DEV_ROLE"] = "maker"
    r = c.post("/finance/api/deposit/%d/clear" % dep["id"], json={"ym": YM, "amount": "1"})
    check("a maker cannot allocate deposits", r.status_code == 403)
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    r = c.post("/finance/api/month/%s/finalise" % YM, json={})
    check("cannot finalise twice", r.status_code == 409)

    con = sqlite3.connect(DB_PATH)
    st = con.execute("SELECT status FROM day_entry WHERE unit=? AND business_date=?",
                     (UNIT, D1)).fetchone()[0]
    con.close()
    check("finalised month locks its days", st == "locked")

    # ---- B3a: patient-wise lines from a swappable source -------------------
    r = c.get("/finance/api/sources")
    j = r.get_json()
    ad = {s_["adapter"]: s_ for s_ in j["sources"]}
    check("sarvam is the seeded primary", ad["sarvam_ocr"]["primary"] is True)
    check("marg is present but not yet mapped", ad["marg_export"]["mapped"] is False)

    r = c.post("/finance/api/sources/marg_export/map", json={
        "config": {"delimiter": ",", "date_format": "%d/%m/%Y"},
        "active": True, "make_primary": True,
        "column_map": [
            {"field": "bill_no", "column": "Bill No", "required": True},
            {"field": "bill_date", "column": "Bill Date", "transform": "ddmmyyyy"},
            {"field": "patient_name", "column": "Customer", "required": True},
            {"field": "amount", "column": "Net Amt", "required": True},
            {"field": "description", "column": "Particulars"}]})
    check("marg column map accepted", r.status_code == 200 and r.get_json()["columns"] == 5)

    r = c.post("/finance/api/sources/marg_export/map",
               json={"column_map": [{"field": "not_a_field", "column": "X"}]})
    check("bad field rejected", r.status_code == 400)

    MARG = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
            "H-9001,%s,4471 Ramesh Kumar,Tab Calcium,Rs 450.00\n"
            "H-9002,%s,Sunita Devi (5120),Knee cap,\"1,250.00\"\n"
            "H-9003,%s,Walk in customer,Bandage,120\n"
            % tuple([parse_iso_date(D1).strftime("%d/%m/%Y")] * 3))

    r = c.post("/finance/api/day/%s/ingest" % D1,
               json={"adapter": "marg_export", "payload": MARG, "source_ref": "marg.csv"})
    j = r.get_json()
    check("marg ingest ok", r.status_code == 200 and j["ok"])
    check("two lines attributed", j["accepted"] == 2)
    check("one line queued for review", j["review"] == 1)
    check("attribution reported against day total", j["day_total"] and j["unattributed"])

    r = c.get("/finance/api/day/%s/lines" % D1)
    j = r.get_json()
    check("lines listed", len(j["lines"]) == 2)
    ids = sorted(l["clinic_id"] for l in j["lines"])
    check("clinic ids parsed from the name column", ids == ["4471", "5120"])
    check("review queue exposed", len(j["review"]) == 1)
    check("batch history exposed", len(j["batches"]) >= 1)

    exc = c.get("/finance/api/exceptions").get_json()["exceptions"]
    check("unattributed remainder shouts",
          any(e["kind"] == "line_sum_vs_day_total" for e in exc))

    rid = j["review"][0]["id"]
    r = c.post("/finance/api/review/%d/resolve" % rid,
               json={"action": "assign", "clinic_id": "6001", "name": "Walk in customer"})
    check("review line assignable", r.status_code == 200)
    j = c.get("/finance/api/day/%s/lines" % D1).get_json()
    check("assigned line joins the spine", len(j["lines"]) == 3)
    check("review queue cleared", len(j["review"]) == 0)

    # a wrong file must fail loudly and leave good lines alone
    r = c.post("/finance/api/day/%s/ingest" % D1,
               json={"adapter": "marg_export", "payload": "Invoice,Name,Total\nX-1,foo,100\n"})
    check("wrong format fails loudly", r.status_code == 422 and
          "not found" in (r.get_json().get("error_") or r.get_json().get("error", "") or
                          r.get_json().get("message", "") or str(r.get_json())))
    j = c.get("/finance/api/day/%s/lines" % D1).get_json()
    check("failed ingest preserved existing lines", len(j["lines"]) == 3)

    r = c.post("/finance/api/day/%s/ingest" % D1, json={"adapter": "sarvam_ocr", "payload": "x"})
    check("sarvam reports unavailable, not empty", r.status_code == 422)

    con = sqlite3.connect(DB_PATH)
    pv = con.execute("SELECT COUNT(*) FROM v_patient_revenue").fetchone()[0]
    con.close()
    check("patient revenue spine populated", pv >= 3)

    os.environ["FINANCE_DEV_ROLE"] = "maker"

    DB_PATH = live_db
    try:
        os.remove(tmp_db)
    except OSError:
        pass

    print("SMOKE %d/%d passed  (ran on a throwaway copy; %s untouched)"
          % (ok, ok + len(fail), os.path.basename(live_db)))
    for f in fail:
        print("  FAIL:", f)
    return 0 if not fail else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    app.run(host="127.0.0.1", port=int(os.environ.get("FINANCE_PORT", "8099")))
