#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_digest.py -- v1.0-S142 -- D236 digest layer (Dr. Manoj Agarwal Clinic)

WHAT THIS IS
  The doctor's two daily emails, built from data the pipeline already writes.
  This script READS everything and WRITES NOTHING SHARED (D236). It owns no
  tab, it appends no row, it never calls the Sheets append API (D235).

TWO MODES
  --pulse    11:00 IST morning pulse. ALWAYS SENDS (owner amendment, S142):
             opens with ALL of the morning's calls (judged first, then
             awaiting-verdict), then a short "needs attention" list.
             No AI call. Zero rupees.
  --digest   21:30 IST full digest: day-in-one-line, the day's numbers,
             worst-first review list with recording links, the day's 2 MATCH
             spot-checks for the doctor to referee (D237 drip; answers land
             in Verdict_Review -> Doctor_Verdicts and count toward D191),
             at most ONE data-backed suggestion. One small AI call (Haiku)
             writes the summary line + suggestion from AGGREGATE COUNTS ONLY
             -- no names, no numbers, no transcripts ever leave the sheet.
             Degrades to a computed line if the AI key is absent or the call
             fails; the email still goes out.

OTHER MODES
  --test      send a short test email now (subject "DIGEST TEST ...").
  --dry-run   build the email and print it to stdout; send nothing,
              read-only against the live sheets.
  --selftest  offline unit tests; no network, no sheets, no email.

DATA SOURCES (read-only)
  Audit sheet  (AUDIT_SHEET_ID .. default the doctor-only audit book)
     Call_Verdicts    -- one row per judged call (35 cols, v2.1 layout)
     Doctor_Verdicts  -- the doctor's referee answers (D191 progress)
  Tracker sheet (TRACKER_SHEET_ID .. default the Clinic Callback Tracker)
     Call_Durations    -- every captured call (hook v3.x, 14 cols)
     Followup_Outcomes -- every staff tap/log (18 cols)

DELIVERY
  Gmail SMTP (smtp.gmail.com:587 STARTTLS), FROM the clinic account,
  TO the owner's personal Gmail. Same proven path as the attendance mailer.

ENV (/root/wa/.env -- same loader pattern as the other stages)
  GOOGLE_SA_KEY        (required; falls back to WA_SA_KEY) service-acct JSON
  TRACKER_SHEET_ID     (optional override)
  AUDIT_SHEET_ID       (optional override)
  DIGEST_SMTP_USER     (optional; default drmka.ortho@gmail.com)
  DIGEST_SMTP_PASS     (required to send; Gmail APP password, 16 chars)
  DIGEST_TO            (optional; default drmanojkragarwal@gmail.com)
  ANTHROPIC_API_KEY    (optional; digest-mode AI line. Absent = fallback.)
  AI_DIGEST_MODEL      (optional; default claude-haiku-4-5)

EXIT CODES
  0 sent / dry-run OK      2 config error      3 send failure

CRON (installed at S142)
  0 11 * * *  /root/wa/venv/bin/python3 /root/wa/recordings-archive/daily_digest.py --pulse  >> /root/wa/recordings-archive/digest_cron.log 2>&1
  30 21 * * * /root/wa/venv/bin/python3 /root/wa/recordings-archive/daily_digest.py --digest >> /root/wa/recordings-archive/digest_cron.log 2>&1

Version history
  v1.4-S145  F-44: the "talked, no recording" fault detector now also reads
             the call's top-level status. A call MyOperator marks
             missed/voicemail is labelled "missed -- no recording expected"
             (NOT an alert) -- its ring/hold seconds are no longer mistaken
             for a conversation.
  v1.2-S142  owner-directed, same day: every unjudged call now carries an
             automatic REASON (not answered / too short / in pipeline /
             transcribed-verdict due / "talked, no recording"). The last one
             is a fault detector: a connected call with >=15 s of talk, older
             than 30 min, with no transcript, goes into Needs Attention in
             both emails. Keyed on customer_result + customer_talk_duration
             (values verified from the live tab). Reads Call_Transcripts now
             (still read-only). Attention times zero-padded.
  v1.1-S142  dry-run fixes, same session: (1) judged<->pending join now uses
             the real key shapes -- verdict Join Key is mobile10_epochSECONDS,
             duration client_ref_id is mobile10-epoch+hex -- matched by phone
             + epoch (<=300s) with a phone + time-window (<=6 min) fallback for
             IN- rows; (2) Call_Durations rows deduped keep-last per ref;
             (3) verdict times zero-padded so 08:58 sorts before 10:00.
  v1.0-S142  first build. D236 daily layer only; the weekly Sunday section
             (lead funnel, staff scoreboard) is designed but NOT built --
             it rides the D226 expiry detector and lands on a later VPS touch.
"""

import argparse
import datetime
import html
import json
import os
import re
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BUILD_VERSION = "v1.4-S145"
ENV_PATH = "/root/wa/.env"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

DEFAULT_TRACKER_SHEET_ID = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"
DEFAULT_AUDIT_SHEET_ID = "1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ"

VERDICT_TAB = "Call_Verdicts"
DOCTOR_TAB = "Doctor_Verdicts"
DURATIONS_TAB = "Call_Durations"
OUTCOMES_TAB = "Followup_Outcomes"
TRANSCRIPTS_TAB = "Call_Transcripts"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
DEFAULT_SMTP_USER = "drmka.ortho@gmail.com"
DEFAULT_TO = "drmanojkragarwal@gmail.com"

DEFAULT_MODEL = "claude-haiku-4-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
AI_MAX_TOKENS = 400
AI_TIMEOUT_S = 60

REVIEW_LIST_CAP = 12          # worst-first list, 21:30
MORNING_LIST_CAP = 40         # all-morning-calls list, 11:00
REVIEW_TAB = "Verdict_Review"           # read-only here; verdict_review.py owns it
SPOTLINE_LABEL = "Today's spot-checks"  # the summary row v3 writes (D240)
MIN_TALK_S = 15               # below this, a "conversation" is a blip
PIPELINE_GRACE_MIN = 30       # age before a missing transcript is suspicious
# F-44: top-level (webhook) status values that mean nobody actually talked, so
# no recording exists or is expected -- never a "lost conversation" alert.
MISSED_STATUSES = ("missed", "voicemail")
D191_TARGET = 100             # doctor-refereed cards target

# Verdict vocabulary as call_verdict.py writes it (verified from the artefact).
V_MATCH = "Match"
V_MISMATCH = "Mismatch"
V_PARTIAL = "Partial"
V_NOCLAIM = "No claim logged"
V_UNCLEAR = "Unclear"

# Worst-first severity: lower = shown first. Safety before honesty problems.
FLAG_SEVERITY = [
    ("Flag Urgent", "URGENT"),
    ("Flag PostOp", "POST-OP"),
    ("Flag Clinical", "CLINICAL"),
    ("Flag Surgery", "SURGERY"),
    ("Flag Complaint", "COMPLAINT"),
    ("Flag Conduct", "CONDUCT"),
]


# ---------------------------------------------------------------------------
# .env loader -- same pattern as the other stages
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
            os.environ.setdefault(key.strip(), val.strip())


def env(name, default=""):
    return (os.environ.get(name) or default).strip()


# ---------------------------------------------------------------------------
# Small pure helpers (everything below here is selftested)
# ---------------------------------------------------------------------------
def truthy_flag(v):
    """Sheet flag cells arrive as 'TRUE'/'FALSE'/''/'1'... normalise."""
    return str(v).strip().upper() in ("TRUE", "1", "YES", "Y")


def fmt_dur(seconds):
    """'87' -> '1:27'; blanks / junk -> '-'."""
    try:
        s = int(float(str(seconds).strip()))
    except (ValueError, TypeError):
        return "-"
    if s < 0:
        return "-"
    return "%d:%02d" % (s // 60, s % 60)


def parse_when(s):
    """Followup_Outcomes 'When' = 'yyyy-MM-dd HH:mm' -> (date_str, time_str)."""
    s = str(s).strip()
    if len(s) >= 16 and s[4] == "-" and s[10] == " ":
        return s[:10], s[11:16]
    return "", ""


def parse_ended_ist(s):
    """Call_Durations ended_at_ist = 'YYYY-MM-DDTHH:MM:SS+05:30'
    -> (date_str, time_str) or ('','')."""
    s = str(s).strip()
    if len(s) >= 16 and s[4] == "-" and s[10] == "T":
        return s[:10], s[11:16]
    return "", ""


def dir_arrow(direction):
    d = str(direction).strip().lower()
    if d == "incoming":
        return "IN "
    if d == "outgoing":
        return "OUT"
    return "?  "


def dur_row_direction(client_ref_id):
    """Call_Durations has no Direction column: IN-<session> rows are incoming
    (hook v3), everything else is a console-dialled outgoing call."""
    return "incoming" if str(client_ref_id).strip().startswith("IN-") else "outgoing"


def pad_time(t):
    """'8:58' -> '08:58' (verdict Time cells arrive unpadded)."""
    t = str(t).strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", t)
    if not m:
        return t
    return "%02d:%s" % (int(m.group(1)), m.group(2))


JOIN_RE = re.compile(r"^(\d{10})_(\d{9,12})$")     # verdict Join Key shape
REF_RE = re.compile(r"^(\d{10})-(\d{10})")          # OBD client_ref_id shape


def parse_join_key(jk):
    """'9917656698_1783916119' -> ('9917656698', 1783916119) or None."""
    m = JOIN_RE.match(str(jk or "").strip())
    return (m.group(1), int(m.group(2))) if m else None


def parse_client_ref(ref):
    """'9917656698-178391611958e8' -> ('9917656698', 1783916119) or None
    (IN-<session> rows and odd shapes return None)."""
    m = REF_RE.match(str(ref or "").strip())
    return (m.group(1), int(m.group(2))) if m else None


def hhmm_to_min(t):
    t = pad_time(t)
    m = re.match(r"^(\d{2}):(\d{2})$", t)
    return (int(m.group(1)) * 60 + int(m.group(2))) if m else None


def dedupe_keep_last(durations):
    """Call_Durations can hold >1 row per ref (upsert history / backfill);
    keep the LAST occurrence of each client_ref_id, original order."""
    byref, order = {}, []
    for i, p in enumerate(durations):
        r = str(p.get("client_ref_id", "")).strip() or ("row#%d" % i)
        if r not in byref:
            order.append(r)
        byref[r] = p
    return [byref[r] for r in order]


def duration_covered(dur_row, joined_refs, vpe, vphone_min):
    """True if a judged verdict row already represents this duration row.
    Match order: exact ref -> phone+epoch (<=300 s, dial vs recording start)
    -> phone + time window (<=6 min, for IN- rows / unparsable refs).
    Known limit: two calls to the same number inside 6 min may fold into one
    pulse line -- both still appear individually once judged."""
    ref = str(dur_row.get("client_ref_id", "")).strip()
    if ref in joined_refs:
        return True
    pe = parse_client_ref(ref)
    if pe:
        for p, e in vpe:
            if p == pe[0] and abs(e - pe[1]) <= 300:
                return True
    phone = (pe[0] if pe else str(dur_row.get("phone10", "")).strip())
    if phone:
        _d, t = parse_ended_ist(dur_row.get("ended_at_ist", ""))
        tm = hhmm_to_min(t)
        if tm is not None:
            for vm in vphone_min.get(phone, []):
                if abs(vm - tm) <= 6:
                    return True
    return False


def classify_pending(dur_row, now_ist, t_pe, t_phone_min):
    """Why is this captured call not judged? -> (reason_text, is_alert).
    t_pe: [(phone, epoch)] from Call_Transcripts join keys;
    t_phone_min: {phone: [minutes]} fallback for IN- rows."""
    result = str(dur_row.get("customer_result", "")).strip().lower()
    try:
        talk = int(float(str(dur_row.get("customer_talk_duration", "")).strip() or 0))
    except (ValueError, TypeError):
        talk = 0
    status = str(dur_row.get("status", "")).strip().lower()
    if status in MISSED_STATUSES:
        # F-44: provider marked this missed/voicemail. Ring/hold seconds are
        # not a conversation and no recording is expected -- never an alert.
        return "missed — no recording expected", False
    if result == "not_answered" or (talk <= 0 and result not in ("connected", "answered")):
        return "not answered", False
    if talk < MIN_TALK_S:
        return "too short to judge (%ds talk)" % talk, False
    # a real conversation: does a transcript exist?
    ref = str(dur_row.get("client_ref_id", "")).strip()
    pe = parse_client_ref(ref)
    phone = pe[0] if pe else str(dur_row.get("phone10", "")).strip()
    _d, t = parse_ended_ist(dur_row.get("ended_at_ist", ""))
    tm = hhmm_to_min(t)
    has_transcript = False
    if pe:
        has_transcript = any(p == pe[0] and abs(e - pe[1]) <= 300 for p, e in t_pe)
    if not has_transcript and phone and tm is not None:
        has_transcript = any(abs(vm - tm) <= 6 for vm in t_phone_min.get(phone, []))
    if has_transcript:
        return "transcribed — verdict due", False
    # no transcript: fresh = in flight; old = the pipeline lost a conversation
    age_min = None
    if tm is not None:
        age_min = (now_ist.hour * 60 + now_ist.minute) - tm
    if age_min is None or 0 <= age_min <= PIPELINE_GRACE_MIN:
        return "in pipeline", False
    return "⚠ talked %ds, no recording" % talk, True


def rows_as_dicts(values):
    """gspread get_all_values() -> list of dicts keyed by the header row."""
    if not values:
        return []
    head = [str(h).strip() for h in values[0]]
    out = []
    for raw in values[1:]:
        if not any(str(c).strip() for c in raw):
            continue
        rec = {}
        for i, h in enumerate(head):
            rec[h] = raw[i] if i < len(raw) else ""
        out.append(rec)
    return out


def verdict_severity(vrow):
    """(sort_key, label) -- lower key = worse = listed first.
    Flagged rows come before plain mismatches; unflagged non-mismatch = None."""
    for rank, (col, label) in enumerate(FLAG_SEVERITY):
        if truthy_flag(vrow.get(col, "")):
            return rank, label
    if str(vrow.get("Verdict", "")).strip() == V_MISMATCH:
        return len(FLAG_SEVERITY), "MISMATCH"
    return None


def bucket_counts(vrows):
    """Verdict bucket tally for a list of verdict rows."""
    c = {V_MATCH: 0, V_MISMATCH: 0, V_PARTIAL: 0, V_NOCLAIM: 0, V_UNCLEAR: 0,
         "other": 0, "in": 0, "out": 0, "flagged": 0}
    for r in vrows:
        v = str(r.get("Verdict", "")).strip()
        c[v if v in c else "other"] += 1
        d = str(r.get("Direction", "")).strip().lower()
        if d == "incoming":
            c["in"] += 1
        elif d == "outgoing":
            c["out"] += 1
        if any(truthy_flag(r.get(col, "")) for col, _ in FLAG_SEVERITY):
            c["flagged"] += 1
    return c


def find_spotcheck_line(values):
    """v1.3 (S143): the digest no longer picks its own spot-checks.
    verdict_review.py v3 is the ONE DECIDER — it picks, marks the cards in the
    top band, and writes a summary row labelled "Today's spot-checks".  This
    reads that row from the tab's first rows.  Returns "" when absent (e.g. the
    21:00 redraw has not run), and the email then simply points at the band."""
    for r in values or []:
        if r and str(r[0]).strip() == SPOTLINE_LABEL:
            return str(r[1]).strip() if len(r) > 1 else ""
    return ""


def worst_first(vrows, cap=REVIEW_LIST_CAP):
    """Rows needing the doctor, safety-first, capped."""
    tagged = []
    for r in vrows:
        sev = verdict_severity(r)
        if sev is not None:
            tagged.append((sev[0], sev[1], r))
    tagged.sort(key=lambda t: (t[0], str(t[2].get("Time", ""))))
    return [(label, r) for _, label, r in tagged[:cap]]


def who(vrow):
    """'Name (9358001234)' or whichever half exists."""
    name = str(vrow.get("Patient Name", "")).strip()
    num = str(vrow.get("Patient Number", "")).strip()
    if name and num:
        return "%s (%s)" % (name, num)
    return name or num or "unknown caller"


def esc(s):
    return html.escape(str(s), quote=True)


def link(url, text):
    u = str(url).strip()
    if not u.lower().startswith("http"):
        return esc(text)
    return '<a href="%s">%s</a>' % (esc(u), esc(text))


def computed_summary_line(c, staff_logged):
    """The no-AI fallback day-in-one-line. Plain, honest, cheap."""
    total = c["in"] + c["out"]
    bits = ["%d calls (%d in / %d out)" % (total, c["in"], c["out"]),
            "%d staff-logged" % staff_logged]
    if c[V_MISMATCH]:
        bits.append("%d mismatch" % c[V_MISMATCH])
    if c["flagged"]:
        bits.append("%d safety-flagged" % c["flagged"])
    if c[V_NOCLAIM]:
        bits.append("%d calls nobody logged" % c[V_NOCLAIM])
    return " · ".join(bits) + "."


def pulse_subject(day_disp, n_calls, n_attention):
    if n_calls == 0:
        return "Clinic pulse — %s — no calls yet this morning" % day_disp
    tail = ("· %d need attention" % n_attention) if n_attention else "· all clean"
    return "Clinic pulse — %s — %d calls this morning %s" % (day_disp, n_calls, tail)


def digest_subject(day_disp, c):
    total = c["in"] + c["out"]
    return ("Clinic digest — %s — %d calls · %d flagged · %d mismatch"
            % (day_disp, total, c["flagged"], c[V_MISMATCH]))


# ---------------------------------------------------------------------------
# HTML rendering (tables kept simple; every value escaped)
# ---------------------------------------------------------------------------
CSS = "font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222;"
TH = ('style="text-align:left;padding:4px 10px 4px 0;border-bottom:1px solid #999;'
      'font-size:12px;color:#555;"')
TD = 'style="padding:4px 10px 4px 0;border-bottom:1px solid #eee;vertical-align:top;"'


def h_section(title):
    return ('<h3 style="margin:18px 0 6px 0;font-size:15px;color:#0a4d8c;">%s</h3>'
            % esc(title))


def call_line_cells(r):
    """One judged call -> table cells (pulse morning list)."""
    return [pad_time(r.get("Time", "")),
            dir_arrow(r.get("Direction", "")),
            who(r),
            fmt_dur(r.get("Duration", "")),
            str(r.get("Claimed Outcome", "")).strip() or "—",
            str(r.get("AI Outcome", "")).strip() or "—",
            str(r.get("Verdict", "")).strip() or "—"]


def render_table(headers, rows_of_cells):
    out = ['<table style="border-collapse:collapse;">', "<tr>"]
    for h in headers:
        out.append("<th %s>%s</th>" % (TH, esc(h)))
    out.append("</tr>")
    for cells in rows_of_cells:
        out.append("<tr>" + "".join(
            "<td %s>%s</td>" % (TD, c if str(c).startswith("<a ") else esc(c))
            for c in cells) + "</tr>")
    out.append("</table>")
    return "".join(out)


def footer(refereed, note=""):
    prog = "Doctor referee progress: %d / %d cards (D191)." % (refereed, D191_TARGET)
    extra = (" " + esc(note)) if note else ""
    return ('<p style="margin-top:22px;font-size:11px;color:#888;">%s%s<br>'
            "daily_digest.py %s · generated %s IST · reads only, writes nothing.</p>"
            % (esc(prog), extra, esc(BUILD_VERSION),
               datetime.datetime.now(IST).strftime("%d %b %Y %H:%M")))


def build_pulse_email(day_disp, judged_today, pending_rows, attention, refereed):
    """11:00 -- ALL morning calls first (owner amendment S142), then attention."""
    n_calls = len(judged_today) + len(pending_rows)
    parts = ['<div style="%s">' % CSS]
    parts.append(h_section("All calls this morning (%d)" % n_calls))
    if n_calls == 0:
        parts.append("<p>No calls captured yet this morning.</p>")
    else:
        cells = [call_line_cells(r) for r in
                 sorted(judged_today, key=lambda r: pad_time(r.get("Time", "")))]
        for p in pending_rows:
            _d, t = parse_ended_ist(p.get("ended_at_ist", ""))
            numcol = (str(p.get("phone10", "")).strip()
                      or str(p.get("client_ref_id", "")).strip())
            cells.append([t, dir_arrow(dur_row_direction(p.get("client_ref_id", ""))),
                          numcol, fmt_dur(p.get("total_duration", "")),
                          "—", p.get("_reason", "awaiting verdict"), "—"])
        cells = cells[:MORNING_LIST_CAP]
        parts.append(render_table(
            ["Time", "Dir", "Patient / number", "Dur", "Staff logged",
             "AI heard", "Verdict"], cells))
        if n_calls > MORNING_LIST_CAP:
            parts.append("<p>…and %d more.</p>" % (n_calls - MORNING_LIST_CAP))
    parts.append(h_section("Needs attention"))
    if not attention:
        parts.append("<p>Nothing actionable. ✅</p>")
    else:
        parts.append("<ul>%s</ul>" % "".join("<li>%s</li>" % a
                                             for a in attention[:5]))
    parts.append(footer(refereed))
    parts.append("</div>")
    return "".join(parts)


def build_digest_email(day_disp, summary_line, c, staff_logged, review, spots,
                       suggestion, refereed, ai_note=""):
    parts = ['<div style="%s">' % CSS]
    parts.append(h_section("The day in one line"))
    parts.append("<p><b>%s</b></p>" % esc(summary_line))

    parts.append(h_section("Numbers"))
    parts.append(render_table(
        ["Calls", "In", "Out", "Staff logged", "Match", "Mismatch", "Partial",
         "Nobody logged", "Unclear", "Flagged"],
        [[str(c["in"] + c["out"]), str(c["in"]), str(c["out"]), str(staff_logged),
          str(c[V_MATCH]), str(c[V_MISMATCH]), str(c[V_PARTIAL]),
          str(c[V_NOCLAIM]), str(c[V_UNCLEAR]), str(c["flagged"])]]))

    parts.append(h_section("Worst first — listen to these (%d)" % len(review)))
    if not review:
        parts.append("<p>Nothing flagged today. ✅</p>")
    else:
        cells = []
        for label, r in review:
            cells.append([str(r.get("Time", "")).strip(), label, who(r),
                          str(r.get("Claimed Outcome", "")).strip() or "—",
                          str(r.get("AI Outcome", "")).strip() or "—",
                          link(r.get("Recording Link", ""), "🎧 listen")])
        parts.append(render_table(
            ["Time", "Why", "Patient", "Staff logged", "AI heard", "Recording"],
            cells))

    parts.append(h_section("Your 2 spot-checks (30 seconds each)"))
    if spots:
        parts.append("<p><b>%s</b></p>" % esc(spots))
        parts.append("<p>Their full cards — transcript, evidence and "
                     "\u25b6 listen link — are the \u2605 TODAY'S SPOT-CHECK "
                     "cards at the TOP of the <b>Verdict_Review</b> tab. "
                     "Your answers are what count toward the accuracy gate — "
                     "the machine agreeing with itself never does (D237).</p>")
    else:
        parts.append("<p>The review tab has not marked today's spot-checks "
                     "yet (its 21:00 redraw may not have run). Open "
                     "<b>Verdict_Review</b> — any open card in the top band "
                     "counts just the same.</p>")

    parts.append(h_section("One suggestion"))
    parts.append("<p>%s</p>" % esc(suggestion or "No suggestion today."))
    parts.append(footer(refereed, ai_note))
    parts.append("</div>")
    return "".join(parts)


def html_to_text(h):
    """Crude but honest plaintext alternative."""
    t = re.sub(r"<br\s*/?>", "\n", h)
    t = re.sub(r"</(p|h3|tr|ul|li|table|div)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"[ \t]+", " ", t).strip()


# ---------------------------------------------------------------------------
# Live reads (gspread) -- imports deferred so --selftest runs anywhere
# ---------------------------------------------------------------------------
def get_sheets_client():
    import gspread
    from google.oauth2.service_account import Credentials
    sa_path = env("GOOGLE_SA_KEY") or env("WA_SA_KEY")
    if not sa_path:
        print("ERROR: GOOGLE_SA_KEY / WA_SA_KEY not set. Exiting (2).")
        raise SystemExit(2)
    creds = Credentials.from_service_account_file(
        sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    return gspread.authorize(creds)


def read_tab(book, tab):
    try:
        ws = book.worksheet(tab)
    except Exception:                                          # tab absent
        return []
    return rows_as_dicts(ws.get_all_values())


def collect(day_str):
    """One pass over the four tabs -> everything both emails need."""
    gc = get_sheets_client()
    audit = gc.open_by_key(env("AUDIT_SHEET_ID", DEFAULT_AUDIT_SHEET_ID))
    tracker = gc.open_by_key(env("TRACKER_SHEET_ID", DEFAULT_TRACKER_SHEET_ID))

    verdicts = read_tab(audit, VERDICT_TAB)
    doctor = read_tab(audit, DOCTOR_TAB)
    durations = read_tab(tracker, DURATIONS_TAB)
    outcomes = read_tab(tracker, OUTCOMES_TAB)
    transcripts = read_tab(tracker, TRANSCRIPTS_TAB)

    v_today = [r for r in verdicts if str(r.get("Date", "")).strip() == day_str]
    joined_refs, vpe, vphone_min = set(), [], {}
    for r in v_today:
        jk = str(r.get("Join Key", "")).strip()
        if jk:
            joined_refs.add(jk)
        pe = parse_join_key(jk)
        if pe:
            vpe.append(pe)
        num = str(r.get("Patient Number", "")).strip()
        tm = hhmm_to_min(r.get("Time", ""))
        if num and tm is not None:
            vphone_min.setdefault(num, []).append(tm)
    t_pe, t_phone_min = [], {}
    for r in transcripts:
        pe = parse_join_key(r.get("Join Key", ""))
        if pe:
            t_pe.append(pe)
            t_phone_min.setdefault(pe[0], [])
        num = str(r.get("Number (last-4)", "")).strip()
        # last-4 alone is too weak for the fallback map; rely on join keys and
        # on the full phone when the join key gave it to us
        tm = hhmm_to_min(str(r.get("Time", ""))[:5])
        if pe and tm is not None:
            t_phone_min.setdefault(pe[0], []).append(tm)
    now_ist = datetime.datetime.now(IST)
    d_today = []
    for p in dedupe_keep_last(durations):
        d, _t = parse_ended_ist(p.get("ended_at_ist", ""))
        if d == day_str and not duration_covered(p, joined_refs, vpe, vphone_min):
            reason, alert = classify_pending(p, now_ist, t_pe, t_phone_min)
            p["_reason"], p["_alert"] = reason, alert
            d_today.append(p)
    o_today = [r for r in outcomes if parse_when(r.get("When", ""))[0] == day_str]
    try:
        vr_head = audit.worksheet(REVIEW_TAB).get_values("A1:B30")
    except Exception:                                          # tab absent / first run
        vr_head = []
    return v_today, d_today, o_today, len(doctor), find_spotcheck_line(vr_head)


# ---------------------------------------------------------------------------
# AI (digest mode only): aggregates in, two short lines out. No PHI leaves.
# ---------------------------------------------------------------------------
def ai_summary_and_suggestion(c, staff_logged, review_labels):
    api_key = env("ANTHROPIC_API_KEY")
    if not api_key:
        return None, None, "AI line skipped (no key)."
    import requests
    facts = {"calls_in": c["in"], "calls_out": c["out"],
             "staff_logged": staff_logged, "match": c[V_MATCH],
             "mismatch": c[V_MISMATCH], "partial": c[V_PARTIAL],
             "nobody_logged": c[V_NOCLAIM], "unclear": c[V_UNCLEAR],
             "safety_flag_kinds_today": review_labels}
    prompt = (
        "You write two lines for an orthopaedic clinic owner's nightly email. "
        "Input is aggregate counts for today's phone calls (staff-claimed "
        "outcomes vs an AI listener's verdicts). Reply ONLY with JSON: "
        '{"summary": "<one plain-English line, the day in one sentence>", '
        '"suggestion": "<one specific, data-backed improvement for staff or '
        "system; if the data is too thin, say what to watch tomorrow>\"}. "
        "No preamble, no markdown. Counts: " + json.dumps(facts))
    try:
        resp = requests.post(
            ANTHROPIC_URL, timeout=AI_TIMEOUT_S,
            headers={"x-api-key": api_key,
                     "anthropic-version": ANTHROPIC_VERSION,
                     "content-type": "application/json"},
            json={"model": env("AI_DIGEST_MODEL", DEFAULT_MODEL),
                  "max_tokens": AI_MAX_TOKENS,
                  "messages": [{"role": "user", "content": prompt}]})
        if resp.status_code != 200:
            return None, None, "AI line skipped (http %d)." % resp.status_code
        text = "".join(b.get("text", "") for b in resp.json().get("content", [])
                       if b.get("type") == "text").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        obj = json.loads(text)
        return (str(obj.get("summary", "")).strip() or None,
                str(obj.get("suggestion", "")).strip() or None, "")
    except Exception as e:                                    # noqa: BLE001
        return None, None, "AI line skipped (%s)." % e.__class__.__name__


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------
def send_email(subject, html_body, dry_run=False):
    user = env("DIGEST_SMTP_USER", DEFAULT_SMTP_USER)
    to = env("DIGEST_TO", DEFAULT_TO)
    if dry_run:
        print("=" * 70)
        print("DRY RUN — nothing sent.  From: %s  To: %s" % (user, to))
        print("Subject:", subject)
        print("-" * 70)
        print(html_to_text(html_body))
        print("=" * 70)
        return
    pwd = env("DIGEST_SMTP_PASS")
    if not pwd:
        print("ERROR: DIGEST_SMTP_PASS not set in %s. Exiting (2)." % ENV_PATH)
        raise SystemExit(2)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText(html_to_text(html_body), "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(user, [to], msg.as_string())
        print("SENT: %s -> %s | %s" % (user, to, subject))
    except SystemExit:
        raise
    except Exception as e:                                    # noqa: BLE001
        print("SEND FAILED: %s: %s" % (e.__class__.__name__, e))
        raise SystemExit(3)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def run_pulse(dry_run):
    now = datetime.datetime.now(IST)
    day_str = now.strftime("%Y-%m-%d")
    day_disp = now.strftime("%a %d %b %Y")
    v_today, d_pending, _o_today, refereed, _spot = collect(day_str)

    attention = []
    for p_ in d_pending:
        if p_.get("_alert"):
            _d, t = parse_ended_ist(p_.get("ended_at_ist", ""))
            numcol = (str(p_.get("phone10", "")).strip()
                      or str(p_.get("client_ref_id", "")).strip())
            attention.append("%s %s — %s: connected call, no recording ever "
                             "arrived. Pipeline lost a conversation — check."
                             % (esc(p_.get("_reason", "")), esc(t), esc(numcol)))
    mis = [r for r in v_today if str(r.get("Verdict", "")).strip() == V_MISMATCH]
    for r in mis[:2]:
        attention.append(
            "Mismatch %s — %s: staff logged “%s”, AI heard “%s”."
            % (esc(pad_time(r.get("Time", ""))), esc(who(r)),
               esc(str(r.get("Claimed Outcome", ""))),
               esc(str(r.get("AI Outcome", "")))))
    flagged = [(lab, r) for lab, r in worst_first(v_today, cap=99)
               if lab != "MISMATCH"]
    for lab, r in flagged[:2]:
        attention.append("%s flag %s — %s. %s"
                         % (esc(lab), esc(pad_time(r.get("Time", ""))), esc(who(r)),
                            link(r.get("Recording Link", ""), "🎧 listen")))
    noclaim = [r for r in v_today
               if str(r.get("Verdict", "")).strip() == V_NOCLAIM]
    if noclaim:
        attention.append("%d connected call(s) still have no staff log — "
                         "one tap each on the dashboard closes them."
                         % len(noclaim))

    n_calls = len(v_today) + len(d_pending)
    subject = pulse_subject(day_disp, n_calls, len(attention))
    body = build_pulse_email(day_disp, v_today, d_pending, attention, refereed)
    send_email(subject, body, dry_run)


def run_digest(dry_run):
    now = datetime.datetime.now(IST)
    day_str = now.strftime("%Y-%m-%d")
    day_disp = now.strftime("%a %d %b %Y")
    v_today, d_pending, o_today, refereed, spot_line = collect(day_str)
    lost = [p for p in d_pending if p.get("_alert")]

    c = bucket_counts(v_today)
    staff_logged = len(o_today)
    review = worst_first(v_today)
    spots = spot_line   # v1.3: verdict_review v3 decided; we only report

    ai_sum, ai_sug, ai_note = ai_summary_and_suggestion(
        c, staff_logged, sorted({lab for lab, _ in review}))
    summary = ai_sum or computed_summary_line(c, staff_logged)
    suggestion = ai_sug or (
        ("Biggest gap today: %d connected calls nobody logged — remind staff "
         "the one-tap buttons close these in two seconds." % c[V_NOCLAIM])
        if c[V_NOCLAIM] else "Clean day. Keep the one-tap habit going.")

    if lost:
        lines = "; ".join(
            "%s %s (%s)" % (parse_ended_ist(p.get("ended_at_ist", ""))[1],
                            (str(p.get("phone10", "")).strip()
                             or str(p.get("client_ref_id", "")).strip()),
                            p.get("_reason", ""))
            for p in lost[:6])
        suggestion = ("%d connected call(s) produced NO recording today (%s). "
                      "This is the pipeline losing conversations — worth a "
                      "look before anything else. | %s"
                      % (len(lost), lines, suggestion))
    subject = digest_subject(day_disp, c)
    body = build_digest_email(day_disp, summary, c, staff_logged, review, spots,
                              suggestion, refereed, ai_note)
    send_email(subject, body, dry_run)


def run_test(dry_run):
    now = datetime.datetime.now(IST)
    subject = "DIGEST TEST — %s — delete me" % now.strftime("%d %b %Y %H:%M")
    body = ('<div style="%s"><p>This is the one-time test email from '
            "<b>daily_digest.py %s</b>. If you are reading this in your "
            "personal inbox, the digest pipe is proven end-to-end. "
            "Nothing was read from any sheet for this test.</p>%s</div>"
            % (CSS, esc(BUILD_VERSION), footer(0)))
    send_email(subject, body, dry_run)


# ---------------------------------------------------------------------------
# Selftest -- offline, no network, no sheets, no email
# ---------------------------------------------------------------------------
def selftest():
    passed = [0]

    def check(name, cond):
        print("  %-58s %s" % (name, "PASS" if cond else "FAIL"))
        if cond:
            passed[0] += 1
        else:
            raise SystemExit("SELFTEST FAILED: " + name)

    print("daily_digest.py %s selftest" % BUILD_VERSION)

    # -- duration / parsing ------------------------------------------------
    check("fmt_dur 87 -> 1:27", fmt_dur("87") == "1:27")
    check("fmt_dur 0 -> 0:00", fmt_dur(0) == "0:00")
    check("fmt_dur '' -> -", fmt_dur("") == "-")
    check("fmt_dur junk -> -", fmt_dur("abc") == "-")
    check("parse_when ok",
          parse_when("2026-07-13 10:05") == ("2026-07-13", "10:05"))
    check("parse_when junk", parse_when("nope") == ("", ""))
    check("parse_ended ok",
          parse_ended_ist("2026-07-13T09:14:22+05:30") == ("2026-07-13", "09:14"))
    check("parse_ended junk", parse_ended_ist("") == ("", ""))
    check("dir_arrow in", dir_arrow("incoming") == "IN ")
    check("dir_arrow out", dir_arrow("outgoing") == "OUT")
    check("dur_row_direction IN-", dur_row_direction("IN-abc123") == "incoming")
    check("dur_row_direction OBD", dur_row_direction("cc-77") == "outgoing")
    check("truthy TRUE", truthy_flag("TRUE") and truthy_flag("1"))
    check("truthy blank/false", not truthy_flag("") and not truthy_flag("FALSE"))

    # -- rows_as_dicts -----------------------------------------------------
    rd = rows_as_dicts([["A", "B"], ["1", "2"], ["", ""], ["3"]])
    check("rows_as_dicts skips blank, pads short",
          rd == [{"A": "1", "B": "2"}, {"A": "3", "B": ""}])
    check("rows_as_dicts empty", rows_as_dicts([]) == [])

    # -- severity / worst-first ---------------------------------------------
    vr_urgent = {"Verdict": V_MATCH, "Flag Urgent": "TRUE", "Time": "10:00"}
    vr_conduct = {"Verdict": V_MATCH, "Flag Conduct": "TRUE", "Time": "09:00"}
    vr_mis = {"Verdict": V_MISMATCH, "Time": "08:00"}
    vr_clean = {"Verdict": V_MATCH, "Time": "07:00"}
    check("severity urgent rank 0", verdict_severity(vr_urgent) == (0, "URGENT"))
    check("severity mismatch last",
          verdict_severity(vr_mis) == (len(FLAG_SEVERITY), "MISMATCH"))
    check("severity clean None", verdict_severity(vr_clean) is None)
    wf = worst_first([vr_clean, vr_mis, vr_conduct, vr_urgent])
    check("worst_first order U>C>M",
          [w[0] for w in wf] == ["URGENT", "CONDUCT", "MISMATCH"])
    check("worst_first cap", len(worst_first([vr_mis] * 30)) == REVIEW_LIST_CAP)

    # -- buckets --------------------------------------------------------------
    c = bucket_counts([
        {"Verdict": V_MATCH, "Direction": "outgoing"},
        {"Verdict": V_MISMATCH, "Direction": "outgoing"},
        {"Verdict": V_NOCLAIM, "Direction": "incoming", "Flag Urgent": "TRUE"},
    ])
    check("buckets match/mis/noclaim",
          c[V_MATCH] == 1 and c[V_MISMATCH] == 1 and c[V_NOCLAIM] == 1)
    check("buckets in/out", c["in"] == 1 and c["out"] == 2)
    check("buckets flagged", c["flagged"] == 1)
    check("buckets unknown verdict -> other",
          bucket_counts([{"Verdict": "??", "Direction": ""}])["other"] == 1)

    # -- spot checks (v1.3: read the tab's line; verdict_review decides) --------
    grid = [["CALL VERDICT REVIEW", "x"], ["Generated", "y"],
            [SPOTLINE_LABEL, "******1234 2026-07-12 10:00 (coming)"], [""]]
    check("spot line found", find_spotcheck_line(grid)
          == "******1234 2026-07-12 10:00 (coming)")
    check("spot line absent -> empty", find_spotcheck_line(
          [["CALL VERDICT REVIEW", "x"]]) == "")
    check("spot line empty grid", find_spotcheck_line([]) == ""
          and find_spotcheck_line(None) == "")
    check("spot line short row tolerated",
          find_spotcheck_line([[SPOTLINE_LABEL]]) == "")

    # -- pad / keys / join (v1.1 dry-run fixes) ----------------------------------
    check("pad_time 8:58", pad_time("8:58") == "08:58")
    check("pad_time already padded", pad_time("10:00") == "10:00")
    check("pad_time junk passthrough", pad_time("x") == "x")
    check("parse_join_key ok",
          parse_join_key("9917656698_1783916119") == ("9917656698", 1783916119))
    check("parse_join_key junk", parse_join_key("nope") is None)
    check("parse_client_ref ok",
          parse_client_ref("9917656698-178391611958e8")
          == ("9917656698", 1783916119))
    check("parse_client_ref IN- is None", parse_client_ref("IN-abc") is None)
    check("hhmm_to_min", hhmm_to_min("8:58") == 538 and hhmm_to_min("x") is None)
    dd = dedupe_keep_last([{"client_ref_id": "a", "v": 1},
                           {"client_ref_id": "b"},
                           {"client_ref_id": "a", "v": 2}])
    check("dedupe keeps last, keeps order",
          len(dd) == 2 and dd[0]["v"] == 2 and dd[1]["client_ref_id"] == "b")
    vpe = [("9917656698", 1783916119)]
    vpm = {"8449348409": [538]}
    check("covered by exact ref",
          duration_covered({"client_ref_id": "K1"}, {"K1"}, [], {}))
    check("covered by phone+epoch",
          duration_covered({"client_ref_id": "9917656698-178391611958e8"},
                           set(), vpe, {}))
    check("not covered, epoch too far",
          not duration_covered({"client_ref_id": "9917656698-179000000058e8"},
                               set(), vpe, {}))
    check("covered IN- by phone+time window",
          duration_covered({"client_ref_id": "IN-x", "phone10": "8449348409",
                            "ended_at_ist": "2026-07-13T08:59:10+05:30"},
                           set(), [], vpm))
    check("not covered, unknown phone",
          not duration_covered({"client_ref_id": "IN-y", "phone10": "9000000000",
                                "ended_at_ist": "2026-07-13T08:59:10+05:30"},
                               set(), [], vpm))

    # -- classify_pending (v1.2) -------------------------------------------------
    NOW = datetime.datetime(2026, 7, 13, 11, 30, tzinfo=IST)
    def mk(result, talk, ended, ref="9000000001-1783916000abcd", phone=""):
        return {"customer_result": result, "customer_talk_duration": talk,
                "ended_at_ist": ended, "client_ref_id": ref, "phone10": phone}
    r1 = classify_pending(mk("not_answered", "", "2026-07-13T09:42:00+05:30"),
                          NOW, [], {})
    check("classify not answered", r1 == ("not answered", False))
    r2 = classify_pending(mk("connected", "8", "2026-07-13T09:42:00+05:30"),
                          NOW, [], {})
    check("classify too short", r2[0].startswith("too short") and not r2[1])
    r3 = classify_pending(mk("connected", "40", "2026-07-13T11:20:00+05:30"),
                          NOW, [], {})
    check("classify fresh -> in pipeline", r3 == ("in pipeline", False))
    r4 = classify_pending(mk("connected", "40", "2026-07-13T09:37:00+05:30"),
                          NOW, [("9000000001", 1783916100)], {})
    check("classify transcript exists",
          r4 == ("transcribed — verdict due", False))
    r5 = classify_pending(mk("connected", "40", "2026-07-13T09:37:00+05:30"),
                          NOW, [], {})
    check("classify LOST CONVERSATION alert",
          r5[1] and "no recording" in r5[0])
    # F-44: same call, but MyOperator marked it missed -> NOT an alert
    r5b = dict(mk("connected", "40", "2026-07-13T09:37:00+05:30"), status="missed")
    r5b_out = classify_pending(r5b, NOW, [], {})
    check("classify provider-missed -> not an alert",
          r5b_out[1] is False and "no recording expected" in r5b_out[0])
    r6 = classify_pending(mk("connected", "101",
                             "2026-07-13T09:37:00+05:30", ref="IN-xyz",
                             phone="9000000002"),
                          NOW, [], {"9000000002": [577]})
    check("classify IN- via phone+time window",
          r6 == ("transcribed — verdict due", False))

    # -- who / subjects ---------------------------------------------------------
    check("who both",
          who({"Patient Name": "Ram", "Patient Number": "9358001234"})
          == "Ram (9358001234)")
    check("who number only", who({"Patient Number": "9358001234"}) == "9358001234")
    check("who none", who({}) == "unknown caller")
    check("pulse subject zero",
          "no calls yet" in pulse_subject("Mon 13 Jul 2026", 0, 0))
    check("pulse subject clean",
          "all clean" in pulse_subject("Mon 13 Jul 2026", 5, 0))
    check("pulse subject attn",
          "2 need attention" in pulse_subject("Mon 13 Jul 2026", 5, 2))
    ds = digest_subject("Mon 13 Jul 2026", c)
    check("digest subject counts",
          "3 calls" in ds and "1 flagged" in ds and "1 mismatch" in ds)

    # -- summary fallback ---------------------------------------------------------
    line = computed_summary_line(c, 4)
    check("fallback line totals",
          "3 calls" in line and "4 staff-logged" in line)
    check("fallback flags mismatch", "1 mismatch" in line)

    # -- rendering -----------------------------------------------------------------
    vt = {"Time": "10:05", "Direction": "incoming", "Patient Name": "<b>X</b>",
          "Patient Number": "9111", "Duration": "65", "Claimed Outcome": "coming",
          "AI Outcome": "coming", "Verdict": V_MATCH,
          "Recording Link": "https://drive.google.com/file/d/abc/view"}
    body = build_pulse_email(
        "Mon 13 Jul 2026", [vt],
        [{"client_ref_id": "IN-9", "phone10": "9222",
          "ended_at_ist": "2026-07-13T10:40:00+05:30", "total_duration": "30"}],
        ["something"], 7)
    check("pulse html escapes name", "&lt;b&gt;X&lt;/b&gt;" in body)
    check("pulse lists pending row",
          "awaiting verdict" in body and "9222" in body)
    check("pulse footer progress", "7 / 100" in body)
    early = {"Time": "8:58", "Direction": "incoming", "Patient Name": "Early",
             "Patient Number": "9000000001", "Verdict": V_MATCH}
    late = {"Time": "10:00", "Direction": "outgoing", "Patient Name": "Late",
            "Patient Number": "9000000002", "Verdict": V_MATCH}
    bs = build_pulse_email("Mon", [late, early], [], [], 0)
    check("pulse sorts 08:58 before 10:00", bs.index("Early") < bs.index("Late"))
    check("pulse displays padded time", "08:58" in bs)
    body2 = build_pulse_email("Mon", [], [], [], 0)
    check("pulse empty morning line", "No calls captured yet" in body2)
    check("pulse empty attention", "Nothing actionable" in body2)
    dg = build_digest_email("Mon", "line", c, 4, [("URGENT", vt)],
                            "******1234 2026-07-12 10:00 (coming)",
                            "do X", 7, "")
    check("digest has listen link", 'href="https://drive.google.com' in dg)
    check("digest has spot section", "spot-checks" in dg)
    check("digest carries the tab's spot line verbatim",
          "******1234 2026-07-12 10:00 (coming)" in dg)
    dg0 = build_digest_email("Mon", "line", c, 4, [("URGENT", vt)], "",
                             "do X", 7, "")
    check("no spot line -> points at the band, never invents picks",
          "top band" in dg0)
    check("digest has suggestion", "do X" in dg)
    check("bad link not rendered as anchor",
          link("javascript:x", "t") == "t")
    txt = html_to_text(dg)
    check("plaintext non-empty, no tags", len(txt) > 50 and "<td" not in txt)

    # -- construction guarantees ------------------------------------------------
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    check("D235: no Sheets-append call anywhere in this file",
          "append" + "_row" not in src)
    check("read-only scope requested", "spreadsheets.readonly" in src)

    print("SELFTEST: %d/%d PASS" % (passed[0], passed[0]))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="D236 daily digest (%s)" % BUILD_VERSION)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pulse", action="store_true", help="11:00 morning pulse")
    g.add_argument("--digest", action="store_true", help="21:30 full digest")
    g.add_argument("--test", action="store_true", help="send a test email now")
    g.add_argument("--selftest", action="store_true", help="offline unit tests")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the email, send nothing")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    load_env()
    if args.test:
        run_test(args.dry_run)
    elif args.pulse:
        run_pulse(args.dry_run)
    elif args.digest:
        run_digest(args.dry_run)


if __name__ == "__main__":
    main()
