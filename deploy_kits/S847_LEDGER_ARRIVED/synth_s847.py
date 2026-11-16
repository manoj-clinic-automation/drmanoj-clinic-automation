#!/usr/bin/env python3
"""synth_s847.py -- S847_LEDGER_ARRIVED on MADE-UP data only: a waiting scan older than Marg's purchases, or a quantity far beyond the item's
own, is shown and never added to the expected stock; a fresh, sane one is added.   python3 synth_s847.py <finance dir> <S845 kit dir>
(builds its made-up databases with the S845 kit's synth_s845.py)."""
import os, subprocess, sys, tempfile
FIN, K845 = sys.argv[1], sys.argv[2]
W = tempfile.mkdtemp(prefix="synth847_")
env = dict(os.environ, SYNTH_W=W, SYNTH_ONLY_DBS="1")
subprocess.run([sys.executable, "-W", "ignore", "-B", os.path.join(K845, "synth_s845.py"), FIN], env=env, check=True, stdout=subprocess.DEVNULL)
os.environ["SPINE_DB"] = os.path.join(W, "spine.db")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
sys.path.insert(0, FIN); sys.path.insert(0, os.path.join(FIN, "spine"))
import datetime as dt, sqlite3
import item_ledger as IL
RES = []
def ok(n, c, d=""):
    RES.append(bool(c)); print("%s  %s%s" % ("PASS" if c else "FAIL", n, ("  -- " + str(d)[:200]) if d else ""))
con = sqlite3.connect(os.path.join(W, "finance.db")); con.row_factory = sqlite3.Row
sp = IL.spine_con()
T = IL.today()
def D(n): return (T - dt.timedelta(days=n)).isoformat()
PV = IL._PV()
PV.provisional = lambda c, ym: ([
    dict(id=1, stamp="B-1", dealer="", known=False, bill_no="1", date=D(0), total_p=1, day=D(0), lines=[dict(name="TESTOMED 500", qty=3)], why=[]),
    dict(id=2, stamp="B-2", dealer="", known=False, bill_no="2", date=D(20), total_p=1, day=D(20), lines=[dict(name="TESTOMED 500", qty=3)], why=[]),
    dict(id=3, stamp="B-3", dealer="", known=False, bill_no="3", date=D(0), total_p=1, day=D(0), lines=[dict(name="TESTOMED 500", qty=5010)], why=[])]
    if ym == T.strftime("%Y-%m") else [])
A = {a["scan"]["id"]: a for a in IL.arrived(con, sp, "TESTOMED 500")}
ok("a fresh scan with a sane quantity is added (3 strips = 30)", A.get(1) and A[1]["units"] == 30.0, A.get(1, {}).get("units"))
ok("a scan older than Marg's purchases is shown, not added", A.get(2) and A[2]["units"] == 0 and "not added" in A[2]["lines"][0]["why"], A.get(2, {}).get("lines"))
ok("a quantity far beyond the item's own is shown, not added", A.get(3) and A[3]["units"] == 0 and "misread" in A[3]["lines"][0]["why"], A.get(3, {}).get("lines"))
import flask
app = flask.Flask("s"); IL.init(app, lambda: con, lambda r: ({"user": "m"}, None)); c = app.test_client()
t = c.get("/finance/sanjeevni/ledger?k=TESTOMED%20500").get_data(as_text=True)
last = sp.execute("SELECT units FROM sp_close WHERE k20='TESTOMED 500' ORDER BY as_on DESC LIMIT 1").fetchone()[0]
want = IL.item(sp, "TESTOMED 500")["unit"].fmt(last + 30)
ok("the page's expected stock = Marg + only the fresh scan (%s)" % want, ">%s<" % want in t)
ok("the misread and the stale scan are listed with their reason", "looks misread" in t and "Marg&#x27;s purchases already run to" in t)
print("SYNTH S847: %d PASS, %d FAIL" % (sum(RES), len(RES) - sum(RES)))
sys.exit(0 if all(RES) else 1)
