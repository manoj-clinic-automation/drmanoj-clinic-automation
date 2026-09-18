#!/usr/bin/env python3
"""walk_s312.py -- S312_CLAIM_QUEUE, on a SCRATCH COPY of the live database,
BEFORE anything is placed.

    python3 -B walk_s312.py <live app dir> <patched app dir> <scratch db>
    -> last line  WALK OK ...  /  WALK RED ...

What it proves, in this order, because each step is worthless without the one
before it:

  1  OLD = NEW.  The hub is built twice -- once by the LIVE module and once by
     the PATCHED one -- and every key of the payload must be byte-identical
     EXCEPT 'pursue'.  A kit that quietly moved a figure somewhere else on the
     owner's page would be caught here and nowhere else.
  2  The claims appear, and they appear from HIS OWN WORDS -- one live claim for
     each line whose word is RECOVER, and no others.
  3  The whole state machine, on real rows: Darpan answers, the owner settles,
     and step 8 reaches DONE -- which it has never been able to do.
  4  A word taken back withdraws the claim and RECORDS it.
  5  The self-close is honest on real data: with no purchase return stored on
     this box, the sweep closes nothing, whatever else is in the database.

Writes only to the scratch copy.  Never to the live database, never to the live
files.
"""
import sqlite3
import sys

live_dir, new_dir, db = sys.argv[1], sys.argv[2], sys.argv[3]


def hub(appdir, cid):
    for m in ("stock_app", "claim_queue", "padwriter", "pad_receipt"):
        sys.modules.pop(m, None)
    sys.path.insert(0, appdir)
    try:
        import stock_app as S
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        S.ensure_schema(con)
        S._pad_ensure(con)
        h = S._hub_data(con, cid)
        con.commit()
        con.close()
        return S, h
    finally:
        sys.path.remove(appdir)


try:
    con = sqlite3.connect(db)
    r = con.execute("SELECT id FROM stock_count WHERE unit='medical' AND id NOT IN "
                    "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1").fetchone()
    con.close()
    if not r:
        print("WALK OK no count on this box -- nothing to walk")
        sys.exit(0)
    cid = int(r[0])

    # 1 -- old = new everywhere but step 8
    _, old = hub(live_dir, cid)
    S, new = hub(new_dir, cid)
    assert old and new and new["ok"], "the hub did not build"
    moved = [k for k in old if k != "pursue" and old[k] != new.get(k)]
    assert not moved, "the patch moved something outside step 8: %s" % moved
    assert set(old) - {"pursue"} <= set(new), "the patch dropped a key from the hub"
    n_pursue = new["pursue"]["lines"]

    # 2 -- the claims come from his own words, and only from them
    assert new["pursue"]["queue_ok"], "the claim queue did not load: %s" % new["pursue"].get("note")
    # ...and it must be THE ONE BEING INSTALLED, not another copy that happens to be
    # on the path.  Without this the walk passes on a box where the file was never
    # placed, which is exactly the kind of green that teaches nothing.
    import os
    used = os.path.abspath(getattr(S._cq, "__file__", "") or "")
    want = os.path.abspath(os.path.join(new_dir, "claim_queue.py"))
    assert used == want, "the patched module loaded %s, not the kit's %s" % (used, want)
    sys.path.insert(0, new_dir)
    for _m in ("claim_queue",):
        sys.modules.pop(_m, None)
    import claim_queue as cq
    con = sqlite3.connect(db)
    live_claims = con.execute("SELECT item FROM claim_line WHERE count_id=? AND state<>'settled'",
                              (new["count_id"],)).fetchall()
    words = con.execute("SELECT item FROM stock_diff_lane WHERE count_id=? AND action='RECOVER'",
                        (new["count_id"],)).fetchall()
    said = set(cq.norm_key(w[0]) for w in words)
    got = set(cq.norm_key(c[0]) for c in live_claims)
    assert got <= said, "a claim exists for a line he never marked: %s" % (got - said)
    assert len(got) == n_pursue, "claims %d, pursued lines %d" % (len(got), n_pursue)
    s0 = cq.summary(con, new["count_id"])
    assert s0["live"] == n_pursue, "summary disagrees with the page"

    # 3 -- the state machine on the real rows
    ids = [int(x[0]) for x in con.execute(
        "SELECT id FROM claim_line WHERE count_id=? AND state<>'settled' ORDER BY id",
        (new["count_id"],)).fetchall()]
    assert ids, "no claim to walk"
    ok, _m = cq.answer(con, ids[0], "sold_no_bill", "walk", "darpan")
    assert ok, "Darpan's answer refused"
    assert con.execute("SELECT state FROM claim_line WHERE id=?", (ids[0],)).fetchone()[0] == "contacted"
    bad, _m = cq.answer(con, ids[0], "nonsense", "", "darpan")
    assert not bad, "an answer off the list was accepted"
    for i in ids:
        cq.settle(con, i, "written_off", "walk", "manoj")
    con.commit()
    st = cq.step8_state(con, new["count_id"], n_pursue)
    assert st == "done", "step 8 did not reach done, it reads %r" % st
    _, again = hub(new_dir, cid)
    assert again["pursue"]["state"] == "done", "the page does not show what the queue says"

    # 4 -- a word taken back
    con = sqlite3.connect(db)
    first = con.execute("SELECT item FROM stock_diff_lane WHERE count_id=? AND action='RECOVER' LIMIT 1",
                        (new["count_id"],)).fetchone()
    taken = ""
    if first:
        con.execute("INSERT INTO stock_diff_lane (count_id, item, action, note, by_user, at) "
                    "VALUES (?,?,?,?,?,?)", (new["count_id"], first[0], "PARKED", "walk", "walk",
                                             cq.now_iso()))
        con.commit()
        con.close()
        _, after = hub(new_dir, cid)
        con = sqlite3.connect(db)
        row = con.execute("SELECT state, outcome FROM claim_line WHERE count_id=? AND item_key=?",
                          (new["count_id"], cq.norm_key(first[0]))).fetchone()
        assert row and row[0] == "settled", "the claim survived the word being taken back"
        assert con.execute("SELECT COUNT(*) FROM claim_line WHERE item_key=?",
                           (cq.norm_key(first[0]),)).fetchone()[0] == 1, "the withdrawal made a second row"
        taken = "; a word taken back withdrew its claim and kept the row"

    # 5 -- the self-close is honest on real data
    have = cq._returns_available(con)
    neg = con.execute("SELECT COUNT(*) FROM purchase_bill WHERE COALESCE(amount_p,0) < 0").fetchone()[0]
    con.execute("UPDATE claim_line SET state='open', outcome=NULL, settled_at=NULL WHERE count_id=?",
                (new["count_id"],))
    con.commit()
    sw = cq.sweep(con)
    con.commit()
    if not have:
        assert sw["closed_return"] == 0, "the sweep closed a claim on a return that is not stored"
    still = con.execute("SELECT COUNT(*) FROM claim_line WHERE count_id=? AND state='open'",
                        (new["count_id"],)).fetchone()[0]
    assert still or sw["closed_count"], "claims vanished in the sweep"
    con.close()

    print("WALK OK old = new on every key but step 8; %d pursued line(s) carry a claim; "
          "Darpan answered, the owner settled, step 8 reached DONE%s; purchase returns stored on this "
          "box: %s (%d credit note(s) seen, flagged as candidates, %d claim(s) closed by them)"
          % (n_pursue, taken, ("yes" if have else "NO -- the return rule stays asleep, by design"),
             neg, sw["closed_return"]))
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e))
    sys.exit(1)
