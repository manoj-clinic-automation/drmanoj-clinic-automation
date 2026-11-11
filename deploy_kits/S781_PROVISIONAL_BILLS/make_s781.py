#!/usr/bin/env python3
"""make_s781.py FINANCE_DIR KIT_DIR OUT_DIR -- kit S781_PROVISIONAL_BILLS (S426, 11-Nov-2026, the Sanjeevni chat; D891, D892).
purchase_app.py: from its FROM pin, the S781 block appended (KIT_DIR/block_s781.py) -- nothing else in it changes.
provisional_s781.py: NEW, the kit's whole file. Refuses unless the live file is at its FROM pin and provisional_s781.py is absent."""
import hashlib
import os
import shutil
import sys

FROM = {"purchase_app.py": "51e42707211def1a9c13943a19798552"}
NEW = ("provisional_s781.py",)


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main(fin, kit, out):
    os.makedirs(out, exist_ok=True)
    src = os.path.join(fin, "purchase_app.py")
    if md5(src) != FROM["purchase_app.py"]:
        print("REFUSED: purchase_app.py is %s, not %s" % (md5(src)[:8], FROM["purchase_app.py"][:8]))
        return 2
    for n in NEW:
        if os.path.exists(os.path.join(fin, n)):
            print("REFUSED: %s already exists beside purchase_app.py" % n)
            return 2
    s = open(src, encoding="utf-8").read()
    if "# ---- S781 (" in s:
        print("REFUSED: an S781 block is already in purchase_app.py")
        return 2
    if not s.endswith("\n"):
        s += "\n"
    s += open(os.path.join(kit, "block_s781.py"), encoding="utf-8").read()
    with open(os.path.join(out, "purchase_app.py"), "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    shutil.copyfile(os.path.join(kit, "provisional_s781.py"), os.path.join(out, "provisional_s781.py"))
    print("built purchase_app.py %s -> %s · provisional_s781.py NEW %s" % (FROM["purchase_app.py"][:8], md5(os.path.join(out, "purchase_app.py"))[:8],
                                                                          md5(os.path.join(out, "provisional_s781.py"))[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
