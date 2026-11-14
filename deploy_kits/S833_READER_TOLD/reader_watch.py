#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reader_watch.py -- S833_READER_TOLD (F-1404; the Scan App chat, session 461, 14-Nov-2026). NEW file, this project's.

WHY: on 13-Nov the paper reader's key expired; the reader stopped itself ('stopped:the key was refused') and read nothing for about
21 hours, and nothing told the owner. Now a stopped reader is TOLD to him at once -- a push to his clinic app (the estate's one Web
Push road, portal's ring_common.push_user, as owner_notice and the order notices use it), else the private ntfy topic the morning
alarms use -- ONCE per stop; and once more when it reads again.

WHAT IT READS: the scan app's own switch, claude_reader.state(): 'on' | 'off' (his own tap: never announced) | 'stopped:<why>' |
'no key'. Nothing else. It writes only its own small state file (what it last told, and when) -- never the database.
    stopped / no key, not yet told for this stop  -> "Scan app · paper reader STOPPED" + why, in words, + what is needed
    on again, after a stop it told               -> "Scan app · paper reader reading again"
A message that could not go is tried again at the next run (every 5 minutes, cron).

NO WALK CAN REACH A PHONE: it sends only when the database it reads IS the live one (/root/assetapp/assets.db) and no stub is set
(READER_WATCH_STUB=<file> appends the message there instead).

OFF: /root/finance/_off/ALL_OFF (the estate's switch) or the scan app's setting reader_watch.on = off. To whom: the setting
reader_watch.to (default 'manoj').

    /root/wa/venv/bin/python3 -B /root/assetapp/reader_watch.py tick      (cron, every 5 minutes)
    /root/wa/venv/bin/python3 -B /root/assetapp/reader_watch.py show      (what it would say now; sends nothing, writes nothing)
    /root/wa/venv/bin/python3 -B /root/assetapp/reader_watch.py test      (one message -- the install's proof of the road)
"""
import datetime as dt
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE_DB = "/root/assetapp/assets.db"
DB = os.environ.get("ASSETS_DB", LIVE_DB)
STATE = os.environ.get("READER_WATCH_STATE", os.path.join(HERE, "reader_watch_state.json"))
ALL_OFF = os.environ.get("READER_WATCH_ALL_OFF", "/root/finance/_off/ALL_OFF")
PORTAL_DIR = "/root/portal"
NTFY_CONF = "/root/finance/freshness.conf"
URL = "/scanapp/admin"
WHY = {"the key has expired": "the reader's key has EXPIRED -- a new key (never expiring) is needed on the server",
       "the key was refused (expired or revoked)": "the reader's key was REFUSED -- it has expired or been revoked; a new key is needed",
       "the key was refused": "the reader's key was REFUSED -- it has expired or been revoked; a new key is needed",
       "the credit has run out": "the reader's CREDIT has run out -- the Anthropic account needs a top-up"}


def now_ist():
    return dt.datetime.utcnow() + dt.timedelta(minutes=330)


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return default if (r is None or r[0] is None) else str(r[0])
    except sqlite3.Error:
        return default


def reader_state(con):
    """The reader's own switch, through its own function (it also knows 'no key')."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import claude_reader                                             # noqa: PLC0415 -- the scan app's reader, read only
    return claude_reader.state(con)


def words(st):
    """(title, body) for a stop; plain words, never a key."""
    if st == "no key":
        why = "there is no reader key on the server"
    else:
        w = st.split(":", 1)[-1].strip()
        why = WHY.get(w) or ("it stopped itself: " + w)
    return ("Scan app · paper reader STOPPED",
            "The scan app is not reading new papers: %s. Scans wait unread until it is fixed (they are read again after)." % why)


def decide(st, told):
    """-> (title, body, what to remember) or None. told = what was last told ('' at first)."""
    stopped = st.startswith("stopped") or st == "no key"
    if stopped and told != st:
        t, b = words(st)
        return t, b, st
    if st == "on" and (told.startswith("stopped") or told == "no key"):
        return "Scan app · paper reader reading again", "The scan app's paper reader is on again; new scans are read as they come.", "on"
    return None


def load():
    try:
        with open(STATE, encoding="utf-8") as fh:
            d = json.load(fh)
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(d):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh)
    os.replace(tmp, STATE)


def _is_live():
    return os.path.realpath(DB) == os.path.realpath(LIVE_DB)


def _ntfy_url():
    url = ""
    try:
        with open(NTFY_CONF, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "NTFY_URL":
                        url = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return url


def send(title, body, to):
    """-> (sent, how). Never prints a URL, a key or an endpoint."""
    stub = os.environ.get("READER_WATCH_STUB", "")
    if stub:
        with open(stub, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(title=title, body=body, to=to), ensure_ascii=False) + "\n")
        return True, "stub"
    if not _is_live():
        return False, "not the live database -- nothing sent"
    payload = dict(kind="owner", title=title, body=body, url=URL, tag="scanapp-reader", ttl=86400, renotify=True,
                   ts=int(dt.datetime.now().timestamp() * 1000))
    sent, tried = 0, []
    for u in [x.strip().lower() for x in to.split(",") if x.strip()]:
        try:
            if PORTAL_DIR not in sys.path:
                sys.path.append(PORTAL_DIR)
            import ring_common as rc                                 # noqa: PLC0415 -- the estate's one Web Push road
            a, b = rc.push_user(u, payload)
            sent += int(a or 0)
            tried.append("%s %d/%d" % (u, int(a or 0), int(a or 0) + int(b or 0)))
        except Exception as e:                                       # noqa: BLE001
            tried.append("%s %s" % (u, e.__class__.__name__))
    if sent:
        return True, "clinic app: " + ", ".join(tried)
    url = _ntfy_url()
    if not url:
        return False, "no clinic-app device (%s) and no ntfy address" % ", ".join(tried)
    try:
        import urllib.request                                        # noqa: PLC0415
        t = title.replace("·", "-").encode("ascii", "replace").decode("ascii")
        req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST", headers={"Title": t, "Priority": "high", "Tags": "warning"})
        urllib.request.urlopen(req, timeout=20).read()
        return True, "ntfy (no clinic-app device: %s)" % ", ".join(tried)
    except Exception as e:                                           # noqa: BLE001
        return False, "ntfy FAILED (%s) -- tried again at the next run" % e.__class__.__name__


def tick(dry=False):
    """One pass. -> a one-line report. Never raises."""
    try:
        if os.path.exists(ALL_OFF):
            return "off (the estate's ALL_OFF)"
        con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=10)
        try:
            if (_setting(con, "reader_watch.on", "on") or "on").strip().lower() == "off":
                return "off (reader_watch.on = off)"
            st = reader_state(con)
            to = _setting(con, "reader_watch.to", "manoj") or "manoj"
        finally:
            con.close()
        mem = load()
        d = decide(st, mem.get("told", ""))
        if d is None:
            return "reader %s -- nothing to say" % st
        title, body, keep = d
        if dry:
            return "WOULD SAY: %s -- %s" % (title, body)
        ok, how = send(title, body, to)
        if ok:
            save({"told": keep, "at": now_ist().strftime("%Y-%m-%d %H:%M IST"), "how": how})
            return "told: %s (%s)" % (title, how)
        return "NOT told yet: %s (%s)" % (title, how)
    except Exception as e:                                           # noqa: BLE001
        return "error: %s" % e.__class__.__name__


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd in ("tick", "show"):
        print("%s reader_watch: %s" % (now_ist().strftime("%Y-%m-%d %H:%M IST"), tick(dry=(cmd == "show"))))
    elif cmd == "test":                                              # the install's proof of the road: one message, says what it is for
        con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=10)
        to = _setting(con, "reader_watch.to", "manoj") or "manoj"
        con.close()
        ok, how = send("Scan app · reader watch on", "From now on you are told here at once if the scan app's paper reader stops "
                       "(a key refused or expired, the credit run out), and again when it reads again.", to)
        print("test: %s (%s)" % ("SENT" if ok else "NOT SENT", how))
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)
