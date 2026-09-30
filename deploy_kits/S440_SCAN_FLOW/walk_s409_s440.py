#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s409_s440.py -- kit S440_SCAN_FLOW re-runs S409's FROZEN walk (deploy_kits/S409_SCAN_LANES/walk_s409.py) with TWO assertions
adjusted, each named here, and nothing else touched. The S409 kit folder is never edited: its walk and its seed are COPIED into the
scratch folder, the two anchored replacements are made on the copy (each anchor exactly once, else this stops), and the copy runs.

  WHY: S409 asserted that a scanning login (role 'reception') is refused the Purchases list and every bill page (403). S440 (D640, the
  brief's 3.2 / 3.4) opens, read-only, the list of what that login scanned itself and those bills. So:
    A1  "reception reaches only its routes: /bills 403, /lanes 403, /intake 200, a bill view 403"
        -> /bills 200 (its own list), /lanes 403, /intake 200, the view of a bill it scanned itself 200
    A2  "the old app's reception gate was already right (/bills 403, /intake 200) and stays so"
        -> the old app's gate as it was (403, 200); the new app's /bills is 200
  Everything else S409 asserts -- the five lanes, the per-login default, the duplicate guard, the slip's Hindi line, the two taps, the
  re-lane by the checkers and its refusal to reception on a clinic paper (403), /lanes 403, the late bills, the pre-fill, the intake's
  "never scanned again" text, the Sanjeevni side -- runs word for word.

Usage: walk_s409_s440.py --k409 <the S409 kit folder> --work <scratch folder> -- <the arguments of walk_s409.py>
"""
import io
import os
import shutil
import subprocess
import sys

args = sys.argv[1:]
if "--" not in args or "--k409" not in args or "--work" not in args:
    sys.exit("usage: walk_s409_s440.py --k409 DIR --work DIR -- <walk_s409.py arguments>")
cut = args.index("--")
own, rest = args[:cut], args[cut + 1:]
k409 = own[own.index("--k409") + 1]
work = own[own.index("--work") + 1]
assert "walk" in work or work.startswith("/tmp"), "refusing a non-scratch folder"
os.makedirs(work, exist_ok=True)
src = io.open(os.path.join(k409, "walk_s409.py"), encoding="utf-8", newline="").read()

ADJUST = [
    ("A1",
     'check("reception reaches only its routes: /bills 403, /lanes 403, /intake 200, a bill view 403", N["reception_gate"] == [403, 403, 200, 403], N["reception_gate"])',
     'check("S440-ADJUSTED A1: a scanning login reads its OWN list and its OWN bill (200, 200 -- read-only, S440 D640); /lanes stays 403, /intake 200", '
     'N["reception_gate"] == [200, 403, 200, 200], N["reception_gate"])'),
    ("A2",
     'check("the old app\'s reception gate was already right (/bills 403, /intake 200) and stays so", O["reception_gate"] == [403, 200] and N["reception_gate"][0] == 403, (O["reception_gate"], N["reception_gate"]))',
     'check("S440-ADJUSTED A2: the old app\'s reception gate as it was (/bills 403, /intake 200); the new app\'s /bills is the login\'s own list (200)", '
     'O["reception_gate"] == [403, 200] and N["reception_gate"][0] == 200, (O["reception_gate"], N["reception_gate"]))'),
]
for name, old, new in ADJUST:
    if src.count(old) != 1:
        sys.exit("REFUSED: the anchor of adjustment %s occurs %d times in S409's walk, not once" % (name, src.count(old)))
    src = src.replace(old, new)
io.open(os.path.join(work, "walk_s409_adjusted.py"), "w", encoding="utf-8", newline="").write(src)
shutil.copy(os.path.join(k409, "seed_s409.py"), os.path.join(work, "seed_s409.py"))
print("-- S409's walk, copied to the scratch folder with 2 assertions adjusted (A1, A2: a scanning login's own list and own bill are 200 since S440); the rest word for word")
sys.stdout.flush()
sys.exit(subprocess.call([sys.executable, "-B", os.path.join(work, "walk_s409_adjusted.py")] + rest))
