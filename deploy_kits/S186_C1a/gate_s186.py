#!/usr/bin/env python3
# =============================================================================
#  gate_s186.py  ·  Session 186  ·  the gate for finance_migration_S186_cash_close
#
#  Two modes, run either side of the migration by install_s186.sh:
#
#    --precheck   refuse BEFORE anything is written unless the store is exactly
#                 the store this migration was built against, and print the
#                 numbers we are about to change.
#    --verify     prove AFTER the fact that it changed what it said and nothing
#                 else. A non-zero exit makes the installer restore the backup.
#
#  WHY A SEPARATE GATE AT ALL. The S184 lesson twice over: F-105 (the record was
#  wrong and the running guard was right) and F-106 (a self-test that asserted a
#  DATA STATE and failed the moment the data was legitimately corrected). So this
#  gate asserts INVARIANTS and DELTAS, never absolute balances -- it stays true
#  whatever the store's starting position, and it is the deltas that matter.
#
#  Read-only in both modes. Stdlib only.
# =============================================================================
import argparse, json, os, sqlite3, sys

PHANTOM_P   = 7500000     # Rs 75,000  -- the 13 Aug deposit that never happened
PHANTOM_DAY = '2026-08-13'
PARK_P      = 8720500     # Rs 87,205  -- D323
COUNT_P     = 17519800    # Rs 1,75,198 -- physical, 17 Aug
MARKER      = 'migration.S186_cash_close'

def rs(p): return "Rs %s" % format(p / 100.0, ",.2f")

def snap(cx):
    q = lambda s, *a: cx.execute(s, a).fetchone()[0]
    return {
        "day_line_sum":  q("SELECT COALESCE(SUM(amount_p),0) FROM day_line"),
        "day_line_rows": q("SELECT COUNT(*) FROM day_line"),
        "closing":       q("SELECT COALESCE((SELECT closing_p FROM v_cash_ledger WHERE unit='medical'"
                           " ORDER BY business_date DESC, day_entry_id DESC LIMIT 1),0)"),
        "phantom":       q("SELECT COUNT(*) FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id"
                           " WHERE e.unit='medical' AND e.business_date=? AND m.direction='out'"
                           " AND m.party='bank' AND m.amount_p=?", PHANTOM_DAY, PHANTOM_P),
        "bank_out_n":    q("SELECT COUNT(*) FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id"
                           " WHERE e.unit='medical' AND m.direction='out' AND m.party='bank'"),
        "bank_out_sum":  q("SELECT COALESCE(SUM(m.amount_p),0) FROM cash_movement m JOIN day_entry e"
                           " ON e.id=m.day_entry_id WHERE e.unit='medical' AND m.direction='out'"
                           " AND m.party='bank'"),
        "s186_adj":      q("SELECT COALESCE(SUM(amount_p),0) FROM cash_adjustment WHERE reason LIKE 'S186:%'"),
        "adj_all":       q("SELECT COALESCE(SUM(a.amount_p),0) FROM cash_adjustment a JOIN day_entry e"
                           " ON e.id=a.day_entry_id WHERE e.unit='medical'"),
        "count_17aug":   q("SELECT COALESCE((SELECT counted_p FROM cash_count WHERE unit='medical'"
                           " AND business_date='2026-08-17'),-1)"),
        "neg_open":      q("SELECT COUNT(*) FROM recon_exception WHERE unit='medical'"
                           " AND kind='negative_cash' AND status='open'"),
        "expense_sum":   q("SELECT COALESCE(SUM(x.amount_p),0) FROM day_expense x JOIN day_entry e"
                           " ON e.id=x.day_entry_id WHERE e.unit='medical'"),
        "marker":        q("SELECT COALESCE((SELECT value FROM setting WHERE key=?),'')", MARKER),
    }

def precheck(cx):
    s = snap(cx); ok, bad = 0, []
    def chk(label, cond, detail=""):
        nonlocal ok
        if cond: ok += 1; print("   OK   %s" % label)
        else: bad.append(label); print("   FAIL %s   %s" % (label, detail))
    print("\n-- PRECHECK: is this the store S186_C1a was built against?\n")
    chk("migration not already applied", s["marker"] != 'applied', "marker=%r" % s["marker"])
    chk("the phantom 13 Aug deposit is present, exactly once",
        s["phantom"] == 1, "found %d rows of %s on %s" % (s["phantom"], rs(PHANTOM_P), PHANTOM_DAY))
    chk("no S186 adjustment exists yet", s["s186_adj"] == 0, "found %s" % rs(s["s186_adj"]))
    chk("the medical unit has sale money to protect", s["day_line_sum"] > 0)
    print("\n-- what this migration will change:")
    print("   medical bank-out deposits : %d rows, %s" % (s["bank_out_n"], rs(s["bank_out_sum"])))
    print("   -> after                  : %d rows, %s" % (s["bank_out_n"]-1, rs(s["bank_out_sum"]-PHANTOM_P)))
    print("   medical cash adjustments  : %s  ->  %s" % (rs(s["adj_all"]), rs(s["adj_all"]+PARK_P)))
    print("   latest medical closing    : %s  ->  %s" % (rs(s["closing"]), rs(s["closing"]+PHANTOM_P+PARK_P)))
    print("   open negative_cash shouts : %d  (recomputed after)" % s["neg_open"])
    print()
    json.dump(s, open(os.environ.get("S186_SNAP", "/tmp/s186_before.json"), "w"))
    if bad:
        print("!! PRECHECK RED — %d check(s) failed. Nothing has been written.\n" % len(bad)); return 1
    print("-- precheck green (%d/%d)\n" % (ok, ok)); return 0

def verify(cx):
    before = json.load(open(os.environ.get("S186_SNAP", "/tmp/s186_before.json")))
    a = snap(cx); ok, bad = 0, []
    def chk(label, cond, detail=""):
        nonlocal ok
        if cond: ok += 1; print("   OK   %s" % label)
        else: bad.append(label); print("   FAIL %s   %s" % (label, detail))
    print("\n-- VERIFY: did it change exactly what it said, and nothing else?\n")
    chk("day_line (the sale money) BYTE-UNCHANGED — sum",
        a["day_line_sum"] == before["day_line_sum"],
        "%s -> %s" % (rs(before["day_line_sum"]), rs(a["day_line_sum"])))
    chk("day_line row count unchanged", a["day_line_rows"] == before["day_line_rows"])
    chk("expenses untouched (the advances go through the APP, not here)",
        a["expense_sum"] == before["expense_sum"])
    chk("the phantom deposit is gone", a["phantom"] == 0)
    chk("exactly ONE bank deposit removed", a["bank_out_n"] == before["bank_out_n"] - 1,
        "%d -> %d" % (before["bank_out_n"], a["bank_out_n"]))
    chk("deposits total fell by exactly Rs 75,000",
        a["bank_out_sum"] == before["bank_out_sum"] - PHANTOM_P,
        "%s -> %s" % (rs(before["bank_out_sum"]), rs(a["bank_out_sum"])))
    def rows(tbl):
        try: return cx.execute("SELECT COUNT(*) FROM %s" % tbl).fetchone()[0]
        except sqlite3.OperationalError: return -1      # table absent = not applied
    chk("the removed row is backed up and restorable", rows("s186_removed_movements") == 1,
        "backup table rows=%d" % rows("s186_removed_movements"))
    chk("parked exactly Rs 87,205, once", a["s186_adj"] == PARK_P, rs(a["s186_adj"]))
    chk("the park is APPROVED and reasoned",
        cx.execute("SELECT COUNT(*) FROM cash_adjustment WHERE reason LIKE 'S186:%'"
                   " AND status='approved' AND approved_by IS NOT NULL"
                   " AND LENGTH(explanation) > 200").fetchone()[0] == 1)
    chk("cash adjustments rose by exactly the parked figure",
        a["adj_all"] == before["adj_all"] + PARK_P)
    chk("closing rose by exactly Rs 75,000 + Rs 87,205 = Rs 1,62,205",
        a["closing"] == before["closing"] + PHANTOM_P + PARK_P,
        "%s -> %s" % (rs(before["closing"]), rs(a["closing"])))
    chk("the 17 Aug physical count is recorded", a["count_17aug"] == COUNT_P, rs(a["count_17aug"]))
    chk("negative_cash recomputed from the live ledger — no stale shout survives",
        a["neg_open"] == cx.execute("SELECT COUNT(*) FROM v_cash_ledger WHERE unit='medical'"
                                    " AND closing_p < 0").fetchone()[0],
        "open=%d, genuinely negative days=%d" % (a["neg_open"],
        cx.execute("SELECT COUNT(*) FROM v_cash_ledger WHERE unit='medical' AND closing_p<0").fetchone()[0]))
    chk("marker written", a["marker"] == 'applied')
    print("\n   open negative_cash shouts : %d  ->  %d" % (before["neg_open"], a["neg_open"]))
    print("   latest medical closing    : %s  ->  %s\n" % (rs(before["closing"]), rs(a["closing"])))
    if bad:
        print("!! VERIFY RED — %d check(s) failed. The installer will RESTORE the backup.\n" % len(bad)); return 1
    print("-- verify green (%d/%d)\n" % (ok, ok)); return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db"); ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--verify", action="store_true")
    g = ap.parse_args()
    if not (g.precheck ^ g.verify): ap.error("give exactly one of --precheck / --verify")
    if not os.path.isfile(g.db): sys.stderr.write("!! no such database: %s\n" % g.db); return 2
    cx = sqlite3.connect("file:%s?mode=ro" % g.db, uri=True)
    try: return precheck(cx) if g.precheck else verify(cx)
    finally: cx.close()

if __name__ == "__main__":
    sys.exit(main())
