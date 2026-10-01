#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s440_s444.py -- kit S444_STAFF_SAFE: S440's walk, re-run on the box + S444 (Purchase orders carries S444's one 'Signed in'
line in its S440 BACK bar), against S440's own control (the .bak_S440 files).

S440's walk is COPIED to scratch and two assertions are adjusted there by anchored replacement (each anchor exactly once, else STOP);
the S440 kit folder is never edited. Both were already red on the box as it is, before S444 -- both moved by the parent's S441
(installed 01-Oct 09:19 IST):
  A8  "the count on the section is groups 1-4": S441 added the 'twin' question group to Scan ka kaam and counts it.
  A9  "the explanation is folded under 'Kaise?' with its three paragraphs word for word": S441 reworded the intake's paragraphs;
      the adjusted check still asserts the fold and that it carries text.

    walk_s440_s444.py --k440 DIR --work DIR -- <walk_s440.py's own arguments>
"""
import os
import subprocess
import sys

R = "S444-ADJUSTED"
ADJ = [
    ("A8",
     'K0["counts"]["amount"],',
     'K0["counts"]["amount"] + K0["counts"].get("twin", 0),   # ' + R + ' A8: S441 counts its twin group\n                    '),
    ("A9",
     'text_kept=all(t in ik for t in ("Photograph the paper bill", "A paper that already carries a B-number is never scanned again", "Old bills from last month?")),',
     'text_kept=bool(re.search(r"<details class=card id=kaise><summary[^>]*>.*?</summary>.{40,}?</details>", ik, re.S)),   # ' + R + ' A9: S441 reworded'),
]


def main():
    argv = sys.argv[1:]
    k440 = argv[argv.index("--k440") + 1]
    work = argv[argv.index("--work") + 1]
    rest = argv[argv.index("--") + 1:]
    src = open(os.path.join(k440, "walk_s440.py"), encoding="utf-8").read()
    for code, old, new in ADJ:
        n = src.count(old)
        if n != 1:
            print("STOP: walk_s440.py adjustment %s anchor occurs %d times" % (code, n))
            return 2
        src = src.replace(old, new, 1)
    os.makedirs(work, exist_ok=True)
    w = os.path.join(work, "walk_s440.py")
    open(w, "w", encoding="utf-8").write(src)
    print("-- S440's walk copied to %s with A8 (the twin group counted, S441) and A9 (the intake's reworded fold, S441)" % w)
    p = subprocess.run([sys.executable, "-B", w] + rest, cwd=work)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
