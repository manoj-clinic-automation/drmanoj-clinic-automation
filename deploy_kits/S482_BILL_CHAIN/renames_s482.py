#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""renames_s482.py -- kit S482_BILL_CHAIN, Part B (D676): the rename list carries the right names.

D676 (the owner, 05-Oct-2026): a Marg item is renamed only where the system cannot tell it apart (its first 20 letters), and the words
staff type to search never change. Seven rows of finance.db `marg_item_rename` hold S268's spellings (LS BELT ..., ... TRACT L BELT);
they get the spellings of S295_ORTHOTIC_RENAMES_CHECKED. This is the kit's ONE data write besides the new table.

  apply(con)   one UPDATE per row, keyed by id AND old_name. Every key is checked first: a key that does not match stops the whole
               write (the table is not the one the brief read). A row Amir has already ticked or Marg has already shown (done_by,
               done_at, verified_* not NULL) is STOPPED and reported -- he did it under the old name -- and the other rows go on.
               After the write: no two rows share new20, no new_name is longer than 29, and every row but the updated ones is
               unchanged, cell for cell -- else everything is rolled back. The caller commits.

  python3 -B renames_s482.py DB [--dry]     (the installer's call; --dry rolls back and only reports)

item_alias.py is not edited: its seed() keeps existing rows by old_name, so the UPDATE stands; its hard-coded list is corrected in S483.
"""
import sqlite3
import sys

KIT = "S482_BILL_CHAIN"
NOTE = " · S482/D676: spelling per S295_ORTHOTIC_RENAMES_CHECKED (the search words kept)"
SALE_CLIP, PURCHASE_CLIP, MASTER_CLIP = 20, 27, 29          # item_alias.py's own widths
ROWS = (
    (5, "L S BELT CONT GRAY UNISON L", "L S BELT L CONT GRAY UNISON"),
    (6, "L S BELT CONT GRAY UNISON M", "L S BELT M CONT GRAY UNISON"),
    (7, "L S BELT CONT GRAY UNISON XL", "L S BELT XL CONT GRAY UNISON"),
    (8, "L S BELT CONT GRAY UNISON XXL", "L S BELT XXL CONT GRAY UNISON"),
    (9, "L S BELT CONT GRAY UNISON XXX", "L S BELT 3XL CONT GRAY UNISON"),
    (21, "BLING PELVIC TRACTION BELT L", "BLING PELVIC L TRACTION BELT"),
    (22, "BLING PELVIC TRACTION BELT XL", "BLING PELVIC XL TRACTION BELT"),
)
DONE_COLS = ("done_by", "done_at", "verified_at", "verified_md5", "verified_as_on")


class Stop(Exception):
    """Nothing was written."""


def clip(name, width):
    """item_alias.clip(), verbatim -- what Marg prints of a name in a report of that width (a right-stripped cut)."""
    return str(name or "")[:width].rstrip()


def table(con):
    """{id: the whole row as a tuple} -- for the before / after comparison."""
    cur = con.execute("SELECT * FROM marg_item_rename ORDER BY id")
    return {r[0]: tuple(r) for r in cur.fetchall()}


def apply(con, rows=ROWS):
    """-> dict(updated=[ids], already=[ids], stopped=[(id, why)], before={id: (new_name, new20, new27)}, after={...}, n_rows).
    Raises Stop (after a rollback) when a key does not match or a check after the write fails."""
    before = table(con)
    cols = [c[1] for c in con.execute("PRAGMA table_info(marg_item_rename)")]
    ix = {c: i for i, c in enumerate(cols)}
    bad = [(i, old) for i, old, _new in rows if i not in before or before[i][ix["old_name"]] != old]
    if bad:
        raise Stop("no row with this id AND old_name: %s -- the table is not the one the brief read; nothing written" % bad)
    out = dict(updated=[], already=[], stopped=[], before={}, after={}, n_rows=len(before))
    try:
        for i, old, new in rows:
            r = before[i]
            out["before"][i] = (r[ix["new_name"]], r[ix["new20"]], r[ix["new27"]])
            if r[ix["new_name"]] == new:
                out["already"].append(i)
                continue
            if any(r[ix[c]] is not None for c in DONE_COLS):
                out["stopped"].append((i, "already ticked or seen under the old spelling (%s)"
                                       % ", ".join(c for c in DONE_COLS if r[ix[c]] is not None)))
                continue
            n = con.execute("UPDATE marg_item_rename SET new_name = ?, new20 = ?, new27 = ?, note = COALESCE(note, '') || ? "
                            "WHERE id = ? AND old_name = ?",
                            (new, clip(new, SALE_CLIP), clip(new, PURCHASE_CLIP), NOTE, i, old)).rowcount
            if n != 1:
                raise Stop("row %d: the keyed UPDATE touched %d rows, not one" % (i, n))
            out["updated"].append(i)
        after = table(con)
        for i in out["updated"] + out["already"]:
            out["after"][i] = (after[i][ix["new_name"]], after[i][ix["new20"]], after[i][ix["new27"]])
        touched = set(out["updated"])
        moved = [i for i in before if i not in touched and before[i] != after.get(i)]
        if moved or set(after) != set(before):
            raise Stop("rows other than the updated ones changed: %s" % moved)
        for i in touched:                                   # of an updated row only new_name, new20, new27 and note may differ
            diff = [c for c in cols if before[i][ix[c]] != after[i][ix[c]]]
            if set(diff) - {"new_name", "new20", "new27", "note"}:
                raise Stop("row %d: columns %s moved" % (i, diff))
        n20 = [r[ix["new20"]] for r in after.values()]
        dup = sorted({x for x in n20 if n20.count(x) > 1})
        if dup:
            raise Stop("two rows would share a 20-letter name: %s" % dup)
        longn = [r[ix["new_name"]] for r in after.values() if len(r[ix["new_name"]] or "") > MASTER_CLIP]
        if longn:
            raise Stop("a new name is longer than %d: %s" % (MASTER_CLIP, longn))
    except Exception:
        con.rollback()
        raise
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    dry = "--dry" in argv[2:]
    con = sqlite3.connect(argv[1], timeout=60)
    con.execute("PRAGMA busy_timeout=60000")
    try:
        r = apply(con)
    except Stop as e:
        print("RENAMES_S482 STOPPED -- %s" % e)
        return 1
    for i, _old, _new in ROWS:
        if i in r["updated"] or i in r["already"]:
            print("   row %2d  %-29s -> %-29s  new20 %-20s  %s" % (i, r["before"][i][0], r["after"][i][0], r["after"][i][1],
                                                                  "updated" if i in r["updated"] else "already so"))
    for i, why in r["stopped"]:
        print("   row %2d  STOPPED -- %s" % (i, why))
    if dry:
        con.rollback()
    else:
        con.commit()
    con.close()
    print("RENAMES_S482 %s -- %d updated, %d already so, %d stopped; %d rows in the table, the others unchanged cell for cell%s"
          % ("OK" if not r["stopped"] else "PART", len(r["updated"]), len(r["already"]), len(r["stopped"]), r["n_rows"],
             " (DRY: rolled back)" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
