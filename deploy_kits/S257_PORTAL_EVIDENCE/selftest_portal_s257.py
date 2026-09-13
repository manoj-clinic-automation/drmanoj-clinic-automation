#!/usr/bin/env python3
"""S257_PORTAL_EVIDENCE selftest -- offline. Rebuilds the two real cases that refuted S255:
Bindu (29-Aug: 'Online Payment' WITH a Razorpay id) and Alka (12-Sep: 'Wallet' WITHOUT one)."""
import importlib.util, os, sqlite3, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ok = fail = 0
def chk(c, l):
    global ok, fail
    if c: ok += 1;  print("PASS ", l)
    else: fail += 1; print("FAIL ", l)
def load(n, p):
    sp = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(sp)
    sys.modules[n] = m; sp.loader.exec_module(m); return m

SCHEMA = """CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, sn INTEGER, patient TEXT,
  clinic_id TEXT, amount_p INTEGER, mode TEXT, shift TEXT%s);
CREATE TABLE clinic_day_tender (business_date TEXT, clinic_id TEXT, invoice_no TEXT, tender TEXT, amount_p INTEGER);"""
D = "2026-09-12"
def db(with_col):
    con = sqlite3.connect(":memory:"); con.row_factory = sqlite3.Row
    con.executescript(SCHEMA % (", gateway_ref TEXT NOT NULL DEFAULT ''" if with_col else ""))
    rows = [(D,"consult",1,"Alka","8071", 60000,"Wallet",        "morning",""),                 # no id -> ICICI
            (D,"xray",   9,"Alka","8071", 50000,"Wallet",        "morning",""),                 # no id -> ICICI
            (D,"consult",2,"Bindu","7961",60000,"Online Payment","morning","pay_TVSzKeESCXc04L"),# id  -> portal
            (D,"consult",3,"Ajay","C3",   10000,"Online Payment","morning",""),                 # ICICI
            (D,"consult",4,"D","C4",      40000,"Cash",          "evening","")]
    if with_col:
        con.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)", rows)
    else:
        con.executemany("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?)", [r[:8] for r in rows])
    con.executemany("INSERT INTO clinic_day_tender VALUES (?,?,?,?,?)",
                    [(D,"8067","2353","Online Payment",205000), (D,"8067","2353","Cash",60000)])
    con.commit(); return con

fcd = load("finance_clinic_day", os.path.join(HERE, "finance_clinic_day.py"))
cm  = load("clinic_money",       os.path.join(HERE, "clinic_money.py"))

con = db(True)
ents = fcd._our_online_entries(con, D)
por = [o for o in ents if o["channel"] == "portal"]; ici = [o for o in ents if o["channel"] == "icici"]
chk(len(por) == 1 and por[0]["patient"] == "Bindu", "Bindu's 'Online Payment' WITH id is portal")
chk(all(o["patient"] != "Alka" for o in por), "Alka's 'Wallet' WITHOUT id is NOT portal (the S255 error)")
chk(sum(o["amount_p"] for o in ici) == 60000+50000+10000+205000, "ICICI side = Alka 600+500, Ajay 100, split leg 2,050")
chk(fcd.our_online_p(con, D) == 385000, "our_online_p unchanged = all online ₹3,850")
chk(fcd.our_icici_online_p(con, D) == 325000 and fcd.our_portal_p(con, D) == 60000, "icici ₹3,250 · portal ₹600")
chk(fcd.our_icici_online_p(con, D) + fcd.our_portal_p(con, D) == fcd.our_online_p(con, D), "no rupee invented or lost")

doc = cm._docterz(con, D)
cm_por = [o for o in doc["online"] if o.get("channel") == "portal"]
chk(len(cm_por) == 1 and cm_por[0]["patient"] == "Bindu", "the reconciler tags the SAME single portal entry")
chk({o["patient"] for o in por} == {o["patient"] for o in cm_por}, "F-468: MPR page and reconciler agree on what is portal")
chk(doc["tender"]["upi"] == 385000 and doc["tender"]["cash"] == 100000, "revenue untouched: upi ₹3,850 · cash ₹1,000")
src = open(os.path.join(HERE, "clinic_money.py"), encoding="utf-8").read()
chk(src.count('expected_bank = d_t["upi"] - other - portal_p') == 1, "bank expectation subtracts portal, once")
chk(src.count('ours = [o for o in doc["online"] if o.get("channel") != "portal"]') == 1, "portal kept out of pairing, once")
chk("PORTAL_MODES" not in src and "PORTAL_MODES" not in open(os.path.join(HERE,"finance_clinic_day.py"),encoding="utf-8").read(),
    "no mode-label list exists anywhere -- the label is never consulted")
row = cm._portal_month_row(con, D, D)
chk("Portal (Razorpay" in row and "600" in row and "1 payment" in row, "month row: 1 payment, ₹600, by id")
chk(cm._portal_month_row(con, "2026-01-01", "2026-01-31") == "", "a month with no id shows no row")
fsrc = open(os.path.join(HERE, "finance_clinic_day.py"), encoding="utf-8").read()
chk('ours = [o for o in _all if o.get("channel") != "portal"]' in fsrc and "out.append(portal_note)" in fsrc,
    "the MPR page pairs ICICI-only and says what it kept out")

# a database never written since S256: no column at all
old = db(False)
chk(fcd.our_online_p(old, D) == 385000 and fcd.our_portal_p(old, D) == 0, "no column -> everything ICICI, no crash, total intact")
chk(cm._docterz(old, D)["tender"]["upi"] == 385000, "reconciler reads an unmigrated database unchanged")
chk(cm._portal_month_row(old, D, D) == "", "month row silent without the column")
print("\n%d passed, %d failed" % (ok, fail)); sys.exit(1 if fail else 0)
