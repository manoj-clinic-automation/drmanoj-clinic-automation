#!/usr/bin/env python3
"""set_usernames_s296.py -- S296 (17-Sep-2026). Ties a portal login to its staff row when the two are
spelled differently, so 'Meri attendance' (/register/me) opens for that login.

WHY. The S295 attendance map found two logins that open nothing: sandeep (staff row 'Sandip') and
vikky (staff row 'Vikki'). staff_register.py maps a login by staff.username first, else by an
unambiguous first name -- these two differ in spelling, so neither rule finds them.

WHAT IT WRITES. staff.username on exactly one staff row per pair, and only when every guard holds:
  the login exists, is active, and is a staff or manager login;
  exactly one ACTIVE staff row has that first name;
  that row's username is empty (or already this login -> nothing to do);
  no other active staff row already carries this login.
A refused pair writes nothing for ANY pair. Before the write the database is copied with sqlite's
backup API to <db>.bak_S296_<stamp>. Names only on screen -- never a number (F-31).

Usage: set_usernames_s296.py USERS_JSON REGISTER_DB login=firstname [...] [--dry] [--no-backup] [--undo]
       set_usernames_s296.py --selftest
Exit: 0 written (or all already set) · 1 refused / error
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time


def first(name):
    p = (name or "").strip().lower().split()
    return p[0] if p else ""


def plan(users, con, pairs):
    """Return (actions, already, refusals). actions = [(login, staff_id, name)]."""
    staff = list(con.execute("SELECT staff_id, name, COALESCE(username,'') AS un FROM staff WHERE active=1"))
    acts, done, bad = [], [], []
    for login, fname in pairs:
        u = users.get(login)
        if not u or not u.get("active", False) or u.get("role") not in ("staff", "manager"):
            bad.append("%s: not an active staff/manager login" % login)
            continue
        hits = [s for s in staff if first(s["name"]) == fname]
        if len(hits) != 1:
            bad.append("%s: %d active staff rows with first name '%s' (need exactly 1)" % (login, len(hits), fname))
            continue
        row = hits[0]
        owners = [s for s in staff if s["un"].strip().lower() == login and s["staff_id"] != row["staff_id"]]
        if owners:
            bad.append("%s: already the username of %s" % (login, owners[0]["name"]))
            continue
        if row["un"].strip().lower() == login:
            done.append("%s -> %s" % (login, row["name"]))
            continue
        if row["un"].strip():
            bad.append("%s: %s already has username '%s'" % (login, row["name"], row["un"]))
            continue
        acts.append((login, row["staff_id"], row["name"]))
    return acts, done, bad


def undo(db_path, pairs):
    """Restore path: clear exactly the usernames this kit sets, and nothing else."""
    con = sqlite3.connect(db_path, timeout=30)
    try:
        with con:
            n = sum(con.execute("UPDATE staff SET username='' WHERE LOWER(COALESCE(username,''))=?", (l,)).rowcount
                    for l, _ in pairs)
        print("RESULT UNDONE -- %d username(s) cleared" % n)
        return 0
    finally:
        con.close()


def run(users_path, db_path, pairs, dry=False, backup=True, stamp=None):
    users = json.load(open(users_path, encoding="utf-8")).get("users", {})
    users = {k.strip().lower(): v for k, v in users.items()}
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        acts, done, bad = plan(users, con, pairs)
        for d in done:
            print("  already  %s" % d)
        for b in bad:
            print("  REFUSED  %s" % b)
        if bad:
            print("RESULT REFUSED -- nothing written")
            return 1
        for login, sid, name in acts:
            print("  %s  %s -> %s" % ("would set" if dry else "set", login, name))
        if dry or not acts:
            print("RESULT %s -- %d to set, %d already" % ("DRY" if dry else "ALREADY", len(acts), len(done)))
            return 0
        if backup:
            bak = "%s.bak_S296_%s" % (db_path, stamp or time.strftime("%Y%m%d_%H%M%S"))
            dst = sqlite3.connect(bak)
            con.backup(dst)
            dst.close()
            print("  backup   %s" % bak)
        with con:
            for login, sid, name in acts:
                con.execute("UPDATE staff SET username=? WHERE staff_id=? AND active=1 AND COALESCE(username,'')=''",
                            (login, sid))
        acts2, done2, bad2 = plan(users, con, pairs)
        if acts2 or bad2 or len(done2) != len(pairs):
            print("RESULT FAIL -- read-back does not show every pair set")
            return 1
        print("RESULT OK -- %d set, read back" % len(acts))
        return 0
    finally:
        con.close()


def selftest():
    n = [0]

    def check(name, got, want):
        n[0] += 1
        if got != want:
            print("FAIL %d %s: got %r want %r" % (n[0], name, got, want))
            sys.exit(1)
    tmp = tempfile.mkdtemp(prefix="s296_")
    db, uj = os.path.join(tmp, "r.db"), os.path.join(tmp, "u.json")
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE staff (staff_id INTEGER PRIMARY KEY, name TEXT, active INTEGER, username TEXT)")
    con.executemany("INSERT INTO staff VALUES (?,?,?,?)", [
        (1, "Sandip", 1, None), (2, "Vikki", 1, ""), (3, "Shavez", 1, "shavez"),
        (4, "Ravi A", 1, None), (5, "Ravi B", 1, None), (6, "Old", 0, None), (7, "Neha", 1, "neha2")])
    con.commit()
    con.close()
    json.dump({"users": {"sandeep": {"active": True, "role": "staff"}, "Vikky": {"active": True, "role": "manager"},
                         "ravi": {"active": True, "role": "staff"}, "doc": {"active": True, "role": "doctor"},
                         "gone": {"active": False, "role": "staff"}, "shavez": {"active": True, "role": "manager"},
                         "neha": {"active": True, "role": "staff"}, "oldie": {"active": True, "role": "staff"}}},
              open(uj, "w"))
    un = lambda: dict(sqlite3.connect(db).execute("SELECT staff_id, COALESCE(username,'') FROM staff").fetchall())
    P = [("sandeep", "sandip"), ("vikky", "vikki")]
    check("dry writes nothing", (run(uj, db, P, dry=True), un()[1], un()[2]), (0, "", ""))
    check("one bad pair refuses all", (run(uj, db, P + [("ravi", "ravi")]), un()[1]), (1, ""))
    check("doctor login refused", run(uj, db, [("doc", "sandip")], dry=True), 1)
    check("inactive login refused", run(uj, db, [("gone", "sandip")], dry=True), 1)
    check("inactive staff row not a target", run(uj, db, [("oldie", "old")], dry=True), 1)
    check("row with another username refused", run(uj, db, [("neha", "neha")], dry=True), 1)
    check("login owned by another row refused", run(uj, db, [("shavez", "sandip")], dry=True), 1)
    check("the real write", (run(uj, db, P, stamp="T"), un()[1], un()[2], un()[3]), (0, "sandeep", "vikky", "shavez"))
    check("backup taken before the write", os.path.exists(db + ".bak_S296_T")
          and dict(sqlite3.connect(db + ".bak_S296_T").execute("SELECT staff_id, COALESCE(username,'') FROM staff"))[1], "")
    check("second run is ALREADY, no new backup", (run(uj, db, P, stamp="U"), os.path.exists(db + ".bak_S296_U")), (0, False))
    undo(db, P)
    check("undo clears only this kit's usernames", (un()[1], un()[2], un()[3], un()[7]), ("", "", "shavez", "neha2"))
    shutil.rmtree(tmp)
    print("SELFTEST OK -- %d checks (dry, all-or-nothing, role/active/row guards, write, backup, idempotent, undo)" % n[0])
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    flags = {a for a in argv if a.startswith("--")}
    rest = [a for a in argv if not a.startswith("--")]
    if len(rest) < 3:
        print(__doc__)
        return 1
    pairs = []
    for p in rest[2:]:
        l, _, f = p.partition("=")
        pairs.append((l.strip().lower(), f.strip().lower()))
    if "--undo" in flags:
        return undo(rest[1], pairs)
    return run(rest[0], rest[1], pairs, dry="--dry" in flags, backup="--no-backup" not in flags)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
