#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yes_branch.py -- S433 (28-Sep-2026, F-652). OWNER: PARENT (clinic). The Yes Bank BRANCH statement, read and proved.

The branch sends every account's month as an unlocked PDF ('STATEMENT OF ACCOUNT' ... 'Period :   01-AUG-2026 To 31-AUG-2026' ...
TXN DATE / VALUE DATE / DESCRIPTION / REFERENCE / DEBITS / CREDITS / BALANCE ... the Opening / Total Debit / Total Credit / Closing
foot). That is a different layout from the e-statement finance_yesbank.py reads (S360: 'Period: 1 Aug 2026 - 20 Sep 2026'), so the
statement shelf (packs.py, S408) could give these files no month and the Yes Bank reader refused them. This module reads the branch
layout only; finance_yesbank.py (the Sanjeevni chat's) is not touched.

It PROVES the statement before one row is stored -- the same four checks as S360: every row's running balance, the printed opening,
the printed closing, the printed debit and credit totals, and every row inside the printed period. Any failure refuses the whole file.

Same interface as finance_yesbank: parse_statement(blob) -> {account_ref (last 4 only), period_from, period_to, opening_p, closing_p,
lines[]}; ingest_statement(con, filename, blob, store_dir=None, now=None, tables=None). One difference, on purpose: when the table pair
is the SHARED bank_statement_period/_line (Sanjeevni's) and a statement already held there covers the branch period, the branch copy is
CHECKED against the lines held (date + amount) and nothing is written -- the same month read twice would otherwise double the lines.

No account number beyond its last four digits reaches a table, a log or a message: long digit runs in a narration are masked the way
finance_yesbank.mask_name masks a file name.
"""
import datetime as dt
import hashlib
import re
import shutil
import subprocess

VERSION = "S433 1.0"


class StatementRejected(ValueError):
    pass


_DATE = r"\d{2}-[A-Za-z]{3}-\d{4}"
_AMT = r"-?\d[\d,]*\.\d{2}"
PERIOD_RE = re.compile(r"Period\s*:\s*(%s)\s+To\s+(%s)" % (_DATE, _DATE), re.I)
ACCT_RE = re.compile(r"A/C\s*Number\s*:\s*(\d{6,})", re.I)
TYPE_RE = re.compile(r"A/C\s*type\s*:\s*([^\n]+)", re.I)
ROW_RE = re.compile(r"^\s{0,4}(%s)\s+(%s)\s+(.*?)\s+(%s)\s+(%s)\s+(%s)\s*$" % (_DATE, _DATE, _AMT, _AMT, _AMT))
FOOT = {"opening": re.compile(r"Opening\s+Balance\s*:\s*(%s)" % _AMT, re.I),
        "debits": re.compile(r"Total\s+Debit\s+Amt\s*:\s*(%s)" % _AMT, re.I),
        "credits": re.compile(r"Total\s+Credit\s+Amt\s*:\s*(%s)" % _AMT, re.I),
        "closing": re.compile(r"Closing\s+Balance\s*:\s*(%s)" % _AMT, re.I)}
CASH_DEP_RE = re.compile(r"\bCASH\s*DEP\b", re.I)


def _p(s):
    """'2,707,001.34' -> 270700134 (paise)."""
    s = str(s).replace(",", "").strip()
    neg = s.startswith("-")
    s = s.lstrip("-")
    rs, _, ps = s.partition(".")
    v = int(rs or 0) * 100 + int((ps + "00")[:2])
    return -v if neg else v


def _iso(s):
    return dt.datetime.strptime(s.title(), "%d-%b-%Y").date().isoformat()


def mask(s):
    """A long digit run keeps its last four: an account number never reaches a table from a narration."""
    return re.sub(r"\d{11,}", lambda m: "x" + m.group(0)[-4:], s or "")


def pdf_text(blob):
    if not shutil.which("pdftotext"):
        raise StatementRejected("pdftotext is not on this machine")
    r = subprocess.run(["pdftotext", "-layout", "-", "-"], input=blob, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return r.stdout.decode("utf-8", "replace")


def is_branch(text):
    """The branch layout: its own title, the 'Period : .. To ..' line, the A/C Number line and Yes Bank's own foot."""
    t = text or ""
    up = t.upper()
    return bool("STATEMENT OF ACCOUNT" in up and PERIOD_RE.search(t) and ACCT_RE.search(t)
                and ("YES TOUCH" in up or "YES BANK" in up) and "TXN DATE" in up)


def is_branch_blob(blob):
    if not (isinstance(blob, bytes) and blob.lstrip()[:5] == b"%PDF-"):
        return False
    try:
        return is_branch(pdf_text(blob))
    except Exception:                                    # noqa: BLE001
        return False


def holder(text):
    """The account holder as the branch prints it: the left column of the 'OD Limit' line (the line under it is the proprietor or
    the address, never the holder -- 'PROP MANOJ KUMAR AGARWAL HUF' on Sanjeevni's statement is not the HUF account)."""
    for ln in (text or "").splitlines():
        if re.search(r"\bOD\s+Limit\b", ln, re.I):
            left = re.split(r"\s{3,}", ln.strip())[0]
            if left and not re.match(r"OD\s+Limit", left, re.I):
                return left.strip()
    return ""


def kind(text):
    m = TYPE_RE.search(text or "")
    t = (m.group(1) if m else "").upper()
    t = re.split(r"\s{3,}", t.strip())[0]
    return "savings" if ("SAVINGS" in t or t.startswith("SA ")) else ("current" if t else "")


def ident(text):
    """What the shelf needs to place the file: bank, kind, tail, period, holder."""
    m = PERIOD_RE.search(text)
    a = ACCT_RE.search(text)
    return dict(bank="YES", kind=kind(text), tail=(a.group(1)[-4:] if a else ""), period_from=_iso(m.group(1)) if m else None,
                period_to=_iso(m.group(2)) if m else None, holder=holder(text))


def parse_text(text):
    if not is_branch(text):
        raise StatementRejected("this is not a Yes Bank branch statement of account")
    m = PERIOD_RE.search(text)
    pfrom, pto = _iso(m.group(1)), _iso(m.group(2))
    a = ACCT_RE.search(text)
    acct = a.group(1)[-4:]
    foot = {}
    for k, rx in FOOT.items():
        hit = rx.search(text)
        if not hit:
            raise StatementRejected("the foot has no '%s' figure, so the statement cannot be checked against itself -- refusing" % k)
        foot[k] = _p(hit.group(1))

    desc_col = None
    lines, cur, bf = [], None, None
    for raw in text.splitlines():
        if "TXN DATE" in raw.upper() and "BALANCE" in raw.upper():
            desc_col = raw.upper().index("DESCRIPTION")
            cur = None
            continue
        if desc_col is None:
            continue
        rm = ROW_RE.match(raw)
        if rm:
            middle = rm.group(3)
            parts = [p for p in re.split(r"\s{2,}", middle.strip()) if p]
            ref = None
            if len(parts) > 1 and re.fullmatch(r"[0-9A-Za-z]{6,}", parts[-1]) and re.search(r"\d{6,}", parts[-1]):
                ref = parts.pop()
            desc = " ".join(parts)
            dr, cr, bal = _p(rm.group(4)), _p(rm.group(5)), _p(rm.group(6))
            if re.match(r"B/F\b", desc):
                bf = dict(date=_iso(rm.group(1)), balance=bal)
                cur = None
                continue
            cur = dict(txn_date=_iso(rm.group(1)), value_date=_iso(rm.group(2)), description=desc, reference=ref,
                       withdrawal_p=dr, deposit_p=cr, balance_p=bal, is_cash_deposit=0)
            lines.append(cur)
            continue
        s = raw.strip()
        if not s or re.match(r"(Opening Balance|Total Debit|Total Credit|Closing Balance|\*+END)", s, re.I):
            cur = None
            continue
        lead = len(raw) - len(raw.lstrip())
        if cur is not None and abs(lead - desc_col) <= 3 and not re.search(_AMT + r"\s*$", s):
            cur["description"] = (cur["description"] + " " + s).strip()
        else:
            cur = None

    # ---- the proof: the statement checks itself, or nothing is stored -------
    if bf is not None and bf["balance"] != foot["opening"]:
        raise StatementRejected("the B/F row (%.2f) is not the printed opening balance (%.2f) -- refusing" % (bf["balance"] / 100.0, foot["opening"] / 100.0))
    bal = foot["opening"]
    for ln in lines:
        bal = bal + ln["deposit_p"] - ln["withdrawal_p"]
        if bal != ln["balance_p"]:
            raise StatementRejected("the running balance does not add up at the row dated %s (%.2f expected, %.2f printed) -- refusing the whole file"
                                    % (ln["txn_date"], bal / 100.0, ln["balance_p"] / 100.0))
    if bal != foot["closing"]:
        raise StatementRejected("the rows do not reach the printed closing balance (%.2f vs %.2f) -- a row is missing; refusing" % (bal / 100.0, foot["closing"] / 100.0))
    if sum(x["withdrawal_p"] for x in lines) != foot["debits"]:
        raise StatementRejected("the rows do not add up to the printed Total Debit Amt -- refusing")
    if sum(x["deposit_p"] for x in lines) != foot["credits"]:
        raise StatementRejected("the rows do not add up to the printed Total Credit Amt -- refusing")
    for i, ln in enumerate(lines, 1):
        if ln["txn_date"] < pfrom or ln["txn_date"] > pto:
            raise StatementRejected("a row dated %s falls outside the printed period %s to %s -- refusing" % (ln["txn_date"], pfrom, pto))
        ln["description"] = mask(ln["description"])
        ln["reference"] = mask(ln["reference"]) if ln["reference"] else "branch:%s:%d" % (pfrom, i)   # a stable key: the table is UNIQUE on it
        ln["is_cash_deposit"] = 1 if (ln["deposit_p"] > 0 and CASH_DEP_RE.search(ln["description"])) else 0
    return dict(account_ref=acct, period_from=pfrom, period_to=pto, opening_p=foot["opening"], closing_p=foot["closing"],
                lines=lines, source="branch")


def parse_statement(blob):
    if not (isinstance(blob, bytes) and blob.lstrip()[:5] == b"%PDF-"):
        raise StatementRejected("a branch statement is a PDF")
    return parse_text(pdf_text(blob))


def _mask_name(name):
    return re.sub(r"\d{6,}", lambda m: "x" + m.group(0)[-4:], name or "yes_branch.pdf")


def ingest_statement(con, filename, blob, store_dir=None, now=None, tables=None):
    """Parse, prove, store. Idempotent (the line key includes a stable reference). On the SHARED pair, a period already covered by a
    statement held there is CHECKED, not written (see the module note)."""
    ptab, ltab = tables or ("bank_statement_period", "bank_statement_line")
    if not (re.match(r"^[a-z_]+$", ptab) and re.match(r"^[a-z_]+$", ltab)):
        raise StatementRejected("the table pair must be plain identifiers")
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    filename = _mask_name(filename)
    parsed = parse_statement(blob)
    sha = hashlib.sha256(blob).hexdigest()
    acct, pf, pt = parsed["account_ref"], parsed["period_from"], parsed["period_to"]
    base = dict(ok=True, account_ref=acct, period=(pf, pt), lines=len(parsed["lines"]), closing_p=parsed["closing_p"],
                closing_printed=True, layout="branch", sha256=sha[:12])
    if ptab == "bank_statement_period":
        held = con.execute("SELECT period_from, period_to FROM bank_statement_period WHERE account_ref=? AND period_from<=? AND period_to>=? "
                           "AND COALESCE(source_file,'') NOT LIKE '%branch%' LIMIT 1", (acct, pf, pt)).fetchone()
        if held:
            have = sorted((r[0], r[1], r[2]) for r in con.execute(
                "SELECT txn_date, withdrawal_p, deposit_p FROM bank_statement_line WHERE account_ref=? AND txn_date BETWEEN ? AND ?", (acct, pf, pt)))
            want = sorted((x["txn_date"], x["withdrawal_p"], x["deposit_p"]) for x in parsed["lines"])
            base.update(new_lines=0, checked_against="%s..%s" % (held[0], held[1]), agrees=(have == want),
                        differs=([] if have == want else ["held %d lines, the branch copy %d" % (len(have), len(want))]))
            return base
    con.execute("INSERT INTO " + ptab + " (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(account_ref, period_from, period_to) DO UPDATE SET opening_p=excluded.opening_p, "
                "closing_p=excluded.closing_p, source_file=excluded.source_file, sha256=excluded.sha256, ingested_at=excluded.ingested_at",
                (acct, pf, pt, parsed["opening_p"], parsed["closing_p"], "branch:" + filename, sha, now))
    added = 0
    for ln in parsed["lines"]:
        cur = con.execute("INSERT OR IGNORE INTO " + ltab + " (account_ref, txn_date, value_date, description, reference, withdrawal_p, deposit_p, "
                          "balance_p, is_cash_deposit, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                          (acct, ln["txn_date"], ln["value_date"], ln["description"], ln["reference"], ln["withdrawal_p"], ln["deposit_p"],
                           ln["balance_p"], ln["is_cash_deposit"], "branch:" + filename, sha, now))
        added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    base.update(new_lines=added)
    return base


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        with open(p, "rb") as fh:
            b = fh.read()
        try:
            r = parse_statement(b)
            print("%s  OK  ...%s  %s..%s  %d lines  opening %.2f  closing %.2f  holder=%r kind=%s"
                  % (_mask_name(p.rsplit("/", 1)[-1]), r["account_ref"], r["period_from"], r["period_to"], len(r["lines"]),
                     r["opening_p"] / 100.0, r["closing_p"] / 100.0, holder(pdf_text(b)), kind(pdf_text(b))))
        except StatementRejected as ex:
            print("%s  REFUSED  %s" % (p, ex))
