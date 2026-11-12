#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""callback_clock.py -- kit S796_CALLBACK_CLOCK (session S435, 12-Nov-2026, the parent). NEW.

THE OWNER, 12-Nov-2026 07:47 / 07:52 IST, on the plan "so that no caller is lost": "a clock on the callback, this is fine. And the backup
phone should be Shavez." -- "Both" (build it).

WHY. 14-Oct .. 11-Nov, callers counted once a day: 15 in 100 never spoke to anyone, and 57 of those 66 had no call-back on record --
although the missed-call notification goes to the staff phones at once (ring_hook.py) and MyOperator sends the caller its template.
The first notification is easy to lose in a busy hour; nothing asked again.

WHAT IT DOES. Run by cron every 5 minutes. It reads /root/wa/console.db READ-ONLY (the Call Console's own store, rebuilt every 10
minutes) and finds every caller with a MISSED incoming call since yesterday's closing time who has not SPOKEN to the clinic since (no
answered call after it, either way -- the Call Console's own rule for a missed call). The clock counts DUTY minutes only (Mon-Sat
09:00-20:30, Sunday 09:00-14:30), and is judged as of the store's own build time, so a call-back the store has not seen yet is never
chased early:
  * 30 duty minutes  -> ONE notification to the phone staff (shivani, alisha, the reception mobile): how many, and who;
  * 60 duty minutes  -> ONE notification to Shavez, the backup (the owner's word);
  * at closing time  -> the count still open goes to the owner (English), only when it is above zero.
Each caller's missed call is notified once per stage (its own small store, STORE); a number the owner marked Spam is left out; a stale
console.db (older than STALE_MIN) is not judged at all. Nothing here changes console.db, the portal, or any page.

CLI:  callback_clock.py          the run (what cron calls)
      callback_clock.py --dry    counts only; pushes nothing, writes nothing
Stdlib only (+ ring_common from /root/portal for the push: absent = counted, nothing sent).
"""
import datetime as dt
import os
import re
import sqlite3
import sys

VERSION = "S796 1"
CONSOLE_DB = os.environ.get("CC_CONSOLE_DB", "/root/wa/console.db")
REVIEWS_DB = os.environ.get("CC_REVIEWS_DB", "/root/wa/console_reviews.db")
STORE = os.environ.get("CC_STORE", "/root/portal/callback_clock.db")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
STAFF = ("shivani", "alisha", "reception")
BACKUP = ("shavez",)                               # the owner, 12-Nov 07:47 IST
OWNER = ("manoj",)
T1, T2 = 30, 60                                    # duty minutes
OPEN_HM = (9, 0)
CLOSE_HM = (20, 30)
SUN_CLOSE_HM = (14, 30)
STALE_MIN = 25                                     # console.db is rebuilt every 10 minutes
STAFF_URL = "/portal/go/call-tracker"
OWNER_URL = "/portal/console"
SPAM_OUTCOME = "Spam / marketing"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
_JK = re.compile(r"^(\d{10})_(\d{9,12})$")
_TZ = re.compile(r"([+-]\d{2}:?\d{2}|Z)\s*$")


def now_ist():
    return dt.datetime.now(IST).replace(tzinfo=None)


def parse_ts(s):
    s = _TZ.sub("", (s or "").strip()).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def window(day):
    """(start, end) of the duty window of one date."""
    close = SUN_CLOSE_HM if day.weekday() == 6 else CLOSE_HM
    return (dt.datetime.combine(day, dt.time(*OPEN_HM)), dt.datetime.combine(day, dt.time(*close)))


def duty_minutes(t0, t1):
    """Whole duty minutes between two moments (0 when t1 <= t0)."""
    if t1 <= t0:
        return 0
    total = 0.0
    day = t0.date()
    while day <= t1.date():
        a, b = window(day)
        lo, hi = max(a, t0), min(b, t1)
        if hi > lo:
            total += (hi - lo).total_seconds()
        day += dt.timedelta(days=1)
    return int(total // 60)


def phone_of(p10, jk, ref):
    """The Call Console's own rule (calls_console.phone_of)."""
    p = (p10 or "").strip()
    if len(p) == 10 and p.isdigit():
        return p
    m = _JK.match(jk or "")
    if m:
        return m.group(1)
    cr = (ref or "").strip()
    m2 = re.match(r"^(\d{10})\D", cr + " ")
    if m2 and not cr.startswith("IN-"):
        return m2.group(1)
    return ""


def spam_phones(path=None):
    out = set()
    try:
        con = sqlite3.connect("file:%s?mode=ro" % (path or REVIEWS_DB), uri=True, timeout=5)
        try:
            for (jk,) in con.execute("SELECT join_key FROM dispositions WHERE final_outcome=?", (SPAM_OUTCOME,)):
                if "_" in (jk or ""):
                    out.add(jk.split("_", 1)[0])
        finally:
            con.close()
    except Exception:                                    # noqa: BLE001
        pass
    return out


def read_console(path, d_from, d_to):
    """(built_at or None, {phone: [(t, direction, answered)]}, {phone: (name, clinic_id)})."""
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=10)
    try:
        built = None
        try:
            r = con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()
            built = parse_ts(r[0]) if r else None
        except sqlite3.Error:
            built = None
        by = {}
        for p10, jk, ref, direction, answered, ended in con.execute(
                "SELECT c.phone10, c.join_key, c.client_ref_id, c.direction, c.answered, c.ended_at_ist FROM calls c "
                "WHERE substr(c.ended_at_ist,1,10)>=? AND substr(c.ended_at_ist,1,10)<=? ORDER BY c.ended_at_ist ASC, c.id ASC",
                (d_from, d_to)):
            ph, t = phone_of(p10, jk, ref), parse_ts(ended)
            if ph and t:
                by.setdefault(ph, []).append((t, (direction or "").strip(), answered == 1))
        pats = {}
        try:
            for ph, name, cid in con.execute("SELECT phone10, name, clinic_id FROM patients WHERE phone10<>'' ORDER BY rowid"):
                pats[ph] = ((name or "").strip(), (cid or "").strip())
        except sqlite3.Error:
            pats = {}
        return built, by, pats
    finally:
        con.close()


def open_callers(by, pats, spam, cutoff):
    """Callers whose missed call at or after `cutoff` has not been followed by an answered call (either way)."""
    out = []
    for ph, its in by.items():
        if ph in spam:
            continue
        its = sorted(its)
        last_ok = max([t for t, _d, ok in its if ok], default=None)
        opens = [t for t, d, ok in its if d == "In" and not ok and t >= cutoff and (last_ok is None or t > last_ok)]
        if not opens:
            continue
        t0 = opens[0]
        name, cid = pats.get(ph, ("", ""))
        out.append({"phone": ph, "t0": t0, "missed": len(opens), "name": name, "cid": cid, "unknown": not name,
                    "tried": sum(1 for t, d, ok in its if d == "Out" and not ok and t > t0)})
    out.sort(key=lambda c: c["t0"])
    return out


def label(c):
    if c["name"]:
        return c["name"] + ((" (ID %s)" % c["cid"]) if c["cid"] else "")
    return "नया नंबर " + c["phone"]


def names(cs, n=3):
    s = " · ".join(label(c) for c in cs[:n])
    return s + ((" +%d" % (len(cs) - n)) if len(cs) > n else "")


def store_open(path):
    con = sqlite3.connect(path, timeout=10)
    con.execute("CREATE TABLE IF NOT EXISTS sent(phone TEXT NOT NULL, t0 TEXT NOT NULL, stage INTEGER NOT NULL, at TEXT NOT NULL, "
                "PRIMARY KEY(phone, t0, stage))")
    con.execute("CREATE TABLE IF NOT EXISTS runs(at TEXT NOT NULL, open INTEGER, unknown INTEGER, s1 INTEGER, s2 INTEGER, closing INTEGER, "
                "sent TEXT)")
    return con


def get_pusher(pusher=None):
    if pusher is not None:
        return pusher
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import ring_common as rc                         # noqa: PLC0415
        return rc.push_user
    except Exception:                                    # noqa: BLE001
        return None


def push(pusher, who, title, body, url, tag):
    s = f = 0
    for w in who:
        try:
            a, b = pusher(w, {"title": title, "body": body, "url": url, "tag": tag, "ttl": 1800, "requireInteraction": True, "renotify": True})
        except Exception:                                # noqa: BLE001
            a, b = 0, 1
        s, f = s + a, f + b
    return s, f


def run(dry=False, pusher=None, now=None, console=None, store=None, reviews=None):
    now = now or now_ist()
    console = console or CONSOLE_DB
    store = store or STORE
    today = now.date()
    yday = today - dt.timedelta(days=1)
    try:
        built, by, pats = read_console(console, yday.isoformat(), today.isoformat())
    except Exception as e:                               # noqa: BLE001
        print("%s console.db could not be read (%s) -- nothing judged" % (now.strftime("%Y-%m-%d %H:%M"), type(e).__name__))
        return {"ok": False, "why": "unreadable"}
    age = int((now - built).total_seconds() // 60) if built else None
    if built is None or age > STALE_MIN:
        print("%s console.db is stale (built %s) -- nothing judged" % (now.strftime("%Y-%m-%d %H:%M"), built.strftime("%H:%M") if built else "never"))
        return {"ok": False, "why": "stale", "age": age}
    asof = min(now, built)
    cutoff = window(yday)[1]
    cs = open_callers(by, pats, spam_phones(reviews), cutoff)
    for c in cs:
        c["mins"] = duty_minutes(c["t0"], asof)
    a, b = window(today)
    in_duty = a <= now <= b
    closing = now >= b
    res = {"ok": True, "open": len(cs), "unknown": sum(1 for c in cs if c["unknown"]), "due1": sum(1 for c in cs if c["mins"] >= T1),
           "due2": sum(1 for c in cs if c["mins"] >= T2), "asof": asof.strftime("%H:%M"), "new1": 0, "new2": 0, "closing": 0, "sent": {}}
    if dry:
        print("DRY %s: callers not spoken to %d (unknown numbers %d); waiting 30+ duty minutes %d, 60+ %d; judged as of %s; nothing sent, "
              "nothing written" % (now.strftime("%Y-%m-%d %H:%M"), res["open"], res["unknown"], res["due1"], res["due2"], res["asof"]))
        return res
    con = store_open(store)
    try:
        done = {(r[0], r[1], r[2]) for r in con.execute("SELECT phone, t0, stage FROM sent WHERE at >= ?", (yday.isoformat(),))}
        key = lambda c, st: (c["phone"], c["t0"].strftime("%Y-%m-%d %H:%M:%S"), st)        # noqa: E731
        new1 = [c for c in cs if c["mins"] >= T1 and key(c, 1) not in done] if in_duty else []
        new2 = [c for c in cs if c["mins"] >= T2 and key(c, 2) not in done] if in_duty else []
        close_key = ("*", today.isoformat(), 9)
        do_close = closing and close_key not in done and len(cs) > 0
        p = get_pusher(pusher) if (new1 or new2 or do_close) else None
        stamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if new1:
            if p:
                res["sent"]["staff"] = push(p, STAFF, "⏰ %d call back बाकी — 30 मिनट से ज़्यादा" % len(new1),
                                            names(new1) + " — अभी call back करें", STAFF_URL, "cb-clock-1")
            con.executemany("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", [key(c, 1) + (stamp,) for c in new1])
        if new2:
            if p:
                res["sent"]["backup"] = push(p, BACKUP, "⏰ 1 घंटा हो गया — %d call back अभी भी बाकी" % len(new2),
                                             names(new2) + " — Shavez ji, aap call karein", STAFF_URL, "cb-clock-2")
            con.executemany("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", [key(c, 2) + (stamp,) for c in new2])
        if do_close:
            if p:
                res["sent"]["owner"] = push(p, OWNER, "Callers not called back today: %d" % len(cs),
                                            "%d from unknown numbers · %d waited over an hour. Tap for the Call Console."
                                            % (res["unknown"], res["due2"]), OWNER_URL, "cb-clock-9")
            con.execute("INSERT OR IGNORE INTO sent(phone, t0, stage, at) VALUES(?,?,?,?)", close_key + (stamp,))
        res["new1"], res["new2"], res["closing"] = len(new1), len(new2), int(do_close)
        con.execute("INSERT INTO runs(at, open, unknown, s1, s2, closing, sent) VALUES(?,?,?,?,?,?,?)",
                    (stamp, res["open"], res["unknown"], len(new1), len(new2), int(do_close), repr(res["sent"])))
        con.execute("DELETE FROM runs WHERE at < ?", ((today - dt.timedelta(days=45)).isoformat(),))
        con.execute("DELETE FROM sent WHERE at < ?", ((today - dt.timedelta(days=45)).isoformat(),))
        con.commit()
    finally:
        con.close()
    print("%s not spoken to %d (unknown %d) · new at 30 min %d · new at 60 min %d · closing %d · sent %s · as of %s"
          % (stamp, res["open"], res["unknown"], res["new1"], res["new2"], res["closing"], res["sent"] or "-", res["asof"]))
    return res


if __name__ == "__main__":
    run(dry="--dry" in sys.argv[1:])
