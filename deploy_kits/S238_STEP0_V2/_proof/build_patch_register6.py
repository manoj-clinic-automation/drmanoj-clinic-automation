#!/usr/bin/env python3
"""build_patch_register6.py -- staff_register.py v0.17 (2904a118..., LIVE since 11-Sep 06:20)
-> v0.18 (S238, the owner 11-Sep-2026 on the first real print): Step 0 condensed -- three
dates per row, tighter rows, the two explanatory paragraphs removed (a one-line hint stays
in the header). The page template is read from verify_html2.txt beside this script."""
import hashlib, sys, os
SRC, DST = sys.argv[1], sys.argv[2]
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != "2904a11845d7ea9565cca403c5b16ae0":
    sys.exit("source is not the live v0.17")
s = raw.decode("utf-8")
NEW = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_html2.txt"), encoding="utf-8").read()
def rep(old, new, label):
    global s
    if s.count(old) != 1:
        sys.exit("anchor %s found %d times" % (label, s.count(old)))
    s = s.replace(old, new)
rep('''v0.17(S238) — settings page:''', '''v0.18(S238) — Step 0 condensed for print: three dates per row, tighter rows, the two
              explanatory paragraphs removed (the owner, on the first real 3-page print).
v0.17(S238) — settings page:''', "doc")
a = s.index('VERIFY_HTML = """<!doctype html>')
b = s.index('\n\n\ndef _verify_blocks(ym):')
s = s[:a] + NEW.rstrip("\n") + s[b:]
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
