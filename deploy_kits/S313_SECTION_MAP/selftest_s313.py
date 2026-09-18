#!/usr/bin/env python
"""S313_SECTION_MAP selftest -- section_map.py alone, in memory, with negative
controls.  It tests the things a wrong section map would get wrong quietly: a
re-seed overwriting the owner's word, a rename making a second row, a section
that is not one of the three, and the dispute detector calling an agreed item
disputed (or, worse, missing a real disagreement)."""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import section_map as sm                                            # noqa: E402

OK = FAIL = 0


def chk(c, what):
    global OK, FAIL
    if c:
        OK += 1
    else:
        FAIL += 1
        print("  FAIL: %s" % what)


def db():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.execute("CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER)")
    sm.ensure(con)
    return con


def main():
    # ---- 1 the seed rule, on the real shapes ----------------------------
    chk(sm.classify("GLOVES SURGICAL 7") == "Consumables", "a glove is a consumable")
    chk(sm.classify("ANKLE BINDER BAMBOO L") == "Orthotics", "an ankle binder is an orthotic")
    chk(sm.classify("TYRO BR TAB") == "Medicines", "a tablet is a medicine")
    chk(sm.classify("CREPE BANDAGE 10CM") == "Consumables",
        "consumable wins over orthotic when both words are present (the voucher's own order)")
    chk(sm.classify("") == "Medicines", "an empty name still gets a section, never a blank")

    # ---- 2 the four rules, and the measured disagreements ---------------
    chk(sm.is_ortho_priced('PRIME PAD 4"') and not sm.is_orthotic('PRIME PAD 4"')
        and not sm.is_consumable('PRIME PAD 4"'),
        'PRIME PAD 4" is ortho for pricing and in NO section list -- the F-528 case')
    chk(sm.is_orthotic("SKIN TRACTION HOPE") and not sm.is_ortho_priced("SKIN TRACTION HOPE"),
        "SKIN TRACTION HOPE is an orthotic the pricing list does not call ortho")
    chk(sm.is_consumable("TAPEASE NS SPRAY") and not sm.is_ortho_priced("TAPEASE NS SPRAY"),
        "TAPEASE NS SPRAY is a consumable the pricing list does not call ortho")

    # ---- 3 seeding ------------------------------------------------------
    con = db()
    items = ["ANKLE BINDER BAMBOO L", "GLOVES SURGICAL 7", "TYRO BR TAB", 'PRIME PAD 4"']
    a, k = sm.seed(con, items)
    chk((a, k) == (4, 0), "the first seed writes every item")
    a, k = sm.seed(con, items)
    chk((a, k) == (0, 4), "a second seed writes nothing (insert-only)")
    chk(con.execute("SELECT COUNT(*) FROM stock_item_section").fetchone()[0] == 4, "four rows, not eight")
    chk(sm.summary(con)["by_section"]["Orthotics"] == 1, "one orthotic")
    chk(sm.summary(con)["by_section"]["Medicines"] == 2,
        'PRIME PAD 4" seeds as a MEDICINE -- no section list claims it, and the seed must not invent one')

    # ---- 4 the owner's word is never overwritten ------------------------
    ok, _m = sm.set_section(con, 'PRIME PAD 4"', "Orthotics", "manoj")
    chk(ok, "the owner moves it")
    row = con.execute("SELECT section, source, seeded_as FROM stock_item_section WHERE item_key=?",
                      (sm.norm_key('PRIME PAD 4"'),)).fetchone()
    chk(tuple(row) == ("Orthotics", "owner", "Medicines"),
        "his word is stored, marked his, and what the seed said is KEPT beside it")
    sm.seed(con, items)
    row = con.execute("SELECT section, source FROM stock_item_section WHERE item_key=?",
                      (sm.norm_key('PRIME PAD 4"'),)).fetchone()
    chk(tuple(row) == ("Orthotics", "owner"),
        "NEGATIVE: a re-seed does NOT overwrite the owner's word")
    ok, _m = sm.set_section(con, 'PRIME PAD 4"', "Furniture", "manoj")
    chk(not ok, "NEGATIVE: a section that is not one of the three is refused")
    chk(con.execute("SELECT section FROM stock_item_section WHERE item_key=?",
                    (sm.norm_key('PRIME PAD 4"'),)).fetchone()[0] == "Orthotics",
        "and the refusal changed nothing")

    # ---- 5 one item is one row, however Marg spells it ------------------
    con2 = db()
    sm.seed(con2, ["ANKLE  BINDER   BAMBOO L"])
    sm.seed(con2, ["ankle binder bamboo l"])
    sm.seed(con2, ["ANKLE-BINDER BAMBOO  L"])
    chk(con2.execute("SELECT COUNT(*) FROM stock_item_section").fetchone()[0] == 1,
        "spacing, case and punctuation do not make a second row (norm_key)")

    # ---- 6 the dispute detector ----------------------------------------
    con3 = db()
    sm.seed(con3, ["TYRO BR TAB", 'PRIME PAD 4"', "SKIN TRACTION HOPE", "ANKLE BINDER BAMBOO L"])
    d = {r["item"]: r for r in sm.rows(con3)}
    chk(d['PRIME PAD 4"']["disputed"] is True, 'PRIME PAD 4" is flagged disputed')
    chk(d["SKIN TRACTION HOPE"]["disputed"] is True, "SKIN TRACTION HOPE is flagged disputed")
    chk(d["TYRO BR TAB"]["disputed"] is False,
        "NEGATIVE: a plain medicine no rule claims is NOT flagged -- the page would be useless otherwise")
    chk(d["ANKLE BINDER BAMBOO L"]["disputed"] is False,
        "NEGATIVE: an item every rule agrees on is NOT flagged")
    chk(sm.rows(con3, only_disputed=True) and
        all(r["disputed"] for r in sm.rows(con3, only_disputed=True)),
        "only_disputed returns disputed rows and nothing else")
    chk(sm.rows(con3)[0]["disputed"] is True, "disputed rows sort to the top")

    # ---- 7 the counter's vocabulary is shown, never obeyed --------------
    con4 = db()
    con4.execute("INSERT INTO setting (key, value) VALUES ('orthotics.vocab','CREPE, WRIST')")
    sm.seed(con4, ["CREPE BANDAGE 10CM", "TYRO BR TAB"])
    d = {r["item"]: r for r in sm.rows(con4)}
    chk(d["CREPE BANDAGE 10CM"]["section"] == "Consumables",
        "NEGATIVE: the counter's vocabulary does NOT move the seeded section")
    chk(d["CREPE BANDAGE 10CM"]["counter_vocab"] is True, "but the page is told the counter claims it")
    chk(d["CREPE BANDAGE 10CM"]["disputed"] is False,
        "CREPE is ortho-priced AND on the counter's list, so the two agree -- not a dispute")
    chk(d["TYRO BR TAB"]["counter_vocab"] is False, "and that a tablet is not on it")

    # ---- 8 extra consumable words from the setting ----------------------
    con5 = db()
    con5.execute("INSERT INTO setting (key, value) VALUES ('stock.consumable_words','WIDGET')")
    chk(sm.extra_consumable_words(con5) == ("WIDGET",), "the setting is read")
    chk(sm.classify("WIDGET BRACE L", sm.extra_consumable_words(con5)) == "Consumables",
        "a word from the setting makes it a consumable even though BRACE is an orthotic word")
    chk(sm.classify("WIDGET BRACE L") == "Orthotics",
        "NEGATIVE: and without the setting the same item is an orthotic")

    # ---- 9 items_in, the whole point of the table -----------------------
    con6 = db()
    sm.seed(con6, ["ANKLE BINDER BAMBOO L", "GLOVES SURGICAL 7", "TYRO BR TAB"])
    chk(sm.items_in(con6, "Orthotics") == ["ANKLE BINDER BAMBOO L"], "the section's list is exact")
    chk(sm.items_in(con6, "Nothing") == [], "an unknown section is empty, not an error")

    # ---- 10 the snapshot reader picks the NEWEST date -------------------
    con7 = db()
    for a, i in (("06-09-2026", "OLD ONE"), ("16-09-2026", "NEW ONE"), ("31-08-2026", "OLDER")):
        con7.execute("INSERT INTO stock_snapshot (as_on, item, qty) VALUES (?,?,1)", (a, i))
    as_on, items = sm.snapshot_items(con7)
    chk(as_on == "16-09-2026" and items == ["NEW ONE"],
        "the newest snapshot is chosen by its dd-mm-yyyy key, not by string order")

    print("SELFTEST %d checks, %d failed" % (OK + FAIL, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
