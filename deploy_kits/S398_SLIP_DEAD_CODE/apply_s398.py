#!/usr/bin/env python3
"""apply_s398.py -- kit S398_SLIP_DEAD_CODE. Makes the S398 slip_log.py from the live S392 bytes (ffb629c1) by DELETION ONLY:
the Docterz-upload screen retired at S379 left its old code behind unconditional returns, and three helpers that only that
code called. Nothing that runs today is touched: both old doors still answer with the same redirect.
Usage: python apply_s398.py <S392 slip_log.py> <out>"""
import ast, hashlib, sys
b = open(sys.argv[1], "rb").read()
assert hashlib.md5(b).hexdigest() == "ffb629c1b4dd3220053d2ecf02d5d6b1", "the source is not S392 slip_log.py"
s = b.decode("utf-8")
L = s.split("\n")                                     # L[i] is line i+1
drop = set()
tree = ast.parse(s)
fn = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
# 1-3: whole helpers whose only callers are dead code
for name in ("emr_items", "emr_pending_count", "_emr_html"):
    n = fn[name]
    start = min([n.lineno] + [d.lineno for d in n.decorator_list])
    drop.update(range(start, n.end_lineno + 1))
    # the two blank lines that followed the function
    k = n.end_lineno + 1
    while k <= len(L) and L[k - 1].strip() == "" and k <= n.end_lineno + 2:
        drop.add(k); k += 1
# 4-5: the bodies left after "return redirect(...)" in the two retired doors
for name in ("emr_page", "emr_mark"):
    n = fn[name]
    ret = [i for i, st in enumerate(n.body) if isinstance(st, ast.Return)
           and "redirect" in ast.get_source_segment(s, st) and "S379" in L[st.lineno - 1]]
    assert len(ret) == 1, name
    tail = n.body[ret[0] + 1:]
    assert tail, name
    drop.update(range(tail[0].lineno, n.end_lineno + 1))
# 6: the X-ray-upload panel in _report_html, switched off by "n_emr, old_emr = 0, None"
n = fn["_report_html"]
blk = [i for i, st in enumerate(n.body) if isinstance(st, ast.Assign) and "n_emr, old_emr = 0, None" in L[st.lineno - 1]]
assert len(blk) == 1
a = n.body[blk[0]]; iff = n.body[blk[0] + 1]
assert isinstance(iff, ast.If) and ast.get_source_segment(s, iff.test) == "n_emr" and not iff.orelse
drop.update(range(a.lineno, iff.end_lineno + 1))
# 7: the flag only the retired screen read
k = [i + 1 for i, x in enumerate(L) if x == "_BLOOD_ASKING = [False]"]
assert len(k) == 1; drop.add(k[0])
out = "\n".join(x for i, x in enumerate(L) if i + 1 not in drop)
assert "_BLOOD_ASKING" not in out and "emr_items" not in out and "_emr_html" not in out and "n_emr" not in out
ast.parse(out)
open(sys.argv[2], "wb").write(out.encode("utf-8"))
print("S398 slip_log.py md5", hashlib.md5(out.encode("utf-8")).hexdigest(), "lines", out.count("\n") + 1, "removed", len(drop))
