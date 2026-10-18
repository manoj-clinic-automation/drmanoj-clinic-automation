#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s582.py -- the S582_XRAY_COSTS walk. The app with the given files on a COPY of a database (SQLite's backup API), in its own
scratch folder; made-up rows only: papers of 'WALK582 ..' suppliers with stamps the walk picks from numbers no paper of the copy has
(B-9nnn), dated in a made-up June 2031 (today frozen at 15-Jun-2031); a made-up machine 'WALK582 FDR detector' in a made-up room, a
made-up battery place 'WALK582 X-ray UPS'; made-up logins (walk_own_2031 / walk_mgr_2031, made here); no reader thread, no paid call,
nothing sent anywhere. Flask's test client; no port. Every row the walk uses is found by its key (its id, stamp or name), never by
counting rows; totals are compared for the made-up month only.

    python3 -B walk_s582.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js, stationery.py, batteries.py [, xray_costs.py]> <assets.db to copy>
                            --from <dir with the FROM files> [--work DIR] [--shared DIR] [--expect-red] [--keep] [--save-pages DIR]

Checks: W1 (structural) the app imports from the scratch folder; W2 the S582 mark; Z1 (structural) the mount adds only the table
xray_mark and its index xray_mark_live, no row, no setting; X1-X11 one per item of the brief's walk list (s5). --expect-red (the
control, on the FROM files: no xray_costs.py, batteries.py at 40eb8a91): exit 0 only if every check in MUST_RED is RED (W1, Z1 are
structural: green on both). Counts and made-up totals are printed, never a live row's content. X11 runs FROM and TO each in a fresh
process (this file with --pages) on two copies of the same database with the same made-up rows. --save-pages DIR writes the owner's
X-ray expenses page (made-up month) for the PC's browser walk at 1366 x 768."""
import datetime, importlib.util, json, os, re, shutil, sqlite3, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.realpath(p or os.getcwd()) != HERE]   # never import xray_costs from the kit's own folder
ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11")
TODAY = datetime.date(2031, 6, 15)
YM = "2031-06"
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js", "stationery.py", "batteries.py", "xray_costs.py")
XR_OBJS = {("table", "xray_mark"), ("index", "xray_mark_live")}
XR_A = re.compile(r'<a href="[^"]*" data-s559="s582_xray"[^>]*>X-ray costs</a>')


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


def shape(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    try:
        objs = {(r[0], r[1]) for r in c.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        counts = {t: c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for k, t in objs if k == "table"}
        sets = {r[0]: r[1] for r in c.execute("SELECT key, value FROM settings")}
    finally:
        c.close()
    return objs, counts, sets


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
    for k in ("desk.on", "machine.on", "desk.floor", "stationery.issue_on", "batteries.on"):
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


class Rows(object):
    """Made-up rows, inserted with plain SQL (the same on every copy: the stamps are picked from B-9999 down)."""

    def __init__(self, db):
        self.db, self.used = db, set()

    def free_stamp(self):
        for n in range(9999, 999, -1):
            s_ = "B-%04d" % n
            if s_ not in self.used and not self.db.execute("SELECT 1 FROM bills WHERE upper(stamp_no)=?", (s_,)).fetchone():
                self.used.add(s_)
                return s_
        raise RuntimeError("no free stamp")

    def paper(self, vendor, lane="clinic", status=None, created="2031-06-10 05:00:00", kind=None, **cols_):
        kd = kind or {"clinic": "Consumable", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st_ = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no=self.free_stamp(), status=st_, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk", bill_date=created[:10])
        vals.update(cols_)
        bid = self.db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        self.db.commit()
        return bid, vals["stamp_no"]

    def room(self, name):
        r = self.db.execute("SELECT id FROM locations WHERE name=?", (name,)).fetchone()
        if r:
            return r[0]
        x = self.db.execute("INSERT INTO locations(name, visibility) VALUES(?, 'general')", (name,)).lastrowid
        self.db.commit()
        return x

    def machine(self, name, room, created, price=None):
        x = self.db.execute("INSERT INTO assets(name, location_id, category, price, purchase_date, created_at, hidden) VALUES(?,?,?,?,?,?,0)",
                            (name, room, "Other", price, created[:10], created)).lastrowid
        self.db.commit()
        return x

    def spend(self, aid, day, cost, work="WALK582 service", bill=None, bill_fp=None):
        x = self.db.execute("INSERT INTO service_logs(asset_id, log_date, work, cost, done_by, created_at, bill_id, bill_created_at) VALUES(?,?,?,?,?,?,?,?)",
                            (aid, day, work, cost, "WALK582 Engineer", day + " 10:00:00", bill, bill_fp)).lastrowid
        self.db.commit()
        return x

    def cover(self, aid, a_fp, frm, till, cost, kind="amc", bill=None, bill_fp=None, voided="", at="2031-06-01 10:00:00"):
        x = self.db.execute("INSERT INTO asset_cover(asset_id, kind, provider, from_day, till_day, cost, bill_id, voided_at, by_whom, at, asset_created_at, "
                            "bill_created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (aid, kind, "WALK582 Provider", frm, till, cost, bill, voided, "Walk", at, a_fp, bill_fp)).lastrowid
        self.db.commit()
        return x

    def place(self, name, made):
        x = self.db.execute("INSERT INTO battery_place(grp, name, sub, payer, supplier, warranty_months, life_months, sort, made_by, made_at) "
                            "VALUES('online_ups',?,'Walk','clinic','B.L. Computers',12,30,950,'Walk',?)", (name, made)).lastrowid
        self.db.commit()
        return x

    def fit(self, pid, day, price, bill=None, bill_fp="", voided=""):
        x = self.db.execute("INSERT INTO battery_fit(place_id, fitted_on, supplier, brand, price, bill_id, bill_created_at, by_whom, at, voided_at) "
                            "VALUES(?,?,?,?,?,?,?,?,?,?)", (pid, day, "B.L. Computers", "WalkBrand", price, bill, bill_fp or "", "Walk",
                                                             day + " 10:00:00", voided)).lastrowid
        self.db.commit()
        return x


# ---------------------------------------------------------------------------------------------- X11's fresh process
def pages_mode():
    """--pages <dir> <db> <out.json> --work W: the app from <dir> on a fresh copy, the same made-up rows, the four pages for the owner
    and the manager (desk.on, batteries.on, machine.on ON), written as JSON."""
    i = ARGS.index("--pages")
    D, SRC, OUT = ARGS[i + 1], ARGS[i + 2], ARGS[i + 3]
    work = opt("--work") or tempfile.mkdtemp(prefix="s582pages_", dir="/tmp" if os.path.isdir("/tmp") else None)
    dbp, appdir = prepare(os.path.abspath(D), os.path.abspath(SRC), opt("--shared", "/root/shared"), os.path.abspath(work))
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    users_and_settings(db)
    for k in ("batteries.on", "machine.on"):
        db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?, 'on')", (k,))
    db.commit()
    rw = Rows(db)
    room = rw.room("WALK582 Page room")
    aid = rw.machine("WALK582 Page machine", room, "2031-06-01 10:00:00", 1000.0)
    rw.spend(aid, "2031-06-02", 300.0)
    rw.cover(aid, "2031-06-01 10:00:00", "2031-06-01", "2032-05-31", 900.0)
    pid = rw.place("WALK582 Page UPS", "2031-06-01 09:00:00")
    rw.fit(pid, "2031-06-03", 5000.0)
    rw.paper("WALK582 Film Page", status="approved", subgroup="xray_small", total_amount=700.0, created="2031-06-04 10:00:00")
    db.close()
    m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
    freeze(sys.modules.get("sorting_desk"), sys.modules.get("asset_machine"), sys.modules.get("stationery"), sys.modules.get("batteries"),
           sys.modules.get("xray_costs"))
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    out = {"xray_mounted": bool(getattr(sys.modules.get("xray_costs"), "MOUNTED", False))}
    for un in ("walk_own_2031", "walk_mgr_2031"):
        u = db.execute("SELECT * FROM users WHERE username=?", (un,)).fetchone()
        cl = m.app.test_client()
        with cl.session_transaction() as ss:
            ss["uid"] = u["id"]; ss["epoch"] = epoch
        for nm, url in (("month", "/desk/month?ym=" + YM), ("batteries", "/batteries"), ("place", "/batteries/place/%d" % pid),
                        ("machine", "/assets/%d" % aid)):
            r_ = cl.get(url)
            out["%s:%s" % (u["role"], nm)] = [r_.status_code, r_.get_data(as_text=True)]
    db.close()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    if "--keep" not in ARGS:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------------------------- the walk
def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S582_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s582walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
    work = os.path.abspath(work)
    try:
        run(D, SRC, shared_src, work)
    finally:
        if "--keep" not in ARGS:
            shutil.rmtree(work, ignore_errors=True)


def run(D, SRC, shared_src, work):
    FROMD = os.path.abspath(opt("--from") or D)
    dbp, appdir = prepare(D, SRC, shared_src, work)
    shape0 = shape(dbp)
    try:
        m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
    except Exception as e:                                                 # noqa: BLE001
        ck("W1 the app imports with these files", lambda: False, lambda: repr(e)); return
    cp, sd, am = sys.modules.get("clinic_papers"), sys.modules.get("sorting_desk"), sys.modules.get("asset_machine")
    st, bt, xc = sys.modules.get("stationery"), sys.modules.get("batteries"), sys.modules.get("xray_costs")
    shape1 = shape(dbp)
    ck("W1 (structural) the app imports; asset_register, clinic_papers, sorting_desk, asset_machine, stationery and batteries come from "
       "the scratch folder; the database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and am is not None and under(am.__file__, appdir) and st is not None and under(st.__file__, appdir)
       and bt is not None and under(bt.__file__, appdir) and bt.MOUNTED and m.DB_PATH == dbp)
    ck("W2 the S582 mark: xray_costs VERSION S582, mounted from the scratch folder (from batteries.init); the S575 / S571 marks kept "
       "(batteries SETUP S575, VERSION S571) and the S568 / S566 / S563 / S560 / S559 / S557 / S555 / S551 marks kept",
       lambda: xc is not None and under(xc.__file__, appdir) and xc.VERSION == "S582" and xc.MOUNTED
       and getattr(bt, "SETUP", None) == "S575" and bt.VERSION == "S571" and getattr(sd, "BATTERY", None) == "S571"
       and sd.STOCK == "S568" and sd.LAST == "S566" and sd.TIDY == "S563" and sd.RECEIPTS == "S560" and sd.ROAD == "S559"
       and sd.MACHINE == "S557" and sd.CORRECTIONS == "S555" and sd.VERSION == "S551.2")
    new_objs = shape1[0] - shape0[0]
    differ = sorted(t for t, n in shape0[1].items() if shape1[1].get(t) != n and t != "settings")
    set_new = {k: v for k, v in shape1[2].items() if k not in shape0[2]}
    set_same = all(shape1[2].get(k) == v for k, v in shape0[2].items())
    xr_rows = shape1[1].get("xray_mark", 0)
    print("Z1 counts: new objects %s; every old table's row count kept %s%s; settings added %s; every old setting kept %s; xray_mark rows %s"
          % (sorted(n for _t, n in new_objs), not differ, (" (differ: %s)" % ", ".join(differ)) if differ else "", sorted(set_new), set_same, xr_rows))
    ck("Z1 (structural) the mount adds only the table xray_mark and its index xray_mark_live (no seed at mount: no row), no setting; no "
       "existing table's rows or setting changed",
       lambda: not differ and set_same and not set_new and not (shape0[0] - shape1[0]) and new_objs in (set(), XR_OBJS) and xr_rows == 0)

    freeze(sd, am, st, bt, xc)
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    users_and_settings(db)
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    own_u = db.execute("SELECT * FROM users WHERE username='walk_own_2031'").fetchone()
    mgr_u = db.execute("SELECT * FROM users WHERE username='walk_mgr_2031'").fetchone()

    def client(u):
        cl = m.app.test_client()
        with cl.session_transaction() as ss:
            ss["uid"] = u["id"]; ss["epoch"] = epoch
        return cl
    own, mgr = client(own_u), client(mgr_u)

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    def row(bid):
        r_ = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        return dict(r_) if r_ else {}

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

    def digits(stamp):
        return stamp.split("-", 1)[1].lstrip("0")

    def menu(u):
        with m.app.test_request_context("/"):
            from flask import g as g_
            g_.user = u
            return [x[1] for x in m._s559_items(u)]

    def after(lst, a, b):
        return a in lst and b in lst and lst.index(b) == lst.index(a) + 1

    def view():
        db2 = sqlite3.connect(dbp); db2.row_factory = sqlite3.Row
        try:
            with m.app.test_request_context("/"):
                return xc.month_view(db2, YM)
        finally:
            db2.close()

    def tot(page, fold):
        x = re.search(r'id=%s open data-total="([-\d.]+)"' % fold, page)
        return float(x.group(1)) if x else None

    def row_of(page, attr, val):
        i_ = page.find('<tr %s="%s">' % (attr, val))
        return page[i_:page.find("</tr>", i_)] if i_ >= 0 else ""

    def mark_stamp(stamp_typed):
        r_ = own.post("/xray/mark", data={"do": "paper", "stamp": stamp_typed, "ym": YM})
        return r_.status_code, flashes(own)

    rw = Rows(db)
    # ------------------------------------------------------------------ the made-up rows (June 2031)
    f_bill, s_fbill = rw.paper("WALK582 Film Co", status="approved", subgroup="xray_small", total_amount=1000.0, created="2031-06-04 10:00:00")
    f_fin, s_ffin = rw.paper("WALK582 Film Co", subgroup="xray_11x14", doc_kind="challan", challan_state="final", total_amount=500.0, created="2031-06-05 10:00:00")
    f_cov, s_fcov = rw.paper("WALK582 Film AMC", status="approved", subgroup="xray", total_amount=400.0, created="2031-06-06 10:00:00")
    f_rct, _ = rw.paper("WALK582 Film Co", status="approved", subgroup="xray_small", doc_kind="receipt", total_amount=700.0, created="2031-06-07 10:00:00")
    f_wai, _ = rw.paper("WALK582 Film Co", subgroup="xray_small", doc_kind="challan", challan_state="awaiting", total_amount=300.0, created="2031-06-08 10:00:00")
    f_asd, _ = rw.paper("WALK582 Film Co", status="rejected", subgroup="xray_small", total_amount=900.0, created="2031-06-09 10:00:00")
    p_stat, s_stat = rw.paper("WALK582 Envelopes", status="approved", subgroup="stationery", total_amount=1200.0, created="2031-06-08 11:00:00")
    p_pers, s_pers = rw.paper("WALK582 Personal shop", lane="owner_expense", subgroup="personal", total_amount=777.0, created="2031-06-09 11:00:00")
    p_wait, s_wait = rw.paper("WALK582 Envelopes", subgroup="stationery", doc_kind="challan", challan_state="awaiting", created="2031-06-10 11:00:00")
    p_spnd, s_spnd = rw.paper("WALK582 Engineer bill", status="approved", subgroup="others", total_amount=2500.0, created="2031-06-03 11:00:00")
    p_batt, s_batt = rw.paper("B.L. Computers WALK582", status="approved", subgroup="clinic_equipment", total_amount=20000.0, created="2031-06-05 11:00:00")
    p_stal, s_stal = rw.paper("WALK582 Old service bill", status="approved", subgroup="others", total_amount=650.0, created="2031-06-11 11:00:00")
    p_re, s_re = rw.paper("WALK582 To be re-issued", status="approved", subgroup="stationery", total_amount=333.0, created="2031-06-12 11:00:00")
    p_phar, s_phar = rw.paper("WALK582 Pharma", lane="pharmacy", total_amount=50.0, created="2031-06-12 12:00:00")
    room = rw.room("WALK582 X-ray room")
    a_fdr = rw.machine("WALK582 FDR detector", room, "2031-01-02 10:00:00", 500000.0)
    a_oth = rw.machine("WALK582 Other machine", room, "2031-01-02 11:00:00", 1000.0)
    a_fp = "2031-01-02 10:00:00"
    sp1 = rw.spend(a_fdr, "2031-06-03", 2500.0, bill=p_spnd, bill_fp=row(p_spnd)["created_at"])
    sp2 = rw.spend(a_fdr, "2031-04-20", 100.0, bill=p_stal, bill_fp="2001-01-01 00:00:00")            # a stale link: claims nothing
    rw.spend(a_oth, "2031-06-03", 999.0)                                                               # an unmarked machine
    cv1 = rw.cover(a_fdr, a_fp, "2031-06-01", "2032-05-31", 8000.0, bill=f_cov, bill_fp=row(f_cov)["created_at"])
    rw.cover(a_fdr, a_fp, "2031-06-02", "2032-06-01", 3000.0, voided="2031-06-02 12:00:00")              # voided: never counted
    cv3 = rw.cover(a_fdr, a_fp, "", "2031-12-31", 50.0, kind="other", at="2031-06-07 10:00:00")        # no from-date: its recorded month
    pl = rw.place("WALK582 X-ray UPS", "2031-01-03 10:00:00")
    ft1 = rw.fit(pl, "2031-06-05", 20000.0, bill=p_batt, bill_fp=row(p_batt)["created_at"])
    rw.fit(pl, "2031-06-06", 9999.0, voided="2031-06-06 12:00:00")                                    # voided: never counted
    watched = (p_stat, p_pers, p_wait, p_batt, p_stal, f_bill)
    before = {b_: row(b_) for b_ in watched}
    rec_before = (dict(db.execute("SELECT * FROM assets WHERE id=?", (a_fdr,)).fetchone()),
                  dict(db.execute("SELECT * FROM battery_place WHERE id=?", (pl,)).fetchone()),
                  dict(db.execute("SELECT * FROM battery_fit WHERE id=?", (ft1,)).fetchone()))
    print("made-up rows: 14 papers, 2 machines (3 spends, 3 covers), 1 battery place (2 fittings), June 2031")

    # ------------------------------------------------------------------ the first look, the ticks, the marks
    pg0r = own.get("/xray?ym=" + YM)
    pg0 = pg0r.get_data(as_text=True)
    mfold = pg0[pg0.find("id=s582mmarks"):pg0.find("</details>", pg0.find("id=s582mmarks"))] if "id=s582mmarks" in pg0 else ""
    i_fdr, i_oth = mfold.find(">WALK582 FDR detector"), mfold.find(">WALK582 Other machine")
    fdr_label = mfold[mfold.rfind("<label", 0, i_fdr):mfold.find("</label>", i_fdr)] if i_fdr >= 0 else ""
    sys_ticked = 'value="%d" checked' % a_fdr in fdr_label
    looks_first = 0 <= i_fdr < i_oth
    t1 = own.post("/xray/mark", data={"do": "ticks", "kind": "machine", "ym": YM, "listed": [str(a_fdr), str(a_oth)], "on": [str(a_fdr)]})
    fl_t1 = flashes(own)
    t2 = own.post("/xray/mark", data={"do": "ticks", "kind": "battery_place", "ym": YM, "listed": [str(pl)], "on": [str(pl)]})
    fl_t2 = flashes(own)
    mk_stat = mark_stamp("b" + digits(s_stat))
    mk_pers = mark_stamp(s_pers)
    mk_wait = mark_stamp("B" + digits(s_wait))
    mk_batt = mark_stamp(s_batt)
    mk_stal = mark_stamp(digits(s_stal))
    mk_film = mark_stamp(s_fbill)
    mk_re = mark_stamp(s_re)
    mk_phar = mark_stamp(s_phar)
    mk_again = mark_stamp(s_stat)
    live_p = quiet(lambda: sorted(xc.live_marks(db, "paper")), [])
    print("marks: ticks %s / %s ('%s' | '%s'); by stamp -- %s; pharmacy %s; again %s; live paper marks of ours %d"
          % (t1.status_code, t2.status_code, fl_t1, fl_t2,
             [(c_, (f_.replace(s_, "B-n"))[:60]) for (c_, f_), s_ in ((mk_stat, s_stat), (mk_pers, s_pers), (mk_wait, s_wait), (mk_batt, s_batt),
                                                                     (mk_stal, s_stal), (mk_film, s_fbill), (mk_re, s_re))],
             (mk_phar[0], mk_phar[1].replace(s_phar, "B-n")), (mk_again[0], mk_again[1].replace(s_stat, "B-n")),
             len([x for x in live_p if x in (p_stat, p_pers, p_wait, p_batt, p_stal, f_bill, p_re)])))

    # the re-issued id (S557 BL1): the paper p_re is deleted and its id given to a new paper
    re_old = row(p_re)
    db.execute("DELETE FROM bills WHERE id=?", (p_re,))
    s_re2 = rw.free_stamp()
    db.execute("INSERT INTO bills(id, kind, vendor, stamp_no, status, lane, created_at, submitted_at, submitted_by, bill_date, subgroup, total_amount) "
               "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (p_re, "Consumable", "WALK582 New paper on an old id", s_re2, "approved", "clinic",
                                                   "2031-06-13 09:09:09", "2031-06-13 09:09", "Walk", "2031-06-13", "stationery", 444.0))
    db.commit()

    pg = html(own, "/xray?ym=" + YM)
    v = quiet(view)
    secs = quiet(lambda: sd.month_data(db, YM, True)[0], [])
    month_films = next((s_["total"] for s_ in secs if s_["key"] == "xray"), None)
    month_films_ids = next((s_["money_ids"] for s_ in secs if s_["key"] == "xray"), [])
    after_ = {b_: row(b_) for b_ in watched}
    rec_after = (dict(db.execute("SELECT * FROM assets WHERE id=?", (a_fdr,)).fetchone()),
                 dict(db.execute("SELECT * FROM battery_place WHERE id=?", (pl,)).fetchone()),
                 dict(db.execute("SELECT * FROM battery_fit WHERE id=?", (ft1,)).fetchone()))
    aud = []
    try:
        for r_ in db.execute("SELECT action, detail FROM desk_audit WHERE action IN ('xray_mark','xray_unmark') ORDER BY id"):
            j_ = json.loads(r_[1] or "{}")
            aud.append((r_[0], j_.get("kind"), j_.get("ref")))
    except Exception:                                                      # noqa: BLE001
        pass

    def vpaper(bid):
        for r_ in (getattr(v, "papers", None) or []):
            if r_["b"]["id"] == bid:
                return r_
        return {}

    def vfilm(bid):
        for r_ in (getattr(v, "films", None) or []):
            if r_["b"]["id"] == bid:
                return r_
        return {}
    T = {k: tot(pg, k) for k in ("s582films", "s582papers", "s582machines", "s582batteries")}
    m_tot = re.search(r'id=s582tot data-total="([-\d.]+)" data-since="([-\d.]+)"', pg)
    print("X counts: page %s; fold totals %s; this month %s, since %s; The month's X-ray films %s (ids ours %s)"
          % (pg0r.status_code, T, m_tot.group(1) if m_tot else None, m_tot.group(2) if m_tot else None, month_films,
             sorted(x for x in month_films_ids if x in (f_bill, f_fin, f_cov, f_rct, f_wai, f_asd))))

    # ================================================================== X1 films by The month's rule
    ck("X1 X-ray films are read with The month's own rule: a bill, a final challan and a film paper are in (₹1,900, the same as The "
       "month's X-ray films section); a receipt, an awaiting challan and a set-aside paper are NOT; the fold shows The month's ₹1,900 "
       "and counts ₹1,500 -- the ₹400 film paper is the AMC cover's own paper (counted there, each rupee once), said in one line",
       lambda: month_films == 1900.0 and v.films_month_total == 1900.0 and v.films_total == 1500.0 and T["s582films"] == 1500.0
       and {f_bill, f_fin, f_cov} <= {r_["b"]["id"] for r_ in v.films} and not ({f_rct, f_wai, f_asd} & {r_["b"]["id"] for r_ in v.films})
       and vfilm(f_cov).get("claimed") is not None and 'data-v="1900.00"' in pg and ("₹400 of it (%s) is counted under" % s_fcov) in pg,
       lambda: (month_films, getattr(v, "films_month_total", None), getattr(v, "films_total", None), T, [r_["b"]["id"] for r_ in getattr(v, "films", [])]))

    # ================================================================== X2 a marked Stationery & packaging paper counted
    ck("X2 a paper marked for X-ray in Stationery & packaging (marked by its stamp typed 'b' + digits) is counted -- ₹1,200 -- and stays "
       "in its own group (the paper's whole row unchanged); every mark audited in desk_audit",
       lambda: mk_stat[0] == 302 and mk_stat[1].startswith("Marked %s for X-ray (June 2031)" % s_stat) and vpaper(p_stat).get("counted") is True
       and vpaper(p_stat).get("section") == "Stationery & packaging" and before[p_stat] == after_[p_stat] and before[p_stat]["subgroup"] == "stationery"
       and ("xray_mark", "paper", p_stat) in aud and ("xray_mark", "machine", a_fdr) in aud and ("xray_mark", "battery_place", pl) in aud
       and mk_again[1].startswith("%s is already marked" % s_stat) and s_stat in row_of(pg, "data-paper", p_stat),
       lambda: (mk_stat, vpaper(p_stat), aud[-12:], mk_again))

    # ================================================================== X3 not counted twice
    pr_film = vpaper(f_bill)
    ck("X3 a film paper also marked for X-ray is not counted twice: it is listed under the marked papers as 'already counted under X-ray "
       "films', at no amount; the marked papers' total is ₹1,850 (₹1,200 + ₹650) -- the stale-linked paper counts as a marked paper",
       lambda: pr_film.get("counted") is False and pr_film.get("why") == "already counted under X-ray films" and v.papers_total == 1850.0
       and T["s582papers"] == 1850.0 and vpaper(p_stal).get("counted") is True,
       lambda: (pr_film, getattr(v, "papers_total", None), T["s582papers"], vpaper(p_stal)))

    # ================================================================== X4 a machine's spend and cover, not its purchase price
    mrows = {(r_["src"], r_["id"]): r_ for r_ in (getattr(v, "machines", None) or [])}
    ck("X4 a machine marked for X-ray (ticked by the owner, never by the system: 'looks like X-ray — tick to count', listed before an "
       "ordinary machine): its June spend ₹2,500, its AMC cover ₹8,000 (from 01-06-2031) and a cover with no from-date ₹50 (its recorded "
       "month, said so) count -- ₹10,550; its April spend, its voided cover, its ₹5,00,000 purchase price and an unmarked machine's spend "
       "do not",
       lambda: pg0r.status_code == 200 and "looks like X-ray — tick to count" in fdr_label and not sys_ticked and looks_first
       and t1.status_code == 302 and "1 machine now count" in fl_t1 and v.machines_total == 10550.0 and T["s582machines"] == 10550.0
       and set(mrows) == {("spend", sp1), ("cover", cv1), ("cover", cv3)} and mrows[("cover", cv3)]["note"] == "no from-date"
       and "500000" not in json.dumps([r_["cost"] for r_ in mrows.values()]) and ("spend", sp2) not in mrows,
       lambda: (pg0r.status_code, fdr_label[:300], sys_ticked, looks_first, t1.status_code, fl_t1, getattr(v, "machines_total", None),
                {k: r_["cost"] for k, r_ in mrows.items()}))

    # ================================================================== X5 a battery fitting's price, not a voided one
    brows = [(r_["id"], r_["cost"]) for r_ in (getattr(v, "batteries", None) or [])]
    ck("X5 a battery place marked for X-ray: its fitting's price ₹20,000 counts; a voided fitting (₹9,999) does not",
       lambda: t2.status_code == 302 and brows == [(ft1, 20000.0)] and v.batteries_total == 20000.0 and T["s582batteries"] == 20000.0,
       lambda: (t2.status_code, fl_t2, brows))

    # ================================================================== X6 each rupee once
    pr_batt = vpaper(p_batt)
    bt_row = row_of(pg, "data-row", "battery-%d" % ft1)
    sp_row = row_of(pg, "data-row", "spend-%d" % sp1)
    ck("X6 each rupee once: the battery fitting's bill (also marked) is shown under the fitting 'its paper B-n' and listed under the "
       "marked papers 'its paper — counted under ...' at no amount; the spend's paper likewise; the April spend's link with a wrong "
       "fingerprint claims nothing (that paper still counts as a marked paper); the month's total is ₹33,900 = films ₹1,500 + papers "
       "₹1,850 + machines ₹10,550 + batteries ₹20,000",
       lambda: pr_batt.get("counted") is False and (pr_batt.get("why") or "").startswith("its paper — counted under WALK582 X-ray UPS")
       and s_batt in bt_row and "its paper" in bt_row and s_spnd in sp_row and v.total == 33900.0 and m_tot is not None
       and float(m_tot.group(1)) == 33900.0 and float(m_tot.group(2)) >= 33900.0 and "since" in pg[pg.find("id=s582tot"):pg.find("</p>", pg.find("id=s582tot"))],
       lambda: (pr_batt, bt_row[:400], sp_row[:400], getattr(v, "total", None), m_tot.groups() if m_tot else None))

    # ================================================================== X7 a manager: 403 and no menu item; the owner's menu order
    setting("batteries.on", "on")
    mg_get = mgr.get("/xray?ym=" + YM).status_code
    mg_post = mgr.post("/xray/mark", data={"do": "paper", "stamp": s_stat, "ym": YM}).status_code
    m_mgr = quiet(lambda: menu(mgr_u), [])
    m_own = quiet(lambda: menu(own_u), [])
    pg_mgr_bt = html(mgr, "/batteries")
    pg_mgr_mo = html(mgr, "/desk/month?ym=" + YM)
    setting("batteries.on", None)
    print("X7 counts: manager /xray %s, POST %s; manager's menu %s; owner's menu %s" % (mg_get, mg_post, " . ".join(m_mgr), " . ".join(m_own)))
    ck("X7 a manager (Batteries switched on for him) gets 403 on the page and on a mark, and no 'X-ray costs' in his menu; the owner's "
       "menu reads Machines . Batteries . X-ray costs . Renewals and the page's bar marks it as the page he is on",
       lambda: mg_get == 403 and mg_post == 403 and "X-ray costs" not in m_mgr and after(m_mgr, "Batteries", "Renewals")
       and after(m_own, "Machines", "Batteries") and after(m_own, "Batteries", "X-ray costs") and after(m_own, "X-ray costs", "Renewals")
       and 'data-s559="s582_xray" class=on' in pg and "X-ray costs" not in pg_mgr_bt,
       lambda: (mg_get, mg_post, m_mgr, m_own))

    # ================================================================== X8 a Personal paper
    pr_pers = vpaper(p_pers)
    ck("X8 a Personal paper is markable by the owner and listed on his page ('not counted: in no section of The month' -- shown, not "
       "added); a manager never sees it (403 on the page; not on his Batteries or The month pages); its row unchanged",
       lambda: mk_pers[0] == 302 and mk_pers[1].startswith("Marked %s" % s_pers) and pr_pers.get("counted") is False
       and pr_pers.get("why") == "not counted: in no section of The month" and s_pers in pg and mg_get == 403
       and s_pers not in pg_mgr_bt and s_pers not in pg_mgr_mo and before[p_pers] == after_[p_pers]
       and vpaper(p_wait).get("why") == "not counted: challan awaiting" and mk_phar[1].startswith("No paper %s that you may mark here" % s_phar),
       lambda: (mk_pers, pr_pers, vpaper(p_wait).get("why"), mk_phar))

    # ================================================================== X9 a re-issued id
    ck("X9 a re-issued id does not inherit a mark: the marked paper was deleted and its id given to a new paper -- the new paper is not "
       "listed, not counted, and its id is not a live mark",
       lambda: mk_re[0] == 302 and mk_re[1].startswith("Marked %s" % s_re) and re_old.get("created_at") == "2031-06-12 11:00:00"
       and vpaper(p_re) == {} and p_re not in quiet(lambda: xc.live_marks(db, "paper"), {p_re: 1}) and s_re2 not in pg,
       lambda: (mk_re, vpaper(p_re)))

    # ================================================================== X10 the seed (the data step), on a schema copy with made-up rows of the same names
    def schema_copy(path, paper=True, places=("Digital X-ray", "X-ray detector (FDR) battery")):
        c = sqlite3.connect(path)
        for t in ("bills", "battery_place", "desk_audit", "settings"):
            sql = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()[0]
            c.execute(sql)
        if paper:
            c.execute("INSERT INTO bills(kind, vendor, stamp_no, status, lane, created_at, subgroup, doc_kind, challan_state) "
                      "VALUES('Consumable','WALK582 Envelopes','B-0163','draft','clinic','2031-06-14 10:00:00','stationery','challan','awaiting')")
        for i, nm in enumerate(places):
            c.execute("INSERT INTO battery_place(grp, name, made_at) VALUES('online_ups', ?, ?)", (nm, "2031-06-0%d 10:00:00" % (i + 1)))
        c.execute("INSERT INTO battery_place(grp, name, made_at) VALUES('online_ups', 'WALK582 Other place', '2031-06-05 10:00:00')")
        c.commit(); c.close()

    def ensure_run(path):
        r_ = subprocess.run([sys.executable, "-B", os.path.join(appdir, "xray_costs.py"), "--ensure", path], capture_output=True, text=True, timeout=60)
        return r_.returncode, r_.stdout.strip().splitlines()

    def live(path):
        c = sqlite3.connect(path)
        try:
            return sorted(tuple(r_) for r_ in c.execute("SELECT kind, ref_id FROM xray_mark WHERE removed_at=''"))
        except sqlite3.Error:
            return None
        finally:
            c.close()
    sdir = os.path.join(work, "seed"); os.makedirs(sdir, exist_ok=True)
    s1 = os.path.join(sdir, "s1.db"); schema_copy(s1)
    e1 = ensure_run(s1); l1 = live(s1)
    e2 = ensure_run(s1); l2 = live(s1)
    c_ = sqlite3.connect(s1)
    try:                                                                   # the owner unmarks the second seeded place (absent on the FROM files)
        c_.execute("UPDATE xray_mark SET removed_at='2031-06-15 10:00:00', removed_by='Walk Owner' WHERE kind='battery_place' AND ref_id=2"); c_.commit()
    except sqlite3.Error as e:
        print("  (the owner's unmark on the seed copy: %s)" % e)
    c_.close()
    e3 = ensure_run(s1); l3 = live(s1)
    s2 = os.path.join(sdir, "s2.db"); schema_copy(s2, paper=False, places=("Digital X-ray",))
    e4 = ensure_run(s2); l4 = live(s2)
    s3 = os.path.join(sdir, "s3.db"); schema_copy(s3)
    procs = [subprocess.Popen([sys.executable, "-B", os.path.join(appdir, "xray_costs.py"), "--ensure", s3], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) for _ in range(2)]
    for p_ in procs:
        p_.communicate(timeout=60)
    l5 = live(s3)
    print("X10 counts: first run %s %s -> %s; second %s; after the owner unmarks a place: %s -> %s; no paper / one name absent: %s -> %s; "
          "two at once -> %s" % (e1[0], e1[1], l1, e2[1], e3[1], l3, e4[1], l4, l5))
    ck("X10 the seed (the installer's data step, xray_costs.py --ensure) on a schema copy with made-up rows of the same names: marks the "
       "paper B-0163 and the places 'Digital X-ray' and 'X-ray detector (FDR) battery' (no other place, no machine); a second run marks "
       "nothing; a seed the owner unmarked is never marked again; an absent paper or name is skipped with one line each; two runs at once "
       "give one live mark each",
       lambda: e1[0] == 0 and l1 == [("battery_place", 1), ("battery_place", 2), ("paper", 1)] and l2 == l1
       and any("already marked" in x for x in e2[1]) and l3 == [("battery_place", 1), ("paper", 1)]
       and any("unmarked by the owner, left unmarked" in x for x in e3[1])
       and l4 == [("battery_place", 1)] and "seed: no paper B-0163 -- not marked" in e4[1]
       and "seed: no battery place named 'X-ray detector (FDR) battery' -- skipped" in e4[1] and l5 == l1,
       lambda: (e1, l1, e2, l2, e3, l3, e4, l4, l5))

    # ================================================================== X11 The month, Batteries, a place and a machine byte-identical before / after
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
    same, diffs, removed = True, [], {}
    for k in ("owner:month", "owner:batteries", "owner:place", "owner:machine", "manager:month", "manager:batteries", "manager:place", "manager:machine"):
        a_, b_ = outs.get("from", {}).get(k), outs.get("to", {}).get(k)
        if not a_ or not b_ or a_[0] != 200 or b_[0] != 200:
            same = False; diffs.append((k, a_ and a_[0], b_ and b_[0])); continue
        tb = b_[1]
        n_ = len(XR_A.findall(tb))
        removed[k] = n_
        if k.startswith("owner:"):
            tb = XR_A.sub("", tb, count=1) if n_ == 1 else tb
            ok_ = n_ == 1 and tb == a_[1] and len(XR_A.findall(a_[1])) == 0
        else:
            ok_ = n_ == 0 and tb == a_[1]
        if not ok_:
            same = False
            i_ = next((j for j in range(min(len(tb), len(a_[1]))) if tb[j] != a_[1][j]), min(len(tb), len(a_[1])))
            diffs.append((k, n_, len(a_[1]), len(tb), a_[1][max(0, i_ - 80):i_ + 80], tb[max(0, i_ - 80):i_ + 80]))
    # the comparison itself can fail: the TO owner's Batteries page with one total changed (a made-up change) is NOT taken as identical
    mut_red = None
    try:
        a_, b_ = outs["from"]["owner:batteries"][1], outs["to"]["owner:batteries"][1]
        bm_ = XR_A.sub("", b_, count=1).replace("Battery places", "Battery placez", 1)
        mut_red = bm_ != a_
    except Exception:                                                      # noqa: BLE001
        mut_red = None
    print("X11 counts: FROM xray mounted %s, TO %s; the 'X-ray costs' bar element per page %s; a changed word on the TO page is caught %s"
          % (outs.get("from", {}).get("xray_mounted"), outs.get("to", {}).get("xray_mounted"), removed, mut_red))
    same = same and mut_red is True
    ck("X11 FROM and TO, each in a fresh process on two copies of the same database with the same made-up rows (today frozen, the month "
       "given): for a manager (desk, Batteries and machine pages switched on) The month, Batteries, a battery place and a machine page are "
       "byte-identical; for the owner they are identical after removing exactly ONE bar element, 'X-ray costs'",
       lambda: same and outs["to"].get("xray_mounted") is True and outs["from"].get("xray_mounted") is False,
       lambda: diffs[:4])

    # D664 / the marks never write the records
    print("records: marked papers' rows unchanged %s; the machine, the battery place and the fitting unchanged %s"
          % (all(before[b_] == after_[b_] for b_ in watched), rec_before == rec_after))
    if not (all(before[b_] == after_[b_] for b_ in watched) and rec_before == rec_after):
        ck("X2b marks never write bills, assets, battery_place or battery_fit", lambda: False)

    sp = opt("--save-pages")
    if sp:
        os.makedirs(sp, exist_ok=True)
        with open(os.path.join(sp, "s582_owner_xray.html"), "w", encoding="utf-8") as fh:
            fh.write(pg)
        print("pages saved: 1")
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
        print("CONTROL structural (green on both, named): %s" % ", ".join("%s %s" % (k, "GREEN" if seen_.get(k) else "RED") for k in ("W1", "Z1")))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
