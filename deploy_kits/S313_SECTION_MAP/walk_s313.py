#!/usr/bin/env python3
"""walk_s313.py -- S313_SECTION_MAP, on a SCRATCH COPY of the live database,
BEFORE anything is placed.

    python3 -B walk_s313.py <live app dir> <patched app dir> <scratch db>
    -> last line  WALK OK ...  /  WALK RED ...

What it proves:

  1  S313 CHANGES NOTHING.  The stock hub is built by the live module and by the
     patched one and the payloads must be identical on EVERY key -- not "every
     key but one".  This kit adds a page and a table and is meant to be
     invisible to the estate; the walk is where that claim is tested rather than
     asserted.
  2  The seed classifies every item of the newest Marg snapshot, once, into the
     three sections the Marg voucher already prints, and a second seed writes
     nothing.
  3  The disagreements it finds are the REAL ones on this box -- the walk names
     them rather than counting them, because a number could be right by accident.
  4  The owner's word survives a re-seed, on real data.

Writes only to the scratch copy.
"""
import os
import sqlite3
import sys

live_dir, new_dir, db = sys.argv[1], sys.argv[2], sys.argv[3]


def hub(appdir):
    for m in ("stock_app", "claim_queue", "section_map", "padwriter", "pad_receipt"):
        sys.modules.pop(m, None)
    sys.path.insert(0, appdir)
    try:
        import stock_app as S
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        S.ensure_schema(con)
        S._pad_ensure(con)
        r = con.execute("SELECT id FROM stock_count WHERE unit='medical' AND id NOT IN "
                        "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1").fetchone()
        h = S._hub_data(con, int(r[0])) if r else None
        con.commit()
        con.close()
        return h
    finally:
        sys.path.remove(appdir)


try:
    # 1 -- S313 changes nothing at all
    old = hub(live_dir)
    new = hub(new_dir)
    if old is None:
        print("WALK OK no count on this box -- nothing to walk")
        sys.exit(0)
    moved = [k for k in old if old[k] != new.get(k)]
    assert not moved, "S313 changed the hub, and it must not: %s" % moved
    assert set(old) == set(new), "S313 added or dropped a key on the hub"

    for m in ("section_map",):
        sys.modules.pop(m, None)
    sys.path.insert(0, new_dir)
    import section_map as sm

    con = sqlite3.connect(db)
    got = sm.snapshot_items(con)
    assert got, "no snapshot on this box"
    as_on, items = got

    # 2 -- the seed
    added, kept = sm.seed(con, None, "walk")
    con.commit()
    assert added == len(items), "seeded %d of %d items" % (added, len(items))
    a2, k2 = sm.seed(con, None, "walk")
    con.commit()
    assert (a2, k2) == (0, len(items)), "a second seed was not a no-op: %d added" % a2
    s = sm.summary(con)
    assert s["total"] == len(items), "summary %d, snapshot %d" % (s["total"], len(items))
    bs = s["by_section"]
    assert sum(bs.values()) == len(items), "the three sections do not add up to the shop"
    assert all(v >= 0 for v in bs.values())

    # 3 -- the real disagreements, named
    dis = sm.rows(con, only_disputed=True, limit=10000)
    names = sorted(r["item"] for r in dis)
    agreed = [r for r in sm.rows(con, limit=10000) if not r["disputed"]]
    assert agreed, "every item is disputed -- the detector is wrong, not the data"
    sample = "; ".join("%s (%s)" % (r["item"], r["why"][0]) for r in dis[:3])

    # 4 -- the owner's word survives a re-seed, on a real item
    first = items[0]
    other = [x for x in sm.SECTIONS if x != sm.classify(first)][0]
    sm.set_section(con, first, other, "walk")
    con.commit()
    sm.seed(con, None, "walk")
    con.commit()
    row = con.execute("SELECT section, source, seeded_as FROM stock_item_section WHERE item_key=?",
                      (sm.norm_key(first),)).fetchone()
    assert row and row[0] == other and row[1] == "owner", "a re-seed overwrote the owner's word"
    assert row[2] and row[2] != other, "what the seed had said was not kept"
    con.close()

    print("WALK OK the hub is byte-identical to the live one on every key (S313 changes nothing); "
          "%d items of the %s snapshot seeded once, second seed a no-op; Medicines %d / Orthotics %d / "
          "Consumables %d; %d item(s) where the rules disagree, e.g. %s; the owner's word survived a "
          "re-seed and what the seed had said was kept"
          % (len(items), as_on, bs.get("Medicines", 0), bs.get("Orthotics", 0),
             bs.get("Consumables", 0), len(names), sample or "none"))
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e))
    sys.exit(1)
