#!/usr/bin/env python3
# =============================================================================
#  WALK_drive_backup.py · S213 · the LIVE-SHAPE walk for finance_drive_backup v2
#
#  v2 walks the UPDATE-IN-PLACE design (the live box proved on 31-Aug-2026 that
#  service accounts have zero storage quota, so the job now overwrites two
#  owner-owned slot files instead of creating its own).
#
#  A real sqlite database, a real backup dir, and a fake Drive that stores the
#  bytes it actually receives, md5s them itself, and keeps a revision list per
#  file. The REAL preflight/run functions are then driven through:
#
#   1  happy path: verify -> gzip -> update nightly -> read-back match ->
#      description stamped -> monthly updated AND PINNED (first run of month)
#   2  corrupt local copy      -> refuses BEFORE any network call
#   3  mangled nightly update  -> exit 30, monthly untouched
#   4  slot files missing      -> exit 13, names them
#   5  second run same month   -> nightly gains a revision, monthly does NOT
#   6  stale local copy (>30h) -> exit 21
#   7  empty day_entry         -> refuses
#   8  preflight               -> end-to-end OK, and content NOT touched
#
#  Run:  python -B WALK_drive_backup.py     (exits 0 with ALL WALK CHECKS PASS)
# =============================================================================
import gzip, hashlib, json, os, sqlite3, sys, tempfile, time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import finance_drive_backup as M

CHECKS = []
def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))

class FakeDrive:
    """Owner-owned slot files with content, revisions and descriptions."""
    def __init__(self, session=None):
        self.files = {}      # id -> {name,bytes,description,revisions:[{id,keepForever}]}
        self.calls = 0
        self.mangle_next = False
        self.folder_id = "FOLDER1"
    def _f(self, i): return self.files[i]
    def seed(self, i, name):
        self.files[i] = {"name": name, "bytes": b"placeholder", "description": "",
                         "revisions": [{"id": "r0", "keepForever": False}]}
    def about(self):
        self.calls += 1
        return {"user": {"emailAddress": "sa@walk"}}
    def folder(self, fid):
        self.calls += 1
        return {"id": fid, "name": "FinanceDB_Backups",
                "mimeType": "application/vnd.google-apps.folder"}
    def list(self, fid):
        self.calls += 1
        return [{"id": k, "name": v["name"], "size": str(len(v["bytes"])),
                 "md5Checksum": hashlib.md5(v["bytes"]).hexdigest(),
                 "description": v["description"]} for k, v in self.files.items()]
    def update_content(self, i, path):
        self.calls += 1
        data = open(path, "rb").read()
        if self.mangle_next:
            data = data[:-1] + b"X"
            self.mangle_next = False
        f = self._f(i)
        f["bytes"] = data
        f["revisions"].append({"id": "r%d" % len(f["revisions"]), "keepForever": False})
        return {"id": i}
    def patch_meta(self, i, body):
        self.calls += 1
        self._f(i)["description"] = body.get("description", self._f(i)["description"])
        return {"id": i}
    def get(self, i):
        self.calls += 1
        v = self._f(i)
        return {"id": i, "name": v["name"], "size": str(len(v["bytes"])),
                "md5Checksum": hashlib.md5(v["bytes"]).hexdigest(),
                "description": v["description"]}
    def revisions(self, i):
        self.calls += 1
        return list(self._f(i)["revisions"])
    def pin_revision(self, i, rid):
        self.calls += 1
        for r in self._f(i)["revisions"]:
            if r["id"] == rid:
                r["keepForever"] = True
                return
        raise RuntimeError("no such revision")

# ---- a real database and a real backup dir ---------------------------------
tmpd = tempfile.mkdtemp(prefix="walk_findb_")
M.BACKUP_DIR = os.path.join(tmpd, "backups")
os.makedirs(M.BACKUP_DIR)
M.CONF_PATH = os.path.join(tmpd, "drive_backup.conf")
sa_path = os.path.join(tmpd, "sa.json")
json.dump({"type": "service_account", "client_email": "walk-sa@example.iam"}, open(sa_path, "w"))
open(M.CONF_PATH, "w").write("SA_JSON=%s\nFOLDER_ID=FOLDER1\n" % sa_path)
M.SA_SEARCH = [sa_path]

def make_db(path, days=5):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE day_entry (d TEXT)")
    c.executemany("INSERT INTO day_entry VALUES (?)",
                  [("2026-08-%02d" % (i + 1),) for i in range(days)])
    c.commit(); c.close()

src = os.path.join(M.BACKUP_DIR, "finance_%s.db" % time.strftime("%Y-%m-%d_%H%M%S"))
make_db(src)

fake = FakeDrive()
fake.seed("N1", M.NIGHTLY)
fake.seed("M1", M.MONTHLY)
mk = lambda sa: None
drv = lambda session: fake

print("— 1 · happy path (first run of the month)")
M.run(drive_cls=drv, session_maker=mk)
exp_md5 = hashlib.md5(fake.files["N1"]["bytes"]).hexdigest()
real_gz_md5 = None
with open(src, "rb") as fi:
    raw = fi.read()
check("nightly holds a gzip of the verified db",
      gzip.decompress(fake.files["N1"]["bytes"]) == raw)
check("monthly holds the same bytes",
      fake.files["M1"]["bytes"] == fake.files["N1"]["bytes"])
check("nightly description stamped", "verified backup" in fake.files["N1"]["description"])
check("monthly head revision pinned",
      fake.files["M1"]["revisions"][-1]["keepForever"] is True)
check("monthly description carries month tag",
      "month=%s" % time.strftime("%Y-%m") in fake.files["M1"]["description"])

print("— 2 · corrupt local copy refuses before any network call")
bad = os.path.join(M.BACKUP_DIR, "finance_bad.db")
open(bad, "wb").write(b"this is not a database")
calls_before = fake.calls
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
except Exception:
    rc = "raised"
check("refused", rc != 0)
check("zero Drive calls made", fake.calls == calls_before)
os.unlink(bad)

print("— 3 · mangled nightly update: exit 30, monthly untouched")
os.utime(src, None)
fake2 = FakeDrive(); fake2.seed("N1", M.NIGHTLY); fake2.seed("M1", M.MONTHLY)
fake2.mangle_next = True
m_bytes_before = fake2.files["M1"]["bytes"]
rc = 0
try:
    M.run(drive_cls=(lambda s: fake2), session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 30 on read-back mismatch", rc == 30)
check("monthly untouched", fake2.files["M1"]["bytes"] == m_bytes_before)
check("nightly description NOT stamped", fake2.files["N1"]["description"] == "")

print("— 4 · slot files missing: exit 13")
fake3 = FakeDrive()   # empty folder
rc = 0
try:
    M.run(drive_cls=(lambda s: fake3), session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 13 when slots absent", rc == 13)

print("— 5 · second run, same month: nightly revises, monthly does not")
n_rev = len(fake.files["N1"]["revisions"])
m_rev = len(fake.files["M1"]["revisions"])
os.utime(src, None)
M.run(drive_cls=drv, session_maker=mk)
check("nightly gained a revision", len(fake.files["N1"]["revisions"]) == n_rev + 1)
check("monthly did not", len(fake.files["M1"]["revisions"]) == m_rev)

print("— 6 · stale local copy refuses")
stale_t = time.time() - 40 * 3600
os.utime(src, (stale_t, stale_t))
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 21 on stale copy", rc == 21)

print("— 7 · empty day_entry refuses")
empty = os.path.join(M.BACKUP_DIR, "finance_empty.db")
c = sqlite3.connect(empty); c.execute("CREATE TABLE day_entry (d TEXT)"); c.commit(); c.close()
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
except RuntimeError:
    rc = "refused"
check("refused the empty book", rc != 0)
os.unlink(empty)

print("— 8 · preflight end-to-end, content untouched")
os.utime(src, None)
n_bytes = fake.files["N1"]["bytes"]
n_revs = len(fake.files["N1"]["revisions"])
rc = 0
try:
    M.preflight(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
except RuntimeError as e:
    rc = "raised:%s" % e
check("preflight OK end-to-end", rc == 0)
check("nightly content untouched by preflight",
      fake.files["N1"]["bytes"] == n_bytes and len(fake.files["N1"]["revisions"]) == n_revs)
check("write proven via description", "preflight write-test" in fake.files["N1"]["description"])

fails = [n for n, ok in CHECKS if not ok]
print()
if fails:
    print("WALK FAILED:", ", ".join(fails)); sys.exit(1)
print("ALL WALK CHECKS PASS (%d)" % len(CHECKS))
