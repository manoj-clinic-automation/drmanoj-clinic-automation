#!/usr/bin/env python3
"""
Asset Register — v1.2.0
Single-file Flask + SQLite app. Multi-user (2 roles: owner / manager), 3 seeded users.
Location-class visibility + per-row hide overrides; hide_price extends to invoice files.
Generic expiries + attachments schema (assets now, staff module included, more later).
Session-epoch auth (GutLog v3.1 pattern). WhatsApp-stack integration via /api/due token endpoint.

v1.2.0 adds:
  - Drafts: scan/upload FIRST, fill the asset form after. Drafts never expire.
  - Owner-only document delete and replace (replace re-derives the sensitive flag).
  - document_text column + search over digitised document text (visibility-gated).
  - OCR adapter stub — digitise_document() returns 'skipped' until v1.2.1 wires Sarvam.

Run:   gunicorn -w 2 -b 127.0.0.1:8030 asset_register:app
Env:   ASSETS_DB (default ./assets.db)   ASSETS_UPLOADS (default ./uploads)
       SARVAM_API_KEY (optional; absent = OCR skipped, everything else unaffected)
"""
import os, sqlite3, secrets, functools, datetime, mimetypes
from flask import (Flask, request, session, redirect, url_for, abort, g,
                   render_template_string, send_file, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
from werkzeug.utils import secure_filename

APP_VERSION = "1.4.2"
DB_PATH = os.environ.get("ASSETS_DB", os.path.join(os.path.dirname(__file__), "assets.db"))
UPLOAD_DIR = os.environ.get("ASSETS_UPLOADS", os.path.join(os.path.dirname(__file__), "uploads"))
SCANNER_JS_PATH = os.path.join(os.path.dirname(__file__), "scanner_widget.js")  # shared scanner widget (Stage 1A)
ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png", "webp", "heic", "doc", "docx"}
THRESHOLD_DEFAULT = 60  # days; per-expiry override supported
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "").strip()
OCR_EXT = {"pdf", "jpg", "jpeg", "png"}   # formats Sarvam Doc AI accepts

app = Flask(__name__)

# ---------------------------------------------------------------- DB helpers
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN('owner','manager')),
  password_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS locations(
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
  visibility TEXT NOT NULL DEFAULT 'general' CHECK(visibility IN('general','owner_only')));
CREATE TABLE IF NOT EXISTS entities(
  id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
  visibility TEXT NOT NULL DEFAULT 'general' CHECK(visibility IN('general','owner_only')),
  sort INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS zones(
  id INTEGER PRIMARY KEY, entity_id INTEGER NOT NULL REFERENCES entities(id),
  name TEXT NOT NULL, sort INTEGER NOT NULL DEFAULT 0,
  UNIQUE(entity_id, name));
CREATE TABLE IF NOT EXISTS assets(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL,
  location_id INTEGER NOT NULL REFERENCES locations(id),
  category TEXT NOT NULL DEFAULT 'Other',
  purchase_date TEXT, price REAL, vendor TEXT, vendor_phone TEXT,
  serial_no TEXT, status TEXT NOT NULL DEFAULT 'Active',
  contract_type TEXT NOT NULL DEFAULT 'None', provider TEXT, contract_cost REAL,
  notes TEXT, hidden INTEGER NOT NULL DEFAULT 0, hide_price INTEGER NOT NULL DEFAULT 0,
  created_by INTEGER REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS staff(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, role_title TEXT, phone TEXT,
  joined_date TEXT, status TEXT NOT NULL DEFAULT 'Active', notes TEXT,
  hidden INTEGER NOT NULL DEFAULT 0,
  created_by INTEGER REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS expiries(
  id INTEGER PRIMARY KEY,
  entity TEXT NOT NULL CHECK(entity IN('asset','staff')),
  entity_id INTEGER NOT NULL, label TEXT NOT NULL, due_date TEXT NOT NULL,
  threshold_days INTEGER NOT NULL DEFAULT 60, resolved INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS attachments(
  id INTEGER PRIMARY KEY,
  entity TEXT NOT NULL CHECK(entity IN('asset','staff','service')),
  entity_id INTEGER NOT NULL, stored_name TEXT NOT NULL, orig_name TEXT NOT NULL,
  sensitive INTEGER NOT NULL DEFAULT 0,
  document_text TEXT,
  ocr_status TEXT NOT NULL DEFAULT 'pending',
  uploaded_by INTEGER REFERENCES users(id),
  uploaded_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS drafts(
  id INTEGER PRIMARY KEY, stored_name TEXT NOT NULL, orig_name TEXT NOT NULL,
  note TEXT,
  created_by INTEGER REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS service_logs(
  id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL REFERENCES assets(id),
  log_date TEXT NOT NULL, work TEXT NOT NULL, cost REAL, done_by TEXT,
  next_due TEXT, created_by INTEGER REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
"""

CATEGORIES = ["Lab Equipment", "Medical Equipment", "Electrical (Battery/Inverter/Stabilizer)",
              "IT / Electronics", "Appliance", "Furniture", "Vehicle", "Document / Licence", "Other"]
STATUSES = ["Active", "Under Repair", "Retired", "Sold"]
CONTRACT_TYPES = ["None", "Warranty only", "AMC", "CMC"]

# --- Phase A taxonomy (D-pending): 3 owning entities x per-entity zones ---
ENTITY_SEED = [("Dr Manoj Clinic", "general", 1),
               ("NK Pathology",    "general", 2),
               ("Personal",        "owner_only", 3)]
ZONE_SEED = {
    "Dr Manoj Clinic": ["Unassigned", "Reception", "Consultation", "X-ray/Imaging",
                        "Minor OT/Procedure", "Physiotherapy", "Pharmacy",
                        "Waiting/Common", "Power/Backup", "IT/Network"],
    "NK Pathology":    ["Unassigned", "Sample collection", "Lab bench/Analysers",
                        "Reagent store", "Reception", "Power/Backup", "IT"],
    "Personal":        ["Unassigned", "Dr Manoj", "Dr Bhawna", "Home",
                        "Vehicle", "Devices", "Documents/Licences"],
}
# old location name -> (entity name, zone name); backfill is refused if any live
# location is absent here (fail-loud, D236) so nothing is silently miscategorised.
LOC_TAXONOMY_MAP = {
    "Clinic":               ("Dr Manoj Clinic", "Unassigned"),
    "NK Path":              ("NK Pathology",    "Unassigned"),
    "Personal - Dr Manoj":  ("Personal",        "Dr Manoj"),
    "Personal - Dr Bhawna": ("Personal",        "Dr Bhawna"),
    "Home (Shared)":        ("Personal",        "Home"),
}

def migrate(db):
    """Additive column migration for databases created before v1.2.0.
    CREATE TABLE IF NOT EXISTS cannot add columns to an existing table."""
    cols = {r[1] for r in db.execute("PRAGMA table_info(attachments)")}
    if "document_text" not in cols:
        db.execute("ALTER TABLE attachments ADD COLUMN document_text TEXT")
    if "ocr_status" not in cols:
        db.execute("ALTER TABLE attachments ADD COLUMN ocr_status TEXT NOT NULL DEFAULT 'pending'")
    acols = {r[1] for r in db.execute("PRAGMA table_info(assets)")}
    if "entity_id" not in acols:
        db.execute("ALTER TABLE assets ADD COLUMN entity_id INTEGER")   # -> entities(id)
    if "zone_id" not in acols:
        db.execute("ALTER TABLE assets ADD COLUMN zone_id INTEGER")     # -> zones(id)

def seed_taxonomy(db):
    """Idempotent: seed the 3 entities + their zones if not present.
    Runs on every restart; guarded by COUNT so it seeds once, then no-ops.
    Never deletes or renames — only inserts missing rows."""
    if db.execute("SELECT COUNT(*) FROM entities").fetchone()[0] == 0:
        for name, vis, srt in ENTITY_SEED:
            db.execute("INSERT INTO entities(name,visibility,sort) VALUES(?,?,?)", (name, vis, srt))
    ent = {r[1]: r[0] for r in db.execute("SELECT id,name FROM entities")}
    for ename, zones in ZONE_SEED.items():
        eid = ent.get(ename)
        if not eid:
            continue
        for i, zname in enumerate(zones):
            db.execute("INSERT OR IGNORE INTO zones(entity_id,name,sort) VALUES(?,?,?)",
                       (eid, zname, i))

def migrate_taxonomy(apply=False):
    """One-time backfill of assets.entity_id/zone_id from the old location.
    Dry-run by default (prints the plan, changes nothing). --apply commits.
    Idempotent (only touches rows where entity_id IS NULL). Fail-loud: refuses
    to apply if any live location is missing from LOC_TAXONOMY_MAP."""
    init_db()  # guarantees tables + seed
    db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row
    ent = {r["name"]: r["id"] for r in db.execute("SELECT id,name FROM entities")}
    zmap = {(r["entity_id"], r["name"]): r["id"]
            for r in db.execute("SELECT id,entity_id,name FROM zones")}
    rows = db.execute("""SELECT a.id aid, l.name loc FROM assets a
                         JOIN locations l ON l.id=a.location_id
                         WHERE a.entity_id IS NULL""").fetchall()
    plan, unmapped, updates = {}, {}, []
    for r in rows:
        loc = r["loc"]
        if loc not in LOC_TAXONOMY_MAP:
            unmapped[loc] = unmapped.get(loc, 0) + 1
            continue
        en, zn = LOC_TAXONOMY_MAP[loc]
        eid = ent[en]; zid = zmap[(eid, zn)]
        plan[(en, zn)] = plan.get((en, zn), 0) + 1
        updates.append((eid, zid, r["aid"]))
    total_assets = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    already = db.execute("SELECT COUNT(*) FROM assets WHERE entity_id IS NOT NULL").fetchone()[0]
    print("=== TAXONOMY BACKFILL %s ===" % ("APPLY" if apply else "DRY-RUN"))
    print("assets total: %d | already classified: %d | to backfill now: %d"
          % (total_assets, already, len(updates)))
    for (en, zn), n in sorted(plan.items()):
        print("  %-18s / %-16s <- %d" % (en, zn, n))
    if unmapped:
        print("  !! UNMAPPED LOCATIONS (backfill will be REFUSED):")
        for loc, n in unmapped.items():
            print("     %r  x%d" % (loc, n))
    if apply:
        if unmapped:
            print("REFUSED: unmapped locations present. Fix LOC_TAXONOMY_MAP first. Nothing changed.")
        elif updates:
            db.executemany("UPDATE assets SET entity_id=?, zone_id=? WHERE id=?", updates)
            db.commit()
            print("APPLIED: %d rows updated." % len(updates))
        else:
            print("Nothing to do (all rows already classified).")
    else:
        print("(dry-run: nothing changed. Re-run with --apply to commit.)")
    db.close()
    return len(updates), unmapped

def init_db(seed=True):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    migrate(db)
    seed_taxonomy(db)
    cur = db.execute("SELECT COUNT(*) c FROM users")
    if seed and cur.fetchone()[0] == 0:
        for u, d, r, p in [("manoj", "Dr Manoj", "owner", "change-me-manoj"),
                           ("bhawna", "Dr Bhawna", "owner", "change-me-bhawna"),
                           ("manager", "Manager", "manager", "change-me-manager")]:
            db.execute("INSERT INTO users(username,display_name,role,password_hash) VALUES(?,?,?,?)",
                       (u, d, r, generate_password_hash(p)))
        for n, v in [("NK Path", "general"), ("Clinic", "general"),
                     ("Personal - Dr Manoj", "owner_only"),
                     ("Personal - Dr Bhawna", "owner_only"), ("Home (Shared)", "owner_only")]:
            db.execute("INSERT INTO locations(name,visibility) VALUES(?,?)", (n, v))
        db.execute("INSERT INTO settings(key,value) VALUES('auth_epoch','1')")
        db.execute("INSERT INTO settings(key,value) VALUES('api_token',?)", (secrets.token_urlsafe(24),))
        db.execute("INSERT INTO settings(key,value) VALUES('secret_key',?)", (secrets.token_urlsafe(32),))
    db.commit(); db.close()

def setting(key):
    return get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()["value"]

def _load_secret():
    # v1.2.0 FIX: always run init_db(), not only when the file is absent.
    # gunicorn merely imports this module; if schema creation and migrate() are
    # skipped on an existing database, new tables and columns never appear and
    # every route touching them 500s. init_db() is idempotent:
    #   - executescript uses CREATE TABLE IF NOT EXISTS
    #   - migrate() checks PRAGMA table_info before each ALTER
    #   - seeding is guarded by COUNT(*)==0 on users
    init_db()
    db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row
    row = db.execute("SELECT value FROM settings WHERE key='secret_key'").fetchone()
    db.close()
    return row["value"]
app.secret_key = _load_secret()

# ---------------------------------------------------------------- clinic SSO
# Step 4 (Session 158): accept a valid portal `clinic_sso` cookie as login,
# mapping the SSO role to a local asset user (doctor -> owner, manager ->
# manager). The app's own username/password login + auth-epoch stay as the
# permanent fallback. If the portal secret can't be read, the shim is INERT and
# the app behaves exactly as before -- so this cannot break existing access.
import sys as _sys, json as _json
_PORTAL_DIR = os.environ.get("CLINIC_PORTAL_DIR", "/root/portal")
try:
    if _PORTAL_DIR not in _sys.path:
        _sys.path.insert(0, _PORTAL_DIR)
    import clinic_sso as _sso
    import portal_config as _pcfg
    _SSO_SECRET = getattr(_pcfg, "CLINIC_SSO_SECRET", None)
except Exception:
    _sso = None
    _SSO_SECRET = None
_SSO_STORE = os.path.join(_PORTAL_DIR, "clinic_users.json")


def _sso_epoch():
    try:
        with open(_SSO_STORE) as f:
            return int(_json.load(f).get("epoch", 1))
    except Exception:
        return None


def _sso_user():
    """A valid portal clinic_sso cookie -> a local asset user row (or None).
    doctor -> an active 'owner' row; manager -> an active 'manager' row.
    Prefers a same-username local row when that row's role agrees."""
    if not _sso or not _SSO_SECRET:
        return None
    tok = request.cookies.get(_sso.COOKIE_NAME)
    if not tok:
        return None
    try:
        data = _sso.verify_token(tok, _SSO_SECRET, current_epoch=_sso_epoch())
    except Exception:
        data = None
    if not data:
        return None
    asset_role = "owner" if data.get("role") == "doctor" else "manager"
    db = get_db()
    row = None
    uname = (data.get("user") or "").strip().lower()
    if uname:
        row = db.execute("SELECT * FROM users WHERE lower(username)=? AND active=1",
                         (uname,)).fetchone()
        if row is not None and row["role"] != asset_role:
            row = None
    if row is None:
        row = db.execute("SELECT * FROM users WHERE role=? AND active=1 ORDER BY id LIMIT 1",
                         (asset_role,)).fetchone()
    return row

# ---------------------------------------------------------------- auth
def current_user():
    uid, epoch = session.get("uid"), session.get("epoch")
    if uid:
        if str(epoch) != setting("auth_epoch"):
            session.clear()
        else:
            u = get_db().execute("SELECT * FROM users WHERE id=? AND active=1", (uid,)).fetchone()
            if u:
                return u
    # no valid asset session -> accept a portal clinic_sso cookie (Step 4 SSO)
    return _sso_user()

def login_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u:
            return redirect(url_for("login", next=request.path))
        g.user = u
        return f(*a, **k)
    return w

def owner_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u:
            return redirect(url_for("login", next=request.path))
        if u["role"] != "owner":
            abort(403)
        g.user = u
        return f(*a, **k)
    return w

def is_owner():
    return g.user["role"] == "owner"

# ---------------------------------------------------------------- visibility
def visible_assets_where():
    """SQL fragment restricting assets for managers."""
    if is_owner():
        return "1=1", []
    return ("a.hidden=0 AND l.visibility='general'", [])

def asset_or_403(aid):
    a = get_db().execute(
        "SELECT a.*, l.name loc_name, l.visibility FROM assets a JOIN locations l ON l.id=a.location_id WHERE a.id=?",
        (aid,)).fetchone()
    if not a:
        abort(404)
    if not is_owner() and (a["hidden"] or a["visibility"] == "owner_only"):
        abort(403)
    return a

def can_see_price(a):
    return is_owner() or not a["hide_price"]

def draft_or_403(did):
    d = get_db().execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone()
    if not d:
        abort(404)
    # a draft has no location or hide_price yet, so it cannot be classified:
    # creator + owners only, deliberately conservative
    if not is_owner() and d["created_by"] != g.user["id"]:
        abort(403)
    return d

# ---------------------------------------------------------------- OCR adapter
def digitise_document(path, ext):
    """Return (text, status). v1.2.0 is a deliberate stub: the register must
    never depend on an external API being reachable. v1.2.1 replaces the body
    with the Sarvam Doc AI async job flow (create -> upload -> start -> poll ->
    download). Status is one of: done | failed | skipped."""
    if not SARVAM_API_KEY:
        return None, "skipped"
    if ext not in OCR_EXT:
        return None, "skipped"
    return None, "pending"   # v1.2.1 performs the call here

# ---------------------------------------------------------------- dates
def today():
    return datetime.date.today()

def due_state(due_str, threshold):
    try:
        d = datetime.date.fromisoformat(due_str)
    except Exception:
        return "", None
    delta = (d - today()).days
    if delta < 0:
        return "red", delta
    if delta <= threshold:
        return "amber", delta
    return "", delta

# ---------------------------------------------------------------- templates
BASE = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Asset Register</title><style>
body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f5f6f8;color:#222}
header{background:#1f3864;color:#fff;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap}
header a{color:#cfe0ff;text-decoration:none;margin-left:14px}
main{max-width:1080px;margin:16px auto;padding:0 12px}
table{border-collapse:collapse;width:100%;background:#fff}
th,td{border:1px solid #ddd;padding:6px 8px;font-size:14px;text-align:left}
th{background:#e8edf7}
.card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:14px;margin-bottom:14px}
.amber{background:#fce5cd}.red{background:#f4cccc}
.badge{padding:1px 7px;border-radius:9px;font-size:12px}
.badge.amber{background:#b45f06;color:#fff}.badge.red{background:#990000;color:#fff}
input,select,textarea{padding:6px;margin:3px 0;width:100%;max-width:420px;box-sizing:border-box}
label{font-size:13px;color:#555;display:block;margin-top:8px}
button,.btn{background:#1f3864;color:#fff;border:0;padding:8px 16px;border-radius:4px;cursor:pointer;text-decoration:none;display:inline-block;font-size:14px}
.btn.small{padding:3px 9px;font-size:12px}
.btn.danger{background:#990000}
.flash{background:#fff3cd;border:1px solid #ffec99;padding:8px 12px;margin-bottom:12px;border-radius:4px}
.muted{color:#888;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}
</style></head><body>
<header><div><b>🗂 Asset Register</b> <span class=muted style="color:#9fb3d9">v{{version}}</span></div>
<nav>{% if user %}<a href="{{url_for('dashboard')}}">Dashboard</a>
<a href="{{url_for('assets_list')}}">Assets</a>
<a href="{{url_for('drafts_list')}}">Drafts</a>
<a href="{{url_for('staff_list')}}">Staff</a>
{% if user['role']=='owner' %}<a href="{{url_for('admin')}}">Admin</a>{% endif %}
<a href="{{url_for('account')}}">{{user['display_name']}}</a>
<a href="{{url_for('logout')}}">Logout</a>{% endif %}</nav></header>
<main>{% with m=get_flashed_messages() %}{% for f in m %}<div class=flash>{{f}}</div>{% endfor %}{% endwith %}
{{body}}</main></body></html>"""

def page(body_tpl, **ctx):
    u = current_user()
    body = render_template_string(body_tpl, user=u, is_owner=(u and u["role"] == "owner"), **ctx)
    return render_template_string(BASE, user=u, body=Markup(body), version=APP_VERSION)

# ---------------------------------------------------------------- routes: auth
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = get_db().execute("SELECT * FROM users WHERE username=? AND active=1",
                             (request.form.get("username", "").strip().lower(),)).fetchone()
        if u and check_password_hash(u["password_hash"], request.form.get("password", "")):
            session.clear()
            session["uid"] = u["id"]
            session["epoch"] = setting("auth_epoch")
            session.permanent = True
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid credentials.")
    return page("""<div class=card style="max-width:380px;margin:40px auto"><h3>Sign in</h3>
<form method=post><label>Username</label><input name=username required>
<label>Password</label><input type=password name=password required>
<br><br><button>Sign in</button></form></div>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    db = get_db()
    if request.method == "POST":
        act = request.form.get("action")
        if act == "password":
            if not check_password_hash(g.user["password_hash"], request.form.get("current", "")):
                flash("Current password incorrect.")
            elif len(request.form.get("new", "")) < 8:
                flash("New password must be at least 8 characters.")
            else:
                db.execute("UPDATE users SET password_hash=? WHERE id=?",
                           (generate_password_hash(request.form["new"]), g.user["id"]))
                db.commit(); flash("Password changed.")
        elif act == "epoch" and is_owner():
            db.execute("UPDATE settings SET value=CAST(value AS INTEGER)+1 WHERE key='auth_epoch'")
            db.commit(); session.clear()
            return redirect(url_for("login"))
        return redirect(url_for("account"))
    return page("""<div class=card><h3>Account — {{user['display_name']}} ({{user['role']}})</h3>
<form method=post><input type=hidden name=action value=password>
<label>Current password</label><input type=password name=current required>
<label>New password (min 8)</label><input type=password name=new required>
<br><br><button>Change password</button></form></div>
{% if is_owner %}<div class=card><h4>Sign out everywhere</h4>
<p class=muted>Invalidates all sessions on all devices for all users (auth-epoch bump).</p>
<form method=post><input type=hidden name=action value=epoch>
<button class="btn danger">Sign out all devices</button></form></div>{% endif %}""")

# ---------------------------------------------------------------- dashboard
@app.route("/")
@login_required
def dashboard():
    db = get_db()
    where, params = visible_assets_where()
    rows = db.execute(f"""
      SELECT e.*, a.name entity_name, 'asset' AS kind FROM expiries e
        JOIN assets a ON e.entity='asset' AND a.id=e.entity_id
        JOIN locations l ON l.id=a.location_id
       WHERE e.resolved=0 AND {where}
      UNION ALL
      SELECT e.*, s.name entity_name, 'staff' AS kind FROM expiries e
        JOIN staff s ON e.entity='staff' AND s.id=e.entity_id
       WHERE e.resolved=0 AND (s.hidden=0 OR :owner=1)
      ORDER BY due_date""", dict(owner=1 if is_owner() else 0) if not params else params).fetchall() \
        if is_owner() else db.execute(f"""
      SELECT e.*, a.name entity_name, 'asset' AS kind FROM expiries e
        JOIN assets a ON e.entity='asset' AND a.id=e.entity_id
        JOIN locations l ON l.id=a.location_id
       WHERE e.resolved=0 AND {where}
      UNION ALL
      SELECT e.*, s.name entity_name, 'staff' AS kind FROM expiries e
        JOIN staff s ON e.entity='staff' AND s.id=e.entity_id
       WHERE e.resolved=0 AND s.hidden=0
      ORDER BY due_date""").fetchall()
    due = []
    for r in rows:
        state, days = due_state(r["due_date"], r["threshold_days"])
        if state:
            due.append((r, state, days))
    counts = db.execute(f"""SELECT COUNT(*) c FROM assets a JOIN locations l ON l.id=a.location_id
                            WHERE {where}""").fetchone()["c"]
    return page("""<h2>Dashboard</h2>
<div class=grid><div class=card><b>{{counts}}</b><br>assets visible to you</div>
<div class=card><b>{{due|length}}</b><br>items needing attention</div></div>
<div class=card><h3>Renewals & expiries due</h3>
{% if not due %}<p class=muted>Nothing amber or red. All clear.</p>{% else %}
<table><tr><th>Item</th><th>What</th><th>Due</th><th>Status</th></tr>
{% for r,state,days in due %}<tr class={{state}}>
<td>{% if r['kind']=='asset' %}<a href="{{url_for('asset_view',aid=r['entity_id'])}}">{{r['entity_name']}}</a>{% else %}{{r['entity_name']}} (staff){% endif %}</td>
<td>{{r['label']}}</td><td>{{r['due_date']}}</td>
<td><span class="badge {{state}}">{{'overdue' if days<0 else (days|string)+' days'}}</span></td>
</tr>{% endfor %}</table>{% endif %}</div>""", due=due, counts=counts)

# ---------------------------------------------------------------- assets
@app.route("/assets")
@login_required
def assets_list():
    """Grouped index (Phase C): Entity -> Zone -> assets, collapsible.
    Visibility gate + search unchanged; unclassified assets group last so they
    are never hidden."""
    where, params = visible_assets_where()
    q = request.args.get("q", "").strip()
    doc_sub = ("(SELECT COUNT(*) FROM attachments at WHERE at.entity='asset' "
               "AND at.entity_id=a.id AND at.document_text LIKE ?)")
    cols = ("a.*, l.name loc_name, en.name ent_name, en.sort ent_sort, "
            "zn.name zone_name, zn.sort zone_sort")
    joins = ("FROM assets a JOIN locations l ON l.id=a.location_id "
             "LEFT JOIN entities en ON en.id=a.entity_id LEFT JOIN zones zn ON zn.id=a.zone_id")
    if q:
        sql = f"SELECT {cols}, {doc_sub} doc_hit {joins} WHERE {where}"
        params = [f"%{q}%"] + params
        sql += (" AND (a.name LIKE ? OR a.vendor LIKE ? OR a.serial_no LIKE ?"
                " OR EXISTS(SELECT 1 FROM attachments at2 WHERE at2.entity='asset'"
                " AND at2.entity_id=a.id AND at2.document_text LIKE ?))")
        params += [f"%{q}%"] * 4
    else:
        sql = f"SELECT {cols}, 0 doc_hit {joins} WHERE {where}"
    sql += " ORDER BY a.name"
    rows = get_db().execute(sql, params).fetchall()

    # group entity -> zone, preserving admin sort order; NULLs (unclassified) last
    groups = {}
    for a in rows:
        en = a["ent_name"] or "Unclassified"
        es = a["ent_sort"] if a["ent_sort"] is not None else 9999
        zn = a["zone_name"] or "\u2014"
        zs = a["zone_sort"] if a["zone_sort"] is not None else 9999
        g = groups.setdefault(en, {"sort": es, "zones": {}, "count": 0})
        g["count"] += 1
        z = g["zones"].setdefault(zn, {"sort": zs, "rows": []})
        z["rows"].append(a)
    ordered = []
    for en, g in sorted(groups.items(), key=lambda kv: (kv[1]["sort"], kv[0])):
        zones = [(zn, z["rows"]) for zn, z in
                 sorted(g["zones"].items(), key=lambda kv: (kv[1]["sort"], kv[0]))]
        ordered.append((en, g["count"], zones))

    return page("""<h2>Assets</h2>
<form method=get style="margin-bottom:10px"><input name=q value="{{q}}" placeholder="search name / vendor / serial / document text" style="max-width:320px"> <button class="btn small">Search</button></form>
<p><a class=btn href="{{url_for('asset_edit')}}">+ Add asset</a>
<a class="btn small" href="{{url_for('drafts_list')}}">\U0001F4F7 Scan first (Drafts)</a></p>
{% if q %}<p class=muted>Matches for \u201c{{q}}\u201d \u00b7 <a href="{{url_for('assets_list')}}">clear</a></p>{% endif %}
{% for ent_name, ent_count, zones in ordered %}
<details open><summary style="font-size:16px;font-weight:bold;cursor:pointer;padding:8px 0;color:#1f3864">{{ent_name}} <span class=muted>({{ent_count}})</span></summary>
{% for zone_name, zrows in zones %}
<details open style="margin:0 0 8px 12px"><summary style="cursor:pointer;padding:4px 0;font-weight:bold">{{zone_name}} <span class=muted>({{zrows|length}})</span></summary>
<table style="margin:4px 0 6px"><tr><th>Name</th><th>Category</th><th>Status</th><th>Contract</th></tr>
{% for a in zrows %}<tr><td><a href="{{url_for('asset_view',aid=a['id'])}}">{{a['name']}}</a>{% if a['hidden'] %} <span class=muted>(hidden)</span>{% endif %}{% if a['doc_hit'] %}<br><span class=muted>\u21b3 matched in attached document</span>{% endif %}</td>
<td>{{a['category']}}</td><td>{{a['status']}}</td><td>{{a['contract_type']}}</td></tr>
{% endfor %}</table>
</details>
{% endfor %}
</details>
{% endfor %}
{% if not ordered %}<p class=muted>No assets{{' match your search' if q else ''}}.</p>{% endif %}""",
        ordered=ordered, q=q)

def locations_for_user():
    if is_owner():
        return get_db().execute("SELECT * FROM locations ORDER BY id").fetchall()
    return get_db().execute("SELECT * FROM locations WHERE visibility='general' ORDER BY id").fetchall()

@app.route("/assets/new", methods=["GET", "POST"])
@app.route("/assets/<int:aid>/edit", methods=["GET", "POST"])
@login_required
def asset_edit(aid=None):
    db = get_db()
    a = asset_or_403(aid) if aid else None
    if request.method == "POST":
        f = request.form
        loc = db.execute("SELECT * FROM locations WHERE id=?", (f.get("location_id"),)).fetchone()
        if not loc or (not is_owner() and loc["visibility"] != "general"):
            abort(403)
        vals = dict(
            name=f.get("name", "").strip(), location_id=loc["id"],
            category=f.get("category") if f.get("category") in CATEGORIES else "Other",
            purchase_date=f.get("purchase_date") or None,
            price=float(f["price"]) if f.get("price") else None,
            vendor=f.get("vendor") or None, vendor_phone=f.get("vendor_phone") or None,
            serial_no=f.get("serial_no") or None,
            status=f.get("status") if f.get("status") in STATUSES else "Active",
            contract_type=f.get("contract_type") if f.get("contract_type") in CONTRACT_TYPES else "None",
            provider=f.get("provider") or None,
            contract_cost=float(f["contract_cost"]) if f.get("contract_cost") else None,
            notes=f.get("notes") or None)
        if is_owner():
            vals["hidden"] = 1 if f.get("hidden") else 0
            vals["hide_price"] = 1 if f.get("hide_price") else 0
        elif a and a["hide_price"]:
            # price fields are absent from the manager's form on hide_price assets;
            # preserve stored values instead of overwriting with NULL
            vals["price"] = a["price"]
            vals["contract_cost"] = a["contract_cost"]
        if not vals["name"]:
            flash("Name is required.")
        else:
            if a:
                sets = ",".join(f"{k}=:{k}" for k in vals)
                db.execute(f"UPDATE assets SET {sets} WHERE id=:id", {**vals, "id": a["id"]})
                new_id = a["id"]
            else:
                vals["created_by"] = g.user["id"]
                cols = ",".join(vals); ph = ",".join(":" + k for k in vals)
                cur = db.execute(f"INSERT INTO assets({cols}) VALUES({ph})", vals)
                new_id = cur.lastrowid
            # expiries: warranty + contract renewal, replacing prior unresolved ones of same label
            for label, key in [("Warranty", "warranty_till"), ("Contract renewal", "renewal_date")]:
                db.execute("DELETE FROM expiries WHERE entity='asset' AND entity_id=? AND label=? AND resolved=0",
                           (new_id, label))
                if f.get(key):
                    thr = int(f.get("threshold_days") or THRESHOLD_DEFAULT)
                    db.execute("INSERT INTO expiries(entity,entity_id,label,due_date,threshold_days) VALUES('asset',?,?,?,?)",
                               (new_id, label, f[key], thr))
            # scan-first: promote the staged draft into a real attachment
            did = f.get("draft_id", type=int)
            if did:
                d = draft_or_403(did)
                ext = d["orig_name"].rsplit(".", 1)[-1].lower() if "." in d["orig_name"] else ""
                sens = 1 if vals.get("hide_price", a["hide_price"] if a else 0) else 0
                _, st = digitise_document(os.path.join(UPLOAD_DIR, d["stored_name"]), ext)
                db.execute("""INSERT INTO attachments(entity,entity_id,stored_name,orig_name,
                              sensitive,ocr_status,uploaded_by) VALUES('asset',?,?,?,?,?,?)""",
                           (new_id, d["stored_name"], d["orig_name"], sens, st, d["created_by"]))
                db.execute("DELETE FROM drafts WHERE id=?", (did,))
            db.commit()
            return redirect(url_for("asset_view", aid=new_id))
    exp = {}
    if a:
        for e in db.execute("SELECT * FROM expiries WHERE entity='asset' AND entity_id=? AND resolved=0", (a["id"],)):
            exp[e["label"]] = e
    draft = None
    if not a and request.args.get("draft", type=int):
        draft = draft_or_403(request.args.get("draft", type=int))
    return page("""<h2>{{'Edit' if a else 'New'}} asset</h2>
{% if draft %}<div class=card style="background:#eef5ff">📄 <b>{{draft['orig_name']}}</b>
<a class="btn small" href="{{url_for('draft_preview',did=draft['id'])}}" target=_blank>Open document</a>
<div class=muted>This document attaches to the asset when you save.</div></div>{% endif %}
<div class=card><form method=post>
{% if draft %}<input type=hidden name=draft_id value={{draft['id']}}>{% endif %}
<label>Name*</label><input name=name value="{{a['name'] if a else ''}}" required>
<label>Location</label><select name=location_id>{% for l in locs %}
<option value={{l['id']}} {{'selected' if a and a['location_id']==l['id']}}>{{l['name']}}{{' 🔒' if l['visibility']=='owner_only'}}</option>{% endfor %}</select>
<label>Category</label><select name=category>{% for c in cats %}<option {{'selected' if a and a['category']==c}}>{{c}}</option>{% endfor %}</select>
<label>Purchase date</label><input type=date name=purchase_date value="{{a['purchase_date'] or '' if a else ''}}">
{% if not a or can_price %}<label>Purchase price (₹)</label><input type=number step=0.01 name=price value="{{a['price'] or '' if a else ''}}">{% endif %}
<label>Vendor</label><input name=vendor value="{{a['vendor'] or '' if a else ''}}">
<label>Vendor phone</label><input name=vendor_phone value="{{a['vendor_phone'] or '' if a else ''}}">
<label>Serial / model no.</label><input name=serial_no value="{{a['serial_no'] or '' if a else ''}}">
<label>Status</label><select name=status>{% for s in sts %}<option {{'selected' if a and a['status']==s}}>{{s}}</option>{% endfor %}</select>
<label>Warranty till</label><input type=date name=warranty_till value="{{exp['Warranty']['due_date'] if 'Warranty' in exp else ''}}">
<label>Contract type</label><select name=contract_type>{% for c in cts %}<option {{'selected' if a and a['contract_type']==c}}>{{c}}</option>{% endfor %}</select>
<label>AMC/CMC provider</label><input name=provider value="{{a['provider'] or '' if a else ''}}">
{% if not a or can_price %}<label>Contract cost (₹/yr)</label><input type=number step=0.01 name=contract_cost value="{{a['contract_cost'] or '' if a else ''}}">{% endif %}
<label>Contract renewal date</label><input type=date name=renewal_date value="{{exp['Contract renewal']['due_date'] if 'Contract renewal' in exp else ''}}">
<label>Reminder threshold (days before due; default 60)</label><input type=number name=threshold_days value="{{thr}}">
<label>Notes</label><textarea name=notes rows=3>{{a['notes'] or '' if a else ''}}</textarea>
{% if is_owner %}<label><input type=checkbox name=hidden style="width:auto" {{'checked' if a and a['hidden']}}> Hide entire asset from manager</label>
<label><input type=checkbox name=hide_price style="width:auto" {{'checked' if a and a['hide_price']}}> Hide price & invoices from manager</label>{% endif %}
<br><button>Save</button></form></div>""",
        a=a, locs=locations_for_user(), cats=CATEGORIES, sts=STATUSES, cts=CONTRACT_TYPES,
        exp=exp, can_price=(a is None or can_see_price(a)), draft=draft,
        thr=(next(iter(exp.values()))["threshold_days"] if exp else THRESHOLD_DEFAULT))

@app.route("/assets/<int:aid>")
@login_required
def asset_view(aid):
    db = get_db()
    a = asset_or_403(aid)
    show_price = can_see_price(a)
    exp = db.execute("SELECT * FROM expiries WHERE entity='asset' AND entity_id=? AND resolved=0 ORDER BY due_date",
                     (aid,)).fetchall()
    exp = [(e, *due_state(e["due_date"], e["threshold_days"])) for e in exp]
    logs = db.execute("""SELECT sl.*, u.display_name entered_by FROM service_logs sl
                         LEFT JOIN users u ON u.id=sl.created_by
                         WHERE asset_id=? ORDER BY log_date DESC""", (aid,)).fetchall()
    att_sql = "SELECT at.*, u.display_name up_by FROM attachments at LEFT JOIN users u ON u.id=at.uploaded_by WHERE entity='asset' AND entity_id=?"
    if not show_price:
        att_sql += " AND sensitive=0"
    atts = db.execute(att_sql, (aid,)).fetchall()
    return page("""<h2>{{a['name']}}</h2>
<p><a class="btn small" href="{{url_for('asset_edit',aid=a['id'])}}">Edit</a>
{% if is_owner %}<form method=post action="{{url_for('asset_delete',aid=a['id'])}}" style="display:inline" onsubmit="return confirm('Delete asset and all its logs/files?')"><button class="btn small danger">Delete</button></form>{% endif %}</p>
<div class=grid>
<div class=card><b>Location:</b> {{a['loc_name']}}<br><b>Category:</b> {{a['category']}}<br>
<b>Status:</b> {{a['status']}}<br><b>Serial:</b> {{a['serial_no'] or '—'}}<br>
<b>Purchased:</b> {{a['purchase_date'] or '—'}}
{% if show_price %}<br><b>Price:</b> ₹{{'%.0f'|format(a['price']) if a['price'] else '—'}}{% endif %}</div>
<div class=card><b>Vendor:</b> {{a['vendor'] or '—'}} {{a['vendor_phone'] or ''}}<br>
<b>Contract:</b> {{a['contract_type']}}{% if a['provider'] %} — {{a['provider']}}{% endif %}
{% if show_price and a['contract_cost'] %}<br><b>Contract cost:</b> ₹{{'%.0f'|format(a['contract_cost'])}}/yr{% endif %}</div></div>
{% if a['notes'] %}<div class=card>{{a['notes']}}</div>{% endif %}
<div class=card><h4>Dates to watch</h4>{% if not exp %}<span class=muted>none set</span>{% endif %}
{% for e,state,days in exp %}<div>{{e['label']}}: <b>{{e['due_date']}}</b>
{% if state %}<span class="badge {{state}}">{{'overdue' if days<0 else (days|string)+'d'}}</span>{% endif %}</div>{% endfor %}</div>
<div class=card><h4>Files</h4>
<p><a class="btn small" href="{{url_for('scan_page',entity='asset',eid=a['id'])}}">📷 Scan document</a></p>
{% for f in atts %}<div style="margin-bottom:6px">📄 <a href="{{url_for('file_get',fid=f['id'])}}">{{f['orig_name']}}</a>
{% if f['sensitive'] %}<span class=muted>(price-sensitive)</span>{% endif %}
<span class=muted>by {{f['up_by']}} {{f['uploaded_at'][:10]}}
· text: {{f['ocr_status']}}</span>
{% if is_owner %}
<form method=post action="{{url_for('file_delete',fid=f['id'])}}" style="display:inline"
 onsubmit="return confirm('Delete this document permanently?')"><button class="btn small danger">Delete</button></form>
<form method=post enctype=multipart/form-data action="{{url_for('file_replace',fid=f['id'])}}" style="display:inline">
<input type=file name=file required style="max-width:170px;display:inline">
<button class="btn small">Replace</button></form>{% endif %}
</div>{% endfor %}
<form method=post enctype=multipart/form-data action="{{url_for('file_upload')}}">
<input type=hidden name=entity value=asset><input type=hidden name=entity_id value={{a['id']}}>
<input type=file name=file accept="image/*,.pdf,.doc,.docx" required style="max-width:260px">
<label><input type=checkbox name=sensitive style="width:auto" {{'checked' if a['hide_price']}}> price-sensitive (hidden with price)</label>
<button class="btn small">Upload</button></form></div>
<div class=card><h4>Service log</h4>
<table><tr><th>Date</th><th>Work</th>{% if show_price %}<th>Cost</th>{% endif %}<th>By</th><th>Next due</th><th>Entered</th></tr>
{% for s in logs %}<tr><td>{{s['log_date']}}</td><td>{{s['work']}}</td>
{% if show_price %}<td>{{'₹%.0f'|format(s['cost']) if s['cost'] else ''}}</td>{% endif %}
<td>{{s['done_by'] or ''}}</td><td>{{s['next_due'] or ''}}</td><td class=muted>{{s['entered_by']}}</td></tr>{% endfor %}</table>
<form method=post action="{{url_for('service_add',aid=a['id'])}}">
<label>Date</label><input type=date name=log_date value="{{today}}" required>
<label>Work done / issue</label><input name=work required>
<label>Cost (₹)</label><input type=number step=0.01 name=cost>
<label>Done by</label><input name=done_by>
<label>Next service due</label><input type=date name=next_due>
<br><button class="btn small">Add entry</button></form></div>""",
        a=a, exp=exp, logs=logs, atts=atts, show_price=show_price, today=today().isoformat())

@app.route("/assets/<int:aid>/delete", methods=["POST"])
@owner_required
def asset_delete(aid):
    db = get_db()
    asset_or_403(aid)
    for f in db.execute("SELECT stored_name FROM attachments WHERE entity='asset' AND entity_id=?", (aid,)):
        try: os.remove(os.path.join(UPLOAD_DIR, f["stored_name"]))
        except OSError: pass
    db.execute("DELETE FROM attachments WHERE entity='asset' AND entity_id=?", (aid,))
    db.execute("DELETE FROM expiries WHERE entity='asset' AND entity_id=?", (aid,))
    db.execute("DELETE FROM service_logs WHERE asset_id=?", (aid,))
    db.execute("DELETE FROM assets WHERE id=?", (aid,))
    db.commit(); flash("Asset deleted.")
    return redirect(url_for("assets_list"))

@app.route("/assets/<int:aid>/service", methods=["POST"])
@login_required
def service_add(aid):
    a = asset_or_403(aid)
    f = request.form
    get_db().execute("""INSERT INTO service_logs(asset_id,log_date,work,cost,done_by,next_due,created_by)
                        VALUES(?,?,?,?,?,?,?)""",
                     (aid, f.get("log_date") or today().isoformat(), f.get("work", "").strip(),
                      float(f["cost"]) if f.get("cost") else None,
                      f.get("done_by") or None, f.get("next_due") or None, g.user["id"]))
    get_db().commit()
    return redirect(url_for("asset_view", aid=aid))

# ---------------------------------------------------------------- files
@app.route("/files/upload", methods=["POST"])
@login_required
def file_upload():
    entity, eid = request.form.get("entity"), request.form.get("entity_id", type=int)
    if entity == "asset":
        a = asset_or_403(eid)
        sensitive = 1 if (request.form.get("sensitive") or a["hide_price"]) else 0
        back = url_for("asset_view", aid=eid)
    elif entity == "staff":
        staff_or_403(eid); sensitive = 1 if request.form.get("sensitive") else 0
        back = url_for("staff_view", sid=eid)
    elif entity == "draft":
        eid = 0; sensitive = 0
        back = url_for("drafts_list")
    else:
        abort(400)
    fobj = request.files.get("file")
    if not fobj or "." not in fobj.filename:
        flash("No file."); return redirect(back)
    ext = fobj.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        flash("File type not allowed."); return redirect(back)
    stored = f"{entity}{eid}_{secrets.token_hex(8)}.{ext}"
    fobj.save(os.path.join(UPLOAD_DIR, stored))
    db = get_db()
    if entity == "draft":
        db.execute("INSERT INTO drafts(stored_name,orig_name,note,created_by) VALUES(?,?,?,?)",
                   (stored, secure_filename(fobj.filename),
                    (request.form.get("note") or "").strip() or None, g.user["id"]))
    else:
        _, st = digitise_document(os.path.join(UPLOAD_DIR, stored), ext)
        db.execute("""INSERT INTO attachments(entity,entity_id,stored_name,orig_name,
                      sensitive,ocr_status,uploaded_by) VALUES(?,?,?,?,?,?,?)""",
                   (entity, eid, stored, secure_filename(fobj.filename), sensitive, st, g.user["id"]))
    db.commit()
    return redirect(back)

@app.route("/files/<int:fid>")
@login_required
def file_get(fid):
    f = get_db().execute("SELECT * FROM attachments WHERE id=?", (fid,)).fetchone()
    if not f:
        abort(404)
    if f["entity"] == "asset":
        a = asset_or_403(f["entity_id"])          # visibility gate
        if f["sensitive"] and not can_see_price(a):  # price gate extends to files
            abort(403)
    elif f["entity"] == "staff":
        staff_or_403(f["entity_id"])
        if f["sensitive"] and not is_owner():
            abort(403)
    path = os.path.join(UPLOAD_DIR, f["stored_name"])
    if not os.path.exists(path):
        abort(404)
    return send_file(path, download_name=f["orig_name"],
                     mimetype=mimetypes.guess_type(f["orig_name"])[0] or "application/octet-stream")

def _file_back(f):
    return (url_for("asset_view", aid=f["entity_id"]) if f["entity"] == "asset"
            else url_for("staff_view", sid=f["entity_id"]))

def _drop_file(db, f):
    try: os.remove(os.path.join(UPLOAD_DIR, f["stored_name"]))
    except OSError: pass
    db.execute("DELETE FROM attachments WHERE id=?", (f["id"],))

@app.route("/files/<int:fid>/delete", methods=["POST"])
@owner_required
def file_delete(fid):
    db = get_db()
    f = db.execute("SELECT * FROM attachments WHERE id=?", (fid,)).fetchone()
    if not f:
        abort(404)
    back = _file_back(f)
    _drop_file(db, f); db.commit()
    flash("Document deleted."); return redirect(back)

@app.route("/files/<int:fid>/replace", methods=["POST"])
@owner_required
def file_replace(fid):
    db = get_db()
    old = db.execute("SELECT * FROM attachments WHERE id=?", (fid,)).fetchone()
    if not old:
        abort(404)
    back = _file_back(old)
    fobj = request.files.get("file")
    if not fobj or "." not in fobj.filename:
        flash("No replacement file."); return redirect(back)
    ext = fobj.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        flash("File type not allowed."); return redirect(back)
    # sensitivity is RE-DERIVED from the record's CURRENT state, never inherited
    if old["entity"] == "asset":
        a = db.execute("SELECT hide_price FROM assets WHERE id=?", (old["entity_id"],)).fetchone()
        sens = 1 if (a and a["hide_price"]) else 0
    else:
        sens = old["sensitive"]
    stored = f"{old['entity']}{old['entity_id']}_{secrets.token_hex(8)}.{ext}"
    fobj.save(os.path.join(UPLOAD_DIR, stored))
    _, st = digitise_document(os.path.join(UPLOAD_DIR, stored), ext)
    _drop_file(db, old)          # old file destroyed — no superseded copy kept
    db.execute("""INSERT INTO attachments(entity,entity_id,stored_name,orig_name,
                  sensitive,ocr_status,uploaded_by) VALUES(?,?,?,?,?,?,?)""",
               (old["entity"], old["entity_id"], stored, secure_filename(fobj.filename),
                sens, st, g.user["id"]))
    db.commit()
    flash("Document replaced."); return redirect(back)

# ---------------------------------------------------------------- drafts (scan-first)
@app.route("/drafts")
@login_required
def drafts_list():
    db = get_db()
    if is_owner():
        rows = db.execute("""SELECT d.*, u.display_name by_name FROM drafts d
                             LEFT JOIN users u ON u.id=d.created_by ORDER BY d.created_at DESC""").fetchall()
    else:
        rows = db.execute("""SELECT d.*, u.display_name by_name FROM drafts d
                             LEFT JOIN users u ON u.id=d.created_by
                             WHERE d.created_by=? ORDER BY d.created_at DESC""", (g.user["id"],)).fetchall()
    return page("""<h2>📷 Drafts — scanned, not yet filed</h2>
<p class=muted>Scan or upload the bill first, then fill in the asset when you have time.
Drafts do not expire. They are visible only to whoever created them, plus the owners.</p>
<div class=card><h4>Add a document</h4>
<p><a class="btn small" href="{{url_for('scan_page',entity='draft',eid=0)}}">📷 Scan with camera</a></p>
<form method=post enctype=multipart/form-data action="{{url_for('file_upload')}}">
<input type=hidden name=entity value=draft><input type=hidden name=entity_id value=0>
<input type=file name=file accept="image/*,.pdf,.doc,.docx" required style="max-width:260px">
<input name=note placeholder="note (optional) e.g. Fuji AMC bill" style="max-width:260px">
<button class="btn small">Upload to drafts</button></form></div>
<table><tr><th>Document</th><th>Note</th><th>Added</th><th>By</th><th></th></tr>
{% for d in rows %}<tr>
<td>📄 <a href="{{url_for('draft_preview',did=d['id'])}}" target=_blank>{{d['orig_name']}}</a></td>
<td>{{d['note'] or ''}}</td><td>{{d['created_at'][:10]}}</td><td class=muted>{{d['by_name']}}</td>
<td><a class="btn small" href="{{url_for('asset_edit')}}?draft={{d['id']}}">Create asset →</a>
<form method=post action="{{url_for('draft_delete',did=d['id'])}}" style="display:inline"
 onsubmit="return confirm('Discard this scanned document?')"><button class="btn small danger">Discard</button></form></td>
</tr>{% endfor %}</table>
{% if not rows %}<p class=muted>No drafts waiting.</p>{% endif %}""", rows=rows)

@app.route("/drafts/<int:did>/preview")
@login_required
def draft_preview(did):
    d = draft_or_403(did)
    path = os.path.join(UPLOAD_DIR, d["stored_name"])
    if not os.path.exists(path):
        abort(404)
    return send_file(path, download_name=d["orig_name"],
                     mimetype=mimetypes.guess_type(d["orig_name"])[0] or "application/octet-stream")

@app.route("/drafts/<int:did>/delete", methods=["POST"])
@login_required
def draft_delete(did):
    d = draft_or_403(did)
    try: os.remove(os.path.join(UPLOAD_DIR, d["stored_name"]))
    except OSError: pass
    get_db().execute("DELETE FROM drafts WHERE id=?", (did,))
    get_db().commit()
    flash("Draft discarded."); return redirect(url_for("drafts_list"))

# ---------------------------------------------------------------- staff module
def staff_or_403(sid):
    s = get_db().execute("SELECT * FROM staff WHERE id=?", (sid,)).fetchone()
    if not s:
        abort(404)
    if not is_owner() and s["hidden"]:
        abort(403)
    return s

@app.route("/staff")
@login_required
def staff_list():
    if is_owner():
        rows = get_db().execute("SELECT * FROM staff ORDER BY name").fetchall()
    else:
        rows = get_db().execute("SELECT * FROM staff WHERE hidden=0 ORDER BY name").fetchall()
    return page("""<h2>Staff records</h2><p><a class=btn href="{{url_for('staff_edit')}}">+ Add staff</a></p>
<table><tr><th>Name</th><th>Role</th><th>Phone</th><th>Joined</th><th>Status</th></tr>
{% for s in rows %}<tr><td><a href="{{url_for('staff_view',sid=s['id'])}}">{{s['name']}}</a></td>
<td>{{s['role_title'] or ''}}</td><td>{{s['phone'] or ''}}</td><td>{{s['joined_date'] or ''}}</td><td>{{s['status']}}</td></tr>{% endfor %}</table>""", rows=rows)

@app.route("/staff/new", methods=["GET", "POST"])
@app.route("/staff/<int:sid>/edit", methods=["GET", "POST"])
@login_required
def staff_edit(sid=None):
    db = get_db()
    s = staff_or_403(sid) if sid else None
    if request.method == "POST":
        f = request.form
        vals = dict(name=f.get("name", "").strip(), role_title=f.get("role_title") or None,
                    phone=f.get("phone") or None, joined_date=f.get("joined_date") or None,
                    status=f.get("status") or "Active", notes=f.get("notes") or None)
        if is_owner():
            vals["hidden"] = 1 if f.get("hidden") else 0
        if not vals["name"]:
            flash("Name required.")
        else:
            if s:
                sets = ",".join(f"{k}=:{k}" for k in vals)
                db.execute(f"UPDATE staff SET {sets} WHERE id=:id", {**vals, "id": s["id"]})
                sid_new = s["id"]
            else:
                vals["created_by"] = g.user["id"]
                cols = ",".join(vals); ph = ",".join(":" + k for k in vals)
                sid_new = db.execute(f"INSERT INTO staff({cols}) VALUES({ph})", vals).lastrowid
            db.execute("DELETE FROM expiries WHERE entity='staff' AND entity_id=? AND resolved=0", (sid_new,))
            if f.get("doc_label") and f.get("doc_due"):
                db.execute("INSERT INTO expiries(entity,entity_id,label,due_date,threshold_days) VALUES('staff',?,?,?,?)",
                           (sid_new, f["doc_label"], f["doc_due"], int(f.get("threshold_days") or THRESHOLD_DEFAULT)))
            db.commit()
            return redirect(url_for("staff_view", sid=sid_new))
    return page("""<h2>{{'Edit' if s else 'New'}} staff record</h2><div class=card><form method=post>
<label>Name*</label><input name=name value="{{s['name'] if s else ''}}" required>
<label>Role / designation</label><input name=role_title value="{{s['role_title'] or '' if s else ''}}">
<label>Phone</label><input name=phone value="{{s['phone'] or '' if s else ''}}">
<label>Joined</label><input type=date name=joined_date value="{{s['joined_date'] or '' if s else ''}}">
<label>Status</label><select name=status><option>Active</option><option {{'selected' if s and s['status']=='Left'}}>Left</option></select>
<label>Notes</label><textarea name=notes rows=3>{{s['notes'] or '' if s else ''}}</textarea>
<label>Tracked expiry — label (e.g. Contract renewal)</label><input name=doc_label>
<label>Tracked expiry — date</label><input type=date name=doc_due>
{% if is_owner %}<label><input type=checkbox name=hidden style="width:auto" {{'checked' if s and s['hidden']}}> Hide from manager</label>{% endif %}
<br><button>Save</button></form></div>""", s=s)

@app.route("/staff/<int:sid>")
@login_required
def staff_view(sid):
    s = staff_or_403(sid)
    db = get_db()
    exp = [(e, *due_state(e["due_date"], e["threshold_days"])) for e in
           db.execute("SELECT * FROM expiries WHERE entity='staff' AND entity_id=? AND resolved=0", (sid,))]
    att_sql = "SELECT at.*,u.display_name up_by FROM attachments at LEFT JOIN users u ON u.id=at.uploaded_by WHERE entity='staff' AND entity_id=?"
    if not is_owner():
        att_sql += " AND sensitive=0"
    atts = db.execute(att_sql, (sid,)).fetchall()
    return page("""<h2>{{s['name']}} <span class=muted>{{s['role_title'] or ''}}</span></h2>
<p><a class="btn small" href="{{url_for('staff_edit',sid=s['id'])}}">Edit</a></p>
<div class=card><b>Phone:</b> {{s['phone'] or '—'}}<br><b>Joined:</b> {{s['joined_date'] or '—'}}<br>
<b>Status:</b> {{s['status']}}{% if s['notes'] %}<br>{{s['notes']}}{% endif %}</div>
<div class=card><h4>Dates to watch</h4>{% if not exp %}<span class=muted>none</span>{% endif %}
{% for e,state,days in exp %}<div>{{e['label']}}: <b>{{e['due_date']}}</b>
{% if state %}<span class="badge {{state}}">{{'overdue' if days<0 else (days|string)+'d'}}</span>{% endif %}</div>{% endfor %}</div>
<div class=card><h4>Documents</h4>
<p><a class="btn small" href="{{url_for('scan_page',entity='staff',eid=s['id'])}}">📷 Scan document</a></p>
{% for f in atts %}<div style="margin-bottom:6px">📄 <a href="{{url_for('file_get',fid=f['id'])}}">{{f['orig_name']}}</a>
{% if f['sensitive'] %}<span class=muted>(owner-only)</span>{% endif %}
<span class=muted>text: {{f['ocr_status']}}</span>
{% if is_owner %}
<form method=post action="{{url_for('file_delete',fid=f['id'])}}" style="display:inline"
 onsubmit="return confirm('Delete this document permanently?')"><button class="btn small danger">Delete</button></form>
<form method=post enctype=multipart/form-data action="{{url_for('file_replace',fid=f['id'])}}" style="display:inline">
<input type=file name=file required style="max-width:170px;display:inline">
<button class="btn small">Replace</button></form>{% endif %}
</div>{% endfor %}
<form method=post enctype=multipart/form-data action="{{url_for('file_upload')}}">
<input type=hidden name=entity value=staff><input type=hidden name=entity_id value={{s['id']}}>
<input type=file name=file accept="image/*,.pdf,.doc,.docx" required style="max-width:260px">
{% if is_owner %}<label><input type=checkbox name=sensitive style="width:auto"> owner-only document</label>{% endif %}
<button class="btn small">Upload</button></form></div>""", s=s, exp=exp, atts=atts)

# ---------------------------------------------------------------- built-in scanner
SCAN_TPL = """<script>window.SCANNER_CONFIG = {{ config|tojson }};</script>
<div id=scanroot></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="{{ widget_url }}"></script>
<noscript><p class=card>This scanner needs JavaScript enabled.</p></noscript>"""

def _widget_version():
    try:
        return int(os.path.getmtime(SCANNER_JS_PATH))
    except OSError:
        return 0

@app.route("/scan/widget.js")
def scanner_widget_js():
    """Serve the shared scanner widget from disk (edit-and-drop, cache-busted by ?v=mtime)."""
    if not os.path.exists(SCANNER_JS_PATH):
        abort(404)
    resp = send_file(SCANNER_JS_PATH, mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-cache"
    return resp

def _name_stem(s, fallback):
    """ASCII-safe filename stem mirroring secure_filename, so the default shown
    to the user matches what the server will store."""
    out = []
    for ch in (s or "").strip():
        if (ch.isalnum() and ord(ch) < 128) or ch in "._-":
            out.append(ch)
        else:
            out.append("_")
    r = "".join(out).strip("._-")
    while "__" in r:
        r = r.replace("__", "_")
    return r or fallback

def _scan_config(entity, eid, ename, back, sensitive_default, name_base):
    fields = {"entity": entity, "entity_id": str(eid)}
    if sensitive_default:
        fields["sensitive"] = "1"
    return {
        "title": "Scan \u2192 " + ename,
        "uploadUrl": url_for("file_upload"),
        "fileField": "file",
        "uploadFields": fields,
        "nameBase": name_base,
        "backUrl": back,
        "allowIdCard": True,
        "allowBatch": True,
    }

@app.route("/scan/<entity>/<int:eid>")
@login_required
def scan_page(entity, eid):
    widget_url = url_for("scanner_widget_js") + "?v=" + str(_widget_version())
    if entity == "asset":
        a = asset_or_403(eid)
        cfg = _scan_config("asset", eid, a["name"], url_for("asset_view", aid=eid),
                           bool(a["hide_price"]), _name_stem(a["name"], "asset"))
        return page(SCAN_TPL, config=cfg, widget_url=widget_url)
    if entity == "staff":
        s = staff_or_403(eid)
        cfg = _scan_config("staff", eid, s["name"], url_for("staff_view", sid=eid),
                           False, _name_stem(s["name"], "staff"))
        return page(SCAN_TPL, config=cfg, widget_url=widget_url)
    if entity == "draft":
        cfg = _scan_config("draft", 0, "Drafts", url_for("drafts_list"), False, "Draft")
        return page(SCAN_TPL, config=cfg, widget_url=widget_url)
    abort(404)

# ---------------------------------------------------------------- admin (owner)
@app.route("/admin", methods=["GET", "POST"])
@owner_required
def admin():
    db = get_db()
    if request.method == "POST":
        act = request.form.get("action")
        if act == "add_location" and request.form.get("name", "").strip():
            db.execute("INSERT OR IGNORE INTO locations(name,visibility) VALUES(?,?)",
                       (request.form["name"].strip(),
                        "owner_only" if request.form.get("owner_only") else "general"))
        elif act == "reset_pw":
            uid = request.form.get("uid", type=int)
            urow = db.execute("SELECT username FROM users WHERE id=?", (uid,)).fetchone()
            if request.form.get("gen"):
                new = secrets.token_urlsafe(9)          # strong, readable, ~12 chars
            else:
                new = request.form.get("new", "")
            if urow and len(new) >= 8:
                db.execute("UPDATE users SET password_hash=? WHERE id=?",
                           (generate_password_hash(new), uid))
                # passwords are stored ONE-WAY (hash); we reveal the value ONCE here
                # so you always know what you just set. It cannot be retrieved later.
                flash("Password for %s is now:  %s   \u2014 shown once, copy it now."
                      % (urow["username"], new))
            else:
                flash("Min 8 characters (or tick \u2018generate\u2019).")
        elif act == "rotate_token":
            db.execute("UPDATE settings SET value=? WHERE key='api_token'",
                       (secrets.token_urlsafe(24),))
            flash("API token rotated \u2014 update the WhatsApp cron with the new token.")
        db.commit()
        return redirect(url_for("admin"))
    users = db.execute("SELECT id,username,display_name,role FROM users").fetchall()
    locs = db.execute("SELECT * FROM locations").fetchall()
    return page("""<h2>Admin</h2>
<div class=card><h4>Locations</h4>
{% for l in locs %}<div>{{l['name']}} <span class=muted>{{l['visibility']}}</span></div>{% endfor %}
<form method=post><input type=hidden name=action value=add_location>
<input name=name placeholder="new location" style="max-width:220px">
<label><input type=checkbox name=owner_only style="width:auto"> owner-only</label>
<button class="btn small">Add</button></form></div>
<div class=card><h4>Users</h4>
{% for u in users %}<form method=post style="margin-bottom:6px">
<input type=hidden name=action value=reset_pw><input type=hidden name=uid value={{u['id']}}>
<b>{{u['display_name']}}</b> <span class=muted>{{u['username']}} / {{u['role']}}</span>
<input type=password name=new placeholder="new password" style="max-width:180px">
<label style="display:inline"><input type=checkbox name=gen style="width:auto"> generate strong</label>
<button class="btn small">Set &amp; reveal</button></form>{% endfor %}
<p class=muted>Passwords are stored one-way (hashed) \u2014 they cannot be read back.
The value you set is shown once here, so you always control every login. Forgot one? Set a new one.</p></div>
<div class=card><h4>WhatsApp integration</h4>
<p class=muted>Cron endpoint (JSON of amber/red items). The token is a secret \u2014 kept hidden below so it is not on screen by default.</p>
<details><summary class=muted style="cursor:pointer">Show API token</summary>
<p><code>/api/due?token={{token}}</code></p></details>
<form method=post style="margin-top:6px"><input type=hidden name=action value=rotate_token>
<button class="btn small danger" onclick="return confirm('Rotate the API token? The current WhatsApp cron stops working until you update it with the new token.')">Rotate token</button></form></div>
<div class=card><h4>Document text (OCR)</h4>
<p>Sarvam key configured: <b>{{'yes' if ocr_key else 'no'}}</b></p>
<table><tr><th>Status</th><th>Documents</th></tr>
{% for st,n in ocr %}<tr><td>{{st}}</td><td>{{n}}</td></tr>{% endfor %}</table>
<p class=muted>v1.2.0 stores the column and searches it; the Sarvam worker arrives in v1.2.1.
Until then every document reads <code>skipped</code> or <code>pending</code> and nothing else is affected.</p></div>
<div class=card><h4>Drafts</h4><p><b>{{ndrafts}}</b> scanned document(s) waiting to be filed.
<a class="btn small" href="{{url_for('drafts_list')}}">Open drafts</a></p>
<p class=muted>Drafts never expire and are never auto-deleted.</p></div>""",
        users=users, locs=locs, token=setting("api_token"),
        ocr=db.execute("SELECT ocr_status, COUNT(*) FROM attachments GROUP BY ocr_status").fetchall(),
        ndrafts=db.execute("SELECT COUNT(*) FROM drafts").fetchone()[0],
        ocr_key=bool(SARVAM_API_KEY))

# ---------------------------------------------------------------- API for WhatsApp stack
@app.route("/api/due")
def api_due():
    db_ = sqlite3.connect(DB_PATH); db_.row_factory = sqlite3.Row
    tok = db_.execute("SELECT value FROM settings WHERE key='api_token'").fetchone()["value"]
    if request.args.get("token") != tok:
        db_.close(); abort(403)
    rows = db_.execute("""
      SELECT e.label, e.due_date, e.threshold_days, a.name entity_name, 'asset' kind
        FROM expiries e JOIN assets a ON e.entity='asset' AND a.id=e.entity_id WHERE e.resolved=0
      UNION ALL
      SELECT e.label, e.due_date, e.threshold_days, s.name, 'staff'
        FROM expiries e JOIN staff s ON e.entity='staff' AND s.id=e.entity_id WHERE e.resolved=0
      ORDER BY due_date""").fetchall()
    db_.close()
    out = []
    for r in rows:
        state, days = due_state(r["due_date"], r["threshold_days"])
        if state:
            out.append(dict(item=r["entity_name"], kind=r["kind"], what=r["label"],
                            due=r["due_date"], state=state, days=days))
    return jsonify(out)

# ---------------------------------------------------------------- main
if __name__ == "__main__":
    import sys
    if "--migrate-taxonomy" in sys.argv:
        migrate_taxonomy(apply=("--apply" in sys.argv))
    else:
        init_db()
        app.run(debug=True, port=8030)
