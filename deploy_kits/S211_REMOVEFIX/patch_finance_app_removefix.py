#!/usr/bin/env python3
"""
patch_finance_app_removefix.py -- S211: Remove could never have worked.

THE FAULT (owner-reported twice, 30-Aug-2026, then measured)
  S210_MARGTIDY shipped POST /finance/api/marg-push/dismiss, which does

      UPDATE marg_push_staging SET status='dismissed' ...

  but the table forbids that value. Its DDL, in _marg_staging(), reads

      status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','applied','rejected','superseded'))

  so every Remove raised sqlite3.IntegrityError and Flask answered a 500 HTML
  page. The button was broken from the hour it was written. Nobody saw it
  because the page turned every 500 into the word "network" (fixed in
  S211_HONESTERRORS) and because MARGTIDY's selftest checked the PATCH -- that
  it applied, compiled and was idempotent -- and never once called the route
  against a database. Five green checks over a route that could not run.

  The same DDL is `CREATE TABLE IF NOT EXISTS`, so the constraint on the live
  table is whatever it was the day it was created; editing the DDL would have
  changed nothing at all.

THE FIX -- no migration of a live money database
  'rejected' is already this schema's word for a push ruled out, and
  _marg_push_reject() already uses it for exactly that meaning. A removed
  report becomes 'rejected'. The row is kept, the audit entry is kept, the
  replay payload is still cleared, and the page renders a red badge with NO
  Apply button -- so it can never be loaded into the books.

  It stays VISIBLE rather than vanishing. MARGTIDY's hide-filter tested for
  'dismissed', a value the schema forbids, so it never hid anything and the
  list has always shown every row; this patch makes that honest instead of
  quietly changing what the owner sees. Hiding removed reports is a separate
  decision and is left to him.

SAFETY: exact-anchor replaces -- refuses if an anchor is absent or ambiguous;
timestamped backup; py_compile with automatic restore on failure.

USAGE
    /root/wa/venv/bin/python3 patch_finance_app_removefix.py /root/finance/finance_app.py
    python3 patch_finance_app_removefix.py --selftest <a post-MARGTIDY finance_app.py>
"""
import datetime, os, py_compile, shutil, sqlite3, sys

MARK = "S211 (remove fix)"

A1 = """    con.execute("UPDATE marg_push_staging SET status='dismissed', "
                "parsed_json=NULL, apply_result_json=? WHERE id=?","""
N1 = """    # %s -- 'dismissed' is not a value this table allows: the CHECK on
    # marg_push_staging.status admits only pending / applied / rejected /
    # superseded, so this UPDATE raised IntegrityError and the owner got a 500.
    # 'rejected' is the word this schema already uses for a push ruled out
    # (see _marg_push_reject), so the fix needs no migration.
    con.execute("UPDATE marg_push_staging SET status='rejected', "
                "parsed_json=NULL, apply_result_json=? WHERE id=?",""" % MARK

A2 = '''    return jsonify(ok=True, id=pid, status="dismissed")'''
N2 = '''    return jsonify(ok=True, id=pid, status="rejected")'''

A3 = '''"FROM marg_push_staging WHERE status != 'dismissed' "
                         "ORDER BY id DESC LIMIT 20"):'''
N3 = '''"FROM marg_push_staging "
                         # %s: the filter here tested for 'dismissed', a value
                         # the schema forbids, so it never hid a single row. A
                         # removed report is now 'rejected' -- visible, and
                         # with no Apply button, unusable.
                         "ORDER BY id DESC LIMIT 20"):''' % MARK

DDL = ("CREATE TABLE marg_push_staging ("
       " id INTEGER PRIMARY KEY AUTOINCREMENT,"
       " unit TEXT NOT NULL DEFAULT 'medical',"
       " received_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),"
       " file_md5 TEXT NOT NULL,"
       " filename_hint TEXT,"
       " status TEXT NOT NULL DEFAULT 'pending'"
       "   CHECK (status IN ('pending','applied','rejected','superseded')),"
       " survey_json TEXT,"
       " parsed_json TEXT,"
       " applied_at TEXT, applied_by TEXT, apply_result_json TEXT)")


def patch_text(s):
    if MARK in s:
        return s, "already_patched"
    for a in (A1, A2, A3):
        n = s.count(a)
        if n != 1:
            return s, ("anchor_missing" if n == 0 else "anchor_ambiguous")
    return s.replace(A1, N1).replace(A2, N2).replace(A3, N3), "patched"


def selftest():
    ok = bad = 0
    def check(name, cond):
        nonlocal ok, bad
        if cond: ok += 1
        else: bad += 1
        print(("  ok   " if cond else "  FAIL ") + name)

    # ---- the DEFECT, reproduced against the real schema -------------------
    con = sqlite3.connect(":memory:")
    con.execute(DDL)
    con.execute("INSERT INTO marg_push_staging (file_md5, filename_hint) "
                "VALUES ('abc123', 'REPORT_1.XLS')")
    con.commit()
    try:
        con.execute("UPDATE marg_push_staging SET status='dismissed' WHERE id=1")
        check("the OLD value is refused by the table", False)
    except sqlite3.IntegrityError as ex:
        check("the OLD value is refused by the table (%s)" % str(ex)[:38], True)
        con.rollback()
    check("  ...and the row is untouched, exactly as the owner found it",
          con.execute("SELECT status FROM marg_push_staging WHERE id=1"
                      ).fetchone()[0] == "pending")
    # ---- the FIX, against the same schema ---------------------------------
    con.execute("UPDATE marg_push_staging SET status='rejected', "
                "parsed_json=NULL, apply_result_json='{}' WHERE id=1")
    con.commit()
    r = con.execute("SELECT status, parsed_json FROM marg_push_staging "
                    "WHERE id=1").fetchone()
    check("the NEW value is accepted", r[0] == "rejected")
    check("  ...and the replay payload is cleared, so it can never be applied",
          r[1] is None)
    check("  ...and the row itself is kept, for the audit",
          con.execute("SELECT COUNT(*) FROM marg_push_staging").fetchone()[0] == 1)
    con.close()

    # ---- the PATCH, against a real post-MARGTIDY finance_app.py -----------
    for path in sys.argv[2:]:
        s = open(path, encoding="utf-8").read()
        out, st = patch_text(s)
        check("%s: patches cleanly (%s)" % (os.path.basename(path), st), st == "patched")
        if st != "patched":
            continue
        check("  both mark comments landed", out.count(MARK) == 2)
        check("  result compiles", compile(out, path, "exec") is not None)
        out2, st2 = patch_text(out)
        check("  second run is a no-op", st2 == "already_patched" and out2 == out)
        check("  no 'dismissed' status value survives anywhere",
              "status='dismissed'" not in out and 'status="dismissed"' not in out)
        check("  the rejected UPDATE is present once",
              out.count("SET status='rejected', ") == 1)
        check("  the dead hide-filter is gone", "!= 'dismissed'" not in out)
        check("  the route still clears the replay payload",
              out.count("parsed_json=NULL, apply_result_json=? WHERE id=?") == 1)
    _, st3 = patch_text("def f():\n    pass\n")
    check("no anchors -> refused", st3 == "anchor_missing")
    print("\nselftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print(__doc__); return 2
    p = argv[1]
    if not os.path.isfile(p):
        print("!! not found:", p); return 2
    s = open(p, encoding="utf-8").read()
    new, st = patch_text(s)
    if st == "already_patched":
        print("already patched -- nothing to do."); return 0
    if st != "patched":
        print("!! REFUSED:", st, "-- nothing was written."); return 1
    bak = "%s.bak_S211_removefix_%s" % (p, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8", newline="").write(new)
    try:
        py_compile.compile(p, doraise=True)
    except py_compile.PyCompileError as ex:
        shutil.copy2(bak, p)
        print("!! compile failed -- RESTORED from", bak, "\n", ex); return 1
    print("patched OK\nbackup:", bak)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
