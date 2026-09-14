# -*- coding: utf-8 -*-
r"""patch_vendor_pay_s261.py -- S261, the vendor payments page.

Runs ON THE BOX. It refuses to touch /root/finance/purchase_app.py unless that
file is EXACTLY the one this kit was built from, writes a backup beside it, and
re-reads what it wrote. Three anchored edits, no line of existing behaviour
changed:

ONE anchored insert, and not one existing line edited: the new page, its
bill-lines reader, its own CSS, and a wrapper around the nav helper so every
purchase screen gains the way in without the nav's format string being touched.

    python3 patch_vendor_pay_s261.py --file /root/finance/purchase_app.py
    python3 patch_vendor_pay_s261.py --file X --check    say what it would do
"""
import argparse, hashlib, io, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM_MD5 = "52550e63e7fdffc186de4fcd4f93717b"
TO_MD5 = "a7df849bb3d22b626eed1a958adc8107"

A_BLOCK = '@bp.route("/page/month/<month>")\ndef page_month(month):'


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    raw = open(a.file, "rb").read()
    got = md5(raw)
    if got == TO_MD5:
        print("ALREADY INSTALLED -- %s is already the S261 file (%s)" % (a.file, TO_MD5))
        return 0
    if got != FROM_MD5:
        print("REFUSING -- %s is not the file this kit was built from." % a.file)
        print("           it reads   %s" % got)
        print("           expected   %s" % FROM_MD5)
        return 2

    t = raw.decode("utf-8")
    block = io.open(os.path.join(HERE, "block.py"), encoding="utf-8").read()

    if t.count(A_BLOCK) != 1:
        print("REFUSING -- the anchor appears %d times, not once." % t.count(A_BLOCK))
        return 3

    t = t.replace(A_BLOCK, block.rstrip("\n") + "\n\n\n" + A_BLOCK)

    new = t.encode("utf-8")
    if a.check:
        print("would write %s -> %s" % (got, md5(new)))
        return 0
    bak = "%s.bak_S261_%s" % (a.file, got[:8])
    if not os.path.exists(bak):
        shutil.copy2(a.file, bak)
    open(a.file, "wb").write(new)
    back = md5(open(a.file, "rb").read())
    print("patched %s" % a.file)
    print("   was  %s" % got)
    print("   now  %s" % back)
    print("   backup %s" % bak)
    if back != TO_MD5:
        print("   !! expected %s -- tell Claude before restarting anything" % TO_MD5)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
