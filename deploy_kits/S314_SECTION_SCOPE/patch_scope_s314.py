#!/usr/bin/env python
"""S314_SECTION_SCOPE -- rungs 2 and 3 of S268_COUNT2_BY_SECTION_PLAN.

THE ONE THING THIS CHANGES.  Until now "the count" meant THE WHOLE SHOP,
everywhere, and that assumption lived in one function: _pad_family() computed
`uncounted` as every item of the newest Marg snapshot the round did not carry.
So a count of the 69 orthotics reported 304 items not counted, api_pad_close
refused it for staff and stamped it 'incomplete' for the owner -- and that one
function feeds the upload's reply, the result workbook, the recent-counts list,
the desk, Amir's board, the report, the hub and the loss board.  A sectioned
count without this change would look like it worked and would never close.

HOW THE SCOPE IS DECIDED, and why it is derived rather than declared.  The pad
reader has always been right about blanks -- "a blank is an item NOT COUNTED",
never a zero -- so counting only the orthotic rows of the ordinary 373-row pad
already records exactly those items and nothing else.  The round therefore
already SAYS what it covers, in the only way that cannot be wrong: by what was
counted.  So:

    every counted item in the family resolves to ONE section   -> that section
    anything else (or the map is not loaded, or an item is not in it)
                                                               -> the whole shop

and `stock_count.section`, added here, OVERRIDES that when it is set, for the
case where a round must be declared rather than observed.  Nothing writes it
except the owner's own door below.

THE SAFETY VALVE.  An OBSERVED section is an inference, and there is one way it
could mislead: a round MEANT to be the whole shop whose first sheet happens to
carry only orthotics reads as an orthotics round, and could then be closed
'complete' by a staff member with 304 shelves never counted.  So a round whose
section is observed rather than declared can be closed COMPLETE only by the
owner.  A declared round, and a whole-shop round, close exactly as they do today.

AND COUNT #1 KEEPS THE HUB.  The five pages that pick "the current count" took
the newest root, full stop -- so the first sectioned round would have displaced
count #06-Sep, which is still open with real work on it.  _newest_root() now
prefers a whole-shop round, and a sectioned round is reached by ?count=N.

Anchored, idempotent, refuses on drift.  One file.
"""
import argparse
import hashlib
import os
import shutil
import sys

MARK = "S314_SECTION_SCOPE"

# ---------------------------------------------------------------- 1 helpers
HELP_OLD = '''def _pad_ensure(con):
    con.executescript(PAD_SCHEMA)
'''
HELP_NEW = '''def _pad_ensure(con):
    con.executescript(PAD_SCHEMA)
    _section_ensure(con)


# --- S314_SECTION_SCOPE begin (rungs 2 and 3) ----------------------------
def _section_ensure(con):
    """Rung 2: stock_count.section, added HERE and not in stock_schema.sql --
    that file is executed as CREATE TABLE IF NOT EXISTS on every boot, so
    editing it would change nothing on a database that already exists.
    Additive, guarded, and a round that predates it stays NULL, which means
    exactly what it has always meant: the whole shop."""
    try:
        cols = set(r[1] for r in con.execute("PRAGMA table_info(stock_count)"))
        if "section" not in cols:
            con.execute("ALTER TABLE stock_count ADD COLUMN section TEXT")
    except Exception:                                          # pragma: no cover
        pass


def _round_section(con, fam, declared=None):
    """The section this round covers, or "" for the whole shop.

    A DECLARED section (stock_count.section) wins outright.  Otherwise it is
    OBSERVED: if every item counted across the family sits in one section of
    the map, the round covers that section.  One item outside it -- or one item
    the map does not know -- and the round is a whole-shop round again, which is
    the truth rather than a convenience.  Returns (section, declared?)."""
    if declared:
        return str(declared), True
    if not SECTION_MAP_OK:
        return "", False
    try:
        q = ",".join("?" * len(fam))
        rows = [r[0] for r in con.execute(
            "SELECT DISTINCT item FROM stock_count_item WHERE count_id IN (%s)" % q, tuple(fam))]
        if not rows:
            return "", False
        secs = set()
        for it in rows:
            r = con.execute("SELECT section FROM stock_item_section WHERE item_key=?",
                            (_sm.norm_key(it),)).fetchone()
            if not r:
                return "", False                               # an item the map does not know
            secs.add(str(r[0]))
            if len(secs) > 1:
                return "", False
        one = secs.pop() if secs else ""
        # a round that covers every section's worth of one section only is a
        # section round; a round that happens to hold one item is not evidence
        # of anything, so it stays the whole shop until there are at least two.
        return (one, False) if len(rows) >= 2 else ("", False)
    except Exception:                                          # pragma: no cover
        return "", False


def _section_items(con, section, packs):
    """The items of `packs` that belong to `section`. packs is the snapshot, so
    the scope is always a subset of what Marg actually lists today."""
    if not section or not SECTION_MAP_OK:
        return set(packs)
    try:
        want = set()
        for it in packs:
            r = con.execute("SELECT section FROM stock_item_section WHERE item_key=?",
                            (_sm.norm_key(it),)).fetchone()
            if r and str(r[0]) == section:
                want.add(it)
        return want or set(packs)
    except Exception:                                          # pragma: no cover
        return set(packs)


def _newest_root(con):
    """The count the pages open when none is named.

    It PREFERS AN OPEN WHOLE-SHOP ROUND. Before S314 this was the newest root,
    full stop -- so the first sectioned round would have taken the hub, the
    desk, Amir's board, the report and the loss board away from the 06-Sep
    count, which is still open with real work on it.

    The preference reads the EFFECTIVE scope, not just the column: a round that
    covers one section because that is all that was counted must not capture the
    pages either, and the column may well be NULL on it.

    It deliberately does NOT skip a round that has been closed. "Closed" here
    means the COUNTING is finished, not the check: the 06-Sep round was closed
    complete on the day it was counted and is still the round every screen has
    been working through ever since. Preferring an unclosed round would have
    handed the pages to the first sectioned count on the day it was uploaded.

    So: the newest WHOLE-SHOP root, and only if every root is sectioned does the
    newest one win. A sectioned round is opened by ?count=N until there is a
    chooser; a new whole-shop count takes the pages by being the newest of its
    kind, which is what should happen."""
    _section_ensure(con)
    roots = [int(r[0]) for r in con.execute(
        "SELECT id FROM stock_count WHERE unit=? AND id NOT IN "
        "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 12", (_unit,))]
    if not roots:
        return 0
    for rid in roots:
        try:
            fam = [rid] + [x[0] for x in con.execute(
                "SELECT count_id FROM stock_count_part WHERE part_of=?", (rid,))]
            dec = con.execute("SELECT section FROM stock_count WHERE id=?", (rid,)).fetchone()
            sec, _d = _round_section(con, fam, (dec[0] if dec else None) or None)
            if not sec:
                return rid                                     # a whole-shop round
        except Exception:                                      # pragma: no cover
            continue
    return roots[0]                                            # every round is sectioned
# --- S314_SECTION_SCOPE end ----------------------------------------------
'''

# ------------------------------------------------------- 2 _pad_family scope
FAM_OLD = '''    uncounted = [(it, packing[it], packs[it]) for it in sorted(packs, key=str.upper) if it not in items]
'''
FAM_NEW = '''    # S314: what this round is RESPONSIBLE for. `packs` stays the whole snapshot
    # so that a pack size or a packing text is never lost for an item counted
    # outside the scope; only the SCOPE decides what is owed.
    _sec_declared = None
    try:
        _sd = con.execute("SELECT section FROM stock_count WHERE id=?", (root_id,)).fetchone()
        _sec_declared = (_sd[0] if _sd else None) or None
    except Exception:
        _sec_declared = None
    section, section_declared = _round_section(con, fam, _sec_declared)
    scope = _section_items(con, section, packs)
    uncounted = [(it, packing[it], packs[it]) for it in sorted(scope, key=str.upper) if it not in items]
'''

SHOP_OLD = '''             items_in_shop=len(packs), counted=len(items), agreed=len(matched),
'''
SHOP_NEW = '''             items_in_shop=len(scope), items_in_whole_shop=len(packs),
             section=section, section_declared=section_declared,
             scope_text=("the whole shop -- %d items" % len(packs)) if not section
                        else ("%s only -- %d of the shop's %d items%s"
                              % (section, len(scope), len(packs),
                                 "" if section_declared else " (read from what was counted)")),
             counted=len(items), agreed=len(matched),
'''

# ------------------------------------------------- 3 the five current-count picks
PICK_OLD = '''        r = con.execute("SELECT id FROM stock_count WHERE unit=? AND id NOT IN "
                        "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1", (_unit,)).fetchone()
        cid = str(r[0]) if r else "0"
'''
PICK_NEW = '''        cid = str(_newest_root(con) or 0)          # S314: a whole-shop round first
'''

# ------------------------------------------------------------ 4 the close valve
CLOSE_OLD = '''    remaining = R["sent_back"] + R["not_counted"]
    if remaining > 0:
'''
CLOSE_NEW = '''    remaining = R["sent_back"] + R["not_counted"]
    # S314: an OBSERVED section is an inference -- the round covers one section
    # because that is all that was counted, not because anyone said so. The one
    # way that could mislead is a round meant to be the whole shop whose first
    # sheet happened to carry a single section: it would read complete with the
    # rest of the shop never counted. So only the owner closes such a round as
    # complete. A declared round, and a whole-shop round, are untouched.
    if remaining <= 0 and R.get("section") and not R.get("section_declared") and not _may_decide(u):
        return jsonify(ok=False, error="scope_unconfirmed", section=R["section"],
                       message="This round covers %s only (%d items), read from what was counted "
                               "rather than declared. Only the doctor can close a count whose scope "
                               "was not set in advance." % (R["section"], R["items_in_shop"])), 200
    if remaining > 0:
'''

# --------------------------------------------------------- 5 the owner's door
DOOR_OLD = '''@bp.route("/api/pad/preview", methods=["POST"])
'''
DOOR_NEW = '''@bp.route("/api/pad/section/<int:cid>", methods=["POST"])
def api_pad_section(cid):
    """S314. DECLARE what a round covers, or clear it. {section} -- one of the
    map's sections, or empty for the whole shop. The owner's, because it decides
    what a round is answerable for. A declared section overrides what the counted
    items say, and makes the round closeable by staff again."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="Only the doctor sets a round's scope."), 403
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    root_id, fam, R = _pad_family(con, cid)
    if R is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    if R.get("closed"):
        return jsonify(ok=False, error="closed", message="Count #%d is closed." % root_id), 409
    sec = str((request.get_json(silent=True) or {}).get("section") or "").strip()
    if sec and (not SECTION_MAP_OK or sec not in _sm.SECTIONS):
        return jsonify(ok=False, error="bad_request",
                       message="That is not one of the sections."), 400
    con.execute("UPDATE stock_count SET section=? WHERE id=?", (sec or None, root_id))
    con.commit()
    root_id, fam, R = _pad_family(con, root_id)
    return jsonify(ok=True, count_id=root_id, section=R["section"], scope_text=R["scope_text"],
                   items_in_shop=R["items_in_shop"], not_counted=R["not_counted"],
                   message="Count #%d now covers %s." % (root_id, R["scope_text"]))


@bp.route("/api/pad/preview", methods=["POST"])
'''

EDITS = [("the scope helpers", HELP_OLD, HELP_NEW, 1),
         ("_pad_family's scope", FAM_OLD, FAM_NEW, 1),
         ("items_in_shop", SHOP_OLD, SHOP_NEW, 1),
         ("the five current-count picks", PICK_OLD, PICK_NEW, 5),
         ("the close valve", CLOSE_OLD, CLOSE_NEW, 1),
         ("the owner's scope door", DOOR_OLD, DOOR_NEW, 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="frm", default="")
    ap.add_argument("--expect", default="")
    a = ap.parse_args()
    p = a.file
    if not os.path.exists(p):
        print("MISSING %s" % p); return 2
    src = open(p, encoding="utf-8").read()
    cur = hashlib.md5(src.encode("utf-8")).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED -- %s" % cur); return 0
    if a.frm and cur != a.frm:
        print("REFUSED -- live md5 %s, expected %s" % (cur, a.frm)); return 3
    for name, old, new, want in EDITS:
        n = src.count(old)
        if n != want:
            print("REFUSED -- anchor '%s' occurs %d times, expected %d" % (name, n, want)); return 4
        src = src.replace(old, new)
    shutil.copyfile(p, p + ".bak_S314_" + cur[:8])
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    got = hashlib.md5(src.encode("utf-8")).hexdigest()
    if a.expect and got != a.expect:
        print("REFUSED AFTER WRITE -- got %s, expected %s" % (got, a.expect)); return 5
    print("PATCHED %s -> %s" % (cur, got))
    return 0


if __name__ == "__main__":
    sys.exit(main())
