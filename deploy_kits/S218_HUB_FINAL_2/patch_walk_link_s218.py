#!/usr/bin/env python3
"""patch_walk_link_s218.py -- S218: the walk's not-filed step linked
/finance/daily, which role-bounces a CHECKER to the portal (found by the owner
on the first live walk). Point it at the Review console instead."""
import datetime as dt, os, shutil, sys
TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
OLD = """                links=[dict(label="open the maker page", url="/finance/daily?d=" + iso)]))"""
NEW = """                links=[dict(label="open your Review console", url="/finance/review")]))"""
def main():
    src = open(TARGET, encoding="utf-8").read()
    if NEW in src:
        print("already patched -- nothing to do"); return 0
    n = src.count(OLD)
    if n != 1:
        raise SystemExit("REFUSED: anchor matches %d times (need 1)." % n)
    bak = TARGET + ".bak_S218_walklink_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copyfile(TARGET, bak)
    out = src.replace(OLD, NEW, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); restored" % ex)
    print("patched walk link; backup %s" % bak)
    return 0
if __name__ == "__main__":
    sys.exit(main())
