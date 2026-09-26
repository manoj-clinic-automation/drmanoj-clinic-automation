#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""finance_icici.py -- S408 (26-Sep-2026, D624). The ICICI account statement reader: the PDF through `pdftotext -layout`
into the SAME shape finance_yesbank writes (bank_statement_period / bank_statement_line, account_ref = the last four digits),
PROVEN against the statement's own opening and closing balances and every running balance (the S360 method) -- it refuses,
with a message, on any mismatch, and never half-ingests.

No ICICI statement had ever been read by this box (S281/S283 confirmed; only bank_anchor was seeded by hand from the August
closing, S377). So this reader is written against ICICI's printed layout as it is known -- Date · Particulars · Deposits ·
Withdrawals · Balance, one row per transaction, dd/mm/yyyy or dd-mm-yyyy -- and proven on a fixture in that layout. Which
column an amount belongs to is never guessed from its position: each row's amount is placed by the running balance
(previous + amount = balance -> deposit; previous - amount = balance -> withdrawal). Anything else is a refusal. The first
real statement decides; a refusal names the row.

Stdlib + pdftotext only. Read-only against every existing table except the two it fills (INSERT OR IGNORE / upsert).
"""
import datetime as dt
import hashlib
import os
import re
import subprocess
import tempfile

VERSION = "1.0"
AMT = r"-?\d{1,3}(?:,\d{2,3})*(?:\.\d{2})|-?\d+\.\d{2}"
ROW_RE = re.compile(r"^\s*(\d{2}[/-]\d{2}[/-]\d{4})\s+(.*?)\s+((?:%s)(?:\s+(?:%s))*)\s*$" % (AMT, AMT))
NUM_RE = re.compile(AMT)
PERIOD_RES = (re.compile(r"(?:statement\s+period|period)\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})\s*(?:to|-|–)\s*(\d{2}[/-]\d{2}[/-]\d{4})", re.I),
              re.compile(r"from\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})\s*(?:to|-|–)\s*(\d{2}[/-]\d{2}[/-]\d{4})", re.I))
ACCT_RES = (re.compile(r"account\s*(?:no\.?|number|#)?\s*[:\-]?\s*[Xx*]*(\d{4})\b", re.I),
            re.compile(r"\b\d{8,}(\d{4})\b"))
OPEN_RE = re.compile(r"opening\s+balance[^0-9\-]*(%s)" % AMT, re.I)
CLOSE_RE = re.compile(r"closing\s+balance[^0-9\-]*(%s)" % AMT, re.I)


class StatementRejected(Exception):
    """Refuse the file rather than half-read it (the finance_upi / finance_yesbank posture)."""


def _p(s):
    return int(round(float(str(s).replace(",", "")) * 100))


def _iso(s):
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    raise StatementRejected("cannot read a date from %r" % s)


def pdf_text(blob):
    """pdftotext -layout of a PDF's bytes; '' when the tool cannot read it."""
    d = tempfile.mkdtemp(prefix="icici_")
    try:
        p = os.path.join(d, "s.pdf")
        with open(p, "wb") as fh:
            fh.write(blob)
        r = subprocess.run(["pdftotext", "-layout", p, "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
        return r.stdout.decode("utf-8", "replace")
    except Exception:                                    # noqa: BLE001
        return ""
    finally:
        try:
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))
            os.rmdir(d)
        except OSError:
            pass


def parse_text(text):
    """The statement's text -> {account_ref, period_from, period_to, opening_p, closing_p, lines[]}; raises StatementRejected."""
    if not text or "icici" not in text.lower():
        raise StatementRejected("this text does not name ICICI Bank")
    acct = None
    for rx in ACCT_RES:
        m = rx.search(text)
        if m:
            acct = m.group(1)
            break
    if not acct:
        raise StatementRejected("no account number (or its last four digits) found")
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
                raise StatementRejected("row %s '%s': %s does not carry the balance from %s to %s"
                                        % (date, desc[:40], nums[0], _r(prev), _r(bal)))
        else:
            d0, w0 = abs(amts[0]), abs(amts[1])
            if prev + d0 - w0 == bal:
                dep, wd = d0, w0
            elif prev - d0 + w0 == bal:
                dep, wd = w0, d0
            else:
                raise StatementRejected("row %s '%s': the amounts do not carry the balance from %s to %s"
                                        % (date, desc[:40], _r(prev), _r(bal)))
        prev = bal
        ref = ""
        mref = re.search(r"\b([A-Z0-9]{10,22})\b", desc)
        if mref:
            ref = mref.group(1)
        lines.append(dict(txn_date=_iso(date), value_date=_iso(date), description=desc, reference=ref,
                          withdrawal_p=wd, deposit_p=dep, balance_p=bal,
                          is_cash_deposit=1 if (dep > 0 and re.search(r"\bCASH\s*DEP", desc, re.I)) else 0))
    if not lines:
        raise StatementRejected("no transaction rows (Date · Particulars · amounts · Balance) were found")
    if closing is not None and closing != prev:
        raise StatementRejected("the closing balance printed (%s) is not the last running balance (%s)" % (_r(closing), _r(prev)))
    if closing is None:
        closing = prev
    if not pf:
        pf, pt = lines[0]["txn_date"], lines[-1]["txn_date"]
    return dict(account_ref=acct, period_from=pf, period_to=pt, opening_p=opening, closing_p=closing, lines=lines)


def _r(p):
    return "{:,.2f}".format(p / 100.0)


def parse_statement(blob):
    return parse_text(pdf_text(blob) if isinstance(blob, bytes) and blob.lstrip()[:5] == b"%PDF-" else
                      (blob.decode("utf-8", "replace") if isinstance(blob, bytes) else blob))


def ingest_statement(con, filename, blob, now=None):
    """Parse + store one ICICI statement into bank_statement_period / bank_statement_line (finance_yesbank's shape).
    Idempotent on (account_ref, date, ref, amounts). Raises StatementRejected; never half-ingests."""
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    parsed = parse_statement(blob)
    sha = hashlib.sha256(blob if isinstance(blob, bytes) else blob.encode()).hexdigest()
    fname = re.sub(r"\d{8,}", lambda m: "..." + m.group(0)[-4:], str(filename or "icici.pdf"))[-120:]
    con.execute("CREATE TABLE IF NOT EXISTS bank_statement_period (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, period_from TEXT NOT NULL,"
                " period_to TEXT NOT NULL, opening_p INTEGER, closing_p INTEGER, source_file TEXT, sha256 TEXT, ingested_at TEXT,"
                " UNIQUE (account_ref, period_from, period_to))")
    con.execute("CREATE TABLE IF NOT EXISTS bank_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT NOT NULL, txn_date TEXT NOT NULL,"
                " value_date TEXT, description TEXT NOT NULL, reference TEXT, withdrawal_p INTEGER NOT NULL DEFAULT 0, deposit_p INTEGER NOT NULL DEFAULT 0,"
                " balance_p INTEGER, is_cash_deposit INTEGER NOT NULL DEFAULT 0, source_file TEXT, sha256 TEXT, ingested_at TEXT,"
                " UNIQUE (account_ref, txn_date, reference, deposit_p, withdrawal_p))")
    con.execute("INSERT INTO bank_statement_period (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(account_ref, period_from, period_to) DO UPDATE SET opening_p=excluded.opening_p, "
                "closing_p=excluded.closing_p, source_file=excluded.source_file, sha256=excluded.sha256, ingested_at=excluded.ingested_at",
                (parsed["account_ref"], parsed["period_from"], parsed["period_to"], parsed["opening_p"], parsed["closing_p"], fname, sha, now))
    added = 0
    for ln in parsed["lines"]:
        cur = con.execute("INSERT OR IGNORE INTO bank_statement_line (account_ref, txn_date, value_date, description, reference, withdrawal_p, "
                          "deposit_p, balance_p, is_cash_deposit, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                          (parsed["account_ref"], ln["txn_date"], ln["value_date"], ln["description"], ln["reference"], ln["withdrawal_p"],
                           ln["deposit_p"], ln["balance_p"], ln["is_cash_deposit"], fname, sha, now))
        added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    con.commit()
    return dict(ok=True, account_ref=parsed["account_ref"], period=(parsed["period_from"], parsed["period_to"]),
                lines=len(parsed["lines"]), new_lines=added, opening_p=parsed["opening_p"], closing_p=parsed["closing_p"])
