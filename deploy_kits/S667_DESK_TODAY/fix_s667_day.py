#!/usr/bin/env python3
"""fix_s667_day.py -- kit S667_DESK_TODAY's data step (the parent, S358, 27-Oct-2026). Moves the two parchis the stale desk
filed under 26-Oct this morning onto 27-Oct, the day they were written: OPD 19858 and X-ray 1420, typed 27-Oct 11:26.
Only a row that is EXACTLY that (series, number, day 2026-10-26, state ok, typed 2026-10-27 11:26) moves; anything else is
left and named. One audit_log row each. With --lib <dir holding slip_log.py> the 'new patient' mark is worked out again for
27-Oct (it was worked out for 26-Oct). Any OTHER parchi typed 27-Oct but filed on an earlier day is listed, never moved.
Safe to run twice. Exit 0 = every row is on 27-Oct (moved now or before); 2 = a row was not as expected (left); 1 = error.
  python3 fix_s667_day.py <finance.db> [--dry] [--lib <dir>]"""
import datetime as dt
import json
import sqlite3
import sys

ROWS = (("opd", 19858), ("xp", 1420))
OLD_DAY, NEW_DAY, TYPED = "2026-10-26", "2026-10-27", "2026-10-27 11:26"


def main(path, dry=False, lib=""):
    SL = None
    if lib:
        sys.path.insert(0, lib)
        try:
            import slip_log as SL                                       # noqa: N813
        except Exception as e:                                          # noqa: BLE001
            print("slip_log not loaded (%s) -- the new-patient mark is left as it is" % type(e).__name__)
            SL = None
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("BEGIN IMMEDIATE")
    moved, bad, said = 0, 0, []
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for series, no in ROWS:
        r = con.execute("SELECT * FROM slip WHERE series=? AND slip_no=? AND state='ok'", (series, no)).fetchone()
        if r is None:
            said.append("%s %d: not found as a saved parchi -- left" % (series, no)); bad += 1
            continue
        if r["day"] == NEW_DAY:
            said.append("%s %d: already on %s" % (series, no, NEW_DAY))
            continue
        if r["day"] != OLD_DAY or not str(r["logged_at"] or "").startswith(TYPED):
            said.append("%s %d: day %s typed %s -- not the row this step was written for; left" % (series, no, r["day"], r["logged_at"])); bad += 1
            continue
        new_mark = r["is_new"]
        if SL is not None and r["clinic_id"]:
            try:
                new_mark = 1 if SL.is_new_id(con, r["clinic_id"], NEW_DAY) else 0
            except Exception:                                           # noqa: BLE001
                new_mark = r["is_new"]
        con.execute("UPDATE slip SET day=?, is_new=?, updated_by='S667', updated_at=? WHERE id=?", (NEW_DAY, new_mark, now, r["id"]))
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("slip", r["id"], "slip_day_move", json.dumps({"day": OLD_DAY, "is_new": r["is_new"]}),
                     json.dumps({"day": NEW_DAY, "is_new": new_mark, "why": "typed 27-Oct on a desk page left open since 26-Oct (S667)"}), "S667", now))
        moved += 1
        said.append("%s %d: moved %s -> %s%s" % (series, no, OLD_DAY, NEW_DAY, (" (new-patient mark %s -> %s)" % (r["is_new"], new_mark)) if new_mark != r["is_new"] else ""))
    others = con.execute("SELECT series, slip_no, day, logged_at FROM slip WHERE state='ok' AND day<? AND logged_at LIKE ? "
                         "AND NOT ((series='opd' AND slip_no=19858) OR (series='xp' AND slip_no=1420)) ORDER BY logged_at",
                         (NEW_DAY, NEW_DAY + "%")).fetchall()
    if dry:
        con.rollback()
    else:
        con.commit()
    con.close()
    print("; ".join(said))
    for o in others:
        print("also typed %s but filed on %s (NOT moved -- a late entry, or a decision for the owner): %s %s"
              % (o["logged_at"][:16], o["day"], o["series"], o["slip_no"]))
    print("moved %d%s" % (moved, " (DRY: rolled back)" if dry else ""))
    return 2 if bad else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    lib = a[a.index("--lib") + 1] if "--lib" in a else ""
    pos = [x for x in a if not x.startswith("--") and x != lib]
    if len(pos) != 1:
        sys.exit(__doc__)
    try:
        sys.exit(main(pos[0], "--dry" in a, lib))
    except Exception as e:                                              # noqa: BLE001
        print("the data step failed: %s: %s" % (type(e).__name__, e))
        sys.exit(1)
