#!/usr/bin/env python3
# make_s369.py -- portal.py S366 (7bddc17c) -> S369: the card's HTML and script swapped for the S369 ones (two anchored
# replacements, each the whole S366 block, taken from the S366 portal_push.py beside this file as portal_push_S366.py).
import hashlib, os, sys
FROM = "7bddc17cd7e65c75303b0046a86a08db"
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest() == FROM, "live portal.py is not 7bddc17c (S366)"
t = b.decode("utf-8")
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import portal_push_S366 as old, portal_push as new  # noqa: E402
for o, n, label in ((old.CARD_HTML, new.CARD_HTML, "card"), (old.CARD_JS, new.CARD_JS, "script")):
    assert t.count(o) == 1, "anchor not unique: " + label + " (" + str(t.count(o)) + ")"
    t = t.replace(o, n)
open(out, "wb").write(t.encode("utf-8"))
print("portal.py S369 ->", hashlib.md5(t.encode("utf-8")).hexdigest())
