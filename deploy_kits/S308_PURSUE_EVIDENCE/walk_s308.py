#!/usr/bin/env python3
"""walk_s308.py -- on the box, BEFORE anything is placed: the patched stock module against a SCRATCH copy of the
live database. The hub builds with step 8's cards; every line the owner has marked to pursue gets a card, and with
one more line marked on the scratch copy a card is built for it too, with its own words. Writes only to the copy.
    python3 -B walk_s308.py <patched app dir> <scratch db>        -> last line WALK OK ... / WALK RED ..."""
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
    assert h and h["ok"] and isinstance(h["pursue"].get("cards"), list), "the hub did not build with step 8's cards"
    live = len(h["pursue"]["cards"])
    assert live == h["pursue"]["lines"] or live == 40, "a pursued line without a card"
    d = S._pad_report_data(con, cid)
    open_short = [x for x in d["differences"] if x["diff"] < 0 and not x.get("word")]
    extra = ""
    if open_short:
        x = sorted(open_short, key=lambda y: int(y.get("mrp_p") or 0))[0]
        con.execute("INSERT INTO stock_diff_lane (count_id, item, action, note, by_user, at) VALUES (?,?,?,?,?,?)",
                    (h["count_id"], x["item"], "RECOVER", None, "walk", S.now_iso()))
        con.commit()
        c = [y for y in S._pursue_cards(con, S._pad_report_data(con, cid)) if y["item"] == x["item"]]
        assert c and c[0]["lines"], "the marked line got no evidence"
        extra = "; one more line marked on the copy reads: %s" % c[0]["lines"][0][:90]
    con.close()
    print("WALK OK hub builds; %d pursued line(s) carry a card today%s" % (live, extra))
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e)); sys.exit(1)
