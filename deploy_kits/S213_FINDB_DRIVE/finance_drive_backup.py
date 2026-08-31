#!/root/wa/venv/bin/python3
# =============================================================================
#  finance_drive_backup.py  ·  Session 213  ·  F-261  ·  v2
#
#  THE OFF-BOX LEG OF THE finance.db BACKUP.
#
#  finance_backup.sh (S179, cron 5 1) already takes a VERIFIED local copy every
#  night and refuses to prune on a bad day. But every copy sits on the same
#  disk as the original. Meanwhile the clinic CSVs reach Google Drive nightly
#  and finance.db reaches nowhere (F-261, measured at S212).
#
#  v2 — WHY THIS SCRIPT UPDATES FILES INSTEAD OF CREATING THEM.
#  v1 had the service account CREATE a new file per night. Proven wrong on the
#  live box, 31-Aug-2026: HTTP 403 "Service Accounts do not have storage
#  quota." Google no longer gives service accounts any storage of their own.
#  What a zero-quota service account CAN still do is write new CONTENT into a
#  file the owner already owns — the bytes then count against the OWNER's
#  quota. So the design is now:
#
#    * two files exist in the shared folder, OWNED by drmka.ortho:
#        finance_nightly.db.gz   overwritten every night
#        finance_monthly.db.gz   overwritten on the first verified run of the
#                                month; that head revision is PINNED (keep
#                                forever), giving one immortal copy per month
#    * history comes from Drive's own revision history: Drive keeps a file's
#      previous versions ~30 days (pinned ones indefinitely), so the nightly
#      file alone carries about a month of restore points
#    * the 30 on-box dailies + 12 on-box monthlies of finance_backup.sh are
#      unchanged and remain the first restore stop
#
#  Refusal stances, inherited from S179 and kept absolute:
#    * a copy failing integrity_check, or with an empty day_entry, never
#      leaves the box; nor does a copy older than 30 h (the 01:05 job is
#      broken then — fix that, not this)
#    * an update whose read-back md5 differs is FATAL and the monthly is not
#      touched; the previous good version still sits in revision history
#
#  Modes:
#    preflight  find the SA json, reach Drive, find both files, prove write
#               access by a metadata-only touch (no content changed). Report.
#    run        the nightly job.
#    list       what is in the folder + nightly revision count. Read-only.
#
#  Config:  /root/finance/drive_backup.conf   (KEY=VALUE, chmod 600)
#    SA_JSON=/root/wa/patient-mirror-key.json
#    FOLDER_ID=<folder id>
#
#  Cron (after the 01:05 local backup):
#    40 1 * * *  /root/wa/venv/bin/python3 /root/finance/finance_drive_backup.py run >> /root/finance/drive_backup.log 2>&1
#
#  No patient data, no numbers, no secrets in this file (F-185): ids and
#  paths live in the conf on the VPS, never in git.
# =============================================================================
import gzip
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)   # google-auth py3.9 EOL noise

CONF_PATH   = "/root/finance/drive_backup.conf"
BACKUP_DIR  = "/root/backups/finance"          # where finance_backup.sh writes
NIGHTLY     = "finance_nightly.db.gz"
MONTHLY     = "finance_monthly.db.gz"
MAX_BACKUP_AGE_H = 30                          # newest local copy must be fresher
PIN_WARN    = 180                              # Drive pins cap at 200/file

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
def make_session(sa_json):
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    creds = Credentials.from_service_account_file(
        sa_json, scopes=["https://www.googleapis.com/auth/drive"])
    return AuthorizedSession(creds)

class Drive:
    """The six Drive calls this job needs, and nothing else."""
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

    def pin_revision(self, file_id, rev_id):
        self._ck(self.s.patch(self.API + "/files/%s/revisions/%s" % (file_id, rev_id),
                              headers={"Content-Type": "application/json"},
                              data=json.dumps({"keepForever": True})), "revision pin")

# ---------------------------------------------------------------- verify ----
def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def verify_db(path):
    """The copy must open and answer, exactly as finance_backup.sh demands."""
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    try:
        ok = c.execute("PRAGMA integrity_check").fetchone()[0]
        days = c.execute("SELECT COUNT(*) FROM day_entry").fetchone()[0]
    finally:
        c.close()
    if ok != "ok":
        raise RuntimeError("integrity_check said %r" % ok)
    if days <= 0:
        raise RuntimeError("day_entry is empty — refusing to ship an empty book")
    return days

def newest_local_backup():
    if not os.path.isdir(BACKUP_DIR):
        return None
    cands = [os.path.join(BACKUP_DIR, n) for n in os.listdir(BACKUP_DIR)
             if n.startswith("finance_") and n.endswith(".db")]
    cands = [p for p in cands if os.path.isfile(p)]
    return max(cands, key=os.path.getmtime) if cands else None

def gzip_to_tmp(src):
    fd, tmp = tempfile.mkstemp(suffix=".db.gz", prefix="findb_",
                               dir=os.path.dirname(CONF_PATH) or "/tmp")
    os.close(fd)
    with open(src, "rb") as fi, gzip.open(tmp, "wb", compresslevel=6) as fo:
        while True:
            b = fi.read(1 << 20)
            if not b:
                break
            fo.write(b)
    os.chmod(tmp, 0o600)
    return tmp

def find_slots(d, folder_id):
    """Both owner-owned slot files, by exact name."""
    files = {f["name"]: f for f in d.list(folder_id)}
    missing = [n for n in (NIGHTLY, MONTHLY) if n not in files]
    if missing:
        die(13, "slot file(s) missing in the Drive folder:", ", ".join(missing),
            "— they are owner-owned and must exist (created once from the owner's"
            " account); the service account cannot create them (zero quota).")
    return files[NIGHTLY], files[MONTHLY]

# ----------------------------------------------------------------- modes ----
def _connect(conf_required=True):
    conf = load_conf()
    sa = find_sa_json(conf)
    if not sa:
        die(10, "no service-account json found; searched", ", ".join(SA_SEARCH),
            "and /root/wa/*.json — set SA_JSON= in", CONF_PATH)
    if not os.path.exists(CONF_PATH):
        with open(CONF_PATH, "w") as fh:
            fh.write("SA_JSON=%s\nFOLDER_ID=\n" % sa)
        os.chmod(CONF_PATH, 0o600)
        log("wrote", CONF_PATH, "— FOLDER_ID is still blank")
    fid = conf.get("FOLDER_ID")
    if conf_required and not fid:
        log("FOLDER_ID not set in %s yet." % CONF_PATH)
        sys.exit(11)
    return conf, sa, fid

def preflight(drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect(conf_required=False)
    email = json.load(open(sa)).get("client_email", "?")
    log("service account json:", sa)
    log("service account identity:", email)
    d = drive_cls(session_maker(sa))
    ab = d.about()
    log("drive reachable as:", ab.get("user", {}).get("emailAddress", "?"))
    if not fid:
        log("OWNER STEP: share the folder with the identity above (Editor) and put"
            " its id in", CONF_PATH)
        sys.exit(11)
    f = d.folder(fid)
    if f.get("mimeType") != "application/vnd.google-apps.folder":
        die(12, "FOLDER_ID is not a folder:", f)
    log("folder visible:", f.get("name"), "(%s)" % fid)
    nightly, monthly = find_slots(d, fid)
    log("slot files found:", NIGHTLY, "(%s)" % nightly["id"], "·",
        MONTHLY, "(%s)" % monthly["id"])
    # prove WRITE access without touching content: a metadata-only description
    # touch on the nightly slot. Content and revisions are unchanged by this.
    stamp = "preflight write-test %s" % time.strftime("%F %T")
    d.patch_meta(nightly["id"], {"description": (nightly.get("description") or "")
                                 [:900] + " | " + stamp})
    log("metadata write on", NIGHTLY, ": OK (content untouched)")
    nb = newest_local_backup()
    if nb:
        try:
            days = verify_db(nb)
            log("newest local backup:", os.path.basename(nb),
                "· verifies, %d day-entries" % days)
        except Exception as ex:
            log("WARNING: newest local backup", os.path.basename(nb),
                "does NOT verify:", ex)
    else:
        log("WARNING: no local backup found in", BACKUP_DIR,
            "— is finance_backup.sh installed and cronned?")
    log("PREFLIGHT OK — ready for 'run'")

def run(drive_cls=Drive, session_maker=make_session, now=None):
    now = now or time.localtime()
    conf, sa, fid = _connect()

    src = newest_local_backup()
    if not src:
        die(20, "no local backup in", BACKUP_DIR, "— nothing to ship")
    age_h = (time.time() - os.path.getmtime(src)) / 3600.0
    if age_h > MAX_BACKUP_AGE_H:
        die(21, "newest local backup is %.1f h old (%s) — finance_backup.sh has"
                " not produced a fresh copy; NOT shipping a stale one"
                % (age_h, os.path.basename(src)))
    days = verify_db(src)          # raises on a bad copy — nothing is shipped
    log("local copy verifies:", os.path.basename(src), "· %d day-entries" % days)

    tmp = gzip_to_tmp(src)
    try:
        local_md5 = md5_file(tmp)
        d = drive_cls(session_maker(sa))
        nightly, monthly = find_slots(d, fid)

        d.update_content(nightly["id"], tmp)
        got = d.get(nightly["id"])
        if got.get("md5Checksum") != local_md5 or int(got.get("size", -1)) != os.path.getsize(tmp):
            die(30, "nightly update DID NOT VERIFY (drive md5 %s vs local %s) —"
                    " monthly untouched; the previous good version is still in"
                    " the file's revision history" % (got.get("md5Checksum"), local_md5))
        desc = ("verified backup of %s · md5 %s · %d day-entries · shipped %s"
                % (os.path.basename(src), local_md5, days, time.strftime("%F %T")))
        d.patch_meta(nightly["id"], {"description": desc})
        log("shipped -> %s · %d bytes · md5 %s · verified by read-back"
            % (NIGHTLY, os.path.getsize(tmp), local_md5))

        # ---- monthly: first verified run of the month, pinned forever ------
        mtag = time.strftime("%Y-%m", now)
        mdesc = monthly.get("description") or ""
        if ("month=%s" % mtag) not in mdesc:
            d.update_content(monthly["id"], tmp)
            mg = d.get(monthly["id"])
            if mg.get("md5Checksum") == local_md5:
                revs = d.revisions(monthly["id"])
                if revs:
                    try:
                        d.pin_revision(monthly["id"], revs[-1]["id"])
                        log("monthly copy for", mtag, "shipped and PINNED (kept forever)")
                    except Exception as ex:
                        log("WARNING: monthly shipped but pin failed:", ex)
                pins = sum(1 for r in d.revisions(monthly["id"]) if r.get("keepForever"))
                if pins >= PIN_WARN:
                    log("WARNING: %d pinned revisions on %s — Drive caps at 200;"
                        " plan a second monthly file" % (pins, MONTHLY))
                d.patch_meta(monthly["id"],
                             {"description": "month=%s · %s" % (mtag, desc)})
            else:
                log("WARNING: monthly update did not verify — its previous version"
                    " still stands in revision history; the nightly above is good")
        # ---- visibility ----------------------------------------------------
        nrev = len(d.revisions(nightly["id"]))
        log("held on Drive: %s (%d revisions ≈ restore points) · %s (monthly, pinned)"
            % (NIGHTLY, nrev, MONTHLY))
    finally:
        os.unlink(tmp)

def list_mode(drive_cls=Drive, session_maker=make_session):
    conf, sa, fid = _connect()
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
        print("usage: finance_drive_backup.py preflight|run|list")
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv)
