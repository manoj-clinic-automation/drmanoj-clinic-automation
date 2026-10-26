#!/root/wa/venv/bin/python3
# =============================================================================
#  verify_restore_state.py  ·  kit S661, session S357  ·  the RESTORE side of the
#  encrypted clinic state bundle.  Sibling of verify_restore.py (S230, the
#  finance.db drill) and companion to
#  /root/state_backup/clinic_state_backup.py (S230/S233, cron 01:50).
#
#  WHAT THE EXISTING CHAIN PROVES, AND WHAT IT DOES NOT.
#
#  Every night clinic_state_backup.py gathers the PHI stores and the shape of
#  the machine into a tar.gz, encrypts it ON THE BOX (openssl AES-256-CBC,
#  PBKDF2, key file that never leaves the box), decrypts its own ciphertext
#  once to prove the round trip, overwrites an owner-owned Drive slot file and
#  reads Drive's md5Checksum back.
#
#  That proves TRANSPORT and that the ciphertext decrypted ONCE, on the night,
#  with the key as it then was. It does NOT prove RECOVERABILITY: nobody has
#  pulled the slot back down, decrypted it with the key file as it is TODAY,
#  untarred it, and opened the databases inside. A key file that was rotated,
#  a tar torn after the round trip, or a database that fails integrity_check
#  inside the bundle would ship and verify and stamp exactly like a good one.
#
#  This script closes that hole, and only that hole. It downloads the slot,
#  checks the md5, DECRYPTS IT with the box's key file (the exact openssl
#  invocation the writer uses), UNTARS IT, reads the INVENTORY.txt the writer
#  put inside, compares the inventory with what the bundle actually holds,
#  runs PRAGMA integrity_check on every sqlite member, and reports the
#  bundle's own taken-at stamp and age.
#
#  THE PLAINTEXT HOLDS PATIENT DATA (F-31). It is untarred into a mode-0700
#  directory in the work dir, it is DELETED at the end unless --keep, and it is
#  NEVER LISTED file by file in any log -- counts only, on every line here.
#  The key file's path and content are never printed.
#
#  IT IS STRICTLY READ-ONLY, ON BOTH SIDES.
#  Nothing is uploaded. No description is patched, no revision is pinned, no
#  metadata is touched -- there is no patch_meta and no update_content in this
#  file at all (the Drive class below has list, get and download, and nothing
#  else). On the box it writes exactly three things: temp files in the work
#  dir (deleted unless --keep), its own state file and one summary line.
#
#  A VERIFICATION THAT CANNOT STATE ITS OWN AGE HAS NOT BEEN DONE -- which is
#  why EVERY run, PASS or FAIL, leaves the state file behind with an ISO
#  timestamp on it.
#
#  Modes:
#    (default)   download, decrypt, untar, inventory, integrity
#    --dry       preflight: conf, key file present and mode 600, openssl
#                usable, a real encrypt->decrypt->compare round trip on a
#                fixture, slot present. No download, no plaintext from Drive.
#    --keep      leave the download, the decrypted tar and the untarred tree
#                in the work dir (patient data -- for a look, then delete)
#    --root P    root every path at P instead of "/" (the test harness)
#
#  Config: the SAME conf the writer reads (KEY=VALUE, chmod 600), never in git:
#    /root/state_backup/clinic_state_backup.conf
#      SA_JSON=                    service-account json  (required here)
#      FOLDER_ID=                  the Drive folder      (required here)
#      ENC_KEY_FILE=               the key file          (required here)
#      WORK_DIR=                   optional, default <conf dir>/work
#      VERIFY_RESTORE_STATE_FILE=  optional, default
#                                  /root/state_backup/verify_restore_state.state.json
#
#  Exit codes:
#    0 pass · 2 usage · 10 conf/SA · 11 no FOLDER_ID · 13 slot missing
#    14 no openssl · 15 key file · 20 Drive unreachable · 30 download bad
#    31 decrypt failed · 32 untar failed · 33 inventory missing
#    34 database(s) fail integrity_check · 42 round trip failed (--dry)
#
#  No patient data, no ids, no key paths, no secrets in this file (F-185).
# =============================================================================
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)   # google-auth py3.9 EOL noise

# --- the same names clinic_state_backup.py uses -------------------------------
CONF_REL   = "root/state_backup/clinic_state_backup.conf"   # writer CONF_PATH
NIGHTLY    = "clinic_state_nightly.tar.gz.enc"              # writer NIGHTLY
INVENTORY  = "INVENTORY.txt"                                # writer _write_inventory
INV_HEAD   = "# clinic_state_backup inventory · "           # its first line
OPENSSL    = "openssl"                                      # writer OPENSSL
STATE_REL  = "root/state_backup/verify_restore_state.state.json"
SUMMARY_REL = "root/state_backup/verify_restore_state.summary.txt"
CHUNK      = 1 << 20
STALE_H    = 30                      # the writer's own STALE_WARN_H


def log(*a):
    print("[%s]" % time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def die(code, *a):
    log("FATAL:", *a)
    sys.exit(code)


def under_root(root, rel):
    return os.path.join(root, rel.lstrip("/"))


# ---------------------------------------------------------------- config ----
def load_conf(conf_path):
    conf = {}
    if os.path.exists(conf_path):
        for line in open(conf_path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def work_dir(conf, conf_path):
    d = conf.get("WORK_DIR") or os.path.join(os.path.dirname(conf_path) or "/tmp", "work")
    if not os.path.isdir(d):
        os.makedirs(d, 0o700)
    return d


def state_path(conf, root):
    return conf.get("VERIFY_RESTORE_STATE_FILE") or under_root(root, STATE_REL)


def summary_path(conf, root):
    return conf.get("VERIFY_RESTORE_SUMMARY_FILE") or under_root(root, SUMMARY_REL)


# ---------------------------------------------------------- crypto (copied) --
# The next four functions are the writer's, copied so the drill stands alone:
# clinic_state_backup.py openssl_ok / check_keyfile / encrypt_file /
# decrypt_file / crypto_roundtrip. The invocation must stay byte-identical to
# the writer's or the drill proves nothing about the writer's ciphertext.
def openssl_ok():
    try:
        r = subprocess.run([OPENSSL, "version"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=30)
        return r.returncode == 0, r.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError) as ex:
        return False, str(ex)


def check_keyfile(conf, conf_path):
    kf = conf.get("ENC_KEY_FILE")
    if not kf:
        die(10, "ENC_KEY_FILE= is not set in", conf_path, "-- the key file is"
            " generated by the installer and its path is site configuration;"
            " this script never guesses a path.")
    if not os.path.exists(kf):
        die(15, "the encryption key file named in the conf does not exist."
                " Without it nothing in the slot file can ever be read --"
                " A BACKUP WHOSE KEY IS LOST IS UNRECOVERABLE.")
    if os.path.getsize(kf) < 16:
        die(15, "the encryption key file is shorter than 16 bytes -- that is not a key.")
    mode = stat.S_IMODE(os.stat(kf).st_mode)
    if mode & 0o077:
        die(15, "the encryption key file is mode %o -- it must be 600."
                " Refusing to use a key the whole box can read." % mode)
    if not os.access(kf, os.R_OK):
        die(15, "the encryption key file is not readable by this user.")
    return kf


def encrypt_file(src, dst, keyfile):
    cmd = [OPENSSL, "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
           "-salt", "-pass", "file:" + keyfile, "-in", src, "-out", dst]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise RuntimeError("openssl enc failed (rc %d): %s"
                           % (r.returncode, r.stdout.decode("utf-8", "replace")[:300]))
    os.chmod(dst, 0o600)
    return dst


def decrypt_file(src, dst, keyfile):
    cmd = [OPENSSL, "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
           "-pass", "file:" + keyfile, "-in", src, "-out", dst]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise RuntimeError("openssl enc -d failed (rc %d): %s"
                           % (r.returncode, r.stdout.decode("utf-8", "replace")[:300]))
    return dst


def crypto_roundtrip(keyfile, work):
    """Encrypt a small fixture, decrypt it, compare hashes. Proof, not faith."""
    d = tempfile.mkdtemp(prefix="cryptowalk_", dir=work)
    try:
        plain = os.path.join(d, "fixture.bin")
        with open(plain, "wb") as fh:
            fh.write(b"clinic-state-backup round-trip fixture " * 64)
        before = md5_file(plain)
        enc = encrypt_file(plain, os.path.join(d, "fixture.enc"), keyfile)
        with open(enc, "rb") as fh:
            head = fh.read(16)
        if head[:8] != b"Salted__":
            raise RuntimeError("ciphertext has no openssl salt header")
        if head[8:] == b"\x00" * 8:
            raise RuntimeError("ciphertext salt looks empty")
        back = decrypt_file(enc, os.path.join(d, "fixture.out"), keyfile)
        after = md5_file(back)
        if before != after:
            raise RuntimeError("round trip changed the bytes (%s -> %s)"
                               % (before, after))
        return True
    finally:
        shutil.rmtree(d, ignore_errors=True)


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
        """Stream the content to disk, never into memory."""
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
    """The one owner-owned slot file, by exact name -- the same name the
    writer uses, taken from the same constant. None when it is gone."""
    return {f["name"]: f for f in listing}.get(name)


# ---------------------------------------------------------------- verify ----
def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(CHUNK), b""):
            h.update(b)
    return h.hexdigest()


def safe_members(tf):
    """Only directories and regular files with clean relative names. Anything
    that could write outside the work dir, or is a link or device, is refused."""
    out = []
    for m in tf.getmembers():
        parts = m.name.replace("\\", "/").split("/")
        if m.name.startswith(("/", "\\")) or ".." in parts or parts[0] == "":
            raise RuntimeError("unsafe member path in the archive")
        if m.isdir() or m.isfile():
            out.append(m)
        else:
            raise RuntimeError("archive carries a non-regular member")
    return out


def untar(src, dest):
    """Extract into dest; return [relative paths of regular files]. The list
    stays inside this process -- it is counted, never logged."""
    with tarfile.open(src, "r:gz") as tf:
        members = safe_members(tf)
        try:
            tf.extractall(dest, members=members, filter="data")
        except TypeError:
            tf.extractall(dest, members=members)
    return [m.name for m in members if m.isfile()]


def find_inventory(files):
    """The writer tars the stage under one top directory (clinic_state_<date>),
    so the inventory sits at '<arc>/INVENTORY.txt'. Returns (arc, member) or
    (None, None)."""
    for name in sorted(files):
        parts = name.split("/")
        if parts[-1] == INVENTORY and len(parts) <= 2:
            return ("/".join(parts[:-1]), name)
    return None, None


def read_inventory(path):
    """(taken_at, [(rel, bytes)]) from the writer's INVENTORY.txt:
    header '# clinic_state_backup inventory · <ts>', then
    'path_in_bundle\\tbytes\\tsource_mtime\\tsource' rows. The source column
    is read and dropped; it names stores, never a patient, but nothing from
    inside the bundle is printed by this drill regardless."""
    taken_at, rows = None, []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh.read().splitlines():
            if line.startswith(INV_HEAD):
                taken_at = line[len(INV_HEAD):].strip()
                continue
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split("\t")
            if len(f) >= 2 and f[1].isdigit():
                rows.append((f[0], int(f[1])))
    return taken_at, rows


def is_sqlite(path):
    try:
        with open(path, "rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def sqlite_integrity(path):
    """PRAGMA integrity_check, read-only. 'ok' is the only acceptable answer.
    (the writer's, copied)"""
    try:
        c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    except sqlite3.Error as ex:
        return "unopenable: %s" % ex
    try:
        return c.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.DatabaseError as ex:
        return "unreadable: %s" % ex
    finally:
        c.close()


def age_hours(stamp):
    try:
        t = time.mktime(time.strptime(stamp, "%Y-%m-%d %H:%M:%S"))
        return (time.time() - t) / 3600.0
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ state ---
def load_state(p):
    try:
        with open(p) as fh:
            return json.load(fh)
    except Exception:
        return {}


def write_state(p, new):
    """Merge over what is there (a preflight must not erase the last real
    verify and vice versa), then atomic replace, mode 600."""
    state = load_state(p)
    state.update(new)
    try:
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d, 0o700)
        tmp = p + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, p)
        os.chmod(p, 0o600)
        log("state written:", p)
    except OSError as ex:
        log("WARNING: could not write the state file", p, ":", ex)


def append_summary(p, line):
    try:
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d, 0o700)
        with open(p, "a") as fh:
            fh.write(line.rstrip("\n") + "\n")
    except OSError as ex:
        log("WARNING: could not write the summary line:", ex)


def cleanup(paths, keep):
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        if keep:
            log("kept (PATIENT DATA -- delete when done):", p)
            continue
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.unlink(p)
            log("deleted:", p)
        except OSError as ex:
            log("WARNING: could not delete", p, ":", ex)


# ------------------------------------------------------------------- run ----
def _connect(root):
    conf_path = under_root(root, CONF_REL)
    if not os.path.exists(conf_path):
        die(10, "no conf at", conf_path, "-- the installer writes it; this"
            " verifier reads the SAME conf the writer reads and never invents one.")
    conf = load_conf(conf_path)
    sa = conf.get("SA_JSON")
    if not sa:
        die(10, "SA_JSON= is not set in", conf_path)
    if not os.path.exists(sa):
        die(10, "SA_JSON in the conf points at a file that does not exist.")
    fid = conf.get("FOLDER_ID")
    if not fid:
        die(11, "FOLDER_ID= is not set in", conf_path)
    return conf, conf_path, sa, fid


def _crypto_ready(conf, conf_path, work):
    ok, ver = openssl_ok()
    if not ok:
        die(14, "openssl is not usable (%s) -- nothing in the slot file can be"
                " read without it." % ver)
    log("openssl:", ver)
    kf = check_keyfile(conf, conf_path)
    log("key file: present, mode 600 ·", os.path.getsize(kf), "bytes"
        " (its path and content are never printed)")
    try:
        crypto_roundtrip(kf, work)
    except Exception as ex:
        die(42, "encryption round trip FAILED on a fixture:", ex)
    log("encrypt -> decrypt -> compare on a fixture: OK (AES-256-CBC, PBKDF2 200k)")
    return kf


def preflight(root="/", drive_cls=Drive, session_maker=make_session):
    """--dry: prove conf, key, openssl, round trip, folder and slot. No download."""
    conf, conf_path, sa, fid = _connect(root)
    sp = state_path(conf, root)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    pre = {"last_preflight_iso": now, "preflight": "FAIL (did not start)"}
    try:
        work = work_dir(conf, conf_path)
        log("conf ok · SA_JSON present · FOLDER_ID set · work dir", work)
        pre["preflight"] = "FAIL (crypto)"
        _crypto_ready(conf, conf_path, work)
        pre["preflight"] = "FAIL (drive)"
        try:
            listing = drive_cls(session_maker(sa)).list(fid)
        except Exception as ex:
            die(20, "cannot reach Google Drive:", ex)
        meta = find_slot(listing, NIGHTLY)
        if meta is None:
            pre["preflight"] = "FAIL (slot missing)"
            die(13, "slot file", NIGHTLY, "is not in the Drive folder")
        log("slot present:", NIGHTLY, "·", meta.get("size", "?"), "bytes · drive md5",
            meta.get("md5Checksum") or "(none)")
        log("    description:", (meta.get("description") or "(empty)")[:300])
        pre["preflight"] = "OK"
        log("PREFLIGHT OK -- nothing downloaded; run without --dry for the drill")
        return 0
    finally:
        write_state(sp, pre)


def verify(root="/", keep=False, drive_cls=Drive, session_maker=make_session):
    conf, conf_path, sa, fid = _connect(root)
    sp = state_path(conf, root)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S")
    state = {"last_verify_iso": now_iso, "slot": NIGHTLY,
             "result": "FAIL (did not start)", "drive_md5": None,
             "members": None, "inventory_rows": None, "inventory_unlisted": None,
             "inventory_absent": None, "db_checked": None, "db_bad": None,
             "taken_at": None}
    work = work_dir(conf, conf_path)
    enc_path = tar_path = tree = None
    warned = []

    def fail(code, label, *msg):
        state["result"] = "FAIL (%s)" % label
        die(code, *msg)

    try:
        # -- 0 · the key, before a byte is downloaded ------------------------
        kf = _crypto_ready(conf, conf_path, work)

        # -- 1 · the slot ----------------------------------------------------
        try:
            d = drive_cls(session_maker(sa))
            listing = d.list(fid)
        except Exception as ex:
            fail(20, "drive unreachable", "cannot reach Google Drive:", ex)
        meta = find_slot(listing, NIGHTLY)
        if meta is None:
            fail(13, "slot missing", "slot file", NIGHTLY, "is not in the Drive"
                 " folder -- it is owner-owned and must exist; recreate it from"
                 " the owner's account (the service account cannot, it has"
                 " zero quota).")
        drive_md5 = meta.get("md5Checksum")
        log("1 · slot file:", meta.get("name"), "·", meta.get("size", "?"),
            "bytes · drive md5", drive_md5 or "(none)")
        log("    description:", (meta.get("description") or "(empty)")[:300])
        state["drive_md5"] = drive_md5

        # -- 2 · download ----------------------------------------------------
        fd, enc_path = tempfile.mkstemp(suffix=".tar.gz.enc", prefix="restore_state_", dir=work)
        os.close(fd)
        os.chmod(enc_path, 0o600)
        try:
            got = d.download(meta["id"], enc_path)
        except SystemExit:
            raise
        except Exception as ex:
            fail(20, "download failed", "download of", NIGHTLY, "failed:", ex)
        log("2 · downloaded %d bytes -> %s" % (got, enc_path))

        # -- 3 · the bytes that arrived --------------------------------------
        size = os.path.getsize(enc_path)
        if size == 0:
            fail(30, "empty download", "the download is ZERO BYTES -- nothing to restore from")
        if meta.get("size") is not None and str(meta["size"]).isdigit() \
                and int(meta["size"]) != size:
            fail(30, "truncated download", "TRUNCATED: Drive reports %s bytes,"
                 " %d arrived" % (meta["size"], size))
        local_md5 = md5_file(enc_path)
        if drive_md5 and local_md5 != drive_md5:
            fail(30, "download md5", "download DID NOT VERIFY: drive md5 %s vs"
                 " downloaded %s" % (drive_md5, local_md5))
        state["drive_md5"] = local_md5
        log("3 · md5 of the downloaded bytes matches Drive:", local_md5)

        # -- 4 · decrypt with the key as it is TODAY -------------------------
        tar_path = enc_path[:-4]
        try:
            decrypt_file(enc_path, tar_path, kf)
        except SystemExit:
            raise
        except Exception as ex:
            fail(31, "decrypt", "DECRYPT FAILED (%s) -- the slot file does not"
                 " open with the key file named in the conf. Either the key"
                 " was rotated after the night it was written, or the"
                 " ciphertext is damaged. Transport verified these bytes; they"
                 " are not recoverable with this key." % ex)
        os.chmod(tar_path, 0o600)
        log("4 · decrypted: %d bytes of tar.gz" % os.path.getsize(tar_path))

        # -- 5 · the step nobody has run -------------------------------------
        tree = tempfile.mkdtemp(prefix="restore_state_tree_", dir=work)
        os.chmod(tree, 0o700)
        try:
            files = untar(tar_path, tree)
        except SystemExit:
            raise
        except Exception as ex:
            fail(32, "untar", "UNTAR FAILED (%s: %s) -- decrypted, but not a"
                 " usable tar.gz. This is the check that had never been run."
                 % (type(ex).__name__, ex))
        state["members"] = len(files)
        log("5 · untarred cleanly: %d members (gzip CRC ok) -> %s (mode 0700;"
            " contents are never listed)" % (len(files), tree))

        # -- 6 · the inventory the writer put inside -------------------------
        arc, inv_member = find_inventory(files)
        if inv_member is None:
            fail(33, "inventory missing", "the bundle carries no %s -- not a"
                 " clinic state bundle as the writer builds it" % INVENTORY)
        taken_at, rows = read_inventory(os.path.join(tree, inv_member))
        state["inventory_rows"] = len(rows)
        state["taken_at"] = taken_at
        prefix = arc + "/" if arc else ""
        have = {}
        for name in files:
            if name.startswith(prefix):
                have[name[len(prefix):]] = os.path.getsize(os.path.join(tree, name))
        listed = {rel for rel, _b in rows}
        inv_absent = sum(1 for rel in listed if rel not in have)
        unlisted = sum(1 for rel in have if rel not in listed and rel != INVENTORY)
        size_mism = sum(1 for rel, b in rows if rel in have and have[rel] != b)
        state["inventory_unlisted"], state["inventory_absent"] = unlisted, inv_absent
        log("6 · inventory: %d rows · bundle holds %d files (+ the inventory)"
            " · %d listed-but-absent · %d unlisted · %d size mismatch"
            % (len(rows), len(have) - (1 if INVENTORY in have else 0),
               inv_absent, unlisted, size_mism))
        if not rows:
            warned.append("inventory has no rows")
        if inv_absent or unlisted or size_mism:
            warned.append("inventory disagrees with contents (%d absent, %d unlisted,"
                          " %d size)" % (inv_absent, unlisted, size_mism))
            log("    *** WARNING *** the inventory and the contents disagree."
                " The bytes decrypted and untarred; what is in doubt is whether"
                " this bundle was written by the writer as it stands.")
        age = age_hours(taken_at)
        if taken_at:
            log("    taken_at=%s (%s)" % (taken_at, "%.1f h ago" % age
                                          if age is not None else "age unknown"))
            if age is not None and age > STALE_H:
                warned.append("bundle is %.0f h old" % age)
                log("    *** WARNING *** the bundle is older than %d h -- the"
                    " 01:50 job may not be running" % STALE_H)
        else:
            warned.append("inventory carries no taken-at stamp")
            log("    *** WARNING *** the inventory carries no taken-at stamp")

        # -- 7 · every database opens and is whole ---------------------------
        db_checked = db_bad = 0
        for name in files:
            p = os.path.join(tree, name)
            if not is_sqlite(p):
                continue
            db_checked += 1
            if sqlite_integrity(p) != "ok":
                db_bad += 1
        state["db_checked"], state["db_bad"] = db_checked, db_bad
        log("7 · sqlite members: %d checked · %d ok · %d FAIL integrity_check"
            % (db_checked, db_checked - db_bad, db_bad))
        if db_bad:
            fail(34, "integrity_check", "%d database(s) inside the bundle fail"
                 " PRAGMA integrity_check -- the writer refuses to ship a"
                 " database that fails on the box, so a failure HERE means the"
                 " copy inside the bundle is damaged." % db_bad)
        if db_checked == 0:
            warned.append("no sqlite member found")
            log("    *** WARNING *** no sqlite database inside the bundle at all")

        # -- 8 · verdict -----------------------------------------------------
        state["result"] = "PASS" + (" (with warnings)" if warned else "")
        state["last_pass_iso"] = now_iso
        log("RESTORE VERIFY PASS -- %s · %d members · %d inventory rows · %d db ok"
            " · taken %s" % (NIGHTLY, len(files), len(rows), db_checked, taken_at or "?"))
        if warned:
            log("PASS carries %d warning(s): %s" % (len(warned), "; ".join(warned)))
        return 0
    finally:
        # deletion happens on every path, failures included -- plaintext first
        cleanup([tree, tar_path, enc_path], keep)
        if not state["result"].startswith("PASS"):
            state["last_failure_iso"] = now_iso
            log("RESTORE VERIFY FAIL -- %s · %s" % (NIGHTLY, state["result"]))
        write_state(sp, state)
        append_summary(summary_path(conf, root),
                       "%s %s slot=%s drive_md5=%s members=%s inventory_rows=%s"
                       " db_checked=%s db_bad=%s taken_at=%s"
                       % (now_iso, state["result"], NIGHTLY, state["drive_md5"],
                          state["members"], state["inventory_rows"],
                          state["db_checked"], state["db_bad"], state["taken_at"]))


USAGE = ("usage: verify_restore_state.py [--dry] [--keep] [--root PATH]\n"
         "  (default)   download the encrypted state bundle, decrypt, untar,\n"
         "              check the inventory and every database inside\n"
         "  --dry       preflight only: conf, key, openssl, round trip, slot\n"
         "  --keep      leave the plaintext in the work dir (patient data)\n"
         "  --root P    root every path at P (test harness)\n"
         "read-only: this never writes to Drive.")


def main(argv, drive_cls=Drive, session_maker=make_session):
    keep = dry = False
    root = os.environ.get("ROOT", "/") or "/"
    args = list(argv[1:])
    while args:
        a = args.pop(0)
        if a == "--keep":
            keep = True
        elif a == "--dry":
            dry = True
        elif a == "--root" and args:
            root = args.pop(0)
        else:
            print(USAGE)
            return 2
    if dry:
        return preflight(root=root, drive_cls=drive_cls, session_maker=session_maker)
    return verify(root=root, keep=keep, drive_cls=drive_cls, session_maker=session_maker)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
