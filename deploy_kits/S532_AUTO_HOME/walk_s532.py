#!/usr/bin/env python3
"""walk_s532.py -- the S532_AUTO_HOME walk: the built files on a COPY of the live database (under the session's home, removed
after; made-up rows only, dated 2031, no person), the rule through the app's own reading hook and the heal.

    python3 walk_s532.py <dir with asset_register.py + clinic_papers.py + scanner_widget.js> <live assets.db> [--expect-red]"""
import importlib.util, os, shutil, sqlite3, sys, tempfile, types

D, LIVEDB = [os.path.abspath(a) for a in sys.argv[1:3]]
EXPECT_RED = "--expect-red" in sys.argv
R = []


def check(name, ok, detail=""):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)) if detail else ""))


def main():
    wd = tempfile.mkdtemp(prefix="s532_walk_", dir=os.path.expanduser("~"))
    try:
        for f in ("asset_register.py", "clinic_papers.py", "scanner_widget.js"):
            shutil.copy(os.path.join(D, f), wd)
        dbc = os.path.join(wd, "assets.db")
        src = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True); dst = sqlite3.connect(dbc); src.backup(dst); src.close(); dst.close()
        up = os.path.join(wd, "uploads"); os.makedirs(up)
        os.environ["ASSETS_DB"] = dbc; os.environ["ASSETS_UPLOADS"] = up; sys.path.insert(0, wd)
        before = sqlite3.connect(dbc).execute("SELECT COUNT(*) FROM bills WHERE status IN ('draft','captured') AND COALESCE(subgroup,'')='' AND COALESCE(ocr_status,'')='read' AND dup_of IS NULL").fetchone()[0]
        spec = importlib.util.spec_from_file_location("asset_register", os.path.join(wd, "asset_register.py"))
        try:
            m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
        except Exception as e:                                                    # noqa: BLE001
            check("W1 the app imports with the built files", False, repr(e)[:200]); return
        cp = sys.modules.get("clinic_papers")
        check("W1 the app imports; clinic_papers %s mounted" % getattr(cp, "VERSION", "?"), cp is not None and getattr(cp, "VERSION", "") == "S532.1")
        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        placed = db.execute("SELECT COUNT(DISTINCT bill_id) FROM bill_audit WHERE action IN ('auto_lane','auto_group')").fetchone()[0]
        after = db.execute("SELECT COUNT(*) FROM bills WHERE status IN ('draft','captured') AND COALESCE(subgroup,'')='' AND COALESCE(ocr_status,'')='read' AND dup_of IS NULL").fetchone()[0]
        check("W2 the heal at start placed what the history allows (waiting %d -> %d, %d placed by the system)" % (before, after, placed), after <= before)
        # the history as the rule reads it, from the real rows
        lh, gh = cp.supplier_history(db, cp._supplier_key("SHIVAAZ FORMULATIONS"), -1)
        check("W3 history: Shivaaz's papers all on the pharmacy lane, two or more", list(lh.keys()) == ["pharmacy"] and lh["pharmacy"] >= 2, lh)
        lv, gv = cp.supplier_history(db, cp._supplier_key("VARIETY STATIONERS"), -1)
        check("W4 history: Variety Stationers all on the clinic lane, all in one group (others), two or more", list(lv.keys()) == ["clinic"] and list(gv.keys()) == ["others"] and gv["others"] >= 2, (lv, gv))
        ly, gy = cp.supplier_history(db, cp._supplier_key("YUVIKA SURGICALS"), -1)
        check("W5 history: Yuvika is seen on two lanes (never decided)", len(ly) >= 2, ly)
        def mk(vendor, lane, status, kind, doc_kind=None, ocr="read"):
            cur = db.execute("INSERT INTO bills(kind,vendor,bill_date,total_amount,source_stored,stamp_no,status,lane,created_at,bill_month,ocr_status,doc_kind,challan_state) "
                             "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (kind, vendor, "2031-01-15", 999.0, "", "Z-%d" % (9200 + db.execute("SELECT COUNT(*) FROM bills WHERE stamp_no LIKE 'Z-92%'").fetchone()[0]),
                                                                  status, lane, "2031-01-15 10:00:00", "2031-01", ocr, doc_kind, ("awaiting" if doc_kind == "challan" else None)))
            db.commit(); return cur.lastrowid
        def row(bid):
            return dict(db.execute("SELECT lane, status, kind, subgroup, approved_by FROM bills WHERE id=?", (bid,)).fetchone())
        def audits(bid):
            return [r[0] for r in db.execute("SELECT action FROM bill_audit WHERE bill_id=? ORDER BY id", (bid,))]
        b1 = mk("SHIVAAZ FORMULATIONS BAREILLY", "clinic", "draft", "Consumable")
        did = cp.auto_home(db, b1); r1 = row(b1)
        check("W6 a Shivaaz bill scanned on the clinic lane goes to the pharmacy lane by itself (captured, kind Pharmacy, audited)", did == ["lane:pharmacy"] and r1["lane"] == "pharmacy" and r1["status"] == "captured" and r1["kind"] == "Pharmacy" and "auto_lane" in audits(b1), (did, r1))
        b2 = mk("Variety Stationers", "pharmacy", "captured", "Pharmacy")
        did = cp.auto_home(db, b2); r2 = row(b2)
        check("W7 a Variety Stationers bill scanned on the pharmacy lane goes to the clinic lane, gets 'others' and is accepted", did == ["lane:clinic", "group:others,accepted"] and r2["lane"] == "clinic" and r2["subgroup"] == "others" and r2["status"] == "approved" and (r2["approved_by"] or "").startswith("system"), (did, r2))
        b3 = mk("YUVIKA SURGICALS", "clinic", "draft", "Consumable")
        did = cp.auto_home(db, b3); r3 = row(b3)
        check("W8 a Yuvika bill is not decided at all (two lanes in its history): no lane, no group", did == [] and r3["lane"] == "clinic" and r3["subgroup"] is None and r3["status"] == "draft", (did, r3))
        b4 = mk("Made-Up Never Seen Traders", "clinic", "draft", "Consumable")
        check("W9 an unknown supplier: nothing", cp.auto_home(db, b4) == [] and row(b4)["lane"] == "clinic")
        b5 = mk("SHIVAAZ FORMULATIONS", "clinic", "draft", "Consumable", doc_kind="challan")
        check("W10 a challan is never moved", cp.auto_home(db, b5) == [] and row(b5)["lane"] == "clinic")
        check("W11 a second look at the same paper does nothing (idempotent)", cp.auto_home(db, b1) == [] and cp.auto_home(db, b2) == [])
        # the system never feeds itself: two papers the system placed are no evidence until a person confirms them
        la = mk("Made-Up Loop Traders", "pharmacy", "captured", "Pharmacy"); lb = mk("Made-Up Loop Traders", "pharmacy", "captured", "Pharmacy"); lz = mk("Made-Up Loop Traders", "pharmacy", "captured", "Pharmacy")
        for x in (la, lb, lz):
            db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (x, "2031-01-15 10:01", "", "auto_lane", '{"from":"clinic","to":"pharmacy","evidence":2}'))
        db.commit()
        lc = mk("Made-Up Loop Traders", "clinic", "draft", "Consumable")
        check("W12 three system-placed papers are no evidence: the next is not moved", cp.auto_home(db, lc) == [] and row(lc)["lane"] == "clinic")
        for x in (la, lb, lz):
            db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (x, "2031-01-15 10:02", "Dr Manoj", "relane", '{"from":"pharmacy","to":"pharmacy"}'))
        db.commit()
        did = cp.auto_home(db, lc)
        check("W13 once a person has confirmed all three, the next follows", did == ["lane:pharmacy"] and row(lc)["lane"] == "pharmacy", did)
        b8 = mk("ENVIRAD MEDICARE PVT LTD", "lab_purchase", "captured", "Lab")
        check("W14a a paper on the lab lane is never moved by the system (Envirad bills both NK Pathology and the clinic)", cp.auto_home(db, b8) == [] and row(b8)["lane"] == "lab_purchase")
        b9 = mk("ENVIRAD MEDICARE PVT LTD", "pharmacy", "captured", "Pharmacy")
        check("W14b a supplier whose clinic papers were never sorted by a person is not sent to the clinic lane", cp.auto_home(db, b9) == [] and row(b9)["lane"] == "pharmacy")
        b6 = mk("SHIVAAZ FORMULATIONS", "clinic", "draft", "Consumable")
        db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (b6, "2031-01-15 10:03", "Shavez", "relane", '{"from":"pharmacy","to":"clinic"}')); db.commit()
        check("W14 a paper a person has moved is never moved by the system", cp.auto_home(db, b6) == [] and row(b6)["lane"] == "clinic")
        # the hook: the background reading ends with the system's look (Sarvam stood in by a stub; no key needed)
        b7 = mk(None, "clinic", "draft", "Consumable", ocr=None)
        m.SARVAM = types.SimpleNamespace(extract=lambda path, schema=None: ({"vendor": "GUNINA PHARMACEUTICALS PVT LTD"}, "done"))
        m._map_bill = lambda data: ({"vendor": data.get("vendor")}, [])
        st = m._bg_extract(b7, os.path.join(up, "none.pdf"))
        db2 = sqlite3.connect(dbc); db2.row_factory = sqlite3.Row; r7 = dict(db2.execute("SELECT lane, status, vendor, ocr_status FROM bills WHERE id=?", (b7,)).fetchone()); db2.close()
        check("W15 the reading hook: after the OCR fills the supplier, the paper goes home by itself", st == "read" and r7["vendor"].startswith("GUNINA") and r7["lane"] == "pharmacy" and r7["status"] == "captured", (st, r7))
        # the page says so
        c = m.app.test_client()
        u = db.execute("SELECT id FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone(); ep = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()
        with c.session_transaction() as s:
            s["uid"] = u[0]; s["epoch"] = ep[0] if ep else None
        t = c.get("/papers/%d" % b2).get_data(as_text=True)
        check("W16 the paper page says it was placed by the system and can be changed", "Placed by the system from" in t and "change it here if wrong" in t)
        for path, name in (("/papers", "papers"), ("/papers/month", "month"), ("/papers/challans", "bills awaited"), ("/bills", "bills"), ("/intake", "intake"), ("/healthz", "healthz")):
            rr = c.get(path); check("W17 %s still answers" % name, rr.status_code == 200, rr.status_code)
        db.close()
        live = sqlite3.connect("file:%s?mode=ro" % LIVEDB, uri=True)
        check("W18 the LIVE database was not written", live.execute("SELECT COUNT(*) FROM bill_audit WHERE action IN ('auto_lane','auto_group')").fetchone()[0] == 0 and live.execute("SELECT COUNT(*) FROM bills WHERE stamp_no LIKE 'Z-92%'").fetchone()[0] == 0)
        live.close()
    finally:
        shutil.rmtree(wd, ignore_errors=True)


try:
    main()
except Exception as _e:                                                          # noqa: BLE001
    check("X the walk ran to its end", False, repr(_e)[:160])
red = R.count(False)
print("%d checks: %d green, %d red" % (len(R), len(R) - red, red))
sys.exit((0 if red else 1) if EXPECT_RED else (1 if red else 0))
