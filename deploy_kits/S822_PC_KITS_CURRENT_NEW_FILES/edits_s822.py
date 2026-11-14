#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s822.py -- kit S822_PC_KITS_CURRENT_NEW_FILES (session S456, the parent, 14-Nov-2026): exact, counted edits
turning the live /root/finance/pc_kits.py (4191e447, S821) into the S822 file.
    python3 edits_s822.py LIVE OUT [KIT]   (exit 0 only if every anchor occurs once and, when KIT is given, OUT = KIT)

Why (D972, F-1386): the Medical PC's kit sentence promised 'The new kit shows here after your next publish and the next
server line'. With S822 the server pulls the repository clone by itself every half hour (cron, /root/deploy/repo_pull_s822.sh),
so a repacked kit reaches the Clinic PCs page within half an hour of the owner's publish -- no server line. One sentence
changes; nothing else. Display only: no route, no door, no logic changed; nothing written. Never a number, key or token.
"""
import hashlib
import sys

EDITS = [
    # 1 -- the module's own note
    ('''door, nothing written, the same owner-only gate.
"""
''', '''door, nothing written, the same owner-only gate.

S822 (14-Nov-2026, D972): the server pulls the repository clone this page serves from by itself, every half hour
(cron '# S822_REPO_PULL', /root/deploy/repo_pull_s822.sh, fast-forward only) -- a kit repacked on Dr Manoj's PC by the
nightly pc_kits_current.py reaches this page within half an hour of his publish, with no server line. Only the Medical
PC's `kit_keeps` sentence changes here. Display only.
"""
'''),
    # 2 -- the Medical PC's kit sentence
    ('''                  "into the kit by itself, or the night's report says why not. The new kit shows here after your "
                  "next publish and the next server line."},
''', '''                  "into the kit by itself, or the night's report says why not. A new program on that PC joins the kit "
                  "the same way. The new kit shows here within half an hour of your publish."},
'''),
]


def main():
    if len(sys.argv) < 3:
        print("usage: edits_s822.py LIVE OUT [KIT]")
        return 2
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    with open(live, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    for k, (old, new) in enumerate(EDITS, 1):
        n = text.count(old)
        if n != 1:
            print("edit %d: anchor occurs %d time(s), not once -- STOP" % (k, n))
            return 1
        text = text.replace(old, new)
        print("edit %d ok" % k)
    data = text.encode("utf-8")
    with open(out, "wb") as fh:
        fh.write(data)
    print("out %s %d bytes" % (hashlib.md5(data).hexdigest(), len(data)))
    if kit:
        with open(kit, "rb") as fh:
            kb = fh.read()
        if kb != data:
            print("OUT is not the kit's file (%s) -- STOP" % hashlib.md5(kb).hexdigest())
            return 1
        print("OUT = the kit's file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
