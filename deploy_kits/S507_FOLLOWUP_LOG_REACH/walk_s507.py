"""walk_s507.py -- S507_FOLLOWUP_LOG_REACH, session 304 (parent), 10-Oct-2026. The walk the installer runs BEFORE placing.

On a SCRATCH copy of finance.db and a scratch copy of /root/finance's programs (the kit's three over them, unless --control):
  * docterz_pickup.ensure() adds the two columns; backfill_spans() fills them for the follow-up logs already kept;
  * take() on a MADE-UP follow-up log (no patient: an id, a made-up number, one due date -- never real data) records its span
    and says it does not reach the next call day;
  * the two duty lines, evaluated at FIXED times on made-up rows dated in 2031 (nothing real is touched or counted):
    Saturday 21:30 with a log covering only Sunday -> the evening line counts it missing; with a month's log -> not;
    Monday 09:00 -> the morning line counts Saturday's short log missing;
  * the owner's page line; the hint staff read.
The SAME walk on the live programs (--control) must end RED. Prints dates, counts and words only.
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
scr = tempfile.mkdtemp(prefix="s507_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".json")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))
if not a.control:
    for n in ("docterz_pickup.py", "aaj_duties.json", "aaj_seed.py"):
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
SAT = dt.date(2031, 3, 8)                                          # a Saturday, far from any real row
assert SAT.weekday() == 5
SUN, MON = SAT + dt.timedelta(days=1), SAT + dt.timedelta(days=2)


def at(sql, stamp):
    return sql.replace("'now','localtime'", "'%s'" % stamp)


try:
    import docterz_pickup as DP                                    # noqa: E402
    con = sqlite3.connect(db, timeout=60)
    con.row_factory = sqlite3.Row
    DP.ensure(con)
    cols = {r[1] for r in con.execute("PRAGMA table_info(docterz_export)")}
    has = {"due_from", "due_to"} <= cols
    filled = DP.backfill_spans(con) if hasattr(DP, "backfill_spans") else 0
    print("  pass the table: due_from/due_to %s . follow-up logs given their due dates from their own bytes: %d" % ("there" if has else "MISSING", filled))
    if not has:
        red.append("the two columns were not added")
    if has:
        print("  the follow-up logs of the last 10 days, as the server holds them:")
        for r in con.execute("SELECT business_date, rows, due_from, due_to FROM docterz_export WHERE kind='followup' AND status='current' "
                             "AND business_date >= date('now','localtime','-10 day') ORDER BY business_date"):
            ok = (not r["due_to"]) or (not hasattr(DP, "next_call_day")) or r["due_to"] >= DP.next_call_day(r["business_date"])
            print("     %s  %4d rows  due %s .. %s  %s" % (r["business_date"], r["rows"], r["due_from"] or "?", r["due_to"] or "?",
                                                         "reaches the next call day" if ok else "SHORT -- the next call day is not in it"))
    # take() on a made-up follow-up log: one row, due on Sunday
    fake = ("Appointment ID,Patient Name,Mobile No,Due Date\r\nX1,Test Patient,0000000000,%s\r\n" % SUN.strftime("%d-%m-%Y")).encode()
    kind, day, nrows, st, note = DP.take(con, {"id": "walk-s507", "name": "walk.csv", "modifiedTime": "2031-03-08T15:59:00Z"}, fake)
    row = con.execute("SELECT * FROM docterz_export WHERE drive_id='walk-s507'").fetchone()
    span = (row["due_from"], row["due_to"]) if has else ("", "")
    print("  pass take() on a made-up one-day log: %s %s rows=%d -> %s . covers %s .. %s . note: %s" % (kind, day, nrows, st, span[0] or "?", span[1] or "?", note or "-"))
    if span != (SUN.isoformat(), SUN.isoformat()) or "next call day" not in (note or ""):
        red.append("take() did not record the log's reach")
    con.execute("DELETE FROM docterz_export WHERE drive_id='walk-s507'")
    # the duty lines at fixed times
    duties = {d["id"]: d for d in json.load(open(os.path.join(fin, "aaj_duties.json")))["extra"]}
    night, morn = duties["reception.night_exports"]["sql"], duties["reception.docterz_followup"]["sql"]
    ins = ("INSERT INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at%s) "
           "VALUES (?,?,?,?,?,?,?,?,?,?,?%s)") % ((", due_from, due_to", ",?,?") if has else ("", ""))

    def put(did, kind, rows, due_to, status="current"):
        v = [did, "walk", "2031", did, kind, SAT.isoformat(), rows, "", status, "", "2031-03-08 21:00:00"]
        if has:
            v += [(SUN.isoformat() if kind == "followup" else ""), due_to]
        con.execute(ins, v)
    put("w-c", "consultation", 20, "")
    put("w-f1", "followup", 1, SUN.isoformat())
    n1 = con.execute(at(night, "%s 21:30:00" % SAT)).fetchone()[0]
    m1 = con.execute(at(morn, "%s 09:00:00" % MON)).fetchone()[0]
    con.execute("UPDATE docterz_export SET status='superseded' WHERE drive_id='w-f1'")
    put("w-f2", "followup", 120, (SAT + dt.timedelta(days=31)).isoformat())
    n2 = con.execute(at(night, "%s 21:30:00" % SAT)).fetchone()[0]
    m2 = con.execute(at(morn, "%s 09:00:00" % MON)).fetchone()[0]
    print("  pass Saturday 21:30 -- the log covers only Sunday: evening line counts %d missing (of 2); the month's log: %d" % (n1, n2))
    print("  pass Monday 09:00 -- Saturday's short log: morning line %d; the month's log: %d" % (m1, m2))
    if not (n1 == 1 and n2 == 0 and m1 == 1 and m2 == 0):
        red.append("the duty lines do not tell a short log from a whole one (%d %d %d %d)" % (n1, n2, m1, m2))
    con.execute("UPDATE docterz_export SET status='superseded' WHERE drive_id='w-f2'")
    con.execute("UPDATE docterz_export SET status='current' WHERE drive_id='w-f1'")
    lines = DP.owner_lines(con, at=dt.datetime(MON.year, MON.month, MON.day, 11, 0))
    short = [x for x in lines if "reaches only" in x]
    print("  pass the owner's page, Monday 11:00: %s" % (short[0][:120] + "..." if short else "NO line for the short log"))
    if not short:
        red.append("the owner's page says nothing of the short log")
    con.execute("DELETE FROM docterz_export WHERE drive_id LIKE 'w-%'")
    con.rollback()
    os.environ["AAJ_DUTIES_JSON"] = os.path.join(fin, "aaj_duties.json")
    import aaj_kaam                                                # noqa: E402
    res = aaj_kaam.build_all(db)
    got = {i.get("id"): i for i in res.get("items") or []}
    for lid in ("reception.night_exports", "reception.docterz_followup", "reception.docterz_consultation"):
        it = got.get(lid)
        print("  pass the staff list reads %s now: %s" % (lid, ("n=%s%s" % (it.get("n"), (" ERROR " + str(it.get("err"))) if it.get("err") else "")) if it else "NOT READ"))
        if not it or it.get("err"):
            red.append("%s is not read cleanly" % lid)
    import aaj_seed                                                # noqa: E402
    how = aaj_seed.ENGINE.get("reception.night_exports", {}).get("how", "")
    print("  pass the hint reception reads: %s" % how[:110])
    if "agle kaam ke din" not in how:
        red.append("the hint is not in the staff's line")
    con.close()
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S507 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
