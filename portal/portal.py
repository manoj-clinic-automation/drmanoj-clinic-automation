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
    "Call Tracker": "Clinic", "Attendance": "Clinic", "Asset Register": "Clinic",
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
        <div class="ds"{% if t.review_counts %} data-review-counts{% endif %}>{{ t.desc }}</div>
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
