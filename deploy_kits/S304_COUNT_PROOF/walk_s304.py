#!/usr/bin/env python3
"""walk_s304.py -- on the box, BEFORE anything is placed: the patched stock module against a SCRATCH copy of
the live database. The hub builds and its step 7 comes from the proof, not from the counting close; the proof
reads whatever vouchers and exports the box holds; and with a round made and entered on the scratch copy it
still answers (wait / now / done) without error. Writes only to the scratch copy.
    python3 -B walk_s304.py <patched app dir> <scratch db>        -> last line WALK OK ... / WALK RED ..."""
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
    assert h and h["ok"] and "text" in h["proof"], "the hub did not build with the proof"
    live = h["proof"]
    print("count #%d: step 7 today = %s -- %s" % (cid, live["state"], live["text"][:140]))
    d = S._pad_report_data(con, cid)
    rno, n = S._voucher_make(con, d, {"user": "walk"})
    if rno:
        for b in S._voucher_state(con, d)["rounds"][-1]["batches"]:
            con.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                        (h["count_id"], rno, b["kind"], b["batch_no"], "WALK", "walk", "walk", S.now_iso()))
        con.commit()
    p = S._proof_state(con, S._pad_report_data(con, cid))
    assert p["state"] in ("wait", "now", "done") and p["text"], "the proof did not answer"
    assert not (p["state"] == "done" and not p["items"]), "done with nothing proven"
    con.close()
    print("WALK OK hub builds with the proof (today: %s); with a round of %d lines entered on the scratch copy: %s" % (live["state"], n, p["state"]))
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e)); sys.exit(1)
