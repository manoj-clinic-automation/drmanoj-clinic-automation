#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s439.py -- kit S439_SCANS_SMS_SCROLL. THE REAL finance_app.py (a copy of /root/finance carrying the kit's three files) over
SCRATCH COPIES of finance.db and assets.db, driven through Flask's test client (header identity, walk only), and the same walk over
the box as it is (the negative control). Its own rows are keyed W439: purchase bills under the export md5 'w439...' with suppliers
whose names carry WALK, scans stamped 'W439-nn', SMS posts from 'W439-SENDER' or of its own amounts. Every row is found by that key, never by
counting. The crafted bill numbers keep the FORMS the real scans have (prefix letters, leading zeros, dashes, a bracket, a licence
number) over digits of the walk's own; every date is computed from today. The bank-SMS door is opened with the walk's OWN key file;
the merchant id an ICICI text needs is read from the scratch copy and never printed. Nothing is posted to a live door.

  --app NEW  --old OLD   (copies of /root/finance: the kit's files / the box as it is)
  --db PATH              (the scratch finance.db; PATH.old is made for the old app)
  --assets-db PATH       (the scratch assets.db; PATH.old likewise)
  --kit DIR              (where replay_s439.py is; default: beside this file)
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
for k in ("--app", "--old", "--db", "--assets-db"):
    ap.add_argument(k, required=True)
ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
assert "walk" in a.assets_db or "scratch" in a.assets_db or a.assets_db.startswith("/tmp"), "refusing a non-scratch assets database"
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


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


TODAY = dt.date.today()
NOW = dt.datetime.now().replace(microsecond=0)


def D(k):
    return (TODAY - dt.timedelta(days=k)).isoformat()


def yr(iso, year):
    """The same day and month under a year OCR might print."""
    return "%04d-%s" % (year, iso[5:])


MD5 = "w439" + hashlib.md5(b"walk_s439").hexdigest()[:28]
# name -> (supplier as Marg prints it, Marg's bill number, days ago, rupees)
# The walk's suppliers are names no real supplier's name sits inside (S403's vendor rule also matches a name CONTAINED in another).
BILLS = [
    ("b1", "KEDWALK PHARMACEUTICAL", "439166", 12, 8840.39),
    ("b2", "GUNWALK PHARMACEUTICALS PVT LTD", "43964906", 11, 6724.39),
    ("b3", "JUBIWALK AGENCIES              BAREILLY", "43915521", 10, 6113.39),
    ("b4", "SHIVWALK FORMULATIONS          BAREILLY", "4393051", 9, 17130.39),
    ("b5", "WALKESS WALKAY AGENCIES EXTN", "4397234", 9, 2048.39),
    ("b6", "WALKAGAR SURGICALS AND MEDICALS", "4394430", 8, 400.39),
    ("b7", "DEALWALK DRUGS                 BAREILLY", "4395620", 8, 1281.39),
    ("b8", "DEEPWALK PHARMA", "439601", 7, 3800.39),
    ("b9", "JUBIWALK AGENCIES              BAREILLY", "4315878", 6, 2941.39),
    ("b10", "JUBIWALK AGENCIES              BAREILLY", "43918112", 6, 2941.39),
    ("b11", "YUVIWALK SURGICALS", "439585", 5, 2470.39),
    ("b12", "YUVIWALK SURGICALS", "439634", 15, 5235.39),
    ("b13", "KEDWALK PHARMACEUTICAL", "439175", 4, 19880.39),
    ("b14", "KEDWALK PHARMACEUTICAL", "439182", 3, 6490.39),
    ("b15", "GUNWALK PHARMACEUTICALS PVT LTD", "43971226", 2, 14908.39),
    ("b16", "DEEPWALK PHARMA", "439189", 2, 7008.39),
]
BD = {b[0]: b for b in BILLS}
# name -> (vendor as OCR read it, bill number as OCR read it, the date OCR read, rupees or None)
SCANS = [
    ("s1", "KEDWALK PHAMACEUTICAL", "A0439166", yr(D(12), 2036), 8840.39),                        # prefix + zeros, vendor misspelt, year off
    ("s2", "GUNWALK PHARMACEUTICALS PVT. LTD.", "GPPL-26-43964906", yr(D(11), 2024), 6724.39),     # dashes, a short run before the number
    ("s3", "JUBWALK AGENCIES", "NOT043915521", yr(D(10), 2028), 6113.39),                         # vendor misspelt (JUBWALK for JUBIWALK)
    ("s4", "SHIVWALC FORMULATIONS", "SF 004393051", yr(D(9), 2018), 17130.39),                    # a space inside; vendor misspelt
    ("s5", "WALKESS WALKAY AGENCIES (EXTN)", "A04397234", D(9), 2048.39),
    ("s6", "WALKAGAR SURGICAL & MEDICALS", "G-4394430", D(8), 400.39),
    ("s7", "WHOLE SALE CHEMIST & DRUGGIST", "T004395620", D(8), 1281.39),                          # the letterhead read as the vendor
    ("s8", "M/S SANJEEVANI MEDICOS", "A000439601", D(7), 3806.09),                                # the BUYER read as the vendor, the amount 0.15% off
    ("s9", "JUBWALK AGENCIES", "43918112 (NOT04315878)", yr(D(6), 2025), 2941.39),                # two runs: the LAST is the number
    ("s11", "YUVIWALK SURGICALS", "21/2014/BLY", D(3), 2470.39),                                   # the licence number read as the bill number; date 2 days off
    ("s12", "YUVIWALK SURGICALS", "", D(9), 5235.39),                                              # no number, the date 6 days off
    ("s13a", "KEDWALK PHARMACEUTICAL", "439175", D(4), 19880.39),                                  # the first scan: exact, as S403 linked it
    ("s13b", "KEDWALK PHAMACEUTICAL", "A000439175", D(4), 19880.39),                               # the same paper scanned again
    ("s14", "KEDWALK PHAMACEUTICAL", "A0439182", yr(D(3), 2036), 6490.39),                        # the same misspelling once more
    ("s15", "SUNWALK PHARMACEUTICALS PVT. LTD.", "GPPL-26-43971226", D(2), 152618.0),               # vendor misspelt AND the amount misread
    ("w_nobill", "KEDWALK PHARMACEUTICAL", "A0439991", D(0), 1234.39),
    ("w_vendor", "M/S SANJEEVNI MEDICOSE", "A00439992", D(0), 95.25),
    ("w_amount", "SANJEEVINI MEDICOS", "A000439189", D(2), 7668.39),
    ("w_digits", "KEDWALK PHARMACEUTICAL", "", D(0), None),
    ("p1", "KEDWALK PHARMACEUTICAL", "A0439777", yr(D(0), 2036), 777.39),                          # scanned BEFORE Marg has the bill (prefix, year off)
]
SD = {s[0]: s for s in SCANS}


def craft(fin, ast):
    F = sqlite3.connect(fin, timeout=30)
    A = sqlite3.connect(ast, timeout=30)
    F.execute("INSERT OR REPLACE INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
              (MD5, "BILLWISE", "W439_WALK", D(20), D(1), NOW.strftime("%Y%m%d-%H%M%S"), NOW.isoformat(), len(BILLS), 0))
    ids = {"md5": MD5, "bills": {}, "scans": {}}
    for name, sup, bno, ago, rs in BILLS:
        key = re.sub(r"\s+", " ", sup.upper()).strip()
        key = key[:-len(" BAREILLY")] if key.endswith(" BAREILLY") else key
        p = int(round(rs * 100))
        cur = F.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, cash_p, credit_p, amount_p, source_md5, bw_md5, bw_amount_p, date_src) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (key, sup, bno, D(ago), D(ago)[:7], 0, p, p, MD5, MD5, p, "BILLWISE"))
        ids["bills"][name] = cur.lastrowid
    for i, (name, vendor, bno, date, rs) in enumerate(SCANS):
        cur = A.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, notes, created_at, stamp_no, status, ocr_status, lane) VALUES ('Pharmacy',?,?,?,?,?,?,?,'captured','read','pharmacy')",
                        (vendor, bno, date, rs, "W439 walk", NOW.strftime("%Y-%m-%d %H:%M:%S"), "W439-%02d" % (i + 1)))
        ids["scans"][name] = cur.lastrowid
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
KEYF = os.path.join(os.path.dirname(os.path.abspath(a.db)), "w439_door.key")
with io.open(KEYF, "w", encoding="utf-8") as fh:
    fh.write("walk-key-W439-not-a-secret\n")
ASSETS_MD5 = md5f(a.assets_db)
print("-- scratch copies made for the old app; %d purchase bills (export %s) and %d scans (W439-01..%02d) crafted on both; the walk's own door key written"
      % (len(BILLS), MD5[:8], len(SCANS), len(SCANS)))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re, io, subprocess, hashlib
from urllib.parse import quote
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
os.environ["FINANCE_MARG_TOKEN"] = "w439-walk-token"      # the walk's own machine token: the front gate and the push door read it at import
NEW = os.environ["MODE"] == "new"
KEY = open(os.environ["BANK_SMS_KEY_FILE"]).read().strip()
W = json.loads(os.environ["W439"]); SC = W["scans"]; BL = W["bills"]
import finance_app as fa
import purchase_app as pa, bank_sms as bs
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
one = lambda s, *a: db.execute(s, a).fetchone()[0]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
today = dt.date.today(); now = dt.datetime.now().replace(microsecond=0)
out = {}
def links():
    return {str(r["bill_id"]): [r["asset_bill_id"], r["grade"], r["matched_on"]] for r in q(
        "SELECT l.bill_id, l.asset_bill_id, l.grade, l.matched_on FROM purchase_scan_link l JOIN purchase_bill b ON b.id=l.bill_id WHERE b.supplier_norm LIKE '%WALK%'")}
def n_audit(action):
    return one("SELECT COUNT(*) FROM purchase_audit WHERE action=?", action)
# ------------------------------------------------------------------ the matcher
out["alias0"] = one("SELECT COUNT(*) FROM purchase_vendor_alias") if has("purchase_vendor_alias") else 0
pg = G("manoj", "/finance/purchase/page/scans")               # the owner opens the scan-links page: the scans have changed, the pass runs
out["page_code"] = pg[0]
out["links1"] = links()
html = pg[1] if isinstance(pg[1], str) else ""
out["page_head"] = ["Why it is not linked" in html, "A scan already here?" in html]
if NEW:
    st = {r["asset_bill_id"]: r for r in q("SELECT * FROM purchase_scan_state")}
    out["state"] = {k: ({x: st[v][x] for x in ("why", "detail", "dup_cand", "dup_bill", "hint_bill")} if v in st else None) for k, v in SC.items()}
    out["page_why"] = {k: bool(v in st and esc(st[v]["detail"]) in html) for k, v in SC.items() if v in st}
    out["page_hint"] = [("scan #%d</a>" % SC["w_amount"]) in html and "is probably this bill" in html, ("scan #%d</a>" % SC["s12"]) in html]
    out["audit_links"] = {r["ref"]: [r["who"], json.loads(r["detail"])] for r in q("SELECT ref, who, detail FROM purchase_audit WHERE action='scan_link' AND ref IN (%s)" % ",".join("'%d'" % v for v in BL.values()))}
    out["audit_dup"] = [json.loads(r["detail"]) for r in q("SELECT detail FROM purchase_audit WHERE action='scan_dup' AND ref=?", str(BL["b13"]))]
    out["learned"] = q("SELECT ocr_norm, supplier_norm, scan_id, who FROM purchase_scan_alias WHERE ocr_norm LIKE '%WAL%' ORDER BY ocr_norm")
    out["learn_audit"] = [[r["ref"], json.loads(r["detail"]).get("note")] for r in q("SELECT ref, detail FROM purchase_audit WHERE action='alias_learn' AND ref LIKE '%WAL%' ORDER BY ref")]
    out["alias1"] = one("SELECT COUNT(*) FROM purchase_vendor_alias") if has("purchase_vendor_alias") else 0
    out["bill_scan_id"] = one("SELECT scan_bill_id FROM purchase_bill WHERE id=?", BL["b1"])
    # the second run: nothing new
    a0 = n_audit("scan_link"); d0 = n_audit("scan_dup"); l0 = n_audit("alias_learn")
    r2 = P("manoj", "/finance/purchase/api/rematch")
    last = json.loads(q("SELECT detail FROM purchase_audit WHERE action='rematch' ORDER BY id DESC LIMIT 1")[0]["detail"])
    out["run2"] = [r2[0], (r2[1] or {}).get("ok"), last.get("new"), n_audit("scan_link") - a0, n_audit("scan_dup") - d0, n_audit("alias_learn") - l0, links() == out["links1"]]
    ctx = pa._vendor_ctx_s439(db, [dict(b) for b in db.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL).fetchall()])
    out["resolve2"] = list(pa._vendor_resolve_s439("KEDWALK PHAMACEUTICAL", ctx))
    out["tails"] = [pa._bill_tails_s439(x) for x in ("GPPL-26-64906", "A000166", "NOT015521", "SF 003051", "18112 (NOT015878)", "YS/0585/2026-27", "KT-078347", "")]
    out["buyer"] = [pa._vendor_resolve_s439(x, ctx)[1] for x in ("SANJEEVNI MEDICOS", "M/S SANJEEVINI MEDICOSE", "M/s SANJEEVANI MEDICOS")]
# the push door: a scan made BEFORE Marg had the bill is linked when the bill lands
out["p1_before"] = links().get(str(one("SELECT COALESCE(MAX(id),0) FROM purchase_bill WHERE supplier_norm='KEDWALK PHARMACEUTICAL' AND bill_no='439777'")))
body = {"type": "BILLWISE", "md5": hashlib.md5(("w439 push %s" % now.isoformat()).encode()).hexdigest(), "period_from": today.isoformat(), "period_to": today.isoformat(),
        "export_stamp": now.strftime("%Y%m%d-%H%M%S"), "file": "W439_PUSH", "grand_amount_p": 77739,
        "rows": [{"supplier": "KEDWALK PHARMACEUTICAL", "bill_no": "439777", "bill_date": today.isoformat(), "cash_p": 0, "credit_p": 77739}]}
r = c.post("/finance/purchase/api/push", json=body, headers={"X-Finance-Marg": "w439-walk-token"})
out["push"] = [r.status_code, (r.get_json(silent=True) or {}).get("stored"), (r.get_json(silent=True) or {}).get("rows")]
pb = one("SELECT COALESCE(MAX(id),0) FROM purchase_bill WHERE supplier_norm='KEDWALK PHARMACEUTICAL' AND bill_no='439777'")
out["p1_after"] = links().get(str(pb))
out["p1_audit"] = [[x["who"], json.loads(x["detail"]).get("rule")] for x in q("SELECT who, detail FROM purchase_audit WHERE action='scan_link' AND ref=?", str(pb))]
env = dict(os.environ); env.pop("BANK_SMS_NOW", None)
p = subprocess.run([sys.executable, "-B", os.path.join(APP, "purchase_app.py"), "rematch", "--list"], env=env, cwd=APP, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
line = (p.stdout.splitlines() or [""])[0]
out["cli"] = [p.returncode, line.startswith("S439 rematch"), " 0 new link(s)" in line, ("scan #%d" % SC["w_nobill"]) in p.stdout, p.stderr[-300:]]
out["links_end"] = links()
out["other_pages"] = [G("manoj", "/finance/purchase/page/hub")[0], G("darpan", "/finance/porders/api/state")[0]]
# ------------------------------------------------------------------ the bank-SMS door
tail6 = str(one("SELECT merchant_id FROM business_unit WHERE code='medical'"))[-6:]
day = today.strftime("%d-%b-%y")
def icici(rs):
    return "ICICI Bank Account XX439 credited:Rs. %s on %s. Info EZY*ICICIPOS_SET_10XX%s_. Available Balance is Rs. 1,00,000.00." % (rs, day, tail6)
YES_CASH = "Your YES BANK A/c XX4439 has been credited with INR 43,902.00 on %s by CASH DEPOSIT at BAREILLY. Avl Bal INR 5,00,000.00" % day
OTP = "Your OTP is 482913 for a payment of Rs 999.00 at SOME STORE. Do not share it. Ref W439R1."
HK = {"X-Bank-Sms-Key": KEY}
def post(**kw):
    r = c.post("/finance/api/bank-sms", **kw); j = r.get_json(silent=True) or {}
    return [r.status_code, j.get("stored"), j.get("ignored"), j.get("unit") or j.get("kind")]
def settle(p):
    return q("SELECT unit, credit_date, amount_p, phone_sender, parse_grade, seen, received_at, (instr(sms_text, '.=ICICI') > 0) AS doubled FROM bank_sms_settlement WHERE amount_p=? AND credit_date=?", p, today.isoformat())
ign0 = one("SELECT COALESCE(MAX(id),0) FROM bank_sms_ignored") if has("bank_sms_ignored") else 0
out["sms_bad_key"] = post(data={"message": icici("4,391.00")}, headers={"X-Bank-Sms-Key": "not-the-key"})[0]
out["sms_message_from"] = post(data={"message": icici("4,391.01"), "from": "W439-SENDER"}, headers=HK) + [settle(439101)]
out["sms_body_number"] = post(json={"body": YES_CASH, "number": "W439-SENDER"}, headers=HK) + [q("SELECT kind, sms_date, amount_p, acct_tail, phone_sender FROM bank_sms_yes WHERE phone_sender='W439-SENDER'") if has("bank_sms_yes") else []]
out["sms_raw_body"] = post(data=icici("4,391.03"), headers=dict(HK, **{"Content-Type": "text/plain"})) + [settle(439103)]
out["sms_bare_query"] = post(query_string=quote(icici("4,391.04")) + "=" + quote(icici("4,391.04")), headers=HK) + [settle(439104)]      # ?<the SMS>=<the SMS>: the macro's own shape
out["sms_upper_json"] = post(json={"MESSAGE": icici("4,391.05"), "From": "W439-SENDER"}, headers=HK) + [settle(439105)]
out["sms_text_sender"] = post(data={"text": icici("4,391.06"), "sender": "W439-SENDER"}, headers=HK) + [settle(439106)]
out["sms_key_in_query"] = post(query_string="key=" + KEY + "&" + quote(icici("4,391.07"))) + [settle(439107)]
out["sms_refused"] = post(data={"message": OTP, "from": "W439-SENDER", "ts": "1"}, headers=HK)
out["sms_refused_raw"] = post(data="W439 note " + KEY + " not a bank SMS 1234567", headers=dict(HK, **{"Content-Type": "text/plain"}))
cols = [r[1] for r in db.execute("PRAGMA table_info(bank_sms_ignored)")]
out["ign_cols"] = "fields" in cols
ig = q("SELECT * FROM bank_sms_ignored WHERE id>? ORDER BY id", ign0)
out["ign_rows"] = [[r.get("phone_sender"), r.get("reason"), r.get("fields"), bool(r.get("masked_text")), bool(re.search(r"\d{5,}", r.get("masked_text") or "")), "Rs ####" in (r.get("masked_text") or ""),
                    "[key]" in (r.get("masked_text") or "")] for r in ig]
blob = json.dumps(q("SELECT * FROM bank_sms_ignored WHERE id>?", ign0) + q("SELECT * FROM bank_sms_settlement WHERE credit_date=?", today.isoformat()) + (q("SELECT * FROM bank_sms_yes WHERE phone_sender='W439-SENDER'") if has("bank_sms_yes") else []), default=str)
out["key_stored"] = KEY in blob
pg2 = G("manoj", "/finance/bank-sms")
out["sms_page"] = [pg2[0], "Fields it carried" in pg2[1], "does not have to change" in pg2[1], "message,from,ts" in pg2[1], KEY in pg2[1].replace('<p class="key">%s</p>' % KEY, "")]
out["version"] = [bs.APP_VERSION, getattr(bs, "S439_REV", None)]
if NEW:
    # the replay of the web server's log: the walk's own log lines, the walk's own refused note
    db.execute("DELETE FROM setting WHERE key='bank_sms.s439_replay'"); db.commit()      # scratch only: a copy made after the install carries the mark
    at = dt.datetime.combine(today, dt.time(7, 1, 36))
    logf = os.path.join(os.path.dirname(os.environ["FINANCE_DB"]), "w439_access.log")
    L = at.strftime("%d/%b/%Y:%H:%M:%S +0530")
    with io.open(logf, "w", encoding="utf-8") as fh:
        fh.write('10.0.0.9 - - [%s] "POST /finance/api/bank-sms?%s=%s HTTP/2" 200 42 "-" "macrodroid/5.67.8"\n' % (L, quote(icici("4,391.11")), quote(icici("4,391.11"))))
        fh.write('10.0.0.9 - - [%s] "POST /finance/api/bank-sms?%%7Bsms_message%%7D=%%7Bsms_message%%7D HTTP/2" 200 42 "-" "macrodroid/5.67.8"\n' % (at + dt.timedelta(minutes=5)).strftime("%d/%b/%Y:%H:%M:%S +0530"))
        fh.write('10.0.0.9 - - [%s] "POST /finance/api/bank-sms?%s HTTP/2" 401 31 "-" "curl/7.76.1"\n' % ((at + dt.timedelta(minutes=9)).strftime("%d/%b/%Y:%H:%M:%S +0530"), quote(icici("4,391.12"))))
    db.execute("INSERT INTO bank_sms_ignored (received_at, phone_sender, bank_guess, reason, masked_text) VALUES (?,?,?,?,?)", (at.strftime("%Y-%m-%d %H:%M:%S"), "", "UNKNOWN", "not a bank SMS this door reads", ""))
    db.commit()
    rp = [sys.executable, "-B", os.path.join(os.environ["KITDIR"], "replay_s439.py"), "--app", APP, "--db", os.environ["FINANCE_DB"], "--log", logf, "--log", logf + ".none"]
    p1 = subprocess.run(rp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(logf))
    p2 = subprocess.run(rp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(logf))
    out["replay"] = [p1.returncode, "1 replayed" in p1.stdout, "1 empty refused note(s) replaced" in p1.stdout, "4,391" in p1.stdout or tail6 in p1.stdout, p2.returncode, "already replayed" in p2.stdout,
                     settle(439111), settle(439112), one("SELECT COUNT(*) FROM bank_sms_ignored WHERE received_at=? AND masked_text=''", at.strftime("%Y-%m-%d %H:%M:%S")), p1.stdout[-300:] if p1.returncode else ""]
    out["replay_at"] = at.strftime("%Y-%m-%d %H:%M:%S")
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath, adb):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, ASSETS_DB=adb, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"),
               FINANCE_ALLOW_HEADER_AUTH="1", BANK_SMS_KEY_FILE=KEYF, W439=json.dumps(W), KITDIR=a.kit)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, "old", a.db + ".old", a.assets_db + ".old")
N = probe(a.app, "new", a.db, a.assets_db)
B, S = W["bills"], W["scans"]
L1 = N["links1"]


def link(b):
    return L1.get(str(B[b])) or [None, None, None]


def linked(b, s, grade, rule):
    return link(b) == [S[s], grade, rule]


print("-- 1  the matcher: what OCR really writes links to its bill, by the named rule (the forms of the real scans, the walk's own digits)")
check("'A0439166' (prefix + zeros, vendor misspelt PHAMACEUTICAL, year 2036) links to bill 439166: EXACT bill_tail+vendor+amount~2%", linked("b1", "s1", "EXACT", "bill_tail+vendor+amount~2%"), link("b1"))
check("'GPPL-26-43964906' (dashes, 'PVT. LTD.', year 2024) links to 43964906: EXACT bill_tail+vendor+amount~2%", linked("b2", "s2", "EXACT", "bill_tail+vendor+amount~2%"), link("b2"))
check("'NOT043915521' (vendor misspelt JUBWALK for JUBIWALK, year 2028) links to 43915521: EXACT bill_tail+vendor+amount~2%", linked("b3", "s3", "EXACT", "bill_tail+vendor+amount~2%"), link("b3"))
check("'SF 004393051' (a space, vendor misspelt SHIVWALC, year 2018) links to 4393051: EXACT bill_tail+vendor+amount~2%", linked("b4", "s4", "EXACT", "bill_tail+vendor+amount~2%"), link("b4"))
check("'A04397234' (vendor '... AGENCIES (EXTN)') links to 4397234: EXACT bill_tail+vendor+amount~2%", linked("b5", "s5", "EXACT", "bill_tail+vendor+amount~2%"), link("b5"))
check("'G-4394430' (vendor 'SURGICAL & MEDICALS' for 'SURGICALS AND MEDICALS') links to 4394430: EXACT bill_tail+vendor+amount~2%", linked("b6", "s6", "EXACT", "bill_tail+vendor+amount~2%"), link("b6"))
check("'T004395620' under a letterhead that is no vendor ('WHOLE SALE CHEMIST & DRUGGIST') links to 4395620: PROBABLE bill_tail+amount~2%", linked("b7", "s7", "PROBABLE", "bill_tail+amount~2%"), link("b7"))
check("'A000439601' with the BUYER as the vendor ('M/S SANJEEVANI MEDICOS'), the amount 0.15% off, links to 439601: PROBABLE bill_tail+amount~2%", linked("b8", "s8", "PROBABLE", "bill_tail+amount~2%"), link("b8"))
check("'43918112 (NOT04315878)' links by its LAST digit run to bill 4315878 -- not to bill 43918112 of the same vendor and amount, which stays unscanned",
      linked("b9", "s9", "EXACT", "bill_tail+vendor+amount~2%") and link("b10") == [None, None, None], (link("b9"), link("b10")))
check("a year-off date never blocks: the five scans dated 2036 / 2024 / 2028 / 2018 / 2025 above are all linked", all(link(b)[0] for b in ("b1", "b2", "b3", "b4", "b9")))
check("the licence number read as the bill number ('21/2014/BLY'), the date 2 days off: PROBABLE vendor+date+amount (the date rule takes +-3 days)", linked("b11", "s11", "PROBABLE", "vendor+date+amount"), link("b11"))
check("the first, exact scan of bill 439175 links as S403 linked it: EXACT vendor+bill+amount", linked("b13", "s13a", "EXACT", "vendor+bill+amount"), link("b13"))
check("vendor misspelt AND the amount misread (SUNWALK for GUNWALK, 1,52,618 for 14,908): PROBABLE bill_tail+vendor", linked("b15", "s15", "PROBABLE", "bill_tail+vendor"), link("b15"))
check("the pieces: the tails of the real forms, the buyer in three spellings", N["tails"] == [["64906"], ["166"], ["15521"], ["3051"], ["15878", "18112"], ["585"], ["78347"], []]
      and N["buyer"] == ["buyer", "buyer", "buyer"], (N["tails"], N["buyer"]))

print("-- 2  a bill takes ONE scan; the spelling is learned once; every link is audited; the second run links nothing")
st = N["state"]
check("the same paper scanned again ('A000439175') is NOT linked a second time: marked 'already scanned', dup_cand = the first scan, its bill named; audited once",
      st["s13b"] and st["s13b"]["why"] == "dup" and st["s13b"]["dup_cand"] == S["s13a"] and st["s13b"]["dup_bill"] == B["b13"] and link("b13")[0] == S["s13a"]
      and len(N["audit_dup"]) == 1 and N["audit_dup"][0].get("dup_cand") == S["s13a"], (st["s13b"], N["audit_dup"]))
lk = [x for x in N["learned"] if x["ocr_norm"] == "KEDWALK PHAMACEUTICAL"]
la = [x for x in N["learn_audit"] if x[0] == "KEDWALK PHAMACEUTICAL"]
check("the misspelt vendor linked (bills 439166 and 439182) and its spelling was learned ONCE: one purchase_scan_alias row -> KEDWALK PHARMACEUTICAL, one audit 'S439 learned from scan <id>'",
      linked("b14", "s14", "EXACT", "bill_tail+vendor+amount~2%") and len(lk) == 1 and lk[0]["supplier_norm"] == "KEDWALK PHARMACEUTICAL" and len(la) == 1
      and re.match(r"^S439 learned from scan \d+$", la[0][1] or "") and lk[0]["who"] == la[0][1], (lk, la))
check("after the pass the spelling resolves as learned, with no similarity guess", N["resolve2"][:2] == ["KEDWALK PHARMACEUTICAL", "learned"], N["resolve2"])
check("the owner's S263 table purchase_vendor_alias (it decides which bank account a bill is paid into) is untouched: %s rows before and after" % N["alias0"], N["alias0"] == N["alias1"], (N["alias0"], N["alias1"]))
al = N["audit_links"]
need = {"b1": "s1", "b2": "s2", "b3": "s3", "b4": "s4", "b5": "s5", "b6": "s6", "b7": "s7", "b8": "s8", "b9": "s9", "b11": "s11", "b13": "s13a", "b14": "s14", "b15": "s15"}
check("every one of the 13 links written is audited with its scan, its grade and the rule that made it",
      all(str(B[b]) in al and al[str(B[b])][1].get("scan") == S[s] and al[str(B[b])][1].get("grade") == link(b)[1] and al[str(B[b])][1].get("rule") == link(b)[2] for b, s in need.items()),
      {b: al.get(str(B[b])) for b in ("b1", "b7")})
check("purchase_bill.scan_bill_id carries the scan of a linked bill", N["bill_scan_id"] == S["s1"], N["bill_scan_id"])
check("the second run (the Re-match button) links 0: no new link, no new audit of a link, a duplicate or a spelling; the links are the same",
      N["run2"] == [200, True, 0, 0, 0, 0, True], N["run2"])

print("-- 3  WHY: every scan still open says why, on the owner's scan-links page")
check("no bill on the server yet (a number Marg has not sent)", st["w_nobill"] and st["w_nobill"]["why"] == "no_bill_yet" and st["w_nobill"]["detail"].startswith("no bill on the server yet"), st["w_nobill"])
check("vendor unknown (the buyer's own name, a number that is on no bill)", st["w_vendor"] and st["w_vendor"]["why"] == "vendor_unknown" and st["w_vendor"]["detail"].startswith("vendor unknown"), st["w_vendor"])
check("amount differs (the buyer as vendor, bill 439189 found by its number, the amount 9% off) -- and that bill is named as the scan's probable bill",
      st["w_amount"] and st["w_amount"]["why"] == "amount_differs" and st["w_amount"]["detail"].startswith("amount differs") and st["w_amount"]["hint_bill"] == B["b16"], st["w_amount"])
check("no digits read (no bill number, no amount)", st["w_digits"] and st["w_digits"]["why"] == "no_digits" and st["w_digits"]["detail"].startswith("no digits read"), st["w_digits"])
check("a fifth, beside the brief's four: bill number differs (same vendor, same amount to the rupee, no number read, the date 6 days off -- NOT linked, the likely bill named)",
      st["s12"] and st["s12"]["why"] == "number_differs" and st["s12"]["hint_bill"] == B["b12"] and link("b12") == [None, None, None], st["s12"])
check("the page (200) carries the two new columns and the reason of each of the six open W439 scans, word for word",
      N["page_code"] == 200 and all(N["page_head"]) and all(N["page_why"].get(k) for k in ("w_nobill", "w_vendor", "w_amount", "w_digits", "s12", "s13b")), (N["page_head"], N["page_why"]))
check("the 'Marg bills with no scan' list names the open scan beside bill 439189 and bill 439634 ('is probably this bill -- do not scan again')", all(N["page_hint"]), N["page_hint"])

print("-- 4  the re-match runs when Marg's bill lands (the push door), and from the command line (the nightly cron, the install)")
check("the scan made before Marg had its bill waits with 'no bill on the server yet'; the push of bill 439777 (200, stored) links it at once: EXACT bill_tail+vendor+amount~2%, audited by 'push'",
      st["p1"] and st["p1"]["why"] == "no_bill_yet" and N["p1_before"] is None and N["push"][:2] == [200, True] and N["p1_after"] == [S["p1"], "EXACT", "bill_tail+vendor+amount~2%"]
      and N["p1_audit"] == [["push", "bill_tail+vendor+amount~2%"]], (N["push"], N["p1_after"], N["p1_audit"]))
check("'purchase_app.py rematch --list' (the cron line's command) exits 0, prints its one line with 0 new links, and lists the open scans with their reasons",
      N["cli"][0] == 0 and N["cli"][1] and N["cli"][2] and N["cli"][3], N["cli"])
check("after the push and the command line the earlier links are as they were (a stored link stays); the purchase hub and reception's Purchase orders screen still answer 200",
      all(N["links_end"].get(k) == v for k, v in L1.items()) and N["other_pages"] == [200, 200], (len(N["links_end"]), N["other_pages"]))
check("assets.db was only READ: the scratch copy is byte-identical after every pass", md5f(a.assets_db) == ASSETS_MD5)

print("-- 5  the bank-SMS door: any of the field names, the raw body, the bare address -- the way the phone really posts")
t = TODAY.isoformat()


def stored(x, sender):
    return (x[:2] == [200, True] and len(x[4]) == 1 and x[4][0]["unit"] == "medical" and x[4][0]["credit_date"] == t and x[4][0]["phone_sender"] == sender and x[4][0]["seen"] == 1
            and x[4][0]["doubled"] == 0)


check("a wrong key is still 401", N["sms_bad_key"] == 401, N["sms_bad_key"])
check("form fields message / from: the ICICI settlement is stored (unit medical, today's credit date, the sender kept)", stored(N["sms_message_from"], "W439-SENDER"), N["sms_message_from"][:4])
check("JSON fields body / number: the Yes Bank cash deposit is stored (cash_credit, the account tail, the sender)", N["sms_body_number"][:2] == [200, True] and N["sms_body_number"][3] == "cash_credit"
      and len(N["sms_body_number"][4]) == 1 and N["sms_body_number"][4][0]["amount_p"] == 4390200 and N["sms_body_number"][4][0]["acct_tail"] == "4439", N["sms_body_number"][:4])
check("a raw body with no field at all (text/plain): stored", stored(N["sms_raw_body"], ""), N["sms_raw_body"][:4])
check("THE PHONE'S REAL SHAPE -- the SMS as the bare query string of the address ('?<the SMS>=<the SMS>': no field name, no body): stored, one copy of the text kept", stored(N["sms_bare_query"], ""), N["sms_bare_query"][:4])
check("field names in any letter case (MESSAGE / From): stored", stored(N["sms_upper_json"], "W439-SENDER"), N["sms_upper_json"][:4])
check("the fields the door always read (text / sender) still work", stored(N["sms_text_sender"], "W439-SENDER"), N["sms_text_sender"][:4])
check("the key given in the address and the SMS as a bare name (?key=...&<the SMS>): the door opens and the SMS is stored", stored(N["sms_key_in_query"], ""), N["sms_key_in_query"][:4])
ir = N["ign_rows"]
r1 = next((x for x in ir if x[2] == "message,from,ts"), None)
check("a non-bank post (an OTP) is refused 200/ignored and KEEPS THE FIELD NAMES it carried ('message,from,ts') with its masked text (no 5+ digit run, 'Rs ####')",
      N["sms_refused"][:3] == [200, False, True] and N["ign_cols"] and r1 and r1[0] == "W439-SENDER" and r1[3] and r1[4] is False and r1[5], (N["sms_refused"], r1))
r2 = next((x for x in ir if (x[2] or "").startswith("(raw body")), None)
check("the key is never stored: a refused raw body that carried the key keeps '[key]' in its place; the key is in no row of the three tables, nor on the page beyond its own setup card",
      N["sms_refused_raw"][:3] == [200, False, True] and r2 and r2[6] and N["key_stored"] is False and N["sms_page"][4] is False, (r2, N["key_stored"]))
check("the owner's Bank SMS page (200): the Ignored card shows 'Fields it carried' with 'message,from,ts'; the phone-setup card names the accepted field names ('The macro does not have to change')",
      N["sms_page"][:4] == [200, True, True, True], N["sms_page"])
rp = N["replay"]
check("the web log replayed through the same door (the walk's own log lines): the bare-query post of 07:01:36 is stored with THAT time, the refused note of that second replaced, the {sms_message} test post and the 401 line skipped, nothing printed of the text",
      rp[0] == 0 and rp[1] and rp[2] and rp[3] is False and len(rp[6]) == 1 and rp[6][0]["received_at"] == N["replay_at"] and rp[6][0]["seen"] == 1 and rp[7] == [] and rp[8] == 0, rp)
check("the replay runs once per database: the second run says 'already replayed' and writes nothing", rp[4] == 0 and rp[5] and len(rp[6]) == 1, rp[4:6])
check("APP_VERSION stays S405's (its walk pins it); the S439 mark is beside it", N["version"] == ["S405-BANK-SMS-2.0", "S439-DOOR-1"], N["version"])

print("-- 6  the Days section keeps its place (the page's own script, read as text: no browser here)")


def func(src, name):
    i = src.index("function %s(" % name)
    j = src.index("{", i)
    depth, k = 0, j
    while True:
        depth += {"{": 1, "}": -1}.get(src[k], 0)
        if depth == 0:
            return src[i:k + 1]
        k += 1


new_html = io.open(os.path.join(a.app, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
old_html = io.open(os.path.join(a.old, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
fa_new, fa_old = func(new_html, "approve"), func(old_html, "approve")
check("approve() no longer calls load() (the whole page); its success path calls daysStay()", "daysStay()" in fa_new and not re.search(r"(?<![A-Za-z.])load\(\)", fa_new), fa_new[-260:])
ds = func(new_html, "daysStay") if "function daysStay(" in new_html else ""
dk = func(new_html, "daysKeep") if "function daysKeep(" in new_html else ""
order = [dk.find(x) for x in ("window.pageYOffset", "open:ms[i].open, top:w?w.scrollTop:0", "fn();", "ms[i].open=true", "w.scrollTop=k.top", "window.scrollTo(0,y)")]
check("daysKeep() records the page's offset, the open months and each month box's own scroll, THEN draws, THEN re-opens those months, puts each box's scroll back and restores the offset -- in that order",
      all(x >= 0 for x in order) and order == sorted(order), order)
check("daysStay() draws the Days section through it (daysKeep around DAYS=j; renderDays()); the month box is the page's own 430px scroll box (.tblwrap)",
      "daysKeep(function(){ DAYS=j; renderDays() })" in ds and ".tblwrap{max-height:430px;overflow:auto" in new_html, ds[:200])
calls = sorted(set(re.findall(r"\b(load[A-Za-z]*)\(\)", ds)))
check("it reads again only Days, the Needs-you strip, the Cash card and (if it was opened) the old queue -- never load(), the bank, the months, the returns or the alert bar",
      calls == ["loadCashPos", "loadDays", "loadNeeds", "loadOld"] and "/finance/sanjeevni/api/days" in ds, calls)
gone = [x for x in old_html.splitlines() if x not in set(new_html.splitlines())]
check("ONE change in the parent's page: the only line that left it is approve()'s 'openDays[d]=false; load();'", gone == ["      openDays[d]=false; load();"], gone)

print("-- 7  NEGATIVE CONTROLS on the box as it is (the unpatched files, the same crafted rows)")
OL = O["links1"]
forms = ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9", "b11", "b14", "b15"]
check("NEGATIVE: the old matcher links NONE of the forms (prefix / zeros / dashes / bracket / buyer / misspelt vendor / date 2 days off): %d of 12; only the exact first scan of bill 439175 links" % sum(1 for b in forms if str(B[b]) in OL),
      not any(str(B[b]) in OL for b in forms) and OL.get(str(B["b13"]), [None])[0] == S["s13a"], OL)
check("NEGATIVE: the old scan-links page has no reason column and no probable-scan column; the old push of bill 439777 stores it and links nothing; the old file has no command line",
      O["page_code"] == 200 and not any(O["page_head"]) and O["push"][:2] == [200, True] and O["p1_after"] is None and O["cli"][1] is False, (O["page_head"], O["push"], O["p1_after"], O["cli"][:2]))
oi = O["ign_rows"]
check("NEGATIVE: the old door drops the fields -- message/from, a raw body and the bare query are all refused with an EMPTY text and no field names kept; only text/sender is stored",
      O["sms_message_from"][:3] == [200, False, True] and O["sms_raw_body"][:3] == [200, False, True] and O["sms_bare_query"][:3] == [200, False, True] and O["sms_text_sender"][:2] == [200, True]
      and O["ign_cols"] is False and sum(1 for x in oi if not x[3]) >= 3, (O["sms_message_from"][:3], O["sms_bare_query"][:3], O["ign_cols"], oi[:3]))
check("NEGATIVE: the old approve() calls load() and the old page has no daysStay()", bool(re.search(r"(?<![A-Za-z.])load\(\)", fa_old)) and "daysStay" not in old_html)

print(("WALK_S439 GREEN -- %d of %d passed" % (n, n)) if not fails else ("WALK_S439 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
