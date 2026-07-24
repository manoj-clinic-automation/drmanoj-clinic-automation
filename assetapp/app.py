#!/usr/bin/env python3
"""
Asset Register — v1.0.0
Single-file Flask + SQLite app. Multi-user (2 roles: owner / manager), 3 seeded users.
Location-class visibility + per-row hide overrides; hide_price extends to invoice files.
Generic expiries + attachments schema (assets now, staff module included, more later).
Session-epoch auth (GutLog v3.1 pattern). WhatsApp-stack integration via /api/due token endpoint.

Run:   gunicorn -w 2 -b 127.0.0.1:8030 app:app
Env:   ASSETS_DB (default ./assets.db)   ASSETS_UPLOADS (default ./uploads)
"""
import os, sqlite3, secrets, functools, datetime, mimetypes
from flask import (Flask, request, session, redirect, url_for, abort, g,
                   render_template_string, send_file, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
from werkzeug.utils import secure_filename

APP_VERSION = "1.1.0"
DB_PATH = os.environ.get("ASSETS_DB", os.path.join(os.path.dirname(__file__), "assets.db"))
UPLOAD_DIR = os.environ.get("ASSETS_UPLOADS", os.path.join(os.path.dirname(__file__), "uploads"))
ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png", "webp", "heic", "doc", "docx"}
THRESHOLD_DEFAULT = 60  # days; per-expiry override supported

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
  uploaded_by INTEGER REFERENCES users(id),
  uploaded_at TEXT NOT NULL DEFAULT (datetime('now')));
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

def init_db(seed=True):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
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
    if not os.path.exists(DB_PATH):
        init_db()
    db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row
    row = db.execute("SELECT value FROM settings WHERE key='secret_key'").fetchone()
    db.close()
    return row["value"]
app.secret_key = _load_secret()

# ---------------------------------------------------------------- auth
def current_user():
    uid, epoch = session.get("uid"), session.get("epoch")
    if not uid:
        return None
    if str(epoch) != setting("auth_epoch"):
        session.clear(); return None
    u = get_db().execute("SELECT * FROM users WHERE id=? AND active=1", (uid,)).fetchone()
    return u

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
    where, params = visible_assets_where()
    q = request.args.get("q", "").strip()
    sql = f"""SELECT a.*, l.name loc_name FROM assets a JOIN locations l ON l.id=a.location_id
              WHERE {where}"""
    if q:
        sql += " AND (a.name LIKE ? OR a.vendor LIKE ? OR a.serial_no LIKE ?)"
        params += [f"%{q}%"] * 3
    sql += " ORDER BY a.name"
    rows = get_db().execute(sql, params).fetchall()
    return page("""<h2>Assets</h2>
<form method=get style="margin-bottom:10px"><input name=q value="{{q}}" placeholder="search name / vendor / serial" style="max-width:280px"> <button class="btn small">Search</button></form>
<p><a class=btn href="{{url_for('asset_edit')}}">+ Add asset</a></p>
<table><tr><th>Name</th><th>Location</th><th>Category</th><th>Status</th><th>Contract</th></tr>
{% for a in rows %}<tr><td><a href="{{url_for('asset_view',aid=a['id'])}}">{{a['name']}}</a>
{% if a['hidden'] %}<span class=muted>(hidden)</span>{% endif %}</td>
<td>{{a['loc_name']}}</td><td>{{a['category']}}</td><td>{{a['status']}}</td><td>{{a['contract_type']}}</td></tr>
{% endfor %}</table>""", rows=rows, q=q)

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
            db.commit()
            return redirect(url_for("asset_view", aid=new_id))
    exp = {}
    if a:
        for e in db.execute("SELECT * FROM expiries WHERE entity='asset' AND entity_id=? AND resolved=0", (a["id"],)):
            exp[e["label"]] = e
    return page("""<h2>{{'Edit' if a else 'New'}} asset</h2><div class=card><form method=post>
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
        exp=exp, can_price=(a is None or can_see_price(a)),
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
{% for f in atts %}<div>📄 <a href="{{url_for('file_get',fid=f['id'])}}">{{f['orig_name']}}</a>
{% if f['sensitive'] %}<span class=muted>(price-sensitive)</span>{% endif %}
<span class=muted>by {{f['up_by']}} {{f['uploaded_at'][:10]}}</span></div>{% endfor %}
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
    get_db().execute("""INSERT INTO attachments(entity,entity_id,stored_name,orig_name,sensitive,uploaded_by)
                        VALUES(?,?,?,?,?,?)""",
                     (entity, eid, stored, secure_filename(fobj.filename), sensitive, g.user["id"]))
    get_db().commit()
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
{% for f in atts %}<div>📄 <a href="{{url_for('file_get',fid=f['id'])}}">{{f['orig_name']}}</a>
{% if f['sensitive'] %}<span class=muted>(owner-only)</span>{% endif %}</div>{% endfor %}
<form method=post enctype=multipart/form-data action="{{url_for('file_upload')}}">
<input type=hidden name=entity value=staff><input type=hidden name=entity_id value={{s['id']}}>
<input type=file name=file accept="image/*,.pdf,.doc,.docx" required style="max-width:260px">
{% if is_owner %}<label><input type=checkbox name=sensitive style="width:auto"> owner-only document</label>{% endif %}
<button class="btn small">Upload</button></form></div>""", s=s, exp=exp, atts=atts)

# ---------------------------------------------------------------- built-in scanner
SCAN_TPL = """<h2>📷 Scan document → {{ename}}</h2>
<div class=card>
<input type=file id=cam accept="image/*" capture="environment" style="max-width:300px">
<div id=stage style="display:none">
  <div style="position:relative;display:inline-block;touch-action:none">
    <canvas id=cv style="max-width:100%;border:1px solid #999"></canvas>
    <canvas id=ov style="position:absolute;left:0;top:0;max-width:100%"></canvas>
  </div>
  <p class=muted>Drag the four corners onto the document edges.</p>
  <label><input type=checkbox id=bw checked style="width:auto"> Document mode (B&W contrast boost)</label>
  <p><button type=button class=btn onclick="addPage()">✔ Add page</button>
     <button type=button class="btn small" onclick="resetShot()">↺ Retake</button></p>
</div>
<div id=pages></div>
<p><button type=button class=btn id=finish onclick="finish()" disabled>💾 Save as PDF & attach</button>
   <span id=msg class=muted></span></p>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script>
var srcImg=null, corners=[], drag=-1, done=[];
var cv=document.getElementById('cv'), ov=document.getElementById('ov');
var ctx=cv.getContext('2d'), octx=ov.getContext('2d');
document.getElementById('cam').addEventListener('change',function(e){
  var f=e.target.files[0]; if(!f)return;
  var img=new Image();
  img.onload=function(){
    var s=Math.min(1,1400/Math.max(img.width,img.height));
    cv.width=ov.width=Math.round(img.width*s); cv.height=ov.height=Math.round(img.height*s);
    ctx.drawImage(img,0,0,cv.width,cv.height); srcImg=img;
    var mx=cv.width*0.08,my=cv.height*0.08;
    corners=[[mx,my],[cv.width-mx,my],[cv.width-mx,cv.height-my],[mx,cv.height-my]];
    document.getElementById('stage').style.display='block'; drawOverlay();
  };
  img.src=URL.createObjectURL(f);
});
function drawOverlay(){
  octx.clearRect(0,0,ov.width,ov.height);
  octx.strokeStyle='#1f9dff';octx.lineWidth=3;octx.beginPath();
  octx.moveTo(corners[0][0],corners[0][1]);
  for(var i=1;i<5;i++){var p=corners[i%4];octx.lineTo(p[0],p[1]);}
  octx.stroke();
  corners.forEach(function(p){octx.fillStyle='rgba(31,157,255,.85)';
    octx.beginPath();octx.arc(p[0],p[1],14,0,7);octx.fill();});
}
function evPos(e){
  var r=ov.getBoundingClientRect(), t=e.touches?e.touches[0]:e;
  return [(t.clientX-r.left)*ov.width/r.width,(t.clientY-r.top)*ov.height/r.height];
}
function down(e){var p=evPos(e);drag=-1;var best=2500;
  corners.forEach(function(c,i){var d=(c[0]-p[0])**2+(c[1]-p[1])**2;if(d<best){best=d;drag=i;}});
  if(drag>=0)e.preventDefault();}
function move(e){if(drag<0)return;e.preventDefault();corners[drag]=evPos(e);drawOverlay();}
function up(){drag=-1;}
ov.addEventListener('mousedown',down);ov.addEventListener('mousemove',move);addEventListener('mouseup',up);
ov.addEventListener('touchstart',down,{passive:false});ov.addEventListener('touchmove',move,{passive:false});ov.addEventListener('touchend',up);
function warp(){
  // Heckbert unit-square -> quad homography, inverse-sampled
  var c=corners,x0=c[0][0],y0=c[0][1],x1=c[1][0],y1=c[1][1],x2=c[2][0],y2=c[2][1],x3=c[3][0],y3=c[3][1];
  var W=Math.round((Math.hypot(x1-x0,y1-y0)+Math.hypot(x2-x3,y2-y3))/2);
  var H=Math.round((Math.hypot(x3-x0,y3-y0)+Math.hypot(x2-x1,y2-y1))/2);
  var s=Math.min(1,1600/Math.max(W,H));W=Math.max(50,Math.round(W*s));H=Math.max(50,Math.round(H*s));
  var dx1=x1-x2,dx2=x3-x2,dx3=x0-x1+x2-x3,dy1=y1-y2,dy2=y3-y2,dy3=y0-y1+y2-y3,a,b,cc,d,e,f,g,h;
  if(Math.abs(dx3)<1e-9&&Math.abs(dy3)<1e-9){a=x1-x0;b=x3-x0;cc=x0;d=y1-y0;e=y3-y0;f=y0;g=0;h=0;}
  else{var den=dx1*dy2-dx2*dy1;g=(dx3*dy2-dx2*dy3)/den;h=(dx1*dy3-dx3*dy1)/den;
    a=x1-x0+g*x1;b=x3-x0+h*x3;cc=x0;d=y1-y0+g*y1;e=y3-y0+h*y3;f=y0;}
  var sd=ctx.getImageData(0,0,cv.width,cv.height).data,sw=cv.width,sh=cv.height;
  var out=document.createElement('canvas');out.width=W;out.height=H;
  var oc=out.getContext('2d'),od=oc.createImageData(W,H),D=od.data,k=0;
  for(var r=0;r<H;r++){var v=r/H;
    for(var q=0;q<W;q++){var u=q/W,w=g*u+h*v+1;
      var X=Math.round((a*u+b*v+cc)/w),Y=Math.round((d*u+e*v+f)/w);
      if(X>=0&&Y>=0&&X<sw&&Y<sh){var si=(Y*sw+X)*4;D[k]=sd[si];D[k+1]=sd[si+1];D[k+2]=sd[si+2];}
      else{D[k]=D[k+1]=D[k+2]=255;}
      D[k+3]=255;k+=4;}}
  if(document.getElementById('bw').checked){
    var hist=new Array(256).fill(0),n=W*H;
    for(var i=0;i<D.length;i+=4){var gy=Math.round(.3*D[i]+.59*D[i+1]+.11*D[i+2]);D[i]=gy;hist[gy]++;}
    var lo=0,hi=255,acc=0;
    for(var i=0;i<256;i++){acc+=hist[i];if(acc>n*0.05){lo=i;break;}}
    acc=0;for(var i=255;i>=0;i--){acc+=hist[i];if(acc>n*0.05){hi=i;break;}}
    var rng=Math.max(1,hi-lo);
    for(var i=0;i<D.length;i+=4){var gv=Math.max(0,Math.min(255,Math.round((D[i]-lo)*255/rng)));
      D[i]=D[i+1]=D[i+2]=gv;}}
  oc.putImageData(od,0,0);
  return out;
}
function addPage(){
  var out=warp();done.push(out.toDataURL('image/jpeg',0.85));
  var t=document.createElement('img');t.src=done[done.length-1];
  t.style.cssText='height:90px;border:1px solid #999;margin:3px';
  document.getElementById('pages').appendChild(t);
  document.getElementById('finish').disabled=false;resetShot();
}
function resetShot(){document.getElementById('stage').style.display='none';
  document.getElementById('cam').value='';}
function finish(){
  var msg=document.getElementById('msg');
  var blob,fname;
  if(window.jspdf){
    var pdf=new window.jspdf.jsPDF({unit:'mm',format:'a4'});
    done.forEach(function(du,i){
      if(i>0)pdf.addPage();
      var im=new Image();im.src=du;
      var pw=210-16,ph=297-16,ratio=im.height/im.width||1.4;
      var w=pw,h=pw*ratio;if(h>ph){h=ph;w=ph/ratio;}
      pdf.addImage(du,'JPEG',8,8,w,h);});
    blob=pdf.output('blob');fname='scan_'+new Date().toISOString().slice(0,10)+'.pdf';
  }else{ // CDN unreachable: fall back to first page as JPEG
    var bin=atob(done[0].split(',')[1]),arr=new Uint8Array(bin.length);
    for(var i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
    blob=new Blob([arr],{type:'image/jpeg'});
    fname='scan_'+new Date().toISOString().slice(0,10)+'.jpg';
    msg.textContent='PDF library unreachable — saved page 1 as JPEG. ';
  }
  var fd=new FormData();
  fd.append('entity','{{entity}}');fd.append('entity_id','{{eid}}');
  fd.append('file',blob,fname);
  {% if sensitive_default %}fd.append('sensitive','1');{% endif %}
  msg.textContent='Uploading…';
  fetch('{{url_for("file_upload")}}',{method:'POST',body:fd}).then(function(r){
    if(r.ok){window.location='{{back}}';}else{msg.textContent='Upload failed ('+r.status+')';}
  }).catch(function(){msg.textContent='Upload failed (network)';});
}
</script>
<p><a href="{{back}}">← back without saving</a></p>"""

@app.route("/scan/<entity>/<int:eid>")
@login_required
def scan_page(entity, eid):
    if entity == "asset":
        a = asset_or_403(eid)
        return page(SCAN_TPL, entity="asset", eid=eid, ename=a["name"],
                    back=url_for("asset_view", aid=eid),
                    sensitive_default=bool(a["hide_price"]))
    if entity == "staff":
        s = staff_or_403(eid)
        return page(SCAN_TPL, entity="staff", eid=eid, ename=s["name"],
                    back=url_for("staff_view", sid=eid), sensitive_default=False)
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
            new = request.form.get("new", "")
            if len(new) >= 8:
                db.execute("UPDATE users SET password_hash=? WHERE id=?",
                           (generate_password_hash(new), uid))
                flash("Password reset.")
            else:
                flash("Min 8 characters.")
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
<button class="btn small">Reset</button></form>{% endfor %}</div>
<div class=card><h4>WhatsApp integration</h4>
<p class=muted>Cron endpoint (JSON of amber/red items): <code>/api/due?token={{token}}</code></p></div>""",
        users=users, locs=locs, token=setting("api_token"))

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
    init_db()
    app.run(debug=True, port=8030)
