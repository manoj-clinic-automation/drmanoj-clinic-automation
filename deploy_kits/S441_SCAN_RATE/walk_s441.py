#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s441.py -- kit S441_SCAN_RATE. THE REAL finance app and THE REAL asset app (copies of /root/finance and /root/assetapp
carrying the kit's files, /root/shared carrying scan_checks_s441.py), over SCRATCH COPIES of finance.db and assets.db, through
Flask's test clients (finance: header identity; the asset app: current_user patched -- walk only). The same probe runs over the
box as it is (the negative control). Its own rows are stamped 'W441-nn'; every row is found by that key, never by counting.

  --new-fin DIR --old-fin DIR --new-ast DIR --old-ast DIR --shared DIR --portal DIR --db PATH --adb PATH --uploads DIR
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--new-fin", "--old-fin", "--new-ast", "--old-ast", "--shared", "--portal", "--db", "--adb", "--uploads"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
for _k in ("new_fin", "old_fin", "new_ast", "old_ast", "shared", "portal", "db", "adb", "uploads"):
    setattr(a, _k, os.path.abspath(getattr(a, _k)))
for p in (a.db, a.adb):
    assert ("scratch" in p or "walk" in p or p.startswith("/tmp")), "refusing a non-scratch database: " + p
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


PROBE = r'''
import os, sys, json, sqlite3, datetime as dt, re
FIN, AST, SH = os.environ["W_FIN"], os.environ["W_AST"], os.environ["W_SHARED"]
NEW = os.environ["W_MODE"] == "new"
os.environ.pop("SARVAM_API_KEY", None)
sys.path.insert(0, AST); sys.path.insert(0, FIN); os.chdir(FIN)
import finance_app as fa
import asset_register as ar
import purchase_app as pa, porders
pa._assets_db = os.environ["ASSETS_DB"]
fc = fa.app.test_client(); ac = ar.app.test_client()
with ar.app.app_context():
    ar.init_db()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
USERS = {"manoj": {"id": 1, "username": "manoj", "display_name": "Dr Manoj", "role": "owner", "active": 1, "password_hash": ""},
         "reception": {"id": None, "username": "reception", "display_name": "Reception", "role": "reception", "active": 1},
         "shivani": {"id": None, "username": "shivani", "display_name": "Shivani", "role": "reception", "active": 1},
         "shavez": {"id": None, "username": "shavez", "display_name": "Shavez", "role": "reception", "active": 1}}
CUR = {"u": "manoj"}
ar.current_user = lambda: USERS[CUR["u"]]
adb = sqlite3.connect(os.environ["ASSETS_DB"], timeout=30); adb.row_factory = sqlite3.Row
fdb = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); fdb.row_factory = sqlite3.Row
out = {}
K0 = (fc.get("/finance/porders/api/state", headers=H("shavez")).get_json(silent=True) or {}).get("kaam") or {}
out["kaam_counts0"] = K0.get("counts")                     # before anything here has touched the data: the code alone

# ---- the shared Reception login on the intake; the four widget switches on the intake only
CUR["u"] = "reception"; t = ac.get("/intake").get_data(as_text=True)
out["intake_shared"] = ["window.WHO_SHARED=true" in t, '"autoPage": true' in t, '"inlineStamp": true' in t, '"retryUpload": true' in t, '"directFile": true' in t]
CUR["u"] = "shivani"; t = ac.get("/intake").get_data(as_text=True)
out["intake_personal"] = ["window.WHO_SHARED=true" in t, '"autoPage": true' in t]
src = open(os.path.join(AST, "asset_register.py"), encoding="utf-8").read()
out["flags_elsewhere"] = src.count('"autoPage": True')
w = open(os.path.join(AST, "scanner_widget.js"), encoding="utf-8").read()
out["widget_optin"] = ["CFG.autoPage === true" in w, "CFG.inlineStamp === true" in w, "CFG.retryUpload === true" in w, "CFG.directFile === true" in w]

# ---- one client_token = one bill; the stamp comes back at once; who scanned
pdf = os.path.join(os.environ["W_UP"], "w441_paper.pdf")
def up(tok, who=None):
    CUR["u"] = "reception"
    if who: ac.set_cookie("clinic_who", who)
    else: ac.delete_cookie("clinic_who")
    d = {"lane": "other_doc", "note": "W441 walk", "bill_scan": (open(pdf, "rb"), "w441.pdf")}
    if tok: d["client_token"] = tok
    r = ac.post("/intake/scan_submit", data=d, content_type="multipart/form-data")
    return [r.status_code, r.get_json(silent=True), r.get_data(as_text=True)[:40]]
r1 = up("w441aa01", "shivani"); r2 = up("w441aa01", "shivani")
out["token"] = [r1[0], (r1[1] or {}).get("stamp") is not None, (r2[1] or {}).get("already"), (r1[1] or {}).get("id") == (r2[1] or {}).get("id") if r1[1] and r2[1] else None,
                r1[2] if not r1[1] else None]
if r1[1]:
    b = adb.execute("SELECT * FROM bills WHERE id=?", (r1[1]["id"],)).fetchone()
    out["scanned_by"] = [b["submitted_by"], b["scanned_by"] if "scanned_by" in b.keys() else None]
    adb.execute("UPDATE bills SET stamp_no='W441-00' WHERE id=?", (b["id"],)); adb.commit()

# ---- the after-the-fact pass on crafted rows (W441-01..07)
now = dt.datetime.now()
T = lambda m: (now - dt.timedelta(minutes=m)).strftime("%Y-%m-%d %H:%M")
ROWS = [("W441-01", "clinic", "draft", "WALK SURGICAL WORKS", "WLK-2026-0451", 1200.0, "Walkera", 50, "0f0f0f0f0f0f0f0f"),
        ("W441-02", "clinic", "draft", None, None, 1200.0, "Walkera", 48, "f0f0f0f0f0f0f0f0"),
        ("W441-03", "pharmacy", "captured", "WALKAPHARM DRUG HOUSE", "77904", 14442.0, "Walkerb", 40, "1a1a1a1a1a1a1a1a"),
        ("W441-04", "pharmacy", "captured", "WALKAPHARM DRUG HOUSE BAREILLY", "WK/077904", 14300.0, "Walkerc", 20, "2b2b2b2b2b2b2b2b"),
        ("W441-05", "clinic", "draft", "WALKBEE OPTICS", "WB002243", 5000.0, "Walkerb", 30, "3c3c3c3c3c3c3c3c"),
        ("W441-06", "clinic", "draft", "WALKBEE OPTICS", "WB002243", 6200.0, "Walkerd", 10, "4d4d4d4d4d4d4d4d"),
        ("W441-07", "clinic", "draft", "WALKCEE PHARMACEUTICAL", "189", 900.0, "Walkera", 5, "5e5e5e5e5e5e5e5e")]
IDS = {}
for st, lane, stt, v, no, tot, by, m, fpc in ROWS:
    cur = adb.execute("INSERT INTO bills(kind, stamp_no, lane, status, vendor, bill_no, total_amount, submitted_by, submitted_at, ocr_status, fpc, notes) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ({"clinic": "Consumable", "pharmacy": "Pharmacy"}[lane], st, lane, stt, v, no, tot, by, T(m), "read", fpc, "W441 walk"))
    IDS[st] = cur.lastrowid
adb.commit()
fdb.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, cash_p, credit_p, amount_p, source_md5, bw_md5, bw_amount_p, date_src) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ("WALKCEE PHARMACEUTICAL", "WALKCEE PHARMACEUTICAL", "W441X", now.date().isoformat(), now.strftime("%Y-%m"), 0, 1, 1, "w441walk", "w441walk", 1, "BILLWISE"))
fdb.commit()
if NEW:
    import scan_checks_s441 as S
    S.FIN_DB = os.environ["FINANCE_DB"]
    adb.execute("DELETE FROM scan_check_s441 WHERE bill_id NOT IN (%s)" % ",".join(str(i) for i in IDS.values()))   # judge only the walk's rows here
    adb.execute("INSERT OR IGNORE INTO scan_check_s441 (bill_id, verdict, at) SELECT id, 'walk-skip', '' FROM bills WHERE id NOT IN (%s)" % ",".join(str(i) for i in IDS.values()))
    adb.commit()
    out["pass"] = S.run_pass(adb, upload_dir=os.environ["W_UP"])
row = lambda s: dict(adb.execute("SELECT * FROM bills WHERE id=?", (IDS[s],)).fetchone())
out["rows"] = {s: [row(s)["status"], row(s).get("page_of"), row(s).get("dup_of"), (row(s).get("dup_why") or "")[:20]] for s in IDS}
out["ids"] = IDS
if NEW:
    out["questions"] = [[q["kind"], q["bill_id"], q["cand_id"]] for q in adb.execute("SELECT * FROM scan_question WHERE bill_id IN (%s) ORDER BY id" % ",".join(str(i) for i in IDS.values()))]

# ---- Purchase orders: the shared login is a sender, names who works, refuses a write with no name; Scan ka kaam carries the questions
fc.delete_cookie("clinic_who")
st = fc.get("/finance/porders/api/state", headers=H("reception"))
sj = st.get_json(silent=True) or {}
out["porders_reception"] = [st.status_code, sj.get("me")]
pg = fc.get("/finance/porders", headers=H("reception")).get_data(as_text=True)
out["porders_picker"] = ["window.WHO_SHARED=true" in pg, "window.WHO_SHARED=true" in fc.get("/finance/porders", headers=H("shavez")).get_data(as_text=True)]
r = fc.post("/finance/porders/api/arrive", json={"order_id": 0}, headers=H("reception"))
out["porders_noname"] = r.status_code
fc.set_cookie("clinic_who", "darpan")
r = fc.post("/finance/porders/api/arrive", json={"order_id": 0}, headers=H("reception"))
out["porders_named"] = r.status_code
K = (fc.get("/finance/porders/api/state", headers=H("shavez")).get_json(silent=True) or {}).get("kaam") or {}
out["kaam_twin"] = sorted([x["stamp"], x["kind"], (x.get("cand") or {}).get("stamp")] for x in (K.get("twin") or []) if str(x.get("stamp", "")).startswith("W441"))
out["kaam_keys"] = sorted(K.keys())
out["kaam_counts"] = K.get("counts")
if NEW and out["kaam_twin"]:
    q = [x for x in K["twin"] if x["stamp"] == "W441-06"]
    if q:
        CUR["u"] = "reception"; ac.delete_cookie("clinic_who")
        r0 = ac.post("/bills/%d/s441" % q[0]["scan"], json={"q": q[0]["q"], "answer": "same"})
        ac.set_cookie("clinic_who", "alisha")
        r1 = ac.post("/bills/%d/s441" % q[0]["scan"], json={"q": q[0]["q"], "answer": "same"})
        CUR["u"] = "shavez"
        r2 = ac.post("/bills/%d/s441" % q[0]["scan"], json={"q": q[0]["q"], "answer": "different"})
        out["answer"] = [r0.status_code, r1.status_code, (r1.get_json() or {}).get("by"), (r2.get_json() or {}).get("already"), row("W441-06")["status"], row("W441-06")["dup_of"] == IDS["W441-05"]]
        K2 = (fc.get("/finance/porders/api/state", headers=H("shavez")).get_json(silent=True) or {}).get("kaam") or {}
        out["answered"] = [[x["stamp"], x["answer"], x["by"]] for x in K2.get("answered", []) if str(x.get("stamp", "")).startswith("W441")]

# ---- the rate page: X-ray saves stay on the X-ray view; in place when fetched
pgh = fc.get("/finance/clinic/sheets?kind=xray", headers=H("manoj")).get_data(as_text=True)
xid = fdb.execute("SELECT id FROM owner_service WHERE kind='xray' ORDER BY id LIMIT 1").fetchone()
xid = xid[0] if xid else 0
r = fc.post("/finance/clinic/sheets/price", data={"id": xid, "kind": "xray", "price": "300"}, headers=H("manoj"))
out["sheets_nojs"] = [r.status_code, r.headers.get("Location", "")]
r = fc.post("/finance/clinic/sheets/price", data={"id": xid, "kind": "xray", "price": "300"}, headers=dict(H("manoj"), **{"X-Requested-With": "fetch"}))
j = r.get_json(silent=True) or {}
out["sheets_fetch"] = [r.status_code, j.get("ok"), "id='it-%d'" % xid in (j.get("html") or "")]
out["sheets_page"] = ["details class='sec'" in pgh, "data-live" in pgh]
out["sheets_reception"] = fc.get("/finance/clinic/sheets", headers=H("reception")).status_code
print("W441JSON " + json.dumps(out, default=str))
'''


def run(mode, fin, ast, db, adb):
    env = dict(os.environ, W_MODE=mode, W_FIN=fin, W_AST=ast, W_SHARED=a.shared, W_UP=a.uploads, FINANCE_DB=db, ASSETS_DB=adb,
               ASSETS_UPLOADS=a.uploads, SHARED_LIB_DIR=a.shared, FINANCE_SSO_DIR=a.portal, FINANCE_ALLOW_HEADER_AUTH="1",
               FINANCE_DB_FOR_SCANS=db, RECORDS_DRIVE_STUB=os.path.join(a.uploads, "stub"), PETTY_UPLOAD_DIR=a.uploads,
               PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, capture_output=True, text=True, timeout=900)
    line = [x for x in p.stdout.splitlines() if x.startswith("W441JSON ")]
    if not line:
        print(p.stdout[-3000:])
        print(p.stderr[-3000:])
        raise SystemExit("WALK_S441 RED -- the %s probe printed nothing" % mode)
    return json.loads(line[-1][9:])


os.makedirs(a.uploads, exist_ok=True)
pdfp = os.path.join(a.uploads, "w441_paper.pdf")
if not os.path.exists(pdfp):
    with open(pdfp, "wb") as fh:                        # a one-page PDF, written by hand -- no library needed
        fh.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
                 b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 400]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")
# the shared login's porders seat, as the installer writes it (on the scratch copies only)
for db in (a.db, a.db + ".old"):
    if db.endswith(".old"):
        copydb(a.db, db)
for db in (a.db, a.db + ".old"):
    c = sqlite3.connect(db)
    c.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('porders','reception','maker',1)")
    c.execute("UPDATE setting SET value=value||',reception' WHERE key='porders.senders' AND (','||value||',') NOT LIKE '%,reception,%'")
    c.commit(); c.close()
copydb(a.adb, a.adb + ".old")
NEW = run("new", a.new_fin, a.new_ast, a.db, a.adb)
OLD = run("old", a.old_fin, a.old_ast, a.db + ".old", a.adb + ".old")
print("-- new: " + json.dumps(NEW, default=str)[:1500])
print("-- old: " + json.dumps(OLD, default=str)[:900])

# ---- the rules are S439's: the copies agree with purchase_app on every vendor name and bill number on the box
sys.path.insert(0, a.shared)
import scan_checks_s441 as S  # noqa: E402
src = open(os.path.join(a.old_fin, "purchase_app.py"), encoding="utf-8").read()
ns = {}
exec("import re\nimport difflib as _difflib_s439\n_CITY_TAILS = %r\n" % (S._CITY_TAILS,), ns)
exec(src[src.index("S439_FY_RE = "):src.index("def _is_buyer_s439(")], ns)
fc_ = sqlite3.connect(a.db); ac_ = sqlite3.connect(a.adb)
vendors = sorted({r[0] for r in fc_.execute("SELECT DISTINCT supplier FROM purchase_bill WHERE supplier IS NOT NULL")} |
                 {r[0] for r in ac_.execute("SELECT DISTINCT vendor FROM bills WHERE vendor IS NOT NULL")})
nos = sorted({r[0] for r in fc_.execute("SELECT DISTINCT bill_no FROM purchase_bill WHERE bill_no IS NOT NULL")} |
             {r[0] for r in ac_.execute("SELECT DISTINCT bill_no FROM bills WHERE bill_no IS NOT NULL")})
bad = sum(1 for x in nos if ns["_bill_tails_s439"](x) != S.bill_tails(x))
toks = [(ns["_vendor_tokens_s439"](x), S.vendor_tokens(x)) for x in vendors]
bad += sum(1 for p, q in toks if p != q)
pairs = 0
for i in range(len(toks)):
    for j in range(i + 1, min(len(toks), i + 40)):
        pairs += 1
        if abs(ns["_vendor_sim_s439"](toks[i][0], toks[j][0]) - S.vendor_sim(toks[i][1], toks[j][1])) > 1e-12:
            bad += 1
check("RULES: bill_tails / vendor_tokens / vendor_sim = purchase_app's S439 functions on every bill number and vendor on the box (%d numbers, %d names, %d pairs)" % (len(nos), len(vendors), pairs), bad == 0, bad)

# ---- the new side
check("INTAKE: the shared Reception login gets the name picker and the four switches", NEW["intake_shared"] == [True] * 5, NEW["intake_shared"])
check("INTAKE: a personal login is never asked its name (the switches are on for everyone)", NEW["intake_personal"] == [False, True], NEW["intake_personal"])
check("WIDGET: the four switches are opt-in, and only the bill intake sets them (one config in the asset app)", NEW["widget_optin"] == [True] * 4 and NEW["flags_elsewhere"] == 1, (NEW["widget_optin"], NEW["flags_elsewhere"]))
check("UPLOAD: the stamp comes back at once; the same client_token twice is ONE bill (a retry is never a second scan)", NEW["token"][:4] == [200, True, True, True], NEW["token"])
check("UPLOAD: the shared login's scan carries the person (submitted_by stays 'Reception')", NEW.get("scanned_by") == ["Reception", "Shivani"], NEW.get("scanned_by"))
R = NEW["rows"]
check("PASS: a forgotten page (same person, 2 min later, no bill header, a different picture) joins its bill", R["W441-02"][0] == "rejected" and R["W441-02"][1] == NEW["ids"]["W441-01"], R["W441-02"])
check("PASS: a sure double scan (same supplier, same bill-number tail, amount within 2%) is set aside, kept, the first paper stays", R["W441-04"][0] == "rejected" and R["W441-04"][2] == NEW["ids"]["W441-03"] and R["W441-03"][0] == "captured", (R["W441-03"], R["W441-04"]))
check("PASS: a near match (same supplier and number, amount 24% apart) is asked, never decided", ["twin", NEW["ids"]["W441-06"], NEW["ids"]["W441-05"]] in NEW["questions"] and R["W441-06"][0] == "draft", NEW["questions"])
check("PASS: a Marg pharmacy supplier scanned in the clinic lane is asked about (lane)", ["lane", NEW["ids"]["W441-07"], None] in NEW["questions"], NEW["questions"])
check("PASS: the bill the page joined and the clean bill are left alone", R["W441-01"][0] == "draft" and R["W441-05"][0] == "draft", (R["W441-01"], R["W441-05"]))
check("ORDERS: the shared Reception login is a sender on Purchase orders", NEW["porders_reception"] == [200, "sender"], NEW["porders_reception"])
check("ORDERS: the page asks the shared login who is working; Shavez's own login is never asked", NEW["porders_picker"] == [True, False], NEW["porders_picker"])
check("ORDERS: a write with no name is refused 428 (the page asks first); with a name it goes through (404 = no such order, as before)", NEW["porders_noname"] == 428 and NEW["porders_named"] == 404, (NEW["porders_noname"], NEW["porders_named"]))
check("KAAM: Scan ka kaam carries the two questions, each beside its other paper", NEW["kaam_twin"] == sorted([["W441-06", "twin", "W441-05"], ["W441-07", "lane", None]]), NEW["kaam_twin"])
check("KAAM: the first answer settles it and carries the name; the shared login with no name is refused; a later answer changes nothing",
      NEW.get("answer") == [428, 200, "Alisha (Reception)", True, "rejected", True], NEW.get("answer"))
check("KAAM: who answered is shown", NEW.get("answered") == [["W441-06", "same", "Alisha (Reception)"]], NEW.get("answered"))
check("KAAM: the five S440 groups are untouched -- the same keys as the box plus 'twin' and 'answered'",
      sorted(set(NEW["kaam_keys"]) - set(OLD["kaam_keys"])) == ["answered", "twin"] and not (set(OLD["kaam_keys"]) - set(NEW["kaam_keys"])), (NEW["kaam_keys"], OLD["kaam_keys"]))
oc, nc = dict(OLD["kaam_counts0"] or {}), dict(NEW["kaam_counts0"] or {})
nc.pop("twin", None)
check("KAAM: every S440 count is the same as the box's on the same data (read before the walk touches it)", oc == nc and bool(oc), (oc, nc))
check("SHEETS: an X-ray save without JavaScript comes back to the X-ray view (F-665)", NEW["sheets_nojs"][0] == 302 and "kind=xray" in NEW["sheets_nojs"][1], NEW["sheets_nojs"])
check("SHEETS: a save from the page happens in place -- JSON with the redrawn line, no reload", NEW["sheets_fetch"] == [200, True, True], NEW["sheets_fetch"])
check("SHEETS: collapsible sections, live forms; still the doctor's alone", NEW["sheets_page"] == [True, True] and NEW["sheets_reception"] in (401, 403), (NEW["sheets_page"], NEW["sheets_reception"]))
# ---- the negative control: the box as it is
check("NEGATIVE: the box's intake has no picker and no switches", OLD["intake_shared"] == [False] * 5, OLD["intake_shared"])
check("NEGATIVE: the box's upload answers 'ok' (no stamp in the reply) and keeps no client_token", OLD["token"][1] is False or OLD["token"][4] == "ok", OLD["token"])
check("NEGATIVE: the box leaves the forgotten page and the sure double as two live bills", OLD["rows"]["W441-02"][0] == "draft" and OLD["rows"]["W441-04"][0] == "captured", (OLD["rows"]["W441-02"], OLD["rows"]["W441-04"]))
check("NEGATIVE: the box's Purchase orders never asks who is working, and takes a nameless write", OLD["porders_picker"] == [False, False] and OLD["porders_noname"] == 404, (OLD["porders_picker"], OLD["porders_noname"]))
check("NEGATIVE: the box's X-ray save lands on the procedures view (F-665)", OLD["sheets_nojs"][0] == 302 and "kind=xray" not in OLD["sheets_nojs"][1], OLD["sheets_nojs"])
print("WALK_S441 %s -- %d checks, %d failed%s" % ("GREEN" if not fails else "RED", n, len(fails), (": " + "; ".join(fails)) if fails else ""))
sys.exit(0 if not fails else 1)
