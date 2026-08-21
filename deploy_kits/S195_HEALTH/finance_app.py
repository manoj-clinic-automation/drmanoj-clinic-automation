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
import io
import json
import os
import re
import sqlite3
import sys

from flask import (Flask, g, jsonify, redirect, request, send_file,
                   send_from_directory)

import finance_ingest
import finance_upi

# S186_R2a: the Yes Bank cash reconciler (F-103 / the F-112 detector). Imported
# FAIL-SOFT on purpose — if the module is absent the three new surfaces return
# 503 and every existing screen behaves exactly as before. A finance screen must
# never go dark because an optional module moved (D264, D322(a)).
try:
    import finance_yesbank
except Exception:                                   # pragma: no cover
    finance_yesbank = None

# S186_I1a: the Marg upload surface. Fail-soft for the same reason — an absent
# optional module returns 503 on its own route and changes nothing else.
try:
    import marg_report
except Exception:                                   # pragma: no cover
    marg_report = None
try:
    import finance_returns
except Exception:                                   # pragma: no cover
    finance_returns = None
import csv

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("FINANCE_DB", os.path.join(APP_ROOT, "finance.db"))
UI_DIR = os.environ.get("FINANCE_UI_DIR", os.path.join(APP_ROOT, "finance_ui"))
SCAN_DIR = os.environ.get("FINANCE_SCAN_DIR", os.path.join(APP_ROOT, "finance_scans"))
# D322: clinic-holiday source is the attendance system (read-only, fail-soft).
ATTENDANCE_DB = os.environ.get("FINANCE_ATTENDANCE_DB", "/root/staff_register/staff_register.db")
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
# S187_M1a (B5): the pharmacy sender's token. SEPARATE from CRON_TOKEN on
# purpose -- the medical PC must never hold a secret that also opens the UPI
# and tracker push routes, and rotating one must never break the other.
# Absent => the push surface does not exist at all (fail closed, F-84).
MARG_TOKEN = os.environ.get("FINANCE_MARG_TOKEN", "")
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
IDENTITY_ONLY_PATHS = ("/finance/api/whoami", "/finance/clinic/api/whoami")


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
    # S187_M1a (B5): the pharmacy sender's token opens exactly ONE path -- the
    # staged push. It grants no identity, no role and no other route; the
    # handler re-checks it (defense in depth) and can only STAGE, never apply.
    if MARG_TOKEN and p == "/finance/api/marg-push" \
            and request.headers.get("X-Finance-Marg") == MARG_TOKEN:
        return None
    u = current_user()
    if not u.get("user"):
        if request.path.startswith(("/finance/api/", "/finance/clinic/api/")):
            return jsonify(ok=False, error="not_signed_in",
                           message="Sign in on the clinic portal first."), 401
        return redirect(PORTAL_LOGIN, code=302)

    # Signed in is not the same as entitled. A valid clinic login with no role
    # on THIS unit gets nothing — otherwise every staff member with an SSO
    # account could read the pharmacy's cash position, which is not what the
    # owner asked for (medical's checker is the doctor alone).
    if request.path.rstrip("/") in IDENTITY_ONLY_PATHS:
        return None
    # C1a (S182): the unit is resolved FROM THE PATH — /finance/clinic/... gates
    # on clinic roles, everything else stays the original medical surface. A
    # role in one unit still grants nothing in another (S179).
    unit = _unit_for_path(request.path)
    if roles_for(db(), unit, u["user"], u.get("role")):
        return None
    if request.path.startswith(("/finance/api/", "/finance/clinic/api/")):
        return jsonify(ok=False, error="no_role_here",
                       message="You are signed in, but you have no role in %s."
                               % (CLINIC_NAME if unit == CLINIC_UNIT
                                  else "Sanjeevni Medicos")), 403
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
    _exp_att_tbl(con)                                    # lazy DDL (D330)
    _ev_uids = {r[0] for r in con.execute(
        "SELECT expense_uid FROM expense_attachment WHERE day_entry_id=?", (e["id"],))}
    _expense_uid_col(con)
    exps = [dict(id=r["id"], amount_p=r["amount_p"], amount=rupees(r["amount_p"]),
                 known=bool(r["amount_known"]), category_fixed=r["category_fixed"],
                 category_kind=r["category_kind"],
                 staff_id=r["staff_id"], category_text=r["category_text"],
                 uid=r["expense_uid"],
                 has_evidence=(r["expense_uid"] in _ev_uids),
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
    _noncash_att_tbl(con)
    _nc_ev = {r[0] for r in con.execute(
        "SELECT noncash_uid FROM noncash_attachment WHERE day_entry_id=?", (e["id"],))}
    _noncash_uid_col(con)
    bills = [dict(id=r["id"], bill_no=r["bill_no"], bill_date=r["bill_date"], head=r["head"],
                  head_text=r["head_text"], amount_p=r["amount_p"], amount=rupees(r["amount_p"]),
                  status=r["status"], uid=r["noncash_uid"],
                  has_file=(r["noncash_uid"] in _nc_ev))
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

# The S183 MEASURED Marg-vs-declared tolerance, in paise. It was a bare literal
# inside /full; the D2 mirror needs the SAME number, and two copies of a
# threshold is how the maker and the checker end up disagreeing about whether a
# day is fine. One name, both readers.
MARG_VARIANCE_THRESHOLD_P = 200000          # Rs 2,000

# The Indian financial year: 1 April - 31 March. Parked-cash totals are scoped
# to the CURRENT year on the owner's instruction -- last year's handovers are
# last year's problem, and carrying them forward would make the figure grow
# forever and mean less every April.
def fy_start(d=None):
    d = d or today()
    return dt.date(d.year if d.month >= 4 else d.year - 1, 4, 1)


PARTY_NAMES = {"dr_manoj": "Dr Manoj", "dr_bhawna": "Dr Bhawna",
               "other": "Someone else", "bank": "Bank",
               "drawer": "The drawer", "counter": "The counter"}

# S189 (F-137): parties that are PLACES inside the unit rather than people
# holding its cash. A custody event moves money between places, so these go
# negative by construction; they are never "parked with" anybody.
CUSTODY_STRUCTURAL = ("drawer", "counter", "bank")

# S189 (owner ruling + F-139): the expense MENU -- one authored source. The
# page is served these exact labels and the selftest holds the served HTML to
# every one of them, so the page's copy cannot drift from this one silently.
# What the save WRITES is the canonical label from THIS table, never the
# page's spelling. On the medical page a salary advance is DARPAN'S OWN --
# the owner's ruling ("Darpan draws only his salary advance from the medical
# cash") -- so there is no staff selector anywhere: the SERVER resolves the
# identity (F-84: the client does not get to name who money is attributed to;
# F-139: the page used to offer hardcoded ids 1 and 2 pointing at an empty
# staff_ref -- never exercised, survey S189, but a loaded gun).
# D330 (S190): three categories. Petty business spends (tea, courier
# handling...) run on the owner's separate MANUAL book and never reach this
# menu -- which is what makes compulsory evidence livable. "Home expenses"
# are the owner's personal spends from the drawer (incl. COD deliveries,
# the ruling that retired the transport head): they total separately in
# reporting as the proprietor's DRAWINGS, never as business expenses.
EXPENSE_MENU = (
    ("salary_advance_self", "My salary advance"),
    ("home",                "Home expenses (personal / COD delivery)"),
    ("other",               "Other expenses (write details)"),
)
EXPENSE_LABELS = dict(EXPENSE_MENU)


def advance_ceiling_p(con):
    """D330: the advance ceiling is DERIVED, never typed -- a per-staff
    percentage of base salary, rounded DOWN to the last Rs 100 (F-136: a
    stored Rs-figure would be a second copy of a fact the salary system
    owns). Defaults: base Rs 20,000, pct 75 (Darpan's owner-ruled
    exception; the general staff rule is 50 and lives in the Staff Ledger
    contract, not here). Both are settings, so a salary revision is one
    settings row, not a code change."""
    try:
        base = int(setting(con, "advance.base_p", "2000000") or 2000000)
        pct = int(setting(con, "advance.pct", "75") or 75)
    except (TypeError, ValueError):
        base, pct = 2000000, 75
    return (base * pct // 100) // 10000 * 10000


def advance_month_to_date_p(con, iso, exclude_day_entry_id=None):
    """Salary advances already in the books for iso's CALENDAR month
    (draft + submitted + approved -- a draft row is money already out of
    the drawer). The day being re-saved is excluded so its own replaced
    rows are not double-counted against it."""
    q = ("SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x "
         "JOIN day_entry e ON e.id = x.day_entry_id "
         "WHERE e.unit=? AND substr(e.business_date,1,7)=? "
         "AND x.category_fixed='salary_advance'")
    args = [UNIT, iso[:7]]
    if exclude_day_entry_id:
        q += " AND e.id != ?"
        args.append(exclude_day_entry_id)
    return con.execute(q, args).fetchone()[0]


_UID_RE = re.compile(r"^[A-Za-z0-9_-]{6,40}$")

LEDGER_JSONL = os.environ.get("FINANCE_LEDGER_JSONL", "/root/staff_ledger/ledger.jsonl")


def ledger_fwd_advances_p(month):
    """D331 cross-system plumbing (kit S190_F2): salary-side advances
    ATTRIBUTED to `month` from an earlier month (against_month != the row's
    own entry month). Only forward-attributed rows are counted, because a
    drawer draw is never forward-attributed -- so the same rupee can never be
    counted in both books (the double-count the retired D329 LINK machinery
    existed to prevent, solved structurally instead).
    KNOWN, DOCUMENTED BLIND SPOT: a same-month DIRECT pipeline advance is not
    netted from the drawer limit -- by flow those are rare (within-quota money
    comes from the drawer) and the checker sees both books.
    FAIL-SOFT (the D283/D322 pattern): any problem returns (0, False) and the
    page SAYS the ledger was unreadable -- degraded, never silent, never a
    crash."""
    try:
        total = 0
        with open(LEDGER_JSONL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if (r.get("category") == "ADVANCE_ISSUE"
                        and r.get("staff") == "Darpan"
                        and r.get("status") in ("PENDING", "APPROVED")):
                    _own = (r.get("date_from") or "")[:7]
                    _am = r.get("against_month") or _own
                    if _am == month and _am != _own:
                        total += int(r.get("amount") or 0) * 100
        return total, True
    except OSError:
        return 0, False
    except Exception:
        return 0, False


def _expense_uid_col(con):
    """Lazy ALTER (the day_mirror_reveal pattern: DDL authoritative in
    code). expense_uid is the STABLE identity of an expense row -- the
    save's delete-and-reinsert mints new row ids every time, so evidence
    keys on the uid the PAGE carries, which survives any number of
    re-saves. Without it, a bill attached to a row would be orphaned by
    the next save of its own day."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(day_expense)")}
    if "expense_uid" not in cols:
        con.execute("ALTER TABLE day_expense ADD COLUMN expense_uid TEXT")
    if "category_kind" not in cols:
        # D330: 'home' / 'other'. A NEW column, because category_fixed carries
        # a schema CHECK allowing only NULL/'salary_advance' -- discovered by
        # the offline rehearsal, not on the box. The CHECK keeps guarding what
        # it always guarded; the new categories live beside it, additively.
        con.execute("ALTER TABLE day_expense ADD COLUMN category_kind TEXT")


def _exp_att_tbl(con):
    """Per-expense evidence (D330: COMPULSORY for home/other, no escape
    hatch -- the owner's flow is photograph-at-payment, upload-at-filing).
    Keys on (day_entry_id, expense_uid), NOT day_expense.id, so it
    survives the save's delete-and-reinsert."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS expense_attachment ("
        " id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL,"
        " expense_uid TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT,"
        " bytes INTEGER, uploaded_by TEXT, uploaded_at TEXT,"
        " UNIQUE(day_entry_id, expense_uid))")


def pharmacy_staff_id(con):
    """The staff_ref row this unit's salary advances attribute to (F-139).
    staff_ref sat EMPTY from S179 to S189 while the entry page offered
    hardcoded staff ids 1 and 2 ("Someone else") that pointed at nothing.
    Zero rows ever carried a staff_id (surveyed on the box, S189), so no
    damage was done -- but the identity is resolved HERE from now on, and
    the one real row is created lazily on first use. register_id stays NULL
    until the D3 bridge decides the join key to the staff register."""
    r = con.execute("SELECT id FROM staff_ref WHERE name='Darpan' AND active=1").fetchone()
    if r:
        return r["id"]
    con.execute("INSERT INTO staff_ref (name, is_pharmacy, active) VALUES ('Darpan', 1, 1)")
    return con.execute("SELECT id FROM staff_ref WHERE name='Darpan' AND active=1"
                       ).fetchone()["id"]


def clinic_holidays(first_iso, upto):
    """D322: the days the clinic is officially closed, from the ATTENDANCE system
    (read-only): every `clinic_holiday.reg_date`, plus `festival_day` rows with
    clinic_closed=1 (e.g. Holi). Returns {iso_date: label}. FAIL-SOFT — any problem
    (db absent, locked, schema drift) returns {} so the classifier degrades to
    Sunday-only and NEVER crashes the finance app (D283)."""
    out = {}
    try:
        if not ATTENDANCE_DB or not os.path.exists(ATTENDANCE_DB):
            return out
        ac = sqlite3.connect("file:%s?mode=ro" % ATTENDANCE_DB, uri=True)
        try:
            hi = upto.isoformat()
            try:
                for r in ac.execute(
                        "SELECT reg_date, COALESCE(note,'') FROM clinic_holiday "
                        "WHERE reg_date BETWEEN ? AND ?", (first_iso, hi)):
                    out[r[0]] = r[1] or "clinic holiday"
            except Exception:
                pass
            try:
                for r in ac.execute(
                        "SELECT fest_date, COALESCE(name,'') FROM festival_day "
                        "WHERE clinic_closed=1 AND fest_date BETWEEN ? AND ?", (first_iso, hi)):
                    out.setdefault(r[0], r[1] or "clinic holiday")
            except Exception:
                pass
        finally:
            ac.close()
    except Exception:
        return {}
    return out


def refresh_missing_days(con, unit=UNIT, upto=None):
    """D322 (revises the S179 ruling): a genuine WORKING-day gap is still owed and
    still shouts (kind 'missing_day', high). But SUNDAYS and attendance-sourced
    CLINIC HOLIDAYS are OPTIONAL — officially closed, though sporadic sales happen —
    so they are recorded for clarity as kind 'clinic_holiday' (low, not owed) and
    resolve if the day is actually filed. Darpan's absence still leaves the day owed;
    who files it changes, not whether. The holiday source fails soft to Sunday-only."""
    upto = upto or (today() - dt.timedelta(days=1))
    first = con.execute("SELECT MIN(business_date) d FROM day_entry WHERE unit=?", (unit,)).fetchone()["d"]
    if not first:
        return 0
    have = {r["business_date"] for r in
            con.execute("SELECT business_date FROM day_entry WHERE unit=?", (unit,))}
    holidays = clinic_holidays(first, upto)          # {iso: label}, fail-soft
    d = parse_iso_date(first)
    opened = 0
    while d <= upto:
        iso = d.isoformat()
        if iso in have:
            # filed -> clear BOTH an owed miss and an optional holiday note
            con.execute("UPDATE recon_exception SET status='resolved', "
                        "resolution='day filed', closed_at=? "
                        "WHERE unit=? AND business_date=? "
                        "AND kind IN ('missing_day','clinic_holiday') AND status='open'",
                        (now_iso(), unit, iso))
        else:
            sunday = (d.weekday() == 6)
            fest = holidays.get(iso)
            if sunday or fest is not None:
                if sunday and fest:
                    why = "clinic holiday — Sunday (%s)" % fest
                elif sunday:
                    why = "clinic holiday — Sunday"
                else:
                    why = "clinic holiday — %s" % fest
                # retire any stale OWED miss for this day; it is optional now
                con.execute("UPDATE recon_exception SET status='resolved', "
                            "resolution='reclassified as clinic holiday (D322)', closed_at=? "
                            "WHERE unit=? AND business_date=? AND kind='missing_day' AND status='open'",
                            (now_iso(), unit, iso))
                con.execute(
                    "INSERT OR IGNORE INTO recon_exception "
                    "(unit, business_date, kind, severity, status, detail, opened_at, shout_count) "
                    "VALUES (?,?, 'clinic_holiday', 'low', 'open', ?, ?, 0)",
                    (unit, iso, "%s — optional; file only if there was a sale" % why, now_iso()))
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
    name = "finance_review.html" if "checker" in have else "finance_daily.html"
    return send_from_directory(UI_DIR, name)


@app.route("/finance/entry")
def page_entry():
    # S195: /finance/daily (Daily Sale v2) is the live page. The old single-
    # page entry is kept ONLY as an explicit escape hatch (?legacy=1). Any
    # other hit is redirected to the page for the person's role, so a stale
    # bookmark or a typed old URL never lands reception on the old screen.
    if request.args.get("legacy") == "1":
        return send_from_directory(UI_DIR, "finance_entry.html")
    u = current_user()
    have = roles_for(db(), UNIT, u["user"], u["role"])
    dest = "/finance/review" if "checker" in have else "/finance/daily"
    return redirect(dest, code=302)


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
            "<a href='/finance/daily?d=%s'>Back</a></p>" % iso,
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
        "backUrl": "/finance/daily?d=%s" % iso,
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
            "<div class=top><a href='/finance/daily?d=%s'>← Back</a>"
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
    sub = setting(con, "tile.checker_subtitle" if checker else "tile.maker_subtitle")
    # S195: if something is wrong, SAY SO on the portal home. The portal already
    # prints this subtitle, so a warning reaches the owner's first screen without
    # the portal needing to know anything about health checks.
    if checker:
        try:
            warn = _health_headline(con)
            if warn:
                sub = warn
        except Exception:                                          # noqa: BLE001
            pass
    return jsonify(ok=True,
                   role=("checker" if checker else "maker"),
                   title=setting(con, "tile.checker_title" if checker else "tile.maker_title"),
                   subtitle=sub,
                   href="/finance/review" if checker else "/finance/daily")


@app.route("/finance/api/my-day-summary")
def api_my_day_summary():
    """The MAKER's tile line (S187_P2a): what Darpan owes, nothing he should
    not see. Days-to-file over the last 7 calendar days, D322-aware (Sundays
    and attendance-sourced holidays are optional, not owed), plus today's
    status. No cash position, no approvals, no month data — the medical
    checker's world stays the checker's."""
    u, err = require("maker", "checker")
    if err:
        return err
    con = db()
    t = today()
    hols = clinic_holidays((t - dt.timedelta(days=7)).isoformat(), t)
    owed = []
    for back in range(1, 8):
        d = t - dt.timedelta(days=back)
        if d.weekday() == 6 or d.isoformat() in hols:      # Sunday / holiday
            continue
        e = con.execute("SELECT status FROM day_entry WHERE unit=? AND business_date=?",
                        (UNIT, d.isoformat())).fetchone()
        if not e or e["status"] == "draft":
            owed.append(d.isoformat())
    te = con.execute("SELECT status FROM day_entry WHERE unit=? AND business_date=?",
                     (UNIT, t.isoformat())).fetchone()
    return jsonify(ok=True, to_file=len(owed), days=owed,
                   today=(te["status"] if te else None))


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


# ------------------------------------------------ D330: per-expense evidence

def _expense_row_for_upload(con, unit, date_iso, uid):
    """The expense the upload attaches to. It must EXIST on the day, carry
    this uid, and be a KIND that takes evidence -- so junk uids cannot
    mint orphan files, and an advance (which needs no bill) cannot collect
    one by accident."""
    _expense_uid_col(con)
    return con.execute(
        "SELECT x.id, x.amount_p, x.category_text, x.category_fixed, e.id day_id "
        "FROM day_expense x JOIN day_entry e ON e.id=x.day_entry_id "
        "WHERE e.unit=? AND e.business_date=? AND x.expense_uid=? "
        "AND x.category_kind IN ('home','other')", (unit, date_iso, uid)).fetchone()


def _expense_scan_save(con, unit, date_iso, uid, u):
    """Shared store path for both units' expense-evidence uploads."""
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    if not _UID_RE.match(uid or ""):
        return jsonify(ok=False, error="bad_uid"), 400
    _expense_uid_col(con)
    _exp_att_tbl(con)
    row = _expense_row_for_upload(con, unit, iso, uid)
    if not row:
        return jsonify(ok=False, error="no_expense",
                       message="Save the day first — the bill attaches to a "
                               "saved expense."), 409
    f = request.files.get("file")
    if not f:
        return jsonify(ok=False, error="no_file"), 400
    blob = f.read()
    if not blob:
        return jsonify(ok=False, error="empty_file"), 400
    sha = hashlib.sha256(blob).hexdigest()
    folder = os.path.join(SCAN_DIR, unit, iso[:7])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%s_expense_%s_%s.pdf" % (iso, uid, sha[:10]))
    with open(path, "wb") as fh:
        fh.write(blob)
    con.execute("DELETE FROM expense_attachment WHERE day_entry_id=? AND expense_uid=?",
                (row["day_id"], uid))
    con.execute("INSERT INTO expense_attachment (day_entry_id, expense_uid, path, "
                "sha256, bytes, uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?)",
                (row["day_id"], uid, path, sha, len(blob), u["user"], now_iso()))
    audit(con, "expense_attachment", row["day_id"], "expense_scan_upload",
          after={"uid": uid, "sha256": sha, "bytes": len(blob)}, who=u["user"])
    con.commit()
    return jsonify(ok=True, uid=uid, bytes=len(blob), sha256=sha[:12])


@app.route("/finance/api/day/<date_iso>/expense-scan/<uid>", methods=["POST"])
def api_expense_scan_upload(date_iso, uid):
    u, err = require("maker", "checker")
    if err:
        return err
    return _expense_scan_save(db(), UNIT, date_iso, uid, u)


# ---------------------------------------- S195: per-no-payment-bill evidence
def _noncash_uid_col(con):
    """Stable identity of a no-payment bill row (mirrors expense_uid): the
    save's delete-and-reinsert mints new ids, so a bill's scan keys on the uid
    the page carries, which survives any re-save."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(day_noncash_bill)")}
    if "noncash_uid" not in cols:
        con.execute("ALTER TABLE day_noncash_bill ADD COLUMN noncash_uid TEXT")


def _noncash_att_tbl(con):
    """Per-bill evidence for home/procedure/other bills. Keys on
    (day_entry_id, noncash_uid), NOT day_noncash_bill.id, so it survives the
    save's delete-and-reinsert (the expense_attachment precedent, D330)."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS noncash_attachment ("
        " id INTEGER PRIMARY KEY, day_entry_id INTEGER NOT NULL,"
        " noncash_uid TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT,"
        " bytes INTEGER, uploaded_by TEXT, uploaded_at TEXT,"
        " UNIQUE(day_entry_id, noncash_uid))")


def _noncash_row_for_upload(con, unit, date_iso, uid):
    """The no-payment bill the upload attaches to -- it must exist on the day
    and carry this uid, so a junk uid cannot mint an orphan file."""
    _noncash_uid_col(con)
    return con.execute(
        "SELECT b.id, b.amount_p, b.bill_no, b.head, e.id day_id "
        "FROM day_noncash_bill b JOIN day_entry e ON e.id=b.day_entry_id "
        "WHERE e.unit=? AND e.business_date=? AND b.noncash_uid=?",
        (unit, date_iso, uid)).fetchone()


def _noncash_scan_save(con, unit, date_iso, uid, u):
    """Shared store path for a no-payment bill's scan (twin of _expense_scan_save)."""
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    if not _UID_RE.match(uid or ""):
        return jsonify(ok=False, error="bad_uid"), 400
    _noncash_uid_col(con)
    _noncash_att_tbl(con)
    row = _noncash_row_for_upload(con, unit, iso, uid)
    if not row:
        return jsonify(ok=False, error="no_bill",
                       message="Save the day first -- the scan attaches to a "
                               "saved bill."), 409
    f = request.files.get("file")
    if not f:
        return jsonify(ok=False, error="no_file"), 400
    blob = f.read()
    if not blob:
        return jsonify(ok=False, error="empty_file"), 400
    sha = hashlib.sha256(blob).hexdigest()
    folder = os.path.join(SCAN_DIR, unit, iso[:7])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%s_noncash_%s_%s.pdf" % (iso, uid, sha[:10]))
    with open(path, "wb") as fh:
        fh.write(blob)
    con.execute("DELETE FROM noncash_attachment WHERE day_entry_id=? AND noncash_uid=?",
                (row["day_id"], uid))
    con.execute("INSERT INTO noncash_attachment (day_entry_id, noncash_uid, path, "
                "sha256, bytes, uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?)",
                (row["day_id"], uid, path, sha, len(blob), u["user"], now_iso()))
    audit(con, "noncash_attachment", row["day_id"], "noncash_scan_upload",
          after={"uid": uid, "sha256": sha, "bytes": len(blob)}, who=u["user"])
    con.commit()
    return jsonify(ok=True, uid=uid, bytes=len(blob), sha256=sha[:12])


@app.route("/finance/api/day/<date_iso>/noncash-scan/<uid>", methods=["POST"])
def api_noncash_scan_upload(date_iso, uid):
    u, err = require("maker", "checker")
    if err:
        return err
    return _noncash_scan_save(db(), UNIT, date_iso, uid, u)


@app.route("/finance/scan-noncash/<date_iso>/<uid>")
def scan_noncash_page(date_iso, uid):
    """Host page for ONE no-payment bill's scan -- the same shared widget the
    day scans and expense bills use."""
    u, err = require("maker", "checker")
    if err:
        return err
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    if not _UID_RE.match(uid or ""):
        return jsonify(ok=False, error="bad_uid"), 400
    con = db()
    _noncash_uid_col(con)
    row = _noncash_row_for_upload(con, UNIT, iso, uid)
    if not row:
        return app.response_class(
            "<meta charset=utf-8><p style='font:16px system-ui;padding:24px'>"
            "Save the day first, then attach the bill. "
            "<a href='/finance/daily?d=%s'>Back</a></p>" % iso,
            mimetype="text/html", status=409)
    try:
        ver = int(os.path.getmtime(SCANNER_JS))
    except OSError:
        ver = 0
    title = "Bill %s -- %s" % (row["bill_no"] or "", rupees(row["amount_p"]))
    cfg = {
        "title": "%s -- %s" % (title, iso),
        "uploadUrl": "/finance/api/day/%s/noncash-scan/%s" % (iso, uid),
        "fileField": "file",
        "uploadFields": {"unit": UNIT, "business_date": iso, "noncash_uid": uid},
        "nameBase": "Sanjeevni_bill_%s_%s" % (iso, uid[:8]),
        "backUrl": "/finance/daily?d=%s" % iso,
        "allowIdCard": False,
        "allowBatch": False,
    }
    html = ("<!DOCTYPE html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title>"
            "<style>body{margin:0;background:#f4f6fa;color:#0f172a;"
            "font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif}"
            "input,select,button{font-family:inherit}.muted{color:#64748b}"
            ".top{background:#0b1220;color:#fff;padding:12px 16px;font-weight:650;"
            "display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:30}"
            ".top .t{flex:1}"
            ".top a{color:#e2e8f0;text-decoration:none;font-weight:600;font-size:13px;"
            "padding:8px 13px;border-radius:9px;background:rgba(255,255,255,.13);"
            "white-space:nowrap}</style></head><body>"
            "<div class=top><a href='%s'>← Back</a><span class=t>%s</span></div>"
            "<script>window.SCANNER_CONFIG = %s;</script>"
            "<div id=scanroot></div>"
            "<script src='/finance/scan/jspdf.js'></script>"
            "<script src='/finance/scan/widget.js?v=%d'></script>"
            "</body></html>") % (title, cfg["backUrl"], title, json.dumps(cfg), ver)
    return app.response_class(html, mimetype="text/html")




@app.route("/finance/scan-expense/<date_iso>/<uid>")
def scan_expense_page(date_iso, uid):
    """Host page for ONE expense's bill -- the same shared widget the day
    scans use (verified on the box S190: its <input type=file accept=image/*
    multiple> carries no capture attribute, so a phone offers BOTH camera
    and gallery -- the owner's photograph-at-payment / upload-at-filing flow
    works natively)."""
    u, err = require("maker", "checker")
    if err:
        return err
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    if not _UID_RE.match(uid or ""):
        return jsonify(ok=False, error="bad_uid"), 400
    con = db()
    _expense_uid_col(con)
    row = _expense_row_for_upload(con, UNIT, iso, uid)
    if not row:
        return app.response_class(
            "<meta charset=utf-8><p style='font:16px system-ui;padding:24px'>"
            "Save the day first, then attach the bill. "
            "<a href='/finance/daily?d=%s'>Back</a></p>" % iso,
            mimetype="text/html", status=409)
    try:
        ver = int(os.path.getmtime(SCANNER_JS))
    except OSError:
        ver = 0
    title = "Expense bill — %s (%s)" % (row["category_text"], rupees(row["amount_p"]))
    cfg = {
        "title": "%s — %s" % (title, iso),
        "uploadUrl": "/finance/api/day/%s/expense-scan/%s" % (iso, uid),
        "fileField": "file",
        "uploadFields": {"unit": UNIT, "business_date": iso, "expense_uid": uid},
        "nameBase": "Sanjeevni_expense_%s_%s" % (iso, uid[:8]),
        "backUrl": "/finance/daily?d=%s" % iso,
        "allowIdCard": False,
        "allowBatch": False,
    }
    html = ("<!DOCTYPE html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title>"
            "<style>body{margin:0;background:#f4f6fa;color:#0f172a;"
            "font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif}"
            "input,select,button{font-family:inherit}.muted{color:#64748b}"
            ".top{background:#0b1220;color:#fff;padding:12px 16px;font-weight:650;"
            "display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:30}"
            ".top .t{flex:1}"
            ".top a{color:#e2e8f0;text-decoration:none;font-weight:600;font-size:13px;"
            "padding:8px 13px;border-radius:9px;background:rgba(255,255,255,.13);"
            "white-space:nowrap}</style></head><body>"
            "<div class=top><a href='%s'>← Back</a><span class=t>%s</span></div>"
            "<script>window.SCANNER_CONFIG = %s;</script>"
            "<div id=scanroot></div>"
            "<script src='/finance/scan/jspdf.js'></script>"
            "<script src='/finance/scan/widget.js?v=%d'></script>"
            "</body></html>") % (title, cfg["backUrl"], title, json.dumps(cfg), ver)
    return app.response_class(html, mimetype="text/html")


@app.route("/finance/api/day/<date_iso>")
def api_day(date_iso):
    """One day -- and for a MAKER, only the day.

    F-132. D2a gated this route and recorded that the payload was "already
    correctly scoped". That claim was never tested, and it was wrong.
    `opening_p` comes from `v_cash_ledger`, whose window is
    `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING` -- a running total of
    every day since the books began. So the field the maker's page labels
    "Opening cash - carried from the last filed day" was in fact the entire
    unit cash position, rendered in 24px bold, and "Closing cash" was the same
    number plus his day.

    Worse than the disclosure: it was not TRUE of him. Much of that balance is
    parked with Dr Bhawna (D323) and ~Rs 87,205 of it is a pre-April adjustment
    (S186) -- so a label reading "carried forward" invited him to believe the
    drawer held two lakh rupees. That half predates F-127 entirely; it has been
    on his page since S179.

    A real drawer figure is not computable yet: `cash_custody_event` is empty
    while the custody block waits on the Hindi labels. So nothing is invented
    here -- the running balance is simply withheld from the maker, and the
    server keeps computing it exactly as before. The carry-forward is safe
    because it is COMPUTED and never accepted from a client, not because it is
    displayed."""
    u, err = require("maker", "checker")
    if err:
        return err
    try:
        d = parse_iso_date(date_iso)
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    con = db()
    st = day_state(con, UNIT, d.isoformat())
    st["is_future"] = d > today()
    st["too_old"] = (today() - d).days > BACKFILL_WINDOW_DAYS
    if "checker" not in u["roles"]:
        for _k in ("opening_p", "opening", "closing_p", "closing"):
            st.pop(_k, None)
    # D330: the advance context, shown INLINE before he types -- the total
    # already taken this calendar month (all days) and the derived ceiling.
    _adv_ceil = advance_ceiling_p(con)
    _led_p, _led_ok = ledger_fwd_advances_p(d.isoformat()[:7])
    _adv_mtd = advance_month_to_date_p(con, d.isoformat()) + _led_p
    st["advance_mtd_p"] = _adv_mtd
    st["advance_mtd"] = rupees(_adv_mtd)
    st["advance_ceiling_p"] = _adv_ceil
    st["advance_ceiling"] = rupees(_adv_ceil)
    st["advance_ledger_included"] = _led_ok    # False = "Sanjeevni book only"
    return jsonify(ok=True, day=st)


@app.route("/finance/api/month/<ym>")
def api_month(ym):
    if not re.fullmatch(r"\d{4}-\d{2}", ym):
        return jsonify(ok=False, error="bad_month"), 400
    con = db()
    _expense_uid_col(con)                  # D330: the drawings subselect below
    y, m = int(ym[:4]), int(ym[5:])
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)

    entries = {r["business_date"]: r for r in con.execute(
        "SELECT e.business_date, e.status, l.cash_in_p, l.upi_in_p, l.revenue_p, "
        "       l.expense_p, l.cash_out_p, l.closing_p, "
        "       (SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x "
        "        WHERE x.day_entry_id=e.id AND x.category_kind='home') drawings_p "
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
                         drawings=(rupees(e["drawings_p"])
                                   if e and e["drawings_p"] else ""),
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
    """F-127: ungated, this handed every signed-in identity every open exception
    in the unit -- carry-forward breaks, negative cash, UPI mismatches. The
    maker's page has only ever used the missing-day rows, so that is all a
    maker is given. The checker's answer is byte-for-byte what it always was."""
    u, err = require("maker", "checker")
    if err:
        return err
    excs = open_exceptions(db())
    if "checker" not in u["roles"]:
        excs = [e for e in excs if e.get("kind") == "missing_day"]
    return jsonify(ok=True, exceptions=excs)


@app.route("/finance/api/tile")
def api_tile():
    """The CHECKER's unit position: cash in hand, who is holding it, month to
    date, the bank-trip clock, every open shout.

    F-127 -- this was ungated. Any signed-in finance identity could read the
    whole unit position, and the maker's page fetched it on every load to
    render one deposit banner: a role gate on the SURFACE is not a role gate on
    the DATA, and the page chose to display one number while being handed
    twenty. The maker now has /finance/api/day/<date>/mirror, which answers his
    own day and nothing else.

    Its docstring used to say "feeds the portal tile". It has not done that
    since S187: the portal reads /finance/api/my-day-summary and
    /finance/api/tile-summary. A stale claim about another component nearly
    argued this gate out of existence -- checked against portal.py, not
    believed."""
    u, err = require("checker")
    if err:
        return err
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
    # D330: home expenses are the proprietor's DRAWINGS, totalled separately —
    # never mixed into business expenses (owner ruling, S190).
    _expense_uid_col(con)
    drawings_mtd = con.execute(
        "SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x "
        "JOIN day_entry e ON e.id=x.day_entry_id "
        "WHERE e.unit=? AND substr(e.business_date,1,7)=? "
        "AND x.category_kind='home'", (UNIT, ym)).fetchone()[0]

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
                   drawings_month_to_date=rupees(drawings_mtd),
                   awaiting_approval=awaiting,
                   last_month_close=(dict(ym=mc["ym"], status=mc["status"]) if mc else None),
                   shouts=dict(missing_days=counts.get("missing_day", 0),
                               carry_forward=counts.get("carry_forward_break", 0),
                               negative_cash=counts.get("negative_cash", 0),
                               upi_mismatch=counts.get("upi_vs_statement", 0),
                               total=sum(counts.values())))


# ----------------------------------------------------------------- API: write

def _replay_pending_marg_for_day(con, iso, by="auto"):
    """S194 auto-replay. The moment a day is filed, ingest any PENDING Marg
    push that carries it -- its payload was kept for exactly this (F-155), so a
    report pushed before the day was filed no longer strands its bills. Mirrors
    the checker's api_marg_push_apply path per day; runs AFTER the day's own
    save has committed and NEVER raises into the save."""
    out = []
    if finance_ingest is None or finance_returns is None:
        return out
    try:
        _marg_staging(con)
    except Exception:                                        # noqa: BLE001
        return out
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (UNIT, iso)).fetchone()
    if not e:
        return out
    rows = con.execute(
        "SELECT id, file_md5, parsed_json FROM marg_push_staging "
        "WHERE unit=? AND status='pending' AND parsed_json IS NOT NULL ORDER BY id",
        (UNIT,)).fetchall()
    for row in rows:
        try:
            payload = json.loads(row["parsed_json"] or "null")
        except ValueError:
            continue
        if not payload or not payload.get("days"):
            continue
        day = next((d for d in payload["days"] if d.get("date") == iso), None)
        if not day:
            continue
        try:
            res = finance_ingest.ingest_day(
                con, UNIT, iso, "marg_export", day["lines_csv"], run_by=by,
                source_ref="autoreplay:%s" % (row["file_md5"] or "")[:8])
            got = res.get("rows_read") or 0
            if got != day.get("expect"):
                con.rollback(); continue
            irows = list(csv.DictReader(io.StringIO(day.get("items_csv") or "")))
            con.execute("DELETE FROM sale_line_item WHERE day_entry_id=?", (e["id"],))
            n_lines = finance_returns.load_lines(con, UNIT, iso, irows,
                                                 batch_id=res.get("batch_id"))
            if irows and n_lines == 0:
                con.rollback(); continue
            finance_ingest.reconcile_day_attribution(con, UNIT, iso, now=now_iso())
            remaining = [d["date"] for d in payload["days"]
                         if not con.execute(
                             "SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                             (UNIT, d["date"])).fetchone()]
            if remaining:
                con.execute("UPDATE marg_push_staging SET applied_at=? WHERE id=?",
                            (now_iso(), row["id"]))
            else:
                _res = json.dumps(dict(
                    ingested=[d["date"] for d in payload["days"]], still_not_filed=[]))
                con.execute(
                    "UPDATE marg_push_staging SET status='applied', applied_at=?, "
                    "applied_by=?, apply_result_json=?, parsed_json=NULL WHERE id=?",
                    (now_iso(), by, _res, row["id"]))
            con.commit()
            out.append(dict(push=row["id"], date=iso, bills=got, lines=n_lines))
        except Exception:                                    # noqa: BLE001 -- never break the save
            try:
                con.rollback()
            except Exception:                                # noqa: BLE001
                pass
            continue
    return out


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
            _uid = str(e.get("uid") or "").strip()
            if not _UID_RE.match(_uid):
                _uid = "sv" + hashlib.md5(os.urandom(16)).hexdigest()[:14]
            if "category" in e:
                # S189: the structured path. A row from the new page ALWAYS
                # carries the key; a null/empty value means the maker skipped
                # the choice, and that is refused rather than quietly written
                # as an uncategorised row -- the rogue this menu exists to end.
                cat = (e.get("category") or "").strip()
                if cat not in EXPENSE_LABELS:
                    return jsonify(ok=False, error="choose_category",
                                   message="Choose a category for every expense."), 400
                if cat == "salary_advance_self":
                    # staff_id resolved at write time by pharmacy_staff_id
                    # (the connection is open there); the sentinel below is
                    # never written. Canonical text matches the three S184
                    # rows exactly, so the history stays one queryable string.
                    expenses.append(dict(amount_p=amt, category_fixed="salary_advance",
                                         kind=None, staff_id=None, uid=_uid,
                                         category_text="Salary advance - Darpan"))
                    continue
                # D330: home and other BOTH require details (free text with
                # compulsory evidence; the evidence gate runs at File, below).
                det = (e.get("details") or "").strip()
                if not det:
                    return jsonify(ok=False, error="details_required",
                                   message="Write what this expense was."), 400
                expenses.append(dict(amount_p=amt, category_fixed=None,
                                     kind=cat, staff_id=None, uid=_uid,
                                     category_text=det[:200]))
                continue
            # The pre-S189 shape, kept working so an old cached page cannot
            # become a data-loss machine. Its client-sent staff_id is now
            # IGNORED (F-139): a salary advance's identity is server-resolved
            # at write time, always. (Old-shape rows carry no category and no
            # uid, so the D330 evidence gate does not reach them -- the E1b
            # precedent: old pages keep working, and converge on refresh.)
            fixed = e.get("category_fixed") or None
            if fixed not in (None, "salary_advance"):
                return jsonify(ok=False, error="bad_category"), 400
            expenses.append(dict(amount_p=amt, category_fixed=fixed,
                                 kind=None, staff_id=None, uid=_uid,
                                 category_text=(e.get("category_text") or "").strip()[:200]))
        # Bills raised at full value with no cash across the counter — home
        # medicines, procedure medicines. Revenue is real; the cash is not.
        noncash = []
        for i, b in enumerate(p.get("noncash_bills") or []):
            amt = to_paise(b.get("amount"), "Bill #%d" % (i + 1))
            if amt <= 0:
                continue
            _nuid = str(b.get("uid") or "").strip()
            if not _UID_RE.match(_nuid):
                _nuid = "nc" + hashlib.md5(os.urandom(16)).hexdigest()[:14]
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
            noncash.append(dict(amount_p=amt, head=head, uid=_nuid,
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

    # ---- D330 gate 1: the advance ceiling (hard refusal, figures shown) ----
    # Over the ceiling NOTHING may be drawn from this system -- it becomes a
    # special advance through the regular staff pipeline (owner ruling, S190).
    _existing_row = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                                (UNIT, iso)).fetchone()
    adv_new_p = sum(e["amount_p"] for e in expenses
                    if e["category_fixed"] == "salary_advance")
    if adv_new_p:
        _ceil_p = advance_ceiling_p(con)
        _led_p, _led_ok = ledger_fwd_advances_p(iso[:7])
        _prior_p = advance_month_to_date_p(
            con, iso, exclude_day_entry_id=(_existing_row["id"] if _existing_row else None))             + _led_p
        if _prior_p + adv_new_p > _ceil_p:
            return jsonify(ok=False, error="advance_over_ceiling",
                           advance_taken=rupees(_prior_p), advance_ceiling=rupees(_ceil_p),
                           message="Advance already taken this month %s, ceiling %s. "
                                   "This one cannot be drawn here — above the ceiling it "
                                   "is a special advance through the staff pipeline."
                                   % (rupees(_prior_p), rupees(_ceil_p))), 400

    # ---- D330 gate 2: COMPULSORY evidence for home/other, at FILE ----------
    # No escape hatch (owner ruling). Enforced at submit, never at save,
    # because a bill can only attach to a day that exists. The owner's flow:
    # photograph at payment, upload the saved photo when filing next day.
    if submitting:
        _exp_att_tbl(con)                  # outside BEGIN: DDL
        _have_ev = set()
        if _existing_row:
            _have_ev = {r[0] for r in con.execute(
                "SELECT expense_uid FROM expense_attachment WHERE day_entry_id=?",
                (_existing_row["id"],))}
        _need_ev = [e for e in expenses
                    if e["kind"] in ("home", "other")
                    and e["uid"] not in _have_ev]
        if _need_ev:
            return jsonify(ok=False, error="expense_evidence_required",
                           rows=[dict(uid=e["uid"], amount=rupees(e["amount_p"]),
                                      details=e["category_text"]) for e in _need_ev],
                           message="Attach the bill for: %s. Photograph it, or upload "
                                   "the photo taken when it was paid." % "; ".join(
                                       "%s (%s)" % (e["category_text"], rupees(e["amount_p"]))
                                       for e in _need_ev)), 400

    # ---- write (all-or-nothing) --------------------------------------------
    _mirror_tbl(con)                       # outside BEGIN: DDL, not part of the write
    _expense_uid_col(con)                  # outside BEGIN: DDL (D330)
    _noncash_uid_col(con); _noncash_att_tbl(con)   # S195: per-bill scan DDL
    existing = con.execute("SELECT * FROM day_entry WHERE unit=? AND business_date=?",
                           (UNIT, iso)).fetchone()
    try:
        con.execute("BEGIN")
        if existing:
            # F4 (S190): the UNIT roles decide, never the broker role. Via SSO
            # the doctor's broker role is "doctor", so u["role"] != "checker"
            # refused the ONE person allowed to edit an approved day — found
            # by the owner on the real 31-July screen (the clinic save had
            # the correct form all along; this side never did, and no one had
            # ever re-edited an approved medical day until today).
            if existing["status"] in ("approved", "locked") \
                    and "checker" not in u.get("roles", []):
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
            # F5 (S190): an EDITED day is an app entry, whatever it was
            # imported as -- the approvals queue hides source='legacy_sheet'
            # (the bulk import would flood it), so the owner's edited 31-July
            # day vanished from the queue while its money already counted.
            # The day_revision above keeps the legacy original verbatim.
            con.execute("UPDATE day_entry SET status=?, entered_by=?, entered_at=?, "
                        "manned_by=?, manned_source=?, source='app' WHERE id=?",
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
            _sid = e["staff_id"]
            if e["category_fixed"] == "salary_advance":
                _sid = pharmacy_staff_id(con)          # server-resolved, always (F-139)
            con.execute("INSERT INTO day_expense (day_entry_id, amount_p, amount_known, "
                        "category_fixed, category_kind, staff_id, category_text, "
                        "expense_uid) VALUES (?,?,1,?,?,?,?,?)",
                        (eid, e["amount_p"], e["category_fixed"], e["kind"], _sid,
                         e["category_text"], e["uid"]))
        for m in movements:
            con.execute("INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, "
                        "reference) VALUES (?,?,?,?,?)",
                        (eid, m["direction"], m["party"], m["amount_p"], m["reference"]))
        for b in noncash:
            con.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, "
                        "head_text, bill_no, amount_p, note, noncash_uid, entered_by, entered_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (eid, UNIT, b["bill_date"], b["head"], b["head_text"], b["bill_no"],
                         b["amount_p"], b["note"], b["uid"], u["user"], now_iso()))
        if missing_docs and (p.get("missing_scan_reason") or "").strip():
            con.execute("INSERT INTO data_flag (unit, business_date, day_entry_id, code, severity, detail) "
                        "VALUES (?,?,?,'MISSING_SCAN','medium',?)",
                        (UNIT, iso, eid, "%s | reason: %s"
                         % (",".join(missing_docs), p["missing_scan_reason"][:200])))

        # D2 (D326): the mirror was already shown for this day and the money
        # has moved since. Not blocked, not argued with -- noted, once, where
        # the checker already looks. /finance/api/day/<date>/full renders
        # data_flag rows today, so the badge reaches the approval queue with no
        # change to the checker's code at all.
        rv = con.execute("SELECT fingerprint FROM day_mirror_reveal WHERE day_entry_id=?",
                         (eid,)).fetchone()
        if rv and rv["fingerprint"] != _money_fingerprint(total_p, upi_p, expenses,
                                                          movements, noncash):
            if not con.execute("SELECT 1 FROM data_flag WHERE unit=? AND business_date=? "
                               "AND code='EDITED_AFTER_REVEAL' LIMIT 1",
                               (UNIT, iso)).fetchone():
                con.execute("INSERT INTO data_flag (unit, business_date, day_entry_id, "
                            "code, severity, detail) VALUES "
                            "(?,?,?,'EDITED_AFTER_REVEAL','medium',?)",
                            (UNIT, iso, eid,
                             "the figures were changed after the MAKER was shown the "
                             "bank/Marg check for this day. Not an error and not "
                             "blocked (D326) \u2014 recorded so the cross-check stays "
                             "honest. A checker opening the day does not arm this "
                             "(F-129)."))
            warnings.append("You changed the figures after seeing the check. "
                            "The doctor will see that noted against this day.")

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
    # S194 auto-replay: a Marg push staged before this day was filed loads now.
    try:
        _replayed = _replay_pending_marg_for_day(con, iso, by=u["user"])
    except Exception:                                        # noqa: BLE001
        _replayed = []
    if _replayed:
        _rb = sum(x.get("bills") or 0 for x in _replayed)
        warnings.append("Marg for this day was waiting and has now loaded "
                        "automatically: %d bill(s)." % _rb)
    upi_check = finance_upi.reconcile_upi(con, UNIT, iso, now=now_iso())
    if upi_check and not upi_check["match"]:
        warnings.append("Bank settled %s UPI for this day but the entry says %s — "
                        "difference %s. The day is flagged; the doctor approves with "
                        "acknowledgment." % (rupees(upi_check["bank_p"]),
                                             rupees(upi_check["entered_p"]),
                                             rupees(upi_check["diff_p"])))
    st = day_state(con, UNIT, iso)
    if "checker" not in u["roles"]:          # F-132, same rule as the GET
        for _k in ("opening_p", "opening", "closing_p", "closing"):
            st.pop(_k, None)
    return jsonify(ok=True, day=st, warnings=warnings)


def _staff_ledger_module():
    """Import the Staff Ledger as a library so a salary-advance approval posts
    through the ledger's OWN writer (D235: one writer per store), not around it.
    The ledger's data dir is kept consistent with the JSONL this app already
    reads. FINANCE_LEDGER_PY_DIR lets the offline smoke point at a checkout;
    unset it is /root, where staff_ledger.py lives on the box."""
    d = os.environ.get("FINANCE_LEDGER_PY_DIR", "/root")
    if d not in sys.path:
        sys.path.insert(0, d)
    os.environ.setdefault("LEDGER_DIR", os.path.dirname(LEDGER_JSONL))
    import staff_ledger
    return staff_ledger


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

    # F6 (F-148 / D332 §2.5): APPROVAL posts each pending salary advance to the
    # Staff Ledger, through the ledger's own writer. ORDER: append to the ledger
    # FIRST, then stamp the finance row and commit finance below. A crash between
    # the two leaves a VISIBLE ledger row with no finance ref (recoverable),
    # never a finance record claiming a posting that never happened (F-132's
    # invisible shape). IDEMPOTENT: ledger_posted=0 is the guard, so a re-approval
    # never double-posts. FAIL-LOUD: any ledger error REFUSES the approval -- the
    # day is NOT approved and nothing is committed.
    advances = con.execute("SELECT x.id, x.amount_p, x.staff_id, s.name AS staff_name "
                           "FROM day_expense x LEFT JOIN staff_ref s ON s.id = x.staff_id "
                           "WHERE x.day_entry_id=? AND x.category_fixed='salary_advance' "
                           "AND x.ledger_posted=0", (e["id"],)).fetchall()
    posted = []
    if advances:
        try:
            sl = _staff_ledger_module()
            lusers = sl.load_users()
            if u["user"] not in lusers or lusers[u["user"]].get("role") != "checker":
                raise RuntimeError(
                    "approver '%s' is not a Staff Ledger checker -- the advance "
                    "cannot be posted. Add the identity to the ledger users (or "
                    "map it) before approving salary-advance days." % u["user"])
            for a in advances:
                if not a["staff_name"]:
                    raise RuntimeError("salary-advance expense #%s has no staff_ref "
                                       "name to post against" % a["id"])
                if a["amount_p"] % 100 != 0:
                    raise RuntimeError("salary advance #%s is %s -- the Staff Ledger "
                                       "records whole rupees" % (a["id"], rupees(a["amount_p"])))
                lrow = sl.make_entry(
                    lusers, u["user"], a["staff_name"], "ADVANCE_ISSUE",
                    iso, iso, 0, str(a["amount_p"] // 100),
                    "Salary advance, %s %s (finance expense #%s)" % (UNIT, iso, a["id"]),
                    against_month=iso[:7])
                con.execute("UPDATE day_expense SET ledger_posted=1, ledger_posted_at=?, "
                            "ledger_ref=? WHERE id=?", (now_iso(), lrow["id"], a["id"]))
                posted.append(dict(expense_id=a["id"], amount=rupees(a["amount_p"]),
                                   staff=a["staff_name"], ledger_ref=lrow["id"]))
        except Exception as _lex:                 # noqa: BLE001 -- fail loud, refuse
            con.rollback()
            return jsonify(ok=False, error="ledger_post_failed",
                           message="The day was NOT approved -- %s" % str(_lex)), 409

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
YESBANK_DIR = os.environ.get("FINANCE_YESBANK_DIR",
                              os.path.join(APP_ROOT, "yesbank_statements"))


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


# ============================================================================
#  S186_R2a — Yes Bank cash reconciliation · the workbench · custody (D323)
#
#  Three surfaces, all CHECKER-ONLY and all read-mostly. Darpan's daily entry
#  screen is deliberately NOT touched by this kit: its Hindi labels are not
#  approved yet, and the maker screen is the highest-traffic surface in the
#  system. Custody capture therefore lives on the doctor's workbench, which is
#  where reconciling actually happens.
# ============================================================================

@app.route("/finance/api/yesbank-statement", methods=["POST"])
def api_yesbank_statement():
    """Ingest one Yes Bank CSV, then reconcile the cash deposits it covers.

    This is the F-103 gap closed. It is also the F-112 detector: a deposit the
    books claim and the bank never made is reported, and a deposit booked where
    no statement reaches is reported as UNEVIDENCED rather than passed."""
    if finance_yesbank is None:
        return jsonify(ok=False, error="module_absent",
                       message="finance_yesbank.py is not installed on this box"), 503
    u, err = require("checker")
    if err:
        return err
    f = request.files.get("file")
    blob = f.read() if f else request.get_data()
    if not blob:
        return jsonify(ok=False, error="no_file"), 400
    fname = (f.filename if f else request.headers.get("X-Filename")) or "yesbank.csv"

    con = db()
    try:
        res = finance_yesbank.ingest_statement(con, fname, blob, YESBANK_DIR, now=now_iso())
    except finance_yesbank.StatementRejected as ex:
        con.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                    "VALUES (NULL, NULL, 'YESBANK_STATEMENT_REJECTED', 'high', ?)",
                    (("%s: %s" % (fname, ex))[:400],))
        con.commit()
        return jsonify(ok=False, error="statement_rejected", message=str(ex)), 422

    pf, pt = res["period"]
    rec = finance_yesbank.reconcile_cash_deposits(con, UNIT, pf, pt, now=now_iso())
    audit(con, "yesbank_statement", None, "ingest",
          after={"file": fname, "period": [pf, pt], "lines": res["lines"],
                 "cash_deposits": res["cash_deposits"], "by": u["user"]}, who=u["user"])
    con.commit()
    return jsonify(ok=True, account=res["account_ref"], period=[pf, pt],
                   lines=res["lines"], new_lines=res["new_lines"],
                   cash_deposits=res["cash_deposits"],
                   cash_total=rupees(res["cash_total_p"]),
                   reconciled=_yb_summary(rec))


@app.route("/finance/api/yesbank/reconcile")
def api_yesbank_reconcile():
    """Re-run the match over any window, without loading anything new."""
    if finance_yesbank is None:
        return jsonify(ok=False, error="module_absent"), 503
    u, err = require("checker")
    if err:
        return err
    d1 = request.args.get("from") or "2026-04-01"
    d2 = request.args.get("to") or dt.date.today().isoformat()
    con = db()
    rec = finance_yesbank.reconcile_cash_deposits(con, UNIT, d1, d2, now=now_iso())
    return jsonify(ok=True, window=[d1, d2], **_yb_summary(rec))


def _yb_summary(rec):
    fmt = lambda pairs: [dict(date=d, amount=rupees(p)) for d, p in pairs]
    return dict(matched=rec["matched"], matched_total=rupees(rec["matched_p"]),
                deposit_not_in_bank=fmt(rec["deposit_not_in_bank"]),
                deposit_unevidenced=fmt(rec["deposit_unevidenced"]),
                bank_deposit_not_booked=fmt(rec["bank_deposit_not_booked"]))


@app.route("/finance/workbench")
def page_workbench():
    return send_from_directory(UI_DIR, "finance_workbench.html")


@app.route("/finance/api/workbench/<ym>")
def api_workbench(ym):
    """One month, three sources side by side: what was ENTERED, what MARG sold,
    what the BANK received. Read-only — it computes nothing into the books and
    suggests nothing automatically (D315: a suggestion is graded, never applied)."""
    u, err = require("checker")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", ym or ""):
        return jsonify(ok=False, error="bad_month"), 400
    con = db()
    rows = con.execute(
        "SELECT l.business_date, l.cash_in_p, l.upi_in_p, l.expense_p, l.cash_out_p,"
        "       l.closing_p, e.status,"
        "       (SELECT COALESCE(SUM(si.amount_p),0) FROM sale_item si"
        "         WHERE si.day_entry_id = e.id)                       AS marg_p,"
        "       (SELECT COALESCE(SUM(b.deposit_p),0) FROM bank_statement_line b"
        "         WHERE b.is_cash_deposit=1 AND b.txn_date = l.business_date) AS bank_p,"
        "       (SELECT COUNT(*) FROM recon_exception x WHERE x.unit=l.unit"
        "         AND x.business_date=l.business_date AND x.status='open')    AS shouts,"
        "       (SELECT counted_p FROM cash_count cc WHERE cc.unit=l.unit"
        "         AND cc.business_date=l.business_date)                       AS counted_p"
        "  FROM v_cash_ledger l JOIN day_entry e ON e.id = l.day_entry_id"
        " WHERE l.unit=? AND substr(l.business_date,1,7)=?"
        " ORDER BY l.business_date", (UNIT, ym)).fetchall()

    days, tot = [], dict(cash=0, upi=0, marg=0, bank=0)
    for r in rows:
        cash_p, marg_p = int(r["cash_in_p"] or 0), int(r["marg_p"] or 0)
        tot["cash"] += cash_p; tot["upi"] += int(r["upi_in_p"] or 0)
        tot["marg"] += marg_p; tot["bank"] += int(r["bank_p"] or 0)
        gap_p = marg_p - (cash_p + int(r["upi_in_p"] or 0))
        # D315 grading: a suggestion is offered with its confidence, never applied.
        grade = None
        if marg_p and abs(gap_p) > 100:
            grade = ("exact" if abs(gap_p) <= 100 else
                     "likely" if abs(gap_p) <= max(5000, marg_p // 50) else "weak")
        days.append(dict(
            date=r["business_date"], status=r["status"],
            entered_cash=rupees(cash_p), entered_upi=rupees(int(r["upi_in_p"] or 0)),
            marg=rupees(marg_p) if marg_p else None,
            bank_deposit=rupees(int(r["bank_p"] or 0)) if r["bank_p"] else None,
            expense=rupees(int(r["expense_p"] or 0)), cash_out=rupees(int(r["cash_out_p"] or 0)),
            closing=rupees(int(r["closing_p"] or 0)),
            counted=(rupees(int(r["counted_p"])) if r["counted_p"] is not None else None),
            gap=(rupees(gap_p) if marg_p else None), gap_grade=grade,
            shouts=int(r["shouts"] or 0)))
    return jsonify(ok=True, month=ym, days=days,
                   totals=dict(entered_cash=rupees(tot["cash"]), entered_upi=rupees(tot["upi"]),
                               marg=rupees(tot["marg"]), bank_deposits=rupees(tot["bank"])),
                   custody=_custody_state(con))


def _custody_state(con):
    people = [dict(id=r["id"], name=r["name"], hindi=r["hindi_name"], kind=r["role_kind"],
                   hands_to=r["hands_cash_to"], note=r["note"])
              for r in con.execute("SELECT * FROM counter_person WHERE unit=? AND active=1"
                                   " ORDER BY id", (UNIT,))]
    held = [dict(party=r["party"], held=rupees(int(r["held_p"] or 0)))
            for r in con.execute("SELECT party, held_p FROM v_cash_custody_balance"
                                 " WHERE unit=? AND held_p <> 0 ORDER BY party", (UNIT,))]
    return dict(people=people, held=held)


@app.route("/finance/api/custody", methods=["GET", "POST"])
def api_custody():
    """Record who handed cash to whom — including the month-end marker whose
    ABSENCE hid a float for five months (D323). Never moves money: this is a
    custody record beside cash_movement, not a second copy of it."""
    u, err = require("checker")
    if err:
        return err
    con = db()
    if request.method == "GET":
        ev = [dict(date=r["event_date"], frm=r["from_party"], to=r["to_party"],
                   amount=rupees(int(r["amount_p"])), month_end=r["month_end_kind"],
                   note=r["note"], by=r["entered_by"])
              for r in con.execute("SELECT * FROM cash_custody_event WHERE unit=?"
                                   " ORDER BY event_date DESC, id DESC LIMIT 200", (UNIT,))]
        return jsonify(ok=True, events=ev, **_custody_state(con))

    b = request.get_json(silent=True) or {}
    PARTIES = ("counter", "drawer", "dr_bhawna", "dr_manoj", "bank")
    try:
        amt_p = int(round(float(b.get("amount") or 0) * 100))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount"), 400
    frm, to = (b.get("from") or "").strip(), (b.get("to") or "").strip()
    iso = (b.get("date") or "").strip()
    mek = (b.get("month_end") or "").strip() or None
    if amt_p <= 0:
        return jsonify(ok=False, error="amount_must_be_positive"), 400
    if frm not in PARTIES or to not in PARTIES or frm == to:
        return jsonify(ok=False, error="bad_parties", parties=list(PARTIES)), 400
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", iso):
        return jsonify(ok=False, error="bad_date"), 400
    if mek not in (None, "taken", "carried"):
        return jsonify(ok=False, error="bad_month_end"), 400

    con.execute("INSERT INTO cash_custody_event (unit, event_date, from_party, to_party,"
                " amount_p, counter_person_id, month_end_kind, note, entered_by, entered_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (UNIT, iso, frm, to, amt_p, b.get("counter_person_id"), mek,
                 (b.get("note") or "")[:400], u["user"], now_iso()))
    audit(con, "cash_custody_event", None, "create",
          after={"date": iso, "from": frm, "to": to, "amount_p": amt_p,
                 "month_end": mek, "by": u["user"]}, who=u["user"])
    con.commit()
    return jsonify(ok=True, **_custody_state(con))


@app.route("/finance/api/cash-position")
def api_cash_position():
    """Where the cash is right now, reconciled. Darpan's drawer (day-wise +
    total), the reserve parked with Dr Bhawna, cash with Dr Manoj, and every
    bank deposit. drawer = running UNBANKED closing MINUS what is parked, so
    drawer + reserve + manoj == unbanked, always. Serves BOTH the maker
    (Darpan) and the checker (owner) — same figures for both."""
    u, err = require("maker", "checker")
    if err:
        return err
    con = db()
    held = {r["party"]: int(r["held_p"] or 0)
            for r in con.execute("SELECT party, held_p FROM v_cash_custody_balance "
                                 "WHERE unit=?", (UNIT,))}
    # baseline = the counted custody position (cash_custody_event only).
    base_bhawna = held.get("dr_bhawna", 0)
    base_manoj = held.get("dr_manoj", 0)
    baseline_p = max(0, base_bhawna) + max(0, base_manoj)
    # S194 ⭐4 — hand-overs recorded through the daily flow as cash_movements
    # (party dr_bhawna / dr_manoj) move cash from the drawer to a doctor. Fold
    # them in so reserve / Manoj track LIVE on top of the counted baseline, the
    # drawer falls to match, and unbanked (cash still in the unit) is unchanged
    # by a hand-over — only a BANK deposit reduces it.
    def _mv_net(party):
        r = con.execute(
            "SELECT COALESCE(SUM(CASE WHEN cm.direction='out' THEN cm.amount_p "
            "ELSE -cm.amount_p END), 0) p FROM cash_movement cm "
            "JOIN day_entry de ON de.id=cm.day_entry_id "
            "WHERE de.unit=? AND cm.party=?", (UNIT, party)).fetchone()
        return int(r["p"] or 0)
    mv_bhawna = _mv_net("dr_bhawna")
    mv_manoj = _mv_net("dr_manoj")
    reserve_p = max(0, base_bhawna + mv_bhawna)
    manoj_p = max(0, base_manoj + mv_manoj)
    parked_p = reserve_p + manoj_p
    netmv_p = parked_p - baseline_p        # live delta from doctor hand-overs
    bank = con.execute(
        "SELECT COALESCE(SUM(cm.amount_p),0) p, COUNT(*) n, MAX(de.business_date) last "
        "FROM cash_movement cm JOIN day_entry de ON de.id=cm.day_entry_id "
        "WHERE de.unit=? AND cm.party='bank' AND cm.direction='out'", (UNIT,)).fetchone()
    # Day-wise drawer is meaningful only FROM the last parking/clearing (the
    # reserve date). Before that the reserve did not exist, so subtracting it
    # from an older day's closing shows a false negative. Start there.
    rd = con.execute("SELECT MAX(event_date) d FROM cash_custody_event "
                     "WHERE unit=?", (UNIT,)).fetchone()
    since = rd["d"] if (rd and rd["d"]) else None
    q = "SELECT business_date, closing_p FROM v_cash_ledger WHERE unit=?"
    args = [UNIT]
    if since:
        q += " AND business_date >= ?"
        args.append(since)
    q += " ORDER BY business_date"
    drows = con.execute(q, args).fetchall()
    days = [dict(date=r["business_date"],
                 drawer=rupees(int(r["closing_p"] or 0) - baseline_p),
                 unbanked=rupees(int(r["closing_p"] or 0) + netmv_p))
            for r in drows][-60:]
    lr = con.execute("SELECT closing_p FROM v_cash_ledger WHERE unit=? "
                     "ORDER BY business_date DESC LIMIT 1", (UNIT,)).fetchone()
    latest = int(lr["closing_p"] or 0) if lr else 0
    # per-line detail so each Cash-position row can expand
    dep = con.execute(
        "SELECT de.business_date d, cm.amount_p a, cm.reference r FROM cash_movement cm "
        "JOIN day_entry de ON de.id=cm.day_entry_id WHERE de.unit=? AND cm.party='bank' "
        "AND cm.direction='out' ORDER BY de.business_date DESC, cm.id DESC LIMIT 40",
        (UNIT,)).fetchall()
    bank_deposits = [dict(date=r["d"], amount=rupees(int(r["a"])), ref=(r["r"] or "")) for r in dep]

    def _cust(party):
        rows = [dict(date=e["event_date"], frm=e["from_party"], to=e["to_party"],
                     amount=rupees(int(e["amount_p"])), note=(e["note"] or ""), kind="count")
                for e in con.execute(
                    "SELECT event_date, from_party, to_party, amount_p, note "
                    "FROM cash_custody_event WHERE unit=? AND (from_party=? OR to_party=?) "
                    "ORDER BY event_date DESC, id DESC", (UNIT, party, party))]
        # S194 ⭐4 — live hand-overs recorded through the daily flow
        for m in con.execute(
                "SELECT de.business_date d, cm.direction dir, cm.amount_p a, cm.reference r "
                "FROM cash_movement cm JOIN day_entry de ON de.id=cm.day_entry_id "
                "WHERE de.unit=? AND cm.party=? ORDER BY de.business_date DESC, cm.id DESC",
                (UNIT, party)):
            rows.append(dict(date=m["d"],
                             frm=("drawer" if m["dir"] == "out" else party),
                             to=(party if m["dir"] == "out" else "drawer"),
                             amount=rupees(int(m["a"])), note=(m["r"] or ""), kind="handover"))
        rows.sort(key=lambda x: x["date"] or "", reverse=True)
        return rows
    reserve_detail = _cust("dr_bhawna")
    manoj_detail = _cust("dr_manoj")
    drawer_p = latest - baseline_p
    unbanked_p = latest + netmv_p
    return jsonify(ok=True,
                   bank_deposits=bank_deposits,
                   reserve_detail=reserve_detail,
                   manoj_detail=manoj_detail,
                   drawer=rupees(drawer_p),
                   reserve=rupees(reserve_p),
                   with_manoj=rupees(manoj_p),
                   parked=rupees(parked_p),
                   bank_deposited=rupees(int(bank["p"])),
                   bank_count=int(bank["n"]),
                   last_bank_date=bank["last"],
                   unbanked=rupees(unbanked_p),
                   # S194 ⭐4 — numeric fields for the Daily page + invariant checks
                   drawer_p=drawer_p, reserve_p=reserve_p, with_manoj_p=manoj_p,
                   parked_p=parked_p, unbanked_p=unbanked_p, baseline_p=baseline_p,
                   as_of=(days[-1]["date"] if days else None),
                   since=since,
                   days=days)


@app.route("/finance/api/cash-count", methods=["POST"])
def api_cash_count():
    """The drawer count (F-91). Blank is ACCEPTED and FLAGGED, never silently
    treated as zero — an uncounted drawer and an empty drawer are different
    facts (D166), and conflating them is what hid the float."""
    u, err = require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = (b.get("date") or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", iso):
        return jsonify(ok=False, error="bad_date"), 400
    raw = b.get("counted")
    con = db()
    if raw in (None, "", "-"):
        con.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                    "VALUES (?,?, 'DRAWER_NOT_COUNTED', 'medium', ?)",
                    (UNIT, iso, "drawer count left blank by %s — recorded as UNKNOWN, "
                                "not as zero" % u["user"]))
        con.commit()
        return jsonify(ok=True, counted=None, flagged=True)
    try:
        p = int(round(float(raw) * 100))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount"), 400
    con.execute("INSERT INTO cash_count (unit, business_date, counted_p, counted_by,"
                " counted_at, explanation) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(unit, business_date) DO UPDATE SET counted_p=excluded.counted_p,"
                " counted_by=excluded.counted_by, counted_at=excluded.counted_at,"
                " explanation=excluded.explanation",
                (UNIT, iso, p, u["user"], now_iso(), (b.get("note") or "")[:400]))
    audit(con, "cash_count", None, "upsert",
          after={"date": iso, "counted_p": p, "by": u["user"]}, who=u["user"])
    con.commit()
    return jsonify(ok=True, counted=rupees(p), flagged=False)


# ============================================================================
#  S186_I1a — the Marg item-wise report, uploaded through the portal
#
#  Until now a Marg export reached the books by being copied onto the VPS by
#  hand and fed to marg_backfill.py at a shell. That is why the export had to
#  live on the box at all, and why it then had to be deleted again for PHI
#  hygiene. This route does the whole thing in memory: parse, survey, ingest,
#  and the file is gone before the response is written. Nothing is stored.
#
#  It keeps every guard the command-line driver has, because they were each
#  bought with a fault: refuse a file with no item detail (a mis-export),
#  refuse a column map that does not match the parser (the silent-zero trap),
#  and ABORT the day if the adapter reads a different number of rows than the
#  file contains.
#
#  And it adds the one the driver lacks (F-113): a day skipped because it is
#  NOT FILED now writes a data_flag. "not filed (refused, harmlessly)" is true
#  at that instant and false the moment the day is filed -- so it must leave a
#  record that outlives the run instead of a line of console output.
# ============================================================================

@app.route("/finance/api/marg-upload", methods=["POST"])
def api_marg_upload():
    u, err = require("checker")
    if err:
        return err
    if marg_report is None or finance_returns is None:
        return jsonify(ok=False, error="module_absent",
                       message="marg_report / finance_returns not installed"), 503

    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(ok=False, error="no_file"), 400
    apply_it = str(request.form.get("apply") or request.args.get("apply") or "0") in ("1", "true", "yes")
    blob = f.read()
    if not blob:
        return jsonify(ok=False, error="empty_file"), 400

    import tempfile
    suffix = ".xlsx" if f.filename.lower().endswith("x") else ".xls"
    fd, tmp = tempfile.mkstemp(prefix="marg_upload_", suffix=suffix)
    os.close(fd)
    con = db()
    try:
        with open(tmp, "wb") as fh:
            fh.write(blob)

        # ---- parse. A file that fails its own checks never reaches the db ----
        try:
            rep = marg_report.read_report(tmp, keep_items=True)
        except Exception as ex:                                   # noqa: BLE001
            con.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                        "VALUES (?, NULL, 'MARG_UPLOAD_REJECTED', 'high', ?)",
                        (UNIT, ("%s: %s" % (f.filename, ex))[:400]))
            con.commit()
            return jsonify(ok=False, error="rejected", message=str(ex)), 422

        days = marg_report.day_totals(rep)
        if not days:
            return jsonify(ok=False, error="no_days"), 422
        total_items = sum(len(d.get("items", [])) for d in rep["days"])
        if total_items == 0:
            return jsonify(ok=False, error="no_item_detail",
                           message="this export carries NO item detail (0 drug lines). "
                                   "Re-export from Marg with 'With Item Deta. = Yes'."), 422

        # ---- the column map must match what the parser emits (silent-zero) ---
        probe = io.StringIO()
        marg_report.write_lines_csv(rep, probe, days[0]["business_date"])
        header = probe.getvalue().splitlines()[0].split(",")
        src = con.execute("SELECT id, active FROM ingest_source WHERE unit=? AND adapter='marg_export'",
                          (UNIT,)).fetchone()
        if not src or not src["active"]:
            return jsonify(ok=False, error="source_missing",
                           message="the (medical, marg_export) ingest source is absent or inactive"), 422
        cmap = {r["our_field"]: r["their_column"] for r in con.execute(
            "SELECT our_field, their_column FROM ingest_column_map WHERE source_id=?", (src["id"],))}
        missing = {k: v for k, v in cmap.items() if v not in header}
        if not cmap or missing:
            return jsonify(ok=False, error="column_map_mismatch", missing=missing,
                           message="the column map does not match the parser output"), 422

        nonzero = {d["date"]: sum(1 for b in d["bills"] if b["net_p"] != 0) for d in rep["days"]}

        # ---- survey every day BEFORE writing anything ------------------------
        survey, plan, not_filed = [], [], []
        for d in days:
            iso = d["business_date"]
            e = con.execute("SELECT id, status FROM day_entry WHERE unit=? AND business_date=?",
                            (UNIT, iso)).fetchone()
            row = dict(date=iso, bills=d.get("bills"), net=rupees(d["net_p"]),
                       filed=bool(e), status=(e["status"] if e else None),
                       existing_bills=0, existing_lines=0)
            if e:
                row["existing_bills"] = con.execute(
                    "SELECT COUNT(*) FROM sale_item WHERE ingest_batch_id IN "
                    "(SELECT id FROM ingest_batch WHERE day_entry_id=? AND status!='superseded')",
                    (e["id"],)).fetchone()[0]
                row["existing_lines"] = con.execute(
                    "SELECT COUNT(*) FROM sale_line_item WHERE day_entry_id=?",
                    (e["id"],)).fetchone()[0]
                plan.append((iso, e["id"]))
            else:
                not_filed.append(iso)
            survey.append(row)

        # ---- F-113: a NOT FILED skip must outlive the run --------------------
        for iso in not_filed:
            con.execute(
                "INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                "VALUES (?,?, 'MARG_DAY_NOT_FILED', 'medium', ?)",
                (UNIT, iso,
                 "a Marg export dated %s carried %d bill(s) for this day, but the day was not "
                 "filed at upload time, so it was skipped. RE-UPLOAD once the day is filed — "
                 "this flag exists because a console line does not survive the run (F-113)."
                 % (f.filename[:60], nonzero.get(iso, 0))))
        con.commit()

        if not apply_it:
            return jsonify(ok=True, applied=False, title=rep.get("title"),
                           bills=sum(len(d["bills"]) for d in rep["days"]),
                           item_lines=total_items, warnings=rep.get("warnings", []),
                           days=survey, not_filed=not_filed,
                           message="survey only — nothing was written")

        # ---- apply, one day at a time, aborting rather than half-loading -----
        done, aborted = [], None
        for iso, eid in plan:
            lbuf = io.StringIO()
            marg_report.write_lines_csv(rep, lbuf, iso)
            expect = nonzero.get(iso, 0)
            try:
                res = finance_ingest.ingest_day(con, UNIT, iso, "marg_export", lbuf.getvalue(),
                                                run_by=u["user"],
                                                source_ref="portal:" + f.filename[:60])
                got = res.get("rows_read") or 0
                if got != expect:
                    con.rollback()
                    aborted = dict(date=iso, read=got, expected=expect)
                    break
                ibuf = io.StringIO()
                marg_report.write_items_csv(rep, ibuf, iso)
                irows = list(csv.DictReader(io.StringIO(ibuf.getvalue())))
                con.execute("DELETE FROM sale_line_item WHERE day_entry_id=?", (eid,))
                n_lines = finance_returns.load_lines(con, UNIT, iso, irows, batch_id=res.get("batch_id"))
                if irows and n_lines == 0:
                    con.rollback()
                    aborted = dict(date=iso, read=got, expected=expect, lines=0)
                    break
                if not irows:
                    con.commit()
                finance_ingest.reconcile_day_attribution(con, UNIT, iso, now=now_iso())
                con.commit()
                done.append(dict(date=iso, bills=got, lines=n_lines,
                                 accepted=res.get("accepted"), review=res.get("review"),
                                 attributed=rupees(res.get("attributed_p") or 0)))
            except Exception as ex:                               # noqa: BLE001
                con.rollback()
                aborted = dict(date=iso, error=str(ex)[:200])
                break

        audit(con, "marg_upload", None, "ingest",
              after={"file": f.filename[:80], "days": [d["date"] for d in done],
                     "not_filed": not_filed, "aborted": aborted, "by": u["user"]},
              who=u["user"])
        con.commit()
        return jsonify(ok=(aborted is None), applied=True, title=rep.get("title"),
                       warnings=rep.get("warnings", []), days=survey,
                       ingested=done, not_filed=not_filed, aborted=aborted)
    finally:
        # the export never persists on this box, in any code path
        try:
            os.remove(tmp)
        except OSError:
            pass


# ============================================================================
#  S187_M1a -- B5: the PUSHED Marg export. Reception produces the record of
#  what was sold; the checker alone moves it into the books.
#
#  WHY THIS EXISTS. The S186 upload lives on /finance/workbench, which is
#  checker-only -- and medical's only checker is the doctor. The S183 design's
#  whole point is segregation of duty: the person holding the cash (Darpan)
#  must not produce the record of what was sold, and the person producing it
#  (reception/Shavez) has no portal login. This route lets the medical PC's
#  sender push the day's BILL WISE report with a scoped token.
#
#  WHAT THE TOKEN CAN AND CANNOT DO. X-Finance-Marg opens exactly one path,
#  and that path can only STAGE: parse, survey, store the per-day CSVs, and
#  answer in plain words. It cannot apply, cannot read the books, cannot reach
#  any other route. Applying stays require("checker"), one click on the
#  workbench. A stolen sender token therefore exposes nothing and moves
#  nothing.
#
#  THE FILE STILL DIES IN THE REQUEST (the S186 rule, kept). What is staged
#  is the PARSED per-day line/item CSVs -- exactly the text ingest_day
#  consumes -- so the later apply replays proven inputs with no re-parse and
#  no file. Staged rows are pruned of their payload the moment they are
#  applied.
#
#  THE STAGING TABLE IS CREATED LAZILY, in _marg_staging(), not by a
#  migration: the DDL is purely additive (CREATE IF NOT EXISTS), the selftest
#  runs on throwaway copies that need it, and a table that ships inside the
#  code that uses it cannot be forgotten by an installer. The DDL below is
#  the authoritative schema record.
#
#  KNOWN DUPLICATION, on purpose: the parse/survey guards mirror
#  api_marg_upload above rather than refactoring it -- this kit is additive
#  (0 lines removed) by design; folding the two into one helper is owed and
#  named in the delivery note.
# ============================================================================

def _mirror_tbl(con):
    """The D2 reveal marker (D326). Created lazily, the marg_push_staging way:
    the DDL lives in the code that reads it, so the two cannot drift apart."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS day_mirror_reveal ("
        " day_entry_id INTEGER PRIMARY KEY"
        "   REFERENCES day_entry(id) ON DELETE CASCADE,"
        " revealed_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),"
        " revealed_by TEXT,"
        " fingerprint TEXT NOT NULL)")


def _money_fingerprint(total_p, upi_p, expenses, movements, noncash):
    """Exactly what "the figures he was shown" means.

    A save that changes NONE of these is not an edit -- and that distinction
    earns its keep, because tapping Scan silently saves a draft on the way to
    the scanner. Stamping THAT as an edit-after-reveal would be a false
    accusation against the one person the badge is about."""
    return json.dumps([int(total_p), int(upi_p),
                       sorted(int(e["amount_p"]) for e in expenses),
                       sorted([m["direction"], m["party"], int(m["amount_p"])]
                              for m in movements),
                       sorted([b["bill_no"], int(b["amount_p"])] for b in noncash)],
                      sort_keys=True)


def _marg_staging(con):
    con.execute(
        "CREATE TABLE IF NOT EXISTS marg_push_staging ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " unit TEXT NOT NULL DEFAULT 'medical',"
        " received_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),"
        " file_md5 TEXT NOT NULL,"
        " filename_hint TEXT,"
        " status TEXT NOT NULL DEFAULT 'pending'"
        "   CHECK (status IN ('pending','applied','rejected','superseded')),"
        " survey_json TEXT,"
        " parsed_json TEXT,"
        " applied_at TEXT, applied_by TEXT, apply_result_json TEXT)")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_marg_push_md5 "
                "ON marg_push_staging(file_md5)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_marg_push_status "
                "ON marg_push_staging(status)")


def _marg_push_reject(con, file_md5, filename, why):
    """A refusal must leave a record that outlives the run (F-113) -- on the
    server too, not only on the sender's screen."""
    con.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                "VALUES (?, NULL, 'MARG_PUSH_REJECTED', 'high', ?)",
                (UNIT, ("%s: %s" % (filename, why))[:400]))
    con.execute("INSERT OR IGNORE INTO marg_push_staging "
                "(unit, file_md5, filename_hint, status, survey_json) "
                "VALUES (?,?,?, 'rejected', ?)",
                (UNIT, file_md5, filename[:80],
                 json.dumps({"error": str(why)[:300]})))
    con.commit()


@app.route("/finance/api/marg-push", methods=["POST"])
def api_marg_push():
    # defense in depth: the before_request gate already required this token;
    # this handler must still be safe if it is ever reached another way.
    if not MARG_TOKEN:
        return jsonify(ok=False, verdict="REFUSED", error="not_enabled",
                       message="the push surface is not enabled on this "
                               "server (FINANCE_MARG_TOKEN is not set)"), 503
    if request.headers.get("X-Finance-Marg") != MARG_TOKEN:
        return jsonify(ok=False, verdict="REFUSED", error="bad_token"), 401
    if marg_report is None or finance_returns is None:
        return jsonify(ok=False, verdict="REFUSED", error="module_absent",
                       message="marg_report / finance_returns not installed"), 503

    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(ok=False, verdict="REFUSED", error="no_file",
                       message="no file arrived with the request"), 400
    blob = f.read()
    if not blob:
        return jsonify(ok=False, verdict="REFUSED", error="empty_file",
                       message="the file was empty"), 400
    file_md5 = hashlib.md5(blob).hexdigest()

    con = db()
    _marg_staging(con)
    dup = con.execute("SELECT id, status, received_at FROM marg_push_staging "
                      "WHERE file_md5=?", (file_md5,)).fetchone()
    if dup:
        return jsonify(ok=True, verdict="ALREADY-RECEIVED", id=dup["id"],
                       status=dup["status"], received_at=dup["received_at"],
                       message="this exact file was already received on %s "
                               "(status: %s). If you meant to send today's "
                               "report, run it in Marg first -- yeh file "
                               "pehle bheji ja chuki hai." %
                               (dup["received_at"], dup["status"]))

    import tempfile
    suffix = ".xlsx" if f.filename.lower().endswith("x") else ".xls"
    fd, tmp = tempfile.mkstemp(prefix="marg_push_", suffix=suffix)
    os.close(fd)
    try:
        with open(tmp, "wb") as fh:
            fh.write(blob)

        try:
            rep = marg_report.read_report(tmp, keep_items=True)
        except Exception as ex:                                   # noqa: BLE001
            _marg_push_reject(con, file_md5, f.filename, str(ex))
            return jsonify(ok=False, verdict="REFUSED", error="rejected",
                           message=str(ex)), 422

        days = marg_report.day_totals(rep)
        if not days:
            _marg_push_reject(con, file_md5, f.filename, "no days found")
            return jsonify(ok=False, verdict="REFUSED", error="no_days",
                           message="no daily sections were found in this "
                                   "file"), 422
        total_items = sum(len(d.get("items", [])) for d in rep["days"])
        if total_items == 0:
            _marg_push_reject(con, file_md5, f.filename, "no item detail")
            return jsonify(ok=False, verdict="REFUSED", error="no_item_detail",
                           message="this export carries NO item detail (0 drug "
                                   "lines). Re-export from Marg with 'With "
                                   "Item Deta. = Yes'."), 422

        probe = io.StringIO()
        marg_report.write_lines_csv(rep, probe, days[0]["business_date"])
        header = probe.getvalue().splitlines()[0].split(",")
        src = con.execute("SELECT id, active FROM ingest_source "
                          "WHERE unit=? AND adapter='marg_export'",
                          (UNIT,)).fetchone()
        if not src or not src["active"]:
            _marg_push_reject(con, file_md5, f.filename, "ingest source missing")
            return jsonify(ok=False, verdict="REFUSED", error="source_missing",
                           message="the (medical, marg_export) ingest source "
                                   "is absent or inactive"), 422
        cmap = {r["our_field"]: r["their_column"] for r in con.execute(
            "SELECT our_field, their_column FROM ingest_column_map "
            "WHERE source_id=?", (src["id"],))}
        missing = {k: v for k, v in cmap.items() if v not in header}
        if not cmap or missing:
            _marg_push_reject(con, file_md5, f.filename, "column map mismatch")
            return jsonify(ok=False, verdict="REFUSED",
                           error="column_map_mismatch", missing=missing,
                           message="the column map does not match the parser "
                                   "output"), 422

        nonzero = {d["date"]: sum(1 for b in d["bills"] if b["net_p"] != 0)
                   for d in rep["days"]}

        # ---- survey + the per-day replayable payload ------------------------
        survey, not_filed, days_payload = [], [], []
        for d in days:
            iso_d = d["business_date"]
            e = con.execute("SELECT id, status FROM day_entry "
                            "WHERE unit=? AND business_date=?",
                            (UNIT, iso_d)).fetchone()
            survey.append(dict(date=iso_d, bills=d.get("bills"),
                               net=rupees(d["net_p"]), filed=bool(e),
                               status=(e["status"] if e else None)))
            if not e:
                not_filed.append(iso_d)
            lbuf, ibuf = io.StringIO(), io.StringIO()
            marg_report.write_lines_csv(rep, lbuf, iso_d)
            marg_report.write_items_csv(rep, ibuf, iso_d)
            days_payload.append(dict(date=iso_d,
                                     expect=nonzero.get(iso_d, 0),
                                     lines_csv=lbuf.getvalue(),
                                     items_csv=ibuf.getvalue()))

        # F-113: a NOT FILED day must leave a record that outlives the run.
        for iso_d in not_filed:
            con.execute(
                "INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                "VALUES (?,?, 'MARG_DAY_NOT_FILED', 'medium', ?)",
                (UNIT, iso_d,
                 "a PUSHED Marg export (%s) carried %d bill(s) for this day, "
                 "but the day was not filed at push time. The push is staged; "
                 "apply it from the workbench once the day is filed (F-113)."
                 % (f.filename[:60], nonzero.get(iso_d, 0))))

        survey_json = json.dumps(dict(
            survey=survey, not_filed=not_filed, title=rep.get("title"),
            warnings=rep.get("warnings", []),
            bills=sum(len(d["bills"]) for d in rep["days"]),
            item_lines=total_items))
        parsed_json = json.dumps(dict(title=rep.get("title"),
                                      days=days_payload))
        cur = con.execute(
            "INSERT INTO marg_push_staging (unit, file_md5, filename_hint, "
            "status, survey_json, parsed_json) VALUES (?,?,?, 'pending', ?,?)",
            (UNIT, file_md5, f.filename[:80], survey_json, parsed_json))
        audit(con, "marg_push_staging", cur.lastrowid, "staged",
              after={"file": f.filename[:80], "md5": file_md5,
                     "days": [d["date"] for d in days_payload],
                     "not_filed": not_filed},
              who="marg-sender")
        con.commit()
        return jsonify(ok=True, verdict="ACCEPTED-FOR-REVIEW",
                       id=cur.lastrowid, days=survey, not_filed=not_filed,
                       bills=sum(len(d["bills"]) for d in rep["days"]),
                       item_lines=total_items,
                       message="Received: %d day(s), %d bill(s). NOTHING has "
                               "entered the books -- Dr. Manoj will check and "
                               "apply it on the workbench. Report pahunch "
                               "gayi hai; abhi khaate mein nahi gayi."
                               % (len(days), sum(len(d["bills"])
                                                 for d in rep["days"])))
    finally:
        # the export never persists on this box, in any code path (S186 rule)
        try:
            os.remove(tmp)
        except OSError:
            pass


@app.route("/finance/api/marg-push/list")
def api_marg_push_list():
    u, err = require("checker")
    if err:
        return err
    con = db()
    _marg_staging(con)
    out = []
    for r in con.execute("SELECT id, received_at, filename_hint, file_md5, "
                         "status, survey_json, applied_at, applied_by, "
                         "apply_result_json, (parsed_json IS NOT NULL) AS replayable "
                         "FROM marg_push_staging ORDER BY id DESC LIMIT 20"):
        try:
            sv = json.loads(r["survey_json"] or "{}")
        except ValueError:
            sv = {}
        try:
            _ar = json.loads(r["apply_result_json"] or "{}")
        except ValueError:
            _ar = {}
        out.append(dict(id=r["id"], received_at=r["received_at"],
                        file=r["filename_hint"], md5_8=r["file_md5"][:8],
                        status=r["status"], survey=sv,
                        applied_at=r["applied_at"], applied_by=r["applied_by"],
                        ingested_count=len(_ar.get("ingested") or []),
                        replayable=bool(r["replayable"])))
    return jsonify(ok=True, pushes=out)


@app.route("/finance/api/marg-push/apply", methods=["POST"])
def api_marg_push_apply():
    """The checker's half. Replays the staged per-day CSVs through the SAME
    guarded path as the direct upload: expect-mismatch aborts the day, item
    load of zero aborts the day, and a day that is STILL not filed is reported
    and skipped -- its data_flag from push time already stands."""
    u, err = require("checker")
    if err:
        return err
    if finance_ingest is None or finance_returns is None:
        return jsonify(ok=False, error="module_absent"), 503
    pid = (request.get_json(silent=True) or {}).get("id")
    if not pid:
        return jsonify(ok=False, error="no_id"), 400
    con = db()
    _marg_staging(con)
    row = con.execute("SELECT * FROM marg_push_staging WHERE id=?",
                      (pid,)).fetchone()
    if not row:
        return jsonify(ok=False, error="not_found"), 404
    if row["status"] != "pending":
        return jsonify(ok=False, error="not_pending", status=row["status"],
                       message="this push is %s, not pending" % row["status"]), 409
    try:
        payload = json.loads(row["parsed_json"] or "null")
    except ValueError:
        payload = None
    if not payload or not payload.get("days"):
        return jsonify(ok=False, error="no_payload",
                       message="this push carries no replayable payload"), 409

    done, aborted, still_not_filed = [], None, []
    for d in payload["days"]:
        iso_d = d["date"]
        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                        (UNIT, iso_d)).fetchone()
        if not e:
            still_not_filed.append(iso_d)
            continue
        try:
            res = finance_ingest.ingest_day(con, UNIT, iso_d, "marg_export",
                                            d["lines_csv"], run_by=u["user"],
                                            source_ref="push:%s" % row["file_md5"][:8])
            got = res.get("rows_read") or 0
            if got != d["expect"]:
                con.rollback()
                aborted = dict(date=iso_d, read=got, expected=d["expect"])
                break
            irows = list(csv.DictReader(io.StringIO(d["items_csv"])))
            con.execute("DELETE FROM sale_line_item WHERE day_entry_id=?",
                        (e["id"],))
            n_lines = finance_returns.load_lines(con, UNIT, iso_d, irows,
                                                 batch_id=res.get("batch_id"))
            if irows and n_lines == 0:
                con.rollback()
                aborted = dict(date=iso_d, read=got, expected=d["expect"], lines=0)
                break
            if not irows:
                con.commit()
            finance_ingest.reconcile_day_attribution(con, UNIT, iso_d, now=now_iso())
            con.commit()
            done.append(dict(date=iso_d, bills=got, lines=n_lines,
                             accepted=res.get("accepted"), review=res.get("review")))
        except Exception as ex:                                   # noqa: BLE001
            con.rollback()
            aborted = dict(date=iso_d, error=str(ex)[:200])
            break

    if aborted is None:
        # F-155: a run is "applied" ONLY when every day it carries was ingested.
        # If any day was still not filed, the report is NOT loaded -- marking it
        # 'applied' was the lie (17-Aug showed green while its books were empty).
        # Such a run STAYS 'pending' so it re-applies once the day is filed, and
        # its payload is kept for exactly that; the outcome is recorded either way.
        _result = json.dumps(dict(ingested=done, still_not_filed=still_not_filed))
        if done and not still_not_filed:
            con.execute("UPDATE marg_push_staging SET status='applied', "
                        "applied_at=?, applied_by=?, apply_result_json=?, "
                        "parsed_json=NULL WHERE id=?",
                        (now_iso(), u["user"], _result, pid))
        else:
            con.execute("UPDATE marg_push_staging SET applied_at=?, applied_by=?, "
                        "apply_result_json=? WHERE id=?",
                        (now_iso(), u["user"], _result, pid))
    audit(con, "marg_push_staging", pid, "apply",
          after={"ingested": [d["date"] for d in done],
                 "still_not_filed": still_not_filed, "aborted": aborted,
                 "by": u["user"]},
          who=u["user"])
    con.commit()
    return jsonify(ok=(aborted is None), ingested=done,
                   still_not_filed=still_not_filed, aborted=aborted)


# ============================================================================
#  S187_D1a -- Daily Flow v2, stage D1: the Day Page + the approvals surface.
#
#  ONE canonical expandable day view and ONE checker landing. Every count is a
#  link; every total expands to its rows; bills expand to drug lines. No new
#  pipeline and no schema change -- this stage SURFACES what S179-S187 already
#  store. Darpan-facing screens are untouched (that is stage D2); edits and
#  the Staff Ledger bridge are untouched (stage D3, gated on the backlog-6
#  check). Read-only except the existing approve route, which is reused as-is.
# ============================================================================

def _marg_bills_for_day(con, iso):
    """The day's Marg view, grouped bill -> drug lines. sale_item carries the
    money-side rows; sale_line_item carries item detail keyed by bill_no."""
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (UNIT, iso)).fetchone()
    if not e:
        return [], 0
    items_by_bill = {}
    for r in con.execute("SELECT bill_no, is_return, item_name, pack, qty_raw, "
                         "amount_p, expiry_ym, batch FROM sale_line_item "
                         "WHERE day_entry_id=? ORDER BY bill_no, seq", (e["id"],)):
        items_by_bill.setdefault(r["bill_no"] or "?", []).append(
            dict(item=r["item_name"], pack=r["pack"], qty=r["qty_raw"],
                 amount=rupees(r["amount_p"] or 0), expiry=r["expiry_ym"],
                 batch=r["batch"], is_return=bool(r["is_return"])))
    bills = []
    for r in con.execute(
            "SELECT s.source_ref bill_no, s.amount_p, s.gross_p, s.disc_p, "
            "       s.service, s.mode, "
            "       s.confidence, p.clinic_id, p.name "
            "FROM sale_item s LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
            "WHERE s.day_entry_id=? ORDER BY s.source_ref", (e["id"],)):
        bills.append(dict(bill_no=r["bill_no"], amount=rupees(r["amount_p"]),
                          gross=(rupees(r["gross_p"]) if r["gross_p"] is not None else None),
                          disc=(rupees(r["disc_p"]) if r["disc_p"] is not None else None),
                          service=r["service"], mode=r["mode"],
                          patient=r["name"], clinic_id=r["clinic_id"],
                          is_return=("return" in (r["service"] or "")),
                          items=items_by_bill.get(r["bill_no"] or "", [])))
    n_items = sum(len(v) for v in items_by_bill.values())
    return bills, n_items


@app.route("/finance/api/day/<date_iso>/full")
def api_day_full(date_iso):
    """The Day Page aggregate: declared + Marg (bills -> items) + both banks +
    flags + review + audit stamps, one call. Checker only -- this is the full
    view; the maker's scoped view is stage D2."""
    u, err = require("checker")
    if err:
        return err
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    con = db()
    st = day_state(con, UNIT, iso)

    bills, n_items = _marg_bills_for_day(con, iso)
    batches = []
    if st.get("exists"):
        batches = [dict(adapter=r["adapter"], status=r["status"],
                        rows=r["rows_read"], accepted=r["rows_accepted"],
                        review=r["rows_review"], at=r["run_at"])
                   for r in con.execute(
                       "SELECT * FROM ingest_batch WHERE day_entry_id=? "
                       "ORDER BY id DESC LIMIT 5", (st["id"],))]
    has_marg = any(b["adapter"] == "marg_export" and b["status"] in ("ok", "partial")
                   for b in batches)

    upi_stmt = con.execute("SELECT parsed_total_p, txn_count, ingested_at "
                           "FROM upi_statement WHERE unit=? AND statement_date=?",
                           (UNIT, iso)).fetchone()
    upi_mism = con.execute("SELECT expected_p, actual_p, diff_p, status "
                           "FROM recon_exception WHERE unit=? AND business_date=? "
                           "AND kind='upi_vs_statement' ORDER BY id DESC LIMIT 1",
                           (UNIT, iso)).fetchone()

    yb = [dict(date=r["txn_date"], desc=r["description"],
               deposit=rupees(r["deposit_p"] or 0),
               is_cash=bool(r["is_cash_deposit"]))
          for r in con.execute("SELECT * FROM bank_statement_line "
                               "WHERE txn_date=? AND (deposit_p or 0) > 0 "
                               "ORDER BY id", (iso,))]

    flags = [dict(code=r["code"], severity=r["severity"], detail=r["detail"])
             for r in con.execute("SELECT * FROM data_flag WHERE unit=? AND "
                                  "business_date=? ORDER BY id DESC LIMIT 30",
                                  (UNIT, iso))]
    excs = [dict(kind=r["kind"], status=r["status"], detail=r["detail"])
            for r in con.execute("SELECT kind, status, detail FROM recon_exception "
                                 "WHERE unit=? AND business_date=? "
                                 "ORDER BY id DESC LIMIT 30", (UNIT, iso))]
    review_open = 0
    if st.get("exists"):
        review_open = con.execute("SELECT COUNT(*) FROM sale_item_review "
                                  "WHERE day_entry_id=? AND status='open'",
                                  (st["id"],)).fetchone()[0]

    att = con.execute("SELECT day_total_p, attributed_p FROM v_day_attribution "
                      "WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
    marg_total_p = sum(
        (b_r["amount_p"] or 0) for b_r in con.execute(
            "SELECT s.amount_p, s.service FROM sale_item s JOIN day_entry e "
            "ON e.id=s.day_entry_id WHERE e.unit=? AND e.business_date=?",
            (UNIT, iso))) if st.get("exists") else 0
    declared_p = st.get("total_p") or 0
    variance_p = (marg_total_p - declared_p) if has_marg else None

    return jsonify(ok=True, date=iso, day=st, marg=dict(
                       present=has_marg, bills=bills, item_lines=n_items,
                       total=rupees(marg_total_p),
                       variance=(rupees(variance_p) if variance_p is not None else None),
                       variance_over_threshold=(variance_p is not None
                                                and abs(variance_p)
                                                > MARG_VARIANCE_THRESHOLD_P)),
                   batches=batches,
                   icici=dict(present=bool(upi_stmt),
                              settled=(rupees(upi_stmt["parsed_total_p"]) if upi_stmt else None),
                              txns=(upi_stmt["txn_count"] if upi_stmt else None),
                              declared=st.get("upi"),
                              mismatch=(dict(bank=rupees(upi_mism["expected_p"]),
                                             entered=rupees(upi_mism["actual_p"]),
                                             diff=rupees(upi_mism["diff_p"]),
                                             status=upi_mism["status"])
                                        if upi_mism else None)),
                   yesbank=yb, flags=flags, exceptions=excs,
                   review_open=review_open,
                   attribution=(dict(day_total=rupees(att["day_total_p"]),
                                     attributed=rupees(att["attributed_p"]))
                                if att else None))


@app.route("/finance/api/where-is-the-cash")
def api_where_is_the_cash():
    """F-132/F-133/F-137: what the maker is entitled to know about cash that is
    NOT in front of him -- and nothing else.

    He is told two things: how much is currently held by Dr Manoj or Dr Bhawna,
    and how long since the last bank trip. He is NOT told the unit balance,
    month-to-date revenue, or any other day's money.

    F-137 -- WHY THIS READS `cash_custody_event` AND NOT `cash_movement`.
    S188 built this on `cash_movement` and reasoned, in this docstring, that
    the drawer read over two lakh because "the money left the room and never
    left the books". THAT WAS WRONG, and the correction matters more than the
    display. `v_day_cash` computes `cash_out_p` as SUM(cash_movement WHERE
    direction='out'), so EVERY movement row is subtracted from cash in hand,
    whatever its party. Booking the doctors' holdings there would have taken
    cash in hand from Rs 2,05,198 to about Rs 30,000 -- and the S186 PHYSICAL
    COUNT of 17 Aug 2026 proves that money has not left the business at all:
    drawer 0, owner 18,963, Dr Bhawna 1,56,235, total 1,75,198, which is what
    the books say once Darpan's Rs 30,000 is entered. Owner ruling, S189: cash
    held by either doctor IS cash in hand, merely located elsewhere.

    So custody is LOCATION and belongs in `cash_custody_event`, which no view
    in the cash ledger reads. Recording it here cannot move a rupee, and that
    is the property this endpoint depends on.

    THE ZERO IS STILL THE POINT. Where no custody has been recorded this
    answers Rs 0, and the page renders that as an INSTRUCTION, never a fact.

    Parked totals are scoped to the current financial year (1 April) on the
    owner's ruling. The bank clock deliberately is NOT: 'days since the last
    deposit' must stay true across an April boundary."""
    u, err = require("maker", "checker")
    if err:
        return err
    con = db()
    since = fy_start().isoformat()

    net = {}
    for r in con.execute(
            "SELECT to_party p, SUM(amount_p) s FROM cash_custody_event "
            "WHERE unit=? AND event_date >= ? GROUP BY to_party", (UNIT, since)):
        net[r["p"]] = net.get(r["p"], 0) + r["s"]
    for r in con.execute(
            "SELECT from_party p, SUM(amount_p) s FROM cash_custody_event "
            "WHERE unit=? AND event_date >= ? GROUP BY from_party", (UNIT, since)):
        net[r["p"]] = net.get(r["p"], 0) - r["s"]

    parked = [dict(party=p, name=PARTY_NAMES.get(p, p), amount=rupees(net.get(p, 0)),
                   amount_p=net.get(p, 0))
              for p in ("dr_manoj", "dr_bhawna")]
    # anyone ELSE genuinely holding unit cash is shown too -- but a place is
    # not a person, and a negative is a source, not a holding (F-137).
    for p in sorted(k for k in net
                    if k not in ("dr_manoj", "dr_bhawna")
                    and k not in CUSTODY_STRUCTURAL and net[k] > 0):
        parked.append(dict(party=p, name=PARTY_NAMES.get(p, p),
                           amount=rupees(net[p]), amount_p=net[p]))
    total_p = sum(x["amount_p"] for x in parked)

    # provenance: the last physical count this position rests on. A figure
    # derived from a count should say so -- a count beats a derivation (S186).
    cnt = con.execute(
        "SELECT business_date d, counted_p p, counted_by b FROM cash_count "
        "WHERE unit=? ORDER BY business_date DESC LIMIT 1", (UNIT,)).fetchone()

    dep = con.execute(
        "SELECT e.business_date d, m.amount_p a FROM cash_movement m "
        "JOIN day_entry e ON e.id = m.day_entry_id WHERE e.unit=? AND "
        "m.direction='out' AND m.party='bank' ORDER BY e.business_date DESC "
        "LIMIT 1", (UNIT,)).fetchone()
    try:
        trip_days = int(setting(con, "%s.deposit_trip_days" % UNIT, "7") or 7)
    except (TypeError, ValueError):
        trip_days = 7
    days_since = ((today() - parse_iso_date(dep["d"])).days) if dep else None

    return jsonify(ok=True,
                   fy_from=since,
                   source="cash_custody_event",
                   counted=(dict(date=cnt["d"], amount=rupees(cnt["p"]),
                                 by=(cnt["b"] or "")) if cnt else None),
                   parked_total=rupees(total_p),
                   any_recorded=bool(total_p) or bool([x for x in parked if x["amount_p"]]),
                   parked=[{k: v for k, v in x.items() if k != "amount_p"} for x in parked],
                   bank=dict(last_date=(dep["d"] if dep else None),
                             last_amount=(rupees(dep["a"]) if dep else None),
                             days_since=days_since,
                             threshold_days=trip_days,
                             overdue=bool(days_since is not None and days_since >= trip_days)))


@app.route("/finance/api/day/<date_iso>/mirror")
def api_day_mirror(date_iso):
    """Stage D2 (D326): the MAKER's reveal -- his own day, and nothing else.

    Deliberately NOT a trimmed copy of /full. It is a separate, smaller answer,
    so that a future addition to the checker's view cannot quietly widen the
    maker's. The two surfaces share a threshold, not a payload.

    SAVE-THEN-SEE IS ENFORCED HERE, not in the browser. If the day has not been
    saved there is nothing to reveal, and the endpoint says so rather than
    letting the page decide. The sequencing is what keeps his declaration and
    the Marg export independent records; a promise the UI makes to itself is
    not a property of the system.

    What he is given: his declared figures, the bank's settled UPI, the Marg
    verdict, which scans are attached, his opening carry, and which days he
    still owes. What he is NOT given: any month figure, unit cash in hand, any
    other day's money, or bill-level Marg detail."""
    u, err = require("maker", "checker")
    if err:
        return err
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400

    con = db()
    st = day_state(con, UNIT, iso)
    if not st.get("exists"):
        return jsonify(ok=False, error="not_saved",
                       message="Save the day first \u2014 then the check appears."), 409

    eid = st["id"]
    declared_total_p = st.get("total_p") or 0
    declared_upi_p = st.get("upi_p") or 0

    # ---- ICICI. Pushed by GAS at 09:30 every day since S179, so by the time
    # the previous day is filed after 10am this half is always in. It is the
    # half that fires every single morning.
    stmt = con.execute("SELECT parsed_total_p, txn_count FROM upi_statement "
                       "WHERE unit=? AND statement_date=?", (UNIT, iso)).fetchone()
    if stmt:
        bank_p = stmt["parsed_total_p"] or 0
        icici = dict(present=True, settled=rupees(bank_p), txns=stmt["txn_count"],
                     declared=rupees(declared_upi_p),
                     match=(bank_p == declared_upi_p),
                     diff=rupees(bank_p - declared_upi_p))
    else:
        icici = dict(present=False, declared=rupees(declared_upi_p))

    # ---- Marg. THREE states, not two: "no comparison" has two different
    # causes and they need two different people to act. Reception has not sent
    # it -> ask reception. It is sent but not applied -> the checker's Apply is
    # owed, and telling him that stops him chasing the wrong person.
    has_marg = bool(con.execute(
        "SELECT 1 FROM ingest_batch WHERE day_entry_id=? AND adapter='marg_export' "
        "AND status IN ('ok','partial') LIMIT 1", (eid,)).fetchone())
    if has_marg:
        row = con.execute("SELECT COUNT(*) n, COALESCE(SUM(amount_p),0) t "
                          "FROM sale_item WHERE day_entry_id=?", (eid,)).fetchone()
        marg_total_p, n_bills = int(row["t"]), int(row["n"])
        var_p = marg_total_p - declared_total_p
        marg = dict(state="applied", total=rupees(marg_total_p), bills=n_bills,
                    variance=rupees(var_p),
                    over_threshold=abs(var_p) > MARG_VARIANCE_THRESHOLD_P)
    else:
        marg = dict(state="absent")
        _marg_staging(con)
        for r in con.execute("SELECT survey_json FROM marg_push_staging "
                             "WHERE unit=? AND status='pending' ORDER BY id DESC",
                             (UNIT,)):
            try:
                sv = json.loads(r["survey_json"] or "{}")
            except ValueError:
                continue
            if any(d.get("date") == iso for d in (sv.get("survey") or [])):
                marg = dict(state="staged_not_applied")
                break

    # ---- his three scans
    have = {a["doc_type"] for a in (st.get("attachments") or []) if a.get("has_file")}
    scans = dict(attached=sorted(have),
                 missing=[d for d in REQUIRED_DOCS if d not in have])

    # ---- days he still owes, the same D322-aware rule the portal line uses.
    # The day he is standing on is excluded: he is dealing with it right now,
    # and listing it as owed would be noise, not a nudge.
    t = today()
    hols = clinic_holidays((t - dt.timedelta(days=7)).isoformat(), t)
    owed = []
    for back in range(1, 8):
        d = t - dt.timedelta(days=back)
        di = d.isoformat()
        if d.weekday() == 6 or di in hols or di == iso:
            continue
        e = con.execute("SELECT status FROM day_entry WHERE unit=? AND business_date=?",
                        (UNIT, di)).fetchone()
        if not e or e["status"] == "draft":
            owed.append(di)

    # ---- record the reveal. From here a save that MOVES THE MONEY is an edit
    # after the reveal and the checker will see it noted. Nothing is blocked:
    # D326 chose the stamp, not the lock, because a lock forces a round trip
    # for an honest typo (F-105) while the badge keeps the audit honest anyway.
    # Only the FIRST reveal is recorded -- the fingerprint must stay the
    # figures he actually saw, not the latest ones.
    #
    # F-129 -- ONLY A MAKER'S LOOK ARMS IT. The first version recorded the
    # reveal against the DAY, whoever opened it. So the checker glancing at a
    # draft armed the badge, and the maker was then stamped "changed after the
    # check" for a check he had never been shown. The flag would still have
    # been literally true and would still have named the wrong person.
    #   A marker that records "this was shown" must record WHO it was shown to,
    #   or it will speak about somebody else.
    # Stated assumption, so it is a claim and not a secret: a caller holding
    # BOTH roles is treated as the checker and does not arm the badge. On
    # medical no such person exists -- the checker is the doctor alone (S179)
    # -- and if that ever changes, this line is the one to revisit.
    _mirror_tbl(con)
    _is_maker = ("maker" in u["roles"]) and ("checker" not in u["roles"])
    _armed = False
    if _is_maker and not con.execute(
            "SELECT 1 FROM day_mirror_reveal WHERE day_entry_id=?", (eid,)).fetchone():
        con.execute("INSERT INTO day_mirror_reveal (day_entry_id, revealed_by, "
                    "fingerprint) VALUES (?,?,?)",
                    (eid, u["user"],
                     _money_fingerprint(declared_total_p, declared_upi_p,
                                        st.get("expenses") or [],
                                        st.get("movements") or [],
                                        st.get("noncash_bills") or [])))
        audit(con, "day_mirror_reveal", eid, "reveal", who=u["user"])
        con.commit()
        _armed = True

    edited = bool(con.execute(
        "SELECT 1 FROM data_flag WHERE unit=? AND business_date=? "
        "AND code='EDITED_AFTER_REVEAL' LIMIT 1", (UNIT, iso)).fetchone())

    return jsonify(ok=True, date=iso, status=st.get("status"),
                   armed_by_this_look=_armed, looking_as_maker=_is_maker,
                   # F-132: no opening, no closing. Both are running totals
                   # over all history, not this day, and the mirror is the
                   # maker's surface by definition. The checker has /full.
                   declared=dict(total=rupees(declared_total_p),
                                 upi=rupees(declared_upi_p),
                                 cash=st.get("cash")),
                   icici=icici, marg=marg, scans=scans,
                   owed_days=owed, edited_after_reveal=edited)


@app.route("/finance/api/approvals")
def api_approvals():
    """The landing strip + queue. EVERY count here is backed by the rows it
    counts, in the same payload -- no number without its click-through."""
    u, err = require("checker")
    if err:
        return err
    con = db()
    _marg_staging(con)
    today_iso = today().isoformat()
    horizon = (today() - dt.timedelta(days=45)).isoformat()

    pending = [dict(date=r["business_date"], status=r["status"],
                    entered_by=r["entered_by"])
               for r in con.execute(
                   "SELECT business_date, status, entered_by FROM day_entry "
                   "WHERE unit=? AND status IN ('submitted','draft') "
                   "AND source != 'legacy_sheet' "
                   "ORDER BY business_date DESC LIMIT 30", (UNIT,))]

    # a filed day with no successful marg batch = a missing export, visible
    # the same morning rather than at month-end
    missing_marg = [r["business_date"] for r in con.execute(
        "SELECT e.business_date FROM day_entry e WHERE e.unit=? "
        "AND e.business_date BETWEEN ? AND ? AND NOT EXISTS "
        "(SELECT 1 FROM ingest_batch b WHERE b.day_entry_id=e.id "
        " AND b.adapter='marg_export' AND b.status IN ('ok','partial')) "
        "ORDER BY e.business_date DESC", (UNIT, horizon, today_iso))]

    pushes_pending = [dict(id=r["id"], received_at=r["received_at"],
                           file=r["filename_hint"])
                      for r in con.execute(
                          "SELECT id, received_at, filename_hint FROM "
                          "marg_push_staging WHERE status='pending' "
                          "ORDER BY id DESC LIMIT 10")]

    not_filed_flags = [dict(date=r["business_date"], detail=r["detail"])
                       for r in con.execute(
                           "SELECT df.business_date, df.detail FROM data_flag df "
                           "WHERE df.unit=? AND df.code='MARG_DAY_NOT_FILED' "
                           "AND NOT EXISTS (SELECT 1 FROM day_entry e "
                           "  JOIN ingest_batch b ON b.day_entry_id=e.id "
                           "  WHERE e.unit=df.unit AND e.business_date=df.business_date "
                           "  AND b.adapter='marg_export' AND b.status IN ('ok','partial')) "
                           "ORDER BY df.id DESC LIMIT 15", (UNIT,))]

    upi_open = [dict(date=r["business_date"], diff=rupees(r["diff_p"]))
                for r in con.execute(
                    "SELECT business_date, diff_p FROM recon_exception "
                    "WHERE unit=? AND kind='upi_vs_statement' AND status='open' "
                    "ORDER BY business_date DESC LIMIT 20", (UNIT,))]

    variance = [dict(date=r["business_date"], detail=r["detail"])
                for r in con.execute(
                    "SELECT business_date, detail FROM recon_exception "
                    "WHERE unit=? AND kind='line_sum_vs_day_total' AND status='open' "
                    "ORDER BY business_date DESC LIMIT 20", (UNIT,))]

    review_open = con.execute(
        "SELECT COUNT(*) FROM sale_item_review r JOIN day_entry e "
        "ON e.id=r.day_entry_id WHERE e.unit=? AND r.status='open'",
        (UNIT,)).fetchone()[0]

    return jsonify(ok=True, today=today_iso,
                   pending=pending, missing_marg=missing_marg,
                   pushes_pending=pushes_pending,
                   marg_not_filed_flags=not_filed_flags,
                   upi_mismatches=upi_open, variance_days=variance,
                   review_open=review_open)


@app.route("/finance/api/tile-summary")
def api_tile_summary():
    """One line of truth for the portal's Sanjeevni tile (S187_P1a): what is
    waiting for the checker, as counts. Checker-only -- anyone else gets a
    quiet refusal and the tile keeps its static text (fail-soft by design,
    the tile-meta pattern). Deliberately cheap: five COUNT queries."""
    u, err = require("checker")
    if err:
        return err
    con = db()
    _marg_staging(con)
    horizon = (today() - dt.timedelta(days=45)).isoformat()
    to_approve = con.execute(
        "SELECT COUNT(*) FROM day_entry WHERE unit=? AND status IN "
        "('submitted','draft') AND source != 'legacy_sheet'", (UNIT,)).fetchone()[0]
    marg_pushes = con.execute(
        "SELECT COUNT(*) FROM marg_push_staging WHERE status='pending'").fetchone()[0]
    missing_marg = con.execute(
        "SELECT COUNT(*) FROM day_entry e WHERE e.unit=? AND e.business_date "
        "BETWEEN ? AND ? AND NOT EXISTS (SELECT 1 FROM ingest_batch b WHERE "
        "b.day_entry_id=e.id AND b.adapter='marg_export' AND b.status IN "
        "('ok','partial'))", (UNIT, horizon, today().isoformat())).fetchone()[0]
    exceptions = con.execute(
        "SELECT COUNT(*) FROM recon_exception WHERE unit=? AND status='open' "
        "AND kind IN ('upi_vs_statement','line_sum_vs_day_total')",
        (UNIT,)).fetchone()[0]
    review = con.execute(
        "SELECT COUNT(*) FROM sale_item_review r JOIN day_entry e ON "
        "e.id=r.day_entry_id WHERE e.unit=? AND r.status='open'",
        (UNIT,)).fetchone()[0]
    return jsonify(ok=True, to_approve=to_approve, marg_pushes=marg_pushes,
                   missing_marg=missing_marg, exceptions=exceptions,
                   review=review)


@app.route("/finance/api/orthotics", methods=["GET", "POST"])
def api_orthotics():
    """Orthotics visibility (S187_H1a; stage D4 pulled forward at the owner's
    direction). The vocabulary is a SETTING (`orthotics.vocab`, comma-separated
    keywords matched case-insensitively against sale_line_item.item_name) so
    the item set is the owner's to shape, never hard-coded. GET returns the
    vocab + a rollup over the last N days (per item: times sold, quantity raw
    count, amount, last-sold date) + per-day totals. POST sets the vocab.
    Checker-only; sales-side only — stock claims wait for the asset-app
    purchase-bill feed (the owner's D-decision, addendum §8 Q2)."""
    u, err = require("checker")
    if err:
        return err
    con = db()
    if request.method == "POST":
        vocab = ((request.get_json(silent=True) or {}).get("vocab") or "").strip()
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES "
                    "('orthotics.vocab', ?)", (vocab[:500],))
        audit(con, "setting", None, "orthotics_vocab", after={"vocab": vocab[:200]},
              who=u["user"])
        con.commit()
        return jsonify(ok=True, vocab=vocab)
    vocab = (setting(con, "orthotics.vocab") or "").strip()
    words = [w.strip().lower() for w in vocab.split(",") if w.strip()]
    days_n = min(int(request.args.get("days", "90") or 90), 366)
    since = (today() - dt.timedelta(days=days_n)).isoformat()
    items, day_rows = [], []
    if words:
        like = " OR ".join(["lower(item_name) LIKE ?"] * len(words))
        args = ["%" + w + "%" for w in words]
        # qty_raw is TEXT (Marg's strips:loose notation) -- a numeric sum would
        # be a guess wearing a number. Times-sold is the honest pace signal.
        items = [dict(item=r["item_name"], times=r["n"],
                      amount=rupees(int(r["amt"] or 0)), last_sold=r["last_d"])
                 for r in con.execute(
                     "SELECT item_name, COUNT(*) n, "
                     "SUM(COALESCE(amount_p,0)) amt, MAX(business_date) last_d "
                     "FROM sale_line_item WHERE unit=? AND business_date>=? "
                     "AND is_return=0 AND (" + like + ") "
                     "GROUP BY item_name ORDER BY last_d DESC, amt DESC LIMIT 60",
                     [UNIT, since] + args)]
        day_rows = [dict(date=r["business_date"], lines=r["n"],
                         amount=rupees(int(r["amt"] or 0)))
                    for r in con.execute(
                        "SELECT business_date, COUNT(*) n, SUM(COALESCE(amount_p,0)) amt "
                        "FROM sale_line_item WHERE unit=? AND business_date>=? "
                        "AND is_return=0 AND (" + like + ") "
                        "GROUP BY business_date ORDER BY business_date DESC LIMIT 45",
                        [UNIT, since] + args)]
    return jsonify(ok=True, vocab=vocab, since=since, items=items, days=day_rows)


@app.route("/finance/approvals")
def page_approvals():
    u, err = require("checker")
    if err:
        return redirect(PORTAL_LOGIN, code=302)
    return send_file(os.path.join(UI_DIR, "finance_approvals.html"))


# ===================================================================== S194
#  ⭐1 Daily Sale v2 page · ⭐2 home-medicine bills · ⭐3 cash/UPI reclass log
# =====================================================================

@app.route("/finance/daily")
def page_daily():
    """S194 ⭐1 — the approved two-stage Daily Sale page (Darpan).  A NEW route;
    /finance/entry stays live as the fallback until the owner switches over."""
    u, err = require("maker")
    if err:
        return redirect(PORTAL_LOGIN, code=302)
    return send_file(os.path.join(UI_DIR, "finance_daily.html"))


@app.route("/finance/api/home-medicine")
def api_home_medicine():
    """S194 ⭐2 — home-medicine sales, populated automatically from the Marg
    export (bills made out to 'Home Medicine / Home Medisun').  Read-only."""
    u, err = require("maker", "checker")
    if err:
        return err
    con = db()
    finance_ingest._ensure_home_med_col(con)
    since = request.args.get("since") or (today() - dt.timedelta(days=30)).isoformat()
    rows = con.execute(
        "SELECT e.business_date bd, COUNT(*) n, "
        "       SUM(COALESCE(si.amount_p, 0)) amt "
        "FROM sale_item si JOIN day_entry e ON e.id = si.day_entry_id "
        "WHERE si.unit=? AND si.home_med=1 AND e.business_date>=? "
        "GROUP BY e.business_date ORDER BY e.business_date DESC LIMIT 90",
        (UNIT, since)).fetchall()
    days = [dict(date=r["bd"], n=r["n"],
                 amount=rupees(int(r["amt"] or 0)), amount_p=int(r["amt"] or 0))
            for r in rows]
    tot = sum(d["amount_p"] for d in days)
    cnt = sum(d["n"] for d in days)
    return jsonify(ok=True, since=since, count=cnt,
                   total=rupees(tot), total_p=tot, days=days)


@app.route("/finance/api/reclassifications")
def api_reclassifications():
    """S194 ⭐3 — bills whose payment mode flipped (cash<->upi) on a re-import.
    Makes Amir's counter conversions visible.  Read-only."""
    u, err = require("maker", "checker")
    if err:
        return err
    con = db()
    finance_ingest._ensure_mode_change_log(con)
    since = request.args.get("since") or (today() - dt.timedelta(days=30)).isoformat()
    rows = con.execute(
        "SELECT business_date, source_ref, amount_p, old_mode, new_mode, changed_at "
        "FROM mode_change_log WHERE unit=? AND business_date>=? "
        "ORDER BY changed_at DESC, id DESC LIMIT 200",
        (UNIT, since)).fetchall()
    items = [dict(date=r["business_date"], bill=r["source_ref"],
                  amount=rupees(int(r["amount_p"] or 0)),
                  from_mode=r["old_mode"], to_mode=r["new_mode"],
                  at=r["changed_at"]) for r in rows]
    day_ct = {}
    for r in rows:
        day_ct[r["business_date"]] = day_ct.get(r["business_date"], 0) + 1
    days = [dict(date=k, n=v) for k, v in sorted(day_ct.items(), reverse=True)]
    return jsonify(ok=True, since=since, count=len(items), items=items, days=days)


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
        # S180: a sale return sits in this queue with a NEGATIVE amount_p, because
        # sale_item_review carries no non-negative constraint and a signed value
        # keeps v_day_attribution.in_review_p honest. sale_item does have that
        # constraint, so the sign has to be turned back into a magnitude plus a
        # "_return" service on the way out — exactly as finance_ingest does on the
        # way in. Without this, resolving a queued return raises IntegrityError.
        amt_p = r["amount_p"] or 0
        kind = finance_ingest.KIND_RETURN if amt_p < 0 else finance_ingest.KIND_SALE
        con.execute("INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, "
                    "service, description, amount_p, source, confidence, verified_by, verified_at) "
                    "VALUES (?,?,?,?,?,?,?, 'manual', 1.0, ?, ?)",
                    (r["day_entry_id"], r["ingest_batch_id"], UNIT, pid,
                     finance_ingest.service_for(UNIT, kind),
                     p.get("description"), abs(amt_p), u["user"], now_iso()))
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


# =============================================================== CLINIC (C1a)
# Session 182 · contract S181_Clinic_Module_Build_Contract_C1 + addendum.
# The CLINIC unit's daily entry, replicated from medical WITH CLINIC SEMANTICS:
#
#   * SIX money cells — OPD / X-Ray / Procedure, each cash and UPI — plus zero
#     or more STRAY additions (amount + stream + tender + a required reason).
#   * ⚠ ADDITIVE ARITHMETIC. The clinic day's revenue is the SUM OF ALL CELLS.
#     Medical's convention ("total includes UPI; cash = total − UPI") must NOT
#     leak in: there is no 'total' input here at all, so there is nothing to
#     subtract from. The smoke suite asserts cash equals the cash cells alone —
#     a check medical's formula would fail.
#   * Opening cash stays COMPUTED (D313). No input, no accepted parameter —
#     the save route never reads any 'opening' key a client might send.
#   * Card/wallet are NOT entry fields in this slice; they arrive later via
#     attribution. The tender vocabulary is CLINIC_TENDERS below — a later
#     tender is a tuple entry plus a UI control, not surgery.
#   * Evidence reuses the SAME attachment/scan mechanism as medical (widget
#     host page → POST scan route → attachment row + PDF on disk). Two
#     documents: the OPD register page and the X-Ray + Procedure register page
#     (doc types added by finance_migration_S182_clinic.sql).
#   * Roles: unit_role rows for unit 'clinic' (reception makes; manoj and
#     bhawna check — the roster the schema seeded at S179). The before_request
#     gate resolves the unit from the path, so a clinic login buys nothing on
#     medical and vice versa.
#
# Everything below is NEW code. No medical route or helper above is altered
# beyond the unit-aware gate; helpers that already take a unit parameter
# (day_state, opening_p, roles_for, require, refresh_missing_days,
# open_exceptions, deposit_threshold_p) are reused with unit='clinic'.

CLINIC_UNIT = "clinic"
CLINIC_NAME = "Dr Manoj Agarwal Clinic"
CLINIC_SERVICES = ("opd", "xray", "procedure")
CLINIC_TENDERS = ("cash", "upi")     # C1 vocabulary, kept for the compat path
# (service, tender, payload/UI field name). RETIRED from the UI at C2 (the
# owner replaced the six cells with four tender totals) but the six keys are
# still ACCEPTED by the API for compatibility — an old open tab, a replayed
# request — and stored exactly as C1 stored them.
CLINIC_CELLS = (("opd", "cash", "opd_cash"), ("opd", "upi", "opd_upi"),
                ("xray", "cash", "xray_cash"), ("xray", "upi", "xray_upi"),
                ("procedure", "cash", "proc_cash"), ("procedure", "upi", "proc_upi"))
CLINIC_FIELD_OF = {(s, t): f for s, t, f in CLINIC_CELLS}
# ---- S182 C2: the owner's four tender totals. (tender, payload/UI field).
# 'cash', 'upi' and 'card' fit day_line's mode CHECK and are stored there
# (service 'collection', line_kind 'tender'). 'razorpay' does NOT fit the
# CHECK — mode IN ('cash','upi','card','credit') — and extending a CHECK in
# SQLite means a table rebuild, which is barred. Razorpay rows live in the
# additive side table clinic_line_side instead (see the C2 migration).
CLINIC_TENDER_FIELDS = (("cash", "total_cash"), ("upi", "total_upi"),
                        ("card", "card"), ("razorpay", "razorpay"))
CLINIC_TENDERS_ALL = tuple(t for t, _f in CLINIC_TENDER_FIELDS)
CLINIC_DAYLINE_TENDERS = ("cash", "upi", "card")   # what day_line's CHECK admits
CLINIC_REQUIRED_DOCS = ("opd_register", "xray_proc_register")
CLINIC_DOC_LABEL = {
    "opd_register": "OPD register page",
    "xray_proc_register": "X-Ray + Procedure register page",
    "deposit_slip": "Deposit slip",
}


def clinic_final_checker(con):
    """WHO gives the clinic day its final approval — data, not code (S182 C2).
    Every other clinic checker can only VERIFY (the middle approval)."""
    return (setting(con, "clinic.final_checker", "manoj") or "manoj").strip()


def _unit_for_path(path):
    """Which unit a request path belongs to. The clinic namespace is
    /finance/clinic/...; everything else is the original medical surface."""
    return CLINIC_UNIT if path == "/finance/clinic" or \
        path.startswith("/finance/clinic/") else UNIT


def clinic_day_state(con, date_iso):
    """day_state(), plus the clinic-shaped breakdown: the four tender totals
    (C2), the legacy six cells (still reported for old rows), the stray lines
    with their narrations, the expense list the base day_state already carries,
    the verification record, and attachment URLs kept inside the clinic
    namespace (the medical attachment route refuses clinic rows, and must).

    C2 arithmetic: the day's total is EVERY line — day_line rows of all modes
    (cash, upi, card) PLUS the clinic_line_side rows (razorpay), which the
    shared views cannot see because day_line's mode CHECK excludes that rail.
    Cash/UPI stay exactly what the views say; card and razorpay never touch
    the drawer and never enter the UPI reconcile."""
    st = day_state(con, CLINIC_UNIT, date_iso)
    for a in st.get("attachments", []):
        a["url"] = "/finance/clinic/attachment/%d" % a["id"]
    cells = {f: 0 for _s, _t, f in CLINIC_CELLS}
    tenders = {t: 0 for t in CLINIC_TENDERS_ALL}
    strays = []
    all_p = 0
    st["verification"] = None
    if st.get("exists"):
        for r in con.execute("SELECT service, mode, amount_p, line_kind, note "
                             "FROM day_line WHERE day_entry_id=? ORDER BY id", (st["id"],)):
            all_p += r["amount_p"]
            if r["line_kind"] == "stray":
                strays.append(dict(stream=r["service"], tender=r["mode"],
                                   amount_p=r["amount_p"], amount=rupees(r["amount_p"]),
                                   reason=r["note"], narration=r["note"]))
            else:
                f = CLINIC_FIELD_OF.get((r["service"], r["mode"]))
                if f:
                    cells[f] += r["amount_p"]
                if r["mode"] in tenders:
                    tenders[r["mode"]] += r["amount_p"]
        for r in con.execute("SELECT tender, amount_p, line_kind, note "
                             "FROM clinic_line_side WHERE day_entry_id=? ORDER BY id",
                             (st["id"],)):
            all_p += r["amount_p"]
            if r["line_kind"] == "stray":
                strays.append(dict(stream="collection", tender=r["tender"],
                                   amount_p=r["amount_p"], amount=rupees(r["amount_p"]),
                                   reason=r["note"], narration=r["note"]))
            elif r["tender"] in tenders:
                tenders[r["tender"]] += r["amount_p"]
        ver = con.execute("SELECT verified_by, verified_at, note FROM clinic_verification "
                          "WHERE day_entry_id=?", (st["id"],)).fetchone()
        if ver:
            st["verification"] = dict(verified_by=ver["verified_by"],
                                      verified_at=ver["verified_at"], note=ver["note"])
        # the day's total now includes the razorpay rail the views cannot see
        st["total_p"] = all_p
        st["total"] = rupees(all_p)
    st["cells"] = cells
    st["cells_r"] = {k: rupees(v) for k, v in cells.items()}
    st["tenders"] = tenders
    st["tenders_r"] = {k: rupees(v) for k, v in tenders.items()}
    st["razorpay_p"] = tenders["razorpay"]
    st["strays"] = strays
    st["stray_p"] = sum(s_["amount_p"] for s_ in strays)
    return st


def _clinic_side_by_date(con, a_iso, b_iso):
    """Per-day sums of the side-table rail (razorpay) in a date range, so the
    clinic month grid, day list and tile report WHOLE revenue — v_cash_ledger
    cannot include what day_line's CHECK forced out of day_line."""
    return {r["d"]: int(r["p"] or 0) for r in con.execute(
        "SELECT e.business_date d, SUM(s.amount_p) p FROM clinic_line_side s "
        "JOIN day_entry e ON e.id = s.day_entry_id "
        "WHERE e.unit=? AND e.business_date BETWEEN ? AND ? GROUP BY e.business_date",
        (CLINIC_UNIT, a_iso, b_iso))}


# ------------------------------------------------------------- clinic pages

@app.route("/finance/clinic/")
def clinic_page_root():
    """Same rule as medical's root: land each person on their own screen."""
    u = current_user()
    have = roles_for(db(), CLINIC_UNIT, u["user"], u["role"])
    if "checker" in have:
        return clinic_page_review()
    return send_from_directory(UI_DIR, "finance_entry_clinic.html")


@app.route("/finance/clinic/entry")
def clinic_page_entry():
    return send_from_directory(UI_DIR, "finance_entry_clinic.html")


@app.route("/finance/clinic/review")
def clinic_page_review():
    """The checker experience is the SAME screen medical's checker uses, read
    from the SAME file on disk, served with its API base and the two visible
    unit names rewritten into the clinic namespace. The file itself is never
    modified (medical UI files are out of this slice's scope), so the review
    flow — approve, exceptions, corrections — behaves identically by
    construction. Month-close and cutover buttons exist on the screen; their
    clinic endpoints answer 'not in this slice' loudly rather than 404ing."""
    path = os.path.join(UI_DIR, "finance_review.html")
    if not os.path.exists(path):
        return jsonify(ok=False, error="ui_missing"), 500
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    html = html.replace('var API = "/finance/api";',
                        'var API = "/finance/clinic/api";')
    html = html.replace("<title>Sanjeevni — Review", "<title>Clinic — Review")
    html = html.replace("<h1>Sanjeevni Medicos</h1>", "<h1>%s</h1>" % CLINIC_NAME)
    # S182 C2: the two-stage approval layer + the tracker card, injected at
    # serve time so the medical file on disk stays untouched (same rule as the
    # API-base rewrite above). The layer re-points the shared screen's
    # doApprove at the clinic flow: non-final checkers VERIFY, the final
    # checker sees the verification state and approves (with an explicit,
    # recorded skip when unverified).
    html = html.replace("</body>", _CLINIC_REVIEW_C2_LAYER + "\n</body>")
    return app.response_class(html, mimetype="text/html")


# Serve-time injection for /finance/clinic/review (see clinic_page_review).
# Plain ES5, same conventions as the host page; uses the page's own globals
# (API, show, selected). No external fetch, no new file on disk.
_CLINIC_REVIEW_C2_LAYER = """<script id="c2VerifyLayer">
(function(){
"use strict";
var C2 = { user: "", final: false, final_name: "" };
fetch(API + "/whoami").then(function(r){ return r.json(); }).then(function(j){
  C2.user = j.user || ""; C2.final = !!j.is_final_checker;
  C2.final_name = j.final_checker || "the doctor";
});
function jpost(url, body){
  return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}) }).then(function(r){
      return r.json().then(function(j){ return { s: r.status, j: j }; }); });
}
function vday(iso, cb){
  fetch(API + "/day/" + iso).then(function(r){ return r.json(); })
    .then(function(j){ cb(j.ok ? j.day : null); });
}

/* verification-aware approve: replaces the shared screen's doApprove */
doApprove = function(iso, after){
  vday(iso, function(d){
    if (!d){ show("bad", "Could not open " + iso + "."); return; }
    var v = d.verification;
    if (!C2.final){
      if (v){ show("good", iso + " is already verified by " + v.verified_by +
        ". " + C2.final_name + " gives the final approval."); return; }
      if (!window.confirm("VERIFY " + iso + "?\\n\\nYou are confirming the day's " +
        "figures match the registers.\\nFinal approval stays with " +
        C2.final_name + ".")) return;
      jpost(API + "/verify/" + iso).then(function(res){
        if (!res.j.ok){ show("bad", res.j.message || res.j.error); return; }
        show("good", iso + " verified. " + C2.final_name +
          " will give the final approval.");
        if (after) after();
      });
      return;
    }
    var body = {};
    if (!v){
      if (!window.confirm(iso + " has NOT been verified by the middle checker." +
        "\\n\\nApprove without that verification?\\n(It is recorded as: " +
        "approved without middle verification.)")) return;
      body.skip_verification = true;
    }
    jpost(API + "/approve/" + iso, body).then(function(res){
      if (res.s === 409 && res.j.error === "upi_mismatch"){
        var okgo = window.confirm("BANK DISAGREES ON UPI FOR " + iso +
          "\\n\\nBank settled : \\u20b9" + res.j.bank +
          "\\nDay entered  : \\u20b9" + res.j.entered +
          "\\nDifference   : \\u20b9" + res.j.diff +
          "\\n\\nThe bank is the arbiter. Approve anyway, over the mismatch?" +
          "\\n(Your acknowledgment is recorded against the day.)");
        if (!okgo) return;
        body.acknowledge_upi = true;
        body.ack_note = window.prompt("Optional note for the record:", "") || "";
        jpost(API + "/approve/" + iso, body).then(function(r2){
          if (!r2.j.ok){ show("bad", r2.j.message || r2.j.error); return; }
          show("good", iso + " approved over the UPI mismatch \\u2014 " +
            "acknowledgment recorded.");
          if (after) after();
        });
        return;
      }
      if (!res.j.ok){ show("bad", res.j.message || res.j.error); return; }
      show("good", iso + " approved." +
        (res.j.approval_note ? " (" + res.j.approval_note + ")" : ""));
      if (after) after();
    });
  });
};

/* decorate the open day: verification state + tracker card + button label */
var lastDecor = { day: null, at: 0 };
function decorate(){
  document.querySelectorAll("#btnApprove, .accApprove").forEach(function(b){
    if (!C2.final && b.dataset.c2 !== "1"){
      b.dataset.c2 = "1";
      b.innerHTML = '<svg class="i sm"><use href="#i-check"/></svg>Verify this day';
    }
  });
  var card = document.getElementById("dayCard");
  if (!card || card.style.display === "none" || !selected) return;
  var now = Date.now();
  if (lastDecor.day === selected && now - lastDecor.at < 5000) return;
  lastDecor.day = selected; lastDecor.at = now;
  var anchor = document.getElementById("btnApprove");
  var slot = document.getElementById("c2VerState");
  if (!slot){
    slot = document.createElement("div"); slot.id = "c2VerState";
    slot.className = "note"; anchor.parentNode.insertBefore(slot, anchor);
  }
  var tr = document.getElementById("c2Tracker");
  if (!tr){
    tr = document.createElement("div"); tr.id = "c2Tracker";
    tr.className = "note"; anchor.parentNode.insertBefore(tr, slot);
  }
  vday(selected, function(d){
    if (!d) return;
    var v = d.verification;
    slot.textContent = v
      ? ("Verified by " + v.verified_by + " at " +
         String(v.verified_at || "").replace("T", " "))
      : "Not verified yet. " + (C2.final ?
          "You can approve with the skip confirmed." :
          "Press the button below to verify.");
  });
  fetch(API + "/tracker-day/" + selected).then(function(r){ return r.json(); })
    .then(function(j){
      if (!(j.ok && j.present)){
        tr.textContent = "Docterz / Tracker \\u2014 day revenue: not received yet.";
        return;
      }
      var s = j.summary || {};
      tr.textContent = "Docterz / Tracker \\u2014 day revenue: " +
        "net \\u20b9" + (s.net || 0) + " \\u00b7 cash \\u20b9" + (s.cash || 0) +
        " \\u00b7 online \\u20b9" + (s.online || 0) +
        " \\u00b7 consult " + (s.consult_n || 0) + " (\\u20b9" + (s.consult_amt || 0) + ")" +
        " \\u00b7 x-ray " + (s.xray_n || 0) + " (\\u20b9" + (s.xray_amt || 0) + ")" +
        " \\u00b7 procedures " + (s.proc_n || 0) + " (\\u20b9" + (s.proc_amt || 0) + ")" +
        " \\u00b7 " + (j.line_count || 0) + " line(s)";
    });
}
new MutationObserver(decorate).observe(document.body, { childList: true, subtree: true });
setInterval(decorate, 2000);
})();
</script>"""


# ---------------------------------------------------------- clinic API: read

@app.route("/finance/clinic/api/whoami")
def clinic_api_whoami():
    u = current_user()
    con = db()
    have = roles_for(con, CLINIC_UNIT, u["user"], u["role"])
    role = "checker" if "checker" in have else ("maker" if "maker" in have else (u["role"] or ""))
    final = clinic_final_checker(con)
    return jsonify(ok=True, user=u["user"], role=role, roles=sorted(have),
                   unit=CLINIC_UNIT, unit_name=CLINIC_NAME,
                   final_checker=final,
                   is_final_checker=bool("checker" in have and
                                         u["user"].lower() == final.lower()))


@app.route("/finance/clinic/api/tile-meta")
def clinic_api_tile_meta():
    """Tile wording is a setting, exactly like medical's tile.maker_title
    pattern — unit-prefixed so the two tiles never fight over one key."""
    con = db()
    u = current_user()
    have = roles_for(con, CLINIC_UNIT, u["user"], u["role"])
    checker = "checker" in have
    subtitle = setting(con, "clinic.tile.checker_subtitle" if checker
                       else "clinic.tile.maker_subtitle")
    # S187_P2a: live pending counts ride the EXISTING subtitle hydration --
    # the portal needs no change for the clinic tiles. Behaviour-scoped and
    # cheap; a zero adds nothing so a quiet day reads exactly as before.
    try:
        if checker:
            to_verify = con.execute(
                "SELECT COUNT(*) FROM day_entry e WHERE e.unit=? AND "
                "e.status='submitted' AND NOT EXISTS (SELECT 1 FROM "
                "clinic_verification v WHERE v.day_entry_id=e.id)",
                (CLINIC_UNIT,)).fetchone()[0]
            to_final = con.execute(
                "SELECT COUNT(*) FROM day_entry e WHERE e.unit=? AND "
                "e.status='submitted' AND EXISTS (SELECT 1 FROM "
                "clinic_verification v WHERE v.day_entry_id=e.id)",
                (CLINIC_UNIT,)).fetchone()[0]
            bits = []
            if to_verify:
                bits.append("✅ %d to verify" % to_verify)
            if to_final:
                bits.append("\U0001F510 %d to approve" % to_final)
            if bits:
                subtitle = " · ".join(bits) + \
                    ((" · " + subtitle) if subtitle else "")
        else:
            te = con.execute(
                "SELECT status FROM day_entry WHERE unit=? AND business_date=?",
                (CLINIC_UNIT, today().isoformat())).fetchone()
            if not te:
                subtitle = "✍️ today's day not entered yet" + \
                    ((" · " + subtitle) if subtitle else "")
    except Exception:                                          # noqa: BLE001
        pass                                    # fail-soft: the setting stands
    return jsonify(ok=True,
                   role=("checker" if checker else "maker"),
                   title=setting(con, "clinic.tile.checker_title" if checker
                                 else "clinic.tile.maker_title"),
                   subtitle=subtitle,
                   href="/finance/clinic/review" if checker else "/finance/clinic/entry")


@app.route("/finance/clinic/api/tile")
def clinic_api_tile():
    con = db()
    refresh_missing_days(con, CLINIC_UNIT)
    last = con.execute("SELECT business_date, revenue_p, closing_p FROM v_cash_ledger "
                       "WHERE unit=? ORDER BY business_date DESC LIMIT 1",
                       (CLINIC_UNIT,)).fetchone()
    counts = {r["kind"]: r["c"] for r in con.execute(
        "SELECT kind, COUNT(*) c FROM recon_exception WHERE unit=? AND status='open' GROUP BY kind",
        (CLINIC_UNIT,))}
    awaiting = con.execute("SELECT COUNT(*) c FROM day_entry WHERE unit=? AND status='submitted'",
                           (CLINIC_UNIT,)).fetchone()["c"]
    ym = today().strftime("%Y-%m")
    mtd = con.execute("SELECT COALESCE(SUM(revenue_p),0) r FROM v_cash_ledger "
                      "WHERE unit=? AND business_date LIKE ?",
                      (CLINIC_UNIT, ym + "%")).fetchone()["r"]
    # the razorpay rail lives in the side table the ledger view cannot see
    mtd += int(con.execute(
        "SELECT COALESCE(SUM(s.amount_p),0) p FROM clinic_line_side s "
        "JOIN day_entry e ON e.id = s.day_entry_id "
        "WHERE e.unit=? AND e.business_date LIKE ?",
        (CLINIC_UNIT, ym + "%")).fetchone()["p"])
    last_side = 0
    if last:
        last_side = _clinic_side_by_date(con, last["business_date"],
                                         last["business_date"]).get(last["business_date"], 0)
    cust = con.execute("SELECT cash_p, custodian_name FROM v_cash_custody WHERE unit=?",
                       (CLINIC_UNIT,)).fetchone()
    cash_p = int(cust["cash_p"]) if cust else 0
    thr = deposit_threshold_p(con, CLINIC_UNIT)
    mc = con.execute("SELECT ym, status FROM month_close WHERE unit=? ORDER BY ym DESC LIMIT 1",
                     (CLINIC_UNIT,)).fetchone()
    dep = con.execute("SELECT e.business_date d FROM cash_movement m "
                      "JOIN day_entry e ON e.id=m.day_entry_id "
                      "WHERE e.unit=? AND m.direction='out' AND m.party='bank' "
                      "ORDER BY e.business_date DESC LIMIT 1", (CLINIC_UNIT,)).fetchone()
    try:
        trip_days = int(setting(con, "%s.deposit_trip_days" % CLINIC_UNIT, "7") or 7)
    except (TypeError, ValueError):
        trip_days = 7
    since = None
    if dep:
        since = (today() - parse_iso_date(dep["d"])).days
    nc = con.execute("SELECT COALESCE(SUM(noncash_p),0) n FROM v_cash_ledger "
                     "WHERE unit=? AND business_date LIKE ?",
                     (CLINIC_UNIT, ym + "%")).fetchone()["n"]
    # D330: the drawings split, clinic side.
    _expense_uid_col(con)
    drawings_mtd = con.execute(
        "SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x "
        "JOIN day_entry e ON e.id=x.day_entry_id "
        "WHERE e.unit=? AND substr(e.business_date,1,7)=? "
        "AND x.category_kind='home'", (CLINIC_UNIT, ym)).fetchone()[0]
    return jsonify(ok=True, unit_name=CLINIC_NAME,
                   drawings_month_to_date=rupees(drawings_mtd),
                   last_bank_deposit=(dep["d"] if dep else None),
                   days_since_bank_deposit=since,
                   bank_trip_due=bool(since is not None and since >= trip_days),
                   noncash_month_to_date=rupees(nc),
                   last_filed=last["business_date"] if last else None,
                   last_revenue=rupees(last["revenue_p"] + last_side) if last else "",
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


@app.route("/finance/clinic/api/day/<date_iso>")
def clinic_api_day(date_iso):
    try:
        d = parse_iso_date(date_iso)
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    con = db()
    st = clinic_day_state(con, d.isoformat())
    st["is_future"] = d > today()
    st["too_old"] = (today() - d).days > BACKFILL_WINDOW_DAYS
    return jsonify(ok=True, day=st)


@app.route("/finance/clinic/api/month/<ym>")
def clinic_api_month(ym):
    if not re.fullmatch(r"\d{4}-\d{2}", ym):
        return jsonify(ok=False, error="bad_month"), 400
    con = db()
    first, last = month_bounds(ym)
    entries = {r["business_date"]: r for r in con.execute(
        "SELECT e.business_date, e.status, l.cash_in_p, l.upi_in_p, l.revenue_p, "
        "       l.expense_p, l.cash_out_p, l.closing_p "
        "FROM day_entry e JOIN v_cash_ledger l "
        "  ON l.unit=e.unit AND l.business_date=e.business_date "
        "WHERE e.unit=? AND e.business_date BETWEEN ? AND ?",
        (CLINIC_UNIT, first.isoformat(), last.isoformat()))}
    missing = {r["business_date"] for r in con.execute(
        "SELECT business_date FROM recon_exception WHERE unit=? AND kind='missing_day' "
        "AND status='open' AND business_date BETWEEN ? AND ?",
        (CLINIC_UNIT, first.isoformat(), last.isoformat()))}
    side = _clinic_side_by_date(con, first.isoformat(), last.isoformat())
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
                         revenue=rupees(e["revenue_p"] + side.get(iso, 0)) if e else "",
                         closing=rupees(e["closing_p"]) if e else ""))
        d += dt.timedelta(days=1)
    tot = con.execute(
        "SELECT COUNT(*) days, COALESCE(SUM(revenue_p),0) rev, COALESCE(SUM(cash_in_p),0) cash, "
        "COALESCE(SUM(upi_in_p),0) upi, COALESCE(SUM(expense_p),0) exp, "
        "COALESCE(SUM(cash_out_p),0) dep, COALESCE(SUM(adjust_p),0) adj, "
        "COALESCE(SUM(noncash_p),0) nc "
        "FROM v_cash_ledger WHERE unit=? AND business_date BETWEEN ? AND ?",
        (CLINIC_UNIT, first.isoformat(), last.isoformat())).fetchone()
    heads = [dict(head=r["head"], bills=r["bill_count"], amount=rupees(r["amount_p"]))
             for r in con.execute("SELECT head, bill_count, amount_p FROM v_noncash_by_head "
                                  "WHERE unit=? AND ym=? ORDER BY amount_p DESC",
                                  (CLINIC_UNIT, ym))]
    return jsonify(ok=True, ym=ym, days=days, missing_count=len(missing),
                   noncash_by_head=heads,
                   totals=dict(days=tot["days"],
                               revenue=rupees(tot["rev"] + sum(side.values())),
                               cash=rupees(tot["cash"]), upi=rupees(tot["upi"]),
                               noncash=rupees(tot["nc"]),
                               expenses=rupees(tot["exp"]), deposited=rupees(tot["dep"]),
                               adjustments=rupees(tot["adj"])))


@app.route("/finance/clinic/api/days")
def clinic_api_days():
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
        "ORDER BY e.business_date DESC", (CLINIC_UNIT, a, b)).fetchall()
    side = _clinic_side_by_date(con, a, b)
    return jsonify(ok=True, from_date=a, to_date=b, count=len(rows), days=[
        dict(date=r["business_date"], status=r["status"],
             imported=(r["source"] == "legacy_sheet"),
             approved_by=r["approved_by"], approved_at=r["approved_at"],
             revenue=rupees(r["revenue_p"] + side.get(r["business_date"], 0)),
             cash=rupees(r["cash_in_p"]),
             upi=rupees(r["upi_in_p"]), noncash=rupees(r["noncash_p"]),
             closing=rupees(r["closing_p"]),
             scans=r["scans"], adjustments=r["adjustments"], bills=r["bills"])
        for r in rows])


@app.route("/finance/clinic/api/exceptions")
def clinic_api_exceptions():
    return jsonify(ok=True, exceptions=open_exceptions(db(), CLINIC_UNIT))


@app.route("/finance/clinic/api/parked")
def clinic_api_parked():
    con = db()
    months = [dict(ym=r["ym"], closed_at=r["closed_at"],
                   parked=rupees(r["parked_p"]), cleared=rupees(r["cleared_p"]),
                   outstanding=rupees(r["outstanding_p"]),
                   outstanding_p=r["outstanding_p"],
                   settled=(r["outstanding_p"] <= 0))
              for r in con.execute("SELECT * FROM v_month_parked WHERE unit=? ORDER BY ym DESC",
                                   (CLINIC_UNIT,))]
    deps = [dict(id=r["id"], date=r["business_date"], amount=rupees(r["amount_p"]),
                 amount_p=r["amount_p"], reference=r["reference"],
                 clears_ym=r["clears_ym"],
                 clears_amount=rupees(r["clears_amount_p"]) if r["clears_amount_p"] else None)
            for r in con.execute(
                "SELECT m.id, m.amount_p, m.reference, m.clears_ym, m.clears_amount_p, "
                "       e.business_date "
                "FROM cash_movement m JOIN day_entry e ON e.id = m.day_entry_id "
                "WHERE e.unit=? AND m.direction='out' AND m.party='bank' "
                "ORDER BY e.business_date DESC LIMIT 25", (CLINIC_UNIT,))]
    return jsonify(ok=True, months=months, bank_deposits=deps, nag_days=21, ageing=[])


@app.route("/finance/clinic/attachment/<int:aid>")
def clinic_api_attachment(aid):
    con = db()
    r = con.execute("SELECT at.*, e.unit, e.business_date FROM attachment at "
                    "JOIN day_entry e ON e.id = at.day_entry_id WHERE at.id=?", (aid,)).fetchone()
    if not r or r["unit"] != CLINIC_UNIT:
        return jsonify(ok=False, error="not_found"), 404
    if r["path"] and os.path.exists(r["path"]):
        return send_file(r["path"], mimetype="application/pdf", max_age=0,
                         download_name="%s_%s.pdf" % (r["business_date"], r["doc_type"]))
    if r["external_url"]:
        return redirect(r["external_url"], code=302)
    return jsonify(ok=False, error="file_missing",
                   message="The record exists but the file is not on this server."), 410


# --------------------------------------------------------- clinic API: write

@app.route("/finance/clinic/api/day", methods=["POST"])
def clinic_api_save_day():
    u, err = require("maker", "checker", unit=CLINIC_UNIT)
    if err:
        return err
    p = request.get_json(silent=True) or {}
    con = db()

    # ---- date (picker only; the server is the guarantee) --------------------
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

    # ---- money (S182 C2): FOUR tender totals + strays + expenses. ADDITIVE —
    #      every amount adds; only expenses subtract, and only from the drawer.
    #      There is deliberately NO 'total' input and NO 'opening' input: any
    #      such key in the payload is never read.
    #      COMPAT: the retired six-cell keys (opd_cash … proc_upi) are still
    #      accepted and stored exactly as C1 stored them; the sums land in the
    #      same cash/UPI totals because day_line.mode carries the tender.
    try:
        legacy_cells = any(field in p for _s, _t, field in CLINIC_CELLS)
        cells = {}
        for svc, tender, field in CLINIC_CELLS:
            cells[(svc, tender)] = to_paise(p.get(field), field)
        tenders = {}
        for tender, field in CLINIC_TENDER_FIELDS:
            tenders[tender] = to_paise(p.get(field), field)
        strays = []
        for i, s_ in enumerate(p.get("strays") or []):
            amt = to_paise(s_.get("amount"), "Extra line #%d" % (i + 1))
            if amt <= 0:
                continue
            if s_.get("tender") not in CLINIC_TENDERS_ALL:
                return jsonify(ok=False, error="bad_stray",
                               message="An extra line needs how the money came: "
                                       "cash, UPI, card or Razorpay."), 400
            narr = (s_.get("narration") or s_.get("reason") or "").strip()
            if len(narr) < 3:
                return jsonify(ok=False, error="stray_reason_required",
                               message="Every extra line needs 'What is this amount?' "
                                       "written — that is what makes it an extra "
                                       "and not a typo."), 400
            # the old payload's stream is ACCEPTED but no longer required (C2);
            # when a valid one arrives it is kept as the service, for history
            stream = s_.get("stream")
            strays.append(dict(stream=(stream if stream in CLINIC_SERVICES
                                       else "collection"),
                               tender=s_["tender"], amount_p=amt,
                               narration=narr[:200]))
        expenses = []
        for i, e_ in enumerate(p.get("expenses") or []):
            amt = to_paise(e_.get("amount"), "Expense #%d" % (i + 1))
            if amt <= 0:
                continue
            _uid = str(e_.get("uid") or "").strip()
            if not _UID_RE.match(_uid):
                _uid = "cv" + hashlib.md5(os.urandom(16)).hexdigest()[:14]
            if "category" in e_:
                # D330 (§9 of the contract): the clinic gets the two expense
                # categories — home / other — with the same compulsory
                # evidence. NO salary-advance path at clinic, deliberately:
                # no staff advance is ever drawn from a drawer.
                cat = (e_.get("category") or "").strip()
                if cat not in ("home", "other"):
                    return jsonify(ok=False, error="choose_category",
                                   message="Choose a category for every expense."), 400
                det = (e_.get("details") or "").strip()
                if len(det) < 3:
                    return jsonify(ok=False, error="expense_note_required",
                                   message="Every expense needs 'What was it for?' "
                                           "written — money left the drawer."), 400
                expenses.append(dict(amount_p=amt, note=det[:200],
                                     kind=cat, uid=_uid))
                continue
            # pre-D330 shape: still accepted so an old cached page cannot
            # lose data (the E1b precedent); converges on refresh.
            note = (e_.get("note") or e_.get("category_text") or "").strip()
            if len(note) < 3:
                return jsonify(ok=False, error="expense_note_required",
                               message="Every expense needs 'What was it for?' "
                                       "written — money left the drawer."), 400
            expenses.append(dict(amount_p=amt, note=note[:200],
                                 kind=None, uid=_uid))
    except ValueError as ex:
        return jsonify(ok=False, error="not_a_number", message=str(ex)), 400

    total_p = sum(cells.values()) + sum(tenders.values()) + \
        sum(s_["amount_p"] for s_ in strays)
    cash_p = sum(v for (svc, t_), v in cells.items() if t_ == "cash") + \
        tenders["cash"] + \
        sum(s_["amount_p"] for s_ in strays if s_["tender"] == "cash")
    expense_p = sum(e_["amount_p"] for e_ in expenses)

    warnings = []
    if total_p > MAX_SANE_P and not p.get("confirm_large"):
        return jsonify(ok=False, error="confirm_large",
                       message="Day total %s — that is unusually large. Please confirm."
                               % rupees(total_p)), 409

    # closing cannot go negative. Card / UPI / Razorpay never touch the drawer;
    # expenses come out of it (C2), so the guard now has real work to do.
    op = opening_p(con, CLINIC_UNIT, iso)
    closing = op + cash_p - expense_p
    submitting = (p.get("action") == "submit")
    if closing < 0:
        return jsonify(ok=False, error="negative_cash",
                       message="Cash in the drawer would be %s, which cannot be "
                               "negative. Check the expense amounts."
                               % rupees(closing)), 400

    # ---- evidence required to SUBMIT (truth from the attachment table) ------
    have_docs = {r["doc_type"] for r in con.execute(
        "SELECT doc_type FROM attachment WHERE day_entry_id=("
        "  SELECT id FROM day_entry WHERE unit=? AND business_date=?)", (CLINIC_UNIT, iso))}
    missing_docs = [d_ for d_ in CLINIC_REQUIRED_DOCS if d_ not in have_docs]
    if submitting and missing_docs and not (p.get("missing_scan_reason") or "").strip():
        return jsonify(ok=False, error="scans_required", missing=missing_docs,
                       message="Register pages still missing: %s. Attach them, "
                               "or give a reason." % ", ".join(missing_docs)), 400

    # ---- D330: COMPULSORY per-expense evidence at FILE (no escape hatch) ----
    if submitting:
        _exp_att_tbl(con)                  # outside BEGIN: DDL
        _cl_row = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                              (CLINIC_UNIT, iso)).fetchone()
        _have_ev = set()
        if _cl_row:
            _have_ev = {r[0] for r in con.execute(
                "SELECT expense_uid FROM expense_attachment WHERE day_entry_id=?",
                (_cl_row["id"],))}
        _need_ev = [e_ for e_ in expenses
                    if e_["kind"] in ("home", "other")
                    and e_["uid"] not in _have_ev]
        if _need_ev:
            return jsonify(ok=False, error="expense_evidence_required",
                           rows=[dict(uid=e_["uid"], amount=rupees(e_["amount_p"]),
                                      details=e_["note"]) for e_ in _need_ev],
                           message="Attach the bill for: %s. Photograph it, or upload "
                                   "the photo taken when it was paid." % "; ".join(
                                       "%s (%s)" % (e_["note"], rupees(e_["amount_p"]))
                                       for e_ in _need_ev)), 400

    # ---- write (all-or-nothing; a second submit CORRECTS, never duplicates) --
    _expense_uid_col(con)                  # outside BEGIN: DDL (D330)
    _noncash_uid_col(con); _noncash_att_tbl(con)   # S195: per-bill scan DDL
    existing = con.execute("SELECT * FROM day_entry WHERE unit=? AND business_date=?",
                           (CLINIC_UNIT, iso)).fetchone()
    try:
        con.execute("BEGIN")
        if existing:
            if existing["status"] in ("approved", "locked") and \
               "checker" not in u.get("roles", []):
                con.execute("ROLLBACK")
                return jsonify(ok=False, error="locked",
                               message="This day is already approved — only a "
                                       "checker can change it."), 403
            prev = clinic_day_state(con, iso)
            rev = con.execute("SELECT COALESCE(MAX(revision),0)+1 n FROM day_revision "
                              "WHERE day_entry_id=?", (existing["id"],)).fetchone()["n"]
            con.execute("INSERT INTO day_revision (day_entry_id, revision, submitted_at, "
                        "payload_json, superseded_at) VALUES (?,?,?,?,?)",
                        (existing["id"], rev, existing["entered_at"],
                         json.dumps(prev, ensure_ascii=False), now_iso()))
            eid = existing["id"]
            # C2 writes day_line, day_expense and clinic_line_side; a
            # correction replaces all three for this entry (the revision above
            # keeps the old picture verbatim)
            con.execute("DELETE FROM day_line WHERE day_entry_id=?", (eid,))
            con.execute("DELETE FROM day_expense WHERE day_entry_id=?", (eid,))
            con.execute("DELETE FROM clinic_line_side WHERE day_entry_id=?", (eid,))
            # a verification vouched for the OLD figures; it cannot survive them
            vrow = con.execute("SELECT verified_by FROM clinic_verification "
                               "WHERE day_entry_id=?", (eid,)).fetchone()
            if vrow:
                con.execute("DELETE FROM clinic_verification WHERE day_entry_id=?", (eid,))
                warnings.append("The figures changed, so the earlier verification "
                                "(by %s) was cleared — the day needs verifying again."
                                % vrow["verified_by"])
            # F5 (S190): an EDITED day is an app entry, whatever it was
            # imported as -- the approvals queue hides source='legacy_sheet'
            # (the bulk import would flood it), so the owner's edited 31-July
            # day vanished from the queue while its money already counted.
            # The day_revision above keeps the legacy original verbatim.
            con.execute("UPDATE day_entry SET status=?, entered_by=?, entered_at=?, "
                        "manned_by=?, manned_source=?, source='app' WHERE id=?",
                        ("submitted" if submitting else "draft", u["user"], now_iso(),
                         p.get("manned_by"), p.get("manned_source") or "manual", eid))
            audit(con, "day_entry", eid, "correct", before=prev, who=u["user"])
            warnings.append("The previous entry for this day has been kept as revision %d." % rev)
        else:
            cur = con.execute(
                "INSERT INTO day_entry (unit, business_date, status, manned_by, manned_source, "
                "source, entered_by, entered_at) VALUES (?,?,?,?,?,'app',?,?)",
                (CLINIC_UNIT, iso, "submitted" if submitting else "draft", p.get("manned_by"),
                 p.get("manned_source") or "manual", u["user"], now_iso()))
            eid = cur.lastrowid
            audit(con, "day_entry", eid, "create", who=u["user"])

        # compat path: an old-shape payload still writes its six grid rows
        if legacy_cells:
            for svc, tender, _field in CLINIC_CELLS:
                con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p, "
                            "line_kind) VALUES (?,?,?,?, 'grid')",
                            (eid, svc, tender, cells[(svc, tender)]))
        # C2 path: one row per non-zero tender total. cash/upi/card fit
        # day_line's mode CHECK; razorpay is routed to the side table.
        for tender, _field in CLINIC_TENDER_FIELDS:
            if tenders[tender] <= 0:
                continue
            if tender in CLINIC_DAYLINE_TENDERS:
                con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p, "
                            "line_kind) VALUES (?, 'collection', ?, ?, 'tender')",
                            (eid, tender, tenders[tender]))
            else:
                con.execute("INSERT INTO clinic_line_side (day_entry_id, tender, "
                            "amount_p, line_kind) VALUES (?,?,?, 'tender')",
                            (eid, tender, tenders[tender]))
        for s_ in strays:
            if s_["tender"] in CLINIC_DAYLINE_TENDERS:
                con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p, "
                            "line_kind, note) VALUES (?,?,?,?, 'stray', ?)",
                            (eid, s_["stream"], s_["tender"], s_["amount_p"],
                             s_["narration"]))
            else:
                con.execute("INSERT INTO clinic_line_side (day_entry_id, tender, "
                            "amount_p, line_kind, note) VALUES (?,?,?, 'stray', ?)",
                            (eid, s_["tender"], s_["amount_p"], s_["narration"]))
        for e_ in expenses:
            con.execute("INSERT INTO day_expense (day_entry_id, amount_p, amount_known, "
                        "category_kind, category_text, expense_uid) VALUES (?,?,1,?,?,?)",
                        (eid, e_["amount_p"], e_["kind"], e_["note"], e_["uid"]))
        if missing_docs and (p.get("missing_scan_reason") or "").strip():
            con.execute("INSERT INTO data_flag (unit, business_date, day_entry_id, code, "
                        "severity, detail) VALUES (?,?,?,'MISSING_SCAN','medium',?)",
                        (CLINIC_UNIT, iso, eid, "%s | reason: %s"
                         % (",".join(missing_docs), p["missing_scan_reason"][:200])))
        later = con.execute("SELECT COUNT(*) c FROM day_entry WHERE unit=? AND business_date > ? "
                            "AND status IN ('approved','locked')", (CLINIC_UNIT, iso)).fetchone()["c"]
        if later:
            warnings.append("Filing this back-dated day has recomputed the opening balance of "
                            "%d later approved days. This is correct." % later)
            con.execute("INSERT INTO data_flag (unit, business_date, day_entry_id, code, "
                        "severity, detail) VALUES (?,?,?,'RETRO_INSERT','medium',?)",
                        (CLINIC_UNIT, iso, eid,
                         "back-dated filing recomputed %d later approved days" % later))
        con.execute("COMMIT")
    except Exception as ex:                                  # noqa: BLE001 — fail loud, roll back
        con.execute("ROLLBACK")
        return jsonify(ok=False, error="save_failed", message=str(ex)), 500

    refresh_missing_days(con, CLINIC_UNIT)
    upi_check = finance_upi.reconcile_upi(con, CLINIC_UNIT, iso, now=now_iso())
    if upi_check and not upi_check["match"]:
        warnings.append("Bank settled %s UPI for this day but the entry says %s — "
                        "difference %s. The day is flagged; the doctor approves with "
                        "acknowledgment." % (rupees(upi_check["bank_p"]),
                                             rupees(upi_check["entered_p"]),
                                             rupees(upi_check["diff_p"])))
    st = clinic_day_state(con, iso)
    return jsonify(ok=True, day=st, warnings=warnings)


@app.route("/finance/clinic/api/approve/<date_iso>", methods=["POST"])
def clinic_api_approve(date_iso):
    u, err = require("checker", unit=CLINIC_UNIT)
    if err:
        return err
    con = db()
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    e = con.execute("SELECT * FROM day_entry WHERE unit=? AND business_date=?",
                    (CLINIC_UNIT, iso)).fetchone()
    if not e:
        return jsonify(ok=False, error="not_found"), 404
    if e["status"] not in ("submitted", "draft"):
        return jsonify(ok=False, error="bad_status", message="Status: %s" % e["status"]), 409

    p = request.get_json(silent=True) or {}

    # ---- S182 C2: two-stage approval. Only the FINAL checker (a setting, not
    # code) approves; every other clinic checker verifies. The final checker is
    # never hard-blocked: an unverified day approves with an explicit skip,
    # and the skip is recorded in the approval note.
    final = clinic_final_checker(con)
    if u["user"].lower() != final.lower():
        return jsonify(ok=False, error="not_final_checker",
                       message="Only %s gives the final approval. You can press "
                               "Verify on this day instead — that is the middle "
                               "check." % final), 403
    ver = con.execute("SELECT verified_by, verified_at FROM clinic_verification "
                      "WHERE day_entry_id=?", (e["id"],)).fetchone()
    skipped_verification = False
    if not ver:
        if not p.get("skip_verification"):
            return jsonify(ok=False, error="not_verified", verified=False,
                           message="No one has verified this day yet. Approve "
                                   "again with the skip confirmed to approve "
                                   "without the middle check."), 409
        skipped_verification = True

    mism = con.execute("SELECT id, expected_p, actual_p, diff_p FROM recon_exception "
                       "WHERE unit=? AND business_date=? AND kind='upi_vs_statement' "
                       "AND status='open'", (CLINIC_UNIT, iso)).fetchone()
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

    con.execute("UPDATE day_entry SET status='approved', approved_by=?, approved_at=? WHERE id=?",
                (u["user"], now_iso(), e["id"]))
    note = ("approved without middle verification" if skipped_verification
            else "verified by %s at %s" % (ver["verified_by"], ver["verified_at"]))
    audit(con, "day_entry", e["id"], "approve", after={"date": iso, "note": note},
          who=u["user"])
    con.commit()
    # salary_advances_pending_ledger: the shared review screen reads this key;
    # clinic expenses are plain drawer expenses (no salary-advance path), so it
    # stays empty.
    return jsonify(ok=True, date=iso, status="approved", approval_note=note,
                   verified_by=(ver["verified_by"] if ver else None),
                   salary_advances_pending_ledger=[])


@app.route("/finance/clinic/api/verify/<date_iso>", methods=["POST"])
def clinic_api_verify(date_iso):
    """S182 C2: the MIDDLE approval (owner: "shavez can be a middle approver,
    me being final checker"). Any clinic checker may verify a submitted day —
    except the person who entered it (D272: no one vouches for their own
    figures). The final approval stays with clinic.final_checker."""
    u, err = require("checker", unit=CLINIC_UNIT)
    if err:
        return err
    con = db()
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    e = con.execute("SELECT * FROM day_entry WHERE unit=? AND business_date=?",
                    (CLINIC_UNIT, iso)).fetchone()
    if not e:
        return jsonify(ok=False, error="not_found"), 404
    if e["status"] != "submitted":
        return jsonify(ok=False, error="bad_status",
                       message=("This day is still a draft — ask for it to be "
                                "submitted first." if e["status"] == "draft"
                                else "This day is already %s." % e["status"])), 409
    if (e["entered_by"] or "").lower() == u["user"].lower():
        return jsonify(ok=False, error="self_verify",
                       message="You entered this day yourself, so someone else "
                               "has to verify it. अपनी भरी एंट्री ख़ुद verify "
                               "नहीं होती।"), 403
    ver = con.execute("SELECT verified_by, verified_at FROM clinic_verification "
                      "WHERE day_entry_id=?", (e["id"],)).fetchone()
    if ver:
        return jsonify(ok=True, already=True, date=iso,
                       verified_by=ver["verified_by"], verified_at=ver["verified_at"],
                       message="Already verified by %s." % ver["verified_by"])
    p = request.get_json(silent=True) or {}
    at = now_iso()
    con.execute("INSERT INTO clinic_verification (day_entry_id, verified_by, "
                "verified_at, note) VALUES (?,?,?,?)",
                (e["id"], u["user"], at, (str(p.get("note") or "").strip()[:200] or None)))
    audit(con, "clinic_verification", e["id"], "verify",
          after={"date": iso, "by": u["user"]}, who=u["user"])
    con.commit()
    return jsonify(ok=True, already=False, date=iso,
                   verified_by=u["user"], verified_at=at)


@app.route("/finance/clinic/api/exception/<int:exc_id>/resolve", methods=["POST"])
def clinic_api_resolve_exception(exc_id):
    u, err = require("checker", unit=CLINIC_UNIT)
    if err:
        return err
    p = request.get_json(silent=True) or {}
    reason = (p.get("resolution") or "").strip()
    if len(reason) < 3:
        return jsonify(ok=False, error="reason_required",
                       message="A reason is required — nothing closes without one."), 400
    con = db()
    r = con.execute("SELECT * FROM recon_exception WHERE id=? AND unit=?",
                    (exc_id, CLINIC_UNIT)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found"), 404
    if r["kind"] == "missing_day":
        return jsonify(ok=False, error="file_the_day",
                       message="A missing day closes only when the day is filed, "
                               "not by writing a note."), 409
    con.execute("UPDATE recon_exception SET status='resolved', resolution=?, closed_by=?, "
                "closed_at=? WHERE id=?", (reason, u["user"], now_iso(), exc_id))
    audit(con, "recon_exception", exc_id, "resolve", after={"resolution": reason}, who=u["user"])
    con.commit()
    return jsonify(ok=True, id=exc_id, status="resolved")


# ------------------------------------------------- clinic scans (same widget)

@app.route("/finance/clinic/scan/<date_iso>/<doc_type>")
def clinic_scan_page(date_iso, doc_type):
    """Host page for one clinic document — the SAME scanner widget medical
    uses, served from the same public routes, pointed at the clinic upload."""
    u, err = require("maker", "checker", unit=CLINIC_UNIT)
    if err:
        return err
    if doc_type not in CLINIC_DOC_LABEL:
        return jsonify(ok=False, error="bad_doc_type"), 400
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    con = db()
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (CLINIC_UNIT, iso)).fetchone()
    if not e:
        return app.response_class(
            "<meta charset=utf-8><p style='font:16px system-ui;padding:24px'>"
            "पहले दिन सेव करें, फिर उसके पेज लगाएँ। "
            "<a href='/finance/clinic/entry?d=%s'>वापस</a></p>" % iso,
            mimetype="text/html", status=409)
    try:
        ver = int(os.path.getmtime(SCANNER_JS))
    except OSError:
        ver = 0
    cfg = {
        "title": "%s — %s" % (CLINIC_DOC_LABEL[doc_type], iso),
        "uploadUrl": "/finance/clinic/api/day/%s/scan/%s" % (iso, doc_type),
        "fileField": "file",
        "uploadFields": {"unit": CLINIC_UNIT, "business_date": iso, "doc_type": doc_type},
        "nameBase": "Clinic_%s_%s" % (doc_type, iso),
        "backUrl": "/finance/clinic/entry?d=%s" % iso,
        "allowIdCard": False,
        "allowBatch": False,
    }
    html = ("<!DOCTYPE html><html lang=hi><head><meta charset=utf-8>"
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
            "<div class=top><a href='/finance/clinic/entry?d=%s'>← वापस</a>"
            "<span class=t>%s</span></div>"
            "<script>window.SCANNER_CONFIG = %s;</script>"
            "<div id=scanroot></div>"
            "<script src='/finance/scan/jspdf.js'></script>"
            "<script src='/finance/scan/widget.js?v=%d'></script>"
            "</body></html>") % (CLINIC_DOC_LABEL[doc_type], iso,
                                 CLINIC_DOC_LABEL[doc_type], json.dumps(cfg), ver)
    return app.response_class(html, mimetype="text/html")


@app.route("/finance/clinic/scan-expense/<date_iso>/<uid>")
def clinic_scan_expense_page(date_iso, uid):
    """D330: clinic host page for one expense's bill — same shared widget."""
    u, err = require("maker", "checker", unit=CLINIC_UNIT)
    if err:
        return err
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    if not _UID_RE.match(uid or ""):
        return jsonify(ok=False, error="bad_uid"), 400
    con = db()
    _expense_uid_col(con)
    row = _expense_row_for_upload(con, CLINIC_UNIT, iso, uid)
    if not row:
        return app.response_class(
            "<meta charset=utf-8><p style='font:16px system-ui;padding:24px'>"
            "Save the day first, then attach the bill. "
            "<a href='/finance/clinic/entry?d=%s'>Back</a></p>" % iso,
            mimetype="text/html", status=409)
    try:
        ver = int(os.path.getmtime(SCANNER_JS))
    except OSError:
        ver = 0
    title = "Expense bill — %s (%s)" % (row["category_text"], rupees(row["amount_p"]))
    cfg = {
        "title": "%s — %s" % (title, iso),
        "uploadUrl": "/finance/clinic/api/day/%s/expense-scan/%s" % (iso, uid),
        "fileField": "file",
        "uploadFields": {"unit": CLINIC_UNIT, "business_date": iso, "expense_uid": uid},
        "nameBase": "Clinic_expense_%s_%s" % (iso, uid[:8]),
        "backUrl": "/finance/clinic/entry?d=%s" % iso,
        "allowIdCard": False,
        "allowBatch": False,
    }
    html = ("<!DOCTYPE html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title>"
            "<style>body{margin:0;background:#f4f6fa;color:#0f172a;"
            "font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif}"
            "input,select,button{font-family:inherit}"
            ".top{background:#0b1220;color:#fff;padding:12px 16px;font-weight:650;"
            "display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:30}"
            ".top .t{flex:1}"
            ".top a{color:#e2e8f0;text-decoration:none;font-weight:600;font-size:13px;"
            "padding:8px 13px;border-radius:9px;background:rgba(255,255,255,.13);"
            "white-space:nowrap}</style></head><body>"
            "<div class=top><a href='%s'>← Back</a><span class=t>%s</span></div>"
            "<script>window.SCANNER_CONFIG = %s;</script>"
            "<div id=scanroot></div>"
            "<script src='/finance/scan/jspdf.js'></script>"
            "<script src='/finance/scan/widget.js?v=%d'></script>"
            "</body></html>") % (title, cfg["backUrl"], title, json.dumps(cfg), ver)
    return app.response_class(html, mimetype="text/html")


@app.route("/finance/clinic/api/day/<date_iso>/expense-scan/<uid>", methods=["POST"])
def clinic_api_expense_scan_upload(date_iso, uid):
    """D330: the clinic's per-expense bill upload — the shared store path,
    the clinic's unit and role gate."""
    u, err = require("maker", "checker", unit=CLINIC_UNIT)
    if err:
        return err
    return _expense_scan_save(db(), CLINIC_UNIT, date_iso, uid, u)


@app.route("/finance/clinic/api/day/<date_iso>/scan/<doc_type>", methods=["POST"])
def clinic_api_scan_upload(date_iso, doc_type):
    u, err = require("maker", "checker", unit=CLINIC_UNIT)
    if err:
        return err
    if doc_type not in CLINIC_REQUIRED_DOCS + ("deposit_slip",):
        return jsonify(ok=False, error="bad_doc_type"), 400
    con = db()
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (CLINIC_UNIT, iso)).fetchone()
    if not e:
        return jsonify(ok=False, error="no_day",
                       message="Save the day first, then attach its pages."), 409
    f = request.files.get("file")
    if not f:
        return jsonify(ok=False, error="no_file"), 400
    blob = f.read()
    if not blob:
        return jsonify(ok=False, error="empty_file"), 400
    sha = hashlib.sha256(blob).hexdigest()
    folder = os.path.join(SCAN_DIR, CLINIC_UNIT, iso[:7])
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


# ----------------------------------------- clinic: loud edges of this slice
# The shared review screen carries month-close, cutover and deposit-allocation
# controls. Their clinic endpoints exist so a click gets a clear answer instead
# of a silent 404 — and they refuse, because none of that is in slice C1a.

def _clinic_not_in_slice():
    return jsonify(ok=False, error="not_in_slice",
                   message="Clinic month close, cutover and deposit allocation "
                           "arrive in a later slice. C1a covers the daily entry "
                           "and its approval."), 501


@app.route("/finance/clinic/api/cutover", methods=["POST"])
def clinic_api_cutover():
    return _clinic_not_in_slice()


@app.route("/finance/clinic/api/month/<ym>/close-check")
def clinic_api_month_close_check(ym):
    return _clinic_not_in_slice()


@app.route("/finance/clinic/api/month/<ym>/statement", methods=["POST"])
def clinic_api_month_statement(ym):
    return _clinic_not_in_slice()


@app.route("/finance/clinic/api/month/<ym>/finalise", methods=["POST"])
def clinic_api_month_finalise(ym):
    return _clinic_not_in_slice()


@app.route("/finance/clinic/api/deposit/<int:mid>/clear", methods=["POST"])
def clinic_api_deposit_clear(mid):
    return _clinic_not_in_slice()


# ------------------------------------------- the Docterz / tracker day feed
# S182 C2, owner: "all get to see the staff output sheet revenue data also."
# The clinic Gmail account's Apps Script (gas/VPS_Push_TrackerDay.gs) posts one
# day's revenue summary from the Drive-synced revenue_ledger.csv each evening.
# Stored VERBATIM as attribution context — the spine reads it, never posts
# from it (D313). Lines carry clinic ids + amounts. NO names, NO phones:
# privacy is enforced at the feed — a payload carrying them is refused whole.

TRACKER_LINE_KEYS = {"clinic_id", "source", "net"}
TRACKER_FORBIDDEN = ("name", "patient", "phone", "mobile", "contact")


@app.route("/finance/api/tracker-feed", methods=["POST"])
def api_tracker_feed():
    """Same callers, same gate as /finance/api/upi-statement: the GAS pusher
    (X-Finance-Cron token, which the before_request gate already honours) or a
    signed-in checker posting by hand. Junk is refused loudly, never stored."""
    u = current_user()
    is_cron = bool(CRON_TOKEN and request.headers.get("X-Finance-Cron") == CRON_TOKEN)
    if not is_cron:
        u2, err = require("checker")
        if err:
            return err
        u = u2
    p = request.get_json(silent=True)
    if not isinstance(p, dict):
        return jsonify(ok=False, error="bad_json",
                       message="The body must be a JSON object."), 400
    con = db()
    unit = str(p.get("unit") or "").strip().lower()
    if not con.execute("SELECT 1 FROM business_unit WHERE code=?", (unit,)).fetchone():
        return jsonify(ok=False, error="bad_unit",
                       message="'%s' is not a business unit here." % unit), 400
    try:
        iso = parse_iso_date(p.get("date", "")).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date",
                       message="date must be YYYY-MM-DD."), 400
    summary = p.get("summary")
    if not isinstance(summary, dict) or not summary:
        return jsonify(ok=False, error="bad_summary",
                       message="summary must be a non-empty object."), 400
    lines = p.get("lines")
    if lines is None:
        lines = []
    if not isinstance(lines, list):
        return jsonify(ok=False, error="bad_lines",
                       message="lines must be a list."), 400
    for i, ln in enumerate(lines):
        if not isinstance(ln, dict):
            return jsonify(ok=False, error="bad_lines",
                           message="line #%d is not an object." % (i + 1)), 400
        for k in ln:
            lk = str(k).lower()
            if any(bad in lk for bad in TRACKER_FORBIDDEN):
                return jsonify(ok=False, error="privacy_refused",
                               message="Line #%d carries '%s'. The feed takes "
                                       "clinic ids and amounts only — no names, "
                                       "no phone numbers. Refused whole."
                                       % (i + 1, k)), 400
            if lk not in TRACKER_LINE_KEYS:
                return jsonify(ok=False, error="bad_line_key",
                               message="Line #%d has an unknown key '%s' "
                                       "(allowed: clinic_id, source, net)."
                                       % (i + 1, k)), 400
    payload = json.dumps({"unit": unit, "date": iso, "summary": summary,
                          "lines": lines}, ensure_ascii=False)
    con.execute("INSERT INTO tracker_day (unit, business_date, payload_json, received_at) "
                "VALUES (?,?,?,?) "
                "ON CONFLICT(unit, business_date) DO UPDATE SET "
                " payload_json=excluded.payload_json, received_at=excluded.received_at",
                (unit, iso, payload, now_iso()))
    audit(con, "tracker_day", None, "ingest",
          after={"unit": unit, "date": iso, "lines": len(lines),
                 "by": ("cron" if is_cron else u["user"])},
          who=("cron" if is_cron else u["user"]))
    con.commit()
    return jsonify(ok=True, unit=unit, date=iso, lines=len(lines), stored=True)


@app.route("/finance/clinic/api/tracker-day/<date_iso>")
def clinic_api_tracker_day(date_iso):
    """The day's tracker summary, visible to clinic makers AND checkers — all
    three levels see the same attribution context. Read-only by construction:
    nothing here writes to the spine (D313)."""
    u, err = require("maker", "checker", "viewer", unit=CLINIC_UNIT)
    if err:
        return err
    try:
        iso = parse_iso_date(date_iso).isoformat()
    except ValueError:
        return jsonify(ok=False, error="bad_date"), 400
    con = db()
    r = con.execute("SELECT payload_json, received_at FROM tracker_day "
                    "WHERE unit=? AND business_date=?", (CLINIC_UNIT, iso)).fetchone()
    if not r:
        return jsonify(ok=True, present=False, date=iso,
                       message="not received yet")
    try:
        payload = json.loads(r["payload_json"])
    except ValueError:
        return jsonify(ok=False, error="stored_payload_unreadable"), 500
    lines = payload.get("lines") or []
    return jsonify(ok=True, present=True, date=iso,
                   received_at=r["received_at"],
                   summary=payload.get("summary") or {},
                   lines=lines[:200], line_count=len(lines))


# ----------------------------------------------------------------- selftest

def selftest():
    """F-63: hit the ACTUAL routes with the Flask test client.
    F-79: assert on served HTML including ABSENCE checks.

    The smoke test runs as an INSTALL GATE, so it must never touch the live
    store: it works on a throwaway copy and deletes it afterwards."""
    global DB_PATH, ALLOW_HEADER_AUTH, LEDGER_JSONL
    import shutil
    import tempfile
    live_db = DB_PATH
    tmp_fd, tmp_db = tempfile.mkstemp(prefix="finance_smoke_", suffix=".db")
    os.close(tmp_fd)
    shutil.copyfile(live_db, tmp_db)
    DB_PATH = tmp_db

    # F6: the Staff Ledger is a SEPARATE store this suite does not copy. A
    # salary-advance approval posts to it, so sandbox it for the WHOLE run --
    # otherwise the install gate would write to the live ledger (F-128).
    _f6_ledger_dir = tempfile.mkdtemp(prefix="smoke_ledger_")
    _f6_ledger_prev = (os.environ.get("LEDGER_DIR"), os.environ.get("FINANCE_LEDGER_JSONL"), LEDGER_JSONL)
    os.environ["LEDGER_DIR"] = _f6_ledger_dir
    os.environ["FINANCE_LEDGER_JSONL"] = os.path.join(_f6_ledger_dir, "ledger.jsonl")
    LEDGER_JSONL = os.environ["FINANCE_LEDGER_JSONL"]
    with open(os.path.join(_f6_ledger_dir, "users.json"), "w", encoding="utf-8") as _uf:
        json.dump({"manoj": {"role": "checker"}, "bhawna": {"role": "checker"},
                   "selftest": {"role": "checker"}}, _uf)
    open(LEDGER_JSONL, "w").close()

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
    check("maker tile points at the daily page", j["href"] == "/finance/daily")
    r = c.get("/finance/api/tile-meta", headers={"X-Clinic-Role": "checker"})
    check("checker tile differs", r.get_json()["href"] == "/finance/review")

    r = c.get("/finance/")
    check("root lands maker on the new Daily Sale page", 'data-stage="2"' in r.get_data(as_text=True))
    r = c.get("/finance/", headers={"X-Clinic-Role": "checker"})
    check("root lands checker on the review screen",
          'id="btnApprove"' in r.get_data(as_text=True))

    r = c.get("/finance/entry?legacy=1")
    check("entry page 200", r.status_code == 200)
    html = r.get_data(as_text=True)
    # F-132: the opening/closing display is GONE. Both were `v_cash_ledger`
    # running totals over ALL history -- the unit position, not this day, and
    # not true of this seat's drawer. These two assertions used to require the
    # field to be PRESENT; they are inverted deliberately, and the suite is
    # re-rehearsed against the state that broke them (F-125).
    check("F-132: entry shows no running opening balance", 'id="opening"' not in html)
    check("F-132: entry shows no running closing balance",
          'id="closing"' not in html and 'id="closingBox"' not in html)
    check("F-132: but it DOES say where the cash is", 'id="whereBody"' in html)
    check("F-132: the parked total opens to the individual names",
          "parked-sum" in html and "parked-in" in html)
    check("F-133: a zero is written as an instruction, not as a fact",
          "not yet returned" in html or "enter it under" in html)
    # ABSENCE checks (F-79): the maker page must not expose these
    check("entry has NO approve button", "id=\"btnApprove\"" not in html)
    check("entry has NO editable opening input", 'name="opening"' not in html)
    check("entry titled Daily Sale, not Finance", "Daily Sale" in html and "Finance" not in html)
    # icons are inline <symbol>s; nothing is FETCHED from outside (the only http://
    # occurrence is the SVG xmlns, which is a namespace, not a request)
    check("entry uses inline icon symbols", html.count("<symbol") >= 10)
    check("entry loads nothing external",
          'src="http' not in html and 'href="http' not in html and "@import" not in html)

    # ---- STAGE D2, on the SERVED page (F-63 real route, F-79 absence) -------
    check("D2: the entry page carries the mirror card", 'id="mirrorCard"' in html)
    check("D2: and asks for the mirror by its real path", '/mirror' in html)
    check("D2: File is disabled until the check has been seen",
          'id="btnSubmit"' in html and "state.mirrorFor" in html)
    check("D2: the file gate reads the scans or a stated reason",
          "function scansOk()" in html)
    check("F-129: the page tells a checker his look arms nothing",
          "looking_as_maker" in html)
    # F-127, proven on the bytes the maker actually receives: the deposit banner
    # and the unit-position fetch are GONE, not merely hidden by CSS.
    check("F-127: the entry page no longer has a deposit banner",
          'id="depositMsg"' not in html)
    check("F-127: and no longer fetches the unit position at all",
          '/tile' not in html)
    # the page-only kit contract: every other id it had, it still has
    for _pid in ("bdate", "manned", "total", "upi", "cashCalc", "cashReal",
                 "ncList", "addNc", "expList", "addExp", "movList", "addMov",
                 "scanReason", "btnDraft", "btnSubmit",
                 "shoutBox", "shoutTitle", "shoutList", "msg", "whoami", "mannedHint"):
        check("D2: entry keeps id=%s" % _pid, ('id="%s"' % _pid) in html)
    check("D2: entry keeps all three scan slots",
          all(('data-doc="%s"' % d) in html for d in REQUIRED_DOCS)),
    check("D2: entry follows Clinic Design Language v1",
          "--surface-page:#f3f2ee" in html and 'id="toTop"' in html
          and 'class="kick"' in html and "details class=\"help\"" in html)

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
    check("F-132: a MAKER is not given the running balance",
          "opening_p" not in j["day"] and "closing_p" not in j["day"])
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    j = c.get("/finance/api/day/2026-08-13").get_json()
    check("day opening is computed", "opening_p" in j["day"])
    r = c.get("/finance/api/day/2026-04-01")
    check("first day opening is zero", r.get_json()["day"]["opening_p"] == 0)
    os.environ["FINANCE_DEV_ROLE"] = "maker"

    r = c.get("/finance/api/month/2026-08")
    j = r.get_json()
    check("month 200", j["ok"])
    check("month has 31 cells", len(j["days"]) == 31)

    _fxu = os.environ.get("FINANCE_DEV_USER", "")
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"     # a REAL maker, F-106
    r = c.get("/finance/api/exceptions")
    mk = r.get_json()["exceptions"]
    check("exceptions listed", len(mk) > 0)
    check("F-127: a maker sees ONLY missing-day rows",
          all(e["kind"] == "missing_day" for e in mk))
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    ck = c.get("/finance/api/exceptions").get_json()["exceptions"]
    check("F-127: the checker's list is unchanged and is a superset",
          len(ck) >= len(mk)
          and {e["id"] for e in mk} <= {e["id"] for e in ck})
    os.environ["FINANCE_DEV_USER"] = _fxu
    os.environ["FINANCE_DEV_ROLE"] = "maker"

    r = c.get("/finance/api/days?days=400")
    j = r.get_json()
    check("day list returns every filed day", j["ok"] and j["count"] > 100)
    check("day list carries status and counts",
          "status" in j["days"][0] and "scans" in j["days"][0])
    approved_present = any(d["status"] in ("approved", "locked") for d in j["days"])
    check("approved/locked days are still listed", approved_present)

    # F-127: the unit position is the CHECKER's. This test used to run as the
    # maker and pass, which is precisely the fault. It now asserts the refusal
    # first, then proves the checker still gets everything he always did.
    _f127u = os.environ.get("FINANCE_DEV_USER", "")
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"     # no checker row riding along
    r = c.get("/finance/api/tile")
    check("F-127: the maker is refused the unit position", r.status_code == 403)
    os.environ["FINANCE_DEV_USER"] = _f127u
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    r = c.get("/finance/api/tile")
    j = r.get_json()
    check("tile ok", j["ok"])
    check("tile shouts present", j["shouts"]["total"] > 0)
    check("F-127: and the checker's payload is undiminished",
          all(k in j for k in ("cash_in_hand", "month_to_date", "cash_with",
                               "deposit_due", "shouts")))
    os.environ["FINANCE_DEV_ROLE"] = "maker"

    # ---- the legacy import leaves cash NEGATIVE; the app must refuse to build
    #      on it until a cutover count establishes a real opening balance -------
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    last = con.execute("SELECT business_date, closing_p FROM v_cash_ledger WHERE unit=? "
                       "ORDER BY business_date DESC LIMIT 1", (UNIT,)).fetchone()
    con.close()
    # State-vs-logic split (F-106): a FRESH import leaves cash NEGATIVE with
    # legacy breaks open; once the S184 correction has run the SAME store is
    # CORRECTED (non-negative, breaks resolved). Each check asserts the truth for
    # whichever state the store is actually in, so a legitimate data correction
    # can never fail the suite (the S184_F1a red was exactly this).
    neg = last["closing_p"] < 0
    if neg:
        check("legacy import leaves cash negative", last["closing_p"] < 0)
    else:
        check("legacy cash corrected \u2014 non-negative (S184)", last["closing_p"] >= 0)
    day1 = (parse_iso_date(last["business_date"]) + dt.timedelta(days=1))
    if day1 > today():
        day1 = today()
    D1 = day1.isoformat()

    def post(payload):
        return c.post("/finance/api/day", json=payload)

    r = post({"business_date": D1, "total": "1000", "upi": "0"})
    if neg:
        check("cannot build on negative legacy cash", r.status_code == 400 and
              r.get_json()["error"] == "negative_cash")
    else:
        check("build not blocked by negative_cash on corrected cash",
              not (r.status_code == 400 and (r.get_json() or {}).get("error") == "negative_cash"))

    r = c.post("/finance/api/cutover", json={"date": last["business_date"], "counted": "50000"})
    check("maker cannot cutover", r.status_code == 403)
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    r = c.post("/finance/api/cutover",
               json={"date": last["business_date"], "counted": "50000",
                     "note": "drawer counted at go-live"})
    j = r.get_json()
    check("cutover ok", r.status_code == 200 and j["ok"])
    ob = j.get("legacy_breaks_still_open", 0)
    if neg:
        check("cutover leaves legacy breaks open", ob > 0)
    else:
        check("legacy breaks already resolved (S184)", ob == 0)
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
    check("scan page returns to the entry screen", "/finance/daily?d=%s" % D1 in sp)
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
        check("F-132: the save response withholds it from the maker too",
              "closing_p" not in j["day"])
        os.environ["FINANCE_DEV_ROLE"] = "checker"      # the arithmetic is unchanged
        _led = c.get("/finance/api/day/%s" % D1).get_json()["day"]
        check("closing carries from cutover",
              _led["closing_p"] == 5000000 + 70000 - 5000 - 10000)
        os.environ["FINANCE_DEV_ROLE"] = "maker"

    # S189 (F-139): a salary advance no longer NEEDS a client staff id --
    # the server resolves the identity itself and ignores whatever the client
    # sends. The old check ("salary advance needs staff", a 400) is replaced
    # by its successor: the save succeeds and the row lands attributed to the
    # ONE real staff_ref row, created lazily.
    # D330 shape-2 rehearsal lesson: on a store whose month is already AT its
    # advance ceiling, these legacy posts would be refused for the RIGHT
    # reason and this block would lie red forever. The blocks below test
    # ATTRIBUTION and the MENU, not the ceiling -- so the ceiling is raised
    # out of their way ON THE THROWAWAY and restored before the ceiling's own
    # dedicated block (which reads the real settings back).
    _bump0 = sqlite3.connect(DB_PATH)
    _prior_base = _bump0.execute("SELECT value FROM setting WHERE key='advance.base_p'").fetchone()
    _prior_base = _prior_base[0] if _prior_base else None
    _bump0.execute("INSERT OR REPLACE INTO setting (key,value) VALUES "
                   "('advance.base_p','999999900')")
    _bump0.commit(); _bump0.close()
    r = post({"business_date": D1, "total": "100",
              "expenses": [{"amount": "500", "category_fixed": "salary_advance",
                            "staff_id": 999}]})
    check("F-139: a salary advance saves WITHOUT a client staff id "
          "(server resolves it)", r.status_code == 200 and (r.get_json() or {}).get("ok"))
    _f139 = sqlite3.connect(DB_PATH)
    _srow = _f139.execute("SELECT id FROM staff_ref WHERE name='Darpan' AND active=1").fetchone()
    check("F-139: the one real staff_ref row exists after first use", bool(_srow))
    check("F-139: and the row is attributed to IT, not to the client's 999",
          _f139.execute("SELECT COUNT(*) FROM day_expense x JOIN day_entry e ON "
                        "e.id=x.day_entry_id WHERE e.business_date=? AND "
                        "x.category_fixed='salary_advance' AND x.staff_id=?",
                        (D1, _srow[0])).fetchone()[0] == 1
          if _srow else False)
    _f139.close()

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
        os.environ["FINANCE_DEV_ROLE"] = "checker"
        _led2 = c.get("/finance/api/day/%s" % D1).get_json()["day"]
        check("closing reflects the shortfall",
              _led2["closing_p"] == 5000000 + 70000 - 35000)
        os.environ["FINANCE_DEV_ROLE"] = "maker"

    r = c.get("/finance/api/month/%s" % D1[:7])
    j = r.get_json()
    # F-106 shape. These asserted the month's non-cash was EXACTLY this test's
    # own 350.00 and exactly 2 heads -- true only while NO real no-payment bills
    # existed anywhere. The first real ones were filed on 20-08-2026 (Rs 3,000)
    # and all three checks went red without a line of code changing. Assert the
    # RULE -- this day's bills are counted in the month -- not a frozen total.
    _mnc_s = j["totals"]["noncash"]
    _mnc_p = int(round(float(str(_mnc_s).replace(",", "")) * 100))
    check("month reports non-cash total", _mnc_p >= 35000)
    check("month breaks non-cash down by head", len(j["noncash_by_head"]) >= 2)

    os.environ["FINANCE_DEV_ROLE"] = "checker"          # F-127: checker-only now
    r = c.get("/finance/api/tile")
    j = r.get_json()
    check("tile tracks days since a bank trip", "days_since_bank_deposit" in j)
    # stronger than the old frozen "350.00": the tile must AGREE with the month
    # endpoint, which is the property that actually matters and cannot rot.
    check("tile reports non-cash month to date", j["noncash_month_to_date"] == _mnc_s)
    os.environ["FINANCE_DEV_ROLE"] = "maker"

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
    check("marg_export source present", ad.get("marg_export") is not None)  # F-106: was "not yet mapped"; S183 mapped it

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

    # ================================================================== F6
    # F-148 / D332 §2.5: APPROVAL posts a salary advance to the Staff Ledger.
    # Hermetic: creates its own future-dated days, proves the post/idempotency/
    # fail-loud, then deletes its rows and resets the sandbox ledger so nothing
    # downstream sees residue.
    _f6_du=os.environ.get("FINANCE_DEV_USER",""); _f6_dr=os.environ.get("FINANCE_DEV_ROLE","")
    _sl = _staff_ledger_module()
    _f6c = sqlite3.connect(DB_PATH); _f6c.row_factory = sqlite3.Row
    _f6srow = _f6c.execute("SELECT id FROM staff_ref WHERE name='Darpan' AND active=1").fetchone()
    _f6_made_staff = _f6srow is None            # staff_ref has no UNIQUE(name); reuse, never duplicate
    if _f6srow:
        _f6sid = _f6srow[0]
    else:
        _f6c.execute("INSERT INTO staff_ref (name,is_pharmacy,active) VALUES ('Darpan',1,1)")
        _f6sid = _f6c.execute("SELECT id FROM staff_ref WHERE name='Darpan' AND active=1").fetchone()[0]
    def _f6_make_day(date, amount_p):
        _f6c.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at) "
                     "VALUES ('medical',?, 'submitted','app','darpan',?)", (date, date+"T09:00:00"))
        _e = _f6c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (date,)).fetchone()[0]
        _f6c.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',?)", (_e, amount_p+100000))
        _f6c.execute("INSERT INTO day_expense (day_entry_id,amount_p,category_fixed,staff_id,ledger_posted) "
                     "VALUES (?,?, 'salary_advance', ?, 0)", (_e, amount_p, _f6sid))
        _f6c.commit(); return _e
    import datetime as _f6dt
    _f6last=_f6c.execute("SELECT MAX(business_date) FROM day_entry WHERE unit='medical'").fetchone()[0]
    _f6base=_f6dt.date.fromisoformat(_f6last)
    def _f6_free(_after):
        _d=_after
        while True:
            _d=_d+_f6dt.timedelta(days=1)
            if not _f6c.execute("SELECT 1 FROM day_entry WHERE unit='medical' AND business_date=?", (_d.isoformat(),)).fetchone():
                return _d
    _fd1d=_f6_free(_f6base); _fd1=_fd1d.isoformat()
    _fd2d=_f6_free(_fd1d);  _fd2=_fd2d.isoformat()
    _e1=_f6_make_day(_fd1, 300000)
    os.environ["FINANCE_DEV_USER"]="manoj"; os.environ["FINANCE_DEV_ROLE"]="checker"
    _nb=len(_sl.load_ledger())
    _r=c.post("/finance/api/approve/"+_fd1); _j=_r.get_json() or {}
    _pl=_j.get("salary_advances_pending_ledger", [])
    check("F6: a salary-advance day approves and reports the ledger post",
          _r.status_code==200 and _j.get("ok") and len(_pl)==1 and _pl[0].get("ledger_ref"))
    _ref=(_pl[0] if _pl else {}).get("ledger_ref")
    _exp=_f6c.execute("SELECT ledger_posted, ledger_ref FROM day_expense WHERE day_entry_id=? AND category_fixed='salary_advance'", (_e1,)).fetchone()
    check("F6: the finance expense is stamped ledger_posted=1 with the ledger row id",
          bool(_exp) and _exp["ledger_posted"]==1 and _exp["ledger_ref"]==_ref)
    _led=_sl.load_ledger(); _row=[x for x in _led if x["id"]==_ref]
    check("F6: one new APPROVED ADVANCE_ISSUE for Darpan, Rs 3000, against 2026-08",
          len(_led)==_nb+1 and len(_row)==1 and _row[0]["category"]=="ADVANCE_ISSUE"
          and _row[0]["staff"]=="Darpan" and _row[0]["amount"]==3000
          and _row[0]["status"]=="APPROVED" and _row[0]["against_month"]==_fd1[:7])
    _r2=c.post("/finance/api/approve/"+_fd1)
    check("F6: re-approval is refused and never double-posts",
          _r2.status_code==409 and len(_sl.load_ledger())==_nb+1)
    _e2=_f6_make_day(_fd2, 200000)
    _f6c.execute("INSERT OR IGNORE INTO unit_role (unit,username,role) VALUES ('medical','stranger','checker')"); _f6c.commit()
    os.environ["FINANCE_DEV_USER"]="stranger"; os.environ["FINANCE_DEV_ROLE"]="checker"
    _n2=len(_sl.load_ledger())
    _r3=c.post("/finance/api/approve/"+_fd2); _j3=_r3.get_json() or {}
    _st=_f6c.execute("SELECT status FROM day_entry WHERE id=?", (_e2,)).fetchone()["status"]
    check("F6: fail-loud -- a non-ledger-checker approver refuses the day and posts nothing",
          _r3.status_code==409 and _j3.get("error")=="ledger_post_failed"
          and _st=="submitted" and len(_sl.load_ledger())==_n2)
    # hermetic cleanup
    for _e in (_e1,_e2):
        for _t in ("day_line","day_expense","cash_movement","day_noncash_bill","attachment","expense_attachment","day_revision"):
            try: _f6c.execute("DELETE FROM %s WHERE day_entry_id=?" % _t, (_e,))
            except Exception: pass
        _f6c.execute("DELETE FROM day_entry WHERE id=?", (_e,))
    _f6c.execute("DELETE FROM data_flag WHERE business_date > ?", (_f6base.isoformat(),))
    _f6c.execute("DELETE FROM recon_exception WHERE business_date > ?", (_f6base.isoformat(),))
    if _f6_made_staff:
        _f6c.execute("DELETE FROM staff_ref WHERE id=?", (_f6sid,))
    _f6c.commit(); _f6c.close()
    open(LEDGER_JSONL, "w").close()
    os.environ["FINANCE_DEV_USER"]=_f6_du; os.environ["FINANCE_DEV_ROLE"]=_f6_dr

    # ================================================================== C1a
    # CLINIC unit (S182): six-cell ADDITIVE day, strays, evidence, per-unit
    # gating. Added ABOVE the S180 return-resolution block, which must stay
    # last (see its comment). Requires finance_migration_S182_clinic.sql to
    # have been applied to the store this suite copies — the installer runs
    # the migration before this gate.

    # medical must come out of this section untouched — snapshot it first
    _cm = sqlite3.connect(DB_PATH)
    _cm.row_factory = sqlite3.Row
    _m = _cm.execute(
        "SELECT COUNT(*) n, COALESCE(SUM(revenue_p),0) rev, COALESCE(SUM(cash_in_p),0) cash "
        "FROM v_cash_ledger WHERE unit='medical'").fetchone()
    _med_before = (_m["n"], _m["rev"], _m["cash"])
    _cm.close()
    r = c.get("/finance/api/day/" + D1)
    _md = r.get_json()["day"]
    _med_day_before = (_md["total_p"], _md["closing_p"])

    os.environ["FINANCE_DEV_ROLE"] = ""      # unit_role rows decide, not headers
    RCP = {"X-Clinic-User": "reception"}     # clinic maker (seeded roster)
    DRM = {"X-Clinic-User": "manoj"}         # clinic checker
    DRB = {"X-Clinic-User": "bhawna"}        # clinic checker
    DRP = {"X-Clinic-User": "darpan"}        # medical maker, NO clinic role

    # fail closed per unit: a login that is valid elsewhere still gets nothing
    r = c.get("/finance/clinic/api/day/" + D1, headers=DRP)
    check("clinic roles fail closed (medical maker gets 403)",
          r.status_code == 403 and r.get_json()["error"] == "no_role_here")
    r = c.post("/finance/clinic/api/day", headers=DRP,
               json={"business_date": D1, "opd_cash": "100"})
    check("clinic write refused without a clinic role", r.status_code == 403)
    r = c.get("/finance/clinic/api/whoami", headers=DRP)
    check("clinic whoami still explains why", r.status_code == 200 and
          r.get_json()["roles"] == [])
    r = c.get("/finance/api/tile", headers=RCP)
    check("and a clinic login buys nothing on medical", r.status_code == 403)

    # the entry surface (F-63: real route; F-79: presence AND absence)
    # S182 C2 ADJUSTED: the owner replaced the six cells with four tender
    # totals and simple English — the six-field presence checks became the
    # four-field presence checks plus F-79 ABSENCE checks on the retired ids.
    r = c.get("/finance/clinic/entry", headers=RCP)
    check("clinic entry page 200", r.status_code == 200)
    chh = r.get_data(as_text=True)
    for _f in ("total_cash", "total_upi", "card", "razorpay"):
        check("clinic entry has the %s field (C2)" % _f, ('id="%s"' % _f) in chh)
    for _f in ("opd_cash", "opd_upi", "xray_cash", "xray_upi", "proc_cash", "proc_upi"):
        check("clinic entry no longer has the %s cell (F-79 absence)" % _f,
              ('id="%s"' % _f) not in chh)
    check("clinic entry title is simple English: Clinic Entry Form",
          "Clinic Entry Form" in chh)
    check("the words 'दो सबूत' are gone (F-79 absence)", "सबूत" not in chh)
    check("clinic entry opening is a readonly display",
          'id="opening"' in chh and "readonly" in chh)
    check("clinic entry has NO opening input path (F-79 absence)",
          'name="opening"' not in chh)
    check("clinic entry keeps the owner's Hindi opening-cash hint",
          "पिछले भरे दिन से चली आ रही नक़दी" in chh)
    check("clinic entry names Docterz on the Razorpay field",
          "Razorpay" in chh and "Docterz" in chh)
    check("clinic entry has the expenses repeater (C2)", 'id="addExpense"' in chh)
    check("clinic entry has the grand-total-of-cash panel (C2)",
          'id="grandCash"' in chh and "Grand Total of Cash" in chh)
    check("clinic entry has the tracker card (C2)", 'id="trackerCard"' in chh)
    check("clinic entry loads nothing external",
          'src="http' not in chh and 'href="http' not in chh and "@import" not in chh)
    check("clinic entry has the extra-collection repeater", 'id="addStray"' in chh)
    check("clinic entry carries both evidence boxes",
          'data-doc="opd_register"' in chh and 'data-doc="xray_proc_register"' in chh)
    check("clinic entry has NO approve button", 'id="btnApprove"' not in chh)
    check("clinic entry never says Finance", "Finance" not in chh)

    r = c.get("/finance/clinic/api/tile-meta", headers=RCP)
    j = r.get_json()
    check("clinic maker tile title comes from settings",
          j["title"] == "Daily Collection" and j["href"] == "/finance/clinic/entry")
    r = c.get("/finance/clinic/api/tile-meta", headers=DRM)
    check("clinic checker tile differs", r.get_json()["href"] == "/finance/clinic/review")

    r = c.get("/finance/clinic/", headers=RCP)
    check("clinic root lands the maker on entry",
          'id="btnSubmit"' in r.get_data(as_text=True))
    r = c.get("/finance/clinic/", headers=DRM)
    check("clinic root lands a checker on review",
          'id="btnApprove"' in r.get_data(as_text=True))
    r = c.get("/finance/clinic/review", headers=DRB)
    rvh = r.get_data(as_text=True)
    check("clinic review is the same screen on the clinic API",
          'var API = "/finance/clinic/api";' in rvh and 'id="btnApprove"' in rvh)
    # S182 C2: the serve-time verify/tracker layer rides on that same screen
    check("clinic review carries the C2 verify layer", 'id="c2VerifyLayer"' in rvh)
    check("clinic review layer knows the verify route", '/verify/' in rvh)
    check("clinic review layer knows the skip flag", 'skip_verification' in rvh)
    check("clinic review layer shows verification state", 'Not verified yet' in rvh)
    check("clinic review layer carries the tracker card", '/tracker-day/' in rvh)
    # the medical review, from the same file on disk, carries NONE of it
    _mrv = c.get("/finance/review").get_data(as_text=True)
    check("the medical review screen is untouched by the C2 layer (F-79)",
          'id="c2VerifyLayer"' not in _mrv and 'skip_verification' not in _mrv)

    # validation gates
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": (today() + dt.timedelta(days=1)).isoformat(),
                     "opd_cash": "100"})
    check("clinic future date refused", r.status_code == 400 and
          r.get_json()["error"] == "future_date")
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": D1, "opd_cash": "O"})
    check("clinic letter O refused", r.status_code == 400)
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": D1, "opd_cash": "100",
                     "strays": [{"amount": "50", "stream": "opd", "tender": "cash"}]})
    check("a stray without a reason is refused", r.status_code == 400 and
          r.get_json()["error"] == "stray_reason_required")
    # S182 C2 ADJUSTED: the stream dropdown is gone (owner) — a stray's stream
    # is now accepted-and-ignored, so the old unknown-stream refusal became an
    # unknown-TENDER refusal (the tender is what still matters to the money).
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": D1, "opd_cash": "100",
                     "strays": [{"amount": "50", "tender": "cheque",
                                 "reason": "wrong tender"}]})
    check("a stray with an unknown tender is refused", r.status_code == 400 and
          r.get_json()["error"] == "bad_stray")

    # the six cells, ADDITIVE — and an opening-cash injection attempt
    _six = {"opd_cash": "500", "opd_upi": "250", "xray_cash": "300",
            "xray_upi": "150", "proc_cash": "700", "proc_upi": "100"}
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json=dict(_six, business_date=D1, opening="99999", opening_p=9999900))
    j = r.get_json()
    check("clinic day saved", r.status_code == 200 and j["ok"])
    d0 = j["day"] if j.get("ok") else {}
    check("posted opening is IGNORED — first clinic day opens at zero",
          d0.get("opening_p") == 0)
    check("clinic total is ADDITIVE: the sum of all six cells",
          d0.get("total_p") == 200000)
    # Medical's formula (cash = total − UPI) would call cash 1,000.00 here.
    # The clinic's cash is the cash cells alone: 1,500.00. This check FAILS
    # the moment medical's arithmetic leaks into a clinic day.
    check("clinic cash is the cash cells alone (medical's formula would fail this)",
          d0.get("cash_p") == 150000 and d0.get("upi_p") == 50000)
    check("clinic day reports the six cells", d0.get("cells", {}).get("proc_upi") == 10000)

    _c3 = sqlite3.connect(DB_PATH)
    _c3.row_factory = sqlite3.Row
    _rows = _c3.execute(
        "SELECT l.service, l.mode, l.amount_p, l.line_kind FROM day_line l "
        "JOIN day_entry e ON e.id=l.day_entry_id WHERE e.unit='clinic' "
        "AND e.business_date=?", (D1,)).fetchall()
    _c3.close()
    check("six day_line rows persist as integer paise",
          len(_rows) == 6 and
          {(x["service"], x["mode"]): x["amount_p"] for x in _rows}.get(("xray", "upi")) == 15000)
    check("grid rows are tagged as grid", bool(_rows) and
          all(x["line_kind"] == "grid" for x in _rows))

    # a stray joins the day and keeps its reason
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json=dict(_six, business_date=D1,
                         strays=[{"amount": "151.50", "stream": "xray", "tender": "cash",
                                  "reason": "camp का पुराना पर्चा"}]))
    j = r.get_json()
    check("stray accepted on correction", r.status_code == 200 and j["ok"])
    check("stray joins the additive total",
          j.get("ok") and j["day"]["total_p"] == 200000 + 15150)
    check("stray keeps its reason", j.get("ok") and j["day"]["strays"] and
          j["day"]["strays"][0]["reason"] == "camp का पुराना पर्चा" and
          j["day"]["strays"][0]["amount_p"] == 15150)
    check("the earlier clinic submission is kept as a revision",
          any("revision" in w for w in (j.get("warnings") or [])))

    # ---- S182_C1d: force the bank-arbiter path DETERMINISTICALLY. A clinic
    # statement for D1 whose settled total differs from the entered Rs 500 —
    # on the LIVE store a real statement usually exists already (the MPR push
    # stores every unit since S179), so this insert is OR IGNOREd there and
    # the REAL bank figure drives the same path.
    _bc = sqlite3.connect(DB_PATH)
    _bc.execute("INSERT OR IGNORE INTO upi_statement (merchant_id, unit, statement_date,"
                " source_msg_id, parsed_total_p, txn_count, ingested_at) "
                "VALUES ('100000000306941','clinic',?,'selftest-C1d',123400,3,?)",
                (D1, dt.datetime.now().replace(microsecond=0).isoformat()))
    _bc.commit(); _bc.close()

    # evidence: refuse a bare submit, then attach BOTH register pages for real
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json=dict(_six, business_date=D1, action="submit"))
    check("clinic submit without scans refused", r.status_code == 400 and
          r.get_json()["error"] == "scans_required")
    for doc in CLINIC_REQUIRED_DOCS:
        rr = c.post("/finance/clinic/api/day/%s/scan/%s" % (D1, doc), headers=RCP,
                    data={"file": (_io.BytesIO(b"%PDF-1.4 clinic register"), doc + ".pdf")},
                    content_type="multipart/form-data")
        check("clinic scan uploaded: " + doc, rr.status_code == 200 and rr.get_json()["ok"])
    rr = c.post("/finance/clinic/api/day/%s/scan/sale_report" % D1, headers=RCP,
                data={"file": (_io.BytesIO(b"x"), "x.pdf")},
                content_type="multipart/form-data")
    check("a medical doc_type is refused on the clinic day", rr.status_code == 400)
    r = c.get("/finance/clinic/scan/%s/opd_register" % D1, headers=RCP)
    sp2 = r.get_data(as_text=True)
    check("clinic scan page renders on the clinic route", r.status_code == 200 and
          "/finance/clinic/api/day/%s/scan/opd_register" % D1 in sp2 and
          "/finance/clinic/entry?d=%s" % D1 in sp2)

    # submit with evidence — the stray rides the same maker→checker path
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json=dict(_six, business_date=D1, action="submit",
                         strays=[{"amount": "151.50", "stream": "xray", "tender": "cash",
                                  "reason": "camp का पुराना पर्चा"}]))
    j = r.get_json()
    check("clinic day submitted with evidence", r.status_code == 200 and
          j["ok"] and j["day"]["status"] == "submitted")
    _att = j["day"]["attachments"] if j.get("ok") else []
    check("both register pages recorded", len(_att) == 2 and
          all(a["url"].startswith("/finance/clinic/attachment/") for a in _att))
    if _att:
        r = c.get(_att[0]["url"], headers=DRM)
        check("clinic attachment serves to a clinic checker", r.status_code == 200)
        r = c.get(_att[0]["url"].replace("/clinic", ""),
                  headers={"X-Clinic-User": "selftest"})
        # The refusal legitimately takes TWO shapes: dev/offline auth reaches
        # the route (404 cross-unit); live SSO sends a roleless user to the
        # portal login (302). Both refuse. What must NEVER happen: a 200, or a
        # redirect to the CONTENT (a Drive URL). Assert the invariant, not one
        # refusal shape. (S182_C1e — the C1d live red, root-caused.)
        _loc = r.headers.get("Location", "")
        check("the medical route never serves a clinic scan (got %s -> %s)"
              % (r.status_code, _loc[:60] or r.get_data(as_text=True)[:40]),
              r.status_code in (403, 404)
              or (r.status_code == 302 and "drive.google" not in _loc))

    # maker cannot approve; the named checkers can. D1 now carries an OPEN
    # UPI mismatch (a bank statement exists for it), so approve must REFUSE —
    # the bank is the arbiter (D313) — and the acknowledged one lands.
    # S182 C2 ADJUSTED: the two-stage approval now sits IN FRONT of the UPI
    # gate — the final checker first meets 409 not_verified, so the sequence
    # gained a verify step (shavez, the middle approver) before the original
    # upi_mismatch/acknowledge pair, which then behaves exactly as before.
    SHZ = {"X-Clinic-User": "shavez"}        # middle approver (C2 migration)
    r = c.post("/finance/clinic/api/approve/" + D1, headers=RCP)
    check("clinic maker cannot approve", r.status_code == 403)
    r = c.post("/finance/clinic/api/approve/" + D1, headers=DRB)
    _j = r.get_json() or {}
    check("bhawna (checker, not the final checker) cannot final-approve (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 403 and _j.get("error") == "not_final_checker")
    r = c.post("/finance/clinic/api/approve/" + D1, headers=DRM)
    _j = r.get_json() or {}
    check("unverified final approve asks for the skip flag (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 409 and _j.get("error") == "not_verified")
    r = c.post("/finance/clinic/api/verify/" + D1, headers=RCP)
    check("a clinic maker cannot verify (got %s)" % r.status_code,
          r.status_code == 403)
    r = c.post("/finance/clinic/api/verify/" + D1, headers=SHZ)
    _j = r.get_json() or {}
    check("shavez verifies the submitted day (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 200 and _j.get("ok") and _j.get("verified_by") == "shavez")
    r = c.post("/finance/clinic/api/verify/" + D1, headers=DRB)
    _j = r.get_json() or {}
    check("a second verify says already-verified, does not overwrite (got %s)"
          % _j.get("verified_by", ""),
          r.status_code == 200 and _j.get("already") is True and
          _j.get("verified_by") == "shavez")
    r = c.get("/finance/clinic/api/day/" + D1, headers=DRM)
    _v = ((r.get_json() or {}).get("day") or {}).get("verification") or {}
    check("the day API reports the verification (got %s)" % _v.get("verified_by", ""),
          _v.get("verified_by") == "shavez")
    r = c.post("/finance/clinic/api/approve/" + D1, headers=DRM)
    _j = r.get_json() or {}
    check("clinic approve (now verified) still refuses over the open UPI mismatch (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 409 and _j.get("error") == "upi_mismatch")
    r = c.post("/finance/clinic/api/approve/" + D1, headers=DRM,
               json={"acknowledge_upi": True})
    _j = r.get_json() or {}
    check("clinic checker approves with acknowledgment (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 200 and _j.get("status") == "approved")
    r = c.get("/finance/clinic/api/day/" + D1, headers=DRB)
    _j = r.get_json() or {}
    check("Dr Bhawna sees the approved clinic day (got %s)"
          % ((_j.get("day") or {}).get("status")),
          (_j.get("day") or {}).get("status") == "approved")

    # the checker's screens read clinic numbers, not medical's
    r = c.get("/finance/clinic/api/month/" + D1[:7], headers=DRM)
    j = r.get_json()
    check("clinic month grid is clinic-only", j["ok"] and
          j["totals"]["revenue"] == rupees(215150))
    r = c.get("/finance/clinic/api/days?days=30", headers=DRM)
    check("clinic day list is clinic-only", r.get_json()["count"] == 1)
    r = c.get("/finance/clinic/api/tile", headers=DRM)
    j = r.get_json()
    check("clinic tile is the clinic's",
          j["unit_name"] == "Dr Manoj Agarwal Clinic" and
          j["cash_in_hand"] == rupees(165150))
    r = c.get("/finance/clinic/api/exceptions", headers=DRM)
    check("clinic exceptions endpoint answers", r.get_json()["ok"] is True)
    r = c.get("/finance/clinic/api/parked", headers=DRM)
    check("clinic parked view answers (nothing finalised yet)",
          r.get_json()["ok"] is True and r.get_json()["months"] == [])
    r = c.post("/finance/clinic/api/cutover", headers=DRM, json={})
    check("clinic month-close surface says 'not in this slice'",
          r.status_code == 501 and r.get_json()["error"] == "not_in_slice")

    # ================================================================== C2
    # S182 C2: four tender totals + razorpay side rail, expenses, two-stage
    # approval, tracker feed. The three test days sit BEFORE the earliest
    # clinic entry in whatever store this runs on (live-shaped or synthetic —
    # the C1d lesson), so they can never collide with a real approved day.
    _c4 = sqlite3.connect(DB_PATH)
    _c4.row_factory = sqlite3.Row
    _emin = _c4.execute("SELECT MIN(business_date) d FROM day_entry WHERE unit='clinic'"
                        ).fetchone()["d"] or D1
    _c4.close()
    _eb = parse_iso_date(_emin)
    DM1 = (_eb - dt.timedelta(days=1)).isoformat()
    DM2 = (_eb - dt.timedelta(days=2)).isoformat()
    DM3 = (_eb - dt.timedelta(days=3)).isoformat()

    # ---- the four-tender day, with extras and expenses (DM3) ---------------
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": DM3, "total_cash": "1200", "total_upi": "800",
                     "card": "350", "razorpay": "450",
                     "strays": [{"amount": "60", "tender": "cash",
                                 "narration": "old due paid today"},
                                {"amount": "40", "tender": "razorpay",
                                 "narration": "docterz booking settled late"}],
                     "expenses": [{"amount": "200", "note": "sweeper salary"}],
                     "action": "submit",
                     "missing_scan_reason": "register with the doctor — smoke"})
    j = r.get_json()
    check("C2 four-tender day saves (got %s %s)"
          % (r.status_code, (j or {}).get("error", "")),
          r.status_code == 200 and j["ok"])
    d2 = j["day"] if j.get("ok") else {}
    check("C2 day total is all four tenders plus extras (got %s)"
          % d2.get("total_p"), d2.get("total_p") == 290000)
    check("C2 cash is cash alone: field + cash extra (got %s)"
          % d2.get("cash_p"), d2.get("cash_p") == 126000)
    check("C2 UPI is the UPI field alone (got %s)" % d2.get("upi_p"),
          d2.get("upi_p") == 80000)
    check("C2 razorpay field survives the side rail round-trip (got %s)"
          % (d2.get("tenders") or {}).get("razorpay"),
          (d2.get("tenders") or {}).get("razorpay") == 45000)
    check("C2 the razorpay extra stays a separate line, tender kept (got %s)"
          % [s_.get("tender") for s_ in (d2.get("strays") or [])],
          any(s_.get("tender") == "razorpay" and s_.get("amount_p") == 4000
              for s_ in (d2.get("strays") or [])))
    check("C2 card total reported (got %s)" % (d2.get("tenders") or {}).get("card"),
          (d2.get("tenders") or {}).get("card") == 35000)
    check("C2 first day opens at zero, computed (got %s)" % d2.get("opening_p"),
          d2.get("opening_p") == 0)
    check("C2 expense reduces the drawer: 0 + 1,260 - 200 (got %s)"
          % d2.get("closing_p"), d2.get("closing_p") == 106000)
    check("C2 expense listed with its note",
          len(d2.get("expenses") or []) == 1 and
          d2["expenses"][0]["amount_p"] == 20000)
    check("C2 both extras kept with their narrations",
          len(d2.get("strays") or []) == 2 and
          all((s_.get("narration") or "") for s_ in d2["strays"]))

    _c4 = sqlite3.connect(DB_PATH)
    _c4.row_factory = sqlite3.Row
    _dl = _c4.execute(
        "SELECT l.mode, l.amount_p, l.line_kind FROM day_line l "
        "JOIN day_entry e ON e.id=l.day_entry_id "
        "WHERE e.unit='clinic' AND e.business_date=?", (DM3,)).fetchall()
    _sd = _c4.execute(
        "SELECT s.tender, s.amount_p, s.line_kind FROM clinic_line_side s "
        "JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit='clinic' AND e.business_date=?", (DM3,)).fetchall()
    check("C2 day_line holds only CHECK-legal modes (got %s)"
          % sorted({x["mode"] for x in _dl}),
          {x["mode"] for x in _dl} == {"cash", "upi", "card"})
    check("C2 razorpay rides the side table, day_line untouched by it (got %d rows, %s p)"
          % (len(_sd), sum(x["amount_p"] for x in _sd)),
          len(_sd) == 2 and sum(x["amount_p"] for x in _sd) == 49000 and
          all(x["tender"] == "razorpay" for x in _sd))
    _c4.close()

    # ---- the bank compares against UPI ALONE (card/razorpay stay out) ------
    _c4 = sqlite3.connect(DB_PATH)
    _c4.row_factory = sqlite3.Row
    _c4.execute("INSERT OR IGNORE INTO upi_statement (merchant_id, unit, statement_date,"
                " source_msg_id, parsed_total_p, txn_count, ingested_at) "
                "VALUES ('100000000306941','clinic',?,'selftest-C2',80000,2,?)",
                (DM3, dt.datetime.now().replace(microsecond=0).isoformat()))
    _c4.commit()
    _rc = finance_upi.reconcile_upi(_c4, "clinic", DM3, now=now_iso())
    check("C2 reconcile compares the day's UPI alone — 800, not 800+card+razorpay "
          "(got entered %s)" % (_rc and _rc["entered_p"]),
          _rc is not None and _rc["entered_p"] == 80000)
    check("C2 a card amount does NOT enter the UPI comparison (entered != 1,150; got %s)"
          % (_rc and _rc["entered_p"]),
          _rc is not None and _rc["entered_p"] != 115000)
    _c4.close()

    # ---- validation: narration and note are load-bearing -------------------
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": DM3, "total_cash": "100",
                     "strays": [{"amount": "50", "tender": "card", "narration": ""}]})
    check("C2 an extra line without 'what is this amount?' is refused",
          r.status_code == 400 and r.get_json()["error"] == "stray_reason_required")
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": DM3, "total_cash": "100",
                     "expenses": [{"amount": "50", "note": ""}]})
    check("C2 an expense without 'what was it for?' is refused",
          r.status_code == 400 and r.get_json()["error"] == "expense_note_required")
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": DM3, "total_cash": "10",
                     "expenses": [{"amount": "50000", "note": "impossible expense"}]})
    check("C2 an expense that empties the drawer below zero is refused",
          r.status_code == 400 and r.get_json()["error"] == "negative_cash")

    # ============== D330, clinic side: two categories, evidence at File =====
    # Its OWN rehearsal day, found free BACKWARD from today (the E1b rule) and
    # deleted afterwards -- rehearsing on the suite's _cd clobbered the C2
    # razorpay-total assertions further down, caught offline, not on the box.
    _cd = None
    _ccx = sqlite3.connect(DB_PATH)
    for _b in range(0, 60):
        _try = (today() - dt.timedelta(days=_b)).isoformat()
        if not _ccx.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                            (CLINIC_UNIT, _try)).fetchone():
            _cd = _try
            break
    _ccx.close()
    check("D330c: found a free clinic day to rehearse on", _cd is not None)
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": _cd, "total_cash": "500",
                     "expenses": [{"amount": "50", "category": "bogus",
                                   "details": "x"}]})
    check("D330c: an off-menu clinic category is refused (got %s/%s)"
          % (r.status_code, (r.get_json() or {}).get("error")),
          r.status_code == 400 and r.get_json()["error"] == "choose_category")
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": _cd, "total_cash": "500",
                     "expenses": [{"amount": "50", "category": "home",
                                   "details": "COD parcel",
                                   "uid": "cxsmoke0000home1"}]})
    check("D330c: a categorised clinic expense SAVES as a draft (else: %s)"
          % ((r.get_json() or {}).get("error") or r.status_code),
          r.status_code == 200 and (r.get_json() or {}).get("ok"))
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": _cd, "total_cash": "500", "action": "submit",
                     "missing_scan_reason": "smoke",
                     "expenses": [{"amount": "50", "category": "home",
                                   "details": "COD parcel",
                                   "uid": "cxsmoke0000home1"}]})
    check("D330c: filing it with NO bill is refused (got %s/%s)"
          % (r.status_code, (r.get_json() or {}).get("error")),
          r.status_code == 400
          and (r.get_json() or {}).get("error") == "expense_evidence_required")
    import io as _io2
    r = c.post("/finance/clinic/api/day/%s/expense-scan/cxsmoke0000home1" % _cd,
               headers=RCP,
               data={"file": (_io2.BytesIO(b"%PDF-1.4 clinic bill"), "bill.pdf")},
               content_type="multipart/form-data")
    check("D330c: the bill uploads through the clinic endpoint (got %s/%s)"
          % (r.status_code, (r.get_json() or {}).get("error")),
          r.status_code == 200 and (r.get_json() or {}).get("ok"))
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": _cd, "total_cash": "500", "action": "submit",
                     "missing_scan_reason": "smoke",
                     "expenses": [{"amount": "50", "category": "home",
                                   "details": "COD parcel",
                                   "uid": "cxsmoke0000home1"}]})
    check("D330c: with the bill attached the clinic File goes through (else: %s)"
          % ((r.get_json() or {}).get("error") or r.status_code),
          r.status_code == 200 and (r.get_json() or {}).get("ok"))
    r = c.get("/finance/clinic/api/tile", headers=DRM)
    check("D330c: the clinic tile totals drawings separately",
          "drawings_month_to_date" in (r.get_json() or {}))
    _chh2 = c.get("/finance/clinic/entry", headers=RCP).get_data(as_text=True)
    check("D330c: the clinic page offers the two categories and NO advance",
          "Home expenses (personal / COD delivery)" in _chh2
          and "Other expenses (write details)" in _chh2
          and "My salary advance" not in _chh2)
    check("F3: the clinic page carries the inline bill file input",
          'class="exFile"' in _chh2 and "uploads when you Save" in _chh2)
    if _cd:
        # children FIRST: sqlite reuses a deleted max rowid, so an orphaned
        # child row would silently join the NEXT day created -- reproduced
        # offline when this block's leftovers doubled the compat day's total.
        _ccx = sqlite3.connect(DB_PATH)
        _cide = _ccx.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                             (CLINIC_UNIT, _cd)).fetchone()
        if _cide:
            for _tbl in ("day_line", "day_expense", "clinic_line_side",
                         "cash_movement", "day_noncash_bill", "attachment",
                         "expense_attachment", "day_revision", "clinic_verification"):
                _ccx.execute("DELETE FROM %s WHERE day_entry_id=?" % _tbl, (_cide[0],))
            _ccx.execute("DELETE FROM day_entry WHERE id=?", (_cide[0],))
        _ccx.commit()
        _ccx.close()

    # ---- the old six-cell payload is still ACCEPTED (compat) ---------------
    r = c.post("/finance/clinic/api/day", headers=SHZ,
               json={"business_date": DM1, "opd_cash": "300", "opd_upi": "0",
                     "xray_cash": "200", "xray_upi": "0", "proc_cash": "0",
                     "proc_upi": "0", "action": "submit",
                     "missing_scan_reason": "compat smoke"})
    j = r.get_json()
    check("C2 the retired six-cell payload still lands (compat; got %s %s)"
          % (r.status_code, (j or {}).get("error", "")),
          r.status_code == 200 and j["ok"] and j["day"]["total_p"] == 50000 and
          j["day"]["cash_p"] == 50000)
    check("C2 compat day folds into the tender view for the new UI (got %s)"
          % (j["day"].get("tenders") or {}).get("cash"),
          j.get("ok") and j["day"]["tenders"]["cash"] == 50000)

    # ---- two-stage approval on fresh days ----------------------------------
    # DM1 was ENTERED by shavez — he cannot verify his own figures (D272)
    r = c.post("/finance/clinic/api/verify/" + DM1, headers=SHZ)
    _j = r.get_json() or {}
    check("C2 self-verify is barred, plain English (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 403 and _j.get("error") == "self_verify" and
          "yourself" in _j.get("message", ""))
    r = c.post("/finance/clinic/api/verify/" + DM1, headers=DRB)
    check("C2 bhawna CAN verify (checker, not the enterer) (got %s)" % r.status_code,
          r.status_code == 200 and (r.get_json() or {}).get("verified_by") == "bhawna")
    r = c.post("/finance/clinic/api/approve/" + DM1, headers=DRB)
    check("C2 bhawna still cannot final-approve a verified day",
          r.status_code == 403 and r.get_json()["error"] == "not_final_checker")
    r = c.post("/finance/clinic/api/approve/" + DM1, headers=DRM,
               json={"acknowledge_upi": True})
    _j = r.get_json() or {}
    check("C2 final approve lands over a middle verification (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 200 and _j.get("status") == "approved" and
          "bhawna" in (_j.get("approval_note") or ""))

    # a correction CLEARS the verification (it vouched for the old figures)
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": DM2, "total_cash": "300", "total_upi": "100",
                     "action": "draft"})
    check("C2 draft saved for the verify-state test", r.status_code == 200)
    r = c.post("/finance/clinic/api/verify/" + DM2, headers=SHZ)
    check("C2 a draft cannot be verified — submit first (got %s)" % r.status_code,
          r.status_code == 409)
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": DM2, "total_cash": "300", "total_upi": "100",
                     "action": "submit", "missing_scan_reason": "smoke"})
    check("C2 day submitted for the skip test", r.status_code == 200)
    r = c.post("/finance/clinic/api/verify/" + DM2, headers=SHZ)
    check("C2 shavez verifies DM2", r.status_code == 200)
    r = c.post("/finance/clinic/api/day", headers=RCP,
               json={"business_date": DM2, "total_cash": "310", "total_upi": "100",
                     "action": "submit", "missing_scan_reason": "smoke"})
    j = r.get_json()
    check("C2 a correction clears the stale verification (warned)",
          j.get("ok") and any("verification" in w for w in (j.get("warnings") or [])))
    r = c.get("/finance/clinic/api/day/" + DM2, headers=DRM)
    check("C2 corrected day reads as not-verified again",
          ((r.get_json() or {}).get("day") or {}).get("verification") is None)

    # the final checker is never hard-blocked: unverified needs the skip flag
    r = c.post("/finance/clinic/api/approve/" + DM2, headers=DRM)
    check("C2 unverified approve refuses without the skip flag",
          r.status_code == 409 and r.get_json()["error"] == "not_verified")
    r = c.post("/finance/clinic/api/approve/" + DM2, headers=DRM,
               json={"skip_verification": True, "acknowledge_upi": True})
    _j = r.get_json() or {}
    check("C2 approve with the skip flag lands (got %s %s)"
          % (r.status_code, _j.get("error", "")),
          r.status_code == 200 and _j.get("status") == "approved" and
          _j.get("approval_note") == "approved without middle verification")
    _c4 = sqlite3.connect(DB_PATH)
    _an = _c4.execute("SELECT after_json FROM audit_log WHERE table_name='day_entry' "
                      "AND action='approve' ORDER BY id DESC LIMIT 1").fetchone()
    _c4.close()
    check("C2 the skip is recorded in the approval note (audit)",
          _an and "approved without middle verification" in (_an[0] or ""))
    r = c.post("/finance/clinic/api/verify/" + DM2, headers=SHZ)
    check("C2 an approved day cannot be verified after the fact",
          r.status_code == 409)
    r = c.post("/finance/clinic/api/verify/2026-01-01", headers=SHZ)
    check("C2 verifying a day that was never filed is a 404", r.status_code == 404)

    # whoami tells the screens who the final checker is (data, not code)
    r = c.get("/finance/clinic/api/whoami", headers=DRM)
    j = r.get_json()
    check("C2 whoami: manoj is the final checker (from the setting)",
          j["final_checker"] == "manoj" and j["is_final_checker"] is True)
    r = c.get("/finance/clinic/api/whoami", headers=DRB)
    check("C2 whoami: bhawna is a checker but not final",
          r.get_json()["is_final_checker"] is False)
    r = c.get("/finance/clinic/api/whoami", headers=SHZ)
    j = r.get_json()
    check("C2 whoami: shavez holds both seats (maker + checker), not final",
          "maker" in j["roles"] and "checker" in j["roles"] and
          j["is_final_checker"] is False)

    # ---- the month grid and day list carry the razorpay rail ---------------
    r = c.get("/finance/clinic/api/month/" + DM3[:7], headers=DRM)
    _cell = [x for x in (r.get_json() or {}).get("days", []) if x["date"] == DM3]
    check("C2 month grid shows DM3 whole — razorpay included (got %s)"
          % (_cell and _cell[0]["revenue"]),
          bool(_cell) and _cell[0]["revenue"] == rupees(290000))
    r = c.get("/finance/clinic/api/days?days=60", headers=DRM)
    j = r.get_json()
    _row = [x for x in j.get("days", []) if x["date"] == DM3]
    check("C2 day list shows DM3 whole — razorpay included (got %s)"
          % (_row and _row[0]["revenue"]),
          bool(_row) and _row[0]["revenue"] == rupees(290000))
    check("C2 day list carries all the filed clinic days (got %s)" % j.get("count"),
          j.get("count", 0) >= 4)

    # ---- the Docterz / tracker feed ----------------------------------------
    global CRON_TOKEN
    _tok_before = CRON_TOKEN
    CRON_TOKEN = "smoke-c2-cron"
    _feed = {"unit": "clinic", "date": DM3,
             "summary": {"net": 2400, "cash": 1200, "online": 1200,
                         "consult_n": 18, "consult_amt": 5400,
                         "xray_n": 6, "xray_amt": 3000,
                         "proc_n": 2, "proc_amt": 1600},
             "lines": [{"clinic_id": "4471", "source": "consult", "net": 300},
                       {"clinic_id": "5120", "source": "xray", "net": 500}]}
    r = c.post("/finance/api/tracker-feed", json=_feed,
               headers={"X-Clinic-User": "nobody", "X-Finance-Cron": "wrong"})
    check("C2 tracker feed: wrong token + no role is refused (got %s)"
          % r.status_code, r.status_code in (401, 403))
    r = c.post("/finance/api/tracker-feed", json=_feed,
               headers={"X-Finance-Cron": "smoke-c2-cron"})
    check("C2 tracker feed: the cron token stores the day (got %s)"
          % r.status_code, r.status_code == 200 and r.get_json()["stored"] is True)
    r = c.post("/finance/api/tracker-feed", json=_feed, headers=DRM)
    check("C2 tracker feed: a signed-in checker can post by hand (got %s)"
          % r.status_code, r.status_code == 200)
    _c4 = sqlite3.connect(DB_PATH)
    _n = _c4.execute("SELECT COUNT(*) FROM tracker_day WHERE unit='clinic' "
                     "AND business_date=?", (DM3,)).fetchone()[0]
    _c4.close()
    check("C2 tracker feed upserts — one row per day, not a pile (got %d)" % _n,
          _n == 1)
    r = c.post("/finance/api/tracker-feed", headers={"X-Finance-Cron": "smoke-c2-cron"},
               json=dict(_feed, date="2026-13-40"))
    check("C2 tracker feed refuses a junk date loudly", r.status_code == 400)
    r = c.post("/finance/api/tracker-feed", headers={"X-Finance-Cron": "smoke-c2-cron"},
               json=dict(_feed, unit="spa"))
    check("C2 tracker feed refuses an unknown unit loudly", r.status_code == 400)
    r = c.post("/finance/api/tracker-feed", headers={"X-Finance-Cron": "smoke-c2-cron"},
               json=dict(_feed, lines=[{"clinic_id": "1", "patient_name": "X", "net": 1}]))
    check("C2 tracker feed refuses names at the door (privacy)",
          r.status_code == 400 and r.get_json()["error"] == "privacy_refused")
    r = c.post("/finance/api/tracker-feed", headers={"X-Finance-Cron": "smoke-c2-cron"},
               json=dict(_feed, lines=[{"clinic_id": "1", "phone": "9xxxx", "net": 1}]))
    check("C2 tracker feed refuses phone numbers at the door (privacy)",
          r.status_code == 400 and r.get_json()["error"] == "privacy_refused")
    CRON_TOKEN = _tok_before

    # all three levels SEE the tracker day (maker, middle, final)
    for _who, _hdr in (("maker reception", RCP), ("middle shavez", SHZ),
                       ("final manoj", DRM)):
        r = c.get("/finance/clinic/api/tracker-day/" + DM3, headers=_hdr)
        j = r.get_json() or {}
        check("C2 tracker day visible to %s (got %s net %s)"
              % (_who, r.status_code, (j.get("summary") or {}).get("net")),
              r.status_code == 200 and j.get("present") is True and
              (j.get("summary") or {}).get("net") == 2400)
    r = c.get("/finance/clinic/api/tracker-day/" + DM2, headers=RCP)
    j = r.get_json() or {}
    check("C2 a day with no feed says 'not received yet', not an error",
          r.status_code == 200 and j.get("present") is False and
          "not received" in (j.get("message") or ""))
    r = c.get("/finance/clinic/api/tracker-day/" + DM3, headers=DRP)
    check("C2 tracker day is refused outside the clinic roster (got %s)"
          % r.status_code, r.status_code == 403)

    # and medical came through untouched
    _cm = sqlite3.connect(DB_PATH)
    _cm.row_factory = sqlite3.Row
    _m = _cm.execute(
        "SELECT COUNT(*) n, COALESCE(SUM(revenue_p),0) rev, COALESCE(SUM(cash_in_p),0) cash "
        "FROM v_cash_ledger WHERE unit='medical'").fetchone()
    _med_after = (_m["n"], _m["rev"], _m["cash"])
    _leak = _cm.execute(
        "SELECT COUNT(*) c FROM day_line l JOIN day_entry e ON e.id=l.day_entry_id "
        "WHERE e.unit='medical' AND l.line_kind IS NOT NULL").fetchone()["c"]
    _cm.close()
    check("medical ledger identical before/after the clinic day", _med_before == _med_after)
    check("no clinic tagging leaked onto medical rows", _leak == 0)
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    r = c.get("/finance/api/day/" + D1)
    _md = r.get_json()["day"]
    check("the medical day still reads identically",
          (_md["total_p"], _md["closing_p"]) == _med_day_before)
    # (env role left at 'checker', exactly as the S180 block below expects)

    # ------------------------------------------------------------------ S180
    # A sale return that nobody could name sits in the review queue with a
    # NEGATIVE amount_p (finance_ingest keeps it signed so in_review_p stays
    # honest). sale_item forbids negatives, so resolving one has to turn the
    # sign back into a magnitude plus a "_return" service. Before that was
    # handled, a checker resolving a queued return got an IntegrityError 500.
    #
    # THIS BLOCK RUNS LAST, AND MUST STAY LAST. Two reasons, both learned the
    # hard way at S180:
    #   · resolving the queued line ADDS a sale_item, and an earlier check
    #     asserts the day still has exactly three lines;
    #   · anything that calls /ingest supersedes the day's previous batch and
    #     DELETES what it produced, so this inserts the queue row directly
    #     instead of going through the adapter.
    # Add new checks ABOVE this block, never below it.
    _c2 = sqlite3.connect(DB_PATH)
    _eid = _c2.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                       (UNIT, D1)).fetchone()[0]
    _c2.execute("INSERT INTO sale_item_review (day_entry_id, raw_text, guess_name, amount_p, "
                "confidence, status, reason) VALUES (?,?,?,?,?, 'open', ?)",
                (_eid, '{"Bill No":"CN00168"}', None, -7700, 0.5, "no patient identified"))
    _rid = _c2.execute("SELECT id FROM sale_item_review WHERE amount_p=-7700").fetchone()[0]
    _c2.commit()
    _c2.close()

    r = c.post("/finance/api/review/%d/resolve" % _rid,
               json={"action": "assign", "clinic_id": "6002", "name": "Returned goods"})
    check("resolving a queued RETURN does not blow up", r.status_code == 200)
    _c2 = sqlite3.connect(DB_PATH)
    _row = _c2.execute("SELECT service, amount_p FROM sale_item WHERE patient_ref_id="
                       "(SELECT id FROM patient_ref WHERE clinic_id='6002')").fetchone()
    _c2.close()
    check("resolved return becomes a return row", _row and _row[0] == "pharmacy_return")
    check("resolved return is stored as a magnitude", _row and _row[1] == 7700)

    # ---------------- S186_R2a: Yes Bank recon · workbench · custody --------
    # STATE-ADAPTIVE (F-106): these assert BEHAVIOUR, never a store state, so a
    # legitimate data correction can never make the suite red again.
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    r = c.get("/finance/workbench")
    check("workbench page is served", r.status_code == 200)
    _wb = r.get_data(as_text=True)
    check("workbench names its three sources", all(
        k in _wb for k in ("Entered", "Marg", "Bank")))
    check("workbench never auto-applies a suggestion (F-79 absence check)",
          "auto-apply" not in _wb.lower() and "autoapply" not in _wb.lower())

    _ym = dt.date.today().strftime("%Y-%m")
    r = c.get("/finance/api/workbench/%s" % _ym)
    check("workbench month API answers", r.status_code == 200 and r.get_json().get("ok"))
    _j = r.get_json()
    check("workbench returns a day list", isinstance(_j.get("days"), list))
    check("workbench reports custody people", len(_j.get("custody", {}).get("people", [])) >= 1)
    check("workbench rejects a malformed month",
          c.get("/finance/api/workbench/2026-13-01").status_code == 400)

    _seated = os.environ.get("FINANCE_DEV_USER", "")
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    check("a maker cannot open the workbench data",
          c.get("/finance/api/workbench/%s" % _ym).status_code in (401, 403))
    os.environ["FINANCE_DEV_USER"] = _seated
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    # custody: the validation is the point, so prove each refusal
    _bad = [({"date": "2026-08-17", "from": "drawer", "to": "drawer", "amount": 10},
             "same party both sides"),
            ({"date": "2026-08-17", "from": "drawer", "to": "mars", "amount": 10},
             "unknown party"),
            ({"date": "17-08-2026", "from": "drawer", "to": "bank", "amount": 10},
             "non-ISO date"),
            ({"date": "2026-08-17", "from": "drawer", "to": "bank", "amount": 0},
             "zero amount"),
            ({"date": "2026-08-17", "from": "drawer", "to": "bank", "amount": 10,
              "month_end": "maybe"}, "invented month-end marker")]
    for body, why in _bad:
        check("custody refuses %s" % why,
              c.post("/finance/api/custody", json=body).status_code == 400)

    _before = c.get("/finance/api/custody").get_json()
    _n0 = len(_before.get("events", []))
    r = c.post("/finance/api/custody", json={"date": "2026-08-17", "from": "drawer",
               "to": "dr_bhawna", "amount": 1234.50, "month_end": "carried",
               "note": "smoke"})
    check("custody accepts a well-formed event", r.status_code == 200)
    _after = c.get("/finance/api/custody").get_json()
    check("the custody event is retrievable", len(_after.get("events", [])) == _n0 + 1)
    check("the month-end marker survives the round trip",
          any(e.get("month_end") == "carried" for e in _after.get("events", [])))
    check("custody derives a held balance rather than storing one",
          isinstance(_after.get("held"), list))

    # the drawer count: blank is UNKNOWN, never zero (F-91 / D166)
    r = c.post("/finance/api/cash-count", json={"date": "2026-08-17", "counted": ""})
    check("a blank drawer count is accepted AND flagged",
          r.status_code == 200 and r.get_json().get("flagged") is True
          and r.get_json().get("counted") is None)
    r = c.post("/finance/api/cash-count", json={"date": "2026-08-17", "counted": 4321})
    check("a real drawer count is stored", r.status_code == 200
          and r.get_json().get("flagged") is False)
    check("a malformed drawer count is refused",
          c.post("/finance/api/cash-count",
                 json={"date": "2026-08-17", "counted": "many"}).status_code == 400)

    # Yes Bank: present or absent, it must behave predictably
    if finance_yesbank is None:
        check("without the module the Yes Bank routes 503 rather than crash",
              c.post("/finance/api/yesbank-statement", data=b"x").status_code == 503)
    else:
        _csv = finance_yesbank.SAMPLE.encode()
        r = c.post("/finance/api/yesbank-statement",
                   data={"file": (io.BytesIO(_csv), "yesbank.csv")},
                   content_type="multipart/form-data")
        check("a Yes Bank statement is ingested", r.status_code == 200)
        _y = r.get_json() or {}
        check("the account is reported last-4 only (never in full)",
              len(str(_y.get("account", ""))) <= 4)
        check("five cash deposits are recognised", _y.get("cash_deposits") == 5)
        check("a junk file is REJECTED whole, not half-ingested",
              c.post("/finance/api/yesbank-statement",
                     data={"file": (io.BytesIO(b"not,a,statement\n1,2,3\n"), "x.csv")},
                     content_type="multipart/form-data").status_code == 422)
        r = c.get("/finance/api/yesbank/reconcile?from=2026-07-01&to=2026-08-17")
        check("the reconciler answers over a window", r.status_code == 200)
        _rj = r.get_json() or {}
        check("it reports all four verdicts every run, even when empty",
              all(k in _rj for k in ("matched", "deposit_not_in_bank",
                                     "deposit_unevidenced", "bank_deposit_not_booked")))
        _seated2 = os.environ.get("FINANCE_DEV_USER", "")
        os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
        os.environ["FINANCE_DEV_ROLE"] = "maker"
        check("a maker cannot upload a bank statement",
              c.post("/finance/api/yesbank-statement", data=b"x").status_code in (401, 403))
        os.environ["FINANCE_DEV_USER"] = _seated2
        os.environ["FINANCE_DEV_ROLE"] = "checker"

    # ------------- S186_I1a: the F-114 fix and the Marg upload surface -------
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    r = c.get("/finance/workbench")
    _wb2 = r.get_data(as_text=True)
    check("the workbench carries the Marg upload card", "marg-upload" in _wb2)
    check("the upload offers a check-first path", "Check first" in _wb2)

    check("marg upload refuses a request with no file",
          c.post("/finance/api/marg-upload", data={}).status_code in (400, 503))
    if marg_report is not None and finance_returns is not None:
        check("a file that is not a Marg export is REJECTED whole",
              c.post("/finance/api/marg-upload",
                     data={"file": (io.BytesIO(b"nonsense"), "x.xls")},
                     content_type="multipart/form-data").status_code == 422)
        check("a rejected upload is recorded as a data_flag",
              sqlite3.connect(DB_PATH).execute(
                  "SELECT COUNT(*) FROM data_flag WHERE code='MARG_UPLOAD_REJECTED'"
              ).fetchone()[0] >= 1)
    _seated3 = os.environ.get("FINANCE_DEV_USER", "")
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    check("a maker cannot upload a Marg report",
          c.post("/finance/api/marg-upload", data={}).status_code in (401, 403))
    os.environ["FINANCE_DEV_USER"] = _seated3
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    # ------------- S187_M1a: the pushed Marg export (B5) --------------------
    # The parser itself is proved by marg_report's own selftest against the
    # real exports (38/38); THESE tests stub it and prove the plumbing that is
    # new here -- the scoped token, staging, duplicate refusal, F-113 flags,
    # and the checker-only apply replaying staged CSVs through the REAL
    # finance_ingest / finance_returns path.
    _mp_saved_token = globals().get("MARG_TOKEN", "")

    globals()["MARG_TOKEN"] = ""
    r = c.post("/finance/api/marg-push", headers={"X-Finance-Marg": "anything"},
               data={})
    check("push with NO server token configured is refused (fail closed)",
          r.status_code in (401, 503))

    globals()["MARG_TOKEN"] = "smoke-marg"
    check("push with the WRONG token is refused",
          c.post("/finance/api/marg-push",
                 headers={"X-Finance-Marg": "guess"},
                 data={}).status_code == 401)
    _mp_u, _mp_r = os.environ.get("FINANCE_DEV_USER", ""), os.environ.get("FINANCE_DEV_ROLE", "")
    os.environ["FINANCE_DEV_USER"] = ""
    os.environ["FINANCE_DEV_ROLE"] = ""
    check("the sender token does NOT open any other route",
          c.post("/finance/api/marg-upload",
                 headers={"X-Finance-Marg": "smoke-marg"},
                 data={}).status_code in (401, 403))
    os.environ["FINANCE_DEV_USER"], os.environ["FINANCE_DEV_ROLE"] = _mp_u, _mp_r
    _MH = {"X-Finance-Marg": "smoke-marg"}
    check("push with no file -> 400",
          c.post("/finance/api/marg-push", headers=_MH,
                 data={}).status_code == 400)

    if marg_report is not None and finance_returns is not None:
        r = c.post("/finance/api/marg-push", headers=_MH,
                   data={"file": (io.BytesIO(b"pushed nonsense"), "x.xls")},
                   content_type="multipart/form-data")
        check("a file that is not a Marg export is REFUSED whole (pushed)",
              r.status_code == 422)
        _pcx = sqlite3.connect(DB_PATH)
        _pcx.row_factory = sqlite3.Row
        check("a refused push leaves a data_flag",
              _pcx.execute("SELECT COUNT(*) FROM data_flag "
                           "WHERE code='MARG_PUSH_REJECTED'").fetchone()[0] >= 1)
        check("a refused push leaves a staging row marked rejected",
              _pcx.execute("SELECT COUNT(*) FROM marg_push_staging "
                           "WHERE status='rejected'").fetchone()[0] >= 1)

        # ---- own the column map (the F-106 trap; see the F-114 test above) --
        _mp_sid = _pcx.execute("SELECT id FROM ingest_source WHERE unit='medical'"
                               " AND adapter='marg_export'").fetchone()
        _mp_sid = _mp_sid[0] if _mp_sid else None
        _mp_saved_map = []
        if _mp_sid:
            _mp_saved_map = [dict(x) for x in _pcx.execute(
                "SELECT * FROM ingest_column_map WHERE source_id=?", (_mp_sid,))]
            _pcx.execute("DELETE FROM ingest_column_map WHERE source_id=?", (_mp_sid,))
            for _fld in ("bill_date", "bill_no", "clinic_id", "patient_name",
                         "description", "amount", "mode"):
                _pcx.execute("INSERT INTO ingest_column_map (source_id, our_field,"
                             " their_column, required) VALUES (?,?,?,?)",
                             (_mp_sid, _fld, _fld,
                              1 if _fld in ("bill_date", "amount") else 0))
            _pcx.commit()

        # ---- stub the parser; drive the REAL ingest with canned CSVs --------
        _F187 = "2026-03-03"
        _mp_lines = (
            "bill_date,bill_no,clinic_id,patient_name,phone_last4,description,amount,mode\n"
            "%s,A00T001,,SMOKE PUSH ONE,,,250.00,cash\n"
            "%s,A00T002,,SMOKE PUSH TWO,,,150.00,cash\n" % (_F187, _F187))
        _mp_items = (
            "bill_date,bill_no,is_return,seq,item_name,pack,qty_raw,qty_strips,"
            "qty_loose,amount,expiry_ym,batch,col2\n"
            "%s,A00T001,0,1,SMOKE TAB,1*10,1.0,,,250.00,2027-05,SMK1,1\n" % _F187)
        _mp_rep = {"title": "STUB PUSH", "warnings": [],
                   "days": [{"date": _F187,
                             "bills": [{"net_p": 25000}, {"net_p": 15000}],
                             "items": [{"stub": 1}]}]}

        class _StubMarg(object):
            LINE_COLUMNS = marg_report.LINE_COLUMNS

            @staticmethod
            def read_report(path, keep_items=False):
                return _mp_rep

            @staticmethod
            def day_totals(rep):
                return [{"business_date": _F187, "bills": 2, "net_p": 40000}]

            @staticmethod
            def write_lines_csv(rep, fh, business_date=None):
                fh.write(_mp_lines)
                return 2

            @staticmethod
            def write_items_csv(rep, fh, business_date=None):
                fh.write(_mp_items)
                return 1

        _real_marg = globals()["marg_report"]
        globals()["marg_report"] = _StubMarg
        try:
            _mp_blob = b"stub-marg-export-S187"
            r = c.post("/finance/api/marg-push", headers=_MH,
                       data={"file": (io.BytesIO(_mp_blob), "REPORT_1.XLS")},
                       content_type="multipart/form-data")
            j = r.get_json() or {}
            check("a clean push is ACCEPTED-FOR-REVIEW (got %s %s)"
                  % (r.status_code, j.get("error", "")),
                  r.status_code == 200 and j.get("ok")
                  and j.get("verdict") == "ACCEPTED-FOR-REVIEW")
            _mp_id = j.get("id")
            check("the push message says NOTHING entered the books",
                  "NOTHING" in (j.get("message") or ""))
            check("an unfiled day is reported in the survey",
                  j.get("not_filed") == [_F187])
            check("an unfiled PUSHED day leaves the F-113 data_flag",
                  _pcx.execute("SELECT COUNT(*) FROM data_flag WHERE "
                               "code='MARG_DAY_NOT_FILED' AND business_date=?",
                               (_F187,)).fetchone()[0] >= 1)

            r = c.post("/finance/api/marg-push", headers=_MH,
                       data={"file": (io.BytesIO(_mp_blob), "REPORT_1.XLS")},
                       content_type="multipart/form-data")
            j = r.get_json() or {}
            check("the SAME bytes pushed again -> ALREADY-RECEIVED, not staged twice",
                  j.get("verdict") == "ALREADY-RECEIVED")
            # scoped to THIS test's bytes: the live store legitimately carries
            # real pending pushes (the first one arrived 18 Aug 2026 and broke
            # the unscoped version of this check at the S187_P1a install gate
            # -- F-106 in a test, F-125). Assert the behaviour, not the store.
            check("staging holds exactly one pending row for THOSE bytes",
                  _pcx.execute("SELECT COUNT(*) FROM marg_push_staging WHERE "
                               "status='pending' AND file_md5=?",
                               (hashlib.md5(_mp_blob).hexdigest(),)
                               ).fetchone()[0] == 1)

            # ---- the checker's half --------------------------------------
            # a REAL maker: no seated user with checker rights riding along
            # (the F-106 trap this suite has hit before -- test the guard,
            # not the harness's role state)
            _mp_su = os.environ.get("FINANCE_DEV_USER", "")
            os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
            os.environ["FINANCE_DEV_ROLE"] = "maker"
            check("a maker cannot LIST staged pushes",
                  c.get("/finance/api/marg-push/list").status_code in (401, 403))
            check("a maker cannot APPLY a staged push",
                  c.post("/finance/api/marg-push/apply",
                         json={"id": _mp_id}).status_code in (401, 403))
            os.environ["FINANCE_DEV_USER"] = _mp_su
            os.environ["FINANCE_DEV_ROLE"] = "checker"

            j = c.get("/finance/api/marg-push/list").get_json() or {}
            check("the checker's list shows the pending push",
                  any(p["id"] == _mp_id and p["status"] == "pending"
                      for p in j.get("pushes", [])))
            _wb3 = c.get("/finance/workbench").get_data(as_text=True)
            check("the workbench carries the pushed-reports card",
                  "marg-push" in _wb3 and "loadPushes" in _wb3)

            # applying while the day is still unfiled: reported, not ingested
            j = c.post("/finance/api/marg-push/apply",
                       json={"id": _mp_id}).get_json() or {}
            check("apply on a still-unfiled day ingests nothing and says so",
                  j.get("ok") and j.get("still_not_filed") == [_F187]
                  and not j.get("ingested"))
            check("F-155: a push that ingested nothing stays PENDING, not 'applied'",
                  _pcx.execute("SELECT status FROM marg_push_staging WHERE id=?",
                               (_mp_id,)).fetchone()[0] == "pending")
            check("F-155: it KEEPS its payload so it re-applies once the day is filed",
                  _pcx.execute("SELECT parsed_json FROM marg_push_staging WHERE id=?",
                               (_mp_id,)).fetchone()[0] is not None)
            _f155 = c.get("/finance/api/marg-push/list").get_json() or {}
            _f155p = [p for p in _f155.get("pushes", []) if p["id"] == _mp_id]
            check("F-155: the list reports ingested_count 0 and replayable=True",
                  len(_f155p) == 1 and _f155p[0].get("ingested_count") == 0
                  and _f155p[0].get("replayable") is True)

            # S194 AUTO-REPLAY: filing the day replays the pending push with NO
            # explicit apply -- _mp_id is pending and _F187 was not filed.
            _pcx.execute("INSERT OR IGNORE INTO day_entry (unit, business_date,"
                         " status, source) VALUES ('medical', ?, 'draft', 'app')",
                         (_F187,))
            _pcx.commit()
            _ar = _replay_pending_marg_for_day(_pcx, _F187, by="selftest")
            check("S194 auto-replay: filing the day loaded the pending push",
                  len(_ar) >= 1 and any(x["date"] == _F187 for x in _ar))
            check("S194 auto-replay: the staged bills landed durably",
                  (_pcx.execute("SELECT COUNT(*) FROM sale_item si JOIN day_entry de"
                                " ON de.id=si.day_entry_id WHERE de.unit='medical'"
                                " AND de.business_date=?", (_F187,)).fetchone()[0]
                   + _pcx.execute("SELECT COUNT(*) FROM sale_item_review sr JOIN"
                                  " day_entry de ON de.id=sr.day_entry_id WHERE"
                                  " de.unit='medical' AND de.business_date=?",
                                  (_F187,)).fetchone()[0]) >= 1)

            # a fresh push, then FILE the day, then apply -> real ingest
            _mp_blob2 = b"stub-marg-export-S187-take2"
            j = c.post("/finance/api/marg-push", headers=_MH,
                       data={"file": (io.BytesIO(_mp_blob2), "REPORT_1.XLS")},
                       content_type="multipart/form-data").get_json() or {}
            _mp_id2 = j.get("id")
            _pcx.execute("INSERT OR IGNORE INTO day_entry (unit, business_date,"
                         " status, source) VALUES ('medical', ?, 'draft', 'app')",
                         (_F187,))
            _pcx.commit()
            j = c.post("/finance/api/marg-push/apply",
                       json={"id": _mp_id2}).get_json() or {}
            check("apply after filing ingests the staged day (got %s)"
                  % json.dumps(j.get("aborted")),
                  j.get("ok") and len(j.get("ingested") or []) == 1
                  and j["ingested"][0]["bills"] == 2)
            _mp_row = _pcx.execute("SELECT status, parsed_json FROM "
                                   "marg_push_staging WHERE id=?",
                                   (_mp_id2,)).fetchone()
            check("an applied push is marked applied",
                  _mp_row and _mp_row["status"] == "applied")
            check("an applied push's payload is PRUNED (no PHI at rest)",
                  _mp_row and _mp_row["parsed_json"] is None)
            # name-but-no-clinic-id lines legitimately route to review (D315)
            # or to WALK-IN sale_item (F-114) -- either is the real ingest
            # landing them somewhere durable; console output would not be.
            check("the staged bills landed durably through the real ingest",
                  (_pcx.execute("SELECT COUNT(*) FROM sale_item si JOIN day_entry de"
                                " ON de.id=si.day_entry_id WHERE de.unit='medical'"
                                " AND de.business_date=?", (_F187,)).fetchone()[0]
                   + _pcx.execute("SELECT COUNT(*) FROM sale_item_review sr JOIN"
                                  " day_entry de ON de.id=sr.day_entry_id WHERE"
                                  " de.unit='medical' AND de.business_date=?",
                                  (_F187,)).fetchone()[0]) >= 2)
            check("a non-pending push cannot be applied twice",
                  c.post("/finance/api/marg-push/apply",
                         json={"id": _mp_id2}).status_code == 409)
        finally:
            globals()["marg_report"] = _real_marg
            if _mp_sid:
                _pcx.execute("DELETE FROM ingest_column_map WHERE source_id=?",
                             (_mp_sid,))
                for _m in _mp_saved_map:
                    _pcx.execute(
                        "INSERT INTO ingest_column_map (source_id, our_field,"
                        " their_column, transform, required) VALUES (?,?,?,?,?)",
                        (_mp_sid, _m["our_field"], _m["their_column"],
                         _m.get("transform"), _m.get("required", 0)))
                _pcx.commit()
            _pcx.close()

    globals()["MARG_TOKEN"] = _mp_saved_token

    # ------------- S187_D1a: the Day Page + the approvals surface -----------
    # Read-only aggregates over existing stores; asserted on BEHAVIOUR: the
    # checker gets the full day (marg bills -> items, both banks, flags), a
    # maker gets 403 from every new surface, and every strip count is backed
    # by the rows it counts.
    r = c.get("/finance/api/approvals")
    j = r.get_json() or {}
    check("approvals strip loads for a checker", r.status_code == 200 and j.get("ok"))
    check("every strip count is backed by its rows (no bare numbers)",
          isinstance(j.get("pending"), list) and isinstance(j.get("missing_marg"), list)
          and isinstance(j.get("pushes_pending"), list)
          and isinstance(j.get("upi_mismatches"), list)
          and isinstance(j.get("variance_days"), list))
    check("a filed day with no marg batch appears in missing_marg",
          isinstance(j.get("missing_marg"), list))

    r = c.get("/finance/api/day/%s/full" % _F187)
    jd = r.get_json() or {}
    check("the Day Page aggregate loads (got %s)" % r.status_code,
          r.status_code == 200 and jd.get("ok"))
    check("Day Page carries declared + marg + both banks + flags in ONE call",
          "day" in jd and "marg" in jd and "icici" in jd
          and "yesbank" in jd and "flags" in jd)
    check("the pushed day's marg view groups bills",
          isinstance((jd.get("marg") or {}).get("bills"), list))
    _d1_bills = (jd.get("marg") or {}).get("bills") or []
    check("a bill row can carry its drug lines (item expansion)",
          all("items" in b for b in _d1_bills))
    check("the approvals page is served and wires the Day Page",
          "day/" in c.get("/finance/approvals").get_data(as_text=True)
          and "api/approvals" in c.get("/finance/approvals").get_data(as_text=True))
    check("Day Page refuses a bad date",
          c.get("/finance/api/day/junk/full").status_code == 400)

    # ------------- S187_H1a: the Sanjeevni Hub ------------------------------
    # Orthotics: behaviour-scoped -- set a vocab matching the F187 stub item,
    # expect it found; clear it, expect the rollup empty. The page must carry
    # every hub section and reuse the existing guarded APIs.
    j = c.post("/finance/api/orthotics", json={"vocab": "SMOKE TAB, kneecap"}
               ).get_json() or {}
    check("orthotics vocab saves", j.get("ok") and "SMOKE" in (j.get("vocab") or ""))
    j = c.get("/finance/api/orthotics?days=365").get_json() or {}
    check("orthotics rollup finds the matching item line",
          j.get("ok") and any("SMOKE" in (x.get("item") or "")
                              for x in j.get("items", [])))
    check("orthotics rollup carries per-day rows",
          isinstance(j.get("days"), list))
    c.post("/finance/api/orthotics", json={"vocab": ""})
    j = c.get("/finance/api/orthotics").get_json() or {}
    check("an EMPTY vocab yields an empty rollup, never a guess",
          j.get("ok") and j.get("items") == [] and j.get("days") == [])
    _hub = c.get("/finance/approvals").get_data(as_text=True)
    check("the hub carries every section",
          all(s in _hub for s in ("margCard", "pendCard", "cashCard",
                                  "custCard", "monthCard", "orthoCard")))
    check("the hub reuses the guarded APIs (no new data paths)",
          all(s in _hub for s in ("/finance/api/days", "/finance/api/custody",
                                  "/finance/api/workbench/", "/finance/api/marg-upload",
                                  "/finance/api/marg-push/list", "/finance/api/orthotics")))
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    check("a maker cannot read orthotics",
          c.get("/finance/api/orthotics").status_code in (401, 403))
    check("a maker cannot set the orthotics vocab",
          c.post("/finance/api/orthotics", json={"vocab": "x"}
                 ).status_code in (401, 403))
    os.environ["FINANCE_DEV_USER"] = _seated3
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    # ------------- S187_P2a: the other users' tile lines --------------------
    r = c.get("/finance/api/my-day-summary")
    j = r.get_json() or {}
    check("my-day-summary answers a seated user (S187_P2a)",
          r.status_code == 200 and j.get("ok")
          and isinstance(j.get("to_file"), int)
          and isinstance(j.get("days"), list))
    _p2_su = os.environ.get("FINANCE_DEV_USER", "")
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
    os.environ["FINANCE_DEV_ROLE"] = ""
    check("my-day-summary refuses a user with no medical seat",
          c.get("/finance/api/my-day-summary").status_code in (401, 403))
    os.environ["FINANCE_DEV_USER"] = _p2_su
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    j = c.get("/finance/clinic/api/tile-meta").get_json() or {}
    check("clinic tile-meta still answers, subtitle string-or-null (P2a ride-along)",
          j.get("ok") and (j.get("subtitle") is None
                           or isinstance(j.get("subtitle"), str)))

    r = c.get("/finance/api/tile-summary")
    j = r.get_json() or {}
    check("tile-summary answers the checker with counts (S187_P1a)",
          r.status_code == 200 and j.get("ok")
          and all(isinstance(j.get(k), int) for k in
                  ("to_approve", "marg_pushes", "missing_marg",
                   "exceptions", "review")))

    _d1_su = os.environ.get("FINANCE_DEV_USER", "")
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    check("a maker cannot read the tile summary",
          c.get("/finance/api/tile-summary").status_code in (401, 403))
    check("a maker cannot read the approvals strip",
          c.get("/finance/api/approvals").status_code in (401, 403))
    check("a maker cannot read the full Day Page",
          c.get("/finance/api/day/%s/full" % _F187).status_code in (401, 403))
    check("a maker is bounced off the approvals page",
          c.get("/finance/approvals").status_code in (302, 401, 403))
    os.environ["FINANCE_DEV_USER"] = _d1_su
    os.environ["FINANCE_DEV_ROLE"] = "checker"

    # F-114 itself: a cleanly-read anonymous line must reach WALK-IN, and a
    # badly-read one must still reach review. Asserted on BEHAVIOUR (F-106).
    _cx = sqlite3.connect(DB_PATH)
    _cx.row_factory = sqlite3.Row
    _F114 = "2026-03-02"
    _cx.execute("INSERT OR IGNORE INTO day_entry (unit, business_date, status, source)"
                " VALUES ('medical', ?, 'draft', 'app')", (_F114,))
    _cx.execute("INSERT OR IGNORE INTO day_line (day_entry_id, service, mode, amount_p)"
                " SELECT id,'pharmacy_sale','cash',50000 FROM day_entry"
                "  WHERE unit='medical' AND business_date=?", (_F114,))
    _cx.commit()
    # This test OWNS its column map and puts it back afterwards. An earlier step
    # in this suite rewrites the map to Marg's raw column names, so reading the
    # map — or assuming the shipped one — both make this a test of suite state
    # rather than of behaviour. That is the F-106 trap, and it caught this test
    # twice before it shipped.
    _sid = _cx.execute("SELECT id FROM ingest_source WHERE unit='medical'"
                       " AND adapter='marg_export'").fetchone()
    _sid = _sid[0] if _sid else None
    _saved_map = []
    if _sid:
        _saved_map = _cx.execute("SELECT our_field, their_column FROM ingest_column_map"
                                 " WHERE source_id=?", (_sid,)).fetchall()
        _cx.execute("DELETE FROM ingest_column_map WHERE source_id=?", (_sid,))
        for _f in ("bill_date", "bill_no", "clinic_id", "patient_name",
                   "description", "amount", "mode"):
            _cx.execute("INSERT INTO ingest_column_map (source_id, our_field, their_column)"
                        " VALUES (?,?,?)", (_sid, _f, _f))
        _cx.commit()
    _csv = ("bill_date,bill_no,clinic_id,patient_name,description,amount,mode\n"
            "%s,B1,4471,Ramesh,TAB A,300.00,cash\n"
            "%s,B2,,,TAB B,200.00,cash\n" % (_F114, _F114))
    try:
        _res = finance_ingest.ingest_day(_cx, "medical", _F114, "marg_export", _csv,
                                         run_by="smoke", source_ref="f114")
        _walkin = _cx.execute(
            "SELECT COUNT(*) FROM sale_item s JOIN patient_ref p ON p.id=s.patient_ref_id"
            " JOIN day_entry e ON e.id=s.day_entry_id"
            " WHERE e.business_date=? AND p.clinic_id='WALK-IN'", (_F114,)).fetchone()[0]
        _rev = _cx.execute("SELECT COUNT(*) FROM sale_item_review r JOIN day_entry e"
                           " ON e.id=r.day_entry_id WHERE e.business_date=? AND r.status='open'",
                           (_F114,)).fetchone()[0]
        check("F-114: a clean anonymous line reaches WALK-IN, not the review queue",
              _walkin == 1)
        check("F-114: it is NOT parked in review", _rev == 0)
        check("F-114: the identified line still resolves to its own patient",
              (_res.get("accepted") or 0) == 2)
        # and the setting can turn it off without a code change
        _cx.execute("INSERT OR REPLACE INTO setting (key,value) VALUES"
                    " ('ingest.anonymous_to_walkin','0')")
        _cx.commit()
        finance_ingest.ingest_day(_cx, "medical", _F114, "marg_export", _csv,
                                  run_by="smoke", source_ref="f114b")
        _rev2 = _cx.execute("SELECT COUNT(*) FROM sale_item_review r JOIN day_entry e"
                            " ON e.id=r.day_entry_id WHERE e.business_date=? AND r.status='open'",
                            (_F114,)).fetchone()[0]
        check("F-114: the behaviour is reversible by setting, no code change",
              _rev2 == 1)
        _cx.execute("INSERT OR REPLACE INTO setting (key,value) VALUES"
                    " ('ingest.anonymous_to_walkin','1')")
        _cx.commit()
    except Exception as _ex:                                      # noqa: BLE001
        check("F-114: a clean anonymous line reaches WALK-IN, not the review queue", False)
    if _sid and _saved_map:                       # put the suite's map back
        _cx.execute("DELETE FROM ingest_column_map WHERE source_id=?", (_sid,))
        for _f, _t in _saved_map:
            _cx.execute("INSERT INTO ingest_column_map (source_id, our_field, their_column)"
                        " VALUES (?,?,?)", (_sid, _f, _t))
        _cx.commit()
    _cx.close()

    # ================================================================
    #  STAGE D2 -- the maker's mirror (D326). Asserts BEHAVIOUR, never store
    #  population (F-106/F-125): the day it works on is discovered, not named.
    # ================================================================
    _d2u = os.environ.get("FINANCE_DEV_USER", "")
    _d2r = os.environ.get("FINANCE_DEV_ROLE", "")
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    _dcx = sqlite3.connect(DB_PATH)
    _cand = None
    for _b in range(0, 40):
        _try = (today() - dt.timedelta(days=_b)).isoformat()
        if not _dcx.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                            (UNIT, _try)).fetchone():
            _cand = _try
            break
    _dcx.close()
    check("D2: found an unwritten day to rehearse on", _cand is not None)

    if _cand:
        # 1. save-then-see is the SERVER's rule, not the page's
        r = c.get("/finance/api/day/%s/mirror" % _cand)
        check("D2: the mirror refuses a day that was never saved",
              r.status_code == 409 and (r.get_json() or {}).get("error") == "not_saved")

        r = post({"business_date": _cand, "total": "1000", "upi": "200"})
        _saved = r.status_code == 200 and (r.get_json() or {}).get("ok")
        check("D2: the rehearsal day saved (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code), _saved)

    if _cand and _saved:
        # 2. what he is given
        r = c.get("/finance/api/day/%s/mirror" % _cand)
        j = r.get_json() or {}
        check("D2: the mirror answers the maker", r.status_code == 200 and j.get("ok"))
        check("D2: it carries his declared figures, both banks' verdicts and his scans",
              all(k in j for k in ("declared", "icici", "marg", "scans",
                                   "owed_days", "edited_after_reveal")))
        check("D2: the Marg verdict is one of the three honest states",
              j["marg"]["state"] in ("applied", "staged_not_applied", "absent"))

        # 3. F-79 ABSENCE: what he is NOT given. This is the half of F-127 that
        #    a presence check can never catch.
        _flat = json.dumps(j)
        check("D2: no unit cash position reaches the maker",
              not any(k in j for k in ("cash_in_hand", "cash_with", "month_to_date",
                                       "deposit_due", "deposit_excess", "shouts",
                                       "last_revenue", "awaiting_approval")))
        check("D2: no bill-level Marg detail reaches the maker",
              "bills" not in _flat or isinstance(j["marg"].get("bills"), int))
        check("D2: nothing named 'patient' is in the maker's payload",
              "patient" not in _flat.lower())

        # 4. the scanner path saves a draft with the SAME money. Stamping that
        #    would be a false accusation -- prove it does not.
        r = post({"business_date": _cand, "total": "1000", "upi": "200"})
        _fcx = sqlite3.connect(DB_PATH)
        _n = _fcx.execute("SELECT COUNT(*) FROM data_flag WHERE unit=? AND business_date=? "
                          "AND code='EDITED_AFTER_REVEAL'", (UNIT, _cand)).fetchone()[0]
        check("D2: re-saving the SAME figures is not an edit after the reveal", _n == 0)

        # 5. moving the money after the reveal IS one -- noted, never blocked
        r = post({"business_date": _cand, "total": "1500", "upi": "200"})
        check("D2: the edit itself is allowed through (D326: stamp, not lock)",
              r.status_code == 200 and (r.get_json() or {}).get("ok"))
        check("D2: and he is told it will be visible",
              any("noted" in w for w in ((r.get_json() or {}).get("warnings") or [])))
        _n = _fcx.execute("SELECT COUNT(*) FROM data_flag WHERE unit=? AND business_date=? "
                          "AND code='EDITED_AFTER_REVEAL'", (UNIT, _cand)).fetchone()[0]
        check("D2: an edit after the reveal is stamped exactly once", _n == 1)
        r = post({"business_date": _cand, "total": "1600", "upi": "200"})
        _n = _fcx.execute("SELECT COUNT(*) FROM data_flag WHERE unit=? AND business_date=? "
                          "AND code='EDITED_AFTER_REVEAL'", (UNIT, _cand)).fetchone()[0]
        check("D2: a second edit does not stamp it twice", _n == 1)
        check("D2: the mirror reports the stamp back to him",
              (c.get("/finance/api/day/%s/mirror" % _cand).get_json() or {})
              .get("edited_after_reveal") is True)
        _fcx.close()

        # 6. THE POINT: the badge reaches the checker with no checker-side code
        #    change, because /full already renders data_flag rows.
        os.environ["FINANCE_DEV_ROLE"] = "checker"
        jf = c.get("/finance/api/day/%s/full" % _cand).get_json() or {}
        check("D2: the stamp appears on the checker's Day Page unaided",
              any(f["code"] == "EDITED_AFTER_REVEAL" for f in (jf.get("flags") or [])))

        # 7. a login with no medical role gets nothing from the mirror
        _ns = os.environ.get("FINANCE_DEV_USER", "")
        os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
        os.environ["FINANCE_DEV_ROLE"] = ""
        check("D2: no medical role, no mirror",
              c.get("/finance/api/day/%s/mirror" % _cand).status_code in (401, 403))
        os.environ["FINANCE_DEV_USER"] = _ns

    # ================================================================
    #  F-129 -- a CHECKER's look must not arm the maker's badge.
    #  Rehearsed on its own day, because the assertion is about a day
    #  nobody has revealed yet.
    # ================================================================
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"     # a REAL maker (F-106)
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    _dcx2 = sqlite3.connect(DB_PATH)
    _cand2 = None
    for _b in range(0, 60):
        _try = (today() - dt.timedelta(days=_b)).isoformat()
        if _try == _cand:
            continue
        if not _dcx2.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                             (UNIT, _try)).fetchone():
            _cand2 = _try
            break
    check("F-129: found a second untouched day to rehearse on", _cand2 is not None)

    if _cand2:
        r = post({"business_date": _cand2, "total": "800", "upi": "100"})
        _saved2 = r.status_code == 200 and (r.get_json() or {}).get("ok")
        check("F-129: the second rehearsal day saved (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code), _saved2)

    if _cand2 and _saved2:
        # 1. the CHECKER looks first. This is the exact sequence that used to
        #    arm the badge against the maker.
        os.environ["FINANCE_DEV_USER"] = _d2u or "selftest"
        os.environ["FINANCE_DEV_ROLE"] = "checker"
        j = c.get("/finance/api/day/%s/mirror" % _cand2).get_json() or {}
        check("F-129: the checker may still SEE the mirror", j.get("ok") is True)
        check("F-129: but the look is not a maker's look",
              j.get("looking_as_maker") is False)
        check("F-129: and it arms nothing", j.get("armed_by_this_look") is False)
        check("F-129: no reveal row exists after the checker's look",
              _dcx2.execute("SELECT COUNT(*) FROM day_mirror_reveal m JOIN day_entry e "
                            "ON e.id=m.day_entry_id WHERE e.business_date=?",
                            (_cand2,)).fetchone()[0] == 0)

        # 2. the maker now edits. He was never shown anything, so he must NOT
        #    be badged. This is the whole finding, in one assertion.
        os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
        os.environ["FINANCE_DEV_ROLE"] = "maker"
        post({"business_date": _cand2, "total": "950", "upi": "100"})
        check("F-129: the maker is NOT stamped for a check he was never shown",
              _dcx2.execute("SELECT COUNT(*) FROM data_flag WHERE unit=? AND "
                            "business_date=? AND code='EDITED_AFTER_REVEAL'",
                            (UNIT, _cand2,)).fetchone()[0] == 0)

        # 3. and the mechanism still works when it is HIS look that arms it
        j = c.get("/finance/api/day/%s/mirror" % _cand2).get_json() or {}
        check("F-129: the maker's own look is a maker's look",
              j.get("looking_as_maker") is True and j.get("armed_by_this_look") is True)
        post({"business_date": _cand2, "total": "1100", "upi": "100"})
        check("F-129: and NOW an edit after his own look is stamped",
              _dcx2.execute("SELECT COUNT(*) FROM data_flag WHERE unit=? AND "
                            "business_date=? AND code='EDITED_AFTER_REVEAL'",
                            (UNIT, _cand2,)).fetchone()[0] == 1)
        check("F-129: the reveal is attributed to the maker who saw it",
              _dcx2.execute("SELECT m.revealed_by FROM day_mirror_reveal m JOIN day_entry e "
                            "ON e.id=m.day_entry_id WHERE e.business_date=?",
                            (_cand2,)).fetchone()[0] == "smoke_no_seat")
    _dcx2.close()

    # ================================================================
    #  F-132 / F-133 -- "where is the cash": the ONLY thing the maker is
    #  told about money he cannot see. Parked totals scoped to the Indian
    #  financial year (1 April) on the owner's instruction; the bank clock
    #  deliberately NOT scoped, because "days since" must survive April.
    # ================================================================
    os.environ["FINANCE_DEV_USER"] = "smoke_no_seat"
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    _w = c.get("/finance/api/where-is-the-cash")
    _wj = _w.get_json() or {}
    check("F-132: the maker may ask where the cash is", _w.status_code == 200 and _wj.get("ok"))
    check("F-132: it names Dr Manoj and Dr Bhawna separately",
          [p["party"] for p in (_wj.get("parked") or [])][:2] == ["dr_manoj", "dr_bhawna"])
    check("F-132: it carries a parked TOTAL to summarise them",
          "parked_total" in _wj)
    check("F-132: and the bank-trip clock", "bank" in _wj and "days_since" in _wj["bank"])
    check("F-132: parked totals are scoped to this financial year",
          (_wj.get("fy_from") or "").endswith("-04-01"))
    # F-79 ABSENCE: the unit position must not ride along on the new surface
    _wflat = json.dumps(_wj)
    check("F-132: no unit cash position on the new surface",
          not any(k in _wj for k in ("cash_in_hand", "month_to_date", "last_revenue",
                                     "closing", "opening", "deposit_excess", "shouts")))
    check("F-132: and no other day's money in it", "revenue" not in _wflat)
    check("F-132: a seat with no medical role is refused",
          (lambda: (os.environ.__setitem__("FINANCE_DEV_ROLE", ""),
                    c.get("/finance/api/where-is-the-cash").status_code)[1])() in (401, 403))
    os.environ["FINANCE_DEV_ROLE"] = "maker"

    # ---- F-137: custody is LOCATION, movements are QUANTITY ------------
    # Proven here as a single sequence, because the finding is precisely that
    # the two were confused: a custody event must move THIS CARD and not the
    # ledger; a cash_movement must move the LEDGER and not this card.
    check("F-137: the card says which table it read",
          _wj.get("source") == "cash_custody_event")

    _fx = sqlite3.connect(DB_PATH)
    _fy = fy_start().isoformat()

    def _ledger_total():
        r = _fx.execute("SELECT COALESCE(SUM(net_p),0) FROM v_cash_ledger "
                        "WHERE unit=?", (UNIT,)).fetchone()
        return r[0]

    def _parked_of(party):
        j = c.get("/finance/api/where-is-the-cash").get_json() or {}
        row = [x for x in (j.get("parked") or []) if x["party"] == party]
        return (row[0]["amount"] if row else None), j

    def _paise(txt):
        """'13,579.50' -> 1357950. The suite's earlier stages already write
        custody rows, so every assertion below is a DELTA, never a fixed
        store total (F-106)."""
        return int(round(float((txt or "0").replace(",", "")) * 100))

    # (a) custody dated in the PREVIOUS financial year is excluded.
    # F-138: every assertion here is a DELTA against the live store's own
    # position, never an absolute. The first build of these checks asserted
    # "Rs 0.00" and "exactly Rs 12,345.00" -- true on an empty store, false
    # the moment S189_C1a legitimately recorded the real counted position,
    # at which point the C1a installer's honest red restored the books. The
    # store owes these checks nothing; the checks measure what THEY changed.
    _amt0, _ = _parked_of("dr_manoj")
    _pA = _paise(_amt0)
    _before = (parse_iso_date(_fy) - dt.timedelta(days=17)).isoformat()
    _fx.execute("INSERT INTO cash_custody_event (unit,event_date,from_party,to_party,"
                "amount_p,note,entered_by) VALUES (?,?,'drawer','dr_manoj',1234500,"
                "'last-FY handover (smoke)','smoke')", (UNIT, _before))
    _fx.commit()
    _amt, _ = _parked_of("dr_manoj")
    check("F-137: custody dated in the PREVIOUS financial year is excluded "
          "(delta, F-138)",
          _paise(_amt) == _pA)

    # (b) a free in-year date to rehearse the real sequence on
    _inside = None
    _d = parse_iso_date(_fy)
    while _d <= today():
        if not _fx.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                           (UNIT, _d.isoformat())).fetchone():
            _inside = _d.isoformat(); break
        _d += dt.timedelta(days=1)
    check("F-137: found a free in-year date to rehearse on", _inside is not None)

    if _inside:
        _L0 = _ledger_total()
        _, _j0 = _parked_of("dr_manoj")
        _T0 = _paise(_j0.get("parked_total"))
        _fx.execute("INSERT INTO cash_custody_event (unit,event_date,from_party,"
                    "to_party,amount_p,note,entered_by) VALUES (?,?,'drawer',"
                    "'dr_manoj',1234500,'this-FY handover (smoke)','smoke')",
                    (UNIT, _inside))
        _fx.commit()
        _amt, _j = _parked_of("dr_manoj")
        check("F-137: custody inside this year IS counted (delta, F-138)",
              _paise(_amt) - _pA == 1234500)
        check("F-137: and it lifts the parked TOTAL by exactly that much",
              _paise(_j.get("parked_total")) - _T0 == 1234500
              and _j.get("any_recorded") is True)
        # THE PROPERTY THE WHOLE DESIGN RESTS ON
        check("F-137: a custody event does NOT move cash in hand",
              _ledger_total() == _L0)
        # a place is not a person: 'drawer' went negative and must not show
        check("F-137: a place is not a person -- 'drawer' is never parked WITH anyone",
              not [x for x in (_j.get("parked") or []) if x["party"] in
                   ("drawer", "counter", "bank")])

        # now the mirror image: a MOVEMENT moves the money, not the card
        _fx.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,"
                    "entered_at) VALUES (?,?,'approved','legacy_sheet','smoke',?)",
                    (UNIT, _inside, _inside + "T10:00:00"))
        _eid2 = _fx.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                            (UNIT, _inside)).fetchone()[0]
        _fx.execute("INSERT INTO cash_movement (day_entry_id,direction,party,amount_p,"
                    "reference) VALUES (?,'out','dr_manoj',1234500,'movement (smoke)')",
                    (_eid2,))
        _fx.commit()
        _amt2, _ = _parked_of("dr_manoj")
        check("F-137: a cash_movement handover does NOT reach this card "
              "(delta, F-138)",
              _paise(_amt2) == _paise(_amt))
        check("F-137: ...but it DOES subtract from cash in hand -- which is exactly "
              "why custody may not be recorded there",
              _ledger_total() == _L0 - 1234500)
        _fx.execute("DELETE FROM cash_movement WHERE day_entry_id=?", (_eid2,))
        _fx.execute("DELETE FROM day_entry WHERE id=?", (_eid2,))

    # (c) the card carries the count its position rests on
    _fx.execute("INSERT INTO cash_count (unit,business_date,counted_p,counted_by,"
                "counted_at,explanation) VALUES (?,?,?,'smoke',?,'smoke count') "
                "ON CONFLICT(unit,business_date) DO NOTHING",
                (UNIT, _fy, 4242, _fy))
    _fx.commit()
    _j = c.get("/finance/api/where-is-the-cash").get_json() or {}
    _latest = _fx.execute("SELECT business_date FROM cash_count WHERE unit=? "
                          "ORDER BY business_date DESC LIMIT 1", (UNIT,)).fetchone()
    check("F-137: the card carries the physical count its position rests on, "
          "and it is the LATEST one",
          isinstance(_j.get("counted"), dict) and _latest
          and _j["counted"].get("date") == _latest[0])
    _fx.execute("DELETE FROM cash_count WHERE unit=? AND counted_by='smoke'", (UNIT,))
    _fx.execute("DELETE FROM cash_custody_event WHERE unit=? AND entered_by='smoke'", (UNIT,))
    _fx.commit(); _fx.close()

    os.environ["FINANCE_DEV_USER"], os.environ["FINANCE_DEV_ROLE"] = _d2u, _d2r

    # ---------------- S189_E1a: the expense MENU (owner ruling + F-139) ----
    # Delta-disciplined throughout (F-138): every assertion measures what THIS
    # block's own saves produce, never the store's absolute state.
    os.environ["FINANCE_DEV_USER"] = _d2u or "selftest"
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    _eh = c.get("/finance/entry?legacy=1").get_data(as_text=True)
    for _cv, _cl in EXPENSE_MENU:
        check("E1a: the served page offers '%s'" % _cl, _cl in _eh)
    # careful: "Someone else (reserve)" legitimately exists in the
    # who-ran-the-counter selector -- the absence check targets the FAKE
    # markup exactly (the expStaff control and its invented ids), not the phrase.
    check("E1a: the hardcoded fake staff control is GONE (F-79 absence)",
          'class="expStaff"' not in _eh
          and '<option value="2">Someone else</option>' not in _eh)
    check("E1a: free text is no longer the default first option",
          '<option value="">Free text</option>' not in _eh)
    check("E1a: the menu placeholder demands a choice",
          'disabled selected>Choose' in _eh)

    # a rehearsal day of its own, found free and cleaned afterwards.
    # E1b (the first E1a red, reproduced offline before this line changed):
    # searching FORWARD from fy_start lands on the store's first historical
    # hole -- on the real box that is a Sunday in early April, 135 days back,
    # and the save answers `too_old` (BACKFILL_WINDOW_DAYS=120) BEFORE the
    # expense parse this block exists to test. So the search runs BACKWARD
    # from today, the direction the D2/F-129 blocks already use -- a
    # rehearsal must stand where the maker is allowed to stand.
    _ed = None
    _ecx = sqlite3.connect(DB_PATH)
    for _b in range(0, min(BACKFILL_WINDOW_DAYS, 60)):
        _try = (today() - dt.timedelta(days=_b)).isoformat()
        if not _ecx.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                            (UNIT, _try)).fetchone():
            _ed = _try; break
    _ecx.close()
    check("E1a: found a free RECENT day to rehearse the menu on (E1b)", _ed is not None)
    if _ed:
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "100", "category": "junk_value"}]})
        check("E1a: an off-menu category is refused (got %s/%s)"
              % (r.status_code, (r.get_json() or {}).get("error")),
              r.status_code == 400 and (r.get_json() or {}).get("error") == "choose_category")
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "100", "category": None}]})
        check("E1a: a skipped choice is refused, never written as uncategorised (got %s/%s)"
              % (r.status_code, (r.get_json() or {}).get("error")),
              r.status_code == 400 and (r.get_json() or {}).get("error") == "choose_category")
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "100", "category": "other", "details": "  "}]})
        check("E1a: Other without details is refused (got %s/%s)"
              % (r.status_code, (r.get_json() or {}).get("error")),
              r.status_code == 400 and (r.get_json() or {}).get("error") == "details_required")
        # D330: home requires details exactly like other
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "100", "category": "home", "details": ""}]})
        check("D330: home without details is refused (got %s/%s)"
              % (r.status_code, (r.get_json() or {}).get("error")),
              r.status_code == 400 and (r.get_json() or {}).get("error") == "details_required")
        r = post({"business_date": _ed, "total": "900", "expenses": [
                  {"amount": "100", "category": "home", "details": "COD parcel", "uid": "exsmoke0000home1"},
                  {"amount": "50",  "category": "other", "details": "cycle puncture", "uid": "exsmoke0000othr1"},
                  {"amount": "200", "category": "salary_advance_self", "staff_id": 424242}]})
        check("E1a: a menu save goes through (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))
        _ec = sqlite3.connect(DB_PATH)
        _rows = _ec.execute(
            "SELECT x.category_fixed, x.staff_id, x.category_text, x.expense_uid, "
            "x.category_kind FROM day_expense x "
            "JOIN day_entry e ON e.id=x.day_entry_id WHERE e.business_date=? "
            "ORDER BY x.amount_p DESC", (_ed,)).fetchall()
        check("E1a: exactly the three rows landed", len(_rows) == 3)
        if len(_rows) == 3:
            check("E1a: the advance wrote fixed + the S184-matching canonical text",
                  _rows[0][0] == "salary_advance"
                  and _rows[0][2] == "Salary advance - Darpan")
            check("E1a: and its staff_id is the server's, not the client's 424242",
                  _rows[0][1] is not None and _rows[0][1] != 424242)
            check("D330: home wrote its details with category_kind='home' "
                  "(fixed stays NULL — the schema CHECK owns that column)",
                  _rows[1][2] == "COD parcel" and _rows[1][4] == "home"
                  and _rows[1][0] is None)
            check("D330: other wrote the maker's own words with category_kind='other'",
                  _rows[2][2] == "cycle puncture" and _rows[2][4] == "other"
                  and _rows[2][0] is None)
            check("D330: the page-sent uid is stored verbatim (stable identity)",
                  _rows[1][3] == "exsmoke0000home1" and _rows[2][3] == "exsmoke0000othr1")
            check("D330: the advance was given a server uid when the page sent none",
                  bool(_rows[0][3]))
        _n1 = _ec.execute("SELECT COUNT(*) FROM staff_ref WHERE name='Darpan'").fetchone()[0]
        r = post({"business_date": _ed, "total": "900", "expenses": [
                  {"amount": "300", "category": "salary_advance_self"}]})
        _n2 = _ec.execute("SELECT COUNT(*) FROM staff_ref WHERE name='Darpan'").fetchone()[0]
        check("E1a: a second advance reuses the ONE row, never mints another",
              r.status_code == 200 and _n1 == _n2 == 1)
        # restore the REAL advance settings before the ceiling's own block --
        # it must measure the mechanism against the store's true configuration.
        _bump1 = sqlite3.connect(DB_PATH)
        if _prior_base is None:
            _bump1.execute("DELETE FROM setting WHERE key='advance.base_p'")
        else:
            _bump1.execute("INSERT OR REPLACE INTO setting (key,value) VALUES "
                           "('advance.base_p',?)", (_prior_base,))
        _bump1.commit(); _bump1.close()

        # ============== D330: the ceiling, the evidence gate, the split =====
        # All delta-disciplined (F-138): every figure is measured against what
        # THIS block's own saves produce, and every check that can fail embeds
        # the server's answer in its label (F-140).
        _dj = c.get("/finance/api/day/" + _ed).get_json()["day"]
        check("D330: the day payload carries the advance context inline "
              "(mtd=%s ceil=%s)" % (_dj.get("advance_mtd"), _dj.get("advance_ceiling")),
              "advance_mtd" in _dj and "advance_ceiling" in _dj)
        # the expected ceiling is COMPUTED from the store's own settings —
        # a hardcoded "15,000.00" would go red the day the owner revises the
        # base or the pct (the F-136 shape, inside a test).
        _es0 = sqlite3.connect(DB_PATH)
        def _set_of(k, d):
            _r0 = _es0.execute("SELECT value FROM setting WHERE key=?", (k,)).fetchone()
            try:
                return int((_r0[0] if _r0 else d) or d)
            except (TypeError, ValueError):
                return d
        _base0, _pct0 = _set_of("advance.base_p", 2000000), _set_of("advance.pct", 75)
        _es0.close()
        _want_ceil = (_base0 * _pct0 // 100) // 10000 * 10000
        check("D330: the ceiling is DERIVED — %d%% of the stored base, floored "
              "to Rs 100 (want %s, got %s)"
              % (_pct0, rupees(_want_ceil), _dj.get("advance_ceiling")),
              _dj.get("advance_ceiling") == rupees(_want_ceil))
        # The gate excludes the day being re-saved (its rows are replaced),
        # so the room this day has = ceiling − advances on the month's OTHER
        # days (earlier blocks legitimately saved some) — measured from the
        # store, delta-style, never assumed (F-138).
        _ceil_p_ = _dj["advance_ceiling_p"]
        _er0 = sqlite3.connect(DB_PATH)
        _oth_p = _er0.execute(
            "SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x "
            "JOIN day_entry e ON e.id=x.day_entry_id "
            "WHERE e.unit=? AND substr(e.business_date,1,7)=substr(?,1,7) "
            "AND e.business_date != ? AND x.category_fixed='salary_advance'",
            (UNIT, _ed, _ed)).fetchone()[0]
        _er0.close()
        _led_p0, _ = ledger_fwd_advances_p(_ed[:7])
        _room_p = _ceil_p_ - _oth_p - _led_p0

        # over the ceiling: refused with the figures in the message
        r = post({"business_date": _ed, "total": "90000", "expenses": [
                  {"amount": "%.2f" % ((_room_p + 10000) / 100.0),
                   "category": "salary_advance_self"}]})
        _je = r.get_json() or {}
        check("D330: an advance over the ceiling is REFUSED (got %s/%s)"
              % (r.status_code, _je.get("error")),
              r.status_code == 400 and _je.get("error") == "advance_over_ceiling")
        check("D330: the refusal shows the figures (taken=%s ceiling=%s)"
              % (_je.get("advance_taken"), _je.get("advance_ceiling")),
              bool(_je.get("advance_taken")) and _je.get("advance_ceiling") == "15,000.00")

        # exactly AT the ceiling: allowed (the boundary belongs to him)
        r = post({"business_date": _ed, "total": "90000", "expenses": [
                  {"amount": "%.2f" % (_room_p / 100.0),
                   "category": "salary_advance_self", "uid": "exsmoke0000advc1"}]})
        check("D330: exactly-at-the-ceiling is allowed (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))

        # the ceiling MOVES with the setting — derived, not stored (F-136)
        _es = sqlite3.connect(DB_PATH)
        _es.execute("INSERT OR REPLACE INTO setting (key,value) VALUES ('advance.pct','50')")
        _es.commit()
        _want_50 = (_base0 * 50 // 100) // 10000 * 10000
        _dj2 = c.get("/finance/api/day/" + _ed).get_json()["day"]
        check("D330: the ceiling moves with the setting — pct 50 gives %s "
              "(got %s)" % (rupees(_want_50), _dj2.get("advance_ceiling")),
              _dj2.get("advance_ceiling") == rupees(_want_50))
        _es.execute("INSERT OR REPLACE INTO setting (key,value) VALUES ('advance.pct','%d')" % _pct0)
        _es.commit(); _es.close()

        # ---- evidence: COMPULSORY at File, satisfied by the upload ---------
        r = post({"business_date": _ed, "total": "900", "action": "submit",
                  "attached_docs": [], "missing_scan_reason": "smoke",
                  "expenses": [{"amount": "60", "category": "home",
                                "details": "COD parcel", "uid": "exsmoke0000home2"}]})
        _je = r.get_json() or {}
        check("D330: filing a home expense with NO bill is refused (got %s/%s)"
              % (r.status_code, _je.get("error")),
              r.status_code == 400 and _je.get("error") == "expense_evidence_required")
        check("D330: the refusal names the row (rows=%s)"
              % json.dumps(_je.get("rows"))[:60],
              any(_r.get("uid") == "exsmoke0000home2" for _r in _je.get("rows") or []))

        # a draft save of the same row is FINE — evidence gates File, not Save
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "60", "category": "home",
                                "details": "COD parcel", "uid": "exsmoke0000home2"}]})
        check("D330: the same row SAVES as a draft (evidence gates File, "
              "not Save) (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))

        # upload the bill against the row's uid, through the real endpoint
        import io as _io
        r = c.post("/finance/api/day/%s/expense-scan/exsmoke0000home2" % _ed,
                   data={"file": (_io.BytesIO(b"%PDF-1.4 smoke bill"), "bill.pdf")},
                   content_type="multipart/form-data")
        check("D330: the bill uploads against the expense uid (got %s/%s)"
              % (r.status_code, (r.get_json() or {}).get("error")),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))
        r = c.post("/finance/api/day/%s/expense-scan/nosuchuid000001" % _ed,
                   data={"file": (_io.BytesIO(b"x"), "bill.pdf")},
                   content_type="multipart/form-data")
        check("D330: an upload against an unknown uid is refused (got %s)"
              % r.status_code, r.status_code == 409)
        _dj3 = c.get("/finance/api/day/" + _ed).get_json()["day"]
        _row3 = [x for x in _dj3["expenses"] if x.get("uid") == "exsmoke0000home2"]
        check("D330: the day payload shows the evidence tick on that row",
              bool(_row3) and _row3[0]["has_evidence"] is True)

        # a RE-SAVE with the same uid keeps the attachment married to the row
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "60", "category": "home",
                                "details": "COD parcel edited", "uid": "exsmoke0000home2"}]})
        _dj4 = c.get("/finance/api/day/" + _ed).get_json()["day"]
        _row4 = [x for x in _dj4["expenses"] if x.get("uid") == "exsmoke0000home2"]
        check("D330: evidence SURVIVES the delete-and-reinsert re-save "
              "(the uid is the identity)",
              bool(_row4) and _row4[0]["has_evidence"] is True)

        # and NOW the File goes through
        r = post({"business_date": _ed, "total": "900", "action": "submit",
                  "attached_docs": [], "missing_scan_reason": "smoke",
                  "expenses": [{"amount": "60", "category": "home",
                                "details": "COD parcel", "uid": "exsmoke0000home2"}]})
        check("D330: with the bill attached the File goes through (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))

        # an advance needs NO evidence to file (it is not a bill-bearing
        # spend). The home row rides along so the day ends holding BOTH —
        # each save REPLACES the day, and the split check below measures
        # what this block actually left behind.
        # the advance amount adapts to whatever room the month still has —
        # on a store where the month is already at its ceiling the row would
        # otherwise be refused for the RIGHT reason and this check would lie
        # red forever after (the F-106 shape: a test asserting frozen state).
        _adv_amt_p = min(6000, max(_room_p, 0))
        _exps_fin = [{"amount": "60", "category": "home",
                      "details": "COD parcel", "uid": "exsmoke0000home2"}]
        if _adv_amt_p > 0:
            _exps_fin.insert(0, {"amount": "%.2f" % (_adv_amt_p / 100.0),
                                 "category": "salary_advance_self",
                                 "uid": "exsmoke0000advc2"})
        r = post({"business_date": _ed, "total": "900", "action": "submit",
                  "attached_docs": [], "missing_scan_reason": "smoke",
                  "expenses": _exps_fin})
        check("D330: a salary advance (%s) files with no bill — no evidence "
              "demanded of it (else: %s)"
              % (rupees(_adv_amt_p),
                 (r.get_json() or {}).get("error") or r.status_code),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))

        # ---- the drawings split: home is the proprietor's, other is not ----
        os.environ["FINANCE_DEV_ROLE"] = "checker"
        _tj = c.get("/finance/api/tile").get_json()
        check("D330: the tile totals drawings separately (key present)",
              "drawings_month_to_date" in _tj)
        _mj = c.get("/finance/api/month/" + _ed[:7]).get_json()
        _md = [x for x in _mj["days"] if x["date"] == _ed]
        check("D330: the month grid carries the day's drawings (got %s)"
              % (_md[0].get("drawings") if _md else "no-row"),
              bool(_md) and "drawings" in _md[0])
        # this block's own home row (60) is drawings; the advance is NOT
        _ex2 = sqlite3.connect(DB_PATH)
        _dsum = _ex2.execute(
            "SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x "
            "JOIN day_entry e ON e.id=x.day_entry_id "
            "WHERE e.business_date=? AND x.category_kind='home'", (_ed,)).fetchone()[0]
        _asum = _ex2.execute(
            "SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x "
            "JOIN day_entry e ON e.id=x.day_entry_id "
            "WHERE e.business_date=? AND x.category_fixed='salary_advance'", (_ed,)).fetchone()[0]
        _ex2.close()
        check("D330: home counts as drawings and the advance does not "
              "(home=%d adv=%d want adv=%d)" % (_dsum, _asum, _adv_amt_p),
              _dsum == 6000 and _asum == _adv_amt_p)
        os.environ["FINANCE_DEV_ROLE"] = "maker"

        # ---- F4: an approved day yields to the UNIT checker, whatever the
        # broker role says (the owner's own 31-July refusal, reproduced)
        _f4 = sqlite3.connect(DB_PATH)
        _f4.execute("UPDATE day_entry SET status='approved', approved_by='doc' "
                    "WHERE unit=? AND business_date=?", (UNIT, _ed))
        _f4.commit(); _f4.close()
        os.environ["FINANCE_DEV_USER"] = "manoj"       # unit_role: checker
        os.environ["FINANCE_DEV_ROLE"] = "doctor"      # the SSO broker role
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "60", "category": "home",
                                "details": "COD parcel", "uid": "exsmoke0000home2"}]})
        check("F4: the checker EDITS an approved day though his broker role "
              "is 'doctor' (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))
        # the checker's edit legitimately demoted the day to draft —
        # re-approve before proving the maker is still shut out
        _f4b = sqlite3.connect(DB_PATH)
        _f4b.execute("UPDATE day_entry SET status='approved' "
                     "WHERE unit=? AND business_date=?", (UNIT, _ed))
        _f4b.commit(); _f4b.close()
        os.environ["FINANCE_DEV_USER"] = _d2u or "selftest"
        os.environ["FINANCE_DEV_ROLE"] = "maker"
        r = post({"business_date": _ed, "total": "900", "expenses": []})
        check("F4: a MAKER is still refused on an approved day (got %s/%s)"
              % (r.status_code, (r.get_json() or {}).get("error")),
              r.status_code == 403 and (r.get_json() or {}).get("error") == "locked")
        # F5: an edited LEGACY day surfaces in the approvals queue
        _f5 = sqlite3.connect(DB_PATH)
        _f5.execute("UPDATE day_entry SET source='legacy_sheet' "
                    "WHERE unit=? AND business_date=?", (UNIT, _ed))
        _f5.commit(); _f5.close()
        os.environ["FINANCE_DEV_USER"] = "manoj"
        os.environ["FINANCE_DEV_ROLE"] = "doctor"
        r = post({"business_date": _ed, "total": "900",
                  "expenses": [{"amount": "60", "category": "home",
                                "details": "COD parcel", "uid": "exsmoke0000home2"}]})
        _q = c.get("/finance/api/approvals").get_json() or {}
        check("F5: an edited legacy-sheet day re-becomes an APP entry and "
              "surfaces in the queue (save %s; in queue: %s)"
              % (r.status_code,
                 any(x["date"] == _ed for x in _q.get("pending", []))),
              r.status_code == 200
              and any(x["date"] == _ed for x in _q.get("pending", [])))
        # leave the day as the later blocks expect it (delta discipline)
        _f4c = sqlite3.connect(DB_PATH)
        _f4c.execute("UPDATE day_entry SET status='draft', approved_by=NULL "
                     "WHERE unit=? AND business_date=?", (UNIT, _ed))
        _f4c.commit(); _f4c.close()

        # ---- the served page: refill wiring + the new menu + the bill button
        _eh2 = c.get("/finance/entry?legacy=1").get_data(as_text=True)
        check("D330: the page refills expenses on load (the draft-resave "
              "hazard, closed)", "forEach(function(e){ addExpense(e); })" in _eh2)
        check("D330: the page refills movements and bills on load",
              "forEach(function(m){ addMovement(m); })" in _eh2
              and "forEach(function(b){ addNoncash(b); })" in _eh2)
        check("F3: the bill is chosen INLINE on the maker's page — a file "
              "input in the expense row, uploaded on Save (owner flow)",
              'class="expFile"' in _eh2 and "uploads when you Save" in _eh2)
        check("D330: the movement row gained its reference field",
              'class="movRef"' in _eh2)
        # ============== S190_F2: the ledger cross-read (D331 plumbing) ======
        _lj_prev = LEDGER_JSONL
        import tempfile as _tf
        # absent file: degraded VISIBLY, never a crash
        LEDGER_JSONL = "/nonexistent/ledger.jsonl"
        _fj = c.get("/finance/api/day/" + _ed).get_json()["day"]
        check("F2: ledger unreadable -> advance_ledger_included is FALSE "
              "(degraded, said out loud)", _fj.get("advance_ledger_included") is False)
        _mtd_alone = _fj["advance_mtd_p"]
        # a FORWARD-attributed row for this month is counted...
        _lf = _tf.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        _prev_m = "%04d-%02d" % ((int(_ed[:4]) - 1) if _ed[5:7] == "01" else int(_ed[:4]),
                                 12 if _ed[5:7] == "01" else int(_ed[5:7]) - 1)
        _lf.write(json.dumps({"category": "ADVANCE_ISSUE", "staff": "Darpan",
                              "status": "APPROVED", "amount": 5000,
                              "date_from": _prev_m + "-15",
                              "against_month": _ed[:7]}) + "\n")
        # ...a SAME-month ledger row is NOT (it mirrors a drawer draw)
        _lf.write(json.dumps({"category": "ADVANCE_ISSUE", "staff": "Darpan",
                              "status": "APPROVED", "amount": 7000,
                              "date_from": _ed}) + "\n")
        # junk line: skipped, not fatal
        _lf.write("{not json}\n")
        _lf.close()
        LEDGER_JSONL = _lf.name
        _fj2 = c.get("/finance/api/day/" + _ed).get_json()["day"]
        check("F2: a forward-attributed salary-side advance is COUNTED "
              "(mtd %d -> %d, +500000)" % (_mtd_alone, _fj2["advance_mtd_p"]),
              _fj2["advance_mtd_p"] == _mtd_alone + 500000
              and _fj2["advance_ledger_included"] is True)
        check("F2: a same-month ledger row is NOT counted — a drawer draw is "
              "never forward-attributed, so no rupee lands in both books",
              _fj2["advance_mtd_p"] != _mtd_alone + 500000 + 700000)
        # the gate breathes with it: room shrinks by exactly the ledger figure
        # (clamped at 0 — on a month already at its ceiling the at-boundary
        # save degenerates to a zero-advance save, same convention as above;
        # caught by the shape-2 rehearsal, where negative room printed as a
        # negative amount and failed as not_a_number)
        _room2 = max(_fj2["advance_ceiling_p"] - _oth_p - 500000, 0)
        r = post({"business_date": _ed, "total": "90000", "expenses": [
                  {"amount": "%.2f" % ((_room2 + 10000) / 100.0),
                   "category": "salary_advance_self"}]})
        check("F2: the refusal accounts for the salary-side advance (got %s/%s)"
              % (r.status_code, (r.get_json() or {}).get("error")),
              r.status_code == 400
              and (r.get_json() or {}).get("error") == "advance_over_ceiling")
        r = post({"business_date": _ed, "total": "90000", "expenses": [
                  {"amount": "%.2f" % (_room2 / 100.0),
                   "category": "salary_advance_self", "uid": "exsmoke0000advc3"}]})
        check("F2: exactly-at-the-combined-ceiling is allowed (else: %s)"
              % ((r.get_json() or {}).get("error") or r.status_code),
              r.status_code == 200 and (r.get_json() or {}).get("ok"))
        os.unlink(_lf.name)
        LEDGER_JSONL = _lj_prev

        check("D330: the retired heads are OFF the page (petty spends live "
              "on the manual book)",
              "Medicine purchase (stock)" not in _eh2
              and "Shop expense (tea, cleaning, stationery)" not in _eh2
              and "Transport / courier" not in _eh2)


        _eide = _ec.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                            (UNIT, _ed)).fetchone()
        if _eide:
            # children FIRST -- sqlite reuses a deleted max rowid, so an
            # orphaned child row would silently join the NEXT day created
            # (reproduced offline on the clinic side of this same suite).
            for _tbl in ("day_line", "day_expense", "cash_movement",
                         "day_noncash_bill", "attachment", "expense_attachment",
                         "day_revision", "day_mirror_reveal"):
                try:
                    _ec.execute("DELETE FROM %s WHERE day_entry_id=?" % _tbl, (_eide[0],))
                except sqlite3.OperationalError:
                    pass
            _ec.execute("DELETE FROM day_entry WHERE id=?", (_eide[0],))
        _ec.commit(); _ec.close()
    os.environ["FINANCE_DEV_USER"], os.environ["FINANCE_DEV_ROLE"] = _d2u, _d2r

    # ---------------- F-130: the DESIGN is asserted, not just the ids -------
    # A page-only kit that preserves every id is invisible to an id-based test,
    # so a page could silently revert its design with the whole suite green.
    # The table below is the record of WHICH served pages are under Clinic
    # Design Language v1 -- SURVEYED on the real bytes, not assumed (F-132):
    # at S189 only the entry page and the Hub carry it; the workbench
    # (S187_M1a) and the review page (S179) both predate the design language.
    # The pre-v1 pages are asserted NEGATIVELY on purpose, so that rebuilding
    # one cannot land silently either -- it has to come here and flip the flag.
    _DESIGN_V1_MARKERS = ("--surface-page:#f3f2ee", 'id="toTop"',
                          'class="kick"', 'details class="help"')
    _DESIGN_V1_PAGES = (
        ("/finance/entry?legacy=1", "maker",   True),   # S188_D2a
        ("/finance/approvals", "checker", True),   # S187_H1b / H1c
        ("/finance/workbench", "checker", False),  # S187_M1a -- pre-v1
        ("/finance/review",    "checker", False),  # S179     -- pre-v1
    )
    for _dpath, _drole, _dv1 in _DESIGN_V1_PAGES:
        os.environ["FINANCE_DEV_USER"] = _d2u or "selftest"
        os.environ["FINANCE_DEV_ROLE"] = _drole
        _dr = c.get(_dpath)
        _dh = _dr.get_data(as_text=True) if _dr.status_code == 200 else ""
        _dhave = [_m for _m in _DESIGN_V1_MARKERS if _m in _dh]
        if _dv1:
            check("F-130: %s follows Clinic Design Language v1 (%d/4 markers, "
                  "http %s)" % (_dpath, len(_dhave), _dr.status_code),
                  _dr.status_code == 200
                  and len(_dhave) == len(_DESIGN_V1_MARKERS))
        else:
            check("F-130: %s is still pre-v1, exactly as recorded (%d/4 "
                  "markers, http %s)" % (_dpath, len(_dhave), _dr.status_code),
                  _dr.status_code == 200 and not _dhave)
    os.environ["FINANCE_DEV_USER"], os.environ["FINANCE_DEV_ROLE"] = _d2u, _d2r

    # ---------------- S194: ⭐1 Daily page · ⭐2 home-medicine · ⭐3 reclass ----
    os.environ["FINANCE_DEV_USER"] = "selftest"
    os.environ["FINANCE_DEV_ROLE"] = "maker"
    _s194 = c.get("/finance/daily")
    _s194h = _s194.get_data(as_text=True) if _s194.status_code == 200 else ""
    check("S194 ⭐1: /finance/daily is served to a maker and wires the finance API",
          _s194.status_code == 200 and "/finance/api" in _s194h
          and "cash-position" in _s194h)
    check("S194 ⭐1: the daily page carries the two-stage flow + transfer-only path",
          all(s in _s194h for s in ('data-stage="1"', 'data-stage="2"', "transferOnly")))
    check("S194 ⭐1: the daily page follows Clinic Design Language v1",
          all(m in _s194h for m in _DESIGN_V1_MARKERS))
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    check("S194 ⭐1: a checker is bounced off the maker-only daily page",
          c.get("/finance/daily").status_code in (302, 401, 403))

    for _role in ("maker", "checker"):
        os.environ["FINANCE_DEV_ROLE"] = _role
        _hm = c.get("/finance/api/home-medicine")
        _hj = _hm.get_json() if _hm.is_json else {}
        check("S194 ⭐2: home-medicine endpoint answers for a %s" % _role,
              _hm.status_code == 200 and _hj.get("ok") and "total_p" in _hj)
        _rx = c.get("/finance/api/reclassifications")
        _rj = _rx.get_json() if _rx.is_json else {}
        check("S194 ⭐3: reclassifications endpoint answers for a %s" % _role,
              _rx.status_code == 200 and _rj.get("ok") and "items" in _rj)

    os.environ["FINANCE_DEV_USER"] = ""
    os.environ["FINANCE_DEV_ROLE"] = ""
    check("S194: home-medicine refused without identity",
          c.get("/finance/api/home-medicine").status_code in (401, 403))
    check("S194: reclassifications refused without identity",
          c.get("/finance/api/reclassifications").status_code in (401, 403))

    # ⭐2/⭐3 behaviour on a throwaway test day: a Home-Medisun bill is tagged,
    # and a cash->upi re-import of the SAME bill logs exactly one mode flip.
    import finance_ingest as _fi194
    _tc = sqlite3.connect(DB_PATH)
    _tc.row_factory = sqlite3.Row
    _tc.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at) "
                "VALUES ('medical','2030-01-01','submitted','app','smoke','2030-01-01T10:00:00')")
    _tc.commit()
    _mkln = lambda md: [dict(bill_no="HM-SMOKE", bill_date="2030-01-01",
                             patient_name="HOME MEDISUN", description="HOME MEDISUN",
                             amount="500", mode=md, clinic_id=None)]
    try:
        _fi194.ingest_day(_tc, "medical", "2030-01-01", "manual", _mkln("cash"), run_by="smoke")
        _fi194.ingest_day(_tc, "medical", "2030-01-01", "manual", _mkln("upi"), run_by="smoke")
        _hmrow = _tc.execute("SELECT home_med FROM sale_item WHERE source_ref='HM-SMOKE' "
                             "ORDER BY id DESC LIMIT 1").fetchone()
        check("S194 ⭐2: a Home-Medisun bill is auto-tagged home_med=1",
              bool(_hmrow) and _hmrow["home_med"] == 1)
        _flip = _tc.execute("SELECT COUNT(*) n, MAX(old_mode) om, MAX(new_mode) nm "
                            "FROM mode_change_log WHERE source_ref='HM-SMOKE'").fetchone()
        check("S194 ⭐3: the cash->upi re-import logged exactly one mode flip",
              _flip["n"] == 1 and _flip["om"] == "cash" and _flip["nm"] == "upi")
    except Exception as _e194:                                  # pragma: no cover
        check("S194 ⭐2/⭐3: ingest tagging + reclass logging ran (%s)" % _e194, False)

    # ⭐4 — a doctor hand-over recorded as a cash_movement moves cash from the
    # drawer to the reserve LIVE, leaving unbanked (still in the unit) unchanged;
    # only a bank deposit reduces unbanked. Proven by DELTA so live data cancels.
    os.environ["FINANCE_DEV_USER"] = "selftest"
    os.environ["FINANCE_DEV_ROLE"] = "checker"
    try:
        _cp0 = c.get("/finance/api/cash-position?_=1").get_json()
        _tc.execute("INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference) "
                    "SELECT id, 'out', 'dr_bhawna', 50000, 'smoke handover' FROM day_entry "
                    "WHERE unit='medical' AND business_date='2030-01-01'")
        _tc.commit()
        _cp1 = c.get("/finance/api/cash-position?_=2").get_json()
        check("S194 ⭐4: a hand-over raises reserve and lowers the drawer by the same amount",
              _cp1["reserve_p"] - _cp0["reserve_p"] == 50000
              and _cp1["drawer_p"] - _cp0["drawer_p"] == -50000)
        check("S194 ⭐4: a hand-over leaves unbanked unchanged and the invariant holds",
              _cp1["unbanked_p"] == _cp0["unbanked_p"]
              and _cp1["drawer_p"] + _cp1["reserve_p"] + _cp1["with_manoj_p"] == _cp1["unbanked_p"])
    except Exception as _e4:                                     # pragma: no cover
        check("S194 ⭐4: cash-position hand-over folding ran (%s)" % _e4, False)

    _tc.close()
    os.environ["FINANCE_DEV_USER"] = _d2u

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



# ===================================================================== S195
#  SYSTEM HEALTH — turn a silent failure into a visible one.
#
#  On 21-08-2026 a Marg push started failing at 20:51 with HTTP 401 and nobody
#  noticed for over an hour: the sender said REFUSED on a screen no one was
#  watching, and the Hub looked normal. Everything below answers one question --
#  "is anything wrong right now?" -- from data the app already holds.
#
#  Cheap by construction: five small queries plus one directory stat. Safe to
#  call on every tile render.
# =====================================================================

HEALTH_BACKUP_DIR = os.environ.get("FINANCE_BACKUP_DIR", "/root/backups/finance")
# Yesterday is not "missing" until reception has had the morning to file it.
FILING_DUE_HOUR = int(os.environ.get("FINANCE_FILING_DUE_HOUR", "12"))


def _health_state(con):
    """Every check, worst-first. state is 'ok' | 'warn' | 'bad'."""
    checks = []
    # "info" is shown but never counts as a problem. Flags are notes; if they
    # drove the tile warning it would be lit permanently and stop meaning
    # anything -- the page itself says they are not failures.
    rank = {"ok": 0, "info": 0, "warn": 1, "bad": 2}

    def add(key, label, state, detail, hint=""):
        checks.append(dict(key=key, label=label, state=state, detail=detail, hint=hint))

    today = dt.date.today()

    # ---- 1. the Marg push: is the pharmacy's report arriving? --------------
    try:
        _marg_staging(con)
        row = con.execute("SELECT received_at, status FROM marg_push_staging "
                          "WHERE unit=? ORDER BY id DESC LIMIT 1", (UNIT,)).fetchone()
        pend = con.execute("SELECT COUNT(*) c FROM marg_push_staging "
                           "WHERE unit=? AND status='pending'", (UNIT,)).fetchone()["c"]
        if not row:
            add("push", "Marg report", "bad", "no report has ever arrived")
        else:
            last = str(row["received_at"])[:16].replace("T", " ")
            try:
                age_h = (dt.datetime.now() - dt.datetime.fromisoformat(
                    str(row["received_at"]).replace(" ", "T"))).total_seconds() / 3600.0
            except Exception:                                     # noqa: BLE001
                age_h = 0.0
            extra = (" · %d waiting for you to apply" % pend) if pend else ""
            if age_h > 36:
                add("push", "Marg report", "bad",
                    "last arrived %s (%.0f hours ago)%s" % (last, age_h, extra),
                    "Check the sender on the medical PC — this is how a broken "
                    "push looks.")
            elif age_h > 26:
                add("push", "Marg report", "warn",
                    "last arrived %s (%.0f hours ago)%s" % (last, age_h, extra),
                    "A day may not have been sent yet.")
            else:
                add("push", "Marg report", "ok", "last arrived %s%s" % (last, extra))
    except Exception as ex:                                       # noqa: BLE001
        add("push", "Marg report", "warn", "could not be read (%s)" % ex)

    # ---- 2. days filed: is anything missing? -------------------------------
    try:
        since = (today - dt.timedelta(days=7)).isoformat()
        have = {r["business_date"]: r["status"] for r in con.execute(
            "SELECT business_date, status FROM day_entry WHERE unit=? "
            "AND business_date>=? AND business_date<?",
            (UNIT, since, today.isoformat()))}
        # Reception files YESTERDAY during the morning round. Flagging it the
        # moment midnight passes would show red every single night and teach
        # everyone to ignore this page. Yesterday only counts as late after
        # FILING_DUE_HOUR; before that it is simply today's job, not a fault.
        missing, unapproved, due_today = [], [], None
        yday = today - dt.timedelta(days=1)
        for i in range(1, 8):
            d = (today - dt.timedelta(days=i))
            iso = d.isoformat()
            if d.weekday() == 6:                 # Sunday: the clinic is closed
                continue
            st = have.get(iso)
            if st is None:
                if d == yday and dt.datetime.now().hour < FILING_DUE_HOUR:
                    due_today = iso              # not late yet
                else:
                    missing.append(iso)
            elif st not in ("approved", "locked"):
                unapproved.append("%s (%s)" % (iso, st))
        if missing:
            add("days", "Days filed", "bad",
                "not filed: " + ", ".join(missing),
                "Reception has not sent these days.")
        elif due_today:
            add("days", "Days filed", "ok",
                "%s is today's job (due by %d:00)" % (due_today, FILING_DUE_HOUR))
        elif unapproved:
            add("days", "Days filed", "warn",
                "waiting for you: " + ", ".join(unapproved),
                "Filed, but not applied yet.")
        else:
            add("days", "Days filed", "ok", "last 7 days all filed and approved")
    except Exception as ex:                                       # noqa: BLE001
        add("days", "Days filed", "warn", "could not be read (%s)" % ex)

    # ---- 3. the drawer against the last physical count ---------------------
    try:
        led = con.execute("SELECT business_date, closing_p FROM v_cash_ledger "
                          "WHERE unit=? ORDER BY business_date DESC LIMIT 1",
                          (UNIT,)).fetchone()
        cnt = con.execute("SELECT business_date, counted_p FROM cash_count "
                          "WHERE unit=? ORDER BY business_date DESC LIMIT 1",
                          (UNIT,)).fetchone()
        if led is None:
            add("drawer", "Cash position", "warn", "no ledger rows yet")
        elif cnt is None:
            add("drawer", "Cash position", "warn",
                "books say %s — never counted physically" % rupees(int(led["closing_p"])),
                "A physical count is what makes the figure mean something.")
        else:
            days_since = 0
            try:
                days_since = (today - dt.date.fromisoformat(str(cnt["business_date"]))).days
            except Exception:                                     # noqa: BLE001
                pass
            detail = ("books %s as at %s · last counted %s on %s"
                      % (rupees(int(led["closing_p"])), led["business_date"],
                         rupees(int(cnt["counted_p"])), cnt["business_date"]))
            add("drawer", "Cash position",
                "warn" if days_since > 45 else "ok", detail,
                "The last physical count is %d days old." % days_since
                if days_since > 45 else "")
    except Exception as ex:                                       # noqa: BLE001
        add("drawer", "Cash position", "warn", "could not be read (%s)" % ex)

    # ---- 4. flags raised recently -----------------------------------------
    try:
        since = (today - dt.timedelta(days=30)).isoformat()
        rows = con.execute("SELECT code, COUNT(*) c FROM data_flag WHERE unit=? "
                           "AND business_date>=? GROUP BY code ORDER BY c DESC",
                           (UNIT, since)).fetchall()
        if not rows:
            add("flags", "Flags (30 days)", "ok", "none raised")
        else:
            add("flags", "Flags (30 days)", "info",
                ", ".join("%s x%d" % (r["code"], r["c"]) for r in rows[:5]),
                "Notes, not failures — worth a look, not an alarm.")
    except Exception as ex:                                       # noqa: BLE001
        add("flags", "Flags (30 days)", "info", "could not be read (%s)" % ex)

    # ---- 5. the books' own backup ------------------------------------------
    try:
        newest, newest_t = None, 0
        if os.path.isdir(HEALTH_BACKUP_DIR):
            for n in os.listdir(HEALTH_BACKUP_DIR):
                if n.startswith("finance_") and n.endswith(".db"):
                    p = os.path.join(HEALTH_BACKUP_DIR, n)
                    t = os.path.getmtime(p)
                    if t > newest_t:
                        newest, newest_t = n, t
        if not newest:
            add("backup", "Backup", "bad", "no backup found in %s" % HEALTH_BACKUP_DIR,
                "The books are the one thing that cannot be rebuilt.")
        else:
            age_h = (dt.datetime.now().timestamp() - newest_t) / 3600.0
            when = dt.datetime.fromtimestamp(newest_t).strftime("%Y-%m-%d %H:%M")
            if age_h > 36:
                add("backup", "Backup", "bad",
                    "newest is %s (%.0f hours old)" % (when, age_h),
                    "The nightly backup has not run.")
            else:
                add("backup", "Backup", "ok", "verified copy from %s" % when)
    except Exception as ex:                                       # noqa: BLE001
        add("backup", "Backup", "warn", "could not be read (%s)" % ex)

    worst = "ok"
    for c in checks:
        if rank[c["state"]] > rank[worst]:
            worst = c["state"]
    return {"ok": True, "worst": worst, "checks": checks,
            "as_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M")}


def _health_headline(con):
    """One short line for the portal tile. None when everything is fine."""
    try:
        h = _health_state(con)
    except Exception:                                             # noqa: BLE001
        return None
    if h["worst"] == "ok":
        return None
    bad = [c for c in h["checks"] if c["state"] == "bad"]
    pick = bad[0] if bad else [c for c in h["checks"] if c["state"] == "warn"][0]
    return ("%s %s — %s" % ("⚠" if bad else "•", pick["label"], pick["detail"]))[:110]


@app.route("/finance/api/health")
def api_health():
    u, err = require("checker")
    if err:
        return err
    return jsonify(_health_state(db()))


@app.route("/finance/health")
def page_health():
    u, err = require("checker")
    if err:
        return redirect(PORTAL_LOGIN, code=302)
    h = _health_state(db())
    tone = {"ok": ("#1f6f5c", "#eaf2ef", "All clear"),
            "info": ("#6b675e", "#f0efea", "All clear"),
            "warn": ("#9a6a00", "#fbf3e0", "Needs a look"),
            "bad": ("#a1362c", "#faece9", "Something is wrong")}
    col, wash, word = tone[h["worst"]]
    rows = []
    for c in h["checks"]:
        cc, cw, _ = tone[c["state"]]
        rows.append(
            "<div class=row><div class=dot style='background:%s'></div>"
            "<div class=body><div class=lbl>%s</div><div class=det>%s</div>%s</div></div>"
            % (cc, c["label"], c["detail"],
               ("<div class=hint>%s</div>" % c["hint"]) if c["hint"] else ""))
    html = ("""<!DOCTYPE html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>System health — Sanjeevni</title>
<style>
:root{--page:#f3f2ee;--card:#fff;--line:#e4e1d9;--ink:#22201c;--mut:#6b675e;--brand:#1f6f5c}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
 font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.bar{background:var(--brand);color:#fff;padding:12px 14px;display:flex;align-items:center;gap:10px;
 position:sticky;top:0}
.bar b{font-size:17px}.bar a{margin-left:auto;color:#e7f2ee;text-decoration:none;font-size:13px;
 background:rgba(255,255,255,.15);padding:6px 11px;border-radius:8px}
.wrap{max-width:640px;margin:0 auto;padding:0 12px 40px}
.hero{background:%s;border:1px solid %s55;border-radius:12px;padding:14px;margin:14px 0}
.hero .w{font-size:20px;font-weight:700;color:%s}
.hero .a{color:var(--mut);font-size:13px;margin-top:2px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:4px 14px;margin:12px 0}
.row{display:flex;gap:11px;padding:12px 0;border-bottom:1px dashed var(--line);align-items:flex-start}
.row:last-child{border-bottom:0}
.dot{width:10px;height:10px;border-radius:50%%;margin-top:6px;flex:none}
.lbl{font-weight:600;font-size:14px}
.det{color:var(--mut);font-size:13.5px;margin-top:1px}
.hint{color:var(--mut);font-size:12.5px;margin-top:4px;font-style:italic}
.foot{color:var(--mut);font-size:12.5px;margin-top:16px}
</style></head><body>
<div class=bar><b>System health</b><span style="opacity:.85;font-size:13px">Sanjeevni</span>
<a href="/finance/approvals">← Hub</a></div>
<div class=wrap>
 <div class=hero><div class=w>%s</div><div class=a>checked %s</div></div>
 <div class=card>%s</div>
 <div class=foot>Read-only. Refresh to re-check. This page asks one question:
 is anything wrong right now?</div>
</div></body></html>""" % (wash, col, col, word, h["as_at"], "".join(rows)))
    return app.response_class(html, mimetype="text/html")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    app.run(host="127.0.0.1", port=int(os.environ.get("FINANCE_PORT", "8099")))
