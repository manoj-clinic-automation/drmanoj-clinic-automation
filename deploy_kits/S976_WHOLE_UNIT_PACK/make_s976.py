#!/usr/bin/env python3
"""make_s976.py -- builds S976_WHOLE_UNIT_PACK's five files from their FROM bytes and blocks/ (each anchor found exactly once).
    python3 make_s976.py FROM_DIR OUT_DIR"""
import hashlib, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"stock_figure.py": "0d8cab560d19783febf134058f447763", "stock_watch.py": "fe0a89cd0206b19ccf5439c9f364fb5e",
        "stockmatch.py": "1f5a15bade4f6e002e61b883eadcaee0", "voucher_judge.py": "59a68bb15c24261f533a48a33457fccb",
        "stock_check.py": "6b8d077cd2e30b18dd02e42551a2d83f"}
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = '\nif __name__ == "__main__":\n'


def blk(n):
    return open(os.path.join(HERE, "blocks", n), encoding="utf-8").read()


def once(s, a, b, what):
    if s.count(a) != 1:
        sys.exit("!! %s: the anchor is found %d times" % (what, s.count(a)))
    return s.replace(a, b)


for n, m in FROM.items():
    raw = open(os.path.join(SRC, n), "rb").read()
    if hashlib.md5(raw).hexdigest() != m:
        sys.exit("!! %s is not at its FROM pin %s" % (n, m[:8]))
    s = raw.decode("utf-8")
    if n == "stock_figure.py":
        s = once(s, MAIN, blk("block_sf.py").rstrip("\n") + "\n" + MAIN, n)
    elif n == "stock_watch.py":
        s = once(s, MAIN, blk("block_sw.py").rstrip("\n") + "\n" + MAIN, n)
    elif n == "stockmatch.py":
        s = once(s, '        pack = sw.pack_of(it["packing"])\n',
                 '        pack = sw._s976_pack(con, it["name"], it["packing"])           # S976 (F-1742): a whole-unit item is one box, in its word\n', n)
    elif n == "voucher_judge.py":
        s = s.rstrip("\n") + "\n" + blk("block_vj.py")
    elif n == "stock_check.py":
        s = s.rstrip("\n") + "\n" + blk("block_sc.py")
    open(os.path.join(OUT, n), "w", encoding="utf-8", newline="\n").write(s)
    print("%-18s %s -> %s" % (n, m[:8], hashlib.md5(s.encode("utf-8")).hexdigest()[:8]))
