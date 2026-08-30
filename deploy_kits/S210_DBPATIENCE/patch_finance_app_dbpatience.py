#!/usr/bin/env python3
"""
patch_finance_app_dbpatience.py -- S210: 'database is locked' on Apply.

THE FAULT (journal, 30-Aug 18:35 IST, twice)
    sqlite3.OperationalError: database is locked -- at con.commit() inside
    api_marg_push_apply. Gunicorn runs multiple workers; the owner's retry
    click landed on a second worker while the first still held the write
    lock. sqlite3.connect() default patience is 5 seconds; a long apply
    (ingest of multi-day reports) exceeds it, so a concurrent writer ERRORS
    instead of WAITING. The 500 the owner saw is exactly this.

THE FIX -- one anchored change in db()
    connect(timeout=30) + PRAGMA busy_timeout=30000: any connection that
    meets a locked database now WAITS (up to 30 s) instead of throwing.
    Contention becomes a queue, not an error. No schema, no journal-mode
    change (WAL is a separate decision -- it alters what finance_backup.sh
    must copy; recorded for the owner, not smuggled in here).

SAFETY: exact anchor, refuse if absent/ambiguous; backup; py_compile with
auto-restore.

USAGE
    /root/wa/venv/bin/python3 patch_finance_app_dbpatience.py /root/finance/finance_app.py
    python3 patch_finance_app_dbpatience.py --selftest <copies...>
"""
import datetime, os, py_compile, shutil, sys

MARK = "S210 (db patience)"

A1 = """    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")"""

N1 = """    if "db" not in g:
        # %s -- a concurrent writer must WAIT, not error. 30-Aug the
        # owner's Apply died 500 on 'database is locked': two gunicorn
        # workers + the 5-second default. Patience is the cure, not retry.
        g.db = sqlite3.connect(DB_PATH, timeout=30)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 30000")""" % MARK


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    n = s.count(A1)
    if n != 1:
        return s, ("anchor_missing" if n == 0 else "anchor_ambiguous")
    return s.replace(A1, N1), "patched"


def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1; print("  FAIL:", name)
    for path in sys.argv[2:]:
        s = open(path, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s: patches" % path.split("/")[-2], st == "patched")
        check("  compiles", compile(out, path, "exec") is not None)
        check("  timeout=30 present", "connect(DB_PATH, timeout=30)" in out)
        check("  busy_timeout pragma present", "busy_timeout = 30000" in out)
        _, st2 = patch_text(out)
        check("  second run no-op", st2 == "already_patched")
    _, st3 = patch_text("x=1\n")
    check("no anchor -> refused", st3 == "anchor_missing")
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print(__doc__); return 2
    p = argv[1]
    s = open(p, encoding="utf-8").read()
    new, st = patch_text(s)
    if st == "already_patched":
        print("already patched -- nothing to do."); return 0
    if st != "patched":
        print("!! REFUSING --", st, "\n   Nothing changed."); return 1
    bak = "%s.bak_S210_dbp_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        shutil.copy2(bak, p)
        print("!! compile FAILED -- restored from", bak); print("  ", e); return 1
    print("patched OK"); print("backup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
