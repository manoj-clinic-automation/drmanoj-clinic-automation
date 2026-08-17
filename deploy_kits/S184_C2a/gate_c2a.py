#!/usr/bin/env python3
# gate_c2a.py · kit S184_C2a — state gate + post-verify, READ-ONLY.
#   python3 gate_c2a.py before  -> OK | NEED_C1A | ALREADY_APPLIED
#   python3 gate_c2a.py after   -> OK | BAD ...
import sqlite3, sys, os
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
C1A = "migration.S184_cash_correction"
C2A = "migration.S184_C2a_exceptions"

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    def one(q, a=()): return c.execute(q, a).fetchone()[0]
    c1a = c.execute("select 1 from setting where key=?", (C1A,)).fetchone()
    c2a = c.execute("select 1 from setting where key=?", (C2A,)).fetchone()

    if mode == "before":
        if not c1a: print("NEED_C1A")
        elif c2a:   print("ALREADY_APPLIED")
        else:       print("OK")
        return

    if mode == "after":
        cfb_open = one("select count(*) from recon_exception where unit='medical' and kind='carry_forward_break' and status='open'")
        neg_open = one("select count(*) from recon_exception where unit='medical' and kind='negative_cash' and status='open'")
        neg_live = one("select count(*) from v_cash_ledger where unit='medical' and closing_p<0")
        marker = c.execute("select value from setting where key=?", (C2A,)).fetchone()
        checks = {
            "marker": marker and marker[0] == "applied",
            "carry_forward_cleared": cfb_open == 0,
            "negative_cash_matches_ledger": neg_open == neg_live,
        }
        bad = [k for k, v in checks.items() if not v]
        print("OK" if not bad else "BAD failed=%s cfb_open=%d neg_open=%d neg_live=%d"
              % (",".join(bad), cfb_open, neg_open, neg_live))
        return
    print("BAD unknown mode %r" % mode)

if __name__ == "__main__":
    main()
