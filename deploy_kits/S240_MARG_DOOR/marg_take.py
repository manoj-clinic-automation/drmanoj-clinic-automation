#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_take.py  --  S240 (D467 Phase 2a).  THE ONE DOOR: "take these bytes."

WHY THIS FILE EXISTS
    A Marg export can reach this box four ways -- pushed by the medical PC, collected from Google
    Drive, sent on by Dr Manoj's PC, or handed over by a person through a browser when every
    automatic path is down.  If each way had its own code, they would drift, and the same export
    arriving twice would be counted twice.  So every way calls THIS function and nothing else.

WHAT IT GUARANTEES
    1. DE-DUPLICATED BY THE BYTES THEMSELVES.  The md5 of the content is the key.  The same export
       may arrive by all four routes, any number of times: it is taken once and answers ALREADY
       after that.  This is the property that makes it safe to run every route at the same time.
    2. THE SAME VERDICTS AS THE PC.  It calls the same vendored router (marg_router.py) with the
       same signatures, through marg_ingest, which is already live on this box.  One copy of the
       judgement, not two.
    3. NO RAW EXPORT WITH A PATIENT NUMBER AT REST (S186).  A sale report is read into PHI-free
       item lines and the file is deleted in the same call.  Anything refused or unrecognised is
       treated as if it carried patient data and is deleted too.  Stock, purchase and item files
       carry none and are kept.
    4. THE CAPTURE MOMENT IS KEPT.  Our stock rules turn on WHEN a report was taken, not when it
       arrived.  If the name carries the stamp (the archive's `__YYYYmmdd-HHMMSS__`, or the
       medical PC's `MEDICAL__<stamp>__...`) that is used; only otherwise is it "now".
    5. IT REFUSES BEFORE IT TRUSTS.  Empty, oversized, wrong extension, or bytes that are not
       really a spreadsheet or a PDF: refused, with a reason a person can read.
    6. IT NEVER RUNS BESIDE ITSELF.  It holds the same lock the five-minute collector uses, so a
       browser upload and a scheduled run can never write the archive index at the same moment.

    It creates no schedule, sends nothing and changes no screen.
"""
import datetime as dt
import errno
import hashlib
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import marg_ingest as MI                                        # noqa: E402  (stdlib-only at import)

MAX_BYTES = 25 * 1024 * 1024          # a Marg export is tens of KB; 25 MB is already absurd
LOCK_PATH = "/tmp/marg_ingest.lock"   # the SAME lock the cron uses -- see guarantee 6
LOCK_WAIT_S = 25
BAD_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
EXT_MAGIC = {".xls":  (b"\xd0\xcf\x11\xe0", b"PK\x03\x04"),     # Marg emits both under .xls
             ".xlsx": (b"PK\x03\x04",),
             ".pdf":  (b"%PDF",)}
SOURCES = ("manual", "push", "drive", "pc", "test")


# ------------------------------------------------------------------ helpers
def safe_name(name):
    """A file name that cannot escape a folder or carry a surprise. Never empty."""
    base = str(name or "").replace("\\", "/").split("/")[-1].strip()
    stem, ext = os.path.splitext(base)
    ext = ext.lower()
    stem = BAD_CHARS.sub("_", stem)[:120].strip("._-") or "upload"
    return stem + ext


def _connect(db):
    con = MI._connect(db)                      # creates mi_file / mi_sale_line / mi_run if absent
    try:
        con.execute("ALTER TABLE mi_file ADD COLUMN source TEXT NOT NULL DEFAULT ''")
        con.commit()
    except sqlite3.OperationalError:
        pass                                   # already there
    return con


class _Lock(object):
    """flock, with a bounded wait. A door that blocks for ever is a door that is down."""

    def __init__(self, path=LOCK_PATH, wait=None):
        # read LOCK_WAIT_S at call time, not at class-definition time: a default bound once
        # cannot be changed by a test, and a knob that cannot be exercised is not a knob.
        self.path = path
        self.wait = LOCK_WAIT_S if wait is None else wait
        self.fh = None

    def __enter__(self):
        import fcntl
        self.fh = open(self.path, "a+")
        deadline = time.time() + self.wait
        while True:
            try:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except (IOError, OSError) as e:
                if e.errno not in (errno.EAGAIN, errno.EACCES):
                    raise
                if time.time() >= deadline:
                    self.fh.close()
                    self.fh = None
                    raise RuntimeError("busy")
                time.sleep(0.5)

    def __exit__(self, *a):
        if self.fh is not None:
            import fcntl
            try:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            finally:
                self.fh.close()
                self.fh = None
        return False


def _blank(name, source):
    return dict(status="REFUSED", md5="", name=name, source=source, type="", variant="",
                verdict="", reason="", lines=0, kept=0, stamp="", server_name="",
                date_from="", date_to="", when="")


# ------------------------------------------------------------------ the door
def take(raw, name="", source="manual", db=None, archive=None):
    """Take one Marg export. Returns a dict; never raises for bad input.

    status:  TAKEN      -- new bytes, classified, recorded
             ALREADY    -- these exact bytes are already held (what was decided then is returned)
             REFUSED    -- not taken, with a reason
             BUSY       -- the archive was locked by the collector; send it again shortly
    """
    source = source if source in SOURCES else "manual"
    sname = safe_name(name)
    res = _blank(sname, source)
    if not isinstance(raw, (bytes, bytearray)) or len(raw) == 0:
        res["reason"] = "the file is empty"
        return res
    raw = bytes(raw)
    if len(raw) > MAX_BYTES:
        res["reason"] = "too big (%.1f MB); a Marg export is a few hundred KB" % (len(raw) / 1048576.0)
        return res
    ext = os.path.splitext(sname)[1].lower()
    if ext not in EXT_MAGIC:
        res["reason"] = "%s is not a Marg export (.xls, .xlsx or .pdf)" % (ext or "a file with no extension")
        return res
    if not raw.startswith(EXT_MAGIC[ext]):
        res["reason"] = "the bytes are not really a %s file" % ext
        return res

    md5 = MI.md5_bytes(raw)
    res["md5"] = md5
    db = db or MI.DB_DEFAULT
    archive = archive or MI.ARCHIVE
    con = _connect(db)
    try:
        row = con.execute("SELECT type, variant, verdict, reason, stamp, server_name, lines, kept, "
                          "date_from, date_to, received_at, source FROM mi_file WHERE md5=?",
                          (md5,)).fetchone()
        if row:
            res.update(status="ALREADY", type=row[0], variant=row[1], verdict=row[2], reason=row[3],
                       stamp=row[4], server_name=row[5], lines=row[6], kept=row[7],
                       date_from=row[8], date_to=row[9], when=row[10], source=row[11] or "")
            return res

        stamp = MI.stamp_of(sname, "") or MI.now_ist().strftime("%Y%m%d-%H%M%S")
        res["stamp"] = stamp
        try:
            lock = _Lock().__enter__()
        except RuntimeError:
            res.update(status="BUSY", reason="the archive is busy with the five-minute collection; "
                                             "send it again in a minute")
            return res
        tmpdir = tempfile.mkdtemp(prefix="take_", dir=MI.WORK if os.path.isdir(MI.WORK) else None)
        try:
            R = MI._readers()
            sigs = R.load_signatures(os.path.join(MI.HERE, "signatures.json"))
            os.makedirs(archive, exist_ok=True)
            cfg = {"archive": archive, "outbox": os.path.join(MI.WORK, "outbox"), "dry": False,
                   "index": os.path.join(archive, "index.csv")}
            seen = R.load_index(cfg["index"])
            local = os.path.join(tmpdir, sname)
            with open(local, "wb") as fh:
                fh.write(raw)
            MI.set_mtime(local, stamp)
            quiet = []
            r = R.process(local, sigs, cfg, seen, quiet.append)
            if r is None:                                  # the router already had this md5
                r = dict(seen.get(md5, {}))
            typ = r.get("type", "") or ""
            verdict = r.get("verdict", "") or ""
            dest = r.get("archived_path", "") or ""
            phi = typ in MI.PHI_TYPES or verdict != "VERIFIED" or any(
                ("%s%s" % (os.sep, x)) in dest for x in MI.PHI_FOLDERS)
            nlines = 0
            if typ == "SALE_BILLWISE" and verdict == "VERIFIED":
                rows = MI.sale_lines(local)
                nlines = len(rows)
                con.execute("DELETE FROM mi_sale_line WHERE md5=?", (md5,))
                con.executemany(
                    "INSERT INTO mi_sale_line (md5, bill_date, bill_no, is_return, seq, item_name, "
                    "pack, qty_raw, qty_strips, qty_loose, amount_p, expiry_ym, batch) VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?)", [(md5,) + t for t in rows])
            kept = 0
            if dest and os.path.exists(dest):
                if phi:
                    os.remove(dest)                        # S186: no raw export with a number at rest
                else:
                    kept = 1
            when = MI.now_ist().isoformat()
            con.execute(
                "INSERT OR REPLACE INTO mi_file (md5, drive_id, drive_name, drive_folder, drive_mtime, "
                "size, stamp, type, variant, date_from, date_to, verdict, reason, server_name, kept, "
                "lines, pc_type, pc_verdict, agree, received_at, source) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (md5, "", sname, source, "", len(raw), stamp, typ, r.get("variant", "") or "",
                 r.get("date_from", "") or "", r.get("date_to", "") or "", verdict,
                 (r.get("reason", "") or "")[:300], os.path.basename(dest), kept, nlines,
                 "", "", "", when, source))
            con.commit()
            res.update(status="TAKEN", type=typ, variant=r.get("variant", "") or "", verdict=verdict,
                       reason=(r.get("reason", "") or "")[:300], lines=nlines, kept=kept,
                       server_name=os.path.basename(dest), date_from=r.get("date_from", "") or "",
                       date_to=r.get("date_to", "") or "", when=when)
            return res
        except Exception as e:                             # noqa: BLE001
            res.update(status="REFUSED", reason="could not be read here: %s" % str(e)[:160])
            return res
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            ob = os.path.join(MI.WORK, "outbox")
            if os.path.isdir(ob):
                shutil.rmtree(ob, ignore_errors=True)      # the router's upload queue: not ours
            lock.__exit__()
    finally:
        con.close()


def recent(n=20, db=None):
    """The last files taken, newest first -- for the screen."""
    con = _connect(db or MI.DB_DEFAULT)
    try:
        return [dict(md5=r[0], name=r[1], stamp=r[2], type=r[3], variant=r[4], verdict=r[5],
                     lines=r[6], kept=r[7], date_from=r[8], date_to=r[9], when=r[10],
                     source=r[11] or "", server_name=r[12])
                for r in con.execute(
                    "SELECT md5, drive_name, stamp, type, variant, verdict, lines, kept, date_from, "
                    "date_to, received_at, source, server_name FROM mi_file "
                    "ORDER BY received_at DESC, rowid DESC LIMIT ?", (int(n),))]
    finally:
        con.close()


def counts(db=None):
    con = _connect(db or MI.DB_DEFAULT)
    try:
        tot = con.execute("SELECT COUNT(*) FROM mi_file").fetchone()[0]
        ver = con.execute("SELECT COUNT(*) FROM mi_file WHERE verdict='VERIFIED'").fetchone()[0]
        today = con.execute("SELECT COUNT(*) FROM mi_file WHERE received_at >= ?",
                            (MI.now_ist().strftime("%Y-%m-%d"),)).fetchone()[0]
        return dict(total=tot, verified=ver, today=today)
    finally:
        con.close()
