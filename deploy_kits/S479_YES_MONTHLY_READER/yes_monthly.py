#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yes_monthly.py -- S479 (04-Oct-2026, F-725). OWNER: PARENT (clinic). Yes Bank's MONTHLY E-MAILED statement, read and proved.

The bank mails every account its month as a password-locked PDF ('YOUR ACCOUNT STATEMENT FROM 01-Sep-2026 TO 30-Sep-2026' ...
'Statement Of Transactions In Savings/Current Account No:<number> For The Period Of ... to ...' ... 'Primary Holder : <name>' ...
Transaction Date / Value Date / Description / Cheque No-Reference No / Deposits / Withdrawals / Running Balance ... and one foot line
'Opening Balance: .. Total Deposits: .. Total Withdrawals: .. Closing Balance: ..'). The shelf (packs.py, S412) opens it with the
owner's password. It is a THIRD layout: finance_yesbank.py reads the net-banking download ('Period: 1 Aug 2026 - 20 Sep 2026'),
yes_branch.py the branch's print ('STATEMENT OF ACCOUNT'); both refused this one, so the month's cell stayed empty with the
statement sitting opened on the shelf. This module reads this layout only; neither of the other two readers is touched.

THE LAYOUT, as the unlocked copies on the box print it through pdftotext -layout (three statements read, 04-Oct-2026):
  * the opening row is 'date date B/F <balance>' -- one figure;
  * a transaction row is 'date date [a piece of the description] [reference] <deposit> <withdrawal> <running balance>';
  * every line inside the table that is not a row, the heading or the page's own foot block (the bank's phone lines, its CIN,
    'Page 1 of 2') is a piece of a description -- wherever it starts. v1.1: no column band decides it (a band would drop a
    description silently if the bank moved the column), and a row left without any description refuses the file;
  * the description is WRAPPED AROUND its row, cut wherever the column ends (mid-word): a three-line description prints one line
    above the row, one on it and one below; a two-line one prints one above and one below. So a row always has as many
    description lines above it as below it, and the lines between two rows are the first row's tail and the next row's head.
    The lines are joined as they were cut -- with nothing between them ('MEDI' + 'COS', 'BAN' + 'K LIMITED'). A cut that falls
    exactly on a space loses that space; nothing here depends on it ('CASH DEP' is found with or without it).

It PROVES the statement before one row is stored -- the checks of S360 and S433: the B/F row is the printed opening balance, every
row's running balance, the printed closing, the printed totals of deposits and of withdrawals, and every row inside the printed
period by its value date or its transaction date (S475: the bank posts a quarter's interest on the first of the next month with the
last day's value date). And one check of its own: the description lines must pair with the rows as described above, or the file is
refused -- a description on the wrong row would put 'CASH DEP' on the wrong line of the pharmacy's cash check.

Same interface as yes_branch: is_monthly(text) / is_monthly_blob(blob) / ident(text) / parse_statement(blob) -> {account_ref (last
four only), period_from, period_to, opening_p, closing_p, lines[]} / ingest_statement(con, filename, blob, store_dir=None, now=None,
tables=None). ONE LINE ONCE: when the table pair already holds a statement of this account that covers the period and came from
another file, this copy is CHECKED against the lines held (date + amounts): agreeing, nothing is written; differing, it is said and
the rows not held are written. When another file's lines cover only PART of the period (the net-banking download of 1 Aug - 20 Sep beside September's statement: seen on the box, 04-Oct-2026),
only the rows not already held -- by date, withdrawal and deposit, counted -- are written; the three readers key their rows
differently, so the table's own key would have let those rows in twice. The same file read twice writes nothing new. A statement
that carries more than one account is refused (none has been seen).

No account number beyond its last four digits reaches a table, a log or a message: a long digit run in a description or a
reference keeps its last four, as in yes_branch.
"""
import datetime as dt
import hashlib
import re
import shutil
import subprocess

VERSION = "S479 1.2"


class StatementRejected(ValueError):
    pass


_DATE = r"\d{2}-[A-Za-z]{3}-\d{4}"
_AMT = r"-?\d[\d,]*\.\d{2}"
HEAD_RE = re.compile(r"YOUR\s+ACCOUNT\s+STATEMENT\s+FROM\s+(%s)\s+TO\s+(%s)" % (_DATE, _DATE), re.I)
SECT_RE = re.compile(r"Statement\s+Of\s+Transactions\s+In\s+Savings/Current\s+Account\s+No\s*:\s*(\d{6,})\s+For\s+The\s+Period\s+Of\s+(%s)\s+to\s+(%s)"
                     % (_DATE, _DATE), re.I)
HOLDER_RE = re.compile(r"^\s*Primary\s+Holder\s*:\s*(.+?)(?:\s{3,}.*)?$", re.I | re.M)
TYPE_RE = re.compile(r"^\s*(\d{6,})\s+([A-Za-z][A-Za-z ]*?Account)\s+INR\b", re.M)
ROW_RE = re.compile(r"^\s{0,4}(%s)\s+(%s)(.*?)\s+(%s)\s+(%s)\s+(%s)\s*$" % (_DATE, _DATE, _AMT, _AMT, _AMT))
BF_RE = re.compile(r"^\s{0,4}(%s)\s+(%s)\s+B/F\s+(%s)\s*$" % (_DATE, _DATE, _AMT))
FOOT_RE = re.compile(r"Opening\s+Balance\s*:\s*(%s)\s+Total\s+Deposits\s*:\s*(%s)\s+Total\s+Withdrawals\s*:\s*(%s)\s+Closing\s+Balance\s*:\s*(%s)"
                     % (_AMT, _AMT, _AMT, _AMT), re.I)
CASH_DEP_RE = re.compile(r"\bCASH\s*DEP\b", re.I)
CASH_ANY_RE = re.compile(r"CASH\s*DEP", re.I)         # the words anywhere, glued or not: they must HEAD a description (see parse_text)
REF_RE = re.compile(r"[0-9A-Za-z/_-]{4,}")
# a page's own foot block (the bank's phone lines, its CIN, 'Page 1 of 2'): the table stops there and goes on under the next heading
PAGE_END_RE = re.compile(r'^\s*(?:Say\s+"?Hi"?\s+on\b|WhatsApp\s+Banking\b|Email\s+us\s+at\b|CIN\s*:|Mandatory\s+disclaimer\b)'
                         r'|\bYES\s+TOUCH\b|\bToll\s+Free\b|\bPage\s+\d+\s+of\s+\d+\s*$', re.I)
HEAD3_RE = re.compile(r"^\s*Date\s+No\s*/\s*Reference\s+No\s*$", re.I)      # the heading's third line
REF_BACK = 12                 # a reference starts at most this far left of the 'Cheque' heading


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


def in_period(ln, pfrom, pto):
    """As S475 (F-720): a row belongs to the printed period when its VALUE date OR its transaction date is inside it."""
    v = ln.get("value_date") or ln["txn_date"]
    return (pfrom <= ln["txn_date"] <= pto) or (pfrom <= v <= pto)


def mask(s):
    """A long digit run keeps its last four: an account number never reaches a table from a description or a reference."""
    return re.sub(r"\d{11,}", lambda m: "x" + m.group(0)[-4:], s or "")


def pdf_text(blob):
    if not shutil.which("pdftotext"):
        raise StatementRejected("pdftotext is not on this machine")
    r = subprocess.run(["pdftotext", "-layout", "-", "-"], input=blob, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return r.stdout.decode("utf-8", "replace")


def is_monthly(text):
    """The monthly e-mailed layout: its own title, the one-account section line, the holder line, its column heading, the bank's foot."""
    t = text or ""
    up = t.upper()
    return bool(HEAD_RE.search(t) and SECT_RE.search(t) and "PRIMARY HOLDER" in up and "RUNNING BALANCE" in up
                and ("YES TOUCH" in up or "YES BANK" in up or "YES.BANK.IN" in up))


def is_monthly_blob(blob):
    if not (isinstance(blob, bytes) and blob.lstrip()[:5] == b"%PDF-"):
        return False
    try:
        return is_monthly(pdf_text(blob))
    except Exception:                                    # noqa: BLE001
        return False


def holder(text):
    """The account holder as the statement names it: the 'Primary Holder' line -- never the address block above it, whose
    second line is the proprietor ('PROP MANOJ KUMAR AGARWAL HUF' on Sanjeevni's statement is not the HUF account)."""
    m = HOLDER_RE.search(text or "")
    return " ".join(m.group(1).split()) if m else ""


def kind(text):
    """'current' / 'savings' from the Account Relationship Summary row of THIS account; '' when it does not say."""
    s = SECT_RE.search(text or "")
    for m in TYPE_RE.finditer(text or ""):
        if s and m.group(1) == s.group(1):
            t = m.group(2).upper()
            return "savings" if "SAVING" in t else ("current" if "CURRENT" in t else "")
    return ""


def ident(text):
    """What the shelf needs to place the file: bank, kind, tail, period, holder."""
    s = SECT_RE.search(text or "")
    return dict(bank="YES", kind=kind(text), tail=(s.group(1)[-4:] if s else ""), period_from=_iso(s.group(2)) if s else None,
                period_to=_iso(s.group(3)) if s else None, holder=holder(text))


def _parts(raw, middle_at, middle):
    """The pieces of a row between its dates and its figures, each with the column it starts at."""
    return [(m.group(0), middle_at + m.start()) for m in re.finditer(r"\S+(?: \S+)*", middle)]


def parse_text(text):
    if not is_monthly(text):
        raise StatementRejected("this is not a Yes Bank monthly e-mailed statement")
    sects = SECT_RE.findall(text)
    if len(sects) != 1:
        raise StatementRejected("this statement carries %d accounts; this reader takes one account's statement -- refusing" % len(sects))
    h, s = HEAD_RE.search(text), SECT_RE.search(text)
    pfrom, pto = _iso(s.group(2)), _iso(s.group(3))
    if (_iso(h.group(1)), _iso(h.group(2))) != (pfrom, pto):
        raise StatementRejected("the title's period and the account's period are not the same -- refusing")
    acct = s.group(1)[-4:]
    feet = FOOT_RE.findall(text)
    if len(feet) != 1:
        raise StatementRejected("the foot line (Opening Balance / Total Deposits / Total Withdrawals / Closing Balance) was found %d times, "
                                "so the statement cannot be checked against itself -- refusing" % len(feet))
    foot = dict(zip(("opening", "deposits", "withdrawals", "closing"), (_p(x) for x in feet[0])))

    in_table, started, ref_col, bf = False, False, None, None
    rows, gaps, gap = [], [], []
    for raw in text.splitlines():
        raw = raw.replace("\f", "")
        up = raw.upper()
        if "RUNNING BALANCE" in up and "DESCRIPTION" in up:               # the heading, once on every page
            in_table = started = True
            continue
        if re.match(r"^\s*TRANSACTION\s+CHEQUE\s*$", up):
            ref_col = up.index("CHEQUE")
            continue
        if started and FOOT_RE.search(raw):               # the bank's own totals end the table, on whichever page they fall
            break
        if not in_table:
            continue
        if PAGE_END_RE.search(raw):                       # this page's foot block: nothing below it is the table until the next heading
            in_table = False
            continue
        if HEAD3_RE.match(raw):
            continue
        b = BF_RE.match(raw)
        if b:
            if rows or bf is not None:
                raise StatementRejected("a second opening (B/F) row inside the table -- refusing")
            bf = dict(date=_iso(b.group(1)), balance=_p(b.group(3)))
            gap = []
            continue
        rm = ROW_RE.match(raw)
        if rm:
            desc, ref = [], None
            for piece, col in _parts(raw, rm.start(3), rm.group(3)):
                if (ref is None and col >= (ref_col if ref_col is not None else 72) - REF_BACK and REF_RE.fullmatch(piece)
                        and re.search(r"\d{4,}", piece)):
                    ref = piece
                else:
                    desc.append(piece)
            rows.append(dict(txn_date=_iso(rm.group(1)), value_date=_iso(rm.group(2)), mid=" ".join(desc), reference=ref,
                             deposit_p=_p(rm.group(4)), withdrawal_p=_p(rm.group(5)), balance_p=_p(rm.group(6)), is_cash_deposit=0))
            gaps.append(gap)
            gap = []
            continue
        if re.match(r"^\s{0,4}%s\b" % _DATE, raw):
            raise StatementRejected("a line that begins with a date is not a row this reader knows -- refusing")
        st = raw.strip()
        if st:                                            # EVERY other line inside the table is a piece of a description, wherever it
            gap.append(st)                                # starts: one that belongs to no row breaks the pairing below and refuses the file
    else:
        raise StatementRejected("the table has no foot line -- refusing")
    gaps.append(gap)
    if bf is None:
        raise StatementRejected("the table has no opening (B/F) row -- refusing")

    # ---- the description lines pair with the rows: as many above a row as below it -------------
    below = 0
    for i, ln in enumerate(rows):
        above = len(gaps[i]) - below
        if above < 0 or len(gaps[i + 1]) < above:
            raise StatementRejected("the description lines do not pair with the rows (at the row dated %s) -- refusing" % ln["txn_date"])
        pieces = gaps[i][below:] + ([ln["mid"]] if ln["mid"] else []) + gaps[i + 1][:above]
        ln["description"] = " ".join("".join(pieces).split())
        below = above
    if len(gaps[len(rows)]) != below:
        raise StatementRejected("the description lines do not pair with the rows (after the last row) -- refusing")
    for ln in rows:                                       # the bank prints a narration on every row; one without it was read wrong
        if not ln["description"]:
            raise StatementRejected("the row dated %s has no description -- its lines were not read; refusing" % ln["txn_date"])

    # ---- the proof: the statement checks itself, or nothing is stored --------------------------
    if bf["balance"] != foot["opening"]:
        raise StatementRejected("the B/F row (%.2f) is not the printed opening balance (%.2f) -- refusing" % (bf["balance"] / 100.0, foot["opening"] / 100.0))
    bal = foot["opening"]
    for ln in rows:
        bal = bal + ln["deposit_p"] - ln["withdrawal_p"]
        if bal != ln["balance_p"]:
            raise StatementRejected("the running balance does not add up at the row dated %s (%.2f expected, %.2f printed) -- refusing the whole file"
                                    % (ln["txn_date"], bal / 100.0, ln["balance_p"] / 100.0))
    if bal != foot["closing"]:
        raise StatementRejected("the rows do not reach the printed closing balance (%.2f vs %.2f) -- a row is missing; refusing" % (bal / 100.0, foot["closing"] / 100.0))
    if sum(x["deposit_p"] for x in rows) != foot["deposits"]:
        raise StatementRejected("the rows do not add up to the printed Total Deposits -- refusing")
    if sum(x["withdrawal_p"] for x in rows) != foot["withdrawals"]:
        raise StatementRejected("the rows do not add up to the printed Total Withdrawals -- refusing")
    seen = set()
    for i, ln in enumerate(rows, 1):
        if not in_period(ln, pfrom, pto):
            raise StatementRejected("a row dated %s (value date %s) falls outside the printed period %s to %s -- refusing"
                                    % (ln["txn_date"], ln["value_date"], pfrom, pto))
        ln.pop("mid", None)
        ln["description"] = mask(ln["description"])
        ln["reference"] = mask(ln["reference"]) if ln["reference"] else "monthly:%s:%d" % (pfrom, i)   # a stable key: the table is UNIQUE on it
        key = (ln["txn_date"], ln["reference"], ln["deposit_p"], ln["withdrawal_p"])
        if key in seen:                                   # two rows the table's key cannot tell apart: the later one carries its place
            ln["reference"] = "%s#%d" % (ln["reference"], i)
            key = (ln["txn_date"], ln["reference"], ln["deposit_p"], ln["withdrawal_p"])
        seen.add(key)
        # The bank writes a cash deposit as 'CASH DEP-...' at the HEAD of its narration. The words anywhere else mean the description
        # lines were paired with the wrong rows (a line of another row glued in front), and the pharmacy's cash check would then
        # read the wrong row as cash, or miss one: refuse.
        cm = CASH_ANY_RE.search(ln["description"])
        if cm and cm.start() != 0:
            raise StatementRejected("the row dated %s carries 'CASH DEP' inside its description, not at its head -- the description "
                                    "lines were not paired with their rows; refusing" % ln["txn_date"])
        ln["is_cash_deposit"] = 1 if (ln["deposit_p"] > 0 and cm and CASH_DEP_RE.match(ln["description"])) else 0
    return dict(account_ref=acct, period_from=pfrom, period_to=pto, opening_p=foot["opening"], closing_p=foot["closing"],
                lines=rows, source="monthly")


def parse_statement(blob):
    if not (isinstance(blob, bytes) and blob.lstrip()[:5] == b"%PDF-"):
        raise StatementRejected("a monthly e-mailed statement is a PDF")
    return parse_text(pdf_text(blob))


def _mask_name(name):
    return re.sub(r"\d{6,}", lambda m: "x" + m.group(0)[-4:], name or "yes_monthly.pdf")


def ingest_statement(con, filename, blob, store_dir=None, now=None, tables=None):
    """Parse, prove, store. ONE LINE ONCE: a row another file already holds on this table pair (date + withdrawal + deposit + the cash flag, counted;
    looked for from the period's first day to the statement's last row, which may be the first of the next month) is not written a
    second time. A period another file's statement COVERS is checked against the lines held: when they agree nothing is written;
    when they differ it is SAID and the rows not held are written. The same file again writes nothing new."""
    ptab, ltab = tables or ("bank_statement_period", "bank_statement_line")
    if not (re.match(r"^[a-z_]+$", ptab) and re.match(r"^[a-z_]+$", ltab)):
        raise StatementRejected("the table pair must be plain identifiers")
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    filename = _mask_name(filename)
    parsed = parse_statement(blob)
    sha = hashlib.sha256(blob).hexdigest()
    acct, pf, pt = parsed["account_ref"], parsed["period_from"], parsed["period_to"]
    base = dict(ok=True, account_ref=acct, period=(pf, pt), lines=len(parsed["lines"]), closing_p=parsed["closing_p"],
                closing_printed=True, layout="monthly", sha256=sha[:12])
    days = [x["txn_date"] for x in parsed["lines"]]
    lo, hi = min([pf] + days), max([pt] + days)          # the bank posts a month's interest on the first of the next: that row is this file's too
    others, table = {}, {}                                # what OTHER files hold in those days (the skip), and what the table holds (the check)
    for r in con.execute("SELECT txn_date, withdrawal_p, deposit_p, is_cash_deposit, COALESCE(sha256,'') FROM " + ltab +
                         " WHERE account_ref=? AND txn_date BETWEEN ? AND ?", (acct, lo, hi)):
        k3 = (r[0], r[1], r[2])
        table[k3] = table.get(k3, 0) + 1
        if r[4] != sha:
            k4 = (r[0], r[1], r[2], 1 if r[3] else 0)    # the cash flag is part of the match: a cash deposit is never skipped for a transfer
            others[k4] = others.get(k4, 0) + 1
    held = con.execute("SELECT period_from, period_to FROM " + ptab + " WHERE account_ref=? AND period_from<=? AND period_to>=? "
                       "AND COALESCE(sha256,'')<>? LIMIT 1", (acct, pf, pt, sha)).fetchone()
    differs = []
    if held:
        # AGREES: inside the period the table holds exactly this statement's rows (whoever wrote them -- this file read again is its
        # own witness), and every row it carries from outside the period is on the table too
        want_in, want_out = {}, {}
        for x in parsed["lines"]:
            k = (x["txn_date"], x["withdrawal_p"], x["deposit_p"])
            d = want_in if pf <= x["txn_date"] <= pt else want_out
            d[k] = d.get(k, 0) + 1
        have_in = {k: n for k, n in table.items() if pf <= k[0] <= pt}
        if have_in == want_in and all(table.get(k, 0) >= n for k, n in want_out.items()):
            base.update(new_lines=0, checked_against="%s..%s" % (held[0], held[1]), agrees=True, differs=[])
            return base
        # DIFFERS: said -- and the rows the table does not hold are written, so a period row that promised a month it did not carry
        # (a download taken before the month ended) never leaves the month short.
        differs = ["held %d lines in the period, the monthly statement %d" % (sum(have_in.values()), sum(want_in.values()))]
    con.execute("INSERT INTO " + ptab + " (account_ref, period_from, period_to, opening_p, closing_p, source_file, sha256, ingested_at) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(account_ref, period_from, period_to) DO UPDATE SET opening_p=excluded.opening_p, "
                "closing_p=excluded.closing_p, source_file=excluded.source_file, sha256=excluded.sha256, ingested_at=excluded.ingested_at",
                (acct, pf, pt, parsed["opening_p"], parsed["closing_p"], "monthly:" + filename, sha, now))
    added = already = 0
    for ln in parsed["lines"]:
        k = (ln["txn_date"], ln["withdrawal_p"], ln["deposit_p"], ln["is_cash_deposit"])
        if others.get(k, 0) > 0:                          # this row is on the table from another file: it is not written twice
            others[k] -= 1
            already += 1
            continue
        cur = con.execute("INSERT OR IGNORE INTO " + ltab + " (account_ref, txn_date, value_date, description, reference, withdrawal_p, deposit_p, "
                          "balance_p, is_cash_deposit, source_file, sha256, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                          (acct, ln["txn_date"], ln["value_date"], ln["description"], ln["reference"], ln["withdrawal_p"], ln["deposit_p"],
                           ln["balance_p"], ln["is_cash_deposit"], "monthly:" + filename, sha, now))
        added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
    base.update(new_lines=added, already_held=already)
    if held:
        base.update(checked_against="%s..%s" % (held[0], held[1]), agrees=False,
                    differs=differs + ["%d line(s) written, %d already held" % (added, already)])
    return base


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        with open(p, "rb") as fh:
            b = fh.read()
        try:
            r = parse_statement(b)
            t = pdf_text(b)
            print("%s  OK  ...%s  %s..%s  %d lines  %d cash deposit(s)  holder=%r kind=%s"
                  % (_mask_name(p.rsplit("/", 1)[-1])[-40:], r["account_ref"], r["period_from"], r["period_to"], len(r["lines"]),
                     sum(x["is_cash_deposit"] for x in r["lines"]), holder(t), kind(t)))
        except StatementRejected as ex:
            print("%s  REFUSED  %s" % (_mask_name(p.rsplit("/", 1)[-1])[-40:], ex))
