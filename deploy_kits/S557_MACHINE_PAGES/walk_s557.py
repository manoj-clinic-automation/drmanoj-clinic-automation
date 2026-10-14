#!/usr/bin/env python3
"""walk_s557.py -- the S557_MACHINE_PAGES walk. The app with the given files on a COPY of a database (SQLite's backup API), in
its own scratch folder; made-up rows only (machines WALK S557 .., suppliers and providers WALK.., stamps Z-2031-S7.., dated
around a made-up today of 15-Jun-2031), made-up logins; no reader thread, no paid call, nothing sent anywhere (a made-up key
and URL). Flask's test client; no port. Isolated exactly as walk_s555.py (S551 v4 s6).

    python3 -B walk_s557.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py
                            [, asset_machine.py]> <assets.db to copy> [--work DIR] [--shared DIR]
                            [--dump FILE | --baseline FILE] [--expect-red] [--keep]

--dump FILE: write the pages that must not change (reception's intake; a manager's machine page with the switch absent) as
             they are on these files, then stop (run on the LIVE files first).
--baseline FILE: compare those pages byte for byte with the dump.
GREEN / RED per check; exit 1 on any RED. --expect-red (the control on the old files): exit 0 only if every check named in
MUST_RED is RED. The work folder (default: a new folder under /tmp) is removed at the end unless --keep."""
import datetime, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile, time

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
# W3 (the schema) is not here: it reads the database, and a copy taken after an earlier install already has the additive tables.
MUST_RED = ("W2", "A1a", "A1b", "A1c", "A1d", "A1e", "A1f", "A2a", "A2b", "A3a", "A3b", "A3c", "A4a", "A4b", "A5a", "A5b",
            "A6a", "A6b", "A6c", "A6d", "A6e", "A7b", "A7c", "B1a", "B1b", "B1c", "B1d", "B2", "B3")
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py")
LONG = re.compile(r"Clinic bill|asset or consumable|Pharmacy purchase|Lab purchase|not a bill")


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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:300]) if (d and not ok) else ""))
    return ok


def quiet(fn, default=None):
    try:
        return fn()
    except Exception as e:                                                 # noqa: BLE001
        print("  (step failed: %s)" % repr(e)[:160])
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


def visible(html):
    t = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S557_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s557walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
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
    if os.path.isdir(shared_src):
        for f in os.listdir(shared_src):
            if f.endswith(".py"):
                shutil.copy(os.path.join(shared_src, f), os.path.join(work, "shared", f))
    with open(os.path.join(work, "key", "anthropic.key"), "w") as fh:
        fh.write("sk-ant-walk-made-up-" + "0" * 12 + "\n")
    dbp = os.path.join(work, "assets.db")
    s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True); d = sqlite3.connect(dbp); s.backup(d); s.close(); d.close()
    c = sqlite3.connect(dbp)
    for k in ("desk.on", "machine.on", "d710.challan_amber_days", "desk.floor", "desk.s441_days"):
        c.execute("DELETE FROM settings WHERE key=?", (k,))
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    if not c.execute("SELECT 1 FROM users WHERE username='walk_mgr_2031'").fetchone():
        c.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_mgr_2031','Walk Manager','manager','x',1)")
    if not c.execute("SELECT 1 FROM users WHERE role='owner' AND active=1").fetchone():
        c.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_2031','Walk Owner','owner','x',1)")
    c.commit(); c.close()
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
    ck("W1 the app imports; asset_register, clinic_papers, claude_reader, sorting_desk (and asset_machine when given) come from the scratch folder",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and under(m.CLAUDE.__file__, appdir) and sd is not None
       and under(sd.__file__, appdir) and (am is None or under(am.__file__, appdir)))
    ck("W2 asset_machine S557 is mounted; sorting_desk carries MACHINE = S557 (VERSION S551.2 and CORRECTIONS S555 kept)",
       lambda: am is not None and am.VERSION == "S557" and am.MOUNTED and getattr(sd, "MACHINE", None) == "S557"
       and sd.VERSION == "S551.2" and sd.CORRECTIONS == "S555")
    ck("W4 the shared modules come from the scratch copy; no finance database is reachable",
       lambda: (m.S441 is None or under(m.S441.__file__, os.path.join(work, "shared"))) and (m.SARVAM is None or under(m.SARVAM.__file__, os.path.join(work, "shared")))
       and (m.S441 is None or not os.path.exists(m.S441.FIN_DB)) and m.DB_PATH == dbp and m.UPLOAD_DIR == env["ASSETS_UPLOADS"])
    sd.TODAY = TODAY
    if am is not None:
        am.TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()

    def cols(t):
        return [r[1] for r in db.execute("PRAGMA table_info(%s)" % t)]
    ck("W3 the additive schema: asset_part and asset_cover exactly as the brief; service_logs.bill_id (A4)",
       lambda: cols("asset_part") == ["id", "asset_id", "name", "make", "model", "serial", "fitted_on", "warranty_till", "bill_id",
                                      "removed_on", "removed_by", "expiry_id", "by_whom", "at"]
       and cols("asset_cover") == ["id", "asset_id", "kind", "provider", "from_day", "till_day", "cost", "bill_id", "remind_days",
                                   "expiry_id", "voided_at", "voided_by", "by_whom", "at"]
       and "bill_id" in cols("service_logs"), lambda: (cols("asset_part"), cols("asset_cover"), cols("service_logs")))

    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    own_u = db.execute("SELECT * FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone()
    mgr_u = db.execute("SELECT * FROM users WHERE username='walk_mgr_2031'").fetchone()
    state = {"m": m}

    def client(u):
        cl = state["m"].app.test_client()
        if u is not None:
            with cl.session_transaction() as ss:
                ss["uid"] = u["id"]; ss["epoch"] = epoch
        return cl
    own, mgr, anon = client(own_u), client(mgr_u), client(None)
    rec = {"id": None, "username": "walkrec", "display_name": "Walkrec", "role": "reception", "active": 1}

    def as_reception(fn):
        mm = state["m"]
        real = mm.current_user
        mm.current_user = lambda: rec
        try:
            return fn()
        finally:
            mm.current_user = real

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    gen = db.execute("SELECT id FROM locations WHERE visibility='general' ORDER BY id LIMIT 1").fetchone()[0]
    ent = db.execute("SELECT id FROM entities WHERE name='Dr Manoj Clinic'").fetchone()
    entid = ent[0] if ent else None

    def mach(tag, **cols_):
        vals = dict(name="WALK S557 MACHINE " + tag, location_id=gen, category="Dr MK Clinic Equipment", status="Active",
                    contract_type="None", entity_id=entid, kind="Asset")
        vals.update(cols_)
        aid = db.execute("INSERT INTO assets(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        db.commit()
        return aid

    def mk(tag, vendor=None, lane="clinic", status=None, created="2031-06-10 05:00:00", kind=None, items=(), **cols_):
        kd = kind or {"clinic": "Consumable", "other_doc": "Document", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no="Z-2031-S7" + tag, status=st, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk")
        vals.update(cols_)
        bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        for it in items:
            db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (bid, it[0], it[1], it[2] if len(it) > 2 else None, None))
        db.commit()
        return bid

    def reading(bid, raw_json, ok=1, kind="tax_invoice"):
        db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,?,?,?)",
                   (bid, "2031-06-12 10:00", "walk", ok, kind, raw_json))
        db.commit()

    def one(sql, *a):
        try:
            r = db.execute(sql, a).fetchone()
            return r[0] if r else None
        except sqlite3.Error as e:
            return "ERR " + str(e)

    # ------------------------------------------------------------------ K: the pages that must not change (vs the live files)
    old_a = mach("OLD", purchase_date="2030-02-01", price=100000, vendor="WALKV VENDOR ONE", serial_no="SN-OLD-1",
                 contract_type="AMC", provider="WALKOLD SERVICES", contract_cost=5000)
    db.execute("INSERT INTO service_logs(asset_id, log_date, work, cost, done_by, is_pm, svc_type) VALUES(?,?,?,?,?,0,'Repair')",
               (old_a, "2031-03-04", "walk fan replaced", 1200, "WALKTECH"))
    db.commit()
    snap_old = dict(db.execute("SELECT * FROM assets WHERE id=?", (old_a,)).fetchone())
    pages = {"intake": as_reception(lambda: html(client(None), "/intake")), "mgr_machine": html(mgr, "/assets/%d" % old_a)}
    if opt("--dump"):
        with open(opt("--dump"), "w", encoding="utf-8") as fh:
            json.dump(pages, fh)
        print("DUMPED the unchanged-pages baseline (%d B intake, %d B machine page)" % (len(pages["intake"]), len(pages["mgr_machine"])))
        db.close()
        return
    base = {}
    if opt("--baseline") and os.path.exists(opt("--baseline")):
        base = json.load(open(opt("--baseline"), encoding="utf-8"))
    ck("K1 machine.on absent: a manager's machine page is byte-for-byte the page the live files give (A7)",
       lambda: base.get("mgr_machine") is not None and pages["mgr_machine"] == base["mgr_machine"] and "s557" not in pages["mgr_machine"],
       lambda: ("no baseline" if not base else (len(pages["mgr_machine"]), len(base.get("mgr_machine", "")))))
    ck("K2 reception's intake: byte-for-byte the HTML the live files give (B1: staff words unchanged)",
       lambda: base.get("intake") is not None and pages["intake"] == base["intake"] and "Clinic bill" in pages["intake"],
       lambda: ("no baseline" if not base else (len(pages["intake"]), len(base.get("intake", "")))))

    # ------------------------------------------------------------------ A7 (OFF): the owner has it at once, a manager does not
    t_own0 = html(own, "/assets/%d" % old_a)
    r_mgr_off = mgr.post("/assets/%d/parts/add" % old_a, data={"name": "WALK PART OFF"})
    n_off = one("SELECT COUNT(*) FROM asset_part WHERE name='WALK PART OFF'")
    ck("A7a switch absent: the owner sees the new sections at once; a manager's write is refused (403) and nothing is written",
       lambda: "id=s557top" in t_own0 and "id=s557parts" in t_own0 and r_mgr_off.status_code == 403 and n_off == 0,
       lambda: ("id=s557top" in t_own0, r_mgr_off.status_code, n_off))

    # ------------------------------------------------------------------ A1: the cover line in its states, the totals, the price rule
    m_none = mach("NONE", purchase_date="2030-02-01", price=100000)
    m_live = mach("LIVE", purchase_date="2030-02-01", price=100000)
    m_soon = mach("SOON")
    m_laps = mach("LAPSED")
    m_hide = mach("HIDE", purchase_date="2030-02-01", price=250000, hide_price=1)
    own.post("/assets/%d/covers/add" % m_live, data={"kind": "amc", "provider": "WALKPROV ONE", "from_day": "15-06-2031", "till_day": "14-06-2032", "cost": "12000"})
    own.post("/assets/%d/covers/add" % m_soon, data={"kind": "warranty", "till_day": "01-07-2031"})
    own.post("/assets/%d/covers/add" % m_laps, data={"kind": "cmc", "provider": "WALKPROV TWO", "till_day": "01-05-2031"})
    own.post("/assets/%d/covers/add" % m_hide, data={"kind": "amc", "provider": "WALKPROV THREE", "till_day": "14-06-2032", "cost": "9000"})
    own.post("/assets/%d/service" % m_live, data={"log_date": "2031-02-02", "svc_type": "Repair", "work": "walk board fixed", "cost": "3000"})
    own.post("/assets/%d/service" % m_live, data={"log_date": "2031-04-04", "svc_type": "Preventive maintenance", "work": "walk PM visit"})
    own.post("/assets/%d/service" % m_hide, data={"log_date": "2031-02-02", "svc_type": "Repair", "work": "walk hidden repair", "cost": "7000"})

    def cov(t):
        mm_ = re.search(r'<div id=s557cover class="([^"]*)"[^>]*>(.*?)</div>', t, re.S)
        return (mm_.group(1), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", mm_.group(2))).strip()) if mm_ else (None, "")

    def tot(t):
        mm_ = re.search(r"<div id=s557totals[^>]*>(.*?)</div>", t, re.S)
        return mm_.group(1).strip() if mm_ else ""
    tn, tl, ts, tp = (html(own, "/assets/%d" % x) for x in (m_none, m_live, m_soon, m_laps))
    ck("A1a no cover: 'No cover', neither amber nor red", lambda: cov(tn) == ("", "No cover"), lambda: cov(tn))
    ck("A1b a live cover: 'Covered: AMC by WALKPROV ONE till 14-06-2032'", lambda: cov(tl) == ("", "Covered: AMC by WALKPROV ONE till 14-06-2032"), lambda: cov(tl))
    ck("A1c within 30 days of its end: amber, 'Under warranty till 01-07-2031 -- 16 days left'",
       lambda: cov(ts)[0] == "amber" and cov(ts)[1].startswith("Under warranty till 01-07-2031") and "16 days left" in cov(ts)[1], lambda: cov(ts))
    ck("A1d lapsed: red, 'Covered: CMC by WALKPROV TWO -- lapsed on 01-05-2031'",
       lambda: cov(tp)[0] == "red" and "Covered: CMC by WALKPROV TWO" in cov(tp)[1] and "lapsed on 01-05-2031" in cov(tp)[1], lambda: cov(tp))
    ck("A1e the totals: 'Bought for ₹1,00,000 (01-02-2030) · Spent since ₹3,000 on 2 repairs/services · Cover paid ₹12,000'",
       lambda: tot(tl) == "Bought for ₹1,00,000 (01-02-2030) · Spent since ₹3,000 on 2 repairs/services · Cover paid ₹12,000",
       lambda: tot(tl))
    own.post("/desk/switch", data={"key": "machine.on", "on": "1", "back": "/"})
    th_m, th_o = html(mgr, "/assets/%d" % m_hide), html(own, "/assets/%d" % m_hide)
    ck("A1f a hide_price machine: the manager's totals and cover history carry no ₹ figure; the owner's do",
       lambda: "id=s557totals" in th_m and "₹" not in tot(th_m) and "Bought (01-02-2030)" in tot(th_m) and "₹9,000" not in th_m
       and "₹7,000" not in th_m and "₹2,50,000" in tot(th_o) and "₹9,000" in th_o,
       lambda: (tot(th_m), tot(th_o)))

    # ------------------------------------------------------------------ A7 (ON) and the Switches card
    front = html(own, "/")
    ck("A7b the owner's Switches card carries 'Machine pages for Shavez'; the switch (POST /desk/switch) wrote machine.on and its audit",
       lambda: "Machine pages for Shavez" in front and one("SELECT value FROM settings WHERE key='machine.on'") == "on"
       and one("SELECT COUNT(*) FROM desk_audit WHERE action='switch' AND detail LIKE '%machine.on%'") >= 1)

    # ------------------------------------------------------------------ A6 papers + A2 parts
    ma = mach("A", purchase_date="2030-02-01", price=100000, vendor="WALKV VENDOR ONE")
    p_cl = mk("PCL", "WALKS SPARES ONE", status="approved", subgroup="others", bill_no="P-1", total_amount=1500, bill_date="2031-06-02")
    p_ph = mk("PPH", "WALKS PHARMA ONE", lane="pharmacy", bill_no="P-2", total_amount=500, bill_date="2031-06-02")
    p_pt = mk("PPT", "WALKS PATIENT ONE", lane="other_doc", subgroup="patient_paper", bill_no="P-3", bill_date="2031-06-02")
    p_pe = mk("PPE", "WALKS PERSONAL ONE", lane="other_doc", subgroup="personal", bill_no="P-4", bill_date="2031-06-02")
    r = mgr.post("/assets/%d/parts/add" % ma, data={"name": "WALK PART ONE", "make": "WALKMAKE", "model": "WM-1", "serial": "SN-P1",
                                                    "fitted_on": "01-06-2031", "warranty_till": "31-05-2032", "paper": "z-2031-s7pcl"})
    pa = db.execute("SELECT * FROM asset_part WHERE asset_id=? AND name='WALK PART ONE'", (ma,)).fetchone() if am else None
    t_a = html(own, "/assets/%d" % ma)
    ck("A2a a manager (switch ON) adds a part with its paper: the row (make, model, serial, dates ISO, the paper, by whom); the Parts fold shows it with the paper's link",
       lambda: r.status_code == 302 and pa is not None and (pa["make"], pa["model"], pa["serial"], pa["fitted_on"], pa["warranty_till"], pa["bill_id"], pa["by_whom"])
       == ("WALKMAKE", "WM-1", "SN-P1", "2031-06-01", "2032-05-31", p_cl, "Walk Manager") and "WALK PART ONE" in t_a and "Z-2031-S7PCL" in t_a
       and '<details class=card id=s557parts open>' in t_a and '<details class=card id=s557covers>' in t_a and '<details class=card id=s557spends>' in t_a,
       lambda: (r.status_code, dict(pa) if pa else None))
    n_parts = one("SELECT COUNT(*) FROM asset_part WHERE asset_id=?", ma)
    own.post("/assets/%d/parts/add" % ma, data={"name": "WALK PART PH", "paper": "Z-2031-S7PPH"})
    own.post("/assets/%d/parts/add" % ma, data={"name": "WALK PART PT", "paper": "Z-2031-S7PPT"})
    mgr.post("/assets/%d/parts/add" % ma, data={"name": "WALK PART PE", "paper": "Z-2031-S7PPE"})
    own.post("/assets/%d/parts/add" % ma, data={"name": "WALK PART BAD", "fitted_on": "31-02-2031"})
    ck("A6a the stamp box refuses a pharmacy paper and a patient's paper (owner), a bad date too -- nothing written",
       lambda: one("SELECT COUNT(*) FROM asset_part WHERE asset_id=? AND name IN ('WALK PART PH','WALK PART PT','WALK PART BAD')", ma) == 0 and n_parts == 1)
    own.post("/assets/%d/parts/add" % ma, data={"name": "WALK PART OWNPE", "paper": "Z-2031-S7PPE"})
    ck("A6b a manager may not link a Personal paper (refused, nothing written); the owner may",
       lambda: one("SELECT COUNT(*) FROM asset_part WHERE name='WALK PART PE'") == 0
       and one("SELECT bill_id FROM asset_part WHERE name='WALK PART OWNPE'") == p_pe)
    own.post("/assets/%d/parts/add" % ma, data={"name": "WALK PART TWO", "fitted_on": "2030-01-01", "warranty_till": "2031-12-31"})
    p2 = one("SELECT id FROM asset_part WHERE name='WALK PART TWO'")
    rr = own.post("/assets/%d/parts/%s/remove" % (ma, p2), data={"day": "10-06-2031"})
    t_a = html(own, "/assets/%d" % ma)
    p2row = db.execute("SELECT * FROM asset_part WHERE id=?", (p2,)).fetchone() if am and isinstance(p2, int) else None
    exp_p2 = db.execute("SELECT * FROM expiries WHERE id=?", (p2row["expiry_id"],)).fetchone() if p2row and p2row["expiry_id"] else None
    pa = db.execute("SELECT * FROM asset_part WHERE asset_id=? AND name='WALK PART ONE'", (ma,)).fetchone() if am else None
    exp_p1 = db.execute("SELECT * FROM expiries WHERE id=?", (pa["expiry_id"],)).fetchone() if pa and pa["expiry_id"] else None
    ck("A2b 'Replaced / removed' marks the part (date, who), keeps the row, lists it under Removed parts; its reminder resolved, the live part's stays",
       lambda: rr.status_code == 302 and p2row is not None and (p2row["removed_on"], p2row["removed_by"]) == ("2031-06-10", own_u["display_name"])
       and "id=s557removed" in t_a and re.search(r"(?s)id=s557removed.*WALK PART TWO", t_a) and exp_p2 is not None and exp_p2["resolved"] == 1
       and exp_p1 is not None and (exp_p1["label"], exp_p1["due_date"], exp_p1["resolved"], exp_p1["entity_id"]) == ("Part warranty — WALK PART ONE", "2032-05-31", 0, ma),
       lambda: ((p2row["removed_on"], p2row["removed_by"] == own_u["display_name"]) if p2row else None,
                dict(exp_p2) if exp_p2 else None, dict(exp_p1) if exp_p1 else None))          # never a person's name in the log

    # ------------------------------------------------------------------ A3 cover history
    own.post("/assets/%d/covers/add" % ma, data={"kind": "amc", "provider": "WALKPROV ONE", "from_day": "01-08-2030", "till_day": "01-08-2031", "cost": "10000", "paper": "Z-2031-S7PCL"})
    c1 = one("SELECT id FROM asset_cover WHERE asset_id=? AND till_day='2031-08-01'", ma)
    e1a = one("SELECT resolved FROM expiries WHERE id=(SELECT expiry_id FROM asset_cover WHERE id=?)", c1)
    own.post("/assets/%d/covers/add" % ma, data={"kind": "amc", "provider": "WALKPROV ONE", "from_day": "02-08-2031", "till_day": "01-08-2032", "cost": "11000", "remind_days": "45"})
    c2 = one("SELECT id FROM asset_cover WHERE asset_id=? AND till_day='2032-08-01'", ma)
    e1b = one("SELECT resolved FROM expiries WHERE id=(SELECT expiry_id FROM asset_cover WHERE id=?)", c1)
    e2 = db.execute("SELECT e.* FROM expiries e JOIN asset_cover c ON c.expiry_id=e.id WHERE c.id=?", (c2,)).fetchone() if am else None
    ck("A3a add a cover (its reminder open), then the renewal = the next period: the older period's reminder resolved, the new one's open (label, till, remind days)",
       lambda: e1a == 0 and e1b == 1 and e2 is not None and (e2["label"], e2["due_date"], e2["threshold_days"], e2["resolved"]) == ("AMC — WALKPROV ONE", "2032-08-01", 45, 0),
       lambda: (e1a, e1b, dict(e2) if e2 else None))
    own.post("/assets/%d/covers/add" % ma, data={"kind": "warranty", "provider": "WALKPROV MAKER", "till_day": "31-12-2031"})
    c3 = one("SELECT id FROM asset_cover WHERE asset_id=? AND kind='warranty'", ma)
    own.post("/assets/%d/covers/add" % ma, data={"kind": "cmc", "provider": "WALKPROV WRONG", "till_day": "31-12-2033"})
    c4 = one("SELECT id FROM asset_cover WHERE asset_id=? AND kind='cmc'", ma)
    rv = mgr.post("/assets/%d/covers/%s/void" % (ma, c4))
    c4row = db.execute("SELECT * FROM asset_cover WHERE id=?", (c4,)).fetchone() if am and isinstance(c4, int) else None
    e4 = one("SELECT resolved FROM expiries WHERE id=?", c4row["expiry_id"]) if c4row and c4row["expiry_id"] else None
    t_a = html(own, "/assets/%d" % ma)
    ck("A3b a mistake is voided, never deleted: the row stays (voided_at, voided_by), struck through in the history; its reminder resolved",
       lambda: rv.status_code == 302 and c4row is not None and c4row["voided_at"] and c4row["voided_by"] == "Walk Manager" and e4 == 1
       and "WALKPROV WRONG" in t_a and "line-through" in t_a, lambda: (rv.status_code, (bool(c4row["voided_at"]), c4row["voided_by"] == "Walk Manager") if c4row else None, e4))
    t_old = html(own, "/assets/%d" % old_a)
    snap_old2 = dict(db.execute("SELECT * FROM assets WHERE id=?", (old_a,)).fetchone())
    ck("A3c the old record's single fields are shown once, read-only ('From the old record: AMC -- WALKOLD SERVICES · ₹5,000/yr'), and nothing is moved",
       lambda: t_old.count("From the old record:") == 1 and "From the old record: AMC — WALKOLD SERVICES · ₹5,000/yr" in t_old
       and snap_old2 == snap_old and one("SELECT COUNT(*) FROM asset_cover WHERE asset_id=?", old_a) == 0,
       lambda: (re.findall(r"From the old record:[^<]*", t_old), snap_old2 == snap_old))

    # ------------------------------------------------------------------ A4 spends
    p_sp = mk("PSP", "WALKS SERVICE ONE", status="approved", subgroup="others", bill_no="P-5", total_amount=2500, bill_date="2031-05-20")
    rs = mgr.post("/assets/%d/spends/add" % ma, data={"day": "20-05-2031", "svc_type": "Repair", "work": "walk motor rewound", "cost": "2500", "done_by": "WALKTECH", "paper": "Z-2031-S7PSP"})
    sp = db.execute("SELECT * FROM service_logs WHERE asset_id=? AND work='walk motor rewound'", (ma,)).fetchone()
    ro = own.post("/assets/%d/service" % ma, data={"log_date": "2030-11-11", "svc_type": "Other service", "work": "walk old-form visit", "cost": "800", "done_by": "WALKTECH"})
    so = db.execute("SELECT * FROM service_logs WHERE asset_id=? AND work='walk old-form visit'", (ma,)).fetchone()
    p_sp2 = mk("PSQ", "WALKS SERVICE TWO", status="approved", subgroup="others", bill_no="P-6", total_amount=800, bill_date="2030-11-11")
    rl = own.post("/assets/%d/spends/%s/paper" % (ma, so["id"] if so else 0), data={"paper": "Z-2031-S7PSQ"})
    t_a = html(own, "/assets/%d" % ma)
    ck("A4a a spend with its paper (service_logs, bill_id) shows in the Spends fold with the paper's link; per-year totals",
       lambda: rs.status_code == 302 and sp is not None and (sp["log_date"], sp["cost"], sp["svc_type"], sp["done_by"], sp["bill_id"]) == ("2031-05-20", 2500, "Repair", "WALKTECH", p_sp)
       and "walk motor rewound" in t_a and "Z-2031-S7PSP" in t_a and re.search(r"Per year:</b> 2031 ₹2,500 · 2030 ₹800", t_a),
       lambda: (rs.status_code, dict(sp) if sp else None, re.findall(r"Per year:</b>[^<]*", t_a)))
    ck("A4b the old 'Add service' form still works: its entry is in Spends, and a paper is linked to it afterwards",
       lambda: ro.status_code == 302 and so is not None and "walk old-form visit" in t_a and one("SELECT bill_id FROM service_logs WHERE id=?", so["id"]) == p_sp2
       and rl.status_code == 302, lambda: (ro.status_code, dict(so) if so else None, rl.status_code))

    # ------------------------------------------------------------------ A5 the reminders: one per live cover / part; two restarts
    def mine():
        return [tuple(r_) for r_ in db.execute("SELECT id, label, due_date, threshold_days, resolved FROM expiries WHERE entity='asset' AND entity_id=? ORDER BY id", (ma,))]
    before = mine()
    open_ = [x for x in before if x[4] == 0]
    ck("A5a exactly one open reminder per live cover / part on the machine: the AMC renewal, the warranty, the live part (6 rows in all, 3 resolved)",
       lambda: len(before) == 6 and sorted(x[1] for x in open_) == ["AMC — WALKPROV ONE", "Part warranty — WALK PART ONE", "Warranty — WALKPROV MAKER"]
       and len({x[0] for x in before}) == 6, lambda: before)
    rn = html(own, "/renewals?all=1")
    ids_before = one("SELECT group_concat(expiry_id) FROM (SELECT expiry_id FROM asset_cover WHERE asset_id=? UNION ALL SELECT expiry_id FROM asset_part WHERE asset_id=?)", ma, ma)
    # two restarts: the app imported again, twice -- the heal runs at each mount
    m2 = quiet(lambda: import_file("asset_register", os.path.join(appdir, "asset_register.py")))
    m3 = quiet(lambda: import_file("asset_register", os.path.join(appdir, "asset_register.py")))
    if m3 is not None:
        state["m"] = m3
        m = m3
    after2 = mine()
    db.execute("UPDATE asset_cover SET till_day='2032-09-01' WHERE id=?", (c2,)) if am else None
    db.execute("UPDATE asset_cover SET expiry_id=NULL WHERE id=?", (c3,)) if am else None
    db.commit()
    m4 = quiet(lambda: import_file("asset_register", os.path.join(appdir, "asset_register.py")))
    if m4 is not None:
        state["m"] = m4
        m = m4
    after3 = mine()
    ids_after = one("SELECT group_concat(expiry_id) FROM (SELECT expiry_id FROM asset_cover WHERE asset_id=? UNION ALL SELECT expiry_id FROM asset_part WHERE asset_id=?)", ma, ma)
    ck("A5b after two restarts nothing is duplicated; a changed till is updated in place; a lost link is re-linked to the same reminder",
       lambda: m2 is not None and m3 is not None and after2 == before and len(after3) == 6 and ids_after == ids_before
       and [x for x in after3 if x[1] == "AMC — WALKPROV ONE" and x[4] == 0][0][2] == "2032-09-01"
       and rn.count("AMC — WALKPROV ONE") >= 1 and "Part warranty — WALK PART ONE" in rn,
       lambda: (len(after2), len(after3), ids_before, ids_after, after3))
    own, mgr, anon = client(own_u), client(mgr_u), client(None)

    # ------------------------------------------------------------------ A6 the paper's page, the desk's note, a machine from a paper
    tb = html(own, "/bills/%d" % p_cl)
    ck("A6c the paper's own page: 'Linked to WALK S557 MACHINE A as part; ... as cover'",
       lambda: re.search(r"<b>Machine:</b> Linked to <a [^>]*>WALK S557 MACHINE A</a> as part; <a [^>]*>WALK S557 MACHINE A</a> as cover", tb),
       lambda: re.findall(r"<b>Machine:</b>.{0,200}", tb))
    eq = mk("PEQ", "WALKEQ SUPPLIERS", status="approved", subgroup="clinic_equipment", kind="Asset", bill_no="EQ-1", total_amount=45000,
            bill_date="2031-06-05", approved_by="Walk", items=[("walk analyser line", 1, 45000)])
    reading(eq, json.dumps({"vendor": "WALKEQ SUPPLIERS", "items": [{"name": "WALK ANALYSER", "qty": 1, "make": "WALKMAKE", "model": "WM-7", "serial": "SN-WALK-1"}]}))
    tq = html(own, "/bills/%d" % eq)
    tmon = html(own, "/desk/month?ym=2031-06")
    tf = html(own, "/bills/%d/machine" % eq)
    ck("A6d a Clinic-equipment paper: '+ asset record' on its page and on The month opens the new machine form, pre-filled from the paper and Claude's reading",
       lambda: ('href="/bills/%d/machine"' % eq) in tq and ('href="/bills/%d/machine">+ asset record' % eq) in tmon
       and all(('value="%s"' % v) in tf for v in ("WALK ANALYSER", "WALKEQ SUPPLIERS", "05-06-2031", "45000", "WALKMAKE", "WM-7", "SN-WALK-1")),
       lambda: (('/bills/%d/machine' % eq) in tq, ('/bills/%d/machine' % eq) in tmon, re.findall(r'value="[^"]*"', tf)[:10]))
    rp = own.post("/bills/%d/machine" % eq, data={"name": "WALK ANALYSER", "category": "Dr MK Clinic Equipment", "vendor": "WALKEQ SUPPLIERS",
                                                 "purchase_date": "05-06-2031", "price": "45000", "make": "WALKMAKE", "model": "WM-7", "serial_no": "SN-WALK-1"})
    na = db.execute("SELECT * FROM assets WHERE bill_id=? ORDER BY id", (eq,)).fetchall()
    tq2 = html(own, "/bills/%d" % eq)
    _c, jq = own.get("/desk/api/paper/%d" % eq).status_code, (own.get("/desk/api/paper/%d" % eq).get_json(silent=True) or {})
    ck("A6e ...Save makes the machine (name, supplier, date, price, serial, make/model in its notes) keeping the paper as its purchase bill; the paper reads 'Linked to ... as purchase', and so does the desk's note",
       lambda: rp.status_code == 302 and len(na) == 1 and (na[0]["name"], na[0]["vendor"], na[0]["purchase_date"], na[0]["price"], na[0]["serial_no"])
       == ("WALK ANALYSER", "WALKEQ SUPPLIERS", "2031-06-05", 45000, "SN-WALK-1") and "Make WALKMAKE · Model WM-7" in (na[0]["notes"] or "")
       and one("SELECT asset_id FROM bill_items WHERE bill_id=?", eq) == na[0]["id"] and "as purchase" in tq2
       and jq.get("linked") == "Linked to WALK ANALYSER as purchase." and "+ asset record" not in html(own, "/desk/month?ym=2031-06").split("Z-2031-S7PEQ")[1][:300],
       lambda: (rp.status_code, [dict(x) for x in na], jq.get("linked")))

    # ------------------------------------------------------------------ A7 reception and no login
    routes = ["/assets/%d/parts/add" % ma, "/assets/%d/parts/1/remove" % ma, "/assets/%d/covers/add" % ma, "/assets/%d/covers/1/void" % ma,
              "/assets/%d/spends/add" % ma, "/assets/%d/spends/1/paper" % ma]
    codes = as_reception(lambda: [client(None).post(u, data={}).status_code for u in routes] + [client(None).get("/bills/%d/machine" % eq).status_code])
    nl = [anon.post(u, data={}).status_code for u in routes[:1]] + [anon.get("/bills/%d/machine" % eq).status_code]
    mg = mgr.get("/bills/%d/machine" % eq).status_code
    ck("A7c a reception login gets 403 on every new route; no login gets the login redirect; the new-machine-from-paper page is the owner's (manager 403)",
       lambda: codes and all(x == 403 for x in codes) and all(x == 302 for x in nl) and mg == 403, lambda: (codes, nl, mg))

    # ------------------------------------------------------------------ B1 one word per lane on the owner's and managers' pages
    lb = mk("PLB", "WALKL LAB ONE", lane="lab_purchase", bill_no="L-1", total_amount=100, bill_date="2031-06-03")
    ch = mk("PCH", "WALKC CHALLAN ONE", doc_kind="challan", challan_state="awaiting", bill_no="C-1", bill_date="2031-06-03", items=[("walk gauze", 2)])

    def lane_bits(t):
        lane = re.findall(r"<b>Lane:</b> ([^<]*?)\s*<form", t)
        opts = re.findall(r"(?s)<select name=lane[^>]*>(.*?)</select>", t)
        return lane, re.findall(r">([^<>]+)</option>", opts[0]) if opts else []
    bo, bm = html(own, "/bills/%d" % lb), html(mgr, "/bills/%d" % p_cl)
    ck("B1a the bill page (owner and manager): 'Lane: NK Pathology' / 'Lane: Clinic' and the move list in one word each",
       lambda: lane_bits(bo) == (["NK Pathology"], ["Clinic", "Pharmacy", "NK Pathology", "Personal expense", "Other document"])
       and lane_bits(bm)[0] == ["Clinic"] and not LONG.search(visible(bo)), lambda: (lane_bits(bo), lane_bits(bm), LONG.findall(visible(bo))))
    tlan = html(own, "/lanes")
    ck("B1b the lanes page: one word per lane (table and list)", lambda: "Clinic" in visible(tlan) and not LONG.search(visible(tlan)), lambda: LONG.findall(visible(tlan)))
    tpp, tch = html(own, "/papers/%d" % lb), html(own, "/papers/challans")
    ix = tch.find("Z-2031-S7PCH")
    rowc = visible(tch[max(0, ix - 700): ix + 700]) if ix >= 0 else ""
    ck("B1c the papers pages: a paper's 'Lane: NK Pathology'; the challans page's row reads '· Clinic'",
       lambda: re.search(r"Lane: NK Pathology", tpp) and not re.search(r"Lane: Lab purchase", tpp) and "· Clinic" in rowc
       and "Clinic bill" not in rowc, lambda: (re.findall(r"Lane: [^<·]*", tpp), rowc[:400]))
    jd = own.get("/desk/api/paper/%d" % ch).get_json(silent=True) or {}
    taw = html(own, "/desk/awaited")
    ck("B1d the desk: the paper's lane 'Clinic'; Bills awaited's line 'Clinic' -- never 'Clinic bill'",
       lambda: jd.get("lane") == "Clinic" and "Clinic bill" not in taw and "WALKC CHALLAN ONE" in taw, lambda: (jd.get("lane"), LONG.findall(visible(taw))))
    slip = html(own, "/intake/slip/%d" % ch)
    ck("B1e reception's slip keeps its words (unchanged by design)", lambda: "Clinic bill" in slip, lambda: re.findall(r"id=slipnote.{0,200}", slip))

    # ------------------------------------------------------------------ B2 an amount that is not a number; B3 (N2) a date with its time
    nb = mk("PNA", "WALKN NAN TRADERS", bill_no="N-1", total_amount=100, bill_date="2031-06-05", created="2031-06-12 05:00:00")
    reading(nb, '{"vendor": "WALKN NAN TRADERS", "bill_no": "N-1", "bill_date": "2031-06-05", "total_amount": NaN, "items": [{"name": "walk item", "qty": Infinity}]}')
    tb2 = mk("PNB", "WALKN TEXT TRADERS", bill_no="N-2", total_amount=100, bill_date="2031-06-05", created="2031-06-12 05:00:00")
    reading(tb2, '{"vendor": "WALKN TEXT TRADERS", "total_amount": "about a hundred", "items": []}')
    r1, r2 = own.get("/desk/api/paper/%d" % nb), own.get("/desk/api/paper/%d" % tb2)

    def strict(resp):
        def bad(x):
            raise ValueError("not JSON: " + x)
        return json.loads(resp.get_data(as_text=True), parse_constant=bad)
    ck("B2 a Claude amount NaN / inf / text is ignored: the paper opens (200), its JSON is strict JSON, no amount line, the quantity shows nothing",
       lambda: r1.status_code == 200 and r2.status_code == 200 and "amount" not in (strict(r1).get("claude") or {}) and "amount" not in (strict(r2).get("claude") or {})
       and sd.reading(db, nb)["amount"] is None and "inf" not in strict(r1).get("items", "").lower() and "nan" not in strict(r1).get("items", "").lower(),
       lambda: (r1.status_code, r1.get_data(as_text=True)[:200], r2.status_code))
    dt = mk("PDT", "WALKD TIME TRADERS", bill_no="D-1", total_amount=100, bill_date="2031-06-05 10:00", created="2031-06-12 05:00:00")
    reading(dt, json.dumps({"vendor": "WALKD TIME TRADERS", "bill_no": "D-1", "bill_date": "2031-06-05", "total_amount": 100, "items": []}))
    jt = own.get("/desk/api/paper/%d" % dt).get_json(silent=True) or {}
    ck("B3 (S555 review N2) a stored date with a time part is the same day: no spurious 'Claude read' date line",
       lambda: jt.get("ok") and "date" not in (jt.get("claude") or {}), lambda: jt.get("claude"))

    # ------------------------------------------------------------------ sizes, and the scratch copy only
    t0 = time.time(); a_ = own.get("/assets/%d" % ma); t1 = time.time()
    print("SIZES machine page %d B (%.0f ms) . the old record's page %d B . renewals %d B" % (len(a_.data), (t1 - t0) * 1000, len(t_old), len(rn)))
    ck("T1 the machine page answers 200 in under 2 s", lambda: a_.status_code == 200 and (t1 - t0) < 2)
    ck("Z1 the made-up rows live in the scratch copy only", lambda: dbp.startswith(work) and state["m"].DB_PATH == dbp)
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
    if opt("--dump"):
        sys.exit(0 if os.path.exists(opt("--dump")) else 1)
    reds = R.count(False)
    print("%d checks: %d GREEN, %d RED%s" % (len(R), R.count(True), reds, (" (" + ", ".join(FAILED) + ")") if FAILED else ""))
    if "--expect-red" in ARGS:
        seen_ = {}
        for ok_, nm_ in zip(R, NAMES):
            seen_[nm_] = ok_
        not_red = [k for k in MUST_RED if seen_.get(k) is not False]
        print("CONTROL must-be-red: %s -- %s" % (", ".join(MUST_RED), ("all RED" if not not_red else "NOT red: " + ", ".join(
            k + ("(green)" if seen_.get(k) else "(not reached)") for k in not_red))))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
