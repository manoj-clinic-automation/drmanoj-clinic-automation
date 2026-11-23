#!/usr/bin/env python3
"""make_s940.py -- kit S940's TO files from its FROM files and src/. argv: <S939 kit dir> <order_rules.py FROM> <src dir> <out dir>
porders_s454.py's FROM is kit S939's TO (its TO_PINS.md5); order_rules.py's FROM is the live 0964c6b2."""
import hashlib, os, sys
K939, RULES, SRC, OUT = sys.argv[1:5]
def rd(p): return open(p, "rb").read()
def md5(b): return hashlib.md5(b).hexdigest()
pins = dict((l.split()[1], l.split()[0]) for l in open(os.path.join(K939, "TO_PINS.md5")) if l.strip())
p = rd(os.path.join(K939, "porders_s454.py"))
assert md5(p) == pins["finance/porders_s454.py"], "S939's porders_s454.py is not at its TO pin"
r = rd(RULES)
assert md5(r) == "0964c6b2d8b2c46b243a8501ba3a5350", "order_rules.py is not at its FROM pin"
os.makedirs(OUT, exist_ok=True)
p = p.decode("utf-8")
assert p.endswith("# ---- S939 end ---------------------------------------------------------------------------------------------------------------------------\n")
p += open(os.path.join(SRC, "block_porders_s940.py"), encoding="utf-8").read()
open(os.path.join(OUT, "porders_s454.py"), "w", encoding="utf-8", newline="\n").write(p)
r = r.decode("utf-8")
A = 'if __name__ == "__main__":                                   # S454 P1D: last in the file'
assert r.count(A) == 1
r = r.replace(A, open(os.path.join(SRC, "block_rules_s940.py"), encoding="utf-8").read() + A, 1)
open(os.path.join(OUT, "order_rules.py"), "w", encoding="utf-8", newline="\n").write(r)
open(os.path.join(OUT, "order_d1053_msg.py"), "wb").write(rd(os.path.join(SRC, "order_d1053_msg.py")))
for f in ("porders_s454.py", "order_rules.py", "order_d1053_msg.py"):
    print(md5(rd(os.path.join(OUT, f))), f)
