#!/usr/bin/env python3
"""walk_s559.py -- the S559_ONE_ROAD walk. The app with the given files on a COPY of a database (SQLite's backup API), in its
own scratch folder; made-up rows only (suppliers WALKxx .., each differing in its first two words; stamps Z-2031-S9..; dated
around a made-up today of 15-Jun-2031), made-up logins (walk_own_2031 / walk_mgr_2031, made here); no reader thread, no paid
call, nothing sent anywhere (a made-up key and URL). Flask's test client; no port. Isolated exactly as walk_s557.py.

    python3 -B walk_s559.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js> <assets.db to copy> [--work DIR] [--shared DIR]
                            [--from-widget FILE] [--dump FILE | --baseline FILE] [--expect-red] [--keep]

--dump FILE: write reception's pages (the intake, its own list) as these files give them, then stop (run on the LIVE files).
--baseline FILE: compare those pages byte for byte with the dump.
--from-widget FILE: the pinned live scanner_widget.js -- J1 proves the built widget differs from it only in S559's lines.
GREEN / RED per check; exit 1 on any RED. --expect-red (the control on the live S557 files): exit 0 only if every check named
in MUST_RED is RED. The work folder (default: a new folder under /tmp) is removed at the end unless --keep."""
import datetime, difflib, hashlib, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile, time

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "M1", "M2", "M3", "M4", "M5", "M6", "H1", "H2", "O1", "O2", "O3", "O4", "L1", "L2", "L3", "L4", "L5", "L6",
            "B1", "B2", "B3", "F1", "F2", "N1", "N3", "K2", "Z1", "D1", "C1", "R1", "P1", "J1", "J2",
            "L8", "J3")                                                    # S559_FIX1: L8 (B1), J3 (C1, C2)
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js")
ORDER_OWN = ["s551_desk", "s551_month", "s551_awaited", "s551_implants", "assets_list", "renewals", "bills_list", "vendors_list",
             "admin", "account", "logout"]
OLD_LINK = re.compile(r'href="[^"]*/(?:papers/month|papers/challans|purchases)(?:[?"#])')


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


def bar_eps(h):
    m = re.search(r'<div class=s559h id=s559bar.*?</nav></div>', h or "", re.S)
    return re.findall(r'data-s559="([^"]+)"', m.group(0)) if m else []


def bar_num(h, ep, word):
    m = re.search(r'data-s559="%s"[^>]*>%s \((\d+)\)</a>' % (ep, re.escape(word)), h or "")
    return int(m.group(1)) if m else None


def href_of(h, text, extra=""):
    """The href of the link whose text is exactly `text` (the first one)."""
    m = re.search(r'<a href="([^"]+)"%s[^>]*>%s</a>' % (extra, re.escape(text)), h or "")
    return m.group(1).replace("&amp;", "&") if m else None


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S559_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s559walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
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
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not c.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            c.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
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
    ck("W1 the app imports; asset_register, clinic_papers, claude_reader, sorting_desk, asset_machine come from the scratch folder",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and under(m.CLAUDE.__file__, appdir) and sd is not None
       and under(sd.__file__, appdir) and am is not None and under(am.__file__, appdir) and am.MOUNTED)
    ck("W2 the S559 marks: asset_register ROAD_S559, sorting_desk ROAD, asset_machine ROAD = S559 (S557 / S555 / S551 marks kept)",
       lambda: getattr(m, "ROAD_S559", None) == "S559" and getattr(sd, "ROAD", None) == "S559" and getattr(am, "ROAD", None) == "S559"
       and sd.MACHINE == "S557" and sd.CORRECTIONS == "S555" and sd.VERSION == "S551.2" and am.VERSION == "S557")
    ck("W4 the shared modules come from the scratch copy; no finance database is reachable",
       lambda: (m.S441 is None or under(m.S441.__file__, os.path.join(work, "shared"))) and (m.SARVAM is None or under(m.SARVAM.__file__, os.path.join(work, "shared")))
       and (m.S441 is None or not os.path.exists(m.S441.FIN_DB)) and m.DB_PATH == dbp and m.UPLOAD_DIR == env["ASSETS_UPLOADS"])
    sd.TODAY = TODAY
    am.TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    own_u = db.execute("SELECT * FROM users WHERE username='walk_own_2031'").fetchone()
    mgr_u = db.execute("SELECT * FROM users WHERE username='walk_mgr_2031'").fetchone()
    state = {"m": m}

    def client(u):
        cl = state["m"].app.test_client()
        if u is not None:
            with cl.session_transaction() as ss:
                ss["uid"] = u["id"]; ss["epoch"] = epoch
        return cl
    own, mgr = client(own_u), client(mgr_u)
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

    def one(sql, *a):
        try:
            r = db.execute(sql, a).fetchone()
            return r[0] if r else None
        except sqlite3.Error as e:
            return "ERR " + str(e)

    def setting(k, v):
        if v is None:
            db.execute("DELETE FROM settings WHERE key=?", (k,))
        else:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
        db.commit()

    # ------------------------------------------------------------------ K: reception's pages must not change (vs the live files)
    pages = {"intake": as_reception(lambda: html(client(None), "/intake")),
             "rec_list": as_reception(lambda: html(client(None), "/bills"))}
    if opt("--dump"):
        with open(opt("--dump"), "w", encoding="utf-8") as fh:
            json.dump(pages, fh)
        print("DUMPED reception's pages (%d B intake, %d B its own list)" % (len(pages["intake"]), len(pages["rec_list"])))
        db.close()
        return
    base = {}
    if opt("--baseline") and os.path.exists(opt("--baseline")):
        base = json.load(open(opt("--baseline"), encoding="utf-8"))
    def vless(h):                       # the widget's cache stamp is the file's time (?v=<mtime>): a new widget gets a new stamp
        return re.sub(r"(/scan/widget\.js\?v=)\d+", r"\g<1>N", h or "")
    ck("K1 reception's intake and its own list: byte for byte the HTML the live files give (but the widget's own ?v= time stamp); "
       "no bar, no desk link in them",
       lambda: base.get("intake") is not None and vless(pages["intake"]) == vless(base["intake"]) and pages["rec_list"] == base["rec_list"]
       and pages["intake"].count("/scan/widget.js?v=") == 1
       and "s559" not in pages["intake"] and "/desk" not in pages["intake"] and "Clinic bill" in pages["intake"],
       lambda: ("no baseline" if not base else (len(pages["intake"]), len(base.get("intake", "")), len(pages["rec_list"]), len(base.get("rec_list", "")))))

    # ------------------------------------------------------------------ the made-up rows
    gen = db.execute("SELECT id FROM locations WHERE visibility='general' ORDER BY id LIMIT 1").fetchone()[0]
    ent = db.execute("SELECT id FROM entities WHERE name='Dr Manoj Clinic'").fetchone()
    entid = ent[0] if ent else None

    def mk(tag, vendor, lane="clinic", status=None, created="2031-06-10 05:00:00", kind=None, **cols_):
        kd = kind or {"clinic": "Consumable", "other_doc": "Document", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no="Z-2031-S9" + tag, status=st, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk")
        vals.update(cols_)
        bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        db.commit()
        return bid

    def mach(tag, **cols_):
        vals = dict(name="WALK S559 MACHINE " + tag, location_id=gen, category="Dr MK Clinic Equipment", status="Active",
                    contract_type="None", entity_id=entid, kind="Asset")
        vals.update(cols_)
        aid = db.execute("INSERT INTO assets(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        db.commit()
        return aid

    open(os.path.join(work, "uploads", "walk_s559_a.pdf"), "wb").write(b"%PDF-1.4\n% made-up walk file\n")
    p_cl = mk("01", "WALKCL ALPHA SUPPLIES", bill_date="2031-06-04", total_amount=1200, source_stored="walk_s559_a.pdf", source_orig="walk.pdf")
    p_ph = mk("02", "WALKPH BETA PHARMA", lane="pharmacy", bill_date="2031-06-04", source_stored="walk_s559_a.pdf", source_orig="walk.pdf")
    p_pe = mk("03", "WALKPE GAMMA HOME", status="approved", subgroup="personal", bill_date="2031-06-03")
    p_od = mk("04", "WALKOD DELTA OFFICE", lane="other_doc", bill_date="2031-06-02")
    p_ap = mk("05", "WALKAP EPSILON TRADERS", status="approved", subgroup="procedure", bill_date="2031-06-05", total_amount=500)
    p_rj = mk("06", "WALKRJ ZETA MART", status="rejected", bill_date="2031-06-01")
    p_ch = mk("07", "WALKCH ETA SURGICALS", doc_kind="challan", subgroup="procedure", bill_date="2031-06-06")
    p_im = mk("08", "WALKIM THETA IMPLANTS", status="approved", subgroup="implant_stock", bill_date="2031-06-07", total_amount=9000)
    p_eq = mk("09", "WALKEQ IOTA DEVICES", status="approved", subgroup="clinic_equipment", bill_date="2031-06-08", total_amount=40000)
    p_pa = mk("10", "WALKPA KAPPA PARTS", status="approved", subgroup="others", bill_date="2031-06-09", total_amount=700)
    p_p2 = mk("11", None, subgroup="personal")                  # a Personal paper with nothing read: on the owner's desk only
    owner_ = True

    # ------------------------------------------------------------------ M: the one menu (item 1)
    setting("desk.on", None)
    own_pages = {"home": "/", "assets": "/assets", "renewals": "/renewals", "bills": "/bills", "bill": "/bills/%d" % p_cl,
                 "vendors": "/vendors", "admin": "/admin", "account": "/account", "papers": "/papers",
                 "desk": "/desk", "month": "/desk/month", "awaited": "/desk/awaited", "implants": "/desk/implants"}
    th = {k: html(own, u) for k, u in own_pages.items()}
    seen_ord = {k: bar_eps(h) for k, h in th.items()}
    if opt("--save-pages"):                     # for the browser walk's fit check: three pages holding only made-up rows
        os.makedirs(opt("--save-pages"), exist_ok=True)
        for k in ("account", "desk", "month"):
            with open(os.path.join(opt("--save-pages"), k + ".html"), "w", encoding="utf-8") as fh:
                fh.write(th[k])
    ck("M1 the owner's bar on every page of his (the scan app's ten and the desk's four): Sorting desk (N) . The month . Bills "
       "awaited (N) . Implant ledger . Machines . Renewals . All papers . Vendors . Admin . account . Logout, in that order",
       lambda: all(v == ORDER_OWN for v in seen_ord.values()),
       lambda: {k: v for k, v in seen_ord.items() if v != ORDER_OWN})
    jl = json.loads(own.get("/desk/api/list").get_data(as_text=True))
    n_own = len(sd.waiting(db, True))
    aw_own = len(sd.awaiting_challans(db, True))
    nums = {k: (bar_num(h, "s551_desk", "Sorting desk"), bar_num(h, "s551_awaited", "Bills awaited")) for k, h in th.items()}
    ck("M2 the counts: Sorting desk N = the desk's own list (its /desk/api/list total and len(waiting)), Bills awaited N = the "
       "challans awaiting their bill he may see -- on every page",
       lambda: n_own > 0 and jl.get("total") == n_own and all(v == (n_own, aw_own) for v in nums.values()) and aw_own > 0,
       lambda: (n_own, jl.get("total"), aw_own, set(nums.values())))
    ck("M3 Drafts and Staff are out of the menu; their pages still answer 200 for the owner (Drafts from Assets and Admin, Staff from Admin)",
       lambda: all(v and "drafts_list" not in v and "staff_list" not in v for v in seen_ord.values())
       and not re.search(r'<nav>.*?>(Drafts|Staff)</a>.*?</nav>', th["home"], re.S)
       and not re.search(r'id=s559bar.*?>(Drafts|Staff)</a>.*?</nav>', th["home"], re.S)
       and own.get("/drafts").status_code == 200 and own.get("/staff").status_code == 200
       and 'href="/drafts"' in th["assets"] and 'href="/drafts"' in th["admin"] and 'href="/staff"' in th["admin"],
       lambda: (own.get("/drafts").status_code, own.get("/staff").status_code, 'href="/staff"' in th["admin"]))
    mh = {k: html(mgr, u) for k, u in own_pages.items() if k != "admin"}
    m_off = {k: bar_eps(h) for k, h in mh.items()}
    want_off = [x for x in ORDER_OWN if x not in ("s551_desk", "admin")]
    setting("desk.on", "on")
    mh_on = {k: html(mgr, u) for k, u in own_pages.items() if k != "admin"}
    m_on = {k: bar_eps(h) for k, h in mh_on.items() if k not in ("desk",)}
    n_mgr = len(sd.waiting(db, False))
    ck("M4 a manager: while desk.on is off, no Sorting desk (and no Admin) in his bar; switched on, Sorting desk (N) with HIS count "
       "(no Personal paper) -- the same order otherwise",
       lambda: all(v == want_off for k, v in m_off.items() if k not in ("desk", "month", "awaited", "implants"))
       and all(v == [x for x in ORDER_OWN if x != "admin"] for v in m_on.values())
       and bar_num(mh_on["home"], "s551_desk", "Sorting desk") == n_mgr == n_own - 1
       and p_p2 in [b["id"] for b, _w in sd.waiting(db, True)] and p_p2 not in [b["id"] for b, _w in sd.waiting(db, False)],
       lambda: ({k: v for k, v in m_off.items() if v != want_off}, {k: v for k, v in m_on.items() if v != [x for x in ORDER_OWN if x != "admin"]},
                bar_num(mh_on["home"], "s551_desk", "Sorting desk"), n_mgr, n_own))
    setting("desk.on", None)
    ck("M5 the desk's four pages carry the bar (the desk inside its full-height frame), the scan app's pages carry it once, and "
       "the one helper builds it (the same bar markup on a desk page and an app page)",
       lambda: all(th[k].count("id=s559bar") == 1 for k in th)
       and re.search(r"<div id=app>\s*<style>", th["desk"]) is not None
       and re.search(r'<div class=s559h id=s559bar.*?</nav></div>', th["home"], re.S).group(0)
       .replace(' class=on aria-current=page', '') == re.search(r'<div class=s559h id=s559bar.*?</nav></div>', th["month"], re.S).group(0).replace(' class=on aria-current=page', ''),
       lambda: {k: th[k].count("id=s559bar") for k in th})
    ck("M6 the bar names him (the account item) and the links go to the named doors: /desk, /desk/month, /desk/awaited, "
       "/desk/implants, /assets, /renewals, /bills, /vendors, /admin",
       lambda: all(('data-s559="%s"' % ep) in th["home"] and ('href="%s" data-s559="%s"' % (u, ep)) in th["home"] for ep, u in
                   (("s551_desk", "/desk"), ("s551_month", "/desk/month"), ("s551_awaited", "/desk/awaited"), ("s551_implants", "/desk/implants"),
                    ("assets_list", "/assets"), ("renewals", "/renewals"), ("bills_list", "/bills"), ("vendors_list", "/vendors"), ("admin", "/admin")))
       and ">Walk Owner</a>" in th["home"],
       lambda: re.findall(r'href="([^"]+)" data-s559', th["home"]))

    # ------------------------------------------------------------------ H: the home page's card (item 2)
    ck("H1 the home page opens with the card: 'N papers waiting' (the desk's N), the big 'Open the sorting desk' -> /desk, and "
       "'Bills awaited N . Implant ledger . The month' under it -- above everything else",
       lambda: re.search(r"<main>(?:<div class=flash>.*?</div>)?\s*<div class=card id=s559home", th["home"], re.S) is not None
       and ("%d papers waiting" % n_own) in th["home"] and 'id=s559open href="/desk"' in th["home"]
       and ('>Bills awaited %d</a>' % aw_own) in th["home"] and '>Implant ledger</a> · <a href="/desk/month">The month</a>' in th["home"]
       and th["home"].index("s559home") < th["home"].index("<h2>Dashboard</h2>"),
       lambda: re.findall(r"id=s559n>([^<]+)<", th["home"]))
    real_w = sd.waiting
    sd.waiting = lambda *a, **k: []
    h0 = quiet(lambda: html(own, "/"), "")
    sd.waiting = real_w
    ck("H2 with nothing waiting the card reads 'No paper waiting.'; a manager while the desk is off gets no card (the rest of the page as it was)",
       lambda: "No paper waiting." in h0 and "s559home" not in mh["home"] and "<h2>Dashboard</h2>" in mh["home"],
       lambda: (re.findall(r"id=s559n>([^<]+)<", h0), "s559home" in mh["home"]))

    # ------------------------------------------------------------------ O: the desk opens on a given paper (item 3)
    def cfg_of(h):
        mm = re.search(r"var C=(\{.*?\});\n", h or "")
        return json.loads(mm.group(1)) if mm else {}
    d_cl = html(own, "/desk?open=%d" % p_cl)
    d_st = html(own, "/desk?open=Z-2031-S901")
    d_ph = html(own, "/desk?open=%d" % p_ph)
    d_unk = html(own, "/desk?open=999999999")
    setting("desk.on", "on")
    d_pe_m = html(mgr, "/desk?open=%d" % p_pe)
    d_pe_o = html(own, "/desk?open=%d" % p_pe)
    setting("desk.on", None)
    ck("O1 /desk?open=<id> of a clinic paper: the desk is handed that paper (cfg.open) and opens it after its list, as a pick does; "
       "its paper answers 200 on the desk's own door",
       lambda: cfg_of(d_cl).get("open") == p_cl and "loadList(C.open||0);" in d_cl and "s559cant" not in d_cl
       and own.get("/desk/api/paper/%d" % p_cl).status_code == 200,
       lambda: (cfg_of(d_cl).get("open"), "loadList(C.open||0);" in d_cl))
    ck("O2 /desk?open=B-xxxx (its stamp) opens the same paper", lambda: cfg_of(d_st).get("open") == p_cl and "s559cant" not in d_st,
       lambda: cfg_of(d_st).get("open"))
    ck("O3 a pharmacy paper and an unknown id: the desk opens normally (nothing handed) with the one grey line",
       lambda: cfg_of(d_ph).get("open") == 0 and "That paper can't be opened here" in d_ph and cfg_of(d_unk).get("open") == 0
       and "That paper can't be opened here" in d_unk and "Sorting desk" in d_ph,
       lambda: (cfg_of(d_ph).get("open"), cfg_of(d_unk).get("open")))
    ck("O4 a Personal paper: refused for a manager (the grey line), opened for the owner",
       lambda: cfg_of(d_pe_m).get("open") == 0 and "That paper can't be opened here" in d_pe_m and cfg_of(d_pe_o).get("open") == p_pe,
       lambda: (cfg_of(d_pe_m).get("open"), cfg_of(d_pe_o).get("open")))

    # ------------------------------------------------------------------ L: every paper row leads to the desk (item 4)
    def desk_u(bid):
        return "/desk?open=%d" % bid

    def bill_u(bid):
        return "/bills/%d" % bid
    rows_ = {p_cl: "WALKCL ALPHA SUPPLIES", p_ph: "WALKPH BETA PHARMA", p_pe: "WALKPE GAMMA HOME", p_od: "WALKOD DELTA OFFICE",
             p_ap: "WALKAP EPSILON TRADERS", p_rj: "WALKRJ ZETA MART", p_ch: "WALKCH ETA SURGICALS"}
    filt = {"": rows_, "draft": {p_cl: rows_[p_cl], p_ch: rows_[p_ch]}, "captured": {p_ph: rows_[p_ph], p_od: rows_[p_od]},
            "approved": {p_ap: rows_[p_ap], p_pe: rows_[p_pe]}, "rejected": {p_rj: rows_[p_rj]}}
    got = {}
    for fs, rs in filt.items():
        h = html(own, "/bills" + ("?status=" + fs if fs else ""))
        for bid, v in rs.items():
            got[(fs, bid)] = href_of(h, v)
    want = {k: (bill_u(k[1]) if k[1] == p_ph else desk_u(k[1])) for k in got}
    ck("L1 All papers, every filter (all / draft / captured / approved / rejected): a non-pharmacy paper's row -> /desk?open=<id>; "
       "the pharmacy paper's row -> its old bill page",
       lambda: got == want, lambda: {"%s:%s" % k: v for k, v in got.items() if v != want[k]})
    hp = html(own, "/papers")
    seg = next((x for x in hp.split("<div class=d6card>") if "Z-2031-S901" in x), "")
    ck("L2 the papers list: the paper's picture, its stamp and its 'Open it' all lead to /desk?open=<id>",
       lambda: seg and seg.count('href="%s"' % desk_u(p_cl)) == 3 and ('class="d6b alt" href="%s">' % desk_u(p_cl)) in seg
       and ('href="%s"' % bill_u(p_cl)) not in seg and ("/papers/%d\"" % p_cl) not in seg,
       lambda: re.findall(r'href="([^"]+)"', seg)[:8])
    ha = html(own, "/desk/awaited")
    ck("L3 Bills awaited: the challan's row -> /desk?open=<id>", lambda: href_of(ha, "Z-2031-S907", ' style="text-decoration:none;color:inherit"') == desk_u(p_ch),
       lambda: href_of(ha, "Z-2031-S907", ' style="text-decoration:none;color:inherit"'))
    hi = html(own, "/desk/implants?s=" + sd._key("WALKIM THETA IMPLANTS"))
    ck("L4 the implant ledger: the paper's row -> /desk?open=<id>", lambda: href_of(hi, "Z-2031-S908") == desk_u(p_im), lambda: href_of(hi, "Z-2031-S908"))
    hmo = html(own, "/desk/month?ym=2031-06")
    ck("L5 The month: a Clinic-equipment paper's row -> /desk?open=<id>", lambda: href_of(hmo, "Z-2031-S909") == desk_u(p_eq), lambda: href_of(hmo, "Z-2031-S909"))
    ma = mach("PAPER", purchase_date="2030-02-01", price=100000)
    r_pa = own.post("/assets/%d/parts/add" % ma, data={"name": "WALK S559 FAN", "paper": "Z-2031-S910", "warranty_till": "01-01-2033"})
    hm_ = html(own, "/assets/%d" % ma)
    ck("L6 a machine page's 'its paper' -> /desk?open=<id>", lambda: r_pa.status_code in (302, 303) and href_of(hm_, "Z-2031-S910") == desk_u(p_pa),
       lambda: (r_pa.status_code, href_of(hm_, "Z-2031-S910")))
    hb_m = html(mgr, "/bills")
    ck("L7 a manager while the desk is off: his rows keep the old bill page (the desk would only say it is switched off)",
       lambda: href_of(hb_m, "WALKCL ALPHA SUPPLIES") == bill_u(p_cl) and "id=s559wait" not in hb_m and "pending</a>" in hb_m,
       lambda: href_of(hb_m, "WALKCL ALPHA SUPPLIES"))
    # S559_FIX1 B1: the papers page's Change / Open it -- a manager while the desk is off keeps /papers/<id> (where he sets a
    # paper's place), never the old bill page; the owner goes to the desk; the manager too once desk.on is switched on
    def alt_of(h):
        sg = next((x for x in (h or "").split("<div class=d6card>") if "Z-2031-S901" in x), "")
        mm = re.search(r'class="d6b alt" href="([^"]+)">', sg)
        return mm.group(1) if mm else None
    a8_m_off = alt_of(html(mgr, "/papers"))
    a8_own = alt_of(hp)
    setting("desk.on", "on")
    a8_m_on = alt_of(html(mgr, "/papers"))
    setting("desk.on", None)
    ck("L8 the papers page's Change / Open it: a manager while the desk is off -> /papers/<id> (his sorting page, not the old bill "
       "page); the owner -> /desk?open=<id>; the manager with the desk switched on -> /desk?open=<id>",
       lambda: a8_m_off == "/papers/%d" % p_cl and a8_own == desk_u(p_cl) and a8_m_on == desk_u(p_cl),
       lambda: {"manager, desk off": a8_m_off, "owner": a8_own, "manager, desk on": a8_m_on})

    # ------------------------------------------------------------------ B: the old bill page (item 5)
    pb = {k: html(own, bill_u(k)) for k in (p_cl, p_ph, p_od, p_ap, p_rj)}

    def badge(h):
        mm = re.search(r"id=s559badge[^>]*>([^<]+)</span>", h or "")
        return mm.group(1) if mm else None
    ck("B1 the bill page shows the scan inline at the top (an iframe of /bills/<id>/file, 70% of the window) with 'Open the file' under it",
       lambda: ('<iframe src="/bills/%d/file"' % p_cl) in pb[p_cl] and "height:70vh" in pb[p_cl]
       and ('<a href="/bills/%d/file" target=_blank>Open the file</a>' % p_cl) in pb[p_cl]
       and pb[p_cl].index("id=s559scan") < pb[p_cl].index("<b>Vendor:</b>") and ('<iframe src="/bills/%d/file"' % p_ph) in pb[p_ph],
       lambda: re.findall(r"<iframe[^>]*>", pb[p_cl]))
    ck("B2 'Open on the sorting desk' -> /desk?open=<id> on a clinic paper; none on a pharmacy paper",
       lambda: ('id=s559desk href="%s"' % desk_u(p_cl)) in pb[p_cl] and "s559desk" not in pb[p_ph],
       lambda: (re.findall(r'id=s559desk href="([^"]+)"', pb[p_cl]), "s559desk" in pb[p_ph]))
    ck("B3 the badge tells the truth: draft -> Waiting, captured (an Other-document paper; the pharmacy one too) -> Filed, "
       "approved -> Accepted, rejected -> Set aside",
       lambda: (badge(pb[p_cl]), badge(pb[p_od]), badge(pb[p_ph]), badge(pb[p_ap]), badge(pb[p_rj])) == ("Waiting", "Filed", "Filed", "Accepted", "Set aside")
       and ">approved</span>" not in pb[p_od],
       lambda: (badge(pb[p_cl]), badge(pb[p_od]), badge(pb[p_ph]), badge(pb[p_ap]), badge(pb[p_rj])))

    # ------------------------------------------------------------------ F: one meaning of waiting (item 6)
    hb = html(own, "/bills")
    ck("F1 All papers' header: 'N waiting on the desk ->' (the desk's N) linking to /desk; no 'pending' badge; the page is titled All papers",
       lambda: ('<h2>All papers <a href="/desk" id=s559wait' in hb) and ("%d waiting on the desk →</a>" % n_own) in hb and "pending</a>" not in hb,
       lambda: re.findall(r"<h2>.*?</h2>", hb, re.S)[:1])
    ck("F2 the status filters read: Not accepted yet (draft) . Filed (captured) . Accepted (approved) . Set aside (rejected)",
       lambda: re.findall(r"<option value=(draft|captured|approved|rejected) [^>]*>([^<]+)</option>", hb) == [
           ("draft", "Not accepted yet (draft)"), ("captured", "Filed (captured)"), ("approved", "Accepted (approved)"), ("rejected", "Set aside (rejected)")]
       and len(re.findall(r"<tr class=", html(own, "/bills?status=captured"))) >= 2,
       lambda: re.findall(r"<option[^>]*>([^<]+)</option>", hb)[-6:])

    # ------------------------------------------------------------------ N: one route each, BACK home (items 7, 8)
    scan_p = {k: th[k] for k in ("home", "bills", "papers", "desk", "month", "awaited", "implants", "assets", "renewals")}
    ck("N1 no link to /papers/month, /papers/challans or /purchases in any menu, toolbar or the home page (the owner's pages); "
       "All papers' toolbar carries ONE link to The month (/desk/month)",
       lambda: not any(OLD_LINK.search(h) for h in scan_p.values())
       and re.search(r'<p><a class=btn href="/bills/new">.*?</p>', th["bills"], re.S).group(0).count('href="/desk/month"') == 1,
       lambda: ({k: OLD_LINK.findall(h)[:3] for k, h in scan_p.items() if OLD_LINK.search(h)},
                re.search(r'<p><a class=btn href="/bills/new">.*?</p>', th["bills"], re.S).group(0).count("/desk/month")))
    o1, o2, o3 = own.get("/papers/month"), own.get("/papers/challans"), own.get("/purchases")
    ck("N2 the old pages still answer 200 by their address, each with its 'replaced by' line",
       lambda: (o1.status_code, o2.status_code, o3.status_code) == (200, 200, 200) and "Replaced by" in o1.get_data(as_text=True)
       and "Now by supplier" in o2.get_data(as_text=True) and "Replaced by The month" in o3.get_data(as_text=True),
       lambda: (o1.status_code, o2.status_code, o3.status_code))
    hbp = html(own, "/scanapp/bills")
    ck("N3 BACK on All papers goes to the scan app's home (/scanapp/), not the portal",
       lambda: '<a class=s440back href="/scanapp/">' in hbp and "/portal" not in re.search(r"<div class=s440bar>.*?</div>", hbp, re.S).group(0),
       lambda: re.findall(r"<a class=s440back href=\"([^\"]+)\"", hbp))

    # ------------------------------------------------------------------ K2: reception's own menu and slip words untouched
    k2 = as_reception(lambda: html(client(None), "/intake"))
    ck("K2 the intake's served widget is the kit's: S559.1 inside the intake-only branches (served from the app folder)",
       lambda: "__scannerS559" in client(None).get("/scan/widget.js").get_data(as_text=True) and k2 == pages["intake"],
       lambda: ("__scannerS559" in client(None).get("/scan/widget.js").get_data(as_text=True)))

    # ------------------------------------------------------------------ item 9: the small things
    zs = db.execute("SELECT id FROM zones WHERE lower(trim(name))='unassigned' ORDER BY id").fetchall()
    z_a = mach("ZONE A", zone_id=zs[0][0]) if len(zs) >= 2 else None
    z_b = mach("ZONE B", zone_id=zs[1][0]) if len(zs) >= 2 else None
    ha_ = html(own, "/assets")
    hz = html(own, "/assets?f_zone=%d" % zs[1][0]) if len(zs) >= 2 else ""
    ck("Z1 the Assets page's Zone filter lists 'Unassigned' once; choosing it shows the machines of every Unassigned zone",
       lambda: len(zs) >= 2 and ha_.count(">Unassigned</option>") == 1 and "WALK S559 MACHINE ZONE A" in hz and "WALK S559 MACHINE ZONE B" in hz
       and "selected>Unassigned</option>" in hz.replace("selected >", "selected>").replace("'selected' ", ""),
       lambda: (len(zs), ha_.count(">Unassigned</option>"), "ZONE A" in hz, "ZONE B" in hz))
    db.execute("INSERT INTO service_logs(asset_id, log_date, work, cost, done_by, is_pm, svc_type, next_due) VALUES(?,?,?,?,?,0,'Repair',?)",
               (ma, "2031-03-04", "walk fan replaced", 1200, "WALKTECH", "2031-09-04"))
    db.commit()
    hm2 = html(own, "/assets/%d" % ma)
    hr = html(own, "/renewals?all=1")
    ck("D1 dates read dd-mm-yyyy: the machine page (purchased, the service log, next due, dates to watch), Renewals, All papers' rows",
       lambda: "<b>Purchased:</b> 01-02-2030" in hm2 and "<tr><td>04-03-2031</td>" in hm2 and "04-09-2031" in hm2
       and "2030-02-01" not in hm2 and "01-01-2033" in hr and "2033-01-01" not in hr
       and re.search(r"<td>05-06-2031</td>\s*<td><a href=\"[^\"]+\">WALKAP EPSILON TRADERS</a>", th["bills"]) is not None,
       lambda: ("<b>Purchased:</b> 01-02-2030" in hm2, "<tr><td>04-03-2031</td>" in hm2, "01-01-2033" in hr, "2033-01-01" in hr))
    m_old = mach("OLDREC", contract_type="AMC", provider="WALKOLD SERVICES")
    m_none = mach("NONE")
    h_old, h_none = html(own, "/assets/%d" % m_old), html(own, "/assets/%d" % m_none)
    ck("C1 a machine whose cover lives only in its old record reads 'Covered (old record): AMC — WALKOLD SERVICES', not 'No cover'; "
       "a machine with no cover anywhere still reads 'No cover'",
       lambda: "Covered (old record): AMC — WALKOLD SERVICES" in h_old and re.search(r"id=s557cover[^>]*>No cover", h_old) is None
       and re.search(r"id=s557cover[^>]*>No cover", h_none) is not None,
       lambda: (re.findall(r"id=s557cover[^>]*>([^<]+)", h_old), re.findall(r"id=s557cover[^>]*>([^<]+)", h_none)))
    m_cmc = mach("CMCREC", contract_type="CMC")
    for lb, due in (("Contract renewal", "2032-02-01"), ("Licence renewal", "2032-03-01"), ("Insurance — WALKINS", "2032-04-01"),
                    ("Item expiry", "2032-05-01"), ("Warranty", "2032-06-01")):
        db.execute("INSERT INTO expiries(entity, entity_id, label, due_date, threshold_days) VALUES('asset',?,?,?,30)", (m_cmc, lb, due))
    db.commit()
    m_amc = mach("AMCLIVE")
    r_c1 = own.post("/assets/%d/covers/add" % m_amc, data={"kind": "amc", "provider": "WALKPROV LIVE", "till_day": "01-06-2032"})
    m_lap = mach("LAPSED")
    r_c2 = own.post("/assets/%d/covers/add" % m_lap, data={"kind": "amc", "provider": "WALKPROV OLD", "till_day": "01-01-2031"})
    hr2 = html(own, "/renewals?all=1")

    def kinds_of(aid):
        seg_ = [x for x in hr2.split("<tr") if ('href="/assets/%d"' % aid) in x]
        return [tuple(re.findall(r"<td>([^<]*)</td><td>([^<]*)</td><td>\d\d-\d\d-\d{4}</td>", x)[0]) for x in seg_ if re.findall(r"<td>([^<]*)</td><td>([^<]*)</td><td>\d\d-\d\d-\d{4}</td>", x)]
    ck("R1 Renewals' Kind column: each reminder's own kind -- Warranty / AMC / CMC (a contract renewal on a CMC machine) / "
       "Licence / Insurance / Other -- decided in one helper",
       lambda: "<th>Kind</th>" in hr2 and sorted(kinds_of(m_cmc)) == sorted([("CMC", "Contract renewal"), ("Licence", "Licence renewal"),
                                                                              ("Insurance", "Insurance — WALKINS"), ("Other", "Item expiry"), ("Warranty", "Warranty")])
       and ("AMC", "AMC — WALKPROV LIVE") in kinds_of(m_amc) and m._s559_kind("Part warranty: WALK FAN") == "Warranty",
       lambda: (kinds_of(m_cmc), kinds_of(m_amc)))
    h_amc, h_lap = html(own, "/assets/%d" % m_amc), html(own, "/assets/%d" % m_lap)
    pmw = "Preventive maintenance is covered under the AMC"
    ck("P1 the service form's 'Preventive maintenance is covered under the AMC' shows only under a live AMC/CMC: yes for a live "
       "AMC cover (and an old-record AMC), no for a lapsed AMC and for no cover",
       lambda: r_c1.status_code in (302, 303) and r_c2.status_code in (302, 303) and pmw in h_amc and pmw in h_old
       and pmw not in h_lap and pmw not in h_none and "svcTypeChange();" in h_none,
       lambda: (r_c1.status_code, r_c2.status_code, pmw in h_amc, pmw in h_old, pmw in h_lap, pmw in h_none))

    # ------------------------------------------------------------------ J: item 10, the widget (the box's part; the behaviour is the browser walk)
    jw = open(os.path.join(D, "scanner_widget.js"), encoding="utf-8").read() if os.path.exists(os.path.join(D, "scanner_widget.js")) else ""
    fw_p = opt("--from-widget")
    fw = open(fw_p, encoding="utf-8").read() if (fw_p and os.path.exists(fw_p)) else ""
    dl = [x for x in difflib.unified_diff(fw.splitlines(), jw.splitlines(), lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
    added = [x[1:] for x in dl if x[0] == "+"]
    gone = [x[1:] for x in dl if x[0] == "-"]
    ds = re.search(r"function doSave\(\)\{.*?\n  \}", jw, re.S)
    ck("J1 the widget (item 10): Save while adjusting applies adjustDone() first and closes the stage; addPage / addWhole make no "
       "page from a leftover stage; the queue takes the same pages once in 10 s -- and every changed line is S559's, inside the "
       "intake-only branches (cvScanOn / inlineStamp); nothing else moved",
       lambda: bool(fw) and ds is not None and "if (cvScanOn && adjustIdx >= 0) adjustDone();" in ds.group(0)
       and ds.group(0).index("adjustDone();") < ds.group(0).index("enqueue(pages.slice())") and "stageCloseS559();" in ds.group(0)
       and "if (staleS559()) { stageCloseS559(); return; } addCaptured(warp());" in jw
       and "    if (staleS559()) { stageCloseS559(); return; }" in jw
       and "function staleS559(){ return cvScanOn && autoPage && adjustIdx < 0; }" in jw
       and "if (lastQS559 && lastQS559.k === kS559 && tS559 - lastQS559.t < 10000) return;" in jw
       and all("S559" in a for a in added) and len(gone) == 4
       and sorted(g[:38] for g in gone) == sorted(x[:38] for x in ["    if (inlineStamp && mode === \"doc\")", "  function addPage(){ if (cvScanOn && ",
                                                                   "  function dropSrc(i){ pageSrc.splice(i, 1);", "  function clearSrc(){ pageSrc = []; pageCorners = [];"]),
       lambda: (bool(fw), len(added), len(gone), [a[:60] for a in added if "S559" not in a][:3], sorted(g[:38] for g in gone)))
    ao = re.search(r"function adjustOpen\(i\)\{.*?\n  \}", jw, re.S)
    ad = re.search(r"function adjustDone\(\)\{.*?\n  \}", jw, re.S)
    ck("J3 (S559_FIX1) the widget's two corrections: C1 -- adjustOpen's image load carries a generation, bumped by the stage-close "
       "helper and by clearSrc(), so a late Adjust image after Save never reopens the stage; C2 -- deleting an earlier page shifts "
       "adjustIdx down with it, and adjustDone stops when its page is gone (never the same page twice in one paper)",
       lambda: ao is not None and ad is not None
       and "var genS559 = ++adjGenS559;" in ao.group(0) and "if (genS559 !== adjGenS559 || !pageSrc[i]) return;" in ao.group(0)
       and ao.group(0).index("if (genS559 !== adjGenS559") < ao.group(0).index("adjustIdx = i;")
       and re.search(r"function stageCloseS559\(\)\{[^\n]*adjGenS559\+\+;", jw) is not None
       and re.search(r"function clearSrc\(\)\{[^\n]*adjGenS559\+\+;", jw) is not None
       and "if (adjustIdx === i) adjustIdx = -1; else if (adjustIdx > i) adjustIdx--;" in jw
       and "if (i >= pages.length) { stageCloseS559(); return; }" in ad.group(0)
       and ad.group(0).index("if (i >= pages.length)") < ad.group(0).index("pages[i] ="),
       lambda: (ao is not None, ad is not None, "adjGenS559" in jw, "adjustIdx--" in jw))
    ck("J2 the widget's S559 helpers sit inside the S441 block (after 'var retakeIdx'), run only where inlineStamp / the smart "
       "outline is set: the five finance surfaces and the asset page set neither",
       lambda: jw.index("var lastQS559") > jw.index("var retakeIdx = -1, upq = []") and jw.index("var lastQS559") < jw.index("end S441")
       and "if (inlineStamp) window.__scannerS559" in jw,
       lambda: ("var lastQS559" in jw,))

    # ------------------------------------------------------------------ sizes, time, the scratch copy only
    t0 = time.time(); r0 = own.get("/"); t1 = time.time()
    t2 = time.time(); r1 = own.get("/desk"); t3 = time.time()
    print("SIZES home %d B (%.0f ms) . desk %d B (%.0f ms) . All papers %d B . the bar %d B" % (
        len(r0.data), (t1 - t0) * 1000, len(r1.data), (t3 - t2) * 1000, len(th["bills"]),
        len((re.search(r"<style>\.s559h.*?</nav></div>", th["home"], re.S) or re.search("", "")).group(0))))
    ck("T1 the home page and the desk answer 200 in under 2 s with the counts in the bar", lambda: r0.status_code == 200 and r1.status_code == 200
       and (t1 - t0) < 2 and (t3 - t2) < 2)
    ck("T2 the made-up rows live in the scratch copy only", lambda: dbp.startswith(work) and state["m"].DB_PATH == dbp)
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
