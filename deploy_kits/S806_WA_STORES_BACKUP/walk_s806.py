#!/usr/bin/env python3
"""walk_s806.py -- kit S806_WA_STORES_BACKUP (session 439, the parent, 12-Nov-2026), D939.
   python walk_s806.py <live clinic_state_backup.py> <kit clinic_state_backup.py>
Proves, on made-up files only (no real path is read or written):
  1  the kit's file is the live file plus TWO source lines, /root/portal/wa_ladder.db and /root/portal/callback_clock.db, at the
     end of SRC_FILES (nothing else differs);
  2  its gather() takes each as a WAL-mode store whose newest rows are still in the -wal file, through the online backup:
     the copy passes integrity_check and holds every row (a restore proof on a made-up root);
  3  a store missing from the box is reported as missing (the night's FATAL 41 guard is unchanged).
Exit 0 = WALK OK; 1 = RED. The control (the live file as both arguments) must go RED at check 1."""
import importlib.util, os, sqlite3, sys, tempfile

live, kit = sys.argv[1], sys.argv[2]
NEW = ["/root/portal/wa_ladder.db", "/root/portal/callback_clock.db"]
fails, oks = [], []


def ck(name, cond):
    (oks if cond else fails).append(name)
    print(("  ok   " if cond else "  FAIL ") + name)


def load(p, n):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


L = open(live, encoding="utf-8").read().splitlines()
K = open(kit, encoding="utf-8").read().splitlines()
added = [x for x in K if x not in L]
removed = [x for x in L if x not in K]
code_added = [x for x in added if not x.strip().startswith("#")]
ck("1a the kit adds exactly two code lines, the two stores", [x.strip() for x in code_added] == ['"%s",' % p for p in NEW])
ck("1b the kit removes nothing from the live file", removed == [])
mk = load(kit, "csb_kit")
ml = load(live, "csb_live")
ck("1c SRC_FILES = the live list + the two stores, at the end", mk.SRC_FILES == ml.SRC_FILES + NEW)
ck("1d SRC_DIRS / SRC_TREES / secret patterns unchanged",
   mk.SRC_DIRS == ml.SRC_DIRS and mk.SRC_TREES == ml.SRC_TREES and mk.SECRET_PATTERNS == ml.SECRET_PATTERNS)
ck("1e neither store's name is a secret by the job's own patterns", not any(mk.is_secret(os.path.basename(p)) for p in NEW))
names = [os.path.basename(x) for x in mk.SRC_FILES]
ck("1f neither basename collides with another source", all(names.count(os.path.basename(p)) == 1 for p in NEW))

# 2 -- two made-up WAL stores, their newest rows not yet checkpointed
t = tempfile.mkdtemp(prefix="s806w_")
srcs, keep = [], []
for base, table, n in (("wa_ladder.db", "optout", 40), ("callback_clock.db", "sent", 60)):
    src = os.path.join(t, "portal", base)
    os.makedirs(os.path.dirname(src), exist_ok=True)
    w = sqlite3.connect(src)
    w.execute("PRAGMA journal_mode=WAL")
    w.execute("PRAGMA wal_autocheckpoint=0")
    w.execute("CREATE TABLE %s (id INTEGER PRIMARY KEY, a TEXT)" % table)
    w.executemany("INSERT INTO %s (a) VALUES (?)" % table, [("made-up %d" % i,) for i in range(n)])
    w.commit()                   # left open: the rows live in the -wal file
    keep.append(w); srcs.append((src, base, table, n))
ck("2a both made-up stores are in WAL with their rows still in the -wal file",
   all(os.path.exists(s + "-wal") and os.path.getsize(s + "-wal") > 0 for s, _b, _t, _n in srcs))
mk.SRC_FILES = [s for s, _b, _t, _n in srcs]
mk.SRC_DIRS, mk.SRC_TREES = [], []
mk.log = lambda *a: None
dest = os.path.join(t, "out")
os.makedirs(dest)
g = mk.gather({}, dest)
ck("2b gather took both as present sources", all(s in g.sources_present for s, _b, _t, _n in srcs) and not g.sources_missing)
ck("2c both went through the integrity check ('ok')", all((s, "ok") in g.databases for s, _b, _t, _n in srcs))
good_i = good_n = good_s = True
for s, base, table, n in srcs:
    cp = os.path.join(dest, "data", base)
    r = sqlite3.connect("file:%s?mode=ro" % cp, uri=True) if os.path.isfile(cp) else None
    good_i = good_i and bool(r) and r.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    good_n = good_n and bool(r) and r.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0] == n
    good_s = good_s and os.path.isfile(os.path.join(dest, "shape", "schema", base + ".schema.sql"))
ck("2d each copy passes its own integrity_check", good_i)
ck("2e each copy holds every row, the -wal ones too", good_n)
ck("2f each schema was dumped beside it", good_s)
for w in keep:
    w.close()
# 2g -- the real two stores are in the default (rollback-journal) mode and one is written every 5 minutes: a store with a
#       writer in the middle of a transaction is copied sound, with its committed rows only
src3 = os.path.join(t, "portal2", "wa_ladder.db")
os.makedirs(os.path.dirname(src3))
w3 = sqlite3.connect(src3)
mode = w3.execute("PRAGMA journal_mode").fetchone()[0]
w3.execute("CREATE TABLE optout (id INTEGER PRIMARY KEY, a TEXT)")
w3.executemany("INSERT INTO optout (a) VALUES (?)", [("made-up %d" % i,) for i in range(30)])
w3.commit()
w3.execute("INSERT INTO optout (a) VALUES ('not committed')")       # a transaction left open
ck("2g a third made-up store is in the default journal mode with a write in progress", mode in ("delete", "DELETE") and w3.in_transaction)
mk.SRC_FILES = [src3]
dest3 = os.path.join(t, "out3")
os.makedirs(dest3)
g3 = mk.gather({}, dest3)
cp3 = os.path.join(dest3, "data", "wa_ladder.db")
r3 = sqlite3.connect("file:%s?mode=ro" % cp3, uri=True) if os.path.isfile(cp3) else None
ck("2h it is taken as present and passes the integrity check", src3 in g3.sources_present and (src3, "ok") in g3.databases)
ck("2i its copy is sound and holds the committed rows only (30)", bool(r3) and r3.execute("PRAGMA integrity_check").fetchone()[0] == "ok" and r3.execute("SELECT COUNT(*) FROM optout").fetchone()[0] == 30)
w3.rollback(); w3.close()
ck("2j the writer was not disturbed (its store still opens and holds 30 rows)", sqlite3.connect(src3).execute("SELECT COUNT(*) FROM optout").fetchone()[0] == 30)
# 3 -- missing on the box
mk.SRC_FILES = [os.path.join(t, "nowhere", "wa_ladder.db")]
dest2 = os.path.join(t, "out2")
os.makedirs(dest2)
g2 = mk.gather({}, dest2)
ck("3a a missing store is named missing (FATAL 41 then refuses the night, as before)", g2.sources_missing == mk.SRC_FILES)
print("WALK OK %d/%d" % (len(oks), len(oks) + len(fails)) if not fails else "WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails)))
sys.exit(1 if fails else 0)
