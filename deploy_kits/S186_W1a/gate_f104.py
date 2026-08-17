#!/usr/bin/env python3
# =============================================================================
#  gate_f104.py · Session 186 · the gate for the WALK-IN reclass (F-104)
#
#  --precheck  PROJECTS the after-state before a single row is written: how many
#              days are flagged now, and how many WOULD be flagged after. If the
#              reclass would leave more shouting than it silences, you see that
#              here, not afterwards. (The S184_S1a discipline: survey the box
#              before writing to it.)
#  --verify    proves it changed only attribution and that THE MONEY DID NOT
#              MOVE. day_line is asserted byte-unchanged by sum and row count.
#
#  Asserts deltas and invariants, never absolute balances (F-106).
#  Read-only in both modes. Stdlib only.
# =============================================================================
import argparse, json, os, sqlite3, sys

MARKER = "migration.S186_walkin"

def rs(p): return "Rs %s" % format((p or 0) / 100.0, ",.2f")

def tol(cx):
    r = cx.execute("SELECT value FROM setting WHERE key='ingest.attribution_tolerance_p'").fetchone()
    try: return int(r[0]) if r else 10000
    except (TypeError, ValueError): return 10000

def snap(cx):
    q = lambda s, *a: cx.execute(s, *a).fetchone()[0] if a else cx.execute(s).fetchone()[0]
    t = tol(cx)
    return {
        "day_line_sum":  q("SELECT COALESCE(SUM(amount_p),0) FROM day_line"),
        "day_line_rows": q("SELECT COUNT(*) FROM day_line"),
        "cash_close":    q("SELECT COALESCE((SELECT closing_p FROM v_cash_ledger WHERE unit='medical'"
                           " ORDER BY business_date DESC, day_entry_id DESC LIMIT 1),0)"),
        "review_open":   q("SELECT COUNT(*) FROM sale_item_review r JOIN day_entry e"
                           " ON e.id=r.day_entry_id WHERE e.unit='medical' AND r.status='open'"),
        "review_open_p": q("SELECT COALESCE(SUM(r.amount_p),0) FROM sale_item_review r JOIN day_entry e"
                           " ON e.id=r.day_entry_id WHERE e.unit='medical' AND r.status='open'"),
        "walkin_items":  q("SELECT COUNT(*) FROM sale_item WHERE source_ref LIKE 'S186-F104-%'"),
        "sale_items":    q("SELECT COUNT(*) FROM sale_item WHERE unit='medical'"),
        "flagged":       q("SELECT COUNT(*) FROM recon_exception WHERE unit='medical'"
                           " AND kind='line_sum_vs_day_total' AND status='open'"),
        "walkin_id":     (cx.execute("SELECT id FROM patient_ref WHERE clinic_id='WALK-IN'").fetchone()
                          or [None])[0],
        "marker":        (cx.execute("SELECT value FROM setting WHERE key=?", (MARKER,)).fetchone()
                          or [""])[0],
        "tol":           t,
    }

def project(cx):
    """What the flag count becomes if every open review row is attributed."""
    t = tol(cx)
    rows = cx.execute(
        "SELECT a.business_date, a.day_total_p, a.attributed_p,"
        "  COALESCE((SELECT SUM(r.amount_p) FROM sale_item_review r"
        "             WHERE r.day_entry_id=a.day_entry_id AND r.status='open'),0) rev"
        " FROM v_day_attribution a WHERE a.unit='medical'").fetchall()
    after, worse = 0, []
    for d, tot, att, rev in rows:
        new = tot - (att + rev)
        if abs(new) > t:
            after += 1
            if abs(new) > abs(tot - att):
                worse.append((d, tot - att, new))
    return after, worse, len(rows)

def precheck(cx):
    s = snap(cx); ok, bad = 0, []
    def chk(l, c, d=""):
        nonlocal ok
        if c: ok += 1; print("   OK   %s" % l)
        else: bad.append(l); print("   FAIL %s   %s" % (l, d))
    print("\n-- PRECHECK: survey the box, then project the result\n")
    chk("migration not already applied", s["marker"] != "applied", "marker=%r" % s["marker"])
    chk("the reserved WALK-IN patient exists", s["walkin_id"] is not None)
    chk("there are open review rows to reclassify", s["review_open"] > 0,
        "found %d" % s["review_open"])
    chk("no S186-F104 rows exist yet", s["walkin_items"] == 0, "found %d" % s["walkin_items"])
    after, worse, days = project(cx)
    print("\n-- what this will do:")
    print("   open review rows        : %d   %s" % (s["review_open"], rs(s["review_open_p"])))
    print("   days flagged NOW        : %d  (of %d medical days)" % (s["flagged"], days))
    print("   days flagged AFTER      : %d      <-- projected, before anything is written" % after)
    print("   tolerance in use        : %s per day" % rs(s["tol"]))
    if worse:
        print("\n   !! %d day(s) would end up FURTHER from balanced than they are now:" % len(worse))
        for d, before, aft in worse[:10]:
            print("        %s  gap %s  ->  %s" % (d, rs(before), rs(aft)))
        print("      (these are days whose Marg lines EXCEED the declared day total —")
        print("       a real discrepancy, surfaced rather than buried.)")
    print()
    json.dump(dict(s, projected_after=after, projected_worse=len(worse)),
              open(os.environ.get("F104_SNAP", "/tmp/f104_before.json"), "w"))
    if bad:
        print("!! PRECHECK RED — %d check(s) failed. Nothing written.\n" % len(bad)); return 1
    print("-- precheck green (%d/%d)\n" % (ok, ok)); return 0

def verify(cx):
    b = json.load(open(os.environ.get("F104_SNAP", "/tmp/f104_before.json")))
    a = snap(cx); ok, bad = 0, []
    def chk(l, c, d=""):
        nonlocal ok
        if c: ok += 1; print("   OK   %s" % l)
        else: bad.append(l); print("   FAIL %s   %s" % (l, d))
    print("\n-- VERIFY: attribution moved, money did not\n")
    chk("day_line (the sale money) BYTE-UNCHANGED — sum",
        a["day_line_sum"] == b["day_line_sum"],
        "%s -> %s" % (rs(b["day_line_sum"]), rs(a["day_line_sum"])))
    chk("day_line row count unchanged", a["day_line_rows"] == b["day_line_rows"])
    chk("cash in hand UNCHANGED — this kit touches no money",
        a["cash_close"] == b["cash_close"],
        "%s -> %s" % (rs(b["cash_close"]), rs(a["cash_close"])))
    chk("every open review row was reclassified", a["review_open"] == 0,
        "%d still open" % a["review_open"])
    chk("one WALK-IN line created per review row",
        a["walkin_items"] == b["review_open"],
        "%d created for %d rows" % (a["walkin_items"], b["review_open"]))
    chk("sale_item grew by exactly that many",
        a["sale_items"] == b["sale_items"] + b["review_open"])
    chk("the originals are backed up and restorable",
        cx.execute("SELECT COUNT(*) FROM s186_f104_reviews").fetchone()[0] == b["review_open"])
    chk("every new line is attributed to WALK-IN, none guessed at a name",
        cx.execute("SELECT COUNT(*) FROM sale_item WHERE source_ref LIKE 'S186-F104-%'"
                   " AND patient_ref_id <> ?", (b["walkin_id"],)).fetchone()[0] == 0)
    chk("the reclass is marked as a human ruling, not an OCR reading",
        cx.execute("SELECT COUNT(*) FROM sale_item WHERE source_ref LIKE 'S186-F104-%'"
                   " AND source <> 'manual'").fetchone()[0] == 0)
    chk("flags fell to the projected number, not to a hoped-for one",
        a["flagged"] == b["projected_after"],
        "%d flagged, %d projected" % (a["flagged"], b["projected_after"]))
    chk("the shout was recomputed from the live view, not assumed clean",
        a["flagged"] == cx.execute(
            "SELECT COUNT(*) FROM v_day_attribution WHERE unit='medical'"
            " AND ABS(day_total_p-attributed_p) > ?", (a["tol"],)).fetchone()[0])
    chk("marker written", a["marker"] == "applied")
    print("\n   review queue     : %d  ->  %d" % (b["review_open"], a["review_open"]))
    print("   days flagged     : %d  ->  %d" % (b["flagged"], a["flagged"]))
    print("   cash in hand     : %s  (unchanged)\n" % rs(a["cash_close"]))
    if bad:
        print("!! VERIFY RED — %d check(s) failed. The installer will RESTORE.\n" % len(bad)); return 1
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
