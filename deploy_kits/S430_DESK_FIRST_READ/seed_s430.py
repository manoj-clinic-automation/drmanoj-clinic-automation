#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s430.py -- kit S430_DESK_FIRST_READ. The owner's words of 27-Sep as DATA, on the live database after a green restart, each
write audited and idempotent:
  * ECONORM CAP and PARI CR 25 -> owner's use (a stock_pile_move row each, by 'owner (S430, said in chat 27-Sep)')
  * the consumption list gains VINBACTUM DS, VINTAZ P 4500 INJ and VINTAZ P 4500 (the two spellings of one product)
  * the two VINTAZ spellings joined in the rename memory (marg_item_rename, the D620 way: planned + ticked + verified -- both names
    are in Marg's exports already, so it is a fact, not a pending rename); every import keys them to one line
  * the settings stock.old_stock_days (180) and spot.dead_high_value_p (Rs 2,000) where absent
  * the count-#1 traces whose anchor is the count itself re-labelled 'first_count'; their Needs-you lines expired

  seed_s430.py --app DIR --db PATH      (DIR = the finance folder carrying loss_piles.py v2.1 and stock_watch.py v1.1)
"""
import argparse
import datetime as dt
import json
import sqlite3
import sys

WHO = "owner (S430, said in chat 27-Sep)"
OWNER_USE = ("ECONORM CAP", "PARI CR 25")
CONSUME_ADD = ("VINBACTUM DS", "VINTAZ P 4500 INJ", "VINTAZ P 4500")
ALIAS = ("VINTAZ P 4500 INJ", "VINTAZ P 4500")               # old (the count's key), new (the other spelling)


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def seed(db, app):
    sys.path.insert(0, app)
    import loss_piles                                         # noqa: PLC0415 -- the copies beside the app, never the kit's
    import stock_watch                                        # noqa: PLC0415
    import item_alias                                         # noqa: PLC0415
    con = sqlite3.connect(db, timeout=30)
    loss_piles.ensure(con)
    stock_watch.ensure(con)
    item_alias.ensure(con)
    wrote = loss_piles.seed(con, "S430") + stock_watch.seed(con, "S430")
    print("   settings written: %s" % (", ".join(wrote) or "none (all already set)"))
    root = con.execute("SELECT MAX(id) FROM stock_count WHERE id NOT IN (SELECT count_id FROM stock_count_part)").fetchone()[0] or 1
    ts = now_iso()
    # owner's use
    for item in OWNER_USE:
        last = con.execute("SELECT pile FROM stock_pile_move WHERE count_id=? AND item=? ORDER BY id DESC LIMIT 1", (root, item)).fetchone()
        if last and last[0] == "owner_use":
            print("   %s: already owner's use" % item)
            continue
        if not con.execute("SELECT 1 FROM stock_diff WHERE count_id=? AND item=?", (root, item)).fetchone():
            print("   %s: not a line of count #%d -- nothing moved" % (item, root))
            continue
        con.execute("INSERT INTO stock_pile_move (count_id, item, pile, by_user, at) VALUES (?,?,?,?,?)", (root, item, "owner_use", WHO, ts))
        loss_piles._audit(con, root, "move", dict(item=item, pile="owner_use", was=(last[0] if last else "auto"), text="%s moved -> Owner's use (the owner, 27-Sep, said in chat: domestic consumption, not billed)" % item), WHO)
        print("   %s -> owner's use" % item)
    con.commit()
    # the consumption list
    for name in CONSUME_ADD:
        ok, msg = loss_piles.set_setting_req(con, "stock.consume_items", dict(add=name), WHO, root)
        print("   consumption list: %s" % msg)
    # the two VINTAZ spellings, joined
    old, new = ALIAS
    if con.execute("SELECT 1 FROM marg_item_rename WHERE old_name=? OR new_name=?", (old, new)).fetchone():
        print("   rename memory: %s <-> %s already there" % (old, new))
    else:
        con.execute("INSERT INTO marg_item_rename (old_name, new_name, old20, old27, new20, new27, family, planned_by, planned_at, done_by, done_at, verified_at, verified_as_on, note) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (old, new, item_alias.clip(old, 20), item_alias.clip(old, 27), item_alias.clip(new, 20), item_alias.clip(new, 27), "Vintaz P 4500",
                     WHO, ts, WHO, ts, ts, None, "S430: two spellings of one product on the count and in Marg's exports -- joined, not a rename to do"))
        item_alias._audit(con, WHO, "alias_joined", dict(old=old, new=new, note="S430: the two spellings are one product; every import keys them to one line"))
        print("   rename memory: %s <-> %s joined (verified: both spellings are in Marg's exports)" % (old, new))
    con.commit()
    # the count's own traces: no earlier point -> first_count; their Needs-you lines expire
    ids = [r[0] for r in con.execute("SELECT id FROM stock_trace WHERE verdict='unexplained' AND trigger='big_loss' AND findings_json LIKE '%\"anchor\": \"the full count%'")]
    if ids:
        q = ",".join("?" * len(ids))
        con.execute("UPDATE stock_trace SET verdict='first_count' WHERE id IN (%s)" % q, ids)
        yesterday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
        con.execute("UPDATE stock_watch_notice SET until=? WHERE kind='trace_unexplained' AND ref IN (%s)" % q, [yesterday] + [str(i) for i in ids])
        stock_watch._audit(con, "trace_first_count", dict(n=len(ids), text="%d count-#1 traces re-labelled 'no earlier point -- first count' (S430); their Needs-you lines expired" % len(ids)), "S430")
        con.commit()
    print("   traces re-labelled first_count: %d; open notices left: %d" % (len(ids), con.execute("SELECT COUNT(*) FROM stock_watch_notice WHERE until>=?", (dt.date.today().isoformat(),)).fetchone()[0]))
    con.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.db, a.app))
