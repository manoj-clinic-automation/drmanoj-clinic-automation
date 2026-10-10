"""walk_s508.py -- S508_EXPORTS_CONFIRMED, session 304 (parent), 10-Oct-2026. The walk the installer runs BEFORE placing.

On a SCRATCH copy of finance.db and a scratch copy of /root/finance's programs (the kit's two over them, unless --control), with
MADE-UP export rows dated in 2031 only (no patient, nothing real counted): reception's 'Jaane se pehle' line says, in green, that
both Docterz reports are on the server -- after 19:00 on a working day, both there, the follow-up log reaching the next call
day; and says nothing before 19:00, on a Sunday, with one report missing, or with a short follow-up log. The reception list is
then drawn with that line done, and the green row is in it. The SAME walk on the live programs (--control) must end RED.
"""
import argparse
import datetime as dt
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
scr = tempfile.mkdtemp(prefix="s508_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".json", ".html")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))
if not a.control:
    for n in ("aaj_kaam.py", "aaj_kaam.html"):
        shutil.copy(os.path.join(a.kit, n), os.path.join(fin, n))
db = os.path.join(scr, "fin.db")
src = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
dst = sqlite3.connect(db)
src.backup(dst)
dst.close()
src.close()
os.environ["AAJ_DUTIES_JSON"] = os.path.join(fin, "aaj_duties.json")
sys.path.insert(0, fin)
os.chdir(fin)
red = []
FRI, SAT = dt.date(2031, 3, 7), dt.date(2031, 3, 8)
assert FRI.weekday() == 4
try:
    import aaj_kaam as K                                           # noqa: E402
    con = sqlite3.connect(db)
    cols = {r[1] for r in con.execute("PRAGMA table_info(docterz_export)")}
    if "due_to" not in cols:                                       # S507's two columns (the walk works with or without them)
        con.execute("ALTER TABLE docterz_export ADD COLUMN due_from TEXT NOT NULL DEFAULT ''")
        con.execute("ALTER TABLE docterz_export ADD COLUMN due_to TEXT NOT NULL DEFAULT ''")

    def put(did, kind, day, rows, due_to, taken):
        con.execute("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at, due_to) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (did, "walk", "2031", did, kind, day.isoformat(), rows, "", "current", "", taken, due_to))
    put("w1", "consultation", FRI, 20, "", "%s 21:02:00" % FRI)
    put("w2", "followup", FRI, 120, (FRI + dt.timedelta(days=30)).isoformat(), "%s 21:03:00" % FRI)
    put("w3", "consultation", SAT, 18, "", "%s 21:02:00" % SAT)
    put("w4", "followup", SAT, 1, (SAT + dt.timedelta(days=1)).isoformat(), "%s 21:03:00" % SAT)   # Sunday only: short
    con.commit()
    con.close()

    def said(now):
        rd = K.Reader(db, now=now)
        try:
            f = getattr(K, "_exports_confirmed", None)
            return f(rd) if f else None
        finally:
            rd.close()
    cases = [("Friday 21:30, both there", dt.datetime(2031, 3, 7, 21, 30), True), ("Friday 18:30", dt.datetime(2031, 3, 7, 18, 30), False),
             ("Saturday 21:30, follow-up log covers Sunday only", dt.datetime(2031, 3, 8, 21, 30), False),
             ("Sunday 21:30", dt.datetime(2031, 3, 9, 21, 30), False), ("Thursday 21:30, nothing there", dt.datetime(2031, 3, 6, 21, 30), False)]
    for name, now, want in cases:
        t = said(now)
        print("  pass %-48s -> %s" % (name, t if t else "(no green line)"))
        if bool(t) != want:
            red.append("%s: %s" % (name, "no green line" if want else "a green line where none belongs"))
    rd = K.Reader(db, now=dt.datetime(2031, 3, 7, 21, 30))
    try:
        doc = rd.people.get("reception")
        real = K.line_state
        K.line_state = lambda r, ln: (dict(kind="job", due=False, err=None, since=None, held=None, door=None, how="", tile=None, period=None, fetch=None)
                                      if ln["id"] == "reception.night_exports" else real(r, ln))
        lst = K.person_list(rd, doc) if doc else None
        K.line_state = real
        rows = [r for sec in (lst or {}).get("sections", {}).values() for r in sec if r.get("kind") == "done"]
        print("  pass reception's list, Friday 21:30: %s" % (rows[0]["text"] if rows else "NO green row (reception's list: %s)" % ("found" if doc else "not found")))
        if not rows:
            red.append("the green row is not on reception's list")
    finally:
        rd.close()
    page = open(os.path.join(fin, "aaj_kaam.html"), encoding="utf-8").read()
    if "r.kind==='done'" not in page:
        red.append("the page does not draw a done row")
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S508 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
