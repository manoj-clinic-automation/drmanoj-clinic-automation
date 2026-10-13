#!/usr/bin/env python3
"""walk_box_s545.py -- the box's part of the S545 walk (the browser walk -- made-up photos and the seven surfaces with the
pinned OpenCV 4.10.0 -- ran before the publish; its results are walk/walk_results.txt).

    python3 walk_box_s545.py <scanner_widget.js> [--expect-red]

Checks the file carries every S545 piece, inside the smart-path block. (That nothing else moved is the installer's
rebuild: the four counted edits on the pinned bytes must give the kit's pin exactly.)
Prints GREEN/RED per check; exit 1 on any RED (with --expect-red: exit 0 only if at least one RED -- the control)."""
import sys

F = sys.argv[1]
EXPECT_RED = "--expect-red" in sys.argv
s = open(F, encoding="utf-8").read()
R = []


def check(name, ok):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name)


check("step 3 (the paper by its colour) is called inside cvFindQuad",
      s.count("if (!found) found = quadFromPaper(src, w, h);") == 1)
check("the paper finder, its Otsu split, its frame rule and its sharp-edge rule are defined once each",
      all(s.count("function %s(" % f) == 1 for f in ("quadFromPaper", "paperQuadOK", "edgesSharp", "otsuRange", "cvUpright")))
check("a captured page is turned upright after the warp", s.count("du = cvUpright(cvWarp(full, q,") == 1)
check("an adjusted page is turned upright after the warp", s.count("pages[i] = cvUpright(cvWarp(full, q,") == 1)
a, b = s.find("/* ======================= S523"), s.find("/* ======================= end S523")
if a < 0:
    a = s.find("var CV = null, cvReady = false")
check("every S545 piece sits inside the S523 smart-path block",
      a >= 0 and b > a and all(a < s.find(m) < b for m in ("function quadFromPaper(", "function cvUpright(", "quadFromPaper(src, w, h)")))
check("the smart path is still gated on cvScan and cvUrl", s.count("var cvScanOn = (CFG.cvScan === true) && !!CFG.cvUrl;") == 1)
check("the version mark S545.1 is served", "S545.1" in s)

red = R.count(False)
print("%d checks, %d green, %d red" % (len(R), len(R) - red, red))
if EXPECT_RED:
    sys.exit(0 if red else 1)     # the control: success means the live file is told apart
sys.exit(1 if red else 0)
