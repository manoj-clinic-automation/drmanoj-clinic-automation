#!/usr/bin/env python3
"""walk_s445.py -- walk for S445_RING_OUTCOMES_BACKUP.
usage: walk_s445.py <original (S429)> <patched copy> [<a real ring_outcomes.db>]
Proves: the only change is the one SRC_FILES line; the file compiles and loads; the new name collides with no other
SRC_FILES basename; and the patched file's OWN gather() takes the database through the sqlite online-backup with
integrity 'ok', every table's row count equal to the source. With a third argument (on the box: the live
/root/portal/ring_outcomes.db) that last proof runs on the REAL database, read-only; without it, on a fake one.
No network, no key, no Drive, no crontab. Prints WALK OK n/n."""
import importlib.util
import os
import shutil
import sqlite3
import sys
import tempfile

ORIG, NEW = sys.argv[1], sys.argv[2]
REAL = sys.argv[3] if len(sys.argv) > 3 else None
o = open(ORIG, encoding="utf-8").read()
s = open(NEW, encoding="utf-8").read()
N = [0, 0]


def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1
        print("  ok  %s" % name)
    else:
        print("  RED %s %s" % (name, extra))


A = '    "/root/finance/spine/spine.db",\n'
i = o.index(A) + len(A)
added = s[i:len(s) - (len(o) - i)]
check("before and after the insertion the file is the original byte for byte",
      s[:i] == o[:i] and s[i + len(added):] == o[i:])
check("the insertion is two comment lines and the one path",
      added.count("\n") == 3 and added.rstrip().endswith('"/root/portal/ring_outcomes.db",'))
compile(s, NEW, "exec")
check("compiles", True)
spec = importlib.util.spec_from_file_location("csb_s445", NEW)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
check("loads", True)
check("ring_outcomes.db is in SRC_FILES exactly once", m.SRC_FILES.count("/root/portal/ring_outcomes.db") == 1)
bn = [os.path.basename(p) for p in m.SRC_FILES]
check("no other SRC_FILES entry shares its basename (data/ring_outcomes.db cannot collide)", len(bn) == len(set(bn)))
check("the six earlier SRC_FILES entries are unchanged and in order",
      m.SRC_FILES[:-1] == ["/root/wa/console.db", "/root/assetapp/assets.db", "/root/punches.csv",
                           "/root/punches_raw.log", "/root/staff_master.csv", "/root/finance/spine/spine.db"])
check("not taken for a secret by the file's own patterns", not m.is_secret("ring_outcomes.db"))

tmp = tempfile.mkdtemp(prefix="walk_s445_")
try:
    if REAL:
        src = REAL
        label = "the REAL database (read-only)"
    else:
        src = os.path.join(tmp, "ring_outcomes.db")
        c = sqlite3.connect(src)
        c.execute("create table calls (session text primary key, answered_by text, outcome text)")
        c.executemany("insert into calls values (?,?,?)", [("s%d" % k, "r", "k_coming") for k in range(25)])
        c.execute("create table mirror_queue (id integer primary key, payload text)")
        c.commit(); c.close()
        label = "a fake database"
    m.SRC_FILES = [src]
    m.SRC_DIRS = []
    m.SRC_TREES = []
    m._gather_shape = lambda conf, shape_dir, g: None
    m._write_inventory = lambda dest_root, g: None
    stage = os.path.join(tmp, "stage")
    os.makedirs(stage)
    g = m.gather({}, stage)
    out = os.path.join(stage, "data", os.path.basename(src))
    check("gather() took %s as data/%s" % (label, os.path.basename(src)), os.path.isfile(out) and g.sources_missing == [])
    check("integrity_check said ok", g.databases == [(src, "ok")], repr(g.databases))
    check("the copy is a sqlite database (online backup, not a byte copy)", m.is_sqlite(out))
    a = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    b = sqlite3.connect("file:%s?mode=ro" % out, uri=True)
    ta = [r[0] for r in a.execute("select name from sqlite_master where type='table' order by name")]
    tb = [r[0] for r in b.execute("select name from sqlite_master where type='table' order by name")]
    check("the same tables (%d)" % len(ta), ta == tb and len(ta) > 0)
    same = all(a.execute('select count(*) from "%s"' % t).fetchone() == b.execute('select count(*) from "%s"' % t).fetchone() for t in ta)
    total = sum(a.execute('select count(*) from "%s"' % t).fetchone()[0] for t in ta)
    check("every table's row count equal (%d rows in all)" % total, same)
    a.close(); b.close()
    check("a schema dump was written beside it", os.path.isfile(os.path.join(stage, "shape", "schema", os.path.basename(src) + ".schema.sql")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
