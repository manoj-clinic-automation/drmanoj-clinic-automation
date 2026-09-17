#!/usr/bin/env python3
"""walk_s301.py -- on the box, BEFORE anything is placed: the patched stock module against a SCRATCH
copy of the live database. The hub and Amir's board build with the vouchers; a Yes on a proposed
swap waits as STOCK ISSUE + STOCK RECEIVE; a round is made and its lines chain from Marg's figure;
the round's workbook is written; a voucher is recorded as entered; taking the Yes back puts a
reversal on the waiting list. Writes only to the scratch copy.
    python3 -B walk_s301.py <patched app dir> <scratch db>        -> last line WALK OK ... / WALK RED ..."""
import sys, sqlite3
app, db = sys.argv[1], sys.argv[2]
sys.path.insert(0, app)
try:
    import stock_app as S
    con = sqlite3.connect(db); S.ensure_schema(con); S._pad_ensure(con)
    r = con.execute("SELECT id FROM stock_count WHERE unit='medical' AND id NOT IN (SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1").fetchone()
    if not r:
        print("WALK OK no count on this box -- nothing to walk"); sys.exit(0)
    cid = int(r[0])
    h = S._hub_data(con, cid)
    assert h and h["ok"] and "pending" in h["vouchers"], "the hub did not build with the vouchers"
    ab = S._amir_board(con, cid)
    assert ab and "made" in ab, "Amir's board did not build with the vouchers"
    print("count #%d: %d waiting to go on a voucher, %d rounds made" % (cid, len(ab["made"]["pending"]), len(ab["made"]["rounds"])))
    step = ""
    todo = [x for x in h["match"]["rows"] if not x["settled"]]
    if todo:
        p = todo[0]
        con.execute("INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, note, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                    (h["count_id"], p["short"], p["over"], p["qty"], "YES", "walk", "walk", S.now_iso()))
        con.commit()
        d = S._pad_report_data(con, cid)
        pend = {(x["kind"], x["item"]) for x in S._voucher_pending(con, d)}
        assert ("ISSUE", p["short"]) in pend and ("RECEIVE", p["over"]) in pend, "the Yes is not waiting as ISSUE + RECEIVE"
        rno, n = S._voucher_make(con, d, {"user": "walk"})
        assert rno and n >= 2, "no round made"
        by = {x["item"]: x for x in d["differences"]}
        for it, mf, ch, mt in con.execute("SELECT item, marg_from, change, marg_to FROM stock_voucher_line WHERE count_id=? AND round_no=? AND item IN (?,?)",
                                          (h["count_id"], rno, p["short"], p["over"])):
            assert mt == mf + ch, "a line does not add up: %s" % it
        wb = S._voucher_workbook(con, d, rno)
        assert wb and wb[:2] == b"PK", "the round's workbook was not written"
        con.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                    (h["count_id"], rno, "ISSUE", 1, "WALK", "walk", "walk", S.now_iso()))
        con.commit()
        assert S._voucher_state(con, d)["batches_entered"] >= 1, "the entered voucher was not read back"
        con.execute("INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, note, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                    (h["count_id"], p["short"], p["over"], p["qty"], "OPEN", "walk", "walk", S.now_iso()))
        con.commit()
        d = S._pad_report_data(con, cid)
        pend = {}
        for x in S._voucher_pending(con, d):
            pend[x["item"]] = pend.get(x["item"], 0) + x["change"]
        need = {}
        for v in S._swap_vouchers(d):
            need[v["item"]] = need.get(v["item"], 0) + v["change"]
        for x in S._word_vouchers(d):
            need[x["item"]] = need.get(x["item"], 0) + x["change"]
        frozen = S._voucher_frozen(con, h["count_id"])
        off = [i for i in set(need) | set(frozen) | set(pend) if frozen.get(i, 0) + pend.get(i, 0) != need.get(i, 0)]
        assert not off, "after the Yes was taken back, made + waiting does not equal what the lines need: %s" % off[:3]
        assert pend.get(p["short"], 0) > 0 or need.get(p["short"], 0) != 0, "taking the Yes back did not put a reversal on the waiting list"
        step = "; a Yes on %s / %s waited as ISSUE + RECEIVE, round %d made (%d lines, workbook written), one voucher recorded, the Yes taken back: made + waiting = what every line needs" % (p["short"], p["over"], rno, n)
    con.close()
    print("WALK OK hub and Amir's board build with the vouchers%s" % step)
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e)); sys.exit(1)
