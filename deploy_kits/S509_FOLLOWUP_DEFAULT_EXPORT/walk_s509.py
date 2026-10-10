"""walk_s509.py -- S509_FOLLOWUP_DEFAULT_EXPORT, session 304 (parent), 10-Oct-2026. The walk the installer runs BEFORE placing.

On a SCRATCH copy of finance.db and a scratch copy of /root/finance's programs (the kit's two over them, unless --control), with
MADE-UP follow-up logs only (an id, a made-up name and number, due dates in 2031 -- never real data):
  * Docterz's DEFAULT export made on Friday evening (due Friday .. one month) is Friday's log, reaches the next call day, and
    reception's evening line counts it done;
  * the same default export made on Saturday morning at 08:30 is Friday's log (the morning catch-up);
  * a Saturday-evening default export is Saturday's, and reaches Monday;
  * the hint reception reads says to leave Docterz's dates as they are.
The SAME walk on the live programs (--control) must end RED.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
import tempfile

ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True)
ap.add_argument("--fin", default="/root/finance")
ap.add_argument("--db", default="/root/finance/finance.db")
ap.add_argument("--venv", default="")
ap.add_argument("--control", action="store_true")
a = ap.parse_args()
scr = tempfile.mkdtemp(prefix="s509_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".json", ".html")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))
if not a.control:
    for n in ("docterz_pickup.py", "aaj_seed.py"):
        shutil.copy(os.path.join(a.kit, n), os.path.join(fin, n))
db = os.path.join(scr, "fin.db")
src = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
dst = sqlite3.connect(db)
src.backup(dst)
dst.close()
src.close()
os.environ["DOCTERZ_EXPORT_STORE"] = os.path.join(scr, "store")
sys.path.insert(0, fin)
os.chdir(fin)
red = []
FRI, SAT, MON = dt.date(2031, 3, 7), dt.date(2031, 3, 8), dt.date(2031, 3, 10)


def log(start):
    lines = ["Appointment ID,Patient Name,Mobile No,Followup Date"]
    for i in range(31):
        d = start + dt.timedelta(days=i)
        lines.append("X%d,Test Patient,0000000000,%s" % (i, d.strftime("%d-%m-%Y")))
    return ("\r\n".join(lines) + "\r\n").encode()


def utc(ist):
    return (ist - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


try:
    import docterz_pickup as DP                                    # noqa: E402
    con = sqlite3.connect(db, timeout=60)
    con.row_factory = sqlite3.Row
    DP.ensure(con)
    cases = [("Friday 21:00, Docterz's default (Fri .. one month)", "w9-1", FRI, dt.datetime(2031, 3, 7, 21, 0), FRI),
             ("Saturday 08:30, the same default (the morning catch-up)", "w9-2", SAT, dt.datetime(2031, 3, 8, 8, 30), FRI),
             ("Saturday 21:00, Docterz's default (Sat .. one month)", "w9-3", SAT, dt.datetime(2031, 3, 8, 21, 0), SAT)]
    for name, did, start, ist, want in cases:
        kind, day, nrows, st, note = DP.take(con, {"id": did, "name": "walk.csv", "modifiedTime": utc(ist)}, log(start))
        r = con.execute("SELECT due_to FROM docterz_export WHERE drive_id=?", (did,)).fetchone()
        reach = bool(r and r["due_to"] and r["due_to"] >= DP.next_call_day(day)) if day else False
        print("  pass %-56s -> the log of %s (%s), %s" % (name, day, st, "reaches the next call day" if reach else "does NOT reach the next call day"))
        if day != want.isoformat() or not reach:
            red.append("%s: taken as the log of %s, wanted %s" % (name, day, want))
    duties = {d["id"]: d for d in json.load(open(os.path.join(fin, "aaj_duties.json")))["extra"]}
    night = duties["reception.night_exports"]["sql"]
    con.execute("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at) "
                "VALUES ('w9-c','walk','2031','w9-c','consultation',?,20,'','current','','2031-03-07 21:00:00')", (FRI.isoformat(),))
    n = con.execute(night.replace("'now','localtime'", "'2031-03-07 21:30:00'")).fetchone()[0]
    print("  pass reception's evening line, Friday 21:30, after the default export: %d missing of 2" % n)
    if n != 0:
        red.append("the evening line still counts the default export as missing")
    con.rollback()
    con.execute("DELETE FROM docterz_export WHERE drive_id LIKE 'w9-%'")
    con.commit()
    import aaj_seed                                                # noqa: E402
    how = aaj_seed.ENGINE["reception.night_exports"]["how"]
    print("  pass the hint reception reads: %s" % how[:120])
    if "date badalne ki zaroorat nahin" not in how:
        red.append("the hint still asks for a changed date")
    con.close()
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S509 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
