#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s693.py -- the walk of kit S693_STOCK_ON_BATCH (01-Nov-2026, Sanjeevni session 375).

    python3 -B walk_s693.py --new <root> --scratch <dir>      the walk on the rebuilt expiry_watch.py (own rows only)   -> 'N of N green'
    python3 -B walk_s693.py --old <root> --scratch <dir>      the control on the live file                              -> 'K S693 check(s) red . M green'
    python3 -B walk_s693.py --proof --old-root <root> --new <root> --db <copy of finance.db> --spine <copy of spine.db> --archive <dir> --scratch <dir>

<root>/finance/expiry_watch.py is the file under test; its neighbours are read from <root>.  The walk writes ONLY its own rows: a fresh
finance database and a fresh spine in --scratch (own medicines WALK...; year 2099), one made-up Batch Stock served in place of the archive's.
--proof: on COPIES of the real database and the real spine and an archive (read only), the OLD and the NEW watch run once each; every
difference between the newest runs' lines must be one the kit explains (a bought medicine's minus batch now named, each read against its
sales or Marg's printed minus; a bought medicine's batch with more stock; a new batch from a purchase); anything else is NOT CLEAN.
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


def load(root, scratch, tag):
    d = os.path.join(scratch, "mod_" + tag)
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(os.path.join(root, "finance", "expiry_watch.py"), os.path.join(d, "expiry_watch.py"))
    for p in (os.path.join(root, "finance"), os.path.join(root, "finance", "spine")):
        if p not in sys.path:
            sys.path.append(p)
    spec = importlib.util.spec_from_file_location("expiry_watch_" + tag, os.path.join(d, "expiry_watch.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------------------------------------- the walk's own world
DAY = "2099-03-01"          # the Batch Stock's day (its stamp 23:00 -> stands for its own day; sales after it are taken off)
ITEMS = ("WALKTIE", "WALKNEW", "WALKAMB", "WALKNOB", "WALKSAL", "WALKPRE", "WALKSUP", "WALKORT", "WALKDUP", "WALKLAG", "WALKLOOSE")


def make_spine(path):
    sp = sqlite3.connect(path)
    sp.executescript("""
    CREATE TABLE sp_alias (alias TEXT, k20 TEXT);
    CREATE TABLE sp_close (k20 TEXT, as_on TEXT, units REAL);
    CREATE TABLE sp_move (k20 TEXT, kind TEXT, date TEXT, units REAL);
    CREATE TABLE sp_sale_line (date TEXT, bill TEXT, k20 TEXT, batch TEXT, expiry TEXT, units REAL);
    CREATE TABLE sp_sale_bill (date TEXT, bill TEXT, credit_note INTEGER);
    """)
    for k in ITEMS:
        sp.execute("INSERT INTO sp_close VALUES (?,?,?)", (k, DAY, 100))
    return sp


def B(item, batch, expiry, units, pack=10):
    return dict(item=item, batch=batch, expiry=expiry, units=units, pack=pack, packing=("1*%d" % pack) if pack > 1 else "")


def report():
    bs = [B("WALKTIE", "VGT260049", "2099-09", 50), B("WALKTIE", "TIEA2", "2099-12", 20),
          B("WALKNEW", "OLD1", "2099-10", 5),
          B("WALKAMB", "XAB1234", "2099-10", 10), B("WALKAMB", "YAB1234", "2099-11", 10),
          B("WALKNOB", "D1", "2099-10", 10),
          B("WALKSAL", "KHT.072667", "2099-10", 30), B("WALKSAL", "SALE2", "2099-12", 10),
          B("WALKPRE", "P1", "2099-04", 10),
          B("WALKSUP", "S1", "2099-10", 10),
          B("WALKORT", "O1", "", 3, pack=1),
          B("WALKDUP", "DUP1", "2099-05", 10),
          B("WALKLAG", "L1", "2099-10", 10), B("WALKLAG", "L2", "2099-11", 5),
          B("WALKLOOSE", "LO1", "2099-05", 5)]
    return dict(ok=True, as_on=DAY, items=len(ITEMS), total=sum(b["units"] for b in bs), md5="walk693aaaaaaaaaaaaaaaaaaaaaaaaa",
                name="BATCH_STOCK_BATCHWISE__%s__20990301-230000__walk693a.XLS" % DAY, batches=bs, failed=[])


def serve(m, R):
    m.batch_exports = lambda archive: [R["name"]]
    m.read_batch_stock = lambda path=None, rows=None: R
    m.closing_items_on = lambda sp, as_on: (len(ITEMS), as_on)
    m.item_list_new = lambda archive, known: []
    m.out_of_stock = lambda con, sp, alias, today: []


def finance_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
    CREATE TABLE purchase_export (md5 TEXT PRIMARY KEY, type TEXT, superseded_by TEXT);
    CREATE TABLE purchase_line (id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT, month TEXT, item TEXT, packing TEXT,
        batch TEXT, expiry TEXT, qty REAL, free REAL, loose_qty REAL, direction TEXT, source_md5 TEXT, line_type TEXT);
    CREATE TABLE stock_item_section (item_key TEXT, item TEXT, section TEXT);
    """)
    con.execute("INSERT INTO purchase_export VALUES ('walk693live', 'ITEMWISE', NULL)")
    con.execute("INSERT INTO purchase_export VALUES ('walk693old', 'ITEMWISE', 'walk693live')")
    con.execute("INSERT INTO purchase_export VALUES ('walk693live2', 'ITEMWISE', NULL)")        # a second live export overlapping the first
    L = []

    def pl(item, date, batch, expiry, qty, free, loose, src="walk693live", packing="1*10", direction="PURCHASE", bill=None):
        L.append(("WALK SUPPLIER", bill or "W%d" % (len(L) + 1), date, date[:7], item, packing, batch, expiry, qty, free, loose, direction, src, "ITEMWISE"))
    pl("WALKTIE", "2099-03-03", "GT260049", "9/99", 10, 0, 100)          # the last 8 characters of VGT260049 -> tied
    pl("WALKNEW", "2099-03-03", "EW2A1234", "5/99", 10, 0, 100)          # a batch the Batch Stock does not print -> new (the report's 8-letter clip of NEW2A1234), expiry 2099-05
    pl("WALKAMB", "2099-03-03", "AB1234", "9/99", 5, 0, 50)              # fits XAB1234 and YAB1234 -> untied
    pl("WALKNOB", "2099-03-03", "", "9/99", 5, 0, 50)                    # no batch -> untied
    pl("WALKPRE", DAY, "P1", "4/99", 10, 0, 100)                         # bill dated the report's own day -> already in the print, not placed
    pl("WALKSUP", "2099-03-03", "S1", "9/99", 10, 0, 100, src="walk693old")   # a superseded export -> ignored
    pl("WALKORT", "2099-03-03", "O1", "", 5, None, 5, packing="1*1")     # an orthotic -> ignored
    pl("WALKTIE", "2099-03-04", "GT260049", "9/99", 2, 1, None)          # no loose figure -> (qty + free) x pack = 30
    pl("WALKDUP", "2099-03-03", "DUP1", "5/99", 5, 0, 50, bill="WD1")    # the same bill line ...
    pl("WALKDUP", "2099-03-03", "DUP1", "5/99", 5, 0, 50, bill="WD1", src="walk693live2")   # ... in a second live export: counted once
    pl("WALKLAG", "2099-03-03", "L1", "9/99", 10, 0, 100)               # placed, but the spine knows a bigger purchase the report has not: untied
    pl("WALKLOOSE", "2099-03-03", "LO1", "5/99", 10, 2, 12)             # Marg's loose figure IS the unit (THIO Q AP): 12, not (10 + 2) x 10
    con.executemany("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, expiry, qty, free, loose_qty, "
                    "direction, source_md5, line_type) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", L)
    con.execute("INSERT INTO stock_item_section VALUES (?,?,?)", ("WALKORT", "WALKORT", "Orthotics"))
    con.commit()
    con.close()


def walk(root, scratch):
    E = load(root, scratch, "new")
    c = []
    db, spp = os.path.join(scratch, "walk_finance.db"), os.path.join(scratch, "walk_spine.db")
    for p in (db, spp):
        if os.path.exists(p):
            os.remove(p)
    sp = make_spine(spp)
    sales = [("2099-03-05", "W1", "WALKTIE", "VGT260049", "2099-09", 140), ("2099-03-05", "W2", "WALKTIE", "TIEA2", "2099-12", 30),
             ("2099-03-05", "W3", "WALKNEW", "OLD1", "2099-10", 8), ("2099-03-06", "W3b", "WALKNEW", "NEW2A1234", "2099-05", 30),
             ("2099-03-05", "W3c", "WALKLAG", "L1", "2099-10", 15),
             ("2099-03-05", "W4", "WALKAMB", "XAB1234", "2099-10", 15),
             ("2099-03-05", "W5", "WALKNOB", "D1", "2099-10", 15),
             ("2099-03-05", "W6", "WALKSAL", "HT072667", "2099-10", 20), ("2099-03-06", "W7", "WALKSAL", "HT072667", "2099-10", 15),
             ("2099-03-05", "W8", "WALKPRE", "P1", "2099-04", 5),
             ("2099-03-05", "W9", "WALKSUP", "S1", "2099-10", 15)]
    sp.executemany("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?)", sales)
    sp.executemany("INSERT INTO sp_sale_bill VALUES (?,?,?)", [(s[0], s[1], 0) for s in sales])
    for k in ("WALKTIE", "WALKNEW", "WALKAMB", "WALKNOB", "WALKSUP", "WALKDUP", "WALKLOOSE"):   # the spine knows the purchases (bought_since)
        sp.execute("INSERT INTO sp_move VALUES (?,?,?,?)", (k, "PURCHASE", "2099-03-03", 10))
    sp.execute("INSERT INTO sp_move VALUES (?,?,?,?)", ("WALKLAG", "PURCHASE", "2099-03-03", 100))
    sp.execute("INSERT INTO sp_move VALUES (?,?,?,?)", ("WALKLAG", "PURCHASE", "2099-03-04", 500))   # a purchase the item report has not carried yet
    sp.commit()
    sp.close()
    finance_db(db)
    archive = os.path.join(scratch, "empty_archive")
    os.makedirs(archive, exist_ok=True)
    serve(E, report())
    E.run(db=db, spine_path=spp, archive=archive, today=dt.date(2099, 3, 8), log=lambda *a: None)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    run = con.execute("SELECT * FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
    lines = [dict(r) for r in con.execute("SELECT * FROM stock_expiry_line WHERE run_id=? ORDER BY seq", (run["id"],))]
    for ln in lines:
        ln["info"] = json.loads(ln["info"]) if ln["info"] else {}

    def L(sec, k, part=None):
        return [x for x in lines if x["section"] == sec and x["k20"] == k and (part is None or x["part"] == part)]
    note = run["note"] or ""
    c.append(("the run is ok on the made-up report", run["ok"] == 1 and run["export_as_on"] == DAY, False))
    c.append(("the run's note records the placement (S693: ...)", "S693:" in note, True))
    c.append(("note: 6 lines placed on 5 batches, 1 new (the duplicate line counted once)", "6 purchase line(s)" in note and "on 5 batch(es), 1 new" in note, True))
    c.append(("note: WALKAMB, WALKLAG and WALKNOB untied", "untied WALKAMB,WALKLAG,WALKNOB" in note, True))
    # WALKTIE: VGT260049 50 + 100 + 30 (no loose: (2+1)x10) - 140 = 40; TIEA2 20 - 30 = -10 -> wrong, judged though bought
    w = L("wrong", "WALKTIE", "batch")
    c.append(("WALKTIE: a bought medicine's minus batch TIEA2 is named", len(w) == 1 and w[0]["batch"] == "TIEA2", True))
    c.append(("WALKTIE: the tied batch holds 40 (50 + 100 + 30 - 140)", bool(w) and [h[0:2] for h in w[0]["info"]["has"]] == [["VGT260049", "4:0"]], True))
    # WALKNEW: OLD1 5 - 8 = -3; NEW2 100 new (expiry 2099-05 -> near)
    w = L("wrong", "WALKNEW", "batch")
    c.append(("WALKNEW: minus OLD1 named beside the NEW batch EW2A1234", len(w) == 1 and w[0]["batch"] == "OLD1" and [h[0] for h in w[0]["info"]["has"]] == ["EW2A1234"], True))
    n = L("near", "WALKNEW")
    c.append(("WALKNEW: the new batch is listed near expiry (2099-05) with 70 -- the sale printing NEW2A1234 in full tied to the clip", len(n) == 1 and n[0]["batch"] == "EW2A1234" and n[0]["expiry"] == "2099-05" and n[0]["units"] == 70, True))
    fx = con.execute("SELECT item, minus_batch, units, issue_batch FROM stock_batch_fix WHERE k20='WALKNEW'").fetchall()
    c.append(("WALKNEW: the voucher pair issues 3 from the new batch into OLD1", [tuple(r) for r in fx] == [("WALKNEW", "OLD1", 3, "EW2A1234")], True))
    n = L("near", "WALKDUP")
    c.append(("WALKDUP: the same bill line in two live exports placed once (10 + 50 = 60, not 110)", len(n) == 1 and n[0]["units"] == 60, True))
    c.append(("WALKLAG: the spine knows a purchase the report has not carried -> untied, judged by the printed minus only (no line)", not L("wrong", "WALKLAG") and "WALKLAG" in note.split("untied")[-1], True))
    n = L("near", "WALKLOOSE")
    c.append(("WALKLOOSE: Marg's loose figure is the unit (5 + 12 = 17, not 125)", len(n) == 1 and n[0]["units"] == 17, True))
    # WALKAMB, WALKNOB: untied -> as before (bought, no printed minus) -> no line
    c.append(("WALKAMB: untied (two batches fit) -> judged as before, no line", not L("wrong", "WALKAMB"), False))
    c.append(("WALKNOB: untied (no batch on the line) -> no line", not L("wrong", "WALKNOB"), False))
    # WALKSAL: not bought; the sale's HT072667 ties to KHT.072667: 30 - 35 = -5 beside SALE2 10
    w = L("wrong", "WALKSAL", "batch")
    c.append(("WALKSAL: a sale batch printed without the leading letter and dot ties; the minus is named", len(w) == 1 and w[0]["batch"] == "KHT.072667", True))
    # WALKPRE: the purchase dated the report's own day is not placed: P1 10 - 5 = 5
    n = L("near", "WALKPRE")
    c.append(("WALKPRE: a purchase dated the report's own day is not added (near line 5, not 105)", len(n) == 1 and n[0]["units"] == 5, False))
    # WALKSUP: superseded export ignored: S1 10 - 15 = -5, bought, printed >= 0 -> no line under both
    c.append(("WALKSUP: a superseded export's line is not placed (no line)", not L("wrong", "WALKSUP"), False))
    # WALKORT: the orthotic untouched
    c.append(("WALKORT: an orthotic line is not placed (no line; not in the note)", not L("wrong", "WALKORT") and "WALKORT" not in note, False))
    c.append(("no line of the walk names a medicine outside its own", all(x["k20"] in ITEMS for x in lines), False))
    # the helpers
    if hasattr(E, "_s693_tie"):
        c.append(("_s693_tie: the last 8 characters tie to the one batch", E._s693_tie([("K", "VGT260049"), ("K", "TIEA2")], "GT260049") == ("K", "VGT260049"), True))
        c.append(("_s693_tie: two fits -> None; under 4 characters -> None; the clip ties to the full and the full to the clip", E._s693_tie([("K", "XAB1234"), ("K", "YAB1234")], "AB1234") is None and E._s693_tie([("K", "VGT260049")], "049") is None and E._s693_tie([("K", "EW2A1234")], "NEW2A1234") == ("K", "EW2A1234"), True))
        c.append(("_s693_expiry: '5/99' -> 2099-05, '12/2027' -> 2027-12, '2027-05' kept, junk -> ''", E._s693_expiry("5/99") == "2099-05" and E._s693_expiry("12/2027") == "2027-12" and E._s693_expiry("2027-05") == "2027-05" and E._s693_expiry("x") == "", True))
    else:
        c.append(("_s693_tie exists", False, True))
    con.close()
    return c


def proof(old_root, new_root, db, spine, archive, scratch):
    Eo, En = load(old_root, scratch, "old"), load(new_root, scratch, "new")
    dbo, dbn = os.path.join(scratch, "proof_old.db"), os.path.join(scratch, "proof_new.db")
    shutil.copyfile(db, dbo)
    shutil.copyfile(db, dbn)
    today = dt.datetime.now(IST).date()
    Eo.run(db=dbo, spine_path=spine, archive=archive, today=today, log=lambda *a: None)
    En.run(db=dbn, spine_path=spine, archive=archive, today=today, log=lambda *a: None)

    def lines(p):
        c = sqlite3.connect(p)
        out = {}
        for r in c.execute("SELECT section,part,k20,item,batch,expiry,units,info FROM stock_expiry_line WHERE run_id=(SELECT MAX(id) FROM stock_expiry_run)"):
            out[(r[0], r[1], r[2], r[4])] = dict(item=r[3], expiry=r[5], units=r[6], info=json.loads(r[7]) if r[7] else {})
        ro = c.execute("SELECT export_md5, export_as_on, counts, note FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
        return out, ro
    lo, ro = lines(dbo)
    ln, rn = lines(dbn)
    if not rn[1] or ro[0] != rn[0]:
        return "proof: NOT CLEAN . the two runs read different reports (%s vs %s)" % (ro[0], rn[0])
    sp = sqlite3.connect(spine)
    printed, sa = {}, None
    for pth in En.batch_exports(archive)[:12]:
        try:
            R = En.read_batch_stock(pth)
        except Exception:                                      # noqa: BLE001
            continue
        if R["ok"] and R.get("md5") == rn[0]:
            sa = En._sales_after(R)                            # the day whose END the report stands for (S668): the watch's own cut
            for b in R["batches"]:
                kk = (En.K(b["item"]), En.nbatch(b["batch"]))
                printed[kk] = printed.get(kk, 0) + b["units"]
            break
    if not sa:
        return "proof: NOT CLEAN . the report the runs read (%s) is not in the archive" % rn[0]
    bought = {r[0] for r in sp.execute("SELECT DISTINCT k20 FROM sp_move WHERE kind='PURCHASE' AND date > ?", (sa,))}

    import re as _re

    def _al(x):
        return _re.sub(r'[^A-Z0-9]', '', str(x or "").upper())

    def sold_into(k, batch):
        """Sale lines since the report into this batch -- as printed, or by the kit's letters-and-digits tie (the sale text's spelling)."""
        a = _al(batch)
        n = 0
        for (b2,) in sp.execute("SELECT batch FROM sp_sale_line WHERE k20=? AND date>?", (k, sa)):
            b2a = _al(b2)
            if b2a and (b2a == a or (len(b2a) >= 4 and a.endswith(b2a))):
                n += 1
        return n
    ok, kinds = True, {}

    def note(kind, s):
        kinds[kind] = kinds.get(kind, 0) + 1
        print("  --  %-30s %s" % (kind, s))
    for key in sorted(set(lo) | set(ln)):
        a, b = lo.get(key), ln.get(key)
        if a == b:
            continue
        sec, part, k, batch = key
        if a is None and sec == "wrong" and part == "batch":
            below = [x[0] for x in b["info"].get("below", [])]
            bad = [x for x in below if sold_into(k, x) == 0 and (printed.get((k, x), 0) >= 0 or k not in bought)]
            note("NEW wrong line (%s)" % ("bought" if k in bought else "sale batch tied"), "%s below %s: sales since %s into them %s, printed %s" % (b["item"], below, sa, [sold_into(k, x) for x in below], [printed.get((k, x)) for x in below]))
            if bad:
                ok = False
                print("      RED: a minus batch with neither a sale into it since the report nor a printed minus: %s" % bad)
        elif a is None and sec in ("near", "expired") and k in bought:
            note("NEW %s line (bought)" % sec, "%s %s %s units %s" % (b["item"], batch, b["expiry"], b["units"]))
        elif b is None and sec == "wrong" and part == "batch" and k in bought:
            note("wrong line GONE (bought)", "%s below %s: the purchase brought the batch up" % (a["item"], [x[0] for x in a["info"].get("below", [])]))
        elif a and b and sec in ("near", "expired") and k in bought and b["units"] > a["units"] and a["info"].get("sold_since") == b["info"].get("sold_since"):
            note("%s stock up by the purchase" % sec, "%s %s %d -> %d" % (a["item"], batch, a["units"], b["units"]))
        elif a and b and sec == "wrong":
            ab, bb = [x[0] for x in a["info"].get("below", [])], [x[0] for x in b["info"].get("below", [])]
            ah, bh = [x[0] for x in a["info"].get("has", [])], [x[0] for x in b["info"].get("has", [])]
            new_minus = [x for x in bb if x not in ab]
            bad = [x for x in new_minus if sold_into(k, x) == 0 and (printed.get((k, x), 0) >= 0 or k not in bought)]
            if k not in bought and [x for x in bh if x not in ah]:
                bad.append("has gained %s without a purchase" % [x for x in bh if x not in ah])
            note("wrong line changed (%s)" % ("bought" if k in bought else "sale batch tied"), "%s below %s->%s has %s->%s units %s->%s" % (a["item"], ab, bb, ah, bh, a["units"], b["units"]))
            if bad:
                ok = False
                print("      RED: a new minus batch with neither a sale nor a printed minus: %s" % bad)
        else:
            ok = False
            note("UNEXPLAINED", "%s | old %s | new %s" % (key, str(a)[:140], str(b)[:140]))
    same = sum(1 for key in lo if lo.get(key) == ln.get(key))
    return "proof: old %d lines / new %d lines . identical %d . %s . %s . report %s . %s" % (len(lo), len(ln), same, "CLEAN" if ok else "NOT CLEAN",
                                                                                           json.dumps(kinds, sort_keys=True), (rn[0] or "none")[:8],
                                                                                           (rn[3] or "").split("S693:")[-1].strip()[:120])


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
        c = [("the walk ran to its end (%s: %s)" % (type(ex).__name__, str(ex)[:80]), False, True)]
    red = [t for t, ok, s in c if not ok]
    for t, ok, s in c:
        print("  %s  %s%s" % ("ok " if ok else "RED", t, "  [S693]" if s else ""))
    if a.new:
        print("%d of %d green" % (len(c) - len(red), len(c)))
        sys.exit(1 if red else 0)
    else:
        red693 = [t for t, ok, s in c if not ok and s]
        other = [t for t, ok, s in c if not ok and not s]
        print("%d S693 check(s) red . %d green%s" % (len(red693), len(c) - len(red), " . %d OTHER red" % len(other) if other else ""))


if __name__ == "__main__":
    main()
