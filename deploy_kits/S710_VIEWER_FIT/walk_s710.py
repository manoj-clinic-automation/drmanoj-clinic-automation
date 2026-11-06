#!/usr/bin/env python3
"""walk_s710.py -- S710: the page's viewer opens a PDF with '#navpanes=0&view=FitH', and S708's walk is still green on the same code.
    python3 -B walk_s710.py <finance code dir> <purchase_schema.sql>
CONTROL: on S708's file the first check goes red."""
import os
import subprocess
import sys

CODE, SCHEMA = sys.argv[1], sys.argv[2]
ok = bad = 0


def check(name, cond):
    global ok, bad
    print(("  ok   " if cond else "  RED  ") + name)
    ok += bool(cond)
    bad += (not cond)


src = open(os.path.join(CODE, "order_track_page.py"), encoding="utf-8").read()
check("1 the PC viewer opens a PDF without the thumbnail strip, full width", "fr.src=f+'#navpanes=0&view=FitH';" in src and "fr.src=f+'#view=FitH';" not in src
      and "#s7v .vimg iframe{height:calc(100vh - 230px)}" in src)
here = os.path.dirname(os.path.abspath(__file__))
r = subprocess.run([sys.executable, "-W", "ignore", "-B", os.path.join(here, "walk_s708.py"), CODE, SCHEMA], capture_output=True, text=True, timeout=600, cwd="/tmp")
last = (r.stdout.strip().splitlines() or [""])[-1]
check("2 S708's walk on the same code: %s" % last, last == "WALK S708: 70 ok, 0 red")
print("WALK S710: %d ok, %d red" % (ok, bad))
