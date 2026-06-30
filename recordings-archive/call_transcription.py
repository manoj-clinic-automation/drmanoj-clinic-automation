#!/usr/bin/env python3
"""
call_transcription.py — Stage 2 of the Staff Call Audit project.
Dr. Manoj Agarwal Clinic, Bareilly. Session 23.

WHAT THIS DOES
  Runs once a day, just after Stage 1 (call_recording_archive.py). Reads the
  "Call_Recordings" tab of the Clinic Callback Tracker sheet, finds rows that
  don't yet have a DONE transcript, downloads each call's audio straight from
  the Drive archive Stage 1 already built (no MyOperator re-pull, no 24-hour
  link-expiry risk), sends it to Sarvam (Saaras v3) for transcription, uploads
  the resulting transcript text file to a restricted Drive folder, and writes
  one manifest row to a NEW "Call_Transcripts" tab.

  This is Stage 2 of 4 (recording archive -> transcription -> AI audit
  verdict -> dashboard UI). Per D35, it runs on ALL calls (both directions),
  not flagged-only, for the project's first ~month.

  The transcription logic itself (sync for short calls, Sarvam's batch job
  API for long calls, resumable) is adapted from the kit built and tested
  10–12 days before this session — same model, same settings, same proven
  call shape. What's new here: pulling audio from Drive instead of a local
  folder, and writing results to a new Sheet tab + Drive folder instead of
  local files, so it can run unattended on the VPS.

WHY A NEW TAB, NOT A COLUMN ON Call_Recordings
  "One writer per table" (Umbrella Architecture, core principle #3; D37).
  Call_Recordings is owned solely by call_recording_archive.py. This script
  owns Call_Transcripts exclusively. Join by the same key both tables already
  share: phone10 + "_" + start_unix (CallConsole.gs's `id` field, reused
  throughout this codebase).

WHY TRANSCRIPTS GO TO DRIVE, NOT INTO A SHEET CELL
  Raw transcript text is PHI (patient symptoms, sometimes names not fully
  caught by de-identification — de-identification is a LATER, separate step,
  not run here). A spreadsheet cell is visible to every sheet collaborator
  and isn't built for paragraphs of text. Drive, with the same restricted-
  folder model Stage 1 already uses for audio, is the right home. The sheet
  row holds only metadata + a clickable link — never the transcript body.

FAILURE MAP (per D19 — for the future Diagnostics.gs to consume)
  - SARVAM_API_KEY / GOOGLE_SA_KEY / DRIVE_TOKEN_FILE / DRIVE_RECORDINGS_FOLDER_ID
    missing -> exits 2 before touching anything. Safe to re-run once fixed.
  - Call_Recordings unreachable/empty -> exits 5. Nothing processed.
  - Drive download fails for ONE call -> logs, writes a FAILED row for that
    call (so it's retried next run), continues with the rest.
  - Sarvam transcription fails for ONE call -> same: FAILED row, continue.
  - Drive upload of the transcript fails for ONE call -> same: FAILED row
    (the transcript text is not durably saved anywhere if this happens, so a
    retry re-transcribes — Sarvam cost is trivial, ~₹0.50/min, not worth the
    complexity of a local cache for this).
  - Sheet unreachable mid-run -> exits 5. Rows already written are NOT lost
    (written one at a time, immediately after each successful upload — same
    pattern as Stage 1). A later re-run picks up exactly where this left off,
    via the dedupe-by-join-key check below.
  RESUMABILITY: a call counts as "already done" only if its Call_Transcripts
  row has Status=done. FAILED rows are retried automatically on the next run
  — there is no separate retry command.

CONFIG (environment variables — read from /root/wa/.env, same convention and
same loader pattern as call_recording_archive.py / wa_receiver.py)
  SARVAM_API_KEY               (required, NEW) Sarvam dashboard API key.
                                Confirm this is actually present in .env
                                before installing — it was anticipated in
                                the secrets list but may not be added yet.
  GOOGLE_SA_KEY                (required) same service-account JSON path
                                Stage 1 uses. Falls back to WA_SA_KEY.
                                Used for Sheets only (Call_Transcripts tab).
  DRIVE_TOKEN_FILE             (required) same drive_token.json Stage 1
                                uses (owner-OAuth identity — service accounts
                                have zero Drive storage quota, D36). Used to
                                both DOWNLOAD recording audio and UPLOAD
                                transcript files.
  DRIVE_RECORDINGS_FOLDER_ID   (required) same folder id Stage 1 uses. Reused
                                here ONLY as the parent under which a sibling
                                "Call Transcripts" folder is found-or-created
                                on first run — no new folder id needed from
                                the owner.
  SHEET_ID                     (optional) Clinic Callback Tracker id. Falls
                                back to the known clinic sheet id.

RUN
  Manual test, any past date, writes/uploads nothing:
    /root/wa/venv/bin/python3 call_transcription.py --date 2026-06-29 --dry-run
  Manual real run, small scale first:
    /root/wa/venv/bin/python3 call_transcription.py --limit 2
  Production (systemd timer, daily, just after Stage 1's 02:00 run):
    /root/wa/venv/bin/python3 call_transcription.py

DEPENDENCIES (new on top of what Stage 1 already added)
  /root/wa/venv/bin/pip install sarvamai
  (gspread, google-auth, google-api-python-client already present from
  Stage 1. `requests` already present clinic-wide.)

PRIVACY
  No patient names or full numbers are ever printed. Log lines carry only
  join keys and counts. Raw transcript text never appears in a log line, a
  sheet cell, or this script's own stdout — only inside the Drive file
  itself, in the restricted folder. The .env loader never echoes values.
"""

import argparse
import datetime
import glob
import io
import json
import os
import sys
import tempfile
import time

import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

try:
    from sarvamai import SarvamAI
except ImportError:
    sys.exit("ERROR: sarvamai package not installed. Run: "
             "/root/wa/venv/bin/pip install sarvamai")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ENV_PATH = "/root/wa/.env"

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DEFAULT_SHEET_ID = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"

RECORD_TAB = "Call_Recordings"
TRANSCRIPT_TAB = "Call_Transcripts"
TRANSCRIPT_HEADER = [
    "Date", "Time", "Direction", "Number (last-4)", "Duration",
    "Join Key", "Status", "Language", "Transcript Drive File ID",
    "Transcript Drive Link", "Transcribed At", "Error",
]

TRANSCRIPTS_FOLDER_NAME = "Call Transcripts"   # sibling folder, same parent as recordings

SARVAM_MODEL = "saaras:v3"
SARVAM_MODE = "transcribe"        # keep original Hindi/Hinglish, do not translate
SARVAM_LANGUAGE = "unknown"       # auto-detect
SHORT_CALL_THRESHOLD_S = 30       # <=30s -> sync; >30s -> batch job API
BATCH_CHUNK = 20                  # files per Sarvam batch job
DURATION_HINT = "30 second"       # marker in Sarvam's "too long" error message (fallback safety net)

CODEC_MAP = {".mp3": "mp3", ".wav": "wav", ".m4a": "x-m4a", ".mpeg": "mpeg",
             ".ogg": "ogg", ".flac": "flac", ".aac": "aac"}


# ---------------------------------------------------------------------------
# .env loader — same pattern as call_recording_archive.py / wa_receiver.py
# ---------------------------------------------------------------------------
def load_env():
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


def require_env(name, alt=None):
    val = os.environ.get(name) or (os.environ.get(alt) if alt else None)
    if not val:
        names = name if not alt else f"{name} (or {alt})"
        sys.exit(f"ERROR: required env var {names} not set in {ENV_PATH}. Exiting (code 2).")
    return val


def mask(num):
    d = "".join(ch for ch in str(num or "") if ch.isdigit())
    return ("*" * max(0, len(d) - 4)) + d[-4:] if d else "(none)"


def parse_duration_to_seconds(s):
    """'0:52' -> 52, '1:13' -> 73, '1:02:08' -> 3728. Defensive: bad input -> None."""
    if not s:
        return None
    parts = str(s).strip().split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return None
    secs = 0
    for p in parts:
        secs = secs * 60 + p
    return secs


# ---------------------------------------------------------------------------
# Google clients
# ---------------------------------------------------------------------------
def get_sheets_client():
    sa_path = require_env("GOOGLE_SA_KEY", "WA_SA_KEY")
    creds = Credentials.from_service_account_file(
        sa_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds)


def get_drive_service():
    token_path = require_env("DRIVE_TOKEN_FILE")
    if not os.path.exists(token_path):
        sys.exit(f"ERROR: DRIVE_TOKEN_FILE not found at {token_path}. "
                 f"Re-run get_drive_token.py on the owner's PC if missing/revoked. Exiting (code 2).")
    creds = UserCredentials.from_authorized_user_file(token_path)
    return build("drive", "v3", credentials=creds)


def find_or_create_subfolder(drive_service, parent_id, name):
    """Idempotent: returns the folder id, creating it only if it doesn't already exist."""
    q = (f"'{parent_id}' in parents and name='{name}' "
         f"and mimeType='application/vnd.google-apps.folder' and trashed=false")
    resp = drive_service.files().list(q=q, fields="files(id, name)", pageSize=1).execute()
    hits = resp.get("files", [])
    if hits:
        return hits[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    created = drive_service.files().create(body=body, fields="id").execute()
    print(f"  (created Drive folder '{name}')", flush=True)
    return created["id"]


def download_drive_file(drive_service, file_id, dest_path):
    request = drive_service.files().get_media(fileId=file_id)
    with io.FileIO(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def upload_transcript_text(drive_service, parent_id, filename, text):
    buf = io.BytesIO((text or "").encode("utf-8"))
    media = MediaIoBaseUpload(buf, mimetype="text/plain", resumable=False)
    body = {"name": filename, "parents": [parent_id]}
    f = drive_service.files().create(body=body, media_body=media, fields="id, webViewLink").execute()
    return f["id"], f.get("webViewLink", "")


# ---------------------------------------------------------------------------
# Sheet read/write
# ---------------------------------------------------------------------------
def ensure_transcript_tab(spreadsheet):
    try:
        ws = spreadsheet.worksheet(TRANSCRIPT_TAB)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=TRANSCRIPT_TAB, rows=1000, cols=len(TRANSCRIPT_HEADER))
        ws.append_row(TRANSCRIPT_HEADER, value_input_option="RAW")
        print(f"  (created sheet tab '{TRANSCRIPT_TAB}')", flush=True)
    return ws


def load_done_keys(ws_transcripts):
    """Join keys that already have a DONE row — these are skipped. FAILED rows are retried."""
    rows = ws_transcripts.get_all_records()
    return {r.get("Join Key") for r in rows if r.get("Status") == "done"}


def load_pending_recordings(ws_records, date_filter=None):
    rows = ws_records.get_all_records()
    if date_filter:
        rows = [r for r in rows if r.get("Date") == date_filter]
    # only rows that actually have a Drive File ID (i.e. successfully archived)
    return [r for r in rows if r.get("Drive File ID") and r.get("Join Key")]


def append_transcript_row(ws_transcripts, rec, status, lang="", file_id="", link="", error=""):
    row = [
        rec.get("Date", ""), rec.get("Time", ""), rec.get("Direction", ""),
        rec.get("Number (last-4)", ""), rec.get("Duration", ""),
        rec.get("Join Key", ""), status, lang, file_id, link,
        datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        (error or "")[:200],
    ]
    ws_transcripts.append_row(row, value_input_option="USER_ENTERED")


# ---------------------------------------------------------------------------
# Sarvam transcription
# ---------------------------------------------------------------------------
def transcribe_sync(sarvam_client, local_path, ext):
    with open(local_path, "rb") as af:
        resp = sarvam_client.speech_to_text.transcribe(
            file=af,
            model=SARVAM_MODEL,
            mode=SARVAM_MODE,
            language_code=SARVAM_LANGUAGE,
            input_audio_codec=CODEC_MAP.get(ext, "mp3"),
        )
    return resp.transcript, getattr(resp, "language_code", "")


def extract_transcript(obj):
    """Defensively pull the transcript string out of a batch output JSON."""
    if isinstance(obj, dict):
        if isinstance(obj.get("transcript"), str):
            return obj["transcript"], obj.get("language_code", "")
        for v in obj.values():
            t, l = extract_transcript(v)
            if t:
                return t, l
    elif isinstance(obj, list):
        for v in obj:
            t, l = extract_transcript(v)
            if t:
                return t, l
    return "", ""


def transcribe_batch(sarvam_client, local_paths_by_key):
    """local_paths_by_key: {join_key: local_temp_path}. Returns {join_key: (text, lang) or None}."""
    results = {}
    items = list(local_paths_by_key.items())
    for i in range(0, len(items), BATCH_CHUNK):
        chunk = items[i:i + BATCH_CHUNK]
        print(f"  batch job for {len(chunk)} long call(s) ...", flush=True)
        try:
            job = sarvam_client.speech_to_text_job.create_job(
                model=SARVAM_MODEL, mode=SARVAM_MODE, language_code=SARVAM_LANGUAGE,
            )
            job.upload_files([p for _, p in chunk])
            job.start()
            job.wait_until_complete()
            if not job.is_successful() and not job.get_output_mappings():
                print("    batch job did not complete successfully.", flush=True)
                for key, _ in chunk:
                    results[key] = None
                continue

            tmp = tempfile.mkdtemp(prefix="sarvam_batch_")
            job.download_outputs(tmp)
            mappings = job.get_output_mappings()
            # Sarvam reports input_file as a bare filename (no path), matching what we
            # uploaded — so the lookup key must be basenames, not full local paths.
            path_to_key = {os.path.basename(p): key for key, p in chunk}

            if not mappings:
                print("    batch job completed but returned no output mappings.", flush=True)

            matched = 0
            for m in mappings:
                in_name = os.path.basename(m["input_file"])
                key = path_to_key.get(in_name)
                cand = os.path.join(tmp, in_name + ".json")
                if not os.path.exists(cand):
                    alt = os.path.join(tmp, os.path.basename(m["output_file"]))
                    if os.path.exists(alt):
                        cand = alt
                    else:
                        hits = glob.glob(os.path.join(tmp, "**", "*" + in_name + "*"), recursive=True)
                        cand = hits[0] if hits else None
                if not key:
                    print(f"    batch output didn't match any queued call (filename mismatch)", flush=True)
                    continue
                if not cand:
                    print(f"    no output file found for a matched call", flush=True)
                    results[key] = None
                    continue
                with open(cand, encoding="utf-8") as jf:
                    data = json.load(jf)
                text, lang = extract_transcript(data)
                results[key] = (text, lang)
                matched += 1
            print(f"    matched {matched}/{len(chunk)} batch output(s)", flush=True)

            for key, _ in chunk:
                results.setdefault(key, None)
        except Exception as e:                                    # noqa: BLE001
            print(f"    batch error: {e}", flush=True)
            for key, _ in chunk:
                results.setdefault(key, None)
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Stage 2: Sarvam transcription of archived call recordings.")
    ap.add_argument("--date", help="only process Call_Recordings rows for this Date (YYYY-MM-DD)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N calls processed (0 = no cap)")
    ap.add_argument("--dry-run", action="store_true", help="list what would be processed; do nothing")
    args = ap.parse_args()

    load_env()
    sarvam_key = require_env("SARVAM_API_KEY")
    require_env("GOOGLE_SA_KEY", "WA_SA_KEY")
    require_env("DRIVE_TOKEN_FILE")
    drive_recordings_folder_id = require_env("DRIVE_RECORDINGS_FOLDER_ID")
    sheet_id = os.environ.get("SHEET_ID", DEFAULT_SHEET_ID)

    print("Connecting to Sheets + Drive + Sarvam ...", flush=True)
    gc = get_sheets_client()
    try:
        sh = gc.open_by_key(sheet_id)
        ws_records = sh.worksheet(RECORD_TAB)
        ws_transcripts = ensure_transcript_tab(sh)
    except Exception as e:                                        # noqa: BLE001
        sys.exit(f"ERROR: could not open sheet/tabs ({e}). Exiting (code 5).")

    drive_service = get_drive_service()
    sarvam_client = SarvamAI(api_subscription_key=sarvam_key)

    pending = load_pending_recordings(ws_records, date_filter=args.date)
    done_keys = load_done_keys(ws_transcripts)
    todo = [r for r in pending if r.get("Join Key") not in done_keys]
    if args.limit:
        todo = todo[: args.limit]

    print(f"Call_Recordings rows: {len(pending)} eligible, "
          f"{len(done_keys)} already done, {len(todo)} to process this run.", flush=True)

    if args.dry_run:
        print("\n[dry-run] would process:")
        for r in todo:
            print(f"    {mask(r.get('Number (last-4)'))}  {r.get('Date')} {r.get('Time')}  "
                  f"dur={r.get('Duration')}  key={r.get('Join Key')}")
        print(f"\n[dry-run] {len(todo)} call(s) eligible. Nothing downloaded, transcribed, or uploaded.")
        return

    if not todo:
        print("Nothing to do.")
        return

    transcripts_folder_id = find_or_create_subfolder(
        drive_service, drive_recordings_folder_id, TRANSCRIPTS_FOLDER_NAME)

    done = failed = 0
    long_calls = []  # (record, local_temp_path) for batch pass

    tmpdir = tempfile.mkdtemp(prefix="call_transcribe_")
    try:
        # ---- PASS 1: download everything; transcribe SHORT calls synchronously ----
        for i, rec in enumerate(todo, 1):
            key = rec.get("Join Key")
            num_masked = mask(rec.get("Number (last-4)"))
            print(f"[{i}/{len(todo)}] {num_masked}  {rec.get('Date')} {rec.get('Time')}  key={key}", flush=True)

            ext = os.path.splitext(rec.get("MyOperator Filename", ""))[1].lower() or ".mp3"
            local_path = os.path.join(tmpdir, f"{key}{ext}")
            try:
                download_drive_file(drive_service, rec["Drive File ID"], local_path)
            except Exception as e:                                # noqa: BLE001
                print(f"    FAILED (Drive download): {str(e)[:160]}", flush=True)
                append_transcript_row(ws_transcripts, rec, "failed", error=f"download: {e}")
                failed += 1
                continue

            secs = parse_duration_to_seconds(rec.get("Duration"))
            if secs is not None and secs > SHORT_CALL_THRESHOLD_S:
                long_calls.append((rec, local_path))
                print("    >30s, queued for batch", flush=True)
                continue

            try:
                text, lang = transcribe_sync(sarvam_client, local_path, ext)
            except Exception as e:                                # noqa: BLE001
                if DURATION_HINT in str(e):       # safety net: duration field lied, route to batch
                    long_calls.append((rec, local_path))
                    print("    >30s (caught at call time), queued for batch", flush=True)
                    continue
                print(f"    FAILED (Sarvam): {str(e)[:160]}", flush=True)
                append_transcript_row(ws_transcripts, rec, "failed", error=f"transcribe: {e}")
                failed += 1
                os.remove(local_path)
                continue

            try:
                fname = f"{key}.txt"
                file_id, link = upload_transcript_text(drive_service, transcripts_folder_id, fname, text)
                append_transcript_row(ws_transcripts, rec, "done", lang=lang, file_id=file_id, link=link)
                done += 1
            except Exception as e:                                # noqa: BLE001
                print(f"    FAILED (Drive upload): {str(e)[:160]}", flush=True)
                append_transcript_row(ws_transcripts, rec, "failed", error=f"upload: {e}")
                failed += 1
            finally:
                os.remove(local_path)
            time.sleep(0.2)

        # ---- PASS 2: batch job for LONG calls ----
        if long_calls:
            print(f"\nRouting {len(long_calls)} long call(s) through the Sarvam batch API ...", flush=True)
            by_key = {rec["Join Key"]: path for rec, path in long_calls}
            results = transcribe_batch(sarvam_client, by_key)
            for rec, local_path in long_calls:
                key = rec["Join Key"]
                result = results.get(key)
                if not result:
                    append_transcript_row(ws_transcripts, rec, "failed", error="batch: no result")
                    failed += 1
                else:
                    text, lang = result
                    try:
                        fname = f"{key}.txt"
                        file_id, link = upload_transcript_text(
                            drive_service, transcripts_folder_id, fname, text)
                        append_transcript_row(
                            ws_transcripts, rec, "done", lang=lang, file_id=file_id, link=link)
                        done += 1
                    except Exception as e:                        # noqa: BLE001
                        print(f"    FAILED (Drive upload, batch): {str(e)[:160]}", flush=True)
                        append_transcript_row(ws_transcripts, rec, "failed", error=f"upload: {e}")
                        failed += 1
                if os.path.exists(local_path):
                    os.remove(local_path)
    finally:
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass  # non-empty (a temp file leaked on an unexpected exit) — harmless, VPS /tmp clears on reboot

    print("\n----- DONE -----")
    print(f"  transcribed : {done}")
    print(f"  failed      : {failed}")
    print(f"  tab         : {TRANSCRIPT_TAB}")
    print(f"  drive folder: {TRANSCRIPTS_FOLDER_NAME}")


if __name__ == "__main__":
    main()
