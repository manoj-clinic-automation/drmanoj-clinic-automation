#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s756.py -- S756_SUMMARY_DEALER_WA: the anchored changes and the appended sections of three live files (this project's only).
    python3 -B make_s756.py <finance dir> <out dir> [<dir holding the sec_*756.txt files>]
Each FROM file must carry its pinned md5 (the live bytes of 09-Nov: the 09-Nov bundle = kit S755's TO pins); every anchor must stand
EXACTLY the number of times named; the TO md5s are printed."""
import hashlib
import os
import sys

FROM = {"finance/scan_register.py": "0822d3084c14fc479311d19c3847c57a",     # S755's TO (the 09-Nov bundle)
        "finance/purchase_app.py": "e80f199c2f29cde54baecd43000e659f",      # S755's TO
        "finance/owner_notice.py": "9096af9a328627b923022029de8abc21"}      # S755's TO
APPEND = {"finance/scan_register.py": "sec_sr756.txt", "finance/purchase_app.py": "sec_pa756.txt", "finance/owner_notice.py": "sec_on756.txt"}

SR_EDITS = [
    # row 7: the awaited line follows the month -- a parked month asks nobody; a counted one says the dealer is reminded too
    ('''        else:                                             # S755: on reception's list by itself since the month ended; the owner and Shavez told each morning
            who = "On reception's list by itself since the month ended · you and Shavez are told each morning until it comes."''',
     '''        else:                                             # S755 / S756: the words follow the month -- a parked month asks nobody
            who = _s756_awaited_words(con, month)''', 1),
]

PA_EDITS = []

ON_EDITS = [
    # F-1207: the command-line guard leaves the middle of the file (sec_on756 puts it back LAST)
    ('''        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
''',
     '''        return 0
    print(__doc__)
    return 2


# S756 (F-1207): the command-line guard is at the END of this file, after every section.
''', 1),
    # S755's morning line says nothing when assets.db cannot be read (every dealer would look awaited)
    ('''    for m in SR._s755_ended_months(con):
        key = "summaries:%s:%s" % (m, day)''',
     '''    if SR.s750_summary_scans(con) is None:                        # S756: assets.db unread -> every dealer would look awaited; say nothing
        return []
    for m in SR._s755_ended_months(con):
        key = "summaries:%s:%s" % (m, day)''', 1),
    # the dealers' names without Marg's padding ("Drug Deal                     Bareilly")
    ('''        names = [str(d["name"]).title() for d in aw]''',
     '''        names = [" ".join(str(d["name"]).split()).title() for d in aw]   # S756: Marg's padding gone''', 1),
]

EDITS = {"finance/scan_register.py": SR_EDITS, "finance/purchase_app.py": PA_EDITS, "finance/owner_notice.py": ON_EDITS}


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(text, edits, name):
    for old, new, n in edits:
        c = text.count(old)
        if c != n:
            sys.exit("!! %s: anchor stands %d time(s), expected %d:\n%s" % (name, c, n, old[:200]))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fin, out = sys.argv[1], sys.argv[2]
    here = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    for rel, want in FROM.items():
        src = os.path.join(fin, os.path.basename(rel))
        b = open(src, "rb").read()
        if md5(b) != want:
            sys.exit("!! %s is %s, expected %s -- not the live bytes this kit was built on; STOP" % (src, md5(b)[:8], want[:8]))
        if b"\r\n" in b:
            sys.exit("!! %s carries CRLF; STOP" % src)
        t = b.decode("utf-8")
        if "KIT_S756" in t:
            sys.exit("!! %s already carries S756; STOP" % src)
        t = apply(t, EDITS[rel], rel)
        sec = open(os.path.join(here, APPEND[rel]), "rb").read().decode("utf-8")
        t = t.rstrip("\n") + "\n" + sec
        if rel == "finance/owner_notice.py" and t.count('if __name__ == "__main__":') != 1:
            sys.exit("!! owner_notice.py: the guard must stand exactly once, at the end; STOP")
        nb = t.encode("utf-8")
        os.makedirs(os.path.join(out, os.path.dirname(rel)), exist_ok=True)
        open(os.path.join(out, rel), "wb").write(nb)
        print("%s  %s -> %s" % (rel, want[:8], md5(nb)))


if __name__ == "__main__":
    main()
