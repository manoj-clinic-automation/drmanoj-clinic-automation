#!/usr/bin/env python3
"""f1547_s921.py -- F-1547, once: the order messages of 12-20 Nov the reception phone SENT while the App-foreground constraint blocked its
'sent' report (they stand 'skipped', last_error 'unconfirmed: handed ...', never sent_at) become 'sent' at their hand-out moment.
argv: <db> [--write]. Without --write it only counts. Keyed and idempotent: a second run finds none. Prints 'F1547 n=<count> ids=<...>'."""
import sqlite3
import sys

DB = sys.argv[1]
WRITE = "--write" in sys.argv
WHERE = ("kind='order' AND status='skipped' AND sent_at IS NULL AND handed_at IS NOT NULL AND last_error LIKE 'unconfirmed: handed%' "
         "AND queued_at >= '2026-11-12' AND queued_at < '2026-11-21'")
con = sqlite3.connect(DB, timeout=30)
ids = [r[0] for r in con.execute("SELECT id FROM supplier_msg WHERE " + WHERE + " ORDER BY id")]
if WRITE and ids:
    con.execute("UPDATE supplier_msg SET status='sent', sent_at=handed_at, sent_by='S921 (F-1547)', "
                "last_error='S921: the phone sent it; its report was blocked (F-1547). Was: ' || last_error WHERE " + WHERE)
    con.commit()
left = con.execute("SELECT COUNT(*) FROM supplier_msg WHERE " + WHERE).fetchone()[0]
con.close()
print("F1547 n=%d ids=%s left=%d" % (len(ids), ",".join(map(str, ids)), left))
