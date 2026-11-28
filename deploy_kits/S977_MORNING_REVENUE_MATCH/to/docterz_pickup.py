#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docterz_pickup.py -- kit S443_DOCTERZ_PICKUP (session 287, 01-Oct-2026, D645). PARENT. NEW.

THE OWNER, 30-Sep / 01-Oct-2026: the Docterz export is picked up from the reception PC. Chrome on that PC saves its
downloads into the clinic Drive folder "Docterz exports" (Clinic Records / Docterz exports, made 01-Oct, shared read-only
with the box's own service account) -- the same road as the X-ray inbox: Drive for Desktop (clinic account) is already on
that PC. The one human step is staff exporting the two reports.

WHAT THIS DOES, every 15 minutes (cron, venv python):
  * lists the folder with the read-only service account (docterz_ingest's own credential, nothing new);
  * IDENTIFIES EACH FILE BY ITS CONTENT, never by its name: a consultation report carries the columns
    "Consultation Date" and "Mode Of Payment"; a follow-up log carries "Appointment ID" and "Mobile No".
    Anything else is recorded as 'unknown' and left alone;
  * the business day comes from the content too: a consultation report is the day of its latest consultation (Docterz
    names a file by the DOWNLOAD day -- the tracker's own finding); a follow-up log is its earliest due date minus one day
    (the tracker's rule: Docterz generates it a day ahead);
  * A DAY IS REPLACED, NEVER APPENDED: the newest export of a kind and day wins; the one it replaces is kept as
    'superseded'. A NEWER FILE WITH FEWER ROWS is QUARANTINED and shouted (S223 spec section 3) -- it never replaces;
  * the bytes are kept on the box only (/root/finance/docterz_exports/<kind>/, mode 600) -- they carry patient
    names and numbers, so they never enter the repository or a log (F-185).
S507 (10-Oct-2026): on Saturday 10-Oct reception exported the follow-up log for ONE day -- Sunday 11-Oct -- so the next call
day (Monday 12-Oct) was not in it and Monday's call list would have been empty; the duty lines counted the file as 'there'.
Now each follow-up log records the due dates it covers (due_from / due_to, two columns added by ensure() on first use, filled in
for the logs already kept, by themselves) and a log that does not reach the next call day (the day after, Sunday skipped) is
NOT a done export: reception's evening and morning lines stay up, and the owner's page says so. A one-day export of the next
call day is enough (the tracker loads only that day); Docterz's default one-month export always is.
S509 (the owner, 10-Oct-2026 22:38): "we simply open the follow-up logs in Docterz and it shows the default from date as the
current date until one month and we export it as such ... no date fields need to be altered". So a follow-up log's day is
no longer its earliest due date minus one (that rule needed the start date moved to tomorrow by hand): it is the day it was
EXPORTED (IST), and an export made before 13:00 belongs to the previous working day (the morning catch-up of a missed evening).
The earliest-due rule stays only for a file with no export time. Docterz's default (today .. one month) reaches the next call
day by itself; the tracker on the owner's PC already anchors a log to the consultation day (03-Oct proved it).
S779 (S424, 10-Nov-2026, D884): Docterz's CLINICAL DATA REPORT carries the consultation columns too (Consultation Date, Mode Of
Payment), so identify() took it for a consultation report -- a catch-up export of months would have replaced the day's real one.
It is now a third kind, 'clinical' (it carries Diagnosis and Drugs Prescribed): kept by its bytes, never replacing or replaced
by day (one export may span months), and read into the per-visit diagnosis table by dx_feed.py the moment it is taken.
S868 (18-Nov-2026, the owner: on the days he does not sit, the EMPTY consultation report was set aside as "no date in the
file" and his pages called the day missing): a consultation report with no patients in it belongs to the day it was exported
(export_day, as a follow-up log) and, when that day has no OPD slip or is marked 'not sitting' (off_days.py), it is taken as
that day's report -- CURRENT, 0 rows, nothing stored (reception's PC never gets an empty file back) -- and the day is marked
not sitting by the server. An empty report on a day WITH OPD slips is set aside and said. A report WITH patients clears a
not-sitting mark of its day (he sat). The empty reports set aside before S868 ('no date in the file', 0 rows) are no longer
shouted on his page.
S960 (S527, 26-Nov-2026, D1080 -- the Morning Match's evening check): a consultation report taken as the CURRENT one starts
evening_check.py in its own process (_s960_evening): it reads the stored export at once and tells Shavez and reception which of
the day's slips Docterz does not carry -- or that all are in. The take never waits for it and nothing there can fail the take;
EVCHK_SPAWN=0 turns the start off. A second cron line picks up from Drive every minute 19:00-22:59 Mon-Sat and then runs
evening_check.py --sweep, which judges an evening export no check judged (# S960_EVENING_PICKUP).
THE ALARM: no consultation export for the last working day (Sunday closed) by 10:00 IST -> a red line on the owner's
money page (clinic_money asks owner_lines(); fail-soft). It heals by itself the moment the export lands.

THIS KIT DOES NOT MOVE THE FOLLOW-UP TRACKER. Reading it whole (S287) showed it carries its own live ledgers on the PC
(patient master, visit / follow-up / call / revenue ledgers, concessions, manual procedures) and staff forms that write
them; relocating it is a cut-over of live state, not a copy of code -- put to the owner as a decision first (the plan's
own "unless reading it whole shows a surprise -- say so before going on"). These exports are exactly what the relocated
tracker will read.

    /root/wa/venv/bin/python3 -B /root/finance/docterz_pickup.py [--db PATH] [--dry-run] [--status]
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER_DEFAULT = "1JjWcfk_7IzSBQUbLlbNWPvf96LGcjjDt"     # Clinic Records / Docterz exports (drmka.ortho), 01-Oct-2026
STORE = os.environ.get("DOCTERZ_EXPORT_STORE", os.path.join(HERE, "docterz_exports"))
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
ALARM_HHMM = (10, 0)
KINDS = {"consultation": "consultation report", "followup": "follow-up log", "clinical": "clinical data report"}

DDL = """
CREATE TABLE IF NOT EXISTS docterz_export (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  drive_id      TEXT NOT NULL,
  drive_name    TEXT NOT NULL DEFAULT '',
  drive_mtime   TEXT NOT NULL DEFAULT '',
  md5           TEXT NOT NULL,
  kind          TEXT NOT NULL,
  business_date TEXT NOT NULL DEFAULT '',
  rows          INTEGER NOT NULL DEFAULT 0,
  stored        TEXT NOT NULL DEFAULT '',
  status        TEXT NOT NULL,
  note          TEXT NOT NULL DEFAULT '',
  taken_at      TEXT NOT NULL,
  UNIQUE (drive_id, drive_mtime)
);
CREATE INDEX IF NOT EXISTS ix_docterz_export_day ON docterz_export(kind, business_date, status);
"""


def now():
    return dt.datetime.now().replace(microsecond=0)


def ensure(con):
    con.executescript(DDL)
    _span_cols(con)


def _span_cols(con):
    """S507: the due dates a follow-up log covers -- two columns, added once (no COMMIT of anyone's transaction)."""
    try:
        have = {r[1] for r in con.execute("PRAGMA table_info(docterz_export)")}
        for c in ("due_from", "due_to"):
            if c not in have:
                con.execute("ALTER TABLE docterz_export ADD COLUMN %s TEXT NOT NULL DEFAULT ''" % c)
    except sqlite3.Error:                                    # a read-only connection: the columns come with the next pass
        pass


def next_call_day(day_iso):
    """S507: the day after `day_iso`, Sunday skipped (the clinic is closed on Sunday)."""
    d = dt.date.fromisoformat(day_iso) + dt.timedelta(days=1)
    return (d + dt.timedelta(days=1) if d.weekday() == 6 else d).isoformat()


def followup_span(raw):
    """S507: (earliest, latest) due date of a follow-up log, iso; ('', '') when it is not one or carries no date."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            return "", ""
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return "", ""
    if not rows:
        return "", ""
    head = [h.strip() for h in rows[0]]
    idx = {h: i for i, h in enumerate(head)}
    dkey = next((h for h in head if h.lower().replace("_", " ") in ("due date", "follow up date", "followup date", "follow-up date")), None)
    if not dkey or "Appointment ID" not in idx:
        return "", ""
    dates = [parse_date(r[idx[dkey]]) for r in rows[1:] if len(r) > idx[dkey]]
    dates = [d for d in dates if d]
    return (min(dates).isoformat(), max(dates).isoformat()) if dates else ("", "")


def backfill_spans(con):
    """S507: the follow-up logs kept before the two columns existed get their due dates from their own stored bytes (once)."""
    n = 0
    for rid, stored in con.execute("SELECT id, stored FROM docterz_export WHERE kind='followup' AND COALESCE(due_to,'')='' "
                                   "AND COALESCE(stored,'')<>''").fetchall():
        try:
            with open(stored, "rb") as fh:
                a, b = followup_span(fh.read())
        except OSError:
            continue
        if b:
            con.execute("UPDATE docterz_export SET due_from=?, due_to=? WHERE id=?", (a, b, rid))
            n += 1
    con.commit()
    return n


def folder_id(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='docterz_exports.folder_id'").fetchone()
        if r and (r[0] or "").strip():
            return r[0].strip()
    except sqlite3.Error:
        pass
    return FOLDER_DEFAULT


def parse_date(s):
    s = str(s or "").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def identify(raw):
    """(kind, business_date iso or '', data rows, note) -- by content alone."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            return "unknown", "", 0, "not text"
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return "unknown", "", 0, "not a CSV"
    if not rows:
        return "unknown", "", 0, "empty"
    head = [h.strip() for h in rows[0]]
    body = [r for r in rows[1:] if any(c.strip() for c in r)]
    idx = {h: i for i, h in enumerate(head)}
    if "Consultation Date" in idx and "Diagnosis" in idx and "Drugs Prescribed" in idx:
        # S779: the clinical data report -- before the consultation test, whose two columns it also carries
        dates = [parse_date(r[idx["Consultation Date"]]) for r in body if len(r) > idx["Consultation Date"]]
        dates = [d for d in dates if d]
        return ("clinical", (max(dates).isoformat() if dates else ""), len(dates),
                ("covers %s to %s" % (min(dates).isoformat(), max(dates).isoformat())) if dates else "")
    if "Consultation Date" in idx and "Mode Of Payment" in idx:
        # row 1 may be the clinic's own name (the tracker drops it): it carries no date
        dates = [parse_date(r[idx["Consultation Date"]]) for r in body if len(r) > idx["Consultation Date"]]
        dates = [d for d in dates if d]
        real = [r for r in body if len(r) > idx["Consultation Date"] and parse_date(r[idx["Consultation Date"]])]
        return "consultation", (max(dates).isoformat() if dates else ""), len(real), ""
    if "Appointment ID" in idx and "Mobile No" in idx:
        dkey = next((h for h in head if h.lower().replace("_", " ") in ("due date", "follow up date", "followup date", "follow-up date")), None)
        dates = [parse_date(r[idx[dkey]]) for r in body if dkey and len(r) > idx[dkey]] if dkey else []
        dates = [d for d in dates if d]
        return "followup", ((min(dates) - dt.timedelta(days=1)).isoformat() if dates else ""), len(body), ("" if dkey else "no due-date column")
    return "unknown", "", len(body), "columns: " + ", ".join(head[:6])


def export_day(f, fallback):
    """S509: the business day of a follow-up log -- the IST day of its export time; before 13:00, the previous working day
    (Sunday skipped). `fallback` (the earliest-due rule) when the file carries no time."""
    t = str((f or {}).get("modifiedTime") or "")
    try:
        u = dt.datetime.strptime(t[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return fallback
    ist = u + dt.timedelta(hours=5, minutes=30)
    d = ist.date()
    if ist.hour < 13:
        d -= dt.timedelta(days=1)
    while d.weekday() == 6:
        d -= dt.timedelta(days=1)
    return d.isoformat()


def _s868_off(con, day):
    """S868: (is the day one he did not sit, why) -- marked by him or the server (off_days), or no OPD slip that day."""
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE name='clinic_off_day'").fetchone() and \
                con.execute("SELECT 1 FROM clinic_off_day WHERE day=?", (day,)).fetchone():
            return True, "marked not sitting"
        n = con.execute("SELECT COUNT(*) FROM slip WHERE day=? AND series='opd' AND state='ok'", (day,)).fetchone()[0]
        return (int(n or 0) == 0), ("no OPD slip that day" if not n else "%d OPD slip(s) that day" % int(n))
    except sqlite3.Error:
        return False, "the slips could not be read"


def _s960_evening(con, f):
    """S960 (D1080): start evening_check.py for this export in its own, fully detached process -- never waited for, never a
    reason for the take to fail. EVCHK_SPAWN=0 turns it off; EVCHK_PY names the python (the box's venv by default)."""
    if os.environ.get("EVCHK_SPAWN", "1") == "0":
        return False
    try:
        r = con.execute("SELECT id FROM docterz_export WHERE drive_id=? AND drive_mtime=?", (f["id"], f.get("modifiedTime") or "")).fetchone()
        path = con.execute("PRAGMA database_list").fetchone()[2]
        script = os.path.join(HERE, "evening_check.py")
        if r is None or not path or not os.path.isfile(script):
            return False
        py = os.environ.get("EVCHK_PY", "/root/wa/venv/bin/python3")
        if not os.path.isfile(py):
            py = sys.executable
        logd = os.path.join(HERE, "logs")
        os.makedirs(logd, exist_ok=True)
        env = dict(os.environ, EVCHK_LOGF=os.path.join(logd, "evening_check.log"))
        p = subprocess.Popen(["/bin/sh", "-c", '"$@" </dev/null >>"$EVCHK_LOGF" 2>&1 &', "s960", py, "-B", script,
                              "--export", str(int(r[0])), "--db", path], env=env, cwd=HERE, close_fds=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait(timeout=10)
        return True
    except Exception:                                        # noqa: BLE001 -- the take never fails for this
        return False


def take(con, f, raw, dry=False):
    """One file: identify, store, and replace the day only when it should. Returns the status written."""
    md5 = hashlib.md5(raw).hexdigest()
    kind, day, nrows, note = identify(raw)
    s868_empty = None                                          # S868: an empty consultation report -- None / 'off' / 'worked'
    if kind == "consultation" and not day and nrows == 0:
        eday = export_day(f, "")
        if eday:
            off, why_off = _s868_off(con, eday)
            day, s868_empty = eday, ("off" if off else "worked")
            note = ("no consultations in it -- Dr Manoj not sitting (%s)" % why_off) if off else \
                   ("EMPTY, yet %s -- export the consultation report of that day again" % why_off)
    if kind == "followup" and day:
        day = export_day(f, day)                               # S509: the day it was exported, not its earliest due date minus one
    st, stored = kind if kind == "unknown" else "current", ""
    if kind != "unknown":
        if not day:
            st, note = "quarantined", "no date in the file"
        elif s868_empty == "worked" and con.execute("SELECT 1 FROM docterz_export WHERE kind=? AND business_date=? AND status='current' "
                                                    "AND rows>0", (kind, day)).fetchone() is not None:
            st, note = "superseded", "an empty report after the day's real export -- nothing to take (F-1732)"   # S977
        elif s868_empty == "worked":
            st = "quarantined"                                 # S868: an empty report never stands for a day he worked
        else:
            if kind == "clinical":                             # S779: by its bytes only -- one export may span months
                cur = con.execute("SELECT * FROM docterz_export WHERE kind=? AND md5=? AND status='current'", (kind, md5)).fetchone()
            else:
                cur = con.execute("SELECT * FROM docterz_export WHERE kind=? AND business_date=? AND status='current'", (kind, day)).fetchone()
            if cur is not None and cur["md5"] == md5:
                st, note = "duplicate", "same bytes as export #%d" % cur["id"]
            elif cur is not None and (f["modifiedTime"] or "") < (cur["drive_mtime"] or ""):
                st, note = "superseded", "older than export #%d" % cur["id"]
            elif s868_empty and cur is not None and cur["rows"] > 0:   # S868 review 5: an empty report after the day's real one
                st, note = "superseded", "an empty report after the day's real export #%d -- nothing to take" % cur["id"]
            elif cur is not None and nrows < cur["rows"]:
                st, note = "quarantined", "FEWER ROWS (%d) than export #%d (%d) -- not taken; check the export" % (nrows, cur["id"], cur["rows"])
            elif cur is not None and not dry:
                con.execute("UPDATE docterz_export SET status='superseded', note=? WHERE id=?", ("replaced by a newer export", cur["id"]))
        if st in ("current", "quarantined") and not dry and s868_empty != "off":   # S868: an empty report is not kept
            d = os.path.join(STORE, kind)
            os.makedirs(d, mode=0o700, exist_ok=True)
            stored = os.path.join(d, "%s__%s.csv" % (day or "nodate", md5[:10]))
            with open(stored, "wb") as fh:
                fh.write(raw)
            os.chmod(stored, 0o600)
    if not dry:
        _span_cols(con)                                      # S507: the due dates covered, for a follow-up log
        dfrom, dto = followup_span(raw) if kind == "followup" else ("", "")
        if kind == "followup" and dto and day and st == "current" and dto < next_call_day(day):
            note = (note + "; " if note else "") + "covers only %s to %s -- the next call day %s is not in it" % (dfrom, dto, next_call_day(day))
        con.execute("INSERT OR IGNORE INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at, "
                    "due_from, due_to) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (f["id"], f.get("name") or "", f.get("modifiedTime") or "", md5, kind, day, nrows,
                                                                             stored, st, note, now().isoformat(sep=" "), dfrom, dto))
        con.commit()
        if kind == "consultation" and st == "current":       # S868: the not-sitting mark follows the report (fail-soft)
            try:
                if s868_empty == "off":
                    con.execute("CREATE TABLE IF NOT EXISTS clinic_off_day (day TEXT PRIMARY KEY, how TEXT NOT NULL, by TEXT NOT NULL "
                                "DEFAULT '', at TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')")
                    con.execute("INSERT OR IGNORE INTO clinic_off_day (day, how, by, at, note) VALUES (?,?,?,?,?)",
                                (day, "auto", "server", now().isoformat(sep=" ")[:19], "an empty consultation report"))
                elif nrows > 0 and con.execute("SELECT 1 FROM sqlite_master WHERE name='clinic_off_day'").fetchone():
                    con.execute("DELETE FROM clinic_off_day WHERE day=?", (day,))
                con.commit()
            except sqlite3.Error:
                pass
        if kind == "consultation" and st == "current":       # S960 (D1080): the evening check, at once, in its own process
            _s960_evening(con, f)
        if kind == "clinical" and st == "current":           # S779: the diagnoses, at once (fail-soft: never refuses the export)
            try:
                if HERE not in sys.path:
                    sys.path.insert(0, HERE)
                import dx_feed                                # noqa: PLC0415
                dx_feed.run(con)
            except Exception as ex:                          # noqa: BLE001
                note = (note + "; " if note else "") + "diagnosis feed: %s" % str(ex)[:120]
    return kind, day, nrows, st, note


def list_files(fid):
    sys.path.insert(0, HERE)
    import docterz_ingest                                   # noqa: PLC0415 -- its credential, read-only scope
    cred, requests = docterz_ingest._drive()
    out, tok = [], None
    while True:
        p = {"q": "'%s' in parents and trashed=false" % fid, "fields": "nextPageToken, files(id,name,modifiedTime,mimeType,size)",
             "pageSize": 200, "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
        if tok:
            p["pageToken"] = tok
        r = requests.get("https://www.googleapis.com/drive/v3/files", params=p, headers={"Authorization": "Bearer " + cred.token}, timeout=60)
        r.raise_for_status()
        j = r.json()
        out += j.get("files", [])
        tok = j.get("nextPageToken")
        if not tok:
            break
    return out, (lambda fid_: requests.get("https://www.googleapis.com/drive/v3/files/" + fid_, params={"alt": "media"},
                                            headers={"Authorization": "Bearer " + cred.token}, timeout=120))


def run(con, dry=False):
    ensure(con)
    if not dry:
        backfill_spans(con)                                  # S507
    fid = folder_id(con)
    files, get = list_files(fid)
    seen = {(r["drive_id"], r["drive_mtime"]) for r in con.execute("SELECT drive_id, drive_mtime FROM docterz_export")}
    n_new = 0
    for f in sorted(files, key=lambda x: x.get("modifiedTime") or ""):
        if (f["id"], f.get("modifiedTime") or "") in seen or (f.get("mimeType") or "").startswith("application/vnd.google-apps"):
            continue
        r = get(f["id"])
        if r.status_code != 200:
            print("  %s: download refused (%d) -- tried again next pass" % (f["id"][-6:], r.status_code))
            continue
        kind, day, nrows, st, note = take(con, f, r.content, dry)
        n_new += 1
        print("  %s %s %s rows=%d -> %s%s" % (f["id"][-6:], KINDS.get(kind, kind), day or "-", nrows, st.upper() if st == "quarantined" else st,
                                             (" (" + note + ")") if note else ""))
    print("docterz_pickup: %d file(s) in the folder, %d new" % (len(files), n_new))
    return n_new


def last_working_day(today):
    d = today - dt.timedelta(days=1)
    while d.weekday() == 6:                                  # Sunday: the clinic is closed
        d -= dt.timedelta(days=1)
    return d


def owner_lines(con, at=None):
    """The owner's money page: a red line while the last working day's consultation export is missing after 10:00, and a
    red line for a quarantined export of the last three days. [] once it lands -- it heals by itself."""
    at = at or now()
    out = []
    try:
        ensure(con)
        day = last_working_day(at.date()).isoformat()
        if at.time() >= dt.time(*ALARM_HHMM):
            if not con.execute("SELECT 1 FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current'", (day,)).fetchone():
                out.append("No Docterz export for %s has reached the server (by 10:00). Reception exports the two reports from Docterz "
                           "on the reception PC; it is picked up within 15 minutes. If the clinic was closed that day, nothing to do."
                           % dt.date.fromisoformat(day).strftime("%a %d-%b"))
        # S507: the last working day's follow-up log does not reach the next call day
        r = con.execute("SELECT due_from, due_to FROM docterz_export WHERE kind='followup' AND business_date=? AND status='current' "
                        "ORDER BY id DESC LIMIT 1", (day,)).fetchone()
        if r and r[1] and r[1] < next_call_day(day):
            out.append("The Docterz follow-up log of %s reaches only %s, so the next call day (%s) is not in it and that day's call list is "
                       "short. Export the follow-up log again with Docterz's usual one-month range (reception, or this PC); the tracker "
                       "re-runs the day within minutes." % (dt.date.fromisoformat(day).strftime("%a %d-%b"),
                                                            dt.date.fromisoformat(r[1]).strftime("%a %d-%b"),
                                                            dt.date.fromisoformat(next_call_day(day)).strftime("%a %d-%b")))
        since = (at.date() - dt.timedelta(days=3)).isoformat()
        for r in con.execute("SELECT kind, business_date, note FROM docterz_export WHERE status='quarantined' AND substr(taken_at,1,10)>=? "
                             "AND NOT (kind='consultation' AND rows=0 AND note='no date in the file') "            # S868: the old empty ones
                             "AND NOT (kind='consultation' AND rows=0 AND EXISTS (SELECT 1 FROM docterz_export g WHERE g.kind='consultation' "
                             "AND g.business_date=docterz_export.business_date AND g.status='current' AND g.rows>0)) "   # S977 (F-1732)
                             "AND NOT EXISTS (SELECT 1 FROM docterz_export c WHERE c.kind=docterz_export.kind AND c.business_date=docterz_export.business_date "
                             "AND c.status='current' AND c.id>docterz_export.id)", (since,)):
            out.append("A Docterz %s for %s was set aside: %s." % (KINDS.get(r[0], r[0]), r[1] or "?", r[2]))
    except Exception:                                        # noqa: BLE001 -- the page never waits on this
        return []
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    con = sqlite3.connect(a.db, timeout=30)
    con.row_factory = sqlite3.Row
    ensure(con)
    if a.status:
        for r in con.execute("SELECT kind, business_date, rows, status, taken_at FROM docterz_export ORDER BY id DESC LIMIT 12"):
            print("  %-12s %s rows=%-4d %-11s %s" % tuple(r))
        print("owner lines: %s" % (owner_lines(con) or "none"))
        return
    run(con, a.dry_run)


if __name__ == "__main__":
    main()
