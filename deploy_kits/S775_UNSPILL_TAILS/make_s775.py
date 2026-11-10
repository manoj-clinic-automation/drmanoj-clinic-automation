#!/usr/bin/env python3
"""make_s775.py FINANCE_DIR KIT_DIR OUT_DIR -- kit S775_UNSPILL_TAILS (S423, 10-Nov-2026, the Sanjeevni chat; F-1233).
purchase_unspill.py v1.0 -> v1.1 (whole file from the kit; the live one must be at its FROM pin). purchase_app.py is NOT changed:
it must be at S773's pin (its hook calls the module) and is copied beside the new module only so the walk can push through it."""
import hashlib
import os
import shutil
import sys

FROM = {"purchase_unspill.py": "3c12a4cc49989e7485461ea89e63f298"}
NEEDS = {"purchase_app.py": "51e42707211def1a9c13943a19798552"}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main(fin, kit, out):
    os.makedirs(out, exist_ok=True)
    for name, pin in list(FROM.items()) + list(NEEDS.items()):
        if md5(os.path.join(fin, name)) != pin:
            print("REFUSED: %s is %s, not %s" % (name, md5(os.path.join(fin, name))[:8], pin[:8]))
            return 2
    shutil.copyfile(os.path.join(kit, "purchase_unspill.py"), os.path.join(out, "purchase_unspill.py"))
    shutil.copyfile(os.path.join(fin, "purchase_app.py"), os.path.join(out, "purchase_app.py"))
    print("built purchase_unspill.py %s -> %s (purchase_app.py %s unchanged)" % (FROM["purchase_unspill.py"][:8], md5(os.path.join(out, "purchase_unspill.py"))[:8],
                                                                                NEEDS["purchase_app.py"][:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
