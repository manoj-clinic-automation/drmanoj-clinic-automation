#!/usr/bin/env python3
"""walk_s965.py -- S965_VOUCHER_JUDGE on MADE-UP data only (no real file is read): a small stock record and finance database built here.
    python3 walk_s965.py FIN_DIR MI_DIR [--control]
FIN_DIR holds the finance files (the built ones, or the live ones for the control) with spine/ beside; MI_DIR holds marg_vouchers.py.
Last line: WALK passed/total."""
import datetime as dt, json, os, sqlite3, sys, tempfile, types
FIN, MI = sys.argv[1], sys.argv[2]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, MI); sys.path.insert(0, os.path.join(FIN, "spine")); sys.path.insert(0, FIN)
RES = []
def ok(n, c, d=""):
    RES.append(bool(c)); print("%s  %s%s" % ("PASS" if c else "FAIL", n, ("  -- " + str(d)[:260]) if d and not c else ""))
W = tempfile.mkdtemp(prefix="walk965_")
SP, DB = os.path.join(W, "spine.db"), os.path.join(W, "finance.db")
os.environ["SPINE_DB"] = SP
T = dt.date.today()
def D(n): return (T - dt.timedelta(days=n)).isoformat()
def dmy(iso): return "%s-%s-%s" % (iso[8:10], iso[5:7], iso[:4])
try:
    import voucher_judge as V
except Exception as ex:                                                   # the control: the live files have no judge
    ok("the judge is beside the finance files", False, repr(ex)); print("WALK %d/%d" % (sum(RES), len(RES))); sys.exit(0)
import marg_vouchers as MV
import spine_build
s = sqlite3.connect(SP); s.executescript(spine_build.SCHEMA)
for n, p, u in (("TESTOMED 500", "1*10", "LOOSE"), ("KNEE IMMOBILIZER L UNISON", "1*1", "WHOLE"), ("KNEE IMMOBILIZER M TYNOR", "1*1", "WHOLE"),
                ("KNEE SUPPORT HINGED", "1*1", "WHOLE"), ("KNEE SUPPORT XL HINGED", "1*1", "WHOLE")):
    s.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (n[:20], n, p, u, D(200), D(1)))
s.execute("INSERT INTO sp_meta VALUES ('built', ?)", (dt.datetime.now().isoformat(),))
s.execute("INSERT INTO sp_alias VALUES ('KNEE SUPPORT XL HING', 'KNEE SUPPORT XL HING', 'rename_family', "
          "'S605: a size of a shared key keeps its own key (split %s from KNEE SUPPORT HINGED)')" % D(5))
s.execute("INSERT INTO sp_move VALUES ('TESTOMED 500', ?, 'OPENING', 100, 'x')", (D(60),))
s.execute("INSERT INTO sp_close VALUES (?, 'TESTOMED 500', 100, 'm')", (D(60),))
s.execute("INSERT INTO sp_close VALUES (?, 'TESTOMED 500', 96, 'm')", (D(40),))      # Amir's typed voucher of D-40: before the reports
s.execute("INSERT INTO sp_close VALUES (?, 'TESTOMED 500', 105, 'm')", (D(3),))       # through every voucher line to D-3
s.commit(); s.close()
f = sqlite3.connect(DB)
f.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
import marg_hand_change as H
H.ensure(f)
f.execute("CREATE TABLE stock_voucher_entered (id INTEGER PRIMARY KEY, count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at)")
f.execute("CREATE TABLE stock_voucher_line (id INTEGER PRIMARY KEY, count_id, round_no, kind, batch_no, batches_n, line_no, section, family, item, packing, "
          "pack, marg_from, change, marg_to, counted, rate_p, value_p, reason, made_by, made_at)")
for cid, rno, kind, bno, no, on in ((1, 1, "ISSUE", 1, "31", D(3)), (1, 2, "ISSUE", 1, "7", D(40))):
    f.execute("INSERT INTO stock_voucher_entered (count_id,round_no,kind,batch_no,marg_voucher_no,entered_on,at) VALUES (?,?,?,?,?,?,?)", (cid, rno, kind, bno, no, on, on))
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,pack,change,made_at) VALUES (1,1,'ISSUE',1,'TESTOMED 500',10,-4,?)", (D(10),))
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,pack,change,made_at) VALUES (1,2,'ISSUE',1,'TESTOMED 500',10,-4,?)", (D(45),))
f.execute("CREATE TABLE amir_job (id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, text_hi TEXT, sub_hi TEXT, "
          "created_at TEXT NOT NULL, created_by TEXT, show_from TEXT, said_at TEXT, said_by TEXT, said_what TEXT, done_at TEXT, done_how TEXT, reopened_at TEXT)")
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('W:gel','tap','TESTGEL','TESTGEL — STOCK ISSUE 3 nag Marg mein daaliye',?,?)", (D(9), D(5)))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('W:pay','tap','A DEALER','₹310 cash payment ki entry',?,?)", (D(9), D(5)))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('W:same','tap','SAMEGEL','SAMEGEL — STOCK ISSUE 1 nag Marg mein daaliye',?,?)", (D(4), D(2)))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('W:late','tap','LATEGEL','LATEGEL — STOCK ISSUE 2 nag Marg mein daaliye',?,?)", (D(3), D(1)))
f.execute("CREATE TABLE stock_batch_fix (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, k20 TEXT NOT NULL, item TEXT NOT NULL, pack INTEGER NOT NULL, minus_batch TEXT NOT NULL, "
          "units INTEGER NOT NULL, issue_batch TEXT NOT NULL, issue_printed INTEGER, issue_expiry TEXT, asked_run_id INTEGER NOT NULL, asked_md5 TEXT, asked_day TEXT, "
          "asked_at TEXT NOT NULL, status TEXT NOT NULL, judged_run_id INTEGER, judged_md5 TEXT, judged_at TEXT, done_at TEXT, note TEXT)")
f.execute("INSERT INTO stock_batch_fix (kind,k20,item,pack,minus_batch,units,issue_batch,asked_run_id,asked_day,asked_at,status) "
          "VALUES ('batch','TESTOMED 500','TESTOMED 500',10,'B1',6,'B2',1,?,?,'open')", (D(8), D(8)))
f.execute("INSERT INTO stock_batch_fix (kind,k20,item,pack,minus_batch,units,issue_batch,asked_run_id,asked_day,asked_at,status) "
          "VALUES ('batch','TESTOMED 500','TESTOMED 500',10,'Q1',5,'Q2',1,?,?,'superseded')", (D(20), D(20)))
f.execute("CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER, packing TEXT, pack_size INTEGER, loaded_at TEXT, source TEXT, PRIMARY KEY (as_on, item))")
for n in ("TESTOMED 500", "TESTGEL", "LATEGEL", "SAMEGEL", "NORTIMER TAB", "KNEE IMMOBILIZER L UNISON", "KNEE IMMOBILIZER M TYNOR", "KNEE IMMOBILIZER XL UNISON",
          "KNEE SUPPORT XL HINGED"):
    f.execute("INSERT INTO stock_snapshot VALUES (?,?,1,'1*1',1,'x','x')", (dmy(D(1)), n))
MV.ensure(f); MV._migrate(f)
f.execute("INSERT INTO mi_voucher_file (md5,kind,date_from,date_to,n_vouchers,n_lines,gross_p,bill_p,ok,note,stored_at,seq,exported) "
          "VALUES ('mI','ISSUE',?,?,0,0,0,0,1,'','x',1,?)", (D(30), D(2), D(2).replace('-', '') + '-145500'))
f.execute("INSERT INTO mi_voucher_file (md5,kind,date_from,date_to,n_vouchers,n_lines,gross_p,bill_p,ok,note,stored_at,seq,exported) "
          "VALUES ('mR','RECEIVE',?,?,0,0,0,0,1,'','x',2,'20260101-000000')", (D(30), D(2)))
f.execute("INSERT INTO mi_voucher_file (md5,kind,date_from,date_to,n_vouchers,n_lines,gross_p,bill_p,ok,note,stored_at,seq,exported) "
          "VALUES ('mO','ISSUE',?,?,0,0,0,0,1,'','x',3,'20260101-000000')", (D(52), D(45)))     # an older report: a gap D-44..D-31 (review S5)
LINES = [("mI", "ISSUE", "L000031", 1, D(3), "TESTOMED 500", "B7", 4),         # C1 asked (typed 31)
         ("mR", "RECEIVE", "AD00002", 1, D(7), "TESTOMED 500", "B1", 6),        # C3 the receive half asked
         ("mI", "ISSUE", "L000032", 1, D(7), "TESTOMED 500", "B9", 6),          # C3 the issue half: the wrong batch
         ("mI", "ISSUE", "L000033", 1, D(6), "TESTOMED 500", "X", 2),           # C4 keyed and undone
         ("mR", "RECEIVE", "AD00003", 1, D(6), "TESTOMED 500", "X", 2),
         ("mR", "RECEIVE", "AD00006", 1, D(5), "TESTOMED 500", "B1", 6),        # C5 keyed twice
         ("mR", "RECEIVE", "AD00004", 1, D(4), "NORTIMER TAB", "24006", 90),    # C6 nobody asked
         ("mR", "RECEIVE", "AD00005", 1, D(4), "KNEE IMMOBILIZE", "", 1),       # C7 a cut name, several items
         ("mR", "RECEIVE", "AD00005", 2, D(4), "KNEE IMMOBILIZE", "", 1),
         ("mR", "RECEIVE", "AD00007", 1, D(19), "TESTOMED 500", "Q1", 7),       # R2 only a superseded fix (5) of this batch: nobody asked
         ("mI", "ISSUE", "L000040", 1, D(10), "KNEE SUPPORT XL HINGED", "", 1)] # R4 a new size name before its family's split day
for md5, kind, no, n, day, item, batch, u in LINES:
    f.execute("INSERT OR IGNORE INTO mi_voucher (md5,kind,no,day,cash,gross_p,bill_p,n_lines) VALUES (?,?,?,?,1,0,0,1)", (md5, kind, no, day))
    f.execute("INSERT INTO mi_voucher_line (md5,kind,no,n,day,item,packing,per,batch,qty,units,unit,expiry,rate_p,value_p) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (md5, kind, no, n, day, item, "1*10" if "TESTOMED" in item else "1*1", 10 if "TESTOMED" in item else 1, batch, str(u), u, "TAB", "", 100, 100 * u))
f.commit()
T0 = f.total_changes
J = V.judge(f, T.isoformat())
A = {a["id"]: a for a in J["asks"]}
Lx = {ln["key"]: ln for ln in J["lines"]}
ok("C1 a count line found in Marg by item, figure and day: in Marg, Amir's typed 31 = L000031", A["c1"]["state"] == "in_marg" and A["c1"]["match"]["no"] == "L000031", A["c1"])
ok("C1b a count line typed 7 on a day no report covers (the gap between two reports): 'no report covers its day', not 'not in Marg' (review S5)",
   A["c2"]["state"] == "gap", A["c2"]["state"])
gel = [a for a in J["asks"] if a["src"] == "job" and a["item"] not in ("LATEGEL", "SAMEGEL")]
ok("C2 Amir's card asking STOCK ISSUE 3 of TESTGEL, tapped done, nothing in Marg: 'not in Marg'; the payment card asks nothing",
   len(gel) == 1 and gel[0]["state"] == "not_in_marg" and gel[0]["units"] == 3, [(a["item"], a["state"]) for a in gel])
ok("C3 a batch fix: the receive into B1 in Marg; the issue keyed from B9, not B2: 'wrong batch'",
   A["b1R"]["state"] == "in_marg" and A["b1I"]["state"] == "wrong_batch" and Lx["ISSUE|L000032|1"]["state"] == "wrong_batch", (A["b1R"]["state"], A["b1I"]["state"]))
ok("C4 an issue and a receive of the same item, batch and figure nobody asked: keyed and undone",
   Lx["ISSUE|L000033|1"]["state"] == "cancel" and Lx["RECEIVE|AD00003|1"]["state"] == "cancel")
ok("C5 the same receive keyed again: 'keyed twice'", Lx["RECEIVE|AD00006|1"]["state"] == "twice", Lx["RECEIVE|AD00006|1"]["state"])
ok("C6 a receive no correction asked for: 'nobody asked'", Lx["RECEIVE|AD00004|1"]["state"] == "unasked")
ok("C6b a superseded fix with no line asks nothing", A["b2R"]["state"] == "superseded" and A["b2I"]["state"] == "superseded")
late = [a for a in J["asks"] if a["item"] == "LATEGEL"]
ok("R1 a card tapped done after the newest report's last day: 'after the newest report', never 'not in Marg' (review M1)",
   len(late) == 1 and late[0]["state"] == "beyond", [(a["item"], a["state"]) for a in late])
same = [a for a in J["asks"] if a["item"] == "SAMEGEL"]
ok("R1b a card done on the newest report's export day (after the export): 'after the newest report', never red (second look M1)",
   len(same) == 1 and same[0]["state"] == "beyond", [(a["item"], a["state"]) for a in same])
ok("R2 a superseded fix never claims a line of another figure: the receive of 7 into Q1 is 'nobody asked' (review S4)",
   Lx["RECEIVE|AD00007|1"]["state"] == "unasked", Lx["RECEIVE|AD00007|1"]["state"])
P = V.page(f, T.isoformat())
ok("C7 a cut name fitting several items: listed with its candidates, on no item", len(P["cut"]) == 2 and len(P["cut"][0]["cands"]) == 3
   and all(not x.get("ambiguous") or x["item"] == "KNEE IMMOBILIZE" for x in J["lines"]), P["cut"])
ok("C8 the page: two boxes' parts and chips", P["ok"] and [m["no"] for m in P["moves"]] == ["AD00004", "L000040", "AD00007"] and P["chips"]["not_in_marg"] == 1
   and P["chips"]["off"] == 1 and P["chips"]["waiting"] == 3 and sum(1 for w in P["waiting"] if w["beyond"]) == 2 and sum(1 for w in P["waiting"] if w["gap"]) == 1, (P["chips"], [m["no"] for m in P["moves"]]))
ok("C8b nothing written by the judge or the page", f.total_changes == T0, f.total_changes - T0)
# C9 the registers asked (the Marg watch's own writer), once only
import marg_billwatch as BW
BW.ensure(f); f.commit()
n1 = V.ask_registers(f); n2 = V.ask_registers(f)
asked = [r[0] for r in f.execute("SELECT item FROM marg_watch_report WHERE item IS NOT NULL ORDER BY item")]
ok("C9 the cut name asks each candidate's one-item Stock Register once, for that day", n1 == 3 and n2 == 0 and asked == sorted(
    ["KNEE IMMOBILIZER L UNISON", "KNEE IMMOBILIZER M TYNOR", "KNEE IMMOBILIZER XL UNISON"]), (n1, n2, asked))
f.execute("DELETE FROM marg_watch_report"); f.commit()
ok("R8 an ask closed or gone is never asked again (review S8)", V.ask_registers(f) == 0 and f.execute("SELECT COUNT(*) FROM marg_watch_report").fetchone()[0] == 0)
# C10 the name table settles line 1; a register settles line 2
V.ensure_names(f, seed=False)
f.execute("INSERT INTO mi_voucher_name VALUES ('RECEIVE','AD00005',1,'KNEE IMMOBILIZE','KNEE IMMOBILIZER L UNISON','walk','x')")
f.execute("CREATE TABLE IF NOT EXISTS mi_register (md5 TEXT NOT NULL, seq INTEGER NOT NULL, item TEXT NOT NULL, pack TEXT NOT NULL DEFAULT '', per INTEGER NOT NULL DEFAULT 1, "
          "date_from TEXT NOT NULL DEFAULT '', date_to TEXT NOT NULL DEFAULT '', opening_u INTEGER, closing_u INTEGER, received_u INTEGER, issued_u INTEGER, "
          "n_lines INTEGER NOT NULL DEFAULT 0, n_jumps INTEGER NOT NULL DEFAULT 0, ok INTEGER NOT NULL DEFAULT 0, note TEXT NOT NULL DEFAULT '', stored_at TEXT NOT NULL, PRIMARY KEY (md5, seq))")
f.execute("CREATE TABLE IF NOT EXISTS mi_register_line (md5 TEXT NOT NULL, seq INTEGER NOT NULL, n INTEGER NOT NULL, day TEXT NOT NULL, bill_no TEXT NOT NULL DEFAULT '', "
          "kind TEXT NOT NULL DEFAULT '', batch TEXT NOT NULL DEFAULT '', qty_u INTEGER NOT NULL, value_p INTEGER, bal_u INTEGER, jump_u INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (md5, seq, n))")
f.execute("INSERT INTO mi_register VALUES ('rg',1,'KNEE IMMOBILIZER M TYNOR','1*1',1,?,?,0,1,1,0,1,0,1,'',?)", (D(4), D(4), D(1)))
f.execute("INSERT INTO mi_register_line VALUES ('rg',1,1,?,'AD00005','Received','',1,0,1,0)", (D(4),))
f.commit()
P = V.page(f, T.isoformat())
nm = {(x["no"], x["item"], x["by"]) for x in P["named"]}
ok("C10 his word names line 1, Marg's Stock Register names line 2: no cut name left", not P["cut"] and nm == {
    ("AD00005", "KNEE IMMOBILIZER L UNISON", "your Marg screen"), ("AD00005", "KNEE IMMOBILIZER M TYNOR", "Marg's Stock Register")}, (P["cut"], nm))
ok("C10b his word holds only while the line still prints that cut name", V.ensure_names(f, seed=True) is None and len(
    [1 for x in V.marg_lines(f) if x["no"] == "AD00010"]) == 0)
ok("C11 F-1690: a one-item register shows on the page", any(g["item"] == "KNEE IMMOBILIZER M TYNOR" for g in P["registers"]), P["registers"])
# C12 the item ledger: Marg's own lines inside the reports' days, Amir's typed number outside them
import item_ledger as IL
sp = IL.spine_con()
L = IL.ledger(f, sp, "TESTOMED 500", D(60), D(0))
ve = [(e["ref"], e["u"], (e.get("s965") or {}).get("state")) for d in L["days"] for e in d["entries"] if e["kind"] == "voucher"]
ok("C12 the ledger: inside the reports Marg's numbers and judgments; Amir's typed 31 gone; his typed 7 of D-40 (in the gap between two reports) kept",
   ("Marg voucher L000031", -4.0, "asked") in ve and ("Marg voucher 7", -4.0, None) in ve and not any(r == "Marg voucher 31" for r, _, _ in ve)
   and ("Marg voucher L000032", -6.0, "wrong_batch") in ve, ve)
d3 = [d for d in L["days"] if d["day"] == D(3)][0]
L4 = IL.ledger(f, sp, "KNEE SUPPORT HINGED", D(60), D(0)); L5 = IL.ledger(f, sp, "KNEE SUPPORT XL HING", D(60), D(0))
r4 = [e.get("ref") for d in L4["days"] for e in d["entries"] if e["kind"] == "voucher"]; r5 = [e.get("ref") for d in L5["days"] for e in d["entries"] if e["kind"] == "voucher"]
ok("R4 a new size name keyed before its family's split day lands on the old family key (spine_build.Zd) (review S6)",
   r4 == ["Marg voucher L000040"] and r5 == [], (r4, r5))
ok("C12b the day of L000031 agrees with Marg's closing (105)", d3["state"] == "ok" and abs(d3["expected"] - 105) < 1e-9, (d3["state"], d3["expected"]))
h = IL._ledger_html(L, IL.item(sp, "TESTOMED 500")["unit"], "TESTOMED 500", "full", D(60), D(0))
ok("C12c each voucher row: its judgment, a Voucher button and its folded lines", "Voucher ▾" in h and 'class="vt red">wrong batch' in h
   and "Every line of Marg voucher L000032" in h, h[:200])
ok("C12d the item's open ask (the count line in the gap) shows above the ledger", "vasks" in h and "no report covers its day" in h)
L2 = IL.ledger(f, sp, "KNEE IMMOBILIZER L U", D(60), D(0))
ok("C12e the cut line named by his word lands on its item's ledger", any(e.get("ref") == "Marg voucher AD00005" for d in L2["days"] for e in d["entries"]))
g = sqlite3.connect(os.path.join(W, "empty.db"))
ok("C13 an empty database: the page says so, the ledger keeps the old rule, nothing raises", V.page(g)["ok"] is False and IL._s965_vouchers(g, sp, "X", [1]) == [1])
# C14 the doors (Flask)
import flask
import stock_check as SC
app = flask.Flask("w"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None)); c = app.test_client()
r = c.get("/finance/stockcheck/api/vouchers"); j = r.get_json() or {}
ok("C14 /api/vouchers answers the page's JSON", r.status_code == 200 and j.get("ok") and "moves" in j and "tags" in j, (r.status_code, str(j)[:120]))
pg = c.get("/finance/stockcheck/").get_data(as_text=True)
ok("C14b the page carries the section, the tags and the cut-name list", 'id="vbody"' in pg and "function vsection" in pg and "vtagsFor(r.item)" in pg
   and "/api/vouchers" in pg and "Name cut short by Marg" in pg)
app2 = flask.Flask("w2"); SC.init(app2, lambda: f, lambda *r: (({"user": "viewer"}, None) if "viewer" in r else (None, ("no", 403))))
SC._VCACHE["v"] = None; f.execute("DELETE FROM mi_voucher_regask"); f.execute("DELETE FROM marg_watch_report"); f.commit()
r2 = app2.test_client().get("/finance/stockcheck/api/vouchers?fresh=1")
ok("R8b a viewer's read asks nothing", r2.status_code == 200 and f.execute("SELECT COUNT(*) FROM marg_watch_report").fetchone()[0] == 0)
ok("C14c the healthz says v1.5", c.get("/finance/stockcheck/api/healthz").get_json().get("version") == "1.5")
# C15 F-1701: the export's own stamp wins over a retry's
f.execute("CREATE TABLE IF NOT EXISTS mi_file (md5 TEXT PRIMARY KEY, drive_name TEXT NOT NULL DEFAULT '')")
f.execute("INSERT INTO mi_file (md5, drive_name) VALUES ('mI', 'MEDICAL__20261126-171126__20261126-154650__user_report.txt')")
f.execute("INSERT INTO mi_file (md5, drive_name) VALUES ('mR', 'MEDICAL__20261126-150000__user_report.txt')")
ok("C15 two stamps: the export's (the second); one: its own", MV.export_stamp(f, "mI") == "20261126-154650" and MV.export_stamp(f, "mR") == "20261126-150000"
   and MV.export_stamp(f, "zz", "x") == "x")
ok("C15b restamp puts both kept sheets on their export's time (the real MEDICAL__ names)", MV.restamp(f) == 2 and
   [r[0] for r in f.execute("SELECT exported FROM mi_voucher_file WHERE md5 IN ('mI','mR') ORDER BY md5")] == ["20261126-154650", "20261126-150000"])
print("WALK %d/%d" % (sum(RES), len(RES)))
