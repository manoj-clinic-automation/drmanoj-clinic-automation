#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s585.py -- the S585_STATIONERY_ISSUE_MANY walk. The app with the given files on a COPY of a database (SQLite's backup API), in
its own scratch folder; made-up rows only: stationery items 'WALK585 .. 2031' (one retired), their opening counts, made-up logins
(walk_own_2031 / walk_mgr_2031, made here; a reception user stood in for by the walk); today frozen at 15-Jun-2031; no reader thread,
no paid call, nothing sent anywhere. Flask's test client; no port. Every row the walk checks is found by its key (the item's id, the
move's id), never by counting a table; the live items on the copy are only read (their names and stock, for "every active item").
The data step is walked on SCHEMA copies (the tables' own CREATE statements, no live row) holding made-up items of the seven exact names.

    python3 -B walk_s585.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js, stationery.py, batteries.py, xray_costs.py> <assets.db to copy>
                            --from <dir with the FROM files> [--work DIR] [--shared DIR] [--expect-red] [--keep] [--save-pages DIR]

Checks: W1 (structural) the app imports from the scratch folder; W2 the S585 mark; M1-M9 one per item of the brief's walk list (s5):
M1 switch OFF = byte-identical one-item screen (FROM and TO each in a fresh process; ON, the TO page is the new screen) · M2 switch ON
shows every active item with its stock (the switch on the owner's Stationery page) · M3 one save of three items = three moves in one
transaction; a forced failure on the third writes none · M4 no Kisko / no number = nothing written; OFF = refused · M5 X-ray a place,
on the owner's table · M6 Void by the owner leaves the stock arithmetic; a manager has no Void, a forged POST is refused · M7 the data
step: 7 rows before the opening counts, the stock unchanged, a second run writes nothing, an item without an opening count skipped,
a changed stock rolls back; the sheet's lines in their own fold, never "this month" · M8 ?one=1 still works · M9 the staff page under
100 KB and 2 s. (390 px and 1366 x 768: walk/browser_many_s585.py on the PC; the installer's refusals: rehearse_s585.sh.)
--expect-red (the control, on the FROM files): exit 0 only if every check in MUST_RED is RED (W1 structural: green on both)."""
import datetime, html as htmlmod, importlib.util, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.realpath(p or os.getcwd()) != HERE]   # never import from the kit's own folder
ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9")
TODAY = datetime.date(2031, 6, 15)
YM = "2031-06"
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js", "stationery.py", "batteries.py", "xray_costs.py")
SEVEN = ("Register 72 pages", "Register 104 pages", "Register 192 pages", "Small notebook (copy)", "Notebook (copy) 72 pages")
HIST_BY = "history (Shavez sheet)"


def opt(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = ""
        if not ok and detail:
            try:
                d = detail()
            except Exception as e:                                         # noqa: BLE001
                d = repr(e)
    except Exception as e:                                                 # noqa: BLE001
        ok, d = False, repr(e)
    R.append(ok)
    NAMES.append(name.split(" ")[0])
    if not ok:
        FAILED.append(name.split(" ")[0])
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:1500]) if (d and not ok) else ""))
    return ok


def quiet(fn, default=None):
    try:
        return fn()
    except Exception as e:                                                 # noqa: BLE001
        print("  (step failed: %s)" % repr(e)[:240])
        return default


def setup_env(work):
    app = os.path.join(work, "app")
    return {"ASSETS_DB": os.path.join(work, "assets.db"), "ASSETS_UPLOADS": os.path.join(work, "uploads"),
            "SCANAPP_ANTHROPIC_KEY_FILE": os.path.join(work, "key", "anthropic.key"),
            "SCANAPP_ANTHROPIC_URL": "https://made-up.invalid/v1/messages",
            "CLINIC_PORTAL_DIR": os.path.join(work, "no_portal"), "FINANCE_LOCAL_URL": "http://127.0.0.1:9",
            "SHARED_LIB_DIR": os.path.join(work, "shared"), "FINANCE_DB_FOR_SCANS": os.path.join(work, "no_finance.db"),
            "SCANNER_OPENCV_JS": os.path.join(app, "static", "opencv.js")}


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def under(p, d):
    return bool(p) and os.path.realpath(p).startswith(os.path.realpath(d) + os.sep)


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True); d = sqlite3.connect(dst); s.backup(d); s.close(); d.close()


def prepare(D, SRC, shared_src, work):
    for sub in ("app", "uploads", "key", "no_portal", "shared"):
        os.makedirs(os.path.join(work, sub), exist_ok=True)
    for f in MODS:
        if os.path.exists(os.path.join(D, f)):
            shutil.copy(os.path.join(D, f), os.path.join(work, "app", f))
    if shared_src and os.path.isdir(shared_src):
        for f in os.listdir(shared_src):
            if f.endswith(".py"):
                shutil.copy(os.path.join(shared_src, f), os.path.join(work, "shared", f))
    with open(os.path.join(work, "key", "anthropic.key"), "w") as fh:
        fh.write("sk-ant-walk-made-up-" + "0" * 12 + "\n")
    dbp = os.path.join(work, "assets.db")
    copy_db(SRC, dbp)
    os.environ.update(setup_env(work))
    for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(k, None)
    appdir = os.path.join(work, "app")
    if appdir not in sys.path:
        sys.path.insert(0, appdir)
    return dbp, appdir


def users_and_settings(db):
    for k in ("desk.on", "machine.on", "desk.floor", "stationery.issue_on", "batteries.on", "stationery.many"):
        db.execute("DELETE FROM settings WHERE key=?", (k,))
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
    db.commit()


def freeze(*mods):
    for x in mods:
        if x is not None:
            x.TODAY = TODAY


def ensure_stationery(db):
    """The stationery tables as S568 makes them (a no-op when they are there) -- so the made-up items can be seeded before the import."""
    for d in ("CREATE TABLE IF NOT EXISTS stationery_item(id INTEGER PRIMARY KEY, name TEXT NOT NULL, unit TEXT NOT NULL DEFAULT 'piece', "
              "rate REAL, low_level REAL, active INTEGER NOT NULL DEFAULT 1, made_by TEXT, made_at TEXT, from_bill_id INTEGER, "
              "from_bill_created_at TEXT NOT NULL DEFAULT '')",
              "CREATE TABLE IF NOT EXISTS stationery_move(id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, qty REAL NOT NULL, place TEXT NOT NULL, "
              "day TEXT NOT NULL, ts REAL NOT NULL, stock_before REAL, by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', "
              "voided_by TEXT NOT NULL DEFAULT '')",
              "CREATE TABLE IF NOT EXISTS stationery_count(id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, counted REAL NOT NULL, stock_before REAL, "
              "diff REAL, opening INTEGER NOT NULL DEFAULT 0, day TEXT NOT NULL, ts REAL NOT NULL, by_whom TEXT, at TEXT)"):
        db.execute(d)
    db.commit()


def seed_items(db, t0):
    """Made-up items with opening counts (ts one hour before now, so a fresh issue's ts is after the count). {key: id}."""
    ensure_stationery(db)
    ids = {}
    for key, name, unit, active, counted in (("A", "WALK585 Register 2031", "piece", 1, 10), ("B", "WALK585 Copy 2031", "piece", 1, 5),
                                             ("C", "WALK585 Pen 2031", "packet", 1, 3), ("R", "WALK585 Retired 2031", "piece", 0, 4)):
        iid = db.execute("INSERT INTO stationery_item(name, unit, rate, low_level, active, made_by, made_at) VALUES(?,?,NULL,NULL,?,'Walk',?)",
                         (name, unit, active, "2031-06-01 10:00:00")).lastrowid
        db.execute("INSERT INTO stationery_count(item_id, counted, stock_before, diff, opening, day, ts, by_whom, at) VALUES(?,?,0,?,1,?,?,?,?)",
                   (iid, counted, counted, "2031-06-10", t0, "Walk Owner", "2031-06-10 10:00:00"))
        ids[key] = iid
    db.commit()
    return ids


def client_for(m, db, un):
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    u = db.execute("SELECT * FROM users WHERE username=?", (un,)).fetchone()
    cl = m.app.test_client()
    with cl.session_transaction() as ss:
        ss["uid"] = u["id"]; ss["epoch"] = epoch
    return cl


# ---------------------------------------------------------------------------------------------- M1's fresh process
def pages_mode():
    """--pages <dir> <db> <out.json> --work W: the app from <dir> on a fresh copy, the same made-up items; Stationery diya for the owner
    and a manager (stationery.issue_on ON) with stationery.many absent, ?one=1 absent-switch, then stationery.many ON."""
    i = ARGS.index("--pages")
    D, SRC, OUT = ARGS[i + 1], ARGS[i + 2], ARGS[i + 3]
    work = opt("--work") or tempfile.mkdtemp(prefix="s585pages_", dir="/tmp" if os.path.isdir("/tmp") else None)
    dbp, appdir = prepare(os.path.abspath(D), os.path.abspath(SRC), opt("--shared", "/root/shared"), os.path.abspath(work))
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    users_and_settings(db)
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.issue_on','on')")
    db.commit()
    seed_items(db, 1000000000.0)
    db.close()
    m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
    freeze(sys.modules.get("sorting_desk"), sys.modules.get("asset_machine"), sys.modules.get("stationery"), sys.modules.get("batteries"),
           sys.modules.get("xray_costs"))
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    own, mgr = client_for(m, db, "walk_own_2031"), client_for(m, db, "walk_mgr_2031")
    out = {}
    for tag, cl, url in (("own_off", own, "/stationery/diya"), ("mgr_off", mgr, "/stationery/diya"), ("own_off_one", own, "/stationery/diya?one=1")):
        r_ = cl.get(url)
        out[tag] = [r_.status_code, r_.get_data(as_text=True)]
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.many','on')"); db.commit()
    for tag, cl, url in (("own_on", own, "/stationery/diya"), ("mgr_on", mgr, "/stationery/diya")):
        r_ = cl.get(url)
        out[tag] = [r_.status_code, r_.get_data(as_text=True)]
    db.close()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    if "--keep" not in ARGS:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------------------------- the walk
def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S585_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s585walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
    work = os.path.abspath(work)
    try:
        run(D, SRC, shared_src, work)
    finally:
        if "--keep" not in ARGS:
            shutil.rmtree(work, ignore_errors=True)


def run(D, SRC, shared_src, work):
    FROMD = os.path.abspath(opt("--from") or D)
    dbp, appdir = prepare(D, SRC, shared_src, work)
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    users_and_settings(db)
    T0 = time.time() - 3600.0
    ids = seed_items(db, T0)
    A, B, C, RT = ids["A"], ids["B"], ids["C"], ids["R"]
    db.close()
    try:
        m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
    except Exception as e:                                                 # noqa: BLE001
        ck("W1 the app imports with these files", lambda: False, lambda: repr(e)); return
    cp, sd, am = sys.modules.get("clinic_papers"), sys.modules.get("sorting_desk"), sys.modules.get("asset_machine")
    st, bt, xc = sys.modules.get("stationery"), sys.modules.get("batteries"), sys.modules.get("xray_costs")
    ck("W1 (structural) the app imports; asset_register, clinic_papers, sorting_desk, asset_machine, stationery and batteries come from "
       "the scratch folder; the database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and am is not None and under(am.__file__, appdir) and st is not None and under(st.__file__, appdir) and st.MOUNTED
       and bt is not None and under(bt.__file__, appdir) and m.DB_PATH == dbp)
    ck("W2 the S585 mark: stationery MANY = S585, the switch stationery.many, X-ray in PLACES and the frozen four ONE_PLACES; the S568 "
       "marks kept (VERSION S568, FIX S568_FIX1) and the S582 / S575 / S571 marks kept",
       lambda: getattr(st, "MANY", None) == "S585" and st.MANY_SWITCH == "stationery.many" and ("xray", "X-ray") in st.PLACES
       and st.ONE_PLACES == (("lab", "Lab"), ("reception", "Reception"), ("sanjeevni", "Sanjeevni"), ("clinic", "Clinic"))
       and st.VERSION == "S568" and st.FIX == "S568_FIX1" and xc is not None and xc.VERSION == "S582" and getattr(bt, "SETUP", None) == "S575"
       and bt.VERSION == "S571" and sd.STOCK == "S568")
    freeze(sd, am, st, bt, xc)
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    own, mgr = client_for(m, db, "walk_own_2031"), client_for(m, db, "walk_mgr_2031")
    rcp_u = {"id": None, "username": "walk_rcp_2031", "display_name": "Walk Reception", "role": "reception", "active": 1}

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    def flashes(cl):
        with cl.session_transaction() as ss:
            f_ = list(ss.get("_flashes") or [])
            ss.pop("_flashes", None)
        return " | ".join(x[1] for x in f_)

    def setting(k, v):
        if v is None:
            db.execute("DELETE FROM settings WHERE key=?", (k,))
        else:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
        db.commit()

    def moves(*iids):
        q_ = "SELECT * FROM stationery_move WHERE item_id IN (%s) ORDER BY id" % ",".join("?" * len(iids))
        return [dict(r_) for r_ in db.execute(q_, iids)]

    def live_moves(*iids):
        return [x for x in moves(*iids) if not x["voided_at"]]

    def stock(iid):
        return None if st is None else round(st.stock_of(db, iid), 4)

    def audit_after(mark, action):
        return [dict(r_) for r_ in db.execute("SELECT * FROM desk_audit WHERE id>? AND action=? ORDER BY id", (mark, action))]

    def audit_mark():
        return db.execute("SELECT COALESCE(MAX(id),0) FROM desk_audit").fetchone()[0]

    def form(cl, url, data):
        return cl.post(url, data=data)

    def irow_html(page, iid):
        mm = re.search(r'<tr data-item="%d">(.*?)</tr>' % iid, page, re.S)
        return mm.group(1) if mm else ""

    def tds(rowhtml):
        return [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", rowhtml, re.S)]

    def mrow(page, mid):
        mm = re.search(r'<tr data-move="%d"( class=s585v)?>(.*?)</tr>' % mid, page, re.S)
        return (bool(mm.group(1)), mm.group(2)) if mm else (None, "")

    def section(page, start, end):
        i_ = page.find(start)
        if i_ < 0:
            return ""
        j_ = page.find(end, i_ + len(start))
        return page[i_:j_ if j_ > 0 else len(page)]

    # ================================================================== M1 switch OFF = byte-identical (fresh processes)
    outs = {}
    for tag, dd in (("from", FROMD), ("to", D)):
        o_ = os.path.join(work, "pages_%s.json" % tag)
        r_ = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--pages", dd, SRC, o_, "--work", os.path.join(work, "pg_" + tag),
                             "--shared", shared_src or ""], capture_output=True, text=True, timeout=600)
        if r_.returncode != 0 or not os.path.exists(o_):
            print("  (pages %s failed: %s)" % (tag, (r_.stderr or "")[-600:]))
            outs[tag] = {}
        else:
            outs[tag] = json.load(open(o_, encoding="utf-8"))
    same, diffs = True, []
    for k in ("own_off", "mgr_off", "own_off_one"):
        a_, b_ = outs.get("from", {}).get(k), outs.get("to", {}).get(k)
        if not a_ or not b_ or a_[0] != 200 or b_[0] != 200 or a_[1] != b_[1]:
            same = False
            if a_ and b_:
                i_ = next((j for j in range(min(len(a_[1]), len(b_[1]))) if a_[1][j] != b_[1][j]), min(len(a_[1]), len(b_[1])))
                diffs.append((k, a_[0], b_[0], a_[1][max(0, i_ - 80):i_ + 80], b_[1][max(0, i_ - 80):i_ + 80]))
            else:
                diffs.append((k, a_ and a_[0], b_ and b_[0]))
    to_on = (outs.get("to", {}).get("own_on") or [0, ""])
    to_mon = (outs.get("to", {}).get("mgr_on") or [0, ""])
    on_new = (to_on[0] == 200 and "id=s585many" in to_on[1] and "id=s568diya" not in to_on[1] and to_mon[0] == 200 and "id=s585many" in to_mon[1])
    # the comparison itself can fail: one changed word on the TO page is NOT taken as identical
    try:
        mut_red = outs["to"]["own_off"][1].replace("Kitne", "Kitna", 1) != outs["from"]["own_off"][1]
    except Exception:                                                      # noqa: BLE001
        mut_red = None
    print("M1 counts: OFF pages FROM = TO for the owner, a manager and ?one=1: %s; ON the TO page is the new screen (owner, manager) %s; "
          "a changed word is caught %s" % (same, on_new, mut_red))
    ck("M1 switch OFF (stationery.many absent) = byte-identical one-item screen: Stationery diya for the owner, for a manager "
       "(stationery.issue_on ON) and at ?one=1, FROM and TO each in a fresh process on two copies of the same database with the same "
       "made-up items -- identical bytes; with the switch ON the TO page is the new many-items screen",
       lambda: same and on_new and mut_red is True, lambda: diffs[:3])

    # ================================================================== M2 switch ON (on the owner's Stationery page) shows every active item with its stock
    flashes(own); flashes(mgr)
    am0 = audit_mark()
    sp_off = html(own, "/stationery")
    sw_post = form(own, "/stationery/many", {"on": "1"})
    sw_val = quiet(lambda: db.execute("SELECT value FROM settings WHERE key='stationery.many'").fetchone())
    f_sw = flashes(own)
    sw_aud = audit_after(am0, "stationery_many_switch")
    sp_on = html(own, "/stationery")
    m_sw = form(mgr, "/stationery/many", {"on": "0"}).status_code
    sw_after_m = quiet(lambda: db.execute("SELECT value FROM settings WHERE key='stationery.many'").fetchone())
    pg = html(own, "/stationery/diya")
    one_pg = html(own, "/stationery/diya?one=1")
    setting("stationery.issue_on", "on")
    pg_m = html(mgr, "/stationery/diya")
    rows2 = [(int(a_), htmlmod.unescape(b_), htmlmod.unescape(c_), d_, htmlmod.unescape(e_).strip())
             for a_, b_, c_, d_, e_ in re.findall(r'<div class=s585row data-item="(\d+)" data-name="([^"]*)"><div class=s585nm><b>([^<]*)</b>'
                                                  r'<span>shelf pe ([^ <]+) ([^<]*)</span>', pg)]
    act = quiet(lambda: st.item_rows(db, active_only=True), [])
    book = quiet(lambda: st.stock_book(db), {})
    want2 = [(i_["id"], i_["name"], i_["name"], st._plain(book.get(i_["id"], {"stock": 0.0})["stock"]), i_["unit"]) for i_ in act] if st else []
    places2 = re.findall(r'<label class=s585place><input type=radio name=place value="(\w+)"><span>([^<]+)</span></label>', pg)
    css2 = pg.split("<h2", 1)[0]
    ph = [int(x) for x in re.findall(r"\.s585place span\{[^}]*min-height:(\d+)px", css2)]
    bh = [int(x) for x in re.findall(r"\.s585ctl button\{[^}]*height:(\d+)px", css2)]
    g_many = section(pg, "<div class=card><b>Ginti</b>", "</form></div>")
    g_one = section(one_pg, "<div class=card><b>Ginti</b>", "</form></div>")
    retired_shown = 'data-item="%d"' % RT in pg
    print("M2 counts: switch POST %s -> %s (%s), audit lines %d, the card reads ON %s, a manager's POST %s (still %s); rows %d of %d active "
          "items, equal %s; places %s; button heights %s / %s px; Ginti card = the one-item screen's %s (%d bytes); retired item shown %s; "
          "the manager's screen %s" % (sw_post.status_code, tuple(sw_val) if sw_val else None, f_sw[:60], len(sw_aud),
                                       ">ON</button>" in section(sp_on, "id=s585switch", "</form>"), m_sw, tuple(sw_after_m) if sw_after_m else None,
                                       len(rows2), len(act), rows2 == want2, [w for _k, w in places2], ph, bh, bool(g_many) and g_many == g_one,
                                       len(g_many), retired_shown, "id=s585many" in pg_m))
    ck("M2 switch ON shows every active item with its stock: the ON / OFF card on the owner's Stationery page (OFF until he taps; his tap "
       "writes stationery.many = on, audited; a manager's POST is refused); Stationery diya then shows '1 · Kisko diya?' with five buttons "
       "Lab · Reception · Sanjeevni · Clinic · X-ray (>= 48 px), '2 · Kya aur kitna diya?' with EVERY active item -- its name, 'shelf pe "
       "<stock> <unit>' = the stock book, '−' and '+' >= 44 px -- no retired item; one 'Save karo' (grey until chosen); the Ginti card "
       "byte-equal to the one-item screen's",
       lambda: ">OFF</button>" in section(sp_off, "id=s585switch", "</form>") and sw_post.status_code == 302 and sw_val is not None
       and sw_val[0] == "on" and len(sw_aud) == 1 and ">ON</button>" in section(sp_on, "id=s585switch", "</form>") and m_sw == 403
       and sw_after_m[0] == "on" and rows2 == want2 and len(rows2) == len(act) and len(act) >= 3
       and places2 == [("lab", "Lab"), ("reception", "Reception"), ("sanjeevni", "Sanjeevni"), ("clinic", "Clinic"), ("xray", "X-ray")]
       and ph and min(ph) >= 48 and bh and min(bh) >= 44 and "1 · Kisko diya?" in pg and "2 · Kya aur kitna diya?" in pg
       and 'id=s585save disabled>Save karo</button>' in pg and g_many and g_many == g_one and not retired_shown and "id=s585many" in pg_m,
       lambda: dict(rows=rows2[:4], want=want2[:4], places=places2, ph=ph, bh=bh, ginti=(len(g_many), len(g_one)), sw=(sw_post.status_code, sw_val and tuple(sw_val), len(sw_aud), m_sw)))

    # ================================================================== M3 one save of three items -> three moves, one transaction
    flashes(own)
    am3 = audit_mark()
    mv0 = [x["id"] for x in moves(A, B, C)]
    s_a, s_b, s_c = stock(A), stock(B), stock(C)
    p3 = form(own, "/stationery/diya/many", {"place": "lab", "q%d" % A: "2", "q%d" % B: "1", "q%d" % C: "4", "q%d" % RT: ""})
    f3 = flashes(own)
    new3 = [x for x in moves(A, B, C) if x["id"] not in mv0]
    aud3 = audit_after(am3, "stationery_issue")
    st_after = (stock(A), stock(B), stock(C))
    sp3 = html(own, "/stationery")
    over_c = "above stock" in irow_html(sp3, C)
    # a forced failure on the third issue -> nothing written (the database refuses the third insert)
    orig_issue = getattr(st, "issue", None)
    calls = {"n": 0}

    def failing_issue(*a, **k):
        calls["n"] += 1
        if calls["n"] == 3:
            raise sqlite3.OperationalError("walk: a forced failure on the third issue")
        return orig_issue(*a, **k)
    mv1 = [x["id"] for x in moves(A, B, C)]
    am3b = audit_mark()
    if orig_issue is not None:
        st.issue = failing_issue
    try:
        p3f = form(own, "/stationery/diya/many", {"place": "reception", "q%d" % A: "1", "q%d" % B: "1", "q%d" % C: "1"})
    finally:
        if orig_issue is not None:
            st.issue = orig_issue
    f3f = flashes(own)
    new3f = [x for x in moves(A, B, C) if x["id"] not in mv1]
    aud3f = audit_after(am3b, "stationery_issue")
    # the third a retired item -> issue() refuses it -> nothing written
    p3r = form(own, "/stationery/diya/many", {"place": "reception", "q%d" % A: "1", "q%d" % B: "1", "q%d" % RT: "1"})
    f3r = flashes(own)
    new3r = [x for x in moves(A, B, C, RT) if x["id"] not in mv1]
    print("M3 counts: save of three %s -> new moves %s (places %s), audit lines %d; stock %s -> %s; flash %r; C above stock flagged %s; forced "
          "failure on the third: calls %d, new moves %d, audit lines %d, flash %r; a retired third: new moves %d, flash %r"
          % (p3.status_code, [(x["item_id"] == A and "A" or x["item_id"] == B and "B" or "C", x["qty"]) for x in new3], sorted(set(x["place"] for x in new3)),
             len(aud3), (s_a, s_b, s_c), st_after, f3[:160], over_c, calls["n"], len(new3f), len(aud3f), f3f[:80], len(new3r), f3r[:80]))
    ck("M3 one save of three items writes three moves (one per item with a number, through issue(), stock_before kept) in one "
       "transaction: the stock of each goes down, a quantity above the shelf stock is saved and flagged on the owner's page, 'Save ho "
       "gaya ✓ — <what was saved> → Lab'; a forced database failure on the third writes NONE (no move, no audit line), and a retired "
       "item as the third writes none",
       lambda: p3.status_code == 302 and sorted((x["item_id"], x["qty"], x["place"]) for x in new3) == sorted([(A, 2.0, "lab"), (B, 1.0, "lab"), (C, 4.0, "lab")])
       and all(x["stock_before"] is not None for x in new3) and len(aud3) == 3 and st_after == (s_a - 2, s_b - 1, s_c - 4)
       and f3.startswith("Save ho gaya ✓ — ") and "WALK585 Register 2031 2 piece" in f3 and "WALK585 Pen 2031 4 packet" in f3 and f3.endswith("→ Lab")
       and over_c and calls["n"] == 3 and p3f.status_code == 302 and new3f == [] and aud3f == [] and "Kuch save nahi hua" in f3f
       and p3r.status_code == 302 and new3r == [] and "Kuch save nahi hua" in f3r,
       lambda: dict(new3=[(x["item_id"], x["qty"], x["place"]) for x in new3], aud=len(aud3), st=(s_a, s_b, s_c, st_after), f3=f3, over=over_c,
                    forced=(calls["n"], len(new3f), len(aud3f), f3f), retired=(len(new3r), f3r)))

    # ================================================================== M4 no Kisko / no number = nothing sent; OFF = refused
    mv4 = [x["id"] for x in moves(A, B, C)]
    p4a = form(own, "/stationery/diya/many", {"q%d" % A: "1"}); f4a = flashes(own)
    p4b = form(own, "/stationery/diya/many", {"place": "lab"}); f4b = flashes(own)
    p4c = form(own, "/stationery/diya/many", {"place": "lab", "q%d" % A: "0", "q%d" % B: ""}); f4c = flashes(own)
    p4d = form(own, "/stationery/diya/many", {"place": "lab", "q%d" % A: "abc"}); f4d = flashes(own)
    p4e = form(own, "/stationery/diya/many", {"place": "nowhere", "q%d" % A: "1"}); f4e = flashes(own)
    setting("stationery.many", None)
    p4f = form(own, "/stationery/diya/many", {"place": "lab", "q%d" % A: "1"}); f4f = flashes(own)
    setting("stationery.many", "on")
    setting("stationery.issue_on", None)
    p4g = form(mgr, "/stationery/diya/many", {"place": "lab", "q%d" % A: "1"})
    orig_cu = m.current_user
    m.current_user = lambda: rcp_u
    try:
        p4h = m.app.test_client().post("/stationery/diya/many", data={"place": "lab", "q%d" % A: "1"}).status_code
    finally:
        m.current_user = orig_cu
    setting("stationery.issue_on", "on")
    new4 = [x for x in moves(A, B, C) if x["id"] not in mv4]
    js_ready = "var ready=!!pl&&ch.length>0&&!bad.length;sv.disabled=!ready;" in pg and "sv.disabled=true" in pg
    print("M4 counts: no place %s %r; no number %s %r; zeros %s %r; not a number %s %r; an unknown place %s %r; switch OFF %s %r; a manager "
          "with issue_on OFF %s; reception %s; new moves %d; the page's Save grey until a place and a number (and off after the first tap) %s"
          % (p4a.status_code, f4a[:50], p4b.status_code, f4b[:50], p4c.status_code, f4c[:50], p4d.status_code, f4d[:50], p4e.status_code, f4e[:50],
             p4f.status_code, f4f[:50], p4g.status_code, p4h, len(new4), js_ready))
    ck("M4 no Kisko / no number = nothing sent: the server refuses a save with no place, with no number (or only zeros), with a number "
       "that is not one, or with a place that is not on the list -- 'Kuch save nahi hua', nothing written; with the switch OFF the "
       "many-items save is refused; a manager with stationery.issue_on OFF and the reception login get 403; the page's Save is grey "
       "until a place and a number are chosen and is disabled on the first tap",
       lambda: all(p_.status_code == 302 for p_ in (p4a, p4b, p4c, p4d, p4e, p4f)) and "Kisko diya — chuno" in f4a and "Kuch nahi chuna" in f4b
       and "Kuch nahi chuna" in f4c and "number nahi hai" in f4d and "Kisko diya — chuno" in f4e and "band hai" in f4f
       and all("save nahi hua" in x for x in (f4a, f4b, f4c, f4d, f4e, f4f)) and p4g.status_code == 403 and p4h == 403 and new4 == [] and js_ready,
       lambda: dict(codes=[p_.status_code for p_ in (p4a, p4b, p4c, p4d, p4e, p4f, p4g)] + [p4h], fl=[f4a, f4b, f4c, f4d, f4e, f4f], new=len(new4)))

    # ================================================================== M5 X-ray is a place, on the owner's table
    mv5 = [x["id"] for x in moves(B)]
    p5 = form(own, "/stationery/diya/many", {"place": "xray", "q%d" % B: "1"}); f5 = flashes(own)
    new5 = [x for x in moves(B) if x["id"] not in mv5]
    sp5 = html(own, "/stationery")
    inv5 = quiet(lambda: st.inventory(db, YM), {})
    rb5 = next((r_ for r_ in (inv5 or {}).get("rows", []) if r_["id"] == B), {})
    cells5 = tds(irow_html(sp5, B))
    one5 = re.findall(r'<input type=radio name=place value="(\w+)"', section(html(own, "/stationery/diya?one=1"), "id=s568diya", "</form>"))
    bad_txt = ""
    try:
        st.issue(db, A, 1, "nowhere")
    except ValueError as e:
        bad_txt = str(e)
    except Exception as e:                                                 # noqa: BLE001
        bad_txt = repr(e)
    db.rollback()
    iss5 = section(sp5, "id=s585issues", "id=s585older")
    xr_row = mrow(sp5, new5[0]["id"])[1] if new5 else ""
    print("M5 counts: save to X-ray %s -> %s, flash %r; the owner's header %s; B's issued cell %r, by place %s; the one-item screen's places "
          "%s; issue()'s refusal %r; This month's issues shows it %s"
          % (p5.status_code, [(x["qty"], x["place"]) for x in new5], f5[:80], "Issued this month (Lab · Reception · Sanjeevni · Clinic · X-ray)" in sp5,
             cells5[3] if len(cells5) > 3 else None, rb5.get("by_place"), one5, bad_txt, "X-ray" in xr_row))
    ck("M5 X-ray accepted as a place: the many-items save to X-ray writes one move (place xray), 'Save ho gaya ✓ — … → X-ray'; the owner's "
       "stock table's header reads 'Issued this month (Lab · Reception · Sanjeevni · Clinic · X-ray)' and the item's cell carries the X-ray "
       "figure; This month's issues shows 'X-ray'; issue()'s refusal names X-ray; the one-item screen keeps its four places",
       lambda: p5.status_code == 302 and [(x["qty"], x["place"]) for x in new5] == [(1.0, "xray")] and f5.endswith("→ X-ray")
       and "Issued this month (Lab · Reception · Sanjeevni · Clinic · X-ray)" in sp5 and len(cells5) > 3 and cells5[3] == "1 · 0 · 0 · 0 · 1"
       and rb5.get("by_place", {}).get("xray") == 1.0 and rb5.get("by_place", {}).get("lab") == 1.0 and "X-ray" in xr_row and xr_row in iss5
       and one5 == ["lab", "reception", "sanjeevni", "clinic"] and bad_txt == "Kisko diya — Lab, Reception, Sanjeevni, Clinic ya X-ray chuno.",
       lambda: dict(p=p5.status_code, new=[(x["qty"], x["place"]) for x in new5], f=f5, cells=cells5, bp=rb5.get("by_place"), one=one5, bad=bad_txt))

    # ================================================================== M6 Void
    flashes(own); flashes(mgr)
    a_line = next((x for x in new3 if x["item_id"] == A), None)
    b_line = next((x for x in new3 if x["item_id"] == B), None)
    aid_, bid_ = (a_line or {}).get("id", 0), (b_line or {}).get("id", 0)
    a6 = stock(A)
    am6 = audit_mark()
    m6_page = mgr.get("/stationery").status_code
    m6_post = form(mgr, "/stationery/void", {"id": str(aid_)}).status_code
    m.current_user = lambda: rcp_u
    try:
        r6_post = m.app.test_client().post("/stationery/void", data={"id": str(aid_)}).status_code
    finally:
        m.current_user = orig_cu
    a_after_forged = quiet(lambda: db.execute("SELECT voided_at FROM stationery_move WHERE id=?", (aid_,)).fetchone()[0])
    p6 = form(own, "/stationery/void", {"id": str(aid_)}); f6 = flashes(own)
    arow = quiet(lambda: dict(db.execute("SELECT * FROM stationery_move WHERE id=?", (aid_,)).fetchone()), {})
    a6b = stock(A)
    aud6 = audit_after(am6, "stationery_issue_voided")
    p6again = form(own, "/stationery/void", {"id": str(aid_)}); f6again = flashes(own)
    p6none = form(own, "/stationery/void", {"id": "999999999"}); f6none = flashes(own)
    # a line made BEFORE the latest count: voiding it changes nothing -- the count stands
    form(own, "/stationery/count", {"back": "stock", "c%d" % B: "7"}); flashes(own)
    b6 = stock(B)
    p6b = form(own, "/stationery/void", {"id": str(bid_)}); f6b = flashes(own)
    b6b = stock(B)
    sp6 = html(own, "/stationery")
    inv6 = quiet(lambda: st.inventory(db, YM), {})
    ra6 = next((r_ for r_ in (inv6 or {}).get("rows", []) if r_["id"] == A), {})
    struck, row6 = mrow(sp6, aid_)
    live_row = mrow(sp6, new5[0]["id"] if new5 else 0)
    print("M6 counts: a manager's page %s, a manager's forged Void %s, reception %s (the line still live %s); the owner's Void %s: voided_by %r, "
          "stock %s -> %s, audit %d, flash %r; again %r; no such line %r; before the latest count: stock %s -> %s, flash %r; the page: struck %s, "
          "'voided by' %s, a live line has a Void button %s; A's Lab figure after the Void %s"
          % (m6_page, m6_post, r6_post, a_after_forged == "", p6.status_code, arow.get("voided_by"), a6, a6b, len(aud6), f6[:80], f6again[:50],
             f6none[:50], b6, b6b, f6b[:110], struck, "voided by Walk Owner" in row6, 'name=id value="%d"><button class="btn small danger">Void</button>' % (new5[0]["id"] if new5 else 0) in live_row[1],
             ra6.get("by_place", {}).get("lab")))
    ck("M6 Void by the owner: the line is kept (voided_at, voided_by = the owner), audited in desk_audit, struck through on his page "
       "('voided by …'), and leaves the stock arithmetic (stock up by its quantity; out of the per-place figure); a second Void and an "
       "unknown line change nothing; a line made before the latest count changes no stock ('the count stands', said on the page); a "
       "manager gets 403 on the page (no Void to see) and on a forged POST, and so does reception -- the line stays live",
       lambda: m6_page == 403 and m6_post == 403 and r6_post == 403 and a_after_forged == "" and p6.status_code == 302
       and arow.get("voided_at") and arow.get("voided_by") == "Walk Owner" and a6b == a6 + 2 and len(aud6) == 1 and f6.startswith("Voided: WALK585 Register 2031 2 piece to Lab.")
       and "already voided" in f6again and "not on the list" in f6none and b6 == 7.0 and b6b == 7.0 and "the count stands" in f6b
       and struck is True and "voided by Walk Owner" in row6 and live_row[0] is False and "btn small danger" in live_row[1]
       and "Voiding an issue made before the latest count does not change the stock — the count stands." in sp6
       and ra6.get("by_place", {}).get("lab") == 0.0,
       lambda: dict(m=(m6_page, m6_post, r6_post, a_after_forged), own=(p6.status_code, arow.get("voided_by"), a6, a6b, len(aud6), f6),
                    again=f6again, none=f6none, pre=(b6, b6b, f6b), struck=struck, row=row6[:300], lab=ra6.get("by_place")))

    # ================================================================== M7 the data step (schema copies) and the sheet's lines on the page
    def schema_copy(path, names, counted=None, extra_uncounted=("A4 paper (75 gsm)",)):
        c = sqlite3.connect(path)
        for t in ("bills", "settings", "desk_audit", "stationery_item", "stationery_line", "stationery_move", "stationery_count"):
            sql = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0]
            c.execute(sql)
        T = 1792315046.523                                                  # a made-up count moment (the walk's own)
        out_ = {}
        for nm in list(names) + ["WALK585 Ring file", "WALK585 Clear bag", "WALK585 Folder", "WALK585 Cheque folder"] + list(extra_uncounted):
            iid = c.execute("INSERT INTO stationery_item(name, unit, active, made_by, made_at) VALUES(?, 'piece', 1, 'Walk', '2031-06-01 10:00:00')", (nm,)).lastrowid
            out_[nm] = iid
            if nm not in extra_uncounted and (counted is None or nm in counted):
                c.execute("INSERT INTO stationery_count(item_id, counted, stock_before, diff, opening, day, ts, by_whom, at) VALUES(?,?,0,?,1,'2031-06-10',?,'Walk','x')",
                          (iid, 6.0, 6.0, T))
        c.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, item_id, day, ts) VALUES(1,'',1,'x',2,'ream',?,'2031-06-09',?)",
                  (out_["A4 paper (75 gsm)"], T - 99))
        c.commit(); c.close()
        return out_, T

    def hist_run(path):
        r_ = subprocess.run([sys.executable, "-B", os.path.join(appdir, "stationery.py"), "--history", path], capture_output=True, text=True, timeout=120)
        return r_.returncode, r_.stdout.strip().splitlines()

    def rows_of(path):
        c = sqlite3.connect(path)
        try:
            return [tuple(r_) for r_ in c.execute("SELECT i.name, m.qty, m.place, m.day, m.ts, m.stock_before, m.by_whom FROM stationery_move m "
                                                  "JOIN stationery_item i ON i.id=m.item_id ORDER BY m.id")]
        except sqlite3.Error:
            return None
        finally:
            c.close()

    def key_of(path):
        c = sqlite3.connect(path)
        try:
            r_ = c.execute("SELECT value FROM settings WHERE key='stationery.history_s585'").fetchone()
            return r_[0] if r_ else None
        except sqlite3.Error:
            return None
        finally:
            c.close()
    sdir = os.path.join(work, "seed"); os.makedirs(sdir, exist_ok=True)
    s1 = os.path.join(sdir, "s1.db"); ids1, T1 = schema_copy(s1, SEVEN)
    h1 = hist_run(s1); r1 = rows_of(s1); k1 = key_of(s1)
    h2 = hist_run(s1); r2 = rows_of(s1)
    want7 = sorted([("Register 72 pages", 6.0, "reception"), ("Register 104 pages", 6.0, "reception"), ("Register 192 pages", 3.0, "lab"),
                    ("Register 104 pages", 6.0, "lab"), ("Small notebook (copy)", 2.0, "lab"), ("Notebook (copy) 72 pages", 6.0, "sanjeevni"),
                    ("Small notebook (copy)", 2.0, "xray")])
    stock1 = [x for x in h1[1] if x.startswith("stock: ")]
    s2 = os.path.join(sdir, "s2.db")
    schema_copy(s2, [n for n in SEVEN if n != "Register 72 pages"], counted=[n for n in SEVEN if n != "Small notebook (copy)"])
    h3 = hist_run(s2); r3 = rows_of(s2)
    s3 = os.path.join(sdir, "s3.db"); schema_copy(s3, SEVEN)
    o3 = []
    g3 = quiet(lambda: st.history_step(s3, shift=1.0, out=o3.append), None)            # a line AFTER the count would change the stock
    r4 = rows_of(s3); k3 = key_of(s3)
    print("M7 counts: first run exit %s, lines written %d, rows %d (by_whom %s; ts 1 s before the count %s; day = the count's %s; stock_before "
          "NULL %s); stock lines %d, each before = after %s; key %s; second run %r, rows %d; an absent item / no opening count: %s, rows %d; "
          "a line after the count: %s, %s, rows %d, key %s"
          % (h1[0], len([x for x in h1[1] if x.startswith("history: wrote")]), len(r1 or []), sorted(set(x[6] for x in r1 or [])),
             all(abs(x[4] - (T1 - 1.0)) < 1e-6 for x in r1 or []), all(x[3] == "2031-06-10" for x in r1 or []), all(x[5] is None for x in r1 or []),
             len(stock1), all(x.split("before ")[-1].split(", after ")[0] == x.split(", after ")[-1] for x in stock1), bool(k1), h2[1][-1:],
             len(r2 or []), [x for x in h3[1] if "skipped" in x], len(r3 or []), g3, o3[-1:] if o3 else None, len(r4 or []), k3))
    # the sheet's lines on the owner's page: never "this month", in their own fold, voidable (made-up: one line for item C on the copy)
    o5 = []
    g5 = quiet(lambda: st.history_step(dbp, plan=(("WALK585 Pen 2031", 2, "reception", "walk"),), key="walk585.history_s585", out=o5.append), None)
    hrow = quiet(lambda: dict(db.execute("SELECT * FROM stationery_move WHERE item_id=? AND by_whom=?", (C, HIST_BY)).fetchone()), {})
    c7 = stock(C)
    sp7 = html(own, "/stationery")
    inv7 = quiet(lambda: st.inventory(db, YM), {})
    rc7 = next((r_ for r_ in (inv7 or {}).get("rows", []) if r_["id"] == C), {})
    in_month = 'data-move="%d"' % hrow.get("id", 0) in section(sp7, "id=s585issues", "id=s585older")
    hsec = section(sp7, "id=s585hist", "</details>")
    in_fold = 'data-move="%d"' % hrow.get("id", 0) in hsec
    p7v = form(own, "/stationery/void", {"id": str(hrow.get("id", 0))}); f7v = flashes(own)
    c7b = stock(C)
    hv = quiet(lambda: db.execute("SELECT voided_by FROM stationery_move WHERE id=?", (hrow.get("id", 0),)).fetchone()[0])
    print("M7 page: the line written %s (%s), C's stock %s -> unchanged %s; in This month's issues %s; in the fold 'Earlier issues — from "
          "Shavez's sheet (no date)' %s ('no date' %s); C's Reception figure %s; its Void %s %r -> stock %s"
          % (g5, o5[:1], c7, c7 == st_after[2] if st else None, in_month, in_fold, "<td class=s>no date</td>" in hsec,
             rc7.get("by_place", {}).get("reception"), p7v.status_code, f7v[:90], c7b))
    ck("M7 the data step (stationery.py --history, on schema copies with made-up items of the seven exact names): writes the 7 rows "
       "(by_whom 'history (Shavez sheet)', day = the opening count's, ts 1 s before it, stock_before NULL), the stock figures before = "
       "after, the key set; a second run writes nothing; an absent item and an item with no opening count are skipped with one line each; "
       "a line that WOULD change a stock rolls back (nothing written, no key); on the owner's page such a line is never in This month's "
       "issues or the per-place figures, it is in the fold 'Earlier issues — from Shavez's sheet (no date)', and Void marks it",
       lambda: h1[0] == 0 and len([x for x in h1[1] if x.startswith("history: wrote")]) == 7 and r1 is not None
       and sorted((x[0], x[1], x[2]) for x in r1) == want7 and all(x[6] == HIST_BY and x[5] is None and x[3] == "2031-06-10"
                                                                   and abs(x[4] - (T1 - 1.0)) < 1e-6 for x in r1)
       and len(stock1) == 9 and all(x.split("before ")[-1].split(", after ")[0] == x.split(", after ")[-1] for x in stock1)
       and k1 is not None and k1.startswith("7 rows") and h2[0] == 0 and any("already done" in x for x in h2[1]) and r2 == r1
       and h3[0] == 0 and "history: skipped -- no active item named 'Register 72 pages' (6 to Reception, the OPD register)" in h3[1]
       and len([x for x in h3[1] if "has no opening count yet" in x and "Small notebook (copy)" in x]) == 2 and len(r3 or []) == 4
       and g3 == 1 and any("REFUSED -- a stock figure changed" in x for x in o3) and r4 == [] and k3 is None
       and g5 == 0 and hrow.get("by_whom") == HIST_BY and c7 == st_after[2] and not in_month and in_fold and "<td class=s>no date</td>" in hsec
       and "from Shavez's sheet" in hsec and rc7.get("by_place", {}).get("reception") == 0.0
       and p7v.status_code == 302 and "the count stands" in f7v and c7b == c7 and hv == "Walk Owner",
       lambda: dict(h1=h1, r1=r1, k1=k1, h2=h2[1][-2:], h3=h3[1], r3=r3, g3=(g3, o3[-2:], r4, k3), page=(g5, hrow, c7, in_month, in_fold, rc7.get("by_place"), f7v, c7b, hv)))

    # ================================================================== M8 ?one=1 still works (the manual fallback)
    flashes(own)
    one8 = html(own, "/stationery/diya?one=1")
    mv8 = [x["id"] for x in moves(A)]
    a8 = stock(A)
    p8 = own.post("/stationery/diya", data={"item": str(A), "qty": "1", "place": "clinic", "one": "1"})
    f8 = flashes(own)
    new8 = [x for x in moves(A) if x["id"] not in mv8]
    p8b = own.post("/stationery/diya", data={"item": str(A), "qty": "1", "place": "clinic"}); flashes(own)
    print("M8 counts: ?one=1 -> the one-item form %s with the hidden one=1 %s and four places %s; its POST %s -> %s, flash %r, move %s; "
          "a POST without one=1 -> %s"
          % ("id=s568diya" in one8, '<input type=hidden name=one value=1>' in one8,
             re.findall(r'name=place value="(\w+)"', section(one8, "id=s568diya", "</form>")), p8.status_code, p8.headers.get("Location"),
             f8[:70], [(x["qty"], x["place"]) for x in new8], p8b.headers.get("Location")))
    ck("M8 ?one=1 still works with the switch ON: Stationery diya?one=1 is the one-item screen (four places, a hidden one=1); its Save "
       "issues one item ('Ho gaya — …') and returns to ?one=1; without one=1 it returns to the many-items screen",
       lambda: "id=s568diya" in one8 and "id=s585many" not in one8 and '<input type=hidden name=one value=1>' in one8
       and re.findall(r'name=place value="(\w+)"', section(one8, "id=s568diya", "</form>")) == ["lab", "reception", "sanjeevni", "clinic"]
       and p8.status_code == 302 and (p8.headers.get("Location") or "").endswith("/stationery/diya?one=1") and f8.startswith("Ho gaya — WALK585 Register 2031 1 piece, Clinic ko.")
       and [(x["qty"], x["place"]) for x in new8] == [(1.0, "clinic")] and stock(A) == a8 - 2
       and (p8b.headers.get("Location") or "").endswith("/stationery/diya"),
       lambda: dict(one="id=s568diya" in one8, hidden='name=one value=1' in one8, p8=(p8.status_code, p8.headers.get("Location"), f8), new=new8))

    # ================================================================== M9 the staff page: under 100 KB and 2 s
    flashes(own); flashes(mgr)
    t_ = time.time()
    r9 = mgr.get("/stationery/diya")
    dt9 = time.time() - t_
    b9 = r9.get_data()
    print("M9 counts: the manager's many-items screen %s, %d bytes, %.3f s" % (r9.status_code, len(b9), dt9))
    ck("M9 the staff page (the many-items screen, a manager) answers under 2 s and under 100 KB",
       lambda: r9.status_code == 200 and b"id=s585many" in b9 and len(b9) < 100 * 1024 and dt9 < 2.0,
       lambda: (r9.status_code, len(b9), dt9))

    sp = opt("--save-pages")
    if sp:
        os.makedirs(sp, exist_ok=True)
        form(own, "/stationery/diya/many", {"place": "lab", "q%d" % A: "1"})
        after = html(own, "/stationery/diya")
        for nm_, body_ in (("many.html", html(own, "/stationery/diya")), ("many_after.html", after), ("stock.html", html(own, "/stationery")),
                           ("one.html", html(own, "/stationery/diya?one=1"))):
            with open(os.path.join(sp, nm_), "w", encoding="utf-8") as fh:
                fh.write(body_)
        print("pages saved: 4")
    db.close()


if __name__ == "__main__":
    if "--pages" in ARGS:
        pages_mode(); sys.exit(0)
    if len(ARGS) < 2:
        print(__doc__); sys.exit(2)
    try:
        main()
    except Exception as e:                                                 # noqa: BLE001
        import traceback
        traceback.print_exc()
        ck("the walk ran to its end", lambda: False, lambda: repr(e))
    reds = R.count(False)
    print("%d checks: %d GREEN, %d RED%s" % (len(R), R.count(True), reds, (" (" + ", ".join(FAILED) + ")") if FAILED else ""))
    if "--expect-red" in ARGS:
        seen_ = {}
        for ok_, nm_ in zip(R, NAMES):
            seen_[nm_] = ok_
        not_red = [k for k in MUST_RED if seen_.get(k) is not False]
        print("CONTROL must-be-red: %s -- %s" % (", ".join(MUST_RED), ("all RED" if not not_red else "NOT red: " + ", ".join(
            k + ("(green)" if seen_.get(k) else "(not reached)") for k in not_red))))
        print("CONTROL structural (green on both, named): %s" % ", ".join("%s %s" % (k, "GREEN" if seen_.get(k) else "RED") for k in ("W1",)))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
