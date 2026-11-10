#!/usr/bin/env python3
"""make_s778.py FINANCE_DIR KIT_DIR OUT_DIR -- kit S778_ORDER_SCREEN (S425, 10-Nov-2026, the Sanjeevni chat; D890).
porders_s454.py: from its FROM pin, one counted edit (api_qty accepts a line put on a card by S778) and the S778 block appended
(KIT_DIR/block_s778.py). order_s778.py: NEW, the kit's whole file. Refuses unless the live file is at its FROM pin and order_s778.py
is absent beside it."""
import hashlib
import os
import shutil
import sys

FROM = {"porders_s454.py": "cd2feeb3ad0ef6f34cb2515d56838770"}
NEW = ("order_s778.py",)
QTY_OLD = '    if src not in ("sheet", "proposal", "ortho", "carry"):     # S619: + a carried line\n'
QTY_NEW = '    if src not in ("sheet", "proposal", "ortho", "carry", "s778"):     # S619: + a carried line; S778: + a line put on a card by S778\n'


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main(fin, kit, out):
    os.makedirs(out, exist_ok=True)
    src = os.path.join(fin, "porders_s454.py")
    if md5(src) != FROM["porders_s454.py"]:
        print("REFUSED: porders_s454.py is %s, not %s" % (md5(src)[:8], FROM["porders_s454.py"][:8]))
        return 2
    for n in NEW:
        if os.path.exists(os.path.join(fin, n)):
            print("REFUSED: %s already exists beside porders_s454.py" % n)
            return 2
    s = open(src, encoding="utf-8").read()
    if s.count(QTY_OLD) != 1:
        print("REFUSED: the api_qty line is there %d times, not once" % s.count(QTY_OLD))
        return 2
    s = s.replace(QTY_OLD, QTY_NEW, 1)
    if "# ---- S778 (" in s:
        print("REFUSED: an S778 block is already in porders_s454.py")
        return 2
    if not s.endswith("\n"):
        s += "\n"
    s += open(os.path.join(kit, "block_s778.py"), encoding="utf-8").read()
    with open(os.path.join(out, "porders_s454.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    shutil.copyfile(os.path.join(kit, "order_s778.py"), os.path.join(out, "order_s778.py"))
    print("built porders_s454.py %s -> %s · order_s778.py NEW %s" % (FROM["porders_s454.py"][:8], md5(os.path.join(out, "porders_s454.py"))[:8],
                                                                    md5(os.path.join(out, "order_s778.py"))[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
