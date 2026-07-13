#!/usr/bin/env python3
"""
verdict_review.py — Stage 3b of the Staff Call Audit project: the Verdict
Analysis Layer.  Dr. Manoj Agarwal Clinic, Bareilly.  Session 124.
Decision D155 (parent: D154 design-lock, D149 the AI judge, D62 the audit idea).

WHAT THIS DOES
  Runs after call_verdict.py (Stage 3, the AI judge).  It READS the
  "Call_Verdicts" tab of the doctor-only Call Audit sheet and turns it into a
  human reading surface:

    Verdict_Review   — a rolling 7-day, ONE-PATIENT-PER-SCREEN vertical tab.
                       Cards are segregated by scenario, in this order:
                         1. Mismatch   (includes Partial — a softened mismatch)
                         2. AI logged an outcome, staff didn't
                         3. Unclear
                         4. Suspect joins (a claim bound to an incoming call)
                         5. Matches    (one line each, not cards)
                       Each card carries the full transcript beneath it in a
                       COLLAPSED row group, with the AI's evidence excerpt
                       highlighted in place, so the doctor can judge in context.
                       Two cells per card are left editable: a DROPDOWN of the
                       live dashboard outcome codes, and a free-text note.
                       Everything else on the tab is protected.

    Doctor_Verdicts  — an append/upsert record of the doctor's answers, keyed
                       on Join Key.  This is the durable ground-truth ledger
                       that later seeds the voice-bot KB and the autonomous
                       judge calibration (v1.1 will de-identify and export it).

ONE WRITER PER TABLE  (the standing architecture rule)
  call_verdict.py  owns  Call_Verdicts     — this script NEVER writes to it.
  verdict_review.py owns Verdict_Review  and  Doctor_Verdicts.

THE SAFE ORDER (this is the whole safety story of the script)
  1. HARVEST  the doctor's typed answers out of the existing Verdict_Review
              into Doctor_Verdicts.
  2. Only if the harvest fully succeeded, DELETE and REDRAW Verdict_Review.
  If anything fails in step 1, the script exits BEFORE step 2.  The doctor's
  typed answers can therefore never be destroyed by a rebuild.  Answers already
  in Doctor_Verdicts are pre-filled back into the redrawn cards.

PHI / RETENTION
  Full transcripts are PHI.  They are rendered into a ROLLING WINDOW
  (default 7 days) that is fully redrawn each run, so a transcript leaves this
  tab automatically once its call ages out.  This keeps the tab compliant with
  the LOCKED 90-day raw-transcript purge rule (Voice Bot plan, Stage 2a)
  without the purge job needing to know this tab exists.
  Console output masks phone numbers to the last 4 digits.
  Doctor_Verdicts DOES carry identity (it is in the doctor-only sheet).  The
  de-identified export for the voice-bot KB is a separate, later step (v1.1).

NO AI, NO COST
  This script makes zero API calls to any model.  It reads a sheet, reads
  transcripts from Drive, and writes two tabs.

MODES
  --selftest          pure offline logic checks; no keys, no network, no
                      third-party imports.  Run this first, always.
  --dry-run           reads everything for real, prints the plan (how many
                      cards in each section, how many answers harvested),
                      writes NOTHING -- it will not even create a missing tab.
  (no flag)           real run: harvest, then redraw.
  --days N            size of the rolling window (default 7).
  --no-transcripts    render cards without the transcript row-groups (fast;
                      useful for a first look or if Drive is slow).

ENV (all already present in /root/wa/.env from Stages 1-3)
  GOOGLE_SA_KEY       service-account json path  (sheet read/write)
                      (WA_SA_KEY accepted as the legacy alias)
  DRIVE_TOKEN_FILE    /root/wa/recordings-archive/drive_token.json
                      (owner OAuth; downloads the transcript .txt files)
  AUDIT_SHEET_ID      optional override of the doctor-only sheet id

RUN
  /root/wa/venv/bin/python3 /root/wa/recordings-archive/verdict_review.py --selftest
  /root/wa/venv/bin/python3 /root/wa/recordings-archive/verdict_review.py --dry-run
  /root/wa/venv/bin/python3 /root/wa/recordings-archive/verdict_review.py

DEPENDENCIES
  gspread, google-auth, google-api-python-client  — all already in the venv.
"""

import argparse
import datetime
import hashlib
import io
import os
import random
import re
import sys

# Third-party names are populated in main(); selftest must run without them.
gspread = None
Credentials = None
UserCredentials = None
build = None
MediaIoBaseDownload = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ENV_PATH = "/root/wa/.env"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

DEFAULT_AUDIT_SHEET_ID = "1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ"

VERDICT_TAB = "Call_Verdicts"      # read-only to this script
REVIEW_TAB = "Verdict_Review"      # this script is the only writer
DOCTOR_TAB = "Doctor_Verdicts"     # this script is the only writer

DEFAULT_WINDOW_DAYS = 7
BUILD_VERSION = "verdict_review v3 (S143, D240)"

# --- D240: forced cards — referee sittings + the daily spot-check drip ------
FORCE_FILE_DEFAULT = "/root/wa/recordings-archive/force_keys.txt"
SPOTCHECK_COUNT = 2

# The EXACT Call_Verdicts header, copied from call_verdict.py (S123 layout).
# If this does not match the live tab, we refuse to run.  A silently-changed
# upstream layout would otherwise be read into the wrong columns.
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

DOCTOR_HEADER = [
    "Join Key", "Date", "Time", "Direction", "Patient Number",
    "Patient Name", "Clinic ID", "Agent",
    "Claimed Outcome", "AI Outcome", "Verdict", "Match Confidence",
    "Doctor Final Outcome", "Doctor Note",
    "Section", "Recorded At", "Build",
]

# --- Answer vocabularies: MUST mirror the LIVE dashboard dropdowns ----------
# Same rule as call_verdict.py: if a dashboard dropdown changes, both scripts
# change with it.  These are the doctor's dropdown choices too.
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

# Extra doctor-only choices, appended to whichever vocabulary applies.
DOCTOR_EXTRA = [UNCLEAR, "cannot_judge", "transcript_bad"]

VOCAB_MEANINGS = {
    "coming":              "patient says they will come / visit the clinic",
    "out_of_town":         "patient is out of town / travelling",
    "on_medication":       "patient is continuing medicines, will come later",
    "cant_communicate":    "call connected but no meaningful conversation possible",
    "dikha_chuke":         "patient says they ALREADY visited (dikha chuke)",
    "problem":             "patient reports a problem / needs attention",
    "close_followup":      "treatment complete, follow-up can be closed",
    "not_interested":      "patient clearly not interested in returning",
    "treatment_elsewhere": "patient is taking treatment somewhere else",
    "wrong_number":        "the person reached is not the patient / wrong number",
    "asked_not_to_call":   "the person asked the clinic to stop calling",
    "resolved_on_call":    "caller's question fully answered on this call",
    "appointment_booked":  "an appointment was clearly CONFIRMED on the call",
    "info_given_will_act": "information given; caller will act on it",
    "needs_callback":      "someone must call back; the matter is not finished",
    "escalated":           "the matter needs the doctor personally",
    "will_come":           "caller says they will come (NOT a confirmed booking)",
    "enquiry_only":        "general enquiry only (timings, address, fee)",
    "no_action":           "no action needed / not relevant to patient care",
    UNCLEAR:               "not determinable from the transcript",
    "cannot_judge":        "doctor cannot decide even with the transcript",
    "transcript_bad":      "transcript is empty / unusable",
}

FLAG_COLUMNS = [
    ("Flag PostOp", "post-op"), ("Flag Complaint", "complaint"),
    ("Flag Urgent", "urgent"), ("Flag Surgery", "surgery"),
    ("Flag Clinical", "clinical"), ("Flag Conduct", "conduct"),
]

# --- Section model ---------------------------------------------------------
SEC_MISMATCH = "mismatch"
SEC_AI_ONLY = "ai_only"
SEC_UNCLEAR = "unclear"
SEC_MATCH = "match"
SEC_INCOMING_NOCLAIM = "incoming_noclaim"   # RETIRED S140 (D153 overturned by D190/K-2); kept so old counts never KeyError
SEC_SUSPECT = "suspect_join"                # see classify_section
SEC_FLAGGED = "flagged"                     # see placement_section
SEC_ERROR = "error"                         # judge errored — counted only
SEC_FORCED = "forced"                       # D240: drawn on request, above everything

CARD_SECTIONS = [SEC_FLAGGED, SEC_MISMATCH, SEC_AI_ONLY, SEC_UNCLEAR, SEC_SUSPECT]

SECTION_TITLES = {
    SEC_FORCED:   "0.  REFEREE / SPOT-CHECK  —  answer these. Answered ones collapse to a line.",
    SEC_FLAGGED:  "1.  FLAGGED  —  clinical / safety review. Read these first.",
    SEC_MISMATCH: "2.  MISMATCH  —  staff said one thing, the AI heard another",
    SEC_AI_ONLY:  "3.  AI LOGGED AN OUTCOME  —  staff filed nothing",
    SEC_UNCLEAR:  "4.  UNCLEAR  —  why could nobody tell?",
    SEC_SUSPECT:  "5.  SUSPECT JOINS  —  a claim attached to an INCOMING call. "
                  "Not staff error. DO NOT TRAIN ON THESE.",
    SEC_MATCH:    "6.  MATCHES  —  one line each (no review needed)",
}

# --- Sheet geometry --------------------------------------------------------
# A = label, B = value / dropdown, C = value2 / free-text note, D = spare
# F = Join Key (hidden, machine), G = row marker (hidden, machine)
COL_LABEL, COL_VAL, COL_VAL2, COL_SPARE = 0, 1, 2, 3
COL_MACHINE_KEY, COL_MACHINE_MARK = 5, 6
SHEET_COLS = 7
MARKER_RESPONSE = "RESP"

COLUMN_WIDTHS = {0: 190, 1: 300, 2: 430, 3: 110}

TRANSCRIPT_WRAP = 105       # characters per rendered transcript line
MAX_TRANSCRIPT_LINES = 220  # defensive cap per card
MAX_CARDS_PER_SECTION = 120 # defensive cap; a normal day is single digits

# --- Colours (Sheets API rgb 0..1) -----------------------------------------
C_SECTION_BAND = {"red": 0.16, "green": 0.24, "blue": 0.36}
C_SECTION_TEXT = {"red": 1.0, "green": 1.0, "blue": 1.0}
C_CARD_TITLE = {"red": 0.85, "green": 0.89, "blue": 0.95}
C_RESPONSE_ROW = {"red": 0.85, "green": 0.95, "blue": 0.85}
C_EVIDENCE_HIT = {"red": 1.0, "green": 0.95, "blue": 0.60}
C_TRANSCRIPT = {"red": 0.97, "green": 0.97, "blue": 0.97}
C_SUMMARY = {"red": 0.93, "green": 0.93, "blue": 0.88}


# ---------------------------------------------------------------------------
# .env loader — same pattern as every other stage
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
            os.environ.setdefault(key.strip(),
                                  val.strip().strip('"').strip("'"))


def require_env(name, alt=None):
    """Same lookup as call_verdict.py: the primary name, then a legacy alias.
    The clinic .env has carried WA_SA_KEY since Stage 1; GOOGLE_SA_KEY is the
    newer name.  Accept either.  The VALUE is never printed."""
    val = os.environ.get(name) or (os.environ.get(alt) if alt else None)
    if not val:
        names = name + (f" (or {alt})" if alt else "")
        sys.exit(f"ERROR: required environment variable {names} is not set. "
                 f"Exiting (code 2).")
    return val


def mask_phone(number):
    """Console safety: 9358001234 -> ******1234."""
    s = "".join(ch for ch in str(number or "") if ch.isdigit())
    if len(s) <= 4:
        return "*" * len(s)
    return "*" * (len(s) - 4) + s[-4:]


# ---------------------------------------------------------------------------
# Pure logic — everything below here is covered by --selftest
# ---------------------------------------------------------------------------
# --- S140 (F-18 retired): staff DO file incoming outcomes now (K-2) --------
# A claim on an incoming call is NORMAL. The only remaining wrong-join
# signal (D158/G-4) is a LEGACY OUTGOING dropdown code bound to an incoming
# call: those codes are follow-up statements staff could not have made
# about an incoming conversation. K-era codes (k_*, in_*, no_answer),
# `problem` (incoming button 5 delegates through it) and the shared
# `cant_communicate` are legitimate on incoming.
LEGACY_OUTGOING_SUSPECT = {
    "coming", "out_of_town", "on_medication", "dikha_chuke",
    "close_followup", "not_interested", "treatment_elsewhere",
    "wrong_number", "asked_not_to_call",
}

def normalise_claim(code):
    """Canonical form for the SUSPECT test only: k_* codes stay k_* here —
    aliasing k_coming to coming would make a legitimate K-2 incoming tap
    look like a legacy outgoing code (caught by selftest, S140)."""
    c = "".join(ch if (ch.isalnum() or ch == "_") else "_"
                for ch in str(code or "").strip().lower())
    if c.startswith("in_"):
        c = c[3:]
    return c


def classify_section(row):
    """Which section does one Call_Verdicts row belong in?

    Rules (in order; REWRITTEN S140 — D153 retired, F-18 closed):
      * a row the judge could not process at all -> error (counted, not shown)
      * INCOMING call whose claim is a LEGACY OUTGOING dropdown code ->
        SUSPECT JOIN. Since K-2 (S140) staff file incoming outcomes
        legitimately (k_*, in_*, no_answer, problem), so an incoming claim is
        NORMAL — the only remaining wrong-join signal (D158/G-4) is an
        outgoing-only follow-up code bound to an incoming call: that claim
        almost certainly belongs to a later outgoing call to the same number.
      * Mismatch or Partial                      -> the Mismatch section
        (Partial is a SOFTENED mismatch, e.g. dikha_chuke vs close_followup;
         it is still training material, so it belongs on a card, labelled.)
      * No claim logged (EITHER direction) + a real AI outcome ->
        'AI logged, staff didn't'. D153's "correct by design" excuse for
        incoming is gone: an unlogged incoming conversation is a real gap.
      * No claim logged + no usable AI outcome   -> Unclear
      * Unclear, or the AI answered UNCLEAR      -> Unclear
      * Match                                    -> the collapsed Matches list
      * anything unrecognised                    -> Unclear (fail visible, not silent)
    """
    status = str(row.get("Status", "")).strip().lower()
    error = str(row.get("Error", "")).strip()
    if error or (status and status != "done"):
        return SEC_ERROR

    verdict = str(row.get("Verdict", "")).strip().lower()
    direction = str(row.get("Direction", "")).strip().lower()
    ai_out = str(row.get("AI Outcome", "")).strip()
    has_claim = bool(str(row.get("Claimed Outcome", "")).strip())

    if (direction.startswith("in") and has_claim
            and normalise_claim(row.get("Claimed Outcome")) in LEGACY_OUTGOING_SUSPECT):
        return SEC_SUSPECT
    if verdict in ("mismatch", "partial"):
        return SEC_MISMATCH
    if verdict == "no claim logged":
        if ai_out and ai_out != UNCLEAR:
            return SEC_AI_ONLY
        return SEC_UNCLEAR
    if verdict == "unclear" or ai_out == UNCLEAR:
        return SEC_UNCLEAR
    if verdict == "match":
        return SEC_MATCH
    return SEC_UNCLEAR


def placement_section(row):
    """WHERE a row is drawn, as opposed to WHAT it is.

    A safety flag outranks every scenario.  Without this, a surgery flag on a
    call where staff and the AI agreed would collapse into a one-line entry in
    the Matches list, and a flagged INCOMING call would be dropped from the tab
    altogether.  A flag is a clinical signal about the patient, not a statement
    about staff accuracy, so it must never be hidden by a bookkeeping rule.

    Placement moves; the SCENARIO (classify_section) does not.  Counts and the
    match rate are computed from classify_section, so surfacing a flagged match
    at the top of the tab cannot flatter or damage the accuracy number.
    """
    scenario = classify_section(row)
    if scenario == SEC_ERROR:
        return SEC_ERROR
    if flags_of(row):
        return SEC_FLAGGED
    return scenario


def key_token(join_key):
    """A stable, opaque handle for a row, written into the tab's hidden machine
    column instead of the Join Key itself.

    The Join Key is `<full phone>_<unix>`.  The machine columns are hidden on
    the sheet, but they survive a CSV/XLSX export — so writing the raw key
    would put full patient numbers into every export of this tab.  The token is
    a one-way hash; the script rebuilds the token -> Join Key map at run time
    from Call_Verdicts, which it is already reading anyway.
    """
    return "vr" + hashlib.sha1(str(join_key).encode("utf-8")).hexdigest()[:14]


def parse_row_date(row):
    """'2026-07-06' -> date.  Returns None if unparseable (row then kept, so a
    bad date can never silently hide a mismatch from the doctor)."""
    raw = str(row.get("Date", "")).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def in_window(row, today, days):
    """Rolling window: today and the (days-1) days before it.  A row with an
    unparseable date is KEPT (visible-fail, never a silent drop)."""
    d = parse_row_date(row)
    if d is None:
        return True
    return (today - d).days < days and (today - d).days >= 0


def sort_key(row):
    """Newest first, then by time descending."""
    d = parse_row_date(row) or datetime.date(1900, 1, 1)
    t = str(row.get("Time", "")).strip()
    return (-d.toordinal(), _neg_time(t))


def _neg_time(t):
    """'15:04' -> a value that sorts descending."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})", t or "")
    if not m:
        return 0
    return -(int(m.group(1)) * 60 + int(m.group(2)))


# ---------------------------------------------------------------------------
# D240 — forced cards (referee sittings) + the daily spot-check drip
# ---------------------------------------------------------------------------
def parse_force_file(text):
    """force_keys.txt -> ordered, de-duplicated Join Key list.
    One key per line; blank lines and '#' comments ignored; FILE ORDER is kept
    (the owner works his referee workbook top to bottom)."""
    keys, seen = [], set()
    for line in (text or "").splitlines():
        k = line.split("#", 1)[0].strip()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    return keys


def is_answered(prefill_entry):
    """A card counts as answered once a dropdown outcome exists (note optional).
    Answered forced keys collapse to a line and are never asked twice."""
    return bool(str((prefill_entry or {}).get("outcome", "")).strip())


def pick_spotchecks(rows, prefill, exclude, today, n=SPOTCHECK_COUNT):
    """The daily D237 drip: up to n clean MATCH calls drawn as full cards.

    ONE DECIDER (owner decision, S143): this script picks and marks them; the
    digest only reads the tab and reports what it finds — the two scripts can
    never disagree about which calls are today's spot-checks.

    Pool rules: placement == match (a flagged or suspect row already gets a
    card elsewhere and must never draw twice) · never a call the doctor has
    already answered · never a key already in the forced list.  Seeded by the
    date, so every run on the same day picks the same calls."""
    pool = []
    for r in rows:
        jk = str(r.get("Join Key", "")).strip()
        if (jk and jk not in exclude
                and placement_section(r) == SEC_MATCH
                and not is_answered(prefill.get(jk))):
            pool.append(r)
    pool.sort(key=lambda r: str(r.get("Join Key", "")).strip())
    rng = random.Random(f"spotcheck-{today.isoformat()}")
    picks = pool if len(pool) <= n else rng.sample(pool, n)
    return sorted(picks, key=sort_key)


def vocab_for_direction(direction):
    """The dropdown the doctor gets, chosen by call direction, plus the
    doctor-only escape hatches.  Mirrors the live dashboard (KB rule)."""
    base = (VOCAB_INCOMING if str(direction or "").strip().lower().startswith("in")
            else VOCAB_OUTGOING)
    out = list(base)
    for extra in DOCTOR_EXTRA:
        if extra not in out:
            out.append(extra)
    return out


def describe_outcome(code):
    """'coming' -> 'coming  —  patient says they will come...'  Blank stays blank."""
    code = str(code or "").strip()
    if not code:
        return ""
    meaning = VOCAB_MEANINGS.get(code)
    return f"{code}   —   {meaning}" if meaning else code


def flags_of(row):
    """['surgery', 'clinical'] for the flags marked YES on this row."""
    out = []
    for col, label in FLAG_COLUMNS:
        if str(row.get(col, "")).strip().upper() == "YES":
            out.append(label)
    return out


def extract_drive_file_id(link):
    """https://drive.google.com/file/d/<id>/view  ->  <id>.  '' if not found."""
    if not link:
        return ""
    m = re.search(r"/d/([A-Za-z0-9_\-]{10,})", str(link))
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=([A-Za-z0-9_\-]{10,})", str(link))
    return m.group(1) if m else ""


def strip_evidence_speaker(evidence):
    """call_verdict.py appends '  [Patient]' to the evidence.  Drop it before
    trying to find the excerpt inside the transcript."""
    return re.sub(r"\s*\[[^\]]{1,30}\]\s*$", "", str(evidence or "")).strip()


def normalise(text):
    """Lowercase, strip punctuation, collapse whitespace — for fuzzy matching
    an AI excerpt against transcript text that may differ in punctuation."""
    t = str(text or "").lower()
    t = re.sub(r"[^\w\sऀ-ॿ]+", " ", t)   # keep Devanagari
    return re.sub(r"\s+", " ", t).strip()


def wrap_line(line, width=TRANSCRIPT_WRAP):
    """Wrap one long transcript line onto several sheet rows at word bounds."""
    line = str(line or "").rstrip()
    if len(line) <= width:
        return [line]
    out, cur = [], ""
    for word in line.split(" "):
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            out.append(cur)
            cur = word
        while len(cur) > width:            # a single very long token
            out.append(cur[:width])
            cur = cur[width:]
    if cur:
        out.append(cur)
    return out


def split_transcript(text):
    """Transcript text -> the list of rows we will render, one per sheet row."""
    if not str(text or "").strip():
        return []
    rows = []
    for raw in str(text).splitlines():
        raw = raw.rstrip()
        if not raw.strip():
            continue
        rows.extend(wrap_line(raw))
        if len(rows) >= MAX_TRANSCRIPT_LINES:
            rows = rows[:MAX_TRANSCRIPT_LINES]
            rows.append("… (transcript truncated for display)")
            break
    return rows


def locate_evidence(lines, evidence):
    """Which rendered transcript lines contain the AI's evidence excerpt?

    Returns a set of 0-based indices into `lines`.  Empty set = not located,
    in which case the card SAYS SO rather than highlighting the wrong line.

    Three passes, most trustworthy first:
      1. the normalised excerpt appears inside a normalised line;
      2. a normalised line (>= 4 words) appears inside the normalised excerpt
         — this is the case where the excerpt spans several wrapped rows;
      3. best single line by word overlap, accepted only at >= 0.60 of the
         excerpt's words.

    An excerpt of fewer than 3 words is never matched at all: "ji" or "haan"
    would substring-match half the transcript and highlight the wrong line,
    which is worse than highlighting nothing.
    """
    ev = normalise(strip_evidence_speaker(evidence))
    if not ev or not lines or len(ev.split()) < 3:
        return set()

    norm = [normalise(x) for x in lines]

    hits = {i for i, n in enumerate(norm) if n and ev in n}
    if hits:
        return hits

    hits = {i for i, n in enumerate(norm)
            if n and len(n.split()) >= 4 and n in ev}
    if hits:
        return hits

    ev_words = set(ev.split())
    if len(ev_words) < 3:
        return set()
    best_i, best_score = -1, 0.0
    for i, n in enumerate(norm):
        if not n:
            continue
        overlap = len(ev_words & set(n.split())) / float(len(ev_words))
        if overlap > best_score:
            best_i, best_score = i, overlap
    return {best_i} if best_score >= 0.60 else set()


def summarise_counts(rows):
    """{section: count} over every row in the window."""
    counts = {k: 0 for k in (SEC_MISMATCH, SEC_AI_ONLY, SEC_UNCLEAR,
                             SEC_MATCH, SEC_INCOMING_NOCLAIM, SEC_SUSPECT,
                             SEC_ERROR)}
    counts[SEC_FLAGGED] = 0
    for r in rows:
        sec = classify_section(r)
        counts[sec] += 1
        if sec != SEC_ERROR and flags_of(r):
            counts[SEC_FLAGGED] += 1        # overlaps the scenario counts, by design
    return counts


def direction_counts(rows):
    """{'outgoing': n, 'incoming': n, 'other': n} — printed in the summary so
    the population a rate is measured over can never be misread again."""
    out = {"outgoing": 0, "incoming": 0, "other": 0}
    for r in rows:
        d = str(r.get("Direction", "")).strip().lower()
        if d.startswith("out"):
            out["outgoing"] += 1
        elif d.startswith("in"):
            out["incoming"] += 1
        else:
            out["other"] += 1
    return out


def match_rate(counts):
    """Match rate over EVERY judged claim, both directions (S140; staff
    file incoming outcomes since K-2).  '—' when nothing to
    measure.  Mismatch here includes Partial, deliberately: a Partial is not a
    clean match and should not flatter the number.  Suspect joins are excluded
    entirely — they are not evidence about staff accuracy either way."""
    judged = counts[SEC_MATCH] + counts[SEC_MISMATCH]
    if judged == 0:
        return "—", 0
    return f"{counts[SEC_MATCH]}/{judged}  ({round(100.0 * counts[SEC_MATCH] / judged)}%)", judged


def parse_harvest(values):
    """Read the doctor's typed answers out of an existing Verdict_Review grid.

    `values` is the raw get_all_values() list of rows.  A response row is any
    row whose machine-marker column says RESP.  Returns
    {key_token: {'outcome': str, 'note': str}} for rows where the doctor typed
    something.  Rows with both cells blank are skipped (nothing to record).
    The caller maps tokens back to Join Keys (see key_token).
    """
    out = {}
    for row in values:
        if len(row) <= COL_MACHINE_MARK:
            continue
        if str(row[COL_MACHINE_MARK]).strip() != MARKER_RESPONSE:
            continue
        key = str(row[COL_MACHINE_KEY]).strip()
        if not key:
            continue
        outcome = str(row[COL_VAL]).strip() if len(row) > COL_VAL else ""
        note = str(row[COL_VAL2]).strip() if len(row) > COL_VAL2 else ""
        if not outcome and not note:
            continue
        out[key] = {"outcome": outcome, "note": note}
    return out


def a1_col(idx0):
    """0 -> 'A', 26 -> 'AA'."""
    s, n = "", idx0 + 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# ---------------------------------------------------------------------------
# Card rendering — builds the value grid plus the formatting instructions
# ---------------------------------------------------------------------------
class Grid:
    """Accumulates rows of cell values and the formatting we want applied.

    Nothing here talks to Google.  render_all() produces a Grid; the caller
    turns it into one values_update + one batched set of format requests.
    """

    def __init__(self):
        self.rows = []
        self.band_rows = []        # section headers
        self.title_rows = []       # card titles
        self.response_rows = []    # (row_index, vocab_list)
        self.evidence_rows = []    # highlighted transcript lines
        self.transcript_rows = []  # plain transcript lines
        self.summary_rows = []
        self.groups = []           # (start_row_idx, end_row_idx) collapsed

    def add(self, label="", val="", val2="", spare="", key="", mark=""):
        row = [""] * SHEET_COLS
        row[COL_LABEL] = label
        row[COL_VAL] = val
        row[COL_VAL2] = val2
        row[COL_SPARE] = spare
        row[COL_MACHINE_KEY] = key
        row[COL_MACHINE_MARK] = mark
        self.rows.append(row)
        return len(self.rows) - 1


def render_summary(g, counts, dirs, tstats, window_days, today, generated_at,
                   forced_info=None):
    rate, judged = match_rate(counts)
    start = today - datetime.timedelta(days=window_days - 1)
    r = g.add("CALL VERDICT REVIEW",
              f"{start.isoformat()}  to  {today.isoformat()}   "
              f"({window_days}-day rolling window)")
    g.summary_rows.append(r)
    g.summary_rows.append(g.add("Generated", generated_at))
    g.summary_rows.append(g.add("Source", f"{VERDICT_TAB} (read-only) · {BUILD_VERSION}"))
    g.summary_rows.append(g.add(""))
    g.summary_rows.append(g.add("FLAGGED for clinical / safety review",
                                str(counts[SEC_FLAGGED]),
                                "Drawn at the top, whatever else they are."))
    g.summary_rows.append(g.add("Mismatches to review", str(counts[SEC_MISMATCH])))
    g.summary_rows.append(g.add("AI logged, staff didn't", str(counts[SEC_AI_ONLY])))
    g.summary_rows.append(g.add("Unclear", str(counts[SEC_UNCLEAR])))
    g.summary_rows.append(g.add("Suspect joins (do not train on these)",
                                str(counts[SEC_SUSPECT])))
    g.summary_rows.append(g.add("Matches (collapsed below)", str(counts[SEC_MATCH])))
    g.summary_rows.append(g.add("Match rate (all judged claims)", rate,
                                "Partial counts against the rate, not for it."))
    g.summary_rows.append(g.add("Calls in window: outgoing / incoming",
                                f"{dirs['outgoing']} outgoing   ·   {dirs['incoming']} incoming"
                                + (f"   ·   {dirs['other']} unrecognised direction"
                                   if dirs["other"] else "")))
    if tstats.get("empty") or tstats.get("missing"):
        g.summary_rows.append(g.add(
            "Transcripts empty or unavailable",
            f"{tstats.get('empty', 0)} empty   ·   {tstats.get('missing', 0)} unavailable",
            "A recording/transcription problem, NOT an AI failure. "
            "These land in Unclear looking like the judge failed."))
    if counts[SEC_ERROR]:
        g.summary_rows.append(g.add("Rows the judge could not process",
                                    str(counts[SEC_ERROR]),
                                    "Check the Error column in Call_Verdicts."))
    if forced_info:
        g.summary_rows.append(g.add(
            "REFEREE cards (drawn on request)",
            f"{forced_info['referee_open']} open   ·   "
            f"{forced_info['referee_done']} already answered",
            "Top band. The band shrinks as you answer — nothing is asked twice."))
        if forced_info.get("missing"):
            g.summary_rows.append(g.add(
                "Force keys NOT FOUND", str(forced_info["missing"]),
                "Named in the top band and in the run log — never dropped silently."))
        if forced_info.get("spots"):
            g.summary_rows.append(g.add(
                "Today's spot-checks",
                "   ·   ".join(forced_info["spots"]),
                "Clean matches to confirm — the daily calibration drip (D237). "
                "The digest reads this line."))
    g.add("")
    g.add("")


def render_section_header(g, section, n):
    r = g.add(f"{SECTION_TITLES[section]}      ({n})")
    g.band_rows.append(r)
    g.add("")


def render_card(g, row, transcript_text, transcript_error, prefill):
    """One patient, one screen.  Returns nothing; appends to the Grid."""
    key = str(row.get("Join Key", "")).strip()
    name = str(row.get("Patient Name", "")).strip() or "(name not on file)"
    cid = str(row.get("Clinic ID", "")).strip()
    number = str(row.get("Patient Number", "")).strip()
    direction = str(row.get("Direction", "")).strip()
    verdict = str(row.get("Verdict", "")).strip()
    conf = str(row.get("Match Confidence", "")).strip()

    title = f"■  {name}" + (f"   ·   Clinic ID {cid}" if cid else "")
    g.title_rows.append(g.add(title, f"{verdict}" + (f"   ·   match: {conf}" if conf else "")))

    if flags_of(row):
        g.add("⚑  FLAGGED",
              "This call raised a safety flag (" + ", ".join(flags_of(row))
              + "). It is drawn here whatever its verdict, so a flag can never "
                "hide inside the collapsed Matches list.")

    if classify_section(row) == SEC_SUSPECT:
        g.add("⚠  SUSPECT JOIN",
              "An OUTGOING-only follow-up code is attached to an INCOMING "
              "call. Staff could not have filed that code about this "
              "conversation, so it almost certainly belongs to a LATER "
              "outgoing call to the same number (D158). "
              "Treat the verdict as meaningless. Do not train on this row.")

    g.add("When", f"{row.get('Date','')}   {row.get('Time','')}")
    g.add("Number", number)
    g.add("Direction / Duration", f"{direction}   ·   {row.get('Duration','')}")
    g.add("Agent", str(row.get("Agent", "")).strip() or "(not recorded)")
    g.add("Staff claimed", describe_outcome(row.get("Claimed Outcome"))
          or "(nothing filed)")
    g.add("AI heard", describe_outcome(row.get("AI Outcome")) or "(no answer)")
    g.add("AI confidence", str(row.get("Confidence", "")).strip())
    g.add("Spoke with", str(row.get("Spoke With", "")).strip()
          or "(the AI could not tell — transcripts are not speaker-separated)")

    fl = flags_of(row)
    g.add("Safety flags", ", ".join(fl) if fl else "none")
    if str(row.get("Conduct Note", "")).strip():
        g.add("Conduct note", str(row.get("Conduct Note", "")).strip())

    g.add("AI reason", str(row.get("AI Reason", "")).strip())
    g.add("AI evidence", strip_evidence_speaker(row.get("Evidence")))

    rec = str(row.get("Recording Link", "")).strip()
    g.add("Recording", f'=HYPERLINK("{rec}","▶  listen to the call")' if rec
          else "(no recording link)")

    # ---- the doctor's two cells -------------------------------------------
    r = g.add("YOUR VERDICT  →",
              prefill.get("outcome", ""),
              prefill.get("note", ""),
              "", key_token(key), MARKER_RESPONSE)
    g.response_rows.append((r, vocab_for_direction(direction)))
    g.add("", "↑ pick from the dropdown", "↑ optional note (free text)")

    # ---- the transcript, collapsed ----------------------------------------
    if transcript_error:
        g.add("Transcript", f"(unavailable: {transcript_error})")
    else:
        lines = split_transcript(transcript_text)
        if not lines:
            g.add("Transcript",
                  "(EMPTY transcript — a recording/transcription problem, not "
                  "an AI failure. Answer 'transcript_bad'.)")
        else:
            hits = locate_evidence(lines, row.get("Evidence"))
            note = ("evidence highlighted below" if hits
                    else "evidence excerpt could not be located verbatim")
            g.add("Transcript", f"▸ expand to read ({len(lines)} lines) — {note}")
            first = len(g.rows)
            for i, line in enumerate(lines):
                ri = g.add("", line)
                (g.evidence_rows if i in hits else g.transcript_rows).append(ri)
            g.groups.append((first, len(g.rows)))

    g.add("")
    g.add("")


def render_match_line(g, row):
    g.add(f"{row.get('Date','')} {row.get('Time','')}",
          f"{mask_phone(row.get('Patient Number'))}   "
          f"{str(row.get('Patient Name','')).strip()}",
          f"both said: {str(row.get('AI Outcome','')).strip()}",
          str(row.get("Match Confidence", "")).strip())


def render_answered_line(g, row, prefill_entry):
    """A forced key the doctor has ALREADY answered: one line, no editable
    cell.  This is what makes a referee sitting resumable across days."""
    note = str((prefill_entry or {}).get("note", "")).strip()
    g.add(f"\u2713 answered   {row.get('Date','')} {row.get('Time','')}",
          f"{mask_phone(row.get('Patient Number'))}   "
          f"{str(row.get('Patient Name','')).strip()}",
          f"your verdict: {str((prefill_entry or {}).get('outcome','')).strip()}"
          + (f"   \u00b7   {note}" if note else ""))


def render_forced_band(g, forced_rows, spot_rows, prefill, fetched,
                       missing_keys, today):
    """The D240 band: referee keys in FILE ORDER, then today's spot-checks.
    Exempt from every per-section cap by construction — it never passes
    through by_section.  Returns the number of open (editable) cards drawn."""
    render_section_header(g, SEC_FORCED, len(forced_rows) + len(spot_rows))
    open_cards = 0
    if missing_keys:
        g.add("\u26a0  keys not found",
              f"{len(missing_keys)} supplied key(s) match no row in Call_Verdicts: "
              + ", ".join(key_token(k) for k in missing_keys[:10])
              + ("\u2026" if len(missing_keys) > 10 else ""),
              "Check force_keys.txt \u2014 each line must be an exact Join Key. "
              "Full keys are in the run log, never on this exportable tab.")
    for row in forced_rows:
        jk = str(row.get("Join Key", "")).strip()
        pf = prefill.get(jk, {})
        if is_answered(pf):
            render_answered_line(g, row, pf)
            continue
        text, err = fetched.get(jk, ("", "transcript not fetched"))
        render_card(g, row, text, err, pf)
        open_cards += 1
    for row in spot_rows:
        jk = str(row.get("Join Key", "")).strip()
        g.add("\u2605  TODAY'S SPOT-CHECK",
              f"{today.isoformat()} \u2014 a clean MATCH drawn for the daily "
              "calibration drip (D237). Confirm or overturn it like any other card.")
        text, err = fetched.get(jk, ("", "transcript not fetched"))
        render_card(g, row, text, err, prefill.get(jk, {}))
        open_cards += 1
    if not forced_rows and not spot_rows:
        g.add("", "(no forced keys and no spot-check candidates today)")
    g.add("")
    return open_cards


# ---------------------------------------------------------------------------
# Google plumbing — nothing below here runs during --selftest
# ---------------------------------------------------------------------------
def get_sheets_client():
    sa_path = require_env("GOOGLE_SA_KEY", "WA_SA_KEY")
    creds = Credentials.from_service_account_file(
        sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)


def get_drive_service():
    token_path = require_env("DRIVE_TOKEN_FILE")
    if not os.path.exists(token_path):
        sys.exit(f"ERROR: DRIVE_TOKEN_FILE not found at {token_path}. "
                 f"Exiting (code 2).")
    creds = UserCredentials.from_authorized_user_file(token_path)
    return build("drive", "v3", credentials=creds)


def download_text(drive_service, file_id):
    request = drive_service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8", errors="replace")


def read_verdicts(ws):
    """Call_Verdicts -> list of dicts.  Refuses to proceed on a header change."""
    values = ws.get_all_values()
    if not values:
        sys.exit(f"ERROR: '{VERDICT_TAB}' is empty. Nothing to review. Exiting (code 2).")
    head = values[0]
    if head != VERDICT_HEADER:
        sys.exit(
            f"ERROR: '{VERDICT_TAB}' header does not match the layout this script\n"
            f"       was built against (S123 / D152). Refusing to read it into the\n"
            f"       wrong columns. Re-check call_verdict.py's VERDICT_HEADER.\n"
            f"       Exiting (code 3).")
    return [dict(zip(head, r + [""] * (len(head) - len(r)))) for r in values[1:]]


def ensure_doctor_tab(ss, dry_run):
    """Returns the Doctor_Verdicts worksheet, or None during a dry run when the
    tab does not exist yet.  A dry run must write NOTHING -- not even a tab."""
    try:
        ws = ss.worksheet(DOCTOR_TAB)
    except gspread.exceptions.WorksheetNotFound:
        if dry_run:
            print(f"  ('{DOCTOR_TAB}' does not exist; dry run will NOT create it)",
                  flush=True)
            return None
        ws = ss.add_worksheet(title=DOCTOR_TAB, rows=2000, cols=len(DOCTOR_HEADER))
        ws.append_row(DOCTOR_HEADER, value_input_option="RAW")
        print(f"  (created '{DOCTOR_TAB}' in the doctor-only sheet)", flush=True)
        return ws
    head = ws.row_values(1)
    if head != DOCTOR_HEADER:
        sys.exit(f"ERROR: '{DOCTOR_TAB}' header is not the expected layout. "
                 f"Refusing to write. Exiting (code 3).")
    return ws


def upsert_doctor_verdicts(ws_doctor, harvested, verdict_by_key, generated_at, dry_run):
    """Write the doctor's answers into Doctor_Verdicts, keyed on Join Key.
    Existing rows are updated in place; new keys are appended.  Returns
    (n_new, n_updated, n_unchanged)."""
    if ws_doctor is None:              # dry run, tab absent: report, write nothing
        return len(harvested), 0, 0
    values = ws_doctor.get_all_values()
    head = values[0] if values else DOCTOR_HEADER
    col = {name: i for i, name in enumerate(head)}
    existing = {}
    for n, r in enumerate(values[1:], start=2):
        r = r + [""] * (len(head) - len(r))
        k = str(r[col["Join Key"]]).strip()
        if k:
            existing[k] = (n, r)

    new_rows, cells, n_updated, n_unchanged = [], [], 0, 0

    for key, ans in sorted(harvested.items()):
        src = verdict_by_key.get(key, {})
        if key in existing:
            rn, cur = existing[key]
            same = (str(cur[col["Doctor Final Outcome"]]).strip() == ans["outcome"]
                    and str(cur[col["Doctor Note"]]).strip() == ans["note"])
            if same:
                n_unchanged += 1
                continue
            n_updated += 1
            if not dry_run:
                cells.append(gspread.Cell(rn, col["Doctor Final Outcome"] + 1, ans["outcome"]))
                cells.append(gspread.Cell(rn, col["Doctor Note"] + 1, ans["note"]))
                cells.append(gspread.Cell(rn, col["Recorded At"] + 1, generated_at))
        else:
            new_rows.append([
                key,
                src.get("Date", ""), src.get("Time", ""), src.get("Direction", ""),
                src.get("Patient Number", ""), src.get("Patient Name", ""),
                src.get("Clinic ID", ""), src.get("Agent", ""),
                src.get("Claimed Outcome", ""), src.get("AI Outcome", ""),
                src.get("Verdict", ""), src.get("Match Confidence", ""),
                ans["outcome"], ans["note"],
                classify_section(src) if src else "",   # scenario, not placement
                generated_at, BUILD_VERSION,
            ])

    if not dry_run:
        if cells:
            ws_doctor.update_cells(cells, value_input_option="RAW")
        if new_rows:
            ws_doctor.append_rows(new_rows, value_input_option="RAW")

    return len(new_rows), n_updated, n_unchanged


def format_requests(sheet_id, g):
    """Every formatting instruction for the freshly-drawn Verdict_Review tab."""
    req = []

    def rng(r0, r1, c0=0, c1=SHEET_COLS):
        return {"sheetId": sheet_id, "startRowIndex": r0, "endRowIndex": r1,
                "startColumnIndex": c0, "endColumnIndex": c1}

    def fill(rows, colour, bold=False, wrap=True, text=None):
        for r in rows:
            fmt = {"backgroundColor": colour,
                   "wrapStrategy": "WRAP" if wrap else "CLIP"}
            tf = {}
            if bold:
                tf["bold"] = True
            if text:
                tf["foregroundColor"] = text
            if tf:
                fmt["textFormat"] = tf
            req.append({"repeatCell": {
                "range": rng(r, r + 1),
                "cell": {"userEnteredFormat": fmt},
                "fields": "userEnteredFormat(backgroundColor,wrapStrategy,textFormat)"}})

    for idx, width in COLUMN_WIDTHS.items():
        req.append({"updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                      "startIndex": idx, "endIndex": idx + 1},
            "properties": {"pixelSize": width}, "fields": "pixelSize"}})

    # hide the two machine columns
    req.append({"updateDimensionProperties": {
        "range": {"sheetId": sheet_id, "dimension": "COLUMNS",
                  "startIndex": COL_MACHINE_KEY, "endIndex": COL_MACHINE_MARK + 1},
        "properties": {"hiddenByUser": True}, "fields": "hiddenByUser"}})

    fill(g.summary_rows, C_SUMMARY, bold=False)
    fill(g.band_rows, C_SECTION_BAND, bold=True, text=C_SECTION_TEXT)
    fill(g.title_rows, C_CARD_TITLE, bold=True)
    fill([r for r, _ in g.response_rows], C_RESPONSE_ROW, bold=True)
    fill(g.transcript_rows, C_TRANSCRIPT)
    fill(g.evidence_rows, C_EVIDENCE_HIT, bold=True)

    # Section bands span A:D.  Card titles are NOT merged - column B carries
    # the verdict.  (A one-cell merge is an API error, so never merge A:A.)
    for r in g.band_rows:
        req.append({"mergeCells": {"range": rng(r, r + 1, 0, COL_SPARE + 1),
                                   "mergeType": "MERGE_ROWS"}})

    for r, vocab in g.response_rows:
        req.append({"setDataValidation": {
            "range": rng(r, r + 1, COL_VAL, COL_VAL + 1),
            "rule": {
                "condition": {"type": "ONE_OF_LIST",
                              "values": [{"userEnteredValue": v} for v in vocab]},
                "showCustomUi": True, "strict": False,
                "inputMessage": "Your verdict — what actually happened on this call?"}}})

    # ALL the group-creates first, THEN all the collapses.  Requests are sent
    # in chunks; if a create/collapse pair were split across two chunks the
    # collapse could arrive before its group existed.
    granges = [{"sheetId": sheet_id, "dimension": "ROWS",
                "startIndex": s, "endIndex": e} for s, e in g.groups]
    for gr in granges:
        req.append({"addDimensionGroup": {"range": gr}})
    for gr in granges:
        req.append({"updateDimensionGroup": {
            "dimensionGroup": {"range": gr, "depth": 1, "collapsed": True},
            "fields": "collapsed"}})

    # Read-only everywhere except the doctor's two cells per card.
    unprotected = [rng(r, r + 1, COL_VAL, COL_VAL2 + 1) for r, _ in g.response_rows]
    req.append({"addProtectedRange": {"protectedRange": {
        "range": {"sheetId": sheet_id},
        "description": "Read-only. Type only in the green YOUR VERDICT cells.",
        "warningOnly": False,
        "unprotectedRanges": unprotected}}})

    req.append({"updateSheetProperties": {
        "properties": {"sheetId": sheet_id,
                       "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount"}})
    return req


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# ---------------------------------------------------------------------------
# Selftest — pure logic, zero network, zero keys, zero third-party imports
# ---------------------------------------------------------------------------
def selftest():
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # --- classify_section ---------------------------------------------------
    base = {"Status": "done", "Error": ""}
    check("mismatch -> mismatch",
          classify_section(dict(base, Verdict="Mismatch", Direction="outgoing")) == SEC_MISMATCH)
    check("partial -> mismatch section",
          classify_section(dict(base, Verdict="Partial", Direction="outgoing")) == SEC_MISMATCH)
    check("match -> match",
          classify_section(dict(base, Verdict="Match", Direction="outgoing")) == SEC_MATCH)
    check("incoming no-claim with AI outcome -> a REAL gap (S140, D153 retired)",
          classify_section(dict(base, Verdict="No claim logged", Direction="incoming",
                                **{"AI Outcome": "will_come"})) == SEC_AI_ONLY)
    check("incoming no-claim without AI outcome -> unclear (symmetric with outgoing)",
          classify_section(dict(base, Verdict="No claim logged", Direction="incoming"))
          == SEC_UNCLEAR)
    check("incoming claim in incoming vocab is NORMAL, verdict stands (S140)",
          classify_section(dict(base, Verdict="Mismatch", Direction="incoming",
                                **{"Claimed Outcome": "resolved_on_call"})) == SEC_MISMATCH)
    check("K-code claim on incoming is NORMAL, Match stands (S140)",
          classify_section(dict(base, Verdict="Match", Direction="incoming",
                                **{"Claimed Outcome": "k_coming"})) == SEC_MATCH)
    check("in_-prefixed claim on incoming is NORMAL (S140)",
          classify_section(dict(base, Verdict="Match", Direction="incoming",
                                **{"Claimed Outcome": "in_no_action"})) == SEC_MATCH)
    check("legacy OUTGOING code on incoming -> suspect join (D158 signal kept)",
          classify_section(dict(base, Verdict="Mismatch", Direction="incoming",
                                **{"Claimed Outcome": "coming"})) == SEC_SUSPECT)
    check("legacy outgoing code on incoming beats even a Match verdict",
          classify_section(dict(base, Verdict="Match", Direction="incoming",
                                **{"Claimed Outcome": "dikha_chuke"})) == SEC_SUSPECT)
    check("outgoing WITH a claim is never a suspect join",
          classify_section(dict(base, Verdict="Mismatch", Direction="outgoing",
                                **{"Claimed Outcome": "coming"})) == SEC_MISMATCH)
    check("blank claim on an incoming call is not suspect",
          classify_section(dict(base, Verdict="Unclear", Direction="incoming",
                                **{"Claimed Outcome": "  "})) == SEC_UNCLEAR)
    check("outgoing no-claim + AI outcome -> ai_only",
          classify_section(dict(base, Verdict="No claim logged", Direction="outgoing",
                                **{"AI Outcome": "coming"})) == SEC_AI_ONLY)
    check("outgoing no-claim + UNCLEAR -> unclear",
          classify_section(dict(base, Verdict="No claim logged", Direction="outgoing",
                                **{"AI Outcome": UNCLEAR})) == SEC_UNCLEAR)
    check("outgoing no-claim + blank AI -> unclear",
          classify_section(dict(base, Verdict="No claim logged", Direction="outgoing",
                                **{"AI Outcome": ""})) == SEC_UNCLEAR)
    check("Unclear verdict -> unclear",
          classify_section(dict(base, Verdict="Unclear", Direction="outgoing")) == SEC_UNCLEAR)
    check("error row -> error",
          classify_section({"Status": "error", "Error": "boom", "Verdict": "Match"}) == SEC_ERROR)
    check("status not done -> error",
          classify_section({"Status": "pending", "Error": "", "Verdict": "Match"}) == SEC_ERROR)
    check("unknown verdict -> unclear (visible fail)",
          classify_section(dict(base, Verdict="Wat", Direction="outgoing")) == SEC_UNCLEAR)

    # --- window / sorting ---------------------------------------------------
    today = datetime.date(2026, 7, 8)
    check("today in window", in_window({"Date": "2026-07-08"}, today, 7))
    check("6 days back in window", in_window({"Date": "2026-07-02"}, today, 7))
    check("7 days back out of window", not in_window({"Date": "2026-07-01"}, today, 7))
    check("future date out of window", not in_window({"Date": "2026-07-09"}, today, 7))
    check("bad date kept (visible fail)", in_window({"Date": "garbage"}, today, 7))
    check("parse_row_date ok", parse_row_date({"Date": "2026-07-06"}) == datetime.date(2026, 7, 6))
    rows = [{"Date": "2026-07-06", "Time": "09:00"},
            {"Date": "2026-07-08", "Time": "15:30"},
            {"Date": "2026-07-08", "Time": "17:05"}]
    ordered = sorted(rows, key=sort_key)
    check("newest first", ordered[0]["Time"] == "17:05" and ordered[-1]["Date"] == "2026-07-06")

    # --- vocabularies -------------------------------------------------------
    check("outgoing vocab", vocab_for_direction("outgoing")[:2] == ["coming", "out_of_town"])
    check("incoming vocab", vocab_for_direction("Incoming")[0] == "resolved_on_call")
    check("vocab has UNCLEAR", UNCLEAR in vocab_for_direction("outgoing"))
    check("vocab has escape hatches", "transcript_bad" in vocab_for_direction("incoming"))
    check("no duplicate cant_communicate",
          vocab_for_direction("incoming").count("cant_communicate") == 1)
    check("describe_outcome", describe_outcome("coming").startswith("coming   —   patient says"))
    check("describe_outcome blank", describe_outcome("") == "")
    check("describe_outcome unknown code passes through", describe_outcome("zzz") == "zzz")

    # --- flags / links ------------------------------------------------------
    check("flags_of", flags_of({"Flag Surgery": "YES", "Flag Clinical": "yes",
                                "Flag Urgent": ""}) == ["surgery", "clinical"])
    check("flags_of none", flags_of({}) == [])
    check("drive id from /d/ link",
          extract_drive_file_id("https://drive.google.com/file/d/1AbC_def-123/view") == "1AbC_def-123")
    check("drive id from ?id=",
          extract_drive_file_id("https://x/open?id=1AbC_def-1234") == "1AbC_def-1234")
    check("drive id blank", extract_drive_file_id("") == "")

    # --- evidence location --------------------------------------------------
    check("strip speaker tag",
          strip_evidence_speaker("main aa raha hoon  [Patient]") == "main aa raha hoon")
    lines = ["Namaste, clinic se bol rahe hain",
             "Ji main agle hafte aa raha hoon, doctor sahab",
             "Theek hai, aa jaiye"]
    check("evidence exact-ish match",
          locate_evidence(lines, "main agle hafte aa raha hoon  [Patient]") == {1})
    check("evidence punctuation-insensitive",
          locate_evidence(lines, "Ji, main agle hafte aa raha hoon!") == {1})
    check("evidence not found -> empty",
          locate_evidence(lines, "kal operation karwana hai bilkul") == set())
    check("evidence short excerpt -> empty",
          locate_evidence(lines, "ji") == set())
    check("evidence no lines -> empty", locate_evidence([], "anything at all here") == set())
    long_ev = "Namaste clinic se bol rahe hain Ji main agle hafte aa raha hoon doctor sahab"
    check("excerpt spanning lines finds both",
          locate_evidence(lines, long_ev) == {0, 1})

    # --- transcript splitting ----------------------------------------------
    check("wrap short line", wrap_line("hello there", 20) == ["hello there"])
    w = wrap_line("a" * 250, 100)
    check("wrap long token", len(w) == 3 and all(len(x) <= 100 for x in w))
    w2 = wrap_line("word " * 60, 40)
    check("wrap words at bounds", all(len(x) <= 40 for x in w2) and len(w2) > 1)
    check("split blank transcript", split_transcript("  \n\n ") == [])
    check("split drops blank lines", split_transcript("a\n\nb") == ["a", "b"])
    big = split_transcript("\n".join(["line"] * (MAX_TRANSCRIPT_LINES + 50)))
    check("transcript capped", len(big) == MAX_TRANSCRIPT_LINES + 1
          and big[-1].startswith("…"))

    # --- summary ------------------------------------------------------------
    sample = [dict(base, Verdict="Match", Direction="outgoing"),
              dict(base, Verdict="Match", Direction="outgoing"),
              dict(base, Verdict="Match", Direction="outgoing"),
              dict(base, Verdict="Mismatch", Direction="outgoing"),
              dict(base, Verdict="No claim logged", Direction="incoming")]
    counts = summarise_counts(sample)
    check("counts match", counts[SEC_MATCH] == 3 and counts[SEC_MISMATCH] == 1)
    check("incoming no-claim now counted as a visible section, never dropped (S140)",
          counts[SEC_INCOMING_NOCLAIM] == 0 and counts[SEC_UNCLEAR] == 1)
    rate, judged = match_rate(counts)
    check("match rate 3/4 75%", rate == "3/4  (75%)" and judged == 4)
    check("match rate empty", match_rate(summarise_counts([]))[0] == "—")

    # A suspect join must not move the match rate in either direction.
    poisoned = sample + [dict(base, Verdict="Mismatch", Direction="incoming",
                              **{"Claimed Outcome": "coming"})]   # legacy code = still suspect (S140)
    pc = summarise_counts(poisoned)
    check("suspect join counted separately", pc[SEC_SUSPECT] == 1)
    check("suspect join does not touch the match rate",
          match_rate(pc)[0] == "3/4  (75%)")
    check("suspect join is not a mismatch", pc[SEC_MISMATCH] == 1)

    # --- flagged placement: a flag must never hide -----------------------------
    flagged_match = dict(base, Verdict="Match", Direction="outgoing",
                         **{"Claimed Outcome": "coming", "AI Outcome": "coming",
                            "Flag Surgery": "YES"})
    check("a flagged MATCH is still scenario=match",
          classify_section(flagged_match) == SEC_MATCH)
    check("a flagged MATCH is DRAWN in the flagged section",
          placement_section(flagged_match) == SEC_FLAGGED)
    flagged_incoming = dict(base, Verdict="No claim logged", Direction="incoming",
                            **{"Flag Clinical": "YES"})
    check("a flagged INCOMING call is drawn, not dropped",
          placement_section(flagged_incoming) == SEC_FLAGGED)
    check("an unflagged incoming no-claim is DRAWN as unclear, never dropped (S140)",
          placement_section(dict(base, Verdict="No claim logged",
                                 Direction="incoming")) == SEC_UNCLEAR)
    check("an error row is never promoted to flagged",
          placement_section({"Status": "error", "Error": "x",
                             "Flag Urgent": "YES"}) == SEC_ERROR)
    check("an unflagged mismatch stays in mismatch",
          placement_section(dict(base, Verdict="Mismatch",
                                 Direction="outgoing")) == SEC_MISMATCH)

    fc = summarise_counts(sample + [flagged_match])
    check("flag placement does not change the match count", fc[SEC_MATCH] == 4)
    check("flag placement does not change the match rate",
          match_rate(fc)[0] == "4/5  (80%)")
    check("flagged counted separately", fc[SEC_FLAGGED] == 1)
    check("flagged section is drawn first", CARD_SECTIONS[0] == SEC_FLAGGED)

    # --- key_token: the tab must never carry a phone number --------------------
    jk = "9358001234_1783322828"
    tok = key_token(jk)
    check("token is opaque", "9358001234" not in tok and "1783322828" not in tok)
    check("token is stable", key_token(jk) == tok)
    check("token is unique per key", key_token(jk) != key_token(jk + "1"))
    check("token has the vr prefix", tok.startswith("vr") and len(tok) == 16)

    dirs = direction_counts(poisoned)
    check("direction counts", dirs["outgoing"] == 4 and dirs["incoming"] == 2)
    check("unrecognised direction counted",
          direction_counts([{"Direction": "??"}])["other"] == 1)
    check("suspect_join is a card section", SEC_SUSPECT in CARD_SECTIONS)
    check("every card section has a title",
          all(sec in SECTION_TITLES for sec in CARD_SECTIONS + [SEC_MATCH]))

    # --- harvest round-trip -------------------------------------------------
    g = Grid()
    row = {"Join Key": "JK1", "Direction": "outgoing", "Patient Name": "Ram",
           "Patient Number": "9358001234", "Verdict": "Mismatch",
           "Evidence": "main aa raha hoon  [Patient]", "Date": "2026-07-06",
           "Time": "17:00", "AI Outcome": "coming", "Claimed Outcome": "problem"}
    render_card(g, row, "Ji main aa raha hoon\nTheek hai", None, {})
    check("card emits one response row", len(g.response_rows) == 1)
    check("card response row carries a machine handle",
          bool(g.rows[g.response_rows[0][0]][COL_MACHINE_KEY]))
    check("card response row marked",
          g.rows[g.response_rows[0][0]][COL_MACHINE_MARK] == MARKER_RESPONSE)
    check("card groups the transcript", len(g.groups) == 1)
    check("card highlights the evidence line", len(g.evidence_rows) == 1)

    check("card writes the TOKEN, never the join key",
          g.rows[g.response_rows[0][0]][COL_MACHINE_KEY] == key_token("JK1")
          and "JK1" not in g.rows[g.response_rows[0][0]][COL_MACHINE_KEY])
    check("card shows a Spoke with line",
          any(r[COL_LABEL] == "Spoke with" for r in g.rows))

    grid = [r[:] for r in g.rows]
    rr = g.response_rows[0][0]
    grid[rr][COL_VAL] = "coming"
    grid[rr][COL_VAL2] = "patient did come, staff misfiled"
    harvested = parse_harvest(grid)
    check("harvest returns tokens", list(harvested) == [key_token("JK1")])
    check("harvest round-trips through the token map",
          {key_token("JK1"): "JK1"}[list(harvested)[0]] == "JK1")
    check("harvest carries the typed values",
          list(harvested.values()) == [
              {"outcome": "coming", "note": "patient did come, staff misfiled"}])
    check("harvest ignores untouched cards", parse_harvest(g.rows) == {})
    check("harvest ignores non-response rows", parse_harvest([["x"] * SHEET_COLS]) == {})
    check("harvest tolerates short rows", parse_harvest([["a", "b"]]) == {})

    # --- the suspect-join banner --------------------------------------------
    g4 = Grid()
    suspect = dict(row, Direction="incoming", **{"Claimed Outcome": "coming"})
    render_card(g4, suspect, "kuch baat hui", None, {})
    check("suspect card carries the warning banner",
          any("SUSPECT JOIN" in r[COL_LABEL] for r in g4.rows))
    g5 = Grid()
    render_card(g5, dict(row, **{"Flag Surgery": "YES"}), "kuch baat", None, {})
    check("flagged card carries the flag banner",
          any("FLAGGED" in r[COL_LABEL] for r in g5.rows))
    check("unflagged card carries no flag banner",
          not any("FLAGGED" in r[COL_LABEL] for r in g.rows))
    check("a normal card carries no warning banner",
          not any("SUSPECT JOIN" in r[COL_LABEL] for r in g.rows))
    check("suspect card still gets an answer cell", len(g4.response_rows) == 1)
    check("suspect card dropdown is the incoming vocabulary",
          g4.response_rows[0][1][0] == "resolved_on_call")

    # --- prefill round-trip -------------------------------------------------
    g2 = Grid()
    render_card(g2, row, "", "drive 404", {"outcome": "coming", "note": "n"})
    rr2 = g2.response_rows[0][0]
    check("prefill restores the answer", g2.rows[rr2][COL_VAL] == "coming")
    check("prefill restores the note", g2.rows[rr2][COL_VAL2] == "n")
    check("transcript error shown, no group", len(g2.groups) == 0)

    # --- formatting requests (built offline; never sent during selftest) ----
    g3 = Grid()
    render_summary(g3, summarise_counts(sample), direction_counts(sample),
                   {"empty": 3, "missing": 1}, 7, today, "2026-07-08 03:30:00")
    check("summary reports empty transcripts",
          any("Transcripts empty" in r[COL_LABEL] for r in g3.rows))
    check("summary reports the flagged count",
          any("FLAGGED" in r[COL_LABEL] for r in g3.rows))
    render_section_header(g3, SEC_MISMATCH, 1)
    render_card(g3, row, "Ji main aa raha hoon\nTheek hai", None, {})
    reqs = format_requests(1234, g3)
    kinds = [k for r in reqs for k in r]
    check("requests include validation", "setDataValidation" in kinds)
    check("requests include protection", "addProtectedRange" in kinds)
    check("requests include group create", "addDimensionGroup" in kinds)
    check("requests include group collapse", "updateDimensionGroup" in kinds)
    check("every merge spans >1 column",
          all(r["mergeCells"]["range"]["endColumnIndex"]
              - r["mergeCells"]["range"]["startColumnIndex"] > 1
              for r in reqs if "mergeCells" in r))
    check("all group creates precede all collapses",
          max([i for i, k in enumerate(kinds) if k == "addDimensionGroup"] or [-1])
          < min([i for i, k in enumerate(kinds) if k == "updateDimensionGroup"] or [99999]))
    prot = [r for r in reqs if "addProtectedRange" in r][0]["addProtectedRange"]["protectedRange"]
    check("protection covers the whole sheet",
          set(prot["range"].keys()) == {"sheetId"})
    check("protection leaves one gap per answer row",
          len(prot["unprotectedRanges"]) == len(g3.response_rows))
    check("the unprotected gap is exactly the two answer cells",
          prot["unprotectedRanges"][0]["startColumnIndex"] == COL_VAL
          and prot["unprotectedRanges"][0]["endColumnIndex"] == COL_VAL2 + 1)
    check("machine columns hidden",
          any(r.get("updateDimensionProperties", {}).get("properties", {}).get("hiddenByUser")
              for r in reqs))

    # --- env lookup (no real secrets; values never printed) -----------------
    _saved = {k: os.environ.get(k) for k in ("ZZ_PRIMARY", "ZZ_ALIAS")}
    os.environ.pop("ZZ_PRIMARY", None)
    os.environ["ZZ_ALIAS"] = "/path/from/alias"
    check("require_env falls back to the alias",
          require_env("ZZ_PRIMARY", "ZZ_ALIAS") == "/path/from/alias")
    os.environ["ZZ_PRIMARY"] = "/path/from/primary"
    check("require_env prefers the primary name",
          require_env("ZZ_PRIMARY", "ZZ_ALIAS") == "/path/from/primary")
    for _k, _v in _saved.items():
        os.environ.pop(_k, None)
        if _v is not None:
            os.environ[_k] = _v

    # --- misc ---------------------------------------------------------------
    check("mask_phone", mask_phone("9358001234") == "******1234")
    check("mask_phone short", mask_phone("12") == "**")
    check("a1_col A", a1_col(0) == "A")
    check("a1_col G", a1_col(6) == "G")
    check("a1_col AA", a1_col(26) == "AA")
    check("verdict header is 35 wide", len(VERDICT_HEADER) == 35)
    check("doctor header has both answer columns",
          "Doctor Final Outcome" in DOCTOR_HEADER and "Doctor Note" in DOCTOR_HEADER)
    check("this script never names Call_Verdicts as a write target",
          VERDICT_TAB not in (REVIEW_TAB, DOCTOR_TAB))

    # --- D240: forced band + spot-check drip --------------------------------
    check("forced section has a title", SEC_FORCED in SECTION_TITLES)
    check("banner is honest (F-40 cured)",
          "v3" in BUILD_VERSION and "S143" in BUILD_VERSION)
    check("parse_force_file order + dedupe + comments",
          parse_force_file("k1\n# note\nk2  # trailing\n\nk1\nk3")
          == ["k1", "k2", "k3"])
    check("parse_force_file empty", parse_force_file("") == [])
    check("parse_force_file None", parse_force_file(None) == [])
    check("is_answered", is_answered({"outcome": "coming"})
          and not is_answered({}) and not is_answered(None)
          and not is_answered({"outcome": "  ", "note": "n"}))

    spool = [dict(base, Verdict="Match", Direction="outgoing",
                  **{"Join Key": f"93580012{i:02d}_17833228{i:02d}",
                     "Date": "2026-07-12", "Time": f"10:{i:02d}"})
             for i in range(20)]
    d13 = datetime.date(2026, 7, 13)
    p1 = pick_spotchecks(spool, {}, set(), d13)
    p2 = pick_spotchecks(spool, {}, set(), d13)
    check("spotchecks deterministic for a date",
          [r["Join Key"] for r in p1] == [r["Join Key"] for r in p2]
          and len(p1) == 2)
    ansd = {p1[0]["Join Key"]: {"outcome": "coming", "note": ""}}
    p4 = pick_spotchecks(spool, ansd, set(), d13)
    check("spotchecks never pick an answered call",
          p1[0]["Join Key"] not in [r["Join Key"] for r in p4] and len(p4) == 2)
    only = spool[19]["Join Key"]
    p5 = pick_spotchecks(spool, {},
                         {r["Join Key"] for r in spool[:19]}, d13)
    check("spotchecks never duplicate a forced key",
          [r["Join Key"] for r in p5] == [only])
    check("small pool: takes what exists, never crashes",
          len(pick_spotchecks(spool[:1], {}, set(), d13)) == 1)
    check("spotchecks: a mismatch is never a candidate",
          pick_spotchecks([dict(base, Verdict="Mismatch",
                                Direction="outgoing",
                                **{"Join Key": "x_1"})], {}, set(), d13) == [])
    check("spotchecks: a flagged match is never a candidate (it has a card already)",
          pick_spotchecks([dict(base, Verdict="Match", Direction="outgoing",
                                **{"Join Key": "x_2", "Flag Surgery": "YES"})],
                          {}, set(), d13) == [])

    frow = dict(base, Verdict="Match", Direction="outgoing",
                **{"Join Key": "9358001234_1783322828", "Date": "2026-07-10",
                   "Time": "11:00", "AI Outcome": "coming",
                   "Claimed Outcome": "coming"})
    fdone = dict(frow, **{"Join Key": "9358005678_1783322999"})
    pfx = {"9358005678_1783322999": {"outcome": "coming", "note": "ok"}}
    gf = Grid()
    n_open = render_forced_band(
        gf, [frow, fdone], [], pfx,
        {"9358001234_1783322828": ("Ji main aa raha hoon", None)},
        ["9111122233_1700000000"], d13)
    check("forced band: the open card gets exactly one answer cell",
          len(gf.response_rows) == 1 and n_open == 1)
    check("forced band: a MATCH forced key gets a FULL card (the v2 gap, cured)",
          any(r[COL_MACHINE_MARK] == MARKER_RESPONSE for r in gf.rows))
    check("forced band: an answered key collapses to a line, no editable cell",
          any("\u2713 answered" in r[COL_LABEL] for r in gf.rows))
    check("forced band: missing keys are named, never silently dropped",
          any("keys not found" in r[COL_LABEL] for r in gf.rows))
    check("forced band: a raw Join Key (phone) never lands on the sheet",
          not any("9111122233" in "".join(map(str, r)) for r in gf.rows))
    check("forced band header uses the forced title",
          any(SECTION_TITLES[SEC_FORCED] in str(r[COL_LABEL]) for r in gf.rows))

    gs2 = Grid()
    n_spot = render_forced_band(
        gs2, [], [frow], {},
        {"9358001234_1783322828": ("Ji main aa raha hoon", None)}, [], d13)
    check("spot-check card carries the star banner and an answer cell",
          any("SPOT-CHECK" in str(r[COL_LABEL]) for r in gs2.rows)
          and n_spot == 1 and len(gs2.response_rows) == 1)
    ge = Grid()
    check("empty band renders a friendly line, zero answer cells",
          render_forced_band(ge, [], [], {}, {}, [], d13) == 0
          and len(ge.response_rows) == 0
          and any("no forced keys" in str(r[COL_VAL]) for r in ge.rows))

    g6 = Grid()
    render_summary(g6, summarise_counts(sample), direction_counts(sample),
                   {"empty": 0, "missing": 0}, 7, today, "2026-07-13 21:00:00",
                   {"referee_open": 3, "referee_done": 2, "missing": 1,
                    "spots": ["******1234 2026-07-12 10:00 (coming)"]})
    check("summary carries the spot-check line (the digest reads this label)",
          any("Today's spot-checks" in str(r[COL_LABEL]) for r in g6.rows))
    check("summary carries the referee open/answered counts",
          any("REFEREE" in str(r[COL_LABEL]) for r in g6.rows))
    check("summary without forced_info is unchanged (old call shape still works)",
          not any("REFEREE" in str(r[COL_LABEL]) for r in g3.rows))

    print(f"\nSELFTEST: {passed} passed, {failed} failed "
          f"({passed + failed} checks)")
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Verdict Analysis Layer (Stage 3b)")
    ap.add_argument("--selftest", action="store_true",
                    help="offline logic checks; no keys, no network")
    ap.add_argument("--dry-run", action="store_true",
                    help="read everything, print the plan, write nothing")
    ap.add_argument("--days", type=int, default=DEFAULT_WINDOW_DAYS,
                    help=f"rolling window in days (default {DEFAULT_WINDOW_DAYS})")
    ap.add_argument("--no-transcripts", action="store_true",
                    help="skip transcript download and row-groups")
    ap.add_argument("--force-file", default=None,
                    help="file of Join Keys to force-draw as full cards "
                         f"(when omitted, {FORCE_FILE_DEFAULT} is used IF it exists)")
    ap.add_argument("--force-keys", default="",
                    help="comma-separated Join Keys to force-draw (added to the file's)")
    ap.add_argument("--no-spotchecks", action="store_true",
                    help="skip the daily 2 spot-check cards (D240 escape hatch)")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if args.days < 1 or args.days > 90:
        sys.exit("ERROR: --days must be between 1 and 90 "
                 "(90 = the raw-transcript purge limit). Exiting (code 2).")

    global gspread, Credentials, UserCredentials, build, MediaIoBaseDownload
    import gspread as _gs
    from google.oauth2.service_account import Credentials as _C
    from google.oauth2.credentials import Credentials as _UC
    from googleapiclient.discovery import build as _b
    from googleapiclient.http import MediaIoBaseDownload as _MD
    gspread, Credentials, UserCredentials = _gs, _C, _UC
    build, MediaIoBaseDownload = _b, _MD

    load_env()
    audit_id = os.environ.get("AUDIT_SHEET_ID", DEFAULT_AUDIT_SHEET_ID)
    now = datetime.datetime.now(IST)
    today = now.date()
    generated_at = now.strftime("%Y-%m-%d %H:%M:%S")

    print(f"{BUILD_VERSION}")
    print(f"Run at {generated_at} IST · window {args.days} day(s)"
          + ("  · DRY RUN (writes nothing)" if args.dry_run else ""))

    gc = get_sheets_client()
    ss = gc.open_by_key(audit_id)

    # ---- read the proven verdict data (never written to) -------------------
    ws_verdicts = ss.worksheet(VERDICT_TAB)
    all_rows = read_verdicts(ws_verdicts)
    print(f"Read {len(all_rows)} rows from '{VERDICT_TAB}' (header verified).")

    rows = [r for r in all_rows if in_window(r, today, args.days)]
    print(f"{len(rows)} rows fall inside the rolling window.")
    verdict_by_key = {str(r.get("Join Key", "")).strip(): r
                      for r in all_rows if str(r.get("Join Key", "")).strip()}

    # ---- STEP 1: HARVEST before anything is destroyed ----------------------
    ws_doctor = ensure_doctor_tab(ss, args.dry_run)
    # The tab stores an opaque token, not the Join Key.  Rebuild the map from
    # Call_Verdicts (already in memory) to turn harvested tokens back into keys.
    token_map = {key_token(jk): jk for jk in verdict_by_key}
    harvested = {}
    try:
        ws_review = ss.worksheet(REVIEW_TAB)
        by_token = parse_harvest(ws_review.get_all_values())
        unknown = [t for t in by_token if t not in token_map]
        if unknown:
            print(f"  WARNING: {len(unknown)} typed answer(s) carry a token with no "
                  f"matching row in '{VERDICT_TAB}'. They are NOT discarded silently — "
                  f"they are skipped and reported here. Nothing is being deleted yet.")
            sys.exit("ERROR: refusing to redraw while typed answers cannot be "
                     "matched back to a verdict row. Exiting (code 4).")
        harvested = {token_map[t]: v for t, v in by_token.items()}
    except gspread.exceptions.WorksheetNotFound:
        ws_review = None
        print(f"  ('{REVIEW_TAB}' does not exist yet — first run, nothing to harvest)")

    if harvested:
        n_new, n_upd, n_same = upsert_doctor_verdicts(
            ws_doctor, harvested, verdict_by_key, generated_at, args.dry_run)
        print(f"Harvested {len(harvested)} typed answer(s) -> '{DOCTOR_TAB}': "
              f"{n_new} new, {n_upd} updated, {n_same} unchanged"
              + ("  [dry run: not written]" if args.dry_run else ""))
    else:
        print("No typed answers to harvest.")

    # Everything the doctor has EVER answered, so cards come back pre-filled.
    prefill = {}
    if ws_doctor is not None:
        for r in ws_doctor.get_all_values()[1:]:
            r = r + [""] * (len(DOCTOR_HEADER) - len(r))
            k = str(r[DOCTOR_HEADER.index("Join Key")]).strip()
            if k:
                prefill[k] = {
                    "outcome": str(r[DOCTOR_HEADER.index("Doctor Final Outcome")]).strip(),
                    "note": str(r[DOCTOR_HEADER.index("Doctor Note")]).strip()}
    for k, v in harvested.items():
        prefill[k] = v

    # ---- D240: resolve the forced key list (referee sitting) ----------------
    if args.force_file and not os.path.exists(args.force_file):
        sys.exit(f"ERROR: --force-file {args.force_file} does not exist. "
                 "Exiting (code 5).")
    force_path = args.force_file or (FORCE_FILE_DEFAULT
                                     if os.path.exists(FORCE_FILE_DEFAULT) else None)
    force_keys = []
    if force_path:
        with open(force_path, "r", encoding="utf-8") as fh:
            force_keys = parse_force_file(fh.read())
        print(f"Force file: {force_path} \u2014 {len(force_keys)} key(s).")
    for k in parse_force_file(args.force_keys.replace(",", "\n")):
        if k not in force_keys:
            force_keys.append(k)

    forced_rows, missing_keys = [], []
    for k in force_keys:
        row = verdict_by_key.get(k)   # ALL rows: a referee key may pre-date the window
        if row is not None:
            forced_rows.append(row)
        else:
            missing_keys.append(k)
    if missing_keys:
        print(f"  WARNING: {len(missing_keys)} forced key(s) match no row in "
              f"'{VERDICT_TAB}': {', '.join(missing_keys)}")

    spot_rows = [] if args.no_spotchecks else pick_spotchecks(
        rows, prefill,
        {str(r.get("Join Key", "")).strip() for r in forced_rows}, today)
    n_done = sum(1 for r in forced_rows
                 if is_answered(prefill.get(str(r.get("Join Key", "")).strip())))
    print(f"Forced band: {len(forced_rows)} referee key(s) "
          f"({n_done} already answered), {len(spot_rows)} spot-check(s)"
          + (f", {len(missing_keys)} key(s) NOT FOUND" if missing_keys else "") + ".")

    # ---- STEP 2: build the new grid (still nothing destroyed) --------------
    counts = summarise_counts(rows)
    dirs = direction_counts(rows)
    by_section = {s: [] for s in (SEC_FLAGGED, SEC_MISMATCH, SEC_AI_ONLY,
                                  SEC_UNCLEAR, SEC_SUSPECT, SEC_MATCH)}
    drawn_forced = {str(r.get("Join Key", "")).strip()
                    for r in forced_rows + spot_rows}
    for r in rows:
        if str(r.get("Join Key", "")).strip() in drawn_forced:
            continue   # D240: one call, one answer cell \u2014 never drawn twice
        s = placement_section(r)
        if s in by_section:
            by_section[s].append(r)
    for s in by_section:
        by_section[s].sort(key=sort_key)
        if len(by_section[s]) > MAX_CARDS_PER_SECTION:
            print(f"  (capping section '{s}' at {MAX_CARDS_PER_SECTION} rows)")
            by_section[s] = by_section[s][:MAX_CARDS_PER_SECTION]

    n_cards = sum(len(by_section[s]) for s in CARD_SECTIONS)
    print(f"Window: {dirs['outgoing']} outgoing, {dirs['incoming']} incoming"
          + (f", {dirs['other']} unrecognised direction" if dirs["other"] else ""))
    print(f"Cards to draw: {n_cards}  "
          f"(flagged {len(by_section[SEC_FLAGGED])}, "
          f"mismatch {len(by_section[SEC_MISMATCH])}, "
          f"ai-only {len(by_section[SEC_AI_ONLY])}, "
          f"unclear {len(by_section[SEC_UNCLEAR])}, "
          f"suspect-join {len(by_section[SEC_SUSPECT])})"
          f"  ·  matches shown as lines {len(by_section[SEC_MATCH])}  ·  "
          f"incoming-no-claim {counts[SEC_INCOMING_NOCLAIM]} (not shown)")
    print(f"Scenario counts (unchanged by flag placement): "
          f"mismatch {counts[SEC_MISMATCH]}, matches {counts[SEC_MATCH]}, "
          f"flagged {counts[SEC_FLAGGED]}")
    print(f"Match rate (outgoing with a claim, suspect joins excluded): "
          f"{match_rate(counts)[0]}")

    drive = None if args.no_transcripts else get_drive_service()
    cache = {}

    def transcript_for(row):
        if args.no_transcripts:
            return "", "transcripts skipped (--no-transcripts)"
        fid = extract_drive_file_id(row.get("Transcript Link"))
        if not fid:
            return "", "no transcript link on this row"
        if fid in cache:
            return cache[fid]
        try:
            text = download_text(drive, fid)
            cache[fid] = (text, None)
        except Exception as e:                     # noqa: BLE001 - report, never crash the tab
            cache[fid] = ("", f"{type(e).__name__}: {str(e)[:80]}")
        return cache[fid]

    # Fetch every card transcript FIRST, so the summary can report transcript
    # quality before a single card is drawn.  An empty transcript is a recording
    # problem masquerading as an AI failure; the doctor should see the count.
    fetched, tstats = {}, {"empty": 0, "missing": 0}
    for section in CARD_SECTIONS:
        for row in by_section[section]:
            jk = str(row.get("Join Key", "")).strip()
            text, err = transcript_for(row)
            fetched[jk] = (text, err)
            if err:
                tstats["missing"] += 1
            elif not str(text).strip():
                tstats["empty"] += 1
    # D240: the forced band's OPEN cards need transcripts too (answered lines
    # do not \u2014 skipping them is what makes a shrinking band cheap to redraw).
    band_card_rows = [r for r in forced_rows
                      if not is_answered(prefill.get(
                          str(r.get("Join Key", "")).strip()))] + spot_rows
    for row in band_card_rows:
        jk = str(row.get("Join Key", "")).strip()
        if jk in fetched:
            continue
        text, err = transcript_for(row)
        fetched[jk] = (text, err)
        if err:
            tstats["missing"] += 1
        elif not str(text).strip():
            tstats["empty"] += 1
    print(f"Transcripts: {len(fetched) - tstats['empty'] - tstats['missing']} usable, "
          f"{tstats['empty']} empty, {tstats['missing']} unavailable.")

    spots_desc = [f"{mask_phone(r.get('Patient Number'))} "
                  f"{r.get('Date','')} {r.get('Time','')} "
                  f"({str(r.get('AI Outcome','')).strip()})" for r in spot_rows]
    forced_info = None
    if force_keys or spot_rows or missing_keys:
        forced_info = {"referee_open": len(forced_rows) - n_done,
                       "referee_done": n_done,
                       "missing": len(missing_keys),
                       "spots": spots_desc}

    g = Grid()
    render_summary(g, counts, dirs, tstats, args.days, today, generated_at,
                   forced_info)
    open_forced = render_forced_band(g, forced_rows, spot_rows, prefill,
                                     fetched, missing_keys, today)
    if forced_rows or spot_rows:
        print(f"  \u00b7 forced band: {open_forced} open card(s), "
              f"{n_done} answered line(s).")
    for section in CARD_SECTIONS:
        render_section_header(g, section, len(by_section[section]))
        if not by_section[section]:
            g.add("", "(nothing in this section — good)")
            g.add("")
            continue
        for row in by_section[section]:
            jk = str(row.get("Join Key", "")).strip()
            text, err = fetched[jk]
            render_card(g, row, text, err, prefill.get(jk, {}))
            print(f"  · {section:12s} {row.get('Date','')} {row.get('Time','')} "
                  f"{mask_phone(row.get('Patient Number'))} "
                  f"{str(row.get('Verdict','')).strip()}")

    render_section_header(g, SEC_MATCH, len(by_section[SEC_MATCH]))
    for row in by_section[SEC_MATCH]:
        render_match_line(g, row)
    if not by_section[SEC_MATCH]:
        g.add("", "(no clean matches in this window)")

    print(f"Grid built: {len(g.rows)} rows, {len(g.response_rows)} answer cells, "
          f"{len(g.groups)} transcript groups, {len(g.evidence_rows)} evidence lines.")

    if args.dry_run:
        print("\nDRY RUN — nothing written. Verdict_Review left exactly as it was.")
        return

    # ---- STEP 3: destroy and redraw (only now, harvest is safely stored) ---
    if ws_review is not None:
        ss.del_worksheet(ws_review)
    ws = ss.add_worksheet(title=REVIEW_TAB,
                          rows=max(len(g.rows) + 20, 100), cols=SHEET_COLS)

    ss.values_update(
        f"'{REVIEW_TAB}'!A1",
        params={"valueInputOption": "USER_ENTERED"},
        body={"values": g.rows})

    reqs = format_requests(ws.id, g)
    for batch in chunked(reqs, 200):
        ss.batch_update({"requests": batch})

    print(f"\nRedrew '{REVIEW_TAB}': {len(g.rows)} rows, {n_cards} cards, "
          f"read-only except the {len(g.response_rows)} green answer cells.")
    print(f"'{DOCTOR_TAB}' holds your refereed record. "
          f"'{VERDICT_TAB}' was not touched.")
    print("Done. \u20b90 \u2014 no AI calls were made.")


if __name__ == "__main__":
    main()
