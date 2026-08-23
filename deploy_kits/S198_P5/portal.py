#!/usr/bin/env python3
"""
portal.py  —  Doctor + Manager Clinic Launcher Portal  (now the SSO broker)
===========================================================================
Dr. Manoj Agarwal Clinic, Bareilly.  Session 19 · 30 Jun 2026.
SSO broker wiring added Session 158 (portal SSO, step 1).
Session 159: Group D (Clinic-PC-only local tiles) + personal tiles, both doctor-only,
with a PC-marker so the local tiles show only on the clinic PC's own browser.

ONE self-contained Flask app at followup.dr-manoj.in/portal.

TWO MODES — the file decides at runtime, so this change is safe + reversible:
  * LEGACY (default)  : the original PIN login + device-trust. IDENTICAL to before.
  * BROKER (SSO)      : active ONLY when BOTH a CLINIC_SSO_SECRET is configured AND
                        at least one user exists in the clinic user store. Then login
                        is username + password (per-user identity + role), and a signed
                        `clinic_sso` cookie scoped to .dr-manoj.in is issued so the other
                        clinic apps (attendance / ledger / asset — later steps) trust it.
  Until you set the secret and seed a user, this file behaves EXACTLY like the old one.

--------------------------------------------------------------------------
Secrets (from portal_config.py / env, NEVER hardcoded):
  - PORTAL_PIN_HASH / PORTAL_PIN_SALT / PORTAL_TOKEN_SEED  (legacy PIN + device trust)
  - CLINIC_SSO_SECRET   : shared HMAC secret for the SSO token. MUST be identical on
                          every clinic app that later trusts the cookie. env/config only.
Clinic users + roles live in the store file (clinic_users.py; default /root/portal/clinic_users.json,
  chmod 600, gitignored). Adding lab / Manoj Bhati / Sanjeevni later = one admin command.
--------------------------------------------------------------------------

Run (VPS):
    /root/wa/venv/bin/python3 /root/portal/portal.py        # dev
    gunicorn -b 127.0.0.1:8090 portal:app                   # prod (via systemd)

Reverse proxy maps  followup.dr-manoj.in/portal  ->  127.0.0.1:8090
"""

import os
import json
import sqlite3
import datetime
import hmac
import base64
import hashlib
import secrets
import urllib.request
import urllib.parse
from functools import wraps
from flask import (
    Flask, request, redirect, make_response, render_template_string, abort, send_file
)

# --- SSO broker libraries (optional import: if absent, the portal still runs legacy PIN) ---
try:
    import clinic_sso
    import clinic_users
    _SSO_LIBS = True
except Exception:
    _SSO_LIBS = False

# ---------------------------------------------------------------------------
# CONFIG  — real values come from portal_config.py on the VPS (chmod 600),
# or environment variables. NOTHING secret is hardcoded here.
# ---------------------------------------------------------------------------
try:
    import portal_config as cfg          # VPS-only file, gitignored
    PIN_HASH    = getattr(cfg, "PORTAL_PIN_HASH", "")
    PIN_SALT    = getattr(cfg, "PORTAL_PIN_SALT", "")
    TOKEN_SEED  = getattr(cfg, "PORTAL_TOKEN_SEED", "")
    COOKIE_NAME = getattr(cfg, "PORTAL_COOKIE_NAME", "clinic_portal_device")
    SSO_SECRET  = getattr(cfg, "CLINIC_SSO_SECRET", "")
except Exception:
    PIN_HASH    = os.environ.get("PORTAL_PIN_HASH", "")
    PIN_SALT    = os.environ.get("PORTAL_PIN_SALT", "")
    TOKEN_SEED  = os.environ.get("PORTAL_TOKEN_SEED", "")
    COOKIE_NAME = os.environ.get("PORTAL_COOKIE_NAME", "clinic_portal_device")
    SSO_SECRET  = os.environ.get("CLINIC_SSO_SECRET", "")

# env can always supplement a config file that predates the SSO secret
if not SSO_SECRET:
    SSO_SECRET = os.environ.get("CLINIC_SSO_SECRET", "")

# Personal-account tile targets (Drive folder / sheet). These are capability URLs,
# so they live ONLY in portal_config.py (chmod 600, gitignored) or env — never in
# this committed file and never in the repo (ruling S159, F-31 family). Blank -> the
# tile renders as MANUAL until you fill the value in portal_config.py.
try:
    _CFG = cfg
except NameError:
    _CFG = None


def _cfg_get(name, default=""):
    v = getattr(_CFG, name, None) if _CFG is not None else None
    return v if v else os.environ.get(name, default)


CC_SAVER_URL      = _cfg_get("CC_SAVER_URL")
INBOX_JANITOR_URL = _cfg_get("INBOX_JANITOR_URL")
# S198_P1 (owner): the Janitor's OUTPUT sheet ("Payment Register", personal
# account). Capability URL -- portal_config.py or env ONLY (S159 ruling,
# F-31 family). Blank -> the tile renders MANUAL until filled.
PAYMENT_REGISTER_URL = _cfg_get("PAYMENT_REGISTER_URL")
# S198_P2 (A3): clinic forms live ONLY on the box -- never in the PUBLIC
# repo (D320). Adding a form = uploading it on /portal/forms (doctor).
FORMS_DIR = os.environ.get("PORTAL_FORMS_DIR", "/root/portal/forms")
GMB_HTML_PATH     = _cfg_get("GMB_HTML_PATH", "/root/portal/gmb.html")

STORE = clinic_users.DEFAULT_STORE if _SSO_LIBS else None

app = Flask(__name__)

# ---------------------------------------------------------------------------
# TILES  — flip "live": False -> True and fill "url" to light a tile up later.
# No rebuild needed; just edit this list and restart the service.
# ---------------------------------------------------------------------------
TILES = [
    # ============================ DOCTOR + shared ============================
    {"icon": "\U0001F4CA", "name": "Clinic Gist",
     "desc": "Live bird's-eye \u2014 calls, pipeline, pending", "live": True,
     "url": "/portal/gist", "gist": True,
     "roles": ["doctor"]},

    {"icon": "\U0001F3A7", "name": "Call Console",
     "desc": "Your view \u2014 calls \u00b7 staff \u00b7 leads \u00b7 coaching", "live": True,
     "url": "/portal/console",
     "roles": ["doctor"]},

    {"icon": "\U0001F4DE", "name": "Call Tracker",
     "desc": "Staff's working tracker (the Sheet app)", "live": True,
     "url": "https://script.google.com/macros/s/AKfycbyoQ5R3yvFC0B8arOnVWo4002BFfBGIVM2cBwpaMwUM4GaYw7d89jk1U_g38Ht0omcF/exec",
     "roles": ["doctor"]},

    {"icon": "\u2B50", "name": "GMB Review Assist",
     "desc": "Google review composer \u00b7 any device", "live": True,
     "url": "/portal/gmb", "roles": ["doctor"]},


    {"icon": "\U0001F4AC", "name": "Send WhatsApp",
     "desc": "Approved templates \u00b7 clinic number \u00b7 any patient", "live": True,
     "url": "/portal/wa",
     "roles": ["doctor"]},

    {"icon": "\U0001F4E3", "name": "Follow-up WhatsApps",
     "desc": "Today's due list \u00b7 batch send by section", "live": True,
     "url": "/portal/wa/followups",
     "roles": ["doctor"]},

    {"icon": "\U0001F4F1", "name": "WhatsApp Approvals",
     "desc": "Vendor panel \u2014 active again", "live": True,
     "url": "https://followup.dr-manoj.in/wa-approve",
     "roles": ["doctor"]},

    {"icon": "\U0001F4CB", "name": "Surgical Case Pack",
     "desc": "Estimate \u00b7 OT list \u00b7 consent \u00b7 Ayushman", "live": True,
     "url": "/portal/casepack",
     "roles": ["doctor"]},

    # S198_P2 (A3, owner rulings): everyone logged in prints/downloads;
    # only a doctor adds/removes (upload on the page itself).
    {"icon": "\U0001F5A8\uFE0F", "name": "Forms & Downloads",
     "desc": "Clinic forms \u2014 print & download", "live": True,
     "url": "/portal/forms", "roles": ["doctor", "manager", "staff"]},


    {"icon": "\U0001F465", "name": "Attendance",
     "desc": "Biometric punches \u2192 monthly report", "live": True,
     "url": "https://attendance.dr-manoj.in",
     "roles": ["doctor", "manager", "staff"]},

    {"icon": "\U0001F4C5", "name": "Staff Register",
     "desc": "Daily register \u2014 reads Attendance", "live": True,
     "url": "https://attendance.dr-manoj.in/register/review",
     "review_counts": True,
     "roles": ["doctor", "manager", "staff"]},

    {"icon": "\U0001F4B0", "name": "Salary \u2014 approve & lock",
     "desc": "From Attendance + Ledger deductions", "live": True,
     "url": "https://attendance.dr-manoj.in/register/salary",
     "roles": ["doctor"]},

    {"icon": "\U0001F5C2\uFE0F", "name": "Staff Ledger",
     "desc": "Advances & loans \u2014 recovered at salary close", "live": True,
     "url": "https://attendance.dr-manoj.in/ledger",
     "roles": ["doctor"]},

    {"icon": "\U0001F5C2\uFE0F", "name": "Staff Ledger \u2014 Entry",
     "desc": "Enter staff money events", "live": True,
     "url": "https://attendance.dr-manoj.in/ledger",
     "roles": ["manager"]},

    {"icon": "\U0001F4E6", "name": "Asset Register",
     "desc": "Clinic assets & AMC", "live": True,
     "url": "https://assets.dr-manoj.in",
     "roles": ["doctor", "manager"]},

    {"icon": "\U0001F4F7", "name": "Scan Purchase",
     "desc": "Photograph a new bill \u2192 get a stamp number", "live": True,
     "url": "https://assets.dr-manoj.in/intake",
     "roles": ["staff", "manager"]},

    {"icon": "\U0001F511", "name": "Manage Users",
     "desc": "Logins: add, role, password, active, remove", "live": True,
     "url": "https://followup.dr-manoj.in/portal/users",
     "roles": []},   # manoj-only: shown via USER_TILE_EXTRA + guarded by the route


    {"icon": "\U0001F4B3", "name": "UPI Sheet",
     # S198_P1 (owner ruling): demoted -- medical+clinic UPI recon lives in
     # the finance app since S195; this Sheet covers LAB + legacy and hosts
     # the GAS push. The tile retires when the lab module lands on the VPS.
     "desc": "Lab + legacy recon \u2014 retires when lab moves", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc",
     "roles": ["doctor"]},

    {"icon": "\U0001F697", "name": "Vehicle Tracking",
     "desc": "Track360 Sheet \u2014 VPS module planned", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc/edit?gid=762286425#gid=762286425",
     "roles": ["doctor"]},

    {"icon": "\U0001F4C8", "name": "Monthly Accounting",
     "desc": "Sheet + Form \u2014 fine for now, migrates later", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/13eJo58J7G8n846mGlyv-pHpDILQnCrK-8ZZekyi1Hrg",
     "roles": ["doctor"]},



    # --- Sanjeevni finance (S179) ------------------------------------------
    {"icon": "\U0001F3EA", "name": "Daily Sale",
     # S187_P2a: the maker's tile carries his own to-do line (days to file,
     # today's status) via the same fail-soft client fetch pattern as the
     # Sanjeevni and Staff Register tiles. The endpoint answers only a seated
     # medical maker/checker; anyone else keeps the static text.
     "desc": "Enter today's shop sale", "live": True,
     "url": "/finance/entry",
     "daily_sale_counts": True,
     "roles": ["staff"]},
    {"icon": "\U0001F4B5", "name": "Sanjeevni Medicos",
     # S187_P1a: the tile now lands on the APPROVALS hub (one click, every
     # section linked from there) instead of the review dead-end, and carries
     # a live pending summary exactly like the Staff Register tile does. The
     # counts are fetched client-side (data-sanjeevni-counts below) so the
     # portal never waits on the finance app; if finance is down or the user
     # is not the medical checker, the static text stands and nothing breaks.
     "desc": "Approve days · Marg reports · month close", "live": True,
     "url": "/finance/approvals",
     "sanjeevni_counts": True,
     "roles": ["doctor"]},

    # --- Clinic finance (S182) ---------------------------------------------
    # roles:[] on BOTH tiles - they appear only via USER_TILE_EXTRA below, because
    # the clinic rosters are named people (unit_role), not a portal role. The
    # /finance/clinic/* routes guard themselves; a tile is convenience, never
    # authorisation (F-84). Wording here is the STATIC FALLBACK - the live label
    # comes from clinic.tile.* via /finance/clinic/api/tile-meta (see the script
    # at the foot of PORTAL_HTML), and the tile keeps this text if that is down.
    {"icon": "\U0001F3E5", "name": "Daily Collection",
     "desc": "\u0906\u091C \u0915\u0940 OPD / X-Ray / Procedure entry", "live": True,
     "url": "/finance/clinic/entry", "clinic_meta": True,
     "roles": []},
    {"icon": "\U0001F9FE", "name": "Clinic",
     "desc": "Review and approve the clinic day", "live": True,
     "url": "/finance/clinic/review", "clinic_meta": True,
     "roles": []},
    # --- HELD / MANUAL (doctor only) --------------------------------------
    # S198_P1 (owner rulings, 23-Aug): Ayushman Finder + Surgical Estimate
    # live INSIDE the Case Pack; "WABA Send" is the Send WhatsApp tile;
    # Nutrition/Physio is clinic_writer on the clinic PC (folded into the
    # Vitals & Plan tile). Revenue Reconciler stays -- first in the
    # local-PC -> VPS migration queue.
    {"icon": "\U0001F9FE", "name": "Revenue Reconciler",
     "desc": "Local PC \u2014 migrate first", "live": False, "url": "", "roles": ["doctor"]},

    # ===================== CLINIC PC ONLY  (Group D) ========================
    # These open localhost apps that resolve ONLY on the clinic PC itself, so
    # they are shown ONLY on a browser marked as the clinic PC (see /portal/mark-pc).
    # No probing -> immune to Chrome's localhost restrictions. Plain links.
    {"icon": "\U0001F9E0", "name": "Follow-up Tracker",
     "desc": "Docterz \u2192 call list \u00b7 Clinic PC", "live": True,
     "url": "http://localhost:5000", "roles": ["doctor"], "pc_only": True},

    {"icon": "\U0001FA7A", "name": "Vitals & Plan",
     "desc": "clinic_writer \u2014 Vitals \u00b7 Nutrition \u00b7 Physio", "live": True,
     "url": "http://localhost:5057", "roles": ["doctor"], "pc_only": True},

    {"icon": "\U0001F4CB", "name": "Case Pack \u00b7 PC fallback",
     "desc": "Keeps saved cases \u2014 until they reach the VPS", "live": True,
     "url": "http://localhost:5058", "roles": ["doctor"], "pc_only": True},

    {"icon": "\U0001F9FE", "name": "CC Statements \u2192 Tally",
     "desc": "Statement conversion \u00b7 Clinic PC", "live": True,
     "url": "http://localhost:5059", "roles": ["doctor"], "pc_only": True},

    # ===================== PERSONAL  (doctor only) =========================
    # Targets come from portal_config.py (git-ignored). Blank -> shows MANUAL.
    {"icon": "\U0001F4C7", "name": "CC Statement Saver",
     "desc": "Card statements \u2192 Drive", "live": bool(CC_SAVER_URL),
     "url": CC_SAVER_URL, "roles": ["doctor"]},

    {"icon": "\U0001F9F9", "name": "Inbox Janitor",
     "desc": "Payment register \u2014 view \u00b7 print \u00b7 export", "live": bool(INBOX_JANITOR_URL),
     "url": INBOX_JANITOR_URL, "roles": ["doctor"]},

    # S198_P5 (owner, 23-Aug): the Payment Register tile REMOVED — the Inbox
    # Janitor tile already opens the same sheet (INBOX_JANITOR_URL points at
    # it on the box), so two tiles were one door twice. PAYMENT_REGISTER_URL
    # stays readable in config for any later surface; nothing renders it now.

    # S198_P3 (owner priority): the Renewals Master v2 sheet -- the watch-list
    # the Inbox Janitor's digest nags from. Plain spreadsheet URL, inline per
    # the UPI-Sheet/Monthly-Accounting precedent (the sheet id already lives in
    # the public repo's janitor source; access stays gated by Google login).
    {"icon": "\U0001F5D3\uFE0F", "name": "Renewals",
     "desc": "Master sheet \u2014 every renewal & due date", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E",
     "roles": ["doctor"]},

    # ================== PERSONAL HEALTH CLUSTER (doctor only) ===============
    # Own subdomains, each with its OWN login (owner-key). Link-tiles: clicking
    # opens the app's own sign-in. Public hostnames -> no secret, inline URLs.
    {"icon": "\U0001F48A", "name": "RxGuard",
     "desc": "Prescription safety \u00b7 own login", "live": True,
     "url": "https://rx.dr-manoj.in", "roles": ["doctor"]},

    {"icon": "\U0001F34E", "name": "GutLog",
     "desc": "Gut & diet log \u00b7 own login", "live": True,
     "url": "https://health.dr-manoj.in", "roles": ["doctor"]},

    {"icon": "\U0001F4AA", "name": "FitLog",
     "desc": "Fitness log \u00b7 own login", "live": True,
     "url": "https://fit.dr-manoj.in", "roles": ["doctor"]},
]

# ---------------------------------------------------------------------------
# TILE GROUPING  — sectioned, mobile-friendly layout. Sections with no tile
# visible to the current role/PC are dropped entirely (see _visible_sections).
# ---------------------------------------------------------------------------
GROUP_ORDER = ["Clinic", "Staff", "Money & Accounts", "Personal & Health",
               "Clinic PC tools", "Admin"]

_TILE_GROUP = {
    "Clinic Gist": "Clinic",
    "Call Console": "Clinic", "Call Tracker": "Clinic",
    "Surgical Case Pack": "Clinic", "Send WhatsApp": "Clinic",
    "Follow-up WhatsApps": "Clinic", "WhatsApp Approvals": "Clinic",
    "GMB Review Assist": "Clinic", "Forms & Downloads": "Clinic",
    "Asset Register": "Clinic", "Scan Purchase": "Clinic",
    # S198_P1: the staff money/attendance apps are ONE connected family
    # (attendance -> salary; ledger advances recovered at the salary close).
    "Attendance": "Staff", "Staff Register": "Staff",
    "Salary \u2014 approve & lock": "Staff", "Staff Ledger": "Staff",
    "Staff Ledger \u2014 Entry": "Staff",
    "UPI Sheet": "Money & Accounts", "Monthly Accounting": "Money & Accounts",
    "Daily Sale": "Money & Accounts", "Sanjeevni Medicos": "Money & Accounts",
    "Daily Collection": "Money & Accounts", "Clinic": "Money & Accounts",
    "Vehicle Tracking": "Money & Accounts",
    "CC Statement Saver": "Personal & Health", "Inbox Janitor": "Personal & Health",
    "Renewals": "Personal & Health",
    "RxGuard": "Personal & Health", "GutLog": "Personal & Health",
    "FitLog": "Personal & Health",
    # the local-PC -> VPS migration queue (owner, 23-Aug); rendered as a
    # compact chip row by the template. pc_only gating unchanged.
    "Follow-up Tracker": "Clinic PC tools", "Vitals & Plan": "Clinic PC tools",
    "Case Pack \u00b7 PC fallback": "Clinic PC tools",
    "CC Statements \u2192 Tally": "Clinic PC tools",
    "Revenue Reconciler": "Clinic PC tools",
    "Manage Users": "Admin",
}
# Every tile must map to a known group (fail loud at import, not silently mis-place).
for _t in TILES:
    assert _t["name"] in _TILE_GROUP, "ungrouped tile: " + _t["name"]
    _t["group"] = _TILE_GROUP[_t["name"]]
assert set(_TILE_GROUP.values()) <= set(GROUP_ORDER), "group not in GROUP_ORDER"

# --- per-user tile overrides (D285) ----------------------------------------
# MASK hides named tiles from a specific user even if their role would show them.
# EXTRA grants named tiles to a specific user even if their role would not.
# Names must match TILES["name"] byte-for-byte.
USER_TILE_MASK = {
    "bhawna": {"GMB Review Assist", "Vitals & Plan", "Surgical Case Pack", "Send WhatsApp", "Follow-up WhatsApps",
               "Case Pack \u00b7 PC fallback",
               "CC Statements \u2192 Tally", "Follow-up Tracker"},
}
USER_TILE_EXTRA = {
    "shavez": {"Asset Register"},
    "manoj": {"Manage Users"},
}


# S179: medical's checker is Dr Manoj alone, so Dr Bhawna should not see a
# tile that would only refuse her.
USER_TILE_MASK.setdefault("bhawna", set()).add("Sanjeevni Medicos")


# S179: darpan is role=staff, which is shared. He only needs Daily Sale.
USER_TILE_MASK.setdefault("darpan", set()).update({"Attendance", "Staff Register", "Scan Purchase"})


# S182: the clinic module's REAL rosters, as seeded by migrations S182_clinic
# (C1e) and S182_c2 (C2a) into unit_role. Shavez holds a clinic MAKER seat and
# the middle-approver CHECKER seat, so he gets both tiles; self-verify stays
# barred in code (D272). Kept as explicit grants, not roles, because "shavez"
# is simultaneously portal-manager, medical maker, clinic maker and clinic
# checker - a role-based tile would leak to every other staff login.
for _u in ("shavez", "alisha", "shivani"):
    USER_TILE_EXTRA.setdefault(_u, set()).add("Daily Collection")
for _u in ("manoj", "bhawna", "shavez"):
    USER_TILE_EXTRA.setdefault(_u, set()).add("Clinic")


def _visible_sections(role, pc, user=""):
    """Ordered [(label, [tiles])] for this role/pc/user; empty sections dropped.
    A tile shows when the role matches OR the user is granted it (EXTRA), the user
    is not masked from it (MASK), and PC-gating passes."""
    mask = USER_TILE_MASK.get(user, set())
    extra = USER_TILE_EXTRA.get(user, set())
    out = []
    for _g in GROUP_ORDER:
        _items = [t for t in TILES
                  if t.get("group") == _g
                  and (role in t["roles"] or t["name"] in extra)
                  and t["name"] not in mask
                  and (not t.get("pc_only") or pc)]
        if _items:
            out.append((_g, _items))
    return out

# ---------------------------------------------------------------------------
# AUTH HELPERS
# ---------------------------------------------------------------------------
def _hash_pin(pin: str) -> str:
    """Salted SHA-256 of the PIN. The PIN itself is never stored or logged."""
    return hashlib.sha256((PIN_SALT + pin).encode("utf-8")).hexdigest()


def _expected_device_token() -> str:
    """
    The value a trusted device's cookie must contain.
    Derived from the server seed; rotating the seed invalidates ALL devices
    at once (that is exactly what "forget all devices" does).
    """
    return hmac.new(TOKEN_SEED.encode("utf-8"),
                    b"trusted-device", hashlib.sha256).hexdigest()


def _is_trusted(req) -> bool:
    tok = req.cookies.get(COOKIE_NAME, "")
    if not tok or not TOKEN_SEED:
        return False
    return hmac.compare_digest(tok, _expected_device_token())


# --- clinic-PC marker (gates the Group D local-tool tiles) -----------------
PC_COOKIE = "clinic_portal_pc"


def _pc_token() -> str:
    """Marker a browser must carry to be treated as THE clinic PC.
    Derived from the same server seed as device-trust, so rotating the seed
    (or 'forget all devices') also clears the clinic-PC marking."""
    return hmac.new(TOKEN_SEED.encode("utf-8"),
                    b"clinic-pc-device", hashlib.sha256).hexdigest()


def _is_clinic_pc(req) -> bool:
    tok = req.cookies.get(PC_COOKIE, "")
    if not tok or not TOKEN_SEED:
        return False
    return hmac.compare_digest(tok, _pc_token())


# --- SSO broker helpers ----------------------------------------------------
def _sso_ready() -> bool:
    """BROKER mode is active only when the secret is set AND a user exists."""
    if not _SSO_LIBS or not SSO_SECRET:
        return False
    try:
        return len(clinic_users.list_users(STORE)) > 0
    except Exception:
        return False


def _sso_user(req):
    """Return {user, role, ...} if a valid SSO cookie is present, else None."""
    if not _sso_ready():
        return None
    tok = req.cookies.get(clinic_sso.COOKIE_NAME, "")
    if not tok:
        return None
    try:
        return clinic_sso.verify_token(tok, SSO_SECRET,
                                       current_epoch=clinic_users.get_epoch(STORE))
    except Exception:
        return None


def _authed(req) -> bool:
    """Logged in via a valid SSO cookie OR a trusted device (transition-safe)."""
    return (_sso_user(req) is not None) or _is_trusted(req)


def login_required(view):
    @wraps(view)
    def wrapper(*a, **k):
        if _authed(request):
            return view(*a, **k)
        return redirect("/portal/login")
    return wrapper


def _config_ok() -> bool:
    """Legacy PIN config present. (Broker mode does not need this.)"""
    return bool(PIN_HASH and PIN_SALT and TOKEN_SEED)


def _usable() -> bool:
    """The portal can serve if EITHER the PIN is configured OR broker mode is ready."""
    return _config_ok() or _sso_ready()


# --- user-admin gate (manoj-only: the portal's who-can-touch-everyone screen) ------
USER_ADMINS = set(x.strip().lower() for x in
                  _cfg_get("PORTAL_USER_ADMINS", "manoj").split(",") if x.strip())


def _is_user_admin(req) -> bool:
    w = _sso_user(req)
    return bool(w and (w.get("user") or "").lower() in USER_ADMINS)


def user_admin_required(view):
    @wraps(view)
    def wrapper(*a, **k):
        if not _authed(request):
            return redirect("/portal/login")
        if not _is_user_admin(request):
            abort(403)
        return view(*a, **k)
    return wrapper


def _active_doctors(rows):
    return [r for r in rows if r.get("role") == "doctor" and r.get("active")]


def _admin_guard(action, target, me):
    """'' if the (de)activate/delete action is allowed, else an error string. Blocks
    self-lockout and removing the last active doctor -- admin access can't be bricked."""
    target = (target or "").strip().lower()
    if not target:
        return "no user specified"
    if action in ("deactivate", "delete") and target == (me or "").strip().lower():
        return "you cannot %s your own account" % action
    if action in ("deactivate", "delete"):
        rows = clinic_users.list_users(STORE)
        row = next((r for r in rows if r["user"] == target), None)
        if row and row.get("role") == "doctor" and row.get("active"):
            if len(_active_doctors(rows)) <= 1:
                return "cannot %s the last active doctor" % action
    return ""

# ---------------------------------------------------------------------------
# PAGE TEMPLATES (inline; mobile-first; no external assets)
# ---------------------------------------------------------------------------
PAGE_HEAD = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Clinic Portal</title>
<link rel="manifest" href="/portal/manifest.webmanifest">
<meta name="theme-color" content="#0f2233">
<link rel="apple-touch-icon" href="/portal/pwa-icon-192.png">
<style>
:root{--bg:#0f2233;--card:#16324a;--ink:#eaf2fa;--muted:#9fb6cc;
 --blue:#3b82f6;--green:#22c55e;--line:#274b66;--held:#5b7184;
 --shadow:0 2px 10px rgba(0,0,0,.25)}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
 background:var(--bg);color:var(--ink);line-height:1.4;min-height:100vh}
.wrap{max-width:920px;margin:0 auto;padding:18px 16px 40px}
.head{display:flex;align-items:baseline;justify-content:space-between;
 flex-wrap:wrap;gap:8px;margin:8px 0 18px}
.head h1{font-size:18px;margin:0;color:#fff;letter-spacing:-.01em}
.head .sub{font-size:12px;color:var(--muted)}
.sec{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
 color:var(--muted);margin:24px 2px 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.sec:first-of-type{margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:14px;
 padding:16px 14px;box-shadow:var(--shadow);text-decoration:none;color:var(--ink);
 display:flex;flex-direction:column;gap:6px;min-height:104px;transition:transform .05s,border-color .1s}
.tile:active{transform:scale(.98)}
.tile.live{border-color:var(--blue)}
.tile.live:hover{border-color:#60a5fa}
.tile.held{opacity:.62;cursor:default}
.tile .ic{font-size:26px;line-height:1}
.tile .nm{font-size:15px;font-weight:600}
.tile .ds{font-size:11.5px;color:var(--muted)}
.tag{align-self:flex-start;font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px;margin-top:auto}
.tag.l{background:rgba(34,197,94,.15);color:#86efac}
.tag.h{background:rgba(91,113,132,.25);color:#b8c7d6}
.foot{margin-top:26px;display:flex;justify-content:center;gap:10px;flex-wrap:wrap}
.pcmark{margin-top:16px;text-align:center;font-size:12px;color:var(--muted)}
.pcmark a{color:var(--blue);text-decoration:none}
.pcmark a:hover{text-decoration:underline}
.forget{background:none;border:1px solid var(--line);color:var(--muted);
 font-size:12px;padding:9px 16px;border-radius:10px;cursor:pointer}
.forget:hover{border-color:#7f1d1d;color:#fca5a5}
/* login */
.login{max-width:340px;margin:9vh auto 0;text-align:center;padding:0 16px}
.login h1{font-size:20px;color:#fff;margin:0 0 4px}
.login p{font-size:13px;color:var(--muted);margin:0 0 22px}
.login input{width:100%;font-size:20px;text-align:center;letter-spacing:.06em;
 padding:14px;border:2px solid var(--blue);border-radius:12px;background:#0b1b29;
 color:#fff;outline:none;margin-bottom:10px}
.login input.pin{font-size:22px;letter-spacing:.3em}
.login input:focus{border-color:#60a5fa}
.login button{width:100%;margin-top:6px;font-size:16px;font-weight:600;padding:13px;
 border:none;border-radius:12px;background:var(--blue);color:#fff;cursor:pointer}
.login button:active{transform:scale(.99)}
.pwwrap{position:relative;margin-bottom:10px}
.pwwrap #pw{margin-bottom:0;padding-right:66px}
.login .eye{position:absolute;right:6px;top:0;height:100%;display:flex;align-items:center;background:none;border:none;color:var(--muted);font-size:12px;cursor:pointer;padding:0 10px;width:auto;margin:0}
.err{color:#fca5a5;font-size:13px;margin-top:12px;min-height:18px}
.note{color:var(--muted);font-size:11px;margin-top:22px}
@media(max-width:480px){
 .wrap{padding:14px 12px 36px}
 .grid{grid-template-columns:repeat(2,1fr);gap:10px}
 .tile{padding:14px 12px;min-height:96px}
 .tile .nm{font-size:14px}
 .tile .ic{font-size:24px}
 .head h1{font-size:17px}
}
</style></head><body>
"""

LOGIN_HTML = PAGE_HEAD + """
<div class="login">
  <h1>Clinic Portal</h1>
  <p>Private access — enter PIN</p>
  <form method="POST" action="/portal/login" autocomplete="off">
    <input class="pin" name="pin" type="password" inputmode="numeric" autofocus
           placeholder="• • • •" aria-label="PIN">
    <button type="submit">Unlock</button>
  </form>
  <div class="err">{{ error or "" }}</div>
  <div class="note">This device will be remembered until you sign out
   or use “Forget all devices”.</div>
</div></body></html>
"""

USERPASS_HTML = PAGE_HEAD + """
<div class="login">
  <h1>Clinic Portal</h1>
  <p>Sign in — one login for all your clinic apps</p>
  <form method="POST" action="/portal/login" autocomplete="off">
    <input name="user" type="text" autocapitalize="none" autocorrect="off" autofocus
           placeholder="username" aria-label="Username">
    <div class="pwwrap">
      <input id="pw" name="password" type="password" placeholder="password" aria-label="Password">
      <button type="button" class="eye" aria-label="Show or hide password"
              onclick="var p=document.getElementById('pw');var h=p.type==='password';p.type=h?'text':'password';this.textContent=h?'hide':'show';">show</button>
    </div>
    <button type="submit">Sign in</button>
  </form>
  <div class="err">{{ error or "" }}</div>
  <div class="note">Signing in here signs you in to Attendance, Ledger and Asset too.
   Each app also keeps its own login as a fallback.</div>
</div></body></html>
"""

# ---------------------------------------------------------------------------
# S198_P1 — the HOME page's own head. The owner's ruling (23-Aug): the portal
# KEEPS the dark scheme he finds friendly on the eyes; the warm-paper design
# language stays on the finance pages. Same tokens as PAGE_HEAD, new compact
# layout. Deliberately NOT a change to PAGE_HEAD: login, console, gist,
# digest, staff-report and users pages are byte-untouched.
# ---------------------------------------------------------------------------
HOME_HEAD = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Clinic Portal</title>
<link rel="manifest" href="/portal/manifest.webmanifest">
<meta name="theme-color" content="#0f2233">
<link rel="apple-touch-icon" href="/portal/pwa-icon-192.png">
<style>
:root{--bg:#0f2233;--card:#16324a;--card2:#122a3f;--ink:#eaf2fa;--muted:#9fb6cc;
 --blue:#3b82f6;--green:#22c55e;--line:#274b66;--held:#5b7184;
 --good-bg:rgba(34,197,94,.16);--good-ink:#86efac;
 --warn-bg:rgba(251,191,36,.16);--warn-ink:#fcd34d;
 --shadow:0 2px 10px rgba(0,0,0,.25)}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
 background:var(--bg);color:var(--ink);line-height:1.5;min-height:100vh;
 font-variant-numeric:tabular-nums}
.topbar{position:sticky;top:0;z-index:5;background:#0c1c2b;
 border-bottom:1px solid var(--line);box-shadow:var(--shadow)}
.topin{max-width:1480px;margin:0 auto;display:flex;align-items:center;gap:12px;padding:8px 20px}
.topin img{width:40px;height:40px}
.tname{font-size:16px;font-weight:700;color:#fff;letter-spacing:-.01em}
.tsub{font-size:11.5px;color:var(--muted)}
.tright{margin-left:auto;font-size:12.5px;color:var(--muted)}
.wrap{max-width:1480px;margin:0 auto;padding:12px 20px 40px}
.strip{display:grid;grid-template-columns:minmax(320px,1.4fr) repeat(3,minmax(140px,1fr));gap:10px;margin:12px 0 4px}
.hero{background:var(--card);border:1px solid var(--line);border-radius:12px;
 padding:12px 16px;box-shadow:var(--shadow);display:flex;align-items:center;gap:14px;
 text-decoration:none;color:var(--ink);transition:border-color .1s}
.hero:hover{border-color:var(--blue)}
.hstat{font-size:26px;line-height:1}
.hero .hl{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.hero .hv{font-size:14.5px;font-weight:600;color:#fff}
.hero .badge{margin-left:auto;font-size:12px;font-weight:600;padding:3px 10px;border-radius:20px;white-space:nowrap}
.b-warn{background:var(--warn-bg);color:var(--warn-ink)}
.b-good{background:var(--good-bg);color:var(--good-ink)}
.chipbox{background:var(--card);border:1px solid var(--line);border-radius:12px;
 padding:9px 14px;box-shadow:var(--shadow);text-decoration:none;color:var(--ink);
 display:block;transition:border-color .1s}
.chipbox:hover{border-color:var(--blue)}
.chipbox .cv{font-size:21px;font-weight:700;color:#fff}
.chipbox .cl{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.kick{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
 color:var(--muted);margin:16px 0 8px;display:flex;align-items:center;gap:10px}
.kick::after{content:"";flex:1;height:1px;background:var(--line)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(205px,1fr));gap:8px}
.tile{display:flex;align-items:center;gap:10px;background:var(--card);
 border:1px solid var(--line);border-radius:10px;padding:9px 12px;min-height:54px;
 box-shadow:var(--shadow);text-decoration:none;color:var(--ink);
 transition:border-color .1s,transform .05s}
.tile:hover{border-color:var(--blue)}
.tile:active{transform:scale(.99)}
.tile.held{opacity:.62;cursor:default}
.tile .ic{font-size:20px;flex:0 0 auto;line-height:1}
.tile .tx{min-width:0}
.tile .nm{font-size:13.5px;font-weight:600;line-height:1.25;color:#fff}
.tile .ds{font-size:11px;color:var(--muted);line-height:1.3}
.tag{margin-left:auto;font-size:10px;font-weight:700;padding:2px 7px;border-radius:999px;white-space:nowrap}
.tag.h{background:rgba(91,113,132,.25);color:#b8c7d6}
.mini{display:flex;flex-wrap:wrap;gap:8px}
.mchip{font-size:12px;color:var(--muted);background:var(--card2);
 border:1px solid var(--line);border-radius:16px;padding:6px 12px;text-decoration:none;display:inline-block}
a.mchip:hover{border-color:var(--blue);color:var(--ink)}
.mchip.held{opacity:.55}
.foot{margin-top:26px;display:flex;justify-content:center;gap:10px;flex-wrap:wrap}
.pcmark{margin-top:16px;text-align:center;font-size:12px;color:var(--muted)}
.pcmark a{color:var(--blue);text-decoration:none}
.pcmark a:hover{text-decoration:underline}
.forget{background:none;border:1px solid var(--line);color:var(--muted);
 font-size:12px;padding:9px 16px;border-radius:10px;cursor:pointer}
.forget:hover{border-color:#7f1d1d;color:#fca5a5}
#toTop{position:fixed;right:18px;bottom:18px;width:46px;height:46px;border-radius:50%;
 border:1px solid var(--line);background:var(--card);color:var(--ink);font-size:20px;
 cursor:pointer;display:none;z-index:9;box-shadow:var(--shadow)}
#toTop:hover{border-color:var(--blue)}
@media(max-width:900px){.strip{grid-template-columns:1fr 1fr}.hero{grid-column:1/-1}}
@media(max-width:480px){.wrap{padding:10px 12px 36px}
 .grid{grid-template-columns:repeat(2,1fr)}
 .tile{flex-direction:column;align-items:flex-start;gap:6px;min-height:88px}
 .tag{margin-left:0}}
</style></head><body>
"""

PORTAL_HTML = HOME_HEAD + """
<div class="topbar"><div class="topin">
  <img alt="clinic logo" src="data:image/png;base64,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">
  <div><div class="tname">Dr. Manoj Agarwal Clinic</div>
  <div class="tsub">Advanced Orthopaedic Surgery Centre \u00b7 Portal</div></div>
  {% if who %}<div class="tright">{{ who.user }} ({{ who.role }})</div>{% endif %}
</div></div>
<div class="wrap">
  {% if role == 'doctor' %}
  <div class="strip">
    <a class="hero" href="/finance/health" target="_blank" rel="noopener" id="healthHero">
      <span class="hstat">\U0001FA7A</span>
      <div><div class="hl">Portal health</div>
      <div class="hv" id="heroLine">Open the health page \u2192</div></div>
      <span class="badge b-good" id="heroBadge" hidden></span>
    </a>
    <a class="chipbox" href="/finance/approvals" target="_blank" rel="noopener">
      <div class="cv" id="chipSanj">\u2013</div><div class="cl">Sanjeevni to approve</div></a>
    <a class="chipbox" href="https://attendance.dr-manoj.in/register/review" target="_blank" rel="noopener">
      <div class="cv" id="chipReg">\u2013</div><div class="cl">Register to enter</div></a>
    <a class="chipbox" href="/finance/review" target="_blank" rel="noopener">
      <div class="cv" id="chipRev">\u2013</div><div class="cl">Review queue</div></a>
  </div>
  {% endif %}
  {% for label, items in sections %}
  <div class="kick">{{ label }}</div>
  {% if label == 'Clinic PC tools' %}
  <div class="mini">
  {% for t in items %}
    {% if t.live %}<a class="mchip" href="{{ t.url }}" target="_blank" rel="noopener">{{ t.icon }} {{ t.name }} \u00b7 {{ t.desc }}</a>
    {% else %}<span class="mchip held" title="Not yet hosted">{{ t.icon }} {{ t.name }} \u00b7 {{ t.desc }}</span>{% endif %}
  {% endfor %}
  </div>
  {% else %}
  <div class="grid">
  {% for t in items %}
    {% if t.live %}
      <a class="tile" href="{{ t.url }}" target="_blank" rel="noopener"{% if t.clinic_meta %} data-clinic-tile{% endif %}>
        <div class="ic">{{ t.icon }}</div>
        <div class="tx"><div class="nm">{{ t.name }}</div>
        <div class="ds"{% if t.review_counts %} data-review-counts{% endif %}{% if t.gist %} data-gist-summary{% endif %}{% if t.sanjeevni_counts %} data-sanjeevni-counts{% endif %}{% if t.daily_sale_counts %} data-daily-sale-counts{% endif %}>{{ t.desc }}</div></div>
      </a>
    {% else %}
      <div class="tile held" title="Not yet hosted">
        <div class="ic">{{ t.icon }}</div>
        <div class="tx"><div class="nm">{{ t.name }}</div>
        <div class="ds">{{ t.desc }}</div></div>
        <span class="tag h">MANUAL</span>
      </div>
    {% endif %}
  {% endfor %}
  </div>
  {% endif %}
  {% endfor %}
  <div class="foot">
    <form method="POST" action="/portal/forget"
          onsubmit="return confirm('Sign out EVERY device? Everyone will need to log in again.');">
      <button class="forget" type="submit">Forget all devices</button>
    </form>
    {% if sso %}
    <form method="POST" action="/portal/signout-all"
          onsubmit="return confirm('Sign out of ALL clinic apps everywhere? You and anyone signed in will have to log in again.');">
      <button class="forget" type="submit">Sign out everywhere (all apps)</button>
    </form>
    {% endif %}
  </div>
  {% if role == 'doctor' %}
  <div class="pcmark">
    {% if pc %}
      <span>\U0001F5A5\uFE0F Clinic-PC tools are shown on this device.</span>
      <a href="/portal/unmark-pc">Not the clinic PC?</a>
    {% else %}
      <a href="/portal/mark-pc">\U0001F5A5\uFE0F Is this the clinic PC? Show PC-only tools</a>
    {% endif %}
  </div>
  {% endif %}
<button id="toTop" aria-label="Back to top" title="Back to top">\u2191</button>
<script>
/* S198_P1: the 46px floating back-to-top (the Console \u00a74.8 pattern
   promoted to the home page; appears after 500px of scroll). */
(function(){
  var b=document.getElementById('toTop');
  if(!b)return;
  window.addEventListener('scroll',function(){
    b.style.display=(window.scrollY>500)?'block':'none';
  },{passive:true});
  b.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
})();
/* S198_P1: the Portal Health hero + strip chips (doctor only -- the block is
   not rendered for other roles). ONE fetch of the same checker-only
   tile-summary the Sanjeevni tile uses; fail-soft: a non-checker doctor
   (Dr Bhawna) or finance down leaves the static text and hides nothing. */
(function(){
  var hero=document.getElementById('healthHero');
  if(!hero)return;
  fetch('/finance/api/tile-summary',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok)return;
     var line=document.getElementById('heroLine'),badge=document.getElementById('heroBadge');
     if(d.health_line){line.textContent=d.health_line;badge.textContent='\u26A0 attention';badge.className='badge b-warn';}
     else{line.textContent='All clear';badge.textContent='\u2714 OK';badge.className='badge b-good';}
     badge.hidden=false;
     var c=document.getElementById('chipSanj');
     if(c&&typeof d.to_approve!=='undefined')c.textContent=d.to_approve;
     c=document.getElementById('chipRev');
     if(c&&typeof d.review!=='undefined')c.textContent=d.review;
   })
   .catch(function(){});
})();
/* Daily Sale tile: the maker's own to-do line (S187_P2a). Fail-soft: no
   medical seat or finance down -> the static text stands. */
(function(){
  var el=document.querySelector('[data-daily-sale-counts]');
  if(!el)return;
  fetch('/finance/api/my-day-summary',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok)return;
     var p=[];
     if(d.to_file)p.push('\u270D\uFE0F '+d.to_file+' day'+(d.to_file>1?'s':'')+' to file');
     p.push(d.today?('today: '+d.today):'today: not started');
     /* S195: his own cash/UPI accuracy, from the only independent witness there
        is (the bank). Says nothing when the bank could check no day at all --
        there is nothing to claim then. */
     var a=d.accuracy;
     if(a&&a.checked){
       p.push(a.differing
         ? ('\u26A0 '+a.differing+' cash/UPI day'+(a.differing>1?'s':'')+' to fix')
         : ('\u2714 cash/UPI matched '+a.matched+'/'+a.checked));
     }
     el.textContent=p.join(' \u00b7 ');
   })
   .catch(function(){});
})();
/* Sanjeevni tile: live pending summary from the finance app (S187_P1a).
   Client-side, fail-soft: finance down or the viewer not the medical checker
   -> the static description stands and nothing breaks. Same-site SSO cookie. */
(function(){
  var el=document.querySelector('[data-sanjeevni-counts]');
  if(!el)return;
  fetch('/finance/api/tile-summary',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok)return;
     var p=[];
     /* S196: the health headline FIRST -- after the 21-08 Marg-401 crisis the
        health page existed but the tile stayed innocent-looking; this is the
        wire. Null when all is well, one short line when something is wrong. */
     if(d.health_line)p.push(d.health_line);
     if(d.to_approve)p.push('\u2705 '+d.to_approve+' to approve');
     if(d.marg_pushes)p.push('\U0001F4C4 '+d.marg_pushes+' Marg report'+(d.marg_pushes>1?'s':''));
     if(d.missing_marg)p.push('\U0001F4ED '+d.missing_marg+' day'+(d.missing_marg>1?'s':'')+' no Marg');
     if(d.exceptions)p.push('\u26A0 '+d.exceptions+' exception'+(d.exceptions>1?'s':''));
     el.textContent=p.length?p.join(' \u00b7 '):'\u2714 all clear \u00b7 month close inside';
   })
   .catch(function(){});
})();
/* Fill the Staff Register tile with live pending counts from the register.
   Client-side so the portal never waits on the register; if it is unreachable
   the tile keeps its static description. Same-site cookie carries the SSO. */
(function(){
  var el=document.querySelector('[data-review-counts]');
  if(!el)return;
  fetch('/portal/review-counts',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||typeof d.to_enter==='undefined')return;
     var s='\u270D\uFE0F '+d.to_enter+' to enter';
     if(d.show_approve)s+=' \u00B7 \u2705 '+d.to_approve+' to approve';
     el.textContent=s;
     /* S198_P1: the strip chip reads the same payload. */
     var c=document.getElementById('chipReg');
     if(c)c.textContent=d.to_enter;
   })
   .catch(function(){});
})();
/* Clinic Gist tile: one-line live summary from the same JSON the page renders.
   Client-side so the portal never waits on the file; if unreadable the tile keeps
   its static description. */
(function(){
  var el=document.querySelector('[data-gist-summary]');
  if(!el)return;
  fetch('/portal/gist-data',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok||!d.gist)return;
     var g=d.gist, c=g.calls||{};
     var s='\U0001F4DE '+(c.in_today||0)+' in \u00b7 '+(c.out_today||0)+' out';
     if(typeof g.unfiled_outcomes==='number')s+=' \u00b7 '+g.unfiled_outcomes+' pending';
     if(g.pipeline&&g.pipeline.escalate_lokesh)s+=' \u00b7 \u26A0';
     if(d.stale)s+=' (stale)';
     el.textContent=s;
   })
   .catch(function(){});
})();
/* Clinic finance tiles: the wording is a SETTING (clinic.tile.*), so the label
   is fetched rather than duplicated here. tile-meta answers for the signed-in
   person only - it returns the ONE tile matching their seat (checker wins when
   somebody holds both), so we match on href and leave any other clinic tile on
   its static text. Client-side, so the portal never waits on the finance app;
   if finance is down or the user has no clinic seat, the tiles keep the text
   rendered above and nothing breaks. */
(function(){
  var tiles=document.querySelectorAll('a[data-clinic-tile]');
  if(!tiles.length)return;
  fetch('/finance/clinic/api/tile-meta',{credentials:'same-origin'})
   .then(function(r){return r.ok?r.json():null;})
   .then(function(d){
     if(!d||!d.ok||!d.href)return;
     for(var i=0;i<tiles.length;i++){
       var a=tiles[i];
       if(a.getAttribute('href')!==d.href)continue;
       var nm=a.querySelector('.nm'), ds=a.querySelector('.ds');
       if(nm&&d.title)nm.textContent=d.title;
       if(ds&&d.subtitle)ds.textContent=d.subtitle;
     }
   })
   .catch(function(){});
})();
</script>
</div></body></html>
"""

PC_MARKED_HTML = PAGE_HEAD + """
<div class="login">
  <h1>{{ '\U0001F5A5\uFE0F Clinic PC set' if on else 'Cleared' }}</h1>
  <p>{% if on %}The Clinic-PC-only tools are now visible on this device.
     Tap a tile to open a local tool.{% else %}
     This device no longer shows the Clinic-PC-only tools.{% endif %}</p>
  <a class="note" href="/portal">Back to the portal</a>
</div></body></html>
"""

CONFIG_ERROR_HTML = PAGE_HEAD + """
<div class="login">
  <h1>Setup needed</h1>
  <p>The portal is installed but not configured yet.<br>
  Run the one-time setup to set the PIN and secrets.</p>
</div></body></html>
"""

USERS_HTML = PAGE_HEAD + """
<style>
.u-tbl{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
.u-tbl th,.u-tbl td{border-bottom:1px solid var(--line);padding:8px 8px;text-align:left;vertical-align:middle}
.u-tbl th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
.u-tbl td.u{font-weight:600;white-space:nowrap}
.upill{font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px}
.upill.on{background:rgba(34,197,94,.16);color:#86efac}
.upill.off{background:rgba(239,68,68,.16);color:#fca5a5}
.upill.you{background:rgba(59,130,246,.18);color:#93c5fd;margin-left:6px}
.acts{display:flex;gap:6px;flex-wrap:wrap;align-items:flex-end}
.acts form{margin:0}
.ibtn{font-size:12px;padding:6px 10px;border-radius:8px;border:1px solid var(--line);
 background:var(--card);color:var(--ink);cursor:pointer}
.ibtn.danger:hover{border-color:#7f1d1d;color:#fca5a5}
.ibtn.go{background:var(--blue);border-color:var(--blue);color:#fff}
.ibtn:disabled{opacity:.4;cursor:not-allowed}
.ucard{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:14px 0}
.ucard h2{font-size:14px;color:#fff;margin:0 0 10px}
.fld{display:inline-flex;flex-direction:column;gap:3px;margin:0 10px 8px 0}
.fld label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.fld input,.fld select,.acts select{background:#0b1b29;border:1px solid var(--line);color:#fff;border-radius:8px;padding:8px 8px;font-size:13px}
.msg{padding:9px 12px;border-radius:10px;margin:10px 0;font-size:13px}
.msg.ok{background:rgba(34,197,94,.14);color:#bbf7d0}.msg.err{background:rgba(239,68,68,.14);color:#fecaca}
.role{min-width:104px}
</style>
<div class="wrap">
  <div class="head">
    <h1>\U0001F511 Manage users</h1>
    <span class="sub">Signed in as {{ who.user }} &middot; logins &amp; roles for all clinic apps</span>
  </div>
  {% if msg %}<div class="msg {{ msgcls }}">{{ msg }}</div>{% endif %}

  <div class="ucard">
    <h2>Add a login</h2>
    <form method="POST" action="/portal/users/add" class="acts">
      <div class="fld"><label>Username</label><input name="user" autocapitalize="none" autocorrect="off" required></div>
      <div class="fld"><label>Role</label>
        <select name="role" class="role">{% for r in roles %}<option value="{{ r }}">{{ r }}</option>{% endfor %}</select></div>
      <div class="fld"><label>Password (min 6)</label><input name="password" type="password" required></div>
      <button class="ibtn go" type="submit">Add user</button>
    </form>
  </div>

  <div class="ucard">
    <h2>Users</h2>
    <table class="u-tbl">
      <tr><th>User</th><th>Role</th><th>Status</th><th>Since</th><th>Actions</th></tr>
      {% for u in users %}
      <tr>
        <td class="u">{{ u.user }}{% if u.user == who.user %}<span class="upill you">you</span>{% endif %}</td>
        <td>
          <form method="POST" action="/portal/users/role" class="acts">
            <input type="hidden" name="user" value="{{ u.user }}">
            <select name="role" class="role">{% for r in roles %}<option value="{{ r }}"{% if r==u.role %} selected{% endif %}>{{ r }}</option>{% endfor %}</select>
            <button class="ibtn" type="submit">Set</button>
          </form>
        </td>
        <td>{% if u.active %}<span class="upill on">active</span>{% else %}<span class="upill off">off</span>{% endif %}</td>
        <td style="color:var(--muted);font-size:12px">{{ u.created[:10] }}</td>
        <td>
          <div class="acts">
            {% if u.active %}
            <form method="POST" action="/portal/users/active" onsubmit="return confirm('Deactivate {{ u.user }}? They will be unable to sign in.');">
              <input type="hidden" name="user" value="{{ u.user }}"><input type="hidden" name="active" value="0">
              <button class="ibtn danger" type="submit"{% if u.user==who.user %} disabled title="cannot deactivate yourself"{% endif %}>Deactivate</button>
            </form>
            {% else %}
            <form method="POST" action="/portal/users/active">
              <input type="hidden" name="user" value="{{ u.user }}"><input type="hidden" name="active" value="1">
              <button class="ibtn go" type="submit">Activate</button>
            </form>
            {% endif %}
            <form method="POST" action="/portal/users/passwd"
                  onsubmit="var p=prompt('New password for {{ u.user }} (min 6):');if(!p)return false;this.password.value=p;return true;">
              <input type="hidden" name="user" value="{{ u.user }}"><input type="hidden" name="password" value="">
              <button class="ibtn" type="submit">Reset password</button>
            </form>
            <form method="POST" action="/portal/users/delete" onsubmit="return confirm('DELETE {{ u.user }} permanently? This removes their login.');">
              <input type="hidden" name="user" value="{{ u.user }}">
              <button class="ibtn danger" type="submit"{% if u.user==who.user %} disabled title="cannot delete yourself"{% endif %}>Delete</button>
            </form>
          </div>
        </td>
      </tr>
      {% endfor %}
    </table>
    <div class="note">Deactivating blocks future sign-ins. Sessions already open end when they expire or via "Sign out everywhere". App powers (maker / checker) are set inside each app, not here.</div>
  </div>

  <div class="foot"><a class="forget" href="/portal">&larr; Back to portal</a></div>
</div></body></html>
"""

# ---------------------------------------------------------------------------
# ROUTES  (all under /portal so the reverse proxy is clean)
# ---------------------------------------------------------------------------
@app.route("/portal")
@app.route("/portal/")
def home():
    if not _usable():
        return render_template_string(CONFIG_ERROR_HTML), 503
    if not _authed(request):
        return redirect("/portal/login")
    who = _sso_user(request)
    # F-98: a trusted DEVICE is not an identity. Once broker mode is genuinely
    # available, an unidentified caller is sent to sign in rather than being
    # served the full doctor portal. When broker mode is NOT available the old
    # device-trust path is untouched, so a config failure degrades to the
    # previous behaviour instead of locking everyone out (D264, inert on failure).
    if who is None and _sso_ready():
        return redirect("/portal/login")
    role = who["role"] if who else "doctor"
    pc = _is_clinic_pc(request)
    return render_template_string(PORTAL_HTML,
                                  sections=_visible_sections(role, pc, who["user"] if who else ""),
                                  sso=_sso_ready(), who=who, role=role,
                                  pc=pc)


@app.route("/portal/login", methods=["GET", "POST"])
def login():
    if not _usable():
        return render_template_string(CONFIG_ERROR_HTML), 503
    if _authed(request):
        return redirect("/portal")
    error = ""

    # --- BROKER MODE: username + password -> SSO cookie --------------------
    if _sso_ready():
        if request.method == "POST":
            user = (request.form.get("user") or "").strip()
            pw = (request.form.get("password") or "")
            role = None
            try:
                role = clinic_users.verify_password(STORE, user, pw)
            except Exception:
                role = None
            if role:
                resp = make_response(redirect("/portal"))
                # 1) the SSO cookie -- rides to every .dr-manoj.in clinic app
                token = clinic_sso.make_token(user, role,
                                              clinic_users.get_epoch(STORE), SSO_SECRET)
                resp.set_cookie(clinic_sso.COOKIE_NAME, token, **clinic_sso.cookie_kwargs())
                # 2) the device-trust cookie -- keeps the portal's own access identical to before
                resp.set_cookie(
                    COOKIE_NAME, _expected_device_token(),
                    max_age=10 * 365 * 24 * 3600,
                    secure=True, httponly=True, samesite="Lax", path="/portal",
                )
                return resp
            error = "Wrong username or password."
        return render_template_string(USERPASS_HTML, error=error)

    # --- LEGACY MODE: PIN (unchanged) -------------------------------------
    if request.method == "POST":
        pin = (request.form.get("pin") or "").strip()
        if pin and hmac.compare_digest(_hash_pin(pin), PIN_HASH):
            resp = make_response(redirect("/portal"))
            # Indefinite remember: ~10 years. Secure + HttpOnly + SameSite.
            resp.set_cookie(
                COOKIE_NAME, _expected_device_token(),
                max_age=10 * 365 * 24 * 3600,
                secure=True, httponly=True, samesite="Lax", path="/portal",
            )
            return resp
        error = "Wrong PIN. Try again."
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/portal/forget", methods=["POST"])
@login_required
def forget():
    """
    'Forget all devices' — for a lost/stolen device.
    We rotate the server seed in portal_config.py so EVERY existing device cookie
    becomes invalid at once. Requires write access to the config file.
    If we cannot write the file, we at least clear THIS device and tell the
    doctor to rotate PORTAL_TOKEN_SEED manually.
    """
    new_seed = secrets.token_urlsafe(32)
    rotated = _rotate_seed_in_config(new_seed)
    resp = make_response(redirect("/portal/login"))
    resp.delete_cookie(COOKIE_NAME, path="/portal")
    if not rotated:
        # Could not rewrite config; this device is signed out regardless.
        pass
    return resp


@app.route("/portal/signout-all", methods=["POST"])
@login_required
def signout_all():
    """
    BROKER: 'Sign out everywhere (all apps)'. Bumps the shared SSO epoch so every
    clinic_sso token issued so far is rejected by every app at once, and clears the
    SSO cookie on this device. Device-trust for the portal is also dropped here.
    """
    if _sso_ready():
        try:
            clinic_users.bump_epoch(STORE)
        except Exception:
            pass
    resp = make_response(redirect("/portal/login"))
    if _SSO_LIBS:
        try:
            resp.set_cookie(clinic_sso.COOKIE_NAME, "", **clinic_sso.clear_cookie_kwargs())
        except Exception:
            pass
    resp.delete_cookie(COOKIE_NAME, path="/portal")
    return resp


@app.route("/portal/health")
def health():
    """Simple health probe for the future Diagnostics system."""
    ready = _usable()
    mode = "broker" if _sso_ready() else ("legacy" if _config_ok() else "unconfigured")
    return {"service": "portal", "status": "ok" if ready else "unconfigured",
            "mode": mode}, (200 if ready else 503)


# Same-origin source for the Staff Register tile's pending counts. The browser hits
# THIS (followup origin, no CORS); we fetch the register server-side over localhost,
# forwarding the caller's SSO cookie, and pass its JSON straight through. Any failure
# -> {} so the tile keeps its static text; the portal never waits on / depends on the
# register being up. Register local addr overridable via portal_config.
REGISTER_COUNTS_URL = _cfg_get(
    "REGISTER_COUNTS_URL", "http://127.0.0.1:8044/register/review/counts")


@app.route("/portal/review-counts")
@login_required
def review_counts_proxy():
    out = "{}"
    try:
        req = urllib.request.Request(REGISTER_COUNTS_URL)
        ck = request.headers.get("Cookie", "")
        if ck:
            req.add_header("Cookie", ck)
        with urllib.request.urlopen(req, timeout=2) as r:
            if getattr(r, "status", 200) == 200:
                out = r.read().decode("utf-8", "replace")
    except Exception:
        out = "{}"
    resp = make_response(out)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Cache-Control"] = "no-store"
    return resp


# --- USER MANAGEMENT (manoj-only) -----------------------------------------------
def _users_redir(msg, ok=True):
    return redirect("/portal/users?m=%s&c=%s"
                    % (urllib.parse.quote(msg), "ok" if ok else "err"))


def _render_users(msg="", msgcls="ok"):
    if not _SSO_LIBS or not STORE:
        return render_template_string(CONFIG_ERROR_HTML), 503
    who = _sso_user(request)
    users = clinic_users.list_users(STORE)
    roles = clinic_users.load_store(STORE).get("roles", [])
    return render_template_string(USERS_HTML, who=who, users=users, roles=roles,
                                  msg=msg, msgcls=msgcls)


@app.route("/portal/users")
@user_admin_required
def users_admin():
    return _render_users(request.args.get("m", ""), request.args.get("c", "ok"))


@app.route("/portal/users/add", methods=["POST"])
@user_admin_required
def users_add():
    user = request.form.get("user", ""); role = request.form.get("role", "")
    pw = request.form.get("password", "")
    try:
        clinic_users.add_user(STORE, user, role, pw)
        return _users_redir("added %s (%s)" % (user.strip().lower(), role))
    except ValueError as e:
        return _users_redir(str(e), ok=False)


@app.route("/portal/users/role", methods=["POST"])
@user_admin_required
def users_role():
    user = request.form.get("user", ""); role = request.form.get("role", "")
    try:
        clinic_users.set_role(STORE, user, role)
        return _users_redir("role of %s set to %s" % (user.strip().lower(), role))
    except ValueError as e:
        return _users_redir(str(e), ok=False)


@app.route("/portal/users/passwd", methods=["POST"])
@user_admin_required
def users_passwd():
    user = request.form.get("user", ""); pw = request.form.get("password", "")
    try:
        clinic_users.set_password(STORE, user, pw)
        return _users_redir("password reset for %s" % user.strip().lower())
    except ValueError as e:
        return _users_redir(str(e), ok=False)


@app.route("/portal/users/active", methods=["POST"])
@user_admin_required
def users_active():
    user = request.form.get("user", "")
    active = request.form.get("active", "1") == "1"
    me = (_sso_user(request) or {}).get("user", "")
    if not active:
        err = _admin_guard("deactivate", user, me)
        if err:
            return _users_redir(err, ok=False)
    try:
        clinic_users.set_active(STORE, user, active)
        return _users_redir("%s %s" % ("activated" if active else "deactivated",
                                       user.strip().lower()))
    except ValueError as e:
        return _users_redir(str(e), ok=False)


@app.route("/portal/users/delete", methods=["POST"])
@user_admin_required
def users_delete():
    user = request.form.get("user", "")
    me = (_sso_user(request) or {}).get("user", "")
    err = _admin_guard("delete", user, me)
    if err:
        return _users_redir(err, ok=False)
    try:
        clinic_users.del_user(STORE, user)
        return _users_redir("deleted %s" % user.strip().lower())
    except ValueError as e:
        return _users_redir(str(e), ok=False)


@app.route("/portal/mark-pc")
@login_required
def mark_pc():
    """Visit ONCE in the clinic PC's own browser to reveal the Clinic-PC-only
    tiles on that device. Sets a signed marker cookie (path=/portal)."""
    resp = make_response(render_template_string(PC_MARKED_HTML, on=True))
    resp.set_cookie(PC_COOKIE, _pc_token(),
                    max_age=10 * 365 * 24 * 3600,
                    secure=True, httponly=True, samesite="Lax", path="/portal")
    return resp


@app.route("/portal/unmark-pc")
@login_required
def unmark_pc():
    """Undo mark-pc (e.g. if the wrong device was marked)."""
    resp = make_response(render_template_string(PC_MARKED_HTML, on=False))
    resp.delete_cookie(PC_COOKIE, path="/portal")
    return resp


@app.route("/portal/gmb")
@login_required
def gmb():
    """Serve the GMB Review Assist page from the VPS. It is a static, self-contained
    HTML page (no patient data, all client-side), so it is served as-is behind login,
    reachable on any device. Read per-request so the page can be updated without a
    code change (just replace the file)."""
    try:
        with open(GMB_HTML_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ("GMB page not installed. Place the HTML file at "
                + GMB_HTML_PATH), 503


# ===========================================================================
# D223 GIST TILE  --  the doctor's bird's-eye. Reads /root/wa/portal_gist.json
# (built by portal_gist.py on its own cron) and RENDERS it. The portal never
# computes (D236); it only reads. A missing or stale file is SAID so on the page,
# never shown as a fake zero (fail-loud carries through to the UI).
# ===========================================================================
GIST_JSON_PATH = _cfg_get("PORTAL_GIST_JSON", "/root/wa/portal_gist.json")
_IST_TZ = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _read_gist(path=None):
    """Parse the gist json. Returns the dict, or None on any failure."""
    try:
        with open(path or GIST_JSON_PATH, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _gist_view(path=None, now=None):
    """Read the gist + decorate with freshness. Always returns a render-safe dict:
      {ok, stale, age_min, gist}.  ok=False when the file is unreadable."""
    d = _read_gist(path)
    if d is None:
        return {"ok": False, "stale": True, "age_min": None, "gist": None}
    stale_after = d.get("stale_after_min", 45)
    age_min, stale = None, True
    try:
        gen = datetime.datetime.fromisoformat(d.get("generated_ist", ""))
        cur = now or datetime.datetime.now(gen.tzinfo or _IST_TZ)
        age_min = int((cur - gen).total_seconds() // 60)
        stale = age_min > stale_after
    except Exception:
        pass
    return {"ok": True, "stale": stale, "age_min": age_min, "gist": d}


def _is_doctor(req) -> bool:
    """F-98: identity is PROVEN, never assumed.

    Previously a trusted device with no SSO user was treated as the doctor, so a
    browser still holding the legacy PIN-era device cookie reached every
    @doctor_required surface — the Gist, the Call Console, the staff coaching
    report. That is F-84's pattern (identity granted for convenience) sitting in
    the SSO broker itself.

    Now: if broker mode is available, only a verified SSO user with role=doctor
    qualifies. If broker mode is NOT available, the legacy estate behaves exactly
    as before, so this edit cannot remove existing access (D264).
    """
    who = _sso_user(req)
    if who is not None:
        return who.get("role") == "doctor"
    return not _sso_ready()


def doctor_required(view):
    @wraps(view)
    def wrapper(*a, **k):
        if not _authed(request):
            return redirect("/portal/login")
        if not _is_doctor(request):
            abort(403)
        return view(*a, **k)
    return wrapper


# ---------------------------------------------------------------------------
# SURGICAL CASE PACK (S172) — logic lives beside this file in
# casepack_portal.py; the page HTML + all case files live under
# /root/wa/casepack/ (PHI store — gitignored, F-31/F-49).
# Owner-only: SSO user must be in PORTAL_CASEPACK_USERS (default manoj);
# a trusted device with NO SSO user is the owner's legacy device -> allowed
# (mirrors the _is_doctor transition rule).
# ---------------------------------------------------------------------------
CASEPACK_USERS = set(x.strip().lower() for x in
                     _cfg_get("PORTAL_CASEPACK_USERS", "manoj").split(",") if x.strip())


def _is_casepack_user(req) -> bool:
    who = _sso_user(req)
    if who is None:
        return _is_trusted(req)
    return (who.get("role") == "doctor" and
            (who.get("user") or "").lower() in CASEPACK_USERS)


def casepack_required(view):
    @wraps(view)
    def wrapper(*a, **k):
        if not _authed(request):
            return redirect("/portal/login")
        if not _is_casepack_user(request):
            abort(403)
        return view(*a, **k)
    return wrapper


try:
    import casepack_portal
    casepack_portal.register(
        app, casepack_required,
        lambda: ((_sso_user(request) or {}).get("user") or "doctor"))
    CASEPACK_IMPORT_ERR = ""
except Exception as _cp_e:                      # fail loud on the page, never brick the portal
    CASEPACK_IMPORT_ERR = str(_cp_e)

    @app.route("/portal/casepack")
    @login_required
    def _casepack_broken():
        return make_response(
            "Surgical Case Pack failed to load: " + CASEPACK_IMPORT_ERR, 500)


# ---------------------------------------------------------------------------
# SHARED WHATSAPP SENDER (S172, Phase A) — one sender for the whole portal,
# backed by MyOperator WABA (System B). Doctor-only for now (decision S172);
# the GAS callback tracker's agent-reply hook is Phase B. Token + DRY flag come
# from the portal env (MYOP_AUTH_TOKEN / PORTAL_WA_DRYRUN, default DRY).
# ---------------------------------------------------------------------------
WA_USERS = set(x.strip().lower() for x in
               _cfg_get("PORTAL_WA_USERS", "manoj").split(",") if x.strip())


def _is_wa_user(req) -> bool:
    who = _sso_user(req)
    if who is None:
        return _is_trusted(req)
    return (who.get("role") == "doctor" and
            (who.get("user") or "").lower() in WA_USERS)


def wa_required(view):
    @wraps(view)
    def wrapper(*a, **k):
        if not _authed(request):
            return redirect("/portal/login")
        if not _is_wa_user(request):
            abort(403)
        return view(*a, **k)
    return wrapper


try:
    import portal_wa
    portal_wa.register(
        app, wa_required,
        lambda: ((_sso_user(request) or {}).get("user") or "doctor"),
        _cfg_get)
    WA_IMPORT_ERR = ""
except Exception as _wa_e:
    WA_IMPORT_ERR = str(_wa_e)

    @app.route("/portal/wa")
    @login_required
    def _wa_broken():
        return make_response("WhatsApp sender failed to load: " + WA_IMPORT_ERR, 500)


try:
    import portal_followups
    portal_followups.register(
        app, wa_required,
        lambda: ((_sso_user(request) or {}).get("user") or "doctor"),
        _cfg_get, portal_wa.send)
    FU_IMPORT_ERR = ""
except Exception as _fu_e:
    FU_IMPORT_ERR = str(_fu_e)

    @app.route("/portal/wa/followups")
    @login_required
    def _fu_broken():
        return make_response("Follow-up batch failed to load: " + FU_IMPORT_ERR, 500)


GIST_HTML = PAGE_HEAD + """
<style>
.gcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow)}
.gmetrics{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin-top:6px}
.gbig{font-size:25px;font-weight:700;color:#fff;line-height:1.15}
.glabel{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.gsub{font-size:12px;color:var(--muted);margin-top:5px}
.gbanner{border-radius:12px;padding:10px 14px;font-size:13px;margin:6px 0 14px}
.gbanner.warn{background:rgba(234,179,8,.14);color:#fde68a;border:1px solid rgba(234,179,8,.35)}
.gbanner.bad{background:rgba(239,68,68,.14);color:#fecaca;border:1px solid rgba(239,68,68,.4)}
.gpill{display:inline-block;font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px}
.gpill.ok{background:rgba(34,197,94,.16);color:#86efac}
.gpill.bad{background:rgba(239,68,68,.18);color:#fca5a5}
.gpill.mut{background:rgba(91,113,132,.25);color:#b8c7d6}
.gfoot{margin-top:22px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.gnote{font-size:11px;color:var(--muted)}
</style>
<div class="wrap">
  <div class="head">
    <h1>\U0001F4CA Clinic Gist</h1>
    <span class="sub">Live bird's-eye \u00b7 read-only</span>
  </div>

  {% if not v.ok %}
    <div class="gbanner bad">The gist data could not be read yet \u2014 numbers are withheld
      (never shown as zero). It rebuilds every 30 min; check back shortly.</div>
    <div class="gfoot"><a class="forget" href="/portal">&larr; Back to portal</a></div>
  {% else %}
    {% if v.stale %}
      <div class="gbanner warn">\u26A0 Stale \u2014 last built {{ v.age_min }} min ago
        (fresh under {{ g.stale_after_min }} min). The builder may not have run; treat with caution.</div>
    {% endif %}
    {% if not g.sources_ok %}
      <div class="gbanner warn">Some sources were unreadable this run \u2014 affected numbers are blank, not zero.
        {% for n in g.notes %}{% if 'verdict_awaiting_referee' not in n %}<div class="gnote">\u2022 {{ n }}</div>{% endif %}{% endfor %}
      </div>
    {% endif %}

    <div class="gmetrics">
      <div class="gcard">
        <div class="glabel">Calls today</div>
        {% if g.calls %}
          <div class="gbig">{{ g.calls.in_today }} in \u00b7 {{ g.calls.out_today }} out</div>
          <div class="gsub">Last 7 days: {{ g.calls.in_7d }} in \u00b7 {{ g.calls.out_7d }} out</div>
        {% else %}<div class="gbig">\u2014</div><div class="gsub">unavailable</div>{% endif %}
      </div>

      <div class="gcard">
        <div class="glabel">Recording health (7d)</div>
        {% if g.pipeline %}
          {% if g.pipeline.escalate_lokesh %}
            <div class="gbig">\u26A0 {{ g.pipeline.never_recorded_7d }}</div>
            <div class="gsub"><span class="gpill bad">Escalate to Lokesh</span></div>
          {% elif g.pipeline.never_recorded_7d > 0 %}
            <div class="gbig">{{ g.pipeline.never_recorded_7d }} losses</div>
            <div class="gsub">genuine provider recording losses</div>
          {% else %}
            <div class="gbig">\u2713 0 losses</div>
            <div class="gsub"><span class="gpill ok">healthy</span> \u00b7 {{ g.pipeline.missed_7d }} missed (no recording expected)</div>
          {% endif %}
        {% else %}<div class="gbig">\u2014</div><div class="gsub">unavailable</div>{% endif %}
      </div>

      <div class="gcard">
        <div class="glabel">Callbacks awaiting staff</div>
        {% if g.unfiled_outcomes is not none %}
          <div class="gbig">{{ g.unfiled_outcomes }}</div>
          <div class="gsub">open in Callbacks_Today, not yet actioned</div>
        {% else %}<div class="gbig">\u2014</div><div class="gsub">unavailable</div>{% endif %}
      </div>

      <div class="gcard">
        <div class="glabel">3rd-strike numbers (7d)</div>
        {% if g.third_strikes_7d is not none %}
          <div class="gbig">{{ g.third_strikes_7d }}</div>
          <div class="gsub">reached 3 WhatsApp strikes (don't-call risk)</div>
        {% else %}<div class="gbig">\u2014</div><div class="gsub">unavailable</div>{% endif %}
      </div>

      <div class="gcard">
        <div class="glabel">Verdict cards awaiting referee</div>
        <div class="gbig"><span class="gpill mut">coming soon</span></div>
        <div class="gsub">wires in when the AI-verdict store is bound</div>
      </div>
    </div>

    <div class="gfoot">
      <span class="gnote">{% if v.age_min is not none %}Updated {{ v.age_min }} min ago{% else %}Update time unknown{% endif %}
        \u00b7 auto-refreshes every 30 min</span>
      <a class="forget" href="/portal">&larr; Back to portal</a>
    </div>
  {% endif %}
</div></body></html>
"""


@app.route("/portal/gist-data")
@doctor_required
def gist_data():
    resp = make_response(json.dumps(_gist_view()))
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/portal/gist")
@doctor_required
def gist_page():
    v = _gist_view()
    return render_template_string(GIST_HTML, v=v, g=(v.get("gist") or {}))


# ===========================================================================
# S198_P2 (A3) — FORMS & DOWNLOADS. Blank clinic forms for printing.
# ---------------------------------------------------------------------------
# Files live at FORMS_DIR on the box ONLY (public-repo rule D320). The files
# ARE the list — no database, no metadata to drift. Names are sanitised hard
# (basename + charset allowlist + extension allowlist), so a crafted name can
# never leave the folder. View/print/download = any logged-in identity;
# add/remove = proven doctor (F-98 rule, the same gate the Gist uses).
# ===========================================================================
FORMS_ALLOWED_EXT = (".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx")
FORMS_MAX_BYTES = 15 * 1024 * 1024
_FORMS_ICON = {".pdf": "\U0001F4C4", ".png": "\U0001F5BC\uFE0F",
               ".jpg": "\U0001F5BC\uFE0F", ".jpeg": "\U0001F5BC\uFE0F",
               ".docx": "\U0001F4DD", ".xlsx": "\U0001F4CA"}


def _forms_safe(name):
    """A filename we will touch, or None. basename first, then an allowlist —
    refusal is the default (F-84 ordering)."""
    import re as _fre
    base = os.path.basename(str(name or "")).strip()
    if not base or base.startswith("."):
        return None
    if not _fre.match(r"^[A-Za-z0-9 ._()\-]{1,120}$", base):
        return None
    ext = os.path.splitext(base)[1].lower()
    if ext not in FORMS_ALLOWED_EXT:
        return None
    return base


def _forms_list():
    try:
        names = sorted(n for n in os.listdir(FORMS_DIR) if _forms_safe(n))
    except FileNotFoundError:
        return []
    out = []
    for n in names:
        p = os.path.join(FORMS_DIR, n)
        try:
            st = os.stat(p)
        except OSError:
            continue
        ext = os.path.splitext(n)[1].lower()
        out.append(dict(name=n, icon=_FORMS_ICON.get(ext, "\U0001F4C4"),
                        kb=max(1, st.st_size // 1024),
                        day=datetime.date.fromtimestamp(st.st_mtime).isoformat()))
    return out


FORMS_HTML = HOME_HEAD + """
<div class="topbar"><div class="topin">
  <div class="tname">\U0001F5A8\uFE0F Forms &amp; Downloads</div>
  <div class="tsub">print-ready clinic forms</div>
  <div class="tright"><a href="/portal" style="color:var(--blue);text-decoration:none">\u2190 Portal</a></div>
</div></div>
<div class="wrap" style="max-width:760px">
  {% if msg %}<div style="background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:10px 14px;margin:12px 0;color:var(--ink)">{{ msg }}</div>{% endif %}
  {% if is_doctor %}
  <div class="kick">Add a form</div>
  <form method="POST" action="/portal/forms/upload" enctype="multipart/form-data"
        style="background:var(--card);border:1px solid var(--line);border-radius:10px;
        padding:12px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <input type="file" name="f" required accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
           style="color:var(--muted);font-size:13px">
    <button type="submit" style="background:var(--blue);color:#fff;border:none;
      border-radius:9px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer">Upload</button>
    <span style="font-size:11.5px;color:var(--muted)">PDF is best for printing \u00b7 max 15 MB \u00b7
      a name already in the list is refused (delete it first)</span>
  </form>
  {% endif %}
  <div class="kick">Forms ({{ forms|length }})</div>
  {% if not forms %}<div style="color:var(--muted);font-size:13.5px">No forms yet.{% if is_doctor %}
    Upload the first one above.{% endif %}</div>{% endif %}
  {% for f in forms %}
  <div style="display:flex;align-items:center;gap:12px;background:var(--card);
       border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:8px 0">
    <span style="font-size:22px">{{ f.icon }}</span>
    <span style="min-width:0;flex:1"><span style="font-size:14px;font-weight:600;color:#fff">{{ f.name }}</span><br>
      <span style="font-size:11.5px;color:var(--muted)">{{ f.kb }} KB \u00b7 {{ f.day }}</span></span>
    <a href="/portal/forms/file/{{ f.name|urlencode }}" target="_blank" rel="noopener"
       style="color:var(--blue);text-decoration:none;font-size:13px;font-weight:600">Open / Print</a>
    <a href="/portal/forms/file/{{ f.name|urlencode }}?dl=1"
       style="color:var(--muted);text-decoration:none;font-size:13px">Download</a>
    {% if is_doctor %}
    <form method="POST" action="/portal/forms/delete" style="margin:0"
          onsubmit="return confirm('Remove {{ f.name }} from the portal?');">
      <input type="hidden" name="name" value="{{ f.name }}">
      <button type="submit" style="background:none;border:1px solid var(--line);color:var(--muted);
        border-radius:8px;padding:5px 10px;font-size:12px;cursor:pointer">remove</button>
    </form>
    {% endif %}
  </div>
  {% endfor %}
  <div style="margin-top:18px;font-size:12px;color:var(--muted)">Open / Print shows the form in a new
  tab \u2014 print from there (Ctrl+P). Files live on the clinic server only.</div>
</div></body></html>
"""


@app.route("/portal/forms")
@login_required
def forms_page():
    return render_template_string(
        FORMS_HTML, forms=_forms_list(), is_doctor=_is_doctor(request),
        msg=request.args.get("m", "")[:200])


@app.route("/portal/forms/file/<path:name>")
@login_required
def forms_file(name):
    safe = _forms_safe(name)
    if not safe:
        abort(404)
    path = os.path.join(FORMS_DIR, safe)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=bool(request.args.get("dl")),
                     download_name=safe)


@app.route("/portal/forms/upload", methods=["POST"])
@doctor_required
def forms_upload():
    f = request.files.get("f")
    if f is None or not f.filename:
        return redirect("/portal/forms?m=No file chosen.")
    safe = _forms_safe(f.filename)
    if not safe:
        return redirect("/portal/forms?m=That file type or name is not allowed "
                        "(pdf, png, jpg, docx, xlsx; plain names).")
    os.makedirs(FORMS_DIR, exist_ok=True)
    path = os.path.join(FORMS_DIR, safe)
    if os.path.exists(path):
        return redirect("/portal/forms?m=A form with that name already exists "
                        "- remove it first if you want to replace it.")
    data = f.read(FORMS_MAX_BYTES + 1)
    if len(data) > FORMS_MAX_BYTES:
        return redirect("/portal/forms?m=Too large (max 15 MB).")
    with open(path, "wb") as out:
        out.write(data)
    return redirect("/portal/forms?m=Added %s." % safe)


@app.route("/portal/forms/delete", methods=["POST"])
@doctor_required
def forms_delete():
    safe = _forms_safe(request.form.get("name", ""))
    path = os.path.join(FORMS_DIR, safe) if safe else ""
    if not safe or not os.path.isfile(path):
        return redirect("/portal/forms?m=Not found.")
    os.remove(path)
    return redirect("/portal/forms?m=Removed %s." % safe)


# ===========================================================================
# S198_P4 (A4) — THE PORTAL AS A PHONE APP (PWA).
# ---------------------------------------------------------------------------
# The S196_ATT2 pattern, applied to the portal itself: manifest + two icons
# built from the REAL clinic logo (the exact bytes ATT2 ships — one identity
# on every home screen). The three routes are unauthenticated ON PURPOSE:
# the browser's install machinery fetches them outside the login session, and
# they contain nothing but a name and a picture. NO service worker (the ATT2
# ruling kept): nothing cached offline, every view is live.
# scope "/" so the finance pages a tile opens stay INSIDE the app window;
# the attendance-subdomain tiles open with browser chrome (cross-origin —
# a known PWA limit, same as ATT2's own app).
# ===========================================================================
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


@app.route("/portal/manifest.webmanifest")
def pwa_manifest():
    resp = make_response(json.dumps({
        "name": "Dr. Manoj Agarwal Clinic",
        "short_name": "Clinic",
        "start_url": "/portal",
        "scope": "/",
        "display": "standalone",
        "background_color": "#0f2233",
        "theme_color": "#0f2233",
        "icons": [
            {"src": "/portal/pwa-icon-192.png", "sizes": "192x192",
             "type": "image/png", "purpose": "any"},
            {"src": "/portal/pwa-icon-512.png", "sizes": "512x512",
             "type": "image/png", "purpose": "any maskable"},
        ],
    }))
    resp.headers["Content-Type"] = "application/manifest+json"
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


def _pwa_png(data):
    resp = make_response(data)
    resp.headers["Content-Type"] = "image/png"
    resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp


@app.route("/portal/pwa-icon-192.png")
def pwa_icon_192():
    return _pwa_png(_PWA_ICON_192)


@app.route("/portal/pwa-icon-512.png")
def pwa_icon_512():
    return _pwa_png(_PWA_ICON_512)


# ===========================================================================
# D297 CALL-INTELLIGENCE CONSOLE — Stage B1 page  [S168 rev2 -> S169 rev4]
# ---------------------------------------------------------------------------
# Reads /root/wa/console.db ONLY (built by portal_console.py, Stage A). Pure
# READER: read-only sqlite, never writes, FAIL-LOUD/STALE-AWARE (D236) — a
# missing/old db is SAID, never faked as zeros. Doctor-gated (D297 §3).
# rev2 fixes (S168, from live-data probe): tz-stripped date+time; number
# recovered from the join key / verdict when phone10 is blank (outbound);
# name resolved on the recovered number; AI-outcome column (was TRUE/FALSE);
# recording-link fallback via the recordings table; transcript text shown in
# threads; agent dimension driven off the REAL attribution names in the data
# (verdicts/outbound use full names like "Alisha Khan"; the roster is short).
# rev4 (S169): agent resolution now reads the additive call_agent table
# (portal_console.py Stage-2a, /search _us[received].ky -> Agents.UserId) FIRST,
# then verdict.agent, then outbound -- so the TRUE handler shows on every
# answered call (log, filter, facet, Staff tab). Precedence: call_agent >
# verdict > outbound.
# ===========================================================================
import re as _re

CONSOLE_DB_PATH   = _cfg_get("PORTAL_CONSOLE_DB", "/root/wa/console.db")
# --- W2 (Items 5+6): the PERSISTENT doctor-review store. console.db is rebuilt
# atomically every cron fire, so reviews/send-backs must live OUTSIDE it. This
# portal is the SOLE writer of console_reviews.db (D235); the builder reads it
# read-only to push open send-backs to the staff sheet tab.
REVIEWS_DB_PATH   = _cfg_get("PORTAL_REVIEWS_DB", "/root/wa/console_reviews.db")
REVIEW_VOCAB      = ["Coming", "Came", "Not coming", "Call again",
                     "Wrong claim by staff", "Spam / marketing", "Other"]
REC_CACHE_PATH    = _cfg_get("PORTAL_REC_CACHE", "/root/wa/rec_cache")
SPAM_OUTCOME      = "Spam / marketing"


def _spam_phones():
    """W3 Track M: phones I have marked Spam/marketing (disposition vocabulary).
    join_key = {phone10}_{unix} -> prefix. Fail-soft empty set."""
    out = set()
    try:
        conn = _reviews_conn()
        for (jk,) in conn.execute(
                "SELECT join_key FROM dispositions WHERE final_outcome=?", (SPAM_OUTCOME,)):
            if "_" in (jk or ""):
                out.add(jk.split("_", 1)[0])
        conn.close()
    except Exception:
        pass
    return out


def _reviews_conn():
    """RW connection; creates the schema on first use (portal owns it)."""
    conn = sqlite3.connect(REVIEWS_DB_PATH, timeout=5)
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS dispositions ("
        " join_key TEXT PRIMARY KEY, final_outcome TEXT, note TEXT,"
        " refereed_by TEXT, refereed_at TEXT);"
        "CREATE TABLE IF NOT EXISTS send_backs ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT, join_key TEXT, phone10 TEXT,"
        " patient TEXT, reason TEXT, sent_by TEXT, sent_at TEXT,"
        " status TEXT DEFAULT 'open');"
        "CREATE INDEX IF NOT EXISTS ix_sb_jk ON send_backs(join_key);")
    return conn


def _reviews_maps():
    """{join_key: disposition-dict}, {join_key: open-send-back-dict} for overlay.
    Fail-soft: any error -> empty maps, page still renders."""
    disp, sb = {}, {}
    try:
        conn = _reviews_conn()
        for jk, fo, note, ts in conn.execute(
                "SELECT join_key, final_outcome, note, refereed_at FROM dispositions"):
            disp[jk] = {"final_outcome": fo or "", "note": note or "", "at": (ts or "")[:16]}
        for jk, reason, ts, st in conn.execute(
                "SELECT join_key, reason, sent_at, status FROM send_backs "
                "WHERE status='open'"):
            sb[jk] = {"reason": reason or "", "at": (ts or "")[:16], "status": st}
        conn.close()
    except Exception:
        pass
    return disp, sb
CONSOLE_STALE_MIN = int(_cfg_get("PORTAL_CONSOLE_STALE_MIN", "25") or "25")

_FLAG_COLS = {"postop": "flag_postop", "complaint": "flag_complaint",
              "urgent": "flag_urgent", "surgery": "flag_surgery",
              "clinical": "flag_clinical", "conduct": "flag_conduct"}
_FLAG_LABEL = {"postop": "Post-op", "complaint": "Complaint", "urgent": "Urgent",
               "surgery": "Surgery", "clinical": "Clinical", "conduct": "Conduct"}
_FALSEY = ("", "0", "FALSE", "False", "false", "NO", "No", "no", "N", "n", "-")
_TZ_RE = _re.compile(r'([+-]\d{2}:?\d{2}|Z)\s*$')


def _split_dt(ts):
    """'2026-07-03T16:52:03+05:30' -> ('2026-07-03', '16:52:03'). Strips the tz
    offset the owner asked to remove; puts time in its own column."""
    ts = (ts or "").strip()
    if not ts:
        return "", ""
    ts = _TZ_RE.sub("", ts).strip().replace("T", " ")
    parts = ts.split(" ", 1)
    date = parts[0] if parts else ""
    time = (parts[1].strip() if len(parts) > 1 else "")[:8]
    return date, time


def _console_conn():
    try:
        if not os.path.exists(CONSOLE_DB_PATH):
            return None
        conn = sqlite3.connect("file:%s?mode=ro" % CONSOLE_DB_PATH, uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _console_meta(conn=None):
    own = False
    if conn is None:
        conn = _console_conn(); own = True
    if conn is None:
        return {"ok": False, "stale": True, "age_min": None, "built_at": "", "counts": {}}
    try:
        m = {r["k"]: r["v"] for r in conn.execute("SELECT k, v FROM meta")}
        built = m.get("built_at", "")
        age_min, stale = None, True
        try:
            gen = datetime.datetime.fromisoformat(_TZ_RE.sub("", built))
            age_min = int((datetime.datetime.now() - gen).total_seconds() // 60)
            stale = age_min > CONSOLE_STALE_MIN
        except Exception:
            pass
        counts = {}
        try:
            counts = json.loads(m.get("row_counts", "{}"))
        except Exception:
            pass
        return {"ok": True, "stale": stale, "age_min": age_min,
                "built_at": built, "counts": counts}
    except Exception:
        return {"ok": False, "stale": True, "age_min": None, "built_at": "", "counts": {}}
    finally:
        if own:
            conn.close()


def _console_filters(args):
    return {
        "view": args.get("view", "log"),
        "direction": args.get("direction", ""),
        "answered": args.get("answered", ""),
        "agent": args.get("agent", ""),
        "flag": args.get("flag", ""),
        "frm": args.get("from", ""),
        "to": args.get("to", ""),
        "q": (args.get("q", "") or "").strip(),
    }


# F-74: verdicts holds ALL rows (a re-judged call repeats its join_key) and
# patients can repeat a phone10 -> a plain LEFT JOIN would MULTIPLY call rows.
# These collapse to ONE row per key (SQLite: a single MAX() aggregate makes every
# bare column come from that same row -> MAX(id) = newest verdict per join_key).
_DV = ("(SELECT join_key, MAX(id) AS _vid, patient_number, patient_name, agent, "
       "clinic_id, duration, claimed_outcome, not_filed, ai_outcome, verdict, "
       "ai_reason, evidence, judged_at, "
       "outcome_tf, match_confidence, spoke_with, conduct_note, status, error, "
       "doctor_flag, doctor_note, final_outcome, recording_link, flag_postop, "
       "flag_complaint, flag_urgent, flag_surgery, flag_clinical, flag_conduct "
       "FROM verdicts WHERE join_key<>'' GROUP BY join_key)")
_DP = ("(SELECT phone10, MAX(rowid) AS _pid, name, diagnosis, age, gender, "
       "last_visit, patient_uid, clinic_id FROM patients WHERE phone10<>'' "
       "GROUP BY phone10)")

# Displayed number: phone10 if present, else the join-key prefix (Join Key =
# {phone10}_{unix}) -- recovers the blank OUTBOUND numbers.
_DPHONE = ("COALESCE(NULLIF(c.phone10,''), "
           "CASE WHEN instr(c.join_key,'_')>1 "
           "THEN substr(c.join_key,1,instr(c.join_key,'_')-1) ELSE '' END)")

# Agent for a call (S169 rev4, Stage-2a): the TRUE handler.
# Precedence: call_agent (real MyOperator handler, /search _us[received].ky ->
#   Agents.UserId) > verdict.agent > outbound.agent (recovered number + same day).
# call_agent is built by portal_console.py --with-myop-reconcile -- same build
# guarantee as `conversations`; join_key = {phone10}_{unix}. Full attribution
# names ("Alisha Khan"), NOT the short roster.
_CA_AGENT  = ("(SELECT ca.agent FROM call_agent ca "
              "WHERE ca.join_key=c.join_key AND c.join_key<>'')")
_OUT_AGENT = ("(SELECT o.agent FROM outbound o "
              "WHERE o.phone10=" + _DPHONE + " AND o.date=substr(c.ended_at_ist,1,10) LIMIT 1)")
_AGENT_EXPR = ("COALESCE(NULLIF(" + _CA_AGENT + ",''), "
               "NULLIF(v.agent,''), "
               "NULLIF(" + _OUT_AGENT + ",''), '')")

_LOG_FROM = ("FROM calls c "
             "LEFT JOIN " + _DV + " v ON v.join_key=c.join_key AND c.join_key<>'' "
             "LEFT JOIN " + _DP + " p ON p.phone10=" + _DPHONE + " AND " + _DPHONE + "<>'' ")

_LOG_COLS = (
    "SELECT c.id, c.ended_at_ist, c.direction, c.answered, c.total_duration, "
    "c.join_key, c.recording_filename, " + _DPHONE + " AS phone_disp, "
    "COALESCE(v.patient_number,'') AS vnum, "
    "COALESCE(NULLIF(v.patient_name,''), p.name, '') AS name, "
    "COALESCE(p.diagnosis,'') AS diagnosis, p._pid AS pid, "
    "COALESCE(p.age,'') AS age, COALESCE(p.gender,'') AS gender, "
    "COALESCE(v.claimed_outcome,'') AS claimed, COALESCE(v.not_filed,0) AS not_filed, "
    "COALESCE(v.ai_outcome,'') AS ai_outcome, COALESCE(v.verdict,'') AS verdict, "
    "COALESCE(v.ai_reason,'') AS ai_reason, COALESCE(v.evidence,'') AS evidence, "
    "COALESCE(v.judged_at,'') AS judged_at, "
    "(SELECT t2.transcribed_at FROM transcripts t2 WHERE t2.join_key=c.join_key "
    " AND c.join_key<>'' LIMIT 1) AS tx_at, "
    "COALESCE(v.outcome_tf,'') AS otf, COALESCE(v.agent,'') AS in_agent, v._vid AS vmatch, "
    "COALESCE(v.status,'') AS vstatus, COALESCE(v.error,'') AS verror, "
    "COALESCE(v.doctor_flag,'') AS doctor_flag, COALESCE(v.doctor_note,'') AS doctor_note, "
    "COALESCE(v.final_outcome,'') AS final_outcome, COALESCE(v.conduct_note,'') AS conduct_note, "
    "COALESCE(p.last_visit,'') AS last_visit, COALESCE(p.patient_uid,'') AS patient_uid, "
    "COALESCE(NULLIF(p.clinic_id,''), v.clinic_id, '') AS clinic_id, "
    "COALESCE(NULLIF(v.recording_link,''), "
    " (SELECT recording_link FROM recordings rr WHERE rr.myoperator_filename=c.recording_filename LIMIT 1), '') AS rec_link, "
    "(SELECT text FROM transcripts t WHERE t.join_key=c.join_key AND c.join_key<>'' LIMIT 1) AS tx_text, "
    "COALESCE(v.flag_postop,'') AS f_postop, COALESCE(v.flag_complaint,'') AS f_complaint, "
    "COALESCE(v.flag_urgent,'') AS f_urgent, COALESCE(v.flag_surgery,'') AS f_surgery, "
    "COALESCE(v.flag_clinical,'') AS f_clinical, COALESCE(v.flag_conduct,'') AS f_conduct, "
    "(SELECT o.agent FROM outbound o WHERE o.phone10=" + _DPHONE +
    " AND o.date=substr(c.ended_at_ist,1,10) LIMIT 1) AS out_agent, "
    + _AGENT_EXPR + " AS agent_res "
)

_LOG_LIMIT = 500


def _truthy(val):
    return (val or "").strip() not in _FALSEY


def _parse_any_ts(s):
    """Best-effort timestamp parse (rev5). Strips tz (F-72 kin), tries the formats
    the pipeline actually writes. Returns datetime or None -- NEVER raises."""
    from datetime import datetime as _dt
    s = (s or "").strip()
    if not s:
        return None
    if len(s) > 6 and (s[-6] in "+-") and s[-3] == ":":   # ...+05:30
        s = s[:-6]
    s = s.replace("T", " ").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return _dt.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _lag_min(a, b):
    """Whole minutes from a->b, or None. Negative clamped to 0 (clock skew)."""
    if a is None or b is None:
        return None
    d = (b - a).total_seconds() / 60.0
    return int(d) if d >= 0 else 0


def _hhmm(ts):
    dt = _parse_any_ts(ts)
    return dt.strftime("%H:%M") if dt else (ts or "")


def _log_row(r):
    direction = r["direction"] or "?"
    agent = (r["agent_res"] or "")   # rev4: call_agent > verdict > outbound
    flags = [_FLAG_LABEL[k] for k, col in
             (("postop", "f_postop"), ("complaint", "f_complaint"), ("urgent", "f_urgent"),
              ("surgery", "f_surgery"), ("clinical", "f_clinical"), ("conduct", "f_conduct"))
             if _truthy(r[col])]
    date, time = _split_dt(r["ended_at_ist"])
    answered = r["answered"]
    state = "Answered" if answered == 1 else ("Missed" if answered == 0 else "?")
    number = r["phone_disp"] or r["vnum"] or ""
    has_jk = bool((r["join_key"] or "").strip())
    tx_text = (r["tx_text"] or "").strip()
    # --- AI-verdict state (fixes the false "pending" flood) ---
    ai = (r["ai_outcome"] or "").strip()
    vstatus = (r["vstatus"] or "").strip().lower()
    verror = (r["verror"] or "").strip()
    has_verdict = r["vmatch"] is not None
    if ai:
        ai_state, ai_text = "ok", ai
    elif has_verdict and (verror or vstatus in ("error", "failed", "err")):
        ai_state, ai_text = "error", (verror or "error")
    elif has_verdict:
        ai_state, ai_text = "noout", ((r["verdict"] or "").strip() or "no outcome")
    elif has_jk:
        # rev5 Item 3: name WHY it is pending, per row
        ai_state = "pending"
        ai_text = "judge pending" if (r["tx_at"] or "").strip() else "awaiting transcript"
    else:
        ai_state, ai_text = "na", ""
    # --- rev5 Item 3: pipeline times + lags for this row ---
    t_call = _parse_any_ts(r["ended_at_ist"])
    t_tx = _parse_any_ts(r["tx_at"])
    t_j = _parse_any_ts(r["judged_at"])
    lag_tx = _lag_min(t_call, t_tx)
    lag_judge = _lag_min(t_call, t_j)
    # --- your review (doctor) ---
    fo = (r["final_outcome"] or "").strip(); dn = (r["doctor_note"] or "").strip()
    df = (r["doctor_flag"] or "").strip()
    reviewed = bool(fo or dn or df)
    review_text = fo or df or ("noted" if dn else "")
    return {
        "date": date, "time": time, "direction": direction, "state": state,
        "phone10": number, "name": r["name"] or "",
        "diagnosis": r["diagnosis"] or "", "duration": r["total_duration"] or "",
        "dur_h": _dur_h(r["total_duration"]),
        "age": (r["age"] or "").strip(), "gender": (r["gender"] or "").strip(),
        "agesex": "/".join(x for x in ((r["age"] or "").strip(),
                                       (r["gender"] or "").strip()[:1].upper()) if x),
        "agent": agent, "last_visit": r["last_visit"] or "",
        "clinic_id": r["clinic_id"] or "", "patient_uid": r["patient_uid"] or "",
        "claimed": r["claimed"] or "", "not_filed": (r["not_filed"] == 1),
        "ai_outcome": ai, "verdict": r["verdict"] or "", "otf": r["otf"] or "",
        "ai_state": ai_state, "ai_text": ai_text,
        "ai_reason": (r["ai_reason"] or "").strip(), "evidence": (r["evidence"] or "").strip(),
        "tx_at": _hhmm(r["tx_at"]), "judged_at": _hhmm(r["judged_at"]),
        "lag_tx": lag_tx, "lag_judge": lag_judge,
        "doctor_note": dn, "reviewed": reviewed, "review_text": review_text,
        "conduct_note": (r["conduct_note"] or "").strip(),
        "has_jk": has_jk, "has_verdict": has_verdict,
        "in_master": r["pid"] is not None,
        "flags": flags, "rec_link": r["rec_link"] or "",
        "tx_text": tx_text, "has_tx": bool(tx_text), "join_key": r["join_key"] or "",
    }


def _overlay_reviews(rows, disp, sb):
    """W2: my persistent review + open-send-back state onto rendered rows.
    My disposition WINS over any sheet-side doctor columns."""
    for r in rows:
        jk = r.get("join_key") or ""
        d = disp.get(jk)
        if d:
            r["reviewed"] = True
            r["review_text"] = d["final_outcome"] or "reviewed"
            r["my_note"] = d["note"]
            r["my_review_at"] = d["at"]
        else:
            r["my_note"] = ""; r["my_review_at"] = ""
        s = sb.get(jk)
        r["sent_back"] = bool(s)
        r["sb_reason"] = s["reason"] if s else ""
        r["self_review"] = (r.get("agent") or "").startswith("Dr Manoj")
    return rows


def _group_by_day(rows):
    """rows already ordered newest-first -> ordered [(date, [rows])], newest day first."""
    out, idx = [], {}
    for r in rows:
        d = r["date"] or "(no date)"
        if d not in idx:
            idx[d] = len(out); out.append((d, []))
        out[idx[d]][1].append(r)
    return out


def _log_where(f, exclude=None):
    w, p = [], []
    if f["direction"] and exclude != "direction":
        w.append("c.direction=?"); p.append(f["direction"])
    if f["answered"] and exclude != "answered":
        if f["answered"] == "answered":
            w.append("c.answered=1")
        elif f["answered"] == "missed":
            w.append("c.answered=0")
        elif f["answered"] == "netmissed":
            spam = _spam_phones()
            cl = ("c.direction='In' AND c.answered=0 AND c.phone10 IN "
                  "(SELECT phone10 FROM conversations WHERE net_missed_open=1)")
            if spam:
                cl += " AND c.phone10 NOT IN (%s)" % ",".join(["?"] * len(spam))
                p.extend(sorted(spam))
            w.append(cl)
    if f["agent"] and exclude != "agent":
        w.append(_AGENT_EXPR + "=?"); p.append(f["agent"])
    if f["flag"] and exclude != "flag" and f["flag"] in _FLAG_COLS:
        col = "v." + _FLAG_COLS[f["flag"]]
        w.append("TRIM(COALESCE(%s,'')) NOT IN (%s)" % (col, ",".join(["?"] * len(_FALSEY))))
        p.extend(_FALSEY)
    if f["frm"] and exclude != "date":
        w.append("substr(c.ended_at_ist,1,10)>=?"); p.append(f["frm"])
    if f["to"] and exclude != "date":
        w.append("substr(c.ended_at_ist,1,10)<=?"); p.append(f["to"])
    if f["q"] and exclude != "q":
        w.append("(" + _DPHONE + " LIKE ? OR COALESCE(v.patient_name,'') LIKE ? "
                 "OR COALESCE(p.name,'') LIKE ? OR COALESCE(p.diagnosis,'') LIKE ?)")
        like = "%" + f["q"] + "%"; p.extend([like, like, like, like])
    return (" AND ".join(w) if w else "1=1"), p


def _query_log(conn, f, limit=_LOG_LIMIT):
    where, params = _log_where(f)
    sql = _LOG_COLS + _LOG_FROM + "WHERE " + where + " ORDER BY c.ended_at_ist DESC"
    if limit:
        sql += " LIMIT %d" % (limit + 1)
    rows = [_log_row(r) for r in conn.execute(sql, params)]
    more = False
    if limit and len(rows) > limit:
        more = True; rows = rows[:limit]
    return rows, more


def _count(conn, where, params):
    return conn.execute("SELECT COUNT(*) " + _LOG_FROM + "WHERE " + where, params).fetchone()[0]


def _agent_names(conn):
    """The agent dimension = the REAL attribution names present in the data
    (call_agent + verdicts + outbound), not the short roster."""
    names = set()
    for (a,) in conn.execute("SELECT DISTINCT agent FROM verdicts WHERE TRIM(COALESCE(agent,''))<>''"):
        names.add(a.strip())
    for (a,) in conn.execute("SELECT DISTINCT agent FROM outbound WHERE TRIM(COALESCE(agent,''))<>''"):
        names.add(a.strip())
    for (a,) in conn.execute("SELECT DISTINCT agent FROM call_agent WHERE TRIM(COALESCE(agent,''))<>''"):
        names.add(a.strip())
    return sorted(names, key=lambda s: s.lower())


def _facets(conn, f):
    fac = {"direction": {}, "answered": {}, "agent": {}}
    for val in ("In", "Out"):
        w, p = _log_where(f, exclude="direction")
        fac["direction"][val] = _count(conn, w + " AND c.direction=?", p + [val])
    base_w, base_p = _log_where(f, exclude="answered")
    fac["answered"]["answered"] = _count(conn, base_w + " AND c.answered=1", base_p)
    fac["answered"]["missed"] = _count(conn, base_w + " AND c.answered=0", base_p)
    spam = _spam_phones()
    nm_cl = (" AND c.direction='In' AND c.answered=0 AND c.phone10 IN "
             "(SELECT phone10 FROM conversations WHERE net_missed_open=1)")
    nm_p = list(base_p)
    if spam:
        nm_cl += " AND c.phone10 NOT IN (%s)" % ",".join(["?"] * len(spam))
        nm_p.extend(sorted(spam))
    fac["answered"]["netmissed"] = _count(conn, base_w + nm_cl, nm_p)
    aw, ap = _log_where(f, exclude="agent")
    for nm in _agent_names(conn):
        fac["agent"][nm] = _count(conn, aw + " AND " + _AGENT_EXPR + "=?", ap + [nm])
    return fac


def _query_conversations(conn, f):
    w, p = [], []
    if f["q"]:
        w.append("(cv.phone10 LIKE ? OR COALESCE(p.name,'') LIKE ? OR COALESCE(p.diagnosis,'') LIKE ?)")
        like = "%" + f["q"] + "%"; p.extend([like, like, like])
    if f["frm"]:
        w.append("substr(cv.last_ts,1,10)>=?"); p.append(f["frm"])
    if f["to"]:
        w.append("substr(cv.last_ts,1,10)<=?"); p.append(f["to"])
    where = (" WHERE " + " AND ".join(w)) if w else ""
    sql = ("SELECT cv.phone10, cv.attempts, cv.miss_attempts, cv.any_connected, "
           "cv.net_missed_open, cv.first_ts, cv.last_ts, cv.last_direction, "
           "cv.last_status, cv.last_agent, COALESCE(p.name,'') AS name, "
           "COALESCE(p.diagnosis,'') AS diagnosis, "
           "COALESCE(p.age,'') AS age, COALESCE(p.gender,'') AS gender, "
           "COALESCE(p.clinic_id,'') AS clinic_id, "
           "COALESCE(p.last_visit,'') AS last_visit, "
           "p._pid AS pid FROM conversations cv "
           "LEFT JOIN " + _DP + " p ON p.phone10=cv.phone10 AND cv.phone10<>'' "
           + where + " ORDER BY cv.net_missed_open DESC, cv.last_ts DESC LIMIT 400")
    convs = []
    for r in conn.execute(sql, p):
        legs = [_log_row(lr) for lr in conn.execute(
            _LOG_COLS + _LOG_FROM + "WHERE c.phone10=? ORDER BY c.ended_at_ist ASC", [r["phone10"]])]
        d0, t0 = _split_dt(r["first_ts"]); d1, t1 = _split_dt(r["last_ts"])
        convs.append({
            "phone10": r["phone10"] or "", "name": r["name"] or "",
            "diagnosis": r["diagnosis"] or "",
            "agesex": "/".join(x for x in ((r["age"] or "").strip(),
                                           (r["gender"] or "").strip()[:1].upper()) if x),
            "in_master": r["pid"] is not None,
            "clinic_id": r["clinic_id"] or "", "last_visit": r["last_visit"] or "",
            "attempts": r["attempts"],
            "miss_attempts": r["miss_attempts"], "any_connected": r["any_connected"],
            "net_open": r["net_missed_open"], "first_ts": (d0 + " " + t0).strip(),
            "last_ts": (d1 + " " + t1).strip(), "last_agent": r["last_agent"] or "",
            "legs": legs})
    return convs


def _query_staff(conn, f):
    dw, dp = "", []
    if f["frm"]:
        dw += " AND substr(c.ended_at_ist,1,10)>=?"; dp.append(f["frm"])
    if f["to"]:
        dw += " AND substr(c.ended_at_ist,1,10)<=?"; dp.append(f["to"])
    ow, op = "", []
    if f["frm"]:
        ow += " AND o.date>=?"; op.append(f["frm"])
    if f["to"]:
        ow += " AND o.date<=?"; op.append(f["to"])
    rows = {}

    def slot(name):
        return rows.setdefault(name, {"agent": name, "in_handled": 0, "out_attempts": 0,
                                      "not_filed": 0, "vtrue": 0, "vfalse": 0, "flags": 0})

    for nm in _agent_names(conn):
        slot(nm)
    for r in conn.execute("SELECT " + _AGENT_EXPR + " AS a, COUNT(*) n FROM " + _DV + " v "
                          "JOIN calls c ON c.join_key=v.join_key AND v.join_key<>'' "
                          "WHERE c.direction='In' AND c.answered=1" + dw + " GROUP BY " + _AGENT_EXPR, dp):
        if r["a"]:
            slot(r["a"].strip())["in_handled"] = r["n"]
    for r in conn.execute("SELECT " + _AGENT_EXPR + " AS a, COUNT(*) n FROM " + _DV + " v "
                          "JOIN calls c ON c.join_key=v.join_key AND v.join_key<>'' "
                          "WHERE c.direction='In' AND c.answered=1 AND COALESCE(v.not_filed,0)=1"
                          + dw + " GROUP BY " + _AGENT_EXPR, dp):
        if r["a"]:
            slot(r["a"].strip())["not_filed"] = r["n"]
    for r in conn.execute("SELECT agent AS a, COUNT(*) n FROM outbound o WHERE 1=1" + ow +
                          " GROUP BY agent", op):
        if r["a"]:
            slot(r["a"].strip())["out_attempts"] = r["n"]
    for r in conn.execute(
            "SELECT " + _AGENT_EXPR + " AS a, "
            "SUM(CASE WHEN UPPER(TRIM(COALESCE(v.outcome_tf,'')))='TRUE' THEN 1 ELSE 0 END) t, "
            "SUM(CASE WHEN UPPER(TRIM(COALESCE(v.outcome_tf,'')))='FALSE' THEN 1 ELSE 0 END) f "
            "FROM " + _DV + " v JOIN calls c ON c.join_key=v.join_key AND v.join_key<>'' "
            "WHERE c.direction='In'" + dw + " GROUP BY " + _AGENT_EXPR, dp):
        if r["a"]:
            s = slot(r["a"].strip()); s["vtrue"] = r["t"] or 0; s["vfalse"] = r["f"] or 0
    flagsql = " OR ".join("TRIM(COALESCE(v.%s,'')) NOT IN (%s)"
                          % (col, ",".join(["?"] * len(_FALSEY))) for col in _FLAG_COLS.values())
    fp = list(_FALSEY) * len(_FLAG_COLS)
    for r in conn.execute("SELECT " + _AGENT_EXPR + " AS a, COUNT(*) n FROM " + _DV + " v "
                          "JOIN calls c ON c.join_key=v.join_key AND v.join_key<>'' "
                          "WHERE c.direction='In' AND (" + flagsql + ")" + dw +
                          " GROUP BY " + _AGENT_EXPR, fp + dp):
        if r["a"]:
            slot(r["a"].strip())["flags"] = r["n"]
    return sorted(rows.values(), key=lambda s: (s["in_handled"] + s["out_attempts"]), reverse=True)


def _query_leads(conn, f):
    w = ["c.direction='In'", _DPHONE + "<>''",
         _DPHONE + " NOT IN (SELECT phone10 FROM patients WHERE phone10<>'')"]
    p = []
    if f["frm"]:
        w.append("substr(c.ended_at_ist,1,10)>=?"); p.append(f["frm"])
    if f["to"]:
        w.append("substr(c.ended_at_ist,1,10)<=?"); p.append(f["to"])
    if f["q"]:
        w.append(_DPHONE + " LIKE ?"); p.append("%" + f["q"] + "%")
    sql = ("SELECT " + _DPHONE + " AS ph, MIN(c.ended_at_ist) first_seen, "
           "MAX(c.ended_at_ist) last_seen, COUNT(*) attempts, MAX(c.answered) any_answered "
           "FROM calls c WHERE " + " AND ".join(w) +
           " GROUP BY ph ORDER BY last_seen DESC LIMIT 400")
    leads = []
    for r in conn.execute(sql, p):
        ph = r["ph"]
        d0, t0 = _split_dt(r["first_seen"]); d1, t1 = _split_dt(r["last_seen"])
        legs = [_log_row(lr) for lr in conn.execute(
            _LOG_COLS + _LOG_FROM + "WHERE " + _DPHONE + "=? ORDER BY c.ended_at_ist ASC", [ph])]
        last_agent = ""
        for lg in reversed(legs):
            if lg["agent"]:
                last_agent = lg["agent"]; break
        leads.append({"phone10": ph, "first_seen": (d0 + " " + t0).strip(),
                      "last_seen": (d1 + " " + t1).strip(), "attempts": r["attempts"],
                      "answered": (r["any_answered"] == 1), "last_agent": last_agent,
                      "legs": legs})
    return leads


# ---- S171 v3: GAS outcome vocabularies (verbatim, GAS_Outcome_Vocabularies_v1) ----
HI_OUTCOME = {
    "coming": "\u092e\u0930\u0940\u091c\u093c \u0906 \u0930\u0939\u0947 \u0939\u0948\u0902",
    "will_come": "\u092e\u0930\u0940\u091c\u093c \u0906 \u0930\u0939\u0947 \u0939\u0948\u0902",
    "k_coming": "\u092e\u0930\u0940\u091c\u093c \u0906 \u0930\u0939\u0947 \u0939\u0948\u0902",
    "not_coming": "\u0928\u0939\u0940\u0902 \u0906\u090f\u0901\u0917\u0947",
    "k_not_coming": "\u0928\u0939\u0940\u0902 \u0906\u090f\u0901\u0917\u0947",
    "call_again": "\u092c\u093e\u0924 \u0939\u0941\u0908 \u2014 \u092b\u093f\u0930 call \u0915\u0930\u0928\u093e",
    "k_call_again": "\u092c\u093e\u0924 \u0939\u0941\u0908 \u2014 \u092b\u093f\u0930 call \u0915\u0930\u0928\u093e",
    "needs_callback": "\u092c\u093e\u0924 \u0939\u0941\u0908 \u2014 \u092b\u093f\u0930 call \u0915\u0930\u0928\u093e",
    "no_answer": "\u092c\u093e\u0924 \u0928\u0939\u0940\u0902 \u0939\u094b \u092a\u093e\u0908",
    "no_contact": "\u092c\u093e\u0924 \u0928\u0939\u0940\u0902 \u0939\u094b \u092a\u093e\u0908",
    "problem": "\u0921\u0949\u0915\u094d\u091f\u0930 \u0915\u094b \u0926\u093f\u0916\u093e\u0928\u093e \u0939\u0948",
    "escalated": "\u0921\u0949\u0915\u094d\u091f\u0930 \u0915\u094b \u0926\u093f\u0916\u093e\u0928\u093e \u0939\u0948",
    "to_doctor": "\u0921\u0949\u0915\u094d\u091f\u0930 \u0915\u094b \u0926\u093f\u0916\u093e\u0928\u093e \u0939\u0948",
    "appointment_booked": "Appointment booked",
    "enquiry_only": "\u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u0926\u0947 \u0926\u0940",
    "info_given_will_act": "\u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u0926\u0947 \u0926\u0940",
    "no_action": "\u0915\u093e\u092e \u0915\u093e \u0928\u0939\u0940\u0902",
}


def _hi_out(code):
    """Outcome code -> the staff's own button word (fallback: code as-is)."""
    c = (code or "").strip().lower()
    return HI_OUTCOME.get(c, code or "")


def _rl_sig(jk):
    """Short HMAC for the staff recording-only link /portal/rl/<jk>/<sig>."""
    import hmac as _hmac, hashlib as _hl
    key = (app.secret_key or "portal").encode() if isinstance(app.secret_key, str) else (app.secret_key or b"portal")
    return _hmac.new(key, ("rl:" + (jk or "")).encode(), _hl.sha256).hexdigest()[:16]


def _ns_tries(conn, rows):
    """Attach the due-day calling efforts to each no-show row.
    tries = [{t,agent,ok}] for calls on/after the due date; tries_h = compact line."""
    phones = sorted({(r.get("phone10") or "").strip() for r in rows
                     if (r.get("phone10") or "").strip()})
    if not phones:
        return
    qm = ",".join(["?"] * len(phones))
    by = {}
    try:
        for ph, ts, ans, ag in conn.execute(
                "SELECT c.phone10, c.ended_at_ist, c.answered, COALESCE(ca.agent,'') "
                "FROM calls c LEFT JOIN call_agent ca ON ca.join_key=c.join_key "
                "AND c.join_key<>'' "
                "WHERE c.direction='Out' AND c.phone10 IN (%s) "
                "ORDER BY c.ended_at_ist" % qm, phones):
            by.setdefault(ph, []).append((ts or "", int(ans or 0), (ag or "").strip()))
    except Exception:
        return
    for r in rows:
        due = (str(r.get("due_date") or ""))[:10]
        out = []
        for ts, ans, ag in by.get((r.get("phone10") or "").strip(), []):
            if due and ts[:10] >= due:
                out.append({"t": ts[11:16], "d": ts[:10], "agent": ag or "\u2014",
                            "ok": bool(ans)})
        r["tries"] = out
        r["tries_h"] = " \u00b7 ".join(
            "%s %s %s" % (t["t"], (t["agent"].split()[0] if t["agent"] != "\u2014" else "?"),
                          "\u2713" if t["ok"] else "\u2717") for t in out[:4])


def _staff_week(conn, disp, end_day=None):
    """agents x last-7-days matrix + the per-agent per-day row lists.
    Returns (days [iso newest-first], matrix {agent:{iso:{...}}}, rows_by {(agent,iso):[rows]})."""
    end = end_day or datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        d0 = datetime.date.fromisoformat(end)
    except Exception:
        d0 = datetime.date.today()
    days = [(d0 - datetime.timedelta(days=i)).isoformat() for i in range(7)]
    rows = [_log_row(r) for r in conn.execute(
        _LOG_COLS + _LOG_FROM +
        "WHERE substr(c.ended_at_ist,1,10)>=? AND substr(c.ended_at_ist,1,10)<=? "
        "ORDER BY c.ended_at_ist DESC", (days[-1], days[0]))]
    matrix, rows_by = {}, {}
    for r in rows:
        ag = (r.get("agent") or "").strip()
        if not ag:
            continue
        iso = (r.get("date") or "")[:10]
        if iso not in days:
            continue
        m = matrix.setdefault(ag, {}).setdefault(iso, dict(
            total=0, answered=0, filed=0, mismatch=0, flags=0, myrev=0))
        m["total"] += 1
        if r.get("state") == "Answered":
            m["answered"] += 1
        if (r.get("claimed") or "").strip():
            m["filed"] += 1
        if (r.get("verdict") or "").strip() == "Mismatch":
            m["mismatch"] += 1
        if r.get("flags"):
            m["flags"] += 1
        if r.get("join_key") in disp:
            m["myrev"] += 1
        rows_by.setdefault((ag, iso), []).append(r)
    for ag, dd in matrix.items():
        for iso, m in dd.items():
            m["pct"] = int(round(100.0 * m["filed"] / m["total"])) if m["total"] else 0
    return days, matrix, rows_by


def _coach_data(conn, day, disp, sbm):
    """Per-agent coaching sheet data for one day: stats, lessons, not-filed."""
    rows = [_log_row(r) for r in conn.execute(
        _LOG_COLS + _LOG_FROM +
        "WHERE substr(c.ended_at_ist,1,10)=? ORDER BY c.ended_at_ist", (day,))]
    _overlay_reviews(rows, disp, sbm)
    agents = {}
    for r in rows:
        ag = (r.get("agent") or "").strip()
        if not ag:
            continue
        a = agents.setdefault(ag, dict(agent=ag, total=0, answered=0, filed=0,
                                       lessons=[], notfiled=[]))
        a["total"] += 1
        if r.get("state") == "Answered":
            a["answered"] += 1
        claimed = (r.get("claimed") or "").strip()
        if claimed:
            a["filed"] += 1
        correct = (r.get("review_text") or "").strip() or (r.get("ai_outcome") or "").strip()
        mism = ((r.get("verdict") or "").strip() == "Mismatch") or (
            (r.get("review_text") or "").strip() and claimed and
            _hi_out(r["review_text"]) != _hi_out(claimed))
        if claimed and correct and mism and r.get("join_key"):
            a["lessons"].append(dict(
                time=r.get("time") or "", name=(r.get("name") or "").strip(),
                phone=r.get("phone10") or "",
                filed_h=_hi_out(claimed), correct_h=_hi_out(correct),
                why=(r.get("doctor_note") or "").strip() or (r.get("ai_reason") or "").strip(),
                quote=(r.get("evidence") or "").strip(),
                jk=r["join_key"], sig=_rl_sig(r["join_key"])))
        if r.get("not_filed") and r.get("state") == "Answered":
            a["notfiled"].append("%s %s" % (r.get("time") or "",
                                            (r.get("name") or r.get("phone10") or "").strip()))
    for a in agents.values():
        a["pct"] = int(round(100.0 * a["filed"] / a["total"])) if a["total"] else 0
    return sorted(agents.values(), key=lambda x: -x["total"])


def _dur_h(sec):
    """seconds -> m:ss for the row player."""
    try:
        s = int(str(sec).strip() or 0)
    except Exception:
        return ""
    return "%d:%02d" % (s // 60, s % 60) if s > 0 else ""


def _date_label(iso):
    """YYYY-MM-DD -> '12 Aug (Tue)'; fail-soft to raw."""
    try:
        d = datetime.datetime.strptime((iso or "")[:10], "%Y-%m-%d")
        return d.strftime("%d %b (%a)")
    except Exception:
        return iso or "\u2014"


def _group_by_iso(rows, key):
    """Group dict-rows by ISO date of rows[key][:10], newest first.
    Returns [(label, iso, rows)]."""
    groups = {}
    for r in rows:
        iso = (str(r.get(key) or ""))[:10]
        groups.setdefault(iso, []).append(r)
    out = []
    for iso in sorted(groups, reverse=True):
        out.append((_date_label(iso), iso, groups[iso]))
    return out


ROW_SHARED = """
{% macro detail(r) %}
<div class="detail">
  <div class="dname"><b>{{ r.name or 'Unknown caller' }}</b>{% if r.agesex %} \u00b7 {{ r.agesex }}{% endif %}{% if r.diagnosis %} \u00b7 <span class="dx">{{ r.diagnosis }}</span>{% elif not r.in_master %} \u00b7 <span class="ctx miss">not in patient master</span>{% else %} \u00b7 <span class="ctx" style="opacity:.75">no dx in master</span>{% endif %}</div>
  <div class="dmeta">
    <span class="mono">{{ r.phone10 or '\u2014' }}</span>
    {% if r.clinic_id %}\u00b7 ID {{ r.clinic_id }}{% endif %}
    {% if r.last_visit %}\u00b7 last visit {{ r.last_visit }}{% endif %}
    \u00b7 <span class="dir {{ r.direction }}">{{ r.direction }}</span> <span class="st {{ r.state }}">{{ r.state }}</span>
    {% if r.duration %}\u00b7 {{ r.duration }}s{% endif %}
    \u00b7 staff: <b>{{ r.agent or '\u2014' }}</b>
  </div>
  <div class="drow">
    <span class="dlab">Outcome</span>
    {% if r.not_filed %}<span class="amber">NOT FILED</span>{% else %}{{ r.claimed or '\u2014' }}{% endif %}
    <span class="dlab">AI verdict</span>
    {% if r.ai_state=='ok' %}<span class="pillv U">{{ r.ai_text }}</span>
    {% elif r.ai_state=='error' %}<span class="pillv F">error</span> <span class="muted">{{ r.ai_text }}</span>
    {% elif r.ai_state=='noout' %}<span class="pillv mut">{{ r.ai_text }}</span>
    {% elif r.ai_state=='pending' %}<span class="muted">{{ r.ai_text }}</span>
    {% else %}\u2014{% endif %}
    <span class="dlab">Your review</span>
    {% if r.reviewed %}<span class="pillv T">{{ r.review_text or 'reviewed' }}</span>{% if r.my_review_at %}<span class="muted sm">{{ r.my_review_at }}</span>{% endif %}{% else %}<span class="muted">not reviewed</span>{% endif %}
    {% if r.sent_back %}<span class="sbbadge">SENT BACK</span>{% endif %}
    {% if r.self_review %}<span class="warnbadge">\u26A0 self-review (own call)</span>{% endif %}
  </div>
  {% if r.ai_reason or r.evidence %}<div class="drow"><span class="dlab">AI reason</span><span>{{ r.ai_reason or '\u2014' }}</span>{% if r.evidence %}<span class="dlab">Evidence</span><span class="evq">&ldquo;{{ r.evidence }}&rdquo;</span>{% endif %}</div>{% endif %}
  {% if r.tx_at or r.judged_at %}<div class="drow"><span class="dlab">Pipeline</span><span class="muted sm">{% if r.tx_at %}transcribed {{ r.tx_at }}{% if r.lag_tx is not none %} (+{{ r.lag_tx }}m){% endif %}{% endif %}{% if r.judged_at %} \u00b7 judged {{ r.judged_at }}{% if r.lag_judge is not none %} (+{{ r.lag_judge }}m after call){% endif %}{% endif %}</span></div>{% endif %}
  {% if r.flags %}<div class="drow"><span class="dlab">Flags</span>{% for fl in r.flags %}<span class="flag">{{ fl }}</span>{% endfor %}</div>{% endif %}
  {% if r.doctor_note %}<div class="drow"><span class="dlab">My note</span><span class="muted">{{ r.doctor_note }}</span></div>{% endif %}
  <div class="drow">
    {% if r.join_key and r.rec_link %}
      <audio class="recplayer" controls preload="none" src="/portal/rec/{{ r.join_key }}"></audio>
      <a class="lnk sm" href="{{ r.rec_link }}" target="_blank" rel="noopener">Drive</a>
    {% elif r.rec_link %}<a class="lnk" href="{{ r.rec_link }}" target="_blank" rel="noopener">\u25B6 recording</a>
    {% elif r.state=='Answered' %}<span class="muted">no recording link</span>{% endif %}
  </div>
  {% if r.tx_text %}<div class="txbox"><b>Transcript</b><br>{{ r.tx_text }}</div>{% endif %}
  {% if r.join_key %}
  <div class="actrow">
    <form method="POST" action="/portal/console/review" class="actform">
      <input type="hidden" name="join_key" value="{{ r.join_key }}">
      <input type="hidden" name="ret" value="{{ full_qs }}">
      <select name="final_outcome">
        <option value="">\u2014 my verdict \u2014</option>
        {% for v in vocab %}<option value="{{ v }}" {{ 'selected' if r.review_text==v else '' }}>{{ v }}</option>{% endfor %}
      </select>
      <input type="text" name="note" placeholder="note (optional)" value="{{ r.my_note }}">
      <button class="btn sm" type="submit">Save review</button>
    </form>
    <form method="POST" action="/portal/console/sendback" class="actform">
      <input type="hidden" name="join_key" value="{{ r.join_key }}">
      <input type="hidden" name="phone10" value="{{ r.phone10 }}">
      <input type="hidden" name="patient" value="{{ r.name }}">
      <input type="hidden" name="ret" value="{{ full_qs }}">
      <input type="text" name="reason" placeholder="reason for staff to call again" value="{{ r.sb_reason }}">
      <button class="btn sm alt" type="submit">{{ 'Update send-back' if r.sent_back else 'Send back to staff' }}</button>
    </form>
  </div>
  {% endif %}
</div>
{% endmacro %}

{% macro rowsummary(r) %}
  <span class="tc"><span class="t {{ 'inok' if r.direction=='In' and r.state=='Answered' else ('inmiss' if r.direction=='In' else ('outok' if r.state=='Answered' else 'outmiss')) }}"><svg class="ic"><use href="#i-{{ 'in' if r.direction=='In' else 'out' }}"/></svg>{{ r.time }}</span><span class="u">{{ 'answered' if r.state=='Answered' else 'missed' }}</span></span>
  <span class="rec">{% if r.join_key and r.rec_link %}<button type="button" class="pbtn" data-jk="{{ r.join_key }}" onclick="event.preventDefault();event.stopPropagation();rowPlay(this)"><svg class="ic s"><use href="#i-play"/></svg></button><span class="pdur">{{ r.dur_h }}</span>{% elif r.dur_h %}<span class="pdur">{{ r.dur_h }}</span>{% else %}<span class="pdur">\u2014</span>{% endif %}</span>
  <span class="idc">{% if r.name %}<span class="nm">{{ r.name }}</span><span class="sub">{{ r.phone10 }}{% if r.agesex %} \u00b7 {{ r.agesex }}{% endif %}{% if r.clinic_id %} \u00b7 <b>{{ r.clinic_id }}</b>{% endif %}</span>{% else %}<span class="nm mono">{{ r.phone10 or '\u2014' }}</span>{% if not r.in_master %}<span class="sub warn">not in patient master</span>{% endif %}{% endif %}</span>
  <span class="dxc">{% if r.diagnosis %}<span class="d1">{{ r.diagnosis }}</span>{% elif not r.in_master %}<span class="d1 mut">\u2014</span>{% else %}<span class="d1 mut">no dx in master</span>{% endif %}{% if r.last_visit %}<span class="d2">{{ r.last_visit }}</span>{% endif %}</span>
  <span class="agc">{{ r.agent or '\u2014' }}</span>
  <span class="sig"><span class="l1">{% for fl in r.flags %}<span class="chip flagc"><svg class="ic s"><use href="#i-flag"/></svg>{{ fl }}</span>{% endfor %}{% if r.verdict=='Mismatch' %}<span class="chip flagc">MISMATCH</span>{% endif %}{% if r.not_filed %}<span class="chip amberc">NOT FILED</span>{% endif %}{% if r.sent_back %}<span class="chip sbc">SENT BACK</span>{% endif %}{% if r.has_tx %}<span class="chip infoc">tx</span>{% endif %}</span><span class="l2">{% if r.ai_state=='ok' %}<b>AI:</b> {{ r.ai_text }}{% elif r.ai_state=='pending' %}<b>AI:</b> {{ r.ai_text }}{% endif %}{% if r.claimed %} \u00b7 <b>staff:</b> {{ hi_out(r.claimed) }}{% endif %}</span></span>
  <span class="act" onclick="event.preventDefault();event.stopPropagation()">{% if r.join_key %}<form method="POST" action="/portal/console/review" style="margin:0;flex:1;display:flex"><input type="hidden" name="join_key" value="{{ r.join_key }}"><input type="hidden" name="ret" value="{{ full_qs }}"><select name="final_outcome" onchange="this.form.submit()"><option value="">{{ r.review_text or 'review\u2026' }}</option>{% for v in vocab %}<option value="{{ v }}" {{ 'selected' if r.review_text==v else '' }}>{{ v }}</option>{% endfor %}</select></form><form method="POST" action="/portal/console/sendback" style="margin:0" onsubmit="var x=prompt('Reason for staff to call again', this.reason.value||''); if(!x) return false; this.reason.value=x; return true;"><input type="hidden" name="join_key" value="{{ r.join_key }}"><input type="hidden" name="phone10" value="{{ r.phone10 }}"><input type="hidden" name="patient" value="{{ r.name }}"><input type="hidden" name="ret" value="{{ full_qs }}"><input type="hidden" name="reason" value="{{ r.sb_reason }}"><button class="abtn sb2" type="submit" title="Send back to staff"><svg class="ic"><use href="#i-back"/></svg></button></form>{% endif %}{% if r.phone10 %}<a class="abtn callb" href="tel:+91{{ r.phone10 }}" title="Call {{ r.phone10 }}"><svg class="ic"><use href="#i-call"/></svg></a>{% endif %}</span>
{% endmacro %}
<style>
.cwrap{max-width:1780px}
.cbanner{border-radius:12px;padding:10px 14px;font-size:13px;margin:6px 0 14px}
.cbanner.warn{background:rgba(234,179,8,.14);color:#fde68a;border:1px solid rgba(234,179,8,.35)}
.cbanner.bad{background:rgba(239,68,68,.14);color:#fecaca;border:1px solid rgba(239,68,68,.4)}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 14px}
.tabs a{font-size:13px;font-weight:600;padding:8px 14px;border-radius:10px;text-decoration:none;color:var(--muted);border:1px solid var(--line);background:var(--card)}
.tabs a.on{color:#fff;border-color:var(--blue);background:rgba(59,130,246,.16)}
.filt{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:14px}
.filt .row{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end}
.filt label{display:flex;flex-direction:column;gap:4px;font-size:11px;color:var(--muted);font-weight:600}
.filt select,.filt input{background:#0b1b29;color:var(--ink);border:1px solid var(--line);border-radius:9px;padding:8px 10px;font-size:13px;min-width:120px}
.filt input[type=text]{min-width:190px}
.filt .btn{background:var(--blue);color:#fff;border:none;border-radius:9px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer}
.filt .clr{background:none;border:1px solid var(--line);color:var(--muted);border-radius:9px;padding:9px 14px;font-size:13px;text-decoration:none}
.csvbtn{margin-left:auto;background:none;border:1px solid var(--green);color:#86efac;border-radius:9px;padding:9px 14px;font-size:13px;text-decoration:none;font-weight:600}
.summ{font-size:12px;color:var(--muted);margin:2px 2px 10px}
.muted{color:var(--muted)} .sm{font-size:12px} .mono{font-variant-numeric:tabular-nums}
.lnk{color:#93c5fd;text-decoration:none;font-size:12.5px}.lnk:hover{text-decoration:underline}
.dir{font-weight:700;font-size:11px;padding:2px 7px;border-radius:6px}
.dir.In{background:rgba(59,130,246,.16);color:#93c5fd}.dir.Out{background:rgba(91,113,132,.22);color:#cbd5e1}
.st{font-size:11px;font-weight:600}.st.Answered{color:#86efac}.st.Missed{color:#fca5a5}
.amber{background:rgba(234,179,8,.16);color:#fde68a;font-size:11.5px;font-weight:700;padding:3px 9px;border-radius:10px}
.pillv{font-size:11.5px;font-weight:700;padding:3px 9px;border-radius:10px}
.pillv.T{background:rgba(34,197,94,.16);color:#86efac}.pillv.F{background:rgba(239,68,68,.16);color:#fca5a5}
.pillv.U{background:rgba(59,130,246,.16);color:#93c5fd}.pillv.mut{background:rgba(91,113,132,.25);color:#b8c7d6}
.flag{display:inline-block;font-size:11.5px;font-weight:700;padding:2px 8px;border-radius:10px;margin:1px 2px 1px 0;background:rgba(239,68,68,.14);color:#fca5a5}
.txmark{font-size:11px;font-weight:700;color:#86efac;background:rgba(34,197,94,.12);padding:2px 7px;border-radius:10px}
/* w8 universal grid */
.gwrap{--cols:78px 96px minmax(230px,1.5fr) minmax(160px,1.1fr) 96px minmax(200px,1.4fr) minmax(250px,320px);font-size:13.5px}
.hdr{display:grid;grid-template-columns:var(--cols);gap:10px;padding:8px 14px;font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--muted);background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:6}
details.callrow>summary,details.conv>summary{display:grid;grid-template-columns:var(--cols);gap:10px;align-items:center;padding:10px 14px}
details.callrow>summary:hover,details.conv>summary:hover{background:rgba(59,130,246,.06)}
.arr{font-size:15px;font-weight:800;margin-right:4px}
.arr.inok{color:#4ade80}.arr.inmiss{color:#f87171}.arr.out{color:#93c5fd}.arr.outmiss{color:#fca5a5}
.tcell{font-size:13.5px}
.pbtn{width:30px;height:30px;border-radius:50%;border:1px solid var(--line);background:rgba(59,130,246,.14);color:#bfdbfe;font-size:12px;cursor:pointer;line-height:1}
.pbtn:hover{background:rgba(59,130,246,.28)}
.pdur{font-size:12.5px;color:var(--muted);margin-left:5px;font-variant-numeric:tabular-nums}
.idc{display:flex;flex-direction:column;gap:1px;min-width:0}
.idc .nm{font-size:15px;font-weight:600;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.idc .sub{font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.idc .sub b{color:#93c5fd;font-weight:700}
.dxc{display:flex;flex-direction:column;gap:2px;min-width:0}
.dxc .d1{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dxc .d2{font-size:12px;color:var(--muted)}
.agc{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sigc{display:flex;gap:3px;flex-wrap:wrap;align-items:center;min-width:0}
.actc{display:flex;gap:5px;align-items:center}
.actc select{background:#0b1b29;color:var(--ink);border:1px solid var(--line);border-radius:9px;padding:6px 8px;font-size:13px;flex:1;min-width:0;max-width:170px}
.abtn{width:34px;height:32px;border-radius:8px;border:1px solid var(--line);background:rgba(234,179,8,.12);color:#fde68a;font-size:13px;cursor:pointer}
.abtn:hover{background:rgba(234,179,8,.25)}
.hot{background:rgba(249,115,22,.18);color:#fdba74;font-size:10px;font-weight:800;padding:2px 7px;border-radius:6px}
.mobile-scroll{overflow-x:auto}
.mobile-scroll .hdr,.mobile-scroll details.callrow>summary,.mobile-scroll details.conv>summary{min-width:880px}
.ctx{font-size:10.5px;color:var(--muted);background:rgba(91,113,132,.18);padding:1px 7px;border-radius:6px}
.ctx.dx{color:#c7d2fe;background:rgba(99,102,241,.14)}
.ctx.miss{color:#fca5a5;background:rgba(239,68,68,.12)}
.evq{color:#fde68a;font-style:italic}
.sbbadge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:6px;background:rgba(234,88,12,.2);color:#fdba74}
.warnbadge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:6px;background:rgba(239,68,68,.18);color:#fca5a5}
.actrow{display:flex;flex-wrap:wrap;gap:14px;margin-top:8px;padding-top:8px;border-top:1px dashed rgba(39,75,102,.6)}
.actform{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.actform select,.actform input[type=text]{background:#0b1b29;color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 8px;font-size:12px}
.actform input[type=text]{min-width:200px}
.btn.sm{padding:6px 12px;font-size:12px;background:var(--blue);color:#fff;border:none;border-radius:8px;cursor:pointer}
.btn.sm.alt{background:rgba(234,88,12,.85)}
.recplayer{height:32px;max-width:340px;vertical-align:middle}
.rowplayer{height:26px;max-width:230px}
/* day + call rows */
details.day{margin-bottom:8px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:rgba(22,50,74,.35)}
details.day>summary{cursor:pointer;list-style:none;padding:11px 14px;font-weight:700;font-size:13px;color:#fff;background:var(--card);display:flex;gap:12px;align-items:center}
details.day>summary::-webkit-details-marker{display:none}
details.day>summary .dcount{font-size:11px;color:var(--muted);font-weight:600;margin-left:auto}
details.callrow{border-top:1px solid rgba(39,75,102,.5)}

details.callrow>summary::-webkit-details-marker{display:none}
details.callrow[open]>summary{background:rgba(59,130,246,.07)}
details.callrow:hover>summary{background:rgba(59,130,246,.05)}
.numw{min-width:96px}.namew{min-width:120px}.agw{min-width:90px;color:var(--muted)}
/* conversation / lead groups */
details.conv{background:var(--card);border:1px solid var(--line);border-radius:11px;margin-bottom:8px}
details.conv[open]{border-color:var(--blue)}

details.conv>summary::-webkit-details-marker{display:none}
.netbadge{font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;background:rgba(239,68,68,.16);color:#fca5a5}
.okbadge{font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;background:rgba(34,197,94,.16);color:#86efac}
/* detail block (the one layout used everywhere) */
.detail{padding:10px 14px 12px;border-top:1px solid rgba(39,75,102,.5);background:rgba(11,27,41,.4)}
.dname{font-size:13.5px;margin-bottom:3px}.dname .dx{color:#c7d2fe;font-weight:600}
.dmeta{font-size:12px;color:var(--muted);margin-bottom:7px}
.drow{font-size:12.5px;margin:4px 0;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.dlab{font-size:9.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-left:8px}
.drow .dlab:first-child{margin-left:0}
.txbox{font-size:12px;color:#cbd5e1;background:#0b1b29;border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin:6px 0 2px;line-height:1.5}
table.log{width:100%;border-collapse:collapse;font-size:12.5px}
table.log th{text-align:left;color:var(--muted);font-weight:700;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;padding:8px;border-bottom:1px solid var(--line)}
table.log td{padding:8px;border-bottom:1px solid rgba(39,75,102,.5);vertical-align:top}
</style>
<style>
/* ===== V3 (S171): type scale + capped width + one grid, everywhere ===== */
:root{--f-lg:15px;--f-md:13px;--f-sm:12px;--f-xs:11px}
.cwrap{max-width:1480px}
.gwrap{--cols:74px 84px minmax(200px,1.2fr) minmax(140px,.9fr) 88px minmax(170px,1fr) 226px;
 background:rgba(11,27,41,.35);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.hdr{display:grid;grid-template-columns:var(--cols);gap:10px;padding:8px 16px;font-size:var(--f-xs);font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:6}
details.day>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px;padding:11px 16px;font-size:14px;font-weight:700;color:#fff;background:rgba(22,50,74,.8);border-bottom:1px solid var(--line)}
details.day>summary::-webkit-details-marker{display:none}
details.day>summary .chev{transition:transform .15s}
details.day[open]>summary .chev{transform:rotate(90deg)}
details.day>summary .dcount{margin-left:auto;font-size:var(--f-sm);color:var(--muted);font-weight:600}
details.callrow,details.conv{border-bottom:1px solid rgba(39,75,102,.45);border-top:none}
details.callrow>summary,details.conv>summary{cursor:pointer;list-style:none;display:grid;grid-template-columns:var(--cols);gap:10px;align-items:center;padding:10px 16px;min-height:54px}
details.callrow>summary::-webkit-details-marker,details.conv>summary::-webkit-details-marker{display:none}
details.callrow>summary:hover,details.conv>summary:hover{background:rgba(59,130,246,.06)}
details.callrow[open]>summary,details.conv[open]>summary{background:rgba(59,130,246,.09)}
.ic{width:15px;height:15px;vertical-align:-3px;fill:none;stroke:currentColor;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.ic.s{width:13px;height:13px}
.tc{display:flex;flex-direction:column;gap:2px}
.tc .t{font-size:var(--f-md);font-variant-numeric:tabular-nums;display:flex;align-items:center;gap:5px;color:#fff}
.tc .u{font-size:var(--f-xs);color:var(--muted)}
.t.inok{color:#4ade80}.t.inmiss{color:#f87171}.t.outok{color:#93c5fd}.t.outmiss{color:#fca5a5}
.rec{display:flex;align-items:center;gap:7px}
.pbtn{width:30px;height:30px;border-radius:50%;border:1px solid rgba(59,130,246,.5);background:rgba(59,130,246,.15);color:#bfdbfe;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex:none;font-size:0}
.pbtn:hover{background:rgba(59,130,246,.32)}
.pdur{font-size:var(--f-sm);color:var(--muted);font-variant-numeric:tabular-nums}
.idc{display:flex;flex-direction:column;gap:2px;min-width:0}
.idc .nm{font-size:var(--f-lg);font-weight:650;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.idc .sub{font-size:var(--f-sm);color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.idc .sub b{color:#93c5fd;font-weight:700}
.idc .sub.warn{color:#fca5a5}
.dxc{display:flex;flex-direction:column;gap:2px;min-width:0}
.dxc .d1{font-size:var(--f-md);color:#c7d2fe;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dxc .d1.mut{color:var(--muted)}
.dxc .d2{font-size:var(--f-xs);color:var(--muted)}
.agc{font-size:var(--f-md);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sig{display:flex;flex-direction:column;gap:4px;min-width:0}
.sig .l1{display:flex;gap:4px;flex-wrap:wrap}
.sig .l2{font-size:var(--f-sm);color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sig .l2 b{color:#c7d2fe;font-weight:600}
.chip{font-size:var(--f-xs);font-weight:700;padding:2.5px 8px;border-radius:7px;white-space:nowrap;display:inline-flex;align-items:center;gap:4px}
.chip.flagc{background:rgba(239,68,68,.15);color:#fca5a5}
.chip.amberc{background:rgba(234,179,8,.16);color:#fde68a}
.chip.okc{background:rgba(34,197,94,.15);color:#86efac}
.chip.infoc{background:rgba(59,130,246,.15);color:#93c5fd}
.chip.hotc{background:rgba(249,115,22,.2);color:#fdba74}
.chip.sbc{background:rgba(168,85,247,.18);color:#d8b4fe}
.act{display:flex;gap:6px;align-items:center}
.act select{background:#0b1b29;color:var(--ink);border:1px solid var(--line);border-radius:9px;padding:6px 8px;font-size:var(--f-sm);flex:1;min-width:0;max-width:118px}
.abtn{width:34px;height:32px;border-radius:9px;border:1px solid var(--line);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex:none;background:transparent;text-decoration:none}
.abtn.sb2{background:rgba(234,179,8,.1);color:#fde68a}.abtn.sb2:hover{background:rgba(234,179,8,.25)}
.abtn.callb{background:rgba(34,197,94,.1);color:#86efac}.abtn.callb:hover{background:rgba(34,197,94,.25)}
.xcard{background:rgba(11,27,41,.6);border-top:1px solid var(--line);padding:14px 16px 16px;display:grid;gap:10px}
.xrow{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;font-size:var(--f-md)}
.xlab{font-size:var(--f-xs);font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);min-width:86px}
.summ{font-size:var(--f-md)}
table.log{font-size:var(--f-md)}
table.log th{font-size:10.5px}
.detail{font-size:var(--f-md)}
.dname{font-size:var(--f-lg)}
.recplayer{height:36px;max-width:420px}
.mobile-scroll{overflow-x:visible}
@media(max-width:1000px){.gwrap{overflow-x:auto}.hdr,details.callrow>summary,details.conv>summary{min-width:980px}}
</style>
<svg style="display:none"><defs>
<symbol id="i-in" viewBox="0 0 24 24"><path d="M17 7 7 17M7 9v8h8"/></symbol>
<symbol id="i-out" viewBox="0 0 24 24"><path d="M7 17 17 7M9 7h8v8"/></symbol>
<symbol id="i-play" viewBox="0 0 24 24"><path d="M8 5.5v13l11-6.5z" fill="currentColor" stroke="none"/></symbol>
<symbol id="i-pause" viewBox="0 0 24 24"><path d="M8 5v14M16 5v14"/></symbol>
<symbol id="i-chev" viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></symbol>
<symbol id="i-back" viewBox="0 0 24 24"><path d="M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-3"/></symbol>
<symbol id="i-call" viewBox="0 0 24 24"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.8a2 2 0 0 1-.4 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.5 2.8.7a2 2 0 0 1 1.7 2z"/></symbol>
<symbol id="i-flag" viewBox="0 0 24 24"><path d="M4 15V4s1.5-1 4-1 4 2 7 2 4-1 4-1v11s-1.5 1-4 1-4-2-7-2-4 1-4 1zM4 22v-7"/></symbol>
<symbol id="i-copy" viewBox="0 0 24 24"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></symbol>
<symbol id="i-dl" viewBox="0 0 24 24"><path d="M12 3v12m0 0 5-5m-5 5-5-5M4 21h16"/></symbol>
<symbol id="i-print" viewBox="0 0 24 24"><path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2M6 14h12v8H6z"/></symbol>
</defs></svg>
<script>
var _pa=null,_pb=null;
function _pico(b,p){ b.innerHTML='<svg class="ic s"><use href="#i-'+(p?'pause':'play')+'"/></svg>'; }
function rowPlay(b){
  if(_pb===b&&_pa){ if(_pa.paused){_pa.play();_pico(b,1);}else{_pa.pause();_pico(b,0);} return; }
  if(_pa){ _pa.pause(); if(_pb)_pico(_pb,0); }
  _pa=new Audio("/portal/rec/"+b.dataset.jk); _pb=b;
  _pa.play().catch(function(){ b.textContent="\u26A0"; });
  _pico(b,1);
  _pa.onended=function(){ _pico(b,0); };
}
function copyText(id,btn){
  var el=document.getElementById(id); if(!el) return;
  var t=el.innerText||el.textContent;
  (navigator.clipboard&&navigator.clipboard.writeText(t)||Promise.reject()).then(
    function(){ if(btn){var o=btn.innerHTML;btn.innerHTML='\u2713 copied';setTimeout(function(){btn.innerHTML=o;},1500);} },
    function(){ var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);
      if(btn){var o=btn.innerHTML;btn.innerHTML='\u2713 copied';setTimeout(function(){btn.innerHTML=o;},1500);} });
}
</script>
"""

CONSOLE_HTML = PAGE_HEAD + ROW_SHARED + """

<div class="wrap cwrap">
  <div class="head">
    <h1>\U0001F4DE Call Console</h1>
    <span class="sub">D297 \u00b7 reads console.db \u00b7 doctor-only \u00b7 click any row to expand</span>
  </div>

  {% if not m.ok %}
    <div class="cbanner bad">Console data could not be read yet \u2014 the builder may not have run,
      or console.db is missing. Numbers are withheld, never shown as zero.</div>
    <div class="tabs"><a href="/portal">&larr; Back to portal</a></div>
  {% else %}
    {% if m.stale %}<div class="cbanner warn">\u26A0 Stale \u2014 last built {{ m.age_min }} min ago
      (fresh under {{ stale_min }} min). The refresh cron may not have run; treat with caution.</div>{% endif %}

    <div class="tabs">
      {% for key,lbl in [('log','Call log'),('threads','Conversations'),('staff','Staff'),('leads','New leads'),('noshows','No-shows'),('pipe','Pipeline')] %}
        <a class="{{ 'on' if view==key else '' }}" href="/portal/console?view={{key}}&{{ base_qs }}">{{ lbl }}</a>
      {% endfor %}
      <a class="" href="/portal/digest">Digest</a>
      <a href="/portal" style="margin-left:auto">&larr; Portal</a>
    </div>

    <form class="filt" method="GET" action="/portal/console" id="ff">
      <input type="hidden" name="view" value="{{ view }}">
      <div class="row">
        <label>Direction<select name="direction" onchange="ff.submit()">
          <option value="">All</option>
          <option value="In"  {{ 'selected' if f.direction=='In' else '' }}>In ({{ fac.direction.get('In',0) }})</option>
          <option value="Out" {{ 'selected' if f.direction=='Out' else '' }}>Out ({{ fac.direction.get('Out',0) }})</option>
        </select></label>
        <label>Answered<select name="answered" onchange="ff.submit()">
          <option value="">All</option>
          <option value="answered"  {{ 'selected' if f.answered=='answered' else '' }}>Answered ({{ fac.answered.get('answered',0) }})</option>
          <option value="missed"    {{ 'selected' if f.answered=='missed' else '' }}>Missed ({{ fac.answered.get('missed',0) }})</option>
          <option value="netmissed" {{ 'selected' if f.answered=='netmissed' else '' }}>Net-missed open calls ({{ fac.answered.get('netmissed',0) }})</option>
        </select></label>
        <label>Agent<select name="agent" onchange="ff.submit()">
          <option value="">All</option>
          {% for a in agents %}<option value="{{ a }}" {{ 'selected' if f.agent==a else '' }}>{{ a }} ({{ fac.agent.get(a,0) }})</option>{% endfor %}
        </select></label>
        <label>Flag<select name="flag" onchange="ff.submit()">
          <option value="">Any</option>
          {% for k,lbl in flag_opts %}<option value="{{ k }}" {{ 'selected' if f.flag==k else '' }}>{{ lbl }}</option>{% endfor %}
        </select></label>
        <label>From <input type="date" name="from" value="{{ f.frm }}"></label>
        <label>To <input type="date" name="to" value="{{ f.to }}"></label>
        <label>Search <input type="text" name="q" value="{{ f.q }}" placeholder="number / name / diagnosis"></label>
        <button class="btn" type="submit">Apply</button>
        <a class="clr" href="/portal/console?view={{ view }}">Clear</a>
        <a class="csvbtn" href="/portal/console.csv?{{ full_qs }}">\u2B07 CSV</a>
      </div>
    </form>

    {% if view=='log' %}
      <div class="summ">{{ total }} calls{% if more %} \u2014 showing newest {{ limit }}; narrow filters or export CSV for all{% endif %}. Tap a day, then a row, to expand transcript & AI detail.</div>
      <div class="gwrap mobile-scroll">
      <div class="hdr"><span>call</span><span>rec</span><span>patient</span><span>dx \u00b7 visit</span><span>staff</span><span>signals</span><span>my review \u00b7 actions</span></div>
      {% for day, drows in day_groups %}
        <details class="day" {% if loop.first %}open{% endif %}>
          <summary>{{ day }}<span class="dcount">{{ drows|length }} calls</span></summary>
          {% for r in drows %}
            <details class="callrow"><summary>{{ rowsummary(r) }}</summary>{{ detail(r) }}</details>
          {% endfor %}
        </details>
      {% endfor %}
      </div>
      {% if not day_groups %}<div class="muted" style="padding:18px">No calls match these filters.</div>{% endif %}

    {% elif view=='threads' %}
      <div class="summ">{{ convs|length }} conversations \u00b7 grouped by last-try date \u00b7 net-missed first within a day. Expand for attempts.</div>
      <div class="gwrap mobile-scroll">
      <div class="hdr"><span>call</span><span>rec</span><span>patient</span><span>dx \u00b7 visit</span><span>staff</span><span>signals</span><span>my review \u00b7 actions</span></div>
      {% for lbl, iso, cvs in conv_groups %}
        <details class="day" {% if loop.first %}open{% endif %}>
          <summary>{{ lbl }}<span class="dcount">{{ cvs|length }} conversations</span></summary>
          {% for cv in cvs %}
          <details class="conv">
            <summary>
              <span class="tc"><span class="t {{ 'inok' if cv.any_connected else 'inmiss' }}"><svg class="ic"><use href="#i-in"/></svg>{{ cv.last_ts[11:16] }}</span><span class="u">last try</span></span>
              <span class="tc"><span class="t">{{ cv.attempts }} tries</span><span class="u">{{ cv.miss_attempts }} missed</span></span>
              <span class="idc">{% if cv.name %}<span class="nm">{{ cv.name }}</span><span class="sub">{{ cv.phone10 }}{% if cv.agesex %} \u00b7 {{ cv.agesex }}{% endif %}{% if cv.clinic_id %} \u00b7 <b>{{ cv.clinic_id }}</b>{% endif %}</span>{% else %}<span class="nm mono">{{ cv.phone10 }}</span>{% if not cv.in_master %}<span class="sub warn">not in patient master</span>{% endif %}{% endif %}</span>
              <span class="dxc">{% if cv.diagnosis %}<span class="d1">{{ cv.diagnosis }}</span>{% elif not cv.in_master %}<span class="d1 mut">\u2014</span>{% else %}<span class="d1 mut">no dx in master</span>{% endif %}{% if cv.last_visit %}<span class="d2">{{ cv.last_visit }}</span>{% endif %}</span>
              <span class="agc">{{ cv.last_agent or '\u2014' }}</span>
              <span class="sig"><span class="l1">{% if cv.net_open %}<span class="chip flagc"><svg class="ic s"><use href="#i-flag"/></svg>NET-MISSED</span>{% elif cv.any_connected %}<span class="chip okc">connected</span>{% endif %}</span><span class="l2">{% if cv.net_open %}nobody has reached this caller yet{% elif cv.miss_attempts %}reached after {{ cv.miss_attempts }} miss(es){% else %}all attempts answered{% endif %}</span></span>
              <span class="tc"><span class="u">expand for attempts <svg class="ic s"><use href="#i-chev"/></svg></span></span>
            </summary>
            {% for lg in cv.legs %}{{ detail(lg) }}{% endfor %}
          </details>
          {% endfor %}
        </details>
      {% endfor %}
      </div>
      {% if not convs %}<div class="muted" style="padding:18px">No conversations match.</div>{% endif %}

    {% elif view=='staff' %}
      <div class="summ">Week at a glance \u00b7 cell = answered/total \u00b7 filed % \u2014 tap a date header to open that day \u00b7 <a class="lnk" href="/portal/console/staffreport?day={{ wk_sd }}">\U0001F4CB Daily coaching report \u2192</a></div>
      <div class="gwrap" style="padding:12px 16px;margin-bottom:10px">
      <table class="log"><thead><tr><th>agent</th>{% for d in wk_days %}<th><a class="lnk" href="/portal/console?view=staff&sd={{ d }}">{{ d[5:] }}</a></th>{% endfor %}</tr></thead><tbody>
      {% for ag in wk_agents %}<tr><td><a class="lnk" href="/portal/console?view=log&agent={{ ag|urlencode }}">{{ ag }}</a></td>
        {% for d in wk_days %}{% set m = wk_matrix.get(ag, {}).get(d) %}<td class="mono">{% if m %}{{ m.answered }}/{{ m.total }} \u00b7 <span class="{{ 'ok' if m.pct>=85 else ('amber' if m.pct>=70 else 'netbadge') }}" style="background:none;padding:0">{{ m.pct }}%</span>{% if m.mismatch %} \u00b7 <span class="amber" style="background:none;padding:0">{{ m.mismatch }}\u26A0</span>{% endif %}{% else %}\u2014{% endif %}</td>{% endfor %}
      </tr>{% endfor %}
      </tbody></table>
      </div>
      <div class="gwrap mobile-scroll">
      <div class="hdr"><span>call</span><span>rec</span><span>patient</span><span>dx \u00b7 visit</span><span>staff</span><span>signals</span><span>my review \u00b7 actions</span></div>
      {% for ag in wk_agents %}{% set m = wk_matrix.get(ag, {}).get(wk_sd) %}{% if m %}
        <details class="day" {% if loop.first %}open{% endif %}>
          <summary><svg class="ic chev"><use href="#i-chev"/></svg>{{ wk_sd[5:] }} \u2014 {{ ag }} \u00b7 {{ m.total }} calls \u00b7 {{ m.filed }} filed ({{ m.pct }}%) \u00b7 {{ m.mismatch }} mismatch \u00b7 {{ m.myrev }} reviewed by me<span class="dcount">{{ m.flags }} flag(s)</span></summary>
          {% for r in wk_rows.get(ag ~ '|' ~ wk_sd, []) %}
            <details class="callrow"><summary>{{ rowsummary(r) }}</summary>{{ detail(r) }}</details>
          {% endfor %}
        </details>
      {% endif %}{% endfor %}
      </div>
      {% if not wk_agents %}<div class="muted" style="padding:18px">No attributed calls in the last 7 days.</div>{% endif %}

    {% elif view=='leads' %}
      <div class="summ">{{ leads|length }} unknown incoming numbers (not in Patient_Master) \u2014 first-time enquiries (D243). \U0001F525 = worth chasing \u00b7 grouped by latest attempt.</div>
      <div class="gwrap mobile-scroll">
      <div class="hdr"><span>call</span><span>rec</span><span>patient</span><span>dx \u00b7 visit</span><span>staff</span><span>signals</span><span>my review \u00b7 actions</span></div>
      {% for lbl, iso, ls in lead_groups %}
        <details class="day" {% if loop.first %}open{% endif %}>
          <summary>{{ lbl }}<span class="dcount">{{ ls|length }} leads</span></summary>
          {% for l in ls %}
          <details class="conv">
            <summary>
              <span class="tc"><span class="t {{ 'inok' if l.answered else 'inmiss' }}"><svg class="ic"><use href="#i-in"/></svg>{{ l.last_seen[11:16] }}</span><span class="u">latest</span></span>
              <span class="tc"><span class="t">{{ l.attempts }} tr{{ 'y' if l.attempts==1 else 'ies' }}</span></span>
              <span class="idc"><span class="nm mono">{{ l.phone10 }}</span><span class="sub warn">not in patient master</span></span>
              <span class="dxc"><span class="d1 mut">\u2014</span></span>
              <span class="agc">{{ l.last_agent or '\u2014' }}</span>
              <span class="sig"><span class="l1">{% if l.hot %}<span class="chip hotc">\U0001F525 HOT</span>{% endif %}{% if l.answered %}<span class="chip okc">reached</span>{% else %}<span class="chip amberc">not reached</span>{% endif %}</span><span class="l2">{% if l.hot %}worth chasing \u00b7 {% endif %}call back to convert</span></span>
              <span class="tc"><span class="u">expand for attempts <svg class="ic s"><use href="#i-chev"/></svg></span></span>
            </summary>
            {% for lg in l.legs %}{{ detail(lg) }}{% endfor %}
          </details>
          {% endfor %}
        </details>
      {% endfor %}
      </div>
      {% if not leads %}<div class="muted" style="padding:18px">No new leads in range.</div>{% endif %}

    {% elif view=='noshows' %}
      <div class="summ">Appointment booked, not visited \u2014 tomorrow's calling work \u00b7 plus your open send-backs.
        <a class="lnk" style="margin-left:12px" href="/portal/console/reviews.csv">\u2B07 my reviews (training CSV)</a></div>
      {% if sb_open %}
        <h3 style="font-size:13px;margin:10px 0 6px">Call list from Dr Manoj \u2014 open ({{ sb_open|length }})</h3>
        <table class="log" style="max-width:900px"><thead><tr><th>Sent</th><th>Reason</th><th>Join key</th><th></th></tr></thead><tbody>
        {% for s in sb_open %}<tr><td class="mono">{{ s.at }}</td><td>{{ s.reason }}</td><td class="mono muted sm">{{ s.join_key }}</td>
          <td><form method="POST" action="/portal/console/sendback/resolve" style="margin:0">
            <input type="hidden" name="join_key" value="{{ s.join_key }}">
            <input type="hidden" name="ret" value="view=noshows">
            <button class="btn sm" type="submit">Resolve</button></form></td></tr>{% endfor %}
        </tbody></table>
      {% endif %}
      {% if spam_list %}
        <h3 style="font-size:13px;margin:14px 0 6px">Block list \u2014 marked Spam / marketing ({{ spam_list|length }})</h3>
        <div class="summ">Excluded from New-leads and net-missed. Locking the number itself is a MyOperator-panel action.</div>
        <div style="margin-bottom:10px">{% for p in spam_list %}<span class="ctx" style="margin:2px">{{ p }}</span>{% endfor %}</div>
      {% endif %}
      <h3 style="font-size:13px;margin:14px 0 6px">Appointment booked, not visited</h3>
      {% if noshows and noshows.feed and noshows.feed.found %}
        {% if ns_banner %}
        <div class="cbanner {{ 'bad' if ns_banner.x else 'warn' }}" style="{{ 'background:rgba(34,197,94,.12);color:#86efac;border-color:rgba(34,197,94,.35)' if not ns_banner.x else '' }}">
          Due-date calling: <b>{{ ns_banner.x }}</b> of <b>{{ ns_banner.y }}</b> no-shows have had <b>NO call since due</b> \u00b7 <b>{{ ns_banner.z }}</b> reached.
        </div>
        {% endif %}
        <div class="gwrap mobile-scroll">
        <div class="hdr"><span>due</span><span>calls</span><span>patient</span><span>dx \u00b7 visit</span><span>called by</span><span>status \u00b7 accountability</span><span></span></div>
        {% for lbl, iso, ns in ns_groups %}
          <details class="day" {% if loop.first %}open{% endif %}>
            <summary>due {{ lbl }}<span class="dcount">{{ ns|length }} patients</span></summary>
            {% for n in ns %}
            <details class="conv">
              <summary>
                <span class="tc"><span class="t">{{ n.due_h }}</span><span class="u">due date</span></span>
                <span class="tc"><span class="t">{{ n.cb_attempts }}</span><span class="u">since due</span></span>
                <span class="idc">{% if n.name %}<span class="nm">{{ n.name }}</span><span class="sub">{{ n.phone10 }}{% if n.agesex %} \u00b7 {{ n.agesex }}{% endif %}{% if n.clinic_id %} \u00b7 <b>{{ n.clinic_id }}</b>{% endif %}</span>{% else %}<span class="nm mono">{{ n.phone10 }}</span>{% endif %}</span>
                <span class="dxc">{% if n.diagnosis %}<span class="d1" style="color:#c7d2fe">{{ n.diagnosis }}</span>{% elif not n.in_master %}<span class="d1" style="color:#fca5a5">not in master</span>{% else %}<span class="d1 muted">no dx in master</span>{% endif %}{% if n.lv_h %}<span class="d2">last {{ n.lv_h }}</span>{% endif %}</span>
                <span class="idc"><span class="agc">{{ n.cb_last_agent or '\u2014' }}</span>{% if n.last_h %}<span class="sub">{{ n.last_h }}</span>{% endif %}</span>
                <span class="sig"><span class="l1">{% if not n.cb_attempts %}<span class="chip flagc"><svg class="ic s"><use href="#i-flag"/></svg>NO CALL SINCE DUE</span>{% elif n.cb_reached %}<span class="chip okc">reached{% if n.tries %} on try {{ n.tries|length }}{% endif %}</span>{% else %}<span class="chip amberc">tried \u00b7 not reached</span>{% endif %}{% if n.status_raw %}<span class="chip infoc" title="status noted in tracker">{{ n.status_raw }}</span>{% endif %}</span><span class="l2">{% if n.tries_h %}{{ n.tries_h }}{% else %}protocol: due-day morning + 30 min + 1 hr \u2014 none made yet{% endif %}</span></span>
                <span class="act">{% if n.phone10 %}<a class="abtn callb" href="tel:+91{{ n.phone10 }}" title="Call now"><svg class="ic"><use href="#i-call"/></svg></a>{% endif %}</span>
              </summary>
              {% if n.tries %}
              <div class="xcard">
                <div class="xrow"><span class="xlab">Due-day efforts</span><span>morning \u2192 +30 min \u2192 +1 hr (max 3), then the patient surfaces on the Callback Tracker action sheet.</span></div>
                <table class="log" style="max-width:520px"><thead><tr><th>try</th><th>date</th><th>time</th><th>caller</th><th>result</th></tr></thead><tbody>
                {% for t in n.tries %}<tr><td class="mono">{{ loop.index }}</td><td class="mono">{{ t.d[5:] }}</td><td class="mono">{{ t.t }}</td><td>{{ t.agent }}</td><td>{% if t.ok %}<span class="chip okc">reached</span>{% else %}<span class="chip flagc">no answer</span>{% endif %}</td></tr>{% endfor %}
                </tbody></table>
              </div>
              {% endif %}
            </details>
            {% endfor %}
          </details>
        {% endfor %}
        </div>
        {% if not noshows.rows %}<div class="muted" style="padding:18px">No booked-not-visited rows \U0001F389</div>{% endif %}
      {% else %}
        <div class="cbanner warn">The Followups_Today feed was not found/usable at the last build \u2014 the no-show list cannot be computed. Feed state: {{ noshows.feed if noshows else 'unknown' }}. (Honest absence, not zeros \u2014 D236.)</div>
      {% endif %}

    {% elif view=='pipe' %}
      <div class="summ">Pipeline health \u2014 how fast a call becomes a transcript and a verdict, and exactly why anything is unjudged.</div>
      {% if pipe %}
        {% if pipe.nm_calls is not none %}<div class="cbanner warn" style="background:rgba(59,130,246,.10);color:#93c5fd;border-color:rgba(59,130,246,.3)">Net-missed open: <b>{{ pipe.nm_threads }}</b> patient threads \u00b7 <b>{{ pipe.nm_calls }}</b> missed calls inside them. The filter chip counts calls; the builder reports threads \u2014 both are correct.</div>{% endif %}
        {% if pipe.lat %}<table class="log" style="max-width:520px"><thead><tr><th>Judge lag (call \u2192 verdict)</th><th>Median</th><th>p90</th><th>Max</th></tr></thead>
        <tbody><tr><td class="muted">{{ pipe.lat.n }} judged calls</td><td class="mono">{{ pipe.lat.median }} min</td><td class="mono">{{ pipe.lat.p90 }} min</td><td class="mono">{{ pipe.lat.max }} min</td></tr></tbody></table>{% else %}<div class="muted">No latency rows yet.</div>{% endif %}
        <h3 style="font-size:13px;margin:16px 0 6px">Why calls are unjudged</h3>
        <table class="log" style="max-width:420px"><tbody>
        {% for reason, n in pipe.reasons %}<tr><td>{{ reason }}</td><td class="mono">{{ n }}</td></tr>{% endfor %}
        {% if not pipe.reasons %}<tr><td class="muted">nothing unjudged</td></tr>{% endif %}
        </tbody></table>
        <h3 style="font-size:13px;margin:16px 0 6px">Judge-pending backlog (oldest first)</h3>
        <table class="log" style="max-width:560px"><tbody>
        {% for jk, ts in pipe.backlog %}<tr><td class="mono">{{ ts }}</td><td class="mono muted sm">{{ jk }}</td></tr>{% endfor %}
        {% if not pipe.backlog %}<tr><td class="muted">no judge-pending backlog</td></tr>{% endif %}
        </tbody></table>
      {% endif %}
    {% endif %}

    <div class="summ" style="margin-top:16px">Built {{ m.built_at or 'unknown' }}{% if m.age_min is not none %} \u00b7 {{ m.age_min }} min ago{% endif %}.</div>
  {% endif %}
</div>
</body></html>
"""


def _query_pipeline(conn):
    """rev5 Item 3: the pipeline/latency mini-view. Read-only over latency,
    unjudged, conversations, calls. Fail-soft: any missing table -> empty dict
    section, page still renders (D236)."""
    out = {"lat": None, "reasons": [], "backlog": [], "nm_calls": None, "nm_threads": None}
    def _q(sql, args=()):
        try:
            return conn.execute(sql, args).fetchall()
        except Exception:
            return []
    # latency percentiles (minutes) over rows that have a judge lag
    lags = sorted(x[0] for x in _q(
        "SELECT lag_judge_call FROM latency WHERE lag_judge_call IS NOT NULL") if x[0] is not None)
    if lags:
        def pct(p):
            i = min(len(lags) - 1, max(0, int(round(p * (len(lags) - 1)))))
            return round(lags[i] / 60.0, 1)   # latency lags are seconds -> minutes
        out["lat"] = {"n": len(lags), "median": pct(0.5), "p90": pct(0.9),
                      "max": round(lags[-1] / 60.0, 1)}
    # reasons-not-judged counts
    out["reasons"] = _q("SELECT reason, COUNT(*) FROM unjudged GROUP BY reason ORDER BY 2 DESC")
    # judge-pending backlog with call age (oldest first)
    out["backlog"] = _q(
        "SELECT u.join_key, c.ended_at_ist FROM unjudged u "
        "JOIN calls c ON c.join_key=u.join_key "
        "WHERE u.reason='judge pending' ORDER BY c.ended_at_ist ASC LIMIT 25")
    # net-missed: calls vs threads, labelled (the 139-vs-109 fix)
    r = _q("SELECT COUNT(*) FROM calls c WHERE c.direction='In' AND c.answered=0 "
           "AND c.phone10 IN (SELECT phone10 FROM conversations WHERE net_missed_open=1)")
    out["nm_calls"] = r[0][0] if r else None
    r = _q("SELECT COUNT(*) FROM conversations WHERE net_missed_open=1")
    out["nm_threads"] = r[0][0] if r else None
    return out


def _query_noshows(conn):
    """W2 Track N: booked-but-not-seen rows + the feed's honest discovery state."""
    out = {"feed": None, "rows": []}
    try:
        import json as _json
        m = conn.execute("SELECT v FROM meta WHERE k='followups_feed'").fetchone()
        out["feed"] = _json.loads(m[0]) if m else None
    except Exception:
        out["feed"] = None
    try:
        out["rows"] = [dict(zip(
            ("phone10", "name", "due_date", "status_raw", "cb_attempts",
             "cb_last_ts", "cb_last_agent", "cb_reached",
             "diagnosis", "clinic_id", "last_visit", "age", "gender", "pid"), r))
            for r in conn.execute(
                "SELECT n.phone10,n.name,n.due_date,n.status_raw,n.cb_attempts,"
                "n.cb_last_ts,n.cb_last_agent,n.cb_reached,"
                "COALESCE(p.diagnosis,''),COALESCE(p.clinic_id,''),"
                "COALESCE(p.last_visit,''),COALESCE(p.age,''),COALESCE(p.gender,''),"
                "p._pid "
                "FROM no_shows n LEFT JOIN " + _DP + " p ON p.phone10=n.phone10 "
                "ORDER BY n.due_date DESC, n.name LIMIT 200")]
        for r in out["rows"]:                       # S171: human display, fail-soft
            r["due_h"] = _ns_date_h(r["due_date"])
            r["last_h"] = _ns_ts_h(r["cb_last_ts"])
            r["lv_h"] = _ns_date_h(r["last_visit"])
            r["agesex"] = "/".join(x for x in ((r["age"] or "").strip(),
                                               (r["gender"] or "").strip()[:1].upper()) if x)
            r["in_master"] = r.get("pid") is not None
    except Exception:
        out["rows"] = []
    return out


def _ns_date_h(iso):
    """ISO 'YYYY-MM-DD' -> '11-Aug-2026' for the no-show table. Fail-soft:
    anything unparseable (incl. pre-S171 truncated values) is shown as-is."""
    try:
        return datetime.datetime.strptime((iso or "").strip(),
                                          "%Y-%m-%d").strftime("%d-%b-%Y")
    except Exception:
        return (iso or "").strip()


def _ns_ts_h(ts):
    """'2026-07-31 18:19' (or pre-S171 '...T18:19') -> '31-Jul 18:19'. Fail-soft."""
    t = (ts or "").replace("T", " ").strip()
    try:
        return datetime.datetime.strptime(t, "%Y-%m-%d %H:%M").strftime("%d-%b %H:%M")
    except Exception:
        return t


def _console_base_qs(f, drop=()):
    import urllib.parse as _up
    pairs = []
    for k, key in (("direction", "direction"), ("answered", "answered"), ("agent", "agent"),
                   ("flag", "flag"), ("frm", "from"), ("to", "to"), ("q", "q")):
        if k in drop:
            continue
        if f.get(k, ""):
            pairs.append((key, f[k]))
    return _up.urlencode(pairs)


def _serve_rec(join_key):
    """Serve a recording: local cache first (Range-capable), else 302 to Drive,
    else 404. join_key strictly validated before any path use. UNDECORATED --
    called by the doctor route AND the signed staff link (S171)."""
    import re as _re
    if not _re.fullmatch(r"\d{6,12}_\d{6,14}", join_key or ""):
        abort(404)
    path = os.path.join(REC_CACHE_PATH, join_key + ".mp3")
    if os.path.isfile(path):
        return send_file(path, mimetype="audio/mpeg", conditional=True)
    conn = _console_conn()
    if conn is not None:
        try:
            row = conn.execute(
                "SELECT recording_link FROM recordings WHERE join_key=? "
                "AND recording_link<>'' LIMIT 1", (join_key,)).fetchone()
        finally:
            conn.close()
        if row and row[0]:
            return redirect(row[0])
    abort(404)


@app.route("/portal/rec/<join_key>")
@doctor_required
def console_rec(join_key):
    return _serve_rec(join_key)


@app.route("/portal/console/review", methods=["POST"])
@doctor_required
def console_review():
    """W2 Item 5: idempotent upsert of MY final verdict (the AI-training label)."""
    jk = (request.form.get("join_key") or "").strip()
    fo = (request.form.get("final_outcome") or "").strip()
    note = (request.form.get("note") or "").strip()
    ret = request.form.get("ret") or "view=log"
    if jk and (fo or note):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = _reviews_conn()
        conn.execute(
            "INSERT INTO dispositions (join_key,final_outcome,note,refereed_by,refereed_at) "
            "VALUES (?,?,?,'manoj',?) "
            "ON CONFLICT(join_key) DO UPDATE SET final_outcome=excluded.final_outcome,"
            " note=excluded.note, refereed_at=excluded.refereed_at",
            (jk, fo, note, now))
        conn.commit(); conn.close()
    return redirect("/portal/console?" + ret)


@app.route("/portal/console/sendback", methods=["POST"])
@doctor_required
def console_sendback():
    """W2 Item 6: send a call back to staff with a reason. One OPEN send-back
    per join_key (a second send updates the reason -- idempotent)."""
    jk = (request.form.get("join_key") or "").strip()
    phone = (request.form.get("phone10") or "").strip()
    patient = (request.form.get("patient") or "").strip()
    reason = (request.form.get("reason") or "").strip()
    ret = request.form.get("ret") or "view=log"
    if jk and reason:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = _reviews_conn()
        cur = conn.execute("SELECT id FROM send_backs WHERE join_key=? AND status='open'", (jk,))
        row = cur.fetchone()
        if row:
            conn.execute("UPDATE send_backs SET reason=?, sent_at=? WHERE id=?",
                         (reason, now, row[0]))
        else:
            conn.execute(
                "INSERT INTO send_backs (join_key,phone10,patient,reason,sent_by,sent_at,status) "
                "VALUES (?,?,?,?,'manoj',?,'open')", (jk, phone, patient, reason, now))
        conn.commit(); conn.close()
    return redirect("/portal/console?" + ret)


@app.route("/portal/console/sendback/resolve", methods=["POST"])
@doctor_required
def console_sendback_resolve():
    jk = (request.form.get("join_key") or "").strip()
    ret = request.form.get("ret") or "view=noshows"
    if jk:
        conn = _reviews_conn()
        conn.execute("UPDATE send_backs SET status='done' WHERE join_key=? AND status='open'", (jk,))
        conn.commit(); conn.close()
    return redirect("/portal/console?" + ret)



# ---------------------------------------------------------------------------
# S171 Track G: /portal/digest -- the 11:00 pulse + 21:30 digest, LIVE from
# console.db (D297 §11). Read-only. Fail-loud on stale/missing db (D236).
# Severity ordering ported verbatim from daily_digest.py (URGENT > POST-OP >
# CLINICAL > SURGERY > COMPLAINT > CONDUCT > MISMATCH), cap 12.
# ---------------------------------------------------------------------------
_DG_SEV = [("flag_urgent", "URGENT"), ("flag_postop", "POST-OP"),
           ("flag_clinical", "CLINICAL"), ("flag_surgery", "SURGERY"),
           ("flag_complaint", "COMPLAINT"), ("flag_conduct", "CONDUCT")]
_DG_BUCKETS = ("Match", "Mismatch", "Partial", "No claim logged", "Unclear")
_DG_CAP = 12


def _query_digest(conn, day):
    """Everything the digest page shows, from console.db, for one ISO day."""
    out = {"day": day, "calls": {}, "buckets": {}, "flagged": 0, "other": 0,
           "filed": 0, "not_filed": 0, "worst": [], "unjudged": [],
           "nm_open": None, "judged": 0}
    def q(sql, args=()):
        try:
            return conn.execute(sql, args).fetchall()
        except Exception:
            return []
    r = q("SELECT COUNT(*),"
          " SUM(CASE WHEN direction='In' THEN 1 ELSE 0 END),"
          " SUM(CASE WHEN direction='Out' THEN 1 ELSE 0 END),"
          " SUM(CASE WHEN answered=1 THEN 1 ELSE 0 END),"
          " SUM(CASE WHEN answered=0 THEN 1 ELSE 0 END) "
          "FROM calls WHERE substr(ended_at_ist,1,10)=?", (day,))
    if r:
        t, i, o, a, m = r[0]
        out["calls"] = {"total": t or 0, "in": i or 0, "out": o or 0,
                        "answered": a or 0, "missed": m or 0}
    vrows = q("SELECT verdict, claimed_outcome, ai_outcome, time, patient_name,"
              " patient_number, recording_link, join_key, not_filed,"
              " flag_urgent, flag_postop, flag_clinical, flag_surgery,"
              " flag_complaint, flag_conduct "
              "FROM verdicts WHERE date=?", (day,))
    buckets = {b: 0 for b in _DG_BUCKETS}
    other = flagged = filed = notf = 0
    tagged = []
    flag_jks = []
    for r in vrows:
        (verdict, claimed, ai, tm, pname, pnum, rlink, jk, nf,
         fu, fp, fcl, fs, fc, fcon) = r
        v = (verdict or "").strip()
        if v in buckets:
            buckets[v] += 1
        elif v:
            other += 1
        fvals = {"flag_urgent": fu, "flag_postop": fp, "flag_clinical": fcl,
                 "flag_surgery": fs, "flag_complaint": fc, "flag_conduct": fcon}
        anyflag = any(_truthy(x) for x in fvals.values())
        if anyflag:
            flagged += 1
            if (jk or "").strip():
                flag_jks.append(jk.strip())
        if (claimed or "").strip():
            filed += 1
        if nf == 1:
            notf += 1
        sev = None
        for rank, (col, label) in enumerate(_DG_SEV):
            if _truthy(fvals[col]):
                sev = (rank, label)
                break
        if sev is None and v == "Mismatch":
            sev = (len(_DG_SEV), "MISMATCH")
        if sev is not None:
            tagged.append((sev[0], (tm or ""), {
                "time": (tm or "").strip(), "why": sev[1],
                "name": (pname or "").strip(), "phone": (pnum or "").strip(),
                "claimed": (claimed or "").strip(), "ai": (ai or "").strip(),
                "join_key": (jk or "").strip()}))
    tagged.sort(key=lambda t: (t[0], t[1]))
    out["worst"] = [t[2] for t in tagged[:_DG_CAP]]
    out["buckets"] = buckets
    out["other"], out["flagged"] = other, flagged
    out["filed"], out["not_filed"] = filed, notf
    out["judged"] = len(vrows)
    out["unjudged"] = q(
        "SELECT u.reason, COUNT(*) FROM unjudged u JOIN calls c "
        "ON c.join_key=u.join_key WHERE substr(c.ended_at_ist,1,10)=? "
        "GROUP BY u.reason ORDER BY 2 DESC", (day,))
    r = q("SELECT COUNT(*) FROM conversations WHERE net_missed_open=1")
    out["nm_open"] = r[0][0] if r else None
    # S171 digest v2: time span of the day's calls
    r = q("SELECT MIN(substr(ended_at_ist,12,5)), MAX(substr(ended_at_ist,12,5)) "
          "FROM calls WHERE substr(ended_at_ist,1,10)=?", (day,))
    out["span"] = (r[0][0] or "", r[0][1] or "") if r else ("", "")
    # unique callers, named vs number-only
    r = q("SELECT COUNT(DISTINCT c.phone10), "
          "COUNT(DISTINCT CASE WHEN p._pid IS NOT NULL THEN c.phone10 END) "
          "FROM calls c LEFT JOIN " + _DP + " p ON p.phone10=c.phone10 "
          "WHERE substr(c.ended_at_ist,1,10)=? AND c.phone10<>''", (day,))
    tot, named = (r[0] if r else (0, 0))
    out["callers"] = {"total": tot or 0, "named": named or 0,
                      "unknown": (tot or 0) - (named or 0)}
    # funnel: answered -> transcribed -> judged
    r = q("SELECT COUNT(*) FROM calls c JOIN transcripts t ON t.join_key=c.join_key "
          "WHERE substr(c.ended_at_ist,1,10)=? AND c.answered=1 "
          "AND COALESCE(t.text,'')<>''", (day,))
    out["tx_n"] = r[0][0] if r else 0
    # net-missed split: last 7 days vs older
    try:
        d7 = (datetime.date.fromisoformat(day) - datetime.timedelta(days=7)).isoformat()
    except Exception:
        d7 = day
    r = q("SELECT SUM(CASE WHEN substr(last_ts,1,10)>=? THEN 1 ELSE 0 END), "
          "SUM(CASE WHEN substr(last_ts,1,10)<? THEN 1 ELSE 0 END) "
          "FROM conversations WHERE net_missed_open=1", (d7, d7))
    out["nm7"], out["nm_old"] = ((r[0][0] or 0, r[0][1] or 0) if r else (0, 0))
    out["flag_jks"] = flag_jks
    c = out["calls"]
    cl = out.get("callers") or {}
    bits = ["%d attempts (%d in / %d out)" % (c.get("total", 0), c.get("in", 0),
                                              c.get("out", 0)),
            "%d callers (%d patients / %d unknown)" % (cl.get("total", 0),
                                                       cl.get("named", 0),
                                                       cl.get("unknown", 0)),
            "%d answered \u2192 %d transcribed \u2192 %d judged" % (
                c.get("answered", 0), out.get("tx_n", 0), out["judged"]),
            "%d staff-filed" % out["filed"]]
    if buckets["Mismatch"]:
        bits.append("%d mismatch" % buckets["Mismatch"])
    if flagged:
        bits.append("%d safety-flagged" % flagged)
    if buckets["No claim logged"]:
        bits.append("%d calls nobody logged" % buckets["No claim logged"])
    out["oneline"] = " \u00b7 ".join(bits) + "."
    return out


DIGEST_HTML = PAGE_HEAD + ROW_SHARED + """
<style>
.summ{font-size:13px}
table.log{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0 14px}
table.log th{font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
 color:var(--muted);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
table.log td{padding:7px 8px;border-bottom:1px solid rgba(39,75,102,.4)}
.dgsec{font-size:12px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
 color:var(--muted);margin:22px 2px 8px;padding-bottom:5px;border-bottom:1px solid var(--line)}
.dgbig{font-size:16px;color:#fff;font-weight:600;margin:4px 0 10px;line-height:1.5}
details.dgx{border:1px solid var(--line);border-radius:12px;margin:8px 0;background:rgba(22,50,74,.35)}
details.dgx>summary{cursor:pointer;list-style:none;padding:11px 14px;font-weight:700;font-size:13.5px;color:#fff}
details.dgx>summary::-webkit-details-marker{display:none}
details.dgx>summary:after{content:" \u25BE";color:var(--muted)}
</style>
<div class="wrap cwrap">
  <div class="head"><h1>\U0001F4EF Daily digest \u2014 live</h1>
    <span class="sub">{{ d.day }} \u00b7 <a class="lnk" href="/portal/console">\u2190 Console</a></span></div>

  {% if not m.ok %}<div class="cbanner bad">console.db unavailable \u2014 {{ m.err }}</div>{% else %}
  {% if m.stale %}<div class="cbanner warn">Data is {{ m.age_min }} min old (last build {{ m.built }}). Cron runs 9\u201321 IST.</div>{% endif %}

  <div class="dgsec">The day in one line \u00b7 {{ d.span[0] or '\u2014' }} \u2192 {{ d.span[1] or '\u2014' }}</div>
  <div class="dgbig">{{ d.oneline }}</div>

  <div class="dgsec">Pulse \u00b7 {{ d.span[0] or '\u2014' }} \u2192 {{ d.span[1] or '\u2014' }}</div>
  <table class="log" style="max-width:640px"><thead><tr><th>Attempts</th><th>Callers</th><th>In</th><th>Out</th><th>Answered</th><th>Transcribed</th><th>Judged</th></tr></thead>
  <tbody><tr><td class="mono">{{ d.calls.get('total',0) }}</td><td class="mono">{{ d.callers.total }} <span class="muted sm">({{ d.callers.named }}p/{{ d.callers.unknown }}?)</span></td>
  <td class="mono">{{ d.calls.get('in',0) }}</td><td class="mono">{{ d.calls.get('out',0) }}</td>
  <td class="mono">{{ d.calls.get('answered',0) }}</td><td class="mono">{{ d.tx_n }}</td><td class="mono">{{ d.judged }}</td></tr></tbody></table>
  {% if d.unjudged %}<div class="summ">Awaiting a verdict: {% for rs, n in d.unjudged %}{{ rs }} \u00d7 {{ n }}{{ '' if loop.last else ' \u00b7 ' }}{% endfor %}</div>
  {% else %}<div class="summ">Nothing awaiting a verdict today. \u2705</div>{% endif %}
  <div class="summ">Net-missed open threads: <b>{{ d.nm7 }}</b> in the last 7 days
    \u2014 <a class="lnk" href="/portal/console?view=threads&answered=netmissed">work the list</a>
    {% if d.nm_old %}\u00b7 plus <b>{{ d.nm_old }}</b> older <a class="lnk" href="/portal/console?view=threads&answered=netmissed">(review backlog)</a>{% endif %}</div>

  <div class="dgsec">Numbers (judged calls)</div>
  <table class="log" style="max-width:760px"><thead><tr><th>Match</th><th>Mismatch</th><th>Partial</th><th>Nobody logged</th><th>Unclear</th><th>Flagged</th><th>Staff filed</th><th>NOT FILED</th></tr></thead>
  <tbody><tr><td class="mono">{{ d.buckets.get('Match',0) }}</td><td class="mono">{{ d.buckets.get('Mismatch',0) }}</td>
  <td class="mono">{{ d.buckets.get('Partial',0) }}</td><td class="mono">{{ d.buckets.get('No claim logged',0) }}</td>
  <td class="mono">{{ d.buckets.get('Unclear',0) }}</td><td class="mono">{{ d.flagged }}</td>
  <td class="mono">{{ d.filed }}</td><td class="mono">{{ d.not_filed }}</td></tr></tbody></table>

  {% if d.flag_rows %}
  <details class="dgx"><summary>Safety-flagged today ({{ d.flag_rows|length }}) \u2014 listen here</summary>
    <div class="gwrap mobile-scroll">
    <div class="hdr"><span>call</span><span>rec</span><span>patient</span><span>dx \u00b7 visit</span><span>staff</span><span>signals</span><span>my review \u00b7 actions</span></div>
    {% for r in d.flag_rows %}<details class="callrow"><summary>{{ rowsummary(r) }}</summary>{{ detail(r) }}</details>{% endfor %}
    </div>
  </details>
  {% endif %}

  <div class="dgsec">Worst first \u2014 listen to these ({{ d.worst_rows|length }})</div>
  {% if d.worst_rows %}
  <div class="gwrap mobile-scroll">
  <div class="hdr"><span>call</span><span>rec</span><span>patient</span><span>dx \u00b7 visit</span><span>staff</span><span>signals</span><span>my review \u00b7 actions</span></div>
  {% for r in d.worst_rows %}<details class="callrow"><summary>{{ rowsummary(r) }}</summary>{{ detail(r) }}</details>{% endfor %}
  </div>
  {% else %}<div class="summ">Nothing severity-tagged today. \u2705</div>{% endif %}

  <div class="dgsec">Referee corner</div>
  <div class="summ">You have saved <b>{{ refereed }}</b> review(s) \u2014 they count toward the accuracy gate (D237/D191).</div>
  {% if d.ref_rows %}
  <details class="dgx"><summary>My latest reviews ({{ d.ref_rows|length }}) \u2014 inline</summary>
    <div class="gwrap mobile-scroll">
    <div class="hdr"><span>call</span><span>rec</span><span>patient</span><span>dx \u00b7 visit</span><span>staff</span><span>signals</span><span>my review \u00b7 actions</span></div>
    {% for r in d.ref_rows %}<details class="callrow"><summary>{{ rowsummary(r) }}</summary>{{ detail(r) }}</details>{% endfor %}
    </div>
  </details>
  {% endif %}

  <div class="summ" style="margin-top:18px">Built {{ m.built }} \u00b7 {{ m.age_min }} min ago \u00b7 emails at 11:00 / 21:30 continue unchanged.</div>
  {% endif %}
</div></body></html>
"""


def _rows_by_jks(conn, jks):
    """Full universal-row dicts for a list of join_keys (order preserved)."""
    jks = [j for j in (jks or []) if j]
    if not jks:
        return []
    qm = ",".join(["?"] * len(jks))
    rows = [_log_row(r) for r in conn.execute(
        _LOG_COLS + _LOG_FROM + "WHERE c.join_key IN (%s)" % qm, jks)]
    by = {r["join_key"]: r for r in rows}
    return [by[j] for j in jks if j in by]


@app.route("/portal/digest")
@doctor_required
def portal_digest():
    day = (request.args.get("day") or "").strip()
    if not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", day or ""):
        day = datetime.datetime.now().strftime("%Y-%m-%d")
    m = _console_meta()
    d = {"day": day, "oneline": "", "calls": {}, "buckets": {}, "flagged": 0,
         "filed": 0, "not_filed": 0, "worst": [], "unjudged": [],
         "nm_open": None, "judged": 0}
    refereed = 0
    if m["ok"]:
        conn = _console_conn()
        if conn is not None:
            try:
                d = _query_digest(conn, day)
                disp, sbm = _reviews_maps()
                d["worst_rows"] = _rows_by_jks(
                    conn, [w.get("join_key") for w in d.get("worst", [])])
                d["flag_rows"] = _rows_by_jks(conn, d.get("flag_jks", []))
                ref_jks = [k for k, v in sorted(disp.items(),
                           key=lambda kv: kv[1].get("at", ""), reverse=True)][:15]
                d["ref_rows"] = _rows_by_jks(conn, ref_jks)
                for lst in (d["worst_rows"], d["flag_rows"], d["ref_rows"]):
                    _overlay_reviews(lst, disp, sbm)
            finally:
                conn.close()
        try:
            rc = _reviews_conn()
            refereed = rc.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0]
            rc.close()
        except Exception:
            refereed = 0
    return render_template_string(DIGEST_HTML, hi_out=_hi_out, m=m, d=d, refereed=refereed,
                                  stale_min=CONSOLE_STALE_MIN,
                                  vocab=REVIEW_VOCAB, full_qs="view=log")


STAFFREPORT_HTML = PAGE_HEAD + ROW_SHARED + """
<style>
.coach{background:rgba(11,27,41,.35);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:0 0 14px}
.coach h2{font-size:15px;margin:0 0 4px;color:#fff}
.coach .st{font-size:var(--f-md);color:var(--muted);margin-bottom:10px}
.lesson{border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:8px 0;font-size:var(--f-md)}
.lesson b.bad{color:#fca5a5}.lesson b.good{color:#86efac}
.lesson .q{font-style:italic;color:#fde68a}
.wabox{background:#0b1b29;border:1px solid var(--line);border-radius:12px;padding:14px 16px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;line-height:1.8;white-space:pre-wrap;margin-top:10px}
.rbar{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 12px}
.rbtn{font-size:var(--f-sm);font-weight:600;padding:8px 14px;border-radius:9px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer;display:inline-flex;gap:6px;align-items:center;text-decoration:none}
.rbtn:hover{border-color:var(--blue)}
@media print{body{background:#fff;color:#111}.coach{border-color:#bbb;background:#fff;page-break-after:always}
 .coach h2,.lesson,.st{color:#111}.lesson{border-color:#ccc}.lesson b.bad{color:#b91c1c}.lesson b.good{color:#15803d}
 .lesson .q{color:#555}.rbar,.wabox,.tabs,.head .sub a{display:none}}
</style>
<div class="wrap cwrap">
  <div class="head"><h1>\U0001F4CB Staff coaching report</h1>
    <span class="sub">{{ day }} \u00b7 <a class="lnk" href="/portal/console?view=staff">\u2190 Staff tab</a></span></div>
  <div class="rbar">
    <a class="rbtn" href="/portal/console/staffreport?day={{ day }}&fmt=csv"><svg class="ic s"><use href="#i-dl"/></svg>CSV</a>
    <button class="rbtn" onclick="window.print()"><svg class="ic s"><use href="#i-print"/></svg>Print / PDF</button>
  </div>
  {% if not agents %}<div class="summ">No attributed calls for {{ day }}.</div>{% endif %}
  {% for a in agents %}
  <div class="coach">
    <h2>{{ a.agent }}</h2>
    <div class="st">{{ a.total }} calls \u00b7 {{ a.answered }} answered \u00b7 {{ a.filed }} filed ({{ a.pct }}%) \u00b7 {{ a.lessons|length }} to review</div>
    {% for L in a.lessons %}
    <div class="lesson">
      <div><b>{{ loop.index }}) {{ L.time }} \u00b7 {{ L.name or L.phone }}</b> <span class="muted mono sm">({{ L.phone }})</span></div>
      <div>\u0906\u092a\u0928\u0947 \u0926\u0930\u094d\u091c \u0915\u093f\u092f\u093e: <b class="bad">{{ L.filed_h }} \u274C</b> \u2003 \u0938\u0939\u0940 outcome: <b class="good">{{ L.correct_h }} \u2705</b></div>
      {% if L.why %}<div>\u0915\u094d\u092f\u094b\u0902: {{ L.why }}</div>{% endif %}
      {% if L.quote %}<div>\u092e\u0930\u0940\u091c\u093c \u0915\u0947 \u0936\u092c\u094d\u0926: <span class="q">"{{ L.quote }}"</span></div>{% endif %}
      <div>\U0001F3A7 <a class="lnk" href="/portal/rl/{{ L.jk }}/{{ L.sig }}">\u0938\u0941\u0928\u0947\u0902 (recording)</a></div>
    </div>
    {% endfor %}
    {% if a.notfiled %}<div class="lesson" style="border-color:rgba(234,179,8,.4)">\u26A0\uFE0F \u0906\u091c \u0926\u0930\u094d\u091c \u0928\u0939\u0940\u0902 \u0939\u0941\u0908\u0902: {{ a.notfiled|length }} \u0915\u0949\u0932 ({{ a.notfiled|join(' \u00b7 ') }})</div>{% endif %}
    <div class="rbar"><button class="rbtn" onclick="copyText('wa_{{ loop.index }}', this)"><svg class="ic s"><use href="#i-copy"/></svg>Copy WhatsApp ({{ a.agent.split(' ')[0] }})</button></div>
    <div class="wabox" id="wa_{{ loop.index }}">\U0001F4CB {{ a.agent }} \u2014 {{ day_h }}
\u0906\u091c: {{ a.total }} \u0915\u0949\u0932 \u00b7 {{ a.answered }} \u0909\u0920\u0940\u0902 \u00b7 {{ a.filed }} \u0926\u0930\u094d\u091c ({{ a.pct }}%) \u00b7 {{ a.lessons|length }} \u0938\u0941\u0927\u093e\u0930 \u0915\u0947 \u0932\u093f\u090f
{% if a.lessons %}
\U0001F3A7 \u0938\u0941\u0928\u0915\u0930 \u0938\u0940\u0916\u0947\u0902 \u2014 \u0939\u0930 recording \u091c\u093c\u0930\u0942\u0930 \u0938\u0941\u0928\u0947\u0902:
{% for L in a.lessons %}
{{ loop.index }}) {{ L.time }} \u00b7 {{ L.name or L.phone }} ({{ L.phone }})
   \u0906\u092a\u0928\u0947 \u0926\u0930\u094d\u091c \u0915\u093f\u092f\u093e: {{ L.filed_h }} \u274C
   \u0938\u0939\u0940 outcome: {{ L.correct_h }} \u2705{% if L.why %}
   \u0915\u094d\u092f\u094b\u0902: {{ L.why }}{% endif %}{% if L.quote %}
   \u092e\u0930\u0940\u091c\u093c \u0915\u0947 \u0936\u092c\u094d\u0926: "{{ L.quote }}"{% endif %}
   \U0001F3A7 \u0938\u0941\u0928\u0947\u0902: {{ base }}/portal/rl/{{ L.jk }}/{{ L.sig }}
{% endfor %}{% endif %}{% if a.notfiled %}
\u26A0\uFE0F \u0906\u091c \u0926\u0930\u094d\u091c \u0928\u0939\u0940\u0902 \u0939\u0941\u0908\u0902: {{ a.notfiled|length }} \u0915\u0949\u0932 ({{ a.notfiled|join(' \u00b7 ') }}){% endif %}
\u0939\u0930 \u0915\u0949\u0932 \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902 \u2014 \u0907\u0938\u0940 \u0938\u0947 \u0939\u092e \u0938\u092c \u092c\u0947\u0939\u0924\u0930 \u0939\u094b\u0924\u0947 \u0939\u0948\u0902 \U0001F44D</div>
  </div>
  {% endfor %}
</div></body></html>
"""


@app.route("/portal/console/staffreport")
@doctor_required
def console_staffreport():
    """S171 v3: the daily per-staff coaching report (page + Hindi WhatsApp + CSV)."""
    day = (request.args.get("day") or "").strip()
    if not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", day or ""):
        day = datetime.datetime.now().strftime("%Y-%m-%d")
    agents = []
    conn = _console_conn()
    if conn is not None:
        try:
            disp, sbm = _reviews_maps()
            agents = _coach_data(conn, day, disp, sbm)
        finally:
            conn.close()
    if (request.args.get("fmt") or "") == "csv":
        import csv as _csv, io as _io
        buf = _io.StringIO(); w = _csv.writer(buf)
        w.writerow(["Agent", "Calls", "Answered", "Filed", "Filed %",
                    "Lessons", "Not filed"])
        for a in agents:
            w.writerow([a["agent"], a["total"], a["answered"], a["filed"],
                        a["pct"], len(a["lessons"]), len(a["notfiled"])])
        resp = make_response("\ufeff" + buf.getvalue())
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = \
            "attachment; filename=staff_report_%s.csv" % day
        return resp
    try:
        day_h = datetime.datetime.strptime(day, "%Y-%m-%d").strftime("%a, %d %b")
    except Exception:
        day_h = day
    return render_template_string(STAFFREPORT_HTML, agents=agents, day=day,
                                  day_h=day_h, hi_out=_hi_out,
                                  base="https://followup.dr-manoj.in")


@app.route("/portal/rl/<jk>/<sig>")
def portal_rec_link(jk, sig):
    """Staff recording-only link: HMAC-signed, serves the MP3 (or Drive redirect).
    No portal session needed; the signature is the credential; nothing else reachable."""
    import hmac as _hmac
    if not _hmac.compare_digest(sig or "", _rl_sig(jk)):
        return ("link invalid", 403)
    return _serve_rec(jk)


@app.route("/portal/console/reviews.csv")
@doctor_required
def console_reviews_csv():
    """W2 Item 5: THE training export -- my label beside the AI's, with the
    transcript. One place, one file (doctor-gated, PHI stays on the VPS)."""
    import csv as _csv, io as _io
    buf = _io.StringIO(); w = _csv.writer(buf)
    w.writerow(["Join Key", "Date", "Time", "Number", "Staff", "Claimed Outcome",
                "AI Outcome", "AI Reason", "Evidence", "Doctor Final", "Doctor Note",
                "Refereed At", "Transcript"])
    disp, _ = _reviews_maps()
    conn = _console_conn()
    if conn is not None and disp:
        try:
            qmarks = ",".join(["?"] * len(disp))
            sql = (_LOG_COLS + _LOG_FROM +
                   "WHERE c.join_key IN (%s) ORDER BY c.ended_at_ist DESC" % qmarks)
            for r in conn.execute(sql, list(disp.keys())):
                row = _log_row(r); d = disp.get(row["join_key"], {})
                w.writerow([row["join_key"], row["date"], row["time"], row["phone10"],
                            row["agent"], row["claimed"], row["ai_outcome"],
                            row["ai_reason"], row["evidence"],
                            d.get("final_outcome", ""), d.get("note", ""), d.get("at", ""),
                            row["tx_text"]])
        finally:
            conn.close()
    resp = make_response("\ufeff" + buf.getvalue())   # S171: BOM so Excel renders Hindi
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=doctor_reviews_training.csv"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/portal/console")
@doctor_required
def console_page():
    f = _console_filters(request.args)
    view = f["view"] if f["view"] in ("log", "threads", "staff", "leads", "pipe", "noshows") else "log"
    m = _console_meta()
    ctx = dict(m=m, f=f, view=view, stale_min=CONSOLE_STALE_MIN, agents=[],
               fac={"direction": {}, "answered": {}, "agent": {}},
               flag_opts=[(k, _FLAG_LABEL[k]) for k in _FLAG_COLS],
               day_groups=[], total=0, more=False, limit=_LOG_LIMIT,
               convs=[], staff=[], leads=[], pipe=None, noshows=None, sb_open=[], spam_list=[],
               conv_groups=[], lead_groups=[], ns_groups=[], ns_banner=None,
               wk_days=[], wk_matrix={}, wk_rows={}, wk_agents=[], wk_sd='',
               vocab=REVIEW_VOCAB,
               base_qs=_console_base_qs(f), full_qs=_console_base_qs(f) + "&view=" + view)
    if m["ok"]:
        conn = _console_conn()
        if conn is not None:
            try:
                disp, sbm = _reviews_maps()
                spam = _spam_phones()
                ctx["spam_list"] = sorted(spam)
                ctx["agents"] = _agent_names(conn)
                ctx["fac"] = _facets(conn, f)
                if view == "log":
                    rows, more = _query_log(conn, f)
                    _overlay_reviews(rows, disp, sbm)
                    ctx["day_groups"] = _group_by_day(rows)
                    ctx["total"] = len(rows); ctx["more"] = more
                elif view == "threads":
                    ctx["convs"] = _query_conversations(conn, f)
                    for cv in ctx["convs"]:
                        _overlay_reviews(cv.get("legs", []), disp, sbm)
                    ctx["conv_groups"] = _group_by_iso(ctx["convs"], "last_ts")
                elif view == "staff":
                    ctx["staff"] = _query_staff(conn, f)
                    disp2, sbm2 = _reviews_maps()
                    sd = (request.args.get("sd") or "").strip()
                    if not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", sd):
                        sd = datetime.datetime.now().strftime("%Y-%m-%d")
                    wk_days, wk_matrix, wk_rows = _staff_week(conn, disp2, sd)
                    for lst in wk_rows.values():
                        _overlay_reviews(lst, disp2, sbm2)
                    ctx["wk_days"], ctx["wk_matrix"], ctx["wk_sd"] = wk_days, wk_matrix, sd
                    ctx["wk_agents"] = sorted(wk_matrix.keys())
                    ctx["wk_rows"] = {"%s|%s" % k: v for k, v in wk_rows.items()}
                elif view == "leads":
                    ctx["leads"] = [l for l in _query_leads(conn, f)
                                    if l.get("phone10") not in spam]     # W3 Track M
                    for l in ctx["leads"]:
                        _overlay_reviews(l.get("legs", []), disp, sbm)
                        legs = l.get("legs", [])
                        try:
                            mx = max([int(str(g.get("duration") or 0) or 0)
                                      for g in legs] or [0])
                        except Exception:
                            mx = 0
                        ait = " ".join((g.get("ai_text") or "") for g in legs).lower()
                        l["hot"] = bool((l.get("answered") and mx >= 45)
                                        or l.get("attempts", 0) >= 2
                                        or "book" in ait or "come" in ait)
                    ctx["leads"].sort(key=lambda x: (not x.get("hot"), ), )
                    ctx["lead_groups"] = [
                        (lbl, iso, sorted(rs, key=lambda x: not x.get("hot")))
                        for lbl, iso, rs in _group_by_iso(ctx["leads"], "last_seen")]
                elif view == "pipe":
                    ctx["pipe"] = _query_pipeline(conn)
                elif view == "noshows":
                    ctx["noshows"] = _query_noshows(conn)
                    _nr = (ctx["noshows"] or {}).get("rows") or []
                    _ns_tries(conn, _nr)
                    ctx["ns_groups"] = _group_by_iso(_nr, "due_date")
                    ctx["ns_banner"] = {
                        "y": len(_nr),
                        "x": sum(1 for n in _nr if not n.get("cb_attempts")),
                        "z": sum(1 for n in _nr if n.get("cb_reached"))}
                    ctx["sb_open"] = sorted(
                        ({"join_key": k, **v} for k, v in sbm.items()),
                        key=lambda x: x["at"], reverse=True)
            finally:
                conn.close()
    ctx["hi_out"] = _hi_out
    return render_template_string(CONSOLE_HTML, **ctx)


@app.route("/portal/console.csv")
@doctor_required
def console_csv():
    import csv as _csv
    import io as _io
    f = _console_filters(request.args)
    conn = _console_conn()
    buf = _io.StringIO(); w = _csv.writer(buf)
    w.writerow(["Date", "Time", "Direction", "State", "Number", "Name", "Diagnosis",
                "Age", "Sex", "Last Visit", "Clinic ID", "Duration_s", "Staff", "Claimed Outcome",
                "Not Filed", "AI Verdict", "AI State", "AI Reason", "Evidence",
                "Transcribed At", "Judged At", "Judge Lag Min", "Your Review", "Flags",
                "Recording Link", "Has Transcript", "Join Key"])
    if conn is not None:
        try:
            rows, _ = _query_log(conn, f, limit=None)
            for r in rows:
                w.writerow([r["date"], r["time"], r["direction"], r["state"], r["phone10"],
                            r["name"], r["diagnosis"], r["age"], r["gender"], r["last_visit"], r["clinic_id"],
                            r["duration"], r["agent"], r["claimed"],
                            "YES" if r["not_filed"] else "", r["ai_text"], r["ai_state"],
                            r["ai_reason"], r["evidence"], r["tx_at"], r["judged_at"],
                            r["lag_judge"] if r["lag_judge"] is not None else "",
                            r["review_text"] if r["reviewed"] else "", "; ".join(r["flags"]),
                            r["rec_link"], "YES" if r["has_tx"] else "", r["join_key"]])
        finally:
            conn.close()
    resp = make_response("\ufeff" + buf.getvalue())   # S171: BOM so Excel renders Hindi
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=call_console.csv"
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _rotate_seed_in_config(new_seed: str) -> bool:
    """
    Best-effort rewrite of PORTAL_TOKEN_SEED in portal_config.py.
    Returns True on success. Never raises.
    """
    global TOKEN_SEED
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "portal_config.py")
    try:
        if not os.path.exists(path):
            TOKEN_SEED = new_seed
            return False
        lines = open(path, "r", encoding="utf-8").read().splitlines()
        out, found = [], False
        for ln in lines:
            if ln.strip().startswith("PORTAL_TOKEN_SEED"):
                out.append(f'PORTAL_TOKEN_SEED = "{new_seed}"')
                found = True
            else:
                out.append(ln)
        if not found:
            out.append(f'PORTAL_TOKEN_SEED = "{new_seed}"')
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        TOKEN_SEED = new_seed
        return True
    except Exception:
        TOKEN_SEED = new_seed   # in-memory rotation still invalidates devices
        return False


if __name__ == "__main__":
    # Dev only. Production uses gunicorn (see systemd unit).
    app.run(host="127.0.0.1", port=8090, debug=False)
