#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s851.py -- kit S851_PATIENTS_PAGE (the parent, S474, 17-Nov-2026). Builds the patched owner_console.py from the LIVE bytes.

    python make_s851.py <live_dir> <out_dir>

<live_dir> holds the live owner_console.py (S846's 9f4b284d). Every anchor must occur exactly once or the build STOPS and writes
nothing. Two changes: owner_console.init mounts patients_page (its page and its two doors; a fault leaves the console as it was),
and the console's "The month" section gains one line that opens the Patients page. No patient name, no number (F-185).
"""
import hashlib
import os
import sys

FROM = {"owner_console.py": "9f4b284d"}

P = {"owner_console.py": [
    ("    app.register_blueprint(bp)\n\n\n# ============================================================================================ the builder's part\n",
     "    app.register_blueprint(bp)\n"
     "    try:                                                               # S851: the Patients page (his login alone, the same gate)\n"
     "        import patients_page as _s851_pp                               # noqa: PLC0415 -- beside this file\n"
     "        _s851_pp.init(app, db_getter, require_fn, unit)\n"
     "    except Exception as _ex_s851:                                      # noqa: BLE001 -- the console stands without it\n"
     "        print(\"patients_page NOT mounted: %s\" % _ex_s851, file=sys.stderr)\n"
     "\n\n# ============================================================================================ the builder's part\n"),
    ("    lines = MR.section_lines(r)\n",
     "    lines = MR.section_lines(r)\n"
     "    if os.path.exists(os.path.join(FIN, \"patients_page.py\")):         # S851: one line that opens the Patients page\n"
     "        lines.append(L(\"n\", \"Patients — month by month, the follow-ups you gave, diagnosis groups, late returners\",\n"
     "                       href=\"/finance/console/patients\", link=\"Patients\"))\n"),
]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, out = argv[1], argv[2]
    built = {}
    for fn, edits in P.items():
        b = open(os.path.join(src, fn), "rb").read()
        if not md5(b).startswith(FROM[fn]):
            print("STOP: %s is %s, not the live %s -- read the newest bytes first" % (fn, md5(b)[:8], FROM[fn]))
            return 1
        t = b.decode("utf-8")
        for old, new in edits:
            n = t.count(old)
            if n != 1:
                print("STOP: %s: an anchor occurs %d times: %r" % (fn, n, old[:70]))
                return 1
            t = t.replace(old, new, 1)
        built[fn] = t.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    for fn, b in built.items():
        with open(os.path.join(out, fn), "wb") as fh:
            fh.write(b)
        print("%s %s -> %s" % (fn, FROM[fn], md5(b)[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
