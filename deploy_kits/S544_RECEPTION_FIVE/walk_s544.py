#!/usr/bin/env python3
"""walk_s544.py -- the S544_RECEPTION_FIVE walk: the app with the two built files on a COPY of a database (the live one on
the box, copied under the session's home and removed after; made-up rows dated 2031, made-up names, no person), through
the app's own doors, as the owner, a manager and a reception login.

    python3 walk_s544.py <dir with asset_register.py + clinic_papers.py> <assets.db | --fresh> [--expect-red]

GREEN/RED per check; exit 1 on any RED (--expect-red: exit 0 only if some check is RED -- the control on the live files)."""
import importlib.util, io, os, re, shutil, sqlite3, sys, tempfile

D = os.path.abspath(sys.argv[1])
SRC = sys.argv[2]
EXPECT_RED = "--expect-red" in sys.argv
R = []


def check(name, ok, detail=""):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)[:220]) if (detail and not ok) else ""))


def tiny_pdf(tag):
    body = ("%PDF-1.1\n%% " + tag + "\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 300]>>endobj\ntrailer<</Size 4/Root 1 0 R>>\n%%EOF\n")
    return body.encode()


def main():
    wd = tempfile.mkdtemp(prefix="s544_walk_", dir=os.path.expanduser("~"))
    try:
        for f in ("asset_register.py", "clinic_papers.py"):
            shutil.copy(os.path.join(D, f), wd)
        if os.path.exists(os.path.join(D, "scanner_widget.js")):
            shutil.copy(os.path.join(D, "scanner_widget.js"), wd)
        dbc = os.path.join(wd, "assets.db")
        if SRC != "--fresh":
            src = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(SRC), uri=True); dst = sqlite3.connect(dbc); src.backup(dst); src.close(); dst.close()
        up = os.path.join(wd, "uploads"); os.makedirs(up)
        os.environ["ASSETS_DB"] = dbc; os.environ["ASSETS_UPLOADS"] = up
        os.environ.pop("SARVAM_API_KEY", None)
        sys.path.insert(0, wd)
        spec = importlib.util.spec_from_file_location("asset_register", os.path.join(wd, "asset_register.py"))
        try:
            m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
        except Exception as e:                                                    # noqa: BLE001
            check("W1 the app imports with the built files", False, repr(e)); return
        cp = sys.modules.get("clinic_papers")
        check("W1 the app imports; clinic_papers S544.1 mounted", cp is not None and getattr(cp, "VERSION", "") == "S544.1", getattr(cp, "VERSION", None))

        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        for role, uname in (("owner", "walk_owner_2031"), ("manager", "walk_manager_2031")):
            if not db.execute("SELECT 1 FROM users WHERE role=? AND active=1", (role,)).fetchone():
                db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,?,1)",
                           (uname, uname.replace("_", " ").title(), role, "x"))
        db.commit()
        cols = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
        check("W2 the column pe_who exists after the app's own migration", "pe_who" in cols)
        check("W3 the asset category list reads Dr MK Clinic Equipment, not Medical Equipment",
              "Dr MK Clinic Equipment" in m.CATEGORIES and "Medical Equipment" not in m.CATEGORIES)
        db.execute("INSERT OR IGNORE INTO locations(name, visibility) VALUES('Made-Up Room 2031', 'general')")
        loc = db.execute("SELECT id FROM locations WHERE name='Made-Up Room 2031'").fetchone()[0]
        db.execute("INSERT INTO assets(name, location_id, category) VALUES('Made-Up X-ray Machine 2031', ?, 'Medical Equipment')", (loc,))
        db.commit()
        try:
            m.migrate(db); db.commit()
        except TypeError:
            pass
        left = db.execute("SELECT COUNT(*) FROM assets WHERE category='Medical Equipment'").fetchone()[0]
        moved = db.execute("SELECT COUNT(*) FROM assets WHERE category='Dr MK Clinic Equipment'").fetchone()[0]
        check("W4 every asset in Medical Equipment moves to Dr MK Clinic Equipment (none left behind)", left == 0 and moved >= 1, (left, moved))
        check("W5 the lane's words read Personal expense", m.LANES["owner_expense"][0] == "Personal expense", m.LANES["owner_expense"])
        check("W6 OFF keeps every login's own default (the owner's seed unchanged)", m.LANE_DEFAULTS.get("manoj") == "owner_expense", m.LANE_DEFAULTS.get("manoj"))

        ep = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()
        def client(role):
            c = m.app.test_client()
            u = db.execute("SELECT id FROM users WHERE role=? AND active=1 ORDER BY id LIMIT 1", (role,)).fetchone()
            with c.session_transaction() as s:
                s["uid"] = u[0]; s["epoch"] = ep[0] if ep else None
            return c
        own, man = client("owner"), client("manager")
        real_sso = m._sso_user
        recep_user = {"id": None, "username": "walkrecep2031", "display_name": "Walkrecep2031", "role": "reception", "active": 1}
        class Recep:                                                              # a scanning login (the portal's staff role)
            def __init__(self): self.c = m.app.test_client()
            def _go(self, fn, *a, **k):
                m._sso_user = lambda: recep_user
                try: return fn(*a, **k)
                finally: m._sso_user = real_sso
            def get(self, *a, **k): return self._go(self.c.get, *a, **k)
            def post(self, *a, **k): return self._go(self.c.post, *a, **k)
        rec = Recep()

        # --- F-891 first, on rows written straight into the copy (so the control on the old files reaches these checks)
        db.execute("INSERT OR IGNORE INTO vendors(name) VALUES('Made-Up Secret Vendor 2031')"); db.commit()
        vid = db.execute("SELECT id FROM vendors WHERE name='Made-Up Secret Vendor 2031'").fetchone()[0]
        def mkrow(stamp, lane, kind, status, vendor):
            cur = db.execute("INSERT INTO bills(kind, vendor, bill_date, total_amount, stamp_no, status, lane, subgroup, submitted_by) "
                             "VALUES(?,?,?,?,?,?,?,?,?)", (kind, vendor, "2031-01-05", 100.0, stamp, status, lane, "personal", "Walk"))
            db.commit(); return cur.lastrowid
        p_cl = mkrow("Z-2031-PC", "clinic", "Consumable", "approved", "Made-Up Secret Vendor 2031")
        p_ex = mkrow("Z-2031-PE", "owner_expense", "Expense", "captured", "Made-Up Secret Expense 2031")
        codes = [man.get(u).status_code for u in ("/bills/%d" % p_cl, "/bills/%d/file" % p_cl, "/bills/%d/edit" % p_cl)]
        check("F1 F-891: a manager is refused a Personal paper on the bill page, its file and its edit page", codes[0] == 403 and codes[2] == 403 and codes[1] in (403, 404), codes)
        r = man.post("/bills/%d/month" % p_cl, data={"bill_month": "2031-02"})
        check("F2 F-891: a manager's door that changes a bill (its month) refuses a Personal paper", r.status_code == 403, r.status_code)
        check("F3 F-891: the manager's bills list, searched by its stamp, does not carry it", not re.search(r"/bills/%d\b" % p_cl, man.get("/bills?q=Z-2031-PC").get_data(as_text=True)))
        check("F4 F-891: the supplier's purchase history does not show it to a manager", "Z-2031-PC" not in man.get("/vendors/%d" % vid).get_data(as_text=True))
        check("F5 the owner still opens it, finds it by its stamp and in the supplier's history",
              own.get("/bills/%d" % p_cl).status_code == 200 and re.search(r"/bills/%d\b" % p_cl, own.get("/bills?q=Z-2031-PC").get_data(as_text=True))
              and "Z-2031-PC" in own.get("/vendors/%d" % vid).get_data(as_text=True))
        t = man.get("/papers").get_data(as_text=True)
        check("F6 F-891: the papers page never shows a manager a Personal expense marked Personal", "Made-Up Secret Expense 2031" not in t)
        r = man.post("/papers/%d/pe_who" % p_ex, data={"who": "bhawna"})
        check("F7 F-891: a manager cannot mark whose a Personal paper is", r.status_code == 403, r.status_code)
        t = own.get("/papers").get_data(as_text=True)
        check("F8 the owner's papers page does show it in Personal expenses", "Made-Up Secret Expense 2031" in t and "Personal expenses<small>" in t)
        db.execute("DELETE FROM bills WHERE id IN (?,?)", (p_cl, p_ex)); db.commit()

        # --- switch OFF (as installed): the intake exactly as before, its words aside
        db.execute("DELETE FROM settings WHERE key='scan.lanes5'"); db.commit()
        t = rec.get("/intake").get_data(as_text=True)
        check("W7 OFF: reception's intake has no lane buttons; the old drop-down still offers every lane",
              "id=l5grid" not in t and 'value="owner_expense"' in t and "_challanSet" in t)
        t = own.get("/admin").get_data(as_text=True)
        check("W8 OFF: the owner's admin page shows the switch reading OFF", "reception's lane buttons" in t and re.search(r"lane buttons</h4>.*?Now: <b>OFF</b>", t, re.S) is not None)

        # --- the owner switches it ON
        r = own.post("/admin", data={"action": "set_scan_lanes5", "on": "1"})
        on = db.execute("SELECT value FROM settings WHERE key='scan.lanes5'").fetchone()
        check("W9 the owner's tap switches it ON (settings scan.lanes5 = on)", r.status_code in (302, 303) and on and on[0] == "on", (r.status_code, on and on[0]))
        r = rec.post("/admin", data={"action": "set_scan_lanes5", "on": "0"})
        check("W10 a reception login cannot touch the switch", r.status_code == 403 and (db.execute("SELECT value FROM settings WHERE key='scan.lanes5'").fetchone() or [None])[0] == "on", r.status_code)

        t = rec.get("/intake").get_data(as_text=True)
        lanes = re.findall(r'class=l5b data-lane="?([a-z_]+)', t)
        check("W11 ON: reception sees four lane buttons -- Clinic, Pharmacy, NK Pathology, Other document -- in that order",
              lanes == ["clinic", "pharmacy", "lab_purchase", "other_doc"], lanes)
        check("W12 ON: reception has no Personal expense, neither button nor drop-down option",
              "data-lane=owner_expense" not in t and 'value="owner_expense"' not in t)
        check("W13 ON: reception's words are Roman Hinglish; the CHALLAN button stays", "Yeh kaagaz kiska hai?" in t and "CHALLAN HAI?" in t and "mahina badlo" in t)
        t = own.get("/intake").get_data(as_text=True)
        lanes = re.findall(r'class=l5b data-lane="?([a-z_]+)', t)
        check("W14 ON: the owner sees the four and Personal expense, with Dr MK / Dr Bhawna, in English, and opens on Clinic",
              lanes == ["clinic", "pharmacy", "lab_purchase", "other_doc", "owner_expense"] and "data-who=bhawna" in t and "Whose paper is this?" in t
              and '"lane": "clinic"' in t, lanes)
        t = man.get("/intake").get_data(as_text=True)
        check("W15 ON: a manager (Shavez) sees Personal expense too", "data-lane=owner_expense" in t)

        def scan(cl, lane, tag, who=None, challan=False):
            data = {"lane": lane, "bill_month": "2031-01", "bill_scan": (io.BytesIO(tiny_pdf(tag)), "bill.pdf")}
            if who: data["pe_who"] = who
            if challan: data["challan"] = "1"
            rr = cl.post("/intake/scan_submit", data=data, content_type="multipart/form-data")
            j = rr.get_json(silent=True) or {}
            if j.get("id"):
                db.execute("UPDATE bills SET status=CASE WHEN COALESCE(lane,'clinic')='clinic' THEN 'draft' ELSE 'captured' END, dup_of=NULL, dup_flag=NULL, "
                           "dup_cand=NULL, dup_why=NULL, fp=NULL, fpc=NULL, vendor=? WHERE id=?", ("Made-Up " + tag, j["id"])); db.commit()
            return rr.status_code, j.get("id")
        sc, b_r = scan(rec, "owner_expense", "Reception Stale 2031")
        row = db.execute("SELECT lane FROM bills WHERE id=?", (b_r,)).fetchone()
        check("W16 ON: a reception scan sent as Personal expense (an old page) lands on the Clinic lane", sc == 200 and row and row[0] == "clinic", (sc, row and row[0]))
        sc, b_p = scan(rec, "pharmacy", "Pharma Walk 2031", challan=True)
        row = db.execute("SELECT lane, kind, doc_kind FROM bills WHERE id=?", (b_p,)).fetchone()
        check("W17 ON: reception's pharmacy challan is handed over as before (kind Challan, doc_kind challan)", row and tuple(row) == ("pharmacy", "Challan", "challan"), row and tuple(row))
        sc, b_bh = scan(own, "owner_expense", "Bhawna Walk 2031", who="bhawna")
        sc2, b_mk = scan(own, "owner_expense", "Mk Walk 2031")
        r1 = db.execute("SELECT lane, kind, status, pe_who FROM bills WHERE id=?", (b_bh,)).fetchone()
        r2 = db.execute("SELECT lane, pe_who FROM bills WHERE id=?", (b_mk,)).fetchone()
        check("W18 the owner's Personal expense for Dr Bhawna lands with pe_who bhawna (Expense, captured)",
              r1 and tuple(r1) == ("owner_expense", "Expense", "captured", "bhawna"), r1 and tuple(r1))
        check("W19 one with no name chosen lands with pe_who empty (= Dr MK)", r2 and tuple(r2) == ("owner_expense", None), r2 and tuple(r2))

        t = own.get("/papers").get_data(as_text=True)
        fold = t[t.find("Personal expenses<small>"):t.find("</details>", t.find("Personal expenses<small>"))] if "Personal expenses<small>" in t else ""
        bh_part = fold[fold.find(">Dr Bhawna</div>"):] if fold else ""
        check("W20 the papers page carries the Personal expenses fold; Dr Bhawna's paper under Dr Bhawna",
              bool(fold) and "Made-Up Bhawna Walk 2031" in bh_part and "Made-Up Mk Walk 2031" in fold[:fold.find(">Dr Bhawna</div>")], len(fold))
        t = man.get("/papers").get_data(as_text=True)
        check("W21 a manager (Shavez) sees the fold too", "Personal expenses<small>" in t)
        t = own.get("/papers/%d" % b_mk).get_data(as_text=True)
        check("W22 a personal expense's own page asks whose it is, and keeps its warranty card", "Personal expense — whose?" in t and "Keep the warranty" in t)
        r = man.post("/papers/%d/pe_who" % b_mk, data={"who": "bhawna"})
        v = db.execute("SELECT pe_who FROM bills WHERE id=?", (b_mk,)).fetchone()[0]
        a = db.execute("SELECT COUNT(*) FROM bill_audit WHERE bill_id=? AND action='pe_who'", (b_mk,)).fetchone()[0]
        check("W23 a manager's tap sets Dr Bhawna, with an audit line", r.status_code in (302, 303) and v == "bhawna" and a == 1, (r.status_code, v, a))
        own.post("/papers/%d/pe_who" % b_mk, data={"who": "mk"})
        check("W24 the owner's tap sets it back to Dr MK (empty)", db.execute("SELECT pe_who FROM bills WHERE id=?", (b_mk,)).fetchone()[0] is None)
        r = rec.post("/papers/%d/pe_who" % b_mk, data={"who": "bhawna"})
        check("W25 a reception login cannot set whose expense", r.status_code in (302, 403) and db.execute("SELECT pe_who FROM bills WHERE id=?", (b_mk,)).fetchone()[0] is None, r.status_code)
        r = own.post("/papers/%d/pe_who" % b_r, data={"who": "bhawna"})
        check("W26 a paper that is not a personal expense is refused, unchanged", db.execute("SELECT pe_who FROM bills WHERE id=?", (b_r,)).fetchone()[0] is None)

        # --- F-891: a Personal paper on the bill doors
        db.execute("UPDATE bills SET subgroup='personal' WHERE id=?", (b_r,)); db.commit()
        stamp = db.execute("SELECT stamp_no FROM bills WHERE id=?", (b_r,)).fetchone()[0]
        codes = [man.get(u).status_code for u in ("/bills/%d" % b_r, "/bills/%d/file" % b_r, "/bills/%d/thumb" % b_r)]
        check("W27 F-891: a manager is refused a Personal paper on the bill page, its file and its picture", codes == [403, 403, 403], codes)
        lst = man.get("/bills?q=" + stamp).get_data(as_text=True)
        check("W28 F-891: the manager's bills list, searched by its stamp, does not carry it", not re.search(r"/bills/%d\b" % b_r, lst))
        check("W29 the owner still opens it, and finds it by its stamp", own.get("/bills/%d" % b_r).status_code == 200 and re.search(r"/bills/%d\b" % b_r, own.get("/bills?q=" + stamp).get_data(as_text=True)))
        t = own.get("/papers").get_data(as_text=True)
        check("W30 the owner's stand row reads Personal expenses, Dr MK and Dr Bhawna counted", "Personal expenses" in t and "Dr Bhawna" in t)
        t = own.get("/bills/%d" % b_bh).get_data(as_text=True)
        check("W31 the bill page names the lane Personal expense", "Personal expense" in t and "Dr MK expense" not in t)

        # --- OFF again: the intake as before
        own.post("/admin", data={"action": "set_scan_lanes5", "on": "0"})
        t = rec.get("/intake").get_data(as_text=True)
        check("W32 switched OFF again: reception's intake is the old one", "id=l5grid" not in t and 'value="owner_expense"' in t)
        sc, b_o = scan(rec, "owner_expense", "Off Walk 2031")
        check("W33 OFF: the server takes the lane as before", db.execute("SELECT lane FROM bills WHERE id=?", (b_o,)).fetchone()[0] == "owner_expense")
        db.close()
    finally:
        shutil.rmtree(wd, ignore_errors=True)


try:
    main()
except Exception as _e:                                                          # noqa: BLE001
    check("the walk ran to its end", False, repr(_e))
red = R.count(False)
print("%d checks, %d green, %d red" % (len(R), len(R) - red, red))
if EXPECT_RED:
    sys.exit(0 if red else 1)
sys.exit(1 if red else 0)
