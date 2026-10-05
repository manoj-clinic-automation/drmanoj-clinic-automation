#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reading_s481.py -- S481_COMMAND_CONSOLE: one reading of the REAL box, said in a few lines (the installer's eyes).

  build <dir holding owner_console.py> <finance dir> <finance.db> <out.json>
        makes a reading exactly as the service's builder does (finance.db copied through a read-only door; the app's own
        modules loaded from the finance dir without a cache file; nothing live written) and writes it to <out.json>
  show  <reading.json>
        says an existing reading
Printed: one line of the seven sections' chips; one line per piece that could not be read, with its reason (the page shows
those in grey, in plain words -- the reason is for the assistant). No amount is printed. Last line: READING OK unread=<n>
or READING RED <why>.
"""
import json
import os
import sys

sys.dont_write_bytecode = True
WANT = ["needs", "money", "work", "att", "sanj", "papers", "system"]


def say(snap):
    if not isinstance(snap, dict) or not snap.get("ok"):
        print("READING RED the reading is not a reading")
        return 1
    if snap.get("order") != WANT or any(k not in (snap.get("sections") or {}) for k in WANT):
        print("READING RED the seven sections are not all there: %s" % snap.get("order"))
        return 1
    if snap.get("failed"):
        why = "; ".join("%s (%s)" % (k, snap["sections"][k].get("why", "?")) for k in snap["failed"])
        print("READING RED a whole section could not be made: %s" % why[:400])
        return 1
    g = snap.get("guard") or {}
    if g.get("env_is_copy") is not True or g.get("app_db_is_copy") is False:
        print("READING RED the app's modules were not pointed at the copy: %s" % g)
        return 1
    chips = []
    for k in WANT:
        s = snap["sections"][k]
        chips.append("%s %s" % (s.get("name"), str(s.get("chip") or "")))
    print("   the reading (%s, %s s): %s" % (snap.get("as_of"), snap.get("took_s"), " | ".join(chips))[:600])
    if float(snap.get("took_s") or 0) > 60:
        print("READING RED it took %s s; a reading is stopped at 120 s" % snap.get("took_s"))
        return 1
    unread = [l for k in WANT for l in snap["sections"][k].get("lines") or [] if l.get("why") and "could not be" in (l.get("text") or "")]
    for l in unread:
        print("   not read: %s [%s]" % (str(l.get("text"))[:90], str(l.get("why"))[:200]))
    print("READING OK unread=%d" % len(unread))
    return 0


def main(argv):
    if len(argv) == 3 and argv[1] == "show":
        try:
            with open(argv[2], encoding="utf-8") as fh:
                return say(json.load(fh))
        except Exception as e:                                         # noqa: BLE001
            print("READING RED %s: %s" % (type(e).__name__, str(e)[:200]))
            return 1
    if len(argv) == 6 and argv[1] == "build":
        kit, fin, db, out = argv[2:6]
        os.environ.setdefault("CONSOLE_FRESHNESS", os.path.join(fin, "freshness.json"))
        os.environ.setdefault("CONSOLE_BEAT", os.path.join(fin, "reception_heartbeat.json"))
        try:
            sys.path.insert(0, kit)
            import owner_console as oc                                 # noqa: PLC0415
            oc.FIN = fin                                               # the app's modules are the box's own, read where they live
            os.chdir(fin)
            return say(oc.build(db, out))
        except BaseException as e:                                     # noqa: BLE001
            print("READING RED %s: %s" % (type(e).__name__, str(e)[:300]))
            return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
