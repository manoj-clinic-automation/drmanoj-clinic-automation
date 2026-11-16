#!/usr/bin/env python3
"""synth_s845.py -- S845_ITEM_LEDGER on MADE-UP data only (no real file is read): a small stock record and finance database built here,
for the rules the real-data walk cannot pin down by itself. Runs anywhere.  python3 synth_s845.py <finance dir with the built files>"""
import datetime as dt, os, sqlite3, sys, tempfile
FIN = sys.argv[1]
sys.path.insert(0, FIN); sys.path.insert(0, os.path.join(FIN, "spine"))
RES = []
def ok(n, c, d=""):
    RES.append(bool(c)); print("%s  %s%s" % ("PASS" if c else "FAIL", n, ("  -- " + str(d)[:240]) if d else ""))
W = os.environ.get("SYNTH_W") or tempfile.mkdtemp(prefix="synth845_")
os.makedirs(W, exist_ok=True)
SP, DB = os.path.join(W, "spine.db"), os.path.join(W, "finance.db")
os.environ["SPINE_DB"] = SP
import spine_build
s = sqlite3.connect(SP); s.executescript(spine_build.SCHEMA)
T = dt.date.today()
def D(n): return (T - dt.timedelta(days=n)).isoformat()
items = [("TESTOMED 500", "1*10", "LOOSE"), ("TESTGEL", "1", "WHOLE"), ("MIXPACK TAB", "1*10", "LOOSE"), ("MIXPACK TAB", "1*15", "LOOSE")]
for n, p, u in items:
    s.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (n[:20], n, p, u, D(200), D(1)))
s.execute("INSERT INTO sp_meta VALUES ('built', ?)", (dt.datetime.now().isoformat(),))
# TESTOMED: opening 100 at D(40); closings every day D(20)..D(1) except D(5); sales, a purchase keyed late, a counted move on D(5) (no closing)
s.execute("INSERT INTO sp_move VALUES ('TESTOMED 500', ?, 'OPENING', 100, 'x')", (D(40),))
s.execute("INSERT INTO sp_close VALUES (?, 'TESTOMED 500', 100, 'm')", (D(40),))
bal = 100.0
for k in range(20, 0, -1):
    d = D(k)
    s.execute("INSERT INTO sp_sale_bill VALUES (?,?,0,0,0,0,0,0,0,'m')", (d, "A%04d" % k))
    s.execute("INSERT INTO sp_move VALUES ('TESTOMED 500', ?, 'SALE', -2, ?)", (d, "A%04d" % k))
    s.execute("INSERT INTO sp_sale_line VALUES (?,?,1,'TESTOMED 500','TESTOMED 500','1*10','0:2',2,0,'','')", (d, "A%04d" % k))
    bal -= 2
    if k == 10:                                               # two equal lines of one bill (two batches), keyed late in Marg
        for seq in (1, 2):
            s.execute("INSERT INTO sp_move VALUES ('TESTOMED 500', ?, 'PURCHASE', 30, 'DEEPAMPH/77')", (d,))
        s.execute("INSERT INTO sp_purchase_bill VALUES ('DEEPAM PHARMA','DEEPAMPH','77',?,0,'PURCHASE','m')", (d,))
        s.execute("INSERT INTO sp_purchase_line VALUES ('DEEPAMPH','77',?,1,'TESTOMED 500','TESTOMED 500','1*10',3,0,30,0,0,'PURCHASE','m')", (d,))
        s.execute("INSERT INTO sp_purchase_line VALUES ('DEEPAMPH','77',?,2,'TESTOMED 500','TESTOMED 500','1*10',3,0,30,0,0,'PURCHASE','m')", (d,))
        bal += 60
    marg = bal - (60 if k in (10, 9) else 0)                  # Marg took the bill in at D(8)
    if k != 5:
        s.execute("INSERT INTO sp_close VALUES (?, 'TESTOMED 500', ?, 'm')", (d, marg))
s.execute("INSERT INTO sp_close VALUES (?, 'MIXPACK TAB', 37, 'm')", (D(1),))
s.commit(); s.close()
f = sqlite3.connect(DB)
f.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
import marg_hand_change as H
H.ensure(f)
f.execute("INSERT INTO marg_hand_change (k20,item,kind,day_from,day_to,marg_from,marg_to,system_moved,shift,found_at,status,hist) "
          "VALUES ('TESTOMED 500','TESTOMED 500','hand',?,?,10,7,0,-3,?, 'open',0)", (D(6), D(5), D(4)))
f.execute("CREATE TABLE stock_voucher_entered (id INTEGER PRIMARY KEY, count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at)")
f.execute("CREATE TABLE stock_voucher_line (id INTEGER PRIMARY KEY, count_id, round_no, kind, batch_no, batches_n, line_no, section, family, item, packing, pack, marg_from, change, marg_to, counted, rate_p, value_p, reason, made_by, made_at)")
f.execute("INSERT INTO stock_voucher_entered (count_id,round_no,kind,batch_no,marg_voucher_no,entered_on,at) VALUES (1,1,'ISSUE',1,'31',?,?)", (D(3), D(3)))
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,change) VALUES (1,1,'ISSUE',1,'TESTOMED 500',-4)")
f.commit()
if os.environ.get("SYNTH_ONLY_DBS"):
    f.close(); print("made-up databases in", W); sys.exit(0)
import item_ledger as IL
sp = IL.spine_con()
it = IL.item(sp, "TESTOMED 500")
ok("strip item reads strips:tabs", it["unit"].fmt(37) == "3:7", it["unit"].fmt(37))
mx = IL.item(sp, "MIXPACK TAB")
ok("a key of two strip sizes reads plain units", isinstance(mx["unit"], IL.Plain) and mx["unit"].fmt(37) == "37", mx["unit"].fmt(37))
fr = IL.find(sp, "mixp")
ok("the search shows the same unit as the page", fr and fr[0]["marg"] == "37", fr)
T0 = f.total_changes
L = IL.ledger(f, sp, "TESTOMED 500", D(20), D(0))
st = {d["day"]: d for d in L["days"]}
ok("the counted move on a day with NO closing is red", st.get(D(5), {}).get("state") == "bad", st.get(D(5), {}).get("state"))
ok("and counted once in the totals", L["totals"]["n_bad"] == 1 and L["totals"]["nonrec"] == -3, (L["totals"]["n_bad"], L["totals"]["nonrec"]))
ok("the bill keyed late reads late (both equal lines owed)", st[D(10)]["state"] == "late", (st[D(10)]["state"], st[D(10)].get("late")))
ok("one closing later still owed: no false 'taken in'", st[D(9)]["state"] in ("ok", "late", "differs") and st[D(9)]["state"] != "late_in", st[D(9)]["state"])
ok("taken in at D-8 (both lines at once)", st[D(8)]["state"] == "late_in", (st[D(8)]["state"], st[D(8)].get("late"), st[D(8)]["diff"]))
v = [e for d in L["days"] for e in d["entries"] if e["kind"] == "voucher"]
ok("the voucher is on its day with its Marg number", v and v[0]["ref"] == "Marg voucher 31" and v[0]["u"] == -4, v)
days = list(reversed(L["days"]))
chain = all(abs(days[i]["opening"] - (days[i - 1]["marg"] if days[i - 1]["marg"] is not None else days[i - 1]["expected"])) < 1e-9 for i in range(1, len(days)))
ok("each day opens where the day before ended", chain)
import flask
app = flask.Flask("s"); IL.init(app, lambda: f, lambda r: ({"user": "m"}, None)); c = app.test_client()
for path in ("/finance/sanjeevni/ledger?k=TESTOMED%20500", "/finance/sanjeevni/ledger?k=TESTOMED%20500&r=full", "/finance/sanjeevni/ledger?k=MIXPACK%20TAB",
             "/finance/sanjeevni/ledger?q=testo", "/finance/sanjeevni/ledger?q=" + "x" * 500):
    r = c.get(path); t = r.get_data(as_text=True)
    ok("page %s answers 200" % path[:60], r.status_code == 200 and "Traceback" not in t, r.status_code)
t = c.get("/finance/sanjeevni/ledger?k=TESTOMED%20500").get_data(as_text=True)
ok("the red day without a closing says so on the page", "no Marg closing of this item this day" in t)
ok("the page guards the scan opener", "typeof s738open==='function'" in t)
ok("the search is a form (Enter works before suggestions)", '<form class="search" method="get"' in t)
ok("nothing written", f.total_changes == T0, f.total_changes - T0)
print("SYNTH S845: %d PASS, %d FAIL" % (sum(RES), len(RES) - sum(RES)))
sys.exit(0 if all(RES) else 1)
