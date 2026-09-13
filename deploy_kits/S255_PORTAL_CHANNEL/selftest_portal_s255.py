#!/usr/bin/env python3
"""S255_PORTAL_CHANNEL selftest -- offline, no network, no VPS.
Builds a real sqlite of one day's Docterz entries and asserts the split behaves."""
import io, os, sqlite3, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ok = fail = 0
def chk(cond, label):
    global ok, fail
    if cond: ok += 1;   print("PASS ", label)
    else:    fail += 1; print("FAIL ", label)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m

con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
con.executescript("""
CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INTEGER, patient TEXT,
  clinic_id TEXT, amount_p INTEGER, mode TEXT, shift TEXT);
CREATE TABLE clinic_day_tender (business_date TEXT, clinic_id TEXT, invoice_no TEXT,
  tender TEXT, amount_p INTEGER);
""")
D = "2026-08-29"
rows = [(D,"consult",1,"A","C1", 50000,"Online Payment","morning"),   # ICICI UPI  Rs 500
        (D,"consult",2,"B","C2", 60000,"Wallet",        "morning"),   # portal     Rs 600
        (D,"consult",3,"C","C3", 30000,"Patient APP",   "evening"),   # portal     Rs 300
        (D,"consult",4,"D","C4", 40000,"Cash",          "evening"),
        (D,"proc",   5,"E","C5", 70000,"Split Payment", "evening")]
con.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?)", rows)
con.executemany("INSERT INTO clinic_day_tender VALUES (?,?,?,?,?)",
                [(D,"C5","INV5","Net Banking",20000),                 # portal leg Rs 200
                 (D,"C5","INV5","Cash",        50000)])
con.commit()

fcd = load("finance_clinic_day", os.path.join(HERE, "finance_clinic_day.py"))
chk(fcd.our_online_p(con, D)       == 160000, "our_online_p unchanged = all online (Rs 1,600)")
chk(fcd.our_icici_online_p(con, D) ==  50000, "our_icici_online_p = ICICI only (Rs 500)")
chk(fcd.our_portal_p(con, D)       == 110000, "our_portal_p = Wallet+Patient APP+Net Banking (Rs 1,100)")
chk(fcd.our_icici_online_p(con, D) + fcd.our_portal_p(con, D) == fcd.our_online_p(con, D),
    "the two channels add back to the whole -- no rupee invented or lost")
chk(fcd._channel_of("Online Payment") == "icici" and fcd._channel_of("Wallet") == "portal"
    and fcd._channel_of(None) == "icici", "_channel_of: the three portal modes, and nothing else")

cm = load("clinic_money", os.path.join(HERE, "clinic_money.py"))
doc = cm._docterz(con, D)
chk(doc["tender"]["upi"] == 160000, "revenue untouched: Docterz upi tender still Rs 1,600")
chk(doc["tender"]["cash"] == 90000,  "revenue untouched: cash still Rs 900")
por = [o for o in doc["online"] if o.get("channel") == "portal"]
ici = [o for o in doc["online"] if o.get("channel") == "icici"]
chk(sum(o["amount_p"] for o in por) == 110000 and len(por) == 3, "3 portal entries tagged, Rs 1,100")
chk(sum(o["amount_p"] for o in ici) ==  50000 and len(ici) == 1, "1 ICICI entry tagged, Rs 500")
chk(all("channel" in o for o in doc["online"]), "every online entry carries a channel")

src = io.open(os.path.join(HERE, "clinic_money.py"), encoding="utf-8").read()
chk(src.count('expected_bank = d_t["upi"] - other - portal_p') == 1,
    "the bank expectation subtracts portal money, once")
chk(src.count('ours = [o for o in doc["online"] if o.get("channel") != "portal"]') == 1,
    "portal entries are kept out of the bank pairing, once")
chk(src.count('expl("portal"') == 1, "each portal payment explains itself, once")
chk('never reached the ICICI account' in src, "the old owner-flag text still exists for real ICICI misses")
row = cm._portal_month_row(con, D, D)
chk("Portal (Razorpay" in row and "1,100" in row, "the month card gains a Portal row with the right total")
chk(cm._portal_month_row(con, "2026-01-01", "2026-01-31") == "",
    "a month with no portal payment shows no row at all")

print("\n%d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
