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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER_DEFAULT = "1JjWcfk_7IzSBQUbLlbNWPvf96LGcjjDt"     # Clinic Records / Docterz exports (drmka.ortho), 01-Oct-2026
STORE = os.environ.get("DOCTERZ_EXPORT_STORE", os.path.join(HERE, "docterz_exports"))
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
ALARM_HHMM = (10, 0)
KINDS = {"consultation": "consultation report", "followup": "follow-up log"}

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


def take(con, f, raw, dry=False):
    """One file: identify, store, and replace the day only when it should. Returns the status written."""
    md5 = hashlib.md5(raw).hexdigest()
    kind, day, nrows, note = identify(raw)
    st, stored = kind if kind == "unknown" else "current", ""
    if kind != "unknown":
        if not day:
            st, note = "quarantined", "no date in the file"
        else:
            cur = con.execute("SELECT * FROM docterz_export WHERE kind=? AND business_date=? AND status='current'", (kind, day)).fetchone()
            if cur is not None and cur["md5"] == md5:
                st, note = "duplicate", "same bytes as export #%d" % cur["id"]
            elif cur is not None and (f["modifiedTime"] or "") < (cur["drive_mtime"] or ""):
                st, note = "superseded", "older than export #%d" % cur["id"]
            elif cur is not None and nrows < cur["rows"]:
                st, note = "quarantined", "FEWER ROWS (%d) than export #%d (%d) -- not taken; check the export" % (nrows, cur["id"], cur["rows"])
            elif cur is not None and not dry:
                con.execute("UPDATE docterz_export SET status='superseded', note=? WHERE id=?", ("replaced by a newer export", cur["id"]))
        if st in ("current", "quarantined") and not dry:
            d = os.path.join(STORE, kind)
            os.makedirs(d, mode=0o700, exist_ok=True)
            stored = os.path.join(d, "%s__%s.csv" % (day or "nodate", md5[:10]))
            with open(stored, "wb") as fh:
                fh.write(raw)
            os.chmod(stored, 0o600)
    if not dry:
        con.execute("INSERT OR IGNORE INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (f["id"], f.get("name") or "", f.get("modifiedTime") or "", md5, kind, day, nrows, stored, st, note,
                                                       now().isoformat(sep=" ")))
        con.commit()
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
        since = (at.date() - dt.timedelta(days=3)).isoformat()
        for r in con.execute("SELECT kind, business_date, note FROM docterz_export WHERE status='quarantined' AND substr(taken_at,1,10)>=? "
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
