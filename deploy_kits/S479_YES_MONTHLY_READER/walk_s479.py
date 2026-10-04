#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s479.py -- S479_YES_MONTHLY_READER (session 294, 04-Oct-2026). Hermetic (F-709): yes_monthly.py and packs.py are copied
into a scratch folder (packs.py old as it is, new with the kit) beside the box's other readers; statements are MADE UP at run time
in the monthly layout (every number here is invented when the walk runs); an empty database from packs.ensure(); a throwaway
Flask app with made-up logins. Nothing live is opened, no network, and pdftotext is never asked about a real file.

  1. THE READER: a made-up month is read -- the opening row, rows whose description is wrapped around them in one, two, three and
     four lines (joined as they were cut), a reference in its column, a page break with the bank's foot lines between two rows,
     the interest row posted next month with this month's value date; the holder is the 'Primary Holder' line, never the
     proprietor line; kind and tail from the account's own lines; long digit runs keep their last four.
  2. THE PROOFS: a wrong running balance, a missing row, a wrong total (each of the two), a wrong opening row, a row outside the
     period by both its dates, two accounts in one file, a title whose period is not the account's, a missing foot line, a
     description line that pairs with no row -- each is REFUSED, whole.
  3. NOT ITS LAYOUT: the branch's print and the net-banking download are not taken for it.
  4. ONE LINE ONCE: the first read writes every row; the same file again writes nothing; a period another file COVERS is checked
     and nothing is written (agrees / differs said); rows another file holds for PART of the period are not written twice
     (the net-banking download beside the month's statement), two equal rows on one day are counted, not merged.
  4b. ONE LINE ONCE ACROSS THE THREE LAYOUTS: finance_yesbank.py and yes_branch.py, new beside old, each fed the same bank rows as
     its own layout keys them: after the month's statement neither writes a row twice; two net-banking downloads behave exactly
     as before; SHOWN on the readers as they are today -- the rows go in twice.
  5. THROUGH THE SHELF (packs.py new): the file is named Yes Bank with its period, placed by its holder's words (the HUF's
     statement on the HUF slot, the pharmacy's on the pharmacy's, never on the proprietor's), read, and the month's cell fills;
     a locked twin of a month the branch already gave is 'duplicate of branch copy'.
  6. THE COPY A PERSON CAN OPEN: the accountants' attachment, the owner's preview and Amir's pack carry the unlocked copy of an
     opened statement; a file that was never locked goes out exactly as before.
  7. SHOWN on the old packs.py: the same text is given another bank or no period, and the three doors hand out the locked file.
Last line: WALK_S479 GREEN|RED.
   usage: walk_s479.py --apply apply_s479.py --reader yes_monthly.py --finance /root/finance   (packs.py, finance_yesbank.py, yes_branch.py are read there)
"""
import argparse
import hashlib
import importlib.util
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FAILS, CHECKS = [], 0
RND = random.Random()


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(name)
        print("  FAIL %s %s" % (name, str(detail)[:500]))


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def load(folder, fname, tag):
    sys.path.insert(0, folder)
    for k in [k for k in sys.modules if k in ("packs", "finance_icici", "finance_yesbank", "yes_branch", "yes_monthly")]:
        del sys.modules[k]
    spec = importlib.util.spec_from_file_location(tag, os.path.join(folder, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod


def inr(p):
    """paise -> the bank's own grouping: 12,34,567.89"""
    rs, ps = divmod(abs(p), 100)
    s = str(rs)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:]); head = head[:-2]
        s = ",".join(([head] if head else []) + groups + [tail])
    return ("-" if p < 0 else "") + "%s.%02d" % (s, ps)


def digits(n):
    return "".join(RND.choice("123456789") for _ in range(n))


HEADING = ["Transaction                                                         Cheque",
           "            Value Date                Description                                        Deposits         Withdrawals      Running Balance",
           "   Date                                                         No/Reference No"]
PAGEFOOT = ['Say "Hi" on +00 00000 00000 for     YES TOUCH PhoneBanking Number:',
            "WhatsApp Banking                    0000 0000 (Toll Free for Mobile & Landlines in India)",
            "Email us at yesfirst@yes.bank.in     +00 00 0000 0000 (When calling from Outside India)",
            "                                    Toll Free number from USA: 00000000000",
            "CIN: L00000MH0000PLC000000          Canada: 00000000000 | UK: 0000000000 | UAE: 000000000000",
            "",
            "                                                                                                                                         Page 1 of 2"]


def row(d, vd, mid, ref, dep, wd, bal):
    return ("%s %s " % (d, vd) + (mid or "").ljust(42)[:42] + (ref or "").ljust(16) + inr(dep).rjust(16) + inr(wd).rjust(18) + inr(bal).rjust(20)).rstrip()


def statement(acct, holder, kind_words, opening, txns, pfrom="01-Sep-2026", pto="30-Sep-2026", title=None, break_after=None,
              totals=None, bf=None, drop_foot=False, extra_line_after=None):
    """txns: (date, value date, [description pieces as cut], reference, deposit, withdrawal). Returns (text, facts)."""
    L = ["                              YOUR ACCOUNT STATEMENT FROM %s TO %s" % (title or (pfrom, pto)), "", "",
         " M/S. %s" % holder, " PROP SOMEONE ELSE HUF,                                            RM Details :",
         " 00 WALK STREET                                                           A PERSON", " WALKTOWN", "",
         "                                         Account Relationship Summary as on %s" % pto,
         "      Account Number                    Account Type                          Currency                              Balance",
         "      %s                  %s                           INR                                            %s" % (acct, kind_words, inr(opening)), "",
         "       Statement Of Transactions In Savings/Current Account No:%s For The Period Of %s to %s" % (acct, pfrom, pto),
         "  Branch : 0000, WALKTOWN, A STATE, A TOWER GROUND FLOOR,",
         "                               IFSC: YESB0000000, MICR: 000000000, Email: BM_0000@yes.bank.in", "",
         "Primary Holder : %s                             Product Code                   :   000" % holder,
         "Joint Holder 1   : NA                                          A/C Opening Date               :   01-Jan-2019",
         "Nominee(s)       : NOT REGISTERED                              Account status                 :   ACCOUNT OPEN REGULAR", ""]
    L += HEADING
    L.append(("%s %s B/F" % (pfrom, pfrom)).ljust(110) + inr(opening if bf is None else bf).rjust(20))
    L.append("")
    bal, dep_t, wd_t = opening, 0, 0
    for i, (d, vd, pieces, ref, dep, wd) in enumerate(txns):
        bal += dep - wd; dep_t += dep; wd_t += wd
        n = len(pieces)
        above = pieces[:n // 2]
        mid = pieces[n // 2] if n % 2 else ""
        below = pieces[n // 2 + (n % 2):]
        for p in above:
            L.append(" " * 27 + p)
        L.append(row(d, vd, mid, ref, dep, wd, bal))
        for p in below:
            L.append(" " * (27 if p != "K LIMITED" else 24) + p)
        if extra_line_after == i:
            L.append(" " * 27 + "A LINE THAT BELONGS TO NO ROW")
        if break_after == i:
            L += ["", ""] + PAGEFOOT
            L.append("\f" + HEADING[0]); L += HEADING[1:]
    L.append("")
    t = totals or (opening, dep_t, wd_t, bal)
    if not drop_foot:
        L.append(" Opening Balance: %s         Total Deposits: %s     Total Withdrawals: %s       Closing Balance: %s" % tuple(inr(x) for x in t))
    L += ["", "Mandatory disclaimer", "For any assistance required, please contact a YES BANK branch official.", ""] + PAGEFOOT
    return "\n".join(L) + "\n", dict(closing=bal, deposits=dep_t, withdrawals=wd_t, n=len(txns))


def dbf(dbp):
    con = sqlite3.connect(dbp, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def refuses(M, text, word):
    try:
        M.parse_text(text)
    except M.StatementRejected as ex:
        return word in str(ex), str(ex)
    return False, "it was READ"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--reader", required=True)
    ap.add_argument("--finance", required=True)
    a = ap.parse_args()
    LIVE = [os.path.join(a.finance, f) for f in ("packs.py", "finance_yesbank.py", "yes_branch.py")]
    before = [md5(f) for f in LIVE]
    scr = tempfile.mkdtemp(prefix="s479_walk_")
    try:
        old = os.path.join(scr, "old"); new = os.path.join(scr, "new"); inbox = os.path.join(scr, "inbox")
        for d in (old, new, inbox):
            os.makedirs(d)
        for f in ("packs.py", "packs.html", "stmt_shelf.py", "finance_icici.py", "finance_yesbank.py", "yes_branch.py"):
            src = os.path.join(a.finance, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(old, f)); shutil.copy2(src, os.path.join(new, f))
        shutil.copy2(a.reader, os.path.join(new, "yes_monthly.py"))
        r = subprocess.run([sys.executable, "-B", a.apply] + [os.path.join(new, f) for f in ("packs.py", "finance_yesbank.py", "yes_branch.py")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check("apply on scratch", r.returncode == 0, r.stderr.decode()[-300:])
        os.environ.update(STMT_INBOX=inbox, PACKS_DIR=os.path.join(scr, "packs_store"), PACKS_ENV=os.path.join(scr, "no.env"),
                          ASSETS_UPLOADS=os.path.join(scr, "uploads"), STMT_VENV_PYTHON=sys.executable, PACKS_TODAY="2026-10-04")
        M = load(new, "yes_monthly.py", "ym_new")

        # ---- the made-up month of a pharmacy's current account
        acct = digits(15)
        upi = digits(12)
        cash1, cash2, neft, tax, imps, sip, gst, intr = (RND.randrange(100000, 9000000) for _ in range(8))
        opening = RND.randrange(50000000, 90000000)
        T = [("03-Sep-2026", "03-Sep-2026", ["CASH DEP-SELF-WALK TRAD", "ERS-WALKTOWN"], digits(12), cash1, 0),
             ("05-Sep-2026", "05-Sep-2026", ["Multiple Payee-NEFT DR-00-YES-", "" + digits(11) + "-CMS_" + digits(6) + ".TXT"], digits(6), 0, neft),
             ("15-Sep-2026", "15-Sep-2026", ["CASH DEP-SELF-WALK TRAD", "ERS-OTHERTOWN"], digits(12), cash2, 0),
             ("15-Sep-2026", "15-Sep-2026", ["NET TXN/YTPCBDTINET/" + digits(8), digits(6) + "/CBDT INET/advance tax"], digits(12), 0, tax),
             ("20-Sep-2026", "20-Sep-2026", ["IMPS/WALK TRADERS/XXX1", upi[:3] + "/RRN:" + upi + "/SOME BAN", "K LIMITED"], None, imps, 0),
             ("22-Sep-2026", "22-Sep-2026", [digits(15) + " For Mutual Fund S", "IP"], None, 0, sip),
             ("24-Sep-2026", "24-Sep-2026", ["LINE ONE OF FO", "UR, CUT AS TH", "E COLUMN END", "S, FOUR LINES"], None, 0, 111),
             ("28-Sep-2026", "28-Sep-2026", ["POS GST"], None, 0, gst),
             ("01-Oct-2026", "30-Sep-2026", ["CREDIT INTEREST CAPITAL", "ISED"], None, intr, 0)]
        text, facts = statement(acct, "WALK TRADERS", "Current Account", opening, T, break_after=5)
        p = M.parse_text(text)
        check("1 a made-up month is read: every row, the period, the opening and the closing",
              len(p["lines"]) == 9 and (p["period_from"], p["period_to"]) == ("2026-09-01", "2026-09-30") and p["opening_p"] == opening
              and p["closing_p"] == facts["closing"] and p["source"] == "monthly", p)
        check("1 the account is kept by its last four only", p["account_ref"] == acct[-4:] and acct not in repr(p))
        D = [x["description"] for x in p["lines"]]
        check("1 a two-line description is joined as it was cut (mid-word)", D[0] == "CASH DEP-SELF-WALK TRADERS-WALKTOWN" and D[2] == "CASH DEP-SELF-WALK TRADERS-OTHERTOWN", D[:3])
        check("1 a three-line description: above, on the row, below", D[4].startswith("IMPS/WALK TRADERS/XXX1") and D[4].endswith("/SOME BANK LIMITED"), D[4])
        check("1 a four-line description: two above, two below", D[6] == "LINE ONE OF FOUR, CUT AS THE COLUMN ENDS, FOUR LINES", D[6])
        check("1 a one-line description sits on its row", D[7] == "POS GST", D[7])
        check("1 the page break (the bank's foot lines, the heading again) between two rows moves no description", D[5].endswith("For Mutual Fund SIP") and D[6].startswith("LINE ONE"), D[5:7])
        check("1 long digit runs keep their last four (a description, a reference)", upi not in " ".join(D) and ("x" + upi[-4:]) in D[4]
              and all(len(x) < 11 or not x.isdigit() for x in [l["reference"] for l in p["lines"]]), [l["reference"] for l in p["lines"]])
        check("1 a reference is taken from its own column; a row without one gets a stable key", p["lines"][0]["reference"].startswith("x")
              and p["lines"][1]["reference"] == T[1][3] and p["lines"][7]["reference"] == "monthly:2026-09-01:8", [l["reference"] for l in p["lines"]])
        check("1 the cash deposits are the two cash rows and no other", [x["is_cash_deposit"] for x in p["lines"]] == [1, 0, 1, 0, 0, 0, 0, 0, 0])
        check("1 deposits and withdrawals are in their own columns", p["lines"][0]["deposit_p"] == cash1 and p["lines"][0]["withdrawal_p"] == 0
              and p["lines"][1]["withdrawal_p"] == neft and p["lines"][1]["deposit_p"] == 0)
        check("1 the interest row posted on 01-Oct with value date 30-Sep is inside September (S475's rule)", p["lines"][8]["txn_date"] == "2026-10-01" and p["lines"][8]["value_date"] == "2026-09-30")
        i = M.ident(text)
        check("1 the shelf's facts: Yes Bank, current, the tail, the period, the holder", i == dict(bank="YES", kind="current", tail=acct[-4:],
              period_from="2026-09-01", period_to="2026-09-30", holder="WALK TRADERS"), i)
        check("1 the holder is the 'Primary Holder' line, never the proprietor line", "HUF" not in M.holder(text) and "SOMEONE" not in M.holder(text))
        ts, _f = statement(digits(15), "A PERSON HUF", "Saving Account", opening, T[:2])
        check("1 a 'Saving Account' is a savings account", M.kind(ts) == "savings" and M.ident(ts)["holder"] == "A PERSON HUF")

        moved = text.replace(" " * 27 + "CASH DEP-SELF-WALK TRAD", " " * 61 + "CASH DEP-SELF-WALK TRAD", 1).replace(" " * 27 + "ERS-WALKTOWN", " " * 3 + "ERS-WALKTOWN", 1)
        pm = M.parse_text(moved)
        check("1 a description line is read wherever it starts (no column band drops it): the cash deposit stays a cash deposit",
              moved != text and pm["lines"][0]["description"] == D[0] and [x["is_cash_deposit"] for x in pm["lines"]] == [1, 0, 1, 0, 0, 0, 0, 0, 0], pm["lines"][0])
        late_foot = text.replace("\n Opening Balance:", "\n" + "\n".join(PAGEFOOT) + "\n\f\n Opening Balance:", 1)
        check("1 the totals printed on a page of their own (after a page's foot block, no heading) still end the table",
              late_foot != text and len(M.parse_text(late_foot)["lines"]) == 9)

        # ---- 2 the proofs
        bad = text.replace(inr(opening + cash1 - neft).rjust(20), inr(opening + cash1 - neft + 100).rjust(20), 1)
        ok, why = refuses(M, bad, "running balance"); check("2 a wrong running balance is refused", ok and bad != text, why)
        t2, f2 = statement(acct, "WALK TRADERS", "Current Account", opening, T[:4] + T[5:], totals=(opening, facts["deposits"], facts["withdrawals"], facts["closing"]))
        ok, why = refuses(M, t2, "closing balance"); check("2 a missing row is refused (the rows do not reach the closing)", ok, why)
        t3, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T, totals=(opening, facts["deposits"] + 100, facts["withdrawals"], facts["closing"]))
        ok, why = refuses(M, t3, "Total Deposits"); check("2 a wrong total of deposits is refused", ok, why)
        t4, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T, totals=(opening, facts["deposits"], facts["withdrawals"] - 100, facts["closing"]))
        ok, why = refuses(M, t4, "Total Withdrawals"); check("2 a wrong total of withdrawals is refused", ok, why)
        t5, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T, bf=opening + 500)
        ok, why = refuses(M, t5, "B/F row"); check("2 an opening row that is not the printed opening is refused", ok, why)
        To = T[:8] + [("02-Oct-2026", "01-Oct-2026", ["LATE ROW"], None, 5, 0)]
        t6, _ = statement(acct, "WALK TRADERS", "Current Account", opening, To)
        ok, why = refuses(M, t6, "outside the printed period"); check("2 a row outside the period by BOTH its dates is refused", ok, why)
        two = text + "\n" + text[text.index("       Statement Of Transactions"):]
        ok, why = refuses(M, two, "carries 2 accounts"); check("2 two accounts in one file are refused", ok, why)
        t7, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T, title=("01-Aug-2026", "31-Aug-2026"))
        ok, why = refuses(M, t7, "title's period"); check("2 a title whose period is not the account's is refused", ok, why)
        t8, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T, drop_foot=True)
        ok, why = refuses(M, t8, "foot line"); check("2 a statement without its foot line is refused", ok, why)
        t9, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T, extra_line_after=3)
        ok, why = refuses(M, t9, "do not pair with the rows"); check("2 a description line that pairs with no row is refused", ok, why)
        t11, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T[:7] + [("28-Sep-2026", "28-Sep-2026", [], None, 0, gst)] + T[8:])
        ok, why = refuses(M, t11, "has no description"); check("2 a row left without any description is refused (its lines were not read)", ok, why)
        t12, _ = statement(acct, "WALK TRADERS", "Current Account", opening, T[:7] + [("28-Sep-2026", "28-Sep-2026", ["NEFT-SOMEONE-", "CASH DEP-SELF"], None, gst, 0)] + T[8:])
        ok, why = refuses(M, t12, "inside its description"); check("2 'CASH DEP' that is not at the head of its row's description is refused (lines glued to the wrong row)", ok, why)
        t10 = text.replace("03-Sep-2026 03-Sep-2026 ", "03-Sep-2026 03-Sep-2026 X", 1).replace(inr(cash1).rjust(16), "".rjust(16), 1)
        ok, why = refuses(M, t10, "begins with a date"); check("2 a dated line that is not a row is refused, never skipped", ok, why)

        # ---- 3 not its layout
        branch = "STATEMENT OF ACCOUNT\nPeriod :   01-SEP-2026 To 30-SEP-2026\nA/C Number: %s\nTXN DATE VALUE DATE DESCRIPTION REFERENCE DEBITS CREDITS BALANCE\nYES TOUCH\n" % digits(15)
        netb = "YES BANK\nPeriod: 1 Sep 2026 - 20 Sep 2026\nAccount Statement\n"
        check("3 the branch's print and the net-banking download are not taken for it", not M.is_monthly(branch) and not M.is_monthly(netb) and M.is_monthly(text))
        check("3 a blob that is not a PDF is not asked about", M.is_monthly_blob(b"hello") is False and M.is_monthly_blob("text") is False)

        # ---- 4 one line once (the reader's own ingest, the shared pair's shape)
        P = load(new, "packs.py", "packs_new")
        sys.path.insert(0, new)                               # packs.py imports its readers when it needs them: from the scratch folder, as on the box
        dbp = os.path.join(scr, "finance.db")
        con = dbf(dbp)
        P.ensure(con)
        for d in ("CREATE TABLE IF NOT EXISTS clinic_day_revenue (business_date TEXT, revenue_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS upi_txn (unit TEXT, txn_date TEXT, amount_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS app_setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)",
                  "CREATE TABLE IF NOT EXISTS bank_statement_period (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, period_from TEXT NOT NULL, period_to TEXT NOT NULL,"
                  " opening_p INTEGER, closing_p INTEGER, source_file TEXT, sha256 TEXT, ingested_at TEXT, UNIQUE (account_ref, period_from, period_to))",
                  "CREATE TABLE IF NOT EXISTS bank_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, txn_date TEXT NOT NULL, value_date TEXT,"
                  " description TEXT NOT NULL, reference TEXT, withdrawal_p INTEGER NOT NULL DEFAULT 0, deposit_p INTEGER NOT NULL DEFAULT 0, balance_p INTEGER,"
                  " is_cash_deposit INTEGER NOT NULL DEFAULT 0, source_file TEXT, sha256 TEXT, ingested_at TEXT, UNIQUE (account_ref, txn_date, reference, deposit_p, withdrawal_p))"):
            con.execute(d)
        con.commit()
        texts = {}
        def blob_of(t):
            b = b"%PDF-walk " + hashlib.md5(t.encode()).hexdigest().encode() + b"\n"
            texts[b] = t
            return b
        M.pdf_text = lambda blob: texts.get(blob, "")
        A4 = acct[-4:]
        b1 = blob_of(text)
        # the net-banking download of 1 Aug - 20 Sep is on the table already: the first four rows of September, keyed its own way
        con.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, source_file, sha256) VALUES (?,?,?,?,?)", (A4, "2026-08-01", "2026-09-20", "Account_Statement.pdf", "other"))
        for k, (d, vd, pieces, ref, dep, wd) in enumerate(T[:4]):
            con.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, is_cash_deposit, source_file, sha256) VALUES (?,?,?,?,?,?,?,?,?)",
                        (A4, "2026-09-%s" % d[:2], "as the download words it", "NETBANKING-REF-%d" % k, wd, dep, 1 if "CASH" in pieces[0] else 0, "Account_Statement.pdf", "other"))
        con.commit()
        r1 = M.ingest_statement(con, "2026-10-01_ CASA_%s_monthly.pdf" % digits(12), b1)
        con.commit()
        n_sep = con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=? AND txn_date>='2026-09-01'", (A4,)).fetchone()[0]
        check("4 rows another file holds for PART of the period are not written twice: 4 held, 5 written, 9 on the table",
              r1["ok"] and r1["lines"] == 9 and r1["new_lines"] == 5 and r1["already_held"] == 4 and n_sep == 9 and not r1.get("checked_against"), (r1, n_sep))
        check("4 ... and the cash deposits of the month are counted once (2)", con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=? AND is_cash_deposit=1", (A4,)).fetchone()[0] == 2)
        check("4 the stored file name keeps no long number", all("x" in r[0] and not any(len(tok) > 9 and tok.isdigit() for tok in r[0].replace("_", " ").split())
              for r in con.execute("SELECT DISTINCT source_file FROM bank_statement_line WHERE source_file LIKE 'monthly:%'")))
        r2 = M.ingest_statement(con, "again.pdf", b1); con.commit()
        check("4 the same file again writes nothing new", r2["new_lines"] == 0 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (A4,)).fetchone()[0] == n_sep, r2)
        # a period another file COVERS (the branch's copy came first): checked, not written
        acct2 = digits(15); B4 = acct2[-4:]
        tb, fb = statement(acct2, "OTHER TRADERS", "Current Account", opening, T[:3])
        con.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, source_file, sha256) VALUES (?,?,?,?,?)", (B4, "2026-09-01", "2026-09-30", "branch:sep.pdf", "branchsha"))
        for k, (d, vd, pieces, ref, dep, wd) in enumerate(T[:3]):
            con.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, is_cash_deposit, source_file, sha256) VALUES (?,?,?,?,?,?,?,?,?)",
                        (B4, "2026-09-%s" % d[:2], "branch words", "branch:2026-09-01:%d" % k, wd, dep, 1 if "CASH" in pieces[0] else 0, "branch:sep.pdf", "branchsha"))
        con.commit()
        r3 = M.ingest_statement(con, "m.pdf", blob_of(tb)); con.commit()
        check("4 a period another file covers is CHECKED and nothing is written: agrees", r3["new_lines"] == 0 and r3.get("checked_against") == "2026-09-01..2026-09-30" and r3["agrees"] is True
              and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (B4,)).fetchone()[0] == 3, r3)
        con.execute("DELETE FROM bank_statement_line WHERE account_ref=? AND reference='branch:2026-09-01:2'", (B4,)); con.commit()
        r4 = M.ingest_statement(con, "m.pdf", blob_of(tb)); con.commit()
        check("4 ... and a held month that differs is SAID, and the row the table lacked is written (the month is never left short)",
              r4["agrees"] is False and r4["checked_against"] == "2026-09-01..2026-09-30" and "held 2 lines in the period, the monthly statement 3" in r4["differs"][0]
              and r4["new_lines"] == 1 and r4["already_held"] == 2
              and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (B4,)).fetchone()[0] == 3, r4)
        r4b = M.ingest_statement(con, "m.pdf", blob_of(tb)); con.commit()
        check("4 ... and read again it writes nothing more", r4b["new_lines"] == 0 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (B4,)).fetchone()[0] == 3, r4b)
        acct3 = digits(15)
        same = [("07-Sep-2026", "07-Sep-2026", ["SAME"], None, 500, 0), ("07-Sep-2026", "07-Sep-2026", ["SAME"], None, 500, 0)]
        tc, _ = statement(acct3, "TWIN TRADERS", "Current Account", opening, same)
        pc = M.parse_text(tc)
        check("4 two equal rows on one day get two keys (the table would have dropped one)", len({(x["txn_date"], x["reference"], x["deposit_p"], x["withdrawal_p"]) for x in pc["lines"]}) == 2, [x["reference"] for x in pc["lines"]])
        r5 = M.ingest_statement(con, "t.pdf", blob_of(tc)); con.commit()
        check("4 ... and both are stored", r5["new_lines"] == 2 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (acct3[-4:],)).fetchone()[0] == 2, r5)

        # two equal rows, and another file already holds ONE of them: counted, not merged -- one is written
        acct4 = digits(15)
        td, _ = statement(acct4, "COUNT TRADERS", "Current Account", opening, same)
        con.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, source_file, sha256) VALUES (?,?,?,?,?,?,?,?)",
                    (acct4[-4:], "2026-09-07", "the download's words", "NB-ONE", 0, 500, "Account_Statement.pdf", "other4")); con.commit()
        r6 = M.ingest_statement(con, "c.pdf", blob_of(td)); con.commit()
        check("4 two equal rows of which another file holds ONE: one is written, one is counted held (never both, never none)",
              r6["new_lines"] == 1 and r6["already_held"] == 1 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (acct4[-4:],)).fetchone()[0] == 2, r6)
        # two equal rows that also carry the SAME reference: the table's key cannot tell them apart -- the later one carries its place
        acct5 = digits(15); ref5 = digits(6)
        te, _ = statement(acct5, "KEY TRADERS", "Current Account", opening, [("07-Sep-2026", "07-Sep-2026", ["SAME"], ref5, 500, 0), ("07-Sep-2026", "07-Sep-2026", ["SAME"], ref5, 500, 0)])
        pe = M.parse_text(te)
        r7 = M.ingest_statement(con, "k.pdf", blob_of(te)); con.commit()
        check("4 two equal rows with the same reference are both stored (the second key carries its place)", [x["reference"] for x in pe["lines"]] == [ref5, ref5 + "#2"]
              and r7["new_lines"] == 2 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (acct5[-4:],)).fetchone()[0] == 2, (pe["lines"], r7))
        # the interest row the bank posts on the first of the next month: held by October's download, it is not written twice
        acct6 = digits(15); C4 = acct6[-4:]
        tf, _ = statement(acct6, "INTEREST TRADERS", "Saving Account", opening, [T[7], T[8]])
        con.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, source_file, sha256) VALUES (?,?,?,?,?)", (C4, "2026-10-01", "2026-10-10", "Account_Statement_oct.pdf", "oct"))
        con.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, source_file, sha256) VALUES (?,?,?,?,?,?,?,?)",
                    (C4, "2026-10-01", "interest, the download's words", "NB-INT", 0, intr, "Account_Statement_oct.pdf", "oct")); con.commit()
        r8 = M.ingest_statement(con, "i.pdf", blob_of(tf)); con.commit()
        check("4 a row posted on the first of the next month that October's file already holds is not written twice",
              r8["new_lines"] == 1 and r8["already_held"] == 1 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (C4,)).fetchone()[0] == 2, r8)
        # ... and a file that COVERS the month and holds that row, beside another row of 01-Oct that is October's own: agrees
        acct7 = digits(15); E4 = acct7[-4:]
        tg, _ = statement(acct7, "COVER TRADERS", "Saving Account", opening, [T[7], T[8]])
        con.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, source_file, sha256) VALUES (?,?,?,?,?)", (E4, "2026-08-01", "2026-10-31", "Account_Statement_long.pdf", "long"))
        for k, (dte, wd_, dep_) in enumerate((("2026-09-28", gst, 0), ("2026-10-01", 0, intr), ("2026-10-01", 4242, 0))):
            con.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, source_file, sha256) VALUES (?,?,?,?,?,?,?,?)",
                        (E4, dte, "the download's words", "NB-L%d" % k, wd_, dep_, "Account_Statement_long.pdf", "long"))
        con.commit()
        r9 = M.ingest_statement(con, "v.pdf", blob_of(tg)); con.commit()
        check("4 a covering file that holds the month and its next-day interest row AGREES (October's own row of that day does not count against it)",
              r9.get("agrees") is True and r9["new_lines"] == 0 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (E4,)).fetchone()[0] == 3, r9)

        # the same row held by another file WITHOUT the cash flag: the flagged row is written -- the cash check never loses a deposit
        acct8 = digits(15); F4 = acct8[-4:]
        th, _ = statement(acct8, "FLAG TRADERS", "Current Account", opening, [T[0]])
        con.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, is_cash_deposit, source_file, sha256) VALUES (?,?,?,?,?,?,?,?,?)",
                    (F4, "2026-09-03", "a layout that did not see the cash", "NB-F", 0, cash1, 0, "Account_Statement.pdf", "flag")); con.commit()
        r10 = M.ingest_statement(con, "f.pdf", blob_of(th)); con.commit()
        check("4 a row another file holds WITHOUT the cash flag does not swallow the cash deposit: the flagged row is written",
              r10["new_lines"] == 1 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=? AND is_cash_deposit=1", (F4,)).fetchone()[0] == 1, r10)
        # this file read again AFTER another file's period row came to cover the month: it is its own witness -- agrees, never 'differs'
        acct9 = digits(15); G4 = acct9[-4:]
        tk, _ = statement(acct9, "AGAIN TRADERS", "Current Account", opening, T[:3])
        M.ingest_statement(con, "g.pdf", blob_of(tk))
        con.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, source_file, sha256) VALUES (?,?,?,?,?)", (G4, "2026-09-01", "2026-10-10", "Account_Statement_later.pdf", "later")); con.commit()
        r11 = M.ingest_statement(con, "g.pdf", blob_of(tk)); con.commit()
        check("4 read again after another file's period came to cover the month, it AGREES (its own rows are the table's) and writes nothing",
              r11.get("agrees") is True and r11["new_lines"] == 0 and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (G4,)).fetchone()[0] == 3, r11)

        # ---- 4b ONE LINE ONCE ACROSS THE THREE LAYOUTS: the two older readers, new beside old
        SHARED = [d for d in (
            "CREATE TABLE IF NOT EXISTS bank_statement_period (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, period_from TEXT NOT NULL, period_to TEXT NOT NULL,"
            " opening_p INTEGER, closing_p INTEGER, source_file TEXT, sha256 TEXT, ingested_at TEXT, UNIQUE (account_ref, period_from, period_to))",
            "CREATE TABLE IF NOT EXISTS bank_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, txn_date TEXT NOT NULL, value_date TEXT,"
            " description TEXT NOT NULL, reference TEXT, withdrawal_p INTEGER NOT NULL DEFAULT 0, deposit_p INTEGER NOT NULL DEFAULT 0, balance_p INTEGER,"
            " is_cash_deposit INTEGER NOT NULL DEFAULT 0, source_file TEXT, sha256 TEXT, ingested_at TEXT, UNIQUE (account_ref, txn_date, reference, deposit_p, withdrawal_p))")]
        def fresh():
            c = sqlite3.connect(":memory:"); c.row_factory = sqlite3.Row
            P.ensure(c)
            for d in SHARED:
                c.execute(d)
            return c
        def as_other_layout(parsed, tag, upto=None):          # the same bank rows as another layout words and keys them
            L = [dict(x, reference="%s-%d" % (tag, i), description="as %s words it" % tag) for i, x in enumerate(parsed["lines"])]
            return dict(parsed, lines=(L if upto is None else L[:upto]), source=tag)
        counts = {}
        for tag, folder in (("new", new), ("old", old)):
            FY = load(folder, "finance_yesbank.py", "fy_" + tag); YB = load(folder, "yes_branch.py", "yb_" + tag)
            # (a) the month's statement first, the net-banking download of the same month afterwards -- on the shared pair
            c = fresh(); M.ingest_statement(c, "m.pdf", b1)
            FY.parse_statement = lambda blob, _p=p: as_other_layout(_p, "NB")
            ra = FY.ingest_statement(c, "Account_Statement.pdf", b"download-1", None, now="2026-10-10T10:00:00"); c.commit()
            na = c.execute("SELECT COUNT(*), SUM(is_cash_deposit) FROM bank_statement_line WHERE account_ref=?", (A4,)).fetchone()
            # (b) two net-banking downloads that overlap, no other layout on the table: exactly as before
            c = fresh()
            FY.parse_statement = lambda blob, _p=p: as_other_layout(_p, "NB", 4)
            rb1 = FY.ingest_statement(c, "Account_Statement_a.pdf", b"download-a", None, now="2026-09-20T10:00:00")
            FY.parse_statement = lambda blob, _p=p: as_other_layout(_p, "NB")
            rb2 = FY.ingest_statement(c, "Account_Statement_b.pdf", b"download-b", None, now="2026-10-10T10:00:00"); c.commit()
            nb = c.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (A4,)).fetchone()[0]
            # (c) the month's statement first, the branch's print of the same month afterwards -- on the per-account pair
            c = fresh(); M.ingest_statement(c, "m.pdf", b1, tables=P.YES_ACCOUNT_TABLES)
            YB.parse_statement = lambda blob, _p=p: as_other_layout(_p, "BR")
            rc = YB.ingest_statement(c, "branch.pdf", b"%PDF-branch", None, now="2026-10-12T10:00:00", tables=P.YES_ACCOUNT_TABLES); c.commit()
            nc = c.execute("SELECT COUNT(*) FROM yesbank_account_statement_line WHERE account_ref=?", (A4,)).fetchone()[0]
            # (d) the net-banking download first, the branch's print afterwards -- the per-account pair again
            c = fresh()
            FY.parse_statement = lambda blob, _p=p: as_other_layout(_p, "NB", 4)
            FY.ingest_statement(c, "Account_Statement_a.pdf", b"download-a", None, now="2026-09-20T10:00:00", tables=P.YES_ACCOUNT_TABLES)
            rd = YB.ingest_statement(c, "branch.pdf", b"%PDF-branch", None, now="2026-10-12T10:00:00", tables=P.YES_ACCOUNT_TABLES); c.commit()
            nd = c.execute("SELECT COUNT(*) FROM yesbank_account_statement_line WHERE account_ref=?", (A4,)).fetchone()[0]
            # (e) newest first, as the net-banking download prints: a later CASH deposit and an earlier transfer of the same amount on one
            #     day; the branch's print (cut before the deposit) holds only the transfer. The cash deposit must be the row written.
            c = fresh()
            c.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, reference, withdrawal_p, deposit_p, is_cash_deposit, source_file, sha256) VALUES (?,?,?,?,?,?,?,?,?)",
                      (A4, "2026-09-09", "transfer, the branch's words", "branch:2026-09-01:1", 0, 77700, 0, "branch:early.pdf", "br"))
            two_ = dict(account_ref=A4, period_from="2026-09-01", period_to="2026-09-30", opening_p=0, closing_p=0, source="NB", lines=[
                dict(txn_date="2026-09-09", value_date="2026-09-09", description="CASH DEP-SELF", reference="NB-CASH", withdrawal_p=0, deposit_p=77700, balance_p=0, is_cash_deposit=1),
                dict(txn_date="2026-09-09", value_date="2026-09-09", description="NEFT-SOMEONE", reference="NB-NEFT", withdrawal_p=0, deposit_p=77700, balance_p=0, is_cash_deposit=0)])
            FY.parse_statement = lambda blob, _t=two_: _t
            re_ = FY.ingest_statement(c, "Account_Statement_c.pdf", b"download-c", None, now="2026-10-10T10:00:00"); c.commit()
            ne = c.execute("SELECT COUNT(*), SUM(is_cash_deposit) FROM bank_statement_line WHERE account_ref=?", (A4,)).fetchone()
            counts[tag] = dict(e=(ne[0], ne[1], re_.get("new_lines"), re_.get("already_held")), a=(na[0], na[1], ra.get("new_lines"), ra.get("already_held")), b=(nb, rb1["new_lines"], rb2["new_lines"], rb2.get("already_held", 0)),
                               c=(nc, rc.get("new_lines"), rc.get("already_held")), d=(nd, rd.get("new_lines"), rd.get("already_held")))
        N = counts["new"]; Oc = counts["old"]
        check("4b a net-banking download read AFTER the month's statement writes no row twice: 9 on the table, 2 cash deposits, 9 held", N["a"] == (9, 2, 0, 9), N["a"])
        check("4b two overlapping net-banking downloads behave exactly as before (their own reference keys them): 4 then 5, 9 on the table", N["b"] == (9, 4, 5, 0) and Oc["b"][:3] == (9, 4, 5), (N["b"], Oc["b"]))
        check("4b the branch's print read AFTER the month's statement writes no row twice (the per-account pair)", N["c"] == (9, 0, 9), N["c"])
        check("4b the branch's print after a net-banking download of part of the month writes only the rest", N["d"] == (9, 5, 4), N["d"])
        check("4b a later cash deposit and an earlier transfer of one amount, the transfer held by another layout: the CASH DEPOSIT is the row written", N["e"] == (2, 1, 1, 1), N["e"])
        check("4b SHOWN on the two readers as they are today: the same rows go in twice (18 on the table, 4 cash deposits; 18; 13)",
              Oc["a"][:2] == (18, 4) and Oc["c"][0] == 18 and Oc["d"][0] == 13, Oc)

        # ---- 5 through the shelf
        huf_acct = digits(15)
        t_huf_sep, _ = statement(huf_acct, "MANOJ KUMAR AGARWAL HUF", "Saving Account", opening, T[5:])
        t_huf_aug, _ = statement(huf_acct, "MANOJ KUMAR AGARWAL HUF", "Saving Account", opening,
                                 [("05-Aug-2026", "05-Aug-2026", ["POS GST"], None, 0, 700)], pfrom="01-Aug-2026", pto="31-Aug-2026")
        sanj_acct = digits(15)
        t_sanj, _ = statement(sanj_acct, "SANJEEVNI MEDICOS", "Current Account", opening, T)
        check("5 packs.identify_text names the monthly layout: Yes Bank, the period, the holder's words", (lambda i: i["bank"] == "YES" and i["period_from"] == "2026-09-01"
              and i["holder"] == "SANJEEVNI MEDICOS" and i["kind"] == "current" and i["tail"] == sanj_acct[-4:] and "SANJEEVNI" in i["tokens"])(P.identify_text(t_sanj)))
        files = {}
        def shelf_file(name, t, locked=1):
            raw = os.path.join(inbox, name + ".pdf"); unl = os.path.join(inbox, name + ".unlocked.pdf")
            blob = blob_of(t)
            open(raw, "wb").write(b"%PDF-LOCKED original of " + name.encode())
            open(unl, "wb").write(blob)
            con.execute("INSERT INTO stmt_file (drive_id, name, folder, subfolder, fetched_at, local_path, unlocked_path, locked) VALUES (?,?,?,?,?,?,?,?)",
                        ("w-" + name, name + ".pdf", "bank", "", "2026-10-04T09:31:00", raw, unl if locked else None, locked))
            con.commit()
            fid = con.execute("SELECT id FROM stmt_file WHERE drive_id=?", ("w-" + name,)).fetchone()[0]
            files[unl if locked else raw] = t
            return fid
        P._file_text = lambda lp: (files.get(lp, ""), False)
        import yes_monthly as YM                              # the module packs.py itself will import -- from the scratch folder
        check("5 the reader packs.py imports is the scratch copy", os.path.dirname(os.path.abspath(YM.__file__)) == new, YM.__file__)
        YM.pdf_text = lambda blob: texts.get(blob, "")
        f_sanj = shelf_file("sanj_sep", t_sanj); f_huf = shelf_file("huf_sep", t_huf_sep); f_aug = shelf_file("huf_aug", t_huf_aug)
        # the branch gave the HUF's August already (not locked, read)
        huf_slot = con.execute("SELECT id FROM stmt_slot WHERE key='yes_sav_huf'").fetchone()[0]
        con.execute("INSERT INTO stmt_file (drive_id, name, folder, subfolder, fetched_at, slot_id, period_from, period_to, read_status, locked) VALUES (?,?,?,?,?,?,?,?,?,0)",
                    ("w-branch-aug", "HUF aug.pdf", "bank", "", "2026-09-26T05:40:00", huf_slot, "2026-08-01", "2026-08-31", "read")); con.commit()
        # a net-banking download of the first days of the month already holds the pharmacy's first row on the shared tables
        first = YM.parse_text(t_sanj)["lines"][0]
        con.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?)",
                    (sanj_acct[-4:], "2026-08-01", first["txn_date"], 0, 0, "netbank walk", "walk-netbank", "2026-09-20T10:00:00"))
        con.execute("INSERT INTO bank_statement_line (account_ref, txn_date, value_date, description, reference, withdrawal_p, deposit_p, balance_p, is_cash_deposit, source_file, sha256, ingested_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (sanj_acct[-4:], first["txn_date"], first["value_date"], "held by the download", "NB-1", first["withdrawal_p"],
                                                         first["deposit_p"], first["balance_p"], first["is_cash_deposit"], "netbank walk", "walk-netbank", "2026-09-20T10:00:00")); con.commit()
        out = P.process_inbox(con)
        rows = {r["id"]: dict(r) for r in con.execute("SELECT f.*, s.key AS slot_key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id")}
        check("5 the shelf row says what was written and what another file already held", rows[f_sanj]["matched_status"] == "9 lines: 8 new, 1 already held from another file"
              and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=? AND sha256<>'walk-netbank'", (sanj_acct[-4:],)).fetchone()[0] == 8, rows[f_sanj]["matched_status"])
        check("5 ... and a statement nobody else holds is said as before", rows[f_huf]["matched_status"] == "ingested 4 lines", rows[f_huf]["matched_status"])
        check("5 the pharmacy's statement is placed on the pharmacy's Yes Bank slot and read", rows[f_sanj]["slot_key"] == "yes_cur_sanj" and rows[f_sanj]["read_status"] == "read"
              and rows[f_sanj]["bank"] == "YES" and rows[f_sanj]["period_to"] == "2026-09-30", {k: rows[f_sanj][k] for k in ("slot_key", "read_status", "bank", "period_from", "period_to", "note")})
        check("5 the HUF's statement is placed on the HUF slot (not on the person's) and read", rows[f_huf]["slot_key"] == "yes_sav_huf" and rows[f_huf]["read_status"] == "read",
              {k: rows[f_huf][k] for k in ("slot_key", "read_status", "note")})
        check("5 a locked twin of a month the branch already gave is 'duplicate of branch copy'", rows[f_aug]["read_status"] == P.DUP_OF_BRANCH, rows[f_aug]["read_status"])
        check("5 the pharmacy's rows went to the shared tables, the HUF's to the per-account pair",
              con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (sanj_acct[-4:],)).fetchone()[0] == 9
              and con.execute("SELECT COUNT(*) FROM yesbank_account_statement_line WHERE account_ref=? AND slot_key='yes_sav_huf'", (huf_acct[-4:],)).fetchone()[0] == 4
              and con.execute("SELECT COUNT(*) FROM bank_statement_line WHERE account_ref=?", (huf_acct[-4:],)).fetchone()[0] == 0)
        cl = {c["slot"]: c for c in P.cells(con, "2026-09")}
        check("5 September's cells fill: the pharmacy's 'matched', the HUF's 'read'", cl["yes_cur_sanj"]["state"] == "matched" and cl["yes_sav_huf"]["state"] == "read"
              and cl["yes_cur_sanj"]["file"]["id"] == f_sanj, (cl["yes_cur_sanj"]["state"], cl["yes_sav_huf"]["state"]))
        check("5 the slots learned the tails from the statements", con.execute("SELECT ident_tail FROM stmt_slot WHERE key='yes_cur_sanj'").fetchone()[0] == sanj_acct[-4:])

        # ---- 6 the copy a person can open
        from flask import Flask
        app = Flask("walk479")
        P.init(app, lambda: dbf(dbp), lambda *roles, **kw: ({"user": "walk", "role": "checker", "roles": ["checker", "maker", "viewer"]}, None), unit="packs")
        c = app.test_client()
        unl_bytes = open(os.path.join(inbox, "sanj_sep.unlocked.pdf"), "rb").read()
        r = c.get("/finance/packs/file/%d" % f_sanj)
        check("6 the owner's preview hands the unlocked copy of an opened statement", r.status_code == 200 and r.data == unl_bytes, r.data[:40])
        rows_, att = P.pack_rows(con, "2026-09")
        mine = [x for x in att if x[1] == unl_bytes]
        check("6 the accountants' attachment is the unlocked copy, under a readable name", len(mine) == 1 and mine[0][0].endswith(".pdf") and "Sanjeevni" in mine[0][0]
              and not any(x[1].startswith(b"%PDF-LOCKED") for x in att if x[1]), [x[0] for x in att])
        con.execute("CREATE TABLE IF NOT EXISTS icici_fake (x)")
        ic = con.execute("SELECT id FROM stmt_slot WHERE key='icici_sanj'").fetchone()[0]
        raw_ic = os.path.join(inbox, "icici.pdf"); open(raw_ic, "wb").write(b"%PDF-NEVER-LOCKED icici")
        con.execute("INSERT INTO stmt_file (drive_id, name, folder, subfolder, fetched_at, slot_id, period_from, period_to, read_status, local_path, locked) VALUES (?,?,?,?,?,?,?,?,?,?,0)",
                    ("w-icici", "icici sep.pdf", "bank", "", "2026-10-01T05:40:00", ic, "2026-09-01", "2026-09-30", "read", raw_ic)); con.commit()
        r = c.get("/finance/amir/pack/2026-09/yes")
        check("6 Amir's pack hands the unlocked copy", r.status_code == 200 and r.data == unl_bytes, (r.status_code, r.data[:40]))
        r = c.get("/finance/amir/pack/2026-09/icici")
        check("6 a file that was never locked goes out exactly as before", r.status_code == 200 and r.data == b"%PDF-NEVER-LOCKED icici", (r.status_code, r.data[:40]))
        os.remove(os.path.join(inbox, "sanj_sep.unlocked.pdf"))
        r = c.get("/finance/packs/file/%d" % f_sanj)
        check("6 with the unlocked copy gone from the disk, the file as fetched is handed (never a 404 for a file that is there)", r.status_code == 200 and r.data.startswith(b"%PDF-LOCKED"))
        check("6 an unknown file is 404", c.get("/finance/packs/file/987654").status_code == 404)
        con.close()
        sys.path.remove(new)

        # ---- 7 SHOWN on the old packs.py
        O = load(old, "packs.py", "packs_old")
        sys.path.insert(0, old)
        io_ = O.identify_text(t_sanj)
        check("7 SHOWN: the old identifier gives the monthly statement no period", io_["period_from"] is None, io_)
        check("7 SHOWN: the old packs.py has no _best_path and no word of yes_monthly", not hasattr(O, "_best_path")
              and "yes_monthly" not in open(os.path.join(old, "packs.py"), encoding="utf-8").read())
        sys.path.remove(old)
        check("hermetic: the box's packs.py and its two readers untouched", [md5(f) for f in LIVE] == before)
    except Exception as ex:                              # noqa: BLE001 -- a walk that stops is a red walk, said in its own last line
        FAILS.append("the walk itself stopped")
        print("  FAIL the walk itself stopped: %s: %s" % (type(ex).__name__, str(ex)[:300]))
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S479 %s %d checks, %d fail" % ("GREEN" if not FAILS else "RED", CHECKS, len(FAILS)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()
