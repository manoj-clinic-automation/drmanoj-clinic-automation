#!/root/wa/venv/bin/python3
# =============================================================================
#  finance_drive_backup.py  ·  Session 213  ·  F-261
#
#  THE OFF-BOX LEG OF THE finance.db BACKUP.
#
#  finance_backup.sh (S179, cron 5 1) already takes a VERIFIED local copy every
#  night with sqlite3's own .backup and refuses to prune anything on a bad day.
#  But every one of those copies sits on the SAME DISK as the original — its own
#  closing comment says so. Meanwhile the clinic CSVs go to Google Drive every
#  night and finance.db goes nowhere (F-261, found at S212).
#
#  This script closes that gap without a single new credential:
#    * it reuses the Google SERVICE ACCOUNT the follow-up tracker already uses
#      (gspread on this box) — the same JSON, the Drive API instead of Sheets
#    * it takes the NEWEST copy finance_backup.sh produced tonight, re-verifies
#      it opens and answers (integrity_check + day_entry count), gzips it, and
#      uploads it to ONE Drive folder the owner shared with the service account
#    * it verifies the upload by reading back Drive's own md5Checksum and
#      comparing to the local gzip — an upload is not a backup until it matches
#    * it keeps 30 dailies and one copy per month on Drive, and REFUSES to
#      prune anything if tonight's upload did not verify (same stance as S179)
#
#  Modes:
#    preflight  find the SA json, reach Drive, test-write the folder, report.
#               Uploads one tiny file and deletes it. Touches nothing else.
#    run        the nightly job.
#    list       show what is on Drive in the folder. Read-only.
#
#  Config:  /root/finance/drive_backup.conf   (KEY=VALUE, chmod 600)
#    SA_JSON=/path/to/service_account.json    (preflight suggests one if absent)
#    FOLDER_ID=<Drive folder id>              (the folder the owner shared)
#
#  Cron (after the 01:05 local backup):
#    40 1 * * *  /root/wa/venv/bin/python3 /root/finance/finance_drive_backup.py run >> /root/finance/drive_backup.log 2>&1
#
#  This file contains no patient data, no numbers, no secrets (F-185): the
#  folder id and the json path live in the conf file on the VPS, never in git.
# =============================================================================
import gzip
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import tempfile
import time

CONF_PATH   = "/root/finance/drive_backup.conf"
BACKUP_DIR  = "/root/backups/finance"          # where finance_backup.sh writes
KEEP_DAILY  = 30                               # dailies kept on Drive
KEEP_MONTHLY_DAYS = 400                        # monthlies kept on Drive
MAX_BACKUP_AGE_H  = 30                         # newest local copy must be fresher
DAILY_RE    = re.compile(r"^finance_\d{4}-\d{2}-\d{2}_\d{6}\.db\.gz$")
MONTHLY_RE  = re.compile(r"^finance_monthly_\d{4}-\d{2}\.db\.gz$")

SA_SEARCH = [
    "/root/wa/service_account.json",
    "/root/wa/credentials.json",
    "/root/wa/creds.json",
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
    found = list(dict.fromkeys(p for p in SA_SEARCH if os.path.exists(p)))
    # widen: any json under /root/wa that looks like a service account
    try:
        for name in sorted(os.listdir("/root/wa")):
            if name.endswith(".json"):
                p = os.path.join("/root/wa", name)
                if p not in found:
                    try:
                        j = json.load(open(p))
                        if j.get("type") == "service_account":
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
    """The five Drive calls this job needs, and nothing else."""
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
                                params={"fields": "user(emailAddress),storageQuota(limit,usage)"}),
                     "about")
        return r.json()

    def folder(self, folder_id):
        r = self._ck(self.s.get(self.API + "/files/" + folder_id,
                                params={"fields": "id,name,mimeType",
                                        "supportsAllDrives": "true"}),
                     "folder get")
        return r.json()

    def list(self, folder_id):
        files, token = [], None
        while True:
            params = {"q": "'%s' in parents and trashed=false" % folder_id,
                      "fields": "nextPageToken,files(id,name,size,md5Checksum,createdTime)",
                      "pageSize": "1000", "supportsAllDrives": "true",
                      "includeItemsFromAllDrives": "true"}
            if token:
                params["pageToken"] = token
            r = self._ck(self.s.get(self.API + "/files", params=params), "list")
            j = r.json()
            files += j.get("files", [])
            token = j.get("nextPageToken")
            if not token:
                return files

    def upload(self, folder_id, name, path):
        """Resumable upload: initiate, then one streamed PUT of the file."""
        meta = {"name": name, "parents": [folder_id]}
        size = os.path.getsize(path)
        r = self._ck(self.s.post(
            self.UP + "/files?uploadType=resumable&supportsAllDrives=true"
                      "&fields=id,name,size,md5Checksum",
            headers={"Content-Type": "application/json; charset=UTF-8",
                     "X-Upload-Content-Length": str(size)},
            data=json.dumps(meta)), "upload initiate")
        loc = r.headers.get("Location")
        if not loc:
            raise RuntimeError("upload initiate returned no session URI")
        with open(path, "rb") as f:
            r = self._ck(self.s.put(loc, data=f,
                                    headers={"Content-Length": str(size)}),
                         "upload bytes")
        return r.json()

    def get(self, file_id):
        r = self._ck(self.s.get(self.API + "/files/" + file_id,
                                params={"fields": "id,name,size,md5Checksum",
                                        "supportsAllDrives": "true"}),
                     "file get")
        return r.json()

    def delete(self, file_id):
        self._ck(self.s.delete(self.API + "/files/" + file_id,
                               params={"supportsAllDrives": "true"}), "delete")

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

# ----------------------------------------------------------------- modes ----
def preflight(drive_cls=Drive, session_maker=make_session):
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
    email = json.load(open(sa)).get("client_email", "?")
    log("service account json:", sa)
    log("service account identity:", email)
    d = drive_cls(session_maker(sa))
    ab = d.about()
    q = ab.get("storageQuota", {})
    log("drive reachable as:", ab.get("user", {}).get("emailAddress", "?"),
        "· quota used %s of %s" % (q.get("usage", "?"), q.get("limit", "unlimited")))
    fid = conf.get("FOLDER_ID")
    if not fid:
        log("FOLDER_ID not set in %s yet." % CONF_PATH)
        log("OWNER STEP: in Drive, create/choose a folder, share it with the")
        log("identity above as Editor, and put its id in the conf file.")
        sys.exit(11)
    f = d.folder(fid)
    if f.get("mimeType") != "application/vnd.google-apps.folder":
        die(12, "FOLDER_ID is not a folder:", f)
    log("folder visible:", f.get("name"), "(%s)" % fid)
    # prove writability with a tiny file, then remove it
    fdt, tp = tempfile.mkstemp(suffix=".txt", prefix="findb_preflight_")
    with os.fdopen(fdt, "w") as fh:
        fh.write("finance_drive_backup preflight %s\n" % time.strftime("%F %T"))
    try:
        up = d.upload(fid, "PREFLIGHT_delete_me.txt", tp)
        d.delete(up["id"])
    finally:
        os.unlink(tp)
    log("test write + delete in the folder: OK")
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
    conf = load_conf()
    sa = find_sa_json(conf)
    if not sa:
        die(10, "no service-account json — run preflight")
    fid = conf.get("FOLDER_ID")
    if not fid:
        die(11, "FOLDER_ID not set — run preflight")

    src = newest_local_backup()
    if not src:
        die(20, "no local backup in", BACKUP_DIR, "— nothing to ship")
    age_h = (time.time() - os.path.getmtime(src)) / 3600.0
    if age_h > MAX_BACKUP_AGE_H:
        die(21, "newest local backup is %.1f h old (%s) — finance_backup.sh "
                "has not produced a fresh copy; NOT shipping a stale one"
                % (age_h, os.path.basename(src)))
    days = verify_db(src)          # raises on a bad copy — nothing uploads
    log("local copy verifies:", os.path.basename(src), "· %d day-entries" % days)

    tmp = gzip_to_tmp(src)
    try:
        local_md5 = md5_file(tmp)
        name = os.path.basename(src) + ".gz"       # finance_<stamp>.db.gz
        d = drive_cls(session_maker(sa))
        up = d.upload(fid, name, tmp)
        got = d.get(up["id"])
        if got.get("md5Checksum") != local_md5 or int(got.get("size", -1)) != os.path.getsize(tmp):
            log("upload DID NOT VERIFY (drive md5 %s vs local %s) — deleting the"
                " bad copy, pruning NOTHING" % (got.get("md5Checksum"), local_md5))
            try:
                d.delete(up["id"])
            except Exception as ex:
                log("could not delete the bad copy:", ex)
            sys.exit(30)
        log("shipped %s · %d bytes · md5 %s · verified by read-back"
            % (name, os.path.getsize(tmp), local_md5))

        files = d.list(fid)

        # one monthly copy, created on the first verified run of the month
        mtag = time.strftime("%Y-%m", now)
        mname = "finance_monthly_%s.db.gz" % mtag
        if not any(f["name"] == mname for f in files):
            mu = d.upload(fid, mname, tmp)
            mg = d.get(mu["id"])
            if mg.get("md5Checksum") == local_md5:
                log("kept monthly copy", mname)
                mg = dict(mg); mg["name"] = mname; mg.setdefault("createdTime", "")
                files.append(mg)
            else:
                log("monthly copy did not verify — deleting it; the dailies stand")
                try:
                    d.delete(mu["id"])
                except Exception as ex:
                    log("could not delete bad monthly:", ex)

        # prune — only reachable after tonight's upload verified
        dailies = sorted((f for f in files if DAILY_RE.match(f["name"])),
                         key=lambda f: f["name"])
        for f in dailies[:-KEEP_DAILY] if len(dailies) > KEEP_DAILY else []:
            d.delete(f["id"])
            log("pruned daily", f["name"])
        cutoff = time.strftime("%Y-%m", time.localtime(time.time() - KEEP_MONTHLY_DAYS * 86400))
        for f in (f for f in files if MONTHLY_RE.match(f["name"])):
            if f["name"][len("finance_monthly_"):len("finance_monthly_") + 7] < cutoff:
                d.delete(f["id"])
                log("pruned monthly", f["name"])

        held = d.list(fid)
        log("held on Drive: %d daily, %d monthly"
            % (sum(1 for f in held if DAILY_RE.match(f["name"])),
               sum(1 for f in held if MONTHLY_RE.match(f["name"]))))
    finally:
        os.unlink(tmp)

def list_mode(drive_cls=Drive, session_maker=make_session):
    conf = load_conf()
    sa = find_sa_json(conf)
    fid = conf.get("FOLDER_ID")
    if not (sa and fid):
        die(11, "conf incomplete — run preflight")
    d = drive_cls(session_maker(sa))
    for f in sorted(d.list(fid), key=lambda f: f["name"]):
        log(f["name"], f.get("size", "?"), "bytes", f.get("md5Checksum", ""))

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
