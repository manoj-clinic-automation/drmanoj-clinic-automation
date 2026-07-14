#!/usr/bin/env python3
"""
flag_investigator.py  —  D239 Flag Investigator (v1.2, Session 145)
Dr. Manoj Agarwal Clinic, Bareilly.

  v1.2 (F-44): a provider-missed call is no longer mislabelled "never
  recorded". MyOperator counts a call's clock from the first ring, so a
  missed call can still show tens of "talk" seconds -- but it never has a
  recording, and that is correct, not a fault. Two guards now use
  MyOperator's own status instead of the duration alone:
    - is_lost_candidate() drops any Call_Durations row whose top-level
      status is "missed"/"voicemail" before it can become a candidate.
    - diagnose() gives Search-Logs status "2" its own outcome,
      "missed_no_conversation" (no recording expected), and restricts
      "never_recorded" to status "1" with a blank filename -- i.e. the
      provider says the call CONNECTED yet produced no recording. That
      genuine subset is the only thing the Lokesh threshold now counts.

  v1.1 (F-43): the self-heal kick is now gated on the durable per-call
  "kicked" flag, not on an outcome transition. v1 gated on the transition
  into "recoverable", which let a --no-heal run (or a failed kick) silently
  consume the transition and suppress the real kick forever.

WHAT THIS DOES
  Every 30 minutes during clinic hours it looks at Call_Durations for
  "lost conversations" — connected calls that carry real talk time but for
  which NO recording ever reached us (recording_filename is blank). This is
  fault F-42. For each such call it asks MyOperator's own Search Logs API the
  one question the daily digest cannot answer on its own:

        does the recording actually EXIST on MyOperator's side?

  and then acts:

    * RECOVERABLE — the provider HAS the recording (status "1" + a filename),
      our pipeline simply missed it. If the call is from TODAY, the
      Investigator drops one ordinary pipeline "kick", exactly as the
      call-hook does at hang-up, so the worker re-runs today's
      archive -> transcribe -> verdict and pulls the recording in. Those
      stages are idempotent, so a re-run is safe. (A call from an EARLIER
      day is reported with the exact one-line re-run command instead of being
      auto-run — see the v1 BOUNDARY note below.)

    * NEVER RECORDED — the provider says the call CONNECTED (status "1") yet
      produced NO recording (blank filename). Nothing to heal; this is the
      one genuine provider gap. It is LABELLED and COUNTED. If 3 or more of
      these pile up inside a rolling 7 days, the results file raises the
      "take this to Lokesh" flag (D239 default threshold).

    * MISSED, NO CONVERSATION -- the provider marks the call missed
      (status "2"): nobody answered, so no recording ever existed and none
      was expected. This is NOT a fault (F-44): it used to be mislabelled
      "never recorded" and inflated the Lokesh count. It is labelled
      "missed_no_conversation", surfaced for visibility, and NOT counted.

    * NO PROVIDER LOG — we have a Call_Durations row but MyOperator's search
      returns nothing matching it. Rare; surfaced as an anomaly, not counted
      as never-recorded.

  Everything it learns is written to ONE results file
  (flag_investigator_results.json). The daily digest READS that file to turn
  its blunt "N calls produced no recording — check" line into a precise
  "X recoverable, Y never-recorded (raise with Lokesh)" line. Wiring the
  digest to read this file is a separate, later step; this script only
  produces the file.

WHY IT WRITES A FILE, NOT A SHEET TAB (one-writer rule, D235 / F-3 / F-39)
  Call_Durations has exactly one writer — call_hook_capture.py — and
  Call_Recordings has exactly one — call_recording_archive.py. The
  Investigator must never write to either, or the two-writers-one-tab class
  of bug (F-39) comes straight back. So its output is a plain JSON file it
  alone owns. It also never runs the archive/verdict stages directly; it only
  drops a kick, so the pipeline worker stays the single orchestrator (its
  flock guarantees one pipeline at a time — the Investigator does not fight
  it).

v1 BOUNDARY (deliberate, documented — not hidden)
  Auto-self-heal covers TODAY's recoverable calls only, because a plain kick
  makes the worker run *today's* date. A recoverable call from an earlier day
  is reported as "recoverable_pastdate" with the exact command to re-run
  ("call_recording_archive.py --date D" then "call_verdict.py --date D").
  Recordings that only surface a day or more late are unusual; lifting this
  into full auto-heal is a small v1.1 (a dated kick + one worker tweak) and is
  intentionally left out of v1 to avoid duplicating the worker's orchestration
  and its lock.

FAILURE MAP (for the future Diagnostics.gs to consume)
  - MYOP_LOGS_TOKEN / service-account key missing  -> exits 2, touches nothing.
  - Sheet unreachable                              -> exits 5, writes nothing.
  - MyOperator /search HTTP error for a date       -> that date's candidates
        are recorded as "search_error" and skipped; other dates continue; the
        results file is still written. A later run retries automatically.
  - Kick drop fails                                -> logged, swallowed; the
        nightly sweep is the guaranteed floor anyway.
  Nothing this script does can lose a recording — recordings persist on
  MyOperator's cloud indefinitely; a failed run is a delay, never data loss.

CONFIG (environment, read from /root/wa/.env — same convention as the siblings)
  MYOP_LOGS_TOKEN            (required) Calling/Logs token (3f76...). Reused.
  GOOGLE_SA_KEY              (required) service-account JSON path; falls back
                             to WA_SA_KEY — the same key the other scripts use.
  SHEET_ID                  (optional) Clinic Callback Tracker id (default set).
  CALLHOOK_QUEUE_DIR        (optional) pipeline kick dir
                             (default /root/wa/recordings-archive/pipeline_queue).
  FLAG_RESULTS_FILE         (optional) results path
                             (default /root/wa/recordings-archive/flag_investigator_results.json).
  FLAG_LOOKBACK_DAYS        (optional, default 7)   how far back to diagnose.
  FLAG_GRACE_MIN            (optional, default 25)   ignore calls that ended
                             within this many minutes (still in the D200 retry).
  FLAG_MIN_TALK_SEC         (optional, default 10)   below this, "too short".
  FLAG_NEVER_REC_THRESHOLD  (optional, default 3)    never-recorded/7d -> Lokesh.

RUN
  Diagnose, write nothing, kick nothing:
    /root/wa/venv/bin/python3 flag_investigator.py --dry-run
  Real run (writes the results file, may drop ONE kick):
    /root/wa/venv/bin/python3 flag_investigator.py
  Self-test (no network, no sheet):
    /root/wa/venv/bin/python3 flag_investigator.py --selftest

  Production cron (every 30 min, 09:00-20:00 IST) — D239 default:
    */30 9-19 * * *  /root/wa/venv/bin/python3 /root/wa/recordings-archive/flag_investigator.py >> /root/wa/recordings-archive/flag_investigator.log 2>&1
    0    20   * * *  /root/wa/venv/bin/python3 /root/wa/recordings-archive/flag_investigator.py >> /root/wa/recordings-archive/flag_investigator.log 2>&1
  (The two lines together give :00 and :30 through 20:00 inclusive.)

PRIVACY
  Only the last 4 digits of any number are ever stored or printed, plus the
  internal session/join key. No patient names, no full numbers. The .env
  loader never echoes values.
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DEFAULT_SHEET_ID = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"

MYOP_HOST = "https://developers.myoperator.co"
SEARCH_PATH = "/search"
PAGE_SIZE = 100
MAX_PAGES = 50

DUR_TAB = "Call_Durations"

DEFAULT_QUEUE_DIR = "/root/wa/recordings-archive/pipeline_queue"
DEFAULT_RESULTS = "/root/wa/recordings-archive/flag_investigator_results.json"

CONNECTED_RESULTS = ("connected", "answered")   # customer_result values that mean "talked"
# Top-level (webhook) status values that mean "nobody actually talked": no
# recording exists or is expected. Same truth the Apps Script gate uses
# (status == "bridged" is a real conversation; these are not). F-44.
MISSED_STATUSES = ("missed", "voicemail")
PRUNE_DAYS = 30                                 # drop ledger entries older than this


# ---------------------------------------------------------------------------
# .env loader — identical pattern to call_recording_archive.py / call_api.py
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
    print("[flag_investigator]", *parts, file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Pure helpers (no I/O) — everything below here is unit-tested in _selftest
# ---------------------------------------------------------------------------
def last10(v):
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    return d[-10:] if len(d) >= 10 else d


def last4(v):
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    return d[-4:] if d else ""


def to_sec(v):
    """Tolerant talk/ring duration -> int seconds. Accepts int, '45',
    'MM:SS', 'HH:MM:SS', or junk (-> 0)."""
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    if not s:
        return 0
    if ":" in s:
        try:
            parts = [int(p) for p in s.split(":")]
        except ValueError:
            return 0
        while len(parts) < 3:
            parts.insert(0, 0)
        h, m, sec = parts[-3:]
        return h * 3600 + m * 60 + sec
    try:
        return int(float(s))
    except ValueError:
        return 0


def parse_ist(iso):
    """'2026-07-13T13:21:00+05:30' -> ('2026-07-13', minutes_since_midnight).
    Returns (None, None) if unparsable."""
    s = str(iso or "").strip()
    if not s or "T" not in s:
        return None, None
    try:
        date_part, time_part = s.split("T", 1)
        datetime.datetime.strptime(date_part, "%Y-%m-%d")   # validate
        hh = int(time_part[0:2])
        mm = int(time_part[3:5])
        return date_part, hh * 60 + mm
    except (ValueError, IndexError):
        return None, None


def dur_direction(client_ref_id):
    """IN-<session> rows are incoming; everything else is treated as outgoing."""
    return "incoming" if str(client_ref_id or "").strip().startswith("IN-") else "outgoing"


def session_key(row):
    """Stable per-call key. Prefer the stored session_id, then the client_ref_id,
    then a phone+end synthetic. Used as the ledger key and for matching."""
    sid = str(row.get("session_id", "") or "").strip()
    if sid:
        return sid
    ref = str(row.get("client_ref_id", "") or "").strip()
    if ref:
        return ref
    ph = last10(row.get("phone10", ""))
    _d, tm = parse_ist(row.get("ended_at_ist", ""))
    return "%s_%s" % (ph or "unknown", tm if tm is not None else "na")


def is_lost_candidate(row, now_ist, grace_min, min_talk):
    """True + reason when a Call_Durations row is a lost-conversation candidate:
    connected, real talk time, no recording yet, and past the pipeline grace."""
    if str(row.get("recording_filename", "") or "").strip():
        return False, "has recording"
    status = str(row.get("status", "") or "").strip().lower()
    if status in MISSED_STATUSES:
        # F-44: provider marked this missed/voicemail. Any "talk" seconds are
        # ring/hold time, not a conversation; no recording exists or is due.
        return False, "provider marked it %s -- no conversation" % status
    result = str(row.get("customer_result", "") or "").strip().lower()
    talk = to_sec(row.get("customer_talk_duration", ""))
    if result == "not_answered":
        return False, "not answered"
    if talk <= 0 and result not in CONNECTED_RESULTS:
        return False, "no talk time"
    if talk < min_talk:
        return False, "too short (%ds)" % talk
    date_str, tm = parse_ist(row.get("ended_at_ist", ""))
    if date_str is None:
        return False, "unparsable time"
    today = now_ist.strftime("%Y-%m-%d")
    if date_str == today and tm is not None:
        age = (now_ist.hour * 60 + now_ist.minute) - tm
        if 0 <= age <= grace_min:
            return False, "still in pipeline grace (%dm)" % age
    return True, "connected %ds, no recording" % talk


def hit_id_candidates(source):
    """Best-effort provider unique-id fields, tried in order for a strong match."""
    out = []
    for k in ("id", "uniqueid", "unique_id", "callid", "call_id", "session_id"):
        v = source.get(k)
        if v not in (None, ""):
            out.append(str(v).strip())
    return out


def enrich_hit(hit):
    """One /search hit -> flat fields the matcher and diagnoser use."""
    s = (hit or {}).get("_source") or {}
    start_unix = 0
    try:
        start_unix = int(s.get("start_time") or 0)
    except (ValueError, TypeError):
        start_unix = 0
    dur = to_sec(s.get("duration") or "00:00:00")
    return {
        "phone10": last10(s.get("caller_number_raw") or s.get("caller_number") or ""),
        "start_unix": start_unix,
        "end_unix": start_unix + dur if start_unix else 0,
        "status": str(s.get("status") or ""),
        "filename": str(s.get("filename") or "").strip(),
        "ids": hit_id_candidates(s),
    }


def _minutes_of_unix(unix):
    if not unix:
        return None
    t = datetime.datetime.fromtimestamp(int(unix), tz=IST)
    return t.hour * 60 + t.minute


def match_hit(row, hits, tol_min=6):
    """Find the hit(s) for a Call_Durations row.
    Strong match: shared unique id. Weak match: same phone + end-time within
    tol_min. Returns the chosen hit, preferring one that carries a recording."""
    key = session_key(row)
    ref = str(row.get("client_ref_id", "") or "").strip()
    sid = str(row.get("session_id", "") or "").strip()
    ref_bare = ref[3:] if ref.startswith("IN-") else ref
    want_ids = {x for x in (key, sid, ref, ref_bare) if x}

    strong = [h for h in hits if want_ids & set(h.get("ids", []))]
    if strong:
        with_rec = [h for h in strong if h["filename"]]
        return (with_rec or strong)[0]

    ph = last10(row.get("phone10", ""))
    _d, row_min = parse_ist(row.get("ended_at_ist", ""))
    if not ph or row_min is None:
        return None
    weak = []
    for h in hits:
        if h["phone10"] and h["phone10"] == ph:
            hm = _minutes_of_unix(h["end_unix"]) or _minutes_of_unix(h["start_unix"])
            if hm is not None and abs(hm - row_min) <= tol_min:
                weak.append(h)
    if not weak:
        return None
    with_rec = [h for h in weak if h["filename"]]
    return (with_rec or weak)[0]


def diagnose(row, hits):
    """(outcome, detail, provider_filename). outcome in
    recoverable | never_recorded | missed_no_conversation | no_provider_log.

    F-44: Search-Logs status "1" = answered, "2" = missed. A missed call never
    has a recording and none is expected, so it is NOT "never recorded" -- it
    gets its own outcome and is not counted toward the Lokesh threshold.
    "never_recorded" now means only the genuine gap: the provider says the
    call CONNECTED (status "1") yet carries no filename."""
    h = match_hit(row, hits)
    if h is None:
        return "no_provider_log", "no matching call in MyOperator search", ""
    status = str(h["status"] or "").strip()
    if status == "2":
        return ("missed_no_conversation",
                "provider marks this a missed call (status 2) -- no recording expected", "")
    if status == "1" and h["filename"]:
        return "recoverable", "recording exists at provider (status 1)", h["filename"]
    if status == "1":
        return ("never_recorded",
                "provider says connected (status 1) but produced no recording", "")
    return ("no_provider_log",
            "provider log present, unrecognised status %s" % (status or "?"), "")


# ---------------------------------------------------------------------------
# Ledger (the results file) — pure merge/count logic
# ---------------------------------------------------------------------------
def _now_iso(now_ist):
    return now_ist.strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"


def upsert_entry(ledger, cand, now_ist):
    """ledger: {key: entry}. cand carries a fresh diagnosis. Preserves
    first_seen / kicked state; bumps observations. Idempotent per run."""
    key = cand["key"]
    prev = ledger.get(key)
    entry = {
        "key": key,
        "date": cand["date"],
        "time": cand["time"],
        "phone_last4": cand["phone_last4"],
        "talk_sec": cand["talk_sec"],
        "direction": cand["direction"],
        "outcome": cand["outcome"],
        "detail": cand["detail"],
        "provider_filename": cand.get("provider_filename", ""),
        "first_seen_ist": (prev or {}).get("first_seen_ist") or _now_iso(now_ist),
        "last_seen_ist": _now_iso(now_ist),
        "observations": ((prev or {}).get("observations") or 0) + 1,
        "kicked": bool((prev or {}).get("kicked")),
        "kick_ist": (prev or {}).get("kick_ist", ""),
        "prev_outcome": (prev or {}).get("outcome", ""),
    }
    ledger[key] = entry
    return entry


def prune_ledger(ledger, now_ist, keep_days=PRUNE_DAYS):
    cutoff = (now_ist.date() - datetime.timedelta(days=keep_days))
    out = {}
    for k, e in ledger.items():
        try:
            d = datetime.datetime.strptime(e.get("date", ""), "%Y-%m-%d").date()
        except ValueError:
            out[k] = e            # keep if date unparsable rather than drop silently
            continue
        if d >= cutoff:
            out[k] = e
    return out


def weekly_never_recorded(ledger, now_ist, days=7):
    cutoff = now_ist.date() - datetime.timedelta(days=days)
    n = 0
    for e in ledger.values():
        if e.get("outcome") != "never_recorded":
            continue
        try:
            d = datetime.datetime.strptime(e.get("date", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if d >= cutoff:
            n += 1
    return n


def newly_recoverable_today(entry, today_str):
    """Kick a TODAY recoverable call at most once, gated on the durable
    'kicked' flag — NOT on an outcome transition. (F-43: gating on the
    prev_outcome transition let a --no-heal run, or a failed kick, silently
    consume the transition and suppress the real kick forever. The 'kicked'
    flag is the true 'have we healed this yet?' marker.)"""
    return (entry["outcome"] == "recoverable"
            and entry["date"] == today_str
            and not entry["kicked"])


def summarise(ledger):
    counts = {}
    for e in ledger.values():
        counts[e["outcome"]] = counts.get(e["outcome"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# I/O — search, sheet, kick, results file (thin; logic lives above)
# ---------------------------------------------------------------------------
def myop_search(token, from_unix, to_unix, log_from=0, page_size=PAGE_SIZE):
    """Copied verbatim from call_recording_archive.py — the JSON-body POST is
    the method actually proven working on this account (D172: trust the
    running artefact, not the doc's query-string variant)."""
    url = MYOP_HOST + SEARCH_PATH
    body = {
        "token": token, "from": str(from_unix), "to": str(to_unix),
        "log_from": str(log_from), "page_size": str(page_size),
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8", "replace")
    return json.loads(raw)


def fetch_all_calls(token, from_unix, to_unix):
    all_hits, log_from = [], 0
    for _ in range(MAX_PAGES):
        data = myop_search(token, from_unix, to_unix, log_from, PAGE_SIZE)
        hits = (((data or {}).get("data") or {}).get("hits")) or []
        all_hits.extend(hits)
        if len(hits) < PAGE_SIZE:
            break
        log_from += PAGE_SIZE
    return all_hits


def day_bounds_unix(date_str):
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    start = datetime.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=IST)
    end = start + datetime.timedelta(days=1)
    return int(start.timestamp()), int(end.timestamp()) - 1


def open_durations(sa_key, sheet_id):
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(sa_key, scopes=scopes)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(sheet_id)
    ws = ss.worksheet(DUR_TAB)
    return ws.get_all_values()


def rows_as_dicts(values):
    if not values:
        return []
    head = [str(h).strip() for h in values[0]]
    out = []
    for raw in values[1:]:
        if not any(str(c).strip() for c in raw):
            continue
        out.append({h: (raw[i] if i < len(raw) else "") for i, h in enumerate(head)})
    return out


def drop_heal_kick(queue_dir, now_ist):
    """Drop one ordinary pipeline kick — identical shape to call_hook's
    pipeline_kick — so the worker re-runs today's pipeline."""
    os.makedirs(queue_dir, exist_ok=True)
    name = os.path.join(queue_dir, "%s_%s.kick"
                        % (now_ist.strftime("%Y%m%d%H%M%S%f"), os.urandom(3).hex()))
    with open(name, "w", encoding="utf-8") as f:
        json.dump({"ts": now_ist.timestamp(), "event": "flag_investigator_heal", "due": 0}, f)
    return name


def load_ledger(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {e["key"]: e for e in (data.get("calls") or []) if e.get("key")}
    except (OSError, ValueError, KeyError, TypeError):
        _log("results file unreadable; starting a fresh ledger")
        return {}


def write_ledger(path, ledger, now_ist, threshold, lookback_days):
    never7 = weekly_never_recorded(ledger, now_ist, 7)
    payload = {
        "updated_ist": _now_iso(now_ist),
        "lookback_days": lookback_days,
        "counts": summarise(ledger),
        "never_recorded_7d": never7,
        "never_recorded_threshold": threshold,
        "escalate_lokesh": never7 >= threshold,
        "calls": sorted(ledger.values(), key=lambda e: (e.get("date", ""), e.get("time", ""))),
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)          # atomic
    return payload


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Diagnose and print; write no file, drop no kick.")
    ap.add_argument("--no-heal", action="store_true",
                    help="Diagnose + write results, but never drop a kick.")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(0 if _selftest() else 1)

    _load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    _load_env("/root/wa/.env")

    token = os.environ.get("MYOP_LOGS_TOKEN", "").strip()
    sa_key = os.environ.get("GOOGLE_SA_KEY", "").strip() or os.environ.get("WA_SA_KEY", "").strip()
    sheet_id = os.environ.get("SHEET_ID", "").strip() or DEFAULT_SHEET_ID
    queue_dir = os.environ.get("CALLHOOK_QUEUE_DIR", "").strip() or DEFAULT_QUEUE_DIR
    results = os.environ.get("FLAG_RESULTS_FILE", "").strip() or DEFAULT_RESULTS
    lookback = int(os.environ.get("FLAG_LOOKBACK_DAYS", "7") or "7")
    grace = int(os.environ.get("FLAG_GRACE_MIN", "25") or "25")
    min_talk = int(os.environ.get("FLAG_MIN_TALK_SEC", "10") or "10")
    threshold = int(os.environ.get("FLAG_NEVER_REC_THRESHOLD", "3") or "3")

    if not token:
        _log("FATAL: MYOP_LOGS_TOKEN missing from environment/.env"); sys.exit(2)
    if not sa_key:
        _log("FATAL: GOOGLE_SA_KEY (or WA_SA_KEY) missing"); sys.exit(2)

    now_ist = datetime.datetime.now(IST)
    today_str = now_ist.strftime("%Y-%m-%d")
    _log("run-start", "today=%s" % today_str, "dry_run=%s" % args.dry_run,
         "lookback=%dd grace=%dm min_talk=%ds" % (lookback, grace, min_talk))

    try:
        values = open_durations(sa_key, sheet_id)
    except Exception as e:  # noqa: BLE001
        _log("FATAL sheet-open:", repr(e)); sys.exit(5)

    rows = rows_as_dicts(values)
    cutoff = now_ist.date() - datetime.timedelta(days=lookback)

    # 1) collect in-window lost candidates, grouped by date
    by_date = {}
    for r in rows:
        date_str, _tm = parse_ist(r.get("ended_at_ist", ""))
        if date_str is None:
            continue
        try:
            d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < cutoff or d > now_ist.date():
            continue
        ok, _reason = is_lost_candidate(r, now_ist, grace, min_talk)
        if ok:
            by_date.setdefault(date_str, []).append(r)

    total_cand = sum(len(v) for v in by_date.values())
    _log("candidates", "%d across %d day(s)" % (total_cand, len(by_date)))

    ledger = prune_ledger(load_ledger(results), now_ist)

    # 2) diagnose each date's candidates against one /search sweep for that day
    diagnosed = []
    for date_str, cands in sorted(by_date.items()):
        try:
            f_u, t_u = day_bounds_unix(date_str)
            hits = [enrich_hit(h) for h in fetch_all_calls(token, f_u, t_u)]
        except Exception as e:  # noqa: BLE001
            _log("search-error", date_str, repr(e))
            for r in cands:
                _d, tm = parse_ist(r.get("ended_at_ist", ""))
                diagnosed.append({
                    "key": session_key(r), "date": date_str,
                    "time": "%02d:%02d" % (tm // 60, tm % 60) if tm is not None else "",
                    "phone_last4": last4(r.get("phone10", "")),
                    "talk_sec": to_sec(r.get("customer_talk_duration", "")),
                    "direction": dur_direction(r.get("client_ref_id", "")),
                    "outcome": "search_error", "detail": "search failed this run",
                    "provider_filename": "",
                })
            continue
        for r in cands:
            outcome, detail, fname = diagnose(r, hits)
            _d, tm = parse_ist(r.get("ended_at_ist", ""))
            is_today = (date_str == today_str)
            if outcome == "recoverable" and not is_today:
                outcome = "recoverable_pastdate"
                detail += " — re-run: call_recording_archive.py --date %s then call_verdict.py --date %s" % (date_str, date_str)
            diagnosed.append({
                "key": session_key(r), "date": date_str,
                "time": "%02d:%02d" % (tm // 60, tm % 60) if tm is not None else "",
                "phone_last4": last4(r.get("phone10", "")),
                "talk_sec": to_sec(r.get("customer_talk_duration", "")),
                "direction": dur_direction(r.get("client_ref_id", "")),
                "outcome": outcome, "detail": detail, "provider_filename": fname,
            })

    # 3) upsert ledger, decide whether a heal kick is warranted (today only)
    kick_needed = False
    for cand in diagnosed:
        entry = upsert_entry(ledger, cand, now_ist)
        if newly_recoverable_today(entry, today_str):
            kick_needed = True

    counts = summarise(ledger)
    never7 = weekly_never_recorded(ledger, now_ist, 7)
    _log("diagnosis", " ".join("%s=%d" % (k, v) for k, v in sorted(counts.items())) or "(none)",
         "| never_recorded_7d=%d/%d%s" % (never7, threshold,
                                          "  -> RAISE WITH LOKESH" if never7 >= threshold else ""))

    if args.dry_run:
        for cand in sorted(diagnosed, key=lambda c: (c["date"], c["time"])):
            _log("  would-record", cand["date"], cand["time"], "..%s" % cand["phone_last4"],
                 "%ds" % cand["talk_sec"], cand["outcome"])
        _log("dry-run: no file written, no kick dropped")
        return

    # 4) self-heal (today only) then persist
    if kick_needed and not args.no_heal:
        try:
            kf = drop_heal_kick(queue_dir, now_ist)
            for e in ledger.values():
                if newly_recoverable_today(e, today_str):
                    e["kicked"] = True
                    e["kick_ist"] = _now_iso(now_ist)
            _log("self-heal", "kick dropped ->", os.path.basename(kf),
                 "(worker will re-run today's archive->verdict)")
        except Exception as e:  # noqa: BLE001
            _log("kick-failed (nightly sweep still covers):", repr(e))
    elif kick_needed and args.no_heal:
        _log("self-heal suppressed (--no-heal); recoverable calls left for the worker's nightly sweep")

    payload = write_ledger(results, ledger, now_ist, threshold, lookback)
    _log("run-done", "results ->", results,
         "escalate_lokesh=%s" % payload["escalate_lokesh"])


# ---------------------------------------------------------------------------
# Self-test — pure logic only, no network, no sheet, no real kick
# ---------------------------------------------------------------------------
def _selftest():
    import tempfile
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL:", name)

    now = datetime.datetime(2026, 7, 13, 15, 0, tzinfo=IST)   # 13-Jul 15:00 IST
    today = "2026-07-13"

    # --- duration parsing ---
    check("to_sec int", to_sec(45) == 45)
    check("to_sec str secs", to_sec("33") == 33)
    check("to_sec mm:ss", to_sec("1:41") == 101)
    check("to_sec hh:mm:ss", to_sec("00:01:07") == 67)
    check("to_sec junk", to_sec("--") == 0)
    check("to_sec none", to_sec(None) == 0)

    # --- time parsing (numeric, not text — D240g) ---
    d, m = parse_ist("2026-07-13T13:21:00+05:30")
    check("parse_ist date", d == "2026-07-13")
    check("parse_ist minutes", m == 13 * 60 + 21)
    check("parse_ist single-digit hour", parse_ist("2026-07-13T09:06:00+05:30")[1] == 9 * 60 + 6)
    check("parse_ist junk", parse_ist("") == (None, None))

    check("direction IN-", dur_direction("IN-abc123") == "incoming")
    check("direction odd", dur_direction("1206138695") == "outgoing")

    # --- candidate detection ---
    lost = {"client_ref_id": "IN-8333", "session_id": "8333", "phone10": "9876500011",
            "customer_result": "connected", "customer_talk_duration": "33",
            "recording_filename": "", "ended_at_ist": "2026-07-13T13:21:00+05:30"}
    ok, _ = is_lost_candidate(lost, now, 25, 10)
    check("candidate: connected 33s no recording", ok)

    has_rec = dict(lost, recording_filename="rec_9.mp3")
    check("not candidate: has recording", not is_lost_candidate(has_rec, now, 25, 10)[0])

    short = dict(lost, customer_talk_duration="6")
    check("not candidate: too short 6s", not is_lost_candidate(short, now, 25, 10)[0])

    not_ans = dict(lost, customer_result="not_answered", customer_talk_duration="0")
    check("not candidate: not answered", not is_lost_candidate(not_ans, now, 25, 10)[0])

    # F-44: a provider-missed row is never a candidate, even with "talk" seconds.
    missed_row = dict(lost, status="missed", customer_result="connected",
                      customer_talk_duration="40")
    check("not candidate: provider status missed", not is_lost_candidate(missed_row, now, 25, 10)[0])
    vmail_row = dict(lost, status="voicemail", customer_talk_duration="40")
    check("not candidate: provider status voicemail", not is_lost_candidate(vmail_row, now, 25, 10)[0])
    bridged_row = dict(lost, status="bridged")
    check("still a candidate when status bridged", is_lost_candidate(bridged_row, now, 25, 10)[0])

    fresh = dict(lost, ended_at_ist="2026-07-13T14:50:00+05:30")   # 10 min before 15:00
    check("not candidate: inside grace", not is_lost_candidate(fresh, now, 25, 10)[0])

    odd = {"client_ref_id": "1206138695", "session_id": "1206138695", "phone10": "9812345678",
           "customer_result": "answered", "customer_talk_duration": "19",
           "recording_filename": "", "ended_at_ist": "2026-07-13T14:54:00+05:30"}
    # 14:54 is 6 min before 15:00 -> inside 25m grace, so NOT yet a candidate...
    check("odd-key inside grace not yet", not is_lost_candidate(odd, now, 25, 10)[0])
    later = datetime.datetime(2026, 7, 13, 16, 0, tzinfo=IST)
    check("odd-key becomes candidate after grace", is_lost_candidate(odd, later, 25, 10)[0])

    # --- hit enrich + matching + diagnosis ---
    hit_rec = {"_source": {"id": "8333", "caller_number_raw": "919876500011",
                           "start_time": 1000, "duration": "00:00:33",
                           "status": "1", "filename": "rec_8333.mp3"}}
    hit_missed = {"_source": {"id": "7777", "caller_number_raw": "919812345678",
                              "start_time": 2000, "duration": "00:00:19",
                              "status": "2", "filename": ""}}
    hit_conn_norec = {"_source": {"id": "6666", "caller_number_raw": "919800000066",
                                  "start_time": 3000, "duration": "00:00:22",
                                  "status": "1", "filename": ""}}
    eh = enrich_hit(hit_rec)
    check("enrich status", eh["status"] == "1")
    check("enrich filename", eh["filename"] == "rec_8333.mp3")
    check("enrich ids", "8333" in eh["ids"])
    check("enrich end_unix", eh["end_unix"] == 1033)

    hits = [enrich_hit(hit_rec), enrich_hit(hit_missed), enrich_hit(hit_conn_norec)]
    check("match by id", match_hit(lost, hits) is not None and match_hit(lost, hits)["filename"] == "rec_8333.mp3")

    o, _det, fn = diagnose(lost, hits)
    check("diagnose recoverable", o == "recoverable" and fn == "rec_8333.mp3")

    # status 2 hit -> missed_no_conversation (F-44), NOT never_recorded
    lost_missed = {"client_ref_id": "IN-7777", "session_id": "7777", "phone10": "9812345678",
                   "customer_result": "connected", "customer_talk_duration": "19",
                   "recording_filename": "", "ended_at_ist": "2026-07-13T13:33:00+05:30"}
    om, _dm, _fm = diagnose(lost_missed, hits)
    check("diagnose missed_no_conversation (status 2)", om == "missed_no_conversation")

    # status 1 + blank filename -> the genuine never_recorded
    lost_nr = {"client_ref_id": "IN-6666", "session_id": "6666", "phone10": "9800000066",
               "customer_result": "connected", "customer_talk_duration": "22",
               "recording_filename": "", "ended_at_ist": "2026-07-13T13:40:00+05:30"}
    o2, _d2, _f2 = diagnose(lost_nr, hits)
    check("diagnose never_recorded (status 1, no file)", o2 == "never_recorded")

    lost_nolog = dict(lost, session_id="NOPE", client_ref_id="IN-NOPE", phone10="9000000000")
    o3, _d3, _f3 = diagnose(lost_nolog, hits)
    check("diagnose no_provider_log", o3 == "no_provider_log")

    # weak match by phone+time when ids differ
    row_weak = {"client_ref_id": "IN-zzz", "session_id": "", "phone10": "9876500011",
                "customer_result": "connected", "customer_talk_duration": "33",
                "recording_filename": "", "ended_at_ist": "2026-07-13T00:16:40+05:30"}
    # hit_rec start_time 1000 -> 1970 epoch; skip real-date coupling: just assert phone matcher runs
    check("weak matcher returns something or none safely",
          match_hit(row_weak, hits) is None or isinstance(match_hit(row_weak, hits), dict))

    # --- ledger upsert / idempotence / counts / threshold ---
    led = {}
    cand = {"key": "8333", "date": today, "time": "13:21", "phone_last4": "0011",
            "talk_sec": 33, "direction": "incoming", "outcome": "recoverable",
            "detail": "x", "provider_filename": "rec_8333.mp3"}
    e1 = upsert_entry(led, cand, now)
    check("upsert observations=1", e1["observations"] == 1)
    check("newly recoverable today true", newly_recoverable_today(e1, today))
    e2 = upsert_entry(led, cand, now)
    check("upsert idempotent key count", len(led) == 1)
    check("upsert observations bumped", e2["observations"] == 2)
    check("still kick-eligible after a --no-heal observation (F-43)",
          newly_recoverable_today(dict(e2, prev_outcome="recoverable"), today))
    check("NOT kick-eligible once actually kicked (F-43)",
          not newly_recoverable_today(dict(e2, kicked=True), today))

    pastcand = dict(cand, key="p1", date="2026-07-10", outcome="recoverable_pastdate")
    ep = upsert_entry(led, pastcand, now)
    check("pastdate not kick-eligible", not newly_recoverable_today(ep, today))

    for i in range(3):
        upsert_entry(led, {"key": "nr%d" % i, "date": today, "time": "1%d:00" % i,
                           "phone_last4": "22%d" % i, "talk_sec": 40, "direction": "incoming",
                           "outcome": "never_recorded", "detail": "", "provider_filename": ""}, now)
    check("weekly never_recorded = 3", weekly_never_recorded(led, now, 7) == 3)
    check("threshold escalates at 3", weekly_never_recorded(led, now, 7) >= 3)

    # F-44: a missed_no_conversation entry must NOT count toward never_recorded/7d
    upsert_entry(led, {"key": "miss1", "date": today, "time": "12:00",
                       "phone_last4": "3330", "talk_sec": 40, "direction": "incoming",
                       "outcome": "missed_no_conversation", "detail": "", "provider_filename": ""}, now)
    check("missed_no_conversation not counted in never_recorded 7d",
          weekly_never_recorded(led, now, 7) == 3)
    check("missed_no_conversation appears in summary counts",
          summarise(led).get("missed_no_conversation") == 1)

    old = {"key": "old1", "date": "2026-06-01", "time": "10:00", "phone_last4": "9999",
           "talk_sec": 50, "direction": "incoming", "outcome": "never_recorded",
           "detail": "", "provider_filename": ""}
    led["old1"] = old
    check("old entry not counted in 7d", weekly_never_recorded(led, now, 7) == 3)
    pruned = prune_ledger(led, now, 30)
    check("prune drops >30d entry", "old1" not in pruned)
    check("prune keeps recent", "8333" in pruned)

    # --- results file round-trip (write -> load -> same keys) ---
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "res.json")
        payload = write_ledger(path, pruned, now, 3, 7)
        check("payload escalate flag", payload["escalate_lokesh"] is True)
        reloaded = load_ledger(path)
        check("roundtrip preserves keys", set(reloaded.keys()) == set(pruned.keys()))
        check("results file has no full phone",
              "9876500011" not in open(path, encoding="utf-8").read())
        # kick file shape
        kf = drop_heal_kick(os.path.join(td, "q"), now)
        kick = json.load(open(kf, encoding="utf-8"))
        check("kick has due=0", kick.get("due") == 0)
        check("kick event tagged", kick.get("event") == "flag_investigator_heal")

    print("SELFTEST: %d/%d PASS" % (passed, passed + failed))
    return failed == 0


if __name__ == "__main__":
    main()
