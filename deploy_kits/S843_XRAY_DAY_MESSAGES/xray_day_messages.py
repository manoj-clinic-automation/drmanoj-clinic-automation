#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xray_day_messages.py -- kit S843_XRAY_DAY_MESSAGES (the parent; session 469, 14-Nov-2026). NEW. D979 item 6.

THE OWNER (13-Nov-2026 19:27-19:34 IST, S450 study sec I point 2; the wording approved 22:03 IST 14-Nov on the mock-up
https://claude.ai/artifact/W5TAwHRWP5zFBpN9HtqFhB, artboard "The messages -- final wording (S469)"): reception gets
yesterday's X-ray list at 9:30 am and, in the evening after the upload, a confirmation -- "all N in" or "n of N in, the rest
named"; he gets the evening line too. Counts on the lock screen, names inside the portal. Nothing on a day with no X-ray and
no blood test. The 3 pm / 6 pm notice (xray_photo_nudge.py) stays as it is.

WHAT IT DOES. Run by cron, twice a day:
  morning (09:30)  to RECEPTION -- the 'Kal ki X-ray' card of Check karein (check_screens.kal_card on check_screens.day_strip):
                   the newest X-ray day before today, how many photos are in, how many are still to come, and what is still
                   baaki from the 7 days before it. Not sent when that day is not yesterday and nothing is baaki, nor
                   on a Sunday (the clinic is closed; Monday's message carries Saturday).
  evening (19:00)  to RECEPTION -- "Aaj ki upload": the X-rays due by 3 pm today (yesterday evening's, this morning's; a
                   a Docterz-only X-ray line by its Docterz shift), how many filed (or on their way), the rest counted.
                   Not sent when none was due, nor on a day with no X-ray and no blood test (a closed Sunday).
                   to HIM -- X-rays as above, today's blood tests (report in / not in yet) and the Check karein
                   questions open (check_screens.counts: waiting pictures, likely-wrong lab IDs, not-in-Docterz X-rays).
                   Not sent when no X-ray was due and no blood test was written today.
  Every list and every state comes from check_screens / records -- the due rule is never copied here (F-1384).
  The tap opens the page with the names: reception /finance/checks (the Kal ki X-ray card), him /finance/records/xray-check
  (Last 7 days). Same notification slot as the 3 / 6 pm notice (tag 'xray-photo'): the newest replaces the older on a phone.

SAFE BY CONSTRUCTION. finance.db is opened READ-ONLY (a write anywhere in the path raises and nothing is sent). No name,
number or ID is ever in a notification, the state file or the log -- counts only. Switches: /root/finance/_off/ALL_OFF or
/root/finance/_off/xray_day_messages (either present = nothing sent). Its result goes to STATE (time, mode, counts, sent).

CLI:  xray_day_messages.py morning|evening          the run (what cron calls)
      xray_day_messages.py morning|evening --dry    the texts and counts printed; nothing sent, nothing written
Needs the venv python (records / check_screens import flask). Push: ring_common.push_user from /root/portal.
"""
import datetime as dt
import json
import os
import sqlite3
import sys

VERSION = "S843 2"
FIN = os.environ.get("XD_FIN_DIR", "/root/finance")
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
STATE = os.environ.get("XD_STATE", "/root/finance/xray_day_messages_state.json")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
OFF = (os.path.join(FIN, "_off", "ALL_OFF"), os.path.join(FIN, "_off", "xray_day_messages"))
RECEPTION = ("reception", "shivani", "alisha")
OWNER = ("manoj",)
URL_STAFF = "/finance/checks"
URL_OWNER = "/finance/records/xray-check"
TAG = "xray-photo"                                   # the 3 / 6 pm notice's slot: the newest replaces the older
TTL = 10 * 3600
IN_ST = ("filed", "filing")                          # a photo filed, or on its way (the next filing run files it)
GONE_ST = ("notdone", "answered")                    # 'X-ray nahi hua' -- not an X-ray to upload


def _mods():
    if FIN not in sys.path:
        sys.path.insert(0, FIN)
    import records                                   # noqa: PLC0415 -- importing it attaches check_screens
    import check_screens as cs                       # noqa: PLC0415
    records._schema_done = True                      # the app made the tables; a read-only run never creates them
    cs._rec()
    return records, cs


def _con():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    return con


def _day(d):
    try:
        return dt.date.fromisoformat(d[:10]).strftime("%d %b").lstrip("0")
    except (ValueError, TypeError):
        return d or ""


def _n(k, one, many):
    return "%d %s" % (k, one if k == 1 else many)


# ---------------------------------------------------------------- the morning: reception's 'Kal ki X-ray'
def morning_text(strip, kal, today):
    """{'staff': (title, body)} or {} (silent), and the counts."""
    yday = (dt.date.fromisoformat(today) - dt.timedelta(days=1)).isoformat()
    if dt.date.fromisoformat(today).weekday() == 6:
        return {}, {"why": "Sunday: the clinic is closed; Monday's message carries Saturday"}
    if not kal:
        return {}, {"why": "no X-ray day in the week"}
    filed, rest, older = kal["filed"], len(kal["rows"]), len(kal["older"])
    n = filed + rest
    cnt = {"day": kal["day"], "n": n, "filed": filed, "rest": rest, "older": older}
    if kal["day"] != yday and not rest and not older:
        return {}, dict(cnt, why="yesterday no X-ray, nothing baaki")
    d = _day(kal["day"])
    more = " Pichhle 7 din se %d aur baaki." % older if older else ""
    if not n:                                        # that day's X-rays were all 'X-ray nahi hua' (cold review 3)
        if not older:
            return {}, dict(cnt, why="no X-ray to upload")
        t = ("📷 X-ray: pichhle 7 din se %d baaki" % older, "Naam ke liye dabaiye.")
    elif rest:
        when = "aaj 3 baje tak" if kal["day"] == yday else "abhi"
        t = ("📷 X-ray %s: %d mein se %d ki photo aa gayi" % (d, n, filed),
             "%d baaki — %s upload kijiye.%s Naam ke liye dabaiye." % (rest, when, more))
    else:
        t = ("✅ X-ray %s: sab %d ki photo aa gayi" % (d, n),
             ("Pichhle 7 din se %d baaki. Naam ke liye dabaiye." % older) if older else "Pichhle 7 din se kuch baaki nahi.")
    return {"staff": t}, cnt


# ---------------------------------------------------------------- the evening: 'Aaj ki upload' and his line
def due_today(strip, shift=None):
    """The X-ray rows due by 3 pm today: yesterday's evening X-rays, today's morning X-rays. A Docterz-only line (sh '': no
    slip) goes by its Docterz shift as records.XRAY_DUE does -- morning due that day, evening (or none read) the next day
    (cold review 2). shift: {(day, clinic ID): 'morning'|'evening'}."""
    shift = shift or {}
    t = next((s for s in strip if s["today"]), None)
    y = strip[1] if len(strip) > 1 and t is strip[0] else None

    def sh(s, r):
        return r.get("sh") or ("subah" if shift.get((s["day"], r["cid"])) == "morning" else "shaam")
    rows = []
    if y:
        rows += [dict(r, part="y") for r in y["x"]["rows"] if sh(y, r) == "shaam" and r["st"] not in GONE_ST]
    if t:
        rows += [dict(r, part="t") for r in t["x"]["rows"] if sh(t, r) == "subah" and r["st"] not in GONE_ST]
    return rows, t


def evening_text(strip, questions, shift=None):
    rows, t = due_today(strip, shift)
    n = len(rows)
    inn = sum(1 for r in rows if r["st"] in IN_ST)
    issue = sum(1 for r in rows if r["st"] == "issue")
    miss = n - inn - issue
    y_n = sum(1 for r in rows if r["part"] == "y")
    t_n = n - y_n
    b = [r for r in ((t or {}).get("b") or {}).get("rows", [])]
    b_n = len(b)
    b_in = sum(1 for r in b if r["st"] == "in")
    b_wait = b_n - b_in                              # today's: records opens a late item only after 2 days (cold review 4)
    cnt = {"x_due": n, "x_in": inn, "x_issue": issue, "x_miss": miss, "x_yday_evening": y_n, "x_today_morning": t_n,
           "b_n": b_n, "b_in": b_in, "b_wait": b_wait, "questions": questions,
           "x_today_any": len(((t or {}).get("x") or {}).get("rows", []))}
    out = {}
    if not cnt["x_today_any"] and not b_n:           # his rule: nothing on a day with no X-ray and no blood test (a closed Sunday)
        return out, dict(cnt, why="no X-ray and no blood test today")
    if n:
        if inn == n:
            parts = [p for p in (("kal shaam ki %d" % y_n) if y_n else "", ("aaj subah ki %d" % t_n) if t_n else "") if p]
            body = " aur ".join(parts) + " — sab aa gayi."
            out["staff"] = ("✅ Aaj ki upload: %d mein se %d photo file ho gayi" % (n, n), body[0].upper() + body[1:])
        else:
            why = [p for p in (("%d ki photo nahi aayi" % miss) if miss else "", ("%d mein dikkat" % issue) if issue else "") if p]
            out["staff"] = ("📷 Aaj ki upload: %d mein se %d file — %d baaki" % (n, inn, n - inn),
                            ", ".join(why) + ". Kal 3 baje tak. Naam ke liye dabaiye.")
    if n or b_n:
        head = []
        if n:
            head.append("X-rays %d of %d filed" % (inn, n))
        if b_n:
            head.append("Blood %d of %d in" % (b_in, b_n))
        body = []
        if miss:
            body.append(_n(miss, "X-ray pending", "X-rays pending"))
        if issue:
            body.append(_n(issue, "X-ray photo needs a check", "X-ray photos need a check"))
        if b_wait:
            body.append(_n(b_wait, "blood report not in yet", "blood reports not in yet"))
        body.append(("Check karein: %s open" % _n(questions, "question", "questions")) if questions else "Check karein: nothing open")
        out["owner"] = ("Records today: " + " · ".join(head), " · ".join(body) + ".")
    return out, cnt


# ---------------------------------------------------------------- the push and the run
def send(texts, pusher=None):
    try:
        if pusher is None:
            if PORTAL_DIR not in sys.path:
                sys.path.insert(0, PORTAL_DIR)
            import ring_common as rc                     # noqa: PLC0415
            pusher = rc.push_user
    except Exception as e:                               # noqa: BLE001
        return {"error": "no push: %s" % type(e).__name__}
    out = {}
    for key, who, url in (("staff", RECEPTION, URL_STAFF), ("owner", OWNER, URL_OWNER)):
        if key not in texts:
            continue
        title, body = texts[key]
        for w in who:
            try:
                s, f = pusher(w, {"title": title, "body": body, "url": url, "tag": TAG, "ttl": TTL})
            except Exception:                            # noqa: BLE001
                s, f = 0, 1
            out[w] = [s, f]
    return out


def build(mode):
    """(texts, counts) for this mode, from the live lists. Raises on any fault -- then nothing is sent."""
    R, cs = _mods()
    con = _con()
    try:
        strip = cs.day_strip(con)
        today = R._today()
        if mode == "morning":
            return morning_text(strip, cs.kal_card(strip), today)
        c = cs.counts(con)
        q = int(c.get("wait", 0)) + int(c.get("lab", 0)) + int(c.get("pgap", 0))
        y = (dt.date.fromisoformat(today) - dt.timedelta(days=1)).isoformat()
        shift = {}
        for r in R._rows(con, "SELECT business_date d, clinic_id c, lower(trim(shift)) f FROM clinic_day_line "
                              "WHERE business_date IN (?, ?) AND clinic_id<>'' AND lower(trim(shift)) IN ('morning', 'evening') "
                              "ORDER BY (section <> 'xray'), lower(trim(shift))", (y, today)):
            shift.setdefault((r["d"], r["c"]), r["f"])       # the X-ray line's shift first, then any line's (records.XRAY_DUE)
        return evening_text(strip, q, shift)
    finally:
        con.close()


def _write_state(st):
    try:
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(st, fh, ensure_ascii=False)
        os.replace(tmp, STATE)
    except Exception:                                    # noqa: BLE001
        pass


def run(mode, dry=False, pusher=None):
    now = dt.datetime.now().replace(microsecond=0).isoformat(sep=" ")          # the box's clock is IST
    st = {"version": VERSION, "at": now, "mode": mode}
    if mode not in ("morning", "evening"):
        print("usage: xray_day_messages.py morning|evening [--dry]")
        return 2
    off = [p for p in OFF if os.path.exists(p)]
    if off and not dry:
        st["sent"] = "off: " + os.path.basename(off[0])
        _write_state(st)
        print("%s %s OFF (%s) -- nothing sent" % (now, mode, os.path.basename(off[0])))
        return 0
    try:
        texts, cnt = build(mode)
    except Exception as e:                               # noqa: BLE001
        st["error"] = type(e).__name__              # the type only: a message could carry an ID (cold review 1)
        if not dry:
            _write_state(st)
        print("%s %s ERROR %s -- nothing sent" % (now, mode, st["error"]))
        return 1
    st["counts"] = cnt
    st["texts"] = {k: list(v) for k, v in texts.items()}
    if dry:
        print("DRY %s %s counts %s" % (now, mode, json.dumps(cnt, ensure_ascii=False)))
        for k, (t, b) in texts.items():
            print("  [%s] %s | %s" % (k, t, b))
        if not texts:
            print("  (silent)")
        return 0
    st["sent"] = send(texts, pusher) if texts else "silent"
    _write_state(st)
    print("%s %s %s sent %s" % (now, mode, json.dumps(cnt, ensure_ascii=False), json.dumps(st["sent"])))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(run(a[0] if a else "", dry="--dry" in a))
