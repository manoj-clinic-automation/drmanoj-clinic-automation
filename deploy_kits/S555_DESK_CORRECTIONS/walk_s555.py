#!/usr/bin/env python3
"""walk_s555.py -- the S555_DESK_CORRECTIONS walk. The app with the given files on a COPY of a database (SQLite's backup API),
in its own scratch folder; made-up rows only (suppliers WALK.., stamps Z-2031-S5.., dated around a made-up today of
15-Jun-2031), made-up logins; no reader thread, no paid call, nothing sent anywhere (a made-up key and URL; the reader is a
stub that only counts). Flask's test client; no port. Isolated exactly as walk_s551.py (S551 v4 s6).

    python3 -B walk_s555.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py>
                            <assets.db to copy> [--work DIR] [--shared DIR] [--expect-red] [--keep]

GREEN / RED per check; exit 1 on any RED. --expect-red (the control on the old files): exit 0 only if every check named in
MUST_RED is RED. The work folder (default: a new folder under /tmp) is removed at the end unless --keep."""
import argparse, datetime, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile, time
from html.parser import HTMLParser

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "I1", "I2a", "I2b", "I2d", "I3", "I4", "I5", "I6", "I8a", "I8b")      # red on the old files, by name
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py")
OWN_WORD = "walkown"                     # a made-up own-name word, added to clinic_papers' own list on the scratch copy only


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


VOID = {"input", "br", "img", "meta", "link", "hr", "source", "area", "col", "embed", "param", "track", "wbr"}


class Tree(HTMLParser):
    """Each element id -> the ids of the elements around it (outermost first)."""
    def __init__(self):
        HTMLParser.__init__(self)
        self.stack, self.anc = [], {}

    def handle_starttag(self, tag, attrs):
        i = dict(attrs).get("id")
        if i:
            self.anc[i] = [x[1] for x in self.stack if x[1]]
        if tag not in VOID:
            self.stack.append((tag, i))

    def handle_endtag(self, tag):
        for k in range(len(self.stack) - 1, -1, -1):
            if self.stack[k][0] == tag:
                del self.stack[k:]
                break


def visible(html):
    t = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    return re.sub(r"<[^>]+>", " ", t)


OLD_DATE = re.compile(r"\b\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b|\b\d{4}-\d{2}-\d{2}\b")


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S555_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s555walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
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
    # the copy, before the import: the reader off, the desk's floor, desk.on absent, a made-up manager, a made-up own-name word
    c = sqlite3.connect(dbp)
    for k in ("desk.on", "d710.challan_amber_days", "desk.floor", "desk.s441_days"):
        c.execute("DELETE FROM settings WHERE key=?", (k,))
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    r0 = c.execute("SELECT value FROM settings WHERE key='d664.words.own_name'").fetchone()
    c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('d664.words.own_name',?)", (((r0[0] + ",") if (r0 and r0[0]) else "") + OWN_WORD,))
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
    ck("W1 the app imports; asset_register, clinic_papers, claude_reader and sorting_desk come from the scratch folder",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and under(m.CLAUDE.__file__, appdir) and sd is not None and under(sd.__file__, appdir))
    ck("W2 sorting_desk carries the S555 corrections (VERSION kept at S551.2 for S551's walk)",
       lambda: getattr(sd, "CORRECTIONS", None) == "S555" and sd.VERSION == "S551.2")
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
    own, mgr = client(own_u), client(mgr_u)
    made = {}

    def mk(tag, vendor=None, lane="clinic", status=None, created="2031-06-10 05:00:00", pdf=False, items=(), kind=None, **cols):
        kd = kind or {"clinic": "Consumable", "other_doc": "Document", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy", None: "Consumable"}[lane]
        st = status or ("draft" if lane in ("clinic", None) else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no="Z-2031-S5" + tag, status=st, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk")
        if pdf:
            fn = "walk_s555_%s.pdf" % tag.lower()
            open(os.path.join(up, fn), "wb").write(tiny_pdf(tag)); vals["source_stored"] = fn; vals["source_orig"] = fn
        vals.update(cols)
        cur = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values()))
        bid = cur.lastrowid
        for it in items:
            db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (bid, it[0], it[1], it[2] if len(it) > 2 else None, None))
        db.commit()
        made[tag] = bid
        return bid

    def reading(bid, data, ok=1, kind="tax_invoice"):
        db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,?,?,?)",
                   (bid, "2031-06-12 10:00", "walk", ok, kind, json.dumps(data)))
        db.commit()

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
        j = cl.get("/desk/api/list").get_json(silent=True) or {}
        return {p["id"]: p for p in (j.get("papers") or [])}

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    # ------------------------------------------------------------------ I1: Save always on screen (the panel's footer)
    t = html(own, "/desk")
    tr = Tree()
    tr.feed(t.split("<script>")[0])
    A = tr.anc
    css = " ".join(re.findall(r"(?s)<style>(.*?)</style>", t))

    def rule(sel):
        mm = re.search(r"(?<![\w-])" + re.escape(sel) + r"\{([^}]*)\}", css)
        return mm.group(1) if mm else None
    ck("I1 the Save button, its line and the 'page of another paper / Blank' row sit in the right panel's non-scrolling footer; the fields scroll above it",
       lambda: "foot" in A.get("save", []) and "fields" not in A.get("save", []) and "foot" in A.get("savednote", []) and "foot" in A.get("pagebox", [])
       and "foot" in A.get("blank", []) and "fields" in A.get("f_vendor", []) and "fields" in A.get("groups", []) and "fields" in A.get("flags", [])
       and A.get("foot", [None])[-1] == "panel" and A.get("fields", [None])[-1] == "panel" and "right" in A.get("panel", [])
       and "left" in A.get("list", []) and "fields" not in A.get("foot", []),
       lambda: {k: A.get(k) for k in ("save", "savednote", "pagebox", "blank", "f_vendor", "foot", "fields")})
    ck("I1b the CSS: the panel a column flex box; the fields area overflow:auto + flex:1; the footer flex:none; the left list keeps its own scroll",
       lambda: "flex-direction:column" in (rule("#right") or "") and "overflow:auto" not in (rule("#right") or "x")
       and "flex-direction:column" in (rule("#panel") or "") and "min-height:0" in (rule("#panel") or "")
       and "overflow:auto" in (rule("#fields") or "") and "flex:1" in (rule("#fields") or "") and "flex:none" in (rule("#foot") or "")
       and "overflow:auto" in (rule("#list") or "") and "html,body{height:100%;overflow:hidden}" in t,
       lambda: (rule("#right"), rule("#panel"), rule("#fields"), rule("#foot")))

    # ------------------------------------------------------------------ I2: dates as dd-mm-yyyy
    DV = "WALKDT DATE SUPPLIES"
    dc = mk("DC1", DV, doc_kind="challan", challan_state="awaiting", bill_date="2031-06-08", created="2031-06-08 05:00:00", items=[("Gauze", 2)])
    db_ = mk("DB1", DV, bill_no="DT-1", total_amount=120, bill_date="2031-06-10", created="2031-06-12 05:00:00", items=[("Gauze", 2)])
    _c, jd = paper(own, db_)
    cvd = jd.get("covers") or [{}]
    ck("I2a the desk shows dates as dd-mm-yyyy: the Date box, 'scanned', the covers box, the supplier note",
       lambda: jd.get("date") == "10-06-2031" and jd.get("scanned") == "12-06-2031" and cvd[0].get("date") == "08-06-2031" and "08-06-2031" in jd.get("supplier_note", ""),
       lambda: (jd.get("date"), jd.get("scanned"), cvd[0].get("date"), jd.get("supplier_note")))
    IV = "WALKDI IMPLANT DATES"
    ib = mk("IB1", IV, status="approved", subgroup="implant_stock", bill_no="DI-9", total_amount=900, bill_date="2031-06-04", approved_by="Walk", items=[("Plate", 1, 900)])
    own.post("/desk/implants/pay", data={"s": "walkdi implant", "day": "06-06-2031", "amount": "100", "how": "Cash", "against": ""})
    own.post("/desk/implants/check", data={"s": "walkdi implant"})
    ta, tl, tm, tk = html(own, "/desk/awaited"), html(own, "/desk/implants?s=walkdi+implant"), html(own, "/desk/month?ym=2031-06"), html(own, "/desk")
    bad = [x for p_ in (ta, tl, tm, tk) for x in OLD_DATE.findall(visible(p_))]
    ck("I2b Bills awaited, the implant ledger, The month and the desk: every date dd-mm-yyyy ('checked up to 15-06-2031'), none in another form",
       lambda: "08-06-2031" in ta and "04-06-2031" in tl and "06-06-2031" in tl and "checked up to 15-06-2031" in tl and not bad,
       lambda: ("08-06-2031" in ta, "04-06-2031" in tl, "checked up to 15-06-2031" in tl, bad[:4]))
    forms = (("F1", "21-08-2030", "2030-08-21"), ("F2", "5-6-31", "2031-06-05"), ("F3", "21/08/2030", "2030-08-21"), ("F4", "2030-08-21", "2030-08-21"))
    got = {}
    for tag, typed, iso in forms:
        b_ = mk(tag, "WALKF FORM TRADERS", bill_no="FM-" + tag, total_amount=10, bill_date="2031-06-01", created="2031-06-12 05:00:00")
        code, j = save(own, id=b_, dest="others", kind="bill", bill_date=typed)
        got[typed] = (code, row(b_)["bill_date"], iso)
    pf = mk("PF1", "WALKP PAID FORMS", doc_kind="challan", challan_state="final", subgroup="procedure", total_amount=50, bill_date="2031-06-05", items=[("Swab", 1, 50)])
    own.post("/desk/awaited/pay", data={"bid": pf, "paid_on": "13/06/2031", "amount": "50"})
    own.post("/desk/implants/pay", data={"s": "walkdi implant", "day": "7-6-31", "amount": "5", "how": "Cash", "against": ""})
    try:
        ipd = [r_[0] for r_ in db.execute("SELECT day FROM implant_payment WHERE supplier_key='walkdi implant' ORDER BY id")]
    except sqlite3.Error:
        ipd = []
    ck("I2c each accepted form (dd-mm-yyyy, d-m-yy, dd/mm/yyyy, yyyy-mm-dd) is stored as ISO yyyy-mm-dd (bill_date, paid_on, implant_payment.day)",
       lambda: all(v[0] == 200 and v[1] == v[2] for v in got.values()) and row(pf)["paid_on"] == "2031-06-13" and "2031-06-07" in ipd,
       lambda: (got, row(pf)["paid_on"], ipd))
    bd = mk("BD1", "WALKB BAD DATES", bill_no="BD-1", total_amount=10, bill_date="2031-06-02", created="2031-06-12 05:00:00")
    c1, j1 = save(own, id=bd, dest="others", kind="bill", bill_date="31-02-2031")
    c2, j2 = save(own, id=bd, dest="others", kind="bill", bill_date="not a date")
    n_ip = len(ipd)
    own.post("/desk/implants/pay", data={"s": "walkdi implant", "day": "32-13-2031", "amount": "5", "how": "Cash", "against": ""})
    try:
        n_ip2 = db.execute("SELECT COUNT(*) FROM implant_payment WHERE supplier_key='walkdi implant'").fetchone()[0]
    except sqlite3.Error:
        n_ip2 = -1
    rb = row(bd)
    ck("I2d a date that cannot be understood is refused with one plain line; nothing is written (bill, audit, payment)",
       lambda: c1 == 400 and c2 == 400 and "not understood" in j1.get("error", "") and "\n" not in j1.get("error", "")
       and (rb["bill_date"], rb["subgroup"], rb["status"]) == ("2031-06-02", None, "draft") and not aud(bd, "desk_saved") and n_ip2 == n_ip,
       lambda: (c1, j1.get("error"), c2, rb["bill_date"], rb["subgroup"], n_ip, n_ip2))

    # ------------------------------------------------------------------ I3: the misread-date flag on a genuinely older bill
    def mr(days, scan=TODAY):
        return sd.misread_date({"bill_date": (scan + datetime.timedelta(days=days)).isoformat(), "created_at": scan.isoformat() + " 05:00:00"}, TODAY)
    old = mk("OB1", "WALKO OLDER BILLS", bill_no="OB-1", total_amount=10, bill_date=(datetime.date(2031, 6, 12) - datetime.timedelta(days=358)).isoformat(), created="2031-06-12 05:00:00")
    _c, jo = paper(own, old)
    wo = wlist(own)
    ck("I3 misread date: 358 days before the scan NOT flagged (nor 400; nor 7 after); 401 days before, 8 days after and 2014 flagged",
       lambda: not mr(-358) and not mr(-400) and not mr(7) and mr(-401) and mr(8)
       and sd.misread_date({"bill_date": "2014-12-31", "created_at": "2015-01-05 05:00:00"}, TODAY)
       and jo.get("flags", {}).get("date") is False and "date" not in (wo.get(old) or {}).get("why", []),
       lambda: (mr(-358), mr(-400), mr(7), mr(-401), mr(8), jo.get("flags")))

    # ------------------------------------------------------------------ I4: a supplier read as the buyer (the own name)
    OWNV = OWN_WORD.upper() + " CLINIC 2031"
    o1 = mk("OW1", OWNV, bill_no="OW-1", total_amount=300, bill_date="2031-06-11", created="2031-06-12 05:00:00", items=[("Gauze", 1)])
    reading(o1, {"vendor": "WALKV TRUE SUPPLIERS", "bill_no": "OW-1", "bill_date": "2031-06-11", "total_amount": 300, "made_out_to": "clinic", "items": []})
    o2 = mk("OW2", OWNV, bill_no="OW-2", total_amount=300, bill_date="2031-06-11", created="2031-06-12 05:00:00")
    reading(o2, {"vendor": OWN_WORD.title() + " Clinic", "bill_no": "OW-2", "bill_date": "2031-06-11", "total_amount": 300, "items": []})
    before = (row(o1)["vendor"], len(aud(o1, "desk_saved")))
    _c, j4 = paper(own, o1)
    _c, j4b = paper(own, o2)
    after = (row(o1)["vendor"], len(aud(o1, "desk_saved")))
    sug = cp.suggest(db, OWNV, "", False, False)
    ck("I4 the own name (clinic_papers' own-name words) shows the grey line and offers Claude's supplier; Claude's own-name reading is not offered; nothing changes until Save",
       lambda: j4.get("own_line", "").startswith("This is your own name") and (j4.get("claude") or {}).get("vendor", {}).get("show") == "WALKV TRUE SUPPLIERS"
       and j4b.get("own_line") and "vendor" not in (j4b.get("claude") or {}) and before == after == (OWNV, 0)
       and sug and sug.get("kind") == "note" and "addressed to you" in sug.get("why", "") and sd.own_name(db, OWNV) and not sd.own_name(db, "WALKV TRUE SUPPLIERS")
       and "id=ownline" in tk and "use it" in tk,
       lambda: (j4.get("own_line"), j4.get("claude"), j4b.get("claude"), before, after))
    code, j = save(own, id=o1, dest="others", kind="bill", vendor="WALKV TRUE SUPPLIERS")
    ck("I4b ...and a person's Save with the offered supplier stores it (audited)", lambda: code == 200 and row(o1)["vendor"] == "WALKV TRUE SUPPLIERS" and aud(o1, "desk_fields"), lambda: (code, j))

    # ------------------------------------------------------------------ I5: Claude's reading beside each field
    x1 = mk("CX1", "WALKX FIRST TRADERS", bill_no="AB 12", total_amount=1000.4, bill_date="2031-06-05", created="2031-06-12 05:00:00")
    reading(x1, {"vendor": "Walkx First Traders Pvt Ltd", "bill_no": "ab12", "bill_date": "2031-06-07", "total_amount": 1000, "made_out_to": "clinic", "items": []})
    x2 = mk("CX2", "WALKX FIRST TRADERS", bill_no="AB 13", total_amount=1000, bill_date="2031-06-05", created="2031-06-12 05:00:00")
    reading(x2, {"vendor": "WALKZ OTHER COMPANY", "bill_no": "X-9", "bill_date": None, "date_as_read": "09/06/2031", "total_amount": 1500, "made_out_to": "doctor", "items": []})
    x3 = mk("CX3", "WALKX FIRST TRADERS", bill_no="AB 14", total_amount=1000, bill_date="2031-06-05", created="2031-06-12 05:00:00")
    reading(x3, {"vendor": "WALKZ OTHER COMPANY", "bill_no": "X-9", "bill_date": "2031-06-09", "total_amount": 1500}, ok=0)
    xp = mk("CXP", "WALKX FIRST TRADERS", status="approved", subgroup="personal", bill_no="AB 15", total_amount=1000, bill_date="2031-06-05", created="2031-06-12 05:00:00", approved_by="Walk")
    reading(xp, {"vendor": "WALKZ OTHER COMPANY", "bill_no": "X-9", "bill_date": "2031-06-09", "total_amount": 1500})
    xh = mk("CXH", "WALKX FIRST TRADERS", lane="pharmacy", bill_no="AB 16", total_amount=1000, bill_date="2031-06-05")
    reading(xh, {"vendor": "WALKZ OTHER COMPANY", "bill_no": "X-9", "bill_date": "2031-06-09", "total_amount": 1500})
    snap5 = [(row(b_)["vendor"], row(b_)["bill_no"], row(b_)["bill_date"], row(b_)["total_amount"], len(aud(b_, "desk_saved"))) for b_ in (x1, x2)]
    _c, k1 = paper(own, x1); _c, k2 = paper(own, x2); _c, k3 = paper(own, x3); cpo, kp = paper(own, xp)
    own.post("/desk/switch", data={"key": "desk.on", "on": "1", "back": "/"})
    cpm, kpm = paper(mgr, xp); cm2, km2 = paper(mgr, x2)
    snap5b = [(row(b_)["vendor"], row(b_)["bill_no"], row(b_)["bill_date"], row(b_)["total_amount"], len(aud(b_, "desk_saved"))) for b_ in (x1, x2)]
    c2_ = k2.get("claude") or {}
    try:
        lp = sd.claude_lines(db, sd._row(db, xp), sd.reading(db, xp), False)
        lh = sd.claude_lines(db, sd._row(db, xh), sd.reading(db, xh), True)
    except Exception as e:                                                 # noqa: BLE001
        lp = lh = repr(e)
    ck("I5 'Claude read' only where Claude's value differs (first two words, spaces/case, the date, the rupee): one line on CX1 (the date), four on CX2",
       lambda: set(k1.get("claude") or {"x": 1}) == {"date"} and k1["claude"]["date"] == {"show": "07-06-2031", "fill": "07-06-2031"}
       and set(c2_) == {"vendor", "bill_no", "date", "amount"} and c2_["vendor"]["show"] == "WALKZ OTHER COMPANY" and c2_["bill_no"]["fill"] == "X-9"
       and c2_["date"]["fill"] == "09-06-2031" and c2_["amount"]["fill"] == "1500" and "1,500" in c2_["amount"]["show"]
       and (k3.get("claude") == {}) and "id=cr_vendor" in tk and "id=cr_bill_no" in tk and "id=cr_date" in tk and "id=cr_amount" in tk,
       lambda: (k1.get("claude"), c2_, k3.get("claude")))
    ck("I5b never made_out_to; never a Personal paper to a manager (the owner sees it), never a pharmacy paper; nothing saved by looking",
       lambda: "doctor" not in json.dumps(c2_) and "made_out_to" not in json.dumps(c2_) and cpo == 200 and set(kp.get("claude") or {}) == {"vendor", "bill_no", "date", "amount"}
       and cpm == 403 and "claude" not in kpm and cm2 == 200 and set(km2.get("claude") or {}) == {"vendor", "bill_no", "date", "amount"}
       and lp == ({}, "") and lh == ({}, "") and snap5 == snap5b,
       lambda: (cpo, cpm, cm2, lp, lh, snap5 == snap5b))
    own.post("/desk/switch", data={"key": "desk.on", "on": "0", "back": "/"})

    # ------------------------------------------------------------------ I6: the bills list's lane words
    expect = {}
    for ln, word in (("clinic", "Clinic"), ("pharmacy", "Pharmacy"), ("lab_purchase", "NK Pathology"), ("owner_expense", "Personal expense"), ("other_doc", "Other document")):
        tg = "LW" + ln[:3].upper()
        expect["Z-2031-S5" + tg] = word
        mk(tg, "WALKL LANE WORDS", lane=ln, bill_no="LW-" + tg, bill_date="2031-06-03")
        expect["Z-2031-S5" + tg + "R"] = word
        mk(tg + "R", "WALKL LANE WORDS", lane=ln, status="rejected", bill_no="LW-" + tg + "R", bill_date="2031-06-03", reject_reason="walk")
    for kd, word in (("Consumable", "Clinic"), ("Pharmacy", "Pharmacy"), ("Lab", "NK Pathology"), ("Expense", "Personal expense"), ("Document", "Other document")):
        tg = "LWO" + kd[:3].upper()
        expect["Z-2031-S5" + tg] = word
        mk(tg, "WALKL LANE WORDS", lane=None, kind=kd, status="captured" if kd != "Consumable" else "draft", bill_no="LW-" + tg, bill_date="2031-06-03")
    tb = html(own, "/bills?q=Z-2031-S5LW")
    seen = {}
    for mm in re.finditer(r"(?s)<tr[^>]*><td>(Z-2031-S5LW[A-Z]+)(.*?)</tr>", tb):
        cells = re.findall(r"(?s)<td[^>]*>(.*?)</td>", "<td>" + mm.group(1) + mm.group(2))
        if len(cells) >= 7:
            seen[mm.group(1)] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cells[6])).strip()
    ck("I6 the bills list's Lane column: one short word per lane (Clinic, Pharmacy, NK Pathology, Personal expense, Other document) -- live, rejected and old rows alike",
       lambda: seen == expect, lambda: sorted((k[-6:], seen.get(k), v) for k, v in expect.items() if seen.get(k) != v))

    # ------------------------------------------------------------------ I8: no Claude read of a patient's paper
    pp = mk("PP1", "WALKP PATIENT PAPERS", subgroup="patient_paper", pdf=True)
    nn = mk("NN1", None, pdf=True)

    class _Stub:
        def __init__(self):
            self.calls = []

        def available(self, *a, **k):
            return True

        def read_bill(self, path, bid=None, db_path=None):
            self.calls.append(bid)
            return None

        def read(self, path, bid=None, db_path=None):
            self.calls.append(bid)
            return None
    stub, real_cl = _Stub(), m.CLAUDE
    m.CLAUDE = stub
    try:
        r_pp = m._s550_claude(pp, os.path.join(up, row(pp)["source_stored"]))
        r_nn = m._s550_claude(nn, os.path.join(up, row(nn)["source_stored"]))
    finally:
        m.CLAUDE = real_cl
    ck("I8a _s550_claude never sends a patient's paper (on any lane) to Claude; an ordinary clinic paper still goes (the stub only counts)",
       lambda: pp not in stub.calls and nn in stub.calls and r_pp is None and r_nn is None, lambda: (stub.calls, pp, nn))
    calls = []
    try:
        rr = import_file("claude_reread", os.path.join(appdir, "claude_reread.py"))
        CR = rr.CR
        saved = {k: getattr(CR, k) for k in ("state", "calls_today", "cap", "read")}
        CR.state, CR.calls_today, CR.cap = (lambda con: "on"), (lambda con: 0), (lambda con: 10 ** 6)
        CR.read = lambda path, bid=None, db_path=None: calls.append(bid)
        rr.the_app = lambda db_, up_: object()
        try:
            rr._run(argparse.Namespace(db=dbp, uploads=up, limit=0, gap=0, ids="%d,%d" % (pp, nn)))
            con = CR._db(dbp)
            tf = (rr.to_fill(rr.row(con, pp)), rr.to_fill(rr.row(con, nn)))
            con.close()
        finally:
            for k, v in saved.items():
                setattr(CR, k, v)
        rr_ok = under(rr.__file__, appdir) and under(CR.__file__, appdir)
    except Exception as e:                                                 # noqa: BLE001
        tf, rr_ok = repr(e), False
    ck("I8b claude_reread (from the scratch folder) never selects a patient's paper, nor fills one; an ordinary paper is still selected",
       lambda: rr_ok and pp not in calls and nn in calls and tf == (False, True), lambda: (rr_ok, calls, tf))

    # ------------------------------------------------------------------ sizes, and the scratch copy only
    t0 = time.time(); a_ = own.get("/desk"); t1 = time.time(); b_ = own.get("/desk/api/list"); t2 = time.time()
    first = ((b_.get_json(silent=True) or {}).get("papers") or [{}])[0].get("id")
    c_ = own.get("/desk/api/paper/%d" % first) if first else None
    t3 = time.time()
    print("SIZES desk %d B (%.0f ms) . list %d B (%.0f ms) . paper %d B (%.0f ms) . desk first load %.0f ms" % (
        len(a_.data), (t1 - t0) * 1000, len(b_.data), (t2 - t1) * 1000, len(c_.data) if c_ else 0, (t3 - t2) * 1000, (t3 - t0) * 1000))
    ck("T1 the desk's first load (page + list + one paper) is under 2 s", lambda: a_.status_code == 200 and (t3 - t0) < 2)
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
