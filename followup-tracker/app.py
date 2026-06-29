"""
Docterz EMR Follow-Up Tracker — Web Interface
Dr. Manoj Agarwal Clinic, Bareilly
"""

import os
import secrets
from datetime import date
from pathlib import Path
from functools import wraps

from flask import (
    Flask, request, render_template_string, redirect,
    url_for, session, send_file, flash
)
from werkzeug.utils import secure_filename

from processor import (
    run_daily, run_initial_master, OUTPUTS_DIR, DATA_DIR,
    load_vacations, save_vacations, VACATION_COLS,
)
import revenue
import concessions
from datetime import date as _date

# ── Config ────────────────────────────────────────────────────────────────────
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── Roles ─────────────────────────────────────────────────────────────────────
# STAFF  — upload daily CSVs, download Staff_Action_Today only.
# ADMIN  — everything: full audit, initialise master, vacation calendar.
# On a server (non-local) BOTH env vars are mandatory; there is no default
# password any more. The app refuses to start without them (P1-01).
STAFF_PASSWORD = os.environ.get("TRACKER_PASSWORD", "")
ADMIN_PASSWORD = os.environ.get("TRACKER_ADMIN_PASSWORD", "")

# LOCAL_MODE: when the app runs on the clinic PC (set by run_local.py), skip the
# login gate — there is no network exposure and re-logging-in daily is friction.
# Local mode runs as ADMIN (it is the doctor's own PC).
LOCAL_MODE = os.environ.get("TRACKER_LOCAL", "") == "1"

def _require_server_credentials():
    """Enforced ONLY when the app is actually served on a network (VPS).
    Never blocks the local clinic-PC launch (TRACKER_LOCAL=1), which has no
    network exposure and uses no login. Called from the server entrypoint,
    NOT at import time — importing app must never crash the launcher."""
    if LOCAL_MODE:
        return
    missing = [n for n, v in
               [("TRACKER_PASSWORD", STAFF_PASSWORD),
                ("TRACKER_ADMIN_PASSWORD", ADMIN_PASSWORD)] if not v]
    if missing:
        raise SystemExit(
            "Refusing to start: set environment variable(s) "
            + ", ".join(missing)
            + " (server deployments must not run with default credentials).")
    if STAFF_PASSWORD == ADMIN_PASSWORD:
        raise SystemExit("Refusing to start: staff and admin passwords must differ.")

app = Flask(__name__)
# Stable secret key kept in data/ so sessions survive server restarts (otherwise
# a fresh key each launch forces a re-login). Falls back to a random key.
def _stable_secret():
    env = os.environ.get("SECRET_KEY")
    if env:
        return env
    try:
        keyfile = DATA_DIR / ".secret_key"
        if keyfile.exists():
            return keyfile.read_text().strip()
        k = secrets.token_hex(32)
        keyfile.write_text(k)
        return k
    except Exception:
        return secrets.token_hex(32)
app.secret_key = _stable_secret()
app.permanent_session_lifetime = 86400  # 24 hours

ALLOWED = {"csv"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

# ── Auth ──────────────────────────────────────────────────────────────────────
def current_role() -> str:
    """'admin', 'staff', or '' (not logged in). Local PC counts as admin."""
    if LOCAL_MODE:
        return "admin"
    return session.get("role", "") if session.get("logged_in") else ""

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_role():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        role = current_role()
        if not role:
            return redirect(url_for("login"))
        if role != "admin":
            return "Admin access required", 403
        return f(*args, **kwargs)
    return decorated

# ── Templates ─────────────────────────────────────────────────────────────────
BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f0f4f8; color: #1a2940; min-height: 100vh;
  }
  .header {
    background: #1F4E79; color: white; padding: 14px 20px;
    font-size: 15px; font-weight: 600; letter-spacing: 0.3px;
  }
  .header small { display: block; font-weight: 400; font-size: 12px; opacity: 0.75; margin-top: 2px; }
  .container { max-width: 640px; margin: 30px auto; padding: 0 16px 40px; }
  .card {
    background: white; border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 24px;
    margin-bottom: 20px;
  }
  .card h2 { font-size: 16px; color: #1F4E79; margin-bottom: 16px;
    padding-bottom: 10px; border-bottom: 2px solid #DDEBF7; }
  label { display: block; font-size: 13px; font-weight: 600;
    color: #374151; margin-bottom: 5px; }
  .hint { font-size: 11.5px; color: #6B7280; margin-bottom: 10px; }
  input[type=file], input[type=password], input[type=text] {
    width: 100%; padding: 10px 12px; border: 1.5px solid #D1D5DB;
    border-radius: 7px; font-size: 14px; margin-bottom: 16px;
    background: #fafafa;
  }
  input[type=file]:focus, input[type=password]:focus {
    outline: none; border-color: #1F4E79; background: white;
  }
  .btn {
    display: inline-block; width: 100%; padding: 12px;
    background: #1F4E79; color: white; border: none;
    border-radius: 8px; font-size: 15px; font-weight: 600;
    cursor: pointer; text-align: center; text-decoration: none;
    transition: background 0.2s;
  }
  .btn:hover { background: #163a5e; }
  .btn-green { background: #166534; }
  .btn-green:hover { background: #14532d; }
  .btn-grey { background: #6B7280; }
  .btn-grey:hover { background: #4B5563; }
  .alert { padding: 12px 16px; border-radius: 8px; font-size: 13.5px;
    margin-bottom: 16px; }
  .alert-error { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
  .alert-success { background: #D1FAE5; color: #065F46; border: 1px solid #6EE7B7; }
  .alert-info { background: #DBEAFE; color: #1E40AF; border: 1px solid #93C5FD; }
  .divider { border: none; border-top: 1px solid #E5E7EB; margin: 16px 0; }
  .nav-links { font-size: 13px; margin-top: 12px; }
  .nav-links a { color: #1F4E79; text-decoration: none; margin-right: 16px; }
  .nav-links a:hover { text-decoration: underline; }
  .tag {
    display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 11px; font-weight: 600;
  }
  .tag-red { background: #FEE2E2; color: #991B1B; }
  .tag-green { background: #D1FAE5; color: #065F46; }
  .tag-blue { background: #DBEAFE; color: #1E40AF; }
  .tag-amber { background: #FEF3C7; color: #92400E; }
  .tag-grey { background: #E5E7EB; color: #374151; }
</style>
"""

CALLS_HTML = BASE_STYLE + """
<div class="header">📞 Call Monitor <small>Dr. Manoj Agarwal Clinic — follow-up call outcomes</small></div>
<div class="container">
  <div class="card">
    <h2>Calls on {{ s.date or '—' }}</h2>
    {% if s.all_dates %}
    <form method="get" action="/calls" style="margin-bottom:14px;">
      <label>Show another day</label>
      <select name="date" onchange="this.form.submit()"
        style="width:100%;padding:10px 12px;border:1.5px solid #D1D5DB;border-radius:7px;background:#fafafa;">
        {% for dt in s.all_dates %}<option value="{{dt}}" {{ 'selected' if dt==s.date else '' }}>{{dt}}</option>{% endfor %}
      </select>
    </form>
    {% endif %}
    {% if s.total %}
    <p style="font-size:14px;margin-bottom:8px;"><b>{{ s.total }}</b> calls &nbsp;
      <span class="tag tag-green">{{ s.reached }} reached</span>
      <span class="tag tag-red">{{ s.not_reached }} not reached</span>
      &nbsp; contact rate <b>{{ s.contact_rate }}%</b></p>
    {% else %}
    <p class="hint">No calls recorded for this day yet.</p>
    {% endif %}
    <p class="hint" style="margin-top:6px;">Still pending (actionable follow-ups with no outcome yet):
      <b>{{ s.pending }}</b></p>
  </div>

  {% if s.by_response %}
  <div class="card">
    <h2>By response</h2>
    {% for k,v in s.by_response %}
      <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>{{k}}</span><b>{{v}}</b></div>
    {% endfor %}
  </div>
  {% endif %}

  {% if s.by_staff %}
  <div class="card">
    <h2>By staff member</h2>
    <div style="display:flex;justify-content:space-between;font-size:12px;color:#6B7280;padding-bottom:6px;"><span>Caller</span><span>calls &middot; reached</span></div>
    {% for staff,calls,reached in s.by_staff %}
      <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>{{staff}}</span><b>{{calls}} &middot; {{reached}}</b></div>
    {% endfor %}
  </div>
  {% endif %}

  {% if rec and rec.called %}
  <div class="card">
    <h2>Cross-check vs actual returns</h2>
    <p class="hint" style="margin-bottom:10px;">From who was actually seen in the consultation reports — across all follow-ups, not just one day.</p>
    <p style="font-size:14px;margin-bottom:10px;">Of <b>{{ rec.called }}</b> patients called, <b>{{ rec.called_returned }}</b> actually returned &nbsp;
      <span class="tag tag-green">call &rarr; return {{ rec.call_return_rate }}%</span></p>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>Said "coming" but not back yet</span><b>{{ rec.unfulfilled_promise }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>Said done / elsewhere, no return <span class="hint">(review)</span></span><b>{{ rec.self_resolved_no_return }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>Declined</span><b>{{ rec.declined }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>Unreachable (escalated)</span><b>{{ rec.unreached }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;"><span>Returned without a call <span class="hint">(organic)</span></span><b>{{ rec.organic_return }}</b></div>
  </div>
  {% endif %}

  <div class="nav-links"><a href="/">&larr; Back to home</a></div>
</div>
"""

AUDIT_HTML = BASE_STYLE + """
<div class="header">🔎 Call Audit <small>Dr. Manoj Agarwal Clinic — claimed calls vs IVR telephony</small></div>
<div class="container">
  <div class="card">
    <h2>Telephony</h2>
    {% if msg %}<p style="color:#166534;font-size:13.5px;margin-bottom:8px;">✅ {{ msg }}</p>{% endif %}
    {% if err %}<p style="color:#B91C1C;font-size:13.5px;margin-bottom:8px;">⚠️ {{ err }}</p>{% endif %}
    {% if feed_on %}
      <form method="POST" action="/callaudit" style="margin-bottom:8px;">
        <input type="hidden" name="action" value="refresh">
        <button class="btn" type="submit">↻ Refresh from Google</button>
      </form>
      <p class="hint">Pulls the latest calls straight from the Call_Feed — no download, no upload.
        It also refreshes automatically on each evening run.</p>
    {% else %}
      <p class="hint" style="margin-bottom:8px;">One-time setup turns this into a single button: publish the
        <b>Call_Feed</b> tab (File → Share → Publish to web → Call_Feed → CSV) and save the link in
        <code>data/feed_url.txt</code>. Until then, upload the file below.</p>
    {% endif %}
    <details style="margin-top:8px;">
      <summary class="hint" style="cursor:pointer;">or upload a Call_Feed / Outbound_Log file</summary>
      <form method="POST" action="/callaudit" enctype="multipart/form-data" style="margin-top:8px;">
        <input type="file" name="outbound_xlsx" accept=".csv,.xlsx,.xlsm"
          style="width:100%;padding:9px;border:1.5px solid #D1D5DB;border-radius:7px;background:#fafafa;margin-bottom:10px;">
        <button class="btn btn-grey" type="submit">Upload &amp; reconcile</button>
      </form>
    </details>
    <p class="hint" style="margin-top:8px;">{{ rec.meta.calls }} logged outcomes &middot; {{ rec.meta.outbound }} outbound calls on file.
      Advisory only — it never changes your call sheet or ledger.</p>
  </div>

  <div class="card">
    <h2>Summary</h2>
    {% if rec.meta.no_outbound %}<p class="hint" style="margin-bottom:10px;">No outbound calls loaded yet — upload today's Outbound_Log above to reconcile.</p>{% endif %}
    {% set c = rec.counts %}
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>✅ Consistent with IVR</span><b>{{ c.consistent or 0 }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>🟥 Logged, but no IVR call</span><b>{{ c.logged_no_call or 0 }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>🟧 Claims reached, no call connected</span><b>{{ c.claims_reached_no_connect or 0 }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>🟨 Claims no-answer, but connected</span><b>{{ c.claims_noanswer_but_connected or 0 }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;"><span>🟦 Caller name mismatch</span><b>{{ c.agent_mismatch or 0 }}</b></div>
    <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;"><span>⬜ IVR called, not logged</span><b>{{ c.call_not_logged or 0 }}</b></div>
  </div>

  {% if reinstates %}
  <div class="card">
    <h2>Reinstated callbacks <span class="tag tag-red">{{ reinstates|length }}</span></h2>
    <p class="hint" style="margin-bottom:10px;">Logged NOT PICK but the line connected — callback reinstated on the
      sheet, named to the caller. It clears on its own when the patient is genuinely reached or returns.
      {% if role == 'admin' %}Listen to the recording on MyOperator, then clear here once you've judged it.{% endif %}</p>
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
      <tr style="text-align:left;color:#6B7280;border-bottom:1.5px solid #E5E7EB;">
        <th style="padding:6px 8px;">Patient</th><th style="padding:6px 8px;">Caller</th>
        <th style="padding:6px 8px;">Call</th>{% if role == 'admin' %}<th style="padding:6px 8px;"></th>{% endif %}
      </tr>
      {% for x in reinstates %}
      <tr style="border-bottom:1px solid #F1F5F9;">
        <td style="padding:6px 8px;"><b>{{ x.Patient_Name or '—' }}</b><br><span class="hint">{{ x.Mobile }}</span></td>
        <td style="padding:6px 8px;">{{ x.Orig_Caller or '—' }}</td>
        <td style="padding:6px 8px;">{{ x.Connect_Info }}</td>
        {% if role == 'admin' %}<td style="padding:6px 8px;">
          <form method="POST" action="/callaudit" style="margin:0;">
            <input type="hidden" name="action" value="clear_reinstate">
            <input type="hidden" name="reinstate_id" value="{{ x.Reinstate_ID }}">
            <button class="btn btn-grey" type="submit" style="padding:5px 10px;font-size:12px;">Clear</button>
          </form></td>{% endif %}
      </tr>
      {% endfor %}
    </table>
    </div>
  </div>
  {% endif %}

  {% set flagged = rec.rows | selectattr('flag','ne','consistent') | list %}
  {% if flagged %}
  <div class="card">
    <h2>Needs a look ({{ flagged|length }})</h2>
    <p class="hint" style="margin-bottom:10px;">Consistent rows are hidden. “Connected/missed” is judged on the call <i>status</i>, not its length.</p>
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
      <tr style="text-align:left;color:#6B7280;border-bottom:1.5px solid #E5E7EB;">
        <th style="padding:6px 8px;">Patient</th><th style="padding:6px 8px;">Date</th>
        <th style="padding:6px 8px;">Logged</th><th style="padding:6px 8px;">By</th>
        <th style="padding:6px 8px;">IVR</th><th style="padding:6px 8px;">What to check</th>
      </tr>
      {% for r in flagged %}
      <tr style="border-bottom:1px solid #F1F5F9;">
        <td style="padding:6px 8px;"><b>{{ r.name or '—' }}</b><br><span class="hint">{{ r.mobile }}</span></td>
        <td style="padding:6px 8px;white-space:nowrap;">{{ r.date }}</td>
        <td style="padding:6px 8px;">{{ r.response or '—' }}</td>
        <td style="padding:6px 8px;">{{ r.called_by or '—' }}</td>
        <td style="padding:6px 8px;">{{ r.attempts }} call{{ '' if r.attempts==1 else 's' }}{% if r.attempts %}, {{ 'connected' if r.connected else 'all missed' }}{% endif %}{% if r.ivr_agents %}<br><span class="hint">{{ r.ivr_agents }}</span>{% endif %}</td>
        <td style="padding:6px 8px;">{{ r.note }}</td>
      </tr>
      {% endfor %}
    </table>
    </div>
  </div>
  {% endif %}

  {% if rec.agent %}
  <div class="card">
    <h2>Per caller — logged vs IVR</h2>
    <p class="hint" style="margin-bottom:10px;">IVR calls counted here are calls to follow-up patients only. Ranjeet isn't on the IVR
      (his calls fall under Reception Mobile).</p>
    <div style="display:flex;justify-content:space-between;font-size:12px;color:#6B7280;padding-bottom:6px;border-bottom:1px solid #E5E7EB;"><span>Caller</span><span>logged &middot; IVR calls &middot; connected</span></div>
    {% for a in rec.agent %}
      <div style="display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;border-bottom:1px solid #F1F5F9;">
        <span>{{ a.agent }}{% if not a.on_ivr %} <span class="hint">(not on IVR)</span>{% endif %}</span>
        <b>{{ a.logged }} &middot; {{ a.ivr_calls }} &middot; {{ a.ivr_connected }}</b></div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="nav-links"><a href="/">&larr; Back to home</a> &nbsp; <a href="/calls">📞 Call Monitor</a></div>
</div>
"""

CALLINS_HTML = BASE_STYLE + """
<div class="header">📲 Called In &amp; Due <small>Dr. Manoj Agarwal Clinic — high-intent: due patients who phoned in</small></div>
<div class="container">
  <div class="card">
    <h2>Worklist {% if b.count %}<span class="tag tag-red">{{ b.count }}</span>{% endif %}</h2>
    {% if msg %}<p style="color:#166534;font-size:13.5px;margin-bottom:8px;">✅ {{ msg }}</p>{% endif %}
    {% if err %}<p style="color:#B91C1C;font-size:13.5px;margin-bottom:8px;">⚠️ {{ err }}</p>{% endif %}
    <p class="hint" style="margin-bottom:10px;">Patients who are <b>due or overdue</b> for follow-up <b>and</b> have
      called the clinic but were <b>missed</b>. They're trying to reach you — call these back first.</p>
    {% if feed_on %}
    <form method="POST" action="/callins" style="margin-bottom:6px;">
      <input type="hidden" name="action" value="refresh">
      <button class="btn btn-grey" type="submit">↻ Refresh from Google</button>
    </form>
    {% endif %}
  </div>

  {% if b.rows %}
  <div class="card">
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
      <tr style="text-align:left;color:#6B7280;border-bottom:1.5px solid #E5E7EB;">
        <th style="padding:6px 8px;">Patient</th><th style="padding:6px 8px;">Status</th>
        <th style="padding:6px 8px;">Overdue</th><th style="padding:6px 8px;">Due</th>
        <th style="padding:6px 8px;">Called in</th>
      </tr>
      {% for r in b.rows %}
      <tr style="border-bottom:1px solid #F1F5F9;">
        <td style="padding:6px 8px;"><b>{{ r.name or '—' }}</b><br><span class="hint">{{ r.mobile }}</span></td>
        <td style="padding:6px 8px;">{{ r.status }}</td>
        <td style="padding:6px 8px;">{{ r.overdue }}</td>
        <td style="padding:6px 8px;white-space:nowrap;">{{ r.due }}</td>
        <td style="padding:6px 8px;white-space:nowrap;">{{ r.called_in }}</td>
      </tr>
      {% endfor %}
    </table>
    </div>
  </div>
  {% else %}
  <div class="card">
    <p class="hint">{% if b.meta and b.meta.no_inbound %}No incoming calls loaded yet — refresh the feed, or check that the
      Call_Feed includes incoming calls.{% else %}No due patients have called in. 👍{% endif %}</p>
  </div>
  {% endif %}

  <div class="nav-links"><a href="/">&larr; Back to home</a> &nbsp; <a href="/callaudit">🔎 Call Audit</a> &nbsp; <a href="/confirm">✅ Confirm Closures</a></div>
</div>
"""

CONFIRM_HTML = BASE_STYLE + """
<div class="header">✅ Confirm Closures <small>Dr. Manoj Agarwal Clinic — closes that need a second pair of eyes</small></div>
<div class="container">
  <div class="card">
    <h2>Needs confirmation {% if rows %}<span class="tag tag-red">{{ rows|length }}</span>{% endif %}</h2>
    {% if msg %}<p style="color:#166534;font-size:13.5px;margin-bottom:8px;">✅ {{ msg }}</p>{% endif %}
    {% if err %}<p style="color:#B91C1C;font-size:13.5px;margin-bottom:8px;">⚠️ {{ err }}</p>{% endif %}
    <p class="hint" style="margin-bottom:4px;">A patient's follow-up was closed with a response that can be quietly wrong.
      Check it against the patient / records / pharmacy, then settle it. <b>Confirm</b> closes it; <b>Reject</b> puts the
      patient back on the call sheet. A missing record means <i>unconfirmed</i> — not that anyone lied; listen on
      MyOperator if unsure.</p>
    <p class="hint"><b>Tt COMPLETE → Shavez</b> (confirm with patient/records) &nbsp;·&nbsp;
      <b>MED HERE → Pharmacy</b> (match the bill in the pharmacy upload) &nbsp;·&nbsp;
      <b>NO → Shavez</b> (just review the reason — retention).</p>
  </div>

  {% if rows %}
  <div class="card">
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
      <tr style="text-align:left;color:#6B7280;border-bottom:1.5px solid #E5E7EB;">
        <th style="padding:6px 8px;">Patient</th><th style="padding:6px 8px;">Clinic ID</th>
        <th style="padding:6px 8px;">Close</th><th style="padding:6px 8px;">Owner</th>
        <th style="padding:6px 8px;">Caller</th><th style="padding:6px 8px;">Date</th>
        <th style="padding:6px 8px;">Action</th>
      </tr>
      {% for x in rows %}
      <tr style="border-bottom:1px solid #F1F5F9;">
        <td style="padding:6px 8px;"><b>{{ x.Patient_Name or '—' }}</b><br><span class="hint">{{ x.Mobile }}</span></td>
        <td style="padding:6px 8px;"><b>{{ x.Clinic_Id or '—' }}</b></td>
        <td style="padding:6px 8px;"><span class="tag {{ 'tag-amber' if x.Conf_Type != 'DECLINE' else 'tag-grey' }}">{{ x.Conf_Type }}</span></td>
        <td style="padding:6px 8px;">{{ x.Owner }}</td>
        <td style="padding:6px 8px;">{{ x.Caller or '—' }}</td>
        <td style="padding:6px 8px;white-space:nowrap;">{{ x.Call_Date }}</td>
        <td style="padding:6px 8px;white-space:nowrap;">
          {% if x.Conf_Type == 'DECLINE' %}
          <form method="POST" action="/confirm" style="display:inline;margin:0;">
            <input type="hidden" name="action" value="review"><input type="hidden" name="confirm_id" value="{{ x.Confirm_ID }}">
            <button class="btn btn-grey" type="submit" style="padding:5px 10px;font-size:12px;">Reviewed</button>
          </form>
          {% else %}
          <form method="POST" action="/confirm" style="display:inline;margin:0;">
            <input type="hidden" name="action" value="confirm"><input type="hidden" name="confirm_id" value="{{ x.Confirm_ID }}">
            <button class="btn" type="submit" style="padding:5px 10px;font-size:12px;background:#166534;">Confirm</button>
          </form>
          <form method="POST" action="/confirm" style="display:inline;margin:0 0 0 4px;">
            <input type="hidden" name="action" value="reject"><input type="hidden" name="confirm_id" value="{{ x.Confirm_ID }}">
            <button class="btn btn-grey" type="submit" style="padding:5px 10px;font-size:12px;">Reject → call back</button>
          </form>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </table>
    </div>
  </div>
  {% else %}
  <div class="card"><p class="hint">Nothing to confirm right now. 👍</p></div>
  {% endif %}

  <div class="nav-links"><a href="/">&larr; Back to home</a> &nbsp; <a href="/callaudit">🔎 Call Audit</a> &nbsp; <a href="/confirm">✅ Confirm Closures</a></div>
</div>
"""

LOGIN_HTML = """
<!DOCTYPE html><html><head><title>Follow-Up Tracker — Login</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">
  Dr. Manoj Agarwal Clinic
  <small>Follow-Up Dropout Tracking System</small>
</div>
<div class="container">
  <div class="card">
    <h2>🔐 Login</h2>
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}
    <form method="POST">
      <label>Password</label>
      <input type="password" name="password" placeholder="Enter clinic password" autofocus>
      <button class="btn" type="submit">Login</button>
    </form>
  </div>
</div>
</body></html>
"""

INDEX_HTML = """
<!DOCTYPE html><html><head><title>Follow-Up Tracker</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">
  Dr. Manoj Agarwal Clinic
  <small>Follow-Up Dropout Tracking System — Daily Upload
    {% if role == 'admin' %}· Admin{% else %}· Staff{% endif %}</small>
</div>
<div class="container">

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
    <div class="alert alert-{{ cat }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  <!-- Daily Run -->
  <div class="card">
    <h2>📋 Daily Processing</h2>
    <p class="hint" style="margin-bottom:14px;">
      Upload today's consultation report and tomorrow's follow-up log.
      {% if role == 'admin' %}The system updates all ledgers and generates the
      full audit Excel (plus the staff action sheet).{% else %}The system will
      generate your Staff Action Today sheet.{% endif %}
    </p>
    <form method="POST" action="/run" enctype="multipart/form-data">
      <label>Consultation Report CSV</label>
      <div class="hint">Filename: consultation_report_YYYY-MM-DD.csv</div>
      <input type="file" name="consultation_csv" accept=".csv" required>

      <label>Follow-Up Log CSV</label>
      <div class="hint">Filename: followup_logs_YYYY-MM-DD.csv (or any name)</div>
      <input type="file" name="followup_csv" accept=".csv" required>

      <label>Filled Call Sheet (optional)</label>
      <div class="hint">Yesterday's Staff Action sheet (.xlsx) with RESPONSE / CALLED BY filled in.
        Records the call outcomes. Leave empty if you have none.</div>
      <input type="file" name="callsheet_xlsx" accept=".xlsx">

      <button class="btn" type="submit">▶ Process and Generate Report</button>
    </form>
  </div>

  <!-- Previous outputs -->
  {% if outputs %}
  <div class="card">
    <h2>📥 Previous Reports</h2>
    {% for f in outputs %}
    <div style="display:flex; align-items:center; justify-content:space-between;
      padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
      <span style="font-size:13px;">{{ f }}</span>
      <a class="btn btn-green" style="width:auto; padding: 6px 14px; font-size:13px;"
        href="/download/{{ f }}">Download</a>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if role == 'admin' %}
  <!-- Vacation calendar (admin only) -->
  <div class="card">
    <h2>🏖️ Doctor Unavailability / Vacation Calendar</h2>
    <p class="hint" style="margin-bottom:14px;">
      Add a period when the doctor is unavailable. Follow-ups due in that
      window appear in the <strong>Vacation Notice List</strong> sheet of the
      next report — staff inform those patients in advance. (When WhatsApp
      automation goes live, this same list will feed the unavailability
      template; nothing is sent automatically today.)
    </p>
    {% if vacations %}
    <div style="margin-bottom:14px;">
      {% for v in vacations %}
      <div style="display:flex; align-items:center; justify-content:space-between;
        padding:8px 10px; border:1px solid #eee; border-radius:8px; margin-bottom:6px;">
        <span style="font-size:13px;">
          <strong>{{ v.start.strftime('%d-%m-%Y') }} → {{ v.end.strftime('%d-%m-%Y') }}</strong>
          <span class="tag tag-blue" style="margin-left:8px;">{{ v.slot }}</span>
          {% if v.note %}<span style="color:#6B7280;"> — {{ v.note }}</span>{% endif %}
        </span>
        <form method="POST" action="/vacation/delete/{{ loop.index0 }}" style="margin:0;">
          <button class="btn" style="width:auto; padding:5px 12px; font-size:12px;
            background:#991B1B;" type="submit">Remove</button>
        </form>
      </div>
      {% endfor %}
    </div>
    {% endif %}
    <form method="POST" action="/vacation/add">
      <div style="display:flex; gap:10px;">
        <div style="flex:1;">
          <label>From</label>
          <input type="date" name="start_date" required
            style="width:100%; padding:10px 12px; border:1.5px solid #D1D5DB;
            border-radius:7px; font-size:14px; margin-bottom:16px; background:#fafafa;">
        </div>
        <div style="flex:1;">
          <label>To (optional)</label>
          <input type="date" name="end_date"
            style="width:100%; padding:10px 12px; border:1.5px solid #D1D5DB;
            border-radius:7px; font-size:14px; margin-bottom:16px; background:#fafafa;">
        </div>
      </div>
      <label>Slot</label>
      <select name="slot" style="width:100%; padding:10px 12px; border:1.5px solid #D1D5DB;
        border-radius:7px; font-size:14px; margin-bottom:16px; background:#fafafa;">
        <option>Full Day</option>
        <option>Morning</option>
        <option>Evening</option>
      </select>
      <label>Note (optional)</label>
      <input type="text" name="note" placeholder="e.g. Conference / family function">
      <button class="btn" type="submit">＋ Add Vacation Period</button>
    </form>
  </div>

  <!-- One-time setup (admin only) -->
  <div class="card">
    <h2>⚙️ First-Time Setup — Initialise Patient Master</h2>
    <p class="hint" style="margin-bottom:14px;">
      Upload the 31 May 2026 full patient export once to build the identity base.
      Do not run this again after daily processing has begun.
    </p>
    <form method="POST" action="/init_master" enctype="multipart/form-data">
      <label>Initial Patient Master CSV (31 May 2026 export)</label>
      <input type="file" name="master_csv" accept=".csv" required>
      <button class="btn btn-grey" type="submit">Initialise Patient Master</button>
    </form>
  </div>

  <!-- Diagnosis data freshness + refresh (admin only) -->
  <div class="card">
    <h2>🩺 Diagnosis Data</h2>
    {% if diag.as_of_date or diag.ingested_on %}
      <div style="background:{{ '#FEF3C7' if diag.stale else '#ECFDF5' }};
        border:1px solid {{ '#F59E0B' if diag.stale else '#A7F3D0' }};
        border-radius:8px; padding:12px 14px; margin-bottom:12px; font-size:13px;">
        <div style="font-size:15px; font-weight:700; color:{{ '#92400E' if diag.stale else '#065F46' }};">
          Diagnosis data as of: {{ diag.as_of_label }}
          {% if diag.stale %}&nbsp;·&nbsp;⚠️ {{ diag.age_days }} days old — consider a fresh export{% endif %}
        </div>
        <div style="color:#4B5563; margin-top:5px;">
          Last absorbed {{ diag.ingested_on or '—' }} from
          <strong>{{ diag.source_label }}</strong>.<br>
          {{ diag.with_diagnosis }} of {{ diag.patient_count }} patients carry a diagnosis
          ({{ diag.no_diagnosis }} still blank).
        </div>
      </div>
    {% else %}
      <p class="hint" style="margin-bottom:12px;">
        No diagnosis source recorded yet. The daily consultation report does <em>not</em>
        contain medical history — diagnosis lives only in the periodic full patient export.
        Upload a fresh full export below to build / refresh it.
      </p>
    {% endif %}
    <p class="hint" style="margin-bottom:12px;">
      Absorb a fresh Docterz full patient export (the file whose name ends
      <code>…UPTO_DD_MON_YYYY.csv</code>, or a <code>patients_detail.csv</code>). This refreshes
      diagnoses for <strong>all</strong> patients — a patient whose diagnosis changed over
      treatment is updated; an existing diagnosis is never wiped by a blank.
    </p>
    <form method="POST" action="/diagnosis" enctype="multipart/form-data">
      <label>Full patient export CSV (with medical history)</label>
      <input type="file" name="diagnosis_csv" accept=".csv" required>
      <label style="margin-top:8px;">Data as-of date <span class="hint">(optional — auto-read from filename if it has “UPTO DD MON YYYY”)</span></label>
      <input type="date" name="asof_date"
        style="width:100%; padding:10px 12px; border:1.5px solid #D1D5DB;
        border-radius:7px; font-size:14px; margin-bottom:14px; background:#fafafa;">
      <button class="btn btn-grey" type="submit">Absorb &amp; Refresh Diagnoses (all patients)</button>
    </form>
  </div>
  {% endif %}

  <div class="nav-links">
    <a href="/calls">📞 Call Monitor</a>
    <a href="/callaudit">🔎 Call Audit</a>
    <a href="/callins">📲 Called In &amp; Due</a>
    <a href="/confirm">✅ Confirm Closures</a>
    <a href="/lab">🧪 Lab Revenue Entry</a>
    <a href="/procedure">➕ Mark ₹0 Procedure</a>
    {% if role == 'admin' %}<a href="/finance">💰 Finance Dashboard</a>{% endif %}
    {% if role == 'admin' %}<a href="/revenue/upload">📊 Revenue Upload</a>{% endif %}
    {% if role == 'admin' %}<a href="/concessions">🏷️ VIP &amp; Concessions</a>{% endif %}
    <a href="/logout">Logout</a>
  </div>

</div>
</body></html>
"""

RESULT_HTML = """
<!DOCTYPE html><html><head><title>Processing Complete</title>
""" + BASE_STYLE + """
<script>
  window.onload = function() {
    setTimeout(function() {
      window.location.href = '/download/{{ filename }}';
    }, 800);
  }
</script>
</head><body>
<div class="header">
  Dr. Manoj Agarwal Clinic
  <small>Follow-Up Dropout Tracking System</small>
</div>
<div class="container">
  <div class="card">
    <h2>✅ Processing Complete</h2>
    <div class="alert alert-success">{{ message }} Downloading report automatically...</div>

    {% if notices %}
      {% for n in notices %}
      <div style="background:#fff3cd; border:1px solid #ffe08a; color:#7a5b00;
        border-radius:8px; padding:12px 14px; margin:10px 0; font-size:14px; line-height:1.5;">
        ⚠️ {{ n }}
      </div>
      {% endfor %}
    {% endif %}

    <div style="margin: 16px 0;">
      {% for stat in stats %}
      <div style="display:flex; justify-content:space-between; padding:7px 0;
        border-bottom: 1px solid #f5f5f5; font-size:14px;">
        <span>{{ stat[0] }}</span>
        <strong>{{ stat[1] }}</strong>
      </div>
      {% endfor %}
    </div>

    <a class="btn btn-green" href="/download/{{ filename }}" style="margin-bottom:12px;">
      ⬇ Download Again ({{ filename }})
    </a>
    <a class="btn btn-grey" href="/">← Back to Upload</a>
  </div>
</div>
</body></html>
"""

ERROR_HTML = """
<!DOCTYPE html><html><head><title>Error</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">Dr. Manoj Agarwal Clinic</div>
<div class="container">
  <div class="card">
    <h2>⚠️ Error</h2>
    <div class="alert alert-error">{{ error }}</div>
    <a class="btn btn-grey" href="/">← Back</a>
  </div>
</div>
</body></html>
"""

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        pw = request.form.get("password", "")
        role = ""
        if ADMIN_PASSWORD and pw == ADMIN_PASSWORD:
            role = "admin"
        elif STAFF_PASSWORD and pw == STAFF_PASSWORD:
            role = "staff"
        if role:
            session.permanent = True
            session["logged_in"] = True
            session["role"] = role
            return redirect(url_for("index"))
        error = "Incorrect password. Please try again."
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    role = current_role()
    if role == "admin":
        outputs = sorted(
            [f.name for f in OUTPUTS_DIR.glob("Followup_Audit_*.xlsx")]
            + [f.name for f in OUTPUTS_DIR.glob("Staff_Action_Today_*.xlsx")],
            reverse=True
        )[:14]
    else:
        outputs = sorted(
            [f.name for f in OUTPUTS_DIR.glob("Staff_Action_Today_*.xlsx")],
            reverse=True
        )[:10]
    vacations = load_vacations() if role == "admin" else []
    diag = _diagnosis_status() if role == "admin" else {}
    return render_template_string(
        INDEX_HTML, outputs=outputs, role=role, vacations=vacations, diag=diag)


def _diagnosis_status() -> dict:
    """Summarise diagnosis-layer freshness for the admin home banner."""
    import seed_diagnosis
    m = seed_diagnosis.load_diagnosis_meta()
    if not m:
        return {}
    asof = (m.get("as_of_date") or "").strip()
    age_days, stale, as_of_label = None, False, "unknown"
    ref = asof or (m.get("ingested_on", "")[:10])
    if ref:
        try:
            age_days = (_date.today() - _date.fromisoformat(ref)).days
            stale = age_days is not None and age_days > 45
        except Exception:
            age_days = None
    if asof:
        try:
            as_of_label = _date.fromisoformat(asof).strftime("%d %b %Y")
        except Exception:
            as_of_label = asof
    else:
        as_of_label = "not in filename (using ingest date)"
    srcs = m.get("source_files", [])
    source_label = ", ".join(srcs) if srcs else "—"
    if len(source_label) > 70:
        source_label = source_label[:67] + "…"
    return {
        "as_of_date": asof, "as_of_label": as_of_label,
        "ingested_on": m.get("ingested_on", ""), "source_label": source_label,
        "patient_count": m.get("patient_count", 0),
        "with_diagnosis": m.get("with_diagnosis", 0),
        "no_diagnosis": m.get("no_diagnosis", 0),
        "age_days": age_days, "stale": stale,
    }

@app.route("/run", methods=["POST"])
@login_required
def run():
    cons_file = request.files.get("consultation_csv")
    fu_file   = request.files.get("followup_csv")

    if not cons_file or not fu_file:
        return render_template_string(ERROR_HTML, error="Both files are required.")
    if not allowed_file(cons_file.filename) or not allowed_file(fu_file.filename):
        return render_template_string(ERROR_HTML, error="Only CSV files are accepted.")

    cons_path = str(UPLOAD_DIR / secure_filename(cons_file.filename))
    fu_path   = str(UPLOAD_DIR / secure_filename(fu_file.filename))
    cons_file.save(cons_path)
    fu_file.save(fu_path)

    # Optional: a FILLED call sheet (.xlsx) to capture staff call outcomes.
    cs_file = request.files.get("callsheet_xlsx")
    callsheet_path = None
    if cs_file and cs_file.filename:
        if not cs_file.filename.lower().endswith(".xlsx"):
            return render_template_string(
                ERROR_HTML, error="The filled call sheet must be an .xlsx file.")
        callsheet_path = str(UPLOAD_DIR / secure_filename(cs_file.filename))
        cs_file.save(callsheet_path)

    try:
        # Frame the run on the FILES (the next call day derived from the uploaded
        # consultation + follow-up dates), not the clinic PC clock. This makes an
        # evening upload produce the NEXT CALL DAY's actionable sheet — e.g. a
        # Saturday-night upload yields Monday's call list ready for staff, with no
        # Sunday upload needed. (Pass an explicit date here only for testing.)
        audit_path, staff_path = run_daily(cons_path, fu_path, today=None,
                                           callsheet_path=callsheet_path)
        # Staff receive the action-sheet workbook only; admin gets full audit.
        out_name = Path(audit_path if current_role() == "admin" else staff_path).name

        # Quick stats from the output
        import pandas as pd
        from processor import load_followups, load_master, INGEST_NOTICES
        fu = load_followups()
        master = load_master()
        sc = fu["Followup_Status"].value_counts().to_dict()

        stats = [
            ("Total follow-up obligations", len(fu)),
            ("Probable Dropouts", sc.get("Probable Dropout", 0)),
            ("Actionable Missed Follow-Ups", sc.get("Actionable Missed Follow-Up", 0)),
            ("Grace Period", sc.get("Grace Period", 0)),
            ("Due Today", sc.get("Due Today", 0)),
            ("Identity Problems", sc.get("Identity Unresolved", 0) + sc.get("Ambiguous Mobile", 0) + sc.get("Invalid Mobile / No Contact", 0)),
            ("Total Patients in Master", len(master)),
        ]

        return render_template_string(
            RESULT_HTML,
            message="Report generated successfully.",
            filename=out_name,
            stats=stats,
            notices=list(INGEST_NOTICES)
        )
    except Exception as e:
        import traceback
        traceback.print_exc()   # full detail in the server log
        if current_role() == "admin":
            detail = f"{str(e)}\n\n{traceback.format_exc()}"
        else:
            detail = ("Processing failed. Please check that the correct CSVs were "
                      "uploaded, or contact Dr. Manoj. (Details are in the server log.)")
        return render_template_string(ERROR_HTML, error=detail)

@app.route("/init_master", methods=["POST"])
@admin_required
def init_master():
    f = request.files.get("master_csv")
    if not f or not allowed_file(f.filename):
        flash("Please upload a valid CSV file.", "error")
        return redirect(url_for("index"))
    path = str(UPLOAD_DIR / secure_filename(f.filename))
    f.save(path)
    try:
        result = run_initial_master(path)
        flash(f"✅ {result}", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    return redirect(url_for("index"))

@app.route("/diagnosis", methods=["POST"])
@admin_required
def refresh_diagnosis():
    f = request.files.get("diagnosis_csv")
    if not f or not allowed_file(f.filename):
        flash("Please upload a valid CSV (full patient export with medical history).", "error")
        return redirect(url_for("index"))
    asof = (request.form.get("asof_date") or "").strip()
    path = str(UPLOAD_DIR / secure_filename(f.filename))
    f.save(path)
    try:
        import seed_diagnosis
        _master, stats = seed_diagnosis.ingest([path], asof_date=asof)
        meta = seed_diagnosis.load_diagnosis_meta()
        label = meta.get("as_of_date") or "(date not in filename)"
        flash(
            f"✅ Diagnosis data refreshed (as of {label}). "
            f"{meta.get('with_diagnosis', 0)} of {meta.get('patient_count', 0)} patients now carry a "
            f"diagnosis. This run: {stats.get('updated', 0)} existing updated, "
            f"{stats.get('new', 0) + stats.get('seeded', 0)} new/seeded, "
            f"{stats.get('discarded', 0)} junk rows skipped.",
            "success")
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f"Error absorbing diagnosis file: {e}", "error")
    return redirect(url_for("index"))

@app.route("/download/<filename>")
@login_required
def download(filename):
    if not filename.endswith(".xlsx"):
        return "Not allowed", 403
    is_audit = filename.startswith("Followup_Audit_")
    is_staff = filename.startswith("Staff_Action_Today_")
    if not (is_audit or is_staff):
        return "Not allowed", 403
    # Full audit workbooks (ledgers + patient master) are admin-only (P1-08).
    if is_audit and current_role() != "admin":
        return "Admin access required", 403
    file_path = OUTPUTS_DIR / secure_filename(filename)
    if not file_path.exists():
        return "File not found", 404
    return send_file(str(file_path), as_attachment=True)

# ── Vacation calendar (admin) ─────────────────────────────────────────────────
@app.route("/vacation/add", methods=["POST"])
@admin_required
def vacation_add():
    start = request.form.get("start_date", "").strip()
    end   = request.form.get("end_date", "").strip() or start
    slot  = request.form.get("slot", "Full Day").strip() or "Full Day"
    note  = request.form.get("note", "").strip()
    if not start:
        flash("Start date is required.", "error")
        return redirect(url_for("index"))
    # store as DD-MM-YYYY (HTML date inputs give YYYY-MM-DD)
    def _ddmmyyyy(s):
        p = s.split("-")
        return f"{p[2]}-{p[1]}-{p[0]}" if len(p) == 3 and len(p[0]) == 4 else s
    rows = [{
        "Start_Date": _ddmmyyyy(v["start"].strftime("%Y-%m-%d")),
        "End_Date":   _ddmmyyyy(v["end"].strftime("%Y-%m-%d")),
        "Slot": v["slot"], "Note": v["note"],
    } for v in load_vacations()]
    rows.append({"Start_Date": _ddmmyyyy(start), "End_Date": _ddmmyyyy(end),
                 "Slot": slot, "Note": note})
    save_vacations(rows)
    flash("Vacation period added. It will be reflected in the next processing run.", "success")
    return redirect(url_for("index"))

@app.route("/vacation/delete/<int:idx>", methods=["POST"])
@admin_required
def vacation_delete(idx):
    vacs = load_vacations()
    if 0 <= idx < len(vacs):
        del vacs[idx]
        rows = [{
            "Start_Date": v["start"].strftime("%d-%m-%Y"),
            "End_Date":   v["end"].strftime("%d-%m-%Y"),
            "Slot": v["slot"], "Note": v["note"],
        } for v in vacs]
        save_vacations(rows)
        flash("Vacation period removed.", "success")
    return redirect(url_for("index"))

# ── Lab revenue entry (NK Pathology) ─────────────────────────────────────────
LAB_HTML = """
<!DOCTYPE html><html><head><title>Lab Revenue Entry</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">
  Dr. Manoj Agarwal Clinic
  <small>NK Pathology — Lab Revenue Entry</small>
</div>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
    <div class="alert alert-{{ cat }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  <div class="card">
    <h2>🧪 Add Lab Revenue</h2>
    <p class="hint" style="margin-bottom:14px;">
      Type the Docterz <strong>Clinic ID</strong> (preferred) or the patient's
      <strong>mobile</strong>, then tap <em>Find</em>. The name fills in
      automatically. Enter the amount and any discount — the net is calculated
      for you. Date defaults to today.
    </p>

    <label>Docterz Clinic ID or Mobile</label>
    <div style="display:flex; gap:8px;">
      <input type="text" id="q" placeholder="e.g. 7443  or  9837xxxxxx"
        style="flex:1;" autofocus>
      <button class="btn" style="width:auto; padding:10px 18px;" onclick="findPatient()">Find</button>
    </div>
    <div id="lookupmsg" class="hint" style="min-height:18px;"></div>

    <form method="POST" action="/lab/add" id="labform" style="margin-top:8px;">
      <input type="hidden" name="uid" id="uid">
      <input type="hidden" name="clinic_id" id="clinic_id">
      <input type="hidden" name="mobile" id="mobile">

      <label>Patient Name</label>
      <input type="text" name="name" id="name" readonly
        style="background:#eef2f7; font-weight:600;">

      <div style="display:flex; gap:10px;">
        <div style="flex:1;">
          <label>Amount (₹)</label>
          <input type="number" name="amount" id="amount" min="0" step="1"
            oninput="calcNet()" placeholder="0">
        </div>
        <div style="flex:1;">
          <label>Discount (₹)</label>
          <input type="number" name="discount" id="discount" min="0" step="1"
            value="0" oninput="calcNet()">
        </div>
      </div>

      <label>Net Paid (₹) — auto-calculated</label>
      <input type="text" id="net" readonly
        style="background:#e2efda; font-weight:700; font-size:16px; color:#166534;">

      <label>Date</label>
      <input type="date" name="entry_date" id="entry_date"
        style="width:100%; padding:10px 12px; border:1.5px solid #D1D5DB;
        border-radius:7px; font-size:14px; margin-bottom:16px; background:#fafafa;">

      <label>Note (optional)</label>
      <input type="text" name="note" placeholder="e.g. CBC, LFT, Vitamin D">

      <button class="btn btn-green" type="submit" id="savebtn" disabled>Save Lab Revenue</button>
    </form>
  </div>

  {% if recent %}
  <div class="card">
    <h2>🕑 Last 10 lab entries</h2>
    {% for e in recent %}
    <div style="display:flex; justify-content:space-between; padding:7px 0;
      border-bottom:1px solid #f3f3f3; font-size:13px;">
      <span>{{ e.Date }} · {{ e.Patient_Name }} <span style="color:#9aa;">({{ e.Clinic_Specific_Id }})</span></span>
      <strong>₹{{ e.Net }}</strong>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="nav-links"><a href="/">← Home</a>{% if role=='admin' %} <a href="/finance">💰 Finance</a>{% endif %}</div>
</div>
<script>
  // default date = today
  document.getElementById('entry_date').value = new Date().toISOString().slice(0,10);
  function calcNet(){
    var a = parseFloat(document.getElementById('amount').value||0);
    var d = parseFloat(document.getElementById('discount').value||0);
    var net = a - d; if (net < 0) net = 0;
    document.getElementById('net').value = net;
    document.getElementById('savebtn').disabled =
      !(document.getElementById('uid').value && a > 0);
  }
  async function findPatient(){
    var q = document.getElementById('q').value.trim();
    var msg = document.getElementById('lookupmsg');
    if(!q){ msg.textContent='Enter a Clinic ID or mobile.'; return; }
    msg.style.color='#6B7280'; msg.textContent='Searching…';
    try {
      var res = await fetch('/lab/lookup?q='+encodeURIComponent(q));
      var data = await res.json();
      if(data.found){
        document.getElementById('uid').value = data.uid;
        document.getElementById('clinic_id').value = data.clinic_id;
        document.getElementById('mobile').value = data.mobile;
        document.getElementById('name').value = data.name;
        msg.style.color='#166534';
        msg.textContent='✓ '+data.name+'  (Clinic ID '+data.clinic_id+', '+data.mobile+')';
        calcNet();
        document.getElementById('amount').focus();
      } else {
        document.getElementById('uid').value='';
        document.getElementById('name').value='';
        document.getElementById('savebtn').disabled=true;
        msg.style.color='#991B1B';
        msg.textContent = data.message || 'No patient found. Check the ID/mobile.';
      }
    } catch(e){ msg.style.color='#991B1B'; msg.textContent='Lookup failed. Try again.'; }
  }
  document.getElementById('q').addEventListener('keydown',function(e){
    if(e.key==='Enter'){ e.preventDefault(); findPatient(); }
  });
</script>
</body></html>
"""

@app.route("/lab")
@login_required
def lab_page():
    rev = revenue.load_revenue()
    recent = []
    if len(rev):
        lab = rev[rev["Source"] == "Lab"].tail(10).iloc[::-1]
        recent = lab.to_dict("records")
    return render_template_string(LAB_HTML, role=current_role(), recent=recent)

@app.route("/lab/lookup")
@login_required
def lab_lookup():
    from flask import jsonify
    q = request.args.get("q", "")
    hit = revenue.lookup_patient(q)
    if hit and hit.get("uid"):
        return jsonify({"found": True, "uid": hit["uid"], "clinic_id": hit["clinic_id"],
                        "name": hit["name"], "mobile": hit["mobile"]})
    if hit and hit.get("ambiguous"):
        return jsonify({"found": False, "message": hit["ambiguous"]})
    return jsonify({"found": False, "message": "No patient found for that Clinic ID / mobile."})

@app.route("/lab/add", methods=["POST"])
@login_required
def lab_add():
    uid       = request.form.get("uid", "").strip()
    clinic_id = request.form.get("clinic_id", "").strip()
    name      = request.form.get("name", "").strip()
    mobile    = request.form.get("mobile", "").strip()
    amount    = request.form.get("amount", "0").strip()
    discount  = request.form.get("discount", "0").strip()
    entry_date = request.form.get("entry_date", "").strip() or None
    note      = request.form.get("note", "").strip()
    if not uid or not name:
        flash("Please use Find to select a patient before saving.", "error")
        return redirect(url_for("lab_page"))
    try:
        row = revenue.add_lab_revenue(
            uid, clinic_id, name, mobile, amount, discount,
            entry_date=entry_date, entered_by=current_role(), note=note)
        flash(f"✅ Saved: {name} — net ₹{row['Net']:.0f} on {row['Date']}.", "success")
    except Exception as e:
        flash(f"Error saving: {e}", "error")
    return redirect(url_for("lab_page"))

# ── Mark a ₹0 / free procedure ────────────────────────────────────────────────
PROC_HTML = """
<!DOCTYPE html><html><head><title>Mark ₹0 Procedure</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">
  Dr. Manoj Agarwal Clinic
  <small>Mark a ₹0 / free procedure (e.g. Ayushman cashless)</small>
</div>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
    <div class="alert alert-{{ cat }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  <div class="card">
    <h2>➕ Mark ₹0 / Free Procedure</h2>
    <p class="hint" style="margin-bottom:14px;">
      Use this <strong>only</strong> for a procedure that carries no amount in Docterz
      (free / Ayushman cashless). Paid procedures are captured automatically.
      The patient must have been seen that day. This makes the procedure show in the
      day revenue sheet (at ₹0), the staff call-back list, and the patient's history.
    </p>

    <label>Docterz Clinic ID or Mobile</label>
    <div style="display:flex; gap:8px;">
      <input type="text" id="q" placeholder="e.g. 7443  or  9837xxxxxx" style="flex:1;" autofocus>
      <button class="btn" style="width:auto; padding:10px 18px;" onclick="findP()">Find</button>
    </div>
    <div id="msg" class="hint" style="min-height:18px;"></div>

    <form method="POST" action="/procedure/add" id="pform" style="margin-top:8px;">
      <input type="hidden" name="uid" id="uid">
      <input type="hidden" name="clinic_id" id="clinic_id">
      <input type="hidden" name="mobile" id="mobile">
      <label>Patient Name</label>
      <input type="text" name="name" id="name" readonly style="background:#eef2f7; font-weight:600;">
      <label>Procedure Date</label>
      <input type="date" name="proc_date" id="proc_date"
        style="width:100%; padding:10px 12px; border:1.5px solid #D1D5DB;
        border-radius:7px; font-size:14px; margin-bottom:16px; background:#fafafa;">
      <label>Note (optional)</label>
      <input type="text" name="note" placeholder="e.g. Ayushman cashless / aspiration">
      <button class="btn btn-green" type="submit" id="savebtn" disabled>Mark Procedure (₹0)</button>
    </form>
  </div>

  {% if recent %}
  <div class="card">
    <h2>🕑 Last 10 marked procedures</h2>
    {% for e in recent %}
    <div style="display:flex; justify-content:space-between; padding:7px 0;
      border-bottom:1px solid #f3f3f3; font-size:13px;">
      <span>{{ e.Date }} · {{ e.Patient_Name }} <span style="color:#9aa;">({{ e.Clinic_Specific_Id }})</span></span>
      <span style="color:#6B7280;">{{ e.Note }}</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <div class="nav-links"><a href="/">← Home</a> <a href="/lab">🧪 Lab Entry</a></div>
</div>
<script>
  document.getElementById('proc_date').value = new Date().toISOString().slice(0,10);
  async function findP(){
    var q = document.getElementById('q').value.trim();
    var msg = document.getElementById('msg');
    if(!q){ msg.textContent='Enter a Clinic ID or mobile.'; return; }
    msg.style.color='#6B7280'; msg.textContent='Searching…';
    try {
      var res = await fetch('/lab/lookup?q='+encodeURIComponent(q));
      var data = await res.json();
      if(data.found){
        document.getElementById('uid').value=data.uid;
        document.getElementById('clinic_id').value=data.clinic_id;
        document.getElementById('mobile').value=data.mobile;
        document.getElementById('name').value=data.name;
        document.getElementById('savebtn').disabled=false;
        msg.style.color='#166534';
        msg.textContent='✓ '+data.name+'  (Clinic ID '+data.clinic_id+', '+data.mobile+')';
      } else {
        document.getElementById('uid').value=''; document.getElementById('name').value='';
        document.getElementById('savebtn').disabled=true;
        msg.style.color='#991B1B'; msg.textContent=data.message||'No patient found.';
      }
    } catch(e){ msg.style.color='#991B1B'; msg.textContent='Lookup failed. Try again.'; }
  }
  document.getElementById('q').addEventListener('keydown',function(e){
    if(e.key==='Enter'){ e.preventDefault(); findP(); }
  });
</script>
</body></html>
"""

@app.route("/procedure")
@login_required
def procedure_page():
    man = revenue.load_manual_procedures()
    recent = man.tail(10).iloc[::-1].to_dict("records") if len(man) else []
    return render_template_string(PROC_HTML, role=current_role(), recent=recent)

@app.route("/procedure/add", methods=["POST"])
@login_required
def procedure_add():
    uid       = request.form.get("uid", "").strip()
    clinic_id = request.form.get("clinic_id", "").strip()
    name      = request.form.get("name", "").strip()
    mobile    = request.form.get("mobile", "").strip()
    proc_date = request.form.get("proc_date", "").strip() or None
    note      = request.form.get("note", "").strip()
    if not uid or not name:
        flash("Please use Find to select a patient before marking.", "error")
        return redirect(url_for("procedure_page"))
    try:
        r = revenue.add_manual_procedure(uid, clinic_id, name, mobile,
                                         proc_date=proc_date, entered_by=current_role(), note=note)
        flash(f"✅ Marked ₹0 procedure for {name} on {r['date']}. It will appear in that "
              f"day's revenue sheet, staff call-backs, and the patient's history.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("procedure_page"))

# ── Finance dashboard (admin) ─────────────────────────────────────────────────
FINANCE_HTML = """
<!DOCTYPE html><html><head><title>Finance Dashboard</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">
  Dr. Manoj Agarwal Clinic
  <small>Finance Dashboard — revenue (consultation · X-ray · procedure · lab)</small>
</div>
<div class="container">

  <div class="card">
    <h2>💰 Income — as of {{ fs.as_of }}</h2>
    {% for label, key in [('Today','today'),('This month','month'),('This year (FY)','year')] %}
    {% set t = fs[key] %}
    <div style="border:1px solid #eee; border-radius:8px; padding:12px 14px; margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; align-items:baseline;">
        <strong style="font-size:15px;">{{ label }}</strong>
        <strong style="font-size:18px; color:#166534;">₹{{ '{:,.0f}'.format(t.net) }}</strong>
      </div>
      <div class="hint" style="margin-top:6px;">
        {% for s,v in t.by_source.items() %}{{ s }}: ₹{{ '{:,.0f}'.format(v) }}&nbsp;&nbsp;{% endfor %}
      </div>
      <div class="hint">Cash ₹{{ '{:,.0f}'.format(t.cash) }} · Online ₹{{ '{:,.0f}'.format(t.online) }}
        · {{ t.patients }} patients · {{ t.rows }} revenue lines</div>
    </div>
    {% endfor %}
  </div>

  <div class="card">
    <h2>📅 Revenue by period</h2>
    <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px;">
      {% for p in presets %}
      <button class="btn" style="width:auto;padding:7px 12px;font-size:12.5px;background:#E8EEF6;color:#1F4E79;"
        onclick="setRange('{{ p.from }}','{{ p.to }}')">{{ p.label }}</button>
      {% endfor %}
    </div>
    <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
      <label class="hint">From <input type="date" id="pfrom" value="{{ today }}"></label>
      <label class="hint">To <input type="date" id="pto" value="{{ today }}"></label>
      <button class="btn" style="width:auto;padding:9px 18px;" onclick="runPeriod()">Show</button>
    </div>
    <div class="hint" style="margin-top:6px;">Tip: a single day = same From and To. Click a source in the result to see its individual lines.</div>
    <div id="periodOut" style="margin-top:14px;"></div>
  </div>

  <div class="card">
    <h2>💊 Pharmacy (Marg) &amp; 🧪 Lab</h2>
    <div class="hint">Lab revenue (NK Pathology) is included in every total above once entries are made via <a href="/lab">Lab Entry</a>. Pharmacy (Marg) is <strong>not yet connected</strong> — it will appear here automatically once that integration is live.</div>
  </div>

  <div class="card">
    <h2>🔎 Patient Lifetime Value</h2>
    <div style="display:flex; gap:8px;">
      <input type="text" id="pq" placeholder="Clinic ID / mobile / UID" style="flex:1;">
      <button class="btn" style="width:auto; padding:10px 18px;" onclick="lookupLTV()">Look up</button>
    </div>
    <div id="ltv" style="margin-top:14px;"></div>
  </div>

  <div class="nav-links"><a href="/">← Home</a> <a href="/lab">🧪 Lab Entry</a></div>
</div>
<script>
  function rsx(n){ return '₹'+Math.round(n||0).toLocaleString(); }
  function setRange(f,t){ document.getElementById('pfrom').value=f; document.getElementById('pto').value=t; runPeriod(); }
  async function runPeriod(){
    var f=document.getElementById('pfrom').value, t=document.getElementById('pto').value;
    var box=document.getElementById('periodOut');
    if(!f||!t){ box.innerHTML='<div class="alert alert-error">Pick both dates.</div>'; return; }
    box.innerHTML='<span class="hint">Calculating…</span>';
    var res=await fetch('/finance/period?from='+f+'&to='+t);
    var d=await res.json();
    if(!d.ok){ box.innerHTML='<div class="alert alert-error">'+(d.message||'Error')+'</div>'; return; }
    var srcOrder=['Consultation','X-ray','Procedure','Lab'];
    var chips=srcOrder.map(function(s){
      var v=(d.by_source||{})[s]||0;
      return '<button class="btn" style="width:auto;padding:6px 10px;font-size:12px;margin:2px;background:#F3F4F6;color:#1F4E79;" onclick="drill(' + "'" + s + "'" + ')">'+s+': '+rsx(v)+' ▸</button>';
    }).join('');
    box.innerHTML=
      '<div style="border:1px solid #eee;border-radius:8px;padding:14px;">'
      +'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
      +'<strong style="font-size:15px;">'+d.from+' → '+d.to+'</strong>'
      +'<strong style="font-size:18px;color:#166534;">'+rsx(d.net)+'</strong></div>'
      +'<div style="margin:8px 0;">'+chips+'</div>'
      +'<div class="hint">Cash '+rsx(d.cash)+' · Online '+rsx(d.online)+' · '+d.patients+' patients · '+d.rows+' revenue lines</div>'
      +'<div id="drillOut" style="margin-top:10px;"></div>'
      +'</div>';
  }
  async function drill(src){
    var f=document.getElementById('pfrom').value, t=document.getElementById('pto').value;
    var box=document.getElementById('drillOut');
    box.innerHTML='<span class="hint">Loading '+src+' lines…</span>';
    var res=await fetch('/finance/lines?source='+encodeURIComponent(src)+'&from='+f+'&to='+t);
    var d=await res.json();
    var lines=d.lines||[];
    if(!lines.length){ box.innerHTML='<div class="hint">No '+src+' lines in this period.</div>'; return; }
    var th='<tr style="background:#DDEBF7;">'
      +'<th style="text-align:left;padding:5px 6px;">Date</th>'
      +'<th style="text-align:left;padding:5px 6px;">Patient</th>'
      +'<th style="text-align:left;padding:5px 6px;">Clinic ID</th>'
      +'<th style="text-align:right;padding:5px 6px;">'+src+' ₹</th>'
      +'<th style="text-align:left;padding:5px 6px;">Mode</th></tr>';
    var trs=lines.map(function(v){
      return '<tr>'
        +'<td style="padding:4px 6px;border-top:1px solid #f0f0f0;">'+v.Date+'</td>'
        +'<td style="padding:4px 6px;border-top:1px solid #f0f0f0;">'+(v.Name||'')+'</td>'
        +'<td style="padding:4px 6px;border-top:1px solid #f0f0f0;color:#6B7280;">'+(v.Clinic_Id||'')+'</td>'
        +'<td style="text-align:right;padding:4px 6px;border-top:1px solid #f0f0f0;font-weight:600;">'+rsx(v.Net)+'</td>'
        +'<td style="padding:4px 6px;border-top:1px solid #f0f0f0;color:#6B7280;font-size:11px;">'+(v.Mode||'')+'</td>'
        +'</tr>';
    }).join('');
    var tot=lines.reduce(function(a,v){return a+(v.Net||0);},0);
    box.innerHTML='<div style="font-weight:600;font-size:13px;color:#374151;margin-bottom:4px;">'+src+' — '+lines.length+' lines · '+rsx(tot)+'</div>'
      +'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:12.5px;">'+th+trs+'</table></div>';
  }
  async function lookupLTV(){
    var q = document.getElementById('pq').value.trim();
    var box = document.getElementById('ltv');
    if(!q){ box.innerHTML=''; return; }
    box.innerHTML='<span class="hint">Searching…</span>';
    var res = await fetch('/finance/patient?q='+encodeURIComponent(q));
    var d = await res.json();
    if(!d.found){ box.innerHTML='<div class="alert alert-error">'+(d.message||'Not found')+'</div>'; return; }
    function rs(n){ return '₹'+Math.round(n||0).toLocaleString(); }
    var src = Object.entries(d.by_source||{}).map(function(e){return e[0]+': '+rs(e[1]);}).join(' · ');
    var th = '<tr style="background:#DDEBF7;">'
      +'<th style="text-align:left;padding:5px 6px;">Date</th>'
      +'<th style="text-align:right;padding:5px 6px;">Consult</th>'
      +'<th style="text-align:right;padding:5px 6px;">X-ray</th>'
      +'<th style="text-align:right;padding:5px 6px;">Proc</th>'
      +'<th style="text-align:right;padding:5px 6px;">Lab</th>'
      +'<th style="text-align:right;padding:5px 6px;">Total</th>'
      +'<th style="text-align:left;padding:5px 6px;">Mode</th></tr>';
    var trs = (d.rows||[]).map(function(v){
      var freeTag = v.Had_Revenue ? '' : ' <span class="tag tag-green" style="font-size:9px;">free</span>';
      var cell=function(n){return '<td style="text-align:right;padding:4px 6px;border-top:1px solid #f0f0f0;">'+(n? Math.round(n).toLocaleString():'–')+'</td>';};
      return '<tr>'
        +'<td style="padding:4px 6px;border-top:1px solid #f0f0f0;">'+v.Date+freeTag+'</td>'
        +cell(v.Consultation)+cell(v.Xray)+cell(v.Procedure)+cell(v.Lab)
        +'<td style="text-align:right;padding:4px 6px;border-top:1px solid #f0f0f0;font-weight:600;">'+(v.Total?rs(v.Total):'–')+'</td>'
        +'<td style="padding:4px 6px;border-top:1px solid #f0f0f0;color:#6B7280;font-size:11px;">'+(v.Mode||'')+(v.Pending? ' · pend '+rs(v.Pending):'')+'</td>'
        +'</tr>';
    }).join('');
    box.innerHTML =
      '<div style="border:1px solid #eee;border-radius:8px;padding:14px;">'
      +'<div style="display:flex;justify-content:space-between;align-items:baseline;"><strong style="font-size:15px;">'+d.name+'</strong>'
      +'<strong style="font-size:18px;color:#166534;">'+rs(d.lifetime_net)+'</strong></div>'
      +'<div class="hint">Clinic ID '+d.clinic_id+' · UID '+d.uid+' · '+(d.mobile||'')+'</div>'
      +'<div class="hint">'+d.visit_count+' visits · '+(d.first_date||'')+' → '+(d.last_date||'')+'</div>'
      +'<div class="hint" style="margin:6px 0;">'+src+'</div>'
      +'<div style="margin-top:8px;font-weight:600;font-size:13px;color:#374151;">Every visit (revenue by source)</div>'
      +'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:12.5px;margin-top:4px;">'+th+trs+'</table></div>'
      +'<div class="hint" style="margin-top:6px;">"free" = ₹0 visit (free revisit or complimentary consultation) — shown so the history is complete.</div>'
      +'</div>';
  }
  document.getElementById('pq').addEventListener('keydown',function(e){
    if(e.key==='Enter'){ e.preventDefault(); lookupLTV(); }
  });
</script>
</body></html>
"""

@app.route("/finance")
@admin_required
def finance_page():
    today = _date.today()
    fs = revenue.finance_summary(today)
    presets = revenue.dashboard_presets(today)
    return render_template_string(FINANCE_HTML, fs=fs, presets=presets,
                                  today=revenue.date_to_str(today))

@app.route("/finance/patient")
@admin_required
def finance_patient():
    from flask import jsonify
    q = request.args.get("q", "")
    h = revenue.patient_full_history(q)
    if not h:
        return jsonify({"found": False, "message": "No visits or revenue found for that patient."})
    return jsonify({
        "found": True, "uid": h["uid"], "clinic_id": h["clinic_id"],
        "name": h["name"], "mobile": h["mobile"],
        "lifetime_net": h["lifetime_net"], "by_source": h["by_source"],
        "visit_count": h["visit_count"],
        "first_date": revenue.date_to_str(h["first_date"]) if h["first_date"] else "",
        "last_date": revenue.date_to_str(h["last_date"]) if h["last_date"] else "",
        "rows": [{
            "Date": r["Date"], "Consultation": r["Consultation"], "Xray": r["Xray"],
            "Procedure": r["Procedure"], "Lab": r["Lab"], "Total": r["Total"],
            "Mode": r["Mode"], "Shift": r["Shift"], "Pending": r["Pending"],
            "Had_Revenue": r["Had_Revenue"],
        } for r in h["rows"]],
    })

@app.route("/finance/period")
@admin_required
def finance_period():
    from flask import jsonify
    sd = revenue.parse_date(request.args.get("from", "").strip())
    ed = revenue.parse_date(request.args.get("to", "").strip())
    if not sd or not ed:
        return jsonify({"ok": False, "message": "Pick valid From and To dates."})
    if ed < sd:
        sd, ed = ed, sd
    t = revenue.totals_for_period(sd, ed)
    t.update({"ok": True, "from": revenue.date_to_str(sd), "to": revenue.date_to_str(ed)})
    return jsonify(t)

@app.route("/finance/lines")
@admin_required
def finance_lines():
    from flask import jsonify
    src = request.args.get("source", "").strip()
    sd = revenue.parse_date(request.args.get("from", "").strip())
    ed = revenue.parse_date(request.args.get("to", "").strip())
    if not src or not sd or not ed:
        return jsonify({"ok": False, "lines": []})
    if ed < sd:
        sd, ed = ed, sd
    return jsonify({"ok": True, "source": src,
                    "lines": revenue.lines_for_period(src, sd, ed)})

CONCESSIONS_HTML = """
<!DOCTYPE html><html><head><title>VIP &amp; Concessions</title>
""" + BASE_STYLE + """
<style>
  .wide { max-width: 1040px; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; margin:4px 0 14px; }
  .chip { background:#EEF2F7; border:1px solid #D6E0EC; border-radius:20px;
          padding:6px 12px; font-size:12.5px; color:#1F4E79; }
  .chip b { font-size:14px; }
  .filters { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
  .fbtn { padding:7px 12px; border:1.5px solid #D1D5DB; background:#fff;
          border-radius:7px; font-size:12.5px; font-weight:600; color:#374151;
          cursor:pointer; }
  .fbtn.active { background:#1F4E79; color:#fff; border-color:#1F4E79; }
  .toolbar { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .toolbar input[type=text]{ flex:1; min-width:180px; margin-bottom:0; }
  table.ct { width:100%; border-collapse:collapse; font-size:12.5px; }
  table.ct th, table.ct td { border-bottom:1px solid #E5E7EB; padding:7px 8px;
          text-align:left; white-space:nowrap; }
  table.ct th { background:#F3F7FB; color:#1F4E79; position:sticky; top:0;
          cursor:pointer; user-select:none; }
  table.ct th:hover { background:#E5EEF7; }
  table.ct tr:hover td { background:#FAFCFF; }
  .num { text-align:right; font-variant-numeric:tabular-nums; }
  .tablewrap { overflow-x:auto; border:1px solid #E5E7EB; border-radius:8px; }
  .muted { color:#6B7280; font-size:12px; }
  .count { font-size:12.5px; color:#374151; margin:8px 2px; font-weight:600; }
</style>
</head><body>
  <div class="header">Dr. Manoj Agarwal Clinic
    <small>VIP &amp; Concession List</small></div>
  <div class="container wide">
    <div class="card">
      <h2>🏷️ VIP &amp; Concessions</h2>
      <div class="muted" style="margin-bottom:10px;">
        Diagnosis data as of <b>{{ s.asof }}</b>{% if s.asof_blank %}
        <span class="tag tag-red" style="margin-left:6px;">no date in source filename</span>{% endif %}
        — refresh by re-absorbing a Docterz patient export in the Diagnosis section.
      </div>
      <div class="chips">
        <span class="chip"><b>{{ s.total }}</b> patients tagged</span>
        <span class="chip">VIP <b>{{ s.vip }}</b></span>
        <span class="chip">Cons. charge (CC) <b>{{ s.with_cc }}</b></span>
        <span class="chip">Pharmacy disc (PD) <b>{{ s.with_pd }}</b></span>
        <span class="chip">Blood-inv disc (BID) <b>{{ s.with_bid }}</b></span>
        {% for nm, cnt in s.schemes %}<span class="chip">{{ nm }} <b>{{ cnt }}</b></span>{% endfor %}
      </div>

      <div class="filters">
        <button class="fbtn active" data-f="all">All</button>
        <button class="fbtn" data-f="vip">VIP only</button>
        <button class="fbtn" data-f="cc">Has CC</button>
        <button class="fbtn" data-f="pd">Has PD</button>
        <button class="fbtn" data-f="bid">Has BID</button>
        <button class="fbtn" data-f="scheme">On a scheme</button>
      </div>
      <div class="toolbar">
        <input type="text" id="q" placeholder="Search name, Clinic ID, or mobile…">
        <a class="btn btn-green" style="width:auto; padding:10px 16px;"
           href="/concessions/export">⬇ Excel</a>
      </div>
      <div class="count" id="count"></div>

      <div class="tablewrap">
        <table class="ct" id="tbl">
          <thead><tr>
            <th data-sort="str">Clinic ID</th>
            <th data-sort="str">Patient Name</th>
            <th data-sort="str">Mobile</th>
            <th data-sort="str">Age/Sex</th>
            <th data-sort="str">VIP</th>
            <th data-sort="str">Scheme</th>
            <th data-sort="num">CC ₹</th>
            <th data-sort="num">PD %</th>
            <th data-sort="num">BID %</th>
            <th data-sort="str">Diagnosis</th>
            <th data-sort="str">Pri</th>
          </tr></thead>
          <tbody>
          {% for r in s.rows %}
            <tr data-vip="{{ '1' if r.vip else '0' }}"
                data-cc="{{ '1' if r.cc else '0' }}"
                data-pd="{{ '1' if r.pd else '0' }}"
                data-bid="{{ '1' if r.bid else '0' }}"
                data-scheme="{{ '1' if r.scheme else '0' }}"
                data-search="{{ (r.name ~ ' ' ~ r.clinic_id ~ ' ' ~ r.mobile)|lower }}">
              <td>{{ r.clinic_id }}</td>
              <td>{{ r.name }}</td>
              <td>{{ r.mobile }}</td>
              <td>{{ r.age }}{% if r.age and r.sex %}/{% endif %}{{ r.sex }}</td>
              <td>{% if r.vip %}<span class="tag tag-red">VIP</span>{% endif %}</td>
              <td>{{ r.scheme }}</td>
              <td class="num">{{ r.cc }}</td>
              <td class="num">{{ r.pd }}</td>
              <td class="num">{{ r.bid }}</td>
              <td>{{ r.diagnosis }}</td>
              <td>{{ r.priority }}</td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
      {% if s.total == 0 %}
        <p class="muted" style="margin-top:12px;">No concession markers found yet.
        Re-absorb a Docterz patient export in the Diagnosis section first.</p>
      {% endif %}
    </div>
    <div class="nav-links">
      <a href="/">← Home</a><a href="/finance">💰 Finance</a>
    </div>
  </div>

<script>
(function(){
  var rows = Array.prototype.slice.call(document.querySelectorAll('#tbl tbody tr'));
  var q = document.getElementById('q');
  var countEl = document.getElementById('count');
  var filter = 'all';

  function matchesFilter(tr){
    if(filter === 'all') return true;
    return tr.getAttribute('data-' + filter) === '1';
  }
  function apply(){
    var term = (q.value || '').trim().toLowerCase();
    var shown = 0;
    rows.forEach(function(tr){
      var ok = matchesFilter(tr) &&
               (term === '' || tr.getAttribute('data-search').indexOf(term) !== -1);
      tr.style.display = ok ? '' : 'none';
      if(ok) shown++;
    });
    countEl.textContent = 'Showing ' + shown + ' of ' + rows.length + ' patients';
  }
  q.addEventListener('input', apply);
  document.querySelectorAll('.fbtn').forEach(function(b){
    b.addEventListener('click', function(){
      document.querySelectorAll('.fbtn').forEach(function(x){ x.classList.remove('active'); });
      b.classList.add('active');
      filter = b.getAttribute('data-f');
      apply();
    });
  });

  // column sorting
  var ths = document.querySelectorAll('#tbl thead th');
  var tbody = document.querySelector('#tbl tbody');
  ths.forEach(function(th, idx){
    var asc = true;
    th.addEventListener('click', function(){
      var type = th.getAttribute('data-sort');
      var sorted = rows.slice().sort(function(a, b){
        var av = a.children[idx].textContent.trim();
        var bv = b.children[idx].textContent.trim();
        if(type === 'num'){
          var an = parseFloat(av); var bn = parseFloat(bv);
          if(isNaN(an)) an = -1; if(isNaN(bn)) bn = -1;
          return asc ? an - bn : bn - an;
        }
        return asc ? av.localeCompare(bv) : bv.localeCompare(av);
      });
      asc = !asc;
      sorted.forEach(function(tr){ tbody.appendChild(tr); });
    });
  });

  apply();
})();
</script>
</body></html>
"""


@app.route("/calls")
@login_required
def calls_page():
    from processor import call_monitor_stats, call_reconciliation_stats
    d = request.args.get("date") or None
    s = call_monitor_stats(d)
    rec = call_reconciliation_stats()
    return render_template_string(CALLS_HTML, s=s, rec=rec, role=current_role())


@app.route("/callaudit", methods=["GET", "POST"])
@login_required
def call_audit_page():
    from processor import (ingest_outbound_log, reconcile_calls,
                           fetch_feed_auto, feed_url_configured,
                           open_reinstatements_view, clear_reinstatement)
    msg = err = None
    if request.method == "POST":
        act = request.form.get("action")
        if act == "refresh":
            rep = fetch_feed_auto()
            if rep.get("ok"):
                msg = (f"Refreshed from Google — {rep.get('added', 0)} new "
                       f"({rep.get('total', 0)} calls on file).")
            else:
                err = rep.get("error", "could not refresh from Google.")
        elif act == "clear_reinstate":
            rid = request.form.get("reinstate_id", "")
            if clear_reinstatement(rid, by="doctor", reason="reviewed (recording)"):
                msg = f"Reinstatement {rid} cleared."
            else:
                err = "Could not clear that reinstatement."
        else:
            f = request.files.get("outbound_xlsx")
            if not f or not f.filename:
                err = "Choose an Outbound_Log / Call_Feed file (.csv or .xlsx) to upload."
            elif not f.filename.lower().endswith((".csv", ".xlsx", ".xlsm")):
                err = "The file must be a .csv or .xlsx."
            else:
                path = str(UPLOAD_DIR / secure_filename(f.filename))
                f.save(path)
                rep = ingest_outbound_log(path, source_name=f.filename)
                if rep.get("ok"):
                    msg = (f"Loaded {rep['rows_in_file']} rows — {rep['added']} new "
                           f"({rep['total']} calls on file).")
                else:
                    err = rep.get("error", "could not read the file.")
    rec = reconcile_calls()
    reinstates = open_reinstatements_view()
    return render_template_string(AUDIT_HTML, rec=rec, msg=msg, err=err,
                                  reinstates=reinstates,
                                  feed_on=bool(feed_url_configured()), role=current_role())


@app.route("/callins", methods=["GET", "POST"])
@login_required
def callins_page():
    from processor import find_called_in_and_due, fetch_feed_auto, feed_url_configured
    msg = err = None
    if request.method == "POST" and request.form.get("action") == "refresh":
        rep = fetch_feed_auto()
        if rep.get("ok"):
            msg = f"Refreshed from Google — {rep.get('total', 0)} calls on file."
        else:
            err = rep.get("error", "could not refresh from Google.")
    b = find_called_in_and_due()
    return render_template_string(CALLINS_HTML, b=b, msg=msg, err=err,
                                  feed_on=bool(feed_url_configured()), role=current_role())


@app.route("/confirm", methods=["GET", "POST"])
@login_required
def confirm_page():
    from processor import (open_confirmations_view, confirm_confirmation,
                           reject_confirmation, review_confirmation)
    msg = err = None
    if request.method == "POST":
        act = request.form.get("action")
        cid = request.form.get("confirm_id", "")
        who = current_role()
        if act == "confirm" and confirm_confirmation(cid, by=who):
            msg = f"{cid} confirmed — closed."
        elif act == "reject" and reject_confirmation(cid, by=who):
            msg = f"{cid} rejected — patient put back on the call sheet."
        elif act == "review" and review_confirmation(cid, by=who):
            msg = f"{cid} reviewed."
        else:
            err = "Could not update that item (it may already be settled)."
    rows = open_confirmations_view()
    return render_template_string(CONFIRM_HTML, rows=rows, msg=msg, err=err,
                                  role=current_role())


@app.route("/concessions")
@admin_required
def concessions_page():
    s = concessions.concession_summary()
    return render_template_string(CONCESSIONS_HTML, s=s)


@app.route("/concessions/export")
@admin_required
def concessions_export():
    out = OUTPUTS_DIR / "VIP_Concession_List.xlsx"
    concessions.build_concession_xlsx(out)
    return send_file(out, as_attachment=True,
                     download_name="VIP_Concession_List.xlsx")


# ─────────────────────────────────────────────────────────────────────────────
# REVENUE INGEST — periodic external-revenue upload (Labmate / Marg) + review queue
# Added Session 15. Heavy logic is in revenue_ingest.py (proven offline).
# Policy: only confidently-MATCHED bills hit the live ledger (so /finance counts
# them now); REVIEW + UNCLASSIFIED are HELD in revenue_pending_review.csv and only
# enter the ledger when the doctor PROMOTES them after manual checking.
# ─────────────────────────────────────────────────────────────────────────────
import revenue_ingest

# preview payloads are stashed server-side between the upload and the confirm click,
# keyed by a short token (avoids putting big row-lists in the browser form).
_REVENUE_PREVIEWS = {}

def _revenue_status():
    """Banner data for the home page + upload page (mirrors _diagnosis_status)."""
    try:
        return revenue_ingest.meta_status()
    except Exception:
        return {}


@app.route("/revenue/upload", methods=["GET"])
@admin_required
def revenue_upload_page():
    return render_template_string(REVENUE_UPLOAD_HTML, role=current_role(),
                                  rev=_revenue_status())


@app.route("/revenue/preview", methods=["POST"])
@admin_required
def revenue_preview():
    import uuid as _uuid
    f = request.files.get("revenue_file")
    if not f or not f.filename:
        flash("Please choose a Labmate (.xlsx) or Marg (.xls) file.", "error")
        return redirect(url_for("revenue_upload_page"))
    if not f.filename.lower().endswith((".xlsx", ".xls")):
        flash("Only Excel files (.xlsx / .xls) are accepted.", "error")
        return redirect(url_for("revenue_upload_page"))
    save_path = str(UPLOAD_DIR / secure_filename(f.filename))
    f.save(save_path)
    try:
        prev = revenue_ingest.preview(save_path)
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f"Could not read that file: {e}", "error")
        return redirect(url_for("revenue_upload_page"))
    token = _uuid.uuid4().hex[:12]
    _REVENUE_PREVIEWS[token] = prev
    # keep the stash small — drop anything but the last few
    if len(_REVENUE_PREVIEWS) > 8:
        for k in list(_REVENUE_PREVIEWS)[:-8]:
            _REVENUE_PREVIEWS.pop(k, None)
    return render_template_string(REVENUE_PREVIEW_HTML, role=current_role(),
                                  p=prev, token=token)


@app.route("/revenue/commit", methods=["POST"])
@admin_required
def revenue_commit():
    token = request.form.get("token", "")
    prev = _REVENUE_PREVIEWS.pop(token, None)
    if not prev:
        flash("That preview expired. Please upload the file again.", "error")
        return redirect(url_for("revenue_upload_page"))
    try:
        res = revenue_ingest.commit(prev)
        flash(f"✅ Added to /finance: {res['matched_written']} matched bills. "
              f"Held for your review: {res['held_written']} "
              f"(skipped {res['matched_skipped_dup']} already-loaded).", "success")
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f"Error writing: {e}", "error")
    return redirect(url_for("revenue_review_page"))


@app.route("/revenue/review", methods=["GET"])
@admin_required
def revenue_review_page():
    pend = revenue_ingest.load_pending()
    rows = []
    for _, r in pend.iterrows():
        cand_uids = [x for x in str(r.get("Cand_UIDs", "")).split(";") if x]
        cand_cids = [x for x in str(r.get("Cand_Clinic_Ids", "")).split(";") if x]
        cand_nms  = [x for x in str(r.get("Cand_Names", "")).split(";") if x]
        cands = []
        for i in range(len(cand_uids)):
            cands.append({"uid": cand_uids[i],
                          "clinic_id": cand_cids[i] if i < len(cand_cids) else "",
                          "name": cand_nms[i] if i < len(cand_nms) else ""})
        rows.append({
            "rid": r["Revenue_ID"], "date": r["Date"], "net": r["Net"],
            "source": r["Source"], "status": r.get("Match_Status", ""),
            "bill_name": r.get("Bill_Name", ""), "bill_mobile": r.get("Bill_Mobile", ""),
            "bill_cid": r.get("Bill_Clinic_Id", ""), "cands": cands,
        })
    return render_template_string(REVENUE_REVIEW_HTML, role=current_role(), rows=rows)


@app.route("/revenue/promote", methods=["POST"])
@admin_required
def revenue_promote():
    rid = request.form.get("rid", "").strip()
    uid = request.form.get("uid", "").strip()
    clinic_id = request.form.get("clinic_id", "").strip()
    name = request.form.get("name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    if not rid or not uid:
        flash("Pick a patient to attribute this bill to.", "error")
        return redirect(url_for("revenue_review_page"))
    try:
        res = revenue_ingest.promote(rid, uid, clinic_id, name, mobile)
        if res.get("ok"):
            flash(f"✅ ₹{res['net']:.0f} attributed to {res['name']} and added to /finance.", "success")
        else:
            flash(res.get("message", "Could not promote."), "error")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("revenue_review_page"))


@app.route("/revenue/lookup")
@admin_required
def revenue_lookup():
    """For the review screen's manual search (when none of the candidates is right)."""
    from flask import jsonify
    import revenue as _rev
    hit = _rev.lookup_patient(request.args.get("q", ""))
    if hit and hit.get("uid"):
        return jsonify({"found": True, "uid": hit["uid"], "clinic_id": hit["clinic_id"],
                        "name": hit["name"], "mobile": hit["mobile"]})
    msg = hit.get("ambiguous") if hit else "No patient found."
    return jsonify({"found": False, "message": msg or "No patient found."})


REVENUE_UPLOAD_HTML = """
<!DOCTYPE html><html><head><title>Revenue Upload</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">Dr. Manoj Agarwal Clinic <small>External Revenue — Pharmacy &amp; Lab Upload</small></div>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}<div class="alert alert-{{ cat }}">{{ msg }}</div>{% endfor %}
  {% endwith %}

  {% if rev.as_of_date or rev.ingested_on %}
  <div class="card">
    <h2>📊 Last Revenue Upload</h2>
    <div style="background:{{ '#FEF3C7' if rev.stale else '#ECFDF5' }};
      border:1px solid {{ '#F59E0B' if rev.stale else '#A7F3D0' }};
      border-radius:8px; padding:12px 14px; font-size:13px;">
      <div style="font-size:15px; font-weight:700; color:{{ '#92400E' if rev.stale else '#065F46' }};">
        Revenue data as of: {{ rev.as_of_label }}
        {% if rev.stale %}&nbsp;·&nbsp;⚠️ {{ rev.age_days }} days old — time for a fresh export{% endif %}
      </div>
      <div style="color:#4B5563; margin-top:5px;">
        Last absorbed {{ rev.ingested_on or '—' }} from <strong>{{ rev.source_file }}</strong>
        ({{ rev.kind }}).<br>
        ₹{{ '{:,.0f}'.format(rev.matched_net) }} matched into /finance ·
        ₹{{ '{:,.0f}'.format(rev.held_net) }} held that run.<br>
        <strong>{{ rev.pending_count }}</strong> bills (₹{{ '{:,.0f}'.format(rev.pending_net) }})
        currently waiting in <a href="/revenue/review">Review &amp; Promote</a>.
      </div>
    </div>
  </div>
  {% endif %}

  <div class="card">
    <h2>⬆️ Upload a revenue file</h2>
    <p class="hint" style="margin-bottom:14px;">
      Accepts the <strong>Labmate</strong> pathology export (.xlsx) or the
      <strong>Marg</strong> pharmacy export (.xls). You'll see a <em>preview</em>
      first — nothing is saved until you confirm. Only confident matches go into
      Finance; the rest wait for your check.
    </p>
    <form method="POST" action="/revenue/preview" enctype="multipart/form-data">
      <label>Revenue file (.xlsx / .xls)</label>
      <input type="file" name="revenue_file" accept=".xlsx,.xls" required
        style="width:100%; padding:9px; border:1.5px solid #D1D5DB; border-radius:7px;
        margin-bottom:16px; background:#fafafa;">
      <button class="btn" type="submit">Preview match</button>
    </form>
  </div>

  <div class="nav-links"><a href="/">← Home</a> <a href="/revenue/review">🔎 Review &amp; Promote</a> <a href="/finance">💰 Finance</a></div>
</div></body></html>
"""

REVENUE_PREVIEW_HTML = """
<!DOCTYPE html><html><head><title>Revenue Preview</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">Dr. Manoj Agarwal Clinic <small>Revenue Upload — Preview</small></div>
<div class="container">
  <div class="card">
    <h2>🔍 Preview — {{ p.source_file }}</h2>
    <p class="hint">{{ p.kind }} · as of {{ p.as_of }} · window ±{{ p.window_days }} days ·
      {{ p.bills_in }} bills · total ₹{{ '{:,.0f}'.format(p.net_in) }}</p>

    <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:8px; padding:12px 14px; margin:10px 0;">
      <div style="font-weight:700; color:#065F46; font-size:15px;">
        ✅ Will be ADDED to Finance now:
        {{ p.new_matched_count }} bills · ₹{{ '{:,.0f}'.format(p.new_matched_net) }}
      </div>
      {% if p.already_in_ledger %}<div style="color:#4B5563; font-size:12px;">({{ p.already_in_ledger }} matched bills already in the ledger — will be skipped.)</div>{% endif %}
    </div>

    <div style="background:#FEF3C7; border:1px solid #F59E0B; border-radius:8px; padding:12px 14px; margin:10px 0;">
      <div style="font-weight:700; color:#92400E; font-size:15px;">
        ⏸️ HELD for your review (NOT counted yet):
        {{ p.buckets.review.count + p.buckets.unclassified.count }} bills ·
        ₹{{ '{:,.0f}'.format(p.buckets.review.net + p.buckets.unclassified.net) }}
      </div>
      <div style="color:#4B5563; font-size:12px;">
        {{ p.buckets.review.count }} ambiguous (2+ patients) ·
        {{ p.buckets.unclassified.count }} no-match. You promote these after checking.
      </div>
    </div>

    <table style="width:100%; border-collapse:collapse; font-size:13px; margin-top:8px;">
      <tr style="text-align:left; color:#6B7280;"><th>Match type</th><th>Bills</th><th style="text-align:right;">₹</th></tr>
      {% for k, v in p.by_breakdown.items() %}
      <tr style="border-top:1px solid #f1f1f1;"><td>{{ k }}</td><td>{{ v.count }}</td>
        <td style="text-align:right;">₹{{ '{:,.0f}'.format(v.net) }}</td></tr>
      {% endfor %}
    </table>

    <form method="POST" action="/revenue/commit" style="margin-top:16px;">
      <input type="hidden" name="token" value="{{ token }}">
      <button class="btn btn-green" type="submit">Confirm &amp; append matched to Finance</button>
    </form>
    <p class="hint" style="margin-top:8px;">No rupee is dropped: ₹{{ '{:,.0f}'.format(p.net_in) }} in =
      matched + held. Confirm only writes matched to /finance; held money waits in Review.</p>
  </div>
  <div class="nav-links"><a href="/revenue/upload">← Upload another</a> <a href="/">Home</a></div>
</div></body></html>
"""

REVENUE_REVIEW_HTML = """
<!DOCTYPE html><html><head><title>Revenue Review</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">Dr. Manoj Agarwal Clinic <small>Revenue — Review &amp; Promote held bills</small></div>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}<div class="alert alert-{{ cat }}">{{ msg }}</div>{% endfor %}
  {% endwith %}

  <div class="card">
    <h2>🔎 Held bills awaiting your decision</h2>
    <p class="hint">These were NOT auto-attributed (ambiguous name, or no patient found).
      They are NOT in /finance yet. Pick the right patient and promote — that adds the
      money to Finance under that patient. Nothing here is counted until you do.</p>
    {% if not rows %}
      <p style="color:#065F46; font-weight:600; padding:10px 0;">✅ Nothing pending. All clear.</p>
    {% endif %}
  </div>

  {% for r in rows %}
  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:baseline;">
      <div><strong>{{ r.bill_name or '(no name)' }}</strong>
        <span style="color:#9aa; font-size:12px;">· {{ r.date }} ·
        {{ r.source }}{% if r.status=='unclassified' %} · no match found{% endif %}</span></div>
      <div style="font-weight:700; color:#166534;">₹{{ r.net }}</div>
    </div>
    {% if r.bill_mobile or r.bill_cid %}<div class="hint">on bill: mobile {{ r.bill_mobile or '—' }} · Clinic ID {{ r.bill_cid or '—' }}</div>{% endif %}

    {% if r.cands %}
    <div style="margin-top:8px; font-size:13px; color:#6B7280;">Candidates:</div>
    {% for c in r.cands %}
    <form method="POST" action="/revenue/promote" style="display:flex; gap:8px; align-items:center;
      padding:6px 0; border-bottom:1px solid #f3f3f3;">
      <input type="hidden" name="rid" value="{{ r.rid }}">
      <input type="hidden" name="uid" value="{{ c.uid }}">
      <input type="hidden" name="clinic_id" value="{{ c.clinic_id }}">
      <input type="hidden" name="name" value="{{ c.name }}">
      <span style="flex:1;">{{ c.name }} <span style="color:#9aa;">(Clinic ID {{ c.clinic_id }})</span></span>
      <button class="btn btn-green" style="width:auto; padding:7px 14px;" type="submit">Promote ₹{{ r.net }} → this patient</button>
    </form>
    {% endfor %}
    {% endif %}

    <div style="margin-top:10px; font-size:13px;">
      <span style="color:#6B7280;">None of these? Search by Clinic ID / mobile:</span>
      <div style="display:flex; gap:6px; margin-top:4px;">
        <input type="text" id="q_{{ r.rid }}" placeholder="Clinic ID or mobile" style="flex:1;">
        <button class="btn" style="width:auto; padding:7px 12px;" onclick="findFor('{{ r.rid }}','{{ r.net }}')">Find</button>
      </div>
      <form method="POST" action="/revenue/promote" id="mf_{{ r.rid }}" style="display:none; margin-top:6px;">
        <input type="hidden" name="rid" value="{{ r.rid }}">
        <input type="hidden" name="uid" id="muid_{{ r.rid }}">
        <input type="hidden" name="clinic_id" id="mcid_{{ r.rid }}">
        <input type="hidden" name="name" id="mname_{{ r.rid }}">
        <input type="hidden" name="mobile" id="mmob_{{ r.rid }}">
        <button class="btn btn-green" type="submit" id="mbtn_{{ r.rid }}"></button>
      </form>
      <div id="msg_{{ r.rid }}" class="hint"></div>
    </div>
  </div>
  {% endfor %}

  <div class="nav-links"><a href="/revenue/upload">← Upload</a> <a href="/finance">💰 Finance</a> <a href="/">Home</a></div>
</div>
<script>
async function findFor(rid, net){
  var q = document.getElementById('q_'+rid).value.trim();
  var msg = document.getElementById('msg_'+rid);
  if(!q){ msg.textContent='Enter a Clinic ID or mobile.'; return; }
  msg.style.color='#6B7280'; msg.textContent='Searching…';
  try{
    var res = await fetch('/revenue/lookup?q='+encodeURIComponent(q));
    var d = await res.json();
    if(d.found){
      document.getElementById('muid_'+rid).value=d.uid;
      document.getElementById('mcid_'+rid).value=d.clinic_id;
      document.getElementById('mname_'+rid).value=d.name;
      document.getElementById('mmob_'+rid).value=d.mobile;
      document.getElementById('mbtn_'+rid).textContent='Promote ₹'+net+' → '+d.name;
      document.getElementById('mf_'+rid).style.display='block';
      msg.style.color='#065F46'; msg.textContent='Found: '+d.name;
    } else { msg.style.color='#B91C1C'; msg.textContent=d.message||'Not found.'; }
  }catch(e){ msg.style.color='#B91C1C'; msg.textContent='Lookup failed.'; }
}
</script>
</body></html>
"""

if __name__ == "__main__":
    # Running app.py directly = local clinic-PC mode: 127.0.0.1 only, no login.
    # (For a real VPS, serve via wsgi/gunicorn with TRACKER_LOCAL unset and both
    # passwords set; that path calls _require_server_credentials().)
    if not LOCAL_MODE:
        _require_server_credentials()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
