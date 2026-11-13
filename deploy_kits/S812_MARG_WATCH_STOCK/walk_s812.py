#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s812.py FINANCE_DIR SPINE_DB FINANCE_DB -- kit S812's walk on COPIES (never the live files): the engine and section A.
Every check prints PASS / FAIL; the last line is 'WALK n/m'. Run against the old marg_hand_change.py it must go red (the control)."""
import os, shutil, sqlite3, sys, tempfile

FIN, SPINE, DB = sys.argv[1:4]
sys.path.insert(0, FIN)
os.environ["SPINE_DB"] = SPINE
import marg_hand_change as H                                      # noqa: E402

ok = tot = 0


def check(name, cond):
    global ok, tot
    tot += 1
    ok += bool(cond)
    print("%s  %s" % ("PASS" if cond else "FAIL", name))


COUNTED13 = {("CCM", "2026-08-27"), ("POWERGESIC 200 PATCH", "2026-10-07"), ("FLEMCORT 6", "2026-10-23"), ("FLEMCORT 6", "2026-10-25"), ("KNEE SUPPORT L HINGED", "2026-10-25"),
             ("KNEE IMMOBILIZER L UNISON", "2026-10-25"), ("KNEE SUPPORT M HINGED", "2026-10-25"), ("NORTIMER TAB", "2026-10-25"),
             ("CARTILOX SACHET", "2026-10-25"), ("GLI-ME SR1", "2026-10-25"), ("EXLAIN A", "2026-10-25"), ("RUNVACE TP", "2026-10-25"),
             ("RIFAVAX 550", "2026-11-08"), ("REEBORN D", "2026-11-08")}
EXPECT = {("AURAB L CAP", "2026-11-05"): "bill", ("BIO D3 MAX", "2026-11-05"): "bill", ("FLEMCORT 6", "2026-11-05"): "bill",
          ("JAKMAC 5", "2026-11-05"): "bill", ("TOLIVANT PLUS", "2026-11-05"): "bill", ("DOLONEX 2 ML INJ", "2026-11-08"): "bill",
          ("DOLONEX 2 ML INJ", "2026-10-18"): "bill", ("THIO Q AP TAB", "2026-11-04"): "bill", ("TRAMAVIN GEL", "2026-11-05"): "timing",
          ("TRAMAVIN GEL", "2026-11-08"): "timing", ("CAST SHOE L TYNOR", "2026-10-25"): "sibling", ("CAST SHOE M TYNOR", "2026-10-25"): "sibling",
          ("ENZOMAC OINTMENT", "2026-08-27"): "sibling", ("ENZOMAC OINTMENT", "2026-10-25"): "sibling", ("CCM", "2026-09-03"): "bill", ("CCM", "2026-09-17"): "voucher_qty", ("KNEE IMMOBILIZER M TYNOR", "2026-10-25"): "sale_not_off"}

rows, info = H.compute(SPINE, DB, "2026-10-16")
by = {(r["item"], r["day_to"]): r for r in rows if r["kind"] == "hand"}
cnt = {k for k, r in by.items() if not r.get("rec_kind")}
extra = sorted(cnt - COUNTED13)
check("the 14 moves with nothing behind them are counted (got %d)" % len(cnt), COUNTED13 <= cnt)
check("nothing else is counted up to 10-Nov (newer moves may be: %s)" % (extra,), all(d > "2026-11-10" for _i, d in extra))
for k, kind in sorted(EXPECT.items()):
    check("%s %s lands under its record '%s' (got %s)" % (k + (kind, by.get(k, {}).get("rec_kind"))), by.get(k, {}).get("rec_kind") == kind)
check("BIO D3 MAX +150 of 6-8 Nov is not a row: the late bill 92592 pays it (F-1279)", ("BIO D3 MAX", "2026-11-08") not in by)
check("... and its explanation is kept for the stored row (timing)", (info.get("explain") or {}).get(("BIO D3 MAX", "2026-11-08"), ("",))[0] == "timing")
check("four rename rows stay renames", sum(1 for r in rows if r["kind"] == "rename") == 4)
check("matcher 1 read the bills changed after their day (got %s)" % info.get("bills"), (info.get("bills") or 0) > 0 and not info.get("bills_why"))
check("every counted row with a rate carries its rupees", all(r.get("value_p") is not None for r in rows if (r["item"], r["day_to"]) in COUNTED13 and r.get("rate_p")))
check("no counted row reads Rs 0 for want of a rate", all(not (r.get("rate_p") is None and r.get("value_p") == 0) for r in rows))
w = H.why_of(by[("FLEMCORT 6", "2026-10-23")])
check("the whole-sum line names Marg's move, the system's and the shift (F-1270)", "+360" in w and "system moved" in w and "no record" in w)
check("a note of the owner's table is used only on its own closing (F-1270: CCM's note fits none)", "voucher says -3; Marg moved -2" not in H.why_of(by[("CCM", "2026-08-27")]))

# ---- the made-up controls, on copies of the spine
tmp = tempfile.mkdtemp()
sp2 = os.path.join(tmp, "spine.db")
shutil.copy(SPINE, sp2)
c = sqlite3.connect(sp2)
c.execute("UPDATE sp_close SET units = units + 7 WHERE k20='ROSIKA FORTE' AND as_on >= '2026-11-05'")                 # a move with nothing behind it
c.execute("UPDATE sp_close SET units = units + 1 WHERE k20='AURAB L CAP' AND as_on >= '2026-11-05'")                  # a B finding with the wrong units
c.commit(); c.close()
rows2, _i2 = H.compute(sp2, DB, "2026-10-16")
by2 = {(r["item"], r["day_to"]): r for r in rows2 if r["kind"] == "hand"}
r = by2.get(("ROSIKA FORTE", "2026-11-05"))
check("a made-up move with nothing behind it is counted", r is not None and not r.get("rec_kind") and abs(r["shift"] - 7) < 0.01)
r = by2.get(("AURAB L CAP", "2026-11-05"))
check("a made-up move one unit off the removed bill explains nothing: counted", r is not None and not r.get("rec_kind") and abs(r["shift"] - 11) < 0.01)
check("CCM +5 of 27-Aug stays counted: a -3 voucher seven weeks later is the other way (review MUST 1)", ("CCM", "2026-08-27") in {k for k, r in by2.items() if not r.get("rec_kind")})

# ---- the review's controls: each matcher's limit, on another copy
sp3 = os.path.join(tmp, "spine3.db")
shutil.copy(SPINE, sp3)
c = sqlite3.connect(sp3)
for item, frm, d in (("CAST SHOE L TYNOR", "2026-10-20", -1), ("ENZOMAC OINTMENT", "2026-10-20", -9), ("ECONORM CAP", "2026-10-18", -40),
                     ("PATOPAN DSR", "2026-11-05", 7), ("JAKMAC 5", "2026-11-12", 9)):
    c.execute("UPDATE sp_close SET units = units + ? WHERE k20=? AND as_on >= ?", (d, item, frm))
c.commit(); c.close()
rows3, _i3 = H.compute(sp3, DB, "2026-10-16")
by3 = {(r["item"], r["day_to"]): r for r in rows3 if r["kind"] == "hand"}
def counted_at(item, day):
    return next((r for (i, d), r in by3.items() if i == item and d >= day and not r.get("rec_kind")), None) is not None
check("3a: a -1 on CAST SHOE L with no opposite move on its sibling is counted (review MUST 3)", counted_at("CAST SHOE L TYNOR", "2026-10-20"))
check("3a: the real pair of 25-Oct still uses its voucher", by3.get(("CAST SHOE L TYNOR", "2026-10-25"), {}).get("rec_kind") == "sibling")
check("3c: a -9 on ENZOMAC OINTMENT on another day is counted (review MUST 2)", counted_at("ENZOMAC OINTMENT", "2026-10-20"))
check("4: a -40 on ECONORM CAP beyond its -36 voucher is counted (review MUST 1)", counted_at("ECONORM CAP", "2026-10-18"))
check("5: a +7 on a fast mover equal to one of many sales is counted (review MUST 4)", counted_at("PATOPAN DSR", "2026-11-05"))
check("F-1278: a rise on a closing printed after the last purchase list is not judged yet", ("JAKMAC 5", "2026-11-12") not in by3)

# ---- the store: refresh on a copy of the finance database
db2 = os.path.join(tmp, "finance.db")
shutil.copy(DB, db2)
con = sqlite3.connect(db2)
before = con.execute("SELECT COUNT(*) FROM marg_hand_change").fetchone()[0]
res = H.refresh(con, SPINE, finance_db=db2, force=True)
check("refresh runs (%s)" % res, res.get("ok"))
check("no stored row is deleted (%d before)" % before, con.execute("SELECT COUNT(*) FROM marg_hand_change").fetchone()[0] >= before)
NC = con.execute("SELECT COUNT(*) FROM marg_hand_change WHERE kind='hand' AND status='open' AND COALESCE(rec_kind,'')=''").fetchone()[0]
check("the counted open rows are the 14 and the newer ones (%d)" % NC, NC == 14 + len(extra))
check("the stored BIO D3 MAX +150 is explained with its record", con.execute("SELECT rec_kind FROM marg_hand_change WHERE item='BIO D3 MAX' AND day_to='2026-11-08'").fetchone()[0] == "timing")
check("the expiry page's list (default) holds only counted rows and renames", all(not x.get("rec_kind") for x in H.rows_for_page(con)))
check("S812's first run marks what it adds as history", con.execute("SELECT COUNT(*) FROM marg_hand_change WHERE hist=0 AND found_at >= (SELECT value FROM setting WHERE key='hand.s812_since')").fetchone()[0] == 0)
n0 = con.execute("SELECT COUNT(*), SUM(COALESCE(rec_kind,'')<>'') FROM marg_hand_change").fetchone()
orig = H._b_records
H._b_records = lambda *a, **k: ([], "made-up failure")          # review MUST 5: the bills cannot be read
con.execute("UPDATE setting SET value='x' WHERE key='hand.built_seen'"); con.commit()
rh = H.refresh(con, SPINE, finance_db=db2)
H._b_records = orig
check("bills unreadable: the refresh stores nothing and says so (%s)" % rh.get("error", "")[:60], rh.get("held") and
      con.execute("SELECT COUNT(*), SUM(COALESCE(rec_kind,'')<>'') FROM marg_hand_change").fetchone() == n0)
H.refresh(con, SPINE, finance_db=db2, force=True)
res2 = H.refresh(con, SPINE, finance_db=db2)
check("a second refresh on the same spine does nothing ('same')", res2.get("same"))
import datetime as dt                                              # noqa: E402
now = H.now_ist().replace(tzinfo=None)
con.execute("UPDATE marg_hand_change SET hist=0, found_at=? WHERE kind='hand'", (H.stamp(now),))
con.execute("UPDATE setting SET value='2026-01-01 00:00:00' WHERE key='hand.since'")
g = H.message_groups(con, "2000-01-01", now)
told = {(x["item"], x["day_to"]) for v in g.values() for x in v}
check("the notice speaks only of counted moves (no record) -- %d told" % len(told), told and all(x in cnt for x in told))
con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('hand.floor_rs','50','t')")
g2 = H.message_groups(con, "2000-01-01", now)
told2 = {(x["item"], x["day_to"]) for v in g2.values() for x in v}
check("the floor (Rs 50) keeps a small move (REEBORN D, Rs 20) off the notice; a larger one (RIFAVAX 550, Rs 106) stays", ("REEBORN D", "2026-11-08") not in told2 and ("RIFAVAX 550", "2026-11-08") in told2)
check("with no floor the small move is told", ("REEBORN D", "2026-11-08") in told)
con.execute("UPDATE setting SET value='0' WHERE key='hand.floor_rs'")

# ---- section A on the page
import marg_billwatch as BW                                        # noqa: E402
BW.ensure(con)
V = BW.hand_view(con)
check("section A lists them to look at (%d)" % len(V["counted"]), len(V["counted"]) == NC)
check("section A's Explained after all holds the records", len(V["explained"]) >= 18)
rid = next(x["id"] for x in V["counted"] if x["item"] == "RIFAVAX 550")
check("a close needs a choice", BW.hand_close(con, "manoj", rid, "", "")[2] == 400)
check("his close saves", BW.hand_close(con, "manoj", rid, "ok", "blocked as expired")[0])
check("closed twice is refused", BW.hand_close(con, "manoj", rid, "ok", "")[2] == 409)
g3 = H.message_groups(con, "2000-01-01", now)
check("a move he closed is never pushed", ("RIFAVAX 550", "2026-11-08") not in {(x["item"], x["day_to"]) for v in g3.values() for x in v})
check("reopen", BW.hand_reopen(con, "manoj", rid)[0])
exp = next(x["id"] for x in V["explained"])
check("an explained row cannot be closed (it is not counted)", BW.hand_close(con, "manoj", exp, "ok", "")[2] == 409)
check("the floor refuses a word", BW.hand_set_floor(con, "manoj", "abc")[2] == 400)
check("the floor saves 250", BW.hand_set_floor(con, "manoj", "250")[0] and H.floor_p(con) == 25000)
con.execute("UPDATE marg_hand_change SET hist=1")                 # back to history, as the first S812 run leaves it
con.commit()
n = len([x for x in BW.hand_view(con)["counted"] if x["before"]])
check("all of them are 'before this section began' after the first run", n == NC)
check("the lot refuses a stale count", BW.hand_ok_lot(con, "manoj", n + 1)[2] == 409)
lr = BW.hand_ok_lot(con, "manoj", n)
check("the lot closes them (%s)" % (lr,), lr[0] and len(BW.hand_view(con)["counted"]) == NC - n)
h = BW.hand_html(con)
check("section A renders, its rows and the floor field on it", 'id="stock"' in h and 'id="hfloor"' in h and "Explained after all" in h)
print("WALK %d/%d" % (ok, tot))
sys.exit(0 if ok == tot else 1)
