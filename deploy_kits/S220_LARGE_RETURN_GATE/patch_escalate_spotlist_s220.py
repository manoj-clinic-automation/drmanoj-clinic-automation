#!/usr/bin/env python3
"""
patch_escalate_spotlist_s220.py -- S220 item 1, part 2 of 3: THE SPOT-COUNT LIST.

The owner (02-Sep): "stock checking is suspended due to other compulsions...
random stock checks of the items which we flag could be a deterrent."

finance_returns_escalate.py (pin 35ad7595) already runs at the two right
moments -- after every Apply, and hourly from the watchdog -- and never on a
page load. It gains ONE duty: for every return of the day that is LARGE
(returns.large_p, Rs 1,000) or carries a MONEY verdict, put the items of that
credit note on `stock_spot_check`, once (UNIQUE per bill + item), status
'due'. Nothing is judged; a person counts, and records what was counted on
the owner's card (darpan_app, part 1). Fail-soft: a database that cannot take
the rows leaves the escalation exactly as it was.

TWO anchored changes, sliced verbatim from the live bytes:
  A  `spot_list_day()` before `flagged_rows()`.
  B  one call inside `escalate_day()`, before the flags are read -- and BEFORE
     the historical short-circuit is passed, so D361 holds: nothing before
     returns.act_from is ever listed.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_escalate_spotlist_s220.py
Offline: FRE_PATH=/path/to/finance_returns_escalate.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('FRE_PATH', '/root/finance/finance_returns_escalate.py')
MARK = 'S220 SPOT-COUNT'

A_OLD = 'def flagged_rows(rows):\n'

A_NEW = '''import datetime as dt                                   # S220 SPOT-COUNT

SPOT_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS stock_spot_check ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " bill_no TEXT NOT NULL, item_key TEXT NOT NULL, item_name TEXT, batch TEXT,"
    " reason TEXT NOT NULL, requested_at TEXT NOT NULL,"
    " status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','done','skipped')),"
    " counted_qty TEXT, counted_by TEXT, counted_at TEXT, note TEXT,"
    " UNIQUE(unit, bill_no, item_key))")


def large_p(con):
    """returns.large_p -- the owner's line for a return that needs his OK."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='returns.large_p'").fetchone()
        return int((r[0] if r else "") or 100000)
    except Exception:                                        # noqa: BLE001
        return 100000


def spot_list_day(con, iso, unit, rows):
    """S220 SPOT-COUNT: the items of every LARGE or MONEY-FLAGGED return of the
    day go on the spot-count list, once. Returns the number of rows added.
    Never raises; never touches a row already there (a count already made is
    never re-asked)."""
    try:
        con.execute(SPOT_SCHEMA)
        big = large_p(con)
        added = 0
        now = dt.datetime.now().replace(microsecond=0).isoformat()
        for r in rows:
            v = r.get("verdict")
            amt = int(r.get("amount_p") or 0)
            if amt >= big:
                reason = "large return (Rs %s)" % "{:,.0f}".format(amt / 100.0)
            elif v in MONEY_FLAGS:
                reason = v
            else:
                continue
            bill = r.get("bill")
            if not bill:
                continue
            for ln in con.execute(
                    "SELECT item_key, item_name, batch FROM sale_line_item "
                    "WHERE unit=? AND bill_no=? AND is_return=1 ORDER BY seq",
                    (unit, bill)).fetchall():
                cur = con.execute(
                    "INSERT OR IGNORE INTO stock_spot_check (unit, business_date, bill_no, "
                    "item_key, item_name, batch, reason, requested_at, status) "
                    "VALUES (?,?,?,?,?,?,?,?, 'due')",
                    (unit, iso, bill, ln[0], ln[1], ln[2], reason, now))
                added += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        return added
    except Exception:                                        # noqa: BLE001
        return 0


def flagged_rows(rows):
'''

B_OLD = '    bad = flagged_rows(rows)\n    cur = con.execute(\n        "SELECT id, status, detail FROM recon_exception "\n'

B_NEW = ('    # S220 SPOT-COUNT: list the items a person should count -- the deterrent.\n'
         '    spot_list_day(con, iso, unit, rows)\n'
         '    bad = flagged_rows(rows)\n    cur = con.execute(\n        "SELECT id, status, detail FROM recon_exception "\n')

PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_large_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s -- the live file is unchanged." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
