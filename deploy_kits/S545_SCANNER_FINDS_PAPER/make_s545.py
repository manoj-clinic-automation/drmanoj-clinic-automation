#!/usr/bin/env python3
"""S545_SCANNER_FINDS_PAPER -- exact, counted edits on the md5-pinned live scanner_widget.js (F-890).
usage: patch_s545.py <live scanner_widget.js> <s545_block.js> <out file>
Refuses unless the input is 65127fcb7c9c00ded03190c5156c7f6e and every anchor occurs exactly once."""
import hashlib, sys

FROM_MD5 = "65127fcb7c9c00ded03190c5156c7f6e"
src_p, funcs_p, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
raw = open(src_p, "rb").read()
if hashlib.md5(raw).hexdigest() != FROM_MD5:
    sys.exit("REFUSED: scanner_widget.js is not the pinned " + FROM_MD5)
s = raw.decode("utf-8")
funcs = open(funcs_p, "rb").read().decode("utf-8")

EDITS = [
    ("E1 the S545 block before cvWarp",
     "  function cvWarp(canvas, q, bw){\n",
     funcs + "  function cvWarp(canvas, q, bw){\n"),
    ("E2 step 3 in cvFindQuad",
     "        found = quadFromContours(hulls, w, h, 0.04, blur) || quadFromContours(hulls, w, h, 0.08, blur);\n"
     "        hulls.delete();\n"
     "      }\n",
     "        found = quadFromContours(hulls, w, h, 0.04, blur) || quadFromContours(hulls, w, h, 0.08, blur);\n"
     "        hulls.delete();\n"
     "      }\n"
     "      if (!found) found = quadFromPaper(src, w, h);                                 // S545: 3. the paper by its colour (F-890)\n"),
    ("E3 upright after the warp (capture)",
     "      try { du = cvWarp(full, q, $(\"bw\").checked).toDataURL(\"image/jpeg\", 0.88); }\n",
     "      try { du = cvUpright(cvWarp(full, q, $(\"bw\").checked)).toDataURL(\"image/jpeg\", 0.88); }     // S545: a sideways bill turned upright\n"),
    ("E4 upright after the warp (Adjust)",
     "    try { pages[i] = cvWarp(full, q, $(\"bw\").checked).toDataURL(\"image/jpeg\", 0.88); pageCorners[i] = q; }\n",
     "    try { pages[i] = cvUpright(cvWarp(full, q, $(\"bw\").checked)).toDataURL(\"image/jpeg\", 0.88); pageCorners[i] = q; }   // S545\n"),
]
for name, old, new in EDITS:
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: %s -- anchor found %d times (must be 1)" % (name, n))
    s = s.replace(old, new, 1)
    print("OK", name)
open(out_p, "wb").write(s.encode("utf-8"))
print("written", out_p, hashlib.md5(s.encode("utf-8")).hexdigest())
