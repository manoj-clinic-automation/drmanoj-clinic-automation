#!/usr/bin/python3
"""make_s399.py -- builds day_resync.py S399 from the live S367 bytes (ddbb12eb) by anchored edits.
Each anchor must occur exactly once or the build stops."""
import hashlib, sys
FROM = "ddbb12eb7835b29d44804105432e19a7"
src = open(sys.argv[1], "rb").read()
assert hashlib.md5(src).hexdigest() == FROM, "not the S367 file"
s = src.decode("utf-8")

def rep(old, new):
    global s
    n = s.count(old)
    assert n == 1, "anchor found %d times: %r" % (n, old[:60])
    s = s.replace(old, new)

rep('"""day_resync.py -- S367_DAY_TRUTH_4 (S355 -> S356 -> S357 -> this)',
    '"""day_resync.py -- S399_DAY_TRUTH_5 (S355 -> S356 -> S357 -> S367 -> this)')
rep("""S367 (F-613, the owner's ruling D602 of 22-Sep-2026)""",
    """S399 (F-632, the owner 25-Sep-2026: "a procedure sale ... was not picked up as non-cash")
    A003806 of 23-Sep, "PROSIJER <patient>", Rs 195 cash.  The ingest's lookup ladder (S221,
    rung 'same-day visit') found the patient, so the bill went to sale_item -- which keeps no
    customer text -- and never to the review queue.  Pass 2 read Darpan's label words ONLY from
    the review queue, so it never saw the bill and the day's cash read 195 too high.  The ingest
    DOES keep the bill's own text for every bill it laddered (identity_resolution.bill_name) and
    every bill whose name disagreed with its clinic ID (identity_dispute.bill_name).  Pass 2 now
    reads the label words there too.  An APPROVED day holding a label bill with no deduction is
    named (never touched) -- a person corrects it visibly.

S367 (F-613, the owner's ruling D602 of 22-Sep-2026)""")
rep('KIT = "S367_DAY_TRUTH_4"', 'KIT = "S399_DAY_TRUTH_5"')
rep('''            out.append((bill, bdate, head, amt, "review"))
''', '''            out.append((bill, bdate, head, amt, "review"))
    # S399 (F-632): a label bill the ingest attached to a patient -- by the lookup ladder
    # (identity_resolution) or by a clinic ID whose name disagreed (identity_dispute) --
    # never reaches the review queue; its own text is kept in those two tables.
    for tbl in ("identity_resolution", "identity_dispute"):
        if not _has(con, tbl):
            continue
        for r in con.execute("SELECT bill_no, bill_name FROM %s WHERE unit=? AND business_date=? "
                             "ORDER BY id" % tbl, (UNIT, iso)):
            head = head_for(r["bill_name"], home_w, proc_w)
            bill = str(r["bill_no"] or "").strip()
            if not head or not bill or (bill, iso) in seen:
                continue
            amt = None
            if _has(con, "sale_bill"):
                b = con.execute("SELECT net_p FROM sale_bill WHERE unit=? AND business_date=? AND bill_no=?",
                                (UNIT, iso, bill)).fetchone()
                if b is not None:
                    amt = int(b[0] or 0)
            if amt is None:
                b = con.execute("SELECT amount_p, service FROM sale_item WHERE day_entry_id=? AND source_ref=? "
                                "ORDER BY id DESC LIMIT 1", (eid, bill)).fetchone()
                if b is None:
                    continue
                amt = -int(b[0] or 0) if "return" in (b[1] or "") else int(b[0] or 0)
            seen.add((bill, iso))
            out.append((bill, iso, head, amt, tbl.split("_")[1]))
''')
rep('''def noncash_candidates(con, since):''', '''def approved_label_missing(con, since, home_w, proc_w):
    """S399: approved / locked pharmacy days holding a label bill that carries no deduction --
    named, never touched (the same rule as approved_differs)."""
    out = []
    for e in con.execute("SELECT id, business_date, status FROM day_entry WHERE unit=? AND business_date>=? "
                         "AND status NOT IN ('submitted','draft') ORDER BY business_date", (UNIT, since)).fetchall():
        for bill, bdate, head, amt, where in label_bills(con, e, home_w, proc_w):
            if amt <= 0:
                continue
            if con.execute("SELECT 1 FROM day_noncash_bill WHERE unit=? AND bill_no=? AND bill_date=?",
                           (UNIT, bill, bdate)).fetchone():
                continue
            if _has(con, "cash_bill_ruling") and con.execute(
                    "SELECT 1 FROM cash_bill_ruling WHERE unit=? AND bill_no=?", (UNIT, bill)).fetchone():
                continue
            out.append("%s  APPROVED; %s %s %s has no deduction -- a person corrects it" % (
                e["business_date"], bill, head.replace("_", " "), rupees(amt)))
    return out


def noncash_candidates(con, since):''')
rep('''    print("summary2: " +''', '''    for line in approved_label_missing(con, a.since, home_w, proc_w):
        print("  %-9s %s" % ("APPROVED", line))
    print("summary2: " +''')
rep("""    found in the review queue where the ingest parks a bill with no ID and
    no phone, or tagged home_med by the ingest -- becomes one""",
    """    found in the review queue where the ingest parks a bill with no ID and
    no phone, in the bill text the ingest keeps for a bill it laddered or
    name-checked (S399), or tagged home_med by the ingest -- becomes one""")
open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("built", sys.argv[2], hashlib.md5(s.encode("utf-8")).hexdigest())
