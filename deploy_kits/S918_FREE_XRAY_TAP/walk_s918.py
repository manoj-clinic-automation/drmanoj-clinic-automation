"""walk_s918.py FINDIR DB -- S918's walk on a COPY of the database: 'Free X-ray' closes a parked photo in one tap.
Prints PASS/FAIL lines and 'WALK n/m' last."""
import importlib, os, shutil, sqlite3, sys, tempfile
FIN, DB0 = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
sys.path.insert(0, FIN)
R = importlib.import_module("records")
CS = importlib.import_module("check_screens")
CS._rec()
res = []
def chk(name, ok, why=""):
    res.append(ok); print(("PASS " if ok else "FAIL ") + name + ("" if ok else " -- " + str(why)[:200]))
tmp = tempfile.mkdtemp(prefix="w918_")
p = os.path.join(tmp, "f.db"); shutil.copy(DB0, p)
con = sqlite3.connect(p); con.row_factory = sqlite3.Row
R.ensure(con)
SH = {"user": "shavez", "roles": ["maker"]}
OW = {"user": "manoj", "roles": ["checker"]}
q = CS.xray_queue(con)
chk("A1 parked X-ray photos are waiting on the copy", len(q) >= 1, len(q))
named = [i for i in q if i["n"] > 1] or q
it = named[0]
n_before = len(q)
st, js = CS.answer(con, SH, {"key": it["key"], "a": "free_xray"})
chk("B1 Shavez's Free X-ray answers 200", st == 200 and js.get("ok"), (st, js))
chk("B2 its message says it is closed", "Free X-ray" in str(js.get("msg")), js)
q2 = CS.xray_queue(con)
chk("B3 it left the waiting list (with all its photos)", it["key"] not in {i["key"] for i in q2} and len(q2) == n_before - 1, (len(q2), n_before))
chk("B4 it is not open on his 'Not in Docterz' (no tap left)", it["sid"] not in {i["sid"] for i in CS.pgap_items(con)})
nd = [i for i in CS.xray_queue(con, nodz_only=True, pairs=False) if i["sid"] == it["sid"]]
chk("B5 his 'Not in Docterz' keeps it as explained 'free X-ray'", bool(nd) and not nd[0]["pg"] and "free X-ray" in nd[0]["pg_note"], nd[:1])
ids = [it["sid"]] + list(it["copies"])
def _a(k, col):
    r = con.execute("SELECT %s FROM record_check WHERE key=?" % col, (k,)).fetchone()
    return r[0] if r else None
chk("B6 every photo of the group answered", all(_a("xf:" + s, "answer") == "no_docterz" and _a("pg:" + s, "note") == "free X-ray" for s in ids))
st, js = CS.answer(con, SH, {"key": it["key"], "a": "free_xray"})
chk("B7 a second tap says it was already answered", st in (200, 409), (st, js))
if len(q2):
    it2 = q2[0]
    st, js = CS.answer(con, OW, {"key": it2["key"], "a": "no_docterz"})
    chk("C1 the old 'not in Docterz' answer still works", st == 200, (st, js))
    st, js = CS.answer(con, OW, {"key": it2["key"], "a": "free_xray"})
    chk("C2 from his Not-in-Docterz tile, Free X-ray closes it", st == 200 and it2["sid"] not in {i["sid"] for i in CS.pgap_items(con)}, (st, js))
src = open(os.path.join(FIN, "check_screens.py"), encoding="utf-8").read()
chk("D1 staff card button says Free X-ray", '<button class="b3" id="nodz">Free X-ray</button>' in src)
chk("D2 the owner's waiting card says Free X-ray", "Free X-ray (not registered)" in src)
chk("D3 both taps send free_xray", src.count("a:'free_xray'") == 2)
chk("D4 'Docterz mein nahi' button gone", 'id="nodz">Docterz mein nahi' not in src)
shutil.rmtree(tmp, ignore_errors=True)
print("WALK %d/%d" % (sum(res), len(res)))
