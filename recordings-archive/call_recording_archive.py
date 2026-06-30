#!/usr/bin/env python3
"""
call_recording_archive.py — Stage 1 of the Staff Call Audit project.
Dr. Manoj Agarwal Clinic, Bareilly. Session 22 · 30 Jun 2026.

WHAT THIS DOES
  Runs once a day. Pulls EVERY call from one clinic day (both directions, all
  statuses) from MyOperator's Search Logs API. For every CONNECTED call that
  has a recording, downloads it and uploads it to Google Drive in a dated,
  restricted folder, then writes one manifest row to the "Call_Recordings"
  tab of the Clinic Callback Tracker sheet — including a permanent, clickable
  Drive link, so staff/doctor can spot-check ANY call's recording directly
  from the sheet, no other tool needed.

  This is Stage 1 of 4 (recording archive -> transcription -> AI audit
  verdict -> dashboard UI). It runs completely independently of the other
  three stages — nothing here depends on Stage 2/3/4 existing yet.

WHY A NEW TAB, NOT Followup_Outcomes OR Outcomes_Log
  "One writer per table" (Umbrella Architecture, core principle #3). This
  script archives recordings for ALL calls (incoming, outgoing, follow-up,
  ad-hoc) — a broader set than Followup_Outcomes covers — and Outcomes_Log
  isn't receiving any writes yet (it's waiting on Call Console Step 2, the
  dashboard UI). Call_Recordings is therefore a clean new table, owned ONLY
  by this script. When Stage 4 ships, the dashboard's Audit & Reporting
  section reads this tab and joins it to outcome data by the SAME key
  already used elsewhere in the codebase: phone10 + "_" + start_unix
  (see CallConsole.gs's `id` field — same pattern, deliberately).

FAILURE MAP (per D19 — for the future Diagnostics.gs to consume)
  - MYOP_LOGS_TOKEN / GOOGLE_SA_KEY / DRIVE_RECORDINGS_FOLDER_ID missing
        -> exits 2 before touching anything. Safe to re-run once fixed.
  - MyOperator /search HTTP error
        -> logs + exits 3. Nothing was archived this run. Recordings remain
           on MyOperator's cloud indefinitely (no retention urgency) — a
           later manual re-run catches up fully; nothing is lost.
  - /recordings/link or the download fails for ONE call
        -> logs + SKIPS that call only; the rest of the run continues.
  - Drive upload fails for ONE call
        -> logs + skips that call; the rest continues. If EVERY upload in
           the run fails, check first that DRIVE_TOKEN_FILE points to a
           valid, current token (re-run get_drive_token.py on the owner's
           PC if it's missing or was revoked) — that is overwhelmingly the
           likely cause now that uploads run as the owner's own account.
  - Sheet unreachable
        -> exits 5. Manifest rows are written ONE AT A TIME, right after
           each successful upload (never batched at the end) — so a sheet
           outage only loses the manifest ROW for calls not yet written.
           Recordings already uploaded to Drive are NOT lost; the dedupe
           check (existing join keys already in Call_Recordings) makes a
           later re-run safe — it will just pick up where this run left off
           on the SHEET side (it may re-upload a duplicate Drive file for
           any call whose manifest row never got written; harmless, just
           a duplicate audio file, not a duplicate outcome record).
  KEEP WORKING: this script's success or failure on any given day never
  risks the underlying recordings — they persist on MyOperator's cloud
  regardless. A failed run is a delay, not a data-loss event.

CONFIG (environment variables — read from /root/wa/.env, same convention
as every other script in this repo)
  MYOP_LOGS_TOKEN              (required) Calling/Logs API token (3f76...).
                                Already present in .env — reused, not new.
  GOOGLE_SA_KEY                (required) path to the service-account JSON
                                key. Falls back to WA_SA_KEY if not set —
                                the SAME key already used for Sheets/WA.
                                Used ONLY for the Sheets manifest now —
                                service accounts have NO Drive storage
                                quota of their own (a 2025 Google policy
                                change), so Drive uploads use a different
                                credential, below.
  DRIVE_TOKEN_FILE              (required, NEW) path to drive_token.json —
                                produced once by running get_drive_token.py
                                on the owner's own PC (a one-time browser
                                sign-in as drmka.ortho@gmail.com). This is
                                what actually uploads recordings, so each
                                file is owned by the clinic's own Drive
                                account (real quota) instead of the
                                service account (zero quota, blocked).
  SHEET_ID                     (optional) Clinic Callback Tracker id.
                                Falls back to the known clinic sheet id.
  DRIVE_RECORDINGS_FOLDER_ID   (required) Drive folder id. Sharing it with
                                the service account is no longer load-
                                bearing for uploads (the owner's own OAuth
                                identity already owns everything in their
                                own Drive) — leaving the existing share in
                                place is harmless, just unused for this.

RUN
  One-time, on the owner's PC only (not here): get_drive_token.py — see
  its own docstring. Produces drive_token.json, which then gets uploaded
  to the VPS alongside this script.

  Manual test, any past date, writes/uploads nothing:
    /root/wa/venv/bin/python3 call_recording_archive.py --date 2026-06-29 --dry-run
  Manual real run, small scale first:
    /root/wa/venv/bin/python3 call_recording_archive.py --date 2026-06-29 --limit 2
  Production (systemd timer, daily): defaults to "yesterday" in Asia/Kolkata
    /root/wa/venv/bin/python3 call_recording_archive.py

DEPENDENCIES (new on top of what's already installed in the venv)
  /root/wa/venv/bin/pip install google-api-python-client
  (gspread + google-auth already cover the Sheets side; this adds Drive.
  google-auth-oauthlib is NOT needed here on the VPS — that's only for
  get_drive_token.py, which runs on the owner's PC, not the server.)

PRIVACY
  No patient names or full numbers are ever printed. Log lines carry only
  join keys (phone10_starttime — already only useful inside this system)
  and counts. The .env loader never echoes values.
"""

import argparse
import datetime
import io
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MYOP_HOST = "https://developers.myoperator.co"
SEARCH_PATH = "/search"
RECORDING_LINK_PATH = "/recordings/link"

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DEFAULT_SHEET_ID = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"

RECORD_TAB = "Call_Recordings"
RECORD_HEADER = [
    "Date", "Time", "Direction", "Number (last-4)", "Agent",
    "Patient Name", "Clinic ID", "Duration", "Join Key",
    "MyOperator Filename", "Drive File ID", "Drive Link",
]

PAGE_SIZE = 100
MAX_PAGES = 50


# ---------------------------------------------------------------------------
# .env loader — same pattern as wa_receiver.py / get_users.py / call_api.py
# ---------------------------------------------------------------------------
def _load_env(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


def _log(*parts):
    print("[call_recording_archive]", *parts, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Small utilities (mirrors the style already used in CallConsole.gs)
# ---------------------------------------------------------------------------
def last10(v):
    digits = "".join(ch for ch in str(v or "") if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits


def last4(v):
    digits = "".join(ch for ch in str(v or "") if ch.isdigit())
    return digits[-4:] if digits else ""


def hhmmss_to_sec(s):
    try:
        parts = [int(p) for p in str(s).split(":")]
        while len(parts) < 3:
            parts.insert(0, 0)
        h, m, sec = parts[-3:]
        return h * 3600 + m * 60 + sec
    except (ValueError, TypeError):
        return 0


def mmss(sec):
    sec = int(sec or 0)
    m, s = divmod(sec, 60)
    return "%d:%02d" % (m, s)


def day_bounds_ist(date_str=None):
    """Returns (start_dt, end_dt, date_obj) for one IST calendar day."""
    if date_str:
        d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        d = (datetime.datetime.now(IST) - datetime.timedelta(days=1)).date()
    start = datetime.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=IST)
    end = start + datetime.timedelta(days=1)
    return start, end, d


# ---------------------------------------------------------------------------
# MyOperator API (System A — Call/Logs + Recordings, per the Master Reference)
# ---------------------------------------------------------------------------
def myop_search(token, from_unix, to_unix, log_from=0, page_size=PAGE_SIZE):
    url = MYOP_HOST + SEARCH_PATH
    body = {
        "token": token,
        "from": str(from_unix),
        "to": str(to_unix),
        "log_from": str(log_from),
        "page_size": str(page_size),
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", "replace")
    return json.loads(raw)


def fetch_all_calls(token, from_unix, to_unix):
    all_hits = []
    log_from = 0
    for _ in range(MAX_PAGES):
        data = myop_search(token, from_unix, to_unix, log_from, PAGE_SIZE)
        hits = (((data or {}).get("data") or {}).get("hits")) or []
        all_hits.extend(hits)
        if len(hits) < PAGE_SIZE:
            break
        log_from += PAGE_SIZE
    return all_hits


def enrich(hit):
    s = (hit or {}).get("_source") or {}
    phone_raw = s.get("caller_number_raw") or s.get("caller_number") or ""
    start_unix = int(s.get("start_time") or 0)
    direction = "outgoing" if str(s.get("event")) == "2" else "incoming"
    agent_name = ""
    log_details = s.get("log_details") or []
    if log_details:
        rb = (log_details[0] or {}).get("received_by") or []
        if rb:
            agent_name = (rb[0] or {}).get("name") or ""
    return {
        "phone10": last10(phone_raw),
        "start_unix": start_unix,
        "direction": direction,
        "is_connected": str(s.get("status")) == "1",
        "filename": s.get("filename") or "",
        "duration_sec": hhmmss_to_sec(s.get("duration") or "00:00:00"),
        "agent_name": agent_name,
    }


def get_recording_link(token, filename):
    url = "%s%s?token=%s&file=%s" % (
        MYOP_HOST, RECORDING_LINK_PATH,
        urllib.parse.quote(token, safe=""),
        urllib.parse.quote(filename, safe=""),
    )
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", "replace")
    data = json.loads(raw)
    # Tolerant of the exact response shape — confirm the real key on first
    # live run and tighten this if needed.
    link = (
        data.get("link")
        or data.get("url")
        or (data.get("data") or {}).get("link")
        or (data.get("data") or {}).get("url")
    )
    if not link:
        raise RuntimeError("no recognisable link field in response: %s" % json.dumps(data)[:200])
    return link


def download_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "clinic-archiver/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


# ---------------------------------------------------------------------------
# Google Drive
# ---------------------------------------------------------------------------
def get_or_create_month_folder(drive, parent_id, year_month, cache):
    if year_month in cache:
        return cache[year_month]
    q = (
        "'%s' in parents and name = '%s' and "
        "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    ) % (parent_id, year_month)
    res = drive.files().list(q=q, fields="files(id, name)").execute()
    files = res.get("files") or []
    if files:
        folder_id = files[0]["id"]
    else:
        meta = {
            "name": year_month,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        created = drive.files().create(body=meta, fields="id").execute()
        folder_id = created["id"]
    cache[year_month] = folder_id
    return folder_id


def upload_recording(drive, folder_id, filename, audio_bytes):
    media = MediaIoBaseUpload(io.BytesIO(audio_bytes), mimetype="audio/mpeg", resumable=False)
    meta = {"name": filename, "parents": [folder_id]}
    created = drive.files().create(
        body=meta, media_body=media, fields="id, webViewLink"
    ).execute()
    return created["id"], created.get("webViewLink")


def build_drive_credentials(token_path):
    """
    Loads the owner's own OAuth credentials (produced once by
    get_drive_token.py on their PC) so Drive uploads count against the
    owner's real storage quota, not the service account's (which has
    none — see the module docstring). google-auth refreshes the access
    token automatically using the stored refresh_token; nothing here
    needs to write the file back after a refresh.
    """
    scopes = ["https://www.googleapis.com/auth/drive"]
    return UserCredentials.from_authorized_user_file(token_path, scopes=scopes)


# ---------------------------------------------------------------------------
# Google Sheets — the manifest tab + best-effort patient lookup
# ---------------------------------------------------------------------------
def open_sheet(sa_key_path, sheet_id):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    creds = Credentials.from_service_account_file(sa_key_path, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_key(sheet_id), creds


def ensure_record_tab(ss):
    try:
        sh = ss.worksheet(RECORD_TAB)
    except gspread.WorksheetNotFound:
        sh = ss.add_worksheet(title=RECORD_TAB, rows=200, cols=len(RECORD_HEADER))
        sh.append_row(RECORD_HEADER)
        return sh, set()

    values = sh.get_all_values()
    if not values:
        sh.append_row(RECORD_HEADER)
        return sh, set()

    header = values[0]
    try:
        key_col = header.index("Join Key")
    except ValueError:
        key_col = 8  # positional fallback matching RECORD_HEADER
    existing = set(row[key_col] for row in values[1:] if len(row) > key_col)
    return sh, existing


def patient_map(ss):
    """Best-effort phone10 -> {name, clinicId}. Never raises; returns {} on any problem."""
    m = {}
    try:
        sh = ss.worksheet("Patient_Master")
        values = sh.get_all_values()
        if len(values) < 2:
            return m
        header = [h.strip().lower() for h in values[0]]

        def col(cands):
            for c in cands:
                for i, h in enumerate(header):
                    if c in h:
                        return i
            return -1

        i_phone = col(["mobile", "phone"])
        i_name = col(["patient name", "name"])
        i_id = col(["clinic id", "clinic_id", "uid", "patient id"])
        if i_phone < 0:
            return m
        for row in values[1:]:
            ph = last10(row[i_phone]) if i_phone < len(row) else ""
            if not ph or ph in m:
                continue
            m[ph] = {
                "name": row[i_name].strip() if 0 <= i_name < len(row) else "",
                "clinicId": row[i_id].strip() if 0 <= i_id < len(row) else "",
            }
    except Exception as e:  # noqa: BLE001 — best-effort, never fatal
        _log("patient-map-warning", repr(e))
    return m


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD (IST clinic day). Defaults to yesterday.")
    parser.add_argument("--dry-run", action="store_true",
                         help="List what would be archived; uploads/writes nothing.")
    parser.add_argument("--limit", type=int, default=0,
                         help="Process at most N connected calls this run (0 = no limit). "
                              "Useful for a small first real test before a full-day run.")
    args = parser.parse_args()

    _load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    _load_env("/root/wa/.env")  # the real production location

    token = os.environ.get("MYOP_LOGS_TOKEN", "").strip()
    sa_key = os.environ.get("GOOGLE_SA_KEY", "").strip() or os.environ.get("WA_SA_KEY", "").strip()
    sheet_id = os.environ.get("SHEET_ID", "").strip() or DEFAULT_SHEET_ID
    drive_folder_id = os.environ.get("DRIVE_RECORDINGS_FOLDER_ID", "").strip()
    drive_token_path = os.environ.get("DRIVE_TOKEN_FILE", "").strip()

    if not token:
        _log("FATAL: MYOP_LOGS_TOKEN missing from environment/.env")
        sys.exit(2)
    if not sa_key:
        _log("FATAL: GOOGLE_SA_KEY (or WA_SA_KEY) missing from environment/.env")
        sys.exit(2)
    if not drive_folder_id:
        _log("FATAL: DRIVE_RECORDINGS_FOLDER_ID missing — create the Drive "
             "folder, then set this.")
        sys.exit(2)
    if not args.dry_run and not drive_token_path:
        _log("FATAL: DRIVE_TOKEN_FILE missing from environment/.env — run "
             "get_drive_token.py on the owner's PC first, upload the result, "
             "then set this to its path on the VPS.")
        sys.exit(2)
    if not args.dry_run and not os.path.exists(drive_token_path):
        _log("FATAL: DRIVE_TOKEN_FILE points to a path that doesn't exist:", drive_token_path)
        sys.exit(2)

    start, end, day = day_bounds_ist(args.date)
    from_unix = int(start.timestamp())
    to_unix = int(end.timestamp()) - 1

    _log("run-start", "date=%s" % day, "dry_run=%s" % args.dry_run)

    try:
        ss, creds = open_sheet(sa_key, sheet_id)
    except Exception as e:  # noqa: BLE001
        _log("FATAL sheet-open:", repr(e))
        sys.exit(5)

    sh, existing_keys = ensure_record_tab(ss)
    pmap = patient_map(ss)

    try:
        hits = fetch_all_calls(token, from_unix, to_unix)
    except Exception as e:  # noqa: BLE001
        _log("FATAL search:", repr(e))
        sys.exit(3)

    _log("calls-found", str(len(hits)))

    connected = [enrich(h) for h in hits]
    connected = [c for c in connected if c["is_connected"] and c["filename"]]
    _log("connected-with-recording", str(len(connected)))

    if args.limit and args.limit > 0 and len(connected) > args.limit:
        _log("limit-applied", "processing first %d of %d connected calls" % (args.limit, len(connected)))
        connected = connected[: args.limit]

    drive = None
    if not args.dry_run:
        drive_creds = build_drive_credentials(drive_token_path)
        drive = build("drive", "v3", credentials=drive_creds)

    month_folder_cache = {}
    archived = 0
    skipped_existing = 0
    failed = 0

    for c in connected:
        join_key = "%s_%s" % (c["phone10"], c["start_unix"])
        if join_key in existing_keys:
            skipped_existing += 1
            continue

        when = datetime.datetime.fromtimestamp(c["start_unix"], tz=IST)
        date_str = when.strftime("%Y-%m-%d")
        time_str = when.strftime("%H:%M")
        ym = when.strftime("%Y-%m")
        pinfo = pmap.get(c["phone10"]) or {}

        if args.dry_run:
            _log("would-archive", join_key, c["direction"], "agent=%s" % (c["agent_name"] or "?"))
            archived += 1
            continue

        try:
            link = get_recording_link(token, c["filename"])
            audio = download_bytes(link)
            folder_id = get_or_create_month_folder(drive, drive_folder_id, ym, month_folder_cache)
            drive_name = "%s_%s_%s.mp3" % (date_str, time_str.replace(":", ""), c["filename"])
            file_id, web_link = upload_recording(drive, folder_id, drive_name, audio)
        except Exception as e:  # noqa: BLE001 — one call's failure must not stop the run
            _log("skip-failed", join_key, repr(e))
            failed += 1
            continue

        row = [
            date_str, time_str, c["direction"], last4(c["phone10"]),
            c["agent_name"], pinfo.get("name", ""), pinfo.get("clinicId", ""),
            mmss(c["duration_sec"]), join_key, c["filename"], file_id,
            web_link or ("https://drive.google.com/file/d/%s/view" % file_id),
        ]
        try:
            sh.append_row(row)
        except Exception as e:  # noqa: BLE001
            _log("sheet-write-failed-after-upload", join_key, repr(e),
                 "(recording IS on Drive; will be retried next run, may duplicate the file)")
            failed += 1
            continue

        existing_keys.add(join_key)
        archived += 1

    _log(
        "run-done",
        "archived=%s" % archived,
        "skipped_existing=%s" % skipped_existing,
        "failed=%s" % failed,
        "total_connected=%s" % len(connected),
    )


if __name__ == "__main__":
    main()
