#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phone_check.py -- kit S909_PHONE_DAILY_CHECK (20-Nov-2026, Sanjeevni session 494; D1026, the owner's "GO" 19:37 and "OK" 20:43 IST).

THE DAILY DELIVERY CHECK OF THE RECEPTION PHONE.
Every morning (setting phone_check.hhmm, 10:00 IST) the server queues ONE check message of its own kind ('check') on the reception
phone's road (supplier_msg). The phone sends it by WhatsApp to the clinic's own WhatsApp number (MyOperator; setting phone_check.to,
saved by the owner on his Reception phone card, never printed beyond its last four). The message carries a random code. The server
then looks for that code where the clinic's WhatsApp receiver writes every message it is given (/root/wa/wa_logs/<day>.jsonl) and
in the inbox store (/root/wa/wa_inbox/inbox.db) -- both READ ONLY.

Not there within phone_check.wait_min (20) minutes -> the step that failed is found and acted on:
  * the phone never collected the message  -> nothing on the server can mend a phone: FAILED (when it last asked the server);
  * the phone collected it, no 'sent' report -> queued ONCE more with a fresh code; the second miss: FAILED;
  * reported sent, not in the clinic inbox   -> the clinic doctor runs (/root/deploy/clinic_doctor.py, the parent's, run as it is,
                                                never changed: it restarts only a part that is not answering), then ONE fresh
                                                message; the second miss: FAILED (past the server: MyOperator, or the number).
Every result that is not a plain pass reaches the owner twice: a line in owner_notice (his clinic-app notification, delivered by
owner_notice's own five-minute tick and its switches) and a Needs-you line (supplier_msg.needs_you_lines -> the Hub). A plain pass is quiet.

What it never does: retry a check message (the phone's door never hands kind 'check' twice -- supplier_msg), put a check message on the
stuck list or the silent-phone line, write to the inbox store or the receiver's files, print a number, a code's message body or a key.
Switches: /root/finance/_off/ALL_OFF or /root/finance/_off/PHONE_CHECK_OFF (a file), or the setting phone_check.on = off.
CLI:  phone_check.py tick      the five-minute pass (cron, # S909_PHONE_CHECK)
      phone_check.py status    one line, masked
Stdlib only; Python 3.6+.
"""
import datetime as dt
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys

KIT = "S909_PHONE_DAILY_CHECK"
VERSION = "S909 1.0"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
LIVE_DB = os.environ.get("PHONE_CHECK_DB", "/root/finance/finance.db")
OFF_DIR = os.environ.get("FINANCE_OFF_DIR", "/root/finance/_off")
RAW_DIR = os.environ.get("PHONE_CHECK_RAW_DIR", "/root/wa/wa_logs")
INBOX_DB = os.environ.get("PHONE_CHECK_INBOX_DB", "/root/wa/wa_inbox/inbox.db")
DOCTOR = os.environ.get("PHONE_CHECK_DOCTOR", "/root/deploy/clinic_doctor.py")
DOCTOR_PY = os.environ.get("PHONE_CHECK_DOCTOR_PY", "/usr/bin/python3")
DOCTOR_STATUS = os.environ.get("PHONE_CHECK_DOCTOR_STATUS", "/root/deploy/clinic_doctor_status.json")
LOCK_FILE = os.environ.get("PHONE_CHECK_LOCK", "/tmp/phone_check.lock")
CARD = "/finance/porders?old=1#s454phone"
START_WINDOW_H = 3                       # a scheduled check starts only within 3 h of its time (a box that was down does not start at night)
NOT_ASKED_WAIT_MIN = 120                 # a phone that has not asked the server at all since the message was queued: waited for up to 2 h
MAX_RUN_H = 6                            # a run older than this ends: FAILED if the phone took a message, else closed quietly

SETTINGS = (
    ("phone_check.on", "on", "S909: the reception phone's daily delivery check (on / off)"),
    ("phone_check.to", "", "S909: the clinic's own WhatsApp (MyOperator) number the check message goes to -- saved on the owner's card, never printed in full"),
    ("phone_check.hhmm", "10:00", "S909: when the daily check message is queued (IST, every day)"),
    ("phone_check.wait_min", "20", "S909: minutes a check message has to reach the clinic inbox"),
)
SCHEMA = (
    "CREATE TABLE IF NOT EXISTS phone_check_run (id INTEGER PRIMARY KEY, day TEXT NOT NULL, manual INTEGER NOT NULL DEFAULT 0, "
    " started_at TEXT NOT NULL, started_by TEXT, result TEXT, step TEXT, text TEXT, decided_at TEXT, doctor TEXT)",
    "CREATE UNIQUE INDEX IF NOT EXISTS phone_check_run_day ON phone_check_run(day) WHERE manual=0",
    "CREATE TABLE IF NOT EXISTS phone_check_try (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL, attempt INTEGER NOT NULL, "
    " code TEXT NOT NULL UNIQUE, msg_id INTEGER, queued_at TEXT NOT NULL, step TEXT, found_at TEXT, found_in TEXT, "
    " UNIQUE (run_id, attempt))",
)
RESULT_WORD = {"pass": "passed", "fixed": "fixed itself", "fail": "FAILED", "stopped": "stopped"}


# ------------------------------------------------------------------ small helpers
def now_local():
    """supplier_msg's own clock (naive, the box's local time) -- every comparison with its rows uses this."""
    return dt.datetime.now().replace(microsecond=0)


def now_ist():
    return dt.datetime.now(IST).replace(microsecond=0)


def iso(d):
    return d.replace(microsecond=0).isoformat()


def parse(s):
    try:
        return dt.datetime.fromisoformat(str(s)[:19])
    except (TypeError, ValueError):
        return None


def hhmm(s):
    d = parse(s)
    return d.strftime("%H:%M") if d else "?"


def ddmm_hhmm(s):
    d = parse(s)
    return d.strftime("%d-%m %H:%M") if d else "never"


def mask(d):
    d = re.sub(r"\D", "", str(d or ""))
    return ("•" * max(0, len(d) - 4) + d[-4:]) if d else ""


def digits(raw):
    """'98xxxxxxxx' / '+91 98xxx xxxxx' / '9198xxxxxxxx' -> '9198xxxxxxxx'; anything else ''."""
    d = re.sub(r"\D", "", str(raw or ""))
    if len(d) == 11 and d.startswith("0"):
        d = d[1:]
    if len(d) == 10 and d[0] != "0":
        return "91" + d
    if len(d) == 12 and d.startswith("91") and d[2] != "0":
        return d
    return ""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def setting(con, key):
    default = next((v for k, v, _n in SETTINGS if k == key), "")
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        return default
    return default if r is None or r[0] is None else str(r[0])


def ensure(con):
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for s in SCHEMA:
        con.execute(s)
    for k, v, note in SETTINGS:
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    con.commit()


def _off(con):
    for name in ("ALL_OFF", "PHONE_CHECK_OFF"):
        p = os.path.join(OFF_DIR, name)
        if os.path.exists(p):
            return name
    if setting(con, "phone_check.on").strip().lower() != "on":
        return "phone_check.on"
    return ""


def _int(con, key, default):
    try:
        return max(1, int(str(setting(con, key)).strip()))
    except (TypeError, ValueError):
        return default


def _start_time(con):
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", setting(con, "phone_check.hhmm"))
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        return 10, 0
    return int(m.group(1)), int(m.group(2))


# ------------------------------------------------------------------ the message on the phone's road
def _new_code(con):
    for _ in range(20):
        c = "JC-" + "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        if not con.execute("SELECT 1 FROM phone_check_try WHERE code=?", (c,)).fetchone():
            return c
    raise RuntimeError("no free code")


def body_for(code):
    return "Sanjeevni roz ki jaanch %s\nYeh automatic hai - jawab ki zaroorat nahin." % code


def _queue(con, run_id, attempt, to):
    """One message of kind 'check' (month 'check'); returns the try row's id. supplier_msg's table, its own columns only."""
    code = _new_code(con)
    t = now_local()
    cur = con.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, to_number, body, status, queued_at) "
                      "VALUES ('check','CHECK','Daily phone check','check',?,?,?,'queued',?)",
                      (int(run_id) * 10 + int(attempt), to, body_for(code), iso(t)))
    con.execute("INSERT INTO phone_check_try (run_id, attempt, code, msg_id, queued_at) VALUES (?,?,?,?,?)",
                (run_id, attempt, code, cur.lastrowid, iso(t)))
    return cur.lastrowid


def _skip(con, msg_id, why):
    con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE id=? AND kind='check' AND status IN ('queued','failed')",
                (("phone_check: %s" % why)[:200], int(msg_id)))


def start_run(con, manual=False, who=None):
    """(ok, run id or the reason). A scheduled run: one a day. A manual one: whenever none is running."""
    ensure(con)
    to = digits(setting(con, "phone_check.to"))
    if not to:
        return False, "Save the clinic's WhatsApp number first."
    con.commit()
    con.execute("BEGIN IMMEDIATE")                             # cold review S909 #9: Check now and the 10:00 start never make two runs
    try:
        if con.execute("SELECT 1 FROM phone_check_run WHERE result IS NULL").fetchone():
            con.rollback()
            return False, "A check is already running."
        day = now_ist().date().isoformat()
        try:
            cur = con.execute("INSERT INTO phone_check_run (day, manual, started_at, started_by) VALUES (?,?,?,?)",
                              (day, 1 if manual else 0, iso(now_local()), (str(who)[:40] if who else "server")))
        except sqlite3.IntegrityError:
            con.rollback()
            return False, "Today's check has already run."
        rid = cur.lastrowid
        _queue(con, rid, 1, to)
        con.commit()
    except Exception:
        con.rollback()
        raise
    return True, rid


# ------------------------------------------------------------------ where the message is looked for (read only)
def _raw_names(t_ist):
    days = {t_ist.date(), (t_ist - dt.timedelta(days=1)).date(), now_local().date(), (now_local() - dt.timedelta(days=1)).date()}
    return [os.path.join(RAW_DIR, "%s.jsonl" % d.isoformat()) for d in sorted(days)]


def found(code, t_ist=None):
    """'receiver' / 'inbox' when the code reached the clinic's WhatsApp, else ''. Reads only."""
    t_ist = t_ist or now_ist()
    b = code.encode("ascii")
    for p in _raw_names(t_ist):
        try:
            with open(p, "rb") as fh:
                if b in fh.read():
                    return "receiver"
        except OSError:
            continue
    try:
        c = sqlite3.connect("file:%s?mode=ro" % INBOX_DB, uri=True, timeout=10)
        try:
            if c.execute("SELECT 1 FROM msgs WHERE body LIKE ? LIMIT 1", ("%" + code + "%",)).fetchone():
                return "inbox"
        finally:
            c.close()
    except sqlite3.Error:
        pass
    return ""


def _msg(con, msg_id):
    r = con.execute("SELECT status, handed_at, sent_at, last_error FROM supplier_msg WHERE id=?", (int(msg_id),)).fetchone()
    return dict(status=r[0], handed_at=r[1], sent_at=r[2], error=r[3]) if r else None


def _phone_last(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='supplier_msg.phone_last'").fetchone()
        return str(r[0]).partition(" ")[0] if r and r[0] else ""
    except sqlite3.Error:
        return ""


# ------------------------------------------------------------------ the clinic doctor (the parent's; run as it is)
def run_doctor():
    """-> (verdict, words). Never raises. The doctor runs in ITS OWN AUTOMATIC MODE (--auto): its switch, an install's lock, its
    one-restart-per-hour cap and its boot grace all hold; a busy doctor (its own five-minute round) is said, not waited for; its
    status file is taken only when written by this run (cold review S909 #1)."""
    if os.environ.get("PHONE_CHECK_DOCTOR_STUB"):
        try:
            v = json.load(open(os.environ["PHONE_CHECK_DOCTOR_STUB"], encoding="utf-8"))
            return v.get("verdict", "ALL GOOD"), v.get("words", "stub")
        except (OSError, ValueError):
            return "UNKNOWN", "the doctor's stub could not be read"
    if not os.path.exists(DOCTOR):
        return "UNKNOWN", "the clinic doctor is not on this server"
    t0 = int(dt.datetime.now().timestamp()) - 1
    try:
        p = subprocess.run([DOCTOR_PY, DOCTOR, "--auto"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        return "UNKNOWN", "the clinic doctor did not finish in 4 minutes"
    except OSError as e:
        return "UNKNOWN", "the clinic doctor could not start (%s)" % e.__class__.__name__
    if rc == 3:
        return "BUSY", "the clinic doctor was already running (its own five-minute round)"
    try:
        st = json.load(open(DOCTOR_STATUS, encoding="utf-8"))
    except (OSError, ValueError):
        return ("NOT FIXED" if rc == 1 else "SKIPPED"), "its report could not be read"
    try:
        fresh = int(st.get("epoch") or 0) >= t0
    except (TypeError, ValueError):
        fresh = False
    if not fresh:
        return "SKIPPED", "the clinic doctor stood aside (switched off, an install running, or the server just started)"
    v = str(st.get("verdict") or "UNKNOWN")
    if v == "FIXED":
        return v, "it restarted %s" % (", ".join(st.get("restarted") or []) or "a part")
    if v == "NOT FIXED":
        return v, "still not working: %s" % (", ".join(st.get("still_bad") or []) or "a part")
    return v, "every part of the server answers"


# ------------------------------------------------------------------ the owner's two places
def _notify(con, run_id, result, text):
    """owner_notice's own table; its five-minute tick delivers it (clinic app, else ntfy) under its own switches."""
    try:
        import owner_notice as ON                                  # noqa: PLC0415
        ON.ensure(con)
        title = "Phone check: fixed itself" if result == "fixed" else "Phone check FAILED"
        con.execute("INSERT OR IGNORE INTO owner_notice (key, kind, title, body, made_at) VALUES (?,?,?,?,?)",
                    ("phonecheck:%d:%s" % (int(run_id), result), "phone_check", title, text, ON.stamp(ON.now_ist())))
        con.commit()
        return True
    except Exception:                                              # noqa: BLE001 -- the Needs-you line still stands
        try:
            con.rollback()
        except sqlite3.Error:
            pass
        return False


def _decide(con, run, result, step, text, doctor=None):
    """-> False only when a notice was due and could not be written (said in the tick's log line)."""
    con.execute("UPDATE phone_check_run SET result=?, step=?, text=?, decided_at=?, doctor=COALESCE(?, doctor) WHERE id=? AND result IS NULL",
                (result, step, text, iso(now_local()), doctor, run["id"]))
    con.commit()
    if result in ("fixed", "fail"):
        return _notify(con, run["id"], result, text)
    return True


def _close_quiet(con, run, result, step, text):
    """A run ended without a verdict for the owner (switched off; too old): its check messages withdrawn, no notice."""
    for t in _tries(con, run["id"]):
        _skip(con, t["msg_id"], text)
    _decide(con, run, result, step, text)


# ------------------------------------------------------------------ the five-minute pass
def _active(con):
    r = con.execute("SELECT id, day, manual, started_at, doctor FROM phone_check_run WHERE result IS NULL ORDER BY id DESC LIMIT 1").fetchone()
    return dict(id=r[0], day=r[1], manual=r[2], started_at=r[3], doctor=r[4]) if r else None


def _tries(con, run_id):
    return [dict(id=r[0], attempt=r[1], code=r[2], msg_id=r[3], queued_at=r[4], step=r[5])
            for r in con.execute("SELECT id, attempt, code, msg_id, queued_at, step FROM phone_check_try WHERE run_id=? ORDER BY attempt", (run_id,))]


def step(con, now=None):
    """One look at the running check. Returns what it did, in words for the log (never a number or a code)."""
    run = _active(con)
    if not run:
        return "idle"
    tries = _tries(con, run["id"])
    if not tries:
        _decide(con, run, "fail", "no_message", "Today's phone check could not queue its message.")
        return "decided fail (no message)"
    t_ist = now or now_ist()
    for t in tries:                                                # any of its messages arrived -> the check holds
        where = found(t["code"], t_ist)
        if where:
            con.execute("UPDATE phone_check_try SET found_at=?, found_in=? WHERE id=?", (iso(now_local()), where, t["id"]))
            for o in tries:
                if o["id"] != t["id"]:
                    _skip(con, o["msg_id"], "the check passed on another message")
            con.commit()
            if len(tries) == 1:
                _decide(con, run, "pass", "arrived", "Arrived in the clinic inbox at %s." % hhmm(iso(now_local())))
                return "decided pass"
            first_step = tries[0]["step"] or ""
            if t["attempt"] == 1:
                text = ("Today's first check message reached the clinic inbox late (seen at %s), after a second one had been queued. "
                        "Nothing to do." % hhmm(iso(now_local())))
            elif first_step == "no_report":
                text = ("The reception phone took today's check message but did not report it sent. The server queued it once more and it "
                        "reached the clinic inbox at %s. Nothing to do." % hhmm(iso(now_local())))
            elif first_step == "not_in_inbox":
                text = ("Today's check message left the reception phone but did not reach the clinic inbox. The clinic doctor ran (%s) and "
                        "a fresh message reached the inbox at %s. Nothing to do." % (run.get("doctor") or "?", hhmm(iso(now_local()))))
            else:
                text = "Today's check message reached the clinic inbox at %s, late. Nothing to do." % hhmm(iso(now_local()))
            _decide(con, run, "fixed", "arrived_" + str(t["attempt"]), text)
            return "decided fixed"
    started = parse(run["started_at"]) or now_local()
    if (now_local() - started).total_seconds() > MAX_RUN_H * 3600:        # cold review S909 #3: never a run left open for days
        taken = any((_msg(con, t["msg_id"]) or {}).get("handed_at") for t in tries)
        if taken:                                                         # second look S909 #1: a real fault is never closed quietly
            for t in tries:
                _skip(con, t["msg_id"], "the check ran out of time")
            ok = _decide(con, run, "fail", "too_old",
                         "Today's check message was taken by the reception phone but did not reach the clinic inbox within %d hours. "
                         "Open the Reception phone card and tap Check now; if it repeats, tell Claude." % MAX_RUN_H)
            return "decided fail (too old)%s" % ("" if ok else " -- NOTICE NOT WRITTEN")
        _close_quiet(con, run, "stopped", "too_old", "closed after %d hours without a result" % MAX_RUN_H)
        return "closed (too old)"
    cur = tries[-1]
    queued = parse(cur["queued_at"]) or now_local()
    age = (now_local() - queued).total_seconds() / 60.0
    wait = _int(con, "phone_check.wait_min", 20)
    if age < wait:
        return "waiting (%d of %d min)" % (int(age), wait)
    m = _msg(con, cur["msg_id"]) or {}
    asked = parse(_phone_last(con))
    if not m.get("handed_at"):
        if not (asked and asked > queued) and age < NOT_ASKED_WAIT_MIN:          # cold review S909 #8: a phone that has not asked yet
            return "waiting for the phone to ask (%d of %d min)" % (int(age), NOT_ASKED_WAIT_MIN)
        kind = "not_collected"
    elif m.get("status") != "sent":
        kind = "no_report"
    else:
        kind = "not_in_inbox"
    con.execute("UPDATE phone_check_try SET step=? WHERE id=?", (kind, cur["id"]))
    _skip(con, cur["msg_id"], {"not_collected": "not collected in time", "no_report": "no 'sent' report in time",
                               "not_in_inbox": "reported sent, not in the clinic inbox"}[kind])
    con.commit()
    to = digits(setting(con, "phone_check.to"))
    last_ask = ddmm_hhmm(_phone_last(con))
    if kind == "not_collected":
        if asked and asked > queued:
            why = ("The reception phone asked the server (last %s) but did not collect today's check message in %d minutes. "
                   "Open the Reception phone card and tap Check now; if it repeats, tell Claude." % (last_ask, wait))
        else:
            why = ("The reception phone has not asked the server since %s, so today's check message was never collected. On the reception "
                   "phone: is it switched on, on the internet, and is MacroDroid running ('Sanjeevni Whatsapp')?" % last_ask)
        ok = _decide(con, run, "fail", kind, why)
        return "decided fail (not collected)%s" % ("" if ok else " -- NOTICE NOT WRITTEN")
    if cur["attempt"] >= 2 or not to:
        first = tries[0]["step"] if cur["attempt"] >= 2 else kind
        if kind == "no_report" and first == "no_report":
            text = ("The reception phone took the check message twice but never reported it sent, and it did not reach the clinic inbox. "
                    "On the reception phone: MacroDroid > System Log, macro 'Sanjeevni Whatsapp' -- does WhatsApp Business open and send?")
        elif kind == "no_report":
            text = ("The first check message left the reception phone but never reached the clinic inbox; the clinic doctor ran (%s); the "
                    "second message was taken by the phone but never reported sent. On the reception phone: MacroDroid > System Log, macro "
                    "'Sanjeevni Whatsapp'." % (run.get("doctor") or "not run"))
        else:
            text = ("The reception phone sent the check message, but it never reached the clinic inbox, %s. The clinic doctor ran (%s). "
                    "The fault is past the phone and past this server's parts: MyOperator's WhatsApp delivery to the clinic, or the clinic "
                    "number saved on the Reception phone card (%s)." % ("twice" if cur["attempt"] >= 2 else "and no second message was possible",
                                                                       run.get("doctor") or "not run", mask(to)))
        ok = _decide(con, run, "fail", kind, text)
        return "decided fail (%s, second message)%s" % (kind, "" if ok else " -- NOTICE NOT WRITTEN")
    doctor = None
    if kind == "not_in_inbox" and not run.get("doctor"):                      # cold review S909 #4: the doctor once per run, said first
        v, words = run_doctor()
        doctor = "%s: %s" % (v, words)
        con.execute("UPDATE phone_check_run SET doctor=? WHERE id=?", (doctor[:300], run["id"]))
        con.commit()
    _queue(con, run["id"], 2, to)
    con.commit()
    return "second message queued after %s%s" % (kind, (" (doctor %s)" % doctor.split(":")[0]) if doctor else "")


def tick(con, now=None):
    """The five-minute pass: start today's check when its time has come, then look at the running one. Never raises."""
    try:
        ensure(con)
        off = _off(con)
        if off:
            run = _active(con)                                     # cold review S909 #3: a running check is closed, its message withdrawn
            if run:
                _close_quiet(con, run, "stopped", "switched_off", "switched off (%s)" % off)
                return {"ok": True, "off": off, "did": ["closed the running check"]}
            return {"ok": True, "off": off}
        did = []
        t = now or now_ist()
        h, m = _start_time(con)
        start = t.replace(hour=h, minute=m, second=0, microsecond=0)
        day = t.date().isoformat()
        if (start <= t < start + dt.timedelta(hours=START_WINDOW_H) and digits(setting(con, "phone_check.to"))
                and not con.execute("SELECT 1 FROM phone_check_run WHERE day=? AND manual=0", (day,)).fetchone()
                and not _active(con)):
            ok, v = start_run(con)
            did.append("started" if ok else "not started: %s" % v)
        did.append(step(con, t))
        return {"ok": True, "did": did}
    except Exception as e:                                         # noqa: BLE001
        try:
            con.rollback()
        except sqlite3.Error:
            pass
        return {"ok": False, "error": ("%s: %s" % (e.__class__.__name__, e))[:160]}


# ------------------------------------------------------------------ what the owner sees
def save_to(con, who, raw):
    """(ok, message): the clinic's own WhatsApp number; never written to a log or the audit in full."""
    ensure(con)
    d = digits(raw)
    if not d:
        return False, "Not a mobile number (10 digits, or with 91 in front)."
    con.execute("UPDATE setting SET value=? WHERE key='phone_check.to'", (d,))
    con.commit()
    return True, "Saved: %s" % mask(d)


def latest(con):
    r = con.execute("SELECT id, day, manual, started_at, result, step, text, decided_at, doctor FROM phone_check_run ORDER BY id DESC LIMIT 1").fetchone()
    return dict(id=r[0], day=r[1], manual=r[2], started_at=r[3], result=r[4], step=r[5], text=r[6], decided_at=r[7], doctor=r[8]) if r else None


def needs_you_lines(con):
    """The Hub's Needs-you: a number to save; the last check FAILED or fixed itself (24 h). A plain pass says nothing."""
    out = []
    try:
        ensure(con)
        if _off(con):
            return out
        if not digits(setting(con, "phone_check.to")):
            out.append(dict(cls="warn", target="bank", href=CARD,
                            text="The reception phone's daily check is waiting for the clinic's WhatsApp number -- save it once on the Reception phone card."))
            return out
        last = con.execute("SELECT result, text, decided_at FROM phone_check_run WHERE result IS NOT NULL ORDER BY id DESC LIMIT 1").fetchone()
        if last and last[0] in ("fail", "fixed"):
            d = parse(last[2])
            if d and (now_local() - d) <= dt.timedelta(hours=24):
                out.append(dict(cls=("bad" if last[0] == "fail" else "info"), target="bank", href=CARD,
                                text="Phone check %s (%s): %s" % (RESULT_WORD[last[0]], ddmm_hhmm(last[2]), last[1])))
    except Exception:                                              # noqa: BLE001 -- the Hub never waits on this line
        pass
    return out


def card_block(con):
    """The owner's Reception phone card: the daily check's state, the clinic number (masked), Save, Check now. No dialog."""
    ensure(con)
    to = digits(setting(con, "phone_check.to"))
    h, m = _start_time(con)
    last = latest(con)
    if not last:
        state = "not run yet"
    elif last["result"] is None:
        state = "running since %s" % ddmm_hhmm(last["started_at"])
    else:
        state = "%s %s -- %s" % (RESULT_WORD.get(last["result"], last["result"]), ddmm_hhmm(last["decided_at"]), last["text"] or "")
    off = _off(con)
    colour = "#8c1d18" if last and last["result"] == "fail" else ("#2f6b45" if last and last["result"] == "pass" else "#14181c")
    return ('<div id="s909" style="margin-top:10px;border-top:1px solid #ccc;padding-top:8px">'
            '<div><b>Daily delivery check</b> <span style="color:#666;font-size:13px">-- every day at %02d:%02d the phone sends one check '
            'message to the clinic\'s own WhatsApp; not in the clinic inbox in %d min: the failed step is found and mended where the server can, '
            'and you are told here and on your phone.</span></div>'
            '<div style="margin-top:4px">Last check: <b style="color:%s">%s</b>%s</div>'
            '<div style="margin-top:6px">Clinic WhatsApp number: <b>%s</b> <input id="s909num" inputmode="tel" placeholder="clinic WhatsApp number" '
            'style="width:170px;min-height:36px"> <button style="min-height:36px" onclick="s909(\'clinic_number\',{number:document.getElementById(\'s909num\').value},this)">Save</button></div>'
            '<div style="margin-top:6px"><button style="min-height:40px" %s onclick="s909(\'check_now\',{},this)">Check now</button> '
            '<span id="s909say" style="color:#8c1d18"></span></div>'
            '<script>function s909(a,b,btn){btn.disabled=true;fetch("/finance/porders/api/s909/"+a,{method:"POST",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify(b)}).then(function(r){return r.json();}).then(function(j){if(!j.ok){document.getElementById("s909say").textContent=j.message||j.error||"Not done";'
            'btn.disabled=false;return;}location.reload();}).catch(function(){document.getElementById("s909say").textContent="Not done (network)";btn.disabled=false;});}</script></div>'
            % (h, m, _int(con, "phone_check.wait_min", 20), colour, esc(state), (" <span style=\"color:#8c1d18\">(switched off: %s)</span>" % esc(off)) if off else "",
               esc(mask(to)) if to else "none saved", "" if to else "disabled"))


def status_line(con):
    ensure(con)
    last = latest(con)
    to = digits(setting(con, "phone_check.to"))
    return "%s | number %s | off: %s | last: %s" % (VERSION, mask(to) or "none", _off(con) or "no",
                                                   ("%s %s %s" % (last["day"], last["result"] or "running", last["step"] or "")) if last else "none")


# ------------------------------------------------------------------ CLI
def _connect(db):
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    return con


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "status"
    db = os.environ.get("PHONE_CHECK_DB", LIVE_DB)
    if cmd == "tick":
        import fcntl                                               # noqa: PLC0415
        lk = open(LOCK_FILE, "a")
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("%s phone_check: another tick is running" % now_ist().strftime("%Y-%m-%d %H:%M"))
            return 0
        con = _connect(db)
        try:
            r = tick(con)
        finally:
            con.close()
            lk.close()
        if not r.get("ok") or (r.get("did") and r["did"] != ["idle"]):       # quiet when idle or switched off
            print("%s phone_check %s" % (now_ist().strftime("%Y-%m-%d %H:%M"), json.dumps(r, ensure_ascii=False)))
        return 0 if r.get("ok") else 1
    if cmd == "status":
        con = _connect(db)
        try:
            print(status_line(con))
        finally:
            con.close()
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
