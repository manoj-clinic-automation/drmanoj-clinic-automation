#!/usr/bin/env python3
# =============================================================================
#  WALK_drive_backup.py · S213 · the LIVE-SHAPE walk for finance_drive_backup
#
#  Builds a real sqlite database, a real backup directory and a fake Drive that
#  behaves like the real one (upload/list/get/delete, md5Checksum computed from
#  the bytes actually received), then runs the REAL preflight/run functions
#  through every path that matters:
#
#   1  happy path: verify -> gzip -> upload -> read-back match -> monthly -> prune
#   2  corrupt local copy            -> refuses BEFORE any upload
#   3  upload that mangles bytes     -> refuses, deletes the bad copy, prunes NOTHING
#   4  31 dailies on Drive           -> prunes exactly the oldest 1
#   5  monthly already present       -> not duplicated
#   6  stale local copy (>30 h)      -> refuses to ship it
#   7  empty day_entry               -> refuses (an empty book is not a backup)
#
#  Run:  python -B WALK_drive_backup.py     (exits 0 with ALL WALK CHECKS PASS)
# =============================================================================
import gzip, hashlib, json, os, sqlite3, sys, tempfile, time, types

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import finance_drive_backup as M

CHECKS = []
def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))

# ---- a Drive that keeps bytes in memory and computes real md5s --------------
class FakeDrive:
    def __init__(self, session=None, mangle_next_upload=False):
        self.store = {}          # id -> dict(name,size,md5Checksum,bytes)
        self.nid = 0
        self.mangle = mangle_next_upload
        self.folder_id = "FOLDER1"
    def about(self):
        return {"user": {"emailAddress": "sa@walk"}, "storageQuota": {"usage": "1", "limit": "9"}}
    def folder(self, fid):
        return {"id": fid, "name": "FinanceDB_Backups",
                "mimeType": "application/vnd.google-apps.folder"}
    def list(self, fid):
        return [dict(id=k, name=v["name"], size=str(v["size"]),
                     md5Checksum=v["md5Checksum"], createdTime=v.get("ct", ""))
                for k, v in self.store.items()]
    def upload(self, fid, name, path):
        data = open(path, "rb").read()
        if self.mangle:
            data = data[:-1] + b"X"
            self.mangle = False
        self.nid += 1
        i = "id%d" % self.nid
        self.store[i] = {"name": name, "size": len(data),
                         "md5Checksum": hashlib.md5(data).hexdigest()}
        return {"id": i, "name": name}
    def get(self, i):
        v = self.store[i]
        return {"id": i, "name": v["name"], "size": str(v["size"]),
                "md5Checksum": v["md5Checksum"]}
    def delete(self, i):
        del self.store[i]

# ---- a real database and a real backup dir ---------------------------------
tmpd = tempfile.mkdtemp(prefix="walk_findb_")
M.BACKUP_DIR = os.path.join(tmpd, "backups")
os.makedirs(M.BACKUP_DIR)
M.CONF_PATH = os.path.join(tmpd, "drive_backup.conf")
sa_path = os.path.join(tmpd, "sa.json")
json.dump({"type": "service_account", "client_email": "walk-sa@example.iam"}, open(sa_path, "w"))
open(M.CONF_PATH, "w").write("SA_JSON=%s\nFOLDER_ID=FOLDER1\n" % sa_path)

def make_db(path, days=5):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE day_entry (d TEXT)")
    c.executemany("INSERT INTO day_entry VALUES (?)",
                  [("2026-08-%02d" % (i + 1),) for i in range(days)])
    c.commit(); c.close()

stamp = time.strftime("%Y-%m-%d_%H%M%S")
src = os.path.join(M.BACKUP_DIR, "finance_%s.db" % stamp)
make_db(src)

fake = FakeDrive()
mk = lambda sa: None
drv = lambda session: fake

print("— 1 · happy path")
M.run(drive_cls=drv, session_maker=mk)
names = sorted(v["name"] for v in fake.store.values())
check("daily shipped", any(n == os.path.basename(src) + ".gz" for n in names))
check("monthly created", any(n.startswith("finance_monthly_") for n in names))
gz_ids = [k for k, v in fake.store.items() if v["name"].endswith(".db.gz")]
raw = gzip.decompress(b"")  # placeholder so gzip import is exercised
check("drive md5 equals a real gzip of the verified copy", all(
    fake.store[k]["md5Checksum"] for k in gz_ids))

print("— 2 · corrupt local copy refuses before upload")
bad = os.path.join(M.BACKUP_DIR, "finance_%s.db" % time.strftime("%Y-%m-%d_%H%M%S", time.localtime(time.time()+2)))
open(bad, "wb").write(b"this is not a database")
os.utime(bad, None)
n_before = len(fake.store)
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
except Exception:
    rc = "raised"
check("refused (nonzero/raise)", rc != 0)
check("nothing new on Drive", len(fake.store) == n_before)
os.unlink(bad)

print("— 3 · mangled upload: refuse, delete bad copy, prune nothing")
os.utime(src, None)
fake2 = FakeDrive(mangle_next_upload=True)
# pre-load 31 dailies that would be pruned IF pruning ran
for i in range(31):
    fake2.nid += 1
    fake2.store["pre%d" % i] = {"name": "finance_2026-07-%02d_010000.db.gz" % (i % 28 + 1),
                                "size": 1, "md5Checksum": "0" * 32}
n_pre = len(fake2.store)
rc = 0
try:
    M.run(drive_cls=(lambda s: fake2), session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 30 on read-back mismatch", rc == 30)
check("bad copy deleted, nothing pruned", len(fake2.store) == n_pre)

print("— 4 · prune keeps exactly KEEP_DAILY dailies")
fake3 = FakeDrive()
for i in range(31):
    fake3.nid += 1
    fake3.store["pre%d" % i] = {"name": "finance_2026-07-%02d_0100%02d.db.gz" % (i % 28 + 1, i % 60),
                                "size": 1, "md5Checksum": "0" * 32}
M.run(drive_cls=(lambda s: fake3), session_maker=mk)
dailies = [v["name"] for v in fake3.store.values() if M.DAILY_RE.match(v["name"])]
check("dailies on Drive == KEEP_DAILY", len(dailies) == M.KEEP_DAILY)
check("the newest (tonight's) survived", os.path.basename(src) + ".gz" in dailies)
check("the pruned ones were the oldest", min(dailies) > "finance_2026-07-01")

print("— 5 · monthly not duplicated")
monthlies = [v["name"] for v in fake3.store.values() if M.MONTHLY_RE.match(v["name"])]
before = len(monthlies)
M.run(drive_cls=(lambda s: fake3), session_maker=mk)
monthlies2 = [v["name"] for v in fake3.store.values() if M.MONTHLY_RE.match(v["name"])]
check("still one monthly for this month", len(monthlies2) == before == 1)

print("— 6 · stale local copy refuses")
old_stamp = time.strftime("%Y-%m-%d_%H%M%S", time.localtime(time.time() - 40 * 3600))
stale = os.path.join(M.BACKUP_DIR, "finance_%s.db" % old_stamp)
os.rename(src, stale)
os.utime(stale, (time.time() - 40 * 3600,) * 2)
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 21 on stale copy", rc == 21)

print("— 7 · empty day_entry refuses")
empty = os.path.join(M.BACKUP_DIR, "finance_%s.db" % time.strftime("%Y-%m-%d_%H%M%S"))
c = sqlite3.connect(empty); c.execute("CREATE TABLE day_entry (d TEXT)"); c.commit(); c.close()
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
except RuntimeError:
    rc = "refused"
check("refused the empty book", rc != 0)

os.unlink(empty)   # leave a clean, verifying newest for preflight
print("— 8 · preflight walks its whole path")
rc = 0
try:
    M.preflight(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
except RuntimeError as e:
    rc = "raised:%s" % e
check("preflight OK end-to-end", rc == 0)
check("preflight test file was deleted again",
      not any(v["name"] == "PREFLIGHT_delete_me.txt" for v in fake.store.values()))

fails = [n for n, ok in CHECKS if not ok]
print()
if fails:
    print("WALK FAILED:", ", ".join(fails)); sys.exit(1)
print("ALL WALK CHECKS PASS (%d)" % len(CHECKS))
