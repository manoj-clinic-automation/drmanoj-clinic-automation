#!/usr/bin/env python3
"""fetch_s563.py -- item 12's proof (CP-TIDY): every clinic_papers route fetched, as the owner and as a manager, on made-up rows
(stamps Z-2031-T.., suppliers WALKT.., a made-up month 2031-06), on a COPY of a database (SQLite's backup API). Run by
walk_s563.py once per clinic_papers.py, each time in its own python3 process; the walk compares the two answers.

    python3 -B fetch_s563.py <app dir> <assets.db to copy> <out.json> [--shared DIR] [--work DIR]

GET: the body's md5 and length (no page text is written anywhere). POST: each on a FRESH copy of the made-up database --
the status, the Location, the flash, and the made-up rows afterwards (every time / batch value masked: they differ by the
minute). Nothing is sent anywhere; no reader thread; made-up logins."""
import hashlib, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile

A = sys.argv[1:]
APP, SRC, OUT = [os.path.abspath(x) for x in A[:3]]
SHARED = A[A.index("--shared") + 1] if "--shared" in A else "/root/shared"
WORK = os.path.abspath(A[A.index("--work") + 1]) if "--work" in A else tempfile.mkdtemp(prefix="s563fetch_", dir="/tmp" if os.path.isdir("/tmp") else None)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py", "scanner_widget.js")
TIMEY = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?|\b[0-9a-f]{12}\b")


def main():
    for sub in ("app", "uploads", "key", "no_portal", "shared"):
        os.makedirs(os.path.join(WORK, sub), exist_ok=True)
    for f in MODS:
        if os.path.exists(os.path.join(APP, f)):
            shutil.copy(os.path.join(APP, f), os.path.join(WORK, "app", f))
    if SHARED and os.path.isdir(SHARED):
        for f in os.listdir(SHARED):
            if f.endswith(".py"):
                shutil.copy(os.path.join(SHARED, f), os.path.join(WORK, "shared", f))
    with open(os.path.join(WORK, "key", "anthropic.key"), "w") as fh:
        fh.write("sk-ant-walk-made-up-" + "0" * 12 + "\n")
    dbp, base = os.path.join(WORK, "assets.db"), os.path.join(WORK, "base.db")
    s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True); d = sqlite3.connect(dbp); s.backup(d); s.close(); d.close()
    os.environ.update({"ASSETS_DB": dbp, "ASSETS_UPLOADS": os.path.join(WORK, "uploads"),
                       "SCANAPP_ANTHROPIC_KEY_FILE": os.path.join(WORK, "key", "anthropic.key"),
                       "SCANAPP_ANTHROPIC_URL": "https://made-up.invalid/v1/messages", "CLINIC_PORTAL_DIR": os.path.join(WORK, "no_portal"),
                       "FINANCE_LOCAL_URL": "http://127.0.0.1:9", "SHARED_LIB_DIR": os.path.join(WORK, "shared"),
                       "FINANCE_DB_FOR_SCANS": os.path.join(WORK, "no_finance.db"), "SCANNER_OPENCV_JS": os.path.join(WORK, "app", "static", "opencv.js")})
    for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(k, None)
    appdir = os.path.join(WORK, "app")
    sys.path.insert(0, appdir)
    spec = importlib.util.spec_from_file_location("asset_register", os.path.join(appdir, "asset_register.py"))
    m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db)
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    for k in ("desk.on", "machine.on", "d710.challan_amber_days"):
        db.execute("DELETE FROM settings WHERE key=?", (k,))
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
    db.commit()

    def mk(tag, vendor, lane="clinic", status=None, items=(), **c):
        kd = {"clinic": "Consumable", "other_doc": "Document", "owner_expense": "Expense", "pharmacy": "Pharmacy"}[lane]
        v = dict(kind=kd, vendor=vendor, stamp_no="Z-2031-T" + tag, status=status or ("draft" if lane == "clinic" else "captured"), lane=lane,
                 created_at="2031-06-10 05:00:00", submitted_at="2031-06-10 05:00", submitted_by="Walk", ocr_status="read")
        v.update(c)
        bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(v), ",".join("?" * len(v))), tuple(v.values())).lastrowid
        for it in items:
            db.execute("INSERT INTO bill_items(bill_id, item_name) VALUES(?,?)", (bid, it))
        return bid
    T = {}
    T["draft"] = mk("01", "WALKTA AGARWAL SURGICALS", items=("fibre cast 4 inch", "roller bandage"), bill_no="TA-1", total_amount=640, bill_date="2031-06-04")
    T["blank"] = mk("02", None)
    T["film"] = mk("03", "WALKTB FILM HOUSE", items=("DHL 8*10 150 SH",), bill_no="TB-1", total_amount=900, bill_date="2031-06-05", subgroup="xray_small", status="approved")
    T["other"] = mk("04", None, lane="other_doc", items=("curriculum vitae", "qualification", "experience"))
    T["oe"] = mk("05", "WALKTC INVERTER POINT", lane="owner_expense", items=("inverter battery",), bill_no="TC-1", total_amount=12000, bill_date="2031-06-03", pe_who="bhawna")
    T["pers"] = mk("06", "WALKTD OWN PAPERS", lane="owner_expense", subgroup="personal", total_amount=50, bill_date="2031-06-03")
    T["cons"] = mk("07", "WALKTE CEMENT TRADERS", items=("cement", "sand"), subgroup="construction", total_amount=3000, bill_date="2031-06-06", status="approved")
    T["rcpt"] = mk("08", "WALKTF RECEIPT CO", lane="other_doc", doc_kind="receipt", total_amount=640, bill_date="2031-06-07")
    T["stmt"] = mk("09", "WALKTF RECEIPT CO", lane="other_doc", doc_kind="statement", total_amount=1640, bill_date="2031-06-08")
    T["head2"] = mk("10", "WALKTG GLOVE HOUSE", status="approved", subgroup="procedure", bill_no="TG-1", total_amount=300, bill_date="2031-06-02")
    T["pg2"] = mk("11", None, status="rejected", page_of=T["head2"], reject_reason="joined into Z-2031-T10", approved_by="Walk", approved_at="2031-06-02 10:00")
    db.execute("INSERT INTO d664_join(batch, head_id, page_id, at, who, merged, page_status) VALUES('b0b0b0', ?, ?, '2031-06-02 10:00', 'Walk', 0, 'draft')",
               (T["head2"], T["pg2"]))
    T["ch"] = mk("12", "WALKTH HOTEL STATIONERS", doc_kind="challan", challan_state="awaiting", subgroup="others", total_amount=200, bill_date="2031-06-01")
    T["chp"] = mk("13", "WALKTH HOTEL STATIONERS", doc_kind="challan", challan_state="awaiting", subgroup="personal", total_amount=200, bill_date="2031-06-01")
    T["chpat"] = mk("14", "WALKTH HOTEL STATIONERS", doc_kind="challan", challan_state="awaiting", subgroup="patient_paper", total_amount=200, bill_date="2031-06-01")
    T["chph"] = mk("15", "WALKTI PHARMA", lane="pharmacy", doc_kind="challan", challan_state="awaiting", total_amount=200, bill_date="2031-06-01")
    T["chbill"] = mk("16", "WALKTH HOTEL STATIONERS", bill_no="TH-9", total_amount=200, bill_date="2031-06-09")
    T["chj"] = mk("17", "WALKTJ JOINED STATIONERS", doc_kind="challan", challan_state="joined", challan_of=T["head2"], status="rejected",
                  page_of=T["head2"], reject_reason="joined", total_amount=20, bill_date="2031-05-30")
    T["misc"] = mk("18", None, lane="other_doc", subgroup="misc", items=("notice",))
    db.execute("INSERT OR REPLACE INTO d664_warranty(bill_id, what, till, remind_days, set_by, set_at) VALUES(?,?,?,?,?,?)",
               (T["oe"], "Inverter battery", "2033-06-03", 30, "Walk", "2031-06-03 10:00"))
    db.commit()
    ids = sorted(T.values())
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    users = {r: db.execute("SELECT * FROM users WHERE username=?", ("walk_%s_2031" % r,)).fetchone() for r in ("own", "mgr")}
    db.close()
    s = sqlite3.connect(dbp); d = sqlite3.connect(base); s.backup(d); s.close(); d.close()

    def fresh():
        s_ = sqlite3.connect(base); d_ = sqlite3.connect(dbp); s_.backup(d_); s_.close(); d_.close()

    def client(who):
        cl = m.app.test_client()
        with cl.session_transaction() as ss:
            ss["uid"] = users[who]["id"]; ss["epoch"] = epoch
        return cl

    def mask(v):
        return TIMEY.sub("<t>", v) if isinstance(v, str) else v

    def rows():
        c = sqlite3.connect(dbp); c.row_factory = sqlite3.Row
        q = ",".join(str(i) for i in ids)
        out = {"bills": [[mask(x) for x in tuple(r)] for r in c.execute("SELECT * FROM bills WHERE id IN (%s) ORDER BY id" % q)],
               "audit": [[r["bill_id"], r["who"], r["action"], mask(r["detail"])] for r in c.execute("SELECT * FROM bill_audit WHERE bill_id IN (%s) ORDER BY id" % q)],
               "join": [[mask(x) for x in tuple(r)][2:] for r in c.execute("SELECT * FROM d664_join WHERE head_id IN (%s) ORDER BY id" % q)],
               "warranty": [[mask(x) for x in tuple(r)] for r in c.execute("SELECT * FROM d664_warranty WHERE bill_id IN (%s) ORDER BY bill_id" % q)]}
        c.close()
        return hashlib.md5(json.dumps(out, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    gets = ["/papers", "/papers/month", "/papers/month?ym=2031-06", "/papers/challans", "/renewals?all=1"]
    gets += ["/papers/month?ym=2031-06&g=" + g for g in ("procedure", "xray", "others", "unsorted", "construction", "resume", "misc", "personal")]
    gets += ["/papers/%d" % i for i in ids] + ["/papers/%d/join" % T[k] for k in ("draft", "head2", "film")] + ["/bills/%d" % T[k] for k in ("oe", "chbill", "head2")]
    posts = [("/bills/%d/subgroup" % T["draft"], {"subgroup": "procedure", "back": "/papers"}),
             ("/bills/%d/subgroup" % T["other"], {"subgroup": "resume"}),
             ("/bills/%d/subgroup" % T["pers"], {"subgroup": "misc"}),
             ("/bills/%d/subgroup" % T["film"], {"subgroup": ""}),
             ("/papers/%d/join" % T["draft"], {"page": str(T["blank"])}),
             ("/papers/%d/join" % T["chbill"], {"page": str(T["ch"])}),
             ("/papers/%d/unjoin" % T["head2"], {}),
             ("/papers/%d/warranty" % T["oe"], {"what": "Inverter battery", "till": "2034-01-01", "remind": "7"}),
             ("/papers/%d/warranty" % T["oe"], {"remove": "1"}),
             ("/papers/%d/pe_who" % T["oe"], {"who": "mk"}),
             ("/papers/%d/pe_who" % T["pers"], {"who": "bhawna"}),
             ("/papers/challans/%d/close" % T["ch"], {}),
             ("/papers/challans/%d/close" % T["chp"], {}),
             ("/papers/challans/%d/delete" % T["chj"], {})]
    res = {}
    for who in ("own", "mgr"):
        fresh()
        cl = client(who)
        for u in gets:
            r = cl.get(u)
            b = r.get_data()
            res["GET %s %s" % (who, u)] = {"status": r.status_code, "md5": hashlib.md5(b).hexdigest(), "len": len(b)}
        for u, form in posts:
            fresh()
            cl = client(who)
            r = cl.post(u, data=form)
            with cl.session_transaction() as ss:
                fl = [mask(x[1]) for x in (ss.get("_flashes") or [])]
            res["POST %s %s %s" % (who, u, json.dumps(form, sort_keys=True))] = {"status": r.status_code, "loc": r.headers.get("Location"),
                                                                               "flash": fl, "rows": rows()}
    with open(OUT, "w") as fh:
        json.dump(res, fh, sort_keys=True, indent=0)
    print("fetched %d answers (%d GET, %d POST, each as owner and manager)" % (len(res), len(gets), len(posts)))


if __name__ == "__main__":
    try:
        main()
    finally:
        if "--work" not in A:
            shutil.rmtree(WORK, ignore_errors=True)
