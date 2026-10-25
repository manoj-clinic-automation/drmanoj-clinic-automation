"""walk_s647.py -- kit S647_RECEPTION_ORDER_WORDS (S349, 25-Oct-2026). READ-ONLY: the database is read mode=ro through aaj_kaam's Reader.
  python walk_s647.py <dir holding the aaj_seed.py under test> <finance dir> [--db PATH] [--old]   (internal: --dump)"""
import json, os, subprocess, sys, tempfile
argv = sys.argv[1:]; DB = None
if "--db" in argv:
    k = argv.index("--db"); DB = argv[k + 1]; del argv[k:k + 2]
OLD, DUMP = "--old" in argv, "--dump" in argv
args = [a for a in argv if not a.startswith("--")]
SEEDDIR, FIN = os.path.abspath(args[0]), os.path.abspath(args[1]); DB = DB or os.path.join(FIN, "finance.db")
sys.path[:0] = [SEEDDIR, FIN]
import aaj_seed as S                                                   # noqa: E402
import aaj_kaam as A                                                   # noqa: E402
assert A.SEED is S and os.path.dirname(os.path.abspath(S.__file__)) == SEEDDIR
WANT = "Order ka maal nahi aaya — supplier ko call kijiye"
rd = A.Reader(DB)

def rows():
    out = {}
    for k, doc in rd.people.items():
        lst = A.person_list(rd, doc, view_as=True)
        for sec, rs in lst["sections"].items():
            for r in rs:
                out["%s|%s" % (k, r["id"])] = [sec, r["kind"], r["text"]]
        out["%s|_unread" % k] = lst["unread"]
    return out

if DUMP:
    print(json.dumps(rows(), sort_keys=True, ensure_ascii=False)); sys.exit(0)
res = []
def check(name, ok, s647=True, note=""):
    res.append((name, bool(ok), s647, note))
me = rows()
r = me.get("reception|reception.order_arrival")
check("B1 reception's late-order line reads '%s'" % WANT, bool(r) and r[2] == WANT, True, "now: %s" % (r[2] if r else "absent"))
check("B2 ... it is still a job line in 'Jab aaye' (comeup), read, and her list has no unread line",
      bool(r) and r[0] == "comeup" and r[1] == "job" and me.get("reception|_unread") == 0, False, str(r))
seed = [l for p in getattr(S, "PEOPLE", []) or [] for l in (p.get("lines") or []) if l.get("id") == "reception.order_arrival"] if hasattr(S, "PEOPLE") else []
src = open(os.path.join(SEEDDIR, "aaj_seed.py"), encoding="utf-8").read()
check("B3 the seed's English line says the goods have NOT come", "An order's goods have not come: calls the supplier." in src)
other = os.path.join(FIN, "aaj_seed.py") if not OLD else os.path.join(SEEDDIR, "aaj_seed.py")
tmp = tempfile.mkdtemp(prefix="s647o"); open(os.path.join(tmp, "aaj_seed.py"), "wb").write(open(other, "rb").read())
d = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), tmp, FIN, "--db", DB, "--dump"], capture_output=True, text=True)
os.remove(os.path.join(tmp, "aaj_seed.py")); os.rmdir(tmp)
try:
    them = json.loads(d.stdout)
    diff = [k for k in set(me) | set(them) if k != "reception|reception.order_arrival" and me.get(k) != them.get(k)]
    check("B4 every other line of every person's list (section, kind, words) is as before (%d)" % (len(me) - 1), not diff, False, ", ".join(sorted(diff))[:300])
except Exception:
    check("B4 every other line of every person's list is as before", False, False, d.stderr[-300:])
for name, ok, s6, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", name, ("   [" + note + "]") if note else ""))
g = sum(1 for x in res if x[1])
if OLD:
    print("%d S647 check(s) red · %d older red · %d green" % (sum(1 for x in res if x[2] and not x[1]), sum(1 for x in res if not x[2] and not x[1]), g))
else:
    print("%d of %d green" % (g, len(res)))
