#!/usr/bin/env python3
"""walk_s969.py -- S969_STOCKCHECK_DESK_WRITES (on S967's made-up fixture, three items added) on MADE-UP data only (no real file is read): a small stock record, spine and finance database
built here.      python3 walk_s967.py FIN_DIR MI_DIR
FIN_DIR holds the finance files (the built ones, or the live ones for the control) with spine/ beside; MI_DIR holds marg_vouchers.py.
Last line: WALK passed/total."""
import datetime as dt, json, os, sqlite3, sys, tempfile
FIN, MI = sys.argv[1], sys.argv[2]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, MI); sys.path.insert(0, os.path.join(FIN, "spine")); sys.path.insert(0, FIN)
RES = []


def ok(n, c, d=""):
    RES.append(bool(c)); print("%s  %s%s" % ("PASS" if c else "FAIL", n, ("  -- " + str(d)[:300]) if d and not c else ""))


W = tempfile.mkdtemp(prefix="walk969_")
SP, DB = os.path.join(W, "spine.db"), os.path.join(W, "finance.db")
os.environ["SPINE_DB"] = SP
T = dt.date.today()


def D(n):
    return (T - dt.timedelta(days=n)).isoformat()


def dmy(iso):
    return "%s-%s-%s" % (iso[8:10], iso[5:7], iso[:4])


import stock_check as SC
if not hasattr(SC, "r_desk_act"):                                        # the control: the live files have no desk writes
    ok("the desk's writes are in stock_check.py", False, "no r_desk_act"); print("WALK %d/%d" % (sum(RES), len(RES))); sys.exit(0)
import voucher_judge as V
import item_ledger as IL
import marg_vouchers as MV
import stock_watch as SW
import stock_record as SR
import spine_build
# ---------------------------------------------------------------- the made-up spine
s = sqlite3.connect(SP); s.executescript(spine_build.SCHEMA)
ITEMS = (("NORTEST TAB", "1*10", "LOOSE"), ("ALLOWTEST", "1*10", "LOOSE"), ("OLDTEST", "1*10", "LOOSE"), ("AGREETEST", "1*10", "LOOSE"),
         ("KTTEST DT", "1*15", "LOOSE"), ("PANTEST 40", "1*10", "LOOSE"), ("SHOETEST L", "1*1", "WHOLE"), ("EVETEST", "1*10", "LOOSE"),
         ("VINBACTUM DS", "1*1", "WHOLE"), ("SURPTEST", "1*10", "LOOSE"), ("GONETEST", "1*10", "LOOSE"), ("ALLOW-PT", "1*10", "LOOSE"),
         ("KEPTTEST", "1*10", "LOOSE"), ("TWOTEST", "1*10", "LOOSE"), ("RECTEST", "1*10", "LOOSE"), ("ONLISTTEST", "1*10", "LOOSE"))
for n, p, u in ITEMS:
    s.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (n[:20], n, p, u, D(200), D(1)))
s.execute("INSERT INTO sp_meta VALUES ('built', ?)", (dt.datetime.now().isoformat(),))
for n, _p, _u in ITEMS:
    s.execute("INSERT INTO sp_move VALUES (?, ?, 'OPENING', 100, 'x')", (n[:20], D(60)))
    s.execute("INSERT INTO sp_close VALUES (?, ?, 100, 'm')", (D(60), n[:20]))
# F-1708: two purchase lines of 30, one closing short by 30 -> which one is not known
for bill, d in (("4043", D(10)), ("4100", D(8))):
    s.execute("INSERT INTO sp_move VALUES ('PANTEST 40', ?, 'PURCHASE', 30, ?)", (d, "SUPK/" + bill))
    s.execute("INSERT INTO sp_purchase_bill VALUES ('A DEALER','SUPK',?,?,0,'PURCHASE','x')", (bill, d))
s.execute("INSERT INTO sp_close VALUES (?, 'PANTEST 40', 130, 'm')", (D(7),))
s.execute("INSERT INTO sp_sale_line VALUES (?, 'S1', 1, 'ALLOWTEST', 'ALLOWTEST', '1*10', '100:0', 1000, 100, 'B', '')", (D(15),))   # 1 % of 1000 = 10 = 1:0
for d, u in ((D(45), 1000), (D(20), 500)):                              # ALLOW-PT: 1500 sold since its count of D-60 -> 15 = 1:5 (since D-39 it would be 1:0)
    s.execute("INSERT INTO sp_sale_line VALUES (?, 'S2', 1, 'ALLOW-PT', 'ALLOW-PT', '1*10', 'x', ?, 100, 'B', '')", (d, u))
s.execute("INSERT INTO sp_move VALUES ('NORTEST TAB', ?, 'SALE', -14, 'A1')", (D(5),))
for n in (5, 3, 2):                                                      # 100 + AD00010's 90 - 14 sold = 176; two quiet days after
    s.execute("INSERT INTO sp_close VALUES (?, 'NORTEST TAB', 176, 'm')", (D(n),))
s.commit(); s.close()
# ---------------------------------------------------------------- the made-up finance database
f = sqlite3.connect(DB)
f.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
SW.ensure(f); SR.ensure(f)
import marg_hand_change as H
H.ensure(f)
f.execute("CREATE TABLE stock_voucher_entered (id INTEGER PRIMARY KEY, count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at)")
f.execute("CREATE TABLE stock_voucher_line (id INTEGER PRIMARY KEY, count_id, round_no, kind, batch_no, batches_n, line_no, section, family, item, packing, "
          "pack, marg_from, change, marg_to, counted, rate_p, value_p, reason, made_by, made_at)")
f.execute("CREATE TABLE amir_job (id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, text_hi TEXT, sub_hi TEXT, "
          "created_at TEXT NOT NULL, created_by TEXT, show_from TEXT, said_at TEXT, said_by TEXT, said_what TEXT, done_at TEXT, done_how TEXT, reopened_at TEXT)")
f.execute("CREATE TABLE stock_batch_fix (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, k20 TEXT NOT NULL, item TEXT NOT NULL, pack INTEGER NOT NULL, minus_batch TEXT NOT NULL, "
          "units INTEGER NOT NULL, issue_batch TEXT NOT NULL, issue_printed INTEGER, issue_expiry TEXT, asked_run_id INTEGER NOT NULL, asked_md5 TEXT, asked_day TEXT, "
          "asked_at TEXT NOT NULL, status TEXT NOT NULL, judged_run_id INTEGER, judged_md5 TEXT, judged_at TEXT, done_at TEXT, note TEXT)")
# the old count's line of KTTEST DT (06-Sep shape), Amir's two taps of it and the re-ask after the done tap (F-1706)
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,pack,change,made_at) VALUES (1,2,'ISSUE',8,'KTTEST DT',15,-101,?)", (D(50) + "T12:59:13",))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('fix:S569:KTTEST DT','tap','KTTEST DT','KTTEST DT — Marg mein STOCK ISSUE kijiye: 6 patte + 11 goli',?,?)",
          (D(40) + " 10:57:18", D(38) + " 09:23:17"))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('S829:kttest:lot3','tap','KTTEST DT','KTTEST DT — STOCK ISSUE 6:11 (strip:tab) Marg mein daaliye',?,?)",
          (D(13) + " 10:18:37", D(8) + " 09:29:29"))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('S957:kttest:7-11','tap','KTTEST DT','KTTEST DT — Marg mein STOCK ISSUE kijiye: 7 patte + 11 goli',?,NULL)",
          (D(1) + " 09:44:07",))
# the control twin: asked, tapped done, never asked again -> 'not in Marg'
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,pack,change,made_at) VALUES (1,2,'ISSUE',8,'OLDTEST',10,-5,?)", (D(50) + "T12:59:13",))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('S829:oldtest:lot3','tap','OLDTEST','OLDTEST — STOCK ISSUE 0:5 (strip:tab) Marg mein daaliye',?,?)",
          (D(13) + " 10:18:37", D(8) + " 09:29:29"))
# a held item, said done and never in Marg
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,pack,change,made_at) VALUES (1,2,'ISSUE',8,'VINBACTUM DS',1,-25,?)", (D(50) + "T12:59:13",))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,done_at) VALUES ('fix:S569:VINBACTUM DS','tap','VINBACTUM DS','VINBACTUM DS — Marg mein STOCK ISSUE kijiye: 25 nag',?,?)",
          (D(40) + " 10:57:18", D(38) + " 09:23:17"))
# a wrong-batch fix of AGREETEST keyed from the wrong batch (whole item agrees -> settled; the batch part stays with the Expiry watch)
f.execute("INSERT INTO stock_batch_fix (kind,k20,item,pack,minus_batch,units,issue_batch,asked_run_id,asked_day,asked_at,status) "
          "VALUES ('batch','AGREETEST','AGREETEST',10,'B1',6,'B2',1,?,?,'open')", (D(20), D(20)))
# an open batch fix of ALLOWTEST, waiting (box 2)
f.execute("INSERT INTO stock_batch_fix (kind,k20,item,pack,minus_batch,units,issue_batch,asked_run_id,asked_day,asked_at,status) "
          "VALUES ('batch','ALLOWTEST','ALLOWTEST',10,'Z1',3,'Z2',1,?,?,'open')", (D(3), D(3)))
f.execute("CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER, packing TEXT, pack_size INTEGER, loaded_at TEXT, source TEXT, PRIMARY KEY (as_on, item))")
for n, p, _u in ITEMS:
    f.execute("INSERT INTO stock_snapshot VALUES (?,?,1,?,1,'x','x')", (dmy(D(1)), n, p))
MV.ensure(f); MV._migrate(f)
f.execute("INSERT INTO mi_voucher_file (md5,kind,date_from,date_to,n_vouchers,n_lines,gross_p,bill_p,ok,note,stored_at,seq,exported) "
          "VALUES ('mI','ISSUE',?,?,0,0,0,0,1,'','x',1,?)", (D(58), D(1), D(1).replace('-', '') + '-145500'))
f.execute("INSERT INTO mi_voucher_file (md5,kind,date_from,date_to,n_vouchers,n_lines,gross_p,bill_p,ok,note,stored_at,seq,exported) "
          "VALUES ('mR','RECEIVE',?,?,0,0,0,0,1,'','x',2,?)", (D(58), D(1), D(1).replace('-', '') + '-145500'))
LINES = [("mR", "RECEIVE", "AD00002", 1, D(19), "AGREETEST", "B1", 6),       # the receive half asked
         ("mI", "ISSUE", "L000032", 1, D(19), "AGREETEST", "B9", 6),        # the issue half: the wrong batch
         ("mR", "RECEIVE", "AD00010", 1, D(30), "NORTEST TAB", "24006", 90),  # nobody asked
         ("mI", "ISSUE", "L000031", 1, D(30), "SHOETEST L", "1", 1)]          # nobody asked, an item whose shelf is only the old count
for md5, kind, no, n, day, item, batch, u in LINES:
    f.execute("INSERT OR IGNORE INTO mi_voucher (md5,kind,no,day,cash,gross_p,bill_p,n_lines) VALUES (?,?,?,?,1,0,0,1)", (md5, kind, no, day))
    f.execute("INSERT INTO mi_voucher_line (md5,kind,no,n,day,item,packing,per,batch,qty,units,unit,expiry,rate_p,value_p) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (md5, kind, no, n, day, item, "1*10", 10 if item != "SHOETEST L" else 1, batch, str(u), u, "TAB", "", 100, 100 * u))
# the counts (stock_point) -- each record row stands on one
PTS = [("NORTEST TAB", D(4) + "T10:23:46", 2, 62, -60, "darpan", "settled", "6:0 below Marg -- a loss since the last count"),
       ("ALLOWTEST", D(9) + "T11:24:08", 197, 205, -8, "spot", "settled", "0:8 below Marg -- within the allowance"),
       ("KTTEST DT", D(4) + "T10:18:40", 299, 314, -15, "darpan", "settled", "Marg still holds the older loss of 06-09 (6:11) not yet written off -- not a new loss"),
       ("EVETEST", D(0) + "T18:10:00", 50, None, None, "darpan", "awaits_sales", ""),
       ("GONETEST", D(9) + "T10:59:32", 206, 359, -153, "spot", "settled", "15:3 below Marg -- a loss since the last count"),
       ("SURPTEST", D(6) + "T10:54:05", 282, 268, 14, "spot", "settled", "1:4 more than Marg -- noted, never a loss"),
       ("PANTEST 40", D(4) + "T10:42:46", 442, 462, -20, "spot", "settled", "below Marg by about a delivery -- bill 4100 (A, 05-11: 2:0) may not have been on the shelf; count again"),
       ("PANTEST 40", D(12) + "T10:00:00", 300, 300, 0, "spot", "superseded", "matches Marg"),
       ("OLDTEST", D(82) + "T10:00:00", 30, 35, -5, "full_count", "settled", ""),
       ("ALLOW-PT", D(60) + "T10:00:00", 300, 300, 0, "full_count", "settled", ""),
       ("ALLOW-PT", D(9) + "T11:00:00", 290, 298, -8, "spot", "settled", "0:8 below Marg -- within the allowance"),
       ("KEPTTEST", D(5) + "T11:00:00", 50, None, None, "spot", "settled", "no Marg print for that day -- counted and kept"),
       ("TWOTEST", D(3) + "T10:00:00", 50, 70, -20, "darpan", "settled", "2:0 below Marg -- a loss since the last count")]
if "judge_words" not in {r[1] for r in f.execute("PRAGMA table_info(stock_point)")}:   # S952's column, as on the box
    f.execute("ALTER TABLE stock_point ADD COLUMN judge_words TEXT")
for it, at, q, e, g, src, stt, w in PTS:
    f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
              (SW.norm_name(it), it, at, q, src, "darpan", e, g, stt, w))
# the stock of record (made-up rows in its own table)
REC = [("NORTEST TAB", 10, 62, 2, -60, "darpan", D(4), D(4) + "T10:23:46", "look", ""),
       ("ALLOWTEST", 10, 175, 167, -8, "spot", D(9), D(9) + "T11:24:08", "look", ""),
       ("KTTEST DT", 15, 415, 299, -116, "darpan", D(4), D(4) + "T10:18:40", "look", ""),
       ("EVETEST", 10, 60, 50, -10, "darpan", D(0), D(0) + "T18:10:00", "look", ""),
       ("GONETEST", 10, 206, 206, 0, "spot", D(9), D(9) + "T10:59:32", "agree", ""),
       ("SURPTEST", 10, 268, 282, 14, "spot", D(6), D(6) + "T10:54:05", "look", ""),
       ("PANTEST 40", 10, 462, 442, -20, "spot", D(4), D(4) + "T10:42:46", "look", ""),
       ("OLDTEST", 10, 40, 35, -5, "count", D(82), D(82) + "T10:00:00", "look", "old_base"),
       ("AGREETEST", 10, 132, 132, 0, "count", D(82), D(82) + "T10:00:00", "agree", "old_base"),
       ("SHOETEST L", 1, 1, 2, 1, "count", D(82), D(82) + "T10:00:00", "look", "old_base"),
       ("VINBACTUM DS", 1, 25, 0, -25, "count", D(82), D(82) + "T10:00:00", "consumable", "old_base"),
       ("ALLOW-PT", 10, 298, 290, -8, "spot", D(9), D(9) + "T11:00:00", "look", ""),
       ("KEPTTEST", 10, 55, 50, -5, "spot", D(5), D(5) + "T11:00:00", "look", ""),
       ("TWOTEST", 10, 70, 50, -20, "darpan", D(3), D(3) + "T10:00:00", "look", ""),
       ("RECTEST", 10, 40, 37, -3, "count", D(82), D(82) + "T10:00:00", "look", "old_base"),
       ("ONLISTTEST", 10, 40, 42, 2, "count", D(82), D(82) + "T10:00:00", "look", "old_base")]
for it, pk, m, sh, g, bk, bd, ba, stt, fl in REC:
    f.execute("INSERT INTO stock_of_record (item,k20,pack,marg_units,shelf_units,gap_units,base_kind,base_day,base_at,state,marg_flag,words,forms_json,built_at) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (it, it[:20], pk, m, sh, g, bk, bd, ba, stt, fl, "", "[]", dt.datetime.now().isoformat()))
f.commit()
# ================================================================ S969 · kit A2: the desk's writes
import amir_day as AD
DAYI = T.isoformat()
f.execute("CREATE TABLE IF NOT EXISTS stock_batch_now (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL, at TEXT, as_on TEXT, sales_after TEXT, sales_to TEXT, "
          "k20 TEXT NOT NULL, item TEXT, batch TEXT, expiry TEXT, units INTEGER, printed INTEGER, sold INTEGER, bought INTEGER, new INTEGER, pack INTEGER, packing TEXT)")
for run, b, e, u in ((7, "OLDRUN", "2026-01", 500), (9, "B-NEW", "2027-04", 100), (9, "B-OLD", "2026-12", 30), (9, "B-ZERO", "2026-06", 0)):
    f.execute("INSERT INTO stock_batch_now (run_id, as_on, k20, item, batch, expiry, units, pack) VALUES (?,?,?,?,?,?,?,10)", (run, D(4), "NORTEST TAB", "NORTEST TAB", b, e, u))
f.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at, mode) VALUES (?,?,?,?,?)", (SW.norm_name("ONLISTTEST"), "ONLISTTEST", "manoj", D(2) + "T09:00:00", "next"))
if "audit_log" not in {r[0] for r in f.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
    f.execute("CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT, row_id INTEGER, action TEXT, before_json TEXT, after_json TEXT, by_whom TEXT, at TEXT)")
f.commit()
PUSH = os.path.join(W, "push.jsonl"); os.environ["ORDER_PUSH_STUB"] = PUSH
T0 = f.total_changes
K = SC.desk(f, DAYI)
b1 = {r["item"]: r for r in K["box1"]}; al = {r["item"]: r for r in K["allow"]}; rc = {r["item"]: r for r in K["recount"]}
ok("A1 box 1 offers Write off + Pursue on a fresh loss, Pursue only on 'about a delivery', nothing on an evening count waiting for its sales",
   b1.get("NORTEST TAB", {}).get("acts") == ["wo", "pu"] and b1.get("TWOTEST", {}).get("acts") == ["wo", "pu"] and b1.get("PANTEST 40", {}).get("acts") == ["pu"]
   and b1.get("EVETEST", {}).get("acts") == [], {k: r.get("acts") for k, r in b1.items()})
ok("A2 the allowance rows are the group button's (wo_ok); no per-row button", al and all(r.get("wo_ok") and not r.get("acts") for r in al.values()), {k: (r.get("wo_ok"), r.get("acts")) for k, r in al.items()})
ok("A3 F-1712: an old count that differs from Marg -> 'Count first' with Next list; one already on his list says so, no button; items of boxes 3/4 not repeated",
   rc.get("RECTEST", {}).get("acts") == ["nl"] and rc.get("ONLISTTEST", {}).get("acts") == [] and rc["ONLISTTEST"]["on_list"] == dmy(D(2))
   and "OLDTEST" not in rc and "SHOETEST L" not in rc and K["totals"]["recount"] == 2, {k: (r.get("acts"), r.get("on_list")) for k, r in rc.items()})
ok("A4 the desk still writes nothing", f.total_changes == T0, f.total_changes - T0)
# ---- the doors
import flask
app = flask.Flask("w969"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None) if "checker" in r else (None, ("no", 403)))
c = app.test_client()


def act(**b):
    r = c.post("/finance/stockcheck/api/desk/act", json=b)
    return r.status_code, (r.get_json() or {})


def jobs(like):
    return f.execute("SELECT key, subject, text_hi, sub_hi, done_at, show_from FROM amir_job WHERE key LIKE ? ORDER BY id", (like,)).fetchall()


s, j = act(act="writeoff", item="NORTEST TAB")
J1 = jobs("S969:wo:%")
ok("W1 Write off: one Amir card line, kind tap, the S957 word shape, the day's card 1", s == 200 and j.get("ok") and len(J1) == 1
   and J1[0][0] == "S969:wo:%s:1:NORTEST-TAB" % DAYI and J1[0][2] == "NORTEST TAB — Marg mein STOCK ISSUE kijiye: 6 patte" and J1[0][5], (s, j, J1))
ok("W2 the batch only suggested, from the NEWEST Batch Stock run, nearest expiry first, until covered (30 < 60 -> two), the zero batch never",
   J1 and "B-OLD, phir B-NEW" in (J1[0][3] or "") and "OLDRUN" not in (J1[0][3] or "") and "B-ZERO" not in (J1[0][3] or ""), J1 and J1[0][3])
da = f.execute("SELECT kind, pack, units, point_id, batch, box, by FROM stock_desk_action WHERE item='NORTEST TAB'").fetchall()
ok("W3 the desk's own row: pack 10, units 60, the count it acts on, by him", da == [("writeoff", 10, 60, da[0][3] if da else None, "B-OLD, phir B-NEW", "short", "manoj")] and da[0][3], da)
JJ = V.judge(f, DAYI)
nt = [a for a in JJ["asks"] if a["item"] == "NORTEST TAB" and a["src"] == "job"]
ok("W4 the voucher judge reads it from the desk's row: Issue 60 units (never '6 patte' read with a guessed pack of 1), waiting", nt and nt[0]["units"] == 60
   and nt[0]["kind"] == "ISSUE" and nt[0]["state"] in V.WAY_STATES, [(a["units"], a["state"]) for a in nt])
K2 = SC.desk(f, DAYI)
ok("W5 the row leaves box 1 for box 2 'already asked of Amir'", "NORTEST TAB" not in {r["item"] for r in K2["box1"]}
   and any(r["item"] == "NORTEST TAB" and any("already asked" in t[1] for t in r["tags"]) for r in K2["way"]), [r["item"] for r in K2["way"]])
n0 = f.total_changes
s2, j2 = act(act="writeoff", item="NORTEST TAB")
ok("W6 a second tap (or a stale page) writes nothing", s2 == 409 and not j2.get("ok") and f.total_changes == n0 and len(jobs("S969:wo:%")) == 1, (s2, j2))
s3, j3 = act(act="writeoff", item="TWOTEST")
s4, j4 = act(act="allow", items=["ALLOWTEST", "ALLOW-PT", "NOT ON THE DESK"])
c1 = jobs("S969:wo:%s:1:%%" % DAYI)
ok("W7 the day's other write-offs ride the SAME card (one voucher): 4 lines on card 1; an item not in the allowance box is not written",
   s3 == 200 and s4 == 200 and len(c1) == 4 and {x[1] for x in c1} == {"NORTEST TAB", "TWOTEST", "ALLOWTEST", "ALLOW-PT"}, (s3, j3, s4, j4, [x[0] for x in c1]))
ok("W8 the allowance words: 0:8 -> '8 goli'", any(x[1] == "ALLOWTEST" and x[2].endswith("kijiye: 8 goli") for x in c1), [x[2] for x in c1])
s5, j5 = act(act="writeoff", item="EVETEST")
ok("W9 an evening count waiting for its sales: no Write off is taken", s5 == 409 and not jobs("S969:wo:%%:EVETEST%%"), (s5, j5))
s6, j6 = act(act="writeoff", item="PANTEST 40")
ok("W10 'about a delivery': Write off refused (Pursue only)", s6 == 409, (s6, j6))
# ---- Amir's card: one card, one Kar diya
RD = AD._s494_read(f)
html = "".join(AD._s494_lines(RD["jobs"]))
ok("A5 Amir's card: ONE Stock Issue card listing the four, one 'Kar diya' for the card (tapg), the batch line under its item, no per-item buttons",
   html.count("tapg:%s:1:" % DAYI) == 1 and html.count("Ek STOCK ISSUE voucher banaiye") == 1 and all(x in html for x in ("NORTEST TAB", "TWOTEST", "ALLOWTEST", "ALLOW-PT"))
   and "6 patte" in html and "B-OLD" in html and not any(("tap:%d'" % r["id"]) in html for r in RD["jobs"] if str(r["key"]).startswith("S969:")), html[:400])
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,show_from) VALUES ('S927:voucher:X:1','tap','OTHERJOB','OTHERJOB — ginti ka voucher Marg mein daaliye',?,?)",
          (D(0) + " 08:00:00", D(0) + " 08:00:00")); f.commit()
RD2 = AD._s494_read(f); h2 = "".join(AD._s494_lines(RD2["jobs"]))
oj = [r["id"] for r in RD2["jobs"] if r["key"] == "S927:voucher:X:1"]
ok("A6 his other one-time jobs keep their own line and own button; the write-off card stays one", oj and ("value='tap:%d'" % oj[0]) in h2 and h2.count("Ek STOCK ISSUE voucher banaiye") == 1, h2[:300])
f.execute("DELETE FROM amir_job WHERE key='S927:voucher:X:1'"); f.commit()
import re as _re
TV = _re.search(r"value='(tapg:[^']+)'", html).group(1)                 # the card as Amir's page drew it
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,show_from) VALUES (?,?,?,?,?,?)",   # the owner's write-off lands after the page was drawn
          ("S969:wo:%s:1:LATETEST" % DAYI, "tap", "LATETEST", "LATETEST — Marg mein STOCK ISSUE kijiye: 1 patte", D(0) + " 09:59:00", D(0) + " 09:59:00")); f.commit()
nd = AD._s494_tap(f, "amir", TV)
lt = [x for x in jobs("S969:wo:%s:1:%%" % DAYI) if x[1] == "LATETEST"]
ok("A7 one tap marks done every line of the card he SAW -- a line added after his page was drawn stays open (review 2)", nd == 4
   and all(x[4] for x in jobs("S969:wo:%s:1:%%" % DAYI) if x[1] != "LATETEST") and lt and not lt[0][4], (nd, TV, lt))
h3 = "".join(AD._s494_lines(AD._s494_read(f)["jobs"]))
ok("A7b the line he did not see comes back as its own card, its own Kar diya", h3.count("Ek STOCK ISSUE voucher banaiye") == 1 and "LATETEST" in h3 and "NORTEST TAB" not in h3, h3[:300])
ok("A8 a tap of a card already done changes nothing; a made-up card number nothing; the old two-part value nothing", AD._s494_tap(f, "amir", TV) == 0
   and AD._s494_tap(f, "amir", "tapg:%s:9:999999" % DAYI) == 0 and AD._s494_tap(f, "amir", "tapg:%s:1" % DAYI) == 0)
f.execute("UPDATE amir_job SET done_at=?, said_at=?, done_how='tap' WHERE key=?", (D(0) + " 10:30:00", D(0) + " 10:30:00", "S969:wo:%s:1:LATETEST" % DAYI)); f.commit()
nb = f.total_changes
m3, s3_ = SC._write_off(f, [dict(item="NORTEST TAB", short=60, pack=10, pid=da[0][3], key="NORTEST TAB")], "manoj", "short")
ok("A9 one write-off per count, ever: the same count once its card is done is never written again (review 3)", m3 == [] and s3_ == ["NORTEST TAB"], (m3, s3_))
fl = sqlite3.connect(":memory:"); f.backup(fl)                           # second look 1: a NEW count, the done write-off not yet in Marg
fl.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
           (SW.norm_name("ALLOWTEST"), "ALLOWTEST", D(0) + "T09:30:00", 165, "darpan", "darpan", 175, -10, "settled", "1:0 below Marg -- within the allowance"))
fl.execute("UPDATE stock_of_record SET base_at=?, base_day=?, shelf_units=165, gap_units=-10 WHERE item='ALLOWTEST'", (D(0) + "T09:30:00", D(0))); fl.commit()
Kl = SC.desk(fl, DAYI)
ok("S1 his write-off done by Amir and not yet in Marg: a newer count of the item is NOT offered again (second look 1)", "ALLOWTEST" not in {r["item"] for r in Kl["allow"] + Kl["box1"]}
   and any(r["item"] == "ALLOWTEST" and any("already asked" in x[1] for x in r["tags"]) for r in Kl["way"]), [(r["item"], r["box"]) for r in Kl["allow"] + Kl["box1"] + Kl["way"]])
fm = sqlite3.connect(":memory:"); f.backup(fm)                           # second look 4: in Marg's report, the record not yet rebuilt
fm.execute("INSERT INTO mi_voucher (md5,kind,no,day,cash,gross_p,bill_p,n_lines) VALUES ('mI','ISSUE','L000099',?,1,0,0,1)", (D(0),))
fm.execute("INSERT INTO mi_voucher_line (md5,kind,no,n,day,item,packing,per,batch,qty,units,unit,expiry,rate_p,value_p) VALUES ('mI','ISSUE','L000099',1,?,'TWOTEST','1*10',10,'X','20',20,'TAB','',100,2000)", (D(0),))
fm.execute("UPDATE mi_voucher_file SET date_to=?, exported=? WHERE md5='mI'", (D(0), D(0).replace("-", "") + "-235500")); fm.commit()
st2 = [a["state"] for a in V.judge(fm, DAYI)["asks"] if a["item"] == "TWOTEST" and str(a.get("ref", "")).startswith("S969:")]
Km = SC.desk(fm, DAYI)
tw = [r for r in Km["box1"] + Km["way"] if r["item"] == "TWOTEST"]
ok("S4 written off and in Marg's report, the record not yet: 'Marg's figure catches up', no button (second look 4)", st2 == ["in_marg"] and tw and tw[0]["box"] == "way"
   and not tw[0].get("acts") and any("catches up" in x[1] for x in tw[0]["tags"]), (st2, tw and (tw[0]["box"], tw[0]["tags"])))
fg = sqlite3.connect(":memory:"); f.backup(fg)                           # re-look: a later count agrees with Marg while his write-off is unkeyed
fg.execute("UPDATE amir_job SET done_at=NULL, said_at=NULL WHERE key LIKE 'S969:wo:%:TWOTEST'")
fg.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
           (SW.norm_name("TWOTEST"), "TWOTEST", D(0) + "T09:40:00", 70, "darpan", "darpan", 70, 0, "settled", "matches Marg"))
fg.execute("UPDATE stock_of_record SET base_at=?, base_day=?, shelf_units=70, gap_units=0, state='agree' WHERE item='TWOTEST'", (D(0) + "T09:40:00", D(0))); fg.commit()
Kg = SC.desk(fg, DAYI)
tg_ = [r for r in Kg["way"] if r["item"] == "TWOTEST"]
ok("S5 a later count agrees with Marg while his write-off is unkeyed: red 'not to be keyed' in box 2, never quietly Settled (re-look)", tg_ and tg_[0]["tags"][0][0] == "red"
   and "TWOTEST" not in {r["item"] for r in Kg["settled"]}, tg_ and tg_[0]["tags"])
# a new short after the card is done -> card 2 (a done card never grows)
f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
          (SW.norm_name("KEPTTEST"), "KEPTTEST", D(0) + "T09:00:00", 45, "darpan", "darpan", 55, -10, "settled", "1:0 below Marg -- a loss since the last count"))
f.execute("UPDATE stock_of_record SET base_kind='darpan', base_day=?, base_at=?, shelf_units=45, gap_units=-10 WHERE item='KEPTTEST'", (D(0), D(0) + "T09:00:00")); f.commit()
_jg = V.judge
V.judge = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("made-up judge fault"))
sj, jj = act(act="writeoff", item="KEPTTEST")
V.judge = _jg
ok("W10b the voucher judge cannot run: every write refused, nothing written (review 3)", sj == 409 and not jobs("S969:wo:%%KEPTTEST%%"), (sj, jj))
s7, j7 = act(act="writeoff", item="KEPTTEST")
ok("W11 a card Amir has tapped done never grows: the next write-off opens card 2", s7 == 200 and len(jobs("S969:wo:%s:1:%%" % DAYI)) == 5
   and [x[1] for x in jobs("S969:wo:%s:2:%%" % DAYI)] == ["KEPTTEST"], (s7, j7))
# ---- Pursue and its end rule
s8, j8 = act(act="pursue", item="PANTEST 40")
ak = f.execute("SELECT id, mode, done_at FROM stock_watch_ask WHERE item='PANTEST 40'").fetchall()
pa = f.execute("SELECT point_id, ask_id, units FROM stock_desk_action WHERE kind='pursue' AND item='PANTEST 40'").fetchall()
ok("P1 Pursue: one ask at the head of Darpan's next list, kept with the count it questions", s8 == 200 and j8.get("ok") and len(ak) == 1 and ak[0][1] == "next"
   and not ak[0][2] and pa and pa[0][1] == ak[0][0] and pa[0][0] and pa[0][2] == 20, (s8, j8, ak, pa))
pn = SW.preview_roster(f, T + dt.timedelta(days=1), None, SW.Spine())
ok("P2 the recount is on Darpan's next morning list", any(x["item"] == "PANTEST 40" for x in pn), pn)
K3 = SC.desk(f, DAYI)
pr = [r for r in K3["box1"] if r["item"] == "PANTEST 40"]
ok("P3 the pursued row stays in box 1, tagged, no buttons until the recount", pr and pr[0]["acts"] == [] and any("Pursue" in t[1] for t in pr[0]["tags"]), pr and pr[0]["tags"])
fw = sqlite3.connect(":memory:"); f.backup(fw)
fw.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='withdrawn' WHERE item='PANTEST 40'", (D(0) + "T11:00:00",)); fw.commit()
pw = [r for r in SC.desk(fw, DAYI)["box1"] if r["item"] == "PANTEST 40"]
ok("P3b his Pursue's ask withdrawn, no count since: the button comes back (review 5)", pw and pw[0]["acts"] == ["pu"], pw and (pw[0]["acts"], pw[0]["tags"]))
pp = f.execute("SELECT point_id FROM stock_desk_action WHERE kind='pursue' AND item='PANTEST 40'").fetchone()[0]
fc_ = sqlite3.connect(":memory:"); f.backup(fc_)                         # second look 2: Darpan corrects the pursued count ('Galat likha? Badlo')
nid = fc_.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (SW.norm_name("PANTEST 40"), "PANTEST 40", D(0) + "T23:50:00", 441, "spot", "darpan", 462, -21, "settled", "2:1 below Marg -- a loss since the last count")).lastrowid
fc_.execute("UPDATE stock_point SET status='superseded', note='S502: badla, ab point %d' WHERE id=?" % nid, (pp,))
fc_.execute("UPDATE stock_of_record SET base_at=?, base_day=?, shelf_units=441, gap_units=-21 WHERE item='PANTEST 40'", (D(0) + "T23:50:00", D(0))); fc_.commit()
pc = [r for r in SC.desk(fc_, DAYI)["box1"] if r["item"] == "PANTEST 40"]
ok("S2 a correction of the pursued count is not its recount: still 'Pursue — on Darpan's list', no button (second look 2)", pc and pc[0]["acts"] == []
   and any("Pursue" in x[1] for x in pc[0]["tags"]) and not any(x[1] == "recounted" for x in pc[0]["tags"]), pc and pc[0]["tags"])
fh = sqlite3.connect(":memory:"); f.backup(fh)                           # second look 3: a recount S936 holds is never the answer
fh.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
           (SW.norm_name("PANTEST 40"), "PANTEST 40", D(0) + "T23:50:00", 400, "spot", "darpan", 462, -62, "recount", "")); fh.commit()
ph = [r for r in SC.desk(fh, DAYI)["box1"] if r["item"] == "PANTEST 40"]
ok("S3 a held recount (S936) does not answer the Pursue: still waiting, never 'catches up' (second look 3)", ph and any("Pursue" in x[1] for x in ph[0]["tags"])
   and not any("catches up" in x[1] for x in ph[0]["tags"]), ph and ph[0]["tags"])
s9, j9 = act(act="pursue", item="PANTEST 40")
ok("P4 a second Pursue tap writes nothing", s9 == 409 and len(f.execute("SELECT 1 FROM stock_watch_ask WHERE item='PANTEST 40'").fetchall()) == 1, (s9, j9))
RT = D(0) + "T23:58:00"                                                  # the recount, after his Pursue
f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
          (SW.norm_name("PANTEST 40"), "PANTEST 40", RT, 440, "spot", "darpan", 462, -22, "settled", "2:2 below Marg -- a loss since the last count")); f.commit()
K4 = SC.desk(f, DAYI)
pr = [r for r in K4["box1"] if r["item"] == "PANTEST 40"]
ok("P5 counted, the record not built on it yet: 'the record catches up', still no button", pr and pr[0]["acts"] == [] and any("catches up" in t[1] for t in pr[0]["tags"]), pr and pr[0]["tags"])
fs = sqlite3.connect(":memory:"); f.backup(fs)                           # way 1: the recount still short -> box 1 with both counts
fs.execute("UPDATE stock_of_record SET base_at=?, base_day=?, shelf_units=440, gap_units=-22 WHERE item='PANTEST 40'", (RT, RT[:10])); fs.commit()
pr = [r for r in SC.desk(fs, DAYI)["box1"] if r["item"] == "PANTEST 40"]
ok("P6 the recount still short: back in box 1 with BOTH counts, Write off and Pursue again", pr and pr[0]["acts"] == ["wo", "pu"] and any(t[1] == "recounted" for t in pr[0]["tags"])
   and any("First count" in p[1] for p in pr[0]["path"]) and any("Darpan's recount" in p[1] for p in pr[0]["path"]), pr and (pr[0]["acts"], pr[0]["path"]))
LT = D(0) + "T23:59:30"                                                  # a later count after the recount: the Pursue is history (review 4)
fs.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
           (SW.norm_name("PANTEST 40"), "PANTEST 40", LT, 438, "darpan", "darpan", 462, -24, "settled", "2:4 below Marg -- a loss since the last count"))
fs.execute("UPDATE stock_of_record SET base_at=?, base_day=?, shelf_units=438, gap_units=-24 WHERE item='PANTEST 40'", (LT, LT[:10])); fs.commit()
pr = [r for r in SC.desk(fs, DAYI)["box1"] if r["item"] == "PANTEST 40"]
ok("P6b a count later than the first one after his Pursue reads as any count: no 'recounted', no old story", pr and pr[0]["acts"] == ["wo", "pu"]
   and not any(t[1] == "recounted" for t in pr[0]["tags"]) and not any("First count" in p[1] for p in pr[0]["path"]), pr and (pr[0]["tags"], pr[0]["path"][:2]))
fa = sqlite3.connect(":memory:"); f.backup(fa)                           # way 2: the recount agrees with Marg -> closed by itself
fa.execute("UPDATE stock_point SET qty_units=462, gap_units=0, judge_words='matches Marg' WHERE at=? AND item='PANTEST 40'", (RT,))
fa.execute("UPDATE stock_of_record SET base_at=?, base_day=?, shelf_units=462, gap_units=0, state='agree' WHERE item='PANTEST 40'", (RT, RT[:10])); fa.commit()
Ka = SC.desk(fa, DAYI)
ok("P7 the recount agrees with Marg: closed by itself as a count error (Settled), nothing to write off", "PANTEST 40" not in {r["item"] for r in Ka["box1"]}
   and any(r["item"] == "PANTEST 40" and any("count error" in p[1] for p in r["path"]) for r in Ka["settled"]), [r["item"] for r in Ka["settled"]])
# ---- F-1712: next list
s10, j10 = act(act="nextlist", item="RECTEST")
ok("N1 Next list: the old count's item at the head of Darpan's next list; the row then says so", s10 == 200 and f.execute("SELECT mode FROM stock_watch_ask WHERE item='RECTEST' AND done_at IS NULL").fetchall() == [("next",)]
   and [r for r in SC.desk(f, DAYI)["recount"] if r["item"] == "RECTEST"][0]["acts"] == [], (s10, j10))
s11, j11 = act(act="nextlist", items=["RECTEST", "ONLISTTEST"])
ok("N2 the group button writes only rows still offering it (none left)", s11 == 409, (s11, j11))
# ---- roles, the GET doors, the page
app2 = flask.Flask("w969b"); SC.init(app2, lambda: f, lambda *r: (({"user": "bhati"}, None) if ("maker" in r or "viewer" in r) and "checker" not in r else (None, ("no", 403))))
n1 = f.total_changes
r12 = app2.test_client().post("/finance/stockcheck/api/desk/act", json={"act": "writeoff", "item": "TWOTEST"})
ok("R1 only the owner (checker) writes from the desk", r12.status_code == 403 and f.total_changes == n1, r12.status_code)
SC._DCACHE["v"] = None
app3 = flask.Flask("w969v"); SC.init(app3, lambda: f, lambda *r: ({"user": "viewer"}, None) if "viewer" in r else (None, ("no", 403)))
ok("S6 the desk tells the page who may write: a viewer gets no buttons drawn (second look 6)", (app3.test_client().get("/finance/stockcheck/api/desk?fresh=1").get_json() or {}).get("can_write") is False)
app = flask.Flask("w969c"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None) if "checker" in r else (None, ("no", 403)))   # init sets the module's door again
c = app.test_client()
SC._DCACHE["v"] = None
c.get("/finance/stockcheck/api/desk?fresh=1"); c.get("/finance/stockcheck/api/rows")
ok("R2 the GET doors still write nothing", f.total_changes == n1, f.total_changes - n1)
hz = c.get("/finance/stockcheck/api/healthz").get_json()
ok("R3 healthz v1.7 with writes", hz.get("version") == "1.7" and hz.get("writes") and hz.get("kit_desk") == "S969_STOCKCHECK_DESK_WRITES", hz)
ok("S6b the owner's desk says he may write", c.get("/finance/stockcheck/api/desk").get_json().get("can_write") is True)
pg = c.get("/finance/stockcheck/").get_data(as_text=True)
ok("R4 the page: the buttons, two taps, no pop-up (no confirm/alert/prompt anywhere)", "function deskAct" in pg and "Tap again" in pg and "/api/desk/act" in pg
   and "confirm(" not in pg and "alert(" not in pg and "prompt(" not in pg and 'id="dk6"' in pg, [x for x in ("function deskAct", "Tap again", "/api/desk/act", 'id="dk6"') if x not in pg] + [x for x in ("confirm(", "alert(", "prompt(") if x in pg])
r5a, r5b = act(act="burn", item="X"), act(act="writeoff")
ok("R5 the unknown button and an empty body answer 400 / 409, nothing written", r5a[0] == 400 and r5b[0] == 409 and f.total_changes == n1, (r5a, r5b, f.total_changes - n1))
# ---- the morning list's push (F-1712), on a copy
fp = sqlite3.connect(":memory:"); f.backup(fp)
fp.execute("UPDATE stock_watch_ask SET done_at='x' WHERE done_at IS NULL")
fp.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('spot.days', 'MON,TUE,WED,THU,FRI,SAT,SUN')")
fp.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,1,?,10,'1*10',0)",
           (D(1), SW.norm_name("RECTEST"), "RECTEST", "x", "x", D(1))); fp.commit()
open(PUSH, "w").close()
SW.build_roster(fp, day=T, who="walk")
pl = [json.loads(x) for x in open(PUSH, encoding="utf-8") if x.strip()]
ok("M1 a spot morning's list (no ask of his on it) reaches Darpan's phone: one push naming the items", len(pl) == 1 and pl[0]["user"] == "darpan"
   and "RECTEST" in pl[0]["payload"]["body"] and pl[0]["payload"]["url"] == "/finance/stockmatch", pl)
fq = sqlite3.connect(":memory:"); f.backup(fq)
fq.execute("UPDATE stock_watch_ask SET done_at='x' WHERE done_at IS NULL")
fq.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('spot.days', 'MON,TUE,WED,THU,FRI,SAT,SUN')")
fq.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('count.push_every_list', '0')")
fq.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,1,?,10,'1*10',0)",
           (D(1), SW.norm_name("RECTEST"), "RECTEST", "x", "x", D(1))); fq.commit()
open(PUSH, "w").close()
SW.build_roster(fq, day=T, who="walk")
ok("M2 the switch count.push_every_list = 0 keeps it quiet; a second build the same day pushes nothing", sum(1 for x in open(PUSH) if x.strip()) == 0)
open(PUSH, "w").close(); SW.build_roster(fp, day=T, who="walk")
ok("M3 the list is written once a day: a second build the same morning sends no second push", sum(1 for x in open(PUSH) if x.strip()) == 0)
CALLS = []
appm = flask.Flask("w969m"); SC.init(appm, lambda: CALLS.append(1) or (_ for _ in ()).throw(RuntimeError("Working outside of application context")), lambda *r: ({"user": "manoj"}, None))
ok("I1 the mount never opens the database (the live getter needs a request: review 1)", CALLS == [], CALLS)
print("WALK %d/%d" % (sum(RES), len(RES)))
