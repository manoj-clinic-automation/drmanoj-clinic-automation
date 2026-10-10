import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == '49f2a26e54ddc87dc67cabce5a0b304d', 'FROM pin differs'
s = b.decode('utf-8')
def rep(a, c):
    global s
    n = s.count(a)
    assert n == 1, (n, a[:80])
    s = s.replace(a, c)
rep('''    S504: the card statements' own lines (card_line) first; the running Excel only when they hold nothing for the month."""
    if _has(con, "card_line"):
        lab = _card_labels(con)
        hits = [r for r in con.execute("SELECT txn_date, slot_key, description, amount_p FROM card_line WHERE credit=0 AND substr(txn_date,1,7)=? "
                                       "ORDER BY txn_date", (month,)).fetchall() if any(w in (r[2] or "").upper() for w in words)]
        if hits:
            return ["auto-paid %s on %s by the %s card (%s)" % (_inr(r[3]), _dmy(r[0]), lab.get(r[1], r[1]), re.sub(r"\\d{6,}", "", r[2] or "")[:40])
                    for r in hits]
''', '''    S504: the card statements' own lines (card_line) first; the running Excel only when they hold nothing for the month.
    S505 (the owner, 10-Oct-2026: for September's pack "the 17-Aug payment" -- the one on the card statement dated 12-Sep): a card's
    bill belongs to the month its STATEMENT is dated in, as the card sheet and the attached statement do; the running Excel is read
    (by the line's own date, as before) only when no card statement dated in the month has been read."""
    if _has(con, "card_line") and _has(con, "card_stmt") and con.execute("SELECT 1 FROM card_stmt WHERE substr(statement_date,1,7)=? LIMIT 1", (month,)).fetchone():
        lab = _card_labels(con)
        hits = [r for r in con.execute("SELECT l.txn_date, l.slot_key, l.description, l.amount_p, s.statement_date FROM card_line l JOIN card_stmt s ON s.id=l.stmt_id "
                                       "WHERE l.credit=0 AND substr(s.statement_date,1,7)=? ORDER BY l.txn_date", (month,)).fetchall()
                if any(w in (r[2] or "").upper() for w in words)]
        return ["auto-paid %s on %s by the %s card, on its statement dated %s (%s)" % (_inr(r[3]), _dmy(r[0]), lab.get(r[1], r[1]), _dmy(r[4]),
                                                                                     re.sub(r"\\d{6,}", "", r[2] or "")[:40]) for r in hits]
''')
open(dst, 'wb').write(s.encode('utf-8'))
print('built', hashlib.md5(s.encode('utf-8')).hexdigest())
