#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""call_cap_s911.py -- kit S911 (the parent, S495, 20-Nov-2026): the engine says how many fitted under the 120-call cap.

processor.py caps the day's follow-up calls at 120 (DAILY_CALL_CAP): the most winnable first, the room left filled with the most
overdue probable dropouts; whoever does not fit waits for the next run. The engine never said how many waited. ONE print line,
right after the cap decides, says it -- 'CALL CAP: kept 120 of 143 due for a call -- 23 wait for tomorrow' -- and lands in the
run's own log (the server runner's logs/runner.log; the PC's console log). The owner's console reads the newest line (D1027).
Nothing else changes: the workbook, the data files and the cap itself are as before (Replay 2's content hash is unchanged).

    python3 call_cap_s911.py <processor.py> --check    exit 0: the line is there / 1: not yet / 2: the anchor is missing
    python3 call_cap_s911.py <processor.py> --apply    insert it (idempotent); written beside as <file>.s911, moved into place
"""
import ast
import os
import sys

ANCHOR = ('            else:\n'
          '                # already within cap → keep all (minus the 3-strike rows already removed)\n'
          '                combined = _w\n')
LINE = ('            try:                                                  # S911: the cap\'s count, one line for the owner\'s console\n'
        '                print("CALL CAP: kept %d of %d due for a call -- %d wait for tomorrow"\n'
        '                      % (len(combined), len(_w), len(_w) - len(combined)))\n'
        '            except Exception:\n'
        '                pass\n')
MARK = "CALL CAP: kept %d of %d due for a call"


def state(src):
    if MARK in src:
        return "done"
    return "todo" if src.count(ANCHOR) == 1 else "no-anchor"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    with open(path, encoding="utf-8", newline="") as fh:
        src = fh.read()
    nl = "\r\n" if "\r\n" in src.split("\n", 1)[0] + "\n" else "\n"
    st = state(src if nl == "\n" else src.replace("\r\n", "\n"))
    if "--apply" not in argv:
        print("%s: %s" % (os.path.basename(path), {"done": "the CALL CAP line is there", "todo": "the CALL CAP line is not there (anchor found)",
                                                   "no-anchor": "ANCHOR MISSING -- not the engine this kit was built on"}[st]))
        return {"done": 0, "todo": 1, "no-anchor": 2}[st]
    if st == "done":
        print("%s: already" % os.path.basename(path))
        return 0
    if st == "no-anchor":
        raise SystemExit("%s: the anchor is missing -- nothing written" % os.path.basename(path))
    body = src if nl == "\n" else src.replace("\r\n", "\n")
    out = body.replace(ANCHOR, ANCHOR + LINE)
    ast.parse(out)                                   # still parses
    if nl != "\n":
        out = out.replace("\n", nl)
    tmp = path + ".s911"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    os.replace(tmp, path)
    print("%s: the CALL CAP line inserted" % os.path.basename(path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
