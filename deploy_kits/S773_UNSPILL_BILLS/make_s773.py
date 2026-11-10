#!/usr/bin/env python3
"""make_s773.py FINANCE_DIR KIT_DIR OUT_DIR -- kit S773_UNSPILL_BILLS (S423, 10-Nov-2026, the Sanjeevni chat; F-1233).
purchase_app.py: ONE guarded call in api_push, before the lines are re-dated -- built from the LIVE bytes (F-472): the file must
be at its FROM pin and the anchor must match exactly once, or nothing is built. purchase_unspill.py: NEW, copied from the kit."""
import hashlib
import os
import shutil
import sys

FROM = {"purchase_app.py": "8424e05b780db4624b23b16189ead545"}
ANCHOR = ('    _redate_lines(con)\n'
          '    if typ in ("BILLWISE", "SUPPLIERWISE"):\n'
          '        _resolve_wrong(con, md5=md5, stamp=stamp)                  # S371 (F-614)\n')
HOOK = ('    try:                                                       # S773 (F-1233): a bill number Marg fused onto the item name,\n'
        '        import purchase_unspill                                # noqa: PLC0415 -- split off by evidence (a real bill of the\n'
        '        purchase_unspill.unspill(con, by="push")               # same supplier), logged; beside this file\n'
        '    except Exception as _ex_s773:                              # noqa: BLE001 -- never fails a push: the lines stay as they came\n'
        '        if not con.in_transaction:                             # ...unless the push\'s own writes were lost with it: never "stored"\n'
        '            raise\n'
        '        import sys as _sys_s773                                # noqa: PLC0415\n'
        '        print("purchase_unspill skipped: %s" % _ex_s773, file=_sys_s773.stderr)\n')


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(fin, kit, out):
    os.makedirs(out, exist_ok=True)
    b = open(os.path.join(fin, "purchase_app.py"), "rb").read()
    if md5(b) != FROM["purchase_app.py"]:
        print("REFUSED: purchase_app.py is %s, not its FROM pin %s" % (md5(b)[:8], FROM["purchase_app.py"][:8]))
        return 2
    t = b.decode("utf-8")
    if t.count(ANCHOR) != 1 or t.count("    _redate_lines(con)\n") != 1:
        print("REFUSED: purchase_app.py: the anchor matches %d times" % t.count(ANCHOR))
        return 2
    t = t.replace(ANCHOR, HOOK + ANCHOR)
    nb = t.encode("utf-8")
    open(os.path.join(out, "purchase_app.py"), "wb").write(nb)
    print("built purchase_app.py %s -> %s" % (FROM["purchase_app.py"][:8], md5(nb)[:8]))
    shutil.copyfile(os.path.join(kit, "purchase_unspill.py"), os.path.join(out, "purchase_unspill.py"))
    print("copied purchase_unspill.py (new) %s" % md5(open(os.path.join(out, "purchase_unspill.py"), "rb").read())[:8])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
