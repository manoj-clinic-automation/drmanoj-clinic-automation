#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wa_ladder_send.py -- kit S808_WA_LADDER_SEND (session S442, 12/13-Nov-2026, the parent). NEW.

THE SENDING from /portal/messages. wa_ladder.py decides WHO is on a list (it still holds no send code); this file decides
WHETHER a row goes, sends it through the portal's one sender (portal_wa.send -- ONE request a message; no sender code here),
and writes down everything it did. Built from S440_WA_SENDING_PLAN.md; the owner's words D940, D946, D947.

  wa_ladder_send.py --tick                 cron, every 5 minutes: a list whose switch is ON goes once, at its time
  wa_ladder_send.py --status               one line, counts only (no name; of a number only its last four digits)
  wa_ladder_send.py --stop-all             every switch OFF (the installer's --undo)
  wa_ladder_send.py --contract             one line: does the portal's sender take what this file hands it (nothing is sent)
  wa_ladder_send.py --set-test-mobile N    the installer: the owner's own number for the tests (kept in the store only)
  wa_ladder_send.py --selftest             the date reader and the clock rules on fixed values

THE RULES (the plan's thirteen; each is a check in walk_s808.py):
   1  a switch that is OFF sends nothing; every switch is OFF until the doctor turns it on;
   2  wa_ladder.plan() decides who is on a list -- a row it holds is never sent;
   3  before a batch the newest replies are read (the STOP listener's own pass); if the listener is deaf or behind, or says
      that the Inbox's own reader did not run, nothing goes; the stop list is read AGAIN for every row; if it cannot be
      read nothing goes. The Inbox reader's one silent failure (its folder cannot be listed) is looked for here too;
   4  one number gets at most one message a day -- this file's own record AND the portal's send log (any other page);
   5  never twice for the same follow-up date, whichever page sent the first;
   6  WRITTEN AHEAD: a row is recorded as 'trying' before the request leaves; whatever happens next it is never tried again;
   7  the one canonical sender, one request a message;
   8  a list goes once a day at its time; if that time was missed it may still go inside 90 minutes, otherwise that day is
      skipped and said; no message of a timed list STARTS after those 90 minutes (the last is 10:30 pm, after today's visit),
      and the ticked names go only between 8 am and 9 pm;
   9  at most 150 messages a day across all lists; the rest are held and said;
  10  a list's switch cannot be turned ON (and the ticked names cannot be sent) until a LIVE test of that message has gone
      to the doctor's own phone and he has pressed "It arrived";
  11  PORTAL_WA_DRYRUN is respected, read again for every row: in TEST nothing leaves;
  12  every try, hold and refusal is in the store (wa_ladder.db) and on the page;
  13  /root/finance/_off/ALL_OFF stops everything; so does "Stop all sending" on the page.
ADDED HERE (the safe side): a list waits while the visit records are behind (yesterday's visits not in yet -- a patient who
came would be told he missed his date); a batch STOPS at the first refusal that would repeat for every row (a wrong key, the
gateway down) and after two refusals in a row, so one fault cannot use up every row's one try (the rest of that day's
list is then not sent, and the page says so).
"""
import csv
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import sqlite3
import sys
import time

VERSION = "S808 1.3"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import wa_ladder as L                                                    # noqa: E402 -- the lists, the stop list, the store

ALL_OFF = os.environ.get("WA_LADDER_ALL_OFF", "/root/finance/_off/ALL_OFF")
CONFIG = os.environ.get("WA_LADDER_PORTAL_CONFIG", os.path.join(HERE, "portal_config.py"))
PORTAL_LOG = os.environ.get("WA_LADDER_PORTAL_LOG", "")                   # '' -> portal_wa.LOG
CEILING = 150                                                            # D947: a runaway guard, not a target
WINDOW_MIN = 90
TIMES = {"tomorrow": (18, 0), "post_visit": (21, 0), "appt": (18, 0), "due1": (10, 0), "due5": (10, 0)}      # D947
WHEN = {"tomorrow": "goes at 6:00 pm, the day before", "post_visit": "goes at 9:00 pm, the same day",
        "appt": "goes at 6:00 pm, the evening before", "due1": "goes at 10:00 am, the next morning",
        "due5": "goes at 10:00 am, on day 5", "overdue": "goes only to the names you tick, when you press Send"}
OFFSET = {"tomorrow": 1, "post_visit": 0, "appt": 1, "due1": -1, "due5": -5, "overdue": -14}
AUTO = tuple(k for k, _t, _w, _tp in L.LISTS if k not in L.TICK)
TPL = {k: tp for k, _t, _w, tp in L.LISTS}
TITLE = {k: t for k, t, _w, _tp in L.LISTS}
TICK_HOURS = (8, 21)                                                     # a press outside 8 am - 9 pm sends nothing
RUN_LOCK = os.environ.get("WA_LADDER_SEND_LOCK", os.path.join(HERE, "wa_ladder_send.lock"))   # one timed run at a time, taken inside tick()
READER_RETRY_S = 3                                                       # the Inbox's own reader failed: one more try after this, then nothing goes
LATE_ON_MIN = 6                                                          # switched on this near the end of today's time: it starts tomorrow
MAX_TICKED = 60
PAGE_BUDGET_S = 30                                                       # a press on the page starts no new message after this
SENDER = None                                                            # the walk puts a recorder here; live: portal_wa.send


# ------------------------------------------------------------------ small things
def _stamp(now):
    return now.strftime("%Y-%m-%d %H:%M:%S")


def _hm(ts):
    """'2026-11-13 18:02:10' -> '6:02 pm'."""
    try:
        t = dt.datetime.strptime(str(ts)[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        return str(ts or "")
    return "%d:%02d %s" % ((t.hour % 12) or 12, t.minute, "am" if t.hour < 12 else "pm")


def _at(key):
    h, m = TIMES[key]
    return "%d:%02d %s" % ((h % 12) or 12, m, "am" if h < 12 else "pm")


def _mask(s):
    return re.sub(r"\d{6,}", lambda m: "#" + m.group(0)[-4:], str(s or ""))


_MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def parse_dates(s):
    """The date inside a value another page put into a message ('13 Nov 2026', '13-11-2026', '2026-11-13 10:30') -> a set of
    ISO dates. A date that can be read two ways (3/4/2027) gives BOTH: a doubt holds a message, it never lets one through."""
    s, out = str(s or ""), set()

    def add(y, m, d):
        try:
            out.add(dt.date(int(y), int(m), int(d)).isoformat())
        except ValueError:
            pass
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        add(m.group(1), m.group(2), m.group(3))
        return out
    m = re.search(r"(\d{1,2})[ \-/.]+([A-Za-z]{3,9})[ \-/.,]+(\d{4})", s)
    if m and m.group(2)[:3].lower() in _MON:
        add(m.group(3), _MON[m.group(2)[:3].lower()], m.group(1))
        return out
    m = re.search(r"(\d{1,2})[\-/.](\d{1,2})[\-/.](\d{4})", s)
    if m:
        add(m.group(3), m.group(2), m.group(1))                          # day first, as the clinic writes it
        add(m.group(3), m.group(1), m.group(2))                          # ... and the other reading
    return out


def parse_date(s):
    """One reading (day first) -- for the self-test."""
    d = sorted(parse_dates(s))
    m = re.search(r"(\d{1,2})[\-/.](\d{1,2})[\-/.](\d{4})", str(s or ""))
    if len(d) == 2 and m:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))
    return d[0] if d else ""


def token(day, key, row):
    """What the page hands back for a ticked row: no name, no number -- the server finds the row in its own list again."""
    return hashlib.sha1(("%s|%s|%s|%s" % (day, key, row.get("cid", ""), row.get("mobile", ""))).encode("utf-8")).hexdigest()[:20]


def ref_date(key, day):
    return (L._d(day) + dt.timedelta(days=OFFSET[key])).strftime("%Y-%m-%d")


def clean_name(n):
    s = " ".join(str(n or "").split())
    return s[:60] if re.search(r"[^\W\d_]", s) else ""                    # a name has at least one letter


def values_for(key, row, day):
    """(values, '') for the template of this list, or (None, why) -- built from the SERVER's row only."""
    name = clean_name(row.get("name"))
    if not name:
        return None, "no name on record"
    ref = ref_date(key, day)
    if key == "post_visit":
        return {"1": name}, ""
    if key == "appt":
        when = L._nice(ref)
        m = re.search(r"(\d{1,2}):(\d{2})\s*$", str(row.get("date") or ""))
        if m and int(m.group(1)) < 24:
            h = int(m.group(1))
            when += ", %d:%s %s" % ((h % 12) or 12, m.group(2), "AM" if h < 12 else "PM")
        return {"var_1": name, "var_2": when}, ""
    v = {"1": name, "2": L._nice(ref)}
    if key == "overdue":
        v["3"] = str(-OFFSET[key])
    return v, ""


def sample_values(key, day):
    v, _ = values_for(key, {"name": "Test Patient", "date": "x 10:30"}, day)
    return v


# ------------------------------------------------------------------ the portal's settings (its own rule: the file, else the environment)
def _config():
    """(get, error). get(name, default) answers as the portal's _cfg_get does: the settings file's value, else the environment.
    The file itself is read and run every time (no cached copy), by the page and by the timed run alike. An unreadable file
    is an error and nothing is sent. The installer checks that the timed run's bare environment sees the same mode."""
    ns = {"__name__": "portal_config", "__file__": CONFIG}
    if os.path.exists(CONFIG):
        try:
            with open(CONFIG, "rb") as fh:
                exec(compile(fh.read(), CONFIG, "exec"), ns)             # noqa: S102 -- the portal's own settings file
        except Exception as e:                                           # noqa: BLE001
            return (lambda n, d="": d), "the portal's settings could not be read (%s)" % type(e).__name__

    def get(n, d=""):
        v = ns.get(n)
        return v if v else os.environ.get(n, d)
    return get, ""


def conf():
    """(key, test_mode, error) -- the key is never printed, logged or returned to a page; and no text that came back from
    outside (which could carry anything) is ever kept or shown -- see _why()."""
    get, err = _config()
    if err:
        return "", True, err
    return str(get("MYOP_AUTH_TOKEN", "") or ""), (str(get("PORTAL_WA_DRYRUN", "1") or "1") != "0"), ""


def owner_ok(who):
    """The portal's own WhatsApp gate: the doctor role AND a login named in PORTAL_WA_USERS (default: manoj)."""
    who = who or {}
    get, err = _config()
    if err:
        return False
    allowed = set(x.strip().lower() for x in str(get("PORTAL_WA_USERS", "manoj") or "manoj").split(",") if x.strip())
    return who.get("role") == "doctor" and str(who.get("user") or "").lower() in allowed


def mode():
    """('LIVE' | 'TEST' | 'OFF' | 'ERR', text)."""
    if os.path.exists(ALL_OFF):
        return "OFF", "The estate's master switch is OFF. Nothing is sent from anywhere."
    key, dry, err = conf()
    if err:
        return "ERR", "Nothing can be sent: %s." % err
    if dry:
        return "TEST", "TEST mode: the portal's WhatsApp sender is in test mode. Nothing leaves this page."
    if not key:
        return "ERR", "Nothing can be sent: the WhatsApp key is not set on the server."
    return "LIVE", ""


def _why(r):
    """(state, text, every) for an answer of the sender that is not a success. The words that came back from outside are
    never kept, logged or shown -- only the HTTP number is taken from them. every=True: the same would happen to every row."""
    err = str((r or {}).get("error") or "")
    if (r or {}).get("mode") == "reject":                                # the portal's sender turned it down before any request
        t = ("not a valid mobile number" if err.startswith("not a valid") else "the portal's sender does not know this message" if err.startswith("unknown template")
             else "a value of the message was missing" if err.startswith("missing value") else "the portal's sender turned it down")
        return "failed", "not sent: " + t, False
    if err.startswith("MYOP_AUTH_TOKEN not configured"):
        return "failed", "the WhatsApp key is not set on the server", True
    m = re.match(r"HTTP (\d{3})\b", err)
    if m and int(m.group(1)) < 500:
        code = int(m.group(1))
        return "failed", "WhatsApp refused it (HTTP %d)" % code, code in (401, 403, 429)
    if m:
        return "unsure", "it may have gone; the gateway answered HTTP %s" % m.group(1), True
    return "unsure", "it may have gone; no clear answer came back", True


def _sender():
    if SENDER is not None:
        return SENDER
    import portal_wa
    return portal_wa.send


def _log_path():
    if PORTAL_LOG:
        return PORTAL_LOG
    import portal_wa
    return portal_wa.LOG


# ------------------------------------------------------------------ the store (new tables in wa_ladder.db)
def store():
    con = L.store()
    con.execute("CREATE TABLE IF NOT EXISTS send_switch(list TEXT PRIMARY KEY, is_on INTEGER NOT NULL DEFAULT 0, at TEXT NOT NULL, "
                "by TEXT NOT NULL DEFAULT '')")
    con.execute("CREATE TABLE IF NOT EXISTS send_test(list TEXT PRIMARY KEY, sent_at TEXT NOT NULL, ok INTEGER NOT NULL DEFAULT 0, "
                "mode TEXT NOT NULL DEFAULT '', message_id TEXT NOT NULL DEFAULT '', error TEXT NOT NULL DEFAULT '', "
                "confirmed_at TEXT NOT NULL DEFAULT '', confirmed_by TEXT NOT NULL DEFAULT '')")
    # every attempt, for ever. The two UNIQUE rules ARE rules 4 and 5 for this file's own sends: a second writer is refused
    # by the database itself, whatever process it is in.
    con.execute("CREATE TABLE IF NOT EXISTS send_row(id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, list TEXT NOT NULL, "
                "mobile TEXT NOT NULL, cid TEXT NOT NULL DEFAULT '', name TEXT NOT NULL DEFAULT '', ref_date TEXT NOT NULL, "
                "template TEXT NOT NULL, state TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '', at TEXT NOT NULL, "
                "done_at TEXT NOT NULL DEFAULT '', message_id TEXT NOT NULL DEFAULT '', by TEXT NOT NULL DEFAULT '', "
                "UNIQUE(day, mobile), UNIQUE(list, mobile, ref_date))")
    con.execute("CREATE TABLE IF NOT EXISTS send_hold(day TEXT NOT NULL, list TEXT NOT NULL, mobile TEXT NOT NULL DEFAULT '', "
                "cid TEXT NOT NULL DEFAULT '', name TEXT NOT NULL DEFAULT '', reason TEXT NOT NULL, at TEXT NOT NULL, "
                "PRIMARY KEY(day, list, cid, mobile))")
    con.execute("CREATE TABLE IF NOT EXISTS send_run(day TEXT NOT NULL, list TEXT NOT NULL, state TEXT NOT NULL, at TEXT NOT NULL, "
                "note TEXT NOT NULL DEFAULT '', sent INTEGER NOT NULL DEFAULT 0, failed INTEGER NOT NULL DEFAULT 0, "
                "held INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(day, list))")
    con.execute("CREATE TABLE IF NOT EXISTS send_log(id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, by TEXT NOT NULL DEFAULT '', "
                "what TEXT NOT NULL, list TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')")
    return con


def _note(con, now, by, what, key="", note=""):
    con.execute("INSERT INTO send_log(at, by, what, list, note) VALUES (?,?,?,?,?)", (_stamp(now), str(by or "")[:40], what, key, str(note)[:200]))


def _is_on(con, key):
    r = con.execute("SELECT is_on FROM send_switch WHERE list=?", (key,)).fetchone()
    return bool(r and r[0])


def _test_ok(con, key):
    # confirmed_at is written only by confirm_test, and only when the last test had gone LIVE; a later test that fails, or
    # one in flight, does not undo it (rule 10 asks for a test before the FIRST real send)
    r = con.execute("SELECT confirmed_at FROM send_test WHERE list=?", (key,)).fetchone()
    return bool(r and r[0])


# ------------------------------------------------------------------ the switches and the tests
def _late(now, key):
    """(before, late): before its time today / too near the end of today's time to start today."""
    h, mi = TIMES[key]
    t0 = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    return now < t0, now >= t0 + dt.timedelta(minutes=WINDOW_MIN - LATE_ON_MIN)


def set_switch(key, on, by, now=None):
    now = now or L.now_ist()
    if key not in AUTO:
        return False, "there is no such switch"
    try:
        con = store()
        try:
            if on:
                m, text = mode()
                if m != "LIVE":
                    return False, text
                if not _test_ok(con, key):
                    return False, "First send a test of this message to your own phone and press 'It arrived'."
                if _is_on(con, key):
                    return True, "It is already ON."
            con.execute("INSERT OR REPLACE INTO send_switch(list, is_on, at, by) VALUES (?,?,?,?)", (key, 1 if on else 0, _stamp(now), str(by or "")[:40]))
            _note(con, now, by, "switch on" if on else "switch off", key)
            con.commit()
        finally:
            con.close()
    except sqlite3.Error as e:
        return False, "the switch could not be changed (%s). Tell Claude." % type(e).__name__
    if not on:
        return True, "OFF"
    before, late = _late(now, key)
    if before:
        return True, "ON. It goes by itself every day at %s, starting today." % _at(key)
    if not late:
        return True, "ON. Today's list goes within the next few minutes; from tomorrow at %s." % _at(key)
    return True, "ON. It goes by itself every day at %s, starting tomorrow." % _at(key)


def stop_all(by, now=None):
    now = now or L.now_ist()
    try:
        con = store()
        try:
            con.execute("UPDATE send_switch SET is_on=0, at=?, by=? WHERE is_on<>0", (_stamp(now), str(by or "")[:40]))
            _note(con, now, by, "stop all")
            con.commit()
        finally:
            con.close()
    except sqlite3.Error as e:
        return False, "COULD NOT STOP (%s). Sending may still be ON. Tell Claude NOW." % type(e).__name__
    return True, "All sending is OFF."


def test_mobile(con):
    return L.m10(L._meta(con, "send_test_mobile", ""))


def set_test_mobile(n, now=None):
    mob = L.m10(n)
    if not mob:
        return False, "that is not a plain 10-digit mobile number"
    try:
        con = store()
        try:
            L._set(con, "send_test_mobile", mob)
            _note(con, now or L.now_ist(), "installer", "test number set", "", "....%s" % mob[-4:])
            con.commit()
        finally:
            con.close()
    except sqlite3.Error as e:
        return False, "the number could not be kept (%s)" % type(e).__name__
    return True, "the doctor's own number for the tests is set (....%s)" % mob[-4:]


def send_test(key, by, now=None):
    """One message of this list, with a made-up name, to the doctor's OWN number only."""
    now = now or L.now_ist()
    if key not in TPL:
        return False, "there is no such message"
    if os.path.exists(ALL_OFF):
        return False, "The estate's master switch is OFF. Nothing is sent."
    tok_, dry, err = conf()
    if err:
        return False, "Nothing was sent: %s." % err
    con = store()
    try:
        mob = test_mobile(con)
        if not mob:
            return False, "Your own number has not been set on the server yet. Tell Claude."
        old = con.execute("SELECT sent_at, confirmed_at, confirmed_by FROM send_test WHERE list=?", (key,)).fetchone()
        if old and old[0] and (now.replace(tzinfo=None) - dt.datetime.strptime(old[0], "%Y-%m-%d %H:%M:%S")).total_seconds() < 30:
            return False, "A test of this message went less than half a minute ago. Look at your phone first."
        # written ahead, like every send: the test is on record before the request leaves
        con.execute("INSERT OR REPLACE INTO send_test(list, sent_at, ok, mode, message_id, error, confirmed_at, confirmed_by) VALUES (?,?,0,'','','sending',?,?)",
                    (key, _stamp(now), (old[1] if old else ""), (old[2] if old else "")))
        _note(con, now, by, "test", key)
        con.commit()
        try:
            r = _sender()(mob, TPL[key], sample_values(key, now.strftime("%Y-%m-%d")), "wa_ladder:test", tok_, dry_run=dry, timeout=15) or {}
        except Exception as e:                                           # noqa: BLE001
            r = {"ok": False, "mode": "", "error": ""}
        ok = bool(r.get("ok"))
        why = "" if ok else _why(r)[1]
        con.execute("UPDATE send_test SET ok=?, mode=?, message_id=?, error=? WHERE list=?",
                    (1 if ok else 0, str(r.get("mode") or "")[:8], re.sub(r"[^A-Za-z0-9_.:-]", "", str(r.get("message_id") or ""))[:80], why, key))
        con.commit()
    except sqlite3.Error as e:
        return False, "the test could not be recorded (%s). Nothing more was sent" % type(e).__name__
    finally:
        con.close()
    if not ok and why.startswith("it may have gone"):
        return False, "No clear answer came back for the test: %s. Look at your phone; if it is there, send the test once more and then press 'It arrived'." % why
    if not ok:
        return False, "The test was NOT sent: %s." % why
    if r.get("mode") != "LIVE":
        return True, "TEST mode: nothing left the server. (The portal's sender is in test mode.)"
    return True, "Test sent to your phone (....%s) at %s. When it arrives, press 'It arrived'." % (mob[-4:], _hm(_stamp(now)))


def confirm_test(key, by, now=None):
    now = now or L.now_ist()
    try:
        con = store()
        try:
            r = con.execute("SELECT ok, mode FROM send_test WHERE list=?", (key,)).fetchone()
            if not (r and r[0] and r[1] == "LIVE"):
                return False, "No real test of this message has gone yet. Press 'Send a test to my phone' first."
            con.execute("UPDATE send_test SET confirmed_at=?, confirmed_by=? WHERE list=?", (_stamp(now), str(by or "")[:40], key))
            _note(con, now, by, "test arrived", key)
            con.commit()
        finally:
            con.close()
    except sqlite3.Error as e:
        return False, "could not be recorded (%s)" % type(e).__name__
    return True, "Noted. You can now turn this message on." if key in AUTO else "Noted. You can now send to the names you tick."


# ------------------------------------------------------------------ the portal's send log (rules 4 and 5 across pages)
def portal_log():
    """(rows, error). rows = every LIVE row of the portal's send log except one that was plainly turned down (HTTP 4xx, no
    key): {day, mobile, template, dates (ISO dates found in its values)}. A row with any other ending -- sent, a gateway
    error, a cut line -- counts as "went or may have gone". An unreadable log is an error: nothing is sent."""
    try:
        path = _log_path()
    except Exception as e:                                               # noqa: BLE001
        return None, "the portal's sender could not be loaded (%s)" % type(e).__name__
    if not os.path.exists(path):
        return None, "the portal's send log is not at its place"
    out = []
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as fh:
            rd = csv.DictReader(fh)
            if not rd.fieldnames or not {"ts_ist", "phone", "template", "values_json", "mode", "ok", "error"} <= set(rd.fieldnames):
                return None, "the portal's send log does not have the columns this page reads"
            for r in rd:
                if (r.get("mode") or "") != "LIVE":
                    continue
                err = r.get("error") or ""
                if (r.get("ok") or "") != "1" and (re.match(r"HTTP 4\d\d\b", err) or err.startswith("MYOP_AUTH_TOKEN not configured")):
                    continue                                             # plainly turned down: it did not go
                mob = L.m10(r.get("phone"))
                if not mob:
                    continue
                dates = set()
                try:
                    vals = json.loads(r.get("values_json") or "{}")
                    for v in (vals.values() if isinstance(vals, dict) else []):
                        dates |= parse_dates(v)
                except (ValueError, TypeError):
                    pass
                out.append({"day": (r.get("ts_ist") or "")[:10], "mobile": mob, "template": r.get("template") or "", "dates": dates})
    except (OSError, csv.Error, UnicodeError) as e:
        return None, "the portal's send log could not be read (%s)" % type(e).__name__
    return out, ""


def _other_page(plog, mob, tpl, ref, day, dated=True):
    """'' or why this row must not go, from what ANY page of the portal already sent. dated=False: the message carries no
    date (after today's visit) -- only the one-a-day rule applies to it."""
    near = (L._d(day) - dt.timedelta(days=6)).strftime("%Y-%m-%d")
    for r in plog:
        if r["mobile"] != mob:
            continue
        if r["day"] == day:
            return "this number already got a message today (the portal's send log)"
        if dated and r["template"] == tpl and (ref in r["dates"] or (not r["dates"] and r["day"] >= near)):
            return "this reminder already went on %s" % L._nice(r["day"])
    return ""


# ------------------------------------------------------------------ are the visit records up to date? (added: the safe side)
def last_visit_upto(day):
    """The newest visit date on record that is not after 'day' (a mistyped future date must not make the records look
    up to date), or '' when the records cannot be read."""
    try:
        con = sqlite3.connect("file:%s?mode=ro" % L.DB, uri=True, timeout=5)
        try:
            return con.execute("SELECT MAX(visit_date) FROM patient_visit WHERE visit_date <= ?", (day,)).fetchone()[0] or ""
        finally:
            con.close()
    except sqlite3.Error:
        return ""


def stale_reason(key, p, now, lv=None):
    """'' when the list can be trusted now, else why it must wait. It proves only that visits of the last clinic day have
    reached the server -- not that ALL of them have (README: known and left)."""
    today = now.date()
    if key == "appt":
        return ""
    if lv is None:
        lv = last_visit_upto(today.isoformat())
    if key == "post_visit":
        return "" if lv >= today.isoformat() else "today's visits have not reached the server yet (visits on record up to %s)" % (L._nice(lv) if lv else "?")
    need = today - dt.timedelta(days=1)
    if need.weekday() == 6:                                              # Sunday: the clinic is closed
        need -= dt.timedelta(days=1)
    if lv >= need.isoformat():
        return ""
    return "the visits of %s have not reached the server yet (visits on record up to %s)" % (L._nice(need.isoformat()), L._nice(lv) if lv else "?")


# ------------------------------------------------------------------ one batch
def _hold(con, now, day, key, row, why):
    con.execute("INSERT OR REPLACE INTO send_hold(day, list, mobile, cid, name, reason, at) VALUES (?,?,?,?,?,?,?)",
                (day, key, row.get("mobile") or "", row.get("cid") or "", str(row.get("name") or "")[:60], why[:160], _stamp(now)))
    con.commit()


def send_list(key, by, now_fn=None, only=None, budget_s=None, timeout=20, until=None):
    """Send one list for TODAY. only = a set of row tokens (the ticked names) or None (every row that would go).
    until = no message STARTS at or after this moment. Returns {again, stopped, sent, failed, held, left, note}.
    again=True: nothing was decided and nothing was tried -- call later."""
    now_fn = now_fn or L.now_ist
    t_start = time.time()
    now = now_fn()
    day = now.strftime("%Y-%m-%d")
    res = {"again": False, "stopped": "", "sent": 0, "failed": 0, "held": 0, "left": 0, "note": ""}
    m, text = mode()
    if m != "LIVE":
        res["stopped"] = text
        return res
    key_, _dry, _err = conf()
    note = ""
    for attempt in (0, 1):                                               # rule 3: hear the newest replies first, now
        try:
            L.stop_scan()
            c0 = store()
            try:
                note = L._meta(c0, "ingest_note", "")                    # the listener's own word that the Inbox's reader did not run
            finally:
                c0.close()
        except Exception:                                                # noqa: BLE001 -- deaf: nothing goes
            res["again"], res["note"] = True, "the STOP listener cannot read the replies"
            return res
        if not note:
            break
        if attempt == 0:
            time.sleep(READER_RETRY_S)
    if note:                                                             # replies may be waiting unread: nothing goes
        res["again"], res["note"] = True, "the Inbox's own reader did not run, so new STOP replies may be unread"
        return res
    if os.environ.get("WA_LADDER_INGEST", "1") != "0":                   # the reader's own first step, done here: it returns
        try:                                                             # without a word when its folder cannot be listed
            import portal_inbox
            os.listdir(portal_inbox.RAW_DIR)
        except Exception:                                                # noqa: BLE001
            res["again"], res["note"] = True, "the WhatsApp receiver's log folder cannot be read, so new STOP replies may be unread"
            return res
    p = L.plan(day)
    if p is None:
        res["again"], res["note"] = True, "the clinic records could not be read"
        return res
    f = p.get("fresh") or {}
    if f.get("stop_error") or f.get("stop_stale"):
        res["again"], res["note"] = True, "the STOP listener is not hearing the replies"
        return res
    why = stale_reason(key, p, now)
    if why:
        res["again"], res["note"] = True, why
        return res
    plog, perr = portal_log()
    if perr:
        res["stopped"] = "nothing was sent: %s" % perr
        return res
    rows = [r for x in p["lists"] if x["key"] == key for r in x["rows"]]
    tpl, ref = TPL[key], ref_date(key, day)
    bad_run = 0

    def rest(i):                                                         # the rows from i on that this call was asked to send
        return sum(1 for r2 in rows[i:] if only is None or token(day, key, r2) in only)

    def halt(i, why_):
        res["stopped"], res["left"] = why_, res["left"] + rest(i)
    con = store()
    try:
        if not _test_ok(con, key):                                       # rule 10, read again here
            res["stopped"] = "the test of this message to the doctor's phone has not been confirmed"
            return res
        for i, row in enumerate(rows):
            if only is not None and token(day, key, row) not in only:
                continue
            now = now_fn()
            if os.path.exists(ALL_OFF):                                  # rule 13, every row
                halt(i, "stopped: the estate's master switch was turned off")
                break
            m, text = mode()                                             # rule 11, every row
            if m != "LIVE":
                halt(i, "stopped: %s" % text)
                break
            if key in AUTO and not _is_on(con, key):                     # rule 1, every row
                halt(i, "stopped: this message was switched off while it was going")
                break
            if until is not None and now >= until:                       # rule 8, every row: nothing starts after its time
                halt(i, "stopped: its time was over; the rest were not sent")
                break
            if budget_s is not None and time.time() - t_start > budget_s:
                res["left"] += 1
                continue
            mob = row.get("mobile") or ""
            hold = row.get("hold") or ""                                 # rule 2
            if not hold and key in L.TICK and not row.get("tick"):
                hold = "not for sending"
            if not hold and not L.m10(mob):
                hold = "no mobile number on record"
            if not hold:
                st, serr = L.stops()                                     # rule 3: read again, now
                if serr:
                    halt(i, "stopped: %s" % serr)
                    break
                if mob in st:
                    hold = "replied STOP"
            if not hold:
                plog2, perr = portal_log()                               # rules 4 and 5: read again, now
                if perr:
                    halt(i, "stopped: %s" % perr)
                    break
                hold = _other_page(plog2, mob, tpl, ref, day, dated=(key != "post_visit"))
            if not hold:
                if con.execute("SELECT 1 FROM send_row WHERE day=? AND mobile=?", (day, mob)).fetchone():
                    hold = "this number already had a message tried today"
                elif con.execute("SELECT 1 FROM send_row WHERE list=? AND mobile=? AND ref_date=?", (key, mob, ref)).fetchone():
                    hold = "this reminder was already tried for this date"
            vals = None
            if not hold:
                vals, hold = values_for(key, row, day)
            rid = None
            if not hold:
                # ---- rules 9 and 6 in ONE transaction: the day's count and the written-ahead row. From the commit on, this
                # row is never tried again, whatever happens.
                try:
                    con.execute("BEGIN IMMEDIATE")
                    if con.execute("SELECT COUNT(*) FROM send_row WHERE day=?", (day,)).fetchone()[0] >= CEILING:
                        con.rollback()
                        hold = "the day's ceiling of %d messages was reached" % CEILING
                        res["note"] = "the day's ceiling of %d was reached; the rest were held" % CEILING
                    else:
                        cur = con.execute("INSERT INTO send_row(day, list, mobile, cid, name, ref_date, template, state, reason, at, by) VALUES (?,?,?,?,?,?,?,'trying','',?,?)",
                                          (day, key, mob, row.get("cid") or "", clean_name(row.get("name")), ref, tpl, _stamp(now), str(by or "")[:40]))
                        rid = cur.lastrowid
                        con.commit()
                except sqlite3.IntegrityError:                           # another run wrote this number or this date first
                    con.rollback()
                    hold = "another run was already sending to this number"
            if hold:
                _hold(con, now, day, key, row, hold)
                res["held"] += 1
                continue
            try:
                r = _sender()(mob, tpl, vals, "wa_ladder:" + key, key_, dry_run=False, timeout=timeout) or {}   # rule 7: ONE request
            except Exception as e:                                       # noqa: BLE001 -- the row stays 'trying'; the batch stops (F-1313)
                con.execute("UPDATE send_row SET reason=?, done_at=? WHERE id=?", ("the sender broke (%s)" % type(e).__name__, _stamp(now_fn()), rid))
                con.commit()
                res["failed"] += 1
                halt(i + 1, "stopped: the sender broke (%s). Tell Claude." % type(e).__name__)
                break
            done = _stamp(now_fn())
            if r.get("ok") and r.get("mode") == "LIVE":
                con.execute("UPDATE send_row SET state='sent', done_at=?, message_id=? WHERE id=?",
                            (done, re.sub(r"[^A-Za-z0-9_.:-]", "", str(r.get("message_id") or ""))[:80], rid))
                con.commit()
                res["sent"] += 1
                bad_run = 0
                continue
            res["failed"] += 1
            bad_run += 1
            state, why, every = _why(r)                                  # fixed sentences only: nothing that came back is kept
            con.execute("UPDATE send_row SET state=?, reason=?, done_at=? WHERE id=?", (state, why, done, rid))
            con.commit()
            if every or bad_run >= 2:
                halt(i + 1, "stopped after %s; the rest were not tried. Tell Claude." % (why if every else "two refusals in a row"))
                break
    finally:
        con.close()
    return res


# ------------------------------------------------------------------ the timed run (cron, every 5 minutes)
def tick(now_fn=None):
    """Each list whose switch is ON goes once a day, at its time or within WINDOW_MIN after it. One timed run at a time
    (a lock taken here, so a run by hand or by the installer cannot overlap the cron's). Returns the lines to log."""
    now_fn = now_fn or L.now_ist
    lines = []
    if os.path.exists(ALL_OFF):
        return lines
    try:
        lock = open(RUN_LOCK, "a")
    except OSError:
        return ["%s the timed run could not open its lock %s -- nothing was done" % (_stamp(now_fn())[:16], RUN_LOCK)]
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return lines                                                 # another timed run is going
        for key in AUTO:
            try:
                line = _tick_one(key, now_fn)
            except sqlite3.Error as e:                                   # the store busy or broken: said, tried again at the next tick
                line = "%s %s could not run (%s)" % (_stamp(now_fn())[:16], key, type(e).__name__)
            if line:
                lines.append(line)
    finally:
        lock.close()
    return lines


def _tick_one(key, now_fn):
    now = now_fn()
    day = now.strftime("%Y-%m-%d")
    con = store()
    try:
        r = con.execute("SELECT is_on, at FROM send_switch WHERE list=?", (key,)).fetchone()
        ran = con.execute("SELECT 1 FROM send_run WHERE day=? AND list=?", (day, key)).fetchone()
    finally:
        con.close()
    if not (r and r[0]) or ran:
        return ""
    h, mi = TIMES[key]
    t0 = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    t1 = t0 + dt.timedelta(minutes=WINDOW_MIN)
    if now < t0:
        return ""
    if str(r[1] or "") >= _stamp(t1 - dt.timedelta(minutes=LATE_ON_MIN)):
        return ""                                                        # switched on at the end of, or after, today's time: it starts tomorrow
    if now >= t1:
        con = store()
        try:
            w = L._meta(con, "send_wait_" + key, "")
            why = w.split("|", 1)[1] if w.startswith(day + "|") else "it did not go between %s and %s" % (_at(key), _hm(_stamp(t1)))
            con.execute("INSERT OR IGNORE INTO send_run(day, list, state, at, note) VALUES (?,?,'skipped',?,?)", (day, key, _stamp(now), ("not sent today: %s" % why)[:200]))
            con.commit()
        finally:
            con.close()
        return "%s %s SKIPPED today: %s" % (_stamp(now)[:16], key, why)
    res = send_list(key, "timer", now_fn=now_fn, until=t1)
    con = store()
    try:
        if res["again"]:
            L._set(con, "send_wait_" + key, day + "|" + res["note"])
            con.commit()
            return ""
        state = "stopped" if res["stopped"] else "done"
        con.execute("INSERT OR REPLACE INTO send_run(day, list, state, at, note, sent, failed, held) VALUES (?,?,?,?,?,?,?,?)",
                    (day, key, state, _stamp(now_fn()), (res["stopped"] or res["note"])[:200], res["sent"], res["failed"], res["held"]))
        con.commit()
    finally:
        con.close()
    return "%s %s %s: %d sent, %d not sent, %d held%s" % (_stamp(now)[:16], key, state.upper(), res["sent"], res["failed"], res["held"],
                                                         (" -- " + (res["stopped"] or res["note"])) if (res["stopped"] or res["note"]) else "")


def send_ticked(tokens, day, by, now_fn=None):
    """The long-overdue names the doctor ticked. (ok, text)."""
    now_fn = now_fn or L.now_ist
    now = now_fn()
    if day != now.strftime("%Y-%m-%d"):
        return False, "That list is not today's. Open today's page and tick again. Nothing was sent."
    if not (TICK_HOURS[0] <= now.hour < TICK_HOURS[1]):
        return False, "It is outside 8 am - 9 pm. Nothing was sent; press again in the day."
    if isinstance(tokens, list) and len(tokens) > MAX_TICKED:
        return False, "At most %d names at a time. Untick some and press again. Nothing was sent." % MAX_TICKED
    if not (isinstance(tokens, list) and tokens and all(isinstance(t, str) and re.match(r"^[0-9a-f]{20}$", t) for t in tokens)):
        return False, "Nothing was ticked. Nothing was sent."
    res = send_list("overdue", by, now_fn=now_fn, only=set(tokens), budget_s=PAGE_BUDGET_S, timeout=12,
                    until=now.replace(hour=TICK_HOURS[1], minute=0, second=0, microsecond=0))
    if res["again"]:
        return False, "Nothing was sent: %s." % res["note"]
    if res["stopped"] and not (res["sent"] or res["failed"] or res["held"]):
        return False, res["stopped"]
    text = "%d sent" % res["sent"]
    if res["failed"]:
        text += ", %d not sent" % res["failed"]
    if res["held"]:
        text += ", %d held" % res["held"]
    if res["left"]:
        text += ", %d not started (tick and press again)" % res["left"]
    if res["stopped"]:
        text += ". " + res["stopped"]
    return True, text + "."


# ------------------------------------------------------------------ for the page
def door(what, d, who, now_fn=None):
    """Every change the page can ask for. (ok, text). The request carries a list's key and row tokens only -- never a
    number, a name or words; those come from the server's own record."""
    if not owner_ok(who):
        return False, "Only the doctor's own login can do this."
    by = str((who or {}).get("user") or "doctor")
    now = (now_fn or L.now_ist)()
    key = str(d.get("list") or "")
    if what == "switch":
        return set_switch(key, d.get("on") is True, by, now)
    if what == "stopall":
        return stop_all(by, now)
    if what == "test":
        return send_test(key, by, now)
    if what == "testok":
        return confirm_test(key, by, now)
    if what == "ticked":
        return send_ticked(d.get("tokens"), str(d.get("day") or ""), by, now_fn)
    return False, "there is no such door"


def _preview(key, day):
    try:
        import portal_wa
        t = portal_wa.TEMPLATES[TPL[key]]["preview"]
        for k, v in (sample_values(key, day) or {}).items():
            t = t.replace("{%s}" % k, v)
        return t
    except Exception:                                                    # noqa: BLE001
        return ""


def decorate(p, who=None, now=None):
    """Add to wa_ladder's plan what the page needs about the sending: the switches, the tests, today's record, and for
    today's rows a token and what happened to each."""
    now = now or L.now_ist()
    today = now.strftime("%Y-%m-%d")
    m, mtext = mode()
    con = store()
    try:
        sw = dict(con.execute("SELECT list, is_on FROM send_switch"))
        sw_at = dict(con.execute("SELECT list, at FROM send_switch"))
        tests = {r[0]: {"sent_at": r[1], "ok": bool(r[2]), "mode": r[3], "error": r[4], "confirmed": bool(r[5]), "confirmed_at": r[5]}
                 for r in con.execute("SELECT list, sent_at, ok, mode, error, confirmed_at FROM send_test")}
        runs = {r[0]: {"state": r[1], "at": r[2], "note": r[3], "sent": r[4], "failed": r[5], "held": r[6]}
                for r in con.execute("SELECT list, state, at, note, sent, failed, held FROM send_run WHERE day=?", (today,))}
        tried = con.execute("SELECT list, mobile, cid, name, state, reason, at, done_at FROM send_row WHERE day=? ORDER BY id", (today,)).fetchall()
        holds = {(r[0], r[1], r[2]): r[3] for r in con.execute("SELECT list, cid, mobile, reason FROM send_hold WHERE day=?", (today,))}
        tm = test_mobile(con)
        waits = {k: L._meta(con, "send_wait_" + k, "") for k in AUTO}
    finally:
        con.close()

    def said(state, reason, at, done):
        if state == "sent":
            return {"k": "ok", "t": "Sent %s" % _hm(done or at)}
        if state == "failed":
            return {"k": "no", "t": "Not sent: %s. Not tried again." % reason}
        return {"k": "no", "t": "May have gone at %s; no clear answer came back. Not tried again." % _hm(at)}

    by_mob = {(r[0], r[1]): r for r in tried}
    lists = {}
    for key, title, _w, tpl in L.LISTS:
        h_m = TIMES.get(key)
        over = late_on = False
        if h_m:
            t1 = now.replace(hour=h_m[0], minute=h_m[1], second=0, microsecond=0) + dt.timedelta(minutes=WINDOW_MIN)
            over = now >= t1
            late_on = bool(sw.get(key)) and str(sw_at.get(key) or "") >= _stamp(t1 - dt.timedelta(minutes=LATE_ON_MIN))
        w = waits.get(key, "")
        lists[key] = {"auto": key in AUTO, "on": bool(sw.get(key)), "at": _at(key) if h_m else "", "when": WHEN[key], "template": tpl,
                      "test": tests.get(key) or {"sent_at": "", "ok": False, "mode": "", "error": "", "confirmed": False, "confirmed_at": ""},
                      "run": runs.get(key), "over": over, "late_on": late_on, "wait": w.split("|", 1)[1] if w.startswith(today + "|") and key not in runs else "",
                      "preview": _preview(key, today)}
    if p.get("day") == today:
        for x in p["lists"]:
            for r in x["rows"]:
                r["token"] = token(today, x["key"], r)
                t = by_mob.get((x["key"], r.get("mobile") or ""))
                if t:
                    r["sent"] = said(t[4], t[5], t[6], t[7])
                elif (x["key"], r.get("cid") or "", r.get("mobile") or "") in holds and not r.get("hold"):
                    r["sent"] = {"k": "no", "t": "Not sent: %s" % holds[(x["key"], r.get("cid") or "", r.get("mobile") or "")]}
    record = [{"name": r[3], "cid": r[2], "mobile": r[1], "list": TITLE.get(r[0], r[0]), "said": said(r[4], r[5], r[6], r[7])} for r in tried]
    p["send"] = {"ok": True, "version": VERSION, "today": today, "is_today": p.get("day") == today, "mode": m, "mode_text": mtext,
                 "owner": owner_ok(who), "ceiling": CEILING, "sent_today": sum(1 for r in tried if r[4] == "sent"), "tried_today": len(tried),
                 "test_last4": tm[-4:] if tm else "", "lists": lists, "record": record,
                 "tick_hours": "8 am - 9 pm", "max_ticked": MAX_TICKED}
    p["sends"] = True
    return p


def status():
    """One line, counts only."""
    m, _t = mode()
    try:
        con = store()
        try:
            on = sum(1 for k in AUTO if _is_on(con, k))
            okt = sum(1 for k in TPL if _test_ok(con, k))
            day = L.now_ist().strftime("%Y-%m-%d")
            n = con.execute("SELECT COUNT(*), COALESCE(SUM(state='sent'),0) FROM send_row WHERE day=?", (day,)).fetchone()
            tm = test_mobile(con)
        finally:
            con.close()
    except sqlite3.Error as e:
        return "ERROR the store could not be read (%s)" % type(e).__name__
    rows, perr = portal_log()
    return "ok mode %s . switches ON %d of %d . tests confirmed %d of %d . today %d tried, %d sent (ceiling %d) . the doctor's number %s . the portal's send log %s" % (
        m, on, len(AUTO), okt, len(TPL), n[0], n[1], CEILING, ("set (....%s)" % tm[-4:]) if tm else "NOT SET",
        ("NOT READABLE: " + perr) if perr else "readable (%d rows that went)" % len(rows))


def contract():
    """(ok, text) -- does the portal's sender take exactly what this file hands it? Read from the live portal_wa.py: its
    arguments, the six messages and their fields, the columns of its log. Nothing is sent."""
    import inspect
    try:
        import portal_wa
    except Exception as e:                                               # noqa: BLE001
        return False, "the portal's sender could not be loaded (%s)" % type(e).__name__
    want = ["phone", "template_name", "values", "sent_by", "token", "dry_run", "timeout"]
    got = list(inspect.signature(portal_wa.send).parameters)
    if got != want:
        return False, "the portal's sender takes %s, not %s" % (got, want)
    for k in TPL:
        t = portal_wa.TEMPLATES.get(TPL[k])
        if not t:
            return False, "the portal's sender does not know the message %s" % TPL[k]
        v = sample_values(k, "2026-01-15")
        if sorted(v) != sorted(f["key"] for f in t["fields"]):
            return False, "the message %s wants the fields %s; this file sends %s" % (TPL[k], sorted(f["key"] for f in t["fields"]), sorted(v))
        try:
            portal_wa.build_body(TPL[k], v)
        except ValueError as e:
            return False, "the message %s could not be filled (%s)" % (TPL[k], e)
    if not {"ts_ist", "phone", "template", "values_json", "mode", "ok", "error"} <= set(portal_wa.LOG_COLS):
        return False, "the portal's send log does not have the columns this file reads"
    return True, "the portal's sender takes this file's calls: 7 arguments, %d messages with their fields, the log's columns" % len(TPL)


def selftest():
    d = [("13 Nov 2026", "2026-11-13"), ("13-Nov-2026", "2026-11-13"), ("13/11/2026", "2026-11-13"), ("2026-11-13 10:30", "2026-11-13"),
         ("13 November 2026, 10:30 AM", "2026-11-13"), ("Ram", ""), ("", ""), ("31/02/2026", ""), ("3.1.2027", "2027-01-03")]
    ok = all(parse_date(a) == b for a, b in d) and parse_dates("3/4/2027") == {"2027-04-03", "2027-03-04"} and parse_dates("13/11/2026") == {"2026-11-13"}
    ok = ok and _why({"mode": "LIVE", "error": "HTTP 401: " + "secret"})[1:] == ("WhatsApp refused it (HTTP 401)", True) and _why({"mode": "LIVE", "error": "HTTP 400: x"})[2] is False
    ok = ok and _why({"mode": "LIVE", "error": "HTTP 504: x"})[0] == "unsure" and _why({"mode": "LIVE", "error": "send failed: x"})[0] == "unsure"
    ok = ok and _hm("2026-11-13 18:02:10") == "6:02 pm" and _hm("2026-11-13 00:05:00") == "12:05 am" and _at("due1") == "10:00 am"
    ok = ok and clean_name("  RAM   KUMAR ") == "RAM KUMAR" and clean_name("?") == "" and clean_name("12345") == ""
    ok = ok and values_for("overdue", {"name": "A B"}, "2026-11-13")[0] == {"1": "A B", "2": "30 Oct 2026", "3": "14"}
    ok = ok and values_for("appt", {"name": "A", "date": "14 Nov 2026 18:45"}, "2026-11-13")[0] == {"var_1": "A", "var_2": "14 Nov 2026, 6:45 PM"}
    ok = ok and set(AUTO) == set(TIMES) and "overdue" not in AUTO and _mask("x " + "98765" + "43210 y") == "x #3210 y"
    return ok


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        good = selftest()
        print("selftest", "OK" if good else "RED")
        sys.exit(0 if good else 1)
    if "--tick" in a:
        for line in tick():
            print(line, flush=True)
        sys.exit(0)
    if "--contract" in a:
        good, text = contract()
        print(("ok " if good else "ERROR ") + text)
        sys.exit(0 if good else 1)
    if "--stop-all" in a:
        good, text = stop_all("installer")
        print(("ok " if good else "ERROR ") + text)
        sys.exit(0 if good else 1)
    if "--status" in a:
        s = status()
        print(s)
        sys.exit(0 if s.startswith("ok") else 1)
    if "--set-test-mobile" in a:
        i = a.index("--set-test-mobile")
        good, text = set_test_mobile(a[i + 1] if len(a) > i + 1 else "")
        print(("ok " if good else "ERROR ") + text)
        sys.exit(0 if good else 1)
    print(__doc__)
