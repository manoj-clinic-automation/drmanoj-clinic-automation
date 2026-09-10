#!/usr/bin/env python3
"""build_patch_register3.py -- staff_register.py v0.14 (794afc26..., LIVE since 10-Sep 22:07)
-> v0.15 (S238): the settings page carries 'ot_pay' (salary_policy v1.10). Anchored."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != "794afc2661ae5931f8e3a380401af3e8":
    sys.exit("source is not the live v0.14")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    if s.count(old) != 1:
        sys.exit("anchor %s found %d times" % (label, s.count(old)))
    s = s.replace(old, new)
rep('''v0.14(S238) — STEP 0 of the month-end flow''', '''v0.15(S238) — the settings page carries "Overtime payable enters the net (1/0)" --
              salary_policy v1.10 shows OT on Sheet 1 and pays it only when set.
v0.14(S238) — STEP 0 of the month-end flow''', "doc")
rep('''    ("outstation_rs", "Outstation credit Rs/night"),''', '''    ("outstation_rs", "Outstation credit Rs/night"),
    ("ot_pay", "Overtime payable enters the net (1 = pay, 0 = show only)"),''', "label")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
