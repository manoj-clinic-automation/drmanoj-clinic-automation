"""S503 builder: yes_monthly.py S479 1.2 -> S503 1.3, by anchored edits on the live bytes (each anchor asserted exactly once)."""
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == 'a4270bb3aa12f7c6235167a8cd86a0b3', 'FROM pin differs'
t = b.decode('utf-8')
def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, (n, old[:60])
    t = t.replace(old, new)

rep('VERSION = "S479 1.2"', 'VERSION = "S503 1.3"')
rep('''_DATE = r"\\d{2}-[A-Za-z]{3}-\\d{4}"''', '''_DATE = r"\\d{2}-[A-Za-z]{3}-\\d{4}"
_DATE_ROW = r"(?:\\d{2}-[A-Za-z]{3}-\\d{4}|\\d{2}/\\d{2}/\\d{4})"       # S503: the consolidated layout prints its rows dd/mm/yyyy''')
rep('''HEAD_RE = re.compile(r"YOUR\\s+ACCOUNT\\s+STATEMENT\\s+FROM\\s+(%s)\\s+TO\\s+(%s)" % (_DATE, _DATE), re.I)''',
    '''HEAD_RE = re.compile(r"YOUR\\s+ACCOUNT\\s+STATEMENT\\s+FROM\\s+(%s)\\s+TO\\s+(%s)" % (_DATE, _DATE), re.I)
# S503: the CONSOLIDATED layout (the statement per customer id: 'YOUR CONSOLIDATED STATEMENT FOR SEP' 26'), read by the same rules
CONS_HEAD_RE = re.compile(r"YOUR\\s+CONSOLIDATED\\s+STATEMENT\\s+FOR\\s+([A-Za-z]{3})\\W{0,2}\\s*(\\d{2})\\b", re.I)''')
rep('''In\\s+Savings/Current\\s+Account\\s+No''', '''In\\s+(?:Savings/Current|Savings?|Current)\\s+Account\\s+No''')
rep('''ROW_RE = re.compile(r"^\\s{0,4}(%s)\\s+(%s)(.*?)\\s+(%s)\\s+(%s)\\s+(%s)\\s*$" % (_DATE, _DATE, _AMT, _AMT, _AMT))
BF_RE = re.compile(r"^\\s{0,4}(%s)\\s+(%s)\\s+B/F\\s+(%s)\\s*$" % (_DATE, _DATE, _AMT))''',
    '''ROW_RE = re.compile(r"^\\s{0,4}(%s)\\s+(%s)(.*?)\\s+(%s)\\s+(%s)\\s+(%s)\\s*$" % (_DATE_ROW, _DATE_ROW, _AMT, _AMT, _AMT))
BF_RE = re.compile(r"^\\s{0,4}(%s)\\s+(%s)\\s+B/F(?:\\s*\\.\\.\\.)?\\s+(%s)\\s*$" % (_DATE_ROW, _DATE_ROW, _AMT))''')
rep('''CASH_DEP_RE = re.compile(''', '''# S503: the consolidated layout prints the withdrawals first, in its columns and in its foot line
FOOT_WD_RE = re.compile(r"Opening\\s+Balance\\s*:\\s*(%s)\\s+Total\\s+Withdrawals\\s*:\\s*(%s)\\s+Total\\s+Deposits\\s*:\\s*(%s)\\s+Closing\\s+Balance\\s*:\\s*(%s)"
                        % (_AMT, _AMT, _AMT, _AMT), re.I)
CASH_DEP_RE = re.compile(''')
rep('''HEAD3_RE = re.compile(r"^\\s*Date\\s+No\\s*/\\s*Reference\\s+No\\s*$", re.I)''',
    '''HEAD3_RE = re.compile(r"^\\s*Date\\s+No\\s*/\\s*Reference\\s+No\\.?\\s*$", re.I)''')
rep('''def _iso(s):
    return dt.datetime.strptime(s.title(), "%d-%b-%Y").date().isoformat()''',
    '''def _iso(s):
    s = s.strip()
    if "/" in s:                                          # S503: the consolidated layout's rows, dd/mm/yyyy
        return dt.datetime.strptime(s, "%d/%m/%Y").date().isoformat()
    return dt.datetime.strptime(s.title(), "%d-%b-%Y").date().isoformat()


def _foot(text):
    """S503: the one foot line, in either order -> (opening, deposits, withdrawals, closing) in paise, and how many were found."""
    a = [dict(zip(("opening", "deposits", "withdrawals", "closing"), (_p(x) for x in f))) for f in FOOT_RE.findall(text)]
    b = [dict(zip(("opening", "withdrawals", "deposits", "closing"), (_p(x) for x in f))) for f in FOOT_WD_RE.findall(text)]
    return a + b''')
rep('''    return bool(HEAD_RE.search(t) and SECT_RE.search(t)''', '''    return bool((HEAD_RE.search(t) or CONS_HEAD_RE.search(t)) and SECT_RE.search(t)''')
rep('''    h, s = HEAD_RE.search(text), SECT_RE.search(text)
    pfrom, pto = _iso(s.group(2)), _iso(s.group(3))
    if (_iso(h.group(1)), _iso(h.group(2))) != (pfrom, pto):
        raise StatementRejected("the title's period and the account's period are not the same -- refusing")
    acct = s.group(1)[-4:]
    feet = FOOT_RE.findall(text)
    if len(feet) != 1:
        raise StatementRejected("the foot line (Opening Balance / Total Deposits / Total Withdrawals / Closing Balance) was found %d times, "
                                "so the statement cannot be checked against itself -- refusing" % len(feet))
    foot = dict(zip(("opening", "deposits", "withdrawals", "closing"), (_p(x) for x in feet[0])))
''', '''    h, s = HEAD_RE.search(text), SECT_RE.search(text)
    pfrom, pto = _iso(s.group(2)), _iso(s.group(3))
    layout = "monthly"
    if h:
        if (_iso(h.group(1)), _iso(h.group(2))) != (pfrom, pto):
            raise StatementRejected("the title's period and the account's period are not the same -- refusing")
    else:                                                 # S503: the consolidated title names the month only ('SEP' 26')
        c = CONS_HEAD_RE.search(text)
        layout = "consolidated"
        if (c.group(1).title(), "20" + c.group(2)) != (dt.date.fromisoformat(pfrom).strftime("%b"), pfrom[:4]) or pfrom[:7] != pto[:7]:
            raise StatementRejected("the title's month and the account's period are not the same -- refusing")
    acct = s.group(1)[-4:]
    feet = _foot(text)
    if len(feet) != 1:
        raise StatementRejected("the foot line (Opening Balance / Total Deposits / Total Withdrawals / Closing Balance) was found %d times, "
                                "so the statement cannot be checked against itself -- refusing" % len(feet))
    foot = feet[0]
    dep_first = None                                      # S503: which money column comes first, read from the heading itself
''')
rep('''        if "RUNNING BALANCE" in up and "DESCRIPTION" in up:               # the heading, once on every page
            in_table = started = True
            continue''', '''        if "RUNNING BALANCE" in up and "DESCRIPTION" in up:               # the heading, once on every page
            if "DEPOSITS" not in up or "WITHDRAWALS" not in up:
                raise StatementRejected("the table's heading does not name its Deposits and Withdrawals columns -- refusing")
            df = up.index("DEPOSITS") < up.index("WITHDRAWALS")
            if dep_first is not None and dep_first != df:
                raise StatementRejected("the money columns change order between pages -- refusing")
            dep_first = df
            in_table = started = True
            continue''')
rep('''        if started and FOOT_RE.search(raw):''', '''        if started and (FOOT_RE.search(raw) or FOOT_WD_RE.search(raw)):''')
rep('''        if re.match(r"^\\s*TRANSACTION\\s+CHEQUE\\s*$", up):''', '''        if re.match(r"^\\s*TRANSACTION\\s+CHEQUE\\s*$", up):''')
rep('''                             deposit_p=_p(rm.group(4)), withdrawal_p=_p(rm.group(5)), balance_p=_p(rm.group(6)), is_cash_deposit=0))''',
    '''                             deposit_p=_p(rm.group(4) if dep_first else rm.group(5)),
                             withdrawal_p=_p(rm.group(5) if dep_first else rm.group(4)), balance_p=_p(rm.group(6)), is_cash_deposit=0))''')
rep('''        if re.match(r"^\\s{0,4}%s\\b" % _DATE, raw):''', '''        if re.match(r"^\\s{0,4}%s\\b" % _DATE_ROW, raw):''')
rep('''                lines=rows, source="monthly")''', '''                lines=rows, source="monthly", layout=layout)''')
rep('''    base = dict(ok=True, account_ref=acct, period=(pf, pt), lines=len(parsed["lines"]), closing_p=parsed["closing_p"],
                closing_printed=True, layout="monthly", sha256=sha[:12])''', '''    base = dict(ok=True, account_ref=acct, period=(pf, pt), lines=len(parsed["lines"]), closing_p=parsed["closing_p"],
                closing_printed=True, layout=parsed.get("layout", "monthly"), sha256=sha[:12])''')
# docstring note
rep('''No account number beyond its last four digits reaches a table''', '''S503 (10-Oct-2026): the CONSOLIDATED statement (one per customer id, 'YOUR CONSOLIDATED STATEMENT FOR SEP' 26' ... 'Statement Of
Transactions In Current Account No: ... For The Period Of ...') is the same table with three differences, each read, none guessed: rows
dated dd/mm/yyyy, the Withdrawals column BEFORE Deposits (taken from the heading on every page; a page that disagrees refuses the file),
and the foot line in that order too. The title names a month: it must be the period's month. Everything else -- the pairing, the proof,
one line once -- is unchanged.

No account number beyond its last four digits reaches a table''')
open(dst, 'w', encoding='utf-8').write(t)
print('built', hashlib.md5(t.encode()).hexdigest())
