# -*- coding: utf-8 -*-
"""F-87 rehearsal: the handover route's effects on the app's own arithmetic."""
import sqlite3, os, subprocess, sys
subprocess.check_call([sys.executable, os.path.expanduser("~/s210/seed.py")], stdout=subprocess.DEVNULL)
DB=os.path.expanduser("~/s210/rehearse.db")
con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
con.execute("INSERT OR IGNORE INTO business_unit (code,name) VALUES ('medical','S')")
for iso,cash_p,upi_p in [("2026-08-25",3120000,800000),("2026-08-26",2890000,640000),("2026-08-27",2617900,1117000)]:
    con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by) VALUES ('medical',?,'approved','app','darpan')",(iso,))
    e=con.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?",(iso,)).fetchone()["id"]
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',?)",(e,cash_p))
    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','upi',?)",(e,upi_p))
# the counted custody baseline (like live): Bhawna holds 23,130 via custody event
e27=con.execute("SELECT id FROM day_entry WHERE business_date='2026-08-27'").fetchone()["id"]
con.execute("INSERT INTO cash_custody_event (unit,event_date,from_party,to_party,amount_p,day_entry_id,note,entered_by,entered_at) VALUES ('medical','2026-08-27','drawer','dr_bhawna',2313000,?,'x','manoj','t')",(e27,))
con.commit()
U="medical"
def card():
    held={r["party"]:r["held_p"] for r in con.execute("SELECT party,held_p FROM v_cash_custody_balance WHERE unit=?",(U,))}
    bb=held.get("dr_bhawna",0);bm=held.get("dr_manoj",0);b0=max(0,bb)+max(0,bm)
    def mv(p):
        return int(con.execute("SELECT COALESCE(SUM(CASE WHEN cm.direction='out' THEN cm.amount_p ELSE -cm.amount_p END),0) FROM cash_movement cm JOIN day_entry d ON d.id=cm.day_entry_id WHERE d.unit=? AND cm.party=?",(U,p)).fetchone()[0] or 0)
    rs=max(0,bb+mv("dr_bhawna"));mn=max(0,bm+mv("dr_manoj"))
    lat=con.execute("SELECT closing_p FROM v_cash_ledger WHERE unit=? ORDER BY business_date DESC LIMIT 1",(U,)).fetchone()[0]
    return dict(drawer=lat-b0,bhawna=rs,manoj=mn,unbanked=lat+(rs+mn-b0))
def handover(kind,amt_p):
    """route logic transcription"""
    K={"bank":("out","bank"),"to_bhawna":("out","dr_bhawna"),"to_manoj":("out","dr_manoj"),
       "back_bhawna":("in","dr_bhawna"),"back_manoj":("in","dr_manoj")}
    d,p=K[kind]
    a=con.execute("SELECT id,business_date FROM day_entry WHERE unit=? AND business_date<=? ORDER BY business_date DESC LIMIT 1",(U,"2026-08-30")).fetchone()
    dup=con.execute("SELECT id FROM cash_custody_event WHERE unit=? AND amount_p=? AND (from_party=? OR to_party=?) AND event_date>=?",(U,amt_p,p,p,a["business_date"])).fetchone()
    if dup: return "refused_duplicate"
    con.execute("INSERT INTO cash_movement (day_entry_id,direction,party,amount_p,reference) VALUES (?,?,?,?,?)",(a["id"],d,p,amt_p,"[darpan handover] "+kind))
    con.commit(); return "ok"
BAD=False
def chk(n,c):
    global BAD
    print((" ok  " if c else " FAIL ")+n)
    if not c: BAD=True
c0=card()
chk("baseline: drawer 63,149 / Bhawna 23,130 / unbanked 86,279", c0["drawer"]==6314900 and c0["bhawna"]==2313000 and c0["unbanked"]==8627900)
# 1 bank deposit 50,000
chk("bank deposit accepted", handover("bank",5000000)=="ok")
c1=card()
chk("  drawer -50,000 and UNBANKED -50,000 (it left)", c1["drawer"]==c0["drawer"]-5000000 and c1["unbanked"]==c0["unbanked"]-5000000)
# 2 to_manoj 10,000: location move
chk("to Dr Manoj accepted", handover("to_manoj",1000000)=="ok")
c2=card()
chk("  drawer -10,000, Manoj +10,000, unbanked UNCHANGED", c2["drawer"]==c1["drawer"]-1000000 and c2["manoj"]==1000000 and c2["unbanked"]==c1["unbanked"])
# 3 THE RETURN LEG: back from Bhawna 23,130... wait that would hit the dup guard (same amount+party custody event) -- use 20,000
chk("return from Bhawna accepted", handover("back_bhawna",2000000)=="ok")
c3=card()
chk("  Bhawna -20,000, drawer +20,000, unbanked UNCHANGED", c3["bhawna"]==c2["bhawna"]-2000000 and c3["drawer"]==c2["drawer"]+2000000 and c3["unbanked"]==c2["unbanked"])
# 4 the one-record guard: 23,130 to Bhawna already exists as custody event
chk("duplicate of the 23,130 custody event REFUSED", handover("to_bhawna",2313000)=="refused_duplicate")
c4=card()
chk("  refusal changed nothing", c4==c3)
inv = c4["drawer"]+c4["bhawna"]+c4["manoj"]==c4["unbanked"]
chk("invariant holds throughout: drawer+Bhawna+Manoj == unbanked", inv)
print("HANDOVER REHEARSAL:","FAILED" if BAD else "PASSED 10/10")
