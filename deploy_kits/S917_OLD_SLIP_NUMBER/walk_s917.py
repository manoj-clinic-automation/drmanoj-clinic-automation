"""walk_s917.py FINDIR DB -- S917's walk on a COPY of the database (never the live one): the guard and the one-off together.
Prints PASS/FAIL lines and 'WALK n/m' last."""
import importlib, os, shutil, sqlite3, subprocess, sys, tempfile
FIN, DB0 = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
sys.path.insert(0, FIN)
SL = importlib.import_module("slip_log")
SL._today = lambda: "2026-11-21"
res = []
def chk(name, ok, why=""):
    res.append(ok); print(("PASS " if ok else "FAIL ") + name + ("" if ok else " -- " + str(why)[:200]))
tmp = tempfile.mkdtemp(prefix="w917_")
def copy(n):
    p = os.path.join(tmp, n); shutil.copy(DB0, p)
    c = sqlite3.connect(p); c.row_factory = sqlite3.Row; SL.ensure(c); return c, p
_c0 = sqlite3.connect(DB0)
P14 = _c0.execute("SELECT clinic_id FROM slip WHERE series='opd' AND slip_no=20076 AND day='2026-11-14'").fetchone()[0]   # the 14-Nov patient
P09 = _c0.execute("SELECT clinic_id FROM slip WHERE id=1190").fetchone()[0]                                             # the 9-Nov patient
_c0.close()
X = [{"kind": "xray", "name": "Foot AP & Oblique view", "price_p": 50000}]
def tryw(con, no, cid, day, gap=False):
    try:
        sid, note = SL.log_slip(con, "walk", "xp", no, cid, "", X, confirm_gap=gap, day=day); return ("ok", sid)
    except SL.SlipError as ex:
        return ("err", str(ex))
# A. before the one-off: 1546 is taken (the 9-Nov slip)
c, p = copy("a.db")
r = tryw(c, 1546, P14, "2026-11-14"); chk("A1 before the fix 1546 refused for the 14-Nov patient", r[0] == "err" and "1546" in r[1], r)
# B. the one-off, then the 14-Nov paper 1546
c.close()
fx = subprocess.run([sys.executable, os.path.join(HERE, "s917_fix.py"), p, "--apply"], capture_output=True, text=True)
chk("B1 the one-off applies", "APPLIED" in fx.stdout, fx.stdout + fx.stderr)
c = sqlite3.connect(p); c.row_factory = sqlite3.Row
s = c.execute("SELECT slip_no, day, clinic_id FROM slip WHERE id=1190").fetchone()
chk("B2 the 9-Nov slip is 1481", tuple(s) == (1481, "2026-11-09", P09), tuple(s))
r = tryw(c, 1546, P14, "2026-11-14"); chk("B3 the 14-Nov paper 1546 saves", r[0] == "ok", r)
if r[0] == "ok":
    d = c.execute("SELECT day, clinic_id, state FROM slip WHERE id=?", (r[1],)).fetchone()
    chk("B4 it is on 14-Nov, the right ID, ok", tuple(d) == ("2026-11-14", P14, "ok"), tuple(d))
    m = c.execute("SELECT COUNT(*) FROM slip WHERE series='xp' AND state='missing' AND day='2026-11-14'").fetchone()[0]
    chk("B5 no numbers marked missing by it", m == 0, m)
fx2 = subprocess.run([sys.executable, os.path.join(HERE, "s917_fix.py"), p, "--apply"], capture_output=True, text=True)
chk("B6 the one-off again says ALREADY DONE", "ALREADY DONE" in fx2.stdout, fx2.stdout)
# C. the guard: an old day's number past a later day's saved slip
hi = c.execute("SELECT MAX(slip_no) FROM slip WHERE series='xp' AND state='ok'").fetchone()[0]
n = hi + 1
r = tryw(c, n, P09, "2026-11-09"); chk("C1 9-Nov with a number past later days asks 'Haan, yahi number'", r[0] == "err" and "Haan, yahi number" in r[1], r)
chk("C2 nothing written by the refusal", c.execute("SELECT COUNT(*) FROM slip WHERE series='xp' AND slip_no=?", (n,)).fetchone()[0] == 0)
r = tryw(c, n, P09, "2026-11-09", gap=True); chk("C3 with 'Haan, yahi number' it saves", r[0] == "ok", r)
r = tryw(c, n + 1, P09, "2026-11-21"); chk("C4 today's slip never asked", r[0] == "ok", r)
# D. an old-day number that fits its day is not asked: a number below every later day's slip
c2, p2 = copy("d.db")
lo = c2.execute("SELECT MIN(slip_no) FROM slip WHERE series='xp' AND state='ok' AND day>'2026-11-13'").fetchone()[0]
free = next(k for k in range(lo - 1, lo - 400, -1) if c2.execute("SELECT 1 FROM slip WHERE series='xp' AND slip_no=? AND state<>'void'", (k,)).fetchone() is None)
r = tryw(c2, free, P09, "2026-11-13"); chk("D1 a 13-Nov number below 14-Nov's first is not asked", not (r[0] == "err" and "Haan, yahi number" in r[1] and "ke baad ka number" in r[1]), r)
# E. the message carries the words both pages look for to show the tick
rE = tryw(copy("e.db")[0], n, P09, "2026-11-09")
chk("E1 the ask carries 'Haan, yahi number' (the desk and the form show the tick on it)", rE[0] == "err" and "Haan, yahi number" in str(rE[1]), rE)
shutil.rmtree(tmp, ignore_errors=True)
print("WALK %d/%d" % (sum(res), len(res)))
