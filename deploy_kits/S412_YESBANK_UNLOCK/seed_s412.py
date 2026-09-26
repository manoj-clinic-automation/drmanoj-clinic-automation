#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s412.py -- kit S412_YESBANK_UNLOCK. On the finance database (a scratch copy in the walk, the live one at install):
  1. the S412 tables and columns (packs.ensure): stmt_secret (empty -- the owner types the password on the page), the log, the
     per-account Yes Bank tables, stmt_file.locked / unlocked_path
  2. the ICICI anchor (3a): if the current anchor rests on a degenerate period (the text statement's 'dd..dd' header, S411's first run
     moved it to 10-Sep on that), it is RESTORED -- from the S411 database backup's row when that file is beside the database
     (S412_ANCHOR_BACKUP names another path), else recomputed from the newest iCRM statement of the Sanjeevni account whose closing
     is printed. Dates and the source words are printed, never a balance.
  3. the pipe .txt periods (3b): every 'from == to' pipe period row is dropped and the .txt files are read again with the v1.1+S412
     reader, which widens the period to the rows; the shelf rows take the widened period
  4. every bank file still noted 'password-protected' is flagged locked=1 (the unlock step's key) and its note says where the password goes
  5. packs.process_inbox() -- nothing unlocks without a stored secret; the month grid is printed (states only)
Usage: seed_s412.py DB_PATH   (FINANCE_DIR names the folder holding packs.py; default /root/finance)
"""
import os
import re
import sqlite3
import sys

S411_BACKUP = "finance.db.bak_S411_20260926_124432"


def seed(path):
    fin = os.environ.get("FINANCE_DIR", "/root/finance")
    if fin not in sys.path:
        sys.path.insert(0, fin)
    os.environ.setdefault("FINANCE_DB", path)
    import packs  # noqa: E402
    con = sqlite3.connect(path, timeout=60)
    con.row_factory = sqlite3.Row
    packs.ensure(con)
    # 2 · the anchor
    words = []
    if packs._has(con, "bank_anchor"):
        r = con.execute("SELECT as_on, source FROM bank_anchor WHERE unit='medical' AND account='icici'").fetchone()
        m = re.search(r"(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})", str(r["source"] or "")) if r else None
        if r and m and m.group(1) == m.group(2):
            bak = os.environ.get("S412_ANCHOR_BACKUP") or os.path.join(os.path.dirname(os.path.abspath(path)), S411_BACKUP)
            row = None
            if os.path.exists(bak):
                try:
                    b = sqlite3.connect("file:%s?mode=ro" % bak, uri=True)
                    row = b.execute("SELECT as_on, balance_p, source, entered_by, entered_at FROM bank_anchor WHERE unit='medical' AND account='icici'").fetchone()
                    b.close()
                except sqlite3.Error:
                    row = None
                mm = re.search(r"(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})", str(row[2] or "")) if row else None
                if row and mm and mm.group(1) == mm.group(2):
                    row = None
            if row:
                con.execute("UPDATE bank_anchor SET as_on=?, balance_p=?, source=?, entered_by=?, entered_at=? WHERE unit='medical' AND account='icici'", tuple(row))
                words.append("anchor: was %s (rested on a degenerate text-statement period) -> RESTORED from the S411 backup: as_on %s, source '%s', entered_by %s"
                             % (r["as_on"], row[0], row[2], row[3]))
                tail = con.execute("SELECT ident_tail FROM stmt_slot WHERE key='icici_sanj'").fetchone()
                if tail and tail[0] and packs._has(con, "icici_statement_period"):
                    p = con.execute("SELECT closing_p FROM icici_statement_period WHERE account_ref=? AND period_to=? AND closing_printed=1 AND layout<>'pipe'", (tail[0], row[0])).fetchone()
                    words.append("        the backup's balance equals the iCRM statement's printed closing for %s: %s" % (row[0], ("yes" if (p and int(p[0] or 0) == int(row[1] or 0)) else ("no" if p else "no iCRM statement ends that day"))))
            else:
                tail = con.execute("SELECT ident_tail FROM stmt_slot WHERE key='icici_sanj'").fetchone()
                p = None
                if tail and tail[0] and packs._has(con, "icici_statement_period"):
                    p = con.execute("SELECT period_from, period_to, closing_p FROM icici_statement_period WHERE account_ref=? AND closing_printed=1 AND layout<>'pipe' "
                                    "AND period_from<period_to ORDER BY period_to DESC LIMIT 1", (tail[0],)).fetchone()
                if p:
                    con.execute("UPDATE bank_anchor SET as_on=?, balance_p=?, source=?, entered_by=?, entered_at=? WHERE unit='medical' AND account='icici'",
                                (p[1], p[2], "ICICI Sanjeevni statement %s..%s, the bank's own closing balance (S412 restore)" % (p[0], p[1]), "seed S412", packs._now()))
                    words.append("anchor: was %s (rested on a degenerate text-statement period); no backup row -> RECOMPUTED from the newest iCRM statement with a printed closing: as_on %s" % (r["as_on"], p[1]))
                else:
                    words.append("anchor: was %s (degenerate) but neither a backup row nor an iCRM statement with a printed closing is here -- LEFT ALONE" % r["as_on"])
        elif r:
            words.append("anchor: as_on %s rests on a real period ('%s') -- left alone" % (r["as_on"], (r["source"] or "")[:60]))
        else:
            words.append("anchor: no ICICI anchor row -- nothing to restore")
    con.commit()
    # 3 · the pipe periods
    deg = con.execute("SELECT account_ref, period_from FROM icici_statement_period WHERE layout='pipe' AND period_from=period_to ORDER BY account_ref, period_from").fetchall() if packs._has(con, "icici_statement_period") else []
    if deg:
        con.execute("DELETE FROM icici_statement_period WHERE layout='pipe' AND period_from=period_to")
    n_txt = con.execute("UPDATE stmt_file SET read_status=NULL, matched_status=NULL WHERE folder='bank' AND lower(name) LIKE '%.txt' AND slot_id IS NOT NULL").rowcount
    # 4 · the locked files
    n_lock = con.execute("UPDATE stmt_file SET locked=1 WHERE folder<>'cards' AND note LIKE 'password-protected%' AND COALESCE(locked,0)=0").rowcount
    con.execute("UPDATE stmt_file SET note=? WHERE folder<>'cards' AND locked=1 AND (unlocked_path IS NULL OR unlocked_path='') AND slot_id IS NULL", (packs.LOCKED_NOTE,))
    con.commit()
    # 5 · identify / read again
    res = packs.process_inbox(con)
    for w in words:
        print("  " + w)
    print("  pipe periods: %d degenerate row(s) dropped (%s); %d .txt file(s) read again -> %s" % (
        len(deg), ", ".join("…%s %s" % (d[0], d[1]) for d in deg) or "none", n_txt,
        ", ".join("…%s %s..%s" % (p[0], p[1], p[2]) for p in con.execute("SELECT account_ref, period_from, period_to FROM icici_statement_period WHERE layout='pipe' ORDER BY account_ref, period_from")) if packs._has(con, "icici_statement_period") else "-"))
    print("  locked files flagged: %d newly (locked now: %d, opened: %d, stored passwords: %d)" % (
        n_lock, con.execute("SELECT COUNT(*) FROM stmt_file WHERE locked=1").fetchone()[0],
        con.execute("SELECT COUNT(*) FROM stmt_file WHERE locked=1 AND unlocked_path IS NOT NULL AND unlocked_path<>''").fetchone()[0], packs._secret_count(con)))
    print("  process_inbox -> %s" % res)
    for m in ("2026-07", "2026-08", "2026-09"):
        print("  grid %s: %s" % (m, " · ".join("%s=%s" % (c["slot"], c["state"]) for c in packs.cells(con, m) if c["kind"] != "card")))
    unpl = [u for u in packs.unplaced(con) if u["folder"] != "all_txn"]
    print("  unplaced now: %d (%d locked, %d of them 'no password')" % (len(unpl), sum(1 for u in unpl if u["locked"]), sum(1 for u in unpl if u.get("no_password"))))
    print("  amir August ready: %s" % packs.amir_pack(con, "2026-08")["ready"])
    con.close()
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
