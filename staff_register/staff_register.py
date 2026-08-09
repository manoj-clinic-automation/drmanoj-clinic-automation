#!/usr/bin/env python3
"""
staff_register.py  —  Staff Daily Register  (subsystem D271)   v0.2
===================================================================
Dr. Manoj Agarwal Clinic, Bareilly.  Session 161.

Turns month-end salary prep from data-entry into confirmation: the day's
EXCEPTIONS (leave / lateness / dress / i-card / extra-duty / outstation) are
captured the same day at reception, checked, and stored. The salary engine later
only READS this store; it never guesses. Raw presence/absence stays the
biometric/attendance system's job (D275) — this register only records decisions
that reclassify or add to it.

MODEL (v0.2)
  * One "day_review" row per date = all_clear | exceptions (+ maker/checker/
    override + approval status). A clean day is ONE record, not 12.
  * daily_register rows exist only for staff who actually have an exception.
  * Absence is NOT entered here (biometric owns it, D275). A leave entry marks a
    biometric-absent day as sanctioned.

ROLES (D272)
  override : Dr Manoj + Dr Bhawna (peers) — reverse anything, holidays, toggle,
             ad-hoc fines; approve ANY date incl. Shavez's own.
  checker  : Shavez — maker + one-click approve; may NOT approve a date he himself
             entered (override approves those). Sole staff-document custodian.
  maker    : Alisha (active), Shivani (provisioned, INACTIVE until switched on).

PER-STAFF SCOPING (D276)
  * Arjun (minutes_exempt): Leave only. No dress/i-card, no late, no OT. His
    over-quota leave = flat pro-rata deduction (engine, step 6).
  * Extra duty (was "Cover") : Shivani only (cover_eligible).
  * Outstation               : Darpan only (outstation_eligible).
  * Dress / i-card fine       : hard-gated on an APPROVED issuance record AND no
    active pause window (lost/damaged/being-purchased pauses the fine).

Run (VPS):
    /root/wa/venv/bin/python3 /root/staff_register/staff_register.py --init
    /root/wa/venv/bin/python3 /root/staff_register/staff_register.py --seed /root/staff_master.csv
    /root/wa/venv/bin/python3 /root/staff_register/staff_register.py --selftest
Proxy: attendance.dr-manoj.in/register -> 127.0.0.1:8044
"""

import os
import sys
import csv
import io
import html
import uuid
import hmac
import hashlib
import sqlite3
import secrets
import datetime
from functools import wraps

from flask import (
    Flask, request, redirect, session, render_template_string, send_file, abort,
)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    import staff_register_config as cfg
except Exception:
    cfg = None


def _cfg(name, default=None):
    v = os.environ.get(name)
    if v is not None and v != "":
        return v
    if cfg is not None:
        v = getattr(cfg, name, None)
        if v is not None and v != "":
            return v
    return default


DB_PATH    = _cfg("SR_DB_PATH", os.path.join(APP_DIR, "staff_register.db"))
VAULT_DIR  = _cfg("SR_VAULT_DIR", os.path.join(APP_DIR, "vault"))
PW_SALT    = _cfg("SR_PW_SALT", "staff-register-salt")
APP_PREFIX = "/register"

# Stage-A salary reconciliation (read-only). Guarded import: a missing engine file
# must never take the whole register app down — the feature just goes dark.
SALARY_ATT_DIR = _cfg("SR_ATT_DIR", "/root")       # where salary_inputs_<ym>.csv lives
try:
    import salary_engine as _salary
    _SALARY_OK = True
except Exception:
    _salary = None
    _SALARY_OK = False
SEED_JOIN_FLOOR = _cfg("SR_SEED_JOIN_FLOOR", "2000-01-01")


def _load_secret_key():
    kf = os.path.join(APP_DIR, "secret_key")
    try:
        if os.path.exists(kf):
            return open(kf, "rb").read()
        k = secrets.token_bytes(32)
        with open(kf, "wb") as f:
            f.write(k)
        try:
            os.chmod(kf, 0o600)
        except Exception:
            pass
        return k
    except Exception:
        return secrets.token_bytes(32)


def _resolve_sso_secret():
    s = _cfg("CLINIC_SSO_SECRET")
    if s:
        return s
    for p in ("/root/portal", os.path.join(APP_DIR, "..", "portal")):
        try:
            if p not in sys.path:
                sys.path.insert(0, p)
            import portal_config as _pc   # noqa
            v = getattr(_pc, "CLINIC_SSO_SECRET", "")
            if v:
                return v
        except Exception:
            continue
    return ""


SSO_SECRET = _resolve_sso_secret()

for _p in ("/root/portal", os.path.join(APP_DIR, "..", "portal")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    import clinic_sso
    import clinic_users
    _SSO_LIBS = True
    _STORE = clinic_users.DEFAULT_STORE
except Exception:
    _SSO_LIBS = False
    _STORE = None

# ---------------------------------------------------------------------------
# ROLE MAPPING
# ---------------------------------------------------------------------------
CHECKER_USERS   = set(_cfg("SR_CHECKER_USERS", "shavez").split(","))
MAKER_USERS     = set(_cfg("SR_MAKER_USERS", "alisha,shivani").split(","))
OVERRIDE_USERS  = set(x for x in _cfg("SR_OVERRIDE_USERS", "").split(",") if x)
INACTIVE_MAKERS = set(x for x in _cfg("SR_INACTIVE_MAKERS", "shivani").split(",") if x)
DOC_CUSTODIANS  = set(_cfg("SR_DOC_CUSTODIANS", "shavez").split(","))
DELETER_USERS   = set(_cfg("SR_DELETER_USERS", "manoj").split(","))   # delete = manoj only
# Stage B (D283): salary VIEW allowlist + APPROVE&LOCK allowlist (username-gated, role-independent).
SALARY_USERS    = set(x for x in _cfg("SR_SALARY_USERS", "manoj,bhawna").split(",") if x)  # see the run
LOCK_USERS      = set(x for x in _cfg("SR_LOCK_USERS", "manoj").split(",") if x)            # approve&lock/unlock
# Daily biometric feed (D283): the attendance listener's punch log; read-only here.
SR_PUNCH_CSV    = _cfg("SR_PUNCH_CSV", "/root/punches.csv")


def biometric_present_ids(d):
    """Set of staff_ids (== biometric user_id) with >=1 punch on date d, read
    read-only from the attendance listener's punches.csv. Absence = a staff NOT in
    this set. Returns None if the feed is missing/unreadable so callers fall back to
    manual entry (never a crash). One-writer-per-store: attendance owns this file."""
    p = SR_PUNCH_CSV
    if not p or not os.path.exists(p):
        return None
    ids = set()
    try:
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("datetime") or "")[:10] == d:
                    try:
                        ids.add(int(row.get("user_id")))
                    except (TypeError, ValueError):
                        pass
    except Exception:
        return None
    return ids
SR_LOCAL_USERS  = getattr(cfg, "SR_LOCAL_USERS", {}) if cfg else {}


def _pw_hash(pw):
    return hashlib.sha256((PW_SALT + (pw or "")).encode("utf-8")).hexdigest()


def _register_role(username, broker_role):
    u = (username or "").strip()
    if broker_role == "doctor" or u in OVERRIDE_USERS:
        return "override"
    if u in CHECKER_USERS:
        return "checker"
    if u in MAKER_USERS:
        return "inactive" if u in INACTIVE_MAKERS else "maker"
    return None


def _caps(role, username):
    u = (username or "").strip()
    return {
        "maker":    role in ("maker", "checker", "override"),
        "check":    role in ("checker", "override"),
        "override": role == "override",
        "docs":     (role == "override") or (u in DOC_CUSTODIANS),
        "delete":   u in DELETER_USERS,
        "salary":   u in SALARY_USERS,          # Stage B: see the salary run
        "lock":     u in LOCK_USERS,            # Stage B: approve & lock / unlock
        "active":   role in ("maker", "checker", "override"),
    }

# ---------------------------------------------------------------------------
# RUPEE reference (engine consumes later)
# ---------------------------------------------------------------------------
RUPEE = {"dress_improper": -20, "icard_missing": -20, "extra_duty": 200,
         "outstation": 250, "late_approved_marks": 2, "late_unapproved_marks": 3}

# ---------------------------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS staff (
    staff_id        INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    join_date       TEXT NOT NULL,
    last_working    TEXT,
    base_salary     INTEGER NOT NULL DEFAULT 0,
    sunday_group    TEXT,
    allowed_offs    INTEGER NOT NULL DEFAULT 0,
    minutes_exempt  INTEGER NOT NULL DEFAULT 0,
    cover_eligible  INTEGER NOT NULL DEFAULT 0,
    outstation_eligible INTEGER NOT NULL DEFAULT 0,
    active          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS staff_shift (
    id INTEGER PRIMARY KEY, staff_id INTEGER NOT NULL,
    effective_from TEXT NOT NULL, shift_start TEXT NOT NULL, shift_end TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS day_review (
    reg_date        TEXT PRIMARY KEY,
    state           TEXT NOT NULL DEFAULT 'exceptions',   -- all_clear | exceptions
    maker_user      TEXT, maker_ts TEXT,
    checker_user    TEXT, checker_ts TEXT,
    override_user   TEXT, override_ts TEXT, override_note TEXT,
    status          TEXT NOT NULL DEFAULT 'draft'         -- draft | approved
);

CREATE TABLE IF NOT EXISTS daily_register (
    id INTEGER PRIMARY KEY,
    reg_date TEXT NOT NULL, staff_id INTEGER NOT NULL,
    absence_type TEXT, leave_kind TEXT,
    late_flag TEXT, late_approved_by TEXT,
    dress_improper INTEGER NOT NULL DEFAULT 0,
    icard_missing INTEGER NOT NULL DEFAULT 0,
    outstation_nights INTEGER NOT NULL DEFAULT 0,
    extra_duty INTEGER NOT NULL DEFAULT 0,
    ot_permitted INTEGER NOT NULL DEFAULT 0,
    maker_user TEXT, maker_ts TEXT,
    UNIQUE (reg_date, staff_id)
);
CREATE INDEX IF NOT EXISTS ix_reg_date ON daily_register(reg_date);
CREATE INDEX IF NOT EXISTS ix_reg_staff ON daily_register(staff_id);

CREATE TABLE IF NOT EXISTS clinic_holiday (
    reg_date TEXT PRIMARY KEY, note TEXT, entered_by TEXT, entered_ts TEXT
);

CREATE TABLE IF NOT EXISTS festival_day (
    fest_date     TEXT PRIMARY KEY,
    name          TEXT,
    clinic_closed INTEGER NOT NULL DEFAULT 0,   -- 1 = clinic holiday (Holi); 0 = festival leave day
    entered_by TEXT, entered_ts TEXT
);

CREATE TABLE IF NOT EXISTS issuance (
    id INTEGER PRIMARY KEY, staff_id INTEGER NOT NULL, item_type TEXT NOT NULL,
    season TEXT, issued_date TEXT NOT NULL,
    maker_user TEXT, maker_ts TEXT, checker_user TEXT, checker_ts TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS issuance_pause (
    id INTEGER PRIMARY KEY, staff_id INTEGER NOT NULL, item_type TEXT NOT NULL,
    from_date TEXT NOT NULL, to_date TEXT,          -- to_date NULL = still open
    reason TEXT,
    maker_user TEXT, maker_ts TEXT, checker_user TEXT, checker_ts TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS incentive_pot (
    id INTEGER PRIMARY KEY, staff_id INTEGER NOT NULL, fy_year INTEGER NOT NULL,
    accrual_month TEXT NOT NULL, amount INTEGER NOT NULL DEFAULT 0, written_ts TEXT,
    UNIQUE (staff_id, accrual_month)
);

CREATE TABLE IF NOT EXISTS document_vault (
    id INTEGER PRIMARY KEY, staff_id INTEGER NOT NULL, doc_type TEXT NOT NULL,
    original_name TEXT, stored_path TEXT NOT NULL, is_pdf INTEGER NOT NULL DEFAULT 1,
    sub_type TEXT, council_registered INTEGER, reg_no TEXT,
    note TEXT, uploaded_by TEXT, uploaded_ts TEXT
);

CREATE TABLE IF NOT EXISTS staff_profile (
    staff_id        INTEGER PRIMARY KEY,
    job_roles       TEXT,
    current_address TEXT, permanent_address TEXT,
    emergency_name  TEXT, emergency_phone TEXT,
    family_name     TEXT, family_relation TEXT,
    updated_by TEXT, updated_ts TEXT
);

CREATE TABLE IF NOT EXISTS asset_issue (
    id INTEGER PRIMARY KEY,
    staff_id  INTEGER NOT NULL,
    asset_type TEXT NOT NULL,            -- mobile_phone | bicycle | motorcycle | other
    identifier TEXT,                     -- IMEI / cycle no / reg no / free
    descr      TEXT,
    issued_date TEXT, issued_by TEXT,
    returned_date TEXT, returned_by TEXT,
    status TEXT NOT NULL DEFAULT 'issued', -- issued | returned
    note TEXT
);

CREATE TABLE IF NOT EXISTS degree_registration (
    id INTEGER PRIMARY KEY,
    doc_id     INTEGER NOT NULL,        -- the degree's document_vault.id
    staff_id   INTEGER NOT NULL,
    council    TEXT, reg_no TEXT,
    stored_path TEXT, original_name TEXT, is_pdf INTEGER NOT NULL DEFAULT 1,
    added_by TEXT, added_ts TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    skey TEXT PRIMARY KEY, svalue TEXT, updated_by TEXT, updated_ts TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY, entity TEXT NOT NULL, entity_ref TEXT, action TEXT NOT NULL,
    old_value TEXT, new_value TEXT, actor TEXT NOT NULL, ts TEXT NOT NULL, note TEXT
);

CREATE TABLE IF NOT EXISTS locked_run (          -- Stage B (D283): the official, frozen month run
    ym            TEXT PRIMARY KEY,              -- YYYY-MM
    total_payout  INTEGER NOT NULL,              -- headline TOTAL PAYOUT (rupees, rounded)
    report_html   TEXT NOT NULL,                 -- frozen snapshot of the FINAL SALARY table
    locked_by     TEXT NOT NULL, locked_ts TEXT NOT NULL,
    unlocked_by   TEXT, unlocked_ts TEXT, unlock_reason TEXT,
    status        TEXT NOT NULL DEFAULT 'locked' -- locked | unlocked
);

CREATE TABLE IF NOT EXISTS leave_sanction (       -- grid step 2 (D284): a continuous sanctioned leave
    id INTEGER PRIMARY KEY,
    staff_id INTEGER NOT NULL,
    from_date TEXT NOT NULL, to_date TEXT NOT NULL,
    approved_by TEXT NOT NULL,                     -- bhawna | manoj (the sanctioner)
    note TEXT,
    maker_user TEXT, maker_ts TEXT,
    checker_user TEXT, checker_ts TEXT,
    status TEXT NOT NULL DEFAULT 'draft'           -- draft | approved | cancelled
);
"""

# columns that may be missing on a DB created by an earlier build -> add in place
_MIGRATIONS = [
    ("daily_register", "leave_approved_by", "TEXT"),
    ("staff", "outstation_eligible", "INTEGER NOT NULL DEFAULT 0"),
    ("staff", "allowed_offs", "INTEGER NOT NULL DEFAULT 0"),
    ("document_vault", "sub_type", "TEXT"),
    ("document_vault", "council_registered", "INTEGER"),
    ("document_vault", "reg_no", "TEXT"),
    ("staff_profile", "current_address", "TEXT"),
    ("staff_profile", "permanent_address", "TEXT"),
]


def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA foreign_keys=ON;")
    return con


def init_db():
    con = get_db()
    con.executescript(SCHEMA)
    # in-place migrations for pre-existing DBs (safe, non-destructive)
    for tbl, col, decl in _MIGRATIONS:
        cols = [r["name"] for r in con.execute("PRAGMA table_info(%s)" % tbl)]
        if col not in cols:
            con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (tbl, col, decl))
    con.commit()
    con.close()


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return datetime.date.today().strftime("%Y-%m-%d")


def _audit(con, entity, ref, action, old, new, actor, note=""):
    con.execute("INSERT INTO audit_log(entity,entity_ref,action,old_value,new_value,"
                "actor,ts,note) VALUES(?,?,?,?,?,?,?,?)",
                (entity, str(ref), action, str(old), str(new), actor, _now(), note))

# ---------------------------------------------------------------------------
# SEED from staff_master.csv (D273)
# ---------------------------------------------------------------------------
_ALIASES = {
    "staff_id":       ["staff_id", "user_id", "id", "sid"],
    "name":           ["name", "staff", "staff_name"],
    "join_date":      ["join_date", "doj", "date_of_joining", "joined"],
    "last_working":   ["last_working", "last_day", "exit_date", "resigned"],
    "base_salary":    ["base_salary", "salary", "base", "monthly_salary", "gross"],
    "sunday_group":   ["sunday_group", "sun_group", "group"],
    "allowed_offs":   ["allowed_offs", "offs", "allowed_off"],
    "minutes_exempt": ["minutes_exempt", "exempt", "no_minutes"],
    "cover_eligible": ["cover_eligible", "cover"],
    "active":         ["active", "is_active"],
    "wd_start":       ["wd_start", "shift_start", "start"],
    "wd_end":         ["wd_end", "shift_end", "end"],
}


def _match_header(fieldnames):
    lower = {h.lower().strip(): h for h in fieldnames}
    chosen = {}
    for canon, opts in _ALIASES.items():
        for o in opts:
            if o in lower:
                chosen[canon] = lower[o]
                break
    return chosen


def seed_from_csv(path, verbose=True):
    if not os.path.exists(path):
        raise FileNotFoundError("CSV not found: " + path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        headers = rdr.fieldnames or []
        m = _match_header(headers)
        if "name" not in m:
            raise ValueError("No 'name' column. Header: " + str(headers))
        rows = list(rdr)
    con = get_db()
    n = shifts = issued = 0
    for i, r in enumerate(rows, start=1):
        def g(key, default=None):
            col = m.get(key)
            return (r.get(col) if col else default)

        name = (g("name") or "").strip()
        if not name:
            continue
        try:
            sid = int(g("staff_id")) if m.get("staff_id") else i
        except Exception:
            sid = i
        join_date = (g("join_date") or "").strip() or SEED_JOIN_FLOOR
        last_working = (g("last_working") or "").strip() or None
        try:
            base = int(float(g("base_salary") or 0))
        except Exception:
            base = 0
        sun_group = (g("sunday_group") or "").strip() or None
        try:
            offs = int(float(g("allowed_offs") or 0))
        except Exception:
            offs = 0
        try:
            mexempt = int(float(g("minutes_exempt") or 0))
        except Exception:
            mexempt = 0
        try:
            cover = int(float(g("cover_eligible") or 0))
        except Exception:
            cover = 0
        nlow = name.strip().lower()
        if not cover and nlow.startswith("shivani"):
            cover = 1                     # extra-duty eligible
        outst = 1 if nlow.startswith("darpan") else 0   # outstation eligible
        try:
            active = int(float(g("active") or 1))
        except Exception:
            active = 1
        con.execute(
            "INSERT OR REPLACE INTO staff(staff_id,name,join_date,last_working,"
            "base_salary,sunday_group,allowed_offs,minutes_exempt,cover_eligible,"
            "outstation_eligible,active) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (sid, name, join_date, last_working, base, sun_group, offs,
             mexempt, cover, outst, active))
        ws = (g("wd_start") or "").strip()
        we = (g("wd_end") or "").strip()
        if ws and we:
            con.execute("DELETE FROM staff_shift WHERE staff_id=? AND effective_from=?",
                        (sid, join_date))
            con.execute("INSERT INTO staff_shift(staff_id,effective_from,shift_start,"
                        "shift_end) VALUES(?,?,?,?)", (sid, join_date, ws, we))
            shifts += 1
        # everyone (except Arjun/minutes_exempt) is already issued uniform + i-card
        if not mexempt:
            for item in ("uniform", "icard"):
                ex = con.execute("SELECT 1 FROM issuance WHERE staff_id=? AND "
                                 "item_type=? AND status='approved'",
                                 (sid, item)).fetchone()
                if not ex:
                    con.execute("INSERT INTO issuance(staff_id,item_type,issued_date,"
                                "maker_user,checker_user,status) VALUES(?,?,?,?,?, "
                                "'approved')", (sid, item, join_date, "seed", "seed"))
                    issued += 1
        n += 1
    con.commit()
    con.close()
    if verbose:
        print("Detected header:", headers)
        print("Column mapping :", m)
        print("Seeded staff   :", n, "(staff_id = user_id)" if m.get("staff_id") else "")
        print("Baseline shifts:", shifts)
        print("Issuance rows  :", issued, "(uniform + i-card, approved)")
    return n

# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------
def _sso_identity(req):
    if not _SSO_LIBS or not SSO_SECRET:
        return None, None
    try:
        tok = req.cookies.get(clinic_sso.COOKIE_NAME, "")
        if not tok:
            return None, None
        who = clinic_sso.verify_token(tok, SSO_SECRET,
                                      current_epoch=clinic_users.get_epoch(_STORE))
        if who:
            return who.get("user"), who.get("role")
    except Exception:
        return None, None
    return None, None


def current_user(req):
    user, brole = _sso_identity(req)
    if user:
        role = _register_role(user, brole)
        return {"user": user, "role": role, "via": "sso", "caps": _caps(role, user)}
    lu = session.get("sr_user")
    if lu:
        role = session.get("sr_role")
        return {"user": lu, "role": role, "via": "local", "caps": _caps(role, lu)}
    return None


def _verify_local_login(user, pw):
    user = (user or "").strip()
    if _SSO_LIBS:
        try:
            brole = clinic_users.verify_password(_STORE, user, pw)
            if brole:
                return _register_role(user, brole)
        except Exception:
            pass
    rec = SR_LOCAL_USERS.get(user)
    if rec and hmac.compare_digest(rec.get("pw", ""), _pw_hash(pw)):
        return rec.get("role")
    return None


def require(cap):
    def deco(view):
        @wraps(view)
        def wrapper(*a, **k):
            u = current_user(request)
            if not u:
                return redirect(APP_PREFIX + "/login")
            if u["role"] is None or not u["caps"].get("active"):
                return render_template_string(NO_ACCESS_HTML, who=u,
                                              url_prefix=APP_PREFIX), 403
            if cap and not u["caps"].get(cap):
                return render_template_string(NO_ACCESS_HTML, who=u,
                                              url_prefix=APP_PREFIX), 403
            return view(*a, **k)
        return wrapper
    return deco

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def staff_for_date(con, d):
    rows = con.execute("SELECT * FROM staff WHERE active=1 OR last_working>=? "
                       "ORDER BY name", (d,)).fetchall()
    out = []
    for r in rows:
        if r["join_date"] and r["join_date"] > d:
            continue
        if r["last_working"] and r["last_working"] < d:
            continue
        out.append(r)
    return out


def day_rows(con, d):
    return {r["staff_id"]: r for r in
            con.execute("SELECT * FROM daily_register WHERE reg_date=?", (d,))}


def is_holiday(con, d):
    """Clinic closed if a festival_day entry for d has clinic_closed=1 (e.g. Holi)."""
    return con.execute("SELECT 1 FROM festival_day WHERE fest_date=? AND clinic_closed=1",
                       (d,)).fetchone() is not None


def festival_on(con, d):
    """A leave-eligible festival for d (listed, toggle OFF) -> the row, else None.
    Leave taken on such a date is classified as a FESTIVAL leave (D278)."""
    return con.execute("SELECT * FROM festival_day WHERE fest_date=? AND clinic_closed=0",
                       (d,)).fetchone()


def list_festivals(con):
    return con.execute("SELECT * FROM festival_day ORDER BY fest_date").fetchall()


def issuance_ok(con, staff_id, item_type, d):
    """Fine gate: an APPROVED issuance exists AND date d is not inside a pause
    window (lost/damaged/being-purchased) for that item."""
    if not con.execute("SELECT 1 FROM issuance WHERE staff_id=? AND item_type=? "
                        "AND status='approved'", (staff_id, item_type)).fetchone():
        return False
    paused = con.execute(
        "SELECT 1 FROM issuance_pause WHERE staff_id=? AND item_type=? "
        "AND from_date<=? AND (to_date IS NULL OR to_date>=?)",
        (staff_id, item_type, d, d)).fetchone()
    return paused is None


def review_row(con, d):
    return con.execute("SELECT * FROM day_review WHERE reg_date=?", (d,)).fetchone()


def date_status(con, d):
    r = review_row(con, d)
    if not r:
        return "empty"
    return "approved" if r["status"] == "approved" else "draft"


def _valid_date(s):
    try:
        datetime.datetime.strptime(s, "%Y-%m-%d")
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
# WRITE OPS
# ---------------------------------------------------------------------------
def save_maker(d, all_clear, form, actor):
    con = get_db()
    if date_status(con, d) == "approved":
        con.close()
        raise PermissionError("date already approved; override must reverse first")
    if is_holiday(con, d):
        con.close()
        raise PermissionError("date is a clinic holiday; no duty entries")

    state = "all_clear" if all_clear else "exceptions"
    con.execute(
        "INSERT INTO day_review(reg_date,state,maker_user,maker_ts,status) "
        "VALUES(?,?,?,?, 'draft') ON CONFLICT(reg_date) DO UPDATE SET "
        "state=excluded.state,maker_user=excluded.maker_user,"
        "maker_ts=excluded.maker_ts,status='draft',checker_user=NULL,checker_ts=NULL",
        (d, state, actor, _now()))

    written = 0
    if all_clear:
        con.execute("DELETE FROM daily_register WHERE reg_date=?", (d,))
    else:
        fest = festival_on(con, d)          # D278: leave today classified by the festivals list
        for s in staff_for_date(con, d):
            sid = s["staff_id"]
            pre = "s%d_" % sid
            mexempt = s["minutes_exempt"]
            # LEAVE dropdown: ""(present) | not_approved(genuine absent) | bhawna | manoj
            leave_val = (form.get(pre + "leave") or "").strip()
            leave_kind = leave_by = None
            absence = None
            if leave_val in ("bhawna", "manoj"):
                leave_kind = "festival" if fest else "discretionary"
                leave_by = leave_val
                absence = "leave_sanctioned"
            elif leave_val == "not_approved":
                absence = "absent"                     # biometric-absent, unsanctioned -> genuine
            late_val = form.get(pre + "late") or ""     # not_approved|bhawna|manoj
            dress = 1 if form.get(pre + "dress") else 0
            icard = 1 if form.get(pre + "icard") else 0
            extra = 1 if (form.get(pre + "extra") in ("1", "on", "yes", "Yes")) else 0
            otp = 0   # OT approved-by-default; reviewed next-day (D277), not entered here
            outs = 1 if (form.get(pre + "outstation") in ("1", "on", "yes", "Yes")) else 0

            # decode combined late dropdown -> flag + approver
            if late_val == "not_approved":
                late_flag, late_by = "not_informed", None
            elif late_val in ("bhawna", "manoj"):
                late_flag, late_by = "informed", late_val
            else:
                late_flag, late_by = None, None

            # ---- per-staff scoping + nullification (D276 / S6), server-authoritative ----
            if not s["outstation_eligible"]:
                outs = 0
            if not s["cover_eligible"]:
                extra = 0
            if outs:                          # OUTSTATION wins: no-punch duty day = present, not leave
                leave_kind = leave_by = None
                absence = "outstation"
                late_flag = late_by = None
                dress = icard = extra = 0
            elif leave_kind or absence == "absent":   # leave/absent carries no presence-behaviour
                late_flag = late_by = None
                dress = icard = 0
                extra = 0
            if mexempt:                       # Arjun: leave/absence only
                late_flag = late_by = None
                dress = icard = otp = extra = outs = 0
            if dress and not issuance_ok(con, sid, "uniform", d):
                dress = 0
            if icard and not issuance_ok(con, sid, "icard", d):
                icard = 0

            has_exception = (any([leave_kind, late_flag, dress, icard, extra, outs])
                             or absence in ("absent", "outstation"))
            if has_exception:
                con.execute(
                    "INSERT INTO daily_register(reg_date,staff_id,absence_type,"
                    "leave_kind,leave_approved_by,late_flag,late_approved_by,"
                    "dress_improper,icard_missing,"
                    "outstation_nights,extra_duty,ot_permitted,maker_user,maker_ts) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(reg_date,staff_id) DO UPDATE SET "
                    "absence_type=excluded.absence_type,leave_kind=excluded.leave_kind,"
                    "leave_approved_by=excluded.leave_approved_by,"
                    "late_flag=excluded.late_flag,late_approved_by=excluded.late_approved_by,"
                    "dress_improper=excluded.dress_improper,icard_missing=excluded.icard_missing,"
                    "outstation_nights=excluded.outstation_nights,extra_duty=excluded.extra_duty,"
                    "ot_permitted=excluded.ot_permitted,maker_user=excluded.maker_user,"
                    "maker_ts=excluded.maker_ts",
                    (d, sid, absence, leave_kind, leave_by, late_flag, late_by, dress, icard,
                     outs, extra, otp, actor, _now()))
                written += 1
            else:
                con.execute("DELETE FROM daily_register WHERE reg_date=? AND staff_id=?",
                            (d, sid))
    _audit(con, "day", d, "maker_save",
           "", "all_clear" if all_clear else "%d exceptions" % written, actor)
    con.commit()
    con.close()
    return written


def can_check_approve(con, d, actor, is_override):
    r = review_row(con, d)
    if not r:
        return False
    if is_override:
        return True
    return r["maker_user"] != actor


def approve_date(d, actor, is_override):
    con = get_db()
    if not review_row(con, d):
        con.close()
        raise ValueError("nothing to approve on this date")
    if not can_check_approve(con, d, actor, is_override):
        con.close()
        raise PermissionError("you entered this date; an override must approve it")
    con.execute("UPDATE day_review SET status='approved',checker_user=?,checker_ts=? "
                "WHERE reg_date=?", (actor, _now(), d))
    _audit(con, "day", d, "approve", "draft", "approved", actor)
    con.commit()
    con.close()


def reverse_date(d, actor, note=""):
    con = get_db()
    con.execute("UPDATE day_review SET status='draft',checker_user=NULL,checker_ts=NULL,"
                "override_user=?,override_ts=?,override_note=? WHERE reg_date=?",
                (actor, _now(), note, d))
    _audit(con, "day", d, "reverse", "approved", "draft", actor, note)
    con.commit()
    con.close()


# --- grid step 2 (D284): continuous sanctioned-leave range (maker -> checker) ---------
def active_leave_for(con, sid, d):
    """Approver (bhawna|manoj) of an APPROVED leave range covering (staff sid, date d),
    else None. Only APPROVED ranges pre-fill the daily grid (a draft never affects pay)."""
    row = con.execute(
        "SELECT approved_by FROM leave_sanction WHERE staff_id=? AND status='approved' "
        "AND from_date<=? AND to_date>=? ORDER BY checker_ts DESC LIMIT 1",
        (sid, d, d)).fetchone()
    return row["approved_by"] if row else None


def add_leave_sanction(sid, frm, to, approved_by, note, actor):
    if not (_valid_date(frm) and _valid_date(to)):
        raise ValueError("bad dates")
    if to < frm:
        raise ValueError("the to-date is before the from-date")
    if approved_by not in ("bhawna", "manoj"):
        raise ValueError("choose who sanctioned it")
    con = get_db()
    if not con.execute("SELECT 1 FROM staff WHERE staff_id=?", (sid,)).fetchone():
        con.close()
        raise ValueError("no such staff")
    con.execute("INSERT INTO leave_sanction(staff_id,from_date,to_date,approved_by,note,"
                "maker_user,maker_ts,status) VALUES(?,?,?,?,?,?,?, 'draft')",
                (sid, frm, to, approved_by, (note or "").strip(), actor, _now()))
    _audit(con, "leave", "%d %s..%s" % (sid, frm, to), "sanction_add", "", approved_by, actor, note or "")
    con.commit()
    con.close()


def approve_leave_sanction(lsid, actor, is_override):
    con = get_db()
    row = con.execute("SELECT * FROM leave_sanction WHERE id=?", (lsid,)).fetchone()
    if not row:
        con.close()
        raise ValueError("no such leave sanction")
    if row["status"] != "draft":
        con.close()
        raise ValueError("not pending")
    if not is_override and row["maker_user"] == actor:
        con.close()
        raise PermissionError("you entered this leave; another checker or an override must approve")
    con.execute("UPDATE leave_sanction SET status='approved',checker_user=?,checker_ts=? WHERE id=?",
                (actor, _now(), lsid))
    _audit(con, "leave", lsid, "sanction_approve", "draft", "approved", actor)
    con.commit()
    con.close()


def cancel_leave_sanction(lsid, actor, note=""):
    con = get_db()
    con.execute("UPDATE leave_sanction SET status='cancelled',checker_user=?,checker_ts=? WHERE id=?",
                (actor, _now(), lsid))
    _audit(con, "leave", lsid, "sanction_cancel", "", "cancelled", actor, note)
    con.commit()
    con.close()


def list_leave_sanctions(con):
    return con.execute(
        "SELECT ls.*, s.name AS name FROM leave_sanction ls "
        "LEFT JOIN staff s ON s.staff_id=ls.staff_id "
        "ORDER BY (ls.status='draft') DESC, ls.from_date DESC").fetchall()


def set_festival(d, name, closed, actor):
    con = get_db()
    con.execute("INSERT OR REPLACE INTO festival_day(fest_date,name,clinic_closed,"
                "entered_by,entered_ts) VALUES(?,?,?,?,?)",
                (d, name, 1 if closed else 0, actor, _now()))
    _audit(con, "festival", d, "set", "", "%s%s" % (name, " [closed]" if closed else ""), actor)
    con.commit()
    con.close()


def del_festival(d, actor):
    con = get_db()
    con.execute("DELETE FROM festival_day WHERE fest_date=?", (d,))
    _audit(con, "festival", d, "delete", d, "", actor)
    con.commit()
    con.close()

# ---------------------------------------------------------------------------
# STAFF RECORD: issuance, pause windows, document vault (D274)
# ---------------------------------------------------------------------------
def staff_by_id(con, sid):
    return con.execute("SELECT * FROM staff WHERE staff_id=?", (sid,)).fetchone()


def issuance_for_staff(con, sid):
    return con.execute("SELECT * FROM issuance WHERE staff_id=? ORDER BY item_type,"
                       "issued_date DESC", (sid,)).fetchall()


def pauses_for_staff(con, sid):
    return con.execute("SELECT * FROM issuance_pause WHERE staff_id=? ORDER BY "
                       "from_date DESC", (sid,)).fetchall()


def docs_for_staff(con, sid):
    return con.execute("SELECT * FROM document_vault WHERE staff_id=? ORDER BY "
                       "uploaded_ts DESC", (sid,)).fetchall()


def add_issuance(sid, item, season, issued_date, actor):
    con = get_db()
    con.execute("INSERT INTO issuance(staff_id,item_type,season,issued_date,maker_user,"
                "maker_ts,status) VALUES(?,?,?,?,?,?, 'draft')",
                (sid, item, season or None, issued_date, actor, _now()))
    _audit(con, "issuance", sid, "add", "", "%s %s" % (item, issued_date), actor)
    con.commit()
    con.close()


def approve_issuance(iid, actor):
    con = get_db()
    con.execute("UPDATE issuance SET status='approved',checker_user=?,checker_ts=? "
                "WHERE id=?", (actor, _now(), iid))
    _audit(con, "issuance", iid, "approve", "draft", "approved", actor)
    con.commit()
    con.close()


def add_pause(sid, item, from_date, reason, actor):
    """Open a fine-pause window (item lost / damaged / being purchased). Effective
    immediately (protects the staffer) — the daily gate reads it at once."""
    con = get_db()
    con.execute("INSERT INTO issuance_pause(staff_id,item_type,from_date,to_date,reason,"
                "maker_user,maker_ts,status) VALUES(?,?,?,NULL,?,?,?, 'open')",
                (sid, item, from_date, reason, actor, _now()))
    _audit(con, "pause", sid, "open", "", "%s from %s" % (item, from_date), actor)
    con.commit()
    con.close()


def close_pause(pid, to_date, actor):
    """Resolve a pause (item re-issued / replaced). Fine resumes after to_date."""
    con = get_db()
    con.execute("UPDATE issuance_pause SET to_date=?,checker_user=?,checker_ts=?,"
                "status='closed' WHERE id=?", (to_date, actor, _now(), pid))
    _audit(con, "pause", pid, "close", "open", "closed %s" % to_date, actor)
    con.commit()
    con.close()


DOC_TYPES = ["aadhaar", "pan", "voter_id", "driving_licence", "staff_photo",
             "family_aadhaar", "appointment_letter", "highschool", "intermediate",
             "graduation", "professional_degree", "application", "notice", "other"]
DOC_LABELS = {
    "aadhaar": "Aadhaar card", "pan": "PAN card", "voter_id": "Voter ID",
    "driving_licence": "Driving licence", "staff_photo": "Staff photo",
    "family_aadhaar": "Family member Aadhaar", "appointment_letter": "Appointment letter",
    "highschool": "High school", "intermediate": "Intermediate",
    "graduation": "Graduation", "professional_degree": "Professional degree",
    "application": "Application", "notice": "Notice served", "other": "Other",
}
# groups for the picker (order matters)
DOC_GROUPS = [
    ("Identity & address", ["aadhaar", "pan", "voter_id", "driving_licence",
                            "staff_photo", "family_aadhaar"]),
    ("Appointment", ["appointment_letter"]),
    ("Academic", ["highschool", "intermediate", "graduation"]),
    ("Professional degree", ["professional_degree"]),
    ("Correspondence", ["application", "notice"]),
    ("Other", ["other"]),
]
DEGREE_SUBTYPES = ["DMLT", "BMLT", "Pharmacist", "Other"]
JOB_ROLES = ["Lab technician", "Lab assistant", "Lab field staff", "Receptionist",
             "Clinic assistant", "Pharmacy staff", "Cleaner", "Driver"]
FAMILY_RELATIONS = ["Father", "Mother", "Husband", "Wife", "Son", "Daughter",
                    "Brother", "Sister", "Guardian", "Other"]
ASSET_TYPES = [("mobile_phone", "Mobile phone"), ("bicycle", "Bicycle"),
               ("motorcycle", "Bike / motorcycle"), ("other", "Other")]
ASSET_LABELS = dict(ASSET_TYPES)

# auto-derived completeness (S274 owner rule): id/address/qualification from docs
_ID_DOCS = {"aadhaar", "pan", "voter_id", "driving_licence"}
_ADDR_DOCS = {"aadhaar", "voter_id"}
_QUAL_DOCS = {"highschool", "intermediate", "graduation", "professional_degree"}
_IMG_EXT = ("jpg", "jpeg", "png", "gif", "bmp", "webp")


def doc_summary(con, sid):
    types = {r["doc_type"] for r in
             con.execute("SELECT doc_type FROM document_vault WHERE staff_id=?", (sid,))}
    return {"id_proof": bool(types & _ID_DOCS),
            "address_proof": bool(types & _ADDR_DOCS),
            "qualification": bool(types & _QUAL_DOCS)}


def get_profile(con, sid):
    return con.execute("SELECT * FROM staff_profile WHERE staff_id=?", (sid,)).fetchone()


def save_profile(sid, join_date, last_working, roles, cur_addr, perm_addr,
                 en, ep, fn, fr, actor):
    con = get_db()
    if join_date:
        con.execute("UPDATE staff SET join_date=? WHERE staff_id=?", (join_date, sid))
    # last_working: blank clears it (active); a date sets resignation
    lw = last_working or None
    con.execute("UPDATE staff SET last_working=?, active=? WHERE staff_id=?",
                (lw, 0 if lw else 1, sid))
    con.execute(
        "INSERT INTO staff_profile(staff_id,job_roles,current_address,permanent_address,"
        "emergency_name,emergency_phone,family_name,family_relation,updated_by,updated_ts) "
        "VALUES(?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(staff_id) DO UPDATE SET job_roles=excluded.job_roles,"
        "current_address=excluded.current_address,permanent_address=excluded.permanent_address,"
        "emergency_name=excluded.emergency_name,emergency_phone=excluded.emergency_phone,"
        "family_name=excluded.family_name,family_relation=excluded.family_relation,"
        "updated_by=excluded.updated_by,updated_ts=excluded.updated_ts",
        (sid, roles, cur_addr, perm_addr, en, ep, fn, fr, actor, _now()))
    _audit(con, "profile", sid, "save", "", "roles=%s" % (roles or ""), actor)
    con.commit()
    con.close()


def assets_for_staff(con, sid):
    return con.execute("SELECT * FROM asset_issue WHERE staff_id=? "
                       "ORDER BY status, id DESC", (sid,)).fetchall()


def add_asset(sid, asset_type, identifier, descr, issued_date, note, actor):
    con = get_db()
    con.execute("INSERT INTO asset_issue(staff_id,asset_type,identifier,descr,"
                "issued_date,issued_by,status,note) VALUES(?,?,?,?,?,?,'issued',?)",
                (sid, asset_type, identifier or None, descr or None,
                 issued_date or _today(), actor, note or None))
    _audit(con, "asset", sid, "issue", asset_type, identifier or "", actor)
    con.commit()
    con.close()


def return_asset(aid, returned_date, actor):
    con = get_db()
    a = con.execute("SELECT * FROM asset_issue WHERE id=?", (aid,)).fetchone()
    sid = a["staff_id"] if a else None
    if a and a["status"] != "returned":
        con.execute("UPDATE asset_issue SET status='returned',returned_date=?,returned_by=? "
                    "WHERE id=?", (returned_date or _today(), actor, aid))
        _audit(con, "asset", sid, "return", a["asset_type"], a["identifier"] or "", actor)
    con.commit()
    con.close()
    return sid


def delete_asset(aid, actor):
    con = get_db()
    a = con.execute("SELECT * FROM asset_issue WHERE id=?", (aid,)).fetchone()
    sid = a["staff_id"] if a else None
    if a:
        con.execute("DELETE FROM asset_issue WHERE id=?", (aid,))
        _audit(con, "asset", sid, "delete", a["asset_type"], a["identifier"] or "", actor)
    con.commit()
    con.close()
    return sid


def delete_document(did, actor):
    """Delete a document row AND its file from disk (and any degree registrations
    hanging off it). Restricted to the deleter (manoj)."""
    con = get_db()
    dv = con.execute("SELECT * FROM document_vault WHERE id=?", (did,)).fetchone()
    sid = dv["staff_id"] if dv else None
    if dv:
        # cascade: registration certificates linked to this degree
        for rg in con.execute("SELECT * FROM degree_registration WHERE doc_id=?", (did,)):
            try:
                if rg["stored_path"] and os.path.exists(rg["stored_path"]):
                    os.remove(rg["stored_path"])
            except Exception:
                pass
        con.execute("DELETE FROM degree_registration WHERE doc_id=?", (did,))
        try:
            if dv["stored_path"] and os.path.exists(dv["stored_path"]):
                os.remove(dv["stored_path"])
        except Exception:
            pass
        con.execute("DELETE FROM document_vault WHERE id=?", (did,))
        _audit(con, "document", sid, "delete", dv["doc_type"], "", actor)
    con.commit()
    con.close()
    return sid


def registrations_for_doc(con, doc_id):
    return con.execute("SELECT * FROM degree_registration WHERE doc_id=? ORDER BY id",
                       (doc_id,)).fetchall()


def add_registration(doc_id, staff_id, council, reg_no, filename, data, actor):
    """A council registration for a degree — with its own certificate document.
    File is optional (add the reg now, upload the certificate when it arrives)."""
    stored = orig = None
    ispdf = 1
    if data and filename:
        body, ext, ispdf = _to_pdf(data, filename)
        sdir = os.path.join(VAULT_DIR, str(staff_id), "reg")
        os.makedirs(sdir, exist_ok=True)
        stored = os.path.join(sdir, "%s.%s" % (uuid.uuid4().hex, ext))
        with open(stored, "wb") as f:
            f.write(body)
        try:
            os.chmod(stored, 0o600)
        except Exception:
            pass
        orig = filename
    con = get_db()
    con.execute("INSERT INTO degree_registration(doc_id,staff_id,council,reg_no,"
                "stored_path,original_name,is_pdf,added_by,added_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (doc_id, staff_id, council, reg_no, stored, orig, ispdf, actor, _now()))
    _audit(con, "registration", staff_id, "add", "", "%s %s" % (council, reg_no), actor)
    con.commit()
    con.close()


def delete_registration(rid, actor):
    con = get_db()
    r = con.execute("SELECT * FROM degree_registration WHERE id=?", (rid,)).fetchone()
    sid = r["staff_id"] if r else None
    if r:
        try:
            if r["stored_path"] and os.path.exists(r["stored_path"]):
                os.remove(r["stored_path"])
        except Exception:
            pass
        con.execute("DELETE FROM degree_registration WHERE id=?", (rid,))
        _audit(con, "registration", sid, "delete", r["council"], "", actor)
    con.commit()
    con.close()
    return sid


def _to_pdf(data, filename):
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return data, "pdf", 1
    if ext in _IMG_EXT:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(data)).convert("RGB")
            out = io.BytesIO()
            img.save(out, format="PDF")
            return out.getvalue(), "pdf", 1
        except Exception:
            return data, (ext or "bin"), 0
    return data, (ext or "bin"), 0


def save_document(sid, doc_type, filename, data, note, actor,
                  sub_type=None, council=None, reg_no=None):
    if doc_type not in DOC_TYPES:
        doc_type = "other"
    body, ext, is_pdf = _to_pdf(data, filename or "file")
    sdir = os.path.join(VAULT_DIR, str(sid))
    os.makedirs(sdir, exist_ok=True)
    stored = os.path.join(sdir, "%s.%s" % (uuid.uuid4().hex, ext))
    with open(stored, "wb") as f:
        f.write(body)
    try:
        os.chmod(stored, 0o600)
    except Exception:
        pass
    con = get_db()
    con.execute("INSERT INTO document_vault(staff_id,doc_type,original_name,stored_path,"
                "is_pdf,sub_type,council_registered,reg_no,note,uploaded_by,uploaded_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (sid, doc_type, filename, stored, is_pdf, sub_type, council, reg_no,
                 note, actor, _now()))
    _audit(con, "document", sid, "upload", "", "%s %s" % (doc_type, filename), actor)
    con.commit()
    con.close()
    return stored

# ---------------------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------------------
HEAD = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Staff Daily Register</title>
<style>
:root{--bg:#0f2233;--card:#16324a;--ink:#eaf2fa;--muted:#9fb6cc;--blue:#3b82f6;
 --green:#22c55e;--amber:#f59e0b;--red:#ef4444;--line:#274b66;--shadow:0 2px 10px rgba(0,0,0,.25)}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
 background:var(--bg);color:var(--ink);line-height:1.4;min-height:100vh}
.wrap{max-width:1000px;margin:0 auto;padding:16px 14px 48px}
.head{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:6px 0 12px}
.head h1{font-size:18px;margin:0;color:#fff}.head .sub{font-size:12px;color:var(--muted)}
.datebar{display:flex;align-items:center;gap:8px;margin:8px 0 14px;flex-wrap:wrap}
.datebar a{background:var(--card);border:1px solid var(--line);color:var(--ink);
 border-radius:10px;padding:8px 12px;text-decoration:none;font-size:14px}
.datebar input[type=date]{background:#0b1b29;border:2px solid var(--blue);color:#fff;border-radius:10px;padding:8px 10px;font-size:15px}
.pill{font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px}
.pill.draft{background:rgba(245,158,11,.18);color:#fcd34d}
.pill.approved{background:rgba(34,197,94,.18);color:#86efac}
.pill.empty{background:rgba(159,182,204,.15);color:#c9d6e3}
.pill.holiday{background:rgba(59,130,246,.18);color:#93c5fd}
.allclear{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--line);
 border-radius:12px;padding:14px 16px;margin:6px 0 14px}
.allclear input{width:24px;height:24px;accent-color:var(--green)}
.allclear label{font-size:15px;font-weight:600}
.allclear .hint{font-size:12px;color:var(--muted);margin-left:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:7px 6px;text-align:left;vertical-align:middle}
th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
td.nm{font-weight:600;white-space:nowrap}
select,input[type=number]{background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:6px 6px;font-size:13px}
input[type=number]{width:56px}
input[type=checkbox].cb{width:18px;height:18px;accent-color:var(--blue)}
.gate{font-size:10px;color:var(--muted)}
.tbl.greyed{opacity:.35;pointer-events:none;filter:saturate(.3)}
.btn{display:inline-block;border:none;border-radius:12px;padding:12px 18px;font-size:15px;font-weight:600;cursor:pointer;color:#fff;background:var(--blue)}
.btn.green{background:var(--green)}.btn.ghost{background:var(--card);border:1px solid var(--line);color:var(--ink)}
.btn:disabled{opacity:.5;cursor:not-allowed}
.bar{margin-top:16px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.note{color:var(--muted);font-size:12px;margin-top:8px}
.msg{padding:10px 12px;border-radius:10px;margin:10px 0;font-size:13px}
.msg.ok{background:rgba(34,197,94,.14);color:#bbf7d0}.msg.err{background:rgba(239,68,68,.14);color:#fecaca}
.tblwrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0}
.foot{margin-top:22px;text-align:center}.foot a{color:var(--muted);font-size:12px;text-decoration:none}
.login{max-width:340px;margin:9vh auto 0;text-align:center;padding:0 16px}
.login h1{font-size:20px;color:#fff;margin:0 0 4px}.login p{font-size:13px;color:var(--muted);margin:0 0 20px}
.login input{width:100%;font-size:18px;padding:13px;border:2px solid var(--blue);border-radius:12px;background:#0b1b29;color:#fff;outline:none;margin-bottom:10px;text-align:center}
.login button{width:100%;font-size:16px;font-weight:600;padding:13px;border:none;border-radius:12px;background:var(--blue);color:#fff;cursor:pointer}
.err{color:#fca5a5;font-size:13px;margin-top:10px;min-height:18px}
@media(max-width:480px){.wrap{padding:14px 12px 36px}th,td{padding:6px 4px}}
</style></head><body>
"""

LOGIN_HTML = HEAD + """
<div class="login">
  <h1>Staff Daily Register</h1><p>Sign in (or use the clinic portal single sign-on)</p>
  <form method="POST" action="{{ prefix }}/login" autocomplete="off">
    <input name="user" type="text" autocapitalize="none" autocorrect="off" autofocus placeholder="username">
    <input name="password" type="password" placeholder="password">
    <button type="submit">Sign in</button>
  </form>
  <div class="err">{{ error or "" }}</div>
</div></body></html>
"""

NO_ACCESS_HTML = HEAD + """
<div class="login">
  <h1>No access</h1>
  <p>Signed in as <b>{{ who.user }}</b>{% if who.role %} ({{ who.role }}){% endif %},
     but this account has no active role in the Staff Register{% if who.role=='inactive' %}
     — your maker access is provisioned but not yet activated{% endif %}.</p>
  <a class="btn ghost" href="{{ url_prefix }}/logout">Sign out</a>
</div></body></html>
"""

REGISTER_HTML = HEAD + """
<div class="wrap">
  <div class="head"><h1>🗓️ Staff Daily Register</h1>
    <span class="sub">Signed in as {{ who.user }} ({{ who.role }})</span></div>
  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}

  <div class="datebar">
    <a href="{{ prefix }}/?d={{ prev }}">◀ {{ prev }}</a>
    <form method="GET" action="{{ prefix }}/" style="display:inline">
      <input type="date" name="d" value="{{ d }}" onchange="this.form.submit()"></form>
    <a href="{{ prefix }}/?d={{ next }}">{{ next }} ▶</a>
    <span class="pill {{ status }}">{{ status|upper }}</span>
    {% if holiday %}<span class="pill holiday">CLINIC HOLIDAY</span>{% endif %}
  </div>

  {% if holiday %}
    <div class="card">🏖️ <b>{{ d }} is a clinic holiday{% if holiday_name %} — {{ holiday_name }}{% endif %}.</b>
      No duty, no fines.
      {% if caps.override %}<a class="btn ghost" href="{{ prefix }}/festivals" style="margin-left:10px">Manage festivals & holidays</a>{% endif %}
    </div>
  {% else %}

  {% if festival_name %}<div class="msg ok">🎉 <b>{{ d }} — {{ festival_name }}.</b>
     Any staff marked "on leave" today counts as a <b>festival leave</b>.</div>{% endif %}

  <form method="POST" action="{{ prefix }}/save" id="regform">
   <input type="hidden" name="d" value="{{ d }}">
   {% set locked = (status=='approved') and not caps.override %}
   <div class="allclear">
     <input type="checkbox" id="allclear" name="all_clear" {{ 'checked' if all_clear }}
            {{ 'disabled' if locked }} onchange="toggleClear()">
     <label for="allclear">✅ All clear — nothing to report for {{ d }}</label>
     <span class="hint">tick this on a normal day; the grid below greys out</span>
   </div>

   <div class="tblwrap"><div class="tbl" id="grid" data-locked="{{ 1 if locked else 0 }}">
    <table>
    <thead><tr>
      <th>Staff</th><th>Leave / absence{% if festival_name %} 🎉{% endif %}</th><th>Late 60+ / approved by</th>
      <th>Dress</th><th>I-card</th><th>Cover</th><th>Outstn</th>
    </tr></thead>
    <tbody>
    {% for s in staff %}
      <tr class="srow">
        <td class="nm">{{ s.name }}{% if s.bio_absent %} <span class="pill empty" title="no biometric punch">no punch</span>{% endif %}</td>
        <td><select class="lv" name="s{{ s.staff_id }}_leave" {{ 'disabled' if locked }} onchange="rowSync(this)">
              <option value="" {{ 'selected' if s.leave_sel=='' }}>— present</option>
              <option value="not_approved" {{ 'selected' if s.leave_sel=='not_approved' }}>Absent — not approved</option>
              <option value="bhawna" {{ 'selected' if s.leave_sel=='bhawna' }}>Leave — appr Dr Bhawna</option>
              <option value="manoj" {{ 'selected' if s.leave_sel=='manoj' }}>Leave — appr Dr Manoj</option>
            </select>{% if festival_name %} <span class="gate">fest</span>{% endif %}</td>
        <td>{% if s.mx %}<span class="gate">n/a</span>{% else %}
            <select class="late" name="s{{ s.staff_id }}_late" {{ 'disabled' if locked }}>
              <option value="">—</option>
              <option value="not_approved" {{ 'selected' if s.late_sel=='not_approved' }}>Not approved</option>
              <option value="bhawna" {{ 'selected' if s.late_sel=='bhawna' }}>Approved by Dr Bhawna</option>
              <option value="manoj" {{ 'selected' if s.late_sel=='manoj' }}>Approved by Dr Manoj</option>
            </select>{% endif %}</td>
        <td>{% if s.mx %}<span class="gate">—</span>
            {% elif s.uniform_ok %}<input class="cb dress" type="checkbox" name="s{{ s.staff_id }}_dress" {{ 'checked' if s.dress_sel }} {{ 'disabled' if locked }}>
            {% else %}<span class="gate">{{ 'paused' if s.uniform_issued else 'not issued' }}</span>{% endif %}</td>
        <td>{% if s.mx %}<span class="gate">—</span>
            {% elif s.icard_ok %}<input class="cb icard" type="checkbox" name="s{{ s.staff_id }}_icard" {{ 'checked' if s.icard_sel }} {{ 'disabled' if locked }}>
            {% else %}<span class="gate">{{ 'paused' if s.icard_issued else 'not issued' }}</span>{% endif %}</td>
        <td>{% if s.cover_eligible %}
            <select class="cov" name="s{{ s.staff_id }}_extra" {{ 'disabled' if locked }}>
              <option value="0" {{ 'selected' if s.extra_sel=='0' }}>No</option>
              <option value="1" {{ 'selected' if s.extra_sel=='1' }}>Yes</option>
            </select>{% else %}<span class="gate">—</span>{% endif %}</td>
        <td>{% if s.outstation_eligible %}
            <select class="outs" name="s{{ s.staff_id }}_outstation" {{ 'disabled' if locked }} onchange="rowSync(this)">
              <option value="0" {{ 'selected' if s.outstation_sel=='0' }}>No</option>
              <option value="1" {{ 'selected' if s.outstation_sel=='1' }}>Yes</option>
            </select>{% else %}<span class="gate">—</span>{% endif %}</td>
      </tr>
    {% endfor %}
    </tbody></table>
   </div></div>

   <div class="bar">
     {% if caps.maker and not locked %}<button class="btn" type="submit">💾 Save the day</button>{% endif %}
   </div>
  </form>

  {% if caps.check and status=='draft' %}
   <form method="POST" action="{{ prefix }}/approve" class="bar">
     <input type="hidden" name="d" value="{{ d }}">
     <button class="btn green" type="submit" {{ 'disabled' if not can_approve }}>✔ Approve {{ d }}</button>
     {% if not can_approve %}<span class="note">You entered this date — an override (doctor) must approve it.</span>{% endif %}
   </form>
  {% endif %}
  {% if caps.override and status=='approved' %}
   <form method="POST" action="{{ prefix }}/reverse" class="bar"
         onsubmit="return confirm('Reverse this approved date back to draft?');">
     <input type="hidden" name="d" value="{{ d }}">
     <button class="btn ghost" type="submit">↩ Reverse (override)</button>
   </form>
  {% endif %}
  {% endif %}

  <div class="bar" style="margin-top:18px">
    {% if caps.maker %}<a class="btn ghost" href="{{ prefix }}/staff" target="_blank" rel="noopener">👤 Staff records</a>{% endif %}
    {% if caps.maker %}<a class="btn ghost" href="{{ prefix }}/leave" target="_blank" rel="noopener">🌴 Sanctioned leave</a>{% endif %}
    {% if caps.salary %}<a class="btn ghost" href="{{ prefix }}/salary" target="_blank" rel="noopener">💰 Salary reconciliation</a>{% endif %}
    {% if caps.override %}<a class="btn ghost" href="{{ prefix }}/festivals" target="_blank" rel="noopener">🎉 Festivals &amp; holidays</a>{% endif %}
  </div>

  <div class="foot"><a href="{{ prefix }}/logout">Sign out</a> ·
    <span>presence/absence = biometric · this register = leave &amp; exceptions</span></div>
</div>
<script>
function _grey(list,off){
  for(var i=0;i<list.length;i++){var e=list[i];if(!e)continue;
    e.disabled=off;
    if(off){ if(e.type==='checkbox')e.checked=false;
             else if(e.tagName==='SELECT')e.value=(e.className.indexOf('cov')>=0?'0':''); }
  }
}
function rowSync(el){
  var g=document.getElementById('grid'); if(g&&g.dataset.locked==='1')return;
  var tr=el.closest('tr'); if(!tr)return;
  var lv=tr.querySelector('.lv'), outs=tr.querySelector('.outs');
  var late=tr.querySelector('.late'), dress=tr.querySelector('.dress');
  var icard=tr.querySelector('.icard'), cov=tr.querySelector('.cov');
  var leaveVal=lv?lv.value:'', outVal=outs?outs.value:'0';
  if(outVal==='1'){                     // outstation Yes = present for salary; wins
    if(lv){lv.value='';lv.disabled=true;}
    _grey([late,dress,icard,cov],true);
  }else{
    if(lv)lv.disabled=false;
    _grey([late,dress,icard,cov], leaveVal!=='');   // any leave/absent greys presence items
    if(outs)outs.disabled=(leaveVal==='bhawna'||leaveVal==='manoj'); // approved leave vs outstation
  }
}
function rowSyncAll(){
  var rows=document.querySelectorAll('#grid tr.srow');
  for(var i=0;i<rows.length;i++){
    var o=rows[i].querySelector('.outs');
    if(o&&o.value==='1'){rowSync(o);continue;}
    var lv=rows[i].querySelector('.lv'); if(lv)rowSync(lv);
  }
}
function toggleClear(){
  var on=document.getElementById('allclear').checked;
  var g=document.getElementById('grid'); if(!g)return;
  g.classList.toggle('greyed',on);
  var el=g.querySelectorAll('select,input');
  for(var i=0;i<el.length;i++){el[i].disabled=on;}
  if(!on)rowSyncAll();
}
document.addEventListener('DOMContentLoaded',function(){toggleClear();rowSyncAll();});
</script>
</body></html>
"""

FESTIVALS_HTML = HEAD + """
<div class="wrap">
  <div class="head"><h1>🎉 Festivals & Holidays</h1>
    <span class="sub">{{ who.user }} ({{ who.role }})</span></div>
  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}
  <p class="note">Prepare the year's list in advance. <b>Clinic closed</b> = a full closure
    (e.g. Holi): no duty, no fines, no leave used. <b>Not closed</b> = a normal working day
    that also counts as a festival — any staff on leave that day uses a <b>festival leave</b>
    (2/year, unused ones encashed).</p>

  <form method="POST" action="{{ prefix }}/festival" class="card">
    <b>Add / update an entry</b>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:10px">
      <input type="date" name="fest_date" required
             style="background:#0b1b29;border:2px solid var(--blue);color:#fff;border-radius:10px;padding:9px 10px">
      <input name="name" placeholder="name (e.g. Diwali)" required
             style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:10px;padding:9px 10px">
      <label style="display:flex;align-items:center;gap:6px;font-size:14px">
        <input class="cb" type="checkbox" name="closed"> clinic closed (holiday)</label>
      <button class="btn" type="submit">Save entry</button>
    </div>
  </form>

  <div class="tblwrap"><table>
    <thead><tr><th>Date</th><th>Name</th><th>Type</th><th></th></tr></thead>
    <tbody>
    {% for f in fests %}
      <tr>
        <td class="nm">{{ f.fest_date }}</td>
        <td>{{ f.name }}</td>
        <td>{% if f.clinic_closed %}<span class="pill holiday">CLINIC CLOSED</span>
            {% else %}<span class="pill draft">FESTIVAL (leave)</span>{% endif %}</td>
        <td><form method="POST" action="{{ prefix }}/festival"
              onsubmit="return confirm('Remove {{ f.fest_date }}?');">
              <input type="hidden" name="fest_date" value="{{ f.fest_date }}">
              <input type="hidden" name="action" value="del">
              <button class="btn ghost" type="submit">Remove</button></form></td>
      </tr>
    {% else %}
      <tr><td colspan="4" class="note">No festivals or holidays added yet.</td></tr>
    {% endfor %}
    </tbody>
  </table></div>

  <div class="foot"><a href="{{ prefix }}/">← Back to the daily register</a></div>
</div></body></html>
"""

LEAVE_HTML = HEAD + """
<div class="wrap">
  <div class="head"><h1>\U0001F334 Sanctioned leave</h1>
    <span class="sub">{{ who.user }} ({{ who.role }})</span></div>
  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}
  <p class="note">Enter a continuous leave once (from\u2013to). A <b>checker</b> approves it, then it
    <b>auto-fills</b> the daily register's leave for that staff on every day of the range \u2014 no
    re-tapping. The kind (discretionary / festival) is still worked out per date.</p>

  {% if caps.maker %}
  <form method="POST" action="{{ prefix }}/leave/add" class="card">
    <b>Add a sanctioned leave</b>
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:10px">
      <select name="sid" required
              style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:10px;padding:9px 10px">
        <option value="">\u2014 staff \u2014</option>
        {% for s in staff %}<option value="{{ s.staff_id }}">{{ s.name }}</option>{% endfor %}
      </select>
      <label class="note">from <input type="date" name="from_date" required
             style="background:#0b1b29;border:2px solid var(--blue);color:#fff;border-radius:10px;padding:9px 10px"></label>
      <label class="note">to <input type="date" name="to_date" required
             style="background:#0b1b29;border:2px solid var(--blue);color:#fff;border-radius:10px;padding:9px 10px"></label>
      <select name="approved_by" required
              style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:10px;padding:9px 10px">
        <option value="">\u2014 sanctioned by \u2014</option>
        <option value="bhawna">Dr Bhawna</option>
        <option value="manoj">Dr Manoj</option>
      </select>
      <input name="note" placeholder="note (optional)"
             style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:10px;padding:9px 10px">
      <button class="btn" type="submit">Add (pending approval)</button>
    </div>
  </form>
  {% endif %}

  <div class="tblwrap"><table>
    <thead><tr><th>Staff</th><th>From</th><th>To</th><th>Sanctioned by</th><th>Status</th><th></th></tr></thead>
    <tbody>
    {% for r in rows %}
      <tr>
        <td class="nm">{{ r.name }}</td>
        <td>{{ r.from_date }}</td><td>{{ r.to_date }}</td>
        <td>Dr {{ 'Bhawna' if r.approved_by=='bhawna' else 'Manoj' }}</td>
        <td>{% if r.status=='approved' %}<span class="pill approved">APPROVED</span><div class="gate">by {{ r.checker_user }}</div>
            {% elif r.status=='cancelled' %}<span class="pill empty">CANCELLED</span>
            {% else %}<span class="pill draft">PENDING</span>{% endif %}</td>
        <td>
          {% if r.status=='draft' and caps.check %}
            <form method="POST" action="{{ prefix }}/leave/approve" style="display:inline">
              <input type="hidden" name="id" value="{{ r.id }}">
              <button class="btn green" type="submit" {{ 'disabled' if not r.can_approve }}>\u2714 Approve</button>
            </form>
            {% if not r.can_approve %}<span class="gate">you entered this</span>{% endif %}
          {% endif %}
          {% if r.status!='cancelled' and caps.override %}
            <form method="POST" action="{{ prefix }}/leave/cancel" style="display:inline"
                  onsubmit="return confirm('Cancel this leave range?');">
              <input type="hidden" name="id" value="{{ r.id }}">
              <button class="btn ghost" type="submit">Cancel</button>
            </form>
          {% endif %}
        </td>
      </tr>
    {% else %}
      <tr><td colspan="6" class="note">No sanctioned leaves yet.</td></tr>
    {% endfor %}
    </tbody>
  </table></div>

  <div class="foot"><a href="{{ prefix }}/">\u2190 Back to the daily register</a></div>
</div></body></html>
"""

STAFF_LIST_HTML = HEAD + """
<div class="wrap">
  <div class="head"><h1>👤 Staff Records</h1>
    <span class="sub">{{ who.user }} ({{ who.role }})</span></div>
  <p class="note">Uniform / i-card issuance{% if caps.docs %} and staff documents{% endif %}.
     Pick a staff member.</p>
  <div class="tblwrap"><table>
    <thead><tr><th>Staff</th><th>Uniform</th><th>I-card</th><th></th></tr></thead>
    <tbody>
    {% for s in staff %}
      <tr>
        <td class="nm">{{ s.name }}</td>
        <td>{% if s.uniform_ok %}<span class="pill approved">OK</span>
            {% elif s.uniform_issued %}<span class="pill draft">PAUSED</span>
            {% elif s.mx %}<span class="gate">n/a</span>
            {% else %}<span class="pill empty">none</span>{% endif %}</td>
        <td>{% if s.icard_ok %}<span class="pill approved">OK</span>
            {% elif s.icard_issued %}<span class="pill draft">PAUSED</span>
            {% elif s.mx %}<span class="gate">n/a</span>
            {% else %}<span class="pill empty">none</span>{% endif %}</td>
        <td><a class="btn ghost" href="{{ prefix }}/staff/{{ s.staff_id }}">Open</a></td>
      </tr>
    {% endfor %}
    </tbody>
  </table></div>
  <div class="foot"><a href="{{ prefix }}/">← Back to the daily register</a></div>
</div></body></html>
"""

STAFF_RECORD_HTML = HEAD + """
<div class="wrap">
  <div class="head"><h1>👤 {{ s.name }}</h1>
    <span class="sub">{{ who.user }} ({{ who.role }})</span></div>
  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}

  <div class="card">
    <b>Uniform &amp; I-card issuance</b>
    <p class="note">A fine for dress/i-card is only possible once the item is
       <b>issued &amp; approved</b> here, and is <b>paused</b> during any open window below.</p>
    <div class="tblwrap"><table>
      <thead><tr><th>Item</th><th>Season</th><th>Issued</th><th>Status</th><th></th></tr></thead>
      <tbody>
      {% for i in issuance %}
        <tr><td class="nm">{{ i.item_type }}</td><td>{{ i.season or '—' }}</td>
            <td>{{ i.issued_date }}</td>
            <td>{% if i.status=='approved' %}<span class="pill approved">approved</span>
                {% else %}<span class="pill draft">pending</span>{% endif %}</td>
            <td>{% if i.status!='approved' and caps.check %}
                <form method="POST" action="{{ prefix }}/issuance/approve">
                  <input type="hidden" name="iid" value="{{ i.id }}">
                  <input type="hidden" name="sid" value="{{ s.staff_id }}">
                  <button class="btn green" type="submit">Approve</button></form>{% endif %}</td>
        </tr>
      {% else %}<tr><td colspan="5" class="note">Nothing issued yet.</td></tr>{% endfor %}
      </tbody>
    </table></div>
    {% if caps.maker and not s.mx %}
    <form method="POST" action="{{ prefix }}/issuance/add" style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <input type="hidden" name="sid" value="{{ s.staff_id }}">
      <select name="item" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
        <option value="uniform">uniform</option><option value="icard">i-card</option></select>
      <select name="season" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
        <option value="">— season —</option><option value="summer">summer</option><option value="winter">winter</option></select>
      <input type="date" name="issued_date" value="{{ today }}" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      <button class="btn" type="submit">Issue / re-issue</button>
    </form>{% endif %}
  </div>

  <div class="card">
    <b>Lost / damaged — fine pauses</b>
    <p class="note">Open a window while an item is being replaced; the dress/i-card fine
       is paused for those dates until you close it on re-issue.</p>
    <div class="tblwrap"><table>
      <thead><tr><th>Item</th><th>From</th><th>To</th><th>Reason</th><th></th></tr></thead>
      <tbody>
      {% for p in pauses %}
        <tr><td class="nm">{{ p.item_type }}</td><td>{{ p.from_date }}</td>
            <td>{{ p.to_date or 'open' }}</td><td>{{ p.reason or '—' }}</td>
            <td>{% if not p.to_date and caps.check %}
                <form method="POST" action="{{ prefix }}/pause/close" style="display:flex;gap:6px">
                  <input type="hidden" name="pid" value="{{ p.id }}">
                  <input type="hidden" name="sid" value="{{ s.staff_id }}">
                  <input type="date" name="to_date" value="{{ today }}" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:6px">
                  <button class="btn ghost" type="submit">Close</button></form>{% endif %}</td>
        </tr>
      {% else %}<tr><td colspan="5" class="note">No pause windows.</td></tr>{% endfor %}
      </tbody>
    </table></div>
    {% if caps.maker and not s.mx %}
    <form method="POST" action="{{ prefix }}/pause/add" style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <input type="hidden" name="sid" value="{{ s.staff_id }}">
      <select name="item" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
        <option value="uniform">uniform</option><option value="icard">i-card</option></select>
      <input type="date" name="from_date" value="{{ today }}" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      <input name="reason" placeholder="reason (lost / damaged)" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      <button class="btn" type="submit">Start pause</button>
    </form>{% endif %}
  </div>

  {% if caps.docs %}
  <div class="card">
    <b>🧾 Profile</b>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0">
      <span class="pill {{ 'approved' if summary.id_proof else 'empty' }}">{{ '✓' if summary.id_proof else '✗' }} ID proof</span>
      <span class="pill {{ 'approved' if summary.address_proof else 'empty' }}">{{ '✓' if summary.address_proof else '✗' }} Address proof</span>
      <span class="pill {{ 'approved' if summary.qualification else 'empty' }}">{{ '✓' if summary.qualification else '✗' }} Qualification</span>
    </div>
    <form method="POST" action="{{ prefix }}/profile/save" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <input type="hidden" name="sid" value="{{ s.staff_id }}">
      <label class="note">Date of joining
        <input type="date" name="join_date" value="{{ s.join_date if s.join_date!='2000-01-01' else '' }}" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px"></label>
      <label class="note">Last working day (blank = active)
        <input type="date" name="last_working" value="{{ s.last_working or '' }}" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px"></label>
      <div class="note" style="grid-column:1/3">Job role(s) — tick all that apply (can be mixed)
        <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:6px">
          {% for jr in job_roles_list %}
          <label style="display:flex;align-items:center;gap:5px;color:var(--ink);font-size:13px">
            <input class="cb" type="checkbox" name="role" value="{{ jr }}" {{ 'checked' if jr in role_checked }}> {{ jr }}</label>
          {% endfor %}
        </div>
        <input name="role_custom" value="{{ role_custom }}" placeholder="other role(s) — free text"
               style="width:100%;margin-top:8px;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      </div>
      <label class="note" style="grid-column:1/3">Current address
        <textarea name="current_address" rows="2" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">{{ profile.current_address if profile and profile.current_address else '' }}</textarea></label>
      <label class="note" style="grid-column:1/3">Permanent address
        <textarea name="permanent_address" rows="2" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">{{ profile.permanent_address if profile and profile.permanent_address else '' }}</textarea></label>
      <label class="note">Emergency contact name
        <input name="emergency_name" value="{{ profile.emergency_name if profile else '' }}" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px"></label>
      <label class="note">Emergency contact phone
        <input name="emergency_phone" value="{{ profile.emergency_phone if profile else '' }}" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px"></label>
      <label class="note">Family member name (for Aadhaar on file)
        <input name="family_name" value="{{ profile.family_name if profile else '' }}" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px"></label>
      <label class="note">Family member relation
        <select name="family_relation" style="width:100%;background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
          <option value="">—</option>
          {% for fr in family_relations %}<option value="{{ fr }}" {{ 'selected' if profile and profile.family_relation==fr }}>{{ fr }}</option>{% endfor %}
        </select></label>
      <div style="grid-column:1/3"><button class="btn" type="submit">Save profile</button></div>
    </form>
  </div>

  <div class="card">
    <b>📁 Documents</b>
    <p class="note">Stored on the clinic server; images auto-convert to PDF.
       {% if caps.delete %}You can delete records.{% else %}Only the doctor can delete records.{% endif %}</p>
    <div class="tblwrap"><table>
      <thead><tr><th>Type</th><th>Details</th><th>File</th><th>Uploaded</th><th></th></tr></thead>
      <tbody>
      {% for dv in docs %}
        <tr><td class="nm">{{ doc_labels.get(dv.doc_type, dv.doc_type) }}</td>
            <td>{% if dv.sub_type %}{{ dv.sub_type }}{% endif %}
                {% if dv.council_registered==1 %}<span class="pill approved">council-reg{% if dv.reg_no %} {{ dv.reg_no }}{% endif %}</span>
                {% elif dv.council_registered==0 %}<span class="pill empty">not registered</span>{% endif %}
                {% if dv.note %}<span class="gate">· {{ dv.note }}</span>{% endif %}</td>
            <td>{{ dv.original_name or '—' }}</td>
            <td>{{ dv.uploaded_ts }}</td>
            <td style="display:flex;gap:6px">
              <a class="btn ghost" href="{{ prefix }}/doc/{{ dv.id }}/download">Download</a>
              {% if caps.delete %}<form method="POST" action="{{ prefix }}/doc/delete"
                    onsubmit="return confirm('Delete this document permanently?');">
                    <input type="hidden" name="did" value="{{ dv.id }}">
                    <input type="hidden" name="sid" value="{{ s.staff_id }}">
                    <button class="btn ghost" style="border-color:#7f1d1d;color:#fca5a5" type="submit">Delete</button></form>{% endif %}
            </td>
        </tr>
      {% else %}<tr><td colspan="5" class="note">No documents yet.</td></tr>{% endfor %}
      </tbody>
    </table></div>

    <form method="POST" action="{{ prefix }}/doc/upload" enctype="multipart/form-data"
          style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <input type="hidden" name="sid" value="{{ s.staff_id }}">
      <select name="doc_type" id="doctype" onchange="degToggle()"
              style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
        {% for grp, items in doc_groups %}<optgroup label="{{ grp }}">
          {% for t in items %}<option value="{{ t }}">{{ doc_labels.get(t, t) }}</option>{% endfor %}
        </optgroup>{% endfor %}
      </select>
      <span id="degfields" style="display:none;gap:8px;align-items:center">
        <select name="sub_type" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
          {% for st in degree_subtypes %}<option value="{{ st }}">{{ st }}</option>{% endfor %}</select>
        <span class="gate">add council registration(s) below after uploading</span>
      </span>
      <input type="file" name="file" required style="color:var(--ink);font-size:12px">
      <input name="note" placeholder="note (optional)" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      <button class="btn" type="submit">Upload</button>
    </form>
    <script>
    function degToggle(){var v=document.getElementById('doctype').value;
      document.getElementById('degfields').style.display=(v==='professional_degree')?'inline-flex':'none';}
    document.addEventListener('DOMContentLoaded',degToggle);
    </script>
  </div>

  <div class="card">
    <b>🎓 Professional degrees &amp; council registrations</b>
    <p class="note">Each degree can be registered at one or more councils; every registration
       has its own certificate. A degree with no registration is flagged.</p>
    {% for dg in degrees %}
      <div style="border:1px solid var(--line);border-radius:10px;padding:12px;margin:10px 0">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <b>{{ dg.sub_type or 'Degree' }}</b>
          <span class="gate">{{ dg.original_name or '' }}</span>
          {% if dg.regs %}<span class="pill approved">registered ×{{ dg.regs|length }}</span>
          {% else %}<span class="pill empty">NOT registered</span>{% endif %}
          <a class="btn ghost" href="{{ prefix }}/doc/{{ dg.id }}/download">Degree PDF</a>
          {% if caps.delete %}<form method="POST" action="{{ prefix }}/doc/delete"
                onsubmit="return confirm('Delete this degree and all its registrations?');">
                <input type="hidden" name="did" value="{{ dg.id }}"><input type="hidden" name="sid" value="{{ s.staff_id }}">
                <button class="btn ghost" style="border-color:#7f1d1d;color:#fca5a5" type="submit">Delete degree</button></form>{% endif %}
        </div>
        <div class="tblwrap" style="margin-top:8px"><table>
          <thead><tr><th>Council</th><th>Reg no.</th><th>Certificate</th><th></th></tr></thead>
          <tbody>
          {% for rg in dg.regs %}
            <tr><td class="nm">{{ rg.council or '—' }}</td><td>{{ rg.reg_no or '—' }}</td>
                <td>{% if rg.stored_path %}<a class="btn ghost" href="{{ prefix }}/registration/{{ rg.id }}/download">Download</a>
                    {% else %}<span class="gate">no file yet</span>{% endif %}</td>
                <td>{% if caps.delete %}<form method="POST" action="{{ prefix }}/registration/delete"
                      onsubmit="return confirm('Delete this registration?');">
                      <input type="hidden" name="rid" value="{{ rg.id }}"><input type="hidden" name="sid" value="{{ s.staff_id }}">
                      <button class="btn ghost" style="border-color:#7f1d1d;color:#fca5a5" type="submit">Delete</button></form>{% endif %}</td>
            </tr>
          {% else %}<tr><td colspan="4" class="note">No registration yet.</td></tr>{% endfor %}
          </tbody>
        </table></div>
        <form method="POST" action="{{ prefix }}/registration/add" enctype="multipart/form-data"
              style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input type="hidden" name="doc_id" value="{{ dg.id }}"><input type="hidden" name="sid" value="{{ s.staff_id }}">
          <input name="council" placeholder="council (e.g. UP Paramedical)" required style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
          <input name="reg_no" placeholder="registration no." style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
          <input type="file" name="file" style="color:var(--ink);font-size:12px">
          <button class="btn" type="submit">Add registration</button>
        </form>
      </div>
    {% else %}<p class="note">No professional degrees uploaded yet — add one under Documents.</p>{% endfor %}
  </div>

  <div class="card">
    <b>📦 Issued assets</b>
    <p class="note">Mobile phone, bicycle, bike etc. issued to this staff member — with issue date and return.</p>
    <div class="tblwrap"><table>
      <thead><tr><th>Type</th><th>Identifier</th><th>Details</th><th>Issued</th><th>Status</th><th></th></tr></thead>
      <tbody>
      {% for a in assets %}
        <tr>
          <td class="nm">{{ asset_labels.get(a.asset_type, a.asset_type) }}</td>
          <td>{{ a.identifier or '—' }}</td>
          <td>{{ a.descr or '—' }}{% if a.note %} <span class="gate">· {{ a.note }}</span>{% endif %}</td>
          <td>{{ a.issued_date or '—' }}</td>
          <td>{% if a.status=='returned' %}<span class="pill empty">returned {{ a.returned_date or '' }}</span>
              {% else %}<span class="pill approved">in use</span>{% endif %}</td>
          <td style="display:flex;gap:6px">
            {% if a.status!='returned' %}
            <form method="POST" action="{{ prefix }}/asset/return">
              <input type="hidden" name="aid" value="{{ a.id }}"><input type="hidden" name="sid" value="{{ s.staff_id }}">
              <input type="date" name="returned_date" value="{{ today }}" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:6px;padding:4px;font-size:12px">
              <button class="btn ghost" type="submit">Mark returned</button></form>
            {% endif %}
            {% if caps.delete %}<form method="POST" action="{{ prefix }}/asset/delete"
                  onsubmit="return confirm('Delete this asset record?');">
                  <input type="hidden" name="aid" value="{{ a.id }}"><input type="hidden" name="sid" value="{{ s.staff_id }}">
                  <button class="btn ghost" style="border-color:#7f1d1d;color:#fca5a5" type="submit">Delete</button></form>{% endif %}
          </td>
        </tr>
      {% else %}<tr><td colspan="6" class="note">No assets issued.</td></tr>{% endfor %}
      </tbody>
    </table></div>
    <form method="POST" action="{{ prefix }}/asset/add"
          style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <input type="hidden" name="sid" value="{{ s.staff_id }}">
      <select name="asset_type" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
        {% for val,lab in asset_types %}<option value="{{ val }}">{{ lab }}</option>{% endfor %}</select>
      <input name="identifier" placeholder="IMEI / cycle no / reg no" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      <input name="descr" placeholder="make / model / colour" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      <label class="note">issued <input type="date" name="issued_date" value="{{ today }}" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:6px"></label>
      <input name="note" placeholder="note (optional)" style="background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px">
      <button class="btn" type="submit">Issue asset</button>
    </form>
  </div>
  {% endif %}

  <div class="foot"><a href="{{ prefix }}/staff">← All staff</a> ·
    <a href="{{ prefix }}/">daily register</a></div>
</div></body></html>
"""
app = Flask(__name__)
app.secret_key = _load_secret_key()


@app.route(APP_PREFIX + "/login", methods=["GET", "POST"])
def login():
    if current_user(request):
        return redirect(APP_PREFIX + "/")
    error = ""
    if request.method == "POST":
        user = (request.form.get("user") or "").strip()
        pw = request.form.get("password") or ""
        role = _verify_local_login(user, pw)
        if role:
            session["sr_user"] = user
            session["sr_role"] = role
            return redirect(APP_PREFIX + "/")
        error = "Wrong username or password."
    return render_template_string(LOGIN_HTML, error=error, prefix=APP_PREFIX)


@app.route(APP_PREFIX + "/logout")
def logout():
    session.clear()
    return redirect(APP_PREFIX + "/login")


@app.route(APP_PREFIX + "/", methods=["GET"])
@app.route(APP_PREFIX, methods=["GET"])
@require(None)
def home():
    u = current_user(request)
    d = request.args.get("d", _today())
    if not _valid_date(d):
        d = _today()
    con = get_db()
    rows = day_rows(con, d)
    present_ids = biometric_present_ids(d)        # set of present staff_ids, or None if no feed
    bio_ok = present_ids is not None
    dec = []
    for s in staff_for_date(con, d):
        sid = s["staff_id"]
        sd = dict(s)
        sd["mx"] = bool(s["minutes_exempt"])
        sd["uniform_issued"] = con.execute(
            "SELECT 1 FROM issuance WHERE staff_id=? AND item_type='uniform' "
            "AND status='approved'", (sid,)).fetchone() is not None
        sd["icard_issued"] = con.execute(
            "SELECT 1 FROM issuance WHERE staff_id=? AND item_type='icard' "
            "AND status='approved'", (sid,)).fetchone() is not None
        sd["uniform_ok"] = issuance_ok(con, sid, "uniform", d)
        sd["icard_ok"] = issuance_ok(con, sid, "icard", d)
        sd["bio_absent"] = bool(bio_ok and sid not in present_ids)
        r = rows.get(sid)
        # LEAVE dropdown pre-selection: stored row first, else biometric default
        lv = ""
        if r:
            if (r["leave_approved_by"] or "") in ("bhawna", "manoj"):
                lv = r["leave_approved_by"]
            elif (r["absence_type"] or "") == "absent":
                lv = "not_approved"
        elif active_leave_for(con, sid, d):        # approved sanctioned-leave range (grid step 2)
            lv = active_leave_for(con, sid, d)
        elif sd["bio_absent"]:
            lv = "not_approved"          # absent per biometric, unclassified -> safe default
        sd["leave_sel"] = lv
        sd["outstation_sel"] = "1" if (r and r["outstation_nights"]) else "0"
        sd["extra_sel"] = "1" if (r and r["extra_duty"]) else "0"
        sd["dress_sel"] = bool(r and r["dress_improper"])
        sd["icard_sel"] = bool(r and r["icard_missing"])
        if r and (r["late_approved_by"] or "") in ("bhawna", "manoj"):
            sd["late_sel"] = r["late_approved_by"]
        elif r and r["late_flag"] == "not_informed":
            sd["late_sel"] = "not_approved"
        else:
            sd["late_sel"] = ""
        dec.append(sd)
    status = date_status(con, d)
    rr = review_row(con, d)
    all_clear = bool(rr and rr["state"] == "all_clear")
    holiday = is_holiday(con, d)
    hrow = con.execute("SELECT name FROM festival_day WHERE fest_date=?", (d,)).fetchone()
    holiday_name = hrow["name"] if (holiday and hrow) else ""
    fest = festival_on(con, d)
    festival_name = fest["name"] if fest else ""
    can_approve = can_check_approve(con, d, u["user"], u["caps"]["override"]) \
        if u["caps"]["check"] else False
    con.close()
    dt = datetime.datetime.strptime(d, "%Y-%m-%d").date()
    prev = (dt - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    nxt = (dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return render_template_string(
        REGISTER_HTML, who=u, caps=u["caps"], d=d, prev=prev, next=nxt,
        staff=dec, rows=rows, status=status, holiday=holiday, all_clear=all_clear,
        holiday_name=holiday_name, festival_name=festival_name, bio_ok=bio_ok,
        can_approve=can_approve, prefix=APP_PREFIX,
        msg=request.args.get("m", ""), msgcls=request.args.get("c", "ok"))


@app.route(APP_PREFIX + "/save", methods=["POST"])
@require("maker")
def save():
    u = current_user(request)
    d = request.form.get("d", _today())
    if not _valid_date(d):
        return redirect(APP_PREFIX + "/")
    all_clear = bool(request.form.get("all_clear"))
    try:
        n = save_maker(d, all_clear, request.form, u["user"])
        m = "Marked+all-clear+for+%s" % d if all_clear \
            else "Saved+%d+exception(s)+for+%s" % (n, d)
        return redirect(APP_PREFIX + "/?d=%s&m=%s&c=ok" % (d, m))
    except PermissionError as e:
        return redirect(APP_PREFIX + "/?d=%s&m=%s&c=err" % (d, str(e).replace(" ", "+")))


@app.route(APP_PREFIX + "/approve", methods=["POST"])
@require("check")
def approve():
    u = current_user(request)
    d = request.form.get("d", _today())
    try:
        approve_date(d, u["user"], u["caps"]["override"])
        return redirect(APP_PREFIX + "/?d=%s&m=Approved+%s&c=ok" % (d, d))
    except (PermissionError, ValueError) as e:
        return redirect(APP_PREFIX + "/?d=%s&m=%s&c=err" % (d, str(e).replace(" ", "+")))


@app.route(APP_PREFIX + "/reverse", methods=["POST"])
@require("override")
def reverse():
    u = current_user(request)
    d = request.form.get("d", _today())
    reverse_date(d, u["user"], request.form.get("note", ""))
    return redirect(APP_PREFIX + "/?d=%s&m=Reversed+%s+to+draft&c=ok" % (d, d))


@app.route(APP_PREFIX + "/festivals", methods=["GET"])
@require("override")
def festivals():
    u = current_user(request)
    con = get_db()
    fests = list_festivals(con)
    con.close()
    return render_template_string(FESTIVALS_HTML, who=u, fests=fests, prefix=APP_PREFIX,
                                  msg=request.args.get("m", ""),
                                  msgcls=request.args.get("c", "ok"))


@app.route(APP_PREFIX + "/festival", methods=["POST"])
@require("override")
def festival():
    u = current_user(request)
    d = request.form.get("fest_date", "")
    if not _valid_date(d):
        return redirect(APP_PREFIX + "/festivals?m=Bad+date&c=err")
    if request.form.get("action") == "del":
        del_festival(d, u["user"])
        return redirect(APP_PREFIX + "/festivals?m=Removed+%s&c=ok" % d)
    name = (request.form.get("name") or "").strip()
    closed = bool(request.form.get("closed"))
    set_festival(d, name, closed, u["user"])
    return redirect(APP_PREFIX + "/festivals?m=Saved+%s&c=ok" % d)


@app.route(APP_PREFIX + "/leave", methods=["GET"])
@require("maker")
def leave_page():
    u = current_user(request)
    con = get_db()
    staff = con.execute("SELECT staff_id,name FROM staff WHERE active=1 ORDER BY name").fetchall()
    raw = list_leave_sanctions(con)
    con.close()
    rows = []
    for r in raw:
        rd = dict(r)
        rd["can_approve"] = bool(u["caps"]["override"] or (r["maker_user"] != u["user"]))
        rows.append(rd)
    return render_template_string(LEAVE_HTML, who=u, caps=u["caps"], staff=staff,
                                  rows=rows, prefix=APP_PREFIX,
                                  msg=request.args.get("m", ""), msgcls=request.args.get("c", "ok"))


@app.route(APP_PREFIX + "/leave/add", methods=["POST"])
@require("maker")
def leave_add():
    u = current_user(request)
    try:
        add_leave_sanction(_form_sid(), request.form.get("from_date", ""),
                           request.form.get("to_date", ""),
                           request.form.get("approved_by", ""),
                           request.form.get("note", ""), u["user"])
        return redirect(APP_PREFIX + "/leave?m=Added+(pending+approval)&c=ok")
    except (ValueError, PermissionError) as e:
        return redirect(APP_PREFIX + "/leave?m=%s&c=err" % str(e).replace(" ", "+"))


@app.route(APP_PREFIX + "/leave/approve", methods=["POST"])
@require("check")
def leave_approve():
    u = current_user(request)
    try:
        approve_leave_sanction(int(request.form.get("id")), u["user"], u["caps"]["override"])
        return redirect(APP_PREFIX + "/leave?m=Approved&c=ok")
    except (ValueError, PermissionError, TypeError) as e:
        return redirect(APP_PREFIX + "/leave?m=%s&c=err" % str(e).replace(" ", "+"))


@app.route(APP_PREFIX + "/leave/cancel", methods=["POST"])
@require("override")
def leave_cancel():
    u = current_user(request)
    try:
        cancel_leave_sanction(int(request.form.get("id")), u["user"])
    except Exception:
        pass
    return redirect(APP_PREFIX + "/leave?m=Cancelled&c=ok")


def _form_sid():
    try:
        return int(request.form.get("sid") or 0)
    except Exception:
        return 0


@app.route(APP_PREFIX + "/staff", methods=["GET"])
@require("maker")
def staff_list():
    u = current_user(request)
    d = _today()
    con = get_db()
    dec = []
    for s in con.execute("SELECT * FROM staff WHERE active=1 ORDER BY name"):
        sd = dict(s)
        sd["mx"] = bool(s["minutes_exempt"])
        sd["uniform_issued"] = con.execute(
            "SELECT 1 FROM issuance WHERE staff_id=? AND item_type='uniform' AND "
            "status='approved'", (s["staff_id"],)).fetchone() is not None
        sd["icard_issued"] = con.execute(
            "SELECT 1 FROM issuance WHERE staff_id=? AND item_type='icard' AND "
            "status='approved'", (s["staff_id"],)).fetchone() is not None
        sd["uniform_ok"] = issuance_ok(con, s["staff_id"], "uniform", d)
        sd["icard_ok"] = issuance_ok(con, s["staff_id"], "icard", d)
        dec.append(sd)
    con.close()
    return render_template_string(STAFF_LIST_HTML, who=u, caps=u["caps"], staff=dec,
                                  prefix=APP_PREFIX)


@app.route(APP_PREFIX + "/staff/<int:sid>", methods=["GET"])
@require("maker")
def staff_record(sid):
    u = current_user(request)
    con = get_db()
    s = staff_by_id(con, sid)
    if not s:
        con.close(); abort(404)
    issuance = issuance_for_staff(con, sid)
    pauses = pauses_for_staff(con, sid)
    assets = assets_for_staff(con, sid) if u["caps"]["docs"] else []
    docs = degrees = []
    profile = None
    summary = {}
    role_checked = set()
    role_custom = ""
    if u["caps"]["docs"]:
        alldocs = docs_for_staff(con, sid)
        docs = [dv for dv in alldocs if dv["doc_type"] != "professional_degree"]
        degrees = []
        for dv in alldocs:
            if dv["doc_type"] == "professional_degree":
                dd = dict(dv)
                dd["regs"] = registrations_for_doc(con, dv["id"])
                degrees.append(dd)
        profile = get_profile(con, sid)
        summary = doc_summary(con, sid)
        cur = [r.strip() for r in ((profile["job_roles"] or "").split(",")
               if profile and profile["job_roles"] else []) if r.strip()]
        role_checked = set(cur) & set(JOB_ROLES)
        role_custom = ", ".join(r for r in cur if r not in JOB_ROLES)
    con.close()
    return render_template_string(
        STAFF_RECORD_HTML, who=u, caps=u["caps"], s=s, issuance=issuance,
        pauses=pauses, docs=docs, degrees=degrees, assets=assets, profile=profile,
        summary=summary, doc_labels=DOC_LABELS, doc_groups=DOC_GROUPS,
        degree_subtypes=DEGREE_SUBTYPES, job_roles_list=JOB_ROLES,
        family_relations=FAMILY_RELATIONS, asset_types=ASSET_TYPES, asset_labels=ASSET_LABELS,
        role_checked=role_checked, role_custom=role_custom,
        today=_today(), prefix=APP_PREFIX, msg=request.args.get("m", ""),
        msgcls=request.args.get("c", "ok"))


@app.route(APP_PREFIX + "/issuance/add", methods=["POST"])
@require("maker")
def issuance_add():
    u = current_user(request)
    sid = _form_sid()
    add_issuance(sid, request.form.get("item", "uniform"),
                 request.form.get("season"), request.form.get("issued_date") or _today(),
                 u["user"])
    return redirect(APP_PREFIX + "/staff/%d?m=Issued+(pending+approval)&c=ok" % sid)


@app.route(APP_PREFIX + "/issuance/approve", methods=["POST"])
@require("check")
def issuance_approve_route():
    u = current_user(request)
    sid = _form_sid()
    try:
        approve_issuance(int(request.form.get("iid")), u["user"])
    except Exception:
        pass
    return redirect(APP_PREFIX + "/staff/%d?m=Issuance+approved&c=ok" % sid)


@app.route(APP_PREFIX + "/pause/add", methods=["POST"])
@require("maker")
def pause_add_route():
    u = current_user(request)
    sid = _form_sid()
    add_pause(sid, request.form.get("item", "uniform"),
              request.form.get("from_date") or _today(),
              request.form.get("reason", ""), u["user"])
    return redirect(APP_PREFIX + "/staff/%d?m=Pause+started&c=ok" % sid)


@app.route(APP_PREFIX + "/pause/close", methods=["POST"])
@require("check")
def pause_close_route():
    u = current_user(request)
    sid = _form_sid()
    try:
        close_pause(int(request.form.get("pid")), request.form.get("to_date") or _today(),
                    u["user"])
    except Exception:
        pass
    return redirect(APP_PREFIX + "/staff/%d?m=Pause+closed&c=ok" % sid)


@app.route(APP_PREFIX + "/doc/upload", methods=["POST"])
@require("docs")
def doc_upload():
    u = current_user(request)
    sid = _form_sid()
    f = request.files.get("file")
    if not f or not f.filename:
        return redirect(APP_PREFIX + "/staff/%d?m=No+file+selected&c=err" % sid)
    dtype = request.form.get("doc_type", "other")
    sub_type = request.form.get("sub_type") if dtype == "professional_degree" else None
    save_document(sid, dtype, f.filename, f.read(), request.form.get("note", ""),
                  u["user"], sub_type=sub_type)
    return redirect(APP_PREFIX + "/staff/%d?m=Document+uploaded&c=ok" % sid)


@app.route(APP_PREFIX + "/registration/add", methods=["POST"])
@require("docs")
def registration_add():
    u = current_user(request)
    sid = _form_sid()
    try:
        doc_id = int(request.form.get("doc_id"))
    except Exception:
        return redirect(APP_PREFIX + "/staff/%d?m=Bad+degree&c=err" % sid)
    f = request.files.get("file")
    filename = f.filename if (f and f.filename) else None
    data = f.read() if filename else None
    add_registration(doc_id, sid, request.form.get("council", "").strip(),
                     request.form.get("reg_no", "").strip(), filename, data, u["user"])
    return redirect(APP_PREFIX + "/staff/%d?m=Registration+added&c=ok" % sid)


@app.route(APP_PREFIX + "/registration/<int:rid>/download", methods=["GET"])
@require("docs")
def registration_download(rid):
    con = get_db()
    rg = con.execute("SELECT * FROM degree_registration WHERE id=?", (rid,)).fetchone()
    con.close()
    if not rg or not rg["stored_path"] or not os.path.exists(rg["stored_path"]):
        abort(404)
    return send_file(rg["stored_path"], as_attachment=True,
                     download_name=(rg["original_name"]
                                    or os.path.basename(rg["stored_path"])))


@app.route(APP_PREFIX + "/registration/delete", methods=["POST"])
@require("delete")
def registration_delete():
    u = current_user(request)
    sid = _form_sid()
    try:
        delete_registration(int(request.form.get("rid")), u["user"])
    except Exception:
        pass
    return redirect(APP_PREFIX + "/staff/%d?m=Registration+deleted&c=ok" % sid)


@app.route(APP_PREFIX + "/doc/delete", methods=["POST"])
@require("delete")
def doc_delete():
    u = current_user(request)
    sid = _form_sid()
    try:
        delete_document(int(request.form.get("did")), u["user"])
    except Exception:
        pass
    return redirect(APP_PREFIX + "/staff/%d?m=Document+deleted&c=ok" % sid)


@app.route(APP_PREFIX + "/profile/save", methods=["POST"])
@require("docs")
def profile_save():
    u = current_user(request)
    sid = _form_sid()
    roles = request.form.getlist("role")
    custom = (request.form.get("role_custom") or "").strip()
    if custom:
        roles.append(custom)
    job_roles = ", ".join(r for r in roles if r)
    save_profile(sid,
                 request.form.get("join_date") or "",
                 request.form.get("last_working") or "",
                 job_roles,
                 request.form.get("current_address") or "",
                 request.form.get("permanent_address") or "",
                 request.form.get("emergency_name") or "",
                 request.form.get("emergency_phone") or "",
                 request.form.get("family_name") or "",
                 request.form.get("family_relation") or "",
                 u["user"])
    return redirect(APP_PREFIX + "/staff/%d?m=Profile+saved&c=ok" % sid)


@app.route(APP_PREFIX + "/asset/add", methods=["POST"])
@require("docs")
def asset_add():
    u = current_user(request)
    sid = _form_sid()
    add_asset(sid, request.form.get("asset_type", "other"),
              request.form.get("identifier", "").strip(),
              request.form.get("descr", "").strip(),
              request.form.get("issued_date", "").strip(),
              request.form.get("note", "").strip(), u["user"])
    return redirect(APP_PREFIX + "/staff/%d?m=Asset+issued&c=ok" % sid)


@app.route(APP_PREFIX + "/asset/return", methods=["POST"])
@require("docs")
def asset_return():
    u = current_user(request)
    sid = _form_sid()
    try:
        return_asset(int(request.form.get("aid")),
                     request.form.get("returned_date", "").strip(), u["user"])
    except Exception:
        pass
    return redirect(APP_PREFIX + "/staff/%d?m=Asset+returned&c=ok" % sid)


@app.route(APP_PREFIX + "/asset/delete", methods=["POST"])
@require("delete")
def asset_delete():
    u = current_user(request)
    sid = _form_sid()
    try:
        delete_asset(int(request.form.get("aid")), u["user"])
    except Exception:
        pass
    return redirect(APP_PREFIX + "/staff/%d?m=Asset+deleted&c=ok" % sid)


@app.route(APP_PREFIX + "/doc/<int:did>/download", methods=["GET"])
@require("docs")
def doc_download(did):
    con = get_db()
    dv = con.execute("SELECT * FROM document_vault WHERE id=?", (did,)).fetchone()
    con.close()
    if not dv or not os.path.exists(dv["stored_path"]):
        abort(404)
    return send_file(dv["stored_path"], as_attachment=True,
                     download_name=(dv["original_name"]
                                    or os.path.basename(dv["stored_path"])))


SALARY_PAGE_HTML = """<!doctype html><meta charset="utf-8">
<title>Register salary &mdash; {{ ym }}</title><style>{{ css|safe }}
.btnbar{display:flex;gap:12px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
.btnbar a,.btnbar button{cursor:pointer}
.lockcard{border-radius:10px;padding:12px 14px;margin:10px 0;font-size:14px}
.lockcard.locked{background:rgba(34,197,94,.12);border:1px solid #16794a;color:#bbf7d0}
.lockcard.ready{background:rgba(59,130,246,.12);border:1px solid #1e4f8a;color:#cfe0f2}
.lockcard.block{background:#3a1414;border:1px solid #7f1d1d;color:#ffc9c9}
.lockcard.info{background:#12233b;border:1px solid #24344a;color:#cfe0f2}
.lockcard .big{font-size:22px;font-weight:700;margin-bottom:4px}
.datelinks{margin-top:6px}
.datelinks a{display:inline-block;margin:2px 6px 2px 0;padding:2px 8px;border-radius:8px;
  background:#0b1b29;border:1px solid #7f1d1d;color:#ffd0d0;text-decoration:none;font-size:12.5px}
.lockbtn{border:none;border-radius:12px;padding:12px 20px;font-size:16px;font-weight:700;
  cursor:pointer;color:#fff;background:#16794a}
.unlock{margin-top:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.unlock input[type=text]{background:#0b1b29;border:1px solid #24344a;color:#fff;border-radius:6px;padding:6px;min-width:220px}
.unlock button{border:none;border-radius:8px;padding:8px 12px;cursor:pointer;color:#fff;background:#7f1d1d}</style>
<div class="btnbar">
  <a class="pill" href="{{ prefix }}/">&larr; Daily register</a>
  <form method="GET" style="display:flex;gap:6px;align-items:center;margin:0">
    <label class="note">Month <input type="month" name="ym" value="{{ ym }}"
      style="background:#0b1b29;border:1px solid #24344a;color:#fff;border-radius:6px;padding:4px"></label>
    <button class="pill" type="submit">View</button>
  </form>
  <span class="note">signed in as {{ who.user }} ({{ who.role }})</span>
</div>

{% if msg %}<div class="lockcard {{ msg_kind }}">{{ msg }}</div>{% endif %}

{% if locked %}
  <div class="lockcard locked">
    <div class="big">&#128274; LOCKED &mdash; TOTAL PAYOUT &#8377;{{ locked.total_fmt }}</div>
    <div>Official run for {{ ym }} &middot; locked by <b>{{ locked.locked_by }}</b> on {{ locked.locked_ts }}.</div>
    {% if lock_role %}
    <form class="unlock" method="POST" action="{{ prefix }}/salary/unlock"
          onsubmit="return confirm('Unlock the {{ ym }} salary run? This is logged.');">
      <input type="hidden" name="ym" value="{{ ym }}">
      <input type="text" name="reason" placeholder="reason to unlock (required)" required>
      <button type="submit">Unlock for correction</button>
    </form>
    {% endif %}
  </div>
{% elif blockers.missing or blockers.draft %}
  <div class="lockcard block">
    <b>Not lockable yet.</b> {{ blockers.approved }}/{{ blockers.required }} dates approved.
    Tap a date to review &amp; approve it:
    {% if blockers.draft %}<div class="datelinks"><span class="note">Awaiting approval:</span>
      {% for d in blockers.draft %}<a href="{{ prefix }}/?d={{ d }}">{{ d }}</a>{% endfor %}</div>{% endif %}
    {% if blockers.missing %}<div class="datelinks"><span class="note">Never entered:</span>
      {% for d in blockers.missing %}<a href="{{ prefix }}/?d={{ d }}">{{ d }}</a>{% endfor %}</div>{% endif %}
  </div>
{% elif not ended %}
  <div class="lockcard info">This month has not ended yet &mdash; the run becomes lockable after month-end. (Preview below.)</div>
{% elif lock_role and not complete %}
  <div class="lockcard block">Take-home is unavailable for one or more staff (ledger unreachable) &mdash; cannot lock until it reads cleanly.</div>
{% elif can_lock %}
  <div class="lockcard ready">
    {% if total_fmt %}<div class="big">TOTAL PAYOUT to lock: &#8377;{{ total_fmt }}</div>{% endif %}
    <div>All {{ blockers.required }} dates approved. Ready to finalise the official run.</div>
    <form method="POST" action="{{ prefix }}/salary/lock" style="margin-top:8px"
          onsubmit="return confirm('APPROVE & LOCK the {{ ym }} salary run at the shown total? This freezes the official record.');">
      <input type="hidden" name="ym" value="{{ ym }}">
      <button class="lockbtn" type="submit">&#128274; APPROVE &amp; LOCK {{ ym }}</button>
    </form>
  </div>
{% elif ended and not lock_role %}
  <div class="lockcard info">All dates approved. Locking the official run is doctor-only.</div>
{% endif %}

{{ body|safe }}
"""


def _default_salary_ym():
    """Salary is run for a completed month -> default to the previous month."""
    t = _today()
    y, m = int(t[:4]), int(t[5:7])
    if m == 1:
        return "%04d-12" % (y - 1)
    return "%04d-%02d" % (y, m - 1)


# --- Stage B (D283): approval-completeness gate + APPROVE & LOCK -------------
def _valid_ym(ym):
    try:
        return (isinstance(ym, str) and len(ym) == 7 and ym[4] == "-"
                and 2000 <= int(ym[:4]) <= 2100 and 1 <= int(ym[5:7]) <= 12)
    except (ValueError, TypeError):
        return False


def _salary_month_dates(ym):
    """Every calendar date of ym as ISO strings, 1st..last (inclusive)."""
    y, m = int(ym[:4]), int(ym[5:7])
    first = datetime.date(y, m, 1)
    nxt = datetime.date(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1)
    nd = (nxt - first).days
    return ["%04d-%02d-%02d" % (y, m, day) for day in range(1, nd + 1)]


def month_has_ended(ym):
    """True once the last day of ym is strictly before today (lock only past months)."""
    return _salary_month_dates(ym)[-1] < _today()


def approval_blockers(con, ym):
    """Dates in ym that must be checker-approved before the run can be locked, but
    aren't. Clinic-closed holidays need no daily entry -> excluded. Returns
    {'missing':[...], 'draft':[...], 'required':N, 'approved':N}. A MISSING date
    (never entered) blocks too -- a silent gap must never pass as 'clear'."""
    dates = [d for d in _salary_month_dates(ym) if not is_holiday(con, d)]
    if not dates:
        return {"missing": [], "draft": [], "required": 0, "approved": 0}
    seen = {r["reg_date"]: r["status"] for r in con.execute(
        "SELECT reg_date,status FROM day_review WHERE reg_date>=? AND reg_date<=?",
        (dates[0], dates[-1]))}
    missing, draft, approved = [], [], 0
    for d in dates:
        st = seen.get(d)
        if st is None:
            missing.append(d)
        elif st == "approved":
            approved += 1
        else:
            draft.append(d)
    return {"missing": missing, "draft": draft, "required": len(dates),
            "approved": approved}


def _render_salary(ym, u, msg="", msg_kind="block"):
    """Build the salary page: engine preview body + Stage-B lock controls, for user u."""
    ym = (ym or _default_salary_ym()).strip()
    css = _salary._CSS if _SALARY_OK else ""
    body = ""
    total = None
    complete = False
    if not _SALARY_OK:
        body = ("<div class='warn'>Salary engine unavailable on this server "
                "(salary_engine.py not importable).</div>")
    else:
        try:
            rows, problems, pot = _salary.build_report(
                ym, db_path=DB_PATH, att_dir=SALARY_ATT_DIR)
            body = _salary.render_html(ym, rows, problems, pot, embed=True)
            total, complete = _salary.total_payout(rows)
        except Exception as e:
            body = "<div class='warn'>Could not build report: %s</div>" % html.escape(str(e))
    con = get_db()
    blk = approval_blockers(con, ym)
    lr = con.execute("SELECT * FROM locked_run WHERE ym=?", (ym,)).fetchone()
    con.close()
    lr = dict(lr) if lr else None
    is_locked = bool(lr and lr.get("status") == "locked")
    if lr is not None:
        lr["total_fmt"] = "{:,}".format(int(lr["total_payout"]))
    total_fmt = "{:,}".format(int(total)) if total is not None else None
    ended = month_has_ended(ym)
    lock_role = bool(u["caps"].get("lock"))
    can_lock = (lock_role and ended and complete and (not is_locked)
                and not blk["missing"] and not blk["draft"])
    return render_template_string(
        SALARY_PAGE_HTML, who=u, prefix=APP_PREFIX, ym=ym, css=css, body=body,
        blockers=blk, locked=(lr if is_locked else None), can_lock=can_lock,
        ended=ended, complete=complete, total_fmt=total_fmt, lock_role=lock_role,
        msg=msg, msg_kind=msg_kind)


@app.route(APP_PREFIX + "/salary")
@require("salary")
def salary_view():
    return _render_salary(request.args.get("ym"), current_user(request))


@app.route(APP_PREFIX + "/salary/lock", methods=["POST"])
@require("lock")
def salary_lock():
    u = current_user(request)
    ym = (request.form.get("ym") or "").strip()
    if not _valid_ym(ym):
        return _render_salary(ym, u, "Bad month.")
    if not _SALARY_OK:
        return _render_salary(ym, u, "Salary engine unavailable; cannot lock.")
    if not month_has_ended(ym):
        return _render_salary(ym, u,
            "This month has not ended yet \u2014 a run can be locked only after month-end.")
    con = get_db()
    already = con.execute("SELECT status FROM locked_run WHERE ym=?", (ym,)).fetchone()
    if already and already["status"] == "locked":
        con.close()
        return _render_salary(ym, u,
            "This month is already locked. Unlock it first (doctor-only) to re-lock.")
    blk = approval_blockers(con, ym)
    con.close()
    if blk["missing"] or blk["draft"]:
        return _render_salary(ym, u,
            "Some dates are not approved yet \u2014 approve every listed date, then lock.")
    try:
        rows, problems, pot = _salary.build_report(ym, db_path=DB_PATH, att_dir=SALARY_ATT_DIR)
        total, complete = _salary.total_payout(rows)
    except Exception as e:
        return _render_salary(ym, u, "Could not build the run: %s" % e)
    if not complete:
        return _render_salary(ym, u,
            "The take-home for one or more staff is unavailable (ledger unreachable) "
            "\u2014 refusing to lock an incomplete run.")
    report_html = _salary.render_html(ym, rows, problems, pot, embed=True)
    con = get_db()
    if already:
        con.execute("UPDATE locked_run SET total_payout=?,report_html=?,locked_by=?,"
                    "locked_ts=?,unlocked_by=NULL,unlocked_ts=NULL,unlock_reason=NULL,"
                    "status='locked' WHERE ym=?",
                    (int(total), report_html, u["user"], _now(), ym))
    else:
        con.execute("INSERT INTO locked_run(ym,total_payout,report_html,locked_by,"
                    "locked_ts,status) VALUES(?,?,?,?,?, 'locked')",
                    (ym, int(total), report_html, u["user"], _now()))
    _audit(con, "salary", ym, "lock", "", "TOTAL PAYOUT %d locked" % int(total), u["user"])
    con.commit()
    con.close()
    return redirect(APP_PREFIX + "/salary?ym=" + ym)


@app.route(APP_PREFIX + "/salary/unlock", methods=["POST"])
@require("lock")
def salary_unlock():
    u = current_user(request)
    ym = (request.form.get("ym") or "").strip()
    reason = (request.form.get("reason") or "").strip()
    if not _valid_ym(ym):
        return _render_salary(ym, u, "Bad month.")
    if not reason:
        return _render_salary(ym, u, "An unlock reason is required.")
    con = get_db()
    row = con.execute("SELECT status FROM locked_run WHERE ym=?", (ym,)).fetchone()
    if not row or row["status"] != "locked":
        con.close()
        return _render_salary(ym, u, "This month is not locked.")
    con.execute("UPDATE locked_run SET status='unlocked',unlocked_by=?,unlocked_ts=?,"
                "unlock_reason=? WHERE ym=?", (u["user"], _now(), reason, ym))
    _audit(con, "salary", ym, "unlock", "locked", "unlocked", u["user"], reason)
    con.commit()
    con.close()
    return redirect(APP_PREFIX + "/salary?ym=" + ym)


@app.route(APP_PREFIX + "/health")
def health():
    ok = os.path.exists(DB_PATH)
    return {"service": "staff_register", "status": "ok" if ok else "no-db",
            "sso": bool(_SSO_LIBS and SSO_SECRET), "db": DB_PATH}, (200 if ok else 503)

# ---------------------------------------------------------------------------
# SELFTEST
# ---------------------------------------------------------------------------
def _selftest():
    import tempfile
    global DB_PATH, SR_LOCAL_USERS
    tmp = tempfile.mkdtemp()
    DB_PATH = os.path.join(tmp, "t.db")
    init_db()
    con = get_db()
    # A = normal, S = Shivani(extra-duty), D = Darpan(outstation), X = Arjun(mx)
    demo = [(1, "Demo A", 0, 0, 0), (2, "Shivani X", 1, 0, 0),
            (3, "Darpan Y", 0, 1, 0), (4, "Arjun", 0, 0, 1)]
    for sid, name, cover, outst, mx in demo:
        con.execute("INSERT INTO staff(staff_id,name,join_date,base_salary,allowed_offs,"
                    "minutes_exempt,cover_eligible,outstation_eligible,active) "
                    "VALUES(?,?,?,?,?,?,?,?,1)",
                    (sid, name, "2026-01-01", 10000, 2, mx, cover, outst))
        if not mx:
            for it in ("uniform", "icard"):
                con.execute("INSERT INTO issuance(staff_id,item_type,issued_date,status) "
                            "VALUES(?,?,?, 'approved')", (sid, it, "2026-01-01"))
    con.commit(); con.close()
    d = "2026-08-05"

    class F(dict):
        def get(self, k, default=None): return dict.get(self, k, default)

    # exceptions save: A late-approved-manoj + dress; Shivani extra-duty;
    # Darpan 2 outstation nights; Arjun on leave (leave = single checkbox now)
    form = F({"s1_late": "manoj", "s1_dress": "on",
              "s2_extra": "1", "s3_outstation": "1", "s4_leave": "manoj"})
    n = save_maker(d, False, form, "alisha")
    assert n == 4, "expected 4 exception rows, got %d" % n
    con = get_db()
    a = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=1", (d,)).fetchone()
    assert a["late_flag"] == "informed" and a["late_approved_by"] == "manoj"
    assert a["dress_improper"] == 1
    s2 = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=2", (d,)).fetchone()
    assert s2["extra_duty"] == 1
    s3 = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=3", (d,)).fetchone()
    assert s3["outstation_nights"] == 1 and s3["absence_type"] == "outstation"
    x = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=4", (d,)).fetchone()
    assert x["leave_kind"] == "discretionary" and x["leave_approved_by"] == "manoj"
    con.close()
    # Arjun: leave stored, late/dress/extra/outstation forced clean even if posted
    save_maker(d, False, F({"s4_leave": "manoj", "s4_late": "manoj",
                            "s4_dress": "on", "s4_extra": "on", "s4_outstation": "5"}),
               "alisha")
    con = get_db()
    x = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=4", (d,)).fetchone()
    assert x["leave_kind"] == "discretionary", "Arjun leave should record"
    assert x["late_flag"] is None and x["dress_improper"] == 0 and x["extra_duty"] == 0 \
        and x["outstation_nights"] == 0, "Arjun scoping (D276) failed"
    con.close()

    # D278: same leave on a listed FESTIVAL date classifies as festival
    set_festival(d, "Diwali", False, "manoj")     # festival, clinic open
    save_maker(d, False, F({"s1_leave": "manoj"}), "alisha")
    con = get_db()
    fa = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=1", (d,)).fetchone()
    assert fa["leave_kind"] == "festival", "leave on a festival date must be festival (D278)"
    assert festival_on(con, d) is not None and is_holiday(con, d) is False
    con.close()
    del_festival(d, "manoj")

    # nullification: leave wipes late+dress
    save_maker(d, False, F({"s1_leave": "manoj", "s1_late": "manoj", "s1_dress": "on"}), "alisha")
    con = get_db()
    a2 = con.execute("SELECT * FROM daily_register WHERE reg_date=? AND staff_id=1", (d,)).fetchone()
    assert a2["leave_kind"] and a2["late_flag"] is None and a2["dress_improper"] == 0
    con.close()

    # all-clear wipes exception rows + records the day
    save_maker(d, True, F({}), "alisha")
    con = get_db()
    assert con.execute("SELECT count(*) FROM daily_register WHERE reg_date=?", (d,)).fetchone()[0] == 0
    assert con.execute("SELECT state FROM day_review WHERE reg_date=?", (d,)).fetchone()["state"] == "all_clear"
    assert date_status(con, d) == "draft"
    con.close()

    # D272 own-day guard: Shavez enters -> can't approve own; override can
    save_maker(d, True, F({}), "shavez")
    con = get_db()
    assert can_check_approve(con, d, "shavez", False) is False
    assert can_check_approve(con, d, "shavez", True) is True
    assert can_check_approve(con, d, "alisha", False) is True
    con.close()
    approve_date(d, "manoj", True)
    con = get_db(); assert date_status(con, d) == "approved"; con.close()
    reverse_date(d, "manoj", "t")
    con = get_db(); assert date_status(con, d) == "draft"; con.close()

    # issuance pause: open a uniform pause over d for Demo A -> dress gate closes
    con = get_db()
    con.execute("INSERT INTO issuance_pause(staff_id,item_type,from_date,to_date,status) "
                "VALUES(1,'uniform','2026-08-01','2026-08-31','approved')")
    con.commit()
    assert issuance_ok(con, 1, "uniform", d) is False, "pause window should close the gate"
    assert issuance_ok(con, 1, "icard", d) is True, "i-card unaffected by uniform pause"
    con.close()

    # holiday (festival_day toggle ON) blocks maker save
    set_festival(d, "Holi", True, "manoj")
    assert is_holiday(get_db(), d) is True
    try:
        save_maker(d, False, F({"s1_leave": "manoj"}), "alisha")
        raise AssertionError("holiday should block save")
    except PermissionError:
        pass
    del_festival(d, "manoj")

    # ---- issuance add -> approve -> gate opens; pause -> gate closes; close -> reopens
    global VAULT_DIR
    VAULT_DIR = os.path.join(tmp, "vault")
    con = get_db()
    con.execute("DELETE FROM issuance WHERE staff_id=5")   # clean slate for staff 5
    con.execute("INSERT INTO staff(staff_id,name,join_date,base_salary,active) "
                "VALUES(5,'Fresh Hire','2026-01-01',9000,1)")
    con.commit(); con.close()
    dd = "2026-09-10"
    con = get_db(); assert issuance_ok(con, 5, "uniform", dd) is False; con.close()
    add_issuance(5, "uniform", "summer", "2026-09-01", "alisha")     # draft -> no gate yet
    con = get_db()
    assert issuance_ok(con, 5, "uniform", dd) is False, "draft issuance must NOT open the gate"
    iid = con.execute("SELECT id FROM issuance WHERE staff_id=5 AND item_type='uniform'").fetchone()[0]
    con.close()
    approve_issuance(iid, "shavez")
    con = get_db(); assert issuance_ok(con, 5, "uniform", dd) is True, "approved issuance opens the gate"; con.close()
    add_pause(5, "uniform", "2026-09-05", "lost", "alisha")          # open pause -> fine paused
    con = get_db(); assert issuance_ok(con, 5, "uniform", dd) is False, "open pause must close the gate"
    pid = con.execute("SELECT id FROM issuance_pause WHERE staff_id=5").fetchone()[0]; con.close()
    close_pause(pid, "2026-09-08", "shavez")                          # closed before dd -> gate reopens
    con = get_db(); assert issuance_ok(con, 5, "uniform", dd) is True, "closed pause (before date) reopens the gate"; con.close()

    # ---- document vault: save a tiny PDF, confirm stored + row + download path
    pdf_bytes = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    path = save_document(5, "aadhaar", "id.pdf", pdf_bytes, "front", "shavez")
    assert os.path.exists(path) and path.endswith(".pdf")
    # a professional degree (sub_type only) + two council registrations
    deg_path = save_document(5, "professional_degree", "dmlt.pdf", pdf_bytes, "", "shavez",
                             sub_type="DMLT")
    con = get_db()
    deg = con.execute("SELECT * FROM document_vault WHERE doc_type='professional_degree'").fetchone()
    assert deg["sub_type"] == "DMLT"
    con.close()
    add_registration(deg["id"], 5, "UP Paramedical", "UP-12345", "cert.pdf", pdf_bytes, "shavez")
    add_registration(deg["id"], 5, "National Council", "NC-9", None, None, "shavez")  # no file yet
    con = get_db()
    regs = registrations_for_doc(con, deg["id"])
    assert len(regs) == 2, "degree should have 2 registrations"
    assert regs[0]["stored_path"] and os.path.exists(regs[0]["stored_path"]), "cert file stored"
    assert regs[1]["stored_path"] is None, "reg without file allowed (flagged no-file)"
    # derived summary: aadhaar -> id + address; degree -> qualification
    summ = doc_summary(con, 5)
    assert summ["id_proof"] and summ["address_proof"] and summ["qualification"]
    con.close()
    # deleting the degree cascades its registrations + files
    rpath = regs[0]["stored_path"]
    delete_document(deg["id"], "manoj")
    con = get_db()
    assert con.execute("SELECT count(*) FROM degree_registration WHERE doc_id=?", (deg["id"],)).fetchone()[0] == 0
    assert not os.path.exists(rpath), "registration cert file removed on degree delete"
    con.close()
    # re-add a degree for the route tests below
    save_document(5, "professional_degree", "dmlt2.pdf", pdf_bytes, "", "shavez", sub_type="BMLT")

    # profile save: DOJ + multi roles + custom + addresses + family relation
    save_profile(5, "2026-05-01", "", "Lab technician, Receptionist, Night desk",
                 "House 1, Bareilly", "Village X, Distt Y",
                 "Wife", "9990001111", "Father Name", "Father", "shavez")
    con = get_db()
    st = con.execute("SELECT join_date,last_working,active FROM staff WHERE staff_id=5").fetchone()
    assert st["join_date"] == "2026-05-01" and st["last_working"] is None and st["active"] == 1
    pr = get_profile(con, 5)
    assert "Lab technician" in pr["job_roles"] and "Night desk" in pr["job_roles"]
    assert pr["current_address"] == "House 1, Bareilly" and pr["permanent_address"] == "Village X, Distt Y"
    assert pr["family_relation"] == "Father"
    con.close()

    # asset lifecycle: issue -> in use -> return; delete
    add_asset(5, "mobile_phone", "IMEI-123", "Redmi", "2026-05-02", "for lab", "shavez")
    add_asset(5, "bicycle", "CY-9", "Hero", "", "", "shavez")   # blank date -> today
    con = get_db()
    ax = assets_for_staff(con, 5)
    assert len(ax) == 2
    phone = [a for a in ax if a["asset_type"] == "mobile_phone"][0]
    assert phone["status"] == "issued" and phone["issued_date"] == "2026-05-02"
    con.close()
    return_asset(phone["id"], "2026-06-01", "shavez")
    con = get_db()
    p2 = con.execute("SELECT * FROM asset_issue WHERE id=?", (phone["id"],)).fetchone()
    assert p2["status"] == "returned" and p2["returned_date"] == "2026-06-01"
    cyc = con.execute("SELECT id FROM asset_issue WHERE asset_type='bicycle'").fetchone()["id"]
    con.close()
    delete_asset(cyc, "manoj")
    con = get_db()
    assert con.execute("SELECT count(*) FROM asset_issue WHERE staff_id=5").fetchone()[0] == 1
    con.close()
    con = get_db()
    dv = con.execute("SELECT * FROM document_vault WHERE staff_id=5 AND doc_type='aadhaar'").fetchone()
    con.close()

    # Flask routes (F-63)
    SR_LOCAL_USERS = {"manoj": {"pw": _pw_hash("x"), "role": "override"},
                      "bhawna": {"pw": _pw_hash("x"), "role": "override"},
                      "shavez": {"pw": _pw_hash("x"), "role": "checker"},
                      "alisha": {"pw": _pw_hash("x"), "role": "maker"}}
    app.secret_key = b"selftest-key"
    c = app.test_client()
    assert c.get(APP_PREFIX + "/").status_code in (301, 302)
    assert c.post(APP_PREFIX + "/login", data={"user": "manoj", "password": "x"}).status_code in (301, 302)
    r = c.get(APP_PREFIX + "/?d=" + d)
    assert r.status_code == 200 and b"All clear" in r.data and b"Demo A" in r.data
    assert c.get(APP_PREFIX + "/festivals").status_code == 200
    assert c.get(APP_PREFIX + "/salary").status_code == 200
    assert c.get(APP_PREFIX + "/staff").status_code == 200
    r = c.get(APP_PREFIX + "/staff/5")
    assert r.status_code == 200 and b"Profile" in r.data and b"Documents" in r.data
    assert b"Delete" in r.data, "manoj must see Delete buttons"
    assert c.get(APP_PREFIX + "/doc/%d/download" % dv["id"]).status_code == 200
    # maker (alisha): no documents/profile, and delete forbidden
    c2 = app.test_client(); c2.post(APP_PREFIX + "/login", data={"user": "alisha", "password": "x"})
    r = c2.get(APP_PREFIX + "/staff/5")
    assert r.status_code == 200 and b"Documents" not in r.data
    assert c2.get(APP_PREFIX + "/doc/%d/download" % dv["id"]).status_code == 403
    # shavez (checker): sees docs, but NO delete (manoj only)
    c3 = app.test_client(); c3.post(APP_PREFIX + "/login", data={"user": "shavez", "password": "x"})
    r = c3.get(APP_PREFIX + "/staff/5")
    assert r.status_code == 200 and b"Documents" in r.data and b"Delete" not in r.data, "shavez must NOT see delete"
    assert c3.post(APP_PREFIX + "/doc/delete", data={"did": dv["id"], "sid": 5}).status_code == 403, "shavez delete must be 403"
    # bhawna (override): sees docs, but also NO delete (manoj only)
    c4 = app.test_client(); c4.post(APP_PREFIX + "/login", data={"user": "bhawna", "password": "x"})
    r = c4.get(APP_PREFIX + "/staff/5")
    assert b"Documents" in r.data and b"Delete" not in r.data, "bhawna must NOT see delete (manoj only)"
    assert c.get(APP_PREFIX + "/health").status_code == 200
    # ---- grid step 2 (D284): sanctioned-leave range ----
    add_leave_sanction(1, "2026-09-10", "2026-09-12", "bhawna", "trip", "alisha")
    con = get_db()
    lsid = con.execute("SELECT id FROM leave_sanction ORDER BY id DESC LIMIT 1").fetchone()["id"]
    assert active_leave_for(con, 1, "2026-09-11") is None, "draft range must NOT pre-fill"
    con.close()
    try:
        approve_leave_sanction(lsid, "alisha", False)
        raise AssertionError("maker approved own leave range")
    except PermissionError:
        pass
    approve_leave_sanction(lsid, "shavez", False)
    con = get_db()
    assert active_leave_for(con, 1, "2026-09-11") == "bhawna", "approved range pre-fills covered day"
    assert active_leave_for(con, 1, "2026-09-20") is None, "outside range = no pre-fill"
    con.close()

    print("SELFTEST OK — all-clear, exceptions, Arjun (D276), late+approver, "
          "leave+festival (D278), nullification, issuance add/approve/pause/close gate, "
          "doc vault + profile + degree/council + derived summary, delete = manoj-only, "
          "docs hidden from maker (D274), D272 guard, approve/reverse, holiday, leave-range (D284), routes 200.")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    args = sys.argv[1:]
    if "--init" in args:
        init_db(); print("Initialised DB at", DB_PATH)
    elif "--seed" in args:
        i = args.index("--seed")
        path = args[i + 1] if i + 1 < len(args) else ""
        init_db(); seed_from_csv(path)
    elif "--selftest" in args:
        _selftest()
    else:
        app.run(host="127.0.0.1", port=8044, debug=False)
