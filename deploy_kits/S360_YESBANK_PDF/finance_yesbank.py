#!/usr/bin/env python3
# =============================================================================
#  finance_yesbank.py  ·  v1.1  ·  Session 186, PDF reader Session 280 (S360, F-603)
#
#  THE GAP THIS CLOSES (F-103), AND WHY IT IS NOT THEORETICAL (F-112)
#  -----------------------------------------------------------------
#  finance_upi.py reconciles what the app was told against what ICICI settled.
#  Nothing did the same for CASH. So cash deposits were booked from a human
#  reading of a statement, and at S184 one of them -- 13 Aug Rs 75,000 -- was
#  booked although the record itself said "falls after the statement cutoff,
#  check when booking". It had never happened. It sat in the live books until a
#  statement was pulled by hand at S186.
#
#  This module makes that impossible to repeat, in BOTH directions:
#
#     deposit_not_in_bank      we booked a deposit the bank never received
#                              <- exactly F-112
#     bank_deposit_not_booked  the bank received cash we never recorded
#                              <- exactly the S183 problem, 16 deposits missing
#
#  AND IT REFUSES TO BE SILENT ABOUT WHAT IT CANNOT SEE. A booked deposit on a
#  date no statement covers is NOT "fine" -- it is UNEVIDENCED, reported every
#  run and never counted as a pass. That is the whole of F-112 in one rule, and
#  it is D166 / F-99 applied here: the correct entry is sometimes UNKNOWN.
#
#  Mirrors finance_upi.py deliberately: parse -> ingest -> reconcile -> selftest,
#  same exception vocabulary, same "the bank is the arbiter" posture.
#
#  Stdlib only. No network. Read-only against every existing table.
# =============================================================================

import csv
import datetime as dt
import hashlib
import io
import os
import re

VERSION = "1.1"

# 'CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY'
CASH_DEP_RE = re.compile(r"\bCASH\s*DEP\b", re.I)
AMOUNT_RE = re.compile(r"-?[\d,]+\.?\d*")


class StatementRejected(Exception):
    """Refuse the file rather than half-read it (the finance_upi.py posture)."""


def _p(v):
    """A rupee string to paise. Blank/absent -> 0. Never silently rounds."""
    if v is None:
        return 0
    s = str(v).strip().replace("INR", "").replace(",", "").strip()
    if not s or s in ("-", "--"):
        return 0
    m = AMOUNT_RE.search(s)
    if not m:
        raise StatementRejected("cannot read an amount from %r" % v)
    return int(round(float(m.group(0).replace(",", "")) * 100))


def _iso(v):
    """The bank writes ISO already; accept dd/mm/yyyy and dd-Mon-yyyy too.
    A date this cannot read STOPS the parse -- a mis-parsed date silently
    reconciles the wrong day, which is worse than a refusal (F-78)."""
    s = str(v or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%b-%Y", "%d %b %Y", "%d-%B-%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    raise StatementRejected("cannot read a date from %r" % v)


def parse_statement(blob):
    """Parse a Yes Bank statement -- the PDF (v1.1) or a CSV export -- into lines
    + the period it covers.

    Returns {account_ref, period_from, period_to, opening_p, closing_p, lines[]}.
    account_ref is stored LAST-4 ONLY -- the full number never enters the
    database or a log (the project's masking rule)."""
    if isinstance(blob, bytes) and blob.lstrip()[:5] == b"%PDF-":
        return parse_pdf(blob)
    if isinstance(blob, bytes):
        try:
            text = blob.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = blob.decode("latin-1")
    else:
        text = blob

    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise StatementRejected("empty file")

    acct, pfrom, pto, opening_p, closing_p = None, None, None, None, None
    header_at = None
    for i, r in enumerate(rows):
        cells = [(c or "").strip() for c in r]
        joined = ",".join(cells)
        if acct is None and cells and re.match(r"^\d{6,}$", cells[0].replace(" ", "")):
            acct = cells[0].replace(" ", "")
        if cells and cells[0].lower().startswith("statement period"):
            try:
                pfrom, pto = _iso(cells[1]), _iso(cells[3])
            except (IndexError, StatementRejected):
                raise StatementRejected("statement period row is unreadable: %r" % joined[:90])
        if cells and cells[0].lower().startswith("opening balance"):
            opening_p = _p(cells[1])
        if cells and cells[0].lower().startswith("closing balance"):
            closing_p = _p(cells[1])
        low = [c.lower() for c in cells]
        if "transaction date" in low and any("deposit" in c for c in low):
            header_at = i
            break

    if header_at is None:
        raise StatementRejected("this file has no row naming the columns 'Transaction Date' and "
                                "'Deposits' -- it is not a Yes Bank statement. Load the statement "
                                "PDF or CSV downloaded from Yes Bank net banking")
    if not pfrom or not pto:
        raise StatementRejected("this CSV has no 'Statement Period' line, so it does not say which "
                                "dates it covers (Yes Bank's transaction download never does). "
                                "Load the statement PDF for the same dates instead -- it prints "
                                "the period and its totals, and is checked against them. "
                                "(A reconciler that does not know what it has NOT seen would "
                                "call a missing deposit fine -- F-112.)")

    hdr = [(c or "").strip().lower() for c in rows[header_at]]
    def col(*names):
        for n in names:
            if n in hdr:
                return hdr.index(n)
        return None
    c_txn, c_val = col("transaction date"), col("value date")
    c_desc, c_ref = col("description"), col("reference number", "cheque no/reference no",
                                             "reference no", "cheque no/ref no")
    c_wd, c_dep = col("withdrawals", "withdrawal"), col("deposits", "deposit")
    c_bal = col("running balance", "balance")
    if c_txn is None or c_desc is None or c_dep is None:
        raise StatementRejected("the column row is missing one of 'Transaction Date', "
                                "'Description', 'Deposits' -- not a Yes Bank statement layout this "
                                "reader knows")

    lines = []
    for r in rows[header_at + 1:]:
        cells = [(c or "").strip() for c in r]
        if not any(cells):
            continue
        if len(cells) <= c_desc:
            continue
        try:
            iso = _iso(cells[c_txn])
        except StatementRejected:
            continue                      # trailing notes / totals, not a txn row
        desc = cells[c_desc]
        dep_p = _p(cells[c_dep]) if c_dep is not None and len(cells) > c_dep else 0
        wd_p = _p(cells[c_wd]) if c_wd is not None and len(cells) > c_wd else 0
        lines.append(dict(
            txn_date=iso,
            value_date=(_iso(cells[c_val]) if c_val is not None and len(cells) > c_val
                        and cells[c_val] else None),
            description=desc,
            reference=(cells[c_ref].strip() if c_ref is not None and len(cells) > c_ref else None),
            withdrawal_p=wd_p,
            deposit_p=dep_p,
            balance_p=(_p(cells[c_bal]) if c_bal is not None and len(cells) > c_bal else None),
            is_cash_deposit=1 if (dep_p > 0 and CASH_DEP_RE.search(desc)) else 0,
        ))

    if not lines:
        raise StatementRejected("the column row is there but no transaction row under it has "
                                "a readable date")

    return dict(account_ref=(acct or "unknown")[-4:], period_from=pfrom, period_to=pto,
                opening_p=opening_p, closing_p=closing_p, lines=lines)


# =============================================================================
#  v1.1 · Session 280 · kit S360_YESBANK_PDF · F-603
#  THE STATEMENT PDF. Yes Bank's own statement PDF carries everything the CSV
#  download lacks: the period it covers, and the opening / total / closing
#  figures. That makes it the better evidence -- and it lets the reader PROVE
#  ITSELF before one row is stored (the F-536 rule: a reader that cannot fail
#  is not a reader):
#     1. every row's running balance = the older row's balance + deposit - withdrawal
#     2. the oldest row starts from the stated opening balance
#     3. the newest row's balance is the stated closing balance
#     4. the rows add up to the stated total withdrawals and total deposits
#  Any one of these failing refuses the whole file, and the message names it.
#  Text layer only (pdftotext -layout). A scan or a photo has no text layer and
#  is refused loudly -- never guessed at, never OCR'd.
# =============================================================================

import shutil
import subprocess

_MON = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
_PDF_ROW_RE = re.compile(r"^\s{0,6}(\d{1,2} %s \d{4})\s+(\d{1,2} %s \d{4})\s+(.*)$" % (_MON, _MON))
_PDF_AMT_RE = re.compile(r"(?<![\w.,/-])(\d{1,3}(?:,\d{2,3})*\.\d{2})(?![\w.,/-])")
_PDF_PERIOD_RE = re.compile(r"Period:\s*(\d{1,2} %s \d{4})\s*-\s*(\d{1,2} %s \d{4})" % (_MON, _MON))
_PDF_ACCT_RE = re.compile(r"Statement of account:\s*(\d{6,})")
_PDF_TOTAL_RE = {
    "opening": re.compile(r"Opening Balance:\s*(-?[\d,]+\.\d{2})"),
    "withdrawals": re.compile(r"Total Withdrawals:\s*(-?[\d,]+\.\d{2})"),
    "deposits": re.compile(r"Total Deposits:\s*(-?[\d,]+\.\d{2})"),
    "closing": re.compile(r"Closing Balance:\s*(-?[\d,]+\.\d{2})"),
}


def pdf_to_text(blob):
    """The PDF's own text layer, laid out as printed. Never OCR."""
    exe = shutil.which("pdftotext")
    if not exe:
        raise StatementRejected("this server cannot read PDF files (pdftotext is not installed) "
                                "-- load the CSV statement instead, or ask for the reader to be installed")
    try:
        out = subprocess.run([exe, "-layout", "-enc", "UTF-8", "-", "-"], input=blob,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except subprocess.TimeoutExpired:
        raise StatementRejected("the PDF took too long to read -- is it the bank's statement?")
    if out.returncode != 0:
        raise StatementRejected("the PDF could not be opened (it may be damaged or "
                                "password-protected) -- download the statement again from Yes Bank")
    text = out.stdout.decode("utf-8", "replace")
    if not text.strip():
        raise StatementRejected("this PDF has no text in it -- it is a scan or a photo. Download "
                                "the statement PDF from Yes Bank net banking instead; a picture "
                                "of a statement is never read")
    return text


def _pdf_header_columns(line):
    """End positions of the three amount columns on the header line."""
    cols = {}
    for key, word in (("wd", "Withdrawals"), ("dep", "Deposits"), ("bal", "Running Balance")):
        at = line.find(word)
        if at < 0:
            return None
        cols[key] = at + len(word)
    return cols


def parse_pdf_text(text):
    """Read the laid-out text of a Yes Bank statement PDF, and prove it."""
    m = _PDF_PERIOD_RE.search(text)
    if not m:
        raise StatementRejected("this PDF does not print 'Period: <from> - <to>' -- it does not "
                                "look like a Yes Bank statement of account")
    pfrom, pto = _iso(m.group(1)), _iso(m.group(2))
    a = _PDF_ACCT_RE.search(text)
    acct = a.group(1) if a else None

    totals = {}
    for k, rx in _PDF_TOTAL_RE.items():
        hit = rx.search(text)
        if not hit:
            raise StatementRejected("this PDF has no '%s' figure at its foot, so it cannot be "
                                    "checked against itself -- refusing rather than trusting it"
                                    % {"opening": "Opening Balance",
                                       "withdrawals": "Total Withdrawals",
                                       "deposits": "Total Deposits",
                                       "closing": "Closing Balance"}[k])
        totals[k] = _p(hit.group(1))

    lines, cols, cur = [], None, None
    for raw in text.splitlines():
        if "Cheque No/Reference No" in raw and "Deposits" in raw:
            cols = _pdf_header_columns(raw)
            cur = None
            continue
        if cols is None:
            continue
        s = raw.strip()
        if not s:
            cur = None
            continue
        if s.startswith("Opening Balance:") or s.startswith("Transaction details") \
                or s.startswith("Statement of account"):
            cols, cur = None, None
            continue
        rm = _PDF_ROW_RE.match(raw)
        if not rm:
            if cur is not None and s != "Date":
                cur["description"] = (cur["description"] + " " + s).strip()
            continue
        rest = rm.group(3)
        rest_at = raw.index(rest, rm.start(3))
        amts = []
        for am in _PDF_AMT_RE.finditer(rest):
            end = rest_at + am.end()
            key = min(cols, key=lambda k: abs(cols[k] - end))
            amts.append((key, _p(am.group(1)), rest_at + am.start()))
        keys = [k for k, _, _ in amts]
        if keys.count("bal") != 1 or len(amts) != 2 or keys.count("wd") + keys.count("dep") != 1:
            raise StatementRejected("a row dated %s could not be split into one amount and a "
                                    "running balance -- refusing the whole file rather than "
                                    "misreading one row" % rm.group(1))
        first_amt = min(p for _, _, p in amts)
        middle = raw[rest_at:first_amt].strip()
        parts = re.split(r"\s{2,}", middle, maxsplit=1)
        ref = parts[0].strip() if parts else ""
        desc = parts[1].strip() if len(parts) > 1 else ""
        val = dict((k, v) for k, v, _ in amts)
        cur = dict(txn_date=_iso(rm.group(1)), value_date=_iso(rm.group(2)),
                   description=desc, reference=ref or None,
                   withdrawal_p=val.get("wd", 0), deposit_p=val.get("dep", 0),
                   balance_p=val["bal"], is_cash_deposit=0)
        lines.append(cur)

    if not lines:
        raise StatementRejected("the PDF names a period but no transaction rows could be read")

    # ---- the proof: the statement checks itself, or nothing is stored -------
    newest_first = lines[0]["txn_date"] >= lines[-1]["txn_date"]
    chrono = list(reversed(lines)) if newest_first else list(lines)
    bal = totals["opening"]
    for ln in chrono:
        bal = bal + ln["deposit_p"] - ln["withdrawal_p"]
        if bal != ln["balance_p"]:
            raise StatementRejected("the running balance does not add up at the row dated %s "
                                    "(%.2f expected, %.2f printed) -- refusing the whole file"
                                    % (ln["txn_date"], bal / 100.0, ln["balance_p"] / 100.0))
    if bal != totals["closing"]:
        raise StatementRejected("the rows do not reach the printed closing balance "
                                "(%.2f vs %.2f) -- a row is missing; refusing"
                                % (bal / 100.0, totals["closing"] / 100.0))
    if sum(l["withdrawal_p"] for l in lines) != totals["withdrawals"]:
        raise StatementRejected("the rows do not add up to the printed Total Withdrawals -- refusing")
    if sum(l["deposit_p"] for l in lines) != totals["deposits"]:
        raise StatementRejected("the rows do not add up to the printed Total Deposits -- refusing")
    for ln in lines:
        if ln["txn_date"] < pfrom or ln["txn_date"] > pto:
            raise StatementRejected("a row dated %s falls outside the printed period %s to %s "
                                    "-- refusing" % (ln["txn_date"], pfrom, pto))
        ln["is_cash_deposit"] = 1 if (ln["deposit_p"] > 0
                                      and CASH_DEP_RE.search(ln["description"])) else 0

    return dict(account_ref=(acct or "unknown")[-4:], period_from=pfrom, period_to=pto,
                opening_p=totals["opening"], closing_p=totals["closing"], lines=lines,
                source="pdf")


def parse_pdf(blob):
    return parse_pdf_text(pdf_to_text(blob))


# --------------------------------------------------------------- persistence

def mask_name(name):
    """'yesbank_<15 digits>_x.csv' -> 'yesbank_x1923_x.csv'. Idempotent."""
    return re.sub(r"\d{6,}", lambda m: "x" + m.group(0)[-4:], name or "yesbank_statement")


def ingest_statement(con, filename, blob, store_dir=None, now=None):
    """Parse + store one statement. Idempotent on (account, date, ref, amounts).
    Never half-ingests: the parse either succeeds whole or raises."""
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    # v1.1: the bank names its downloads with the FULL account number; keep the
    # last four digits of any long digit run, so the number never reaches a
    # table, a log or a file name on this box (F-607).
    filename = mask_name(filename)
    parsed = parse_statement(blob)
    sha = hashlib.sha256(blob if isinstance(blob, bytes) else blob.encode()).hexdigest()

    if store_dir:
        os.makedirs(store_dir, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename or "yesbank.csv")[-120:]
        path = os.path.join(store_dir, "%s_%s" % (sha[:10], safe))
        if not os.path.exists(path):
            with open(path, "wb") as fh:
                fh.write(blob if isinstance(blob, bytes) else blob.encode())

    con.execute(
        "INSERT INTO bank_statement_period (account_ref, period_from, period_to, opening_p,"
        " closing_p, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?) "
        "ON CONFLICT(account_ref, period_from, period_to) DO UPDATE SET "
        " opening_p=excluded.opening_p, closing_p=excluded.closing_p,"
        " source_file=excluded.source_file, sha256=excluded.sha256,"
        " ingested_at=excluded.ingested_at",
        (parsed["account_ref"], parsed["period_from"], parsed["period_to"],
         parsed["opening_p"], parsed["closing_p"], filename, sha, now))

    added = 0
    for ln in parsed["lines"]:
        cur = con.execute(
            "INSERT OR IGNORE INTO bank_statement_line (account_ref, txn_date, value_date,"
            " description, reference, withdrawal_p, deposit_p, balance_p, is_cash_deposit,"
            " source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (parsed["account_ref"], ln["txn_date"], ln["value_date"], ln["description"],
             ln["reference"], ln["withdrawal_p"], ln["deposit_p"], ln["balance_p"],
             ln["is_cash_deposit"], filename, sha, now))
        added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    con.commit()

    cash = [l for l in parsed["lines"] if l["is_cash_deposit"]]
    return dict(ok=True, account_ref=parsed["account_ref"], period=(parsed["period_from"],
                parsed["period_to"]), lines=len(parsed["lines"]), new_lines=added,
                cash_deposits=len(cash),
                cash_total_p=sum(l["deposit_p"] for l in cash), sha256=sha[:12])


def covered(con, iso):
    """Is this date inside a statement period we actually hold?"""
    return con.execute("SELECT COUNT(*) FROM bank_statement_period "
                       "WHERE period_from <= ? AND period_to >= ?", (iso, iso)).fetchone()[0] > 0


def reconcile_cash_deposits(con, unit, date_from, date_to, window_days=3, now=None):
    """Match booked bank cash-outs against the bank's own cash deposits.

    Booked -> bank : a deposit we recorded that the bank never received   (F-112)
    Bank -> booked : cash the bank received that we never recorded        (F-103)
    Neither        : a booked deposit on a date no statement covers -> UNEVIDENCED,
                     reported every run, never a pass.

    Read-only against the money. Writes only recon_exception rows.
    """
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()

    booked = [dict(id=r[0], date=r[1], amount_p=r[2]) for r in con.execute(
        "SELECT m.id, e.business_date, m.amount_p FROM cash_movement m "
        "JOIN day_entry e ON e.id = m.day_entry_id "
        "WHERE e.unit=? AND m.direction='out' AND m.party='bank' "
        "  AND e.business_date BETWEEN ? AND ? ORDER BY e.business_date, m.id",
        (unit, date_from, date_to)).fetchall()]

    bank = [dict(id=r[0], date=r[1], amount_p=r[2]) for r in con.execute(
        "SELECT id, txn_date, deposit_p FROM bank_statement_line "
        "WHERE is_cash_deposit=1 AND txn_date BETWEEN ? AND ? ORDER BY txn_date, id",
        (date_from, date_to)).fetchall()]

    used = set()
    matched, unevidenced, not_in_bank = [], [], []
    for b in booked:
        hit = None
        for k in bank:
            if k["id"] in used or k["amount_p"] != b["amount_p"]:
                continue
            lag = (dt.date.fromisoformat(k["date"]) - dt.date.fromisoformat(b["date"])).days
            if 0 <= lag <= window_days:
                hit = k
                break
        if hit:
            used.add(hit["id"]); matched.append((b, hit))
        elif not covered(con, b["date"]):
            unevidenced.append(b)
        else:
            not_in_bank.append(b)

    not_booked = [k for k in bank if k["id"] not in used]

    def shout(iso, kind, expected_p, actual_p, detail, severity="high"):
        con.execute(
            "INSERT INTO recon_exception (unit, business_date, kind, expected_p, actual_p,"
            " diff_p, severity, status, detail, opened_at, shout_count) "
            "VALUES (?,?,?,?,?,?,?, 'open', ?, ?, 0) "
            "ON CONFLICT(unit, business_date, kind) DO UPDATE SET "
            " expected_p=excluded.expected_p, actual_p=excluded.actual_p,"
            " diff_p=excluded.diff_p, severity=excluded.severity, status='open',"
            " detail=excluded.detail, resolution=NULL, closed_by=NULL, closed_at=NULL",
            (unit, iso, kind, expected_p, actual_p,
             (expected_p or 0) - (actual_p or 0), severity, detail, now))

    open_dates = {}
    for b in not_in_bank:
        open_dates.setdefault('deposit_not_in_bank', set()).add(b["date"])
        shout(b["date"], 'deposit_not_in_bank', b["amount_p"], 0,
              "the books record a cash deposit of %.2f on this date and the Yes Bank statement "
              "covering it shows no such credit. This is the F-112 condition — a deposit that "
              "never happened. Do NOT approve around it; check the statement."
              % (b["amount_p"] / 100.0))
    for b in unevidenced:
        open_dates.setdefault('deposit_unevidenced', set()).add(b["date"])
        shout(b["date"], 'deposit_unevidenced', b["amount_p"], None,
              "a cash deposit of %.2f is booked on a date NO loaded statement covers. Not a "
              "failure and NOT a pass — it is unverified. Load the statement for this period."
              % (b["amount_p"] / 100.0), severity="medium")
    for k in not_booked:
        open_dates.setdefault('bank_deposit_not_booked', set()).add(k["date"])
        shout(k["date"], 'bank_deposit_not_booked', 0, k["amount_p"],
              "Yes Bank received a cash deposit of %.2f on this date and the books have no "
              "movement for it. This is how the 16 unrecorded deposits of S183 happened."
              % (k["amount_p"] / 100.0))

    # close anything this run has resolved
    for kind in ('deposit_not_in_bank', 'deposit_unevidenced', 'bank_deposit_not_booked'):
        keep = open_dates.get(kind, set())
        rows = con.execute("SELECT business_date FROM recon_exception WHERE unit=? AND kind=? "
                           "AND status IN ('open','acknowledged') AND business_date BETWEEN ? AND ?",
                           (unit, kind, date_from, date_to)).fetchall()
        for (iso,) in rows:
            if iso not in keep:
                con.execute("UPDATE recon_exception SET status='resolved', "
                            "resolution='matched against the Yes Bank statement', "
                            "closed_by='finance_yesbank', closed_at=? "
                            "WHERE unit=? AND kind=? AND business_date=?", (now, unit, kind, iso))
    con.commit()

    return dict(matched=len(matched), matched_p=sum(b["amount_p"] for b, _ in matched),
                deposit_not_in_bank=[(b["date"], b["amount_p"]) for b in not_in_bank],
                deposit_unevidenced=[(b["date"], b["amount_p"]) for b in unevidenced],
                bank_deposit_not_booked=[(k["date"], k["amount_p"]) for k in not_booked])


# ------------------------------------------------------------------ selftest

SAMPLE = """007485800001923 ,MANOJ KUMAR AGARWAL

Statement Period,2026-07-01,To,2026-08-17,
Opening Balance,INR 498125.67
Closing Balance,INR 257026.17
Transaction Date,Value Date,Description,Reference Number,Withdrawals,Deposits,Running Balance
2026-07-30,2026-07-30,CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY,1000174152026073000420,,85000.00,INR 257026.17
2026-07-30,2026-07-30,M_Jun26_SBOX_pay.ypbsm000006337,SCREF01284581015,125.00,,INR 172026.17
2026-07-22,2026-07-22,CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY,1000174152026072200960,,85000.00,INR 172173.67
2026-07-14,2026-07-14,CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY,1000476282026071400420,,105000.00,INR 528653.67
2026-07-07,2026-07-07,CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY,1000476282026070700080,,180000.00,INR 597838.67
2026-07-01,2026-07-01,CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY,1000476282026070100700,,135000.00,INR 633125.67
"""


def selftest(db_path=":memory:", schema_path=None):
    """Prove the parser reads a real statement and the reconciler can FAIL.
    A reconciler that has never been shown a bad day is not a reconciler."""
    import sqlite3
    print("finance_yesbank v%s — selftest" % VERSION)
    checks, failures = 0, []

    def ok(label, cond):
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(label)

    # --- parser -------------------------------------------------------------
    p = parse_statement(SAMPLE)
    ok("account is stored last-4 only, never in full", p["account_ref"] == "1923")
    ok("period read", (p["period_from"], p["period_to"]) == ("2026-07-01", "2026-08-17"))
    ok("opening balance in paise", p["opening_p"] == 49812567)
    ok("all 6 transaction rows read", len(p["lines"]) == 6)
    cash = [l for l in p["lines"] if l["is_cash_deposit"]]
    ok("5 cash deposits identified", len(cash) == 5)
    ok("the non-cash debit is NOT a cash deposit",
       all(not l["is_cash_deposit"] for l in p["lines"] if l["withdrawal_p"] > 0))
    ok("cash total is 5,90,000", sum(l["deposit_p"] for l in cash) == 59000000)
    for bad, why in [("", "empty file"),
                     ("a,b,c\n1,2,3\n", "no header"),
                     (SAMPLE.replace("Statement Period,2026-07-01,To,2026-08-17,", ""), "no period")]:
        try:
            parse_statement(bad); ok("refuses %s" % why, False)
        except StatementRejected:
            ok("refuses %s" % why, True)

    # --- reconciler ---------------------------------------------------------
    con = sqlite3.connect(db_path)
    con.executescript(open(schema_path).read()) if schema_path else None
    if schema_path is None:
        con.executescript("""
        CREATE TABLE business_unit(code TEXT PRIMARY KEY);
        CREATE TABLE day_entry(id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT);
        CREATE TABLE cash_movement(id INTEGER PRIMARY KEY, day_entry_id INT, direction TEXT,
                                   party TEXT, amount_p INT);
        CREATE TABLE recon_exception(id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT,
            kind TEXT, expected_p INT, actual_p INT, diff_p INT, severity TEXT,
            status TEXT DEFAULT 'open', detail TEXT, opened_at TEXT, shout_count INT DEFAULT 0,
            resolution TEXT, closed_by TEXT, closed_at TEXT,
            UNIQUE(unit,business_date,kind));
        CREATE TABLE bank_statement_line(id INTEGER PRIMARY KEY, account_ref TEXT, txn_date TEXT,
            value_date TEXT, description TEXT, reference TEXT, withdrawal_p INT DEFAULT 0,
            deposit_p INT DEFAULT 0, balance_p INT, is_cash_deposit INT DEFAULT 0,
            source_file TEXT, sha256 TEXT, ingested_at TEXT,
            UNIQUE(account_ref,txn_date,reference,deposit_p,withdrawal_p));
        CREATE TABLE bank_statement_period(id INTEGER PRIMARY KEY, account_ref TEXT,
            period_from TEXT, period_to TEXT, opening_p INT, closing_p INT, source_file TEXT,
            sha256 TEXT, ingested_at TEXT, UNIQUE(account_ref,period_from,period_to));
        """)
    con.execute("INSERT INTO business_unit VALUES('medical')")
    r = ingest_statement(con, "yesbank.csv", SAMPLE.encode(), None)
    ok("ingest reports 5 cash deposits", r["cash_deposits"] == 5)
    ok("re-ingesting the same file adds nothing",
       ingest_statement(con, "yesbank.csv", SAMPLE.encode(), None)["new_lines"] == 0)

    def book(iso, rupees):
        con.execute("INSERT INTO day_entry(unit,business_date) VALUES('medical',?)", (iso,))
        eid = con.execute("SELECT id FROM day_entry WHERE business_date=?", (iso,)).fetchone()[0]
        con.execute("INSERT INTO cash_movement(day_entry_id,direction,party,amount_p)"
                    " VALUES(?,'out','bank',?)", (eid, rupees * 100))

    book("2026-07-01", 135000)      # matches
    book("2026-07-07", 180000)      # matches
    book("2026-07-16", 40000)       # in period, no bank credit  -> deposit_not_in_bank
    book("2026-08-13", 75000)       # in period, no credit       -> THE F-112 CASE
    book("2026-09-02", 50000)       # outside every period       -> unevidenced
    con.commit()

    out = reconcile_cash_deposits(con, "medical", "2026-07-01", "2026-09-30")
    ok("the two real deposits matched", out["matched"] == 2)
    ok("F-112 IS CAUGHT: 13 Aug 75,000 flagged as not in the bank",
       ("2026-08-13", 7500000) in out["deposit_not_in_bank"])
    ok("the other in-period phantom is caught too",
       ("2026-07-16", 4000000) in out["deposit_not_in_bank"])
    ok("a deposit outside every loaded statement is UNEVIDENCED, not a pass",
       ("2026-09-02", 5000000) in out["deposit_unevidenced"])
    ok("unevidenced is never reported as not-in-bank",
       ("2026-09-02", 5000000) not in out["deposit_not_in_bank"])
    ok("bank credits we never booked are caught (the S183 condition)",
       len(out["bank_deposit_not_booked"]) == 3)
    ok("an exception row was actually written",
       con.execute("SELECT COUNT(*) FROM recon_exception WHERE kind='deposit_not_in_bank'"
                   " AND status='open'").fetchone()[0] == 2)
    # book the missing ones and prove it closes cleanly
    book("2026-07-14", 105000); book("2026-07-22", 85000); book("2026-07-30", 85000)
    con.execute("DELETE FROM cash_movement WHERE amount_p IN (4000000,7500000)")
    con.commit()
    out2 = reconcile_cash_deposits(con, "medical", "2026-07-01", "2026-09-30")
    ok("after correction all five bank deposits match", out2["matched"] == 5)
    ok("nothing is left claiming to be missing from the bank", not out2["deposit_not_in_bank"])
    ok("nothing is left unbooked", not out2["bank_deposit_not_booked"])
    ok("resolved exceptions were closed, not left shouting",
       con.execute("SELECT COUNT(*) FROM recon_exception WHERE kind='deposit_not_in_bank'"
                   " AND status='open'").fetchone()[0] == 0)
    con.close()

    print("  %d/%d checks passed" % (checks - len(failures), checks))
    for f in failures:
        print("  FAILED: %s" % f)
    print("SELFTEST GREEN" if not failures else "SELFTEST RED")
    return 1 if failures else 0


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
