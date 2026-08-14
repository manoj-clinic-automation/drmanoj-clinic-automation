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
import os, re, sqlite3, secrets, functools, datetime, mimetypes
from flask import (Flask, request, session, redirect, url_for, abort, g,
                   render_template_string, send_file, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
from werkzeug.utils import secure_filename

APP_VERSION = "1.8.1"   # A.4 + Phase D ledger + Phase E Sarvam extract + scan shadow-flatten; v1.8.1: assets index grouped by LOCATION + Supplier/Serial/Purchased columns
DB_PATH = os.environ.get("ASSETS_DB", os.path.join(os.path.dirname(__file__), "assets.db"))
UPLOAD_DIR = os.environ.get("ASSETS_UPLOADS", os.path.join(os.path.dirname(__file__), "uploads"))
SCANNER_JS_PATH = os.path.join(os.path.dirname(__file__), "scanner_widget.js")  # shared scanner widget (Stage 1A)
ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png", "webp", "heic", "doc", "docx"}
THRESHOLD_DEFAULT = 60  # days; per-expiry override supported
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "").strip()
OCR_EXT = {"pdf", "jpg", "jpeg", "png"}   # formats Sarvam Doc AI accepts
# --- screen background palettes (owner picks live in Admin; lower-glare options) ---
PALETTES = {
    "cool": ("Cool blue-grey (default)", "#eaeef3"),
    "sand": ("Warm sand",                "#f1ece3"),
    "sage": ("Soft sage",                "#e9efe8"),
}
DEFAULT_PALETTE = "cool"

# --- Phase E: shared Sarvam Document AI helper (A-D16). Lives at /root/shared so
#     the asset app, the scanner app, and future apps import the SAME file.
import sys as _sys
_SHARED_DIR = os.environ.get("SHARED_LIB_DIR", "/root/shared")
if _SHARED_DIR and _SHARED_DIR not in _sys.path:
    _sys.path.insert(0, _SHARED_DIR)
try:
    import sarvam_ocr as SARVAM
except Exception:
    SARVAM = None   # app runs fine without it; extraction just isn't offered

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
CREATE TABLE IF NOT EXISTS pick_lists(
  id INTEGER PRIMARY KEY, kind TEXT NOT NULL, value TEXT NOT NULL,
  sort INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  UNIQUE(kind, value));
CREATE TABLE IF NOT EXISTS bills(
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'Consumable',
  vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL,
  notes TEXT, source_stored TEXT, source_orig TEXT,
  created_by INTEGER REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS bill_items(
  id INTEGER PRIMARY KEY,
  bill_id INTEGER NOT NULL REFERENCES bills(id),
  item_name TEXT NOT NULL, pack_size TEXT, quantity REAL, rate REAL, amount REAL,
  make TEXT, model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT);
"""

CATEGORIES = ["Lab Equipment", "Medical Equipment", "Electrical (Battery/Inverter/Stabilizer)",
              "IT / Electronics", "Appliance", "Furniture", "Vehicle", "Document / Licence", "Other"]
STATUSES = ["Active", "Under Repair", "Retired", "Sold"]
CONTRACT_TYPES = ["None", "Warranty only", "AMC", "CMC"]
# --- Wave A (v1.5.0) entry-form vocabularies ---
KINDS = ["Asset", "Consumable"]              # Consumable is Phase D (form shows it disabled)
PERIODS = [("none", "(none / not set)"), ("6mo", "6 months"), ("1yr", "1 year"),
           ("2yr", "2 years"), ("3yr", "3 years"), ("5yr", "5 years"), ("custom", "Custom date")]
PERIOD_MONTHS = {"6mo": 6, "1yr": 12, "2yr": 24, "3yr": 36, "5yr": 60}
PAY_METHODS = ["", "Cash", "Bank transfer", "Cheque", "UPI", "Credit Card", "Unpaid"]
BANK_SEED = ["ICICI", "YES", "SBI"]
CARD_SEED = ["ICICI", "HDFC"]
MONTHS = [("01", "Jan"), ("02", "Feb"), ("03", "Mar"), ("04", "Apr"), ("05", "May"),
          ("06", "Jun"), ("07", "Jul"), ("08", "Aug"), ("09", "Sep"), ("10", "Oct"),
          ("11", "Nov"), ("12", "Dec")]
MAX_COPIES = 50                              # cap on "add N identical"
_YEAR_RE = re.compile(r"\d{4}")
_MON_RE = re.compile(r"0[1-9]|1[0-2]")

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
    # --- Wave A (v1.5.0) additive columns ---
    for _col, _ddl in [
        ("kind",            "ALTER TABLE assets ADD COLUMN kind TEXT NOT NULL DEFAULT 'Asset'"),
        ("coverage_start",  "ALTER TABLE assets ADD COLUMN coverage_start TEXT"),
        ("contract_period", "ALTER TABLE assets ADD COLUMN contract_period TEXT"),
        ("payment_method",  "ALTER TABLE assets ADD COLUMN payment_method TEXT"),
        ("pay_account",     "ALTER TABLE assets ADD COLUMN pay_account TEXT"),
        ("emi",             "ALTER TABLE assets ADD COLUMN emi INTEGER NOT NULL DEFAULT 0"),
        ("emi_count",       "ALTER TABLE assets ADD COLUMN emi_count INTEGER"),
        ("emi_amount",      "ALTER TABLE assets ADD COLUMN emi_amount REAL"),
        ("emi_start",       "ALTER TABLE assets ADD COLUMN emi_start TEXT"),
        ("emi_end",         "ALTER TABLE assets ADD COLUMN emi_end TEXT"),
        ("pm_count",        "ALTER TABLE assets ADD COLUMN pm_count INTEGER"),
        ("pay_ref",         "ALTER TABLE assets ADD COLUMN pay_ref TEXT"),
        ("pay_date",        "ALTER TABLE assets ADD COLUMN pay_date TEXT"),
    ]:
        if _col not in acols:
            db.execute(_ddl)
    scols = {r[1] for r in db.execute("PRAGMA table_info(service_logs)")}
    if "is_pm" not in scols:
        db.execute("ALTER TABLE service_logs ADD COLUMN is_pm INTEGER NOT NULL DEFAULT 0")
    for _sc, _sddl in [
        ("svc_type",       "ALTER TABLE service_logs ADD COLUMN svc_type TEXT"),
        ("part_replaced",  "ALTER TABLE service_logs ADD COLUMN part_replaced TEXT"),
        ("part_warranty",  "ALTER TABLE service_logs ADD COLUMN part_warranty TEXT"),
        ("report_att_id",  "ALTER TABLE service_logs ADD COLUMN report_att_id INTEGER"),
    ]:
        if _sc not in scols:
            db.execute(_sddl)

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

def seed_picklists(db):
    """Idempotent: seed bank/card lists + backfill vendor/provider from existing
    assets. Never deletes; only inserts missing rows (UNIQUE(kind,value))."""
    for v in BANK_SEED:
        db.execute("INSERT OR IGNORE INTO pick_lists(kind,value,sort) VALUES('bank',?,0)", (v,))
    for v in CARD_SEED:
        db.execute("INSERT OR IGNORE INTO pick_lists(kind,value,sort) VALUES('card',?,0)", (v,))
    for _kind, _col in (("vendor", "vendor"), ("provider", "provider")):
        q = "SELECT DISTINCT %s FROM assets WHERE %s IS NOT NULL AND TRIM(%s)<>''" % (_col, _col, _col)
        for r in db.execute(q).fetchall():
            db.execute("INSERT OR IGNORE INTO pick_lists(kind,value,sort) VALUES(?,?,0)",
                       (_kind, (r[0] or "").strip()))

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
    seed_picklists(db)
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

def setting_or(key, default):
    """Safe read: returns default when the key is absent (no seed needed on an existing DB)."""
    row = get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

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
def is_image_name(name):
    """True only for browser-renderable image types (heic/doc/pdf excluded from thumbnails)."""
    return bool(name) and "." in name and name.rsplit(".", 1)[1].lower() in {"jpg", "jpeg", "png", "webp", "gif"}

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
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;margin:0;background:{{palette_bg}};color:#2d3742;line-height:1.45}
header{background:#3a5a78;color:#fff;padding:12px 18px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;box-shadow:0 1px 4px rgba(20,40,70,.18)}
header a{color:#dbe7f2;text-decoration:none;margin-left:15px}
header a:hover{color:#fff}
main{max-width:1080px;margin:18px auto;padding:0 14px}
h2{color:#2c4258;font-weight:600;margin:.2em 0 .5em}
h4{color:#3a5a78;margin:0 0 10px}
a{color:#3a5a78}
table{border-collapse:collapse;width:100%;background:#fff;border-radius:8px;overflow:hidden}
th,td{border:1px solid #eef1f5;padding:8px 10px;font-size:14px;text-align:left}
th{background:#f2f5f9;color:#3a5a78;font-weight:600}
.card{background:#fff;border:1px solid #e4e9ef;border-radius:10px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(20,40,70,.06)}
.amber{background:#fdf3e4}.red{background:#fbecec}
.badge{padding:2px 9px;border-radius:10px;font-size:12px;font-weight:600;white-space:nowrap}
.badge.amber{background:#c47f1a;color:#fff}.badge.red{background:#b23b3b;color:#fff}.badge.green{background:#2e7d5b;color:#fff}
input,select,textarea{padding:8px;margin:3px 0;width:100%;max-width:420px;box-sizing:border-box;border:1px solid #cfd8e3;border-radius:6px;background:#fff;font-size:14px;color:#2d3742}
input:focus,select:focus,textarea:focus{outline:none;border-color:#9db8d4;box-shadow:0 0 0 2px rgba(157,184,212,.5)}
label{font-size:13px;color:#5a6b7b;display:block;margin-top:9px}
button,.btn{background:#3a5a78;color:#fff;border:0;padding:9px 17px;border-radius:6px;cursor:pointer;text-decoration:none;display:inline-block;font-size:14px;transition:background .15s}
button:hover,.btn:hover{background:#31506c}
.btn.small{padding:4px 10px;font-size:12px}
.btn.danger{background:#b23b3b}.btn.danger:hover{background:#9c3131}
.flash{background:#fff8e6;border:1px solid #f2e3b3;color:#6b5a1a;padding:9px 13px;margin-bottom:12px;border-radius:6px}
.muted{color:#8a97a5;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
</style></head><body>
<header><div><b>🗂 Asset Register</b> <span class=muted style="color:#9fb3d9">v{{version}}</span></div>
<nav>{% if user %}<a href="{{url_for('dashboard')}}">Dashboard</a>
<a href="{{url_for('assets_list')}}">Assets</a>
<a href="{{url_for('renewals')}}">Renewals</a>
<a href="{{url_for('drafts_list')}}">Drafts</a>
<a href="{{url_for('staff_list')}}">Staff</a>
{% if user['role']=='owner' %}<a href="{{url_for('bills_list')}}">Purchases</a>{% endif %}
{% if user['role']=='owner' %}<a href="{{url_for('admin')}}">Admin</a>{% endif %}
<a href="{{url_for('account')}}">{{user['display_name']}}</a>
<a href="{{url_for('logout')}}">Logout</a>{% endif %}</nav></header>
<main>{% with m=get_flashed_messages() %}{% for f in m %}<div class=flash>{{f}}</div>{% endfor %}{% endwith %}
{{body}}</main></body></html>"""

def page(body_tpl, **ctx):
    u = current_user()
    body = render_template_string(body_tpl, user=u, is_owner=(u and u["role"] == "owner"), **ctx)
    pal = setting_or("palette", DEFAULT_PALETTE)
    if pal not in PALETTES:
        pal = DEFAULT_PALETTE
    return render_template_string(BASE, user=u, body=Markup(body), version=APP_VERSION,
                                  palette_bg=PALETTES[pal][1])

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
    """Grouped index: by LOCATION (assets always carry a location_id, so every
    asset lands in a real, labelled section). Visibility gate + facets + search
    unchanged; the unclassified bucket sorts last so nothing is ever hidden."""
    where, params = visible_assets_where()
    q = request.args.get("q", "").strip()
    # A.4c: cascading facets (Entity -> Zone -> Category / Kind / Status)
    f_ent = request.args.get("f_ent", type=int)
    f_zone = request.args.get("f_zone", type=int)
    f_cat = request.args.get("f_cat", "").strip()
    f_kind = request.args.get("f_kind", "").strip()
    f_status = request.args.get("f_status", "").strip()
    doc_sub = ("(SELECT COUNT(*) FROM attachments at WHERE at.entity='asset' "
               "AND at.entity_id=a.id AND at.document_text LIKE ?)")
    cols = ("a.*, l.name loc_name, en.name ent_name, en.sort ent_sort, "
            "zn.name zone_name, zn.sort zone_sort")
    joins = ("FROM assets a JOIN locations l ON l.id=a.location_id "
             "LEFT JOIN entities en ON en.id=a.entity_id LEFT JOIN zones zn ON zn.id=a.zone_id")
    db = get_db()
    # facet OPTIONS from the VISIBLE set only (never leak owner-only names; never offer empty filters)
    ent_opts = db.execute(
        f"SELECT DISTINCT en.id id, en.name name {joins} WHERE {where} AND en.id IS NOT NULL "
        "ORDER BY en.sort, en.name", list(params)).fetchall()
    zwhere = where + (" AND a.entity_id=?" if f_ent else "")
    zparams = list(params) + ([f_ent] if f_ent else [])
    zone_opts = db.execute(
        f"SELECT DISTINCT zn.id id, zn.name name {joins} WHERE {zwhere} AND zn.id IS NOT NULL "
        "ORDER BY zn.sort, zn.name", zparams).fetchall()
    def _facet_vals(col):
        return [r["v"] for r in db.execute(
            f"SELECT DISTINCT {col} v {joins} WHERE {where} AND {col} IS NOT NULL AND {col}<>'' "
            "ORDER BY v", list(params))]
    cat_opts = _facet_vals("a.category")
    kind_opts = _facet_vals("a.kind")
    status_opts = _facet_vals("a.status")
    # changing entity resets a now-invalid zone selection
    if f_zone and f_zone not in {z["id"] for z in zone_opts}:
        f_zone = None
    # facet WHERE
    fclauses, fparams = [], []
    if f_ent:
        fclauses.append("a.entity_id=?"); fparams.append(f_ent)
    if f_zone:
        fclauses.append("a.zone_id=?"); fparams.append(f_zone)
    if f_cat:
        fclauses.append("a.category=?"); fparams.append(f_cat)
    if f_kind:
        fclauses.append("a.kind=?"); fparams.append(f_kind)
    if f_status:
        fclauses.append("a.status=?"); fparams.append(f_status)
    facet_sql = "".join(" AND " + c for c in fclauses)
    if q:
        sql = f"SELECT {cols}, {doc_sub} doc_hit {joins} WHERE {where}{facet_sql}"
        mp = [f"%{q}%"] + list(params) + fparams
        sql += (" AND (a.name LIKE ? OR a.vendor LIKE ? OR a.serial_no LIKE ?"
                " OR EXISTS(SELECT 1 FROM attachments at2 WHERE at2.entity='asset'"
                " AND at2.entity_id=a.id AND at2.document_text LIKE ?))")
        mp += [f"%{q}%"] * 4
    else:
        sql = f"SELECT {cols}, 0 doc_hit {joins} WHERE {where}{facet_sql}"
        mp = list(params) + fparams
    sql += " ORDER BY a.name"
    rows = db.execute(sql, mp).fetchall()

    # due-soon state per visible asset (worst of its unresolved expiries)
    due_by_asset = {}
    ids = [a["id"] for a in rows]
    if ids:
        qm = ",".join("?" * len(ids))
        for e in get_db().execute(
                "SELECT entity_id, due_date, threshold_days FROM expiries "
                "WHERE entity='asset' AND resolved=0 AND entity_id IN (%s)" % qm, ids):
            st, days = due_state(e["due_date"], e["threshold_days"])
            if not st:
                continue
            rank = 2 if st == "red" else 1
            cur = due_by_asset.get(e["entity_id"])
            if not cur or rank > cur[0]:
                due_by_asset[e["entity_id"]] = (rank, st, days)

    # group by LOCATION (populated for every asset via location_id); the
    # unclassified "\u2014" bucket, if any, always sorts last.
    groups = {}
    for a in rows:
        ln = a["loc_name"] or "\u2014"
        g = groups.setdefault(ln, {"rows": [], "amber": 0, "red": 0})
        g["rows"].append(a)
        d = due_by_asset.get(a["id"])
        if d:
            g["red" if d[1] == "red" else "amber"] += 1
    ordered = []
    for ln, g in sorted(groups.items(), key=lambda kv: (kv[0] == "\u2014", kv[0].lower())):
        ordered.append((ln, len(g["rows"]), g["amber"], g["red"], g["rows"]))

    return page("""<h2>Assets</h2>
<form method=get style="margin-bottom:10px">
<input name=q value="{{q}}" placeholder="search name / vendor / serial / document text" style="max-width:240px">
<select name=f_ent onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Entity: all</option>{% for e in ent_opts %}<option value="{{e['id']}}" {{'selected' if e['id']==f_ent}}>{{e['name']}}</option>{% endfor %}</select>
<select name=f_zone onchange="this.form.submit()" style="width:auto;max-width:140px"><option value="">Zone: all</option>{% for z in zone_opts %}<option value="{{z['id']}}" {{'selected' if z['id']==f_zone}}>{{z['name']}}</option>{% endfor %}</select>
<select name=f_cat onchange="this.form.submit()" style="width:auto;max-width:160px"><option value="">Category: all</option>{% for c in cat_opts %}<option {{'selected' if c==f_cat}}>{{c}}</option>{% endfor %}</select>
<select name=f_kind onchange="this.form.submit()" style="width:auto;max-width:120px"><option value="">Kind: all</option>{% for k in kind_opts %}<option {{'selected' if k==f_kind}}>{{k}}</option>{% endfor %}</select>
<select name=f_status onchange="this.form.submit()" style="width:auto;max-width:130px"><option value="">Status: all</option>{% for s in status_opts %}<option {{'selected' if s==f_status}}>{{s}}</option>{% endfor %}</select>
<button class="btn small">Search</button>{% if q or f_ent or f_zone or f_cat or f_kind or f_status %} <a class="btn small" href="{{url_for('assets_list')}}">clear</a>{% endif %}</form>
<p><a class=btn href="{{url_for('asset_edit')}}">+ Add asset</a>
<a class="btn small" href="{{url_for('drafts_list')}}">\U0001F4F7 Scan first (Drafts)</a></p>
{% for loc_name, cnt, amber, red, rows in ordered %}
<details open><summary style="font-size:16px;font-weight:bold;cursor:pointer;padding:8px 0;color:#1f3864">{{loc_name}} <span class=muted>({{cnt}})</span>{% if red %} <span class="badge red">{{red+amber}} due</span>{% elif amber %} <span class="badge amber">{{amber}} due</span>{% endif %}</summary>
<table style="margin:4px 0 10px"><tr><th>Name</th><th>Category</th><th>Serial</th><th>Supplier</th><th>Purchased</th><th>Status</th><th>Contract</th></tr>
{% for a in rows %}<tr><td><a href="{{url_for('asset_view',aid=a['id'])}}">{{a['name']}}</a>{% if a['hidden'] %} <span class=muted>(hidden)</span>{% endif %}{% if a['doc_hit'] %}<br><span class=muted>\u21b3 matched in attached document</span>{% endif %}</td>
<td>{{a['category']}}</td><td>{{a['serial_no'] or '\u2014'}}</td><td>{{a['vendor'] or '\u2014'}}</td><td>{{a['purchase_date'] or '\u2014'}}</td><td>{{a['status']}}</td>
<td>{{a['contract_type']}}{% set d = due.get(a['id']) %}{% if d %} <span class="badge {{d[1]}}">{{'overdue' if d[2]<0 else (d[2]|string)+'d'}}</span>{% endif %}</td></tr>
{% endfor %}</table>
</details>
{% endfor %}
{% if not ordered %}<p class=muted>No assets{{' match your search' if q else ''}}.</p>{% endif %}""",
        ordered=ordered, q=q, due=due_by_asset,
        ent_opts=ent_opts, zone_opts=zone_opts, cat_opts=cat_opts, kind_opts=kind_opts,
        status_opts=status_opts, f_ent=f_ent, f_zone=f_zone, f_cat=f_cat, f_kind=f_kind, f_status=f_status)

@app.route("/renewals")
@login_required
def renewals():
    db = get_db()
    show_all = request.args.get("all")
    where, params = visible_assets_where()
    rows = db.execute(f"""
        SELECT e.label, e.due_date, e.threshold_days, a.id aid, a.name aname,
               en.name ent_name, en.sort ent_sort
          FROM expiries e
          JOIN assets a ON e.entity='asset' AND a.id=e.entity_id
          JOIN locations l ON l.id=a.location_id
          LEFT JOIN entities en ON en.id=a.entity_id
         WHERE e.resolved=0 AND {where}
         ORDER BY COALESCE(en.sort, 9999), en.name, e.due_date""", params).fetchall()
    groups = {}
    for r in rows:
        st, days = due_state(r["due_date"], r["threshold_days"])
        if not show_all and not st:
            continue
        en = r["ent_name"] or "Unclassified"
        es = r["ent_sort"] if r["ent_sort"] is not None else 9999
        groups.setdefault(en, {"sort": es, "items": []})["items"].append((r, st, days))
    ordered = sorted(groups.items(), key=lambda kv: (kv[1]["sort"], kv[0]))
    return page("""<h2>Renewals &amp; warranties</h2>
<p class=muted>{{ 'All upcoming' if show_all else 'Due soon (amber / overdue)' }} \u00b7
{% if show_all %}<a href="{{url_for('renewals')}}">due soon only</a>{% else %}<a href="{{url_for('renewals', all=1)}}">show all upcoming</a>{% endif %}</p>
{% if not ordered %}<p class=muted>Nothing {{'to show.' if show_all else 'due soon. All clear.'}}</p>{% endif %}
{% for ent_name, g in ordered %}
<div class=card><h3 style="color:#1f3864">{{ent_name}} <span class=muted>({{g['items']|length}})</span></h3>
<table><tr><th>Asset</th><th>What</th><th>Due</th><th>Status</th></tr>
{% for r,state,days in g['items'] %}<tr class="{{state}}">
<td><a href="{{url_for('asset_view',aid=r['aid'])}}">{{r['aname']}}</a></td>
<td>{{r['label']}}</td><td>{{r['due_date']}}</td>
<td>{% if state %}<span class="badge {{state}}">{{'overdue' if days<0 else (days|string)+' days'}}</span>{% elif days is not none %}<span class=muted>{{days}} days</span>{% else %}<span class=muted>\u2014</span>{% endif %}</td>
</tr>{% endfor %}</table></div>
{% endfor %}""", ordered=ordered, show_all=bool(show_all))


def locations_for_user():
    if is_owner():
        return get_db().execute("SELECT * FROM locations ORDER BY id").fetchall()
    return get_db().execute("SELECT * FROM locations WHERE visibility='general' ORDER BY id").fetchall()

# ---------------------------------------------------------------- Wave A helpers
ENTITY_DEFAULT_LOC = {"Dr Manoj Clinic": "Clinic", "NK Pathology": "NK Path",
                      "Personal": "Personal - Dr Manoj"}

def entities_for_user():
    if is_owner():
        return get_db().execute("SELECT * FROM entities ORDER BY sort, name").fetchall()
    return get_db().execute(
        "SELECT * FROM entities WHERE visibility='general' ORDER BY sort, name").fetchall()

def zones_by_entity():
    m = {}
    for z in get_db().execute("SELECT id, entity_id, name FROM zones ORDER BY sort, name"):
        m.setdefault(z["entity_id"], []).append([z["id"], z["name"]])
    return m

def entity_visible_or_403(eid):
    e = get_db().execute("SELECT * FROM entities WHERE id=?", (eid,)).fetchone()
    if not e or (not is_owner() and e["visibility"] != "general"):
        abort(403)
    return e

def entity_default_location_id(entity_name):
    db = get_db()
    nm = ENTITY_DEFAULT_LOC.get(entity_name)
    if nm:
        r = db.execute("SELECT id FROM locations WHERE name=?", (nm,)).fetchone()
        if r:
            return r["id"]
    r = db.execute("SELECT id FROM locations ORDER BY id LIMIT 1").fetchone()
    return r["id"] if r else None

def pick(kind):
    return [r["value"] for r in get_db().execute(
        "SELECT value FROM pick_lists WHERE kind=? AND active=1 ORDER BY sort, value", (kind,))]

def add_pick(kind, value):
    value = (value or "").strip()
    if value:
        get_db().execute(
            "INSERT OR IGNORE INTO pick_lists(kind,value,sort) VALUES(?,?,0)", (kind, value))

def compose_ym(y, m):
    y = (y or "").strip(); m = (m or "").strip()
    if _YEAR_RE.fullmatch(y) and _MON_RE.fullmatch(m):
        return "%s-%s-01" % (y, m)
    return None

def split_ym(date_str):
    if date_str and re.match(r"^\d{4}-\d{2}", date_str):
        return date_str[:4], date_str[5:7]
    return "", ""

def add_months(date_str, n):
    try:
        d = datetime.date.fromisoformat(date_str)
    except Exception:
        return None
    total = d.year * 12 + (d.month - 1) + int(n)
    y, mo = divmod(total, 12)
    return "%04d-%02d-01" % (y, mo + 1)

def year_choices():
    y = today().year
    return [str(x) for x in range(y - 20, y + 8)]

FORM_TEMPLATE = """<h2>{{'Edit' if a else 'New'}} asset</h2>
{% if draft %}<div class=card style="background:#eef5ff">📄 <b>{{draft['orig_name']}}</b>
<a class="btn small" href="{{url_for('draft_preview',did=draft['id'])}}" target=_blank>Open document</a>
<div class=muted>This document attaches to the asset when you save.</div></div>{% endif %}
<div class=card><form method=post>
{% if draft %}<input type=hidden name=draft_id value={{draft['id']}}>{% endif %}
<label>Kind</label>
<select name=kind id=kind>{% for k in kinds %}<option value="{{k}}" {{'selected' if (a and a['kind']==k) or (not a and k=='Asset')}} {{'disabled' if k!='Asset'}}>{{k}}{{' (Phase D)' if k!='Asset'}}</option>{% endfor %}</select>
<label>Name*</label><input name=name value="{{a['name'] if a else ''}}" required>
<label>Entity</label>
<select name=entity_id id=entity onchange="fillZones()">{% for e in ents %}<option value="{{e['id']}}" {{'selected' if a and a['entity_id']==e['id']}}>{{e['name']}}{{' 🔒' if e['visibility']=='owner_only'}}</option>{% endfor %}</select>
<label>Zone <span class=muted>(area within the entity, e.g. Reception, OT)</span></label><select name=zone_id id=zone></select>
<label>Category</label><select name=category>{% for c in cats %}<option {{'selected' if a and a['category']==c}}>{{c}}</option>{% endfor %}</select>
<label>Purchase month / year</label>
<div style="display:flex;gap:6px;max-width:420px">
<select name=purchase_month id=pmonth style="flex:1">{% for mv,ml in months %}<option value="{{mv}}" {{'selected' if pm==mv}}>{{ml}}</option>{% endfor %}</select>
<select name=purchase_year id=pyear style="flex:1"><option value="">— year —</option>{% for y in years %}<option {{'selected' if py==y}}>{{y}}</option>{% endfor %}</select></div>
{% if not a or can_price %}<label>Purchase price (₹)</label><input type=number step=0.01 name=price oninput="emiRecalc()" value="{{a['price'] or '' if a else ''}}">{% endif %}
<label>Vendor</label>
<select onchange="if(this.value){document.getElementById('vendor_in').value=this.value}" style="max-width:200px"><option value="">— pick existing —</option>{% for v in vendors %}<option>{{v}}</option>{% endfor %}</select>
<input id=vendor_in name=vendor placeholder="or type a new vendor" value="{{a['vendor'] or '' if a else ''}}">
<label>Vendor phone</label><input name=vendor_phone value="{{a['vendor_phone'] or '' if a else ''}}">
<label>Serial / model no.</label><input name=serial_no value="{{a['serial_no'] or '' if a else ''}}">
<label>Status</label><select name=status>{% for s in sts %}<option {{'selected' if a and a['status']==s}}>{{s}}</option>{% endfor %}</select>
<hr><label style="font-weight:bold;color:#1f3864">Contract / warranty</label>
<label>Contract type</label><select name=contract_type id=ctype onchange="ctypeChange()">{% for c in cts %}<option {{'selected' if a and a['contract_type']==c}}>{{c}}</option>{% endfor %}</select>
<div id=contractdetail>
<div id=amconly>
<label>Service provider</label>
<select onchange="if(this.value){document.getElementById('provider_in').value=this.value}" style="max-width:200px"><option value="">— pick existing —</option>{% for p in providers %}<option>{{p}}</option>{% endfor %}</select>
<input id=provider_in name=provider placeholder="or type a new provider" value="{{a['provider'] or '' if a else ''}}">
{% if not a or can_price %}<label>Contract cost (₹/yr)</label><input type=number step=0.01 name=contract_cost value="{{a['contract_cost'] or '' if a else ''}}">{% endif %}
<label>Preventive-maintenance visits included in contract</label><input type=number name=pm_count min=0 placeholder="e.g. 4 per year" value="{{a['pm_count'] or '' if a else ''}}">
</div>
<label id=periodlabel>Contract term</label>
<select name=contract_period id=period onchange="periodChange()">{% for pv,pl in periods %}<option value="{{pv}}" {{'selected' if a and a['contract_period']==pv}}>{{pl}}</option>{% endfor %}</select>
<div id=coverwrap><label>Coverage start month / year <span class=muted>(defaults to purchase)</span></label>
<div style="display:flex;gap:6px;max-width:420px">
<select name=coverage_month style="flex:1">{% for mv,ml in months %}<option value="{{mv}}" {{'selected' if cm==mv}}>{{ml}}</option>{% endfor %}</select>
<select name=coverage_year style="flex:1"><option value="">— year —</option>{% for y in years %}<option {{'selected' if cy==y}}>{{y}}</option>{% endfor %}</select></div></div>
<div id=customwrap><label>Warranty till (exact date)</label><input type=date name=warranty_till value="{{exp['Warranty']['due_date'] if 'Warranty' in exp else ''}}">
<label>Contract renewal date (exact date)</label><input type=date name=renewal_date value="{{exp['Contract renewal']['due_date'] if 'Contract renewal' in exp else ''}}"></div>
</div>
<label>Reminder threshold (days before due; default 60)</label><input type=number name=threshold_days value="{{thr}}">
{% if not a or can_price %}<hr><label style="font-weight:bold;color:#1f3864">Payment (record only)</label>
<label>Paid via</label><select name=payment_method id=paymethod onchange="payChange()">{% for pmx in pay_methods %}<option value="{{pmx}}" {{'selected' if a and a['payment_method']==pmx}}>{{pmx or '—'}}</option>{% endfor %}</select>
<div id=acctwrap><label id=acctlabel>Bank</label>
<select id=payacctsel onchange="if(this.value){document.getElementById('pay_account_in').value=this.value}" style="max-width:200px"></select>
<input id=pay_account_in name=pay_account placeholder="or type a new one" value="{{a['pay_account'] or '' if a else ''}}"></div>
<div id=chequewrap style="display:none"><label>Cheque number</label><input name=cheque_no value="{{a['pay_ref'] or '' if a else ''}}" placeholder="cheque no.">
<label>Cheque date</label><input type=date name=pay_date value="{{a['pay_date'] or '' if a else ''}}"></div>
<div id=upiwrap style="display:none"><label>UPI reference <span class=muted>(optional)</span></label><input name=upi_ref value="{{a['pay_ref'] or '' if a else ''}}" placeholder="UPI txn ref"></div>
<div id=emiopt><label><input type=checkbox name=emi id=emi style="width:auto" {{'checked' if a and a['emi']}} onchange="emiCheck()"> Paid in EMIs</label></div>
<div id=emiwrap><div style="display:flex;gap:6px;max-width:420px">
<input type=number name=emi_count placeholder="no. of instalments" value="{{a['emi_count'] or '' if a else ''}}" oninput="emiRecalc()" style="flex:1">
<input type=number step=0.01 name=emi_amount placeholder="₹ per instalment (auto)" value="{{a['emi_amount'] or '' if a else ''}}" oninput="emiAuto=false" style="flex:1"></div>
<label>EMI start month / year <span class=muted>(defaults to purchase)</span></label><div style="display:flex;gap:6px;max-width:420px">
<select name=emi_month id=emimonth style="flex:1">{% for mv,ml in months %}<option value="{{mv}}" {{'selected' if em==mv}}>{{ml}}</option>{% endfor %}</select>
<select name=emi_year id=emiyear style="flex:1"><option value="">— year —</option>{% for y in years %}<option {{'selected' if ey==y}}>{{y}}</option>{% endfor %}</select></div>
<div class=muted id=emiend></div></div>{% endif %}
{% if not a %}<hr><label>Make identical copies <span class=muted>(one form -> N separate records, for bulk-bought items; max {{max_copies}})</span></label>
<input type=number name=make_copies value=1 min=1 max={{max_copies}} style="max-width:120px">{% endif %}
<label>Notes</label><textarea name=notes rows=3>{{a['notes'] or '' if a else ''}}</textarea>
{% if is_owner %}<label><input type=checkbox name=hidden style="width:auto" {{'checked' if a and a['hidden']}}> Hide entire asset from manager</label>
<label><input type=checkbox name=hide_price style="width:auto" {{'checked' if a and a['hide_price']}}> Hide price & invoices from manager</label>{% endif %}
<br><button>Save</button></form></div>
<script>
var ZONES = {{zmap_json}};
var CUR_ZONE = {{ a['zone_id'] if a and a['zone_id'] else 'null' }};
var BANKS = {{banks_json}};
var CARDS = {{cards_json}};
var emiAuto = {{ 'false' if a and a['emi_amount'] else 'true' }};
function fillZones(){
  var e=document.getElementById('entity'), z=document.getElementById('zone');
  var list=ZONES[e.value]||[]; z.innerHTML='';
  for(var i=0;i<list.length;i++){var o=document.createElement('option');o.value=list[i][0];o.textContent=list[i][1];if(list[i][0]==CUR_ZONE)o.selected=true;z.appendChild(o);}
}
function ctypeChange(){
  var el=document.getElementById('ctype'); if(!el) return; var t=el.value;
  var det=document.getElementById('contractdetail'), amc=document.getElementById('amconly'), pl=document.getElementById('periodlabel');
  if(t=='None'){ if(det) det.style.display='none'; return; }
  if(det) det.style.display='block';
  if(t=='Warranty only'){ if(amc) amc.style.display='none'; if(pl) pl.textContent='Warranty period'; }
  else { if(amc) amc.style.display='block'; if(pl) pl.textContent='Contract term'; }
  periodChange();
}
function periodChange(){
  var el=document.getElementById('period'); if(!el) return; var p=el.value;
  var cw=document.getElementById('customwrap'), ov=document.getElementById('coverwrap');
  if(cw) cw.style.display=(p=='custom')?'block':'none';
  if(ov) ov.style.display=(p=='custom'||p=='none')?'none':'block';
}
function fillAccts(){
  var mEl=document.getElementById('paymethod'), sel=document.getElementById('payacctsel');
  if(!mEl||!sel) return; var m=mEl.value;
  var list=(m=='Bank transfer'||m=='Cheque')?BANKS:((m=='Credit Card')?CARDS:[]);
  var lbl=document.getElementById('acctlabel'); if(lbl) lbl.textContent=(m=='Credit Card')?'Card':'Bank';
  sel.innerHTML=''; var ph=document.createElement('option'); ph.value=''; ph.textContent='- pick existing -'; sel.appendChild(ph);
  for(var i=0;i<list.length;i++){var o=document.createElement('option');o.textContent=list[i];sel.appendChild(o);}
}
function payChange(){
  var mEl=document.getElementById('paymethod'); if(!mEl) return; var m=mEl.value;
  var acct=(m=='Bank transfer'||m=='Cheque'||m=='Credit Card');
  var aw=document.getElementById('acctwrap'); if(aw) aw.style.display=acct?'block':'none';
  var cq=document.getElementById('chequewrap'); if(cq) cq.style.display=(m=='Cheque')?'block':'none';
  var up=document.getElementById('upiwrap'); if(up) up.style.display=(m=='UPI')?'block':'none';
  var eo=document.getElementById('emiopt'); if(eo) eo.style.display=(m=='Bank transfer'||m=='Credit Card')?'block':'none';
  fillAccts(); emiSync();
}
function emiSync(){ var e=document.getElementById('emi'), ew=document.getElementById('emiwrap'); if(ew) ew.style.display=(e&&e.checked)?'block':'none'; emiRecalc(); }
function emiCheck(){
  var e=document.getElementById('emi');
  if(e&&e.checked){
    var ey=document.getElementById('emiyear'), em=document.getElementById('emimonth');
    var py=document.getElementById('pyear'), pm=document.getElementById('pmonth');
    if(ey&&!ey.value&&py&&py.value){ ey.value=py.value; if(em&&pm) em.value=pm.value; }
  }
  emiSync();
}
function emiRecalc(){
  var cf=document.querySelector('[name=emi_count]'); if(!cf) return; var cnt=parseInt(cf.value||'0');
  var prf=document.querySelector('[name=price]'); var pr=prf?parseFloat(prf.value||'0'):0;
  var amt=document.querySelector('[name=emi_amount]');
  if(emiAuto && amt && cnt>0 && pr>0){ amt.value=Math.round(pr/cnt); }
  var syEl=document.getElementById('emiyear'), smEl=document.getElementById('emimonth');
  var sy=syEl?syEl.value:'', sm=smEl?smEl.value:'';
  var out=document.getElementById('emiend');
  if(out){ if(cnt>0&&sy&&sm){ var idx=(parseInt(sy)*12+(parseInt(sm)-1))+(cnt-1); var yy=Math.floor(idx/12), mm=(idx%12)+1; out.textContent='Last instalment: '+yy+'-'+('0'+mm).slice(-2); } else { out.textContent=''; } }
}
fillZones(); ctypeChange(); payChange();
</script>"""

@app.route("/assets/new", methods=["GET", "POST"])

@app.route("/assets/<int:aid>/edit", methods=["GET", "POST"])
@login_required
def asset_edit(aid=None):
    db = get_db()
    a = asset_or_403(aid) if aid else None
    if request.method == "POST":
        f = request.form
        # --- resolve entity/zone/location + visibility (new cascade path OR legacy) ---
        eid = f.get("entity_id", type=int)
        zid = f.get("zone_id", type=int)
        if eid:
            ent = entity_visible_or_403(eid)
            if zid:
                zrow = db.execute("SELECT id FROM zones WHERE id=? AND entity_id=?",
                                  (zid, eid)).fetchone()
                if not zrow:
                    zid = None
            loc_id = entity_default_location_id(ent["name"])
        else:
            # legacy path (fallback form + smoke tests): location_id drives visibility.
            # entity_id/zone_id are LEFT UNTOUCHED (never wiped) -> taxonomy backfill still applies.
            loc = db.execute("SELECT * FROM locations WHERE id=?",
                             (f.get("location_id"),)).fetchone()
            if not loc or (not is_owner() and loc["visibility"] != "general"):
                abort(403)
            loc_id = loc["id"]
        # --- dates: month/year dropdowns preferred, raw date field as fallback ---
        purchase_date = compose_ym(f.get("purchase_year"), f.get("purchase_month")) \
            or (f.get("purchase_date") or None)
        coverage_start = compose_ym(f.get("coverage_year"), f.get("coverage_month")) \
            or purchase_date
        # --- contract / period engine -> effective warranty + renewal dates ---
        period = f.get("contract_period") or "none"
        ctype = f.get("contract_type") if f.get("contract_type") in CONTRACT_TYPES else "None"
        eff_warranty = f.get("warranty_till") or None
        eff_renewal = f.get("renewal_date") or None
        if period in PERIOD_MONTHS and coverage_start:
            computed = add_months(coverage_start, PERIOD_MONTHS[period])
            if ctype == "Warranty only":
                eff_warranty = computed
            elif ctype in ("AMC", "CMC"):
                eff_renewal = computed
        # --- payment / EMI (record-only) ---
        pay_method = f.get("payment_method") if f.get("payment_method") in PAY_METHODS else ""
        pay_account = (f.get("pay_account") or "").strip() or None
        emi = 1 if f.get("emi") else 0
        emi_count = f.get("emi_count", type=int) if f.get("emi_count") else None
        emi_amount = float(f["emi_amount"]) if f.get("emi_amount") else None
        emi_start = compose_ym(f.get("emi_year"), f.get("emi_month")) or (purchase_date if emi else None)
        emi_end = add_months(emi_start, emi_count - 1) if (emi and emi_start and emi_count) else None
        pay_ref = None
        if pay_method == "Cheque":
            pay_ref = (f.get("cheque_no") or "").strip() or None
        elif pay_method == "UPI":
            pay_ref = (f.get("upi_ref") or "").strip() or None
        pay_date = f.get("pay_date") or None            # cheque date (only method that uses it)
        if pay_method in ("Bank transfer", "Cheque") and pay_account:
            add_pick("bank", pay_account)
        elif pay_method == "Credit Card" and pay_account:
            add_pick("card", pay_account)
        vendor = (f.get("vendor") or "").strip() or None
        provider = (f.get("provider") or "").strip() or None
        if vendor:
            add_pick("vendor", vendor)
        if provider:
            add_pick("provider", provider)
        vals = dict(
            name=f.get("name", "").strip(), location_id=loc_id,
            kind=f.get("kind") if f.get("kind") in KINDS else "Asset",
            category=f.get("category") if f.get("category") in CATEGORIES else "Other",
            purchase_date=purchase_date, coverage_start=coverage_start,
            price=float(f["price"]) if f.get("price") else None,
            vendor=vendor, vendor_phone=f.get("vendor_phone") or None,
            serial_no=f.get("serial_no") or None,
            status=f.get("status") if f.get("status") in STATUSES else "Active",
            contract_type=ctype, contract_period=period, provider=provider,
            contract_cost=float(f["contract_cost"]) if f.get("contract_cost") else None,
            payment_method=pay_method or None, pay_account=pay_account,
            pay_ref=pay_ref, pay_date=pay_date,
            emi=emi, emi_count=emi_count, emi_amount=emi_amount,
            emi_start=emi_start, emi_end=emi_end,
            pm_count=(f.get("pm_count", type=int) if (f.get("pm_count") and ctype in ("AMC", "CMC")) else None),
            notes=f.get("notes") or None)
        # only set the taxonomy axis when the cascade posts it (never wipe on a legacy edit)
        if eid:
            vals["entity_id"] = eid
            vals["zone_id"] = zid
        elif not a:
            vals["entity_id"] = None
            vals["zone_id"] = None
        if is_owner():
            vals["hidden"] = 1 if f.get("hidden") else 0
            vals["hide_price"] = 1 if f.get("hide_price") else 0
        elif a and a["hide_price"]:
            # manager editing a price-hidden asset: never overwrite money fields with NULL
            for k in ("price", "contract_cost", "payment_method", "pay_account",
                      "pay_ref", "pay_date",
                      "emi", "emi_count", "emi_amount", "emi_start", "emi_end"):
                vals[k] = a[k]
        if not vals["name"]:
            flash("Name is required.")
        else:
            copies = 1
            if not a:
                copies = f.get("make_copies", type=int) or 1
                copies = max(1, min(MAX_COPIES, copies))
            first_id = None
            for _rep in range(1 if a else copies):
                if a:
                    sets = ",".join(f"{k}=:{k}" for k in vals)
                    db.execute(f"UPDATE assets SET {sets} WHERE id=:id", {**vals, "id": a["id"]})
                    new_id = a["id"]
                else:
                    row = dict(vals); row["created_by"] = g.user["id"]
                    cols = ",".join(row); ph = ",".join(":" + k for k in row)
                    cur = db.execute(f"INSERT INTO assets({cols}) VALUES({ph})", row)
                    new_id = cur.lastrowid
                if first_id is None:
                    first_id = new_id
                for label, val in [("Warranty", eff_warranty), ("Contract renewal", eff_renewal)]:
                    db.execute("DELETE FROM expiries WHERE entity='asset' AND entity_id=? AND label=? AND resolved=0",
                               (new_id, label))
                    if val:
                        thr = int(f.get("threshold_days") or THRESHOLD_DEFAULT)
                        db.execute("INSERT INTO expiries(entity,entity_id,label,due_date,threshold_days) VALUES('asset',?,?,?,?)",
                                   (new_id, label, val, thr))
            new_id = first_id
            # scan-first: promote the staged draft into a real attachment (first copy only)
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
            if not a and copies > 1:
                flash("Created %d identical assets." % copies)
                return redirect(url_for("assets_list"))
            return redirect(url_for("asset_view", aid=new_id))
    # ---- GET: render the cascading form ----
    exp = {}
    if a:
        for e in db.execute("SELECT * FROM expiries WHERE entity='asset' AND entity_id=? AND resolved=0", (a["id"],)):
            exp[e["label"]] = e
    draft = None
    if not a and request.args.get("draft", type=int):
        draft = draft_or_403(request.args.get("draft", type=int))
    py, pm = split_ym(a["purchase_date"]) if a else ("", "")
    cy, cm = split_ym(a["coverage_start"]) if (a and a["coverage_start"]) else (py, pm)
    ey, em = split_ym(a["emi_start"]) if (a and a["emi_start"]) else ("", "")
    return page(FORM_TEMPLATE,
        a=a, ents=entities_for_user(), zmap_json=Markup(_json.dumps(zones_by_entity())),
        cats=CATEGORIES, sts=STATUSES, cts=CONTRACT_TYPES, kinds=KINDS,
        periods=PERIODS, pay_methods=PAY_METHODS, months=MONTHS, years=year_choices(),
        vendors=pick("vendor"), providers=pick("provider"),
        accounts=sorted(set(pick("bank") + pick("card"))),
        banks_json=Markup(_json.dumps(pick("bank"))), cards_json=Markup(_json.dumps(pick("card"))),
        exp=exp, can_price=(a is None or can_see_price(a)), draft=draft,
        py=py, pm=pm, cy=cy, cm=cm, ey=ey, em=em, max_copies=MAX_COPIES,
        thr=(next(iter(exp.values()))["threshold_days"] if exp else THRESHOLD_DEFAULT))

@app.route("/assets/<int:aid>")
@login_required
def asset_view(aid):
    db = get_db()
    a = asset_or_403(aid)
    ent_name = zone_name = None
    if a["entity_id"]:
        _e = db.execute("SELECT name FROM entities WHERE id=?", (a["entity_id"],)).fetchone()
        ent_name = _e["name"] if _e else None
    if a["zone_id"]:
        _z = db.execute("SELECT name FROM zones WHERE id=?", (a["zone_id"],)).fetchone()
        zone_name = _z["name"] if _z else None
    show_price = can_see_price(a)
    exp = db.execute("SELECT * FROM expiries WHERE entity='asset' AND entity_id=? AND resolved=0 ORDER BY due_date",
                     (aid,)).fetchall()
    exp = [(e, *due_state(e["due_date"], e["threshold_days"])) for e in exp]
    logs = db.execute("""SELECT sl.*, u.display_name entered_by FROM service_logs sl
                         LEFT JOIN users u ON u.id=sl.created_by
                         WHERE asset_id=? ORDER BY log_date DESC""", (aid,)).fetchall()
    pm_done = db.execute("SELECT COUNT(*) FROM service_logs WHERE asset_id=? AND is_pm=1", (aid,)).fetchone()[0]
    parts = db.execute("""SELECT log_date, part_replaced, part_warranty, report_att_id
                          FROM service_logs WHERE asset_id=? AND part_replaced IS NOT NULL
                          AND TRIM(part_replaced)<>'' ORDER BY log_date DESC""", (aid,)).fetchall()
    att_sql = "SELECT at.*, u.display_name up_by FROM attachments at LEFT JOIN users u ON u.id=at.uploaded_by WHERE entity='asset' AND entity_id=?"
    if not show_price:
        att_sql += " AND sensitive=0"
    atts = db.execute(att_sql, (aid,)).fetchall()
    # A.4b: which referenced attachments are browser-renderable images (for thumbnails),
    # price-gated the same way the file itself is (sensitive images hidden unless show_price).
    ref_ids = {f["id"] for f in atts}
    for s in logs:
        if s["report_att_id"]:
            ref_ids.add(s["report_att_id"])
    for p in parts:
        if p["report_att_id"]:
            ref_ids.add(p["report_att_id"])
    img_ids = set()
    if ref_ids:
        q = "SELECT id,orig_name,sensitive FROM attachments WHERE id IN (%s)" % ",".join("?" * len(ref_ids))
        for row in db.execute(q, tuple(ref_ids)):
            if row["sensitive"] and not show_price:
                continue
            if is_image_name(row["orig_name"]):
                img_ids.add(row["id"])
    return page("""<p><a class="btn small" href="{{url_for('assets_list')}}">← Assets</a></p>
<h2>{{a['name']}}</h2>
<p><a class="btn small" href="{{url_for('asset_edit',aid=a['id'])}}">Edit</a>
{% if is_owner %}<form method=post action="{{url_for('asset_delete',aid=a['id'])}}" style="display:inline" onsubmit="return confirm('Delete asset and all its logs/files?')"><button class="btn small danger">Delete</button></form>{% endif %}</p>
<div class=grid>
<div class=card>{% if ent_name %}<b>Entity:</b> {{ent_name}}{% if zone_name %} / {{zone_name}}{% endif %}<br>{% endif %}<b>Location:</b> {{a['loc_name']}}<br><b>Category:</b> {{a['category']}}<br>
<b>Status:</b> {{a['status']}}<br><b>Serial:</b> {{a['serial_no'] or '—'}}<br>
<b>Purchased:</b> {{a['purchase_date'] or '—'}}
{% if show_price %}<br><b>Price:</b> ₹{{'%.0f'|format(a['price']) if a['price'] else '—'}}{% endif %}</div>
<div class=card><b>Vendor:</b> {{a['vendor'] or '—'}} {{a['vendor_phone'] or ''}}<br>
<b>Contract:</b> {{a['contract_type']}}{% if a['provider'] %} — {{a['provider']}}{% endif %}
{% if show_price and a['contract_cost'] %}<br><b>Contract cost:</b> ₹{{'%.0f'|format(a['contract_cost'])}}/yr{% endif %}
{% if a['contract_period'] and a['contract_period'] not in ('none','custom') %}<br><b>Coverage:</b> {{a['contract_period']}}{% endif %}
{% if a['pm_count'] %}<br><b>Preventive maint.:</b> {{pm_done}} of {{a['pm_count']}} done{% endif %}
{% if show_price and a['payment_method'] %}<br><b>Paid via:</b> {{a['payment_method']}}{% if a['pay_account'] %} ({{a['pay_account']}}){% endif %}{% if a['payment_method']=='Cheque' and a['pay_ref'] %} · no. {{a['pay_ref']}}{% if a['pay_date'] %} dt {{a['pay_date']}}{% endif %}{% endif %}{% if a['payment_method']=='UPI' and a['pay_ref'] %} · ref {{a['pay_ref']}}{% endif %}{% if a['emi'] %} · EMI {{a['emi_count']}}×{% if a['emi_amount'] %}₹{{'%.0f'|format(a['emi_amount'])}}{% endif %}{% if a['emi_end'] %} → {{a['emi_end'][:7]}}{% endif %}{% endif %}{% endif %}</div></div>
{% if a['notes'] %}<div class=card>{{a['notes']}}</div>{% endif %}
<div class=card><h4>Dates to watch</h4>{% if not exp %}<span class=muted>none set</span>{% endif %}
{% for e,state,days in exp %}<div>{{e['label']}}: <b>{{e['due_date']}}</b>
{% if state %}<span class="badge {{state}}">{{'overdue' if days<0 else (days|string)+'d'}}</span>{% endif %}</div>{% endfor %}</div>
{% if parts %}<div class=card><h4>Parts replaced</h4>
<table><tr><th>Part</th><th>Fitted</th><th>Warranty</th><th></th><th>Report</th></tr>
{% for p in parts %}<tr><td>{{p['part_replaced']}}</td><td>{{p['log_date']}}</td>
<td>{{p['part_warranty'] or '\u2014'}}</td>
<td>{% if p['part_warranty'] %}{% if p['part_warranty']>=tstr %}<span class="badge green">in warranty</span>{% else %}<span class="badge red">expired</span>{% endif %}{% endif %}</td>
<td>{% if p['report_att_id'] %}<a href="{{url_for('file_get',fid=p['report_att_id'])}}">\U0001F4C4 report</a>{% if p['report_att_id'] in img_ids %}<br><a href="{{url_for('file_get',fid=p['report_att_id'])}}"><img src="{{url_for('file_get',fid=p['report_att_id'])}}" loading=lazy alt="" style="max-height:44px;max-width:80px;border:1px solid #e4e9ef;border-radius:5px;margin-top:3px"></a>{% endif %}{% endif %}</td></tr>{% endfor %}</table></div>{% endif %}
<div class=card><h4>Files</h4>
<p><a class="btn small" href="{{url_for('scan_page',entity='asset',eid=a['id'])}}">📷 Scan document</a></p>
{% for f in atts %}<div style="margin-bottom:6px">📄 <a href="{{url_for('file_get',fid=f['id'])}}">{{f['orig_name']}}</a>
{% if img_ids is defined and f['id'] in img_ids %}<a href="{{url_for('file_get',fid=f['id'])}}"><img src="{{url_for('file_get',fid=f['id'])}}" loading=lazy alt="" style="display:block;max-height:70px;max-width:130px;border:1px solid #e4e9ef;border-radius:6px;margin:4px 0"></a>{% endif %}
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
{% for s in logs %}<tr><td>{{s['log_date']}}</td><td>{{s['work']}}{% if s['is_pm'] %} <span class="badge amber">PM</span>{% elif s['svc_type']=='Repair' %} <span class="badge red">Repair</span>{% endif %}{% if s['part_replaced'] %}<br><span class=muted>part: {{s['part_replaced']}}{% if s['part_warranty'] %} · warranty {{s['part_warranty']}}{% endif %}</span>{% endif %}{% if s['report_att_id'] %} <a class=muted href="{{url_for('file_get',fid=s['report_att_id'])}}">\U0001F4C4 report</a>{% if s['report_att_id'] in img_ids %} <a href="{{url_for('file_get',fid=s['report_att_id'])}}"><img src="{{url_for('file_get',fid=s['report_att_id'])}}" loading=lazy alt="" style="max-height:40px;max-width:70px;border:1px solid #e4e9ef;border-radius:5px;vertical-align:middle;margin-left:4px"></a>{% endif %}{% endif %}</td>
{% if show_price %}<td>{{'₹%.0f'|format(s['cost']) if s['cost'] else ''}}</td>{% endif %}
<td>{{s['done_by'] or ''}}</td><td>{{s['next_due'] or ''}}</td><td class=muted>{{s['entered_by']}}</td></tr>{% endfor %}</table>
<form method=post enctype=multipart/form-data action="{{url_for('service_add',aid=a['id'])}}" onsubmit="return svcConfirm()">
<label>Date</label><input type=date name=log_date value="{{today}}" required>
<label>Type of visit</label>
<select name=svc_type id=svctype onchange="svcTypeChange()">
<option>Preventive maintenance</option><option>Repair</option><option>Other service</option></select>
<div class=muted id=pmnote>Preventive maintenance is covered under the AMC — no charge.</div>
<label id=worklabel>Work done / observations</label><input name=work id=workinput required placeholder="what was done">
<label>Report / bill (scan or file, optional)</label><input type=file name=report accept="image/*,.pdf,.doc,.docx" style="max-width:260px">
<div id=svccostwrap><label>Cost (₹)</label><input type=number step=0.01 name=cost id=svccost></div>
<label>Part replaced <span class=muted>(optional)</span></label><input name=part_replaced placeholder="e.g. X-ray tube, battery">
<label>Part warranty <span class=muted>(the replaced part’s own warranty)</span></label>
<select name=part_warranty_period><option value=none>(none)</option><option value=6mo>6 months</option><option value=1yr>1 year</option><option value=2yr>2 years</option><option value=3yr>3 years</option><option value=5yr>5 years</option></select>
<label>Done by</label><input name=done_by>
<label>Next service due</label><input type=date name=next_due>
<br><button class="btn small">Add entry</button></form>
<script>
function svcTypeChange(){
  var el=document.getElementById('svctype'); if(!el) return; var v=el.value, pm=(v=='Preventive maintenance');
  var cw=document.getElementById('svccostwrap'), note=document.getElementById('pmnote');
  if(cw) cw.style.display=pm?'none':'block';
  if(note) note.style.display=pm?'block':'none';
  var wl=document.getElementById('worklabel'), wi=document.getElementById('workinput');
  if(wl){ wl.textContent = pm ? 'Work done / observations' : (v=='Repair' ? 'Issue / fault & work done' : 'Work done'); }
  if(wi){ wi.placeholder = pm ? 'e.g. routine check, cleaned, calibrated' : (v=='Repair' ? 'e.g. tube failed - replaced, tested' : 'what was done'); }
}
svcTypeChange();
function svcConfirm(){
  var c=document.getElementById('svccost');
  if(c && c.value && parseFloat(c.value)>0){
    return confirm('Save this service entry with a cost of \u20b9'+c.value+'?');
  }
  return true;
}
</script></div>""",
        a=a, exp=exp, logs=logs, atts=atts, show_price=show_price, pm_done=pm_done, img_ids=img_ids,
        parts=parts, tstr=today().isoformat(),
        ent_name=ent_name, zone_name=zone_name, today=today().isoformat())

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
    db = get_db()
    log_date = f.get("log_date") or today().isoformat()
    svc_type = f.get("svc_type") or ("Preventive maintenance" if f.get("is_pm") else "Repair")
    is_pm = 1 if svc_type == "Preventive maintenance" else 0
    # PM is part of the AMC -> never carries a cost
    cost = None if is_pm else (float(f["cost"]) if f.get("cost") else None)
    part = (f.get("part_replaced") or "").strip() or None
    pwp = f.get("part_warranty_period") or "none"
    part_warranty = add_months(log_date, PERIOD_MONTHS[pwp]) if (part and pwp in PERIOD_MONTHS) else None
    cur = db.execute("""INSERT INTO service_logs(asset_id,log_date,work,cost,done_by,next_due,is_pm,
                  svc_type,part_replaced,part_warranty,created_by)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
               (aid, log_date, f.get("work", "").strip(), cost,
                f.get("done_by") or None, f.get("next_due") or None, is_pm,
                svc_type, part, part_warranty, g.user["id"]))
    slid = cur.lastrowid
    # a replaced part with its own warranty -> its own reminder on the asset
    if part and part_warranty:
        db.execute("""INSERT INTO expiries(entity,entity_id,label,due_date,threshold_days)
                      VALUES('asset',?,?,?,?)""",
                   (aid, "Part warranty: " + part, part_warranty, THRESHOLD_DEFAULT))
    # optional: attach the report/bill as an asset attachment (reuses the tested path)
    fobj = request.files.get("report")
    if fobj and fobj.filename and "." in fobj.filename:
        ext = fobj.filename.rsplit(".", 1)[1].lower()
        if ext in ALLOWED_EXT:
            stored = "asset%d_%s.%s" % (aid, secrets.token_hex(8), ext)
            fobj.save(os.path.join(UPLOAD_DIR, stored))
            tag = "PM report " if is_pm else "Service report "
            oname = secure_filename(tag + log_date + "." + ext)
            _, st = digitise_document(os.path.join(UPLOAD_DIR, stored), ext)
            acur = db.execute("""INSERT INTO attachments(entity,entity_id,stored_name,orig_name,
                          sensitive,ocr_status,uploaded_by) VALUES('asset',?,?,?,?,?,?)""",
                       (aid, stored, oname, 1 if a["hide_price"] else 0, st, g.user["id"]))
            db.execute("UPDATE service_logs SET report_att_id=? WHERE id=?", (acur.lastrowid, slid))
    db.commit()
    flash("Service entry saved.")
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
    return page("""<p><a class="btn small" href="{{url_for('staff_list')}}">← Staff</a></p>
<h2>{{s['name']}} <span class=muted>{{s['role_title'] or ''}}</span></h2>
<p><a class="btn small" href="{{url_for('staff_edit',sid=s['id'])}}">Edit</a></p>
<div class=card><b>Phone:</b> {{s['phone'] or '—'}}<br><b>Joined:</b> {{s['joined_date'] or '—'}}<br>
<b>Status:</b> {{s['status']}}{% if s['notes'] %}<br>{{s['notes']}}{% endif %}</div>
<div class=card><h4>Dates to watch</h4>{% if not exp %}<span class=muted>none</span>{% endif %}
{% for e,state,days in exp %}<div>{{e['label']}}: <b>{{e['due_date']}}</b>
{% if state %}<span class="badge {{state}}">{{'overdue' if days<0 else (days|string)+'d'}}</span>{% endif %}</div>{% endfor %}</div>
<div class=card><h4>Documents</h4>
<p><a class="btn small" href="{{url_for('scan_page',entity='staff',eid=s['id'])}}">📷 Scan document</a></p>
{% for f in atts %}<div style="margin-bottom:6px">📄 <a href="{{url_for('file_get',fid=f['id'])}}">{{f['orig_name']}}</a>
{% if img_ids is defined and f['id'] in img_ids %}<a href="{{url_for('file_get',fid=f['id'])}}"><img src="{{url_for('file_get',fid=f['id'])}}" loading=lazy alt="" style="display:block;max-height:70px;max-width:130px;border:1px solid #e4e9ef;border-radius:6px;margin:4px 0"></a>{% endif %}
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

# ---------------------------------------------------------------- Phase D: purchase ledger
def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None

@app.route("/bills")
@owner_required
def bills_list():
    db = get_db()
    q = request.args.get("q", "").strip()
    fk = request.args.get("kind", "").strip()
    where, params = "1=1", []
    if q:
        where += (" AND (b.vendor LIKE ? OR b.bill_no LIKE ? OR EXISTS("
                  "SELECT 1 FROM bill_items bi WHERE bi.bill_id=b.id AND bi.item_name LIKE ?))")
        params += ["%" + q + "%"] * 3
    if fk in ("Asset", "Consumable"):
        where += " AND b.kind=?"
        params.append(fk)
    bills = db.execute(
        "SELECT b.*, u.display_name entered_by, "
        "(SELECT COUNT(*) FROM bill_items bi WHERE bi.bill_id=b.id) nitems "
        "FROM bills b LEFT JOIN users u ON u.id=b.created_by "
        "WHERE " + where + " ORDER BY b.bill_date DESC, b.id DESC LIMIT 300", params).fetchall()
    return page("""<h2>Purchases</h2>
<form method=get style="margin-bottom:10px">
<input name=q value="{{q}}" placeholder="vendor / bill no / item" style="max-width:230px">
<select name=kind onchange="this.form.submit()" style="width:auto;max-width:150px"><option value="">Kind: all</option><option {{'selected' if fk=='Consumable'}}>Consumable</option><option {{'selected' if fk=='Asset'}}>Asset</option></select>
<button class="btn small">Search</button>{% if q or fk %} <a class="btn small" href="{{url_for('bills_list')}}">clear</a>{% endif %}</form>
<p><a class=btn href="{{url_for('bill_new')}}">+ New bill</a>
<a class="btn small" href="{{url_for('purchases')}}">\U0001F4C8 Consumption &amp; rate history</a></p>
<table><tr><th>Date</th><th>Vendor</th><th>Bill no</th><th>Kind</th><th>Items</th><th>Total</th></tr>
{% for b in bills %}<tr><td>{{b['bill_date'] or '\u2014'}}</td>
<td><a href="{{url_for('bill_view',bid=b['id'])}}">{{b['vendor'] or '(no vendor)'}}</a></td>
<td>{{b['bill_no'] or '\u2014'}}</td><td>{{b['kind']}}</td><td>{{b['nitems']}}</td>
<td>{{'\u20b9%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '\u2014'}}</td></tr>{% endfor %}</table>
{% if not bills %}<p class=muted>No bills{{' match' if q or fk else ' yet'}}. Add one with \u201c+ New bill\u201d.</p>{% endif %}""",
        bills=bills, q=q, fk=fk)

BILLFORM_TPL = """<h2>New bill</h2>
<p><a class="btn small" href="{{url_for('bills_list')}}">← Purchases</a></p>
<div class=card><h4>Auto-fill from a scanned bill</h4>
<p class=muted>{% if sarvam_on %}Upload a bill image/PDF — Sarvam reads it and pre-fills the form below for you to check.{% else %}Sarvam OCR isn't configured yet, so this attaches the scan and you fill the form. (Set SARVAM_API_KEY + install sarvamai to enable auto-read.){% endif %}</p>
<form method=post action="{{url_for('bill_extract')}}" enctype=multipart/form-data>
<input type=file name=bill accept="image/*,.pdf" required style="max-width:260px">
<button class="btn small">Read bill</button></form></div>
<form method=post>
<input type=hidden name=src_stored value="{{src.get('stored','')}}">
<input type=hidden name=src_orig value="{{src.get('orig','')}}">
<div class=card>
<label>Kind</label><select name=kind style="width:auto"><option {{'selected' if hdr.get('kind')!='Asset'}}>Consumable</option><option {{'selected' if hdr.get('kind')=='Asset'}}>Asset</option></select>
<label>Vendor</label><input name=vendor list=vendorlist value="{{hdr.get('vendor','')}}" placeholder="supplier">
<datalist id=vendorlist>{% for v in vendors %}<option value="{{v}}">{% endfor %}</datalist>
<label>Bill no</label><input name=bill_no value="{{hdr.get('bill_no','')}}">
<label>Bill date</label><input name=bill_date value="{{hdr.get('bill_date') or today}}" placeholder="YYYY-MM-DD">
<label>Bill total (₹)</label><input type=number step=any name=total_amount value="{{hdr.get('total_amount','')}}">
<label>Notes</label><input name=notes value="{{hdr.get('notes','')}}">
{% if src.get('stored') %}<p class=muted>Scan attached: {{src.get('orig','')}}</p>{% endif %}</div>
<div class=card><h4>Items</h4>
<p class=muted>One block per line item; blank blocks are ignored. Consumables use pack / batch / expiry, assets use make / model / serial.</p>
<div id=items>
{% for it in items %}<div class="card litem" style="padding:10px;background:#f7f9fc">
<input name=it_name value="{{it.get('name','')}}" placeholder="item name" style="max-width:220px">
<input name=it_pack value="{{it.get('pack','')}}" placeholder="pack size" style="max-width:130px">
<input name=it_qty type=number step=any value="{{it.get('qty','')}}" placeholder="qty" style="max-width:80px">
<input name=it_rate type=number step=any value="{{it.get('rate','')}}" placeholder="rate" style="max-width:100px">
<input name=it_amount type=number step=any value="{{it.get('amount','')}}" placeholder="amount" style="max-width:110px">
<br><span class=muted>optional —</span>
<input name=it_make value="{{it.get('make','')}}" placeholder="make" style="max-width:110px">
<input name=it_model value="{{it.get('model','')}}" placeholder="model" style="max-width:110px">
<input name=it_serial value="{{it.get('serial','')}}" placeholder="serial" style="max-width:130px">
<input name=it_batch value="{{it.get('batch','')}}" placeholder="batch" style="max-width:110px">
<input name=it_expiry value="{{it.get('expiry','')}}" placeholder="expiry YYYY-MM-DD" style="max-width:150px">
<input name=it_hsn value="{{it.get('hsn','')}}" placeholder="HSN" style="max-width:90px">
</div>{% endfor %}
</div>
<button type=button class="btn small" onclick="addItem()">+ add item</button></div>
<button class="btn">Save bill</button></form>
<script>
function addItem(){
  var box=document.getElementById('items');
  var c=box.querySelector('.litem').cloneNode(true);
  c.querySelectorAll('input').forEach(function(i){i.value='';});
  box.appendChild(c);
}
</script>"""

def _map_bill(data):
    """Tolerantly map a Sarvam extract() result into (hdr, items) for the form.
    Shapes vary, so we probe common key names and never raise."""
    hdr, items = {}, []
    def _cln(v):
        # collapse all whitespace (incl. embedded newlines) to single spaces
        return " ".join(str(v).split()) if v not in (None, "") else ""
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return hdr, items
    for wrap in ("result", "fields", "data", "extraction"):
        if isinstance(data.get(wrap), dict):
            data = data[wrap]
            break
    def g(*keys):
        for k in keys:
            v = data.get(k)
            if v not in (None, ""):
                return v
        return ""
    hdr["vendor"] = _cln(g("vendor", "supplier", "seller", "vendor_name"))
    hdr["bill_no"] = _cln(g("bill_no", "invoice_no", "invoice_number", "bill_number"))
    hdr["bill_date"] = _cln(g("bill_date", "invoice_date", "date"))
    ta = g("total_amount", "total", "grand_total", "amount")
    hdr["total_amount"] = _cln(ta)
    raw = data.get("items") or data.get("line_items") or data.get("lines") or []
    if isinstance(raw, dict):
        raw = [raw]
    for it in (raw if isinstance(raw, list) else []):
        if not isinstance(it, dict):
            continue
        def gi(*keys):
            for k in keys:
                v = it.get(k)
                if v not in (None, ""):
                    return v
            return ""
        items.append({
            "name": _cln(gi("item_name", "name", "description", "item")),
            "pack": _cln(gi("pack_size", "pack", "unit")),
            "qty": _cln(gi("quantity", "qty")),
            "rate": _cln(gi("rate", "unit_rate", "price")),
            "amount": _cln(gi("amount", "total", "value", "line_total")),
            "make": _cln(gi("make", "brand")),
            "model": _cln(gi("model")),
            "serial": _cln(gi("serial_no", "serial")),
            "batch": _cln(gi("batch", "lot")),
            "expiry": _cln(gi("expiry", "expiry_date")),
            "hsn": _cln(gi("hsn", "hsn_sac", "sac")),
        })
    return hdr, items

def _sarvam_on():
    return bool(SARVAM is not None and getattr(SARVAM, "available", lambda: False)())

def _bill_form_page(hdr=None, items=None, src=None):
    items = list(items or [])
    while len(items) < 3:
        items.append({})
    vendors = [r["value"] for r in get_db().execute(
        "SELECT value FROM pick_lists WHERE kind='vendor' AND active=1 ORDER BY value")]
    return page(BILLFORM_TPL, hdr=(hdr or {}), items=items, src=(src or {}),
                vendors=vendors, today=today().isoformat(), sarvam_on=_sarvam_on())

def _save_bill_items(db, bid, f):
    cols = ["it_name", "it_pack", "it_qty", "it_rate", "it_amount", "it_make",
            "it_model", "it_serial", "it_batch", "it_expiry", "it_hsn"]
    lists = {c: f.getlist(c) for c in cols}
    def at(c, i):
        v = lists[c]
        return (v[i].strip() if (i < len(v) and v[i] is not None) else "")
    n = 0
    for i in range(len(lists["it_name"])):
        nm = at("it_name", i)
        if not nm:
            continue
        db.execute(
            "INSERT INTO bill_items(bill_id,item_name,pack_size,quantity,rate,amount,"
            "make,model,serial_no,batch,expiry,hsn) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (bid, nm, at("it_pack", i) or None, _num(at("it_qty", i)), _num(at("it_rate", i)),
             _num(at("it_amount", i)), at("it_make", i) or None, at("it_model", i) or None,
             at("it_serial", i) or None, at("it_batch", i) or None,
             at("it_expiry", i) or None, at("it_hsn", i) or None))
        n += 1
    return n

@app.route("/bills/new", methods=["GET", "POST"])
@owner_required
def bill_new():
    db = get_db()
    if request.method == "POST":
        f = request.form
        kind = f.get("kind") if f.get("kind") in ("Asset", "Consumable") else "Consumable"
        cur = db.execute(
            "INSERT INTO bills(kind,vendor,bill_no,bill_date,total_amount,notes,"
            "source_stored,source_orig,created_by) VALUES(?,?,?,?,?,?,?,?,?)",
            (kind, (f.get("vendor") or "").strip() or None, (f.get("bill_no") or "").strip() or None,
             f.get("bill_date") or None, _num(f.get("total_amount")),
             (f.get("notes") or "").strip() or None,
             (f.get("src_stored") or "").strip() or None, (f.get("src_orig") or "").strip() or None,
             g.user["id"]))
        bid = cur.lastrowid
        n = _save_bill_items(db, bid, f)
        db.commit()
        flash("Bill saved with %d line item(s)." % n)
        return redirect(url_for("bill_view", bid=bid))
    return _bill_form_page()

@app.route("/bills/extract", methods=["POST"])
@owner_required
def bill_extract():
    fobj = request.files.get("bill")
    if not (fobj and fobj.filename and "." in fobj.filename):
        flash("No file to read.")
        return redirect(url_for("bill_new"))
    ext = fobj.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        flash("File type not allowed.")
        return redirect(url_for("bill_new"))
    stored = "bill_%s.%s" % (secrets.token_hex(8), ext)
    fobj.save(os.path.join(UPLOAD_DIR, stored))
    src = {"stored": stored, "orig": secure_filename(fobj.filename)}
    hdr, items = {}, []
    if _sarvam_on():
        data, st = SARVAM.extract(os.path.join(UPLOAD_DIR, stored))
        if st == "done" and data is not None:
            hdr, items = _map_bill(data)
            flash("Auto-filled from the scan — please review and correct before saving.")
        else:
            flash("Couldn't read the bill automatically — enter it manually. The scan is attached.")
    else:
        flash("Sarvam OCR isn't configured — enter the bill manually. The scan is attached.")
    return _bill_form_page(hdr, items, src)

@app.route("/bills/<int:bid>/file")
@owner_required
def bill_file(bid):
    b = get_db().execute("SELECT source_stored, source_orig FROM bills WHERE id=?", (bid,)).fetchone()
    if not b or not b["source_stored"]:
        abort(404)
    path = os.path.join(UPLOAD_DIR, b["source_stored"])
    if not os.path.exists(path):
        abort(404)
    return send_file(path, download_name=b["source_orig"] or "bill",
                     mimetype=mimetypes.guess_type(b["source_orig"] or "")[0] or "application/octet-stream")

@app.route("/bills/<int:bid>")
@owner_required
def bill_view(bid):
    db = get_db()
    b = db.execute("SELECT b.*, u.display_name entered_by FROM bills b "
                   "LEFT JOIN users u ON u.id=b.created_by WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    items = db.execute("SELECT * FROM bill_items WHERE bill_id=? ORDER BY id", (bid,)).fetchall()
    return page("""<h2>Bill <span class=muted>{{b['bill_no'] or ''}}</span></h2>
<p><a class="btn small" href="{{url_for('bills_list')}}">← Purchases</a>
<form method=post action="{{url_for('bill_delete',bid=b['id'])}}" style="display:inline" onsubmit="return confirm('Delete this bill and all its items?')"><button class="btn small danger">Delete</button></form></p>
<div class=grid>
<div class=card><b>Vendor:</b> {{b['vendor'] or '—'}}<br><b>Bill no:</b> {{b['bill_no'] or '—'}}<br>
<b>Date:</b> {{b['bill_date'] or '—'}}<br><b>Kind:</b> {{b['kind']}}<br>
<b>Total:</b> {{'₹%.2f'|format(b['total_amount']) if b['total_amount'] is not none else '—'}}</div>
<div class=card>{% if b['notes'] %}{{b['notes']}}<br>{% endif %}<span class=muted>entered by {{b['entered_by']}} {{b['created_at'][:10]}}</span>
{% if b['source_stored'] %}<br>📄 <a href="{{url_for('bill_file',bid=b['id'])}}">{{b['source_orig'] or 'scanned bill'}}</a>{% endif %}</div></div>
<div class=card><h4>Items</h4>
<table><tr><th>Item</th><th>Pack</th><th>Qty</th><th>Rate</th><th>Amount</th><th>Details</th></tr>
{% for it in items %}<tr><td><a href="{{url_for('purchases')}}?item={{it['item_name']|urlencode}}">{{it['item_name']}}</a></td>
<td>{{it['pack_size'] or '—'}}</td><td>{{it['quantity'] if it['quantity'] is not none else '—'}}</td>
<td>{{'₹%.2f'|format(it['rate']) if it['rate'] is not none else '—'}}</td>
<td>{{'₹%.2f'|format(it['amount']) if it['amount'] is not none else '—'}}</td>
<td class=muted>{% if it['make'] %}{{it['make']}} {% endif %}{% if it['model'] %}{{it['model']}} {% endif %}{% if it['serial_no'] %}· s/n {{it['serial_no']}} {% endif %}{% if it['batch'] %}· batch {{it['batch']}} {% endif %}{% if it['expiry'] %}· exp {{it['expiry']}}{% endif %}{% if it['hsn'] %} · HSN {{it['hsn']}}{% endif %}</td></tr>{% endfor %}</table>
{% if not items %}<p class=muted>No line items on this bill.</p>{% endif %}</div>""",
        b=b, items=items)

@app.route("/bills/<int:bid>/delete", methods=["POST"])
@owner_required
def bill_delete(bid):
    db = get_db()
    db.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,))
    db.execute("DELETE FROM bills WHERE id=?", (bid,))
    db.commit()
    flash("Bill deleted.")
    return redirect(url_for("bills_list"))

@app.route("/purchases")
@owner_required
def purchases():
    db = get_db()
    item = request.args.get("item", "").strip()
    soon = []
    for r in db.execute("SELECT bi.item_name, bi.batch, bi.expiry, b.vendor FROM bill_items bi "
                        "JOIN bills b ON b.id=bi.bill_id WHERE bi.expiry IS NOT NULL AND bi.expiry<>'' "
                        "ORDER BY bi.expiry"):
        st, days = due_state(r["expiry"], THRESHOLD_DEFAULT)
        if st:
            soon.append((r, st, days))
    if item:
        rows = db.execute("SELECT bi.*, b.vendor, b.bill_date, b.bill_no FROM bill_items bi "
                          "JOIN bills b ON b.id=bi.bill_id WHERE bi.item_name=? "
                          "ORDER BY b.bill_date, bi.id", (item,)).fetchall()
        rate_series = [r["rate"] for r in rows if r["rate"] is not None]
        drift = None
        if len(rate_series) >= 2 and rate_series[0]:
            first, last = rate_series[0], rate_series[-1]
            drift = (first, last, (last - first) / first * 100.0)
        frm = request.args.get("from", "").strip() or None
        to = request.args.get("to", "").strip() or None
        csql = ("SELECT COALESCE(SUM(bi.quantity),0) qty, COUNT(*) n FROM bill_items bi "
                "JOIN bills b ON b.id=bi.bill_id WHERE bi.item_name=?")
        cp = [item]
        if frm:
            csql += " AND b.bill_date>=?"; cp.append(frm)
        if to:
            csql += " AND b.bill_date<=?"; cp.append(to)
        cons = db.execute(csql, cp).fetchone()
        return page("""<h2>{{item}}</h2>
<p><a class="btn small" href="{{url_for('purchases')}}">\u2190 All items</a></p>
<div class=card><h4>Rate history <span class=muted>(rate drift over time)</span></h4>
<table><tr><th>Date</th><th>Vendor</th><th>Pack</th><th>Qty</th><th>Rate</th><th>Amount</th></tr>
{% for r in rows %}<tr><td>{{r['bill_date'] or '\u2014'}}</td><td>{{r['vendor'] or '\u2014'}}</td>
<td>{{r['pack_size'] or '\u2014'}}</td><td>{{r['quantity'] if r['quantity'] is not none else '\u2014'}}</td>
<td>{{'\u20b9%.2f'|format(r['rate']) if r['rate'] is not none else '\u2014'}}</td>
<td>{{'\u20b9%.2f'|format(r['amount']) if r['amount'] is not none else '\u2014'}}</td></tr>{% endfor %}</table>
{% if drift %}<p class=muted>First recorded \u20b9{{'%.2f'|format(drift[0])}} \u2192 latest \u20b9{{'%.2f'|format(drift[1])}} ({{'%+.1f'|format(drift[2])}}%).</p>{% endif %}</div>
<div class=card><h4>Consumption</h4>
<form method=get style="margin-bottom:8px"><input type=hidden name=item value="{{item}}">
<label style="display:inline">From</label> <input type=date name=from value="{{frm or ''}}" style="width:auto">
<label style="display:inline">To</label> <input type=date name=to value="{{to or ''}}" style="width:auto">
<button class="btn small">Apply</button></form>
<p><b>{{'%g'|format(cons['qty'])}}</b> total quantity across <b>{{cons['n']}}</b> purchase(s){% if frm or to %} in range{% endif %}.</p></div>""",
            item=item, rows=rows, drift=drift, cons=cons, frm=frm, to=to)
    items = db.execute(
        "SELECT bi.item_name name, COUNT(*) buys, COALESCE(SUM(bi.quantity),0) tot_qty, "
        "(SELECT bi2.rate FROM bill_items bi2 JOIN bills b2 ON b2.id=bi2.bill_id "
        " WHERE bi2.item_name=bi.item_name ORDER BY b2.bill_date DESC, bi2.id DESC LIMIT 1) last_rate, "
        "MAX(b.bill_date) last_date FROM bill_items bi JOIN bills b ON b.id=bi.bill_id "
        "GROUP BY bi.item_name ORDER BY last_date DESC").fetchall()
    return page("""<h2>Consumption &amp; rate history</h2>
<p><a class="btn small" href="{{url_for('bills_list')}}">\u2190 Purchases</a></p>
{% if soon %}<div class=card><h4>Expiring soon</h4>
<table><tr><th>Item</th><th>Batch</th><th>Expiry</th><th></th><th>Vendor</th></tr>
{% for r,st,days in soon %}<tr><td>{{r['item_name']}}</td><td>{{r['batch'] or '\u2014'}}</td>
<td>{{r['expiry']}}</td><td><span class="badge {{st}}">{{'expired' if days<0 else (days|string)+'d'}}</span></td>
<td>{{r['vendor'] or '\u2014'}}</td></tr>{% endfor %}</table></div>{% endif %}
<div class=card><h4>Items purchased</h4>
<table><tr><th>Item</th><th>Buys</th><th>Total qty</th><th>Last rate</th><th>Last bought</th></tr>
{% for it in items %}<tr><td><a href="{{url_for('purchases')}}?item={{it['name']|urlencode}}">{{it['name']}}</a></td>
<td>{{it['buys']}}</td><td>{{'%g'|format(it['tot_qty'])}}</td>
<td>{{'\u20b9%.2f'|format(it['last_rate']) if it['last_rate'] is not none else '\u2014'}}</td>
<td>{{it['last_date'] or '\u2014'}}</td></tr>{% endfor %}</table>
{% if not items %}<p class=muted>No line items yet. Add a bill to start tracking consumption and rate drift.</p>{% endif %}</div>""",
        soon=soon, items=items)

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
        elif act == "add_pick" and request.form.get("value", "").strip():
            _k = request.form.get("pl_kind")
            if _k in ("vendor", "provider", "bank", "card"):
                db.execute("INSERT OR IGNORE INTO pick_lists(kind,value,sort) VALUES(?,?,0)",
                           (_k, request.form["value"].strip()))
        elif act == "del_pick":
            db.execute("UPDATE pick_lists SET active=0 WHERE id=?",
                       (request.form.get("pid", type=int),))
        elif act == "set_palette":
            _p = request.form.get("palette", "")
            if _p in PALETTES:
                db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('palette',?)", (_p,))
        db.commit()
        return redirect(url_for("admin"))
    users = db.execute("SELECT id,username,display_name,role FROM users").fetchall()
    locs = db.execute("SELECT * FROM locations").fetchall()
    return page("""<h2>Admin</h2>
<div class=card><h4>Screen background</h4>
<p class=muted>A comfortable, low-glare background. Applies to everyone; takes effect on the next page load.</p>
<form method=post><input type=hidden name=action value=set_palette>
{% for k,meta in palettes.items() %}<label style="display:inline-flex;align-items:center;gap:6px;margin-right:16px;margin-top:0">
<input type=radio name=palette value="{{k}}" style="width:auto" {{'checked' if k==cur_palette}}>
<span style="display:inline-block;width:16px;height:16px;border:1px solid #cfd8e3;border-radius:3px;background:{{meta[1]}}"></span> {{meta[0]}}</label>{% endfor %}
<br><button class="btn small">Apply</button></form></div>
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
<div class=card><h4>Managed lists (form dropdowns)</h4>
<p class=muted>Vendors, service providers, banks and cards offered in the asset form. Add here, or type a new one while filling the form and it is remembered.</p>
{% for k,label in [('vendor','Vendors'),('provider','Providers'),('bank','Banks'),('card','Cards')] %}
<div style="margin-bottom:8px"><b>{{label}}:</b>
{% for p in picks[k] %}<span style="display:inline-block;background:#e8edf7;border-radius:9px;padding:1px 4px 1px 8px;margin:2px">{{p['value']}}
<form method=post style="display:inline"><input type=hidden name=action value=del_pick><input type=hidden name=pid value={{p['id']}}><button class="btn small danger" style="padding:0 6px;margin-left:2px" onclick="return confirm('Remove {{p['value']}} from {{label}}?')">×</button></form></span>{% endfor %}
<form method=post style="margin-top:4px"><input type=hidden name=action value=add_pick><input type=hidden name=pl_kind value={{k}}>
<input name=value placeholder="add…" style="max-width:170px"><button class="btn small">Add</button></form></div>{% endfor %}</div>
<div class=card><h4>Drafts</h4><p><b>{{ndrafts}}</b> scanned document(s) waiting to be filed.
<a class="btn small" href="{{url_for('drafts_list')}}">Open drafts</a></p>
<p class=muted>Drafts never expire and are never auto-deleted.</p></div>""",
        users=users, locs=locs, token=setting("api_token"),
        ocr=db.execute("SELECT ocr_status, COUNT(*) FROM attachments GROUP BY ocr_status").fetchall(),
        ndrafts=db.execute("SELECT COUNT(*) FROM drafts").fetchone()[0],
        picks={_k: db.execute("SELECT id,value FROM pick_lists WHERE kind=? AND active=1 ORDER BY sort,value", (_k,)).fetchall() for _k in ('vendor','provider','bank','card')},
        palettes=PALETTES, cur_palette=setting_or("palette", DEFAULT_PALETTE),
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
