#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""undo_s598.py -- kit S598_ARRIVALS_BY_LINE: puts the rows rejudge_s598.py saved back, every column, from its JSON. WRITTEN, documented,
NEVER run by the installer (only if the owner says 'undo' and the chat decides the data change must be reversed).

    python3 -B undo_s598.py --db <finance.db or a COPY> --json <the JSON rejudge_s598.py wrote> [--dry]

R1-C6: a row that MOVED since the JSON is refused -- its detected_at or arrived_at is set and differs from the JSON's (a later detect_supplies
tick re-marked it under the new rule, or a person tapped it): skipped and printed. A row cleared by the re-judge (detected_at NULL) or still
equal to the JSON is restored (idempotent). Audits line_undo_s598 per restored row. Prints the diff after (must be empty for the restored rows)
and 'UNDO OK S598 ...'. No phone number is printed."""
import argparse
import json
import re
import sqlite3
import sys


def mask(s):
    return re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))


def say(s=""):
    print(mask(s), flush=True)


def now_iso():
    import datetime as dt
    return dt.datetime.now().replace(microsecond=0).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    J = json.load(open(a.json, encoding="utf-8"))
    cols = J["columns"]
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    live_cols = [r[1] for r in con.execute("PRAGMA table_info(purchase_order_line)")]
    missing = [c for c in cols if c not in live_cols]
    if missing:
        say("UNDO RED S598: the table lacks columns the JSON holds: %s -- nothing done" % missing)
        return 1
    restored, skipped, same = [], [], []
    for j in J["rows"]:
        cur = con.execute("SELECT * FROM purchase_order_line WHERE id=?", (j["id"],)).fetchone()
        if cur is None:
            say("   line %s: not in the table -- skipped" % j["id"])
            skipped.append(j["id"])
            continue
        cur = dict(cur)
        moved = []
        for c in ("detected_at", "arrived_at"):
            if cur.get(c) is not None and cur.get(c) != j.get(c):
                moved.append("%s %r (the JSON: %r)" % (c, cur.get(c), j.get(c)))
        if moved:
            say("   line %-4s %-30s MOVED since the JSON -- refused: %s" % (j["id"], str(j["item"])[:30], "; ".join(moved)))
            skipped.append(j["id"])
            continue
        if all(cur.get(c) == j.get(c) for c in cols):
            say("   line %-4s %-30s already equal to the JSON (nothing to do)" % (j["id"], str(j["item"])[:30]))
            same.append(j["id"])
            continue
        diff = {c: (cur.get(c), j.get(c)) for c in cols if cur.get(c) != j.get(c)}
        say("   line %-4s %-30s restored: %s" % (j["id"], str(j["item"])[:30], diff))
        if not a.dry:
            sets = ", ".join("%s=?" % c for c in cols if c != "id")
            con.execute("UPDATE purchase_order_line SET %s WHERE id=?" % sets, [j[c] for c in cols if c != "id"] + [j["id"]])
            try:
                con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                            (now_iso(), "s598", "line_undo_s598", str(j["id"]), json.dumps(dict(item=j["item"], before=cur, after={c: j[c] for c in cols}), default=str)))
            except sqlite3.Error as e:
                say("   (audit row not written: %s)" % e)
        restored.append(j["id"])
    if a.dry:
        con.rollback()
    else:
        con.commit()
    left = []
    for j in J["rows"]:
        if j["id"] in skipped:
            continue
        cur = con.execute("SELECT * FROM purchase_order_line WHERE id=?", (j["id"],)).fetchone()
        d = {c: (cur[c], j.get(c)) for c in cols if cur is not None and cur[c] != j.get(c)}
        if d and not a.dry:
            left.append((j["id"], d))
    con.close()
    say("   the diff after (restored rows against the JSON): %s" % (left or "empty"))
    if left:
        say("UNDO RED S598: %d row(s) still differ" % len(left))
        return 1
    say("UNDO OK S598: %d restored (%s), %d already equal (%s), %d refused as moved (%s)%s" % (len(restored), ",".join(map(str, restored)) or "-", len(same), ",".join(map(str, same)) or "-",
                                                                                               len(skipped), ",".join(map(str, skipped)) or "-", " [DRY]" if a.dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
