#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s926.py -- S926 on a COPY of finance.db (never the live file).
Usage: walk_s926.py <code_dir_with_TO_files> <finance.db copy> [--control]
Every check prints ok/RED and the last line is 'RESULT: ALL PASS' or 'RESULT: n FAIL'; exit 1 on any RED. The control (the FROM files) must go red.
State-aware (F-1465, the S837 rule): every expectation is read from the copy itself -- the doctor's taps of the morning change what is open --
so a frozen fact never stops an install. Reads only the copy; writes only into the copy (the doors are exercised there).
No patient data is printed: items, dealers, counts, dates."""
import datetime as dt
import os
import shutil
import sqlite3
import sys
import tempfile

RED = []


def ck(name, ok, note=""):
    print("%-4s %s%s" % ("ok" if ok else "RED", name, (" -- " + str(note)) if note else ""))
    if not ok:
        RED.append(name)


def finish():
    print("---- %d RED" % len(RED))
    for r in RED:
        print("     RED:", r)
    print("RESULT: ALL PASS" if not RED else "RESULT: %d FAIL" % len(RED))
    sys.exit(1 if RED else 0)


def main():
    code, dbp = sys.argv[1], sys.argv[2]
    work = tempfile.mkdtemp(prefix="s926_", dir=os.environ.get("TMPDIR") or "/tmp")
    db = os.path.join(work, "finance.db")
    shutil.copy(dbp, db)
    sys.path.insert(0, code)
    os.environ.setdefault("PYTHONPYCACHEPREFIX", os.path.join(work, "pyc"))
    try:
        run(code, db)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run(code, db):
    import order_flow as OF                                   # noqa: E402
    import order_s778 as S7                                   # noqa: E402
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    now = dt.datetime.now()
    ver = getattr(OF, "VERSION", "")
    ck("version 2.0", ver == "2.0", ver)
    has = hasattr(OF, "shortages") and hasattr(OF, "identity") and hasattr(OF, "act_s926")
    ck("S926 functions present", has)
    if not has:
        return finish()
    N = OF._norm
    G = OF.groups(con, now)
    idn = OF.identity(con)
    ck("identity: newest closing read", bool(idn["as_on"]), idn["as_on"])
    dead = set(idn["dead"].keys())
    live = set(idn["live"].keys())
    ck("dead names: none is live", not (dead & live), len(dead))
    zero_live = [k for k, (n, q, ps) in idn["live"].items() if int(float(q or 0)) == 0]
    ck("the newest closing lists zero-stock items too (%d of %d) -- the dead-name rule rests on this" % (len(zero_live), len(idn["live"])), len(zero_live) > 0 and len(idn["live"]) > 100)
    ck("dead names: a zero-stock live item is not dead", all(k not in dead for k in zero_live))
    ck("the newest closing is whole (not a cut export)", idn.get("partial") is False)
    # a cut export must name no dead name: simulate on the copy
    con.execute("CREATE TEMP TABLE _keep AS SELECT rowid AS r FROM stock_snapshot WHERE as_on=? AND (rowid % 3)=0", (idn["as_on"],))
    con.execute("DELETE FROM stock_snapshot WHERE as_on=? AND rowid NOT IN (SELECT r FROM _keep)", (idn["as_on"],))
    idp = OF.identity(con)
    ck("a cut closing (one third of the rows) is read as partial and names NO dead name", idp["partial"] is True and not idp["dead"] and not OF.dead_norms(con), (idp["partial"], len(idp["dead"])))
    con.execute("DROP TABLE _keep")
    # restore the rows from the untouched source copy
    src = sqlite3.connect(sys.argv[2])
    con.execute("DELETE FROM stock_snapshot WHERE as_on=?", (idn["as_on"],))
    con.executemany("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,?)",
                    src.execute("SELECT as_on, item, qty, packing, pack_size, loaded_at, source FROM stock_snapshot WHERE as_on=?", (idn["as_on"],)).fetchall())
    src.close()
    con.commit()
    ck("the copy's closing restored for the rest of the walk", len(OF.identity(con)["live"]) == len(idn["live"]))
    dn = set(OF.dead_norms(con))
    ck("dead_norms() never holds a live name", not (dn & live), len(dn))
    partnered = [k for k in dead if any(N(p) in live for p in idn["partner"].get(k, []))]
    ck("a ticked rename's old name is NOT held off the order list (%d such, the 22 orthotics)" % len(partnered), all(k not in dn for k in partnered))
    hid = S7.hidden(con)
    ck("hidden() unions the partnerless dead names", dn <= hid)
    # the identity question, if one stands in this copy
    vf = N("VFER 500")
    pr = [p for p in idn["pairs"] if N(p["old"]) == vf]
    vf_open = bool(pr)
    if vf_open:
        ck("rename pair VFER 500 -> V FER 500 open, with the new name's stock", pr[0]["new"] == "V FER 500" and bool(pr[0]["new_stock"]), pr[0])
        ck("marg stock of the dead name = its live partner's", OF._marg_stock(idn, "VFER 500")[0] == "V FER 500" and OF._marg_stock(idn, "VFER 500")[2] is True, OF._marg_stock(idn, "VFER 500"))
        ck("the partnerless dead name is held off the order list", vf in hid)
    else:
        print("INFO the VFER 500 question is already answered in this copy -- the rename checks run on it as answered")
        ck("VFER 500 answered: not a shortage, not hidden", vf not in dn)
    sh = OF.shortages(con, G, now)
    by = {(s["item"], s["sn"]): s for s in sh}
    ck("shortages: one row per (medicine, dealer)", len(by) == len(sh), len(sh))
    if not sh:
        print("INFO a quiet copy: no shortage open -- the door checks that need one are skipped")
    ck("shortages: the run ends at a line he settled (no 'closed by you' / 'stopped' / 'came later' / 'substitute OK' inside a run)",
       all(not (o["state"] == "settled" and not str(o["how"]).startswith("ordered again") and str(o["how"]) not in ("stopped by you", "your word given", "your word: keep ordering")) for s in sh for o in s["orders"]))
    ck("shortages: every row carries its history, stock and state", all(s["orders"] and s["state"] in OF.SH_ORDER and "marg_stock" in s for s in sh))
    ck("shortages: n_orders = the run's length, came_total <= ordered_total", all(s["n_orders"] == len(s["orders"]) and s["came_total"] <= s["ordered_total"] for s in sh))
    ck("shortages: a 'keeps' row has >= %d re-orders with nothing come after the first" % OF.KEEPS_AFTER,
       all(s["n_reorders"] >= OF.KEEPS_AFTER and all(o["came"] == 0 for o in s["orders"][1:]) for s in sh if s["state"] == "keeps"))
    ck("shortages: an 'oos' row carries the staff tap it rests on", all(s["na"] is not None for s in sh if s["state"] == "oos"))
    ck("shortages: a 'keeps' row's newest order has failed -- never one on the way or awaiting Marg", all(OF._failed(s["orders"][-1]) for s in sh if s["state"] == "keeps"),
       [(s["item"], s["orders"][-1]["state"]) for s in sh if s["state"] == "keeps"])
    ck("shortages: a 'rename' row carries its open pair", all(s["pair"] is not None for s in sh if s["state"] == "rename"))
    if vf_open:
        v = by.get(("VFER 500", "SHIVAAZ FORMULATIONS"))
        ck("VFER 500: state rename, 5 orders, nothing came", bool(v) and v["state"] == "rename" and v["n_orders"] >= 5 and v["came_total"] == 0, (v["state"], v["n_orders"], v["came_total"]) if v else None)
    # a medicine with 15 of 20 came (CHEXID D, 13-Nov) -- as the copy holds it
    c = by.get(("CHEXID D", "GUNINA PHARMACEUTICALS PVT LTD"))
    if c:
        ck("CHEXID D: came 15 of 20 read from the order and its bill", c["came_total"] == 15 and c["ordered_total"] == 20, (c["came_total"], c["ordered_total"]))
    # the auto-escalation, proven on the copy: take a staff-tapped row with >= 2 re-orders, clear its tap, it must come back as 'keeps'
    cand = [s for s in sh if s["state"] == "oos" and s["n_reorders"] >= OF.KEEPS_AFTER and all(o["came"] == 0 for o in s["orders"][1:]) and s["na"]]
    if cand:
        s0 = cand[0]
        saved = dict(con.execute("SELECT * FROM order_s778_na WHERE id=?", (int(s0["na"]["id"]),)).fetchone())
        con.execute("DELETE FROM order_s778_na WHERE id=?", (int(s0["na"]["id"]),))       # as if nobody had tapped
        con.commit()
        p2 = {(s["item"], s["sn"]): s for s in OF.shortages(con, OF.groups(con, now), now)}.get((s0["item"], s0["sn"]))
        ck("without a tap, %d failed orders come to him by themselves (keeps): %s" % (s0["n_orders"], s0["item"]), bool(p2) and p2["state"] == "keeps" and p2["na"] is None, p2["state"] if p2 else None)
        cols = list(saved)
        con.execute("INSERT INTO order_s778_na (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))), [saved[c] for c in cols])
        con.commit()
    else:
        print("INFO no staff-tapped row with %d+ re-orders in this copy: the auto-escalation is proven by the rule check above" % OF.KEEPS_AFTER)
    # suggestion: a medicine first bought from the dealer while the shortage ran
    sug = [s for s in sh if s.get("suggest")]
    ck("substitute suggestions name a medicine first bought after the shortage began", all(s["suggest"]["first"] >= s["first_day"] for s in sug), [(s["item"], s["suggest"]["item"]) for s in sug][:3])
    # the team list every page reads
    team = OF.team(con, G=G)
    ck("team(): one row per shortage, with state, word and Marg stock", all("state" in r and "word_hi" in r and "marg_stock" in r for r in team))
    ck("team(): no one-miss rows -- those stay on the order", not any(r["state"] == "short" for r in team))
    # his page
    html = OF.owner_body(con, now)
    ck("owner page: the section title", "Not delivered, out of stock and substitutes" in html)
    ck("owner page: Stock & ledger frame with the link to the full page", 'data-src="/finance/sanjeevni/ledger?k=' in html and "open the full page" in html)
    if vf_open:
        ck("owner page: the rename question with both taps", "Yes — same medicine" in html and "No — two items" in html)
    if any(s["state"] in ("keeps", "oos") for s in sh):
        ck("owner page: the new buttons", "Substitute: choose" in html and "Stop ordering it" in html and "It came / we have it" in html and "Not needed now" in html)
    ck("owner page: no confirm()/alert()", "confirm(" not in html and "alert(" not in html)
    rec = OF.rec_body(con, now)
    ck("reception's team block renders (his word as an instruction)", rec == "" or "team list" in rec)
    dv = OF.dar_view(con, now)
    ck("Darpan's team rows carry word/stock/n", all("word" in r and "stock" in r and "n" in r for r in dv["team"]))
    line = OF.needs_you_line(con, now)
    ck("Hub line builds from the same rows", line is None or line["text"].startswith("Purchase orders:"), line["text"] if line else None)
    # the pickers
    its = OF.items_like(con, "V FER")
    ck("items picker finds V FER 500 with its stock", any(i["item"] == "V FER 500" and i["stock"] for i in its))
    ck("items picker never offers a partnerless dead name", not any(N(i["item"]) in dn for i in OF.items_like(con, "")))
    ck("dealers picker answers", len(OF.dealers_like(con, "")) >= 3)
    # the doors, on the copy -- targets picked from this copy's own state
    if vf_open:
        r, st = OF.act(con, "walk", dict(do="two", item="VFER 500", sn="", pair=0))
        ck("door two: remembered as two items", st == 200 and r["ok"], r)
        con.execute("UPDATE order_flow_word SET undone_at='walk' WHERE kind='two'")
        con.commit()
        r, st = OF.act(con, "walk", dict(do="same", item="VFER 500", sn="", pair=0))
        ck("door same: accepted", st == 200 and r["ok"], r)
        ok_alias = con.execute("SELECT count(*) FROM marg_item_rename WHERE old_name='VFER 500' AND new_name='V FER 500' AND verified_at IS NOT NULL").fetchone()[0] == 1
        ok_mn = con.execute("SELECT count(*) FROM med_name WHERE kind='marg' AND state='yes' AND ((form='V FER 500' AND item='VFER 500') OR (form='VFER 500' AND item='V FER 500'))").fetchone()[0] == 1
        ok_hc = con.execute("SELECT count(*) FROM marg_hand_change WHERE kind='rename' AND status='open' AND item IN ('VFER 500','V FER 500')").fetchone()[0] == 0
        ck("same: item_alias row verified, the name pair, the hand-change rows closed", ok_alias and ok_mn and ok_hc, (ok_alias, ok_mn, ok_hc))
        ck("same: forms() join the two names", N("V FER 500") in S7.forms_raw(con, "VFER 500"))
        idn2 = OF.identity(con)
        ck("same: no open pair left", not any(N(p["old"]) == vf for p in idn2["pairs"]))
        ck("same: the old name's stock read as the new name's", OF._marg_stock(idn2, "VFER 500")[0] == "V FER 500" and bool(OF._marg_stock(idn2, "VFER 500")[1]))
        na = con.execute("SELECT status FROM order_s778_na WHERE item='VFER 500' AND cleared_at IS NULL AND status='asked'").fetchone()
        if OF._live_qty(idn2, "V FER 500") > 0:
            ck("same: no open out-of-stock ask on the old name remains (the partner holds stock)", na is None)
        else:
            print("INFO V FER 500 holds no stock in this copy: the ask may stand")
        ck("same: the old name no longer held off the order list", vf not in S7.hidden(con))
        ck("same: VFER 500 gone from his list", ("VFER 500", "SHIVAAZ FORMULATIONS") not in {(s["item"], s["sn"]) for s in OF.shortages(con, OF.groups(con, now), now)})
    open_rows = [s for s in OF.shortages(con, OF.groups(con, now), now) if s["state"] in ("keeps", "oos")]
    print("INFO doors: %d rows to exercise" % len(open_rows))
    picks = list(open_rows)

    def take():
        return picks.pop(0) if picks else None
    s = take()
    if s:
        r, st = OF.act(con, "walk", dict(do="sub_by", item=s["item"], sn=s["sn"], sub_item="WALK SUBSTITUTE X", to_sn=s["sn"]))
        ck("door sub_by (%s): substitute placed" % s["item"], st == 200 and r["ok"], r)
        ag = con.execute("SELECT 1 FROM order_s778_again WHERE kind='s926' AND item='WALK SUBSTITUTE X' AND done_at IS NULL AND cleared_at IS NULL").fetchone()
        rule = con.execute("SELECT rule, note FROM order_item_rule WHERE item_norm=?", (N(s["item"]),)).fetchone()
        ck("sub_by: an again row for the substitute on the dealer; the old medicine's rule never, noted", bool(ag) and rule and rule[0] == "never" and "substituted by WALK SUBSTITUTE X" in (rule[1] or ""), tuple(rule) if rule else None)
        t4 = {(x["item"], x["sn"]): x for x in OF.shortages(con, OF.groups(con, now), now)}.get((s["item"], s["sn"]))
        ck("sub_by: the row now reads substitute on its way", bool(t4) and t4["state"] == "sub_way", t4["state"] if t4 else None)
        tm = [x for x in OF.team(con) if x["item"] == s["item"]]
        ck("staff read the substitute as an instruction", bool(tm) and "substitute WALK SUBSTITUTE X" in tm[0]["word_hi"], tm[0]["word_hi"] if tm else None)
    s = take()
    others = [d for d in OF.dealers_like(con, "") if s and d["sn"] != s["sn"]]
    if s and others:
        other = others[0]
        r, st = OF.act(con, "walk", dict(do="other2", item=s["item"], sn=s["sn"], to_sn=other["sn"]))
        ck("door other2 (%s -> %s): ordered from another dealer" % (s["item"], other["short"]), st == 200 and r["ok"] and con.execute("SELECT 1 FROM order_s778_again WHERE kind='s926' AND item=? AND supplier_norm=?", (s["item"], other["sn"])).fetchone() is not None, r)
        ck("other2: the row has left his list", (s["item"], s["sn"]) not in {(x["item"], x["sn"]) for x in OF.shortages(con, OF.groups(con, now), now)})
    s = take()
    if s:
        r, st = OF.act(con, "walk", dict(do="not_now", item=s["item"], sn=s["sn"]))
        held = con.execute("SELECT count(*) FROM order_s778_na WHERE item_norm=? AND status='asked' AND cleared_at IS NULL", (N(s["item"]),)).fetchone()[0]
        ck("door not_now (%s): off his list 30 days AND still held off the order sheet" % s["item"], st == 200 and held >= 1 and N(s["item"]) in S7.hidden(con)
           and (s["item"], s["sn"]) not in {(x["item"], x["sn"]) for x in OF.shortages(con, OF.groups(con, now), now)}, r)
    s = take()
    if s:
        r, st = OF.act(con, "walk", dict(do="stop", item=s["item"], sn=s["sn"]))
        ck("door stop (%s): the rule never" % s["item"], st == 200 and con.execute("SELECT rule FROM order_item_rule WHERE item_norm=?", (N(s["item"]),)).fetchone()[0] == "never", r)
    s = take()
    if s:
        r, st = OF.act(con, "walk", dict(do="came", item=s["item"], sn=s["sn"], note="counted on the shelf"))
        ck("door came (%s): cleared with his note" % s["item"], st == 200 and con.execute("SELECT count(*) FROM order_s778_na WHERE item_norm=? AND status='asked' AND cleared_at IS NULL", (N(s["item"]),)).fetchone()[0] == 0, r)
    s = take()
    if s:
        r, st = OF.act(con, "walk", dict(do="wait2", item=s["item"], sn=s["sn"]))
        ck("door wait2 (%s): a wait mark and the word" % s["item"], st == 200 and con.execute("SELECT count(*) FROM order_flow_mark WHERE kind='wait' AND item=? AND undone_at IS NULL", (s["item"],)).fetchone()[0] >= 1, r)
    s = take()
    if s:
        r, st = OF.act(con, "walk", dict(do="again_sh", item=s["item"], sn=s["sn"]))
        t6 = {(x["item"], x["sn"]): x for x in OF.shortages(con, OF.groups(con, now), now)}.get((s["item"], s["sn"]))
        ck("door again_sh (%s): once more from the same dealer; the row now reads 'on the dealer's next order', not a failure" % s["item"],
           st == 200 and (t6 is None or (t6["state"] == "wait" and (t6["word"] or {}).get("kind") == "again")), (r, t6["state"] if t6 else None))
    s = take()
    if s:
        r, st = OF.rec_act(con, "reception (walk)", dict(do="sub", oid=s["oid"], lid=s["lid"]))
        t5 = {(x["item"], x["sn"]): x for x in OF.shortages(con, OF.groups(con, now), now)}.get((s["item"], s["sn"]))
        ck("reception's 'Substitute aaya' (%s): the row reads substitute arrived" % s["item"], st == 200 and bool(t5) and t5["state"] == "sub_arr", t5["state"] if t5 else None)
        mid = con.execute("SELECT id FROM order_flow_mark WHERE kind='sub' AND line_id=? AND undone_at IS NULL", (int(s["lid"]),)).fetchone()[0]
        r, st = OF.act(con, "walk", dict(do="sub_ok", sub=int(mid)))
        ck("Substitute OK (the S920 door) takes the row off his list", st == 200 and (s["item"], s["sn"]) not in {(x["item"], x["sn"]) for x in OF.shortages(con, OF.groups(con, now), now) if x["state"] != "short"})
    r, st = OF.act(con, "walk", dict(do="sub_by", item="NOTHING HERE", sn="X", sub_item="Y"))
    ck("a door on a medicine with no shortage is refused 409", st == 409, (r, st))
    r, st = OF.act(con, "walk", dict(do="same", item="NO SUCH PAIR", sn=""))
    ck("same on a medicine with no rename question is refused 409", st == 409)
    still = {(x["item"], x["sn"]) for x in OF.shortages(con, OF.groups(con, now), now) if x["state"] in ("keeps", "oos", "rename")}
    answered = open_rows[1:5]                                  # other2 / not_now / stop / came
    ck("after the words: every answered row has left his list", not [x for x in answered if (x["item"], x["sn"]) in still], [x["item"] for x in answered if (x["item"], x["sn"]) in still])
    ck("the S920 doors still answer (sub_ok on a missing id -> 404)", OF.act(con, "walk", dict(do="sub_ok", sub=999999))[1] == 404)
    ck("the whole page renders after the words", "Not delivered" in OF.owner_body(con, now))
    ck("no walk word carries a 10-digit number", not any(any(len(x) >= 10 and x.isdigit() for x in str(w).split()) for w in con.execute("SELECT item, sub_item, note FROM order_flow_word")))
    return finish()


if __name__ == "__main__":
    main()
