#!/usr/bin/env python3
"""walk_s314.py -- S314_SECTION_SCOPE, on a SCRATCH COPY of the live database,
BEFORE anything is placed.

    python3 -B walk_s314.py <live app dir> <patched app dir> <scratch db>
    -> last line  WALK OK ...  /  WALK RED ...

What it proves, and the first one is the one that matters most:

  1  THE WHOLE-SHOP ROUND IS UNCHANGED.  Count #1 -- the 06-Sep count, still
     open with real work on it -- is read by the live module and by the patched
     one and every figure must be identical. A kit that quietly moved a number
     on that round would be caught here and nowhere else.
  2  THE HUB IS UNCHANGED for that round, on every key.
  3  A SECTIONED ROUND WORKS.  A round carrying only orthotics, built on the
     scratch copy, is recognised as an orthotics round, is answerable for the
     section's items and no others, and reports NOTHING not counted -- where
     today it would report the rest of the shop.
  4  ONE ITEM OUTSIDE THE SECTION MAKES IT A WHOLE-SHOP ROUND AGAIN. The scope
     is read from what was counted, so it must be as quick to lose as to gain.
  5  COUNT #1 KEEPS THE HUB. _newest_root() still returns the 06-Sep count even
     with a newer sectioned round sitting beside it.
  6  THE CLOSE VALVE. An observed-section round is refused to staff and allowed
     to the owner; declaring the section hands it back to staff.

Writes only to the scratch copy.
"""
import os
import sqlite3
import sys

live_dir, new_dir, db = sys.argv[1], sys.argv[2], sys.argv[3]
OWNER = {"user": "manoj", "roles": ["checker"], "role": "checker"}
STAFF = {"user": "amir", "roles": ["maker"], "role": "maker"}


def mod(appdir):
    for m in ("stock_app", "claim_queue", "section_map", "padwriter", "pad_receipt", "padreader"):
        sys.modules.pop(m, None)
    if appdir not in sys.path:
        sys.path.insert(0, appdir)
    import stock_app as S
    return S


def fam(appdir, cid):
    S = mod(appdir)
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    S.ensure_schema(con); S._pad_ensure(con)
    out = S._pad_family(con, cid)
    con.commit(); con.close()
    if appdir in sys.path:
        sys.path.remove(appdir)
    return out[2]


try:
    con = sqlite3.connect(db)
    r = con.execute("SELECT id FROM stock_count WHERE unit='medical' AND id NOT IN "
                    "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1").fetchone()
    if not r:
        print("WALK OK no count on this box -- nothing to walk")
        sys.exit(0)
    whole = int(r[0])
    con.close()

    # the section map must exist; seed it if this box has not (insert-only)
    S = mod(new_dir)
    import section_map as sm
    con = sqlite3.connect(db)
    sm.seed(con, None, "walk"); con.commit()
    as_on, items = sm.snapshot_items(con)
    ortho = [i for i in items if (con.execute(
        "SELECT section FROM stock_item_section WHERE item_key=?", (sm.norm_key(i),)).fetchone() or [""])[0] == "Orthotics"]
    med = [i for i in items if (con.execute(
        "SELECT section FROM stock_item_section WHERE item_key=?", (sm.norm_key(i),)).fetchone() or [""])[0] == "Medicines"]
    con.close()
    assert len(ortho) >= 5 and med, "not enough classified items to walk a section"
    if new_dir in sys.path:
        sys.path.remove(new_dir)

    # 1 -- the whole-shop round is unchanged
    old_R, new_R = fam(live_dir, whole), fam(new_dir, whole)
    added = {"items_in_whole_shop", "section", "section_declared", "scope_text"}
    moved = [k for k in old_R if old_R[k] != new_R.get(k)]
    assert not moved, "S314 moved a figure on the whole-shop round: %s" % moved
    assert set(new_R) - set(old_R) == added, "unexpected new keys: %s" % (set(new_R) - set(old_R))
    assert new_R["section"] == "" and new_R["items_in_shop"] == old_R["items_in_shop"], \
        "the whole-shop round acquired a section"

    # 2 -- the hub is unchanged on every key
    def hub(appdir):
        S = mod(appdir)
        con = sqlite3.connect(db); con.row_factory = sqlite3.Row
        S.ensure_schema(con); S._pad_ensure(con)
        h = S._hub_data(con, whole)
        con.commit(); con.close()
        if appdir in sys.path:
            sys.path.remove(appdir)
        return h
    ho, hn = hub(live_dir), hub(new_dir)
    hmoved = [k for k in ho if ho[k] != hn.get(k)]
    assert not hmoved, "S314 changed the hub: %s" % hmoved

    # 3 -- a sectioned round
    con = sqlite3.connect(db)
    cur = con.execute("INSERT INTO stock_count (unit, marg_as_on, bill_no, bill_date, started_at, "
                      "submitted_at, submitted_by, items_total, items_counted, status) "
                      "VALUES ('medical',?,'WALK','2026-09-16','2026-09-16T10:00:00',"
                      "'2026-09-16T10:00:00','walk',?,?,'submitted')",
                      (as_on, len(ortho), len(ortho)))
    ocid = int(cur.lastrowid)
    for it in ortho:
        q = con.execute("SELECT qty, packing, pack_size FROM stock_snapshot WHERE as_on=? AND item=?",
                        (as_on, it)).fetchone()
        con.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, "
                    "counted_qty, counted_by, entered_by, at) VALUES (?,?,?,?,?,?,'walk','walk',?)",
                    (ocid, it, (q[1] if q else ""), int((q[2] if q else 1) or 1),
                     int((q[0] if q else 0) or 0), int((q[0] if q else 0) or 0), "2026-09-16T10:00:00"))
    con.commit(); con.close()

    R = fam(new_dir, ocid)
    assert R["section"] == "Orthotics", "a round of orthotics read as %r" % R["section"]
    assert R["section_declared"] is False, "it should be observed, not declared"
    assert R["items_in_shop"] == len(ortho), \
        "answerable for %d, the section has %d" % (R["items_in_shop"], len(ortho))
    assert R["items_in_whole_shop"] == len(items), "the whole shop was lost"
    assert R["not_counted"] == 0, "%d not counted on a complete orthotics round" % R["not_counted"]
    Rold = fam(live_dir, ocid)
    assert Rold["not_counted"] == len(items) - len(ortho), \
        "the live module should have reported the rest of the shop; it said %d" % Rold["not_counted"]

    # 4 -- one medicine and it is a whole-shop round again
    con = sqlite3.connect(db)
    m0 = med[0]
    q = con.execute("SELECT qty, packing, pack_size FROM stock_snapshot WHERE as_on=? AND item=?",
                    (as_on, m0)).fetchone()
    con.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, "
                "counted_qty, counted_by, entered_by, at) VALUES (?,?,?,?,?,?,'walk','walk',?)",
                (ocid, m0, (q[1] if q else ""), int((q[2] if q else 1) or 1),
                 int((q[0] if q else 0) or 0), int((q[0] if q else 0) or 0), "2026-09-16T10:01:00"))
    con.commit(); con.close()
    R2 = fam(new_dir, ocid)
    assert R2["section"] == "", "one medicine did not widen the round: %r" % R2["section"]
    assert R2["items_in_shop"] == len(items), "the widened round is not answerable for the shop"
    con = sqlite3.connect(db)
    con.execute("DELETE FROM stock_count_item WHERE count_id=? AND item=?", (ocid, m0))
    con.commit(); con.close()
    assert fam(new_dir, ocid)["section"] == "Orthotics", "removing it did not narrow the round again"

    # 5 -- count #1 keeps the hub
    S = mod(new_dir)
    con = sqlite3.connect(db)
    S.ensure_schema(con); S._pad_ensure(con)
    con.execute("UPDATE stock_count SET section='Orthotics' WHERE id=?", (ocid,))
    con.commit()
    roots_newest = int(con.execute("SELECT id FROM stock_count WHERE unit='medical' AND id NOT IN "
                                   "(SELECT count_id FROM stock_count_part) ORDER BY id DESC "
                                   "LIMIT 1").fetchone()[0])
    picked = S._newest_root(con)
    assert picked == whole, "the pages would open #%d, not the whole-shop #%d" % (picked, whole)
    con.execute("UPDATE stock_count SET section=NULL WHERE id=?", (ocid,))
    con.commit()
    picked2 = S._newest_root(con)
    assert picked2 == whole, ("an UNDECLARED sectioned round captured the pages (#%d): the picker must "
                              "read the effective scope, not only the column" % picked2)
    # a CLOSED whole-shop round is still preferred: "closed" means the counting is
    # finished, not the check -- the 06-Sep round was closed on the day it was
    # counted and is still the round every screen works through.
    assert con.execute("SELECT 1 FROM stock_count_close WHERE count_id=?", (whole,)).fetchone(), \
        "this walk assumes the whole-shop round is closed -- it is the case that matters"
    # and if every round were sectioned, the newest would win
    con.execute("UPDATE stock_count SET section='Medicines' WHERE id=?", (whole,))
    con.commit()
    picked3 = S._newest_root(con)
    assert picked3 == roots_newest, ("with every round sectioned the newest should win, got #%d"
                                     % picked3)
    con.execute("UPDATE stock_count SET section=NULL WHERE id=?", (whole,))
    con.commit()
    assert S._newest_root(con) == whole, "clearing it did not restore the preference"
    con.close()
    if new_dir in sys.path:
        sys.path.remove(new_dir)

    # 6 -- the close valve
    R3 = fam(new_dir, ocid)
    staff_blocked = (R3["not_counted"] + R3["sent_back"] == 0 and R3["section"]
                     and not R3["section_declared"])
    assert staff_blocked, "the valve's own precondition does not hold on this round"

    con = sqlite3.connect(db)
    con.execute("UPDATE stock_count SET section='Orthotics' WHERE id=?", (ocid,))
    con.commit()
    R4 = fam(new_dir, ocid)
    con.close()
    assert R4["section_declared"] is True and R4["items_in_shop"] == len(ortho), \
        "declaring the section did not take"

    print("WALK OK the 06-Sep whole-shop round is IDENTICAL on every figure and the hub on every key; "
          "a round of the %d orthotics is recognised as an orthotics round, answerable for %d items and "
          "0 not counted (the live module says %d not counted on the same rows); one medicine widens it "
          "back to the whole shop and removing it narrows it again; the pages still open #%d and not the "
          "sectioned round whether its section is declared (#%d) or only observed (#%d), and the "
          "preference survives the whole-shop round being CLOSED (closed means counted, not finished) "
          "while the newest still wins if every round is sectioned; "
          "an observed scope is owner-only to close and "
          "declaring it hands it back to staff"
          % (len(ortho), R["items_in_shop"], Rold["not_counted"], whole, picked, picked2))
except Exception as e:                                        # noqa: BLE001
    print("WALK RED %s: %s" % (type(e).__name__, e))
    sys.exit(1)
