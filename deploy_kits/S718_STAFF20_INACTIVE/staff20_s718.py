#!/usr/bin/env python3
"""staff20_s718.py -- kit S718 (session 390, the parent, 06-Nov-2026). F-1131, F-1132.

THE OWNER, 14:10 IST 06-Nov: staff 20 inactive from October -- "ok, paid and all his dues cleared".
Staff 20 is 'Arjun', who LEFT on 30-Sep (D824, 02-Nov). Kit S712 (06-Nov 08:43) wrongly moved HIS base pay to 3,500,
meaning the new cleaner Arjun Dev (a different person, D835). This puts staff 20 right:

  1  /root/staff_master.csv   the ONE line with user_id 20 and name Arjun: base_salary 3500 -> 3200 (as it was when he
                              left) and active Y -> N. Every other byte of the file is proved identical. Backup first,
                              atomic replace, read back.
  2  staff_register.db, staff the active row named exactly 'Arjun' IF there is one: last_working 2026-09-30, active 0 --
                              what the register's own profile page does for a leaver (as kit S298 did for Pravesh). One
                              audit_log row. No row: nothing (the S712 read found him only on staff_master.csv).
GUARD THAT PROTECTS MONEY: an inactive row is dropped from every month the attendance report computes, so September
and October must both be LOCKED in the register (locked_run status 'locked'); their pay is then frozen in the locked
runs. Either not locked -> nothing written. November has not been computed.

  python staff20_s718.py --master /root/staff_master.csv --dir /root/staff_register [--dry]
rc 0 = changed, or already so (nothing written) . rc 2 = STOPPED, nothing written."""
import argparse, datetime as dt, io, os, shutil, sqlite3, sys, time

UID, NAME = "20", "Arjun"
FROM_BASE, TO_BASE = "3500", "3200"
LAST = "2026-09-30"
LOCKED_MONTHS = ("2026-09", "2026-10")
BY = "Claude (kit S718)"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def stop(why):
    print("STOPPED: %s. Nothing was written." % why)
    sys.exit(2)


def db_path(d):
    """The register's own DB path rule (staff_register._cfg): environment, then staff_register_config.py, then the default."""
    v = os.environ.get("SR_DB_PATH")
    if v:
        return v
    sys.path.insert(0, d)
    try:
        import staff_register_config as C            # noqa
        v = getattr(C, "SR_DB_PATH", None)
        if v:
            return v
    except Exception:                                # noqa: BLE001
        pass
    finally:
        sys.path.pop(0)
    return os.path.join(d, "staff_register.db")


def plan_master(path):
    if not os.path.isfile(path):
        stop("%s is not there" % path)
    raw = io.open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        stop("the staff list is not UTF-8")
    bom = text.startswith("﻿")
    body = text[1:] if bom else text
    nl = "\r\n" if "\r\n" in body else "\n"
    lines = body.split(nl)
    head = lines[0].split(",")
    for col in ("user_id", "name", "base_salary", "active"):
        if col not in head:
            stop("the staff list's header has no %s column" % col)
    ix = {c: head.index(c) for c in head}
    hits = [i for i, ln in enumerate(lines[1:], 1) if ln.split(",")[:1] == [UID]]
    if len(hits) != 1:
        stop("number %s is on %d lines of the staff list, not 1" % (UID, len(hits)))
    i = hits[0]
    ln = lines[i]
    if '"' in ln:
        stop("his line carries quotes -- not the plain line this kit was built for")
    f = ln.split(",")
    if len(f) != len(head):
        stop("his line has %d fields, the header %d" % (len(f), len(head)))
    if f[ix["name"]].strip() != NAME:
        stop("number %s is '%s', not %s -- a name is not a person (F-1131)" % (UID, f[ix["name"]].strip(), NAME))
    base, act = f[ix["base_salary"]].strip(), f[ix["active"]].strip().upper()
    if base == TO_BASE and act == "N":
        return None, "staff list: number %s %s already base %s and inactive" % (UID, NAME, TO_BASE)
    if base not in (FROM_BASE, TO_BASE):
        stop("his base pay is %s, not %s (S712) or %s" % (base, FROM_BASE, TO_BASE))
    if act not in ("Y", "N"):
        stop("his active cell is '%s', not Y or N" % act)
    g = list(f)
    g[ix["base_salary"]] = g[ix["base_salary"]].replace(base, TO_BASE) if base != TO_BASE else g[ix["base_salary"]]
    g[ix["active"]] = g[ix["active"]].replace(f[ix["active"]].strip(), "N")
    new_lines = lines[:i] + [",".join(g)] + lines[i + 1:]
    new = (("﻿" if bom else "") + nl.join(new_lines)).encode("utf-8")
    a, b = text.split(nl), (("﻿" if bom else "") + nl.join(new_lines)).split(nl)
    if [k for k in range(max(len(a), len(b))) if (a[k] if k < len(a) else None) != (b[k] if k < len(b) else None)] != [i]:
        stop("the change would touch other lines of the staff list")
    fa, fb = a[i].split(","), b[i].split(",")
    ch = [k for k in range(len(fa)) if fa[k] != fb[k]]
    if not set(ch) <= {ix["base_salary"], ix["active"]} or not ch:
        stop("the change would touch more than his base pay and his active cell")
    return (raw, new), "staff list: number %s %s base %s -> %s, active %s -> N" % (UID, NAME, base, TO_BASE, act)


def plan_register(db):
    if not os.path.isfile(db):
        stop("the register's database is not at %s -- cannot tell whether September and October are locked" % db)
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        con.row_factory = sqlite3.Row
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='locked_run'").fetchone():
            stop("the register has no locked_run table -- cannot tell whether the months are locked")
        for ym in LOCKED_MONTHS:
            r = con.execute("SELECT status FROM locked_run WHERE ym=?", (ym,)).fetchone()
            if not (r and str(r[0]).lower() == "locked"):
                stop("%s is NOT locked in the register -- taking him off would change that month's pay. Lock it first" % ym)
        rows = [dict(r) for r in con.execute("SELECT staff_id, name, active, last_working FROM staff")
                if (r["name"] or "").strip().lower() == NAME.lower()]
        has_audit = bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='audit_log'").fetchone())
        if has_audit:
            acols = set(r[1] for r in con.execute("PRAGMA table_info(audit_log)"))
            need = {"entity", "entity_ref", "action", "old_value", "new_value", "actor", "ts", "note"}
            if not need <= acols:
                stop("the register's audit_log lacks %s -- not the table this kit was built for" % ", ".join(sorted(need - acols)))
        con.close()
    except sqlite3.Error as e:
        stop("could not read the register (%s)" % e)
    if not rows:
        return None, "register: no staff row named %s (nothing to do there)" % NAME
    if len(rows) > 1:
        stop("the register has %d rows named %s -- which one is unclear" % (len(rows), NAME))
    r = rows[0]
    if r["active"] == 0 and r["last_working"]:
        return None, "register: %s already inactive (last working %s)" % (NAME, r["last_working"])
    if r["active"] != 1 or r["last_working"]:
        stop("the register's %s row is half-changed (active %s, last working %s)" % (NAME, r["active"], r["last_working"]))
    return (r["staff_id"], has_audit), "register: %s (staff %s) last working day %s, inactive" % (NAME, r["staff_id"], LAST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    db = db_path(a.dir)
    reg, rsay = plan_register(db)               # the lock guard runs first, before anything else
    mas, msay = plan_master(a.master)
    print("  months locked: %s" % ", ".join(LOCKED_MONTHS))
    print("  " + msay)
    print("  " + rsay)
    if mas is None and reg is None:
        print("ALREADY: nothing to change.")
        return 0
    if a.dry:
        print("DRY: nothing written.")
        return 0
    stamp = time.strftime("%Y%m%d-%H%M%S")
    if mas is not None and io.open(a.master, "rb").read() != mas[0]:
        stop("the staff list changed while the kit ran")
    if reg is not None:                         # the register first: it is the one with an undoable backup API
        bak = "%s.bak_S718_%s" % (db, stamp)
        s = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        d = sqlite3.connect(bak)
        s.backup(d)
        d.close(); s.close()
        con = sqlite3.connect(db)
        try:
            n = con.execute("UPDATE staff SET last_working=?, active=0 WHERE staff_id=? AND active=1 AND last_working IS NULL",
                            (LAST, reg[0])).rowcount
            if n != 1:
                con.rollback()
                stop("the register row changed under the kit")
            if reg[1]:
                con.execute("INSERT INTO audit_log(entity,entity_ref,action,old_value,new_value,actor,ts,note) VALUES "
                            "('staff',?,'exit_s718','active=1','active=0 last_working=%s',?,?,?)" % LAST,
                            (str(reg[0]), BY, dt.datetime.now(IST).isoformat(timespec="seconds"),
                             "left 30-Sep (D824); paid, all dues cleared -- the owner 06-Nov"))
            con.commit()
        finally:
            con.close()
        print("  written: the register (backup %s)" % os.path.basename(bak))
    if mas is not None:
        raw, new = mas
        if io.open(a.master, "rb").read() != raw:
            stop("the staff list changed while the kit ran")
        bak = "%s.bak_S718_%s" % (a.master, stamp)
        shutil.copy2(a.master, bak)
        tmp = a.master + ".tmp_S718"
        with io.open(tmp, "wb") as fh:
            fh.write(new)
        st = os.stat(a.master)
        os.chmod(tmp, st.st_mode & 0o777)
        try:
            os.chown(tmp, st.st_uid, st.st_gid)
        except (AttributeError, PermissionError):
            pass
        os.replace(tmp, a.master)
        if io.open(a.master, "rb").read() != new:
            shutil.copy2(bak, a.master)
            stop("the staff list did not read back -- the old file was put back")
        print("  written: the staff list (backup %s)" % os.path.basename(bak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
