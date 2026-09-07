#!/root/wa/venv/bin/python3
# =============================================================================
#  verify_restore.py  ·  Session 230  ·  the RESTORE side of the finance.db
#  off-box backup.  Companion to S213_FINDB_DRIVE/finance_drive_backup.py.
#
#  WHAT THE EXISTING CHAIN PROVES, AND WHAT IT DOES NOT.
#
#  Every night finance_backup.sh (01:05) takes a verified local copy, and
#  finance_drive_backup.py (01:40) gzips the newest one and overwrites an
#  owner-owned Drive slot file, then reads Drive's own md5Checksum back and
#  dies if it differs from the md5 of the bytes it sent.
#
#  That proves TRANSPORT. It proves the bytes that left the box are the bytes
#  Google now holds. It does NOT prove RECOVERABILITY: nobody has ever pulled
#  that object back down, decompressed it, and opened the database inside it.
#  A gzip whose CRC is wrong, or a database that fails integrity_check, would
#  ship and verify and stamp its description exactly like a good one.
#
#  This script closes that hole, and only that hole. It downloads the slot
#  file, checks the md5, GUNZIPS IT (the check nobody has ever run), opens the
#  result read-only, runs PRAGMA integrity_check, counts what is inside, and
#  compares that count with the one the shipper recorded in the description.
#
#  IT IS STRICTLY READ-ONLY, ON BOTH SIDES.
#  Nothing is uploaded. No description is patched, no revision is pinned, no
#  metadata is touched — there is no patch_meta and no update_content in this
#  file at all. On the local box it writes exactly two things: temp files in
#  the work dir (deleted unless --keep) and its own small state file.
#
#  A VERIFICATION THAT CANNOT STATE ITS OWN AGE HAS NOT BEEN DONE — which is
#  why every run leaves VERIFY_STATE_FILE behind with an ISO timestamp on it.
#
#  Modes:
#    nightly   (default)  verify the nightly slot
#    monthly              verify the monthly slot
#    --keep               leave the restored .db in the work dir for a look
#
#  Config: the SAME conf the shipper uses, read at runtime, never in git:
#    /root/finance/drive_backup.conf   (KEY=VALUE, chmod 600)
#      SA_JSON=            service-account json  (required here)
#      FOLDER_ID=          the Drive folder      (required here)
#      WORK_DIR=           optional, default /tmp
#      VERIFY_STATE_FILE=  optional, default beside the other finance state
#
#  Exit codes:
#    0 pass · 2 usage · 10 conf/SA · 11 no FOLDER_ID · 13 slot missing
#    20 Drive unreachable · 30 download bad · 31 gunzip failed
#    32 database unusable
#
#  No patient data, no ids, no key paths, no secrets in this file (F-185).
# =============================================================================
import gzip
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)   # google-auth py3.9 EOL noise

CONF_PATH = "/root/finance/drive_backup.conf"
NIGHTLY   = "finance_nightly.db.gz"
MONTHLY   = "finance_monthly.db.gz"
CHUNK     = 1 << 20
TOP_N     = 10                                 # largest tables to report


def log(*a):
    print("[%s]" % time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def die(code, *a):
    log("FATAL:", *a)
    sys.exit(code)


# ---------------------------------------------------------------- config ----
def load_conf():
    conf = {}
    if os.path.exists(CONF_PATH):
        for line in open(CONF_PATH):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def find_sa_json(conf):
    """Conf only. The shipper also searches a few well-known paths; this file
    does not repeat them, because key paths do not belong in the repository
    (F-185). Whatever the shipper found, SA_JSON already records."""
    p = conf.get("SA_JSON")
    return p if p and os.path.exists(p) else None


def work_dir(conf):
    d = conf.get("WORK_DIR") or "/tmp"
    if not os.path.isdir(d):
        os.makedirs(d, 0o700)
    return d


def state_path(conf):
    return conf.get("VERIFY_STATE_FILE") or os.path.join(
        os.path.dirname(CONF_PATH) or "/tmp", "finance_restore_verify.state.json")


# ----------------------------------------------------------------- drive ----
def make_session(sa_json):
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    creds = Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive"])
    return AuthorizedSession(creds)


class Drive:
    """The three READ-ONLY Drive calls this job needs, and nothing else.
    There is deliberately no update, no patch and no pin in this class."""
    API = "https://www.googleapis.com/drive/v3"

    def __init__(self, session):
        self.s = session

    def _ck(self, r, what):
        if r.status_code >= 300:
            raise RuntimeError("%s -> HTTP %s: %s" % (what, r.status_code, r.text[:300]))
        return r

    def list(self, folder_id):
        files, token = [], None
        while True:
            params = {"q": "'%s' in parents and trashed=false" % folder_id,
                      "fields": "nextPageToken,files(id,name,size,md5Checksum,description)",
                      "pageSize": "1000"}
            if token:
                params["pageToken"] = token
            r = self._ck(self.s.get(self.API + "/files", params=params), "list")
            j = r.json()
            files += j.get("files", [])
            token = j.get("nextPageToken")
            if not token:
                return files

    def get(self, file_id):
        r = self._ck(self.s.get(self.API + "/files/" + file_id,
                                params={"fields": "id,name,size,md5Checksum,description"}),
                     "file get")
        return r.json()

    def download(self, file_id, dest):
        """Stream the content to disk. Never into memory — the db.gz is large
        and this may run on a small box."""
        r = self.s.get(self.API + "/files/%s" % file_id,
                       params={"alt": "media"}, stream=True)
        self._ck(r, "download")
        n = 0
        with open(dest, "wb") as fh:
            for b in r.iter_content(CHUNK):
                if b:
                    fh.write(b)
                    n += len(b)
        return n


def find_slot(listing, name):
    """The one owner-owned slot file, by exact name — the same names the
    shipper writes, taken from the same constants. None when it is gone."""
    return {f["name"]: f for f in listing}.get(name)


# ---------------------------------------------------------------- verify ----
def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(CHUNK), b""):
            h.update(b)
    return h.hexdigest()


def gunzip(src, dest):
    with gzip.open(src, "rb") as fi, open(dest, "wb") as fo:
        while True:
            b = fi.read(CHUNK)
            if not b:
                break
            fo.write(b)
    return os.path.getsize(dest)


def inspect_db(path):
    """Open READ-ONLY and ask the database about itself. Returns
    (integrity, tables, day_entries, [(table, rows), ...] largest first)."""
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    try:
        integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
        names = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
            " AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        counts = []
        for n in names:
            try:
                counts.append((n, c.execute('SELECT COUNT(*) FROM "%s"' % n).fetchone()[0]))
            except sqlite3.Error:
                counts.append((n, -1))
        days = dict(counts).get("day_entry")
    finally:
        c.close()
    counts.sort(key=lambda t: (-t[1], t[0]))
    return integrity, len(names), days, counts


DESC_DAYS = re.compile(r"(\d+)\s+day-entr", re.I)


def desc_day_entries(desc):
    """The shipper stamps: 'verified backup of <name> · md5 <gz md5> ·
    <N> day-entries · shipped <ts>' (the monthly is prefixed 'month=YYYY-MM · ').
    Pull N back out. None when the description has no count in it."""
    m = DESC_DAYS.search(desc or "")
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------ state ---
def write_state(conf, state):
    p = state_path(conf)
    try:
        tmp = p + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, p)
        os.chmod(p, 0o600)
        log("state written:", p)
    except OSError as ex:
        log("WARNING: could not write the state file", p, ":", ex)


def cleanup(paths, keep):
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        if keep:
            log("kept:", p)
            continue
        try:
            os.unlink(p)
            log("deleted:", p)
        except OSError as ex:
            log("WARNING: could not delete", p, ":", ex)


# ------------------------------------------------------------------- run ----
def _connect():
    conf = load_conf()
    if not os.path.exists(CONF_PATH):
        die(10, "no conf at", CONF_PATH, "— this verifier reads the SAME conf"
            " the shipper writes; install and preflight the shipper first.")
    sa = find_sa_json(conf)
    if not sa:
        die(10, "SA_JSON is not set in", CONF_PATH, "or does not point at an"
            " existing file — this verifier reads the key path from the conf"
            " and never carries one of its own.")
    fid = conf.get("FOLDER_ID")
    if not fid:
        die(11, "FOLDER_ID is not set in", CONF_PATH)
    return conf, sa, fid


def verify(slot=NIGHTLY, keep=False, drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect()
    state = {"last_verify_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "slot": slot, "result": "FAIL (did not start)",
             "tables": None, "day_entries": None, "bytes": None, "gz_md5": None}
    wd = work_dir(conf)
    gz_path = db_path = None
    warned = []

    def fail(code, label, *msg):
        state["result"] = "FAIL (%s)" % label
        die(code, *msg)

    try:
        # -- 1 · the slot ----------------------------------------------------
        try:
            d = drive_cls(session_maker(sa))
            listing = d.list(fid)
        except Exception as ex:
            fail(20, "drive unreachable", "cannot reach Google Drive:", ex)
        meta = find_slot(listing, slot)
        if meta is None:
            fail(13, "slot missing", "slot file", slot, "is not in the Drive"
                 " folder — it is owner-owned and must exist; recreate it from"
                 " the owner's account (the service account cannot, it has"
                 " zero quota).")
        drive_md5 = meta.get("md5Checksum")
        log("1 · slot file:", meta.get("name"), "·", meta.get("size", "?"),
            "bytes · drive md5", drive_md5 or "(none)")
        log("    description:", (meta.get("description") or "(empty)")[:300])
        state["gz_md5"] = drive_md5

        # -- 2 · download ----------------------------------------------------
        fd, gz_path = tempfile.mkstemp(suffix=".db.gz", prefix="restore_verify_", dir=wd)
        os.close(fd)
        os.chmod(gz_path, 0o600)
        try:
            got = d.download(meta["id"], gz_path)
        except SystemExit:
            raise
        except Exception as ex:
            fail(20, "download failed", "download of", slot, "failed:", ex)
        log("2 · downloaded %d bytes -> %s" % (got, gz_path))

        # -- 3 · the bytes that arrived --------------------------------------
        size = os.path.getsize(gz_path)
        if size == 0:
            fail(30, "empty download", "the download is ZERO BYTES —"
                 " nothing to restore from")
        if meta.get("size") is not None and str(meta["size"]).isdigit() \
                and int(meta["size"]) != size:
            fail(30, "truncated download", "TRUNCATED: Drive reports %s bytes,"
                 " %d arrived" % (meta["size"], size))
        local_md5 = md5_file(gz_path)
        if drive_md5 and local_md5 != drive_md5:
            fail(30, "download md5", "download DID NOT VERIFY: drive md5 %s vs"
                 " downloaded %s" % (drive_md5, local_md5))
        state["gz_md5"] = local_md5
        log("3 · md5 of the downloaded bytes matches Drive:", local_md5)

        # -- 4 · the check nobody has ever run -------------------------------
        db_path = gz_path[:-3] if gz_path.endswith(".gz") else gz_path + ".db"
        try:
            db_size = gunzip(gz_path, db_path)
        except SystemExit:
            raise
        except Exception as ex:
            fail(31, "gunzip", "GUNZIP FAILED (%s: %s) — the archive is corrupt;"
                 " transport verified these bytes but they are not a usable"
                 " gzip. This is the check that had never been run."
                 % (type(ex).__name__, ex))
        state["bytes"] = db_size
        log("4 · decompressed cleanly: %d bytes (gzip CRC ok) -> %s" % (db_size, db_path))

        # -- 5 · does it open ------------------------------------------------
        try:
            integrity, tables, days, counts = inspect_db(db_path)
        except SystemExit:
            raise
        except Exception as ex:
            fail(32, "not a database", "the decompressed file does not open as a"
                 " database (%s: %s)" % (type(ex).__name__, ex))
        if integrity != "ok":
            fail(32, "integrity_check", "PRAGMA integrity_check said %r" % integrity)
        log("5 · opened read-only · PRAGMA integrity_check: ok")

        # -- 6 · what is inside ----------------------------------------------
        state["tables"] = tables
        if days is None:
            fail(32, "no day_entry", "there is no day_entry table in the"
                 " restored database — the shipper's own guard table is"
                 " missing, so this is not the finance book")
        state["day_entries"] = days
        if days <= 0:
            fail(32, "empty day_entry", "day_entry is EMPTY — the shipper"
                 " refuses to ship an empty book, so an empty one here means"
                 " the chain is broken, not that the clinic had no days")
        log("6 · %d tables · day_entry holds %d rows" % (tables, days))
        log("    largest tables by row count:")
        for n, c in counts[:TOP_N]:
            log("      %-28s %s" % (n, c if c >= 0 else "(unreadable)"))

        # -- 7 · against what the shipper recorded ---------------------------
        rec = desc_day_entries(meta.get("description"))
        if rec is None:
            log("7 · the description records no day-entry count — nothing to"
                " cross-check (a slot written before the description stamp,"
                " or one edited by hand)")
        elif rec == days:
            log("7 · cross-check: description recorded %d day-entries, the"
                " restored database holds %d — agree" % (rec, days))
        else:
            warned.append("day-entry count %d recorded vs %d restored" % (rec, days))
            log("7 · *** WARNING *** the description records %d day-entries but"
                " the restored database holds %d." % (rec, days))
            log("    This is a WARNING, not a failure. The description records"
                " the state AT SHIP TIME; the slot file may legitimately hold a"
                " later revision, or the description may have been stamped by a"
                " run whose content update was refused. The restore itself is"
                " sound — the bytes decompressed and the database opened.")

        # -- 8/9 · verdict ---------------------------------------------------
        state["result"] = "PASS" + (" (with warnings)" if warned else "")
        log("RESTORE VERIFY PASS — %s · %d tables · %d day-entries · %d bytes"
            % (slot, tables, days, db_size))
        if warned:
            log("PASS carries %d warning(s): %s" % (len(warned), "; ".join(warned)))
        return 0
    finally:
        # deletion happens on every path, failures included
        cleanup([gz_path, db_path], keep)
        write_state(conf, state)
        if not state["result"].startswith("PASS"):
            log("RESTORE VERIFY FAIL — %s · %s" % (slot, state["result"]))


USAGE = ("usage: verify_restore.py [nightly|monthly] [--keep]\n"
         "  nightly  (default)  verify the nightly slot file\n"
         "  monthly             verify the monthly slot file\n"
         "  --keep              leave the restored database in the work dir\n"
         "read-only: this never writes to Drive.")


def main(argv):
    keep = False
    slot = NIGHTLY
    seen = False
    for a in argv[1:]:
        if a == "--keep":
            keep = True
        elif a in ("nightly", "monthly") and not seen:
            slot = NIGHTLY if a == "nightly" else MONTHLY
            seen = True
        else:
            print(USAGE)
            return 2
    return verify(slot=slot, keep=keep)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
