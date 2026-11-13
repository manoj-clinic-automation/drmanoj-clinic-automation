#!/usr/bin/env python3
"""
calls_console.py -- S698_CALLS_R1 (the parent, S379, 02-Nov-2026): the owner's Call Console in the
month page's look, built to the APPROVED mock-up v12 (D819, D820).

ONE READING LAYER over /root/wa/console.db (built by portal_console.py; read-only, mode=ro).
Nothing here writes console.db. The two things this page can DO are the two the old page could:
  . a click-to-call through call_api.py (the owner's own MyOperator agent; the number is the row's
    stored number, never one typed on the page; one call per number per minute);
  . the owner's review verdict, posted to the old page's own route (/portal/console/review).

What this kit shows (calls only -- S699 adds the WhatsApps, the sanitised follow-up list and Call ke
baad; S700 the Staff performance section; S701 the Patients section of the command console):
  the legend . the strip with icon counts (calls only) . Needs you today as icon chains . People today,
  ONE ROW PER PERSON with every contact in time order (unknown numbers first) -- the timeline is built to
  hold any kind of contact . the tracker's booked-not-visited rows as icon chains . this week's unknown
  callers . earlier days.

S742_CALLS_R3 (the parent, S397, 07-Nov-2026) -- the owner's "build now" (06:36 IST) on mock-up R3 (v19 of
https://claude.ai/artifact/AwBDzfttkYPygGVcrQbTfD; his asks 06:00 IST: the icon key short, every section folded with
its summary on the top line and the line's colour saying "open me", the page compact):
  . WHATSAPPS in each person's timeline, read-only from the inbox store (/root/wa/wa_inbox/inbox.db). D820's answer
    rule: a WhatsApp is answered by a DELIVERED (or read) reply, or by an answered call of 30 s or more within 2 clinic
    hours; a missed call only by a connected call; templates and failed replies never count. Call counts count calls.
  . THE FOLLOW-UP LIST CLEANED (F-1106): from console.db's fu_all (the whole Followups_Today feed, today's rows
    included -- portal_console.py keeps it from this kit), ONE open row per patient at its latest due date; a row
    closes by itself on a Docterz visit on or after the due date (finance.db patient_visit, read-only, by clinic ID or
    the clinic's own mobile fingerprint) or a filed "not coming"; sections Today . Grace 1-3 . Overdue 4-14 . Lapsed 15+
    . Came / closed (the last 7 days); called-of per section and who called today.
  . CALL KE BAAD for the week, booked -> came / awaited / never came, per staff -- ring_outcome.list_data, the list's
    own rule, read-only.
  . The strip tells "missed, then we called back" apart from "missed, then they rang again and got through".
  . The look of R3: a one-line key, every section folded with a coloured top line, two columns.
Nothing here writes anything. The Staff performance section is the next kit.

S747_CALLS_REVIEW_CARDS (the parent, S400, 07-Nov-2026) -- D856, Build B part 2, on the owner's mock-up
https://claude.ai/artifact/LNNtTvacjz3v9Nf77sJfhB (v2; his ask 08:52 IST: every call's transcript inline, expandable as on
the console, and its log):
  . HIS REVIEW BUTTONS on each staff card's call: Ask to log . Mark reviewed . Staff right . AI right . Note to staff (and
    Undo in the Reviewed fold). They are written to a store of this module's own, /root/portal/call_review.db (setting
    PORTAL_CALL_REVIEW_DB) -- the only thing this page writes besides the click-to-call. A reviewed call leaves the 'to check'
    lists for the folded 'Reviewed by you'; an ask to log stays on the list, marked asked, until the call is logged. The old
    final-outcome verdict (/portal/console/review) is read alongside, as before. 'To check' is never a verdict.
  . EACH PERSON'S OWN CARD (Aaj ka kaam, in Hindi): GET /portal/console/api/mycard with their own login (the owner's ?as=
    view: /portal/console/api/card/<login>, behind his gate) gives the same card his page draws, every call they handled with
    its log line; GET /portal/console/api/myrec/<jk> plays the recording of one of THEIR calls (of the last 7 days, through
    the portal's own recording server) and nobody else's. Staff get recordings, never transcript text (the owner, 09:23 IST
    07-Nov); the transcripts stay on his own page; POST /portal/console/api/dispute {ref, fig, text} -- 'Galat hai?' -- one line
    about one call behind one of their figures; it comes to his card as Disputed, he answers Accept (the call leaves that
    person's figures) or It stands (POST /portal/console/api/dispute-answer).
  . THE RECEPTION MOBILE (F-1168): a call on the reception mobile's agent (first name, setting PORTAL_RECEPTION_AGENT,
    default 'reception') is credited to the ONE phone staff member on duty at that minute; with both or neither on duty it
    stays on a 'Reception mobile' line that says why. Missed calls were and stay charged by duty.
The staff routes use the portal's own login gate and signed-in user (found in the module that defines the doctor gate);
when either cannot be found they are not registered and the staff page simply shows no card.
S748_MISSED_PEOPLE (S400, 07-Nov-2026, the owner's 'yes' 10:02 and 10:06 IST): NET MISSED leads each card -- the patients
who rang on that person's duty and were never reached after, either way ('Net missed: 3 patients . 16 missed calls from 9
patients, 6 reached later'); a call the owner marked reviewed still counts here (it is a fact, not a verdict); a dispute he
accepted does not. The card is rose whenever net missed is above zero. Calls stay counted as calls everywhere else.

S817_CALLS_FOLLOWUP_LINES (the parent, S447, 13-Nov-2026) -- F-1322 and the owner's rulings of 13-Nov on the approved mock-up
https://claude.ai/artifact/8J3R3QtW9awbajmLN4rmic (screen 1, the follow-up lines). ONLY the follow-up sections change:
  . In Grace and older a CALL counts for a patient only when it was made on a day AFTER the due date (a call on the
    appointment day counted before -- F-1322); the Today section counts today's calls.
  . Each folded line: "Called today N of M" large, "Reached K", and smaller "Earlier days, after the due date: x called .
    y reached".
  . Only patients who have not come back by D893 are listed: a visit from half the advised period before the due date
    (never the visit at which the follow-up was advised) closes the row. The advised period is read from finance.db's
    dx_visit (read-only); when it cannot be read the old rule stands (only a visit on or after the due date), so the
    row STAYS.
  . Each patient in Grace and older shows when they were LAST REACHED (the last answered call of the last 60 days, D899)
    with the page's own player and transcript.
    A visit on or after the due date closes a row only among the days the page has always read (60 days back).
  . On the folded lines a patient who rang in and was answered counts as called and reached for that day.
Nothing outside followup_list() and its rows reads any of this: the staff cards, Mere calls, the strip and today's top
line (due / called / reached / who) are unchanged; only "came" on today's line can rise.

Registered from portal.py:  calls_console.register(app, doctor_required, who_fn, cfg_get, helpers)
Routes:  GET  /portal/console                 the page (?span=today|yesterday|7|30 . ?day=YYYY-MM-DD . ?q=)
         GET  /portal/console/api/tx/<jk>     one transcript, on tap
         POST /portal/console/api/call        {"phone10": ...} -> the IVR call
The old page's views (?view=log|threads|staff|pipe|noshows) redirect to /portal/console/old.
"""

import datetime as _dt
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from urllib.parse import urlencode

from flask import request, redirect, make_response, render_template_string, jsonify, abort

KIT = "S817_CALLS_FOLLOWUP_LINES"
VERSION = "S817 1.0"
INBOX_DB_DEFAULT = "/root/wa/wa_inbox/inbox.db"
WA_CALL_MIN_S = 30          # D820: an answered call of 30 s or more ...
WA_CALL_WITHIN_H = 2.0      # ... within 2 clinic hours answers a WhatsApp
FU_ROWS_MAX = 80            # rows drawn per follow-up section (the count is always the whole)
FU_BANDS = (("today", "Today’s follow-ups", "due today"), ("grace", "Grace period", "1–3 days late"),
            ("overdue", "Overdue", "4–14 days late"), ("lapsed", "Lapsed", "15+ days late"))
NOT_COMING = ("not_coming", "k_not_coming")
FU_BACK_DAYS = 60           # S817: the calls are read this far back, for each listed patient's last answered call (D899)
FU_EARLY_SHARE = 0.5        # S817 (D893): a visit from half the advised period before the due date is the return
IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))

# The reading window (D819): the console builder runs 07:00-22:50 IST; outside it the page says "as of"
# and is never called stale.
READ_FROM_H, READ_TO_H = 7, 23
STALE_MIN_DEFAULT = 25
CALL_GAP = 60            # one IVR call per number per minute (as Call ke baad, D806)
CALL_TIMEOUT = 30
CALL_URL_DEFAULT = "http://127.0.0.1:8097/call"
WA_ENV_DEFAULT = "/root/wa/.env"

_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_JK = re.compile(r"^(\d{10})_(\d{9,12})$")
_FALSEY = ("", "0", "FALSE", "False", "false", "NO", "No", "no", "N", "n", "-")
_FLAG_COLS = (("flag_urgent", "urgent"), ("flag_postop", "post-op"), ("flag_clinical", "clinical"),
              ("flag_surgery", "surgery"), ("flag_complaint", "complaint"), ("flag_conduct", "conduct"))

# Outcome codes (the staff's buttons, GAS_Outcome_Vocabularies_v1) -> English words for the owner's page.
EN_OUTCOME = {
    "coming": "coming", "will_come": "coming", "k_coming": "coming",
    "not_coming": "not coming", "k_not_coming": "not coming",
    "call_again": "call again", "k_call_again": "call again", "needs_callback": "call again",
    "no_answer": "no answer", "no_contact": "no answer",
    "problem": "to the doctor", "escalated": "to the doctor", "to_doctor": "to the doctor",
    "appointment_booked": "booked", "booked": "booked",
    "enquiry_only": "enquiry", "info_given_will_act": "enquiry",
    "no_action": "no action", "spam": "spam",
    # S762 (F-1213): the codes the live read found on his screens raw -- the AI's words and the in_/out_ prefixed buttons
    "unclear": "not clear", "resolved_on_call": "sorted on the call", "on_medication": "on medicines",
    "in_appointment_booked": "booked", "in_enquiry_only": "enquiry", "in_will_come": "coming", "in_coming": "coming",
    "in_not_coming": "not coming", "in_call_again": "call again", "in_problem": "to the doctor",
}
# S762: two words that do not contradict each other -- staff passed the call to the doctor and the patient is coming /
# booked. A verdict 'Mismatch' between the same English words, or between these, is not a mismatch on this page.
AGREE_PAIRS = {("to the doctor", "coming"), ("to the doctor", "booked"), ("coming", "booked"), ("booked", "coming")}

_H = {}            # helpers handed in by portal.py (console_conn, console_meta, reviews_maps, spam_phones)
_WHO = None
_CFG = None


# ---------------------------------------------------------------------------------------------- small helpers
def now_ist(now=None):
    return now if now is not None else _dt.datetime.now(IST).replace(tzinfo=None)


def en_out(code):
    c = (code or "").strip().lower()
    if c in EN_OUTCOME:
        return EN_OUTCOME[c]
    for pre in ("in_", "out_", "k_"):                    # S762: a prefixed button reads as its plain word
        if c.startswith(pre) and c[len(pre):] in EN_OUTCOME:
            return EN_OUTCOME[c[len(pre):]]
    return c.replace("_", " ") if c else ""             # S762: never a raw code on a screen


def real_mismatch(verdict, claimed_h, ai_h):
    """S762: the verdict layer's 'Mismatch' stands only when the two English words truly differ."""
    if verdict != "Mismatch":
        return False
    a, b = (claimed_h or "").strip(), (ai_h or "").strip()
    if a and b and (a == b or (a, b) in AGREE_PAIRS or (b, a) in AGREE_PAIRS):
        return False
    return True


def _truthy(v):
    return (v or "").strip() not in _FALSEY


def parse_ts(s):
    """'2026-11-01T16:52:03+05:30' / '2026-11-01 16:52:03' / '2026-11-01 16:52' -> naive datetime, or None."""
    s = (s or "").strip()
    if not s:
        return None
    s = re.sub(r"([+-]\d{2}:?\d{2}|Z)\s*$", "", s).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return _dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _int(v, d=0):
    try:
        return int(float(str(v).strip() or 0))
    except Exception:
        return d


def dur_h(sec):
    s = _int(sec)
    return "%d:%02d" % (s // 60, s % 60) if s > 0 else ""


def fmt_num(p):
    """'5000014075' -> '50000 14075' (the mock-up's grouping; the FULL number, D819)."""
    p = (p or "").strip()
    return (p[:5] + " " + p[5:]) if len(p) == 10 and p.isdigit() else p


def first_name(agent):
    a = (agent or "").strip()
    if a.lower().startswith("dr manoj") or a.lower().startswith("dr. manoj"):
        return "you"
    return a.split()[0] if a else ""


def day_label(iso, today=None):
    try:
        d = _dt.date.fromisoformat(iso)
    except Exception:
        return iso
    today = today or _dt.date.today()
    if d == today:
        return "Today · " + d.strftime("%a %-d %b")
    if d == today - _dt.timedelta(days=1):
        return "Yesterday · " + d.strftime("%a %-d %b")
    return d.strftime("%A %-d %B")


def wait_h(since, now):
    """Hours waited, counted in the reading window only (07:00-23:00) -- a call at 22:50 is not 'late' at 08:00."""
    if since is None or now is None or now <= since:
        return 0.0
    since = max(since, now - _dt.timedelta(days=31))      # a wait is never walked further back than a month
    t, total = since, 0.0
    while t < now:
        nxt = min(now, t + _dt.timedelta(minutes=10))
        if READ_FROM_H <= t.hour < READ_TO_H:
            total += (nxt - t).total_seconds()
        t = nxt
    return total / 3600.0


def wait_words(h):
    if h < 1.0:
        m = int(round(h * 60))
        return "%d min" % m if m else "just now"
    return "%d h" % int(h) if h < 48 else "%d days" % int(h // 24)


def call_start(ts_end, join_key, total_duration):
    """A call's START: the join key carries the start unix; else the end minus the duration; else the end."""
    m = _JK.match(join_key or "")
    if m:
        try:
            return _dt.datetime.fromtimestamp(int(m.group(2)), IST).replace(tzinfo=None)
        except Exception:
            pass
    end = parse_ts(ts_end)
    if end is None:
        return None
    return end - _dt.timedelta(seconds=max(0, _int(total_duration)))


# ---------------------------------------------------------------------------------------------- the reading
_CALLS_SQL = """
SELECT c.id, c.direction, c.answered, c.total_duration, c.customer_ring_duration, c.customer_talk_duration,
       c.phone10, c.join_key, c.ended_at_ist, c.client_ref_id, c.recording_filename, c.status,
       COALESCE(ca.agent,'') AS ca_agent,
       COALESCE(v.agent,'') AS v_agent, COALESCE(v.patient_name,'') AS v_name, COALESCE(v.clinic_id,'') AS v_cid,
       COALESCE(v.claimed_outcome,'') AS claimed, COALESCE(v.ai_outcome,'') AS ai_outcome,
       COALESCE(v.verdict,'') AS verdict, COALESCE(v.ai_reason,'') AS ai_reason, COALESCE(v.evidence,'') AS evidence,
       COALESCE(v.flag_urgent,'') AS flag_urgent, COALESCE(v.flag_postop,'') AS flag_postop,
       COALESCE(v.flag_clinical,'') AS flag_clinical, COALESCE(v.flag_surgery,'') AS flag_surgery,
       COALESCE(v.flag_complaint,'') AS flag_complaint, COALESCE(v.flag_conduct,'') AS flag_conduct,
       COALESCE(v.final_outcome,'') AS final_outcome, COALESCE(v.doctor_note,'') AS doctor_note,
       (SELECT 1 FROM transcripts t WHERE t.join_key=c.join_key AND c.join_key<>'' AND COALESCE(t.text,'')<>'' LIMIT 1) AS has_tx,
       (SELECT substr(t.text,1,220) FROM transcripts t WHERE t.join_key=c.join_key AND c.join_key<>'' AND COALESCE(t.text,'')<>'' LIMIT 1) AS tx_head,
       (SELECT 1 FROM recordings rr WHERE rr.join_key=c.join_key AND c.join_key<>'' AND COALESCE(rr.recording_link,'')<>'' LIMIT 1) AS has_rec
FROM calls c
LEFT JOIN call_agent ca ON ca.join_key=c.join_key AND c.join_key<>''
LEFT JOIN (SELECT join_key, MAX(id) AS _vid, agent, patient_name, clinic_id, claimed_outcome, ai_outcome, verdict,
                  ai_reason, evidence, flag_urgent, flag_postop, flag_clinical, flag_surgery, flag_complaint,
                  flag_conduct, final_outcome, doctor_note
           FROM verdicts WHERE join_key<>'' GROUP BY join_key) v ON v.join_key=c.join_key AND c.join_key<>''
WHERE substr(c.ended_at_ist,1,10)>=? AND substr(c.ended_at_ist,1,10)<=?
ORDER BY c.ended_at_ist ASC, c.id ASC
"""

# a call belongs to a number by its phone10, or (an OBD row, phone10 blank) by its join key's prefix or its reference's
_PHONE_IS = "(c.phone10=? OR c.join_key LIKE ? OR c.client_ref_id LIKE ?)"

_PAT_SQL = ("SELECT phone10, name, diagnosis, age, gender, clinic_id, last_visit FROM "
            "(SELECT phone10, MAX(rowid) AS _r, name, diagnosis, age, gender, clinic_id, last_visit FROM patients "
            " WHERE phone10<>'' GROUP BY phone10)")


def _table_exists(conn, name):
    try:
        return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None
    except Exception:
        return False


def phone_of(row):
    """The person's number: phone10, else the join key's prefix, else the ten digits an OBD reference starts with."""
    p = (row["phone10"] or "").strip()
    if len(p) == 10 and p.isdigit():
        return p
    m = _JK.match(row["join_key"] or "")
    if m:
        return m.group(1)
    cr = (row["client_ref_id"] or "").strip()
    m2 = re.match(r"^(\d{10})\D", cr + " ")
    if m2 and not cr.startswith("IN-"):
        return m2.group(1)
    return ""


def call_item(row, patients, now):
    """One call -> one timeline item (a dict the page renders). Pure."""
    ph = phone_of(row)
    direction = (row["direction"] or "").strip()
    answered = row["answered"]
    kind = ("in_ok" if answered == 1 else "in_miss") if direction == "In" else ("out_ok" if answered == 1 else "out_miss")
    start = call_start(row["ended_at_ist"], row["join_key"], row["total_duration"])
    end = parse_ts(row["ended_at_ist"])
    agent = (row["ca_agent"] or row["v_agent"] or "").strip()
    flags = [lab for col, lab in _FLAG_COLS if _truthy(row[col])]
    ai = (row["ai_outcome"] or "").strip()
    claimed = (row["claimed"] or "").strip()
    verdict = (row["verdict"] or "").strip()
    ring = _int(row["customer_ring_duration"])
    dur = _int(row["total_duration"])
    talk = _int(row["customer_talk_duration"])
    jk = (row["join_key"] or "").strip()
    has_rec = bool(jk) and (bool(row["has_rec"]) or bool((row["recording_filename"] or "").strip()))
    it = {
        "id": row["id"], "phone": ph, "kind": kind, "direction": direction, "answered": (answered == 1),
        "t": start, "t_h": start.strftime("%H:%M") if start else "", "day": (start or end or now).strftime("%Y-%m-%d") if (start or end) else "",
        "end": end, "agent": agent, "agent_h": first_name(agent), "flags": flags,
        "ai": ai, "ai_h": en_out(ai), "claimed": claimed, "claimed_h": en_out(claimed), "verdict": verdict,
        "mismatch": real_mismatch(verdict, en_out(claimed), en_out(ai)), "not_filed": (answered == 1 and not claimed and bool(jk)),
        "ai_reason": (row["ai_reason"] or "").strip(), "evidence": (row["evidence"] or "").strip(),
        "jk": jk, "has_rec": has_rec, "has_tx": bool(row["has_tx"]), "tx_head": (row["tx_head"] or "").strip(),
        "dur": dur, "dur_h": dur_h(dur), "ring": ring, "talk": talk,
        "final": (row["final_outcome"] or "").strip(), "note": (row["doctor_note"] or "").strip(),
        "v_name": (row["v_name"] or "").strip(), "v_cid": (row["v_cid"] or "").strip(),
    }
    return it


_WA_STATUS_H = {"delivered": "delivered", "read": "read", "sent": "sent, not yet delivered", "failed": "NOT delivered",
                "pending": "test mode — not sent", "retrying": "MyOperator busy — retrying", "unsure": "may have gone"}


def _who_h(login):
    a = (login or "").strip()
    if a.lower() in ("manoj", "doctor", "dr manoj", "drmanoj"):
        return "you"
    return first_name(a)[:1].upper() + first_name(a)[1:] if a else ""


def wa_item(r):
    """One inbox message -> one timeline item, shaped like a call item so the page draws both. Pure."""
    d = (r["dir"] or "").strip().lower()
    mtype = (r["mtype"] or "text").strip().lower()
    st = (r["status"] or "").strip().lower()
    if d == "in":
        kind = "wa_in"
    elif mtype == "template":
        kind = "wa_tpl"
    elif st == "failed":
        kind = "wa_fail"
    else:
        kind = "wa_out"
    t = parse_ts(r["ts"])
    body = " ".join(str(r["body"] or "").split())
    if not body:
        body = "[" + (mtype or "message") + "]"
    by = (r["sent_by"] or "").strip()
    return {"id": "wa%s" % r["rid"], "ch": "wa", "phone": re.sub(r"\D", "", r["phone"] or "")[-10:], "kind": kind,
            "direction": "In" if d == "in" else "Out", "answered": False, "delivered": (kind == "wa_out" and st in ("delivered", "read")),
            "status": st, "status_h": _WA_STATUS_H.get(st, st), "body": body[:200] + ("…" if len(body) > 200 else ""),
            "t": t, "t_h": t.strftime("%H:%M") if t else "", "day": t.strftime("%Y-%m-%d") if t else "", "end": t,
            "agent": by, "agent_h": _who_h(by), "flags": [], "ai": "", "ai_h": "", "claimed": "", "claimed_h": "",
            "verdict": "", "mismatch": False, "not_filed": False, "ai_reason": "", "evidence": "", "jk": "",
            "has_rec": False, "has_tx": False, "tx_head": "", "dur": 0, "dur_h": "", "ring": 0, "talk": 0,
            "final": "", "note": "", "v_name": "", "v_cid": ""}


def wa_items(path, d_from, d_to, phones=None):
    """The inbox's messages from d_from to d_to (IST days), read-only. ([], False) when the store cannot be read --
    the page then says so; nothing is shown as zero."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (path or INBOX_DB_DEFAULT), uri=True, timeout=3)
        con.row_factory = sqlite3.Row
    except sqlite3.Error:
        return [], False
    try:
        rows = con.execute("SELECT rid, phone, dir, ts, mtype, body, status, sent_by FROM msgs "
                           "WHERE substr(ts,1,10)>=? AND substr(ts,1,10)<=? ORDER BY ts, rid", (d_from, d_to)).fetchall()
    except sqlite3.Error:
        return [], False
    finally:
        con.close()
    out = []
    for r in rows:
        it = wa_item(r)
        if len(it["phone"]) == 10 and (phones is None or it["phone"] in phones):
            out.append(it)
    return out, True


def item_words(it):
    """The timeline line and its sub-line (the mock-up's words)."""
    if it.get("ch") == "wa":
        if it["kind"] == "wa_in":
            return "WhatsApp received", ""
        if it["kind"] == "wa_tpl":
            return "Template sent — not a reply", " · ".join(x for x in (it["agent_h"], it["status_h"]) if x)
        if it["kind"] == "wa_fail":
            return "WhatsApp reply — NOT delivered", it["agent_h"]
        return "WhatsApp reply — " + (it["status_h"] or "sent"), it["agent_h"]
    if it["kind"] == "in_ok":
        line = "Incoming call — answered" + ((" by " + it["agent_h"]) if it["agent_h"] and it["agent_h"] != "you" else (" by you" if it["agent_h"] == "you" else ""))
    elif it["kind"] == "in_miss":
        line = "Missed call" + ((" — rang %d s" % it["ring"]) if it["ring"] else "")
    elif it["kind"] == "out_ok":
        line = "Outgoing call — answered"
    else:
        line = "Outgoing call — not answered"
    sub = []
    if it["kind"] == "in_miss":
        sub.append("no one picked up")
    if it["kind"].startswith("out") and it["agent_h"]:
        sub.append(it["agent_h"])
    if it["kind"] == "out_miss" and it["ring"]:
        sub.append("rang %d s" % it["ring"])
    if it["ai_h"]:
        sub.append("AI: " + it["ai_h"])
    if it["claimed_h"]:
        sub.append("filed: " + it["claimed_h"])
    elif it["not_filed"]:
        sub.append("not logged")
    if it["flags"]:
        sub.append("AI flagged: " + ", ".join(it["flags"]))
    if it["final"]:
        sub.append("your review: " + it["final"])
    return line, " · ".join(sub)


def person_state(items, now):
    """The person's state from the whole timeline (D820, S742). EVERY thing the patient sent is judged by its own rule:
    a missed call is answered only by a connected call after it (either direction); a WhatsApp by wa_answer(). The
    person is green when nothing they sent is left unanswered; otherwise the EARLIEST unanswered one decides: amber when
    someone has tried since (a call, or a real reply still on its way -- never a template, a failed or a test-mode
    message), rose when nobody has. Returns (state, words, since) with state in green|amber|rose|grey."""
    its = sorted(items, key=lambda x: (x["t"] or _dt.datetime.min))
    ins = [it for it in its if it["direction"] == "In"]
    if not ins:
        # staff-initiated only
        if any(it["answered"] for it in its):
            return "green", "called · answered", None
        if any(it["direction"] == "Out" and it.get("ch") != "wa" for it in its):
            return "amber", "tried · not reached", None
        return "grey", "sent only", None

    def after(x):
        if x["t"] is None:                                       # no readable time: the list's own order decides
            return its[its.index(x) + 1:]
        return [it for it in its if it["t"] and it["t"] > x["t"]]

    def answer(x):
        if x.get("ch") == "wa":
            return wa_answer(x, its)
        if x["answered"]:
            return x
        return next((it for it in after(x) if it["answered"] and it.get("ch") != "wa"), None)

    open_ = [x for x in ins if answer(x) is None]
    if not open_:
        last = ins[-1]
        ans = answer(last)
        if last.get("ch") == "wa":
            return "green", ("answered on WhatsApp" if ans.get("ch") == "wa" else "answered by a call"), None
        if ans is last:
            return "green", "answered", None
        gap = ((ans["t"] - last["t"]).total_seconds() / 60.0) if (ans["t"] and last["t"]) else 0
        return "green", ("answered · %d min" % int(gap)) if gap >= 1 else "answered", None
    first = open_[0]

    def tried(it):
        if it["direction"] != "Out":
            return False
        if it.get("ch") == "wa":
            return it["kind"] == "wa_out" and it.get("status") in ("sent", "retrying", "unsure")
        return True
    if any(tried(it) for it in after(first)):
        return "amber", ("tried · not answered yet" if first.get("ch") == "wa" else "tried · not reached"), first["t"]
    if first.get("ch") == "wa":
        return "rose", "WhatsApp awaiting · " + wait_words(wait_h(first["t"], now)), first["t"]
    return "rose", "awaiting · " + wait_words(wait_h(first["t"], now)), first["t"]


def _talk_s(it):
    """The seconds actually spoken: the talk time when the record carries it, else the length less the ring."""
    return it["talk"] if it["talk"] > 0 else max(0, it["dur"] - it["ring"])


def wa_answer(w, its):
    """D820: the first thing after WhatsApp `w` that answers it -- a delivered (or read) reply that is not a template,
    or an answered call of 30 s or more within 2 clinic hours -- or None. Templates and failed replies never count."""
    if w.get("t") is None:
        return None
    for it in sorted(its, key=lambda x: (x["t"] or _dt.datetime.min)):
        if it["t"] is None or it["t"] <= w["t"]:
            continue
        if it.get("ch") == "wa":
            if it["kind"] == "wa_out" and it.get("delivered"):
                return it
        elif it["answered"] and _talk_s(it) >= WA_CALL_MIN_S and wait_h(w["t"], it["t"]) <= WA_CALL_WITHIN_H:
            return it
    return None


def chain_tail(items):
    """What the chain ends with after the last answered call: the outcome word ('booked', 'coming')."""
    for it in reversed(items):
        if it["answered"] and (it["ai_h"] or it["claimed_h"]):
            return it["ai_h"] or it["claimed_h"]
    return ""


def build_people(conn, d_from, d_to, now, q="", wa=None):
    """Rows per person in the window: unknown numbers first, awaiting first within. Pure over console.db (and the
    inbox's items, S742, handed in as `wa`)."""
    patients = {}
    try:
        for r in conn.execute(_PAT_SQL):
            patients[r[0]] = {"name": (r[1] or "").strip(), "dx": (r[2] or "").strip(), "age": (r[3] or "").strip(),
                              "sex": (r[4] or "").strip()[:1].upper(), "cid": (r[5] or "").strip(),
                              "last_visit": (r[6] or "").strip()}
    except Exception:
        patients = {}
    try:
        spam = set(_H["spam_phones"]()) if _H.get("spam_phones") else set()
    except Exception:
        spam = set()
    has_ca = _table_exists(conn, "call_agent")
    sql = _CALLS_SQL if has_ca else _CALLS_SQL.replace(
        "LEFT JOIN call_agent ca ON ca.join_key=c.join_key AND c.join_key<>''",
        "LEFT JOIN (SELECT '' AS join_key, '' AS agent WHERE 0) ca ON 0")
    items = [call_item(r, patients, now) for r in conn.execute(sql, (d_from, d_to))]
    by = {}
    no_number = 0
    for it in items:
        if not it["phone"]:
            no_number += 1
            continue
        by.setdefault(it["phone"], []).append(it)
    for w in (wa or []):                                  # S742: the WhatsApps join the same person's timeline
        by.setdefault(w["phone"], []).append(w)
    people = []
    for ph, its in by.items():
        its.sort(key=lambda x: (x["t"] or _dt.datetime.min, str(x["id"])))
        p = patients.get(ph)
        vname = next((x["v_name"] for x in reversed(its) if x["v_name"]), "")
        vcid = next((x["v_cid"] for x in reversed(its) if x["v_cid"]), "")
        name = (p or {}).get("name") or vname
        cid = (p or {}).get("cid") or vcid
        unknown = (p is None) and not name
        state, words, since = person_state(its, now)
        if ph in spam:                                   # a number the owner marked spam: listed last, counted nowhere
            state, words, since = "grey", "marked spam", None
        n_in = sum(1 for x in its if x["direction"] == "In" and x.get("ch") != "wa")
        n_out = sum(1 for x in its if x["direction"] == "Out" and x.get("ch") != "wa")
        n_wa = sum(1 for x in its if x.get("ch") == "wa")
        last = its[-1]
        row = {
            "phone": ph, "phone_h": fmt_num(ph), "name": name, "cid": cid, "unknown": unknown,
            "dx": (p or {}).get("dx", ""), "agesex": "/".join(x for x in ((p or {}).get("age", ""), (p or {}).get("sex", "")) if x),
            "state": state, "state_h": words, "since": since,
            "n_calls": n_in + n_out, "n_wa": n_wa, "n_in": n_in, "n_out": n_out,
            "n_missed": sum(1 for x in its if x["kind"] == "in_miss"),
            "wa_wait": (state == "rose" and words.startswith("WhatsApp")),
            "flagged": sum(1 for x in its if x["flags"]), "mismatch": sum(1 for x in its if x["mismatch"]),
            "tail": chain_tail(its), "calls": its, "last_t": last["t"], "spam": ph in spam,
            "any_answered": any(x["answered"] for x in its),
            "booked": any((x["ai"] or "").lower().find("book") >= 0 or x["claimed"] == "appointment_booked" for x in its),
        }
        people.append(row)
    order = {"rose": 0, "amber": 1, "green": 2, "grey": 3}
    _epoch = _dt.datetime(2000, 1, 1)
    people.sort(key=lambda r: (r["spam"], not r["unknown"], order.get(r["state"], 9),
                               -((r["last_t"] or _epoch) - _epoch).total_seconds()))
    if q:
        ql = q.lower()
        def hit(r):
            return (ql in r["phone"] or ql in r["name"].lower() or ql in r["dx"].lower() or ql in r["cid"].lower()
                    or any(ql in (x["tx_head"] or "").lower() or ql in (x["evidence"] or "").lower()
                           or ql in (x.get("body") or "").lower() for x in r["calls"]))
        people = [r for r in people if hit(r)]
    return people, items, no_number


def strip_counts(people, items):
    """The strip's figures. Call counts count CALLS only (D820)."""
    c = {"calls": len(items), "callers": len({x["phone"] for x in items if x["phone"]}),
         "in_ok": sum(1 for x in items if x["kind"] == "in_ok"),
         "out_ok": sum(1 for x in items if x["kind"] == "out_ok"),
         "miss_then_ok": 0, "miss_then_back": 0, "miss_then_again": 0, "miss_open": 0,
         "wa_in": sum(1 for p in people for x in p["calls"] if x["kind"] == "wa_in"),
         "wa_people": sum(1 for p in people if any(x["kind"] == "wa_in" for x in p["calls"])),
         "wa_replied": sum(1 for p in people for x in p["calls"] if x["kind"] == "wa_out" and x.get("delivered")),
         "awaiting": sum(1 for p in people if p["state"] == "rose"),
         "tried": sum(1 for p in people if p["state"] == "amber"),
         "answered": sum(1 for p in people if p["state"] == "green"),
         "flagged": sum(1 for x in items if x["flags"]), "mismatch": sum(1 for x in items if x["mismatch"])}
    for p in people:
        its = [x for x in p["calls"] if x.get("ch") != "wa"]
        for i, it in enumerate(its):
            if it["kind"] == "in_miss":
                nxt = next((y for y in its[i + 1:] if y["answered"]), None)
                if nxt is not None:
                    c["miss_then_ok"] += 1
                    # S742: the arrow the way it happened -- we called back, or they rang again and got through
                    c["miss_then_again" if nxt["direction"] == "In" else "miss_then_back"] += 1
                else:
                    c["miss_open"] += 1
    tot = c["awaiting"] + c["tried"] + c["answered"]
    if tot:
        c["bar"] = {"g": int(round(100.0 * c["answered"] / tot)), "w": int(round(100.0 * c["tried"] / tot))}
        c["bar"]["b"] = max(0, 100 - c["bar"]["g"] - c["bar"]["w"])
    else:
        c["bar"] = {"g": 0, "w": 0, "b": 0}          # an empty day: the bar stays grey
    return c


def needs_you(people, items, now):
    """The Needs-you lines, calls only: unknown callers nobody answered (rose), AI-flagged calls (amber),
    staff ≠ AI (amber). Each line is an icon chain, as the mock-up."""
    out = []
    for p in people:
        if p["state"] == "rose" and not p["spam"]:
            out.append({"tone": "rose", "who": (p["name"] + (" · " + p["cid"] if p["cid"] else "")) if p["name"] else p["phone_h"], "unknown": p["unknown"],
                        "name": p["name"], "cid": p["cid"], "chain": p["calls"][-3:],
                        "text": "WhatsApp not answered" if p.get("wa_wait") else "nobody has answered",
                        "sub": "waiting " + wait_words(wait_h(p["since"], now)) if p["since"] else "",
                        "n": p["n_missed"] or 1, "act": "call", "phone": p["phone"], "anchor": "p" + p["phone"]})
    for p in people:
        for it in p["calls"]:
            if it["flags"]:
                out.append({"tone": "amber", "who": (p["name"] + (" · " + p["cid"] if p["cid"] else "")) if p["name"] else p["phone_h"],
                            "name": p["name"], "cid": p["cid"], "chain": [it],
                            "text": "AI heard “" + (it["evidence"] or it["ai_reason"] or ", ".join(it["flags"])) + "”",
                            "sub": ((it["agent_h"] + "'s call" if it["agent_h"] not in ("", "you") else "your own call") + ((" · ▶ " + it["dur_h"]) if it["dur_h"] else "")),
                            "n": 1, "act": "listen" if it["has_rec"] else "", "jk": it["jk"], "anchor": "p" + p["phone"]})
    for p in people:
        for it in p["calls"]:
            if it["mismatch"] and not it["final"]:
                out.append({"tone": "amber", "who": (p["name"] + (" · " + p["cid"] if p["cid"] else "")) if p["name"] else p["phone_h"],
                            "name": p["name"], "cid": p["cid"], "chain": [it],
                            "text": (it["agent_h"] or "staff") + " logged “" + (it["claimed_h"] or "—") + "”; the recording says “" + (it["ai_h"] or "—") + "”",
                            "sub": "staff ≠ AI — to check", "n": 1, "act": "review", "jk": it["jk"], "anchor": "p" + p["phone"]})
    return out


# ---------------------------------------------------------------------------------------------- S742: the follow-ups
def _ro():
    import ring_outcome as _r                       # the Call-ke-baad list's own module (read-only readers)
    return _r


def _fu_source(conn):
    """(rows, source, found): fu_all (the whole feed, S742's builder) when it is there; else the old no_shows rows
    (due before today only) for the minutes between the install and the next reading."""
    def meta_found(k):
        try:
            m = conn.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
            return bool(json.loads(m[0]).get("found")) if m else None
        except Exception:
            return None
    if _table_exists(conn, "fu_all"):
        try:
            rows = [tuple(r) for r in conn.execute(
                "SELECT key, section, name, phone10, dx, due_date, status_raw FROM fu_all")]
            return rows, "fu_all", meta_found("fu_all")
        except Exception:
            pass
    if _table_exists(conn, "no_shows"):
        try:
            rows = [("", "", r[0], r[1], "", r[2], r[3]) for r in conn.execute(
                "SELECT name, phone10, due_date, status_raw FROM no_shows")]
            return rows, "no_shows", meta_found("followups_feed")
        except Exception:
            pass
    return [], "", False


def fu_clean(rows, today):
    """ONE open row per patient: the rows grouped by mobile (a row with no mobile by its name), the LATEST due date
    kept, a due date after today left out. Returns (list, repeats_removed). Pure."""
    groups, removed, later = {}, 0, set()
    for key, sec, name, ph, dx, due, st in rows:
        try:
            dd = _dt.date.fromisoformat(str(due or "")[:10])
        except Exception:
            continue
        p = re.sub(r"\D", "", str(ph or ""))[-10:]
        p = p if len(p) == 10 else ""
        g = p or ("n:" + " ".join(str(name or key or "").lower().split()))
        if g == "n:":
            continue
        if dd > today:
            later.add(g)                     # a patient given a later date is not chased on an old one
            continue
        row = {"phone": p, "name": str(name or "").strip(), "dx": str(dx or "").strip(), "section": str(sec or "").strip(),
               "status": str(st or "").strip(), "dd": dd, "due": dd.isoformat()}
        cur = groups.get(g)
        if cur is None:
            groups[g] = row
            continue
        removed += 1
        if dd > cur["dd"]:
            groups[g] = row
    for g in later:
        if g in groups:
            groups.pop(g)
            removed += 1
    return list(groups.values()), removed


def fu_band(age):
    return "today" if age <= 0 else ("grace" if age <= 3 else ("overdue" if age <= 14 else "lapsed"))


def fu_row_state(r, tries, visit, today, strict=False, hist=None):
    """Where one follow-up stands, from what happened since its due date. Pure.
    closed: came (a Docterz visit that counts as the return, D893) . notcoming (staff filed "not coming") . else open.
    S817 (F-1322, the owner 13-Nov): strict (the Grace and older sections) -> a CALL counts for the patient only when it
    was made on a day AFTER the due date; the Today section (strict False) counts today's calls. A "not coming" filed on
    the due day still closes the row, and the WhatsApps are read as before (on or after the due day). `hist` = every
    call to the row's mobile that the page read (FU_BACK_DAYS), for 'last reached' (D899)."""
    all_calls = [t for t in tries if t.get("ch") != "wa"]
    calls = [t for t in all_calls if t["day"] > r["due"]] if strict else all_calls
    wa = [t for t in tries if t.get("ch") == "wa"]
    seen = sorted(calls + wa, key=lambda x: (x["t"] or _dt.datetime.min, str(x["id"]))) if strict else tries
    out_calls = [t for t in calls if t["direction"] == "Out"]
    ans = [t for t in calls if t["answered"]]
    nc = next((t for t in all_calls if (t.get("claimed") or "").strip().lower() in NOT_COMING), None)
    tday = today.isoformat()
    r["called"] = bool(out_calls)
    r["reached"] = bool(ans)
    r["called_today"] = any(t["day"] == tday for t in out_calls)
    r["reached_today"] = any(t["day"] == tday for t in ans)
    r["called_before"] = any(t["day"] < tday for t in out_calls)      # an earlier day, after the due date
    r["reached_before"] = any(t["day"] < tday for t in ans)
    # the folded line's own figures: a patient who rang in and was answered counts as called AND reached for that day,
    # so "Reached" can never exceed "Called" (only out["fl"] reads these two)
    r["line_today"] = r["called_today"] or r["reached_today"]
    r["line_before"] = r["called_before"] or r["reached_before"]
    r["closed"], r["closed_day"], r["nc_filed"] = "", None, nc is not None
    if visit is not None:
        r["closed"], r["closed_day"] = "came", visit
    elif nc is not None:
        r["closed"], r["closed_day"] = "notcoming", (nc["t"].date() if nc["t"] else today)
    last_ans = ans[-1] if ans else None
    outcome = ""
    if last_ans is not None:
        outcome = last_ans["claimed_h"] or last_ans["ai_h"]
    ai_nc = bool(last_ans is not None and (last_ans["ai"] or "").strip().lower() in NOT_COMING
                 and not (last_ans["claimed"] or "").strip())
    wa_wait = next((w for w in reversed(wa) if w["kind"] == "wa_in" and wa_answer(w, tries) is None), None)
    if r["closed"] == "came":
        pill, tone = "Came ✓ (Docterz %s)" % visit.strftime("%-d %b"), "green"
    elif r["closed"] == "notcoming":
        pill, tone = "Not coming — filed by " + (nc["agent_h"] or "staff"), "grey"
    elif not seen:
        pill, tone = "Not called yet", "rose"
    elif wa_wait is not None:
        pill, tone = "Wrote back · to call", "amber"
    elif ai_nc:
        pill, tone = "AI heard “not coming” — not filed", "amber"
    elif last_ans is not None:
        pill, tone = ("Reached · " + outcome) if outcome else "Reached", "green"
    elif out_calls:
        n = sum(1 for t in out_calls if not t["answered"])
        pill, tone = ("Not reached × %d" % n) if n > 1 else "Not reached", "amber"
    else:
        pill, tone = "Not called yet", "rose"
    quote = ""
    if wa_wait is not None:
        quote = "WhatsApp: “" + wa_wait["body"][:90] + "”"
    elif last_ans is not None and (last_ans["evidence"] or last_ans["tx_head"]):
        quote = "AI heard: “" + (last_ans["evidence"] or last_ans["tx_head"])[:90] + "”"
    # S817: the row's own lines (the mock-up's words) -- the latest call that counts, and when the patient was last reached
    lc = out_calls[-1] if out_calls else None
    call_line = ""
    if lc is not None:
        call_line = "%s — called, %s%s%s" % (_when_h(lc["t"], today) or "time not known",
                                             "answered" if lc["answered"] else "no answer",
                                             (" (" + lc["agent_h"] + ")") if lc["agent_h"] else "",
                                             (" · %d calls since the due date" % len(out_calls)) if (strict and len(out_calls) > 1) else "")
    la = next((t for t in reversed(hist or []) if t.get("ch") != "wa" and t["answered"] and t["t"] is not None), None)
    last_reached = None
    if la is not None:
        said = " · ".join(x for x in (la["claimed_h"] or la["ai_h"], ("“" + la["evidence"][:90] + "”") if la["evidence"] else "") if x)
        rel = "" if la["day"] > r["due"] or not strict else ("on the due date" if la["day"] == r["due"] else "before the due date")
        last_reached = {"when_h": _when_h(la["t"], today), "said": said, "rel": rel, "jk": la["jk"],
                        "has_rec": bool(la["jk"] and la["has_rec"]), "dur_h": la["dur_h"], "tx_head": la["tx_head"],
                        "has_tx": bool(la["has_tx"]), "who": la["agent_h"], "day": la["day"]}
    r.update({"pill": pill, "tone": tone, "quote": quote, "tries": seen[-4:], "n_tries": len(seen),
              "play": next((t for t in reversed(calls) if t["jk"] and t["has_rec"]), None),
              "call_line": call_line, "last_reached": last_reached,
              "note_h": pill if (not r["closed"] and (wa_wait is not None or ai_nc)) else ""})
    return r


def _cid_key(v):
    """A clinic ID as text ('1234.0' -> '1234'), for matching one store's ID to another's."""
    s = str(v if v is not None else "").strip()
    return s[:-2] if re.match(r"^\d+\.0$", s) else s


def _when_h(t, today):
    """'Today 10:42 am' / 'Thu 12 Nov, 4:12 pm' (the mock-up's words)."""
    if t is None:
        return ""
    hm = t.strftime("%-I:%M %p").lower()
    return ("Today " + hm) if t.date() == today else (t.strftime("%a %-d %b, ") + hm)


def fu_advice(db_path, lo, today):
    """S817 (D893): the advised period of a follow-up, read-only from finance.db's dx_visit (the Clinical data report: each
    visit and the follow-up date given at it). {"ok", "by": {(clinic ID, due day): the day of the LATEST visit before it at
    which that date was advised}}. ok False when the table cannot be read -- every row then keeps the old rule (only a
    visit on or after the due date closes it). Never raises."""
    out = {"ok": False, "by": {}}
    if not db_path:
        return out
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=3)
    except sqlite3.Error:
        return out
    try:
        rows = con.execute("SELECT clinic_id, visit_date, follow_up_date FROM dx_visit "
                           "WHERE substr(follow_up_date,1,10)>=? AND substr(follow_up_date,1,10)<=?",
                           (lo.isoformat(), today.isoformat())).fetchall()
    except sqlite3.Error:
        return out
    finally:
        con.close()
    for cid, vd, fu in rows:
        k = _cid_key(cid)
        try:
            v = _dt.date.fromisoformat(str(vd or "")[:10])
            f = _dt.date.fromisoformat(str(fu or "")[:10])
        except Exception:
            continue
        if not k or v >= f:
            continue
        cur = out["by"].get((k, f))
        if cur is None or v > cur:
            out["by"][(k, f)] = v
    out["ok"] = True
    return out


def fu_return_day(dd, id_days, fp_days, presc, lo=None):
    """D893, in one place: the day of the visit that closes a follow-up due on `dd`, or None (the row stays). Pure.
      . a visit on or after the due date closes it -- by the clinic ID or by the mobile's fingerprint, as before, and
        only among the days the page has always read (from `lo`, at most 60 days back): a row due longer ago than that
        is not closed here by a visit older than `lo`;
      . when the advised period can be read (`presc` = the day of the visit at which this follow-up was advised), a visit
        of the SAME clinic ID after that visit and from half the advised period before the due date (at least 1 day)
        closes it too -- never the prescribing visit itself, never a visit matched on the mobile alone;
      . presc None (the advised period cannot be read) -> the first rule alone, so the patient stays on the list."""
    ds = [d for d in list(id_days) + list(fp_days) if d >= dd and (lo is None or d >= lo)]
    if presc is not None and presc < dd:
        start = dd - _dt.timedelta(days=max(1, int((dd - presc).days * FU_EARLY_SHARE)))
        ds += [d for d in id_days if presc < d and start <= d < dd]
    return min(ds) if ds else None


def followup_list(conn, now, fin_db=None, inbox_path=None):
    """The cleaned follow-up list, every section with its counts. Read-only. Never raises.
    S817: only patients who have not come back by D893 stay on the list (fu_return_day); in Grace and older a call counts
    only from the day after the due date (fu_row_state strict); each section carries its line -- called today, reached
    today, and the earlier days after the due date (out["fl"]); each row its last answered call (D899)."""
    today = now.date()
    out = {"found": False, "src": "", "bands": [], "came": [], "today": {}, "who": [], "visits_ok": False,
           "removed": 0, "open": 0, "wa_ok": True, "fl": {}, "advice_ok": False, "advised": 0, "early": 0, "dropped": 0}
    try:
        raw, src, found = _fu_source(conn)
        out["src"], out["found"] = src, (bool(raw) if found is None else found)     # the builder's word wins when it gave one
        rows, out["removed"] = fu_clean(raw, today)
        if not rows:
            out["bands"] = [(k, t, s, [], 0, 0, 0, "green") for k, t, s in FU_BANDS]
            out["fl"] = {k: {"n": 0, "ct": 0, "rt": 0, "ec": 0, "er": 0, "tone": "green"} for k, _t, _s in FU_BANDS}
            return out
        pats = {}
        try:
            for r in conn.execute(_PAT_SQL):
                pats[r[0]] = r
        except Exception:
            pats = {}
        lo = max(min(r["dd"] for r in rows), today - _dt.timedelta(days=60))
        lo_c = today - _dt.timedelta(days=FU_BACK_DAYS)          # S817: the calls, for 'last reached' (D899)
        phones = {r["phone"] for r in rows if r["phone"]}
        has_ca = _table_exists(conn, "call_agent")
        sql = _CALLS_SQL if has_ca else _CALLS_SQL.replace(
            "LEFT JOIN call_agent ca ON ca.join_key=c.join_key AND c.join_key<>''",
            "LEFT JOIN (SELECT '' AS join_key, '' AS agent WHERE 0) ca ON 0")
        by = {}
        for row in conn.execute(sql, (min(lo, lo_c).isoformat(), today.isoformat())):
            it = call_item(row, pats, now)
            if it["phone"] in phones:
                by.setdefault(it["phone"], []).append(it)
        wa, out["wa_ok"] = wa_items(inbox_path, lo.isoformat(), today.isoformat(), phones)
        for w in wa:
            by.setdefault(w["phone"], []).append(w)
        for v in by.values():
            v.sort(key=lambda x: (x["t"] or _dt.datetime.min, str(x["id"])))
        for r in rows:
            p = pats.get(r["phone"]) if r["phone"] else None
            r["cid"] = ((p[5] or "").strip() if p else "")
        adv = {"ok": False, "by": {}}
        try:
            R = _ro()
            adv = fu_advice(fin_db or getattr(R.rc, "FINANCE_DB", None), min(r["dd"] for r in rows), today)
            prescs = [adv["by"][k] for k in ((_cid_key(r["cid"]), r["dd"]) for r in rows if r["cid"]) if k in adv["by"]]
            visits = R.visits_since(min([lo] + prescs).isoformat(), today, fin_db)
        except Exception:
            R, visits = None, {"ok": False, "by_id": {}, "by_fp": {}}
        out["visits_ok"] = bool(visits.get("ok"))
        out["advice_ok"] = bool(adv.get("ok"))
        ids_n = {}                                   # the visits by clinic ID, '12.0' and '12' one ID (as dx_visit is matched)
        for k_, v_ in (visits.get("by_id") or {}).items():
            ids_n.setdefault(_cid_key(k_), []).extend(v_)
        bands = {k: [] for k, _t, _s in FU_BANDS}
        who, fps, t_closed = {}, {}, []
        for r in rows:
            p = pats.get(r["phone"]) if r["phone"] else None
            r["name"] = r["name"] or ((p[1] or "").strip() if p else "")
            r["dx"] = r["dx"] or ((p[2] or "").strip() if p else "")
            r["phone_h"] = fmt_num(r["phone"])
            r["due_h"] = r["dd"].strftime("%-d %b")
            r["due_wd"] = r["dd"].strftime("%a %-d %b")
            r["age"] = (today - r["dd"]).days
            hist = by.get(r["phone"], []) if r["phone"] else []
            tries = [t for t in hist if t["day"] and t["day"] >= r["due"]]
            visit, was = None, None
            presc = adv["by"].get((_cid_key(r["cid"]), r["dd"])) if (r["cid"] and adv.get("ok")) else None
            r["advised"] = (r["dd"] - presc).days if presc is not None else None
            if presc is not None:
                out["advised"] += 1
            if visits.get("ok"):
                ds_id = list(ids_n.get(_cid_key(r["cid"]), ())) if r["cid"] else []
                ds_raw = list(visits["by_id"].get(r["cid"], ())) if r["cid"] else []     # as the page matched before
                ds_fp = []
                if r["phone"] and R is not None:
                    if r["phone"] not in fps:
                        try:
                            fps[r["phone"]] = R._mobile_fp(r["phone"])
                        except Exception:
                            fps[r["phone"]] = ""
                    fp = fps[r["phone"]]
                    if fp:
                        ds_fp = [d for d, _c in visits["by_fp"].get(fp, ())]
                    else:
                        out["visits_ok"] = False     # the fingerprint could not be made: said on the page, as the list does
                visit = fu_return_day(r["dd"], ds_id, ds_fp, presc, lo)
                was = fu_return_day(r["dd"], ds_raw, ds_fp, None, lo)        # the rule before this kit, exactly
            fu_row_state(r, tries, visit, today, strict=(r["age"] > 0), hist=hist)
            if visit is not None and was is None and not r["nc_filed"]:
                out["dropped"] += 1                  # a row the page before this kit would have left open
                if visit < r["dd"]:
                    out["early"] += 1                # ... closed by a visit before the due date (D893)
            for t in tries:
                if t.get("ch") != "wa" and t["direction"] == "Out" and t["day"] == today.isoformat():
                    who.setdefault(t["agent_h"] or "staff", set()).add(r["phone"])
            if r["closed"]:
                if r["dd"] == today:
                    t_closed.append(r)               # today's line and the strip: every closed row due today
                if r["closed_day"] and r["closed_day"] >= today - _dt.timedelta(days=6):
                    out["came"].append(r)
                continue
            bands[fu_band(r["age"])].append(r)
        order = {"rose": 0, "amber": 1, "green": 2, "grey": 3}
        for k, title, sub in FU_BANDS:
            lst = sorted(bands[k], key=lambda x: (order.get(x["tone"], 9), x["dd"], x["name"]))
            n, called = len(lst), sum(1 for x in lst if x["called"])
            reached = sum(1 for x in lst if x["reached"])
            ct = sum(1 for x in lst if x["line_today"])
            tone = "green" if ct == n else ("rose" if ct == 0 else "amber")      # S817: by the calls made TODAY
            out["bands"].append((k, title, sub, lst, n, called, reached, tone))
            out["fl"][k] = {"n": n, "ct": ct, "rt": sum(1 for x in lst if x["reached_today"]),
                            "ec": sum(1 for x in lst if x["line_before"]),
                            "er": sum(1 for x in lst if x["reached_before"]), "tone": tone}
            out["open"] += n
        out["came"].sort(key=lambda x: (x["closed_day"] or today), reverse=True)
        t_open = bands["today"]
        t_came = t_closed            # NOT the 7-day 'Came / closed' list: a row due today that an earlier visit closed stays in 'due'
        out["today"] = {"due": len(t_open) + len(t_came), "called": sum(1 for x in t_open + t_came if x["called"]),
                        "reached": sum(1 for x in t_open + t_came if x["reached"]),
                        "came": sum(1 for x in t_came if x["closed"] == "came")}
        out["who"] = sorted(((k, len(v)) for k, v in who.items()), key=lambda x: -x[1])
    except Exception:
        out["found"] = False
    return out


def ckb_week(now, fin_db=None):
    """Call ke baad, the last 7 days: appointments booked on a call -> came / still awaited / never came, per staff.
    The list's own rule and readers (ring_outcome.list_data, read-only). Never raises."""
    out = {"ok": False, "booked": 0, "came": 0, "due": 0, "noshow": 0, "staff": [], "never": [], "from": "", "to": ""}
    try:
        R = _ro()
        L = R.list_data(span="7", now=now, finance_db=fin_db)
    except Exception:
        return out
    if not L.get("store_ok"):
        return out
    today = now.date()
    back = today - _dt.timedelta(days=6)
    out.update({"ok": True, "visits_ok": bool(L.get("visits_ok")), "from": back, "to": today})
    st = {}
    for key in ("came", "due", "noshow"):
        for r in L.get(key) or []:
            if not r.get("booked") or r["booked"] < back:
                continue
            try:
                who = R._person(r.get("login"), r.get("handler"))
            except Exception:
                who = str(r.get("handler") or r.get("login") or "staff")
            s = st.setdefault(who or "staff", {"booked": 0, "came": 0, "due": 0, "noshow": 0})
            s["booked"] += 1
            s[key] += 1
            out["booked"] += 1
            out[key] += 1
            if key == "noshow":
                m10 = re.sub(r"\D", "", str(r.get("mobile") or ""))[-10:]
                out["never"].append({"name": str(r.get("patient") or "").strip(), "cid": str(r.get("clinic_id") or "").strip(),
                                     "phone": m10 if len(m10) == 10 else "", "phone_h": fmt_num(m10),
                                     "booked_h": r["booked"].strftime("%-d %b"),
                                     "appt_h": r["appt"].strftime("%-d %b") if r.get("appt") else "",
                                     "who": who or "staff", "known": bool(r.get("known"))})
    out["staff"] = sorted(st.items(), key=lambda x: -x[1]["booked"])
    return out


# ---------------------------------------------------------------------------------------------- S744: staff cards
STAFF_MASTER_DEFAULT = "/root/staff_master.csv"     # duty times only are read (never a pay column)
PUNCH_CSV_DEFAULT = "/root/punches.csv"              # the biometric machine's punch log (the attendance listener's)
CALLBACK_MIN = 60                                    # a missed call called back within the hour
PHONE_STAFF_DEFAULT = "shivani,alisha"               # S745, the owner's roster (02-Nov): who answers the clinic line
OWNER_FIRST = ("manoj",)                             # S745: the owner's own agent is never a card
RECEPTION_DEFAULT = "reception"                      # S747 (F-1168): the reception mobile's MyOperator agent, by first name
REVIEW_DB_DEFAULT = "/root/portal/call_review.db"    # S747: the owner's review buttons and the staff's disputes -- this module's own store
REVIEW_ACTS = ("ask_log", "reviewed", "staff_right", "ai_right", "undo", "note")
REVIEWED = ("reviewed", "staff_right", "ai_right")
REVIEW_WORDS = {"reviewed": "Reviewed", "staff_right": "Staff right", "ai_right": "AI right"}
FIGS = ("missed", "wa", "not_logged", "mismatch")    # the figures a staff member may dispute, one call at a time
FIG_SHORT = {"not_back": "missed on duty, not called back", "not_logged": "not logged", "mismatch": "staff ≠ AI",
             "wa": "WhatsApp not answered", "missed": "missed on duty"}
FIG_WORDS = {"missed": "counted as missed on duty", "wa": "counted as a WhatsApp not answered",
             "not_logged": "counted as not logged", "mismatch": "counted as staff ≠ AI"}
_REF = re.compile(r"^(\d{10}_\d{9,12}|c\d{1,12}|wa\d{1,12})$")
_RV_SQL = (
    "CREATE TABLE IF NOT EXISTS review (id INTEGER PRIMARY KEY, ref TEXT NOT NULL, staff TEXT NOT NULL, act TEXT NOT NULL, "
    "note TEXT NOT NULL DEFAULT '', by_whom TEXT NOT NULL, at TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS review_ref ON review(ref, staff)",
    "CREATE TABLE IF NOT EXISTS dispute (id INTEGER PRIMARY KEY, ref TEXT NOT NULL, staff TEXT NOT NULL, fig TEXT NOT NULL, "
    "text TEXT NOT NULL, call_h TEXT NOT NULL DEFAULT '', by_whom TEXT NOT NULL, at TEXT NOT NULL, "
    "answer TEXT NOT NULL DEFAULT '', answer_note TEXT NOT NULL DEFAULT '', answer_by TEXT NOT NULL DEFAULT '', "
    "answer_at TEXT NOT NULL DEFAULT '')",
    "CREATE INDEX IF NOT EXISTS dispute_staff ON dispute(staff, answer)",
)


def iref(it):
    """One call's or WhatsApp's own reference: its join key, else 'c<id>' (a call) or 'wa<rid>' (a WhatsApp). S747."""
    if it.get("jk"):
        return it["jk"]
    return str(it["id"]) if it.get("ch") == "wa" else "c%s" % it["id"]


def rv_init(path):
    """Create the review store's tables (the installer, and every write). Never drops or changes a row."""
    con = sqlite3.connect(path, timeout=5)
    try:
        for s in _RV_SQL:
            con.execute(s)
        con.commit()
    finally:
        con.close()


def rv_read(path):
    """The review store, read-only: ({(ref, staff): {state, at, asked, notes[(at, text)]}}, [dispute rows], ok). A store
    that cannot be read gives ({}, [], False): the cards then count every call as before and the page says so."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=3)
        con.row_factory = sqlite3.Row
    except sqlite3.Error:
        return {}, [], False
    st = {}
    try:
        for r in con.execute("SELECT ref, staff, act, note, at FROM review ORDER BY id"):
            e = st.setdefault((r["ref"], r["staff"]), {"state": "", "at": "", "asked": "", "notes": []})
            if r["act"] == "note":
                e["notes"].append((r["at"], r["note"]))
            elif r["act"] == "undo":
                e["state"], e["at"], e["asked"] = "", r["at"], ""
            elif r["act"] == "ask_log":
                e["asked"] = r["at"]
            elif r["act"] in REVIEWED:
                e["state"], e["at"] = r["act"], r["at"]
        ds = [dict(r) for r in con.execute("SELECT id, ref, staff, fig, text, call_h, by_whom, at, answer, answer_note, "
                                           "answer_by, answer_at FROM dispute ORDER BY id")]
    except sqlite3.Error:
        return {}, [], False
    finally:
        con.close()
    return st, ds, True


def _rv_write(path, sql, args):
    rv_init(path)
    con = sqlite3.connect(path, timeout=5)
    try:
        cur = con.execute(sql, args)
        con.commit()
        return cur.rowcount
    finally:
        con.close()


def _stamp(now=None):
    return now_ist(now).strftime("%Y-%m-%d %H:%M:%S")


def login_key(login):
    """A login -> the card it reads: the setting PORTAL_CARD_LOGINS ('login:key,...') first, else the login's first word in
    small letters when it is letters only ('Shivani' -> 'shivani'); a login like 'shivani2' reads no card -- never a near
    name (the cold review's should-fix 1). S747."""
    lg = " ".join(str(login or "").lower().split())
    for part in str(_cfg_path("PORTAL_CARD_LOGINS", "") or "").split(","):
        if ":" in part:
            x, y = part.split(":", 1)
            if x.strip().lower() == lg and y.strip():
                return re.sub(r"[^a-z]", "", y.strip().lower())
    first = lg.split()[0] if lg else ""
    return first if re.match(r"^[a-z]{1,30}$", first) else ""


def _hm(s):
    try:
        return _dt.datetime.strptime((s or "").strip(), "%H:%M").time()
    except Exception:
        return None


def load_duty(master_path=None, punch_path=None, days=()):
    """({first-name: {name, shifts}}, {first-name: {day: first punch}}, ok). Read-only, fail-soft: (…, False) when a
    file cannot be read -- the cards then say the duty is not known. Only user_id, name, the four time columns and
    active are read from the master."""
    import csv
    staff, punches, ok = {}, {}, True
    uid_name = {}
    try:
        with open(master_path or STAFF_MASTER_DEFAULT, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if (row.get("active") or "Y").strip().upper() == "N":
                    continue
                nm = " ".join((row.get("name") or "").split())
                if not nm:
                    continue
                key = nm.split()[0].lower()
                uid = _uid(row.get("user_id"))
                if not uid:
                    continue
                ent = {"name": nm, "wd": (_hm(row.get("wd_start")), _hm(row.get("wd_end"))),
                       "sun": (_hm(row.get("sun_start")), _hm(row.get("sun_end"))), "uid": uid}
                if key in staff:                           # two staff share a first name: neither is matched (never a guess)
                    staff[key] = None
                else:
                    staff[key] = ent
                uid_name[ent["uid"]] = key
    except Exception:
        return {}, {}, False
    if not staff:
        staff["\x00read"] = None                      # the list was read but holds no usable row (kept apart from unreadable)
    want = set(days)
    try:
        with open(punch_path or PUNCH_CSV_DEFAULT, newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            if not {"user_id", "datetime"} <= set(rd.fieldnames or []):
                raise ValueError("the punch log's columns")
            for row in rd:
                ds = (row.get("datetime") or "").strip().replace("T", " ")
                if ds[:10] not in want:
                    continue
                key = uid_name.get(_uid(row.get("user_id")))
                if not key:
                    continue
                t = parse_ts(ds)
                if t is None:
                    continue
                cur = punches.setdefault(key, {}).get(ds[:10])
                if cur is None or t < cur:
                    punches[key][ds[:10]] = t
    except Exception:
        ok = False
    return {k: v for k, v in staff.items() if v}, punches, ok


def _uid(v):
    v = str(v or "").strip()
    try:
        return str(int(v))                      # '007' and '7' are one person
    except ValueError:
        return ""


def duty_window(ent, day, punch):
    """(start, end) datetimes of one person's duty on one day, or None when off or not punched in. A Sunday follows the
    Sunday columns (empty = off); the duty starts at the shift start, or at the punch when that is later."""
    d = _dt.date.fromisoformat(day)
    a, b = ent["sun"] if d.weekday() == 6 else ent["wd"]
    if not a or not b or punch is None:
        return None
    start = max(_dt.datetime.combine(d, a), punch)
    end = _dt.datetime.combine(d, b)
    return (start, end) if end > start else None


def roster_window(ent, day):
    """S762: (start, end) of one person's rostered shift on one day, whatever the punch says; None when off."""
    d = _dt.date.fromisoformat(day)
    a, b = ent["sun"] if d.weekday() == 6 else ent["wd"]
    if not a or not b:
        return None
    s_, e_ = _dt.datetime.combine(d, a), _dt.datetime.combine(d, b)
    return (s_, e_) if e_ > s_ else None


def staff_cards(people, d_from, d_to, now, master_path=None, punch_path=None, agents=None, phone_staff=None, rv=None,
                reception=None, split=False):
    """One card per person who handled calls in the window (the clinic's MyOperator agents; your own calls are not a
    card). Figures from the timelines already built for the page; the duty from the master and the punch. Pure but for
    the two read-only files.
    S747: `rv` is the review store as rv_read() gives it -- a call the owner reviewed leaves the 'to check' lists for
    'Reviewed by you'; a dispute he accepted takes that call off that person's figures. A call on the reception mobile
    (`reception`, its agent's first name) is credited to the ONE phone staff member on duty at that minute; with both or
    neither on duty, or their duty unknown, it stays on a 'Reception mobile' card that says why."""
    d0, d1 = _dt.date.fromisoformat(d_from), _dt.date.fromisoformat(d_to)
    days = [(d0 + _dt.timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]
    staff, punches, duty_ok = load_duty(master_path, punch_path, days)
    master_ok = bool(staff) or (duty_ok is not False and os.path.exists(master_path or STAFF_MASTER_DEFAULT))
    punch_ok = duty_ok or not master_ok                # ... and (staff, {}, False) when only the punch log is
    agents = agents or {}                              # first name -> the full MyOperator agent names that carry it
    rst, rdisp, rv_ok = rv if rv is not None else ({}, [], True)
    rec = (str(reception or "").strip().lower() or RECEPTION_DEFAULT).split()[0]
    phone = [k.split()[0].lower() for k in (phone_staff or PHONE_STAFF_DEFAULT).split(",") if k.strip()]   # first names
    pwins = {}                                         # the phone staff's duty windows, to tell when someone else is covering
    for k in phone:
        e = staff.get(k) if len(agents.get(k, ())) <= 1 else None
        if e:
            pwins[k] = {d: w for d in days for w in [duty_window(e, d, punches.get(k, {}).get(d))] if w}
    phone_known = all(k in pwins for k in phone)       # an unmatched phone staff member would make everyone "covering"
    today_iso_ = now.strftime("%Y-%m-%d")

    def pre_punch(k, t):
        """S762 (the owner, 09:27 IST 09-Nov): a call missed in phone staff member k's ROSTERED shift before she punched in
        counts on her card, marked 'before punch-in' -- when she punched in later that day, or today before she has punched.
        A past day with no punch at all is not hers (she was not there; the card says 'did not punch')."""
        if t is None or k not in phone or not punch_ok:   # cold review MF1: an unreadable punch log charges nobody
            return False
        e = staff.get(k) if len(agents.get(k, ())) <= 1 else None
        if not e:
            return False
        d = t.strftime("%Y-%m-%d")
        rw = roster_window(e, d)
        if not rw or not (rw[0] <= t <= rw[1]):
            return False
        w = pwins.get(k, {}).get(d)
        if w and w[0] <= t <= w[1]:
            return False                               # on duty by the punch: an ordinary miss
        pu = punches.get(k, {}).get(d)
        return (pu is not None and t < pu) or (pu is None and d == today_iso_)

    def phone_has(k, t):
        """S762: phone staff member k answers for a miss at t -- on duty by the punch, or before her punch-in."""
        if t is None:
            return False
        w = pwins.get(k, {}).get(t.strftime("%Y-%m-%d"))
        return bool(w and w[0] <= t <= w[1]) or pre_punch(k, t)

    def phone_on(t):
        if t is None:
            return False
        d = t.strftime("%Y-%m-%d")
        return any(w.get(d) and w[d][0] <= t <= w[d][1] for w in pwins.values())

    def phone_who(t):
        """(the ONE phone staff member on duty at t, '') or (None, why). S747."""
        if t is None:
            return None, "the call carries no time"
        if not phone_known or not punch_ok:
            return None, "the phone staff's duty is not known"
        d = t.strftime("%Y-%m-%d")
        on = [k for k in phone if pwins[k].get(d) and pwins[k][d][0] <= t <= pwins[k][d][1]]
        if len(on) == 1:
            return on[0], ""
        return None, ("two phone staff on duty" if on else "no phone staff on duty")
    cards = {}
    calls = []
    eff, rec_why = {}, {}                              # S747: the card each call belongs to; why a reception call is not credited
    for p in people:
        for it in p["calls"]:
            it["ref"] = iref(it)
            if it.get("ch") == "wa":
                continue
            calls.append((p, it))
            ah = (it.get("agent_h") or "").strip().lower()
            if not ah or ah == "you" or ah in OWNER_FIRST:
                continue
            k = ah
            if ah == rec and rec not in phone:
                it["rec_mob"] = True
                who_, why = phone_who(it["t"])
                if who_:
                    k = who_
                else:
                    rec_why[id(it)] = why
            eff[id(it)] = k
            cards.setdefault(k, None)
    for key in agents:                                 # a known call handler on duty gets a card with no call of her own
        if key in OWNER_FIRST or (key == rec and rec not in phone):
            continue
        ent = staff.get(key)
        if ent and key not in cards and any(duty_window(ent, d, punches.get(key, {}).get(d)) for d in days):
            cards[key] = None
    for key in phone:                                  # S762: a phone staff member with a miss before her punch-in has a card
        if key not in cards and key not in OWNER_FIRST and any(it["kind"] == "in_miss" and pre_punch(key, it["t"]) for p, it in calls):
            cards[key] = None
    accepted = {(x.get("ref"), x.get("staff")) for x in rdisp if x.get("answer") == "accept"}
    # S762 (the owner, 09:27 IST 09-Nov): a call missed while BOTH (two or more) phone staff answer for it is shown ONCE on
    # his console, on a shared 'Both on duty' line (split=True, his page); each of them still sees it in her own card
    # (split=False, the staff's Mere calls).
    # A miss that a late phone staff member (before her punch-in) and a covering colleague both answer for is shared the
    # same way -- each sees it, his page counts it once.
    shared = {}
    if punch_ok and phone_known:
        cover = {}
        for key in cards:
            if key in phone or key == rec or len(agents.get(key, ())) > 1 or not staff.get(key):
                continue
            cover[key] = {d: w for d in days for w in [duty_window(staff[key], d, punches.get(key, {}).get(d))] if w}
        for p, it in calls:
            if it["kind"] == "in_miss" and it["t"] is not None:
                ks = [k for k in phone if phone_has(k, it["t"])]
                if not phone_on(it["t"]):
                    dd = it["t"].strftime("%Y-%m-%d")
                    ks += [k for k, w in cover.items() if w.get(dd) and w[dd][0] <= it["t"] <= w[dd][1]]
                if len(ks) > 1 and not any((it["ref"], k) in accepted for k in ks):
                    shared[it["ref"]] = ks        # R2 SF3: once a dispute is accepted, it follows the other person's card
    since7 = (now - _dt.timedelta(days=7)).strftime("%Y-%m-%d")
    out = []
    for key in sorted(cards):
        is_rec = (key == rec and rec not in phone)
        ambiguous = len(agents.get(key, ())) > 1
        ent = None if (ambiguous or is_rec) else staff.get(key)
        wins = {}
        if ent:
            for day in days:
                w = duty_window(ent, day, punches.get(key, {}).get(day))
                if w:
                    wins[day] = w

        is_phone = key in phone

        def on_duty(t):
            if t is None:
                return False
            w = wins.get(t.strftime("%Y-%m-%d"))
            if not (w and w[0] <= t <= w[1]):
                return False
            return is_phone or (phone_known and not phone_on(t))   # anyone else answers only while covering

        def reviewed(it):
            return ((rst.get((it["ref"], key)) or {}).get("state") or "") in REVIEWED

        def miss_here(it):
            """S762: this miss is on this card -- on duty (or, for phone staff, before her punch-in), and on the owner's
            page not one of the misses shared by both phone staff."""
            if not (on_duty(it["t"]) or (is_phone and ent and pre_punch(key, it["t"]))):
                return False
            return not (split and it["ref"] in shared)
        c = {"key": key, "name": "", "answered": 0, "rung": 0, "missed": 0, "made": 0, "cb_in_h": 0,
             "wa_in": 0, "wa_ans": 0, "cb_later": 0, "phone": is_phone, "not_logged": [], "not_back": [], "mismatch": [], "agreed": 0, "wa": [],
             "matched": bool(ent), "duty_h": "", "punch_h": "", "duty_ok": duty_ok,
             "missed_known": is_rec or (bool(ent) and punch_ok and (is_phone or phone_known)),
             "rec": is_rec, "items": [], "missed_items": [], "reviewed": [], "wa_open": [], "credited": 0,
             "rv": {}, "rv_ok": rv_ok, "disputes": [], "disputes_all": [],
             "pre_punch": set(), "shared": set(), "both": False}
        for p, it in calls:
            gone = (it["ref"], key) in accepted
            mine = eff.get(id(it)) == key
            if mine:
                c["name"] = c["name"] or (it.get("agent") or "").strip()
                c["items"].append((p, it))
                if it.get("rec_mob") and not is_rec:
                    c["credited"] += 1
                if it["direction"] == "Out":
                    c["made"] += 1
                if it["answered"]:
                    if it["direction"] == "In":
                        c["answered"] += 1
                    if it["jk"] and not it["claimed"]:
                        if gone:
                            pass
                        elif reviewed(it):
                            c["reviewed"].append((p, it, "not_logged"))
                        else:
                            c["not_logged"].append((p, it))
                    elif it["mismatch"] and not it["final"]:
                        if gone:
                            pass
                        elif reviewed(it):
                            c["reviewed"].append((p, it, "mismatch"))
                        else:
                            c["mismatch"].append((p, it))
                    elif it["claimed"] and (it["verdict"] == "Match" or (it["verdict"] == "Mismatch" and not it["mismatch"])):
                        c["agreed"] += 1                   # S762: same words / AGREE_PAIRS agree
            if it["kind"] == "in_miss" and not gone and miss_here(it):
                c["missed"] += 1
                c["missed_items"].append((p, it))
                if is_phone and pre_punch(key, it["t"]):
                    c["pre_punch"].add(it["ref"])
                if it["ref"] in shared:
                    c["shared"].add(it["ref"])
                later = [y for y in p["calls"] if y.get("ch") != "wa" and y["answered"] and y["t"] and it["t"] and y["t"] > it["t"]]
                if later:
                    if (later[0]["t"] - it["t"]).total_seconds() <= CALLBACK_MIN * 60:
                        c["cb_in_h"] += 1
                    else:
                        c["cb_later"] += 1
                elif reviewed(it):
                    c["reviewed"].append((p, it, "not_back"))
                else:
                    c["not_back"].append((p, it))
        c["rung"] = c["answered"] + c["missed"]
        for p in people:
            for w in p["calls"]:
                if w["kind"] == "wa_in" and on_duty(w["t"]) and (w["ref"], key) not in accepted:
                    c["wa_in"] += 1
                    a = wa_answer(w, p["calls"])
                    if a is not None:
                        c["wa_ans"] += 1
                    elif reviewed(w):
                        c["reviewed"].append((p, w, "wa"))
                    else:
                        c["wa_open"].append((p, w))
                    c["wa"].append((p, w, a))
        c["name"] = (ent["name"] if ent else "") or c["name"] or key.title()
        today_iso = now.strftime("%Y-%m-%d")
        if is_rec:
            c["name"] = "Reception mobile"
            whys = sorted({rec_why.get(id(it), "") for p, it in c["items"]} - {""})
            c["duty_h"] = ("calls on the reception mobile not credited to a person (" + "; ".join(whys or ["—"]) +
                           ") · a call there is credited to the phone staff member on duty when exactly one is · missed calls are "
                           "counted to the phone staff on duty, as always")
        elif ent and not punch_ok:
            c["duty_h"] = "the punch log could not be read — missed calls on duty are not counted"
        elif ent:
            ws = [wins[d] for d in days if d in wins]
            if len(days) == 1:
                a, b = ent["sun"] if d0.weekday() == 6 else ent["wd"]
                pu = punches.get(key, {}).get(days[0])
                past = days[0] != today_iso
                c["duty_h"] = ("on duty %s–%s" % (a.strftime("%H:%M"), b.strftime("%H:%M"))) if (a and b) else ("off that day" if past else "off today")
                c["punch_h"] = ("punched %s" % pu.strftime("%H:%M")) if pu else (("did not punch" if past else "not punched yet") if (a and b) else "")
            else:
                c["duty_h"] = "on duty %d of %d days" % (len(ws), len(days))
            if not is_phone:
                c["duty_h"] += (" · missed calls and WhatsApps counted only while covering (no phone staff on duty)" if phone_known
                                else " · the phone staff's duty is not known, so nothing missed is counted to this card")
        elif ambiguous:
            c["duty_h"] = "two agents share this first name — duty not matched, missed calls not counted"
        elif not master_ok:
            c["duty_h"] = "the duty list could not be read — missed calls on duty are not counted"
        else:
            c["duty_h"] = "duty not known (name not matched in the staff list) — missed calls not counted"
        if c["credited"]:
            c["duty_h"] += " · %d call%s on the reception mobile counted here (the only phone staff on duty)" % (
                c["credited"], "s" if c["credited"] != 1 else "")
        if c["pre_punch"]:
            c["duty_h"] += " · %d missed before punch-in counted here" % len(c["pre_punch"])
        if split and any(key in v for v in shared.values()):
            n_sh = sum(1 for r_, v in shared.items() if key in v and not any((r_, k_) in accepted for k_ in v))
            c["duty_h"] += " · %d missed while two were on duty are on the 'Both on duty' line" % n_sh
        c["disputes"] = [x for x in rdisp if x.get("staff") == key and not x.get("answer")]
        c["disputes_all"] = [x for x in rdisp if x.get("staff") == key and
                             (not x.get("answer") or str(x.get("answer_at") or "")[:10] >= since7)]
        refs = ({it["ref"] for p, it in c["items"]} | {it["ref"] for p, it in c["missed_items"]} | {w["ref"] for p, w, a in c["wa"]}
                | {it["ref"] for p, it, k in c["reviewed"]})
        c["rv"] = {r: rst[(r, key)] for r in refs if (r, key) in rst}
        c["missed_people"] = len({(p.get("phone") or it["ref"]) for p, it in c["missed_items"]})       # S748
        c["not_back_people"] = len({(p.get("phone") or it["ref"]) for p, it in c["not_back"]})
        c["net_missed"] = len({(p.get("phone") or it["ref"]) for p, it in c["not_back"]} |
                              {(p.get("phone") or it["ref"]) for p, it, k in c["reviewed"] if k == "not_back"})
        nl, nb, mm = len(c["not_logged"]), len(c["not_back"]), len(c["mismatch"])
        c["check"] = nl + nb + mm
        c["tone"] = "rose" if (nl or nb or c["net_missed"]) else ("amber" if (mm or c["disputes"] or not c["missed_known"]) else "green")
        out.append(c)
    if split and shared:
        out.append(_both_card(calls, shared, rst, accepted, rv_ok))

    def _t(x):
        return (x[1]["t"] or _dt.datetime.min)
    for c in out:                                       # S762: every list newest first, as the staff's own card
        for f in ("items", "missed_items", "not_logged", "not_back", "mismatch", "wa_open", "reviewed", "wa", "reached"):
            if f in c:
                c[f].sort(key=_t, reverse=True)
    order = {"rose": 0, "amber": 1, "green": 2}
    out.sort(key=lambda x: (x["rec"], x.get("both", False), order[x["tone"]], -(x["made"] + x["rung"])))
    return out


def _both_card(calls, shared, rst, accepted, rv_ok):
    """S762: the owner's 'Both on duty' line -- the calls missed while two phone staff answered for them, counted once.
    A call is off it when a dispute about it was accepted for every one of them; 'reviewed' when either reviewed it.
    Each row carries Call back, the recording, and Mark reviewed / Undo -- written under the first person who answered for
    it (never under 'both'); a review by either of them counts here."""
    names = sorted({k for v in shared.values() for k in v})
    c = {"key": "both", "name": "Both on duty", "both": True, "rec": False, "phone": True, "matched": True,
         "answered": 0, "rung": 0, "missed": 0, "made": 0, "cb_in_h": 0, "cb_later": 0, "wa_in": 0, "wa_ans": 0,
         "not_logged": [], "not_back": [], "mismatch": [], "agreed": 0, "wa": [], "wa_open": [], "items": [],
         "missed_items": [], "reviewed": [], "credited": 0, "rv": {}, "rv_ok": rv_ok, "disputes": [], "disputes_all": [],
         "missed_known": True, "duty_ok": True, "pre_punch": set(), "shared": set(shared),
         "reached": [], "staff_of": {},
         "duty_h": "missed while two of %s were on duty (or one before her punch-in) — counted once here; each sees them in her own card"
                   % " and ".join(n.title() for n in names), "punch_h": ""}
    for p, it in calls:
        ks = shared.get(it["ref"])
        if not ks or any((it["ref"], k) in accepted for k in ks):   # cold review SF2: one accepted dispute takes it off
            continue
        c["staff_of"][it["ref"]] = ks[0]
        for k in ks:                                   # R2 SF1/SF2: the reviewer's own entry wins, and Undo goes to her
            st_ = rst.get((it["ref"], k))
            if st_ and (it["ref"] not in c["rv"] or (st_.get("state") or "") in REVIEWED):
                c["rv"][it["ref"]] = st_
                if (st_.get("state") or "") in REVIEWED:
                    c["staff_of"][it["ref"]] = k
        c["missed"] += 1
        c["missed_items"].append((p, it))
        later = [y for y in p["calls"] if y.get("ch") != "wa" and y["answered"] and y["t"] and it["t"] and y["t"] > it["t"]]
        if later:
            c["reached"].append((p, it))
            if (later[0]["t"] - it["t"]).total_seconds() <= CALLBACK_MIN * 60:
                c["cb_in_h"] += 1
            else:
                c["cb_later"] += 1
        elif any(((rst.get((it["ref"], k)) or {}).get("state") or "") in REVIEWED for k in ks):
            c["reviewed"].append((p, it, "not_back"))
        else:
            c["not_back"].append((p, it))
    c["rung"] = c["missed"]
    c["missed_people"] = len({(p.get("phone") or it["ref"]) for p, it in c["missed_items"]})
    c["not_back_people"] = len({(p.get("phone") or it["ref"]) for p, it in c["not_back"]})
    c["net_missed"] = len({(p.get("phone") or it["ref"]) for p, it in c["not_back"]} |
                          {(p.get("phone") or it["ref"]) for p, it, k in c["reviewed"]})
    c["check"] = len(c["not_back"])
    c["tone"] = "rose" if c["net_missed"] else "green"
    return c


def _row_json(p, it, c, figs):
    """One call (or WhatsApp) of a card, for the staff's own page: what happened, the log, and whether its recording can be
    played. NO transcript text goes to staff -- the owner's rule (09:23 IST 07-Nov): staff get the recordings only. S747."""
    st_ = c["rv"].get(it["ref"]) or {}
    wa = it.get("ch") == "wa"
    return {"ref": it["ref"], "day": it.get("day") or "", "t": it.get("t_h") or "", "kind": it["kind"],
            "name": p.get("name") or "", "cid": p.get("cid") or "", "phone": p.get("phone") or "",
            "claimed": "" if wa else (it.get("claimed_h") or ""), "ai": "" if wa else (it.get("ai_h") or ""),
            "jk": "" if wa else (it.get("jk") or ""), "dur": "" if wa else (it.get("dur_h") or ""),
            "has_rec": (not wa) and bool(it.get("has_rec")) and bool(it.get("jk")),
            "body": (it.get("body") or "")[:200] if wa else "", "figs": sorted(figs),
            "asked": st_.get("asked") or "", "notes": [{"at": a, "text": n} for a, n in st_.get("notes", [])],
            "rec": bool(it.get("rec_mob")), "pre_punch": it["ref"] in c.get("pre_punch", ()), "sort": (it["t"] or _dt.datetime.min).strftime("%Y-%m-%d %H:%M:%S")}


def card_json(c):
    """A card as the person's own page reads it: the same figures as the owner's, every call once (newest first) with the
    figures it is behind, the owner's asks and notes, and their disputes of the last 7 days. S747."""
    rows = {}

    def add(p, it, fig=None):
        r = rows.setdefault(it["ref"], [p, it, set()])
        if fig:
            r[2].add(fig)
    for p, it in c["items"]:
        add(p, it)
    for p, it in c["missed_items"]:
        add(p, it, "missed")
    for p, it in c["not_logged"]:
        add(p, it, "not_logged")
    for p, it in c["mismatch"]:
        add(p, it, "mismatch")
    for p, w, a in c["wa"]:
        add(p, w, None if a is not None else "wa")
    for p, it, k in c["reviewed"]:
        add(p, it)
    calls = sorted((_row_json(p, it, c, f) for p, it, f in rows.values()), key=lambda r: r["sort"], reverse=True)
    keep = ("id", "ref", "fig", "text", "call_h", "at", "answer", "answer_note", "answer_at")
    return {"key": c["key"], "name": c["name"], "tone": c["tone"], "rec": c["rec"],
            "figs": {"answered": c["answered"], "rung": c["rung"], "missed": c["missed"], "missed_known": c["missed_known"],
                     "made": c["made"], "cb_in_h": c["cb_in_h"], "cb_later": c["cb_later"], "wa_in": c["wa_in"],
                     "wa_ans": c["wa_ans"], "not_logged": len(c["not_logged"]), "mismatch": len(c["mismatch"]),
                     "agreed": c["agreed"], "missed_people": c.get("missed_people", 0), "net_missed": c.get("net_missed", 0),
                     "reached_later": max(0, c.get("missed_people", 0) - c.get("net_missed", 0)),
                     "pre_punch": len(c.get("pre_punch", ()))},
            "asks": [r for r in calls if r["asked"] and "not_logged" in r["figs"]],
            "notes": [r for r in calls if r["notes"]],
            "disputes": [{k: x.get(k) for k in keep} for x in c["disputes_all"]],
            "calls": calls}


_CARD_CACHE = {}
CARD_CACHE_S = 60


def card_for(conn, key, span="yesterday", now=None, cached=False):
    """(card or None, handler, mode, cards_made) for one person: the window today | yesterday | 7, read exactly as the
    owner's page reads it. handler: the person handles calls (an agent of the last 30 days, or phone staff). A first name
    two MyOperator agents share gives NO card (their calls would be one card -- the cold review's should-fix 1). cached:
    the checks behind a transcript tap or a dispute reuse a card made in the last minute (should-fix 3). S747."""
    if cached:
        hit = _CARD_CACHE.get((key, span))
        if hit and time.time() - hit[0] < CARD_CACHE_S:
            return hit[1]
    res = _card_for(conn, key, span, now)
    if len(_CARD_CACHE) > 50:
        _CARD_CACHE.clear()
    _CARD_CACHE[(key, span)] = (time.time(), res)
    return res


def _card_for(conn, key, span, now):
    now = now_ist(now)
    d_from, d_to, mode = span_bounds(span if span in ("today", "yesterday", "7") else "yesterday", "", now)
    wa, _ok = wa_items(_cfg_path("PORTAL_INBOX_DB", INBOX_DB_DEFAULT), d_from, d_to)
    people, _items, _nn = build_people(conn, d_from, d_to, now, wa=wa)
    cards = _safe_cards(conn, people, d_from, d_to, now, _cfg_path("SR_STAFF_MASTER", STAFF_MASTER_DEFAULT),
                        _cfg_path("SR_PUNCH_CSV", PUNCH_CSV_DEFAULT))
    phone = [k.split()[0].lower() for k in str(_cfg_path("PORTAL_PHONE_STAFF", PHONE_STAFF_DEFAULT)).split(",") if k.strip()]
    agents = _agent_firsts(conn, now)
    rec = (str(_cfg_path("PORTAL_RECEPTION_AGENT", RECEPTION_DEFAULT) or "").strip().lower() or RECEPTION_DEFAULT).split()[0]
    handler = bool(key) and key != rec and (key in phone or key in agents)
    if cards is None:
        return None, handler, mode, False
    if len(agents.get(key, ())) > 1:
        return None, handler, mode, True
    return next((x for x in cards if x["key"] == key and not x["rec"]), None), handler, mode, True

def _agent_firsts(conn, now=None):
    """first name (lower) -> the set of full MyOperator agent names (call_agent) seen on calls of the last 30 days,
    compared in small letters so one person's two spellings are one; read-only; {} when unreadable."""
    out = {}
    since = (now_ist(now) - _dt.timedelta(days=30)).strftime("%Y-%m-%d")
    try:
        for (a,) in conn.execute("SELECT DISTINCT ca.agent FROM call_agent ca JOIN calls c ON c.join_key=ca.join_key "
                                 "WHERE TRIM(COALESCE(ca.agent,''))<>'' AND substr(c.ended_at_ist,1,10)>=?", (since,)):
            k = (first_name(a) or "").lower()
            if k and k != "you":
                out.setdefault(k, set()).add(" ".join(a.lower().split()))
    except Exception:
        return {}
    return out


def _safe_cards(conn, people, d_from, d_to, now, master_path, punch_path, split=False):
    """The staff cards, never at the cost of the page: an error here gives no cards and the section says so. S747: the
    review store and the reception agent from the settings."""
    try:
        return staff_cards(people, d_from, d_to, now, master_path=master_path, punch_path=punch_path,
                           agents=_agent_firsts(conn, now), phone_staff=_cfg_path("PORTAL_PHONE_STAFF", PHONE_STAFF_DEFAULT),
                           rv=rv_read(_cfg_path("PORTAL_CALL_REVIEW_DB", REVIEW_DB_DEFAULT)),
                           reception=_cfg_path("PORTAL_RECEPTION_AGENT", RECEPTION_DEFAULT), split=split)
    except Exception:
        return None

def _calls_min(conn, d_from, d_to):
    """(phone, direction, answered, ai_outcome, claimed, day) for every call of the window, the phone recovered
    from the join key or the OBD reference when phone10 is blank."""
    out = []
    try:
        for r in conn.execute(
                "SELECT c.phone10, c.join_key, c.client_ref_id, c.direction, c.answered, substr(c.ended_at_ist,1,10) AS d, "
                "COALESCE(v.ai_outcome,'') AS ai, COALESCE(v.claimed_outcome,'') AS cl "
                "FROM calls c LEFT JOIN (SELECT join_key, MAX(id) AS _vid, ai_outcome, claimed_outcome FROM verdicts "
                "WHERE join_key<>'' GROUP BY join_key) v ON v.join_key=c.join_key AND c.join_key<>'' "
                "WHERE substr(c.ended_at_ist,1,10)>=? AND substr(c.ended_at_ist,1,10)<=?", (d_from, d_to)):
            ph = phone_of({"phone10": r[0], "join_key": r[1], "client_ref_id": r[2]})
            out.append((ph, r[3], r[4], r[6], r[7], r[5]))
    except Exception:
        pass
    return out


def week_unknown(conn, now, days=7):
    """This week's unknown callers: numbers not in the patient list that rang; reached (a connected call either way);
    booked (the AI heard a booking or staff filed one). 'Came to the clinic' and 'old patient, new mobile' come with
    S699 (the Call-ke-baad list's Docterz match and the link store)."""
    d_to = now.strftime("%Y-%m-%d")
    d_from = (now - _dt.timedelta(days=days - 1)).strftime("%Y-%m-%d")
    out = {"from": d_from, "to": d_to, "rang": 0, "reached": 0, "booked": 0, "never": 0}
    try:
        pats = {r[0] for r in conn.execute("SELECT DISTINCT phone10 FROM patients WHERE phone10<>''")}
        try:
            spam = set(_H["spam_phones"]()) if _H.get("spam_phones") else set()
        except Exception:
            spam = set()
        seen = {}
        for ph, d, a, ai, cl, _day in _calls_min(conn, d_from, d_to):
            if not ph or ph in pats or ph in spam:
                continue
            s = seen.setdefault(ph, {"rang": False, "reached": False, "booked": False})
            if d == "In":
                s["rang"] = True
            if a == 1:
                s["reached"] = True
            if "book" in (ai or "").lower() or (cl or "") == "appointment_booked":
                s["booked"] = True
        rang = [s for s in seen.values() if s["rang"]]
        out["rang"] = len(rang)
        out["reached"] = sum(1 for s in rang if s["reached"])
        out["booked"] = sum(1 for s in rang if s["booked"])
        out["never"] = sum(1 for s in rang if not s["reached"])
    except Exception:
        pass
    return out


def earlier_days(conn, now, days=7):
    """One line per earlier day: calls, callers, unknown (reached / never reached)."""
    out = []
    try:
        pats = {r[0] for r in conn.execute("SELECT DISTINCT phone10 FROM patients WHERE phone10<>''")}
    except Exception:
        pats = set()
    d_to = (now - _dt.timedelta(days=1)).strftime("%Y-%m-%d")
    d_from = (now - _dt.timedelta(days=days)).strftime("%Y-%m-%d")
    byday = {}
    for ph, dr, a, _ai, _cl, day in _calls_min(conn, d_from, d_to):
        byday.setdefault(day, []).append((ph, dr, a))
    for d in sorted(byday, reverse=True):
        rows = byday[d]
        callers = {}
        for ph, dr, a in rows:
            if not ph:
                continue
            s = callers.setdefault(ph, {"in": False, "ok": False})
            if dr == "In":
                s["in"] = True
            if a == 1:
                s["ok"] = True
        unk = {ph: s for ph, s in callers.items() if ph not in pats and s["in"]}
        never = sum(1 for s in unk.values() if not s["ok"])
        out.append({"day": d, "label": day_label(d, now.date()), "calls": len(rows), "callers": len(callers),
                    "unknown": len(unk), "never": never})
    return out


def read_meta(now):
    """Built-at, age, and whether the page may call itself stale (only inside the reading window)."""
    m = _H["console_meta"]() if _H.get("console_meta") else {"ok": False}
    built = parse_ts(m.get("built_at") or "")
    age = int((now - built).total_seconds() // 60) if built else None
    in_window = READ_FROM_H <= now.hour < READ_TO_H
    stale_min = STALE_MIN_DEFAULT
    try:
        stale_min = int(_CFG("PORTAL_CONSOLE_STALE_MIN", str(STALE_MIN_DEFAULT)) or STALE_MIN_DEFAULT) if _CFG else STALE_MIN_DEFAULT
    except Exception:
        pass
    stale = bool(m.get("ok")) and in_window and (age is None or age > stale_min)
    asof = built.strftime("%H:%M, %a %-d %b") if built else "—"          # S742: the long form, the day always
    return {"ok": bool(m.get("ok")), "built": built, "asof": asof, "age": age, "stale": stale, "in_window": in_window,
            "next": "07:00" if not in_window else ""}


def span_bounds(span, day, now):
    today = now.date()
    if day and _ISO_DAY.match(day):
        return day, day, "day"
    if span == "yesterday":
        d = (today - _dt.timedelta(days=1)).isoformat()
        return d, d, "yesterday"
    if span == "7":
        return (today - _dt.timedelta(days=6)).isoformat(), today.isoformat(), "7"
    if span == "30":
        return (today - _dt.timedelta(days=29)).isoformat(), today.isoformat(), "30"
    return today.isoformat(), today.isoformat(), "today"


def page_data(conn, span="today", day="", q="", now=None, inbox_path=None, fin_db=None, master_path=None, punch_path=None):
    """Everything the page shows, in one dict. Pure over the connections (console.db; the inbox and finance.db
    are opened read-only by their own readers)."""
    now = now_ist(now)
    d_from, d_to, mode = span_bounds(span, day, now)
    wa, wa_ok = wa_items(inbox_path, d_from, d_to)
    people, items, no_number = build_people(conn, d_from, d_to, now, q=q, wa=wa)
    everyone = people if not q else build_people(conn, d_from, d_to, now, q="", wa=wa)[0]       # S744: cards ignore the search
    counts = strip_counts(people, items)
    ny = needs_you(people, items, now) if mode in ("today", "day") else []
    chips = {"all": len(people), "awaiting": sum(1 for p in people if p["state"] == "rose"),
             "calls": sum(1 for p in people if p["n_calls"]), "wa": sum(1 for p in people if p["n_wa"]),
             "unknown": sum(1 for p in people if p["unknown"])}
    # a multi-day span: the people rows group by the day of their last contact
    groups = []
    if mode in ("7", "30"):
        byday = {}
        for p in people:
            byday.setdefault((p["last_t"] or now).strftime("%Y-%m-%d"), []).append(p)
        for d in sorted(byday, reverse=True):
            groups.append((d, day_label(d, now.date()), byday[d]))
    else:
        groups.append((d_to, day_label(d_to, now.date()), people))
    return {"now": now, "from": d_from, "to": d_to, "mode": mode, "q": q, "people": people, "groups": groups,
            "counts": counts, "needs": ny, "chips": chips, "no_number": no_number, "wa_ok": wa_ok,
            "staff": _safe_cards(conn, everyone, d_from, d_to, now, master_path, punch_path, split=True),
            "fu": followup_list(conn, now, fin_db=fin_db, inbox_path=inbox_path), "ckb": ckb_week(now, fin_db=fin_db),
            "week": week_unknown(conn, now), "earlier": earlier_days(conn, now),
            "title_day": day_label(d_to, now.date()) if mode in ("today", "day", "yesterday") else
            ("Last 7 days" if mode == "7" else "Last 30 days")}


# ---------------------------------------------------------------------------------------------- the click-to-call
_LAST_CALL = {}


def ivr_call(phone10, login, env_path=None, call_url=None, now=None, post=None):
    """The owner's click-to-call: his own MyOperator agent (ring_agents.json, by login), the number from the
    row (10 digits), one call per number per minute. Returns (ok, message, http status). Nothing logged."""
    ph = re.sub(r"\D", "", phone10 or "")[-10:]
    if len(ph) != 10:
        return False, "No 10-digit number on this row.", 400
    try:
        import ring_outcome as _ro
        agent = _ro.ivr_agent(login)
    except Exception:
        agent = ""
    if not agent:
        return False, "Your login is not tied to a MyOperator agent (ring_agents.json).", 400
    t = time.time() if now is None else now
    last = _LAST_CALL.get(ph)
    if last is not None and t - last < CALL_GAP:
        return False, "This number was just called — try again in a minute.", 429
    env = {}
    try:
        with open(env_path or WA_ENV_DEFAULT, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    key = env.get("CALL_API_SECRET", "")
    if not key:
        return False, "The IVR call key is not set on the server.", 502
    body = {"agent": agent, "patient_number": ph, "reference_id": "CC%d" % int(t)}
    poster = post or _post_json
    try:
        st, j = poster(call_url or CALL_URL_DEFAULT, body, key, CALL_TIMEOUT)
    except Exception:
        st, j = 0, {}
    if st == 200 and j.get("accepted") is True:
        _LAST_CALL[ph] = t                                  # the minute's gap starts only on an accepted call
        return True, "Your phone is ringing — pick up, and the patient is joined.", 200
    if st == 0:
        return False, "No answer from the IVR server.", 502
    reason = re.sub(r"\d{5,}", lambda m: "…" + m.group(0)[-4:], " ".join(str(j.get("reason") or ("http %s" % st)).split()))[:120]
    return False, "The call was refused: " + reason, 502


def _post_json(url, body, key, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Call-Key", key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code, raw = resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read().decode("utf-8", "replace")
    try:
        j = json.loads(raw)
    except Exception:
        j = {}
    return code, (j if isinstance(j, dict) else {})


# ---------------------------------------------------------------------------------------------- the page
ICONS = {
    "in_ok":    ('<svg class="ic" role="img" aria-label="incoming call, answered" viewBox="0 0 24 24" fill="none" stroke="#1f5fa8" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="5" x2="5.5" y2="18.5"/><polyline points="5 10 5 19 14 19"/></svg>'),
    "in_miss":  ('<svg class="ic" role="img" aria-label="missed call" viewBox="0 0 24 24" fill="none" stroke="#b3261e" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 3.5"><line x1="19" y1="5" x2="5.5" y2="18.5"/><polyline points="5 10 5 19 14 19"/></svg>'),
    "out_ok":   ('<svg class="ic" role="img" aria-label="outgoing call, answered" viewBox="0 0 24 24" fill="none" stroke="#1f5fa8" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="19" x2="18.5" y2="5.5"/><polyline points="10 5 19 5 19 14"/></svg>'),
    "out_miss": ('<svg class="ic" role="img" aria-label="outgoing call, not answered" viewBox="0 0 24 24" fill="none" stroke="#b3261e" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 3.5"><line x1="5" y1="19" x2="18.5" y2="5.5"/><polyline points="10 5 19 5 19 14"/></svg>'),
    "wa_in":    ('<svg class="ic" role="img" aria-label="WhatsApp from the patient" viewBox="0 0 24 24" fill="none" stroke="#1e7a45" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11.5a8 8 0 0 1-11.6 7.1L4 20l1.4-4.2A8 8 0 1 1 20 11.5z"/><line x1="8.5" y1="10" x2="15.5" y2="10"/><line x1="8.5" y1="13.5" x2="13" y2="13.5"/></svg>'),
    "wa_out":   ('<svg class="ic" role="img" aria-label="WhatsApp reply by the clinic" viewBox="0 0 24 24" fill="#1e7a45" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11.5a8 8 0 0 1-11.6 7.1L4 20l1.4-4.2A8 8 0 1 1 20 11.5z"/></svg>'),
    "wa_fail":  ('<svg class="ic" role="img" aria-label="WhatsApp reply failed" viewBox="0 0 24 24" fill="none" stroke="#b3261e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11.5a8 8 0 0 1-11.6 7.1L4 20l1.4-4.2A8 8 0 1 1 20 11.5z"/><line x1="9.5" y1="9" x2="14.5" y2="14"/><line x1="14.5" y1="9" x2="9.5" y2="14"/></svg>'),
    "calls":    ('<svg class="ic" role="img" aria-label="calls" viewBox="0 0 24 24" fill="none" stroke="#6b716d" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.8a2 2 0 0 1-.4 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.5 2.8.7a2 2 0 0 1 1.7 2z"/></svg>'),
    "wa_tpl":   ('<svg class="ic" role="img" aria-label="WhatsApp template, not a reply" viewBox="0 0 24 24" fill="none" stroke="#6b716d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="3 2.5"><path d="M20 11.5a8 8 0 0 1-11.6 7.1L4 20l1.4-4.2A8 8 0 1 1 20 11.5z"/></svg>'),
}

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Calls — Command console</title>
<!-- S742_CALLS_R3 (the parent, S397, 07-Nov-2026), on S698_CALLS_R1 / S703: the Call Console to mock-up R3.
     Reads console.db only. The old page is /portal/console/old. -->
<style>
:root{
  --bg:#f3f2ed; --paper:#ffffff; --chip:#ecebe4; --fg:#1d211f; --muted:#3f4541; --line:#dbd8cf; --line2:#ecebe4;
  --accent:#1f5f4a; --accent-ink:#ffffff; --good:#2f7a4e; --warn:#8c6a00; --warn-ink:#7a5c00; --warn-soft:#fdf1c7;
  --bad:#b3261e; --bad-soft:#fbe1de; --grey:#9aa19b; --blue:#1f5fa8;
  --body:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"IBM Plex Sans",sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"IBM Plex Mono",monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);font-size:13.5px;line-height:1.4;-webkit-text-size-adjust:100%}
a{color:var(--accent)}
.wrap{max-width:1320px;margin:0 auto;padding:12px 16px 40px;display:flex;flex-direction:column;gap:10px}
.head{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center}
h1{font-weight:700;font-size:22px;margin:0}
h1 a{color:var(--muted);text-decoration:none;font-weight:500;font-size:13px;margin-left:8px;font-family:var(--mono)}
.tabs{display:flex;gap:6px;flex-wrap:wrap}
.tabs a,.chips button{font-weight:600;font-size:13px;padding:5px 11px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:var(--fg);text-decoration:none;cursor:pointer;font-family:var(--body)}
.tabs a.on,.chips button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.chips button{min-height:32px}
form.q{display:flex;align-items:center;gap:6px;font-size:13.5px;color:var(--muted)}
form.q input{font:inherit;font-size:13px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--paper);color:var(--fg);min-width:260px}
.mbtn{font-family:var(--mono);font-size:12px;padding:3px 8px;border-radius:6px;border:1px solid var(--line);background:var(--paper);color:var(--muted);cursor:pointer;text-decoration:none}
.mbtn.asof{margin-left:auto}.mbtn.w{color:var(--warn);border-color:var(--warn)}
.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.ic{width:22px;height:22px;flex:none;display:block}
.chain .ic,.cnt .ic{width:17px;height:17px}.tl .ic{width:20px;height:20px}
.strip{display:grid;grid-template-columns:1fr;gap:6px 18px;align-items:center;padding:9px 14px}
.strip .big{font-weight:600;font-size:17px;line-height:1.25}
.strip .big a{text-decoration:none;color:inherit;border-bottom:1px dotted var(--muted)}
.strip .big a.b{color:var(--bad);border-color:var(--bad)}.strip .big a.w{color:var(--warn);border-color:var(--warn)}
.cnt{display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.cnt span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
.cnt b{font-family:var(--mono);font-size:14px}
.cnt .arr{color:var(--muted);font-size:12px}
.bar{grid-column:1/-1;height:6px;border-radius:3px;background:var(--chip);overflow:hidden;display:flex}
.bar i{display:block;height:100%}.bar .g{background:var(--good)}.bar .w{background:var(--warn)}.bar .b{background:var(--bad)}
h2{font-weight:600;font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 5px;display:flex;justify-content:space-between;align-items:center;gap:8px}
h2 .l{display:inline-flex;align-items:center;gap:6px;flex-wrap:wrap}
h2 .pill{font-family:var(--mono);font-size:11.5px;letter-spacing:.03em;text-transform:none;padding:1px 7px;border-radius:999px;background:var(--chip);color:var(--fg);white-space:nowrap}
h2 .pill.w{background:var(--warn-soft);color:var(--warn)}
.ny{display:flex;gap:10px;align-items:center;padding:9px 12px;margin:4px 6px;border-radius:8px}
.ny.rose{background:var(--bad-soft);border-left:3px solid var(--bad)}.ny.amber{background:var(--warn-soft);border-left:3px solid var(--warn)}
.ny .t{flex:1;min-width:0;font-size:14px}.ny .t .sub{display:block;color:var(--muted);font-size:13.5px}
.ny .n{font-family:var(--mono);font-size:15px}.ny .unk{font-family:var(--mono);font-size:12px;padding:2px 8px;border-radius:999px;background:var(--warn-soft);color:var(--warn-ink);white-space:nowrap}.ny.rose .n{color:var(--bad)}.ny.amber .n{color:var(--warn-ink)}
.btn{font-weight:600;font-size:12.5px;text-decoration:none;white-space:nowrap;border-radius:6px;padding:5px 10px;color:var(--accent-ink);background:var(--accent);border:1px solid var(--accent);cursor:pointer;font-family:var(--body)}
.btn.soft{color:var(--accent);background:var(--paper)}
.chain{display:inline-flex;flex-wrap:wrap;align-items:center;gap:4px 6px}
.chain .c{display:inline-flex;align-items:center;gap:3px}
.chain .c span{font-family:var(--mono);font-size:12.5px}
.chain .arr{color:var(--muted);font-size:12px}
.chain .tail{font-size:13px}
.chips{display:flex;flex-wrap:wrap;gap:6px;padding:8px 12px;border-bottom:1px solid var(--line)}
details.p{border-bottom:1px solid var(--line)}
details.p:last-child{border-bottom:0}
details.p>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:14px 1fr auto;gap:8px;align-items:center;padding:5px 12px 5px 10px;min-height:40px}
details.p>summary::-webkit-details-marker{display:none}
details.p.rose>summary{background:var(--bad-soft)}details.p.amber>summary{background:var(--warn-soft)}
details.p>summary .car{font-size:11px;color:var(--muted);transition:transform .12s}
details.p[open]>summary .car{transform:rotate(90deg)}
.who{min-width:0}.who b{font-weight:600;font-size:14.5px}
.who .unk{font-family:var(--mono);font-size:12px;padding:2px 8px;border-radius:999px;background:var(--warn-soft);color:var(--warn-ink);white-space:nowrap}
.who .spam{font-family:var(--mono);font-size:12px;padding:2px 8px;border-radius:999px;background:var(--chip);color:var(--muted)}
.who .sub{display:block;color:var(--muted);font-size:13.5px}
.right{display:flex;flex-direction:column;align-items:flex-end;gap:4px}
.right .st{font-size:12.5px;white-space:nowrap;font-weight:700}
.st.green{color:var(--good)}.st.amber{color:var(--warn)}.st.rose{color:var(--bad)}.st.grey{color:var(--muted)}
.tl{display:grid;grid-template-columns:46px 20px 1fr auto;gap:8px;align-items:start;padding:6px 12px 6px 14px;border-top:1px solid var(--line2)}
.tl.rose{background:var(--bad-soft)}
.tl .tm{font-family:var(--mono);font-size:12.5px;color:var(--muted);padding-top:1px}
.tl .tx{min-width:0;font-size:14px}.tl .tx .sub{display:block;color:var(--muted);font-size:13px}
.tl .tx .snip{display:block;margin-top:3px;font-size:13px;color:var(--fg);background:var(--bg);border-radius:6px;padding:4px 8px}
.tl .tx .full{white-space:pre-wrap;display:block;margin-top:4px;font-size:13px;background:var(--bg);border-radius:6px;padding:6px 8px;max-height:60vh;overflow:auto}
.play{font-family:var(--mono);font-size:12.5px;color:var(--accent);border:1px solid var(--accent);border-radius:999px;padding:2px 8px;white-space:nowrap;background:var(--paper);cursor:pointer}
.play.on{background:var(--accent);color:var(--accent-ink)}
.rev{display:inline-flex;gap:6px;align-items:center;margin-top:4px}
.rev select,.rev input{font:inherit;font-size:12.5px;padding:3px 6px;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--fg)}
.row{display:grid;grid-template-columns:14px 1fr auto;gap:8px;align-items:start;padding:6px 12px 6px 10px;border-top:1px solid var(--line2)}
.dot{width:9px;height:9px;border-radius:50%;margin-top:6px;background:var(--grey);justify-self:center}
.dot.g{background:var(--good)}.dot.w{background:var(--warn)}.dot.b{background:var(--bad)}
.row .t{min-width:0}.row .t .sub{display:block;margin-top:3px;color:var(--muted)}
details.d>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:14px 1fr auto;gap:8px;align-items:center;padding:7px 12px 7px 10px;border-bottom:1px solid var(--line);min-height:38px}
details.d>summary::-webkit-details-marker{display:none}
details.d>summary .car{font-size:11px;color:var(--muted)}details.d[open]>summary .car{transform:rotate(90deg)}
details.d>summary b.n{font-weight:600;font-size:14px}details.d>summary .sub{display:block;color:var(--muted);font-size:13.5px}
details.d>summary .r{font-family:var(--mono);font-size:13px}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:5px 8px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-family:var(--mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500}
td:first-child,th:first-child{text-align:left;padding-left:12px}td{font-family:var(--mono)}td:first-child{font-family:var(--body)}
tr.tot td{font-weight:600;border-top:1px solid var(--muted);background:var(--chip)}
.note{padding:7px 12px;color:var(--muted);font-size:13.5px;border-top:1px solid var(--line)}
.foot{color:var(--muted);font-size:12.5px;line-height:1.5}
.empty{padding:14px 12px;color:var(--muted)}
.banner{padding:9px 14px;border-radius:10px;background:var(--warn-soft);color:var(--warn-ink);font-size:13.5px}
.banner.bad{background:var(--bad-soft);color:var(--bad)}
/* S703: the recording player */
.play,.btn.soft{background-image:linear-gradient(to right,rgba(31,95,74,.22) var(--pp,0%),transparent var(--pp,0%))}
.play.on{background-image:linear-gradient(to right,rgba(255,255,255,.38) var(--pp,0%),transparent var(--pp,0%))}
.play.load,.btn.load{opacity:.75}
.pl{position:fixed;left:0;right:0;bottom:0;z-index:8;display:none;background:var(--paper);border-top:3px solid var(--accent);box-shadow:0 -4px 14px rgba(0,0,0,.12);padding:10px 16px calc(12px + env(safe-area-inset-bottom))}
.pl .plrow{display:flex;align-items:center;gap:12px;max-width:1100px;margin:0 auto}
.pl .plbtn{flex:none;width:46px;height:46px;border-radius:50%;border:0;background:var(--accent);color:var(--accent-ink);font-size:19px;cursor:pointer}
.pl .pllab{flex:1;min-width:0;font-size:15px;color:var(--fg);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pl .pltime{flex:none;font-family:var(--mono);font-size:16px;font-weight:600;color:var(--fg)}
.pl .plx{flex:none;border:1px solid var(--line);background:var(--paper);color:var(--muted);border-radius:8px;font-size:20px;line-height:1;padding:6px 11px;cursor:pointer}
.pl .plt{max-width:1100px;margin:10px auto 0;height:12px;border-radius:6px;background:var(--line);cursor:pointer;position:relative;overflow:hidden}
.pl .plf{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--accent);border-radius:6px}
.pl.loading .plf{width:100%!important;background:repeating-linear-gradient(45deg,var(--line) 0 10px,#c9c5b9 10px 20px)}
.pl .plmsg{max-width:1100px;margin:8px auto 0;font-size:15px;display:none}
.pl.err{border-top-color:var(--bad)}.pl.err .plmsg{display:block;color:var(--bad);font-weight:600}
.pl.err .plt,.pl.err .plbtn{display:none}
body.plon .toast{bottom:var(--plh,140px)}
.toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);background:var(--fg);color:var(--paper);padding:9px 14px;border-radius:8px;font-size:13.5px;max-width:92vw;display:none;z-index:9}
/* S742_CALLS_R3: the one-line key, folded sections with a coloured top line, two columns */
.key{display:flex;flex-wrap:wrap;align-items:center;gap:4px 16px;font-size:13px;color:var(--muted);padding:0 2px}
.key b{font-size:12px;letter-spacing:.08em;text-transform:uppercase}
.key span{display:inline-flex;align-items:center;gap:4px;white-space:nowrap}.key .ic{width:16px;height:16px}.key .dim{color:#6b716d}
.cnt .sep{width:1px;height:18px;background:var(--line)}
.cols{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(0,1fr);gap:10px;align-items:start}
.col{display:grid;grid-template-columns:minmax(0,1fr);gap:10px;min-width:0}.cols>section,.col>section{min-width:0}
details.s{border-top:1px solid var(--line)}
details.s>summary{list-style:none;cursor:pointer;display:flex;flex-wrap:wrap;align-items:center;gap:6px 12px;padding:6px 12px;min-height:40px;border-left:4px solid var(--good)}
details.s>summary::-webkit-details-marker{display:none}
details.s.amber>summary{background:var(--warn-soft);border-left-color:var(--warn)}
details.s.rose>summary{background:var(--bad-soft);border-left-color:var(--bad)}
details.s>summary .car{font-size:11px;color:var(--muted)}details.s[open]>summary .car{transform:rotate(90deg)}
details.s>summary .sl{flex:1;min-width:0;font-size:14px}details.s>summary .sl .sub{color:var(--muted);font-size:13px}
details.s>summary .sr{font-family:var(--mono);font-size:13px;font-weight:600}
details.s.amber>summary .sr{color:var(--warn-ink)}details.s.rose>summary .sr{color:var(--bad)}
.fuline{padding:6px 12px;font-size:14px}.fuline .g,.g{color:var(--good)}.fuline .w{color:var(--warn-ink)}.fuline .b{color:var(--bad)}
.fr{display:grid;grid-template-columns:14px 1fr auto auto;gap:8px;align-items:start;padding:6px 12px 6px 10px;border-top:1px solid var(--line2)}
.fr .t{min-width:0;font-size:14px}.fr .t .sub{display:block;color:var(--muted);font-size:13px;margin-top:2px}
.fr .q{display:block;font-size:13px;color:var(--muted);margin-top:3px}
.fr .act{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.mono{font-family:var(--mono);font-size:12.5px;white-space:nowrap}
.unk{font-family:var(--mono);font-size:12px;padding:2px 8px;border-radius:999px;background:var(--warn-soft);color:var(--warn-ink);white-space:nowrap}
.pillx{display:inline-block;font-weight:600;font-size:13px;padding:3px 10px;border-radius:999px;white-space:nowrap;background:var(--chip);color:var(--fg)}
.pillx.green{background:#e3f0e7;color:var(--good)}.pillx.amber{background:var(--warn-soft);color:var(--warn-ink)}.pillx.rose{background:var(--bad-soft);color:var(--bad)}
table.mini th,table.mini td{padding:3px 10px;font-size:13.5px}
@media (max-width:420px){table.mini th,table.mini td{padding:3px 6px;font-size:12.5px;letter-spacing:0}}
.subh{padding:5px 12px 5px 14px;font-weight:600;font-size:13.5px;border-top:1px solid var(--line2);background:#faf9f5}
.subh.rose{background:var(--bad-soft);color:var(--bad)}.subh.amber{background:var(--warn-soft);color:var(--warn-ink)}
details.s>summary .figs{font-size:13.5px;color:var(--fg);font-weight:400}.figs .b{color:var(--bad)}.figs .w{color:var(--warn-ink)}
/* S817: the follow-up lines -- the owner's mock-up of 13-Nov (sizes and colours as approved) */
.fuhead{padding:8px 14px 0;font-size:13px;color:#4A5562}
details.fu2{margin:8px 10px;border:1px solid #D5DBE1;border-radius:12px;background:#FFFFFF;overflow:hidden}
details.fu2[open]{border:2px solid #1F5FBF}
details.fu2>summary{list-style:none;cursor:pointer;display:flex;flex-direction:column;gap:6px;padding:14px;min-height:44px}
details.fu2>summary::-webkit-details-marker{display:none}
.fu2 .ft{display:flex;justify-content:space-between;gap:8px;font-size:14px;font-weight:600;color:#1B1F24}
.fu2 .ft .fn{color:#4A5562;font-weight:500;white-space:nowrap}
.fu2 .fbig{font-size:24px;font-weight:700;line-height:1.2}
.fu2 .fbig.green{color:#1E6B3A}.fu2 .fbig.amber{color:#8A5A00}.fu2 .fbig.rose{color:#B3261E}
.fu2 .fre{font-size:14px;color:#1B1F24}
.fu2 .fea{font-size:13px;color:#4A5562}
ul.fpl{list-style:none;margin:0;padding:0 14px 4px}
li.fp{border-top:1px solid #E3E7EB;padding:10px 0;display:flex;flex-direction:column;gap:4px;min-width:0}
.fp .f1{display:flex;justify-content:space-between;gap:8px;font-size:14px;font-weight:600;color:#1B1F24}
.fp .f1 b{font-weight:600}
.fp .f1 .nm{min-width:0;overflow-wrap:anywhere}
.fp .late{white-space:nowrap}.fp .late.amber{color:#8A5A00}.fp .late.rose{color:#B3261E}
.fp .f2{font-size:13px;color:#4A5562}
.fp .f3,.fp .f4{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:13px;color:#1B1F24}
.fp .f3>span,.fp .f4>span{min-width:0}
.fp .f3 .no{color:#B3261E;font-weight:600}
.fp .f3 .btn,.fp .f4 .play{flex:none;min-height:44px;padding:0 12px;border-radius:8px;font-size:13px;font-weight:600;font-family:var(--body)}
.fp .f4 .play{color:#1F5FBF;border-color:#1F5FBF}
.fp .f4 .play.on{background-color:#1F5FBF;color:#FFFFFF}
.fp .snip{display:block;font-size:13px;color:#1B1F24;background:var(--bg);border-radius:6px;padding:4px 8px}
.fp .full{white-space:pre-wrap;display:block;margin-top:4px;font-size:13px;background:var(--bg);border-radius:6px;padding:6px 8px;max-height:60vh;overflow:auto}
.funote{padding:4px 14px 10px;font-size:13px;color:#4A5562;line-height:1.45}
/* S747: the review buttons, the log line and the transcript on each staff call; the disputes */
.rb{font-weight:600;font-size:12.5px;padding:4px 9px;border-radius:6px;border:1px solid var(--accent);background:var(--paper);color:var(--accent);cursor:pointer;white-space:nowrap;font-family:var(--body)}
.rb.p{background:var(--accent);color:var(--accent-ink)}
.rb.done,.rb:disabled{border-color:var(--line);color:var(--muted);background:var(--paper);cursor:default}
.fr .act{max-width:360px}
.fr .logl{display:block;font-size:12.5px;color:var(--muted);margin-top:2px}
.fr .snip{display:block;margin-top:3px;font-size:13px;background:var(--bg);border-radius:6px;padding:4px 8px}
.fr .full{white-space:pre-wrap;display:block;margin-top:4px;font-size:13px;background:var(--bg);border-radius:6px;padding:6px 8px;max-height:60vh;overflow:auto}
.fr .rvs{display:block;font-size:12.5px;color:var(--blue);font-weight:600;margin-top:3px}
.fr .tag{font-family:var(--mono);font-size:11.5px;padding:1px 7px;border-radius:999px;background:var(--chip);color:var(--muted);white-space:nowrap}
.fr .nbox{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}.fr .nbox[hidden]{display:none}
.fr .nbox input{flex:1;min-width:0;font:inherit;font-size:13px;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--fg)}
.fr .dispute{display:block;background:var(--warn-soft);border-left:3px solid var(--warn);padding:5px 9px;border-radius:6px;margin-top:4px;font-size:13.5px}
.subh.blue{color:var(--blue)}
details.rvd>summary{min-height:34px;border-left-color:var(--line)}
@media (max-width:900px){.cols{grid-template-columns:minmax(0,1fr)}h2{flex-wrap:wrap}}
@media (max-width:640px){
  .fr{grid-template-columns:14px 1fr}.fr .pillx,.fr .act{grid-column:2;justify-self:start}
  .wrap{padding:10px 12px 40px}h1{font-size:20px}
  form.q input{min-width:0;width:100%}form.q{width:100%}
  .strip .big{font-size:15.5px}
  details.p>summary{grid-template-columns:14px 1fr}.right{grid-column:2;flex-direction:row;align-items:center;gap:10px}
  .tl{grid-template-columns:40px 20px 1fr}.tl .play,.tl .act{grid-column:2/-1;justify-self:start}
  .ny{flex-wrap:wrap}.ny .chain{display:flex;width:100%;margin-top:3px}.mbtn.asof{margin-left:0}
}
</style>
</head>
{% macro strow(p, it, tail) %}<div class="fr"><span class="dot {{ 'b' if it.kind=='in_miss' else ('g' if it.answered else 'w') }}"></span><span class="t"><span class="c">{{ I[it.kind]|safe }}</span> <span class="mono">{% if d.mode in ('7','30') %}{{ it.day[8:] }}/{{ it.day[5:7] }} {% endif %}{{ it.t_h }}</span> <b>{{ p.name or p.phone_h }}</b>{% if p.cid %} · {{ p.cid }}{% endif %}{% if p.name %} <span class="mono">{{ p.phone_h }}</span>{% endif %}{% if tail %}<span class="sub">{{ tail }}</span>{% endif %}{% if it.evidence %}<span class="q">AI heard: “{{ it.evidence[:90] }}”</span>{% endif %}</span><span></span><span class="act">{% if it.has_rec and it.jk %}<button type="button" class="play" data-jk="{{ it.jk }}" onclick="playJk('{{ it.jk }}',this)">&#9654; {{ it.dur_h or 'play' }}</button>{% endif %}{% if it.kind=='in_miss' %}<button type="button" class="btn" onclick="callBack('{{ p.phone }}',this)">Call back</button>{% endif %}</span></div>{% endmacro %}
{% macro srow(c, p, it, tail, kind) %}{% set rs = c.rv.get(it.ref, {}) %}{% set fn = c.name.split()[0] %}<div class="fr" data-ref="{{ it.ref }}" data-staff="{{ c.key }}"><span class="dot {{ 'b' if kind in ('not_back','not_logged') else ('w' if kind in ('mismatch','wa') else 'g') }}"></span><span class="t"><span class="c">{{ I[it.kind]|safe }}</span> <span class="mono">{% if d.mode in ('7','30') %}{{ it.day[8:] }}/{{ it.day[5:7] }} {% endif %}{{ it.t_h }}</span> <b>{{ p.name or p.phone_h }}</b>{% if p.cid %} · {{ p.cid }}{% endif %}{% if p.name %} <span class="mono">{{ p.phone_h }}</span>{% endif %}{% if it.rec_mob %} <span class="tag">reception mobile</span>{% endif %}{% if it.ref in c.pre_punch %} <span class="tag">before punch-in</span>{% endif %}{% if tail %}<span class="sub">{{ tail }}</span>{% endif %}
  {% if it.ch != 'wa' and it.kind != 'in_miss' %}<span class="logl">log: {{ ('filed ' ~ it.claimed_h) if it.claimed_h else 'nothing filed' }} · AI: {{ it.ai_h or '—' }}{% if it.final %} · your verdict: {{ it.final }}{% endif %}</span>{% endif %}
  {% if it.ch == 'wa' %}<span class="q">“{{ it.body[:160] }}”</span>{% elif it.tx_head and it.jk %}<span class="snip">{{ it.tx_head }}{% if it.tx_head|length >= 200 %}…{% endif %} <a href="#" onclick="return wholeTx(this,'{{ it.jk }}')">whole transcript</a></span>{% elif it.evidence %}<span class="q">AI heard: “{{ it.evidence[:90] }}”</span>{% endif %}
  {% if rs.asked %}<span class="rvs">Asked to log · {{ rs.asked[8:10] }}-{{ rs.asked[5:7] }} {{ rs.asked[11:16] }}{% if kind == 'not_logged' %} — waiting for {{ fn }}{% endif %}</span>{% endif %}
  {% for a, n in rs.get('notes', []) %}<span class="rvs">Note to {{ fn }} · {{ a[8:10] }}-{{ a[5:7] }} {{ a[11:16] }}: “{{ n }}”</span>{% endfor %}
  {% if kind == 'reviewed' %}<span class="rvs">{{ rw.get(rs.state, rs.state) }} · {{ rs.at[8:10] }}-{{ rs.at[5:7] }} {{ rs.at[11:16] }}</span>{% endif %}
  <span class="nbox" hidden><input type="text" maxlength="300" aria-label="Note to {{ fn }}" placeholder="Your note to {{ fn }} — it shows on their card"><button type="button" class="rb p nb" onclick="rvNote(this)">Send note</button></span></span>
  <span></span><span class="act">{% if it.has_rec and it.jk %}<button type="button" class="play" data-jk="{{ it.jk }}" onclick="playJk('{{ it.jk }}',this)">&#9654; {{ it.dur_h or 'play' }}</button>{% endif %}{% if it.kind == 'in_miss' and kind != 'reviewed' %}<button type="button" class="btn" onclick="callBack('{{ p.phone }}',this)">Call back</button>{% endif %}{% if kind == 'not_logged' %}{% if rs.asked %}<button type="button" class="rb done" disabled>Asked</button>{% else %}<button type="button" class="rb p" onclick="rv(this,'ask_log')">Ask to log</button>{% endif %}{% endif %}{% if kind == 'mismatch' %}<button type="button" class="rb" onclick="rv(this,'staff_right')">Staff right</button><button type="button" class="rb" onclick="rv(this,'ai_right')">AI right</button>{% elif kind in ('not_back','not_logged','wa') %}<button type="button" class="rb" onclick="rv(this,'reviewed')">Mark reviewed</button>{% endif %}{% if kind == 'reviewed' %}<button type="button" class="rb" onclick="rv(this,'undo')">Undo</button>{% else %}<button type="button" class="rb nb" onclick="rvOpen(this)">Note to staff</button>{% endif %}</span></div>{% endmacro %}
{% macro brow(c, p, it, tail, kind) %}{% set rs = c.rv.get(it.ref, {}) %}<div class="fr" data-ref="{{ it.ref }}" data-staff="{{ c.staff_of.get(it.ref, '') }}"><span class="dot {{ 'b' if kind == 'not_back' else 'g' }}"></span><span class="t"><span class="c">{{ I[it.kind]|safe }}</span> <span class="mono">{% if d.mode in ('7','30') %}{{ it.day[8:] }}/{{ it.day[5:7] }} {% endif %}{{ it.t_h }}</span> <b>{{ p.name or p.phone_h }}</b>{% if p.cid %} · {{ p.cid }}{% endif %}{% if p.name %} <span class="mono">{{ p.phone_h }}</span>{% endif %}{% if tail %}<span class="sub">{{ tail }}</span>{% endif %}{% if kind == 'reviewed' and rs.at %}<span class="rvs">{{ rw.get(rs.state, rs.state) }} · {{ rs.at[8:10] }}-{{ rs.at[5:7] }} {{ rs.at[11:16] }}</span>{% endif %}</span><span></span><span class="act">{% if it.has_rec and it.jk %}<button type="button" class="play" data-jk="{{ it.jk }}" onclick="playJk('{{ it.jk }}',this)">&#9654; {{ it.dur_h or 'play' }}</button>{% endif %}{% if kind == 'not_back' %}<button type="button" class="btn" onclick="callBack('{{ p.phone }}',this)">Call back</button>{% if c.staff_of.get(it.ref) %}<button type="button" class="rb" onclick="rv(this,'reviewed')">Mark reviewed</button>{% endif %}{% elif kind == 'reviewed' and c.staff_of.get(it.ref) %}<button type="button" class="rb" onclick="rv(this,'undo')">Undo</button>{% endif %}</span></div>{% endmacro %}
{% macro furow(r) %}<div class="fr {{ r.tone }}"><span class="dot {{ {'green':'g','amber':'w','rose':'b'}.get(r.tone,'') }}"></span>
  <span class="t"><b>{{ r.name or r.phone_h or 'no name' }}</b>{% if r.cid %} · {{ r.cid }}{% endif %}{% if r.phone %} <span class="mono">{{ r.phone_h }}</span>{% else %} <span class="unk">no mobile</span>{% endif %}{% if r.dx %} · {{ r.dx }}{% endif %}
    <span class="sub">due {{ r.due_h }}{% if r.age > 0 %} ({{ r.age }} day{{ 's' if r.age!=1 else '' }} ago){% endif %}{% if r.tries %} · <span class="chain">{% for t in r.tries %}{% if not loop.first %}<span class="arr">&#8594;</span>{% endif %}<span class="c">{{ I[t.kind]|safe }}<span>{% if t.day != today_iso %}{{ t.day[8:] }}/{{ t.day[5:7] }} {% endif %}{{ t.t_h }}</span></span>{% endfor %}{% set lt = r.tries[-1] %}{% if lt.agent_h %} <span class="tail">{{ lt.agent_h }}</span>{% endif %}</span>{% endif %}{% if r.section and r.section|lower not in ('follow-up','due today','grace period') %} · {{ r.section }}{% endif %}</span>
    {% if r.quote %}<span class="q">{{ r.quote }}</span>{% endif %}</span>
  <span class="pillx {{ r.tone }}">{{ r.pill }}</span>
  <span class="act">{% if r.play %}<button type="button" class="play" data-jk="{{ r.play.jk }}" onclick="playJk('{{ r.play.jk }}',this)">&#9654; {{ r.play.dur_h or 'play' }}</button>{% endif %}{% if r.phone and not r.closed %}<button type="button" class="btn" onclick="callBack('{{ r.phone }}',this)">Call</button>{% endif %}</span>
</div>
{% endmacro %}
{% macro furow2(r, tone) %}<li class="fp">
  <div class="f1"><span class="nm"><b>{{ r.name or r.phone_h or 'no name' }}</b>{% if r.cid %} · ID {{ r.cid }}{% endif %}</span><span class="late {{ tone }}">{{ r.age }} day{{ 's' if r.age!=1 else '' }} late</span></div>
  <div class="f2">{% if r.phone %}{{ r.phone_h }}{% else %}no mobile{% endif %} · due {{ r.due_wd }}{% if r.dx %} · {{ r.dx }}{% endif %}</div>
  <div class="f3">{% if r.call_line %}<span>{{ r.call_line }}</span>{% else %}<span class="no">Not called since the due date</span>{% endif %}{% if r.phone %}<button type="button" class="btn" onclick="callBack('{{ r.phone }}',this)">Call</button>{% endif %}</div>
  {% if r.note_h %}<div class="f2">{{ r.note_h }}{% if r.quote and r.quote.startswith('WhatsApp') %} — {{ r.quote }}{% endif %}</div>{% endif %}
  {% set lr = r.last_reached %}{% if lr %}<div class="f4"><span>Last reached {{ lr.when_h }}{% if lr.rel %}, {{ lr.rel }}{% endif %}{% if lr.said %} — {{ lr.said }}{% endif %}</span>{% if lr.has_rec %}<button type="button" class="play" data-jk="{{ lr.jk }}" onclick="playJk('{{ lr.jk }}',this)">&#9654; Play{% if lr.dur_h %} {{ lr.dur_h }}{% endif %}</button>{% endif %}</div>
  {% if lr.tx_head and lr.jk %}<span class="snip">{{ lr.tx_head }}{% if lr.tx_head|length >= 200 %}…{% endif %} <a href="#" onclick="return wholeTx(this,'{{ lr.jk }}')">whole transcript</a></span>{% endif %}{% else %}<div class="f2">No answered call in the last {{ fu_back }} days</div>{% endif %}
</li>
{% endmacro %}
<body>
<div class="wrap">
  <div class="head">
    <h1>Calls <a href="/finance/console">&larr; console</a></h1>
    <div class="tabs">
      <a class="{{ 'on' if d.mode=='today' else '' }}" href="/portal/console">Today</a>
      <a class="{{ 'on' if d.mode=='yesterday' else '' }}" href="/portal/console?span=yesterday">Yesterday</a>
      <a class="{{ 'on' if d.mode=='7' else '' }}" href="/portal/console?span=7">7 days</a>
      <a class="{{ 'on' if d.mode=='30' else '' }}" href="/portal/console?span=30">30 days</a>
      {% if d.mode=='day' %}<a class="on" href="/portal/console?day={{ d.to }}">{{ d.title_day }}</a>{% endif %}
    </div>
    <form class="q" method="GET" action="/portal/console">{% if d.mode in ('yesterday','7','30') %}<input type="hidden" name="span" value="{{ d.mode }}">{% elif d.mode=='day' %}<input type="hidden" name="day" value="{{ d.to }}">{% endif %}<span>Search</span><input type="text" name="q" value="{{ d.q }}" placeholder="number · name · diagnosis · words said"></form>
    <a class="mbtn" href="#staff">staff cards &darr;</a>
    <button type="button" class="mbtn" onclick="expandAll()">expand all</button>
    <button type="button" class="mbtn" onclick="foldAll()">fold all</button>
    <a class="mbtn asof {{ 'w' if m.stale else '' }}" href="{{ self_url }}" title="{{ 'the reading is older than expected' if m.stale else 'reload' }}">as of {{ m.asof }}{% if m.stale %} · stale{% elif m.next %} · next reading {{ m.next }}{% endif %} · refresh</a>
  </div>

  {% if not m.ok %}<div class="banner bad">The call records could not be read yet — the builder may not have run, or console.db is missing. Nothing is shown as zero.</div>{% endif %}
  {% if not d.wa_ok %}<div class="banner">The WhatsApp messages could not be read just now — the timelines show calls only. Nothing is shown as zero.</div>{% endif %}
  {% if d.no_number %}<div class="banner">{{ d.no_number }} call{{ 's' if d.no_number!=1 else '' }} in this window carr{{ 'y' if d.no_number!=1 else 'ies' }} no number and cannot be placed with a person.</div>{% endif %}

  <div class="key" role="note" aria-label="Icon key"><b>Key</b>
    <span>{{ I.in_ok|safe }}In</span><span>{{ I.in_miss|safe }}Missed</span><span>{{ I.out_ok|safe }}Out</span><span>{{ I.out_miss|safe }}No answer</span>
    <span>{{ I.wa_in|safe }}WhatsApp in</span><span>{{ I.wa_out|safe }}WhatsApp sent</span><span>{{ I.wa_fail|safe }}Failed</span><span>{{ I.wa_tpl|safe }}Template</span>
    <span class="dim">dashed = not connected</span>
  </div>

  {% set c = d.counts %}{% set fu = d.fu %}
  <div class="card strip">
    <div class="big">{{ d.title_day.split(' · ')[0] }}: <b>{{ c.calls }} call{{ 's' if c.calls!=1 else '' }}</b> from <b>{{ c.callers }} caller{{ 's' if c.callers!=1 else '' }}</b>{% if c.wa_in %} · <b>{{ c.wa_in }} WhatsApp{{ 's' if c.wa_in!=1 else '' }}</b> from <b>{{ c.wa_people }} {{ 'person' if c.wa_people==1 else 'people' }}</b>{% endif %}{% if c.awaiting %} · <a href="#people" class="b">{{ c.awaiting }} {{ 'person' if c.awaiting==1 else 'people' }} nobody has answered</a>{% endif %}{% if c.tried %} · <a href="#people" class="w">{{ c.tried }} tried, not reached</a>{% endif %}{% if d.mode=='today' and fu.found and fu.today.due %} · follow-ups called <a href="#followups" class="{{ 'w' if fu.today.called < fu.today.due else '' }}">{{ fu.today.called }} of {{ fu.today.due }}</a>{% endif %}{% if c.flagged %} · {{ c.flagged }} call{{ 's' if c.flagged!=1 else '' }} flagged for you{% endif %}{% if c.mismatch %} · {{ c.mismatch }} to check (staff ≠ AI){% endif %}.</div>
    <div class="cnt">
      <span title="incoming calls answered">{{ I.in_ok|safe }}<b>{{ c.in_ok }}</b></span>
      <span title="outgoing calls answered">{{ I.out_ok|safe }}<b>{{ c.out_ok }}</b></span>
      <span title="missed, then we called back and reached them">{{ I.in_miss|safe }}<span class="arr">&#8594;</span>{{ I.out_ok|safe }}<b>{{ c.miss_then_back }}</b></span>
      <span title="missed, then they rang again and got through">{{ I.in_miss|safe }}<span class="arr">&#8594;</span>{{ I.in_ok|safe }}<b>{{ c.miss_then_again }}</b></span>
      <span title="missed, nobody reached">{{ I.in_miss|safe }}<b>{{ c.miss_open }}</b></span>
      <span class="sep"></span>
      <span title="WhatsApps received">{{ I.wa_in|safe }}<b>{{ c.wa_in }}</b></span>
      <span title="replies delivered">{{ I.wa_out|safe }}<b>{{ c.wa_replied }}</b></span>
    </div>
    <div class="bar"><i class="g" style="width:{{ c.bar.g }}%"></i><i class="w" style="width:{{ c.bar.w }}%"></i><i class="b" style="width:{{ c.bar.b }}%"></i></div>
  </div>

  <div class="cols">
  <div class="col">
  {% if d.mode in ('today','day') %}
  <section id="needs">
    <h2><span class="l">Needs you {{ 'today' if d.mode=='today' else d.title_day }}</span><span class="pill {{ 'w' if d.needs else '' }}">{{ d.needs|length }} need you</span></h2>
    <div class="card">
      {% for n in d.needs %}
      <div class="ny {{ n.tone }}"><div class="t"><div><b>{{ n.who }}</b>{% if n.unknown %} <span class="unk">unknown number</span>{% endif %} &nbsp;<span class="chain">{% for it in n.chain %}{% if not loop.first %}<span class="arr">&#8594;</span>{% endif %}<span class="c">{{ I[it.kind]|safe }}<span>{{ it.t_h }}</span></span>{% endfor %}</span> &nbsp;{% if n.tone=='rose' %}<b style="color:var(--bad)">{{ n.text }}</b>{% else %}{{ n.text }}{% endif %}</div>{% if n.sub %}<span class="sub">{{ n.sub }}</span>{% endif %}</div>
        <b class="n">{{ n.n }}</b>
        {% if n.act=='call' %}<button type="button" class="btn" onclick="callBack('{{ n.phone }}',this)">Call back</button>{% elif n.act=='listen' %}<button type="button" class="btn soft" onclick="playJk('{{ n.jk }}',this)">Listen</button>{% elif n.act=='review' %}<a class="btn soft" href="#{{ n.anchor }}" onclick="openRow('{{ n.anchor }}')">Review</a>{% endif %}
      </div>
      {% else %}<div class="empty">Nothing needs you{{ ' today' if d.mode=='today' else '' }}.</div>{% endfor %}
    </div>
  </section>
  {% endif %}

  <section id="people">
    <h2><span class="l">People {{ 'today' if d.mode=='today' else '' }} — {{ I.in_ok|safe }}+{{ I.wa_in|safe }} one timeline each</span><span class="pill {{ 'w' if (c.awaiting or c.tried) else '' }}">{{ d.chips.all }} {{ 'person' if d.chips.all==1 else 'people' }}{% if c.awaiting %} · {{ c.awaiting }} awaiting{% endif %}{% if c.tried %} · {{ c.tried }} tried{% endif %}</span></h2>
    <div class="card">
      <div class="chips" role="group" aria-label="filter">
        <button type="button" aria-pressed="true" data-f="all" onclick="chip(this)">All {{ d.chips.all }}</button>
        <button type="button" aria-pressed="false" data-f="awaiting" onclick="chip(this)">Awaiting {{ d.chips.awaiting }}</button>
        <button type="button" aria-pressed="false" data-f="calls" onclick="chip(this)">Calls {{ d.chips.calls }}</button>
        <button type="button" aria-pressed="false" data-f="wa" onclick="chip(this)">WhatsApp {{ d.chips.wa }}</button>
        <button type="button" aria-pressed="false" data-f="unknown" onclick="chip(this)">Unknown numbers {{ d.chips.unknown }}</button>
      </div>
      {% for gday, glabel, plist in d.groups %}
      {% if d.groups|length > 1 %}<div class="note" style="border-top:0;border-bottom:1px solid var(--line);font-weight:600;color:var(--fg)">{{ glabel }} <span style="font-family:var(--mono);font-weight:400;color:var(--muted)">· {{ plist|length }} {{ 'person' if plist|length==1 else 'people' }}</span></div>{% endif %}
      {% for p in plist %}
      <details class="p {{ p.state if p.state in ('rose','amber') else '' }}" id="p{{ p.phone }}" data-state="{{ p.state }}" data-unknown="{{ 1 if p.unknown else 0 }}" data-calls="{{ p.n_calls }}" data-wa="{{ p.n_wa }}">
        <summary><span class="car" aria-hidden="true">&#9654;</span>
          <span class="who">{% if p.name %}<b>{{ p.name }}{% if p.cid %} · {{ p.cid }}{% endif %}</b>{% else %}<b>{{ p.phone_h }}</b> <span class="unk">unknown number</span>{% endif %}{% if p.spam %} <span class="spam">marked spam</span>{% endif %}
            {% if p.name %}<span class="sub">{{ p.phone_h }}{% if p.agesex %} · {{ p.agesex }}{% endif %}{% if p.dx %} · {{ p.dx }}{% endif %}</span>{% endif %}<span class="sub"><span class="chain">{% for it in p.calls %}{% if not loop.first %}<span class="arr">&#8594;</span>{% endif %}<span class="c">{{ I[it.kind]|safe }}<span>{% if d.mode in ('7','30') and it.day != gday %}{{ it.day[8:] }}/{{ it.day[5:7] }} {% endif %}{{ it.t_h }}</span></span>{% endfor %}{% if p.tail %}<span class="arr">&#8594;</span><span class="tail">{{ p.tail }}</span>{% endif %}</span></span>
          </span>
          <span class="right"><span class="cnt">{% if p.n_calls %}<span title="calls">{{ I.calls|safe }}<b>{{ p.n_calls }}</b></span>{% endif %}{% if p.n_wa %}<span title="WhatsApps">{{ I.wa_in|safe }}<b>{{ p.n_wa }}</b></span>{% endif %}</span><b class="st {{ p.state }}">{{ p.state_h }}</b></span>
        </summary>
        {% for it in p.calls %}{% set w = words(it) %}
        <div class="tl"><span class="tm">{{ it.t_h }}</span><span>{{ I[it.kind]|safe }}</span>
          <span class="tx">{{ w[0] }}{% if w[1] %}<span class="sub">{{ w[1] }}</span>{% endif %}{% if it.ch=='wa' %}<span class="snip">{{ it.body }}</span>{% endif %}{% if it.evidence %}<span class="sub">“{{ it.evidence }}”</span>{% endif %}{% if it.tx_head %}<span class="snip">{{ it.tx_head }}{% if it.tx_head|length >= 200 %}…{% endif %} <a href="#" onclick="return wholeTx(this,'{{ it.jk }}')">whole transcript</a></span>{% endif %}
            {% if it.jk and it.answered %}<span class="rev"><form method="POST" action="/portal/console/review" style="display:inline-flex;gap:6px;align-items:center;margin:0"><input type="hidden" name="join_key" value="{{ it.jk }}"><input type="hidden" name="ret" value="{{ ret_qs }}"><select name="final_outcome" onchange="this.form.submit()"><option value="">{{ it.final or 'your verdict…' }}</option>{% for v in vocab %}<option value="{{ v }}" {{ 'selected' if it.final==v else '' }}>{{ v }}</option>{% endfor %}</select></form></span>{% endif %}
          </span>
          {% if it.has_rec and it.jk %}<button type="button" class="play" data-jk="{{ it.jk }}" onclick="playJk('{{ it.jk }}',this)">&#9654; {{ it.dur_h or 'play' }}</button>{% elif it.dur_h %}<span class="tm">{{ it.dur_h }}</span>{% else %}<span></span>{% endif %}
        </div>
        {% endfor %}
        {% if p.state=='rose' %}<div class="tl rose"><span class="tm"></span><span>{{ I['wa_in' if p.wa_wait else 'in_miss']|safe }}</span><span class="tx"><b style="color:var(--bad)">{{ 'Nobody has replied' if p.wa_wait else 'Nobody has called back' }}</b><span class="sub">{{ 'a WhatsApp is answered by a delivered reply, or a call of 30 s or more within 2 hours' if p.wa_wait else 'a missed call is answered only by a call' }}</span></span><button type="button" class="btn act" onclick="callBack('{{ p.phone }}',this)">Call back</button></div>{% endif %}
      </details>
      {% endfor %}
      {% endfor %}
      {% if not d.people %}<div class="empty">No calls or WhatsApps {{ 'today yet' if d.mode=='today' else 'in this window' }}{% if d.q %} matching “{{ d.q }}”{% endif %}.</div>{% endif %}
    </div>
  </section>
  </div>

  <div class="col">
  <section id="followups">
    <h2><span class="l">Follow-ups — one row per patient</span><span class="pill {{ 'w' if fu.open else '' }}">{% if fu.found %}{{ fu.open }} open{% if fu.removed %} · {{ fu.removed }} repeat{{ 's' if fu.removed!=1 else '' }} folded{% endif %}{% else %}feed not readable{% endif %}</span></h2>
    <div class="card">
      {% if not fu.found %}<div class="empty">The tracker's follow-up feed was not readable at the last reading — nothing is shown as zero.</div>{% else %}
      <div class="fuhead">Only patients who have not visited are listed.</div>
      <div class="fuline">Today: <b>{{ fu.today.due }} due</b> · {{ fu.today.called }} called · {{ fu.today.reached }} reached · <b class="g">{{ fu.today.came }} came</b>{% if fu.who %} &nbsp;·&nbsp; Who called: {% for w, n in fu.who %}<b>{{ w }} {{ n }}</b>{{ ', ' if not loop.last else '' }}{% endfor %}{% endif %}</div>
      {% if fu.src=='no_shows' %}<div class="note">Showing the older list (due before today) until the next reading brings the whole feed — today's follow-ups appear within ten minutes.</div>{% endif %}
      {% if not fu.visits_ok %}<div class="note">The Docterz visits could not be read in full just now — some patients who came may still show as open.</div>{% endif %}
      {% if not fu.advice_ok %}<div class="note">The advised periods could not be read just now — a patient who came a little before the due date may still show as open.</div>{% endif %}
      {% for key, title, sub, rows, n, called, reached, tone in fu.bands %}{% set L = fu.fl[key] %}
      <details class="fu2" id="fu-{{ key }}">
        <summary><span class="ft"><span>{{ title }}{% if key != 'today' %} · {{ sub }}{% endif %}</span><span class="fn">{{ n }} {% if key == 'today' %}patient{{ 's' if n != 1 else '' }}{% else %}not visited{% endif %}</span></span>
          <span class="fbig {{ L.tone }}">Called today {{ L.ct }} of {{ n }}</span>
          {% if L.ct or L.rt %}<span class="fre">Reached {{ L.rt }}</span>{% endif %}
          {% if key != 'today' %}<span class="fea">Earlier days, after the due date: {{ L.ec }} called · {{ L.er }} reached</span>{% endif %}</summary>
        {% if key == 'today' %}{% for r in rows[:fu_max] %}{{ furow(r) }}{% endfor %}{% else %}<ul class="fpl">{% for r in rows[:fu_max] %}{{ furow2(r, 'amber' if key == 'grace' else 'rose') }}{% endfor %}</ul>{% endif %}
        {% if n > fu_max %}<div class="note">… and {{ n - fu_max }} more in this section (the not-called first are shown).</div>{% endif %}
        {% if not rows %}<div class="empty">None.</div>{% endif %}
      </details>
      {% endfor %}
      <div class="funote">In Grace and older, a call counts only from the day after the due date. A call made on the appointment day does not count. Today’s list counts today’s calls.</div>
      <details class="s green" id="fu-came">
        <summary><span class="car" aria-hidden="true">&#9654;</span><span class="sl"><b>Came / closed</b> <span class="sub">the last 7 days — a Docterz visit, or “not coming” filed</span></span><span class="sr">{{ fu.came|length }}</span></summary>
        {% for r in fu.came[:fu_max] %}{{ furow(r) }}{% endfor %}
        {% if not fu.came %}<div class="empty">None this week.</div>{% endif %}
      </details>
      {% endif %}
      <div class="note">The WhatsApp batch send by section is still at <a href="/portal/wa/followups">Follow-up WhatsApps (batch)</a>.</div>
    </div>
  </section>


  <section id="staff">
    <h2><span class="l">Staff performance — {{ I.in_ok|safe }}+{{ I.wa_in|safe }} on duty</span><span class="pill {{ 'w' if (d.staff or [])|selectattr('check')|list else '' }}">{{ (d.staff or [])|rejectattr('rec')|rejectattr('both')|list|length }} on calls</span></h2>
    <div class="card">
      <div class="note" style="border-top:0">A coloured line needs you — open it. “To check” is never a verdict: you decide, with the buttons on each call. Each person sees their own card, in Hindi, on Aaj ka kaam — the same figures — and can say “Galat hai?” about one call; it comes here as Disputed. Duty from the staff list and the morning punch.</div>
      {% if d.staff is none %}<div class="empty">The staff cards could not be made just now — the rest of the page is as usual.</div>{% endif %}
      {% if d.staff and not d.staff[0].rv_ok %}<div class="note">Your reviews could not be read just now — every call shows as to check until they can. Nothing you did is lost.</div>{% endif %}
      {% for c in (d.staff or []) %}{% set nl = c.not_logged|length %}{% set nb = c.not_back|length %}{% set mm = c.mismatch|length %}{% set fn = c.name.split()[0] %}
      <details class="s {{ c.tone }}" id="st-{{ c.key }}">
        <summary><span class="car" aria-hidden="true">&#9654;</span><span class="sl">{% if c.both %}<b>Both on duty</b> <span class="figs">{% if c.net_missed %}<b class="b">Net missed: {{ c.net_missed }} patient{{ 's' if c.net_missed != 1 else '' }}</b>{% else %}<b class="g">Net missed: 0</b>{% endif %} · {{ c.missed }} missed call{{ 's' if c.missed != 1 else '' }} from {{ c.missed_people }} patient{{ 's' if c.missed_people != 1 else '' }}, {{ c.missed_people - c.net_missed }} reached later · called back ≤1 h {{ c.cb_in_h }}/{{ c.missed }}{% if c.cb_later %} (+{{ c.cb_later }} later){% endif %} · counted once</span>{% elif c.rec %}<b>Reception mobile</b> <span class="figs">{{ c.answered }} answered · {{ c.made }} made · not credited to a person · {% if nl %}<b class="b">{{ nl }} not logged</b>{% else %}0 not logged{% endif %}{% if mm %} · <b class="w">staff ≠ AI {{ mm }}</b>{% endif %}</span>{% else %}<b>{{ fn }}</b> <span class="figs">{% if c.missed_known %}{% if c.net_missed %}<b class="b">Net missed: {{ c.net_missed }} patient{{ 's' if c.net_missed != 1 else '' }}</b>{% else %}<b class="g">Net missed: 0</b>{% endif %}{% if c.missed %} · {{ c.missed }} missed call{{ 's' if c.missed != 1 else '' }} from {{ c.missed_people }} patient{{ 's' if c.missed_people != 1 else '' }}, {{ c.missed_people - c.net_missed }} reached later{% endif %} · {{ c.answered }}/{{ c.rung }} answered{% else %}{{ c.answered }} answered · missed on duty not known{% endif %} · {{ c.made }} made{% if c.missed %} · called back ≤1 h {{ c.cb_in_h }}/{{ c.missed }}{% if c.cb_later %} (+{{ c.cb_later }} later){% endif %}{% endif %}{% if c.wa_in %} · WhatsApp {{ c.wa_in }} &#8594; {{ c.wa_ans }}{% endif %} · {% if nl %}<b class="b">{{ nl }} not logged</b>{% else %}0 not logged{% endif %}{% if mm %} · <b class="w">staff ≠ AI {{ mm }}</b>{% endif %} · {{ c.agreed }} agreed</span>{% endif %}</span><span class="sr">{{ (c.check ~ ' to check') if c.check else ('all clear' if c.missed_known else 'duty not known') }}{% if c.disputes %} · {{ c.disputes|length }} disputed{% endif %}</span></summary>
        <div class="note">{{ c.duty_h }}{% if c.punch_h %} · {{ c.punch_h }}{% endif %}{% if not c.rec and not c.both %} · <a href="/finance/aaj?as={{ c.key }}">{{ fn }}’s own card (Aaj ka kaam)</a>{% endif %}</div>
        {% if c.both %}{% if c.not_back %}<div class="subh rose">Missed while both on duty, not called back · {{ c.not_back|length }}</div>{% for p, it in c.not_back %}{{ brow(c, p, it, 'nobody has called back', 'not_back') }}{% endfor %}{% endif %}{% if c.reviewed %}<div class="subh">Reviewed by you · {{ c.reviewed|length }}</div>{% for p, it, k in c.reviewed %}{{ brow(c, p, it, 'reviewed', 'reviewed') }}{% endfor %}{% endif %}{% if c.reached %}<div class="subh">Reached later · {{ c.reached|length }}</div>{% for p, it in c.reached %}{{ strow(p, it, 'reached later') }}{% endfor %}{% endif %}{% else %}
        {% if c.disputes %}<div class="subh blue">Disputed by {{ fn }} · {{ c.disputes|length }}</div>{% for x in c.disputes %}<div class="fr" data-did="{{ x.id }}"><span class="dot w"></span><span class="t"><b>{{ x.call_h }}</b><span class="sub">{{ figw.get(x.fig, x.fig) }}</span><span class="dispute">{{ fn }}, {{ x.at[8:10] }}-{{ x.at[5:7] }} {{ x.at[11:16] }}: “{{ x.text }}”</span></span><span></span><span class="act"><button type="button" class="rb p" onclick="dAns(this,'accept')">Accept — take it off the count</button><button type="button" class="rb" onclick="dAns(this,'stands')">It stands</button></span></div>{% endfor %}{% endif %}
        {% if nb %}<div class="subh rose">Missed on duty, not called back · {{ nb }}{% if c.not_back_people != nb %} ({{ c.not_back_people }} patient{{ 's' if c.not_back_people != 1 else '' }}){% endif %}</div>{% for p, it in c.not_back %}{{ srow(c, p, it, 'nobody has called back', 'not_back') }}{% endfor %}{% endif %}
        {% if nl %}<div class="subh rose">Not logged — answered, no outcome filed · {{ nl }}</div>{% for p, it in c.not_logged %}{{ srow(c, p, it, (it.direction == 'In') and 'incoming, answered' or 'outgoing, answered', 'not_logged') }}{% endfor %}{% endif %}
        {% if mm %}<div class="subh amber">Staff ≠ AI — to check · {{ mm }}</div>{% for p, it in c.mismatch %}{{ srow(c, p, it, 'filed “' ~ (it.claimed_h or '—') ~ '” · the recording says “' ~ (it.ai_h or '—') ~ '”', 'mismatch') }}{% endfor %}{% endif %}
        {% if c.wa_in %}<div class="subh {{ 'amber' if c.wa_ans < c.wa_in else '' }}">WhatsApps on duty · {{ c.wa_in }} &#8594; {{ c.wa_ans }} answered</div>{% for p, w in c.wa_open %}{{ srow(c, p, w, 'not answered', 'wa') }}{% endfor %}{% for p, w, a in c.wa %}{% if a %}<div class="fr"><span class="dot g"></span><span class="t"><span class="c">{{ I.wa_in|safe }}</span> <span class="mono">{{ w.t_h }}</span> <b>{{ p.name or p.phone_h }}</b><span class="q">“{{ w.body[:90] }}”</span></span><span class="pillx green">answered</span><span></span></div>{% endif %}{% endfor %}{% endif %}
        <div class="subh">Logged and agreed with the AI · {{ c.agreed }}</div>
        {% if c.reviewed %}<details class="s rvd"><summary><span class="car" aria-hidden="true">&#9654;</span><span class="sl"><b>Reviewed by you</b> <span class="sub">off the “to check” count — Undo puts one back</span></span><span class="sr">{{ c.reviewed|length }}</span></summary>{% for p, it, k in c.reviewed %}{{ srow(c, p, it, figshort.get(k, k), 'reviewed') }}{% endfor %}</details>{% endif %}
        {% endif %}
      </details>
      {% else %}{% if d.staff is not none %}<div class="empty">No staff calls {{ 'today yet' if d.mode=='today' else 'in this window' }}.</div>{% endif %}{% endfor %}
    </div>
  </section>
  {% set k = d.ckb %}
  <section id="ckb">
    <h2><span class="l">Call ke baad — appointments booked on a call</span><span class="pill">last 7 days</span></h2>
    <div class="card">
      {% if not k.ok %}<div class="empty">The Call-ke-baad list could not be read just now.</div>{% else %}
      <div class="fuline"><b>{{ k.booked }} booked</b> on calls &#8594; <b class="g">{{ k.came }} came</b> · <b class="w">{{ k.due }} still awaited</b> · <b class="b">{{ k.noshow }} never came</b></div>
      {% if k.staff %}<div class="tw"><table class="mini"><thead><tr><th>Staff</th><th>Booked</th><th>Came</th><th>Awaited</th><th>Never</th></tr></thead><tbody>
        {% for who, s in k.staff %}<tr><td>{{ who }}</td><td>{{ s.booked }}</td><td>{{ s.came }}</td><td>{{ s.due }}</td><td>{{ s.noshow }}</td></tr>{% endfor %}
      </tbody></table></div>{% endif %}
      <details class="s {{ 'rose' if k.never else 'green' }}" id="ckb-never">
        <summary><span class="car" aria-hidden="true">&#9654;</span><span class="sl"><b>Never came</b> <span class="sub">booked for a day that has passed</span></span><span class="sr">{{ k.never|length }}</span></summary>
        {% for r in k.never %}<div class="fr rose"><span class="dot b"></span><span class="t"><b>{{ r.name or r.phone_h or 'no name' }}</b>{% if r.cid %} · {{ r.cid }}{% endif %}{% if not r.known %} <span class="unk">new</span>{% endif %} <span class="mono">{{ r.phone_h }}</span><span class="sub">booked {{ r.booked_h }}{% if r.appt_h %} · for {{ r.appt_h }}{% endif %} · {{ r.who }}</span></span><span class="pillx rose">Never came</span><span class="act">{% if r.phone %}<button type="button" class="btn" onclick="callBack('{{ r.phone }}',this)">Call</button>{% endif %}</span></div>
        {% else %}<div class="empty">None this week.</div>{% endfor %}
      </details>
      {% if not k.visits_ok %}<div class="note">The Docterz visits could not be read just now — some “came” may still show as awaited.</div>{% endif %}
      <div class="note">The whole list, with its buttons: <a href="/portal/ring/list">Call ke baad</a>.</div>
      {% endif %}
    </div>
  </section>
  </div>
  </div>

  <div class="cols">
  {% set wk = d.week %}
  <section id="unknown">
    <h2><span class="l">This week — unknown callers</span><span class="pill">{{ wk.from[8:]|int }} {{ wk.from|month }} – {{ wk.to[8:]|int }} {{ wk.to|month }}</span></h2>
    <div class="card"><div class="tw"><table>
      <thead><tr><th>Step</th><th>Callers</th></tr></thead>
      <tbody>
        <tr><td>Unknown numbers that rang</td><td>{{ wk.rang }}</td></tr>
        <tr><td>Reached by staff</td><td>{{ wk.reached }}</td></tr>
        <tr class="tot"><td>Booked an appointment</td><td>{{ wk.booked }}</td></tr>
      </tbody></table></div>
      <div class="note">Never reached this week: <b style="color:{{ 'var(--bad)' if wk.never else 'var(--good)' }}">{{ wk.never }} number{{ 's' if wk.never!=1 else '' }}</b>{% if wk.never %} · <a href="/portal/console?span=7#people" onclick="sessionStorage.setItem('cc_chip','unknown')">see them</a>{% endif %}</div>
    </div>
  </section>

  <section id="earlier">
    <h2><span class="l">Earlier days</span><span class="pill">one day, one row</span></h2>
    <div class="card">
      {% for e in d.earlier %}
      <details class="d"><summary onclick="location.href='/portal/console?day={{ e.day }}';return false;"><span class="car" aria-hidden="true">&#9654;</span><span><b class="n">{{ e.label }}</b><span class="sub">{{ e.calls }} call{{ 's' if e.calls!=1 else '' }} · {{ e.callers }} caller{{ 's' if e.callers!=1 else '' }} · unknown {{ e.unknown }}{% if e.unknown %} ({{ 'all reached' if not e.never else (e.never ~ ' never reached') }}){% endif %}</span></span><b class="r" style="color:{{ 'var(--good)' if not e.never else 'var(--bad)' }}">{{ 'clear' if not e.never else (e.never ~ ' never reached') }}</b></summary></details>
      {% else %}<div class="empty">No earlier days in the last week.</div>{% endfor %}
    </div>
  </section>
  </div>

  <div class="foot">Every section opens folded; a coloured line is one to open. Green = answered or all clear · amber = tried, late or to check · rose = nobody answered or needs action. Call counts count calls only. A WhatsApp is answered by a delivered reply, or by an answered call of 30 s or more within 2 clinic hours; a missed call is answered only by a call; templates and failed replies never count. One person, one timeline. The follow-up list keeps one open row per patient (the latest due date) and closes it by itself on a Docterz visit from half the advised period before the due date (when the advised period cannot be read: only on a visit on or after the due date), or when staff file “not coming”. In Grace and older a call counts only from the day after the due date. The recording plays in the player at the foot of the screen (pause, tap the bar to jump); the transcript opens under its row. Every patient carries the clinic ID. The reading runs 07:00–22:50; the page says “as of” outside those hours.
    <br>The older console (log · staff week · pipeline · no-shows with send-backs) is still at <a href="/portal/console/old">/portal/console/old</a>.</div>
</div>
<div class="pl" id="pl" role="region" aria-label="Recording player"><div class="plrow"><button type="button" class="plbtn" id="plbtn" onclick="plToggle()" aria-label="Play or pause">&#9654;</button><span class="pllab" id="pllab">Recording</span><span class="pltime" id="pltime">Loading…</span><button type="button" class="plx" onclick="plClose()" aria-label="Close the player">&times;</button></div><div class="plt" id="plt" onclick="plSeek(event)" title="Tap to jump"><div class="plf" id="plf"></div></div><div class="plmsg" id="plmsg"></div></div>
<div class="toast" id="toast"></div>
<script>
var _pa=null,_pb=null;
/* S703: the recording player -- the bar at the foot of the screen and the row's own button both show what is happening */
function _f(s){ if(!isFinite(s)||s<0) return '–:––'; s=Math.floor(s); return Math.floor(s/60)+':'+('0'+(s%60)).slice(-2); }
function _el(i){ return document.getElementById(i); }
function _plState(st,msg){
  var p=_el('pl'); p.classList.toggle('loading',st==='loading'); p.classList.toggle('err',st==='err');
  _el('plmsg').textContent=msg||''; p.style.display='block'; document.body.classList.add('plon');
  document.body.style.paddingBottom=(p.offsetHeight+24)+'px'; document.documentElement.style.setProperty('--plh',(p.offsetHeight+12)+'px');
  if(st==='loading'){ _el('pltime').textContent='Loading…'; }
  _el('plbtn').innerHTML=(st==='playing'||st==='loading')?'&#10074;&#10074;':'&#9654;';
}
function _btnRestore(b){
  if(!b) return; b.classList.remove('on','load','ps'); b.style.removeProperty('--pp');
  if(b.dataset.orig!==undefined){ b.innerHTML=b.dataset.orig; }
}
function _tick(){
  if(!_pa) return; var d=_pa.duration, t=_pa.currentTime, pct=(isFinite(d)&&d>0)?Math.min(100,t/d*100):0;
  _el('plf').style.width=pct+'%'; _el('pltime').textContent=_f(t)+' / '+_f(d);
  if(_pb){ _pb.style.setProperty('--pp',pct+'%'); _pb.innerHTML=(_pa.paused?'&#9654; ':'&#10074;&#10074; ')+_f(t)+' / '+_f(d); }
}
function _fail(a){
  if(a!==_pa) return;
  var b=_pb; _pa=null; _pb=null; try{ a.pause(); }catch(e){}
  _btnRestore(b);
  _plState('err','This recording could not be played — it is not on the server yet, or its link has expired. Try again later.');
  _el('pltime').textContent='';
}
function _label(b){
  var p=b.closest('details.p'), r=b.closest('.tl')||b.closest('.ny')||b.closest('tr')||b.closest('li')||b.parentNode, nm='', tm='';
  if(p){ var w=p.querySelector('summary .who b'); nm=w?w.textContent:''; }
  if(r){ var t=r.querySelector('.tm'); tm=(t&&t!==b)?t.textContent:''; if(!nm){ var bb=r.querySelector('b'); nm=bb?bb.textContent:''; } }
  if(!nm&&r){ var out=[], tw=document.createTreeWalker(r,NodeFilter.SHOW_TEXT,null), n;
    while((n=tw.nextNode())){ if(n.parentNode&&n.parentNode.closest('button,select,option,form,script')) continue; var s=n.nodeValue.trim(); if(s) out.push(s); }
    nm=out.join(' '); }
  var lab=[nm.replace(/\s+/g,' ').trim(), (tm||'').trim()].filter(Boolean).join(' · ');
  return 'Recording — '+(lab||'call').slice(0,80);
}
function playJk(jk,b){
  if(_pb===b&&_pa){ plToggle(); return; }
  plClose(true);
  var a=new Audio('/portal/rec/'+encodeURIComponent(jk)); a.preload='auto';
  _pa=a; _pb=b; if(b.dataset.orig===undefined) b.dataset.orig=b.innerHTML;
  b.classList.add('on','load');
  _el('pllab').textContent=_label(b); _el('plf').style.width='0';
  _plState('loading');
  function mine(fn){ return function(){ if(a===_pa) fn(); }; }
  a.addEventListener('waiting',mine(function(){ _plState('loading'); _pb&&_pb.classList.add('load'); }));
  a.addEventListener('playing',mine(function(){ _plState('playing'); _pb.classList.remove('load','ps'); _pb.classList.add('on'); _tick(); }));
  a.addEventListener('pause',mine(function(){ if(a.ended) return; _plState('paused'); _pb.classList.remove('on','load'); _pb.classList.add('ps'); _tick(); }));
  a.addEventListener('timeupdate',mine(_tick)); a.addEventListener('loadedmetadata',mine(_tick)); a.addEventListener('durationchange',mine(_tick));
  a.addEventListener('ended',mine(function(){ _tick(); _plState('paused'); _el('pltime').textContent='Finished · '+_f(a.duration);
    _el('plf').style.width='100%'; var b2=_pb; _btnRestore(b2); }));
  a.addEventListener('error',function(){ _fail(a); });
  var pr=a.play(); if(pr&&pr.catch) pr.catch(function(e){ if(a===_pa&&!(e&&e.name==='AbortError')) _fail(a); });
}
function plToggle(){
  var a=_pa; if(!a) return;
  if(a.paused||a.ended){ if(a.ended) a.currentTime=0; if(_pb){ _pb.classList.add('on'); }
    var pr=a.play(); if(pr&&pr.catch) pr.catch(function(e){ if(a===_pa&&!(e&&e.name==='AbortError')) _fail(a); }); }
  else { a.pause(); }
}
function plSeek(ev){
  var a=_pa; if(!a||!isFinite(a.duration)||a.duration<=0) return;
  var r=_el('plt').getBoundingClientRect(), x=(ev.clientX-r.left)/r.width;
  a.currentTime=Math.max(0,Math.min(1,x))*a.duration; _tick();
}
function plClose(keep){
  var a=_pa, b=_pb; _pa=null; _pb=null;
  if(a){ try{ a.pause(); a.removeAttribute('src'); a.load(); }catch(e){} }
  _btnRestore(b);
  if(!keep){ var p=_el('pl'); p.style.display='none'; p.className='pl'; document.body.style.paddingBottom=''; document.body.classList.remove('plon'); }
}
function wholeTx(a,jk){
  var box=a.parentNode; a.textContent='loading…';
  fetch('/portal/console/api/tx/'+jk,{credentials:'same-origin'}).then(function(r){return r.json();}).then(function(j){
    var f=document.createElement('span'); f.className='full'; f.textContent=j.text||'(no transcript)'; box.appendChild(f); a.remove();
  }).catch(function(){ a.textContent='whole transcript'; toast('The transcript could not be loaded.'); });
  return false;
}
function callBack(ph,b){
  if(!confirm('Call this number through the clinic line? Your phone rings first, then the patient is joined.')) return;
  b.disabled=true;
  fetch('/portal/console/api/call',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone10:ph})})
  .then(function(r){return r.json();}).then(function(j){ toast(j.msg||'done'); b.disabled=false; }).catch(function(){ toast('The call could not be placed.'); b.disabled=false; });
}
/* S747: your review buttons -- one POST each; the row then says what was done. Nothing is asked twice, no pop-up. */
function _rvSend(url,body,b,done){
  b.disabled=true;
  fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){ if((r.headers.get('Content-Type')||'').indexOf('json')<0) throw new Error('x'); return r.json(); })
  .then(function(j){ if(j.ok){ done(j); } else { b.disabled=false; } toast(j.msg||(j.ok?'Saved.':'Not saved.')); })
  .catch(function(){ b.disabled=false; toast('Not saved — the server did not answer. Try again.'); });
}
function rv(b,act){
  var r=b.closest('[data-ref]');
  _rvSend('/portal/console/api/review2',{ref:r.dataset.ref,staff:r.dataset.staff,act:act},b,function(){
    var w={ask_log:'Asked',reviewed:'Reviewed ✓',staff_right:'Staff right ✓',ai_right:'AI right ✓',undo:'Back to check'}[act]||'Saved';
    if(act!=='ask_log'){ r.querySelectorAll('.rb').forEach(function(x){ if(x!==b&&!x.classList.contains('nb')) x.disabled=true; }); }
    b.textContent=w; b.classList.add('done'); b.disabled=true;
  });
}
function rvOpen(b){ var r=b.closest('[data-ref]'), s=r.querySelector('.nbox'); s.hidden=false; s.querySelector('input').focus(); }
function rvNote(b){
  var r=b.closest('[data-ref]'), i=r.querySelector('.nbox input'), v=(i.value||'').trim();
  if(!v){ toast('Write the note first.'); return; }
  _rvSend('/portal/console/api/review2',{ref:r.dataset.ref,staff:r.dataset.staff,act:'note',note:v},b,function(){
    var s=document.createElement('span'); s.className='rvs'; s.textContent='Note sent: “'+v+'”';
    i.value=''; r.querySelector('.nbox').hidden=true; r.querySelector('.t').insertBefore(s,r.querySelector('.nbox')); b.disabled=false;
  });
}
function dAns(b,ans){
  var r=b.closest('[data-did]');
  _rvSend('/portal/console/api/dispute-answer',{id:+r.dataset.did,answer:ans},b,function(){
    r.querySelectorAll('.rb').forEach(function(x){ x.disabled=true; });
    b.textContent=(ans==='accept'?'Accepted — off the count':'It stands ✓'); b.classList.add('done');
  });
}
function toast(t){ var e=document.getElementById('toast'); e.textContent=t; e.style.display='block'; setTimeout(function(){e.style.display='none';},5000); }
function chip(b){
  var f=b.getAttribute('data-f');
  document.querySelectorAll('.chips button').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
  document.querySelectorAll('details.p').forEach(function(d){
    var show = f==='all' || (f==='awaiting' && d.dataset.state==='rose') || (f==='calls' && +d.dataset.calls>0) || (f==='wa' && +d.dataset.wa>0) || (f==='unknown' && d.dataset.unknown==='1');
    d.style.display = show?'':'none';
  });
  try{ sessionStorage.setItem('cc_chip',f); }catch(e){}
}
function expandAll(){ document.querySelectorAll('details').forEach(function(d){ d.open=true; }); }
function foldAll(){ document.querySelectorAll('details').forEach(function(d){ d.open=false; }); }
function openRow(id){ var d=document.getElementById(id); if(d){ d.open=true; d.scrollIntoView({behavior:'smooth',block:'start'}); } }
(function(){ try{ var f=sessionStorage.getItem('cc_chip'); if(f&&f!=='all'){ var b=document.querySelector('.chips button[data-f="'+f+'"]'); if(b) chip(b); } sessionStorage.removeItem('cc_chip'); }catch(e){} })();
</script>
</body></html>
"""

REVIEW_VOCAB = ["Coming", "Came", "Not coming", "Call again", "Wrong claim by staff", "Spam / marketing", "Other"]
_MON = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

_OLD_VIEWS = ("log", "threads", "staff", "leads", "pipe", "noshows")


def render(conn, args, now=None):
    span = (args.get("span") or "today").strip()
    day = (args.get("day") or "").strip()
    q = (args.get("q") or "").strip()[:60]
    d = page_data(conn, span=span, day=day, q=q, now=now, inbox_path=_cfg_path("PORTAL_INBOX_DB", INBOX_DB_DEFAULT),
                  fin_db=_cfg_path("FINANCE_DB_PATH", None), master_path=_cfg_path("SR_STAFF_MASTER", STAFF_MASTER_DEFAULT),
                  punch_path=_cfg_path("SR_PUNCH_CSV", PUNCH_CSV_DEFAULT))
    m = read_meta(d["now"])
    qs = {}
    if d["mode"] in ("yesterday", "7", "30"):
        qs["span"] = d["mode"]
    elif d["mode"] == "day":
        qs["day"] = d["to"]
    if q:
        qs["q"] = q
    self_url = "/portal/console" + (("?" + urlencode(qs)) if qs else "")
    ret_qs = urlencode(qs) if qs else "span=today"
    return render_template_string(PAGE, d=d, m=m, I=ICONS, words=item_words, vocab=REVIEW_VOCAB, rw=REVIEW_WORDS, figshort=FIG_SHORT, figw=FIG_WORDS,
                                  self_url=self_url, ret_qs=ret_qs, fu_max=FU_ROWS_MAX, fu_back=FU_BACK_DAYS, today_iso=d["now"].strftime("%Y-%m-%d"))


def _cfg_path(key, default):
    try:
        v = str((_CFG(key, default or "") if _CFG else (default or "")) or "").strip()
    except Exception:
        v = ""
    return v or default


def register(app, gate, who, cfg_get, helpers):
    """Called from portal.py. gate = doctor_required; who() = the login; helpers = the portal's console readers."""
    global _WHO, _CFG
    _H.update(helpers or {})
    _WHO, _CFG = who, cfg_get

    @app.template_filter("month")
    def _month(iso):
        try:
            return _MON[int(iso[5:7])]
        except Exception:
            return ""

    @app.route("/portal/console", endpoint="s698_calls_page")
    @gate
    def _page():
        view = (request.args.get("view") or "").strip()
        if view in _OLD_VIEWS or request.args.get("direction") or request.args.get("answered") or request.args.get("agent") or request.args.get("flag"):
            qs = request.query_string.decode("utf-8", "replace")
            return redirect("/portal/console/old" + (("?" + qs) if qs else ""))
        conn = _H["console_conn"]() if _H.get("console_conn") else None
        if conn is None:
            html = render_template_string(PAGE, d={"mode": "today", "to": "", "q": "", "people": [], "groups": [], "counts": strip_counts([], []),
                                                   "needs": [], "chips": {"all": 0, "awaiting": 0, "calls": 0, "wa": 0, "unknown": 0}, "no_number": 0,
                                                   "wa_ok": True, "fu": {"found": False, "bands": [], "came": [], "today": {}, "who": [], "open": 0, "removed": 0, "src": "", "visits_ok": True},
                                                   "ckb": {"ok": False}, "staff": [],
                                                   "week": {"from": "2026-01-01", "to": "2026-01-01", "rang": 0, "reached": 0, "booked": 0, "never": 0},
                                                   "earlier": [], "title_day": "Today"},
                                          m={"ok": False, "asof": "—", "stale": False, "next": ""}, I=ICONS, words=item_words,
                                          vocab=REVIEW_VOCAB, self_url="/portal/console", ret_qs="span=today", fu_max=FU_ROWS_MAX, today_iso="")
            return make_response(html, 200)
        try:
            html = render(conn, request.args)
        finally:
            conn.close()
        resp = make_response(html, 200)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/console/api/tx/<jk>", endpoint="s698_calls_tx")
    @gate
    def _tx(jk):
        if not _JK.match(jk or ""):
            abort(404)
        conn = _H["console_conn"]() if _H.get("console_conn") else None
        if conn is None:
            return jsonify({"text": ""}), 503
        try:
            r = conn.execute("SELECT text FROM transcripts WHERE join_key=? AND COALESCE(text,'')<>'' LIMIT 1", (jk,)).fetchone()
        finally:
            conn.close()
        resp = jsonify({"text": (r[0] if r else "")})
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/console/api/call", methods=["POST"], endpoint="s698_calls_call")
    @gate
    def _call():
        body = request.get_json(silent=True) or {}
        login = ""
        try:
            login = who() or ""
        except Exception:
            login = ""
        ok, msg, code = ivr_call(body.get("phone10"), login, env_path=(cfg_get("PORTAL_WA_ENV", WA_ENV_DEFAULT) if cfg_get else WA_ENV_DEFAULT),
                                 call_url=(cfg_get("RING_CALL_URL", CALL_URL_DEFAULT) if cfg_get else CALL_URL_DEFAULT))
        return jsonify({"ok": ok, "msg": msg}), code

    # ------------------------------------------------------------------ S747: the review buttons and each person's own card
    def _review_db():
        return _cfg_path("PORTAL_CALL_REVIEW_DB", REVIEW_DB_DEFAULT)

    def _jbody():
        b = request.get_json(silent=True)
        return b if isinstance(b, dict) else {}

    def _txt(v, n=300):
        return " ".join(str(v or "").split())[:n]

    @app.route("/portal/console/api/review2", methods=["POST"], endpoint="s747_review")
    @gate
    def _review2():
        b = _jbody()
        ref, staff_k, act = str(b.get("ref") or ""), str(b.get("staff") or ""), str(b.get("act") or "")
        note = _txt(b.get("note"))
        if not _REF.match(ref) or not re.match(r"^[a-z]{1,30}$", staff_k) or act not in REVIEW_ACTS:
            return jsonify({"ok": False, "msg": "That call could not be read — reload the page."}), 400
        if act == "note" and not note:
            return jsonify({"ok": False, "msg": "Write the note first."}), 400
        try:
            by = (who() or "") if who else ""
        except Exception:
            by = ""
        try:
            _rv_write(_review_db(), "INSERT INTO review (ref, staff, act, note, by_whom, at) VALUES (?,?,?,?,?,?)",
                      (ref, staff_k, act, note if act == "note" else "", by or "manoj", _stamp()))
        except sqlite3.Error:
            return jsonify({"ok": False, "msg": "Not saved — the review store could not be written. Try again."}), 503
        words = {"ask_log": "Asked — it is on their card until they log it.", "reviewed": "Marked reviewed.",
                 "staff_right": "Saved: staff right.", "ai_right": "Saved: AI right.", "undo": "Back on the 'to check' list.",
                 "note": "Note sent — it shows on their card."}
        return jsonify({"ok": True, "msg": words.get(act, "Saved.")})

    @app.route("/portal/console/api/dispute-answer", methods=["POST"], endpoint="s747_dispute_answer")
    @gate
    def _dispute_answer():
        b = _jbody()
        ans = str(b.get("answer") or "")
        try:
            did = int(b.get("id"))
        except Exception:
            did = 0
        if did <= 0 or ans not in ("accept", "stands"):
            return jsonify({"ok": False, "msg": "That dispute could not be read — reload the page."}), 400
        try:
            by = (who() or "") if who else ""
        except Exception:
            by = ""
        try:
            n = _rv_write(_review_db(), "UPDATE dispute SET answer=?, answer_note=?, answer_by=?, answer_at=? WHERE id=? AND answer=''",
                          (ans, _txt(b.get("note")), by or "manoj", _stamp(), did))
        except sqlite3.Error:
            return jsonify({"ok": False, "msg": "Not saved — the review store could not be written. Try again."}), 503
        if not n:
            return jsonify({"ok": False, "msg": "Already answered."}), 409
        return jsonify({"ok": True, "msg": "Accepted — the call is off their count." if ans == "accept" else "Saved: it stands."})

    def _card_resp(key, span):
        conn = _H["console_conn"]() if _H.get("console_conn") else None
        if conn is None:
            return jsonify({"ok": False, "error": "no_console"}), 503
        today = None
        try:
            c, handler, mode, made = card_for(conn, key, span)
            if made and c is not None and mode != "today":      # S762: 'aaj abhi tak' on the staff's folded line
                try:
                    ct, _h2, _m2, made2 = card_for(conn, key, "today", cached=True)
                    if made2:
                        today = {"net_missed": (ct or {}).get("net_missed", 0) if (ct is None or ct.get("missed_known")) else None}
                except Exception:
                    today = None
        finally:
            conn.close()
        if not made:
            return jsonify({"ok": False, "error": "cards"}), 503
        resp = jsonify({"ok": True, "span": mode, "handler": handler, "card": card_json(c) if c else None, "today": today})
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/console/api/card/<login>", endpoint="s747_card_as")
    @gate
    def _card_as(login):
        """The owner's ?as= view of one person's card (Aaj ka kaam), behind his own gate."""
        return _card_resp(login_key(login), (request.args.get("span") or "yesterday").strip())

    pm = sys.modules.get(getattr(gate, "__module__", "") or "")
    staff_gate = getattr(pm, "login_required", None) if pm is not None else None
    sso_user = getattr(pm, "_sso_user", None) if pm is not None else None
    serve_rec = getattr(pm, "_serve_rec", None) if pm is not None else None
    if callable(staff_gate) and callable(sso_user):
        def _me():
            try:
                u = sso_user(request) or {}
            except Exception:
                u = {}
            return str(u.get("user") or "").strip()

        @app.route("/portal/console/api/mycard", endpoint="s747_mycard")
        @staff_gate
        def _mycard():
            login = _me()
            if not login:
                return jsonify({"ok": False, "error": "not_signed_in"}), 401
            key = login_key(login)
            if not key or key in OWNER_FIRST:
                return jsonify({"ok": True, "span": "", "handler": False, "card": None})
            return _card_resp(key, (request.args.get("span") or "yesterday").strip())

        def _mine(key, ref, fig=None):
            """The row of one of THIS person's calls of the last 7 days (and behind `fig`, when given), or None."""
            conn = _H["console_conn"]() if _H.get("console_conn") else None
            if conn is None:
                return None
            try:
                c, _h, _m, _made = card_for(conn, key, "7", cached=True)
            finally:
                conn.close()
            if not c:
                return None
            r = next((x for x in card_json(c)["calls"] if x["ref"] == ref), None)
            if r is None or (fig and fig not in r["figs"]):
                return None
            return r

        @app.route("/portal/console/api/myrec/<jk>", endpoint="s747_myrec")
        @staff_gate
        def _myrec(jk):
            """The recording of one of THIS person's calls of the last 7 days, through the portal's own recording server
            (local copy first, else Drive). Anyone else's call: 403. Staff get recordings, never transcripts."""
            login = _me()
            key = login_key(login)
            if not _JK.match(jk or "") or not key or key in OWNER_FIRST or not callable(serve_rec):
                abort(404)
            r = _mine(key, jk)
            if r is None or not r.get("has_rec"):
                abort(403)
            return serve_rec(jk)

        @app.route("/portal/console/api/dispute", methods=["POST"], endpoint="s747_dispute")
        @staff_gate
        def _dispute():
            login = _me()
            key = login_key(login)
            b = _jbody()
            ref, fig, text = str(b.get("ref") or ""), str(b.get("fig") or ""), _txt(b.get("text"))
            if not login or not key or key in OWNER_FIRST:
                return jsonify({"ok": False, "msg": "Pehle Clinic app par login kijiye."}), 401
            if not _REF.match(ref) or fig not in FIGS or not text:
                return jsonify({"ok": False, "msg": "Call chuniye aur likhiye kya galat hai."}), 400
            r = _mine(key, ref, fig)
            if r is None:
                return jsonify({"ok": False, "msg": "Yeh call aapki ginti mein nahin mila — page dobara kholiye."}), 409
            try:
                st, ds, ok = rv_read(_review_db())
            except Exception:
                ds, ok = [], False
            if any(x.get("ref") == ref and x.get("staff") == key and not x.get("answer") for x in ds):
                return jsonify({"ok": False, "msg": "Is call ke baare mein pehle hi bhej diya hai — jawab ka intezaar."}), 409
            call_h = " · ".join(x for x in ((r["day"][8:10] + "-" + r["day"][5:7] + " " + r["t"]) if r["day"] else r["t"],
                                            r["name"], r["cid"], fmt_num(r["phone"])) if x)
            try:
                _rv_write(_review_db(), "INSERT INTO dispute (ref, staff, fig, text, call_h, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                          (ref, key, fig, text, call_h, login, _stamp()))
            except sqlite3.Error:
                return jsonify({"ok": False, "msg": "Nahin gaya. Dobara kijiye."}), 503
            return jsonify({"ok": True, "msg": "Doctor sahab ko bhej diya."})

    return True
