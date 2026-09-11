#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_ingest.py -- S240 (D467), the server's own front door for Marg exports. Phase 1: SHADOW.

THE OWNER, 11-Sep-2026: the system leans too much on his own PC. The server must do the work; the
medical PC's only job is to export Marg reports and push them; his PC stays open for development.
"Make it stable, fail safe, and with good fallback options."

WHAT THIS DOES, every 5 minutes (cron, one lock):
  1. Lists the Marg archive on Google Drive -- the copy his PC already mirrors every 10 minutes
     (Clinic Data Archive/MargArchive). Drive is the transport: it queues and retries on its own,
     and in Phase 2 the medical PC writes its captures to Drive the same way, with no new program.
  2. Takes each file it has not seen (by Drive's own md5), checks the bytes against that md5, and
     runs THE SAME ROUTER his PC runs (marg_router.py + signatures.json, vendored here unchanged)
     into a server-side archive. Same classification, same verification, same names.
  3. Keeps what carries no patient identity (stock, purchases, item lists) as files, exactly where
     the PC keeps them. A sale report carries each patient's mobile on its bill rows, so it is
     read into PHI-free item lines (date, bill, item, pack, quantity, batch, expiry, amount) and the
     file itself is deleted -- the S186 rule, no raw export with a phone number at rest.
  4. Compares its own verdict with the verdict his PC recorded (index.csv on the same Drive).

WHAT IT DOES NOT DO: it sends nothing, applies nothing, and feeds no screen. Phase 1 exists to
prove, day after day, that the server reaches the same answers as his PC. Only then does anything
switch over (Phase 3), one job at a time, with the PC's path kept as the fallback.

SWITCH-OFF: create /root/marg_ingest/OFF (the run exits at once), or remove the cron line.

    /root/wa/venv/bin/python3 -B /root/marg_ingest/marg_ingest.py [--source drive|DIR] [--dry-run]
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)   # google-auth's Python 3.9 end-of-life
                                                            # notice, twice per run, in every log
import argparse
import csv
import datetime as dt
import glob
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DB_DEFAULT = "/root/finance/finance.db"
ARCHIVE = os.path.join(HERE, "archive")
WORK = os.path.join(HERE, "work")
OFF_FLAG = os.path.join(HERE, "OFF")
HEARTBEAT = os.path.join(HERE, "last_run.json")
DRIVE_ROOT_NAME = "MargArchive"
DRIVE_ROOT_ID = "1k01zTGMPiTVYAz4e1GCKMHj-QMZi5O1H"     # Clinic Data Archive/MargArchive
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
MAX_NEW_PER_RUN = 400

# Report types whose files may carry a patient's name or mobile. Read what is needed, keep no file.
PHI_TYPES = ("SALE_BILLWISE", "SALE_BOOK", "SALE_RETURN", "STOCK_ITEM_LEDGER", "DOCUMENT_PDF")
PHI_FOLDERS = ("_REFUSED", "_UNKNOWN")          # contents not established -> treated as PHI
STAMP_RE = re.compile(r"__(\d{8}-\d{6})__")

SCHEMA = """
CREATE TABLE IF NOT EXISTS mi_file (
  md5           TEXT PRIMARY KEY,
  drive_id      TEXT NOT NULL DEFAULT '',
  drive_name    TEXT NOT NULL DEFAULT '',
  drive_folder  TEXT NOT NULL DEFAULT '',
  drive_mtime   TEXT NOT NULL DEFAULT '',
  size          INTEGER NOT NULL DEFAULT 0,
  stamp         TEXT NOT NULL DEFAULT '',
  type          TEXT NOT NULL DEFAULT '',
  variant       TEXT NOT NULL DEFAULT '',
  date_from     TEXT NOT NULL DEFAULT '',
  date_to       TEXT NOT NULL DEFAULT '',
  verdict       TEXT NOT NULL DEFAULT '',
  reason        TEXT NOT NULL DEFAULT '',
  server_name   TEXT NOT NULL DEFAULT '',
  kept          INTEGER NOT NULL DEFAULT 0,
  lines         INTEGER NOT NULL DEFAULT 0,
  pc_type       TEXT NOT NULL DEFAULT '',
  pc_verdict    TEXT NOT NULL DEFAULT '',
  agree         TEXT NOT NULL DEFAULT '',
  received_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_mi_file_type ON mi_file(type, date_from);
CREATE TABLE IF NOT EXISTS mi_sale_line (
  md5        TEXT NOT NULL,
  bill_date  TEXT NOT NULL,
  bill_no    TEXT NOT NULL,
  is_return  INTEGER NOT NULL DEFAULT 0,
  seq        INTEGER,
  item_name  TEXT NOT NULL DEFAULT '',
  pack       TEXT NOT NULL DEFAULT '',
  qty_raw    TEXT NOT NULL DEFAULT '',
  qty_strips INTEGER,
  qty_loose  INTEGER,
  amount_p   INTEGER,
  expiry_ym  TEXT NOT NULL DEFAULT '',
  batch      TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_mi_sale_line ON mi_sale_line(bill_date, bill_no);
CREATE INDEX IF NOT EXISTS ix_mi_sale_line_md5 ON mi_sale_line(md5);
CREATE TABLE IF NOT EXISTS mi_run (
  id        INTEGER PRIMARY KEY,
  started   TEXT NOT NULL,
  finished  TEXT,
  listed    INTEGER, new INTEGER, failed INTEGER,
  note      TEXT NOT NULL DEFAULT ''
);
"""


def now_ist():
    return dt.datetime.now(IST).replace(microsecond=0)


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


# ------------------------------------------------------------------ sources
class DirSource:
    """A local folder laid out like the archive -- for tests, and a fallback feed."""
    def __init__(self, root):
        self.root = root

    def list(self):
        out = []
        for p in glob.glob(os.path.join(self.root, "**", "*"), recursive=True):
            if not os.path.isfile(p):
                continue
            rel = os.path.relpath(p, self.root)
            if rel.lower().endswith((".xls", ".xlsx")) and not rel.startswith(("_spool", "_outbox")):
                b = open(p, "rb").read()
                out.append(dict(id=p, name=os.path.basename(p), folder=os.path.dirname(rel),
                                md5=md5_bytes(b), size=len(b),
                                mtime=dt.datetime.fromtimestamp(os.path.getmtime(p), IST).isoformat()))
        return out

    def fetch(self, f):
        return open(f["id"], "rb").read()

    def pc_index(self):
        p = os.path.join(self.root, "index.csv")
        return open(p, "rb").read() if os.path.exists(p) else b""


class DriveSource:
    """Google Drive, read-only, through the box's own service account (the one docterz_ingest uses)."""
    API = "https://www.googleapis.com/drive/v3/files"

    def __init__(self, root_id=DRIVE_ROOT_ID):
        self.root_id = root_id
        self._cred = None

    def _find_key(self):
        for d in ("/root/wa", "/root/wa/keys", "/root"):
            for path in sorted(glob.glob(os.path.join(d, "*.json"))):
                try:
                    if b"service_account" in open(path, "rb").read():
                        return path
                except OSError:
                    continue
        return ""

    def account(self):
        k = self._find_key()
        if not k:
            return ""
        try:
            return json.load(open(k)).get("client_email", "")
        except (OSError, ValueError):
            return ""

    def _auth(self):
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        if self._cred is None or not self._cred.valid:
            key = self._find_key()
            if not key:
                raise RuntimeError("no service-account key under /root/wa, /root/wa/keys or /root")
            self._cred = service_account.Credentials.from_service_account_file(key, scopes=SCOPES)
            self._cred.refresh(Request())
        return {"Authorization": "Bearer " + self._cred.token}

    def _get(self, params):
        import requests
        for attempt in range(3):
            r = requests.get(self.API, params=params, headers=self._auth(), timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError("Drive list HTTP %s -- %s" % (r.status_code, r.text[:160]))

    def _children(self, folder_id):
        out, token = [], None
        while True:
            p = {"q": "'%s' in parents and trashed=false" % folder_id, "pageSize": 1000,
                 "fields": "nextPageToken,files(id,name,mimeType,md5Checksum,size,modifiedTime)"}
            if token:
                p["pageToken"] = token
            d = self._get(p)
            out.extend(d.get("files", []))
            token = d.get("nextPageToken")
            if not token:
                return out

    def list(self):
        out, stack = [], [(self.root_id, "")]
        while stack:
            fid, rel = stack.pop()
            for f in self._children(fid):
                if f["mimeType"] == "application/vnd.google-apps.folder":
                    if f["name"] not in ("_spool", "_outbox"):
                        stack.append((f["id"], os.path.join(rel, f["name"]) if rel else f["name"]))
                elif f["name"].lower().endswith((".xls", ".xlsx")) and f.get("md5Checksum"):
                    out.append(dict(id=f["id"], name=f["name"], folder=rel, md5=f["md5Checksum"],
                                    size=int(f.get("size") or 0), mtime=f.get("modifiedTime", "")))
        return out

    def _media(self, fid):
        import requests
        for attempt in range(3):
            r = requests.get(self.API + "/" + fid, params={"alt": "media"},
                             headers=self._auth(), timeout=120)
            if r.status_code == 200:
                return r.content
            if r.status_code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError("Drive download HTTP %s" % r.status_code)

    def fetch(self, f):
        return self._media(f["id"])

    def pc_index(self):
        for f in self._children(self.root_id):
            if f["name"] == "index.csv":
                return self._media(f["id"])
        return b""


# ------------------------------------------------------------------ helpers
def stamp_of(name, mtime_iso):
    """The capture moment: from the archived name first, else the source's own mtime."""
    m = STAMP_RE.search(name)
    if m:
        return m.group(1)
    try:
        t = dt.datetime.fromisoformat(mtime_iso.replace("Z", "+00:00")).astimezone(IST)
        return t.strftime("%Y%m%d-%H%M%S")
    except (ValueError, AttributeError):
        return ""


def set_mtime(path, stamp):
    """The router names a file by its file time; make that the capture moment, not download time."""
    try:
        t = dt.datetime.strptime(stamp, "%Y%m%d-%H%M%S").replace(tzinfo=IST).timestamp()
        os.utime(path, (t, t))
    except (ValueError, TypeError):
        pass


def pc_verdicts(raw):
    out = {}
    if not raw:
        return out
    try:
        rd = csv.DictReader(io.StringIO(raw.decode("utf-8", "replace")))
        for r in rd:
            if r.get("md5"):
                out[r["md5"]] = (r.get("type", ""), r.get("verdict", ""))
    except csv.Error:
        pass
    return out


def sale_lines(path):
    """PHI-free item lines from a sale report. The bill rows (name, mobile) are never read out."""
    import marg_report as MR
    rep = MR.read_report(path, keep_items=True)
    returns = {b["bill_no"] for day in rep["days"] for b in day["bills"] if b.get("is_credit_note")}
    rows = []
    for day in rep["days"]:
        for it in day["items"]:
            p = it["parsed"]
            rows.append((it["bill_date"], it["bill_no"], 1 if it["bill_no"] in returns else 0,
                         p.get("seq"), p.get("item_name") or "", p.get("pack") or "",
                         p.get("qty_raw") or "", p.get("qty_strips"), p.get("qty_loose"),
                         p.get("amount_p"), p.get("expiry_ym") or "", p.get("batch") or ""))
    return rows


def _connect(db):
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    con.executescript(SCHEMA)
    return con


# ------------------------------------------------------------------ one run
def _readers():
    """The router, with the sale-report reader able to open .xlsx on this Python. xlrd reads .xlsx
    only below Python 3.9 -- his PC's Python is old enough, this box's is not -- so the reader is
    pointed at the router's own opener (stdlib .xlsx, xlrd for .xls), exactly as push_expected does
    on the PC. Without this a perfectly good .xlsx sale report is refused here and verified there."""
    import marg_router as R
    import marg_report as MR
    MR._open_sheet = R.open_sheet
    return R


def run(source, db, archive=ARCHIVE, dry=False, out=print, limit=MAX_NEW_PER_RUN):
    R = _readers()
    t0 = now_ist()
    con = _connect(db)
    run_id = None
    if not dry:
        run_id = con.execute("INSERT INTO mi_run (started) VALUES (?)", (t0.isoformat(),)).lastrowid
        con.commit()
    known = {r[0] for r in con.execute("SELECT md5 FROM mi_file")}
    files = source.list()
    new = [f for f in files if f["md5"] not in known]
    # oldest capture first: the router's stock-universe memory depends on the order it sees days
    new.sort(key=lambda f: (stamp_of(f["name"], f["mtime"]), f["name"]))
    pc = pc_verdicts(source.pc_index()) if new else {}
    if new or dry:
        out("marg_ingest %s  listed %d, new %d%s" % (t0.strftime("%d-%m-%Y %H:%M"), len(files), len(new),
                                                      "  (DRY RUN)" if dry else ""))
    sigs = R.load_signatures(os.path.join(HERE, "signatures.json"))
    os.makedirs(archive, exist_ok=True)
    cfg = {"archive": archive, "outbox": os.path.join(WORK, "outbox"), "dry": dry,
           "index": os.path.join(archive, "index.csv")}
    seen = R.load_index(cfg["index"])
    done = failed = 0
    for f in new[:limit]:
        tmpdir = tempfile.mkdtemp(prefix="mi_", dir=WORK if os.path.isdir(WORK) else None)
        try:
            raw = source.fetch(f)
            if md5_bytes(raw) != f["md5"]:
                raise RuntimeError("bytes do not match the source's md5 -- not taken")
            stamp = stamp_of(f["name"], f["mtime"])
            local = os.path.join(tmpdir, f["name"])
            with open(local, "wb") as fh:
                fh.write(raw)
            set_mtime(local, stamp)
            quiet = []
            res = R.process(local, sigs, cfg, seen, quiet.append)
            if res is None:                               # the router had this md5 already
                res = dict(seen.get(f["md5"], {}))
            else:
                seen[f["md5"]] = res
            typ = res.get("type", "") or ""
            verdict = res.get("verdict", "") or ""
            dest = res.get("archived_path", "") or ""
            phi = typ in PHI_TYPES or verdict != "VERIFIED" or any(
                ("%s%s" % (os.sep, x)) in dest for x in PHI_FOLDERS)
            nlines = 0
            if typ == "SALE_BILLWISE" and verdict == "VERIFIED":
                rows = sale_lines(local)
                nlines = len(rows)
                if not dry:
                    con.execute("DELETE FROM mi_sale_line WHERE md5=?", (f["md5"],))
                    con.executemany(
                        "INSERT INTO mi_sale_line (md5, bill_date, bill_no, is_return, seq, item_name, "
                        "pack, qty_raw, qty_strips, qty_loose, amount_p, expiry_ym, batch) VALUES "
                        "(?,?,?,?,?,?,?,?,?,?,?,?,?)", [(f["md5"],) + r for r in rows])
            kept = 0
            if dest and os.path.exists(dest):
                if phi:
                    os.remove(dest)                          # no raw export with a phone number at rest
                else:
                    kept = 1
            pct, pcv = pc.get(f["md5"], ("", ""))
            agree = ("" if not pcv else
                     "yes" if (pct, pcv) == (typ, verdict) else "NO")
            if not dry:
                con.execute(
                    "INSERT OR REPLACE INTO mi_file (md5, drive_id, drive_name, drive_folder, drive_mtime, "
                    "size, stamp, type, variant, date_from, date_to, verdict, reason, server_name, kept, "
                    "lines, pc_type, pc_verdict, agree, received_at) VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (f["md5"], str(f["id"]) if not isinstance(source, DirSource) else "",
                     f["name"], f["folder"], f["mtime"], f["size"], stamp, typ,
                     res.get("variant", "") or "", res.get("date_from", "") or "",
                     res.get("date_to", "") or "", verdict, (res.get("reason", "") or "")[:300],
                     os.path.basename(dest), kept, nlines, pct, pcv, agree, now_ist().isoformat()))
                con.commit()
            done += 1
            out("  %-8s %-22s %s%s%s" % (verdict, typ or "?", f["name"][:70],
                                         "  [%d lines]" % nlines if nlines else "",
                                         "  PC DISAGREES (%s/%s)" % (pct, pcv) if agree == "NO" else ""))
        except Exception as e:                                 # noqa: BLE001
            failed += 1
            out("  FAILED   %s -- %s" % (f["name"][:70], str(e)[:160]))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            ob = cfg["outbox"]
            if os.path.isdir(ob):
                shutil.rmtree(ob, ignore_errors=True)       # the router's upload queue: not ours to keep
    t1 = now_ist()
    note = "more than %d new -- the rest next run" % limit if len(new) > limit else ""
    if not dry:
        con.execute("UPDATE mi_run SET finished=?, listed=?, new=?, failed=? , note=? WHERE id=?",
                    (t1.isoformat(), len(files), done, failed, note, run_id))
        con.execute("DELETE FROM mi_run WHERE started < ?", ((t1 - dt.timedelta(days=45)).isoformat(),))
        con.commit()
        try:
            with open(HEARTBEAT, "w") as fh:
                json.dump(dict(finished=t1.isoformat(), listed=len(files), new=done, failed=failed,
                               note=note), fh)
        except OSError:
            pass
    if new or dry:                       # a quiet run writes only the heartbeat, not the log
        out("done: %d taken, %d failed%s" % (done, failed, ("; " + note) if note else ""))
    con.close()
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--source", default=os.environ.get("MARG_INGEST_SOURCE", "drive"),
                    help="'drive' or a local folder laid out like the archive")
    ap.add_argument("--db", default=os.environ.get("MARG_INGEST_DB", DB_DEFAULT))
    ap.add_argument("--archive", default=ARCHIVE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=MAX_NEW_PER_RUN)
    ap.add_argument("--whoami", action="store_true", help="print the Drive account this box reads as")
    a = ap.parse_args(argv)
    if os.path.exists(OFF_FLAG):
        print("marg_ingest: switched off (%s exists)" % OFF_FLAG)
        return 0
    os.makedirs(WORK, exist_ok=True)
    src = DriveSource() if a.source == "drive" else DirSource(a.source)
    if a.whoami:
        print(src.account() if isinstance(src, DriveSource) else "local folder")
        return 0
    return run(src, a.db, archive=a.archive, dry=a.dry_run, limit=a.limit)


if __name__ == "__main__":
    sys.exit(main())
