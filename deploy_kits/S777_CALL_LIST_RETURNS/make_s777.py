"""S777 maker: python -B make_s777.py <live processor.py (md5 0e7c129f)> <out>
Replaces recalculate_statuses whole with s777_block.py (anchors read from the live bytes)."""
import sys, os, hashlib
src, out = sys.argv[1], sys.argv[2]
b = open(src, encoding='utf-8').read()
assert hashlib.md5(b.encode('utf-8')).hexdigest() == '0e7c129f57b53fca2cb21ba6dcd4d381', 'not the live 0e7c129f'
assert b.count("def recalculate_statuses(") == 1
start = b.index("def recalculate_statuses(")
end = b.index("# ── Step 8: Build output Excel")
new = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 's777_block.py'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8', newline='').write(b[:start] + new + b[end:])
print(hashlib.md5(open(out, 'rb').read()).hexdigest())
