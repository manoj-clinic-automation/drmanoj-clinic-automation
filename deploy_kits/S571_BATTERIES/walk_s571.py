#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s571.py -- the S571_BATTERIES walk. The app with the given files on a COPY of a database (SQLite's backup API), in its own
scratch folder; made-up rows only (suppliers 'B.L. Computers WALK571' / 'Jasoria WALK571 ..', stamps Z-2031-B.., machines 'WALK571 ..';
dated around a made-up today of 15-Jun-2031, injected), made-up logins (walk_own_2031 / walk_mgr_2031, made here; a reception user
stood in for by the walk); no reader thread, no paid call, nothing sent anywhere (a made-up key and URL). Flask's test client; no port.
Every place, fitting and paper the walk uses is found by its key (seed_key, stamp, the machine's name), never by counting rows.

    python3 -B walk_s571.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js, stationery.py [, batteries.py]> <assets.db to copy>
                            [--work DIR] [--shared DIR] [--expect-red [--must-red I8,I9]] [--keep] [--save-pages DIR]

One named check per brief item 1-6 (I1..I6), I7 (D664: a linked paper's lane, section and status unchanged; the picker's
visibility), I8 and I9 (S571_FIX1: no desk offer / pre-select for a manager while batteries.on is absent or OFF; a paper the viewer
may not see shows in a history with no amount and no link -- --must-red I8,I9 on the round-0 kit: those two RED, all others GREEN), W1, W2 and Z1 (structural: the database's shape after the mount -- only the three new tables, two indexes and the
batteries.since setting are new; no existing row changed). GREEN / RED; exit 1 on any RED. --expect-red (the control, on the live
FROM files -- no batteries.py): exit 0 only if every check named in MUST_RED is RED (W1 and Z1 are structural: green on both).
Counts are printed (never a live row's content). --save-pages DIR writes the owner's Batteries page and a place's history (made-up
rows) for the PC's browser walk at 1366 x 768."""
import datetime, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9")
if "--must-red" in ARGS:                   # S571_FIX1: the round-0 control names only the fix's checks (I8, I9); every other check must be GREEN
    MUST_RED = tuple(x for x in ARGS[ARGS.index("--must-red") + 1].split(",") if x)
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js", "stationery.py", "batteries.py")
SEEDS = {   # seed_key: (group, name, payer, supplier first word, warranty, life, owner only)
    "online_ups.digital_xray": ("online_ups", "Digital X-ray", "clinic", "bl", 12, 30, 0),
    "online_ups.nk_pathology": ("online_ups", "NK Pathology", "nk", "bl", 12, 30, 0),
    "online_ups.dth_lab": ("online_ups", "DTH lab", "confirm", "bl", 12, 30, 0),
    "small_ups.reception_pc": ("small_ups", "Reception PC", "clinic", "bl", 12, 30, 0),
    "small_ups.second_pc": ("small_ups", "Second PC", "clinic", "bl", 12, 30, 0),
    "small_ups.lab_analysers": ("small_ups", "Lab analysers", "nk", "bl", 12, 30, 0),
    "small_ups.home_dvr_router": ("small_ups", "Home DVR + router", "owner", "bl", 12, 30, 1),
    "gen_inv.generator": ("gen_inv", "Generator", "clinic", "jasoria", None, 30, 0),
    "gen_inv.clinic_inverter": ("gen_inv", "Clinic inverter", "clinic", "jasoria", None, 54, 0),
    "gen_inv.home_inverter": ("gen_inv", "Home inverter", "owner", "jasoria", None, 54, 1),
    "vehicles.carnival": ("vehicles", "Carnival", "owner", "jasoria", None, 42, 1),
    "vehicles.wagon_r": ("vehicles", "Wagon R", "owner", "jasoria", None, 42, 1),
    "vehicles.vento": ("vehicles", "Vento", "owner", "jasoria", None, 42, 1),
    "vehicles.scooty": ("vehicles", "Scooty", "owner", "jasoria", None, 30, 1),
    "vehicles.bike": ("vehicles", "Bike", "owner", "jasoria", None, 30, 1),
}


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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:900]) if (d and not ok) else ""))
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


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S571_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s571walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
    work = os.path.abspath(work)
    try:
        run(D, SRC, shared_src, work)
    finally:
        if "--keep" not in ARGS:
            shutil.rmtree(work, ignore_errors=True)


def run(D, SRC, shared_src, work):
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
    s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True); d = sqlite3.connect(dbp); s.backup(d); s.close(); d.close()
    shape0 = shape(dbp)
    env = setup_env(work)
    os.environ.update(env)
    for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(k, None)

    # ------------------------------------------------------------------ W: the import, isolated
    appdir = os.path.join(work, "app")
    if appdir not in sys.path:
        sys.path.insert(0, appdir)
    try:
        m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
    except Exception as e:                                                 # noqa: BLE001
        ck("W1 the app imports with these files", lambda: False, lambda: repr(e)); return
    cp = sys.modules.get("clinic_papers")
    sd = sys.modules.get("sorting_desk")
    am = sys.modules.get("asset_machine")
    st = sys.modules.get("stationery")
    bt = sys.modules.get("batteries")
    shape1 = shape(dbp)
    ck("W1 the app imports; asset_register, clinic_papers, sorting_desk, asset_machine, stationery come from the scratch folder; the "
       "database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and am is not None and under(am.__file__, appdir) and st is not None and under(st.__file__, appdir) and m.DB_PATH == dbp)
    ck("W2 the S571 marks: sorting_desk BATTERY, asset_register BATTERY_S571 = S571; batteries.py mounted from the scratch folder; "
       "the S568 / S566 / S563 / S560 / S559 / S557 / S555 / S551 marks kept",
       lambda: getattr(sd, "BATTERY", None) == "S571" and getattr(m, "BATTERY_S571", None) == "S571"
       and bt is not None and under(bt.__file__, appdir) and bt.MOUNTED and bt.VERSION == "S571"
       and sd.STOCK == "S568" and sd.STOCK_FIX == "S568_FIX1" and m.STOCK_S568 == "S568" and st.MOUNTED and st.VERSION == "S568"
       and sd.LAST == "S566" and m.LAST_S566 == "S566" and sd.TIDY == "S563" and sd.RECEIPTS == "S560"
       and sd.ROAD == "S559" and sd.MACHINE == "S557" and sd.CORRECTIONS == "S555" and sd.VERSION == "S551.2")
    # Z1 (structural): what the mount did to the database
    new_objs = shape1[0] - shape0[0]
    differ = sorted(t for t, n in shape0[1].items() if t != "settings" and shape1[1].get(t) != n)      # settings: compared by key below
    old_same = not differ
    set_new = {k: v for k, v in shape1[2].items() if k not in shape0[2]}
    set_same = all(shape1[2].get(k) == v for k, v in shape0[2].items())
    print("Z1 counts: new objects %s; every old table's row count kept %s%s; settings added %s; every old setting kept %s"
          % (sorted(n for _t, n in new_objs), old_same, (" (differ: %s)" % ", ".join(differ)) if differ else "", sorted(set_new), set_same))
    ck("Z1 (structural) the mount adds only the battery tables, their two indexes and the one setting batteries.since (when batteries.py "
       "is there); no existing table's rows and no existing setting changed",
       lambda: old_same and set_same and not (shape0[0] - shape1[0])
       and (new_objs == ({("table", "battery_place"), ("table", "battery_fit"), ("table", "battery_upkeep"), ("index", "battery_place_asset"),
                          ("index", "battery_fit_place")} if bt is not None else set()))
       and set(set_new) == ({"batteries.since"} if bt is not None else set()))

    sd.TODAY = TODAY
    am.TODAY = TODAY
    st.TODAY = TODAY
    if bt is not None:
        bt.TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    for k in ("desk.on", "machine.on", "desk.floor", "stationery.issue_on", "batteries.on"):
        db.execute("DELETE FROM settings WHERE key=?", (k,))
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
    db.commit()
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    own_u = db.execute("SELECT * FROM users WHERE username='walk_own_2031'").fetchone()
    mgr_u = db.execute("SELECT * FROM users WHERE username='walk_mgr_2031'").fetchone()
    rcp_u = {"id": None, "username": "walk_rcp_2031", "display_name": "Walk Reception", "role": "reception", "active": 1}

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

    def mk(tag, vendor, lane="clinic", status=None, created="2031-06-10 05:00:00", kind=None, **cols_):
        kd = kind or {"clinic": "Consumable", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st_ = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no="Z-2031-B" + tag, status=st_, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk", bill_date=created[:10])
        vals.update(cols_)
        bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        db.commit()
        return bid

    def post(cl, url, j):
        r_ = cl.post(url, json=j)
        return r_.status_code, (r_.get_json(silent=True) or {})

    def form(cl, url, data):
        return cl.post(url, data=data)

    def flashes(cl):
        with cl.session_transaction() as ss:
            f_ = list(ss.get("_flashes") or [])
            ss.pop("_flashes", None)
        return " | ".join(x[1] for x in f_)

    def paper(cl, bid):
        r_ = cl.get("/desk/api/paper/%d" % bid)
        return r_.status_code, (r_.get_json(silent=True) or {})

    def setting(k, v):
        if v is None:
            db.execute("DELETE FROM settings WHERE key=?", (k,))
        else:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
        db.commit()

    def pid(seed):
        try:
            r_ = db.execute("SELECT id FROM battery_place WHERE seed_key=?", (seed,)).fetchone()
        except sqlite3.Error:
            return None
        return r_[0] if r_ else None

    def cur_fit(p):
        try:
            r_ = db.execute("SELECT * FROM battery_fit WHERE place_id=? AND voided_at='' AND removed_on IS NULL ORDER BY fitted_on DESC, id DESC LIMIT 1",
                            (p,)).fetchone()
        except sqlite3.Error:
            return None
        return dict(r_) if r_ else None

    def view(seed):
        db2 = sqlite3.connect(dbp); db2.row_factory = sqlite3.Row
        try:
            p_ = bt.place(db2, pid(seed))
            return bt.place_view(db2, p_, TODAY)
        except Exception as e:                                             # noqa: BLE001
            print("  (view %s failed: %s)" % (seed, repr(e)[:160]))
            return {"badge": ("", ""), "await": "-", "upkeep_next": None}
        finally:
            db2.close()

    def card_of(page):
        i_ = page.find("id=s571card")
        return page[i_:page.find("</table></div>", i_)] if i_ >= 0 else ""

    exp0 = db.execute("SELECT COUNT(*) FROM expiries").fetchone()[0]

    def menu(u):
        with m.app.test_request_context("/"):
            from flask import g as g_
            g_.user = u
            return [x[1] for x in m._s559_items(u)]

    def after(lst, a, b):
        return a in lst and b in lst and lst.index(b) == lst.index(a) + 1

    def fit(cl, seed, **f_):
        return form(cl, "/batteries/fit/%s" % pid(seed), f_).status_code

    DX, NKP, DTH, RPC, SPC = "online_ups.digital_xray", "online_ups.nk_pathology", "online_ups.dth_lab", "small_ups.reception_pc", "small_ups.second_pc"
    GEN, CINV, HINV, WAG, CAR, HDVR = "gen_inv.generator", "gen_inv.clinic_inverter", "gen_inv.home_inverter", "vehicles.wagon_r", "vehicles.carnival", "small_ups.home_dvr_router"

    # ================================================================== I2 (item 2): the seeded places
    seed_rows = {}
    try:
        for r_ in db.execute("SELECT * FROM battery_place WHERE seed_key IS NOT NULL"):
            seed_rows[r_["seed_key"]] = dict(r_)
    except sqlite3.Error:
        pass
    bad = []
    for k, (gp, nm, py, s1, wm, lf, oo) in SEEDS.items():
        r_ = seed_rows.get(k)
        sup1 = (bt.sup1(r_["supplier"]) if (r_ and bt) else "")
        if not r_ or (r_["grp"], r_["name"], r_["payer"], sup1, r_["warranty_months"], r_["life_months"], r_["owner_only"]) != (gp, nm, py, s1, wm, lf, oo):
            bad.append(k)
    upk = {k: (r_["upkeep"], r_["upkeep_months"]) for k, r_ in seed_rows.items()}
    n_before = len(seed_rows)
    since0 = db.execute("SELECT value FROM settings WHERE key='batteries.since'").fetchone()
    again = quiet(lambda: bt.ensure_path(dbp), (None, None))
    n_after = quiet(lambda: db.execute("SELECT COUNT(*) FROM battery_place WHERE seed_key IS NOT NULL").fetchone()[0], None)
    since1 = db.execute("SELECT value FROM settings WHERE key='batteries.since'").fetchone()
    pg_dth = html(own, "/batteries")
    print("I2 counts: seeded places %s (wrong %s); a second ensure: %s -> %s; batteries.since kept %s; upkeep inverter %s, UPS %s, generator %s, car %s"
          % (n_before, bad, n_before, n_after, (since0 is not None and since0 == since1),
             upk.get(CINV), upk.get(DX), upk.get(GEN), upk.get(WAG)))
    ck("I2 (item 2) the seeded places: 3 online UPS, 4 small UPS, generator and 2 inverters, 5 vehicles -- each with its group, payer "
       "(DTH lab 'to confirm', shown so), supplier (B.L. Computers / Jasoria), warranty (B.L. 12, Jasoria empty), usual life (car 42, "
       "two-wheeler 30, inverter 54, UPS 30, generator 30) and owner-only flag; upkeep 3 / 3 / 1 months; a second run adds nothing",
       lambda: n_before == 15 and not bad and n_after == 15 and since0 is not None and since0 == since1
       and upk.get(CINV) == ("water", 3) and upk.get(DX) == ("backup", 3) and upk.get(GEN) == ("start", 1) and upk.get(WAG) == ("", None)
       and "paid by: to confirm" in pg_dth,
       lambda: (n_before, bad, n_after, upk.get(CINV), upk.get(GEN)))

    # ================================================================== I1 (item 1): the Batteries page
    r1 = own.get("/batteries")
    p1 = r1.get_data(as_text=True)
    m_own = quiet(lambda: menu(own_u), [])
    tot_words = ("Due for replacement", "Warranty ends within 30 days", "B.L. bill awaited", "Battery places")
    grp_words = ("Online UPS", "Small UPS", "Generator and inverters", "Vehicles")
    names_ok = all(v[1].replace("+", "&#43;") in p1 or v[1] in p1 for v in SEEDS.values())
    n_fit_btn = p1.count("New battery fitted")
    h1 = own.get("/batteries/place/%s" % pid(DX))
    h1t = h1.get_data(as_text=True)
    add = form(own, "/batteries/place", {"do": "add", "name": "WALK571 Spare UPS", "grp": "small_ups", "payer": "clinic", "sub": "Store"}).status_code
    added = quiet(lambda: dict(db.execute("SELECT * FROM battery_place WHERE name='WALK571 Spare UPS'").fetchone()), {})
    p1b = html(own, "/batteries")
    print("I1 counts: page %s; 'New battery fitted' buttons %d; menu %s; a place's history %s; added place %s (group %s, supplier %s, warranty %s)"
          % (r1.status_code, n_fit_btn, " . ".join(m_own), h1.status_code, add, added.get("grp"), added.get("supplier"), added.get("warranty_months")))
    ck("I1 (item 1) the Batteries page (owner): totals -- due for replacement, warranty ends within 30 days, B.L. bill awaited, battery "
       "places; the four groups with their notes; one row per place with 'New battery fitted'; '+ Add a battery place' adds one; the menu "
       "has Batteries right after Machines; tapping a place opens its history with the re-order line",
       lambda: r1.status_code == 200 and all(w in p1 for w in tot_words) and all(w in p1 for w in grp_words)
       and "B.L. Computers · warranty 1 year · bill with the battery" in p1 and "old battery paid back" in p1 and names_ok
       and n_fit_btn >= 15 and "+ Add a battery place" in p1 and after(m_own, "Machines", "Batteries") and after(m_own, "Batteries", "Renewals")
       and h1.status_code == 200 and "Re-order:" in h1t and "history" in h1t and "paid by Clinic" in h1t
       and add == 302 and added.get("grp") == "small_ups" and added.get("supplier") == "B.L. Computers" and added.get("warranty_months") == 12
       and "WALK571 Spare UPS" in p1b and re.search(r"<b>16</b>Battery places", p1b),
       lambda: (r1.status_code, [w for w in tot_words + grp_words if w not in p1], names_ok, n_fit_btn, m_own, h1.status_code, add, added))

    # ================================================================== I3 (item 3): New battery fitted
    flashes(own)
    fp = html(own, "/batteries/fit/%s" % pid(DX))
    a_dx = fit(own, DX, fitted_on="15-06-2031", supplier="B.L. Computers", warranty_months="12", set_n="3", brand="WalkBrand", bill="awaited")
    v_dx0 = quiet(lambda: view(DX), {})
    pg3 = html(own, "/batteries")
    bl1 = mk("BL1", "B.L. Computers WALK571", created="2031-06-14 09:00:00", total_amount=18500.0)
    before_bl1 = row(bl1)
    s_o, j_o = paper(own, bl1)
    offer = ((j_o.get("bat") or {}).get("offers") or [])
    off_dx = [o for o in offer if o.get("text") == "Battery fitted at Digital X-ray on 15-06-2031 — this bill?"]
    f_dx = cur_fit(pid(DX)) or {}
    s_l, j_l = post(own, "/batteries/link", {"fit": f_dx.get("id"), "paper": bl1, "as": "bill"})
    f_dx2 = cur_fit(pid(DX)) or {}
    v_dx1 = quiet(lambda: view(DX), {})
    s_o2, j_o2 = paper(own, bl1)
    bat2 = j_o2.get("bat") or {}
    after_bl1 = row(bl1)
    # Jasoria: Wagon R (owner only) -- price, old battery, net, the warranty typed from the card; bill and card
    fj = html(own, "/batteries/fit/%s" % pid(WAG))
    j1 = mk("JB1", "Jasoria Battery House WALK571", created="2031-06-09 09:00:00", total_amount=5000.0)
    j2 = mk("JC1", "JASORIA BATTERIES WALK571", created="2031-06-09 09:05:00")
    a_w1 = fit(own, WAG, fitted_on="10-06-2028", supplier="Jasoria", price="5,000", old_amount="800", warranty_months="24", brand="WalkJas", ah="35", bill=str(j1), card=str(j2))
    fw1 = cur_fit(pid(WAG)) or {}
    hw1 = html(own, "/batteries/place/%s" % pid(WAG))
    a_w2 = fit(own, WAG, fitted_on="15-06-2031", supplier="Jasoria", price="5200", old_amount="900", warranty_months="18", brand="WalkJas2")
    fut = fit(own, WAG, fitted_on="20-06-2031", price="1")
    f_fut = flashes(own)
    hw2 = html(own, "/batteries/place/%s" % pid(WAG))
    nw = quiet(lambda: db.execute("SELECT COUNT(*) FROM battery_fit WHERE place_id=?", (pid(WAG),)).fetchone()[0], 0)
    old_w = quiet(lambda: dict(db.execute("SELECT * FROM battery_fit WHERE id=?", (fw1.get("id"),)).fetchone()), {})
    print("I3 counts: B.L. form %s; fitted %s -> badge '%s', awaited %s; desk offer %s (%d offer(s)); link %s; bill %s; badge then '%s'; "
          "desk then: linked %s, pre '%s'; Jasoria form %s; first fitting %s (net shown %s, till %s); second %s; a future date %s; fittings %s; "
          "the first removed %s"
          % ("bill awaited" in fp, a_dx, (v_dx0.get("badge") or ("",))[0], v_dx0.get("await"), s_o, len(off_dx), s_l, f_dx2.get("bill_id") == bl1,
             (v_dx1.get("badge") or ("",))[0], bool(bat2.get("linked")), bat2.get("pre"), "Old battery ₹" in fj, a_w1, "₹4,200" in hw1,
             "10-06-2030" in hw1, a_w2, fut, nw, old_w.get("removed_on")))
    ck("I3 (item 3) New battery fitted: a B.L. place -- warranty 12 filled, 'bill awaited' until linked; a B.L. paper on the desk offers "
       "'Battery fitted at <place> on <date> — this bill?', one tap links it, no longer awaited, the desk then says it is linked and "
       "pre-selects Clinic equipment (the payer); a Jasoria place -- price, old-battery amount, net, warranty typed from the card, bill and "
       "card linked; a second fitting puts the first into the history with its removed date and how long it lasted; a future date refused",
       lambda: "New battery fitted — Digital X-ray" in fp and "UPS place · B.L. Computers" in fp and 'value="12"' in fp and "bill awaited" in fp
       and a_dx == 302 and v_dx0["badge"][0] == "Bill awaited 0 days" and v_dx0["await"] == 0 and "Bill awaited 0 days" in pg3
       and s_o == 200 and len(off_dx) == 1 and s_l == 200 and j_l.get("ok") and "unchanged" in (j_l.get("message") or "")
       and f_dx2.get("bill_id") == bl1 and f_dx2.get("bill_created_at") == "2031-06-14 09:00:00"
       and v_dx1["await"] is None and v_dx1["badge"][0] == "OK" and bat2.get("linked") and bat2.get("pre") == "clinic_equipment" and not bat2.get("offers")
       and "Vehicle place · Jasoria · yours only" in fj and "Price ₹" in fj and "Old battery ₹" in fj and "from the card" in fj
       and a_w1 == 302 and fw1.get("price") == 5000.0 and fw1.get("old_amount") == 800.0 and fw1.get("warranty_months") == 24
       and fw1.get("bill_id") == j1 and fw1.get("card_id") == j2 and "₹4,200" in hw1 and "price ₹5,000 − old battery ₹800" in hw1
       and "Z-2031-BJB1" in hw1 and "Z-2031-BJC1" in hw1
       and a_w2 == 302 and nw == 2 and old_w.get("removed_on") == "2031-06-15" and "36 months" in hw2 and "— in use" in hw2
       and "15-06-2031" in hw2 and fut == 302 and "after today" in f_fut,
       lambda: (a_dx, v_dx0.get("badge"), s_o, offer, s_l, j_l, f_dx2.get("bill_id"), v_dx1.get("badge"), bat2, a_w1, fw1, a_w2, nw, old_w, fut, f_fut))

    # ================================================================== I7 (D664): the linked paper unchanged; the picker's visibility
    jp = mk("JP1", "Jasoria WALK571 personal", lane="owner_expense", subgroup="personal", created="2031-06-11 09:00:00")
    jx = mk("JX1", "Jasoria WALK571 pharmacy", lane="pharmacy", created="2031-06-11 09:01:00")
    jq = mk("JQ1", "Jasoria WALK571 patient", subgroup="patient_paper", created="2031-06-11 09:02:00")
    jo = mk("JO1", "Jasoria WALK571 old", created="2031-01-02 09:00:00")
    a_ci = fit(own, CINV, fitted_on="01-01-2031", warranty_months="24", price="12000", old_amount="1500", set_n="2")
    pc = bt.place(db, pid(CINV)) if bt else None
    c_own = [c["id"] for c in (bt.candidates(db, pc, True, TODAY) if bt else [])]
    c_mgr = [c["id"] for c in (bt.candidates(db, pc, False, TODAY) if bt else [])]
    fci = cur_fit(pid(CINV)) or {}
    setting("batteries.on", "on")
    rows_b = {b_: row(b_) for b_ in (jp, j1, j2)}
    s_mp, j_mp = post(mgr, "/batteries/link", {"fit": fci.get("id"), "paper": jp, "as": "card"})
    s_op, j_op = post(own, "/batteries/link", {"fit": fci.get("id"), "paper": jp, "as": "card"})
    h_mgr_ci = html(mgr, "/batteries/place/%s" % pid(CINV))
    setting("batteries.on", None)
    rows_a = {b_: row(b_) for b_ in (jp, j1, j2)}
    same = before_bl1 == after_bl1 and all(rows_b[k] == rows_a[k] for k in rows_b)
    print("I7 counts: the linked B.L. paper lane %s -> %s, section %s -> %s, status %s -> %s (whole row unchanged %s); picker owner %s, manager %s "
          "(personal / pharmacy / patient / older than 90 days: owner %s %s %s %s, manager %s); a manager linking a Personal paper %s, the owner %s; "
          "the manager's history of that place shows it as 'a paper you do not see' %s"
          % (before_bl1.get("lane"), after_bl1.get("lane"), before_bl1.get("subgroup"), after_bl1.get("subgroup"), before_bl1.get("status"),
             after_bl1.get("status"), same, len(c_own), len(c_mgr), jp in c_own, jx in c_own, jq in c_own, jo in c_own, jp in c_mgr,
             s_mp, s_op, "a paper you do not see" in h_mgr_ci))
    ck("I7 (D664) linking never changes a paper: its lane, section and status (the whole row) unchanged; the picker follows the desk's "
       "visibility -- never a pharmacy or a patient paper, a Personal paper to the owner only, the last 90 days; a manager linking a "
       "Personal paper is refused, the owner's link keeps the paper as private as its section",
       lambda: same and before_bl1.get("status") == "draft" and a_ci == 302 and j1 in c_own and j2 in c_own and jp in c_own
       and jx not in c_own and jq not in c_own and jo not in c_own and jp not in c_mgr and j1 in c_mgr
       and s_mp == 400 and not j_mp.get("ok") and s_op == 200 and j_op.get("ok") and "a paper you do not see" in h_mgr_ci
       and "Z-2031-BJP1" not in h_mgr_ci,
       lambda: (same, c_own, c_mgr, s_mp, j_mp, s_op, j_op))

    # ================================================================== I4 (item 4): reminders into Renewals
    a_nk = fit(own, NKP, fitted_on="05-07-2030", warranty_months="12")                    # warranty ends in 20 days
    a_sp = fit(own, SPC, fitted_on="15-10-2028", warranty_months="12")                    # usual life (30) reached
    a_rp = fit(own, RPC, fitted_on="01-05-2031", warranty_months="12")                    # a B.L. bill awaited 45 days
    v_nk, v_sp, v_rp, v_ci = view(NKP), view(SPC), view(RPC), view(CINV)
    ren = html(own, "/renewals")
    ren_all = html(own, "/renewals?all=1")
    rem = bt.reminders(db, True, False, TODAY) if bt else []
    rem_all = bt.reminders(db, True, True, TODAY) if bt else []
    kinds = {(r_["place"], r_["kind"]) for r_ in rem}
    ci_due0 = ("Clinic inverter", "upkeep") in kinds
    tot4, _g4 = bt.overview(db, True, TODAY) if bt else ({}, [])
    dn = form(own, "/batteries/done", {"place": str(pid(CINV))}).status_code
    v_ci2 = view(CINV)
    kinds2 = {(r_["place"], r_["kind"]) for r_ in (bt.reminders(db, True, False, TODAY) if bt else [])}
    ups_n = quiet(lambda: db.execute("SELECT COUNT(*) FROM battery_upkeep WHERE place_id=?", (pid(CINV),)).fetchone()[0], 0)
    print("I4 counts: badges NK Pathology '%s', Second PC '%s', Reception PC '%s', Clinic inverter '%s'; due-soon reminders %d, all upcoming %d; "
          "kinds warranty %s, life %s, bill %s, upkeep %s; totals %s; done %s -> Clinic inverter '%s' (next %s), its upkeep reminder gone %s"
          % (v_nk["badge"][0], v_sp["badge"][0], v_rp["badge"][0], v_ci["badge"][0], len(rem), len(rem_all),
             ("NK Pathology", "warranty") in kinds, ("Second PC", "life") in kinds, ("Reception PC", "bill") in kinds, ci_due0, tot4, dn,
             v_ci2["badge"][0], v_ci2.get("upkeep_next"), ("Clinic inverter", "upkeep") not in kinds2))
    ck("I4 (item 4) reminders, computed when read, in the Renewals list as one 'Batteries' card: warranty ends in 30 days, usual life "
       "reached, a B.L. bill still awaited after 30 days, upkeep (inverter water, UPS backup check, generator start); ?all=1 shows every "
       "upcoming date; a 'done' tap resets the upkeep; nothing is written to expiries",
       lambda: a_nk == 302 and a_sp == 302 and a_rp == 302
       and v_nk["badge"][0] == "Warranty ends in 20 days" and v_sp["badge"][0] == "Due for replacement" and v_rp["badge"][0] == "Bill awaited 45 days"
       and v_ci["badge"][0] == "Water top-up due"
       and ("NK Pathology", "warranty") in kinds and ("Second PC", "life") in kinds and ("Reception PC", "bill") in kinds and ci_due0
       and ("Digital X-ray", "bill") not in kinds and len(rem_all) > len(rem)
       and "id=s571card" in ren and "Warranty ends — test the battery now" in ren and "Usual life reached — plan a replacement" in ren
       and "B.L. bill still awaited" in ren and "Inverter water" in ren and "Generator start test" in ren and "UPS backup check" in ren
       and ren_all.count("<tr") > ren.count("<tr")
       and tot4.get("due") == 1 and tot4.get("warranty") == 1 and tot4.get("awaited") == 3
       and dn == 302 and ups_n == 1 and v_ci2["badge"][0] == "OK" and v_ci2.get("upkeep_next") == datetime.date(2031, 9, 15)
       and ("Clinic inverter", "upkeep") not in kinds2
       and db.execute("SELECT COUNT(*) FROM expiries").fetchone()[0] == exp0,
       lambda: (v_nk.get("badge"), v_sp.get("badge"), v_rp.get("badge"), v_ci.get("badge"), sorted(kinds), tot4, dn, v_ci2.get("badge")))

    # ================================================================== I5 (item 5): a new machine's place, by itself
    since = (db.execute("SELECT value FROM settings WHERE key='batteries.since'").fetchone() or [""])[0]
    loc = db.execute("SELECT id FROM locations WHERE visibility='general' ORDER BY id LIMIT 1").fetchone()
    ent = quiet(lambda: db.execute("SELECT id FROM entities WHERE name='Dr Manoj Clinic'").fetchone(), None)
    acols = {r_[1] for r_ in db.execute("PRAGMA table_info(assets)")}

    def asset(name, cat, created, hidden=0):
        vals = {"name": name, "location_id": loc[0], "category": cat, "created_at": created, "hidden": hidden}
        if "entity_id" in acols and ent is not None:
            vals["entity_id"] = ent[0]
        a_ = db.execute("INSERT INTO assets(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        db.commit()
        return a_
    A1 = asset("WALK571 Online UPS X-ray room", "Electrical (Battery/Inverter/Stabilizer)", "2031-06-14 10:00:00")
    A2 = asset("WALK571 Stabilizer", "Electrical (Battery/Inverter/Stabilizer)", "2031-06-14 10:01:00")
    A3 = asset("WALK571 old UPS", "IT / Electronics", "2020-01-01 00:00:00")
    A4 = asset("WALK571 Car", "Vehicle", "2031-06-14 10:02:00")
    A5 = asset("WALK571 Inverter home", "Electrical (Battery/Inverter/Stabilizer)", "2031-06-14 10:03:00", hidden=1)

    def places_of(a_):
        try:
            return [dict(r_) for r_ in db.execute("SELECT * FROM battery_place WHERE asset_id=?", (a_,))]
        except sqlite3.Error:
            return []
    g1 = mgr.get("/batteries").status_code                                    # the switch is absent: refused, makes nothing
    n_g1 = len(places_of(A1))
    p5 = html(own, "/batteries")
    p5b = html(own, "/batteries")
    pl = {a_: places_of(a_) for a_ in (A1, A2, A3, A4, A5)}
    print("I5 counts: since set %s; manager (switch absent) %s made %d; places for the online UPS %d (group %s, supplier %s, payer %s), "
          "the stabilizer %d, the machine from before the install %d, the car %d (group %s, yours only %s), the hidden inverter %d (yours only %s); "
          "a second load made %s more"
          % (bool(since), g1, n_g1, len(pl[A1]), pl[A1][0]["grp"] if pl[A1] else "-", pl[A1][0]["supplier"] if pl[A1] else "-",
             pl[A1][0]["payer"] if pl[A1] else "-", len(pl[A2]), len(pl[A3]), len(pl[A4]), pl[A4][0]["grp"] if pl[A4] else "-",
             pl[A4][0]["owner_only"] if pl[A4] else "-", len(pl[A5]), pl[A5][0]["owner_only"] if pl[A5] else "-",
             "1 new place" in p5b or "new places made" in p5b))
    ck("I5 (item 5) a machine added in Machines after the install gets its battery place at the next page load, once: a whole-word UPS "
       "(Online UPS when it says online; B.L. Computers, warranty 12; payer from its entity), a Vehicle (Vehicles, yours only), an inverter "
       "(Generator and inverters; a hidden one yours only); a stabilizer and a machine from before the install get none; a second load "
       "makes nothing",
       lambda: bool(since) and g1 == 403 and n_g1 == 0
       and len(pl[A1]) == 1 and pl[A1][0]["grp"] == "online_ups" and pl[A1][0]["supplier"] == "B.L. Computers" and pl[A1][0]["warranty_months"] == 12
       and (pl[A1][0]["payer"] == "clinic" or ent is None) and pl[A1][0]["asset_created_at"] == "2031-06-14 10:00:00"
       and len(pl[A2]) == 0 and len(pl[A3]) == 0 and len(pl[A4]) == 1 and pl[A4][0]["grp"] == "vehicles" and pl[A4][0]["owner_only"] == 1
       and len(pl[A5]) == 1 and pl[A5][0]["grp"] == "gen_inv" and pl[A5][0]["owner_only"] == 1
       and "WALK571 Online UPS X-ray room" in p5 and "made from Machines just now" in p5 and "made from Machines just now" not in p5b,
       lambda: (since, g1, {k: [(x["grp"], x["owner_only"], x["payer"]) for x in v] for k, v in pl.items()}))

    # ================================================================== I6 (item 6): who sees what
    a_car = fit(own, CAR, fitted_on="01-06-2031")                                  # a Jasoria battery awaiting its bill, owner only
    j3 = mk("JB3", "Jasoria WALK571 three", created="2031-06-13 09:00:00")
    m_off = mgr.get("/batteries")
    m_off_t = m_off.get_data(as_text=True)
    m_off_pl = mgr.get("/batteries/place/%s" % pid(DX)).status_code
    m_off_ren = html(mgr, "/renewals")
    m_off_menu = quiet(lambda: menu(mgr_u), [])
    home = html(own, "/")
    sw = form(own, "/desk/switch", {"key": "batteries.on", "on": "1", "back": "/"}).status_code
    sw_v = db.execute("SELECT value FROM settings WHERE key='batteries.on'").fetchone()
    m_on = mgr.get("/batteries")
    m_on_t = m_on.get_data(as_text=True)
    m_on_menu = quiet(lambda: menu(mgr_u), [])
    m_on_ren = html(mgr, "/renewals")
    m_wag = mgr.get("/batteries/place/%s" % pid(WAG)).status_code
    m_wag_fit = form(mgr, "/batteries/fit/%s" % pid(WAG), {"fitted_on": "15-06-2031"}).status_code
    m_hinv_done = form(mgr, "/batteries/done", {"place": str(pid(HINV))}).status_code
    fwag = cur_fit(pid(WAG)) or {}
    m_wag_link, j_wl = post(mgr, "/batteries/link", {"fit": fwag.get("id"), "paper": j3, "as": "bill"})
    s_j3o, j_j3o = paper(own, j3)
    s_j3m, j_j3m = paper(mgr, j3)
    off_o = [o["text"] for o in ((j_j3o.get("bat") or {}).get("offers") or [])]
    off_m = [o["text"] for o in ((j_j3m.get("bat") or {}).get("offers") or [])]
    m_add = form(mgr, "/batteries/place", {"do": "add", "name": "WALK571 Lab UPS two", "grp": "small_ups", "payer": "owner", "owner_only": "1"}).status_code
    m_added = quiet(lambda: dict(db.execute("SELECT * FROM battery_place WHERE name='WALK571 Lab UPS two'").fetchone()), {})
    m_edit = form(mgr, "/batteries/place", {"do": "edit", "id": str(pid(DTH)), "payer": "clinic"}).status_code
    dth_payer = db.execute("SELECT payer FROM battery_place WHERE id=?", (pid(DTH),)).fetchone()[0] if pid(DTH) else None
    orig_cu = m.current_user
    m.current_user = lambda: rcp_u
    try:
        rc1 = m.app.test_client().get("/batteries").status_code
        rc2 = m.app.test_client().get("/batteries/place/%s" % pid(DX)).status_code
        rc3 = m.app.test_client().post("/batteries/link", json={"fit": 1, "paper": j3}).status_code
    finally:
        m.current_user = orig_cu
    hidden_words = ("Carnival", "Wagon R", "Vento", "Scooty", "Home inverter", "Home DVR", "WALK571 Car", "WALK571 Inverter home")
    shown_words = ("Digital X-ray", "NK Pathology", "DTH lab", "Reception PC", "Second PC", "Lab analysers", "Generator", "Clinic inverter",
                   "WALK571 Online UPS X-ray room")
    print("I6 counts: manager, switch absent: page %s, a place %s, Renewals card %s, menu has Batteries %s; his Switches card has the row %s; "
          "switched ON %s (%s); manager then: page %s, menu %s, Renewals card %s; owner-only place %s, its fit %s, its upkeep %s, a link to it %s; "
          "desk offers for a Jasoria paper: owner %d, manager %d; manager's added place owner-only %s payer %s; manager's edit %s (DTH payer %s); "
          "reception %s / %s / %s"
          % (m_off.status_code, m_off_pl, "id=s571card" in m_off_ren, "Batteries" in m_off_menu, "Batteries for Shavez" in home, sw,
             sw_v[0] if sw_v else None, m_on.status_code, " . ".join(m_on_menu), "id=s571card" in m_on_ren, m_wag, m_wag_fit, m_hinv_done,
             m_wag_link, len(off_o), len(off_m), m_added.get("owner_only"), m_added.get("payer"), m_edit, dth_payer, rc1, rc2, rc3))
    ck("I6 (item 6) who sees what: the owner everything; a manager refused while batteries.on is absent (page, places, Renewals card, "
       "menu), and once the owner switches it ON (a row 'Batteries for Shavez' on his Switches card) the clinic and lab places only -- "
       "owner-only places, their fittings, upkeep, links and desk offers refused server-side; a manager cannot make a place 'yours only' or "
       "change a place's payer; the reception login never",
       lambda: m_off.status_code == 403 and "band hai" in m_off_t and m_off_pl == 403 and "id=s571card" not in m_off_ren and "Batteries" not in m_off_menu
       and "Batteries for Shavez" in home and sw == 302 and sw_v is not None and sw_v[0] == "on"
       and m_on.status_code == 200 and all(w in m_on_t for w in shown_words) and not any(w in m_on_t for w in hidden_words)
       and after(m_on_menu, "Machines", "Batteries") and "id=s571card" in m_on_ren and "Reception PC" in card_of(m_on_ren)
       and not any(w in card_of(m_on_ren) for w in ("Wagon R", "Home inverter", "Carnival", "Home DVR", "WALK571 Car"))
       and m_wag == 403 and m_wag_fit == 403 and m_hinv_done == 403 and m_wag_link == 403
       and s_j3o == 200 and s_j3m == 200 and "Battery fitted at Carnival on 01-06-2031 — this bill?" in off_o
       and not any("Carnival" in t for t in off_m) and a_car == 302
       and m_add == 302 and m_added.get("owner_only") == 0 and m_added.get("payer") == "confirm" and m_edit == 403 and dth_payer == "confirm"
       and rc1 == 403 and rc2 == 403 and rc3 == 403,
       lambda: (m_off.status_code, m_off_pl, m_off_menu, sw, m_on.status_code, [w for w in shown_words if w not in m_on_t],
                [w for w in hidden_words if w in m_on_t], m_on_menu, m_wag, m_wag_fit, m_hinv_done, m_wag_link, off_o, off_m, m_added, m_edit, rc1, rc2, rc3))

    # ================================================================== I8 (S571_FIX1, K1 Correction 1): the desk while batteries.on is OFF
    a_dvr = fit(own, HDVR, fitted_on="01-06-2031", warranty_months="12")          # a B.L. battery awaiting its bill, owner only
    bl8 = mk("BL8", "B.L. Computers WALK571 eight", created="2031-06-14 10:00:00")
    st8 = {}
    for sw8 in (None, "off", "on"):
        setting("batteries.on", sw8)
        s8m, j8m = paper(mgr, bl8)
        s8l, j8l = paper(mgr, bl1)                                                    # linked to Digital X-ray, not sorted yet
        s8o, j8o = paper(own, bl8)
        st8[sw8] = {"s": (s8m, s8l, s8o), "m_bat": "bat" in j8m, "m_off": [o["text"] for o in ((j8m.get("bat") or {}).get("offers") or [])],
                    "l_bat": "bat" in j8l, "l_pre": (j8l.get("bat") or {}).get("pre"),
                    "o_off": [o["text"] for o in ((j8o.get("bat") or {}).get("offers") or [])]}
    clinic_names = ("NK Pathology", "Second PC", "Reception PC")
    print("I8 counts: manager's desk, B.L. paper / the linked paper -- switch absent: bat %s / %s (offers %d, pre %s); OFF: bat %s / %s "
          "(offers %d, pre %s); ON: offers %d (owner-only among them %s), pre %s; the owner's offers %d each time (%s), Home DVR among them %s"
          % (st8[None]["m_bat"], st8[None]["l_bat"], len(st8[None]["m_off"]), st8[None]["l_pre"], st8["off"]["m_bat"], st8["off"]["l_bat"],
             len(st8["off"]["m_off"]), st8["off"]["l_pre"], len(st8["on"]["m_off"]), any("Home DVR" in t for t in st8["on"]["m_off"]),
             st8["on"]["l_pre"], len(st8["on"]["o_off"]), "/".join(str(len(st8[k]["o_off"])) for k in (None, "off", "on")),
             any("Home DVR" in t for t in st8[None]["o_off"])))
    ck("I8 (S571_FIX1, K1 C1) a manager's sorting desk shows no battery offer and no pre-selection while batteries.on is absent or OFF; "
       "with it ON he gets the offers for clinic and lab places only, and the linked paper's payer pre-select; the owner always",
       lambda: a_dvr == 302 and all(st8[k]["s"] == (200, 200, 200) for k in st8)
       and not st8[None]["m_bat"] and not st8[None]["l_bat"] and not st8["off"]["m_bat"] and not st8["off"]["l_bat"]
       and st8["on"]["m_bat"] and all(any(("at %s on" % n) in t for t in st8["on"]["m_off"]) for n in clinic_names)
       and not any(w in t for t in st8["on"]["m_off"] for w in ("Home DVR", "Carnival", "Wagon R", "Home inverter"))
       and st8["on"]["l_pre"] == "clinic_equipment"
       and all(any("Home DVR" in t for t in st8[k]["o_off"]) and len(st8[k]["o_off"]) == len(st8["on"]["m_off"]) + 1 for k in st8),
       lambda: st8)

    # ================================================================== I9 (S571_FIX1, K1 Note 2): a paper the viewer may not see, in a history
    setting("batteries.on", "on")
    gp9 = mk("GP9", "Jasoria WALK571 gen personal", lane="owner_expense", subgroup="personal", created="2031-06-12 09:00:00", total_amount=7350.0)
    gc9 = mk("GC9", "Jasoria WALK571 gen card", lane="owner_expense", subgroup="personal", created="2031-06-12 09:05:00")
    a_gen = fit(own, GEN, fitted_on="12-06-2031", warranty_months="18", bill=str(gp9), card=str(gc9))      # no price typed: cost = the bill's
    fgen = cur_fit(pid(GEN)) or {}
    h9m = html(mgr, "/batteries/place/%s" % pid(GEN))
    h9o = html(own, "/batteries/place/%s" % pid(GEN))

    def hist_of(page):
        i_ = page.find("id=s571hist")
        return page[i_:page.find("</table>", i_)] if i_ >= 0 else ""
    t9m, t9o = hist_of(h9m), hist_of(h9o)
    hrefs9 = [h_ for h_ in re.findall(r'<a href="([^"]*)"', t9m)]
    print("I9 counts: the Generator's fitting with a Personal bill (₹7,350) and card linked %s; manager's history: amount shown %s, stamps shown %s, "
          "'a paper' lines %d, links in the table %d; the owner's: amount %s, stamps %s, links %d"
          % (a_gen == 302 and fgen.get("bill_id") == gp9 and fgen.get("card_id") == gc9, "7,350" in t9m, ("Z-2031-BGP9" in t9m or "Z-2031-BGC9" in t9m),
             t9m.count("a paper"), len(hrefs9), "7,350" in t9o, ("Z-2031-BGP9" in t9o and "Z-2031-BGC9" in t9o), len(re.findall(r"<a href=", t9o))))
    ck("I9 (S571_FIX1, K1 N2) a place's history shows a paper's amount and its link only to a viewer who may see the paper: a manager "
       "viewing a clinic place whose bill and card are Personal papers sees 'a paper', no amount, no link; the owner sees both",
       lambda: a_gen == 302 and fgen.get("bill_id") == gp9 and fgen.get("card_id") == gc9
       and "Generator" in h9m and "id=s571hist" in h9m and "7,350" not in h9m and "Z-2031-BGP9" not in h9m and "Z-2031-BGC9" not in h9m
       and t9m.count("a paper") >= 2 and not hrefs9 and '<a href=""' not in h9m
       and "₹7,350 (the bill)" in t9o and "Z-2031-BGP9" in t9o and "Z-2031-BGC9" in t9o and len(re.findall(r'<a href="[^"]+">Z-2031-BG', t9o)) == 2,
       lambda: (a_gen, fgen, t9m[-900:]))

    # ------------------------------------------------------------------ pages for the PC's browser walk (made-up rows)
    sp = opt("--save-pages")
    if sp:
        os.makedirs(sp, exist_ok=True)
        for nm, url in (("batteries_owner.html", "/batteries"), ("batteries_place.html", "/batteries/place/%s" % pid(WAG)),
                        ("batteries_fit_bl.html", "/batteries/fit/%s" % pid(DX)), ("batteries_fit_jasoria.html", "/batteries/fit/%s" % pid(WAG))):
            with open(os.path.join(sp, nm), "w", encoding="utf-8") as fh:
                fh.write(html(own, url))
        with open(os.path.join(sp, "batteries_manager.html"), "w", encoding="utf-8") as fh:
            fh.write(html(mgr, "/batteries"))
        print("pages saved: 5")
    setting("batteries.on", None)
    db.close()


if __name__ == "__main__":
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
        if "--must-red" in ARGS:
            other_red = [k for k in FAILED if k not in MUST_RED]
            print("CONTROL every other check GREEN: %s" % ("yes" if not other_red else "NO -- red: " + ", ".join(other_red)))
            sys.exit(0 if (reds and not not_red and not other_red) else 1)
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
