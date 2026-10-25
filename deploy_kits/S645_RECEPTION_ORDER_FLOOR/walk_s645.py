"""walk_s645.py -- kit S645_RECEPTION_ORDER_FLOOR (S349, the parent, 25-Oct-2026; F-1024). READ-ONLY on the books: every read of
the real database is mode=ro through aaj_kaam's own Reader; the made-up rows live only in a throwaway copy made by sqlite's
backup, removed at the end.
  python walk_s645.py <dir holding the aaj_seed.py under test> <finance dir: aaj_kaam.py, aaj_duties.json> [--db PATH] [--old]
  --old: the control -- on the LIVE aaj_seed.py every S645 check must be red and every older check green.
  (internal) --dump: every person's line states as JSON."""
import datetime as dt, json, os, sqlite3, subprocess, sys, tempfile
argv = sys.argv[1:]
DB = None
if "--db" in argv:
    k = argv.index("--db"); DB = argv[k + 1]; del argv[k:k + 2]
OLD, DUMP = "--old" in argv, "--dump" in argv
args = [a for a in argv if not a.startswith("--")]
SEEDDIR, FIN = os.path.abspath(args[0]), os.path.abspath(args[1])
DB = DB or os.path.join(FIN, "finance.db")
sys.path[:0] = [SEEDDIR, FIN]
import aaj_seed as S                                                   # noqa: E402
import aaj_kaam as A                                                   # noqa: E402
assert os.path.dirname(os.path.abspath(S.__file__)) == SEEDDIR, "aaj_seed.py did not come from the folder under test"
assert A.SEED is S, "aaj_kaam did not take the aaj_seed.py under test"
rd = A.Reader(DB)

def states():
    out = {}
    for k, doc in rd.people.items():
        for ln in doc["lines"]:
            if ln.get("on"):
                st = A.line_state(rd, ln)
                out["%s|%s" % (k, ln["id"])] = dict(kind=st["kind"], due=st["due"], err=st["err"], since=st["since"])
    return out

if DUMP:
    print(json.dumps(states(), sort_keys=True)); sys.exit(0)

res = []
def check(name, ok, s645=True, note=""):
    res.append((name, bool(ok), s645, note))

m = json.load(open(A.DUTY_MAP))
SQL = {d["id"]: d.get("due_sql") or "" for d in m["duties"]}
D3 = ("reception.order_arrival", "shavez.order_followup", "reception.bill_scan")
check("A0 the duty map (v%s) carries the three order duties" % m.get("version"), all(i in SQL for i in D3), False)
fits = {i: bool(S.REWRITE.get(i)) and SQL.get(i, "").count(S.REWRITE[i][0]) == 1 for i in D3}
check("A1 each of the three has its piece, fitting its SQL exactly once", all(fits.values()), True, str(fits))

def floored(i, con):
    rw = S.REWRITE.get(i)
    return SQL[i].replace(rw[0], rw[1].replace("{floor}", A.staff_floor(con))) if fits.get(i) else None

def n_staff(i, con):
    """exactly as aaj_kaam._item does: a duty with a REWRITE entry is floored by it or UNREAD; one without runs as the map has it"""
    if not S.REWRITE.get(i):
        return A._one(con, SQL[i])
    q = floored(i, con)
    return A._one(con, q) if q else (None, None, "piece does not fit")

# her list and Shavez's, as the server shows them
for who, i in (("reception", "reception.order_arrival"), ("shavez", "shavez.order_followup"), ("reception", "reception.bill_scan")):
    doc = rd.people.get(who) or {"lines": []}
    ln = [l for l in doc["lines"] if l["id"] == i and l.get("on")]
    if ln:
        st = A.line_state(rd, ln[0])
        check("A2 %s's line %s is READ (a job, no error)" % (who, i), st["kind"] == "job" and not st["err"], True, "err=%s" % st["err"])
lst = A.person_list(rd, rd.people["reception"])
check("A3 reception's list has no unread line -> no 'Poori list' banner", lst["unread"] == 0 and not rd.defs_err(), True, "unread=%s" % lst["unread"])
lst2 = A.person_list(rd, rd.people["shavez"])
check("A4 Shavez's list has no unread line", lst2["unread"] == 0, False, "unread=%s" % lst2["unread"])
# the real books: what the staff connection counts = what the whole books count (the floor 01-Oct is before every duty's own day)
for i in D3:
    a, b = n_staff(i, rd.con), A._one(rd.raw, SQL[i])
    check("A5 the real books, %s: her/his list counts what the whole books count (%s = %s)" % (i, a[0], b[0]),
          not a[2] and not b[2] and a[0] == b[0], True, a[2] or "")
# every other line of every person reads as it did under the live seed
me = states()
other = os.path.join(FIN, "aaj_seed.py") if not OLD else os.path.join(SEEDDIR, "aaj_seed.py")
tmp = tempfile.mkdtemp(prefix="s645other")
open(os.path.join(tmp, "aaj_seed.py"), "wb").write(open(other, "rb").read())
dump = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), tmp, FIN, "--db", DB, "--dump"], capture_output=True, text=True)
os.remove(os.path.join(tmp, "aaj_seed.py")); os.rmdir(tmp)
try:
    them = json.loads(dump.stdout)
    diff = [k for k in set(me) | set(them) if k.split("|")[1] not in D3 and me.get(k) != them.get(k)]
    check("A6 every other line of every person reads as before (%d lines)" % sum(1 for k in me if k.split("|")[1] not in D3), not diff, False, ", ".join(sorted(diff))[:300])
except Exception:
    check("A6 every other line of every person reads as before", False, False, "dump failed: %s" % dump.stderr[-300:])
check("A7 amir.bills_answer's own floor still fits", SQL.get("amir.bills_answer", "").count(S.REWRITE["amir.bills_answer"][0]) == 1, False)

# THE WALK'S OWN ROWS (F-998), on a throwaway copy: every real order, line, tie and carry removed from the COPY
td = tempfile.mkdtemp(prefix="s645walk"); cp = os.path.join(td, "copy.db")
try:
    src = sqlite3.connect("file:%s?mode=ro" % DB, uri=True); dst = sqlite3.connect(cp); src.backup(dst); src.close()
    t = dt.date.today(); dX, dY = (t - dt.timedelta(days=10)).isoformat(), (t - dt.timedelta(days=4)).isoformat()
    for q in ("DELETE FROM purchase_order_line", "DELETE FROM order_scan_tie", "DELETE FROM order_carry", "DELETE FROM purchase_order",
              "DELETE FROM setting WHERE key='aaj.from'"):
        dst.execute(q)
    dst.commit(); dst.close()
    def counts():
        sc = A.connect(cp, rd.x, "staff")[0]; wc = sqlite3.connect("file:%s?mode=ro" % cp, uri=True)
        try:
            return {i: (n_staff(i, sc)[0], A._one(wc, SQL[i])[0]) for i in D3}, A.staff_floor(sc)
        finally:
            sc.close(); wc.close()
    base, _f = counts()
    w = sqlite3.connect(cp)
    for oid, d in ((990645, dX), (990646, dY)):                       # X, Y: sent, nothing came
        w.execute("INSERT INTO purchase_order(id, created_at, created_by, vendor, status, total_p) VALUES (?, ?, 'walk', 'WALK S645 MADE-UP', 'sent', 0)", (oid, d + " 10:00:00"))
        w.execute("INSERT INTO purchase_order_line(order_id, item, packs, pack_size, units) VALUES (?, 'WALK S645 ITEM', 2, 1, 2)", (oid,))
    # Z: received today, not scanned; one line marked missing at arrival, one where nothing came yet
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    w.execute("INSERT INTO purchase_order(id, created_at, created_by, vendor, status, total_p, received_at, received_by) VALUES (990647, ?, 'walk', 'WALK S645 Z', 'received', 0, ?, 'walk')", (now, now))
    w.execute("INSERT INTO purchase_order_line(order_id, item, packs, pack_size, units, missing, arrived_at, arrived_by) VALUES (990647, 'WALK S645 Z1', 1, 1, 1, 1, ?, 'walk')", (now.replace(" ", "T"),))
    w.execute("INSERT INTO purchase_order_line(order_id, item, packs, pack_size, units) VALUES (990647, 'WALK S645 Z2', 1, 1, 1)")
    w.commit(); w.close()
    got, fl = counts()
    dl = {i: (got[i][0] - base[i][0] if None not in (got[i][0], base[i][0]) else None, got[i][1] - base[i][1]) for i in D3}
    check("A8 the made-up X and Y (sent %s, %s, nothing came), floor %s: on reception's list %s and in the whole books %s"
          % (dX, dY, fl, dl["reception.order_arrival"][0], dl["reception.order_arrival"][1]), dl["reception.order_arrival"] == (2, 2), True)
    check("A9 the same two on Shavez's follow-up: list %s, whole books %s" % dl["shavez.order_followup"], dl["shavez.order_followup"] == (2, 2), True)
    check("A10 the made-up Z (received today, one line missing, one not come) on reception's bill scan: list %s, whole books %s" % dl["reception.bill_scan"],
          dl["reception.bill_scan"] == (1, 1), True)
    w = sqlite3.connect(cp); w.execute("INSERT INTO setting(key, value) VALUES ('aaj.from', ?)", ((t - dt.timedelta(days=7)).isoformat(),)); w.commit(); w.close()
    got2, fl2 = counts()
    a2 = {i: (got2[i][0] - base[i][0] if None not in (got2[i][0], base[i][0]) else None, got2[i][1] - base[i][1]) for i in D3}
    check("A11 the floor moved to %s: X leaves both lists (reception %s, Shavez %s), the whole books keep both (%s, %s)"
          % (fl2, a2["reception.order_arrival"][0], a2["shavez.order_followup"][0], a2["reception.order_arrival"][1], a2["shavez.order_followup"][1]),
          a2["reception.order_arrival"] == (1, 2) and a2["shavez.order_followup"] == (1, 2), True)
    check("A12 ... and Z, received today, stays on the bill scan (%s, %s)" % a2["reception.bill_scan"], a2["reception.bill_scan"] == (1, 1), True)
finally:
    for f in os.listdir(td):
        os.remove(os.path.join(td, f))
    os.rmdir(td)

for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if note else ""))
g = sum(1 for r in res if r[1])
if OLD:
    print("%d S645 check(s) red · %d older red · %d green" % (sum(1 for r in res if r[2] and not r[1]), sum(1 for r in res if not r[2] and not r[1]), g))
else:
    print("%d of %d green" % (g, len(res)))
