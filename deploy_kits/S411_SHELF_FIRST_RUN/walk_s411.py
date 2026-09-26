#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s411.py -- kit S411_SHELF_FIRST_RUN. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over SCRATCH
COPIES of finance.db: (1) a fixture Drive of crafted statements in ICICI's real layouts (the iCRM PDF with EN-dash dates and Cr suffixes,
the pipe-delimited .txt, a password-locked PDF, look-alike holders, a narration that names the other bank) -- keyed W411 / tails 41xx;
(2) the REAL 21 files of the first run, re-identified in a second scratch copy exactly as the install will do it -- only counts and slot
names are printed, never an amount or an account. Never the live database.

  --app NEW --old OLD --db PATH
"""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []
W = os.path.dirname(os.path.abspath(a.db))
STUB = os.path.join(W, "stub411")
for d in (os.path.join(STUB, "bank", "2026"), os.path.join(STUB, "cards"), os.path.join(STUB, "decrypted")):
    os.makedirs(d, exist_ok=True)


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


def text_pdf(path, lines, locked=False):
    """A minimal text PDF (Courier, a wide page so long statement lines keep their columns; pdftotext -layout reads them back).
    locked=True writes a well-formed /Encrypt dictionary whose keys are nonsense: no password opens it -- exactly the bank's locked PDF."""
    pages = [lines[i:i + 60] for i in range(0, len(lines), 60)] or [[]]
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", None, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"]
    kids = []
    for pg in pages:
        content = b"BT /F1 9 Tf 11 TL 20 800 Td " + b" ".join(b"(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("cp1252", "replace") + b") Tj T*" for ln in pg) + b" ET"
        objs.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        c = len(objs)
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1400 842] /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % c)
        kids.append(len(objs))
    objs[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    enc = b""
    if locked:
        objs.append(b"<< /Filter /Standard /V 1 /R 2 /Length 40 /P -1 /O <" + b"41" * 32 + b"> /U <" + b"42" * 32 + b"> >>")
        enc = b" /Encrypt %d 0 R /ID [<%s> <%s>]" % (len(objs), b"43" * 16, b"43" * 16)
    out = bytearray(b"%PDF-1.4\n")
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R%s >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, enc, x)
    with open(path, "wb") as fh:
        fh.write(bytes(out))


def rs(p):
    return "{:,.2f}".format(p / 100.0)


def icrm(holder, kind, tail, month, rows, opening, extra_narration=None):
    """An iCRM statement in ICICI's own printed shape: (date, particulars, withdrawal, deposit) rows; balances computed; EN-dash dates."""
    y, m = int(month[:4]), int(month[5:7])
    last = (dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)).day
    bal = opening
    body = []
    for d, desc, wd, dep in rows:
        bal = bal - wd + dep
        body.append("%02d–%02d–%d   %-50s   %14s   %14s                                    %16s Cr" % (d, m, y, desc, rs(wd), rs(dep), rs(bal)))
    closing = bal
    L = ["                                                                                                          Page 1",
         "[iCRM_90029944 _10.129.54.208_XXXXXXXX%s ]" % tail, "Your Details With Us:", holder, "35-G/15-B RAMPUR GARDEN,.,", "BAREILLY", "UTTAR PRADESH - INDIA - 243001",
         "                                     Your Base Branch: ICICI Bank Ltd, 116, Civil Lines, Bareilly, Uttar Pradesh.",
         "                                     Summary of Account as on %02d-%02d-%d" % (last, m, y), "                                                I. Operative Account in INR",
         "      Type of Account                  Account Number                  Balance (INR )                 MICR                       IFSC                      Nomination",
         "           %-10s                    XXXXXXXX%s                    %16s Cr       243229002                ICIC0000192                  Not Registered" % (kind.capitalize(), tail, rs(closing)),
         "                                                          TOTAL                %s Cr" % rs(closing),
         "          Statement of transactions in Account number: XXXXXXXX%s in INR For the period 01-%02d-%d To %02d-%02d-%d" % (tail, m, y, last, m, y),
         "   Date                          Particulars                         Chq.No.   Withdrawals       Deposits        Autosweep          Reverse Sweep             Balance(INR )",
         " 01-%02d-%d B/F                                                                                                                                                    %s Cr" % (m, y, rs(opening))]
    L += body
    if extra_narration:
        L.append(extra_narration)
    L += ["                                Page Total:                                       0.00    0.00                0.00                      0.00      %s Cr" % rs(closing),
          "                                               Legends for transactions in your account statement", "Sincerely,", "Team ICICI Bank"]
    return L


def pipe_txt(path, tail, d0, d1, opening, rows):
    L = ["ICICI Bank account Statement from %s to %s. " % (d0.strftime("%d-%m-%Y"), d1.strftime("%d-%m-%Y")),
         "Account Number|Tran Date |  Tran Particular    | Inst Num      |   Dr Tran Amt   |    Cr Tran Amt |      Bal Amt      | Deposit Branch",
         "-------------- ---------    ---------------      ---------       ---------------   ---------------        --------    | ------- ------",
         "XXXXXXXX%s|   %s|  B/F                                                                                                 |                 |                |                |  %12.2f|    " % (tail, d0.strftime("%d-%b-%Y").upper(), opening / 100.0)]
    bal = opening
    for d, desc, wd, dep in rows:
        bal = bal - wd + dep
        L.append("XXXXXXXX%s|   %s|  %-100s|                 |  %14s|  %14s|  %12.2f|    " % (tail, d.strftime("%d-%b-%Y"), desc, ("%.2f" % (wd / 100.0)) if wd else "", ("%.2f" % (dep / 100.0)) if dep else "", bal / 100.0))
    with open(path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("\n".join(L) + "\n")


B = os.path.join(STUB, "bank", "2026")
AUG = [(3, "EBA/eATM 03AUG/XXXXXXXX1548", 0, 31593870), (3, "EBA/EQ Trade 03AUG/XXXXXXXX0931", 20280870, 0), (14, "UPI/Blinkit/paytm-blinkit@/Blinkit Pa/YES BANK L/2", 17200, 0),
       (22, "INF/INFT/XXXXXXXX3891/Self to savings/SANJEEVNI ME", 0, 15000000), (24, "CASH DEP BAREILLY", 0, 180000), (24, "INF/INFT/XXXXXXXX4431/Self transfer t/NK PATHOLOGY", 0, 18000000)]
text_pdf(os.path.join(B, "w411_huf_aug.pdf"), icrm("M/S.MANOJ KUMAR AGARWAL HUF", "savings", "4111", "2026-08", AUG, 7964970))
text_pdf(os.path.join(B, "w411_bhawna_aug.pdf"), icrm("DR.BHAWNA AGARWAL", "savings", "4112", "2026-08", AUG[:3] + [(17, "BIL/BPAY/0000001Y8JQP/BBPS/UPPCL-Post/190690", 1054200, 0)] + AUG[5:], 15685354))
text_pdf(os.path.join(B, "w411_manoj_aug.pdf"), icrm("DR.MANOJ KUMAR AGARWAL", "savings", "4113", "2026-08", AUG[:2], 2189854))
text_pdf(os.path.join(B, "w411_clinic_aug.pdf"), icrm("M/S.DR MANOJ AGARWAL CLINIC", "current", "4114", "2026-08", AUG[:2], 4609905))
text_pdf(os.path.join(B, "w411_nk_aug.pdf"), icrm("M/S.NK PATHOLOGY", "current", "4115", "2026-08", AUG[:2], 10545187))
text_pdf(os.path.join(B, "w411_sanj_aug.pdf"), icrm("M/S.SANJEEVNI MEDICOS", "current", "4116", "2026-08", AUG[:2] + [(12, "BIL/ONL/PVVNL ELECTRICITY BAREILLY", 250000, 0)], 7148742))
text_pdf(os.path.join(B, "w411_sanj_jul.pdf"), icrm("M/S.SANJEEVNI MEDICOS", "current", "4116", "2026-07", AUG[:2], 9445700))
text_pdf(os.path.join(B, "w411_lookalike_aug.pdf"), icrm("M/S.RAJESH AGARWAL", "savings", "4117", "2026-08", AUG[:2], 100000))
tam = icrm("M/S.NK PATHOLOGY", "current", "4115", "2026-07", AUG[:2], 4393637)
tam = [ln.replace(rs(4393637 + 31593870), rs(4393637 + 31593870 + 10)) if ln.startswith("03–") and "eATM" in ln else ln for ln in tam]
text_pdf(os.path.join(B, "w411_nk_jul_tampered.pdf"), tam)
text_pdf(os.path.join(B, "w411_locked_aug.pdf"), ["YES BANK LIMITED", "locked"], locked=True)
text_pdf(os.path.join(B, "w411_yes_sanj_aug.pdf"), ["YES BANK LIMITED", "Account Statement", "SANJEEVNI MEDICOS", "CURRENT ACCOUNT", "Account No: 000000004181", "Statement Period: 01/08/2026 to 31/08/2026",
                                                    "Transaction Date  Description  Deposits  Withdrawals  Balance", "05/08/2026 UPI/NK PATHOLOGY/transfer 1,000.00 5,000.00"])
pipe_txt(os.path.join(B, "w411_sanj_pipe.txt"), "4116", dt.date(2026, 8, 15), dt.date(2026, 9, 14), 9040000,
         [(dt.date(2026, 8, 15), "EZY/ICICIPOS_SET_10XXXXXX2505_150826", 0, 170000), (dt.date(2026, 9, 2), "INF/INFT/XXXXXXXX0561/Self transfer t/MKHUFICI", 6500000, 0), (dt.date(2026, 9, 10), "EZY/ICICIPOS_SET_10XXXXXX2505_100926", 0, 6000000)])

copydb(a.db, a.db + ".real")
sys.path.insert(0, a.app)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FINANCE_DIR"] = a.app
os.environ["FINANCE_DB"] = a.db
# the fixture scratch (and the old-code control made from it) starts with an EMPTY shelf and no learned tail; the real files stay in .real
db = sqlite3.connect(a.db)
db.execute("DELETE FROM stmt_file WHERE folder IN ('bank','cards','decrypted','all_txn')") if db.execute("SELECT 1 FROM sqlite_master WHERE name='stmt_file'").fetchone() else None
if db.execute("SELECT 1 FROM sqlite_master WHERE name='stmt_slot'").fetchone():
    db.execute("UPDATE stmt_slot SET ident_tail=NULL, owner_set=NULL")
for t in ("icici_statement_period", "icici_statement_line"):
    db.execute("DROP TABLE IF EXISTS %s" % t)
db.commit()
db.close()
copydb(a.db, a.db + ".old")
print("-- scratch copies made (.old = the box as it is, .real = the live shelf's 21 files); 12 crafted statements in the fixture Drive")

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
import packs, stmt_shelf, finance_icici
out = {"version": getattr(finance_icici, "VERSION", "?"), "slots": q("SELECT key, ident_words FROM stmt_slot ORDER BY sort")}
if NEW:
    import seed_s411
    seed_s411.seed(os.environ["FINANCE_DB"])
new, seen, errors = stmt_shelf.fetch(db)
out["fetch"] = [new, seen, errors]
out["process"] = packs.process_inbox(db)
F = {r["name"]: r for r in q("SELECT f.*, s.key AS slot_key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.folder='bank'")}
out["placed"] = {k: [v["slot_key"], v["ident_how"], v["bank"], v["kind"], v["tail"], v["period_from"], v["period_to"], v["read_status"], (v["note"] or "")[:70], v["holder"]] for k, v in F.items()}
out["tails"] = q("SELECT key, ident_tail, substr(owner_set,1,28) AS how FROM stmt_slot WHERE ident_tail IS NOT NULL ORDER BY key")
out["icici_tables"] = [has("icici_statement_period"), has("icici_statement_line"), (q("SELECT COUNT(*) AS n FROM icici_statement_line")[0]["n"] if has("icici_statement_line") else 0),
                       (q("SELECT account_ref, layout, closing_printed FROM icici_statement_period ORDER BY account_ref, period_from") if has("icici_statement_period") else [])]
out["bank_tables_untouched"] = [q("SELECT COUNT(*) AS n FROM bank_statement_period WHERE account_ref LIKE '41%'")[0]["n"] if has("bank_statement_period") else 0,
                                q("SELECT COUNT(*) AS n FROM bank_statement_line WHERE account_ref LIKE '41%'")[0]["n"] if has("bank_statement_line") else 0]
out["cells_aug"] = {x["slot"]: x["state"] for x in packs.cells(db, "2026-08") if x["kind"] != "card"}
out["cells_sep"] = {x["slot"]: x["state"] for x in packs.cells(db, "2026-09") if x["kind"] != "card"}
out["cells_jul"] = {x["slot"]: x["state"] for x in packs.cells(db, "2026-07") if x["kind"] != "card"}
out["unplaced"] = [[u["name"], u.get("holder"), u.get("locked"), (u["why"] or "")[:60]] for u in packs.unplaced(db) if u["folder"] == "bank"]
out["elec"] = packs.electricity_lines(db, "2026-08")
if not NEW:
    print("JSON:" + json.dumps(out, default=str)); raise SystemExit
# the owner: words edit (darpan cannot); assign the locked file -> 'locked original'; the look-alike stays with its holder text
lk = next((u for u in packs.unplaced(db) if u["name"] == "w411_locked_aug.pdf"), None)
sid = q("SELECT id FROM stmt_slot WHERE key='yes_cur_sanj'")[0]["id"]
out["assign_locked"] = P("manoj", "/finance/packs/api/assign", {"file": lk["id"] if lk else 0, "slot": sid})
out["locked_after"] = q("SELECT read_status, ident_how FROM stmt_file WHERE name='w411_locked_aug.pdf'")
out["words_darpan"] = P("darpan", "/finance/packs/api/slot-words", {"slot": sid, "words": "X"})[0]
sid2 = q("SELECT id FROM stmt_slot WHERE key='icici_personal'")[0]["id"]
db.execute("UPDATE stmt_slot SET ident_tail=NULL WHERE id=?", (sid2,)); db.commit()     # a slot with no learned tail yet takes the edited words
out["words_owner"] = P("manoj", "/finance/packs/api/slot-words", {"slot": sid2, "words": "RAJESH AGARWAL"})
out["lookalike_after"] = q("SELECT s.key AS slot_key, f.ident_how FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.name='w411_lookalike_aug.pdf'")
P("manoj", "/finance/packs/api/slot-words", {"slot": sid2, "words": "MANOJ KUMAR AGARWAL"})
st = G("manoj", "/finance/packs/api/state?month=2026-08")[1]
out["rows_aug"] = {r["key"]: [r["status"], r["why"][:60]] for r in st["rows"] if r["key"].startswith("stmt:icici") or r["key"] == "electricity"}
out["rows_sep"] = {r["key"]: [r["status"], r["why"][:70]] for r in G("manoj", "/finance/packs/api/state?month=2026-09")[1]["rows"] if r["key"] == "stmt:icici_sanj"}
out["amir_aug"] = packs.amir_pack(db, "2026-08")["ready"]
out["amir_sep"] = packs.amir_pack(db, "2026-09")["ready"]
out["page"] = "Holder (as the PDF prints it)" in G("manoj", "/finance/packs")[1]
# the tampered file is refused naming its row; a good file the same shape is read
out["tamper"] = out["placed"].get("w411_nk_jul_tampered.pdf", [None] * 9)[7]
print("JSON:" + json.dumps(out, default=str))
'''

PROBE_REAL = r'''
import json, os, sys, sqlite3
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
import packs, finance_icici, seed_s411
out = {}
files = q("SELECT id, name, folder, local_path FROM stmt_file WHERE folder='bank' ORDER BY id")
present = [f for f in files if f["local_path"] and os.path.exists(f["local_path"])]
out["files"] = [len(files), len(present)]
# (a) the reader over every real bank file, read-only: counts and the proof, never an amount
res = {"read": 0, "locked": 0, "refused": [], "lines": [], "layouts": {}, "closing_printed": 0}
for f in present:
    try:
        with open(f["local_path"], "rb") as fh:
            blob = fh.read()
        p = finance_icici.parse_statement(blob)
        res["read"] += 1; res["lines"].append(len(p["lines"])); res["layouts"][p["layout"]] = res["layouts"].get(p["layout"], 0) + 1
        res["closing_printed"] += 1 if p["closing_printed"] else 0
    except finance_icici.StatementRejected as e:
        if "password" in str(e):
            res["locked"] += 1
        else:
            res["refused"].append(str(e)[:80])
out["reader"] = res
# (b) the seed exactly as the install runs it: the shelf re-identified, the grid
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    seed_s411.seed(os.environ["FINANCE_DB"])
out["seed_print"] = buf.getvalue()[-1200:]
rows = q("SELECT f.id, f.folder, f.ident_how, f.read_status, f.note, f.holder, f.bank, f.kind, s.key AS slot_key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.folder='bank' ORDER BY f.id")
out["by_slot"] = {}
for r in rows:
    out["by_slot"].setdefault(r["slot_key"] or "(unplaced)", []).append([r["ident_how"], r["read_status"] or (r["note"] or "")[:30]])
out["refused_n"] = sum(1 for r in rows if (r["read_status"] or "").startswith("refused"))
out["read_n"] = sum(1 for r in rows if r["read_status"] == "read")
out["bytail_n"] = sum(1 for r in rows if r["ident_how"] == "by tail")
out["bywords_n"] = sum(1 for r in rows if r["ident_how"] == "by words")
out["locked_n"] = sum(1 for r in rows if (r["note"] or "").startswith("password-protected"))
out["misbank"] = [r["id"] for r in rows if r["holder"] and r["bank"] and r["slot_key"] and not r["slot_key"].startswith(r["bank"].lower()[:3])]
out["grid"] = {m: {x["slot"]: x["state"] for x in packs.cells(db, m) if x["kind"] != "card"} for m in ("2026-07", "2026-08", "2026-09")}
out["tails_learned"] = q("SELECT COUNT(*) AS n FROM stmt_slot WHERE ident_tail IS NOT NULL AND ident_tail<>''")[0]["n"]
out["icici_lines"] = q("SELECT COUNT(*) AS n FROM icici_statement_line")[0]["n"]
out["bank_periods"] = q("SELECT COUNT(*) AS n FROM bank_statement_period")[0]["n"]
out["elec_aug"] = [len(packs.electricity_lines(db, "2026-08")[0] or []), (packs.electricity_lines(db, "2026-08")[1] or "")[:60]]
out["unplaced"] = [[u.get("locked"), (u.get("holder") or "")[:30], (u["why"] or "")[:40]] for u in packs.unplaced(db) if u["folder"] == "bank"]
out["unplaced_open"] = sum(1 for u in packs.unplaced(db) if u["folder"] == "bank" and not u.get("locked"))
out["amir_aug"] = packs.amir_pack(db, "2026-08")["ready"]
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath, script):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_DIR=appdir, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1",
               STMT_DRIVE_STUB=STUB, STMT_INBOX=os.path.join(W, "inbox411_" + mode), PACKS_TODAY="2026-09-26")
    p = subprocess.run([sys.executable, "-B", "-c", script], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, "old", a.db + ".old", PROBE)
N = probe(a.app, "new", a.db, PROBE)
R = probe(a.app, "real", a.db + ".real", PROBE_REAL)

print("-- 1  the identifier on ICICI's real layout (crafted files): the header decides, holders match as word sets, the longest wins")
pl = N["placed"]
S = lambda name: pl.get(name, [None] * 10)  # noqa: E731
check("the HUF statement (a Yes Bank narration and 'SANJEEVNI' inside it) lands on the ICICI HUF slot by words, bank ICICI, savings, tail 4111, Aug",
      S("w411_huf_aug.pdf")[:7] == ["icici_huf", "by words", "ICICI", "savings", "4111", "2026-08-01", "2026-08-31"], S("w411_huf_aug.pdf"))
check("Dr Bhawna's ('NK PATHOLOGY' inside a transfer narration) -> ICICI Bhawna; Dr Manoj Kumar Agarwal -> ICICI personal (not the HUF, not the clinic); the clinic -> ICICI clinic; NK Pathology -> ICICI NK; Sanjeevni -> ICICI Sanjeevni",
      S("w411_bhawna_aug.pdf")[0] == "icici_bhawna" and S("w411_manoj_aug.pdf")[0] == "icici_personal" and S("w411_clinic_aug.pdf")[0] == "icici_clinic" and S("w411_nk_aug.pdf")[0] == "icici_nk" and S("w411_sanj_aug.pdf")[0] == "icici_sanj",
      {k: v[0] for k, v in pl.items()})
check("a look-alike holder (RAJESH AGARWAL) is UNPLACED and carries the holder text the PDF prints; a Yes Bank head (no 'Your Details' block) still places by its own words on the Yes Bank slot",
      S("w411_lookalike_aug.pdf")[0] is None and S("w411_lookalike_aug.pdf")[9] == "M/S.RAJESH AGARWAL" and "no slot's words" in S("w411_lookalike_aug.pdf")[8] and S("w411_yes_sanj_aug.pdf")[0] == "yes_cur_sanj" and S("w411_yes_sanj_aug.pdf")[2] == "YES",
      (S("w411_lookalike_aug.pdf"), S("w411_yes_sanj_aug.pdf")[:3]))
check("each by-words placement of a bank statement LEARNS the account tail (6 ICICI slots + the Yes Bank one); the pipe .txt (account number only) then lands BY TAIL on ICICI Sanjeevni",
      len(N["tails"]) == 7 and all(t["how"].startswith("learned from the statement") for t in N["tails"]) and S("w411_sanj_pipe.txt")[:2] == ["icici_sanj", "by tail"], (N["tails"], S("w411_sanj_pipe.txt")[:3]))

print("-- 2  the reader on ICICI's real layouts: the proof kept, the tampered file refused, the lines in ICICI's own tables")
rd = {k: v[7] for k, v in pl.items()}
check("the six iCRM statements and the July one read (B/F + rows = every running balance = the printed closing); the pipe .txt read (its own proof); the tampered NK July file REFUSED naming the row",
      all(rd.get(k) == "read" for k in ("w411_huf_aug.pdf", "w411_bhawna_aug.pdf", "w411_manoj_aug.pdf", "w411_clinic_aug.pdf", "w411_nk_aug.pdf", "w411_sanj_aug.pdf", "w411_sanj_jul.pdf", "w411_sanj_pipe.txt"))
      and str(N["tamper"]).startswith("refused: row 03-07-2026") and "does not carry the balance" in str(N["tamper"]), (rd, N["tamper"]))
check("the lines went to icici_statement_period / icici_statement_line (v1.1; layouts icrm + pipe, the pipe marked 'closing not printed'); NOTHING of them in the Yes Bank tables the Bank card reads",
      N["icici_tables"][0] and N["icici_tables"][1] and N["icici_tables"][2] >= 20 and {x["layout"] for x in N["icici_tables"][3]} == {"icrm", "pipe"} and any(x["layout"] == "pipe" and not x["closing_printed"] for x in N["icici_tables"][3])
      and N["bank_tables_untouched"] == [0, 0] and N["version"] == "1.1", (N["icici_tables"][:3], N["bank_tables_untouched"], N["version"]))
check("a password-locked PDF is named as such (unplaced, 'password-protected'); the owner's tap files it as a locked original; darpan cannot edit a slot's words, the owner can, and the look-alike then lands on the edited slot (and is released again)",
      any(u[0] == "w411_locked_aug.pdf" and u[2] is True for u in N["unplaced"]) and N["assign_locked"][0] == 200 and N["locked_after"] == [{"read_status": "locked original", "ident_how": "the owner's tap"}]
      and N["words_darpan"] in (302, 403) and N["words_owner"][0] == 200 and N["lookalike_after"] == [{"slot_key": "icici_personal", "ident_how": "by words"}], (N["unplaced"], N["assign_locked"], N["locked_after"], N["words_darpan"], N["words_owner"], N["lookalike_after"]))

print("-- 3  the month grid and the pack rows: read / matched, a partial statement is never the month's")
ca, cs, cj = N["cells_aug"], N["cells_sep"], N["cells_jul"]
check("August: the six ICICI cells read (Sanjeevni 'matched'), the Yes Bank ones empty; July: Sanjeevni read, NK empty (its file was the tampered one, refused -> 'arrived'); September: Sanjeevni PARTIAL (the .txt covers 15-Aug..14-Sep only)",
      ca["icici_huf"] == "read" and ca["icici_bhawna"] == "read" and ca["icici_personal"] == "read" and ca["icici_clinic"] == "read" and ca["icici_nk"] == "read" and ca["icici_sanj"] == "matched" and ca["yes_cur_nk"] == "empty"
      and cj["icici_sanj"] == "matched" and cj["icici_nk"] == "arrived" and cs["icici_sanj"] == "partial" and cs["icici_huf"] == "empty", (ca, cj, cs))
check("the pack rows: August ICICI statements ready; the electricity row reads the two ICICI lines (PVVNL from Sanjeevni, UPPCL from Dr Bhawna); September's Sanjeevni row is MISSING with 'only 15-Aug → 14-Sep on the shelf'; Amir's pack ready for August (both Sanjeevni files there), NOT for September (partial)",
      all(v[0] == "ready" for k, v in N["rows_aug"].items() if k.startswith("stmt:icici")) and N["rows_aug"]["electricity"][0] == "ready" and len(N["elec"][0]) == 2
      and N["rows_sep"]["stmt:icici_sanj"][0] == "missing" and "only 15-Aug-2026 → 14-Sep-2026" in N["rows_sep"]["stmt:icici_sanj"][1] and N["amir_aug"] is True and N["amir_sep"] is False and N["page"],
      (N["rows_aug"], N["elec"], N["rows_sep"], N["amir_aug"], N["amir_sep"], N["page"]))

print("-- 4  THE REAL 21 FILES of the first run, re-identified in a scratch copy exactly as the install does (counts and slots only)")
rr = R["reader"]
check("the reader over the real files: every iCRM PDF and every pipe .txt reads with its proof, the password-locked ones say so, nothing refused (present %d of %d; read %d, locked %d, layouts %s, lines per file min %s)"
      % (R["files"][1], R["files"][0], rr["read"], rr["locked"], rr["layouts"], min(rr["lines"]) if rr["lines"] else None),
      R["files"][1] == 0 or (rr["refused"] == [] and rr["read"] >= 12 and rr["locked"] >= 1 and rr["layouts"].get("icrm", 0) >= 12 and (min(rr["lines"]) if rr["lines"] else 0) >= 8 and rr["closing_printed"] == rr["layouts"].get("icrm", 0)), rr)
check("the shelf after the seed: every readable real file placed (the first statement of each account by words, the rest by the learned tail -- the .txt too, in a second pass), READ, on ICICI slots only, none refused, none left over; the locked ones unplaced and named; the six ICICI cells of July and August read / matched; tails learned",
      R["files"][1] == 0 or (R["refused_n"] == 0 and R["read_n"] == R["reader"]["read"] and R["bywords_n"] >= 6 and R["bytail_n"] >= 6 and R["unplaced_open"] == 0 and R["misbank"] == [] and R["locked_n"] == R["reader"]["locked"]
                             and all(R["grid"]["2026-08"][k] in ("read", "matched") for k in ("icici_huf", "icici_bhawna", "icici_personal", "icici_clinic", "icici_nk", "icici_sanj"))
                             and all(R["grid"]["2026-07"][k] in ("read", "matched") for k in ("icici_huf", "icici_bhawna", "icici_personal", "icici_clinic", "icici_nk", "icici_sanj")) and R["tails_learned"] >= 6),
      (R["refused_n"], R["read_n"], R["bywords_n"], R["bytail_n"], R["unplaced_open"], R["misbank"], R["locked_n"], R["grid"], R["tails_learned"]))
check("the Yes Bank tables gained nothing (%d period rows, as before); the ICICI table holds the lines; Amir's August pack is not ready (the Yes Bank Sanjeevni statement is locked); the grid for the report is printed below" % R["bank_periods"],
      R["files"][1] == 0 or (R["icici_lines"] >= 100 and R["amir_aug"] is False and R["bank_periods"] <= 2), (R["icici_lines"], R["amir_aug"], R["bank_periods"]))
for m in ("2026-07", "2026-08", "2026-09"):
    print("     grid %s: %s" % (m, " · ".join("%s=%s" % (k, v) for k, v in R["grid"][m].items())))
print("     unplaced after the seed: %s" % R["unplaced"])
print("     electricity August (count only): %s" % R["elec_aug"][0])

print("-- 5  NEGATIVE CONTROLS on the box as it is (the S408 identifier and reader, the same crafted files)")
op = O["placed"]
check("NEGATIVE: the S408 identifier flips the HUF statement to bank YES (the narration) and puts it and Dr Bhawna's on YES BANK slots (the wrong bank); the S408 reader refuses every iCRM file it gets ('no opening balance printed'); the .txt is 'not a readable PDF'; no learned tail",
      op["w411_huf_aug.pdf"][2] == "YES" and str(op["w411_huf_aug.pdf"][0]).startswith("yes_") and str(op["w411_bhawna_aug.pdf"][0]).startswith("yes_") and any("no opening balance" in str(v[7]) for v in op.values())
      and op["w411_sanj_pipe.txt"][8].startswith("not a readable PDF") and O["tails"] == [] and O["version"] == "1.0", ({k: (v[0], v[2], str(v[7])[:30], v[8][:25]) for k, v in op.items()}, O["tails"], O["version"]))

print(("WALK_S411 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S411 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
