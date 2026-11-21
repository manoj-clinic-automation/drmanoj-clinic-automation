#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docterz_taken_notice.py -- kit S915_DOCTERZ_TAKEN_NOTICE (the parent, S496, 21-Nov-2026). NEW.

THE OWNER, 21-Nov-2026 08:34 IST: "there shd be a message when the Docterz reports are generated / picked by server,
consultation report, followup, clinical data, and i shd know till when is clinical data exported, so I export a relevant date
range when needed, from reception pc and manojz, and the pc source shd be written on message as well".

WHAT IT DOES, every 5 minutes (cron; it waits for the pickup's own lock, so it speaks just after a pickup pass):
  * reads finance.db's docterz_export (READ ONLY) for rows newer than the last one it has looked at (a state file beside it);
  * for every new consultation report, follow-up log and clinical data report the server TOOK (status 'current') or set
    aside (any status but duplicate / superseded / unknown), one line: what it is, the day, the rows, and WHERE IT CAME FROM:
        drive_id 'reception:...'            -> the reception PC (its agent)
        a Drive file named '..._manojz_...' -> your PC (manojz)
        drive_id 'owner:...'                -> the Docterz reports page (an upload by hand)
        any other Drive file                -> the reception PC (Chrome saves into the Drive folder)
    a follow-up log says the call days it covers; a clinical data report says the period it covers;
  * every message ends with how far the clinical data on the server reaches, and the day to export from next time;
  * ONE push for the pass (the portal's own Web Push to the owner's login, docterz_missing_alert's road); when no device takes
    it, the private ntfy topic once. A not-sitting mark, a duplicate, a superseded row, a stray PDF: nothing said.
  * FIRST RUN: no state file -> the newest row is noted and NOTHING is sent (no flood of old exports).
It never prints a file name, a patient or a number; the message carries kinds, days, counts and where from.
Off switch: /root/finance/_off/ALL_OFF or /root/finance/_off/DOCTERZ_TAKEN_NOTICE_OFF.

CLI:  docterz_taken_notice.py                 the run (what cron calls)
      docterz_taken_notice.py --dry           what it WOULD send for the rows after the state's mark; sends and writes nothing
      docterz_taken_notice.py --dry --since N the same for the rows after id N (to read a past evening)
      docterz_taken_notice.py --probe         one line: the store readable, the newest row, the state's mark (the installer's gate)
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time

VERSION = "S915 1"
HERE = os.path.dirname(os.path.abspath(__file__))
FINANCE_DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
OFF_DIR = os.environ.get("FINANCE_OFF_DIR", "/root/finance/_off")
OFF_NAMES = ("ALL_OFF", "DOCTERZ_TAKEN_NOTICE_OFF")
STATE = os.environ.get("DTN_STATE", os.path.join(HERE, "docterz_taken_notice_state.json"))
KINDS = ("consultation", "followup", "clinical")
QUIET = ("duplicate", "superseded", "unknown")
OWNER = ("manoj",)
OWNER_URL = "/finance/console/docterz-reports"
MAX_LINES = 12
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)


def off_switch(off_dir=None):
    d = off_dir or OFF_DIR
    for n in OFF_NAMES:
        if os.path.exists(os.path.join(d, n)):
            return os.path.join(d, n)
    return ""


def _connect(db):
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=20)
    con.row_factory = sqlite3.Row
    return con


def _day(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def dnm(d, wd=True):
    """'Fri 20 Nov' / '20 Nov'."""
    if d is None:
        return "?"
    return (d.strftime("%a ") if wd else "") + "%d %s" % (d.day, d.strftime("%b"))


def source(drive_id, drive_name):
    did, nm = str(drive_id or ""), str(drive_name or "")
    if did.startswith("reception:"):
        return "the reception PC"
    if did.startswith("owner:"):
        return "the Docterz reports page"
    if "_manojz_" in nm:
        return "your PC (manojz)"
    return "the reception PC"


def _covers(note):
    """'covers 2026-11-19 to 2026-11-20' (the pickup's own note on a clinical report) -> (d0, d1) or (None, None)."""
    try:
        s = str(note or "")
        i = s.index("covers ")
        a, b = s[i + 7:].split(" to ")[:2]
        return _day(a), _day(b[:10])
    except (ValueError, IndexError):
        return None, None


def line_for(r):
    """One plain-English line for one taken row, or '' when nothing is to be said about it."""
    kind, status = r["kind"], str(r["status"] or "")
    if kind not in KINDS or status in QUIET or str(r["drive_id"] or "").startswith("offday:"):
        return ""
    src = source(r["drive_id"], r["drive_name"])
    day = _day(r["business_date"])
    n = int(r["rows"] or 0)
    if kind == "consultation":
        what = "Consultation report for %s — %d patient%s" % (dnm(day), n, "" if n == 1 else "s")
    elif kind == "followup":
        d0, d1 = _day(r["due_from"]), _day(r["due_to"])
        span = (" — calls due %s to %s" % (dnm(d0, False), dnm(d1, False))) if (d0 and d1) else ""
        what = "Follow-up log of %s%s, %d row%s" % (dnm(day), span, n, "" if n == 1 else "s")
    else:
        c0, c1 = _covers(r["note"])
        span = (" — covers %s to %s" % (dnm(c0, False), dnm(c1, False))) if (c0 and c1) else \
               (" — up to %s" % dnm(day, False) if day else "")
        what = "Clinical data report%s, %d visit row%s" % (span, n, "" if n == 1 else "s")
    tail = "" if status == "current" else (" — NOT used (%s)" % ("fewer rows than the one already held" if status == "quarantined"
                                                                  else status.replace("_", " ")))
    return "%s — from %s%s." % (what, src, tail)


def clinical_reach(con):
    """The newest day the server's clinical data reaches (current reports), or None."""
    try:
        v = con.execute("SELECT MAX(business_date) FROM docterz_export WHERE kind='clinical' AND status='current' "
                        "AND business_date<>''").fetchone()[0]
    except sqlite3.Error:
        return None
    return _day(v)


def compose(con, since, now):
    """(title, body, last_id, nlines) for the rows after `since`; title '' when there is nothing to say."""
    rows = con.execute("SELECT id, drive_id, drive_name, kind, business_date, rows, status, note, due_from, due_to "
                       "FROM docterz_export WHERE id>? ORDER BY id", (since,)).fetchall()
    last = max([since] + [int(r["id"]) for r in rows])
    lines = [x for x in (line_for(r) for r in rows) if x]
    if not lines:
        return "", "", last, 0
    more = len(lines) - MAX_LINES
    lines = lines[:MAX_LINES] + (["... and %d more on the Docterz reports page." % more] if more > 0 else [])
    reach = clinical_reach(con)
    if reach:
        nxt = reach + dt.timedelta(days=1)
        lines.append("Clinical data on the server reaches %s — next time export it from %s." % (dnm(reach), dnm(nxt, False)))
    title = "Docterz reports received (%s)" % now.strftime("%H:%M")
    return title, "\n".join(lines), last, len(lines)


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return int(d.get("last_id"))
    except (OSError, ValueError, TypeError):
        return None


def save_state(path, last_id, now):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"last_id": int(last_id), "at": now.strftime("%Y-%m-%d %H:%M:%S"), "version": VERSION}, fh)
    os.replace(tmp, path)


def _mal():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import docterz_missing_alert as M                    # noqa: PLC0415 -- its push and its ntfy fallback, not re-invented
    return M


def send(title, body, pusher=None, ntfy=None):
    """-> (how, ok). The owner's devices first; the ntfy topic once when none took it."""
    try:
        M = _mal()
        p = M.get_pusher(pusher)
        s = f = 0
        if p is not None:
            for w in OWNER:                               # docterz_missing_alert.push's own call, with this page's address
                try:
                    a_, b_ = p(w, {"title": title, "body": body, "url": OWNER_URL, "tag": "docterz-taken", "ttl": 43200,
                                   "requireInteraction": False, "renotify": True})
                    s, f = s + int(a_ or 0), f + int(b_ or 0)
                except Exception:                        # noqa: BLE001
                    f += 1
        if s:
            return "push %d device(s)" % s, True
        went, how = (ntfy or M.send_ntfy)(title, body)
        return ("no device took it; " + how), bool(went)
    except Exception as e:                               # noqa: BLE001
        return "could not send (%s)" % type(e).__name__, False


def run(db=None, state=None, now=None, dry=False, since=None, pusher=None, ntfy=None, off_dir=None):
    now = now or now_ist()
    db, state = db or FINANCE_DB, state or STATE
    head = "%s%s" % ("DRY " if dry else "", now.strftime("%Y-%m-%d %H:%M"))
    off = off_switch(off_dir)
    if off and not dry:
        return head + ": off switch there -- nothing sent"
    try:
        con = _connect(db)
    except sqlite3.Error as e:
        return head + ": finance.db could not be opened (%s) -- nothing sent" % type(e).__name__
    try:
        mark = since if since is not None else load_state(state)
        if mark is None:
            top = int(con.execute("SELECT COALESCE(MAX(id),0) FROM docterz_export").fetchone()[0])
            if not dry:
                save_state(state, top, now)
            return head + ": first run -- the mark set at row %d, nothing sent" % top
        title, body, last, n = compose(con, mark, now)
    except sqlite3.Error as e:
        return head + ": docterz_export could not be read (%s) -- nothing sent" % type(e).__name__
    finally:
        con.close()
    if dry:
        return head + (": would send %d line(s)\n%s\n%s" % (n, title, body) if title else ": nothing new to say (mark %d -> %d)" % (mark, last))
    if not title:
        if last != mark:
            save_state(state, last, now)
        return ""
    how, ok = send(title, body, pusher, ntfy)
    save_state(state, last, now)                          # spoken or not, a row is told once: never a storm of repeats
    return head + ": %d line(s), rows %d -> %d, %s%s" % (n, mark, last, how, "" if ok else " -- NOT delivered")


def probe(db=None, state=None):
    try:
        con = _connect(db or FINANCE_DB)
        top = int(con.execute("SELECT COALESCE(MAX(id),0) FROM docterz_export").fetchone()[0])
        reach = clinical_reach(con)
        con.close()
    except sqlite3.Error as e:
        return "PROBE FAIL: %s" % type(e).__name__
    return "PROBE OK newest row %d, mark %s, clinical reaches %s" % (top, load_state(state or STATE), reach or "-")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--since", type=int)
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.probe:
            print(probe())
            return 0
        line = run(dry=a.dry or a.since is not None, since=a.since)
        if line:
            print(line)
    except Exception as e:                               # noqa: BLE001 -- one line, exit 0
        print("%s: ERROR %s" % (now_ist().strftime("%Y-%m-%d %H:%M"), type(e).__name__))
    return 0


if __name__ == "__main__":
    sys.exit(main())
