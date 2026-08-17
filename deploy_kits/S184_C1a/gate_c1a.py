#!/usr/bin/env python3
# =============================================================================
#  gate_c1a.py · kit S184_C1a — state gate + post-verify, READ-ONLY
#
#    python3 gate_c1a.py before   -> OK | ALREADY_APPLIED | WRONG_STATE ... | WRONG_CASH ...
#    python3 gate_c1a.py after    -> OK | BAD ...
#
#  Opens finance.db mode=ro; it can only read. The installer acts on the single
#  word it prints. No PHI is emitted.
# =============================================================================
import sqlite3, sys, os

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
BEFORE_CLOSE_P = -3005600      # -30,056.00, the state we built against
AFTER_CLOSE_P  = 2765400       # +27,654.00 expected after
CASH_TOTAL_P   = 179803300     # 17,98,033.00 day_line cash — invariant
DEP_TOTAL_P    = 164560000     # 16,45,600.00 — 16 Yes Bank deposits
ADV_TOTAL_P    = 4000000       # 40,000.00 advances
REF            = "Yes Bank verified deposit (S184)"
MARK           = "migration.S184_cash_correction"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)

    def one(q, a=()):
        return c.execute(q, a).fetchone()[0]

    marker = c.execute("select value from setting where key=?", (MARK,)).fetchone()
    closing = one("""select closing_p from v_cash_ledger where unit='medical'
                      order by business_date desc, day_entry_id desc limit 1""")
    cash = one("select coalesce(sum(amount_p),0) from day_line where mode='cash'")

    if mode == "before":
        if marker:
            print("ALREADY_APPLIED"); return
        if closing != BEFORE_CLOSE_P:
            print("WRONG_STATE close=%d expected=%d" % (closing, BEFORE_CLOSE_P)); return
        if cash != CASH_TOTAL_P:
            print("WRONG_CASH cash=%d expected=%d" % (cash, CASH_TOTAL_P)); return
        print("OK"); return

    if mode == "after":
        deps = one("select count(*) from cash_movement where reference=?", (REF,))
        depsum = one("""select coalesce(sum(m.amount_p),0) from cash_movement m
                         join day_entry e on e.id=m.day_entry_id
                        where e.unit='medical' and m.party='bank' and m.direction='out'""")
        adj = one("""select count(*) from cash_adjustment a
                      join day_entry e on e.id=a.day_entry_id where e.unit='medical'""")
        bmv = one("select count(*) from s184_removed_movements")
        badj = one("select count(*) from s184_removed_adjustments")
        adv = one("select coalesce(sum(amount_p),0) from day_expense where note like 'S184:%'")
        checks = {
            "marker": (marker and marker[0] == "applied"),
            "closing": closing == AFTER_CLOSE_P,
            "cash_unchanged": cash == CASH_TOTAL_P,
            "16_deposits": deps == 16,
            "deposit_total": depsum == DEP_TOTAL_P,
            "adjustments_gone": adj == 0,
            "backup_movements": bmv == 31,
            "backup_adjustments": badj == 36,
            "advances": adv == ADV_TOTAL_P,
        }
        bad = [k for k, v in checks.items() if not v]
        if bad:
            print("BAD failed=%s close=%d cash=%d deps=%d depsum=%d adj=%d bmv=%d badj=%d adv=%d"
                  % (",".join(bad), closing, cash, deps, depsum, adj, bmv, badj, adv))
        else:
            print("OK")
        return

    print("BAD unknown mode %r" % mode)


if __name__ == "__main__":
    main()
