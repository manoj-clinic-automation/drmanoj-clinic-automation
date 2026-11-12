#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wa_ladder.py -- kit S798_WA_MESSAGES_SHOWONLY (session S437, 12-Nov-2026, the parent). NEW.

THE LISTS. This file holds NO send code: it opens no network connection and calls no sender. It answers one question for the
owner -- "which approved WhatsApp message would go to whom today?" -- and keeps the STOP list.
S808 (13-Nov-2026): the page gains a switch for each message, the tests and today's record. The SENDING is in
wa_ladder_send.py; the doors below only hand a request over to it (a list's key and row tokens -- never a number or a name).

The owner (D934, 12-Nov-2026 08:34 / 09:39 IST): start the approved templates through the WABA -- post-visit, follow-up,
appointment reminders -- "show only" first. His "ok" (10:12 IST) on the order: follow-up tomorrow, after the visit, appointment
reminder, follow-up date passed (the next morning, again after 5 days), long overdue (two weeks, only the names he ticks).

  GET /portal/messages             the page (English; the doctor role only)
  POST /portal/messages/api/unstop S805: the doctor takes ONE number off the stop list (recorded, never erased)
  POST /portal/messages/api/restop S805: the doctor puts a number he took off back on the stop list
  POST /portal/messages/api/send/<what>  S808: switch | stopall | test | testok | ticked -> wa_ladder_send.door (the doctor only)
  GET /portal/messages/api/plan    {day?} -> the day's lists: name, clinic ID, FULL mobile (his ruling of 21-Sep), the date,
                                   and why a row is held back
  wa_ladder.py --stop-scan         cron, every 5 minutes: an incoming WhatsApp that says STOP puts that number on the stop list
  wa_ladder.py --rescan            the same, reading every stored incoming message again (after the STOP rule is widened)
  wa_ladder.py --stop-status       one line: "ok ..." or "ERROR ..." -- whether the listener is hearing the Inbox
  wa_ladder.py --inbox-check       one line: whether the Inbox store can be read (a count only)
  wa_ladder.py --counts [day]      counts only (no name, no number) -- the installer's DRY line
  wa_ladder.py --selftest          the STOP rule and the number rule on fixed sentences

READS (read-only): finance.db -- dx_visit (the follow-up date given at each visit), patient_visit (who came, when),
patient_ref (name), online_booking; the Call Console's patient mirror /root/wa/console.db (the FULL mobile, by clinic ID or
patient key -- S801: patient_ref keeps the last four digits only); the WhatsApp Inbox's store; the older opt-out file.
WRITES: its own store only (WA_LADDER_DB, default /root/portal/wa_ladder.db): the stop list and the listener's place.
The listener first asks the Inbox to read its receiver's log forward (portal_inbox.ingest -- local files only, what opening
the Inbox page does).

THE RULES (each row is "would go", "on your tick", or held with its reason):
  * a follow-up counts from the patient's LATEST visit only; a patient who has come since is not on any follow-up list;
  * no plain 10-digit mobile on record, or more than one -> held;  the number is on the stop list -> held;
  * if the stop list cannot be read, EVERY row is held (it fails closed);
  * one number gets at most one message a day (the order of the lists decides which);
  * a patient with an online booking ahead is not told "your date has passed";
  * the long-overdue list never goes by itself: every row waits for his tick.
NOT YET (said on the page): leaving out patients who bought medicines meanwhile (D919) -- the pharmacy bill is not yet matched
to the patient here.
"""
import csv
import datetime as dt
import os
import re
import sqlite3
import sys

VERSION = "S808 1.4"
HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
STORE = os.environ.get("WA_LADDER_DB", os.path.join(HERE, "wa_ladder.db"))
INBOX_DB = os.environ.get("WA_LADDER_INBOX_DB", "/root/wa/wa_inbox/inbox.db")
OLD_OPTOUT = os.environ.get("WA_LADDER_OLD_OPTOUT", "/root/wa/wa_opt_outs.csv")
CONSOLE_DB = os.environ.get("WA_LADDER_CONSOLE_DB", "/root/wa/console.db")     # S801: the Call Console's patient mirror
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
STALE_MIN = 20

# the owner's order (10:12 IST 12-Nov); it also decides which message a number gets when it is on two lists the same day
LISTS = [
    ("tomorrow", "Follow-up is tomorrow", "6 pm the day before", "drmanoj_followup_tomorrow"),
    ("post_visit", "After today's visit", "the same day", "drmanoj_post_visit"),
    ("appt", "Appointment reminder (online booking)", "the evening before", "appointment_reminder_1day_ortho"),
    ("due1", "Follow-up date passed yesterday", "the next morning", "drmanoj_followup_due"),
    ("due5", "Follow-up date passed 5 days ago", "the morning of day 5", "drmanoj_followup_missed"),
    ("overdue", "Long overdue (2 weeks) -- only the names you tick", "once, on your tick", "drmanoj_followup_dropout"),
]
TICK = ("overdue",)


def now_ist():
    return dt.datetime.now(IST)


def m10(s):
    """A plain Indian mobile -> its 10 digits; anything else (two numbers in one cell, a landline, a short number) -> ''."""
    d = re.sub(r"\D", "", str(s or ""))
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 and d[0] in "6789" else ""


# ------------------------------------------------------------------ the STOP rule
# A message is a STOP only when, with courtesy words taken out, the WHOLE message is one of these shapes. "report nahi bheji",
# "mera whatsapp band tha", "bus stop ke paas" are ordinary messages and match nothing.
_FILL = set("please pls plz plzz kindly kripya kripaya sir ji dr doctor sahab saheb madam mam maam me mujhe mujhko hume humko hamein "
            "ab now se aage dobara phir aap aapke ye yeh this these is number par pe on my mere mera ko thanks thank you dhanyavad ok okay "
            "hi hello namaste namaskar "
            u"कृपया जी सर अब मुझे हमें "
            u"आगे यह ये इस नंबर पर "
            u"धन्यवाद नमस्ते डॉक्टर "
            u"साहब".split())
_OBJ = r"(?:message|messages|msg|msgs|sms|whatsapp|reminder|reminders|promotion|promotions)"
_OBJ_H = (u"(?:मैसेज|मेसेज|संदेश|"
          u"व्हाट्सएप|व्हाट्सऐप|"
          u"रिमाइंडर)")
_STOP_SHAPES = [re.compile("^" + p + "$") for p in (
    r"(?:stop|stopp|unsubscribe|optout|opt out)(?: (?:it|all|the|sending|send|message|messages|msg|msgs|sms|whatsapp|reminder|reminders|promotion|promotions))*",
    r"(?:do not|dont|no more|never) (?:send|message|messages|msg|msgs)(?: (?:message|messages|msg|msgs|sms|whatsapp|any|more|anymore|again))*",
    _OBJ + r"? ?(?:bhejna )?(?:mat|na|naa|nahi|nahin) (?:bhejo|bheje|bhejen|bhejiye|bhejie|bhejiyega|bhejna)",
    _OBJ + r" (?:mat|na|naa|nahi|nahin) (?:karo|kare|karen|kariye|kijiye)",
    _OBJ + r"? ?(?:bhejna )?(?:band|bandh) (?:karo|kar do|kardo|kijiye|kariye|kar dijiye|karen|kare|kar dein)",
    u"(?:स्टॉप|स्टाप)",
    _OBJ_H + u"? ?(?:भेजना )?(?:मत|न|ना|नहीं) "
             u"(?:भेजो|भेजें|भेजे|भेजिए|भेजिये|भेजना)",
    _OBJ_H + u"? ?(?:भेजना )?बंद "
             u"(?:करो|कर दो|करें|करे|कीजिए|कीजिये|करिए|करिये|कर दीजिए)",
)]


def _norm(body):
    t = str(body or "").lower().replace(u"’", "").replace(u"‘", "").replace("'", "")
    t = re.sub(u"[।॥]", " ", t)                              # the Hindi full stop
    t = re.sub(u"[^a-z0-9ऀ-ॿ]+", " ", t)                     # letters, digits and Devanagari stay; emoji and marks go
    return " ".join(w for w in t.split() if w not in _FILL)


def is_stop(body):
    """True when a short incoming message, as a whole, asks for no more messages."""
    if len(str(body or "")) > 80:
        return False
    t = _norm(body)
    return bool(t) and any(p.match(t) for p in _STOP_SHAPES)


def selftest():
    yes = ["STOP", "stop.", " Stop ", "Stop!!", "stop please", "Please stop", u"STOP \U0001F64F", "Stop promotions", "unsubscribe",
           "opt out", "message mat bhejo", "Mat bhejo", "msg band karo", "band karo", "Band kar do", "please dont send messages",
           u"don’t send", "Do not message", "no more messages", "msg mat karo", "Sir please message mat bhejiye",
           u"स्टॉप", u"मत भेजो", u"मैसेज बंद करो।",
           u"कृपया मैसेज न भेजें"]
    no = ["", "Hi", "clinic kab band hota hai", "Sunday band hai kya", "bus stop ke paas", "dard nahi ruk raha", "report bhej do",
          "stop " + "x" * 80, "kab aana hai", "non stop dard", "report nahi bheji", "kitna bhejna hai", "X-ray purana bhej du",
          "mera whatsapp band tha", "dawai stop karni hai kya", "no message aaya", "band", "mat karo",
          u"लोकेशन भेज दो", u"पैसे ऑनलाइन भेज दूं",
          u"रिपोर्ट नहीं भेजी"]
    a, b = "9" + "%09d" % 79801, "9" + "%09d" % 79802                  # made up at run time: no number is written in this file (F-185)
    nums = (m10(a) == a and m10("+91 " + a[:5] + "-" + a[5:]) == a and m10("0" + a) == a and m10(a + "/11") == ""
            and m10(a + ", " + b) == "" and m10("0581 " + "25" + "67890") == "" and m10("12345") == "")
    return all(is_stop(s) for s in yes) and not any(is_stop(s) for s in no) and nums


# ------------------------------------------------------------------ its own store
def store():
    con = sqlite3.connect(STORE, timeout=10)
    con.execute("CREATE TABLE IF NOT EXISTS optout(mobile TEXT PRIMARY KEY, at TEXT NOT NULL, source TEXT NOT NULL, "
                "said TEXT NOT NULL DEFAULT '', rid INTEGER)")
    con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
    # S805: every number the doctor took off the stop list -- kept for ever; upto_rid = the last incoming message the
    # listener had read at that moment (a STOP up to it is the old one and never puts the number back)
    con.execute("CREATE TABLE IF NOT EXISTS optout_removed(id INTEGER PRIMARY KEY AUTOINCREMENT, mobile TEXT NOT NULL, "
                "removed_at TEXT NOT NULL, removed_by TEXT NOT NULL DEFAULT '', was_at TEXT NOT NULL DEFAULT '', "
                "was_source TEXT NOT NULL DEFAULT '', was_said TEXT NOT NULL DEFAULT '', upto_rid INTEGER NOT NULL DEFAULT 0)")
    return con


def _meta(con, k, default=""):
    r = con.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return r[0] if r and r[0] is not None else default


def _set(con, k, v):
    con.execute("INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?)", (k, str(v)))


def stops():
    """({mobile: {at, source, said}}, error) -- this store's list plus the older opt-out file. error is '' or a plain reason;
    with an error the caller must hold every row."""
    out, err = {}, ""
    taken = {}                                                         # S805: {mobile: when it was last taken off}
    try:
        con = store()
        try:
            for mob, at, src, said in con.execute("SELECT mobile, at, source, said FROM optout"):
                out[mob] = {"at": at or "", "source": src or "", "said": said or ""}
            taken = dict(con.execute("SELECT mobile, MAX(removed_at) FROM optout_removed GROUP BY mobile"))   # S805
        finally:
            con.close()
    except sqlite3.Error as e:
        err = "the stop list could not be read (%s)" % type(e).__name__
    if os.path.exists(OLD_OPTOUT):
        try:
            # S805: a number of this hand-kept file that the doctor took off stays off -- until the file is changed again;
            # then every number still in it is back on the list (the safe direction; he can take it off again)
            fchg = dt.datetime.fromtimestamp(os.path.getmtime(OLD_OPTOUT), IST).strftime("%Y-%m-%d %H:%M:%S")
            with open(OLD_OPTOUT, newline="", encoding="utf-8-sig", errors="replace") as fh:
                for r in csv.reader(fh):
                    for cell in r:
                        mob = m10(cell)
                        if mob:
                            if not (mob in taken and str(taken[mob] or "") >= fchg):   # S805
                                out.setdefault(mob, {"at": "", "source": "older list", "said": ""})
                            break
        except (OSError, csv.Error, UnicodeError) as e:
            err = err or "the older opt-out file could not be read (%s)" % type(e).__name__
    return out, err


class ListenerError(RuntimeError):
    pass


def inbox_check():
    """(ok, text) -- can the Inbox store be read the way the listener reads it? A count only."""
    if not os.path.exists(INBOX_DB):
        return False, "the Inbox store is not at %s" % INBOX_DB
    try:
        src = sqlite3.connect("file:%s?mode=ro" % INBOX_DB, uri=True, timeout=10)
        try:
            n = src.execute("SELECT COUNT(*), COALESCE(MAX(rid), 0) FROM msgs WHERE dir='in' AND phone IS NOT NULL AND (body IS NULL OR body IS NOT NULL) "
                            "AND (ts IS NULL OR ts IS NOT NULL)").fetchone()
        finally:
            src.close()
    except sqlite3.Error as e:
        return False, "the Inbox store could not be read (%s: %s)" % (type(e).__name__, str(e)[:80])
    return True, "%d incoming messages in the Inbox store" % n[0]


def stop_scan(ingest=True, rescan=False):
    """Read the Inbox store's incoming messages after the last one seen; a STOP goes on the list. Returns (seen, new).
    Raises ListenerError (its reason kept for the page) when the Inbox store cannot be read -- never silently deaf."""
    note = ""
    if ingest and os.environ.get("WA_LADDER_INGEST", "1") != "0":
        try:                                                           # what opening the Inbox does: read the receiver's log forward
            if HERE not in sys.path:
                sys.path.insert(0, HERE)
            import portal_inbox
            portal_inbox.ingest(force=True)
        except Exception as e:                                         # noqa: BLE001 -- the listener still reads what is stored
            note = "the Inbox's own reader did not run (%s)" % type(e).__name__
    con = store()
    try:
        stamp = now_ist().strftime("%Y-%m-%d %H:%M:%S")
        _set(con, "ingest_note", note)
        last = 0 if rescan else int(_meta(con, "last_rid", "0") or 0)
        ok, why = inbox_check()
        rows = []
        if ok:
            try:
                src = sqlite3.connect("file:%s?mode=ro" % INBOX_DB, uri=True, timeout=10)
                try:
                    rows = src.execute("SELECT rid, phone, ts, body FROM msgs WHERE dir='in' AND rid > ? ORDER BY rid", (last,)).fetchall()
                finally:
                    src.close()
            except sqlite3.Error as e:
                ok, why = False, "the Inbox store could not be read (%s)" % type(e).__name__
        if not ok:
            changed = _meta(con, "last_error", "") != why
            _set(con, "last_error", why)
            if changed:
                _set(con, "last_error_at", stamp)
            con.commit()
            e = ListenerError(why)
            e.changed = changed
            raise e
        seen = new = 0
        taken = dict(con.execute("SELECT mobile, MAX(upto_rid) FROM optout_removed GROUP BY mobile"))   # S805
        for rid, phone, ts, body in rows:
            seen += 1
            last = max(last, int(rid))
            mob = m10(phone)
            if mob and is_stop(body) and int(rid) > int(taken.get(mob, -1)):   # S805: only a STOP newer than the taking-off
                cur = con.execute("INSERT OR IGNORE INTO optout(mobile, at, source, said, rid) VALUES (?,?,?,?,?)",
                                  (mob, str(ts or "")[:19] or stamp, "WhatsApp reply", str(body or "").strip()[:80], int(rid)))
                new += cur.rowcount
        _set(con, "last_rid", last)
        _set(con, "last_scan", stamp)
        _set(con, "last_error", "")
        con.commit()
        return (seen, new)
    finally:
        con.close()


def unstop(mobile, by):
    """S805 -- the doctor takes ONE number off the stop list. Returns (ok, text). The removal is RECORDED in optout_removed
    (the number, what it had said, when, who) and never erased; the listener does not put the number back for a STOP it had
    already read (not on --rescan either), but a NEW STOP reply -- also one that had arrived and was not read yet -- puts it back."""
    mob = m10(mobile)
    if not mob:
        return False, "that is not a mobile number"
    st, err = stops()
    if err:
        return False, err
    if mob not in st:
        return False, "that number is not on the stop list"
    was = st[mob]
    try:
        con = store()
        try:
            con.execute("BEGIN IMMEDIATE")        # the listener cannot write between the read of its place and this change
            row = con.execute("SELECT rid FROM optout WHERE mobile=?", (mob,)).fetchone()
            upto = max(int(_meta(con, "last_rid", "0") or 0), int((row[0] if row else 0) or 0))
            con.execute("INSERT INTO optout_removed(mobile, removed_at, removed_by, was_at, was_source, was_said, upto_rid) VALUES (?,?,?,?,?,?,?)",
                        (mob, now_ist().strftime("%Y-%m-%d %H:%M:%S"), str(by or "")[:40], was["at"], was["source"], was["said"], upto))
            con.execute("DELETE FROM optout WHERE mobile=?", (mob,))      # the row lives on, whole, in optout_removed
            con.commit()
        finally:
            con.close()
    except (sqlite3.Error, ValueError) as e:
        return False, "the stop list could not be changed (%s)" % type(e).__name__
    return True, "taken off the stop list"


def restop(mobile, by):
    """S805 -- the doctor puts a number he took off BACK on the stop list (a slip corrected). Only a number that was taken off
    here can be put back this way. Returns (ok, text)."""
    mob = m10(mobile)
    if not mob:
        return False, "that is not a mobile number"
    try:
        con = store()
        try:
            con.execute("BEGIN IMMEDIATE")
            r = con.execute("SELECT was_said FROM optout_removed WHERE mobile=? ORDER BY id DESC LIMIT 1", (mob,)).fetchone()
            if not r:
                con.rollback()
                return False, "that number was not taken off the stop list here"
            con.execute("INSERT OR IGNORE INTO optout(mobile, at, source, said, rid) VALUES (?,?,?,?,NULL)",
                        (mob, now_ist().strftime("%Y-%m-%d %H:%M:%S"), ("put back by " + str(by or "the doctor"))[:60], r[0] or ""))
            con.commit()
        finally:
            con.close()
    except sqlite3.Error as e:
        return False, "the stop list could not be changed (%s)" % type(e).__name__
    return True, "back on the stop list"


def taken_off(on_list=None, limit=50):
    """S805 -- the numbers the doctor took off the stop list and that are OFF it now, newest first, one line a number."""
    on = on_list if on_list is not None else stops()[0]
    rows, seen = [], set()
    try:
        con = store()
        try:
            for m, a, b_, s, sc in con.execute("SELECT mobile, removed_at, removed_by, was_said, was_source FROM optout_removed ORDER BY id DESC"):
                if m in seen:
                    continue
                seen.add(m)
                if m in on:                                              # it said STOP again, or was put back
                    continue
                rows.append({"mobile": m, "at": a, "by": b_, "said": s, "source": sc})
                if len(rows) >= int(limit):
                    break
        finally:
            con.close()
    except sqlite3.Error:
        return []
    return rows


def stop_status():
    """One line for the installer and the log: 'ok ...' or 'ERROR ...'."""
    try:
        con = store()
        try:
            err, at, scan, note = (_meta(con, "last_error"), _meta(con, "last_error_at"), _meta(con, "last_scan"), _meta(con, "ingest_note"))
            n = con.execute("SELECT COUNT(*) FROM optout").fetchone()[0]
        finally:
            con.close()
    except sqlite3.Error as e:
        return "ERROR the stop list could not be read (%s)" % type(e).__name__
    if err:
        return "ERROR %s (since %s)" % (err, at or "?")
    if not scan:
        return "ERROR the listener has not run yet"
    return "ok last checked %s . stop list %d%s" % (scan, n, (" . note: " + note) if note else "")


# ------------------------------------------------------------------ the mobiles (S801)
def _key(v):
    s = str(v if v is not None else "").strip()
    return s[:-2] if re.match(r"^\d+\.0$", s) else s


def console_mobiles():
    """({clinic_id: {mobiles}}, {patient_uid: {mobiles}}, error) from the Call Console's patient mirror, read-only."""
    by_cid, by_uid = {}, {}
    if not os.path.exists(CONSOLE_DB):
        return by_cid, by_uid, "the Call Console's patient list is not at %s" % CONSOLE_DB
    try:
        con = sqlite3.connect("file:%s?mode=ro" % CONSOLE_DB, uri=True, timeout=10)
        try:
            for ph, uid, cid in con.execute("SELECT phone10, patient_uid, clinic_id FROM patients"):
                mob = m10(ph)
                if not mob:
                    continue
                if _key(cid):
                    by_cid.setdefault(_key(cid), set()).add(mob)
                if _key(uid):
                    by_uid.setdefault(_key(uid), set()).add(mob)
        finally:
            con.close()
    except sqlite3.Error as e:
        return {}, {}, "the Call Console's patient list could not be read (%s)" % type(e).__name__
    return by_cid, by_uid, ""


# ------------------------------------------------------------------ the day's lists
def _d(s):
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def _nice(s):
    try:
        t = _d(str(s)[:10])
        return "%d %s %d" % (t.day, t.strftime("%b"), t.year) + (str(s)[10:16] if len(str(s)) > 10 else "")
    except (ValueError, TypeError):
        return str(s or "")


def plan(day=None):
    """The lists for one day. None when finance.db cannot be read."""
    day = day or now_ist().strftime("%Y-%m-%d")
    D = _d(day)
    off = lambda n: (D + dt.timedelta(days=n)).strftime("%Y-%m-%d")    # noqa: E731
    try:
        con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=5)
    except sqlite3.Error:
        return None
    try:
        last = {}                                                      # the latest visit that carries a diagnosis row, per patient
        for uid, vd, cid, fu in con.execute("SELECT patient_uid, visit_date, clinic_id, follow_up_date FROM dx_visit ORDER BY visit_date"):
            uid, cid = uid or "", cid or ""
            if uid or cid:
                last[uid or ("cid:" + cid)] = (uid, vd or "", cid, (fu or "")[:10])
        lv_uid, lv_cid = {}, {}                                        # the latest visit of any kind, by either key
        for uid, cid, m in con.execute("SELECT patient_uid, clinic_id, MAX(visit_date) FROM patient_visit GROUP BY patient_uid, clinic_id"):
            if uid:
                lv_uid[uid] = max(lv_uid.get(uid, ""), m or "")
            if cid:
                lv_cid[cid] = max(lv_cid.get(cid, ""), m or "")
        ref = {}
        for cid, name, mob, l4 in con.execute("SELECT clinic_id, name, mobile, phone_last4 FROM patient_ref"):
            ref[cid] = (name or "", m10(mob), l4 or "")
        today_vis = [(r[0] or "", r[1] or "") for r in con.execute("SELECT DISTINCT clinic_id, patient_uid FROM patient_visit WHERE visit_date=?", (day,))]
        try:
            books = con.execute("SELECT name, mobile, appt_at FROM online_booking WHERE substr(COALESCE(appt_at,''),1,10) >= ? "
                                "ORDER BY appt_at", (day,)).fetchall()
        except sqlite3.Error:                                          # no table yet: nothing has come
            books = []
        fresh = {"last_visit": con.execute("SELECT MAX(visit_date) FROM patient_visit").fetchone()[0] or "",
                 "last_dx": con.execute("SELECT MAX(visit_date) FROM dx_visit").fetchone()[0] or ""}
    except sqlite3.Error:
        return None
    finally:
        con.close()

    c_cid, c_uid, c_err = console_mobiles()

    def person(cid, date, uid=""):
        name, mob, l4 = ref.get(cid, ("", "", ""))
        many = 0
        if not mob:                                                    # S801: patient_ref has no full mobile -> the Call Console's list
            cand = c_cid.get(_key(cid)) or c_uid.get(_key(uid)) or set()
            if len(cand) == 1:
                mob = next(iter(cand))
            elif len(cand) > 1:
                many = len(cand)
        return {"name": name or "?", "cid": cid or "", "mobile": mob, "last4": l4, "date": _nice(date), "hold": "", "tick": False, "many": many}

    raw = {k: [] for k, _t, _w, _tp in LISTS}
    want = {off(1): "tomorrow", off(-1): "due1", off(-5): "due5", off(-14): "overdue"}
    for uid, vd, cid, fu in last.values():
        k = want.get(fu)
        if not k or max(lv_uid.get(uid, ""), lv_cid.get(cid, "")) > vd:   # no such date, or the patient has come since
            continue
        raw[k].append(person(cid, fu, uid))
    for cid, uid in today_vis:
        raw["post_visit"].append(person(cid, day, uid))
    booked_ahead = set()
    for name, mob, at in books:
        mob = m10(mob)
        if mob:
            booked_ahead.add(mob)
        if (at or "")[:10] == off(1):
            raw["appt"].append({"name": name or "?", "cid": "", "mobile": mob, "last4": mob[-4:], "date": _nice(at), "hold": "", "tick": False, "many": 0})

    st, st_err = stops()
    used = set()
    lists = []
    for k, title, when, tpl in LISTS:
        rows = sorted(raw[k], key=lambda r: (str(r["name"]).lower(), str(r["cid"])))
        go = tick = 0
        for r in rows:
            mob = r["mobile"]
            if st_err:
                r["hold"] = "the stop list could not be read"
            elif not mob:
                r["hold"] = ("%d different mobiles on record" % r["many"]) if r.get("many") else "no mobile number on record"
            elif mob in st:
                r["hold"] = "replied STOP"
            elif k in ("due1", "due5", "overdue") and mob in booked_ahead:
                r["hold"] = "has an online booking ahead"
            elif mob in used:
                r["hold"] = "this number already gets a message today"
            elif k in TICK:
                r["tick"] = True                                       # never by itself; takes no number's place for the day
                tick += 1
            else:
                used.add(mob)
                go += 1
        lists.append({"key": k, "title": title, "when": when, "template": tpl, "rows": rows, "go": go, "tick": tick,
                      "held": len(rows) - go - tick})
    fresh.update({"stop_scan": "", "stop_error": st_err, "stop_error_at": "", "stop_stale": True, "mobile_error": c_err})
    try:
        sc = store()
        try:
            fresh["stop_scan"] = _meta(sc, "last_scan", "")
            if not st_err:
                fresh["stop_error"] = _meta(sc, "last_error", "")
                fresh["stop_error_at"] = _meta(sc, "last_error_at", "")
        finally:
            sc.close()
        t = dt.datetime.strptime(fresh["stop_scan"], "%Y-%m-%d %H:%M:%S")
        fresh["stop_stale"] = (now_ist().replace(tzinfo=None) - t).total_seconds() > STALE_MIN * 60
    except (sqlite3.Error, ValueError):
        pass
    stop_rows = sorted(({"mobile": m, "at": v["at"], "source": v["source"], "said": v["said"]} for m, v in st.items()),
                       key=lambda r: r["at"], reverse=True)
    return {"ok": True, "day": day, "day_nice": _nice(day), "weekday": D.strftime("%A"), "today": now_ist().strftime("%Y-%m-%d"),
            "lists": lists, "stops": stop_rows, "taken_off": ([] if st_err else taken_off(st)), "fresh": fresh, "sends": False, "version": VERSION}


def counts(day=None):
    p = plan(day)
    if p is None:
        return "finance.db not readable"
    parts = ["%s %d go / %d held" % (x["key"], x["go"], x["held"]) if x["key"] not in TICK
             else "%s %d for his tick / %d held" % (x["key"], x["tick"], x["held"]) for x in p["lists"]]
    nomob = sum(1 for x in p["lists"] for r in x["rows"] if not r["mobile"])
    return "%s: %s | no mobile %d | stop list %d | visits up to %s" % (p["day"], " . ".join(parts), nomob, len(p["stops"]),
                                                                        p["fresh"]["last_visit"])


# ------------------------------------------------------------------ the page
def install(app, login_required, sso_user):
    from flask import jsonify, make_response, request

    def _doctor():
        return ((sso_user(request) or {}).get("role")) == "doctor"

    def _send_mod():                                                   # S808: the sending lives in its own file
        try:
            import wa_ladder_send
            return wa_ladder_send
        except Exception:                                              # noqa: BLE001 -- the page stands without it, show only
            return None

    @app.route("/portal/messages")
    @login_required
    def wl_page():
        if not _doctor():
            return make_response("Not for this login.", 403)
        resp = make_response(PAGE)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.route("/portal/messages/api/plan")
    @login_required
    def wl_plan():
        if not _doctor():
            return jsonify({"ok": False}), 403
        day = request.args.get("day", "")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
            day = None
        else:
            try:
                if abs((_d(day) - now_ist().date()).days) > 31:
                    day = None
            except ValueError:
                day = None
        p = plan(day)
        if p is None:
            return jsonify({"ok": False, "msg": "database not readable"}), 503
        S = _send_mod()                                                # S808
        if S is None:
            p["send"] = {"ok": False, "msg": "The sending part is not on the server."}
        else:
            try:
                S.decorate(p, sso_user(request))
            except Exception as e:                                     # noqa: BLE001 -- the lists still show
                p["send"] = {"ok": False, "broken": True,
                             "msg": "The switches could not be read (%s). Sending may still be ON. Tell Claude." % type(e).__name__}
                p["sends"] = False
        resp = jsonify(p)
        resp.headers["Cache-Control"] = "no-store"
        return resp

    def _stop_door(change):                                            # S805
        if not _doctor():
            return jsonify({"ok": False, "msg": "Not for this login."}), 403
        if request.headers.get("X-Messages") != "1":                   # only this page's own script sends it
            return jsonify({"ok": False, "msg": "bad request"}), 400
        d = request.get_json(silent=True) or {}
        ok, text = change(d.get("mobile", "") if isinstance(d, dict) else "", (sso_user(request) or {}).get("user") or "doctor")
        resp = jsonify({"ok": ok, "msg": text})
        resp.headers["Cache-Control"] = "no-store"
        return resp, (200 if ok else 409)

    @app.route("/portal/messages/api/unstop", methods=["POST"])       # S805
    @login_required
    def wl_unstop():
        return _stop_door(unstop)

    @app.route("/portal/messages/api/restop", methods=["POST"])       # S805
    @login_required
    def wl_restop():
        return _stop_door(restop)

    @app.route("/portal/messages/api/send/<what>", methods=["POST"])  # S808
    @login_required
    def wl_send(what):
        if not _doctor():
            return jsonify({"ok": False, "msg": "Not for this login."}), 403
        if request.headers.get("X-Messages") != "1":                   # only this page's own script sends it
            return jsonify({"ok": False, "msg": "bad request"}), 400
        S = _send_mod()
        if S is None:
            return jsonify({"ok": False, "msg": "The sending part is not on the server. Nothing was sent."}), 503
        d = request.get_json(silent=True)
        if not isinstance(d, dict):
            d = {}
        try:
            ok, text = S.door(str(what), d, sso_user(request))
        except Exception as e:                                         # noqa: BLE001
            ok, text = False, "It did not work (%s). Do not press again: look at 'What went today', and tell Claude." % type(e).__name__
        resp = jsonify({"ok": bool(ok), "msg": str(text)})
        resp.headers["Cache-Control"] = "no-store"
        return resp, (200 if ok else 409)


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WhatsApp messages to patients</title>
<style>
:root{--pg:#f3f2ee;--cd:#fbfaf8;--in:#f0eee8;--ln:#e0dcd3;--t1:#23272f;--t2:#5d6470;--t3:#8a8f99;--ac:#1c5cab;--warn:#7a5600;--warnbg:#fdf3d7;--bad:#a52626;--badbg:#fbeaea;--good:#0a6b2a;--goodbg:#e4f3e7;--knob:#fff;--off:#b9b4a8}
*{box-sizing:border-box}body{margin:0;background:var(--pg);color:var(--t1);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--ln);background:var(--cd)}
header a{color:var(--t2);text-decoration:none;font-size:22px}h1{font-size:18px;margin:0;flex:1}
main{max-width:860px;margin:0 auto;padding:12px 16px 48px}
button{font:inherit;color:inherit}
.strip{background:var(--warnbg);color:var(--warn);font-weight:700;border-radius:10px;padding:10px 14px;margin:0 0 10px}
.err{background:var(--badbg);color:var(--bad);font-weight:600;border-radius:10px;padding:10px 14px;margin:0 0 10px}
.okm{background:var(--goodbg);color:var(--good);font-weight:600;border-radius:10px;padding:10px 14px;margin:0 0 10px}
.state{background:var(--cd);border:1px solid var(--ln);border-radius:12px;padding:12px 14px;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:0 0 10px}
.state b{font-size:16px;flex:1 1 220px;min-width:0}.state .cap{color:var(--t2);font-variant-numeric:tabular-nums}
.state.on{background:var(--goodbg);border-color:var(--good)}
.btn{min-height:40px;padding:6px 12px;border:1px solid var(--ln);background:var(--cd);border-radius:10px;cursor:pointer;color:var(--ac)}
.btn[disabled]{color:var(--t3);cursor:default}
.btn.stop{color:var(--bad);border-color:var(--bad);font-weight:700}
.btn.sure2{background:var(--warnbg);color:var(--warn);border-color:var(--warn);font-weight:700}
.btn:focus-visible,.sw:focus-visible,summary:focus-visible{outline:2px solid var(--ac);outline-offset:2px}
.day{display:flex;align-items:center;gap:8px;margin:0 0 12px;flex-wrap:wrap}
.day b{font-size:16px}.day button{min-height:38px;min-width:44px;border:1px solid var(--ln);background:var(--cd);border-radius:10px;cursor:pointer;color:var(--t1)}
.day .tot{margin-left:auto;color:var(--t2);font-variant-numeric:tabular-nums}
.card,details.box{background:var(--cd);border:1px solid var(--ln);border-radius:12px;margin:0 0 10px;overflow:hidden}
.card.on{border-color:var(--good)}
.top{display:flex;gap:10px;align-items:center;padding:12px 14px;flex-wrap:wrap}
.tt{flex:1 1 200px;min-width:0}.tt b{display:block}.tt span{color:var(--t2);font-size:13px;overflow-wrap:anywhere}
.n{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}.n b{font-size:20px}.n span{display:block;font-size:13px;color:var(--t2)}
.sw{position:relative;width:64px;height:36px;border-radius:18px;border:0;background:var(--off);cursor:pointer;flex:none}
.sw::after{content:"";position:absolute;top:4px;left:4px;width:28px;height:28px;border-radius:50%;background:var(--knob);transition:left .15s}
.sw[aria-checked="true"]{background:var(--good)}.sw[aria-checked="true"]::after{left:32px}
@media (prefers-reduced-motion: reduce){.sw::after{transition:none}}
.swb{display:flex;align-items:center;gap:8px;flex:none}
.swl{font-size:12px;font-weight:800;letter-spacing:.05em;width:30px;text-align:center;color:var(--t2)}
.card.on .swl{color:var(--good)}
.sure{flex:1 1 100%;background:var(--warnbg);color:var(--warn);font-weight:700;border-radius:8px;padding:8px 10px}
.runl{flex:1 1 100%;color:var(--t2);font-size:14px}.runl.bad{color:var(--bad);font-weight:600}
.card details{border-top:1px solid var(--ln)}
.card summary{cursor:pointer;padding:9px 14px;color:var(--ac);font-size:14px}
details.box summary{list-style:none;cursor:pointer;padding:12px 14px;display:flex;gap:10px;align-items:center}
details.box summary::-webkit-details-marker{display:none}
.rw{border-top:1px solid var(--ln);padding:9px 14px;display:flex;flex-wrap:wrap;gap:2px 12px;align-items:baseline}
.rw .nm{font-weight:600;flex:1 1 170px;min-width:0}
.rw label{display:flex;gap:10px;align-items:center;flex:1 1 170px;min-width:0;font-weight:600;cursor:pointer}
.rw input{width:20px;height:20px;flex:none}
.rw .st{font-size:13px;font-weight:600;color:var(--t2)}
.rw .st.ok,.rw .st.go{color:var(--good)}.rw .st.no{color:var(--bad)}.rw .st.tk{color:var(--warn)}
.rw .meta{flex:1 1 100%;color:var(--t2);font-size:14px;font-variant-numeric:tabular-nums}
.rw .meta b{color:var(--t1);font-weight:600;letter-spacing:.3px}
.rw.held{background:var(--in)}.rw.held .st{color:var(--bad);white-space:normal}
.rw .off,.rw .on{font-size:13px;min-height:36px;padding:4px 10px;border:1px solid var(--ln);background:var(--cd);border-radius:10px;cursor:pointer;color:var(--ac);white-space:nowrap}
.rw .off.sure1{background:var(--warnbg);color:var(--warn);border-color:var(--warn);font-weight:700}
.acts{border-top:1px solid var(--ln);padding:10px 14px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.acts .said{color:var(--t2);font-size:13px;flex:1 1 200px;min-width:0}
pre{margin:0;border-top:1px solid var(--ln);padding:12px 14px;background:var(--in);white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.empty{padding:12px 14px;color:var(--t2);border-top:1px solid var(--ln)}
ul.rules{margin:0;padding:10px 14px 12px 32px;border-top:1px solid var(--ln)}ul.rules li{margin:4px 0}
.foot{color:var(--t2);font-size:13px;margin-top:14px}
</style></head><body>
<header><a href="/portal" aria-label="back">&#8592;</a><h1>WhatsApp messages to patients</h1></header>
<main>
<div id="mode"></div>
<div class="state" id="state" hidden><b id="stateTxt"></b><span class="cap" id="cap"></span><button class="btn stop" id="stopAll" hidden>Stop all sending</button></div>
<div id="msg"></div>
<div id="lis"></div>
<div class="day"><button id="pv" aria-label="previous day">&#8249;</button><b id="dn"></b><button id="nx" aria-label="next day">&#8250;</button><button id="td">Today</button><span class="tot" id="tot"></span></div>
<div id="m"></div>
<p class="foot" id="ft"></p>
</main>
<script>
var DAY='',OPENSTOP=false,D=null,OPEN={},ARM='',ARMT=0,SAID={},TICKED={},TARM=0,BUSY=false,MSG=null;
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function shift(d,n){var p=d.split('-'),t=new Date(Date.UTC(+p[0],+p[1]-1,+p[2]+n));return t.toISOString().slice(0,10);}
function hm(ts){var m=/(\d\d):(\d\d)/.exec(String(ts||'').slice(11));if(!m)return String(ts||'');var h=+m[1];return ((h%12)||12)+':'+m[2]+(h<12?' am':' pm');}
function dm(ts){var p=String(ts||'').slice(0,10).split('-');if(p.length<3)return '';return (+p[2])+' '+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+p[1]-1];}
function S(){return (D&&D.send&&D.send.ok)?D.send:null;}
function canAct(){var s=S();return !!(s&&s.owner&&s.is_today);}
function tickable(r){return canAct()&&r.tick&&!r.hold&&!r.sent&&r.token;}
function nTicked(){var n=0;if(!D)return 0;D.lists.forEach(function(x){if(x.key==='overdue')x.rows.forEach(function(r){if(tickable(r)&&TICKED[r.token])n++;});});return n;}
function runline(x,li){
 var r=li.run;
 if(r){var c=r.sent+' sent'+(r.failed?', '+r.failed+' not sent':'')+(r.held?', '+r.held+' held':'');
  if(r.state==='done')return ['Went today at '+hm(r.at)+': '+c+'.'+(r.note?' '+r.note+'.':''),0];
  if(r.state==='stopped')return ['STOPPED today at '+hm(r.at)+': '+c+'. '+r.note,1];
  return [r.note||'Not sent today.',1];}
 if(!li.auto||!li.on)return null;
 if(li.late_on)return ['Switched on after today\'s time had passed. It starts tomorrow at '+li.at+'.',0];
 if(li.wait)return ['Waiting: '+li.wait+'. It goes as soon as they arrive, or not at all today.',1];
 if(li.over)return ['Not sent today.',1];
 return ['Goes today at '+li.at+'.',0];}
function acts(x,li){
 var t=li.test||{},k=x.key,h='<div class="acts">';
 if(k==='overdue'){var n=nTicked();h+='<button class="btn'+(TARM?' sure2':'')+'" data-send="1"'+((n&&t.confirmed)?'':' disabled')+'>'+(TARM?'Tap again to send to '+n+(n===1?' name':' names'):'Send to the ticked names ('+n+')')+'</button>';}
 h+='<button class="btn" data-test="'+k+'">Send a test to my phone</button>';
 if(t.ok&&t.mode==='LIVE'&&!t.confirmed)h+='<button class="btn" data-testok="'+k+'">It arrived</button>';
 var need=(k==='overdue'?'The ticked names cannot be sent':'This message cannot be turned on')+' until a test has reached your phone.';
 var said=SAID[k]||(t.confirmed?'Test confirmed on '+dm(t.confirmed_at)+'.'+((t.sent_at>t.confirmed_at&&!t.ok&&t.error&&t.error!=='sending')?' A later test was not sent: '+t.error+'.':''):(t.ok&&t.mode==='LIVE'?'Test sent at '+hm(t.sent_at)+'. When it is on your phone, press "It arrived".':
  (t.sent_at&&!t.ok?'The last test was not sent'+(t.error&&t.error!=='sending'?': '+t.error:'')+'. '+need:'No test sent yet. '+need)));
 return h+'<span class="said">'+esc(said)+'</span></div>';}
function sec(x){
 var s=S(),li=s?s.lists[x.key]:null,isT=x.key==='overdue',today=!!(s&&s.is_today),on=!!(li&&li.on),act=canAct();
 var big=isT?x.tick:x.go,lab=isT?'for your tick':(on&&today?'will go':'would go');
 if(li&&li.run&&today&&li.run.state!=='skipped'){big=li.run.sent;lab='sent today';}
 var h='<div class="card'+(on?' on':'')+'"><div class="top"><span class="tt"><b>'+esc(x.title)+'</b><span>'+esc(li?li.when:x.when)+' &middot; '+esc(x.template)+'</span></span>'+
  '<span class="n"><b>'+big+'</b><span>'+lab+(x.held?' &middot; '+x.held+' held':'')+'</span></span>';
 if(li&&li.auto){h+='<span class="swb"><span class="swl">'+(on?'ON':'OFF')+'</span>';
  if(act)h+='<button class="sw" role="switch" aria-checked="'+on+'" aria-label="'+esc(x.title)+' on or off" data-sw="'+x.key+'"></button>';
  h+='</span>';}
 if(ARM===x.key&&li)h+='<div class="sure">Tap the switch once more to turn this ON. From then it goes by itself every day at '+esc(li.at)+'.</div>';
 if(li&&today){var rl=runline(x,li);if(rl)h+='<div class="runl'+(rl[1]?' bad':'')+'">'+esc(rl[0])+'</div>';}
 h+='</div><details data-k="'+x.key+'"'+(OPEN[x.key]?' open':'')+'><summary>Who is on this list ('+x.rows.length+')</summary>';
 if(!x.rows.length)h+='<div class="empty">Nobody on this list for this day.</div>';
 x.rows.forEach(function(r){
  var st,cls='';
  if(r.sent){st=r.sent.t;cls=r.sent.k==='ok'?' ok':' no';}
  else if(r.hold){st='Held: '+r.hold;}
  else if(isT){st=r.tick?'on your tick':'';cls=' tk';}
  else if(on&&today&&li.run){st='not sent in today\'s run';}
  else if(on&&today&&!li.over&&!li.late_on&&!li.wait){st='will go at '+li.at;cls=' go';}
  else st='would go';
  var bad=r.hold||(r.sent&&r.sent.k!=='ok');
  h+='<div class="rw'+(bad?' held':'')+'">'+(tickable(r)?'<label><input type="checkbox" class="tkb" data-t="'+esc(r.token)+'"'+(TICKED[r.token]?' checked':'')+'>'+esc(r.name)+'</label>':'<span class="nm">'+esc(r.name)+'</span>')+
   '<span class="st'+cls+'">'+esc(st)+'</span><span class="meta">'+(r.cid?'ID '+esc(r.cid):'new patient')+' &middot; <b>'+esc(r.mobile||(r.last4?'....'+r.last4:'no number'))+'</b> &middot; '+esc(r.date)+'</span></div>';});
 h+='</details>';
 if(li&&li.preview)h+='<details data-k="pv-'+x.key+'"'+(OPEN['pv-'+x.key]?' open':'')+'><summary>See the message the patient gets</summary><pre>'+esc(li.preview)+
  '\n\n(This is the message in short. The full approved wording is the one in your MyOperator panel; the test to your phone shows it exactly.)</pre></details>';
 if(li&&act)h+=acts(x,li);
 return h+'</div>';}
function record(){
 var s=S();if(!s||!s.is_today||!s.record.length)return '';
 var h='<div class="card"><details data-k="rec"'+(OPEN.rec?' open':'')+'><summary>What went today ('+s.record.length+')</summary>';
 s.record.forEach(function(r){h+='<div class="rw'+(r.said.k==='ok'?'':' held')+'"><span class="nm">'+esc(r.name)+'</span><span class="st '+(r.said.k==='ok'?'ok':'no')+'">'+esc(r.said.t)+'</span>'+
  '<span class="meta">'+esc(r.list)+' &middot; '+(r.cid?'ID '+esc(r.cid):'new patient')+' &middot; <b>'+esc(r.mobile)+'</b></span></div>';});
 return h+'</details></div>';}
function rules(){
 if(!S())return '';
 return '<div class="card"><details data-k="rules"'+(OPEN.rules?' open':'')+'><summary>What never happens</summary><ul class="rules">'+
  '<li>A message whose switch is OFF is never sent.</li><li>A number that replied STOP is never messaged. The stop list is read again at the moment of sending.</li>'+
  '<li>A patient whose return visit is on the server\'s records is not reminded.</li><li>One number gets at most one message a day.</li>'+
  '<li>No patient gets the same reminder twice for the same follow-up date, whichever page sent the first one.</li>'+
  '<li>A message that fails after it has left is not sent again.</li><li>"Long overdue" goes only to the names you tick.</li>'+
  '<li>Before the first real send of any message, a test goes to your own phone.</li>'+
  '<li>If yesterday\'s visits have not reached the server, the reminders wait rather than tell a patient who came that he did not.</li>'+
  '<li>Nothing goes after its time has passed by more than an hour and a half; that day is skipped and the page says so.</li></ul></details></div>';}
function stops(s){
 var h='<details class="box"'+(OPENSTOP?' open':'')+'><summary><span class="tt"><b>Numbers that said STOP</b><span>never messaged again, unless you take one off</span></span><span class="n"><b>'+s.length+'</b></span></summary>';
 if(!s.length)return h+'<div class="empty">Nobody has replied STOP.</div></details>';
 s.forEach(function(r){h+='<div class="rw"><span class="nm">'+esc(r.mobile)+'</span><button class="off" data-m="'+esc(r.mobile)+'">Take off the stop list</button><span class="meta">'+esc(r.source)+((r.at||'')?' &middot; '+esc((r.at||'').slice(0,16)):'')+(r.said?' &middot; said: '+esc(r.said):'')+'</span></div>';});
 return h+'</details>';}
function taken(t){
 if(!t||!t.length)return '';
 var h='<details class="box"'+(OPENSTOP?' open':'')+'><summary><span class="tt"><b>Taken off the stop list by you</b><span>can be messaged again; a new STOP reply puts the number back</span></span><span class="n"><b>'+t.length+'</b></span></summary>';
 t.forEach(function(r){h+='<div class="rw"><span class="nm">'+esc(r.mobile)+'</span><button class="on" data-m="'+esc(r.mobile)+'">Put back on the stop list</button><span class="meta">taken off '+esc((r.at||'').slice(0,16))+(r.by?' by '+esc(r.by):'')+(r.said?' &middot; had said: '+esc(r.said):(r.source?' &middot; '+esc(r.source):''))+'</span></div>';});
 return h+'</details>';}
function draw(){
 var d=D,s=S(),go=0,held=0,tick=0,n=0;d.lists.forEach(function(x){go+=x.go;held+=x.held;tick+=x.tick;});
 document.getElementById('dn').textContent=d.weekday+', '+d.day_nice+(d.day===d.today?' (today)':'');
 document.getElementById('tot').textContent=go+(s&&s.is_today?' on the lists':' would go')+(tick?' · '+tick+' for your tick':'')+(held?' · '+held+' held':'');
 var M='';
 if(!s&&d.send&&d.send.broken)M='<div class="err">'+esc(d.send.msg)+'</div>';
 else if(!s)M='<div class="strip">SHOW ONLY &mdash; nothing is sent from this page. '+esc((d.send&&d.send.msg)||'It lists who would get which approved message.')+'</div>';
 else{
  if(s.mode==='TEST')M+='<div class="strip">'+esc(s.mode_text)+'</div>';
  else if(s.mode!=='LIVE')M+='<div class="err">'+esc(s.mode_text)+'</div>';
  if(!s.owner)M+='<div class="strip">You can read this page. Only the doctor\'s own login can turn a message on or send.</div>';
  else if(!s.is_today)M+='<div class="strip">This is not today\'s page. The switches and the sending are on today\'s page.</div>';
  else if(!s.test_last4)M+='<div class="err">Your own number for the tests is not set on the server yet. Tell Claude.</div>';}
 document.getElementById('mode').innerHTML=M;
 var st=document.getElementById('state'),brk=!s&&d.send&&d.send.broken;st.hidden=!s&&!brk;
 if(brk){document.getElementById('stateTxt').textContent='The switches could not be read.';document.getElementById('cap').textContent='';st.className='state';document.getElementById('stopAll').hidden=false;}
 if(s){for(var k in s.lists)if(s.lists[k].auto&&s.lists[k].on)n++;
  document.getElementById('stateTxt').textContent=n?('Sending is ON for '+n+' of the five automatic messages.'):'Sending is OFF for all five automatic messages.';
  document.getElementById('cap').textContent=s.sent_today+' sent today · at most '+s.ceiling+' a day';
  st.className='state'+(n?' on':'');document.getElementById('stopAll').hidden=!(n&&s.owner);}
 document.getElementById('msg').innerHTML=MSG?'<div class="'+(MSG.ok?'okm':'err')+'">'+esc(MSG.t)+'</div>':'';
 document.getElementById('m').innerHTML=d.lists.map(sec).join('')+record()+stops(d.stops)+taken(d.taken_off)+rules();
 var f=d.fresh||{},L='';
 if(f.stop_error)L='The STOP listener is not working: '+f.stop_error+(f.stop_error_at?' (since '+f.stop_error_at.slice(0,16)+')':'')+'. Tell Claude.';
 else if(f.stop_stale)L='The STOP listener has not checked for replies since '+((f.stop_scan||'').slice(0,16)||'it was installed')+'. Tell Claude.';
 var MB=f.mobile_error?'The patient mobile numbers could not be read: '+f.mobile_error+'. Tell Claude.':'';
 document.getElementById('lis').innerHTML=(L?'<div class="err">'+esc(L)+'</div>':'')+(MB?'<div class="err">'+esc(MB)+'</div>':'');
 document.getElementById('ft').textContent='Visits on record up to '+(f.last_visit||'?')+' · follow-up dates up to '+(f.last_dx||'?')+' · STOP replies last checked '+((f.stop_scan||'never').slice(0,16))+
  '. Not applied yet: leaving out patients who bought medicines meanwhile.';}
function load(){
 return fetch('/portal/messages/api/plan'+(DAY?'?day='+DAY:''),{credentials:'same-origin',cache:'no-store'}).then(function(x){return x.json();}).then(function(d){
  if(!d.ok){document.getElementById('m').innerHTML='<div class="err">Could not read the clinic records. Try again in a minute.</div>';return;}
  D=d;DAY=d.day;draw();
 }).catch(function(){document.getElementById('m').innerHTML='<div class="err">Could not load. Open the page again.</div>';});}
function post(what,body,key){
 if(BUSY)return;BUSY=true;ARM='';TARM=0;
 if(key){SAID[key]='Working...';draw();}
 fetch('/portal/messages/api/send/'+what,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Messages':'1'},body:JSON.stringify(body)})
  .then(function(x){return x.json();}).then(function(d){
   var t=(d&&d.msg)||'No answer.';if(key)SAID[key]=t;if(!key||what==='ticked')MSG={ok:!!(d&&d.ok),t:t};
   if(what==='ticked'&&d&&d.ok)TICKED={};
   BUSY=false;return load();})
  .catch(function(){BUSY=false;var t='The server did not answer. Do not press again: open the page again and look at "What went today".';if(key)SAID[key]=t;else MSG={ok:false,t:t};if(D)draw();});}
document.getElementById('pv').onclick=function(){if(DAY){DAY=shift(DAY,-1);load();}};
document.getElementById('nx').onclick=function(){if(DAY){DAY=shift(DAY,1);load();}};
document.getElementById('td').onclick=function(){DAY='';load();};
document.getElementById('stopAll').onclick=function(){MSG=null;post('stopall',{});};
document.getElementById('m').addEventListener('toggle',function(e){var k=e.target&&e.target.getAttribute&&e.target.getAttribute('data-k');if(k)OPEN[k]=e.target.open;},true);
document.getElementById('m').addEventListener('change',function(e){
 var c=e.target;if(!c||!c.classList||!c.classList.contains('tkb'))return;
 TICKED[c.getAttribute('data-t')]=c.checked;TARM=0;
 var b=document.querySelector('[data-send]'),n=nTicked(),s=S(),ok=s&&s.lists.overdue&&s.lists.overdue.test.confirmed;
 if(b){b.textContent='Send to the ticked names ('+n+')';b.classList.remove('sure2');b.disabled=!(n&&ok);}});
document.getElementById('m').addEventListener('click',function(e){
 var b=e.target;if(!b||!b.classList||!b.getAttribute)return;var now=Date.now(),s=S(),k;
 if(b.getAttribute('data-sw')){k=b.getAttribute('data-sw');var li=s&&s.lists[k];if(!li||BUSY)return;
  if(li.on){post('switch',{list:k,on:false},k);return;}
  if(!li.test.confirmed){SAID[k]='First send a test of this message to your phone and press "It arrived". Then it can be turned on.';ARM='';draw();return;}
  if(ARM!==k){ARM=k;ARMT=now;SAID[k]='';draw();setTimeout(function(){if(ARM===k&&Date.now()-ARMT>=5900){ARM='';if(D&&!BUSY)draw();}},6000);return;}
  if(now-ARMT<700)return;
  post('switch',{list:k,on:true},k);return;}
 if(b.getAttribute('data-test')){k=b.getAttribute('data-test');post('test',{list:k},k);return;}
 if(b.getAttribute('data-testok')){k=b.getAttribute('data-testok');post('testok',{list:k},k);return;}
 if(b.getAttribute('data-send')){if(BUSY||b.disabled)return;var toks=[];D.lists.forEach(function(x){if(x.key==='overdue')x.rows.forEach(function(r){if(tickable(r)&&TICKED[r.token])toks.push(r.token);});});
  if(!toks.length)return;
  if(!TARM){TARM=now;b.textContent='Tap again to send to '+toks.length+(toks.length===1?' name':' names');b.classList.add('sure2');
   setTimeout(function(){if(TARM&&Date.now()-TARM>=5900){TARM=0;if(D&&!BUSY)draw();}},6000);return;}
  if(now-TARM<700)return;
  post('ticked',{day:D.day,tokens:toks},'overdue');return;}
 var off=b.classList.contains('off'),on=b.classList.contains('on');if(!off&&!on)return;
 var label=off?'Take off the stop list':'Put back on the stop list';
 function calm(){b.disabled=false;b.removeAttribute('data-sure');b.classList.remove('sure1');}
 if(off){
  if(b.getAttribute('data-sure')!=='1'){b.setAttribute('data-sure','1');b.setAttribute('data-t',String(now));b.textContent='Tap again to take it off';b.classList.add('sure1');
   setTimeout(function(){if(b.isConnected&&!b.disabled&&b.getAttribute('data-sure')==='1'){calm();b.textContent=label;}},6000);return;}
  if(now-(+b.getAttribute('data-t')||0)<700)return;}
 b.disabled=true;b.textContent=off?'Taking off...':'Putting back...';
 fetch('/portal/messages/api/'+(off?'unstop':'restop'),{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Messages':'1'},body:JSON.stringify({mobile:b.getAttribute('data-m')})})
  .then(function(x){return x.json();}).then(function(d){if(d&&d.ok){OPENSTOP=true;load();}else{calm();b.textContent='Could not: '+((d&&d.msg)||'try again');}})
  .catch(function(){calm();b.textContent='Could not - open the page again and retry';});
});
setInterval(function(){if(document.visibilityState==='visible'&&D&&!BUSY&&!ARM&&!TARM&&!nTicked()&&!document.querySelector('[data-sure="1"]'))load();},120000);
load();
</script></body></html>"""


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        ok = selftest()
        print("selftest", "OK" if ok else "RED")
        sys.exit(0 if ok else 1)
    if "--stop-scan" in a or "--rescan" in a:
        try:
            seen, new = stop_scan(rescan="--rescan" in a)
        except ListenerError as e:
            if getattr(e, "changed", True):                            # said once, not every 5 minutes
                print("%s STOP LISTENER NOT WORKING: %s" % (now_ist().strftime("%Y-%m-%d %H:%M"), e), flush=True)
            sys.exit(1)
        if new:
            print("%s STOP: %d new on the stop list (of %d incoming read)" % (now_ist().strftime("%Y-%m-%d %H:%M"), new, seen), flush=True)
        sys.exit(0)
    if "--stop-status" in a:
        s = stop_status()
        print(s)
        sys.exit(0 if s.startswith("ok") else 1)
    if "--inbox-check" in a:
        ok, text = inbox_check()
        print(("ok " if ok else "ERROR ") + text)
        sys.exit(0 if ok else 1)
    if "--counts" in a:
        i = a.index("--counts")
        print(counts(a[i + 1] if len(a) > i + 1 else None))
        sys.exit(0)
    print(__doc__)
