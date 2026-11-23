#!/usr/bin/env python3
"""make_s941.py -- kit S941's TO files. argv: <S940 kit dir> <src dir> <out dir>
porders_s454.py's FROM = S940's TO; order_d1053_msg.py's FROM = S940's TO (replaced whole: v1.0 -> v1.1)."""
import hashlib, os, sys
K940, SRC, OUT = sys.argv[1:4]
def rd(p): return open(p, "rb").read()
def md5(b): return hashlib.md5(b).hexdigest()
pins = dict((l.split()[1], l.split()[0]) for l in open(os.path.join(K940, "TO_PINS.md5")) if l.strip())
p = rd(os.path.join(K940, "porders_s454.py")); assert md5(p) == pins["finance/porders_s454.py"]
assert md5(rd(os.path.join(K940, "order_d1053_msg.py"))) == pins["finance/order_d1053_msg.py"]
os.makedirs(OUT, exist_ok=True)
p = p.decode("utf-8")
assert p.endswith("# ---- S940 end ---------------------------------------------------------------------------------------------------------------------------\n")
p += open(os.path.join(SRC, "block_porders_s941.py"), encoding="utf-8").read()
open(os.path.join(OUT, "porders_s454.py"), "w", encoding="utf-8", newline="\n").write(p)
open(os.path.join(OUT, "order_d1053_msg.py"), "wb").write(rd(os.path.join(SRC, "order_d1053_msg.py")))
for f in ("porders_s454.py", "order_d1053_msg.py"):
    print(md5(rd(os.path.join(OUT, f))), f)
