#!/root/wa/venv/bin/python3
# =============================================================================
#  code_bundle.py  .  Session 243  .  S243_CODE_BUNDLE  .  v1.4 (S306)
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
#  v1.4 (S306, 17-Sep-2026 -- F-518): the content scan above only knows a
#  QUOTED literal. A systemd unit writes Environment=NAME=value unquoted, so
#  clinic-finance.service carried FINANCE_CRON_TOKEN and FINANCE_MARG_TOKEN
#  to Drive and to the owner's PC every night. Unit files are now MASKED, not
#  dropped (the unit is the record of how a service runs): on every
#  Environment= line of a file under etc/systemd/system, a secret-shaped name
#  keeps its name and its value becomes MASKED_BY_CODE_BUNDLE. The manifest
#  row is the md5 of the masked bytes the bundle carries; BUNDLE_INFO.txt
#  records, per masked file, the md5 of the ORIGINAL file and the names masked
#  (never a value), so a live pin can still be held against the bundle.
#  A closing guard re-reads every unit member of the finished tarball and
#  refuses to ship (exit 23) if an Environment= secret value is still there.
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
UNITSTATE = "unit_state.txt"          # v1.5 (S317, F-496)
# v1.6 (S318, the gap): what makes a unit OURS rather than the hosting
# panel's or the distribution's. Used ONLY to decide which enabled units
# are worth naming when they are missing from the bundle -- never to decide
# what is carried (the patterns below do that). One line to widen.
OURS = ("clinic-", "wa-", "call-", "staff-", "att", "assetapp",
        "fitlog", "gutlog", "rxguard", "email-agent")
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
    # --- v1.3 (S273, 15-Sep-2026) --------------------------------------------
    # S258 held every live pin against this bundle, then against GitHub, then
    # against the encrypted state bundle's own SRC_FILES and SRC_DIRS. SIX files
    # pinned as LIVE had no byte-exact copy in ANY store. Five of them are here;
    # the sixth, freshness_legs.json, comes in through the root/finance "*.json"
    # entry added below. Nothing above this comment changed.
    #
    #   root/assetapp  -- assets.dr-manoj.in. Its DATA (assets.db) has been in
    #                     the encrypted state bundle since S230; its CODE was in
    #                     no store at all. uploads/ and static/ are not matched.
    #   root/shared    -- sarvam_ocr.py, shared by the scanner surfaces.
    #   root/deploy    -- walled off by EXCLUDE_DIRS and still is: only the
    #                     paths named in DEPLOY_ALLOW survive that wall.
    ("root/assetapp",                ("*.py", "*.js", "*.html", "*.sql"),            False, ("users", "secret")),
    ("root/shared",                  ("*.py",),                                      False, ()),
    ("root/deploy",                  ("*.py", "*.txt"),                              False, ()),
    ("root/deploy/repo/deploy_kits/S229_ITEM_SPINE",
                                     ("*.py", "*.sql"),                              False, ()),
    # freshness_legs.json is CONFIGURATION, not code: a leg is widened or retired
    # there and never in freshness.py, so the file IS the setting. A SECOND entry
    # for root/finance rather than an edit to the first, so that no file carried
    # today can stop being carried by this change.
    ("root/finance",                 ("*.json",),                                    False, ("secret", "token", "cred", "key")),
    ("etc/systemd/system",           ("clinic-*.service", "clinic-*.timer",
                                      "wa-*.service", "call-*.service"),            False, ()),
    # v1.6 (S318): the estate's OTHER units. S317's first run read every
    # enable symlink on the box and eleven enabled units matched none of the
    # four patterns above -- the staff register, the asset app, the two
    # attendance services, the staff ledger, and the two call-* TIMERS whose
    # services were already carried. A SECOND entry rather than an edit to
    # the first, so that no file carried today can stop being carried by this
    # change (the S273 precedent, three entries above).
    ("etc/systemd/system",           ("call-*.timer", "staff-*.service",
                                      "assetapp.service", "attlistener.service",
                                      "attendance-*.service"),                      False, ()),
    # v1.7 (S347, the spine): the pharmacy spine, live since S331 (20-Sep-2026)
    # under /root/finance/spine/ and in no store until now -- the root/finance
    # entries above are non-recursive by design, so a new sub-folder is
    # invisible until it is named. Code, the two rule files the owner edits
    # (spine_rules.json, order_rules.json) and the nightly witness text.
    # NON-recursive on purpose: readings/ orders/ expiry/ are data and go to
    # the state backup; spine.db is walled off by "*.db*" below regardless.
    ("root/finance/spine",           ("*.py", "*.json", "*.txt"),                   False, ()),
    # v1.8 (S416, F-631, 26-Sep-2026): five live files the S279 close found in NO
    # nightly bundle, each coming back byte-identical only from its repository
    # kit. New entries, never an edit to an old one (the S273 precedent):
    #   root/portal *.js            -- portal_sw.js, the service worker (S366)
    #   ring-*.service              -- ring-hook.service, the caller pop-up's unit (S366)
    #   root/wa/casepack *.html/.py -- casepack_page.html (S216/S385) and its helpers
    #   root/wa *.sh                -- fu_push_on_arrival.sh (S376)
    # http_ece.py is already matched by root/portal *.py when it exists on disk.
    ("root/portal",                  ("*.js",),                                      False, ("users", "secret")),
    ("etc/systemd/system",           ("ring-*.service",),                            False, ()),
    ("root/wa/casepack",             ("*.html", "*.py"),                             False, ("users", "secret", "token")),
    ("root/wa",                      ("*.sh",),                                      False, ("users", "secret", "token")),
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

# --- v1.4 (S306, F-518): unit-file Environment= values -------------------------
UNIT_PREFIX = "etc/systemd/system/"
MASK_VALUE = "MASKED_BY_CODE_BUNDLE"
UNIT_SECRET_NAME = re.compile(
    r"(?i)(?:^|_)(token|secret|key|api_?key|password|passwd|pwd|auth|credential|credentials)(?:$|_)")
_ENV_LINE = re.compile(r"^(\s*Environment\s*=\s*)(.*)$")
_ENV_PAIR = re.compile(r'("?)([A-Za-z_][A-Za-z0-9_]*)=((?:[^"\s\\]|\\.)*)("?)')


def mask_unit_text(text):
    """(masked text, [names masked]). Only Environment= lines change, and on them
    only the VALUE of a secret-shaped name; every other byte is kept."""
    out, names = [], []
    for line in text.split("\n"):
        m = _ENV_LINE.match(line)
        if m:
            def _one(p):
                q1, name, val, q2 = p.group(1), p.group(2), p.group(3), p.group(4)
                if val and val != MASK_VALUE and UNIT_SECRET_NAME.search(name):
                    names.append(name)
                    return "%s%s=%s%s" % (q1, name, MASK_VALUE, q2)
                return p.group(0)
            line = m.group(1) + _ENV_PAIR.sub(_one, m.group(2))
        out.append(line)
    return "\n".join(out), names


def unit_secret_left(text):
    """True when a unit's Environment= line still carries a secret-shaped value."""
    for line in text.split("\n"):
        m = _ENV_LINE.match(line)
        if not m:
            continue
        for p in _ENV_PAIR.finditer(m.group(2)):
            if p.group(3) and p.group(3) != MASK_VALUE and UNIT_SECRET_NAME.search(p.group(2)):
                return True
    return False

# --- a path component that disqualifies the whole path
EXCLUDE_DIRS = ("_retired", "_retired_*", "__pycache__", "backups", "deploy")

# --- v1.3 (S273): the ONLY paths allowed to survive the "deploy" wall above.
#     The wall stays exactly as it is. These are named one at a time because
#     each is a LIVE file that S258 proved exists byte-exact in no other store:
#     not this bundle, not GitHub, not the encrypted state bundle, not the SSD.
#     A path not on this list is still dropped, so /root/deploy/repo -- the
#     deploy clone -- remains excluded apart from the two files the item spine
#     is actually run from. Every one of these is still name-checked and
#     content-scanned afterwards, like every other file.
DEPLOY_ALLOW = (
    "root/deploy/email_agent.py",
    "root/deploy/gen_live_pins.py",
    "root/deploy/verify_live_pins.py",
    "root/deploy/sweep_baseline.txt",
    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py",
    "root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine_schema.sql",
)

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
    if rel in DEPLOY_ALLOW:          # v1.3 (S273) -- the named exceptions only
        return False
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

# --- v1.5 (S317, F-496): WHAT A UNIT IS, AND WHETHER IT IS SWITCHED ON --------
#  The bundle has carried the unit FILES since S243 and the root crontab since
#  S250. Both answer "what would run". NEITHER answers "is it switched on".
#  A .timer that was never enabled has no symlink in any *.wants directory and
#  never fires once, and its unit file in this bundle looks exactly like a
#  healthy one. That is F-496, and two cheap facts close it:
#
#    1. THE SYMLINKS. gather() skips symlinks by design (os.path.islink), so
#       /etc/systemd/system/*.wants/ has never been in a bundle at all. The
#       link IS the enabled state on disk: no link, not enabled, whatever the
#       unit file says.
#    2. SYSTEMCTL'S OWN ANSWER -- is-enabled and is-active, per unit, for the
#       units this bundle carries, on the box it is actually running on.
#
#  Fact 1 is read from ROOT and is therefore true in a test tree. Fact 2 asks
#  the live machine, so it is SKIPPED, IN WRITING, whenever ROOT is not "/":
#  a bundle built against a copied tree must never report that copy's units as
#  the live machine's. Nothing here reads a unit's CONTENT -- is-enabled and
#  is-active print one word each -- so no Environment= value can leak by this
#  route (F-518 stays closed).

def _systemctl_one(verb, unit):
    """One word from systemctl about one unit, or a word saying why not.
    A NON-ZERO EXIT IS NORMAL here: systemctl exits non-zero for a disabled or
    inactive unit and still prints the answer, so the output is read and the
    return code is not. Never raises."""
    try:
        p = subprocess.run(["systemctl", verb, "--no-pager", unit],
                           capture_output=True, text=True, timeout=15)
        word = (p.stdout or "").strip().splitlines()
        if word:
            return word[0].strip() or "?"
        err = (p.stderr or "").strip().splitlines()
        return ("error:" + err[0].strip()[:40]) if err else "?"
    except Exception as ex:
        return "unavailable:%s" % type(ex).__name__


def capture_wants():
    """(lines, ok) -- every *.wants / *.requires symlink under ROOT's
    /etc/systemd/system, as "dir/link -> target". Filesystem truth, and it
    works in a test tree because it never asks the running machine."""
    base = under_root("etc/systemd/system")
    lines = []
    try:
        for name in sorted(os.listdir(base)):
            d = os.path.join(base, name)
            if not (name.endswith(".wants") or name.endswith(".requires")):
                continue
            if not os.path.isdir(d):
                continue
            for link in sorted(os.listdir(d)):
                p = os.path.join(d, link)
                if os.path.islink(p):
                    tgt = os.path.basename(os.readlink(p))
                else:
                    tgt = "(not a symlink)"
                lines.append("%s/%s -> %s" % (name, link, tgt))
    except OSError as ex:
        return ["# %s could not be listed: %s" % (base, ex)], False
    return lines, True


def capture_unit_state(rels):
    """(text, ok). One line per unit file the bundle carries: is-enabled,
    is-active, and whether any *.wants link points at it. A note instead of a
    failure when something cannot be read -- this leg never stops a bundle."""
    units = sorted(set(r.split("/")[-1] for r in rels if r.startswith(UNIT_PREFIX)))
    wants, wants_ok = capture_wants()
    linked = set()
    for ln in wants:
        if " -> " in ln and "/" in ln:
            linked.add(ln.split("/", 1)[1].split(" -> ")[0])
    live = (ROOT == "/")
    out = ["# unit_state.txt -- S317 (F-496): whether each carried job is SWITCHED ON,",
           "# not merely what it would do. Read with crontab.txt, never instead of it.",
           "# root=%s host=%s built=%s" % (ROOT, socket.gethostname(),
                                           time.strftime("%Y-%m-%d %H:%M:%S")),
           "",
           "[enable symlinks under %s]" % under_root("etc/systemd/system")]
    out += wants or ["(none -- nothing under this tree is enabled by symlink)"]
    # v1.6 (S318): THE GAP REPORTS ITSELF. An enabled unit this bundle does
    # not carry is a unit file in no store at all. Ours are named; the rest
    # are counted, because a nightly list of the panel's fifty would be
    # wallpaper inside a week (the S195 ruling).
    ours_linked = sorted(u for u in linked if u.startswith(OURS))
    gap = [u for u in ours_linked if u not in units]
    others = len([u for u in linked if not u.startswith(OURS)])
    out += ["", "[enabled, ours, and NOT carried by this bundle: %d]" % len(gap)]
    out += gap or ["(none -- every enabled unit of ours is in this bundle)"]
    out += ["# %d other enabled unit(s) are not ours (the hosting panel's and"
            " the distribution's) and are not listed here." % others]
    out += ["", "[units carried by this bundle: %d]" % len(units)]
    for u in units:
        if live:
            e, a = _systemctl_one("is-enabled", u), _systemctl_one("is-active", u)
        else:
            e = a = "not-asked"
        out.append("%-44s is-enabled=%-14s is-active=%-12s wants-link=%s"
                   % (u, e, a, "yes" if u in linked else "no"))
    if not units:
        out.append("(none)")
    if not live:
        out += ["",
                "# ROOT is not \"/\", so systemctl was NOT consulted and the two columns",
                "# above read not-asked. The symlink list above is still this tree's own",
                "# truth, and is the fact that matters most."]
    return "\n".join(out) + "\n", bool(wants_ok)

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

    unit_text, unit_ok = capture_unit_state(rels)        # v1.5 (S317, F-496)
    if not unit_ok:
        log("WARNING: the enable symlinks could not be listed; unit_state.txt says so")

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR, mode=0o700)
    fd, tmp = tempfile.mkstemp(suffix=".tar.gz", prefix="code_bundle_", dir=OUT_DIR)
    os.close(fd)

    manifest_lines = []
    content_bytes = 0
    key_md5 = None
    masked = []          # v1.4: (rel, original md5, [names])
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
                if rel.startswith(UNIT_PREFIX):          # v1.4 (F-518)
                    with open(ap, "rb") as fh:
                        raw = fh.read()
                    text, names = mask_unit_text(raw.decode("utf-8", errors="surrogateescape"))
                    if names:
                        data = text.encode("utf-8", errors="surrogateescape")
                        masked.append((rel, m, names))
                        manifest_lines.append("%s  %s" % (md5_bytes(data), rel))
                        add_bytes(tf, rel, data)
                        continue
                manifest_lines.append("%s  %s" % (m, rel))
                tf.add(ap, arcname=rel, recursive=False)
            cron_b = cron_text.encode("utf-8")
            manifest_lines.append("%s  %s" % (md5_bytes(cron_b), CRONFILE))
            add_bytes(tf, CRONFILE, cron_b)
            unit_b = unit_text.encode("utf-8")           # v1.5 (S317, F-496)
            manifest_lines.append("%s  %s" % (md5_bytes(unit_b), UNITSTATE))
            add_bytes(tf, UNITSTATE, unit_b)
            info = ("kit=%s\nbuilt=%s\nhost=%s\nroot=%s\nfiles=%d\ncontent_bytes=%d\n"
                    "finance_app_md5=%s\ncrontab_captured=%s\nunit_state_captured=%s\n"
                    % (KIT, time.strftime("%Y-%m-%d %H:%M:%S"), socket.gethostname(),
                       ROOT, len(files), content_bytes, key_md5, cron_ok, unit_ok))
            for rel, om, names in masked:                   # v1.4: names only, never a value
                info += "masked=%s original_md5=%s names=%s\n" % (rel, om, ",".join(names))
            add_bytes(tf, INFOFILE, info.encode("utf-8"))
            add_bytes(tf, MANIFEST, ("\n".join(manifest_lines) + "\n").encode("utf-8"))
        os.chmod(tmp, 0o600)
        bad = verify_tarball(tmp)
        if bad:
            die(22, "the bundle does not verify against its own manifest:", bad)
        left = units_with_secret(tmp)                      # v1.4 (F-518) closing guard
        if left:
            die(23, "a unit file in the bundle still carries a secret value -- not shipping:",
                ", ".join(left))
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
               "excluded_secret": content_hits,
               "masked": [(rel, names) for rel, _om, names in masked]}
    log("SUMMARY files=%d content_bytes=%d tar_bytes=%d finance_app.py md5 %s"
        " excluded_by_rule=%d excluded_secret=%d (%s) -> %s"
        % (summary["files"], content_bytes, summary["tar_bytes"], key_md5,
           skipped, len(content_hits), ", ".join(content_hits) or "-", OUT_PATH))
    log("MASKED %d unit value(s) in %d file(s): %s"
        % (sum(len(n) for _r, _o, n in masked), len(masked),
           "; ".join("%s (%s)" % (r.split("/")[-1], ",".join(n)) for r, _o, n in masked) or "-"))
    return OUT_PATH, summary


def units_with_secret(path):
    """v1.4: unit members of a finished tarball that still carry a secret value."""
    left = []
    with tarfile.open(path, "r:gz") as tf:
        for mem in tf.getmembers():
            if mem.isfile() and mem.name.startswith(UNIT_PREFIX):
                text = tf.extractfile(mem).read().decode("utf-8", errors="ignore")
                if unit_secret_left(text):
                    left.append(mem.name)
    return left

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
