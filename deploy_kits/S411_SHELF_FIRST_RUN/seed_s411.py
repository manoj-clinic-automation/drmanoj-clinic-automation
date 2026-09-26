#!/usr/bin/env python3
"""seed_s411.py -- kit S411_SHELF_FIRST_RUN. On the finance database (a scratch copy in the walk, the live one at install):
  1. the three ICICI slots the first run showed (INSERT OR IGNORE) and the twelve accounts' holder words as the banks print them
     (only where the words are still the S408 seed's -- a value the owner edited is left alone)
  2. every bank-folder file's identification is cleared (slot, read status, note) -- the card files are untouched
  3. packs.process_inbox() re-identifies and reads them with the S411 identifier and the v1.1 ICICI reader
  4. the month grid for August and September 2026 is printed (states only -- no amount, no account)
Usage: seed_s411.py DB_PATH   (FINANCE_DIR names the folder holding packs.py; default /root/finance)
"""
import os
import sqlite3
import sys


def seed(path):
    fin = os.environ.get("FINANCE_DIR", "/root/finance")
    if fin not in sys.path:
        sys.path.insert(0, fin)
    os.environ.setdefault("FINANCE_DB", path)
    import packs  # noqa: E402
    con = sqlite3.connect(path, timeout=60)
    con.row_factory = sqlite3.Row
    packs.ensure(con)
    words_now = {r["key"]: (r["ident_words"] or "") for r in con.execute("SELECT key, ident_words FROM stmt_slot")}
    new_words = {k: w for (k, _b, _l, _kind, w, _s) in packs.SLOTS}
    changed = []
    for key, old in packs.S408_WORDS.items():
        if key in words_now and words_now[key].strip().upper() == old and new_words.get(key) and new_words[key] != old:
            con.execute("UPDATE stmt_slot SET ident_words=? WHERE key=?", (new_words[key], key))
            changed.append("%s: %s -> %s" % (key, old, new_words[key]))
    n_before = con.execute("SELECT COUNT(*) FROM stmt_file WHERE folder='bank'").fetchone()[0]
    con.execute("UPDATE stmt_file SET slot_id=NULL, read_status=NULL, matched_status=NULL, note=NULL, identified_at=NULL, ident_how=NULL WHERE folder='bank'")
    con.commit()
    res = packs.process_inbox(con)
    slots = con.execute("SELECT COUNT(*) FROM stmt_slot").fetchone()[0]
    print("seed: %d slots (3 ICICI added by S411 where missing); words replaced: %s; %d bank files re-identified -> %s"
          % (slots, ("; ".join(changed) if changed else "none (already S411's or owner-edited)"), n_before, res))
    for m in ("2026-07", "2026-08", "2026-09"):
        cells = packs.cells(con, m)
        print("  grid %s: %s" % (m, " · ".join("%s=%s" % (c["slot"], c["state"]) for c in cells if c["kind"] != "card")))
    unpl = packs.unplaced(con)
    print("  unplaced now: %d -> %s" % (len(unpl), "; ".join("#%d %s (%s%s)" % (u["id"], (u["holder"] or ("locked" if u["locked"] else "?"))[:40], u["bank"] or "?", (" …" + u["tail"]) if u["tail"] else "") for u in unpl if u["folder"] != "all_txn")))
    ref = con.execute("SELECT COUNT(*) FROM stmt_file WHERE read_status LIKE 'refused%'").fetchone()[0]
    print("  still refused: %d" % ref)
    con.close()
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
