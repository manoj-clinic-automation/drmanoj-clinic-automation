#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s568.py -- the S568_STATIONERY_STOCK walk. The app with the given files on a COPY of a database (SQLite's backup API),
in its own scratch folder; made-up rows only (suppliers WALK568 .., stamps Z-2031-T.., items 'Walk ..'; dated around a made-up
today of 15-Jun-2031, injected), made-up logins (walk_own_2031 / walk_mgr_2031, made here; a reception user stood in for by
the walk); no reader thread, no paid call, nothing sent anywhere (a made-up key and URL). Flask's test client; no port.
Sanjeevni's four readers and the parent's packs.py are READ from the finance folder, never edited, never run against a live
database: their queries run on the scratch copy; packs.py runs on a made-up database.

    python3 -B walk_s568.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js [, stationery.py] [, packs.py]> <assets.db to copy>
                            [--work DIR] [--shared DIR] [--fin DIR] [--no-pack] [--expect-red] [--keep]

One named check per item 1-8 (I1..I8), and W1, W2, Z1; GREEN / RED; exit 1 on any RED. --expect-red (the control, on the live
FROM files -- no stationery.py, the live packs.py): exit 0 only if every check named in MUST_RED is RED. Counts are printed
(never a live row's content). packs.py: the one in <dir> when there, else <fin>/packs.py; 'before' = <fin>/packs.py."""
import datetime, html as htmlmod, importlib.util, io, json, os, re, shutil, sqlite3, sys, tempfile, time

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8")
TODAY = datetime.date(2031, 6, 15)
YM = "2031-06"
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js", "stationery.py")
SANJ = (("scan_register.py", 1), ("purchase_app.py", 2), ("porders.py", 1), ("order_sheet.py", 1))      # the least each must hold


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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:700]) if (d and not ok) else ""))
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


_PDF_N = [0]


def made_up_pdf(text):
    """A one-page PDF with a made-up line of text and a block placed differently on each call (each a different picture)."""
    _PDF_N[0] += 1
    k = _PDF_N[0]
    body = "0 0 0 rg %d %d %d %d re f BT /F1 18 Tf 72 740 Td (%s) Tj ET" % (40 + 60 * (k % 8), 60 + 80 * (k % 7), 120 + 30 * (k % 3), 160 + 40 * (k % 4), text)
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            "<< /Length %d >>\nstream\n%s\nendstream" % (len(body), body), "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += "%d 0 obj\n%s\nendobj\n" % (i, o)
    x = len(out)
    out += "xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + "".join("%010d 00000 n \n" % o for o in offs)
    out += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    return out.encode("latin-1")


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S568_SHARED_DIR", "/root/shared"))
    fin = os.path.abspath(opt("--fin", os.environ.get("S568_FIN_DIR", "/root/finance")))
    work = opt("--work") or tempfile.mkdtemp(prefix="s568walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
    work = os.path.abspath(work)
    try:
        run(D, SRC, shared_src, fin, work)
    finally:
        if "--keep" not in ARGS:
            shutil.rmtree(work, ignore_errors=True)


def run(D, SRC, shared_src, fin, work):
    for sub in ("app", "uploads", "key", "no_portal", "shared", "fin"):
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
    st = sys.modules.get("stationery")
    ck("W1 the app imports; asset_register, clinic_papers, sorting_desk, asset_machine come from the scratch folder; the database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and am is not None and under(am.__file__, appdir) and m.DB_PATH == dbp and m.UPLOAD_DIR == env["ASSETS_UPLOADS"])
    ck("W2 the S568 marks: sorting_desk STOCK, clinic_papers STOCK, asset_register STOCK_S568 = S568; stationery.py mounted from the "
       "scratch folder; the S566 / S563 / S560 / S559 / S557 / S555 / S551 marks kept",
       lambda: getattr(sd, "STOCK", None) == "S568" and getattr(cp, "STOCK", None) == "S568" and getattr(m, "STOCK_S568", None) == "S568"
       and st is not None and under(st.__file__, appdir) and st.MOUNTED and st.VERSION == "S568"
       and sd.LAST == "S566" and cp.LAST == "S566" and m.LAST_S566 == "S566" and sd.TIDY == "S563" and sd.RECEIPTS == "S560"
       and sd.ROAD == "S559" and sd.MACHINE == "S557" and sd.CORRECTIONS == "S555" and sd.VERSION == "S551.2" and cp.VERSION == "S551")
    sd.TODAY = TODAY
    am.TODAY = TODAY
    if st is not None:
        st.TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    for k in ("desk.on", "machine.on", "d710.challan_amber_days", "desk.floor", "desk.s441_days", "stationery.issue_on"):
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
        st_ = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no=cols_.pop("stamp_no", None) or ("Z-2031-T" + tag), status=st_, lane=lane,
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

    def form(cl, url, data, **kw):
        return cl.post(url, data=data, **kw)

    def flashes(cl):
        with cl.session_transaction() as ss:
            f_ = list(ss.get("_flashes") or [])
            ss.pop("_flashes", None)
        return " | ".join(x[1] for x in f_)

    def paper(cl, bid):
        r_ = cl.get("/desk/api/paper/%d" % bid)
        return r_.status_code, (r_.get_json(silent=True) or {})

    def month_of(bid):
        return db.execute("SELECT " + cp.MONTH_OF + " FROM bills b WHERE b.id=?", (bid,)).fetchone()[0]

    def stamp(bid):
        return row(bid).get("stamp_no") or ""

    def item_id(name):
        try:
            r_ = db.execute("SELECT id FROM stationery_item WHERE name=? ORDER BY id DESC LIMIT 1", (name,)).fetchone()
        except sqlite3.Error:
            return None
        return r_[0] if r_ else None

    def stock(name):
        i_ = item_id(name)
        return None if (i_ is None or st is None) else round(st.stock_of(db, i_), 4)

    def setting(k, v):
        if v is None:
            db.execute("DELETE FROM settings WHERE key=?", (k,))
        else:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
        db.commit()

    def month_page(cl, ym):
        h_ = html(cl, "/desk/month?ym=" + ym)
        secs = dict(re.findall(r'id="sec-(\w+)".*?class=sectotal data-total="([0-9.\-]+)"', h_, re.S))
        return {k: float(v) for k, v in secs.items()}, h_

    # ================================================================== I1 (item 1): the group Stationery & packaging
    base1, _h = month_page(own, YM)
    mt0 = quiet(lambda: sd.month_total(db, YM, True))
    o1 = mk("O1", "WALK568 OLD OTHERS SHOP", status="approved", subgroup="others", doc_kind="bill", bill_no="OO-1", total_amount=410,
            bill_date="2031-06-03", approved_by="Walk", approved_at="2031-06-03 10:00")         # an existing paper in Others: never moved
    s1 = mk("S1", "WALK568 PRINT HOUSE", status="draft", doc_kind="bill", bill_no="PH-1", total_amount=700, bill_date="2031-06-04",
            items=[("Printed letterheads", 1, 700, 700)])
    c_s1, j_s1 = post(own, "/desk/api/save", {"id": s1, "dest": "stationery", "kind": "bill"})
    h1 = mk("H1", "WALK568 HEAL STATIONERS", status="draft", subgroup="stationery", doc_kind="bill", bill_no="HS-1", total_amount=90,
            bill_date="2031-06-05")                                                               # a draft already in the group
    quiet(lambda: cp.heal(db))
    after1, mh1 = month_page(own, YM)
    mt1 = quiet(lambda: sd.month_total(db, YM, True))
    dh = html(own, "/desk")
    cfgm = re.search(r"var C=(\{.*?\});\nvar S=", dh, re.S)
    cfg = json.loads(cfgm.group(1)) if cfgm else {}
    grp = [g_ for g_ in (cfg.get("groups") or []) if g_[0] == "Clinic consumables"]
    pp1 = html(own, "/papers/%d" % o1)
    old_m = own.get("/papers/month?ym=%s&g=stationery" % YM)
    print("I1 counts: the save answered %s; Stationery section %s (before %s); The month's sections add %s, month_total %s (before %s)"
          % (c_s1, after1.get("stationery"), base1.get("stationery"), sum(after1.values()), mt1, mt0))
    ck("I1 (item 1) 'Stationery & packaging' is a clinic consumables group: on the desk's list after Others; a desk Save files it there and "
       "accepts it (sorted = accepted); the heal accepts a draft already in it; The month has its section after Others and month_total "
       "follows it; the old papers page offers it; an existing Others paper is not moved (D664)",
       lambda: c_s1 == 200 and row(s1).get("subgroup") == "stationery" and row(s1).get("status") == "approved"
       and row(h1).get("status") == "approved" and grp and [x[0] for x in grp[0][1]][-2:] == ["others", "stationery"]
       and dict((x[0], x[1]) for x in grp[0][1]).get("stationery") == "Stationery & packaging"
       and abs(after1.get("stationery", -1) - 790) < 0.005 and base1.get("stationery") == 0.0
       and list(after1.keys()).index("stationery") == list(after1.keys()).index("others") + 1
       and mt1 is not None and abs(mt1 - sum(after1.values())) < 0.005 and abs((mt1 - mt0) - (790 + 410)) < 0.005
       and row(o1).get("subgroup") == "others" and "value=stationery" in pp1 and old_m.status_code == 200
       and cp.SUB.get("stationery") == "Stationery & packaging" and "stationery" in cp.CONSUMABLE and cp.GROUP_OF.get("stationery") == "stationery",
       lambda: dict(save=c_s1, msg=(j_s1.get("message") or j_s1.get("error") or "")[:100], s1=(row(s1).get("subgroup"), row(s1).get("status")),
                    heal=row(h1).get("status"), grp=grp, secs=after1, base=base1, mt=(mt0, mt1), o1=row(o1).get("subgroup"),
                    chooser="value=stationery" in pp1, old=old_m.status_code))

    # ================================================================== I2 (item 2): the item list
    A, RG, PEN, ENV, DUPN = "Walk A4 paper", "Walk Register 200 pages", "Walk Pen blue", "Walk Envelope brown", "Walk a4  PAPER"
    flashes(own)
    g_own = own.get("/stationery")
    g_mgr = mgr.get("/stationery")
    for nm, un, rt, lo in ((A, "ream", "240", "4"), (RG, "piece", "60", ""), (ENV, "packet", "30", "")):
        form(own, "/stationery/item", {"do": "add", "name": nm, "unit": un, "rate": rt, "low": lo})
    f_add = flashes(own)
    form(own, "/stationery/item", {"do": "add", "name": DUPN, "unit": "ream", "rate": "1"})
    f_dup = flashes(own)
    n_a4 = quiet(lambda: db.execute("SELECT COUNT(*) FROM stationery_item WHERE lower(name) LIKE 'walk a4%'").fetchone()[0], -1)
    form(own, "/stationery/item", {"do": "edit", "id": str(item_id(RG) or 0), "name": RG, "unit": "piece", "rate": "65", "low": "2"})
    f_ed = flashes(own)
    rg_rate = quiet(lambda: db.execute("SELECT rate, low_level FROM stationery_item WHERE id=?", (item_id(RG),)).fetchone())
    form(own, "/stationery/item", {"do": "edit", "id": str(item_id(RG) or 0), "name": RG, "unit": "piece", "rate": "60", "low": "2"})
    eid = item_id(ENV)
    form(own, "/stationery/item", {"do": "delete", "id": str(eid or 0)})
    f_del = flashes(own)
    env_gone = item_id(ENV) is None
    m_post = form(mgr, "/stationery/item", {"do": "add", "name": "Walk manager item", "unit": "piece"}).status_code
    print("I2 counts: owner page %s, manager page %s; items made %s; 'Walk a4' items %s; manager's add answered %s"
          % (g_own.status_code, g_mgr.status_code, [x is not None for x in (item_id(A), item_id(RG))], n_a4, m_post))
    ck("I2 (item 2) the owner-only Stationery page: '+ Add item' (name, unit, agreed rate, low level), the same name never twice, edited "
       "in place, an item with no moves deleted (one with moves is retired -- I5); a manager is refused the page and the list",
       lambda: g_own.status_code == 200 and "+ Add item" in g_own.get_data(as_text=True) and g_mgr.status_code == 403
       and item_id(A) and item_id(RG) and n_a4 == 1 and "already on the list" in f_dup and rg_rate is not None
       and abs(rg_rate[0] - 65) < 0.001 and abs(rg_rate[1] - 2) < 0.001 and env_gone and "Deleted" in f_del
       and m_post == 403 and item_id("Walk manager item") is None,
       lambda: dict(own=g_own.status_code, mgr=g_mgr.status_code, add=f_add[:120], dup=f_dup[:80], n_a4=n_a4,
                    rate=tuple(rg_rate) if rg_rate else None, ed=f_ed[:60], deleted=env_gone, fdel=f_del[:60], mpost=m_post))

    # ================================================================== I3 (item 3): received -- from the desk, never twice
    V = "WALK568 VARIETY STATIONERS"
    c1 = mk("C1", V, doc_kind="challan", challan_state="awaiting", created="2031-06-10 05:00:00",
            reading={"doc_kind": "challan", "vendor": V, "items": [
                {"name": "Walk A4 paper 75 GSM", "qty": 5, "unit": "ream", "rate": 250},
                {"name": "Walk Register 200 pages", "qty": 4, "unit": "pcs", "rate": 60},
                {"name": "Printed OPD slips", "qty": 2, "unit": "book"},
                {"name": "Walk Pen blue", "qty": 10, "unit": "piece", "rate": 5},
                {"name": "Stapler pins", "qty": 1, "unit": "box"}]})
    cj0 = paper(own, c1)[1]
    st0 = (cj0.get("stk") or {})
    pre_a = [l_ for l_ in (st0.get("lines") or []) if l_.get("name") == "Walk A4 paper 75 GSM"]
    lines_before = quiet(lambda: db.execute("SELECT COUNT(*) FROM stationery_line WHERE bill_id=?", (c1,)).fetchone()[0], -1)
    L = lambda a_, q4=5: [{"no": 1, "name": "Walk A4 paper 75 GSM", "qty": str(q4), "unit": "ream", "rate": 250, "item": str(item_id(A))},   # noqa: E731
                          {"no": 2, "name": "Walk Register 200 pages", "qty": "4", "unit": "pcs", "rate": 60, "item": str(item_id(RG))},
                          {"no": 3, "name": "Printed OPD slips", "qty": "2", "unit": "book", "rate": None, "item": "ns"},
                          {"no": 4, "name": "Walk Pen blue", "qty": "10", "unit": "piece", "rate": 5, "item": "new"},
                          {"no": 5, "name": "Stapler pins", "qty": "1", "unit": "box", "rate": None, "item": ""}]
    c_c1, j_c1 = post(own, "/desk/api/save", {"id": c1, "dest": "stationery", "kind": "challan", "st_lines": L(None), "mixed": True})
    s_after_c1 = (stock(A), stock(RG), stock(PEN))
    cj1 = paper(own, c1)[1]
    flag_a = [l_.get("flag") for l_ in ((cj1.get("stk") or {}).get("lines") or []) if l_.get("no") == 1]
    c_c1b, j_c1b = post(own, "/desk/api/save", {"id": c1, "dest": "stationery", "kind": "challan", "st_lines": L(None)})       # re-saved as is
    s_resave = stock(A)
    c_c1c, j_c1c = post(own, "/desk/api/save", {"id": c1, "dest": "stationery", "kind": "challan", "st_lines": L(None, 6)})    # re-saved, 6 reams
    s_resave6 = stock(A)
    voided = quiet(lambda: db.execute("SELECT COUNT(*) FROM stationery_line WHERE bill_id=? AND voided_at<>''", (c1,)).fetchone()[0], -1)
    # its bill comes later and joins it: the stock does not rise again
    b1 = mk("B1", V, doc_kind="bill", bill_no="VS-61", total_amount=1500, bill_date="2031-06-12", created="2031-06-12 05:00:00",
            reading={"doc_kind": "tax_invoice", "vendor": V, "bill_no": "VS-61", "total_amount": 1500,
                     "items": [{"name": "Walk A4 paper 75 GSM", "qty": 6, "unit": "ream", "rate": 250}]})
    c_b1, j_b1 = post(own, "/desk/api/save", {"id": b1, "dest": "stationery", "kind": "bill", "joins": [c1],
                                              "st_lines": [{"no": 1, "name": "Walk A4 paper 75 GSM", "qty": "6", "unit": "ream", "rate": 250, "item": str(item_id(A))}]})
    s_join = stock(A)
    c1_after_join = row(c1)
    # an estimate slip counts like a challan; a lone bill (no challan) counts; a line in another unit says so
    e1 = mk("E1", "WALK568 ELEGANS BAGS", doc_kind="estimate", total_amount=300, bill_date="2031-06-11",
            reading={"doc_kind": "estimate", "vendor": "WALK568 ELEGANS BAGS", "items": [
                {"name": "Walk A4 paper", "qty": 2, "unit": "ream", "rate": 240}, {"name": "Carry bag medium", "qty": 100, "unit": "piece", "rate": 3}]})
    c_e1, j_e1 = post(own, "/desk/api/save", {"id": e1, "dest": "stationery", "kind": "estimate", "st_lines": [
        {"no": 1, "name": "Walk A4 paper", "qty": "2", "unit": "ream", "rate": 240, "item": str(item_id(A))},
        {"no": 2, "name": "Carry bag medium", "qty": "100", "unit": "piece", "rate": 3, "item": "ns"}]})
    b2 = mk("B2", "WALK568 OTHER SHOP", doc_kind="bill", bill_no="OS-1", total_amount=1380, bill_date="2031-06-13",
            items=[("Walk Register 200 pages", 3, 60, 180), ("Walk A4 paper box", 1, 1200, 1200)])
    j_b2pre = paper(own, b2)[1]
    c_b2, j_b2 = post(own, "/desk/api/save", {"id": b2, "dest": "stationery", "kind": "bill", "st_lines": [
        {"no": 1, "name": "Walk Register 200 pages", "qty": "3", "unit": "", "rate": 60, "item": str(item_id(RG))},
        {"no": 2, "name": "Walk A4 paper box", "qty": "1", "unit": "box", "rate": 1200, "item": str(item_id(A))}]})
    j_b2 = paper(own, b2)[1]
    unit_flag = [l_.get("flag") for l_ in ((j_b2.get("stk") or {}).get("lines") or []) if l_.get("no") == 2]
    # a matched line with no quantity is refused, nothing saved; an untouched line never blocks
    b3 = mk("B3", "WALK568 THIRD SHOP", doc_kind="bill", bill_no="TS-1", total_amount=60, bill_date="2031-06-13", items=[("Walk Register 200 pages", 1, 60, 60)])
    c_b3x, j_b3x = post(own, "/desk/api/save", {"id": b3, "dest": "stationery", "kind": "bill", "st_lines": [
        {"no": 1, "name": "Walk Register 200 pages", "qty": "", "unit": "", "rate": 60, "item": str(item_id(RG))}]})
    b3_sub_after_refusal = row(b3).get("subgroup")
    c_b3, j_b3 = post(own, "/desk/api/save", {"id": b3, "dest": "stationery", "kind": "bill", "st_lines": [
        {"no": 1, "name": "Walk Register 200 pages", "qty": "1", "unit": "", "rate": 60, "item": str(item_id(RG))}]})
    s_rg_b3 = stock(RG)
    c_b3o, j_b3o = post(own, "/desk/api/save", {"id": b3, "dest": "others", "kind": "bill"})          # moved out: its line taken off
    s_rg_out = stock(RG)
    # a paper with nothing read: one empty line to fill by hand
    n0 = mk("N0", "WALK568 HANDWRITTEN SLIP", doc_kind="challan", challan_state="awaiting")
    jn0 = paper(own, n0)[1]
    print("I3 counts: the challan's save %s -- stock A4 %s, register %s, pen %s; re-saved as is %s; re-saved with 6 %s (voided lines kept %s); "
          "its bill joining it %s -> A4 %s; estimate %s; lone bill %s; a no-quantity line refused %s; register %s -> moved out %s"
          % (c_c1, s_after_c1[0], s_after_c1[1], s_after_c1[2], s_resave, s_resave6, voided, c_b1, s_join, c_e1, c_b2, c_b3x, s_rg_b3, s_rg_out))
    ck("I3 (item 3) received from the desk, stock up once: a challan's matched lines (a pre-match by name offered, never saved before the "
       "Save; 'Add to the list' makes the item; 'not a stock item' and an untouched line count nothing and never block); re-saved -> "
       "replaced, never doubled; its bill joining it later adds nothing; an estimate slip counts like a challan; a lone bill counts; "
       "'rate ₹250 — list ₹240' and 'unit differs' flagged; a matched line with no quantity refused with nothing saved; a paper moved out "
       "of the group has its lines taken off; nothing read -> one empty line to fill",
       lambda: pre_a and pre_a[0].get("sug") and str(pre_a[0].get("item")) == str(item_id(A)) and lines_before == 0
       and c_c1 == 200 and s_after_c1 == (5.0, 4.0, 10.0) and flag_a == ["rate ₹250 — list ₹240"]
       and c_c1b == 200 and "unchanged" in (j_c1b.get("message") or "") and s_resave == 5.0
       and c_c1c == 200 and s_resave6 == 6.0 and voided >= 4
       and c_b1 == 200 and s_join == 6.0 and c1_after_join.get("page_of") == b1 and c1_after_join.get("status") == "rejected"
       and "not added to the stock" in (j_b1.get("message") or "")
       and c_e1 == 200 and stock(A) == 9.0 and c_b2 == 200 and stock(RG) == 7.0 and unit_flag and (unit_flag[0] or "").startswith("unit differs")
       and c_b3x == 400 and "quantity" in (j_b3x.get("error") or "") and b3_sub_after_refusal in (None, "")
       and c_b3 == 200 and s_rg_b3 == 8.0 and c_b3o == 200 and s_rg_out == 7.0 and row(b3).get("subgroup") == "others"
       and (jn0.get("stk") or {}).get("noread") is True and len((jn0.get("stk") or {}).get("lines") or []) == 1,
       lambda: dict(pre=pre_a, lb=lines_before, c1=(c_c1, (j_c1.get("message") or j_c1.get("error") or "")[:200]), s1=s_after_c1, flag=flag_a,
                    resave=(c_c1b, (j_c1b.get("message") or "")[:120], s_resave), r6=(c_c1c, s_resave6, voided),
                    b1=(c_b1, (j_b1.get("message") or j_b1.get("error") or "")[:200], s_join, c1_after_join.get("page_of"), c1_after_join.get("status")),
                    e1=(c_e1, (j_e1.get("error") or "")[:100]), b2=(c_b2, (j_b2.get("error") or "")[:100], unit_flag), a=stock(A), rg=stock(RG),
                    b3x=(c_b3x, (j_b3x.get("error") or "")[:100], b3_sub_after_refusal), b3=(c_b3, s_rg_b3, c_b3o, s_rg_out, row(b3).get("subgroup")),
                    n0=(jn0.get("stk") or {}).get("noread")))

    # ================================================================== I4 (item 4): issued -- the staff screen, switched OFF
    flashes(own); flashes(mgr)
    rcp_u = {"id": None, "username": "walk_rcp_2031", "display_name": "Walk Reception", "role": "reception", "active": 1}
    a_before = stock(A)
    g_own4 = html(own, "/stationery/diya")
    p_own = form(own, "/stationery/diya", {"item": str(item_id(A)), "qty": "2", "place": "lab"}).status_code
    f_own = flashes(own)
    p_over = form(own, "/stationery/diya", {"item": str(item_id(PEN)), "qty": "15", "place": "reception"}).status_code
    f_over = flashes(own)
    pen_after = stock(PEN)
    g_m_off = mgr.get("/stationery/diya")
    p_m_off = form(mgr, "/stationery/diya", {"item": str(item_id(RG)), "qty": "1", "place": "sanjeevni"}).status_code
    rg_m_off = stock(RG)
    home_off = html(own, "/")
    bar_m_off = html(mgr, "/desk/month?ym=" + YM)
    form(own, "/desk/switch", {"key": "stationery.issue_on", "on": "1", "back": "/"})
    sw_on = db.execute("SELECT value FROM settings WHERE key='stationery.issue_on'").fetchone()
    p_m_on = form(mgr, "/stationery/diya", {"item": str(item_id(RG)), "qty": "1", "place": "sanjeevni"}).status_code
    f_m_on = flashes(mgr)
    rg_m_on = stock(RG)
    bar_m_on = html(mgr, "/desk/month?ym=" + YM)
    bar_own = html(own, "/desk/month?ym=" + YM)
    orig_cu = m.current_user
    m.current_user = lambda: rcp_u
    try:
        rc_get = m.app.test_client().get("/stationery/diya").status_code
        rc_post = m.app.test_client().post("/stationery/diya", data={"item": str(item_id(A)), "qty": "1", "place": "lab"}).status_code
    finally:
        m.current_user = orig_cu
    print("I4 counts: owner issue %s (A4 %s -> %s); above stock %s (pen %s); manager with the switch absent: page %s, issue %s; ON: issue %s "
          "(register %s -> %s); reception %s / %s" % (p_own, a_before, stock(A), p_over, pen_after, g_m_off.status_code, p_m_off, p_m_on,
                                                       rg_m_off, rg_m_on, rc_get, rc_post))
    ck("I4 (item 4) 'Stationery diya' (Roman Hinglish): item, quantity, Lab / Reception / Sanjeevni / Clinic, Save with no confirmation -- "
       "stock goes down; above the stock it is still saved (flagged on his page); the owner at once; a manager refused while "
       "stationery.issue_on is absent, allowed once he switches it ON (a row on his Switches card); reception never; the menu: his "
       "'Stationery', the manager's 'Stationery diya' only with the switch ON",
       lambda: "Kya diya?" in g_own4 and "Kisko diya?" in g_own4 and all(w in g_own4 for w in ("Lab", "Reception", "Sanjeevni", "Clinic"))
       and p_own == 302 and "Save ho gaya" in f_own and stock(A) == a_before - 2
       and p_over == 302 and pen_after == -5.0 and "Save ho gaya" in f_over
       and g_m_off.status_code == 200 and "band hai" in g_m_off.get_data(as_text=True) and p_m_off == 403 and rg_m_off == 7.0
       and "Stationery diya for managers" in home_off and sw_on is not None and sw_on[0] == "on"
       and p_m_on == 302 and rg_m_on == 6.0 and "Save ho gaya" in f_m_on
       and rc_get == 403 and rc_post == 403
       and 'data-s559="s568_stock"' in bar_own and 'data-s559="s568_issue"' not in bar_m_off and 'data-s559="s568_issue"' in bar_m_on
       and 'data-s559="s568_stock"' not in bar_m_on,
       lambda: dict(own_page=("Kya diya?" in g_own4), own=(p_own, f_own[:80], a_before, stock(A)), over=(p_over, pen_after, f_over[:60]),
                    m_off=(g_m_off.status_code, p_m_off, rg_m_off), card="Stationery diya for managers" in home_off, sw=tuple(sw_on) if sw_on else None,
                    m_on=(p_m_on, rg_m_on, f_m_on[:60]), rc=(rc_get, rc_post), bars=('data-s559="s568_stock"' in bar_own,
                                                                                    'data-s559="s568_issue"' in bar_m_off, 'data-s559="s568_issue"' in bar_m_on)))

    # ================================================================== I5 (item 5): the inventory -- counts, low stock, the page
    flashes(own); flashes(mgr)
    rg0 = stock(RG)
    form(own, "/stationery/count", {"back": "stock", "c%s" % item_id(RG): "6"})
    f_c1 = flashes(own)
    rg_c1 = stock(RG)
    form(own, "/stationery/diya", {"item": str(item_id(RG)), "qty": "1", "place": "clinic"})
    rg_i = stock(RG)
    form(own, "/stationery/count", {"back": "stock", "c%s" % item_id(RG): "3"})
    rg_c2 = stock(RG)
    cts = quiet(lambda: [dict(r_) for r_ in db.execute("SELECT * FROM stationery_count WHERE item_id=? ORDER BY id", (item_id(RG),))], [])
    form(mgr, "/stationery/count", {"back": "diya", "c%s" % item_id(A): "7"})                       # a manager's count (switch ON)
    f_mc = flashes(mgr)
    a_c = stock(A)
    form(own, "/stationery/item", {"do": "edit", "id": str(item_id(A)), "name": A, "unit": "ream", "rate": "240", "low": "8"})
    flashes(own)
    form(own, "/stationery/item", {"do": "delete", "id": str(item_id(A))})
    f_dela = flashes(own)
    form(own, "/stationery/item", {"do": "retire", "id": str(item_id(A))})
    f_ret = flashes(own)
    retired = quiet(lambda: db.execute("SELECT active FROM stationery_item WHERE id=?", (item_id(A),)).fetchone()[0])
    j_ret = paper(own, b2)[1]
    form(own, "/stationery/item", {"do": "restore", "id": str(item_id(A))})
    flashes(own)
    sp = html(own, "/stationery")
    inv = quiet(lambda: st.inventory(db, YM), {})
    ra = next((r_ for r_ in (inv or {}).get("rows", []) if r_["id"] == item_id(A)), {})
    print("I5 counts: register %s -> first count 6: %s -> issued 1: %s -> second count 3: %s (counts %d: opening %s, not accounted for %s); "
          "manager's count of A4 -> %s; A4 row: stock %s, received this month %s, issued %s, last rate %s, low %s"
          % (rg0, rg_c1, rg_i, rg_c2, len(cts), [c_["opening"] for c_ in cts], [c_["diff"] for c_ in cts], a_c, ra.get("stock"),
             ra.get("recv"), ra.get("by_place"), ra.get("last_rate"), ra.get("is_low")))
    ck("I5 (item 5) the inventory: a first count is the opening stock, a later count records the difference as 'not accounted for' and "
       "sets the stock to it; a manager counts from Stationery diya (switch ON); one row per item -- in stock, received this month, "
       "issued this month by place, last rate paid, a low-stock mark at its level; this month's issues (above stock flagged), the "
       "counts and the papers that fed the stock (links to the desk); an item with moves is retired, never deleted",
       lambda: rg_c1 == 6.0 and rg_i == 5.0 and rg_c2 == 3.0 and len(cts) == 2 and cts[0]["opening"] == 1 and cts[1]["opening"] == 0
       and abs(cts[1]["diff"] - (-2.0)) < 1e-9 and "Count saved" in f_c1 and a_c == 7.0 and "Ginti save ho gayi" in f_mc
       and ra.get("stock") == 7.0 and ra.get("recv") == 9.0 and ra.get("by_place", {}).get("lab") == 2.0 and ra.get("last_rate") is not None
       and ra.get("is_low") is True and "low stock" in sp and "above stock" in sp and "not accounted for" in sp and "opening stock" in sp
       and stamp(c1) in sp and stamp(e1) in sp and stamp(b2) in sp and stamp(b1) not in sp and "/desk?open=%d" % c1 in sp
       and "retired, never deleted" in f_dela and retired == 0 and "Retired" in f_ret
       and not any(str(x.get("id")) == str(item_id(A)) for x in ((j_ret.get("stk") or {}).get("items") or [])),
       lambda: dict(rg=(rg0, rg_c1, rg_i, rg_c2), cts=[(c_["opening"], c_["diff"]) for c_ in cts], fc=f_c1[:60], a_c=a_c, fmc=f_mc[:60],
                    row={k: ra.get(k) for k in ("stock", "recv", "by_place", "last_rate", "is_low")},
                    page=dict(low="low stock" in sp, over="above stock" in sp, na="not accounted for" in sp, op="opening stock" in sp,
                              c1=stamp(c1) in sp, e1=stamp(e1) in sp, b2=stamp(b2) in sp, b1=stamp(b1) in sp, link="/desk?open=%d" % c1 in sp),
                    dela=f_dela[:80], retired=retired, ret=f_ret[:60]))

    # ================================================================== I6 (item 6): the mixed-challan mark
    mix0 = quiet(lambda: st.mixed_n(db, YM), -1)
    c6 = mk("C6", V, doc_kind="challan", challan_state="awaiting", created="2031-06-14 05:00:00")
    c_c6, j_c6 = post(own, "/desk/api/save", {"id": c6, "dest": "lab", "kind": "challan", "mixed": True})
    mix1 = quiet(lambda: st.mixed_n(db, YM), -1)
    sp6 = html(own, "/stationery")
    b7 = mk("B7", V, doc_kind="bill", bill_no="VS-70", total_amount=10, bill_date="2031-06-14")
    note7 = paper(own, b7)[1].get("supplier_note") or ""
    e6 = mk("E6", "WALK568 ESTIMATE ONLY", doc_kind="estimate", total_amount=5, bill_date="2031-06-14")
    c_e6, _j = post(own, "/desk/api/save", {"id": e6, "dest": "stationery", "kind": "estimate", "mixed": True})
    print("I6 counts: mixed papers this month %s -> %s (the challan saved %s, mixed=%s; its earlier challan C1 mixed=%s); the supplier "
          "note says it: %s; an estimate's tick ignored: %s" % (mix0, mix1, c_c6, row(c6).get("mixed"), row(c1).get("mixed"),
                                                                 "Mixed challans this month: 2" in note7, row(e6).get("mixed")))
    ck("I6 (item 6) 'mixed: clinic + lab items' on a challan or a bill is stored on the paper (bills.mixed, audited) -- a joined challan "
       "still counts; the owner's Stationery page and the supplier note show 'Mixed challans this month: N'; an estimate slip takes no tick",
       lambda: row(c1).get("mixed") == 1 and len(aud(c1, "mixed")) == 1 and c_c6 == 200 and row(c6).get("mixed") == 1
       and mix1 == mix0 + 1 and mix0 >= 1 and ("Mixed challans this month: %d" % mix1) in sp6
       and "Mixed challans this month: 2" in note7 and c_e6 == 200 and not row(e6).get("mixed"),
       lambda: dict(c1=row(c1).get("mixed"), aud=len(aud(c1, "mixed")), c6=(c_c6, row(c6).get("mixed"), (j_c6.get("error") or "")[:80]),
                    mix=(mix0, mix1), page=("Mixed challans this month: %d" % mix1) in sp6, note=note7[-160:], e6=row(e6).get("mixed")))

    # ================================================================== I7 (item 7): Add a paper from a file; the Aumni preset
    flashes(own); flashes(mgr)
    seen_commits, top = [], db.execute("SELECT COALESCE(MAX(id),0) FROM bills").fetchone()[0]
    spy = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)

    class Spy(object):
        def __init__(self, real):
            object.__setattr__(self, "_r", real)

        def __getattr__(self, k):
            return getattr(self._r, k)

        def commit(self):
            self._r.commit()
            seen_commits.extend(spy.execute("SELECT id, kind FROM bills WHERE id>?", (top,)).fetchall())
    orig_get_db = m.get_db
    m.get_db = lambda: Spy(orig_get_db())
    try:
        g_add = own.get("/desk/add")
        r_x = own.post("/desk/add", data={"what": "pexp", "paid_on": "12-06-2031", "amount": "1,180", "note": "walk",
                                          "paper_file": (io.BytesIO(made_up_pdf("Walk568 made-up invoice AUM-1")), "walk568_a.pdf")},
                       content_type="multipart/form-data")
        r_y = own.post("/desk/add", data={"what": "pexp", "paid_on": "12-06-2031", "amount": "640",
                                          "paper_file": (io.BytesIO(made_up_pdf("Walk568 made-up invoice AUM-2")), "walk568_b.pdf")},
                       content_type="multipart/form-data")
        r_nop = own.post("/desk/add", data={"what": "pexp", "paid_on": "", "amount": "640",
                                            "paper_file": (io.BytesIO(made_up_pdf("Walk568 made-up invoice AUM-3")), "walk568_c.pdf")},
                         content_type="multipart/form-data")
        r_pl = own.post("/desk/add", data={"what": "paper", "lane": "clinic", "challan": "1",
                                           "paper_file": (io.BytesIO(made_up_pdf("Walk568 made-up challan PL-1")), "walk568_d.pdf")},
                        content_type="multipart/form-data")
        r_bad = own.post("/desk/add", data={"what": "paper", "lane": "made_up_lane",
                                            "paper_file": (io.BytesIO(made_up_pdf("Walk568 made-up PL-2")), "walk568_e.pdf")},
                         content_type="multipart/form-data")
        setting("desk.on", None)
        r_moff = mgr.post("/desk/add", data={"what": "pexp", "paid_on": "12-06-2031", "amount": "5",
                                             "paper_file": (io.BytesIO(made_up_pdf("Walk568 made-up AUM-4")), "walk568_f.pdf")},
                          content_type="multipart/form-data")
        setting("desk.on", "on")
        r_ph = own.post("/desk/add", data={"what": "paper", "lane": "pharmacy",
                                           "paper_file": (io.BytesIO(made_up_pdf("Walk568 made-up Marg-type scan")), "walk568_g.pdf")},
                        content_type="multipart/form-data")
    finally:
        m.get_db = orig_get_db
    spy.close()
    newrows = [dict(r_) for r_ in db.execute("SELECT * FROM bills WHERE id>? ORDER BY id", (top,))]
    pex = [r_ for r_ in newrows if (r_.get("kind") or "") == "Pharmacy expense"]
    plain = [r_ for r_ in newrows if (r_.get("lane") or "") == "clinic"]
    phs = [r_ for r_ in newrows if (r_.get("kind") or "") == "Pharmacy"]
    ever_ph = [x for x in seen_commits if x[0] in {p_["id"] for p_ in pex} and x[1] == "Pharmacy"]
    pay_rows = quiet(lambda: db.execute("SELECT COUNT(*) FROM paper_payment_bill WHERE bill_id IN (%s)" % ",".join(str(p_["id"]) for p_ in pex)).fetchone()[0]
                     if pex else 0, -1)
    paid_aud = [json.loads(a_["detail"] or "{}") for p_ in pex for a_ in aud(p_["id"], "paid")]
    # Sanjeevni's four readers, read only (their own query text, run on the scratch copy)
    sanj, found = {}, {}
    for f_, least in SANJ:
        src_ = open(os.path.join(fin, f_), encoding="utf-8").read() if os.path.exists(os.path.join(fin, f_)) else ""
        cl_ = re.findall(r"WHERE (kind='Pharmacy'[^\"]*)\"", src_)
        found[f_] = len(cl_)
        for i_, c_ in enumerate(cl_):
            c2 = re.split(r"\s+ORDER BY\s+", c_)[0].replace("?", "'2000-01-01'")
            ids_ = {r_[0] for r_ in db.execute("SELECT id FROM bills WHERE " + c2)}
            sanj["%s#%d" % (f_, i_ + 1)] = ids_
    pex_ids = {p_["id"] for p_ in pex}
    ph_ids = {p_["id"] for p_ in phs}
    in_sanj = sorted(k for k, v in sanj.items() if v & pex_ids)
    ph_seen = sorted(k for k, v in sanj.items() if v & ph_ids)
    # the system never moves it: the supplier's earlier papers all person-placed on the clinic lane in one group
    moved = []
    if pex:
        px = pex[0]
        db.execute("UPDATE bills SET vendor='WALK568 AUMNI CRAFTS', bill_no='AUM-1', total_amount=1180, ocr_status='read' WHERE id=?", (px["id"],))
        if len(pex) > 1:
            db.execute("UPDATE bills SET vendor='WALK568 AUMNI CRAFTS', bill_no='AUM-2', total_amount=640, ocr_status='read' WHERE id=?", (pex[1]["id"],))
        for t_ in ("H71", "H72", "H73"):
            hb = mk(t_, "WALK568 AUMNI CRAFTS", status="approved", subgroup="others", doc_kind="bill", bill_no=t_, total_amount=1)
            db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (hb, "2031-06-01 10:00", "Walk", "subgroup", "{}"))
        db.commit()
        moved = quiet(lambda: cp.auto_home(db, px["id"]), ["error"])
        quiet(lambda: cp.heal_auto(db))
        hist = quiet(lambda: cp.supplier_history(db, cp._supplier_key("WALK568 AUMNI CRAFTS"), -1), ({}, {}))
    else:
        hist = ({}, {})
    s441_apart = None
    if len(pex) > 1 and getattr(m, "S441", None) is not None:
        quiet(lambda: m.S441.run_pass(db, only=pex[1]["id"], upload_dir=m.UPLOAD_DIR))
        s441_apart = row(pex[0]["id"]).get("page_of") is None and row(pex[1]["id"]).get("page_of") is None
    # The month: its own line, never in a section or the total
    pm_ym = month_of(pex[0]["id"]) if pex else YM
    secs_x, mhx = month_page(own, pm_ym)
    mtx = quiet(lambda: sd.month_total(db, pm_ym, True))
    pexp_line = re.search(r'id=s568pexp.*?<b>([^<]*)</b>', mhx, re.S)
    apart_ph = re.search(r"<span>Pharmacy — Sanjeevni</span><b>(\d+) scan", mhx)
    n_ph_month = db.execute("SELECT COUNT(*) FROM bills b WHERE b.lane='pharmacy' AND b.status<>'rejected' AND b.dup_of IS NULL AND b.page_of IS NULL "
                            "AND COALESCE(b.kind,'')<>'Pharmacy expense' AND " + cp.MONTH_OF + "=?", (pm_ym,)).fetchone()[0]
    # the old edit page keeps the kind; the re-lane door: a manager refused, the owner's move audited
    if pex:
        px = pex[0]
        form(own, "/bills/%d/edit" % px["id"], {"vendor": "WALK568 AUMNI CRAFTS", "bill_no": "AUM-1", "bill_date": "", "kind": "Consumable",
                                                "total_amount": "1180"})
        kind_after_edit = row(px["id"]).get("kind")
        rl_m = form(mgr, "/bills/%d/lane" % px["id"], {"lane": "clinic"}).status_code
        lane_after_m = row(px["id"]).get("lane")
        rl_o = form(own, "/bills/%d/lane" % pex[-1]["id"], {"lane": "other_doc"}).status_code
        rl_aud = [json.loads(a_["detail"] or "{}") for a_ in aud(pex[-1]["id"], "relane")]
        bpage = html(own, "/bills/%d" % px["id"])
    else:
        bpage = ""
        kind_after_edit, rl_m, lane_after_m, rl_o, rl_aud = None, None, None, None, []
    msg_x = htmlmod.unescape(r_x.headers.get("Location") or "")
    print("I7 counts: the add page %s; preset saves %s / %s, no paid day %s, plain challan %s -> %s, a made-up lane %s, a manager with "
          "the desk off %s, a pharmacy scan %s; papers made: pharmacy expense %d, clinic %d, Marg-type %d; commits seen showing a preset as "
          "'Pharmacy': %d; payment rows %s; Sanjeevni queries found %s -- holding a preset: %s, holding the Marg-type scan: %d of %d; "
          "auto_home %s; the supplier's history lanes %s; S441 kept two presets apart: %s; The month %s: its line %r, pharmacy count "
          "%s = %s; month_total %s = sections %s; kind after the old edit %r; re-lane: manager %s (lane %s), owner %s"
          % (g_add.status_code, r_x.status_code, r_y.status_code, r_nop.status_code, r_pl.status_code, (r_pl.headers.get("Location") or "")[-30:],
             r_bad.status_code, r_moff.status_code, r_ph.status_code, len(pex), len(plain), len(phs), len(ever_ph), pay_rows, found, in_sanj,
             len(ph_seen), len(sanj), moved, list(hist[0].keys()) if hist else None, s441_apart, pm_ym,
             pexp_line.group(1) if pexp_line else None, apart_ph.group(1) if apart_ph else None, n_ph_month, mtx, sum(secs_x.values()),
             kind_after_edit, rl_m, lane_after_m, rl_o))
    ck("I7 (item 7) 'Add a paper from a file' through the intake's own path: the preset files the PDF on the pharmacy lane as "
       "kind 'Pharmacy expense' (doc_kind bill, captured) -- no commit ever shows it as 'Pharmacy' -- paid on the paper itself (the "
       "day and amount typed; one audit 'paid' how card, 'Dr MK's card'; no payment row); absent from all four Sanjeevni-side queries "
       "(a Marg-type scan present); never moved by the system (auto_home, the heal, supplier_history); two presets stay apart; The month "
       "shows 'Sanjeevni — pharmacy expenses' outside every section and total; the old edit keeps the kind; the re-lane door refuses a "
       "manager and audits the owner's move; the plain form offers the intake's lanes and its challan tick; a manager with the desk off is refused",
       lambda: g_add.status_code == 200 and r_x.status_code == 302 and r_y.status_code == 302 and len(pex) == 2
       and all(p_["lane"] == "pharmacy" and p_["status"] == "captured" and p_["doc_kind"] == "bill" for p_ in pex)
       and pex[0]["paid_on"] == "2031-06-12" and abs((pex[0]["paid_amount"] or 0) - 1180) < 0.005 and not ever_ph and seen_commits
       and pay_rows == 0 and len(paid_aud) == 2 and all(a_.get("how") == "card" and a_.get("note") == "Dr MK's card" for a_ in paid_aud)
       and r_nop.status_code == 302 and len(newrows) == 4
       and all(found.get(f_, 0) >= least for f_, least in SANJ) and not in_sanj and len(phs) == 1 and len(ph_seen) == len(sanj)
       and moved == [] and row(pex[0]["id"]).get("lane") == "pharmacy" and row(pex[0]["id"]).get("kind") == "Pharmacy expense"
       and "pharmacy" not in (hist[0] if hist else {"pharmacy": 1}) and s441_apart in (True, None)
       and pexp_line is not None and pexp_line.group(1).startswith("2 · ₹1,820") and "paid by Dr MK's card" in pexp_line.group(1)
       and apart_ph is not None and int(apart_ph.group(1)) == n_ph_month and mtx is not None and abs(mtx - sum(secs_x.values())) < 0.005
       and kind_after_edit == "Pharmacy expense" and "Sanjeevni pharmacy expense — Paid 12-06-2031" in bpage and "paid by Dr MK&#39;s card" in bpage
       and rl_m == 403 and lane_after_m == "pharmacy" and rl_o == 302
       and any(a_.get("kind_from") == "Pharmacy expense" for a_ in rl_aud)
       and r_pl.status_code == 302 and "/desk?open=" in (r_pl.headers.get("Location") or "") and len(plain) == 1
       and plain[0]["doc_kind"] == "challan" and plain[0]["kind"] == "Consumable" and r_bad.status_code == 302 and r_moff.status_code == 403,
       lambda: dict(add=g_add.status_code, x=(r_x.status_code, msg_x[-160:]), y=r_y.status_code, pex=[{k: p_.get(k) for k in ("lane", "status", "doc_kind", "paid_on", "paid_amount")} for p_ in pex],
                    ever_ph=len(ever_ph), commits=len(seen_commits), pay=pay_rows, paud=paid_aud, nop=r_nop.status_code, found=found, in_sanj=in_sanj,
                    phs=len(phs), ph_seen=len(ph_seen), nsanj=len(sanj), moved=moved, hist=hist[0] if hist else None, s441=s441_apart,
                    line=pexp_line.group(1) if pexp_line else None, ph=(apart_ph.group(1) if apart_ph else None, n_ph_month), mt=(mtx, sum(secs_x.values())),
                    kind=kind_after_edit, card=re.findall(r"id=s568card[^>]*>([^<]*)<", bpage), rl=(rl_m, lane_after_m, rl_o, rl_aud), pl=(r_pl.status_code, r_pl.headers.get("Location"), [(p_["doc_kind"], p_["kind"]) for p_ in plain]),
                    bad=r_bad.status_code, moff=r_moff.status_code))

    # ================================================================== I8 (item 8): the pack fix -- only bills and invoices
    if "--no-pack" in ARGS:                                         # the installer: packs.py STOPPED (not at its FROM pin)
        print("I8 NOT RUN -- packs.py was stopped (not at its FROM pin); the pack fix is not in this install")
        ck("Z1 the made-up rows live in the scratch copy only", lambda: dbp.startswith(work) and m.DB_PATH == dbp)
        db.close()
        return
    pk_path = os.path.join(D, "packs.py") if os.path.exists(os.path.join(D, "packs.py")) else os.path.join(fin, "packs.py")
    pk_before = os.path.join(fin, "packs.py")
    res8 = quiet(lambda: pack_check(pk_path, pk_before, fin, work), None)
    if res8:
        print("I8 counts: before -- %s" % res8["before_txt"])
        print("I8 counts: after  -- %s" % res8["after_txt"])
    ck("I8 (item 8) the parent's build_bundle (8.1-8.4) takes only bills and invoices: an estimate slip and a final (paid-on-challan) "
       "challan are in 8.1 before the fix and in no bundle after it; a paper with no kind set stays in; receipts, statements and waiting "
       "challans stay out; a 'Pharmacy expense' paper is in no bundle; 8.4 unchanged",
       lambda: res8 is not None and res8["ok"],
       lambda: res8)

    ck("Z1 the made-up rows live in the scratch copy only", lambda: dbp.startswith(work) and m.DB_PATH == dbp)
    db.close()


PACK_ROWS = [  # stamp, lane, status, doc_kind, challan_state, subgroup, to_accountant, kind
    ("Z-S568-LN", "lab_purchase", "captured", None, None, None, 0, "Lab"),
    ("Z-S568-LB", "lab_purchase", "captured", "bill", None, None, 0, "Lab"),
    ("Z-S568-LE", "lab_purchase", "captured", "estimate", None, None, 0, "Lab"),
    ("Z-S568-LF", "lab_purchase", "captured", "challan", "final", None, 0, "Lab"),
    ("Z-S568-LC", "lab_purchase", "captured", "challan", "awaiting", None, 0, "Lab"),
    ("Z-S568-LR", "lab_purchase", "captured", "receipt", None, None, 0, "Lab"),
    ("Z-S568-OE", "owner_expense", "captured", "estimate", None, None, 0, "Expense"),
    ("Z-S568-OB", "owner_expense", "captured", "bill", None, None, 0, "Expense"),
    ("Z-S568-CB", "clinic", "approved", "bill", None, "construction", 1, "Consumable"),
    ("Z-S568-PX", "pharmacy", "captured", "bill", None, None, 0, "Pharmacy expense"),
]
PACK_LANES = ("lab_purchase", "owner_expense", "owner_expense_bhawna", "construction_accountant")


def pack_check(pk_path, pk_before, fin, work):
    wd = os.path.join(work, "pack")
    os.makedirs(os.path.join(wd, "finance"), exist_ok=True)
    for f in os.listdir(fin):                                         # the program files only -- never a database or a scan
        fp = os.path.join(fin, f)
        if os.path.isfile(fp) and f.endswith((".py", ".html")) and ".bak" not in f and f != "packs.py":
            shutil.copy(fp, os.path.join(wd, "finance"))
    if os.path.join(wd, "finance") not in sys.path:
        sys.path.insert(0, os.path.join(wd, "finance"))
    dbp = os.path.join(wd, "made_up_assets.db")
    c = sqlite3.connect(dbp)
    c.execute("CREATE TABLE bills(id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, source_stored TEXT, "
              "late_for TEXT, created_at TEXT, bill_month TEXT, lane TEXT, status TEXT, doc_kind TEXT, challan_state TEXT, subgroup TEXT, "
              "to_accountant INTEGER NOT NULL DEFAULT 0, pe_who TEXT, kind TEXT)")
    for i, (stp, lane, status, dk, cs, sg, ta, kd) in enumerate(PACK_ROWS, 1):
        c.execute("INSERT INTO bills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (i, stp, "Made-Up Supplier %d" % i, "N%d" % i, "2031-09-0%d" % min(i, 9),
                                                                                  10.0 * i, None, None, "2031-09-01 10:00", "2031-09", lane, status, dk, cs, sg, ta, None, kd))
    c.commit(); c.close()

    def bundles(path, name):
        shutil.copy(path, os.path.join(wd, "finance", name + ".py"))
        spec = importlib.util.spec_from_file_location(name, os.path.join(wd, "finance", name + ".py"))
        pk = importlib.util.module_from_spec(spec); sys.modules[name] = pk; spec.loader.exec_module(pk)
        cap = []

        def con():
            x = sqlite3.connect(dbp); x.row_factory = sqlite3.Row; return x
        pk._assets_con = con
        pk._text_pdf = lambda title, lines: (cap.append(list(lines)), b"%PDF-1.4 made-up index")[1]
        book = sqlite3.connect(":memory:")
        book.execute("CREATE TABLE pack_send(id INTEGER PRIMARY KEY, month TEXT, sent_at TEXT, sent_by TEXT)")
        out = {}
        for lane in PACK_LANES:
            del cap[:]
            b, _why = pk.build_bundle(book, "2031-09", lane)
            out[lane] = sorted(x[7:] for x in re.findall(r"Z-S568-\w\w", " ".join(cap[0]))) if (b and cap) else []
        return out
    after = bundles(pk_path, "packs_walked_s568")
    before = bundles(pk_before, "packs_before_s568")
    allin = lambda d_: sorted(set(sum(d_.values(), [])))               # noqa: E731
    ok = (after["lab_purchase"] == ["LB", "LN"] and after["owner_expense"] == ["OB"] and after["construction_accountant"] == ["CB"]
          and "LE" not in allin(after) and "LF" not in allin(after) and "OE" not in allin(after) and "PX" not in allin(after)
          and "LC" not in allin(after) and "LR" not in allin(after)
          and "LE" in before["lab_purchase"] and "LF" in before["lab_purchase"] and "OE" in before["owner_expense"]
          and "PX" not in allin(before) and before["construction_accountant"] == ["CB"])
    return {"ok": ok, "before": before, "after": after,
            "before_txt": " ".join("%s=%s" % (k, ",".join(v) or "-") for k, v in before.items()),
            "after_txt": " ".join("%s=%s" % (k, ",".join(v) or "-") for k, v in after.items())}


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
        must_ = tuple(k for k in MUST_RED if not (k == "I8" and "--no-pack" in ARGS))
        not_red = [k for k in must_ if seen_.get(k) is not False]
        print("CONTROL must-be-red: %s -- %s" % (", ".join(must_),("all RED" if not not_red else "NOT red: " + ", ".join(
            k + ("(green)" if seen_.get(k) else "(not reached)") for k in not_red))))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
