#!/usr/bin/env python3
"""selftest_s361.py -- kit S361_CASH_CORE. Builds a scratch database in the live shape
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
DAYS = [("2026-08-15", 3926, 4925), ("2026-08-17", 13401, 10071), ("2026-08-18", 18469, 6707),
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

# ---- before any seed: no anchor, no invented position
c = build()
sc.ensure_schema(c)
ok("unseeded: no position is stated (never a 0)", sc.position(c, "2026-08-31").get("ok") is False)
ok("unseeded: the proof is RED", sc.prove(c)[0] is False)

# ---- seeded: the August proof
w = sc.seed_august(c, "selftest", "2026-09-21T00:00:00")
ok("seed writes the anchor, 14 day covers, the ruling and the close", w == dict(anchor=1, cover=14, ruling=1, close=1))
good, res = sc.prove(c)
ok("the August proof is GREEN", good)
p24 = sc.position(c, "2026-08-24"); p31 = sc.position(c, "2026-08-31")
ok("25-Aug count: drawer 43,903 before that day's handover", p24["drawer"] == 4390300)
ok("31-Aug: drawer 7 / Dr Bhawna 2,98,155 / Dr Manoj 79,703", (p31["drawer"], p31["dr_bhawna"], p31["dr_manoj"]) == (700, 29815500, 7970300))
ok("both registers read, each handover once: 8 handovers after the count",
   len(sc.handovers(c, "2026-08-17", "2026-08-31", "medical", {1, 2, 3, 4})) == 8)
ok("seeding again writes nothing", sc.seed_august(c, "selftest", "x") == dict(anchor=0, cover=0, ruling=0, close=0))
m = {r["ym"]: r for r in sc.month_rows(c)}["2026-08"]
ok("month: the Rs 3,000 of 20-Aug is paid elsewhere, not without-cash", (m["other_p"], m["received_elsewhere_p"]) == (0, 300000))
ok("month: cash income = cash - home - proc - other", m["cash_income_p"] == m["cash_p"] - 1550000)
ok("a day before the count is never positioned", all(r["date"] >= "2026-08-17" for r in sc.days(c, "2026-08-01", "2026-08-31")["rows"]))

# ---- deliberate failures
c2 = build(); sc.ensure_schema(c2)
c2.execute("INSERT INTO cash_movement(day_entry_id,direction,party,amount_p) VALUES((SELECT id FROM day_entry WHERE business_date='2026-08-27'),'out','dr_bhawna',2313000)")
sc.seed_august(c2, "t", "t")   # custody 27-Aug now ALSO in cash_movement: must count once
ok("NEG: a handover written in BOTH registers is counted once", sc.position(c2, "2026-08-31")["drawer"] == 700)
c3 = build(); c3.execute("UPDATE cash_count SET counted_p = counted_p + 100")
ok("NEG: an anchor that does not add up to the count is refused", refuses(lambda: sc.seed_august(c3, "t", "t")))
ok("NEG: ... and nothing was written", c3.execute("SELECT COUNT(*) FROM cash_anchor").fetchone()[0] == 0)
c4 = build(); c4.execute("DELETE FROM cash_movement WHERE amount_p=4390000")
ok("NEG: a handover the seed names but cannot find is refused", refuses(lambda: sc.seed_august(c4, "t", "t")))
c5 = build(); c5.execute("UPDATE day_noncash_bill SET amount_p=250000 WHERE bill_no='2777'")
ok("NEG: a ruling on a bill that is not what the owner named is refused", refuses(lambda: sc.seed_august(c5, "t", "t")))
c6 = build(); sc.seed_august(c6, "t", "t")
c6.execute("UPDATE day_line SET amount_p = amount_p + 100000 WHERE mode='cash' AND day_entry_id=(SELECT id FROM day_entry WHERE business_date='2026-08-22')")
ok("NEG: a day's cash changed after the fact turns the proof RED", sc.prove(c6)[0] is False)
c7 = build(); sc.seed_august(c7, "t", "t"); c7.execute("DELETE FROM cash_handover_cover WHERE covers_date='2026-08-28'")
ok("NEG: a day left uncovered turns the proof RED", sc.prove(c7)[0] is False)
c8 = build(); c8.execute("DELETE FROM day_expense")
sc.ensure_schema(c8); sc.seed_august(c8, "t", "t")
ok("NEG: the pre-count 20,000 is not what makes 25-Aug agree (removing it changes nothing after the count)",
   sc.position(c8, "2026-08-24")["drawer"] == 4390300)

print("selftest_s361: %d/%d checks passed" % (n - len(fails), n))
for f in fails: print("  FAILED:", f)
print("SELFTEST_S361 GREEN" if not fails else "SELFTEST_S361 RED")
sys.exit(1 if fails else 0)
