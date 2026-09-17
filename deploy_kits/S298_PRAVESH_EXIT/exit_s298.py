#!/usr/bin/env python3
"""exit_s298.py -- S298 (17-Sep-2026). Finishes the leaving of Pravesh: the step the exit page calls
'staff master rebuilt', which is not a tick but three real changes nobody had made.

WHAT WAS TRUE ON 17-Sep (read, not assumed). EXIT-2026-0001 ('parvesh') had six of seven steps ticked on
16-Sep, but: staff_master.csv still carried Pravesh (code 17) as active 'Y'; the attendance register
still had him active; and code 17 was never retired, because the record carried no Emp Code when
'removed from the biometric device' was ticked.

WHAT IT CHANGES, and only after every guard holds (one refusal writes nothing):
  1  /root/staff_master.csv          the one row with user_id 17 and name Pravesh: active Y -> N.
                                     Every other line is left byte-for-byte as it was.
  2  staff_register.db, table staff  the one active row named Pravesh: last_working = 2026-08-31,
                                     active = 0 -- exactly what the register's own profile page does
                                     for a resignation (save_profile). Days up to 31-Aug keep him.
                                     One audit_log row.
  3  finance.db, the exit register   emp_code 17 on EXIT-2026-0001; code 17 retired on 2026-08-31
                                     (never deleted, never reissued); step STAFF_MASTER ticked with
                                     what was done; the record COMPLETE.
GUARD THAT PROTECTS MONEY. att_month_report.py drops an inactive row from EVERY month it runs, so
August must already be LOCKED in the register (locked_run 2026-08 status locked) -- his August pay
is then frozen in the locked run. Not locked -> nothing written.
Read-only evidence printed: his punches after 2026-08-31 in /root/punches.csv (device still has him?).

Backups before any write: staff_master.csv.bak_S298_<stamp>, and both databases through sqlite's backup
API. --undo reverses exactly these changes from the state file it leaves. Names only (F-31).

Usage: exit_s298.py [--dry] [--undo] [--selftest] [--finance-db P] [--register-db P] [--staff-master P]
                    [--punches P] [--state P]
Exit 0 done / dry / already · 1 refused or failed
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time

REF, UID, NAME, LAST = "EXIT-2026-0001", 17, "pravesh", "2026-08-31"
RECORD_NAMES = ("parvesh", "pravesh")
PRIOR_STEPS = ("DECIDED", "PORTAL_DISABLED", "BIOMETRIC_REMOVED", "ROSTER_INACTIVE",
               "DUES_SETTLED", "ITEMS_RETURNED")
BY = "Claude (kit S298)"
DETAIL = ("staff master: Pravesh (code 17) inactive; attendance register: last working day "
          "31-Aug-2026; code 17 retired -- he no longer appears")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now_ist():
    return dt.datetime.now(IST)


def read_master(path):
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    lines = text.splitlines(keepends=True)
    header = [h.strip() for h in next(csv.reader([lines[0].lstrip("\ufeff")]))]   # a BOM is kept, not parsed
    return raw, lines, header


def master_hits(lines, header):
    iu, iname, iact = header.index("user_id"), header.index("name"), header.index("active")
    hits = []
    for n, line in enumerate(lines[1:], 1):
        if not line.strip():
            continue
        f = next(csv.reader([line]))
        if len(f) > iu and f[iu].strip() == str(UID):
            hits.append((n, f, f[iname].strip().lower(), f[iact].strip().upper()))
    return hits, iact


def edit_line(line, fields, iact, value):
    end = line[len(line.rstrip("\r\n")):]
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow(fields[:iact] + [value] + fields[iact + 1:])
    return buf.getvalue() + end


def plan(a):
    """Returns (todo dict, already list, refused list, evidence list)."""
    todo, done, bad, ev = {}, [], [], []
    # 1 staff master
    try:
        _, lines, header = read_master(a.staff_master)
        hits, iact = master_hits(lines, header)
        if len(hits) != 1:
            bad.append("staff master: %d rows with code %d (need exactly 1)" % (len(hits), UID))
        elif hits[0][2] != NAME:
            bad.append("staff master: code %d is '%s', not Pravesh" % (UID, hits[0][1][header.index('name')]))
        elif hits[0][3] == "N":
            done.append("staff master: Pravesh already inactive")
        elif hits[0][3] != "Y":
            bad.append("staff master: Pravesh active='%s' (expected Y)" % hits[0][3])
        else:
            todo["master"] = hits[0][0]
    except (OSError, ValueError, StopIteration) as e:
        bad.append("staff master unreadable: %s" % e)
    # register
    rc = sqlite3.connect(a.register_db, timeout=30)
    rc.row_factory = sqlite3.Row
    try:
        lk = rc.execute("SELECT status FROM locked_run WHERE ym='2026-08'").fetchone()
        if not lk or lk["status"] != "locked":
            bad.append("August 2026 is not LOCKED in the register (%s) -- his August pay must be frozen first"
                       % (lk["status"] if lk else "no run"))
        rows = [r for r in rc.execute("SELECT staff_id, name, active, last_working FROM staff")
                if (r["name"] or "").strip().lower().split()[:1] == [NAME]]
        if len(rows) != 1:
            bad.append("register: %d staff rows named Pravesh (need exactly 1)" % len(rows))
        elif rows[0]["active"] == 0 and rows[0]["last_working"]:
            done.append("register: Pravesh already left (last working %s)" % rows[0]["last_working"])
        elif rows[0]["active"] != 1 or rows[0]["last_working"]:
            bad.append("register: Pravesh row is half-changed (active %s, last working %s)"
                       % (rows[0]["active"], rows[0]["last_working"]))
        else:
            todo["register"] = rows[0]["staff_id"]
    finally:
        rc.close()
    # exit register
    fc = sqlite3.connect(a.finance_db, timeout=30)
    fc.row_factory = sqlite3.Row
    try:
        j = fc.execute("SELECT id, kind, person, status, emp_code, updated_at FROM joiner WHERE ref=?", (REF,)).fetchone()
        if not j or j["kind"] != "EXIT" or (j["person"] or "").strip().lower() not in RECORD_NAMES:
            bad.append("exit register: %s is not Pravesh's exit" % REF)
        else:
            steps = {r["step"]: r["done_on"] for r in fc.execute(
                "SELECT step, done_on FROM joiner_step WHERE joiner_id=?", (j["id"],))}
            if steps.get("STAFF_MASTER"):
                done.append("exit register: %s already complete" % REF)
            elif [s for s in PRIOR_STEPS if not steps.get(s)]:
                bad.append("exit register: steps not ticked yet: %s"
                           % ", ".join(s for s in PRIOR_STEPS if not steps.get(s)))
            elif j["emp_code"] not in (None, "", str(UID)):
                bad.append("exit register: record carries code %s, not %d" % (j["emp_code"], UID))
            else:
                code = fc.execute("SELECT person, retired_on FROM emp_code WHERE code=?", (UID,)).fetchone()
                if code and (code["person"] or "").strip().lower() != NAME:
                    bad.append("code register: code %d belongs to %s" % (UID, code["person"]))
                else:
                    todo["joiner"] = {"id": j["id"], "status": j["status"], "emp_code": j["emp_code"], "updated_at": j["updated_at"],
                                      "code_row": bool(code), "retired_on": code["retired_on"] if code else None}
    finally:
        fc.close()
    # evidence: punches after his last day
    try:
        n, last = 0, None
        with open(a.punches, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if str(r.get("user_id", "")).strip() == str(UID) and (r.get("datetime") or "")[:10] > LAST:
                    n += 1
                    last = max(last or "", r["datetime"][:16])
        ev.append("punches under code %d after %s: %d%s" % (UID, LAST, n, (" (latest %s)" % last) if last else
                                                           " -- the device is not recording him"))
    except OSError:
        ev.append("punches file not readable -- no evidence either way")
    return todo, done, bad, ev


def backup_db(path, stamp):
    dst = "%s.bak_S298_%s" % (path, stamp)
    s, d = sqlite3.connect(path, timeout=30), sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()
    return dst


def apply(a, todo, stamp):
    state = {"stamp": stamp}
    if "master" in todo:
        bak = "%s.bak_S298_%s" % (a.staff_master, stamp)
        shutil.copy2(a.staff_master, bak)
        raw, lines, header = read_master(a.staff_master)
        hits, iact = master_hits(lines, header)
        n, f = hits[0][0], hits[0][1]
        lines[n] = edit_line(lines[n], f, iact, "N")
        tmp = a.staff_master + ".s298tmp"
        with open(tmp, "wb") as fh:
            fh.write("".join(lines).encode("utf-8"))
        shutil.copymode(a.staff_master, tmp)
        os.replace(tmp, a.staff_master)
        state["master"] = {"line": n, "backup": bak}
        print("  staff master: Pravesh active Y -> N (backup %s)" % bak)
    if "register" in todo:
        bak = backup_db(a.register_db, stamp)
        con = sqlite3.connect(a.register_db, timeout=30)
        with con:
            con.execute("UPDATE staff SET last_working=?, active=0 WHERE staff_id=? AND active=1", (LAST, todo["register"]))
            con.execute("INSERT INTO audit_log(entity,entity_ref,action,old_value,new_value,actor,ts,note) "
                        "VALUES('staff',?, 'exit_s298','active=1','active=0 last_working=%s',?,?,?)" % LAST,
                        (str(todo["register"]), BY, now_ist().strftime("%Y-%m-%d %H:%M:%S"), REF))
        con.close()
        state["register"] = {"staff_id": todo["register"], "backup": bak}
        print("  register: Pravesh last working day %s, inactive (backup %s)" % (LAST, bak))
    if "joiner" in todo:
        t = todo["joiner"]
        bak = backup_db(a.finance_db, stamp)
        con = sqlite3.connect(a.finance_db, timeout=30)
        today = now_ist().strftime("%Y-%m-%d")
        with con:
            if t["code_row"]:
                if not t["retired_on"]:
                    con.execute("UPDATE emp_code SET retired_on=? WHERE code=?", (LAST, UID))
            else:
                con.execute("INSERT INTO emp_code (code,person,issued_on,retired_on,source,note) "
                            "VALUES (?,?,?,?,?,?)", (UID, "Pravesh", None, LAST, "roster", REF))
            con.execute("UPDATE joiner SET emp_code=? WHERE id=?", (str(UID), t["id"]))
            con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) VALUES (?,?,?,?,?)",
                        (t["id"], "STAFF_MASTER", today, BY, DETAIL))
            con.execute("UPDATE joiner SET status='COMPLETE', closed_on=?, closed_by=?, updated_at=? WHERE id=?",
                        (today, BY, now_ist().isoformat(timespec="seconds"), t["id"]))
            con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) VALUES (?,?,?,?,?)",
                        (t["id"], now_ist().isoformat(timespec="seconds"), BY, "STAFF_MASTER", DETAIL))
        con.close()
        state["joiner"] = dict(t, backup=bak)
        print("  exit register: code %d retired %s, step 7 ticked, %s COMPLETE (backup %s)" % (UID, LAST, REF, bak))
    with open(a.state, "w") as fh:
        json.dump(state, fh)
    return state


def undo(a):
    if not os.path.exists(a.state):
        print("RESULT UNDO -- no state file %s, nothing to undo" % a.state)
        return 1
    st = json.load(open(a.state))
    if "master" in st:
        _, lines, header = read_master(a.staff_master)
        hits, iact = master_hits(lines, header)
        if len(hits) == 1 and hits[0][3] == "N":
            lines[hits[0][0]] = edit_line(lines[hits[0][0]], hits[0][1], iact, "Y")
            with open(a.staff_master, "wb") as fh:
                fh.write("".join(lines).encode("utf-8"))
        print("  undone: staff master Pravesh active Y")
    if "register" in st:
        con = sqlite3.connect(a.register_db, timeout=30)
        with con:
            con.execute("UPDATE staff SET last_working=NULL, active=1 WHERE staff_id=?", (st["register"]["staff_id"],))
            con.execute("DELETE FROM audit_log WHERE action='exit_s298'")
        con.close()
        print("  undone: register Pravesh active")
    if "joiner" in st:
        t = st["joiner"]
        con = sqlite3.connect(a.finance_db, timeout=30)
        with con:
            if t["code_row"]:
                con.execute("UPDATE emp_code SET retired_on=? WHERE code=?", (t["retired_on"], UID))
            else:
                con.execute("DELETE FROM emp_code WHERE code=?", (UID,))
            con.execute("DELETE FROM joiner_step WHERE joiner_id=? AND step='STAFF_MASTER' AND done_by=?", (t["id"], BY))
            con.execute("DELETE FROM joiner_event WHERE joiner_id=? AND actor=?", (t["id"], BY))
            con.execute("UPDATE joiner SET status=?, emp_code=?, closed_on=NULL, closed_by=NULL, updated_at=? WHERE id=?",
                        (t["status"], t["emp_code"], t["updated_at"], t["id"]))
        con.close()
        print("  undone: exit register back to %s" % t["status"])
    os.remove(a.state)
    print("RESULT UNDONE")
    return 0


def run(a):
    todo, done, bad, ev = plan(a)
    for e in ev:
        print("  evidence  %s" % e)
    for d in done:
        print("  already   %s" % d)
    for b in bad:
        print("  REFUSED   %s" % b)
    if bad:
        print("RESULT REFUSED -- nothing written")
        return 1
    if not todo:
        print("RESULT ALREADY -- nothing to do")
        return 0
    if a.dry:
        print("RESULT DRY -- would change: %s" % ", ".join(sorted(todo)))
        return 0
    apply(a, todo, a.stamp or now_ist().strftime("%Y%m%d_%H%M%S"))
    todo2, done2, bad2, _ = plan(a)
    if todo2 or bad2 or len(done2) != 3:
        print("RESULT FAIL -- read-back does not show all three changed")
        return 1
    print("RESULT OK -- 3 changed, read back")
    return 0


SCHEMA_FALLBACK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "joiner_schema.sql")


def selftest(schema=None):
    n = [0]

    def check(name, got, want):
        n[0] += 1
        if got != want:
            print("FAIL %d %s: got %r want %r" % (n[0], name, got, want))
            sys.exit(1)
    tmp = tempfile.mkdtemp(prefix="s298_")
    a = argparse.Namespace(finance_db=os.path.join(tmp, "f.db"), register_db=os.path.join(tmp, "r.db"),
                           staff_master=os.path.join(tmp, "staff_master.csv"), punches=os.path.join(tmp, "p.csv"),
                           state=os.path.join(tmp, "state.json"), dry=False, stamp="T")
    master = ("user_id,name,department,base_salary,allowed_offs,wd_start,wd_end,sun_start,sun_end,active,"
              "timing_note,sunday_group,minutes_exempt\r\n"
              "16,Vikki,Clinic,1,2,09:00,17:00,,,Y,,C,N\r\n"
              "17,Pravesh,Pathology,1,2,08:00,16:00,,,Y,\"08:00-12:00 + 17:00-21:00\",A,N\r\n"
              "18,Shavez,Clinic,1,2,09:00,17:00,,,Y,,B,N\r\n")
    open(a.staff_master, "wb").write(master.encode())
    open(a.punches, "w").write("user_id,datetime\n17,2026-08-30 08:01:00\n17,2026-08-31 08:02:00\n16,2026-09-02 09:00:00\n")
    f = sqlite3.connect(a.finance_db)
    f.executescript(open(schema or SCHEMA_FALLBACK).read())
    f.execute("INSERT INTO joiner (id,ref,kind,person,status,opened_on,opened_by,created_at,updated_at) "
              "VALUES (2,?,'EXIT','parvesh','ITEMS_RETURNED','2026-09-16','dr manoj','x','x')", (REF,))
    for s in PRIOR_STEPS:
        f.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) VALUES (2,?,'2026-09-16','dr manoj')", (s,))
    f.execute("INSERT INTO emp_code (code,person,source) VALUES (17,'Pravesh','seed')")
    f.commit()
    f.close()
    r = sqlite3.connect(a.register_db)
    r.executescript("CREATE TABLE staff (staff_id INTEGER PRIMARY KEY, name TEXT, join_date TEXT, last_working TEXT, active INTEGER);"
                    "CREATE TABLE locked_run (ym TEXT PRIMARY KEY, status TEXT);"
                    "CREATE TABLE audit_log (id INTEGER PRIMARY KEY, entity TEXT, entity_ref TEXT, action TEXT, old_value TEXT,"
                    " new_value TEXT, actor TEXT, ts TEXT, note TEXT);"
                    "INSERT INTO staff VALUES (9,'Pravesh','2026-01-01',NULL,1),(10,'Vikki','2026-01-01',NULL,1);"
                    "INSERT INTO locked_run VALUES ('2026-08','unlocked');")
    r.commit()
    r.close()
    q = lambda db, sql: sqlite3.connect(db).execute(sql).fetchall()
    check("August not locked refuses everything", (run(a), open(a.staff_master, "rb").read() == master.encode(),
          q(a.register_db, "SELECT active FROM staff WHERE staff_id=9")), (1, True, [(1,)]))
    sqlite3.connect(a.register_db).execute("UPDATE locked_run SET status='locked'").connection.commit()
    a.dry = True
    check("dry writes nothing", (run(a), open(a.staff_master, "rb").read() == master.encode()), (0, True))
    a.dry = False
    f = sqlite3.connect(a.finance_db)
    f.execute("DELETE FROM joiner_step WHERE step='ITEMS_RETURNED'")
    f.commit()
    check("an unticked earlier step refuses", run(a), 1)
    f.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by) VALUES (2,'ITEMS_RETURNED','2026-09-16','dr manoj')")
    f.commit()
    f.close()
    check("the real run", run(a), 0)
    after = open(a.staff_master, "rb").read().decode()
    want = master.replace("16:00,,,Y,\"08:00-12:00", "16:00,,,N,08:00-12:00").replace("17:00-21:00\",A", "17:00-21:00,A")
    lines_b, lines_a = master.splitlines(True), after.splitlines(True)
    check("only Pravesh's line changed, CRLF kept", (lines_a[0], lines_a[1], lines_a[3], lines_a[2].endswith("\r\n"),
          next(csv.reader([lines_a[2]]))[9], next(csv.reader([lines_a[2]]))[10]),
          (lines_b[0], lines_b[1], lines_b[3], True, "N", "08:00-12:00 + 17:00-21:00"))
    check("register: last working 31-Aug, inactive, audited",
          (q(a.register_db, "SELECT last_working, active FROM staff WHERE staff_id=9"),
           q(a.register_db, "SELECT active FROM staff WHERE staff_id=10"),
           len(q(a.register_db, "SELECT 1 FROM audit_log WHERE action='exit_s298'"))), ([(LAST, 0)], [(1,)], 1))
    check("exit register complete, code retired never deleted",
          (q(a.finance_db, "SELECT status, emp_code, closed_by FROM joiner WHERE id=2"),
           q(a.finance_db, "SELECT person, retired_on FROM emp_code WHERE code=17"),
           q(a.finance_db, "SELECT done_by FROM joiner_step WHERE step='STAFF_MASTER'")),
          ([("COMPLETE", "17", BY)], [("Pravesh", LAST)], [(BY,)]))
    check("three backups taken", all(os.path.exists(p + ".bak_S298_T") for p in (a.staff_master, a.register_db, a.finance_db)), True)
    check("backups hold the old state", (open(a.staff_master + ".bak_S298_T", "rb").read() == master.encode(),
          q(a.register_db + ".bak_S298_T", "SELECT active FROM staff WHERE staff_id=9")), (True, [(1,)]))
    a.stamp = "U"
    check("second run ALREADY, nothing new", (run(a), os.path.exists(a.finance_db + ".bak_S298_U")), (0, False))
    check("undo restores all three", (undo(a), open(a.staff_master, "rb").read() == master.encode(),
          q(a.register_db, "SELECT last_working, active FROM staff WHERE staff_id=9"),
          q(a.finance_db, "SELECT status, emp_code FROM joiner WHERE id=2"),
          q(a.finance_db, "SELECT retired_on FROM emp_code WHERE code=17"),
          q(a.finance_db, "SELECT count(*) FROM joiner_step WHERE step='STAFF_MASTER'")),
          (0, False, [(None, 1)], [("ITEMS_RETURNED", None)], [(None,)], [(0,)]))
    sqlite3.connect(a.register_db).execute("INSERT INTO staff VALUES (11,'Pravesh Kumar','2026-01-01',NULL,1)").connection.commit()
    check("two register rows named Pravesh refuses", run(a), 1)
    shutil.rmtree(tmp)
    print("SELFTEST OK -- %d checks (lock gate, dry, step gate, csv line-exact, register, exit register, backups, "
          "idempotent, undo, ambiguity)" % n[0])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance-db", default="/root/finance/finance.db")
    ap.add_argument("--register-db", default="/root/staff_register/staff_register.db")
    ap.add_argument("--staff-master", default="/root/staff_master.csv")
    ap.add_argument("--punches", default="/root/punches.csv")
    ap.add_argument("--state", default="/root/finance/exit_s298_state.json")
    ap.add_argument("--schema", default=None)
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--undo", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.schema)
    if a.undo:
        return undo(a)
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
