#!/usr/bin/env python3
"""selftest_s363.py -- kit S363_CASH_POOL (sanjeevni_cash v1.1: the pool, approval = handover, pool deposits).
Reuses S361's August fixture; Builds a scratch database in the live shape
holding August 2026's DAY TOTALS only (no bill, no patient, no person's detail), seeds it
with the module's own seed, proves it, and then breaks it on purpose seven ways.
Usage: python3 selftest_s361.py [path/to/sanjeevni_cash.py]"""
import importlib.util, os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
target = next((a for a in sys.argv[1:] if a.endswith(".py")), os.path.join(HERE, "sanjeevni_cash.py"))
spec = importlib.util.spec_from_file_location("sc_under_test", target)
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)

n, fails = 0, []
def ok(label, cond):
    global n
    n += 1
    if not cond: fails.append(label)

LIVE_SHAPE = """
CREATE TABLE day_entry(id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, status TEXT);
CREATE TABLE day_line(id INTEGER PRIMARY KEY, day_entry_id INT, service TEXT, mode TEXT, amount_p INT, line_kind TEXT, note TEXT);
CREATE TABLE day_noncash_bill(id INTEGER PRIMARY KEY, day_entry_id INT, unit TEXT, bill_date TEXT, head TEXT, head_text TEXT, bill_no TEXT, amount_p INT);
CREATE TABLE day_expense(id INTEGER PRIMARY KEY, day_entry_id INT, amount_p INT, amount_known INT, expense_uid TEXT);
CREATE TABLE cash_movement(id INTEGER PRIMARY KEY, day_entry_id INT, direction TEXT, party TEXT, amount_p INT, reference TEXT);
CREATE TABLE cash_adjustment(id INTEGER PRIMARY KEY, day_entry_id INT, amount_p INT);
CREATE TABLE cash_custody_event(id INTEGER PRIMARY KEY, unit TEXT, event_date TEXT, from_party TEXT, to_party TEXT, amount_p INT, note TEXT);
CREATE TABLE cash_count(id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, counted_p INT);
CREATE TABLE sale_bill(unit TEXT, business_date TEXT, bill_no TEXT, net_p INT);
CREATE VIEW v_day_cash AS
SELECT e.id AS day_entry_id, e.unit AS unit, e.business_date AS business_date,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l WHERE l.day_entry_id = e.id AND l.mode = 'cash'), 0) AS cash_in_p,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l WHERE l.day_entry_id = e.id AND l.mode = 'upi'), 0) AS upi_in_p,
    COALESCE((SELECT SUM(l.amount_p) FROM day_line l WHERE l.day_entry_id = e.id), 0) AS revenue_p,
    COALESCE((SELECT SUM(b.amount_p) FROM day_noncash_bill b WHERE b.day_entry_id = e.id), 0) AS noncash_p,
    COALESCE((SELECT SUM(x.amount_p) FROM day_expense x WHERE x.day_entry_id = e.id AND x.amount_known = 1), 0) AS expense_p,
    COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m WHERE m.day_entry_id = e.id AND m.direction = 'out'), 0) AS cash_out_p,
    COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m WHERE m.day_entry_id = e.id AND m.direction = 'in'), 0) AS cash_back_p,
    COALESCE((SELECT SUM(a.amount_p) FROM cash_adjustment a WHERE a.day_entry_id = e.id), 0) AS adjust_p
FROM day_entry e;
"""
# August 2026, day totals in rupees: (date, cash, upi)
DAYS = [("2026-09-02", 7900, 9744), ("2026-09-03", 12343, 4214), ("2026-09-04", 11066, 12609),
        ("2026-08-15", 3926, 4925), ("2026-08-17", 13401, 10071), ("2026-08-18", 18469, 6707),
        ("2026-08-19", 15124, 28996), ("2026-08-20", 7939, 8194), ("2026-08-21", 36913, 12268),
        ("2026-08-22", 14922, 7043), ("2026-08-24", 7565, 5399), ("2026-08-25", 15809, 2669),
        ("2026-08-26", 7321, 8638), ("2026-08-27", 26179, 11170), ("2026-08-28", 8710, 6687),
        ("2026-08-29", 16006, 971), ("2026-08-31", 32809, 7363), ("2026-09-01", 9350, 643)]
MOVES = [("2026-08-20", "dr_manoj", 51930), ("2026-08-25", "dr_bhawna", 43900), ("2026-08-31", "dr_bhawna", 26180),
         ("2026-08-31", "dr_bhawna", 8710), ("2026-08-31", "dr_bhawna", 16000), ("2026-08-31", "dr_bhawna", 24000)]
CUSTODY = [("2026-08-06", "counter", "dr_bhawna", 7309), ("2026-08-15", "counter", "dr_bhawna", 3926),
           ("2026-08-17", "counter", "dr_bhawna", 145000), ("2026-08-17", "drawer", "dr_manoj", 18963),
           ("2026-08-27", "drawer", "dr_bhawna", 23130), ("2026-08-31", "drawer", "dr_manoj", 8810)]

def build():
    c = sqlite3.connect(":memory:")
    c.executescript(LIVE_SHAPE)
    ids = {}
    for d, cash, upi in DAYS:
        cur = c.execute("INSERT INTO day_entry(unit,business_date,status) VALUES('medical',?,'approved')", (d,))
        ids[d] = cur.lastrowid
        c.execute("INSERT INTO day_line(day_entry_id,mode,amount_p) VALUES(?,?,?)", (ids[d], "cash", cash * 100))
        c.execute("INSERT INTO day_line(day_entry_id,mode,amount_p) VALUES(?,?,?)", (ids[d], "upi", upi * 100))
        c.execute("INSERT INTO sale_bill(unit,business_date,bill_no,net_p) VALUES('medical',?,'B',?)", (d, (cash + upi) * 100))
    c.execute("INSERT INTO day_noncash_bill(day_entry_id,unit,head,bill_no,amount_p) VALUES(?,?,?,?,?)", (ids["2026-08-20"], "medical", "other", "2777", 300000))
    c.execute("INSERT INTO day_noncash_bill(day_entry_id,unit,head,bill_no,amount_p) VALUES(?,?,?,?,?)", (ids["2026-08-21"], "medical", "home_medicine", "3114", 1550000))
    c.execute("INSERT INTO day_expense(day_entry_id,amount_p,amount_known,expense_uid) VALUES(?,?,1,?)", (ids["2026-08-17"], 2000000, "exS202darpan20k17aug"))
    for d, p, a in MOVES:
        c.execute("INSERT INTO cash_movement(day_entry_id,direction,party,amount_p) VALUES(?,'out',?,?)", (ids[d], p, a * 100))
    for d, f, t, a in CUSTODY:
        c.execute("INSERT INTO cash_custody_event(unit,event_date,from_party,to_party,amount_p) VALUES('medical',?,?,?,?)", (d, f, t, a * 100))
    c.execute("INSERT INTO cash_count(unit,business_date,counted_p) VALUES('medical','2026-08-17',17519800)")
    return c

def refuses(fn):
    try:
        fn(); return False
    except RuntimeError:
        return True


def mark(c, d, status):
    c.execute("UPDATE day_entry SET status=? WHERE business_date=?", (status, d))

c = build(); sc.ensure_schema(c); sc.seed_august(c, "t", "t")
for d in ("2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04"):
    mark(c, d, "submitted")
p31 = sc.position(c, "2026-08-31")
into = {r["date"]: r["into_drawer_p"] for r in sc.days(c, "2026-09-01", "2026-09-30")["rows"]}
p = sc.position(c, "2026-09-30")
ok("unapproved September days stay in the drawer, marked waiting", p["drawer"] == p31["drawer"] + sum(into.values()) and len(p["waiting_days"]) == 4)
mark(c, "2026-09-01", "approved"); mark(c, "2026-09-02", "approved")
p = sc.position(c, "2026-09-30")
ok("approving a day sends that day's cash from the drawer to the pool",
   p["drawer"] == p31["drawer"] + into["2026-09-03"] + into["2026-09-04"] and p["pool"] == into["2026-09-01"] + into["2026-09-02"])
ok("... and the doctors' total is August's pool plus the approved days", p["with_doctors"] == p31["dr_bhawna"] + p31["dr_manoj"] + into["2026-09-01"] + into["2026-09-02"])
nseed = sc.seed_september(c, "t", "t")
p2 = sc.position(c, "2026-09-30")
ok("the two pool deposits are seeded once", nseed == 2 and sc.seed_september(c, "t", "t") == 0)
ok("a pool deposit leaves the pool for the bank and never touches the drawer",
   p2["drawer"] == p["drawer"] and p2["bank"] == p["bank"] + 40000000 and p2["with_doctors"] == p["with_doctors"] - 40000000)
ok("cash is conserved across approval and deposit", p2["in_unit"] + p2["bank"] == p["in_unit"] + p["bank"])
did = c.execute("SELECT id FROM day_entry WHERE business_date='2026-09-03'").fetchone()[0]
c.execute("INSERT INTO cash_movement(day_entry_id,direction,party,amount_p,reference) VALUES(?,'out','dr_bhawna',?,'[kal] logged')", (did, into["2026-09-03"]))
mark(c, "2026-09-03", "approved")
p3 = sc.position(c, "2026-09-30")
ok("NEG: an approved day that also has a recorded handover is counted once (the record wins)",
   p3["drawer"] == p31["drawer"] + into["2026-09-04"] and p3["dr_bhawna"] == p31["dr_bhawna"] + into["2026-09-03"])
cv = {x["date"]: x for x in sc.coverage(c, "2026-09-01", "2026-09-30")["days"]}
ok("coverage: approved days are done by approval, the waiting day is not", cv["2026-09-01"]["done"] and cv["2026-09-01"]["by_approval"] and not cv["2026-09-04"]["done"])
mm = sc.month_moves(c).get("2026-09", {})
ok("month moves: September to the pool and to the bank", mm.get("to_pool_p") == into["2026-09-01"] + into["2026-09-02"] and mm.get("to_bank_p") == 40000000)
c2 = build(); sc.ensure_schema(c2); sc.seed_august(c2, "t", "t")
c2.execute("INSERT INTO cash_movement(day_entry_id,direction,party,amount_p) VALUES((SELECT id FROM day_entry WHERE business_date='2026-09-03'),'out','bank',30000000)")
ok("NEG: a pool deposit already booked as a drawer movement is refused", refuses(lambda: sc.seed_september(c2, "t", "t")))
ok("the August proof still holds on v1.1 (with the September days and deposits in)", sc.prove(c)[0])

print("selftest_s363: %d/%d checks passed" % (n - len(fails), n))
for f in fails: print("  FAILED:", f)
print("SELFTEST_S363 GREEN" if not fails else "SELFTEST_S363 RED")
sys.exit(1 if fails else 0)
