#!/usr/bin/env python3
# make_s370.py -- portal.py S369 (f24abe2d) -> S370: the card's script swapped whole (one anchored replacement; the HTML is unchanged).
import hashlib, os, sys
FROM = "f24abe2d61bd95062741ab577c59c5a1"
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read(); assert hashlib.md5(b).hexdigest() == FROM, "live portal.py is not f24abe2d (S369)"
t = b.decode("utf-8"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portal_push_S369 as old, portal_push as new  # noqa: E402
assert old.CARD_HTML == new.CARD_HTML and t.count(old.CARD_JS) == 1
t = t.replace(old.CARD_JS, new.CARD_JS)
open(out, "wb").write(t.encode("utf-8")); print("portal.py S370 ->", hashlib.md5(t.encode("utf-8")).hexdigest())
