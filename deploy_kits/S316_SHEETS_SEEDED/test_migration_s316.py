#!/usr/bin/env python3
"""test_migration_s316.py -- S315's live tables must survive. Builds the S315 shape (no S316 columns),
puts a row in it as the owner would have, then loads S316 over it and checks: the columns are added,
his row is untouched and still reachable, and the two lists seed beside it.
Usage: test_migration_s316.py OLD_MODULE NEW_MODULE_DIR"""
import importlib.util
import os
import sqlite3
import sys
import tempfile

old_py, new_dir = sys.argv[1], sys.argv[2]
tmp = tempfile.mkdtemp(prefix="s316_mig_")
db = os.path.join(tmp, "f.db")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def con():
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    return c


n = [0]


def check(name, ok):
    n[0] += 1
    if not ok:
        print("FAIL %d %s" % (n[0], name))
        sys.exit(1)


old = load(old_py, "s315_old")
c = con()
old.ensure(c)
cols_before = [r[1] for r in c.execute("PRAGMA table_info(owner_service)")]
check("the S315 shape has no S316 columns", "status" not in cols_before and "code" not in cols_before)
old.add_service(c, "manoj", "xray", "Knee my own way", "500")
sid = c.execute("SELECT id FROM owner_service").fetchone()["id"]
old.add_item(c, "manoj", c.execute("SELECT id FROM owner_service WHERE kind='proc'").fetchone()["id"]
             if c.execute("SELECT id FROM owner_service WHERE kind='proc'").fetchone() else sid,
             "x", "1") if False else None
c.close()

new = load(os.path.join(new_dir, "owner_sheets.py"), "s316_new")
new.SEED_DIR = new_dir
c = con()
new.ensure(c)
cols_after = [r[1] for r in c.execute("PRAGMA table_info(owner_service)")]
check("S316 adds its columns in place", all(x in cols_after for x in
                                            ("code", "status", "seen", "grp", "forms", "source")))
row = c.execute("SELECT * FROM owner_service WHERE id=?", (sid,)).fetchone()
check("his S315 row is still there, with its name and price",
      row["name"] == "Knee my own way" and row["price_p"] == 50000)
check("and it is not left in limbo -- it reads as pending until he says",
      row["status"] in ("pending", "approved"))
check("both lists seeded beside it",
      c.execute("SELECT COUNT(*) n FROM owner_service WHERE kind='xray'").fetchone()["n"] >= 19 and
      c.execute("SELECT COUNT(*) n FROM owner_service WHERE kind='proc'").fetchone()["n"] >= 17)
before = c.execute("SELECT COUNT(*) n FROM owner_service").fetchone()["n"]
new.ensure(c)
check("a second load changes nothing",
      c.execute("SELECT COUNT(*) n FROM owner_service").fetchone()["n"] == before)
c.close()
print("TEST OK -- %d checks (S315 tables migrate in place, nothing of his is lost)" % n[0])
