#!/usr/bin/env python3
"""walk_s560.py -- the S560_RECEIPTS_STATEMENTS walk. The app with the given files on a COPY of a database (SQLite's backup
API), in its own scratch folder; made-up rows only (suppliers WALKxx .., each differing in its first two words; stamps
Z-2031-R..; dated around a made-up today of 15-Jun-2031), made-up logins (walk_own_2031 / walk_mgr_2031, made here); no reader
thread, no paid call, nothing sent anywhere (a made-up key and URL). Flask's test client; no port. Isolated as walk_s559.py.

    python3 -B walk_s560.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js> <assets.db to copy> [--work DIR] [--shared DIR]
                            [--save-pages DIR] [--live-stamps] [--expect-red [--must-red R4,S3,..]] [--keep]

--save-pages DIR: the desk's page and its JSON answers for made-up papers (the browser walk measures the layout on them).
--live-stamps: print, stamps only, which papers of the COPY the fix rules list (read only; the copy is thrown away).
GREEN / RED per check; exit 1 on any RED. --expect-red (the control on the live S559 files): exit 0 only if every check named
in MUST_RED is RED. The work folder (default: a new folder under /tmp) is removed at the end unless --keep."""
import datetime, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile, time

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "W3", "K1", "K2", "R1", "R2", "R3", "S1", "S2", "P1", "V1", "F1", "L1", "D1", "C1", "C2", "X1", "X2",
            "X3", "G1", "A1", "I1", "M1", "U1", "U2", "B1", "B2", "N1", "R4", "S3", "D2", "R5", "N2", "R6")
if "--must-red" in ARGS:                                                    # FIX1: the control on the S560 kit as it was before fix round 1
    MUST_RED = tuple(x for x in ARGS[ARGS.index("--must-red") + 1].split(",") if x)
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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:400]) if (d and not ok) else ""))
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
    shared_src = opt("--shared", os.environ.get("S560_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s560walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
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
    ck("W1 the app imports; asset_register, clinic_papers, claude_reader, sorting_desk come from the scratch folder; the database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and m.DB_PATH == dbp and m.UPLOAD_DIR == env["ASSETS_UPLOADS"])
    ck("W2 the S560 marks: sorting_desk RECEIPTS, clinic_papers RECEIPTS, asset_register RECEIPTS_S560 = S560 (S559 / S557 / S555 / S551 marks kept)",
       lambda: getattr(sd, "RECEIPTS", None) == "S560" and getattr(cp, "RECEIPTS", None) == "S560" and getattr(m, "RECEIPTS_S560", None) == "S560"
       and sd.ROAD == "S559" and sd.MACHINE == "S557" and sd.CORRECTIONS == "S555" and sd.VERSION == "S551.2" and m.ROAD_S559 == "S559")
    sd.TODAY = TODAY
    if sys.modules.get("asset_machine") is not None:
        sys.modules["asset_machine"].TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    for k in ("desk.on", "machine.on", "d710.challan_amber_days", "desk.floor", "desk.s441_days"):
        db.execute("DELETE FROM settings WHERE key=?", (k,))
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
    db.commit()
    bcols = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    tabs = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    ppb = {r[1] for r in db.execute("PRAGMA table_info(paper_payment_bill)")}
    ck("W3 the database part, added at mount (ensure): bills.to_accountant (0 by default), paper_payment, paper_payment_bill with "
       "the bill's fingerprint (bill_created_at); the payment's mode limited to cash / cheque / bank",
       lambda: "to_accountant" in dict(getattr(sd, "BILL_COLS", ())) and any("paper_payment(" in x for x in getattr(sd, "DDL", ()))
       and any("paper_payment_bill(" in x and "bill_created_at" in x for x in getattr(sd, "DDL", ()))
       and "to_accountant" in bcols and {"paper_payment", "paper_payment_bill"} <= tabs and "bill_created_at" in ppb
       and "CHECK(mode IN ('cash','cheque','bank'))" in (db.execute("SELECT sql FROM sqlite_master WHERE name='paper_payment'").fetchone() or [""])[0],
       lambda: ("to_accountant" in bcols, sorted(tabs & {"paper_payment", "paper_payment_bill"}), sorted(ppb)))

    if "--live-stamps" in ARGS:
        try:
            fx = sd.fixes(db, True, datetime.date.today())
            print("LIVE-STAMPS the fix rules list on the copy (stamps and reasons only): " +
                  (" . ".join("%s %s" % (b["stamp_no"] or "#%d" % b["id"], k) for b, k, _t in fx) or "none"))
        except Exception as e:                                             # noqa: BLE001
            print("LIVE-STAMPS could not be read: %r" % e)

    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    own_u = db.execute("SELECT * FROM users WHERE username='walk_own_2031'").fetchone()
    mgr_u = db.execute("SELECT * FROM users WHERE username='walk_mgr_2031'").fetchone()

    def client(u):
        cl = m.app.test_client()
        if u is not None:
            with cl.session_transaction() as ss:
                ss["uid"] = u["id"]; ss["epoch"] = epoch
        return cl
    own, mgr = client(own_u), client(mgr_u)

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    def one(sql, *a):
        r = db.execute(sql, a).fetchone()
        return r[0] if r else None

    def row(bid):
        return db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()

    def aud(bid, action):
        return db.execute("SELECT * FROM bill_audit WHERE bill_id=? AND action=? ORDER BY id", (bid, action)).fetchall()

    def mk(tag, vendor, lane="clinic", status=None, created="2031-06-10 05:00:00", kind=None, items=(), reading=None, **cols_):
        kd = kind or {"clinic": "Consumable", "other_doc": "Document", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no="Z-2031-R" + tag, status=st, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk")
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

    def save(cl, **p):
        r = cl.post("/desk/api/save", json=p)
        try:
            return r.status_code, r.get_json() or {}
        except Exception:                                                  # noqa: BLE001
            return r.status_code, {}

    def paper(cl, bid):
        r = cl.get("/desk/api/paper/%d" % bid)
        return r.status_code, (r.get_json(silent=True) or {})

    def wlist(cl):
        j = cl.get("/desk/api/list").get_json(silent=True) or {}
        return j.get("papers") or []

    def state(bid):
        with m.app.test_request_context("/"):
            return sd.paid_state(db, db.execute("SELECT b.*, " + cp.MONTH_OF + " AS mo FROM bills b WHERE b.id=?", (bid,)).fetchone())

    def month_sec(ym, key):
        with m.app.test_request_context("/"):
            secs, _a, _n = sd.month_data(db, ym, True, TODAY)
        return next((x for x in secs if x["key"] == key), None)

    PAY = {"paid_on": "08-06-2031", "amount": "850", "mode": "cheque", "ref": "123456"}

    # ------------------------------------------------------------------ K: the five kinds; Claude's pre-choice
    G = "WALKKD GENERAL TRADERS"
    kinds_ok = {}
    for k in ("bill", "estimate", "challan"):
        bid = mk("K" + k[:2].upper(), G, bill_no="K-" + k, total_amount=100, bill_date="2031-06-05")
        code, j = save(own, id=bid, dest="others", kind=k)
        kinds_ok[k] = (code, row(bid)["doc_kind"])
    kr = mk("KRC", G, bill_no="K-rc", total_amount=55, bill_date="2031-06-06")
    code, j = save(own, id=kr, dest="others", kind="receipt", receipt=dict(PAY, pays="none", amount="55"))
    kinds_ok["receipt"] = (code, row(kr)["doc_kind"])
    ks = mk("KST", G, bill_no="K-st", total_amount=200, bill_date="2031-06-07")
    code, j = save(own, id=ks, dest="others", kind="statement", statement=dict(PAY, amount="200", covers=[], total="200"))
    kinds_ok["statement"] = (code, row(ks)["doc_kind"])
    ck("K1 the five paper kinds saved and read back: Bill . Estimate slip . Challan . Receipt . Statement (bills.doc_kind); the desk "
       "offers all five", lambda: all(v == (200, k) for k, v in kinds_ok.items()) and [x[0] for x in sd.KINDS] == ["bill", "estimate", "challan", "receipt", "statement"],
       lambda: kinds_ok)
    k_rc = mk("KC1", "WALKKC ONE PAPERS", reading={"doc_kind": "other", "vendor": "WALKKC ONE PAPERS", "total_amount": 40,
                                                    "items": [{"name": "Money receipt -- received with thanks"}]})
    k_ti = mk("KC2", "WALKKC TWO PAPERS", reading={"doc_kind": "tax_invoice", "vendor": "WALKKC TWO PAPERS", "total_amount": 40,
                                                    "items": [{"name": "Money receipt"}]})
    k_bl = mk("KC3", "WALKKC THREE PAPERS", reading={"doc_kind": "tax_invoice", "vendor": "WALKKC THREE PAPERS", "total_amount": 40,
                                                      "items": [{"name": "Gauze roll", "amount": 40}]})
    pk = {x: paper(own, x)[1] for x in (k_rc, k_ti, k_bl)}
    ck("K2 Claude's reading pre-chooses (never saves): its text says receipt AND its kind is 'other' -> Receipt; says receipt but its "
       "kind is a tax invoice -> nothing pre-chosen; a plain tax invoice -> Bill as before",
       lambda: (pk[k_rc].get("kind"), pk[k_rc].get("kind_from")) == ("receipt", "Claude's reading") and pk[k_ti].get("kind") == ""
       and pk[k_bl].get("kind") == "bill" and row(k_rc)["doc_kind"] is None,
       lambda: {x: (v.get("kind"), v.get("kind_from")) for x, v in pk.items()})

    # ------------------------------------------------------------------ R: a receipt linked to a bill; no bill; to a statement
    RA = "WALKRA ALPHA MEDICARE"
    a_bill = mk("A1", RA, status="approved", subgroup="others", doc_kind="bill", bill_no="RA-3773", total_amount=850, bill_date="2031-06-01")
    a_other = mk("A2", RA, status="approved", subgroup="others", doc_kind="bill", bill_no="RA-3000", total_amount=300, bill_date="2031-05-20")
    a_rc = mk("A3", RA, bill_no="13826", total_amount=850, bill_date="2031-06-08",
              reading={"doc_kind": "other", "vendor": RA, "bill_no": "13826", "bill_date": "2031-06-08", "total_amount": 850, "items": []})
    others_before = month_sec("2031-06", "others")
    code0, pj = paper(own, a_rc)
    cands = (pj.get("rc") or {}).get("cands") or []
    code, j = save(own, id=a_rc, dest="", kind="receipt", receipt=dict(PAY, pays=str(a_bill)))
    rr = row(a_rc)
    others_after = month_sec("2031-06", "others")
    pays_a = quiet(lambda: db.execute("SELECT p.*, a.amount alloc, a.bill_created_at FROM paper_payment p JOIN paper_payment_bill a ON a.payment_id=p.id WHERE a.bill_id=?", (a_bill,)).fetchall(), [])
    ck("R1 a receipt linked to its bill: 'Pays which bill?' lists the supplier's unpaid bills newest first, the one of the same amount "
       "pre-ticked; Save records ONE payment (cheque, its no., the bill's fingerprint, the receipt as proof); the bill reads Paid; the "
       "receipt is filed in the bill's place (clinic . Others), Filed -- never accepted, never in the month's total",
       lambda: code0 == 200 and [c["id"] for c in cands][:2] == [a_bill, a_other] and [c["id"] for c in cands if c.get("pre")] == [a_bill]
       and code == 200 and rr["doc_kind"] == "receipt" and rr["status"] == "captured" and rr["lane"] == "clinic" and rr["subgroup"] == "others"
       and len(pays_a) == 1 and pays_a[0]["mode"] == "cheque" and pays_a[0]["ref"] == "123456" and pays_a[0]["proof_bill_id"] == a_rc
       and pays_a[0]["bill_created_at"] == row(a_bill)["created_at"] and pays_a[0]["paid_on"] == "2031-06-08"
       and state(a_bill)["state"] == "paid" and others_before["total"] == others_after["total"] and a_rc not in others_after["money_ids"]
       and not aud(a_rc, "d710_accepted"),
       lambda: (code0, [(c["id"], c.get("pre")) for c in cands][:3], code, j, dict(rr) if rr else None, len(pays_a), state(a_bill)["state"],
                others_before and others_before["total"], others_after and others_after["total"]))
    ck("R2 the bill shows 'Paid 08-06-2031 . Rs850 . Cheque . no. 123456' with the receipt's scan one tap away (the desk and the old "
       "bill page); the receipt's page says what it pays",
       lambda: state(a_bill)["lines"][0]["text"] == "Paid 08-06-2031 · ₹850 · Cheque · no. 123456" and state(a_bill)["lines"][0]["proof_id"] == a_rc
       and "Paid 08-06-2031 · ₹850 · Cheque · no. 123456" in html(own, "/bills/%d" % a_bill) and "Z-2031-RA3" in html(own, "/bills/%d" % a_bill)
       and "pays Z-2031-RA1" in html(own, "/bills/%d" % a_rc) and "Paid 08-06-2031" in json.dumps(paper(own, a_bill)[1].get("pay"), ensure_ascii=False),
       lambda: (state(a_bill)["lines"], re.findall(r"id=s560paid[^>]*>(.*?)</span>", html(own, "/bills/%d" % a_bill), re.S)))
    nb = mk("NB1", "WALKNB DIRECT HOUSE", bill_no="NB-1", total_amount=75, bill_date="2031-06-09")
    code_nd, j_nd = save(own, id=nb, dest="", kind="receipt", receipt=dict(PAY, pays="none", amount="75"))
    code_nb, j_nb = save(own, id=nb, dest="lab", kind="receipt", receipt=dict(PAY, pays="none", amount="75", mode="cash", ref=""))
    pnb = quiet(lambda: db.execute("SELECT * FROM paper_payment WHERE proof_bill_id=?", (nb,)).fetchall(), [])
    ck("R3 a receipt 'No bill -- paid directly': the person chooses its place (refused without one); one payment with no bill under "
       "it; filed (NK Pathology here), never a bill",
       lambda: code_nd == 400 and code_nb == 200 and len(pnb) == 1 and pnb[0]["mode"] == "cash" and one("SELECT COUNT(*) FROM paper_payment_bill WHERE payment_id=?", pnb[0]["id"]) == 0
       and row(nb)["lane"] == "lab_purchase" and row(nb)["doc_kind"] == "receipt" and row(nb)["status"] == "captured",
       lambda: (code_nd, j_nd, code_nb, j_nb, len(pnb), dict(row(nb))))

    # ------------------------------------------------------------------ S: a statement covering three invoices (a difference)
    RS = "WALKST SIGMA COMPUTERS"
    i1 = mk("I1", RS, lane="owner_expense", bill_no="BLC-1", total_amount=300, bill_date="2031-05-05")
    i2 = mk("I2", RS, lane="owner_expense", bill_no="BLC-2", total_amount=400, bill_date="2031-05-12")
    i3 = mk("I3", RS, lane="owner_expense", bill_no="BLC-3", total_amount=500, bill_date="2031-05-20")
    i4 = mk("I4", RS, lane="owner_expense", bill_no="BLC-0", total_amount=999, bill_date="2031-02-01")
    stp = mk("ST1", RS, total_amount=1300, bill_date="2031-05-31",
             reading={"doc_kind": "other", "vendor": RS, "total_amount": 1300, "items": [{"name": "Inv 1", "amount": 300}, {"name": "Inv 2", "amount": 400},
                                                                                         {"name": "Inv 3", "amount": 500}]})
    c_st, pst = paper(own, stp)
    st_c = [c["id"] for c in ((pst.get("st") or {}).get("cands") or [])]
    code, j = save(own, id=stp, dest="", kind="statement", statement={"from": "01-05-2031", "to": "31-05-2031", "total": "1300", "paid_on": "10-06-2031",
                                                                   "amount": "1200", "mode": "cheque", "ref": "654321", "covers": [i1, i2, i3]})
    pst_rows = quiet(lambda: db.execute("SELECT a.bill_id, a.amount FROM paper_payment p JOIN paper_payment_bill a ON a.payment_id=p.id WHERE p.proof_bill_id=? ORDER BY a.bill_id", (stp,)).fetchall(), [])
    dtpl = sd.DESK_TPL
    ck("S1 a statement: its invoices offered (the supplier's unpaid ones), Save records ONE payment covering the three ticked invoices, "
       "each marked paid by it (Rs300 + Rs400 + Rs500), the fourth (outside the period) untouched; the statement filed with them "
       "(Personal expense), never counted; the desk's line 'Ticked Rs X of statement Rs Y -- difference Rs Z' and its grey line",
       lambda: c_st == 200 and set([i1, i2, i3, i4]) <= set(st_c) and code == 200 and [tuple(x) for x in pst_rows] == [(i1, 300.0), (i2, 400.0), (i3, 500.0)]
       and all(state(x)["state"] == "paid" for x in (i1, i2, i3)) and state(i4)["state"] == "unpaid"
       and row(stp)["doc_kind"] == "statement" and row(stp)["lane"] == "owner_expense" and row(stp)["status"] == "captured"
       and "'Ticked '+inr(x)+' of statement '+inr(y)+' — difference '+inr(z)" in dtpl and "An invoice may not be scanned yet." in dtpl
       and "Which invoices does it cover?" in dtpl,
       lambda: (c_st, st_c, code, j, [tuple(x) for x in pst_rows], [state(x)["state"] for x in (i1, i2, i3, i4)], dict(row(stp))))
    rsr = mk("ST2", RS, total_amount=1200, bill_date="2031-06-10")
    n_pay0 = quiet(lambda: one("SELECT COUNT(*) FROM paper_payment"), -1)
    c_r4, pj4 = paper(own, rsr)
    code, j = save(own, id=rsr, dest="", kind="receipt", receipt={"pays": "st:%d" % stp, "paid_on": "10-06-2031", "amount": "1200", "mode": "cheque", "ref": "654321"})
    ck("S2 a receipt that pays a statement: 'A statement' lists the supplier's statements; Save links it as the statement's proof -- no "
       "second payment (the money counted once); filed with the statement",
       lambda: [x["id"] for x in (pj4.get("rc") or {}).get("stmts") or []] == [stp] and code == 200 and one("SELECT COUNT(*) FROM paper_payment") == n_pay0
       and aud(rsr, "desk_receipt_to_statement") and row(rsr)["doc_kind"] == "receipt" and row(rsr)["lane"] == "owner_expense"
       and "Receipt for the statement Z-2031-RST1" in json.dumps(paper(own, rsr)[1].get("pay"), ensure_ascii=False),
       lambda: ((pj4.get("rc") or {}).get("stmts"), code, j, one("SELECT COUNT(*) FROM paper_payment"), n_pay0, dict(row(rsr))))

    # ------------------------------------------------------------------ P, V, F, L, D: part-paid, void, fingerprint, the lab lane, Paid?
    pp = mk("PP1", "WALKPP PART TRADERS", status="approved", subgroup="procedure", doc_kind="bill", bill_no="PP-1", total_amount=1000, bill_date="2031-06-02")
    code_p, j_p = save(own, id=pp, dest="procedure", kind="bill", pay={"paid_on": "09-06-2031", "amount": "400", "mode": "bank", "ref": "UTR77"})
    bl = html(own, "/bills?q=Z-2031-RPP1")
    ck("P1 part-paid: 'Paid?' of Rs400 on a Rs1,000 bill -> 'Part-paid Rs400 of Rs1,000' (the desk, the old bill page, All papers' "
       "small mark 'Part-paid')",
       lambda: code_p == 200 and state(pp)["state"] == "part" and state(pp)["word"] == "Part-paid ₹400 of ₹1,000"
       and "Part-paid ₹400 of ₹1,000" in html(own, "/bills/%d" % pp) and "id=s560mark title=\"part-paid\">Part-paid</span>" in bl,
       lambda: (code_p, j_p, state(pp)["state"], state(pp)["word"], re.findall(r"id=s560mark[^<]*<", bl)))
    pid_pp = quiet(lambda: one("SELECT payment_id FROM paper_payment_bill WHERE bill_id=?", pp), 0)
    rv = own.post("/desk/api/payment/void", json={"id": pid_pp})
    rv2 = own.post("/desk/api/payment/void", json={"id": pid_pp})
    ck("V1 a voided payment is ignored: void -> the bill unpaid again; the payment stays on record (voided_at, voided_by); voiding "
       "twice is refused",
       lambda: rv.status_code == 200 and state(pp)["state"] == "unpaid" and one("SELECT voided_at FROM paper_payment WHERE id=?", pid_pp)
       and one("SELECT voided_by FROM paper_payment WHERE id=?", pid_pp) == "Walk Owner" and rv2.status_code == 404
       and one("SELECT COUNT(*) FROM paper_payment WHERE id=?", pid_pp) == 1,
       lambda: (rv.status_code, state(pp)["state"], rv2.status_code))
    fx_b = mk("FP1", "WALKFP FINGER PRINTS", status="approved", subgroup="others", doc_kind="bill", bill_no="FP-1", total_amount=90,
              bill_date="2031-06-03", created="2031-06-03 05:00:00")
    code_f, _jf = save(own, id=fx_b, dest="others", kind="bill", pay={"paid_on": "03-06-2031", "amount": "90", "mode": "cash"})
    paid_before = quiet(lambda: state(fx_b)["state"])
    db.execute("DELETE FROM bills WHERE id=?", (fx_b,)); db.commit()
    db.execute("INSERT INTO bills(id, kind, vendor, stamp_no, status, lane, created_at, subgroup, doc_kind, total_amount, bill_date) "
               "VALUES(?,?,?,?,?,?,?,?,?,?,?)", (fx_b, "Consumable", "WALKFQ NEW PAPER", "Z-2031-RFP2", "approved", "clinic",
                                                  "2031-06-12 05:00:00", "others", "bill", 90, "2031-06-12"))
    db.commit()
    ck("F1 a re-issued bill id inherits nothing: the paid bill's id taken by a new paper (its own created_at) -> the new one unpaid; "
       "the payment kept, pointing at the old fingerprint",
       lambda: code_f == 200 and paid_before == "paid" and state(fx_b)["state"] == "unpaid" and "id=s560mark" not in html(own, "/bills?q=Z-2031-RFP2")
       and one("SELECT COUNT(*) FROM paper_payment_bill WHERE bill_id=?", fx_b) == 1,
       lambda: (code_f, paid_before, state(fx_b)["state"]))
    LB = "WALKLB LAMBDA DIAGNOSTICS"
    lb = mk("LB1", LB, lane="lab_purchase", bill_no="EN-3717", total_amount=850, bill_date="2031-06-04")
    lr = mk("LB2", LB, bill_no="13825", total_amount=850, bill_date="2031-06-08")
    code_l, j_l = save(own, id=lr, dest="", kind="receipt", receipt=dict(PAY, pays=str(lb)))
    ck("L1 a lab bill's receipt is filed on the NK Pathology lane (the lane of the bill it pays), as a receipt, Filed; the lab bill Paid",
       lambda: code_l == 200 and row(lr)["lane"] == "lab_purchase" and row(lr)["doc_kind"] == "receipt" and row(lr)["status"] == "captured"
       and state(lb)["state"] == "paid", lambda: (code_l, j_l, dict(row(lr))))
    dp = mk("DP1", "WALKDP DELTA PAINTS", status="approved", subgroup="others", doc_kind="bill", bill_no="DP-1", total_amount=640, bill_date="2031-06-05")
    code_d0, j_d0 = save(own, id=dp, dest="others", kind="bill", pay={"paid_on": "11-06-2031", "amount": "640", "mode": ""})
    code_d, j_d = save(own, id=dp, dest="others", kind="bill", pay={"paid_on": "11-06-2031", "amount": "640", "mode": "bank", "ref": "UTR9"})
    ck("D1 'Paid?' on a bill (a handwritten 'paid' note): refused without how it was paid; then one payment, no proof paper -> Paid "
       "11-06-2031 . Rs640 . Bank / UPI; All papers' mark 'Paid'",
       lambda: code_d0 == 400 and code_d == 200 and state(dp)["state"] == "paid" and state(dp)["lines"][0]["text"] == "Paid 11-06-2031 · ₹640 · Bank / UPI · no. UTR9"
       and one("SELECT proof_bill_id FROM paper_payment p JOIN paper_payment_bill a ON a.payment_id=p.id WHERE a.bill_id=?", dp) is None
       and "id=s560mark title=\"paid\">Paid</span>" in html(own, "/bills?q=Z-2031-RDP1"),
       lambda: (code_d0, j_d0, code_d, j_d, state(dp)))

    # ------------------------------------------------------------------ FIX1 B1: a payment is recorded ONCE (R4, S3, D2, R5)
    def live_pays(proof):
        return quiet(lambda: one("SELECT COUNT(*) FROM paper_payment WHERE proof_bill_id=? AND voided_at=''", proof), -1)

    def live_allocs(bid):
        return quiet(lambda: db.execute("SELECT a.payment_id, a.amount FROM paper_payment_bill a JOIN paper_payment p ON p.id=a.payment_id "
                                        "WHERE a.bill_id=? AND p.voided_at='' AND a.voided_at='' ORDER BY a.payment_id", (bid,)).fetchall(), [])

    def pre_pick(bid):                                                      # what the desk would send: the ticked bill, else 'none'
        c = [x for x in ((paper(own, bid)[1].get("rc") or {}).get("cands") or []) if x.get("pre")]
        return str(c[0]["id"]) if c else "none"
    word0 = quiet(lambda: state(a_bill)["word"])
    pk_a = pre_pick(a_rc)
    code_r4a, j_r4a = save(own, id=a_rc, dest="", kind="receipt", receipt=dict(PAY, pays=pk_a))       # the paid bill's receipt re-opened, saved
    RV = "WALKRV RECEIPT VEE"
    rv_b = mk("RV1", RV, status="approved", subgroup="others", doc_kind="bill", bill_no="RV-1", total_amount=1000, bill_date="2031-06-02")
    rv_r = mk("RV2", RV, bill_no="RV-R", total_amount=400, bill_date="2031-06-09")
    PV = {"paid_on": "09-06-2031", "amount": "400", "mode": "cheque", "ref": "4401"}
    code_r4b, _j = save(own, id=rv_r, dest="", kind="receipt", receipt=dict(PV, pays=str(rv_b)))
    w1 = quiet(lambda: state(rv_b)["word"])
    code_r4c, j_r4c = save(own, id=rv_r, dest="", kind="receipt", receipt=dict(PV, pays=pre_pick(rv_r)))     # re-saved as it was
    w2 = quiet(lambda: state(rv_b)["word"]); n2 = live_pays(rv_r)
    code_r4d, j_r4d = save(own, id=rv_r, dest="", kind="receipt", receipt=dict(PV, pays=pre_pick(rv_r), paid_on="10-06-2031", amount="450"))
    rvp = quiet(lambda: db.execute("SELECT * FROM paper_payment WHERE proof_bill_id=?", (rv_r,)).fetchall(), [])
    rv_void = quiet(lambda: one("SELECT COUNT(*) FROM paper_payment_bill WHERE bill_id=? AND voided_at<>''", rv_b), -1)
    ck("R4 a receipt re-saved records NO second payment: the paid bill's receipt re-opened (its bill still ticked) and saved -> still one "
       "payment, the bill's word unchanged; a part-paying receipt re-saved as it was -> one payment, 'Part-paid Rs400 of Rs1,000' "
       "unchanged; re-saved with a new date and Rs450 -> the SAME payment changed (one row), its old allocation voided and kept, "
       "'Part-paid Rs450 of Rs1,000'",
       lambda: pk_a == str(a_bill) and code_r4a == 200 and live_pays(a_rc) == 1 and state(a_bill)["word"] == word0 == "Paid"
       and code_r4b == 200 and w1 == "Part-paid ₹400 of ₹1,000" and code_r4c == 200 and w2 == w1 and n2 == 1
       and code_r4d == 200 and len(rvp) == 1 and rvp[0]["amount"] == 450 and rvp[0]["paid_on"] == "2031-06-10" and rvp[0]["voided_at"] == ""
       and state(rv_b)["word"] == "Part-paid ₹450 of ₹1,000" and rv_void == 1 and [tuple(x)[1] for x in live_allocs(rv_b)] == [450.0]
       and aud(rv_r, "payment_changed"),
       lambda: (pk_a, code_r4a, j_r4a, live_pays(a_rc), state(a_bill)["word"], code_r4b, w1, code_r4c, j_r4c, w2, n2, code_r4d, j_r4d,
                [dict(x) for x in rvp], rv_void))
    SV = "WALKSV STATE VEE"
    sv1 = mk("SV1", SV, lane="owner_expense", bill_no="SV-1", total_amount=300, bill_date="2031-05-06")
    sv2 = mk("SV2", SV, lane="owner_expense", bill_no="SV-2", total_amount=400, bill_date="2031-05-16")
    svs = mk("SV3", SV, total_amount=700, bill_date="2031-05-31")
    SP = {"from": "01-05-2031", "to": "31-05-2031", "total": "700", "paid_on": "12-06-2031", "amount": "700", "mode": "cheque", "ref": "7007"}
    code_s3a, _j = save(own, id=svs, dest="", kind="statement", statement=dict(SP, covers=[sv1, sv2]))
    stj = paper(own, svs)[1].get("st") or {}
    ticked = [c["id"] for c in stj.get("cands") or [] if c.get("cur")]                                # what the desk ticks on re-open
    code_s3b, j_s3b = save(own, id=svs, dest="", kind="statement", statement=dict(SP, covers=ticked))
    n_s3 = live_pays(svs); al_s3 = [live_allocs(x) for x in (sv1, sv2)]
    code_s3c, j_s3c = save(own, id=svs, dest="", kind="statement", statement=dict(SP, amount="300", covers=[sv1]))
    ck("S3 a statement re-saved records NO second payment: re-opened, its two invoices still ticked, saved -> one payment, each invoice "
       "paid once; re-saved covering only the first for Rs300 -> the same payment changed, the second invoice unpaid again",
       lambda: code_s3a == 200 and sorted(ticked) == sorted([sv1, sv2]) and code_s3b == 200 and n_s3 == 1
       and [len(x) for x in al_s3] == [1, 1] and code_s3c == 200 and live_pays(svs) == 1
       and one("SELECT COUNT(*) FROM paper_payment WHERE proof_bill_id=?", svs) == 1
       and state(sv1)["state"] == "paid" and state(sv2)["state"] == "unpaid",
       lambda: (code_s3a, ticked, code_s3b, j_s3b, n_s3, al_s3, code_s3c, j_s3c, live_pays(svs), state(sv1)["state"], state(sv2)["state"]))
    pj_dp = paper(own, dp)[1].get("pay") or {}
    n_d2 = quiet(lambda: one("SELECT COUNT(*) FROM paper_payment"), -1)
    code_d2a, j_d2a = save(own, id=dp, dest="others", kind="bill", pay={"paid_on": "12-06-2031", "amount": "640", "mode": "cash", "ref": ""})
    dpp = live_allocs(dp)
    n_d2b = quiet(lambda: one("SELECT COUNT(*) FROM paper_payment"), -1)
    code_d2b, j_d2b = save(own, id=a_bill, dest="others", kind="bill", pay={"paid_on": "12-06-2031", "amount": "850", "mode": "cash"})
    ck("D2 'Paid?' on a bill already Paid: the desk shows 'Paid on 11-06-2031 -- change?' with that payment's boxes; Save CHANGES that "
       "payment (no second one); on a bill paid by a receipt 'Paid?' is refused, and nothing is written",
       lambda: (pj_dp.get("edit") or {}).get("paid_on") == "11-06-2031" and pj_dp.get("last_on") == "11-06-2031"
       and "'Paid on '+(pp.last_on||'')+' — change?'" in sd.DESK_TPL
       and code_d2a == 200 and len(dpp) == 1 and one("SELECT COUNT(*) FROM paper_payment") == n_d2
       and one("SELECT paid_on FROM paper_payment WHERE id=?", dpp[0][0]) == "2031-06-12" and one("SELECT mode FROM paper_payment WHERE id=?", dpp[0][0]) == "cash"
       and code_d2b == 400 and "already paid" in (j_d2b.get("error") or "") and one("SELECT COUNT(*) FROM paper_payment") == n_d2b,
       lambda: (pj_dp.get("edit"), pj_dp.get("last_on"), code_d2a, j_d2a, [tuple(x) for x in dpp], code_d2b, j_d2b))
    RF = "WALKRF RHO FIVE"
    rf_b = mk("RF1", RF, status="approved", subgroup="others", doc_kind="bill", bill_no="RF-1", total_amount=500, bill_date="2031-06-03")
    rf_r = mk("RF2", RF, bill_no="RF-R", total_amount=800, bill_date="2031-06-09")
    code_r5, j_r5 = save(own, id=rf_r, dest="", kind="receipt", receipt={"pays": str(rf_b), "paid_on": "09-06-2031", "amount": "800", "mode": "cheque", "ref": "5005"})
    rf_a = live_allocs(rf_b)
    rg_b = mk("RG1", "WALKRG RHO SIX", status="approved", subgroup="others", doc_kind="bill", bill_no="RG-1", total_amount=500, bill_date="2031-06-03")
    code_r5b, _j = save(own, id=rg_b, dest="others", kind="bill", pay={"paid_on": "04-06-2031", "amount": "300", "mode": "cash"})
    rg_r = mk("RG2", "WALKRG RHO SIX", bill_no="RG-R", total_amount=500, bill_date="2031-06-09")
    code_r5c, _j = save(own, id=rg_r, dest="", kind="receipt", receipt={"pays": str(rg_b), "paid_on": "09-06-2031", "amount": "500", "mode": "cheque", "ref": "6006"})
    ck("R5 a receipt for more than the bill still owes allocates only what it owes: Rs800 against a Rs500 bill -> Rs500 on it (the "
       "payment kept as typed, the rest named in the message); Rs500 against a bill that owes Rs200 after a Rs300 'Paid?' -> Rs200",
       lambda: code_r5 == 200 and [tuple(x)[1] for x in rf_a] == [500.0] and one("SELECT amount FROM paper_payment WHERE proof_bill_id=?", rf_r) == 800
       and "not counted on it" in (j_r5.get("message") or "") and state(rf_b)["state"] == "paid"
       and code_r5b == 200 and code_r5c == 200 and sorted(tuple(x)[1] for x in live_allocs(rg_b)) == [200.0, 300.0] and state(rg_b)["word"] == "Paid",
       lambda: (code_r5, j_r5, [tuple(x) for x in rf_a], code_r5b, code_r5c, [tuple(x) for x in live_allocs(rg_b)]))
    # FIX2 C4: a clinic-lane receipt that paid a bill, re-saved as a Bill into Others
    RX = "WALKRX RHO SEVEN"
    rx_b = mk("RX1", RX, status="approved", subgroup="others", doc_kind="bill", bill_no="RX-1", total_amount=600, bill_date="2031-06-03")
    rx_r = mk("RX2", RX, bill_no="RX-R", total_amount=600, bill_date="2031-06-09")
    code_r6a, j_r6a = save(own, id=rx_r, dest="", kind="receipt", receipt={"pays": str(rx_b), "paid_on": "09-06-2031", "amount": "600", "mode": "cheque", "ref": "6606"})
    st6a, stat6a = quiet(lambda: state(rx_b)["state"]), quiet(lambda: row(rx_r)["status"])
    code_r6, j_r6 = save(own, id=rx_r, dest="others", kind="bill")
    rxp = quiet(lambda: db.execute("SELECT * FROM paper_payment WHERE proof_bill_id=?", (rx_r,)).fetchall(), [])
    rxa = quiet(lambda: db.execute("SELECT a.* FROM paper_payment_bill a JOIN paper_payment p ON p.id=a.payment_id WHERE p.proof_bill_id=?",
                                   (rx_r,)).fetchall(), [])
    oth6 = month_sec("2031-06", "others")
    ck("R6 a receipt saved as a Bill: its own payment voided (kept, with its allocation), the bill it paid reads unpaid again, the "
       "paper is accepted as a bill (approved, in the clinic's Others total), audited; nothing deleted",
       lambda: code_r6a == 200 and st6a == "paid" and stat6a == "captured" and code_r6 == 200
       and row(rx_r)["doc_kind"] == "bill" and row(rx_r)["status"] == "approved" and state(rx_b)["state"] == "unpaid"
       and len(rxp) == 1 and rxp[0]["voided_at"] != "" and len(rxa) == 1 and rxa[0]["voided_at"] != "" and live_allocs(rx_b) == []
       and oth6 is not None and rx_r in oth6["money_ids"] and rx_b in oth6["money_ids"]
       and aud(rx_r, "desk_not_spend_undone") and aud(rx_r, "payment_voided") and aud(rx_b, "payment_voided")
       and "voided (kept on record)" in (j_r6.get("message") or ""),
       lambda: (code_r6a, j_r6a, st6a, stat6a, code_r6, j_r6, row(rx_r)["doc_kind"], row(rx_r)["status"], quiet(lambda: state(rx_b)["state"]),
                [dict(x) for x in rxp], [dict(x) for x in rxa], oth6 and (rx_r in oth6["money_ids"], rx_b in oth6["money_ids"])))

    # ------------------------------------------------------------------ C: Construction's "Send to accountant"
    CW = "WALKCW CEMENT WORKS"
    cb1 = mk("CB1", CW, bill_no="CW-1", total_amount=5000, bill_date="2031-06-05")
    cb2 = mk("CB2", CW, bill_no="CW-2", total_amount=7000, bill_date="2031-06-06")
    ce = mk("CE1", CW, bill_no="CW-E", total_amount=900, bill_date="2031-06-06")
    cc = mk("CC1", CW, bill_no="CW-C", bill_date="2031-06-06")
    r1 = save(own, id=cb1, dest="construction", kind="bill", to_accountant=True)
    r2 = save(own, id=cb2, dest="construction", kind="bill")
    r3 = save(own, id=ce, dest="construction", kind="estimate", to_accountant=True)
    r4 = save(own, id=cc, dest="construction", kind="challan", to_accountant=True)
    ta = quiet(lambda: {x: row(x)["to_accountant"] for x in (cb1, cb2, ce, cc)}, {})
    r5 = save(own, id=cb1, dest="construction", kind="estimate", to_accountant=True)
    ta5 = quiet(lambda: row(cb1)["to_accountant"])
    r6 = save(own, id=cb1, dest="construction", kind="bill", to_accountant=True)
    ck("C1 'Send to accountant': on a Construction-work BILL when ticked (saved, audited); off by default; forced off for an estimate "
       "and a challan (and when a ticked bill turns into an estimate); the tick shown only for a construction bill",
       lambda: all(r[0] == 200 for r in (r1, r2, r3, r4, r5, r6)) and ta == {cb1: 1, cb2: 0, ce: 0, cc: 0} and ta5 == 0 and row(cb1)["to_accountant"] == 1
       and aud(cb1, "to_accountant") and "S.dest=='construction'&&S.kind=='bill'" in sd.DESK_TPL and "Send to accountant" in html(own, "/desk"),
       lambda: ([r[0] for r in (r1, r2, r3, r4, r5, r6)], ta, ta5, row(cb1)["to_accountant"]))
    con = month_sec("2031-06", "construction")
    ck("C2 the month page's Construction card: 'N bills . M marked for the accountant'",
       lambda: con is not None and "2 bills" in con["papers"] and "1 marked for the accountant" in con["papers"]
       and "1 marked for the accountant" in html(own, "/desk/month?ym=2031-06"), lambda: con and con["papers"])

    # ------------------------------------------------------------------ X: the papers to put right, by rule (made-up look-alikes)
    XB = "WALKXB BLANK MEDICARE"
    xb = mk("XB1", XB, status="rejected", reject_reason="blank — discarded on the sorting desk", bill_no="EN-1", total_amount=1,
            reading={"doc_kind": "tax_invoice", "vendor": XB, "bill_no": "EN-1", "total_amount": 850, "items": [{"name": "Transport", "amount": 850}]})
    db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (xb, "2031-06-10 11:00", "Walk", "desk_blank",
                                                                                            json.dumps({"status_from": "draft", "lane": "clinic", "via": "desk"})))
    XR = "WALKXR RHO MEDICARE"
    mk("XR0", XR, status="approved", subgroup="others", doc_kind="bill", bill_no="XR-1", total_amount=777, bill_date="2031-06-01")
    xr = mk("XR1", XR, lane="lab_purchase", bill_no="5555", total_amount=777, bill_date="2031-06-08",
            reading={"doc_kind": "other", "vendor": XR, "bill_no": "5555", "bill_date": "2031-06-08", "total_amount": 777, "items": []})
    xs = mk("XS1", "WALKXS SIGMA SYSTEMS", lane="owner_expense", bill_no="XS-1", total_amount=80, bill_date="2031-05-06",
            reading={"doc_kind": "other", "vendor": "WALKXS SIGMA SYSTEMS", "total_amount": 3290, "bill_no": None, "bill_date": None,
                     "items": [{"name": "Battery", "amount": 80}, {"name": "Keyboard", "amount": 75}, {"name": "Printer", "amount": 1550},
                               {"name": "Mouse", "amount": 65}]})
    xu = mk("XU1", "", status="approved", subgroup="others", items=[("Curriculum vitae",), ("Work experience",), ("Education qualification",)])
    xn = mk("XN1", "WALKXN NU SURGICALS", status="approved", subgroup="others", doc_kind="bill", bill_no="XN-1", total_amount=60, bill_date="2031-06-02",
            reading={"doc_kind": "other", "vendor": "WALKXN NU SURGICALS", "total_amount": 60, "items": [{"name": "Gauze", "amount": 60}]})
    wl = wlist(own)
    top = [(p["id"], p["hint"]) for p in wl[:12]]
    want = {xb: "Set aside as blank, but it reads as a bill — restore?", xr: "This looks like a receipt", xs: "This looks like a statement",
            xu: "looks like Resumes"}
    got = {i: h for i, h in top if i in want}
    fix_ids = [i for i, h in top if h in want.values() or h.startswith("looks like Resumes")]
    ck("X1 the papers to put right, at the top of Waiting with the reason, each by rule (no stamp in the code): set aside as blank but "
       "Claude read a supplier and an amount; Claude's 'other' paper with an amount and no goods while the supplier has a bill of that "
       "amount (a receipt); 'other' with several priced lines and no single number or date (a statement); a Resumes-like paper filed as "
       "a consumable (suggest() says resume: its grey hint); a plain bill is not listed",
       lambda: got == want and set(fix_ids[:len(want)]) >= set(want) and [p["id"] for p in wl].index(xb) < len(fixes_only(sd, db))
       and xn not in [i for i, _h in top if i in fix_ids],
       lambda: (top, got))
    rr_k = own.post("/desk/api/fix", json={"id": xr, "answer": "keep"})
    rr_r = own.post("/desk/api/fix", json={"id": xb, "answer": "restore"})
    rr_bad = own.post("/desk/api/fix", json={"id": xs, "answer": "restore"})
    wl2 = [p["id"] for p in wlist(own)]
    hint2 = {p["id"]: p["hint"] for p in wlist(own)}
    ck("X2 one tap each: Restore puts the blank set-aside back on its lane as it was (draft, the reason cleared, audited) -- it then "
       "waits to be sorted; 'No -- leave it' takes a paper off the list (audited); Restore is refused where it is not a blank",
       lambda: rr_r.status_code == 200 and row(xb)["status"] == "draft" and row(xb)["reject_reason"] is None and aud(xb, "desk_blank_restored")
       and rr_k.status_code == 200 and aud(xr, "desk_fix_answered") and hint2.get(xr) != "This looks like a receipt"
       and hint2.get(xb) != want[xb] and xb in wl2 and rr_bad.status_code == 400 and hint2.get(xs) == "This looks like a statement",
       lambda: (rr_r.status_code, dict(row(xb)), rr_k.status_code, hint2.get(xr), hint2.get(xb), rr_bad.status_code))
    code_x3, j_x3 = save(own, id=xs, dest="", kind="statement", statement={"from": "", "to": "", "total": "3290", "paid_on": "05-06-2031",
                                                                         "amount": "3290", "mode": "cheque", "ref": "99", "covers": []})
    code_x3b, j_x3b = save(own, id=xs, dest="pe", kind="statement", who="mk", statement={"from": "", "to": "", "total": "3290", "paid_on": "05-06-2031",
                                                                                       "amount": "3290", "mode": "cheque", "ref": "99", "covers": []})
    ck("X3 a person's Save answers it: the statement look-alike saved as a Statement leaves the list; no paper changes without a Save",
       lambda: code_x3 == 400 and code_x3b == 200 and row(xs)["doc_kind"] == "statement" and xs not in [p["id"] for p in wlist(own)[:6] if p["hint"].startswith("This looks")],
       lambda: (code_x3, j_x3, code_x3b, j_x3b))

    # ------------------------------------------------------------------ G: the manager's own eyes (the desk switched on for him)
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')"); db.commit()
    mh = html(mgr, "/desk")
    ml = wlist(mgr)
    db.execute("DELETE FROM settings WHERE key='desk.on'"); db.commit()
    ck("G1 the manager's own desk (signed in as him, the desk switched on): the five kinds, Save, no Personal button; the papers to "
       "put right on HIS list too (the Resumes-like paper with its grey hint)",
       lambda: "id=save" in mh and '["receipt", "Receipt"]' in mh and '["statement", "Statement"]' in mh and "Personal (you only)" not in mh
       and any(p_["id"] == xu and p_["hint"].startswith("looks like Resumes") for p_ in ml),
       lambda: ("id=save" in mh, '["receipt", "Receipt"]' in mh, "Personal (you only)" in mh, [(p_["id"], p_["hint"]) for p_ in ml[:6]]))

    # ------------------------------------------------------------------ A, I, M, U, B, N
    ach = mk("CH1", "WALKCH CHI STATIONERS", doc_kind="challan", challan_state="awaiting", subgroup="procedure", bill_date="2031-06-11",
             items=[("WALK ENVELOPE 8.5 X 10.5", 2), ("WALK TAPE", 1)])
    ha = html(own, "/desk/awaited")
    ck("A1 Bills awaited's items line prints the items (no '<built-in method items of dict object>')",
       lambda: "WALK ENVELOPE 8.5 X 10.5 × 2 · WALK TAPE × 1" in ha and "built-in method" not in ha,
       lambda: re.findall(r"built-in method[^<]{0,40}", ha)[:2])
    IM = "WALKIM IOTA IMPLANTS"
    ib = mk("IM1", IM, status="approved", subgroup="implant_stock", doc_kind="bill", bill_no="IM-1", total_amount=5000, bill_date="2031-06-02")
    key = sd._key(IM)
    db.execute("INSERT INTO implant_payment(supplier_key, day, amount, how, against, by_whom, at) VALUES(?,?,?,?,?,?,?)",
               (key, "2031-06-05", 1000, "Cheque", "IM-1", "Walk", "2031-06-05 10:00")); db.commit()
    code_i, _ji = save(own, id=ib, dest="implant_stock", kind="bill", pay={"paid_on": "06-06-2031", "amount": "2000", "mode": "cheque", "ref": "777"})
    irc = mk("IM2", IM, total_amount=5000, bill_date="2031-06-07")
    code_i2, _ji2 = save(own, id=irc, dest="implant_stock", kind="receipt", receipt={"pays": "none", "paid_on": "07-06-2031", "amount": "10", "mode": "cash"})
    with m.app.test_request_context("/"):
        lg = sd.ledger(db).get(key)
    hi = html(own, "/desk/implants?s=" + key)
    ck("I1 the implant ledger counts each payment once: its own 'Note payment' Rs1,000 + the desk's Rs2,000 = Paid Rs3,000 (both rows "
       "shown, once each); a receipt filed there is never owed",
       lambda: code_i == 200 and code_i2 == 200 and lg is not None and abs(lg["paid"] - 3000) < 0.01 and abs(lg["owed"] - 5000) < 0.01
       and len([r_ for r_ in lg["rows"] if r_["k"] == "Payment"]) == 2 and "id=paid>₹3,000<" in hi.replace("</div>", "<"),
       lambda: (code_i, code_i2, lg and (lg["paid"], lg["owed"], [(r_["k"], r_["pd"], r_["o"]) for r_ in lg["rows"]])))
    oth = month_sec("2031-06", "others")
    ck("M1 the month page: a 'paid / unpaid' count per section; receipts and statements in no total (the Others section's money ids hold "
       "none of them)",
       lambda: oth is not None and re.search(r"paid \d+ / unpaid \d+", oth["papers"]) is not None
       and not ({a_rc, kr, ks} & set(oth["money_ids"])) and "paid " in html(own, "/desk/month?ym=2031-06"),
       lambda: oth and (oth["papers"], oth["money_ids"]))
    hd = html(own, "/desk?open=%d" % a_other)
    cfg_ = quiet(lambda: json.loads(re.search(r"var C=(\{.*?\});\n", hd).group(1)), {})
    titles = None
    groups = [g[0] for g in cfg_.get("groups") or []]
    ck("U1 the desk's destinations: Clinic consumables . Clinic expense . My expense -- Dr MK / Dr Bhawna . Handed over . Documents . "
       "Not here; Personal expense shown as its two choices Dr MK / Dr Bhawna beside Personal (you only); a compact grid of buttons at "
       "least 36 px high",
       lambda: groups == ["Clinic consumables", "Clinic expense", "My expense — Dr MK / Dr Bhawna", "Handed over", "Documents", "Not here"]
       and "data-d=pe data-who=mk>Dr MK</button>" in hd and "data-d=pe data-who=bhawna>Dr Bhawna</button>" in hd and "Personal (you only)" in hd
       and ".d{min-height:36px;" in hd and ".kinds .b{min-height:36px;" in hd,
       lambda: (groups, titles))
    ck("U2 What was read folds to one line (supplier . no. . date . Rs amount . 'edit') that opens in place; the 'more' cue; Save, the "
       "join / blank row in the footer; the receipt, statement and 'Paid?' boxes",
       lambda: "<details id=readbox><summary id=readsum>" in hd and "edit ▾" in hd and "id=morecue" in hd and "id=rcpt" in hd and "id=stmt" in hd
       and "<details id=paidf" in hd and hd.index("id=foot") < hd.index("id=morecue") < hd.index("id=pagebox") < hd.index("id=save"),
       lambda: ("readbox" in hd, "morecue" in hd))
    bp = html(own, "/bills/%d" % a_bill)
    ck("B1 the old bill page: the Paid line under Total, the receipt's scan link when the receipt carries a file",
       lambda: re.search(r"<b>Total:</b> ₹850\.00<br><span id=s560paid", bp) is not None, lambda: re.findall(r"<b>Total:</b>.{0,120}", bp))
    hb = html(own, "/bills?q=WALKRA")
    ck("B2 All papers: a small 'Paid' mark on the paid bill; none on the unpaid one or on the receipt",
       lambda: len(re.findall(r"id=s560mark title=\"paid\">Paid</span>", hb)) == 1,
       lambda: re.findall(r"id=s560mark[^<]*<", hb))
    with m.app.test_request_context("/"):
        live_sql = cp._live(db)
        sec_sql = cp._live_sections(db)
    ms = one("SELECT COALESCE(SUM(total_amount),0) FROM bills WHERE status='approved' AND vendor IN (?,?,?)", RA, RS, LB)
    ck("N1 a receipt or a statement is counted as spend nowhere: the papers that count (clinic_papers._live, _live_sections) leave them "
       "out; none is ever accepted (the dashboard's approved sum holds only the bills); sorted = accepted refuses one; the heal at start "
       "never accepts one",
       lambda: "NOT IN ('challan','receipt','statement')" in live_sql and "NOT IN ('challan','receipt','statement')" in sec_sql
       and all(row(x)["status"] == "captured" for x in (a_rc, kr, ks, nb, stp, rsr, lr)) and ms == 850 + 300
       and cp._accept(db, a_rc, "walk") is False and "NOT IN ('receipt','statement')" in open(cp.__file__, encoding="utf-8").read(),
       lambda: (live_sql, ms, [row(x)["status"] for x in (a_rc, kr, ks, nb, stp, rsr, lr)]))
    n2r = mk("NR1", "WALKNR NU RECEIPTS", status="draft", subgroup="others", doc_kind="receipt", bill_no="NR-1", total_amount=90, bill_date="2031-06-05")
    n2s = mk("NR2", "WALKNS NU STATEMENTS", status="draft", subgroup="others", doc_kind="statement", bill_no="NR-2", total_amount=90, bill_date="2031-06-05")
    n2b = mk("NR3", "WALKNC NU BILLS", status="draft", subgroup="others", doc_kind="bill", bill_no="NR-3", total_amount=90, bill_date="2031-06-05")
    ra_ = own.post("/bills/%d/approve" % n2r, data={}); rs_ = own.post("/bills/%d/approve" % n2s, data={}); rb_ = own.post("/bills/%d/approve" % n2b, data={})
    ck("N2 the old bill page's Approve never approves a receipt or a statement as spend (a draft one on the clinic lane stays draft, "
       "one plain line); a draft bill is still approved there",
       lambda: row(n2r)["status"] == "draft" and row(n2s)["status"] == "draft" and row(n2b)["status"] == "approved"
       and ra_.status_code in (302, 303) and "A receipt or a statement is never approved as a bill" in open(m.__file__, encoding="utf-8").read(),
       lambda: (ra_.status_code, row(n2r)["status"], rs_.status_code, row(n2s)["status"], rb_.status_code, row(n2b)["status"]))

    # ------------------------------------------------------------------ the pages for the browser walk (made-up rows only)
    if opt("--save-pages"):
        out = opt("--save-pages")
        os.makedirs(out, exist_ok=True)
        lay = mk("LY1", "WALKLY LAYOUT SUPPLIES", bill_no="LY-1", total_amount=1234, bill_date="2031-06-12", items=[("WALK GAUZE", 2, 10, 20)])
        lrc = mk("LY2", RA, bill_no="LY-R", total_amount=300, bill_date="2031-06-13",
                 reading={"doc_kind": "other", "vendor": RA, "total_amount": 300, "bill_date": "2031-06-13", "items": []})
        S2 = "WALKSZ ZETA SYSTEMS"
        for t_, amt_, d_ in (("Z1", 300, "2031-05-05"), ("Z2", 400, "2031-05-12"), ("Z3", 500, "2031-05-20")):
            mk(t_, S2, lane="owner_expense", bill_no="SZ-" + t_, total_amount=amt_, bill_date=d_)
        lst = mk("LY3", S2, total_amount=1300, bill_date="2031-05-31")
        pages = {"desk.html": html(own, "/desk?open=%d" % lay), "list.json": own.get("/desk/api/list").get_data(as_text=True)}
        for x in (lay, lrc, lst):
            pages["paper_%d.json" % x] = own.get("/desk/api/paper/%d" % x).get_data(as_text=True)
        for k, v in pages.items():
            with open(os.path.join(out, k), "w", encoding="utf-8") as fh:
                fh.write(v)
        with open(os.path.join(out, "ids.json"), "w") as fh:
            json.dump({"bill": lay, "receipt": lrc, "statement": lst}, fh)
        print("SAVED the desk's page and %d answers for the browser walk (made-up rows only)" % (len(pages) - 1))

    t0 = time.time(); r0 = own.get("/desk"); t1 = time.time()
    t2 = time.time(); r1 = own.get("/desk/api/list"); t3 = time.time()
    print("SIZES desk %d B (%.0f ms) . list %d B (%.0f ms)" % (len(r0.data), (t1 - t0) * 1000, len(r1.data), (t3 - t2) * 1000))
    ck("T1 the desk and its list answer 200 in under 2 s", lambda: r0.status_code == 200 and r1.status_code == 200 and (t1 - t0) < 2 and (t3 - t2) < 2)
    ck("T2 the made-up rows live in the scratch copy only", lambda: dbp.startswith(work) and m.DB_PATH == dbp)
    db.close()


def fixes_only(sd, db):
    try:
        return sd.fixes(db, True, TODAY)
    except Exception:                                                      # noqa: BLE001
        return []


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
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
