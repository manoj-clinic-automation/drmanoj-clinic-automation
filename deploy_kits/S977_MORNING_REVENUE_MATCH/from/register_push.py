#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""register_push.py -- kit S968_REGISTER_PUSH (the parent, S531, 27-Nov-2026). PARENT. NEW.

THE OWNER, 27-Nov-2026 (10:31 IST): a dressing was charged on 26-Nov evening with no parchi and no Docterz entry; the evening
check said all was well (it checks parchis against Docterz, and there was no parchi); in the morning Shavez entered the register
"and he did not get any prompt as to whether there is any discrepancy, or we do not know where to check it". The day check HAD
carded it ("Rs 100 -- Docterz entry missing, patient not found · procedure · cash") -- on a page nobody was sent to.
His word at 10:40: "PROCEED".

WHAT IT DOES. The moment the register of a day is saved (clinic_register.py starts this file in its own process -- never waited
for, nothing here can fail the Save), and every 5 minutes from 08:00 to 21:55 (cron # S968_REGISTER_PUSH), it reads the day check
of each recent day (day_check.check_day -- the same answer the page shows, worked out afresh) and pushes to the logins in
REGPUSH_TO (shavez, reception) through the call-back clock's own road (the portal's Web Push; ntfy for a login with no device):
    the day has lines to fix, and one is new since the last push  ->  "<day>: N galti -- din ki jaanch"  + the first lines
    the day is clean, and no push was ever sent for it            ->  "<day>: register, Docterz aur parchi sab mile"
    the day is clean now, after a push that named lines            ->  "<day>: sab galtiyan theek"
    the same lines as last time, or fewer (still some)             ->  nothing (already told)
"Lines" are the STAFF's: the Docterz and parchi corrections not yet ticked; the owner's back-date rows and the "check by hand"
lines stay on his page and are never pushed to them. An amount at the end of a line's key is not part of its name (a partly
fixed line is not a new one). A day not yet checked is recorded as 'waiting', so a late Docterz export is still told.
Tapping the push opens the staff's own day check (/finance/clinic/check/mine). Only a day whose Docterz export AND register are
both in is judged (the page says "waiting" otherwise). A day the sweep meets for the first time that is older than yesterday is
recorded quietly (no push about an old day at install); a Save always judges its own day, whatever its age. Pushes go out only
on the live database (REGPUSH_LIVE_DB): a walk or a rehearsal records its answer and pushes nothing. REGPUSH_ON=0 turns it off.

ONE TABLE OF ITS OWN, created on first use (F-303):
    register_push  day (PRIMARY KEY), keys (the open lines' keys, no names), n, at, outcome (open | clean | cleared | quiet |
                   seeded | waiting | off), sent
It reads only what day_check.check_day reads; it writes register_push -- and, from S970, an answer on his list (below).

S970 (the owner, 27-Nov-2026 12:45 IST: "ONLY SLIP OF THIS DRESSING ALSO SETTLES THE MATCH OF MORNING CASH WITH SLIPS, EVEN IF
DOCTERZ ISNT UPDATED, AS UPDATING BACK DATE DOCTERZ I WANT TO AVOID?" -- and 12:46 "YES" to making it automatic). Before a day is
judged, each row of his back-date list whose WHOLE money the register holds (the day check's backdate row with placed and allp:
a slip Docterz does not carry, every part of its money in the register) is answered "Not entering in Docterz" by itself -- not_in_docterz.mark(...,
'outside') as the login 'auto'. The day then matches with no tap and no back-dated Docterz entry; his list shows the answer with
its Undo. A row anyone has answered or undone before is never answered again (an Undo is final). A slip Docterz carries later
leaves his list by itself, its answer with it (not_in_docterz.rows reads Docterz first), so nothing is counted twice.
Never today's day (the evening list is still the staff's).
REGPUSH_AUTO_OUTSIDE=0 turns this alone off. Writes nid_mark rows only through not_in_docterz.mark().
No patient name, no number, no secret in this file (F-185). A push carries the day check's own line words.

    /root/wa/venv/bin/python3 -B /root/finance/register_push.py --day YYYY-MM-DD [--db PATH] [--no-push]   (started by the Save)
    /root/wa/venv/bin/python3 -B /root/finance/register_push.py --sweep [--db PATH] [--no-push]            (cron, every 5 min)
    /root/wa/venv/bin/python3 -B /root/finance/register_push.py --status [--db PATH]                       (counts only)
"""
import datetime as dt
import fcntl
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
VERSION = "S970 1"
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
LIVE_DB = os.environ.get("REGPUSH_LIVE_DB", "/root/finance/finance.db")
TO_DEFAULT = "shavez,reception"
CHECK_URL = "/finance/clinic/check/mine"
DAYS = 7                                                  # the staff's week (day_check.STAFF_DAYS)
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
PUSHER = None                                             # the walk hands in a stub (login, payload) -> (ok, failed)
CC_MOD = None                                             # the walk may hand in a callback_clock module
DC_MOD = None                                             # the walk may hand in a day_check module
NID_MOD = None                                            # the walk may hand in a not_in_docterz module (S970)
AUTO_WHO = "auto"                                         # S970: the login named on an answer given by itself

DDL = """
CREATE TABLE IF NOT EXISTS register_push (
  day      TEXT PRIMARY KEY,
  keys     TEXT NOT NULL DEFAULT '',
  n        INTEGER NOT NULL DEFAULT 0,
  at       TEXT NOT NULL DEFAULT '',
  outcome  TEXT NOT NULL DEFAULT '',
  sent     TEXT NOT NULL DEFAULT ''
);
"""


def now_ist():
    """The IST clock; REGPUSH_NOW=<iso> pins it for the walk."""
    v = os.environ.get("REGPUSH_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)


def _stamp(t=None):
    return (t or now_ist()).strftime("%Y-%m-%d %H:%M:%S")


def dm(day_iso):
    try:
        return dt.date.fromisoformat(day_iso).strftime("%d-%b")
    except (ValueError, TypeError):
        return day_iso or ""


def _ev():
    """evening_check.py beside this file: the clock, the settings reader and the live-database test are its own."""
    import evening_check as ev                            # noqa: PLC0415
    if CC_MOD is not None:
        ev.CC_MOD = CC_MOD
    return ev


def _dc():
    if DC_MOD is not None:
        return DC_MOD
    import day_check as dc                                # noqa: PLC0415
    return dc


def cfg(name, default=""):
    try:
        return _ev().cfg(name, default)
    except Exception:                                     # noqa: BLE001
        v = os.environ.get(name, "").strip()
        return v or default


def is_on():
    return cfg("REGPUSH_ON", "1").lower() not in ("0", "off", "no", "false")


def _live(con):
    try:
        path = con.execute("PRAGMA database_list").fetchone()[2]
        return bool(path) and os.path.realpath(path) == os.path.realpath(LIVE_DB)
    except Exception:                                     # noqa: BLE001
        return False


def ensure(con):
    con.executescript(DDL)
    con.commit()


def _lock(con):
    try:
        path = con.execute("PRAGMA database_list").fetchone()[2]
    except Exception:                                     # noqa: BLE001
        path = ""
    fh = open(os.path.join(os.path.dirname(path) if path else HERE, ".register_push.lock"), "a")
    fcntl.flock(fh, fcntl.LOCK_EX)
    return fh


def _send(who, title, body, tag):
    """(sent, failed, ntfy) through callback_clock.send -- or a word on why nothing went."""
    try:
        cc = _ev()._cc()
    except Exception as ex:                               # noqa: BLE001
        return None, "the evening check is not here (%s)" % type(ex).__name__
    if cc is None:
        return None, "the call-back clock is not here"
    try:
        pusher = cc.get_pusher(PUSHER)
        return cc.send(pusher, who, title, body, (lambda w: CHECK_URL), tag), ""
    except Exception as ex:                               # noqa: BLE001
        return None, "send: %s" % str(ex)[:100]


def _norm(key):
    """A line's lasting name. Of the staff's lines only 'patient not found' (nf:<tender>:<section>:<amount>) carries an amount in
    its key; it is dropped, so a partly fixed line is not a 'new' one. Every other key names its slip, item or patient."""
    k = str(key or "")
    return re.sub(r":\d+$", "", k) if k.startswith("nf:") else k


def open_lines(chk):
    """{lasting key: words} of what the STAFF still have to do on the day: the Docterz and parchi lines not yet ticked (cold
    review, S968: the owner's back-date rows and the 'check by hand' lines are not theirs, so never pushed to them as 'galti')."""
    out = {}
    for c in chk.get("cards") or []:
        if c.get("who") in ("docterz", "parchi") and not c.get("tick"):
            out.setdefault(_norm(c.get("key") or c.get("kind") or "?"), c.get("hi") or c.get("en") or "")
    return out


def auto_on():
    return cfg("REGPUSH_AUTO_OUTSIDE", "1").lower() not in ("0", "off", "no", "false")


def _nid():
    if NID_MOD is not None:
        return NID_MOD
    import not_in_docterz as nid                          # noqa: PLC0415
    return nid


def _answered_before(con, slip_id, kind):
    """True when the row has ANY answer, live or undone (an Undo is final). Unreadable = True: never answer blind."""
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='nid_mark'").fetchone() is None:
            return False                                  # no answer was ever given on this box
        return con.execute("SELECT 1 FROM nid_mark WHERE slip_id=? AND kind=? LIMIT 1", (slip_id, kind)).fetchone() is not None
    except sqlite3.Error:
        return True


def auto_outside(con, chk, day=None, at=None):
    """S970: answer 'Not entering in Docterz' for each back-date row whose WHOLE money the register holds (allp: every part of
    the row placed -- cold review: a part-held row is his). Never today's day (its evening list is still the staff's). Returns how many."""
    if not auto_on():
        return 0
    if day and day >= (at or now_ist()).date().isoformat():
        return 0
    rows = [b for b in (chk.get("backdate") or []) if b.get("placed") and b.get("allp") and b.get("slip_id")
            and b.get("kind") in ("opd", "xray", "proc")]
    if not rows:
        return 0
    nid = _nid()
    n = 0
    for b in rows:
        try:
            sid = int(b["slip_id"])
        except (TypeError, ValueError):
            continue
        if _answered_before(con, sid, b["kind"]):
            continue
        try:
            nid.mark(con, AUTO_WHO, sid, b["kind"], "outside")
            n += 1
        except Exception:                                 # noqa: BLE001 -- refused (already answered, Docterz carries it): leave it
            try:
                con.rollback()
            except Exception:                             # noqa: BLE001
                pass
    return n


def judge(con, day, push=True, at=None, from_save=False):
    """One day: read its check, compare with the last push, push when something new is to be said. Returns the outcome word."""
    at = at or now_ist()
    ensure(con)
    dc = _dc()
    chk = dc.check_day(con, day)
    prev = con.execute("SELECT keys, outcome FROM register_push WHERE day=?", (day,)).fetchone()
    if chk.get("state") != "checked":
        if prev is None:                                  # cold review, S968: a day checked late is not 'met first' when old
            con.execute("INSERT OR IGNORE INTO register_push (day, at, outcome) VALUES (?,?,'waiting')", (day, _stamp(at)))
            con.commit()
        return "skip: %s" % (chk.get("state") or "not checked")
    try:
        if auto_outside(con, chk, day, at):               # S970: rows answered by themselves -- read the day afresh
            chk = dc.check_day(con, day)
    except Exception:                                     # noqa: BLE001 -- the push stands without it
        pass
    lines = open_lines(chk)
    keys = sorted(lines)
    pkeys = set(k for k in ((prev[0] if prev else "") or "").split(",") if k)
    pout = prev[1] if prev else None
    today = at.date()
    old = dt.date.fromisoformat(day) < today - dt.timedelta(days=1)
    title = body = ""
    if prev is None and old and not from_save:
        outcome = "seeded"
    elif not is_on():
        outcome = "off"
    elif keys:
        new = [k for k in keys if k not in pkeys]           # a line not named before (a seeded old day's lines were named)
        if new:
            outcome = "open"
            n = len(keys)
            title = "%s: %d galti — din ki jaanch" % (dm(day), n) if n == 1 else "%s: %d galtiyan — din ki jaanch" % (dm(day), n)
            lead = " ; ".join(w for w in [lines[k] for k in new] + [lines[k] for k in keys if k not in new] if w)[:300]
            body = (lead or dc.summary_hi(chk)) + " — kholiye aur theek kijiye"
        else:
            outcome = "quiet"
    elif pout == "open":
        outcome = "cleared"
        title, body = "✓ %s: sab galtiyan theek" % dm(day), "Din ki jaanch — kaam poora"
    elif pout in (None, "waiting") and dc.is_clean(chk):
        outcome = "clean"
        title, body = "✓ %s: register, Docterz aur parchi sab mile" % dm(day), "Kuch nahi karna"
    else:
        outcome = "quiet"
    sent = ""
    if title:
        who = [w.strip() for w in cfg("REGPUSH_TO", TO_DEFAULT).split(",") if w.strip()]
        if not push:
            sent = "not pushed (asked not to)"
        elif not _live(con):
            sent = "not pushed (not the live database)"
        elif not who:
            sent = "not pushed (no login in REGPUSH_TO)"
        else:
            res, why = _send(who, title, body, "daycheck-" + day)
            sent = ("sent %d, failed %d, ntfy %d" % tuple(res)) if res else ("not pushed (%s)" % why)
    if outcome == "quiet" and prev is not None:
        con.execute("UPDATE register_push SET keys=?, n=?, outcome=CASE WHEN outcome='waiting' THEN 'quiet' ELSE outcome END "
                    "WHERE day=?", (",".join(keys), len(keys), day))
    else:
        con.execute("INSERT OR REPLACE INTO register_push (day, keys, n, at, outcome, sent) VALUES (?,?,?,?,?,?)",
                    (day, ",".join(keys), len(keys), _stamp(at), outcome, sent))
    con.commit()
    return "%s %s %d (%s)" % (day, outcome, len(keys), sent or "nothing to send")


def one_day(con, day, push=True, at=None, from_save=False):
    lk = _lock(con)
    try:
        return judge(con, day, push, at, from_save)
    finally:
        try:
            fcntl.flock(lk, fcntl.LOCK_UN)
            lk.close()
        except Exception:                                 # noqa: BLE001
            pass


def sweep(con, push=True, at=None):
    """Every recent day with a saved register, judged in turn. Returns the outcomes worth a log line."""
    at = at or now_ist()
    lo = (at.date() - dt.timedelta(days=DAYS)).isoformat()
    hi = at.date().isoformat()
    try:
        days = [r[0] for r in con.execute("SELECT business_date FROM clinic_register_day WHERE business_date>=? AND business_date<=? "
                                          "ORDER BY business_date", (lo, hi))]
    except sqlite3.Error:
        return []
    out = []
    lk = _lock(con)
    try:
        for d in days:
            try:
                w = judge(con, d, push, at)
            except Exception as ex:                       # noqa: BLE001 -- one day's fault never stops the others
                w = "%s error %s" % (d, type(ex).__name__)
            if not w.startswith("skip") and " quiet " not in w:
                out.append(w)
    finally:
        try:
            fcntl.flock(lk, fcntl.LOCK_UN)
            lk.close()
        except Exception:                                 # noqa: BLE001
            pass
    return out


def main(argv=None):
    import argparse                                       # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--day")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args(argv)
    con = sqlite3.connect(a.db, timeout=30)
    con.row_factory = sqlite3.Row
    t = now_ist()
    if a.status:
        ensure(con)
        rows = con.execute("SELECT outcome, COUNT(*) FROM register_push GROUP BY outcome ORDER BY outcome").fetchall()
        print("REGPUSH %s: %s" % (VERSION, " . ".join("%s %d" % (r[0], r[1]) for r in rows) or "no day judged yet"))
        return 0
    if a.sweep:
        for w in sweep(con, push=not a.no_push, at=t):
            print("%s register_push %s %s" % (_stamp(t), VERSION, w))
        return 0
    if a.day:
        print("%s register_push %s save %s" % (_stamp(t), VERSION, one_day(con, a.day, push=not a.no_push, at=t, from_save=True)))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
