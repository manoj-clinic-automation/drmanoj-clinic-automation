#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s408.py -- kit S408_MONTH_END_PACKS. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over a
SCRATCH COPY of finance.db and a scratch assets.db; Drive is NOT called -- a fixture folder of crafted statement PDFs stands in
(STMT_DRIVE_STUB); the mail is NOT sent -- the sender writes .eml files (PACKS_MAIL_STUB) whose parts and attachments are
asserted; 'today' is set (PACKS_TODAY). Its own rows are keyed W408*; the fixture accounts end in 408x. Never a real email,
never a Drive read, never the live databases.

  --app NEW --old OLD --db PATH --assets-db PATH --portal-new DIR --portal-old DIR
"""
import argparse
import datetime as dt
import io
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--db", "--assets-db", "--portal-new", "--portal-old"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
assert a.assets_db.startswith("/tmp") or "walk" in a.assets_db, "refusing a non-scratch assets database"
n, fails = 0, []
W = os.path.dirname(os.path.abspath(a.db))
STUB = os.path.join(W, "stub408")
INBOX = os.path.join(W, "inbox408")
MAIL = os.path.join(W, "mail408")
UP = os.path.join(W, "uploads408")
for d in (os.path.join(STUB, "bank", "2026"), os.path.join(STUB, "cards", "HDFC Business Regalia"), os.path.join(STUB, "decrypted", "HDFC Business Regalia"), INBOX, MAIL, UP):
    os.makedirs(d, exist_ok=True)


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


def text_pdf(path, lines):
    """A minimal text PDF (Helvetica, one page per 55 lines) -- pdftotext -layout reads it back line for line."""
    pages = [lines[i:i + 55] for i in range(0, len(lines), 55)] or [[]]
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", None, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"]
    kids = []
    for pg in pages:
        content = b"BT /F1 10 Tf 12 TL 40 800 Td " + b" ".join(b"(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace") + b") Tj T*" for ln in pg) + b" ET"
        objs.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        c = len(objs)
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % c)
        kids.append(len(objs))
    objs[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    out = bytearray(b"%PDF-1.4\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    with open(path, "wb") as fh:
        fh.write(bytes(out))


ICICI = ["ICICI Bank Limited", "Statement of Account", "SANJEEVNI MEDICOS   CURRENT ACCOUNT", "Account Number: 000401004082",
         "Statement Period: 01/08/2026 To 31/08/2026", "Opening Balance 1,00,000.00", "",
         "Date        Particulars                          Deposits     Withdrawals     Balance",
         "05/08/2026  CASH DEP-SELF SANJEEVNI              10,000.00                    1,10,000.00",
         "12/08/2026  BIL/ONL/PVVNL ELECTRICITY BAREILLY                2,500.00       1,07,500.00",
         "20/08/2026  ICICIPOS SETTLEMENT                  5,000.00                     1,12,500.00",
         "", "Closing Balance 1,12,500.00"]
text_pdf(os.path.join(STUB, "bank", "2026", "icici_sanj_aug.pdf"), ICICI)
text_pdf(os.path.join(W, "icici_tampered.pdf"), [l.replace("1,12,500.00", "1,12,600.00") if l.startswith("20/08") else l for l in ICICI])
text_pdf(os.path.join(STUB, "bank", "2026", "yes_sanj_aug.pdf"), ["YES BANK LIMITED", "Account Statement", "SANJEEVNI MEDICOS", "CURRENT ACCOUNT", "Account No: 000000004081", "Statement Period: 01/08/2026 to 31/08/2026", "Transaction Date  Description  Deposits  Withdrawals  Balance", "05/08/2026 CASH DEP-SELF-SANJEEVNI MEDICOS 1,000.00 5,000.00"])
text_pdf(os.path.join(STUB, "bank", "2026", "yes_huf_aug.pdf"), ["YES BANK LIMITED", "Account Statement", "MANOJ KUMAR AGARWAL HUF", "SAVINGS ACCOUNT", "Account No: 000000004083", "Statement Period: 01/08/2026 to 31/08/2026"])
text_pdf(os.path.join(STUB, "bank", "2026", "yes_unknown_aug.pdf"), ["YES BANK LIMITED", "Account Statement", "SOME OTHER HOLDER", "SAVINGS ACCOUNT", "Account No: 000000004089", "Statement Period: 01/08/2026 to 31/08/2026"])
text_pdf(os.path.join(STUB, "cards", "HDFC Business Regalia", "hdfc_aug_locked.pdf"), ["HDFC Bank", "Business Regalia Credit Card Statement", "Card Number: XXXX XXXX XXXX 4084", "Statement Date: 31/08/2026", "Minimum Amount Due 1,000.00"])
text_pdf(os.path.join(STUB, "decrypted", "HDFC Business Regalia", "hdfc_aug.pdf"), ["HDFC Bank", "Business Regalia Credit Card Statement", "Card Number: XXXX XXXX XXXX 4084", "Statement Date: 31/08/2026", "Minimum Amount Due 1,000.00"])
text_pdf(os.path.join(STUB, "cards", "HDFC Business Regalia", "hdfc_sep_locked.pdf"), ["HDFC Bank", "Business Regalia Credit Card Statement", "Card Number: XXXX XXXX XXXX 4084", "Statement Date: 30/09/2026", "Minimum Amount Due 1,200.00"])
_t = __import__("time").time()
os.utime(os.path.join(STUB, "cards", "HDFC Business Regalia", "hdfc_aug_locked.pdf"), (_t - 3 * 86400, _t - 3 * 86400))
os.utime(os.path.join(STUB, "decrypted", "HDFC Business Regalia", "hdfc_aug.pdf"), (_t - 2 * 86400, _t - 2 * 86400))
os.utime(os.path.join(STUB, "cards", "HDFC Business Regalia", "hdfc_sep_locked.pdf"), (_t, _t))
from openpyxl import Workbook  # noqa: E402
wb = Workbook()
wb.active.append(["Date", "Card", "Amount"])
wb.save(os.path.join(STUB, "all_transactions.xlsx"))
subprocess.run(["convert", "-size", "600x800", "xc:white", "-fill", "black", "-pointsize", "30", "-draw", "text 40,100 'W408 LAB BILL'", "-draw", "rectangle 40,300 560,340", os.path.join(UP, "w408_lab1.jpg")], check=True)
subprocess.run(["convert", "-size", "600x800", "xc:white", "-fill", "black", "-pointsize", "30", "-draw", "text 40,100 'W408 LAB BILL LATE'", "-draw", "rectangle 40,500 560,540", os.path.join(UP, "w408_lab2.jpg")], check=True)
subprocess.run(["convert", "-size", "600x800", "xc:white", "-fill", "black", "-pointsize", "30", "-draw", "text 40,100 'W408 EXPENSE'", "-draw", "rectangle 300,100 560,700", os.path.join(UP, "w408_exp1.jpg")], check=True)

copydb(a.db, a.db + ".old")
copydb(a.assets_db, a.assets_db + ".old")
sys.path.insert(0, a.app)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FINANCE_DIR"] = a.app
os.environ["FINANCE_DB"] = a.db
import seed_s408  # noqa: E402
assert seed_s408.seed(a.db) == 0, "seed failed"
db0 = sqlite3.connect(a.db)
db0.execute("UPDATE setting SET value='w408a@example.invalid,w408b@example.invalid' WHERE key='packs.accountant_to'")
db0.commit()
db0.close()
adb = sqlite3.connect(a.assets_db)
acols = {r[1] for r in adb.execute("PRAGMA table_info(bills)")}
assert "lane" in acols, "the scratch assets.db has no lane column -- S409 must be installed first"
adb.execute("DELETE FROM bills WHERE vendor LIKE 'W408%'")
adb.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, source_stored, stamp_no, status, submitted_by, submitted_at, lane, created_at) VALUES ('Lab','W408 LAB VENDOR','L-1','2026-08-12',1500.0,'w408_lab1.jpg','B-9401','captured','walk','2026-08-12T10:00:00','lab_purchase','2026-08-12 04:30:00')")
adb.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, source_stored, stamp_no, status, submitted_by, submitted_at, lane, late_for, created_at) VALUES ('Lab','W408 LAB VENDOR','L-2','2026-07-20',900.0,'w408_lab2.jpg','B-9402','captured','walk','2026-08-14T10:00:00','lab_purchase','2026-07','2026-08-14 04:30:00')")
adb.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, source_stored, stamp_no, status, submitted_by, submitted_at, lane, created_at) VALUES ('Expense','W408 EXP VENDOR','E-1','2026-08-20',2500.0,'w408_exp1.jpg','B-9403','captured','walk','2026-08-20T10:00:00','owner_expense','2026-08-20 04:30:00')")
adb.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, source_stored, stamp_no, status, submitted_by, submitted_at, lane, created_at) VALUES ('Lab','W408 LAB VENDOR','L-3','2026-08-22',300.0,'w408_lab1.jpg','B-9404','rejected','walk','2026-08-22T10:00:00','lab_purchase','2026-08-22 04:30:00')")
adb.commit()
adb.close()
print("-- scratch copies made and seeded; the fixture Drive (%d PDFs), three crafted scans, the mail stub" % sum(len(f) for _r, _d, f in os.walk(STUB)))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re, io, subprocess, glob
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else (r.get_data(as_text=True) if (r.mimetype or "").startswith("text") or (r.mimetype or "").endswith("json") else r.get_data())]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True), r.headers.get("Location", "")]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
one = lambda s, *a: db.execute(s, a).fetchone()[0]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
M = "2026-08"
out = {"unit": fa._unit_for_path("/finance/packs/api/state"), "mounted": "packs" in fa.app.blueprints}
out["page_owner"] = G("manoj", "/finance/packs")[0]
out["page_gate"] = {u: G(u, "/finance/packs")[0] for u in ("bhati", "darpan", "amir", "shavez")}
out["chk_gate"] = {u: G(u, "/finance/packs/checklist")[0] for u in ("shavez", "manoj", "bhati", "amir")}
out["amir_old"] = G("amir", "/finance/amir/step/1"); out["amir_old"] = [out["amir_old"][0], "Pichle mahine ka pack" in str(out["amir_old"][1])]
out["needs0"] = [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", [])]
out["tables"] = {t: has(t) for t in ("stmt_slot", "stmt_file", "pack_send", "packs_item")}
if not NEW:
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
import packs, stmt_shelf, finance_icici
# --- the shelf: fetch from the fixture Drive, identify by content
new, seen, errors = stmt_shelf.fetch(db)
out["fetch"] = [new, seen, errors]
out["process"] = packs.process_inbox(db)
F = {r["name"]: r for r in q("SELECT f.*, s.key AS slot_key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id")}
out["placed"] = {k: [v["slot_key"], v["ident_how"], v["tail"], v["period_from"], v["period_to"], v["read_status"], v["matched_status"], v["note"]] for k, v in F.items()}
out["icici_lines"] = q("SELECT txn_date, description, deposit_p, withdrawal_p, balance_p FROM bank_statement_line WHERE account_ref='4082' ORDER BY txn_date")
out["icici_period"] = q("SELECT account_ref, period_from, period_to, opening_p, closing_p FROM bank_statement_period WHERE account_ref='4082'")
out["anchor"] = q("SELECT account, as_on, source FROM bank_anchor WHERE unit='medical' AND account='icici'")
try:
    finance_icici.parse_statement(open(os.environ["TAMPERED"], "rb").read()); out["tamper"] = "NOT CAUGHT"
except finance_icici.StatementRejected as ex:
    out["tamper"] = str(ex)[:120]
out["cells"] = {x["slot"]: [x["state"], bool(x["file"]), x["twin_missing"]] for x in packs.cells(db, M)}
out["unplaced"] = [[u["name"], u["tail"], u["why"]] for u in packs.unplaced(db)]
# --- the owner's one tap: the unknown file is Dr Bhawna's savings -> the tail is learned; a later file of the same tail lands by itself
uf = next((u for u in packs.unplaced(db) if u["tail"] == "4089"), None)
sid = one("SELECT id FROM stmt_slot WHERE key='yes_sav_bhawna'")
out["assign"] = P("manoj", "/finance/packs/api/assign", {"file": uf["id"] if uf else 0, "slot": sid})
out["assign_darpan"] = P("darpan", "/finance/packs/api/assign", {"file": uf["id"] if uf else 0, "slot": sid})[0]
out["tail_learned"] = q("SELECT ident_tail, owner_set FROM stmt_slot WHERE key='yes_sav_bhawna'")
open(os.path.join(os.environ["STMT_DRIVE_STUB"], "bank", "2026", "yes_unknown_sep.pdf"), "wb").write(open(os.environ["TAMPERED"].replace("icici_tampered.pdf", "yes_sep_src.pdf"), "rb").read())
stmt_shelf.fetch(db); packs.process_inbox(db)
sep = q("SELECT f.ident_how, s.key AS slot_key, f.period_from FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.name='yes_unknown_sep.pdf'")
out["sep_by_tail"] = sep
# --- Needs you: after the 10th / before it
os.environ["PACKS_TODAY"] = "2026-09-12"
out["needs_after10"] = [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", []) if "shelf" in l["text"] or "checklist" in l["text"]]
os.environ["PACKS_TODAY"] = "2026-09-05"
out["needs_before10"] = [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", []) if "shelf" in l["text"] or "checklist" in l["text"]]
os.environ["PACKS_TODAY"] = "2026-09-12"
# --- the pack rows
st = G("manoj", "/finance/packs/api/state?month=" + M)[1]
out["rows"] = {r["key"]: [r["status"], r["why"][:90], r["files"]] for r in st["rows"]}
out["row_keys"] = sorted(out["rows"].keys())
out["electricity"] = out["rows"].get("electricity")
out["att"] = [(x["name"], x["bytes"]) for x in st["attachments"]]
bpdf = G("manoj", "/finance/packs/preview/bundle_lab_purchase?month=" + M)
idx = ""
if bpdf[0] == 200:
    p = os.path.join(os.environ["WALKDIR"], "bundle_lab.pdf"); open(p, "wb").write(bpdf[1] if isinstance(bpdf[1], bytes) else bpdf[1].encode())
    idx = subprocess.run(["pdftotext", "-l", "1", p, "-"], stdout=subprocess.PIPE).stdout.decode("utf-8", "replace")
    pages = subprocess.run(["pdfinfo", p], stdout=subprocess.PIPE).stdout.decode("utf-8", "replace")
    out["bundle"] = [bpdf[0], "B-9401" in idx, "B-9402" in idx, "Late, belongs to 2026-07" in idx, "B-9403" in idx, "B-9404" in idx, re.search(r"Pages:\s+(\d+)", pages).group(1) if re.search(r"Pages:\s+(\d+)", pages) else None]
else:
    out["bundle"] = [bpdf[0]]
out["income_prev"] = G("manoj", "/finance/packs/preview/income?month=" + M)[0]
out["upi_prev"] = G("manoj", "/finance/packs/preview/upi?month=" + M)[0]
# --- the two paper ticks; the send (stub), the split, the re-send, the 10-minute guard
out["tick"] = [P("manoj", "/finance/packs/api/tick", {"month": M, "item": "lab_register"})[0], P("darpan", "/finance/packs/api/tick", {"month": M, "item": "lab_register"})[0]]
s1 = P("manoj", "/finance/packs/api/send", {"month": M}); out["send1"] = [s1[0], (s1[1] or {}).get("parts"), (s1[1] or {}).get("attachments"), (s1[1] or {}).get("resend")]
emls = sorted(glob.glob(os.path.join(os.environ["PACKS_MAIL_STUB"], "pack_%s_part*.eml" % M)))
import email
m1 = email.message_from_bytes(open(emls[0], "rb").read()) if emls else None
out["eml1"] = [len(emls), m1["To"] if m1 else None, m1["Subject"] if m1 else None, [p.get_filename() for p in m1.walk() if p.get_filename()] if m1 else None]
out["send_repeat"] = (P("manoj", "/finance/packs/api/send", {"month": M})[1] or {}).get("already")
db.execute("UPDATE pack_send SET sent_at=? WHERE month=?", ((dt.datetime.now() - dt.timedelta(minutes=11)).replace(microsecond=0).isoformat(), M)); db.commit()
db.execute("UPDATE setting SET value='0.05' WHERE key='packs.mail_limit_mb'"); db.commit()
for f in glob.glob(os.path.join(os.environ["PACKS_MAIL_STUB"], "*.eml")): os.remove(f)
s2 = P("manoj", "/finance/packs/api/send", {"month": M}); out["send2"] = [s2[0], (s2[1] or {}).get("parts"), (s2[1] or {}).get("resend")]
emls2 = sorted(glob.glob(os.path.join(os.environ["PACKS_MAIL_STUB"], "pack_%s_part*.eml" % M)))
out["eml2"] = [len(emls2), all(("part %d of %d" % (i, len(emls2))) in email.message_from_bytes(open(e, "rb").read())["Subject"] for i, e in enumerate(emls2, 1)), all("resend" in email.message_from_bytes(open(e, "rb").read())["Subject"] for e in emls2)]
out["sends"] = q("SELECT month, sent_by, parts, resend FROM pack_send WHERE month=? ORDER BY id", M)
out["send_bhati"] = P("bhati", "/finance/packs/api/send", {"month": M})[0]
# --- Amir's pack
ap_ = packs.amir_pack(db, M); out["amir_ready"] = [ap_["ready"], bool(ap_["yes"]), bool(ap_["icici"])]
am = G("amir", "/finance/amir/step/1"); out["amir_card"] = [am[0], "Pichle mahine ka pack" in str(am[1]), "August 2026" in str(am[1]), "Dekh liya" in str(am[1])]
out["amir_neft"] = G("amir", "/finance/amir/pack/%s/neft" % M)[0]
out["amir_yes"] = G("amir", "/finance/amir/pack/%s/yes" % M)[0]
out["amir_icici"] = G("amir", "/finance/amir/pack/%s/icici" % M)[0]
out["amir_seen"] = P("amir", "/finance/amir/pack/%s/seen" % M)[0]
out["amir_tick"] = q("SELECT done_by FROM pack_tick WHERE month=? AND item='amir_seen'", M)
am2 = G("amir", "/finance/amir/step/1"); out["amir_card2"] = "dekh liya" in str(am2[1])
out["amir_pack_gate"] = G("bhati", "/finance/amir/pack/%s/neft" % M)[0]
# --- Shavez's checklist
cl = G("shavez", "/finance/packs/api/checklist?month=" + M)[1]
items = cl["items"]
man = next(i for i in items if not i["auto"] and not i["done"])
auto_ = next(i for i in items if i["auto"])
out["chk"] = [len(items), sorted(set(i["grp"] for i in items)), sum(1 for i in items if i["auto"]), sum(1 for i in items if i["done"])]
out["chk_tick"] = P("shavez", "/finance/packs/api/checklist/tick", {"month": M, "id": man["id"]})
out["chk_tick_again"] = (P("shavez", "/finance/packs/api/checklist/tick", {"month": M, "id": man["id"]})[1] or {}).get("already")
out["chk_tick_auto"] = P("shavez", "/finance/packs/api/checklist/tick", {"month": M, "id": auto_["id"]})[0]
out["chk_tick_bhati"] = P("bhati", "/finance/packs/api/checklist/tick", {"month": M, "id": man["id"]})[0]
cl2 = G("shavez", "/finance/packs/api/checklist?month=" + M)[1]
out["chk_after"] = [x for x in cl2["items"] if x["id"] == man["id"]][0]
out["chk_sent_auto"] = [x for x in cl2["items"] if x["item"].startswith("Pack accountant")][0]["done"]
pg = G("shavez", "/finance/packs/checklist")[1]
out["chk_page"] = ["Mahine ka kaam" in pg, "system se ho gaya" in pg]
out["owner_open"] = len(packs.open_items(db, M))
out["item_add"] = P("manoj", "/finance/packs/api/item", {"action": "add", "grp": "Lab", "item": "W408 naya kaam"})[0]
out["item_added"] = q("SELECT grp, item, source FROM packs_item WHERE item='W408 naya kaam'")
out["item_shavez"] = P("shavez", "/finance/packs/api/item", {"action": "add", "grp": "Lab", "item": "x"})[0]
opg = G("manoj", "/finance/packs")[1]
out["owner_page"] = ["Send to accountants" in opg, "The statement shelf" in opg, "which account?" in opg.lower() or "Unplaced" in opg]
print("JSON:" + json.dumps(out, default=str))
'''

text_pdf(os.path.join(W, "yes_sep_src.pdf"), ["YES BANK LIMITED", "Account Statement", "SOME OTHER HOLDER", "SAVINGS ACCOUNT", "Account No: 000000004089", "Statement Period: 01/09/2026 to 30/09/2026"])


def probe(appdir, mode, dbpath, adbpath):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1",
               ASSETS_DB=adbpath, ASSETS_UPLOADS=UP, STMT_DRIVE_STUB=STUB, STMT_INBOX=INBOX + "_" + mode, PACKS_MAIL_STUB=MAIL, PACKS_TODAY="2026-09-12",
               TAMPERED=os.path.join(W, "icici_tampered.pdf"), WALKDIR=W, PACKS_ENV=os.path.join(W, "no.env"))
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, "old", a.db + ".old", a.assets_db + ".old")
N = probe(a.app, "new", a.db, a.assets_db)

print("-- 1  the unit, the pages, the gate")
check("finance_app resolves /finance/packs/... to the unit 'packs' and mounts packs; the owner opens the page (200)", N["unit"] == "packs" and N["mounted"] and N["page_owner"] == 200, (N["unit"], N["mounted"], N["page_owner"]))
check("bhati, darpan, amir and shavez cannot open the owner's page (302/403); shavez and the owner open the checklist, bhati and amir cannot",
      all(v in (302, 403) for v in N["page_gate"].values()) and N["chk_gate"]["shavez"] == 200 and N["chk_gate"]["manoj"] == 200 and N["chk_gate"]["bhati"] in (302, 403) and N["chk_gate"]["amir"] in (302, 403), (N["page_gate"], N["chk_gate"]))

print("-- 2  the shelf: identification by content (the fixture Drive stands in)")
pl = N["placed"]
check("the fetch took every fixture file (%d new); nothing errored" % N["fetch"][0], N["fetch"][0] >= 7 and N["fetch"][2] == [], N["fetch"])
check("the Yes Bank current statement -> Sanjeevni's slot by its words; the ICICI one -> ICICI Sanjeevni; the HUF savings -> the HUF slot; each with its tail and period",
      pl["yes_sanj_aug.pdf"][0] == "yes_cur_sanj" and pl["yes_sanj_aug.pdf"][2] == "4081" and pl["icici_sanj_aug.pdf"][0] == "icici_sanj" and pl["icici_sanj_aug.pdf"][2] == "4082"
      and pl["yes_huf_aug.pdf"][0] == "yes_sav_huf" and pl["yes_huf_aug.pdf"][3:5] == ["2026-08-01", "2026-08-31"], {k: v[:5] for k, v in pl.items()})
check("the card statement: the locked original filed as 'locked original', the decrypted twin placed on the HDFC card slot; a file whose holder no slot names is UNPLACED with the reason",
      pl["hdfc_aug_locked.pdf"][0] == "card_hdfc_regalia" and pl["hdfc_aug_locked.pdf"][5] == "locked original" and pl["hdfc_aug.pdf"][0] == "card_hdfc_regalia"
      and pl["yes_unknown_aug.pdf"][0] is None and "no slot" in (pl["yes_unknown_aug.pdf"][7] or ""), (pl["hdfc_aug_locked.pdf"][:6], pl["hdfc_aug.pdf"][:6], pl["yes_unknown_aug.pdf"]))
check("the ICICI reader read the fixture into bank_statement_period/_line (tail 4082, 01..31-Aug, opening 1,00,000, closing 1,12,500, three lines placed by the running balance; the cash deposit flagged)",
      pl["icici_sanj_aug.pdf"][5] == "read" and N["icici_period"] == [{"account_ref": "4082", "period_from": "2026-08-01", "period_to": "2026-08-31", "opening_p": 10000000, "closing_p": 11250000}]
      and [(l["deposit_p"], l["withdrawal_p"], l["balance_p"]) for l in N["icici_lines"]] == [(1000000, 0, 11000000), (0, 250000, 10750000), (500000, 0, 11250000)], (N["icici_period"], N["icici_lines"]))
check("NEGATIVE CONTROL: the same statement with one running balance changed by ₹100 is REFUSED, naming the row", "does not carry the balance" in N["tamper"] and "20/08/2026" in N["tamper"], N["tamper"])
check("the Yes Bank fixture is placed but its READ is refused by finance_yesbank (a crafted text, not the bank's PDF) -- and the shelf says so instead of pretending", str(pl["yes_sanj_aug.pdf"][5]).startswith("refused"), pl["yes_sanj_aug.pdf"][5])
check("bank_anchor for ICICI Sanjeevni is NOT moved by an August statement (the live anchor is already as-on 31-Aug)", N["anchor"] and N["anchor"][0]["as_on"] >= "2026-08-31", N["anchor"])
cl = N["cells"]
check("the August cells: ICICI Sanjeevni matched, Yes Bank Sanjeevni arrived (read refused), HUF arrived, the HDFC card read with 'newest original has no decrypted twin'; the rest empty",
      cl["icici_sanj"][0] == "matched" and cl["yes_cur_sanj"][0] == "arrived" and cl["yes_sav_huf"][0] == "arrived" and cl["card_hdfc_regalia"][0] == "read" and cl["card_hdfc_regalia"][2] is True
      and cl["yes_cur_nk"][0] == "empty" and cl["icici_clinic"][0] == "empty", cl)
check("the owner's one tap files the unknown file as Dr Bhawna's savings and the slot learns the tail 4089 for ever (darpan cannot); the September file of that tail then lands BY TAIL on its own",
      N["assign"][0] == 200 and N["assign"][1]["tail_learned"] == "4089" and N["assign_darpan"] in (302, 403) and N["tail_learned"][0]["ident_tail"] == "4089"
      and N["sep_by_tail"] and N["sep_by_tail"][0]["slot_key"] == "yes_sav_bhawna" and N["sep_by_tail"][0]["ident_how"] == "by tail", (N["assign"], N["tail_learned"], N["sep_by_tail"]))

print("-- 3  Needs you after the 10th; the pack rows")
check("on the 12th the owner's Needs you names the previous month's empty cells and Shavez's open items; on the 5th it says nothing",
      len(N["needs_after10"]) == 2 and any("statement" in t for t in N["needs_after10"]) and any("checklist" in t for t in N["needs_after10"]) and N["needs_before10"] == [], (N["needs_after10"], N["needs_before10"]))
R = N["rows"]
check("every item of the owner's list is a row with ready / missing (why) / late / tick: %d rows" % len(R), all(v[0] in ("ready", "missing", "late", "tick") and (v[0] == "ready" or v[1]) for v in R.values())
      and {"income", "upi", "electricity", "neft", "digest", "bundle:lab_purchase", "bundle:owner_expense", "cards", "lab_register", "lab_receipt_book"} <= set(R), {k: v[:2] for k, v in R.items()})
check("electricity: the ICICI line 'PVVNL' of the fixture reads 'auto-paid ₹2,500 on 12-Aug-2026 from account …4082'", R["electricity"][0] == "ready" and "₹2,500" in R["electricity"][1] and "12-Aug-2026" in R["electricity"][1] and "4082" in R["electricity"][1], R["electricity"])
check("the Sanjeevni NEFT row (August is final on the live sheet): advice Excel + letter ready", R["neft"][0] == "ready" and len(R["neft"][2]) == 2, R["neft"])
check("the lab bundle: one PDF -- the index page names B-9401 and B-9402 ('Late, belongs to 2026-07'), not the rejected B-9404; the expense bundle ready; the two Excel previews answer",
      N["bundle"][0] == 200 and N["bundle"][1] and N["bundle"][2] and N["bundle"][3] and N["bundle"][5] is False and int(N["bundle"][6] or 0) >= 3 and R["bundle:owner_expense"][0] == "ready" and N["income_prev"] in (200, 404) and N["upi_prev"] in (200, 404), (N["bundle"], R["bundle:owner_expense"], N["income_prev"], N["upi_prev"]))
check("the card rows: the HDFC card reads 'late' with 'no decrypted twin'; All_Transactions.xlsx fetched and ready", R["card:card_hdfc_regalia"][0] == "late" and "no decrypted twin" in R["card:card_hdfc_regalia"][1] and R["cards"][0] == "ready", (R["card:card_hdfc_regalia"], R["cards"]))

print("-- 4  the Send (stubbed): one mail, the receipt, the split, the re-send, the guards")
check("the owner ticks a paper item (darpan cannot); Send builds ONE mail to the two addresses with every ready attachment and writes pack_send",
      N["tick"][0] == 200 and N["tick"][1] in (302, 403) and N["send1"][0] == 200 and N["send1"][1] == 1 and N["send1"][2] >= 4 and N["eml1"][0] == 1 and "w408a@example.invalid" in N["eml1"][1] and "accounts pack August 2026" in N["eml1"][2] and len(N["eml1"][3]) >= 4, (N["tick"], N["send1"], N["eml1"]))
check("a repeat within 10 minutes is not sent again (already); with the limit at 0.05 MB the next send goes as parts 1..N, each subject 'part i of N' and 'resend'; both recorded, bhati refused",
      N["send_repeat"] is True and N["send2"][0] == 200 and N["send2"][1] >= 2 and N["send2"][2] is True and N["eml2"][0] == N["send2"][1] and N["eml2"][1] and N["eml2"][2]
      and len(N["sends"]) == 1 + N["send2"][1] and N["sends"][-1]["resend"] == 1 and N["send_bhati"] in (302, 403), (N["send_repeat"], N["send2"], N["eml2"], N["sends"], N["send_bhati"]))

print("-- 5  Amir's pack (Sanjeevni)")
check("with both Sanjeevni statements on the shelf the pack is ready; Amir's board carries 'Pichle mahine ka pack — August 2026' with Dekh liya; the three pieces open (Excel 200, the two PDFs 200); the tick stores and the card says dekh liya; bhati refused",
      N["amir_ready"] == [True, True, True] and N["amir_card"] == [200, True, True, True] and N["amir_neft"] == 200 and N["amir_yes"] == 200 and N["amir_icici"] == 200 and N["amir_seen"] == 303
      and N["amir_tick"] == [{"done_by": "amir"}] and N["amir_card2"] and N["amir_pack_gate"] in (302, 403), (N["amir_ready"], N["amir_card"], N["amir_neft"], N["amir_yes"], N["amir_icici"], N["amir_seen"], N["amir_tick"], N["amir_pack_gate"]))

print("-- 6  Shavez's checklist")
check("the checklist lists the four groups (%d items, %d automatic); a manual tick stores once (again = already); an automatic item refuses a tick (409); bhati refused; 'Pack accountant ko bheja' reads done by the system after the send" % (N["chk"][0], N["chk"][2]),
      N["chk"][0] >= 18 and set(N["chk"][1]) == {"Sanjeevni", "Lab", "Clinic", "Accountant ka samaan"} and N["chk_tick"][0] == 200 and N["chk_tick_again"] is True and N["chk_tick_auto"] == 409 and N["chk_tick_bhati"] in (302, 403)
      and N["chk_after"]["done"] and N["chk_after"]["done_by"] == "shavez" and N["chk_sent_auto"] is True, (N["chk"], N["chk_tick"], N["chk_tick_again"], N["chk_tick_auto"], N["chk_tick_bhati"], N["chk_after"], N["chk_sent_auto"]))
check("the Hindi page renders; the owner sees the open items (%d) and edits the list (add 200, source owner); shavez cannot edit" % N["owner_open"], all(N["chk_page"]) and N["owner_open"] >= 1 and N["item_add"] == 200 and N["item_added"] and N["item_added"][0]["source"] == "owner" and N["item_shavez"] in (302, 403), (N["chk_page"], N["item_add"], N["item_added"], N["item_shavez"]))
check("the owner's page carries the shelf, the Send and the unplaced list", all(N["owner_page"]), N["owner_page"])

print("-- 7  NEGATIVE CONTROLS on the box as it is (the unpatched files)")
check("NEGATIVE: no packs unit (%s), nothing mounted, /finance/packs not 200, no shelf tables, Amir's page without the card, Needs you without the lines" % O["unit"],
      O["unit"] != "packs" and not O["mounted"] and O["page_owner"] != 200 and not any(O["tables"].values()) and O["amir_old"][1] is False and not any("shelf" in t or "checklist" in t for t in O["needs0"]), (O["unit"], O["mounted"], O["page_owner"], O["tables"], O["amir_old"]))

print("-- 8  the portal tiles")


def tiles(pdir):
    src = io.open(os.path.join(pdir, "portal.py"), encoding="utf-8").read()
    head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
    ns = {"__name__": "p", "__file__": os.path.join(pdir, "portal.py")}
    exec(compile(head, "<p>", "exec"), ns)
    return {(u, r): sorted(sum([[t["name"] for t in ts] for g, ts in ns["_visible_sections"](r, False, u)], []))
            for u in ("manoj", "bhawna", "darpan", "shavez", "bhati", "alisha", "shivani", "amir", "nobody") for r in ("doctor", "staff", "manager")}


try:
    T0, T1 = tiles(a.portal_old), tiles(a.portal_new)
    changed = sorted(k for k in T0 if T0[k] != T1[k])
    check("'Month-end packs' shows for the doctor only; 'Mahine ka kaam' for shavez (staff) and the doctor", "Month-end packs" in T1[("manoj", "doctor")] and "Mahine ka kaam" in T1[("shavez", "staff")] and "Mahine ka kaam" in T1[("manoj", "doctor")]
          and "Month-end packs" not in T1[("shavez", "staff")] and "Mahine ka kaam" not in T1[("alisha", "staff")], (T1[("shavez", "staff")], [x for x in T1[("manoj", "doctor")] if "pack" in x.lower() or "Mahine" in x]))
    check("no other login loses or gains anything", all(k[0] == "shavez" or k[1] == "doctor" for k in changed) and all(not (set(T0[k]) - set(T1[k])) for k in changed), changed)
    g = json.load(open(os.path.join(a.portal_new, "tile_grants.json"), encoding="utf-8"))
    check("tile_grants.json is v29 and grants 'Mahine ka kaam' to shavez by name", g["version"] == 29 and "Mahine ka kaam" in g["users"]["shavez"]["extra"], g["version"])
except Exception as ex:  # noqa: BLE001
    check("the portal head executes for the tile check", False, repr(ex)[:200])

print(("WALK_S408 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S408 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
