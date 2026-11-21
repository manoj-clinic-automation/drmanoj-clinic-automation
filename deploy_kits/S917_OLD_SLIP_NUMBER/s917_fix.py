"""s917_fix.py -- S917 one-off (the parent, S498, 21-Nov-2026). Data only, finance.db, in ONE transaction:
  1. slip id 1190 (xp, day 09-Nov, a replacement slip saved by Shavez 15-Nov) carries number 1546 -- the paper of ANOTHER
     patient's 14-Nov X-ray. It takes 1481, the number of the same 9-Nov patient's own paper (slip 1017, voided). 1546 is free
     again for the 14-Nov slip, written by Shavez from that paper.
  2. the discount ask (slip_adjust id 8) still waiting on the VOIDED slip 1481 is withdrawn ('replaced') -- it belongs to no slip.
Every precondition is read first; anything not exactly as found on 21-Nov changes NOTHING. Audited in audit_log.
Usage: s917_fix.py DB [--apply | --revert]   (neither: reads and says what it would do). --revert puts both rows back only while
1546 is still free (the 14-Nov slip not yet written)."""
import datetime as dt, json, sqlite3, sys
DB = sys.argv[1]
APPLY = "--apply" in sys.argv[2:]
REVERT = "--revert" in sys.argv[2:]
WHO = "system S917 (owner's word 21-Nov)"
now = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")
con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
def one(q, a=()):
    return con.execute(q, a).fetchone()
s = one("SELECT * FROM slip WHERE id=1190")
v = one("SELECT * FROM slip WHERE id=1017")
live1481 = one("SELECT id FROM slip WHERE series='xp' AND slip_no=1481 AND state<>'void' AND id<>1190")
ask = one("SELECT * FROM slip_adjust WHERE id=8")
if REVERT:
    if not (s and s["slip_no"] == 1481 and s["state"] == "ok"):
        print("S917_FIX: NOTHING TO REVERT (slip 1190 is not at 1481)"); sys.exit(0)
    if one("SELECT id FROM slip WHERE series='xp' AND slip_no=1546 AND state<>'void'"):
        print("S917_FIX: NOT REVERTED -- 1546 is now the 14-Nov slip; tell Claude"); sys.exit(2)
    con.execute("BEGIN IMMEDIATE")
    con.execute("UPDATE slip SET slip_no=1546, updated_by=?, updated_at=? WHERE id=1190 AND slip_no=1481", (WHO, now.replace("T", " ")))
    con.execute("UPDATE slip_adjust SET state='pending', checked_by='', checked_at='', check_note='' WHERE id=8 AND state='replaced'")
    con.execute("INSERT INTO audit_log(table_name,row_id,action,before_json,after_json,by_whom,at) VALUES ('slip',1190,'slip_renumber',?,?,?,?)",
                (json.dumps(json.dumps({"slip_no": 1481})), json.dumps(json.dumps({"slip_no": 1546, "why": "S917 undo"})), WHO, now))
    con.commit()
    print("S917_FIX: REVERTED -- slip 1190 back to 1546; ask 8 pending"); sys.exit(0)
if s and s["slip_no"] == 1481 and s["state"] == "ok" and (not ask or ask["state"] != "pending"):
    print("S917_FIX: ALREADY DONE (slip 1190 is 1481; the ask on 1481 not pending)"); sys.exit(0)
bad = []
if not s or (s["series"], s["slip_no"], s["day"], s["state"]) != ("xp", 1546, "2026-11-09", "ok"):
    bad.append("slip 1190 is not xp 1546 / 09-Nov / ok")
if not v or (v["series"], v["slip_no"], v["day"], v["state"]) != ("xp", 1481, "2026-11-09", "void"):
    bad.append("slip 1017 is not xp 1481 / 09-Nov / void")
if s and v and (not s["clinic_id"] or s["clinic_id"] != v["clinic_id"]):
    bad.append("slips 1190 and 1017 are not the same patient")
if live1481:
    bad.append("another live slip holds 1481")
if not ask or (ask["slip_id"], ask["kind"], ask["state"]) != (1017, "discount", "pending"):
    bad.append("slip_adjust 8 is not the pending discount on slip 1017")
if bad:
    print("S917_FIX: NOT AS FOUND -- nothing changed: " + "; ".join(bad)); sys.exit(2)
if not APPLY:
    print("S917_FIX: WOULD renumber slip 1190 1546 -> 1481 and withdraw ask 8 (dry)"); sys.exit(0)
try:
    con.execute("BEGIN IMMEDIATE")
    n1 = con.execute("UPDATE slip SET slip_no=1481, note=?, updated_by=?, updated_at=? WHERE id=1190 AND slip_no=1546 AND state='ok'",
                     ("tha 1546 (14-Nov ki X-ray parchi ka number); is marij ki apni parchi 1481 -- S917", WHO,
                      now.replace("T", " "))).rowcount
    n2 = con.execute("UPDATE slip_adjust SET state='replaced', checked_by=?, checked_at=?, check_note=? WHERE id=8 AND slip_id=1017 "
                     "AND state='pending'", (WHO, now.replace("T", " "), "S917: the slip it was on (1481) is voided; re-written as slip 1190")).rowcount
    if n1 != 1 or n2 != 1:
        raise RuntimeError("rows %d/%d" % (n1, n2))
    for row, act, before, after in ((1190, "slip_renumber", {"slip_no": 1546}, {"slip_no": 1481, "why": "S917: 1546 is the 14-Nov X-ray paper"}),
                                     (1017, "slip_adjust_withdrawn", {"ask": 8, "state": "pending"}, {"ask": 8, "state": "replaced"})):
        con.execute("INSERT INTO audit_log(table_name,row_id,action,before_json,after_json,by_whom,at) VALUES ('slip',?,?,?,?,?,?)",
                    (row, act, json.dumps(json.dumps(before)), json.dumps(json.dumps(after)), WHO, now))
    con.commit()
except Exception as ex:                                  # noqa: BLE001
    con.rollback()
    print("S917_FIX: FAILED, rolled back -- nothing changed: %s" % ex); sys.exit(3)
s = one("SELECT slip_no FROM slip WHERE id=1190"); a = one("SELECT state FROM slip_adjust WHERE id=8")
print("S917_FIX: APPLIED -- slip 1190 now %d; ask 8 %s; 1546 free for the 14-Nov slip" % (s["slip_no"], a["state"]))
