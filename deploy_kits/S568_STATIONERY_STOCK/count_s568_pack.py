#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""count_s568_pack.py -- the pack fix on a COPY of the live data: how many papers each accountants' bundle holds before and after
S568's build_bundle change, per month and bundle -- COUNTS ONLY, never a name, a stamp or an amount.

    python3 -B count_s568_pack.py <packs.py before> <packs.py after> <the finance folder> <assets.db> <finance.db> <scratch dir> [months...]

Both databases are copied into <scratch dir> with SQLite's backup API (read-only opens of the live files); packs.py is imported
from a copy of the finance folder's program files there, its reader pointed at the copies (count_only=True: no PDF is built,
nothing is sent). The scratch dir is removed at the end."""
import importlib.util, os, shutil, sqlite3, sys

LANES = (("lab_purchase", "8.1 lab"), ("owner_expense", "8.2 Dr Manoj"), ("owner_expense_bhawna", "8.3 Dr Bhawna"),
         ("construction_accountant", "8.4 construction"))


def snap(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close(); s.close()


def main():
    a = sys.argv[1:]
    before, after, fin, adb, fdb, wd = a[:6]
    months = a[6:] or ["2026-08", "2026-09", "2026-10"]
    os.makedirs(os.path.join(wd, "finance"), exist_ok=True)
    try:
        for f in os.listdir(fin):
            fp = os.path.join(fin, f)
            if os.path.isfile(fp) and f.endswith((".py", ".html")) and ".bak" not in f and f != "packs.py":
                shutil.copy(fp, os.path.join(wd, "finance"))
        sys.path.insert(0, os.path.join(wd, "finance"))
        asnap, fsnap = os.path.join(wd, "assets_copy.db"), os.path.join(wd, "finance_copy.db")
        snap(adb, asnap); snap(fdb, fsnap)

        def load(path, name):
            shutil.copy(path, os.path.join(wd, "finance", name + ".py"))
            spec = importlib.util.spec_from_file_location(name, os.path.join(wd, "finance", name + ".py"))
            m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)

            def con():
                c = sqlite3.connect("file:%s?mode=ro" % asnap, uri=True); c.row_factory = sqlite3.Row; return c
            m._assets_con = con
            return m
        pb, pa = load(before, "packs_before_count"), load(after, "packs_after_count")
        book = sqlite3.connect("file:%s?mode=ro" % fsnap, uri=True)
        print("the accountants' bundles on a copy of the live data -- papers per bundle, before -> after S568 (counts only)")
        for mo in months:
            bits = []
            for lane, word in LANES:
                n0 = pb.build_bundle(book, mo, lane, count_only=True)[0] or 0
                n1 = pa.build_bundle(book, mo, lane, count_only=True)[0] or 0
                bits.append("%s %d -> %d%s" % (word, n0, n1, (" (%d out)" % (n0 - n1)) if n0 != n1 else ""))
            print("  %s: %s" % (mo, " · ".join(bits)))
        book.close()
    finally:
        shutil.rmtree(wd, ignore_errors=True)


if __name__ == "__main__":
    main()
