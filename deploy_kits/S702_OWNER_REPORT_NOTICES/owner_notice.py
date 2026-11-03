#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
owner_notice.py -- S702_OWNER_REPORT_NOTICES (03-Nov-2026, Sanjeevni session 380): the owner is told when the Marg work is DONE.

THE OWNER, 03-Nov-2026 09:43-10:10 IST: "how do I get notified for the reports when they are generated or they are missing ... and a
confirmation from the server that the reports have been correctly arrived there"; 10:04: "the Shavez exports are the ones which I need to
manually confirm from him daily. So I want them to appear as soon as his work is done. Amir comes and does his work, so I get that when he
does it. Same flow for Darpan's purchase orders ... Saturday work is exported on Sunday, and Amir also works on Sunday ... Don't make them
silent on Sundays."  10:10: "build it now".

WHAT IT SAYS, each message ONCE (table owner_notice, one row per key), every day of the week:
  pair:<day>             Morning reports ✓ -- the sale report and the closing stock of the due day both certified (the page's own judgement,
                         reports_tile.status -- read, never copied).
  valuation:<yyyy-mm>    Stock Valuation ✓ (1st-7th) -- and valuation_due:<day> each evening from owner_notice.valuation_hhmm until it comes.
  amir:<day>             Amir's work ✓ -- on an Amir day (his punch or his page): purchase item-wise, bill-wise and the Batch Stock (whole
                         store, the run has read it), with the batch fixes done / left; amir_missing:<day> at owner_notice.amir_missing_hhmm
                         when something of the three is not in.
  sheet:<id>             Darpan's order sheet ✓ -- every sheet the server took (order_sheet), with its suppliers and medicines;
  sheet_refused:<at>     ... or refused, with the reason.
  list_soon / list_due   his own three lists (salt, category, item): at owner_notice.lists_hhmm, owner_notice.lists_days_before days before
                         the due day and on the due day (the due day = the last list + its limit, reports_tile.owner_lists);
  list_overdue:<day>     ... overdue: on the install's day and then once a week until it comes;
  list_in:<md5>          ... and a confirmation when one arrives: checked by the spine's certified reader (or failed / refused).
  phone:<last ask>       F-1089: the reception phone has not asked the server for owner_notice.phone_quiet_min minutes inside the working
                         window (09:00-20:00; Sunday 09:00-14:00) -- once per silence; phone_refused:<day> when it asks and is refused.
  After 21:00 the pair of TODAY is looked for too, so an evening export is said that evening, not at midnight.
Nothing that happened before the install (owner_notice.since) is announced.

WHERE IT GOES: the clinic app (Web Push) on every device the owner's login allowed (owner_notice.to, default "manoj"; tapping opens his
command console); when none of them has a device, the same private ntfy topic the morning-report alarms use.  A message that could not go is
tried at the next tick, at most MAX_TRIES times, and never after a day.

NO WALK CAN REACH A PHONE: a message leaves only when the connection's main database IS the live one and no stub is set
(OWNER_NOTICE_STUB=<file> appends the message there; ORDER_PUSH_STUB / ORDER_PUSH_NONE send nothing).

    /root/wa/venv/bin/python3 -B owner_notice.py tick              (cron, every 5 minutes)
    /root/wa/venv/bin/python3 -B owner_notice.py test              (one test message -- the install's proof of the road)
    /root/wa/venv/bin/python3 -B owner_notice.py show              (the last 15 rows)
    /root/wa/venv/bin/python3 -B owner_notice.py collect [--now 2026-11-03T10:30]   (what it WOULD say now; writes nothing)

OFF: /root/finance/_off/ALL_OFF or /root/finance/_off/OWNER_NOTICE_OFF (a file), or the setting owner_notice.on = off.
WRITES ONLY owner_notice and its setting rows.  Reads finance.db, the page's judgement and the order sheets.
"""
import datetime as dt
import json
import os
import sqlite3
import sys

KIT = "S702_OWNER_REPORT_NOTICES"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
LIVE_DB = "/root/finance/finance.db"
OFF_DIR = os.environ.get("FINANCE_OFF_DIR", "/root/finance/_off")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
CONSOLE_URL = "/finance/console"
MAX_TRIES = 12
LIST_NAMES = {"SALT_WISE_ITEM_LIST": "Salt list", "CATEGORY_WISE_ITEM_LIST": "Category list", "ITEM_MASTER": "Item list"}

SETTINGS = (
    ("owner_notice.on", "on", "S702: the owner's work-done messages (on / off)"),
    ("owner_notice.to", "manoj", "S702: the logins whose clinic-app devices get the messages (comma-separated); ntfy when none has a device"),
    ("owner_notice.since", "", "S702: set by the install -- nothing that happened before it is announced"),
    ("owner_notice.amir_missing_hhmm", "23:40", "S702: on an Amir day, what is still missing of his three exports is said at this time"),
    ("owner_notice.valuation_hhmm", "20:00", "S702: from the 1st to the 7th, the Stock Valuation not yet in is said each evening at this time"),
    ("owner_notice.lists_hhmm", "09:00", "S702: the owner's three lists -- the reminder goes at this time"),
    ("owner_notice.lists_days_before", "2", "S702: the owner's three lists -- the first reminder this many days before the due day"),
    ("owner_notice.phone_quiet_min", "60", "S702 (F-1089): the reception phone silent this long inside the working window -- the owner is told once"),
    ("owner_notice.phone_from", "09:00", "S702 (F-1089): the working window opens"),
    ("owner_notice.phone_to", "20:00", "S702 (F-1089): the working window closes, Monday to Saturday"),
    ("owner_notice.phone_to_sunday", "14:00", "S702 (F-1089): the working window closes on a Sunday (the half day)"),
)

SCHEMA = ("CREATE TABLE IF NOT EXISTS owner_notice (id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, "
          "title TEXT NOT NULL, body TEXT NOT NULL, made_at TEXT NOT NULL, sent_at TEXT, how TEXT, tries INTEGER NOT NULL DEFAULT 0)")


# ------------------------------------------------------------------ small helpers
def now_ist():
    return dt.datetime.now(IST).replace(microsecond=0)


def stamp(t):
    return t.strftime("%Y-%m-%d %H:%M:%S")


def norm_ts(s):
    """Any stamp the estate writes ('2026-11-03T09:12:33+05:30', '2026-11-03 09:12', '20261103-091233') -> 'YYYY-MM-DD HH:MM:SS' or ''."""
    s = str(s or "").strip()
    if len(s) >= 15 and s[8] == "-" and s[:8].isdigit():
        s = "%s-%s-%s %s:%s:%s" % (s[:4], s[4:6], s[6:8], s[9:11], s[11:13], s[13:15])
    s = s.replace("T", " ")[:19]
    if len(s) == 16:
        s += ":00"
    return s if len(s) == 19 and s[4] == "-" else ""


def ddmm(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%m")
    except ValueError:
        return str(iso or "")


def hhmm_of(ts):
    t = norm_ts(ts)
    return t[11:16] if t else ""


def mins(hm, default):
    try:
        h, m = str(hm).split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return default


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def setting(con, key):
    default = next((d for k, d, _n in SETTINGS if k == key), "")
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    except sqlite3.Error:
        return default
    return default if r is None or r[0] is None else str(r[0])


def ensure(con):
    con.execute(SCHEMA)
    for k, v, note in SETTINGS:
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    con.commit()


def _off():
    for name in ("ALL_OFF", "OWNER_NOTICE_OFF"):
        p = os.path.join(OFF_DIR, name)
        if os.path.exists(p):
            return p
    return ""


def _is_live(con):
    try:
        for r in con.execute("PRAGMA database_list").fetchall():
            if str(r[1]) == "main":
                return bool(r[2]) and os.path.realpath(str(r[2])) == os.path.realpath(LIVE_DB)
    except sqlite3.Error:
        pass
    return False


def _table(con, name):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None
    except sqlite3.Error:
        return False


def _status(con, now, day=None):
    """The page's own judgement (reports_tile.status) for `day` (default: today); the page's chain reader adds to sys.path -- put it back."""
    path = list(sys.path)
    try:
        import reports_tile                                       # noqa: PLC0415
        return reports_tile.status(con, day or now.date(), now)
    finally:
        sys.path[:] = path


# ------------------------------------------------------------------ what to say (reads only)
def _part_pair(s, since, now):
    pair = [r for r in s.get("rows") or [] if r.get("pair")]
    if len(pair) != 2 or any(r.get("state") != "ok" for r in pair):
        return []
    last = max(norm_ts(r.get("when")) for r in pair)
    if not last or last < since or last > stamp(now):
        return []
    due = s.get("due_day") or ""
    return [dict(key="pair:%s" % due, kind="pair", title="Morning reports ✓",
                 body="Sale %s ✓ · Closing %s ✓ — in by %s" % (ddmm(due), ddmm(due), last[11:16]))]


def _part_valuation(con, s, now, since):
    rows = [r for r in s.get("rows") or [] if r.get("key") == "STOCK_VALUATION"]
    if not rows:
        return []
    r = rows[0]
    last = (now.date().replace(day=1) - dt.timedelta(days=1)).isoformat()
    if r.get("state") == "ok":
        when = norm_ts(r.get("when"))
        if when and when >= since:
            return [dict(key="valuation:%s" % now.strftime("%Y-%m"), kind="valuation", title="Stock Valuation ✓",
                         body="As on %s — in at %s" % (ddmm(last), when[11:16]))]
        return []
    if now.hour * 60 + now.minute < mins(setting(con, "owner_notice.valuation_hhmm"), 1200) or stamp(now)[:10] < since[:10]:
        return []
    why = ""
    if r.get("state") == "refused":
        why = " A file came at %s but was refused%s." % (r.get("at") or "?", (": " + str(r.get("reason"))[:120]) if r.get("reason") else "")
    return [dict(key="valuation_due:%s" % now.date().isoformat(), kind="valuation_due", title="Stock Valuation not in yet",
                 body="As on %s — Shavez to save it from his reports login (until the 7th).%s" % (ddmm(last), why))]


def _part_amir(con, s, now, since):
    if not s.get("amir_day"):
        return []
    rows = {r.get("key"): r for r in s.get("rows") or []}
    it, bw = rows.get("PURCHASE_ITEMWISE") or {}, rows.get("PURCHASE_BILLWISE") or {}
    try:
        import expiry_watch                                       # noqa: PLC0415
        bs = expiry_watch.batch_stock_state(con, now.date()) or {}
    except Exception:                                             # noqa: BLE001
        bs = {"state": "unknown"}
    day = now.date().isoformat()
    ok_it, ok_bw, ok_bs = it.get("state") == "ok", bw.get("state") == "ok", bs.get("state") == "ok"
    if ok_it and ok_bw and ok_bs:
        last = max(norm_ts(it.get("when")), norm_ts(bw.get("when")), "%s %s:00" % (day, bs.get("at") or "00:00"))
        if last < since:
            return []
        body = "Item-wise ✓ · Bill-wise ✓ · Batch Stock ✓ — in by %s" % last[11:16]
        if _table(con, "stock_batch_fix"):
            try:
                done = con.execute("SELECT COUNT(*) FROM stock_batch_fix WHERE status='done' AND substr(COALESCE(done_at,''),1,10)=?",
                                   (day,)).fetchone()[0]
                left = con.execute("SELECT COUNT(*) FROM stock_batch_fix WHERE status IN ('open','receive_only','issue_only')").fetchone()[0]
                if done or left:
                    body += "\nBatch fixes: %d done today, %d left" % (done, left)
            except sqlite3.Error:
                pass
        return [dict(key="amir:%s" % day, kind="amir", title="Amir's work ✓", body=body)]
    if now.hour * 60 + now.minute < mins(setting(con, "owner_notice.amir_missing_hhmm"), 23 * 60 + 40) or day < since[:10]:
        return []
    miss = []
    for name, ok, r in (("purchase item-wise", ok_it, it), ("purchase bill-wise", ok_bw, bw)):
        if not ok:
            miss.append(name + (" (refused)" if r.get("state") == "refused" else ""))
    if not ok_bs:
        miss.append({"wait": "Batch Stock (still being read)", "bad": "Batch Stock (not the whole store — to be saved again)"}
                    .get(bs.get("state"), "Batch Stock"))
    return [dict(key="amir_missing:%s" % day, kind="amir_missing", title="Amir's work — not complete",
                 body="Amir came today; not in: %s." % ", ".join(miss))]


def _part_sheets(con, now, since):
    if not _table(con, "order_sheet"):
        return []
    out = []
    try:
        import order_sheet                                        # noqa: PLC0415
    except Exception:                                             # noqa: BLE001
        return []
    floor = max(since, stamp(now - dt.timedelta(days=2)))
    for sid, taken in con.execute("SELECT id, taken_at FROM order_sheet ORDER BY id DESC LIMIT 20").fetchall():
        t = norm_ts(taken)
        if not t or t < floor or t > stamp(now):
            continue
        try:
            nmed, nsup = order_sheet.day_order(con, sid)
        except Exception:                                         # noqa: BLE001
            nmed, nsup = 0, 0
        out.append(dict(key="sheet:%s" % sid, kind="sheet", title="Darpan's order sheet ✓",
                        body="%s, %s — in at %s" % (plural(nsup, "supplier"), plural(nmed, "medicine"), t[11:16])))
    try:
        rs = order_sheet.refused_sheet(con, staff=False)
    except Exception:                                             # noqa: BLE001
        rs = None
    if rs and floor <= norm_ts(rs.get("at")) <= stamp(now):
        out.append(dict(key="sheet_refused:%s" % norm_ts(rs.get("at")), kind="sheet_refused", title="Darpan's order sheet refused",
                        body="It came at %s and was refused: %s" % (hhmm_of(rs.get("at")), (rs.get("reason") or "no reason given")[:160])))
    return out


def _part_lists(con, now, since):
    try:
        import reports_tile                                       # noqa: PLC0415
    except Exception:                                             # noqa: BLE001
        return []
    out = []
    today = now.date()
    at_min = now.hour * 60 + now.minute
    before = int(setting(con, "owner_notice.lists_days_before") or 2)
    for l in reports_tile.owner_lists(con, today):
        name = LIST_NAMES.get(l["key"], l.get("label") or l["key"])
        if l.get("last") and at_min >= mins(setting(con, "owner_notice.lists_hhmm"), 540) and today.isoformat() >= since[:10]:
            try:
                due = dt.date.fromisoformat(l["last"][:10]) + dt.timedelta(days=int(l["limit"]))
            except (ValueError, TypeError):
                due = None
            if due and today == due - dt.timedelta(days=before):
                out.append(dict(key="list_soon:%s:%s" % (l["key"], due.isoformat()), kind="list_soon", title="Your %s is due soon" % name.lower(),
                                body="%s due %s %s (last as on %s)" % (name, due.strftime("%a"), ddmm(due.isoformat()), ddmm(l["last"]))))
            elif due and today == due:
                out.append(dict(key="list_due:%s:%s" % (l["key"], due.isoformat()), kind="list_due", title="Your %s is due today" % name.lower(),
                                body="%s due today (last as on %s)" % (name, ddmm(l["last"]))))
            elif due and today > due and ((today - due).days % 7 == 0 or today.isoformat() == since[:10]):
                # overdue: said on the install's day and then once a week until it comes (the cold review: an overdue list was never said)
                out.append(dict(key="list_overdue:%s:%s" % (l["key"], today.isoformat()), kind="list_overdue",
                                title="Your %s is overdue" % name.lower(),
                                body="%s was due %s — %d days overdue (last as on %s)" % (name, ddmm(due.isoformat()), (today - due).days,
                                                                                             ddmm(l["last"]))))
        if not _table(con, "mi_file"):
            continue
        rows = con.execute("SELECT md5, verdict, reason, received_at, server_name FROM mi_file WHERE type=? ORDER BY received_at DESC LIMIT 10",
                           (l["key"],)).fetchall()
        for md5, verdict, reason, received, server_name in rows:
            t = norm_ts(received)
            if not t or t < since or t < stamp(now - dt.timedelta(days=2)) or t > stamp(now):
                continue
            if verdict != "VERIFIED":
                out.append(dict(key="list_in:%s" % md5, kind="list_refused", title="%s refused" % name,
                                body="It came at %s and was refused: %s" % (t[11:16], (reason or "no reason given")[:160])))
                continue
            c = reports_tile.certify(md5, server_name, l["key"])
            if c is None:
                if t > stamp(now - dt.timedelta(minutes=30)):
                    continue                                      # being read: the next tick says it
                out.append(dict(key="list_in:%s" % md5, kind="list_in", title="%s received" % name,
                                body="Arrived at %s; the server's check had not run after 30 minutes." % t[11:16]))
            elif c.get("ok"):
                out.append(dict(key="list_in:%s" % md5, kind="list_in", title="%s received ✓" % name,
                                body="Checked by the server%s — in at %s" % ((" — " + c["count"]) if c.get("count") else "", t[11:16])))
            else:
                out.append(dict(key="list_in:%s" % md5, kind="list_bad", title="%s received but failed the check" % name,
                                body="Arrived at %s: %s" % (t[11:16], ", ".join(c.get("failed") or [])[:160] or "see the reports line")))
    return out


def _part_phone(con, now):
    """F-1089: the reception phone silent inside the working window, told once per silence."""
    try:
        import order_sheet                                        # noqa: PLC0415
    except Exception:                                             # noqa: BLE001
        return []
    if not order_sheet.setting(con, "supplier_msg.phone_token", ""):
        return []
    raw = str(order_sheet.setting(con, "supplier_msg.phone_last", "") or "")
    at, _sp, code = raw.partition(" ")
    last = order_sheet._dtm(at)
    if last is None:
        return []
    n = now.replace(tzinfo=None)
    start = mins(setting(con, "owner_notice.phone_from"), 540)
    end = mins(setting(con, "owner_notice.phone_to_sunday" if n.weekday() == 6 else "owner_notice.phone_to"), 1200)
    m = n.hour * 60 + n.minute
    if m < start or m >= end:
        return []
    if code and code != "200" and (n - last) < dt.timedelta(minutes=30):
        # the cold review: a phone that keeps asking and is refused refreshes phone_last every minute -- never "silent"; said once a day
        return [dict(key="phone_refused:%s" % n.date().isoformat(), kind="phone_refused", title="Reception phone refused",
                     body="It is asking the server but is refused (%s) — its setup needs you; WhatsApp orders and payment messages wait." % code)]
    opened = n.replace(hour=start // 60, minute=start % 60, second=0)
    quiet_from = max(last, opened)
    if (n - quiet_from) < dt.timedelta(minutes=int(setting(con, "owner_notice.phone_quiet_min") or 60)):
        return []
    wait = ""
    try:
        import supplier_msg                                       # noqa: PLC0415
        f = supplier_msg.s454_card_facts(con)
        nw = int(f.get("orders_wait") or 0) + int(f.get("pay_wait") or 0)
        if nw:
            wait = " %s wait for it." % plural(nw, "message")
    except Exception:                                             # noqa: BLE001
        pass
    when = "%s %s" % (last.strftime("%d-%m"), last.strftime("%H:%M"))
    if code and code != "200":
        body = "It last asked at %s and was refused (%s) — its setup needs you.%s" % (when, code, wait)
    else:
        body = "Silent since %s — ask reception: phone unlocked, screen on, mobile data on.%s" % (when, wait)
    return [dict(key="phone:%s" % raw.strip(), kind="phone", title="Reception phone silent", body=body)]


def collect(con, now):
    """-> (messages, errors).  Reads only.  Each part is fail-soft: one part's fault never stops the others."""
    since = norm_ts(setting(con, "owner_notice.since")) or "~ (not set: nothing is announced)"
    out, errors = [], []
    s = None
    try:
        s = _status(con, now)
    except Exception as e:                                        # noqa: BLE001
        errors.append("status: %s" % e.__class__.__name__)
    parts = []
    if s is not None:
        parts += [("pair", lambda: _part_pair(s, since, now)), ("valuation", lambda: _part_valuation(con, s, now, since)),
                  ("amir", lambda: _part_amir(con, s, now, since))]
    parts += [("sheets", lambda: _part_sheets(con, now, since)), ("lists", lambda: _part_lists(con, now, since)),
              ("phone", lambda: _part_phone(con, now))]
    if s is not None and now.hour >= 21:                         # an evening export of today's pair is said that evening, not at midnight
        try:
            s2 = _status(con, now, day=now.date() + dt.timedelta(days=1))
            parts.insert(1, ("pair_tonight", lambda: _part_pair(s2, since, now)))
        except Exception as e:                                    # noqa: BLE001
            errors.append("pair_tonight: %s" % e.__class__.__name__)
    for name, fn in parts:
        try:
            out += fn()
        except Exception as e:                                    # noqa: BLE001
            errors.append("%s: %s" % (name, e.__class__.__name__))
        try:
            con.commit()                                          # a module's ensure() may have opened a write; never hold it across parts
        except sqlite3.Error:
            pass
    seen, uniq = set(), []
    for m in out:
        if m["key"] not in seen:
            seen.add(m["key"])
            uniq.append(m)
    return uniq, errors


# ------------------------------------------------------------------ sending
def _payload(key, title, body):
    return dict(kind="owner", title="Sanjeevni · " + title, body=body, url=CONSOLE_URL, tag="owner-" + key, ttl=86400,
                renotify=True, ts=int(dt.datetime.now().timestamp() * 1000))


def deliver(con, key, title, body):
    """-> (sent, how).  Never prints a URL, a key or an endpoint."""
    stub = os.environ.get("OWNER_NOTICE_STUB", "")
    if stub:
        with open(stub, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(key=key, title=title, body=body), ensure_ascii=False) + "\n")
        return True, "stub"
    if os.environ.get("ORDER_PUSH_STUB") or os.environ.get("ORDER_PUSH_NONE"):
        return False, "a walk's push stub is set -- nothing sent"
    if not _is_live(con):
        return False, "not the live database -- nothing sent"
    sent, tried = 0, []
    for u in [x.strip().lower() for x in setting(con, "owner_notice.to").split(",") if x.strip()]:
        try:
            import order_rules                                    # noqa: PLC0415 -- the one Web Push road (portal_push's store and key)
            a, b = order_rules._push(u, _payload(key, title, body))
            sent += int(a or 0)
            tried.append("%s %d/%d" % (u, int(a or 0), int(a or 0) + int(b or 0)))
        except Exception as e:                                    # noqa: BLE001
            tried.append("%s %s" % (u, e.__class__.__name__))
    if sent:
        return True, "clinic app: " + ", ".join(tried)
    ok, how = _ntfy("Sanjeevni: " + title, body, done=("✓" in title))
    return ok, "ntfy (no clinic-app device: %s): %s" % (", ".join(tried) or "no login", how)


def ascii_title(s):
    """An HTTP header carries latin-1 only (the cold review: 'Morning reports ✓' raised UnicodeEncodeError before any connection)."""
    s = str(s).replace("✓", "OK").replace("—", "-").replace("·", "-")
    return s.encode("ascii", "replace").decode("ascii")


def _ntfy(title, body, done=False):
    """The same private ntfy topic the morning alarms use (reports_watch reads NTFY_URL from freshness.conf; never printed)."""
    try:
        import urllib.request                                     # noqa: PLC0415
        import reports_watch                                      # noqa: PLC0415
        url = reports_watch._conf_url()
    except Exception as e:                                        # noqa: BLE001
        return False, "ntfy %s" % e.__class__.__name__
    if not url:
        return False, "NTFY_URL not set -- nothing sent"
    try:
        req = urllib.request.Request(url, data=str(body).encode("utf-8"), method="POST",
                                     headers={"Title": ascii_title(title), "Priority": "default",
                                              "Tags": "white_check_mark" if done else "warning"})
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:                                        # noqa: BLE001
        return False, "ntfy FAILED (%s) -- tried again at the next tick" % e.__class__.__name__
    return True, "ntfy"


LOCK_FILE = os.environ.get("OWNER_NOTICE_LOCK", "/tmp/owner_notice.lock")


def tick(con, now=None):
    """The five-minute pass, one at a time (the cold review: two ticks at once would send twice).  Never raises."""
    try:
        import fcntl                                              # noqa: PLC0415
        lk = open(LOCK_FILE, "a")
        try:
            fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lk.close()
            return {"ok": True, "busy": "another tick holds %s" % LOCK_FILE}
    except Exception as e:                                        # noqa: BLE001
        return {"ok": False, "error": "lock: %s" % e.__class__.__name__}
    try:
        return _tick(con, now)
    finally:
        try:
            lk.close()
        except Exception:                                         # noqa: BLE001
            pass


def _tick(con, now=None):
    try:
        off = _off()
        if off:
            return {"ok": True, "off": os.path.basename(off)}
        ensure(con)
        if setting(con, "owner_notice.on").strip().lower() != "on":
            return {"ok": True, "off": "owner_notice.on"}
        if now is None or now.tzinfo is None:
            now = now_ist()
        msgs, errors = collect(con, now)
        made = 0
        for m in msgs:
            cur = con.execute("INSERT OR IGNORE INTO owner_notice (key, kind, title, body, made_at) VALUES (?,?,?,?,?)",
                              (m["key"], m["kind"], m["title"], m["body"], stamp(now)))
            made += cur.rowcount or 0
        con.commit()
        floor = stamp(now - dt.timedelta(days=1))
        con.execute("UPDATE owner_notice SET how=? WHERE sent_at IS NULL AND (made_at < ? OR tries >= ?) AND COALESCE(how,'') NOT LIKE 'given up%'",
                    ("given up (older than a day, or %d tries)" % MAX_TRIES, floor, MAX_TRIES))
        con.commit()
        unsent = con.execute("SELECT id, key, title, body FROM owner_notice WHERE sent_at IS NULL AND made_at >= ? AND tries < ? "
                             "AND COALESCE(how,'') NOT LIKE 'given up%' ORDER BY id", (floor, MAX_TRIES)).fetchall()
        sent = 0
        hows = []
        for rid, key, title, body in unsent:
            ok, how = deliver(con, key, title, body)
            con.execute("UPDATE owner_notice SET tries=tries+1, how=?, sent_at=? WHERE id=?",
                        (how[:300], stamp(now_ist()) if ok else None, rid))
            con.commit()
            sent += 1 if ok else 0
            hows.append(how[:80])
        return {"ok": True, "made": made, "sent": sent, "unsent": len(unsent) - sent, "errors": errors, "how": hows[:3]}
    except Exception as e:                                        # noqa: BLE001
        return {"ok": False, "error": ("%s: %s" % (e.__class__.__name__, e))[:160]}


def test(con):
    """The install's proof of the road: one message, said as a test."""
    ensure(con)
    now = now_ist()
    key = "test:%s" % stamp(now)
    title = "Messages are on ✓"
    body = ("This is the install's test (%s). From now you are told when Shavez's morning reports, Amir's exports and Darpan's order sheet "
            "are in, and about your three lists." % now.strftime("%d-%m %H:%M"))
    ok, how = deliver(con, key, title, body)
    con.execute("INSERT OR IGNORE INTO owner_notice (key, kind, title, body, made_at, sent_at, how, tries) VALUES (?,?,?,?,?,?,?,1)",
                (key, "test", title, body, stamp(now), stamp(now) if ok else None, how[:300]))
    con.commit()
    return ok, how


# ------------------------------------------------------------------ the command line
def _connect(db, ro=False):
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30) if ro else sqlite3.connect(db, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else ""
    db = os.environ.get("FINANCE_DB", LIVE_DB)
    if "--db" in argv:
        db = argv[argv.index("--db") + 1]
    now = None
    if "--now" in argv:
        now = dt.datetime.fromisoformat(argv[argv.index("--now") + 1]).replace(tzinfo=IST)
    if cmd == "tick":
        con = _connect(db)
        r = tick(con, now)
        print("%s owner_notice %s tick %s" % (stamp(now_ist()), KIT, json.dumps(r, ensure_ascii=False)))
        return 0 if r.get("ok") else 1
    if cmd == "test":
        con = _connect(db)
        ok, how = test(con)
        print("owner_notice test: %s -- %s" % ("SENT" if ok else "NOT SENT", how))
        return 0 if ok else 1
    if cmd == "collect":
        con = _connect(db, ro=True)
        msgs, errors = collect(con, now or now_ist())
        for m in msgs:
            print("%-40s %s | %s" % (m["key"][:40], m["title"], m["body"].replace("\n", " / ")))
        print("collect: %d message(s); errors: %s" % (len(msgs), "; ".join(errors) or "none"))
        return 0
    if cmd == "show":
        con = _connect(db)
        ensure(con)
        for r in con.execute("SELECT made_at, key, sent_at, how FROM owner_notice ORDER BY id DESC LIMIT 15").fetchall():
            print("%s  %-36s  %s  %s" % (r[0], r[1][:36], r[2] or "(not sent)", (r[3] or "")[:70]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
