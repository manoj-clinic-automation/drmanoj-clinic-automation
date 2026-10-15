#!/usr/bin/env python3
"""walk_s563.py -- the S563_SCANAPP_TIDY walk. The app with the given files on a COPY of a database (SQLite's backup API), in
its own scratch folder; made-up rows only (suppliers WALKxx .., stamps Z-2031-R..; dated around a made-up today of 15-Jun-2031),
made-up logins (walk_own_2031 / walk_mgr_2031, made here); no reader thread, no paid call, nothing sent anywhere (a made-up key
and URL). Flask's test client; no port. Isolated as walk_s560.py (the files imported from the scratch folder, by path).

    python3 -B walk_s563.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js> <assets.db to copy> [--work DIR] [--shared DIR]
                            [--tidy-from DIR] [--save-pages DIR] [--expect-red] [--keep]

--tidy-from DIR: item 12's proof -- DIR holds clinic_papers.py with item 3 only (make_s563.py --cp-item3-only). fetch_s563.py
  is run twice, each in its own python3 process, on the same copy: the other four files the given (TO) files, clinic_papers.py
  swapped between DIR's and the given one; every clinic_papers route fetched as owner and as manager; the POST routes each on a
  fresh copy of the made-up database. The served bytes must be identical (check T1).
--save-pages DIR: the desk's page and its JSON answers for made-up papers (the browser walk measures the layout on them).
GREEN / RED per check; exit 1 on any RED. --expect-red (the control on the live S560 files): exit 0 only if every check named
in MUST_RED is RED. The work folder (default: a new folder under /tmp) is removed at the end unless --keep."""
import datetime, importlib.util, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, time

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "F1", "F2", "F3", "F4", "N1", "D1", "D2", "S1", "M1", "M2", "M3", "P1", "J1")
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js")
HERE = os.path.dirname(os.path.abspath(__file__))


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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:500]) if (d and not ok) else ""))
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
    shared_src = opt("--shared", os.environ.get("S563_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s563walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
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
    ck("W2 the S563 marks: sorting_desk TIDY, clinic_papers TIDY, asset_register TIDY_S563, asset_machine TIDY = S563 (S560 / S559 / "
       "S557 / S555 / S551 marks kept)",
       lambda: getattr(sd, "TIDY", None) == "S563" and getattr(cp, "TIDY", None) == "S563" and getattr(m, "TIDY_S563", None) == "S563"
       and getattr(am, "TIDY", None) == "S563" and sd.RECEIPTS == "S560" and cp.RECEIPTS == "S560" and m.RECEIPTS_S560 == "S560"
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
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
    db.commit()
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

    def post(cl, url, j):
        r = cl.post(url, json=j)
        return r.status_code, (r.get_json(silent=True) or {})

    def state(bid):
        with m.app.test_request_context("/"):
            return sd.paid_state(db, db.execute("SELECT b.*, " + cp.MONTH_OF + " AS mo FROM bills b WHERE b.id=?", (bid,)).fetchone())

    def desk_on(on):
        if on:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
        else:
            db.execute("DELETE FROM settings WHERE key='desk.on'")
        db.commit()

    def flashes(cl):
        with cl.session_transaction() as ss:
            f = list(ss.get("_flashes") or [])
            ss.pop("_flashes", None)
        return " | ".join(x[1] for x in f)

    loc = db.execute("SELECT id FROM locations ORDER BY id LIMIT 1").fetchone()[0]

    def mk_asset(name, bill_id=None, contract_type="None"):
        aid = db.execute("INSERT INTO assets(name, location_id, category, status, contract_type, kind, bill_id, created_at) "
                         "VALUES(?,?,?,'Active',?,'Asset',?,'2031-06-01 05:00:00')", (name, loc, "Other", contract_type, bill_id)).lastrowid
        db.commit()
        return aid

    # ------------------------------------------------------------------ F: item 1 (F-902) and item 2 (S560-N3)
    FA = "WALKFA ALPHA TRADERS"
    f_rej = mk("FA1", FA, status="rejected", reject_reason="not ours", approved_by="Walk Rejecter", approved_at="2031-06-09 10:00",
               subgroup="others", doc_kind="bill", bill_no="FA-1", total_amount=410, bill_date="2031-06-08")
    f_rej2 = mk("FA2", "WALKFE EPSILON TRADERS", status="rejected", reject_reason="not ours", created="2031-06-03 20:00:00",
                bill_no="FE-1", total_amount=120, bill_date="2031-06-02")
    f_head = mk("FB0", "WALKFB BETA TRADERS", status="approved", subgroup="others", doc_kind="bill", bill_no="FB-1", total_amount=999,
                bill_date="2031-06-04")
    f_page = mk("FB1", "WALKFB BETA TRADERS", status="rejected", page_of=f_head, reject_reason="joined into Z-2031-RFB0",
                approved_by="Walk", approved_at="2031-06-05 10:00")
    f_dup = mk("FB2", "WALKFB BETA TRADERS", status="rejected", dup_of=f_head, dup_flag="yes", reject_reason="second scan",
               approved_by="Walk", approved_at="2031-06-05 11:00", bill_no="FB-1", total_amount=999)
    FD = "WALKFD DELTA SUPPLIES"
    f_blank = mk("FD1", FD, status="rejected", reject_reason="blank — discarded on the sorting desk", approved_by="Walk",
                 approved_at="2031-06-07 09:00", reading={"doc_kind": "tax_invoice", "vendor": FD, "bill_no": "FD-9", "total_amount": 640,
                                                          "items": [{"name": "Transport", "amount": 640}]})
    pj = {x: paper(own, x)[1] for x in (f_rej, f_rej2, f_page, f_dup, f_blank)}
    dh = html(own, "/desk?open=%d" % f_rej)
    ck("F1 (item 1) a set-aside paper shows ONE line 'Already set aside on dd-mm-yyyy — Restore?' (the day from approved_at; with "
       "none, the scan day in IST) and a Restore button; never on a joined page or an S441 double scan; a blank set-aside that "
       "Claude read keeps its one blank-fix line (no second Restore)",
       lambda: (pj[f_rej].get("aside") or {}).get("text") == "Already set aside on 09-06-2031 — Restore?"
       and (pj[f_rej2].get("aside") or {}).get("text") == "Already set aside on 04-06-2031 — Restore?"
       and pj[f_page].get("aside", "x") is None and pj[f_dup].get("aside", "x") is None
       and (pj[f_blank].get("fix") or {}).get("key") == "blank" and pj[f_blank].get("aside", "x") is None
       and "data-restore=1>Restore</button>" in dh and '"restore": "/desk/api/restore"' in dh and "if(j.aside&&j.status=='set aside')" in dh,
       lambda: ({k: (v.get("aside"), (v.get("fix") or {}).get("key")) for k, v in pj.items()}, '"restore":' in dh))

    db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
               (f_rej, "2031-06-10 11:00", "Walk", "desk_fix_answered", json.dumps({"answer": "saved", "via": "desk"})))
    db.commit()
    nfa0 = len(aud(f_rej, "desk_fix_answered"))
    before = dict(row(f_rej))
    c_r, j_r = post(own, "/desk/api/restore", {"id": f_rej})
    after = dict(row(f_rej)) if row(f_rej) else {}
    ra = aud(f_rej, "desk_restored")
    rad = json.loads(ra[-1]["detail"]) if ra else {}
    c_s0, j_s0 = save(own, id=f_rej2, dest="others", kind="bill")
    c_s, j_s = save(own, id=f_rej, dest="others", kind="bill")
    f_oe = mk("FO1", "WALKFO OMICRON STORES", lane="owner_expense", status="rejected", reject_reason="not ours", pe_who="bhawna",
              approved_at="2031-06-06 10:00", total_amount=70)
    c_oe, _j = post(own, "/desk/api/restore", {"id": f_oe})
    ck("F2 (items 1, 2) Restore: back to the status a fresh paper on its lane has (clinic draft; Personal expense captured), lane, "
       "section, kind, doc kind and Dr MK / Dr Bhawna kept; the reason, approved_by and approved_at cleared; audited (who, when, "
       "from what); no desk_fix_answered read or written (it works though one exists); then an ordinary paper -- the normal Save "
       "accepts it; a Save on a paper still set aside says 'Press Restore'",
       lambda: c_r == 200 and after.get("status") == "draft" and after.get("reject_reason") is None and after.get("approved_by") is None
       and after.get("approved_at") is None and all(after.get(k) == before[k] for k in ("lane", "subgroup", "kind", "doc_kind", "pe_who", "challan_state"))
       and rad.get("status_from") == "rejected" and rad.get("by") == "Walk Owner" and rad.get("at") and rad.get("reject_reason") == "not ours"
       and rad.get("approved_by") == "Walk Rejecter" and len(aud(f_rej, "desk_fix_answered")) == nfa0
       and c_s == 200 and row(f_rej)["status"] == "approved"
       and c_s0 == 400 and "Press Restore" in (j_s0.get("error") or "")
       and c_oe == 200 and row(f_oe)["status"] == "captured" and row(f_oe)["lane"] == "owner_expense" and row(f_oe)["pe_who"] == "bhawna",
       lambda: (c_r, j_r, {k: after.get(k) for k in ("status", "reject_reason", "approved_by", "approved_at")}, rad, c_s, j_s, c_s0, j_s0, c_oe))

    f_pers = mk("FP1", "WALKFP PI PERSONAL", status="rejected", subgroup="personal", reject_reason="not ours", approved_at="2031-06-06 10:00")
    f_ph = mk("FH1", "WALKFH PHI PHARMA", lane="pharmacy", status="rejected", reject_reason="not ours")
    desk_on(True)
    c_mp, _j = post(mgr, "/desk/api/restore", {"id": f_pers})
    c_mpj, _j2 = paper(mgr, f_pers)
    desk_on(False)
    st_after_mgr = row(f_pers)["status"]
    c_pg, j_pg = post(own, "/desk/api/restore", {"id": f_page})
    c_dp, j_dp = post(own, "/desk/api/restore", {"id": f_dup})
    c_ph, _j3 = post(own, "/desk/api/restore", {"id": f_ph})
    c_op, _j4 = post(own, "/desk/api/restore", {"id": f_pers})
    ck("F3 (item 1) the server checks: a manager's Restore of a Personal paper is refused (403; it stays hidden from him as today); a "
       "joined page and a double scan are refused (400, unchanged); a pharmacy paper is never restored from the desk; the owner "
       "restores his Personal paper",
       lambda: c_mp == 403 and c_mpj == 403 and st_after_mgr == "rejected" and c_pg == 400 and row(f_page)["status"] == "rejected"
       and row(f_page)["page_of"] == f_head and c_dp == 400 and row(f_dup)["status"] == "rejected" and c_ph in (400, 403)
       and row(f_ph)["status"] == "rejected" and c_op == 200 and row(f_pers)["status"] == "draft",
       lambda: (c_mp, c_mpj, st_after_mgr, c_pg, j_pg, c_dp, j_dp, c_ph, c_op))

    FN = "WALKFN NU MEDICALS"
    mk("FN0", FN, status="approved", subgroup="others", doc_kind="bill", bill_no="FN-7", total_amount=555, bill_date="2031-06-03")
    f_bl2 = mk("FN1", FN, status="rejected", reject_reason="blank — discarded on the sorting desk", approved_by="Walk Blank",
               approved_at="2031-06-08 09:00", bill_no="FN-7", total_amount=555, bill_date="2031-06-03",
               reading={"doc_kind": "tax_invoice", "vendor": FN, "bill_no": "FN-7", "total_amount": 555, "items": [{"name": "Cotton", "amount": 555}]})
    db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (f_bl2, "2031-06-08 09:00", "Walk", "desk_blank",
                                                                                            json.dumps({"status_from": "approved", "lane": "clinic", "via": "desk"})))
    db.commit()
    c_fx, j_fx = post(own, "/desk/api/fix", {"id": f_bl2, "answer": "restore"})
    r_fx = dict(row(f_bl2))
    c_fs, j_fs = save(own, id=f_bl2, dest="others", kind="bill")
    ck("F4 (item 2, S560-N3) the blank fix's Restore never returns a paper straight to accepted, though it was accepted when set "
       "aside: draft, approved_by and approved_at cleared (one shared restore); the next Save runs the normal accept and its "
       "same-vendor-number-amount check holds it -- never two accepted copies",
       lambda: c_fx == 200 and r_fx["status"] == "draft" and r_fx["approved_by"] is None and r_fx["approved_at"] is None
       and aud(f_bl2, "desk_blank_restored") and row(f_bl2)["status"] != "approved",
       lambda: (c_fx, j_fx, {k: r_fx[k] for k in ("status", "approved_by", "approved_at")}, c_fs, j_fs, row(f_bl2)["status"]))

    # ------------------------------------------------------------------ N: item 3 (NEW1) -- the old Bills awaited page
    CN = "WALKCN GAMMA SURGICALS"
    n_ok = mk("CN1", CN, doc_kind="challan", challan_state="awaiting", subgroup="procedure", total_amount=100, bill_date="2031-06-02")
    n_pers = mk("CN2", CN, doc_kind="challan", challan_state="awaiting", subgroup="personal", total_amount=100, bill_date="2031-06-02")
    n_pat = mk("CN3", CN, doc_kind="challan", challan_state="awaiting", subgroup="patient_paper", total_amount=100, bill_date="2031-06-02")
    n_ph = mk("CN4", "WALKCP GAMMA PHARMA", lane="pharmacy", doc_kind="challan", challan_state="awaiting", total_amount=100, bill_date="2031-06-02")
    n_cl = mk("CN5", CN, doc_kind="challan", challan_state="closed", subgroup="personal", total_amount=100, bill_date="2031-05-02")
    n_bp = mk("CN6", CN, status="approved", subgroup="personal", doc_kind="bill", bill_no="CN-P", total_amount=100, bill_date="2031-06-05")
    n_bo = mk("CN7", CN, status="approved", subgroup="others", doc_kind="bill", bill_no="CN-O", total_amount=100, bill_date="2031-06-05")
    n_bat = mk("CN8", CN, status="draft", doc_kind="bill", bill_no="CN-B", total_amount=100, bill_date="2031-06-06")
    hm, ho = html(mgr, "/papers/challans"), html(own, "/papers/challans")
    cm, co = html(mgr, "/papers/%d" % n_bat), html(own, "/papers/%d" % n_bat)

    def has(h, bid):
        return row(bid)["stamp_no"] in h
    with m.app.test_request_context("/"):
        aw_m = quiet(lambda: {r_["id"] for r_ in cp.challans_awaiting(db, owner=False)}, set())
        aw_o = quiet(lambda: {r_["id"] for r_ in cp.challans_awaiting(db, owner=True)}, set())
    ck("N1 (item 3, NEW1) the old Bills awaited page and the bill page's 'The bill for a challan?': never a patient's challan, for "
       "anyone; a Personal challan (and a Personal bill among the candidates, and a closed Personal challan) for the owner only; a "
       "pharmacy challan still listed; the desk's helper not called (filtered in place)",
       lambda: has(hm, n_ok) and has(hm, n_ph) and not has(hm, n_pers) and not has(hm, n_pat) and not has(hm, n_bp) and has(hm, n_bo)
       and "Z-2031-RCN5" not in hm and "Z-2031-RCN5" in ho
       and has(ho, n_ok) and has(ho, n_pers) and not has(ho, n_pat) and has(ho, n_bp)
       and "Z-2031-RCN1" in cm and "Z-2031-RCN3" not in cm and "Z-2031-RCN2" not in cm and "Z-2031-RCN2" in co and "Z-2031-RCN3" not in co
       and {n_ok, n_ph} <= aw_m and not ({n_pers, n_pat} & aw_m) and n_pers in aw_o and n_pat not in aw_o
       and "sorting_desk" not in open(cp.__file__, encoding="utf-8").read().split("def challans_awaiting", 1)[1].split("\ndef ", 1)[0],
       lambda: ({x: (has(hm, x), has(ho, x)) for x in (n_ok, n_pers, n_pat, n_ph, n_bp, n_bo)}, "Z-2031-RCN3" in cm, "Z-2031-RCN2" in cm,
                sorted(aw_m & {n_ok, n_pers, n_pat, n_ph})))

    # ------------------------------------------------------------------ D: item 4 (NEW2 + S557-K2-N2) -- the owner's Delete
    DL = "WALKDL DELTA MEDICAL"
    d_bill = mk("DL1", DL, status="approved", subgroup="others", doc_kind="bill", bill_no="DL-1", total_amount=500, bill_date="2031-06-02")
    d_rc = mk("DL2", DL, bill_no="DL-R", total_amount=500, bill_date="2031-06-05")
    c_d0, j_d0 = save(own, id=d_rc, dest="others", kind="receipt", receipt={"pays": str(d_bill), "paid_on": "05-06-2031", "amount": "500", "mode": "cash"})
    paid0 = state(d_bill)["state"]
    d_as = mk_asset("WALK DL MACHINE", bill_id=d_rc)
    pay = db.execute("SELECT * FROM paper_payment WHERE proof_bill_id=? ORDER BY id DESC LIMIT 1", (d_rc,)).fetchone()
    r_del = own.post("/bills/%d/delete" % d_rc, data={})
    fl_del = flashes(own)
    pay2 = db.execute("SELECT * FROM paper_payment WHERE id=?", (pay["id"],)).fetchone() if pay else None
    live_al = db.execute("SELECT COUNT(*) FROM paper_payment_bill WHERE payment_id=? AND voided_at=''", (pay["id"],)).fetchone()[0] if pay else -1
    pd_ = aud(d_rc, "paper_deleted")
    ck("D1 (item 4) the owner's Delete of a receipt: in one go its payment voided (kept on record) and its allocation voided, so the "
       "bill it paid reads unpaid again; the machine that pointed at it no longer does (assets.bill_id NULL); one 'paper_deleted' "
       "audit row; the paper gone",
       lambda: c_d0 == 200 and paid0 == "paid" and r_del.status_code in (302, 303) and row(d_rc) is None and pay2 is not None
       and pay2["voided_at"] != "" and live_al == 0 and state(d_bill)["state"] == "unpaid"
       and db.execute("SELECT bill_id FROM assets WHERE id=?", (d_as,)).fetchone()[0] is None
       and len(pd_) == 1 and json.loads(pd_[0]["detail"]).get("payments_voided") == [pay["id"]],
       lambda: (c_d0, j_d0, paid0, r_del.status_code, row(d_rc) is None, pay2 and pay2["voided_at"], live_al, state(d_bill)["state"], len(pd_), fl_del))
    d_x = mk("DL3", "WALKDX XI PAPERS", bill_no="DX-1", total_amount=20)
    npd0 = db.execute("SELECT COUNT(*) FROM bill_audit WHERE action='paper_deleted'").fetchone()[0]   # by count: SQLite may re-use the deleted id
    sdm = sys.modules.pop("sorting_desk")
    try:
        r_dx = own.post("/bills/%d/delete" % d_x, data={})
        fl_dx = flashes(own)
    finally:
        sys.modules["sorting_desk"] = sdm
    ck("D2 (item 4) with the desk module not loaded the Delete is refused with one plain line and nothing is changed",
       lambda: r_dx.status_code in (302, 303) and row(d_x) is not None and row(d_x)["stamp_no"] == "Z-2031-RDL3" and "not deleted" in fl_dx
       and db.execute("SELECT COUNT(*) FROM bill_audit WHERE action='paper_deleted'").fetchone()[0] == npd0,
       lambda: (r_dx.status_code, row(d_x) is not None, fl_dx))

    # ------------------------------------------------------------------ S: item 5 (S560-N4) -- a statement's order
    SG = "WALKSG SIGMA TRADERS"
    s_a = mk("SG1", SG, status="approved", subgroup="others", doc_kind="bill", bill_no="SG-1", bill_date="2031-05-03")
    s_b = mk("SG2", SG, status="approved", subgroup="others", doc_kind="bill", bill_no="SG-2", total_amount=300, bill_date="2031-05-10")
    s_c = mk("SG3", SG, status="approved", subgroup="others", doc_kind="bill", bill_no="SG-3", total_amount=200, bill_date="2031-05-20")
    s_st = mk("SG4", SG, total_amount=400, bill_date="2031-05-31")
    c_st, j_st = save(own, id=s_st, dest="", kind="statement", statement={"from": "01-05-2031", "to": "31-05-2031", "total": "400",
                                                                          "paid_on": "01-06-2031", "amount": "400", "mode": "cheque",
                                                                          "ref": "1", "covers": [s_a, s_b, s_c]})
    sp = db.execute("SELECT id FROM paper_payment WHERE proof_bill_id=? AND voided_at='' ORDER BY id DESC LIMIT 1", (s_st,)).fetchone()
    al = {r_[0]: r_[1] for r_ in db.execute("SELECT bill_id, amount FROM paper_payment_bill WHERE payment_id=? AND voided_at=''", (sp[0] if sp else -1,))}
    ck("S1 (item 5) a statement pays the invoices that have a total first, oldest first (Rs300 then Rs100 of Rs200); the older invoice "
       "with no total takes only what is left (here nothing) -- and the Save's message says so",
       lambda: c_st == 200 and al.get(s_b) == 300 and al.get(s_c) == 100 and s_a not in al and "has no total" in (j_st.get("message") or ""),
       lambda: (c_st, j_st.get("message") or j_st, al))

    # ------------------------------------------------------------------ M: items 6, 7, 8 -- asset_machine (and asset_register's PM sentence)
    m_p = mk("MP1", "WALKMP MU EQUIPMENT", status="approved", subgroup="clinic_equipment", doc_kind="bill", bill_no="MP-1",
             total_amount=45000, bill_date="2031-06-01")
    orig_pf = am.prefill

    def other_tap(db_, b_):                                                # the other worker's POST lands between the check and the INSERT
        if b_["id"] == m_p:
            c2 = sqlite3.connect(dbp, timeout=20)
            c2.execute("INSERT INTO assets(name, location_id, category, status, contract_type, kind, bill_id) VALUES(?,?,?,'Active','None','Asset',?)",
                       ("WALK FIRST TAP", loc, "Other", m_p))
            c2.commit(); c2.close()
        return orig_pf(db_, b_)
    am.prefill = other_tap
    try:
        r_mp = own.post("/bills/%d/machine" % m_p, data={"name": "WALK SECOND TAP", "category": "Other", "purchase_date": "01-06-2031", "price": "45000"})
    finally:
        am.prefill = orig_pf
    n_m = db.execute("SELECT COUNT(*) FROM assets WHERE bill_id=?", (m_p,)).fetchone()[0]
    ck("M1 (item 6) 'already a machine's purchase bill' checked again inside the POST under the write lock: a second tap that lands "
       "after the first made its machine gets that machine -- one machine per paper, never two",
       lambda: r_mp.status_code in (302, 303) and n_m == 1 and "/assets/" in (r_mp.headers.get("Location") or ""),
       lambda: (r_mp.status_code, r_mp.headers.get("Location"), n_m))
    ref = {}
    with m.app.test_request_context("/"):
        for tag, x in (("dup", "Z-2031-RFB2"), ("page", "Z-2031-RFB1"), ("ok", "Z-2031-RFB0")):
            try:
                ref[tag] = ("id", am.paper_from_box(db, x, True))
            except am.Refused as e:
                ref[tag] = ("refused", str(e))
    ck("M2 (item 7) the stamp box refuses a copy and a page: 'This paper is a copy / a page of B-xxxx — open B-xxxx instead.'; the "
       "real paper is taken; refusal() itself unchanged (its three displays)",
       lambda: ref["dup"] == ("refused", "This paper is a copy of Z-2031-RFB0 — open Z-2031-RFB0 instead. Nothing was saved.")
       and ref["page"] == ("refused", "This paper is a page of Z-2031-RFB0 — open Z-2031-RFB0 instead. Nothing was saved.")
       and ref["ok"] == ("id", f_head) and "dup_of" not in open(am.__file__, encoding="utf-8").read().split("def refusal", 1)[1].split("\ndef ", 1)[0],
       lambda: ref)
    a_old = mk_asset("WALK OLD AMC LAPSED", contract_type="AMC")
    a_new = mk_asset("WALK OLD AMC RUNNING", contract_type="AMC")
    a_non = mk_asset("WALK OLD AMC NO DATE", contract_type="AMC")
    for aid_, d_ in ((a_old, "2030-05-01"), (a_old, "2031-05-01"), (a_new, "2031-12-01")):
        db.execute("INSERT INTO expiries(entity, entity_id, label, due_date) VALUES('asset',?,'Contract renewal',?)", (aid_, d_))
    db.commit()
    arow = {x: db.execute("SELECT * FROM assets WHERE id=?", (x,)).fetchone() for x in (a_old, a_new, a_non)}
    with m.app.test_request_context("/"):
        cl_ = {x: am.cover_line(db, arow[x]) for x in arow}
        pm_ = {x: m._s559_pm(arow[x]) for x in arow}
    ck("M3 (item 8) with no S557 cover row, an old record whose own Contract renewal date (the latest such row) is past reads "
       "'... lapsed on dd-mm-yyyy' in red and the PM sentence is not shown; a future date or none: as today",
       lambda: cl_[a_old] == ("Covered (old record): AMC — lapsed on 01-05-2031", "red") and pm_[a_old] is False
       and cl_[a_new] == ("Covered (old record): AMC", "") and pm_[a_new] is True and cl_[a_non] == ("Covered (old record): AMC", "") and pm_[a_non] is True,
       lambda: (cl_, pm_))

    # ------------------------------------------------------------------ P: item 9 (S560-N2) -- the words, never item names
    p_st = mk("PS1", "WALKPS PI STATIONERS", items=[("Receipt book", 1, 50, 50), ("A4 paper", 1, 250, 250)], bill_no="PS-1", total_amount=300,
              reading={"doc_kind": "tax_invoice", "vendor": "WALKPS PI STATIONERS", "bill_no": "PS-1", "total_amount": 300,
                       "items": [{"name": "Receipt book", "amount": 50}, {"name": "A4 paper", "amount": 250}]})
    p_lg = mk("PS2", "WALKPL LAMBDA STATIONERS", items=[("Ledger register", 1, 90, 90)], bill_no="PL-1", total_amount=90,
              reading={"doc_kind": "tax_invoice", "vendor": "WALKPL LAMBDA STATIONERS", "bill_no": "PL-1", "total_amount": 90,
                       "items": [{"name": "Ledger register", "amount": 90}]})
    p_rc = mk("PS3", "WALKPR RHO AGENCIES", reading={"doc_kind": "other", "vendor": "WALKPR RHO AGENCIES", "bill_no": "MONEY RECEIPT 45",
                                                       "total_amount": 90, "items": []})
    pk = {x: paper(own, x)[1] for x in (p_st, p_lg, p_rc)}
    with m.app.test_request_context("/"):
        fxk = {b_["id"]: k_ for b_, k_, _t in sd.fixes(db, True, TODAY) if b_["id"] in (p_st, p_lg)}
    ck("P1 (item 9) a 'Receipt book' or 'Ledger register' line on a stationery bill leaves its Bill pre-choice alone and is not listed "
       "'This looks like a receipt / statement'; the words still count on Claude's supplier / number ('MONEY RECEIPT 45' -> Receipt)",
       lambda: (pk[p_st].get("kind"), pk[p_st].get("kind_from")) == ("bill", "Claude's reading") and pk[p_lg].get("kind") == "bill"
       and not fxk and (pk[p_rc].get("kind"), pk[p_rc].get("kind_from")) == ("receipt", "Claude's reading"),
       lambda: ({x: (v.get("kind"), v.get("kind_from")) for x, v in pk.items()}, fxk))

    # ------------------------------------------------------------------ J: item 10 -- the widget's bytes (its behaviour: the browser walk)
    wj = open(os.path.join(appdir, "scanner_widget.js"), encoding="utf-8").read()
    ck("J1 (item 10) scanner_widget.js: dropSrc (called only inside the intake's cvScanOn branch) bumps the Adjust generation "
       "(adjGenS559++) and, after a shift, names the page now adjusted on the stage button; nothing else in the file differs "
       "(proven in the headless-Chrome walk)",
       lambda: "function dropSrc(i){ pageSrc.splice(i, 1); pageCorners.splice(i, 1); adjGenS559++;" in wj
       and 'else if (adjustIdx > i) { adjustIdx--; $("addpage").textContent = "\\u2714 Theek hai \\u2014 page " + (adjustIdx + 1); }' in wj
       and wj.count("dropSrc(") == 2 and 'window.__scannerS559 = {version: "S559.1"}' in wj)

    # ------------------------------------------------------------------ T: item 12 -- the tidy changes no served byte
    tf = opt("--tidy-from")
    if tf:
        db.close()
        outs = []
        for i, cpdir in enumerate((os.path.abspath(tf), D)):
            fd = os.path.join(work, "fetch%d" % i)
            os.makedirs(fd, exist_ok=True)
            for f in MODS:
                src_ = os.path.join(cpdir if f == "clinic_papers.py" else D, f)
                if os.path.exists(src_):
                    shutil.copy(src_, os.path.join(fd, f))
            outp = os.path.join(work, "fetch%d.json" % i)
            pr = subprocess.run([sys.executable, "-B", os.path.join(HERE, "fetch_s563.py"), fd, SRC, outp, "--shared", shared_src or "",
                                 "--work", os.path.join(work, "fw%d" % i)], capture_output=True, text=True, timeout=900)
            if pr.returncode != 0:
                print("  (fetch %d failed: %s)" % (i, (pr.stdout + pr.stderr)[-600:]))
            outs.append(json.load(open(outp)) if os.path.exists(outp) else {})
        a_, b_ = outs
        diff = sorted(k for k in set(a_) | set(b_) if a_.get(k) != b_.get(k))
        print("TIDY fetched %d answers with item-3-only clinic_papers.py, %d with the TO file (owner and manager; GET bodies, "
              "POST status / Location / flash / rows); differing: %s" % (len(a_), len(b_), diff[:8] or "none"))
        ck("T1 (item 12) the tidy changes no served byte: with the other four files at TO, clinic_papers.py item-3-only and TO each fetch "
           "every clinic_papers route as owner and as manager on the same made-up rows, the same day -- every GET body, every POST's "
           "status, Location, flash and changed rows identical (each POST on a fresh copy)",
           lambda: a_ and b_ and len(a_) >= 40 and not diff, lambda: diff[:10])
        db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row

    # ------------------------------------------------------------------ the pages for the browser walk (made-up rows only)
    if opt("--save-pages"):
        out = opt("--save-pages")
        os.makedirs(out, exist_ok=True)
        RA = "WALKRA ALPHA MEDICARE"
        mk("LYA", RA, status="approved", subgroup="others", doc_kind="bill", bill_no="RA-3773", total_amount=300, bill_date="2031-06-01")
        lay = mk("LY1", "WALKLY LAYOUT SUPPLIES", bill_no="LY-1", total_amount=1234, bill_date="2031-06-12", items=[("WALK GAUZE", 2, 10, 20)])
        lrc = mk("LY2", RA, bill_no="LY-R", total_amount=300, bill_date="2031-06-13",
                 reading={"doc_kind": "other", "vendor": RA, "total_amount": 300, "bill_date": "2031-06-13", "items": []})
        S2 = "WALKSZ ZETA SYSTEMS"
        for t_, amt_, d_ in (("Z1", 300, "2031-05-05"), ("Z2", 400, "2031-05-12"), ("Z3", 500, "2031-05-20")):
            mk(t_, S2, lane="owner_expense", bill_no="SZ-" + t_, total_amount=amt_, bill_date=d_)
        lst = mk("LY3", S2, total_amount=1300, bill_date="2031-05-31")
        lasd = mk("LY4", "WALKLA LAYOUT ASIDE", status="rejected", reject_reason="not ours", approved_at="2031-06-11 10:00",
                  bill_no="LA-1", total_amount=210, bill_date="2031-06-11")
        lj = json.loads(own.get("/desk/api/list").get_data(as_text=True))   # only the made-up papers leave the box (no live row)
        lj["papers"] = [p_ for p_ in (lj.get("papers") or []) if str(p_.get("stamp") or "").startswith("Z-2031-")]
        pages = {"desk.html": html(own, "/desk?open=%d" % lay), "list.json": json.dumps(lj)}
        for x in (lay, lrc, lst, lasd):
            pages["paper_%d.json" % x] = own.get("/desk/api/paper/%d" % x).get_data(as_text=True)
        for k, v in pages.items():
            with open(os.path.join(out, k), "w", encoding="utf-8") as fh:
                fh.write(v)
        with open(os.path.join(out, "ids.json"), "w") as fh:
            json.dump({"bill": lay, "receipt": lrc, "statement": lst, "aside": lasd}, fh)
        print("SAVED the desk's page and %d answers for the browser walk (made-up rows only)" % (len(pages) - 1))

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
    if "--expect-red" in ARGS:
        seen_ = {}
        for ok_, nm_ in zip(R, NAMES):
            seen_[nm_] = ok_
        not_red = [k for k in MUST_RED if seen_.get(k) is not False]
        print("CONTROL must-be-red: %s -- %s" % (", ".join(MUST_RED), ("all RED" if not not_red else "NOT red: " + ", ".join(
            k + ("(green)" if seen_.get(k) else "(not reached)") for k in not_red))))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
