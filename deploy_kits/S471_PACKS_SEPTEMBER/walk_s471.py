#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s471.py -- S471_PACKS_SEPTEMBER (session 293, 04-Oct-2026). Hermetic (F-709): every store the code can reach is a
scratch folder made here and removed at the end -- a scratch finance folder with the edited files beside the box's own
readers, an EMPTY finance.db built by packs.ensure(), a scratch statement inbox, made-up PDFs. Nothing live is read.

What it proves, each on the NEW files and -- where the behaviour changed -- SHOWN on the OLD file too:
  A  two consecutive cycle statements (11-Aug..10-Sep + 11-Sep..10-Oct) are the month's statement: the cell reads 'read' with
     two pieces, the pack row is 'ready' with two attachments 'part 1 of 2' / 'part 2 of 2'. On the OLD file: 'partial'.
  B  one cycle statement alone is 'partial' on the cell AND the row (one word), and the row says which statement completes
     the month and roughly when it is due.
  C  a whole-month statement is unchanged: 'read' / 'ready', one attachment, no 'part'.
  D  two statements with a gap between them are NOT stitched.
  E  the passwords card lists the six Yes Bank accounts first (account=True), then the three banks as 'any other'; a password
     saved under an account key is stored and listed; an unknown key is refused (400); the bank-wide key still works.
  F  the unlock step tries the account key FIRST: with a wrong bank-wide password and the right account password stored, a
     locked PDF (made here with pypdf) opens and the log names the account key; the card shows 'opened 1'.
     (needs pypdf: run under the venv python when there is one; otherwise this check is a NOTE, not a FAIL)
  G  the row titles are numbered 3.1 .. 3.12, 4.1 .. 4.4, 8.1, 8.2 -- no two rows share a title; the electricity row says the
     bills show in the ICICI statements when none is on the shelf.
  H  packs.html carries the new words ('partial', '(bank-wide)', '07:30', 'open part', 'open' in the Shavez summary).
Prints FAIL / NOTE lines and ends with WALK_S471 GREEN|RED <n checks>.
   usage: walk_s471.py --apply apply_s471.py --finance /root/finance [--venv /root/wa/venv/bin/python3]
"""
import argparse
import datetime as dt
import hashlib
import importlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FAILS, NOTES, CHECKS = [], [], 0


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(name + (" -- " + detail if detail else ""))
        print("  FAIL %s %s" % (name, detail))
    return ok


def note(msg):
    NOTES.append(msg)
    print("  NOTE " + msg)


def pdf_bytes(text):
    """A one-page PDF with the given text (pdftotext reads it). Hand-written, no library."""
    stream = ("BT /F1 12 Tf 40 750 Td (%s) Tj ET" % text).encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out


def load_packs(folder, tag):
    """Import packs.py from a folder under a unique module name, with HERE pointing at that folder."""
    sys.path.insert(0, folder)
    for k in [k for k in sys.modules if k in ("packs", "finance_icici", "finance_yesbank", "yes_branch")]:
        del sys.modules[k]
    spec = importlib.util.spec_from_file_location("packs_" + tag, os.path.join(folder, "packs.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod


def seed_file(con, folder, slot_key, pf, pt, text, read="read", locked=0, local=True):
    sid = con.execute("SELECT id FROM stmt_slot WHERE key=?", (slot_key,)).fetchone()
    sid = sid[0] if sid else None
    name = "%s_%s_%s.pdf" % (slot_key, pf, pt)
    path = os.path.join(folder, name)
    with open(path, "wb") as fh:
        fh.write(pdf_bytes(text))
    con.execute("INSERT INTO stmt_file (drive_id, name, mtime, size, folder, slot_id, period_from, period_to, read_status, matched_status, fetched_at, local_path, bank, locked)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("drv_" + hashlib.md5(name.encode()).hexdigest()[:10], name, "2026-10-04T05:40:00", 1000, "bank", sid, pf, pt, read, "ingested 9 lines" if read == "read" else "",
                 "2026-10-04T05:40:00", path if local else None, (slot_key.split("_")[0].upper() if sid else ""), locked))
    con.commit()
    return con.execute("SELECT id FROM stmt_file WHERE name=?", (name,)).fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True, help="the box's finance folder (READ ONLY: its readers are copied beside the scratch)")
    ap.add_argument("--venv", default="/root/wa/venv/bin/python3")
    a = ap.parse_args()
    scr = tempfile.mkdtemp(prefix="s471_walk_")
    try:
        old = os.path.join(scr, "old"); new = os.path.join(scr, "new"); inbox = os.path.join(scr, "inbox")
        os.makedirs(old); os.makedirs(new); os.makedirs(inbox)
        for f in ("packs.py", "packs.html", "stmt_shelf.py", "finance_icici.py", "finance_yesbank.py", "yes_branch.py"):
            src = os.path.join(a.finance, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(old, f)); shutil.copy2(src, os.path.join(new, f))
        r = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "packs.py"), os.path.join(new, "packs.html"), os.path.join(new, "stmt_shelf.py")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check("apply on scratch", r.returncode == 0, r.stderr.decode()[-200:])
        os.environ["STMT_INBOX"] = inbox
        os.environ["STMT_VENV_PYTHON"] = a.venv if os.path.exists(a.venv) else sys.executable
        os.environ["PACKS_DIR"] = os.path.join(scr, "packs")
        os.environ["PACKS_ENV"] = os.path.join(scr, "no.env")
        os.environ["ASSETS_UPLOADS"] = os.path.join(scr, "uploads")
        os.environ["FINANCE_DB"] = os.path.join(scr, "finance.db")
        dbp = os.path.join(scr, "finance.db")
        P = load_packs(new, "new")
        con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row
        P.ensure(con)
        # the tables other builders touch, so pack_rows runs on an empty box
        for d in ("CREATE TABLE IF NOT EXISTS clinic_day_revenue (business_date TEXT, revenue_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS upi_txn (unit TEXT, txn_date TEXT, amount_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS app_setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)"):
            con.execute(d)
        con.commit()
        M = "2026-09"
        # ---- A: two cycle statements, contiguous
        seed_file(con, inbox, "icici_sanj", "2026-08-11", "2026-09-10", "ICICI Sanjeevni cycle one")
        seed_file(con, inbox, "icici_sanj", "2026-09-11", "2026-10-10", "ICICI Sanjeevni cycle two")
        # ---- B: one cycle statement alone
        seed_file(con, inbox, "icici_clinic", "2026-08-15", "2026-09-14", "ICICI clinic cycle one")
        # ---- C: a whole-month branch statement
        seed_file(con, inbox, "yes_cur_nk", "2026-09-01", "2026-09-30", "YES NK September")
        # ---- D: two statements with a gap (ends 10-Sep, next starts 15-Sep)
        seed_file(con, inbox, "icici_nk", "2026-08-11", "2026-09-10", "ICICI NK cycle one")
        seed_file(con, inbox, "icici_nk", "2026-09-15", "2026-10-14", "ICICI NK cycle two (gap)")
        cl = {c["slot"]: c for c in P.cells(con, M)}
        A = cl["icici_sanj"]
        check("A cell is read with 2 pieces", A["state"] == "read" and len(A["pieces"]) == 2, "%s %d" % (A["state"], len(A.get("pieces") or [])))
        B = cl["icici_clinic"]
        check("B cell is partial", B["state"] == "partial", B["state"])
        check("B partial words name the next statement and its due", "15-Sep-2026 → 14-Oct-2026" in (B.get("partial_words") or "") and "due from the bank about 15-Oct-2026" in (B.get("partial_words") or ""), B.get("partial_words"))
        C = cl["yes_cur_nk"]
        check("C whole-month cell unchanged (read, no pieces)", C["state"] == "read" and not C["pieces"], C["state"])
        D = cl["icici_nk"]
        check("D a gap is not stitched", D["state"] == "partial" and not D["pieces"], "%s %d" % (D["state"], len(D["pieces"])))
        rows, att = P.pack_rows(con, M)
        by = {r["key"]: r for r in rows}
        rA = by["stmt:icici_sanj"]
        check("A row ready with two attachments part 1/2", rA["status"] == "ready" and len(rA["files"]) == 2 and "(part 1 of 2)" in rA["files"][0] and "(part 2 of 2)" in rA["files"][1], json.dumps(rA["files"]))
        check("A row why names both periods", "2 statements together cover the month" in rA["why"] and "11-Aug-2026 → 10-Sep-2026 + 11-Sep-2026 → 10-Oct-2026" in rA["why"], rA["why"])
        rB = by["stmt:icici_clinic"]
        check("B row status is 'partial' (one word with the shelf)", rB["status"] == "partial" and rB["why"] == B["partial_words"], "%s | %s" % (rB["status"], rB["why"]))
        rC = by["stmt:yes_cur_nk"]
        check("C row ready, one attachment, no 'part'", rC["status"] == "ready" and len(rC["files"]) == 1 and "part" not in rC["files"][0], json.dumps(rC["files"]))
        rD = by["stmt:icici_nk"]
        check("D row partial", rD["status"] == "partial", rD["status"])
        check("an empty slot is still 'missing' / 'not on the shelf'", by["stmt:yes_sav_huf"]["status"] == "missing" and by["stmt:yes_sav_huf"]["why"] == "not on the shelf")
        # ---- G: numbering and the electricity words
        titles = [r["title"] for r in rows]
        check("G no two rows share a title", len(titles) == len(set(titles)), str([t for t in titles if titles.count(t) > 1][:3]))
        s3 = [r["title"] for r in rows if r["key"].startswith("stmt:")]
        check("G bank rows numbered 3.1 .. 3.%d" % len(s3), s3[0].startswith("3.1 · ") and s3[-1].startswith("3.%d · " % len(s3)), "%s .. %s" % (s3[0][:8], s3[-1][:8]))
        s4 = [r["title"] for r in rows if r["key"].startswith("card:") or r["key"] == "cards"]
        check("G card rows 4.1 .. 4.4", [t.split(" ")[0] for t in s4] == ["4.1", "4.2", "4.3", "4.4"], str([t[:6] for t in s4]))
        s8 = [r["title"] for r in rows if r["key"].startswith("bundle:")]
        check("G bundle rows 8.1, 8.2", [t.split(" ")[0] for t in s8] == ["8.1", "8.2"], str(s8))
        # electricity with no ICICI statement on the shelf: a fresh month
        rows2, _ = P.pack_rows(con, "2026-07")
        e = [r for r in rows2 if r["key"] == "electricity"][0]
        check("G electricity says the bills show in the ICICI statements (none on the shelf)", "paid around the 17th" in e["why"] and "not on the shelf yet" in e["why"], e["why"])
        e9 = by["electricity"]
        check("G electricity keeps the old words once an ICICI statement is on the shelf", "paid around the 17th" not in e9["why"], e9["why"][:80])
        # the checklist's own count still reads the stitched row as ready
        ck = {c["item"]: c for c in P.checklist(con, M)}
        st_item = [v for k, v in ck.items() if "Saare bank statement" in k]
        check("checklist 'Saare bank statement' counts the stitched month as on the shelf (A + C = 2)", bool(st_item) and st_item[0]["words"].startswith("2 / "), st_item[0]["words"] if st_item else "no item")
        # ---- E: the passwords card
        sec = P.secret_state(con)
        keys = [b["bank"] for b in sec["banks"]]
        check("E six Yes Bank accounts first, then three banks", keys[:6] == ["YES:yes_cur_nk", "YES:yes_cur_clinic", "YES:yes_cur_sanj", "YES:yes_sav_manoj", "YES:yes_sav_bhawna", "YES:yes_sav_huf"] and keys[6:] == ["YES", "ICICI", "HDFC"], str(keys))
        check("E account rows say account=True, bank rows 'any other'", all(b["account"] for b in sec["banks"][:6]) and all((not b["account"]) and "(any other)" in b["label"] for b in sec["banks"][6:]))
        body, code = P.set_secret(con, "YES:yes_sav_huf", "huf-secret-S471\n", "walk")
        check("E an account password is accepted", code == 200 and body["ok"] and body["bank"] == "YES:yes_sav_huf", json.dumps(body)[:160])
        body, code = P.set_secret(con, "YES:no_such_slot", "x", "walk")
        check("E an unknown account key is refused", code == 400)
        body, code = P.set_secret(con, "yes", "wrong-bank-wide\n", "walk")
        check("E the bank-wide key still works (case folded)", code == 200 and body["bank"] == "YES")
        sec = P.secret_state(con)
        huf = [b for b in sec["banks"] if b["bank"] == "YES:yes_sav_huf"][0]
        check("E the account row reads set, 1 candidate", huf["set"] and huf["candidates"] == 1)
        check("E no password value in the state", "huf-secret-S471" not in json.dumps(sec) and "wrong-bank-wide" not in json.dumps(sec))
        # ---- F: the unlock order, under the venv python (pypdf) when there is one
        vpy = a.venv if os.path.exists(a.venv) else sys.executable
        has_pypdf = subprocess.run([vpy, "-c", "import pypdf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
        if not has_pypdf:
            note("F skipped: no python with pypdf here (%s); the unlock order is proven on the box under the venv" % vpy)
        else:
            lockedp = os.path.join(inbox, "locked_huf.pdf")
            mk = ("import sys\nfrom pypdf import PdfReader, PdfWriter\nimport io\nrd=PdfReader(io.BytesIO(open(sys.argv[1],'rb').read()))\n"
                  "wr=PdfWriter(clone_from=rd)\nwr.encrypt('huf-secret-S471')\nwr.write(open(sys.argv[2],'wb'))\n")
            plain = os.path.join(inbox, "plain_huf.pdf")
            with open(plain, "wb") as fh:
                fh.write(pdf_bytes("YES BANK HUF e-statement"))
            r = subprocess.run([vpy, "-c", mk, plain, lockedp], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            check("F a locked PDF is made", r.returncode == 0 and os.path.exists(lockedp), r.stderr.decode()[-160:])
            con.execute("INSERT INTO stmt_file (drive_id, name, mtime, size, folder, fetched_at, local_path, locked) VALUES (?,?,?,?,?,?,?,1)",
                        ("drv_locked_huf", "locked_huf.pdf", "2026-10-04T05:40:00", 900, "bank", "2026-10-04T05:40:00", lockedp))
            con.commit()
            r = subprocess.run([vpy, "-B", os.path.join(new, "stmt_shelf.py"), "unlock"], cwd=new, env=dict(os.environ, FINANCE_DB=dbp, STMT_INBOX=inbox),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
            out = r.stdout.decode()
            check("F unlock opened 1", "opened 1" in out, (out + r.stderr.decode())[-200:])
            con2 = sqlite3.connect(dbp)
            who = con2.execute("SELECT bank FROM stmt_secret_log WHERE action LIKE 'opened file %' ORDER BY id DESC LIMIT 1").fetchone()
            check("F the log names the ACCOUNT key, not the bank", bool(who) and who[0] == "YES:yes_sav_huf", str(who))
            up = con2.execute("SELECT unlocked_path FROM stmt_file WHERE name='locked_huf.pdf'").fetchone()
            check("F the unlocked copy is in the scratch inbox", bool(up and up[0] and up[0].startswith(inbox) and os.path.exists(up[0])), str(up))
            con2.close()
            sec = P.secret_state(con)
            huf = [b for b in sec["banks"] if b["bank"] == "YES:yes_sav_huf"][0]
            check("F the card shows opened 1 for the account", huf["opened"] == 1, str(huf))
            check("F no secret in the unlock output", "huf-secret" not in out and "wrong-bank" not in out)
        # ---- H: the page
        html = open(os.path.join(new, "packs.html"), encoding="utf-8").read()
        for w in ('r.status==="partial"', "(bank-wide)", "07:30", "open part", '" open"', "One password per Yes Bank account"):
            check("H packs.html carries %r" % w, w in html)
        # ---- SHOWN on the OLD file: the same two cycle statements are 'partial' there
        con.close()
        O = load_packs(old, "old")
        conO = sqlite3.connect(dbp); conO.row_factory = sqlite3.Row
        clO = {c["slot"]: c for c in O.cells(conO, M)}
        check("SHOWN on the old file: A is 'partial' there", clO["icici_sanj"]["state"] == "partial", clO["icici_sanj"]["state"])
        rowsO, _ = O.pack_rows(conO, M)
        check("SHOWN on the old file: A's row is 'missing' there", [r for r in rowsO if r["key"] == "stmt:icici_sanj"][0]["status"] == "missing")
        conO.close()
        # nothing outside the scratch was touched
        check("hermetic: the box's packs.py untouched", hashlib.md5(open(os.path.join(a.finance, "packs.py"), "rb").read()).hexdigest() == hashlib.md5(open(os.path.join(old, "packs.py"), "rb").read()).hexdigest())
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S471 %s %d checks, %d fail, %d note" % ("GREEN" if not FAILS else "RED", CHECKS, len(FAILS), len(NOTES)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    import importlib.util  # noqa: E402
    main()
