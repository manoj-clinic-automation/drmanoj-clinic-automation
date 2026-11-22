#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s932.py -- kit S932_ORTHO_ORDER_NAMES (F-1579) on a MADE-UP store: a scratch database with the live file's schema (no rows), one
ticked rename (W932 BINDER M -> W932 BINDER BAMBOO M), Darpan's yes rows, orders of the orthotic vendor. Checks: the order line carries
Marg's CURRENT name; an order under the new name clears the kept row; an edit under either name applies; porders' on-order folds the new
name back to the lane's key; a name with no rename is untouched. --control runs the SAME checks on the OLD files and must go red.
    python3 -B walk_s932.py <dir with the files> <COPY of finance.db> [--control]
No patient data: the copy lends its schema only. Nothing printed but the made-up names and counts."""
import os
import re
import shutil
import sqlite3
import sys
import tempfile

FAILS = []


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def check(label, cond, got=None):
    if cond:
        say("ok   " + label)
    else:
        FAILS.append(label)
        say("FAIL " + label + ("  [%s]" % (str(got)[:300],) if got is not None else ""))


def schema_only(copy, dbp):
    src = sqlite3.connect(copy)
    dst = sqlite3.connect(dbp)
    for (sql,) in src.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND type IN ('table','index') AND name NOT LIKE 'sqlite_%' ORDER BY type DESC"):
        try:
            dst.execute(sql)
        except sqlite3.Error:
            pass
    dst.commit()
    src.close()
    return dst


def main():
    fin, copy = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    control = "--control" in sys.argv
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
    sys.path.insert(0, fin)
    scratch = tempfile.mkdtemp(prefix="s932_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        run(fin, copy, control, scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    say("INFO %d checks, %d fail" % (N[0], len(FAILS)))
    say("RESULT: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    sys.exit(0 if not FAILS else 1)


N = [0]
_check = check


def check(label, cond, got=None):                             # noqa: F811
    N[0] += 1
    _check(label, cond, got)


def run(fin, copy, control, scratch):
    dbp = os.path.join(scratch, "fin.db")
    con = schema_only(copy, dbp)
    con.row_factory = sqlite3.Row
    import order_sheet as OS                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    import item_alias as IA                                   # noqa: E402
    check("files from the given dir", all(m.__file__.startswith(fin) for m in (OS, PO, IA)), [m.__file__ for m in (OS, PO, IA)])
    OS.ensure(con)
    IA.ensure(con)
    PO.ensure(con) if hasattr(PO, "ensure") else None
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('porders.ortho_vendor', 'W932 SURGICALS')")
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('order.source', 'system')")
    old, new = "W932 BINDER M", "W932 BINDER BAMBOO M"
    con.execute("INSERT INTO marg_item_rename (old_name, new_name, old20, old27, new20, new27, planned_by, planned_at, done_by, done_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'owner', '2026-11-01T10:00:00', 'amir', '2026-11-02T10:00:00')", (old, new, old[:20], old[:27], new[:20], new[:27]))
    con.execute("INSERT INTO marg_item_rename (old_name, new_name, old20, old27, new20, new27, planned_by, planned_at) "
                "VALUES ('W932 PLANNED L', 'W932 PLANNED BAMBOO L', 'W932 PLANNED L', 'W932 PLANNED L', 'W932 PLANNED BAMBOO L', 'W932 PLANNED BAMBOO L', 'owner', '2026-11-01T10:00:00')")
    con.commit()
    sn = PO._pa().supplier_key("W932 SURGICALS") if hasattr(PO, "_pa") else OS._pa().supplier_key("W932 SURGICALS")
    has_fn = hasattr(OS, "_s932_marg_name")
    # T1 the name doors
    check("T1 a ticked rename gives Marg's current name; a planned (unticked) one and a plain name give the name itself",
          has_fn and OS._s932_marg_name(con, old) == new and OS._s932_marg_name(con, "W932 PLANNED L") == "W932 PLANNED L" and OS._s932_marg_name(con, "W932 PLAIN S") == "W932 PLAIN S",
          "no _s932_marg_name" if not has_fn else None)
    check("T2 the forms of the count's name carry the new name too", has_fn and old in OS._s932_forms(con, old) and new in OS._s932_forms(con, old))
    # Darpan's yes rows: the renamed item, a plain item
    con.execute("INSERT INTO ortho_yes (tap, at, by, answer, item, qty, short_at_answer) VALUES (1, '2026-11-10T19:00:00', 'darpan', 'yes', ?, 3, 3)", (old,))
    con.execute("INSERT INTO ortho_yes (tap, at, by, answer, item, qty, short_at_answer) VALUES (1, '2026-11-10T19:00:00', 'darpan', 'yes', 'W932 PLAIN S', 2, 2)")
    con.commit()
    v, kept = OS.ortho_kept(con)
    check("T3 both yes rows kept (no order yet)", v == "W932 SURGICALS" and sorted(a["item"] for a in kept) == [old, "W932 PLAIN S"], (v, [a["item"] for a in kept]))
    cards = OS.entries(con, t="2026-11-22")
    oc = [c for c in cards if c["sn"] == sn]
    items = {l["item"]: l for l in (oc[0]["lines"] if oc else [])}
    check("T4 the card line of the renamed item carries Marg's CURRENT name (W932 BINDER BAMBOO M), qty 3 from the yes row",
          new in items and items[new]["qty"] == 3 and old not in items, sorted(items))
    check("T5 the plain item's line is untouched (W932 PLAIN S, qty 2)", "W932 PLAIN S" in items and items["W932 PLAIN S"]["qty"] == 2, sorted(items))
    ref = "ortho:%d" % [a for a in kept if a["item"] == old][0]["id"] if kept else "ortho:0"
    # an edit saved under the NEW name (as the page now prints it) applies; one under the old name applies too
    con.execute("INSERT OR REPLACE INTO s454_line_edit (src, ref, item, qty, removed, by, at) VALUES ('ortho', ?, ?, 5, 0, 'shavez', '2026-11-22T10:00:00')", (ref, new))
    con.commit()
    items = {l["item"]: l for l in [l for c in OS.entries(con, t="2026-11-22") if c["sn"] == sn for l in c["lines"]]}
    check("T6 reception's quantity edit saved under the new name applies (5)", new in items and items[new]["qty"] == 5, {k: v["qty"] for k, v in items.items()})
    con.execute("DELETE FROM s454_line_edit WHERE ref=?", (ref,))
    con.execute("INSERT OR REPLACE INTO s454_line_edit (src, ref, item, qty, removed, by, at) VALUES ('ortho', ?, ?, 4, 0, 'shavez', '2026-11-22T10:00:00')", (ref, old))
    con.commit()
    items = {l["item"]: l for l in [l for c in OS.entries(con, t="2026-11-22") if c["sn"] == sn for l in c["lines"]]}
    check("T6b an older edit saved under the old name applies too (4)", new in items and items[new]["qty"] == 4, {k: v["qty"] for k, v in items.items()})
    con.execute("DELETE FROM s454_line_edit WHERE ref=?", (ref,))
    # the order goes out under the NEW name: the kept row is cleared (no third order)
    con.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, supplier_norm, order_src) VALUES ('2026-11-11T10:00:00', 'shavez', 'W932 SURGICALS', 'sent', ?, 's454')", (sn,))
    oid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?, ?, 3, 1, 3)", (oid, new))
    con.commit()
    v, kept = OS.ortho_kept(con)
    check("T7 an order carrying the NEW name since the yes clears the kept row (the plain item stays)", [a["item"] for a in kept] == ["W932 PLAIN S"], [a["item"] for a in kept])
    check("T7b _s605_ordered_since finds the order under either name", OS._s605_ordered_since(con, sn, old, "2026-11-10T19:00:00") and OS._s605_ordered_since(con, sn, new, "2026-11-10T19:00:00"))
    check("T7c ... and not before the yes, nor another item", not OS._s605_ordered_since(con, sn, old, "2026-11-12T00:00:00") and not OS._s605_ordered_since(con, sn, "W932 PLAIN S", "2026-11-10T19:00:00"))
    # porders' on-order picture: the line under the new name counts for the lane's own key (the old name)
    oo = PO._on_order(con, "W932 SURGICALS")
    check("T8 porders._on_order folds the line under the new name back to the count's key: {W932 BINDER M: 3}", oo.get(old) == 3 and new not in oo, oo)
    con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?, 'W932 PLAIN S', 2, 1, 2)", (oid,))
    con.commit()
    oo = PO._on_order(con, "W932 SURGICALS")
    check("T8b a plain line is counted as before", oo.get("W932 PLAIN S") == 2 and oo.get(old) == 3, oo)
    # the review's MUST: a never-renamed SIBLING whose 20-letter clip equals the renamed item's new name's clip keeps its OWN key
    sib = "W932 BINDER BAMBOO L"                              # clips to 'W932 BINDER BAMBOO' at 20 -- as the renamed M does
    con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?, ?, 4, 1, 4)", (oid, sib))
    con.commit()
    oo = PO._on_order(con, "W932 SURGICALS")
    check("T8c a plain sibling sharing the 20-letter clip (W932 BINDER BAMBOO L) keeps its own key: L 4, the renamed M still 3", oo.get(sib) == 4 and oo.get(old) == 3, oo)
    # a chain X->Y, Y->Z ticked: a line under Y folds nowhere (Y is a key of its own)
    con.execute("INSERT INTO marg_item_rename (old_name, new_name, old20, old27, new20, new27, planned_by, planned_at, done_by, done_at) "
                "VALUES ('W932 CHAIN X', 'W932 CHAIN Y', 'W932 CHAIN X', 'W932 CHAIN X', 'W932 CHAIN Y', 'W932 CHAIN Y', 'owner', '2026-11-01T10:00:00', 'amir', '2026-11-02T10:00:00')")
    con.execute("INSERT INTO marg_item_rename (old_name, new_name, old20, old27, new20, new27, planned_by, planned_at, done_by, done_at) "
                "VALUES ('W932 CHAIN Y', 'W932 CHAIN Z', 'W932 CHAIN Y', 'W932 CHAIN Y', 'W932 CHAIN Z', 'W932 CHAIN Z', 'owner', '2026-11-01T10:00:00', 'amir', '2026-11-02T10:00:00')")
    con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?, 'W932 CHAIN Y', 1, 1, 1)", (oid,))
    con.commit()
    oo = PO._on_order(con, "W932 SURGICALS")
    check("T8d a chain's middle name (X->Y, Y->Z) folds nothing: the line under Y stays under Y", oo.get("W932 CHAIN Y") == 1 and "W932 CHAIN X" not in oo, oo)
    check("T8e _s932_marg_name: X -> nothing (its new name is a key of its own), Y -> Z; a spacing difference still maps ('W932  BINDER M' -> the new name)",
          has_fn and OS._s932_marg_name(con, "W932 CHAIN X") == "W932 CHAIN X" and OS._s932_marg_name(con, "W932 CHAIN Y") == "W932 CHAIN Z" and OS._s932_marg_name(con, "W932  BINDER M") == new,
          None if not has_fn else (OS._s932_marg_name(con, "W932 CHAIN X"), OS._s932_marg_name(con, "W932 CHAIN Y"), OS._s932_marg_name(con, "W932  BINDER M")))
    check("T8f the forms are the two exact names only (no clip)", has_fn and OS._s932_forms(con, old) == [old, new])
    # an item on BOTH the sheet card and the kept rows is shown once -- under either spelling
    L9 = [(l["item"], l["src"]) for c in OS.entries(con, t="2026-11-22") if c["sn"] == sn for l in c["lines"]]
    check("T9 with both items on the sent order, no kept line is offered again (the card is empty)", L9 == [], L9)
    con.close()


if __name__ == "__main__":
    main()
