#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s627.py -- S627_LATE_FOLLOWS_MONTH: rebuilds the two TO files from the pinned FROM bytes by exact, counted edits.

    python3 -B make_s627.py <FROM folder> <TO folder>

Each anchor must occur exactly ONCE; a FROM byte other than the pin stops it; nothing else is written.
"""
import hashlib
import os
import sys

FROM_PIN = {"asset_register.py": "f21ae7ca012f67ea7aa10a0f9d6f05c9",      # S625's TO
            "sorting_desk.py": "110335eac5a9792ebe52620ee676a13c"}

EDITS = {
    "asset_register.py": [
        ('''    elif bd and re.match(r"^\\d{4}-\\d{2}-\\d{2}$", bd) and bd[:7] < made:
        late = bd[:7]
    db.execute("UPDATE bills SET late_for=? WHERE id=?", (late, bid))''',
         '''    elif bd and re.match(r"^\\d{4}-\\d{2}-\\d{2}$", bd) and bd[:7] < made:
        late = bd[:7]
    if late is None:                                                        # S627: a paper that counts in an earlier month by S625's
        mo = _s625_counts(db, bid)                                          # rule (clinic_papers.MONTH_OF) is 'late' for that month too
        try:                                                                # -- compared with the scan month in IST, as the rule counts it
            mi = (datetime.datetime.strptime((b["created_at"] or "")[:19], "%Y-%m-%d %H:%M:%S")
                  + datetime.timedelta(minutes=330)).strftime("%Y-%m")
        except ValueError:
            mi = made
        if mo and mo < mi:
            late = mo
    db.execute("UPDATE bills SET late_for=? WHERE id=?", (late, bid))'''),
    ],
    "sorting_desk.py": [
        ('''The month is the one set on the bill, else its bill date, else the month it was scanned; supplier spellings are merged.''',
         '''The month is the one set on the bill, else its bill date, else the month it was scanned; from 22-Oct-2026 a bill dated in an earlier month than its scan counts in its own month (a person's earlier month still wins); supplier spellings are merged.'''),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    total = 0
    for f, edits in EDITS.items():
        raw = open(os.path.join(src, f), "rb").read()
        if md5(raw) != FROM_PIN[f]:
            raise SystemExit("REFUSED: %s is %s, not the pinned %s" % (f, md5(raw)[:8], FROM_PIN[f][:8]))
        s = raw.decode("utf-8")
        for k, (a, b) in enumerate(edits, 1):
            n = s.count(a)
            if n != 1:
                raise SystemExit("REFUSED: %s edit %d -- its anchor occurs %d times (want 1)" % (f, k, n))
            s = s.replace(a, b)
            total += 1
        data = s.encode("utf-8")
        open(os.path.join(dst, f), "wb").write(data)
        out("%s: %d counted edit(s), %s -> %s" % (f, len(edits), FROM_PIN[f][:8], md5(data)))
    out("make_s627: %d counted edits in all" % total)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
