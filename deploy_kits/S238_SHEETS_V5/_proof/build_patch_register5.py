#!/usr/bin/env python3
"""build_patch_register5.py -- staff_register.py v0.16 (b6da7c8d..., LIVE since 11-Sep 05:41)
-> v0.17 (S238): the settings page carries cover_auto_from (salary_policy v1.12). Anchored."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != "b6da7c8d56b74daee7e96f94fa84ea9f":
    sys.exit("source is not the live v0.16")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    if s.count(old) != 1:
        sys.exit("anchor %s found %d times" % (label, s.count(old)))
    s = s.replace(old, new)
rep('''v0.16(S238) — Step 0 is a proper A4 document''', '''v0.17(S238) — settings page: "Cover staff: a punch-out at/after this time is a cover day"
              (cover_auto_from, 20:00; salary_policy v1.12 verifies cover by the punch).
v0.16(S238) — Step 0 is a proper A4 document''', "doc")
rep('''    ("cover_end", "Extra-duty (cover) ends at (HH:MM) — OT on a cover day counts after this"),''',
    '''    ("cover_auto_from", "Cover staff: a punch-out at/after this time (HH:MM) is a cover day — extra-duty paid"),
    ("cover_end", "Extra-duty (cover) ends at (HH:MM) — OT on a cover day counts after this"),''', "label")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
