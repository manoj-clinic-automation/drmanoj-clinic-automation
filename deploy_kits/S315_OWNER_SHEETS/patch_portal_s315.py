#!/usr/bin/env python3
"""patch_portal_s315.py -- adds ONE tile to /root/portal/portal.py: the doctor's two sheets.
Two additive edits, both anchored on text read from the live file (no inferred anchor, F-472):
a tile dict at the head of TILES' doctor block, and its _TILE_GROUP row. Idempotent; refuses
to write anything else. Usage: patch_portal_s315.py PORTAL_PY [--check]"""
import io
import sys

TILE = ('    {"icon": "\\U0001FA7B", "name": "Procedures & prices",\n'
        '     "desc": "Your X-ray price list and what each procedure uses", "live": True,\n'
        '     "url": "/finance/clinic/sheets",\n'
        '     "roles": ["doctor"]},\n\n')
ANCHOR = ('    {"icon": "\\U0001F4CA", "name": "Clinic Gist",\n')
GROUP_ANCHOR = '    "System Board": "Clinic",\n'
GROUP_ROW = '    "Procedures & prices": "Clinic",\n'


def apply(text):
    done = 0
    if '"name": "Procedures & prices"' not in text:
        if text.count(ANCHOR) != 1:
            raise SystemExit("!! the TILES anchor is not unique - nothing written")
        text = text.replace(ANCHOR, TILE + ANCHOR)
        done += 1
    if GROUP_ROW not in text:
        if text.count(GROUP_ANCHOR) != 1:
            raise SystemExit("!! the _TILE_GROUP anchor is not unique - nothing written")
        text = text.replace(GROUP_ANCHOR, GROUP_ANCHOR + GROUP_ROW)
        done += 1
    return text, done


def main():
    path = sys.argv[1]
    src = io.open(path, encoding="utf-8").read()
    out, done = apply(src)
    if "--check" in sys.argv:
        print("WOULD CHANGE %d" % done)
        return 0
    if done:
        io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("portal patched: %d edit(s)%s" % (done, "" if done else " - already in place"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
