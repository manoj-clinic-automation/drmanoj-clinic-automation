#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s946_verdict_cleanup.py -- S946 (the parent, S512, 24-Nov-2026) -- roadmap S510 A2, the one-off on Call_Verdicts.

WHAT IT DOES (the Call Audit sheet, doctor-only; tab Call_Verdicts)
  1. BACKUP first: the whole tab to an owner-only CSV (dir 0700, file 0600) under --backup-dir;
     the file is read back and its row count must equal the tab's, or nothing goes on.
  2. DEBRIS: a row whose Status is not 'done' while the SAME Join Key has a 'done' row (the call was
     judged by a later run -- S510 plan v2 s2.5: the 1,374 August 'FAILED' rows) is removed.
     A FAILED row whose call has NO done row is NOT debris and stays (the night sweep's retry candidate).
  3. THE JULY CALLS: a Call_Transcripts row with Status 'done', Date in 2026-07, whose Join Key has no row
     at all in Call_Verdicts (the judge's history starts after them) gets ONE row: Status 'done',
     Verdict 'Not judgeable', Error 'before the stage (S946)' -- so no reader counts it as waiting.
  4. READ BACK: rows after = rows before - debris + marked; no debris left.
  --dry does 1 (the backup) and the counts, writes nothing to the sheet.
  The pipeline lock (/root/wa/recordings-archive/pipeline.lock) is taken BEFORE the first read (waited for, up to
  10 min) and held through the read-back: the at-hangup worker waits (its kicks stay queued), so no concurrent
  writer sees shifted rows and no row appears between the read and the delete. Not inside 01:55-04:05 IST (the
  night sweeps do not take the lock) -- the installer refuses that window.

  Nothing patient-level is printed: counts, months and row numbers only.

USAGE (on the box)
  /root/wa/venv/bin/python3 s946_verdict_cleanup.py --dry  --backup-dir /root/wa/recordings-archive/backup_S946
  /root/wa/venv/bin/python3 s946_verdict_cleanup.py        --backup-dir /root/wa/recordings-archive/backup_S946
  --fake DIR   the walk: DIR/Call_Verdicts.csv and DIR/Call_Transcripts.csv stand in for the two tabs
               (written back to DIR after the live step); no network, no lock.
Python 3.9 compatible.
"""
import argparse
import csv
import datetime
import fcntl
import os
import sys
import time

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
RA_DIR = os.environ.get("S946_RA_DIR", "").strip() or "/root/wa/recordings-archive"
LOCK_PATH = os.path.join(RA_DIR, "pipeline.lock")
LOCK_WAIT_S = int(os.environ.get("S946_LOCK_WAIT_S", "600"))
JULY = "2026-07"
MARK_VERDICT = "Not judgeable"
MARK_ERROR = "before the stage (S946)"


def say(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------
class FakeWorksheet(object):
    """A CSV-backed stand-in for a gspread worksheet: the walk's tabs."""

    def __init__(self, path, title):
        self.path, self.title, self.id = path, title, 7
        with open(path, "r", encoding="utf-8", newline="") as f:
            self.rows = [list(r) for r in csv.reader(f)]

    def get_all_values(self):
        return [list(r) for r in self.rows]

    def append_rows(self, values, value_input_option="RAW"):
        self.rows.extend([list(v) for v in values])
        self._flush()

    def delete_ranges(self, ranges):                 # [(start0, end0), ...] descending, 0-based, end exclusive
        for s0, e0 in ranges:
            del self.rows[s0:e0]
        self._flush()

    def _flush(self):
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(self.rows)


class RealWorksheet(object):
    def __init__(self, ws, spreadsheet):
        self.ws, self.ss, self.title, self.id = ws, spreadsheet, ws.title, ws.id

    def get_all_values(self):
        return self.ws.get_all_values()

    def append_rows(self, values, value_input_option="RAW"):
        self.ws.append_rows(values, value_input_option=value_input_option)

    def delete_ranges(self, ranges):
        reqs = [{"deleteDimension": {"range": {"sheetId": self.id, "dimension": "ROWS",
                                               "startIndex": s0, "endIndex": e0}}} for s0, e0 in ranges]
        if reqs:
            self.ss.batch_update({"requests": reqs})


# ---------------------------------------------------------------------------
def open_tabs(fake_dir):
    if fake_dir:
        return (FakeWorksheet(os.path.join(fake_dir, "Call_Verdicts.csv"), "Call_Verdicts"),
                FakeWorksheet(os.path.join(fake_dir, "Call_Transcripts.csv"), "Call_Transcripts"))
    sys.path.insert(0, RA_DIR)
    import call_verdict as cv                      # the stage's own helpers: .env, the client, the ids, the header
    import gspread as _gs
    from google.oauth2.service_account import Credentials as _C
    cv.gspread, cv.Credentials = _gs, _C
    cv.load_env()
    client = cv.get_sheets_client()
    tracker = client.open_by_key(os.environ.get("TRACKER_SHEET_ID", cv.DEFAULT_TRACKER_SHEET_ID))
    audit = client.open_by_key(os.environ.get("AUDIT_SHEET_ID", cv.DEFAULT_AUDIT_SHEET_ID))
    ws_v = audit.worksheet(cv.VERDICT_TAB)
    ws_t = tracker.worksheet(cv.TRANSCRIPT_TAB)
    return RealWorksheet(ws_v, audit), RealWorksheet(ws_t, tracker)


def backup(values, backup_dir, title):
    os.makedirs(backup_dir, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    stamp = datetime.datetime.now(IST).strftime("%Y%m%d-%H%M%S")
    path = os.path.join(backup_dir, "%s_%s.csv" % (title, stamp))
    k = 0
    while os.path.exists(path):                     # two backups in one second (the dry read, then the live run)
        k += 1
        path = os.path.join(backup_dir, "%s_%s_%d.csv" % (title, stamp, k))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(values)
    with open(path, "r", encoding="utf-8", newline="") as f:
        n = sum(1 for _ in csv.reader(f))
    if n != len(values):
        raise SystemExit("!! backup read back %d rows, the tab has %d -- STOP, nothing changed" % (n, len(values)))
    return path, n


def col(header, name):
    return header.index(name) if name in header else None


def cell(row, i):
    return (row[i] if (i is not None and i < len(row)) else "").strip()


def find_debris(values):
    """Row numbers (1-based, sheet) of non-done rows whose Join Key has a done row; plus counts."""
    header = values[0]
    jk, st, dt = col(header, "Join Key"), col(header, "Status"), col(header, "Date")
    if jk is None or st is None:
        raise SystemExit("!! Call_Verdicts has no Join Key / Status column -- STOP")
    done_keys = set()
    for row in values[1:]:
        if cell(row, st) == "done" and cell(row, jk):
            done_keys.add(cell(row, jk))
    debris, by_month, kept_failed = [], {}, 0
    for n, row in enumerate(values[1:], start=2):
        if cell(row, st) == "done":
            continue
        k = cell(row, jk)
        if k and k in done_keys:
            debris.append(n)
            m = cell(row, dt)[:7] or "?"
            by_month[m] = by_month.get(m, 0) + 1
        else:
            kept_failed += 1
    return debris, by_month, kept_failed, done_keys


def find_july(tvalues, vvalues):
    """Transcript rows (done, July, join key absent from EVERY verdict row)."""
    th = tvalues[0]
    tjk, tst, tdt = col(th, "Join Key"), col(th, "Status"), col(th, "Date")
    if tjk is None or tst is None or tdt is None:
        raise SystemExit("!! Call_Transcripts lacks Join Key / Status / Date -- STOP")
    vh = vvalues[0]
    vjk = col(vh, "Join Key")
    all_keys = set(cell(r, vjk) for r in vvalues[1:] if cell(r, vjk))
    out, seen = [], set()
    for row in tvalues[1:]:
        if cell(row, tst) != "done" or not cell(row, tdt).startswith(JULY):
            continue
        k = cell(row, tjk)
        if not k or k in all_keys or k in seen:
            continue
        seen.add(k)
        out.append(row)
    return out


def mark_rows(july_rows, theader, vheader):
    now = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    fixed = {"Status": "done", "Verdict": MARK_VERDICT, "Error": MARK_ERROR, "Judged At": now,
             "Prompt Ver": "", "Model": "S946", "AI Outcome": "", "Match Confidence": "none"}
    out = []
    for trow in july_rows:
        trec = {theader[i]: cell(trow, i) for i in range(len(theader))}
        row = []
        for name in vheader:
            if name in fixed:
                row.append(fixed[name])
            elif name == "Transcript Link":
                row.append(trec.get("Transcript Drive Link", ""))
            elif name in ("Date", "Time", "Direction", "Duration", "Join Key"):
                row.append(trec.get(name, ""))
            else:
                row.append("")
        out.append(row)
    return out


def ranges_desc(rows):
    """1-based sheet rows -> [(start0, end0)] contiguous, descending, 0-based end-exclusive."""
    rows = sorted(set(rows))
    out = []
    i = 0
    while i < len(rows):
        j = i
        while j + 1 < len(rows) and rows[j + 1] == rows[j] + 1:
            j += 1
        out.append((rows[i] - 1, rows[j]))
        i = j + 1
    return sorted(out, reverse=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--backup-dir", default=os.path.join(RA_DIR, "backup_S946"))
    ap.add_argument("--fake", default=None, help="walk: a folder with the two CSVs")
    a = ap.parse_args(argv)
    a.fake = a.fake or os.environ.get("S946_FAKE_DIR", "").strip() or None     # the rehearsal's stand-in tabs

    ws_v, ws_t = open_tabs(a.fake)
    lock_f = None
    if not a.fake or os.environ.get("S946_LOCK_IN_FAKE") == "1":   # the whole read-decide-write-read-back under the pipeline lock (MUST 1, cold review)
        lock_f = open(LOCK_PATH, "w")
        waited = 0
        while True:
            try:
                fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if waited >= LOCK_WAIT_S:
                    lock_f.close()
                    raise SystemExit("!! the pipeline held its lock for %d s -- try again later; nothing changed" % waited)
                if waited == 0:
                    say("the pipeline is running -- waiting for its lock (up to %d s)" % LOCK_WAIT_S)
                time.sleep(5)
                waited += 5
    try:
        return _main_locked(a, ws_v, ws_t)
    finally:
        if lock_f is not None:
            try:
                fcntl.flock(lock_f, fcntl.LOCK_UN)
            except OSError:
                pass
            lock_f.close()


def _main_locked(a, ws_v, ws_t):
    vvalues = ws_v.get_all_values()
    tvalues = ws_t.get_all_values()
    if len(vvalues) < 2 or len(tvalues) < 2:
        raise SystemExit("!! an empty tab (verdicts %d rows, transcripts %d) -- STOP" % (len(vvalues), len(tvalues)))
    vheader = vvalues[0]
    for need in ("Join Key", "Status", "Verdict", "Error", "Judged At", "Date"):
        if need not in vheader:
            raise SystemExit("!! Call_Verdicts header lacks %r -- STOP" % need)

    bpath, bn = backup(vvalues, a.backup_dir, ws_v.title)
    say("BACKUP %s rows -> %s (0600)" % (bn, bpath))

    st = col(vheader, "Status")
    n_done = sum(1 for r in vvalues[1:] if cell(r, st) == "done")
    debris, by_month, kept_failed, done_keys = find_debris(vvalues)
    july = find_july(tvalues, vvalues)
    say("BEFORE rows %d (done %d, not done %d) . debris %d [%s] . failed kept (no done row) %d . July calls to mark %d"
        % (len(vvalues) - 1, n_done, len(vvalues) - 1 - n_done, len(debris),
           ", ".join("%s %d" % (m, c) for m, c in sorted(by_month.items())) or "-", kept_failed, len(july)))
    if not july:
        say("WARN: no July call to mark -- either already marked, or the transcripts' Date is not written 2026-07-DD (read the DRY line)")
    if a.dry:
        say("DRY: nothing written to the sheet")
        return 0

    if debris:
        ws_v.delete_ranges(ranges_desc(debris))
    marked = mark_rows(july, tvalues[0], vheader)
    if marked:
        ws_v.append_rows(marked, value_input_option="RAW")

    after = ws_v.get_all_values()
    d2, _, kept2, _ = find_debris(after)
    want = len(vvalues) - 1 - len(debris) + len(july)
    n_done2 = sum(1 for r in after[1:] if cell(r, st) == "done")
    say("AFTER rows %d (done %d) . debris left %d . failed kept %d . expected rows %d"
        % (len(after) - 1, n_done2, len(d2), kept2, want))
    if len(after) - 1 != want or d2 or kept2 != kept_failed or n_done2 != n_done + len(july):
        say("!! CLEANUP RED: the tab after is not as expected -- the backup is %s; tell Claude" % bpath)
        return 1
    say("CLEANUP OK: removed %d, marked %d" % (len(debris), len(july)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
