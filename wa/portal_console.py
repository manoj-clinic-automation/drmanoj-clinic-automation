#!/usr/bin/env python3
"""
portal_console.py  --  D297 Call-Intelligence Console : Stage A builder (A1 core)

Reads the two live Google Sheets READ-ONLY and builds the SQLite spine
/root/wa/console.db that every downstream console view (Stage B page, gist
metric 5, referee, digest, ...) reads from.  Sole writer of console.db.

Built from D297_Call_Console_Contract_v4_FINAL.md (Appendix A ground truth,
S166).  Nothing here is from memory: schemas are discovered from the live
header rows by NAME (never by position); a required column that is absent
halts the build with the real header row printed (D188 -- a filename/position
is not provenance).

Scope THIS FILE = A1 core + A2a:
  join (Call_Durations x Call_Recordings-bridge x Call_Verdicts x Patient_Master
        x Outbound_Log x Agents) . conversation threads . two-way net-missed
        . reasons-not-judged . latency . net-missed reconcile vs Daily_Summary.
  A2a: net-missed rule ported from the live Netting.gs / Config.gs
       (CFG.RESOLUTION_MUST_BE_AFTER=false) -- a conversation is net-missed iff it
       has >=1 INCOMING missed leg and NO connected leg in either direction
       (outbound-miss-only is NOT a candidate; any connect resolves).
Optional layers in THIS file (ported from live; enable with a flag):
  --with-myop-reconcile  (A2b) reproduce Daily_Summary from the MyOperator /search
                          log AND resolve the open list our webhook over-counted.
  --with-transcripts     (A3) back-pull Drive transcript text (text/plain, get_media,
                          READ-ONLY) into a PERSISTENT cache -> merged into console.db.

Modes (exactly one):
  --selftest   offline, synthetic fixtures, NO network/gspread. Proves the whole
               transform path.  This is the gate that runs on the build machine.
  --dry-run    on the VPS: reads both live Sheets READ-ONLY, writes NOTHING to
               Sheets and does NOT write console.db.  Prints the discovered header
               inventory + row counts + join-match rate + net-missed reconcile vs
               Daily_Summary.  This is the pre-ship reconcile (contract 13-A).
  --build      reads live READ-ONLY, writes console.db atomically (tmp + replace).

Credential: service-account JSON path in env GOOGLE_SA_KEY (alias WA_SA_KEY),
resolved from the clinic .env (/root/wa/recordings-archive/.env or /root/wa/.env).
Google scope is spreadsheets.readonly -- read-only is enforced at the API.
VPS python: /root/wa/venv/bin/python3
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Identifiers (D297 v4 Appendix A -- re-verify live)
# ---------------------------------------------------------------------------
TRACKER_SHEET_ID = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"   # Clinic Callback Tracker
AUDIT_SHEET_ID   = "1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ"   # Call Audit (Doctor Only)

READONLY_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

DEFAULT_DB   = "/root/wa/console.db"
ENV_CANDIDATES = ["/root/wa/recordings-archive/.env", "/root/wa/.env"]
SA_ENV_KEYS  = ["GOOGLE_SA_KEY", "WA_SA_KEY"]

# MyOperator /search (A2b) -- ported from the live flag_investigator.py / Config.gs
MYOP_HOST        = "https://developers.myoperator.co"
MYOP_SEARCH_PATH = "/search"
MYOP_PAGE_SIZE   = 100          # Config.gs PAGE_SIZE (API max)
MYOP_MAX_PAGES   = 50           # Config.gs MAX_PAGES safety stop
MYOP_TOKEN_KEY   = "MYOP_LOGS_TOKEN"
IST              = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# Tab specs.  For each tab: which sheet it lives in, its tab name, and the
# canonical field -> acceptable header aliases.  'required' fields must be
# found or the build halts.  Header matching is by NAME, normalised
# (lowercased, non-alphanumerics stripped) so minor punctuation/spacing
# differences don't break discovery -- while the real header is still printed.
# ---------------------------------------------------------------------------
TRACKER = "tracker"
AUDIT   = "audit"

TABS = {
    "Call_Durations": {
        "sheet": TRACKER,
        "required": {
            "category":            ["category"],
            "status":              ["status"],
            "recording_filename":  ["recording_filename", "recordingfilename"],
            "phone10":             ["phone10"],
        },
        "optional": {
            "client_ref_id":            ["client_ref_id"],
            "ref_id":                   ["ref_id"],
            "session_id":               ["session_id"],
            "total_duration":           ["total_duration"],
            "customer_result":          ["customer_result"],
            "customer_talk_duration":   ["customer_talk_duration"],
            "customer_ring_duration":   ["customer_ring_duration"],
            "ended_at_ist":             ["ended_at_ist"],
            "captured_at_ist":          ["captured_at_ist"],
            "source_event":             ["source_event"],
        },
    },
    "Call_Recordings": {   # headers NOT pinned in Appendix A -> discovered here
        "sheet": TRACKER,
        "required": {
            "myoperator_filename": ["myoperator filename", "myoperatorfilename"],
            "join_key":            ["join key", "joinkey"],
        },
        "optional": {
            "recording_link":      ["recording link", "recordinglink", "link"],
        },
    },
    "Call_Verdicts": {
        "sheet": AUDIT,
        "required": {
            "join_key":            ["join key", "joinkey"],
        },
        "optional": {
            "date":            ["date"],
            "time":            ["time"],
            "direction":       ["direction"],
            "patient_number":  ["patient number"],
            "agent":           ["agent"],
            "patient_name":    ["patient name"],
            "clinic_id":       ["clinic id"],
            "duration":        ["duration"],
            "claimed_outcome": ["claimed outcome"],
            "ai_outcome":      ["ai outcome"],
            "verdict":         ["verdict"],
            "match_confidence":["match confidence"],
            "outcome_tf":      ["outcome true/false", "outcome truefalse", "outcometruefalse"],
            "spoke_with":      ["spoke with"],
            "flag_postop":     ["flag postop"],
            "flag_complaint":  ["flag complaint"],
            "flag_urgent":     ["flag urgent"],
            "flag_surgery":    ["flag surgery"],
            "flag_clinical":   ["flag clinical"],
            "flag_conduct":    ["flag conduct"],
            "conduct_note":    ["conduct note"],
            "recording_link":  ["recording link"],
            "transcript_link": ["transcript link"],
            "status":          ["status"],
            "error":           ["error"],
            "judged_at":       ["judged at"],
            "prompt_ver":      ["prompt ver"],
            "model":           ["model"],
            "doctor_flag":     ["doctor flag"],
            "doctor_note":     ["doctor note"],
            "final_outcome":   ["final outcome"],
        },
    },
    "Call_Transcripts": {  # headers NOT pinned in Appendix A -> discovered here
        "sheet": TRACKER,
        "required": {
            "join_key":       ["join key", "joinkey"],
        },
        "optional": {
            "transcribed_at": ["transcribed at", "transcribedat"],
            "text":           ["transcript text", "content"],
            "drive_file_id":  ["transcript drive file id", "transcriptdrivefileid"],
        },
    },
    "Patient_Master": {
        "sheet": TRACKER,
        "required": {
            "mobile":        ["mobile"],
            "patient_name":  ["patient name"],
        },
        "optional": {
            "diagnosis":     ["diagnosis"],
            "age":           ["age"],
            "gender":        ["gender"],
            "last_visit":    ["last visit"],
            "patient_uid":   ["patient uid"],
            "clinic_id":     ["clinic_specific_id", "clinicspecificid"],
        },
    },
    "Outbound_Log": {
        "sheet": TRACKER,
        "required": {
            "phone10":    ["phone10"],
            "agent":      ["agent"],
        },
        "optional": {
            "date":       ["date"],
            "time":       ["time"],
            "duration_s": ["duration_s", "durations"],
            "status":     ["status"],
            "start_unix": ["start_unix", "startunix"],
        },
    },
    "Agents": {
        "sheet": TRACKER,
        "required": {
            "ext":   ["ext"],
            "name":  ["name"],
        },
        "optional": {
            "userid": ["userid"],
            "active": ["active"],
        },
    },
    "Daily_Summary": {
        "sheet": TRACKER,
        "required": {
            "date":       ["date"],
            "net_missed": ["net-missed", "net missed", "netmissed"],
        },
        "optional": {
            "total_calls": ["total calls"],
            "incoming":    ["incoming"],
            "resolved":    ["resolved"],
            "net_missed_pct": ["net-missed %", "net missed %", "netmissed"],
        },
    },
}


# ---------------------------------------------------------------------------
# Pure helpers (stdlib only -- exercised by --selftest exactly as by --build)
# ---------------------------------------------------------------------------
def norm_header(h):
    return re.sub(r"[^a-z0-9]", "", (h or "").strip().lower())


def find_cols(header_row, spec, tab_name):
    """Map canonical field -> column index by NAME. Halt on any missing required."""
    norm_index = {}
    for i, h in enumerate(header_row):
        norm_index.setdefault(norm_header(h), i)  # first wins on dup headers
    resolved = {}
    for canon, aliases in spec.get("required", {}).items():
        idx = None
        for a in aliases:
            idx = norm_index.get(norm_header(a))
            if idx is not None:
                break
        if idx is None:
            raise SystemExit(
                "HALT (D188): tab '%s' is missing required column '%s' "
                "(tried %s).\n  live header row = %s"
                % (tab_name, canon, aliases, header_row)
            )
        resolved[canon] = idx
    for canon, aliases in spec.get("optional", {}).items():
        for a in aliases:
            idx = norm_index.get(norm_header(a))
            if idx is not None:
                resolved[canon] = idx
                break
    return resolved


def rows_to_dicts(header_row, data_rows, spec, tab_name):
    cols = find_cols(header_row, spec, tab_name)
    out = []
    for r in data_rows:
        d = {}
        for canon, idx in cols.items():
            d[canon] = r[idx] if idx < len(r) else ""
        out.append(d)
    return out, list(cols.keys())


def norm_phone10(s):
    d = re.sub(r"\D", "", s or "")
    return d[-10:] if len(d) >= 10 else d


JK_RE = re.compile(r"^(\d{10})_(\d{9,12})$")


def valid_join_key(s):
    return bool(JK_RE.match((s or "").strip()))


def derive_direction(category):
    c = (category or "").strip().lower()
    if c == "incoming":
        return "In"
    if c == "obd":
        return "Out"
    return "?"


def derive_answered(status):
    """bridged -> 1 (answered), missed -> 0.  Never talk-seconds (D244/F-44)."""
    s = (status or "").strip().lower()
    if s == "bridged":
        return 1
    if s == "missed":
        return 0
    return None  # unknown (probe is filtered out before this)


_TS_FORMATS = (
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M", "%Y/%m/%d %H:%M:%S",
)


def parse_ts(s):
    """Parse a timestamp to a NAIVE datetime. Any tz-aware value (e.g. an
    ISO string carrying +05:30) has its tzinfo dropped, so every comparison
    and subtraction is on one wall clock -- every source column here is IST.
    Mixed aware/naive would otherwise raise (seen live, S167). A genuine
    cross-zone source would surface as a suspicious ~constant offset in the
    latency stats rather than being silently wrong (F-41 lesson)."""
    s = (s or "").strip()
    if not s:
        return None
    dt = None
    for fmt in _TS_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            break
        except ValueError:
            pass
    if dt is None:
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            return None
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def unjudged_reason(has_join_key, has_recording, verdict):
    """Why a call carries no usable AI verdict.  None => judged fine."""
    if verdict is None:
        if not has_recording:
            return "no recording"
        if not has_join_key:
            return "no join key (recording unmatched)"
        return "judge pending"
    st = (verdict.get("status") or "").strip().lower()
    if (verdict.get("error") or "").strip():
        return "verdict error"
    if st in ("error", "failed"):
        return "verdict error"
    if not (verdict.get("verdict") or "").strip():
        return "judge pending"
    return None


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_ref_id TEXT, ref_id TEXT, session_id TEXT,
  category TEXT, status TEXT, direction TEXT, answered INTEGER,
  total_duration TEXT, customer_result TEXT,
  customer_talk_duration TEXT, customer_ring_duration TEXT,
  recording_filename TEXT, ended_at_ist TEXT, captured_at_ist TEXT,
  source_event TEXT, phone10 TEXT, join_key TEXT
);
CREATE INDEX ix_calls_jk    ON calls(join_key);
CREATE INDEX ix_calls_phone ON calls(phone10);

CREATE TABLE verdicts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  join_key TEXT, date TEXT, time TEXT, direction TEXT, patient_number TEXT,
  agent TEXT, patient_name TEXT, clinic_id TEXT, duration TEXT,
  claimed_outcome TEXT, not_filed INTEGER, ai_outcome TEXT, verdict TEXT,
  match_confidence TEXT, outcome_tf TEXT, spoke_with TEXT,
  flag_postop TEXT, flag_complaint TEXT, flag_urgent TEXT, flag_surgery TEXT,
  flag_clinical TEXT, flag_conduct TEXT, conduct_note TEXT,
  recording_link TEXT, transcript_link TEXT, status TEXT, error TEXT,
  judged_at TEXT, prompt_ver TEXT, model TEXT,
  doctor_flag TEXT, doctor_note TEXT, final_outcome TEXT
);
CREATE INDEX ix_verdicts_jk ON verdicts(join_key);

CREATE TABLE recordings (myoperator_filename TEXT, join_key TEXT, recording_link TEXT);
CREATE INDEX ix_rec_fn ON recordings(myoperator_filename);

CREATE TABLE transcripts (join_key TEXT, transcribed_at TEXT, text TEXT, drive_file_id TEXT);
CREATE INDEX ix_tr_jk ON transcripts(join_key);

CREATE TABLE patients (
  phone10 TEXT, name TEXT, diagnosis TEXT, age TEXT, gender TEXT,
  last_visit TEXT, patient_uid TEXT, clinic_id TEXT
);
CREATE INDEX ix_pat_phone ON patients(phone10);

CREATE TABLE outbound (
  phone10 TEXT, agent TEXT, start_unix TEXT, date TEXT, time TEXT,
  duration_s TEXT, status TEXT
);

CREATE TABLE agents (ext TEXT, name TEXT, userid TEXT, active TEXT);

CREATE TABLE daily_summary (
  date TEXT, total_calls TEXT, incoming TEXT, net_missed TEXT,
  resolved TEXT, net_missed_pct TEXT
);

CREATE TABLE conversations (
  phone10 TEXT PRIMARY KEY, attempts INTEGER, miss_attempts INTEGER,
  any_connected INTEGER, net_missed_open INTEGER, first_ts TEXT, last_ts TEXT,
  last_direction TEXT, last_status TEXT, last_agent TEXT, resolved_by TEXT
);

CREATE TABLE latency (
  join_key TEXT, t_call TEXT, t_transcript TEXT, t_judge TEXT,
  lag_tx_call REAL, lag_judge_tx REAL, lag_judge_call REAL
);

CREATE TABLE unjudged (id INTEGER PRIMARY KEY AUTOINCREMENT, join_key TEXT, phone10 TEXT, reason TEXT);

CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
"""


def create_schema(conn):
    conn.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Loaders (operate on already-normalised dicts -- same path for test & build)
# ---------------------------------------------------------------------------
def load_recordings(conn, rows):
    """Insert recordings; return {myoperator_filename: join_key} for valid keys."""
    index = {}
    for d in rows:
        fn = (d.get("myoperator_filename") or "").strip()
        jk = (d.get("join_key") or "").strip()
        conn.execute("INSERT INTO recordings VALUES (?,?,?)",
                     (fn, jk, d.get("recording_link", "")))
        if fn and valid_join_key(jk):
            index.setdefault(fn, jk)
    return index


def load_calls(conn, rows, rec_index):
    kept = skipped_probe = unknown_status = matched_jk = 0
    for d in rows:
        status = d.get("status", "")
        if (status or "").strip().lower() == "probe":       # spine excludes probe
            skipped_probe += 1
            continue
        answered = derive_answered(status)
        if answered is None:
            unknown_status += 1
        fn = (d.get("recording_filename") or "").strip()
        jk = rec_index.get(fn) if fn else None
        if jk:
            matched_jk += 1
        conn.execute(
            "INSERT INTO calls (client_ref_id,ref_id,session_id,category,status,"
            "direction,answered,total_duration,customer_result,"
            "customer_talk_duration,customer_ring_duration,recording_filename,"
            "ended_at_ist,captured_at_ist,source_event,phone10,join_key) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d.get("client_ref_id", ""), d.get("ref_id", ""), d.get("session_id", ""),
             d.get("category", ""), status, derive_direction(d.get("category", "")),
             answered, d.get("total_duration", ""), d.get("customer_result", ""),
             d.get("customer_talk_duration", ""), d.get("customer_ring_duration", ""),
             fn, d.get("ended_at_ist", ""), d.get("captured_at_ist", ""),
             d.get("source_event", ""), norm_phone10(d.get("phone10", "")), jk),
        )
        kept += 1
    return {"kept": kept, "skipped_probe": skipped_probe,
            "unknown_status": unknown_status, "matched_jk": matched_jk}


def load_verdicts(conn, rows):
    for d in rows:
        claimed = (d.get("claimed_outcome") or "").strip()
        conn.execute(
            "INSERT INTO verdicts (join_key,date,time,direction,patient_number,agent,"
            "patient_name,clinic_id,duration,claimed_outcome,not_filed,ai_outcome,"
            "verdict,match_confidence,outcome_tf,spoke_with,flag_postop,flag_complaint,"
            "flag_urgent,flag_surgery,flag_clinical,flag_conduct,conduct_note,"
            "recording_link,transcript_link,status,error,judged_at,prompt_ver,model,"
            "doctor_flag,doctor_note,final_outcome) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d.get("join_key", ""), d.get("date", ""), d.get("time", ""),
             d.get("direction", ""), d.get("patient_number", ""), d.get("agent", ""),
             d.get("patient_name", ""), d.get("clinic_id", ""), d.get("duration", ""),
             claimed, 1 if claimed == "" else 0, d.get("ai_outcome", ""),
             d.get("verdict", ""), d.get("match_confidence", ""), d.get("outcome_tf", ""),
             d.get("spoke_with", ""), d.get("flag_postop", ""), d.get("flag_complaint", ""),
             d.get("flag_urgent", ""), d.get("flag_surgery", ""), d.get("flag_clinical", ""),
             d.get("flag_conduct", ""), d.get("conduct_note", ""), d.get("recording_link", ""),
             d.get("transcript_link", ""), d.get("status", ""), d.get("error", ""),
             d.get("judged_at", ""), d.get("prompt_ver", ""), d.get("model", ""),
             d.get("doctor_flag", ""), d.get("doctor_note", ""), d.get("final_outcome", "")),
        )


def load_transcripts(conn, rows):
    for d in rows:
        conn.execute("INSERT INTO transcripts (join_key,transcribed_at,text,drive_file_id) "
                     "VALUES (?,?,?,?)",
                     (d.get("join_key", ""), d.get("transcribed_at", ""),
                      d.get("text", ""), d.get("drive_file_id", "")))


def load_patients(conn, rows):
    for d in rows:
        conn.execute("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)",
                     (norm_phone10(d.get("mobile", "")), d.get("patient_name", ""),
                      d.get("diagnosis", ""), d.get("age", ""), d.get("gender", ""),
                      d.get("last_visit", ""), d.get("patient_uid", ""), d.get("clinic_id", "")))


def load_outbound(conn, rows):
    for d in rows:
        conn.execute("INSERT INTO outbound VALUES (?,?,?,?,?,?,?)",
                     (norm_phone10(d.get("phone10", "")), d.get("agent", ""),
                      d.get("start_unix", ""), d.get("date", ""), d.get("time", ""),
                      d.get("duration_s", ""), d.get("status", "")))


def load_agents(conn, rows):
    for d in rows:
        conn.execute("INSERT INTO agents VALUES (?,?,?,?)",
                     (d.get("ext", ""), d.get("name", ""), d.get("userid", ""), d.get("active", "")))


def load_daily_summary(conn, rows):
    for d in rows:
        conn.execute("INSERT INTO daily_summary VALUES (?,?,?,?,?,?)",
                     (d.get("date", ""), d.get("total_calls", ""), d.get("incoming", ""),
                      d.get("net_missed", ""), d.get("resolved", ""), d.get("net_missed_pct", "")))


# ---------------------------------------------------------------------------
# Derived builders
# ---------------------------------------------------------------------------
def build_conversations(conn):
    """A conversation = all calls sharing phone10 (contract 4).
    Net-missed rule ported from Netting.gs (CFG.RESOLUTION_MUST_BE_AFTER=false):
    a conversation is NET-MISSED-OPEN iff it has >=1 INCOMING missed leg and NO
    connected leg in either direction. Outbound-miss-only is NOT a candidate."""
    groups = {}
    for row in conn.execute(
        "SELECT phone10, answered, direction, status, ended_at_ist, captured_at_ist, join_key "
        "FROM calls WHERE phone10 <> ''"
    ):
        phone, answered, direction, status, ended, captured, jk = row
        groups.setdefault(phone, []).append(
            {"answered": answered, "direction": direction, "status": status,
             "ended": ended, "captured": captured, "jk": jk})
    for phone, calls in groups.items():
        # order by best available timestamp; unparseable rows keep original order
        def keyf(c, i):
            ts = parse_ts(c["ended"]) or parse_ts(c["captured"])
            return (0, ts) if ts else (1, i)
        ordered = [c for _, c in sorted(
            ((keyf(c, i), c) for i, c in enumerate(calls)), key=lambda t: (t[0][0], t[0][1] if t[0][0] == 0 else 0, t[0][1]))]
        any_conn = 1 if any(c["answered"] == 1 for c in ordered) else 0
        miss_attempts = sum(1 for c in ordered
                            if c["direction"] == "In" and c["answered"] == 0)
        net_open = 1 if (miss_attempts > 0 and not any_conn) else 0
        first_ts = ordered[0]["ended"] or ordered[0]["captured"]
        last = ordered[-1]
        last_ts = last["ended"] or last["captured"]
        last_agent = ""
        if last["jk"]:
            r = conn.execute("SELECT agent FROM verdicts WHERE join_key=? LIMIT 1",
                             (last["jk"],)).fetchone()
            if r:
                last_agent = r[0] or ""
        conn.execute(
            "INSERT INTO conversations (phone10,attempts,miss_attempts,any_connected,"
            "net_missed_open,first_ts,last_ts,last_direction,last_status,last_agent) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (phone, len(ordered), miss_attempts, any_conn, net_open, first_ts,
             last_ts, last["direction"], last["status"], last_agent))


def build_latency(conn):
    tr = {}
    for jk, at in conn.execute("SELECT join_key, transcribed_at FROM transcripts WHERE join_key<>''"):
        tr.setdefault(jk, at)
    jd = {}
    for jk, at in conn.execute("SELECT join_key, judged_at FROM verdicts WHERE join_key<>''"):
        jd.setdefault(jk, at)
    for jk, captured in conn.execute("SELECT join_key, captured_at_ist FROM calls WHERE join_key<>''"):
        t_call = captured
        t_tr = tr.get(jk, "")
        t_ju = jd.get(jk, "")
        p_call, p_tr, p_ju = parse_ts(t_call), parse_ts(t_tr), parse_ts(t_ju)
        lag_tx_call   = (p_tr - p_call).total_seconds() if p_call and p_tr else None
        lag_judge_tx  = (p_ju - p_tr).total_seconds() if p_tr and p_ju else None
        lag_judge_call = (p_ju - p_call).total_seconds() if p_call and p_ju else None
        conn.execute("INSERT INTO latency VALUES (?,?,?,?,?,?,?)",
                     (jk, t_call, t_tr, t_ju, lag_tx_call, lag_judge_tx, lag_judge_call))


def build_unjudged(conn):
    verdict_by_jk = {}
    for row in conn.execute("SELECT join_key,status,error,verdict FROM verdicts WHERE join_key<>''"):
        verdict_by_jk.setdefault(row[0], {"status": row[1], "error": row[2], "verdict": row[3]})
    for cid, jk, phone, fn in conn.execute(
            "SELECT id, join_key, phone10, recording_filename FROM calls"):
        v = verdict_by_jk.get(jk) if jk else None
        reason = unjudged_reason(bool(jk), bool((fn or "").strip()), v)
        if reason:
            conn.execute("INSERT INTO unjudged (join_key,phone10,reason) VALUES (?,?,?)",
                         (jk or "", phone or "", reason))


def reconcile_net_missed(conn):
    """Per-day net-missed by the ported Netting.gs rule (CFG.RESOLUTION_MUST_BE_AFTER
    =false): a phone is net-missed for a day iff it had >=1 INCOMING missed leg that
    day and NO connected leg that day (either direction). Compared to Daily_Summary.

    Daily_Summary is built from the MyOperator /search log; THIS is built from
    Call_Durations (our webhook). With the rule now aligned, the residual delta is
    our webhook's under-capture -- exactly what A2b (--with-myop-reconcile) surfaces.
    Daily_Summary stays authoritative (F-41: report, never fake agreement)."""
    day = {}
    for phone, direction, answered, ended, captured in conn.execute(
            "SELECT phone10, direction, answered, ended_at_ist, captured_at_ist "
            "FROM calls WHERE phone10<>''"):
        ts = parse_ts(ended) or parse_ts(captured)
        d = ts.date().isoformat() if ts else "UNKNOWN"
        st = day.setdefault(d, {}).setdefault(phone, {"in_miss": False, "conn": False})
        if answered == 1:
            st["conn"] = True
        elif answered == 0 and direction == "In":
            st["in_miss"] = True
    provisional = {d: sum(1 for s in phones.values() if s["in_miss"] and not s["conn"])
                   for d, phones in day.items()}
    ds = {}
    for d, nm in conn.execute("SELECT date, net_missed FROM daily_summary"):
        ds[(d or "").strip()] = (nm or "").strip()
    rows = []
    for d in sorted(set(provisional) | set(ds)):
        prov = provisional.get(d, 0)
        auth = ds.get(d, "")
        try:
            delta = prov - int(auth)
        except (ValueError, TypeError):
            delta = None
        rows.append((d, prov, auth, delta))
    return rows


def write_meta(conn, headers_by_tab, counts):
    def setk(k, v):
        conn.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (k, json.dumps(v) if not isinstance(v, str) else v))
    setk("built_at", datetime.now().isoformat(timespec="seconds"))
    setk("builder", "portal_console.py A1 (D297 Stage A)")
    setk("row_counts", counts)
    setk("source_headers", headers_by_tab)
    wm = conn.execute("SELECT MAX(ended_at_ist) FROM calls").fetchone()[0]
    setk("watermark_ended_at", wm or "")


# ---------------------------------------------------------------------------
# The one transform used by every mode: dict-per-tab -> populated console.db
# ---------------------------------------------------------------------------
def transform(conn, tabdata):
    """tabdata = {tab_name: (header_row, data_rows)}.  Builds the whole db."""
    create_schema(conn)
    headers_by_tab, dicts = {}, {}
    for tab, spec in TABS.items():
        header, data = tabdata.get(tab, ([], []))
        d, present = rows_to_dicts(header, data, spec, tab)
        dicts[tab] = d
        headers_by_tab[tab] = {"header": header, "resolved": present}

    rec_index = load_recordings(conn, dicts["Call_Recordings"])
    call_stats = load_calls(conn, dicts["Call_Durations"], rec_index)
    load_verdicts(conn, dicts["Call_Verdicts"])
    load_transcripts(conn, dicts["Call_Transcripts"])
    load_patients(conn, dicts["Patient_Master"])
    load_outbound(conn, dicts["Outbound_Log"])
    load_agents(conn, dicts["Agents"])
    load_daily_summary(conn, dicts["Daily_Summary"])

    build_conversations(conn)
    build_latency(conn)
    build_unjudged(conn)

    counts = {t: conn.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
              for t in ("calls", "verdicts", "recordings", "transcripts", "patients",
                        "outbound", "agents", "daily_summary", "conversations",
                        "latency", "unjudged")}
    counts["_call_stats"] = call_stats
    write_meta(conn, headers_by_tab, counts)
    conn.commit()
    return counts, headers_by_tab


# ---------------------------------------------------------------------------
# Live Sheets I/O (gspread imported lazily so --selftest needs no network)
# ---------------------------------------------------------------------------
def _read_env(env_path=None):
    paths = [env_path] if env_path else ENV_CANDIDATES
    env = {}
    for p in paths:
        if p and os.path.exists(p):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
            break
    return env


def _open_clients(env_path=None):
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        raise SystemExit("HALT: gspread/google-auth not available. On the VPS use "
                         "/root/wa/venv/bin/python3 (which has them).")
    env = _read_env(env_path)
    sa_path = ""
    for k in SA_ENV_KEYS:
        sa_path = os.environ.get(k) or env.get(k) or ""
        if sa_path:
            break
    if not sa_path or not os.path.exists(sa_path):
        raise SystemExit("HALT: service-account key not found via %s in %s "
                         "(value=%r). Cannot read Sheets." %
                         (SA_ENV_KEYS, env_path or ENV_CANDIDATES, sa_path))
    creds = Credentials.from_service_account_file(sa_path, scopes=READONLY_SCOPES)
    gc = gspread.authorize(creds)
    return {TRACKER: gc.open_by_key(TRACKER_SHEET_ID),
            AUDIT:   gc.open_by_key(AUDIT_SHEET_ID)}


def read_live_tabs(env_path=None):
    books = _open_clients(env_path)
    tabdata = {}
    for tab, spec in TABS.items():
        book = books[spec["sheet"]]
        try:
            ws = book.worksheet(tab)
        except Exception:
            raise SystemExit("HALT: tab '%s' not found in the %s sheet." % (tab, spec["sheet"]))
        values = ws.get_all_values()          # READ-ONLY
        if not values:
            tabdata[tab] = ([], [])
        else:
            tabdata[tab] = (values[0], values[1:])
    return tabdata


# ---------------------------------------------------------------------------
# MyOperator /search (A2b) -- read-only; ported verbatim from flag_investigator.py
# (JSON-body POST is the proven-working method on this account -- D172).
# ---------------------------------------------------------------------------
def _myop_token(env_path=None):
    tok = os.environ.get(MYOP_TOKEN_KEY, "").strip()
    if tok:
        return tok
    for p in ([env_path] if env_path else ENV_CANDIDATES):
        if p and os.path.exists(p):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(MYOP_TOKEN_KEY + "=") and "=" in line:
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def myop_search(token, from_unix, to_unix, log_from=0, page_size=MYOP_PAGE_SIZE):
    import urllib.request
    body = {"token": token, "from": str(from_unix), "to": str(to_unix),
            "log_from": str(log_from), "page_size": str(page_size)}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(MYOP_HOST + MYOP_SEARCH_PATH, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def myop_fetch_all(token, from_unix, to_unix):
    all_hits, log_from = [], 0
    for _ in range(MYOP_MAX_PAGES):
        data = myop_search(token, from_unix, to_unix, log_from, MYOP_PAGE_SIZE)
        hits = (((data or {}).get("data") or {}).get("hits")) or []
        all_hits.extend(hits)
        if len(hits) < MYOP_PAGE_SIZE:
            break
        log_from += MYOP_PAGE_SIZE
    return all_hits


def myop_day_bounds(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=IST)
    end = start + timedelta(days=1)
    return int(start.timestamp()), int(end.timestamp()) - 1


def cmd_myop_probe(days, env_path):
    """Read-only vocabulary probe: proves the /search status/event vocabulary
    before A2b-reconcile trusts any mapping (Netting.gs reads numeric status==2;
    flag_investigator.py reads string statuses -- they disagree; the artefact
    decides). Prints codes + counts only; numbers masked to last-4, no names."""
    import collections
    token = _myop_token(env_path)
    if not token:
        raise SystemExit("HALT: %s not found in env or .env (%s)."
                         % (MYOP_TOKEN_KEY, env_path or ENV_CANDIDATES))
    today = datetime.now(IST).date()
    start_date = (today - timedelta(days=max(1, days) - 1)).isoformat()
    from_unix, _ = myop_day_bounds(start_date)
    _, to_unix = myop_day_bounds(today.isoformat())
    print("D297 A2b -- MyOperator /search PROBE (read-only)  window %s..%s (%s day(s))"
          % (start_date, today.isoformat(), days))
    hits = myop_fetch_all(token, from_unix, to_unix)
    print("hits pulled: %s" % len(hits))
    if not hits:
        print("no hits in window -- widen with --days N")
        return 0
    src0 = (hits[0] or {}).get("_source") or {}
    print("_source keys: %s" % sorted(src0.keys()))
    for field in ("status", "call_status", "disposition", "event", "type",
                  "direction", "call_type", "call_direction"):
        c = collections.Counter()
        present = False
        for h in hits:
            s = (h or {}).get("_source") or {}
            if field in s:
                present = True
                c[str(s.get(field))] += 1
        if present:
            print("  field %-14s distinct: %s" % (field, dict(c)))
    print("-- 3 masked samples (status | event | dir | phone last4 | start_time) --")
    for h in hits[:3]:
        s = (h or {}).get("_source") or {}
        ph = norm_phone10(s.get("caller_number_raw") or s.get("caller_number") or "")
        print("  status=%s  event=%s  dir=%s  phone=****%s  start=%s"
              % (s.get("status"), s.get("event"),
                 s.get("direction") or s.get("type"), ph[-4:] if ph else "----",
                 s.get("start_time")))
    print("\nPROBE complete (nothing written). Paste the field-distinct lines back so "
          "the A2b reconcile mapping is proven against Daily_Summary, not guessed.")
    return 0


# ---------------------------------------------------------------------------
# A2b reconcile: mirror the GAS Netting reading of /search to reproduce
# Daily_Summary AND resolve our over-counted open list. Mapping LOCKED to the
# probed vocabulary: status "2"=missed / "1"=connected; event "2"=outgoing else
# incoming; day from start_time (unix, IST). Pure fns below are offline-tested.
# ---------------------------------------------------------------------------
def myop_is_incoming(src):
    return str(src.get("event")) != "2"          # event 1 = incoming, 2 = outgoing


def myop_is_missed(src):
    return str(src.get("status")) == "2"          # status 2 = no one answered


def myop_is_connected(src):
    return str(src.get("status")) == "1"          # status 1 = someone answered


def myop_phone(src):
    return norm_phone10(src.get("caller_number_raw") or src.get("caller_number") or "")


def myop_day(src):
    try:
        u = int(src.get("start_time") or 0)
    except (ValueError, TypeError):
        u = 0
    return datetime.fromtimestamp(u, IST).date().isoformat() if u else "UNKNOWN"


def myop_net_missed_by_day(sources):
    """Ported Netting rule on the MyOperator log (RESOLUTION_MUST_BE_AFTER=false):
    per day, a phone is net-missed iff >=1 incoming missed leg and no connected
    leg (either direction)."""
    day = {}
    for s in sources:
        ph = myop_phone(s)
        if not ph:
            continue
        st = day.setdefault(myop_day(s), {}).setdefault(ph, {"in_miss": False, "conn": False})
        if myop_is_connected(s):
            st["conn"] = True
        elif myop_is_incoming(s) and myop_is_missed(s):
            st["in_miss"] = True
    return {d: sum(1 for x in ph.values() if x["in_miss"] and not x["conn"])
            for d, ph in day.items()}


def myop_connected_phones(sources):
    return {myop_phone(s) for s in sources if myop_is_connected(s) and myop_phone(s)}


def apply_myop_correction(conn, connected_phones):
    """Resolve conversations we flagged net-missed-OPEN but MyOperator shows a
    connect for -> our webhook missed the connecting leg. Only ever REDUCES the
    open list (never inflates). Returns count corrected."""
    corrected = 0
    for (ph,) in conn.execute("SELECT phone10 FROM conversations WHERE net_missed_open=1").fetchall():
        if ph in connected_phones:
            conn.execute("UPDATE conversations SET net_missed_open=0, resolved_by='myop' "
                         "WHERE phone10=?", (ph,))
            corrected += 1
    return corrected


def myop_reconcile_layer(conn, token, days):
    today = datetime.now(IST).date()
    dates = [(today - timedelta(days=i)).isoformat() for i in range(max(1, days))][::-1]
    from_unix, _ = myop_day_bounds(dates[0])
    _, to_unix = myop_day_bounds(dates[-1])
    hits = myop_fetch_all(token, from_unix, to_unix)
    sources = [(h or {}).get("_source") or {} for h in hits]
    nm = myop_net_missed_by_day(sources)
    ds = {(d or "").strip(): (v or "").strip()
          for d, v in conn.execute("SELECT date, net_missed FROM daily_summary")}
    rows = []
    for d in sorted(nm):
        prov, auth = nm[d], ds.get(d, "")
        try:
            delta = prov - int(auth)
        except (ValueError, TypeError):
            delta = None
        rows.append((d, prov, auth, delta))
    before = conn.execute("SELECT COUNT(*) FROM conversations WHERE net_missed_open=1").fetchone()[0]
    corrected = apply_myop_correction(conn, myop_connected_phones(sources))
    conn.execute("DROP TABLE IF EXISTS myop_daily")
    conn.execute("CREATE TABLE myop_daily (date TEXT, myop_net_missed INTEGER, "
                 "daily_summary TEXT, delta INTEGER)")
    conn.executemany("INSERT INTO myop_daily VALUES (?,?,?,?)", rows)
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('myop_window', ?)",
                 (dates[0] + ".." + dates[-1],))
    conn.commit()
    return {"rows": rows, "hits": len(hits), "window": dates[0] + ".." + dates[-1],
            "before_open": before, "after_open": before - corrected, "corrected": corrected}


def _print_myop(res):
    print("\n-- A2b MyOperator /search reconcile  (window %s, %s hits) --"
          % (res["window"], res["hits"]))
    print("  %-12s %15s %15s %8s" % ("date", "myop_netmissed", "daily_summary", "delta"))
    for d, prov, auth, delta in res["rows"]:
        print("  %-12s %15s %15s %8s" % (d, prov, auth, "" if delta is None else delta))
    match = sum(1 for _, _, _, dl in res["rows"] if dl == 0)
    print("  days matching Daily_Summary: %s / %s  (proves the /search port)"
          % (match, len(res["rows"])))
    print("  net-missed-OPEN corrected by MyOperator connects: %s   (%s -> %s)"
          % (res["corrected"], res["before_open"], res["after_open"]))


def _require_myop_token(env_path):
    t = _myop_token(env_path)
    if not t:
        raise SystemExit("HALT: %s not found; cannot run --with-myop-reconcile." % MYOP_TOKEN_KEY)
    return t


# ---------------------------------------------------------------------------
# A3: transcript back-pull (Track T seed). Transcript TEXT lives in Drive as
# text/plain (call_transcription.py). We cache it in a PERSISTENT store
# (transcript_cache.db, survives full rebuilds) keyed by Join Key, then MERGE
# into console.db. Incremental: only Join Keys not yet cached are pulled.
# Drive READ-ONLY (get_media only; never create/delete -- owner rule). Cache
# holds patient speech -> F-31: never in repo/kit.
# ---------------------------------------------------------------------------
DEFAULT_CACHE       = "/root/wa/transcript_cache.db"
DEFAULT_DRIVE_TOKEN = "/root/wa/recordings-archive/drive_token.json"


def open_cache(cache_path):
    c = sqlite3.connect(cache_path)
    c.execute("CREATE TABLE IF NOT EXISTS t (join_key TEXT PRIMARY KEY, text TEXT, "
              "drive_file_id TEXT, cached_at TEXT)")
    c.commit()
    return c


def rows_needing_backpull(conn, cache_conn):
    cached = {r[0] for r in cache_conn.execute(
        "SELECT join_key FROM t WHERE text IS NOT NULL AND text<>''")}
    out = []
    for jk, fid in conn.execute(
            "SELECT join_key, drive_file_id FROM transcripts "
            "WHERE drive_file_id IS NOT NULL AND drive_file_id<>'' AND join_key<>''"):
        if jk not in cached:
            out.append((jk, fid))
    return out


def merge_transcript_cache(conn, cache_conn):
    filled = 0
    for jk, txt in cache_conn.execute("SELECT join_key, text FROM t WHERE text IS NOT NULL AND text<>''"):
        cur = conn.execute("UPDATE transcripts SET text=? WHERE join_key=? AND (text IS NULL OR text='')",
                           (txt, jk))
        filled += cur.rowcount if (cur.rowcount and cur.rowcount > 0) else 0
    conn.commit()
    return filled


def _drive_token_path(env_path=None):
    p = os.environ.get("DRIVE_TOKEN_FILE", "").strip()
    if p:
        return p
    for f in ([env_path] if env_path else ENV_CANDIDATES):
        if f and os.path.exists(f):
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("DRIVE_TOKEN_FILE=") and "=" in line:
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return DEFAULT_DRIVE_TOKEN


def get_drive_service(env_path=None):
    try:
        from google.oauth2.credentials import Credentials as UserCredentials
        from googleapiclient.discovery import build
    except ImportError:
        raise SystemExit("HALT: googleapiclient/google-auth not available. Use /root/wa/venv/bin/python3.")
    token_path = _drive_token_path(env_path)
    if not os.path.exists(token_path):
        raise SystemExit("HALT: DRIVE_TOKEN_FILE not found at %s (re-run get_drive_token.py on the "
                         "owner PC if revoked)." % token_path)
    creds = UserCredentials.from_authorized_user_file(token_path)
    return build("drive", "v3", credentials=creds)


def download_drive_text(service, file_id):
    from googleapiclient.http import MediaIoBaseDownload
    import io
    req = service.files().get_media(fileId=file_id)      # READ-ONLY
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue().decode("utf-8", "replace")


def transcript_backpull(conn, cache_conn, service, limit=None, sample_only=False):
    need = rows_needing_backpull(conn, cache_conn)
    if sample_only:                                        # PHI-safe probe: sizes only
        sampled = []
        for jk, fid in need[:(limit or 3)]:
            try:
                sampled.append((fid, len(download_drive_text(service, fid))))
            except Exception as e:
                sampled.append((fid, "ERR:" + type(e).__name__))
        return {"needing": len(need), "sampled": sampled, "pulled": 0, "errors": 0}
    batch = need if limit is None else need[:limit]
    pulled = errors = 0
    for i, (jk, fid) in enumerate(batch, 1):
        try:
            txt = download_drive_text(service, fid)
            cache_conn.execute("INSERT OR REPLACE INTO t VALUES (?,?,?,?)",
                               (jk, txt, fid, datetime.now().isoformat(timespec="seconds")))
            pulled += 1
        except Exception as e:
            errors += 1
            print("  [transcript] file %s error: %s" % (fid, type(e).__name__))
        if i % 50 == 0:
            cache_conn.commit()
            print("  [transcript] %s / %s pulled" % (i, len(batch)))
    cache_conn.commit()
    return {"needing": len(need), "pulled": pulled, "errors": errors, "sampled": []}


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def _print_summary(counts, headers_by_tab, reconcile, conn):
    print("\n-- header inventory (discovered by name; required cols resolved) --")
    for tab, info in headers_by_tab.items():
        print("  %-16s resolved=%s" % (tab, ",".join(info["resolved"]) or "(none)"))
        print("  %-16s live header = %s" % ("", info["header"]))
    cs = counts.get("_call_stats", {})
    print("\n-- row counts --")
    for t in ("calls", "verdicts", "recordings", "transcripts", "patients",
              "outbound", "agents", "daily_summary", "conversations", "latency", "unjudged"):
        print("  %-14s %s" % (t, counts.get(t)))
    print("\n-- calls detail --")
    print("  kept=%s  skipped_probe=%s  unknown_status=%s  matched_join_key=%s"
          % (cs.get("kept"), cs.get("skipped_probe"), cs.get("unknown_status"), cs.get("matched_jk")))
    if cs.get("kept"):
        print("  join-match rate = %.1f%%" % (100.0 * cs.get("matched_jk", 0) / cs["kept"]))
    nmo = conn.execute("SELECT COUNT(*) FROM conversations WHERE net_missed_open=1").fetchone()[0]
    print("  conversations net-missed-OPEN = %s" % nmo)
    ufr = conn.execute("SELECT reason, COUNT(*) FROM unjudged GROUP BY reason ORDER BY 2 DESC")
    print("\n-- reasons-not-judged --")
    for reason, n in ufr:
        print("  %-32s %s" % (reason, n))
    print("\n-- net-missed reconcile  (Netting rule on Call_Durations  vs  Daily_Summary[MyOperator]) --")
    print("  %-12s %12s %16s %8s" % ("date", "from_calls", "daily_summary", "delta"))
    shown = [r for r in reconcile if r[0] != "UNKNOWN"][-14:]
    for d, prov, auth, delta in shown:
        print("  %-12s %12s %16s %8s" % (d, prov, auth, "" if delta is None else delta))
    mism = sum(1 for _, _, _, dl in reconcile if dl not in (0, None))
    print("  days with non-zero delta = %s  (residual = webhook under-capture -> A2b; "
          "Daily_Summary stays authoritative)" % mism)


def cmd_dry_run(env_path, with_myop=False, days=3, with_tr=False, tr_limit=None, cache_path=DEFAULT_CACHE):
    print("D297 Stage A -- DRY RUN (read-only; NO Sheet writes; console.db NOT written)")
    tabdata = read_live_tabs(env_path)
    conn = sqlite3.connect(":memory:")
    counts, headers = transform(conn, tabdata)
    reconcile = reconcile_net_missed(conn)
    _print_summary(counts, headers, reconcile, conn)
    if with_myop:
        _print_myop(myop_reconcile_layer(conn, _require_myop_token(env_path), days))
    if with_tr:
        cache_conn = open_cache(cache_path if os.path.exists(cache_path) else ":memory:")
        res = transcript_backpull(conn, cache_conn, get_drive_service(env_path),
                                  limit=tr_limit, sample_only=True)
        cache_conn.close()
        print("\n-- A3 transcript back-pull PROBE (read-only; nothing cached) --")
        print("  transcripts needing back-pull: %s" % res["needing"])
        for fid, info in res["sampled"]:
            print("  sample %s -> %s" % (fid, ("%s chars" % info) if isinstance(info, int) else info))
        print("  (transcript text NOT shown -- PHI; probe only confirms the download works)")
    print("\nDRY RUN complete. Nothing was written. Reconcile the deltas above "
          "before --build.")
    conn.close()
    return 0


def cmd_build(env_path, db_path, with_myop=False, days=3, with_tr=False, tr_limit=None, cache_path=DEFAULT_CACHE):
    print("D297 Stage A -- BUILD -> %s" % db_path)
    tabdata = read_live_tabs(env_path)
    tmp = db_path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    conn = sqlite3.connect(tmp)
    counts, headers = transform(conn, tabdata)
    reconcile = reconcile_net_missed(conn)
    _print_summary(counts, headers, reconcile, conn)
    if with_myop:
        _print_myop(myop_reconcile_layer(conn, _require_myop_token(env_path), days))
    # A3: back-pull new transcripts (if requested), then merge cached text in
    if with_tr or os.path.exists(cache_path):
        cache_conn = open_cache(cache_path)
        if with_tr:
            res = transcript_backpull(conn, cache_conn, get_drive_service(env_path), limit=tr_limit)
            print("-- A3 transcript back-pull: needing=%s pulled=%s errors=%s --"
                  % (res["needing"], res["pulled"], res["errors"]))
        filled = merge_transcript_cache(conn, cache_conn)
        cache_conn.close()
        print("-- A3 transcripts merged from cache: %s row(s) now carry text --" % filled)
    conn.close()
    os.replace(tmp, db_path)               # atomic; readers never see a half-built db
    print("\nBUILD complete. console.db written atomically at %s" % db_path)
    return 0


# ---------------------------------------------------------------------------
# Selftest -- synthetic fixtures through the real transform path
# ---------------------------------------------------------------------------
def _fixtures():
    # Synthetic (non-real) phones. Header order shuffled + a junk column to prove
    # name-based discovery. Days chosen so per-day net-missed reconciles exactly.
    P_ANS        = "9000000001"  # D0 incoming bridged, rec R1 -> JK_A
    P_OBD        = "9000000003"  # D0 obd bridged, rec R2 -> JK_B (NOT FILED verdict)
    P_OPEN2      = "9000000010"  # D1 two incoming misses, no connect -> OPEN, 2 attempts
    P_RES_IN     = "9000000011"  # D1 incoming miss + incoming bridged -> RESOLVED
    P_MISS_NOREC = "9000000002"  # D1 incoming miss, no rec -> OPEN + 'no recording'
    P_RES_OUT    = "9000000012"  # D2 incoming miss + obd bridged -> RESOLVED (either dir)
    P_OBDMISS    = "9000000013"  # D2 obd miss only, NO incoming miss -> NOT a candidate
    P_UNMATCHED  = "9000000004"  # D2 incoming miss, rec R3 unmatched -> OPEN + 'no join key'
    JK_A = P_ANS + "_1700000001"
    JK_B = P_OBD + "_1700000002"
    D0, D1, D2 = "2026-07-09", "2026-07-10", "2026-07-11"
    return {
        "Call_Durations": (
            ["junk", "phone10", "category", "status", "recording_filename",
             "captured_at_ist", "ended_at_ist", "session_id"],
            [
                ["x", P_ANS,        "incoming", "bridged", "R1", D0 + " 10:00:00", D0 + " 10:01:00", "s1"],
                ["x", P_OBD,        "obd",      "bridged", "R2", D0 + " 11:00:00", D0 + " 11:02:00", "s2"],
                ["x", "0000000000", "incoming", "probe",   "",   D0 + " 09:00:00", D0 + " 09:00:00", "s3"],
                ["x", P_OPEN2,      "incoming", "missed",  "",   D1 + " 10:00:00", D1 + " 10:00:00", "s4"],
                ["x", P_OPEN2,      "incoming", "missed",  "",   D1 + " 10:30:00", D1 + " 10:30:00", "s5"],
                ["x", P_RES_IN,     "incoming", "missed",  "",   D1 + " 11:00:00", D1 + " 11:00:00", "s6"],
                ["x", P_RES_IN,     "incoming", "bridged", "",   D1 + " 11:05:00", D1 + " 11:06:00", "s7"],
                ["x", P_MISS_NOREC, "incoming", "missed",  "",   D1 + " 12:00:00", D1 + " 12:00:00", "s8"],
                ["x", P_RES_OUT,    "incoming", "missed",  "",   D2 + " 09:00:00", D2 + " 09:00:00", "s9"],
                ["x", P_RES_OUT,    "obd",      "bridged", "",   D2 + " 09:30:00", D2 + " 09:31:00", "s10"],
                ["x", P_OBDMISS,    "obd",      "missed",  "",   D2 + " 14:00:00", D2 + " 14:00:00", "s11"],
                ["x", P_UNMATCHED,  "incoming", "missed",  "R3", D2 + " 15:00:00", D2 + " 15:00:00", "s12"],
            ],
        ),
        "Call_Recordings": (
            ["MyOperator Filename", "Join Key"],
            [["R1", JK_A], ["R2", JK_B]],   # R3 intentionally absent (unmatched)
        ),
        "Call_Verdicts": (
            ["Join Key", "Agent", "Claimed Outcome", "Verdict", "Status", "Judged At", "Patient Name"],
            [
                [JK_A, "Shavez", "k_coming", "TRUE", "done", D0 + " 10:10:00", "AAA"],
                [JK_B, "Alisha", "",         "",     "done", D0 + " 11:20:00", "BBB"],  # NOT FILED + judge pending
            ],
        ),
        "Call_Transcripts": (
            ["Join Key", "Transcribed At", "Transcript Drive File ID"],
            [[JK_A, D0 + " 10:05:00", "DFID_A"]],
        ),
        "Patient_Master": (["Mobile", "Patient Name", "Diagnosis"], [[P_ANS, "AAA", "Knee OA"]]),
        "Outbound_Log": (
            ["Date", "Time", "Phone10", "Agent", "Duration_s", "Status", "Start_Unix"],
            [[D2, "09:30", P_RES_OUT, "Alisha", "60", "bridged", "1700000099"]],
        ),
        "Agents": (["Ext", "Name", "UserId", "Active"], [["10", "Manoj", "u10", "TRUE"]]),
        "Daily_Summary": (
            ["Date", "Total Calls", "Incoming", "Net-Missed", "Resolved", "Net-Missed %"],
            [[D0, "2", "1", "0", "0", "0%"],
             [D1, "5", "4", "2", "1", "x"],
             [D2, "4", "2", "1", "1", "x"]],
        ),
    }, {"JK_A": JK_A, "JK_B": JK_B, "P_OPEN2": P_OPEN2, "P_RES_IN": P_RES_IN,
        "P_RES_OUT": P_RES_OUT, "P_OBDMISS": P_OBDMISS, "P_MISS_NOREC": P_MISS_NOREC,
        "P_UNMATCHED": P_UNMATCHED, "D0": D0, "D1": D1, "D2": D2}


def cmd_selftest():
    fx, k = _fixtures()
    conn = sqlite3.connect(":memory:")
    counts, headers = transform(conn, fx)
    reconcile = reconcile_net_missed(conn)
    fails, total = [], [0]

    def check(name, cond):
        total[0] += 1
        print("  [%s] %s" % ("PASS" if cond else "FAIL", name))
        if not cond:
            fails.append(name)

    def scalar(sql, args=()):
        return conn.execute(sql, args).fetchone()[0]

    def recon(date):
        return next((x for x in reconcile if x[0] == date), None)

    print("D297 Stage A -- SELFTEST")
    check("probe excluded from spine (11 calls kept of 12)", counts["calls"] == 11)
    check("direction incoming->In", scalar("SELECT direction FROM calls WHERE session_id='s1'") == "In")
    check("direction obd->Out", scalar("SELECT direction FROM calls WHERE session_id='s2'") == "Out")
    check("answered: bridged->1", scalar("SELECT answered FROM calls WHERE session_id='s1'") == 1)
    check("answered: missed->0", scalar("SELECT answered FROM calls WHERE session_id='s4'") == 0)
    check("join_key attached via recordings bridge",
          scalar("SELECT join_key FROM calls WHERE session_id='s1'") == k["JK_A"])
    check("no recording -> join_key NULL",
          scalar("SELECT join_key FROM calls WHERE session_id='s4'") in (None, ""))
    check("recording present but unmatched -> join_key NULL",
          scalar("SELECT join_key FROM calls WHERE session_id='s12'") in (None, ""))
    check("NOT FILED derived (blank Claimed Outcome)",
          scalar("SELECT not_filed FROM verdicts WHERE join_key=?", (k["JK_B"],)) == 1)
    check("filed verdict not flagged NOT FILED",
          scalar("SELECT not_filed FROM verdicts WHERE join_key=?", (k["JK_A"],)) == 0)
    # --- ported Netting.gs net-missed rule ---
    check("net-missed OPEN: two incoming misses, no connect",
          scalar("SELECT net_missed_open FROM conversations WHERE phone10=?", (k["P_OPEN2"],)) == 1)
    check("net-missed miss_attempts counted (2)",
          scalar("SELECT miss_attempts FROM conversations WHERE phone10=?", (k["P_OPEN2"],)) == 2)
    check("RESOLVED by incoming connect (same direction)",
          scalar("SELECT net_missed_open FROM conversations WHERE phone10=?", (k["P_RES_IN"],)) == 0)
    check("RESOLVED by OUTBOUND connect (either direction)",
          scalar("SELECT net_missed_open FROM conversations WHERE phone10=?", (k["P_RES_OUT"],)) == 0)
    check("outbound-miss-only is NOT a net-missed candidate",
          scalar("SELECT net_missed_open FROM conversations WHERE phone10=?", (k["P_OBDMISS"],)) == 0)
    check("net-missed OPEN: incoming miss with no recording",
          scalar("SELECT net_missed_open FROM conversations WHERE phone10=?", (k["P_MISS_NOREC"],)) == 1)
    check("total net-missed-OPEN conversations = 3",
          scalar("SELECT COUNT(*) FROM conversations WHERE net_missed_open=1") == 3)
    check("latency lags computed for JK_A (>=0)",
          (scalar("SELECT lag_judge_call FROM latency WHERE join_key=?", (k["JK_A"],)) or -1) >= 0)
    check("unjudged: no-recording reason present",
          scalar("SELECT COUNT(*) FROM unjudged WHERE phone10=? AND reason='no recording'",
                 (k["P_MISS_NOREC"],)) == 1)
    check("unjudged: unmatched-recording reason present",
          scalar("SELECT COUNT(*) FROM unjudged WHERE phone10=? AND reason LIKE 'no join key%'",
                 (k["P_UNMATCHED"],)) == 1)
    check("unjudged: judge-pending reason for blank verdict",
          scalar("SELECT COUNT(*) FROM unjudged WHERE join_key=? AND reason='judge pending'",
                 (k["JK_B"],)) == 1)
    r0, r1, r2 = recon(k["D0"]), recon(k["D1"]), recon(k["D2"])
    check("reconcile D0 net-missed = 0, delta 0", r0 is not None and r0[1] == 0 and r0[3] == 0)
    check("reconcile D1 net-missed = 2, delta 0 (matches Daily_Summary)",
          r1 is not None and r1[1] == 2 and r1[3] == 0)
    check("reconcile D2 net-missed = 1, delta 0 (outbound-miss NOT counted)",
          r2 is not None and r2[1] == 1 and r2[3] == 0)
    check("meta watermark set", bool(scalar("SELECT v FROM meta WHERE k='watermark_ended_at'")))
    check("header discovery ignored junk column",
          "junk" not in headers["Call_Durations"]["resolved"])

    # --- A2b: MyOperator /search classification + net-missed + over-count fix ---
    def ist_unix(dt_str):
        return int(datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=IST).timestamp())
    D = k["D1"]
    myop_hits = [
        {"event": "1", "status": "2", "caller_number_raw": "919000000020", "start_time": ist_unix(D + " 10:00")},
        {"event": "1", "status": "2", "caller_number_raw": "919000000020", "start_time": ist_unix(D + " 10:30")},
        {"event": "1", "status": "2", "caller_number_raw": "919000000021", "start_time": ist_unix(D + " 11:00")},
        {"event": "2", "status": "1", "caller_number_raw": "919000000021", "start_time": ist_unix(D + " 11:05")},
        {"event": "1", "status": "1", "caller_number_raw": "919000000022", "start_time": ist_unix(D + " 12:00")},
        {"event": "2", "status": "2", "caller_number_raw": "919000000023", "start_time": ist_unix(D + " 13:00")},
        {"event": "2", "status": "1", "caller_number_raw": "91" + k["P_OPEN2"], "start_time": ist_unix(D + " 18:00")},
    ]
    check("myop: event 1 incoming, event 2 outgoing",
          myop_is_incoming(myop_hits[0]) and not myop_is_incoming(myop_hits[3]))
    check("myop: status 2 missed, status 1 connected",
          myop_is_missed(myop_hits[0]) and myop_is_connected(myop_hits[3]))
    check("myop net-missed by day = 1 (021 resolved by outbound, 023 not incoming)",
          sum(myop_net_missed_by_day(myop_hits).values()) == 1)
    check("myop connected phones = {021, 022, P_OPEN2}",
          myop_connected_phones(myop_hits) == {"9000000021", "9000000022", k["P_OPEN2"]})
    open_before = scalar("SELECT COUNT(*) FROM conversations WHERE net_missed_open=1")
    corrected = apply_myop_correction(conn, myop_connected_phones(myop_hits))
    check("myop correction resolves P_OPEN2 (webhook missed the connect)",
          corrected == 1
          and scalar("SELECT net_missed_open FROM conversations WHERE phone10=?", (k["P_OPEN2"],)) == 0
          and scalar("SELECT resolved_by FROM conversations WHERE phone10=?", (k["P_OPEN2"],)) == "myop")
    check("myop correction only reduces the open list (3 -> 2)",
          open_before == 3 and scalar("SELECT COUNT(*) FROM conversations WHERE net_missed_open=1") == 2)

    # --- A3: transcript back-pull selection + cache merge (offline) ---
    tcache = sqlite3.connect(":memory:")
    tcache.execute("CREATE TABLE t (join_key TEXT PRIMARY KEY, text TEXT, "
                   "drive_file_id TEXT, cached_at TEXT)")
    check("A3: 1 transcript needs back-pull (JK_A has a Drive file id, uncached)",
          rows_needing_backpull(conn, tcache) == [(k["JK_A"], "DFID_A")])
    tcache.execute("INSERT INTO t VALUES (?,?,?,?)", (k["JK_A"], "hello transcript text", "DFID_A", "t"))
    check("A3: once cached, nothing left needing back-pull",
          rows_needing_backpull(conn, tcache) == [])
    check("A3: merge fills console.db transcript text from cache",
          merge_transcript_cache(conn, tcache) == 1
          and scalar("SELECT text FROM transcripts WHERE join_key=?", (k["JK_A"],)) == "hello transcript text")
    tcache.close()

    conn.close()
    print("\nSELFTEST %s (%d checks, %d failed)"
          % ("PASSED" if not fails else "FAILED", total[0], len(fails)))
    return 0 if not fails else 1


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="D297 Call-Intelligence Console -- Stage A builder (A1)")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--selftest", action="store_true", help="offline synthetic self-test")
    mode.add_argument("--dry-run", action="store_true", help="read live sheets, write nothing")
    mode.add_argument("--build", action="store_true", help="build console.db from live sheets")
    mode.add_argument("--myop-probe", action="store_true",
                      help="A2b: read-only MyOperator /search vocabulary probe")
    ap.add_argument("--db", default=DEFAULT_DB, help="console.db path (default %s)" % DEFAULT_DB)
    ap.add_argument("--days", type=int, default=3, help="probe window in days (default 3)")
    ap.add_argument("--transcripts-limit", type=int, default=None,
                    help="A3: cap transcript back-pull per run (default: all)")
    ap.add_argument("--cache", default=DEFAULT_CACHE,
                    help="A3 transcript cache path (default %s)" % DEFAULT_CACHE)
    ap.add_argument("--env", default=None, help="override .env path")
    ap.add_argument("--with-myop-reconcile", action="store_true",
                    help="A2b: reconcile net-missed vs the MyOperator /search log + correct the open list")
    ap.add_argument("--with-transcripts", action="store_true",
                    help="A3: back-pull Drive transcripts into the cache (build) / PHI-safe probe (dry-run)")
    args = ap.parse_args(argv)


    if args.myop_probe:
        return cmd_myop_probe(args.days, args.env)
    if args.selftest:
        return cmd_selftest()
    if args.dry_run:
        return cmd_dry_run(args.env, args.with_myop_reconcile, args.days,
                           args.with_transcripts, args.transcripts_limit, args.cache)
    if args.build:
        return cmd_build(args.env, args.db, args.with_myop_reconcile, args.days,
                         args.with_transcripts, args.transcripts_limit, args.cache)
    return 2


if __name__ == "__main__":
    sys.exit(main())
