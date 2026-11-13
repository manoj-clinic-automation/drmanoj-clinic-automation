#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docterz_missing_alert.py -- kit S811_FEED_ON_ARRIVAL, build 2 (session S443, 13-Nov-2026, the parent). NEW.

WHY. Reception exports two Docterz reports every evening after 9 pm: the consultation report and the follow-up log. The server
picks them up from Drive every 15 minutes (/root/finance/docterz_pickup.py) and records each in finance.db, table docterz_export.
When one does not come, the staff page says so (Aaj ka kaam) -- but the OWNER hears nothing until the next day's lists are short.

WHAT IT DOES. Run by cron twice:
  * 21:45 Monday-Saturday (--slot evening): is TODAY's consultation report on the server, and a follow-up log of today that
    reaches the next call day?  If not: ONE notification to the owner, in English, naming which is missing and the day.
  * 08:15 Monday-Saturday (--slot morning): the same question about the LAST WORKING DAY (Tuesday-Saturday: yesterday; Monday:
    Saturday); one more notification if it is still missing. Nothing is ever said on a Sunday.
"Reached the server" is the staff page's own rule, read from /root/finance/aaj_kaam.py (_exports_confirmed) and aaj_duties.json
(reception.night_exports) and not re-invented:
    consultation:  a row kind='consultation', business_date = the day, status='current'
    follow-up log: a row kind='followup',     business_date = the day, status='current', whose due_to is blank or reaches the
                   next call day (the day after, Sunday skipped) -- a short log is not a done export (S507).
A DAY THE CLINIC DID NOT WORK says nothing. The sign of work: a slip logged in the chamber that day (finance.db, table slip,
state='ok' -- Shavez's parchi log, which does not depend on Docterz), or either export of that day on the server (somebody
exported). Neither report and no sign of work = no notification.
An export landing in the pickup pass that runs at the same minute is waited for (the pass's own lock) before anything is said.
ONE notification per report-day per slot: a small state file beside this script, written under its own lock (two runs at the
same instant: the second says so and sends nothing). The slot is taken BEFORE the push, so a run stopped mid-way can never send
twice -- the next run then says "slot taken, outcome not known" and sends nothing more. A notification nothing took is not
counted as told.

HOW IT REACHES THE OWNER. The portal's own Web Push -- ring_common.push_user, the road /root/portal/callback_clock.py (S796) uses
for its closing-time count -- to the same login it uses for the owner. When no device takes it, it is tried twice more, 60
seconds apart; after the third, the private ntfy topic the morning freshness alarm uses (NTFY_URL in /root/finance/freshness.conf,
read the way freshness.py reads it and posted the way owner_notice.py posts it; never printed). No number, key or address is in
this file. (ring_common drops a device from its own list when the push service says that device is gone -- its doing, as on
every push.)

It only READS finance.db (opened read-only; a busy store is tried three times). It writes its state file (and its .lock) and its
lines on stdout (cron appends them to docterz_missing_alert.log): one line per run, plus one per push that nothing took. Any
error = one line, exit 0, nothing sent. The message carries no patient data.
Off switch: /root/finance/_off/ALL_OFF or /root/finance/_off/DOCTERZ_MISSING_ALERT_OFF.

CLI:  docterz_missing_alert.py --slot evening|morning      the run (what cron calls)
      docterz_missing_alert.py --dry [--slot S] [--date YYYY-MM-DD]   what it WOULD send; sends nothing, writes nothing
      docterz_missing_alert.py --probe [--date YYYY-MM-DD]  one line: can the exports and the slips be read, how many devices
                                                            the owner's login has, is the ntfy topic set (the installer's gate)
      --date sets "today", judged at the slot's own time, and ALWAYS means --dry: a dated run sends nothing and writes nothing.
      (Only the kit's walk can make a dated run send, to its own stand-in: DMA_TEST_SEND=1 together with its own DMA_STATE.)
      --slot defaults by the clock (before 13:00 = morning).
Stdlib only (+ ring_common from /root/portal for the push: absent = judged, said in the line, the ntfy topic tried).
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time

VERSION = "S811 2"
HERE = os.path.dirname(os.path.abspath(__file__))
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", HERE)
FINANCE_DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
OFF_DIR = os.environ.get("FINANCE_OFF_DIR", "/root/finance/_off")
OFF_NAMES = ("ALL_OFF", "DOCTERZ_MISSING_ALERT_OFF")
STATE = os.environ.get("DMA_STATE", os.path.join(HERE, "docterz_missing_alert_state.json"))
PICKUP_LOCK = os.environ.get("DMA_PICKUP_LOCK", "/tmp/docterz_pickup.lock")      # the pickup's cron line: flock -n on this file
NTFY_CONF = os.environ.get("DMA_NTFY_CONF", "/root/finance/freshness.conf")       # KEY=VALUE, 0600; NTFY_URL (freshness.py)
SETTLE_S = 30                                      # the cron run waits this long, then for the pickup's lock, before it says "missing"
LOCK_WAIT_S = 150
PUSH_TRIES = 3                                     # the cron run: three pushes at most ...
PUSH_WAIT_S = 60                                   # ... this far apart
MAX_RUN_S = 420                                    # no new try is begun once a run would pass this
OWNER = ("manoj",)                                 # callback_clock.OWNER -- the owner's portal login
OWNER_URL = "/finance/console"                     # his command console
KEEP_DAYS = 60
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
NAMES = {"consultation": "the consultation report", "followup": "the follow-up log"}
# the three reads, each used by the run AND by --probe (the installer runs the probe against the live store before placing)
CONS_SQL = ("SELECT 1 FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' "
            "ORDER BY id DESC LIMIT 1")
FU_SQL = "SELECT 1%s FROM docterz_export WHERE kind='followup' AND business_date=? AND status='current' ORDER BY id DESC LIMIT 1"
SLIP_SQL = "SELECT COUNT(*) FROM slip WHERE day=? AND state='ok'"
_NONE = object()


def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None)


def next_call_day(day):
    """The day after `day`, Sunday skipped (docterz_pickup.next_call_day; aaj_kaam._exports_confirmed)."""
    d = day + dt.timedelta(days=1)
    return d + dt.timedelta(days=1) if d.weekday() == 6 else d


def report_day(slot, today):
    """The day a slot speaks about; None on a Sunday (nothing is said on a Sunday). The morning speaks about the last working
    day: yesterday, and on a Monday the Saturday before."""
    if today.weekday() == 6:
        return None
    if slot == "morning":
        d = today - dt.timedelta(days=1)
        return d - dt.timedelta(days=1) if d.weekday() == 6 else d
    return today


def off_switch(off_dir=None):
    for name in OFF_NAMES:
        p = os.path.join(off_dir or OFF_DIR, name)
        if os.path.exists(p):
            return p
    return ""


def read_day(db, day):
    """What finance.db holds for one day. Read-only. Raises sqlite3.Error when docterz_export cannot be read."""
    iso = day.isoformat()
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=10)
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(docterz_export)")}
        if not cols:
            raise sqlite3.OperationalError("no table docterz_export")
        first = con.execute("SELECT MIN(business_date) FROM docterz_export WHERE business_date<>''").fetchone()[0] or ""
        c = con.execute(CONS_SQL, (iso,)).fetchone()
        f = con.execute(FU_SQL % (", due_to" if "due_to" in cols else ""), (iso,)).fetchone()
        due_to = str(f[1] or "") if (f and len(f) > 1) else ""
        short = bool(f and due_to and due_to < next_call_day(day).isoformat())      # a short log is not a done export (S507)
        try:
            slips = int(con.execute(SLIP_SQL, (iso,)).fetchone()[0] or 0)
        except sqlite3.Error:
            slips = None                                                           # no slip table: no sign either way
        return {"first": first, "cons": bool(c), "fu_row": bool(f), "fu": bool(f) and not short,
                "short_to": due_to if short else "", "slips": slips}
    finally:
        con.close()


def read_day_patiently(db, day, tries=1, sleep=time.sleep, wait_s=5):
    """read_day, tried again when finance.db is busy (many jobs start at the same minute)."""
    tries = max(1, int(tries))
    for i in range(tries):
        try:
            return read_day(db, day)
        except sqlite3.OperationalError:
            if i + 1 >= tries:
                raise
            sleep(wait_s)


def judge(st):
    """(missing kinds, worked, sign) -- the clinic worked when the consultation report came, when any follow-up log of the day
    came, or when a slip was logged that day."""
    missing = [k for k, ok in (("consultation", st["cons"]), ("followup", st["fu"])) if not ok]
    signs = []
    if st["cons"]:
        signs.append("the consultation report came")
    if st["fu_row"]:
        signs.append("a follow-up log came")
    if st["slips"]:
        signs.append("%d slip%s logged" % (st["slips"], "" if st["slips"] == 1 else "s"))
    return missing, bool(signs), ", ".join(signs)


def _dnm(d):
    return "%s %d %s" % (d.strftime("%a"), d.day, d.strftime("%b"))


def _clock(t):
    return "%d:%02d %s" % (t.hour % 12 or 12, t.minute, "am" if t.hour < 12 else "pm")


def wording(slot, day, now, st):
    """(title, body) in plain English. Every sentence is either a fact read from the store or an 'unless / until' -- nothing
    that a later export could make false. Both always name the day they are about (a push can land late). No patient data:
    day names and dates, the two report names, nothing else."""
    today = now.date()
    morning = slot == "morning"
    cons_missing, fu_missing, short_to = not st["cons"], not st["fu_row"], st["short_to"]
    two = cons_missing and (fu_missing or bool(short_to))                 # two things to name: no bare "it"
    short_txt = ""
    if short_to:
        try:
            short_txt = _dnm(dt.date.fromisoformat(short_to[:10]))
        except ValueError:
            short_txt = "an early date"
    if cons_missing and fu_missing:
        lead = "Neither the consultation report nor the follow-up log has come from reception."
    elif cons_missing and short_to:
        lead = "The consultation report has not come from reception, and the follow-up log that came reaches only %s." % short_txt
    elif cons_missing:
        lead = "The consultation report has not come from reception; the follow-up log has."
    elif fu_missing:
        lead = "The follow-up log has not come from reception; the consultation report has."
    else:
        lead = "The follow-up log that came from reception reaches only %s; the consultation report has come." % short_txt
    call = next_call_day(day)
    effects = []
    if morning:
        whose = "today's" if call == today else (call.strftime("%A") + "'s")
        if cons_missing:
            effects.append("Until %s comes, that day's visits are not on record." % ("the consultation report" if two else "it"))
        if fu_missing:
            effects.append("Until %s comes, %s calling list is made from the last log." % ("the follow-up log" if two else "it", whose))
        elif short_to:
            effects.append("Until a longer %s comes, %s calling list is short." % ("follow-up log" if two else "one", whose))
        title = "Docterz export still missing (%s)" % _dnm(day)
        lead = "Still missing this morning from %s %d %s: %s%s" % (day.strftime("%A"), day.day, day.strftime("%b"), lead[0].lower(), lead[1:])
    else:
        if call == today + dt.timedelta(days=1):
            when, whose = "tonight", "tomorrow's"
        else:
            when, whose = "before %s morning" % call.strftime("%A"), call.strftime("%A") + "'s"
        if cons_missing:
            effects.append("Unless %s comes tonight, today's visits will not be on record tomorrow morning."
                           % ("the consultation report" if two else "it"))
        if fu_missing:
            effects.append("Unless %s comes %s, %s calling list will be made from the last log." % ("the follow-up log" if two else "it", when, whose))
        elif short_to:
            effects.append("Unless a longer %s comes %s, %s calling list will be short." % ("follow-up log" if two else "one", when, whose))
        title = "Docterz export missing at %s (%s)" % (_clock(now), _dnm(day))
    return title, " ".join([lead] + effects)


def load_state(path):
    """{'told': {'<day>|<slot>': {...}}}. A file that cannot be read is set aside and a fresh one started (said in the line)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and isinstance(d.get("told"), dict):
            return d, ""
        raise ValueError("not this script's state")
    except FileNotFoundError:
        return {"told": {}}, ""
    except Exception as e:                               # noqa: BLE001
        try:
            os.replace(path, path + ".unreadable")
        except OSError:
            pass
        return {"told": {}}, " (the state file could not be read -- %s -- set aside, a fresh one started)" % type(e).__name__


def save_state(path, d, today):
    keep = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
    d["told"] = {k: v for k, v in d["told"].items() if str(k)[:10] >= keep}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def take_lock(state):
    """(fd, '') when this run holds the state's lock; (None, 'busy') when another run holds it; (None, 'error') when the lock
    file cannot be made. Released by closing fd."""
    try:
        import fcntl                                     # noqa: PLC0415
        fd = os.open(state + ".lock", os.O_CREAT | os.O_RDWR, 0o600)
    except Exception:                                    # noqa: BLE001
        return None, "error"
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd, ""
    except OSError:
        os.close(fd)
        return None, "busy"


def get_pusher(pusher=None):
    """callback_clock.get_pusher: the portal's own push, or None when it cannot be loaded."""
    if pusher is not None:
        return pusher
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import ring_common as rc                         # noqa: PLC0415
        return rc.push_user
    except Exception:                                    # noqa: BLE001
        return None


def device_count(user=None):
    """How many devices the owner's login has allowed (ring_common.subs_for); None when that cannot be asked."""
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import ring_common as rc                         # noqa: PLC0415
        return len(rc.subs_for(user or OWNER[0]))
    except Exception:                                    # noqa: BLE001
        return None


def push(pusher, who, title, body, tag):
    s = f = 0
    for w in who:
        try:
            a, b = pusher(w, {"title": title, "body": body, "url": OWNER_URL, "tag": tag, "ttl": 43200,
                              "requireInteraction": True, "renotify": True})
            a, b = int(a or 0), int(b or 0)
        except Exception:                                # noqa: BLE001
            a, b = 0, 1
        s, f = s + a, f + b
    return s, f


def ntfy_url(conf=None):
    """NTFY_URL from the freshness conf, read the way freshness.load_conf reads it. '' when it is not there. Never printed."""
    try:
        with open(conf or NTFY_CONF, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "NTFY_URL":
                        return v.strip()
    except OSError:
        pass
    return ""


def send_ntfy(title, body, conf=None):
    """The fallback: one POST to the private ntfy topic (owner_notice._ntfy's own call). -> (went, how). The address is never
    in a line."""
    url = ntfy_url(conf)
    if not url:
        return False, "no ntfy topic is set in the freshness conf"
    try:
        import urllib.request                            # noqa: PLC0415
        req = urllib.request.Request(url, data=str(body).encode("utf-8"), method="POST",
                                     headers={"Title": str(title).encode("ascii", "replace").decode("ascii"),
                                              "Priority": "default", "Tags": "warning"})
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:                               # noqa: BLE001
        return False, "the ntfy topic did not take it (%s)" % type(e).__name__
    return True, "the ntfy topic took it"


def wait_for_pickup(settle, lock_path=None, lock_wait=LOCK_WAIT_S, sleep=time.sleep):
    """Let the pickup pass that started at this same minute finish: wait `settle` seconds, then until its lock is free."""
    if settle <= 0:
        return
    sleep(settle)
    try:
        import fcntl                                     # noqa: PLC0415
        fd = os.open(lock_path or PICKUP_LOCK, os.O_RDONLY)
    except Exception:                                    # noqa: BLE001 -- no lock file: no pass has ever run with it
        return
    try:
        end = time.time() + lock_wait
        while time.time() < end:
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
                return
            except OSError:
                sleep(3)
    finally:
        os.close(fd)


def run(slot, now=None, db=None, state=None, pusher=None, dry=False, off_dir=None, settle=0, lock_path=None, tries=1, sleep=time.sleep,
        push_tries=1, push_wait=PUSH_WAIT_S, ntfy=None, say=None, clock=time.monotonic, max_run=MAX_RUN_S):
    """One run. Returns {'line': the last log line ('' = say nothing), 'pushed': n, 'why': ..., 'progress': [earlier lines]}.
    Never raises on a bad store. push_tries / ntfy are what the cron run asks for (3 tries, the ntfy fallback); the default is
    one try and no fallback."""
    t0 = clock()
    now = now or now_ist()
    db = db or FINANCE_DB
    state = state or STATE
    today = now.date()
    day = report_day(slot, today)
    head = "%s%s %s" % ("DRY " if dry else "", now.strftime("%Y-%m-%d %H:%M"), slot)
    res = {"slot": slot, "day": day.isoformat() if day else "", "pushed": 0, "missing": [], "line": "", "progress": []}

    def note(text):
        res["progress"].append(text)
        if say is not None:
            say(text)

    off = off_switch(off_dir)
    if off:
        res["why"] = "off"
        res["line"] = (head + ": the off switch %s is there -- nothing would be sent" % off) if dry else ""
        return res
    if day is None:
        res["why"] = "sunday"
        res["line"] = head + ": a Sunday -- no export is due, nothing is said on a Sunday"
        return res
    head += ", report day %s" % day.isoformat()
    try:
        st = read_day_patiently(db, day, tries, sleep)
        missing, worked, sign = judge(st)
        if missing and not dry and settle > 0:
            wait_for_pickup(settle, lock_path, sleep=sleep)
            st = read_day_patiently(db, day, tries, sleep)
            missing, worked, sign = judge(st)
    except Exception as e:                               # noqa: BLE001
        res["why"] = "unreadable"
        res["line"] = head + ": finance.db could not be read (%s) -- nothing judged, nothing sent" % type(e).__name__
        return res
    res["missing"] = missing
    if not st["first"] or day.isoformat() < st["first"]:
        res["why"] = "before"
        res["line"] = head + ": before the first export the server ever took -- nothing judged"
        return res
    if not missing:
        res["why"] = "both"
        res["line"] = head + ": both reports reached the server -- nothing sent"
        return res
    what = " and ".join(("a follow-up log that reaches the next call day" if (k == "followup" and st["short_to"]) else NAMES[k])
                        for k in missing)
    if not worked:
        res["why"] = "no_work"
        res["line"] = head + (": %s not on the server, and no sign the clinic worked (no slip logged that day%s) -- taken as a "
                              "closed day, nothing sent" % (what, "" if st["slips"] is not None else "; the slip table could not be read"))
        return res
    title, body = wording(slot, day, now, st)
    res["title"], res["body"] = title, body
    key = "%s|%s" % (day.isoformat(), slot)
    if dry:
        told = False
        try:
            if os.path.isfile(state):
                with open(state, "r", encoding="utf-8") as fh:
                    d = json.load(fh)
                told = isinstance(d, dict) and isinstance(d.get("told"), dict) and key in d["told"]
        except Exception:                                # noqa: BLE001
            told = False
        res["why"] = "dry"
        res["line"] = head + ": %s not on the server (%s) -- %s to %s: %s | %s -- nothing sent, nothing written" % (
            what, sign, "this slot is already taken; WOULD NOT send again" if told else "WOULD SEND", OWNER[0], title, body)
        return res
    fd, why_not = take_lock(state)
    if fd is None:
        if why_not == "busy":
            res["why"] = "busy"
            res["line"] = head + ": %s not on the server -- another run of this script holds the state at this moment; it speaks, this one sends nothing" % what
        else:
            res["why"] = "state"
            res["line"] = head + ": %s not on the server -- the state file's lock could not be made beside %s, so NOTHING SENT" % (what, state)
        return res
    try:
        d, note_state = load_state(state)
        entry = d["told"].get(key, _NONE)
        if entry is not _NONE:
            at = str(entry.get("at", "?")) if isinstance(entry, dict) else "?"
            if isinstance(entry, dict) and (entry.get("sent") or entry.get("ntfy")):
                res["why"] = "told"
                res["line"] = head + ": %s not on the server -- already told in this slot at %s, nothing sent%s" % (what, at, note_state)
            else:                                        # taken, never finished: a run was stopped between taking the slot and the push's answer
                res["why"] = "unknown"
                res["line"] = head + (": %s not on the server -- slot taken at %s, outcome not known (a run was stopped mid-way); "
                                      "nothing more is sent, so that it can never go twice%s" % (what, at, note_state))
            return res
        stamp = now.strftime("%Y-%m-%d %H:%M:%S")
        try:                                             # the slot is taken BEFORE the push: a crash after it can never send twice
            d["told"][key] = {"at": stamp, "missing": missing, "sent": None}
            save_state(state, d, today)
        except Exception as e:                           # noqa: BLE001
            res["why"] = "state"
            res["line"] = head + ": %s not on the server -- the state file could not be written (%s), so NOTHING SENT%s" % (
                what, type(e).__name__, note_state)
            return res
        p = get_pusher(pusher)
        sent = failed = 0
        n_try = 0
        push_tries = max(1, int(push_tries))
        if p is None:
            note(head + ": the portal's push (ring_common) could not be loaded")
        else:
            while True:
                n_try += 1
                sent, failed = push(p, OWNER, title, body, "docterz-missing-" + slot)
                if sent or n_try >= push_tries:
                    break
                if clock() - t0 + push_wait > max_run:
                    note(head + ": push %d of %d: no device took it (sent 0, failed %d) -- no time left for another try" % (n_try, push_tries, failed))
                    break
                note(head + ": push %d of %d: no device took it (sent 0, failed %d) -- trying again in %d seconds" % (n_try, push_tries, failed, push_wait))
                sleep(push_wait)
        went, how = (False, "")
        if not sent and ntfy is not None:
            try:
                went, how = ntfy(title, body)
            except Exception as e:                       # noqa: BLE001
                went, how = False, "the ntfy topic did not take it (%s)" % type(e).__name__
        res["pushed"], res["failed"], res["tries"], res["ntfy"] = sent, failed, n_try, bool(went)
        try:
            if sent or went:
                d["told"][key]["sent"] = sent
                if went:
                    d["told"][key]["ntfy"] = True
            else:
                del d["told"][key]                       # nothing took it: not told
            save_state(state, d, today)
        except Exception:                                # noqa: BLE001 -- the slot stays taken: never twice
            pass
        tried = "push %d of %d" % (n_try, push_tries) if p is not None else "no push"
        if sent:
            res["why"] = "pushed"
            res["line"] = head + ": %s not on the server (%s) -- told %s (%s): sent %d, failed %d%s" % (what, sign, OWNER[0], tried, sent, failed, note_state)
        elif went:
            res["why"] = "ntfy"
            res["line"] = head + ": %s not on the server (%s) -- no device took the push (%s); told by ntfy instead: %s%s" % (what, sign, tried, how, note_state)
        else:
            res["why"] = "undelivered" if p is not None else "no_pusher"
            res["line"] = head + ": %s not on the server (%s) -- NOT DELIVERED to %s (%s: sent 0, failed %d%s): nothing took it; not counted as told%s" % (
                what, sign, OWNER[0], tried, failed, ("; " + how) if how else "", note_state)
        return res
    finally:
        os.close(fd)


def probe(day=None, db=None):
    """One line for the installer: the three reads the run makes, tried on the live store; the owner's devices; the ntfy topic."""
    day = day or now_ist().date()
    out = []
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (db or FINANCE_DB), uri=True, timeout=10)
    except Exception as e:                               # noqa: BLE001
        return "PROBE exports=ERR(%s) slips=ERR(%s) devices=? ntfy=?" % (type(e).__name__, type(e).__name__)
    try:
        try:
            cols = {r[1] for r in con.execute("PRAGMA table_info(docterz_export)")}
            if not cols:
                raise sqlite3.OperationalError("no table")
            con.execute(CONS_SQL, (day.isoformat(),)).fetchone()
            con.execute(FU_SQL % (", due_to" if "due_to" in cols else ""), (day.isoformat(),)).fetchone()
            out.append("exports=ok")
        except Exception as e:                           # noqa: BLE001
            out.append("exports=ERR(%s)" % type(e).__name__)
        try:
            n = int(con.execute(SLIP_SQL, (day.isoformat(),)).fetchone()[0] or 0)
            out.append("slips=ok(%d)" % n)
        except Exception as e:                           # noqa: BLE001
            out.append("slips=ERR(%s)" % type(e).__name__)
    finally:
        con.close()
    n = device_count()
    out.append("devices=%s" % ("?" if n is None else n))
    out.append("ntfy=%s" % ("yes" if ntfy_url() else "no"))
    return "PROBE " + " ".join(out)


def main(argv=None):
    try:
        ap = argparse.ArgumentParser()
        ap.add_argument("--slot", choices=("evening", "morning"))
        ap.add_argument("--date")
        ap.add_argument("--dry", action="store_true")
        ap.add_argument("--probe", action="store_true")
        a = ap.parse_args(argv)
        if a.probe:
            print(probe(dt.date.fromisoformat(a.date) if a.date else None))
            return 0
        now = now_ist()
        slot = a.slot or ("morning" if now.hour < 13 else "evening")
        dated = bool(a.date)
        if dated:                                        # a set day is judged at the slot's own time
            now = dt.datetime.combine(dt.date.fromisoformat(a.date), dt.time(8, 15) if slot == "morning" else dt.time(21, 45))
        # a dated run sends nothing and writes nothing. The walk alone can lift that, and only onto a state file of its own.
        test_send = dated and os.environ.get("DMA_TEST_SEND") == "1" and bool(os.environ.get("DMA_STATE"))
        dry = a.dry or (dated and not test_send)
        live = not dry and not dated

        def knob(name, default):
            try:
                return int(os.environ.get(name, default))
            except ValueError:
                return default
        fallback = send_ntfy if (live or (test_send and os.environ.get("DMA_NTFY_CONF"))) else None
        res = run(slot, now=now, dry=dry, settle=knob("DMA_SETTLE", SETTLE_S) if live else 0, tries=3 if live else 1,
                  push_tries=1 if dry else PUSH_TRIES, push_wait=knob("DMA_PUSH_WAIT", PUSH_WAIT_S), ntfy=fallback,
                  say=lambda s: print(s, flush=True))
        if res.get("line") and not (res.get("why") == "off" and not a.dry):      # under the off switch only an asked-for --dry speaks
            print(res["line"])
    except SystemExit:
        raise
    except Exception as e:                               # noqa: BLE001 -- fail quiet and safe: one line, exit 0, nothing sent
        print("%s docterz_missing_alert: stopped on %s -- nothing sent" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), type(e).__name__))
    return 0


if __name__ == "__main__":
    sys.exit(main())
