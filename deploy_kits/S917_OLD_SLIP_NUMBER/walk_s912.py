"""walk_s912.py -- kit S912_SLIPS_OLD_DAY: a walk on a MADE-UP root (no real patient, no real number).
usage: python walk_s912.py <dir holding slip_log.py + parchi_desk.py> <work dir>
Prints one line per check and last 'WALK n/N'. Run on the live files it must go red (the control)."""
import importlib.util, os, sqlite3, sys, types

SRC, WORK = sys.argv[1], sys.argv[2]
os.makedirs(WORK, exist_ok=True)
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.abspath(os.path.dirname(__file__))]   # F-1441
os.environ["SLIP_NOW"] = "2026-11-21T10:00:00"
spec = importlib.util.spec_from_file_location("slip_log", os.path.join(SRC, "slip_log.py"))
SL = importlib.util.module_from_spec(spec); sys.modules["slip_log"] = SL; spec.loader.exec_module(SL)
from flask import Flask  # noqa: E402

ADJ = """CREATE TABLE IF NOT EXISTS slip_adjust (id INTEGER PRIMARY KEY AUTOINCREMENT, slip_id INTEGER NOT NULL, item_id INTEGER,
 kind TEXT NOT NULL, amount_p INTEGER NOT NULL DEFAULT 0, reason TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',
 cancel_how TEXT NOT NULL DEFAULT '', clinic_id TEXT NOT NULL DEFAULT '', day TEXT NOT NULL, made_by TEXT NOT NULL, made_at TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending', checked_by TEXT NOT NULL DEFAULT '', checked_at TEXT NOT NULL DEFAULT '', check_note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS owner_service (id INTEGER PRIMARY KEY, kind TEXT, name TEXT, price_p INTEGER, active INTEGER, side TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, table_name TEXT, row_id INTEGER, action TEXT,
 before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT);"""
dbp = os.path.join(WORK, "walk.db")
if os.path.exists(dbp):
    os.remove(dbp)
con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row
SL._schema_done = False
def _aud(con_, table, row_id, action, before=None, after=None, who=""):
    con_.execute("INSERT INTO audit_log(table_name,row_id,action,before_json,after_json,by_whom,at) VALUES (?,?,?,?,?,?,'w')",
                 (table, row_id, action, before, after, who))
SL._audit = _aud
SL.ensure(con); con.executescript(ADJ)
con.execute("UPDATE slip_book SET first_no=1401, last_no=1800, start_no=1501 WHERE series='xp'")
con.execute("INSERT INTO owner_service VALUES (1,'xray','Knee AP & Lateral view',50000,1,'','approved')")
D7, D6, D20, D40 = "2026-11-14", "2026-11-15", "2026-11-01", "2026-10-12"
def slip(no, day, state, cid):
    return con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, no_id_name, is_new, name_seen, state, logged_by, logged_at, "
                       "updated_by, updated_at) VALUES ('xp',?,?,?,'',0,'',?,'w','2026-11-15 11:00:00','w','2026-11-15 11:00:00')",
                       (no, day, cid, state)).lastrowid
for n in range(1530, 1546):
    slip(n, D7, "ok", "9%03d" % n)
con.execute("DELETE FROM slip WHERE slip_no IN (1535, 1539, 1541, 1543, 1544)")
s35 = slip(1535, D7, "cancelled", "cancel"); s39 = slip(1539, D7, "cancelled", "cancel")
s41 = slip(1541, D6, "cancelled", "cancel"); s43 = slip(1543, D7, "spoilt", ""); s44 = slip(1544, D7, "cancelled", "cancel")
for sid, st in ((s35, "pending"), (s39, "approved"), (s41, "pending"), (s44, "pending")):
    con.execute("INSERT INTO slip_adjust(slip_id, kind, cancel_how, clinic_id, day, made_by, made_at, state) "
                "VALUES (?,'cancel','never_taken','cancel',?, 'w','2026-11-15 11:29:00',?)", (sid, D7, st))
slip(1565, "2026-11-20", "ok", "9565")
s66 = slip(1566, "2026-11-21", "cancelled", "cancel")
con.commit()
ITEM = [{"kind": "xray", "service_id": 1, "name": "Knee AP & Lateral view", "side": "", "price_p": 50000}]
R = []
def check(name, ok, why=""):
    R.append(bool(ok)); print(("ok   " if ok else "FAIL ") + name + ((" -- " + why) if (why and not ok) else ""))
def tryslip(no, cid, day):
    try:
        sid, _n = SL.log_slip(con, "shavez", "xp", no, cid, "", ITEM, day=day)
        return sid, None
    except SL.SlipError as e:
        con.rollback(); return None, str(e)

# 1-3 the window: a month back
check("W1 writing: a day 20 days back is accepted", getattr(SL, "_entry_day", SL._late_day)(D20) == D20)
check("W2 writing: a day 40 days back is refused", getattr(SL, "_entry_day", SL._late_day)(D40) is None)
check("W4 edits / removals / radd stay at 7 days", SL._late_day(D20) is None and SL.LATE_DAYS == 7)
check("W3 the day 7 days back still accepted", SL._late_day(D7) == D7)
# 4-7 a number marked radd (pending ask) on that day is written as the parchi it was
sid, err = tryslip(1535, "9900", D7)
r = con.execute("SELECT state, clinic_id, day FROM slip WHERE id=?", (s35,)).fetchone()
check("R1 radd 1535 (pending ask, same day) written", sid == s35 and err is None, err or "")
check("R2 it is now ok with the patient's ID on its day", r["state"] == "ok" and r["clinic_id"] == "9900" and r["day"] == D7)
a = con.execute("SELECT state, check_note FROM slip_adjust WHERE slip_id=?", (s35,)).fetchone()
check("R3 its radd ask is set aside (replaced)", a["state"] == "replaced" and "S912" in a["check_note"])
check("R4 one item on it", con.execute("SELECT COUNT(*) FROM slip_item WHERE slip_id=?", (s35,)).fetchone()[0] == 1)
au = con.execute("SELECT COUNT(*) FROM audit_log WHERE action='slip_radd_written_s912' AND row_id=?", (s35,)).fetchone()[0]
check("R5 audited", au == 1)
# 8 an approved radd is refused, with a reason
sid, err = tryslip(1539, "9901", D7)
check("R6 radd 1539 approved by Sir: refused", sid is None and err and "manzoor" in err, err or "saved")
check("R7 1539 untouched", con.execute("SELECT state FROM slip WHERE id=?", (s39,)).fetchone()[0] == "cancelled")
# a radd number of ANOTHER day is refused and the message names its day
sid, err = tryslip(1541, "9902", D7)
check("R8 radd of 15-Nov written as 14-Nov: refused, its day named", sid is None and err and "15-Nov" in err, err or "saved")
# kharab (spoilt, no ask) on that day: written
sid, err = tryslip(1543, "9903", D7)
check("R9 kharab 1543 (no ask): refused, named kharab", sid is None and err and "kharab" in err, err or "saved")
# an ok number: refused, its day + ID named
sid, err = tryslip(1536, "9904", D7)
check("R10 a written number: refused naming its day and ID", sid is None and err and "14-Nov" in err and "91536" in err, err or "saved")
# a free number of an old day: still written; numbers after it are not marked chhoota
sid, err = tryslip(1520, "9905", D7)
check("R11 a free number on an old day written", sid is not None and err is None, err or "")
check("R12 no chhoota numbers made by an old-day write",
      con.execute("SELECT COUNT(*) FROM slip WHERE state='missing'").fetchone()[0] == 0)
# today's next number is unchanged by all this
check("R13 today's next number still 1567", SL.next_no(con, "xp") == 1567, str(SL.next_no(con, "xp")))
sid, err = tryslip(1566, "9906", "2026-11-21")
check("R14 a radd number of TODAY stays refused", sid is None and err and "radd" in err, err or "saved")
con.execute("UPDATE slip SET state='cancelled', clinic_id='cancel' WHERE id=?", (s43,)); con.commit()
sid, err = tryslip(1543, "9908", D7)
check("R16 a radd with NO ask (not Shavez's pending one): refused", sid is None and err and "radd" in err, err or "saved")
try:
    sid2, note = SL.log_slip(con, "shavez", "xp", 1544, "9907", "", ITEM, day=D7)
except SL.SlipError as e:
    con.rollback(); sid2, note = None, str(e)
check("R15 the save says the number was radd before", sid2 == s44 and "pehle radd" in note, note)

# the old page's form
app = Flask("w")
SL._db = lambda: con
with app.test_request_context("/finance/slips?s=xp&day=%s" % D7):
    nx, head = SL._entry_head(con, "xp")
check("F1 old day: number box empty", 'value=""' in head and "1567" not in head.split("book")[0], head[:300])
check("F2 old day: says whose number", "us din ki parchi ka number" in head)
check("F3 old day: the Din list holds that day, selected", ('value="%s" selected' % D7) in head)
with app.test_request_context("/finance/slips?s=xp&day=%s" % D20):
    nx, head = SL._entry_head(con, "xp")
check("F4 20 days back: the Din list holds it, selected", ('value="%s" selected' % D20) in head)
check("F5 the Din list is short (<= 16 days)", head.count("<option") <= 16, str(head.count("<option")))
with app.test_request_context("/finance/slips?s=xp"):
    nx, head = SL._entry_head(con, "xp")
check("F6 today: number box shows the next number", 'value="1567"' in head)
with app.test_request_context("/finance/slips?s=xp&day=%s&no=1535" % D7):
    nx, head = SL._entry_head(con, "xp")
check("F7 an error round-trip keeps the typed number", 'value="1535"' in head)

# the desk
desk = open(os.path.join(SRC, "parchi_desk.py"), encoding="utf-8").read()
check("D1 desk: an old day's number boxes start empty", "oldDay?'':(st.nx_xp||'')" in desk and "oldDay?'':(st.nx_opd||'')" in desk)
check("D2 desk: its own day list and window unchanged", "for i in range(SL.LATE_DAYS + 1):" in desk)
print("WALK %d/%d" % (sum(R), len(R)))
