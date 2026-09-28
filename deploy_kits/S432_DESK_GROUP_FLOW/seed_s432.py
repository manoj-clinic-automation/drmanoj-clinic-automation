#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s432.py -- kit S432_DESK_GROUP_FLOW. On the live database after a green restart (and on the walk's scratch copy first), each
write audited and idempotent:
  * BELL CAST 5 -> Consumables in the section map (stock_item_section), audited "S432, cast material" (the brief, 3.4)
  * the desk's new tables and columns (loss_piles.ensure / stock_watch.ensure) -- created here so the first read finds them
  * the pile cache and the stored watch WARMED for the newest whole-shop count, so the owner's first read after the install is a
    plain read (a failed warm-up is not fatal: the first read builds them)

  seed_s432.py --app DIR --db PATH      (DIR = the finance folder carrying loss_piles.py v2.2 and stock_watch.py v1.2)
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time

WHO = "S432, cast material"
MOVE = ("BELL CAST 5", "Consumables")


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def seed(db, app):
    sys.path.insert(0, app)
    import section_map                                        # noqa: PLC0415 -- the copies beside the app, never the kit's
    import loss_piles                                         # noqa: PLC0415
    import stock_watch                                        # noqa: PLC0415
    con = sqlite3.connect(db, timeout=30)
    section_map.ensure(con)
    loss_piles.ensure(con)
    stock_watch.ensure(con)
    item, to = MOVE
    row = con.execute("SELECT section, source FROM stock_item_section WHERE item_key=?", (section_map.norm_key(item),)).fetchone()
    if row and row[0] == to:
        print("   %s: already in %s (%s)" % (item, to, row[1]))
    else:
        ok, msg = section_map.set_section(con, item, to, WHO)
        try:
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        ("stock_item_section", 0, "section_set", json.dumps(dict(item=item, section=(row[0] if row else None))),
                         json.dumps(dict(item=item, section=to, text="%s moved to %s -- cast material (the brief S432, 3.4)" % (item, to))), WHO, now_iso()))
        except sqlite3.Error:
            pass
        con.commit()
        print("   %s: %s -> %s (%s)" % (item, (row[0] if row else "not in the map"), to, msg))
    root = con.execute("SELECT MAX(id) FROM stock_count WHERE id NOT IN (SELECT count_id FROM stock_count_part)").fetchone()[0] or 0
    con.close()
    # the warm-up: the cache and the stored watch for the newest whole-shop count, through the real app over this database
    if not root:
        print("   no whole-shop count: nothing to warm")
        return 0
    try:
        os.environ["FINANCE_DB"] = db
        os.chdir(app)
        import finance_app as fa                              # noqa: PLC0415
        import stock_app                                      # noqa: PLC0415
        with fa.app.test_request_context():
            c2 = stock_app._db()
            stock_app.ensure_schema(c2)
            t0 = time.time()
            got = loss_piles.cached(c2, root, force=True, who="S432 warm-up")
            t1 = time.time()
            V = stock_watch.stored_owner_view(c2, root)
            t2 = time.time()
            lines, over, skipped, info = got
            print("   warmed count #%d: %d desk lines + %d over in %d ms (%s); the watch %s in %d ms" % (
                root, len(lines), len(over), int((t1 - t0) * 1000), info.get("built"), "stored" if V.get("stored") else "not stored", int((t2 - t1) * 1000)))
            r = c2.execute("SELECT stamp FROM stock_pile_cache_meta WHERE count_id=?", (root,)).fetchone()
            print("   stamp: %s" % ", ".join("%s=%s" % (k, v) for k, v in sorted(json.loads(r[0]).items()) if k in ("v", "spine", "moves", "words", "runs")))
    except Exception as e:                                    # noqa: BLE001 -- the first read builds what the warm-up did not
        print("   warm-up skipped: %s: %s" % (type(e).__name__, str(e)[:160]))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.db, a.app))
