#!/usr/bin/env python3
"""walk_s967.py -- S967_STOCKCHECK_ONE_PAGE on MADE-UP data only (no real file is read): a small stock record, spine and finance database
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


W = tempfile.mkdtemp(prefix="walk967_")
SP, DB = os.path.join(W, "spine.db"), os.path.join(W, "finance.db")
os.environ["SPINE_DB"] = SP
T = dt.date.today()


def D(n):
    return (T - dt.timedelta(days=n)).isoformat()


def dmy(iso):
    return "%s-%s-%s" % (iso[8:10], iso[5:7], iso[:4])


import stock_check as SC
if not hasattr(SC, "desk"):                                              # the control: the live files have no one page
    ok("the one page's desk is in stock_check.py", False, "no desk()"); print("WALK %d/%d" % (sum(RES), len(RES))); sys.exit(0)
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
         ("KEPTTEST", "1*10", "LOOSE"))
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
       ("KEPTTEST", D(5) + "T11:00:00", 50, None, None, "spot", "settled", "no Marg print for that day -- counted and kept")]
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
       ("KEPTTEST", 10, 55, 50, -5, "spot", D(5), D(5) + "T11:00:00", "look", "")]
for it, pk, m, sh, g, bk, bd, ba, stt, fl in REC:
    f.execute("INSERT INTO stock_of_record (item,k20,pack,marg_units,shelf_units,gap_units,base_kind,base_day,base_at,state,marg_flag,words,forms_json,built_at) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (it, it[:20], pk, m, sh, g, bk, bd, ba, stt, fl, "", "[]", dt.datetime.now().isoformat()))
f.commit()
T0 = f.total_changes
# ---------------------------------------------------------------- 1 · F-1706
J = V.judge(f, T.isoformat())
kt = [a for a in J["asks"] if a["item"] == "KTTEST DT"]
ok("F1 F-1706: asked again on Amir's card after his done tap -> waiting again, never 'not in Marg' on the older tap",
   len(kt) == 1 and kt[0]["state"] == "waiting" and kt[0]["units"] == 116 and kt[0].get("reasked") == D(1), [(a["state"], a["units"], a.get("done_day"), a.get("reasked")) for a in kt])
ot = [a for a in J["asks"] if a["item"] == "OLDTEST"]
ok("F2 the twin never asked again keeps its done tap: 'not in Marg'", len(ot) == 1 and ot[0]["state"] == "not_in_marg", [(a["state"], a.get("done_day")) for a in ot])
f2 = sqlite3.connect(":memory:"); f.backup(f2)
f2.execute("UPDATE amir_job SET done_at=? WHERE key='S957:kttest:7-11'", (D(0) + " 08:00:00",)); f2.commit()
kt2 = [a for a in V.judge(f2, T.isoformat())["asks"] if a["item"] == "KTTEST DT"]
ok("F3 the re-ask tapped done in its turn: Amir's newest done mark stands (not in Marg, done today)", kt2 and kt2[0].get("done_day") == D(0) and not kt2[0].get("reasked") and kt2[0]["state"] in ("not_in_marg", "beyond"),
   [(a["state"], a.get("done_day")) for a in kt2])
f3 = sqlite3.connect(":memory:"); f.backup(f3)                           # review S4: an open re-ask with a lower id than a later done tap
f3.execute("UPDATE amir_job SET id=0 WHERE key='S957:kttest:7-11'")
f3.execute("INSERT INTO amir_job (id,key,kind,subject,text_hi,created_at,done_at) VALUES (100,'S829:kttest:lot4','tap','KTTEST DT','KTTEST DT — STOCK ISSUE 6:11 (strip:tab) Marg mein daaliye',?,?)",
           (D(5) + " 10:00:00", D(2) + " 09:29:29")); f3.commit()
kt3 = [a for a in V.judge(f3, T.isoformat())["asks"] if a["item"] == "KTTEST DT"]
ok("F4 decided on time, not on the order of ids: the open re-ask of D-1 is newer than the done tap of D-2 -> waiting", kt3 and kt3[0]["state"] == "waiting",
   [(a["state"], a.get("done_day"), a.get("reasked")) for a in kt3])
# ---------------------------------------------------------------- 2 · the whole-item re-judge
RJ = {e["item"]: e for e in V.rejudge(f, J)}
ok("R1 Marg = shelf -> settled by later entries; the batch part stays with the Expiry watch", RJ.get("AGREETEST", {}).get("verdict", {}).get("v") == "settled"
   and "Expiry watch" in RJ["AGREETEST"]["batch_note"] and RJ["AGREETEST"]["batch_only"], {k: e["verdict"]["v"] for k, e in RJ.items()})
ok("R2 a shelf only from the old count -> count first", RJ.get("OLDTEST", {}).get("verdict", {}).get("v") == "count_first", RJ.get("OLDTEST", {}).get("verdict"))
ok("R3 his held item -> held (D1077), never sent on", RJ.get("VINBACTUM DS", {}).get("verdict", {}).get("v") == "held")
ok("R4 a fresh count that still differs -> today's gap, in words with both figures", V.whole_item(V.record_rows(f)["NORTEST TAB"])["v"] == "fresh_gap"
   and "6:2" in V.whole_item(V.record_rows(f)["NORTEST TAB"])["word"])
ok("R5 the waiting ask is not an old card", "KTTEST DT" not in RJ)
# ---------------------------------------------------------------- 3 · the desk
K = SC.desk(f, T.isoformat())
b1 = {r["item"]: r for r in K["box1"]}; al = {r["item"]: r for r in K["allow"]}; wy = {r["item"]: r for r in K["way"]}
ol = {r["item"]: r for r in K["old"]}; se = {r["item"]: r for r in K["settled"]}
ok("D1 box 1: a fresh loss (NORTEST 6:0) with Marg, shelf and short", K["ok"] and "NORTEST TAB" in b1 and b1["NORTEST TAB"]["short_t"] == "6:0"
   and b1["NORTEST TAB"]["fig"] == "Marg 6:2 · shelf 0:2 · short 6:0", (K.get("reason"), list(b1)))
ok("D2 within the allowance -> the group, not box 1", "ALLOWTEST" in al and "ALLOWTEST" not in b1, (list(al), list(b1)))
ok("D2b the allowance the count's own judgment used is shown (1 % of 1000 sold since = 1:0, the spine read)", al.get("ALLOWTEST", {}).get("allowance_t") == "1:0"
   and any("(1:0)" in t[1] for t in al["ALLOWTEST"]["tags"]), al.get("ALLOWTEST"))
ok("D2c the earlier count is found by stock_watch's own name form (a name with '-'): since D-60, 1500 sold -> 1:5 (review M1)",
   al.get("ALLOW-PT", {}).get("allowance_t") == "1:5", al.get("ALLOW-PT", {}).get("allowance_t"))
ok("D2d a fresh short the judgment did not call a loss ('counted and kept') is not offered for a write-off (review S6)", "KEPTTEST" not in b1 and "KEPTTEST" not in al)
ok("D3 a short Marg still holds as an older loss, already asked of Amir -> box 2 with its whole path (F-1706 named)", "KTTEST DT" in wy and "KTTEST DT" not in b1
   and any("F-1706" in p[1] for p in wy["KTTEST DT"]["path"]) and any("7:11" in p[1] for p in wy["KTTEST DT"]["path"]), wy.get("KTTEST DT", {}).get("path"))
ok("D4 an evening count waits for the day's sales: tagged, no call", "EVETEST" in b1 and b1["EVETEST"]["awaits"] and any("waits" in t[1] for t in b1["EVETEST"]["tags"]),
   b1.get("EVETEST"))
ok("D5 about a delivery: tagged 'count again', never a write-off", "PANTEST 40" in b1 and any("about a delivery" in t[1] for t in b1["PANTEST 40"]["tags"]))
ok("D6 more on the shelf than in Marg, or a shelf only from an old count: not in box 1", "SURPTEST" not in b1 and "OLDTEST" not in b1)
ok("D7 a fresh short since written off in Marg -> settled", "GONETEST" in se, list(se))
ok("D8 box 2 holds the Expiry watch's open batch fix (his word 27-11: the night asks keep running)", "ALLOWTEST" in wy and any(t[1] == "batch fix" for t in wy["ALLOWTEST"]["tags"]),
   list(wy))
ok("D9 box 3: OLDTEST count first (with its Count button), VINBACTUM held; AGREETEST settled under 'Settled in Marg'",
   ol.get("OLDTEST", {}).get("verdict") == "count_first" and ol["OLDTEST"].get("count_btn") and ol.get("VINBACTUM DS", {}).get("verdict") == "held" and "AGREETEST" in se,
   (list(ol), list(se)))
mv = {m["no"]: m for m in K["moves"]}
ok("D10 box 4: each voucher nobody asked for, each item with its whole-item verdict; no rule date -> history",
   set(mv) == {"AD00010", "L000031"} and mv["L000031"]["items"][0]["verdict"] == "count_first" and mv["AD00010"]["items"][0]["verdict"] == "fresh_gap"
   and all(m["history"] for m in K["moves"]) and not K["rule_date"], {k: (m["items"], m["history"]) for k, m in mv.items()})
f.execute("INSERT INTO setting (key, value) VALUES ('stock.voucher_rule_from', ?)", (D(31),)); f.commit()
K2 = SC.desk(f, T.isoformat())
ok("D11 with his rule date set, a voucher after it is no longer history", {m["no"]: m["history"] for m in K2["moves"]} == {"AD00010": False, "L000031": False}
   and K2["rule_date"] == dmy(D(31)), {m["no"]: m["history"] for m in K2["moves"]})
f.execute("DELETE FROM setting WHERE key='stock.voucher_rule_from'"); f.commit()
T1 = f.total_changes
ok("D12 the desk and the judge write nothing (read only; the 2 are the walk's own setting row in and out)", T1 - T0 == 2, T1 - T0)
ok("D13 the rules panel: the allowance, the evening hour, the rule date, the batch check", {s["k"] for s in K["settings"]} >= {"stock.allowance_pct", "stock.allowance_min_strips",
   "evening_hour", "stock.voucher_rule_from", "batch_check", "cancel_days"})
# ---------------------------------------------------------------- 4 · the item ledger: counts (F-1707), the fold, the 'one of' words (F-1708)
sp = IL.spine_con()
L = IL.ledger(f, sp, "NORTEST TAB", D(29), D(0))
ce = [(d["day"], e["mark"], e["counted"]) for d in L["days"] for e in d["entries"] if e["kind"] == "count"]
ok("L1 F-1707: Darpan's count is a row of its day on the ledger (counted 0:2, 6:0 short)", ce == [(D(4), "6:0 short", 2)], ce)
d5 = [d for d in L["days"] if d["day"] == D(5)][0]
ok("L2 a count moves no balance: the day after it still agrees with Marg's closing", d5["state"] == "ok", (d5["state"], d5["expected"]))
LP = IL.ledger(f, sp, "PANTEST 40", D(29), D(0))
pc = [(e["mark"], e["status"]) for d in LP["days"] for e in d["entries"] if e["kind"] == "count"]
ok("L3 a replaced count says so; the standing one its gap", ("replaced by a later count", "superseded") in pc and ("2:0 short", "settled") in pc, pc)
d7 = [d for d in LP["days"] if d["day"] == D(7)][0]
ok("L4 F-1708: a closing short by one of two equal purchase lines names both ('bill 4043 … or bill 4100 …')", d7["state"] == "late" and "one of these" in d7.get("late", "")
   and "4043" in d7["late"] and "4100" in d7["late"], (d7["state"], d7.get("late")))
U = IL.item(sp, "NORTEST TAB")["unit"]
h = IL._ledger_html(L, U, "NORTEST TAB", "30", D(29), D(0))
ok("L5 the ledger page draws the count as an amber row: what was counted and the judgment", 'class="cnt' in h and "0:2 counted" in h and "6:0 short" in h, h[:200])
F = IL.fold(f, sp, "NORTEST TAB")
ok("L6 the fold: newest lines as data, the count among them, quiet days one line", F["ok"] and any(r["cls"] == "cnt" and r["bal"] == "0:2 counted" for r in F["rows"])
   and any(r["entry"] == "no movement" for r in F["rows"]) and F["rows"][0]["day"] != "" and len(F["rows"]) <= IL.FOLD_ROWS, F.get("rows"))
ok("L7 an unknown key: no fold, nothing raises", IL.fold(f, sp, "NO SUCH ITEM") is None)
pe = IL.page_html(f, {"k": "NORTEST TAB", "r": "full", "embed": "1"})
pn = IL.page_html(f, {"k": "NORTEST TAB", "r": "full"})
ok("L8 the embed view: no head crumb, no search; its own links keep the embed view", 'class="crumb"' not in pe and 'id="q"' not in pe and "&embed=1&r=30" in pe
   and 'class="crumb"' in pn and 'id="q"' in pn and "&embed=1" not in pn)
ok("L9 the ledger writes nothing either", f.total_changes == T1, f.total_changes - T1)
# ---------------------------------------------------------------- 5 · the doors (Flask)
import flask
app = flask.Flask("w"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None)); IL.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None))
c = app.test_client()
r = c.get("/finance/stockcheck/api/desk"); j = r.get_json() or {}
ok("W1 /api/desk answers the five boxes", r.status_code == 200 and j.get("ok") and all(k in j for k in ("box1", "allow", "way", "old", "moves", "settled", "settings")),
   (r.status_code, str(j)[:160]))
pg = c.get("/finance/stockcheck/").get_data(as_text=True)
ok("W2 the page draws the boxes and folds the S965 boxes under them", 'id="desk"' in pg and "function renderDesk" in pg and "/api/desk" in pg and 'id="vwrap"' in pg
   and "function vsection" in pg and "ledOpen" in pg and "embed=1" in pg)
rf = c.get("/finance/sanjeevni/ledger/api/fold?k=NORTEST%20TAB"); jf = rf.get_json() or {}
ok("W3 the ledger's fold door answers its rows", rf.status_code == 200 and jf.get("ok") and jf.get("rows"), (rf.status_code, str(jf)[:160]))
ok("W4 the healthz says v1.6 and the desk", c.get("/finance/stockcheck/api/healthz").get_json().get("version") == "1.6" and c.get("/finance/stockcheck/api/healthz").get_json().get("desk"))
app2 = flask.Flask("w2"); SC.init(app2, lambda: f, lambda *r: (({"user": "viewer"}, None) if "viewer" in r else (None, ("no", 403))))
IL.init(app2, lambda: f, lambda *r: (({"user": "viewer"}, None) if "viewer" in r else (None, ("no", 403))))
c2 = app2.test_client(); SC._DCACHE["v"] = None
ok("W5 a viewer reads the boxes; the ledger fold stays the doctor's", c2.get("/finance/stockcheck/api/desk?fresh=1").status_code == 200
   and c2.get("/finance/sanjeevni/ledger/api/fold?k=NORTEST%20TAB").status_code == 403)
ok("W6 no door wrote anything", f.total_changes == T1, f.total_changes - T1)
g = sqlite3.connect(os.path.join(W, "empty.db"))
ok("W7 an empty database: the desk says so, nothing raises", SC.desk(g, T.isoformat())["ok"] is False)
print("WALK %d/%d" % (sum(RES), len(RES)))
