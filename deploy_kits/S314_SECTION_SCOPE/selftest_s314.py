#!/usr/bin/env python
"""S314_SECTION_SCOPE selftest -- the scope logic alone, over small synthetic
databases, with negative controls.

It tests the ways a wrong scope would be wrong QUIETLY: a round declared to
cover one section while it holds another; a round scoped from a single item; a
round holding an item the map has never heard of; and a picker that hands the
owner's live whole-shop count to the first sectioned round that arrives.

    python3 -B selftest_s314.py <dir holding the patched stock_app.py>
"""
import os
import sqlite3
import sys

APP = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP)
import stock_app as S                                          # noqa: E402
import section_map as sm                                       # noqa: E402

S._unit = "medical"
OK = FAIL = 0


def chk(c, what):
    global OK, FAIL
    if c:
        OK += 1
    else:
        FAIL += 1
        print("  FAIL: %s" % what)


def db(items=(("A BELT", "Orthotics"), ("B TAB", "Medicines"), ("C GLOVE", "Consumables"))):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE stock_count (id INTEGER PRIMARY KEY AUTOINCREMENT, unit TEXT, "
                "marg_as_on TEXT, status TEXT)")
    con.execute("CREATE TABLE stock_count_item (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "count_id INTEGER, item TEXT)")
    con.execute("CREATE TABLE stock_count_part (count_id INTEGER PRIMARY KEY, part_of INTEGER)")
    con.execute("CREATE TABLE stock_count_close (count_id INTEGER PRIMARY KEY)")
    sm.ensure(con)
    for it, sec in items:
        con.execute("INSERT INTO stock_item_section (item_key, item, section, source, seeded_as, "
                    "by_user, at) VALUES (?,?,?,'seed',?, 'test','2026-09-18T00:00:00')",
                    (sm.norm_key(it), it, sec, sec))
    S._section_ensure(con)
    return con


def mkround(con, items, section=None):
    cur = con.execute("INSERT INTO stock_count (unit, marg_as_on, status) "
                      "VALUES ('medical','16-09-2026','submitted')")
    cid = int(cur.lastrowid)
    for it in items:
        con.execute("INSERT INTO stock_count_item (count_id, item) VALUES (?,?)", (cid, it))
    if section is not None:
        con.execute("UPDATE stock_count SET section=? WHERE id=?", (section, cid))
    return cid


def main():
    # ---- 1 the column ---------------------------------------------------
    con = db()
    cols = set(r[1] for r in con.execute("PRAGMA table_info(stock_count)"))
    chk("section" in cols, "the section column is added")
    S._section_ensure(con); S._section_ensure(con)
    chk(len([r for r in con.execute("PRAGMA table_info(stock_count)") if r[1] == "section"]) == 1,
        "adding it twice leaves one column")
    cid = mkround(con, ["A BELT"])
    S._section_ensure(con)
    chk(con.execute("SELECT COUNT(*) FROM stock_count").fetchone()[0] == 1, "no row is lost")

    # ---- 2 the observed scope -------------------------------------------
    con = db()
    c1 = mkround(con, ["A BELT", "A BELT 2"])
    con.execute("INSERT INTO stock_item_section (item_key, item, section, source, by_user, at) "
                "VALUES (?,?,'Orthotics','seed','t','x')", (sm.norm_key("A BELT 2"), "A BELT 2"))
    chk(S._round_section(con, [c1]) == ("Orthotics", False), "two orthotics read as an orthotics round")
    c2 = mkround(con, ["A BELT", "B TAB"])
    chk(S._round_section(con, [c2]) == ("", False),
        "NEGATIVE: two sections is the whole shop, not a guess at the bigger one")
    c3 = mkround(con, ["A BELT"])
    chk(S._round_section(con, [c3]) == ("", False),
        "NEGATIVE: ONE item is not evidence of a section -- the whole shop")
    c4 = mkround(con, ["A BELT", "Z UNKNOWN"])
    chk(S._round_section(con, [c4]) == ("", False),
        "NEGATIVE: an item the map does not know makes it the whole shop")
    c5 = mkround(con, [])
    chk(S._round_section(con, [c5]) == ("", False), "an empty round is the whole shop")

    # ---- 3 declared beats observed --------------------------------------
    con = db()
    c = mkround(con, ["A BELT", "B TAB"], section="Orthotics")
    chk(S._round_section(con, [c], "Orthotics") == ("Orthotics", True),
        "a DECLARED section wins even when the items disagree")
    chk(S._round_section(con, [c], None) == ("", False),
        "and with the declaration cleared it is the whole shop again")
    chk(S._round_section(con, [c], "") == ("", False), "an empty declaration is not a declaration")

    # ---- 4 the family, not just the root --------------------------------
    con = db()
    root = mkround(con, ["A BELT", "A BELT 2"])
    con.execute("INSERT INTO stock_item_section (item_key, item, section, source, by_user, at) "
                "VALUES (?,?,'Orthotics','seed','t','x')", (sm.norm_key("A BELT 2"), "A BELT 2"))
    part = mkround(con, ["B TAB"])
    con.execute("INSERT INTO stock_count_part (count_id, part_of) VALUES (?,?)", (part, root))
    chk(S._round_section(con, [root]) == ("Orthotics", False), "the root alone is orthotics")
    chk(S._round_section(con, [root, part]) == ("", False),
        "NEGATIVE: a PART that adds a medicine widens the whole family -- the scope is the family's")

    # ---- 5 the scope's items --------------------------------------------
    con = db()
    packs = {"A BELT": 1, "B TAB": 10, "C GLOVE": 1}
    chk(S._section_items(con, "Orthotics", packs) == {"A BELT"}, "the section's items only")
    chk(S._section_items(con, "", packs) == set(packs), "no section is the whole snapshot")
    chk(S._section_items(con, "Nothing", packs) == set(packs),
        "a section with no items falls back to the whole shop rather than returning nothing")

    # ---- 6 the picker ----------------------------------------------------
    con = db()
    whole = mkround(con, ["A BELT", "B TAB"])
    chk(S._newest_root(con) == whole, "one whole-shop round is picked")
    ortho = mkround(con, ["A BELT", "A BELT 2"])
    con.execute("INSERT INTO stock_item_section (item_key, item, section, source, by_user, at) "
                "VALUES (?,?,'Orthotics','seed','t','x')", (sm.norm_key("A BELT 2"), "A BELT 2"))
    chk(S._newest_root(con) == whole,
        "NEGATIVE: a NEWER sectioned round does NOT capture the pages, though it is the newest root")
    con.execute("INSERT INTO stock_count_close (count_id) VALUES (?)", (whole,))
    chk(S._newest_root(con) == whole,
        "NEGATIVE: nor when the whole-shop round is CLOSED -- closed means counted, not finished")
    con.execute("UPDATE stock_count SET section='Medicines' WHERE id=?", (whole,))
    chk(S._newest_root(con) == ortho, "with every round sectioned, the newest wins")
    con.execute("UPDATE stock_count SET section=NULL WHERE id=?", (whole,))
    chk(S._newest_root(con) == whole, "and clearing it restores the preference")
    con2 = db()
    chk(S._newest_root(con2) == 0, "no round at all is 0, not an error")

    print("SELFTEST %d checks, %d failed" % (OK + FAIL, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
