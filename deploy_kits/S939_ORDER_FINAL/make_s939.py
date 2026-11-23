#!/usr/bin/env python3
"""make_s939.py -- builds kit S939's TO files from the FROM files (pinned) and src/. argv: <from dir> <src dir> <out dir>"""
import hashlib, os, sys
FROM, SRC, OUT = sys.argv[1:4]
PIN = {"porders_s454.py": "e98e5ed08f861ff3e92ea7fd815cba0f", "darpan_kal.py": "64ce53b75024916d67ec78110c8b1198",
       "darpan_kal.html": "3c30f22dd797aa4036452bc44eb3f78f"}
def rd(p): return open(p, "rb").read()
def md5(b): return hashlib.md5(b).hexdigest()
for f, h in PIN.items():
    assert md5(rd(os.path.join(FROM, f))) == h, "FROM pin mismatch: " + f
os.makedirs(OUT, exist_ok=True)
# 1 porders_s454.py: S939 block appended
p = rd(os.path.join(FROM, "porders_s454.py")).decode("utf-8")
assert p.endswith("# ---- S921 end ---------------------------------------------------------------------------------------------------------------------------\n")
p = p.replace('KIT = "S454_BILL_REGISTER"', 'KIT = "S454_BILL_REGISTER"', 1)
p += open(os.path.join(SRC, "block_porders.py"), encoding="utf-8").read()
open(os.path.join(OUT, "porders_s454.py"), "w", encoding="utf-8", newline="\n").write(p)
# 2 darpan_kal.py: S939 block appended
d = rd(os.path.join(FROM, "darpan_kal.py")).decode("utf-8")
assert d.endswith("# ---- S922 end ---------------------------------------------------------------------------------------------------------------------------\n")
d += open(os.path.join(SRC, "block_darpan.py"), encoding="utf-8").read()
open(os.path.join(OUT, "darpan_kal.py"), "w", encoding="utf-8", newline="\n").write(d)
# 3 darpan_kal.html: three exact anchors
h = rd(os.path.join(FROM, "darpan_kal.html")).decode("utf-8")
A1 = " .ochips{margin-top:4px}\n</style>"
C1 = (" .ochips{margin-top:4px}\n /* S939 (D1053): the old-line questions, the final */\n"
      " .d53box{background:#fff6e0;border:2px solid #8a5a00;border-radius:12px;padding:10px 12px;margin:10px 0}\n"
      " .d53t{font-size:17px;font-weight:700;color:#6b4500;margin:2px 0 6px}\n"
      " .d53q{background:#fff;border-radius:10px;padding:10px;margin:8px 0}.d53i{font-size:16px;font-weight:700;overflow-wrap:anywhere}\n"
      " .d53said{font-size:13px;font-weight:700;color:#1f5f99}\n"
      " .btn.d53{margin:8px 8px 0 0;font:inherit;font-size:14px}.btn.d53w{border-color:#8a5a00;color:#6b4500;background:#fff}\n"
      " .btn.d53.arm{background:#fff3d6;border-color:#e3a008;color:#6b4500}\n"
      "</style>")
assert h.count(A1) == 1; h = h.replace(A1, C1, 1)
A2 = "function renderOrder(){\n const j=OJ, ro=OWNER_RO||j.me===\"owner\", can=j.editable&&!ro;"
C2 = "function renderOrder(){\n if(OJ&&OJ.d1053){d1053Render();return;}   /* S939 (D1053): the one list on Marg's sheet */\n const j=OJ, ro=OWNER_RO||j.me===\"owner\", can=j.editable&&!ro;"
assert h.count(A2) == 1; h = h.replace(A2, C2, 1)
A3 = "load();\nif(location.hash===\"#order\") showTab(true);"
C3 = open(os.path.join(SRC, "js_darpan.js"), encoding="utf-8").read() + A3
assert h.count(A3) == 1; h = h.replace(A3, C3, 1)
open(os.path.join(OUT, "darpan_kal.html"), "w", encoding="utf-8", newline="\n").write(h)
# 4 order_d1053.py: new
open(os.path.join(OUT, "order_d1053.py"), "wb").write(rd(os.path.join(SRC, "order_d1053.py")))
for f in ("porders_s454.py", "darpan_kal.py", "darpan_kal.html", "order_d1053.py"):
    print(md5(rd(os.path.join(OUT, f))), f)
