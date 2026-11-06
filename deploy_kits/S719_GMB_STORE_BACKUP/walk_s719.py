#!/usr/bin/env python3
"""walk_s719.py -- kit S719 (session 390, the parent, 06-Nov-2026), F-1129.
   python walk_s719.py <live clinic_state_backup.py> <kit clinic_state_backup.py>
Proves, on made-up files only (no real path is read or written):
  1  the kit's file is the live file plus ONE source line, /root/portal/gmb_store.db, in SRC_FILES (nothing else differs);
  2  its gather() takes a WAL-mode store whose newest rows are still in the -wal file, through the online backup:
     the copy passes integrity_check and holds every row (a restore proof on a made-up root);
  3  a store missing from the box is reported as missing (the night's FATAL 41 guard is unchanged).
Exit 0 = WALK OK; 1 = RED. The control (live file as both arguments) must go RED at check 1."""
import importlib.util, os, sqlite3, sys, tempfile

live, kit = sys.argv[1], sys.argv[2]
LINE = '"/root/portal/gmb_store.db"'
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
ck("1a the kit adds exactly one code line, the GMB store", [x.strip() for x in code_added] == [LINE + ","])
ck("1b the kit removes nothing from the live file", removed == [])
mk = load(kit, "csb_kit")
ml = load(live, "csb_live")
ck("1c SRC_FILES = the live list + /root/portal/gmb_store.db, at the end",
   mk.SRC_FILES == ml.SRC_FILES + ["/root/portal/gmb_store.db"])
ck("1d SRC_DIRS / SRC_TREES / secret patterns unchanged",
   mk.SRC_DIRS == ml.SRC_DIRS and mk.SRC_TREES == ml.SRC_TREES and mk.SECRET_PATTERNS == ml.SECRET_PATTERNS)
ck("1e the GMB store's name is not a secret by the job's own patterns", not mk.is_secret("gmb_store.db"))
ck("1f its basename collides with no other source", [os.path.basename(x) for x in mk.SRC_FILES].count("gmb_store.db") == 1)

# 2 -- a made-up WAL store, its newest rows not yet checkpointed
t = tempfile.mkdtemp(prefix="s719w_")
src = os.path.join(t, "portal", "gmb_store.db")
os.makedirs(os.path.dirname(src))
w = sqlite3.connect(src)
w.execute("PRAGMA journal_mode=WAL")
w.execute("PRAGMA wal_autocheckpoint=0")
w.execute("CREATE TABLE press (id INTEGER PRIMARY KEY, lang TEXT, drafts TEXT)")
w.executemany("INSERT INTO press (lang, drafts) VALUES (?,?)", [("hi", "draft %d" % i) for i in range(250)])
w.commit()                       # left open: the rows live in the -wal file
ck("2a the made-up store is in WAL with its rows still in the -wal file",
   os.path.exists(src + "-wal") and os.path.getsize(src + "-wal") > 0)
mk.SRC_FILES = [src]
mk.SRC_DIRS, mk.SRC_TREES = [], []
mk.log = lambda *a: None
dest = os.path.join(t, "out")
os.makedirs(dest)
g = mk.gather({}, dest)
cp = os.path.join(dest, "data", "gmb_store.db")
ck("2b gather took it as a present source", src in g.sources_present and not g.sources_missing)
ck("2c it went through the integrity check ('ok')", (src, "ok") in g.databases)
ok = os.path.isfile(cp)
r = sqlite3.connect("file:%s?mode=ro" % cp, uri=True) if ok else None
ck("2d the copy passes its own integrity_check", bool(r) and r.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
ck("2e the copy holds every row, the -wal ones too (250)", bool(r) and r.execute("SELECT COUNT(*) FROM press").fetchone()[0] == 250)
ck("2f its schema was dumped beside it", os.path.isfile(os.path.join(dest, "shape", "schema", "gmb_store.db.schema.sql")))
w.close()
# 3 -- missing on the box
mk.SRC_FILES = [os.path.join(t, "nowhere", "gmb_store.db")]
dest2 = os.path.join(t, "out2")
os.makedirs(dest2)
g2 = mk.gather({}, dest2)
ck("3a a missing store is named missing (FATAL 41 then refuses the night, as before)", g2.sources_missing == mk.SRC_FILES)
print("WALK OK %d/%d" % (len(oks), len(oks) + len(fails)) if not fails else "WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails)))
sys.exit(1 if fails else 0)
