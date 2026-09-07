#!/usr/bin/env python3
# =============================================================================
#  WALK_restore_verify.py · S230 · the LIVE-SHAPE walk for verify_restore.py
#
#  A REAL sqlite database, really gzipped, served by a fake Drive that hands
#  back the actual bytes and md5s them itself — so the md5 check, the gunzip
#  and PRAGMA integrity_check are all doing real work here, on real files.
#  No network, no /root path, nothing outside one temp directory.
#
#   1  happy path: download -> md5 -> gunzip -> open -> count -> verdict
#   2  the state file: every field, and the ISO stamp that gives a
#      verification its age
#   3  --keep leaves the restored db; the default deletes both temp files
#   4  md5 mismatch                      -> exit 30
#   5  zero-byte and truncated downloads -> exit 30
#   6  corrupt gzip, mid-stream and CRC  -> exit 31   (the never-run check)
#   7  a malformed database              -> exit 32
#   8  an empty day_entry                -> exit 32
#   9  description parsing, with and without a count
#  10  a description that disagrees      -> WARNS, still passes
#  11  deletion happens on failure paths too
#  12  slot missing 13 · no SA 10 · no FOLDER_ID 11 · unreachable 20
#  13  monthly mode reads the monthly slot
#  14  the script cannot write to Drive at all — there is no such call in it
#
#  Run:  python -B WALK_restore_verify.py     (prints "N checks, 0 failures")
# =============================================================================
import contextlib
import gzip
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify_restore as M

CHECKS = []


def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))


# ----------------------------------------------------------- fake drive ----
class FakeDrive:
    """Serves real bytes. Read-only on purpose: it has no update, no patch and
    no pin, so any attempt by the script to write would blow up here."""

    def __init__(self, blobs):
        self.files = {}
        self.downloads = 0
        self.truncate = 0
        self.lie_md5 = None
        self.lie_size = None
        for i, (name, data) in enumerate(blobs.items()):
            self.files["ID%d" % i] = {"name": name, "bytes": data, "description": ""}

    def _meta(self, fid):
        v = self.files[fid]
        return {"id": fid, "name": v["name"],
                "size": self.lie_size if self.lie_size is not None else str(len(v["bytes"])),
                "md5Checksum": self.lie_md5 or hashlib.md5(v["bytes"]).hexdigest(),
                "description": v["description"]}

    def set_desc(self, name, desc):
        for fid, v in self.files.items():
            if v["name"] == name:
                v["description"] = desc

    def list(self, folder_id):
        return [self._meta(f) for f in self.files]

    def get(self, fid):
        return self._meta(fid)

    def download(self, fid, dest):
        self.downloads += 1
        data = self.files[fid]["bytes"]
        if self.truncate:
            data = data[:-self.truncate]
        with open(dest, "wb") as fh:
            fh.write(data)
        return len(data)


def run(slot=None, keep=False, drive=None):
    """Drive the real verify() and capture what it printed and how it exited."""
    buf = io.StringIO()
    rc = 0
    try:
        with contextlib.redirect_stdout(buf):
            rc = M.verify(slot=slot or M.NIGHTLY, keep=keep,
                          drive_cls=(lambda s: drive), session_maker=(lambda p: None))
    except SystemExit as e:
        rc = e.code
    return rc, buf.getvalue()


# ------------------------------------------------------------- fixtures ----
tmpd = tempfile.mkdtemp(prefix="walk_restore_")
WORK = os.path.join(tmpd, "work")
os.makedirs(WORK)
M.CONF_PATH = os.path.join(tmpd, "drive_backup.conf")
sa_path = os.path.join(tmpd, "sa.json")
json.dump({"type": "service_account", "client_email": "walk-sa@example.iam"},
          open(sa_path, "w"))
STATE = os.path.join(tmpd, "verify.state.json")
CONF_GOOD = ("SA_JSON=%s\nFOLDER_ID=FOLDER1\nWORK_DIR=%s\nVERIFY_STATE_FILE=%s\n"
             % (sa_path, WORK, STATE))
open(M.CONF_PATH, "w").write(CONF_GOOD)


def make_db(path, days=7, items=400, drop_day_entry=False):
    c = sqlite3.connect(path)
    if not drop_day_entry:
        c.execute("CREATE TABLE day_entry (d TEXT, note TEXT)")
        c.executemany("INSERT INTO day_entry VALUES (?,?)",
                      [("2026-09-%02d" % (i + 1), "x" * 40) for i in range(days)])
    c.execute("CREATE TABLE item_line (id INTEGER, name TEXT)")
    c.executemany("INSERT INTO item_line VALUES (?,?)",
                  [(i, "item-%d" % i) for i in range(items)])
    c.execute("CREATE TABLE ledger (id INTEGER)")
    c.executemany("INSERT INTO ledger VALUES (?)", [(i,) for i in range(items // 2)])
    c.execute("CREATE TABLE empty_table (x TEXT)")
    c.commit()
    c.close()


def gz_of(path):
    raw = open(path, "rb").read()
    b = io.BytesIO()
    with gzip.GzipFile(fileobj=b, mode="wb", compresslevel=6, mtime=0) as fo:
        fo.write(raw)
    return b.getvalue()


DB = os.path.join(tmpd, "finance.db")
make_db(DB)
GOOD_GZ = gz_of(DB)
DB_BYTES = os.path.getsize(DB)


def leftovers():
    return sorted(n for n in os.listdir(WORK) if n.startswith("restore_verify_"))


def state():
    return json.load(open(STATE))


# ------------------------------------------------------------------ 1-2 ----
print("- 1 · happy path, nightly")
fake = FakeDrive({M.NIGHTLY: GOOD_GZ, M.MONTHLY: GOOD_GZ})
fake.set_desc(M.NIGHTLY, "verified backup of finance_2026-09-07.db · md5 %s ·"
              " 7 day-entries · shipped 2026-09-07 01:40:11"
              % hashlib.md5(GOOD_GZ).hexdigest())
rc, out = run(drive=fake)
check("happy path exits 0", rc == 0)
check("it actually downloaded", fake.downloads == 1)
check("verdict line printed", "RESTORE VERIFY PASS" in out)
check("verdict names the slot", M.NIGHTLY in out)
check("verdict reports 4 tables", "4 tables" in out)
check("verdict reports 7 day-entries", "7 day-entries" in out)
check("verdict reports the decompressed size", "%d bytes" % DB_BYTES in out)
check("integrity_check reported ok", "integrity_check: ok" in out)
check("largest tables listed", "item_line" in out and "ledger" in out)
check("gunzip stage says the CRC was ok", "CRC ok" in out)
check("no WARNING on a matching description", "WARNING" not in out)

print("- 2 · the state file")
st = state()
check("state result PASS", st["result"] == "PASS")
check("state slot is the nightly", st["slot"] == M.NIGHTLY)
check("state tables == 4", st["tables"] == 4)
check("state day_entries == 7", st["day_entries"] == 7)
check("state bytes == the decompressed size", st["bytes"] == DB_BYTES)
check("state gz_md5 == md5 of the served bytes",
      st["gz_md5"] == hashlib.md5(GOOD_GZ).hexdigest())
check("state carries an ISO timestamp — a verification can state its age",
      isinstance(st.get("last_verify_iso"), str) and
      st["last_verify_iso"][:2] == "20" and "T" in st["last_verify_iso"])
check("state has exactly the seven agreed keys",
      set(st) == {"last_verify_iso", "slot", "result", "tables", "day_entries",
                  "bytes", "gz_md5"})

print("- 3 · --keep versus delete")
check("default run left nothing behind", leftovers() == [])
rc, out = run(drive=fake, keep=True)
kept = leftovers()
check("--keep exits 0", rc == 0)
check("--keep leaves the archive and the restored db", len(kept) == 2)
check("--keep leaves a .db to look at", any(n.endswith(".db") for n in kept))
check("--keep says so", "kept:" in out)
for n in kept:
    os.unlink(os.path.join(WORK, n))

# -------------------------------------------------------------------- 4 ----
print("- 4 · md5 mismatch")
bad = FakeDrive({M.NIGHTLY: GOOD_GZ})
bad.lie_md5 = "0" * 32
rc, out = run(drive=bad)
check("md5 mismatch exits 30", rc == 30)
check("it says the download did not verify", "DID NOT VERIFY" in out)
check("nothing left behind after an md5 failure", leftovers() == [])
check("state records the md5 failure", state()["result"] == "FAIL (download md5)")

# -------------------------------------------------------------------- 5 ----
print("- 5 · zero-byte and truncated downloads")
zero = FakeDrive({M.NIGHTLY: b""})
rc, out = run(drive=zero)
check("zero-byte download exits 30", rc == 30)
check("it says zero bytes", "ZERO BYTES" in out)

trunc = FakeDrive({M.NIGHTLY: GOOD_GZ})
trunc.truncate = 64
rc, out = run(drive=trunc)
check("truncated download exits 30", rc == 30)
check("it says truncated", "TRUNCATED" in out)
check("state records the truncation", state()["result"] == "FAIL (truncated download)")

# -------------------------------------------------------------------- 6 ----
print("- 6 · corrupt gzip — the check nobody had ever run")
mid = bytearray(GOOD_GZ)
mid[len(mid) // 2] ^= 0xFF
rc, out = run(drive=FakeDrive({M.NIGHTLY: bytes(mid)}))
check("mid-stream corruption exits 31", rc == 31)
check("it names the gunzip stage", "GUNZIP FAILED" in out)
check("it says the transport check could not have caught this",
      "transport verified these bytes" in out)

crc = bytearray(GOOD_GZ)
crc[-5] ^= 0xFF                      # inside the trailing CRC32
rc, out = run(drive=FakeDrive({M.NIGHTLY: bytes(crc)}))
check("a flipped CRC exits 31", rc == 31)
check("nothing left behind after a gunzip failure", leftovers() == [])
check("state records the gunzip failure", state()["result"] == "FAIL (gunzip)")

# -------------------------------------------------------------------- 7 ----
print("- 7 · a malformed database")
MAL = os.path.join(tmpd, "malformed.db")
make_db(MAL, items=2000)
blob = bytearray(open(MAL, "rb").read())
for off in range(4096, 4096 * 6):    # leave page 1 (the header) alone
    blob[off] = 0x5A
open(MAL, "wb").write(bytes(blob))
rc, out = run(drive=FakeDrive({M.NIGHTLY: gz_of(MAL)}))
check("a malformed database exits 32", rc == 32)
check("state records a database failure", state()["result"].startswith("FAIL ("))
check("nothing left behind after a database failure", leftovers() == [])

# -------------------------------------------------------------------- 8 ----
print("- 8 · an empty day_entry, and a missing one")
EMPTY = os.path.join(tmpd, "empty.db")
make_db(EMPTY, days=0)
rc, out = run(drive=FakeDrive({M.NIGHTLY: gz_of(EMPTY)}))
check("an empty day_entry exits 32", rc == 32)
check("it explains the shipper never ships an empty book", "EMPTY" in out)
check("state records the empty book", state()["result"] == "FAIL (empty day_entry)")

NOTBL = os.path.join(tmpd, "noday.db")
make_db(NOTBL, drop_day_entry=True)
rc, out = run(drive=FakeDrive({M.NIGHTLY: gz_of(NOTBL)}))
check("a missing day_entry table exits 32", rc == 32)
check("state records the missing table", state()["result"] == "FAIL (no day_entry)")

# -------------------------------------------------------------------- 9 ----
print("- 9 · description parsing")
check("parses the shipper's own stamp",
      M.desc_day_entries("verified backup of finance_2026-09-07.db · md5 abc ·"
                         " 1234 day-entries · shipped 2026-09-07 01:40:11") == 1234)
check("parses it through the monthly prefix",
      M.desc_day_entries("month=2026-09 · verified backup of x · md5 abc ·"
                         " 88 day-entries · shipped 2026-09-01 01:40:02") == 88)
check("no count -> None", M.desc_day_entries("preflight write-test 2026-09-07") is None)
check("empty description -> None", M.desc_day_entries("") is None)
check("missing description -> None", M.desc_day_entries(None) is None)

# ------------------------------------------------------------------- 10 ----
print("- 10 · a description that disagrees WARNS, it does not fail")
warn = FakeDrive({M.NIGHTLY: GOOD_GZ})
warn.set_desc(M.NIGHTLY, "verified backup of finance_2026-09-06.db · md5 abc ·"
                         " 9999 day-entries · shipped 2026-09-06 01:40:03")
rc, out = run(drive=warn)
check("a disagreeing count still exits 0", rc == 0)
check("it warns loudly", "*** WARNING ***" in out)
check("it names both counts", "9999" in out and "holds 7" in out)
check("it explains a later revision is legitimate", "later revision" in out)
check("it still prints PASS", "RESTORE VERIFY PASS" in out)
check("state says PASS with warnings", state()["result"] == "PASS (with warnings)")

nodesc = FakeDrive({M.NIGHTLY: GOOD_GZ})
rc, out = run(drive=nodesc)
check("an unstamped description is not a failure", rc == 0)
check("it says there was nothing to cross-check", "nothing to" in out)

# ------------------------------------------------------------------- 11 ----
print("- 11 · slot missing, conf problems, no network")
rc, out = run(drive=FakeDrive({M.MONTHLY: GOOD_GZ}))
check("a missing nightly slot exits 13", rc == 13)
check("it names the missing slot", M.NIGHTLY in out)
check("state records the missing slot", state()["result"] == "FAIL (slot missing)")

open(M.CONF_PATH, "w").write("FOLDER_ID=FOLDER1\n")
rc, out = run(drive=FakeDrive({M.NIGHTLY: GOOD_GZ}))
check("no SA_JSON exits 10", rc == 10)
open(M.CONF_PATH, "w").write("SA_JSON=%s\n" % sa_path)
rc, out = run(drive=FakeDrive({M.NIGHTLY: GOOD_GZ}))
check("no FOLDER_ID exits 11", rc == 11)
open(M.CONF_PATH, "w").write(CONF_GOOD)

buf = io.StringIO()
rc = 0
try:
    with contextlib.redirect_stdout(buf):
        def boom(_s):
            raise OSError("Network is unreachable")
        M.verify(slot=M.NIGHTLY, drive_cls=(lambda s: None), session_maker=boom)
except SystemExit as e:
    rc = e.code
check("no network exits 20", rc == 20)
check("it says Drive is unreachable", "cannot reach Google Drive" in buf.getvalue())

# ------------------------------------------------------------------- 12 ----
print("- 12 · monthly mode, and read-only by construction")
monthly = FakeDrive({M.NIGHTLY: b"not even a gzip", M.MONTHLY: GOOD_GZ})
rc, out = run(slot=M.MONTHLY, drive=monthly)
check("monthly mode exits 0 on a good monthly slot", rc == 0)
check("monthly mode read the monthly slot", M.MONTHLY in out)
check("state slot is the monthly", state()["slot"] == M.MONTHLY)

src = open(os.path.join(HERE, "verify_restore.py")).read()
check("no upload endpoint anywhere in the script", "upload/drive" not in src)
check("the Drive class cannot update content", not hasattr(M.Drive, "update_content"))
check("the Drive class cannot patch metadata", not hasattr(M.Drive, "patch_meta"))
check("the Drive class cannot pin revisions", not hasattr(M.Drive, "pin_revision"))
check("it never issues a PATCH or a PUT", ".patch(" not in src and ".put(" not in src)
check("the header states its own age rule",
      "CANNOT STATE ITS OWN AGE" in src.upper())

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = M.main(["verify_restore.py", "--nonsense"])
check("a bad argument exits 2 with usage", rc == 2 and "usage:" in buf.getvalue())

# -------------------------------------------------------------------------
fails = [n for n, ok in CHECKS if not ok]
print()
print("%d checks, %d failures" % (len(CHECKS), len(fails)))
if fails:
    for n in fails:
        print("  FAILED:", n)
    sys.exit(1)
sys.exit(0)
