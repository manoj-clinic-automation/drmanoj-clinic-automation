#!/usr/bin/env python3
"""
WALK_sump.py -- S212 LIVE-SHAPE walk for the sump.

Not a gate. A walk. It builds a REAL database from the REAL schema files,
loads the REAL Marg archive into it, deliberately manufactures the two awkward
populations, and then runs the actual returns_for_day() against it.

S208 found two defects behind 65 green checks; S209 found a page that killed a
console behind four green gates. So this asks the questions a gate cannot:

  1  does the sump SEE an orphan -- a return with lines and no bill row?
  2  does it still see a return with a bill row and NO lines?
  3  does its money equal the value computed independently from the archive?
  4  does it refuse to call an orphan "NEVER BOUGHT"?
  5  is a full patient number anywhere in what it returns?
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIN = sys.argv[1]
ARCHIVE = sys.argv[2]
sys.path.insert(0, FIN)
sys.path.insert(0, HERE)

import marg_report
import finance_money as M
import finance_returns_audit as R

DB = os.path.join(HERE, "walk.db")
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
for f in ("finance_schema.sql", "finance_returns.sql"):
    con.executescript(open(os.path.join(FIN, f)).read())
con.execute("INSERT OR IGNORE INTO business_unit (code,name) VALUES ('medical','Medical')")

# --------------------------------------------------------------- load archive
files = sorted(os.path.join(r, n)
               for r, _d, ns in os.walk(ARCHIVE) for n in ns
               if "BILLWISE_DETAIL" in n.upper())
pat, days, nbill, nline = {}, {}, 0, 0
for f in files:
    try:
        rep = marg_report.read_report(f, keep_items=True)
    except Exception:
        continue
    for d in rep["days"]:
        date = d.get("date") or d.get("business_date")
        if date not in days:
            cur = con.execute("INSERT OR IGNORE INTO day_entry (unit,business_date,source) "
                              "VALUES ('medical',?,'app')", (date,))
            days[date] = con.execute("SELECT id FROM day_entry WHERE unit='medical' "
                                     "AND business_date=?", (date,)).fetchone()[0]
        eid = days[date]
        for b in d["bills"]:
            cid = b["clinic_id"] or ("WALKIN-" + b["bill_no"])
            if cid not in pat:
                con.execute("INSERT OR IGNORE INTO patient_ref (clinic_id,name,phone_last4) "
                            "VALUES (?,?,?)", (cid, b["patient_name"],
                                               (b["phone"] or "")[-4:] or None))
                pat[cid] = con.execute("SELECT id FROM patient_ref WHERE clinic_id=?",
                                       (cid,)).fetchone()[0]
            con.execute(
                "INSERT INTO sale_item (day_entry_id,unit,patient_ref_id,service,"
                "amount_p,source,source_ref) VALUES (?,'medical',?,?,?,'ocr',?)",
                (eid, pat[cid],
                 "pharmacy_return" if b["is_credit_note"] else "pharmacy",
                 abs(b["net_p"] or 0), b["bill_no"]))
            nbill += 1
        for it in d["items"]:
            p = it["parsed"]
            if p.get("seq") is None:
                continue
            try:
                con.execute(
                    "INSERT OR IGNORE INTO sale_line_item (day_entry_id,unit,business_date,"
                    "bill_no,is_return,seq,item_name,item_key,pack,qty_raw,amount_p,"
                    "expiry_ym,batch) VALUES (?,'medical',?,?,?,?,?,?,?,?,?,?,?)",
                    (eid, date, it["bill_no"], 1 if it["bill_no"].startswith("CN") else 0,
                     p["seq"], p["item_name"] or "?",
                     (p["item_name"] or "?").upper().strip(), p["pack"], p["qty_raw"],
                     p["amount_p"], p["expiry_ym"], p["batch"]))
                nline += 1
            except sqlite3.IntegrityError:
                pass
con.commit()
print("loaded: %d bills, %d item lines, %d days" % (nbill, nline, len(days)))

# ------------------------------------------------- the independent expectation
# DEDUPLICATED BY BILL NUMBER. The archive exports some days more than once --
# 2026-08-18 and 2026-08-24 each appear in two files, and one file spans
# 08-23_to_08-24. Summing across files without deduplicating inflates the
# total, which is how a first pass here expected Rs 8,951.47 where the truth
# for unique bills is lower. The database cannot double-count (sale_line_item
# is UNIQUE on unit+bill_no+seq), so the expectation must not either.
exp_by_bill = {}
for f in files:
    try:
        rep = marg_report.read_report(f, keep_items=True)
    except Exception:
        continue
    for d in rep["days"]:
        byb = {}
        for it in d["items"]:
            byb.setdefault(it["bill_no"], []).append(it["parsed"])
        for b in d["bills"]:
            if b["is_credit_note"] and byb.get(b["bill_no"]):
                g, _ = M.bill_gross_p(byb[b["bill_no"]])
                exp_by_bill[b["bill_no"]] = g
exp_p = sum(exp_by_bill.values())
exp_bills = set(exp_by_bill)
print("independent expectation: %d UNIQUE CN bills with lines, %s"
      % (len(exp_bills), M.rupees(exp_p)))

# ------------------------------------------ manufacture the awkward populations
cn = [r[0] for r in con.execute(
    "SELECT DISTINCT bill_no FROM sale_line_item WHERE is_return=1 ORDER BY bill_no")]
orphaned = cn[:5]
con.execute("DELETE FROM sale_item WHERE source_ref IN (%s)"
            % ",".join("?" * len(orphaned)), orphaned)
stripped = cn[5:8]
con.execute("DELETE FROM sale_line_item WHERE bill_no IN (%s)"
            % ",".join("?" * len(stripped)), stripped)
con.commit()
print("manufactured: %d orphans (lines, no bill row), %d stripped (bill row, no lines)"
      % (len(orphaned), len(stripped)))

# ---------------------------------------------------------------------- the run
dates = [r[0] for r in con.execute(
    "SELECT DISTINCT business_date FROM day_entry ORDER BY 1")]
tot_p = tot_n = 0
seen_orphan = seen_nodetail = 0
bad_verdict = []
leaks = []
for d in dates:
    rows, s = R.returns_for_day(con, d, "medical")
    tot_p += s["value_p"]
    tot_n += s["count"]
    seen_orphan += s["orphans"]
    seen_nodetail += s["no_item_detail"]
    for r in rows:
        if r["population"] == "orphan" and r["verdict"] == "NEVER BOUGHT":
            bad_verdict.append(r["bill"])
        for v in (r.get("mobile_last4"), r.get("name"), r.get("clinic_id")):
            if v and len(str(v)) > 4 and str(v).isdigit() and len(str(v)) >= 7:
                leaks.append((r["bill"], v))

print()
print("=" * 74)
print("THE WALK")
print("=" * 74)


def ck(label, cond, extra=""):
    print("  %s  %s%s" % ("PASS" if cond else "**FAIL**", label,
                          ("   " + extra) if extra else ""))
    return bool(cond)


ok = True
ok &= ck("1 orphans are SEEN (lines, no bill row)", seen_orphan == len(orphaned),
         "found %d of %d" % (seen_orphan, len(orphaned)))
ok &= ck("2 bill-row-without-lines still seen", seen_nodetail == len(stripped),
         "found %d of %d" % (seen_nodetail, len(stripped)))
# The stripped bills lost their lines, so the sump must value them from the
# bill row instead -- and that is a DIFFERENT number from their line value.
# The expectation says so explicitly rather than hoping the two agree.
# The headline is NET where a bill row exists (cash actually refunded) and
# GROSS from lines only for an orphan, which has no bill row. The expectation
# says that in full rather than assuming the two are interchangeable -- they
# are not, and the first version of this walk failed precisely because it
# assumed they were.
# DEDUPLICATED BY BILL, exactly as the sump does. sale_item carries one row
# per archive occurrence, so a day exported twice yields two rows for the same
# credit note; the sump keys by bill number and so must this.
net_by_bill = {}
for r in con.execute(
        "SELECT s.source_ref b, s.amount_p a FROM sale_item s "
        "JOIN day_entry e ON e.id=s.day_entry_id WHERE e.unit='medical' "
        "AND s.service LIKE '%!_return' ESCAPE '!'"):
    net_by_bill[r["b"]] = abs(r["a"] or 0)
net_p = sum(net_by_bill.values())
orphan_p = sum(v for b, v in exp_by_bill.items() if b in orphaned)
want_p = net_p + orphan_p
ok &= ck("3 money equals the independent figure", tot_p == want_p,
         "sump %s vs expected %s (%s net from bill rows + %s gross from orphan lines)"
         % (M.rupees(tot_p), M.rupees(want_p), M.rupees(net_p),
            M.rupees(orphan_p)))

# 6 -- the discount-on-a-refund signal must actually fire where it should.
disc_rows, disc_total = [], 0
for d in dates:
    rows, _s = R.returns_for_day(con, d, "medical")
    for r in rows:
        if r.get("refund_shortfall_p"):
            disc_rows.append((r["bill"], r["refund_shortfall_p"], r["verdict"]))
            disc_total += r["refund_shortfall_p"]
ok &= ck("6 discount-on-a-refund is flagged, not netted away",
         any(v == "DISCOUNTED RETURN" for _b, _p, v in disc_rows),
         "%d flagged, %s withheld from refunds; largest: %s"
         % (len(disc_rows), M.rupees(disc_total),
            max(disc_rows, key=lambda x: x[1])[0] if disc_rows else "--"))
if disc_rows:
    print()
    print("     returns refunded BELOW what the goods were worth:")
    for b_, p_, v_ in sorted(disc_rows, key=lambda x: -x[1]):
        print("       %-10s short by %s   (%s)" % (b_, M.rupees(p_), v_))
ok &= ck("4 no orphan is called NEVER BOUGHT", not bad_verdict,
         ("offenders: %s" % bad_verdict[:5]) if bad_verdict else "")
ok &= ck("5 no full patient number in the output", not leaks,
         ("leaks: %s" % leaks[:3]) if leaks else "")
print()
print("  sump total over %d days: %d returns, %s"
      % (len(dates), tot_n, M.rupees(tot_p)))
print()
print("WALK: %s" % ("all clear" if ok else "SOMETHING IS WRONG -- read above"))
