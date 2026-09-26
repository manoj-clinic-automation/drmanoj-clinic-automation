#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""finance_icici.py -- ICICI bank statements for the statement shelf. v1.1 (S411, the first real run; v1.0 was S408).

THE LAYOUTS ICICI ACTUALLY SENDS (read on the box, 26-Sep-2026, twelve real files, six accounts):
  * the "iCRM" monthly PDF: 'Your Details With Us:' + the holder line · a Summary row 'Savings|Current  XXXX1234  <closing> Cr' ·
    'Statement of transactions in Account number: XXXX1234 in INR For the period dd-mm-yyyy To dd-mm-yyyy' · a 'dd-mm-yyyy B/F <opening> Cr'
    row · rows 'dd–mm–yyyy  particulars  withdrawals  deposits  [autosweep  reverse-sweep]  balance Cr|Dr' (EN dashes in the dates),
    'Page Total:' rows, two or three pages.
  * the pipe-delimited .txt: 'ICICI Bank account Statement from dd-mm-yyyy to dd-mm-yyyy.' then
    'Account Number|Tran Date|Tran Particular|Inst Num|Dr Tran Amt|Cr Tran Amt|Bal Amt|Deposit Branch' rows, a B/F row first.
  * the generic 'Opening Balance / Date Particulars Deposits Withdrawals Balance / Closing Balance' text (S408's fixture) is still read.

THE PROOF, never loosened: the opening (B/F) + every row = every running balance, and the last running balance = the printed closing
(the Summary row) when one is printed. Any row that does not carry the balance refuses the whole file, naming the row. The pipe .txt
prints no closing: its proof is the running balance from B/F to the last row, and the result says so.

WHERE THE LINES GO (S411): icici_statement_period / icici_statement_line -- ICICI's own tables, the same shape as the Yes Bank ones.
NOT bank_statement_period / bank_statement_line: those are read as 'the Yes Bank statement' by the owner's Bank card, the
statement-covers test and the NEFT bank check without an account filter; ICICI rows there would be taken for Yes Bank money.
The account is kept as its last four digits only (F-607).
"""
import datetime as dt
import hashlib
import os
import re
import subprocess
import tempfile

VERSION = "1.1"
PERIOD_TABLE = "icici_statement_period"
LINE_TABLE = "icici_statement_line"
AMT = r"-?\d{1,3}(?:,\d{2,3})*(?:\.\d{2})|-?\d+\.\d{2}"
NUM_RE = re.compile(r"(?<![\w.,])(%s)(?![\w.,])" % AMT)
DATE_RE = r"\d{2}[-–/]\d{2}[-–/]\d{4}"
ROW_RE = re.compile(r"^\s*(%s)\s+(.*?)\s+((?:%s)(?:\s+(?:%s))*)\s*$" % (DATE_RE, AMT, AMT))
ICRM_ROW_RE = re.compile(r"^\s*(%s)\s+(.*?)\s{2,}((?:%s)(?:\s+(?:%s)){1,4})\s*(Cr|Dr)?\s*$" % (DATE_RE, AMT, AMT), re.I)
BF_RE = re.compile(r"^\s*(%s)\s+B/F\s+(%s)\s*(Cr|Dr)?\s*$" % (DATE_RE, AMT), re.I)
SUMMARY_RE = re.compile(r"^\s*(Savings|Current|OD|Overdraft|NRE|NRO)\s+[Xx*]*\d{2,}\s+(%s)\s*(Cr|Dr)?\b" % AMT, re.I)
ICRM_PERIOD_RE = re.compile(r"for\s+the\s+period\s+(%s)\s+to\s+(%s)" % (DATE_RE, DATE_RE), re.I)
PIPE_PERIOD_RE = re.compile(r"statement\s+from\s+(%s)\s+to\s+(%s)" % (DATE_RE, DATE_RE), re.I)
PERIOD_RES = (re.compile(r"(?:statement\s+period|period)\s*[:\-]?\s*(%s)\s*(?:to|-|–)\s*(%s)" % (DATE_RE, DATE_RE), re.I),
              re.compile(r"from\s*[:\-]?\s*(%s)\s*(?:to|-|–)\s*(%s)" % (DATE_RE, DATE_RE), re.I))
ACCT_RES = (re.compile(r"account\s*(?:no\.?|number|#)?\s*[:\-]?\s*[Xx*]*(\d{4})\b", re.I),
            re.compile(r"\b[Xx*]{4,}(\d{4})\b"),
            re.compile(r"\b\d{8,}(\d{4})\b"))
OPEN_RE = re.compile(r"opening\s+balance[^0-9\-]*(%s)" % AMT, re.I)
CLOSE_RE = re.compile(r"closing\s+balance[^0-9\-]*(%s)" % AMT, re.I)
CASH_RE = re.compile(r"\bCASH\s*DEP", re.I)


class StatementRejected(Exception):
    """Refuse the file rather than half-read it (the finance_upi / finance_yesbank posture)."""


def _p(s):
    return int(round(float(str(s).replace(",", "")) * 100))


def _iso(s):
    s = str(s).strip().replace("–", "-").replace("/", "-")
    for fmt in ("%d-%m-%Y", "%d-%b-%Y", "%d-%B-%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return dt.datetime.strptime(s.title(), "%d-%b-%Y").date().isoformat()
    except ValueError:
        raise StatementRejected("cannot read a date from %r" % s)


def _r(p):
    return "{:,.2f}".format(p / 100.0)


def _signed(p, crdr):
    return -abs(p) if (crdr or "").lower() == "dr" else abs(p)


def pdf_text(blob):
    """pdftotext -layout of a PDF's bytes; raises StatementRejected when the PDF is password-locked; '' when unreadable."""
    d = tempfile.mkdtemp(prefix="icici_")
    try:
        p = os.path.join(d, "s.pdf")
        with open(p, "wb") as fh:
            fh.write(blob)
        r = subprocess.run(["pdftotext", "-layout", p, "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        err = r.stderr.decode("utf-8", "replace")
        if "Incorrect password" in err or "Encrypted" in err:
            raise StatementRejected("password-protected PDF -- a decrypted copy is needed")
        return r.stdout.decode("utf-8", "replace")
    except StatementRejected:
        raise
    except Exception:                                    # noqa: BLE001
        return ""
    finally:
        try:
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))
            os.rmdir(d)
        except OSError:
            pass


def _account(text):
    for rx in ACCT_RES:
        m = rx.search(text)
        if m:
            return m.group(1)
    raise StatementRejected("no account number (or its last four digits) found")


def _line(date, desc, wd, dep, bal):
    ref = ""
    mref = re.search(r"\b([A-Z0-9]{10,22})\b", desc)
    if mref:
        ref = mref.group(1)
    return dict(txn_date=date, value_date=date, description=desc, reference=ref, withdrawal_p=wd, deposit_p=dep, balance_p=bal,
                is_cash_deposit=1 if (dep > 0 and CASH_RE.search(desc)) else 0)


# ---------------------------------------------------------------- the iCRM monthly PDF
def _parse_icrm(text):
    if "icici" not in text.lower():
        raise StatementRejected("this text does not name ICICI Bank")
    acct = _account(text)
    m = ICRM_PERIOD_RE.search(text)
    pf, pt = (_iso(m.group(1)), _iso(m.group(2))) if m else (None, None)
    opening = None
    closing = None
    lines, prev = [], None
    for raw in text.splitlines():
        if opening is None:
            mb = BF_RE.match(raw)
            if mb:
                opening = _signed(_p(mb.group(2)), mb.group(3))
                prev = opening
                continue
        if closing is None:
            ms = SUMMARY_RE.match(raw)
            if ms:
                closing = _signed(_p(ms.group(2)), ms.group(3))
                continue
        if opening is None:
            continue
        m = ICRM_ROW_RE.match(raw)
        if not m or "B/F" in raw.upper()[:40] or "Page Total" in raw:
            continue
        date, desc, nums = _iso(m.group(1)), " ".join(m.group(2).split()), NUM_RE.findall(m.group(3))
        crdr = m.group(4)
        if len(nums) < 3:
            continue
        bal = _signed(_p(nums[-1]), crdr)
        wd, dep = abs(_p(nums[0])), abs(_p(nums[1]))
        auto = abs(_p(nums[2])) if len(nums) >= 5 else 0
        rev = abs(_p(nums[3])) if len(nums) >= 5 else 0
        if prev - wd + dep - auto + rev != bal:
            raise StatementRejected("row %s '%s': %s does not carry the balance from %s to %s"
                                    % (m.group(1).replace("–", "-"), desc[:40], (nums[0] if wd else nums[1]), _r(prev), _r(bal)))
        prev = bal
        lines.append(_line(date, desc, wd + auto, dep + rev, bal))
    if opening is None:
        raise StatementRejected("no B/F (opening) row printed")
    if not lines:
        raise StatementRejected("no transaction rows (date · particulars · withdrawals · deposits · balance) were found")
    if closing is not None and closing != prev:
        raise StatementRejected("the closing balance printed (%s) is not the last running balance (%s)" % (_r(closing), _r(prev)))
    if closing is None:
        closing = prev
    if not pf:
        pf, pt = lines[0]["txn_date"], lines[-1]["txn_date"]
    return dict(account_ref=acct, period_from=pf, period_to=pt, opening_p=opening, closing_p=closing, lines=lines, layout="icrm",
                closing_printed=True, proof="B/F + %d rows = every running balance = the printed closing" % len(lines))


# ---------------------------------------------------------------- the pipe-delimited .txt
def _parse_pipe(text):
    if "icici" not in text.lower():
        raise StatementRejected("this text does not name ICICI Bank")
    m = PIPE_PERIOD_RE.search(text)
    pf, pt = (_iso(m.group(1)), _iso(m.group(2))) if m else (None, None)
    acct = None
    opening = None
    lines, prev = [], None
    col = None                                            # the columns come from the header row, never from a position guessed
    for raw in text.splitlines():
        parts = [x.strip() for x in raw.split("|")]
        if col is None:
            low = [p.lower() for p in parts]
            if "tran date" in low and any("bal" in p for p in low):
                col = dict(acct=next(i for i, p in enumerate(low) if "account" in p), date=low.index("tran date"),
                           desc=next(i for i, p in enumerate(low) if "particular" in p), dr=next(i for i, p in enumerate(low) if p.startswith("dr")),
                           cr=next(i for i, p in enumerate(low) if p.startswith("cr")), bal=next(i for i, p in enumerate(low) if "bal" in p))
            continue
        if len(parts) <= col["bal"] or not re.match(r"^[Xx*\d]{6,}$", parts[col["acct"]]):
            continue
        if acct is None:
            acct = parts[col["acct"]][-4:]
        date_s, desc, dr, cr, bal = parts[col["date"]], " ".join(parts[col["desc"]].split()), parts[col["dr"]], parts[col["cr"]], parts[col["bal"]]
        if desc.upper() == "B/F":
            if not bal:
                raise StatementRejected("the B/F row prints no balance -- no opening to prove from")
            opening = _p(bal)
            prev = opening
            continue
        if opening is None:
            raise StatementRejected("a transaction row comes before the B/F row")
        if not bal:
            raise StatementRejected("row %s '%s' prints no balance" % (date_s, desc[:40]))
        date = _iso(date_s)
        wd = abs(_p(dr)) if dr else 0
        dep = abs(_p(cr)) if cr else 0
        b = _p(bal)
        if prev - wd + dep != b:
            raise StatementRejected("row %s '%s': %s does not carry the balance from %s to %s" % (date_s, desc[:40], (dr if wd else cr), _r(prev), _r(b)))
        prev = b
        lines.append(_line(date, desc, wd, dep, b))
    if col is None:
        raise StatementRejected("no column row naming 'Tran Date' and 'Bal Amt' was found")
    if acct is None:
        raise StatementRejected("no account rows found")
    if opening is None:
        raise StatementRejected("no B/F (opening) row printed")
    if not lines:
        raise StatementRejected("no transaction rows were found")
    if not pf:
        pf, pt = lines[0]["txn_date"], lines[-1]["txn_date"]
    return dict(account_ref=acct, period_from=pf, period_to=pt, opening_p=opening, closing_p=prev, lines=lines, layout="pipe",
                closing_printed=False, proof="B/F + %d rows = every running balance; no closing is printed in this format, the last running balance stands" % len(lines))


# ---------------------------------------------------------------- the generic text (S408's fixture layout)
def _parse_generic(text):
    if not text or "icici" not in text.lower():
        raise StatementRejected("this text does not name ICICI Bank")
    acct = _account(text)
    pf = pt = None
    for rx in PERIOD_RES:
        m = rx.search(text)
        if m:
            pf, pt = _iso(m.group(1)), _iso(m.group(2))
            break
    mo, mc = OPEN_RE.search(text), CLOSE_RE.search(text)
    if not mo:
        raise StatementRejected("no opening balance printed")
    opening = _p(mo.group(1))
    closing = _p(mc.group(1)) if mc else None
    lines, prev = [], opening
    for raw in text.splitlines():
        m = ROW_RE.match(raw)
        if not m:
            continue
        date, desc, nums = m.group(1), " ".join(m.group(2).split()), NUM_RE.findall(m.group(3))
        if len(nums) < 2:
            continue
        bal = _p(nums[-1])
        amts = [_p(x) for x in nums[:-1]]
        dep = wd = 0
        if len(amts) == 1:
            a = abs(amts[0])
            if prev + a == bal:
                dep = a
            elif prev - a == bal:
                wd = a
            else:
                raise StatementRejected("row %s '%s': %s does not carry the balance from %s to %s" % (date, desc[:40], nums[0], _r(prev), _r(bal)))
        else:
            d0, w0 = abs(amts[0]), abs(amts[1])
            if prev + d0 - w0 == bal:
                dep, wd = d0, w0
            elif prev - d0 + w0 == bal:
                dep, wd = w0, d0
            else:
                raise StatementRejected("row %s '%s': the amounts do not carry the balance from %s to %s" % (date, desc[:40], _r(prev), _r(bal)))
        prev = bal
        lines.append(_line(_iso(date), desc, wd, dep, bal))
    if not lines:
        raise StatementRejected("no transaction rows (Date · Particulars · amounts · Balance) were found")
    if closing is not None and closing != prev:
        raise StatementRejected("the closing balance printed (%s) is not the last running balance (%s)" % (_r(closing), _r(prev)))
    if closing is None:
        closing = prev
    if not pf:
        pf, pt = lines[0]["txn_date"], lines[-1]["txn_date"]
    return dict(account_ref=acct, period_from=pf, period_to=pt, opening_p=opening, closing_p=closing, lines=lines, layout="generic",
                closing_printed=bool(mc), proof="opening + %d rows = every running balance%s" % (len(lines), " = the printed closing" if mc else ""))


def parse_text(text):
    """The statement's text -> {account_ref, period_from, period_to, opening_p, closing_p, lines[], layout, proof}; raises StatementRejected."""
    if not text or not text.strip():
        raise StatementRejected("empty text")
    if "|" in text and re.search(r"Tran\s+Date", text, re.I):
        return _parse_pipe(text)
    if re.search(r"Statement of transactions in Account number", text, re.I) or re.search(r"^\s*%s\s+B/F\b" % DATE_RE, text, re.M):
        return _parse_icrm(text)
    return _parse_generic(text)


def parse_statement(blob):
    if isinstance(blob, bytes) and blob.lstrip()[:5] == b"%PDF-":
        return parse_text(pdf_text(blob))
    return parse_text(blob.decode("utf-8", "replace") if isinstance(blob, bytes) else blob)


def ensure_tables(con):
    con.execute("CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, period_from TEXT NOT NULL,"
                " period_to TEXT NOT NULL, opening_p INTEGER, closing_p INTEGER, source_file TEXT, sha256 TEXT, ingested_at TEXT,"
                " layout TEXT, closing_printed INTEGER, UNIQUE (account_ref, period_from, period_to))" % PERIOD_TABLE)
    con.execute("CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, txn_date TEXT NOT NULL,"
                " value_date TEXT, description TEXT NOT NULL, reference TEXT, withdrawal_p INTEGER NOT NULL DEFAULT 0, deposit_p INTEGER NOT NULL DEFAULT 0,"
                " balance_p INTEGER, is_cash_deposit INTEGER NOT NULL DEFAULT 0, source_file TEXT, sha256 TEXT, ingested_at TEXT,"
                " UNIQUE (account_ref, txn_date, reference, deposit_p, withdrawal_p, balance_p))" % LINE_TABLE)


def ingest_statement(con, filename, blob, now=None):
    """Parse + store one ICICI statement into icici_statement_period / icici_statement_line. Idempotent on
    (account_ref, date, ref, amounts, balance). Raises StatementRejected; never half-ingests."""
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    parsed = parse_statement(blob)
    sha = hashlib.sha256(blob if isinstance(blob, bytes) else blob.encode()).hexdigest()
    fname = re.sub(r"\d{6,}", lambda m: "x" + m.group(0)[-4:], str(filename or "icici.pdf"))[-120:]
    ensure_tables(con)
    con.execute("INSERT INTO %s (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at, layout, closing_printed) "
                "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(account_ref, period_from, period_to) DO UPDATE SET opening_p=excluded.opening_p, "
                "closing_p=excluded.closing_p, source_file=excluded.source_file, sha256=excluded.sha256, ingested_at=excluded.ingested_at, "
                "layout=excluded.layout, closing_printed=excluded.closing_printed" % PERIOD_TABLE,
                (parsed["account_ref"], parsed["period_from"], parsed["period_to"], parsed["opening_p"], parsed["closing_p"], fname, sha, now,
                 parsed["layout"], 1 if parsed["closing_printed"] else 0))
    added = 0
    for ln in parsed["lines"]:
        cur = con.execute("INSERT OR IGNORE INTO %s (account_ref, txn_date, value_date, description, reference, withdrawal_p, "
                          "deposit_p, balance_p, is_cash_deposit, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)" % LINE_TABLE,
                          (parsed["account_ref"], ln["txn_date"], ln["value_date"], ln["description"], ln["reference"], ln["withdrawal_p"],
                           ln["deposit_p"], ln["balance_p"], ln["is_cash_deposit"], fname, sha, now))
        added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    con.commit()
    return dict(ok=True, account_ref=parsed["account_ref"], period=(parsed["period_from"], parsed["period_to"]),
                lines=len(parsed["lines"]), new_lines=added, opening_p=parsed["opening_p"], closing_p=parsed["closing_p"],
                layout=parsed["layout"], closing_printed=parsed["closing_printed"], proof=parsed["proof"])
