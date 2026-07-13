#!/usr/bin/env python3
"""
call_verdict.py — Stage 3 of the Staff Call Audit project: the AI judge.
Dr. Manoj Agarwal Clinic, Bareilly. Session 128. Decision D149 (design locked
Sessions 122-127; D62 is the parent decision from Session 24).

UPDATED Session 141 (12 Jul 2026, v2.1) — F-39 WRITE FIX:
  Sheets' append "table detection" was landing EVERY new verdict on top
  of row 61 instead of below the data — each write erased the previous
  one, and ~500 judged rows were silently lost on 12-Jul. New rows now
  go to an EXPLICIT computed row; the header write is explicit too; and
  PROMPT_VERSION is finally bumped (v2 rows were mislabelled v1.0-S128).

UPDATED Session 140 (12 Jul 2026) — the K-era claim vocabulary:
  K-1/K-2 one-tap buttons (Dashboard v18.28) write NEW claim codes into
  Followup_Outcomes: `k_coming` / `k_not_coming` / `k_call_again` (source=K),
  `no_answer` (button 4 + the old snooze path), and incoming codes prefixed
  `in_` (e.g. `in_appointment_booked`). The AI's answer vocabulary is
  UNCHANGED (frozen S125-126) — only the COMPARISON now normalises staff
  claims and understands the K buttons' "what next" meaning groups
  (Console Spec §K.6.1: the AI says what HAPPENED; the buttons say what
  NEXT — exact equality is impossible by design for three of them).

WHAT THIS DOES
  Runs after Stage 2 (call_transcription.py, 03:00 IST). Reads the
  "Call_Transcripts" tab of the Clinic Callback Tracker, finds transcribed
  calls (Status=done) that don't yet have a verdict, downloads each call's
  transcript text from the restricted Drive folder, sends the TRANSCRIPT ONLY
  to Claude Haiku with a fixed classification prompt, receives a structured
  verdict, then SEPARATELY matches the staff's claimed outcome from
  "Followup_Outcomes" and mechanically compares:
  Match / Mismatch / Partial / Unclear / No claim logged. One row per call is
  written to a "Call_Verdicts" tab in the DOCTOR-ONLY "Call Audit" sheet.

SESSION 123 REDESIGN (this version)
  1. CLAIM JOIN — the old ±45-min window matched 0/15 real calls because
     staff file outcomes in MORNING BATCHES, hours after the call. The join
     now pairs on the patient's phone number over a whole-day forward window
     (call time -> next-morning batch); two calls to one number pair in
     call-time order; each row gets a Match Confidence (unique/ordered/none).
  2. ENRICHED ROW — full patient number, a Recording Link (joined from the
     Stage-1 Call_Recordings tab), Match Confidence, and a name/Clinic-ID
     fallback so even an unmatched call carries an identity (training KB).
  3. JUDGE ONCE, FILL LATER — a call is sent to the AI only once. When the
     staff's outcome lands later, the row's claim/verdict cells are UPDATED
     in place (no second AI call). The doctor's own columns are never touched.
     This lets the AI verdict + flags reach the doctor the SAME day while the
     staff-vs-AI diff fills itself in whenever the claim is filed.

  This is Stage 3 of 4 (recording archive -> transcription -> AI verdict ->
  dashboard UI). v1 is CLASSIFY-AND-FLAG ONLY: it never sends messages, never
  books anything, never edits any other table, and triggers no actions.

THE BLIND-JUDGE RULE (D62 — the heart of the design)
  The AI is NEVER shown the staff's claimed outcome, the patient's name,
  mobile number, Clinic ID, or the agent's name. It sees only: transcript
  text + call direction + talk-seconds. It must form its own independent
  opinion. The Match/Mismatch comparison happens in Python AFTERWARDS.
  This kills anchoring bias and doubles as a privacy measure: no patient
  identifiers travel to the AI service.

ANSWER VOCABULARY (frozen from the LIVE dashboard, Session 125-126)
  Outgoing follow-up calls -> the 11 FU_OUTCOMES codes staff actually pick
  from. Incoming calls -> the union of IN_RESOLUTIONS + IN_NEW_OUTCOMES.
  Plus UNCLEAR always. The judge answers in the staff's own language so the
  comparison is apples-to-apples. If the dashboard dropdowns ever change,
  the lists below must change with them (single place: VOCAB_* constants).

SIX FLAGS (second lane, Sessions 126-127; conduct flag owner-approved S126)
  postop / complaint / urgent / surgery / clinical_question / conduct.
  Any flag TRUE -> mandatory doctor review regardless of Match status.
  Flags never settle anything; they only raise attention.

TRANSCRIPTS ARE UNDIARISED (owner decision "a", Session 127)
  Stage 2 produces one undivided block of text (no speaker labels). The
  prompt tells the judge this and instructs it to infer speakers cautiously
  and answer UNCLEAR when it genuinely can't tell who said what. During
  calibration we measure how often this costs us a verdict; that number
  justifies (or not) a later Stage-2 diarization upgrade.

WHERE THINGS LIVE (verified Session 128 — evidence over notes)
  READ : Call_Transcripts  -> Clinic Callback Tracker (Stage 2's default;
                              the planned move to the doctor-only sheet never
                              happened — confirmed by the doctor-only sheet's
                              untouched-since-creation timestamp).
  READ : Followup_Outcomes -> Clinic Callback Tracker (WebApp.gs is its only
                              writer; incoming outcomes land here too with
                              Source='incoming', so ALL calls are comparable).
  WRITE: Call_Verdicts     -> "Call Audit (Doctor Only)" sheet. THIS script
                              is its ONLY writer (one-writer-per-table, D37
                              pattern). Doctor Flag / Doctor Note / Final
                              Outcome columns are the doctor's to fill by
                              hand; this script never touches a written row.

FAILURE MAP (per D19 — for the future Diagnostics.gs to consume)
  - ANTHROPIC_API_KEY / GOOGLE_SA_KEY / DRIVE_TOKEN_FILE missing -> exits 2
    before touching anything. Safe to re-run once fixed.
  - Call_Transcripts unreachable/empty -> exits 5. Nothing processed.
  - Followup_Outcomes unreadable -> WARN and continue; every verdict this
    run gets Claimed Outcome blank -> "No claim logged" (never a false
    Mismatch). Better a comparison gap than a stalled pipeline.
  - Drive download fails for ONE call -> FAILED row for that call (retried
    next run), continue with the rest.
  - AI call fails / returns unparseable JSON for ONE call -> same: FAILED
    row, continue. The raw error (never the transcript) goes in the Error
    column, truncated.
  - Doctor-only sheet unreachable mid-run -> exits 5. Rows already written
    are NOT lost (written one at a time, immediately after each verdict).
    A re-run resumes exactly where this left off via the done-key check.
  RESUMABILITY: a call counts as "already judged" only if its Call_Verdicts
  row has Status=done. FAILED rows are retried automatically on the next
  run — there is no separate retry command.

PRIVACY RULES BAKED IN
  - No patient identifier is ever sent to the AI (see blind-judge rule).
  - Transcript text NEVER appears in stdout, logs, or the Error column.
  - Phone numbers print masked (last-4 only), same mask() as Stage 1/2.
  - The verdict row carries a LINK to the transcript, never its text.

CONFIG (environment variables — read from /root/wa/.env, same loader
pattern as call_recording_archive.py / call_transcription.py)
  ANTHROPIC_API_KEY   (required, NEW)  console.anthropic.com key. Add to
                                       /root/wa/.env before first real run.
  GOOGLE_SA_KEY       (required)       same service-account JSON path the
                                       other stages use. Falls back to
                                       WA_SA_KEY. Sheets access only.
  DRIVE_TOKEN_FILE    (required)       same drive_token.json (owner-OAuth,
                                       D36) — used to DOWNLOAD transcript
                                       .txt files from the restricted folder.
  TRACKER_SHEET_ID    (optional)       Clinic Callback Tracker id. Falls
                                       back to the known clinic sheet id.
                                       (Deliberately NOT reusing the bare
                                       SHEET_ID name so this script can
                                       never be silently re-pointed by an
                                       env line meant for another stage.)
  AUDIT_SHEET_ID      (optional)       "Call Audit (Doctor Only)" sheet id.
                                       Falls back to the known id.
  AI_JUDGE_MODEL      (optional)       default "claude-haiku-4-5". One-line
                                       switch per the S123 isolation rule.

RUN
  Offline logic test, no network, no key needed:
    python call_verdict.py --selftest            (clinic PC / sandbox)
  Preview against real data, judges but WRITES NOTHING:
    /root/wa/venv/bin/python3 call_verdict.py --date 2026-07-06 --dry-run --limit 3
  Real run (writes Call_Verdicts rows):
    /root/wa/venv/bin/python3 call_verdict.py --date 2026-07-06
  No systemd timer yet — that is a later step, after the owner has reviewed
  a real judged day (calibration model, Sessions 126-127).

DEPENDENCIES: gspread, google-auth, google-api-python-client (already in the
venv from Stages 1-2) and requests (a gspread dependency — already present).
Nothing new to install.
"""

import argparse
import datetime
import io
import json
import os
import re
import sys
import tempfile
import time

# Imports that need the venv are deferred so --selftest runs anywhere
# (clinic PC py_compile box, sandbox) with zero third-party packages.
gspread = None            # populated in main()
Credentials = None
UserCredentials = None
build = None
MediaIoBaseDownload = None
requests = None

PROMPT_VERSION = "v2.1-S141"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ENV_PATH = "/root/wa/.env"

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

DEFAULT_TRACKER_SHEET_ID = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"
DEFAULT_AUDIT_SHEET_ID = "1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ"

TRANSCRIPT_TAB = "Call_Transcripts"
OUTCOMES_TAB = "Followup_Outcomes"
VERDICT_TAB = "Call_Verdicts"

DEFAULT_MODEL = "claude-haiku-4-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MAX_TRANSCRIPT_CHARS = 12000     # defensive cap; longest clinic calls are minutes, not hours
AI_MAX_TOKENS = 700
AI_TIMEOUT_S = 120
AI_RETRIES = 2                   # per call, on transport/5xx errors

# --- Claim-matching window (REDESIGNED Session 123) ------------------------
# The old ±45-min window assumed staff file an outcome right after hanging up.
# They DON'T — they clear outcomes in morning batches, so a filed outcome
# usually lands MANY HOURS after its call (which is why the first real run
# matched 0/15). New rule: match on the patient's PHONE NUMBER, accepting an
# outcome filed from just before the call through to the next morning's batch.
# Calls can't leak past ~01:00 (Stage-1 downloads at 02:00), so a call and its
# outcome can never be confused with the NEXT day's calls. Earliest-unclaimed
# -in-window wins; two calls to one number are paired in call-time order.
CLAIM_SKEW_BEFORE_S = 10 * 60          # 10 min before the call (clock-skew safety)
CLAIM_MAX_FORWARD_S = 28 * 3600        # forward to the next-morning batch filing

# Recording link (Session 123): joined from the Stage-1 Call_Recordings tab.
RECORD_TAB = "Call_Recordings"
DRIVE_FILE_VIEW = "https://drive.google.com/file/d/{}/view"

# --- Answer vocabularies: frozen from the LIVE dashboard (S125-126) --------
VOCAB_OUTGOING = [
    "coming", "out_of_town", "on_medication", "cant_communicate",
    "dikha_chuke", "problem", "close_followup", "not_interested",
    "treatment_elsewhere", "wrong_number", "asked_not_to_call",
]
VOCAB_INCOMING = [
    "resolved_on_call", "appointment_booked", "info_given_will_act",
    "needs_callback", "escalated", "cant_communicate",
    "will_come", "enquiry_only", "no_action",
]
UNCLEAR = "UNCLEAR"

VOCAB_MEANINGS = {
    # outgoing follow-up codes
    "coming":              "patient says they will come / visit the clinic",
    "out_of_town":         "patient is out of town / travelling",
    "on_medication":       "patient is continuing medicines, will come later",
    "cant_communicate":    "call connected but no meaningful conversation possible",
    "dikha_chuke":         "patient says they ALREADY visited / already shown (dikha chuke)",
    "problem":             "patient reports a problem / needs attention",
    "close_followup":      "treatment complete, follow-up can be closed",
    "not_interested":      "patient clearly not interested in returning",
    "treatment_elsewhere": "patient is taking treatment somewhere else",
    "wrong_number":        "the person reached is not the patient / wrong number",
    "asked_not_to_call":   "the person asked the clinic to stop calling",
    # incoming codes
    "resolved_on_call":    "caller's question fully answered on this call",
    "appointment_booked":  "an appointment was clearly CONFIRMED on the call (date/time agreed or staff said it is noted)",
    "info_given_will_act": "information given; caller will act on it",
    "needs_callback":      "someone must call back; the matter is not finished",
    "escalated":           "the matter needs the doctor personally",
    "will_come":           "caller says they will come / considering visiting (NOT a confirmed booking)",
    "enquiry_only":        "general enquiry only (timings, address, fee, availability)",
    "no_action":           "no action needed / not relevant to patient care",
}

# Verdict softening: these pairs count as Partial, not Mismatch.
PARTIAL_PAIRS = {
    frozenset(("dikha_chuke", "close_followup")),
    frozenset(("not_interested", "treatment_elsewhere")),
    frozenset(("appointment_booked", "will_come")),
    frozenset(("resolved_on_call", "info_given_will_act")),
    frozenset(("enquiry_only", "info_given_will_act")),
    frozenset(("enquiry_only", "resolved_on_call")),
}

# --- S140: staff-claim normalisation (K-1/K-2 one-tap codes) ---------------
# `in_` prefix (saveIncomingOutcome) maps 1:1 onto VOCAB_INCOMING once
# stripped. `k_coming` is the button spelling of `coming`. The remaining
# K codes are "what next" statements, compared through meaning GROUPS.
CLAIM_ALIAS = {"k_coming": "coming"}

def normalise_claim(code):
    c = "".join(ch if (ch.isalnum() or ch == "_") else "_"
                for ch in str(code or "").strip().lower())
    if c.startswith("in_"):
        c = c[3:]
    return CLAIM_ALIAS.get(c, c)

# claim -> AI outcomes that COUNT AS A MATCH (both directions, because K-2
# puts the same buttons on incoming calls for known patients)
CLAIM_EQUIV = {
    "k_not_coming": {"not_interested", "treatment_elsewhere",
                     "close_followup", "no_action"},
    "k_call_again": {"on_medication", "out_of_town", "needs_callback"},
    "no_answer":    {"cant_communicate"},
    "problem":      {"escalated"},
}
# claim -> AI outcomes that count as PARTIAL (softened, still shown)
CLAIM_PARTIAL = {
    "k_call_again": {"coming", "will_come"},
}

FLAG_KEYS = ["flag_postop", "flag_complaint", "flag_urgent",
             "flag_surgery", "flag_clinical", "flag_conduct"]

VERDICT_HEADER = [
    "Date", "Time", "Direction", "Patient Number", "Agent",
    "Patient Name", "Clinic ID", "Duration",
    "Claimed Outcome", "AI Outcome", "Verdict", "Match Confidence",
    "Outcome TRUE/FALSE",
    "AI Reason", "Evidence", "Spoke With", "Confidence",
    "Flag PostOp", "Flag Complaint", "Flag Urgent",
    "Flag Surgery", "Flag Clinical", "Flag Conduct", "Conduct Note",
    "Recording Link", "Transcript Link", "Join Key", "Status", "Error",
    "Judged At", "Prompt Ver", "Model",
    "Doctor Flag", "Doctor Note", "Final Outcome",
]


# ---------------------------------------------------------------------------
# .env loader — same pattern as the other stages
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


# ---------------------------------------------------------------------------
# Pure helpers (everything --selftest exercises lives here, network-free)
# ---------------------------------------------------------------------------
def split_join_key(join_key):
    """'9358001234_1751871234' -> ('9358001234', 1751871234). Bad -> (None, None)."""
    m = re.match(r"^(\d{10})_(\d{9,12})$", str(join_key or "").strip())
    if not m:
        return None, None
    return m.group(1), int(m.group(2))


def parse_when_to_unix(when_str):
    """Followup_Outcomes 'When' cell (IST wall time) -> unix seconds. Bad -> None."""
    s = str(when_str or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            dt = datetime.datetime.strptime(s, fmt).replace(tzinfo=IST)
            return int(dt.timestamp())
        except ValueError:
            continue
    return None


def normalise_direction(d):
    s = str(d or "").strip().lower()
    if "out" in s:
        return "outgoing"
    if "in" in s:
        return "incoming"
    return "unknown"


def vocab_for_direction(direction):
    if direction == "outgoing":
        return list(VOCAB_OUTGOING)
    if direction == "incoming":
        return list(VOCAB_INCOMING)
    return sorted(set(VOCAB_OUTGOING) | set(VOCAB_INCOMING))


def build_claim_index(outcome_rows):
    """Followup_Outcomes rows -> {mobile_last10: [(when_unix, row_dict), ...]}."""
    idx = {}
    for r in outcome_rows:
        digits = "".join(ch for ch in str(r.get("Mobile", "")) if ch.isdigit())
        if len(digits) < 10:
            continue
        m10 = digits[-10:]
        w = parse_when_to_unix(r.get("When"))
        if w is None:
            continue
        idx.setdefault(m10, []).append((w, r))
    for m10 in idx:
        idx[m10].sort(key=lambda t: t[0])
    return idx


def build_identity_index(outcome_rows):
    """{mobile_last10: {'Patient':.., 'Clinic ID':..}} — last non-blank wins.
    Fallback so a call with NO matched claim still carries a name / Clinic ID
    (needed for the training-KB completeness the owner asked for, S123)."""
    idx = {}
    for r in outcome_rows:
        digits = "".join(ch for ch in str(r.get("Mobile", "")) if ch.isdigit())
        if len(digits) < 10:
            continue
        m10 = digits[-10:]
        cur = idx.setdefault(m10, {"Patient": "", "Clinic ID": ""})
        name = str(r.get("Patient", "")).strip()
        cid = str(r.get("Clinic ID", "")).strip()
        if name:
            cur["Patient"] = name
        if cid:
            cur["Clinic ID"] = cid
    return idx


def build_recording_index(record_rows):
    """{join_key: recording_view_link} from the Stage-1 Call_Recordings tab.
    Prefers an existing link column; else builds one from the Drive File ID."""
    idx = {}
    for r in record_rows:
        jk = str(r.get("Join Key", "")).strip()
        if not jk:
            continue
        link = str(r.get("Drive Link", "")
                   or r.get("Recording Drive Link", "")).strip()
        if not link:
            fid = str(r.get("Drive File ID", "")).strip()
            if fid:
                link = DRIVE_FILE_VIEW.format(fid)
        if link:
            idx[jk] = link
    return idx


def duration_to_seconds(dur_str):
    """'0:52' / '1:02:03' -> seconds. Blank/bad -> None."""
    ds = str(dur_str or "").strip()
    if not ds:
        return None
    try:
        total = 0
        for p in ds.split(":"):
            total = total * 60 + int(p)
        return total
    except ValueError:
        return None


def assign_claims(call_list, claim_index):
    """Whole-day, phone-keyed claim assignment (REDESIGNED S123).

    call_list  : [(mobile10, call_start_unix, join_key), ...] — ALL of the
                 day's calls, so multi-call pairing is stable.
    claim_index: {mobile10: [(when_unix, row_dict), ...]} sorted by when.
    Returns    : {join_key: (claim_row_or_None, confidence)} where confidence
                 is 'unique'  (1 call + 1 candidate claim -> trustworthy),
                    'ordered' (competition; paired by call-time order -> glance),
                    'none'    (no claim filed -> the safe 'No claim logged').

    For each number: sort its calls by start time; walk them in order; each
    call takes the EARLIEST not-yet-taken claim that falls in its window
    [start - skew, start + forward]. That both fixes the batch-filing lag and
    keeps two calls to the same number from grabbing the same claim.
    """
    by_mobile = {}
    for m10, s, jk in call_list:
        if m10 and s is not None and jk:
            by_mobile.setdefault(m10, []).append((s, jk))
    result = {}
    for m10, calls in by_mobile.items():
        calls.sort(key=lambda t: t[0])
        claims = list(claim_index.get(m10, []))      # (when, row), time-sorted
        consumed = [False] * len(claims)
        n_calls = len(calls)
        for s, jk in calls:
            lo, hi = s - CLAIM_SKEW_BEFORE_S, s + CLAIM_MAX_FORWARD_S
            pick = None
            for i, (w, _row) in enumerate(claims):
                if consumed[i]:
                    continue
                if lo <= w <= hi:
                    pick = i
                    break                            # earliest unclaimed in window
            if pick is None:
                result[jk] = (None, "none")
                continue
            consumed[pick] = True
            if n_calls == 1:
                in_window = sum(1 for (w, _r) in claims if lo <= w <= hi)
                conf = "unique" if in_window == 1 else "ordered"
            else:
                conf = "ordered"
            result[jk] = (claims[pick][1], conf)
    return result


def resolve_identity(claim_row, identity_index, phone10):
    """Patient name + Clinic ID: prefer the matched claim, else fall back to
    the number's past outcomes so unmatched calls still carry an identity."""
    claim_row = claim_row or {}
    name = str(claim_row.get("Patient", "")).strip()
    cid = str(claim_row.get("Clinic ID", "")).strip()
    if (not name or not cid) and phone10:
        fb = (identity_index or {}).get(phone10, {})
        name = name or str(fb.get("Patient", "")).strip()
        cid = cid or str(fb.get("Clinic ID", "")).strip()
    return name, cid


def compare_outcomes(claimed, ai_outcome):
    """Mechanical comparison. Returns (verdict, true_false_cell).
    S140: the staff claim is NORMALISED first (in_ prefix, k_ aliases) and
    the K buttons' meaning groups count as Match/Partial — the AI's own
    vocabulary is untouched."""
    c_raw = str(claimed or "").strip()
    a = str(ai_outcome or "").strip()
    if a == UNCLEAR or not a:
        return "Unclear", ""
    if not c_raw:
        return "No claim logged", ""
    c = normalise_claim(c_raw)
    if a == c:
        return "Match", "TRUE"
    if a in CLAIM_EQUIV.get(c, ()):
        return "Match", "TRUE"
    if frozenset((a, c)) in PARTIAL_PAIRS:
        return "Partial", ""
    if a in CLAIM_PARTIAL.get(c, ()):
        return "Partial", ""
    return "Mismatch", "FALSE"


def build_system_prompt():
    """The judge's standing instructions. Cached by the API across calls."""
    def lines(codes):
        return "\n".join(f"  - {c}: {VOCAB_MEANINGS[c]}" for c in codes)
    return f"""You are a strict call-outcome classifier for an orthopaedic clinic in Bareilly, India. Patients are mostly older, Hindi-first, semi-urban; calls are in Hindi or Hinglish.

You will be given ONE call transcript, the call direction, and the talk duration in seconds. The transcript has NO speaker labels — it is one undivided block. Infer cautiously from context who is speaking (clinic staff vs patient/family). If you genuinely cannot tell what happened, answer UNCLEAR.

YOUR ONLY JOB: pick exactly ONE outcome code from the allowed list for this call's direction, plus set the six flags. Base everything ONLY on what the transcript actually says. Never guess, never assume, never invent dates/names/commitments.

OUTGOING follow-up call codes:
{lines(VOCAB_OUTGOING)}

INCOMING call codes:
{lines(VOCAB_INCOMING)}

Special code (either direction):
  - {UNCLEAR}: transcript too short, garbled, or genuinely ambiguous.

RULES
1. Pick from the allowed list for the given direction ONLY. If two codes could apply, pick the dominant one and say so in the reason.
2. A clear statement of fact (e.g. "dikha chuke hain", "operation ho gaya") outranks politeness noise ("theek hai, theek hai") elsewhere in the call.
3. "appointment_booked" needs explicit confirmation evidence (a date/time agreed, or staff saying it is noted). Mere intention ("aa jaunga") is will_come (incoming) or coming (outgoing), not a booking.
4. Very short or garbled transcript -> {UNCLEAR}. An honest "can't tell" is more useful than a confident wrong answer.
5. FLAGS — set true when the transcript contains:
   - flag_postop: any concern after surgery (pain, swelling, fever, wound, discharge, bleeding, implant worry, unexpected symptoms post-op).
   - flag_complaint: dissatisfaction with staff, waiting, charges, missed callbacks, rude behaviour, clinic process.
   - flag_urgent: possible urgent clinical concern (severe/sudden pain, cannot walk after injury, post-op fever, breathlessness, chest pain, new weakness/numbness, uncontrolled bleeding, bladder/bowel loss). You do not diagnose urgency; you flag trigger concepts.
   - flag_surgery: surgery/operation/estimate/package/implant/insurance/admission enquiry or discussion.
   - flag_clinical: caller asks a clinical question needing a doctor (symptoms, medicine change, reports meaning, activity limits, rehab). You NEVER answer such questions; you only flag them.
   - flag_conduct: staff conduct concern — curt/rude tone, call cut off abruptly on the caller, dismissive handling, caller audibly upset by staff. If true, one short conduct_note.
6. EVIDENCE: quote the single most decisive phrase from the transcript verbatim (Hindi as-is), with your best guess of who said it.
7. Reply with STRICT JSON ONLY — no markdown fences, no commentary — exactly these keys:
{{"ai_outcome": "<code or {UNCLEAR}>", "spoke_with": "patient|family|unclear", "confidence": "high|medium|low", "ai_reason": "<one line, simple English>", "evidence": "<decisive phrase quoted from transcript>", "evidence_speaker": "staff|patient|family|unclear", "flag_postop": false, "flag_complaint": false, "flag_urgent": false, "flag_surgery": false, "flag_clinical": false, "flag_conduct": false, "conduct_note": ""}}"""


def build_user_message(transcript_text, direction, duration_s):
    t = (transcript_text or "").strip()
    if len(t) > MAX_TRANSCRIPT_CHARS:
        t = t[:MAX_TRANSCRIPT_CHARS] + " …[truncated]"
    allowed = ", ".join(vocab_for_direction(direction) + [UNCLEAR])
    return (f"Call direction: {direction}\n"
            f"Talk duration (seconds): {duration_s if duration_s is not None else 'unknown'}\n"
            f"Allowed outcome codes for THIS call: {allowed}\n\n"
            f"TRANSCRIPT (no speaker labels):\n{t}")


def parse_ai_json(raw_text):
    """Model reply -> dict. Tolerates stray fences/whitespace. Raises ValueError."""
    s = str(raw_text or "").strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object in model reply")
    d = json.loads(s[start:end + 1])
    if "ai_outcome" not in d:
        raise ValueError("model JSON missing ai_outcome")
    d["ai_outcome"] = str(d.get("ai_outcome", "")).strip()
    d["spoke_with"] = str(d.get("spoke_with", "unclear")).strip().lower() or "unclear"
    d["confidence"] = str(d.get("confidence", "low")).strip().lower() or "low"
    d["ai_reason"] = str(d.get("ai_reason", "")).strip()
    d["evidence"] = str(d.get("evidence", "")).strip()
    d["evidence_speaker"] = str(d.get("evidence_speaker", "unclear")).strip().lower() or "unclear"
    d["conduct_note"] = str(d.get("conduct_note", "")).strip()
    for k in FLAG_KEYS:
        d[k] = bool(d.get(k, False))
    return d


def validate_ai_outcome(d, direction):
    """Off-list answer -> forced UNCLEAR with a note (never trust free text)."""
    allowed = set(vocab_for_direction(direction)) | {UNCLEAR}
    if d["ai_outcome"] not in allowed:
        d["ai_reason"] = (f"[off-list answer '{d['ai_outcome']}' forced to {UNCLEAR}] "
                          + d.get("ai_reason", ""))[:300]
        d["ai_outcome"] = UNCLEAR
        d["confidence"] = "low"
    return d


def assemble_verdict_row(trec, claim_row, ai, verdict, tf, confidence,
                         status, error, model_name,
                         phone10, patient_name, clinic_id, recording_link):
    """One Call_Verdicts row, in VERDICT_HEADER order (enriched S123)."""
    yn = lambda b: "YES" if b else ""
    claim_row = claim_row or {}
    ai = ai or {}
    return [
        trec.get("Date", ""), trec.get("Time", ""), trec.get("Direction", ""),
        phone10 or "",
        claim_row.get("Handled By", ""),
        patient_name,
        clinic_id,
        trec.get("Duration", ""),
        claim_row.get("Outcome", ""),
        ai.get("ai_outcome", ""),
        verdict, confidence, tf,
        ai.get("ai_reason", "")[:300],
        (ai.get("evidence", "")[:200]
         + (f"  [{ai.get('evidence_speaker')}]" if ai.get("evidence") else "")),
        ai.get("spoke_with", ""), ai.get("confidence", ""),
        yn(ai.get("flag_postop")), yn(ai.get("flag_complaint")),
        yn(ai.get("flag_urgent")), yn(ai.get("flag_surgery")),
        yn(ai.get("flag_clinical")), yn(ai.get("flag_conduct")),
        ai.get("conduct_note", "")[:200],
        recording_link or "",
        trec.get("Transcript Drive Link", ""),
        trec.get("Join Key", ""),
        status, (error or "")[:200],
        datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        PROMPT_VERSION, model_name,
        "", "", "",   # Doctor Flag / Doctor Note / Final Outcome — doctor's columns
    ]


# ---------------------------------------------------------------------------
# The AI call (isolated per the S123 provider-switch rule)
# ---------------------------------------------------------------------------
def call_ai_judge(api_key, model_name, system_prompt, user_message):
    """One classification call. Returns the model's raw text reply.
    Transport/5xx errors retried AI_RETRIES times; 4xx raised immediately."""
    payload = {
        "model": model_name,
        "max_tokens": AI_MAX_TOKENS,
        "temperature": 0,
        "system": [{"type": "text", "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_message}],
    }
    headers = {"x-api-key": api_key,
               "anthropic-version": ANTHROPIC_VERSION,
               "content-type": "application/json"}
    last_err = None
    for attempt in range(1 + AI_RETRIES):
        try:
            resp = requests.post(ANTHROPIC_URL, headers=headers,
                                 json=payload, timeout=AI_TIMEOUT_S)
            if resp.status_code == 200:
                data = resp.json()
                parts = [b.get("text", "") for b in data.get("content", [])
                         if b.get("type") == "text"]
                return "".join(parts)
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise RuntimeError(f"API {resp.status_code}: {resp.text[:150]}")
            last_err = RuntimeError(f"API {resp.status_code} (attempt {attempt+1})")
        except requests.exceptions.RequestException as e:
            last_err = e
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"AI call failed after retries: {last_err}")


# ---------------------------------------------------------------------------
# Sheet helpers
# ---------------------------------------------------------------------------
def get_sheets_client():
    sa_path = require_env("GOOGLE_SA_KEY", "WA_SA_KEY")
    creds = Credentials.from_service_account_file(
        sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)


def get_drive_service():
    token_path = require_env("DRIVE_TOKEN_FILE")
    if not os.path.exists(token_path):
        sys.exit(f"ERROR: DRIVE_TOKEN_FILE not found at {token_path}. Exiting (code 2).")
    creds = UserCredentials.from_authorized_user_file(token_path)
    return build("drive", "v3", credentials=creds)


def ensure_verdict_tab(audit_spreadsheet):
    try:
        ws = audit_spreadsheet.worksheet(VERDICT_TAB)
    except gspread.exceptions.WorksheetNotFound:
        ws = audit_spreadsheet.add_worksheet(title=VERDICT_TAB, rows=2000,
                                             cols=len(VERDICT_HEADER))
        ws.update(range_name="A1", values=[VERDICT_HEADER],
                  value_input_option="RAW")      # explicit cell (F-39, S141)
        print(f"  (created sheet tab '{VERDICT_TAB}' in the doctor-only sheet)", flush=True)
    return ws


COL = {name: i for i, name in enumerate(VERDICT_HEADER)}   # 0-based column map


def verify_verdict_header(ws_verdicts):
    """Fail-safe (S123): refuse to append onto an out-of-date tab layout.
    True if the sheet's header row matches VERDICT_HEADER exactly."""
    try:
        head = ws_verdicts.row_values(1)
    except Exception:
        head = []
    return head == VERDICT_HEADER


def build_existing_map(ws_verdicts):
    """{join_key: (sheet_row_number, record_dict)} for every existing row.
    row_number is 1-based INCLUDING the header, so data starts at row 2.
    Lets us judge a call ONCE and later fill in the claim without re-judging."""
    values = ws_verdicts.get_all_values()
    out = {}
    if not values:
        return out
    header = values[0]
    jk_col = header.index("Join Key") if "Join Key" in header else None
    for n, row in enumerate(values[1:], start=2):
        rec = {header[i]: (row[i] if i < len(row) else "")
               for i in range(len(header))}
        jk = (row[jk_col] if (jk_col is not None and jk_col < len(row))
              else rec.get("Join Key", ""))
        if jk:
            out[jk] = (n, rec)
    return out


def download_transcript_text(drive_service, file_id):
    request = drive_service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Selftest — pure logic, zero network, zero keys, zero third-party imports
# ---------------------------------------------------------------------------
def selftest():
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

    # 1-3: join key parsing
    p, u = split_join_key("9358001234_1751871234")
    check("join key parses phone", p == "9358001234")
    check("join key parses unix", u == 1751871234)
    check("bad join key -> None", split_join_key("garbage") == (None, None))

    # 4-5: When parsing (IST wall time round-trip)
    w = parse_when_to_unix("2026-07-06 16:30:00")
    expect = int(datetime.datetime(2026, 7, 6, 16, 30, tzinfo=IST).timestamp())
    check("When parses to unix (IST)", w == expect)
    check("junk When -> None", parse_when_to_unix("not a date") is None)

    # 6-7: direction + vocab
    check("direction normalises", normalise_direction("Outgoing") == "outgoing"
          and normalise_direction("INCOMING") == "incoming")
    check("unknown direction -> union vocab",
          set(vocab_for_direction("unknown")) == set(VOCAB_OUTGOING) | set(VOCAB_INCOMING))

    # S140: K-era claim normalisation + meaning groups
    check("in_ prefix strips to incoming vocab",
          compare_outcomes("in_appointment_booked", "appointment_booked") == ("Match", "TRUE"))
    check("k_coming aliases to coming",
          compare_outcomes("k_coming", "coming") == ("Match", "TRUE"))
    check("k_coming vs will_come never silently matches",
          compare_outcomes("k_coming", "will_come")[0] in ("Mismatch", "Partial"))
    check("k_not_coming group matches not_interested",
          compare_outcomes("k_not_coming", "not_interested") == ("Match", "TRUE"))
    check("k_call_again group matches on_medication",
          compare_outcomes("k_call_again", "on_medication") == ("Match", "TRUE"))
    check("k_call_again vs coming is Partial",
          compare_outcomes("k_call_again", "coming") == ("Partial", ""))
    check("no_answer claim matches cant_communicate",
          compare_outcomes("no_answer", "cant_communicate") == ("Match", "TRUE"))
    check("problem claim matches escalated (incoming button 5)",
          compare_outcomes("problem", "escalated") == ("Match", "TRUE"))
    check("k_not_coming vs coming is a real Mismatch",
          compare_outcomes("k_not_coming", "coming") == ("Mismatch", "FALSE"))

    # 8-17: claim matching (REDESIGNED S123 — whole-day, phone-keyed, ordered)
    # The core fix: a call at 16:00 whose outcome the staff files the NEXT
    # MORNING at 10:00 must still match (the old +45-min window failed it).
    call_A = int(datetime.datetime(2026, 7, 6, 16, 0, tzinfo=IST).timestamp())
    call_A2 = int(datetime.datetime(2026, 7, 6, 16, 30, tzinfo=IST).timestamp())
    outcome_rows = [
        {"Mobile": "919358001234", "When": "2026-07-07 10:00:00",   # next-morning batch
         "Outcome": "coming", "Handled By": "Shivani",
         "Patient": "Test A", "Clinic ID": "101"},
        {"Mobile": "9358001234", "When": "2026-07-07 10:05:00",     # 2nd claim, same number
         "Outcome": "problem", "Handled By": "Alisha",
         "Patient": "Test A", "Clinic ID": "101"},
        {"Mobile": "9000000000", "When": "2026-07-06 16:35:00",     # same-evening filing
         "Outcome": "dikha_chuke", "Handled By": "Manoj B",
         "Patient": "Test B", "Clinic ID": "202"},
    ]
    idx = build_claim_index(outcome_rows)
    jkA, jkA2 = "9358001234_%d" % call_A, "9358001234_%d" % call_A2
    calls = [("9358001234", call_A, jkA),
             ("9358001234", call_A2, jkA2),
             ("1111111111", call_A, "1111111111_%d" % call_A)]
    asg = assign_claims(calls, idx)
    check("next-morning claim NOW MATCHES (the batch-filing fix)",
          asg[jkA][0] and asg[jkA][0]["Outcome"] == "coming")
    check("two calls to one number pair in order (2nd call -> 2nd claim)",
          asg[jkA2][0] and asg[jkA2][0]["Outcome"] == "problem")
    check("competition -> 'ordered' confidence", asg[jkA][1] == "ordered")
    check("no claim for this number -> (None, 'none')",
          asg["1111111111_%d" % call_A] == (None, "none"))
    solo = assign_claims([("9000000000", call_A, "9000000000_solo")], idx)
    check("single call + single candidate claim -> 'unique'",
          solo["9000000000_solo"][1] == "unique")
    late = build_claim_index([{"Mobile": "9358001234",
                               "When": "2026-07-08 12:00:00", "Outcome": "coming"}])
    check("claim beyond the forward window -> none",
          assign_claims([("9358001234", call_A, "k")], late)["k"] == (None, "none"))
    ident = build_identity_index(outcome_rows)
    nm, cid = resolve_identity(None, ident, "9000000000")
    check("identity fallback fills name/ID for an unmatched call",
          nm == "Test B" and cid == "202")
    rec_idx = build_recording_index([{"Join Key": "k1", "Drive File ID": "FID9"}])
    check("recording link built from Drive File ID",
          rec_idx.get("k1", "").endswith("/FID9/view"))
    check("duration parses mm:ss and hh:mm:ss",
          duration_to_seconds("0:52") == 52 and duration_to_seconds("1:02:03") == 3723)
    rows = outcome_rows  # reused by the row-assembly test below

    # 11-15: comparison table
    check("Match", compare_outcomes("coming", "coming") == ("Match", "TRUE"))
    check("Mismatch", compare_outcomes("not_interested", "coming") == ("Mismatch", "FALSE"))
    check("Partial", compare_outcomes("dikha_chuke", "close_followup") == ("Partial", ""))
    check("Unclear", compare_outcomes("coming", UNCLEAR) == ("Unclear", ""))
    check("No claim", compare_outcomes("", "coming") == ("No claim logged", ""))

    # 16-18: model-reply parsing + off-list guard
    fake = ('```json\n{"ai_outcome":"dikha_chuke","spoke_with":"patient",'
            '"confidence":"high","ai_reason":"Patient said already visited.",'
            '"evidence":"parso dikha chuke hain","evidence_speaker":"patient",'
            '"flag_postop":false,"flag_complaint":false,"flag_urgent":false,'
            '"flag_surgery":true,"flag_clinical":false,"flag_conduct":false,'
            '"conduct_note":""}\n```')
    d = parse_ai_json(fake)
    check("AI JSON parses through fences", d["ai_outcome"] == "dikha_chuke"
          and d["flag_surgery"] is True)
    try:
        parse_ai_json("no json here")
        check("bad AI reply raises", False)
    except ValueError:
        check("bad AI reply raises", True)
    off = validate_ai_outcome({"ai_outcome": "made_up_code", "ai_reason": "x",
                               "confidence": "high", "spoke_with": "patient",
                               "evidence": "", "evidence_speaker": "unclear",
                               "conduct_note": "",
                               **{k: False for k in FLAG_KEYS}}, "outgoing")
    check("off-list answer forced to UNCLEAR", off["ai_outcome"] == UNCLEAR)

    # row assembly (enriched S123 signature)
    trec = {"Date": "2026-07-06", "Time": "16:30", "Direction": "outgoing",
            "Duration": "0:52", "Join Key": "9358001234_1751871234",
            "Transcript Drive Link": "https://drive.example/x"}
    row = assemble_verdict_row(trec, rows[0], d, "Match", "TRUE", "unique",
                               "done", "", DEFAULT_MODEL,
                               "9358001234", "Test A", "101",
                               "https://drive.example/rec")
    check("row length == header length", len(row) == len(VERDICT_HEADER))
    check("row carries FULL patient number",
          row[VERDICT_HEADER.index("Patient Number")] == "9358001234")
    check("row carries agent from claim",
          row[VERDICT_HEADER.index("Agent")] == "Shivani")
    check("row carries match confidence",
          row[VERDICT_HEADER.index("Match Confidence")] == "unique")
    check("row carries recording link",
          row[VERDICT_HEADER.index("Recording Link")] == "https://drive.example/rec")
    check("doctor columns blank", row[-3:] == ["", "", ""])

    # 22-23: prompt sanity
    sp = build_system_prompt()
    check("prompt carries all outgoing codes",
          all(c in sp for c in VOCAB_OUTGOING))
    check("prompt forbids identifiers (no name/mobile fields sent)",
          "Patient name" not in build_user_message("test", "outgoing", 30))

    # 24: mask
    check("mask hides all but last-4", mask("9358001234") == "******1234")

    passed = sum(1 for _, ok in results if ok)
    print(f"\nSELFTEST: {passed}/{len(results)} PASS")
    return 0 if passed == len(results) else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Stage 3: AI judge — classify transcripts, compare to staff claims.")
    ap.add_argument("--date", help="only judge Call_Transcripts rows for this Date (YYYY-MM-DD)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N calls judged (0 = no cap)")
    ap.add_argument("--dry-run", action="store_true",
                    help="judge for real (AI is called) but write NOTHING to any sheet")
    ap.add_argument("--selftest", action="store_true",
                    help="offline logic test; no network, no keys, no writes")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    # Deferred imports: only real runs need the venv packages.
    global gspread, Credentials, UserCredentials, build, MediaIoBaseDownload, requests
    import gspread as _gs
    from google.oauth2.service_account import Credentials as _C
    from google.oauth2.credentials import Credentials as _UC
    from googleapiclient.discovery import build as _b
    from googleapiclient.http import MediaIoBaseDownload as _MD
    import requests as _rq
    gspread, Credentials, UserCredentials = _gs, _C, _UC
    build, MediaIoBaseDownload, requests = _b, _MD, _rq

    load_env()
    api_key = require_env("ANTHROPIC_API_KEY")
    model_name = os.environ.get("AI_JUDGE_MODEL", DEFAULT_MODEL)
    tracker_id = os.environ.get("TRACKER_SHEET_ID", DEFAULT_TRACKER_SHEET_ID)
    audit_id = os.environ.get("AUDIT_SHEET_ID", DEFAULT_AUDIT_SHEET_ID)

    gc = get_sheets_client()
    drive = get_drive_service()

    # --- read Call_Transcripts (tracker) ---
    try:
        tracker = gc.open_by_key(tracker_id)
        ws_tr = tracker.worksheet(TRANSCRIPT_TAB)
        trans_rows = ws_tr.get_all_records()
    except Exception as e:
        sys.exit(f"ERROR: cannot read {TRANSCRIPT_TAB}: {e}. Exiting (code 5).")
    if not trans_rows:
        sys.exit(f"ERROR: {TRANSCRIPT_TAB} is empty. Exiting (code 5).")

    # --- read Followup_Outcomes (tracker); failure degrades, never stalls ---
    claim_index, identity_index = {}, {}
    try:
        ws_out = tracker.worksheet(OUTCOMES_TAB)
        outcome_rows = ws_out.get_all_records()
        claim_index = build_claim_index(outcome_rows)
        identity_index = build_identity_index(outcome_rows)
    except Exception as e:
        print(f"WARN: cannot read {OUTCOMES_TAB} ({e}); verdicts this run will "
              f"show 'No claim logged' and may lack a name.", flush=True)

    # --- read Call_Recordings (tracker) for recording links; best-effort -----
    recording_index = {}
    try:
        ws_rec = tracker.worksheet(RECORD_TAB)
        recording_index = build_recording_index(ws_rec.get_all_records())
    except Exception as e:
        print(f"WARN: cannot read {RECORD_TAB} ({e}); recording links blank "
              f"this run.", flush=True)

    # --- open doctor-only sheet; verify layout; map existing rows ------------
    try:
        audit = gc.open_by_key(audit_id)
        ws_v = ensure_verdict_tab(audit)
    except Exception as e:
        sys.exit(f"ERROR: cannot open doctor-only audit sheet: {e}. Exiting (code 5).")
    if not verify_verdict_header(ws_v):
        sys.exit(
            f"ERROR: the '{VERDICT_TAB}' tab has an OLD column layout. This "
            f"version adds columns (Patient Number, Match Confidence, "
            f"Recording Link). Please DELETE or RENAME the '{VERDICT_TAB}' tab "
            f"in the doctor-only sheet, then re-run — it is recreated with the "
            f"new layout. No existing row is touched. Exiting (code 5).")
    existing = build_existing_map(ws_v)

    # --- pair the whole day's calls to claims UP FRONT (redesigned join) -----
    scope_rows = [r for r in trans_rows
                  if r.get("Status") == "done" and r.get("Join Key")]
    if args.date:
        scope_rows = [r for r in scope_rows
                      if str(r.get("Date", "")).strip() == args.date]
    call_list = []
    for r in scope_rows:
        p10, s = split_join_key(r.get("Join Key", ""))
        call_list.append((p10, s, r.get("Join Key", "")))
    assignment = assign_claims(call_list, claim_index)

    # --- split into: judge-new / re-match (claim landed later) / settled -----
    to_judge, to_rematch = [], []
    for r in scope_rows:
        jk = r.get("Join Key", "")
        if not r.get("Transcript Drive File ID"):
            continue
        if jk not in existing:
            to_judge.append(r)
        elif str(existing[jk][1].get("Status", "")).strip() != "done":
            to_judge.append(r)                        # a prior FAILED row -> retry
        elif not str(existing[jk][1].get("Claimed Outcome", "")).strip():
            to_rematch.append(r)                      # judged, still no claim -> try to fill
        # else: fully settled -> skip
    if args.limit:
        to_judge = to_judge[: args.limit]             # --limit caps costly AI calls only

    tag = "  [dry-run: nothing will be written]" if args.dry_run else ""
    print(f"{len(to_judge)} to judge, {len(to_rematch)} to re-match"
          f"{' for ' + args.date if args.date else ''}.{tag}", flush=True)
    if not to_judge and not to_rematch:
        return

    system_prompt = build_system_prompt()
    n_ok = n_fail = n_upd = 0

    # --- F-39 (S141): never trust Sheets append-detection again. Compute
    #     the true last data row ONCE, write every new verdict to an
    #     EXPLICIT range, and advance the counter locally.
    next_row = 0
    if to_judge and not args.dry_run:
        next_row = len(ws_v.get_all_values()) + 1
        short = next_row + len(to_judge) - 1 - ws_v.row_count
        if short > 0:
            ws_v.add_rows(short)

    # ----- NEW calls: run the AI judge once, then append a full row ----------
    for i, trec in enumerate(to_judge, 1):
        jk = trec.get("Join Key", "")
        phone10, _start = split_join_key(jk)
        direction = normalise_direction(trec.get("Direction"))
        dur = duration_to_seconds(trec.get("Duration"))
        claim_row, confidence = assignment.get(jk, (None, "none"))

        print(f"[judge {i}/{len(to_judge)}] {trec.get('Date')} {trec.get('Time')} "
              f"{direction} {mask(phone10)} …", flush=True)

        status, error, ai, verdict, tf = "done", "", None, "", ""
        try:
            text = download_transcript_text(drive, trec["Transcript Drive File ID"])
            raw = call_ai_judge(api_key, model_name, system_prompt,
                                build_user_message(text, direction, dur))
            ai = validate_ai_outcome(parse_ai_json(raw), direction)
            verdict, tf = compare_outcomes(
                (claim_row or {}).get("Outcome", ""), ai["ai_outcome"])
            flags_on = [k for k in FLAG_KEYS if ai.get(k)]
            print(f"      AI={ai['ai_outcome']}  claim="
                  f"{(claim_row or {}).get('Outcome', '(none)')}  "
                  f"[{confidence}] -> {verdict}"
                  f"{'  FLAGS: ' + ','.join(f[5:] for f in flags_on) if flags_on else ''}",
                  flush=True)
            n_ok += 1
        except Exception as e:
            status, error = "FAILED", str(e)
            verdict, tf, confidence = "", "", "none"
            print(f"      FAILED: {str(e)[:150]}", flush=True)
            n_fail += 1

        name, cid = resolve_identity(claim_row, identity_index, phone10)
        rec_link = recording_index.get(jk, "")
        if not args.dry_run:
            row = assemble_verdict_row(trec, claim_row, ai, verdict, tf,
                                       confidence, status, error, model_name,
                                       phone10, name, cid, rec_link)
            ws_v.update(range_name=f"A{next_row}", values=[row],
                        value_input_option="USER_ENTERED")   # F-39: explicit row
            next_row += 1

    # ----- ALREADY-JUDGED calls: fill the claim/verdict if it landed now -----
    for trec in to_rematch:
        jk = trec.get("Join Key", "")
        phone10, _start = split_join_key(jk)
        claim_row, confidence = assignment.get(jk, (None, "none"))
        if not claim_row:
            continue                                  # still no claim; leave the row as-is
        row_num, rec = existing[jk]
        verdict, tf = compare_outcomes(
            claim_row.get("Outcome", ""), str(rec.get("AI Outcome", "")).strip())
        name, cid = resolve_identity(claim_row, identity_index, phone10)
        updates = {
            "Agent": claim_row.get("Handled By", ""),
            "Claimed Outcome": claim_row.get("Outcome", ""),
            "Verdict": verdict,
            "Match Confidence": confidence,
            "Outcome TRUE/FALSE": tf,
        }
        if not str(rec.get("Patient Name", "")).strip():
            updates["Patient Name"] = name
        if not str(rec.get("Clinic ID", "")).strip():
            updates["Clinic ID"] = cid
        print(f"[update] {trec.get('Date')} {trec.get('Time')} {mask(phone10)} "
              f"claim now={claim_row.get('Outcome', '')} [{confidence}] -> {verdict}",
              flush=True)
        if not args.dry_run:
            cells = [gspread.Cell(row_num, COL[col] + 1, val)
                     for col, val in updates.items()]
            ws_v.update_cells(cells, value_input_option="USER_ENTERED")
        n_upd += 1

    print(f"\nDone. {n_ok} judged, {n_fail} failed, {n_upd} claim-updated"
          f"{' (dry-run: nothing written)' if args.dry_run else ''}.", flush=True)


if __name__ == "__main__":
    main()
