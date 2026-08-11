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
import hashlib
import secrets
import urllib.request
import urllib.parse
from functools import wraps
from flask import (
    Flask, request, redirect, make_response, render_template_string, abort
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
     "desc": "Call log \u00b7 staff \u00b7 net-missed \u00b7 leads", "live": True,
     "url": "/portal/console",
     "roles": ["doctor"]},

    {"icon": "\U0001F4DE", "name": "Call Tracker",
     "desc": "Calls, follow-ups, dashboard", "live": True,
     "url": "https://script.google.com/macros/s/AKfycbyoQ5R3yvFC0B8arOnVWo4002BFfBGIVM2cBwpaMwUM4GaYw7d89jk1U_g38Ht0omcF/exec",
     "roles": ["doctor"]},

    {"icon": "\U0001F465", "name": "Attendance",
     "desc": "Punches & monthly report", "live": True,
     "url": "https://attendance.dr-manoj.in",
     "roles": ["doctor", "manager", "staff"]},

    {"icon": "\U0001F4C5", "name": "Staff Register",
     "desc": "Pending review \u2014 entries & approvals", "live": True,
     "url": "https://attendance.dr-manoj.in/register/review",
     "review_counts": True,
     "roles": ["doctor", "manager", "staff"]},

    {"icon": "\U0001F4B0", "name": "Salary \u2014 approve & lock",
     "desc": "Stage-B salary: preview, approve, lock", "live": True,
     "url": "https://attendance.dr-manoj.in/register/salary",
     "roles": ["doctor"]},

    {"icon": "\U0001F5C2\uFE0F", "name": "Staff Ledger",
     "desc": "Staff money events & approvals", "live": True,
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

    {"icon": "\U0001F511", "name": "Manage Users",
     "desc": "Logins: add, role, password, active, remove", "live": True,
     "url": "https://followup.dr-manoj.in/portal/users",
     "roles": []},   # manoj-only: shown via USER_TILE_EXTRA + guarded by the route

    {"icon": "\U0001F4F1", "name": "WhatsApp Approvals",
     "desc": "\u26A0 blocked \u2014 vendor (Lokesh)", "live": True,
     "url": "https://followup.dr-manoj.in/wa-approve",
     "roles": ["doctor"]},

    {"icon": "\U0001F4B3", "name": "UPI Reconciliation",
     "desc": "Clinic / pharmacy / lab vs bank", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc",
     "roles": ["doctor"]},

    {"icon": "\U0001F697", "name": "Vehicle Tracking",
     "desc": "Track360 \u2014 2 vehicles", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc/edit?gid=762286425#gid=762286425",
     "roles": ["doctor"]},

    {"icon": "\U0001F4C8", "name": "Monthly Accounting",
     "desc": "Department-wise monthly summaries", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/13eJo58J7G8n846mGlyv-pHpDILQnCrK-8ZZekyi1Hrg",
     "roles": ["doctor"]},

    {"icon": "\U0001F4B0", "name": "Daily Collections",
     "desc": "Staff daily entry sheet", "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8",
     "roles": ["doctor"]},

    {"icon": "\u2B50", "name": "GMB Review Assist",
     "desc": "Google review composer \u00b7 any device", "live": True,
     "url": "/portal/gmb", "roles": ["doctor"]},

    # --- HELD / MANUAL (doctor only) --------------------------------------
    {"icon": "\U0001F9FE", "name": "Revenue Reconciler",
     "desc": "Local \u2014 pending VPS hosting", "live": False, "url": "", "roles": ["doctor"]},
    {"icon": "\U0001F9B4", "name": "Ayushman Finder",
     "desc": "Local \u2014 pending hosting", "live": False, "url": "", "roles": ["doctor"]},
    {"icon": "\U0001F4F1", "name": "WABA Send",
     "desc": "Held \u2014 pending hosting + verify-gate", "live": False, "url": "", "roles": ["doctor"]},
    {"icon": "\U0001F4CB", "name": "Surgical Estimate",
     "desc": "Manual \u2014 open Excel for now", "live": False, "url": "", "roles": ["doctor"]},
    {"icon": "\U0001F957", "name": "Nutrition / Physio",
     "desc": "Manual \u2014 open Excel for now", "live": False, "url": "", "roles": ["doctor"]},

    # ===================== CLINIC PC ONLY  (Group D) ========================
    # These open localhost apps that resolve ONLY on the clinic PC itself, so
    # they are shown ONLY on a browser marked as the clinic PC (see /portal/mark-pc).
    # No probing -> immune to Chrome's localhost restrictions. Plain links.
    {"icon": "\U0001F9E0", "name": "Follow-up Tracker",
     "desc": "Docterz \u2192 call list \u00b7 Clinic PC", "live": True,
     "url": "http://localhost:5000", "roles": ["doctor"], "pc_only": True},

    {"icon": "\U0001FA7A", "name": "Vitals & Plan",
     "desc": "clinic_writer v28 \u00b7 Clinic PC", "live": True,
     "url": "http://localhost:5057", "roles": ["doctor"], "pc_only": True},

    {"icon": "\U0001F4CB", "name": "Surgical Case Pack",
     "desc": "Pre-surgical paperwork \u00b7 Clinic PC", "live": True,
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
     "desc": "Payment register & renewals", "live": bool(INBOX_JANITOR_URL),
     "url": INBOX_JANITOR_URL, "roles": ["doctor"]},

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
GROUP_ORDER = ["Clinic", "Money & Accounts", "Clinic PC tools",
               "Personal", "Health", "Coming soon", "Admin"]

_TILE_GROUP = {
    "Clinic Gist": "Clinic",
    "Call Console": "Clinic", "Call Tracker": "Clinic", "Attendance": "Clinic", "Asset Register": "Clinic",
    "WhatsApp Approvals": "Clinic", "GMB Review Assist": "Clinic",
    "Staff Register": "Clinic",
    "Salary \u2014 approve & lock": "Money & Accounts", "Staff Ledger": "Money & Accounts",
    "Staff Ledger \u2014 Entry": "Money & Accounts",
    "UPI Reconciliation": "Money & Accounts", "Monthly Accounting": "Money & Accounts",
    "Daily Collections": "Money & Accounts", "Vehicle Tracking": "Money & Accounts",
    "Follow-up Tracker": "Clinic PC tools", "Vitals & Plan": "Clinic PC tools",
    "Surgical Case Pack": "Clinic PC tools", "CC Statements \u2192 Tally": "Clinic PC tools",
    "CC Statement Saver": "Personal", "Inbox Janitor": "Personal",
    "RxGuard": "Health", "GutLog": "Health", "FitLog": "Health",
    "Revenue Reconciler": "Coming soon", "Ayushman Finder": "Coming soon",
    "WABA Send": "Coming soon", "Surgical Estimate": "Coming soon",
    "Nutrition / Physio": "Coming soon",
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
    "bhawna": {"GMB Review Assist", "Vitals & Plan", "Surgical Case Pack",
               "CC Statements \u2192 Tally", "Follow-up Tracker"},
}
USER_TILE_EXTRA = {
    "shavez": {"Asset Register"},
    "manoj": {"Manage Users"},
}


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

PORTAL_HTML = PAGE_HEAD + """
<div class="wrap">
  <div class="head">
    <h1>🏥 Clinic Portal</h1>
    {% if who %}<span class="sub">Signed in as {{ who.user }} ({{ who.role }})</span>
    {% else %}<span class="sub">Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre</span>{% endif %}
  </div>
  {% for label, items in sections %}
  <div class="sec">{{ label }}</div>
  <div class="grid">
  {% for t in items %}
    {% if t.live %}
      <a class="tile live" href="{{ t.url }}" target="_blank" rel="noopener">
        <div class="ic">{{ t.icon }}</div>
        <div class="nm">{{ t.name }}</div>
        <div class="ds"{% if t.review_counts %} data-review-counts{% endif %}{% if t.gist %} data-gist-summary{% endif %}>{{ t.desc }}</div>
        <span class="tag l">OPEN</span>
      </a>
    {% else %}
      <div class="tile held" title="Not yet hosted">
        <div class="ic">{{ t.icon }}</div>
        <div class="nm">{{ t.name }}</div>
        <div class="ds">{{ t.desc }}</div>
        <span class="tag h">MANUAL</span>
      </div>
    {% endif %}
  {% endfor %}
  </div>
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
<script>
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
    """Mirror home(): a trusted device with no SSO user is treated as the doctor."""
    who = _sso_user(req)
    role = who["role"] if who else "doctor"
    return role == "doctor"


def doctor_required(view):
    @wraps(view)
    def wrapper(*a, **k):
        if not _authed(request):
            return redirect("/portal/login")
        if not _is_doctor(request):
            abort(403)
        return view(*a, **k)
    return wrapper


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
       "outcome_tf, match_confidence, spoke_with, conduct_note, status, error, "
       "doctor_flag, doctor_note, final_outcome, recording_link, flag_postop, "
       "flag_complaint, flag_urgent, flag_surgery, flag_clinical, flag_conduct "
       "FROM verdicts WHERE join_key<>'' GROUP BY join_key)")
_DP = ("(SELECT phone10, MAX(rowid) AS _pid, name, diagnosis, last_visit, "
       "patient_uid, clinic_id FROM patients WHERE phone10<>'' GROUP BY phone10)")

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
    "COALESCE(p.diagnosis,'') AS diagnosis, "
    "COALESCE(v.claimed_outcome,'') AS claimed, COALESCE(v.not_filed,0) AS not_filed, "
    "COALESCE(v.ai_outcome,'') AS ai_outcome, COALESCE(v.verdict,'') AS verdict, "
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
        ai_state, ai_text = "pending", "pending"
    else:
        ai_state, ai_text = "na", ""
    # --- your review (doctor) ---
    fo = (r["final_outcome"] or "").strip(); dn = (r["doctor_note"] or "").strip()
    df = (r["doctor_flag"] or "").strip()
    reviewed = bool(fo or dn or df)
    review_text = fo or df or ("noted" if dn else "")
    return {
        "date": date, "time": time, "direction": direction, "state": state,
        "phone10": number, "name": r["name"] or "",
        "diagnosis": r["diagnosis"] or "", "duration": r["total_duration"] or "",
        "agent": agent, "last_visit": r["last_visit"] or "",
        "clinic_id": r["clinic_id"] or "", "patient_uid": r["patient_uid"] or "",
        "claimed": r["claimed"] or "", "not_filed": (r["not_filed"] == 1),
        "ai_outcome": ai, "verdict": r["verdict"] or "", "otf": r["otf"] or "",
        "ai_state": ai_state, "ai_text": ai_text,
        "doctor_note": dn, "reviewed": reviewed, "review_text": review_text,
        "conduct_note": (r["conduct_note"] or "").strip(),
        "has_jk": has_jk, "has_verdict": has_verdict,
        "flags": flags, "rec_link": r["rec_link"] or "",
        "tx_text": tx_text, "has_tx": bool(tx_text), "join_key": r["join_key"] or "",
    }


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
            w.append("c.direction='In' AND c.answered=0 AND c.phone10 IN "
                     "(SELECT phone10 FROM conversations WHERE net_missed_open=1)")
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
    fac["answered"]["netmissed"] = _count(
        conn, base_w + " AND c.direction='In' AND c.answered=0 AND c.phone10 IN "
        "(SELECT phone10 FROM conversations WHERE net_missed_open=1)", base_p)
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
           "COALESCE(p.diagnosis,'') AS diagnosis FROM conversations cv "
           "LEFT JOIN patients p ON p.phone10=cv.phone10 AND cv.phone10<>'' "
           + where + " ORDER BY cv.net_missed_open DESC, cv.last_ts DESC LIMIT 400")
    convs = []
    for r in conn.execute(sql, p):
        legs = [_log_row(lr) for lr in conn.execute(
            _LOG_COLS + _LOG_FROM + "WHERE c.phone10=? ORDER BY c.ended_at_ist ASC", [r["phone10"]])]
        d0, t0 = _split_dt(r["first_ts"]); d1, t1 = _split_dt(r["last_ts"])
        convs.append({
            "phone10": r["phone10"] or "", "name": r["name"] or "",
            "diagnosis": r["diagnosis"] or "", "attempts": r["attempts"],
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


CONSOLE_HTML = PAGE_HEAD + """
{% macro detail(r) %}
<div class="detail">
  <div class="dname"><b>{{ r.name or 'Unknown caller' }}</b>{% if r.diagnosis %} \u00b7 <span class="dx">{{ r.diagnosis }}</span>{% endif %}</div>
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
    {% elif r.ai_state=='pending' %}<span class="muted">pending judgement</span>
    {% else %}\u2014{% endif %}
    <span class="dlab">Your review</span>
    {% if r.reviewed %}<span class="pillv T">{{ r.review_text or 'reviewed' }}</span>{% else %}<span class="muted">not reviewed</span>{% endif %}
  </div>
  {% if r.flags %}<div class="drow"><span class="dlab">Flags</span>{% for fl in r.flags %}<span class="flag">{{ fl }}</span>{% endfor %}</div>{% endif %}
  {% if r.doctor_note %}<div class="drow"><span class="dlab">My note</span><span class="muted">{{ r.doctor_note }}</span></div>{% endif %}
  <div class="drow">
    {% if r.rec_link %}<a class="lnk" href="{{ r.rec_link }}" target="_blank" rel="noopener">\u25B6 recording</a>{% endif %}
    {% if not r.rec_link and r.state=='Answered' %}<span class="muted">no recording link</span>{% endif %}
  </div>
  {% if r.tx_text %}<div class="txbox"><b>Transcript</b><br>{{ r.tx_text }}</div>{% endif %}
</div>
{% endmacro %}

{% macro rowsummary(r) %}
  <span class="mono">{{ r.time }}</span>
  <span class="dir {{ r.direction }}">{{ r.direction }}</span>
  <span class="st {{ r.state }}">{{ r.state }}</span>
  <span class="mono numw">{{ r.phone10 or '\u2014' }}</span>
  <span class="namew">{{ r.name or '\u2014' }}</span>
  <span class="agw">{{ r.agent or '\u2014' }}</span>
  {% if r.not_filed %}<span class="amber">NOT FILED</span>{% endif %}
  {% if r.ai_state=='ok' %}<span class="pillv U">{{ r.ai_text }}</span>{% elif r.ai_state=='pending' %}<span class="muted sm">pending</span>{% elif r.ai_state=='error' %}<span class="pillv F">err</span>{% endif %}
  {% if r.reviewed %}<span class="pillv T sm">reviewed</span>{% endif %}
  {% if r.has_tx %}<span class="txmark">tx</span>{% endif %}
{% endmacro %}
<style>
.cwrap{max-width:1180px}
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
.muted{color:var(--muted)} .sm{font-size:10px} .mono{font-variant-numeric:tabular-nums}
.lnk{color:#93c5fd;text-decoration:none;font-size:12.5px}.lnk:hover{text-decoration:underline}
.dir{font-weight:700;font-size:11px;padding:2px 7px;border-radius:6px}
.dir.In{background:rgba(59,130,246,.16);color:#93c5fd}.dir.Out{background:rgba(91,113,132,.22);color:#cbd5e1}
.st{font-size:11px;font-weight:600}.st.Answered{color:#86efac}.st.Missed{color:#fca5a5}
.amber{background:rgba(234,179,8,.16);color:#fde68a;font-size:10px;font-weight:700;padding:2px 7px;border-radius:6px}
.pillv{font-size:10px;font-weight:700;padding:2px 7px;border-radius:6px}
.pillv.T{background:rgba(34,197,94,.16);color:#86efac}.pillv.F{background:rgba(239,68,68,.16);color:#fca5a5}
.pillv.U{background:rgba(59,130,246,.16);color:#93c5fd}.pillv.mut{background:rgba(91,113,132,.25);color:#b8c7d6}
.flag{display:inline-block;font-size:10px;font-weight:700;padding:1px 6px;border-radius:6px;margin:1px 2px 1px 0;background:rgba(239,68,68,.14);color:#fca5a5}
.txmark{font-size:10px;font-weight:700;color:#86efac;background:rgba(34,197,94,.12);padding:1px 6px;border-radius:6px}
/* day + call rows */
details.day{margin-bottom:8px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:rgba(22,50,74,.35)}
details.day>summary{cursor:pointer;list-style:none;padding:11px 14px;font-weight:700;font-size:13px;color:#fff;background:var(--card);display:flex;gap:12px;align-items:center}
details.day>summary::-webkit-details-marker{display:none}
details.day>summary .dcount{font-size:11px;color:var(--muted);font-weight:600;margin-left:auto}
details.callrow{border-top:1px solid rgba(39,75,102,.5)}
details.callrow>summary{cursor:pointer;list-style:none;padding:8px 14px;display:flex;flex-wrap:wrap;gap:9px;align-items:center;font-size:12.5px}
details.callrow>summary::-webkit-details-marker{display:none}
details.callrow[open]>summary{background:rgba(59,130,246,.07)}
details.callrow:hover>summary{background:rgba(59,130,246,.05)}
.numw{min-width:96px}.namew{min-width:120px}.agw{min-width:90px;color:var(--muted)}
/* conversation / lead groups */
details.conv{background:var(--card);border:1px solid var(--line);border-radius:11px;margin-bottom:8px}
details.conv[open]{border-color:var(--blue)}
details.conv>summary{cursor:pointer;list-style:none;padding:11px 13px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;font-size:12.5px}
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
      {% for key,lbl in [('log','Call log'),('threads','Conversations'),('staff','Staff'),('leads','New leads')] %}
        <a class="{{ 'on' if view==key else '' }}" href="/portal/console?view={{key}}&{{ base_qs }}">{{ lbl }}</a>
      {% endfor %}
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
          <option value="netmissed" {{ 'selected' if f.answered=='netmissed' else '' }}>Net-missed open ({{ fac.answered.get('netmissed',0) }})</option>
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
      <div class="summ">{{ total }} calls{% if more %} \u2014 showing newest {{ limit }}; narrow filters or export CSV for all{% endif %}. Click a day, then a call, to expand.</div>
      {% for day, drows in day_groups %}
        <details class="day" {% if loop.first %}open{% endif %}>
          <summary>{{ day }}<span class="dcount">{{ drows|length }} calls</span></summary>
          {% for r in drows %}
            <details class="callrow"><summary>{{ rowsummary(r) }}</summary>{{ detail(r) }}</details>
          {% endfor %}
        </details>
      {% endfor %}
      {% if not day_groups %}<div class="muted" style="padding:18px">No calls match these filters.</div>{% endif %}

    {% elif view=='threads' %}
      <div class="summ">{{ convs|length }} conversations (net-missed-open first). Click to expand attempts.</div>
      {% for cv in convs %}
        <details class="conv">
          <summary>
            {% if cv.net_open %}<span class="netbadge">NET-MISSED</span>{% elif cv.any_connected %}<span class="okbadge">connected</span>{% endif %}
            <span class="mono" style="font-weight:600">{{ cv.phone10 }}</span>
            <span>{{ cv.name or 'Unknown' }}</span><span class="muted">{{ cv.diagnosis or '' }}</span>
            <span class="muted" style="margin-left:auto">{{ cv.attempts }} attempts \u00b7 {{ cv.miss_attempts }} missed \u00b7 last {{ cv.last_ts }}{% if cv.last_agent %} \u00b7 {{ cv.last_agent }}{% endif %}</span>
          </summary>
          {% for lg in cv.legs %}{{ detail(lg) }}{% endfor %}
        </details>
      {% endfor %}
      {% if not convs %}<div class="muted" style="padding:18px">No conversations match.</div>{% endif %}

    {% elif view=='staff' %}
      <div class="summ">Per-agent{% if f.frm or f.to %} ({{ f.frm or '\u2026' }} to {{ f.to or '\u2026' }}){% endif %}. Click an agent to filter the log.</div>
      <table class="log"><thead><tr><th>Agent</th><th>In answered</th><th>Out attempts</th><th>Handled</th><th>Not filed</th><th>Verdict TRUE</th><th>Verdict FALSE</th><th>Flags</th></tr></thead><tbody>
      {% for s in staff %}<tr>
        <td><a class="lnk" href="/portal/console?view=log&agent={{ s.agent|urlencode }}">{{ s.agent }}</a></td>
        <td class="mono">{{ s.in_handled }}</td><td class="mono">{{ s.out_attempts }}</td>
        <td class="mono">{{ s.in_handled + s.out_attempts }}</td>
        <td class="mono">{% if s.not_filed %}<span class="amber">{{ s.not_filed }}</span>{% else %}0{% endif %}</td>
        <td class="mono">{{ s.vtrue }}</td><td class="mono">{{ s.vfalse }}</td><td class="mono">{{ s.flags }}</td>
      </tr>{% endfor %}
      </tbody></table>

    {% elif view=='leads' %}
      <div class="summ">{{ leads|length }} unknown incoming numbers (not in Patient_Master) \u2014 first-time enquiries (D243). Click to expand attempts.</div>
      {% for l in leads %}
        <details class="conv">
          <summary>
            {% if l.answered %}<span class="okbadge">reached</span>{% else %}<span class="netbadge">not reached</span>{% endif %}
            <span class="mono" style="font-weight:600">{{ l.phone10 }}</span>
            <span class="muted" style="margin-left:auto">{{ l.attempts }} attempt(s) \u00b7 first {{ l.first_seen }} \u00b7 latest {{ l.last_seen }}{% if l.last_agent %} \u00b7 {{ l.last_agent }}{% endif %}</span>
          </summary>
          {% for lg in l.legs %}{{ detail(lg) }}{% endfor %}
        </details>
      {% endfor %}
      {% if not leads %}<div class="muted" style="padding:18px">No new leads in range.</div>{% endif %}
    {% endif %}

    <div class="summ" style="margin-top:16px">Built {{ m.built_at or 'unknown' }}{% if m.age_min is not none %} \u00b7 {{ m.age_min }} min ago{% endif %}.</div>
  {% endif %}
</div></body></html>
"""


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


@app.route("/portal/console")
@doctor_required
def console_page():
    f = _console_filters(request.args)
    view = f["view"] if f["view"] in ("log", "threads", "staff", "leads") else "log"
    m = _console_meta()
    ctx = dict(m=m, f=f, view=view, stale_min=CONSOLE_STALE_MIN, agents=[],
               fac={"direction": {}, "answered": {}, "agent": {}},
               flag_opts=[(k, _FLAG_LABEL[k]) for k in _FLAG_COLS],
               day_groups=[], total=0, more=False, limit=_LOG_LIMIT,
               convs=[], staff=[], leads=[],
               base_qs=_console_base_qs(f), full_qs=_console_base_qs(f) + "&view=" + view)
    if m["ok"]:
        conn = _console_conn()
        if conn is not None:
            try:
                ctx["agents"] = _agent_names(conn)
                ctx["fac"] = _facets(conn, f)
                if view == "log":
                    rows, more = _query_log(conn, f)
                    ctx["day_groups"] = _group_by_day(rows)
                    ctx["total"] = len(rows); ctx["more"] = more
                elif view == "threads":
                    ctx["convs"] = _query_conversations(conn, f)
                elif view == "staff":
                    ctx["staff"] = _query_staff(conn, f)
                elif view == "leads":
                    ctx["leads"] = _query_leads(conn, f)
            finally:
                conn.close()
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
                "Last Visit", "Clinic ID", "Duration_s", "Staff", "Claimed Outcome",
                "Not Filed", "AI Verdict", "AI State", "Your Review", "Flags",
                "Recording Link", "Has Transcript", "Join Key"])
    if conn is not None:
        try:
            rows, _ = _query_log(conn, f, limit=None)
            for r in rows:
                w.writerow([r["date"], r["time"], r["direction"], r["state"], r["phone10"],
                            r["name"], r["diagnosis"], r["last_visit"], r["clinic_id"],
                            r["duration"], r["agent"], r["claimed"],
                            "YES" if r["not_filed"] else "", r["ai_text"], r["ai_state"],
                            r["review_text"] if r["reviewed"] else "", "; ".join(r["flags"]),
                            r["rec_link"], "YES" if r["has_tx"] else "", r["join_key"]])
        finally:
            conn.close()
    resp = make_response(buf.getvalue())
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
