#!/usr/bin/env python3
"""
staff_register.py  —  Staff Daily Register  (subsystem D271)   v0.4
===================================================================
Dr. Manoj Agarwal Clinic, Bareilly.  Session 161; v0.3 + v0.4 = Session 196.

v0.8 (S200) — D338 past-day presence correction (approver-only door);
v0.7 (S199-D) — THE LOCK DESK: /register/salary is rebuilt on the NEW engine
(salary_policy) — big buttons, the lock card, pack status, and a summary
identical to Sheet 3. The Lock records the NEW-model numbers, writes the hold
ledger (once per month, re-lock-safe), and REFUSES while the month is not
covered by enforce_from (F-150 made structural). Old engine dormant fallback.

v0.6 (S199) — THE MONTH-END FLOW (owner spec): Sheet1 attendance grid (staff
view + doored review) · Sheet2 advances/loans/holds · pack approval gates the
salary lock · policy-settings page (every fine a setting, D332 pattern) ·
sheets 3+4 preview — all computed by salary_policy.py, PREVIEW unless the
enforcement date covers the month. Also /me/month (own grid, no money).

v0.5 (S199) — DEDUCTION SCENARIO page: a read-only /register/salary/scenario
route (gated to the salary allowlist, manoj/bhawna) renders att_scenario.py's
old-vs-new-vs-strict comparison inline, reached by a pill on the salary page.
No existing route, store, or salary math touched.

v0.4 (S196, same session) — PWA INSTALLABILITY for the self page: a web app
manifest + icons served from this app's own origin, linked from /register/me
only. NO service worker — nothing is cached offline, every view is live, and
the mark-me-present request still requires the network (its server timestamp
is the punch). Staff: open /register/me in Chrome -> menu -> Add to Home
screen -> a real app icon that opens full-screen.

v0.3 (S196) — STAFF SELF-SERVICE + MACHINE LATE-MINUTES:
  * NEW role "self": any portal login that maps to a staff row (staff.username,
    else an unambiguous first-name match) but holds no maker/checker/override
    power. Self users see ONLY /register/me — today's date and today's punch
    times. No history, no other staff, no shift or salary data (owner ruling,
    S196: punch history stays out of staff hands).
  * "Mark me present" request (/register/me/request): allowed only for TODAY,
    only while the machine has NO punch for that staff today, one per day,
    reason required. THE SERVER'S receipt time IS the punch time (leakage
    check: a delayed request costs exactly what a late punch costs; the phone
    clock is never trusted). Flow: staff -> checker verifies (never his own,
    D272 analogue) -> final approval by SR_PRESENT_APPROVERS (manoj) only.
    Approved requests feed att_month_report v2.6 as synthetic punches.
  * Machine late minutes in the day grid: for every staff row the grid shows
    the machine's first punch and, when the person is MORE THAN 60 MINUTES
    late, the exact minutes — read-only, server-computed, stored on save in
    daily_register.late_minutes. The maker can only mark informed/uninformed,
    never type over the minutes. Sundays included via the D253 roster rule
    (transcribed below from att_month_report v2.5; the month-end report stays
    the money authority — this display can surface, never cause, divergence).

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
import json
import html
import uuid
import base64
import hmac
import hashlib
import sqlite3
import secrets
import datetime
from functools import wraps

from flask import (
    Flask, request, redirect, session, render_template_string, send_file, abort,
    make_response,
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
# S164: Shivani activated -> no inactive makers by default. Add usernames via
# SR_INACTIVE_MAKERS (env or staff_register_config) to re-park a maker later.
INACTIVE_MAKERS = set(x for x in _cfg("SR_INACTIVE_MAKERS", "").split(",") if x)
DOC_CUSTODIANS  = set(_cfg("SR_DOC_CUSTODIANS", "shavez").split(","))
DELETER_USERS   = set(_cfg("SR_DELETER_USERS", "manoj").split(","))   # delete = manoj only
# Stage B (D283): salary VIEW allowlist + APPROVE&LOCK allowlist (username-gated, role-independent).
SALARY_USERS    = set(x for x in _cfg("SR_SALARY_USERS", "manoj,bhawna").split(",") if x)  # see the run
LOCK_USERS      = set(x for x in _cfg("SR_LOCK_USERS", "manoj").split(",") if x)            # approve&lock/unlock
# Daily biometric feed (D283): the attendance listener's punch log; read-only here.
SR_PUNCH_CSV    = _cfg("SR_PUNCH_CSV", "/root/punches.csv")
# --- S196 staff self-service ---------------------------------------------
# Final approvers for "mark me present" requests (owner ruling S196: checker
# verifies, the doctor decides). Username list, role-independent.
PRESENT_APPROVERS = set(x for x in _cfg("SR_PRESENT_APPROVERS", "manoj").split(",") if x)
# staff_master.csv (shift timings + sunday_group), read-only here — the same
# file the attendance report reads. One writer per store: build_staff_master
# owns it; this app only reads.
SR_STAFF_MASTER  = _cfg("SR_STAFF_MASTER", "/root/staff_master.csv")
# Self sessions live long (PWA on staff phones); revocation stays instant via
# the portal active switch / sign-out-everywhere epoch.
SR_SELF_SESSION_DAYS = int(_cfg("SR_SELF_SESSION_DAYS", "180") or 180)
# D253 Sunday roster start month — transcribed from att_month_report v2.5
# (ROSTER_FROM). If the attendance policy layer ever moves this, move it here
# too; the grid display would otherwise disagree VISIBLY with the report.
ROSTER_FROM = "2026-09"


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


def punch_times_for_day(d):
    """{staff_id: [datetime, ...]} for date d, read-only from punches.csv, with
    the listener's own de-dup key (user_id, datetime). None = feed unreadable
    (callers fail soft, never crash). One writer per store: attendance owns it."""
    p = SR_PUNCH_CSV
    if not p or not os.path.exists(p):
        return None
    out = {}
    seen = set()
    try:
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ds = (row.get("datetime") or "")
                if ds[:10] != d:
                    continue
                key = (row.get("user_id"), ds)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    uid = int(row.get("user_id"))
                    dt = datetime.datetime.strptime(ds.strip(), "%Y-%m-%d %H:%M:%S")
                except (TypeError, ValueError):
                    continue
                out.setdefault(uid, []).append(dt)
    except Exception:
        return None
    for uid in out:
        out[uid].sort()
    return out


def _parse_hhmm(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%H:%M").time()
    except ValueError:
        return None


def load_staff_shifts():
    """{staff_id: {wd_start, wd_end, sun_start, sun_end, sunday_group,
    minutes_exempt}} read-only from staff_master.csv (same columns the
    attendance layer reads). None on any problem — display then degrades to
    punch times without late minutes; nothing crashes."""
    p = SR_STAFF_MASTER
    if not p or not os.path.exists(p):
        return None
    out = {}
    try:
        with open(p, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    uid = int(row.get("user_id"))
                except (TypeError, ValueError):
                    continue
                out[uid] = {
                    "wd_start": _parse_hhmm(row.get("wd_start")),
                    "wd_end": _parse_hhmm(row.get("wd_end")),
                    "sun_start": _parse_hhmm(row.get("sun_start")),
                    "sun_end": _parse_hhmm(row.get("sun_end")),
                    "sunday_group": (row.get("sunday_group") or "").strip().upper(),
                    "minutes_exempt": (row.get("minutes_exempt") or "").strip().upper()
                                      in ("Y", "1", "TRUE"),
                }
    except Exception:
        return None
    return out


def duty_shift_for(date, sh):
    """(start, end) duty shift for one staff on one date, or (None, None) = OFF.
    TRANSCRIBED from att_month_report v2.5 duty_shift() (D253 roster): weekday =
    wd shift; Sunday pre-ROSTER_FROM = sun columns (empty sun_start = off);
    roster era: A duty 1st/3rd, B 2nd/4th (weekday shift), C/ARJ every Sunday
    (sun columns), 5th Sunday = normal full day for all."""
    if date.weekday() != 6:
        return sh["wd_start"], sh["wd_end"]
    ym = date.strftime("%Y-%m")
    if ym < ROSTER_FROM:
        if sh["sun_start"]:
            return sh["sun_start"], sh["sun_end"]
        return None, None
    grp = sh["sunday_group"]
    si = (date.day - 1) // 7 + 1
    if si == 5:
        return sh["wd_start"], sh["wd_end"]
    if grp == "A":
        return (sh["wd_start"], sh["wd_end"]) if si in (1, 3) else (None, None)
    if grp == "B":
        return (sh["wd_start"], sh["wd_end"]) if si in (2, 4) else (None, None)
    if grp in ("C", "ARJ"):
        return sh["sun_start"], sh["sun_end"]
    if sh["sun_start"]:
        return sh["sun_start"], sh["sun_end"]
    return None, None


def approved_present_requests(con, d):
    """{staff_id: 'YYYY-MM-DD HH:MM:SS' req_ts} of APPROVED requests for date d.
    The request's server receipt time IS the punch time (S196)."""
    out = {}
    try:
        for r in con.execute("SELECT staff_id, req_ts FROM present_request "
                             "WHERE reg_date=? AND status='approved'", (d,)):
            out[r["staff_id"]] = r["req_ts"]
    except Exception:
        pass
    return out


def machine_day(con, d):
    """Per-staff machine picture for date d, for the day grid + /me page:
    {sid: {"in": "HH:MM", "n": punches, "late": minutes-int, "off": bool,
           "via_req": bool}} — server-computed, read-only facts. Approved
    present-requests are merged as punches at their request time. Returns None
    when the punch feed is unreadable (grid renders exactly as pre-v0.3)."""
    times = punch_times_for_day(d)
    if times is None:
        return None
    times = dict(times)          # never mutate a cached/shared dict
    via_req = set()
    for sid, ts in approved_present_requests(con, d).items():
        try:
            dt = datetime.datetime.strptime(ts.strip(), "%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            continue
        lst = list(times.get(sid, []))
        lst.append(dt)
        lst.sort()
        times[sid] = lst
        via_req.add(sid)
    shifts = load_staff_shifts()
    try:
        date = datetime.datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        return None
    out = {}
    for sid, lst in times.items():
        if not lst:
            continue
        first = lst[0]
        info = {"in": first.strftime("%H:%M"), "n": len(lst), "late": 0,
                "off": False, "via_req": sid in via_req}
        sh = shifts.get(sid) if shifts else None
        if sh and not sh["minutes_exempt"]:
            s_start, s_end = duty_shift_for(date, sh)
            if s_start is None:
                info["off"] = True
            else:
                sched_start = datetime.datetime.combine(date, s_start)
                sched_end = (datetime.datetime.combine(date, s_end)
                             if s_end else None)
                # lateness only when the first punch is plausibly an arrival —
                # the same guard att_month_report v2.5 applies
                if sched_end is None or first <= sched_end:
                    info["late"] = max(0, int(
                        (first - sched_start).total_seconds() // 60))
        out[sid] = info
    return out


def staff_for_user(con, username):
    """Map a login username to its staff row id. Exact staff.username first;
    else a case-insensitive FIRST-NAME match, accepted only when unambiguous.
    None = this login is not a staff member (no self page)."""
    u = (username or "").strip().lower()
    if not u:
        return None
    try:                                    # exact mapping (staff.username)
        r = con.execute("SELECT staff_id FROM staff WHERE active=1 AND "
                        "LOWER(COALESCE(username,''))=?", (u,)).fetchone()
        if r:
            return r["staff_id"]
    except Exception:
        pass                                # pre-v0.3 DB: column not there yet
    try:                                    # unambiguous first-name fallback
        hits = [row["staff_id"] for row in
                con.execute("SELECT staff_id, name FROM staff WHERE active=1")
                if (row["name"] or "").strip().lower().split()[:1] == [u]]
        if len(hits) == 1:
            return hits[0]
    except Exception:
        return None
    return None


def _self_sid(username):
    """staff_for_user with its own short-lived connection (auth path)."""
    try:
        con = get_db()
        try:
            return staff_for_user(con, username)
        finally:
            con.close()
    except Exception:
        return None
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
        "present":  u in PRESENT_APPROVERS,     # S196: decide mark-me-present
        "active":   role in ("maker", "checker", "override", "self"),
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

CREATE TABLE IF NOT EXISTS earlybig_ruling (       -- S163: register-owned big early-exit verdicts
    ym        TEXT NOT NULL,                        -- YYYY-MM
    staff     TEXT NOT NULL,                        -- staff name (matches the attendance report)
    ebdate    TEXT NOT NULL,                        -- YYYY-MM-DD of the early exit
    verdict   TEXT NOT NULL DEFAULT 'waived',       -- genuine | waived  (only genuine deducts)
    ruled_by  TEXT, ruled_ts TEXT,
    PRIMARY KEY (ym, staff, ebdate)
);

CREATE TABLE IF NOT EXISTS present_request (       -- S196: "my biometric missed me"
    id          INTEGER PRIMARY KEY,
    reg_date    TEXT NOT NULL,                     -- always the SERVER's today
    staff_id    INTEGER NOT NULL,
    req_user    TEXT NOT NULL,                     -- the login that raised it
    req_ts      TEXT NOT NULL,                     -- SERVER receipt time = the punch time
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',   -- pending|verified|approved|rejected
    verify_user TEXT, verify_ts TEXT,              -- checker's confirmation
    decide_user TEXT, decide_ts TEXT, decide_note TEXT,
    UNIQUE (reg_date, staff_id)                    -- one request per staff per day
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
    ("staff", "username", "TEXT"),                 # S196: login -> staff mapping
    ("daily_register", "late_minutes", "INTEGER"), # S196: machine late minutes, stored fact
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
        if role is None and _self_sid(user):     # S196: staff self-service
            role = "self"
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
                role = _register_role(user, brole)
                if role is None and _self_sid(user):   # S196: portal-verified
                    role = "self"                      # staff -> self page only
                return role
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
        mach = machine_day(con, d) or {}    # S196: machine facts, server-computed,
        #                                     stored read-only — never from the form
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
            # S199: Yes/No dropdown — only an explicit "no" (without) stores 1.
            dress = 1 if (form.get(pre + "dress") or "").strip().lower() == "no" else 0
            icard = 1 if (form.get(pre + "icard") or "").strip().lower() == "no" else 0
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

            # S196: machine late minutes — a stored FACT beside the maker's
            # decision. Server-computed from the punch feed (or an approved
            # present-request); the form cannot supply or override it.
            late_min = int((mach.get(sid) or {}).get("late", 0) or 0)

            has_exception = (any([leave_kind, late_flag, dress, icard, extra, outs])
                             or absence in ("absent", "outstation"))
            if has_exception:
                con.execute(
                    "INSERT INTO daily_register(reg_date,staff_id,absence_type,"
                    "leave_kind,leave_approved_by,late_flag,late_approved_by,"
                    "dress_improper,icard_missing,"
                    "outstation_nights,extra_duty,ot_permitted,late_minutes,"
                    "maker_user,maker_ts) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(reg_date,staff_id) DO UPDATE SET "
                    "absence_type=excluded.absence_type,leave_kind=excluded.leave_kind,"
                    "leave_approved_by=excluded.leave_approved_by,"
                    "late_flag=excluded.late_flag,late_approved_by=excluded.late_approved_by,"
                    "dress_improper=excluded.dress_improper,icard_missing=excluded.icard_missing,"
                    "outstation_nights=excluded.outstation_nights,extra_duty=excluded.extra_duty,"
                    "ot_permitted=excluded.ot_permitted,late_minutes=excluded.late_minutes,"
                    "maker_user=excluded.maker_user,"
                    "maker_ts=excluded.maker_ts",
                    (d, sid, absence, leave_kind, leave_by, late_flag, late_by, dress, icard,
                     outs, extra, otp, late_min, actor, _now()))
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
.mlate{background:rgba(239,68,68,.16);color:#fecaca;border:1px solid rgba(239,68,68,.35);
 border-radius:8px;padding:3px 7px;font-size:11px;font-weight:700;margin-bottom:4px;white-space:nowrap}
.mmin{color:var(--muted);font-size:10px;margin-bottom:3px;white-space:nowrap}
.pill.req{background:rgba(34,197,94,.18);color:#86efac}
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
      <th>Dress OK?</th><th>I-card?</th><th>Cover</th><th>Outstn</th>
    </tr></thead>
    <tbody>
    {% for s in staff %}
      <tr class="srow">
        <td class="nm">{{ s.name }}{% if s.m_req %} <span class="pill req" title="present by approved request — the request time is the punch time">req {{ s.m_in }}</span>{% elif s.bio_absent %} <span class="pill empty" title="no biometric punch">no punch</span>{% endif %}</td>
        <td><select class="lv" name="s{{ s.staff_id }}_leave" {{ 'disabled' if locked }} onchange="rowSync(this)">
              <option value="" {{ 'selected' if s.leave_sel=='' }}>— present</option>
              <option value="not_approved" {{ 'selected' if s.leave_sel=='not_approved' }}>Absent — not approved</option>
              <option value="bhawna" {{ 'selected' if s.leave_sel=='bhawna' }}>Leave — appr Dr Bhawna</option>
              <option value="manoj" {{ 'selected' if s.leave_sel=='manoj' }}>Leave — appr Dr Manoj</option>
            </select>{% if festival_name %} <span class="gate">fest</span>{% endif %}</td>
        <td>{% if s.mx %}<span class="gate">n/a</span>{% else %}
            {% if s.m_late >= 60 %}<div class="mlate" title="machine-computed from the punch record — cannot be edited">&#9200; {{ s.m_late }} min late (machine)</div>
            {% elif s.m_in %}<div class="mmin">in {{ s.m_in }}{% if s.m_late %} &middot; {{ s.m_late }}m late{% endif %}</div>{% endif %}
            <select class="late" name="s{{ s.staff_id }}_late" {{ 'disabled' if locked }}>
              <option value="">—</option>
              <option value="not_approved" {{ 'selected' if s.late_sel=='not_approved' }}>Not approved</option>
              <option value="bhawna" {{ 'selected' if s.late_sel=='bhawna' }}>Approved by Dr Bhawna</option>
              <option value="manoj" {{ 'selected' if s.late_sel=='manoj' }}>Approved by Dr Manoj</option>
            </select>{% endif %}</td>
        <td>{% if s.mx %}<span class="gate">—</span>
            {% elif s.uniform_ok %}<select class="cb dress" name="s{{ s.staff_id }}_dress" {{ 'disabled' if locked }}><option value="yes" {{ 'selected' if not s.dress_sel }}>Yes</option><option value="no" {{ 'selected' if s.dress_sel }}>No</option></select>
            {% else %}<span class="gate">{{ 'paused' if s.uniform_issued else 'not issued' }}</span>{% endif %}</td>
        <td>{% if s.mx %}<span class="gate">—</span>
            {% elif s.icard_ok %}<select class="cb icard" name="s{{ s.staff_id }}_icard" {{ 'disabled' if locked }}><option value="yes" {{ 'selected' if not s.icard_sel }}>Yes</option><option value="no" {{ 'selected' if s.icard_sel }}>No</option></select>
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
    {% if caps.check %}<a class="btn ghost" href="{{ prefix }}/review" target="_blank" rel="noopener">&#128449; Pending review &middot; &#9997;&#65039; {{ review_to_enter }} to enter &middot; &#9989; {{ review_to_approve }} to approve</a>{% endif %}
    {% if caps.maker %}<a class="btn ghost" href="{{ prefix }}/staff" target="_blank" rel="noopener">👤 Staff records</a>{% endif %}
    {% if caps.maker %}<a class="btn ghost" href="{{ prefix }}/leave" target="_blank" rel="noopener">🌴 Sanctioned leave</a>{% endif %}
    {% if caps.salary %}<a class="btn ghost" href="{{ prefix }}/salary" target="_blank" rel="noopener">💰 Salary reconciliation</a>{% endif %}
    {% if caps.override %}<a class="btn ghost" href="{{ prefix }}/festivals" target="_blank" rel="noopener">🎉 Festivals &amp; holidays</a>{% endif %}
  </div>

  {% if corr_show %}
  <div class="card" id="d338">
    <b>&#128295; Past-day presence correction (D338)</b>
    <div class="note">Doctor-only. For a day the machine missed someone entirely:
      the in-time below becomes the punch time (pre-filled with the shift start
      &mdash; overtype the real arrival), recorded in your name with the reason.
      Staff self-requests stay today-only (D334).</div>
    {% for s in staff %}{% if s.bio_absent %}
    <form method="POST" action="{{ prefix }}/present/correct"
          style="display:flex;gap:6px;align-items:center;margin:6px 0;flex-wrap:wrap"
          onsubmit="return confirm('Mark {{ s.name }} PRESENT for {{ d }}?');">
      <input type="hidden" name="d" value="{{ d }}">
      <input type="hidden" name="sid" value="{{ s.staff_id }}">
      <span style="min-width:110px">{{ s.name }}</span>
      <input type="time" name="in_time" value="{{ s.corr_prefill }}" required>
      <input name="reason" required maxlength="200"
             placeholder="reason — e.g. machine missed the punch"
             style="flex:1;min-width:180px">
      <button class="btn" type="submit">Mark present</button>
    </form>
    {% endif %}{% endfor %}
  </div>
  {% endif %}

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
# S196: only sessions explicitly marked permanent (self logins) use this;
# maker/checker/override sessions stay browser-session cookies as before.
app.permanent_session_lifetime = datetime.timedelta(days=SR_SELF_SESSION_DAYS)


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
            if role == "self":
                session.permanent = True     # S196: long-lived staff session (PWA)
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
    if u["role"] == "self":                       # S196: staff see only their page
        return redirect(APP_PREFIX + "/me")
    d = request.args.get("d", _today())
    if not _valid_date(d):
        d = _today()
    con = get_db()
    rows = day_rows(con, d)
    present_ids = biometric_present_ids(d)        # set of present staff_ids, or None if no feed
    bio_ok = present_ids is not None
    mach = machine_day(con, d)                    # S196: machine facts (None = no feed)
    _sh_all = None                                # D338: lazy shift map for prefill
    try:
        _dt_obj = datetime.datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        _dt_obj = None
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
        mi = (mach or {}).get(sid)
        sd["m_in"] = mi["in"] if mi else ""
        sd["m_late"] = int(mi["late"]) if mi else 0
        sd["m_req"] = bool(mi and mi["via_req"])
        # an approved present-request counts as presence on this screen too
        sd["bio_absent"] = bool(bio_ok and sid not in present_ids
                                and not sd["m_req"])
        # D338: prefill for the presence-correction card = the shift start
        # (editable in the form); fail-soft to 09:00 on any lookup trouble.
        sd["corr_prefill"] = "09:00"
        if sd["bio_absent"] and _dt_obj is not None:
            if _sh_all is None:
                try:
                    _sh_all = load_staff_shifts() or {}
                except Exception:
                    _sh_all = {}
            _sh = _sh_all.get(sid)
            if _sh is not None:
                try:
                    if not _sh["minutes_exempt"]:
                        _ss, _se = duty_shift_for(_dt_obj, _sh)
                        if _ss:
                            sd["corr_prefill"] = _ss.strftime("%H:%M")
                except Exception:
                    pass
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
    # D338: the correction card — approvers only, past-or-today, not a holiday,
    # and only when someone is actually machine-absent on this date.
    corr_show = (bool(u["caps"].get("present")) and d <= _today()
                 and not holiday and any(x.get("bio_absent") for x in dec))
    fest = festival_on(con, d)
    festival_name = fest["name"] if fest else ""
    can_approve = can_check_approve(con, d, u["user"], u["caps"]["override"]) \
        if u["caps"]["check"] else False
    # pending-review tile counts (checkers/override only; makers don't see the tile)
    if u["caps"]["check"]:
        _rc = review_board(con, _today()[:7], u["user"], u["caps"]["override"], True)
        r_enter, r_approve = _rc["to_enter"], _rc["to_approve"]
    else:
        r_enter = r_approve = 0
    con.close()
    dt = datetime.datetime.strptime(d, "%Y-%m-%d").date()
    prev = (dt - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    nxt = (dt + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return render_template_string(
        REGISTER_HTML, who=u, caps=u["caps"], d=d, prev=prev, next=nxt,
        staff=dec, rows=rows, status=status, holiday=holiday, all_clear=all_clear,
        holiday_name=holiday_name, festival_name=festival_name, bio_ok=bio_ok,
        can_approve=can_approve, corr_show=corr_show, prefix=APP_PREFIX,
        review_to_enter=r_enter, review_to_approve=r_approve,
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


# ---------------------------------------------------------------------------
# S196 — STAFF SELF-SERVICE: "My biometric" (today only) + mark-me-present
# ---------------------------------------------------------------------------
# v0.4: PWA head links (manifest + icons + theme color), injected ONLY into the
# self page's head — the maker/checker pages are unchanged.
PWA_HEAD = ('<link rel="manifest" href="' + APP_PREFIX + '/manifest.webmanifest">'
            '<meta name="theme-color" content="#0f2233">'
            '<link rel="apple-touch-icon" href="' + APP_PREFIX + '/pwa-icon-192.png">')
ME_HEAD = HEAD.replace("</head>", PWA_HEAD + "</head>")

ME_HTML = ME_HEAD + """
<div class="wrap" style="max-width:480px">
  <div class="head"><h1>&#129465; My biometric</h1>
  <div style="text-align:right;margin:2px 0"><a href="{{ url_prefix }}/me/month" style="color:#5fd;font-size:13px">&#128198; My month</a></div>
    <span class="sub">{{ name }} &middot; signed in as {{ who.user }}</span></div>
  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}

  <div class="card" style="text-align:center">
    <div style="font-size:13px;color:var(--muted)">Today</div>
    <div style="font-size:22px;font-weight:700;margin:4px 0 12px">{{ d }}</div>
    {% if holiday %}
      <div class="msg ok">&#127958;&#65039; Clinic holiday today.</div>
    {% elif feed_down %}
      <div class="msg err">Punch machine feed is unavailable right now.
        Please contact reception.</div>
    {% elif times %}
      <div style="font-size:13px;color:var(--muted);margin-bottom:6px">Your punch today</div>
      {% for t in times %}
        <div style="font-size:26px;font-weight:700;letter-spacing:.03em">{{ t }}</div>
      {% endfor %}
      <div class="note" style="margin-top:10px">All recorded. Nothing to do.</div>
    {% else %}
      <div class="msg err" style="text-align:center">No punch recorded for you today.</div>
      {% if req %}
        {% if req.status == 'approved' %}
          <div class="msg ok">&#9989; Marked present &mdash; your request time
            <b>{{ req.req_ts[11:16] }}</b> counts as your punch time.</div>
        {% elif req.status == 'rejected' %}
          <div class="msg err">&#10060; Your request was not approved.
            {% if req.decide_note %}Reason: {{ req.decide_note }}{% endif %}</div>
        {% else %}
          <div class="msg ok">&#8987; Request sent at <b>{{ req.req_ts[11:16] }}</b>
            &mdash; waiting for {{ 'the doctor' if req.status=='verified' else 'verification' }}.
            If approved, {{ req.req_ts[11:16] }} counts as your punch time.</div>
        {% endif %}
      {% elif can_request %}
        <form method="POST" action="{{ prefix }}/me/request" style="margin-top:8px">
          <input name="reason" maxlength="200" required placeholder="reason — e.g. machine did not read finger"
                 style="width:100%;font-size:15px;padding:12px;border:2px solid var(--blue);
                        border-radius:12px;background:#0b1b29;color:#fff;margin-bottom:10px">
          <button class="btn" type="submit" style="width:100%;font-size:16px"
                  onclick="return confirm('Request to be marked present NOW? The current time will be recorded as your punch time.');">
            &#128075; Mark me present (time now = punch time)</button>
        </form>
        <div class="note">The request time is recorded as your punch time and is
          checked and approved by the clinic. Punch out on the machine as usual.</div>
      {% endif %}
    {% endif %}
  </div>
  <div class="foot"><a href="{{ prefix }}/logout">Sign out</a></div>
</div></body></html>
"""


def _me_context(con, user):
    """(sid, name, d, times_list_or_None, req_row) for the self page."""
    sid = staff_for_user(con, user)
    if not sid:
        return None, None, None, None, None
    row = con.execute("SELECT name FROM staff WHERE staff_id=?", (sid,)).fetchone()
    name = row["name"] if row else user
    d = _today()
    allt = punch_times_for_day(d)
    times = None
    if allt is not None:
        times = [t.strftime("%H:%M") for t in allt.get(sid, [])]
    req = con.execute("SELECT * FROM present_request WHERE reg_date=? AND staff_id=?",
                      (d, sid)).fetchone()
    return sid, name, d, times, req


def request_present(user, reason):
    """Raise a mark-me-present request for TODAY. Server-authoritative guards:
    today only (no date parameter exists), machine must have NO punch for this
    staff today, one request per day, reason required, no clinic holiday. The
    SERVER receipt time is stored and, on approval, IS the punch time."""
    reason = (reason or "").strip()[:200]
    con = get_db()
    try:
        sid, name, d, times, req = _me_context(con, user)
        if not sid:
            raise PermissionError("this login is not mapped to a staff member")
        if is_holiday(con, d):
            raise PermissionError("today is a clinic holiday")
        if times is None:
            raise PermissionError("punch feed unavailable — ask at reception")
        if times:
            raise PermissionError("machine already has your punch at %s" % times[0])
        if req:
            raise PermissionError("a request for today already exists (%s)" % req["status"])
        if not reason:
            raise PermissionError("a reason is required")
        now = _now()
        con.execute("INSERT INTO present_request(reg_date,staff_id,req_user,req_ts,"
                    "reason,status) VALUES(?,?,?,?,?,'pending')",
                    (d, sid, user, now, reason))
        _audit(con, "present_request", "%s/%s" % (d, sid), "raise",
               "", "req_ts=%s reason=%s" % (now, reason), user)
        con.commit()
        return now
    finally:
        con.close()


def correct_present(actor, d, sid, in_time, reason):
    """D338 (S200): owner-approved PAST-DAY presence correction. The staff
    self-request stays today-only (D334); this is the APPROVER's door for a
    day the machine missed someone entirely. Writes an already-approved
    present_request whose req_ts carries the corrected in-time, so every
    existing reader — machine_day, att_month_report v2.6's synthetic punches,
    the salary engine, Sheet 1's * mark — treats the day as present through
    the ONE mechanism that already exists. Server-authoritative guards:
    approver-only, valid date not in the future, active staff that day, punch
    feed readable, NO machine punch that day, one row per staff-day (any
    status), valid HH:MM in-time, compulsory reason, no clinic holiday."""
    if actor not in PRESENT_APPROVERS:
        raise PermissionError("only a present-request approver may correct a past day")
    reason = (reason or "").strip()[:200]
    if not reason:
        raise PermissionError("a reason is required")
    if not _valid_date(d):
        raise PermissionError("invalid date")
    if d > _today():
        raise PermissionError("cannot mark a future day present")
    try:
        t = datetime.datetime.strptime((in_time or "").strip(), "%H:%M").time()
    except ValueError:
        raise PermissionError("in-time must look like 09:05")
    try:
        sid = int(sid)
    except (TypeError, ValueError):
        raise PermissionError("invalid staff")
    con = get_db()
    try:
        if is_holiday(con, d):
            raise PermissionError("that date is a clinic holiday")
        if not any(s["staff_id"] == sid for s in staff_for_date(con, d)):
            raise PermissionError("no such active staff member on that date")
        allt = punch_times_for_day(d)
        if allt is None:
            raise PermissionError("punch feed unavailable — cannot prove the machine has no punch")
        if allt.get(sid):
            raise PermissionError("machine already has a punch for that staff member that day")
        ex = con.execute("SELECT status FROM present_request WHERE reg_date=? AND staff_id=?",
                         (d, sid)).fetchone()
        if ex:
            raise PermissionError("a request/correction for that day already exists (%s)"
                                  % ex["status"])
        ts = "%s %s:00" % (d, t.strftime("%H:%M"))
        con.execute("INSERT INTO present_request(reg_date,staff_id,req_user,req_ts,"
                    "reason,status,decide_user,decide_ts,decide_note) "
                    "VALUES(?,?,?,?,?,'approved',?,?,?)",
                    (d, sid, actor, ts, reason, actor, _now(),
                     "past-day presence correction (D338)"))
        _audit(con, "present_request", "%s/%s" % (d, sid), "correct_past_day",
               "", "in_time=%s reason=%s" % (t.strftime("%H:%M"), reason), actor)
        con.commit()
        return ts
    finally:
        con.close()


def verify_present(rid, actor):
    """Checker step: confirms against who was actually at the clinic. A checker
    can NEVER verify his own request (D272 analogue) — those go straight to the
    approver."""
    con = get_db()
    try:
        r = con.execute("SELECT * FROM present_request WHERE id=?", (rid,)).fetchone()
        if not r:
            raise PermissionError("no such request")
        if r["status"] != "pending":
            raise PermissionError("request is already %s" % r["status"])
        if r["req_user"] == actor:
            raise PermissionError("you cannot verify your own request")
        con.execute("UPDATE present_request SET status='verified',verify_user=?,"
                    "verify_ts=? WHERE id=?", (actor, _now(), rid))
        _audit(con, "present_request", rid, "verify", "pending", "verified", actor)
        con.commit()
    finally:
        con.close()


def decide_present(rid, actor, action, note=""):
    """Final step — SR_PRESENT_APPROVERS (manoj) only. Approving makes the
    request's server receipt time the staff member's punch time for the day
    (att_month_report v2.6 folds it as a synthetic punch)."""
    if action not in ("approve", "reject"):
        raise PermissionError("bad action")
    con = get_db()
    try:
        r = con.execute("SELECT * FROM present_request WHERE id=?", (rid,)).fetchone()
        if not r:
            raise PermissionError("no such request")
        if r["status"] not in ("pending", "verified"):
            raise PermissionError("request is already %s" % r["status"])
        if r["req_user"] == actor:
            raise PermissionError("you cannot decide your own request")
        new = "approved" if action == "approve" else "rejected"
        con.execute("UPDATE present_request SET status=?,decide_user=?,decide_ts=?,"
                    "decide_note=? WHERE id=?",
                    (new, actor, _now(), (note or "").strip()[:200], rid))
        _audit(con, "present_request", rid, action, r["status"], new, actor)
        con.commit()
    finally:
        con.close()


# v0.4: PWA assets — icons embedded as base64 (no file dependencies), manifest
# served from this origin. These three routes are unauthenticated on purpose:
# the browser's install machinery fetches them outside the login session, and
# they contain nothing but a name and a picture.
_PWA_ICON_192 = base64.b64decode(
    "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"
    "SUVORK5CYII=")
_PWA_ICON_512 = base64.b64decode(
    "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"
    "PJlXPJlVnOalQPaB5T5xtBTOPyiq4mN67azIbgZ7VPlbI1R2DOzk7YGRzkc6F/Gq1GrQ7La4d/I3O+tkyWNniCWKIahhiBX"
    "bOGHtjtn0p2wnK6Yhic2saRMJMPm5xuTqqHceoWCcuM+vuElE1krI3vzpNffe0vsFy+6Ey+0Y+J9wsT1l083pfA1iMSb1/K"
    "tMANL1kV93lV3J/0fcqQd6xIP7SZPaP9HIiI8Orab0UeiD4dsbR10Zjic1s6bHiBJUeTyrmTcV1so99YEWfWAhAAW/XYz9/"
    "lF3nPri+zt+CJGrznPdK1+tB/5+4/k6l/3PB+ilAWtQ7zEx7JXJO39/uTNBIPfl+O8RAdir41OwrkwS+jUHnv1jBjb6I5hs"
    "JezyCuDOR1of2QzpoyA0lbCo05TApDKsh7RD4KL1vNmmP5ddYDVEWp+ehc1+/sLt3qzemQYQkewQJwRTMYQJGzdj5Y456k+"
    "ZVD3GDMxMwNJm4VkkiIG0tia/P4e7Aj7Mk38/hmdyxWbs1WeLXwmAZXA1rZuy7s+4Wj/hzeYjLjZPuN6csu3n9KHOM/66+9"
    "5xUkB376XsqNy/Rb5kJBD5P1XAJPFIuiQMMQakqpC6Ye06Xm8j/1w6rFFc8HQu0p9GPl3A8aK6VfmTXRKQKoLjSGLRBBQCU"
    "PAbKXWOvW9VBcOt7WGQ7H2frx1fLz1frhxfriLftnAZhF5qpLKp9xhcGvcDNMRbucleScSdsSN9e4bzYG7+EHGQH5TV3/oH"
    "+f5vP5x06LzS5j99iEzsbaW/GZ0RJZXuNy5y1aZg/mbrWQ6eqDDPVsFnU8usMqxd5Jubnq+ve/5xM/Bi7bhsPa1P413m0A+"
    "Au4WTgzLw4e4kk4JXiJbeT1j3C27qRzSVwzBgTM/EDlQMiEAUEOy+AqAH+5I/uLA//jVTKzX5tY8Yo1QyevtXDL6hdccs21"
    "MutmdcrD7izfox1/0Z22HGECZoDvhJLzCuAt4Ti8Nl0D/gqn34ir9VrzdJExDT4qgQlRBjEi9iUGOwtmLthW83gcE7Whfoh"
    "oj3ERuhMpH5fPIg0RjHgUuHqBCAgt8Idmf9W9rube75f7Uc+L9Xni+Xjuc9XAxCpwc9f+9Sz1/jQVlSdtmCHu4J1oeOMn1r"
    "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"
    "9CdcbR9zkUf9broT2n6OizZXjrJWIBOAtBfAZoL28woszEFEHhX6Md+CMRNwDYGoypCMKZhZS2WUoyl8fDrh948WfLIwLKa"
    "5vWSy4O8HRPcS/AsBKHjPM519z19ue8CT1O6XXeCyD3yz8fz92vHVKvKihfNe6aihriAkkx9RReI45rcXE96r9Ouv47U5fJ"
    "6jKU+eqtqtCN64wOutwwq4GLnsQrYFrpjaNOsdgEVlsIuKR5MKl8WPYyvho7nlqE77BAavPJpZ/vtswt8eTfjLacNnxw1Hj"
    "cVFTWOCQ+TbZcWiNljZZ3BblwiA5td99G0wJlsEaS5qZ89/MAQMQ5yxcQtW/Sl1NVDbHiM91g4Ifj+JLnZXFpff6MIgPTDh"
    "IVdBjImpKpLtlSOWwS3YdCep7L9+wvnqjOv2lFW7oHdVmvO3cbfSV3YtlP2NsLdZ1v/8Wr196+7GT83BPRdRQlR8jLigSXu"
    "SS1qiJD+KxnC2aHh6MuezxzP+8vGC351OOTUDHy2SULXK15w9mHIhm1kVFAJQ8CsiACEqEaVS2d3QI1ZD5MXG8/Vy4Kuc+X"
    "+zVs6doVPA1ik78n43559Omrjz9t8pm3f7xB8qFn5fAfZ7PvsT7gK495XZ/+BQ5TxOLNoDTtMH5bLz9D6V5F+uHR/NK3531"
    "PDJ6BI4NTyeVdQGjJid9AtIZf3jtEXw9cbRe2XeGH53VPO3RxN+f9Sk8cDKEBVqI7zZOp7OKx7lyYDrXnA+TQR0QXO2mkSB"
    "krc1Si7jj5a+RtKhHVUY/IStm7PsT7C2o6k7arOhsluaGozG3bKa36L6bwzAOwslNaCC1ZhcEm0O4hqJahncjHV/etDzT5v"
    "91t2cwU/QsVVg/N7gB5Md/u6X/N9+Rf7r6/aQqOqB78O4zdJmIhgjOyOuEJXep6x/JP/TSjieVHx62vCHkymfnU3460dT/v"
    "Kk4XePJhzXEybG82hS7a7FIeh+JbUIxty3CdeDG0oKQSgEoOB9PADvC/66sO/5/98rxxcrz/NWufSGjQdMyvw1OKLrMJrDS"
    "0wu/5JnmvcbRH49pf+Hjt3xyB6lDKMXeojKOqRS/lUvXLZpSqLPc/snE8vMGp7ObPp7ZXNvfU80bvqaz04C152nD0plhJPG"
    "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"
    "hY9mBvulRmkCgA4herROLECXwSEqyQ5QisBeZlyU6vm4HSFMr/cJ+KNlAfRmNxj84jnFpbogO8GERD9/OjX4eM/io7nF6cR"
    "syP24H6tILC6AHlbfhv1zFHRykO3fQyYYFsrioNTwsQBINO6VGcyD8lGkiOB5zhZIqoDrVgqA6y7gWZkSCYMQAbuR/C9DvO"
    "oGvD7m7UsX34P3TKnzdahUjXlRY2oblKqGphqasvWv3rD+FS/9MLrub7Hw0qZb3gYCQDIC4ChkQCIHpTyU9oKYKUB5Fge//"
    "KlSJUA37sOhq97+Nx4N21X+ug3OHxkHbbLzPwywlrkprETzTiM0oPER57V0/j9cNfj+osFl46EJOJmKMmG/Mjiq5P4qkmrk"
    "uvFiDb10UCQogO8imFOOQGoUiChB8EmESbkS43vXOG93CpK/fyIhEEi4F0yISovDHxE4NNgrGR/tafztrMI3pxX+fCoZDGd"
    "7FSqrbl1bacMTZTfz3xUAv1FoOhv4cJ88x33nJpwAhYNSvqdxAbULaJw8QC+dwnUM8ESI0AKbKQ8VeDCXuXN1+vdjCNJGNz"
    "9sC4UWB7+DUuOwFA/+QtOGYYimzQm3sJQTsfMNxCLqO0nCxABH0BszyR7uHr1G9owwSmBoq4cI2M5FrD1j2UWxAE7IRIau9"
    "Qbrf8T2zp3RVvAOs+4hU02MQntURYuJrVHaNQrTSN4BRRBn+H/Tivq9YlTpro0kefGTSF4VIqxiFIpR6AijAjqlQaxG5SaN"
    "Rhz8Vm+KMA4IGh6dOIpUHn/WX2JT2XaszMeqC3ixcvjhqsU/Lxo8XzmEyDiaGEwKhcOJwfHU4nhicVAZFIbQhYjLWjICZmU"
    "L3RevHmuHPu+AwqbIgEYX8xeZGG7P/DkR/ZjgoiAA2du/Uh6P5yW+OLT45qzCX88m+PS4wsmsxMTq3cx/VwD8MY5xAh0n/e"
    "4YRj6tND6eatReHg6rGaYGqAUuOSKSBnQp1q9tA5VDg2IYRQnnF1QftnX5gxRiimSTtopQarXpqQ75e6veTlPcF3mvWYwyi"
    "SzmCOLIcBGofUQbBqfBcavoEVET4CP1m4VRBI1N45nb7aC4dwjkpLFmBogDFHmUqsHU1JgWK0xtnZz/xIWSaVi0eZzE+8HL"
    "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")


@app.route(APP_PREFIX + "/manifest.webmanifest")
def pwa_manifest():
    mf = {
        "name": "My Biometric — Dr Manoj Clinic",
        "short_name": "My Biometric",
        "start_url": APP_PREFIX + "/me",
        "scope": APP_PREFIX + "/",
        "display": "standalone",
        "background_color": "#0f2233",
        "theme_color": "#0f2233",
        "icons": [
            {"src": APP_PREFIX + "/pwa-icon-192.png", "sizes": "192x192",
             "type": "image/png"},
            {"src": APP_PREFIX + "/pwa-icon-512.png", "sizes": "512x512",
             "type": "image/png"},
        ],
    }
    resp = make_response(json.dumps(mf))
    resp.headers["Content-Type"] = "application/manifest+json"
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.route(APP_PREFIX + "/pwa-icon-192.png")
def pwa_icon_192():
    resp = make_response(_PWA_ICON_192)
    resp.headers["Content-Type"] = "image/png"
    resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp


@app.route(APP_PREFIX + "/pwa-icon-512.png")
def pwa_icon_512():
    resp = make_response(_PWA_ICON_512)
    resp.headers["Content-Type"] = "image/png"
    resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp


@app.route(APP_PREFIX + "/me", methods=["GET"])
@require(None)
def me_view():
    u = current_user(request)
    con = get_db()
    sid, name, d, times, req = _me_context(con, u["user"])
    holiday = is_holiday(con, d) if sid else False
    con.close()
    if not sid:
        return render_template_string(NO_ACCESS_HTML, who=u,
                                      url_prefix=APP_PREFIX), 403
    can_request = bool(times is not None and not times and not req and not holiday)
    return render_template_string(
        ME_HTML, who=u, name=name, d=d, times=times or [],
        feed_down=(times is None), req=req, can_request=can_request,
        holiday=holiday, prefix=APP_PREFIX,
        msg=request.args.get("m", ""), msgcls=request.args.get("c", "ok"))


@app.route(APP_PREFIX + "/me/request", methods=["POST"])
@require(None)
def me_request():
    u = current_user(request)
    try:
        ts = request_present(u["user"], request.form.get("reason"))
        return redirect(APP_PREFIX + "/me?m=" +
                        ("Request+sent+at+%s" % ts[11:16]) + "&c=ok")
    except PermissionError as e:
        return redirect(APP_PREFIX + "/me?m=%s&c=err" % str(e).replace(" ", "+"))


@app.route(APP_PREFIX + "/present/verify", methods=["POST"])
@require("check")
def present_verify():
    u = current_user(request)
    try:
        verify_present(request.form.get("rid"), u["user"])
        return redirect(APP_PREFIX + "/review?m=Request+verified&c=ok")
    except PermissionError as e:
        return redirect(APP_PREFIX + "/review?m=%s&c=err" % str(e).replace(" ", "+"))


@app.route(APP_PREFIX + "/present/decide", methods=["POST"])
@require(None)
def present_decide():
    u = current_user(request)
    if not u["caps"].get("present"):
        return render_template_string(NO_ACCESS_HTML, who=u,
                                      url_prefix=APP_PREFIX), 403
    try:
        decide_present(request.form.get("rid"), u["user"],
                       request.form.get("action"), request.form.get("note"))
        return redirect(APP_PREFIX + "/review?m=Request+decided&c=ok")
    except PermissionError as e:
        return redirect(APP_PREFIX + "/review?m=%s&c=err" % str(e).replace(" ", "+"))


@app.route(APP_PREFIX + "/present/correct", methods=["POST"])
@require(None)
def present_correct():
    # D338: approver-only past-day presence correction (see correct_present).
    u = current_user(request)
    if not u["caps"].get("present"):
        return render_template_string(NO_ACCESS_HTML, who=u,
                                      url_prefix=APP_PREFIX), 403
    d = request.form.get("d", "")
    try:
        correct_present(u["user"], d, request.form.get("sid"),
                        request.form.get("in_time"), request.form.get("reason"))
        return redirect(APP_PREFIX + "/?d=%s&m=Marked+present+(D338)&c=ok" % d)
    except (PermissionError, ValueError) as e:
        return redirect(APP_PREFIX + "/?d=%s&m=%s&c=err"
                        % (d if _valid_date(d) else _today(),
                           str(e).replace(" ", "+")))


@app.route(APP_PREFIX + "/approve", methods=["POST"])
@require("check")
def approve():
    u = current_user(request)
    d = request.form.get("d", _today())
    back = request.form.get("back", "")
    try:
        approve_date(d, u["user"], u["caps"]["override"])
        if back == "review":
            return redirect(APP_PREFIX + "/review?ym=%s&m=Approved+%s&c=ok" % (d[:7], d))
        return redirect(APP_PREFIX + "/?d=%s&m=Approved+%s&c=ok" % (d, d))
    except (PermissionError, ValueError) as e:
        if back == "review":
            return redirect(APP_PREFIX + "/review?ym=%s&m=%s&c=err"
                            % (d[:7], str(e).replace(" ", "+")))
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Salary lock desk — {{ ym }}</title><style>
body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:#0b1220;color:#e5edf5;margin:0;padding:18px;font-size:16px}
h1{font-size:24px;margin:0 0 10px}
.btnbar{display:flex;gap:12px;align-items:center;margin-bottom:14px;flex-wrap:wrap}
.btn{display:inline-block;padding:10px 18px;border-radius:10px;font-size:17px;font-weight:700;
     background:#13233b;border:1px solid #2e4a6e;color:#bfe3ff;text-decoration:none;cursor:pointer}
.btn.gold{color:#ffd868;border-color:#8a6d1e}
.who{color:#93a4b8;font-size:14px;margin-left:auto}
.mform{display:flex;gap:8px;align-items:center;background:#13233b;border:1px solid #2e4a6e;
       border-radius:10px;padding:6px 12px}
.mform input{background:#0b1b29;border:1px solid #24344a;color:#fff;border-radius:8px;padding:8px;font-size:16px}
.mform button{padding:8px 16px;border-radius:8px;border:none;background:#1e4f8a;color:#fff;font-size:16px;font-weight:700;cursor:pointer}
table{border-collapse:collapse;width:100%;font-size:15px;margin:12px 0}
th,td{border:1px solid #24344a;padding:8px 10px;text-align:right;white-space:nowrap}
th{background:#13233b;color:#cfe0f2}
td.nm,th.nm{text-align:left}
.pos{color:#7ee0a2}.neg{color:#ff9b9b}.zero{color:#6b7c90}
.tot{background:#10203a;font-weight:700}
.note{color:#93a4b8;font-size:14px;margin:8px 0}
.lockcard{border-radius:12px;padding:14px 16px;margin:12px 0;font-size:16px}
.lockcard.locked{background:rgba(34,197,94,.12);border:1px solid #16794a;color:#bbf7d0}
.lockcard.ready{background:rgba(59,130,246,.12);border:1px solid #1e4f8a;color:#cfe0f2}
.lockcard.block{background:#3a1414;border:1px solid #7f1d1d;color:#ffc9c9}
.lockcard.info{background:#12233b;border:1px solid #24344a;color:#cfe0f2}
.lockcard .big{font-size:24px;font-weight:700;margin-bottom:6px}
.datelinks a{display:inline-block;margin:3px 8px 3px 0;padding:4px 10px;border-radius:8px;
  background:#0b1b29;border:1px solid #7f1d1d;color:#ffd0d0;text-decoration:none;font-size:14px}
.lockbtn{border:none;border-radius:12px;padding:14px 24px;font-size:18px;font-weight:700;
  cursor:pointer;color:#fff;background:#16794a}
.unlock{margin-top:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.unlock input[type=text]{background:#0b1b29;border:1px solid #24344a;color:#fff;border-radius:8px;padding:8px;min-width:240px;font-size:15px}
.unlock button{border:none;border-radius:8px;padding:10px 14px;cursor:pointer;color:#fff;background:#7f1d1d;font-size:15px}
.okline{color:#7ee0a2}.badline{color:#ff9b9b}
</style>
<body>
<div class="btnbar">
  <a class="btn" href="{{ prefix }}/">&#128197; Daily register</a>
  <a class="btn" href="{{ prefix }}/salary/flow?ym={{ ym }}">&#128203; Month-end flow</a>
  <a class="btn" href="{{ prefix }}/salary/flow/preview?ym={{ ym }}">&#128196; Salary sheets</a>
  <a class="btn gold" href="{{ prefix }}/salary/policy-settings">&#9881; Settings</a>
  <a class="btn" href="{{ prefix }}/salary/scenario?ym={{ ym }}">&#128202; Scenario</a>
  <a class="btn" href="{{ prefix }}/salary/earlybig?ym={{ ym }}">&#9201; Early-big{% if eb_unruled %} · {{ eb_unruled }}{% endif %}</a>
  <span class="who">{{ who.user }} ({{ who.role }})</span>
</div>
<div class="btnbar"><form method="GET" class="mform">
  <label>Month <input type="month" name="ym" value="{{ ym }}"></label>
  <button type="submit">View</button></form></div>

{% if msg %}<div class="lockcard {{ msg_kind }}">{{ msg }}</div>{% endif %}

{% if locked %}
  <div class="lockcard locked">
    <div class="big">&#128274; LOCKED &mdash; TOTAL PAYOUT &#8377;{{ locked.total_fmt }}</div>
    <div>Official run for {{ ym }} &middot; locked by <b>{{ locked.locked_by }}</b> on {{ locked.locked_ts }}.</div>
    {% if lock_role %}
    <form class="unlock" method="POST" action="{{ prefix }}/salary/unlock"
          onsubmit="return confirm('Unlock {{ ym }}? The official run stays on record until re-locked.');">
      <input type="hidden" name="ym" value="{{ ym }}">
      <input type="text" name="reason" placeholder="unlock reason (required)">
      <button type="submit">Unlock</button>
    </form>{% endif %}
  </div>
{% else %}
  <div class="lockcard {{ 'ready' if can_lock else 'block' }}">
    <div class="big">{{ 'Ready to lock.' if can_lock else 'Not lockable yet.' }}</div>
    <div>{% if blockers.missing or blockers.draft %}<span class="badline">&#10007;</span> {{ (blockers.missing|length) + (blockers.draft|length) }} register date(s) not approved{% else %}<span class="okline">&#10003;</span> every register date approved{% endif %}</div>
    <div>{% if s1 %}<span class="okline">&#10003;</span> Sheet 1 approved ({{ s1.approved_by }}){% else %}<span class="badline">&#10007;</span> Sheet 1 not approved{% endif %}
         &nbsp;·&nbsp; {% if s2 %}<span class="okline">&#10003;</span> Sheet 2 approved ({{ s2.approved_by }}){% else %}<span class="badline">&#10007;</span> Sheet 2 not approved{% endif %}</div>
    <div>{% if enforced %}<span class="okline">&#10003;</span> enforcement covers {{ ym }}{% else %}<span class="badline">&#10007;</span> PREVIEW month — set "ENFORCE FROM" in Settings before this month can lock{% endif %}</div>
    <div>{% if ended %}<span class="okline">&#10003;</span> month ended{% else %}<span class="badline">&#10007;</span> month still running{% endif %}</div>
    {% if blockers.missing or blockers.draft %}
    <div class="datelinks">{% for d in blockers.missing %}<a href="{{ prefix }}/?d={{ d }}">{{ d }}</a>{% endfor %}
      {% for d in blockers.draft %}<a href="{{ prefix }}/?d={{ d }}">{{ d }}</a>{% endfor %}</div>
    {% endif %}
    {% if can_lock and lock_role %}
    <form method="POST" action="{{ prefix }}/salary/lock" style="margin-top:10px"
          onsubmit="return confirm('LOCK {{ ym }} at TOTAL PAYOUT ₹{{ total_fmt }}? This records the official run and writes the hold ledger.');">
      <input type="hidden" name="ym" value="{{ ym }}">
      <button class="lockbtn" type="submit">&#128274; APPROVE &amp; LOCK {{ ym }} — &#8377;{{ total_fmt }}</button>
    </form>{% endif %}
  </div>
{% endif %}

<h1>Salary lock desk — {{ ym }}</h1>
{% if perr %}<div class="lockcard block">New salary engine unreachable: {{ perr }} — no figures can be shown or locked.</div>{% endif %}
{% if rows %}
<p class="note">Computed by the NEW policy engine — identical to Sheet 3 of the month-end flow. Incentive accrues to the Diwali pot (not in NET).</p>
<table><thead><tr><th class="nm">Staff</th><th>Base</th><th>Advance ded.</th><th>Leave amt</th>
<th>Late collect</th><th>Hold</th><th>Released</th><th>Fines</th><th>D+I</th><th>Duty +</th>
<th>Incentive&rarr;pot</th><th>NET</th></tr></thead><tbody>
{% for r in rows %}
<tr><td class="nm"><b>{{ r.name }}</b></td><td>{{ r.base }}</td><td>{{ r.adv }}</td><td>{{ r.leave }}</td>
<td>{{ r.collect }}</td><td>{{ r.hold }}</td><td>{{ r.rel }}</td><td>{{ r.fines }}</td><td>{{ r.di }}</td>
<td>{{ r.duty }}</td><td>{{ r.pot }}</td><td><b>{{ r.net }}</b></td></tr>
{% endfor %}
<tr class="tot"><td class="nm">TOTAL</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>{{ pot_total }}</td><td><b>{{ total_fmt }}</b></td></tr>
</tbody></table>
{% endif %}
<p class="note">This desk locks the month; day-to-day review lives in the Month-end flow. The old computation is retired from this page (dormant fallback in code).</p>
</body>"""


EARLYBIG_PAGE_HTML = """<!doctype html><meta charset="utf-8">
<title>Big early-exit rulings &mdash; {{ ym }}</title><style>{{ css|safe }}
.btnbar{display:flex;gap:12px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
.btnbar a,.btnbar button{cursor:pointer}</style>
<div class="btnbar">
  <a class="pill" href="{{ prefix }}/salary?ym={{ ym }}">&larr; Salary</a>
  <form method="GET" action="{{ prefix }}/salary/earlybig" style="display:flex;gap:6px;align-items:center;margin:0">
    <label class="note">Month <input type="month" name="ym" value="{{ ym }}"
      style="background:#0b1b29;border:1px solid #24344a;color:#fff;border-radius:6px;padding:4px"></label>
    <button class="pill" type="submit">View</button>
  </form>
  <span class="note">signed in as {{ who.user }} ({{ who.role }})</span>
</div>

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


def _ym_shift(ym, delta):
    """ym +/- delta months, wrapping year. 'YYYY-MM' in, 'YYYY-MM' out."""
    y, m = int(ym[:4]), int(ym[5:7])
    m += delta
    while m < 1:
        m += 12; y -= 1
    while m > 12:
        m -= 12; y += 1
    return "%04d-%02d" % (y, m)


def review_board(con, ym, actor=None, is_override=False, can_check=False):
    """Pending-review board for ym. Reuses approval_blockers for the authoritative
    buckets (so the board and the salary lock can never disagree), decorates each
    draft (checker-pending) date with the maker stamp + per-date approve-eligibility
    (D272 self-approve guard), and splits maker-pending into due-now (<= today) vs
    upcoming (future). Read-only."""
    blk = approval_blockers(con, ym)          # {missing, draft, required, approved}
    today = _today()
    draft = []
    for d in blk["draft"]:
        r = review_row(con, d)
        draft.append({
            "d": d,
            "state": (r["state"] if r else "exceptions"),
            "maker_user": (r["maker_user"] if r else ""),
            "maker_ts": (r["maker_ts"] if r else ""),
            "can_approve": bool(can_check and can_check_approve(con, d, actor, is_override)),
        })
    due = [d for d in blk["missing"] if d <= today]       # maker-pending, due now
    upcoming = [d for d in blk["missing"] if d > today]   # future -> not nagged
    # S196: open mark-me-present requests for ym (pending + verified), each with
    # the staff name, the Nth-this-month count (misuse stands out), and per-row
    # eligibility: verify = checker, never his own; decide = PRESENT_APPROVERS,
    # never his own.
    preq = []
    try:
        for r in con.execute(
                "SELECT pr.*, s.name AS staff_name, "
                "(SELECT COUNT(*) FROM present_request p2 WHERE p2.staff_id=pr.staff_id "
                " AND p2.reg_date LIKE ? AND p2.status!='rejected') AS month_n "
                "FROM present_request pr JOIN staff s ON s.staff_id=pr.staff_id "
                "WHERE pr.reg_date LIKE ? AND pr.status IN ('pending','verified') "
                "ORDER BY pr.reg_date, pr.req_ts", (ym + "%", ym + "%")):
            preq.append({
                "id": r["id"], "d": r["reg_date"], "name": r["staff_name"],
                "t": (r["req_ts"] or "")[11:16], "reason": r["reason"],
                "status": r["status"], "month_n": r["month_n"],
                "verify_user": r["verify_user"] or "",
                "can_verify": bool(can_check and r["status"] == "pending"
                                   and r["req_user"] != actor),
                "can_decide": bool(actor in PRESENT_APPROVERS
                                   and r["req_user"] != actor),
            })
    except Exception:
        preq = []            # pre-init DB: table absent -> card shows empty
    return {"ym": ym, "draft": draft, "to_approve": len(draft),
            "due": due, "to_enter": len(due), "upcoming": len(upcoming),
            "approved": blk["approved"], "required": blk["required"],
            "preq": preq, "preq_n": len(preq)}


REVIEW_PAGE_HTML = HEAD + """
<div class="wrap">
  <div class="head">
    <h1>Pending review &mdash; {{ ym }}</h1>
    <div class="sub">&#9997;&#65039; {{ bd.to_enter }} to enter &middot; &#9989; {{ bd.to_approve }} to approve</div>
  </div>
  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}
  <div class="datebar">
    <a href="{{ prefix }}/review?ym={{ prev_ym }}">&#9664; {{ prev_ym }}</a>
    <a href="{{ prefix }}/review?ym={{ next_ym }}">{{ next_ym }} &#9654;</a>
    <a href="{{ prefix }}/">&#128197; Daily register</a>
    {% if caps.salary %}<a href="{{ prefix }}/salary?ym={{ ym }}">&#128176; Salary</a>{% endif %}
  </div>

  {% if bd.preq %}
  <div class="card">
    <h2 style="margin:0 0 8px;font-size:15px;color:#fff">&#128587; Present requests
      <span class="pill draft">{{ bd.preq_n }}</span></h2>
    <div class="note" style="margin:0 0 8px">The request time IS the punch time.
      Verify against who was actually at the clinic; only the doctor's approval counts it.</div>
    <div class="tblwrap"><table>
      <tr><th>Date</th><th>Staff</th><th>Req time</th><th>Reason</th><th>This month</th><th>Status</th><th></th></tr>
      {% for p in bd.preq %}
      <tr>
        <td>{{ p.d }}</td><td class="nm">{{ p.name }}</td><td><b>{{ p.t }}</b></td>
        <td>{{ p.reason }}</td><td>#{{ p.month_n }}</td>
        <td><span class="pill {{ 'approved' if p.status=='verified' else 'draft' }}">{{ p.status|upper }}</span>
            {% if p.verify_user %}<span class="gate">by {{ p.verify_user }}</span>{% endif %}</td>
        <td style="white-space:nowrap">
          {% if p.can_verify %}
          <form method="POST" action="{{ prefix }}/present/verify" style="display:inline">
            <input type="hidden" name="rid" value="{{ p.id }}">
            <button class="btn ghost" type="submit">Verify</button></form>
          {% endif %}
          {% if p.can_decide %}
          <form method="POST" action="{{ prefix }}/present/decide" style="display:inline"
                onsubmit="return confirm('Approve — the request time becomes the punch time?');">
            <input type="hidden" name="rid" value="{{ p.id }}"><input type="hidden" name="action" value="approve">
            <button class="btn green" type="submit">Approve</button></form>
          <form method="POST" action="{{ prefix }}/present/decide" style="display:inline">
            <input type="hidden" name="rid" value="{{ p.id }}"><input type="hidden" name="action" value="reject">
            <button class="btn ghost" type="submit">Reject</button></form>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </table></div>
  </div>
  {% endif %}

  <div class="card">
    <h2 style="margin:0 0 8px;font-size:15px;color:#fff">&#9989; Awaiting approval
      <span class="pill draft">{{ bd.to_approve }}</span></h2>
    {% if bd.draft %}
    <div class="tblwrap"><table>
      <tr><th>Date</th><th>Entry</th><th>Entered by</th><th></th></tr>
      {% for x in bd.draft %}
      <tr>
        <td class="nm"><a href="{{ prefix }}/?d={{ x.d }}" style="color:#93c5fd;text-decoration:none">{{ x.d }}</a></td>
        <td>{% if x.state=='all_clear' %}All clear{% else %}Exceptions{% endif %}</td>
        <td>{{ x.maker_user or "&mdash;" }}{% if x.maker_ts %}<span class="gate"> &middot; {{ x.maker_ts }}</span>{% endif %}</td>
        <td>
          {% if x.can_approve %}
          <form method="POST" action="{{ prefix }}/approve" style="margin:0">
            <input type="hidden" name="d" value="{{ x.d }}">
            <input type="hidden" name="back" value="review">
            <button class="btn green" type="submit" style="padding:7px 14px;font-size:13px">Approve</button>
          </form>
          {% elif caps.check %}<span class="note">you entered &mdash; needs another checker/override</span>
          {% else %}<span class="gate">a checker approves</span>{% endif %}
        </td>
      </tr>
      {% endfor %}
    </table></div>
    {% else %}<div class="note">Nothing waiting for approval. &#9989;</div>{% endif %}
  </div>

  <div class="card">
    <h2 style="margin:0 0 8px;font-size:15px;color:#fff">&#9997;&#65039; Not yet entered
      <span class="pill empty">{{ bd.to_enter }}</span></h2>
    {% if bd.due %}
    <div class="bar" style="margin-top:4px">
      {% for d in bd.due %}<a class="btn ghost" href="{{ prefix }}/?d={{ d }}" style="padding:7px 12px;font-size:13px">{{ d }}</a>{% endfor %}
    </div>
    <div class="note">These days have no entry yet &mdash; a maker must record them (or mark all-clear).</div>
    {% else %}<div class="note">Every day up to today is entered.</div>{% endif %}
    {% if bd.upcoming %}<div class="note">{{ bd.upcoming }} upcoming day(s) not yet due.</div>{% endif %}
  </div>

  <div class="card">
    <h2 style="margin:0 0 8px;font-size:15px;color:#fff">Progress</h2>
    <div class="note">Approved <b style="color:#86efac">{{ bd.approved }}</b> of {{ bd.required }}
      working day(s) this month (clinic-closed holidays excluded).{% if bd.to_approve==0 and bd.to_enter==0 %} Month is clear.{% endif %}</div>
  </div>

  <div class="foot"><a href="{{ prefix }}/">&larr; Back to the daily register</a></div>
</div></body></html>
"""


@app.route(APP_PREFIX + "/review", methods=["GET"])
@require(None)
def review_view():
    u = current_user(request)
    if not u["caps"].get("maker"):          # S196: staff land on their own page
        return redirect(APP_PREFIX + "/me")
    ym = (request.args.get("ym") or "")
    try:
        datetime.date(int(ym[:4]), int(ym[5:7]), 1)
    except Exception:
        ym = _today()[:7]
    con = get_db()
    bd = review_board(con, ym, u["user"], u["caps"]["override"], u["caps"]["check"])
    con.close()
    return render_template_string(
        REVIEW_PAGE_HTML, who=u, caps=u["caps"], prefix=APP_PREFIX, ym=ym,
        prev_ym=_ym_shift(ym, -1), next_ym=_ym_shift(ym, 1), bd=bd,
        msg=request.args.get("m", ""), msgcls=request.args.get("c", "ok"))


# The portal (followup) reads the current-month review counts for its Staff Register
# tile. Cross-origin GET with credentials -> echo the one allowed origin (ACAC=true
# forbids '*'). show_approve is decided HERE by role, so a maker never receives the
# approve count -- one brain for the maker/checker/override display rule.
REVIEW_COUNTS_ORIGINS = {"https://followup.dr-manoj.in"}


@app.route(APP_PREFIX + "/review/counts", methods=["GET"])
@require("maker")
def review_counts():
    u = current_user(request)
    con = get_db()
    bd = review_board(con, _today()[:7], u["user"], u["caps"]["override"], u["caps"]["check"])
    con.close()
    show_approve = bool(u["caps"]["check"])
    payload = {"ym": bd["ym"], "role": u["role"], "to_enter": bd["to_enter"],
               "to_approve": (bd["to_approve"] if show_approve else 0),
               "show_approve": show_approve}
    resp = make_response(json.dumps(payload))
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Cache-Control"] = "no-store"
    origin = request.headers.get("Origin", "")
    if origin in REVIEW_COUNTS_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Vary"] = "Origin"
    return resp


def _render_salary(ym, u, msg="", msg_kind="block"):
    """S199-D: the LOCK DESK — everything from the NEW engine (salary_policy).
    The old engine no longer renders here (dormant fallback in code)."""
    ym = (ym or _default_salary_ym()).strip()
    P, perr = _policy_module()
    rows, total, pot_total, enforced_flag = [], 0.0, 0.0, False
    if P is not None:
        try:
            os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
            res = P.compute(ym)
            enforced_flag = bool(res.get("enforced"))
            for st in res["staff"]:
                di = st["dress_rs"] + st["icard_rs"]
                fines = st["fine_uninf"] + st["fine_exc"]
                rows.append(dict(
                    name=st["name"], base=P.money(st["base"]),
                    adv=P.money(st["adv_ded"]), leave=P.money(st["leave_amt"]),
                    collect=P.money(st["collect"]), hold=P.money(st["held"]),
                    rel=P.money(st["release"]), fines=P.money(fines),
                    di=P.money(di), duty=P.money(st["duty_credits"]),
                    pot=P.money(st["incentive"]), net=P.money(st["net"])))
                total += st["net"]
                pot_total += st["incentive"]
        except Exception as e:
            perr = "%s: %s" % (type(e).__name__, e)
            rows = []
    eb_unruled = 0
    if _SALARY_OK:
        try:
            eb_unruled = _salary.earlybig_unruled(
                _salary.earlybig_events(ym, SALARY_ATT_DIR),
                _salary.load_register_earlybig(ym, DB_PATH))
        except Exception:
            eb_unruled = 0
    con = get_db()
    blk = approval_blockers(con, ym)
    lr = con.execute("SELECT * FROM locked_run WHERE ym=?", (ym,)).fetchone()
    con.close()
    st_pack = pack_status(ym)
    lr = dict(lr) if lr else None
    is_locked = bool(lr and lr.get("status") == "locked")
    if lr is not None:
        lr["total_fmt"] = "{:,}".format(int(lr["total_payout"]))
    total_fmt = "{:,}".format(int(round(total)))
    ended = month_has_ended(ym)
    lock_role = bool(u["caps"].get("lock"))
    can_lock = (lock_role and ended and bool(rows) and (not is_locked)
                and not blk["missing"] and not blk["draft"]
                and bool(st_pack.get("sheet1")) and bool(st_pack.get("sheet2"))
                and enforced_flag)
    return render_template_string(
        SALARY_PAGE_HTML, who=u, prefix=APP_PREFIX, ym=ym,
        blockers=blk, locked=(lr if is_locked else None), can_lock=can_lock,
        ended=ended, total_fmt=total_fmt, lock_role=lock_role,
        eb_unruled=eb_unruled, msg=msg, msg_kind=msg_kind,
        rows=rows, pot_total=(P.money(pot_total) if P and rows else "0"),
        perr=(perr if not rows else ""), enforced=enforced_flag,
        s1=st_pack.get("sheet1"), s2=st_pack.get("sheet2"))


@app.route(APP_PREFIX + "/salary")
@require("salary")
def salary_view():
    return _render_salary(request.args.get("ym"), current_user(request))


# --- Deduction scenario (S199, kit S199_SCEN2): read-only what-if beside the
# salary run. Same salary gate (manoj/bhawna). Imports att_scenario.py from the
# attendance root (/root) fail-soft; NEVER writes a file and NEVER touches pay.
def _scenario_module():
    """(module, '') or (None, reason). att_scenario + att_month_report + att_core
    + att_config live in the attendance root; add it to sys.path guarded."""
    for d in ("/root", os.path.dirname(SALARY_ATT_DIR) if SALARY_ATT_DIR else "",
              SALARY_ATT_DIR):
        if d and os.path.isdir(d) and d not in sys.path:
            sys.path.append(d)
    try:
        import att_scenario as _S
        return _S, ""
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


@app.route(APP_PREFIX + "/salary/scenario")
@require("salary")
def salary_scenario():
    ym = (request.args.get("ym") or _today()[:7]).strip()
    if not _valid_ym(ym):
        ym = _today()[:7]
    back = "%s/salary?ym=%s" % (APP_PREFIX, ym)
    mod, err = _scenario_module()
    if mod is None:
        return render_template_string(
            SCENARIO_SHELL_HTML, prefix=APP_PREFIX, ym=ym, back=back,
            inner=("<div style='background:#3a1414;border:1px solid #7a2a2a;"
                   "padding:12px;border-radius:8px'>The attendance scenario tool "
                   "is not reachable from this server (%s). It can still be run "
                   "from the shell.</div>" % html.escape(err))), 200
    try:
        os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
        rows, note, gerr, limits = mod.build(ym)
        doc = mod.render_document(ym, rows, note, gerr, limits, back_href=back)
        return doc, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return render_template_string(
            SCENARIO_SHELL_HTML, prefix=APP_PREFIX, ym=ym, back=back,
            inner=("<div style='background:#3a1414;border:1px solid #7a2a2a;"
                   "padding:12px;border-radius:8px'>Could not build the scenario "
                   "for %s: %s</div>" % (html.escape(ym), html.escape(str(e))))), 200


SCENARIO_SHELL_HTML = """<!doctype html><meta charset="utf-8">
<title>Deduction scenario {{ ym }}</title>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#0b1b29;color:#eee;margin:18px">
<a href="{{ back }}" style="color:#5fd;text-decoration:none;font-weight:bold">&larr; Back to Salary</a>
<h1 style="font-size:17px">Deduction scenario &mdash; {{ ym }}</h1>
{{ inner|safe }}
</body>"""


# =====================================================================
# S199 — THE MONTH-END FLOW (Sheet1/Sheet2 pack -> approval -> salary)
# All computation lives in salary_policy.py (fail-soft import); these
# routes are thin doors. PREVIEW is standard: nothing writes until a
# month is locked AND covered by the enforcement date.
# =====================================================================
def _policy_module():
    for dd in (APP_DIR, "/root/staff_register", "/root", SALARY_ATT_DIR or ""):
        if dd and os.path.isdir(dd) and dd not in sys.path:
            sys.path.append(dd)
    try:
        import salary_policy as _P
        return _P, ""
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)


def _pack_table(con):
    con.execute("CREATE TABLE IF NOT EXISTS pack_approval ("
                "ym TEXT NOT NULL, sheet TEXT NOT NULL, approved_by TEXT, "
                "approved_ts TEXT, PRIMARY KEY (ym, sheet))")


def pack_status(ym):
    con = get_db(); _pack_table(con)
    rows = {r["sheet"]: dict(r) for r in con.execute(
        "SELECT * FROM pack_approval WHERE ym=?", (ym,))}
    con.close()
    return rows


def _flow_ym():
    ym = (request.args.get("ym") or _today()[:7]).strip()
    return ym if _valid_ym(ym) else _today()[:7]


FLOW_SHELL = """<!doctype html><meta charset="utf-8">
<title>Month-end flow {{ ym }}</title>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#0b1b29;color:#eee;margin:18px">
<a href="{{ prefix }}/salary?ym={{ ym }}" style="color:#5fd;text-decoration:none;font-weight:bold">&larr; Salary</a>
<h1 style="font-size:18px">Month-end flow &mdash; {{ ym }}</h1>
{% if msg %}<div style="background:#274; padding:6px 10px;border-radius:6px;margin:6px 0">{{ msg }}</div>{% endif %}
{% if err %}<div style="background:#733;padding:6px 10px;border-radius:6px;margin:6px 0">{{ err }}</div>{% endif %}
<div style="margin:8px 0;display:flex;gap:8px;flex-wrap:wrap">
  <form method="GET" style="margin:0"><label>Month <input type="month" name="ym" value="{{ ym }}"
    style="background:#0b1b29;border:1px solid #24344a;color:#fff;border-radius:6px;padding:4px"></label>
    <button style="padding:4px 10px">View</button></form>
  <a href="{{ prefix }}/salary/policy-settings" style="color:#fd5">&#9881; Fines &amp; policy settings</a>
</div>
<ol style="line-height:2">
  <li><a href="{{ prefix }}/salary/flow/sheet1?ym={{ ym }}" style="color:#5fd">SHEET 1 — attendance grid</a>
      (<a href="{{ prefix }}/salary/flow/sheet1?ym={{ ym }}&print=1" style="color:#8ac">print</a>)
      {% if s1 %}&#9989; approved by {{ s1.approved_by }} {{ s1.approved_ts }}{% else %}
      <form method="POST" action="{{ prefix }}/salary/flow/approve" style="display:inline">
        <input type="hidden" name="ym" value="{{ ym }}"><input type="hidden" name="sheet" value="sheet1">
        <button style="padding:2px 10px">Approve Sheet 1</button></form>{% endif %}</li>
  <li><a href="{{ prefix }}/salary/flow/sheet2?ym={{ ym }}" style="color:#5fd">SHEET 2 — advances, loans &amp; holds</a>
      · <a href="{{ prefix }}/salary/flow/sheet2?ym={{ ym }}&staff=Darpan" style="color:#fd5">Darpan's page</a>
      {% if s2 %}&#9989; approved by {{ s2.approved_by }} {{ s2.approved_ts }}{% else %}
      <form method="POST" action="{{ prefix }}/salary/flow/approve" style="display:inline">
        <input type="hidden" name="ym" value="{{ ym }}"><input type="hidden" name="sheet" value="sheet2">
        <button style="padding:2px 10px">Approve Sheet 2</button></form>{% endif %}</li>
  <li><a href="{{ prefix }}/salary/flow/preview?ym={{ ym }}" style="color:#5fd">SHEETS 3+4 — salary computation</a>
      (print from that page){% if not (s1 and s2) %} &mdash; <i>working preview until both sheets approved</i>{% endif %}</li>
</ol>
{% if remarks %}<h2 style="font-size:15px">&#9997;&#65039; Staff remarks awaiting review</h2>
<table style="border-collapse:collapse">{% for r in remarks %}
 <tr><td style="padding:3px 10px;color:#cde">{{ r.reg_date }}</td>
     <td style="padding:3px 10px"><b>{{ r.name }}</b></td>
     <td style="padding:3px 10px">{{ r.remark }}</td>
     <td><a href="{{ prefix }}/?d={{ r.reg_date }}" style="color:#5fd">open day</a></td>
     <td><form method="POST" action="{{ prefix }}/salary/flow/remark-done" style="margin:0">
       <input type="hidden" name="ym" value="{{ ym }}"><input type="hidden" name="sid" value="{{ r.staff_id }}">
       <input type="hidden" name="d" value="{{ r.reg_date }}">
       <button style="padding:1px 8px">handled</button></form></td></tr>
{% endfor %}</table>{% endif %}
<p style="color:#9ab">Corrections: open a day/leave from Sheet 1 (it links to the register page),
or defer/waive money items in the Ledger from Sheet 2 — then reload. The sheets always
recompute from the stores. PREVIEW is standard: nothing touches pay until the month is
locked AND the enforcement date covers it.</p>
</body>"""


@app.route(APP_PREFIX + "/salary/flow")
@require("salary")
def salary_flow():
    ym = _flow_ym()
    st = pack_status(ym)
    con = get_db(); _remark_table(con)
    remarks = [dict(r) | {"name": (con.execute("SELECT name FROM staff WHERE staff_id=?",
                                               (r["staff_id"],)).fetchone() or {"name": "#%d" % r["staff_id"]})["name"]}
               for r in con.execute("SELECT * FROM month_remark WHERE ym=? AND status='open' "
                                    "ORDER BY reg_date", (ym,))]
    con.close()
    return render_template_string(FLOW_SHELL, prefix=APP_PREFIX, ym=ym,
                                  s1=st.get("sheet1"), s2=st.get("sheet2"), remarks=remarks,
                                  msg=request.args.get("msg", ""), err="")


@app.route(APP_PREFIX + "/salary/flow/approve", methods=["POST"])
@require("salary")
def salary_flow_approve():
    u = current_user(request)
    ym = (request.form.get("ym") or "").strip()
    sheet = (request.form.get("sheet") or "").strip()
    if not _valid_ym(ym) or sheet not in ("sheet1", "sheet2"):
        return redirect(APP_PREFIX + "/salary/flow?ym=" + (ym or _today()[:7]))
    con = get_db(); _pack_table(con)
    con.execute("INSERT OR REPLACE INTO pack_approval (ym, sheet, approved_by, "
                "approved_ts) VALUES (?,?,?,?)", (ym, sheet, u["user"], _now()))
    _audit(con, "salary", ym, "pack_approve", "", sheet, u["user"])
    con.commit(); con.close()
    return redirect(APP_PREFIX + "/salary/flow?ym=%s&msg=%s approved" % (ym, sheet))


@app.route(APP_PREFIX + "/salary/flow/remark-done", methods=["POST"])
@require("salary")
def salary_flow_remark_done():
    u = current_user(request)
    ym = (request.form.get("ym") or "").strip()
    try:
        sid = int(request.form.get("sid") or 0)
    except ValueError:
        sid = 0
    d = (request.form.get("d") or "").strip()
    con = get_db(); _remark_table(con)
    con.execute("UPDATE month_remark SET status='handled', decided_by=?, decided_ts=? "
                "WHERE ym=? AND staff_id=? AND reg_date=?", (u["user"], _now(), ym, sid, d))
    _audit(con, "remark", d, "handled", "open", "", u["user"])
    con.commit(); con.close()
    return redirect(APP_PREFIX + "/salary/flow?ym=" + ym)


def _flow_doc(kind):
    ym = _flow_ym()
    P, err = _policy_module()
    if P is None:
        return render_template_string(FLOW_SHELL, prefix=APP_PREFIX, ym=ym,
                                      s1=None, s2=None, msg="",
                                      err="salary_policy not reachable: %s" % err)
    try:
        os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
        res = P.compute(ym)
        back = "%s/salary/flow?ym=%s" % (APP_PREFIX, ym)
        if kind == "sheet1":
            doc = P.sheet1_html(res, doors=(not request.args.get("print")),
                                prefix=APP_PREFIX, back=back,
                                print_=bool(request.args.get("print")))
        elif kind == "sheet2":
            doc = P.sheet2_html(res, doors=True, back=back, prefix=APP_PREFIX,
                                staff=(request.args.get("staff") or None))
        else:
            st = pack_status(ym)
            doc = P.sheets34_html(res, back=back, prefix=APP_PREFIX,
                                  approved=bool(st.get("sheet1") and st.get("sheet2")))
        return doc, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return render_template_string(FLOW_SHELL, prefix=APP_PREFIX, ym=ym,
                                      s1=None, s2=None, msg="",
                                      err="could not build %s: %s" % (kind, e))


@app.route(APP_PREFIX + "/salary/flow/sheet1")
@require("salary")
def salary_flow_sheet1():
    return _flow_doc("sheet1")


@app.route(APP_PREFIX + "/salary/flow/sheet2")
@require("salary")
def salary_flow_sheet2():
    return _flow_doc("sheet2")


@app.route(APP_PREFIX + "/salary/flow/preview")
@require("salary")
def salary_flow_preview():
    return _flow_doc("preview")


SETTINGS_LABELS = [
    ("free_late_min", "Free late minutes per month (over the 10-min x8 grace)"),
    ("band1_end", "Band 1 ends at (cumulative minutes)"),
    ("band2_end", "Band 2 ends at (cumulative minutes)"),
    ("mult1", "Band 1 multiplier (x own salary minute-rate)"),
    ("mult2", "Band 2 multiplier"),
    ("mult3", "Band 3 multiplier (chronic tail)"),
    ("collect_now_pct", "Late charge collected now (%); rest goes to HOLD"),
    ("improve_pct", "Improvement (%) that releases last month's hold"),
    ("hold_enabled", "Hold enabled (1 = yes, 0 = collect everything)"),
    ("dress_rs", "Dress fine Rs/day without"),
    ("icard_rs", "I-card fine Rs/day without"),
    ("fine_uninformed", "Uninformed-absence fine (Rs)"),
    ("fine_excess", "Excess-absence fine Rs/day"),
    ("excess_free_days", "Excess-absence free days"),
    ("incentive_full_marks", "FULL-day incentive if marks <="),
    ("incentive_half_marks", "HALF-day incentive if marks <="),
    ("day_divisor", "Day-rate divisor (salary / this)"),
    ("require_pack_approval", "Salary lock needs Sheet1+Sheet2 approval (1/0)"),
    ("min_charge_rs", "Minimum late charge (below this = Rs.0)"),
    ("extra_duty_rs", "Extra-duty credit Rs/day"),
    ("outstation_rs", "Outstation credit Rs/night"),
    ("staff_view_current", "Staff see the RUNNING month live (1/0)"),
    ("staff_view_after_lock_days", "Staff month view disappears N days after lock"),
    ("staff_remarks_enabled", "Staff may raise day remarks (1/0)"),
    ("enforce_from", "ENFORCE FROM month (YYYY-MM; empty = preview only)"),
]

SETTINGS_HTML = """<!doctype html><meta charset="utf-8">
<title>Fines &amp; policy settings</title>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#0b1b29;color:#eee;margin:18px">
<a href="{{ prefix }}/salary/flow" style="color:#5fd;font-weight:bold;text-decoration:none">&larr; Month-end flow</a>
<h1 style="font-size:18px">Fines &amp; policy settings</h1>
<p style="color:#9ab">Recalibration happens HERE — never in code (owner ruling, D332 pattern).
Changes apply to every preview and to future computations immediately. Every change is audited.</p>
{% if msg %}<div style="background:#274;padding:6px 10px;border-radius:6px">{{ msg }}</div>{% endif %}
{% if err %}<div style="background:#733;padding:6px 10px;border-radius:6px">{{ err }}</div>{% endif %}
<form method="POST"><table style="border-collapse:collapse">
{% for key, label, val in rows %}
 <tr><td style="padding:4px 10px 4px 0;color:#cde">{{ label }}</td>
     <td><input name="{{ key }}" value="{{ val }}"
       style="background:#12283c;border:1px solid #24344a;color:#fff;border-radius:6px;padding:4px;width:110px"></td></tr>
{% endfor %}
</table><button style="margin-top:10px;padding:6px 16px">Save settings</button></form>
</body>"""


@app.route(APP_PREFIX + "/salary/policy-settings", methods=["GET", "POST"])
@require("salary")
def salary_policy_settings():
    u = current_user(request)
    P, perr = _policy_module()
    if P is None:
        return render_template_string(SETTINGS_HTML, prefix=APP_PREFIX, rows=[],
                                      msg="", err="salary_policy not reachable: %s" % perr)
    msg = err = ""
    if request.method == "POST":
        if not u["caps"].get("lock"):
            err = "Only the doctor changes policy settings."
        else:
            ok, e2 = P.save_settings({k: request.form.get(k) for k, _l in SETTINGS_LABELS},
                                     by=u["user"])
            msg, err = ("Settings saved.", "") if ok else ("", e2)
    s = P.load_settings()
    rows = [(k, lab, s.get(k, "")) for k, lab in SETTINGS_LABELS]
    return render_template_string(SETTINGS_HTML, prefix=APP_PREFIX, rows=rows,
                                  msg=msg, err=err)


def _remark_table(con):
    con.execute("CREATE TABLE IF NOT EXISTS month_remark ("
                "ym TEXT NOT NULL, staff_id INTEGER NOT NULL, reg_date TEXT NOT NULL, "
                "remark TEXT NOT NULL, raised_ts TEXT, status TEXT NOT NULL DEFAULT 'open', "
                "decided_by TEXT, decided_ts TEXT, PRIMARY KEY (ym, staff_id, reg_date))")


def _staff_month_visible(ym, s):
    """The owner's windows (S199-B, all settings): the running month live if
    staff_view_current; a completed month from its end until N days after the
    salary lock (no lock yet = still visible)."""
    today = _today()
    cur = today[:7]
    if ym > cur:
        return False, "that month has not started"
    if ym == cur:
        return (bool(int(s.get("staff_view_current", 1))), "the running month opens per settings")
    con = get_db()
    lr = con.execute("SELECT locked_ts, status FROM locked_run WHERE ym=?", (ym,)).fetchone()
    con.close()
    if lr and lr["status"] == "locked" and lr["locked_ts"]:
        try:
            lt = datetime.datetime.strptime(lr["locked_ts"][:10], "%Y-%m-%d").date()
            days = int(s.get("staff_view_after_lock_days", 5))
            if datetime.date.fromisoformat(today) > lt + datetime.timedelta(days=days):
                return False, "this month's sheet is closed (salary finalised)"
        except (ValueError, TypeError):
            pass
    return True, ""


REMARK_FORM_HTML = """
<div style="max-width:640px;margin:14px auto;padding:10px;border:1px solid #ccc;border-radius:8px;background:#fbf9f4">
 <b>&#9997;&#65039; कोई दिन गलत लगे? / Raise a remark for the doctor's review</b>
 <form method="POST" action="{prefix}/me/month/remark" style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
  <input type="hidden" name="ym" value="{ym}">
  <input type="date" name="d" min="{ym}-01" max="{maxd}" required style="padding:4px">
  <input type="text" name="remark" maxlength="200" required placeholder="उस दिन क्या हुआ था / what happened that day"
         style="flex:1;min-width:220px;padding:4px">
  <button style="padding:4px 12px">Send</button>
 </form>
 {mine}
</div>"""


@app.route(APP_PREFIX + "/me/month/remark", methods=["POST"])
@require(None)
def me_month_remark():
    u = current_user(request)
    sid = _self_sid(u["user"]) if u else None
    ym = (request.form.get("ym") or "").strip()
    d = (request.form.get("d") or "").strip()
    txt = (request.form.get("remark") or "").strip()[:200]
    P, _e = _policy_module()
    s = P.load_settings() if P else {}
    if not (sid and _valid_ym(ym) and d.startswith(ym) and txt
            and int(s.get("staff_remarks_enabled", 1))):
        return redirect(APP_PREFIX + "/me/month?ym=" + (ym or _today()[:7]))
    ok, _why = _staff_month_visible(ym, s)
    if not ok:
        return redirect(APP_PREFIX + "/me/month?ym=" + ym)
    con = get_db(); _remark_table(con)
    con.execute("INSERT OR REPLACE INTO month_remark (ym, staff_id, reg_date, remark, "
                "raised_ts, status) VALUES (?,?,?,?,?, 'open')",
                (ym, sid, d, txt, _now()))
    _audit(con, "remark", d, "raise", "", txt, u["user"])
    con.commit(); con.close()
    return redirect(APP_PREFIX + "/me/month?ym=" + ym)


@app.route(APP_PREFIX + "/me/month")
@require(None)
def me_month():
    """A staff member's OWN month grid — no other staff, no money (S199).
    Visibility windows + the remark form are the owner's settings (S199-B)."""
    u = current_user(request)
    con = get_db()
    sid = _self_sid(u["user"]) if u else None
    name = None
    if sid:
        r = con.execute("SELECT name FROM staff WHERE staff_id=?", (sid,)).fetchone()
        name = r["name"] if r else None
    con.close()
    if not u or (not name and not u["caps"].get("salary")):
        return render_template_string(NO_ACCESS_HTML, who=u, url_prefix=APP_PREFIX), 403
    ym = _flow_ym()
    P, perr = _policy_module()
    if P is None:
        return "attendance view unavailable (%s)" % html.escape(perr), 200
    s = P.load_settings()
    if name:                                   # windows apply to STAFF, never the owner
        ok, why = _staff_month_visible(ym, s)
        if not ok:
            return ("<body style='font-family:Segoe UI,Arial,sans-serif;margin:24px'>"
                    "<a href='%s/me'>&larr; Back</a><p>%s</p></body>"
                    % (APP_PREFIX, html.escape(why))), 200
    try:
        os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
        res = P.compute(ym, with_prev=False)
        uid = None
        if name:
            for st in res["staff"]:
                if st["name"].strip().lower() == name.strip().lower():
                    uid = st["uid"]
                    break
            if uid is None:
                return "no attendance record found for %s" % html.escape(name), 200
        doc = P.sheet1_html(res, doors=False, only_uid=uid,
                            back=APP_PREFIX + "/me" if name else APP_PREFIX + "/salary/flow?ym=" + ym)
        if name and int(s.get("staff_remarks_enabled", 1)):
            con = get_db(); _remark_table(con)
            mine = con.execute("SELECT * FROM month_remark WHERE ym=? AND staff_id=? "
                               "ORDER BY reg_date", (ym, sid)).fetchall()
            con.close()
            mine_html = ""
            if mine:
                mine_html = "<div style='margin-top:8px;font-size:13px'><b>आपके रिमार्क / your remarks:</b><ul>" + "".join(
                    "<li>%s — %s <i>(%s)</i></li>" % (html.escape(m["reg_date"]),
                                                      html.escape(m["remark"]),
                                                      "seen by doctor" if m["status"] != "open" else "waiting")
                    for m in mine) + "</ul></div>"
            import calendar as _cal
            maxd = "%s-%02d" % (ym, _cal.monthrange(int(ym[:4]), int(ym[5:7]))[1])
            form = REMARK_FORM_HTML.format(prefix=APP_PREFIX, ym=ym, maxd=maxd, mine=mine_html)
            doc = doc.replace("</body></html>", form + "</body></html>")
        return doc, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return "could not build the month view: %s" % html.escape(str(e)), 200




@app.route(APP_PREFIX + "/salary/lock", methods=["POST"])
@require("lock")
def salary_lock():
    u = current_user(request)
    ym = (request.form.get("ym") or "").strip()
    if not _valid_ym(ym):
        return _render_salary(ym, u, "Bad month.")
    P, perr = _policy_module()
    if P is None:
        return _render_salary(ym, u, "New salary engine unavailable (%s); cannot lock." % perr)
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
    if int(P.load_settings().get("require_pack_approval", 1)):
        _st = pack_status(ym)
        if not (_st.get("sheet1") and _st.get("sheet2")):
            return _render_salary(ym, u,
                "Sheet 1 / Sheet 2 of the month-end flow are not approved yet "
                "\u2014 review and approve the pack, then lock.")
    try:
        os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
        res = P.compute(ym)
    except Exception as e:
        return _render_salary(ym, u, "Could not compute the run: %s" % e)
    if not res.get("enforced"):
        return _render_salary(ym, u,
            "This month is PREVIEW \u2014 enforcement does not cover it. Set "
            "'ENFORCE FROM' in the policy settings first (D332: enforcement is "
            "a deliberate switch, never an accident).")
    total = round(sum(st["net"] for st in res["staff"]))
    report_html = P.sheets34_html(res, approved=True, prefix=APP_PREFIX)
    # S199-D: the lock is the REAL event — write the hold ledger, once per
    # (staff, month); a re-lock after unlock never double-appends (guard below).
    existing = P.hold_state()
    pm = P.prev_ym(ym)
    for st in res["staff"]:
        if st["held"] > 0 and (st["name"], ym) not in existing:
            P.append_hold({"id": secrets.token_hex(6), "ym": ym, "staff": st["name"],
                           "computed": st["late_charge"], "collected": st["collect"],
                           "held": st["held"], "ts": _now(), "by": u["user"]})
        if st["release"] > 0:
            ph = existing.get((st["name"], pm))
            if ph and ph["status"] == "HELD":
                P.append_hold({"id": secrets.token_hex(6), "action": "RELEASE",
                               "staff": st["name"], "ym": pm,
                               "amount": st["release"], "reason": st["release_note"],
                               "by": u["user"], "ts": _now()})
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
    _audit(con, "salary", ym, "lock", "", "TOTAL PAYOUT %d locked (new engine)" % int(total), u["user"])
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


# --- Big early-exit rulings (D288 / S163): the register's own ruling screen, so
# the ledger salary page can be retired. VIEW+RULE = salary cap (Manoj + Bhawna);
# a locked month is read-only. The engine READS these verdicts; this app is the
# sole writer of earlybig_ruling.
@app.route(APP_PREFIX + "/salary/earlybig")
@require("salary")
def salary_earlybig():
    u = current_user(request)
    ym = (request.args.get("ym") or _default_salary_ym()).strip()
    if not _valid_ym(ym):
        ym = _default_salary_ym()
    css = _salary._CSS if _SALARY_OK else ""
    if not _SALARY_OK:
        body = "<div class='warn'>Salary engine unavailable on this server.</div>"
    else:
        try:
            events = _salary.earlybig_events(ym, SALARY_ATT_DIR)
        except Exception:
            events = None
        verdicts = _salary.load_register_earlybig(ym, DB_PATH)
        con = get_db()
        lr = con.execute("SELECT status FROM locked_run WHERE ym=?", (ym,)).fetchone()
        con.close()
        locked = bool(lr and lr["status"] == "locked")
        body = _salary.render_earlybig_html(ym, events, verdicts, locked, APP_PREFIX)
    return render_template_string(EARLYBIG_PAGE_HTML, who=u, prefix=APP_PREFIX,
                                  ym=ym, css=css, body=body)


@app.route(APP_PREFIX + "/salary/earlybig", methods=["POST"])
@require("salary")
def salary_earlybig_save():
    u = current_user(request)
    ym = (request.form.get("ym") or "").strip()
    if not _valid_ym(ym):
        return redirect(APP_PREFIX + "/salary/earlybig")
    if not _SALARY_OK:
        return redirect(APP_PREFIX + "/salary/earlybig?ym=" + ym)
    con = get_db()
    lr = con.execute("SELECT status FROM locked_run WHERE ym=?", (ym,)).fetchone()
    if lr and lr["status"] == "locked":
        con.close()
        return redirect(APP_PREFIX + "/salary/earlybig?ym=" + ym)
    con.executescript(_salary.EARLYBIG_SCHEMA)      # idempotent: table may predate --init
    try:                                            # only accept real events this month
        valid = set("%s|%s" % (e["name"], e["date"])
                    for e in _salary.earlybig_events(ym, SALARY_ATT_DIR))
    except Exception:
        valid = set()
    for k, v in request.form.items():
        if not k.startswith("eb_"):
            continue
        key = k[3:]
        if key not in valid:
            continue
        staff, _sep, ebdate = key.partition("|")
        verdict = "genuine" if v == "genuine" else "waived"
        prev = con.execute("SELECT verdict FROM earlybig_ruling WHERE ym=? AND staff=? "
                           "AND ebdate=?", (ym, staff, ebdate)).fetchone()
        con.execute("INSERT OR REPLACE INTO earlybig_ruling"
                    "(ym,staff,ebdate,verdict,ruled_by,ruled_ts) VALUES(?,?,?,?,?,?)",
                    (ym, staff, ebdate, verdict, u["user"], _now()))
        if (prev["verdict"] if prev else None) != verdict:
            _audit(con, "earlybig", "%s|%s|%s" % (ym, staff, ebdate), "rule",
                   (prev["verdict"] if prev else ""), verdict, u["user"])
    con.commit()
    con.close()
    return redirect(APP_PREFIX + "/salary/earlybig?ym=" + ym)


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
    form = F({"s1_late": "manoj", "s1_dress": "no",
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
                            "s4_dress": "no", "s4_extra": "on", "s4_outstation": "5"}),
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
    save_maker(d, False, F({"s1_leave": "manoj", "s1_late": "manoj", "s1_dress": "no"}), "alisha")
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
    assert c.get(APP_PREFIX + "/salary/scenario").status_code == 200
    assert c.get(APP_PREFIX + "/salary/flow").status_code == 200
    assert c.get(APP_PREFIX + "/salary/policy-settings").status_code == 200
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
    # ---- pending-review board (S164, F-63) ----
    save_maker(_today(), True, {}, "alisha")           # fresh all-clear DRAFT for today
    _rv = _today()[:7]
    rB = c3.get(APP_PREFIX + "/review?ym=" + _rv)       # shavez (checker) did NOT enter it
    assert rB.status_code == 200 and b"Pending review" in rB.data
    assert _today().encode() in rB.data, "today's draft must show on the board"
    assert b">Approve<" in rB.data, "checker sees an approve control for a maker's draft"
    rM = c2.get(APP_PREFIX + "/review?ym=" + _rv)       # alisha (maker): board visible...
    assert rM.status_code == 200 and b"Pending review" in rM.data
    assert b">Approve<" not in rM.data, "maker sees no approve control"
    # counts endpoint (portal tile source): role decides show_approve; CORS echo
    rC = c3.get(APP_PREFIX + "/review/counts",
                headers={"Origin": "https://followup.dr-manoj.in"})   # shavez=checker
    assert rC.status_code == 200
    jC = json.loads(rC.data)
    assert jC["show_approve"] is True and "to_approve" in jC and "to_enter" in jC
    assert rC.headers.get("Access-Control-Allow-Origin") == "https://followup.dr-manoj.in"
    rCm = c2.get(APP_PREFIX + "/review/counts")                       # alisha=maker
    assert rCm.status_code == 200 and json.loads(rCm.data)["show_approve"] is False
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

    # ================= S196: machine late + self page + present requests =====
    global SR_PUNCH_CSV, SR_STAFF_MASTER
    _old_punch, _old_sm = SR_PUNCH_CSV, SR_STAFF_MASTER
    SR_PUNCH_CSV = os.path.join(tmp, "punches.csv")
    SR_STAFF_MASTER = os.path.join(tmp, "staff_master.csv")
    with open(SR_STAFF_MASTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "name", "department", "base_salary", "allowed_offs",
                    "wd_start", "wd_end", "sun_start", "sun_end", "active",
                    "timing_note", "sunday_group", "minutes_exempt"])
        w.writerow([1, "Demo A", "X", 10000, 2, "09:30", "18:00", "", "", "Y", "", "A", "N"])
        w.writerow([2, "Shivani X", "X", 10000, 2, "09:30", "18:00", "", "", "Y", "", "B", "N"])
        w.writerow([4, "Arjun", "X", 6000, 2, "09:30", "18:00", "09:30", "14:00", "Y", "", "ARJ", "Y"])
        w.writerow([6, "Sukhveer T", "X", 9000, 2, "09:30", "18:00", "10:00", "14:00", "Y", "", "C", "N"])
        w.writerow([7, "Ranjeet K", "X", 9000, 2, "09:30", "18:00", "", "", "Y", "", "A", "N"])
        w.writerow([9, "Sandip J", "X", 9000, 2, "09:30", "18:00", "", "", "Y", "", "B", "N"])
    d2 = "2026-08-06"                              # Thursday, pre-roster
    d3 = "2026-09-06"                              # 1st Sunday of Sep — ROSTER era
    with open(SR_PUNCH_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "datetime"])
        w.writerow([1, d2 + " 10:44:00"])          # 74 min late (>=60 -> loud)
        w.writerow([1, d2 + " 10:44:00"])          # duplicate row: must de-dup
        w.writerow([2, d2 + " 09:35:00"])          # 5 min (grace band, quiet line)
        w.writerow([4, d2 + " 11:00:00"])          # Arjun: minutes_exempt -> late 0
        w.writerow([1, d3 + " 10:31:00"])          # group A duty Sunday -> 61 late
        w.writerow([2, d3 + " 10:31:00"])          # group B OFF Sunday -> off, late 0
        w.writerow([7, _today() + " 10:00:00"])    # Ranjeet HAS a punch today
    con = get_db()
    m2 = machine_day(con, d2)
    assert m2[1]["late"] == 74 and m2[1]["in"] == "10:44" and m2[1]["n"] == 1, m2[1]
    assert m2[2]["late"] == 5, "grace-band minutes must still be exact"
    assert m2[4]["late"] == 0, "minutes_exempt (Arjun) never gets machine late"
    m3 = machine_day(con, d3)
    assert m3[1]["late"] == 61, "roster Sunday (A on 1st) uses the weekday shift"
    assert m3[2]["off"] is True and m3[2]["late"] == 0, "B on 1st Sunday is OFF"
    con.close()
    # save stores the machine minutes as a read-only fact (form cannot supply it)
    save_maker(d2, False, F({"s1_late": "manoj", "s1_late_minutes": "3"}), "alisha")
    con = get_db()
    lr_ = con.execute("SELECT late_minutes FROM daily_register WHERE reg_date=? "
                      "AND staff_id=1", (d2,)).fetchone()
    assert lr_["late_minutes"] == 74, "late_minutes must come from the machine, not the form"
    con.close()
    r = c.get(APP_PREFIX + "/?d=" + d2)            # manoj's grid shows the loud badge
    assert r.status_code == 200 and b"74 min late (machine)" in r.data
    assert b"in 09:35" in r.data, "sub-60 lates show quietly with the in-time"
    # --- self role: mapping, today-only page, request flow --------------------
    con = get_db()
    for sid, nm in ((6, "Sukhveer T"), (7, "Ranjeet K"), (8, "Shavez P"), (9, "Sandip J")):
        con.execute("INSERT OR IGNORE INTO staff(staff_id,name,join_date,base_salary,active) "
                    "VALUES(?,?, '2026-01-01', 9000, 1)", (sid, nm))
    con.execute("UPDATE staff SET username='sukhveer' WHERE staff_id=6")   # exact map
    con.commit()
    assert staff_for_user(con, "sukhveer") == 6, "exact username mapping"
    assert staff_for_user(con, "ranjeet") == 7, "first-name fallback mapping"
    assert staff_for_user(con, "shavez") == 8, "checker also maps to his staff row"
    assert staff_for_user(con, "nobody") is None
    con.close()
    SR_LOCAL_USERS["sukhveer"] = {"pw": _pw_hash("x"), "role": "self"}
    SR_LOCAL_USERS["ranjeet"] = {"pw": _pw_hash("x"), "role": "self"}
    SR_LOCAL_USERS["sandip"] = {"pw": _pw_hash("x"), "role": "self"}
    c5 = app.test_client()
    c5.post(APP_PREFIX + "/login", data={"user": "sukhveer", "password": "x"})
    r = c5.get(APP_PREFIX + "/")                   # self never sees the grid
    assert r.status_code in (301, 302) and "/me" in r.headers.get("Location", "")
    r = c5.get(APP_PREFIX + "/me")
    assert r.status_code == 200 and _today().encode() in r.data
    assert b"No punch recorded" in r.data and b"Mark me present" in r.data
    assert b"Demo A" not in r.data, "self page must show no other staff"
    r = c5.get(APP_PREFIX + "/review")
    assert r.status_code in (301, 302) and "/me" in r.headers.get("Location", ""), \
        "self never reaches the review board — routed to the self page"
    # raise the request: server time becomes the punch time
    c5.post(APP_PREFIX + "/me/request", data={"reason": "machine did not read finger"})
    con = get_db()
    pr = con.execute("SELECT * FROM present_request WHERE staff_id=6").fetchone()
    assert pr and pr["status"] == "pending" and pr["reg_date"] == _today()
    assert pr["req_ts"][:10] == _today() and pr["reason"].startswith("machine")
    con.close()
    c5.post(APP_PREFIX + "/me/request", data={"reason": "again"})
    con = get_db()
    assert con.execute("SELECT COUNT(*) FROM present_request WHERE staff_id=6")\
        .fetchone()[0] == 1, "one request per day"
    con.close()
    r = c5.get(APP_PREFIX + "/me")
    assert b"Request sent at" in r.data
    # a punch on the machine blocks the request entirely (Ranjeet punched 10:00)
    c6 = app.test_client()
    c6.post(APP_PREFIX + "/login", data={"user": "ranjeet", "password": "x"})
    c6.post(APP_PREFIX + "/me/request", data={"reason": "try"})
    con = get_db()
    assert con.execute("SELECT COUNT(*) FROM present_request WHERE staff_id=7")\
        .fetchone()[0] == 0, "an existing machine punch must refuse the request"
    con.close()
    r = c6.get(APP_PREFIX + "/me")
    assert b"10:00" in r.data, "self page shows today's punch time"
    # board: checker sees the card and verifies (never his own)
    r = c3.get(APP_PREFIX + "/review?ym=" + _today()[:7])
    assert b"Present requests" in r.data and b"Sukhveer" in r.data and b">Verify<" in r.data
    c3.post(APP_PREFIX + "/present/verify", data={"rid": pr["id"]})
    con = get_db()
    assert con.execute("SELECT status FROM present_request WHERE id=?",
                       (pr["id"],)).fetchone()["status"] == "verified"
    con.close()
    c3.post(APP_PREFIX + "/me/request", data={"reason": "shavez fingerprint fail"})
    con = get_db()
    pr8 = con.execute("SELECT * FROM present_request WHERE staff_id=8").fetchone()
    assert pr8 and pr8["status"] == "pending", "a checker can raise his own request"
    con.close()
    try:
        verify_present(pr8["id"], "shavez")
        raise AssertionError("checker verified his own request")
    except PermissionError:
        pass
    # deciding is PRESENT_APPROVERS only; maker gets 403, manoj approves
    rA = c2.post(APP_PREFIX + "/present/decide",
                 data={"rid": pr["id"], "action": "approve"})
    assert rA.status_code == 403, "maker must not decide requests"
    c.post(APP_PREFIX + "/present/decide", data={"rid": pr["id"], "action": "approve"})
    c.post(APP_PREFIX + "/present/decide", data={"rid": pr8["id"], "action": "approve"})
    con = get_db()
    assert con.execute("SELECT status FROM present_request WHERE id=?",
                       (pr["id"],)).fetchone()["status"] == "approved"
    assert con.execute("SELECT status FROM present_request WHERE id=?",
                       (pr8["id"],)).fetchone()["status"] == "approved", \
        "manoj may approve a still-pending request directly"
    # the approved request now IS a punch: machine picture + grid pill + /me
    mT = machine_day(con, _today())
    assert 6 in mT and mT[6]["via_req"] is True and mT[6]["in"] == pr["req_ts"][11:16]
    con.close()
    r = c5.get(APP_PREFIX + "/me")
    assert b"Marked present" in r.data
    r = c.get(APP_PREFIX + "/?d=" + _today())
    assert b'class="pill req"' in r.data, "grid shows the request-backed presence pill"
    # reject path, with the note reaching the staffer
    c7 = app.test_client()
    c7.post(APP_PREFIX + "/login", data={"user": "sandip", "password": "x"})
    c7.post(APP_PREFIX + "/me/request", data={"reason": "forgot"})
    con = get_db()
    pr9 = con.execute("SELECT * FROM present_request WHERE staff_id=9").fetchone()
    con.close()
    c.post(APP_PREFIX + "/present/decide",
           data={"rid": pr9["id"], "action": "reject", "note": "was not seen at clinic"})
    r = c7.get(APP_PREFIX + "/me")
    assert b"not approved" in r.data and b"was not seen at clinic" in r.data
    # ---- D338 (S200): past-day presence correction — approver-only door ----
    d_past = "2026-08-04"                      # a weekday with no punches in the fixture
    rC = c2.post(APP_PREFIX + "/present/correct",
                 data={"d": d_past, "sid": 6, "in_time": "09:05", "reason": "x"})
    assert rC.status_code == 403, "maker must not correct a past day"
    rC = c.post(APP_PREFIX + "/present/correct",
                data={"d": d_past, "sid": 6, "in_time": "09:05",
                      "reason": "machine missed the punch"})
    assert rC.status_code in (301, 302) and "c=ok" in rC.headers.get("Location", ""), \
        "approver correction must save"
    con = get_db()
    pc = con.execute("SELECT * FROM present_request WHERE reg_date=? AND staff_id=6",
                     (d_past,)).fetchone()
    assert pc and pc["status"] == "approved" and pc["req_ts"] == d_past + " 09:05:00"
    assert pc["decide_note"] and "D338" in pc["decide_note"]
    mP = machine_day(con, d_past)
    assert mP and 6 in mP and mP[6]["via_req"] is True and mP[6]["in"] == "09:05", \
        "the correction must read as a synthetic punch"
    con.close()
    for _kw, _msg in ((dict(d=d_past, sid=6, in_time="09:10", reason="dup"),
                       "one correction per staff-day"),
                      (dict(d=_today(), sid=7, in_time="09:00", reason="x"),
                       "a machine punch must refuse the correction"),
                      (dict(d="2027-01-01", sid=6, in_time="09:00", reason="x"),
                       "a future day must refuse"),
                      (dict(d=d_past, sid=1, in_time="09:00", reason=""),
                       "an empty reason must refuse"),
                      (dict(d=d_past, sid=1, in_time="nine", reason="x"),
                       "a bad in-time must refuse")):
        try:
            correct_present("manoj", _kw["d"], _kw["sid"], _kw["in_time"], _kw["reason"])
            raise AssertionError(_msg)
        except PermissionError:
            pass
    rD = c.get(APP_PREFIX + "/?d=" + d_past)
    assert rD.status_code == 200 and b"Past-day presence correction" in rD.data \
        and b'class="pill req"' in rD.data, "approver sees the D338 card + the req pill"
    rD = c2.get(APP_PREFIX + "/?d=" + d_past)
    assert rD.status_code == 200 and b"Past-day presence correction" not in rD.data, \
        "maker must not see the D338 card"

    # feed-down: no punch file -> page says so and the request refuses loudly
    SR_PUNCH_CSV = os.path.join(tmp, "missing_punches.csv")
    r = c6.get(APP_PREFIX + "/me")
    assert b"feed is unavailable" in r.data
    try:
        request_present("ranjeet", "x")
        raise AssertionError("feed-down must refuse the request")
    except PermissionError:
        pass
    SR_PUNCH_CSV, SR_STAFF_MASTER = _old_punch, _old_sm

    # ---- v0.4: PWA assets — manifest + icons, fetchable WITHOUT a login ----
    c9 = app.test_client()                          # fresh client, no session
    r = c9.get(APP_PREFIX + "/manifest.webmanifest")
    assert r.status_code == 200, "manifest must be public (install machinery)"
    mf = json.loads(r.data)
    assert mf["start_url"] == APP_PREFIX + "/me" and mf["display"] == "standalone"
    assert len(mf["icons"]) == 2, mf
    for pth in ("/pwa-icon-192.png", "/pwa-icon-512.png"):
        ri = c9.get(APP_PREFIX + pth)
        assert ri.status_code == 200 and ri.data[:4] == b"\x89PNG", pth
    r = c5.get(APP_PREFIX + "/me")                  # self page links the manifest
    assert b'rel="manifest"' in r.data and b"theme-color" in r.data
    r = c.get(APP_PREFIX + "/?d=" + d2)             # maker/checker pages do NOT
    assert b'rel="manifest"' not in r.data

    print("SELFTEST OK — all-clear, exceptions, Arjun (D276), late+approver, "
          "leave+festival (D278), nullification, issuance add/approve/pause/close gate, "
          "doc vault + profile + degree/council + derived summary, delete = manoj-only, "
          "docs hidden from maker (D274), D272 guard, approve/reverse, holiday, leave-range (D284), "
          "pending-review board (S164), routes 200, "
          "S196: machine late minutes (weekday+roster-Sunday, de-dup, exempt, "
          "form-proof store), self page (today only, no grid, no others), "
          "present requests (server-time punch, one/day, punch-blocks, own-verify "
          "guard, approver-only decide, reject note, feed-down refusal), "
          "v0.4: PWA manifest+icons public, linked on the self page only, "
          "v0.8/D338: past-day presence correction (approver-only route+card, "
          "guards, synthetic punch, card visibility).")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    args = sys.argv[1:]
    if "--init" in args:
        init_db(); print("Initialised DB at", DB_PATH)
    elif "--map-usernames" in args:
        # S196: fill staff.username from each active staffer's first name
        # (lowercase). Prints the mapping table (names only — F-31) and flags
        # collisions LOUDLY instead of guessing. Run once after --init.
        init_db()
        con = get_db()
        rows = con.execute("SELECT staff_id,name,COALESCE(username,'') AS un "
                           "FROM staff WHERE active=1 ORDER BY name").fetchall()
        firsts = {}
        for r in rows:
            fn = (r["name"] or "").strip().lower().split()
            firsts.setdefault(fn[0] if fn else "", []).append(r["staff_id"])
        n = 0
        for r in rows:
            fn = (r["name"] or "").strip().lower().split()
            key = fn[0] if fn else ""
            if r["un"]:
                print("  kept   %-12s -> %s" % (r["un"], r["name"]))
                continue
            if not key or len(firsts[key]) > 1:
                print("  ⚠ SKIP %-12s (ambiguous/empty first name) -> set "
                      "username by hand" % (r["name"],))
                continue
            con.execute("UPDATE staff SET username=? WHERE staff_id=?",
                        (key, r["staff_id"]))
            print("  mapped %-12s -> %s" % (key, r["name"]))
            n += 1
        con.commit(); con.close()
        print("Mapped %d username(s)." % n)
    elif "--seed" in args:
        i = args.index("--seed")
        path = args[i + 1] if i + 1 < len(args) else ""
        init_db(); seed_from_csv(path)
    elif "--selftest" in args:
        _selftest()
    else:
        app.run(host="127.0.0.1", port=8044, debug=False)
