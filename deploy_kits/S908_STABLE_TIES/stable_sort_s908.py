#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stable_sort_s908.py -- kit S908 (the parent, S493, 20-Nov-2026): the engine picks the same patients on every machine.

THE FINDING (Replay 2, S897-S907): when the day's list runs over the 120-call cap, processor.py fills the room with the most
overdue dropouts -- `_drop.sort_values("_od", ascending=False).head(_room)` -- a one-key sort whose TIE order numpy settles by
the CPU's instruction set, so the PC and the box choose different patients among those tied on days overdue at the cut-off.
The Probable Dropouts sheet sorts the same column the same way. THE CHANGE: `kind="stable"` on those two sorts -- ties keep
the engine's own priority order (the order the rows arrived in), the same everywhere. Nothing else changes.

    python3 stable_sort_s908.py <processor.py> --check    says whether the two sorts are stable (exit 0) or not (1)
    python3 stable_sort_s908.py <processor.py> --apply    patches in place (idempotent; <file>.s908 then moved into place)
"""
import os
import sys

EDITS = [
    ('.sort_values("_od", ascending=False) \\', '.sort_values("_od", ascending=False, kind="stable") \\'),
    ('''    df_dropout = df_dropout.sort_values("Days_Overdue",
        key=lambda x: pd.to_numeric(x, errors='coerce'), ascending=False)''',
     '''    df_dropout = df_dropout.sort_values("Days_Overdue",
        key=lambda x: pd.to_numeric(x, errors='coerce'), ascending=False, kind="stable")'''),
]


def state(src):
    done = sum(1 for old, new in EDITS if new in src)
    todo = sum(1 for old, new in EDITS if old in src and new not in src)
    return done, todo


def main(argv):
    path = argv[1]
    with open(path, encoding="utf-8", newline="") as fh:
        src = fh.read()
    done, todo = state(src)
    if "--apply" not in argv:
        print("%s: %d of %d sorts stable, %d to do" % (os.path.basename(path), done, len(EDITS), todo))
        return 0 if done == len(EDITS) else 1
    if todo + done != len(EDITS):
        raise SystemExit("%s: an anchor is missing (%d done, %d to do of %d) -- nothing written" % (os.path.basename(path), done, todo, len(EDITS)))
    out = src
    for old, new in EDITS:
        if new in out:
            continue
        if out.count(old) != 1:
            raise SystemExit("anchor not exactly once: %r" % old[:60])
        out = out.replace(old, new)
    import ast
    ast.parse(out)
    tmp = path + ".s908"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    os.replace(tmp, path)
    print("%s: %d sort(s) made stable" % (os.path.basename(path), todo))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
