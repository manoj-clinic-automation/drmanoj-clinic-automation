#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s440.py -- kit S440_SCAN_FLOW. THE REAL finance_app.py (a copy of /root/finance carrying the kit's three files) AND THE REAL
asset app (a copy of /root/assetapp carrying the kit's asset_register.py), in ONE process, over SCRATCH COPIES of finance.db and
assets.db, each driven through Flask's test client (finance: header identity; the asset app: current_user patched -- walk only). The
same walk runs over the box as it is (the negative control). Its own rows are keyed W440: purchase bills under the export md5
'w440...' of suppliers whose names carry WALK, scans stamped 'W440-nn', two crafted papers (a PDF and a photo, made here with
ImageMagick) in the walk's own uploads folder. Every row is found by that key, never by counting; every date is computed from today.
The asset app's list asks finance's read door through the finance test client (asset_register.SCAN_STATUS_FETCH, the walk's hook).

  --app NEW --old OLD                  (copies of /root/finance: the kit's files / the box as it is)
  --assets-new DIR --assets-old DIR    (copies of /root/assetapp likewise)
  --db PATH --assets-db PATH           (the scratch databases; PATH.old is made for the old apps)
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--assets-new", "--assets-old", "--db", "--assets-db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
assert "walk" in a.assets_db or "scratch" in a.assets_db or a.assets_db.startswith("/tmp"), "refusing a non-scratch assets database"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:420] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


TODAY = dt.date.today()
NOW = dt.datetime.now().replace(microsecond=0)
THIS = TODAY.strftime("%Y-%m")
LASTM = (TODAY.replace(day=1) - dt.timedelta(days=1))


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


MD5 = "w440" + hashlib.md5(b"walk_s440").hexdigest()[:28]
# name -> (supplier as Marg prints it, Marg's bill number, days ago, rupees). Names no real supplier's name sits inside.
BILLS = [
    ("k1", "KEDWALK PHARMACEUTICAL", "440101", 5, 1200.39),          # nobody has scanned it: Scan karo
    ("g1", "GUNWALK PHARMA", "A440202", 6, 2300.39),                 # Marg's double entry: the same number in two cases
    ("g2", "GUNWALK PHARMA", "a440202", 6, 2300.39),
    ("c1", "JUBIWALK AGENCIES", "440303", 10, 3456.39),              # a near-match: Haan
    ("c2", "SHIVWALK FORMULATIONS", "440404", 10, 5000.39),          # a near-match: Nahi
    ("c3", "DEEPWALK PHARMA", "440505", 8, 700.39),                  # scanned, then the same paper scanned again
    ("c4", "JUBIWALK AGENCIES", "440304", 10, 777.39),               # a near-match nobody answers: stays "Aapka jawab chahiye"
    ("v1", "WALKESS WALKAY AGENCIES", "440606", 7, 2222.39),         # its scan's vendor is unreadable
    ("v2", "WALKESS WALKAY AGENCIES", "440707", 6, 1111.39),         # the same unreadable spelling once more
    ("v3", "DEALWALK DRUGS", "440808", 5, 900.39),                   # the BUYER read as the vendor
    ("a1", "YUVIWALK SURGICALS", "440911", 4, 14442.39),             # the scan misread the amount
    ("a2", "YUVIWALK SURGICALS", "440912", 4, 2000.39),              # Marg has the amount wrong
    ("a3", "YUVIWALK SURGICALS", "440913", 4, 3000.39),              # neither agrees with the paper
    ("z", "KEDWALK PHARMACEUTICAL", "440990", 1, 50.39),             # Marg's latest bill (so no scan below is "after Marg's last bill")
]
# name -> (vendor as OCR read it, the number OCR read, days ago of the date OCR read, rupees, lane, status, submitted by, in which month)
SCANS = [
    ("sc1", "JUBIWALK AGENCIES", "X-449901", 4, 3456.39, "pharmacy", "captured", "Darpan", 0),
    ("sc2", "SHIVWALK FORMULATIONS", "Y-449902", 4, 5000.39, "pharmacy", "captured", "Darpan", 0),
    ("sc3a", "DEEPWALK PHARMA", "440505", 8, 700.39, "pharmacy", "captured", "Darpan", 0),
    ("sc3b", "DEEPWALK PHARMA", "Z-449903", 3, 700.39, "pharmacy", "captured", "Darpan", 0),
    ("sc4", "JUBIWALK AGENCIES", "X-449910", 4, 777.39, "pharmacy", "captured", "Darpan", 0),
    ("sv1", "XQZ TRADRS W440", "Q-449904", 7, 2222.39, "pharmacy", "captured", "Darpan", 0),
    ("sv2", "XQZ TRADRS W440", "R-449905", 6, 1111.39, "pharmacy", "captured", "Darpan", 0),
    ("sv3", "M/S SANJEEVNI MEDICOS", "T-449906", 5, 900.39, "pharmacy", "captured", "Darpan", 0),
    ("sv4", "ZZKOI NAHI W440", "U-449907", 2, 321.39, "pharmacy", "captured", "Darpan", 0),
    ("sa1", "YUVIWALK SURGICALS", "YS/440911", 4, 1444.39, "pharmacy", "captured", "Darpan", 0),
    ("sa2", "YUVIWALK SURGICALS", "YS/440912", 4, 2500.39, "pharmacy", "captured", "Darpan", 0),
    ("sa3", "YUVIWALK SURGICALS", "YS/440913", 4, 3500.39, "pharmacy", "captured", "Darpan", 0),
    ("sw", "KEDWALK PHARMACEUTICAL", "A0449908", 2, 4321.39, "pharmacy", "captured", "Darpan", 0),
    ("sg", "KEDWALK PHARMACEUTICAL", "G-449909", 2, 99.39, "pharmacy", "captured", "Darpan", 0),
    ("cl1", "W440 CLINIC VENDOR", "C-1", 1, 10.0, "clinic", "draft", "Darpan", 0),            # another lane: not on "my lane"
    ("lm1", "KEDWALK PHARMACEUTICAL", "L-449911", 35, 11.39, "pharmacy", "captured", "Darpan", 1),   # last month: not on "this month"
    ("rj1", "KEDWALK PHARMACEUTICAL", "J-449912", 1, 12.39, "pharmacy", "rejected", "Darpan", 0),    # rejected: folded away
    ("od1", "W440 CLINIC VENDOR", "C-2", 35, 13.0, "clinic", "draft", "Darpan", 1),           # a draft of an earlier month: folded away
    ("x1", "KEDWALK PHARMACEUTICAL", "O-449913", 1, 14.39, "pharmacy", "captured", "Alisha", 0),     # someone else's pharmacy scan
    ("x2", "W440 CLINIC VENDOR", "C-3", 1, 15.0, "clinic", "draft", "Alisha", 0),             # someone else's clinic bill
] + [("f%02d" % i, "KEDWALK PHARMACEUTICAL", "F-4498%02d" % i, 1, 20.39 + i, "pharmacy", "captured", "Darpan", 0) for i in range(1, 17)]
KIND = {"pharmacy": "Pharmacy", "clinic": "Consumable"}
UP = os.path.join(os.path.dirname(os.path.abspath(a.assets_db)), "w440_uploads")
os.makedirs(UP, exist_ok=True)
subprocess.run(["convert", "-size", "600x800", "xc:white", "-fill", "black", "-pointsize", "40", "-draw", "text 60,120 'W440 PAPER'", "-draw", "rectangle 60,200 540,260",
                "-draw", "rectangle 60,400 300,430", os.path.join(UP, "w440_paper.jpg")], check=True)
subprocess.run(["convert", os.path.join(UP, "w440_paper.jpg"), os.path.join(UP, "w440_paper.pdf")], check=True)
subprocess.run(["convert", "-size", "600x800", "xc:white", "-fill", "black", "-pointsize", "40", "-draw", "text 60,700 'W440 NEW BILL'", "-draw", "rectangle 300,100 560,520",
                "-draw", "rectangle 40,560 200,600", os.path.join(UP, "w440_new.jpg")], check=True)


def craft(fin, ast):
    F = sqlite3.connect(fin, timeout=30)
    A = sqlite3.connect(ast, timeout=30)
    F.execute("INSERT OR REPLACE INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
              (MD5, "BILLWISE", "W440_WALK", D(20), D(1), NOW.strftime("%Y%m%d-%H%M%S"), NOW.isoformat(), len(BILLS), 0))
    ids = {"bills": {}, "scans": {}, "stamps": {}}
    for name, sup, bno, ago, rs in BILLS:
        p = int(round(rs * 100))
        cur = F.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, cash_p, credit_p, amount_p, source_md5, bw_md5, bw_amount_p, date_src) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (sup, sup, bno, D(ago), D(ago)[:7], 0, p, p, MD5, MD5, p, "BILLWISE"))
        ids["bills"][name] = cur.lastrowid
    for i, (name, vendor, bno, ago, rs, lane, status, by, back) in enumerate(SCANS):
        at = dt.datetime.combine(LASTM if back else TODAY, dt.time(12, 0)) - dt.timedelta(minutes=i)      # noon, so no row slips into another day
        stamp = "W440-%02d" % (i + 1)
        cur = A.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, notes, created_at, stamp_no, status, ocr_status, lane, submitted_by, submitted_at, source_stored, source_orig) "
                        "VALUES (?,?,?,?,?,?,?,?,?,'read',?,?,?,?,?)",
                        (KIND[lane], vendor, bno, D(ago), rs, "W440 walk", at.strftime("%Y-%m-%d %H:%M:%S"), stamp, status, lane, by, at.strftime("%Y-%m-%d %H:%M"),
                         "w440_paper.pdf" if i % 2 == 0 else "w440_paper.jpg", "w440"))
        ids["scans"][name] = cur.lastrowid
        ids["stamps"][name] = stamp
    F.commit()
    A.commit()
    F.close()
    A.close()
    return ids


copydb(a.db, a.db + ".old")
copydb(a.assets_db, a.assets_db + ".old")
W = craft(a.db, a.assets_db)
W_old = craft(a.db + ".old", a.assets_db + ".old")
assert W == W_old, "the crafted rows must carry the same ids on both sides"
print("-- scratch copies made for the old apps; %d purchase bills (export %s) and %d scans (W440-01..%02d) crafted on both; two crafted papers in %s"
      % (len(BILLS), MD5[:8], len(SCANS), len(SCANS), UP))

# The six real near-matches the brief names (supplier as Marg keys it, Marg's bill number): found BY KEY on the copy of today's data.
REAL6 = [["L.K. DRUG HOUSE", "75904"], ["L.K. DRUG HOUSE", "78354"], ["ESSENTIAL PHARMA", "EP002243"], ["SAISUN PHARMA PVT. LTD", "IP006767"],
         ["A.A. PHARMACEUTICALS", "416"], ["KEDAR PHARMACEUTICAL", "189"]]

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re, io
from urllib.parse import quote
APP = os.environ["APPDIR"]; AST = os.environ["ASSETSDIR"]
sys.path.insert(0, AST); sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
os.environ.pop("SARVAM_API_KEY", None)
NEW = os.environ["MODE"] == "new"
W = json.loads(os.environ["W440"]); SC = W["scans"]; BL = W["bills"]; ST = W["stamps"]
REAL6 = json.loads(os.environ["REAL6"])
SCN = {v: k for k, v in SC.items()}; BLN = {v: k for k, v in BL.items()}
import finance_app as fa
import purchase_app as pa, porders
import asset_register as ar
fc = fa.app.test_client(); ac = ar.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def FG(u, p):
    r = fc.get(p, headers=(H(u) if u else {})); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def FP(u, p, b=None):
    r = fc.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
USERS = {"manoj": {"id": 1, "username": "manoj", "display_name": "Dr Manoj", "role": "owner", "active": 1, "password_hash": ""},
         "manager": {"id": 3, "username": "manager", "display_name": "Manager", "role": "manager", "active": 1, "password_hash": ""}}
for u in ("darpan", "alisha", "sukhveer"):
    USERS[u] = {"id": None, "username": u, "display_name": u.title(), "role": "reception", "active": 1}
CUR = {"u": "manoj"}
ar.current_user = lambda: USERS[CUR["u"]]
def AG(u, p, **kw):
    CUR["u"] = u; r = ac.get(p, **kw); return [r.status_code, r.get_data(as_text=True) if (r.mimetype or "").startswith("text") else r.mimetype, r.headers.get("Location", "")]
def AP(u, p, data, **kw):
    CUR["u"] = u; r = ac.post(p, data=data, follow_redirects=False, **kw); return [r.status_code, r.headers.get("Location", ""), r.get_data(as_text=True)[:200]]
if NEW:
    ar.SCAN_STATUS_FETCH = lambda ids, username: fc.get("/finance/porders/api/scan-status?ids=" + ",".join(str(i) for i in ids), headers=H(username)).get_json(silent=True)
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
adb = sqlite3.connect(os.environ["ASSETS_DB"], timeout=30); adb.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
aq = lambda s, *a: [dict(r) for r in adb.execute(s, a).fetchall()]
one = lambda s, *a: db.execute(s, a).fetchone()[0]
def link(b):
    r = q("SELECT asset_bill_id, grade, matched_on FROM purchase_scan_link WHERE bill_id=?", BL[b])
    return [SCN.get(r[0]["asset_bill_id"], r[0]["asset_bill_id"]), r[0]["grade"], r[0]["matched_on"]] if r else None
def audits(action, ref):
    return [[r["who"], json.loads(r["detail"] or "{}")] for r in q("SELECT who, detail FROM purchase_audit WHERE action=? AND ref=? ORDER BY id", action, str(ref))]
def srow(s):
    r = q("SELECT * FROM purchase_scan_state WHERE asset_bill_id=?", SC[s]); return r[0] if r else None
def count(html, needle):
    return html.count(needle) if isinstance(html, str) else -1
out = {}
st = FG("darpan", "/finance/porders/api/state")
out["state_code"] = st[0]; S0 = st[1] if isinstance(st[1], dict) else {}
out["has_kaam"] = "kaam" in S0
old_list = [b["bill_id"] for b in (S0.get("scans") or {}).get("bills", [])]
out["s403_list"] = {k: (BL[k] in old_list) for k in ("k1", "c1", "c2", "c3", "v1", "g1", "g2")}
# the six real near-matches, by key
real = []
for sup, bno in REAL6:
    r = q("SELECT b.id FROM purchase_bill b WHERE b.supplier_norm=? AND b.bill_no=? AND " + pa.EFF_BILL, sup, bno)
    if r:
        real.append(r[0]["id"])
linked_real = {x["bill_id"] for x in q("SELECT bill_id FROM purchase_scan_link")} & set(real)
out["real6"] = dict(found=len(real), linked=len(linked_real), in_old_list=sum(1 for i in real if i in old_list))
page = FG("darpan", "/finance/porders")
out["page"] = [page[0], count(page[1], 'id="s440bar"'), count(page[1], "← BACK"), count(page[1], 'id="s440up"'), "Scan ka kaam (%d)" in page[1], "Bill scans pending" in page[1]]
out["page_src"] = page[1] if NEW else ""
pg = FG("manoj", "/finance/purchase/page/scans")
out["scans_page"] = [pg[0], count(pg[1], 'id="s440bar"'), count(pg[1], "← BACK"), count(pg[1], 'id="s440up"'), 'href="/portal"' in pg[1]]
# ---- the asset app, before anything is tapped
ik = AG("darpan", "/intake")
out["intake"] = [ik[0], count(ik[1], "class=s440bar"), count(ik[1], "← BACK"), count(ik[1], "id=s440up"), "<header>" in ik[1],
                 ik[1].find("id=scanroot"), ik[1].find("id=intake_lane"), ik[1].find("id=intake_month"), ik[1].find("id=intake_note"), ik[1].find("Kaise?")]
out["bills_darpan"] = AG("darpan", "/bills")[0]
out["bill_darpan"] = AG("darpan", "/bills/%d" % SC["sc1"])[0]
out["thumb"] = AG("darpan", "/bills/%d/thumb" % SC["sc1"])[:2]
io_ = AG("manoj", "/intake")
out["intake_owner"] = [io_[0], "<header>" in io_[1], "Asset Register" in io_[1], count(io_[1], "class=s440bar")]
bo = AG("manoj", "/bills")
out["bills_owner"] = [bo[0], "<header>" in bo[1], count(bo[1], "class=s440bar"), "<th>Lane</th>" in bo[1]]
sl = AG("darpan", "/intake/slip/%d" % SC["sw"])
out["slip_old"] = [sl[0], "Ho gaya" in sl[1], "Scan another" in sl[1]]
if not NEW:
    out["door_old"] = FG("darpan", "/finance/porders/api/scan-status?ids=%d" % SC["sc1"])[0]
    out["confirm_old"] = FP("darpan", "/finance/porders/api/scan/confirm", {"scan": SC["sc1"], "bill": BL["c1"], "yes": True})[0]
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit

# =================================================================== NEW ONLY
K0 = S0["kaam"]
def shape(K):
    return dict(scan=sorted(BLN[x["bill_id"]] for x in K["scan"] if x["bill_id"] in BLN), confirm=sorted(SCN[x["scan"]] for x in K["confirm"] if x["scan"] in SCN),
                vendor=sorted(SCN[x["scan"]] for x in K["vendor"] if x["scan"] in SCN), amount=sorted(SCN[x["scan"]] for x in K["amount"] if x["scan"] in SCN),
                wait=sorted(SCN[x["scan"]] for x in K["wait"] if x["scan"] in SCN))
def line(K, grp, name):
    key = "bill_id" if grp == "scan" else "scan"; want = BL[name] if grp == "scan" else SC[name]
    return next((x for x in K[grp] if x[key] == want), None)
def kaam(u="darpan"):
    return FG(u, "/finance/porders/api/state")[1]["kaam"]
out["k0"] = shape(K0)
out["k0_counts"] = [K0["n"], K0["counts"], K0["n"] == K0["counts"]["scan"] + K0["counts"]["confirm"] + K0["counts"]["vendor"] + K0["counts"]["amount"],
                    all(K0["counts"][g] == len(K0[g]) + (len(K0["received"]) if g == "scan" else 0) for g in ("scan", "confirm", "vendor", "amount", "wait"))]
out["k0_lines"] = dict(k1=line(K0, "scan", "k1"), g1=line(K0, "scan", "g1"), sc1=line(K0, "confirm", "sc1"), sc3b=line(K0, "confirm", "sc3b"), sv1=line(K0, "vendor", "sv1"),
                       sa1=line(K0, "amount", "sa1"), sw=line(K0, "wait", "sw"))
out["suppliers"] = ["WALKESS WALKAY AGENCIES" in K0["suppliers"], "DEALWALK DRUGS" in K0["suppliers"], K0["suppliers"] == sorted(K0["suppliers"])]
real_open = [i for i in real if i not in linked_real]
refused = set()
for r in q("SELECT hint_no FROM purchase_scan_state WHERE COALESCE(hint_no,'')<>''"):
    refused |= {int(x) for x in r["hint_no"].split(",") if x.strip().isdigit()}
real_ask = [i for i in real_open if i not in refused]
out["real6"].update(open=len(real_open), asked=len(real_ask), in_scan=sum(1 for i in real_ask if any(x["bill_id"] == i for x in K0["scan"])),
                    in_confirm=sum(1 for i in real_ask if any(x["bill_id"] == i for x in K0["confirm"])))
# the double entry: shown once, the extra row on the WRONG list, audited once however often the list is read
kaam(); kaam("manoj")
g2 = q("SELECT verdict, verdict_by, wrong_amount_p, reason FROM purchase_bill WHERE id=?", BL["g2"])[0]
out["double"] = [g2["verdict"], g2["verdict_by"], g2["wrong_amount_p"], (g2["reason"] or "")[:17], len(audits("double_entry", BL["g2"])),
                 q("SELECT verdict FROM purchase_bill WHERE id=?", BL["g1"])[0]["verdict"]]
ids0 = [SC[k] for k in ("sc1", "sv1", "sa1", "sw", "sc3a", "cl1")]
d0 = FG("darpan", "/finance/porders/api/scan-status?ids=" + ",".join(str(i) for i in ids0))
out["door0"] = [d0[0], {SCN[int(k)]: v["code"] for k, v in (d0[1].get("status") or {}).items()}, {SCN[int(k)]: v["word"] for k, v in (d0[1].get("status") or {}).items()}]
out["door_nologin"] = FG(None, "/finance/porders/api/scan-status?ids=%d" % SC["sc1"])[0]
sm = FG("darpan", "/finance/porders/api/summary")[1]
pg = FG("manoj", "/finance/purchase/page/scans")
m = re.search(r"what the staff see on Purchase orders \((\d+) to act on\)", pg[1])
m2 = re.search(r"To scan (\d+) · Is this the bill\? (\d+) · Choose the supplier (\d+) · Match the amount (\d+) · Waiting for Marg (\d+)", pg[1])
K1 = kaam()
out["agree"] = [K1["n"], (sm.get("scan_kaam") or {}).get("n"), int(m.group(1)) if m else None,
                [K1["counts"][g] for g in ("scan", "confirm", "vendor", "amount", "wait")], [(sm.get("scan_kaam") or {}).get(g) for g in ("scan", "confirm", "vendor", "amount", "wait")],
                [int(x) for x in m2.groups()] if m2 else None, count(pg[1], 'id="s440groups"'), ST["sc1"] in pg[1] and ST["sv1"] in pg[1] and ST["sa1"] in pg[1]]
pf = FG("manoj", "/finance/purchase/page/scans?from=/finance/approvals"); pe = FG("manoj", "/finance/purchase/page/scans?from=//evil.example/x")
out["scans_from"] = ['id="s440back" href="/finance/approvals"' in pf[1], 'id="s440back" href="/portal"' in pe[1]]
# ---- a viewer may not answer; the three answers
senders = one("SELECT value FROM setting WHERE key='porders.senders'")
db.execute("UPDATE setting SET value=? WHERE key='porders.senders'", (",".join(x for x in senders.split(",") if x.strip().lower() != "alisha"),)); db.commit()
va = FP("alisha", "/finance/porders/api/scan/confirm", {"scan": SC["sc1"], "bill": BL["c1"], "yes": True})       # a login of the unit that is NOT a sender: view only
out["viewer"] = [va[0], (va[1] or {}).get("error"), link("c1"), FP("alisha", "/finance/porders/api/scan/vendor", {"scan": SC["sv1"], "vendor": "WALKESS WALKAY AGENCIES"})[0],
                 FP("alisha", "/finance/porders/api/scan/amount", {"scan": SC["sa1"], "paper": "14442.39"})[0], FG("alisha", "/finance/porders/api/scan-status?ids=%d" % SC["sc1"])[0]]
db.execute("UPDATE setting SET value=? WHERE key='porders.senders'", (senders,)); db.commit()
out["stale"] = FP("darpan", "/finance/porders/api/scan/confirm", {"scan": SC["sc1"], "bill": BL["c2"], "yes": True})[0]
r = FP("darpan", "/finance/porders/api/scan/confirm", {"scan": SC["sc1"], "bill": BL["c1"], "yes": True})
out["haan"] = [r[0], r[1].get("linked"), link("c1"), one("SELECT scan_bill_id FROM purchase_bill WHERE id=?", BL["c1"]) == SC["sc1"],
               [[x[0], x[1].get("grade"), x[1].get("rule"), x[1].get("scan") == SC["sc1"]] for x in audits("scan_link", BL["c1"])]]
r = FP("darpan", "/finance/porders/api/scan/confirm", {"scan": SC["sc2"], "bill": BL["c2"], "yes": False})
out["nahi"] = [r[0], r[1].get("linked"), link("c2"), (srow("sc2") or {}).get("hint_no") == str(BL["c2"]), (srow("sc2") or {}).get("why"),
               len(audits("scan_hint_refused", BL["c2"]))]
r = FP("darpan", "/finance/porders/api/scan/confirm", {"scan": SC["sc3b"], "bill": BL["c3"], "yes": True})
out["second"] = [r[0], r[1].get("second_scan"), link("c3"), (srow("sc3b") or {}).get("why"), (srow("sc3b") or {}).get("dup_cand") == SC["sc3a"],
                 len(audits("scan_dup_confirmed", BL["c3"]))]
K2 = kaam(); out["k2"] = shape(K2); out["k2_dup"] = K2["counts"]["dup"] - K0["counts"]["dup"]
# ---- Supplier chuno
out["vendor_bad"] = FP("darpan", "/finance/porders/api/scan/vendor", {"scan": SC["sv1"], "vendor": "NOT A SUPPLIER W440"})[0]
r = FP("darpan", "/finance/porders/api/scan/vendor", {"scan": SC["sv1"], "vendor": "WALKESS WALKAY AGENCIES"})
al = q("SELECT ocr_norm, supplier_norm, scan_id, who FROM purchase_scan_alias WHERE supplier_norm='WALKESS WALKAY AGENCIES'")
out["vendor1"] = [r[0], r[1].get("learned"), r[1].get("linked"), link("v1"), link("v2"), [[x["ocr_norm"], x["scan_id"] == SC["sv1"], x["who"]] for x in al],
                  [[x[0], x[1].get("learned")] for x in audits("scan_vendor_chosen", SC["sv1"])], len(audits("alias_learn", al[0]["ocr_norm"])) if al else 0]
out["vendor_again"] = FP("darpan", "/finance/porders/api/scan/vendor", {"scan": SC["sv1"], "vendor": "WALKESS WALKAY AGENCIES"})[0]
r = FP("darpan", "/finance/porders/api/scan/vendor", {"scan": SC["sv3"], "vendor": "DEALWALK DRUGS"})
out["vendor_buyer"] = [r[0], r[1].get("learned"), r[1].get("linked"), link("v3"), one("SELECT COUNT(*) FROM purchase_scan_alias WHERE supplier_norm='DEALWALK DRUGS'"),
                       (srow("sv3") or {}).get("chosen_vendor")]
r = FP("darpan", "/finance/porders/api/scan/vendor", {"scan": SC["sv4"], "vendor": "-"})
K3 = kaam(); out["k3"] = shape(K3)
out["vendor_none"] = [r[0], r[1].get("linked"), (line(K3, "wait", "sv4") or {}).get("note"), (srow("sv4") or {}).get("chosen_vendor")]
# ---- Amount milao
out["amount_bad"] = FP("darpan", "/finance/porders/api/scan/amount", {"scan": SC["sa1"], "paper": "12a"})[0]
r = FP("darpan", "/finance/porders/api/scan/amount", {"scan": SC["sa1"], "paper": "14442.39"})
out["amt_scan_wrong"] = [r[0], r[1].get("outcome"), link("a1"), (srow("sa1") or {}).get("paper_amount"), (srow("sa1") or {}).get("amount_state"),
                         aq("SELECT total_amount FROM bills WHERE id=?", SC["sa1"])[0]["total_amount"], q("SELECT verdict FROM purchase_bill WHERE id=?", BL["a1"])[0]["verdict"]]
r = FP("darpan", "/finance/porders/api/scan/amount", {"scan": SC["sa2"], "paper": "2,500.39"})
a2 = q("SELECT verdict, verdict_by, wrong_amount_p, reason FROM purchase_bill WHERE id=?", BL["a2"])[0]
out["amt_marg_wrong"] = [r[0], r[1].get("outcome"), link("a2"), a2["verdict"], a2["verdict_by"], a2["wrong_amount_p"], a2["reason"],
                         [[x[0], x[1].get("via"), x[1].get("wrong_amount_p")] for x in audits("verdict", BL["a2"])]]
r = FP("darpan", "/finance/porders/api/scan/amount", {"scan": SC["sa3"], "paper": "3300"})
needs = [l["text"] for l in porders.needs_you_lines(db)]
ny = FG("manoj", "/finance/sanjeevni/api/needs-you")
out["amt_owner"] = [r[0], r[1].get("outcome"), link("a3"), (srow("sa3") or {}).get("amount_state"), q("SELECT verdict FROM purchase_bill WHERE id=?", BL["a3"])[0]["verdict"],
                    [t for t in needs if "440913" in t], any("440913" in (l.get("text") or "") for l in ((ny[1] or {}).get("lines") or [])) if isinstance(ny[1], dict) else None]
out["amount_again"] = FP("darpan", "/finance/porders/api/scan/amount", {"scan": SC["sa1"], "paper": "14442.39"})[0]
K4 = kaam(); out["k4"] = shape(K4)
# ---- what a person decided rides every pass of the matcher
r = FP("manoj", "/finance/purchase/api/rematch")
p = __import__("subprocess").run([sys.executable, "-B", os.path.join(APP, "purchase_app.py"), "rematch"], env=dict(os.environ), cwd=APP, stdout=-1, stderr=-1, text=True)
K5 = kaam(); out["k5"] = shape(K5)
out["persist"] = [r[0], p.returncode, link("c1"), link("a1"), link("c2"), (srow("sc2") or {}).get("hint_no") == str(BL["c2"]), (srow("sc3b") or {}).get("why"),
                  (srow("sa1") or {}).get("paper_amount"), (srow("sa3") or {}).get("amount_state"), (srow("sv4") or {}).get("chosen_vendor"), len(audits("double_entry", BL["g2"]))]
# =================================================================== the asset app
def bar(html):
    m_ = re.search(r'<div class=s440bar><a class=s440back href="([^"]*)">← BACK</a><span class=s440name>([^<]*)</span></div>', html or "")
    return [count(html, "class=s440bar"), count(html, "← BACK"), count(html, "id=s440up"), m_.group(1) if m_ else None, m_.group(2) if m_ else None]
pages = {}
pages["intake"] = bar(AG("darpan", "/intake")[1])
pages["intake_from"] = bar(AG("darpan", "/intake?from=/finance/porders")[1])
pages["intake_evil"] = bar(AG("darpan", "/intake?from=https://evil.example/x")[1])
pages["intake_evil2"] = bar(AG("darpan", "/intake?from=//evil.example/x")[1])
pages["intake_assets_host"] = bar(AG("darpan", "/intake", base_url="https://assets.dr-manoj.in")[1])
pages["intake_scanapp"] = bar(AG("darpan", "/scanapp/intake", base_url="https://followup.dr-manoj.in")[1])
pages["list_staff"] = bar(AG("darpan", "/bills")[1])
pages["list_owner"] = bar(AG("manoj", "/bills")[1])
pages["list_owner_from"] = bar(AG("manoj", "/bills?from=/finance/purchase/page/scans")[1])
pages["bill_staff"] = bar(AG("darpan", "/bills/%d?from=/scanapp/bills" % SC["sw"])[1])
pages["bill_owner"] = bar(AG("manoj", "/bills/%d" % SC["sw"])[1])
pages["lanes_owner"] = bar(AG("manoj", "/lanes")[1])
pages["slip"] = bar(AG("darpan", "/intake/slip/%d" % SC["sw"])[1])
out["pages"] = pages
out["menu"] = {"darpan_intake": "<header>" in AG("darpan", "/intake")[1], "darpan_list": "<header>" in AG("darpan", "/bills")[1], "darpan_bill": "<header>" in AG("darpan", "/bills/%d" % SC["sw"])[1],
               "sukhveer_intake": "<header>" in AG("sukhveer", "/intake")[1], "owner_intake": "<header>" in AG("manoj", "/intake")[1], "owner_list": "<header>" in AG("manoj", "/bills")[1],
               "manager_list": "<header>" in AG("manager", "/bills")[1]}
ik = AG("darpan", "/intake")[1]
idx = [ik.find(x) for x in ("id=lane_line", "id=scanroot", "id=lanebox", "id=intake_lane", "id=intake_month", "id=intake_note", "Kaise?", "Basic upload")]
mline = re.search(r"<span id=lane_line>([^<]*)</span>", ik)
out["intake_new"] = dict(idx=idx, line=mline.group(1) if mline else None, month=ar._month_label(THIS) if False else ar._month_label(dt.date.today().strftime("%Y-%m")),
                         lanebox_hidden='id=lanebox style="display:none' in ik, badlo="badlo" in ik, kaise_folded=bool(re.search(r"<details class=card id=kaise><summary", ik)),
                         text_kept=all(t in ik for t in ("Photograph the paper bill", "A paper that already carries a B-number is never scanned again", "Old bills from last month?")),
                         old_h2="Scan a new purchase bill" in ik, sel=(re.search(r'<option value="([a-z_]+)" selected', ik) or [None, None])[1],
                         sel_sukhveer=(re.search(r'<option value="([a-z_]+)" selected', AG("sukhveer", "/intake")[1]) or [None, None])[1])
k1 = line(K5, "scan", "k1")
out["intake_link"] = k1["intake"] if k1 else None
ip = AG("darpan", (k1["intake"] if k1 else "/intake").replace("/scanapp", "", 1))
mcfg = re.search(r"window\.SCANNER_CONFIG = (\{.*?\});</script>", ip[1], re.S)
cfg = json.loads(mcfg.group(1)) if mcfg else {}
out["prefill"] = [ip[0], cfg.get("uploadFields"), cfg.get("backUrl"), bar(ip[1]), '<input type=hidden name=from value="/finance/porders">' in ip[1]]
# ---- a real submission through the intake's own route, opened from the Scan karo line of bill 440101
from werkzeug.datastructures import FileStorage
with open(os.path.join(os.environ["ASSETS_UPLOADS"], "w440_new.jpg"), "rb") as fh:
    raw = fh.read()
sub = AP("darpan", "/intake/submit", {"lane": "pharmacy", "bill_month": dt.date.today().strftime("%Y-%m"), "from": "/finance/porders", "vendor": "KEDWALK PHARMACEUTICAL", "bill_no": "440101",
                                       "bill_date": q("SELECT bill_date FROM purchase_bill WHERE id=?", BL["k1"])[0]["bill_date"], "amount": "1200.39", "note": "W440 walk",
                                       "bill_file": (io.BytesIO(raw), "w440_new.jpg")}, content_type="multipart/form-data")
mnew = re.search(r"/intake/slip/(\d+)", sub[1])
newid = int(mnew.group(1)) if mnew else 0
nb = (aq("SELECT * FROM bills WHERE id=?", newid) or [{}])[0]
out["submit"] = [sub[0], sub[1], nb.get("kind"), nb.get("status"), nb.get("lane"), nb.get("vendor"), nb.get("bill_no"), nb.get("total_amount"), bool(nb.get("stamp_no")), nb.get("submitted_by")]
sp = AG("darpan", sub[1]) if newid else [0, "", ""]
out["slip_new"] = dict(code=sp[0], bar=bar(sp[1]), ho_gaya="Ho gaya" in sp[1], stamp=bool(nb.get("stamp_no")) and ("<span id=slipstamp" in sp[1]) and (nb.get("stamp_no") or "?") in sp[1],
                       likh_do="bill par likh do" in sp[1],
                       agla=(re.search(r'<a class="btn s440big" href="([^"]*)"[^>]*>Agla bill scan karo</a>', sp[1]) or [None, None])[1],
                       back=(re.search(r'<a class="btn s440big" href="([^"]*)"[^>]*>← BACK to the list</a>', sp[1]) or [None, None])[1],
                       polls="json=1" in sp[1], today="Aaj ke scan" in sp[1], today_row=(nb.get("stamp_no") or "?") in sp[1].split("Aaj ke scan")[-1], old_text="Scan another" in sp[1])
sp2 = AG("darpan", "/intake/slip/%d" % SC["cl1"])[1]
out["slip_clinic_back"] = (re.search(r'<a class="btn s440big" href="([^"]*)"[^>]*>← BACK to the list</a>', sp2) or [None, None])[1]
K6 = kaam(); out["k6"] = shape(K6)
out["new_link"] = [link("k1"), newid and (q("SELECT asset_bill_id FROM purchase_scan_link WHERE bill_id=?", BL["k1"]) or [{}])[0].get("asset_bill_id") == newid]
# ---- the list of a scanning login
def rows_of(html):
    return re.findall(r"<tr class=s440row>.*?</tr>", html, re.S)
def word_of(html, stamp):
    r_ = next((x for x in rows_of(html) if (">%s<" % stamp) in x), None)
    return re.sub(r"<[^>]+>", "", r_.split("<td>")[-1]).strip() if r_ else None
ls = AG("darpan", "/bills")[1]
full = AG("darpan", "/bills?n=500")[1]
alln = AG("darpan", "/bills?lane=&month=&n=500")[1]
lastm = AG("darpan", "/bills?month=%s&n=500" % os.environ["LASTM"])[1]
old_part = ls.split("purane drafts (")[-1] if "purane drafts (" in ls else ""
out["list"] = dict(rows=len(rows_of(ls)), aur="aur dikhao" in ls, rows_full=len(rows_of(full)), aur_full="aur dikhao" in full,
                   mine_only=all((">%s<" % ST[k]) not in full for k in ("x1", "x2")), my_lane=(">%s<" % ST["cl1"]) not in "".join(rows_of(full)), this_month=(">%s<" % ST["lm1"]) not in "".join(rows_of(full)),
                   all_lanes=(">%s<" % ST["cl1"]) in "".join(rows_of(alln)) and (">%s<" % ST["lm1"]) in "".join(rows_of(alln)), last_month=(">%s<" % ST["lm1"]) in "".join(rows_of(lastm)),
                   lane_sel='<option value="pharmacy" selected' in ls, month_sel=('<option value="%s" selected' % dt.date.today().strftime("%Y-%m")) in ls,
                   old_folded=bool(re.search(r"<details class=card[^>]*><summary[^>]*>purane drafts \(\d+\) ▾</summary>", ls)), old_has_rejected=ST["rj1"] in old_part,
                   rejected_not_in_rows=(">%s<" % ST["rj1"]) not in "".join(rows_of(full)), old_draft_all=ST["od1"] in (alln.split("purane drafts (")[-1] if "purane drafts (" in alln else ""),
                   status_head="<th>Status</th>" in ls, filters=all(x in ls for x in ("name=q", "name=lane", "name=month")))
out["words"] = {k: word_of(full, ST[k]) for k in ("sc3a", "sw", "sc4", "sc3b", "sc1", "sa1")}
out["word_link"] = bool(re.search(r'<a href="/finance/porders" style="font-weight:700;color:#b3261e">Aapka jawab chahiye → Scan ka kaam</a>', full))
out["word_new"] = word_of(full, nb.get("stamp_no") or "?")
keep = ar.SCAN_STATUS_FETCH
ar.SCAN_STATUS_FETCH = lambda ids, username: (_ for _ in ()).throw(RuntimeError("the door is shut"))
out["word_failsoft"] = word_of(AG("darpan", "/bills?n=500")[1], ST["sc3a"])
ar.SCAN_STATUS_FETCH = keep
ol = AG("manoj", "/bills")[1]
out["list_owner"] = [len(rows_of(ol)), "<th>Lane</th>" in ol, "purane drafts" in ol, "aur dikhao" in ol]
bv = AG("darpan", "/bills/%d" % SC["sw"])
out["bill_staff"] = [bv[0], "Marg ka intezaar (Amir)" in bv[1], "Scan dekho" in bv[1], any(x in bv[1] for x in ("Approve", "Reject", "name=lane", "<form"))]
out["gates"] = dict(other_bill=AG("darpan", "/bills/%d" % SC["x1"])[0], other_clinic_bill=AG("darpan", "/bills/%d" % SC["x2"])[0],
                    thumb_pdf=AG("darpan", "/bills/%d/thumb" % SC["sc1"])[:2], thumb_jpg=AG("darpan", "/bills/%d/thumb" % SC["sc2"])[:2],
                    thumb_other_pharmacy=AG("darpan", "/bills/%d/thumb" % SC["x1"])[0], file_other_pharmacy=AG("darpan", "/bills/%d/file" % SC["x1"])[0],
                    thumb_other_clinic=AG("darpan", "/bills/%d/thumb" % SC["x2"])[0], file_other_clinic=AG("darpan", "/bills/%d/file" % SC["x2"])[0],
                    thumb_rejected=AG("alisha", "/bills/%d/thumb" % SC["rj1"])[0], lanes=AG("darpan", "/lanes")[0], purchases=AG("darpan", "/purchases")[0],
                    approve=AP("darpan", "/bills/%d/approve" % SC["cl1"], {})[0], dup=AP("darpan", "/bills/%d/dup" % SC["sw"], {"what": "yes"})[0],
                    month=AP("darpan", "/bills/%d/month" % SC["sw"], {"bill_month": dt.date.today().strftime("%Y-%m")})[0], owner_thumb=AG("manoj", "/bills/%d/thumb" % SC["sc1"])[0])
# ---- Galat lane
out["lane_refused"] = [AP("darpan", "/bills/%d/lane" % SC["sg"], {"lane": "owner_expense"})[0], AP("darpan", "/bills/%d/lane" % SC["sg"], {"lane": "pharmacy"})[0],
                       AP("darpan", "/bills/%d/lane" % SC["cl1"], {"lane": "other_doc"})[0], AP("darpan", "/bills/%d/lane" % SC["rj1"], {"lane": "clinic"})[0]]
in_wait_before = line(K6, "wait", "sg") is not None
r = AP("alisha", "/bills/%d/lane" % SC["sg"], {"lane": "clinic", "back": "/finance/porders"})
sgr = aq("SELECT lane, kind, status FROM bills WHERE id=?", SC["sg"])[0]
K7 = kaam()
out["galat_lane"] = [r[0], r[1], sgr, in_wait_before, line(K7, "wait", "sg") is None,
                     [[x["who"], json.loads(x["detail"] or "{}")] for x in aq("SELECT who, detail FROM bill_audit WHERE bill_id=? AND action='relane' ORDER BY id", SC["sg"])],
                     (">%s<" % ST["sg"]) not in "".join(rows_of(AG("darpan", "/bills?n=500")[1]))]
out["k7"] = shape(K7)
out["final_agree"] = [K7["n"], (FG("darpan", "/finance/porders/api/summary")[1].get("scan_kaam") or {}).get("n"),
                      int((re.search(r"\((\d+) to act on\)", FG("manoj", "/finance/purchase/page/scans")[1]) or [0, -1])[1])]
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, astdir, mode, dbpath, adb):
    env = dict(os.environ, APPDIR=appdir, ASSETSDIR=astdir, MODE=mode, FINANCE_DB=dbpath, ASSETS_DB=adb, ASSETS_UPLOADS=UP, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"),
               FINANCE_ALLOW_HEADER_AUTH="1", W440=json.dumps(W), REAL6=json.dumps(REAL6), LASTM=LASTM.strftime("%Y-%m"))
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s apps did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, a.assets_old, "old", a.db + ".old", a.assets_db + ".old")
N = probe(a.app, a.assets_new, "new", a.db, a.assets_db)
B, S, STAMP = W["bills"], W["scans"], W["stamps"]
HUB = "/portal"

print("-- 1  Scan ka kaam: five kinds of line, each bill or scan in exactly one (the walk's own rows, found by key)")
k0 = N["k0"]
check("reception's state (200) carries 'kaam'; S403's own list ('scans') is still there, unchanged, for the month-end checklist",
      N["state_code"] == 200 and N["has_kaam"] and N["s403_list"]["k1"] and N["s403_list"]["c1"], N["s403_list"])
check("1 Scan karo: the bill nobody scanned (440101), the three whose scans OCR could not name (440606 / 440707 / 440808), Marg's latest (440990) and the double entry ONCE",
      k0["scan"] == sorted(["k1", "z", "v1", "v2", "v3", "g1"]), k0["scan"])
L = N["k0_lines"]
check("   its line carries supplier, number, date, amount, the days waiting and the S403 pre-filled intake link, which now says where to come back (from=/finance/porders)",
      L["k1"] and L["k1"]["vendor"] == "KEDWALK PHARMACEUTICAL" and L["k1"]["bill_no"] == "440101" and L["k1"]["amount"] == "₹1,200" and L["k1"]["age"] == 5 and L["k1"]["red"] is True
      and L["k1"]["intake"].startswith("/scanapp/intake?lane=pharmacy&vendor=KEDWALK+PHARMACEUTICAL&bill_no=440101") and "amount=1200.39" in L["k1"]["intake"]
      and L["k1"]["intake"].endswith("&from=%2Ffinance%2Fporders"), L["k1"])
check("2 Yahi bill hai?: the three scans whose number was read differently (the same supplier, the same amount to the rupee) and the second scan of a linked bill; their bills are NOT in Scan karo",
      k0["confirm"] == sorted(["sc1", "sc2", "sc3b", "sc4"]) and not any(x in k0["scan"] for x in ("c1", "c2", "c3", "c4")), k0["confirm"])
check("   the line shows the scan's reading and Marg's bill side by side, with the scan's thumbnail and PDF",
      L["sc1"] and L["sc1"]["scan_no"] == "X-449901" and L["sc1"]["scan_amount"] == "₹3,456.39" and L["sc1"]["bill_no"] == "440303" and L["sc1"]["bill_id"] == B["c1"] and L["sc1"]["amount"] == "₹3,456.39"
      and L["sc1"]["stamp"] == STAMP["sc1"] and L["sc1"]["thumb"] == "/scanapp/bills/%d/thumb" % S["sc1"] and L["sc1"]["pdf"] == "/scanapp/bills/%d/file" % S["sc1"] and L["sc1"]["taken_by"] is None,
      L["sc1"])
check("   the scan whose likely bill ALREADY has a scan says so (the first scan's stamp): 'yeh wahi kaagaz hai?'", L["sc3b"] and L["sc3b"]["taken_by"] == S["sc3a"] and L["sc3b"]["taken_stamp"] == STAMP["sc3a"],
      (L["sc3b"] or {}).get("taken_stamp"))
check("3 Supplier chuno: the four scans whose vendor nobody could read (two of one misspelling, the buyer's own name, a name on no list); the supplier list is offered, sorted",
      k0["vendor"] == sorted(["sv1", "sv2", "sv3", "sv4"]) and N["suppliers"] == [True, True, True] and L["sv1"]["scan_no"] == "Q-449904" and L["sv1"]["scan_amount"] == "₹2,222.39", (k0["vendor"], N["suppliers"]))
check("4 Amount milao: the three linked scans whose amount is more than 2% off Marg's; both figures on the line",
      k0["amount"] == sorted(["sa1", "sa2", "sa3"]) and L["sa1"]["scan_amount"] == "₹1,444.39" and L["sa1"]["amount"] == "₹14,442.39" and L["sa1"]["bill_no"] == "440911", (k0["amount"], L["sa1"]))
check("5 Marg ka intezaar: the scans of bills Marg has not sent (the two crafted ones and the sixteen fillers), each with 'Amir ke entry ke baad khud jud jayega'",
      all(x in k0["wait"] for x in ["sw", "sg"] + ["f%02d" % i for i in range(1, 17)]) and L["sw"]["note"] == "Amir ke entry ke baad khud jud jayega", len(k0["wait"]))
check("the count on the section is groups 1-4 (group 5 carries no button and is not counted); every group's count is its lines", N["k0_counts"][2] and N["k0_counts"][3], N["k0_counts"][:2])
src = N["page_src"]


def seg(a_, b_):
    i = src.find(a_)
    j = src.find(b_, i + 1) if b_ else len(src)
    return src[i:j] if i >= 0 and j > i else ""


g = {1: seg(' let g1="";', ' let g2="";'), 2: seg(' let g2="";', ' let g3="";'), 3: seg(' let g3="";', ' let g4="";'), 4: seg(' let g4="";', ' let g5="";'), 5: seg(' let g5="";', " h+=sec(3,")}
acts = {k: [x for x in ("kConfirm(", "kVendor(", "kAmount(", 'L("scan")', "lane(x)") if x in v] for k, v in g.items()}
check("each kind renders exactly its buttons and no other (the page's own script, group by group): 1 = 📷 Scan only · 2 = Haan / Nahi + Galat lane · 3 = the supplier drop-down + Galat lane · "
      "4 = the amount box + Galat lane · 5 = Galat lane and NO button",
      acts == {1: ['L("scan")'], 2: ["kConfirm(", "lane(x)"], 3: ["kVendor(", "lane(x)"], 4: ["kAmount(", "lane(x)"], 5: ["lane(x)"]}
      and g[2].count("kConfirm(") == 2 and ",true)" in g[2] and ",false)" in g[2] and "pic(x)" not in g[1] and all("pic(x)" in g[i] for i in (2, 3, 4, 5)), acts)
check("the answers post to the three doors and the list is drawn again in place (no jump to the top): kDo() calls load(), never say() or scrollTo",
      all(x in src for x in ('"/finance/porders/api/scan/confirm"', '"/finance/porders/api/scan/vendor"', '"/finance/porders/api/scan/amount"'))
      and "await load();" in seg("async function kDo(", "function kConfirm(") and "scrollTo" not in seg("async function kDo(", "function kConfirm("))

print("-- 2  Yahi bill hai?  Haan links · Nahi clears the hint · a second scan is marked, never linked twice")
check("a login of the unit that is not a sender may READ (the read door 200) and not answer: 403 'view_only' on each of the three doors, nothing linked; an answer naming another bill than the one on the line: 409",
      N["viewer"] == [403, "view_only", None, 403, 403, 200] and N["stale"] == 409, (N["viewer"], N["stale"]))
check("Haan, yahi hai: linked, grade CONFIRMED, 'reception confirmed'; purchase_bill.scan_bill_id set; audited scan_link by darpan with the grade and the rule",
      N["haan"][:4] == [200, True, ["sc1", "CONFIRMED", "reception confirmed"], True] and N["haan"][4] == [["darpan", "CONFIRMED", "reception confirmed", True]], N["haan"])
check("Nahi: not linked; the refusal is kept (hint_no = that bill); the scan now waits for Marg ('no bill on the server yet'); audited once",
      N["nahi"] == [200, False, None, True, "no_bill_yet", 1], N["nahi"])
check("Haan on the scan whose bill already has a scan: NOT linked a second time (the bill keeps its first scan); marked a second scan of it (dup, the first scan named); audited",
      N["second"] == [200, True, ["sc3a", "EXACT", "vendor+bill+amount"], "dup", True, 1], N["second"])
k2 = N["k2"]
check("after the three answers: the three lines are gone from 'Yahi bill hai?' (the unanswered one stays); the refused bill 440404 is back in Scan karo, the linked 440303 is not; "
      "the refused scan sits in Marg ka intezaar; the second scan is counted, not listed",
      k2["confirm"] == ["sc4"] and "c2" in k2["scan"] and "c1" not in k2["scan"] and "c3" not in k2["scan"] and "sc2" in k2["wait"] and "sc3b" not in k2["wait"] and N["k2_dup"] == 1, (k2["confirm"], k2["scan"], N["k2_dup"]))

print("-- 3  Supplier chuno: the spelling is learned ONCE and the matcher runs at once")
check("a name that is not on the supplier list is refused (400)", N["vendor_bad"] == 400, N["vendor_bad"])
v1 = N["vendor1"]
check("'Yeh supplier hai' on the unreadable 'XQZ TRADRS W440': learned, and linked at once to bill 440606 (PROBABLE vendor+date+amount)",
      v1[:4] == [200, True, True, ["sv1", "PROBABLE", "vendor+date+amount"]], v1[:4])
check("the OTHER scan with the same misspelling links too, without being asked (bill 440707) -- the spelling resolves as learned",
      v1[4] == ["sv2", "PROBABLE", "vendor+date+amount"], v1[4])
check("ONE purchase_scan_alias row for it (the scan and the person named), one alias_learn audit, one scan_vendor_chosen audit; asking again is refused (409: no such line)",
      len(v1[5]) == 1 and v1[5][0][0] == "XQZ TRADRS W440" and v1[5][0][1] is True and re.match(r"^S440 darpan chose for scan \d+$", v1[5][0][2] or "") and v1[6] == [["darpan", True]] and v1[7] == 1
      and N["vendor_again"] == 409, (v1[5:], N["vendor_again"]))
vb = N["vendor_buyer"]
check("the scan that read the BUYER's own name as the vendor: the choice is kept for that scan only (no alias row -- the buyer's name must never mean a supplier) and it links to bill 440808",
      vb == [200, False, True, ["sv3", "PROBABLE", "vendor+date+amount"], 0, "DEALWALK DRUGS"], vb)
vn = N["vendor_none"]
check("'List mein nahi hai': no link; the line leaves Supplier chuno and waits for Marg, saying why", vn[0] == 200 and vn[1] is False and (vn[2] or "").startswith("Supplier list mein nahi") and vn[3] == "-", vn)
k3 = N["k3"]
check("after the four answers Supplier chuno is empty and the three bills have left Scan karo", k3["vendor"] == [] and not any(x in k3["scan"] for x in ("v1", "v2", "v3")) and "sv4" in k3["wait"], (k3["vendor"], k3["scan"]))

print("-- 4  Amount milao: the amount ON THE PAPER, three outcomes")
check("anything but digits is refused (400)", N["amount_bad"] == 400, N["amount_bad"])
x = N["amt_scan_wrong"]
check("paper = Marg -> Scan galat padha: the link becomes EXACT ('paper amount = Marg (reception)'); the paper amount is kept in purchase_scan_state; assets.db still holds what OCR read (1444.39); no verdict on the bill",
      x == [200, "scan_wrong", ["sa1", "EXACT", "paper amount = Marg (reception)"], 1444239, "scan_wrong", 1444.39, None], x)
x = N["amt_marg_wrong"]
check("paper = the scan -> Marg galat: the bill is marked WRONG by darpan with the paper's amount and the reason 'bill <no> <supplier>: paper Rs X, Marg Rs Y' (the S371 list Amir corrects); the link stays; audited as a verdict 'via Scan ka kaam'",
      x[:6] == [200, "marg_wrong", ["sa2", "PROBABLE", "bill_tail+vendor"], "WRONG", "darpan", 250039]
      and (x[6] or "").startswith("bill 440912 YUVIWALK SURGICALS: paper Rs 2,500.39, Marg Rs 2,000.39") and x[7] == [["darpan", "Scan ka kaam", 250039]], x)
x = N["amt_owner"]
check("paper = neither -> Dr sahab ko dikhao: nothing marked, the link stays, and the owner's Needs you carries 'Scan amount to settle: bill 440913 ...' (the module's line, and the strip's API)",
      x[:5] == [200, "owner", ["sa3", "PROBABLE", "bill_tail+vendor"], "owner", None] and len(x[5]) == 1 and "the paper reads ₹3,300" in x[5][0] and "Marg ₹3,000.39" in x[5][0] and x[6] is True, x)
check("an answered line cannot be answered twice (409) and all three have left Amount milao", N["amount_again"] == 409 and N["k4"]["amount"] == [], (N["amount_again"], N["k4"]["amount"]))

print("-- 5  what a person decided rides every pass of the matcher (the Re-match button and the nightly command line)")
x = N["persist"]
check("after two more passes: the CONFIRMED link and the EXACT-by-paper link stand, the refused bill is still not offered, the second scan is still a second scan, the paper amounts, the owner's line and the 'not on the list' choice are kept",
      x[:2] == [200, 0] and x[2] == ["sc1", "CONFIRMED", "reception confirmed"] and x[3] == ["sa1", "EXACT", "paper amount = Marg (reception)"] and x[4] is None and x[5] is True and x[6] == "dup"
      and x[7] == 1444239 and x[8] == "owner" and x[9] == "-", x)
check("the five groups are the same after those passes as before them", N["k5"] == N["k4"], N["k5"])

print("-- 6  Marg's double entry · the six real near-matches · the counts agree")
d = N["double"]
check("the same number in two cases (A440202 / a440202: one supplier, date, amount) shows ONCE in Scan karo, saying so; the extra row is on the WRONG list (should be Rs 0, 'Marg mein do baar ...', by 'S440 rule'), "
      "audited ONCE however often the list is read; the row shown carries no verdict",
      "g1" in k0["scan"] and "g2" not in k0["scan"] and L["g1"]["double"] is True and sorted(L["g1"]["double_nos"]) == ["A440202", "a440202"] and d == ["WRONG", "S440 rule", 0, "Marg mein do baar", 1, None]
      and x[10] == 1, (L["g1"]["double_nos"], d))
r6 = N["real6"]
check("THE SIX REAL NEAR-MATCHES (found by supplier and bill number on the copy of today's data): %d found, %d still without a link and not refused -- every one of those is in 'Yahi bill hai?' and NONE is in Scan karo"
      % (r6["found"], r6["asked"]), r6["in_scan"] == 0 and r6["in_confirm"] == r6["asked"], r6)
ag = N["agree"]
check("the count agrees everywhere: the list (%s) = the summary the tile line reads (scan_kaam) = the owner's Scan links page ('N to act on'), group by group" % ag[0],
      ag[0] == ag[1] == ag[2] and ag[3] == ag[4] == ag[5], ag[:6])
check("the owner's Scan links page shows the five groups ONCE, read-only, above its tables, naming the walk's scans by their stamps", ag[6] == 1 and ag[7], ag[6:])
d0 = N["door0"]
check("the read door (/finance/porders/api/scan-status, inside the unit's login gate, read-only) answers in staff words: linked / waiting / your answer; a clinic scan gets no word; without a login it is refused",
      d0[0] == 200 and d0[1] == {"sc1": "you", "sv1": "you", "sa1": "you", "sw": "wait", "sc3a": "linked"} and d0[2]["sc3a"] == "Marg se mil gaya" and d0[2]["sw"] == "Marg ka intezaar (Amir)"
      and d0[2]["sc1"] == "Aapka jawab chahiye → Scan ka kaam" and N["door_nologin"] in (302, 401, 403), (d0, N["door_nologin"]))

print("-- 7  BACK and the up-arrow on every page of the flow; the register's menu")
P = N["pages"]
check("Purchase orders (200): the bar ONCE, the text '← BACK' once, the up-arrow once; the page reads ?from= (a path inside the site only) and falls back to /portal; section 3 is 'Scan ka kaam (N)', 'Bill scans pending' is gone",
      N["page"] == [200, 1, 1, 1, True, False] and 'id="s440back" href="/portal"' in src and 'get("from")' in src and 'f.charAt(0)==="/"&&f.charAt(1)!=="/"' in src, N["page"])
check("the owner's Scan links (200): the bar once, '← BACK' once, the up-arrow once, to /portal; ?from=/finance/approvals is honoured; ?from=//evil.example is not",
      N["scans_page"] == [200, 1, 1, 1, True] and N["scans_from"] == [True, True], (N["scans_page"], N["scans_from"]))
want = {"intake": [1, 1, 1, HUB, "Scan"], "intake_from": [1, 1, 1, "/finance/porders", "Scan"], "intake_evil": [1, 1, 1, HUB, "Scan"], "intake_evil2": [1, 1, 1, HUB, "Scan"],
        "intake_assets_host": [1, 1, 1, "https://followup.dr-manoj.in/portal", "Scan"], "intake_scanapp": [1, 1, 1, HUB, "Scan"],
        "list_staff": [1, 1, 1, HUB, "Meri scan list"], "list_owner": [1, 1, 1, HUB, "Purchases"], "list_owner_from": [1, 1, 1, "/finance/purchase/page/scans", "Purchases"],
        "bill_staff": [1, 1, 1, "/scanapp/bills", "Bill " + STAMP["sw"]], "bill_owner": [1, 1, 1, "/bills", "Bill " + STAMP["sw"]], "lanes_owner": [1, 1, 1, "/bills", "Scan lanes"]}
bad = {k: P.get(k) for k, v in want.items() if P.get(k) != v}
check("the asset app -- intake, the Purchases list (staff and owner), a bill (staff and owner), Scan lanes: the bar once, '← BACK' once, the up-arrow once, the page's name on the right; "
      "?from= honoured; another host or '//' refused -> the hub; from the assets host the hub is the followup site's /portal", not bad, bad or "12 pages")
check("the stamp slip carries the bar too, once (BACK = the list), and the up-arrow", P["slip"][0] == 1 and P["slip"][2] == 1 and P["slip"][3] == "/finance/porders", P["slip"])
mn = N["menu"]
check("the register's menu: ABSENT for a scanning login on the intake, the list and a bill (darpan, sukhveer); PRESENT for the owner and the manager",
      mn == {"darpan_intake": False, "darpan_list": False, "darpan_bill": False, "sukhveer_intake": False, "owner_intake": True, "owner_list": True, "manager_list": True}, mn)

print("-- 8  the intake, camera first; the Save card; S403's pre-fill")
it = N["intake_new"]
ix = it["idx"]
check("the order in the page: the kind/month line, THE SCANNER, then the two drop-downs (in a box that opens only on 'badlo'), the note, 'Kaise?', the basic upload -- the camera precedes the drop-downs in the DOM",
      all(i >= 0 for i in ix) and ix[0] < ix[1] < ix[2] < ix[3] < ix[4] < ix[5] < ix[6] < ix[7] and it["lanebox_hidden"] and it["badlo"], ix)
check("the line is pre-set from the login's lane and today: 'Pharmacy purchase · %s' for darpan; the selects still open on each person's own lane (darpan pharmacy, sukhveer lab_purchase)" % it["month"],
      it["line"] == "Pharmacy purchase · %s" % it["month"] and it["sel"] == "pharmacy" and it["sel_sukhveer"] == "lab_purchase", (it["line"], it["sel"], it["sel_sukhveer"]))
check("the explanation is folded under 'Kaise? ▾' with its three paragraphs word for word; the old heading is gone", it["kaise_folded"] and it["text_kept"] and it["old_h2"] is False, it)
pf = N["prefill"]
check("opened from the Scan karo line of bill 440101: S403's pre-fill is intact (lane, vendor, number, date, amount ride the scanner's fields) and the bar NAMES THE BILL; BACK and the scanner's return both lead to Purchase orders",
      pf[0] == 200 and pf[1].get("lane") == "pharmacy" and pf[1].get("vendor") == "KEDWALK PHARMACEUTICAL" and pf[1].get("bill_no") == "440101" and pf[1].get("amount") == "1200.39"
      and "from=" in (pf[2] or "") and pf[3][3] == "/finance/porders" and pf[3][4] == "KEDWALK PHARMACEUTICAL 440101 · ₹1200.39" and pf[4], pf)
sb = N["submit"]
check("a paper saved through the intake's own route lands as before (Pharmacy, captured, the pre-filled vendor / number / amount, a stamp, by Darpan) and goes to its slip carrying the way back",
      sb[0] in (302, 303) and "/intake/slip/" in sb[1] and "from=" in sb[1] and sb[2:] == ["Pharmacy", "captured", "pharmacy", "KEDWALK PHARMACEUTICAL", "440101", 1200.39, True, "Darpan"], sb)
sn = N["slip_new"]
check("THE SAVE CARD: 'Ho gaya — <stamp> · bill par likh do', two big buttons -- 'Agla bill scan karo' (the intake again, the same lane, the way back kept) and '← BACK to the list' (Purchase orders); it still polls for a double scan",
      sn["code"] == 200 and sn["ho_gaya"] and sn["stamp"] and sn["likh_do"] and (sn["agla"] or "").startswith("/intake?lane=pharmacy") and "from=" in (sn["agla"] or "") and sn["back"] == "/finance/porders"
      and sn["polls"] and sn["old_text"] is False and sn["bar"][3] == "/finance/porders", sn)
check("today's scans sit BELOW the card with the status in staff words (the new paper is on it); a clinic paper's BACK goes to the scan list instead", sn["today"] and sn["today_row"] and N["slip_clinic_back"] == "/bills",
      (sn["today"], sn["today_row"], N["slip_clinic_back"]))
check("'the line already gone': the saved paper linked to bill 440101 at once (EXACT vendor+bill+amount) and the bill has left Scan karo", N["new_link"][0] and N["new_link"][0][1:] == ["EXACT", "vendor+bill+amount"] and N["new_link"][1]
      and "k1" not in N["k6"]["scan"], (N["new_link"], N["k6"]["scan"]))

print("-- 9  the Purchases list of a scanning login; what stays shut")
ls = N["list"]
check("opens on MY LANE · THIS MONTH (both selected), 25 rows, 'aur dikhao' for more (with n=500 every row, no 'aur dikhao'); the search and the two filters stay; a Status column",
      ls["rows"] == 25 and ls["aur"] and ls["rows_full"] > 25 and ls["aur_full"] is False and ls["lane_sel"] and ls["month_sel"] and ls["filters"] and ls["status_head"], ls)
check("only what this login scanned itself; its clinic paper and last month's scan are not on the opening view, and come with 'Sab lane' / the month filter",
      ls["mine_only"] and ls["my_lane"] and ls["this_month"] and ls["all_lanes"] and ls["last_month"], ls)
check("rejected rows and drafts of an earlier month are folded under 'purane drafts (N) ▾', not in the rows", ls["old_folded"] and ls["old_has_rejected"] and ls["rejected_not_in_rows"] and ls["old_draft_all"], ls)
wd = N["words"]
check("the status column's four words: 'Marg se mil gaya' · 'Marg ka intezaar (Amir)' · 'Aapka jawab chahiye → Scan ka kaam' (a link to Purchase orders) · 'Doosri baar scan (<the first stamp>)'",
      wd["sc3a"] == "Marg se mil gaya" and wd["sw"] == "Marg ka intezaar (Amir)" and wd["sc4"] == "Aapka jawab chahiye → Scan ka kaam" and wd["sc3b"] == "Doosri baar scan (%s)" % STAMP["sc3a"]
      and wd["sc1"] == "Marg se mil gaya" and N["word_link"] and N["word_new"] == "Marg se mil gaya", (wd, N["word_new"]))
check("when finance's door cannot be asked the list still opens and says plainly 'Scan ho gaya'", N["word_failsoft"] == "Scan ho gaya", N["word_failsoft"])
check("the owner's view of the list is unchanged (its own table with the Lane column; no 25-row page, no 'purane drafts')", N["list_owner"] == [0, True, False, False], N["list_owner"])
check("a scanning login's bill page is read-only: the status in staff words, the scan, no form and no action", N["bill_staff"] == [200, True, True, False], N["bill_staff"])
gt = N["gates"]
check("what stays shut for a scanning login: another person's bill page (403), a clinic paper's picture (403), a rejected scan's picture (403), /lanes, /purchases, approve, the duplicate taps, the month (403 each); "
      "the picture of ANY live pharmacy scan is open (the line on Purchase orders shows it): PDF and photo both give a PNG",
      gt["other_bill"] == 403 and gt["other_clinic_bill"] == 403 and gt["thumb_other_clinic"] == 403 and gt["file_other_clinic"] == 403 and gt["thumb_rejected"] == 403 and gt["lanes"] == 403
      and gt["purchases"] == 403 and gt["approve"] == 403 and gt["dup"] == 403 and gt["month"] == 403 and gt["thumb_pdf"] == [200, "image/png"] and gt["thumb_jpg"] == [200, "image/png"]
      and gt["thumb_other_pharmacy"] == 200 and gt["file_other_pharmacy"] == 200 and gt["owner_thumb"] == 200, gt)
gl = N["galat_lane"]
check("GALAT LANE: a scanning login moves a captured pharmacy scan to clinic (302 back to Purchase orders; lane clinic, a draft for approval), audited (who, from -> to, 'via Scan ka kaam'); "
      "the line vanishes from Scan ka kaam and from the pharmacy list",
      gl[0] in (302, 303) and gl[1] == "/finance/porders" and gl[2] == {"lane": "clinic", "kind": "Consumable", "status": "draft"} and gl[3] and gl[4] and len(gl[5]) == 1 and gl[5][0][0] == "Alisha"
      and gl[5][0][1].get("from") == "pharmacy" and gl[5][0][1].get("to") == "clinic" and gl[5][0][1].get("via") == "Scan ka kaam" and gl[6], gl)
check("and nothing else: into the pharmacy or the owner's lane, a paper that is not a pharmacy scan, a rejected one -- 403 each", N["lane_refused"] == [403, 403, 403, 403], N["lane_refused"])
check("at the end the three counts still agree (the list, the summary, the owner's page)", N["final_agree"][0] == N["final_agree"][1] == N["final_agree"][2], N["final_agree"])

print("-- 10 NEGATIVE CONTROLS on the box as it is (the unpatched files, the same crafted rows)")
check("NEGATIVE: the old state has no 'kaam'; the near-match bill 440303 IS asked for again in the old list; the double entry shows twice",
      O["state_code"] == 200 and O["has_kaam"] is False and O["s403_list"]["c1"] and O["s403_list"]["c2"] and O["s403_list"]["g1"] and O["s403_list"]["g2"], O["s403_list"])
o6 = O["real6"]
check("NEGATIVE: the six real near-matches: %d found, %d without a link -- every one of those is still in the old 'Bill scans pending'" % (o6["found"], o6["found"] - o6["linked"]),
      o6["in_old_list"] == o6["found"] - o6["linked"], o6)
check("NEGATIVE: the old Purchase orders page has no bar, no up-arrow, and says 'Bill scans pending'; the old Scan links page has no bar; the read door and the confirm door do not exist (404 / 405)",
      O["page"] == [200, 0, 0, 0, False, True] and O["scans_page"][:4] == [200, 0, 0, 0] and O["door_old"] == 404 and O["confirm_old"] in (404, 405), (O["page"], O["scans_page"], O["door_old"], O["confirm_old"]))
oi = O["intake"]
check("NEGATIVE: the old intake has no bar and no up-arrow, shows the register's header to a scanning login, and its camera sits BELOW the two drop-downs and the note; no 'Kaise?'",
      oi[:5] == [200, 0, 0, 0, True] and 0 <= oi[6] < oi[7] < oi[8] < oi[5] and oi[9] == -1, oi)
check("NEGATIVE: the old asset app refuses a scanning login the list and its own bill (403), has no thumbnail route (404), and its slip says 'Scan another', not 'Ho gaya'",
      O["bills_darpan"] == 403 and O["bill_darpan"] == 403 and O["thumb"][0] == 404 and O["slip_old"] == [200, False, True], (O["bills_darpan"], O["bill_darpan"], O["thumb"], O["slip_old"]))
check("NEGATIVE: the owner's pages of the old asset app carry the header and no bar", O["intake_owner"] == [200, True, True, 0] and O["bills_owner"][:3] == [200, True, 0], (O["intake_owner"], O["bills_owner"]))

print(("WALK_S440 GREEN -- %d of %d passed" % (n, n)) if not fails else ("WALK_S440 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
