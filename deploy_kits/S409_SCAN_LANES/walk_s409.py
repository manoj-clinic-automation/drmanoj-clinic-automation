#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s409.py -- kit S409_SCAN_LANES. THE REAL asset app (a copy of /root/assetapp carrying the kit's file) over a SCRATCH
COPY of assets.db, and THE REAL finance_app (a copy of /root/finance carrying the two Sanjeevni edits) over a SCRATCH COPY of
finance.db. Crafted bill images made on the box with ImageMagick (the same tool the guard uses), crafted logins through the
app's own login_required (current_user patched, walk only), its own rows keyed W409*. Nothing real is scanned or matched.

  --assets-new DIR --assets-old DIR  (copies of /root/assetapp: the kit's file / the box as it is)
  --assets-db PATH                   (the scratch assets.db; PATH.old is made for the old app)
  --app DIR --old DIR --db PATH      (copies of /root/finance: the kit's two files / the box as it is; the scratch finance.db)
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--assets-new", "--assets-old", "--assets-db", "--app", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert a.assets_db.startswith("/tmp") or "walk" in a.assets_db, "refusing a non-scratch assets database"
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
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


copydb(a.assets_db, a.assets_db + ".old")
copydb(a.db, a.db + ".old")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s409  # noqa: E402
assert seed_s409.seed(a.db, a.assets_db) == 0, "seed failed"
IMG = os.path.join(os.path.dirname(os.path.abspath(a.assets_db)), "w409img")
os.makedirs(IMG, exist_ok=True)
SEED = {"one.jpg": 11, "n2.jpg": 22, "n3.jpg": 33, "n4.jpg": 44, "n5.jpg": 55, "n6.jpg": 66, "n7.jpg": 77, "t1.jpg": 101, "t2.jpg": 102,
        "t3.jpg": 103, "t4.jpg": 104, "t5.jpg": 105, "r1.jpg": 201, "late.jpg": 301}


def paper(name, text, *rects):
    """A crafted 'bill': a white page printed with a deterministic pattern of bars and lines (a different seed per paper --
    like a different printed form, never a blank sheet), a caption and a block or two, so the perceptual hashes of different
    papers are far apart and only a re-shot of the SAME paper is near. (ImageMagick's plasma ignores -seed; this does not.)"""
    rng = SEED[name] * 7919 + 17
    cmd = ["convert", "-size", "600x800", "xc:white", "-fill", "black", "-pointsize", "34", "-draw", "text 40,790 '%s'" % text]
    for _ in range(16):
        rng = (rng * 1103515245 + 12345) % 2147483648
        y = 40 + rng % 700
        rng = (rng * 1103515245 + 12345) % 2147483648
        x0 = 30 + rng % 260
        rng = (rng * 1103515245 + 12345) % 2147483648
        w = 100 + rng % 420
        rng = (rng * 1103515245 + 12345) % 2147483648
        h = 8 + rng % 34
        cmd += ["-draw", "rectangle %d,%d %d,%d" % (x0, y, min(590, x0 + w), min(795, y + h))]
    for r in rects:
        cmd += ["-draw", "rectangle " + r]
    subprocess.run(cmd + [os.path.join(IMG, name)], check=True)


paper("one.jpg", "W409 BILL ONE", "60,300 500,340", "60,420 300,440")
subprocess.run(["convert", os.path.join(IMG, "one.jpg"), "-gravity", "center", "-crop", "96%x96%+0+0", "+repage",
                os.path.join(IMG, "one_reshot.jpg")], check=True)                         # a straight re-scan: a 4% re-crop
subprocess.run(["convert", os.path.join(IMG, "one.jpg"), "-background", "white", "-rotate", "2", "-gravity", "center", "-crop", "96%x96%+0+0", "+repage",
                os.path.join(IMG, "one_tilt.jpg")], check=True)                           # a re-shot with a visible tilt: the OCR's job
paper("n2.jpg", "W409 BILL TWO", "40,40 300,400")
paper("n3.jpg", "W409 BILL THREE", "300,40 560,400")
paper("n4.jpg", "W409 BILL FOUR", "40,400 300,760")
paper("n5.jpg", "W409 BILL FIVE", "300,400 560,760")
paper("n6.jpg", "W409 BILL SIX", "150,200 450,600")
paper("n7.jpg", "W409 BILL SEVEN", "40,40 200,760")
paper("t1.jpg", "W409 TRIPLE ONE", "40,40 560,250")
paper("t2.jpg", "W409 TRIPLE TWO", "40,550 560,760")
paper("t3.jpg", "W409 TRIPLE THREE", "40,40 160,760", "440,40 560,760")
paper("t4.jpg", "W409 TRIPLE FOUR", "40,300 560,500")
paper("t5.jpg", "W409 TRIPLE FIVE", "40,40 300,300", "300,500 560,760")
paper("r1.jpg", "W409 RELANE", "200,40 400,760")
paper("late.jpg", "W409 LATE", "40,40 560,120", "40,680 560,760")
subprocess.run(["convert", os.path.join(IMG, "n2.jpg"), os.path.join(IMG, "n2.pdf")], check=False)
print("-- scratch copies made and seeded; %d crafted bill images in %s" % (len(os.listdir(IMG)), IMG))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, io, re
APP = os.environ["ASSETSDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ.pop("SARVAM_API_KEY", None)
NEW = os.environ["MODE"] == "new"
IMG = os.environ["IMG"]
import asset_register as ar
from werkzeug.datastructures import FileStorage
c = ar.app.test_client()
USERS = {"manoj": {"id": 1, "username": "manoj", "display_name": "Dr Manoj", "role": "owner", "active": 1, "password_hash": ""},
         "manager": {"id": 3, "username": "manager", "display_name": "Manager", "role": "manager", "active": 1, "password_hash": ""}}
for u in ("sukhveer", "awdhesh", "darpan", "shavez", "alisha"):
    USERS[u] = {"id": None, "username": u, "display_name": u.title(), "role": "reception", "active": 1}
CUR = {"u": "manoj"}
ar.current_user = lambda: USERS[CUR["u"]]
def AS(u): CUR["u"] = u
db = sqlite3.connect(os.environ["ASSETS_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
one = lambda s, *a: db.execute(s, a).fetchone()[0]
def G(u, p):
    AS(u); r = c.get(p); return [r.status_code, r.get_data(as_text=True)]
def P(u, p, data):
    AS(u); r = c.post(p, data=data, follow_redirects=False); return [r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)]
def submit(u, fname, lane, note="walk", prefill=None):
    AS(u)
    with ar.app.test_request_context("/intake/submit", method="POST"):
        ar.g.user = USERS[u]
        with open(os.path.join(IMG, fname), "rb") as fh:
            fs = FileStorage(stream=io.BytesIO(fh.read()), filename=fname)
        return ar._create_intake_bill(fs, note, lane, prefill or {})
def bill(bid):
    r = q("SELECT * FROM bills WHERE id=?", bid)        # every column the copy has; the old copy lacks the S409 ones
    if not r:
        return None
    d = r[0]
    for k in ("lane", "fp", "dup_of", "dup_flag", "dup_cand", "late_for"):
        d.setdefault(k, None)
    return d
out = {"cols": [c_[1] for c_ in db.execute("PRAGMA table_info(bills)")]}
out["has_lane_col"] = "lane" in out["cols"]
out["backfill"] = q("SELECT COALESCE(lane,'(null)') lane, kind, COUNT(*) n FROM bills GROUP BY 1,2 ORDER BY 1,2") if NEW else None
# --- the five lanes (one distinct image each)
b = {}
for lane, img in (("clinic", "n2.jpg"), ("pharmacy", "n3.jpg"), ("lab_purchase", "n4.jpg"), ("owner_expense", "n5.jpg"), ("other_doc", "n6.jpg")):
    b[lane] = bill(submit("sukhveer" if lane == "lab_purchase" else "alisha", img, lane))
out["lanes"] = {k: [v["kind"], v["status"], v.get("lane"), bool(v["stamp_no"]), bool(v.get("fp"))] for k, v in b.items()}
out["draft_list"] = G("manager", "/bills?status=draft")
out["draft_list"] = [out["draft_list"][0], b["clinic"]["stamp_no"] in out["draft_list"][1], b["lab_purchase"]["stamp_no"] in out["draft_list"][1], b["pharmacy"]["stamp_no"] in out["draft_list"][1]]
db.execute("UPDATE bills SET vendor='W409 LAB VENDOR', bill_no='L1', total_amount=99999.5, bill_date=? WHERE id=?", (dt.date.today().isoformat(), b["lab_purchase"]["id"])); db.commit()
pp = G("manoj", "/purchases")
out["purchases"] = [pp[0], "99999.50" in pp[1] or "99,999.50" in pp[1] or "99,999" in pp[1], "Scans this month" in pp[1]]
if not NEW:
    out["intake_sukhveer"] = G("sukhveer", "/intake")[1]
    out["intake_sukhveer"] = ["lab_purchase" in out["intake_sukhveer"], 'value="lab_purchase" selected' in out["intake_sukhveer"]]
    b1 = bill(submit("alisha", "one.jpg", "clinic")); b2 = bill(submit("alisha", "one.jpg", "clinic"))
    out["dup_old"] = [b1["status"], b2["status"], b2.get("dup_of") if b2 else None, b1["stamp_no"] != b2["stamp_no"]]
    out["routes_old"] = [G("manoj", "/lanes")[0], P("manoj", "/bills/%d/lane" % b1["id"], {"lane": "pharmacy"})[0]]
    out["slip_old"] = G("alisha", "/intake/slip/%d?json=1" % b2["id"])
    out["slip_old"] = [out["slip_old"][0], "Yeh bill pehle" in out["slip_old"][1]]
    out["reception_gate"] = [G("alisha", "/bills")[0], G("alisha", "/intake")[0]]
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
# --- per-user default lane
def sel(u):
    h = G(u, "/intake")[1]; m = re.search(r'<option value="([a-z_]+)" selected', h); return m.group(1) if m else None
out["defaults"] = {u: sel(u) for u in ("sukhveer", "awdhesh", "darpan", "manoj", "shavez")}
out["lanes_reception"] = G("shavez", "/lanes")[0]
out["lanes_set"] = P("manoj", "/lanes", {"username": "shavez", "lane": "pharmacy"})[0]
out["defaults_after"] = sel("shavez")
out["lanes_page"] = G("manoj", "/lanes"); out["lanes_page"] = [out["lanes_page"][0], "shavez" in out["lanes_page"][1], "sukhveer" in out["lanes_page"][1]]
# --- the duplicate guard, layer (a): the same image twice; a re-shot; a different paper
b1 = bill(submit("alisha", "one.jpg", "clinic"))
b2 = bill(submit("alisha", "one.jpg", "clinic"))
b3 = bill(submit("darpan", "one_reshot.jpg", "pharmacy"))
b7 = bill(submit("alisha", "n7.jpg", "clinic"))
bt = bill(submit("alisha", "one_tilt.jpg", "clinic"))
HC = lambda x, y: ar._hamming(x.get("fpc") or "", y.get("fpc") or "") if (x.get("fpc") and y.get("fpc")) else None
out["fp"] = [bool(b1["fp"]) and bool(b1.get("fpc")), b1["fp"] == b2["fp"], HC(b1, b3), HC(b1, b7), HC(b1, bt), ar._hamming(b1["fp"], bt["fp"]) if bt.get("fp") else None]
out["dup_a"] = [b1["status"], b2["status"], b2["dup_of"] == b1["id"], b2["dup_flag"], b2["stamp_no"] != b1["stamp_no"],
                (b3["status"] == "rejected" and b3["dup_of"] == b1["id"]) or (b3["dup_flag"] == "maybe" and b3["dup_cand"] == b1["id"]), b3["status"], b3["dup_flag"],
                b7["status"], b7["dup_of"], b7["dup_flag"], bt["status"], bt["dup_flag"]]
sj = G("alisha", "/intake/slip/%d?json=1" % b2["id"])
out["slip_json"] = [sj[0], json.loads(sj[1]).get("first_stamp") == b1["stamp_no"], json.loads(sj[1]).get("message")]
sh = G("alisha", "/intake/slip/%d" % b2["id"])
out["slip_html"] = [sh[0], ("Yeh bill pehle %s par scan ho chuka hai" % b1["stamp_no"]) in sh[1], "void" in sh[1]]
sh1 = G("alisha", "/intake/slip/%d" % b1["id"])
out["slip_ok"] = [sh1[0], ("slipstamp" in sh1[1]) and (b1["stamp_no"] in sh1[1]), "json=1" in sh1[1]]
pdf_ok = os.path.exists(os.path.join(IMG, "n2.pdf"))
bp = bill(submit("alisha", "n2.pdf", "clinic")) if pdf_ok else None
out["pdf"] = [pdf_ok, bool(bp and bp["fp"]), ((bp["status"] == "rejected" and bp["dup_of"] == b["clinic"]["id"]) or (bp["dup_flag"] == "maybe" and bp["dup_cand"] == b["clinic"]["id"])) if bp else None,
              (bp["status"], bp["dup_flag"], ar._hamming(bp["fp"], b["clinic"]["fp"]) if (bp and bp["fp"] and b["clinic"]["fp"]) else None) if bp else None]
# --- layer (b): the OCR triple (simulated: the fields land, then the after-OCR hook runs) on fresh distinct papers
tA = bill(submit("alisha", "t1.jpg", "clinic")); tB = bill(submit("alisha", "t2.jpg", "clinic")); tC = bill(submit("alisha", "t3.jpg", "clinic")); tD = bill(submit("alisha", "t4.jpg", "clinic"))
out["triple_fps_distinct"] = len({tA["fp"], tB["fp"], tC["fp"], tD["fp"]}) == 4
# the image layer may have gone amber on one of these against an earlier crafted paper (by design it may); this test is layer (b)'s
# alone, so the image verdicts are cleared here and noted
out["t_image_flags"] = [x["dup_flag"] for x in (tA, tB, tC, tD)]
db.execute("UPDATE bills SET dup_flag=NULL, dup_cand=NULL, dup_why=NULL WHERE id IN (?,?,?,?)", (tA["id"], tB["id"], tC["id"], tD["id"])); db.commit()
db.execute("UPDATE bills SET vendor='W409 VENDOR X', bill_no='INV-77', total_amount=1234.5, bill_date=? WHERE id=?", (dt.date.today().isoformat(), tA["id"]))
db.execute("UPDATE bills SET vendor='w409 vendor x', bill_no='inv 77', total_amount=1234.50, bill_date=? WHERE id=?", (dt.date.today().isoformat(), tB["id"]))
db.execute("UPDATE bills SET vendor='W409 VENDOR X', bill_no=NULL, total_amount=1234.5, bill_date=? WHERE id=?", (dt.date.today().isoformat(), tC["id"]))
db.execute("UPDATE bills SET vendor='W409 VENDOR X', bill_no='INV-78', total_amount=1299.0, bill_date=? WHERE id=?", (dt.date.today().isoformat(), tD["id"]))
db.commit()
ar._dup_after_ocr(db, tB["id"]); ar._dup_after_ocr(db, tC["id"]); ar._dup_after_ocr(db, tD["id"]); db.commit()
tB, tC, tD = bill(tB["id"]), bill(tC["id"]), bill(tD["id"])
out["triple"] = [[tB["status"], tB["dup_of"] == tA["id"]], [tC["status"], tC["dup_flag"], tC["dup_cand"] == tA["id"]], [tD["status"], tD["dup_flag"]]]
lst = G("manager", "/bills")[1]
out["list_amber"] = [("second scan of %s?" % tA["stamp_no"]) in lst, "Not duplicate" in lst, "<th>Lane</th>" in lst]
out["dup_no"] = P("manager", "/bills/%d/dup" % tC["id"], {"what": "no"})[0]; tC = bill(tC["id"])
tE = bill(submit("alisha", "t5.jpg", "clinic"))
db.execute("UPDATE bills SET vendor='W409 VENDOR X', bill_no='', total_amount=1234.5, dup_flag=NULL, dup_cand=NULL, dup_why=NULL WHERE id=?", (tE["id"],)); db.commit()
ar._dup_after_ocr(db, tE["id"]); db.commit(); tE = bill(tE["id"])
out["dup_yes"] = [tE["dup_flag"], P("manager", "/bills/%d/dup" % tE["id"], {"what": "yes"})[0]]; tE = bill(tE["id"])
out["dup_decided"] = [tC["dup_flag"], tE["status"], tE["dup_of"] == tA["id"]]
out["audit"] = q("SELECT action, COUNT(*) n FROM bill_audit GROUP BY action ORDER BY action")
# --- approve of a triple already approved is refused, naming the stamp
out["approve_A"] = P("manager", "/bills/%d/approve" % tA["id"], {})[0]; tA = bill(tA["id"])
out["approve_D_before"] = tD["status"]
db.execute("UPDATE bills SET bill_no='INV-77', total_amount=1234.5 WHERE id=?", (tD["id"],)); db.commit()     # now the same triple as the approved tA
r = P("manager", "/bills/%d/approve" % tD["id"], {}); tD = bill(tD["id"])
fl = G("manager", "/bills/%d" % tD["id"])[1]
out["approve_dup"] = [tA["status"], r[0], tD["status"], tD["dup_flag"], ("already approved as %s" % tA["stamp_no"]) in fl]
# --- re-lane, audited; an approved bill cannot leave clinic; reception cannot
rl = bill(submit("alisha", "r1.jpg", "clinic"))
out["relane1"] = P("manager", "/bills/%d/lane" % rl["id"], {"lane": "pharmacy"})[0]; rl = bill(rl["id"])
out["relane_after"] = [rl["lane"], rl["kind"], rl["status"]]
out["relane2"] = P("manoj", "/bills/%d/lane" % rl["id"], {"lane": "clinic"})[0]; rl = bill(rl["id"])
out["relane_back"] = [rl["lane"], rl["kind"], rl["status"]]
out["relane_reception"] = P("alisha", "/bills/%d/lane" % rl["id"], {"lane": "pharmacy"})[0]
out["relane_approved"] = P("manager", "/bills/%d/lane" % tA["id"], {"lane": "lab_purchase"})[0]; tA2 = bill(tA["id"])
out["relane_approved_after"] = [tA2["lane"], tA2["status"]]
out["relane_audit"] = q("SELECT action, detail FROM bill_audit WHERE bill_id=? ORDER BY id", rl["id"])
# --- late bills
lt = bill(submit("darpan", "late.jpg", "pharmacy", prefill={"vendor": "W409 LATE VENDOR", "bill_no": "LT1", "bill_date": "2026-07-15", "amount": "500.00"}))
out["late"] = [lt["late_for"], lt["bill_date"], lt["lane"], b["pharmacy"]["late_for"]]
db.execute("UPDATE bills SET bill_date=? WHERE id=?", (dt.date.today().isoformat(), lt["id"])); ar._set_late(db, lt["id"]); db.commit()
out["late_fixed"] = bill(lt["id"])["late_for"]
# --- S403's pre-filled intake still lands on pharmacy; the prefill parser knows the five lanes and drops nonsense
with ar.app.test_request_context("/intake?lane=pharmacy&vendor=YUVIKA%20SURGICALS&bill_no=9&amount=1.00"):
    pf1 = ar._intake_prefill()
with ar.app.test_request_context("/intake?lane=lab_purchase&vendor=NK"):
    pf2 = ar._intake_prefill()
with ar.app.test_request_context("/intake?lane=nonsense"):
    pf3 = ar._intake_prefill()
out["prefill"] = [pf1.get("lane"), pf2.get("lane"), "lane" in pf3]
# --- reception still reaches only its routes; the lane line on /purchases
out["reception_gate"] = [G("alisha", "/bills")[0], G("alisha", "/lanes")[0], G("alisha", "/intake")[0], G("alisha", "/bills/%d" % rl["id"])[0]]
pp2 = G("manoj", "/purchases")[1]
m = re.search(r"Scans this month[^<]*", pp2)
out["lane_line"] = m.group(0) if m else None
out["intake_text"] = "A paper that already carries a B-number is never scanned again" in G("alisha", "/intake")[1]
print("JSON:" + json.dumps(out, default=str))
'''

FIN_PROBE = r'''
import json, os, sys, sqlite3, datetime as dt
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
now = lambda: dt.datetime.now().replace(microsecond=0).isoformat()
out = {}
md = "w409sw"
db.execute("INSERT OR REPLACE INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
           (md, "SUPPLIERWISE", "W409", "2026-08-01", "2026-09-30", "20260926-000000", now(), 2, 200000))
for bno, d in (("W409OLD", "2026-08-25"), ("W409NEW", "2026-09-02")):
    db.execute("INSERT OR IGNORE INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, sw_md5, sw_amount_p) VALUES (?,?,?,?,?,?,?,?)",
               ("W409 VENDOR", "W409 VENDOR", bno, d, d[:7], 100000, md, 100000))
db.commit()
out["setting"] = [r[0] for r in db.execute("SELECT value FROM setting WHERE key='porders.scan_from'")]
import porders
lst = porders.unscanned_bills(db)
nos = [x["bill_no"] for x in lst]
out["porders"] = ["W409OLD" in nos, "W409NEW" in nos, min((x["bill_date"] for x in lst), default=None)]
pg = G("manoj", "/finance/purchase/page/scans")[1]
out["scans_page"] = ["W409OLD" in pg, "W409NEW" in pg]
st = G("darpan", "/finance/porders/api/state")[1]
out["state_scans"] = [st["scans"]["n"], any(b_["bill_no"] == "W409OLD" for b_ in st["scans"]["bills"]), any(b_["bill_no"] == "W409NEW" for b_ in st["scans"]["bills"])] if isinstance(st, dict) else st
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, adb):
    up = os.path.join(os.path.dirname(adb), "uploads_" + mode)
    os.makedirs(up, exist_ok=True)
    env = dict(os.environ, ASSETSDIR=appdir, MODE=mode, ASSETS_DB=adb, ASSETS_UPLOADS=up, IMG=IMG)
    env.pop("SARVAM_API_KEY", None)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s asset app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


def fprobe(appdir, mode, dbpath):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1")
    p = subprocess.run([sys.executable, "-B", "-c", FIN_PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s finance app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.assets_old, "old", a.assets_db + ".old")
N = probe(a.assets_new, "new", a.assets_db)
FO = fprobe(a.old, "old", a.db + ".old")
FN = fprobe(a.app, "new", a.db)

print("-- 1  the five lanes, the approval queue, the spend")
check("bills.lane exists and every old row is backfilled (Pharmacy -> pharmacy, the rest -> clinic)", N["has_lane_col"] and all((r["lane"] == "pharmacy") == (r["kind"] == "Pharmacy") and r["lane"] != "(null)" for r in N["backfill"]), N["backfill"])
L = N["lanes"]
check("clinic -> Consumable/draft; pharmacy -> Pharmacy/captured; lab_purchase -> Lab/captured; owner_expense -> Expense/captured; other_doc -> Document/captured; each stamped and fingerprinted",
      L["clinic"][:3] == ["Consumable", "draft", "clinic"] and L["pharmacy"][:3] == ["Pharmacy", "captured", "pharmacy"] and L["lab_purchase"][:3] == ["Lab", "captured", "lab_purchase"]
      and L["owner_expense"][:3] == ["Expense", "captured", "owner_expense"] and L["other_doc"][:3] == ["Document", "captured", "other_doc"] and all(v[3] and v[4] for v in L.values()), L)
check("only the clinic bill is in the approval queue (status=draft list); the lab and pharmacy ones are not", N["draft_list"] == [200, True, False, False], N["draft_list"])
check("NEGATIVE CONTROL inside the new app: a lab-purchase row with a ₹99,999.50 total never enters the owner's spend (status captured, never approved); the lane line is on /purchases",
      N["purchases"] == [200, False, True], N["purchases"])

print("-- 2  each person's drop-down opens on their own head")
check("sukhveer -> lab purchase, awdhesh -> clinic, darpan -> pharmacy, manoj -> Dr MK expense, shavez -> clinic", N["defaults"] == {"sukhveer": "lab_purchase", "awdhesh": "clinic", "darpan": "pharmacy", "manoj": "owner_expense", "shavez": "clinic"}, N["defaults"])
check("the owner's /lanes card: reception refused (403); the owner sets shavez -> pharmacy and shavez's drop-down follows; the card lists the seeds", N["lanes_reception"] == 403 and N["lanes_set"] in (302, 303) and N["defaults_after"] == "pharmacy" and N["lanes_page"] == [200, True, True], (N["lanes_reception"], N["lanes_set"], N["defaults_after"], N["lanes_page"]))

print("-- 3  the duplicate guard at capture: the image fingerprint (perceptual, pdftoppm / ImageMagick, hashed in pure Python)")
check("the fingerprints are computed (perceptual dHash: fine 256 bits + coarse 64, not a text one); the same image gives the same hash; a straight re-scan (4%% re-crop) is within 6 coarse bits (%s); a different paper is far (%s); a re-shot with a 2° TILT is NOT near (%s coarse / %s fine) -- the OCR triple's job, said in the README"
      % (N["fp"][2], N["fp"][3], N["fp"][4], N["fp"][5]),
      N["fp"][0] and N["fp"][1] and N["fp"][2] is not None and N["fp"][2] <= 6 and N["fp"][3] is not None and N["fp"][3] > 6 and N["fp"][4] is not None, N["fp"])
check("the same image twice: the second lands REJECTED with dup_of the first, its own stamp kept (void-pair); the straight re-scan is caught (%s%s); the different paper and the tilted re-shot are plain rows, never rejected (%s%s)"
      % (N["dup_a"][6], (" / " + N["dup_a"][7]) if N["dup_a"][7] else "", N["dup_a"][11], (" / " + N["dup_a"][12]) if N["dup_a"][12] else ""),
      N["dup_a"][0] == "draft" and N["dup_a"][1] == "rejected" and N["dup_a"][2] and N["dup_a"][3] == "yes" and N["dup_a"][4] and N["dup_a"][5] is True and N["dup_a"][8] == "draft" and N["dup_a"][9] is None
      and N["dup_a"][10] is None and N["dup_a"][11] == "draft", N["dup_a"])
check("the stamp slip says it in Hindi and names the FIRST stamp ('Yeh bill pehle B-nnnn par scan ho chuka hai — wahi number likho'); the slip's JSON carries the same; a clean slip shows its stamp and polls",
      N["slip_json"][0] == 200 and N["slip_json"][1] and "wahi number likho" in (N["slip_json"][2] or "") and N["slip_html"] == [200, True, True] and N["slip_ok"] == [200, True, True], (N["slip_json"], N["slip_html"], N["slip_ok"]))
check("a PDF is fingerprinted through pdftoppm and, being the same paper as an earlier JPG (a re-scan, not the same capture), is caught -- rejected or amber (pdf made: %s; %s)" % (N["pdf"][0], N["pdf"][3]),
      (not N["pdf"][0]) or (N["pdf"][1] and N["pdf"][2] is True), N["pdf"])

print("-- 4  the duplicate guard after the OCR: the triple, the amber near-miss, the two taps; approve refused")
check("four distinct papers, distinct fingerprints (the image layer's own verdicts on them, cleared for this test: %s); the OCR triple (vendor+bill no+total, case/punctuation free) REJECTS the second; same vendor+total with no bill number -> amber 'maybe' against the ORIGINAL; a different bill number and amount -> clean" % N["t_image_flags"],
      N["triple_fps_distinct"] and N["triple"][0] == ["rejected", True] and N["triple"][1] == ["draft", "maybe", True] and N["triple"][2] == ["draft", None], N["triple"])
check("the checker's list shows the amber row with 'Duplicate' / 'Not duplicate' and the Lane column", all(N["list_amber"]), N["list_amber"])
check("'Not duplicate' keeps it (dup_flag no); 'Duplicate' on another near-miss rejects it with dup_of; both audited", N["dup_no"] in (302, 303) and N["dup_yes"][0] == "maybe" and N["dup_yes"][1] in (302, 303) and N["dup_decided"] == ["no", "rejected", True]
      and any(r["action"] == "duplicate" for r in N["audit"]) and any(r["action"] == "not_duplicate" for r in N["audit"]), (N["dup_no"], N["dup_yes"], N["dup_decided"], N["audit"]))
check("the first bill approves; approving a bill whose triple matches an APPROVED one is refused, the message names the stamp, the bill turns amber", N["approve_A"] in (302, 303) and N["approve_dup"] == ["approved", 302, "draft", "maybe", True], (N["approve_A"], N["approve_dup"]))

print("-- 5  re-lane, late bills, the pre-fill, the gate")
check("re-lane clinic -> pharmacy (manager): lane, kind Pharmacy, status captured; back to clinic (owner): draft; reception refused (403); an approved bill cannot leave clinic; audited from -> to",
      N["relane1"] in (302, 303) and N["relane_after"] == ["pharmacy", "Pharmacy", "captured"] and N["relane2"] in (302, 303) and N["relane_back"] == ["clinic", "Consumable", "draft"] and N["relane_reception"] == 403
      and N["relane_approved"] in (302, 303) and N["relane_approved_after"] == ["clinic", "approved"] and [x["action"] for x in N["relane_audit"]] == ["relane", "relane"], (N["relane_after"], N["relane_back"], N["relane_reception"], N["relane_approved_after"], N["relane_audit"]))
check("a bill scanned now with bill_date 15-Jul carries late_for 2026-07 (the pharmacy lane, S403's pre-fill intact); a current-month bill carries none; a corrected date clears it",
      N["late"][0] == "2026-07" and N["late"][1] == "2026-07-15" and N["late"][2] == "pharmacy" and N["late"][3] is None and N["late_fixed"] is None, (N["late"], N["late_fixed"]))
check("the pre-fill parser keeps lane=pharmacy (S403) and lane=lab_purchase, drops nonsense", N["prefill"] == ["pharmacy", "lab_purchase", False], N["prefill"])
check("reception reaches only its routes: /bills 403, /lanes 403, /intake 200, a bill view 403", N["reception_gate"] == [403, 403, 200, 403], N["reception_gate"])
check("the owner's /purchases carries the month's count per lane; the intake text says a stamped paper is never scanned again", bool(N["lane_line"]) and N["intake_text"], N["lane_line"])

print("-- 6  the Sanjeevni side: scans counted from 01-Sep-2026 (porders.scan_from)")
check("the setting is seeded; 'Bill scan karo' lists the 02-Sep bill and NOT the 25-Aug one; the earliest listed bill is on or after 01-Sep", FN["setting"] == ["2026-09-01"] and FN["porders"][0] is False and FN["porders"][1] is True and (FN["porders"][2] or "9") >= "2026-09-01", FN)
check("the owner's scan-links page lists the 02-Sep bill and not the 25-Aug one; the Purchase orders state agrees", FN["scans_page"] == [False, True] and FN["state_scans"][1] is False and FN["state_scans"][2] is True, (FN["scans_page"], FN["state_scans"]))

print("-- 7  NEGATIVE CONTROLS on the box as it is (the unpatched files, the same crafted papers)")
check("NEGATIVE: the old intake has no lane defaults (sukhveer opens on the two-lane select); the same image twice gives TWO drafts with two stamps; no /lanes, no re-lane route; the slip has no Hindi duplicate line",
      O["intake_sukhveer"] == [False, False] and O["dup_old"] == ["draft", "draft", None, True] and O["routes_old"] == [404, 404] and O["slip_old"][1] is False, (O["intake_sukhveer"], O["dup_old"], O["routes_old"], O["slip_old"]))
check("NEGATIVE: the old finance side lists the 25-Aug bill on 'Bill scan karo' and the scan-links page (since 17-Aug)", FO["porders"][0] is True and FO["scans_page"][0] is True, (FO["porders"], FO["scans_page"]))
check("the old app's reception gate was already right (/bills 403, /intake 200) and stays so", O["reception_gate"] == [403, 200] and N["reception_gate"][0] == 403, (O["reception_gate"], N["reception_gate"]))

print(("WALK_S409 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S409 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
