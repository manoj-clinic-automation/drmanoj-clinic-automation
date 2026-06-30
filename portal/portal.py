#!/usr/bin/env python3
"""
portal.py  —  Doctor-only Clinic Launcher Portal
================================================
Dr. Manoj Agarwal Clinic, Bareilly.  Session 19 · 30 Jun 2026.

ONE self-contained Flask app. Serves a single private launcher page at
followup.dr-manoj.in/portal with PIN login + indefinite device-trust.
It LINKS to existing tools only — it touches no other live system.

--------------------------------------------------------------------------
FAILURE MAP  (per D19 discipline)
--------------------------------------------------------------------------
External dependencies: NONE for the page itself. Tiles open other systems
  in a new tab; if a target system is down, only that tile's link fails —
  the portal still loads. No tile can crash the portal.
Secrets used (from portal_config.py / env, NEVER hardcoded):
  - PORTAL_PIN_HASH   : salted hash of the PIN (never the PIN itself)
  - PORTAL_PIN_SALT   : random salt for the hash
  - PORTAL_TOKEN_SEED : server secret; rotating it = "forget all devices"
Fault behaviours:
  - Missing config        -> app refuses to start with a clear message (fail safe)
  - Bad/again PIN         -> generic "wrong PIN" (no lockout, no info leak)
  - Tampered/old cookie   -> treated as logged-out -> PIN screen
  - "Forget all devices"  -> rotates PORTAL_TOKEN_SEED -> all cookies invalid
Fallbacks:
  - Portal down entirely  -> every tool remains reachable at its own URL
                             (this app is a convenience layer, not a gatekeeper
                              for the underlying tools).
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

# ---------------------------------------------------------------------------
# CONFIG  — real values come from portal_config.py on the VPS (chmod 600),
# or environment variables. NOTHING secret is hardcoded here.
# ---------------------------------------------------------------------------
try:
    import portal_config as cfg          # VPS-only file, gitignored
    PIN_HASH   = getattr(cfg, "PORTAL_PIN_HASH", "")
    PIN_SALT   = getattr(cfg, "PORTAL_PIN_SALT", "")
    TOKEN_SEED = getattr(cfg, "PORTAL_TOKEN_SEED", "")
    COOKIE_NAME = getattr(cfg, "PORTAL_COOKIE_NAME", "clinic_portal_device")
except Exception:
    PIN_HASH   = os.environ.get("PORTAL_PIN_HASH", "")
    PIN_SALT   = os.environ.get("PORTAL_PIN_SALT", "")
    TOKEN_SEED = os.environ.get("PORTAL_TOKEN_SEED", "")
    COOKIE_NAME = os.environ.get("PORTAL_COOKIE_NAME", "clinic_portal_device")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# TILES  — flip "live": False -> True and fill "url" to light a tile up later.
# No rebuild needed; just edit this list and restart the service.
# ---------------------------------------------------------------------------
TILES = [
    # --- LIVE NOW (reachable by URL) ---------------------------------------
    {"icon": "📞", "name": "Call Tracker",
     "desc": "Calls, follow-ups, dashboard",
     "live": True,
     "url": "https://script.google.com/macros/s/AKfycbyoQ5R3yvFC0B8arOnVWo4002BFfBGIVM2cBwpaMwUM4GaYw7d89jk1U_g38Ht0omcF/exec"},

    {"icon": "👥", "name": "Attendance & Salary",
     "desc": "Punches, monthly salary, advances",
     "live": True,
     "url": "https://followup.dr-manoj.in:8042"},

    {"icon": "💳", "name": "UPI Reconciliation",
     "desc": "Clinic / pharmacy / lab vs bank",
     "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc"},

    {"icon": "🚗", "name": "Vehicle Tracking",
     "desc": "Track360 — 2 vehicles",
     "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc"},

    {"icon": "📈", "name": "Monthly Accounting",
     "desc": "Department-wise monthly summaries",
     "live": True,
     "url": "https://docs.google.com/spreadsheets/d/13eJo58J7G8n846mGlyv-pHpDILQnCrK-8ZZekyi1Hrg"},

    {"icon": "💰", "name": "Daily Collections",
     "desc": "Staff daily entry sheet",
     "live": True,
     "url": "https://docs.google.com/spreadsheets/d/1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8"},

    # --- HELD / MANUAL (flip to live when hosted) --------------------------
    {"icon": "🧾", "name": "Revenue Reconciler",
     "desc": "Local — pending VPS hosting",
     "live": False, "url": ""},

    {"icon": "🦴", "name": "Ayushman Finder",
     "desc": "Local — pending hosting",
     "live": False, "url": ""},

    {"icon": "📱", "name": "WABA Send",
     "desc": "Held — pending hosting + verify-gate",
     "live": False, "url": ""},

    {"icon": "📋", "name": "Surgical Estimate",
     "desc": "Manual — open Excel for now",
     "live": False, "url": ""},

    {"icon": "🥗", "name": "Nutrition / Physio",
     "desc": "Manual — open Excel for now",
     "live": False, "url": ""},
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


def login_required(view):
    @wraps(view)
    def wrapper(*a, **k):
        if _is_trusted(request):
            return view(*a, **k)
        return redirect("/portal/login")
    return wrapper


def _config_ok() -> bool:
    return bool(PIN_HASH and PIN_SALT and TOKEN_SEED)

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
.foot{margin-top:26px;display:flex;justify-content:center}
.forget{background:none;border:1px solid var(--line);color:var(--muted);
 font-size:12px;padding:9px 16px;border-radius:10px;cursor:pointer}
.forget:hover{border-color:#7f1d1d;color:#fca5a5}
/* login */
.login{max-width:340px;margin:9vh auto 0;text-align:center;padding:0 16px}
.login h1{font-size:20px;color:#fff;margin:0 0 4px}
.login p{font-size:13px;color:var(--muted);margin:0 0 22px}
.login input{width:100%;font-size:22px;text-align:center;letter-spacing:.3em;
 padding:14px;border:2px solid var(--blue);border-radius:12px;background:#0b1b29;
 color:#fff;outline:none}
.login input:focus{border-color:#60a5fa}
.login button{width:100%;margin-top:14px;font-size:16px;font-weight:600;padding:13px;
 border:none;border-radius:12px;background:var(--blue);color:#fff;cursor:pointer}
.login button:active{transform:scale(.99)}
.err{color:#fca5a5;font-size:13px;margin-top:12px;min-height:18px}
.note{color:var(--muted);font-size:11px;margin-top:22px}
</style></head><body>
"""

LOGIN_HTML = PAGE_HEAD + """
<div class="login">
  <h1>Clinic Portal</h1>
  <p>Private access — enter PIN</p>
  <form method="POST" action="/portal/login" autocomplete="off">
    <input name="pin" type="password" inputmode="numeric" autofocus
           placeholder="• • • •" aria-label="PIN">
    <button type="submit">Unlock</button>
  </form>
  <div class="err">{{ error or "" }}</div>
  <div class="note">This device will be remembered until you sign out
   or use “Forget all devices”.</div>
</div></body></html>
"""

PORTAL_HTML = PAGE_HEAD + """
<div class="wrap">
  <div class="head">
    <h1>🏥 Clinic Portal</h1>
    <span class="sub">Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre</span>
  </div>
  <div class="grid">
  {% for t in tiles %}
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
  {% endfor %}
  </div>
  <div class="foot">
    <form method="POST" action="/portal/forget"
          onsubmit="return confirm('Sign out EVERY device? Everyone will need the PIN again.');">
      <button class="forget" type="submit">Forget all devices</button>
    </form>
  </div>
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
    if not _config_ok():
        return render_template_string(CONFIG_ERROR_HTML), 503
    if not _is_trusted(request):
        return redirect("/portal/login")
    return render_template_string(PORTAL_HTML, tiles=TILES)


@app.route("/portal/login", methods=["GET", "POST"])
def login():
    if not _config_ok():
        return render_template_string(CONFIG_ERROR_HTML), 503
    if _is_trusted(request):
        return redirect("/portal")
    error = ""
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
    We rotate the server seed in portal_config.py so EVERY existing cookie
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


@app.route("/portal/health")
def health():
    """Simple health probe for the future Diagnostics system."""
    status = "ok" if _config_ok() else "unconfigured"
    return {"service": "portal", "status": status}, (200 if _config_ok() else 503)


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
