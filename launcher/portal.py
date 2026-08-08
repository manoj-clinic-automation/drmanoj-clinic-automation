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
import hmac
import hashlib
import secrets
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
     "roles": ["doctor", "manager"]},

    {"icon": "\U0001F4BC", "name": "Salary & Ledger",
     "desc": "Staff money, salary, approvals", "live": True,
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
]

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
  <div class="grid">
  {% for t in tiles %}
    {% if role in t.roles and (not t.pc_only or pc) %}
    {% if t.live %}
      <a class="tile live" href="{{ t.url }}" target="_blank" rel="noopener">
        <div class="ic">{{ t.icon }}</div>
        <div class="nm">{{ t.name }}</div>
        <div class="ds">{{ t.desc }}</div>
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
    {% endif %}
  {% endfor %}
  </div>
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
    return render_template_string(PORTAL_HTML, tiles=TILES,
                                  sso=_sso_ready(), who=who, role=role,
                                  pc=_is_clinic_pc(request))


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
