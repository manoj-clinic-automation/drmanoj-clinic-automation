#!/usr/bin/env python3
"""walk_s531.py -- the S531_CHALLAN_FLOW walk: the app with the three built files on a COPY of the live database (under the
session's home, removed after; made-up rows dated 2031, no person), through the app's own doors; then, with --browser, the
intake page in headless Chromium against a live copy of the app: the CHALLAN button, the widget's snapshot of the fields
at Save, the row that lands.

    python3 walk_s531.py <dir with the three built files> <live assets.db> [--browser] [--expect-red]

GREEN/RED per check; exit 1 on any RED (--expect-red: exit 0 only if some check is RED -- the control on the live files)."""
import importlib.util, io, os, shutil, sqlite3, sys, tempfile, threading, time

D, LIVEDB = [os.path.abspath(a) for a in sys.argv[1:3]]
EXPECT_RED = "--expect-red" in sys.argv
BROWSER = "--browser" in sys.argv
R = []


def check(name, ok, detail=""):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)) if detail else ""))


def tiny_pdf():
    return (b"%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 300]>>endobj\nxref\n0 4\n0000000000 65535 f \n"
            b"0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF\n")


def main():
    wd = tempfile.mkdtemp(prefix="s531_walk_", dir=os.path.expanduser("~"))
    try:
        for f in ("asset_register.py", "clinic_papers.py", "scanner_widget.js"):
            shutil.copy(os.path.join(D, f), wd)
        dbc = os.path.join(wd, "assets.db")
        src = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True); dst = sqlite3.connect(dbc); src.backup(dst); src.close(); dst.close()
        up = os.path.join(wd, "uploads"); os.makedirs(up)
        os.environ["ASSETS_DB"] = dbc; os.environ["ASSETS_UPLOADS"] = up
        sys.path.insert(0, wd)
        spec = importlib.util.spec_from_file_location("asset_register", os.path.join(wd, "asset_register.py"))
        try:
            m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
        except Exception as e:                                                    # noqa: BLE001
            check("P1 the app imports with the three built files", False, repr(e)[:200]); return
        cp = sys.modules.get("clinic_papers")
        check("P1 the app imports; clinic_papers %s mounted" % getattr(cp, "VERSION", "?"), cp is not None and getattr(cp, "VERSION", "") == "S531.1")
        db = sqlite3.connect(dbc); cols = {r[1] for r in db.execute("PRAGMA table_info(bills)")}; db.close()
        check("P2 the three columns exist after the app's own migration", {"doc_kind", "challan_state", "challan_of"} <= cols)
        def client(role):
            c = m.app.test_client()
            db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
            u = db.execute("SELECT id FROM users WHERE role=? AND active=1 ORDER BY id LIMIT 1", (role,)).fetchone()
            ep = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone(); db.close()
            with c.session_transaction() as s:
                s["uid"] = u[0]; s["epoch"] = ep[0] if ep else None
            return c
        own = client("owner")
        r = own.get("/intake"); t = r.get_data(as_text=True)
        check("P3 the intake carries the one CHALLAN button, its field and its script", r.status_code == 200 and "CHALLAN HAI?" in t and 'id=challan_basic' in t and "_challanSet" in t and "Sirf tab dabao" in t, r.status_code)
        def scan(lane, challan, vendor=None):
            data = {"lane": lane, "bill_month": "2031-01", "bill_scan": (io.BytesIO(tiny_pdf()), "bill.pdf")}
            if challan: data["challan"] = "1"
            if vendor: data["vendor"] = vendor
            rr = own.post("/intake/scan_submit", data=data, content_type="multipart/form-data")
            j = rr.get_json() or {}
            # the walk's made-up PDFs are byte-identical, so the app's own capture guard marks every one after the first a
            # duplicate (rightly). Un-mark the made-up row so the flow under test can be walked; a real scan is never identical.
            if j.get("id"):
                dbu = sqlite3.connect(dbc)
                dbu.execute("UPDATE bills SET status=CASE WHEN COALESCE(lane,'clinic')='clinic' THEN 'draft' ELSE 'captured' END, dup_of=NULL, dup_flag=NULL, dup_cand=NULL, dup_why=NULL, fp=NULL, fpc=NULL WHERE id=?", (j["id"],))
                dbu.commit(); dbu.close()
            return rr.status_code, j
        sc, j1 = scan("clinic", True, "Made-Up Yuvika Surgicals")
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        b1 = db.execute("SELECT * FROM bills WHERE id=?", (j1.get("id"),)).fetchone()
        check("P4 a clinic challan lands: doc_kind challan, awaiting, status draft, the reply says challan", sc == 200 and b1 and b1["doc_kind"] == "challan" and b1["challan_state"] == "awaiting" and b1["status"] == "draft" and j1.get("challan") is True, dict(j1))
        check("P5 the audit carries 'challan'", db.execute("SELECT COUNT(*) FROM bill_audit WHERE bill_id=? AND action='challan'", (b1["id"],)).fetchone()[0] == 1)
        sc, j2 = scan("pharmacy", True, "Made-Up Pharma Distributors")
        b2 = db.execute("SELECT * FROM bills WHERE id=?", (j2.get("id"),)).fetchone()
        check("P6 a pharmacy challan is handed over as kind 'Challan' (not Pharmacy), captured, doc_kind challan", b2 and b2["kind"] == "Challan" and b2["status"] == "captured" and b2["doc_kind"] == "challan", dict(b2) if b2 else None)
        sc, j3 = scan("clinic", False, "Made-Up Plain Traders")
        b3 = db.execute("SELECT * FROM bills WHERE id=?", (j3.get("id"),)).fetchone()
        check("P7 a plain bill is untouched: no doc_kind, the reply says challan false", b3 and b3["doc_kind"] is None and j3.get("challan") is False)
        # the register's own view of pharmacy scans (the Sanjeevni side's query shape) does not see the challan
        n_ph = db.execute("SELECT COUNT(*) FROM bills WHERE kind='Pharmacy' AND status='captured' AND id=?", (b2["id"],)).fetchone()[0]
        check("P8 the Sanjeevni side's query (kind='Pharmacy' AND captured) does not take the pharmacy challan", n_ph == 0)
        # age the clinic challan 20 days back so it turns amber
        db.execute("UPDATE bills SET bill_date=date('now','-20 days'), created_at=datetime('now','-20 days'), total_amount=4200 WHERE id=?", (b1["id"],)); db.commit(); db.close()
        r = own.get("/intake/slip/%d" % b1["id"]); t = r.get_data(as_text=True)
        check("P9 the slip says CHALLAN", r.status_code == 200 and "CHALLAN — bill baad mein aayega" in t)
        r = own.get("/intake/slip/%d" % b3["id"]); check("P10 a plain bill's slip does not", "bill baad mein aayega" not in r.get_data(as_text=True))
        r = own.get("/papers/challans"); t = r.get_data(as_text=True)
        check("P11 Bills awaited lists both challans; the pharmacy one 'handed to the Sanjeevni side'; the 20-day one amber", r.status_code == 200 and b1["stamp_no"] in t and b2["stamp_no"] in t and "handed to the Sanjeevni side" in t and 'style="background:#fff4e0"' in t)
        r = own.get("/papers"); t = r.get_data(as_text=True)
        sort_part = t.split("</details>")[-1] if "Where each paper stands" in t else t      # the cards come after the owner's fold
        check("P12 the to-sort list does not carry the challan; its head links Bills awaited (2)", b1["stamp_no"] not in sort_part and "Bills awaited (2)" in t and "Challans" in t,
              "%s / %s / %s / %s" % (b1["stamp_no"] not in sort_part, "Bills awaited (2)" in t, "Challans" in t, sort_part[max(0, sort_part.find(b1["stamp_no"]) - 200):sort_part.find(b1["stamp_no"]) + 40].replace("\n", " ") if b1["stamp_no"] in sort_part else ""))
        # the bill comes: same supplier
        sc, j4 = scan("clinic", False, "Made-Up Yuvika Surgicals")
        db = sqlite3.connect(dbc); db.execute("UPDATE bills SET total_amount=4180, bill_date=date('now') WHERE id=?", (j4["id"],)); db.commit(); db.close()
        r = own.get("/papers"); t = r.get_data(as_text=True)
        check("P13 the to-sort card of the new bill says it may be the bill for the challan", "This may be the bill for challan <b>%s</b>" % b1["stamp_no"] in t)
        r = own.get("/papers/%d" % j4["id"]); t = r.get_data(as_text=True)
        check("P14 the bill's page offers the join with one button", r.status_code == 200 and "The bill for a challan?" in t and "Yes — join %s into this bill" % b1["stamp_no"] in t)
        r = own.post("/papers/%d/join" % j4["id"], data={"page": str(b1["id"]), "back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row; c1 = db.execute("SELECT * FROM bills WHERE id=?", (b1["id"],)).fetchone(); db.close()
        check("P15 the join: the challan is a page of the bill, state joined, remembers its bill", c1["status"] == "rejected" and c1["page_of"] == j4["id"] and c1["challan_state"] == "joined" and c1["challan_of"] == j4["id"], dict(c1))
        r = own.get("/papers/challans"); t = r.get_data(as_text=True)
        check("P16 Bills awaited no longer lists it; it is under closed and deleted ones", b1["stamp_no"] not in t.split("Closed and deleted")[0] and b1["stamp_no"] in t.split("Closed and deleted")[-1])
        r = own.get("/papers/%d" % b1["id"]); t = r.get_data(as_text=True)
        check("P17 the challan's own page offers Delete after the join", "Delete the challan %s" % b1["stamp_no"] in t)
        r = own.post("/papers/%d/unjoin" % j4["id"], data={"back": "/papers"}, follow_redirects=True)
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row; c1 = db.execute("SELECT * FROM bills WHERE id=?", (b1["id"],)).fetchone(); db.close()
        check("P18 undo the join: the challan is awaiting again", c1["status"] == "draft" and c1["page_of"] is None and c1["challan_state"] == "awaiting" and c1["challan_of"] is None, dict(c1))
        r = own.post("/papers/challans/%d/delete" % b1["id"], data={"back": "/papers/challans"}, follow_redirects=True)
        check("P19 delete before the join is refused", "only after it is joined" in r.get_data(as_text=True))
        own.post("/papers/%d/join" % j4["id"], data={"page": str(b1["id"]), "back": "/papers"}, follow_redirects=True)
        # give the challan a real file so the move can be seen
        db = sqlite3.connect(dbc); db.execute("UPDATE bills SET source_stored='bill_walk_challan.pdf' WHERE id=?", (b1["id"],)); db.commit(); db.close()
        open(os.path.join(up, "bill_walk_challan.pdf"), "wb").write(tiny_pdf())
        r = own.post("/papers/challans/%d/delete" % b1["id"], data={"back": "/papers/challans"}, follow_redirects=True)
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row; c1 = db.execute("SELECT * FROM bills WHERE id=?", (b1["id"],)).fetchone(); db.close()
        moved = os.path.exists(os.path.join(up, "_deleted_challans", "bill_walk_challan.pdf")) and not os.path.exists(os.path.join(up, "bill_walk_challan.pdf"))
        check("P20 delete after the join: state deleted, the reason names the bill, the file MOVED (never removed), the number stays", c1["challan_state"] == "deleted" and (c1["reject_reason"] or "").startswith("challan — bill came") and moved and c1["stamp_no"] == b1["stamp_no"], dict(c1))
        sc, j5 = scan("clinic", True, "Made-Up Sample Giver")
        r = own.post("/papers/challans/%d/close" % j5["id"], data={"back": "/papers/challans"}, follow_redirects=True)
        db = sqlite3.connect(dbc); st = db.execute("SELECT challan_state FROM bills WHERE id=?", (j5["id"],)).fetchone()[0]; db.close()
        check("P21 'Bill nahi aayega' closes a challan", st == "closed")
        r = own.get("/papers/month?ym=2031-01"); t = r.get_data(as_text=True)
        check("P22 the month page does not count a challan under consumables", r.status_code == 200 and "Made-Up Sample Giver" not in t)
        for path, name in (("/papers", "papers"), ("/papers/month", "month"), ("/bills", "bills"), ("/bills/%d" % b1["id"], "the challan's bill page"), ("/renewals", "renewals"), ("/purchases", "purchases"), ("/healthz", "healthz"), ("/scan/widget.js", "the widget")):
            rr = own.get(path); check("P23 %s still answers" % name, rr.status_code == 200, rr.status_code)
        check("P24 the served widget carries S531 and S523", b"S531" in own.get("/scan/widget.js").data and b"S523" in own.get("/scan/widget.js").data)
        live = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True)
        check("P25 the LIVE database was not written", live.execute("SELECT COUNT(*) FROM bills WHERE vendor LIKE 'Made-Up%'").fetchone()[0] == 0)
        live.close()
        if BROWSER:
            browser_walk(m, dbc, up, wd)
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def browser_walk(m, dbc, up, wd):
    """The intake in headless Chromium against this very app (a dev server in a thread): the button, the widget's snapshot."""
    import asyncio, socket
    from werkzeug.security import generate_password_hash
    from playwright.async_api import async_playwright
    db = sqlite3.connect(dbc)
    db.execute("INSERT OR IGNORE INTO users(username,display_name,role,password_hash,active) VALUES('s531walk','S531 walk','owner',?,1)", (generate_password_hash("s531-walk-only"),)); db.commit(); db.close()
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    th = threading.Thread(target=lambda: m.app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True), daemon=True); th.start()
    time.sleep(1.5)
    from PIL import Image
    img = Image.new("RGB", (1600, 1200), (120, 84, 50)); img.paste(Image.new("RGB", (700, 1000), (250, 250, 245)), (450, 100))
    shot = os.path.join(wd, "made_up_bill.jpg"); img.save(shot, quality=85)
    U = "http://127.0.0.1:%d" % port

    async def go():
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 390, "height": 844})
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(U + "/login"); await pg.fill("input[name=username]", "s531walk"); await pg.fill("input[name=password]", "s531-walk-only"); await pg.click("button")
            await pg.goto(U + "/intake"); await pg.wait_for_timeout(800)
            ok = await pg.evaluate("!!document.getElementById('scanroot') && !!document.getElementById('challan_btn') && !!document.getElementById('cam')")
            check("B1 the intake renders with the widget and the CHALLAN button", ok)
            await pg.click("#challan_btn"); await pg.wait_for_timeout(100)
            st = await pg.evaluate("[window.SCANNER_CONFIG.uploadFields.challan, document.getElementById('lane_line').textContent, document.getElementById('challan_btn').textContent, document.getElementById('challan_basic').value]")
            check("B2 one tap: the field is 1, the line says CHALLAN, the button turns", st[0] == "1" and st[1].endswith("· CHALLAN") and "CHALLAN" in st[2] and st[3] == "1", st)
            await pg.set_input_files("#cam", [shot]); await pg.wait_for_timeout(2500)
            n = await pg.evaluate("document.querySelectorAll('#pages img').length")
            check("B3 a chosen photo became a page", n == 1, n)
            await pg.click("#savebtn"); await pg.wait_for_timeout(200)
            after = await pg.evaluate("[window.SCANNER_CONFIG.uploadFields.challan || null, document.getElementById('challan_btn').textContent]")
            check("B4 right after Save the button is back to normal and the field is clear", after[0] is None and "CHALLAN HAI?" in after[1], after)
            for _ in range(40):
                okup = await pg.evaluate("(document.getElementById('stampbox')||{}).textContent || ''")
                if "kaagaz par likho" in okup or "B-" in okup or "#" in okup: break
                await pg.wait_for_timeout(250)
            dbx = sqlite3.connect(dbc); dbx.row_factory = sqlite3.Row
            row = dbx.execute("SELECT doc_kind, challan_state, lane FROM bills WHERE submitted_by='S531 walk' ORDER BY id DESC LIMIT 1").fetchone(); dbx.close()
            check("B5 the upload that was queued BEFORE the reset still landed as a challan (the widget's snapshot)", row and row["doc_kind"] == "challan" and row["challan_state"] == "awaiting", dict(row) if row else None)
            await pg.set_input_files("#cam", [shot]); await pg.wait_for_timeout(2500); await pg.click("#savebtn")
            for _ in range(40):
                await pg.wait_for_timeout(250)
                dbx = sqlite3.connect(dbc); nrows = dbx.execute("SELECT COUNT(*) FROM bills WHERE submitted_by='S531 walk'").fetchone()[0]; dbx.close()
                if nrows >= 2: break
            dbx = sqlite3.connect(dbc); dbx.row_factory = sqlite3.Row
            row2 = dbx.execute("SELECT doc_kind FROM bills WHERE submitted_by='S531 walk' ORDER BY id DESC LIMIT 1").fetchone(); dbx.close()
            check("B6 the next scan, untouched, is a plain bill", row2 and row2["doc_kind"] is None, dict(row2) if row2 else None)
            check("B7 no page error", not errs, errs[:2])
            await b.close()
    asyncio.run(go())


try:
    main()
except Exception as _e:                                                          # noqa: BLE001 -- a crash is a RED, not a silence
    check("X the walk ran to its end", False, repr(_e)[:160])
red = R.count(False)
print("%d checks: %d green, %d red" % (len(R), len(R) - red, red))
sys.exit((0 if red else 1) if EXPECT_RED else (1 if red else 0))
