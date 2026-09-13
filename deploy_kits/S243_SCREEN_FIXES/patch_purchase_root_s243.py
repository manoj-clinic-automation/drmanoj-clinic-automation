#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_purchase_root_s243.py -- S243: the bare prefix /finance/purchase (with or
without the trailing slash) answered 404 because the blueprint had no root rule;
every rule was /page/..., /api/..., /salts.xlsx. One new rule sends the bare
prefix to the hub, the page the portal tile already opens. Nothing else moves.

    python3 -B patch_purchase_root_s243.py            # reads PA_PATH or /root/finance/purchase_app.py
    PA_PATH=./purchase_app.py python3 -B patch_purchase_root_s243.py --out purchase_app.py.new

Refuses unless the anchor occurs exactly once; prints the md5 before and after.
With --out it writes the patched text to that path and never touches the source.
"""
import hashlib
import io
import os
import sys

TARGET = os.environ.get("PA_PATH", "/root/finance/purchase_app.py")
FROM_MD5 = "8090ca2041574e25be39682dd5555ffe"      # S240_SANJEEVNI_123 rev 13, the live pin
MARK = "def page_root():"

OLD = '@bp.route("/page/hub")\ndef page_hub():\n'
NEW = ('@bp.route("/", strict_slashes=False)\n'
       'def page_root():\n'
       '    """S243: the bare prefix -> the hub. Both /finance/purchase and\n'
       '    /finance/purchase/ land here; the app\'s own gate has already run."""\n'
       '    return redirect(request.script_root + _url_prefix + "/page/hub", code=302)\n'
       '\n\n'
       '@bp.route("/page/hub")\ndef page_hub():\n')


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    print("source %s md5 %s" % (TARGET, md5(raw)))
    if MARK in src:
        print("ALREADY PATCHED -- nothing to do")
        return 0
    if md5(raw) != FROM_MD5:
        print("REFUSED: source is not the pin this patch was built on (%s)" % FROM_MD5)
        return 2
    n = src.count(OLD)
    if n != 1:
        print("REFUSED: anchor occurs %d times, need exactly 1" % n)
        return 2
    new = src.replace(OLD, NEW, 1)
    compile(new, TARGET, "exec")
    dest = out or TARGET
    io.open(dest, "w", encoding="utf-8", newline="\n").write(new)
    print("wrote %s md5 %s" % (dest, md5(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
