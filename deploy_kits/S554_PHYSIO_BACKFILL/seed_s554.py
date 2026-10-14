"""seed_s554.py -- kit S554_PHYSIO_BACKFILL, the data step (idempotent).
    python3 -B seed_s554.py <finance.db>
Writes the register's floor ONCE: setting physio_book.from = 2026-10-01 (INSERT OR IGNORE -- a value already there, e.g. one the
owner chose, is kept). Writes nothing else; no physio row, no clinic_physio_day row."""
import sqlite3
import sys

KEY, VALUE = "physio_book.from", "2026-10-01"
NOTE = "S554: the physio register's floor -- slips, home visits, payments, the report's match and Bhati's duty line start here"


def main(dbp):
    con = sqlite3.connect(dbp, timeout=60)
    try:
        cur = con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (KEY, VALUE, NOTE))
        con.commit()
        added = cur.rowcount
        v = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()[0]
    finally:
        con.close()
    print("data step: setting %s = %s (%d added)" % (KEY, v, added))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
