#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s862.py -- kit S862_PATIENTS_WORDS_ENQUIRIES (the parent, S480, 18-Nov-2026). Builds the three TO files from the FROM
files read out of the 18-Nov bundle (each FROM checked by md5; every anchor must occur exactly once).
    python3 make_s862.py <from_dir> <to_dir>"""
import hashlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import snip_pp as A, snip_p2 as B, snip_html as C   # noqa: E401,E402
FROM = {"patients_page.py": "561c6bf442c3bc40dde695e96d88bddc", "patients_page.html": "62e5dc884c30a83ae0e3314b4ea1003b",
        "patients_part2.py": "0277cb5cb32f3b95c420ca6745e19e7e"}
src, dst = sys.argv[1:3]
os.makedirs(dst, exist_ok=True)


def rep(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit("!! anchor %s found %d times" % (what, n))
    return t.replace(old, new)


def ins_before(t, anchor, block, what):
    return rep(t, anchor, block + anchor, what)


for n, m in FROM.items():
    b = open(os.path.join(src, n), "rb").read()
    if hashlib.md5(b).hexdigest() != m:
        sys.exit("!! %s is not its FROM pin" % n)
t = open(os.path.join(src, "patients_page.py"), encoding="utf-8").read()
t = rep(t, 'VERSION = "S853 1.0"', 'VERSION = "S862 1.0"', "pp version")
t = rep(t, A.DOC_OLD, A.DOC_NEW, "pp doc")
t = rep(t, A.WORDS_OLD, A.WORDS_NEW, "pp words")
t = rep(t, A.READING_OLD, A.READING_NEW, "pp reading")
t = ins_before(t, A.HELPERS_ANCHOR, A.HELPERS, "pp helpers")
t = ins_before(t, A.REBUILD_ANCHOR, A.REBUILD, "pp rebuild")
t = ins_before(t, A.ROUTES_ANCHOR, A.ROUTES, "pp routes")
open(os.path.join(dst, "patients_page.py"), "w", encoding="utf-8").write(t)

t = open(os.path.join(src, "patients_part2.py"), encoding="utf-8").read()
t = rep(t, B.DOC_OLD, B.DOC_NEW, "p2 doc")
t = rep(t, B.CONST_OLD, B.CONST_NEW, "p2 const")
t = rep(t, B.GOOGLE_OLD, B.GOOGLE_NEW, "p2 google")
t = rep(t, B.GHEAD_OLD, B.GHEAD_NEW, "p2 google head")
t = rep(t, B.GCONST_OLD, B.GCONST_NEW, "p2 google const")
t = ins_before(t, B.BECAME_ANCHOR, B.BECAME, "p2 became")
t = rep(t, B.READ2_OLD, B.READ2_NEW, "p2 read2")
t = rep(t, B.READ2B_OLD, B.READ2B_NEW, "p2 read2b")
open(os.path.join(dst, "patients_part2.py"), "w", encoding="utf-8").write(t)

t = open(os.path.join(src, "patients_page.html"), encoding="utf-8").read()
for o, nw, w in ((C.CSS_OLD, C.CSS_NEW, "css"), (C.WORDS_OLD, C.WORDS_NEW, "words"), (C.NEXT_OLD, C.NEXT_NEW, "next"),
                 (C.DESK_OLD, C.DESK_NEW, "desk"), (C.GSUB_OLD, C.GSUB_NEW, "gsub"), (C.CHIPS_OLD, C.CHIPS_NEW, "chips")):
    t = rep(t, o, nw, "html " + w)
open(os.path.join(dst, "patients_page.html"), "w", encoding="utf-8").write(t)
for n in FROM:
    print("%s %s" % (hashlib.md5(open(os.path.join(dst, n), "rb").read()).hexdigest(), n))
