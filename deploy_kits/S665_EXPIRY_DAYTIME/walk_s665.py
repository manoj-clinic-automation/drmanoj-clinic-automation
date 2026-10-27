"""walk_s665.py -- kit S665_EXPIRY_DAYTIME (Sanjeevni session S359, 27-Oct-2026). Writes nothing outside --scratch.
  python walk_s665.py --new <root holding finance/spine/near_expiry.py as built> --lib <root of the unchanged modules> --db <COPY of finance.db>
                      --scratch <dir> [--spine <COPY of spine.db>]      (--old <live root>: the control)
A, B: on the walk's own two small spines and its own runs (F-998). C (only with --spine, i.e. on the box): the whole watch made through the
new line on the copies -- the live shape -- and its run reaches the spine's newest sale day."""
import argparse, os, shutil, sqlite3, sys, io, contextlib, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
for x in ("--new", "--old", "--lib", "--db", "--scratch", "--spine"):
    ap.add_argument(x)
a = ap.parse_args()
a.db = os.path.abspath(a.db); a.spine = os.path.abspath(a.spine) if a.spine else None
ROOT = os.path.abspath(a.old or a.new)
LIB = os.path.abspath(a.lib or a.old or a.new)
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
FIN = os.path.join(a.scratch, "overlay", "finance"); SP = os.path.join(FIN, "spine"); os.makedirs(SP)
for e in os.listdir(os.path.join(LIB, "finance")):
    if e not in ("spine", "finance.db"):
        os.symlink(os.path.join(LIB, "finance", e), os.path.join(FIN, e))
for e in os.listdir(os.path.join(LIB, "finance", "spine")):          # the spine's own modules (marg_read, the opener) beside the file under test
    if e != "near_expiry.py" and e.endswith(".py"):
        os.symlink(os.path.join(LIB, "finance", "spine", e), os.path.join(SP, e))
shutil.copyfile(os.path.join(ROOT, "finance", "spine", "near_expiry.py"), os.path.join(SP, "near_expiry.py"))
sys.path[:0] = [SP, FIN]
os.chdir(a.scratch)
res = []


def check(name, ok, s665=True, note=""):
    res.append((name, bool(ok), s665, str(note)[:300]))


import expiry_watch, near_expiry                                  # noqa: E402
assert os.path.dirname(os.path.abspath(near_expiry.__file__)) == SP
DB = os.path.join(a.scratch, "walk.db"); shutil.copyfile(a.db, DB)


def spine(name, last_day):
    p = os.path.join(a.scratch, name)
    c = sqlite3.connect(p); c.execute("CREATE TABLE sp_sale_line (date TEXT)"); c.execute("INSERT INTO sp_sale_line VALUES ('2026-10-01'), (?)", (last_day,)); c.commit(); c.close()
    return p


def runs(sales_to):
    c = sqlite3.connect(DB); expiry_watch.ensure(c)
    c.execute("INSERT INTO stock_expiry_run (at, today, ok, kit, sales_to, counts, note) VALUES ('2099-01-01T23:57:01','2099-01-01',1,'walk',?, '{}','walk S665')", (sales_to,))
    c.commit(); c.close()


runs("2026-10-25")
ahead, same = spine("ahead.db", "2026-10-26"), spine("same.db", "2026-10-25")
called = []
real_main = expiry_watch.main
expiry_watch.main = lambda argv=None: called.append(list(argv or [])) or 0
f = getattr(near_expiry, "newer", None)
g1 = f(DB, ahead) if f else (None, "")
g2 = f(DB, same) if f else (None, "")
check("A1 the spine holds a sale day newer than the newest run: make the watch now", g1[0] is True and "2026-10-26" in g1[1] and "2026-10-25" in g1[1], note=g1)
check("A2 the spine holds nothing newer: do nothing", g2[0] is False, note=g2)
out = io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        r1 = near_expiry.main(["--if-newer", "--db", DB, "--spine", ahead])
    ok1 = r1 == 0 and called == [["run", "--db", DB, "--spine", ahead]]
except SystemExit as ex:
    ok1 = False; called.append("SystemExit %s" % ex)
check("A3 --if-newer with newer sales: the watch is made, with the same --db/--spine (and the flag not passed on)", ok1, note=called)
called[:] = []
out2 = io.StringIO()
try:
    with contextlib.redirect_stdout(out2):
        r2 = near_expiry.main(["--if-newer", "--db", DB, "--spine", same])
    ok2 = r2 == 0 and called == [] and out2.getvalue() == ""
except SystemExit as ex:
    ok2 = False
check("A4 --if-newer with nothing newer: nothing made and nothing printed (the line runs every ten minutes)", ok2, note=(called, out2.getvalue()[:80]))
called[:] = []
near_expiry.main(["--db", DB, "--spine", same])
check("B1 the 23:57 line (no flag) makes the watch exactly as before", called == [["run", "--db", DB, "--spine", same]], s665=False, note=called)
missing = os.path.join(a.scratch, "no_such_spine.db")
g3 = f(DB, missing) if f else (None, "")
check("B2 a spine that cannot be read: no run, a reason (never a crash)", g3[0] is False and "not read" in g3[1], note=g3)
expiry_watch.main = real_main

if a.spine:                                                         # ---- C: the live shape (the box)
    SPC = os.path.join(a.scratch, "spine_copy.db")
    _s = sqlite3.connect("file:%s?mode=ro" % a.spine, uri=True); _d = sqlite3.connect(SPC); _s.backup(_d); _d.close(); _s.close()
    c = sqlite3.connect(DB); c.execute("DELETE FROM stock_expiry_run WHERE note='walk S665'"); c.commit(); c.close()
    s = sqlite3.connect(SPC).execute("SELECT MAX(date) FROM sp_sale_line").fetchone()[0]
    c = sqlite3.connect(DB); c.execute("UPDATE stock_expiry_run SET sales_to='2000-01-01' WHERE id=(SELECT MAX(id) FROM stock_expiry_run)"); c.commit(); c.close()
    n0 = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM stock_expiry_run").fetchone()[0]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = near_expiry.main(["--if-newer", "--db", DB, "--spine", SPC])
    except (SystemExit, Exception) as ex:                         # noqa: BLE001
        rc = "%s %s" % (type(ex).__name__, str(ex)[:120])
    r = sqlite3.connect(DB).execute("SELECT ok, sales_to, export_name FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
    n1 = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM stock_expiry_run").fetchone()[0]
    check("C1 on copies of the live database and spine: the line makes one whole run, good, reaching the spine's newest sale day",
          rc == 0 and n1 == n0 + 1 and r and r[0] == 1 and r[1] == s and r[2], note=(rc, n0, n1, r, s))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            near_expiry.main(["--if-newer", "--db", DB, "--spine", SPC])
    except (SystemExit, Exception):                                 # noqa: BLE001
        pass
    n2 = sqlite3.connect(DB).execute("SELECT COUNT(*) FROM stock_expiry_run").fetchone()[0]
    check("C2 ... and the next tick, nothing newer, makes none", n2 == n1, note=(n1, n2))

for n, ok, s, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", n, "" if ok else "   -- " + note))
g = sum(1 for _n, ok, _s, _x in res if ok)
if a.old:
    r6 = sum(1 for _n, ok, s, _x in res if s and not ok); ro = sum(1 for _n, ok, s, _x in res if not s and not ok)
    print("%d S665 check(s) red · %d older red · %d green" % (r6, ro, g))
else:
    print("%d of %d green" % (g, len(res)))
