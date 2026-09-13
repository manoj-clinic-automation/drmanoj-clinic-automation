#!/root/wa/venv/bin/python3
# =============================================================================
#  code_bundle.py  .  Session 243  .  S243_CODE_BUNDLE  .  v1.2
#
#  THE OFF-BOX LEG OF THE LIVE CODE.
#
#  finance.db has had a nightly off-box copy since S213 (finance_drive_backup.py,
#  cron 01:40, into the FinanceDB_Backups Drive folder). The CODE that reads it
#  has none: /root/finance/finance_app.py is a base plus twelve patches applied
#  on the box, and that exact file exists nowhere but the box. Same for the
#  portal, the Marg ingest, the WA console, the staff register. GitHub holds
#  the kits, not the assembled result. This script closes that gap the same
#  way S213 did for the database: one owner-owned slot file on Drive,
#  overwritten every night, Drive's revision history as the archive.
#
#  WHAT IS TAKEN (see SOURCES below): code, templates, SQL, shell, unit files
#  and the root crontab. WHAT IS NEVER TAKEN (HARD_EXCLUDES / EXCLUDE_DIRS):
#  any .env, any .conf, any database, any log, any .bak, any token or key
#  json, any *config*.py, the portal user file (password hashes), the staff
#  settings/advances files, anything under _retired / __pycache__ / backups /
#  deploy. The excludes are applied AFTER the include patterns, so a pattern
#  can never pull a secret in.
#
#  v1.1 (S243, after the first live bundle of 07:19 was inspected): that bundle
#  carried portal_config.py, att_config.py and freshness.conf -- literal
#  passwords, tokens, seeds, salts and a live ntfy topic. Standing hold:
#  SECRETS NEVER GO TO CLOUD STORAGE. So, three new walls:
#    * *config*.py and *_config.py are hard-excluded by name
#    * *.conf are no longer a source at all (this script reads its own conf
#      from disk; it never needed to ship it)
#    * EVERY candidate file is read and scanned with the repository's own
#      publish-gate credential heuristic (NO_PHONE_NUMBERS.py, ported below):
#      a file the gate would refuse is left out and the SUMMARY names it
#      (excluded_secret=N (basenames)).
#
#  v1.2 (S243, same day): v1.1's own blunt pattern excluded finance_app.py,
#  purchase_app.py, finance_patient_match.py, clinic_sso.py and
#  portal_console.py on the live box (constants like TOKEN_HEADER = "X-...")
#  and the FATAL guard fired -- the installer rolled back as designed. The
#  scan is now the gate's, which knows a constant, a path, a filename, a
#  placeholder and a hash pin from a credential; and att_config.py /
#  portal_config.py are named outright in BASENAME_EXCLUDES.
#
#  The Drive half is REUSED from finance_drive_backup.py (S213 v2, pin
#  14b406773de7f196abb105114f346080): load_conf, find_sa_json, make_session,
#  the Drive class, md5_file, _connect and the list mode are that file's,
#  unchanged in behaviour. Same conf (/root/finance/drive_backup.conf), same
#  service-account key discovery, same folder, same update-in-place with a
#  read-back md5 check. WHY update-in-place: a service account has ZERO Drive
#  quota (HTTP 403 on create, proven live 31-Aug-2026); it may only write new
#  CONTENT into a file the owner already owns. So the slot file
#  code_nightly.tar.gz must be created ONCE from the owner's account inside
#  the same folder as finance_nightly.db.gz. If it is missing, run stops with
#  exit 13 and names it; list says MISSING.
#
#  Modes:
#    build   build the tarball, verify its own manifest, keep the local copy
#            at /root/state_backup/code_nightly.tar.gz, print the summary.
#            NO network. This is the installer smoke and the selftest path.
#    run     build, then overwrite the Drive slot and read it back.
#    list    what is in the Drive folder, whether the slot exists, its
#            revision count. Read-only.
#
#  ROOT: every path below is rooted at the environment variable ROOT
#  (default "/"). The selftest points ROOT at a mock tree; on the box it is
#  unset. The conf and the local copy are under ROOT too, so a test never
#  touches the real box.
#
#  Cron (after the db leg, before the state leg):
#    35 1 * * * /root/wa/venv/bin/python3 /root/state_backup/code_bundle.py run >> /root/state_backup/code_bundle.log 2>&1 # S243_CODE_BUNDLE
#
#  No patient data, no numbers, no secrets in this file (F-185).
# =============================================================================
import fnmatch
import hashlib
import io
import json
import os
import re
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)   # google-auth py3.9 EOL noise

KIT      = "S243_CODE_BUNDLE"
ROOT     = os.environ.get("ROOT", "/") or "/"
SLOT     = "code_nightly.tar.gz"
MANIFEST = "MANIFEST.md5"
CRONFILE = "crontab.txt"
INFOFILE = "BUNDLE_INFO.txt"
KEYFILE  = "root/finance/finance_app.py"     # the bundle is pointless without it

def under_root(rel):
    return os.path.join(ROOT, rel.lstrip("/"))

CONF_PATH = under_root("root/finance/drive_backup.conf")   # same conf as the db leg
OUT_DIR   = under_root("root/state_backup")
OUT_PATH  = os.path.join(OUT_DIR, SLOT)

# --- what goes in: (directory relative to ROOT, name patterns, recurse,
#     substrings that exclude a file name inside THAT directory) -------------
SOURCES = [
    ("root/finance",                 ("*.py", "*.sql", "*.html", "*.sh"),           False, ()),
    ("root/finance/finance_ui",      ("*.html",),                                    False, ()),
    ("root/portal",                  ("*.py", "*.html", "*.json"),                   False, ("users", "secret")),
    ("root/marg_ingest",             ("*.py", "*.json"),                             False, ()),
    ("root/marg_ingest/lib",         ("*",),                                         True,  ()),
    ("root/wa",                      ("*.py",),                                      False, ()),
    ("root/wa/call-hook",            ("*.py",),                                      False, ()),
    ("root/wa/recordings-archive",   ("*.py",),                                      False, ()),
    ("root/staff_register",          ("*.py", "*.json"),                             False, ("settings", "advances")),
    ("root/staff_ledger_reconcile",  ("*.py",),                                      False, ()),
    ("root/state_backup",            ("*.py",),                                      False, ()),
    ("root",                         ("*.py",),                                      False, ()),
    ("etc/systemd/system",           ("clinic-*.service", "clinic-*.timer",
                                      "wa-*.service", "call-*.service"),            False, ()),
]

# --- what never goes in, whatever the pattern said (fnmatch on the file name)
HARD_EXCLUDES = (".env*", "*.env", "*.conf", "*.db*", "*.log", "*.bak*", "token*",
                 "*key*.json", "patient_fp.env", "*config*.py", "*_config.py")
# --- an explicit basename wall: the two files the first live bundle carried.
#     att_config.py holds its literals in a shape the heuristic below does
#     not flag, so it is named here outright (v1.2).
BASENAME_EXCLUDES = ("att_config.py", "portal_config.py")

# =============================================================================
#  CONTENT SCAN -- ported from the repository's own publish gate,
#  deploy_kits/NO_PHONE_NUMBERS.py (S231 census, credential layer): the
#  regexes BEARER / PRIVKEY / SECRET_ASSIGN / PLACEHOLDER / ALLCAPS_NAME /
#  HASH_PIN / FILENAME_VAL / FILEISH_NAME / SECRET_WORD / SECRET_CAMEL and the
#  functions name_is_secret_shaped / benign_secret / scan_secrets_text are that
#  file's, copied verbatim (v1.2). A file is excluded from the bundle exactly
#  when the gate itself would refuse to publish it. v1.1 used a blunter
#  pattern and, live, excluded finance_app.py on a line like
#  TOKEN_HEADER = "X-..." -- a name held as a constant, which the gate's
#  benign_secret() rules out. Nothing here ever prints a value.
# =============================================================================
BEARER = re.compile(r"(?i)\bbearer\s+([A-Za-z0-9_\-\.=+/]{16,})")
PRIVKEY = re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")
SECRET_ASSIGN = re.compile(
    r"(?i)\b([A-Za-z0-9_]*"
    r"(?:TOKEN|SECRET|API_?KEY|PASSWORD|PASSWD|PWD|AUTH)"
    r"[A-Za-z0-9_]*)['\"]?\s*[:=]\s*(['\"])([^'\"\n]*)\2")

PLACEHOLDER = re.compile(
    r"(?i)(put|paste|here|mask|xxxx|todo|change[-_ ]?(this|me|it)|your[_ -]"
    r"|example|dummy|sample|redact|<|>|\u00ab|\u00bb|\u2026|\.\.\.)")
ALLCAPS_NAME = re.compile(r"[A-Z][A-Z0-9_]*$")
HASH_PIN = re.compile(r"(?:[0-9a-fA-F]{16}|[0-9a-fA-F]{32}"
                      r"|[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
FILENAME_VAL = re.compile(r"[\w.-]+\.[A-Za-z0-9]{1,6}$")
FILEISH_NAME = re.compile(r"(?i).*(_FILE|_PATH|FILENAME|_DIR)$")

SECRET_MIN = 16   # shorter than this is not a live credential worth a halt

# The keyword must be a WHOLE COMPONENT of the name, not a fragment of a word.
SECRET_WORD = re.compile(
    r"(?i)(?:^|[_\-])(token|secret|api_?key|password|passwd|pwd|auth)(?:$|[_\-])")
SECRET_CAMEL = re.compile(
    r"(?:^|[a-z0-9])(Token|Secret|ApiKey|Password|Passwd|Auth)(?:$|[A-Z_\-])")


def name_is_secret_shaped(name):
    return bool(SECRET_WORD.search(name) or SECRET_CAMEL.search(name))


def benign_secret(name, value):
    """Why this assignment is NOT a credential -- or None if it looks like one.
    Every branch here was earned by a real line in the repository (gate)."""
    v = value.strip()
    if len(v) < SECRET_MIN:
        return "too short"
    if ALLCAPS_NAME.match(v):
        return "a name held as a constant"
    if "/" in v or "\\" in v:
        return "a path"
    if FILEISH_NAME.match(name) or FILENAME_VAL.match(v):
        return "a filename"
    if PLACEHOLDER.search(v):
        return "a placeholder"
    if HASH_PIN.match(v):
        return "a hash pin"
    if "{" in v or "%s" in v or "$" in v:
        return "interpolated, not a literal"
    return None


def scan_secrets_text(text):
    """[(line, kind)] -- never the value. (gate: scan_secrets_text, minus the
    length string this bundle has no use for)"""
    out = []
    for m in PRIVKEY.finditer(text):
        out.append((text[:m.start()].count("\n") + 1, "PRIVATE KEY BLOCK"))
    for m in BEARER.finditer(text):
        v = m.group(1)
        if PLACEHOLDER.search(v):
            continue
        out.append((text[:m.start()].count("\n") + 1, "Authorization: Bearer"))
    for m in SECRET_ASSIGN.finditer(text):
        name, v = m.group(1), m.group(3)
        if not name_is_secret_shaped(name):
            continue
        if benign_secret(name, v):
            continue
        out.append((text[:m.start()].count("\n") + 1, "%s = <literal>" % name))
    return out

# --- a path component that disqualifies the whole path
EXCLUDE_DIRS = ("_retired", "_retired_*", "__pycache__", "backups", "deploy")

SA_SEARCH = [
    "/root/wa/patient-mirror-key.json",
    "/root/wa/service_account.json",
    "/root/wa/credentials.json",
    "/root/.config/gspread/service_account.json",
]

def log(*a):
    print("[%s]" % time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)

def die(code, *a):
    log("FATAL:", *a)
    sys.exit(code)

# ---------------------------------------------------------------- config ----
# (reused from finance_drive_backup.py S213 v2 -- load_conf, find_sa_json)
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
    if conf.get("SA_JSON") and os.path.exists(conf["SA_JSON"]):
        return conf["SA_JSON"]
    found = [p for p in SA_SEARCH if os.path.exists(p)]
    try:
        for name in sorted(os.listdir("/root/wa")):
            if name.endswith(".json"):
                p = os.path.join("/root/wa", name)
                if p not in found:
                    try:
                        if json.load(open(p)).get("type") == "service_account":
                            found.append(p)
                    except Exception:
                        pass
    except OSError:
        pass
    return found[0] if found else None

# ----------------------------------------------------------------- drive ----
# (reused from finance_drive_backup.py S213 v2 -- make_session, class Drive)
def make_session(sa_json):
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    creds = Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive"])
    return AuthorizedSession(creds)

class Drive:
    """The Drive calls this job needs, and nothing else (S213 v2)."""
    API = "https://www.googleapis.com/drive/v3"
    UP  = "https://www.googleapis.com/upload/drive/v3"

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

# ---------------------------------------------------------------- verify ----
def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def md5_bytes(data):
    return hashlib.md5(data).hexdigest()

# --------------------------------------------------------------- gather -----
def _name_excluded(name):
    if name in BASENAME_EXCLUDES:
        return True
    for pat in HARD_EXCLUDES:
        if fnmatch.fnmatch(name, pat):
            return True
    return False

def _path_excluded(rel):
    for part in rel.split("/"):
        for pat in EXCLUDE_DIRS:
            if fnmatch.fnmatch(part, pat):
                return True
    return False

def has_secret_literal(path):
    """True when the repository gate's credential layer would flag the file.
    Read as text with errors ignored; binaries simply do not match."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return True      # unreadable: treat as unsafe, leave it out
    return bool(scan_secrets_text(text))

def _wanted(name, patterns, subs):
    if not any(fnmatch.fnmatch(name, p) for p in patterns):
        return False
    low = name.lower()
    return not any(s in low for s in subs)

def gather():
    """Every file the bundle carries, as sorted (relative path, absolute path).
    Include patterns first, then the hard excludes -- a secret named to match
    an include pattern is still dropped."""
    seen = {}
    skipped_secret = 0
    content_hits = []
    for d, patterns, recurse, subs in SOURCES:
        base = under_root(d)
        if not os.path.isdir(base):
            log("note: source directory absent, skipped:", "/" + d)
            continue
        if recurse:
            walker = os.walk(base)
        else:
            walker = [(base, [], os.listdir(base))]
        for cur, dirs, files in walker:
            dirs.sort()
            for name in sorted(files):
                ap = os.path.join(cur, name)
                if not os.path.isfile(ap) or os.path.islink(ap):
                    continue
                if not _wanted(name, patterns, subs):
                    continue
                rel = os.path.relpath(ap, ROOT).replace(os.sep, "/")
                if _name_excluded(name) or _path_excluded(rel):
                    skipped_secret += 1
                    continue
                if has_secret_literal(ap):
                    content_hits.append(name)
                    log("EXCLUDED (secret literal in content):", "/" + rel)
                    continue
                seen[rel] = ap
    return sorted(seen.items()), skipped_secret, sorted(content_hits)

def capture_crontab():
    """The root crontab as text; a note instead of a failure when there is
    none (an empty crontab is a fact worth recording, not a reason to stop)."""
    try:
        p = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=20)
        if p.returncode == 0:
            return p.stdout, True
        return "# crontab -l returned %d: %s\n" % (p.returncode, p.stderr.strip()), False
    except Exception as ex:
        return "# crontab -l unavailable: %s\n" % ex, False

# ---------------------------------------------------------------- build -----
def build():
    """Build the tarball into OUT_PATH (atomic replace), verify it against its
    own manifest, print the summary. Returns (path, summary dict)."""
    files, skipped, content_hits = gather()
    if not files:
        die(20, "nothing gathered under", ROOT, "-- refusing to write an empty bundle")
    rels = [r for r, _ in files]
    if KEYFILE not in rels:
        die(21, "/" + KEYFILE, "is not in the gather -- the bundle is pointless"
                " without it; not writing one")

    cron_text, cron_ok = capture_crontab()
    if not cron_ok:
        log("WARNING:", cron_text.strip())

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR, mode=0o700)
    fd, tmp = tempfile.mkstemp(suffix=".tar.gz", prefix="code_bundle_", dir=OUT_DIR)
    os.close(fd)

    manifest_lines = []
    content_bytes = 0
    key_md5 = None
    now = int(time.time())

    def add_bytes(tf, arcname, data):
        info = tarfile.TarInfo(arcname)
        info.size = len(data)
        info.mtime = now
        info.mode = 0o600
        tf.addfile(info, io.BytesIO(data))

    try:
        with tarfile.open(tmp, "w:gz", compresslevel=6) as tf:
            for rel, ap in files:
                m = md5_file(ap)
                content_bytes += os.path.getsize(ap)
                if rel == KEYFILE:
                    key_md5 = m
                manifest_lines.append("%s  %s" % (m, rel))
                tf.add(ap, arcname=rel, recursive=False)
            cron_b = cron_text.encode("utf-8")
            manifest_lines.append("%s  %s" % (md5_bytes(cron_b), CRONFILE))
            add_bytes(tf, CRONFILE, cron_b)
            info = ("kit=%s\nbuilt=%s\nhost=%s\nroot=%s\nfiles=%d\ncontent_bytes=%d\n"
                    "finance_app_md5=%s\ncrontab_captured=%s\n"
                    % (KIT, time.strftime("%Y-%m-%d %H:%M:%S"), socket.gethostname(),
                       ROOT, len(files), content_bytes, key_md5, cron_ok))
            add_bytes(tf, INFOFILE, info.encode("utf-8"))
            add_bytes(tf, MANIFEST, ("\n".join(manifest_lines) + "\n").encode("utf-8"))
        os.chmod(tmp, 0o600)
        bad = verify_tarball(tmp)
        if bad:
            die(22, "the bundle does not verify against its own manifest:", bad)
        os.replace(tmp, OUT_PATH)
    except SystemExit:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    summary = {"files": len(files), "content_bytes": content_bytes,
               "tar_bytes": os.path.getsize(OUT_PATH), "tar_md5": md5_file(OUT_PATH),
               "finance_app_md5": key_md5, "skipped_by_exclude": skipped,
               "excluded_secret": content_hits}
    log("SUMMARY files=%d content_bytes=%d tar_bytes=%d finance_app.py md5 %s"
        " excluded_by_rule=%d excluded_secret=%d (%s) -> %s"
        % (summary["files"], content_bytes, summary["tar_bytes"], key_md5,
           skipped, len(content_hits), ", ".join(content_hits) or "-", OUT_PATH))
    return OUT_PATH, summary

def verify_tarball(path):
    """Re-read the tarball; every manifest row must match its member and
    every member (bar the manifest and info) must have a row. Returns a
    list of problems, empty when good."""
    problems = []
    with tarfile.open(path, "r:gz") as tf:
        members = {m.name: m for m in tf.getmembers() if m.isfile()}
        if MANIFEST not in members:
            return ["manifest missing"]
        rows = tf.extractfile(members[MANIFEST]).read().decode("utf-8").splitlines()
        listed = set()
        for row in rows:
            if not row.strip():
                continue
            m, rel = row.split("  ", 1)
            listed.add(rel)
            if rel not in members:
                problems.append("listed but absent: " + rel)
                continue
            if md5_bytes(tf.extractfile(members[rel]).read()) != m:
                problems.append("md5 mismatch: " + rel)
        for name in members:
            if name not in listed and name not in (MANIFEST, INFOFILE):
                problems.append("member without a row: " + name)
    return problems

# ----------------------------------------------------------------- modes ----
# (reused from finance_drive_backup.py S213 v2 -- _connect; no conf is written)
def _connect():
    conf = load_conf()
    sa = find_sa_json(conf)
    if not sa:
        die(10, "no service-account json found; searched", ", ".join(SA_SEARCH),
            "and /root/wa/*.json -- set SA_JSON= in", CONF_PATH)
    fid = conf.get("FOLDER_ID")
    if not fid:
        die(11, "FOLDER_ID not set in", CONF_PATH, "-- the db leg's conf is the"
                " one this job shares; it is normally there already")
    return conf, sa, fid

def find_slot(d, folder_id):
    files = {f["name"]: f for f in d.list(folder_id)}
    return files.get(SLOT)

def run(drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect()
    path, summary = build()
    local_md5 = summary["tar_md5"]
    d = drive_cls(session_maker(sa))
    slot = find_slot(d, fid)
    if not slot:
        die(13, "slot file missing in the Drive folder:", SLOT,
            "-- it is owner-owned and must exist (created once from the owner's"
            " account, next to finance_nightly.db.gz); the service account cannot"
            " create it (zero quota). The local copy at", path, "is good.")
    d.update_content(slot["id"], path)
    got = d.get(slot["id"])
    if got.get("md5Checksum") != local_md5 or int(got.get("size", -1)) != os.path.getsize(path):
        die(30, "slot update DID NOT VERIFY (drive md5 %s vs local %s) -- the"
                " previous good version still stands in the file's revision"
                " history" % (got.get("md5Checksum"), local_md5))
    desc = ("code bundle . %d files . md5 %s . finance_app.py %s . shipped %s"
            % (summary["files"], local_md5, summary["finance_app_md5"],
               time.strftime("%F %T")))
    d.patch_meta(slot["id"], {"description": desc})
    log("shipped -> %s . %d bytes . md5 %s . verified by read-back"
        % (SLOT, summary["tar_bytes"], local_md5))
    nrev = len(d.revisions(slot["id"]))
    log("held on Drive: %s (%d revisions = restore points)" % (SLOT, nrev))

def list_mode(drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect()
    d = drive_cls(session_maker(sa))
    for f in sorted(d.list(fid), key=lambda f: f["name"]):
        log(f["name"], f.get("size", "?"), "bytes", f.get("md5Checksum", ""),
            ".", (f.get("description") or "")[:80])
    slot = find_slot(d, fid)
    if slot:
        log("slot", SLOT, "present . revisions:", len(d.revisions(slot["id"])))
    else:
        log("slot", SLOT, "MISSING -- owner step: upload any file with exactly"
            " that name into the folder from the owner's account, once")
    if os.path.exists(OUT_PATH):
        age_h = (time.time() - os.path.getmtime(OUT_PATH)) / 3600.0
        log("local copy:", OUT_PATH, "%.1f h old" % age_h, "md5", md5_file(OUT_PATH))
    else:
        log("local copy: none yet at", OUT_PATH)

def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    if mode == "build":
        build()
    elif mode == "run":
        run()
    elif mode == "list":
        list_mode()
    else:
        print("usage: code_bundle.py build|run|list")
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv)
