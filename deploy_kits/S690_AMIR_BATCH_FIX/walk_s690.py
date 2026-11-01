#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s690.py -- the walk of kit S690_AMIR_BATCH_FIX.

    python3 -B walk_s690.py --new <root> --scratch <dir>            the walk on the rebuilt files (own rows only)
    python3 -B walk_s690.py --old <root> --scratch <dir>            the control: the live files must go red
    python3 -B walk_s690.py --proof --old-root <root> --new <root> --db <copy of finance.db> --spine <copy of spine.db> --archive <dir> --scratch <dir>

<root>/finance/expiry_watch.py and <root>/finance/amir_day.py are the files under test (their neighbours are read from <root> too).
The walk writes ONLY its own rows: a fresh finance database and a fresh spine made in --scratch (own items WALKSIX / WALKTWO / WALKNOB ...),
two made-up Batch Stock reports served to the module in place of the archive's (the certified reader is S638's and is not under test).
--proof: on COPIES of the real database, the real spine and the real archive (read only), the OLD and the NEW expiry_watch run once each;
the newest run's lines must be identical apart from the figures S690 adds (below[3], has[2..3], the no-batch line's item and pack), and
the NEW run's fixes are listed.  Last line: "N of N green" (walk), "K S690 check(s) red . M green" (control) or "proof: ..." (proof).
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import sqlite3
import sys

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def load(root, scratch, tag, name):
    mod_dir = os.path.join(scratch, "mod_" + tag)
    os.makedirs(mod_dir, exist_ok=True)
    src = os.path.join(root, "finance", name + ".py")
    shutil.copyfile(src, os.path.join(mod_dir, name + ".py"))
    for p in (os.path.join(root, "finance"), os.path.join(root, "finance", "spine")):
        if p not in sys.path:
            sys.path.append(p)
    spec = importlib.util.spec_from_file_location(name + "_" + tag, os.path.join(mod_dir, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------------------------------------- the walk's own world
def make_spine(path):
    sp = sqlite3.connect(path)
    sp.executescript("""
    CREATE TABLE sp_alias (alias TEXT, k20 TEXT);
    CREATE TABLE sp_close (k20 TEXT, as_on TEXT, units REAL);
    CREATE TABLE sp_move (k20 TEXT, kind TEXT, date TEXT, units REAL);
    CREATE TABLE sp_sale_line (date TEXT, bill TEXT, k20 TEXT, batch TEXT, expiry TEXT, units REAL);
    CREATE TABLE sp_sale_bill (date TEXT, bill TEXT, credit_note INTEGER);
    """)
    for k in ("WALKSIX", "WALKTWO", "WALKNOB", "WALKBUY", "WALKFEW"):
        sp.execute("INSERT INTO sp_close VALUES (?,?,?)", (k, "2099-03-01", 100))
        sp.execute("INSERT INTO sp_close VALUES (?,?,?)", (k, "2099-03-20", 100))
    sp.commit()
    return sp


def B(item, batch, expiry, units, pack=10):
    return dict(item=item, batch=batch, expiry=expiry, units=units, pack=pack, packing=("1*%d" % pack) if pack > 1 else "")


def report1():
    """Report A (as on 2099-03-01): WALKSIX a blank-batch minus beside two batches (the earliest expiry is short: a split);
    WALKTWO minus 'B1222' beside 'TSF B1222' (the same batch typed short) and another; WALKFEW nothing wrong; WALKBUY a minus."""
    bs = [B("WALKSIX", "", "", -14), B("WALKSIX", "SIXA", "2099-05", 4), B("WALKSIX", "SIXB", "2099-09", 50),
          B("WALKTWO", "B1222", "", -3), B("WALKTWO", "TSF B1222", "2100-01", 40), B("WALKTWO", "TWOX", "2099-06", 9),
          B("WALKFEW", "FEW1", "2099-12", 30), B("WALKNOB", "NOBA", "2099-10", 40),
          B("WALKBUY", "BUYM", "", -5), B("WALKBUY", "BUYA", "2099-08", 60)]
    return dict(ok=True, as_on="2099-03-01", items=5, total=sum(b["units"] for b in bs), md5="walk690aaaaaaaaaaaaaaaaaaaaaaaaa",
                name="BATCH_STOCK_BATCHWISE__2099-03-01__20990301-230000__walk690a.XLS", batches=bs, failed=[])


def report2():
    """Report B (as on 2099-03-20): WALKSIX fixed whole (Receive 14 into blank -> 0; Issue 4 from SIXA and 10 from SIXB, minus the 6 sold
    from SIXB between); WALKTWO: Receive done, Issue NOT (TSF B1222 only down by its 2 sold); WALKBUY bought since -> Receive alone counts;
    WALKFEW now a minus of 2 on FEW9 (new); WALKNOB untouched."""
    bs = [B("WALKSIX", "", "", 0), B("WALKSIX", "SIXA", "2099-05", 0), B("WALKSIX", "SIXB", "2099-09", 34),
          B("WALKTWO", "B1222", "", 0), B("WALKTWO", "TSF B1222", "2100-01", 38), B("WALKTWO", "TWOX", "2099-06", 9),
          B("WALKFEW", "FEW1", "2099-12", 28), B("WALKFEW", "FEW9", "2099-11", -2),
          B("WALKNOB", "", "", -3), B("WALKNOB", "NOBA", "2099-10", 40),
          B("WALKBUY", "BUYM", "", 0), B("WALKBUY", "BUYA", "2099-08", 80)]
    return dict(ok=True, as_on="2099-03-20", items=5, total=sum(b["units"] for b in bs), md5="walk690bbbbbbbbbbbbbbbbbbbbbbbbb",
                name="BATCH_STOCK_BATCHWISE__2099-03-20__20990320-230000__walk690b.XLS", batches=bs, failed=[])


def serve(m, R):
    m.batch_exports = lambda archive: [R["name"]]
    m.read_batch_stock = lambda path=None, rows=None: R
    m.closing_items_on = lambda sp, as_on: (5, as_on)
    m.item_list_new = lambda archive, known: []
    m.out_of_stock = lambda con, sp, alias, today: []


def mi_file(con, md5, stamp, received, name):
    con.execute("CREATE TABLE IF NOT EXISTS mi_file (md5 TEXT, type TEXT, verdict TEXT, stamp TEXT, received_at TEXT, server_name TEXT, "
                "variant TEXT, date_from TEXT, date_to TEXT, source TEXT)")
    con.execute("INSERT INTO mi_file VALUES (?,?,?,?,?,?,?,?,?,?)", (md5, "BATCH_STOCK", "VERIFIED", stamp, received, name, "BATCHWISE", "", "", "push"))
    con.commit()


class S:
    pass


def walk(root, scratch):
    E = load(root, scratch, "new", "expiry_watch")
    c = []
    db = os.path.join(scratch, "walk_finance.db")
    spp = os.path.join(scratch, "walk_spine.db")
    for p in (db, spp):
        if os.path.exists(p):
            os.remove(p)
    sp = make_spine(spp)
    # sales after report A: WALKNOB sold 3 with NO batch (a no-batch sale; its stock on NOBA); WALKSIX 6 from SIXB; WALKTWO 2 from TSF B1222
    sp.executemany("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?)", [
        ("2099-03-05", "W1", "WALKNOB", "", "", 3), ("2099-03-06", "W2", "WALKSIX", "SIXB", "2099-09", 6), ("2099-03-07", "W3", "WALKTWO", "TSF B1222", "2100-01", 2)])
    sp.executemany("INSERT INTO sp_sale_bill VALUES (?,?,?)", [("2099-03-05", "W1", 0), ("2099-03-06", "W2", 0), ("2099-03-07", "W3", 0)])
    sp.execute("INSERT INTO sp_move VALUES (?,?,?,?)", ("WALKBUY", "PURCHASE", "2099-03-10", 20))
    sp.commit()
    sp.close()
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.commit()
    con.close()
    archive = os.path.join(scratch, "empty_archive")
    os.makedirs(archive, exist_ok=True)
    # --- run 1 on report A
    serve(E, report1())
    rc = E.run(db=db, spine_path=spp, archive=archive, today=dt.date(2099, 3, 8), log=lambda *a: None)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM stock_batch_fix ORDER BY id")]
    by = {}
    for r in rows:
        by.setdefault(r["item"], []).append(r)
    c.append(("run 1 writes a run and the fix table", rc == 0 and bool(rows)))
    six = by.get("WALKSIX", [])
    c.append(("a blank-batch minus is split: 4 from the earliest expiry (SIXA), 10 from the next (SIXB)",
              [(x["minus_batch"], x["units"], x["issue_batch"]) for x in six] == [("", 4, "SIXA"), ("", 10, "SIXB")]))
    c.append(("the issue batch's printed figure is kept", [x["issue_printed"] for x in six] == [4, 50]))
    two = by.get("WALKTWO", [])
    c.append(("the same batch typed short is the issue batch (B1222 -> TSF B1222), not the earlier expiry",
              [(x["units"], x["issue_batch"]) for x in two] == [(3, "TSF B1222")]))
    nob = by.get("WALKNOB", [])
    c.append(("a no-batch sale after the report is a pair too (Receive into blank, Issue from the batch with stock)",
              [(x["kind"], x["minus_batch"], x["units"]) for x in nob] == [("nobatch", "", 3)] if nob else False))
    c.append(("nothing wrong, nothing asked (WALKFEW)", "WALKFEW" not in by))
    c.append(("every row starts open, asked on report A", all(x["status"] == "open" and x["asked_md5"].startswith("walk690a") for x in rows)))
    # --- Amir's rows before any report: vouchers, no confirmation
    am = E.fixes_rows(con, dt.date(2099, 3, 8))
    html = am[0][1] if am else ""
    c.append(("Amir's card: the vouchers, Receive set then Issue set", "Voucher 1 &mdash; STOCK RECEIVE" in html and "STOCK ISSUE" in html))
    c.append(("Amir's card: a blank batch reads 'bina batch'; the figure in strips:tabs", "bina batch" in html and "0:4" in html))
    c.append(("Amir's card: no confirmation before a new report", "mil gayi" not in html))
    c.append(("Amir's card never holds his day (his_line False)", am[0][3] is False))
    # more than 6 lines a voucher: add 5 more open rows by hand and look
    con.executemany("INSERT INTO stock_batch_fix (kind,k20,item,pack,minus_batch,units,issue_batch,issue_printed,issue_expiry,asked_run_id,asked_md5,asked_day,asked_at,status) "
                    "VALUES ('batch',?,?,10,'M',1,'I',9,'',1,'walk690aaaaaaaaaaaaaaaaaaaaaaaaa','2099-03-01','2099-03-08T10:00:00','open')",
                    [("WALKX%d" % i, "WALKX%d" % i) for i in range(5)])
    con.commit()
    html = E.fixes_rows(con, dt.date(2099, 3, 8))[0][1]
    c.append(("max 6 lines a voucher: 10 Receive lines make Voucher 1 (6) and Voucher 2 (4)", "Voucher 2 &mdash; STOCK RECEIVE (4 line)" in html))
    con.execute("DELETE FROM stock_batch_fix WHERE k20 LIKE 'WALKX%'")
    con.commit()
    # --- step 4 state before any file today
    st = E.batch_stock_state(con, dt.date(2099, 3, 20))
    c.append(("step 4: no Batch Stock today -> none", st.get("state") == "none"))
    mi_file(con, "walk690bbbbbbbbbbbbbbbbbbbbbbbbb", "20990320-093000", "2099-03-20T09:30:11+05:30", report2()["name"])
    st = E.batch_stock_state(con, dt.date(2099, 3, 20))
    c.append(("step 4: a file at the door, no run yet -> wait with its time", st.get("state") == "wait" and st.get("at") == "09:30"))
    c.append(("run --if-new: a file newer than the newest run says run", E.new_batch_stock(db) is True))
    con.close()
    # --- run 2 on report B with the spine BEHIND the report day (its sales end 03-07): the Receive judged, the Issue deferred
    serve(E, report2())
    rc = E.run(db=db, spine_path=spp, archive=archive, today=dt.date(2099, 3, 20), log=lambda *a: None)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM stock_batch_fix ORDER BY id")]
    six0 = [x for x in rows if x["item"] == "WALKSIX"]
    c.append(("the spine behind the report day: WALKSIX's Receive is seen, the Issue waits (receive_only, 'issue pending')",
              all(x["status"] == "receive_only" and str(x["note"] or "").startswith("issue pending") and not x["judged_md5"] for x in six0)))
    html = E.fixes_rows(con, dt.date(2099, 3, 20))[0][1]
    c.append(("Amir's card then says 'Issue ki jaanch kal subah', nothing 'theek ho gaya'", "Issue ki jaanch kal subah" in html and "Theek ho gaya" not in html))
    con.close()
    sp = sqlite3.connect(spp)                                   # the day's sale export comes in: the spine reaches the report day
    sp.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?)", ("2099-03-20", "W4", "WALKFEW", "FEW1", "2099-12", 2))
    sp.execute("INSERT INTO sp_sale_bill VALUES (?,?,?)", ("2099-03-20", "W4", 0))
    sp.commit()
    sp.close()
    rc = E.run(db=db, spine_path=spp, archive=archive, today=dt.date(2099, 3, 20), log=lambda *a: None)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM stock_batch_fix ORDER BY id")]
    by = {}
    for r in rows:
        by.setdefault(r["item"], []).append(r)
    six = by.get("WALKSIX", [])
    c.append(("WALKSIX: both halves seen on report B -> done, with done_at", all(x["status"] == "done" and x["done_at"] for x in six)))
    two = by.get("WALKTWO", [])
    c.append(("WALKTWO: the minus gone, the issue batch down only by its sales -> receive_only (Issue baaki)",
              [x["status"] for x in two] == ["receive_only"]))
    buy = by.get("WALKBUY", [])
    c.append(("WALKBUY: bought between the reports -> judged on the Receive alone -> done", [x["status"] for x in buy] == ["done"]))
    nob = by.get("WALKNOB", [])
    c.append(("WALKNOB: no figure moved -> still open", [x["status"] for x in nob] == ["open"]))
    few = by.get("WALKFEW", [])
    c.append(("WALKFEW: a new minus on report B -> a new row asked on B", [(x["minus_batch"], x["units"], x["status"], x["asked_md5"][:8]) for x in few] == [("FEW9", 2, "open", "walk690b")]))
    c.append(("a judged row names the report it was judged on", all(x["judged_md5"] and x["judged_md5"].startswith("walk690b") for x in six + two + buy + nob)))
    before = [(x["id"], x["status"], x["judged_at"]) for x in rows]
    con.close()
    E.run(db=db, spine_path=spp, archive=archive, today=dt.date(2099, 3, 21), log=lambda *a: None)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    after = [(x["id"], x["status"], x["judged_at"]) for x in con.execute("SELECT * FROM stock_batch_fix ORDER BY id")]
    c.append(("a second run on the SAME report judges nothing again (every status and judged_at unchanged)", before == after))
    am = E.fixes_rows(con, dt.date(2099, 3, 20))
    html = am[0][1] if am else ""
    c.append(("Amir's card: 'Batch Stock mil gayi 09:30' with the counts", "Batch Stock mil gayi 09:30" in html and "theek ho gaye" in html))
    c.append(("Amir's card: the done list names WALKSIX", "Theek ho gaya" in html and "WALKSIX" in html))
    c.append(("Amir's card: WALKTWO says Receive ho gaya, Issue baaki by batch", "Issue baaki" in html and "TSF B1222" in html))
    c.append(("Amir's card: the open vouchers carry WALKNOB and WALKFEW, not the done ones", "WALKNOB" in html and "FEW9" in html and html.count("WALKBUY") == 1))
    c.append(("Amir's card: no double-escaped dash anywhere", "&amp;mdash;" not in html))
    st = E.batch_stock_state(con, dt.date(2099, 3, 20))
    c.append(("step 4: the run used the file -> ok with the item count", st.get("state") == "ok" and st.get("items") == 5))
    c.append(("run --if-new: nothing newer -> no run", E.new_batch_stock(db) is False))
    # a partial print judged by a run that refused it -> bad
    con.execute("UPDATE stock_expiry_run SET note=? WHERE id=(SELECT MAX(id) FROM stock_expiry_run)",
                ("BATCH_STOCK_BATCHWISE__2099-03-20__20990320-110000__walk690c.XLS: a filtered batch list (3 items; the closing of 2099-03-20 holds 5)",))
    mi_file(con, "walk690cccccccccccccccccccccccccc", "20990320-110000", "2099-03-20T11:00:00+05:30", "BATCH_STOCK_BATCHWISE__2099-03-20__20990320-110000__walk690c.XLS")
    con.execute("UPDATE stock_expiry_run SET at='2099-03-20T11:05:00' WHERE id=(SELECT MAX(id) FROM stock_expiry_run)")
    con.commit()
    st = E.batch_stock_state(con, dt.date(2099, 3, 20))
    c.append(("step 4: a partial print the run refused -> bad, 'poore store ki nahi thi'", st.get("state") == "bad" and st.get("reason") == "poore store ki nahi thi"))
    c.append(("the owner's line names the open and the done", "voucher line" in E.fixes_owner_line(con) and "done" in E.fixes_owner_line(con)))
    # the supersede: a minus that moved while nothing was done
    con.execute("UPDATE stock_batch_fix SET status='open', judged_md5=NULL WHERE item='WALKNOB'")
    con.commit()
    con.close()
    R3 = report2()
    R3["md5"], R3["as_on"], R3["name"] = "walk690dddddddddddddddddddddddddd", "2099-03-25", "BATCH_STOCK_BATCHWISE__2099-03-25__20990325-230000__walk690d.XLS"
    R3["batches"] = [b for b in R3["batches"] if b["item"] != "WALKNOB"] + [B("WALKNOB", "", "", -7), B("WALKNOB", "NOBA", "2099-10", 40)]
    serve(E, R3)
    E.run(db=db, spine_path=spp, archive=archive, today=dt.date(2099, 3, 25), log=lambda *a: None)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    nob = [dict(r) for r in con.execute("SELECT * FROM stock_batch_fix WHERE item='WALKNOB' ORDER BY id")]
    c.append(("a minus that moved (3 -> 7) while nothing was done: the old row superseded, a new row of 7 from the new report",
              [(x["units"], x["status"]) for x in nob] == [(3, "superseded"), (7, "open")]))
    # both halves keyed, then the minus batch sold one more before the print: the Receive still needed is 1, not the asked 3
    con.execute("UPDATE stock_batch_fix SET status='open', judged_md5=NULL, units=3 WHERE item='WALKTWO'")
    con.commit()
    con.close()
    R4 = report2()
    R4["md5"], R4["as_on"], R4["name"] = "walk690eeeeeeeeeeeeeeeeeeeeeeeeee", "2099-03-20", "BATCH_STOCK_BATCHWISE__2099-03-20__20990320-235000__walk690e.XLS"
    R4["batches"] = [b for b in R4["batches"] if b["item"] != "WALKTWO"] + [B("WALKTWO", "B1222", "", -1), B("WALKTWO", "TSF B1222", "2100-01", 35), B("WALKTWO", "TWOX", "2099-06", 9)]
    serve(E, R4)
    E.run(db=db, spine_path=spp, archive=archive, today=dt.date(2099, 3, 20), log=lambda *a: None)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    two = [dict(r) for r in con.execute("SELECT * FROM stock_batch_fix WHERE item='WALKTWO' AND status IN ('open','receive_only','issue_only')")]
    c.append(("Issue keyed, the minus sold one more: issue_only with the Receive still needed = 1 (the minus as it stands)",
              [(x["status"], x["units"]) for x in two] == [("issue_only", 1)]))
    # amir_day's card
    try:
        A = load(root, scratch, "new", "amir_day")
        s = S()
        s.batchstock = dict(state="none")
        h0 = A._s690_batchstock_card(s)
        s.batchstock = dict(state="ok", at="09:12", items=238, as_on="2099-03-20")
        h1 = A._s690_batchstock_card(s)
        s.batchstock = dict(state="bad", at="09:12", reason="poore store ki nahi thi")
        h2 = A._s690_batchstock_card(s)
        s.batchstock = dict(state="wait", at="09:12")
        h3 = A._s690_batchstock_card(s)
        c.append(("amir_day step 4: 'not yet' shows the steps, WHOLE in them", "Tarika" in h0 and "WHOLE" in h0))
        c.append(("amir_day step 4: ok shows the tick, the count and the time", "&#10003;" in h1 and "238" in h1 and "09:12" in h1))
        c.append(("amir_day step 4: bad says WHOLE, dobara", "WHOLE" in h2 and "dobara" in h2))
        c.append(("amir_day step 4: wait says 'jaanch ho rahi hai'", "jaanch ho rahi hai" in h3))
    except Exception as ex:                                        # noqa: BLE001
        c.append(("amir_day step 4 card (%s)" % str(ex)[:60], False))
    con.close()
    return c


def proof(old_root, new_root, db, spine, archive, scratch):
    Eo = load(old_root, scratch, "old", "expiry_watch")
    En = load(new_root, scratch, "new", "expiry_watch")
    dbo, dbn = os.path.join(scratch, "proof_old.db"), os.path.join(scratch, "proof_new.db")
    shutil.copyfile(db, dbo)
    shutil.copyfile(db, dbn)
    today = dt.datetime.now(IST).date()
    Eo.run(db=dbo, spine_path=spine, archive=archive, today=today, log=lambda *a: None)
    En.run(db=dbn, spine_path=spine, archive=archive, today=today, log=lambda *a: None)

    def lines(p):
        c = sqlite3.connect(p)
        out = []
        for r in c.execute("SELECT section,part,k20,item,batch,expiry,units,pack,packing,last_sale,last_buy,info,seq FROM stock_expiry_line "
                           "WHERE run_id=(SELECT MAX(id) FROM stock_expiry_run) ORDER BY seq"):
            r = list(r)
            i = json.loads(r[11]) if r[11] else {}
            if "below" in i:
                i["below"] = [b[:3] for b in i["below"]]
            if "has" in i:
                i["has"] = [h[:2] for h in i["has"]]
            if r[0] == "wrong" and r[1] == "nobatch":
                i.pop("has", None)
                r[3], r[7], r[8] = r[2], 1, ""
            r[11] = json.dumps(i, sort_keys=True)
            out.append(tuple(r))
        ro = c.execute("SELECT export_md5, export_as_on, counts FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
        return out, ro
    lo, ro = lines(dbo)
    ln, rn = lines(dbn)
    same = (lo == ln and ro == rn)
    c = sqlite3.connect(dbn)
    fx = c.execute("SELECT COUNT(*) FROM stock_batch_fix").fetchone()[0]
    for r in c.execute("SELECT item, minus_batch, units, issue_batch, status FROM stock_batch_fix ORDER BY id"):
        print("  --  %s · %s %d -> %s · %s" % (r[0], r[1] or "bina batch", r[2], r[3], r[4]))
    if not same:
        for a, b in zip(lo, ln):
            if a != b:
                print("      RED  first difference:\n      old %s\n      new %s" % (a, b))
                break
    return "proof: old %d lines / new %d lines . %s . report %s . fixes %d" % (len(lo), len(ln), "IDENTICAL" if same else "DIFFER", (rn[0] or "none")[:8] if rn else "none", fx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new")
    ap.add_argument("--old")
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--old-root")
    ap.add_argument("--db")
    ap.add_argument("--spine")
    ap.add_argument("--archive")
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    if a.proof:
        print(proof(a.old_root, a.new, a.db, a.spine, a.archive, a.scratch))
        return
    try:
        c = walk(a.new or a.old, a.scratch)
    except Exception as ex:                                        # noqa: BLE001
        c = [("the walk ran to its end (%s: %s)" % (type(ex).__name__, str(ex)[:80]), False)]
    red = [t for t, ok in c if not ok]
    for t, ok in c:
        print("  %s  %s" % ("ok " if ok else "RED", t))
    if a.new:
        print("%d of %d green" % (len(c) - len(red), len(c)))
    else:
        print("%d S690 check(s) red . %d green" % (len(red), len(c) - len(red)))


if __name__ == "__main__":
    main()
