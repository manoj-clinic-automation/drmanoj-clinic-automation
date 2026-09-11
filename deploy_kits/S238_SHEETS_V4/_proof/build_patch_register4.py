#!/usr/bin/env python3
"""build_patch_register4.py -- staff_register.py v0.15 (f7cbfe3e..., LIVE since 10-Sep 23:20)
-> v0.16 (S238, the owner 11-Sep-2026): Step 0 rebuilt as a proper A4 document (one
table, a row per date, tick boxes, Sundays shaded, the header repeating on every page);
dates-only staff (Amir Sohail) listed by the dates they punched; settings page carries
cover_end, dates_only_staff and the optional daily OT threshold. The new page block is read from verify_block.txt beside
this script. Anchored, exactly-once edits."""
import hashlib, sys, os
SRC, DST = sys.argv[1], sys.argv[2]
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != "f7cbfe3ee4150d84f5013703c686c05b":
    sys.exit("source is not the live v0.15")
s = raw.decode("utf-8")
BLOCK = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_block.txt"), encoding="utf-8").read()
def rep(old, new, label):
    global s
    if s.count(old) != 1:
        sys.exit("anchor %s found %d times" % (label, s.count(old)))
    s = s.replace(old, new)
rep('''v0.15(S238) — the settings page carries''', '''v0.16(S238) — Step 0 is a proper A4 document (a row per date, P/L/A tick boxes, Sundays
              shaded, header repeated on every printed page); staff listed in the policy's
              dates_only_staff (Amir Sohail) appear only as the dates they punched; the
              settings page carries cover_end and dates_only_staff (salary_policy v1.11).
v0.15(S238) — the settings page carries''', "doc")
a = s.index('VERIFY_HTML = """<!doctype html>')
b = s.index('@app.route(APP_PREFIX + "/salary/flow")\n@require("salary")\ndef salary_flow():')
s = s[:a] + BLOCK + s[b:]
rep('''        _vb, _vok = _verify_blocks(ym)''', '''        _vb, _vok, _vd = _verify_blocks(ym)''', "flow_v0")
rep('''    ("ot_pay", "Overtime payable enters the net (1 = pay, 0 = show only)"),''',
    '''    ("ot_pay", "Overtime payable enters the net (1 = pay, 0 = show only)"),
    ("cover_end", "Extra-duty (cover) ends at (HH:MM) — OT on a cover day counts after this"),
    ("dates_only_staff", "Staff shown by punch dates only, not on the grid (names, comma-separated)"),
    ("ot_threshold_on", "Ignore small daily overtime (1 = on, 0 = off)"),
    ("ot_daily_min", "…a day's overtime under this many minutes is not counted (when switched on)"),''', "labels")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
