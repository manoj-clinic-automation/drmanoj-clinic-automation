#!/usr/bin/env python3
"""walk_s530.py -- the S530_PAPERS_SECTIONS walk: the app with the built clinic_papers.py on a COPY of the live database
(made under the session's home, removed after; made-up rows only, dated 2031, no person), as the owner and as a manager.

    python3 walk_s530.py <dir with clinic_papers.py> <live asset_register.py> <live assets.db> [--expect-red]

GREEN/RED per check; exit 1 on any RED (--expect-red: exit 0 only if some check is RED -- the control on the live file)."""
import importlib.util, os, shutil, sqlite3, sys, tempfile

D, APY, LIVEDB = [os.path.abspath(a) for a in sys.argv[1:4]]
EXPECT_RED = "--expect-red" in sys.argv
R = []


def check(name, ok, detail=""):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)) if detail else ""))


def main():
    wd = tempfile.mkdtemp(prefix="s530_walk_", dir=os.path.expanduser("~"))
    try:
        shutil.copy(os.path.join(D, "clinic_papers.py"), wd); shutil.copy(APY, os.path.join(wd, "asset_register.py"))
        dbc = os.path.join(wd, "assets.db")
        src = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True); dst = sqlite3.connect(dbc); src.backup(dst); src.close()
        dst.row_factory = sqlite3.Row
        # made-up rows, dated far in the future, no person: three clinic drafts (two a same-vendor-number-amount pair), one
        # other-document paper with resume words, one clinic paper from a hardware shop, one addressed to the clinic itself
        def mk(stamp, lane, status, vendor, bill_no, total, items, kind="Consumable"):
            cur = dst.execute("INSERT INTO bills(kind,vendor,bill_no,bill_date,total_amount,source_stored,stamp_no,status,lane,created_at,bill_month) "
                              "VALUES(?,?,?,?,?,?,?,?,?,?,?)", (kind, vendor, bill_no, "2031-01-15", total, "", stamp, status, lane, "2031-01-15 10:00:00", "2031-01"))
            bid = cur.lastrowid
            for it in items:
                dst.execute("INSERT INTO bill_items(bill_id,item_name) VALUES(?,?)", (bid, it))
            return bid
        before_drafts_grouped = dst.execute("SELECT COUNT(*) FROM bills WHERE COALESCE(lane,'clinic')='clinic' AND status='draft' AND COALESCE(subgroup,'')<>''").fetchone()[0]
        b_proc = mk("Z-9001", "clinic", "draft", "Made-Up Surgicals", "MU-1", 1234.0, ["roller bandage", "cotton"])
        b_dupA = mk("Z-9002", "clinic", "draft", "Made-Up Twice Traders", "MU-77", 500.0, ["tape"])
        b_dupB = mk("Z-9003", "clinic", "draft", "Made-Up Twice Traders", "MU-77", 500.0, ["tape"])
        b_res = mk("Z-9004", "other_doc", "captured", None, None, None, ["curriculum vitae", "qualification b.sc nursing", "experience two years", "career objective"], kind="Document")
        b_con = mk("Z-9005", "clinic", "draft", "Made-Up Hardware & Paints", "MU-9", 6850.0, ["cement 4 bag", "putty", "labour"])
        b_own = mk("Z-9006", "clinic", "draft", "Dr. Manoj Agarwal", None, None, [])
        b_mk = mk("Z-9007", "owner_expense", "captured", "Made-Up Electricals", "MU-3", 9000.0, ["inverter battery"], kind="Expense")
        dst.commit(); dst.close()
        os.environ["ASSETS_DB"] = dbc; os.environ["ASSETS_UPLOADS"] = os.path.join(wd, "uploads"); os.makedirs(os.environ["ASSETS_UPLOADS"])
        sys.path.insert(0, wd)
        spec = importlib.util.spec_from_file_location("asset_register", os.path.join(wd, "asset_register.py"))
        try:
            m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
        except Exception as e:                                                    # noqa: BLE001
            check("W1 the app imports with the built clinic_papers.py", False, repr(e)[:200]); return
        cp = sys.modules.get("clinic_papers")
        check("W1 the app imports and mounts clinic_papers %s" % (getattr(cp, "VERSION", "?") if cp else "?"), cp is not None and getattr(cp, "VERSION", "") == "S530.1")
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        after = db.execute("SELECT COUNT(*) FROM bills WHERE COALESCE(lane,'clinic')='clinic' AND status='draft' AND COALESCE(subgroup,'')<>''").fetchone()[0]
        healed = db.execute("SELECT COUNT(*) FROM bill_audit WHERE action='d710_accepted' AND who=''").fetchone()[0]
        check("W2 the heal at start: grouped clinic drafts %d -> %d, %d accepted by the system (idempotent on the next start)" % (before_drafts_grouped, after, healed), after <= 0 or healed > 0)
        # a second heal changes nothing
        a2, h2 = cp.heal(db) if hasattr(cp, "heal") else (-1, -1)
        check("W3 a second heal accepts nothing more", a2 == 0, "accepted %d held %d" % (a2, h2))
        db.close()
        def client(role):
            c = m.app.test_client()
            db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
            u = db.execute("SELECT id FROM users WHERE role=? AND active=1 ORDER BY id LIMIT 1", (role,)).fetchone()
            ep = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone(); db.close()
            if not u:
                db = sqlite3.connect(dbc); from werkzeug.security import generate_password_hash
                db.execute("INSERT INTO users(username,display_name,role,password_hash,active) VALUES(?,?,?,?,1)", ("s530" + role, "S530 " + role, role, generate_password_hash("x" * 12))); db.commit()
                u = db.execute("SELECT id FROM users WHERE username=?", ("s530" + role,)).fetchone(); db.close()
            with c.session_transaction() as s:
                s["uid"] = u[0]; s["epoch"] = ep[0] if ep else None
            return c
        own, mgr = client("owner"), client("manager")
        r = own.get("/papers"); t = r.get_data(as_text=True)
        check("W4 /papers (owner): the page, the new title, the fold 'Where each paper stands'", r.status_code == 200 and "Papers to sort" in t and "Where each paper stands" in t, r.status_code)
        check("W5 /papers lists the Other-document paper (a resume) with its suggestion", "Z-9004" in t and "Looks like <b>Resumes</b>" in t)
        check("W6 /papers suggests Construction work for the hardware shop's slip", "Z-9005" in t and "Looks like <b>Construction work</b>" in t)
        check("W7 /papers says the paper addressed to the clinic is not a supplier's bill", "Z-9006" in t and "addressed to you" in t)
        r = mgr.get("/papers"); t2 = r.get_data(as_text=True)
        check("W8 /papers (manager): no owner's fold, the list as the owner's", r.status_code == 200 and "Where each paper stands" not in t2 and "Z-9004" in t2)
        r = own.get("/papers/%d" % b_proc); t = r.get_data(as_text=True)
        check("W9 a clinic draft's page: the consumables fold and the four sections, Personal shown to the owner", r.status_code == 200 and "Clinic consumables" in t and 'value="construction"' in t and 'value="personal"' in t and "and accepts the paper" in t)
        r = mgr.get("/papers/%d" % b_proc); t = r.get_data(as_text=True)
        check("W10 the same page for the manager: no Personal", r.status_code == 200 and 'value="construction"' in t and 'value="personal"' not in t)
        # sorted = accepted
        r = own.post("/bills/%d/subgroup" % b_proc, data={"subgroup": "procedure", "back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        b = db.execute("SELECT status, subgroup, approved_by FROM bills WHERE id=?", (b_proc,)).fetchone()
        check("W11 one tap on a clinic draft: sorted AND accepted (status approved, by the person)", b["status"] == "approved" and b["subgroup"] == "procedure" and b["approved_by"], dict(b))
        check("W12 the audit carries d710_accepted", db.execute("SELECT COUNT(*) FROM bill_audit WHERE bill_id=? AND action='d710_accepted'", (b_proc,)).fetchone()[0] == 1)
        check("W13 the vendor book gained the supplier", db.execute("SELECT COUNT(*) FROM vendors WHERE name=?", ("Made-Up Surgicals",)).fetchone()[0] == 1)
        db.close()
        own.post("/bills/%d/subgroup" % b_dupA, data={"subgroup": "others", "back": "/papers"}, follow_redirects=True)
        r = own.post("/bills/%d/subgroup" % b_dupB, data={"subgroup": "others", "back": "/papers"}, follow_redirects=True); t = r.get_data(as_text=True)
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        a, bb = db.execute("SELECT status FROM bills WHERE id=?", (b_dupA,)).fetchone()[0], db.execute("SELECT status, subgroup FROM bills WHERE id=?", (b_dupB,)).fetchone()
        check("W14 the duplicate rule holds: the first accepted, the second sorted but NOT accepted and said so", a == "approved" and bb["status"] == "draft" and bb["subgroup"] == "others" and "NOT accepted" in t, "%s / %s" % (a, dict(bb)))
        db.close()
        r = own.post("/bills/%d/subgroup" % b_res, data={"subgroup": "resume", "back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); b = db.execute("SELECT status, subgroup FROM bills WHERE id=?", (b_res,)).fetchone(); db.close()
        check("W15 an Other-document paper takes a section and keeps its status", b[0] == "captured" and b[1] == "resume", b)
        r = own.post("/bills/%d/subgroup" % b_res, data={"subgroup": "procedure", "back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); b = db.execute("SELECT subgroup FROM bills WHERE id=?", (b_res,)).fetchone(); db.close()
        check("W16 a consumable group is refused off the clinic lane", b[0] == "resume" and "not on the clinic lane" in r.get_data(as_text=True))
        r = mgr.post("/bills/%d/subgroup" % b_own, data={"subgroup": "personal", "back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); b = db.execute("SELECT subgroup, status FROM bills WHERE id=?", (b_own,)).fetchone(); db.close()
        check("W17 Personal refused to the manager", b[0] is None and "alone" in r.get_data(as_text=True), b)
        r = own.post("/bills/%d/subgroup" % b_own, data={"subgroup": "personal", "back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); b = db.execute("SELECT subgroup, status FROM bills WHERE id=?", (b_own,)).fetchone(); db.close()
        check("W18 Personal set by the owner; a clinic draft so sorted is accepted too", b[0] == "personal" and b[1] == "approved", b)
        check("W19 the manager cannot open a Personal paper", mgr.get("/papers/%d" % b_own).status_code == 403)
        r = own.post("/bills/%d/subgroup" % b_con, data={"subgroup": "construction", "back": "/papers"}, follow_redirects=True)
        r = own.post("/bills/%d/subgroup" % b_mk, data={"subgroup": "misc", "back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); b = db.execute("SELECT subgroup, status FROM bills WHERE id=?", (b_mk,)).fetchone(); db.close()
        check("W20 a Dr MK expense paper takes a section and keeps its status", b[0] == "misc" and b[1] == "captured", b)
        r = own.get("/papers/month?ym=2031-01"); t = r.get_data(as_text=True)
        check("W21 the month page: 'Other sections' with Construction work (money) and Resumes, Personal for the owner", r.status_code == 200 and "Other sections" in t and "Construction work" in t and "clinic / MK not decided" in t and "Resumes" in t and "Personal" in t)
        import re
        tot = re.search(r"All clinic consumables.*?<td class=r><b>([^<]+)</b>", t, re.S)
        check("W22 the consumables total leaves the construction slip out (2,234 = 1,234 + 500 + 500; not 9,084)", tot and "2,234" in tot.group(1), tot.group(1) if tot else "no total")
        r = mgr.get("/papers/month?ym=2031-01"); t = r.get_data(as_text=True)
        check("W23 the manager's month page has no Personal row", r.status_code == 200 and "Other sections" in t and "Personal" not in t)
        r = own.get("/papers/month?ym=2031-01&g=construction"); t = r.get_data(as_text=True)
        check("W24 one section's list opens", r.status_code == 200 and "Z-9005" in t)
        check("W25 the manager cannot list Personal", "Z-9006" not in mgr.get("/papers/month?ym=2031-01&g=personal").get_data(as_text=True))
        for path, name in (("/papers/month", "the month page"), ("/papers/%d/join" % b_proc, "the join page"), ("/bills/%d" % b_proc, "the bill page"), ("/renewals", "renewals"), ("/purchases", "purchases"), ("/bills", "the bills list"), ("/healthz", "healthz")):
            rr = own.get(path)
            check("W26 %s still answers" % name, rr.status_code == 200, rr.status_code)
        live = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True)
        check("W27 the LIVE database was not written (no Z-9xxx row, no d710 audit)", live.execute("SELECT COUNT(*) FROM bills WHERE stamp_no LIKE 'Z-9%'").fetchone()[0] == 0 and live.execute("SELECT COUNT(*) FROM bill_audit WHERE action LIKE 'd710%'").fetchone()[0] == 0)
        live.close()
    finally:
        shutil.rmtree(wd, ignore_errors=True)


main()
red = R.count(False)
print("%d checks: %d green, %d red" % (len(R), len(R) - red, red))
sys.exit((0 if red else 1) if EXPECT_RED else (1 if red else 0))
