#!/usr/bin/env python3
"""walk_s299.py -- on the box, BEFORE anything is placed: the patched stock module against a
scratch copy of the live database. The hub builds, (S299) a Yes is issue + receive vouchers at once, the swaps are proposed, one Yes lands and
takes its units off both lines, taking it back restores them, Darpan's list says what it waits
for, and a list with a swapped line renders. Writes only to the scratch copy.
    python3 -B walk_s299.py <patched app dir> <scratch db>        -> last line WALK OK ... / WALK RED ..."""
import sys, os, sqlite3
app, db = sys.argv[1], sys.argv[2]
sys.path.insert(0, app)
try:
    import stock_app as S, pad_receipt as PR
    con = sqlite3.connect(db); S.ensure_schema(con); S._pad_ensure(con)
    r = con.execute("SELECT id FROM stock_count WHERE unit='medical' AND id NOT IN (SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1").fetchone()
    if not r:
        print("WALK OK no count on this box -- nothing to walk"); sys.exit(0)
    cid = int(r[0])
    h = S._hub_data(con, cid)
    assert h and h["ok"], "hub did not build"
    M = h["match"]
    print("count #%d: %d pairs proposed (%d orthotic units), %d answered; hold: %s" % (cid, M["total"], M["units"], M["answered"], h["lists"]["hold"] or "none"))
    step = ""
    todo = [x for x in M["rows"] if not x["settled"]]
    if todo:
        p = todo[0]
        before = {x["item"]: x["diff"] for x in S._pad_report_data(con, cid)["differences"]}
        con.execute("INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, note, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                    (h["count_id"], p["short"], p["over"], p["qty"], "YES", "walk", "walk", S.now_iso()))
        d = S._pad_report_data(con, cid)
        after = {x["item"]: x["diff"] for x in d["differences"]}
        assert after[p["short"]] == before[p["short"]] + p["qty"], "the Yes did not reduce the short line"
        assert after[p["over"]] == before[p["over"]] - p["qty"], "the Yes did not reduce the extra line"
        sv = [(v["voucher"], v["item"], v["qty"]) for v in S._swap_vouchers(d)]          # S299: the Yes is on the vouchers at once
        assert ("ISSUE", p["short"], p["qty"]) in sv and ("RECEIVE", p["over"], p["qty"]) in sv, "the Yes did not become issue + receive vouchers"
        assert all(r[5] != 0 for r in S._cleanup_rows(d)), "a cleanup row reads CHANGE 0"
        assert len((S._amir_board(con, cid) or {}).get("vouchers", {}).get("swap") or []) >= 2, "Amir's board does not list the swap vouchers"
        hv = S._hub_data(con, cid)["vouchers"]
        assert hv["swap_issue"] >= 1 and hv["swap_receive"] >= 1, "the hub's step 6 does not count the swap vouchers"
        con.execute("INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, note, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                    (h["count_id"], p["short"], p["over"], p["qty"], "OPEN", "walk", "walk", S.now_iso()))
        back = {x["item"]: x["diff"] for x in S._pad_report_data(con, cid)["differences"]}
        assert back == before, "taking the answer back did not restore the lines"
        step = "; a Yes on %s / %s took %d off both lines, gave STOCK ISSUE + STOCK RECEIVE, and taking it back restored them" % (p["short"], p["over"], p["qty"])
    pdf = PR.render_tranche(dict(count_id=cid, day=h["day"], reasons=[(1, "count error", "")],
                                 tranche=dict(no=1, kind="ortho", issued_text="walk"),
                                 rows=[dict(item="WALK ITEM", packing="1*1", pack=1, marg=3, counted=0, diff=-3, swapped=2, swap_with=["WALK OTHER"])]))
    assert pdf[:5] == b"%PDF-", "the list did not render"
    con.rollback(); con.close()
    print("WALK OK hub builds, %d pairs%s, list renders" % (M["total"], step))
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e)); sys.exit(1)
