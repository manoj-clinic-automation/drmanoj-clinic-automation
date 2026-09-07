#!/root/wa/venv/bin/python3
# =============================================================================
#  clinic_state_backup.py  ·  Session 230  ·  S230_STATE_BACKUP  ·  v1
#
#  A BACKUP THAT CANNOT STATE ITS OWN AGE HAS NOT BEEN TAKEN.
#
#  THE SECOND OFF-BOX LEG. S213 gave finance.db a nightly off-box copy
#  (finance_drive_backup.py, cron 01:40). S230 measured the rest of the box and
#  found it has none: the call console, the asset index, the punches, the staff
#  register and ledger, and — quieter but just as costly — the SHAPE of the
#  machine (crontab, unit files, vhost configs). Code is safe in GitHub and the
#  OS is safe in the provider snapshot; this script covers what neither holds.
#
#  WHY IT UPDATES FILES INSTEAD OF CREATING THEM (inherited from S213 v2, and
#  proven on the live box 31-Aug-2026): a service account has ZERO Drive storage
#  quota and gets HTTP 403 "Service Accounts do not have storage quota" the
#  moment it tries to create a file. What it CAN do is write new CONTENT into a
#  file the OWNER already owns — those bytes bill the owner. So two owner-owned
#  slot files exist and are overwritten:
#
#     clinic_state_nightly.tar.gz.enc   every night; Drive's own revision
#                                       history is the ~30-day archive
#     clinic_state_monthly.tar.gz.enc   first verified run of a month, and that
#                                       revision is PINNED (keepForever)
#
#  🔴 ENCRYPTION IS NOT OPTIONAL (F-31). console.db holds patient call records;
#  the staff register and ledger hold staff-financial data. Patient data and
#  staff-financial data never reach cloud, chat or GitHub in the clear. The
#  bundle is therefore encrypted ON THE BOX, with openssl AES-256-CBC + PBKDF2,
#  using a key file that never leaves the box and never goes to Drive.
#  A BACKUP WHOSE KEY IS LOST IS UNRECOVERABLE. The installer generates the
#  key; this file never contains it, never names its path, and never guesses.
#
#  Refusal stances, absolute — nothing leaves the box on a bad day:
#    * any sqlite database failing integrity_check           -> FATAL (40)
#    * a source file missing that was present on the last run-> FATAL (41)
#    * the encrypt/decrypt round trip failing                -> FATAL (42)
#    * a read-back md5 differing from the local md5          -> FATAL (30),
#      and the monthly slot is NOT touched; the previous good version still
#      stands in the nightly file's revision history
#
#  Modes:
#    preflight  prove every precondition WITHOUT shipping: conf, openssl, key
#               file and its mode, a real encrypt->decrypt->compare round trip,
#               every source's presence, every database's integrity, Drive
#               reachable, both slot files present, and write access proven by
#               a metadata-only touch (no content changed, no revision made).
#    run        the nightly job.
#    list       what is in the Drive folder, the nightly revision count, and
#               the age of the last success from the state file. Read-only.
#
#  Config:  /root/state_backup/clinic_state_backup.conf   (KEY=VALUE, chmod 600)
#           Every value that is a secret, an id, or a path to a key lives THERE
#           and never here (F-185). The script refuses rather than guesses.
#
#  Cron (after the finance legs, before the CyberPanel window):
#    50 1 * * *  /root/wa/venv/bin/python3 /root/state_backup/clinic_state_backup.py run >> /root/state_backup/clinic_state_backup.log 2>&1
#
#  No patient data, no numbers, no secrets, no key paths in this file (F-185).
# =============================================================================
import fnmatch
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

# --- everything below is a module-level knob so the WALK can point the whole
# --- job at a fixture tree and touch no real path and no network.
CONF_PATH = "/root/state_backup/clinic_state_backup.conf"

NIGHTLY = "clinic_state_nightly.tar.gz.enc"
MONTHLY = "clinic_state_monthly.tar.gz.enc"

# INCLUDED — the data with no other off-box copy.
SRC_FILES = [
    "/root/wa/console.db",          # call console: calls, verdicts, transcripts
    "/root/assetapp/assets.db",     # asset index ONLY — uploads/ is excluded
    "/root/punches.csv",
    "/root/punches_raw.log",
    "/root/staff_master.csv",
]
# INCLUDED — stores whose data files are discovered at runtime, never guessed.
SRC_DIRS = [
    "/root/staff_register",
    "/root/staff_ledger",
]
DIR_DATA_EXT = (".db", ".sqlite", ".sqlite3", ".csv")
DIR_SKIP_NAMES = ("__pycache__", ".git", "venv", ".venv", "node_modules",
                  "uploads", "static", "templates")

# INCLUDED — the shape of the machine. Small, and it turns a rebuild from
# archaeology into an afternoon.
SYSTEMD_DIR = "/etc/systemd/system"
VHOST_DIR = "/usr/local/lsws/conf/vhosts"
CRONTAB_CMD = ["crontab", "-l"]
OPENSSL = "openssl"

# Clinic unit-name prefixes. Personal-cluster units (fitlog/gutlog/rxguard) are
# a different trust class and are deliberately NOT collected here.
UNIT_MATCH_DEFAULT = ("clinic-,assetapp,attendance-,attlistener,staff-,call-,"
                      "wa-,email-agent,marg,portal")
VHOST_MATCH_DEFAULT = "dr-manoj.in"

# EXCLUDED, actively, by pattern — every secret. Counted, never named.
SECRET_PATTERNS = (".env", ".env.*", "*.env", "*key*.json", "token*", "*token*",
                   "credentials*", "*credentials*", "*.pem", "*.key", "*.p12",
                   "*.pfx", "id_rsa*", "*secret*", "*.crt", "service_account*")

# a single file larger than this is skipped, and the run says so
MAX_FILE_MB_DEFAULT = 64
# 'list' calls the state stale past this many hours
STALE_WARN_H = 30

EXIT_CONF = 10
EXIT_FOLDER_UNSET = 11
EXIT_NOT_A_FOLDER = 12
EXIT_SLOTS_MISSING = 13
EXIT_NO_OPENSSL = 14
EXIT_KEYFILE = 15
EXIT_READBACK = 30
EXIT_NOTHING = 20
EXIT_INTEGRITY = 40
EXIT_SOURCE_VANISHED = 41
EXIT_CRYPTO = 42


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


def need(conf, key, why):
    v = conf.get(key)
    if not v:
        die(EXIT_CONF, "%s= is not set in %s — %s. This script never guesses a"
                       " path, an id or a key." % (key, CONF_PATH, why))
    return v


def work_dir(conf):
    d = conf.get("WORK_DIR") or os.path.join(os.path.dirname(CONF_PATH) or "/tmp",
                                             "work")
    if not os.path.isdir(d):
        os.makedirs(d, 0o700)
    return d


def state_path(conf):
    return conf.get("STATE_FILE") or os.path.join(
        os.path.dirname(CONF_PATH) or "/tmp", "clinic_state_backup.state.json")


def summary_path(conf):
    return conf.get("SUMMARY_FILE") or os.path.join(
        os.path.dirname(CONF_PATH) or "/tmp", "clinic_state_backup.summary.log")


def csv_conf(conf, key, default):
    raw = conf.get(key) or default
    return tuple(p.strip() for p in raw.split(",") if p.strip())


# ----------------------------------------------------------------- state ----
def load_state(conf):
    p = state_path(conf)
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception as ex:
            log("WARNING: state file unreadable (%s) — treating as first run" % ex)
    return {}


def save_state(conf, st):
    p = state_path(conf)
    tmp = p + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh, indent=2, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, p)


def append_summary(conf, line):
    try:
        with open(summary_path(conf), "a") as fh:
            fh.write(line.rstrip("\n") + "\n")
    except OSError as ex:
        log("WARNING: could not write the summary line:", ex)


# ------------------------------------------------------------ primitives ----
def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def is_secret(name):
    low = os.path.basename(name).lower()
    for pat in SECRET_PATTERNS:
        if fnmatch.fnmatch(low, pat):
            return True
    return False


def is_sqlite(path):
    try:
        with open(path, "rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def sqlite_integrity(path):
    """PRAGMA integrity_check, read-only. Returns the answer; 'ok' is the only
    acceptable one."""
    try:
        c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    except sqlite3.Error as ex:
        return "unopenable: %s" % ex
    try:
        return c.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.DatabaseError as ex:
        # a file that carries the sqlite header but cannot be read at all is
        # not 'an error to report later' — it is a failed integrity check.
        return "unreadable: %s" % ex
    finally:
        c.close()


def sqlite_backup(src, dst):
    """The sqlite ONLINE BACKUP api — the same thing the sqlite3 shell's
    '.backup' runs. Never a file copy: a live database copied byte-wise while a
    writer holds it is a torn database that verifies today and fails in a year."""
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    try:
        s.backup(d)
    finally:
        d.close()
        s.close()


def sqlite_schema(path):
    """A schema-only dump, exactly what the shell's '.schema' prints, so a
    corrupt file can still be read structurally."""
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    try:
        rows = c.execute("SELECT type, name, sql FROM sqlite_master"
                         " WHERE sql IS NOT NULL ORDER BY type, name").fetchall()
    finally:
        c.close()
    out = ["-- .schema of %s" % os.path.basename(path),
           "-- taken %s" % time.strftime("%Y-%m-%d %H:%M:%S"), ""]
    for _t, _n, sql in rows:
        out.append(sql.rstrip().rstrip(";") + ";")
    return "\n".join(out) + "\n"


def openssl_ok():
    try:
        r = subprocess.run([OPENSSL, "version"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=30)
        return r.returncode == 0, r.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError) as ex:
        return False, str(ex)


def check_keyfile(conf):
    kf = need(conf, "ENC_KEY_FILE",
              "the encryption key file is generated by the installer and its"
              " path is site configuration")
    if not os.path.exists(kf):
        die(EXIT_KEYFILE, "the encryption key file named in the conf does not"
                          " exist. Generate it once (see INSTALL_ONE_PASTE) and"
                          " copy it to the cold store — A BACKUP WHOSE KEY IS"
                          " LOST IS UNRECOVERABLE.")
    if os.path.getsize(kf) < 16:
        die(EXIT_KEYFILE, "the encryption key file is shorter than 16 bytes —"
                          " that is not a key. Regenerate it.")
    mode = stat.S_IMODE(os.stat(kf).st_mode)
    if mode & 0o077:
        die(EXIT_KEYFILE, "the encryption key file is mode %o — it must be 600."
                          " Refusing to use a key the whole box can read." % mode)
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


# ---------------------------------------------------------------- gather ----
class Gathered(object):
    def __init__(self):
        self.root = None
        self.entries = []        # (relpath, bytes, mtime, source_or_'-')
        self.secrets_skipped = 0
        self.oversize_skipped = 0
        self.sources_present = []
        self.sources_missing = []
        self.databases = []      # (source_path, integrity_answer)


def _walk_dir_data(d):
    """Discover the actual data files under a store — never hard-code names.
    Secrets are matched by pattern FIRST, so they are counted as skipped even
    when the extension filter would have dropped them anyway."""
    out, secrets = [], 0
    for base, dirs, files in os.walk(d):
        dirs[:] = sorted(x for x in dirs if x not in DIR_SKIP_NAMES)
        for name in sorted(files):
            full = os.path.join(base, name)
            if is_secret(name):
                secrets += 1
                continue
            if not name.lower().endswith(DIR_DATA_EXT):
                continue
            if not os.path.isfile(full):
                continue
            out.append(full)
    return out, secrets


def gather(conf, dest_root, integrity_fatal=True):
    """Copy every included thing into dest_root. Databases go through the
    sqlite online-backup api; secrets are skipped by pattern and counted."""
    g = Gathered()
    g.root = dest_root
    max_bytes = int(float(conf.get("MAX_FILE_MB") or MAX_FILE_MB_DEFAULT) * 1024 * 1024)
    data_dir = os.path.join(dest_root, "data")
    shape_dir = os.path.join(dest_root, "shape")
    schema_dir = os.path.join(shape_dir, "schema")
    for d in (data_dir, shape_dir, schema_dir):
        os.makedirs(d, exist_ok=True)

    def take(src, rel_prefix):
        name = os.path.basename(src)
        if is_secret(name):
            g.secrets_skipped += 1
            return
        if not os.path.isfile(src):
            g.sources_missing.append(src)
            return
        size = os.path.getsize(src)
        if size > max_bytes:
            g.oversize_skipped += 1
            log("WARNING: skipping %s — %.1f MB is over the MAX_FILE_MB guard"
                % (name, size / 1048576.0))
            return
        mt = os.path.getmtime(src)
        rel = os.path.join(rel_prefix, name) if rel_prefix else name
        dst = os.path.join(data_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if is_sqlite(src):
            answer = sqlite_integrity(src)
            g.databases.append((src, answer))
            if answer != "ok":
                if integrity_fatal:
                    die(EXIT_INTEGRITY, "%s failed integrity_check (said %r) —"
                                        " NOTHING is shipped. Fix or restore the"
                                        " database first." % (name, answer))
                log("INTEGRITY FAIL:", name, "said", repr(answer))
                return
            sqlite_backup(src, dst)
            try:
                with open(os.path.join(schema_dir, name + ".schema.sql"), "w") as fh:
                    fh.write(sqlite_schema(src))
            except Exception as ex:
                log("WARNING: schema dump failed for", name, ":", ex)
        else:
            shutil.copy2(src, dst)
        g.sources_present.append(src)
        g.entries.append((os.path.join("data", rel), os.path.getsize(dst), mt, src))

    for src in SRC_FILES:
        take(src, "")

    for d in SRC_DIRS:
        if not os.path.isdir(d):
            g.sources_missing.append(d)
            continue
        label = os.path.basename(d.rstrip("/"))
        found, sec = _walk_dir_data(d)
        g.secrets_skipped += sec
        if not found:
            log("WARNING: no *.db / *.csv data files found under", d)
        for src in found:
            take(src, label)

    _gather_shape(conf, shape_dir, g)
    _write_inventory(dest_root, g)
    return g


def _gather_shape(conf, shape_dir, g):
    # 1 · crontab
    try:
        r = subprocess.run(CRONTAB_CMD, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=60)
        text = r.stdout.decode("utf-8", "replace")
        if r.returncode != 0:
            text = "-- crontab -l returned %d --\n%s" % (r.returncode, text)
    except (OSError, subprocess.SubprocessError) as ex:
        text = "-- crontab -l could not run: %s --\n" % ex
        log("WARNING: crontab -l could not run:", ex)
    p = os.path.join(shape_dir, "crontab.txt")
    with open(p, "w") as fh:
        fh.write(text)
    g.entries.append(("shape/crontab.txt", os.path.getsize(p),
                      os.path.getmtime(p), "crontab -l"))

    # 2 · the clinic systemd units, discovered by name
    units = csv_conf(conf, "UNIT_MATCH", UNIT_MATCH_DEFAULT)
    sysd = conf.get("SYSTEMD_DIR") or SYSTEMD_DIR
    udir = os.path.join(shape_dir, "systemd")
    os.makedirs(udir, exist_ok=True)
    if os.path.isdir(sysd):
        for name in sorted(os.listdir(sysd)):
            if not name.endswith((".service", ".timer")):
                continue
            stem = name.rsplit(".", 1)[0].lower()
            if not any(stem.startswith(u.lower()) or u.lower() in stem for u in units):
                continue
            src = os.path.join(sysd, name)
            if not os.path.isfile(src) or is_secret(name):
                continue
            dst = os.path.join(udir, name)
            shutil.copy2(src, dst)
            g.entries.append((os.path.join("shape", "systemd", name),
                              os.path.getsize(dst), os.path.getmtime(src), src))
    else:
        log("WARNING: no", sysd, "— unit files not collected")

    # 3 · the OpenLiteSpeed vhost configs the clinic uses
    vmatch = csv_conf(conf, "VHOST_MATCH", VHOST_MATCH_DEFAULT)
    vhd = conf.get("VHOST_DIR") or VHOST_DIR
    vdir = os.path.join(shape_dir, "vhosts")
    os.makedirs(vdir, exist_ok=True)
    if os.path.isdir(vhd):
        for dom in sorted(os.listdir(vhd)):
            if not any(m.lower() in dom.lower() for m in vmatch):
                continue
            src = os.path.join(vhd, dom, "vhost.conf")
            if not os.path.isfile(src):
                continue
            dst = os.path.join(vdir, dom + ".vhost.conf")
            shutil.copy2(src, dst)
            g.entries.append((os.path.join("shape", "vhosts", dom + ".vhost.conf"),
                              os.path.getsize(dst), os.path.getmtime(src), src))
    else:
        log("WARNING: no", vhd, "— vhost configs not collected")

    # 4 · the schema dumps written during gather()
    schema_dir = os.path.join(shape_dir, "schema")
    for name in sorted(os.listdir(schema_dir)):
        p = os.path.join(schema_dir, name)
        g.entries.append((os.path.join("shape", "schema", name),
                          os.path.getsize(p), os.path.getmtime(p), "sqlite .schema"))


def _write_inventory(dest_root, g):
    """Plain text: every file included, its path, size and mtime."""
    lines = ["# clinic_state_backup inventory · %s"
             % time.strftime("%Y-%m-%d %H:%M:%S"),
             "# path_in_bundle\tbytes\tsource_mtime\tsource",
             ""]
    total = 0
    for rel, size, mt, src in sorted(g.entries):
        total += size
        lines.append("%s\t%d\t%s\t%s"
                     % (rel, size, time.strftime("%Y-%m-%d %H:%M:%S",
                                                 time.localtime(mt)), src))
    lines += ["",
              "# files: %d" % len(g.entries),
              "# bytes (uncompressed): %d" % total,
              "# secrets skipped by pattern: %d" % g.secrets_skipped,
              "# oversize files skipped: %d" % g.oversize_skipped,
              "# sources missing: %d" % len(g.sources_missing),
              "# EXCLUDED by design: application code (GitHub), OS and packages",
              "#   (provider snapshot), /root/assetapp/uploads/, and every secret.",
              ""]
    p = os.path.join(dest_root, "INVENTORY.txt")
    with open(p, "w") as fh:
        fh.write("\n".join(lines))
    g.entries.append(("INVENTORY.txt", os.path.getsize(p),
                      os.path.getmtime(p), "generated"))


def tar_gz(src_root, out_path, arcname):
    with tarfile.open(out_path, "w:gz", compresslevel=6) as tf:
        for base, dirs, files in os.walk(src_root):
            dirs.sort()
            for name in sorted(files):
                full = os.path.join(base, name)
                rel = os.path.relpath(full, src_root)
                tf.add(full, arcname=os.path.join(arcname, rel))
    os.chmod(out_path, 0o600)
    return out_path


# ----------------------------------------------------------------- drive ----
def make_session(sa_json):
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    creds = Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive"])
    return AuthorizedSession(creds)


class Drive:
    """The same six Drive calls the S213 sibling needs, and nothing else."""
    API = "https://www.googleapis.com/drive/v3"
    UP = "https://www.googleapis.com/upload/drive/v3"

    def __init__(self, session):
        self.s = session

    def _ck(self, r, what):
        if r.status_code >= 300:
            raise RuntimeError("%s -> HTTP %s: %s" % (what, r.status_code, r.text[:300]))
        return r

    def about(self):
        r = self._ck(self.s.get(self.API + "/about",
                                params={"fields": "user(emailAddress)"}), "about")
        return r.json()

    def folder(self, folder_id):
        r = self._ck(self.s.get(self.API + "/files/" + folder_id,
                                params={"fields": "id,name,mimeType"}), "folder get")
        return r.json()

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

    def update_content(self, file_id, path):
        """Resumable content update of an EXISTING file (PATCH), streamed."""
        size = os.path.getsize(path)
        r = self._ck(self.s.patch(
            self.UP + "/files/%s?uploadType=resumable&fields=id,size,md5Checksum" % file_id,
            headers={"Content-Type": "application/json; charset=UTF-8",
                     "X-Upload-Content-Length": str(size)},
            data=json.dumps({})), "update initiate")
        loc = r.headers.get("Location")
        if not loc:
            raise RuntimeError("update initiate returned no session URI")
        with open(path, "rb") as f:
            r = self._ck(self.s.put(loc, data=f,
                                    headers={"Content-Length": str(size)}),
                         "update bytes")
        return r.json()

    def patch_meta(self, file_id, body):
        r = self._ck(self.s.patch(self.API + "/files/" + file_id,
                                  headers={"Content-Type": "application/json"},
                                  params={"fields": "id,name,description"},
                                  data=json.dumps(body)), "meta patch")
        return r.json()

    def get(self, file_id):
        r = self._ck(self.s.get(self.API + "/files/" + file_id,
                                params={"fields": "id,name,size,md5Checksum,description"}),
                     "file get")
        return r.json()

    def revisions(self, file_id):
        r = self._ck(self.s.get(self.API + "/files/%s/revisions" % file_id,
                                params={"fields": "revisions(id,modifiedTime,keepForever)",
                                        "pageSize": "1000"}), "revisions")
        return r.json().get("revisions", [])

    def pin_revision(self, file_id, rev_id):
        self._ck(self.s.patch(self.API + "/files/%s/revisions/%s" % (file_id, rev_id),
                              headers={"Content-Type": "application/json"},
                              data=json.dumps({"keepForever": True})), "revision pin")


PIN_WARN = 180      # Drive caps pinned revisions at 200 per file


def find_slots(d, folder_id):
    files = {f["name"]: f for f in d.list(folder_id)}
    missing = [n for n in (NIGHTLY, MONTHLY) if n not in files]
    if missing:
        die(EXIT_SLOTS_MISSING,
            "slot file(s) missing in the Drive folder:", ", ".join(missing),
            "— they are owner-owned and must exist (created once from the owner's"
            " account); the service account cannot create them (zero quota).")
    return files[NIGHTLY], files[MONTHLY]


def _connect(folder_required=True):
    if not os.path.exists(CONF_PATH):
        die(EXIT_CONF, "no conf at", CONF_PATH,
            "— the installer writes it; this script never invents one.")
    conf = load_conf()
    sa = need(conf, "SA_JSON", "the service-account json is site configuration")
    if not os.path.exists(sa):
        die(EXIT_CONF, "SA_JSON in the conf points at a file that does not exist.")
    fid = conf.get("FOLDER_ID")
    if folder_required and not fid:
        die(EXIT_FOLDER_UNSET, "FOLDER_ID= is not set in", CONF_PATH)
    return conf, sa, fid


# ----------------------------------------------------------------- modes ----
def preflight(drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect(folder_required=False)
    work = work_dir(conf)

    ok, ver = openssl_ok()
    if not ok:
        die(EXIT_NO_OPENSSL,
            "openssl is not usable (%s). This bundle carries patient and staff"
            " financial data and MUST NOT leave the box in the clear (F-31)."
            " Install openssl, or the job stays off." % ver)
    log("openssl:", ver)

    kf = check_keyfile(conf)
    log("key file: present, mode 600 ·", os.path.getsize(kf), "bytes"
        " (its path and content are never printed)")
    try:
        crypto_roundtrip(kf, work)
    except Exception as ex:
        die(EXIT_CRYPTO, "encryption round trip FAILED:", ex)
    log("encrypt -> decrypt -> compare: OK (AES-256-CBC, PBKDF2 200k)")

    # sources and integrity, without shipping anything
    stage = tempfile.mkdtemp(prefix="preflight_", dir=work)
    try:
        g = gather(conf, stage, integrity_fatal=False)
        bad = [(os.path.basename(p), a) for p, a in g.databases if a != "ok"]
        for src, answer in g.databases:
            log("database:", os.path.basename(src), "integrity_check ->", answer)
        for m in g.sources_missing:
            log("WARNING: source not present:", m)
        log("would include %d files · %d secrets skipped by pattern · %d oversize"
            % (len(g.entries), g.secrets_skipped, g.oversize_skipped))
        if bad:
            die(EXIT_INTEGRITY, "%d database(s) fail integrity_check: %s"
                % (len(bad), ", ".join(n for n, _a in bad)))
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    st = load_state(conf)
    if st.get("last_success_iso"):
        log("last success:", st["last_success_iso"], "·", st.get("bytes", "?"),
            "bytes ·", st.get("files_included", "?"), "files")
    else:
        log("state file: none yet — this box has never completed a run")

    email = json.load(open(sa)).get("client_email", "?")
    log("service account identity:", email)
    d = drive_cls(session_maker(sa))
    ab = d.about()
    log("drive reachable as:", ab.get("user", {}).get("emailAddress", "?"))
    if not fid:
        log("OWNER STEP: share the folder with the identity above (Editor) and"
            " put its id in", CONF_PATH)
        sys.exit(EXIT_FOLDER_UNSET)
    f = d.folder(fid)
    if f.get("mimeType") != "application/vnd.google-apps.folder":
        die(EXIT_NOT_A_FOLDER, "FOLDER_ID is not a folder:", f)
    log("folder visible:", f.get("name"), "(%s)" % fid)
    nightly, monthly = find_slots(d, fid)
    log("slot files found:", NIGHTLY, "·", MONTHLY)
    stamp = "preflight write-test %s" % time.strftime("%F %T")
    d.patch_meta(nightly["id"], {"description": (nightly.get("description") or "")
                                 [:900] + " | " + stamp})
    log("metadata write on", NIGHTLY, ": OK (content untouched, no revision made)")
    log("PREFLIGHT OK — ready for 'run'")


def run(drive_cls=Drive, session_maker=make_session, now=None):
    now = now or time.localtime()
    conf, sa, fid = _connect()
    work = work_dir(conf)
    prev = load_state(conf)

    ok, ver = openssl_ok()
    if not ok:
        die(EXIT_NO_OPENSSL, "openssl is not usable (%s) — refusing to ship"
                             " patient and staff data in the clear (F-31)." % ver)
    kf = check_keyfile(conf)

    stage = tempfile.mkdtemp(prefix="bundle_", dir=work)
    tmpdir = tempfile.mkdtemp(prefix="ship_", dir=work)
    try:
        # ---- gather + verify (integrity failure is fatal inside gather) -----
        g = gather(conf, stage, integrity_fatal=True)
        if not g.entries:
            die(EXIT_NOTHING, "nothing was gathered — refusing to ship an empty"
                              " bundle over a good one.")
        for src, answer in g.databases:
            log("verified:", os.path.basename(src), "integrity_check ->", answer)

        # ---- a source that was there last time and is gone now is fatal -----
        was = set(prev.get("sources") or [])
        vanished = sorted(was - set(g.sources_present))
        if vanished:
            die(EXIT_SOURCE_VANISHED,
                "%d source(s) present on the last successful run are missing"
                " now: %s — that is a change to the estate, not a backup"
                " decision. Investigate, then re-run."
                % (len(vanished), ", ".join(vanished)))

        log("gathered %d files · %d secrets skipped by pattern · %d oversize"
            " skipped · %d source(s) absent (and absent last time too)"
            % (len(g.entries), g.secrets_skipped, g.oversize_skipped,
               len(g.sources_missing)))

        # ---- tar + gzip -----------------------------------------------------
        arc = "clinic_state_%s" % time.strftime("%Y-%m-%d", now)
        tar = tar_gz(stage, os.path.join(tmpdir, arc + ".tar.gz"), arc)
        tar_md5 = md5_file(tar)
        log("bundle: %s · %d bytes (gz)" % (arc + ".tar.gz", os.path.getsize(tar)))

        # ---- encrypt, then PROVE the round trip on the real artefact --------
        enc = encrypt_file(tar, os.path.join(tmpdir, arc + ".tar.gz.enc"), kf)
        back = os.path.join(tmpdir, "verify.tar.gz")
        try:
            decrypt_file(enc, back, kf)
        except Exception as ex:
            die(EXIT_CRYPTO, "the encrypted bundle DOES NOT DECRYPT:", ex,
                "— nothing shipped.")
        if md5_file(back) != tar_md5:
            die(EXIT_CRYPTO, "the encrypted bundle decrypts to different bytes —"
                             " nothing shipped.")
        os.unlink(back)
        local_md5 = md5_file(enc)
        size = os.path.getsize(enc)
        log("encrypted: %d bytes · AES-256-CBC/PBKDF2 · round trip proven"
            " · md5 %s" % (size, local_md5))

        # ---- ship -----------------------------------------------------------
        d = drive_cls(session_maker(sa))
        nightly, monthly = find_slots(d, fid)
        d.update_content(nightly["id"], enc)
        got = d.get(nightly["id"])
        if got.get("md5Checksum") != local_md5 or int(got.get("size", -1)) != size:
            die(EXIT_READBACK,
                "nightly update DID NOT VERIFY (drive md5 %s vs local %s) —"
                " monthly untouched; the previous good version is still in the"
                " file's revision history" % (got.get("md5Checksum"), local_md5))
        desc = ("encrypted clinic state · %d files · md5 %s · %d bytes ·"
                " shipped %s" % (len(g.entries), local_md5, size,
                                 time.strftime("%F %T")))
        d.patch_meta(nightly["id"], {"description": desc})
        log("shipped -> %s · verified by read-back" % NIGHTLY)

        # ---- monthly: first verified run of the month, pinned forever -------
        mtag = time.strftime("%Y-%m", now)
        monthly_done = False
        if ("month=%s" % mtag) not in (monthly.get("description") or ""):
            d.update_content(monthly["id"], enc)
            mg = d.get(monthly["id"])
            if mg.get("md5Checksum") == local_md5:
                revs = d.revisions(monthly["id"])
                if revs:
                    try:
                        d.pin_revision(monthly["id"], revs[-1]["id"])
                        log("monthly copy for", mtag, "shipped and PINNED (kept forever)")
                        monthly_done = True
                    except Exception as ex:
                        log("WARNING: monthly shipped but pin failed:", ex)
                pins = sum(1 for r in d.revisions(monthly["id"]) if r.get("keepForever"))
                if pins >= PIN_WARN:
                    log("WARNING: %d pinned revisions on %s — Drive caps at 200;"
                        " plan a second monthly file" % (pins, MONTHLY))
                d.patch_meta(monthly["id"],
                             {"description": "month=%s · %s" % (mtag, desc)})
            else:
                log("WARNING: monthly update did not verify — its previous"
                    " version still stands in revision history; the nightly"
                    " above is good")

        # ---- the state file: a backup must be able to state its own age -----
        st = {
            "last_success_iso": time.strftime("%Y-%m-%dT%H:%M:%S", now),
            "last_success_epoch": int(time.time()),
            "bytes": size,
            "md5": local_md5,
            "files_included": len(g.entries),
            "secrets_skipped": g.secrets_skipped,
            "oversize_skipped": g.oversize_skipped,
            "databases_verified": len(g.databases),
            "sources": sorted(g.sources_present),
            "sources_missing": sorted(g.sources_missing),
            "monthly_month": mtag if monthly_done else prev.get("monthly_month", ""),
            "nightly_slot": NIGHTLY,
            "monthly_slot": MONTHLY,
            "kit": "S230_STATE_BACKUP",
        }
        save_state(conf, st)
        line = ("%s OK files=%d bytes=%d md5=%s secrets_skipped=%d monthly=%s"
                % (st["last_success_iso"], st["files_included"], st["bytes"],
                   st["md5"], st["secrets_skipped"],
                   "yes" if monthly_done else "no"))
        append_summary(conf, line)
        log("state written:", state_path(conf))
        log("SUMMARY:", line)

        nrev = len(d.revisions(nightly["id"]))
        log("held on Drive: %s (%d revisions ~ restore points) · %s (monthly, pinned)"
            % (NIGHTLY, nrev, MONTHLY))
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        shutil.rmtree(tmpdir, ignore_errors=True)


def list_mode(drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect()
    st = load_state(conf)
    if st.get("last_success_epoch"):
        age_h = (time.time() - st["last_success_epoch"]) / 3600.0
        log("last success: %s · %.1f h ago · %d bytes · %d files · md5 %s"
            % (st.get("last_success_iso"), age_h, st.get("bytes", 0),
               st.get("files_included", 0), st.get("md5", "?")))
        if age_h > STALE_WARN_H:
            log("WARNING: that is older than %d h — this backup is STALE."
                % STALE_WARN_H)
    else:
        log("state file: none — no successful run has been recorded on this box.")
    d = drive_cls(session_maker(sa))
    for f in sorted(d.list(fid), key=lambda f: f["name"]):
        log(f["name"], f.get("size", "?"), "bytes", f.get("md5Checksum", ""),
            "·", (f.get("description") or "")[:80])
    n, _m = find_slots(d, fid)
    log("nightly revisions:", len(d.revisions(n["id"])))


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "preflight":
        preflight()
    elif mode == "run":
        run()
    elif mode == "list":
        list_mode()
    else:
        print("usage: clinic_state_backup.py preflight|run|list")
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
