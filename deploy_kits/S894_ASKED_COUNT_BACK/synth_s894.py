# synth_s894.py -- S894 on a COPY of the finance database with the code laid out beside it.
#   python3 synth_s894.py --code <dir with stock_watch.py> --finance <copy of finance.db> [--control]
# Made-up asks only on real item names; nothing is written to any live file. The copy is changed: use a copy.
import argparse, datetime as dt, importlib, os, sqlite3, sys
ap = argparse.ArgumentParser(); ap.add_argument("--code", required=True); ap.add_argument("--finance", required=True)
ap.add_argument("--control", action="store_true"); a = ap.parse_args()
sys.path.insert(0, a.code); sys.path.insert(1, os.path.join(a.code, "spine"))
sw = importlib.import_module("stock_watch")
con = sqlite3.connect(a.finance); con.row_factory = None
sw.ensure(con)
R = []
def check(n, c, why=""):
    R.append((n, bool(c))); print(("ok   " if c else "RED  ") + n + ("" if c else "  " + why))

# items with a Marg closing, not asked now
items = [r[0] for r in con.execute("SELECT item FROM stock_snapshot WHERE qty>20 GROUP BY item ORDER BY item LIMIT 400")]
asked = {r[0] for r in con.execute("SELECT item_norm FROM stock_watch_ask WHERE done_at IS NULL")}
items = [i for i in items if sw.norm_name(i) not in asked][:6]
assert len(items) >= 4, "not enough items"
X, Y, Z, W = items[:4]
marg = lambda it: con.execute("SELECT qty FROM stock_snapshot WHERE item=? ORDER BY rowid DESC LIMIT 1", (it,)).fetchone()[0]
today = sw.today().isoformat(); yday = (sw.today() - dt.timedelta(days=2)).isoformat()
def notices_for(it):
    return [r[0] for r in con.execute("SELECT text FROM stock_watch_notice WHERE kind='asked_count' AND text LIKE ?", ("%" + it + "%",))]

def roster_row(day, it, carried):
    return con.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (day, sw.norm_name(it), it, "you asked for it", "Doctor sahab ne kaha", 9, sw.now_iso(), 1, "", carried)).lastrowid

# T1 -- the 18-Nov shape: the ask tied to an old roster row, answered on a carried row
ok, msg, code = sw.ask(con, X, "synth")
r_old = roster_row(yday, X, 0)
con.execute("UPDATE stock_watch_ask SET roster_id=? WHERE item_norm=? AND done_at IS NULL", (r_old, sw.norm_name(X)))
r_new = roster_row(today, X, 1); con.commit()
mx = marg(X)
try:
    res = sw.answer_roster(con, r_new, mx - 3, "synth")
    answered = res[0]
except Exception as e:
    answered = False; print("   answer_roster raised:", e)
check("T1 the count is taken", answered)
check("T1 the ask closes when answered on a carried row", not con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL", (sw.norm_name(X),)).fetchone())
n = notices_for(X)
check("T1 one Needs-you line, against Marg, 'fewer than Marg'", len(n) == 1 and "fewer than Marg" in n[0] and "(you asked)" in n[0], str(n))
ny = sw.needs_you_lines(con)
check("T1 the line is in the owner's Needs-you, as warn", any(X in l["text"] and l["cls"] == "warn" for l in ny), str([l["text"][:60] for l in ny][:6]))

# T1b -- 'Galat likha? Badlo' the same day: the owner's line follows the corrected count
try:
    rc = sw.correct_roster(con, r_new, mx - 1, "synth")
except Exception as e:
    rc = (False,); print("   T1b raised:", e)
n = notices_for(X)
check("T1b a same-day correction rewrites the owner's line", rc[0] and len(n) == 1 and "(corrected)" in n[0], str(n))

# T2 -- an item nobody asked for: no line
r2 = roster_row(today, Y, 0); con.commit()
try: sw.answer_roster(con, r2, marg(Y), "synth")
except Exception as e: print("   T2 raised:", e)
check("T2 no line for an item not asked", not notices_for(Y))

# T3 -- 'Stock batao' on an asked item, matching Marg: closes, info line
sw.ask(con, Z, "synth")
try: sw.darpan_point(con, Z, marg(Z), "synth")
except Exception as e: print("   T3 raised:", e)
nz = notices_for(Z)
check("T3 'Stock batao' on an asked item: one line, 'matches Marg'", len(nz) == 1 and "matches Marg" in nz[0], str(nz))
check("T3 ...shown as info", any(Z in l["text"] and l["cls"] == "info" for l in sw.needs_you_lines(con)))
check("T3 ...and the ask closes", not con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL", (sw.norm_name(Z),)).fetchone())

# T4 -- the same item asked and answered again the same day: still one line
sw.ask(con, X, "synth"); r4 = roster_row(today, X, 0); con.commit()
try: sw.answer_roster(con, r4, mx - 3, "synth")
except Exception as e: print("   T4 raised:", e)
check("T4 one line per item per day", len(notices_for(X)) == 1)

# T5 -- a failure while writing the line never raises (the count itself is already stored by then)
sw.ask(con, W, "synth"); con.commit()
class Boom:
    def __init__(self, c): self.c = c
    def execute(self, q, *x):
        if "FROM stock_snapshot" in q: raise sqlite3.OperationalError("boom")
        return self.c.execute(q, *x)
    def __getattr__(self, k): return getattr(self.c, k)
try:
    got = sw._s894_asked_back(Boom(con), W, 5)
    ok5 = bool(got) and "see the stock page" in got and not con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL", (sw.norm_name(W),)).fetchone()
except Exception as e:
    ok5 = False; print("   T5 raised:", e)
check("T5 Marg unreadable: no raise, a plain line still written, the ask closed", ok5)

con.rollback(); con.close()
bad = [n for n, ok in R if not ok]
print("synth_s894: %d ok, %d red" % (len(R) - len(bad), len(bad)))
sys.exit(1 if bad else 0)
