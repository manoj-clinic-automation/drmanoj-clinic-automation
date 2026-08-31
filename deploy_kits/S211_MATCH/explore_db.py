#!/usr/bin/env python3
"""explore_db.py -- READ-ONLY, thorough. What is actually in finance.db?

Opened with mode=ro, so a write is impossible, not merely avoided.
Prints counts, date ranges, schema and masked shapes -- never a patient name,
a mobile, or a bill's text.
"""
import collections, os, re, sqlite3, sys
sys.path.insert(0, "/root/finance")
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
con.row_factory = sqlite3.Row
def q(sql, *a):
    try: return con.execute(sql, a).fetchall()
    except sqlite3.Error as e: return [{"err": str(e)[:60]}]
def one(sql, *a):
    r = q(sql, *a)
    return (list(r[0]) or [None])[0] if r else None
def H(t): print("\n" + "=" * 74 + "\n" + t + "\n" + "=" * 74)

H("1  EVERY TABLE, ITS SIZE, AND WHAT PERIOD IT COVERS")
tabs = [r["name"] for r in q("SELECT name FROM sqlite_master WHERE type='table' "
                             "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
print("tables: %d\n" % len(tabs))
print("%-26s %9s  %s" % ("table", "rows", "date span (if any)"))
for t in tabs:
    n = one("SELECT COUNT(*) FROM [%s]" % t)
    cols = [c["name"] for c in q("PRAGMA table_info([%s])" % t)]
    dc = next((c for c in ("business_date", "statement_date", "visit_date",
                           "reg_date", "first_noted", "at", "run_at",
                           "received_at", "entered_at") if c in cols), None)
    span = ""
    if dc and n:
        lo = one("SELECT MIN([%s]) FROM [%s]" % (dc, t))
        hi = one("SELECT MAX([%s]) FROM [%s]" % (dc, t))
        span = "%s  %s .. %s" % (dc, str(lo)[:10], str(hi)[:10])
    print("%-26s %9s  %s" % (t, n, span))

H("2  THE MONEY SPINE -- day_entry, day_line, sale_item, sale_line_item")
print("day_entry by status:", {r[0]: r[1] for r in
      q("SELECT status, COUNT(*) FROM day_entry GROUP BY 1")})
print("day_entry by unit  :", {r[0]: r[1] for r in
      q("SELECT unit, COUNT(*) FROM day_entry GROUP BY 1")})
print()
print("sale_item by service:", {r[0]: r[1] for r in
      q("SELECT service, COUNT(*) FROM sale_item GROUP BY 1 ORDER BY 2 DESC")})
print("sale_item by mode   :", {r[0]: r[1] for r in
      q("SELECT COALESCE(mode,'(null)'), COUNT(*) FROM sale_item GROUP BY 1")})
print("sale_item by source :", {r[0]: r[1] for r in
      q("SELECT COALESCE(source,'(null)'), COUNT(*) FROM sale_item GROUP BY 1")})
print()
for c in ("description", "gross_p", "disc_p", "patient_ref_id", "source_ref", "confidence"):
    f = one("SELECT COUNT(*) FROM sale_item WHERE COALESCE([%s],'')<>''" % c)
    print("   sale_item.%-14s populated on %6s of %s" %
          (c, f, one("SELECT COUNT(*) FROM sale_item")))
print()
print("day_line by mode    :", {r[0]: r[1] for r in
      q("SELECT mode, COUNT(*) FROM day_line GROUP BY 1")})
print("months with day_line:", {r[0]: r[1] for r in
      q("SELECT substr(e.business_date,1,7), COUNT(DISTINCT e.id) FROM day_line l "
        "JOIN day_entry e ON e.id=l.day_entry_id GROUP BY 1 ORDER BY 1")})

H("3  COVERAGE BY MONTH -- where the history actually is")
print("%-9s %8s %10s %10s %8s %8s" % ("month","days","sale_item","line_items","returns","bank"))
for r in q("SELECT substr(business_date,1,7) m, COUNT(*) d FROM day_entry "
           "WHERE unit='medical' GROUP BY 1 ORDER BY 1"):
    m = r[0]
    si = one("SELECT COUNT(*) FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
             "WHERE e.unit='medical' AND substr(e.business_date,1,7)=?", m)
    li = one("SELECT COUNT(*) FROM sale_line_item WHERE substr(business_date,1,7)=?", m)
    rt = one("SELECT COUNT(*) FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
             "WHERE e.unit='medical' AND substr(e.business_date,1,7)=? "
             "AND s.service LIKE '%!_return' ESCAPE '!'", m)
    bk = one("SELECT COUNT(*) FROM upi_statement WHERE substr(statement_date,1,7)=?", m)
    print("%-9s %8s %10s %10s %8s %8s" % (m, r[1], si, li, rt, bk))

H("4  THE PATIENT SPINE")
for c in ("clinic_id","name","mobile","mobile_fp","phone_last4","patient_uid",
          "admin_cc_p","admin_pd_pct","admin_bid_pct","is_vip"):
    print("   patient_ref.%-15s populated on %6s of %s" %
          (c, one("SELECT COUNT(*) FROM patient_ref WHERE COALESCE([%s],'')<>''" % c),
           one("SELECT COUNT(*) FROM patient_ref")))
print()
print("   collisions by kind :", {r[0]: r[1] for r in
      q("SELECT COALESCE(kind,'(unset)'), COUNT(*) FROM patient_id_collision GROUP BY 1")})
print("   merge candidates   :", one("SELECT COUNT(*) FROM patient_merge_candidate"))
print("   visits             :", one("SELECT COUNT(*) FROM patient_visit"))

H("5  BILLS THAT CANNOT BE JOINED -- and why")
print("sale_item rows with no patient link :",
      one("SELECT COUNT(*) FROM sale_item WHERE patient_ref_id IS NULL"))
wid = one("SELECT id FROM patient_ref WHERE UPPER(clinic_id)='WALK-IN'")
print("rows on WALK-IN                     :",
      one("SELECT COUNT(*) FROM sale_item WHERE patient_ref_id=?", wid) if wid else "no WALK-IN row")
print("rows on a patient with no uid       :",
      one("SELECT COUNT(*) FROM sale_item s JOIN patient_ref p ON p.id=s.patient_ref_id "
          "WHERE COALESCE(p.patient_uid,'')=''"))
print()
print("source_ref SHAPES on return bills (digits->#, letters->A):")
sh = collections.Counter()
for r in q("SELECT DISTINCT source_ref FROM sale_item "
           "WHERE service LIKE '%!_return' ESCAPE '!' AND source_ref IS NOT NULL"):
    s = re.sub(r"\d","#",str(r[0])); s = re.sub(r"[A-Za-z]","A",s)
    sh[re.sub(r"#{2,}","#+",re.sub(r"A{2,}","A+",s))] += 1
print("  ", dict(sh))

H("6  THE THREE DETECTORS, FIRST REAL NUMBERS")
try:
    import finance_returns_audit as RA
    rets = q("SELECT s.source_ref b, e.business_date d, s.amount_p a FROM sale_item s "
             "JOIN day_entry e ON e.id=s.day_entry_id WHERE e.unit='medical' "
             "AND s.service LIKE '%!_return' ESCAPE '!'")
    rung = collections.Counter()
    for r in rets:
        _l, how = RA.find_return_lines(con, r["b"], r["d"], r["a"])
        rung[(how.split("(")[0].strip() if how else "NOT FOUND")] += 1
    print("RETURNS -- how the item lines were found:")
    for k, v in rung.most_common(): print("   %-48s %5d" % (k, v))
    got = sum(v for k, v in rung.items() if k != "NOT FOUND")
    print("   examinable: %d of %d" % (got, sum(rung.values())))
except Exception as e:
    print("returns audit not importable:", str(e)[:70])
try:
    import finance_item_anomaly as IA
    days = [r[0] for r in q("SELECT DISTINCT business_date FROM sale_line_item "
                            "ORDER BY business_date DESC LIMIT 30")]
    t = collections.Counter()
    for d in days:
        # per day, strictly from earlier days -- never one global yardstick
        _rows, tt = IA.scan_day(con, d, "medical")
        t.update(tt)
    print("\nITEM ANOMALY -- last %d days with item lines:" % len(days))
    for k, v in t.most_common(): print("   %-34s %6d" % (k, v))
    nn = IA.item_norms(con)
    print("   items with enough history to judge : %d of %d" %
          (sum(1 for v in nn.values() if v.get("n",0) >= IA.MIN_HISTORY), len(nn)))
except Exception as e:
    print("anomaly detector not importable:", str(e)[:70])
con.close()
print("\n(read-only throughout; nothing was written)")
