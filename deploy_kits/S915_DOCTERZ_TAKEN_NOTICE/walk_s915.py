"""walk_s915.py -- kit S915_DOCTERZ_TAKEN_NOTICE on a MADE-UP docterz_export (no patient, no number, no real store).
usage: python walk_s915.py <dir holding docterz_taken_notice.py + docterz_missing_alert.py> <work dir>  -> last line 'WALK n/N'.
--control: the same walk on a broken copy it makes itself (the source rule and the first-run guard removed) -- must go red."""
import datetime as dt, importlib.util, os, shutil, sqlite3, sys

SRC, WORK = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.abspath(os.path.dirname(__file__))]   # F-1441
shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK)
CODE = os.path.join(WORK, "code"); os.makedirs(CODE)
for n in ("docterz_taken_notice.py", "docterz_missing_alert.py"):
    shutil.copy(os.path.join(SRC, n), os.path.join(CODE, n))
if "--control" in sys.argv:
    p = os.path.join(CODE, "docterz_taken_notice.py"); t = open(p, encoding="utf-8").read()
    t = t.replace('if "_manojz_" in nm:', 'if False:').replace("if mark is None:", "if mark is None and False:\n            pass\n        if mark is None:\n            mark = 0\n        if False:")
    open(p, "w", encoding="utf-8").write(t)
spec = importlib.util.spec_from_file_location("dtn", os.path.join(CODE, "docterz_taken_notice.py"))
N = importlib.util.module_from_spec(spec); spec.loader.exec_module(N)
DB, ST, OFF = os.path.join(WORK, "f.db"), os.path.join(WORK, "state.json"), os.path.join(WORK, "_off")
os.makedirs(OFF)
con = sqlite3.connect(DB)
con.execute("CREATE TABLE docterz_export (id INTEGER PRIMARY KEY AUTOINCREMENT, drive_id TEXT, drive_name TEXT, drive_mtime TEXT, md5 TEXT, kind TEXT,"
            " business_date TEXT, rows INTEGER, stored TEXT, status TEXT, note TEXT, taken_at TEXT, due_from TEXT, due_to TEXT)")
def add(did, name, kind, day, rows, status, note="", df="", dto=""):
    con.execute("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at, due_from, due_to)"
                " VALUES (?,?,'',?,?,?,?,'',?,?,'2026-11-20 21:00:00',?,?)", (did, name, did + name, kind, day, rows, status, note, df, dto))
    con.commit()
add("d0", "old.csv", "consultation", "2026-11-19", 30, "current")
add("d1", "clinical_old_manojz_aaaaaa.csv", "clinical", "2026-11-10", 300, "current", "covers 2026-10-01 to 2026-11-10")
SENT, NT = [], []
def pusher(user, payload):
    SENT.append((user, payload)); return (1, 0)
def none_pusher(user, payload):
    SENT.append((user, payload)); return (0, 1)
def ntfy(title, body):
    NT.append((title, body)); return True, "the ntfy topic took it"
NOW = dt.datetime(2026, 11, 20, 21, 5)
R = []
def check(n, ok, why=""):
    R.append(bool(ok)); print(("ok   " if ok else "FAIL ") + n + ((" -- %s" % str(why)[:300]) if (why and not ok) else ""))
def go(**kw):
    kw.setdefault("pusher", pusher); kw.setdefault("ntfy", ntfy)
    return N.run(db=DB, state=ST, now=NOW, off_dir=OFF, **kw)

line = go()
check("T1 first run: the mark set, nothing sent", not SENT and "first run" in line and N.load_state(ST) == 2, line)
add("reception:ab12", "consultation_report_2026-11-20.csv", "consultation", "2026-11-20", 19, "current")
add("1DriveId", "followup_logs_2026-11-21_manojz_c0ffee.csv", "followup", "2026-11-20", 107, "current", "", "2026-11-21", "2026-12-20")
add("owner:manoj:9f", "clinical data report (1).csv", "clinical", "2026-11-20", 51, "current", "covers 2026-11-19 to 2026-11-20")
add("1DriveId2", "consultation_report_2026-11-20 (1).csv", "consultation", "2026-11-20", 12, "quarantined")
add("1DriveId3", "consultation_report_2026-11-20 (2).csv", "consultation", "2026-11-20", 19, "duplicate", "same bytes as export #3")
add("offday:manoj", "not sitting", "consultation", "2026-11-22", 0, "current")
add("1DriveId4", "Product Catalogue.pdf", "unknown", "", 0, "unknown", "not text")
line = go()
check("T2 one push for the pass", len(SENT) == 1, SENT)
body = SENT[0][1]["body"] if SENT else ""
title = SENT[0][1]["title"] if SENT else ""
check("T3 to the owner's login, his Docterz reports page", SENT and SENT[0][0] == "manoj" and SENT[0][1]["url"] == "/finance/console/docterz-reports", SENT)
check("T4 the reception PC named for its agent's report", "Consultation report for Fri 20 Nov — 19 patients — from the reception PC." in body, body)
check("T5 his PC named for a _manojz_ file; the call days given",
      "Follow-up log of Fri 20 Nov — calls due 21 Nov to 20 Dec, 107 rows — from your PC (manojz)." in body, body)
check("T6 an upload on the page named so; the period covered", "Clinical data report — covers 19 Nov to 20 Nov, 51 visit rows — from the Docterz reports page." in body, body)
check("T7 a quarantined report said NOT used, with why", "12 patients — from the reception PC — NOT used (fewer rows than the one already held)." in body, body)
check("T8 duplicate / not-sitting / stray PDF: nothing said", body.count("\n") == 4 and "Catalogue" not in body and "22 Nov" not in body, body)
check("T9 the clinical reach and the day to export from", body.endswith("Clinical data on the server reaches Fri 20 Nov — next time export it from 21 Nov."), body)
check("T10 no file name in the message", ".csv" not in body and ".csv" not in title, body)
check("T11 the title names the time", title == "Docterz reports received (21:05)", title)
check("T12 the mark moves past every row", N.load_state(ST) == 9, N.load_state(ST))
line = go()
check("T13 nothing new: nothing sent", len(SENT) == 1 and line == "", line)
open(os.path.join(OFF, "DOCTERZ_TAKEN_NOTICE_OFF"), "w").close()
add("reception:cd34", "followup_logs (38).csv", "followup", "2026-11-21", 90, "current", "", "2026-11-23", "2026-12-22")
line = go()
check("T14 the off switch: nothing sent, the mark kept", len(SENT) == 1 and "off switch" in line and N.load_state(ST) == 9, line)
os.remove(os.path.join(OFF, "DOCTERZ_TAKEN_NOTICE_OFF"))
line = go(pusher=none_pusher)
check("T15 no device took it: the ntfy topic once", len(NT) == 1 and "Follow-up log of Sat 21 Nov" in NT[0][1], (line, NT))
check("T16 ... and the row told once (mark moved)", N.load_state(ST) == 10, N.load_state(ST))
dry = N.run(db=DB, state=ST, now=NOW, off_dir=OFF, dry=True, since=2, pusher=pusher, ntfy=ntfy)
check("T17 --dry --since: says, sends nothing, writes nothing", "would send" in dry and len(SENT) == 2 and N.load_state(ST) == 10, dry)
for i in range(14):
    add("reception:x%d" % i, "c%d.csv" % i, "consultation", "2026-11-%02d" % (1 + i), 10 + i, "current")
go()
check("T18 many rows: twelve lines and '... and N more'", SENT and "... and 2 more on the Docterz reports page." in SENT[-1][1]["body"], SENT[-1][1]["body"] if SENT else "")
bad = N.run(db=os.path.join(WORK, "nope", "x.db"), state=ST, now=NOW, off_dir=OFF, pusher=pusher, ntfy=ntfy)
check("T19 an unreadable store: one line, nothing sent", "could not be" in bad and len(SENT) == 3, bad)
print("WALK %d/%d" % (sum(R), len(R)))
