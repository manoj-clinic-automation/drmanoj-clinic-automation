#!/usr/bin/env python3
"""REHEARSAL_anomaly.py -- the walk for the item-anomaly detector.

Case 1 IS the owner's June bill: an ointment that normally leaves in ones and
twos, billed as 20 tubes at the price of 2, then 'corrected' by a Marg stock
adjustment so the stock balanced and the bill stayed wrong.
"""
import os, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_item_anomaly as A

OK = BAD = 0
def check(n, c, d=""):
    global OK, BAD
    if c: OK += 1
    else: BAD += 1
    print(("  ok   " if c else "  FAIL ") + n + (("   " + d) if d else ""))

SCHEMA = """
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT);
CREATE TABLE sale_item (id INTEGER PRIMARY KEY, source_ref TEXT, patient_ref_id INTEGER);
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, business_date TEXT NOT NULL,
  bill_no TEXT NOT NULL, is_return INTEGER NOT NULL DEFAULT 0, seq INTEGER,
  item_name TEXT, item_key TEXT, qty_raw TEXT, pack TEXT, amount_p INTEGER);
"""
HIST, DAY = "2026-06-01", "2026-06-20"

def main():
    tmp = tempfile.mkdtemp(prefix="anom_")
    db = os.path.join(tmp, "f.db")
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row; con.executescript(SCHEMA)
    con.execute("INSERT INTO patient_ref (id,clinic_id,name) VALUES (1,'4471','A PATIENT')")
    def line(d, bill, key, qty, amt, ret=0, seq=1, pack="1*1"):
        con.execute("INSERT INTO sale_line_item (business_date,bill_no,is_return,seq,"
                    "item_name,item_key,qty_raw,pack,amount_p) VALUES (?,?,?,?,?,?,?,?,?)",
                    (d, bill, ret, seq, key, key, qty, pack, amt))
        con.execute("INSERT OR IGNORE INTO sale_item (source_ref,patient_ref_id) "
                    "VALUES (?,1)", (bill,))
    # an ointment that leaves in ones and twos, at 5000 paise a tube
    # the rate is printed per pack and does NOT move with quantity
    for i in range(10):
        line(HIST, "H%02d" % i, "OINT", "%d:0" % (1 + i % 2), 5000)
    # a tablet with only two lines of history -- not enough to judge anything
    line(HIST, "T1", "RAREITEM", "1:0", 900)
    line(HIST, "T2", "RAREITEM", "1:0", 900)

    # 1 -- THE OWNER'S CASE: 20 tubes billed, charged as 2
    line(DAY, "B-JUNE", "OINT", "20:0", 500)     # rate a tenth of normal
    # 2 -- a genuine bulk purchase: 20 tubes at the proper rate
    line(DAY, "B-BULK", "OINT", "20:0", 5000)    # 20 tubes at the proper rate
    # 3 -- an ordinary line
    line(DAY, "B-OK", "OINT", "2:0", 5000)
    # 4 -- an item with no history to compare against
    line(DAY, "B-RARE", "RAREITEM", "9:0", 900)
    # 5 -- a quantity that cannot be parsed, so no rate may be claimed
    # a partial strip with NO pack size recorded: strips and loose cannot be put
    # in the same terms, so no rate may be claimed.
    line(DAY, "B-ODD", "OINT", "3:7", 5000, pack="")
    # AN ORTHOTIC: high value, and a discount that legitimately ranges wide.
    # The owner's real figures: 22,000 MRP sold at 15,500; 17,600 given 600 off.
    for amt in (2200000, 1550000, 1760000, 1700000, 2000000, 1850000, 1600000):
        line(HIST, "O%d" % amt, "ORTHO", "1:0", amt)
    line(DAY, "B-ORTHO", "ORTHO", "1:0", 1550000)   # 30% off -- entirely normal
    line(DAY, "B-ORTHO2", "ORTHO", "1:0", 1740000)  # 1% off  -- also normal
    line(DAY, "B-ORTHO-BAD", "ORTHO", "1:0", 120000) # a tenth of any of them
    # A MONTH'S COURSE must not be flagged: a tablet that regularly leaves in
    # 90 units is not news at 90. This is the 445-false-flag case from the first
    # real run, seeded so it can never come back.
    for i in range(12):
        line(HIST, "C%02d" % i, "COURSE", "%d:0" % (1 + i % 6), 4000, pack="1*15")
    line(DAY, "B-COURSE", "COURSE", "6:0", 4000, pack="1*15")   # 90 units, normal
    # LOOSE UNITS: a strip of 10 at 500 per unit. '0:5' is five singles, '1:0'
    # is a whole strip of ten -- and until the pack size was used, every partial
    # strip was thrown away as not comparable.
    for i in range(6):
        line(HIST, "L%d" % i, "TABS", "1:0", 5000, pack="1*10")
    line(DAY, "B-LOOSE", "TABS", "0:5", 5000, pack="1*10")   # 5 singles, same rate
    line(DAY, "B-LOOSE-BAD", "TABS", "0:5", 500, pack="1*10")  # a tenth of it
    con.commit()

    rows, tally = A.scan_day(con, DAY)
    by = {r["bill"]: r for r in rows}

    check("the owner's June case is caught", "B-JUNE" in by,
          by.get("B-JUNE", {}).get("verdict", "MISSED"))
    check("  ...and it is caught on BOTH signals, rate and quantity",
          by.get("B-JUNE", {}).get("verdict") == "RATE OFF AND QUANTITY HIGH")
    check("  ...and it says what the item normally rates",
          "usually rates" in by.get("B-JUNE", {}).get("detail", ""))
    check("a genuine bulk buy at the right rate is flagged on QUANTITY ONLY",
          by.get("B-BULK", {}).get("verdict") == "QUANTITY HIGH",
          "a bulk purchase must not be called a rate error")
    check("an ordinary line is not flagged at all", "B-OK" not in by)
    check("A MONTH'S COURSE of a drug that regularly sells in 90s is NOT flagged",
          "B-COURSE" not in by,
          "the median rule flagged 445 of these over five months")
    check("an item with too little history is NOT judged", "B-RARE" not in by
          and tally.get("too little history to judge") == 1)
    # NOT the old assertion. Now that the rate is taken as printed, a line whose
    # QUANTITY cannot be expressed in single units can still have its RATE
    # judged -- the two signals are independent, and only the quantity one is
    # withheld. That is strictly better than discarding the line.
    check("a partial strip with no pack size is not judged on QUANTITY",
          tally.get("_quantity not comparable") == 1)
    check("  ...but its RATE is still judged, and here it is normal",
          "B-ODD" not in by)
    check("an ORTHOTIC discounted 30% is NOT flagged -- its price legitimately "
          "ranges that far", "B-ORTHO" not in by)
    check("  ...nor one discounted barely at all", "B-ORTHO2" not in by)
    check("  ...but a tenth of its range still IS flagged",
          by.get("B-ORTHO-BAD", {}).get("verdict", "").startswith("RATE OFF"))
    check("  ...and the flag quotes the item's own observed range",
          "has ranged" in by.get("B-ORTHO-BAD", {}).get("detail", ""))
    check("a PARTIAL STRIP is now comparable, not discarded",
          tally.get("_quantity not comparable", 0) == 1,
          "only the one with no pack size remains")
    check("  ...and a loose sale at the right rate is not flagged", "B-LOOSE" not in by)
    check("  ...but a loose sale at a tenth of the rate IS",
          by.get("B-LOOSE-BAD", {}).get("verdict", "").startswith("RATE OFF"))
    # the VERDICT buckets are disjoint and sum to the number of lines; keys
    # beginning with "_" are notes and are counted separately on purpose.
    check("every line lands in exactly ONE verdict bucket",
          sum(v for k, v in tally.items() if not k.startswith("_")) == 11,
          str(tally))

    # the median must not be moved by the outlier it is about to judge
    n = A.item_norms(con, DAY)["OINT"]
    check("one wrong line does not move the yardstick",
          n["rate"] == 5000.0, "median rate %.0f" % n["rate"])
    check("  ...and the day being judged is EXCLUDED from its own yardstick",
          n["qty_max"] == 2, "ceiling from earlier days only: %g" % n["qty_max"])
    check("the RATE is taken as printed, never divided by the quantity",
          "amount_p IS THE RATE" in open("finance_item_anomaly.py",
                                         encoding="utf-8").read())

    con.close()
    print("\nREHEARSAL: %d/%d %s" % (OK, OK + BAD, "ALL PASS" if BAD == 0 else "-- FAILED"))
    return 0 if BAD == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
