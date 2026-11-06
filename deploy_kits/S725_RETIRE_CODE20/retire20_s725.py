#!/usr/bin/env python3
"""retire20_s725.py -- kit S725 (session 390, the parent, 06-Nov-2026). The leaving of staff 20 'Arjun' on the exit register.

The owner: Arjun left on 30-Sep (D824, 02-Nov); "paid and all his dues cleared" (06-Nov 14:10 IST). The exit record
EXIT-2026-0002 was opened through the owner's own page at S390 (06-Nov 15:4x IST) with its first two steps ticked
(decided; portal login -- he never had one). Its Emp Code was left blank, and the register's own 'removed from the
biometric device' step retires only the code ALREADY on the record -- so code 20 would never be retired. This tool:
  1  EXIT-2026-0002 (kind EXIT, person Arjun, open): emp_code '20' (only if blank).
  2  emp_code 20 ('Arjun'): retired 2026-09-30 (only if not retired) -- never deleted, never given to anyone again.
  3  one joiner_event row saying so.
Every guard holds or nothing is written; one transaction; a backup of finance.db first (sqlite's backup API).
  python retire20_s725.py <finance.db> [--dry]      rc 0 done / already / dry . rc 2 stopped"""
import datetime as dt, os, sqlite3, sys

REF, CODE, NAME, LAST = "EXIT-2026-0002", 20, "arjun", "2026-09-30"
BY = "Claude (kit S725)"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def stop(why):
    print("STOPPED: %s. Nothing was written." % why)
    sys.exit(2)


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    db, dry = sys.argv[1], "--dry" in sys.argv
    if not os.path.isfile(db):
        stop("no database at %s" % db)
    con = sqlite3.connect(db, timeout=30)
    con.row_factory = sqlite3.Row
    j = con.execute("SELECT * FROM joiner WHERE ref=?", (REF,)).fetchone()
    if not j:
        stop("no record %s" % REF)
    if j["kind"] != "EXIT" or (j["person"] or "").strip().lower() != NAME:
        stop("%s is not the leaving of Arjun (kind %s, person %s)" % (REF, j["kind"], j["person"]))
    if j["status"] == "COMPLETE":
        stop("%s is already complete -- not the record this kit was built for" % REF)
    if (j["emp_code"] or "") not in ("", str(CODE)):
        stop("%s carries Emp Code %s, not 20" % (REF, j["emp_code"]))
    e = con.execute("SELECT * FROM emp_code WHERE code=?", (CODE,)).fetchone()
    if not e:
        stop("code 20 is not on the code register")
    if (e["person"] or "").strip().lower() != NAME:
        stop("code 20 belongs to '%s', not Arjun -- a name is not a person" % e["person"])
    other = con.execute("SELECT ref FROM joiner WHERE emp_code=? AND ref<>?", (str(CODE), REF)).fetchone()
    if other:
        stop("code 20 is on another record (%s)" % other["ref"])
    todo = []
    if (j["emp_code"] or "") == "":
        todo.append("record %s: Emp Code 20" % REF)
    if not e["retired_on"]:
        todo.append("code 20 (Arjun): retired %s, never to be given again" % LAST)
    if not todo:
        print("ALREADY: %s carries code 20 and code 20 is retired (%s)." % (REF, e["retired_on"]))
        return 0
    for t in todo:
        print("  " + t)
    if dry:
        print("DRY: nothing written.")
        return 0
    bak = "%s.bak_S725_%s" % (db, dt.datetime.now(IST).strftime("%Y%m%d-%H%M%S"))
    d = sqlite3.connect(bak)
    con.backup(d)
    d.close()
    now = dt.datetime.now(IST).isoformat(timespec="seconds")
    try:
        con.execute("BEGIN IMMEDIATE")
        if (j["emp_code"] or "") == "":
            con.execute("UPDATE joiner SET emp_code=?, updated_at=? WHERE ref=? AND COALESCE(emp_code,'')=''", (str(CODE), now, REF))
        if not e["retired_on"]:
            con.execute("UPDATE emp_code SET retired_on=? WHERE code=? AND retired_on IS NULL", (LAST, CODE))
        con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) VALUES (?,?,?,?,?)",
                    (j["id"], now, BY, "EMP_CODE_RETIRED",
                     "code 20 on the record and retired on %s (left 30-Sep, D824; paid, dues cleared -- the owner 06-Nov)" % LAST))
        con.commit()
    except Exception as ex:                                 # noqa: BLE001
        con.rollback()
        stop("the write failed (%s) -- rolled back" % ex)
    r = con.execute("SELECT j.emp_code, c.retired_on FROM joiner j, emp_code c WHERE j.ref=? AND c.code=?", (REF, CODE)).fetchone()
    con.close()
    if not (r and r[0] == str(CODE) and r[1]):
        print("!! the read-back is not as written -- the backup is %s" % bak)
        return 2
    print("written; read back; backup %s" % os.path.basename(bak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
