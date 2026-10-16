#!/usr/bin/env python3
"""walk_s566.py -- the S566_SCANAPP_LAST_FIXES walk. The app with the given files on a COPY of a database (SQLite's backup
API), in its own scratch folder; made-up rows only (suppliers WALKxx .., stamps Z-2031-S.. and one unused B-0nnn found by
key; dated around a made-up today of 15-Jun-2031), made-up logins (walk_own_2031 / walk_mgr_2031, made here); no reader
thread, no paid call, nothing sent anywhere (a made-up key and URL). Flask's test client; no port. Isolated as walk_s563.py.

    python3 -B walk_s566.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js> <assets.db to copy> [--work DIR] [--shared DIR]
                            [--expect-red] [--keep]

One named check per item (I1-I8, and FIX1's I6b), GREEN / RED; exit 1 on any RED. --expect-red (the control on the live S563
files): exit 0 only if every check named in MUST_RED is RED. --expect-red-r0 (FIX1: the control on S566's round-0 TO files):
exit 0 only if every check named in MUST_RED_R0 (I3, I5, I6b -- the K1 review's points) is RED. Counts are printed (never a live row's content). The work folder (default: a
new folder under /tmp) is removed at the end unless --keep."""
import datetime, html as htmlmod, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "I1", "I2", "I3", "I4", "I5", "I6", "I6b", "I7", "I8")
MUST_RED_R0 = ("I3", "I5", "I6b")        # FIX1: --expect-red-r0, the control on S566's round-0 TO files (K1 points 1-3)
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js")


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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:600]) if (d and not ok) else ""))
    return ok


def quiet(fn, default=None):
    try:
        return fn()
    except Exception as e:                                                 # noqa: BLE001
        print("  (step failed: %s)" % repr(e)[:200])
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


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S566_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s566walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
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
    ck("W1 the app imports; asset_register, clinic_papers, sorting_desk, asset_machine come from the scratch folder; the database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and am is not None and under(am.__file__, appdir) and m.DB_PATH == dbp and m.UPLOAD_DIR == env["ASSETS_UPLOADS"])
    ck("W2 the S566 marks: sorting_desk LAST, clinic_papers LAST, asset_register LAST_S566 = S566 (the S563 / S560 / S559 / S557 / "
       "S555 / S551 marks kept)",
       lambda: getattr(sd, "LAST", None) == "S566" and getattr(cp, "LAST", None) == "S566" and getattr(m, "LAST_S566", None) == "S566"
       and sd.TIDY == "S563" and cp.TIDY == "S563" and m.TIDY_S563 == "S563" and am.TIDY == "S563" and sd.RECEIPTS == "S560"
       and sd.ROAD == "S559" and sd.MACHINE == "S557" and sd.CORRECTIONS == "S555" and sd.VERSION == "S551.2" and cp.VERSION == "S551")
    sd.TODAY = TODAY
    am.TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    for k in ("desk.on", "machine.on", "d710.challan_amber_days", "desk.floor", "desk.s441_days"):
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

    def aud(bid, action):
        return db.execute("SELECT * FROM bill_audit WHERE bill_id=? AND action=? ORDER BY id", (bid, action)).fetchall()

    def mk(tag, vendor, lane="clinic", status=None, created="2031-06-10 05:00:00", kind=None, items=(), reading=None, **cols_):
        kd = kind or {"clinic": "Consumable", "other_doc": "Document", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no=cols_.pop("stamp_no", None) or ("Z-2031-S" + tag), status=st, lane=lane,
                    created_at=created, submitted_at=created[:16], submitted_by="Walk")
        vals.update(cols_)
        bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        for it in items:
            db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)",
                       (bid, it[0], it[1] if len(it) > 1 else None, it[2] if len(it) > 2 else None, it[3] if len(it) > 3 else None))
        if reading is not None:
            db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data, error) VALUES(?,?,?,1,?,?,NULL)",
                       (bid, "2031-06-10 10:00", "walk-made-up", reading.get("doc_kind"), json.dumps(reading)))
        db.commit()
        return bid

    def post(cl, url, j):
        r_ = cl.post(url, json=j)
        return r_.status_code, (r_.get_json(silent=True) or {})

    def form(cl, url, data):
        r_ = cl.post(url, data=data)
        return r_.status_code

    def flashes(cl):
        with cl.session_transaction() as ss:
            f_ = list(ss.get("_flashes") or [])
            ss.pop("_flashes", None)
        return " | ".join(x[1] for x in f_)

    live_max = db.execute("SELECT COALESCE(MAX(id),0) FROM bills").fetchone()[0]

    def listed(owner):
        """The whole Waiting list (not list_json's first 300); the hint read for the made-up rows only."""
        with m.app.test_request_context("/"):
            return {b_["id"]: {"why": why_, "hint": (sd._hint(db, b_, why_) if b_["id"] > live_max else None)}
                    for b_, why_ in sd.waiting(db, owner, TODAY)}

    def month_of(bid):
        return db.execute("SELECT " + cp.MONTH_OF + " FROM bills b WHERE b.id=?", (bid,)).fetchone()[0]

    def stamp(bid):
        return row(bid).get("stamp_no") or ""

    # ------------------------------------------------------------------ I6 first: The month's base before any other made-up row
    def month_total_page(cl, ym):
        h_ = html(cl, "/desk/month?ym=" + ym)
        return sum(float(x) for x in re.findall(r'class=sectotal data-total="([0-9.\-]+)"', h_)), h_
    base6, _h = month_total_page(own, "2031-06")
    p6 = mk("P6", "WALK6 PROC SUPPLIES", status="approved", subgroup="procedure", doc_kind="bill", bill_no="P6-1", total_amount=1000,
            bill_date="2031-06-05", approved_by="Walk", approved_at="2031-06-05 10:00")
    o6 = mk("O6", "WALK6 OTHERS TRADERS", status="approved", subgroup="others", doc_kind="bill", bill_no="O6-1", total_amount=850,
            created="2031-06-08 05:00:00", approved_by="Walk", approved_at="2031-06-08 10:00")             # no bill date: the scan month
    e6 = mk("E6", "WALK6 IMPLANT HOUSE", status="draft", subgroup="implant_stock", doc_kind="estimate", bill_no="E6-1",
            total_amount=640, bill_date="2031-06-06")                                                       # an estimate slip, a draft
    after6, mh = month_total_page(own, "2031-06")
    home = html(own, "/")
    mt = quiet(lambda: sd.month_total(db, "2031-06", True))
    want_home = "₹" + m._inr(after6)
    print("I6 counts: The month's sections add to %s; the made-up rows add %s; home shows the month total: %s"
          % (m._inr(after6), m._inr(after6 - base6), want_home in home))

    # ------------------------------------------------------------------ I6b (FIX1, K1 BLOCKER 1): a held double is never money twice
    base6b, _h = month_total_page(own, "2031-06")
    mt6b0 = quiet(lambda: sd.month_total(db, "2031-06", True))
    o6b = mk("O6B", "WALK6B HELD TRADERS", status="approved", subgroup="others", doc_kind="bill", bill_no="H6-1", total_amount=500,
             bill_date="2031-06-07", approved_by="Walk", approved_at="2031-06-07 10:00")              # the accepted original
    q6b = mk("Q6B", "WALK6B HELD TRADERS", status="draft", doc_kind="bill", bill_no="H6-1", total_amount=500,
             bill_date="2031-06-07", created="2031-06-09 05:00:00")                                    # its second paper, unsorted
    c6b, j6b = post(own, "/desk/api/save", {"id": q6b, "dest": "others", "kind": "bill"})              # the desk Save -> the D710 hold
    held6b = bool(sd.held(sd._row(db, q6b), sd._marks(db, q6b)))
    after6b, mh6b = month_total_page(own, "2031-06")
    home6b = html(own, "/")
    mt6b = quiet(lambda: sd.month_total(db, "2031-06", True))
    l6b = listed(True)
    print("I6b counts: the save answered %s; the copy held: %s; The month rose by %s; month_total rose by %s; home shows the month "
          "total: %s; the copy waits on the desk: %s" % (c6b, held6b, m._inr(after6b - base6b),
                                                        m._inr((mt6b or 0) - (mt6b0 or 0)) if mt6b is not None else None,
                                                        ("₹" + m._inr(after6b)) in home6b, q6b in l6b))
    ck("I6b (FIX1, K1 BLOCKER 1) an accepted ₹500 bill plus its D710-held copy (same supplier, number, amount; NOT accepted on its "
       "desk Save) raise The month's total and home's Spend this month by ₹500, not ₹1,000 -- the copy waits on the desk as held",
       lambda: c6b == 200 and held6b and row(q6b).get("status") == "draft" and abs((after6b - base6b) - 500) < 0.005
       and mt6b is not None and mt6b0 is not None and abs((mt6b - mt6b0) - 500) < 0.005 and abs(mt6b - after6b) < 0.005
       and ("₹" + m._inr(after6b)) in home6b and q6b in l6b and "hold" in l6b[q6b]["why"],
       lambda: dict(save=c6b, msg=(j6b.get("message") or j6b.get("error") or "")[:120], held=held6b, page_delta=after6b - base6b,
                    mt0=mt6b0, mt=mt6b, page=after6b, home=("₹" + m._inr(after6b)) in home6b, listed=(l6b.get(q6b) or {}).get("why")))

    # ------------------------------------------------------------------ I1: a restored paper never counts twice blind
    p10 = mk("P10", "WALK1A ALPHA TRADERS", status="approved", subgroup="others", doc_kind="bill", bill_no="A-1", total_amount=500,
             bill_date="2031-06-02", approved_by="Walk", approved_at="2031-06-02 10:00")
    r11 = mk("R11", "WALK1A ALPHA TRADERS", lane="owner_expense", status="rejected", reject_reason="not ours", approved_by="Walk",
             approved_at="2031-06-03 10:00", subgroup="construction", bill_no="A-1", total_amount=500, created="2031-05-20 05:00:00")
    p20 = mk("P20", "WALK1B BETA TRADERS", status="approved", subgroup="others", doc_kind="bill", bill_no="B-77", total_amount=640,
             bill_date="2031-06-02", approved_by="Walk", approved_at="2031-06-02 10:00")
    r21 = mk("R21", None, status="rejected", reject_reason="blank — discarded on the sorting desk", approved_by="Walk",
             approved_at="2031-06-04 10:00", reading={"doc_kind": "tax_invoice", "vendor": "WALK1B BETA TRADERS", "bill_no": "B-77",
                                                      "total_amount": 640, "items": [{"name": "Transport", "amount": 640}]})
    fp_, fpc_ = "ab" * 32, "cd" * 8
    p30 = mk("P30", "WALK1C GAMMA", status="approved", subgroup="others", doc_kind="bill", bill_no="C-1", total_amount=111,
             bill_date="2031-06-02", fp=fp_, fpc=fpc_, approved_by="Walk", approved_at="2031-06-02 10:00")
    r31 = mk("R31", "WALK1C2 OTHER NAME", status="rejected", reject_reason="not ours", approved_by="Walk", approved_at="2031-06-04 10:00",
             subgroup="others", bill_no="C-9", total_amount=999, fp=fp_, fpc=fpc_)
    r41 = mk("R41", "WALK1D DELTA UNIQUE", lane="other_doc", status="rejected", reject_reason="not ours", approved_by="Walk",
             approved_at="2031-05-21 10:00", subgroup="construction", bill_no="D-1", total_amount=777, created="2031-05-20 05:00:00")
    r51 = mk("R51", "WALK1E EPSILON UNIQUE", status="rejected", reject_reason="not ours", approved_by="Walk",
             approved_at="2031-05-21 10:00", subgroup="others", bill_no="E-1", total_amount=333, created="2031-05-20 05:00:00")
    b11, b21, b31 = row(r11), row(r21), row(r31)
    c11, j11 = post(own, "/desk/api/restore", {"id": r11})
    c21, j21 = post(own, "/desk/api/fix", {"id": r21, "answer": "restore"})
    c31, j31 = post(own, "/desk/api/restore", {"id": r31})
    c41, j41 = post(own, "/desk/api/restore", {"id": r41})
    c51, j51 = post(own, "/desk/api/restore", {"id": r51})
    l1 = listed(True)
    st41, st51 = row(r41).get("status"), row(r51).get("status")
    hint41 = (l1.get(r41) or {}).get("hint")
    c41s, j41s = post(own, "/desk/api/save", {"id": r41, "dest": "construction", "kind": "bill"})
    l1b = listed(True)
    print("I1 counts: refused %d of 3 doubles; restored %d of 2 unique papers; listed after the restore %d, after the Save %d"
          % (sum(1 for c_ in (c11, c21, c31) if c_ == 400), sum(1 for c_ in (c41, c51) if c_ == 200),
             sum(1 for x in (r41, r51) if x in l1), sum(1 for x in (r41,) if x in l1b)))
    ck("I1 (item 1, N5) a restore runs the duplicate check first on every lane: the same supplier / number / amount as a live paper "
       "(a Personal-expense Construction paper), Claude's reading's triple on a blank-fix paper with nothing on the row, the same "
       "capture again -- each refused 'This looks like <stamp> — open it instead.', nothing written; a unique paper restores to its "
       "lane's own status (other document: captured; clinic: draft), shows in Waiting as 'restored — sort it' (scanned before the "
       "floor) until its Save",
       lambda: c11 == 400 and j11.get("error") == "This looks like %s — open it instead." % stamp(p10) and row(r11) == b11
       and not aud(r11, "desk_restored")
       and c21 == 400 and j21.get("error") == "This looks like %s — open it instead." % stamp(p20) and row(r21) == b21
       and not aud(r21, "desk_blank_restored") and not aud(r21, "desk_fix_answered")
       and c31 == 400 and stamp(p30) in (j31.get("error") or "") and row(r31) == b31
       and c41 == 200 and st41 == "captured" and c51 == 200 and st51 == "draft"
       and r41 in l1 and hint41 == "restored — sort it" and r51 in l1 and "restored" in l1[r51]["why"]
       and c41s == 200 and r41 not in l1b,
       lambda: dict(c11=c11, e11=j11.get("error"), c21=c21, e21=j21.get("error"), c31=c31, e31=j31.get("error"), c41=c41, st41=st41,
                    c51=c51, st51=st51, in41=r41 in l1, hint41=hint41, in51=r51 in l1, save=c41s, after=r41 in l1b))

    # ------------------------------------------------------------------ I2: the old challan doors check on the server
    pc = mk("C2T", "WALK2 PATIENT LAB", lane="other_doc", status="captured", subgroup="patient_paper", doc_kind="challan",
            challan_state="awaiting")
    pp = mk("C2P", "WALK2 PERSONAL SHOP", status="draft", subgroup="personal", doc_kind="challan", challan_state="awaiting")
    pl = mk("C2L", "WALK2 PLAIN SUPPLY", status="draft", subgroup="others", doc_kind="challan", challan_state="awaiting")
    hj = mk("H2J", "WALK2 HEAD SUPPLY", status="draft", subgroup="others", doc_kind="bill", bill_no="H-1")
    jp = mk("J2P", "WALK2 HEAD SUPPLY", status="rejected", subgroup="personal", doc_kind="challan", challan_state="joined",
            challan_of=hj, page_of=hj, reject_reason="joined into Z-2031-SH2J")
    pp2 = mk("C2Q", "WALK2 PERSONAL SHOP", status="draft", subgroup="personal", doc_kind="challan", challan_state="awaiting")
    pc2 = mk("C2U", "WALK2 PATIENT LAB", lane="other_doc", status="captured", subgroup="patient_paper", doc_kind="challan",
             challan_state="awaiting")
    hp = mk("H2P", "WALK2 PERSONAL HEAD", status="approved", subgroup="personal", doc_kind="bill", bill_no="HP-1")
    flashes(own); flashes(mgr)
    form(own, "/papers/challans/%d/close" % pc, {}); f_a = flashes(own)
    form(mgr, "/papers/challans/%d/close" % pp, {}); f_b = flashes(mgr)
    form(mgr, "/papers/challans/%d/close" % pl, {}); f_c = flashes(mgr)
    form(mgr, "/papers/challans/%d/delete" % jp, {}); f_d = flashes(mgr)
    form(mgr, "/papers/%d/join" % hj, {"page": str(pp2)}); f_e = flashes(mgr)
    form(own, "/papers/%d/join" % hj, {"page": str(pc2)}); f_f = flashes(own)
    form(mgr, "/papers/%d/unjoin" % hp, {}); f_g = flashes(mgr)
    form(own, "/papers/challans/%d/close" % pp, {}); f_h = flashes(own)
    wp = mk("W2P", "WALK2 WARRANTY SHOP", lane="owner_expense", status="captured", subgroup="personal", doc_kind="bill", bill_no="W-1")
    wform = {"what": "Inverter battery", "till": "2032-06-01", "remind": str(cp.REMIND[0][0])}

    def wrow():
        try:
            return db.execute("SELECT what, till FROM d664_warranty WHERE bill_id=?", (wp,)).fetchone()
        except sqlite3.Error:
            return None
    form(mgr, "/papers/%d/warranty" % wp, wform); f_w = flashes(mgr); w_m = wrow()
    form(own, "/papers/%d/warranty" % wp, wform); f_w2 = flashes(own); w_o = wrow()
    st2 ={k: row(v).get("challan_state") for k, v in (("pc", pc), ("pp", pp), ("pl", pl), ("jp", jp), ("pp2", pp2), ("pc2", pc2))}
    print("I2 counts: 7 doors that must refuse tried, %d refused" % sum(1 for f_ in (f_a, f_b, f_d, f_e, f_f, f_g, f_w) if "Nothing was changed" in f_))
    ck("I2 (item 2, N6) the old Bills awaited doors refuse on the server, nothing written: close of a patient's challan (owner too); "
       "close of a Personal challan, delete of a joined Personal challan, join of a Personal page, unjoin under a Personal head "
       "(a manager); join of a patient's challan as a page (owner); a Personal paper's warranty (a manager; R1 note 18) -- a plain "
       "challan still closes for the manager, a Personal one for the owner, the owner's warranty saves",
       lambda: "owner's alone" in f_w and w_m is None and w_o is not None and "Saved" in f_w2
       and "patient's challan" in f_a and st2["pc"] == "awaiting" and "owner's alone" in f_b
       and "owner's alone" in f_d and st2["jp"] == "joined" and "owner's alone" in f_e and row(pp2).get("page_of") is None
       and st2["pp2"] == "awaiting" and "patient's challan" in f_f and row(pc2).get("page_of") is None and st2["pc2"] == "awaiting"
       and "owner's alone" in f_g and st2["pl"] == "closed" and st2["pp"] == "closed" and "is closed" in f_h,
       lambda: dict(w=f_w[:80], w_m=bool(w_m), w_o=bool(w_o), w2=f_w2[:60], st=st2, a=f_a[:90], b=f_b[:90], c=f_c[:60], d=f_d[:90], e=f_e[:90], f=f_f[:90], g=f_g[:90], h=f_h[:60]))

    # ------------------------------------------------------------------ I3: no paper waits where nobody sees it (B-0009's shapes)
    n3_before = len(quiet(lambda: sd.waiting(db, True, TODAY), []))
    b9a = mk("9A", None, status="draft", subgroup="construction", doc_kind="challan", challan_state="awaiting", created="2031-05-11 05:00:00")
    b9b = mk("9B", "WALK9B BUILDERS", status="draft", subgroup="construction", doc_kind="challan", challan_state="closed",
             created="2031-05-11 05:00:00")
    db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
               (b9b, "2031-05-12 10:00", "Walk", "desk_saved", json.dumps({"dest": "construction", "via": "desk"}))); db.commit()
    b9c = mk("9C", "WALK9C SUPPLY CO", status="draft", subgroup="others", doc_kind="challan", challan_state="awaiting", created="2031-05-11 05:00:00")
    b9e = mk("9E", "WALK9E EQUIPMENT", status="draft", subgroup="clinic_equipment", kind="Asset", doc_kind="bill", bill_no="E9",
             total_amount=5000, created="2031-05-11 05:00:00")
    b9p = mk("9P", "WALK9P PERSONAL", status="draft", subgroup="personal", doc_kind="bill", bill_no="P9", total_amount=90,
             created="2031-05-11 05:00:00")
    b9t = mk("9T", "WALK9T PATIENT", status="draft", subgroup="patient_paper", doc_kind="bill", created="2031-05-11 05:00:00")
    seeds3 = (b9a, b9b, b9c, b9e, b9p, b9t)
    rows3 = {x: row(x) for x in seeds3}
    lo, lm = listed(True), listed(False)
    n3_after = len(quiet(lambda: sd.waiting(db, True, TODAY), []))
    with m.app.test_request_context("/"):
        m.g.user = own_u
        dn_own = quiet(lambda: m._s559_desk_n(own_u))
    added = [x for x in seeds3 if x in lo and "waiting" in lo[x]["why"]]
    rows3_mid = {x: row(x) for x in seeds3}
    # FIX1 (K1 CORRECTION 2): the closed challan's desk Save keeps it as a record and takes it off the Waiting list
    c9s, j9s = post(own, "/desk/api/save", {"id": b9b, "dest": "construction", "kind": "challan"})
    msg9 = j9s.get("message") or j9s.get("error") or ""
    lo2, lm2 = listed(True), listed(False)
    kept9 = len(aud(b9b, "desk_closed_kept"))
    print("I3 counts: the 'waiting' reason lists %d of the 6 made-up papers for the owner, %d for the manager; the owner's Waiting "
          "grew by %d; the closed challan's Save answered %s with 'kept as a record': %s, its desk_closed_kept rows %d, still listed "
          "after: owner %s, manager %s" % (len(added), len([x for x in seeds3 if x in lm]), n3_after - n3_before, c9s,
                                          "kept as a record" in msg9, kept9, b9b in lo2, b9b in lm2))
    ck("I3 (item 3; FIX1) a waiting paper is always reachable: B-0009's two shapes (a vendorless awaiting Construction challan and a "
       "closed-challan draft saved before, both scanned before the floor) are in the desk's Waiting with 'challan — supplier not "
       "read' / 'not accepted yet — check'; a challan with its supplier read stays on Bills awaited only; a Clinic-equipment draft and "
       "a Personal one for the owner only; a patient's paper never; the menu's count is the list's; no row written by the list "
       "(D664) -- and the closed challan's desk Save says 'kept as a record' (never 'Bills awaited'), writes one desk_closed_kept "
       "audit row and nothing else on the row, and takes it off Waiting for owner and manager",
       lambda: b9a in lo and lo[b9a]["hint"] == "challan — supplier not read" and b9b in lo and lo[b9b]["hint"] == "not accepted yet — check"
       and b9c not in lo and b9e in lo and b9e not in lm and b9p in lo and b9p not in lm and b9t not in lo and b9t not in lm
       and b9a in lm and b9b in lm and dn_own == n3_after and all(rows3_mid[x] == rows3[x] for x in seeds3)
       and c9s == 200 and "kept as a record" in msg9 and "Bills awaited" not in msg9 and kept9 == 1
       and b9b not in lo2 and b9b not in lm2 and b9a in lo2 and row(b9b) == rows3[b9b],
       lambda: {stamp(x): ((lo.get(x) or {}).get("hint"), x in lm) for x in seeds3} | {"desk_n": dn_own, "n": n3_after, "save": c9s,
                "msg": msg9[:120], "kept": kept9, "after_owner": b9b in lo2, "after_mgr": b9b in lm2,
                "row_same": row(b9b) == rows3[b9b]})

    # ------------------------------------------------------------------ I4: Bills awaited's count = the rows the page shows
    a1 = mk("A41", "WALK4 PLAIN SUPPLY", status="draft", subgroup="others", doc_kind="challan", challan_state="awaiting", created="2031-06-03 05:00:00")
    a2 = mk("A42", None, status="draft", subgroup="others", doc_kind="challan", challan_state="awaiting", created="2031-06-04 05:00:00")
    a3 = mk("A43", "WALK4 PERSONAL SHOP", status="draft", subgroup="personal", doc_kind="challan", challan_state="awaiting", created="2031-06-04 05:00:00")
    a4 = mk("A44", "WALK4 PATIENT LAB", lane="other_doc", status="captured", subgroup="patient_paper", doc_kind="challan",
            challan_state="awaiting", created="2031-06-04 05:00:00")
    a5 = mk("A45", "WALK4 FINAL TRADERS", status="draft", subgroup="others", doc_kind="challan", challan_state="final", total_amount=300,
            created="2031-06-04 05:00:00")
    res4 = {}
    for who, u, cl in (("owner", own_u, own), ("manager", mgr_u, mgr)):
        ow = who == "owner"
        with m.app.test_request_context("/"):
            m.g.user = u
            cards = sd.awaited(db, ow, TODAY)[0]
            n_menu = m._s559_awaited_n(u)
        open_ids = [r_["id"] for c_ in cards for r_ in c_["rows"] if not r_["final"]]
        lst = getattr(sd, "awaited_open", None) or sd.awaiting_challans
        res4[who] = dict(n_menu=n_menu, n_rows=len(open_ids), same=set(open_ids) == {c_["id"] for c_ in lst(db, ow)},
                         h=html(cl, "/desk/awaited"), ids=set(open_ids))
        print("I4 counts (%s): the menu says %s; the page shows %d open challan rows" % (who, n_menu, len(open_ids)))
    ho, hm = res4["owner"]["h"], res4["manager"]["h"]
    ck("I4 (item 4) Bills awaited: the menu's count comes from the page's own list, for owner and manager -- a challan whose supplier "
       "is not read is shown in its own card 'Supplier not read' (not dropped); a Personal one for the owner only; a patient's never; "
       "a paid-on-challan (final) row is shown but not counted",
       lambda: all(v["n_menu"] == v["n_rows"] and v["same"] for v in res4.values())
       and a2 in res4["owner"]["ids"] and a2 in res4["manager"]["ids"] and a3 in res4["owner"]["ids"] and a3 not in res4["manager"]["ids"]
       and a4 not in res4["owner"]["ids"] and a5 not in res4["owner"]["ids"] and a1 in res4["owner"]["ids"]
       and stamp(a2) in ho and "Supplier not read" in ho and stamp(a1) in ho and stamp(a3) in ho and stamp(a4) not in ho
       and stamp(a5) in ho and stamp(a2) in hm and stamp(a3) not in hm,
       lambda: {k: {kk: vv for kk, vv in v.items() if kk not in ("h", "ids")} for k, v in res4.items()}
       | {"a2_owner_page": stamp(a2) in ho, "noread": "Supplier not read" in ho})

    # ------------------------------------------------------------------ I5: a date is never stored half-read
    d1 = mk("D51", "WALK5 CLINIC READ", status="draft", subgroup="others")
    d1b = mk("D52", "WALK5 CLINIC FULL", status="draft", subgroup="others")
    d2 = mk("D53", "WALK5 PHARMA READ", lane="pharmacy", status="captured")
    quiet(lambda: m._bg_extract(d1, os.path.join(work, "uploads", "none.pdf"), _reading=({"bill_date": "14/10"}, [])))
    quiet(lambda: m._bg_extract(d1b, os.path.join(work, "uploads", "none.pdf"), _reading=({"bill_date": "14-10-2031"}, [])))
    quiet(lambda: m._bg_extract(d2, os.path.join(work, "uploads", "none.pdf"), _reading=({"bill_date": "14/10"}, [])))
    d3 = mk("D54", "WALK5 EDIT SUPPLY", status="draft", subgroup="others", bill_no="ED-1")
    flashes(own)
    form(own, "/bills/%d/edit" % d3, {"bill_date": "14/10", "vendor": "WALK5 EDIT CHANGED", "kind": "Consumable", "bill_no": "ED-1"})
    f_e5 = flashes(own); r_e5 = row(d3)
    form(own, "/bills/%d/edit" % d3, {"bill_date": "15-06-2031", "vendor": "WALK5 EDIT SUPPLY", "kind": "Consumable", "bill_no": "ED-1"})
    r_e5b = row(d3); flashes(own)
    form(own, "/bills/new", {"bill_date": "14/10", "vendor": "WALK5 NEW PAGE", "kind": "Consumable"})
    f_n5 = flashes(own)
    n_new = db.execute("SELECT COUNT(*) FROM bills WHERE vendor='WALK5 NEW PAGE'").fetchone()[0]
    # FIX1 (K1 CORRECTION 3): a stored '14/10' left as it was shown is not refused (a clinic draft, a pharmacy captured scan);
    # a newly typed partial date still is
    u1 = mk("D5U", "WALK5 UNTOUCHED CLINIC", status="draft", subgroup="others", bill_no="UT-1", bill_date="14/10")
    u2 = mk("D5V", "WALK5 UNTOUCHED PHARMA", lane="pharmacy", status="captured", bill_no="UT-2", bill_date="14/10")
    flashes(own)
    form(own, "/bills/%d/edit" % u1, {"bill_date": "14/10", "vendor": "WALK5 UNTOUCHED CLINIC FIXED", "kind": "Consumable", "bill_no": "UT-1"})
    f_u1 = flashes(own); r_u1 = row(u1)
    form(own, "/bills/%d/edit" % u2, {"bill_date": "14/10", "vendor": "WALK5 UNTOUCHED PHARMA FIXED", "kind": "Pharmacy", "bill_no": "UT-2"})
    f_u2 = flashes(own); r_u2 = row(u2)
    form(own, "/bills/%d/edit" % u1, {"bill_date": "15/10", "vendor": "WALK5 RETYPED", "kind": "Consumable", "bill_no": "UT-1"})
    f_u3 = flashes(own); r_u3 = row(u1)
    print("I5b counts: untouched '14/10' -- clinic vendor saved %s, date kept %r; pharmacy vendor saved %s, date kept %r; a newly "
          "typed '15/10' refused %s" % (r_u1.get("vendor") == "WALK5 UNTOUCHED CLINIC FIXED", r_u1.get("bill_date"),
                                        r_u2.get("vendor") == "WALK5 UNTOUCHED PHARMA FIXED", r_u2.get("bill_date"),
                                        "not a full date" in f_u3 and r_u3.get("vendor") == "WALK5 UNTOUCHED CLINIC FIXED"))
    untouched_ok = (r_u1.get("vendor") == "WALK5 UNTOUCHED CLINIC FIXED" and r_u1.get("bill_date") == "14/10" and "not a full date" not in f_u1
                    and r_u2.get("vendor") == "WALK5 UNTOUCHED PHARMA FIXED" and r_u2.get("bill_date") == "14/10" and "not a full date" not in f_u2
                    and r_u2.get("lane") == "pharmacy" and "not a full date" in f_u3 and r_u3.get("vendor") == "WALK5 UNTOUCHED CLINIC FIXED"
                    and r_u3.get("bill_date") == "14/10")
    d4 = mk("D55", "WALK5 STORED SUPPLY", status="draft", subgroup="others", doc_kind="challan", challan_state="awaiting",
            bill_date="14/10", approved_by="system — sorted = accepted (D710)", approved_at="2031-06-10 09:00")
    d5 = mk("D56", "WALK5 APPROVED SUPPLY", status="approved", subgroup="others", doc_kind="bill", bill_no="AP-1", total_amount=10,
            bill_date="2031-06-10", approved_by="Walk Approver", approved_at="2031-06-10 09:00")
    d6 = mk("D57", "WALK5 REJECTED SUPPLY", status="rejected", subgroup="others", reject_reason="not ours", bill_date="2031-06-10",
            approved_by="Walk Rejecter", approved_at="2031-06-10 09:00")
    h4 = own.get("/bills/%d" % d4); h4t = h4.get_data(as_text=True)
    h5, h6 = html(own, "/bills/%d" % d5), html(own, "/bills/%d" % d6)
    pj4 = own.get("/desk/api/paper/%d" % d4)
    codes5 = {u_: own.get(u_).status_code for u_ in ("/desk", "/desk/awaited", "/desk/month?ym=2031-06", "/papers", "/bills",
                                                    "/papers/challans", "/desk?open=%d" % d4)}
    print("I5 counts: dates stored -- clinic fill %r, full fill %r, pharmacy fill %r; the edit refused: %s; new-bill rows made: %d; "
          "pages answering 200: %d of %d" % (row(d1).get("bill_date"), row(d1b).get("bill_date"), row(d2).get("bill_date"),
                                               r_e5.get("vendor") == "WALK5 EDIT SUPPLY", n_new, list(codes5.values()).count(200), len(codes5)))
    ck("I5 (item 5) a bill date is written only as yyyy-mm-dd or left empty: the reading's fill leaves '14/10' out (a full date is "
       "written; the pharmacy lane's fill unchanged); the old edit and new-bill pages refuse it with one line, nothing saved; a "
       "stored '14/10' shows as written with the misread flag, takes the scan month (not a month called '14/10'), and every page "
       "answers; 'approved by' only on an approved paper ('rejected by' as before); FIX1: a stored '14/10' left untouched on the "
       "old edit page saves the other fields and keeps '14/10' (a clinic draft and a pharmacy captured scan), a newly typed '15/10' "
       "is refused",
       lambda: untouched_ok and row(d1).get("bill_date") is None and row(d1b).get("bill_date") == "2031-10-14" and row(d2).get("bill_date") == "14/10"
       and "not a full date" in f_e5 and r_e5.get("vendor") == "WALK5 EDIT SUPPLY" and r_e5.get("bill_date") is None
       and r_e5b.get("bill_date") == "2031-06-15" and "not a full date" in f_n5 and n_new == 0
       and month_of(d4) == "2031-06" and h4.status_code == 200 and "14/10" in h4t and "date looks misread" in h4t
       and "approved by" not in h4t and "approved by" in h5 and "rejected by" in h6
       and pj4.status_code == 200 and ((pj4.get_json(silent=True) or {}).get("flags") or {}).get("date") is True
       and all(c_ == 200 for c_ in codes5.values()),
       lambda: dict(d1=row(d1).get("bill_date"), d1b=row(d1b).get("bill_date"), d2=row(d2).get("bill_date"), fe=f_e5[:80],
                    e_vendor=r_e5.get("vendor"), e_date=r_e5.get("bill_date"), e2=r_e5b.get("bill_date"), fn=f_n5[:80], n_new=n_new,
                    mo=month_of(d4), flag="date looks misread" in h4t, appr="approved by" in h4t, h5="approved by" in h5,
                    h6="rejected by" in h6, pj=pj4.status_code, codes=codes5, untouched=untouched_ok, u1=(r_u1.get("vendor"), r_u1.get("bill_date"), f_u1[:60]),
                    u2=(r_u2.get("vendor"), r_u2.get("bill_date"), f_u2[:60]), u3=f_u3[:60]))

    # ------------------------------------------------------------------ I6: home's Spend this month = The month (computed above)
    ck("I6 (item 6) the home card's 'Spend this month' is The month's grand total (sorting_desk.month_total, the sum of its section "
       "totals, today's month): an Others paper with no bill date and an implant estimate slip (a draft) count in both",
       lambda: mt is not None and abs(mt - after6) < 0.005 and abs((after6 - base6) - 2490) < 0.005 and want_home in home
       and 'data-total="1000.00"' in mh,
       lambda: dict(month_total=mt, page=after6, delta=after6 - base6, home_has=want_home in home))

    # ------------------------------------------------------------------ I7: the Contract column never shows the word None
    loc = db.execute("SELECT id FROM locations ORDER BY id LIMIT 1").fetchone()[0]

    def mk_asset(name, contract_type):
        aid = db.execute("INSERT INTO assets(name, location_id, category, status, contract_type, created_at) "
                         "VALUES(?,?,?,'Active',?,'2031-06-01 05:00:00')", (name, loc, "Other", contract_type)).lastrowid
        db.commit()
        return aid
    an = mk_asset("WALK7 NO CONTRACT MACHINE", "None")
    aa = mk_asset("WALK7 AMC MACHINE", "AMC")
    hl = html(own, "/assets")

    def cell(name):
        i = hl.find(">%s</a>" % name)
        return hl[i:hl.find("</tr>", i)] if i >= 0 else ""
    cn, ca = cell("WALK7 NO CONTRACT MACHINE"), cell("WALK7 AMC MACHINE")
    vn, va = html(own, "/assets/%d" % an), html(own, "/assets/%d" % aa)
    ed = html(own, "/assets/%d/edit" % an)
    stored7 = db.execute("SELECT contract_type FROM assets WHERE id=?", (an,)).fetchone()[0]
    nlist = len(re.findall(r"<td>None(?:<| )", hl))
    print("I7 counts: Machines list cells reading 'None' on this copy: %d" % nlist)
    ck("I7 (item 7) the Machines list's Contract cell and the machine page's 'Contract:' line show a blank for the stored word "
       "'None' (an AMC still shows); the stored value stays 'None' and the edit form still offers it",
       lambda: cn and "<td>None" not in cn and "<td>AMC" in ca and "<b>Contract:</b> None" not in vn and "<b>Contract:</b> AMC" in va
       and stored7 == "None" and ">None</option>" in ed and nlist == 0,
       lambda: dict(cn=cn[-120:], ca=ca[-80:], vn="<b>Contract:</b> None" in vn, stored=stored7, nlist=nlist))

    # ------------------------------------------------------------------ I8: /desk?open= takes the stamp in any common form
    n8 = next(n for n in range(901, 1000) if not db.execute("SELECT 1 FROM bills WHERE upper(stamp_no)=?", ("B-%04d" % n,)).fetchone())
    b8 = mk("B8", "WALK8 OPEN SUPPLY", status="draft", subgroup="others", stamp_no="B-%04d" % n8)
    p8 = mk("P8", "WALK8 PERSONAL", status="draft", subgroup="personal", doc_kind="bill")

    def opened(cl, v):
        h_ = html(cl, "/desk?open=" + v)
        mo = re.search(r'"open":\s*(\d+)', h_)
        ln = re.search(r"<span id=s559cant[^>]*>([^<]*)</span>", h_)
        return (int(mo.group(1)) if mo else None), (htmlmod.unescape(ln.group(1)) if ln else "")
    forms8 = ["B-%04d" % n8, "b-%04d" % n8, "B-%d" % n8, "B%d" % n8, "b%d" % n8]
    got8 = {v: opened(own, v) for v in forms8}
    by_id = opened(own, str(b8))
    unk = opened(own, "B-99999")
    ref = opened(mgr, str(p8))
    with m.app.test_request_context("/"):
        bare = sd._s559_open(db, True, str(n8))[0]
    print("I8 counts: %d of %d stamp forms open the paper" % (sum(1 for v in got8.values() if v[0] == b8), len(forms8)))
    ck("I8 (item 8) /desk?open= opens the paper by its stamp written B-0nnn, b-0nnn, B-nnn, Bnnn or bnnn; a bare number stays the "
       "record id (never read as a stamp); an unknown value opens the desk with 'No paper <typed>', a refused one with the reason",
       lambda: all(v[0] == b8 for v in got8.values()) and by_id[0] == b8 and unk[0] == 0 and unk[1] == "No paper B-99999"
       and ref[0] == 0 and ref[1] == "Personal papers are the owner's alone." and (bare != b8 or n8 == b8),
       lambda: dict(forms={k: v for k, v in got8.items()}, by_id=by_id, unk=unk, ref=ref, bare=bare, id=b8))

    ck("Z1 the made-up rows live in the scratch copy only", lambda: dbp.startswith(work) and m.DB_PATH == dbp)
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
    if "--expect-red" in ARGS or "--expect-red-r0" in ARGS:
        must_ = MUST_RED_R0 if "--expect-red-r0" in ARGS else MUST_RED
        seen_ = {}
        for ok_, nm_ in zip(R, NAMES):
            seen_[nm_] = ok_
        not_red = [k for k in must_ if seen_.get(k) is not False]
        print("CONTROL must-be-red: %s -- %s" % (", ".join(must_), ("all RED" if not not_red else "NOT red: " + ", ".join(
            k + ("(green)" if seen_.get(k) else "(not reached)") for k in not_red))))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
