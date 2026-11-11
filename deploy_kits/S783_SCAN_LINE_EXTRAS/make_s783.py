#!/usr/bin/env python3
"""make_s783.py FINANCE_DIR ASSETAPP_DIR KIT_DIR OUT_DIR -- kit S783_SCAN_LINE_EXTRAS (S426, 11-Nov-2026, the Sanjeevni chat).
claude_reader.py: from its FROM pin, the S783 block appended (KIT_DIR/block_s783_reader.py) -- nothing else changes.
provisional_s781.py: from its FROM pin, replaced whole by the kit's file. Refuses unless both live files are at their FROM pins."""
import hashlib
import os
import shutil
import sys

FROM = {"claude_reader.py": "ce3868ed707220221728f7012c55d08e", "provisional_s781.py": "15daff39abf9307eb2d71040e2fd22b1"}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main(fin, app, kit, out):
    os.makedirs(out, exist_ok=True)
    cr, ps = os.path.join(app, "claude_reader.py"), os.path.join(fin, "provisional_s781.py")
    for p, n in ((cr, "claude_reader.py"), (ps, "provisional_s781.py")):
        if not os.path.exists(p) or md5(p) != FROM[n]:
            print("REFUSED: %s is %s, not %s" % (n, md5(p)[:8] if os.path.exists(p) else "missing", FROM[n][:8]))
            return 2
    s = open(cr, encoding="utf-8").read()
    if "# ---- S783 (" in s:
        print("REFUSED: an S783 block is already in claude_reader.py")
        return 2
    if not s.endswith("\n"):
        s += "\n"
    s += open(os.path.join(kit, "block_s783_reader.py"), encoding="utf-8").read()
    with open(os.path.join(out, "claude_reader.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    shutil.copyfile(os.path.join(kit, "provisional_s781.py"), os.path.join(out, "provisional_s781.py"))
    print("built claude_reader.py %s -> %s · provisional_s781.py %s -> %s" % (FROM["claude_reader.py"][:8], md5(os.path.join(out, "claude_reader.py"))[:8],
                                                                           FROM["provisional_s781.py"][:8], md5(os.path.join(out, "provisional_s781.py"))[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
