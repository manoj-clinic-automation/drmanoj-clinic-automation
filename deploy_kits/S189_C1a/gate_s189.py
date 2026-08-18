#!/usr/bin/env python3
# =============================================================================
#  gate_s189.py  ·  Session 189  ·  the gate for finance_migration_S189_custody
#
#    --precheck   refuse BEFORE anything is written unless the store is the one
#                 this migration was built against, and print what will change.
#    --verify     prove AFTER the fact that it changed what it said and NOTHING
#                 else. A non-zero exit makes the installer restore the backup.
#
#  It asserts INVARIANTS and DELTAS, never absolute balances (F-106): a gate
#  that asserts a store state goes red the moment the data is legitimately
#  corrected, and then the gate is what gets disabled.
#
#  THE INVARIANT THAT MATTERS MOST is that cash in hand does not move. Custody
#  is location. If the ledger shifts by a single paisa this returns non-zero and
#  the installer puts the books back.
#
#  Read-only in both modes. Stdlib only.
# =============================================================================
import argparse, json, os, sqlite3, sys

UNIT      = 'medical'
MANOJ_P   = 1896300      # Rs   18,963
BHAWNA_P  = 15623500     # Rs 1,56,235  = 730900 + 392600 + 14500000
TOTAL_P   = MANOJ_P + BHAWNA_P            # Rs 1,75,198
COUNT_DAY = '2026-08-17'
MARKER    = 'migration.S189_custody'
SNAP      = os.environ.get('S189_SNAP', '/tmp/s189_before.json')


def rs(p):
    return "Rs %s" % format(p / 100.0, ",.2f")


def custody(cx, party):
    """Net held by a party, all time -- to_party in, from_party out."""
    a = cx.execute("SELECT COALESCE(SUM(amount_p),0) FROM cash_custody_event "
                   "WHERE unit=? AND to_party=?", (UNIT, party)).fetchone()[0]
    b = cx.execute("SELECT COALESCE(SUM(amount_p),0) FROM cash_custody_event "
                   "WHERE unit=? AND from_party=?", (UNIT, party)).fetchone()[0]
    return a - b


def snap(cx):
    q = lambda s, *a: cx.execute(s, a).fetchone()[0]
    return {
        # the money -- every one of these must be IDENTICAL afterwards
        "day_line_sum":   q("SELECT COALESCE(SUM(amount_p),0) FROM day_line"),
        "day_line_rows":  q("SELECT COUNT(*) FROM day_line"),
        "movement_rows":  q("SELECT COUNT(*) FROM cash_movement"),
        "movement_sum":   q("SELECT COALESCE(SUM(amount_p),0) FROM cash_movement"),
        "adjust_sum":     q("SELECT COALESCE(SUM(amount_p),0) FROM cash_adjustment"),
        "expense_sum":    q("SELECT COALESCE(SUM(amount_p),0) FROM day_expense"),
        "ledger_net":     q("SELECT COALESCE(SUM(net_p),0) FROM v_cash_ledger WHERE unit=?", UNIT),
        "closing":        q("SELECT COALESCE((SELECT closing_p FROM v_cash_ledger WHERE unit=? "
                            "ORDER BY business_date DESC, day_entry_id DESC LIMIT 1),0)", UNIT),
        # the thing that is allowed to change
        "custody_rows":   q("SELECT COUNT(*) FROM cash_custody_event WHERE unit=?", UNIT),
        "manoj":          custody(cx, 'dr_manoj'),
        "bhawna":         custody(cx, 'dr_bhawna'),
    }


def precheck(cx):
    bad = []
    if cx.execute("SELECT COUNT(*) FROM setting WHERE key=?", (MARKER,)).fetchone()[0]:
        bad.append("marker %s already present -- this migration has been applied" % MARKER)

    n = cx.execute("SELECT COUNT(*) FROM cash_custody_event WHERE unit=? AND "
                   "note LIKE 'S189 (F-137).%'", (UNIT,)).fetchone()[0]
    if n:
        bad.append("%d S189 custody rows already exist -- refusing to double-enter" % n)

    row = cx.execute("SELECT counted_p, business_date FROM cash_count WHERE unit=? AND "
                     "business_date=?", (UNIT, COUNT_DAY)).fetchone()
    if not row:
        bad.append("no cash_count row for %s -- this migration exists to record THAT "
                   "count and refuses without it" % COUNT_DAY)
    elif row[0] != TOTAL_P:
        bad.append("the %s count is %s but this migration totals %s -- they must agree "
                   "to the paise" % (COUNT_DAY, rs(row[0]), rs(TOTAL_P)))

    for who in ('Vinay Saxena', 'Darpan'):
        if not cx.execute("SELECT 1 FROM counter_person WHERE unit=? AND name=?",
                          (UNIT, who)).fetchone():
            bad.append("counter_person '%s' missing -- the rows would attribute to NULL" % who)

    s = snap(cx)
    print("-- PRECHECK, read-only")
    print("   cash in hand now          : %s   <- MUST NOT CHANGE" % rs(s["closing"]))
    print("   custody rows now          : %d" % s["custody_rows"])
    print("   held by Dr Manoj  now     : %s" % rs(s["manoj"]))
    print("   held by Dr Bhawna now     : %s" % rs(s["bhawna"]))
    print("")
    print("   THE PROJECTION -- written before anything is measured again:")
    print("     + 4 custody rows")
    print("     Dr Manoj   %s -> %s" % (rs(s["manoj"]),  rs(s["manoj"] + MANOJ_P)))
    print("     Dr Bhawna  %s -> %s" % (rs(s["bhawna"]), rs(s["bhawna"] + BHAWNA_P)))
    print("     their total                %s  = the counted position" % rs(TOTAL_P))
    print("     cash in hand   %s -> %s   UNCHANGED" % (rs(s["closing"]), rs(s["closing"])))
    print("     day_line, cash_movement, cash_adjustment, day_expense  ALL UNCHANGED")
    if bad:
        print("")
        for b in bad:
            print("!! %s" % b)
        return 1
    with open(SNAP, "w") as fh:
        json.dump(s, fh)
    print("")
    print("   precheck GREEN -- snapshot written to %s" % SNAP)
    return 0


def verify(cx):
    try:
        before = json.load(open(SNAP))
    except (OSError, ValueError) as e:
        print("!! cannot read the pre-migration snapshot %s (%s)" % (SNAP, e))
        return 1
    after = snap(cx)
    bad = []

    # 1. nothing about the MONEY moved
    for k in ("day_line_sum", "day_line_rows", "movement_rows", "movement_sum",
              "adjust_sum", "expense_sum", "ledger_net", "closing"):
        if before[k] != after[k]:
            bad.append("%s changed: %s -> %s  (this migration must not touch it)"
                       % (k, before[k], after[k]))

    # 2. exactly what was promised WAS added
    if after["custody_rows"] - before["custody_rows"] != 4:
        bad.append("custody rows moved by %d, expected exactly 4"
                   % (after["custody_rows"] - before["custody_rows"]))
    if after["manoj"] - before["manoj"] != MANOJ_P:
        bad.append("Dr Manoj delta %s, expected %s"
                   % (rs(after["manoj"] - before["manoj"]), rs(MANOJ_P)))
    if after["bhawna"] - before["bhawna"] != BHAWNA_P:
        bad.append("Dr Bhawna delta %s, expected %s"
                   % (rs(after["bhawna"] - before["bhawna"]), rs(BHAWNA_P)))

    # 3. it ties to the count, which is the whole point
    row = cx.execute("SELECT counted_p FROM cash_count WHERE unit=? AND business_date=?",
                     (UNIT, COUNT_DAY)).fetchone()
    delta_total = (after["manoj"] - before["manoj"]) + (after["bhawna"] - before["bhawna"])
    if not row or delta_total != row[0]:
        bad.append("what was entered (%s) does not equal the %s physical count (%s)"
                   % (rs(delta_total), COUNT_DAY, rs(row[0]) if row else "absent"))

    # 4. every row attributes to a real person and carries its reasoning
    n_null = cx.execute("SELECT COUNT(*) FROM cash_custody_event WHERE unit=? AND "
                        "note LIKE 'S189 (F-137).%' AND counter_person_id IS NULL",
                        (UNIT,)).fetchone()[0]
    if n_null:
        bad.append("%d of the new rows attribute to no counter_person" % n_null)

    if not cx.execute("SELECT 1 FROM setting WHERE key=?", (MARKER,)).fetchone():
        bad.append("marker %s was not written" % MARKER)

    print("-- VERIFY")
    print("   cash in hand   %s -> %s   %s"
          % (rs(before["closing"]), rs(after["closing"]),
             "UNCHANGED, as promised" if before["closing"] == after["closing"] else "*** MOVED ***"))
    print("   custody rows   %d -> %d" % (before["custody_rows"], after["custody_rows"]))
    print("   Dr Manoj       %s -> %s" % (rs(before["manoj"]), rs(after["manoj"])))
    print("   Dr Bhawna      %s -> %s" % (rs(before["bhawna"]), rs(after["bhawna"])))
    print("   entered total  %s   vs the 17 Aug count %s"
          % (rs(delta_total), rs(row[0]) if row else "absent"))
    if bad:
        print("")
        for b in bad:
            print("!! %s" % b)
        return 1
    print("")
    print("   verify GREEN -- location recorded, not one paisa moved")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    cx = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    try:
        return precheck(cx) if a.precheck else verify(cx)
    finally:
        cx.close()


if __name__ == "__main__":
    sys.exit(main())
