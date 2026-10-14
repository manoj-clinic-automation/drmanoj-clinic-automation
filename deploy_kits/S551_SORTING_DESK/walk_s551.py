#!/usr/bin/env python3
"""walk_s551.py -- the S551_SORTING_DESK walk. The app with the given files on a COPY of a database (SQLite's backup API),
in its own scratch folder; made-up rows only (suppliers WALKA.. WALKY, stamps Z-2031-.., dated around a made-up today of
15-Jun-2031), made-up logins; no reader thread, no paid call, nothing sent anywhere. Flask's test client; no port.

    python3 -B walk_s551.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py [, sorting_desk.py]>
                            <assets.db to copy> [--work DIR] [--shared DIR] [--expect-red] [--papers] [--keep]

GREEN / RED per check; exit 1 on any RED (--expect-red, the control on the old files: exit 0 only if every check named in
MUST_RED is RED -- S551_FIX1 N3).
--papers prints what the desk shows on the three papers of the owner's plan (stamps and choices only, no figure).
The work folder (default: a new folder under /tmp) is removed at the end unless --keep."""
import datetime, importlib.util, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, time

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "S3", "W3", "C2", "R2", "V1", "H2", "FC2", "FC3", "FC4", "FN5", "FN6")    # FIX1 N3: red on the old files, by name
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py")


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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:240]) if (d and not ok) else ""))
    return ok


def tiny_pdf(tag):
    return ("%PDF-1.1\n%% " + tag + "\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 300]>>endobj\ntrailer<</Size 4/Root 1 0 R>>\n%%EOF\n").encode()


def setup_env(work, shared_src):
    app = os.path.join(work, "app")
    return {"ASSETS_DB": os.path.join(work, "assets.db"), "ASSETS_UPLOADS": os.path.join(work, "uploads"),
            "SCANAPP_ANTHROPIC_KEY_FILE": os.path.join(work, "key", "anthropic.key"),
            "SCANAPP_ANTHROPIC_URL": "https://made-up.invalid/v1/messages",
            "CLINIC_PORTAL_DIR": os.path.join(work, "no_portal"), "FINANCE_LOCAL_URL": "http://127.0.0.1:9",
            "SHARED_LIB_DIR": os.path.join(work, "shared"), "FINANCE_DB_FOR_SCANS": os.path.join(work, "no_finance.db"),
            "SCANNER_OPENCV_JS": os.path.join(app, "static", "opencv.js")}


def import_app(work):
    app = os.path.join(work, "app")
    if app not in sys.path:
        sys.path.insert(0, app)
    spec = importlib.util.spec_from_file_location("asset_register", os.path.join(app, "asset_register.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["asset_register"] = m
    spec.loader.exec_module(m)
    return m


def under(p, d):
    return bool(p) and os.path.realpath(p).startswith(os.path.realpath(d) + os.sep)


def reimport_main(work):
    """A fresh interpreter imports the app on the same copy: init_db, migrate, the seeds and the heals run again."""
    m = import_app(work)
    cp = sys.modules.get("clinic_papers")
    ok = under(m.__file__, os.path.join(work, "app")) and cp is not None and under(cp.__file__, os.path.join(work, "app"))
    print("reimported" if ok else "reimport outside the scratch folder")
    sys.exit(0 if ok else 2)


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S551_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s551walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
    work = os.path.abspath(work)
    keep = "--keep" in ARGS
    try:
        run(D, SRC, shared_src, work)
    finally:
        if not keep:
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
    # the copy, before the import: the reader off, the desk's floor, the 15-day default, a made-up manager; desk.on absent
    c = sqlite3.connect(dbp)
    for k in ("desk.on", "d710.challan_amber_days", "desk.floor", "desk.s441_days"):
        c.execute("DELETE FROM settings WHERE key=?", (k,))
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    if not c.execute("SELECT 1 FROM users WHERE username='walk_mgr_2031'").fetchone():
        c.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_mgr_2031','Walk Manager','manager','x',1)")
    if not c.execute("SELECT 1 FROM users WHERE role='owner' AND active=1").fetchone():
        c.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_2031','Walk Owner','owner','x',1)")
    c.commit(); c.close()
    env = setup_env(work, shared_src)
    os.environ.update(env)
    for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(k, None)

    # ------------------------------------------------------------------ W: the import, isolated
    try:
        m = import_app(work)
    except Exception as e:                                                 # noqa: BLE001
        ck("W1 the app imports with these files", lambda: False, lambda: repr(e)); return
    appdir = os.path.join(work, "app")
    cp = sys.modules.get("clinic_papers")
    sd = sys.modules.get("sorting_desk")
    ck("W1 the app imports; asset_register, clinic_papers and claude_reader come from the scratch folder",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and under(m.CLAUDE.__file__, appdir))
    ck("W2 sorting_desk S551.2 (fix round 1) is mounted from the scratch folder", lambda: sd is not None and sd.VERSION == "S551.2" and under(sd.__file__, appdir))
    ck("W3 clinic_papers is S551 (the three new sections in SUB, APART_KEYS, join_pages)", lambda: cp.VERSION == "S551" and hasattr(cp, "join_pages")
       and "patient_paper" in cp.APART_KEYS and all(k in cp.SUB for k in ("implant_stock", "clinic_equipment", "patient_paper"))
       and not any(k in cp.SECTION_KEYS for k in ("implant_stock", "clinic_equipment", "patient_paper")))
    ck("W4 the shared modules come from the scratch copy; no finance database is reachable",
       lambda: (m.S441 is None or under(m.S441.__file__, os.path.join(work, "shared"))) and (m.SARVAM is None or under(m.SARVAM.__file__, os.path.join(work, "shared")))
       and (m.S441 is None or not os.path.exists(m.S441.FIN_DB)) and m.DB_PATH == dbp and m.UPLOAD_DIR == env["ASSETS_UPLOADS"])
    if sd is not None:
        sd.TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    up = env["ASSETS_UPLOADS"]
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()

    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    own_u = db.execute("SELECT * FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone()
    mgr_u = db.execute("SELECT * FROM users WHERE username='walk_mgr_2031'").fetchone()

    def client(u):
        cl = m.app.test_client()
        if u is not None:
            with cl.session_transaction() as ss:
                ss["uid"] = u["id"]; ss["epoch"] = epoch
        return cl
    own, mgr, anon = client(own_u), client(mgr_u), client(None)

    made = {}

    def mk(tag, vendor=None, lane="clinic", status=None, created="2031-06-10 05:00:00", pdf=False, items=(), **cols):
        kind = {"clinic": "Consumable", "other_doc": "Document", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kind, vendor=vendor, stamp_no="Z-2031-" + tag, status=st, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk")
        if pdf:
            fn = "walk_s551_%s.pdf" % tag.lower()
            open(os.path.join(up, fn), "wb").write(tiny_pdf(tag)); vals["source_stored"] = fn; vals["source_orig"] = fn
        vals.update(cols)
        cur = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values()))
        bid = cur.lastrowid
        for it in items:
            db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (bid, it[0], it[1], it[2] if len(it) > 2 else None, None))
        db.commit()
        made[tag] = bid
        return bid

    def row(bid):
        return dict(db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone())

    def aud(bid, action):
        return db.execute("SELECT who, detail FROM bill_audit WHERE bill_id=? AND action=? ORDER BY id", (bid, action)).fetchall()

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
        r = cl.get("/desk/api/list")
        j = r.get_json(silent=True) or {}
        return {p["id"]: p for p in (j.get("papers") or [])}

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    # ------------------------------------------------------------------ the owner's three papers (--papers): what the desk shows
    if "--papers" in ARGS and sd is not None:
        print("--- the three papers of the plan (stamps and choices only) ---")
        ids = []
        for st in ("B-0001", "B-0015"):
            r_ = db.execute("SELECT id FROM bills WHERE stamp_no=?", (st,)).fetchone()
            ids.append((st, r_[0] if r_ else None))
        r_ = db.execute("SELECT id, stamp_no FROM bills WHERE bill_no LIKE '%1952%' AND upper(COALESCE(vendor,'')) LIKE '%AINDOS%' ORDER BY id LIMIT 1").fetchone()
        ids.append(("AINDOS 1952", r_[0] if r_ else None))
        wl = wlist(own)
        for label, bid in ids:
            if not bid:
                print("PAPER %s: not found in the copy" % label); continue
            code, j = paper(own, bid)
            if code != 200:
                print("PAPER %s: the desk refuses it (%s)" % (label, j.get("error"))); continue
            print("PAPER %s = %s | waiting: %s | now: %s | status: %s | pre-selected: %s | kind: %s%s | flags: %s | hints: %s" % (
                label, j["stamp"], "yes" if bid in wl else "no", j["current"] or "not sorted", j["status"],
                sd.DEST_NAME.get(j["dest"], "nothing"), j["kind"] or "none", (" (from %s)" % j["kind_from"]) if j["kind_from"] else "",
                ",".join(k for k, v in j["flags"].items() if v) or "none", " / ".join(h[:90] for h in j["hints"]) or "none"))
        print("--- end of the three papers ---")

    # ------------------------------------------------------------------ H: the header, the menus, the banners
    t = html(own, "/bills")
    ck("H1 the header reads 'Scan app & assets' (page title and top bar)", lambda: "<title>Scan app &amp; assets</title>" in t and "Scan app &amp; assets</b>" in t and "Asset Register</b>" not in t)
    # FIX1 N2: H2 seeds its own made-up paper first (a sorted document, placed by a person), so an empty list proves nothing
    h2r = mk("H2R", "WALKH2 LIST ROW", lane="other_doc", subgroup="misc", created="2031-05-01 05:00:00", bill_no="H2-1")
    db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (h2r, "2031-05-01 10:00", "Walk Person", "subgroup", "{}")); db.commit()
    t2 = html(own, "/bills?q=Z-2031-H2R")
    ck("H2 the bills list has no instant lane drop-down (a made-up row is listed, linked to its paper)",
       lambda: "Z-2031-H2R" in t2 and ('href="/bills/%d"' % h2r) in t2 and "<select name=lane" not in t2, lambda: ("Z-2031-H2R" in t2, "<select name=lane" in t2))
    ck("H3 the bills list's history links point to The month (owner)", lambda: 'href="/desk/month">The month</a>' in t and "Consumption — now The month" in t)
    t = html(own, "/")
    ck("H4 the owner's front page carries the Switches card (three switches, Claude reading link)",
       lambda: "id=s551switches" in t and "Smart scanner" in t and "Reception buttons" in t and "Sorting desk for Shavez" in t and 'action="/desk/switch"' in t and "Claude reading" in t)
    ck("H5 the dashboard tile points to The month", lambda: 'href="/desk/month"' in t and "tap for the month" in t)
    ck("H6 a manager's front page has no Switches card", lambda: "s551switches" not in html(mgr, "/"))
    ck("H7 /purchases carries the banner 'Replaced by The month'", lambda: "Replaced by The month" in html(own, "/purchases"))
    ck("H8 the old month and challans pages carry a banner; the papers page links the desk",
       lambda: "Replaced by <a" in html(own, "/papers/month") and "Now by supplier" in html(own, "/papers/challans") and "Sorting desk" in html(own, "/papers"))

    # ------------------------------------------------------------------ S: who may open what; the switch
    t = html(mgr, "/desk")
    ck("S1 desk.on absent: a manager sees one line, not the desk", lambda: "The sorting desk opens when Dr Manoj switches it on." in t and "id=save" not in t)
    ck("S2 ...and the desk's JSON and forms refuse him", lambda: mgr.get("/desk/api/list").status_code == 403 and mgr.post("/desk/api/save", json={"id": 1}).status_code == 403)
    t = html(own, "/desk")
    ck("S3 the owner uses the desk while it is OFF", lambda: "id=save" in t and "Where does it go?" in t and "Personal (you only)" in t)
    ck("S4 a manager cannot touch the switches", lambda: mgr.post("/desk/switch", data={"key": "desk.on", "on": "1", "back": "/"}).status_code == 403)
    r_ = own.post("/desk/switch", data={"key": "desk.on", "on": "1", "back": "/"})
    ck("S5 the owner switches the desk on for Shavez: the setting /admin uses, recorded, back to the page",
       lambda: r_.status_code == 302 and r_.headers["Location"].endswith("/") and db.execute("SELECT value FROM settings WHERE key='desk.on'").fetchone()[0] == "on"
       and db.execute("SELECT COUNT(*) FROM desk_audit WHERE action='switch'").fetchone()[0] >= 1)
    t = html(mgr, "/desk")
    ck("S6 desk ON: the manager gets the desk, without the Personal button", lambda: "id=save" in t and "Personal (you only)" not in t)
    rec = {"id": None, "username": "walkrec", "display_name": "Walkrec", "role": "reception", "active": 1}
    real_cu = m.current_user
    m.current_user = lambda: rec
    try:
        codes = [anon.get(u).status_code for u in ("/desk", "/desk/api/list", "/desk/api/paper/1", "/desk/api/find?no=B-0001", "/desk/awaited", "/desk/implants", "/desk/month")]
        codes += [anon.post(u, data={}).status_code for u in ("/desk/api/save", "/desk/awaited/mode", "/desk/awaited/pay", "/desk/implants/pay", "/desk/implants/void", "/desk/implants/check", "/desk/switch")]
    finally:
        m.current_user = real_cu
    ck("S7 a reception login gets 403 on every new route", lambda: codes and all(x == 403 for x in codes), lambda: codes)
    r_ = anon.get("/desk")
    ck("S8 no login -> the login redirect", lambda: r_.status_code == 302 and "/login" in r_.headers["Location"])

    # ------------------------------------------------------------------ D: every destination, read back
    G = "WALKG GENERAL SUPPLIES"
    dests = [("D1", "procedure", "procedure"), ("D2", "xray_small", "xray_small"), ("D3", "xray_11x14", "xray_11x14"), ("D4", "others", "others"),
             ("D5", "implant_stock", "implant_stock")]
    for n_, (tag, dest, sg) in enumerate(dests):
        bid = mk(tag, G, bill_no="G-%d" % n_, total_amount=100 + n_, bill_date="2031-06-05", ocr_status="read")
        code, j = save(own, id=bid, dest=dest, kind="bill")
        rr = row(bid)
        ck("%s %s: clinic lane, sorted = accepted" % (tag, dest), lambda: code == 200 and rr["lane"] == "clinic" and rr["subgroup"] == sg and rr["status"] == "approved"
           and rr["doc_kind"] == "bill" and aud(bid, "desk_saved") and any(a["who"] for a in aud(bid, "subgroup")), lambda: (code, j, rr["subgroup"], rr["status"]))
    e2 = mk("E2", G, bill_no="G-E2", total_amount=2222, bill_date="2031-06-05", items=[("ECG machine", 1, 2222)])
    code, j = save(mgr, id=e2, dest="clinic_equipment", kind="bill")
    rr = row(e2)
    ck("D6 a manager's Clinic-equipment Save files it, NOT accepted: 'Waiting for Dr Manoj's Save'", lambda: code == 200 and rr["subgroup"] == "clinic_equipment"
       and rr["status"] == "draft" and rr["kind"] == "Asset" and "Waiting for Dr Manoj" in j.get("message", ""), lambda: (code, j, rr["status"]))
    e1 = mk("E1", G, bill_no="G-E1", total_amount=3333, bill_date="2031-06-05", items=[("Autoclave", 1, 3333)])
    save(mgr, id=e1, dest="clinic_equipment", kind="bill")
    code, j = save(own, id=e1, dest="clinic_equipment", kind="bill")
    ck("D7 ...the owner's own Save accepts it; no asset record is made", lambda: code == 200 and row(e1)["status"] == "approved"
       and db.execute("SELECT COUNT(*) FROM assets WHERE bill_id=?", (e1,)).fetchone()[0] == 0, lambda: (code, j, row(e1)["status"]))
    c1 = mk("C1", "WALKG2 BUILDERS SUPPLY", lane="other_doc", bill_no="K-1", total_amount=8079, bill_date="2031-06-04")
    c2 = mk("C2", "WALKG3 HARDWARE MART", lane="owner_expense", bill_no="K-2", total_amount=500, bill_date="2031-06-04")
    save(own, id=c1, dest="construction", kind="bill"); save(own, id=c2, dest="construction", kind="estimate")
    ck("D8 Construction work: left on its own lane (other document / personal expense), captured, its section set",
       lambda: (row(c1)["lane"], row(c1)["subgroup"], row(c1)["status"]) == ("other_doc", "construction", "captured")
       and (row(c2)["lane"], row(c2)["subgroup"], row(c2)["doc_kind"]) == ("owner_expense", "construction", "estimate"))
    p1 = mk("PE1", G, bill_no="G-P1", total_amount=410, bill_date="2031-06-05")
    save(own, id=p1, dest="pe", who="mk", kind="bill")
    rr = row(p1)
    ck("D9 Personal expense -> Dr MK: owner_expense, Expense / captured, pe_who NULL, relane audited",
       lambda: (rr["lane"], rr["kind"], rr["status"], rr["pe_who"], rr["subgroup"]) == ("owner_expense", "Expense", "captured", None, None) and aud(p1, "relane"), lambda: rr)
    p2 = mk("PE2", G, lane="other_doc", subgroup="resume", bill_no="G-P2")
    save(own, id=p2, dest="pe", who="bhawna")
    p3 = mk("PE3", G, status="approved", subgroup="procedure", bill_no="G-P3", total_amount=33, bill_date="2031-06-05", approved_by="Walk", approved_at="2031-06-06 10:00")
    save(own, id=p3, dest="pe", who="mk")
    ck("D10 Dr Bhawna: a section kept (resume), pe_who 'bhawna'; a consumable group cleared and audited as 'subgroup'",
       lambda: (row(p2)["subgroup"], row(p2)["pe_who"]) == ("resume", "bhawna") and row(p3)["subgroup"] is None and row(p3)["lane"] == "owner_expense"
       and any(json.loads(a["detail"]).get("from") == "procedure" for a in aud(p3, "subgroup")))
    ps = mk("PS1", G, bill_no="G-S1", total_amount=71, bill_date="2031-06-05")
    code_m, _ = save(mgr, id=ps, dest="personal")
    code_o, _ = save(own, id=ps, dest="personal")
    ck("D11 Personal (you only): the owner's Save sets it on its lane; a manager is refused", lambda: code_m == 403 and code_o == 200
       and (row(ps)["subgroup"], row(ps)["lane"]) == ("personal", "clinic"), lambda: (code_m, code_o, row(ps)["subgroup"]))
    ph = mk("PH1", G, bill_no="G-H1", total_amount=72, bill_date="2031-06-05")
    save(own, id=ph, dest="pharmacy")
    phc = mk("PH2", G, bill_no="G-H2", doc_kind="challan", challan_state="awaiting", bill_date="2031-06-05")
    save(own, id=phc, dest="pharmacy", kind="challan")
    ck("D12 Pharmacy -- Sanjeevni: = _lane_kind_status('pharmacy'); a challan handed over as kind Challan",
       lambda: (row(ph)["lane"], row(ph)["kind"], row(ph)["status"]) == ("pharmacy",) + tuple(m._lane_kind_status("pharmacy")) and row(ph)["subgroup"] is None
       and (row(phc)["lane"], row(phc)["kind"], row(phc)["status"]) == ("pharmacy", "Challan", "captured"))
    lb = mk("LB1", G, bill_no="G-L1", subgroup="others")
    save(own, id=lb, dest="lab")
    ck("D13 NK Pathology: lab_purchase, Lab / captured, no group", lambda: (row(lb)["lane"], row(lb)["kind"], row(lb)["status"], row(lb)["subgroup"]) == ("lab_purchase", "Lab", "captured", None))
    rs = mk("RS1", "WALKR APPLICANT 2031", lane="other_doc"); ms = mk("MS1", "WALKS NOTICE 2031", lane="other_doc")
    save(own, id=rs, dest="resume"); save(own, id=ms, dest="misc")
    ck("D14 Resumes / Miscellaneous: on their lane, the section set", lambda: (row(rs)["lane"], row(rs)["subgroup"], row(ms)["subgroup"]) == ("other_doc", "resume", "misc"))
    ap = mk("AP1", "WALKP PATIENT IMPLANTS", status="approved", subgroup="procedure", bill_no="AP-1", total_amount=9876.5, bill_date="2031-06-07",
            approved_by="Walk", approved_at="2031-06-08 10:00", pdf=True)
    appr = lambda: db.execute("SELECT COALESCE(SUM(total_amount),0) FROM bills WHERE status='approved' AND substr(bill_date,1,7)='2031-06' AND id=?", (ap,)).fetchone()[0]   # noqa: E731
    before = appr()
    code, j = save(own, id=ap, dest="patient_paper")
    rr = row(ap)
    ra = aud(ap, "relane")
    ck("D15 an APPROVED clinic paper -> A patient's paper: other_doc, Document / captured, out of the approved total, 'relane' by the person",
       lambda: code == 200 and before == 9876.5 and appr() == 0 and (rr["lane"], rr["kind"], rr["status"], rr["subgroup"]) == ("other_doc", "Document", "captured", "patient_paper")
       and ra and ra[-1]["who"] == own_u["display_name"] and json.loads(ra[-1]["detail"]).get("via") == "desk"
       and json.loads(ra[-1]["detail"]).get("status_from") == "approved" and rr["approved_by"] == "Walk", lambda: (code, j, rr["status"], rr["lane"]))
    bl = mk("BL1", None)
    save(own, id=bl, blank=True)
    ck("D16 Blank -- discard: rejected, kept on record, 'desk_blank'", lambda: row(bl)["status"] == "rejected" and aud(bl, "desk_blank"))
    hd = mk("HD1", G, bill_no="G-HD", total_amount=150, bill_date="2031-06-05", pdf=True)
    pg = mk("PG1", None, lane="other_doc", pdf=True)
    code, j = save(own, id=pg, page_of="Z-2031-HD1")
    apg = mk("APG", G, status="approved", bill_no="G-AG", total_amount=1, approved_by="Walk")
    code2, j2 = save(own, id=apg, page_of="Z-2031-HD1")
    ck("D17 A page of another paper: joined through the shared join (d664_join, 'joined into'); an approved paper refused",
       lambda: code == 200 and row(pg)["page_of"] == hd and row(pg)["status"] == "rejected" and db.execute("SELECT COUNT(*) FROM d664_join WHERE page_id=?", (pg,)).fetchone()[0] == 1
       and code2 == 400 and row(apg)["page_of"] is None, lambda: (code, j, code2, j2))
    phx = mk("PHX", G, lane="pharmacy", bill_no="G-X")
    ck("D18 a pharmacy-lane paper is never listed, never opened, never saved on the desk",
       lambda: phx not in wlist(own) and paper(own, phx)[0] == 403 and save(own, id=phx, dest="procedure")[0] == 400 and row(phx)["lane"] == "pharmacy")
    a2 = mk("AF1", G, status="approved", subgroup="others", bill_no="G-F1", total_amount=999, bill_date="2031-06-01", approved_by="Walk",
            items=[("Register", 2, 50), ("Pen box", 1, 20)])
    code, j = save(own, id=a2, dest="others", kind="bill", vendor="WALKG GENERAL SUPPLIES CO", bill_no="G-F1", bill_date="05-06-2031", total_amount="1,250")
    rr = row(a2)
    ck("D19 an approved paper's header corrected with bill_edit's normalisation; its items untouched",
       lambda: code == 200 and rr["vendor"] == "WALKG GENERAL SUPPLIES CO" and rr["total_amount"] == 1250.0 and rr["bill_date"] == "2031-06-05"
       and db.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (a2,)).fetchone()[0] == 2 and aud(a2, "desk_fields"), lambda: (code, j, rr))
    code, j = save(own, id=a2, dest="others", total_amount="12x")
    ck("D20 a bad amount refuses the whole Save; nothing changes (one transaction)", lambda: code == 400 and row(a2)["total_amount"] == 1250.0)

    # ------------------------------------------------------------------ P: what is pre-selected, never saved
    yv = mk("YV1", "WALKY YUVIKA-TEST 2031", items=[("Fibre cast 4 in", 6), ("Roller bandage", 12)])
    hb = mk("HB1", "WALKH HANDWRITTEN BANDAGES", items=[("Fibre cast 4 in", 6), ("Roller bandage", 12)])
    _c, jy = paper(own, yv); _c, jh = paper(own, hb)
    ck("P1 Yuvika is never pre-selected (the same items from another supplier are)", lambda: jy.get("dest") == "" and jh.get("dest") == "procedure"
       and any("Yuvika" in h for h in jy.get("hints", [])), lambda: (jy.get("dest"), jh.get("dest")))
    pt = mk("PT0", "WALKP PATIENT IMPLANTS", bill_no="PT-0", items=[("Hip stem", 1)])
    db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
               (pt, "2031-06-10 10:00", "walk", "tax_invoice", json.dumps({"made_out_to": "patient", "items": [{"name": "Hip stem", "qty": 1, "unit": "set"}]})))
    db.commit()
    _c, jp = paper(own, pt)
    rr = row(pt)
    ck("P2 Claude read 'made out to a patient' -> A patient's paper pre-selected, with the line; nothing saved",
       lambda: jp.get("dest") == "patient_paper" and "made out to a patient" in (jp.get("hints") or [""])[0] and jp.get("kind") == "bill"
       and (rr["lane"], rr["subgroup"], rr["status"]) == ("clinic", None, "draft") and not aud(pt, "desk_saved"), lambda: (jp.get("dest"), rr))
    kn = mk("KN1", "WALKK LIGHTS-TEST ELECTRICALS", items=[("Gate light fittings", 4), ("Wire", 2), ("Switch", 3)])
    _c, jk = paper(own, kn)
    ck("P3 a section suggested by suggest() is a grey hint only (D664): nothing pre-selected", lambda: jk.get("dest") == ""
       and any("Construction work" in h for h in jk.get("hints", [])), lambda: jk)

    # ------------------------------------------------------------------ C: challans, by supplier
    A, Av, B_, Cc, F_ = "WALKA MONTHLY TRADERS", "Walka Monthly Traders Pvt Ltd", "WALKB SOMETIMES STORES", "WALKC OTHER AGENCIES", "WALKF PAID STATIONERS"
    ca0 = mk("CA0", A, doc_kind="challan", challan_state="awaiting", bill_date="2031-04-08", created="2031-04-08 05:00:00", items=[("Register", 1)])
    ca3 = mk("CA3", A, doc_kind="challan", challan_state="awaiting", bill_date="2031-05-12", created="2031-05-12 05:00:00", items=[("Register", 1)])
    ca1 = mk("CA1", A, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-02", created="2031-06-02 05:00:00", items=[("Register", 2), ("Pen box", 1)], pdf=True)
    ca2 = mk("CA2", A, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-09", created="2031-06-09 05:00:00", items=[("File cover", 10)], pdf=True)
    ca4 = mk("CA4", A, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-11", created="2031-06-11 05:00:00", items=[("Stapler", 1)])
    r_ = own.post("/desk/awaited/mode", data={"key": "walka monthly", "name": A, "mode": "monthly"})
    ck("C1 one tap sets a supplier to Monthly bill (challan_supplier; desk_audit)", lambda: r_.status_code == 302
       and db.execute("SELECT mode FROM challan_supplier WHERE supplier_key='walka monthly'").fetchone()[0] == "monthly"
       and db.execute("SELECT COUNT(*) FROM desk_audit WHERE action='challan_mode'").fetchone()[0] >= 1)
    code, j = save(own, id=ca1, dest="others", kind="challan")
    save(own, id=ca4, dest="others", kind="challan")
    ck("C2 a grouped clinic challan is filed but NOT accepted (draft, awaiting) -- it can still be joined",
       lambda: code == 200 and (row(ca1)["subgroup"], row(ca1)["status"], row(ca1)["challan_state"]) == ("others", "draft", "awaiting"), lambda: (code, j, row(ca1)))
    ba = mk("BA1", Av, bill_no="WA-31", total_amount=640, bill_date="2031-06-14", items=[("Register", 2), ("Pen box", 1), ("File cover", 10), ("Toner", 1)])
    _c, jb = paper(own, ba)
    cv = {x["id"]: x for x in jb.get("covers", [])}
    ck("C3 a monthly supplier's bill: the month's challans pre-ticked (spellings merged), not other months'; Challan pre-chosen from the supplier",
       lambda: set(cv) == {ca1, ca2, ca4} and all(x["ticked"] for x in cv.values()) and jb.get("kind") == "challan" and "bills every month" in jb.get("supplier_note", ""),
       lambda: (list(cv), jb.get("kind"), jb.get("supplier_note")))
    cmp_ = sd.compare_items([n for n, _q, _u in sd.items_of(db, row_obj(db, ba))], ["Register", "Pen box", "File cover"]) if sd else {}
    ck("C4 the item compare: '3 of 3 match - 1 extra on the bill - 0 missing'", lambda: (cmp_["match"], cmp_["of"], cmp_["extra"], cmp_["missing"]) == (3, 3, 1, 0), lambda: cmp_)
    code, j = save(own, id=ba, dest="others", kind="bill", joins=[ca1, ca2])
    ck("C5 Save joins the ticked challans through join_pages; the bill accepted", lambda: code == 200 and row(ca1)["page_of"] == ba and row(ca2)["page_of"] == ba
       and row(ca1)["challan_state"] == "joined" and row(ba)["status"] == "approved" and row(ca4)["challan_state"] == "awaiting", lambda: (code, j))
    cb1 = mk("CB1", B_, doc_kind="challan", challan_state="awaiting", bill_date="2031-05-01", created="2031-05-01 05:00:00", items=[("Glove box", 4)])
    cb2 = mk("CB2", B_, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-05", created="2031-06-05 05:00:00", items=[("Gauze", 10)])
    own.post("/desk/awaited/mode", data={"key": "walkb sometimes", "name": B_, "mode": "sometimes"})
    bb = mk("BB1", B_, bill_no="WB-1", total_amount=300, bill_date="2031-06-13", items=[("Gauze", 10)])
    _c, jb = paper(own, bb)
    cvl = jb.get("covers", [])
    ck("C6 a now-and-then supplier: every open challan, unticked, oldest first, with its age", lambda: [x["id"] for x in cvl] == [cb1, cb2]
       and not any(x["ticked"] for x in cvl) and cvl[0]["age"] == 45, lambda: cvl)
    bb2 = mk("BB2", B_, status="approved", subgroup="others", bill_no="WB-2", total_amount=301, bill_date="2031-06-12", created="2031-06-12 05:00:00", approved_by="Walk")
    w = wlist(own)
    ck("C7 waiting rule (d): a sorted bill of a supplier with an open challan, scanned after the floor, not yet saved on the desk",
       lambda: bb2 in w and "covers" in w[bb2]["why"], lambda: w.get(bb2))
    cc1 = mk("CC1", Cc, doc_kind="challan", challan_state="awaiting", bill_date="2031-05-20", created="2031-05-20 05:00:00", items=[("Toner", 1)])
    cc2 = mk("CC2", Cc, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-10", created="2031-06-10 05:00:00", items=[("Toner", 1)])
    cards = {c_["key"]: c_ for c_ in sd.awaited(db, True, TODAY)[0]} if sd else {}
    amb = {r__["id"]: r__["amber"] for c_ in cards.values() for r__ in c_["rows"]}
    ck("C8 amber rules against the made-up today: monthly -> after the 10th of next month (April, May amber; June not); now and then never; any other after 15 days",
       lambda: amb[ca0] and amb[ca3] and not amb[ca4] and not amb[cb1] and not amb[cb2] and amb[cc1] and not amb[cc2] and sd.CP._amber_days(db) == 15, lambda: amb)
    ck("C9 the monthly rule's edges: a bill of the month clears it; on the 10th not yet; on the 11th amber",
       lambda: not sd.challan_amber("monthly", "2031-05", 40, True, TODAY, 15) and not sd.challan_amber("monthly", "2031-05", 40, False, datetime.date(2031, 6, 10), 15)
       and sd.challan_amber("monthly", "2031-05", 40, False, datetime.date(2031, 6, 11), 15) and not sd.challan_amber("sometimes", "2031-01", 400, False, TODAY, 15))
    t = html(own, "/desk/awaited")
    ck("C10 Bills awaited: one card per supplier with its modes; pharmacy challans not listed", lambda: "WALKA MONTHLY TRADERS" in t and "WALKB SOMETIMES STORES" in t
       and "WALKC OTHER AGENCIES" in t and "Z-2031-PH2" not in t and "Monthly bill" in t and "amber-row" in t)
    # the month page equals /papers/month for a month with no final challan; then a final challan adds exactly its amount
    cf1 = mk("CF1", F_, doc_kind="challan", challan_state="awaiting", subgroup="procedure", total_amount=250, bill_date="2031-06-06", items=[("Cotton roll", 5, 50)])

    def old_totals():
        t_ = html(own, "/papers/month?ym=2031-06")
        out = {}
        for g_, nm in (("procedure", "Procedure room"), ("xray", "X-ray films"), ("others", "Others")):
            mm = re.search(r'g=%s"[^>]*><b>%s</b>.*?<td class=r><b>([^<]+)</b>' % (g_, re.escape(nm)), t_, re.S)
            out[g_] = float(mm.group(1).replace("₹", "").replace(",", "")) if mm else None
        return out

    def new_totals():
        t_ = html(own, "/desk/month?ym=2031-06")
        return {g_: (float(mm.group(1)) if mm else None) for g_ in ("procedure", "xray", "others")
                for mm in [re.search(r'id="sec-%s".*?data-total="([0-9.]+)"' % g_, t_, re.S)]}
    o1, n1 = old_totals(), new_totals()
    ck("C11 The month: the three consumables groups equal /papers/month (no final challan this month)", lambda: o1 == n1 and o1["procedure"] is not None and o1["procedure"] > 0, lambda: (o1, n1))
    r_ = own.post("/desk/awaited/mode", data={"key": "walkf paid", "name": F_, "mode": "paid"})
    o2, n2 = old_totals(), new_totals()
    ck("C12 Paid on challan: its challan becomes the final paper (audited), accepted like a bill; it adds exactly its amount on The month",
       lambda: row(cf1)["challan_state"] == "final" and aud(cf1, "challan_final") and row(cf1)["status"] == "approved"
       and o2 == o1 and abs(n2["procedure"] - (o1["procedure"] + 250)) < 0.001 and n2["xray"] == o1["xray"] and n2["others"] == o1["others"], lambda: (o2, n2, row(cf1)["status"]))
    r_ = own.post("/desk/awaited/pay", data={"bid": cf1, "paid_on": "12-06-2031", "amount": "250"})
    ck("C13 Note payment on a paid-on-challan paper: paid_on, paid_amount (rupees), audited on the bill",
       lambda: r_.status_code == 302 and (row(cf1)["paid_on"], row(cf1)["paid_amount"]) == ("2031-06-12", 250.0) and aud(cf1, "paid"))

    # ------------------------------------------------------------------ L: the implant stock ledger
    Dd = "WALKD IMPLANT SURGICALS"
    cd0 = mk("CD0", Dd, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-03", created="2031-06-03 05:00:00", items=[("Cortical screw 4.5 mm", 12)])
    save(own, id=cd0, dest="implant_stock", kind="challan")
    bd1 = mk("BD1", Dd, bill_no="DI-1", total_amount=5000, bill_date="2031-06-08", items=[("Cortical screw 4.5 mm", 12, 400)])
    _c, jd = paper(own, bd1)
    code, j = save(own, id=bd1, dest="implant_stock", kind="bill", joins=[x["id"] for x in jd.get("covers", [])])
    own.post("/desk/implants/pay", data={"s": "walkd implant", "day": "10-06-2031", "amount": "2,000", "how": "Bank / UPI", "against": "DI-1"})
    own.post("/desk/implants/pay", data={"s": "walkd implant", "day": "11-06-2031", "amount": "300", "how": "Cash", "against": ""})
    try:
        pid = db.execute("SELECT id FROM implant_payment WHERE supplier_key='walkd implant' AND amount=300").fetchone()
    except sqlite3.Error:                                                  # the old files have no ledger (the control)
        pid = None
    if pid:
        own.post("/desk/implants/void", data={"s": "walkd implant", "id": pid[0]})
    cd2 = mk("CD2", Dd, doc_kind="challan", challan_state="awaiting", total_amount=700, bill_date="2031-06-12", created="2031-06-12 05:00:00", items=[("Interlocking screw", 2)])
    save(own, id=cd2, dest="implant_stock", kind="challan")
    own.post("/desk/awaited/mode", data={"key": "walkd implant", "name": Dd, "mode": "paid"})
    own.post("/desk/awaited/pay", data={"bid": cd2, "paid_on": "13-06-2031", "amount": "700"})
    pt1 = mk("PT1", Dd, bill_no="DI-P", total_amount=60000, bill_date="2031-06-09", items=[("Hip set", 1)])
    save(own, id=pt1, dest="patient_paper")
    own.post("/desk/implants/check", data={"s": "walkd implant"})
    L = (sd.ledger(db).get("walkd implant") if sd else None) or {}
    rows_ = {r__["p"]: r__ for r__ in L.get("rows", []) if r__["bid"]}
    ck("L1 the joined challan is shown with its items and owes nothing (its bill owes -- never twice)", lambda: code == 200 and "Z-2031-CD0" in rows_
       and rows_["Z-2031-CD0"]["o"] is None and "joined into Z-2031-BD1" in rows_["Z-2031-CD0"]["i"], lambda: (code, j, rows_.get("Z-2031-CD0")))
    ck("L2 owed = the bill + the final challan; paid = live payments + the final paper's paid_amount (a voided payment ignored); balance",
       lambda: (L["owed"], L["paid"], L["balance"]) == (5700.0, 2700.0, 3000.0), lambda: (L.get("owed"), L.get("paid"), L.get("balance")))
    ck("L3 a patient's paper never appears in the ledger", lambda: "Z-2031-PT1" not in rows_)
    t = html(own, "/desk/implants?s=walkd+implant")
    ck("L4 the ledger page: checked up to the made-up today; Owed / Paid / Balance shown; the void kept on record",
       lambda: "checked up to 15-Jun-2031" in t and "Payment (voided)" in t and "3,000" in t and "5,700" in t)

    # ------------------------------------------------------------------ F: the flags -- the D710 hold and the S441 set-aside, both ways
    o1_ = mk("O1", Cc, status="approved", bill_no="W-77", total_amount=4321, bill_date="2031-06-01", created="2031-06-01 05:00:00", approved_by="Walk")
    h1 = mk("H1", Cc, bill_no="W-77", total_amount=4321, bill_date="2031-06-01", created="2031-06-12 05:00:00")
    code, j = save(own, id=h1, dest="procedure", kind="bill")
    w = wlist(own)
    _c, jh = paper(own, h1)
    ck("F1 a second scan is held, shown, not silent: 'NOT accepted', listed with 'Looks like a second scan of Z-2031-O1'",
       lambda: code == 200 and "NOT accepted" in j.get("message", "") and row(h1)["status"] == "draft" and h1 in w and "hold" in w[h1]["why"]
       and jh.get("flags", {}).get("hold") == "Z-2031-O1", lambda: (code, j, w.get(h1), jh.get("flags")))
    code_x, _ = save(own, id=h1, dest="procedure")
    code, j = save(own, id=h1, flag="same")
    ck("F2 ...a Save without the answer is refused; 'It is the same -- set aside' = _mark_dup(desk)", lambda: code_x == 400 and code == 200
       and (row(h1)["status"], row(h1)["dup_of"], row(h1)["dup_flag"]) == ("rejected", o1_, "yes") and h1 not in wlist(own), lambda: (code_x, code, j))
    h2 = mk("H2", Cc, bill_no="W-77", total_amount=4321, bill_date="2031-06-01", created="2031-06-13 05:00:00")
    save(own, id=h2, dest="procedure", kind="bill")
    code, j = save(own, id=h2, flag="keep", dest="procedure", kind="bill")
    ck("F3 'Not the same -- keep': dup_flag 'no', 'not_duplicate', accepted by the person ('d710_accepted_by_person')",
       lambda: code == 200 and (row(h2)["status"], row(h2)["dup_flag"]) == ("approved", "no") and aud(h2, "not_duplicate") and aud(h2, "d710_accepted_by_person"), lambda: (code, j, row(h2)))
    s1 = mk("SA1", Cc, status="rejected", dup_of=o1_, dup_flag="yes", approved_by="server (S441 double-scan rule)", approved_at="2031-06-12 10:00:00", created="2031-06-12 05:00:00", reject_reason="duplicate of Z-2031-O1")
    s2 = mk("SA2", Cc, status="rejected", dup_of=o1_, dup_flag="yes", approved_by="server (S441 double-scan rule)", approved_at="2031-06-12 10:00:00", created="2031-06-12 06:00:00", reject_reason="duplicate of Z-2031-O1")
    s0 = mk("SA0", Cc, status="rejected", dup_of=o1_, dup_flag="yes", approved_by="server (S441 double-scan rule)", approved_at="2031-04-01 10:00:00", created="2031-06-02 06:00:00")
    w = wlist(own)
    ck("F4 an S441 set-aside of the last 30 days is listed (an older one is not)", lambda: s1 in w and s2 in w and "s441" in w[s1]["why"] and s0 not in w, lambda: (list(w)[:5]))
    code, j = save(own, id=s1, flag="same")
    code2, j2 = save(own, id=s2, flag="restore")
    w = wlist(own)
    ck("F5 'Same' = no change, 'desk_dup_same'; 'Not the same' = back to the lane's status, dup_of NULL, 'desk_dup_restored' with the old values",
       lambda: code == 200 and row(s1)["status"] == "rejected" and aud(s1, "desk_dup_same") and s1 not in w
       and code2 == 200 and (row(s2)["status"], row(s2)["dup_of"], row(s2)["dup_flag"]) == ("draft", None, "no")
       and json.loads(aud(s2, "desk_dup_restored")[-1]["detail"]).get("dup_of") == o1_ and s2 in w, lambda: (code, j, code2, j2))
    mr = mk("MR1", G, status="approved", subgroup="procedure", bill_no="G-M1", total_amount=1, bill_date="2029-01-05", created="2031-06-11 05:00:00", approved_by="Walk")
    mr0 = mk("MR0", G, status="approved", subgroup="procedure", bill_no="G-M0", total_amount=1, bill_date="2020-01-05", created="2031-05-20 05:00:00", approved_by="Walk")
    nr = mk("NR1", None, created="2031-06-12 05:00:00")
    w = wlist(own)
    _c, jm = paper(own, mr)
    _c, jn = paper(own, nr)
    ck("F6 a misread date is flagged and listed (scanned after the floor); before the floor it is not", lambda: mr in w and "date" in w[mr]["why"] and jm["flags"]["date"] and mr0 not in w)
    ck("F7 'Nothing could be read' is flagged", lambda: nr in w and "nothing" in w[nr]["why"] and jn["flags"]["nothing"])
    save(own, id=mr, dest="procedure", kind="bill")
    ck("F8 once saved on the desk, the flag is answered and it leaves the list", lambda: mr not in wlist(own))

    # ------------------------------------------------------------------ V: Personal hidden from the manager
    pv = mk("PV1", G, status="approved", subgroup="personal", bill_no="G-V1", bill_date="2029-02-02", created="2031-06-12 05:00:00", pdf=True, approved_by="Walk")
    wm, wo = wlist(mgr), wlist(own)
    ck("V1 Personal: never in a manager's list, file, reading, Open box or button; shown to the owner",
       lambda: pv not in wm and pv in wo and paper(mgr, pv)[0] == 403 and mgr.get("/bills/%d/file" % pv).status_code == 403
       and mgr.get("/desk/api/find?no=Z-2031-PV1").status_code == 403 and own.get("/desk/api/find?no=Z-2031-PV1").status_code == 200
       and paper(own, pv)[0] == 200 and save(mgr, id=pv, dest="misc")[0] == 403, lambda: (pv in wm, pv in wo))

    # ------------------------------------------------------------------ R: after the saves, a fresh import -- nothing a person placed moves
    pm = "WALKM MOVED-TO-PHARMACY"
    for i_ in range(2):
        h_ = mk("PMH%d" % i_, pm, status="approved", subgroup="procedure", bill_no="M-%d" % i_, total_amount=10 + i_, approved_by="Walk", ocr_status="read")
        db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (h_, "2031-06-10 10:00", "Walk Person", "subgroup", "{}")); db.commit()
    pma = mk("PMA", pm, bill_no="M-9", total_amount=19, ocr_status="read")
    save(own, id=pma, dest="pharmacy")
    cols = ("lane", "subgroup", "status", "kind", "pe_who", "doc_kind", "challan_state", "page_of", "dup_of")
    snap = {b_: tuple(row(b_)[k] for k in cols) for b_ in made.values()}
    db.close()
    rp = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--reimport", work], capture_output=True, text=True, timeout=300, env=dict(os.environ))
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    moved = [k for k, b_ in made.items() if tuple(dict(db.execute("SELECT * FROM bills WHERE id=?", (b_,)).fetchone())[c_] for c_ in cols) != snap[b_]]
    ck("R1 a fresh import (init, heal, auto_home) moves nothing a person placed", lambda: rp.returncode == 0 and "reimported" in rp.stdout and not moved,
       lambda: (rp.returncode, rp.stdout[-200:], rp.stderr[-300:], moved))
    rr = dict(db.execute("SELECT * FROM bills WHERE id=?", (ca4,)).fetchone())
    ck("R2 the grouped clinic challan stays a draft after the heal (it can still be joined)", lambda: (rr["status"], rr["challan_state"], rr["subgroup"]) == ("draft", "awaiting", "others"))
    ck("R3 the manager's Clinic-equipment Save still waits for the owner after the heal", lambda: dict(db.execute("SELECT status FROM bills WHERE id=?", (e2,)).fetchone())["status"] == "draft")
    ck("R4 the paper the desk handed to the pharmacy stays there (the system never sends it back)", lambda: dict(db.execute("SELECT lane FROM bills WHERE id=?", (pma,)).fetchone())["lane"] == "pharmacy")

    def row(bid):                                                          # noqa: F811 -- the re-opened connection
        return dict(db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone())

    # ------------------------------------------------------------------ M: The month -- kept apart, a patient's paper out of every total
    t = html(own, "/desk/month?ym=2031-06")
    secs = sd.month_data(db, "2031-06", True)[0] if sd else []
    money = {i_ for s_ in secs for i_ in s_["money_ids"]}
    npt = db.execute("SELECT COUNT(*) FROM bills b WHERE b.subgroup='patient_paper' AND b.status<>'rejected' AND b.dup_of IS NULL AND b.page_of IS NULL AND " + cp.MONTH_OF + "='2031-06'").fetchone()[0]
    ck("M1 a patient's paper is in no total and is counted under Kept apart", lambda: ap not in money and pt1 not in money and npt >= 2
       and re.search(r"<b id=patients>%d</b>" % npt, t), lambda: (npt, ap in money))
    ck("M2 Implant stock, Construction work and Clinic equipment are their own sections, out of the consumables",
       lambda: all(x in t for x in ('id="sec-implant_stock"', 'id="sec-construction"', 'id="sec-clinic_equipment"', "clinic / MK not decided")))
    ck("M3 a Clinic-equipment row offers '+ asset record' to the owner, not to the manager", lambda: "+ asset record" in t and "+ asset record" not in html(mgr, "/desk/month?ym=2031-06"))

    # ------------------------------------------------------------------ FIX1 (S551_FIX1): C2, C3, C4, N4, N5, N6
    def ids(lst):
        return {x["id"] for x in (lst or [])}
    # C2 -- a challan saved as A patient's paper: out of Bills awaited, the covers box, the waiting list and every count on The month
    E_ = "WALKE PATIENT CHALLANS"
    pch = mk("PCH", E_, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-07", created="2031-06-07 05:00:00", items=[("Locking plate", 1)])
    md0 = sd.month_data(db, "2031-06", True) if sd else None
    code_pc, j_pc = save(own, id=pch, dest="patient_paper", kind="challan")
    pcb = mk("PCB", E_, bill_no="PE-1", total_amount=100, bill_date="2031-06-14", created="2031-06-14 05:00:00", items=[("Locking plate", 1)])
    _c, jpc = paper(own, pcb)
    md2 = sd.month_data(db, "2031-06", True) if sd else None
    aw2 = {r__["id"] for c_ in sd.awaited(db, True, TODAY)[0] for r__ in c_["rows"]} if sd else set()
    w = wlist(own)
    ck("FC2 a challan saved as A patient's paper: not on Bills awaited, not in the covers box or the waiting list, out of The month's challan count; counted in Kept apart",
       lambda: code_pc == 200 and row(pch)["subgroup"] == "patient_paper" and row(pch)["challan_state"] == "awaiting" and pch not in aw2
       and pch not in ids(jpc.get("covers")) and md2[2] == md0[2] - 1 and md2[1]["patient"] == md0[1]["patient"] + 1
       and pch not in {i_ for s_ in md2[0] for i_ in s_["money_ids"]} and pch not in w and pcb in w and "covers" not in w[pcb]["why"]
       and "Z-2031-PCH" not in html(own, "/desk/awaited"),
       lambda: (code_pc, j_pc, pch in aw2, ids(jpc.get("covers")), md0 and md0[2], md2 and md2[2], w.get(pcb)))
    # C3 -- an ACCEPTED paper saved as Challan goes back to draft, awaiting, audited -- and is then joined by its bill
    J_ = "WALKJ REOPEN SUPPLIES"
    rc = mk("RC1", J_, status="approved", subgroup="others", bill_no="J-C1", bill_date="2031-06-03", created="2031-06-03 05:00:00",
            approved_by="Walk", approved_at="2031-06-03 10:00", items=[("Toner", 2)], pdf=True)
    code_r, j_r = save(own, id=rc, dest="others", kind="challan")
    rr3 = row(rc)
    ra3 = aud(rc, "desk_challan_reopened")
    rcb = mk("RCB", J_, bill_no="J-B1", total_amount=500, bill_date="2031-06-14", created="2031-06-14 05:00:00", items=[("Toner", 2)], pdf=True)
    _c, jr = paper(own, rcb)
    code_j, j_j = save(own, id=rcb, dest="others", kind="bill", joins=[rc])
    ck("FC3 an accepted clinic paper saved as Challan: back to draft, challan awaiting, 'desk_challan_reopened' with the old status; then joined by its bill",
       lambda: code_r == 200 and (rr3["status"], rr3["doc_kind"], rr3["challan_state"], rr3["subgroup"]) == ("draft", "challan", "awaiting", "others")
       and ra3 and json.loads(ra3[-1]["detail"]).get("status_from") == "approved" and ra3[-1]["who"] == own_u["display_name"]
       and rc in ids(jr.get("covers")) and code_j == 200 and row(rc)["page_of"] == rcb and row(rc)["challan_state"] == "joined",
       lambda: (code_r, j_r, rr3["status"], rr3["challan_state"], bool(ra3), ids(jr.get("covers")), code_j, j_j))
    # C4 -- a Personal challan never reaches a manager: not in his covers box, supplier note or waiting reasons; his join refused
    Q_ = "WALKQ PRIVATE STORES"
    qc = mk("QC1", Q_, subgroup="personal", doc_kind="challan", challan_state="awaiting", bill_date="2031-06-04", created="2031-06-04 05:00:00", items=[("Kettle", 1)])
    qb = mk("QB1", Q_, bill_no="Q-1", total_amount=90, bill_date="2031-06-14", created="2031-06-14 05:00:00", items=[("Kettle", 1)])
    _c, jqm = paper(mgr, qb)
    _c, jqo = paper(own, qb)
    wm = wlist(mgr)
    code_q, j_q = save(mgr, id=qb, dest="others", kind="bill", joins=[qc])
    ck("FC4 a Personal challan: never in a manager's covers box, supplier note, waiting reasons or Bills awaited; his join is refused server-side; the owner sees it",
       lambda: qc not in ids(jqm.get("covers")) and qc in ids(jqo.get("covers")) and "open challan" not in jqm.get("supplier_note", "")
       and qb in wm and "covers" not in wm[qb]["why"] and code_q == 400 and row(qc)["page_of"] is None and row(qc)["challan_state"] == "awaiting"
       and row(qb)["status"] == "draft" and "Z-2031-QC1" not in html(mgr, "/desk/awaited"),
       lambda: (ids(jqm.get("covers")), jqm.get("supplier_note"), wm.get(qb), code_q, j_q))
    # N5 -- a closed challan is never owed in the implant ledger
    N_ = "WALKN CLOSED IMPLANTS"
    mk("NC1", N_, subgroup="implant_stock", doc_kind="challan", challan_state="closed", total_amount=900, bill_date="2031-06-02", items=[("Bone screw", 4)])
    mk("NB1", N_, status="approved", subgroup="implant_stock", bill_no="N-1", total_amount=100, bill_date="2031-06-05", approved_by="Walk", items=[("Bone screw", 4, 25)])
    Ln = (sd.ledger(db).get("walkn closed") if sd else None) or {}
    ck("FN5 the implant ledger never counts a closed challan as owed", lambda: Ln["owed"] == 100.0 and Ln["balance"] == 100.0
       and any(r__["p"] == "Z-2031-NC1" and r__["o"] is None for r__ in Ln["rows"]), lambda: (Ln.get("owed"), [(r__["p"], r__["k"], r__["o"]) for r__ in Ln.get("rows", [])]))
    # N6 -- 'Rate before' only from the consumables groups / the row's own section: never Personal, a personal expense or a patient's paper
    ri = "Walk rate swab"
    mk("RT4", G, status="approved", subgroup="procedure", bill_no="RT-4", total_amount=50, bill_date="2031-04-05", created="2031-04-05 05:00:00", approved_by="Walk", items=[(ri, 1, 50)])
    mk("RT5P", G, status="approved", subgroup="personal", bill_no="RT-5P", total_amount=999, bill_date="2031-05-05", created="2031-05-05 05:00:00", approved_by="Walk", items=[(ri, 1, 999)])
    mk("RT5E", G, lane="owner_expense", bill_no="RT-5E", total_amount=777, bill_date="2031-05-06", created="2031-05-06 05:00:00", items=[(ri, 1, 777)])
    mk("RT5X", G, lane="other_doc", subgroup="patient_paper", bill_no="RT-5X", total_amount=888, bill_date="2031-05-07", created="2031-05-07 05:00:00", items=[(ri, 1, 888)])
    mk("RT6", G, status="approved", subgroup="procedure", bill_no="RT-6", total_amount=60, bill_date="2031-06-06", created="2031-06-06 05:00:00", approved_by="Walk", items=[(ri, 1, 60)])
    rowx = [r__ for s_ in (sd.month_data(db, "2031-06", True)[0] if sd else []) if s_["key"] == "procedure" for r__ in s_["rows"] if r__["n"] == ri]
    ck("FN6 'Rate before' on The month reads only the consumables groups (never Personal, a personal expense or a patient's paper)",
       lambda: rowx and rowx[0]["b"] == "%s (Apr)" % sd._inr(50), lambda: rowx)
    # N4 -- a locked database at mount is retried briefly and then ignored; unlocked, the tables are made
    lk = os.path.join(work, "lock_test.db")
    con = sqlite3.connect(lk)
    con.execute("CREATE TABLE bills(id INTEGER PRIMARY KEY)"); con.execute("CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)"); con.commit()
    con.execute("BEGIN EXCLUSIVE")
    try:
        r4, e4 = sd.ensure_at_mount(lk, tries=2, wait=0.05, timeout=0.1), None
    except Exception as e_:                                                # noqa: BLE001
        r4, e4 = None, e_
    con.rollback(); con.close()
    try:
        r4b = sd.ensure_at_mount(lk, tries=1, wait=0, timeout=1)
    except Exception as e_:                                                # noqa: BLE001
        r4b = repr(e_)
    con = sqlite3.connect(lk)
    n4 = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name IN ('challan_supplier','implant_payment','implant_check','desk_audit')").fetchone()[0]
    con.close()
    ck("FN4 at mount a 'database is locked' is retried briefly, then ignored (no error, the desk mounts); unlocked, the tables are made",
       lambda: r4 is False and e4 is None and r4b is True and n4 == 4, lambda: (r4, repr(e4), r4b, n4))

    # ------------------------------------------------------------------ E: the edit page, the month list, the re-read
    le = mk("LE1", G, lane="lab_purchase", bill_no="G-LE", total_amount=55, bill_date="2031-06-05")
    t = html(own, "/bills/%d/edit" % le)
    own.post("/bills/%d/edit" % le, data={"kind": "Consumable", "vendor": G, "bill_no": "G-LE", "bill_date": "2031-06-05", "total_amount": "55"})
    ck("E1 the edit page reads 'Edit bill' and keeps a Lab paper's kind", lambda: "Edit bill" in t and row(le)["kind"] == "Lab" and "New bill" in html(own, "/bills/new"))
    real = datetime.date.today()
    y_, m_ = real.year, real.month - 14
    while m_ < 1:
        y_, m_ = y_ - 1, m_ + 12
    back14 = "%04d-%02d" % (y_, m_)
    bm = mk("BM1", G, bill_no="G-BM", total_amount=5, bill_date=back14 + "-03")
    r_ = own.post("/bills/%d/month" % bm, data={"bill_month": back14})
    t = html(own, "/bills/%d" % bm)
    ck("E2 a paper's month can be set 14 months back; the intake still refuses that month; the page lists its own month",
       lambda: row(bm)["bill_month"] == back14 and m._good_bill_month(back14) is None and ('<option value="%s"' % back14) in t, lambda: (row(bm)["bill_month"], back14))

    class _Stub:
        def available(self):
            return True

        def extract(self, path, schema=None):
            return {"vendor": "WALK STUB"}, "done"
    m.SARVAM = _Stub()
    m._bg_extract = lambda *a, **k: None                                   # no reader thread: the 'reading' mark alone tells
    r_ = own.post("/bills/%d/reread" % ap)
    ck("E3 a patient's paper is never read again (the re-read is refused)", lambda: r_.status_code == 302 and (row(ap)["ocr_status"] or "") != "reading" and row(ap)["vendor"] == "WALKP PATIENT IMPLANTS",
       lambda: (row(ap)["ocr_status"], row(ap)["vendor"]))

    # ------------------------------------------------------------------ T: sizes and the first load
    t0 = time.time(); a_ = own.get("/desk"); t1 = time.time(); b_ = own.get("/desk/api/list"); t2 = time.time()
    first = ((b_.get_json(silent=True) or {}).get("papers") or [{}])[0].get("id")
    c_ = own.get("/desk/api/paper/%d" % first) if first else None
    t3 = time.time()
    load = (t3 - t0) * 1000
    print("SIZES desk %d B (%.0f ms) . list %d B (%.0f ms) . paper %d B (%.0f ms) . desk first load %.0f ms" % (
        len(a_.data), (t1 - t0) * 1000, len(b_.data), (t2 - t1) * 1000, len(c_.data) if c_ else 0, (t3 - t2) * 1000, load))
    for u in ("/desk/month", "/desk/awaited", "/desk/implants"):
        t0 = time.time(); r_ = own.get(u)
        print("SIZES %s %d B (%.0f ms)" % (u, len(r_.data), (time.time() - t0) * 1000))
    ck("T1 the desk's first load (page + list + one paper) is under 2 s; the page fits a laptop (no page scroll)",
       lambda: a_.status_code == 200 and load < 2000 and "html,body{height:100%;overflow:hidden}" in a_.get_data(as_text=True))

    # the made-up rows are only in the scratch copy, which is removed with the work folder
    ck("Z1 the made-up rows live in the scratch copy only", lambda: dbp.startswith(work) and m.DB_PATH == dbp)
    db.close()


def row_obj(db, bid):
    return db.execute("SELECT b.*, '' AS mo FROM bills b WHERE b.id=?", (bid,)).fetchone()


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--reimport":
        reimport_main(os.path.abspath(sys.argv[2]))
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
        # FIX1 N3: the control names the checks that MUST be red on the old files -- the desk route (W2 mounted, S3 the page),
        # the new sections in SUB (W3), the challan-not-accepted rule (C2, R2), the Personal guard (V1), the seeded list (H2)
        # and the fix round's C2, C3, C4, N5, N6 -- and fails if any of them is green (or was never reached).
        seen = {}
        for ok_, nm_ in zip(R, NAMES):
            seen[nm_] = ok_
        not_red = [k for k in MUST_RED if seen.get(k) is not False]
        print("CONTROL must-be-red: %s -- %s" % (", ".join(MUST_RED), ("all RED" if not not_red else "NOT red: " + ", ".join(
            k + ("(green)" if seen.get(k) else "(not reached)") for k in not_red))))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
