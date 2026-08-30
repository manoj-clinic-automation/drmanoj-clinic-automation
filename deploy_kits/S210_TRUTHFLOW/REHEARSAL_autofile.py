# -*- coding: utf-8 -*-
"""F-87 rehearsal: the D354 autofile block, verbatim logic, on a seeded store."""
import sqlite3, os, io, csv, subprocess, sys
subprocess.check_call([sys.executable, os.path.expanduser("~/s210/seed.py")], stdout=subprocess.DEVNULL)
DB=os.path.expanduser("~/s210/rehearse.db")
con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
con.execute("INSERT OR IGNORE INTO business_unit (code,name) VALUES ('medical','Sanjeevni')")
con.execute("CREATE TABLE IF NOT EXISTS upi_txn (unit TEXT, txn_date TEXT, amount_p INTEGER, rrn TEXT, mode TEXT, txn_time TEXT)")
UNIT="medical"
for iso,cash_p,upi_p in [("2026-08-25",3120000,800000),("2026-08-26",2890000,640000),("2026-08-27",2617900,1117000)]:
    con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by) VALUES ('medical',?,'approved','app','darpan')",(iso,))
    _e=con.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?",(iso,)).fetchone()["id"]
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',?)",(_e,cash_p))
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','upi',?)",(_e,upi_p))
con.commit()

def autofile(iso_d, lines_csv):
    """The patch's block, transcribed."""
    e=con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",(UNIT,iso_d)).fetchone()
    if e: return "already", e["id"]
    _rows=list(csv.DictReader(io.StringIO(lines_csv)))
    _net_p=int(round(sum(float(x.get("amount") or 0) for x in _rows)*100))
    _upi_p=int(con.execute("SELECT COALESCE(SUM(amount_p),0) FROM upi_txn WHERE unit=? AND txn_date=?",(UNIT,iso_d)).fetchone()[0] or 0)
    _cash_p=_net_p-_upi_p
    if _net_p<=0 or _cash_p<0: return "manual", None
    cur=con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at) VALUES (?,?,?,?,?,?)",(UNIT,iso_d,"submitted","app","manoj","2026-08-30"))
    eid=cur.lastrowid
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',?)",(eid,_cash_p))
    if _upi_p: con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','upi',?)",(eid,_upi_p))
    con.commit(); return "filed", eid

def chk(n,c):
    print((" ok  " if c else " FAIL ")+n)
    if not c: global BAD; BAD=True
BAD=False
H="bill_date,bill_no,clinic_id,patient_name,phone_last4,description,amount,mode\n"

# 28-Aug: net 4,120.00 with one CN -150; bank UPI 971 (his real MPR shape)
con.execute("INSERT INTO upi_txn VALUES ('medical','2026-08-28',42500,'r1','UPI','19:36')")
con.execute("INSERT INTO upi_txn VALUES ('medical','2026-08-28',35000,'r2','UPI','15:43')")
con.execute("INSERT INTO upi_txn VALUES ('medical','2026-08-28',13000,'r3','UPI','11:42')")
con.execute("INSERT INTO upi_txn VALUES ('medical','2026-08-28',6600,'r4','UPI','19:55')")
lines=H+"2026-08-28,A1,,X,,,2270.00,CASH\n2026-08-28,A2,4471,Y,,,2000.00,CASH\n2026-08-28,CN1,,Z,,,-150.00,CASH\n"
st,eid=autofile("2026-08-28",lines)
r=con.execute("SELECT mode,amount_p FROM day_line WHERE day_entry_id=? ORDER BY mode",(eid or 0,)).fetchall()
chk("28-Aug files: status=%s"%st, st=="filed")
chk("  cash = net 4,120 - UPI 971 = 3,149.00", dict((x[0],x[1]) for x in r).get("cash")==314900)
chk("  upi = bank truth 971.00", dict((x[0],x[1]) for x in r).get("upi")==97100)
chk("  day_entry status 'submitted' (owner approval queue)", con.execute("SELECT status FROM day_entry WHERE id=?",(eid,)).fetchone()[0]=="submitted")
cl=con.execute("SELECT closing_p FROM v_cash_ledger WHERE unit='medical' ORDER BY business_date DESC LIMIT 1").fetchone()[0]
chk("  ledger closing advances by the cash (86,279+3,149=89,428)", cl==8942800)

# guard 1: CN-heavy day, net negative -> manual
st2,_=autofile("2026-08-29", H+"2026-08-29,CN9,,A,,,-500.00,CASH\n")
chk("net<=0 day stays manual", st2=="manual")
# guard 2: bank UPI exceeds net -> manual
con.execute("INSERT INTO upi_txn VALUES ('medical','2026-08-30',999900,'r9','UPI','10:00')")
st3,_=autofile("2026-08-30", H+"2026-08-30,A9,,B,,,50.00,CASH\n")
chk("UPI-over-net day stays manual", st3=="manual")
# guard 3: already-filed day untouched
st4,_=autofile("2026-08-27", H+"2026-08-27,A5,,C,,,100.00,CASH\n")
chk("an already-filed day is untouched", st4=="already")
n=con.execute("SELECT COUNT(*) FROM day_entry WHERE unit='medical'").fetchone()[0]
chk("exactly one new day created in total", n==4)
print("AUTOFILE REHEARSAL:", "FAILED" if BAD else "PASSED 9/9")
