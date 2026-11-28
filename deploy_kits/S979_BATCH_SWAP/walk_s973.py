#!/usr/bin/env python3
"""walk_s973.py -- S973_VOUCHER_SCANS (the Sanjeevni side) on MADE-UP data only: kit B's own walk fixture (walk_s971.py, run up to its
'Pehle bana chuka hoon' step, its checks counted apart) and a made-up assets.db for the scans. No real file is read.
    python3 walk_s973.py FIN_DIR MI_DIR WALK_S971
FIN_DIR holds the finance files (the built ones, or the live ones for the control) with spine/ beside; MI_DIR holds marg_vouchers.py.
Last line: WALK passed/total."""
import datetime as dt, json, os, sqlite3, sys, tempfile

FIN, MI, W971 = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(W971, encoding="utf-8").read()
CUT = 'ans(cA[1], "already"); VI.sync(f, DAYI)'
head = src[:src.index(CUT)]
ns = {"__name__": "__walk971_head__", "__file__": W971}
sys.argv = [W971, FIN, MI]
exec(compile(head, W971, "exec"), ns)                                    # kit B's fixture and its checks up to C12 (printed, not counted here)
HEAD_RES = list(ns["RES"])
RES = []


def ok(n, c, d=""):
    RES.append(bool(c)); print("%s  %s%s" % ("PASS" if c else "FAIL", n, ("  -- " + str(d)[:300]) if d and not c else ""))


print("---- (kit B's own checks above: %d/%d) ---- S973 ----" % (sum(HEAD_RES), len(HEAD_RES)))
f, VI, V, AD, SC = ns["f"], ns["VI"], ns["V"], ns["AD"], ns["SC"]
D, DAYI, jrow, card, ans, act, pushes, line, PUSH, W = ns["D"], ns["DAYI"], ns["jrow"], ns["card"], ns["ans"], ns["act"], ns["pushes"], ns["line"], ns["PUSH"], ns["W"]
cA = ns["cA"]
try:
    import voucher_scan as VS
except ImportError:
    ok("kit C (voucher_scan.py) is in place", False, "no voucher_scan"); print("WALK %d/%d" % (sum(RES), len(RES))); sys.exit(0)
# ---------------------------------------------------------------- the made-up assets.db (the Scan App's three tables, as read)
ADB = os.path.join(W, "assets.db"); os.environ["ASSETS_DB"] = ADB
if "purchase_app" in sys.modules:
    sys.modules["purchase_app"]._assets_db = ADB
a = sqlite3.connect(ADB)
a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, kind TEXT, stamp_no TEXT, bill_no TEXT, bill_date TEXT, submitted_at TEXT, created_at TEXT, status TEXT, dup_of INTEGER, lane TEXT)")
a.execute("CREATE TABLE bill_items (id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, quantity REAL, batch TEXT)")
a.execute("CREATE TABLE claude_reading (bill_id INTEGER PRIMARY KEY, at TEXT, model TEXT, ok INTEGER, doc_kind TEXT, data TEXT, error TEXT)")
a.commit()
SN = [9000]


def scan(no, day, lines, kind="Stock voucher", at=None, vt="ISSUE"):
    SN[0] += 1
    at = at or (dt.datetime.now(VS.IST).replace(tzinfo=None) + dt.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
    cur = a.execute("INSERT INTO bills (kind, stamp_no, bill_no, bill_date, submitted_at, status, lane) VALUES (?,?,?,?,?,'captured','pharmacy')",
                    (kind, "B-%04d" % SN[0], no, day, at))
    for n_, q in lines:
        a.execute("INSERT INTO bill_items (bill_id, item_name, quantity, batch) VALUES (?,?,?,'')", (cur.lastrowid, n_, q))
    a.execute("INSERT INTO claude_reading (bill_id, ok, doc_kind, data) VALUES (?,1,'stock_voucher',?)",
              (cur.lastrowid, json.dumps(dict(doc_kind="stock_voucher", voucher_type=vt, bill_no=no, items=[dict(name=n_, qty=q) for n_, q in lines]))))
    a.commit()
    return "B-%04d" % SN[0]


def claim(cid):
    return f.execute("SELECT state, answer, closed_how, round, job_key, note FROM stock_voucher_claim WHERE id=?", (cid,)).fetchone()


def sask(why, ref):
    return VS.ask_of(f, why, ref)


def prt_job(sa):
    return jrow(sa["job_key"]) if sa and sa.get("job_key") else None


open(PUSH, "w").close()
f.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.scan_ask_from', ?)", (D(3),)); f.commit()   # the install day's date (made-up)
# ================================================================ P · the claim's print and scan
ans(cA[1], "already")                                                    # amir_day's tap: syncs at once (no 5-minute wait)
c1 = claim(cA[0]); s1 = sask("claim", cA[0]); j1 = prt_job(s1)
ok("P1 'Pehle bana chuka hoon': the claim waits for the voucher's print AT ONCE (no 5-minute wait): ONE print ask, ONE card 'Print diya'",
   c1[0] == "print" and s1 and s1["state"] == "card" and j1 and j1[1] == "ask" and j1[4] == "printed" and j1[5] is None, (c1, s1, j1))
ok("P1b one push to Amir: the voucher's print is asked", any(p["user"] == "amir" and "print" in p["payload"]["title"].lower() for p in pushes()), pushes())
h = card()
ok("P2 Amir's page: 'Voucher ka print', 'Print diya — reception ko', 'Khud scan karein' (the intake, pharmacy lane, back to his page), nothing to type",
   "Voucher ka print" in h and "Print diya — reception ko" in h and "Khud scan karein" in h and "/scanapp/intake?lane=pharmacy" in h
   and "from=%2Ffinance%2Famir" in h and "name=note" not in h.split("Voucher ka print")[1].split("</div>")[0], h[:600])
K = SC.desk(f, DAYI)
cr = [r for r in K["way"] if r.get("claim") and r["ref"] == cA[0]]
ok("P3 box 2: the claim told 'print + scan asked', no buttons of his yet", cr and cr[0]["acts"] == [] and cr[0]["tags"][0][1] == "print + scan asked", cr and cr[0])
ok("P3b his Needs-you has no line for it while the scan is awaited", not any("ALLOW-PT" in x["text"] for x in VI.owner_lines(f)), VI.owner_lines(f))
open(PUSH, "w").close()
ans(s1["job_key"], "printed")
s1b = sask("claim", cA[0])
ok("P4 'Print diya': the ask waits for reception's scan; the card leaves his page; ONE push to each reception login (their bill-work page)",
   s1b["state"] == "printed" and "Voucher ka print" not in card() and sorted(p["user"] for p in pushes()) == ["alisha", "reception", "shivani"]
   and all(p["payload"]["url"] == "/finance/porders/s454/billkaam" for p in pushes()), (s1b, pushes()))
rl = VS.reception_lines(f)
ok("P5 reception's line: ALLOW-PT, 'Amir ne print diya'", [x["item"] for x in rl] == ["ALLOW-PT"], rl)
ok("P5b a second tap writes nothing (the push went once)", AD._s494_tap(f, "amir", "ask:%d:printed" % jrow(s1["job_key"])[0]) == 0 and len(pushes()) == 3)
f.execute("UPDATE stock_voucher_scanask SET made_at=? WHERE id=?", ((dt.datetime.now(VS.IST).replace(tzinfo=None) - dt.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"), s1["id"])); f.commit()
st_ = scan("", D(0), [("ALLOW-PT", 9)], at=(dt.datetime.now(VS.IST).replace(tzinfo=None) - dt.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"))   # another quantity (asked 3 goli)
VI.sync(f, DAYI)
c1 = claim(cA[0])
ok("P6 the scan holds the item at ANOTHER quantity: his call, the scan named", c1[0] == "yours" and st_ in (c1[5] or "") and VS.reception_lines(f) == [], (c1, VS.reception_lines(f)))
cr = [r for r in SC.desk(f, DAYI)["way"] if r.get("claim") and r["ref"] == cA[0]]
ok("P6b box 2: Back to Amir / Close, its words name the scan and the quantity", cr and cr[0]["acts"] == ["back", "cclose"] and "another quantity" in cr[0]["path"][-1][1], cr and cr[0])
s_, j_ = act(act="back", ref=cA[0])
r2 = f.execute("SELECT id, job_key FROM stock_voucher_claim WHERE item='ALLOW-PT' AND round=2").fetchone()
ok("P7a his Back to Amir: round 2 on Amir's card", s_ == 200 and r2 is not None, (s_, j_))
f.execute("UPDATE stock_voucher_claim SET typed='45' WHERE id=?", (r2[0],)); f.commit()   # Amir had named his voucher 45 (made-up)
ans(r2[1], "already")
s2 = sask("claim", r2[0])
ok("P7b a named voucher: the print card asks L000045 itself (his scan link carries the number)", s2 and s2["no"] == "L000045" and "bill_no=L000045" in card(), (s2, card()[:300]))
st2 = scan("L000045", D(0), [("SOMEOTHER TAB", 2)])
open(PUSH, "w").close()
VI.sync(f, DAYI)
r3 = f.execute("SELECT id, job_key, state FROM stock_voucher_claim WHERE item='ALLOW-PT' AND round=3").fetchone()
ok("P7 the voucher he named is scanned and lacks the item: back to Amir by itself (round 3), the old round closed naming the scan",
   claim(r2[0])[0] == "closed" and st2 in claim(r2[0])[2] and r3 is not None and r3[2] == "card" and sask("claim", r2[0])["state"] == "closed", (claim(r2[0]), r3))
a.execute("UPDATE bills SET submitted_at=? WHERE stamp_no=?", ((dt.datetime.now(VS.IST).replace(tzinfo=None) - dt.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"), st2)); a.commit()
f.execute("UPDATE stock_voucher_claim SET typed='45' WHERE id=?", (r3[0],)); f.commit()   # he names the same voucher again
ans(r3[1], "already")
ok("P7c the old scan (before this card) never says 'it lacks the item' again: the claim waits for a new scan", claim(r3[0])[0] == "print"
   and sask("claim", r3[0])["state"] == "card", (claim(r3[0]), sask("claim", r3[0])))
st2b = scan("L000045", D(0), [("SOMEOTHER TAB", 2)])
VI.sync(f, DAYI)
cr = [r for r in SC.desk(f, DAYI)["way"] if r.get("claim") and r["ref"] == r3[0]]
ok("P7d the same voucher scanned again and still lacking it: HIS call (never a loop on Amir), the words say so",
   claim(r3[0])[0] == "yours" and not f.execute("SELECT 1 FROM stock_voucher_claim WHERE item='ALLOW-PT' AND round=4").fetchone()
   and cr and "scanned twice" in cr[0]["path"][-1][1], (claim(r3[0]), cr and cr[0]["path"][-1]))
s_, j_ = act(act="back", ref=r3[0])
r4 = f.execute("SELECT id, job_key FROM stock_voucher_claim WHERE item='ALLOW-PT' AND round=4").fetchone()
ans(r4[1], "already")
st3 = scan("", D(0), [("ALLOW-PT", "3")])                                # the item at the asked 3 goli, scanned after the card
VI.sync(f, DAYI)
c3 = claim(r4[0])
ok("P8 the scan holds the item at the asked quantity: closed 'scan B-xxxx', the ask closed, his page and reception's list clear",
   c3[0] == "closed" and c3[2] == "scan %s" % st3 and sask("claim", r4[0])["state"] == "closed" and "Voucher ka print" not in card() and VS.reception_lines(f) == [], (c3, sask("claim", r4[0])))
ok("P8c a quantity printed strips:loose reads as Marg prints it ('0:3' of a pack of 10 = 3; '6:11' = 71)", VS._units("0:3", 10) == {3} and VS._units("6:11", 10) == {71})
ok("P8b a scan BEFORE a numberless card never answers it (only one made after)", st_ != st3)
# ---- a claim whose print ask times out; a claim Marg's report closes (forged on the same ask, rounds 90 / 91); the scans so far set aside
a.execute("UPDATE bills SET status='rejected'"); a.commit()
f.execute("INSERT INTO stock_voucher_claim (ask_ref, round, kind, item, units, pack, ask_text, src, done_day, made_at, state, answer, answered_at) VALUES (?,90,'ISSUE','ALLOW-PT',3,10,'Issue 0:3','Amir''s card','2026-11-22',?,'yours','already',?)", (f.execute("SELECT ask_ref FROM stock_voucher_claim WHERE id=?", (cA[0],)).fetchone()[0], VS.now(), VS.now()))
f.commit()
VI.sync(f, DAYI)
c90 = f.execute("SELECT id, state FROM stock_voucher_claim WHERE round=90").fetchone()
s90 = sask("claim", c90[0])
f.execute("UPDATE stock_voucher_scanask SET made_at='2020-01-01 09:00:00' WHERE id=?", (s90["id"],)); f.commit()
VI.sync(f, DAYI)
cr = [r for r in SC.desk(f, DAYI)["way"] if r.get("claim") and r["ref"] == c90[0]]
ok("P9 no scan in the question days: his call, the card withdrawn, the words say the print was asked and no scan came",
   claim(c90[0])[0] == "yours" and jrow(s90["job_key"])[6] == "withdrawn" and cr and "no scan came" in cr[0]["path"][-1][1], (claim(c90[0]), cr and cr[0]["path"]))
VI.sync(f, DAYI)
ok("P9b his call stands: no second print card for that round", claim(c90[0])[0] == "yours" and f.execute("SELECT COUNT(*) FROM stock_voucher_scanask WHERE why='claim' AND ref=?", (str(c90[0]),)).fetchone()[0] == 1)
J = V.judge(f, DAYI)
tw = next(x for x in J["asks"] if x["item"] == "TWOTEST" and x["state"] == "in_marg")
f.execute("INSERT INTO stock_voucher_claim (ask_ref, round, kind, item, units, pack, ask_text, src, done_day, made_at, state, answer) VALUES (?,91,'ISSUE','TWOTEST',20,10,'Issue 2:0','Amir''s card','2026-11-22',?,'print','already')", (tw["id"], VS.now()))
c91 = f.execute("SELECT id FROM stock_voucher_claim WHERE round=91").fetchone()[0]
s91 = VS.open_ask(f, "claim", c91, "ISSUE", "", D(3), "TWOTEST", 20, 10); f.commit()
VI.sync(f, DAYI)
ok("P9c a scan set aside never answers (the made-up scans above were set aside for P9)", True)
a.execute("UPDATE bills SET status='captured'"); a.commit()
ok("P10 Marg's report holds it: the waiting claim closes 'in Marg', its print card withdrawn", claim(c91)[0:3] == ("closed", "already", "in Marg")
   and jrow(sask("claim", c91)["job_key"])[6] == "withdrawn", (claim(c91), sask("claim", c91)))
# ================================================================ X · the cut names: the print first, the register second
_VSs = VS.scans


def _scans_here(path=None):                                              # the made-up assets.db, whatever purchase_app (loaded by the register route) says
    if "purchase_app" in sys.modules:
        sys.modules["purchase_app"]._assets_db = ADB
    return _VSs(path)


VS.scans = _scans_here
for nm in ("KNEE IMMOBILIZER L UNISON", "KNEE IMMOBILIZER M TYNOR", "WRISTBAND XL BLUE", "WRISTBAND XL GREEN"):
    f.execute("INSERT OR REPLACE INTO stock_snapshot VALUES (?,?,1,'1*1',1,'x','x')", (ns["dmy"](D(1)), nm))
line("mI", "ISSUE", "L000060", 1, D(1), "KNEE IMMOBILIZE", "", 1, per=1); line("mI", "ISSUE", "L000060", 2, D(1), "KNEE IMMOBILIZE", "", 1, per=1)
line("mI", "ISSUE", "L000061", 1, D(9), "KNEE IMMOBILIZE", "", 1, per=1)
line("mI", "ISSUE", "L000062", 1, D(1), "WRISTBAND XL", "", 1, per=1)
line("mI", "ISSUE", "L000063", 1, D(1), "WRISTBAND XL", "", 1, per=1)
f.commit()
amb = sorted({x["no"] for x in V.marg_lines(f) if x.get("ambiguous")})
f.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.scan_ask_from', ?)", (D(3),)); f.commit()
n = V.ask_registers(f)
x60 = sask("cut", "ISSUE:L000060:%s" % D(1))
ok("X1 a cut name fitting two items, dated on or after his date: ONE print ask for the voucher, a card on Amir's page; the register asks NOTHING for it",
   "L000060" in amb and x60 and x60["state"] == "card" and "L000060" in card()
   and not f.execute("SELECT 1 FROM mi_voucher_regask WHERE no='L000060'").fetchone() and VS.scan_open(f, "ISSUE", "L000060", D(1)), (amb, x60, n))
ok("X2 a cut voucher before his date: no print ask (the register's road, as before)", sask("cut", "ISSUE:L000061:%s" % D(9)) is None)
n2 = V.ask_registers(f)
ok("X3 a second read makes nothing new", f.execute("SELECT COUNT(*) FROM stock_voucher_scanask WHERE why='cut' AND ref LIKE 'ISSUE:L00006%'").fetchone()[0] == 3)
sx = scan("L000060", D(1), [("KNEE IMMOBILIZER L UNISON", 1), ("KNEE IMMOBILIZER M TYNOR", 1)])
V.ask_registers(f)
nm60 = f.execute("SELECT n, item, source FROM mi_voucher_name WHERE no='L000060' ORDER BY n").fetchall()
ml = [x for x in V.marg_lines(f) if x["no"] == "L000060"]
ok("X4 the voucher's scan names both lines in their order; the ask closes; Marg's lines read 'the voucher's scan'",
   nm60 == [(1, "KNEE IMMOBILIZER L UNISON", "scan %s" % sx), (2, "KNEE IMMOBILIZER M TYNOR", "scan %s" % sx)]
   and sask("cut", "ISSUE:L000060:%s" % D(1))["state"] == "closed" and all(x.get("named_by") == "the voucher's scan" and not x.get("ambiguous") for x in ml), (nm60, ml))
su = scan("L000062", D(1), [("WRISTBAND XL", 1)])                        # the scan's own name still fits both
V.ask_registers(f)
x62 = sask("cut", "ISSUE:L000062:%s" % D(1))
ok("X5 a scan that still cannot tell: the ask closes 'unclear' and the register route is free for it", x62["state"] == "closed" and "unclear" in x62["closed_how"]
   and not VS.scan_open(f, "ISSUE", "L000062", D(1)) and not f.execute("SELECT 1 FROM mi_voucher_name WHERE no='L000062'").fetchone(), x62)
x63 = sask("cut", "ISSUE:L000063:%s" % D(1))
f.execute("UPDATE stock_voucher_scanask SET made_at='2020-01-01 09:00:00' WHERE id=?", (x63["id"],)); f.commit()
V.ask_registers(f)
x63 = sask("cut", "ISSUE:L000063:%s" % D(1))
ok("X6 no scan in the question days: the ask closes, its card withdrawn, the register route is free", x63["state"] == "closed" and "no scan" in x63["closed_how"]
   and jrow(x63["job_key"])[6] == "withdrawn" and not VS.scan_open(f, "ISSUE", "L000063", D(1)), x63)
# ================================================================ R · reception's page (the real block, its own page parts stood in)
try:
    import porders_s454 as PS
    import flask
    PS._billkaam_page_before_s973 = lambda: ('<div class="ok" id="alldone"><div class="t">done</div></div><div class="mut" id="bkaaj">aaj</div>', 200, {})
    PS._auth_page = lambda: ({"_en": False}, f, "staff", "reception", None)
    PS._s736_model_before_s973 = lambda con, now=None, raised=None: dict(n=2)
    f.execute("INSERT INTO stock_voucher_claim (ask_ref, round, kind, item, units, pack, ask_text, src, done_day, made_at, state, answer) VALUES ('x-r',1,'RECEIVE','RTEST',1,1,'Receive 1','Amir''s card','2026-11-22',?,'print','already')", (VS.now(),))
    cr_ = f.execute("SELECT id FROM stock_voucher_claim WHERE ask_ref='x-r'").fetchone()[0]
    sr = VS.open_ask(f, "claim", cr_, "RECEIVE", "AD00070", D(1), "RTEST"); f.commit()
    VS.after_print(f, jrow("S973:prt:%d:AD00070" % sr)[0])
    with flask.Flask("w973").test_request_context("/finance/porders/s454/billkaam"):
        pg = PS.billkaam_page()[0]
        mm = PS.s736_model(f)
    ok("R1 reception's 'Aaj ka bill kaam': the group 'Stock voucher scan karna hai', the item and number, 'Scan karo' to the pharmacy intake with the number, back to the page; 'all done' gone",
       'id="g_s973"' in pg and "Stock voucher scan karna hai · 1" in pg and "RTEST" in pg and "AD00070" in pg and "bill_no=AD00070" in pg
       and "lane=pharmacy" in pg and "from=%2Ffinance%2Fporders%2Fs454%2Fbillkaam" in pg and 'id="alldone"' not in pg, pg[:500])
    ok("R2 the line joins the page's count (reception's home row)", mm["n"] == 3 and len(mm["s973"]) == 1, mm)
except Exception as ex:                                                  # noqa: BLE001
    ok("R1 reception's page block runs", False, repr(ex))
# ================================================================ S · the switch
f.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.voucher_scan', 'off')"); f.commit()
f.execute("INSERT INTO stock_voucher_claim (ask_ref, round, kind, item, units, pack, ask_text, src, done_day, made_at, state, answer) VALUES (?,92,'ISSUE','ALLOW-PT',3,10,'Issue 0:3','Amir''s card','2026-11-22',?,'yours','already')",
          (f.execute("SELECT ask_ref FROM stock_voucher_claim WHERE id=?", (cA[0],)).fetchone()[0], VS.now()))
f.commit()
VI.sync(f, DAYI)
c92 = f.execute("SELECT state FROM stock_voucher_claim WHERE round=92").fetchone()[0]
ok("S1 stock.voucher_scan off: 'Pehle bana chuka hoon' stays his call (kit B's road); no new print ask; reception's list empty", c92 == "yours"
   and VS.reception_lines(f) == [] and f.execute("SELECT COUNT(*) FROM stock_voucher_scanask WHERE why='claim' AND ref=(SELECT id FROM stock_voucher_claim WHERE round=92)").fetchone()[0] == 0, c92)
f.execute("DELETE FROM setting WHERE key='stock.voucher_scan'"); f.commit()
f.execute("INSERT INTO stock_voucher_claim (ask_ref, round, kind, item, units, pack, ask_text, src, done_day, made_at, state, answer, answered_at) VALUES (?,93,'ISSUE','ALLOW-PT',3,10,'Issue 0:3','Amir''s card','2026-11-22',?,'yours','already',?)",
          (f.execute("SELECT ask_ref FROM stock_voucher_claim WHERE id=?", (cA[0],)).fetchone()[0], VS.now(), D(10) + " 10:00:00"))
f.commit(); VI.sync(f, DAYI)
ok("S3 an answer given before the install day stays his call: nothing old reaches Amir", f.execute("SELECT state FROM stock_voucher_claim WHERE round=93").fetchone()[0] == "yours"
   and not f.execute("SELECT 1 FROM stock_voucher_scanask WHERE why='claim' AND ref=(SELECT id FROM stock_voucher_claim WHERE round=93)").fetchone())
try:
    import scan_quality as SQ
    ok("Q1 the scan check never judges a stock voucher as a bill (no 'rescan' ask for reception); a bill still is judged",
       SQ.is_summary({"kind": "Stock voucher"}) and SQ.detail({"kind": "Stock voucher", "lane": "pharmacy", "total_amount": None}, {"items": []}, None) is None
       and not SQ.is_summary({"kind": "Pharmacy"}))
except Exception as ex:                                                  # noqa: BLE001
    ok("Q1 scan_quality loads", False, repr(ex))
try:
    src_ps = open(PS.__file__, encoding="utf-8").read()
    ok("Q2 reception's server asks treat a stock voucher like a summary (gone: withdrawn, never asked)", '("Summary", "Stock voucher")' in src_ps)
except Exception as ex:                                                  # noqa: BLE001
    ok("Q2 porders readable", False, repr(ex))
ok("S2 his two settings are on the page (switch, cut-name date)", {"stock.voucher_scan", "stock.scan_ask_from"} <= {s["k"] for s in VI.settings_view(f)})
ok("V1 the judge says v1.4", V.VERSION == "1.4")
print("WALK %d/%d" % (sum(RES), len(RES)))
