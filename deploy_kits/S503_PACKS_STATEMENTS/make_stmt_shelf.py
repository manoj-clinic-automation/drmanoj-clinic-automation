"""S503 builder: stmt_shelf.py (52a5fb07) -> S503, anchored edits on the live bytes."""
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
assert hashlib.md5(b).hexdigest() == '52a5fb07339e12d6a875b6fbdb6acddc', 'FROM pin differs'
t = b.decode('utf-8')
def rep(old, new):
    global t
    n = t.count(old)
    assert n == 1, (n, old[:80])
    t = t.replace(old, new)
rep('''S417 (F-636): an .xlsx in the Credit Card Statements root is recorded as the running Excel (folder all_txn), never as a card file.
"""''', '''S417 (F-636): an .xlsx in the Credit Card Statements root is recorded as the running Excel (folder all_txn), never as a card file.
S503 (10-Oct-2026): the running Excel is fetched AGAIN whenever Drive's copy changes (it is rebuilt in place, so its id never
changes and the old 'once per id' rule left the shelf on its first copy for ever); a locked file the owner set aside is never tried.
"""''')
rep('''    rows = con.execute("SELECT id, local_path FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='')%s ORDER BY id" % fresh).fetchall()''',
    '''    rows = con.execute("SELECT id, local_path FROM stmt_file WHERE locked=1 AND (unlocked_path IS NULL OR unlocked_path='') "
                       "AND COALESCE(read_status,'')<>'set aside'%s ORDER BY id" % fresh).fetchall()       # S503: the owner's set-aside files are left alone''')
rep('''        elif m and m["id"] in have:
            seen += 1''', '''        elif m and m["id"] in have:
            seen += 1
            old = con.execute("SELECT mtime, size FROM stmt_file WHERE drive_id=?", (m["id"],)).fetchone()     # S503: rebuilt in place -> fetched again
            if old and ((m.get("modifiedTime") or "")[:19] != (old[0] or "") or int(m.get("size") or 0) != int(old[1] or 0)):
                try:
                    blob = media(m["id"])
                    local = os.path.join(INBOX, "all_transactions.xlsx")
                    with open(local, "wb") as fh:
                        fh.write(blob)
                    con.execute("UPDATE stmt_file SET name=?, mtime=?, size=?, sha256=?, fetched_at=?, local_path=? WHERE drive_id=?",
                                (m["name"][:200], (m.get("modifiedTime") or "")[:19], int(m.get("size") or 0), sha(blob), time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 local, m["id"]))
                    new += 1
                except Exception as ex:                  # noqa: BLE001
                    errors.append("All_Transactions.xlsx (refresh): %s" % str(ex)[:100])''')
open(dst, 'w', encoding='utf-8').write(t)
print('built', hashlib.md5(t.encode()).hexdigest())
