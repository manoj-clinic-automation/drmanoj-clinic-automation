#!/usr/bin/env python3
"""walk_s971.py -- S971_AMIR_BY_HIMSELF (on S969 fixture) on MADE-UP data only (no real file is read): a small stock record, spine and finance database
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


W = tempfile.mkdtemp(prefix="walk971_")
SP, DB = os.path.join(W, "spine.db"), os.path.join(W, "finance.db")
os.environ["SPINE_DB"] = SP
T = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()      # IST, as the pages read it


def D(n):
    return (T - dt.timedelta(days=n)).isoformat()


def dmy(iso):
    return "%s-%s-%s" % (iso[8:10], iso[5:7], iso[:4])


import stock_check as SC
try:
    import voucher_inquiry as VI
except ImportError:                                                      # the control: the live files have no kit B
    ok("kit B (voucher_inquiry.py) is in place", False, "no voucher_inquiry"); print("WALK %d/%d" % (sum(RES), len(RES))); sys.exit(0)
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
# ================================================================ S971 · kit B: Amir by himself
import amir_day as AD
import re as _re
DAYI = T.isoformat()
PUSH = os.path.join(W, "push.jsonl"); os.environ["ORDER_PUSH_STUB"] = PUSH
TOM = (T + dt.timedelta(days=1)).strftime("%Y%m%d") + "-000100"         # a report exported after anything stamped today


def pushes():
    try:
        return [json.loads(x) for x in open(PUSH, encoding="utf-8") if x.strip()]
    except OSError:
        return []


def line(md5, kind, no, n, day, item, batch, u, per=10):
    f.execute("INSERT OR IGNORE INTO mi_voucher (md5,kind,no,day,cash,gross_p,bill_p,n_lines) VALUES (?,?,?,?,1,0,0,1)", (md5, kind, no, day))
    f.execute("INSERT INTO mi_voucher_line (md5,kind,no,n,day,item,packing,per,batch,qty,units,unit,expiry,rate_p,value_p) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (md5, kind, no, n, day, item, "1*10", per, batch, str(u), u, "TAB", "", 100, 100 * u))


def report(exported, to=None):
    f.execute("UPDATE mi_voucher_file SET exported=?, date_to=? WHERE ok=1", (exported, to or D(0))); f.commit()


def job(key, kind, subj, text, cat, done=None, how=None):
    f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,show_from,done_at,done_how,said_at) VALUES (?,?,?,?,?,?,?,?,?)",
              (key, kind, subj, text, cat, cat, done, how, done)); f.commit()


def jrow(key):
    return f.execute("SELECT id, kind, subject, text_hi, sub_hi, done_at, done_how, said_what FROM amir_job WHERE key=?", (key,)).fetchone()


def card():
    return "".join(AD._s494_lines(AD._s494_read(f)["jobs"]))


def ans(key, code):
    return AD._s494_tap(f, "amir", "ask:%d:%s" % (jrow(key)[0], code))


import flask
app = flask.Flask("w971"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None) if ("checker" in r or "maker" in r) else (None, ("no", 403)))
c = app.test_client()


def act(**b):
    r = c.post("/finance/stockcheck/api/desk/act", json=b)
    return r.status_code, (r.get_json() or {})


# ---- the judge v1.3 (read only)
line("mI", "ISSUE", "L000040", 1, D(4), "KEPTTEST", "K1", 5)               # keyed 2 days before the ask below, after the count it stands on
line("mI", "ISSUE", "L000042", 1, D(30), "KEPTTEST", "K1", 4)              # far before: never 'early'
line("mI", "ISSUE", "L000045", 1, D(4), "KEPTTEST", "K2", 5)               # second look M1: a SECOND line the same open ask could explain
job("S957:kepttest:x", "tap", "KEPTTEST", "KEPTTEST — Marg mein STOCK ISSUE kijiye: 5 goli", D(2) + " 09:00:00")
job("S969:wo:%s:1:GONETEST" % D(2), "tap", "GONETEST", "GONETEST — Marg mein STOCK ISSUE kijiye: 1 patte", D(2) + " 09:00:00", D(2) + " 10:00:00", "withdrawn")
line("mI", "ISSUE", "L000041", 1, D(6), "SURPTEST", "X", 3); line("mR", "RECEIVE", "AD00020", 1, D(3), "SURPTEST", "X", 3)
line("mI", "ISSUE", "L000044", 1, D(7), "RECTEST", "R", 6); line("mR", "RECEIVE", "AD00021", 1, D(6), "RECTEST", "R", 6)   # review M1: a cancel pair
job("S957:rectest:x", "tap", "RECTEST", "RECTEST — Marg mein STOCK ISSUE kijiye: 6 goli", D(2) + " 09:00:00")
f.commit()
J = V.judge(f, DAYI)
kp = [a for a in J["asks"] if a["item"] == "KEPTTEST" and a["src"] == "job"]
l40 = [x for x in J["lines"] if x["no"] == "L000040"]; l42 = [x for x in J["lines"] if x["no"] == "L000042"]
rc_ = [a["state"] for a in J["asks"] if a["item"] == "RECTEST" and a["src"] == "job"]; rcl = [x["state"] for x in J["lines"] if x["item"] == "RECTEST"]
ok("J1 the judge never takes a line keyed before its ask (review M1): the ask still waits, the line stays 'nobody asked' (the inquiry tells it)",
   kp and kp[0]["state"] == "waiting" and l40 and l40[0]["state"] == "unasked" and l42 and l42[0]["state"] == "unasked", (kp and kp[0]["state"], l40 and l40[0]["state"], l42 and l42[0]["state"]))
ok("J1b the review's control: an issue and a receive that cancel stay a cancel pair, the later ask of the same figure still waits", rcl == ["cancel", "cancel"] and rc_ == ["waiting"], (rcl, rc_))
ok("J2 a job the owner withdrew asks nothing", not [a for a in J["asks"] if "GONETEST" in a["item"] and a["src"] == "job"])
sp_ = [x["state"] for x in J["lines"] if x["item"] == "SURPTEST"]
f.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.voucher_cancel_days', '2')"); f.commit()
sp2 = [x["state"] for x in V.judge(f, DAYI)["lines"] if x["item"] == "SURPTEST"]
f.execute("DELETE FROM setting WHERE key='stock.voucher_cancel_days'"); f.commit()
ok("J3 the cancel window is his setting: 3 days apart cancel at 7, not at 2", sp_ == ["cancel", "cancel"] and sp2 == ["unasked", "unasked"], (sp_, sp2))
ok("J4 the judge v1.3 is still read only", V.VERSION == "1.3")
# ---- nothing before his dates: no rule date, no claim date -> the sync writes no card
VI.ensure(f); f.commit()
n0 = f.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0]
VI.sync(f, DAYI)
ok("K0 with no rule date and no claim date, the sync puts nothing on Amir's card", f.execute("SELECT COUNT(*) FROM amir_job").fetchone()[0] == n0)
# ---- the claim card
job("S957:twotest:x", "tap", "TWOTEST", "TWOTEST — Marg mein STOCK ISSUE kijiye: 20 goli", D(6) + " 09:00:00", D(4) + " 11:00:00")
f.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.claim_from', ?)", (D(5),)); f.commit()
open(PUSH, "w").close()
o = VI.sync(f, DAYI)
cl = f.execute("SELECT id, item, state, job_key, round FROM stock_voucher_claim").fetchall()
ok("C1 Amir said done (on or after the claim date) and Marg's newer report lacks it: ONE claim card by itself; the old done tap before the date none",
   o["claims"] == 1 and [x[1] for x in cl] == ["TWOTEST"] and cl[0][2] == "card" and "OLDTEST" not in str(cl), (o, cl))
jr = jrow(cl[0][3]) if cl else None
ok("C2 the card: kind ask, the two answers, the words of mock-up v7", jr and jr[1] == "ask" and jr[4] == "made,already"
   and jr[3].startswith("STOCK ISSUE ") and "TWOTEST" in jr[3] and "Marg ki nayi report mein yeh voucher nahi hai" in jr[3], jr)
h = card()
ok("C3 Amir's page: 'Voucher Marg mein nahi mila', 'Ab bana diya' / 'Pehle bana chuka hoon', nothing to type",
   "Voucher Marg mein nahi mila" in h and "Ab bana diya" in h and "Pehle bana chuka hoon" in h and "name=note" not in h.split("Voucher Marg mein nahi mila")[1].split("</form>")[0], h[:300])
ok("C4 one push to Amir", len(pushes()) == 1 and pushes()[0]["user"] == "amir", pushes())
o2 = VI.sync(f, DAYI)
ok("C5 a second sync makes nothing new", o2["claims"] == 0 and f.execute("SELECT COUNT(*) FROM stock_voucher_claim").fetchone()[0] == 1)
ans(cl[0][3], "made"); VI.sync(f, DAYI)
ok("C6 'Ab bana diya': the claim waits for the next report; the card leaves his page", f.execute("SELECT state FROM stock_voucher_claim WHERE id=?", (cl[0][0],)).fetchone()[0] == "made"
   and "Voucher Marg mein nahi mila" not in card())
e = VI.export_need(f, V.judge(f, DAYI))
ok("E1 the ONE export line on his list names it", e and e["n"] == 1 and "TWOTEST" in e["text"] and e["text"].startswith("Take Marg's Stock Issue + Stock Receive"), e)
report(TOM)
VI.sync(f, DAYI)
ok("C7 a newer report still lacks it: his call", f.execute("SELECT state FROM stock_voucher_claim WHERE id=?", (cl[0][0],)).fetchone()[0] == "yours")
ol = VI.owner_lines(f)
ok("C8 his Needs-you: one red line naming it", any(x["cls"] == "bad" and "TWOTEST" in x["text"] for x in ol), ol)
K = SC.desk(f, DAYI)
cr = [r for r in K["way"] if r.get("claim")]
ok("C9 box 2: the claim row with Back to Amir / Close, its path told", cr and cr[0]["acts"] == ["back", "cclose"] and any("Your call" in p[1] for p in cr[0]["path"]), cr and cr[0])
s_, j_ = act(act="back", ref=cl[0][0])
cl2 = f.execute("SELECT id, round, state, job_key FROM stock_voucher_claim ORDER BY id").fetchall()
ok("C10 Back to Amir: a second round on his card, the first closed", s_ == 200 and len(cl2) == 2 and cl2[0][2] == "closed" and cl2[1][1] == 2 and cl2[1][2] == "card", (s_, j_, cl2))
s_, j_ = act(act="back", ref=cl[0][0])
ok("C11 the same tap again writes nothing", s_ == 409 and f.execute("SELECT COUNT(*) FROM stock_voucher_claim").fetchone()[0] == 2, (s_, j_))
line("mI", "ISSUE", "L000043", 1, D(0), "TWOTEST", "T", 20); f.commit()
VI.sync(f, DAYI)
c3 = f.execute("SELECT state, closed_how FROM stock_voucher_claim WHERE id=?", (cl2[1][0],)).fetchone()
ok("C12 Marg's report shows it: the claim closes by itself, its card leaves", c3 == ("closed", "in Marg") and jrow(cl2[1][3])[6] == "withdrawn", (c3, jrow(cl2[1][3])))
job("S957:allowtest:x", "tap", "ALLOW-PT", "ALLOW-PT — Marg mein STOCK ISSUE kijiye: 3 goli", D(5) + " 09:00:00", D(5) + " 10:00:00")
VI.sync(f, DAYI)
cA = f.execute("SELECT id, job_key FROM stock_voucher_claim WHERE item='ALLOW-PT'").fetchone()
ans(cA[1], "already"); VI.sync(f, DAYI)
ok("C13 'Pehle bana chuka hoon': straight to his call (the print and scan are kit C)", f.execute("SELECT state, answer FROM stock_voucher_claim WHERE id=?", (cA[0],)).fetchone() == ("yours", "already"))
s_, j_ = act(act="cclose", ref=cA[0], note="checked in Marg myself")
ok("C14 Close with his line: closed, his note kept", s_ == 200 and f.execute("SELECT state, closed_how, note FROM stock_voucher_claim WHERE id=?", (cA[0],)).fetchone() == ("closed", "your OK", "checked in Marg myself"), (s_, j_))
job("S957:alltest:x", "tap", "AGREETEST", "AGREETEST — Marg mein STOCK ISSUE kijiye: 1 goli", D(5) + " 09:00:00", D(5) + " 10:00:00")
VI.sync(f, DAYI)
ok("C15 Marg already equals the shelf: no card (nothing to key)", not f.execute("SELECT 1 FROM stock_voucher_claim WHERE item='AGREETEST'").fetchone())
# ---- the inquiry (plan 2.5)
line("mI", "ISSUE", "L000050", 1, D(20), "AGREETEST", "A", 2)                      # Marg = shelf after it -> explained
line("mI", "ISSUE", "L000051", 1, D(15), "ALLOWTEST", "Z1", 4); line("mR", "RECEIVE", "AD00051", 1, D(14), "ALLOWTEST", "Z9", 4)   # a batch move
line("mI", "ISSUE", "L000052", 1, D(50), "RECTEST", "R", 1)                        # before the rule date: history
f.commit()
s_, j_ = act(act="setting", key="stock.voucher_rule_from", value=dmy(D(40)))
ok("S1 the rule date is his to set on the page (dd-mm-yyyy kept as a date)", s_ == 200 and VI.setting(f, "stock.voucher_rule_from") == D(40), (s_, j_))
open(PUSH, "w").close()
o = VI.sync(f, DAYI)
IQ = {r[1]: r for r in f.execute("SELECT id, no, state, job_key, how_json FROM stock_voucher_inquiry").fetchall()}
ok("I1 the vouchers after the rule date: L000031, AD00010 and L000042 asked of Amir; L000050 (Marg = shelf) and the batch move explained by the system; the history none",
   IQ.get("L000031", [0, 0, ""])[2] == "asked" and IQ.get("AD00010", [0, 0, ""])[2] == "asked" and IQ.get("L000042", [0, 0, ""])[2] == "asked" and IQ.get("L000040", [0, 0, ""])[2] == "early" and IQ.get("L000045", [0, 0, ""])[2] == "asked"
   and "L000044" not in IQ and "AD00021" not in IQ and IQ.get("L000050", [0, 0, ""])[2] == "explained"
   and IQ.get("L000051", [0, 0, ""])[2] == "explained" and IQ.get("AD00051", [0, 0, ""])[2] == "explained" and "L000052" not in IQ, {k: v[2] for k, v in IQ.items()})
ok("I1b the system's own words for an explained one", "batches" in (IQ.get("L000051") or [0] * 5)[4] and "Marg equals the shelf" in (IQ.get("L000050") or [0] * 5)[4]
   and "keyed before it was asked" in (IQ.get("L000040") or [0] * 5)[4], (IQ.get("L000040") or [0] * 5)[4])
ok("I2 ONE push for the sync, however many cards", len(pushes()) == 1 and pushes()[0]["payload"]["title"].startswith("Marg ke"), pushes())
jq = jrow(IQ["L000031"][3])
ok("I3 the question: the words of mock-up v9, five one-tap answers", jq and jq[3] == "L000031 (%s): STOCK ISSUE — SHOETEST L 1 nag. System ne yeh nahi maanga tha. Kyon banaya?" % VI.dm(D(30))
   and jq[4] == "vmistake,vcount,vbatch,vdump,unknown", jq)
h = card()
ok("I4 Amir's page: 'Sawaal · Stock voucher' with the five answers, nothing to type", h.count("Sawaal · Stock voucher") == 4 and "name=note" not in h and all(w in h for w in ("Galti se bana", "Ginti mein farak tha", "Batch theek kiya", "Kharab / expiry", "Pata nahi")), h[:200])
line("mI", "ISSUE", "L000046", 1, D(1), "KEPTTEST", "K3", 5); f.commit()    # the ask is now answered by another line
VI.sync(f, DAYI)
e40 = f.execute("SELECT state, job_key FROM stock_voucher_inquiry WHERE no='L000040'").fetchone()
ok("I4b second look M1: one open ask explains ONE line (L000045 asked); the 'keyed before the ask' row is watched and, once the ask is in Marg by "
   "another line, asked of Amir", e40[0] == "asked" and e40[1] and jrow(e40[1]) and jrow(e40[1])[1] == "ask", e40)
gq = sqlite3.connect(":memory:"); f.backup(gq)                           # re-look M1: an asked row, then a later ask of the same figure, then 'Galti se bana'
def gline(no, day, u):
    gq.execute("INSERT OR IGNORE INTO mi_voucher (md5,kind,no,day,cash,gross_p,bill_p,n_lines) VALUES ('mI','ISSUE',?,?,1,0,0,1)", (no, day))
    gq.execute("INSERT INTO mi_voucher_line (md5,kind,no,n,day,item,packing,per,batch,qty,units,unit,expiry,rate_p,value_p) VALUES ('mI','ISSUE',?,1,?,'ONLISTTEST','1*10',10,'O',?,?,'TAB','',100,100)", (no, day, str(u), u))
    gq.commit()
gline("L000080", D(30), 3); VI.sync(gq, DAYI)
j80 = gq.execute("SELECT state, job_key FROM stock_voucher_inquiry WHERE no='L000080'").fetchone()
gq.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,show_from) VALUES (?,?,?,?,?,?)", ("S998:onlisttest:y", "tap", "ONLISTTEST",
           "ONLISTTEST — Marg mein STOCK ISSUE kijiye: 3 goli", D(25) + " 09:00:00", D(25) + " 09:00:00")); gq.commit()
gline("L000081", D(27), 3); VI.sync(gq, DAYI)
ok("I4c an asked row never draws on a later ask: it stays asked, its card stays; the newer line that ask fits is the one watched ('early')",
   j80[0] == "asked" and gq.execute("SELECT state FROM stock_voucher_inquiry WHERE no='L000080'").fetchone()[0] == "asked"
   and not gq.execute("SELECT done_at FROM amir_job WHERE key=?", (j80[1],)).fetchone()[0]
   and (gq.execute("SELECT state FROM stock_voucher_inquiry WHERE no='L000081'").fetchone() or [""])[0] == "early",
   gq.execute("SELECT no, state FROM stock_voucher_inquiry WHERE no IN ('L000080','L000081')").fetchall())
AD._s494_tap(gq, "amir", "ask:%d:vmistake" % gq.execute("SELECT id FROM amir_job WHERE key=?", (j80[1],)).fetchone()[0]); VI.sync(gq, DAYI)
rv80 = gq.execute("SELECT state, rev_json FROM stock_voucher_inquiry WHERE no='L000080'").fetchone()
ok("I4d ... then 'Galti se bana': the reversal IS made (never an empty one)", rv80[0] == "reversing" and json.loads(rv80[1] or "[]")
   and gq.execute("SELECT 1 FROM amir_job WHERE key LIKE 'S971:rev:ISSUE:L000080:%'").fetchone() is not None, rv80)
ok("I5 a made-up answer code changes nothing", AD._s494_tap(f, "amir", "ask:%d:fixed" % jq[0]) == 0 and AD._s494_tap(f, "amir", "ask:%d:burn" % jq[0]) == 0)
# a mistake -> the exact reversal on Amir's card, closed by the next report
fm = sqlite3.connect(":memory:"); f.backup(fm)
ans(IQ["L000031"][3], "vmistake"); VI.sync(f, DAYI)
rv = jrow("S971:rev:ISSUE:L000031:%s:1" % D(30).replace("-", ""))
ok("R1 'Galti se bana': the exact reversal on his card -- STOCK RECEIVE SHOETEST L 1 nag, its own row of units", rv and rv[1] == "tap" and rv[3] == "SHOETEST L — Marg mein STOCK RECEIVE kijiye: 1 nag"
   and f.execute("SELECT kind, units, pack FROM stock_inquiry_job WHERE job_key='S971:rev:ISSUE:L000031:%s:1'" % D(30).replace("-", "") + "").fetchone() == ("RECEIVE", 1, 1), rv)
h = card()
ok("R2 Amir's page: 'Marg mein theek kariye', one 'Marg mein kar diya' (tapr)", "Marg mein theek kariye" in h and h.count("tapr:ISSUE:L000031:") == 1, h[:300])
ra = [a for a in V.judge(f, DAYI)["asks"] if a.get("ref") == "S971:rev:ISSUE:L000031:%s:1" % D(30).replace("-", "")]
ok("R3 the judge reads the reversal as a RECEIVE of 1, from its own row", ra and ra[0]["kind"] == "RECEIVE" and ra[0]["units"] == 1, ra and (ra[0]["kind"], ra[0]["units"]))
TV = _re.search(r"value='(tapr:[^']+)'", h).group(1)
ok("R4 his one tap marks the reversal done", AD._s494_tap(f, "amir", TV) == 1 and jrow("S971:rev:ISSUE:L000031:%s:1" % D(30).replace("-", ""))[5])
line("mR", "RECEIVE", "AD00060", 1, D(0), "SHOETEST L", "1", 1, 1); f.commit()
VI.sync(f, DAYI)
ok("R5 Marg's report shows the reversal: the inquiry closes 'reversed'", f.execute("SELECT state FROM stock_voucher_inquiry WHERE no='L000031'").fetchone()[0] == "reversed")
# a count difference -> a recount on Darpan's next list; agrees -> explained; not -> the reversal + his list
fr = sqlite3.connect(":memory:"); f.backup(fr)
ans(IQ["AD00010"][3], "vcount"); VI.sync(f, DAYI)
ra_ = f.execute("SELECT state, rec_json FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()
ak = f.execute("SELECT id, mode, done_at FROM stock_watch_ask WHERE item='NORTEST TAB'").fetchall()
ok("N1 'Ginti mein farak tha': a recount of NORTEST TAB at the head of Darpan's next list", ra_[0] == "recount" and ak and ak[-1][1] == "next" and not ak[-1][2], (ra_, ak))
fa = sqlite3.connect(":memory:"); f.backup(fa)
LT = (dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))) + dt.timedelta(minutes=5)).replace(tzinfo=None).isoformat(timespec="seconds")
fa.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
           (SW.norm_name("NORTEST TAB"), "NORTEST TAB", LT, 62, "darpan", "darpan", 62, 0, "settled", "matches Marg"))
fa.execute("UPDATE stock_of_record SET base_kind='darpan', base_at=?, base_day=?, shelf_units=62, gap_units=0, state='agree' WHERE item='NORTEST TAB'", (LT, LT[:10])); fa.commit()
fo = sqlite3.connect(":memory:"); f.backup(fo)                           # the record moved on a count made BEFORE the question: never its answer
fo.execute("UPDATE stock_of_record SET base_kind='darpan', base_at=?, gap_units=0, state='agree' WHERE item='NORTEST TAB'", (D(4) + "T10:23:46",)); fo.commit()
VI.sync(fo, DAYI)
ok("N1b a count made before the question never answers the recount (by the count's own id, not by clocks)", fo.execute("SELECT state FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0] == "recount")
fo.execute("UPDATE stock_voucher_inquiry SET answered_at='2000-01-01 00:00:00' WHERE no='AD00010'"); fo.commit(); VI.sync(fo, DAYI)
ok("N1c no recount in %d days: his list, red, Reverse / Close" % VI.RECOUNT_DAYS, any("no recount" in x["text"] for x in VI.owner_lines(fo))
   and [x for x in VI.inquiry_view(fo, D(40))[0] if x["no"] == "AD00010"][0]["acts"] == ["reverse", "close"])
VI.sync(fa, DAYI)
ok("N2 the recount agrees with Marg after the voucher: explained, closed by itself", fa.execute("SELECT state FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0] == "explained")
f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
          (SW.norm_name("NORTEST TAB"), "NORTEST TAB", LT, 2, "darpan", "darpan", 62, -60, "settled", "6:0 below Marg"))
f.execute("UPDATE stock_of_record SET base_kind='darpan', base_at=?, base_day=? WHERE item='NORTEST TAB'", (LT, LT[:10])); f.commit()
VI.sync(f, DAYI)
dg = f.execute("SELECT state, disagree FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()
ok("N3 the recount does not agree: the reversal goes to Amir (STOCK ISSUE 9 patte) and one red line to his list", dg == ("reversing", 1)
   and (jrow("S971:rev:RECEIVE:AD00010:%s:1" % D(30).replace("-", "")) or [0, 0, 0, ""])[3] == "NORTEST TAB — Marg mein STOCK ISSUE kijiye: 9 patte"
   and any("recount disagrees" in x["text"] for x in VI.owner_lines(f)), (dg, jrow("S971:rev:RECEIVE:AD00010:%s:1" % D(30).replace("-", ""))))
s_, j_ = act(act="close", ref=IQ["AD00010"][0], note="the count was wrong, AD00010 is right")
ok("N4 his Close: closed with his line; the unkeyed reversal taken off Amir's card", s_ == 200 and f.execute("SELECT state, note FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone() == ("closed", "the count was wrong, AD00010 is right")
   and jrow("S971:rev:RECEIVE:AD00010:%s:1" % D(30).replace("-", ""))[6] == "withdrawn", (s_, j_))
ok("N5 a withdrawn reversal asks nothing of the judge", not [a for a in V.judge(f, DAYI)["asks"] if a.get("ref") == "S971:rev:RECEIVE:AD00010:%s:1" % D(30).replace("-", "")])
# the other three answers and the silence, each on a copy
for code, want in (("unknown", "yours"), ("vdump", "dump"), ("vbatch", "batch")):
    g = sqlite3.connect(":memory:"); fr.backup(g)
    AD._s494_tap(g, "amir", "ask:%d:%s" % (g.execute("SELECT id FROM amir_job WHERE key=?", (IQ["AD00010"][3],)).fetchone()[0], code)); VI.sync(g, DAYI)
    st_ = g.execute("SELECT state FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0]
    ok("A-%s the answer '%s' -> %s" % (code, code, want), st_ == want, st_)
    if code == "unknown":
        ok("A-unknown2 his list: red, 'Pata nahi'; Reverse / Close on the row", any("Pata nahi" in x["text"] for x in VI.owner_lines(g))
           and [x for x in VI.inquiry_view(g, D(40))[0] if x["no"] == "AD00010"][0]["acts"] == ["reverse", "close"])
        app2 = flask.Flask("w971r"); SC.init(app2, lambda: g, lambda *r: ({"user": "manoj"}, None) if ("checker" in r or "maker" in r) else (None, ("no", 403)))
        r2 = app2.test_client().post("/finance/stockcheck/api/desk/act", json={"act": "reverse", "ref": IQ["AD00010"][0]})
        ok("A-unknown3 his Reverse: the reversal on Amir's card", r2.status_code == 200 and g.execute("SELECT state FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0] == "reversing"
           and g.execute("SELECT 1 FROM amir_job WHERE key LIKE 'S971:rev:RECEIVE:AD00010:%'").fetchone() is not None, r2.get_json())
        app = flask.Flask("w971c"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None) if ("checker" in r or "maker" in r) else (None, ("no", 403))); c = app.test_client()
    if code == "vdump":
        app3 = flask.Flask("w971d"); SC.init(app3, lambda: g, lambda *r: ({"user": "manoj"}, None) if ("checker" in r or "maker" in r) else (None, ("no", 403)))
        r3 = app3.test_client().post("/finance/stockcheck/api/desk/act", json={"act": "dumpok", "ref": IQ["AD00010"][0]})
        ok("A-vdump2 his one tap OK closes it as damaged / expiry", r3.status_code == 200 and g.execute("SELECT state, closed_how FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0] == "closed")
        app = flask.Flask("w971c"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None) if ("checker" in r or "maker" in r) else (None, ("no", 403))); c = app.test_client()
    if code == "vbatch":
        g.execute("INSERT INTO stock_batch_now (run_id, as_on, at, k20, item, batch, units, pack) VALUES (11, ?, ?, 'X', 'X', 'B', 1, 1)", (DAYI, "2099-01-01T00:00:00")); g.commit()
        VI.sync(g, DAYI)
        ok("A-vbatch2 the next Batch Stock export is in: explained", g.execute("SELECT state FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0] == "explained")
g = sqlite3.connect(":memory:"); fr.backup(g)                            # review S1: the rule date cleared -- an open row is still followed
g.execute("DELETE FROM setting WHERE key='stock.voucher_rule_from'"); g.commit()
AD._s494_tap(g, "amir", "ask:%d:unknown" % g.execute("SELECT id FROM amir_job WHERE key=?", (IQ["AD00010"][3],)).fetchone()[0]); VI.sync(g, DAYI)
ok("Q0 his rule date cleared: Amir's open answer is still taken, the row still shown", g.execute("SELECT state FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0] == "yours"
   and any(x["no"] == "AD00010" for x in VI.inquiry_view(g, "")[0]))
g = sqlite3.connect(":memory:"); fr.backup(g)
g.execute("UPDATE stock_voucher_inquiry SET made_at='2000-01-01 00:00:00' WHERE no='AD00010'"); g.commit(); VI.sync(g, DAYI)
ok("Q1 no answer in the set days: his list, red; Reverse / Close; the question stays on Amir's card", any("no answer" in x["text"] for x in VI.owner_lines(g))
   and [x for x in VI.inquiry_view(g, D(40))[0] if x["no"] == "AD00010"][0]["acts"] == ["reverse", "close"]
   and not g.execute("SELECT done_at FROM amir_job WHERE key=?", (IQ["AD00010"][3],)).fetchone()[0])
g = sqlite3.connect(":memory:"); fr.backup(g)
g.execute("UPDATE stock_of_record SET gap_units=0, shelf_units=62, state='agree' WHERE item='NORTEST TAB'")
g.execute("UPDATE stock_of_record SET gap_units=0, shelf_units=3, state='agree' WHERE item IN ('KNEE IMMOBILIZER L UNISON')"); g.commit()
VI.sync(g, DAYI)
ok("Q2 explained since (Marg now equals the shelf): the question leaves Amir's card by itself", g.execute("SELECT state FROM stock_voucher_inquiry WHERE no='AD00010'").fetchone()[0] == "explained"
   and g.execute("SELECT done_how FROM amir_job WHERE key=?", (IQ["AD00010"][3],)).fetchone()[0] == "withdrawn")
K = SC.desk(f, DAYI)
b4 = {x["no"]: x for x in K["inquiry"] + K["inquiry_done"]}
ok("B1 box 4: the inquiry's rows (open and folded), the history before the rule date as history, nothing twice",
   "L000031" in b4 and "AD00010" in b4 and any(m["no"] == "L000052" and m["history"] for m in K["moves"]) and not any(m["no"] in b4 for m in K["moves"]), (list(b4), [(m["no"], m["history"]) for m in K["moves"]]))
ok("B2 the tally of the month (his only)", set(K["tally"]) >= {"explained", "reversed", "closed", "open"} and K["rule_date"] == dmy(D(40)), K["tally"])
ok("B3 the settings are his to change on the page", {s["k"] for s in K["edit"]} >= {"stock.voucher_rule_from", "stock.inq_question_days", "stock.voucher_cancel_days", "stock.inq_batch_check"})
# ---- settings, by the door
for k, v, good in (("stock.voucher_rule_from", (T + dt.timedelta(days=3)).strftime("%d-%m-%Y"), False), ("stock.inq_question_days", "0", False),
                   ("stock.inq_question_days", "3", True), ("stock.inq_batch_check", "off", True), ("stock.not_a_key", "1", False), ("stock.claim_from", "", False)):
    s_, j_ = act(act="setting", key=k, value=v)
    ok("S2 setting %s = %r %s" % (k, v, "saved" if good else "refused"), (s_ == 200) == good, (s_, j_))
ok("S3 the saved values read back", VI.int_setting(f, "stock.inq_question_days") == 3 and VI.setting(f, "stock.inq_batch_check") == "off")
# ---- the loss register's prices, and Withdraw (S969's red 'not to be keyed' row)
f.execute("CREATE TABLE IF NOT EXISTS stock_rate (item TEXT PRIMARY KEY, rate_p INTEGER NOT NULL, pack_size INTEGER NOT NULL DEFAULT 1, as_of TEXT, source TEXT)")
f.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, pack_size, as_of, source) VALUES ('TWOTEST', 50, 10, ?, 'walk')", (D(1),))
s = sqlite3.connect(SP); s.execute("INSERT INTO sp_item_fact VALUES ('TWOTEST', '1*10', 'mrp', '70.00', ?, 'x')", (D(5),)); s.commit(); s.close()
f.commit()
P = f.execute("SELECT id, at FROM stock_point WHERE item='TWOTEST'").fetchone()
SC._ensure_desk(f); f.commit()
mk, sk = SC._write_off(f, [dict(item="TWOTEST", short=20, pack=10, pid=P[0], pat=P[1], qty=50, expected=70, key="TWOTEST")], "manoj", "short")
da = f.execute("SELECT cost_p, mrp_p, priced, job_key FROM stock_desk_action WHERE kind='writeoff' AND item='TWOTEST'").fetchone()
ok("L1 a write-off is priced AT THE TAP: cost 20 x Rs 0.50 = Rs 10.00, MRP 20 x Rs 70.00 / 10 = Rs 140.00", mk == ["TWOTEST"] and da and da[0] == 1000 and da[1] == 14000 and da[2] == "at the tap", (mk, sk, da))
f.execute("UPDATE stock_of_record SET base_at=?, base_day=?, shelf_units=70, gap_units=0, state='agree' WHERE item='TWOTEST'", (D(0) + "T09:40:00", D(0)))
f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
          (SW.norm_name("TWOTEST"), "TWOTEST", D(0) + "T09:40:00", 70, "darpan", "darpan", 70, 0, "settled", "matches Marg")); f.commit()
SC._DCACHE["v"] = None
K = SC.desk(f, DAYI)
red = [r for r in K["way"] if r["item"] == "TWOTEST" and r["tags"] and r["tags"][0][0] == "red"]
ok("W1 the red row 'not to be keyed' now offers Withdraw (Amir has not tapped it done)", red and red[0]["acts"] == ["wd"], [(r["item"], r["tags"], r.get("acts")) for r in K["way"] if r["item"] == "TWOTEST"])
s_, j_ = act(act="withdraw", item="TWOTEST")
ok("W2 Withdraw: off Amir's card (withdrawn), a desk row of its own; the judge asks nothing of it", s_ == 200 and jrow(da[3])[6] == "withdrawn"
   and f.execute("SELECT COUNT(*) FROM stock_desk_action WHERE kind='withdraw' AND item='TWOTEST'").fetchone()[0] == 1
   and not [a for a in V.judge(f, DAYI)["asks"] if a.get("ref") == da[3]], (s_, j_))
s_, j_ = act(act="withdraw", item="TWOTEST")
ok("W3 a second Withdraw writes nothing", s_ == 409, (s_, j_))
ok("W4 the row is no longer red", not [r for r in SC.desk(f, DAYI)["way"] if r["item"] == "TWOTEST" and r["tags"] and r["tags"][0][0] == "red"])
# ---- the loss register
f.execute("INSERT INTO stock_desk_action (kind, item, item_norm, pack, units, point_id, point_at, qty_units, expected_units, job_key, box, day, at, by) "
          "VALUES ('writeoff','ALLOWTEST','ALLOWTEST',10,8,NULL,?,167,175,'S969:wo:%s:1:ALLOWTEST','allow',?,?,'manoj')" % D(3), (D(9) + "T11:24:08", D(3), D(3) + "T12:00:00"))
f.execute("INSERT INTO amir_job (key,kind,subject,text_hi,created_at,show_from) VALUES (?,?,?,?,?,?)", ("S969:wo:%s:1:ALLOWTEST" % D(3), "tap", "ALLOWTEST",
          "ALLOWTEST — Marg mein STOCK ISSUE kijiye: 8 goli", D(3) + " 12:00:00", D(3) + " 12:00:00")); f.commit()
nb = VI.backfill_values(f, "at install 27-11")
pr = f.execute("SELECT priced FROM stock_desk_action WHERE item='ALLOWTEST' AND kind='writeoff'").fetchone()[0]
ok("L2 the installer prices a write-off made before the kit once, and says so; one priced at the tap is never re-priced", nb == 1 and pr == "at install 27-11"
   and f.execute("SELECT priced FROM stock_desk_action WHERE item='TWOTEST' AND kind='writeoff'").fetchone()[0] == "at the tap", (nb, pr))
f.execute("INSERT INTO stock_desk_action (kind, item, item_norm, pack, units, point_id, ask_id, box, day, at, by) VALUES ('pursue','PANTEST 40','PANTEST 40',10,20,NULL,NULL,'short',?,?,'manoj')",
          (D(2), D(2) + "T10:00:00")); f.commit()
f.execute("CREATE TABLE IF NOT EXISTS stock_writeoff_run (id INTEGER PRIMARY KEY, count_id INTEGER NOT NULL, at TEXT NOT NULL, by_user TEXT, lines_n INTEGER NOT NULL, mrp_p INTEGER NOT NULL, "
          "cost_p INTEGER NOT NULL, unpriced INTEGER NOT NULL, groups TEXT NOT NULL, settings TEXT NOT NULL, round_no INTEGER, md5 TEXT NOT NULL)")
f.execute("INSERT INTO stock_writeoff_run (count_id, at, lines_n, mrp_p, cost_p, unpriced, groups, settings, md5) VALUES (1, '2026-09-27T12:58:31', 122, 6390329, 4427185, 0, '{}', '{}', 'x')"); f.commit()
LR = VI.losses(f)
mo = LR["months"][0] if LR["months"] else {}
tw = [x for x in mo.get("lines", []) if x["item"] == "TWOTEST"]
ok("L3 the register: the month, its lines; a withdrawn line struck and out of the totals", tw and tw[0]["withdrawn"] and tw[0]["marg"].startswith("withdrawn")
   and mo["n"] == sum(1 for m in LR["months"] for x in m["lines"] if not x["withdrawn"] and m is mo), (mo.get("n"), [(x["item"], x["withdrawn"], x["marg"]) for x in mo.get("lines", [])]))
al = [x for m in LR["months"] for x in m["lines"] if x["item"] == "ALLOWTEST"]
ok("L4 each line: its count (counted vs Marg), its group, Marg's voucher state", al and al[0]["group"] == "within the allowance" and al[0]["marg"] == "on Amir's card" and "counted 16:7, Marg 17:5" in al[0]["count"], al)
ok("L5 the pursued item's end; the full count's runs beside", any(p["item"] == "PANTEST 40" for p in LR["pursued"]) and LR["runs"] and LR["runs"][0]["cost_t"] == "₹44,271.85", (LR["pursued"], LR["runs"]))
ok("L6 rupees in the Indian way", VI.rupees(6390329) == "₹63,903.29" and VI.rupees(1000) == "₹10.00" and VI.rupees(None) == "—")
r = c.get("/finance/stockcheck/api/losses").get_json()
ok("L7 /api/losses (the owner) answers the register; the page is served", r.get("ok") and r.get("months") is not None and "Loss register" in c.get("/finance/stockcheck/losses").get_data(as_text=True), r.get("reason"))
appv = flask.Flask("w971v"); SC.init(appv, lambda: f, lambda *r: ({"user": "bhati"}, None) if ("viewer" in r and "checker" not in r) else (None, ("no", 403)))
cv = appv.test_client()
ok("L8 the loss register is his only: a viewer gets 403", cv.get("/finance/stockcheck/api/losses").status_code == 403 and cv.get("/finance/stockcheck/losses").status_code == 403)
nv = f.total_changes; SC._DCACHE["v"] = None
cv.get("/finance/stockcheck/api/desk?fresh=1")
ok("R1 a viewer's read of the desk writes nothing (no sync)", f.total_changes == nv, f.total_changes - nv)
r5 = cv.post("/finance/stockcheck/api/desk/act", json={"act": "close", "ref": 1})
ok("R2 only the owner taps the inquiry's buttons", r5.status_code == 403)
app = flask.Flask("w971e"); SC.init(app, lambda: f, lambda *r: ({"user": "manoj"}, None) if ("checker" in r or "maker" in r) else (None, ("no", 403))); c = app.test_client()
hz = c.get("/finance/stockcheck/api/healthz").get_json()
ok("R3 healthz v1.8, kit B and the loss register", hz.get("version") == "1.8" and hz.get("kit_b") == "S971_AMIR_BY_HIMSELF" and hz.get("losses"), hz)
pg = c.get("/finance/stockcheck/").get_data(as_text=True) + c.get("/finance/stockcheck/losses").get_data(as_text=True)
ok("R4 the pages: no confirm / alert / prompt anywhere; the new buttons and the intro fix in place", "confirm(" not in pg and "alert(" not in pg and "prompt(" not in pg
   and "function irow" in pg and "Open the loss register" in pg and "The boxes are read" in pg and "Back to Amir" in pg, [x for x in ("confirm(", "alert(", "prompt(") if x in pg])
r6 = act(act="reverse", ref=999999)
ok("R5 a made-up row id writes nothing", r6[0] == 409)
f.execute("UPDATE stock_voucher_inquiry SET state='yours' WHERE no='AD00010'"); f.commit()   # one of his, for the Hub
NY = AD.needs_you_lines(f)
ok("H1 the Hub's Needs-you carries his lines (amir_day)", isinstance(NY, list) and any(x.get("target") == "stock" and ("Voucher nobody asked for" in x["text"] or "Take Marg's" in x["text"] or "your call" in x["text"]) for x in NY), [x.get("text") for x in NY][:6])
ns = f.total_changes
f.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.inq_synced_at', ?)", (dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).replace(tzinfo=None, microsecond=0).isoformat(),)); f.commit()
ns = f.total_changes
VI.sync_maybe(f)
ok("H2 Amir's page syncs at most once in 5 minutes", f.total_changes == ns, f.total_changes - ns)
f.execute("BEGIN"); f.execute("UPDATE setting SET value=value WHERE key='stock.inq_synced_at'")
ok("H3 never inside a caller's open transaction", VI.sync_maybe(f, force=True) is None); f.rollback()
CALLS = []
appm = flask.Flask("w971m"); SC.init(appm, lambda: CALLS.append(1) or (_ for _ in ()).throw(RuntimeError("Working outside of application context")), lambda *r: ({"user": "manoj"}, None))
ok("I9 the mount never opens the database", CALLS == [], CALLS)
print("WALK %d/%d" % (sum(RES), len(RES)))
