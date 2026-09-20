#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""records_drive.py -- S335 (session 273, 20-Sep-2026). The patient-record page's one door to Google Drive.

WHY A SEPARATE FILE. The finance web app runs under the system python, which has no Google libraries;
the box's venv (/root/wa/venv) has them and already reads Drive for the Marg collector. records.py runs
this helper with the venv python for each Drive read. Read-only scope; nothing is written to Drive.
  media <file id>     the file's bytes on stdout
  list  <folder id>   JSON list of the plain files in that folder on stdout
Exit 0 on success; 2 with one line on stderr otherwise. RECORDS_HELPER_STUB=<dir> serves the walk.
No patient data, no secret in this file (F-185).
"""
import glob
import json
import os
import re
import sys
import time

API = "https://www.googleapis.com/drive/v3/files"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FIELDS = "nextPageToken,files(id,name,mimeType,md5Checksum,size,modifiedTime,createdTime,imageMediaMetadata/time)"


def die(msg):
    sys.stderr.write(msg[:200] + "\n")
    sys.exit(2)


def key_file():
    for d in ("/root/wa", "/root/wa/keys", "/root"):
        for path in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                if b"service_account" in open(path, "rb").read():
                    return path
            except OSError:
                continue
    return ""


def headers():
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    k = key_file()
    if not k:
        die("no service-account key on this box")
    c = service_account.Credentials.from_service_account_file(k, scopes=SCOPES)
    c.refresh(Request())
    return {"Authorization": "Bearer " + c.token}


def get(url, params, h, timeout=60):
    import requests
    for attempt in range(3):
        r = requests.get(url, params=params, headers=h, timeout=timeout)
        if r.status_code == 200:
            return r
        if r.status_code in (429, 500, 502, 503) and attempt < 2:
            time.sleep(3 * (attempt + 1))
            continue
        die("Drive said %s" % r.status_code)


def main(argv):
    if len(argv) != 3 or argv[1] not in ("media", "list") or not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", argv[2]):
        die("usage: records_drive.py media|list <id>")
    what, fid = argv[1], argv[2]
    stub = os.environ.get("RECORDS_HELPER_STUB", "")
    if stub:
        p = os.path.join(stub, fid if what == "media" else "list_%s.json" % fid)
        if not os.path.exists(p):
            die("Drive said 404")
        data = open(p, "rb").read()
        sys.stdout.buffer.write(data)
        return 0
    h = headers()
    if what == "media":
        sys.stdout.buffer.write(get(API + "/" + fid, {"alt": "media"}, h, 120).content)
        return 0
    out, token = [], None
    while True:
        prm = {"q": "'%s' in parents and trashed=false" % fid, "pageSize": 1000, "fields": FIELDS}
        if token:
            prm["pageToken"] = token
        d = get(API, prm, h).json()
        out.extend(f for f in d.get("files", []) if f.get("mimeType") != "application/vnd.google-apps.folder")
        token = d.get("nextPageToken")
        if not token:
            break
    sys.stdout.write(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
