#!/usr/bin/env python3
"""
call_log_db.py -- the call log on the server: table call_log_raw in /root/wa/calls.db.
S949 (the parent, S516, 24-Nov-2026) -- roadmap S510 F1, its first half (F1a).

ONE WRITER: call_hook_capture.py (the MyOperator webhook) calls upsert() for every call it would put on the
Call_Durations Sheet -- the table FIRST, the Sheet second. The Sheet stays as it is (its readers are untouched) until the
nightly compare (call_log_compare.py, 23:40) has shown the table equal to the Sheet; only then (F1b) do the console builder
and the write probe read the table.

The row is the Sheet's row: the same 14 fields (HEADER, in the same order) from the same extract_record(), keyed the same
way (client_ref_id; ref_id -- MyOperator's own uuid -- as the second key, so the two events of one call stay one row even
if a session id differs). Three bookkeeping columns: events (how many webhook events wrote the row), first_written_at,
written_at (IST). Values are stored as given (no column type), so a duration stays a number.

PHI: phone10 (incoming / app-dialled rows) and the OBD client_ref_id carry a patient number -- exactly what the Sheet holds.
The file is made 0600 inside /root/wa (root only). Nothing here prints a key or a number.

DEGRADE-SAFE: the hook wraps every call in its own try/except; a failure here never touches the Sheet write or the reply.
The raw jsonl log stays the recovery truth.
"""
import os
import sqlite3
import datetime

_DB_ENV = os.environ.get("CALLHOOK_DB", "").strip()
DB_PATH = _DB_ENV if os.path.isabs(_DB_ENV) else "/root/wa/calls.db"     # only a full path is a path (off/on/1 are not)
TABLE = "call_log_raw"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

HEADER = [
    "client_ref_id", "ref_id", "session_id", "category", "status",
    "total_duration", "customer_result", "customer_talk_duration",
    "customer_ring_duration", "recording_filename",
    "ended_at_ist", "captured_at_ist", "source_event",
    "phone10",
]

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS call_log_raw ("
    " client_ref_id TEXT PRIMARY KEY, ref_id, session_id, category, status,"
    " total_duration, customer_result, customer_talk_duration, customer_ring_duration, recording_filename,"
    " ended_at_ist, captured_at_ist, source_event, phone10,"
    " events INTEGER NOT NULL DEFAULT 1, first_written_at TEXT, written_at TEXT)",
    "CREATE INDEX IF NOT EXISTS ix_call_log_raw_ref ON call_log_raw(ref_id)",
    "CREATE INDEX IF NOT EXISTS ix_call_log_raw_ended ON call_log_raw(ended_at_ist)",
    "CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)",
)


def now_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"


def _owner_only(path):
    for p in (path, path + "-journal"):
        try:
            if os.path.exists(p):
                os.chmod(p, 0o600)
        except OSError:
            pass


def connect(path=None, readonly=False, timeout=5):
    """A connection with a 5-second busy wait. readonly=True opens the file read-only (the compare, later the builder);
    a missing file is then an error, never created."""
    path = path or DB_PATH
    if readonly:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=timeout)
    else:
        con = sqlite3.connect(path, timeout=timeout)
    con.row_factory = sqlite3.Row
    return con


def init(path=None):
    """Create the table and the meta row 'started_at' (the first moment the table was written; the compare's window
    starts there). Idempotent. Returns (rows, started_at)."""
    path = path or DB_PATH
    con = connect(path)
    try:
        with con:
            for s in _SCHEMA:
                con.execute(s)
            con.execute("INSERT OR IGNORE INTO meta (k, v) VALUES ('started_at', ?)", (now_ist(),))
            con.execute("INSERT OR IGNORE INTO meta (k, v) VALUES ('writer', 'call_hook_capture.py (S949)')")
        n = con.execute("SELECT COUNT(*) FROM call_log_raw").fetchone()[0]
        started = con.execute("SELECT v FROM meta WHERE k='started_at'").fetchone()[0]
    finally:
        con.close()
    _owner_only(path)
    return n, started


def _val(rec, h):
    v = rec.get(h, "")
    return "" if v is None else v


def upsert(rec, path=None):
    """Insert or update one row, the Sheet's way: found by client_ref_id, else by ref_id (the newest row carrying it);
    an update rewrites all 14 fields -- the key included, as the Sheet rewrites column A. Returns 'inserted'|'updated'."""
    path = path or DB_PATH
    key = str(rec.get("client_ref_id") or "").strip()
    if not key:
        raise ValueError("no client_ref_id")
    ref = str(rec.get("ref_id") or "").strip()
    vals = [_val(rec, h) for h in HEADER]
    vals[0] = key
    stamp = now_ist()
    con = connect(path, timeout=2)          # the webhook waits at most 2 s on a busy file
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT client_ref_id FROM call_log_raw WHERE client_ref_id=?", (key,)).fetchone()
        if row is None and ref:
            row = con.execute("SELECT client_ref_id FROM call_log_raw WHERE ref_id=? ORDER BY written_at DESC LIMIT 1",
                              (ref,)).fetchone()
        if row is not None:
            sets = ", ".join("%s=?" % h for h in HEADER)
            con.execute("UPDATE call_log_raw SET %s, events=events+1, written_at=? WHERE client_ref_id=?" % sets,
                        vals + [stamp, row[0]])
            action = "updated"
        else:
            cols = ", ".join(HEADER)
            con.execute("INSERT INTO call_log_raw (%s, events, first_written_at, written_at) VALUES (%s, 1, ?, ?)"
                        % (cols, ", ".join("?" * len(HEADER))), vals + [stamp, stamp])
            action = "inserted"
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except Exception:               # noqa: BLE001
            pass
        raise
    finally:
        con.close()
    return action


def started_at(path=None):
    con = connect(path, readonly=True)
    try:
        r = con.execute("SELECT v FROM meta WHERE k='started_at'").fetchone()
        return r[0] if r else ""
    finally:
        con.close()


def rows(path=None):
    """Every row as a dict of the 14 fields (the compare's view)."""
    con = connect(path, readonly=True)
    try:
        return [{h: r[h] for h in HEADER} for r in con.execute("SELECT %s FROM call_log_raw" % ", ".join(HEADER))]
    finally:
        con.close()


def _selftest():
    import tempfile
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL: %s" % name)

    num = "5" + "0" * 8 + "1"          # a made-up ten-digit number, built at run time (F-185)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "calls.db")
        n, st = init(p)
        check("init: empty table, started_at set", n == 0 and st.endswith("+05:30"))
        check("init: 0600", (os.stat(p).st_mode & 0o777) == 0o600)
        n2, st2 = init(p)
        check("init again: started_at kept", st2 == st)
        rec = {h: "" for h in HEADER}
        rec.update({"client_ref_id": "IN-s1", "ref_id": "u1", "session_id": "s1", "category": "incoming",
                    "status": "bridged", "total_duration": 82, "customer_talk_duration": 80, "phone10": num,
                    "source_event": "call.end"})
        check("first event inserts", upsert(rec, p) == "inserted")
        rec2 = dict(rec, source_event="call.summary", recording_filename="r.mp3")
        check("second event of the call updates", upsert(rec2, p) == "updated")
        rs = rows(p)
        check("one row for the pair", len(rs) == 1 and rs[0]["recording_filename"] == "r.mp3")
        check("a duration stays a number", rs[0]["total_duration"] == 82)
        rec3 = dict(rec2, client_ref_id="IN-s1b", session_id="s1b")
        check("changed session id, same uuid: updates", upsert(rec3, p) == "updated")
        rs = rows(p)
        check("the key rewritten as the Sheet does", len(rs) == 1 and rs[0]["client_ref_id"] == "IN-s1b")
        con = connect(p, readonly=True)
        ev = con.execute("SELECT events FROM call_log_raw").fetchone()[0]
        con.close()
        check("events counted", ev == 3)
        other = dict(rec, client_ref_id="R2", ref_id="", category="obd", phone10="")
        check("a second call inserts", upsert(other, p) == "inserted" and len(rows(p)) == 2)
        check("blank ref_id never matches another row", upsert(dict(other, client_ref_id="R3"), p) == "inserted")
        try:
            upsert(dict(rec, client_ref_id=""), p)
            check("no key refused", False)
        except ValueError:
            check("no key refused", True)
        check("readonly connect refuses a missing file", _ro_missing(os.path.join(td, "none.db")))
        check("started_at read", started_at(p) == st)
    print("selftest: %d/%d passed" % (passed, passed + failed))
    return 0 if failed == 0 else 1


def _ro_missing(p):
    try:
        connect(p, readonly=True).execute("SELECT 1 FROM meta").fetchone()
        return False
    except sqlite3.Error:
        return not os.path.exists(p)


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if "--check" in sys.argv:
        try:
            print("call log table: %d rows since %s (%s)" % (len(rows()), started_at(), DB_PATH))
        except Exception as e:          # noqa: BLE001
            print("call log table: not readable (%s)" % type(e).__name__)
            sys.exit(1)
        sys.exit(0)
    print("usage: call_log_db.py --selftest | --check")
