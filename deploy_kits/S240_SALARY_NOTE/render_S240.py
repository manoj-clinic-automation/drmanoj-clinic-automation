#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_S240.py <month> <outfile> -- render sheets 3 and 4 exactly as the page does, to a file.
Read-only: it computes and renders, and writes nothing but the file it is given."""
import io
import sys

import salary_policy as P

ym, out = sys.argv[1], sys.argv[2]
res = P.compute(ym)
io.open(out, "w", encoding="utf-8").write(P.sheets34_html(res))
print("rendered %s -> %s (%d staff)" % (ym, out, len(res["staff"])))
