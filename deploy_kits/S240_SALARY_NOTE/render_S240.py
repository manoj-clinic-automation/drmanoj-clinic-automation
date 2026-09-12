#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_S240.py <salary_policy dir> <month> <outfile>

Renders sheets 3 and 4 exactly as the page does, to a file. Read-only: it computes and renders,
and writes nothing but the file it is given.

The directory is passed in rather than assumed from the working directory: a script run by its
absolute path puts its OWN folder on the import path, not the one it was launched from -- which
is how the first attempt failed with ModuleNotFoundError while sitting in the right folder.
"""
import io
import os
import sys

sdir, ym, out = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, sdir)
os.chdir(sdir)

import salary_policy as P                                      # noqa: E402

res = P.compute(ym)
io.open(out, "w", encoding="utf-8").write(P.sheets34_html(res))
print("   rendered %s from %s -> %d staff" % (ym, sdir, len(res["staff"])))
