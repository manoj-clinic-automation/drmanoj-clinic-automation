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
import time
import urllib.request
import urllib.error
from urllib.parse import urlencode

from flask import request, redirect, make_response, render_template_string, jsonify, abort

KIT = "S742_CALLS_R3"
VERSION = "S742 1.0"
INBOX_DB_DEFAULT = "/root/wa/wa_inbox/inbox.db"
WA_CALL_MIN_S = 30          # D820: an answered call of 30 s or more ...
WA_CALL_WITHIN_H = 2.0      # ... within 2 clinic hours answers a WhatsApp
FU_ROWS_MAX = 80            # rows drawn per follow-up section (the count is always the whole)
FU_BANDS = (("today", "Today’s follow-ups", "due today"), ("grace", "Grace period", "1–3 days late"),
            ("overdue", "Overdue", "4–14 days late"), ("lapsed", "Lapsed", "15+ days late"))
NOT_COMING = ("not_coming", "k_not_coming")
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
}

_H = {}            # helpers handed in by portal.py (console_conn, console_meta, reviews_maps, spam_phones)
_WHO = None
_CFG = None


# ---------------------------------------------------------------------------------------------- small helpers
def now_ist(now=None):
    return now if now is not None else _dt.datetime.now(IST).replace(tzinfo=None)


def en_out(code):
    c = (code or "").strip().lower()
    return EN_OUTCOME.get(c, (code or "").strip())


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
        "mismatch": (verdict == "Mismatch"), "not_filed": (answered == 1 and not claimed and bool(jk)),
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


def fu_row_state(r, tries, visit, today):
    """Where one follow-up stands, from what happened since its due date. Pure.
    closed: came (a Docterz visit on or after the due date) . notcoming (staff filed "not coming") . else open."""
    calls = [t for t in tries if t.get("ch") != "wa"]
    wa = [t for t in tries if t.get("ch") == "wa"]
    out_calls = [t for t in calls if t["direction"] == "Out"]
    ans = [t for t in calls if t["answered"]]
    nc = next((t for t in calls if (t.get("claimed") or "").strip().lower() in NOT_COMING), None)
    r["called"] = bool(out_calls)
    r["reached"] = bool(ans)
    r["closed"], r["closed_day"] = "", None
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
    elif not tries:
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
    r.update({"pill": pill, "tone": tone, "quote": quote, "tries": tries[-4:], "n_tries": len(tries),
              "play": next((t for t in reversed(calls) if t["jk"] and t["has_rec"]), None)})
    return r


def followup_list(conn, now, fin_db=None, inbox_path=None):
    """The cleaned follow-up list, every section with its counts. Read-only. Never raises."""
    today = now.date()
    out = {"found": False, "src": "", "bands": [], "came": [], "today": {}, "who": [], "visits_ok": False,
           "removed": 0, "open": 0, "wa_ok": True}
    try:
        raw, src, found = _fu_source(conn)
        out["src"], out["found"] = src, (bool(raw) if found is None else found)     # the builder's word wins when it gave one
        rows, out["removed"] = fu_clean(raw, today)
        if not rows:
            out["bands"] = [(k, t, s, [], 0, 0, 0, "green") for k, t, s in FU_BANDS]
            return out
        pats = {}
        try:
            for r in conn.execute(_PAT_SQL):
                pats[r[0]] = r
        except Exception:
            pats = {}
        lo = max(min(r["dd"] for r in rows), today - _dt.timedelta(days=60))
        phones = {r["phone"] for r in rows if r["phone"]}
        has_ca = _table_exists(conn, "call_agent")
        sql = _CALLS_SQL if has_ca else _CALLS_SQL.replace(
            "LEFT JOIN call_agent ca ON ca.join_key=c.join_key AND c.join_key<>''",
            "LEFT JOIN (SELECT '' AS join_key, '' AS agent WHERE 0) ca ON 0")
        by = {}
        for row in conn.execute(sql, (lo.isoformat(), today.isoformat())):
            it = call_item(row, pats, now)
            if it["phone"] in phones:
                by.setdefault(it["phone"], []).append(it)
        wa, out["wa_ok"] = wa_items(inbox_path, lo.isoformat(), today.isoformat(), phones)
        for w in wa:
            by.setdefault(w["phone"], []).append(w)
        for v in by.values():
            v.sort(key=lambda x: (x["t"] or _dt.datetime.min, str(x["id"])))
        try:
            R = _ro()
            visits = R.visits_since(lo.isoformat(), today, fin_db)
        except Exception:
            R, visits = None, {"ok": False, "by_id": {}, "by_fp": {}}
        out["visits_ok"] = bool(visits.get("ok"))
        bands = {k: [] for k, _t, _s in FU_BANDS}
        who, fps = {}, {}
        for r in rows:
            p = pats.get(r["phone"]) if r["phone"] else None
            r["cid"] = ((p[5] or "").strip() if p else "")
            r["name"] = r["name"] or ((p[1] or "").strip() if p else "")
            r["dx"] = r["dx"] or ((p[2] or "").strip() if p else "")
            r["phone_h"] = fmt_num(r["phone"])
            r["due_h"] = r["dd"].strftime("%-d %b")
            r["age"] = (today - r["dd"]).days
            tries = [t for t in by.get(r["phone"], []) if t["day"] and t["day"] >= r["due"]] if r["phone"] else []
            visit = None
            if visits.get("ok"):
                ds = list(visits["by_id"].get(r["cid"], ())) if r["cid"] else []
                if r["phone"] and R is not None:
                    if r["phone"] not in fps:
                        try:
                            fps[r["phone"]] = R._mobile_fp(r["phone"])
                        except Exception:
                            fps[r["phone"]] = ""
                    fp = fps[r["phone"]]
                    if fp:
                        ds += [d for d, _c in visits["by_fp"].get(fp, ())]
                    else:
                        out["visits_ok"] = False     # the fingerprint could not be made: said on the page, as the list does
                ds = [d for d in ds if d >= r["dd"]]
                visit = min(ds) if ds else None
            fu_row_state(r, tries, visit, today)
            for t in tries:
                if t.get("ch") != "wa" and t["direction"] == "Out" and t["day"] == today.isoformat():
                    who.setdefault(t["agent_h"] or "staff", set()).add(r["phone"])
            if r["closed"]:
                if r["closed_day"] and r["closed_day"] >= today - _dt.timedelta(days=6):
                    out["came"].append(r)
                continue
            bands[fu_band(r["age"])].append(r)
        order = {"rose": 0, "amber": 1, "green": 2, "grey": 3}
        for k, title, sub in FU_BANDS:
            lst = sorted(bands[k], key=lambda x: (order.get(x["tone"], 9), x["dd"], x["name"]))
            n, called = len(lst), sum(1 for x in lst if x["called"])
            reached = sum(1 for x in lst if x["reached"])
            tone = "green" if called == n else ("rose" if k == "lapsed" else "amber")
            out["bands"].append((k, title, sub, lst, n, called, reached, tone))
            out["open"] += n
        out["came"].sort(key=lambda x: (x["closed_day"] or today), reverse=True)
        t_open = bands["today"]
        t_came = [x for x in out["came"] if x["dd"] == today]
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


def page_data(conn, span="today", day="", q="", now=None, inbox_path=None, fin_db=None):
    """Everything the page shows, in one dict. Pure over the connections (console.db; the inbox and finance.db
    are opened read-only by their own readers)."""
    now = now_ist(now)
    d_from, d_to, mode = span_bounds(span, day, now)
    wa, wa_ok = wa_items(inbox_path, d_from, d_to)
    people, items, no_number = build_people(conn, d_from, d_to, now, q=q, wa=wa)
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
{% macro furow(r) %}<div class="fr {{ r.tone }}"><span class="dot {{ {'green':'g','amber':'w','rose':'b'}.get(r.tone,'') }}"></span>
  <span class="t"><b>{{ r.name or r.phone_h or 'no name' }}</b>{% if r.cid %} · {{ r.cid }}{% endif %}{% if r.phone %} <span class="mono">{{ r.phone_h }}</span>{% else %} <span class="unk">no mobile</span>{% endif %}{% if r.dx %} · {{ r.dx }}{% endif %}
    <span class="sub">due {{ r.due_h }}{% if r.age > 0 %} ({{ r.age }} day{{ 's' if r.age!=1 else '' }} ago){% endif %}{% if r.tries %} · <span class="chain">{% for t in r.tries %}{% if not loop.first %}<span class="arr">&#8594;</span>{% endif %}<span class="c">{{ I[t.kind]|safe }}<span>{% if t.day != today_iso %}{{ t.day[8:] }}/{{ t.day[5:7] }} {% endif %}{{ t.t_h }}</span></span>{% endfor %}{% set lt = r.tries[-1] %}{% if lt.agent_h %} <span class="tail">{{ lt.agent_h }}</span>{% endif %}</span>{% endif %}{% if r.section and r.section|lower not in ('follow-up','due today','grace period') %} · {{ r.section }}{% endif %}</span>
    {% if r.quote %}<span class="q">{{ r.quote }}</span>{% endif %}</span>
  <span class="pillx {{ r.tone }}">{{ r.pill }}</span>
  <span class="act">{% if r.play %}<button type="button" class="play" data-jk="{{ r.play.jk }}" onclick="playJk('{{ r.play.jk }}',this)">&#9654; {{ r.play.dur_h or 'play' }}</button>{% endif %}{% if r.phone and not r.closed %}<button type="button" class="btn" onclick="callBack('{{ r.phone }}',this)">Call</button>{% endif %}</span>
</div>
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
      <div class="fuline">Today: <b>{{ fu.today.due }} due</b> · {{ fu.today.called }} called · {{ fu.today.reached }} reached · <b class="g">{{ fu.today.came }} came</b>{% if fu.who %} &nbsp;·&nbsp; Who called: {% for w, n in fu.who %}<b>{{ w }} {{ n }}</b>{{ ', ' if not loop.last else '' }}{% endfor %}{% endif %}</div>
      {% if fu.src=='no_shows' %}<div class="note">Showing the older list (due before today) until the next reading brings the whole feed — today's follow-ups appear within ten minutes.</div>{% endif %}
      {% if not fu.visits_ok %}<div class="note">The Docterz visits could not be read in full just now — some patients who came may still show as open.</div>{% endif %}
      {% for key, title, sub, rows, n, called, reached, tone in fu.bands %}
      <details class="s {{ tone }}" id="fu-{{ key }}">
        <summary><span class="car" aria-hidden="true">&#9654;</span><span class="sl"><b>{{ title }}</b> <span class="sub">{{ sub }}</span></span><span class="sr">called {{ called }} of {{ n }}{% if reached %} · reached {{ reached }}{% endif %}</span></summary>
        {% for r in rows[:fu_max] %}{{ furow(r) }}{% endfor %}
        {% if n > fu_max %}<div class="note">… and {{ n - fu_max }} more in this section (the not-called first are shown).</div>{% endif %}
        {% if not rows %}<div class="empty">None.</div>{% endif %}
      </details>
      {% endfor %}
      <details class="s green" id="fu-came">
        <summary><span class="car" aria-hidden="true">&#9654;</span><span class="sl"><b>Came / closed</b> <span class="sub">the last 7 days — a Docterz visit, or “not coming” filed</span></span><span class="sr">{{ fu.came|length }}</span></summary>
        {% for r in fu.came[:fu_max] %}{{ furow(r) }}{% endfor %}
        {% if not fu.came %}<div class="empty">None this week.</div>{% endif %}
      </details>
      {% endif %}
      <div class="note">The WhatsApp batch send by section is still at <a href="/portal/wa/followups">Follow-up WhatsApps (batch)</a>.</div>
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

  <div class="foot">Every section opens folded; a coloured line is one to open. Green = answered or all clear · amber = tried, late or to check · rose = nobody answered or needs action. Call counts count calls only. A WhatsApp is answered by a delivered reply, or by an answered call of 30 s or more within 2 clinic hours; a missed call is answered only by a call; templates and failed replies never count. One person, one timeline. The follow-up list keeps one open row per patient (the latest due date) and closes it by itself on a Docterz visit on or after the due date, or when staff file “not coming”. The recording plays in the player at the foot of the screen (pause, tap the bar to jump); the transcript opens under its row. Every patient carries the clinic ID. The reading runs 07:00–22:50; the page says “as of” outside those hours.
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
                  fin_db=_cfg_path("FINANCE_DB_PATH", None))
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
    return render_template_string(PAGE, d=d, m=m, I=ICONS, words=item_words, vocab=REVIEW_VOCAB,
                                  self_url=self_url, ret_qs=ret_qs, fu_max=FU_ROWS_MAX, today_iso=d["now"].strftime("%Y-%m-%d"))


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
                                                   "ckb": {"ok": False},
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

    return True
