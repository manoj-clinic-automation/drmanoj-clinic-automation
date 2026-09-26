#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s412.py -- kit S412_YESBANK_UNLOCK. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over SCRATCH
COPIES of finance.db: (1) a fixture Drive with Yes Bank statements in S360's proven PDF layout -- three of them password-locked with
pypdf (AES-256-R5 and RC4-128, the two ciphers the five real files use), a branch copy (not locked) of one of them, a non-Sanjeevni
plain one -- plus ICICI's iCRM PDFs and a pipe .txt with a DEGENERATE header period; the passwords are random, made here, never
printed, and the walk asserts they appear in no page, no answer, no log line, no shelf row; (2) the seed's two anchor routes on copies;
(3) THE REAL shelf (the live 21 files) in a further copy, seeded exactly as the install does it -- counts, dates and states only, never
an amount. Never the live database. Negative control: the box as it is (S411's files) on the same fixtures.

  --app NEW --old OLD --db PATH [--anchor-backup PATH]
"""
import argparse
import datetime as dt
import io
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import zlib

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--db"):
    ap.add_argument(k, required=True)
ap.add_argument("--anchor-backup", default="")
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []
W = os.path.dirname(os.path.abspath(a.db))
KIT = os.path.dirname(os.path.abspath(__file__))
STUB = os.path.join(W, "stub412")
for d in (os.path.join(STUB, "bank", "2026"), os.path.join(STUB, "cards"), os.path.join(STUB, "decrypted")):
    os.makedirs(d, exist_ok=True)
P1, P2, P3 = ("w412-" + secrets.token_hex(5), "w412-" + secrets.token_hex(5), "w412-" + secrets.token_hex(5))   # never printed


def check(label, cond, got=None):
    global n
    n += 1
    s = ("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:700] + "]") if got is not None else "")
    for p in (P1, P2, P3):
        s = s.replace(p, "<secret>")
    print(s)
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


# ---------------------------------------------------------------- fixtures: Yes Bank in S360's proven layout (fixtures_s360.py), locked with pypdf
HDR = (" Transaction\n"
       "                  Value Date             Cheque No/Reference No                "
       "                    Description                            Withdrawals              Deposits           Running Balance\n"
       "    Date\n\n")
_hl = HDR.splitlines()[1]
COLS = {"wd": _hl.find("Withdrawals") + len("Withdrawals"), "dep": _hl.find("Deposits") + len("Deposits"), "bal": _hl.find("Running Balance") + len("Running Balance")}


def inr(p):
    return "{:,.2f}".format(p / 100.0)


def yrow(d, ref, desc, wd, dep, bal):
    s = " %s      %s       %s            %s" % (d, d, ref, desc)
    for key, v in (("wd", wd), ("dep", dep), ("bal", bal)):
        if v:
            s = s.ljust(COLS[key] - len(v)) + v
    return s + "\n"


def yes_statement(holder, kind, acct, pfrom, pto, opening, rows):
    """rows: (d Mon yyyy, ref, desc, withdrawal_p, deposit_p) in date order; balances, totals and the closing computed -> the proof holds."""
    bal, body, tw, td = opening, [], 0, 0
    for d, ref, desc, wd, dep in rows:
        bal = bal - wd + dep
        tw += wd
        td += dep
        body.append(yrow(d, ref, desc, inr(wd) if wd else "", inr(dep) if dep else "", inr(bal)))
    top = ("YES BANK LIMITED\n   Statement of account: %s\n   Period: %s - %s\n\n %s\n\n"
           "        Transaction details for your account number %s (%s)\n\n" % (acct, pfrom, pto, holder, acct, kind.upper()))
    foot = ("\n\n\nOpening Balance: %s        Total Withdrawals: %s        Total Deposits: %s        Closing Balance: %s\n\nsome footer text that is not a row\n"
            % (inr(opening), inr(tw), inr(td), inr(bal)))
    return top + HDR + "".join(body) + foot


def make_pdf(text):
    lines = text.splitlines()
    ops = ["BT", "/F1 5 Tf", "6 TL", "10 %d Td" % (20 + 6 * len(lines))]
    for ln in lines:
        esc = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ops.append("(%s) Tj T*" % esc)
    ops.append("ET")
    stream = zlib.compress("\n".join(ops).encode("latin-1"))
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 %d] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>" % (40 + 6 * len(lines)),
            b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"]
    out, offs = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    return bytes(out)


def write_pdf(path, text, password=None, algorithm=None):
    blob = make_pdf(text)
    if password:
        from pypdf import PdfReader, PdfWriter              # noqa: PLC0415  (the venv python runs this walk)
        wr = PdfWriter(clone_from=PdfReader(io.BytesIO(blob)))
        wr.encrypt(user_password=password, owner_password=None, algorithm=algorithm)
        with open(path, "wb") as fh:
            wr.write(fh)
        return
    with open(path, "wb") as fh:
        fh.write(blob)


# ---------------------------------------------------------------- fixtures: ICICI (walk_s411's shapes)
def text_pdf(path, lines):
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


def rs(p):
    return "{:,.2f}".format(p / 100.0)


def icrm(holder, kind, tail, month, rows, opening):
    y, m = int(month[:4]), int(month[5:7])
    last = (dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)).day
    bal, body = opening, []
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
    L += ["                                Page Total:                                       0.00    0.00                0.00                      0.00      %s Cr" % rs(closing),
          "                                               Legends for transactions in your account statement", "Sincerely,", "Team ICICI Bank"]
    return L, closing


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
AUG = [(3, "EBA/eATM 03AUG/XXXXXXXX1548", 0, 31593870), (3, "EBA/EQ Trade 03AUG/XXXXXXXX0931", 20280870, 0), (12, "BIL/ONL/PVVNL ELECTRICITY BAREILLY", 250000, 0)]
L_aug, ICRM_AUG_CLOSING = icrm("M/S.SANJEEVNI MEDICOS", "current", "4116", "2026-08", AUG, 7148742)
text_pdf(os.path.join(B, "w412_icici_sanj_aug.pdf"), L_aug)
L_jul, _ = icrm("M/S.SANJEEVNI MEDICOS", "current", "4116", "2026-07", AUG[:2], 9445700)
text_pdf(os.path.join(B, "w412_icici_sanj_jul.pdf"), L_jul)
pipe_txt(os.path.join(B, "w412_icici_sanj_pipe_deg.txt"), "4116", dt.date(2026, 9, 10), dt.date(2026, 9, 10), ICRM_AUG_CLOSING,
         [(dt.date(2026, 9, 1), "EZY/ICICIPOS_SET_10XXXXXX2505_010926", 0, 170000), (dt.date(2026, 9, 4), "INF/INFT/XXXXXXXX0561/Self transfer t/MKHUFICI", 6500000, 0),
          (dt.date(2026, 9, 10), "EZY/ICICIPOS_SET_10XXXXXX2505_100926", 0, 6000000)])
# odd amounts, no cash-deposit narration: nothing here can coincide with a live Sanjeevni movement the Bank card matches against
YR = [("02 Aug 2026", "REF0000000C", "NEFT-IN/SOMEONE/SOMETHING", 0, 1000037), ("10 Aug 2026", "REF0000000B", "NET TXN/SOMETHING/TAX", 1200011, 0), ("28 Aug 2026", "REF0000000A", "UPI/PAYMENT/SOMEONE", 0, 350009)]
YS = [("03 Sep 2026", "REF0000001C", "NEFT-IN/SOMEONE/SOMETHING", 0, 2000023), ("15 Sep 2026", "REF0000001B", "NET TXN/SOMETHING/TAX", 700017, 0)]
write_pdf(os.path.join(B, "w412_yes_nk_aug_locked.pdf"), yes_statement("NK PATHOLOGY", "current", "555004121", "01 Aug 2026", "31 Aug 2026", 5000000, YR), P1, "AES-256-R5")
SANJ = yes_statement("SANJEEVNI MEDICOS", "current", "555004122", "01 Aug 2026", "31 Aug 2026", 8000000, YR)
write_pdf(os.path.join(B, "w412_yes_sanj_aug_branch.pdf"), SANJ)
write_pdf(os.path.join(B, "w412_yes_sanj_aug_locked.pdf"), SANJ, P2, "RC4-128")
# the clinic's (non-Sanjeevni, plain) statement is dropped into the Drive by the probe AFTER the first run, alone -- so the Bank card can be
# compared around exactly that one ingest (the first run also moves the ICICI anchor, which the card reads)
write_pdf(os.path.join(W, "w412_clinic_src.pdf"), yes_statement("DR MANOJ AGARWAL CLINIC", "current", "555004123", "01 Sep 2026", "30 Sep 2026", 3000000, YS))
write_pdf(os.path.join(B, "w412_yes_bhawna_aug_locked.pdf"), yes_statement("DR BHAWNA AGARWAL", "savings", "555004124", "01 Aug 2026", "31 Aug 2026", 2500000, YR), P3, "AES-256-R5")

# sanity on the fixtures: pdftotext refuses the locked ones exactly as it refuses the bank's; pypdf sees them encrypted
from pypdf import PdfReader  # noqa: E402
enc = {}
for nm in ("w412_yes_nk_aug_locked.pdf", "w412_yes_sanj_aug_locked.pdf", "w412_yes_bhawna_aug_locked.pdf", "w412_yes_sanj_aug_branch.pdf"):
    r = subprocess.run(["pdftotext", "-layout", os.path.join(B, nm), "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    enc[nm] = [r.returncode, "Incorrect password" in r.stderr.decode("utf-8", "replace"), PdfReader(os.path.join(B, nm)).is_encrypted, len(r.stdout)]

copydb(a.db, a.db + ".real")
sys.path.insert(0, a.app)
sys.path.insert(0, KIT)
os.environ["FINANCE_DIR"] = a.app
os.environ["FINANCE_DB"] = a.db
# the fixture scratch (and the old-code control made from it) starts with an EMPTY shelf, no learned tail, no secret, an anchor at 31-Jul
db = sqlite3.connect(a.db)
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())   # noqa: E731
if has("stmt_file"):
    db.execute("DELETE FROM stmt_file WHERE folder IN ('bank','cards','decrypted','all_txn')")
if has("stmt_slot"):
    db.execute("UPDATE stmt_slot SET ident_tail=NULL, owner_set=NULL")
for t in ("icici_statement_period", "icici_statement_line", "yesbank_account_statement_period", "yesbank_account_statement_line", "stmt_secret", "stmt_secret_log"):
    db.execute("DROP TABLE IF EXISTS %s" % t)
if has("bank_anchor"):
    db.execute("UPDATE bank_anchor SET as_on='2026-07-31', source='walk S412 start', entered_by='walk', entered_at='2026-09-26T00:00:00' WHERE unit='medical' AND account='icici'")
SHARED0 = db.execute("SELECT COUNT(*) FROM bank_statement_period").fetchone()[0] if has("bank_statement_period") else 0
db.commit()
db.close()
copydb(a.db, a.db + ".old")
print("-- scratch copies made (.old = the box as it is, .real = the live shelf's files); 8 crafted statements in the fixture Drive (3 locked); the passwords are random and never printed")

PROBE = r'''
import json, os, sys, sqlite3, subprocess
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
P1, P2, P3 = os.environ["W412_P1"], os.environ["W412_P2"], os.environ["W412_P3"]
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
import packs, stmt_shelf, finance_icici, finance_yesbank, sanjeevni_approvals as sa
out = {"versions": [getattr(finance_icici, "VERSION", "?"), getattr(finance_yesbank, "VERSION", "?")]}
def card():
    try:
        return json.dumps([sa.yesbank_position(db), sa.bank_view(db, "2026-09")], sort_keys=True, default=str)
    except Exception as e:
        return "ERR " + str(e)[:80]
def F():
    return {r["name"]: [r["slot_key"], r["ident_how"], r["bank"], r["kind"], r["tail"], r["period_from"], r["period_to"], r["read_status"], (r["note"] or "")[:130], r["holder"],
                        r.get("locked"), bool(r.get("unlocked_path")), r["matched_status"]]
            for r in q("SELECT f.*, s.key AS slot_key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.folder='bank'")}
def shared():
    return {"periods": q("SELECT account_ref, period_from, period_to FROM bank_statement_period ORDER BY account_ref, period_from"),
            "n_lines": q("SELECT COUNT(*) AS n FROM bank_statement_line")[0]["n"],
            "by_tail": {t: q("SELECT COUNT(*) AS n FROM bank_statement_period WHERE account_ref=?", t)[0]["n"] for t in ("4121", "4122", "4123", "4124")}}
def needs():
    return [l["text"] for l in (G("manoj", "/finance/sanjeevni/api/needs-you")[1] or {}).get("lines", []) if "password" in l["text"]]
def anchor():
    r = q("SELECT as_on, balance_p, source, entered_by FROM bank_anchor WHERE unit='medical' AND account='icici'")
    return r[0] if r else None
CLINIC = os.path.join(os.environ["STMT_DRIVE_STUB"], "bank", "2026", "w412_yes_clinic_sep_branch.pdf")
if os.path.exists(CLINIC):
    os.remove(CLINIC)
out["card0"] = card()
new, seen, errors = stmt_shelf.fetch(db)
out["fetch"] = [new, seen, errors]
out["process1"] = packs.process_inbox(db)
out["card1"] = card()
# the clinic's statement alone: the ONE ingest the Bank card is compared around
with open(os.path.join(os.environ["WALKDIR"], "w412_clinic_src.pdf"), "rb") as fh:
    open(CLINIC, "wb").write(fh.read())
stmt_shelf.fetch(db)
out["process1b"] = packs.process_inbox(db)
out["placed1"] = F()
out["shared1"] = shared()
out["card1b"] = card()
out["anchor1"] = anchor()
out["pipe1"] = q("SELECT account_ref, period_from, period_to, closing_printed FROM icici_statement_period WHERE layout='pipe'") if has("icici_statement_period") else []
out["needs1"] = needs()
page = G("manoj", "/finance/packs")[1]
out["page_card"] = "Statement passwords" in page
st1 = G("manoj", "/finance/packs/api/state?month=2026-08")
out["state1_secrets"] = (st1[1] or {}).get("secrets") if isinstance(st1[1], dict) else None
out["secret_darpan"] = P("darpan", "/finance/packs/api/secret", {"bank": "YES", "text": "x"})[0]
out["secret_bad"] = P("manoj", "/finance/packs/api/secret", {"bank": "YES", "text": "  \n "})[0]
s1 = P("manoj", "/finance/packs/api/secret", {"bank": "YES", "text": "not-the-one\n" + P1 + "\n" + P2 + "\n"})
out["secret_set"] = [s1[0], {k: v for k, v in (s1[1] or {}).items() if k in ("ok", "action", "candidates", "bank")}, ((s1[1] or {}).get("result") or {}).get("unlocked")]
leak_pool = [page, json.dumps(st1[1], default=str), json.dumps(s1[1], default=str)]
out["placed2"] = F()
out["shared2"] = shared()
out["card2"] = card()
out["yes_acct"] = ([q("SELECT account_ref, slot_key, period_from, period_to FROM yesbank_account_statement_period ORDER BY account_ref"),
                    q("SELECT account_ref, slot_key, COUNT(*) AS n FROM yesbank_account_statement_line GROUP BY account_ref, slot_key ORDER BY account_ref")]
                   if has("yesbank_account_statement_period") else None)
out["log"] = [r["bank"] + ":" + r["action"] for r in q("SELECT bank, action FROM stmt_secret_log ORDER BY id")] if has("stmt_secret_log") else None
unl = q("SELECT id, name, unlocked_path FROM stmt_file WHERE name='w412_yes_nk_aug_locked.pdf'") if NEW else []
out["unlocked_reads"] = None
if unl and unl[0]["unlocked_path"] and os.path.exists(unl[0]["unlocked_path"]):
    r = subprocess.run(["pdftotext", "-layout", unl[0]["unlocked_path"], "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out["unlocked_reads"] = [r.returncode, "NK PATHOLOGY" in r.stdout.decode("utf-8", "replace"), os.path.basename(unl[0]["unlocked_path"])]
out["cells_aug"] = {x["slot"]: [x["state"], (x["file"] or {}).get("name"), (x["file"] or {}).get("locked")] for x in packs.cells(db, "2026-08") if x["bank"] in ("YES",) or x["slot"] == "icici_sanj"}
out["cells_sep"] = {x["slot"]: [x["state"], (x["file"] or {}).get("period_from"), (x["file"] or {}).get("period_to")] for x in packs.cells(db, "2026-09") if x["slot"] in ("yes_cur_clinic", "icici_sanj")}
out["amir"] = [packs.amir_pack(db, "2026-07")["ready"], packs.amir_pack(db, "2026-08")["ready"]]
out["needs2"] = needs()
out["anchor2"] = anchor()
s2 = P("manoj", "/finance/packs/api/secret", {"bank": "YES", "text": P3})
out["secret_replace"] = [s2[0], {k: v for k, v in (s2[1] or {}).items() if k in ("ok", "action", "candidates")}, ((s2[1] or {}).get("result") or {}).get("unlocked")]
leak_pool.append(json.dumps(s2[1], default=str))
out["placed3"] = F()
st2 = G("manoj", "/finance/packs/api/state?month=2026-08")
out["state2_secrets"] = (st2[1] or {}).get("secrets") if isinstance(st2[1], dict) else None
out["log2"] = [r["bank"] + ":" + r["action"] for r in q("SELECT bank, action FROM stmt_secret_log ORDER BY id")] if has("stmt_secret_log") else None
out["yes_acct2"] = q("SELECT account_ref, slot_key FROM yesbank_account_statement_period ORDER BY account_ref") if has("yesbank_account_statement_period") else None
out["card3"] = card()
out["shared3"] = shared()
ur = None
if NEW:
    r = subprocess.run([os.environ["STMT_VENV_PYTHON"], "-B", os.path.join(APP, "stmt_shelf.py"), "unlock"], cwd=APP, env=dict(os.environ), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ur = r.stdout.decode("utf-8", "replace") + " | " + r.stderr.decode("utf-8", "replace")[-300:]
    leak_pool.append(ur)
    out["unlock_cmd"] = (r.stdout.decode("utf-8", "replace").strip()[-90:])
leak_pool.append(json.dumps(q("SELECT * FROM stmt_file"), default=str))
if has("stmt_secret_log"):
    leak_pool.append(json.dumps(q("SELECT * FROM stmt_secret_log"), default=str))
leak_pool.append(G("manoj", "/finance/packs")[1])
leak_pool.append(json.dumps(st2[1], default=str))
out["leak"] = [any(p in blob for p in (P1, P2, P3)) for blob in leak_pool]
out["in_secret_table"] = (P3 in json.dumps(q("SELECT secret FROM stmt_secret"))) if has("stmt_secret") else None
out["stmt_secret_cols_in_state"] = ("secret" in json.dumps(st2[1], default=str).replace("secrets", "").replace("stmt_secret", ""))
print("JSON:" + json.dumps(out, default=str))
'''

PROBE_SEED = r'''
import json, os, sys, sqlite3, io, contextlib
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
import packs, seed_s412
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
# the state S411's first run left: the anchor on the text statement's degenerate day, a degenerate pipe period row beside the widened one
db.execute("UPDATE bank_anchor SET as_on='2026-09-10', balance_p=1, source=\"ICICI Sanjeevni statement 2026-09-10..2026-09-10, the bank's own closing balance (S408 shelf)\", entered_by='shelf' WHERE unit='medical' AND account='icici'")
db.execute("INSERT OR IGNORE INTO icici_statement_period (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at, layout, closing_printed) VALUES ('4116','2026-09-10','2026-09-10',0,0,'x','x','x','pipe',0)")
db.commit()
out = {"deg_before": q("SELECT COUNT(*) AS n FROM icici_statement_period WHERE layout='pipe' AND period_from=period_to")[0]["n"]}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    seed_s412.seed(os.environ["FINANCE_DB"])
out["print"] = buf.getvalue()[-1500:]
out["anchor"] = q("SELECT as_on, balance_p, source, entered_by FROM bank_anchor WHERE unit='medical' AND account='icici'")[0]
out["deg_after"] = q("SELECT COUNT(*) AS n FROM icici_statement_period WHERE layout='pipe' AND period_from=period_to")[0]["n"]
out["pipe"] = q("SELECT account_ref, period_from, period_to FROM icici_statement_period WHERE layout='pipe' ORDER BY period_from")
out["txt_row"] = q("SELECT period_from, period_to, read_status FROM stmt_file WHERE name='w412_icici_sanj_pipe_deg.txt'")
out["icrm_aug_closing"] = q("SELECT closing_p FROM icici_statement_period WHERE account_ref='4116' AND period_to='2026-08-31' AND layout='icrm'")[0]["closing_p"]
print("JSON:" + json.dumps(out, default=str))
'''

PROBE_REAL = r'''
import json, os, sys, sqlite3, io, contextlib
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
c = fa.app.test_client()
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
has = lambda t: bool(db.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone())
import packs, seed_s412
out = {}
def snap():
    return dict(read=q("SELECT COUNT(*) AS n FROM stmt_file WHERE folder='bank' AND read_status='read'")[0]["n"],
                locked_note=q("SELECT COUNT(*) AS n FROM stmt_file WHERE folder='bank' AND note LIKE 'password-protected%'")[0]["n"],
                icici_lines=(q("SELECT COUNT(*) AS n FROM icici_statement_line")[0]["n"] if has("icici_statement_line") else 0),
                bank_periods=(q("SELECT COUNT(*) AS n FROM bank_statement_period")[0]["n"] if has("bank_statement_period") else 0),
                bank_lines=(q("SELECT COUNT(*) AS n FROM bank_statement_line")[0]["n"] if has("bank_statement_line") else 0),
                pipe=[(r["account_ref"], r["period_from"], r["period_to"]) for r in q("SELECT account_ref, period_from, period_to FROM icici_statement_period WHERE layout='pipe' ORDER BY account_ref, period_from")] if has("icici_statement_period") else [],
                anchor=(q("SELECT as_on, source, entered_by FROM bank_anchor WHERE unit='medical' AND account='icici'") or [None])[0],
                files=q("SELECT COUNT(*) AS n FROM stmt_file WHERE folder='bank'")[0]["n"])
out["before"] = snap()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    seed_s412.seed(os.environ["FINANCE_DB"])
out["seed_print"] = buf.getvalue()[-2200:]
out["after"] = snap()
out["locked_flag"] = q("SELECT COUNT(*) AS n FROM stmt_file WHERE folder='bank' AND locked=1")[0]["n"]
out["opened"] = q("SELECT COUNT(*) AS n FROM stmt_file WHERE locked=1 AND unlocked_path IS NOT NULL")[0]["n"]
out["secret_rows"] = q("SELECT COUNT(*) AS n FROM stmt_secret")[0]["n"]
out["unplaced"] = [[u["locked"], u.get("no_password"), (u["why"] or "")[:50]] for u in packs.unplaced(db) if u["folder"] == "bank"]
out["needs"] = [l["text"] for l in (c.get("/finance/sanjeevni/api/needs-you", headers={"X-Clinic-User": "manoj", "X-Clinic-Role": ""}).get_json(silent=True) or {}).get("lines", []) if "password" in l["text"]]
out["grid_aug"] = {x["slot"]: x["state"] for x in packs.cells(db, "2026-08") if x["kind"] != "card"}
out["grid_sep"] = {x["slot"]: x["state"] for x in packs.cells(db, "2026-09") if x["kind"] != "card"}
out["txt_rows"] = [(r["period_from"], r["period_to"], r["read_status"]) for r in q("SELECT period_from, period_to, read_status FROM stmt_file WHERE folder='bank' AND lower(name) LIKE '%.txt' ORDER BY id")]
out["amir_aug"] = packs.amir_pack(db, "2026-08")["ready"]
out["state_secrets"] = (c.get("/finance/packs/api/state?month=2026-08", headers={"X-Clinic-User": "manoj", "X-Clinic-Role": ""}).get_json(silent=True) or {}).get("secrets")
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath, script, extra=None):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_DIR=appdir, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1",
               STMT_DRIVE_STUB=STUB, STMT_INBOX=os.path.join(W, "inbox412_" + mode), PACKS_TODAY="2026-09-26", STMT_VENV_PYTHON=sys.executable, WALKDIR=W,
               W412_P1=P1, W412_P2=P2, W412_P3=P3)
    env.update(extra or {})
    p = subprocess.run([sys.executable, "-B", "-c", script], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        err = (p.stderr[-3000:] + "\n" + p.stdout[-800:])
        for s in (P1, P2, P3):
            err = err.replace(s, "<secret>")
        sys.exit("!! the %s app did not answer: %s" % (mode, err))
    return O


O = probe(a.old, "old", a.db + ".old", PROBE)
N = probe(a.app, "new", a.db, PROBE)
# the seed's two anchor routes, on copies of the NEW scratch after the run above
copydb(a.db, a.db + ".seedA")
copydb(a.db, a.db + ".seedB")
bakA = os.path.join(W, "w412_fake_backup.db")
copydb(a.db, bakA)
bk = sqlite3.connect(bakA)
bk.execute("UPDATE bank_anchor SET as_on='2026-08-31', balance_p=12345678, source=\"ICICI Sanjeevni statement 01-Aug..31-Aug-2026, the bank's own closing balance\", entered_by='seed S377', entered_at='2026-09-23T09:50:07' WHERE unit='medical' AND account='icici'")
bk.commit()
bk.close()
SA = probe(a.app, "seedA", a.db + ".seedA", PROBE_SEED, {"S412_ANCHOR_BACKUP": bakA})
SB = probe(a.app, "seedB", a.db + ".seedB", PROBE_SEED, {"S412_ANCHOR_BACKUP": os.path.join(W, "no_such_backup.db")})
R = probe(a.app, "real", a.db + ".real", PROBE_REAL, ({"S412_ANCHOR_BACKUP": a.anchor_backup} if a.anchor_backup else {"S412_ANCHOR_BACKUP": os.path.join(W, "no_such_backup.db")}))

print("-- 0  the fixtures: pdftotext refuses the three pypdf-locked PDFs exactly as it refuses the bank's ('Incorrect password'); the branch copy reads")
check("AES-256-R5 (two files) and RC4-128 (one) are refused by pdftotext with 'Incorrect password'; the plain branch copy is read; pypdf sees the three encrypted",
      all(enc[k][:3] == [1, True, True] for k in ("w412_yes_nk_aug_locked.pdf", "w412_yes_sanj_aug_locked.pdf", "w412_yes_bhawna_aug_locked.pdf")) and enc["w412_yes_sanj_aug_branch.pdf"][0] == 0
      and enc["w412_yes_sanj_aug_branch.pdf"][2] is False and enc["w412_yes_sanj_aug_branch.pdf"][3] > 200, enc)

print("-- 1  before any password: the locked files wait, named; everything else is placed and read; the Needs-you line")
p1 = N["placed1"]
S = lambda d, name: d.get(name, [None] * 13)  # noqa: E731
check("the three locked PDFs are unplaced, flagged locked, noted 'password-protected … Statement passwords', read_status empty; the branch copies and the ICICI files are placed and READ",
      all(S(p1, k)[0] is None and S(p1, k)[10] == 1 and S(p1, k)[8].startswith("password-protected") and "Statement passwords" in S(p1, k)[8] and S(p1, k)[7] is None
          for k in ("w412_yes_nk_aug_locked.pdf", "w412_yes_sanj_aug_locked.pdf", "w412_yes_bhawna_aug_locked.pdf"))
      and S(p1, "w412_yes_sanj_aug_branch.pdf")[:2] == ["yes_cur_sanj", "by words"] and S(p1, "w412_yes_sanj_aug_branch.pdf")[7] == "read"
      and S(p1, "w412_yes_clinic_sep_branch.pdf")[0] == "yes_cur_clinic" and S(p1, "w412_yes_clinic_sep_branch.pdf")[7] == "read"
      and S(p1, "w412_icici_sanj_aug.pdf")[7] == "read" and S(p1, "w412_icici_sanj_pipe_deg.txt")[:2] == ["icici_sanj", "by tail"] and S(p1, "w412_icici_sanj_pipe_deg.txt")[7] == "read",
      {k: (v[0], v[1], v[7], v[8][:40], v[10]) for k, v in p1.items()})
check("the Yes Bank reader's proven period is written back to the shelf row (01..31 Aug for the branch copy; 01..30 Sep for the clinic); the pipe .txt's DEGENERATE header (10-Sep..10-Sep) is WIDENED to its rows 01-Sep..10-Sep, on the shelf row and in icici_statement_period (closing not printed)",
      S(p1, "w412_yes_sanj_aug_branch.pdf")[5:7] == ["2026-08-01", "2026-08-31"] and S(p1, "w412_yes_clinic_sep_branch.pdf")[5:7] == ["2026-09-01", "2026-09-30"]
      and S(p1, "w412_icici_sanj_pipe_deg.txt")[5:7] == ["2026-09-01", "2026-09-10"] and N["pipe1"] == [{"account_ref": "4116", "period_from": "2026-09-01", "period_to": "2026-09-10", "closing_printed": 0}],
      (S(p1, "w412_yes_sanj_aug_branch.pdf")[5:7], S(p1, "w412_yes_clinic_sep_branch.pdf")[5:7], S(p1, "w412_icici_sanj_pipe_deg.txt")[5:7], N["pipe1"]))
check("after the 10th, with the previous month's Yes Bank cells still empty, the owner's Needs you says 'Yes Bank statements need their password on the packs page (3 locked files waiting)'; the page carries the 'Statement passwords' card; api/state tells 'not set' for the three banks and never a value",
      N["needs1"] == ["Yes Bank statements need their password on the packs page (3 locked files waiting)"] and N["page_card"] and N["state1_secrets"]
      and [b["bank"] for b in N["state1_secrets"]["banks"]] == ["YES", "ICICI", "HDFC"] and all(b["set"] is False for b in N["state1_secrets"]["banks"]) and N["state1_secrets"]["locked_open"] == 3,
      (N["needs1"], N["page_card"], N["state1_secrets"]))

print("-- 2  the non-Sanjeevni Yes Bank accounts never touch the shared tables; the owner's Bank card is byte-identical")
check("the clinic's Yes Bank statement (plain, 01..30 Sep, fetched alone after the first run) went to yesbank_account_statement_period/_line with slot_key yes_cur_clinic; NOTHING of tail 4123 in bank_statement_*; the Sanjeevni branch copy (4122) went to the SHARED tables (one period row); the Bank card (yesbank_position + bank_view) is byte-identical before and after that ingest -- and after the two unlocked non-Sanjeevni ones below",
      N["yes_acct"] and any(r["account_ref"] == "4123" and r["slot_key"] == "yes_cur_clinic" for r in N["yes_acct"][0]) and N["shared1"]["by_tail"]["4123"] == 0 and N["shared1"]["by_tail"]["4122"] == 1
      and N["card1b"] == N["card1"] and N["card2"] == N["card1"] and N["card3"] == N["card1"] and not N["card1"].startswith("ERR") and N["process1b"]["read"] == 1,
      (N["yes_acct"], N["shared1"]["by_tail"], N["card1b"] == N["card1"], N["card2"] == N["card1"], N["card3"] == N["card1"], N["process1b"], N["card1"][:60]))

print("-- 3  the password: owner-only, never echoed; the shelf opens what it fits, names what it cannot")
check("darpan is refused (302/403), an empty text is 400; the owner's three candidates (one wrong, two right) are accepted -- answer: ok, action 'set', candidates 3, opened now 2 -- and no candidate is in the answer",
      N["secret_darpan"] in (302, 403) and N["secret_bad"] == 400 and N["secret_set"][0] == 200 and N["secret_set"][1] == {"ok": True, "action": "set", "candidates": 3, "bank": "YES"} and N["secret_set"][2] == 2,
      (N["secret_darpan"], N["secret_bad"], N["secret_set"]))
p2 = N["placed2"]
check("the AES-256 NK file OPENED (<id>.unlocked.pdf beside the locked original, pdftotext reads it) -> placed on Yes Bank NK by words, READ into the per-account tables (slot_key yes_cur_nk, tail 4121), nothing of 4121 in the shared tables",
      S(p2, "w412_yes_nk_aug_locked.pdf")[:2] == ["yes_cur_nk", "by words"] and S(p2, "w412_yes_nk_aug_locked.pdf")[7] == "read" and S(p2, "w412_yes_nk_aug_locked.pdf")[11] is True
      and N["unlocked_reads"] and N["unlocked_reads"][0] == 0 and N["unlocked_reads"][1] and N["unlocked_reads"][2].endswith(".unlocked.pdf")
      and any(r["account_ref"] == "4121" and r["slot_key"] == "yes_cur_nk" for r in N["yes_acct"][0]) and N["shared2"]["by_tail"]["4121"] == 0,
      (S(p2, "w412_yes_nk_aug_locked.pdf"), N["unlocked_reads"], N["shared2"]["by_tail"]))
check("the RC4 Sanjeevni file OPENED but its month is already on the shelf from the branch: 'duplicate of branch copy', never read again (the shared tables hold ONE period row and the same lines as before); the cell shows the BRANCH copy",
      S(p2, "w412_yes_sanj_aug_locked.pdf")[7] == "duplicate of branch copy" and "branch copy" in (S(p2, "w412_yes_sanj_aug_locked.pdf")[12] or "") and S(p2, "w412_yes_sanj_aug_locked.pdf")[0] == "yes_cur_sanj"
      and N["shared2"]["by_tail"]["4122"] == 1 and N["shared2"]["n_lines"] == N["shared1"]["n_lines"] and N["cells_aug"]["yes_cur_sanj"] == ["matched", "w412_yes_sanj_aug_branch.pdf", False],
      (S(p2, "w412_yes_sanj_aug_locked.pdf")[7:], N["shared2"]["by_tail"], N["shared2"]["n_lines"], N["shared1"]["n_lines"], N["cells_aug"].get("yes_cur_sanj")))
check("the file no candidate opens reads 'locked -- no password', noted 'none of the stored passwords opens it'; Needs you now says 'the stored Yes Bank password opens none of 1 locked statement'; the Bank card is STILL byte-identical; the log says set + opened, never a value",
      S(p2, "w412_yes_bhawna_aug_locked.pdf")[7] == "locked -- no password" and "none of the stored" in S(p2, "w412_yes_bhawna_aug_locked.pdf")[8] and S(p2, "w412_yes_bhawna_aug_locked.pdf")[0] is None
      and N["needs2"] == ["the stored Yes Bank password opens none of 1 locked statement -- replace it on the packs page"] and N["card2"] == N["card1"]
      and N["log"] and len(N["log"]) == 3 and N["log"][0] == "YES:set" and all(x.startswith("YES:opened file ") for x in N["log"][1:]),
      (S(p2, "w412_yes_bhawna_aug_locked.pdf")[7:9], N["needs2"], N["card2"] == N["card1"], N["log"]))
check("the grid: August NK 'read' from the opened file (flagged), Sanjeevni 'matched' from the branch copy, Dr Bhawna empty; September clinic 'read' 01..30 Sep, ICICI Sanjeevni PARTIAL (01..10 Sep); Amir's pack: July NOT ready (no Yes Bank file), August READY (both Sanjeevni statements)",
      N["cells_aug"]["yes_cur_nk"] == ["read", "w412_yes_nk_aug_locked.pdf", True] and N["cells_aug"]["yes_sav_bhawna"][0] == "empty" and N["cells_aug"]["icici_sanj"][0] == "matched"
      and N["cells_sep"]["yes_cur_clinic"] == ["read", "2026-09-01", "2026-09-30"] and N["cells_sep"]["icici_sanj"] == ["partial", "2026-09-01", "2026-09-10"] and N["amir"] == [False, True],
      (N["cells_aug"], N["cells_sep"], N["amir"]))
p3 = N["placed3"]
check("Replace with the third candidate: action 'replaced', opened now 1 -> Dr Bhawna's file read into the per-account tables (yes_sav_bhawna); the earlier opened files stay opened; api/state: YES set, 1 candidate, 0 locked open, 3 opened; the log: set, opened, opened, replaced, opened",
      N["secret_replace"][0] == 200 and N["secret_replace"][1] == {"ok": True, "action": "replaced", "candidates": 1} and N["secret_replace"][2] == 1
      and S(p3, "w412_yes_bhawna_aug_locked.pdf")[0] == "yes_sav_bhawna" and S(p3, "w412_yes_bhawna_aug_locked.pdf")[7] == "read" and S(p3, "w412_yes_nk_aug_locked.pdf")[7] == "read"
      and any(r["account_ref"] == "4124" and r["slot_key"] == "yes_sav_bhawna" for r in (N["yes_acct2"] or [])) and N["shared3"]["by_tail"]["4124"] == 0 and N["card3"] == N["card1"]
      and N["state2_secrets"]["banks"][0]["set"] is True and N["state2_secrets"]["banks"][0]["candidates"] == 1 and N["state2_secrets"]["locked_open"] == 0 and N["state2_secrets"]["opened"] == 3
      and [x.split(" ")[0] for x in N["log2"]] == ["YES:set", "YES:opened", "YES:opened", "YES:replaced", "YES:opened"],
      (N["secret_replace"], S(p3, "w412_yes_bhawna_aug_locked.pdf")[:2] + S(p3, "w412_yes_bhawna_aug_locked.pdf")[7:8], N["yes_acct2"], N["state2_secrets"], N["log2"]))
check("THE SECRET NEVER APPEARS: not in the page, not in api/state, not in the two answers, not in 'stmt_shelf.py unlock' output ('%s'), not in any stmt_file row or log row; it is in stmt_secret only; no 'secret' field in api/state" % N.get("unlock_cmd"),
      N["leak"] and not any(N["leak"]) and N["in_secret_table"] is True and N["stmt_secret_cols_in_state"] is False and N["versions"] == ["1.1", "1.1"] and "opened 0, still locked 0, candidates 1" in (N.get("unlock_cmd") or ""),
      (N["leak"], N["in_secret_table"], N["stmt_secret_cols_in_state"], N["versions"], N.get("unlock_cmd")))

print("-- 4  the ICICI anchor (3a): a real period with a printed closing moves it; the pipe .txt never")
check("the iCRM August statement (printed closing, 01..31 Aug) moved the anchor 31-Jul -> 31-Aug; the pipe .txt (no closing printed, degenerate header) read AFTER it left the anchor at 31-Aug",
      N["anchor1"] and N["anchor1"]["as_on"] == "2026-08-31" and N["anchor1"]["balance_p"] == ICRM_AUG_CLOSING and "(S408 shelf)" in N["anchor1"]["source"] and N["anchor2"]["as_on"] == "2026-08-31",
      (N["anchor1"], N["anchor2"]))
check("the seed on a copy left as S411's run left it (anchor on 10-Sep..10-Sep, a degenerate pipe row): RESTORED from the backup's row (31-Aug, its balance, 'seed S377'); the degenerate row dropped, the .txt read again with the widened period",
      SA["anchor"]["as_on"] == "2026-08-31" and SA["anchor"]["balance_p"] == 12345678 and SA["anchor"]["entered_by"] == "seed S377" and "RESTORED from the S411 backup" in SA["print"]
      and SA["deg_before"] == 1 and SA["deg_after"] == 0 and SA["pipe"] == [{"account_ref": "4116", "period_from": "2026-09-01", "period_to": "2026-09-10"}] and SA["txt_row"] == [{"period_from": "2026-09-01", "period_to": "2026-09-10", "read_status": "read"}],
      (SA["anchor"], SA["deg_before"], SA["deg_after"], SA["pipe"], SA["txt_row"], SA["print"][-300:]))
check("the same seed with NO backup row: RECOMPUTED from the newest iCRM statement with a printed closing (31-Aug, the iCRM closing, 'seed S412')",
      SB["anchor"]["as_on"] == "2026-08-31" and SB["anchor"]["balance_p"] == SB["icrm_aug_closing"] == ICRM_AUG_CLOSING and SB["anchor"]["entered_by"] == "seed S412" and "RECOMPUTED" in SB["print"] and SB["deg_after"] == 0,
      (SB["anchor"], SB["print"][-200:]))

print("-- 5  THE REAL SHELF (the live files, a scratch copy) seeded exactly as the install does it -- counts, dates and states only")
rb, ra = R["before"], R["after"]
real_ok = rb["files"] == 0 or (
    ra["anchor"] and ra["anchor"]["as_on"] == "2026-08-31" and ra["read"] == rb["read"] and ra["icici_lines"] == rb["icici_lines"] and ra["bank_periods"] == rb["bank_periods"] and ra["bank_lines"] == rb["bank_lines"]
    and len(ra["pipe"]) == 4 and not any(p[1] == p[2] for p in ra["pipe"]) and all(p[1] < p[2] for p in ra["pipe"]) and {p[2] for p in ra["pipe"]} >= {"2026-09-10", "2026-09-14"} and {p[0] for p in ra["pipe"]} == {p[0] for p in rb["pipe"]}
    and sum(1 for p in rb["pipe"] if p[1] == p[2]) == 3
    and R["locked_flag"] == rb["locked_note"] == 5 and R["opened"] == 0 and R["secret_rows"] == 0 and len(R["unplaced"]) == 5 and all(u[0] and not u[1] for u in R["unplaced"])
    and R["needs"] == ["Yes Bank statements need their password on the packs page (5 locked files waiting)"] and R["amir_aug"] is False
    and all(R["grid_aug"][k] in ("read", "matched") for k in ("icici_huf", "icici_bhawna", "icici_personal", "icici_clinic", "icici_nk", "icici_sanj")) and all(R["grid_aug"][k] == "empty" for k in ("yes_cur_nk", "yes_cur_sanj", "yes_sav_bhawna"))
    and all(t[2] == "read" and t[0] < t[1] for t in R["txt_rows"]) and R["state_secrets"]["locked_open"] == 5)
check("the real shelf after the seed: the anchor back on 31-Aug (%s); the 3 degenerate pipe periods gone, all 4 widened to their rows (%s); %d files still read, the ICICI lines and the Yes Bank tables unchanged; the 5 locked files flagged, unplaced and waiting for the password (none opened -- no secret stored); "
      "Needs you names them; the six ICICI cells of August read; Amir's August pack not ready (the Yes Bank Sanjeevni statement is still locked)"
      % ((ra["anchor"] or {}).get("entered_by"), ", ".join("…%s %s..%s" % tuple(p) for p in ra["pipe"]), ra["read"]),
      real_ok, (rb, ra, R["locked_flag"], R["opened"], R["secret_rows"], R["unplaced"], R["needs"], R["amir_aug"], R["grid_aug"], R["txt_rows"], R["state_secrets"]))
for ln in R["seed_print"].splitlines():
    if ln.strip().startswith(("anchor", "the backup", "pipe periods", "locked files", "grid", "unplaced", "amir")):
        print("     " + ln.strip()[:300])

print("-- 6  NEGATIVE CONTROL on the box as it is (S411's files, the same fixtures)")
op = O["placed1"]
check("NEGATIVE: no password card and no /api/secret (404 for the owner); the locked files stay 'password-protected' with no unlock; the clinic's Yes Bank statement lands in the SHARED tables (tail 4123 in bank_statement_period) and the owner's Bank card CHANGES on that one ingest; the pipe period stays degenerate 10-Sep..10-Sep and the anchor moves to 10-Sep on it",
      O["page_card"] is False and O["secret_darpan"] in (302, 403, 404) and O["secret_set"][0] == 404 and all(S(op, k)[0] is None and S(op, k)[8].startswith("password-protected") and S(op, k)[10] is None for k in ("w412_yes_nk_aug_locked.pdf", "w412_yes_sanj_aug_locked.pdf"))
      and O["shared1"]["by_tail"]["4123"] >= 1 and O["card1b"] != O["card1"] and O["pipe1"] and O["pipe1"][0]["period_from"] == O["pipe1"][0]["period_to"] == "2026-09-10" and O["anchor1"]["as_on"] == "2026-09-10" and O["yes_acct"] is None,
      (O["page_card"], O["secret_darpan"], O["secret_set"][0], {k: (v[0], v[8][:25], v[10]) for k, v in op.items() if "locked" in k}, O["shared1"]["by_tail"], O["card1b"] != O["card1"], O["pipe1"], O["anchor1"]))

print(("WALK_S412 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S412 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
