#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s812.py LIVE_MHC SEG_DIR OUT -- kit S812 (13-Nov-2026, Sanjeevni session 445): marg_hand_change.py 3b8c2160 -> the Marg watch's section A engine.
Every patch is an exact anchor that occurs once; the two replaced spans (compute .. refresh, and rows_for_page .. _connect) are cut between
anchors that occur once. Anything else stops the build."""
import hashlib, sys

FROM = "3b8c216011941abe86af2bb0ce836b1e"


def one(s, a, b):
    if s.count(a) != 1:
        raise SystemExit("anchor not found once (%d): %r" % (s.count(a), a[:80]))
    return s.replace(a, b)


def span(s, a, b, new):
    if s.count(a) != 1 or s.count(b) != 1:
        raise SystemExit("span anchors not found once: %r .. %r" % (a[:40], b[:40]))
    i, j = s.index(a), s.index(b)
    return s[:i] + new + s[j:]


def main():
    src, segd, out = sys.argv[1:4]
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("the live file is not %s -- stopped" % FROM[:8])
    s = raw.decode("utf-8")
    seg = lambda n: open("%s/%s" % (segd, n), encoding="utf-8").read()      # noqa: E731
    s = one(s, 'KIT = "S706_HAND_CHANGE_WATCH"\n',
            'KIT = "S706_HAND_CHANGE_WATCH"\nKIT2 = "S812_MARG_WATCH_STOCK"                   # S812 (13-Nov-2026): the records behind a move, the late bill, the rupees, the floor\n')
    s = one(s, '    ("hand.since", "", "S706: set by the first fill -- rows found then are the history: on the page, never announced"),\n)',
            '    ("hand.since", "", "S706: set by the first fill -- rows found then are the history: on the page, never announced"),\n'
            '    ("hand.floor_rs", "0", "S812 (D943): a counted move worth less than this many rupees is listed on the Marg watch, never told; 0 = none"),\n'
            '    ("hand.s812_since", "", "S812: set by its first run -- a move it finds then that was never stored is history: on the page, never told"),\n'
            '    ("hand.last_run", "", "S812: the last refresh -- what it read"),\n)')
    s = one(s, '"found_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT \'open\', status_at TEXT, hist INTEGER NOT NULL DEFAULT 0, UNIQUE (k20, day_to, kind))")\n',
            '"found_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT \'open\', status_at TEXT, hist INTEGER NOT NULL DEFAULT 0, UNIQUE (k20, day_to, kind))")\n'
            'EXTRA_COLS = (("rec_kind", "TEXT"), ("rec_ref", "TEXT"), ("rec_note", "TEXT"), ("owed_paid", "REAL"), ("rate_p", "INTEGER"), ("value_p", "INTEGER"))   # S812, additive\n')
    s = one(s, 'NOTES_TO = "2026-11-04"',
            'NOTES_DAY = {"ANKLE BINDER TYNOR X": "2026-10-10", "ANKLE BINDER XL TYNO": "2026-10-10", "VFER 500": "2026-10-28", "V FER 500": "2026-10-28",\n'
            '             "CARTILOX SACHET": "2026-10-25", "CAST SHOE L TYNOR": "2026-10-25", "EXLAIN A": "2026-10-25", "RUNVACE TP": "2026-10-25",\n'
            '             "KNEE SUPPORT L HINGE": "2026-10-25", "KNEE SUPPORT M HINGE": "2026-10-25", "KNEE IMMOBILIZER L U": "2026-10-25",\n'
            '             "KNEE IMMOBILIZER M T": "2026-10-25", "ENZOMAC OINTMENT": "2026-10-25", "GLI-ME SR1": "2026-10-25", "NORTIMER TAB": "2026-10-25",\n'
            '             "POWERGESIC 200 PATCH": "2026-10-07"}   # S812 (F-1270): the closing each note was written for; CCM\'s note fitted none of its rows\n'
            'NOTES_TO = "2026-11-04"')
    s = one(s, 'def ensure(con):\n    con.execute(SCHEMA)\n',
            'def ensure(con):\n    con.execute(SCHEMA)\n    have = {r[1] for r in con.execute("PRAGMA table_info(marg_hand_change)")}\n'
            '    for c, t in EXTRA_COLS:                                    # S812: added columns; kind, status and the key keep their meaning\n'
            '        if c not in have:\n            con.execute("ALTER TABLE marg_hand_change ADD COLUMN %s %s" % (c, t))\n')
    s = span(s, "def compute(spine_path=SPINE_DB", "def refresh(con, spine_path=SPINE_DB", seg("seg_compute.py"))
    s = span(s, "def refresh(con, spine_path=SPINE_DB", "def _connect(db, ro=False):", seg("seg_refresh.py"))
    s = one(s, '''                snum(r["shift"]), ("  pair " + r["pair_item"]) if r["pair_item"] else "", "  (put right)" if r["settled"] else ""))''',
            '''                snum(r["shift"]), ("  pair " + r["pair_item"]) if r["pair_item"] else "", "  (put right)" if r["settled"] else ""))
            if r.get("rec_kind") or r.get("rec_note"):
                print("         record %s: %s" % (r.get("rec_kind") or "-", r.get("rec_note")))''')
    s = one(s, '''        print("S706 dry END -- %d row(s); nothing written" % len(rows))''',
            '''        print("S812 bills read for matcher 1: %s %s; purchase export last taken %s" % (info.get("bills"), info.get("bills_why") or "", info.get("last_pur_taken")))
        print("S706 dry END -- %d row(s); nothing written" % len(rows))''')
    b = s.encode("utf-8")
    open(out, "wb").write(b)
    print(hashlib.md5(b).hexdigest())


if __name__ == "__main__":
    main()
