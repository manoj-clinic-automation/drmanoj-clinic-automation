#!/usr/bin/env python3
"""walk_s975.py -- S975_STOCKCHECK_V10 on MADE-UP data only: kit B's own walk fixture (walk_s971.py, run whole, its checks counted apart),
then the three bands, F-1738 and F-1739 on it. No real file is read.
    python3 walk_s975.py FIN_DIR MI_DIR WALK_S971
FIN_DIR holds the finance files (the built ones, or the live ones for the control) with spine/ beside; MI_DIR holds marg_vouchers.py.
Last line: WALK passed/total."""
import json, os, sqlite3, sys

FIN, MI, W971 = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(W971, encoding="utf-8").read()
END = 'print("WALK %d/%d" % (sum(RES), len(RES)))'
head = src[:src.rindex(END)]
ns = {"__name__": "__walk971__", "__file__": W971}
sys.argv = [W971, FIN, MI]
exec(compile(head, W971, "exec"), ns)                                    # kit B's fixture and all its checks (printed, not counted here)
HEAD_RES = list(ns["RES"])
RES = []


def ok(n, c, d=""):
    RES.append(bool(c)); print("%s  %s%s" % ("PASS" if c else "FAIL", n, ("  -- " + str(d)[:300]) if d and not c else ""))


print("---- (kit B's own checks above: %d/%d) ---- S975 ----" % (sum(HEAD_RES), len(HEAD_RES)))
f, SC, V, IL, SW, D, DAYI, T = ns["f"], ns["SC"], ns["V"], ns["IL"], ns["SW"], ns["D"], ns["DAYI"], ns["T"]
norm = SC.norm


def mem(src_con):
    g = sqlite3.connect(":memory:"); src_con.backup(g); return g


SC._DCACHE["v"] = None
K = SC.desk(f, DAYI)
ok("V1 the desk answers the three bands, v1.9", K.get("ok") and K.get("v10") and K.get("version") == "1.9"
   and all(k in K for k in ("band1", "band1_foot", "band2", "earlier", "week", "way3", "v10_totals", "counters", "allow_items")), (K.get("v10"), K.get("v10_reason"), K.get("version")))
if not K.get("v10"):
    ok("B0 the bands (none: the checks B and C cannot run)", False)
else:
    B0 = SC._desk_before_s975(f, DAYI)
    same = [k for k in ("box1", "allow", "way", "moves", "settled", "recount", "noted", "inquiry", "inquiry_done", "settings", "totals")
            if json.dumps(K.get(k), sort_keys=True, default=str) != json.dumps(B0.get(k), sort_keys=True, default=str)]
    ok("V2 every box of the desk is as before (the desk's writes and the earlier walks read them)", same == [], same)
    LR = ns["VI"].losses(f)
    openl = [x["item"] for m in LR["months"] for x in m["lines"] if not x["withdrawn"] and not x["marg"][:1].isupper() or x["marg"].startswith("on Amir") or x["marg"].startswith("Amir done")]
    b1 = {r["item"]: r for r in K["band1"]}
    ok("B1 band 1 = his write-offs not yet in Marg (the loss register's open lines); a withdrawn one is not there", "ALLOWTEST" in b1 and "TWOTEST" not in b1, (list(b1), openl))
    a = b1.get("ALLOWTEST") or {}
    ok("B2 a row: written off, booked, the card's name, its state, the 3-step track, its cost; folds to its path",
       a.get("card") == "STOCK ISSUE · %s-%s" % (D(3)[8:10], D(3)[5:7]) and a.get("card_state") == "3 days — not done" and a.get("tags", [[""]])[0][0] == "red"
       and [s[1].split(" ·")[0] for s in a.get("track", [])] == ["Booked " + D(3)[8:10] + "-" + D(3)[5:7], "Amir keys it", "In Marg"]
       and len(a.get("path", [])) >= 4 and "closes by itself" in a["path"][-1][1], a)
    ok("B3 the month's totals under band 1 = the loss register's", K["band1_foot"] and K["band1_foot"]["n"] == LR["months"][0]["n"] and K["band1_foot"]["cost_t"] == LR["months"][0]["cost_t"], (K["band1_foot"], LR["months"][0]["n"]))
    ok("B4 no row twice: a band-1 item stays in way3 only while another correction of it is on its way (here its two batch fixes), told 'your write-off: band 1 above'",
       all(any("band 1 above" in t[1] for t in r["tags"]) for r in K["way3"] if r["item"] in b1 and not r.get("claim")) and [r for r in K["way3"] if r["item"] == "ALLOWTEST"], [(r["item"], r["tags"]) for r in K["way3"]])
    ok("B5 the claim rows stay in way3 (kit B / kit C)", [r for r in K["way3"] if r.get("claim")] == [r for r in K["way"] if r.get("claim")])
    g = mem(f)
    g.execute("UPDATE amir_job SET done_at=?, done_how='tap' WHERE key=?", (D(1) + " 18:00:00", a.get("ref") or "S969:wo:%s:1:ALLOWTEST" % D(3))); g.commit()
    a2 = {r["item"]: r for r in SC.desk(g, DAYI)["band1"]}.get("ALLOWTEST") or {}
    ok("B6 Amir's Kar diya: 'Kar diya dd-mm — the next report decides', the track's second step done; still in band 1 until Marg shows it",
       a2.get("done") and a2.get("card_state", "").startswith("Kar diya %s-%s" % (D(1)[8:10], D(1)[5:7])) and a2["track"][1][0] == "ok" and a2["tags"][0][0] in ("amb", "red"), a2)
    g.execute("UPDATE amir_job SET done_how='withdrawn' WHERE key=?", ("S969:wo:%s:1:ALLOWTEST" % D(3),)); g.commit()
    ok("B7 a withdrawn write-off leaves band 1", "ALLOWTEST" not in {r["item"] for r in SC.desk(g, DAYI)["band1"]})
    J0 = V.judge
    def J_inmarg(con, day=None):
        J = J0(con, day)
        for x in J.get("asks") or []:
            if str(x.get("ref") or "").startswith("S969:wo:") and x["item"] == "ALLOWTEST":
                x["state"], x["match"] = "in_marg", dict(no="L000099", day=D(1), item="ALLOWTEST")
        return J
    V.judge = J_inmarg
    try:
        gone = "ALLOWTEST" not in {r["item"] for r in SC.desk(f, DAYI)["band1"]}
    finally:
        V.judge = J0
    ok("B8 in Marg's report: it leaves band 1 (the loss register keeps it)", gone)
    v = SC._desk_before_s975(f, DAYI)
    v["way"] = list(v["way"]) + [dict(item="ALLOWTEST", key="", pack=10, acts=["wd"], ref="S969:wo:x", box="way", tags=[["red", "a later count agrees with Marg — not to be keyed"]],
                                       path=[["ok", "Written off from this desk"], ["now", "Withdraw takes it off his card."]])]
    v["old"] = list(v.get("old") or []) + [dict(item="ALLOWTEST", verdict="fresh_gap", tags=[["red", "today's gap"]], path=[["now", "Today's gap is already on Amir's card (box 2)."]])]
    X = SC._s975_bands(f, v, DAYI)
    xa = {r["item"]: r for r in X["band1"]}.get("ALLOWTEST") or {}
    ok("B9b (second look 5) Withdraw once: not on the way3 copy when it moved to band 1", not [r for r in X["way3"] if r["item"] == "ALLOWTEST" and "wd" in (r.get("acts") or [])], [(r["item"], r.get("acts")) for r in X["way3"] if r["item"] == "ALLOWTEST"])
    ok("B9 Withdraw (a later count agrees with Marg) moves onto the band-1 row with its red tag; the box-2 row leaves way3",
       xa.get("acts") == ["wd"] and xa.get("ref") == "S969:wo:x" and any("not to be keyed" in t[1] for t in xa.get("tags", []))
       and not [r for r in X["way3"] if r["item"] == "ALLOWTEST" and "wd" in (r.get("acts") or []) and not any("band 1 above" in t[1] for t in r["tags"])], xa)
    ga = mem(f); ga.execute("UPDATE stock_of_record SET base_at=? WHERE item='ALLOWTEST'", (D(0) + "T08:00:00",)); ga.commit()
    va = SC._desk_before_s975(ga, DAYI)
    va["old"] = list(va.get("old") or []) + [dict(item="ALLOWTEST", verdict="fresh_gap", tags=[["red", "today's gap"]], path=[["now", "Today's gap waits for your call."]])]
    SC._s975_bands(ga, va, DAYI)
    ov = [r for r in va["old"] if r["item"] == "ALLOWTEST"][-1]
    ok("B10a box 3: today's gap on a LATER count than the one he wrote off stays as it was (red)", ov["tags"][0][0] == "red", ov)
    gb = mem(f); pat_ = gb.execute("SELECT point_at FROM stock_desk_action WHERE kind='writeoff' AND item='ALLOWTEST'").fetchone()[0]
    gb.execute("UPDATE stock_of_record SET base_at=? WHERE item='ALLOWTEST'", (pat_,)); gb.commit()
    vb = SC._desk_before_s975(gb, DAYI)
    vb["old"] = list(vb.get("old") or []) + [dict(item="ALLOWTEST", verdict="fresh_gap", tags=[["red", "today's gap"]], path=[["now", "Today's gap is already on Amir's card (box 2)."]])]
    SC._s975_bands(gb, vb, DAYI)
    ov = [r for r in vb["old"] if r["item"] == "ALLOWTEST"][-1]
    ok("B10b box 3: today's gap standing on the very count he wrote off is told as band 1's, never red", ov["tags"][0][0] == "blu" and "band 1" in ov["path"][0][1], ov)
    def J_other(con, day=None):
        J = J0(con, day)
        J["asks"] = list(J.get("asks") or []) + [dict(item="ALLOWTEST", forms=["ALLOWTEST"], state="waiting", ref="fix:x:ALLOWTEST", src="job", jobs=["fix:x"], day=D(2))]
        return J
    v2 = SC._desk_before_s975(f, DAYI)
    v2["way"] = list(v2["way"]) + [dict(item="ALLOWTEST", key="", pack=10, acts=[], box="way", tags=[["blu", "waiting on Amir"]], path=[])]
    V.judge = J_other
    try:
        X2 = SC._s975_bands(f, v2, DAYI)
    finally:
        V.judge = J0
    ok("B11 an item that waits on another correction too keeps its way3 row, told 'your write-off: band 1 above'",
       any(r["item"] == "ALLOWTEST" and any("band 1 above" in t[1] for t in r["tags"]) for r in X2["way3"]), [(r["item"], r["tags"]) for r in X2["way3"]])
    # ---- band 2: today's counts, one verdict each
    g = mem(f)
    g.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('stock.whole_unit_items', '[\"WHOLETEST = bottle\"]')")
    cols = [r[1] for r in g.execute("PRAGMA table_info(stock_of_record)")]
    def rec(item, pack, marg, shelf, gap, kind="darpan"):
        d = dict(item=item, k20=item, pack=pack, pieces=0, ortho=0, consumable=0, marg_units=marg, marg_closing=marg, marg_flag="", shelf_units=shelf, base_kind=kind,
                 base_day=DAYI, base_at=DAYI + "T10:00:00", gap_units=gap, state="look" if gap else "agree", words="", approx=0, forms_json="[]")
        g.execute("INSERT OR REPLACE INTO stock_of_record (%s) VALUES (%s)" % (",".join(k for k in d if k in cols), ",".join("?" for k in d if k in cols)), [d[k] for k in d if k in cols])
    def pt(item, at, q, e, gp, status="settled", words="", src_="darpan"):
        g.execute("INSERT INTO stock_point (item_norm,item,at,qty_units,source,by,expected_units,gap_units,status,judge_words) VALUES (?,?,?,?,?,?,?,?,?,?)",
                  (SW.norm_name(item), item, at, q, src_, "darpan", e, gp, status, words))
        return g.execute("SELECT last_insert_rowid()").fetchone()[0]
    rec("WHOLETEST", 40, 0, 40, 40); pt("WHOLETEST", DAYI + "T10:49:00", 40, 0, 40, words="1:0 more than Marg -- noted, never a loss")
    rec("SURPTEST2", 10, 20, 30, 10); pt("SURPTEST2", DAYI + "T10:50:00", 30, 20, 10)
    pt("EVETEST", DAYI + "T18:10:00", 15, 20, -5, status="awaits_sales")
    pt("SUPERTEST", DAYI + "T10:51:00", 1, 50, -49, status="superseded")
    pt("WEEKTEST", D(3) + "T10:00:00", 12, 12, 0)
    pt("OLDWEEK", D(9) + "T10:00:00", 12, 12, 0)
    g.commit()
    SC._DCACHE["v"] = None
    K2 = SC.desk(g, DAYI)
    b2 = {r["item"]: r for r in K2["band2"]}
    w = b2.get("WHOLETEST") or {}
    ok("C1 band 2 holds every count of today, newest first; a replaced count is not there", {"WHOLETEST", "SURPTEST2", "EVETEST", "TWOTEST"} <= set(b2) and "SUPERTEST" not in b2
       and [r["time"] for r in K2["band2"]] == sorted([r["time"] for r in K2["band2"]], reverse=True), [(r["item"], r["time"]) for r in K2["band2"]])
    ok("C2 a whole-unit item (CCM = bottle) is told in its bottles: '1 bottle counted', '+1 bottle', never a loss",
       w.get("fig") == "counted 1 bottle · Marg 0 bottles · +1 bottle" and w.get("verdict") == "surplus" and any("never a loss" in t[1] for t in w.get("tags", [])), w.get("fig"))
    s2 = b2.get("SURPTEST2") or {}
    ok("C3 a surplus: 'more than Marg — never a loss', no button; the page adds the delivery line from Marg's purchases-to day",
       s2.get("verdict") == "surplus" and s2.get("surplus") and not s2.get("acts") and s2.get("fig") == "counted 3:0 · Marg 2:0 · +1:0", s2)
    ok("C4 an evening count waits for the day's sales; a count that agrees says so", (b2.get("EVETEST") or {}).get("verdict") == "awaits" and (b2.get("TWOTEST") or {}).get("verdict") == "agree",
       [(k, x["verdict"]) for k, x in b2.items()])
    ok("C5 this week's earlier counts are in the fold (7 days), older ones are not", "WEEKTEST" in {r["item"] for r in K2["week"]} and "OLDWEEK" not in {r["item"] for r in K2["week"]})
    P = dict(id=999001, item="LOSSTEST", at=DAYI + "T11:00:00", qty=40, expected=60, gap=-20, source="darpan", status="settled", words="2:0 below Marg -- a loss since the last count", by="darpan")
    rm = {999001: dict(item="LOSSTEST", box="short", acts=["wo", "pu"], short_t="2:0", tags=[], path=[["ok", "Darpan's count"], ["now", "Your call"]], pid=999001)}
    L = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), P, rm, set(), {})
    ok("C6 a loss since the last count: red 'your call', its own Write off / Pursue (the desk's row)", L["verdict"] == "loss" and L["acts"] == ["wo", "pu"] and L["tags"][0] == ["red", "a loss since the last count — your call"], L)
    L2 = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), P, {}, {999001}, {})
    L2b = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), P, {}, set(), {"LOSSTEST": [dict(day=D(1), at=D(1) + "T12:00:00")]})
    ok("C7b (cold review 3) a later loss of an item written off earlier is NOT told 'written off'", L2b["verdict"] != "wo", L2b)
    L2c = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), dict(P, at=D(2) + "T11:00:00"), {}, set(), {"LOSSTEST": [dict(day=D(1), at=D(1) + "T12:00:00")]})
    ok("C7c a count before his write-off is told 'before your write-off of dd-mm'", L2c["verdict"] == "before_wo", L2c)
    ok("C7 a count he has written off: 'written off by you — above', no button", L2["verdict"] == "wo" and not L2["acts"] and L2["tags"][0][1] == "written off by you — above", L2)
    L2d = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), dict(P, at=D(1) + "T18:30:00", status="awaits_sales"), {}, set(), {"LOSSTEST": [dict(day=D(1), at=D(1) + "T12:00:00")]})
    ok("C7d (second look 6) an evening count saved after the tap, the same day, is not 'before your write-off'", L2d["verdict"] == "awaits", L2d["verdict"])
    L2e = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), P, {}, {999001: "in Marg"}, {})
    L2f = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), P, {}, {999001: "withdrawn"}, {})
    ok("C7e (second look 1) a count whose write-off is in Marg / withdrawn never says 'above'", "above" not in L2e["tags"][0][1] and "in Marg" in L2e["tags"][0][1] and "withdrawn" in L2f["tags"][0][1], (L2e["tags"], L2f["tags"]))
    L2g = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), dict(P, status="recounted"), {}, set(), {})
    ok("C7f (second look 2) a recounted count says so, never a live loss", L2g["verdict"] == "recounted", L2g["verdict"])
    rm2 = {999001: dict(item="LOSSTEST", box="allow", wo_ok=True, tags=[["gry", "within the allowance (0:5)"]], path=[["now", "Within your allowance"]], pid=999001)}
    L3 = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), P, rm2, set(), {})
    rec("WHOLETEST", 40, 5, 160, 155); g.commit()
    Pw = dict(id=999002, item="WHOLETEST", at=DAYI + "T11:05:00", qty=160, expected=5, gap=155, source="darpan", status="settled", words="", by="darpan")
    Lw = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), Pw, {}, set(), {})
    ok("C12 (second look 3) CCM: 4 bottles counted against Marg's 5 is a loss of 1 bottle, told amber (the record cannot judge it yet), never 'never a loss'",
       Lw["verdict"] == "unit_loss" and Lw["fig"] == "counted 4 bottles · Marg 5 bottles · −1 bottle" and "never a loss" not in str(Lw["tags"]), (Lw["verdict"], Lw["fig"]))
    Lu = SC._s975_count_row(g, V, V.judge(g, DAYI), V.record_rows(g), dict(Pw, qty=5, gap=0), {}, set(), {})
    ok("C13 (second look 4) a CCM count that is not whole packs is not compared (no mixed units)", Lu["verdict"] == "unit" and Lu["fig"].endswith("not compared"), Lu["fig"])
    ok("C8 within the allowance: amber, no button of its own (the group button acts)", L3["verdict"] == "allow" and L3["tags"][0][0] == "amb" and not L3["acts"], L3)
    ok("C9 every box-1 and allowance row stays visible -- today's in band 2, every other one in 'earlier' with its buttons; none in the week fold too",
       {r["item"] for r in K2["box1"] + K2["allow"]} <= {r["item"] for r in K2["earlier"]} | {r["item"] for r in K2["band2"]}
       and not ({r.get("pid") for r in K2["earlier"]} & {r.get("pid") for r in K2["week"]}), ([r["item"] for r in K2["earlier"]], [r["item"] for r in K2["box1"]], [r["item"] for r in K2["allow"]]))
    vx = SC._desk_before_s975(f, DAYI)
    vx["box1"] = list(vx["box1"]) + [dict(item="PURSUETEST", key="", pack=10, pid=888001, pat=D(12) + "T10:00:00", acts=[], box="short", tags=[["amb", "Pursue — on Darpan's list"]], path=[])]
    X3 = SC._s975_bands(f, vx, DAYI)
    ok("C11 (cold review MUST) a box-1 row with no buttons and a count 12 days old -- a Pursue waiting on Darpan -- stays on the page", any(r["item"] == "PURSUETEST" for r in X3["earlier"]), [r["item"] for r in X3["earlier"]])
    ok("C10 the group button's items = the allowance rows it may write off", K2["allow_items"] == [r["item"] for r in K2["allow"] if r.get("wo_ok")])
# ---- F-1738: a fresh surplus is never 'today's gap -- waits for your call'
R0 = dict(item="X", pack=10, gap_units=10, marg_units=0, shelf_units=10, base_kind="darpan", base_day=DAYI, marg_flag="", state="look")
QW0 = __import__("qty_words"); QW0.set_whole_units(["WHOLEJ = bottle"])
ok("F1b (second look 3, re-look B) a whole-unit item (CCM) is never 'surplus' nor red on the stored figure: 'look' -- cannot be judged yet",
   V.whole_item(dict(R0, item="WHOLEJ"))["v"] == "look" and V.whole_item(dict(R0, item="WHOLEJ", gap_units=-10))["v"] == "look" and "cannot be judged yet" in V.whole_item(dict(R0, item="WHOLEJ"))["word"])
ok("F1 whole_item: a fresh count with more on the shelf than in Marg is 'surplus', never a loss; a fresh short stays 'today's gap'",
   V.whole_item(R0)["v"] == "surplus" and "never a loss" in V.whole_item(R0)["word"] and V.whole_item(dict(R0, gap_units=-10))["v"] == "fresh_gap" and V.V_WORD.get("surplus"), V.whole_item(R0))
old0 = [r for r in K["old"]]
it = next((r["item"] for r in old0 if r.get("verdict") in ("count_first", "fresh_gap", "look")), None)
if it:
    g = mem(f)
    g.execute("UPDATE stock_of_record SET base_kind='darpan', base_day=?, base_at=?, marg_flag='', gap_units=5, state='look', shelf_units=COALESCE(marg_units,0)+5 WHERE item=?",
              (DAYI, DAYI + "T10:00:00", it)); g.commit()
    o = [r for r in SC.desk(g, DAYI)["old"] if r["item"] == it]
    ok("F2 box 3 (CCM, 28-11): the surplus is grey 'more than Marg — noted', no red, nothing waits for his call",
       o and o[0]["verdict"] == "surplus" and o[0]["tags"][0][0] == "gry" and not any("waits for your call" in p[1] for p in o[0]["path"]) and o[0]["path"][-1][0] in ("ok",)
       or (o and o[0]["verdict"] == "surplus" and not any(p[0] == "now" and "Whole item" in p[1] for p in o[0]["path"])), o)
else:
    ok("F2 box 3 (CCM, 28-11): an old row to test on", False, [r["item"] for r in old0])
# ---- F-1739: the ledger's count line of a whole-unit item in its bottles
import qty_words as QW
QW.set_whole_units(["WHOLETEST = bottle"])
U = IL.Unit("1*40", "WHOLE", "WHOLETEST")
e = IL._count_entry(dict(qty=40, expected=0, gap=40, status="", source="spot", words="1:0 more than Marg", by="darpan", at=DAYI + "T10:49", pack=40), U)
ok("G1 CCM's 28-11 count: '1 bottle counted', '1 bottle more' (was '40 bottles counted, 40 bottles more'), what the screen stored kept in its words",
   e.get("counted_t") == "1 bottle" and e.get("mark") == "1 bottle more" and "stored 1:0" in e.get("words", ""), e)
Us = IL.Unit("1*10", "LOOSE", "STRIPTEST")
c0 = dict(qty=25, expected=30, gap=-5, status="", source="darpan", words="", by="darpan", at=DAYI + "T10:00", pack=10)
ok("G2 a strip item's count reads exactly as before", IL._count_entry(c0, Us) == IL._count_entry_before_s975(c0, Us))
c1 = dict(c0, qty=30, pack=40)
ok("G3 a whole-unit count that is not whole packs is left as stored (nothing guessed)", "counted_t" not in IL._count_entry(c1, U))
g = mem(f); rec_ok = True
try:
    g.execute("INSERT OR REPLACE INTO stock_of_record (item, k20, pack) VALUES ('WHOLETEST', 'WHOLETEST', 40)"); g.commit()
except sqlite3.Error:
    rec_ok = False
ok("G4 the ledger's counts carry the record's pack", rec_ok and IL._s975_pack(g, "WHOLETEST") == 40 and IL._s975_pack(g, "NOTHERE") == 1)
srcL = open(IL.__file__, encoding="utf-8").read()
ok("G5 both of the ledger's count lines (the fold and the page) read the count's own words", srcL.count('e.get("counted_t") or U.fmt(e["counted"])') == 2)
# ---- the page
appx = ns["flask"].Flask("w975"); SC.init(appx, lambda: f, lambda *r: ({"user": "manoj"}, None) if ("checker" in r or "maker" in r) else (None, ("no", 403))); cx = appx.test_client()
pg = cx.get("/finance/stockcheck/").get_data(as_text=True)
ok("P1 the page draws the bands and keeps the boxes as its folds; no confirm / alert / prompt",
   all(x in pg for x in ("function renderDeskV9(el)", "function renderDesk()", "function b1row", "id=\"band1\"", "id=\"band2\"", "b3way", "b3rec", "Open the full loss register"))
   and "confirm(" not in pg and "alert(" not in pg and "prompt(" not in pg)
hz = cx.get("/finance/stockcheck/api/healthz").get_json()
ok("P2 healthz v1.9", hz.get("version") == "1.9", hz)
j = cx.get("/finance/stockcheck/api/desk?fresh=1").get_json()
ok("P3 /api/desk carries the bands (the owner)", j.get("ok") and j.get("v10") and isinstance(j.get("band1"), list) and j.get("can_write") is not None, j.get("v10_reason"))
print("WALK %d/%d" % (sum(RES), len(RES)))
