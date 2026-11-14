#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xray_photo_nudge.py -- kit S790_XRAY_PHOTO_NUDGE (session S428, 11-Nov-2026, the parent). NEW.
S834_XRAY_DUE_RULE (session S462, 14-Nov-2026, D979 item 1): an X-ray counts only once it is DUE -- a morning X-ray at
15:00 the same day, an evening X-ray at 15:00 the next day (the shift is Docterz's own, clinic_day_line.shift, the X-ray
line first; a slip with no Docterz line yet goes by its own time: typed that day before 16:00 = morning, else evening);
a photo filed for the patient on the slip's day or the two days after counts; the count looks back 7 days, not to
23-Sep. The same rule, byte-equal, in DUTY_MAP alisha.xray_photo, slip_log.xray_pending and records.xray_items.

THE OWNER, 11-Nov-2026 09:49 / 09:51 IST: a notification on the staff phones when X-ray photos have not been put in the Drive folder --
"The notification should be at 3 p.m. and 6 p.m. and both notifications related work when completed should also be flagged everywhere,
and if it is not done then it also remains flagged so that it is visible to everyone."

WHAT IT DOES. Run by cron at 15:00 and 18:00 IST. It reads finance.db READ-ONLY and counts the X-rays with no photo yet: every X-ray slip
(series xp, an X-ray item, a clinic ID) of the last 7 days through TODAY that is DUE (S834, above), with no X-ray photo filed for that
ID within two days, none on its way (the filing plan holds it), and not marked 'X-ray not done' -- the same rule as reception's
Aaj ka kaam line alisha.xray_photo (DUTY_MAP). Then ONE notification to every phone of PUSH_TO that allowed the portal's notifications (the portal's own push,
ring_common.push_user):
  * photos pending   -> how many (today's and older), tap opens Report baaki's X-ray list -- where each stays until its photo is in;
  * none pending     -> "all of today's X-ray photos are in" (the work shown as done).
Hindi for staff, English for the owner. Its result goes to STATE (time, counts, sent) -- the record that it ran.

CLI:  xray_photo_nudge.py          the run (what cron calls)
      xray_photo_nudge.py --dry    counts only; pushes nothing, writes nothing
Stdlib only (+ ring_common from /root/portal for the push: absent = counted, nothing sent).
"""
import datetime as dt
import json
import os
import sqlite3
import sys

VERSION = "S834 1"
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
STATE = os.environ.get("XN_STATE", "/root/finance/xray_photo_nudge_state.json")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
LOOKBACK_DAYS = 7                             # S834: the count looks back 7 days (the plan, point 1), not to 23-Sep
STAFF = ("reception", "shivani", "alisha", "shavez")       # the owner 09:57 IST: not Sukhveer -- he is for the lab work only
OWNER = ("manoj",)
URL = "/finance/slips/pending?t=xray"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

# S834: the due rule -- byte-equal with DUTY_MAP alisha.xray_photo, slip_log.XRAY_DUE / XRAY_FILED and records.XRAY_DUE / XRAY_FILED.
XRAY_DUE = ("(CASE COALESCE("
            "(SELECT MIN(lower(trim(l.shift))) FROM clinic_day_line l WHERE l.business_date = s.day AND l.clinic_id = s.clinic_id "
            "AND l.section = 'xray' AND lower(trim(l.shift)) IN ('morning', 'evening')), "
            "(SELECT MIN(lower(trim(l.shift))) FROM clinic_day_line l WHERE l.business_date = s.day AND l.clinic_id = s.clinic_id "
            "AND lower(trim(l.shift)) IN ('morning', 'evening')), "
            "CASE WHEN substr(s.logged_at, 1, 10) = s.day AND substr(s.logged_at, 12, 5) < '16:00' THEN 'morning' ELSE 'evening' END) "
            "WHEN 'morning' THEN s.day || ' 15:00:00' ELSE date(s.day, '+1 day') || ' 15:00:00' END)")
XRAY_FILED = ("NOT EXISTS (SELECT 1 FROM record_file f WHERE f.kind = 'xray' AND f.state = 'ok' AND f.clinic_id = s.clinic_id "
              "AND f.day >= s.day AND f.day <= date(s.day, '+2 day'))")
SQL = ("SELECT s.day AS day, s.clinic_id AS cid FROM slip s JOIN slip_item i ON i.slip_id = s.id AND i.kind = 'xray' "
       "WHERE s.series = 'xp' AND s.state = 'ok' AND s.clinic_id <> '' AND s.day >= ? AND s.day <= ? "
       "AND " + XRAY_DUE + " <= ? AND " + XRAY_FILED + " "
       "AND NOT EXISTS (SELECT 1 FROM xray_filing x WHERE x.clinic_id = s.clinic_id AND x.day >= s.day AND x.day <= date(s.day, '+2 day') "
       "AND x.state IN ('planned', 'done')) "
       "AND NOT EXISTS (SELECT 1 FROM pend_mark m WHERE m.key = 'xm:' || s.day || ':' || s.clinic_id AND m.act = 'not_done') "
       "AND NOT EXISTS (SELECT 1 FROM record_check c WHERE c.key = 'xm:' || s.day || ':' || s.clinic_id AND c.answer = 'not_done') "
       "GROUP BY s.day, s.clinic_id")
SQL_TODAY_ALL = ("SELECT COUNT(*) FROM (SELECT DISTINCT s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id = s.id AND i.kind = 'xray' "
                 "WHERE s.series = 'xp' AND s.state = 'ok' AND s.clinic_id <> '' AND s.day = ?)")


def now_ist():
    return dt.datetime.now(IST)


def counts(con, today, now=None):
    """(pending today, pending older, X-rays today in all). Only what is DUE by `now` ('YYYY-MM-DD HH:MM:SS', IST) counts (S834)."""
    now = now or now_ist().strftime("%Y-%m-%d %H:%M:%S")
    since = (dt.date.fromisoformat(today) - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    rows = con.execute(SQL, (since, today, now)).fetchall()
    t = sum(1 for r in rows if r[0] == today)
    total = con.execute(SQL_TODAY_ALL, (today,)).fetchone()[0]
    return t, len(rows) - t, total


def cards(t, old, total):
    """{'hi': (title, body), 'en': (title, body)}."""
    n = t + old
    if n:
        hi = ("\U0001F4F7 X-ray photo baaki: %d" % n,
              "Aaj ki %d%s — folder mein daaliye. List ke liye dabaiye." % (t, (", pehle ki %d" % old) if old else ""))
        en = ("\U0001F4F7 X-ray photos not in the folder: %d" % n,
              "Today %d of %d%s · reception to put them in. Tap for the list." % (t, total, (" · older %d" % old) if old else ""))
    else:
        hi = ("✅ X-ray photo: sab aa gayi", "Aaj ki sab %d X-ray photo folder mein hain." % total if total else "Aaj koi X-ray parchi nahi.")
        en = ("✅ All of today's X-ray photos are in", ("%d of %d in the folder." % (total, total)) if total else "No X-ray slip today.")
    return {"hi": hi, "en": en}


def send(c, pusher=None):
    try:
        if pusher is None:
            if PORTAL_DIR not in sys.path:
                sys.path.insert(0, PORTAL_DIR)
            import ring_common as rc                     # noqa: PLC0415
            pusher = rc.push_user
    except Exception as e:                               # noqa: BLE001
        return {"error": "no push: %s" % type(e).__name__}
    out = {}
    for who in STAFF + OWNER:
        title, body = c["en"] if who in OWNER else c["hi"]
        try:
            s, f = pusher(who, {"title": title, "body": body, "url": URL, "tag": "xray-photo", "ttl": 3 * 3600})
        except Exception:                                # noqa: BLE001
            s, f = 0, 1
        out[who] = [s, f]
    return out


def run(dry=False, pusher=None, today=None, now=None):
    now = now or os.environ.get("XN_NOW", "") or now_ist().strftime("%Y-%m-%d %H:%M:%S")   # XN_NOW pins the clock for the walk
    today = today or now[:10]
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=10)
    try:
        t, old, total = counts(con, today, now)
    finally:
        con.close()
    c = cards(t, old, total)
    st = {"version": VERSION, "at": now_ist().strftime("%Y-%m-%d %H:%M:%S"), "today": today, "pending_today": t,
          "pending_older": old, "xrays_today": total}
    if dry:
        print("DRY %s: pending today %d (of %d X-rays today), older %d; nothing sent" % (today, t, total, old))
        return st
    st["sent"] = send(c, pusher)
    try:
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(st, fh)
        os.replace(tmp, STATE)
    except Exception:                                    # noqa: BLE001
        pass
    print("%s pending today %d / %d, older %d, sent %s" % (st["at"], t, total, old,
          sum(v[0] for v in st["sent"].values()) if isinstance(st["sent"], dict) and "error" not in st["sent"] else st["sent"]))
    return st


if __name__ == "__main__":
    run(dry="--dry" in sys.argv[1:])
