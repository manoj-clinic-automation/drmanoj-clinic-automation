#!/usr/bin/env python3
"""walk_s976.py -- S976_WHOLE_UNIT_PACK (F-1742) on MADE-UP data only (no real file is read): a small spine and finance database built here.
    python3 walk_s976.py FIN_DIR MI_DIR KIT_DIR
FIN_DIR holds the finance files (the built ones, or the live ones for the control) with spine/ beside; MI_DIR holds marg_vouchers.py;
KIT_DIR holds fix_s976.py. Last line: WALK passed/total."""
import datetime as dt, json, os, sqlite3, subprocess, sys, tempfile
FIN, MI, KIT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, MI); sys.path.insert(0, os.path.join(FIN, "spine")); sys.path.insert(0, FIN)
RES = []


def ok(n, c, d=""):
    RES.append(bool(c)); print("%s  %s%s" % ("PASS" if c else "FAIL", n, ("  -- " + str(d)[:300]) if d and not c else ""))


W = tempfile.mkdtemp(prefix="walk976_")
SP, DB = os.path.join(W, "spine.db"), os.path.join(W, "finance.db")
os.environ["SPINE_DB"] = SP
T = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()
TI = T.isoformat()
import spine_build
s = sqlite3.connect(SP); s.executescript(spine_build.SCHEMA)
for n, p, u in (("WHOLETEST", "1*40", "LOOSE"), ("STRIPTEST", "1*10", "LOOSE"), ("GELTEST", "30GM", "WHOLE")):
    s.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (n, n, p, u, "2026-01-01", TI))
s.execute("INSERT INTO sp_meta VALUES ('built', ?)", (dt.datetime.now().isoformat(),)); s.commit(); s.close()

import stock_figure as SF, stock_watch as SW, voucher_judge as V, qty_words as QW, stock_check as SC
import marg_vouchers as MV
f = sqlite3.connect(DB)
f.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
f.execute("INSERT INTO setting VALUES ('stock.whole_unit_items', ?, '')", (json.dumps(["WHOLETEST = bottle"]),))
SW.ensure(f); f.commit()
sp = SW.Spine()
# ---------------------------------------------------------------- A the pack
ok("A1 stock_figure: a whole-unit item's pack is 1", SF.pack_of(f, sp, "WHOLETEST")[0] == 1, SF.pack_of(f, sp, "WHOLETEST"))
ok("A2 stock_figure: a strip item keeps its pack (10)", SF.pack_of(f, sp, "STRIPTEST")[0] == 10, SF.pack_of(f, sp, "STRIPTEST"))
ok("A3 stock_figure: the packing is still told (1*40)", SF.pack_of(f, sp, "WHOLETEST")[1] == "1*40")
g = sqlite3.connect(":memory:"); f.backup(g); g.execute("UPDATE setting SET value='[]' WHERE key='stock.whole_unit_items'")
ok("A4 the list governs: off the list the same item reads its packing's 40", SF.pack_of(g, sp, "WHOLETEST")[0] == 40, SF.pack_of(g, sp, "WHOLETEST"))
SF.pack_of(f, sp, "WHOLETEST")
ok("A5 the words read the list too (1 bottle, Hindi 1 botal)", QW.words(1, "1*40", pack=1, name="WHOLETEST") == "1 bottle" and QW.words(1, "1*40", pack=1, name="WHOLETEST", lang="hi") == "1 botal",
   (QW.words(1, "1*40", pack=1, name="WHOLETEST"),))
ok("A6 a database with no setting table: as before (40), never an error", SF.pack_of(sqlite3.connect(":memory:"), sp, "WHOLETEST")[0] == 40)
# ---------------------------------------------------------------- B Darpan's count screen
I = SW.item_info(f, sp, "WHOLETEST")
ok("B1 item_info: the whole-unit item pack 1 (one box)", I["pack"] == 1 and I["packing"] == "1*40", I)
ok("B2 item_info: the strip item pack 10 (Patte + Goli, as before)", SW.item_info(f, sp, "STRIPTEST")["pack"] == 10)
ok("B3 item_info: the gel pack 1 (Tube, as before)", SW.item_info(f, sp, "GELTEST")["pack"] == 1)
ok("B4 the box's word: Botal for the whole-unit item, Tube for the gel", QW.whole_word("1*40", None, "WHOLETEST", 1, "hi") == "botal" and QW.whole_word("30GM", None, "GELTEST", 1, "hi") == "tube")
ok("B5 the search's pack (Stock batao / Kuchh gadbad hai): 1 / 10", SW._s976_pack(f, "WHOLETEST", "1*40") == 1 and SW._s976_pack(f, "STRIPTEST", "1*10") == 10)
src = open(os.path.join(FIN, "stockmatch.py"), encoding="utf-8").read()
ok("B6 stockmatch's item search reads the whole-unit pack", 'pack = sw._s976_pack(con, it["name"], it["packing"])' in src and 'pack = sw.pack_of(it["packing"])' not in src)
f.execute("INSERT INTO stock_spot_roster (day,item_norm,item,reason,reason_hi,rank,asked_at,pack,packing) VALUES (?,?,?,?,?,?,?,?,?)", (TI, "WHOLETEST", "WHOLETEST", "x", "x", 1, TI + "T06:30:00", 40, "1*40"))
f.execute("INSERT INTO stock_spot_roster (day,item_norm,item,reason,reason_hi,rank,asked_at,pack,packing) VALUES (?,?,?,?,?,?,?,?,?)", (TI, "STRIPTEST", "STRIPTEST", "x", "x", 2, TI + "T06:30:00", 10, "1*10"))
f.commit()
RV = SW.build_roster(f, T)
rows = {r["item"]: r for r in (RV.get("items") if isinstance(RV, dict) else []) or []}
ok("B7 the morning list (already written): the whole-unit row reads pack 1, Botal; the strip row as before",
   rows.get("WHOLETEST", {}).get("pack") == 1 and rows.get("WHOLETEST", {}).get("whole_hi") == "botal" and rows.get("STRIPTEST", {}).get("pack") == 10, (list(rows), rows.get("WHOLETEST")))
ok("B8 the list's row in the database: pack 1 (what the screen posts with)", f.execute("SELECT pack FROM stock_spot_roster WHERE item='WHOLETEST'").fetchone()[0] == 1)
rid = f.execute("SELECT id FROM stock_spot_roster WHERE item='WHOLETEST'").fetchone()[0]
f.execute("UPDATE stock_spot_roster SET answered_at=?, qty_units=1 WHERE id=?", (TI + "T10:00:00", rid)); f.execute("UPDATE stock_spot_roster SET pack=40 WHERE id=?", (rid,)); f.commit()
SW.build_roster(f, T)
ok("B9 an ANSWERED row is never re-packed by the list (the fix script's job, audited)", f.execute("SELECT pack FROM stock_spot_roster WHERE id=?", (rid,)).fetchone()[0] == 40)
f.execute("UPDATE stock_spot_roster SET answered_at=NULL, qty_units=NULL, pack=1 WHERE id=?", (rid,)); f.commit()
# ---------------------------------------------------------------- C the voucher judge
f.execute("CREATE TABLE stock_voucher_line (id INTEGER PRIMARY KEY, count_id, round_no, kind, batch_no, batches_n, line_no, section, family, item, packing, "
          "pack, marg_from, change, marg_to, counted, rate_p, value_p, reason, made_by, made_at)")
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,packing,pack,change,made_at) VALUES (1,2,'ISSUE',3,'WHOLETEST','1*40',40,-3,'2026-09-27T12:59:13')")
f.execute("INSERT INTO stock_voucher_line (count_id,round_no,kind,batch_no,item,packing,pack,change,made_at) VALUES (1,2,'ISSUE',3,'STRIPTEST','1*10',10,-3,'2026-09-27T12:59:13')")
MV.ensure(f); MV._migrate(f)
f.execute("INSERT INTO mi_voucher_file (md5,kind,date_from,date_to,n_vouchers,n_lines,gross_p,bill_p,ok,note,stored_at,seq,exported) "
          "VALUES ('mI','ISSUE','2026-10-01',?,0,0,0,0,1,'','x',1,'20261126-145500')", (TI,))
f.execute("INSERT OR IGNORE INTO mi_voucher (md5,kind,no,day,cash,gross_p,bill_p,n_lines) VALUES ('mI','ISSUE','L000009','2026-10-15',1,0,0,2)")
for n, item, packing, per, q, u in ((1, "WHOLETEST", "1*40", 40, "3", 120), (2, "STRIPTEST", "1*10", 10, "3", 30)):
    f.execute("INSERT INTO mi_voucher_line (md5,kind,no,n,day,item,packing,per,batch,qty,units,unit,expiry,rate_p,value_p) VALUES ('mI','ISSUE','L000009',?,'2026-10-15',?,?,?,'B',?,?,'TAB','',100,100)",
              (n, item, packing, per, q, u))
f.commit()
ML = {d["item"]: d for d in V.marg_lines(f)}
ok("C1 Marg's voucher line of the whole-unit item: '3' read as 3 bottles, not 120", ML.get("WHOLETEST", {}).get("units") == 3, {k: (v.get("qty"), v.get("units")) for k, v in ML.items()})
ok("C1b ... told as 3, never '0:3' (its per is 1)", ML.get("WHOLETEST", {}).get("per") == 1 and V.st(ML["WHOLETEST"]["units"], ML["WHOLETEST"]["per"]) == "3", (ML.get("WHOLETEST", {}).get("per"),))
ok("C2 the strip item's line as before (3 strips = 30, per 10)", ML.get("STRIPTEST", {}).get("units") == 30 and ML.get("STRIPTEST", {}).get("per") == 10)
ok("C3 the judge's pack: 1 for the whole-unit item, 10 for the strip item", V._pack_of(f, "WHOLETEST") == 1 and V._pack_of(f, "STRIPTEST") == 10, (V._pack_of(f, "WHOLETEST"), V._pack_of(f, "STRIPTEST")))
J = V.judge(f)
a = [x for x in (J.get("asks") or []) if x.get("item") == "WHOLETEST"]
ok("C4 the judge: the 06-Sep ask of 3 bottles meets Marg's 3 (in Marg, never 'more than asked')", a and a[0].get("state") == "in_marg" and a[0].get("units") == 3, a[:1])
b0, b5 = V._whole_item_before_s976, V._whole_item_before_s975
try:
    V._whole_item_before_s976 = lambda R, item="", fresh_from=None: dict(v="look", pack=1, item="WHOLETEST", word="Marg counts WHOLETEST by the bottle, the stock record by a pack of 40 -- x")
    V._whole_item_before_s975 = lambda R, item="", fresh_from=None: dict(v="fresh_gap", pack=1, item="WHOLETEST", gap=1.0, base="28-11", gap_t="+1 bottle", marg_t="0", shelf_t="1")
    w1 = V.whole_item({}, "WHOLETEST")
    V._whole_item_before_s976 = lambda R, item="", fresh_from=None: dict(v="look", pack=40, item="WHOLETEST", word="Marg counts WHOLETEST by the bottle, the stock record by a pack of 40 -- x")
    w2 = V.whole_item({}, "WHOLETEST")
    V._whole_item_before_s976 = lambda R, item="", fresh_from=None: dict(v="look", pack=1, item="WHOLETEST", word="Marg's figure is behind a bill -- the purchase side is settled first")
    w3 = V.whole_item({}, "WHOLETEST")
finally:
    V._whole_item_before_s976, V._whole_item_before_s975 = b0, b5
ok("C5 S975's 'cannot be judged yet' retires once the pack is 1: a fresh surplus is 'surplus', grey", w1.get("v") == "surplus", w1)
ok("C6 while the record still says a pack above 1, S975's look stands", w2.get("v") == "look")
ok("C7 another 'look' (a bill behind Marg) is never touched", w3.get("v") == "look" and "behind a bill" in w3.get("word", ""))
# ---------------------------------------------------------------- D the one stored count
rid2 = f.execute("INSERT INTO stock_spot_roster (day,item_norm,item,reason,reason_hi,rank,asked_at,answered_at,qty_units,pack,packing) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 (TI, "WHOLETEST", "WHOLETEST", "x", "x", 3, TI + "T06:30:00", TI + "T10:52:00", 40, 40, "1*40")).lastrowid
cols = {r[1] for r in f.execute("PRAGMA table_info(stock_point)")}
if "judge_words" not in cols:
    f.execute("ALTER TABLE stock_point ADD COLUMN judge_words TEXT")
P1 = f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,roster_id,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
               ("WHOLETEST", "WHOLETEST", TI + "T10:52:00", 40, "spot", "darpan", 0, 40, "settled", rid2, "1 bottle more than Marg")).lastrowid
f.execute("UPDATE stock_spot_roster SET point_id=? WHERE id=?", (P1, rid2))
P0 = f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status) VALUES ('WHOLETEST','WHOLETEST','2026-09-06T12:00:00',5,'full_count','manoj',8,-3,'settled')").lastrowid
P2 = f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status) VALUES ('STRIPTEST','STRIPTEST',?,40,'spot','darpan',50,-10,'settled')", (TI + "T10:55:00",)).lastrowid
L1 = f.execute("INSERT INTO stock_watch_loss_line (at,item,gap_units,pack,packing,point_id) VALUES (?,?,?,?,?,?)", (TI + "T10:52:00", "WHOLETEST", -40, 40, "1*40", P1)).lastrowid
f.commit()
snap = lambda: json.dumps([f.execute("SELECT * FROM stock_point ORDER BY id").fetchall(), f.execute("SELECT * FROM stock_spot_roster ORDER BY id").fetchall(),
                           f.execute("SELECT * FROM stock_watch_loss_line ORDER BY id").fetchall()], default=str)
S0 = snap()


def fx(*a):
    r = subprocess.run([sys.executable, "-B", os.path.join(KIT, "fix_s976.py"), DB] + list(a), cwd=FIN, capture_output=True, text=True, env=dict(os.environ, SPINE_DB=SP))
    return (r.stdout + r.stderr).strip()


o = fx("--dry")
ok("D1 --dry names the one stored count (WHOLETEST 40/40) and writes nothing", o.startswith("WOULD n=1 WHOLETEST") and snap() == S0, o)
o = fx("--write")
pt = f.execute("SELECT qty_units, gap_units, expected_units, judge_words, note FROM stock_point WHERE id=?", (P1,)).fetchone()
ok("D2 --write: 40 -> 1 bottle, its gap with it (+1), the note says why", o.startswith("FIXED n=1 ids=%d" % P1) and pt[0] == 1 and pt[1] == 1 and "S976 (F-1742)" in (pt[4] or ""), (o, pt))
ok("D3 the morning-list row: 1, pack 1 (Galat likha? Badlo reads it right)", f.execute("SELECT qty_units, pack FROM stock_spot_roster WHERE id=?", (rid2,)).fetchone() == (1.0, 1))
ok("D4 its loss line with it (-40 -> -1, pack 1)", f.execute("SELECT gap_units, pack FROM stock_watch_loss_line WHERE id=?", (L1,)).fetchone() == (-1.0, 1))
ok("D5 the 06-Sep full count (stored in bottles) and the strip item's count are untouched",
   f.execute("SELECT qty_units FROM stock_point WHERE id=?", (P0,)).fetchone()[0] == 5 and f.execute("SELECT qty_units FROM stock_point WHERE id=?", (P2,)).fetchone()[0] == 40)
S1 = snap()
o = fx("--write")
ok("D6 --write again: nothing (a fixed count is never divided twice)", o.startswith("FIXED n=0") and snap() == S1, o)
o = fx("--undo")
ok("D7 --undo: every row back exactly as it was", o.startswith("UNDONE rows=3") and snap() == S0, o)
o = fx("--write")
ok("D8 --write after an undo: the same fix again", o.startswith("FIXED n=1") and snap() == S1, o)
for i in range(4):
    f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status) VALUES ('WHOLETEST','WHOLETEST',?,80,'darpan','darpan',0,80,'settled')", (TI + "T11:0%d:00" % i,))
f.commit(); S2 = snap()
o = fx("--write")
ok("D9 more than 3 such counts: refused, nothing written (never a mass rewrite)", o.startswith("REFUSED 4") and snap() == S2, o)
f.execute("DELETE FROM stock_point WHERE source='darpan' AND item='WHOLETEST' AND qty_units=80"); f.commit()
r3 = f.execute("INSERT INTO stock_spot_roster (day,item_norm,item,reason,reason_hi,rank,asked_at,answered_at,qty_units,pack,packing) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
               (TI, "WHOLETEST", "WHOLETEST", "x", "x", 4, TI + "T06:30:00", TI + "T12:00:00", 40, 1, "1*40")).lastrowid
f.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,roster_id) VALUES ('WHOLETEST','WHOLETEST',?,40,'spot','darpan',0,40,'settled',?)", (TI + "T12:00:00", r3))
f.commit(); S3 = snap()
o = fx("--write")
ok("D10 a count whose list row already asked in bottles (pack 1) is a true count: never divided", o.startswith("FIXED n=0") and snap() == S3, o)
o = fx("--undo"); o = fx("--write")
f.execute("UPDATE stock_spot_roster SET pack=7 WHERE id=?", (rid2,)); f.commit()
o = fx("--undo")
ok("D11 undo leaves a row changed since the fix as it stands (the list row), puts back the rest",
   "left (changed since the fix): stock_spot_roster %d" % rid2 in o and f.execute("SELECT qty_units FROM stock_point WHERE id=?", (P1,)).fetchone()[0] == 40, o)
r9 = f.execute("INSERT INTO stock_spot_roster (day,item_norm,item,reason,reason_hi,rank,asked_at,pack,packing) VALUES (?,?,?,?,?,?,?,?,?)", (TI, "WHOLETEST", "WHOLETEST", "x", "x", 5, TI + "T06:30:00", 40, "1*40")).lastrowid
f.execute("INSERT INTO s976_fix (at, tbl, row_id, before_json, after_json) VALUES (?, 'stock_spot_roster', ?, ?, ?)", (TI, r9, json.dumps(dict(id=r9, pack=40, qty_units=None)), json.dumps(dict(pack=1))))
f.execute("UPDATE stock_spot_roster SET pack=1, answered_at=?, qty_units=2 WHERE id=?", (TI + "T13:00:00", r9)); f.commit()
o = fx("--undo")
ok("D12 a list row re-packed at install and answered since (2 bottles) is never put back to pack 40", f.execute("SELECT pack FROM stock_spot_roster WHERE id=?", (r9,)).fetchone()[0] == 1 and "stock_spot_roster %d" % r9 in o, o)
# ---------------------------------------------------------------- E Stock check's band 2 in bottles (D1107)
b0 = SC._s975_count_row_before_s976
try:
    SC._s975_count_row_before_s976 = lambda con, VJ, J, RR, P, rowmap, WOP, b1: dict(pack=P["pk"], fig="counted %g · Marg %g · x" % (P["qty"], P["expected"]),
                                                                                  path=[["ok", "Darpan's count at x: %g counted, Marg %g at the time." % (P["qty"], P["expected"])]])
    PW = dict(item="WHOLETEST", qty=1.0, expected=2.0, source="darpan", at=TI + "T10:52:00", pk=1)
    e1 = SC._s975_count_row(f, None, None, None, PW, {}, {}, {})
    e2 = SC._s975_count_row(f, None, None, None, dict(PW, qty=3.0, expected=2.0), {}, {}, {})
    e3 = SC._s975_count_row(f, None, None, None, dict(PW, item="GELTEST"), {}, {}, {})
    e4 = SC._s975_count_row(f, None, None, None, dict(PW, pk=40), {}, {}, {})
finally:
    SC._s975_count_row_before_s976 = b0
ok("E1 band 2: a whole-unit count at pack 1 reads 'counted 1 bottle · Marg 2 bottles · −1 bottle'", e1["fig"] == "counted 1 bottle · Marg 2 bottles · −1 bottle", e1["fig"])
ok("E2 ... and its first path line in bottles", "1 bottle counted, Marg 2 bottles at the time" in e1["path"][0][1], e1["path"])
ok("E3 a surplus reads '+1 bottle'", e2["fig"].endswith("· +1 bottle"), e2["fig"])
ok("E4 a gel (not on the list) as before", e3["fig"] == "counted 1 · Marg 2 · x", e3["fig"])
ok("E5 while the record still says a pack above 1, S975's own words stand", e4["fig"] == "counted 1 · Marg 2 · x", e4["fig"])
print("WALK %d/%d" % (sum(RES), len(RES)))
