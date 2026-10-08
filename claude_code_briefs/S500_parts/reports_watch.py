#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reports_watch.py -- S500_REPORT_CHECK (08-Oct-2026, D694, F-799): the morning reports' watch.

THE OWNER, 08-Oct-2026: the two morning Marg reports (yesterday's bill-wise sale report and the closing
stock) are made from the REPORT login by whoever is on morning duty; the page "Aaj ki reports" says of
each RIGHT or WRONG; the first wrong one gets a second try; "and I also get a notification when a right
report is not uploaded. Finally, after his two tries in the morning."

THREE THINGS LIVE HERE, and nothing else:

  1. THE SHORT-CLOSING RULE (F-799).  On 07-Oct a closing stock with every zero-stock item left out (250
     items against 379 the day before) passed as the day's closing everywhere: nothing compared a closing
     with the one before it.  closing_short(con, as_on, n_items) is that comparison, ONE function read by
     the page (reports_tile), by the snapshot door (stock_app /api/snapshot, which refuses a short one)
     and by this watch:  a closing is SHORT when it lists fewer items than reports.closing_min_share
     percent of the MEDIAN of the last 7 closings loaded before it (stock_snapshot) -- one short day, or one
     day swollen by a re-push after renames (stock_snapshot is upserted, never pruned), cannot move it.
     No earlier closing in 21 days -> no judgement.  Setting 0 -> the rule is off.  A real trim of Marg's
     item list by more than (100 - share) percent is refused too, until the setting is lowered.

  2. THE SETTINGS, every one a row of `setting` with its note (seeded by the installer, INSERT OR IGNORE):
       reports.tries              2       wrong tries before the owner is told
       reports.late_hhmm          10:00   the hour by which both must be right, else he is told
       reports.closing_min_share  90      percent (0 = off)
       reports.try_gap_min        3       files of one report within these minutes are ONE try
       reports.alert              on      the owner's phone message (on / off)

  3. THE OWNER'S ONE MESSAGE.  tick(con) rides the ten-minute job (order_rules.tick, 05:00-21:50, the venv
     python): it reads the page's own status (reports_tile.status -- the same judgement the staff see) and
     makes at most ONE row per report per day in marg_report_alert:
        kind 'wrong'  the report is wrong on reports.tries tries and no right copy has come
        kind 'late'   at or after reports.late_hhmm the report is not right (not in, or still wrong; a
                      file still being checked is given 30 more minutes)
     Never on a Sunday (the counter is closed).  A row not yet sent is withdrawn when the report turns
     right.  Unsent rows of today go out as ONE ntfy message through the same private topic the freshness
     watch and export_watch use (NTFY_URL in /root/finance/freshness.conf -- never printed), and are
     stamped sent_at only after the POST succeeds; a failed POST is tried again at the next tick.
     A right morning sends nothing.

NO WALK, NO SCRATCH RUN CAN REACH HIS PHONE.  A message leaves this box only when the connection's main
database IS the live one (/root/finance/finance.db) and no push stub is set (ORDER_PUSH_STUB,
ORDER_PUSH_NONE).  With REPORTS_NTFY_STUB=<file> the message is appended to that file instead (the walk).

OFF: /root/finance/_off/ALL_OFF or /root/finance/_off/REPORTS_WATCH_OFF (a file; nothing to restart), or
the setting reports.alert = off.  The short-closing rule is switched by its own setting, not by these.

WRITES ONLY marg_report_alert (and, through ensure(), the five setting rows).  No Flask here: stock_app
and the cron tick import this file on either python.
"""
import datetime as dt
import io
import json
import math
import os
import statistics
import sqlite3
import sys
import urllib.request

KIT = "S500_REPORT_CHECK"
VERSION = "S500 1.0"

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
CONF = "/root/finance/freshness.conf"          # fixed on purpose: no environment can point the message at another place
LIVE_DB = "/root/finance/finance.db"
OFF_DIR = os.environ.get("REPORTS_WATCH_OFF_DIR", "/root/finance/_off")
OFF_NAMES = ("ALL_OFF", "REPORTS_WATCH_OFF")
REF_CLOSINGS = 7          # the MEDIAN of this many earlier closings is the reference
REF_DAYS_BACK = 21        # ... looked for in this many calendar days before the closing
PENDING_GRACE_MIN = 30    # a file still being checked at the hour is given this long before he is told

SETTINGS = {
    "reports.tries": ("2", "Morning reports: wrong tries of one report before the owner is told (1-5)"),
    "reports.late_hhmm": ("10:00", "Morning reports: the hour by which both must be right, else the owner is told (HH:MM)"),
    "reports.closing_min_share": ("90", "Closing stock: a list with fewer items than this percent of the recent lists (the median of the last seven) is SHORT and is refused (0 = off)"),
    "reports.try_gap_min": ("3", "Morning reports: files of one report that arrive within this many minutes count as one try (0-30)"),
    "reports.alert": ("on", "Morning reports: the owner's phone message when a report is wrong twice or late (on / off)"),
}
NAMES = {"SALE_BILLWISE": "Sale report", "STOCK_CLOSING": "Closing stock"}

SCHEMA = ("CREATE TABLE IF NOT EXISTS marg_report_alert ("
          "day TEXT NOT NULL, key TEXT NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL, "
          "made_at TEXT NOT NULL, sent_at TEXT, PRIMARY KEY (day, key))")


# ------------------------------------------------------------------ settings
def setting(con, key):
    """The row's value, else the default.  A database with no setting table reads as the defaults."""
    default = SETTINGS[key][0]
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        return default
    v = str((r[0] if r else "") or "").strip()
    return v or default


def int_setting(con, key):
    v = setting(con, key)
    return int(v) if v.isdigit() else int(SETTINGS[key][0])


def tries_max(con):
    return max(1, min(5, int_setting(con, "reports.tries")))


def try_gap_min(con):
    return max(0, min(30, int_setting(con, "reports.try_gap_min")))


def alert_on(con):
    return setting(con, "reports.alert").strip().lower() not in ("off", "0", "no", "false")


def late_minutes(con):
    """reports.late_hhmm as minutes after midnight; 10:00 when the row does not read as HH:MM."""
    for v in (setting(con, "reports.late_hhmm"), SETTINGS["reports.late_hhmm"][0]):
        try:
            h, m = v.split(":")
            h, m = int(h), int(m)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return h * 60 + m
        except (ValueError, AttributeError):
            continue
    return 600


def hhmm(mins):
    return "%02d:%02d" % (mins // 60, mins % 60)


def ensure(con):
    """The alert table and the five setting rows (INSERT OR IGNORE: a value he has changed is never moved)."""
    con.execute(SCHEMA)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT NOT NULL, note TEXT)")
    for k, (v, note) in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    con.commit()


# ------------------------------------------------------------------ the short-closing rule (F-799)
def iso_day(s):
    """'07-10-2026' or '2026-10-07...' -> '2026-10-07'; '' when it is neither."""
    s = str(s or "").strip()[:10]
    try:
        if len(s) == 10 and s[2] == "-" and s[5] == "-":
            return dt.date(int(s[6:10]), int(s[3:5]), int(s[0:2])).isoformat()
        return dt.date.fromisoformat(s).isoformat()
    except (ValueError, IndexError):
        return ""


def closing_reference(con, as_on):
    """(items, 'YYYY-MM-DD') -- the MEDIAN item count of the last REF_CLOSINGS closings loaded before `as_on` (the upper one of an
    even number), and the newest of those days that has it; or None."""
    d = iso_day(as_on)
    if not d:
        return None
    day = dt.date.fromisoformat(d)
    names = [(day - dt.timedelta(days=i)).strftime("%d-%m-%Y") for i in range(1, REF_DAYS_BACK + 1)]
    try:
        rows = con.execute("SELECT as_on, COUNT(*) FROM stock_snapshot WHERE as_on IN (%s) GROUP BY as_on"
                           % ",".join("?" * len(names)), names).fetchall()
    except sqlite3.Error:
        return None
    have = sorted(((iso_day(r[0]), int(r[1])) for r in rows if iso_day(r[0])), reverse=True)[:REF_CLOSINGS]
    if not have:
        return None
    med = statistics.median_high([n for _x, n in have])
    return med, max(x for x, n in have if n == med)


def closing_short(con, as_on, n_items):
    """None when the closing is full (or cannot be judged, or the rule is off); else
    {'items', 'ref', 'ref_day', 'need', 'share'} -- it lists fewer than `share` percent of the reference."""
    share = int_setting(con, "reports.closing_min_share")
    if share <= 0:
        return None
    ref = closing_reference(con, as_on)
    if not ref:
        return None
    need = int(math.ceil(ref[0] * min(share, 100) / 100.0))
    n = int(n_items or 0)
    if n >= need:
        return None
    return {"items": n, "ref": ref[0], "ref_day": ref[1], "need": need, "share": min(share, 100)}


# ------------------------------------------------------------------ the owner's message
def told(con, day_iso):
    """{report key: sent_at or ''} for the day -- what the page reads to say 'khabar chali gayi hai'."""
    try:
        return {str(r[0]): str(r[1] or "") for r in
                con.execute("SELECT key, sent_at FROM marg_report_alert WHERE day=?", (day_iso,)).fetchall()}
    except sqlite3.Error:
        return {}


def _off():
    for n in OFF_NAMES:
        p = os.path.join(OFF_DIR, n)
        if os.path.exists(p):
            return p
    return ""


def is_off():
    """Is the message switched off by a file (the page says 'Doctor sahab ko bataiye' then, never 'khabar ja rahi hai')?"""
    return bool(_off())


def _is_live(con):
    try:
        for r in con.execute("PRAGMA database_list").fetchall():
            if str(r[1]) == "main":
                return bool(r[2]) and os.path.realpath(str(r[2])) == os.path.realpath(LIVE_DB)
    except sqlite3.Error:
        pass
    return False


def _conf_url():
    """NTFY_URL from freshness.conf, read as export_watch.read_conf reads it (the last line of a key wins).  Never printed."""
    url = ""
    try:
        with io.open(CONF, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "NTFY_URL":
                        url = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return url


def _send(con, title, body):
    """-> (sent, how).  Never prints or returns the URL."""
    stub = os.environ.get("REPORTS_NTFY_STUB", "")
    if stub:
        with io.open(stub, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"title": title, "body": body}) + "\n")
        return True, "stub"
    if os.environ.get("ORDER_PUSH_STUB") or os.environ.get("ORDER_PUSH_NONE"):
        return False, "a walk's push stub is set -- nothing sent"
    if not _is_live(con):
        return False, "not the live database -- nothing sent"
    url = _conf_url()
    if not url:
        return False, "NTFY_URL not set -- nothing sent"
    try:                                                         # the Request is built inside: a malformed address names no URL anywhere
        req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST",
                                     headers={"Title": title, "Priority": "default", "Tags": "warning"})
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:                                       # noqa: BLE001
        return False, "push FAILED (%s) -- tried again at the next tick" % e.__class__.__name__
    return True, "pushed to the owner's phone"


def _ddmm(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%m")
    except ValueError:
        return str(iso)


def _times(n):
    return "once" if n == 1 else ("twice" if n == 2 else "%d times" % n)


def decide(s, max_tries, late_min, now):
    """What the owner should be told NOW, from the page's own status: [{'key','kind','text'}].  Pure."""
    out = []
    if now.weekday() == 6:
        return out
    mins = now.hour * 60 + now.minute
    due = _ddmm(s.get("due_day"))
    for r in s.get("rows") or []:
        if not r.get("pair") or r.get("state") == "ok":
            continue
        w = r.get("s500") or {}
        name = NAMES.get(r.get("key"), str(r.get("key")))
        wrong = int(w.get("wrong") or 0)
        why = str(w.get("why_en") or "it did not pass the check")
        if r.get("state") in ("bad", "refused") and wrong >= max_tries:
            out.append({"key": r["key"], "kind": "wrong",
                        "text": "%s of %s is wrong %s: %s." % (name, due, _times(wrong), why)})
        elif mins >= late_min:
            if r.get("state") == "arrived":
                if mins < late_min + PENDING_GRACE_MIN:
                    continue
                text = "%s of %s has come but its check had not finished by %s." % (name, due, hhmm(late_min + PENDING_GRACE_MIN))
            elif r.get("state") in ("bad", "refused") and wrong:
                text = "%s of %s is still wrong at %s (%s): %s." % (name, due, hhmm(late_min), _times(wrong), why)
            else:
                text = "%s of %s has not come by %s." % (name, due, hhmm(late_min))
            out.append({"key": r["key"], "kind": "late", "text": text})
    return out


def _others(s, keys):
    """One short sentence for each of the pair that is NOT in this message."""
    out = []
    for r in s.get("rows") or []:
        if not r.get("pair") or r.get("key") in keys:
            continue
        name = "The %s" % NAMES.get(r.get("key"), str(r.get("key"))).lower()
        st = r.get("state")
        if st == "ok":
            out.append("%s is right." % name)
        elif st == "arrived":
            out.append("%s has come and is being checked." % name)
        elif st in ("bad", "refused"):
            out.append("%s is wrong so far." % name)
        else:
            out.append("%s has not come yet." % name)
    return out


def now_ist():
    return dt.datetime.now(IST)


def tick(con, now=None):
    """The ten-minute pass.  Never raises: the job it rides must not fail for this."""
    try:
        off = _off()
        if off:
            return {"ok": True, "off": os.path.basename(off)}
        if not alert_on(con):
            return {"ok": True, "off": "reports.alert"}
        if now is None or now.tzinfo is None:
            now = now_ist()
        if now.weekday() == 6:
            return {"ok": True, "quiet": "sunday"}
        _path = list(sys.path)                                   # the page's chain reader adds /root/marg_ingest to the path: put it back
        try:
            import reports_tile                                  # noqa: PLC0415 -- the page's own judgement, read not copied
            s = reports_tile.status(con, now.date(), now)
        finally:
            sys.path[:] = _path
        want = decide(s, tries_max(con), late_minutes(con), now)
        con.execute(SCHEMA)
        day = s["day"]
        have = {str(r[0]): str(r[1] or "") for r in
                con.execute("SELECT key, sent_at FROM marg_report_alert WHERE day=?", (day,)).fetchall()}
        right = {r["key"] for r in s["rows"] if r.get("pair") and r.get("state") == "ok"}
        withdrawn = 0
        for k, sent in list(have.items()):
            if not sent and k in right:                         # made, never sent, and the report is right now
                con.execute("DELETE FROM marg_report_alert WHERE day=? AND key=? AND sent_at IS NULL", (day, k))
                have.pop(k)
                withdrawn += 1
        made = 0
        for w in want:
            if w["key"] not in have:
                con.execute("INSERT OR IGNORE INTO marg_report_alert (day, key, kind, text, made_at) VALUES (?,?,?,?,?)",
                            (day, w["key"], w["kind"], w["text"], now.strftime("%Y-%m-%dT%H:%M:%S")))
                made += 1
        con.commit()
        unsent = con.execute("SELECT key, kind, text FROM marg_report_alert WHERE day=? AND sent_at IS NULL ORDER BY key",
                             (day,)).fetchall()
        if not unsent:
            return {"ok": True, "made": made, "withdrawn": withdrawn, "sent": 0}
        keys = {str(r[0]) for r in unsent}
        body = " ".join([str(r[2]) for r in unsent] + _others(s, keys))
        title = "Sanjeevni morning reports %s" % _ddmm(s.get("due_day"))
        ok, how = _send(con, title, body)
        if ok:
            con.execute("UPDATE marg_report_alert SET sent_at=? WHERE day=? AND sent_at IS NULL",
                        (now_ist().strftime("%Y-%m-%dT%H:%M:%S"), day))
            con.commit()
        return {"ok": True, "made": made, "withdrawn": withdrawn, "sent": len(unsent) if ok else 0, "how": how}
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "error": ("%s: %s" % (e.__class__.__name__, e))[:160]}


# ------------------------------------------------------------------ selftest (no network, no Flask)
def selftest():
    fails = []

    def ck(n, c):
        print(("  ok   " if c else "  FAIL ") + n)
        if not c:
            fails.append(n)
    con = sqlite3.connect(":memory:")
    ck("no snapshot table: no judgement", closing_short(con, "2026-10-07", 10) is None)
    con.execute("CREATE TABLE stock_snapshot (as_on TEXT, item TEXT, qty INTEGER, PRIMARY KEY (as_on, item))")
    ck("no earlier closing: no judgement", closing_short(con, "2026-10-07", 10) is None)
    for as_on, n in (("04-10-2026", 379), ("05-10-2026", 379), ("06-10-2026", 250)):
        con.executemany("INSERT INTO stock_snapshot VALUES (?,?,0)", [(as_on, "W%d" % i) for i in range(n)])
    ck("the reference is the median of the earlier closings: one short day does not move it", closing_reference(con, "2026-10-07") == (379, "2026-10-05"))
    ck("the closing's own day is never its reference", closing_reference(con, "06-10-2026") == (379, "2026-10-05"))
    x = closing_short(con, "06-10-2026", 250)
    ck("250 against 379 is SHORT at 90 percent", bool(x) and x["ref"] == 379 and x["need"] == 342 and x["items"] == 250)
    ck("379 and 342 are full; 341 is short", closing_short(con, "2026-10-07", 379) is None and closing_short(con, "2026-10-07", 342) is None
       and bool(closing_short(con, "2026-10-07", 341)))
    ck("a closing 30 days later has no reference in reach", closing_short(con, "2026-11-10", 5) is None)
    con.executemany("INSERT INTO stock_snapshot VALUES ('07-10-2026',?,0)", [("V%d" % i,) for i in range(424)])
    ck("one swollen day (a re-push after renames) does not move the median either", closing_reference(con, "2026-10-08") == (379, "2026-10-05"))
    ensure(con)
    ck("ensure seeds the five rows and keeps the defaults", tries_max(con) == 2 and late_minutes(con) == 600 and try_gap_min(con) == 3 and alert_on(con))
    con.execute("UPDATE setting SET value='0' WHERE key='reports.closing_min_share'")
    ck("the share at 0 switches the rule off", closing_short(con, "2026-10-07", 5) is None)
    con.execute("UPDATE setting SET value='xx' WHERE key='reports.late_hhmm'")
    ck("a late hour that does not read as HH:MM is 10:00", late_minutes(con) == 600)
    at = lambda h, m=0, d=8: dt.datetime(2026, 10, d, h, m, tzinfo=IST)   # noqa: E731 -- 08-Oct-2026 is a Thursday
    row = lambda key, state, **w: {"key": key, "pair": True, "state": state, "s500": w}   # noqa: E731
    s = {"day": "2026-10-08", "due_day": "2026-10-07",
         "rows": [row("SALE_BILLWISE", "ok", wrong=0), row("STOCK_CLOSING", "bad", wrong=1, why_en="zero-stock items are missing")]}
    ck("wrong once before the hour: nothing", decide(s, 2, 600, at(8, 10)) == [])
    s["rows"][1]["s500"]["wrong"] = 2
    d = decide(s, 2, 600, at(8, 20))
    ck("wrong twice: told at once, in words", len(d) == 1 and d[0]["kind"] == "wrong" and "Closing stock of 07-10 is wrong twice: zero-stock items are missing." == d[0]["text"])
    s["rows"][1] = row("STOCK_CLOSING", "due", wrong=0)
    ck("not in before the hour: nothing", decide(s, 2, 600, at(9, 50)) == [])
    d = decide(s, 2, 600, at(10, 0))
    ck("not in at the hour: told", len(d) == 1 and d[0]["kind"] == "late" and d[0]["text"] == "Closing stock of 07-10 has not come by 10:00.")
    s["rows"][1] = row("STOCK_CLOSING", "arrived", wrong=0)
    ck("still being checked at the hour: 30 minutes of grace, then told",
       decide(s, 2, 600, at(10, 20)) == [] and len(decide(s, 2, 600, at(10, 30))) == 1)
    ck("a Sunday is quiet", decide(s, 2, 600, at(11, 0, d=11)) == [])
    ck("the other report gets one sentence", _others(s, {"STOCK_CLOSING"}) == ["The sale report is right."])
    _stub = os.environ.pop("REPORTS_NTFY_STUB", None)            # a walk's stub would answer for the phone
    ck("no message leaves a database that is not the live one", _send(con, "t", "b")[0] is False)
    if _stub is not None:
        os.environ["REPORTS_NTFY_STUB"] = _stub
    print("reports_watch selftest: %d failure(s)" % len(fails))
    return 1 if fails else 0


def main(argv=None):
    """--selftest (the default) | --say : what the owner would be told NOW, from the database of FINANCE_DB; writes nothing, sends
    nothing | --test-message : ONE message to the owner's phone that says it is a test (the installer's proof that the route works)."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or "--selftest" in args:
        return selftest()
    con = sqlite3.connect(os.environ.get("FINANCE_DB", LIVE_DB))
    con.row_factory = sqlite3.Row
    try:
        if "--say" in args:
            import reports_tile                                  # noqa: PLC0415
            now = now_ist()
            s = reports_tile.status(con, now.date(), now)
            for r in s["rows"]:
                if r.get("pair"):
                    w = r.get("s500") or {}
                    print("%s: %s (tries %s, wrong %s)%s" % (NAMES.get(r["key"], r["key"]), r["state"], w.get("tries"), w.get("wrong"),
                                                            (" -- " + w["why_en"]) if w.get("why_en") else ""))
            want = decide(s, tries_max(con), late_minutes(con), now)
            print("would tell the owner now: %s" % ("; ".join(w["text"] for w in want) or "nothing"))
            print("switched off by %s" % (_off() or "nothing") + "; reports.alert = %s; NTFY_URL %s"
                  % (setting(con, "reports.alert"), "is set" if _conf_url() else "is NOT set"))
            return 0
        if "--test-message" in args:
            ok, how = _send(con, "Sanjeevni morning reports - test",
                            "A test from the install of S500. This is where you will be told when a morning Marg report is wrong "
                            "twice or has not come by the hour. Nothing is wrong now.")
            print("test message: %s" % how)
            return 0 if ok else 1
        print("use --selftest, --say or --test-message")
        return 2
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
