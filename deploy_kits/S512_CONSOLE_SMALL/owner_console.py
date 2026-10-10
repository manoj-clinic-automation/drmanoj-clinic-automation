#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owner_console.py -- S481_COMMAND_CONSOLE (parent; session 294, 05-Oct-2026). The owner's word of that morning: "a small
informative tile at top of my pwa, clickable and expandable ... who and when the exports and entries were done for the day,
what all is pending where ... the daily revenues ... anything I need to review, approve ... all collapsible, expandable
sections, down to granular details, across sanjeevni, docterz, attendance, scanapp ... this tile should lead to my command
console type of page".

ONE READING LAYER over what the estate already computes. It makes no figure of its own: every line is the answer of the
module that owns it (clinic_money.match_day, sanjeevni_cash.days, darpan_kal, packs, slip_adjust, slip_log, records,
sanjeevni_approvals.needs_you, att_core.compute_day), the duty map's own due_sql (DUTY_MAP.json, D648), or one plain
SELECT on the owner's table.

HOW IT CANNOT WRITE. Several of those readers write (they create tables, keep counters, refresh a cached figure), so none
of them is ever called on the live connection. The page asks for a reading; a SEPARATE SHORT PROCESS
(owner_console.py --build) copies finance.db with SQLite's own backup into a private temp folder, points FINANCE_DB at the
copy BEFORE it imports any module of the app, calls the owners on the copy, writes ONE json file and deletes the copy.
The service only ever reads that file. The asset app's and the staff register's databases are opened read-only.

NO PATIENT IN THE READING. Where an owner's answer carries a patient's name, clinic ID, phone or a bank reference (the
slip match, the bank pairs, a flag's sentence), only its count, code and amount are taken.

Doors (the owner only -- checker of unit 'packs'):
  GET /finance/console              the page (owner_console.html beside this file)
  GET /finance/console/api/state    the last reading, and whether a new one is being made (?refresh=1 asks for one)
  GET /finance/console/api/tile     the figures of the Today tile on the Clinic app's home
A reading older than five minutes is replaced in the background when either door is asked; there is no timer job.

1.1 (S487_AAJ_KA_KAAM, 05-Oct-2026, D679): the staff's lines and the owner's own lines are now cut from the SAME list the
staff see (aaj_kaam.build_all on the copy): the duty map by its own due_sql with NOTHING BEFORE THE FLOOR (01-Sep-2026)
counted, the parent's extra lines, and the taps with who and when. What the floor hides from the owner's own lines is
said in one grey line. Each queue's head line opens that person's list as they see it. Without aaj_kaam.py (or with a
fault in it) the reading falls back to 1.0's own reading of the map. Three wording slips seen live on 05-Oct are mended
('no punch yet' late in the day, '0 min late').
"""
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

VERSION = "S512 1.2"
# S512 (10-Oct-2026, the owner's list item 8 -- the console's small kit): F-779 the work section follows HIS PANEL -- each person's
# list exactly as they see it (his switches, his own lines, the green 'done' rows) and their tasks with the answers; F-774 the
# System line says how old the freshness reading is and never calls feeds fresh on a reading older than a day; F-795 the flag
# codes in words (pos_diff, mpr_missing, mpr_rejected).
FIN = os.path.dirname(os.path.abspath(__file__))


def _env(name, default):
    return os.environ.get(name) or default


# the reading is NOT named *.json: the nightly code bundle takes every /root/finance/*.json to Drive, and a reading holds
# the day's revenue and the staff's punches. *.dat, *.lock, *.err and *.log are in none of the bundle's lists.
SNAP = _env("CONSOLE_SNAPSHOT", os.path.join(FIN, "console_reading.dat"))
LOCK = SNAP + ".lock"
ERRF = SNAP + ".err"
LOG = _env("CONSOLE_BUILD_LOG", os.path.join(FIN, "console_build.log"))
PAGE = os.path.join(FIN, "owner_console.html")
ATT_DIR = _env("CONSOLE_ATT_DIR", "/root")
ASSETS_DB = _env("CONSOLE_ASSETS_DB", "/root/assetapp/assets.db")
REGISTER_DB = _env("CONSOLE_REGISTER_DB", "/root/staff_register/staff_register.db")
DUTY_MAP = _env("DUTY_MAP_JSON", "/root/deploy/repo/claude_code_briefs/DUTY_MAP.json")
FRESH = _env("CONSOLE_FRESHNESS", os.path.join(FIN, "freshness.json"))
BEAT = _env("CONSOLE_BEAT", os.path.join(FIN, "reception_heartbeat.json"))
MAX_AGE = 300            # seconds: a reading older than this is replaced when the page or the tile asks
LOCK_STALE = 150         # seconds: a lock older than this belongs to a build that was killed outright
BUILD_LIMIT = 120        # seconds: the builder stops itself, says so, and cleans up
FAIL_WAIT = 60           # seconds: after a build that FAILED, no new one is started (a fault never becomes a loop)

# ============================================================================================ the service's part
_db = None
_require = None
_unit = "packs"
_CHILDREN = []

DENIED = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
          "<title>Command console</title><body style='font-family:system-ui;margin:40px 20px;color:#1d211f'>"
          "<h2>This page is the owner's.</h2><p>Your login does not open it.</p><p><a href='/portal'>Back to the Clinic app</a></p>")


def _read_snapshot():
    try:
        with open(SNAP, encoding="utf-8") as fh:
            s = json.load(fh)
        return s, max(0, int(time.time() - float(s.get("built_epoch") or 0)))
    except Exception:                                                  # noqa: BLE001 -- no reading yet, or half a file
        return None, None


def _label(s):
    """'as of 16:20' for a reading of today, 'as of 04-Oct 21:40' for an older one -- the owner must never take
    yesterday's reading for today's."""
    if not s:
        return ""
    d = str(s.get("as_of") or "")[:10]
    if d == dt.date.today().isoformat():
        return "as of %s" % (s.get("as_of_hm") or "")
    return "as of %s %s" % (dm(d), s.get("as_of_hm") or "")


def _building():
    try:
        return (time.time() - os.stat(LOCK).st_mtime) < LOCK_STALE
    except OSError:
        return False


def _reap():
    for p in list(_CHILDREN):
        if p.poll() is not None:
            _CHILDREN.remove(p)


def _note_err(kind, text):
    """One line beside the reading: '<epoch>|<failed or stopped>|<HH:MM -- words>'. Best effort; never raises."""
    try:
        part = "%s.part%d" % (ERRF, os.getpid())
        with open(part, "w", encoding="utf-8") as fh:
            fh.write("%d|%s|%s -- %s" % (int(time.time()), kind, time.strftime("%H:%M"), str(text)[:200]))
        os.chmod(part, 0o600)
        os.replace(part, ERRF)
    except OSError:
        pass


def _read_err():
    """(kind, words, age in seconds) of the note beside the reading, or (None, None, None)."""
    try:
        with open(ERRF, encoding="utf-8") as fh:
            raw = fh.read(400)
        t, kind, words = raw.split("|", 2)
        return kind, words, max(0, int(time.time()) - int(t))
    except (OSError, ValueError):
        return None, None, None


def _kick(db_path):
    """Start ONE builder, detached. True when one is running after the call."""
    _reap()
    try:
        if (time.time() - os.stat(LOCK).st_mtime) < LOCK_STALE:
            return True
        # a stale lock: that build was killed before it could clean up. Exactly ONE asker takes it over -- a rename
        # succeeds for one caller only -- and the page is told what happened until the next reading is whole.
        dead = "%s.dead%d" % (LOCK, os.getpid())
        os.rename(LOCK, dead)
        os.unlink(dead)
        _note_err("stopped", "the reading before this one was stopped before it finished")
    except OSError:
        pass                                                           # no lock, or the other asker took the stale one
    kind, _words, age = _read_err()
    if kind == "failed" and age is not None and age < FAIL_WAIT:
        return False                                                   # it failed a moment ago: the page says so; no loop
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return True                                                    # the other worker took it this instant
    except OSError:
        return False                                                   # the folder cannot be written (a full disk)
    try:
        try:
            os.write(fd, ("%d %s" % (os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S"))).encode("ascii"))
        except OSError:
            pass
    finally:
        os.close(fd)
    try:
        log = open(LOG, "wb")
        try:
            os.chmod(LOG, 0o600)
            p = subprocess.Popen([sys.executable or "/usr/bin/python3", "-B", os.path.abspath(__file__), "--build",
                                  "--db", db_path, "--out", SNAP, "--lock", LOCK],
                                 cwd=FIN, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True, close_fds=True)
        finally:
            log.close()
        _CHILDREN.append(p)
        return True
    except Exception:                                                  # noqa: BLE001
        try:
            os.unlink(LOCK)
        except OSError:
            pass
        return False


def init(app, db_getter, require_fn, unit="packs"):
    global _db, _require, _unit
    from flask import Blueprint, Response, jsonify, request            # noqa: PLC0415
    _db, _require, _unit = db_getter, require_fn, unit
    bp = Blueprint("owner_console", __name__)

    def _gate():
        return _require("checker", unit=_unit)

    def _db_path():
        try:
            for r in _db().execute("PRAGMA database_list").fetchall():
                if r[1] == "main":
                    return r[2] or ""
        except Exception:                                              # noqa: BLE001 -- no path: no builder, the older reading stands
            pass
        return ""

    def _state(force):
        snap, age = _read_snapshot()
        stale = snap is None or age is None or age > MAX_AGE
        building = _building()
        if not building and (stale or (force and (age is None or age > 15))):
            p = _db_path()
            building = bool(p) and _kick(p)
        _kind, berr, _age = _read_err()
        return snap, age, stale, building, berr

    @bp.route("/finance/console")
    def console_page():
        _u, err = _gate()
        if err:
            return Response(DENIED, status=403, mimetype="text/html")
        try:
            with open(PAGE, encoding="utf-8") as fh:
                html = fh.read()
        except OSError as e:
            return Response("The console's page file could not be read (%s)." % e, status=500, mimetype="text/plain")
        r = Response(html, mimetype="text/html")
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/console/api/state")
    def console_state():
        _u, err = _gate()
        if err:
            return err
        snap, age, stale, building, berr = _state(request.args.get("refresh") == "1")
        r = jsonify(ok=True, snapshot=snap, age_s=age, stale=stale, building=building, build_error=berr,
                    as_of_label=_label(snap), max_age_s=MAX_AGE, version=VERSION)
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/console/api/tile")
    def console_tile():
        _u, err = _gate()
        if err:
            return err
        snap, age, stale, building, _berr = _state(False)
        s = snap or {}
        r = jsonify(ok=True, tile=s.get("tile"), as_of_label=_label(snap), as_of=s.get("as_of"), day_words=s.get("day_words"),
                    age_s=age, stale=stale, building=building)
        r.headers["Cache-Control"] = "no-store"
        return r

    app.register_blueprint(bp)


# ============================================================================================ the builder's part
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
DOW = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def inr(p):
    """paise -> '₹1,62,880' (Indian grouping; the paise are shown only when there are any)."""
    if p is None:
        return "–"
    p = int(p)
    neg, p = p < 0, abs(p)
    r, ps = divmod(p, 100)
    s = str(r)
    if len(s) > 3:
        head, tail, parts = s[:-3], s[-3:], []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("\u2212\u2060" if neg else "") + "₹" + s + ((".%02d" % ps) if ps else "")       # a minus that never leaves its amount


def _iso(d):
    return d if isinstance(d, str) else d.isoformat()


def dmy(iso):
    """'2026-10-03...' -> 'Sat 03-Oct'."""
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return "%s %02d\u2011%s" % (DOW[d.weekday()], d.day, MON[d.month - 1])        # a hyphen that never breaks a line
    except Exception:                                                  # noqa: BLE001
        return str(iso or "")[:10]


def hm(ts):
    m = re.search(r"[T ](\d{2}:\d{2})", str(ts or ""))
    return m.group(1) if m else ""


def when(ts, today):
    """A stamp as the owner reads it: '21:41' today, '03-Oct 21:41' otherwise."""
    s = str(ts or "")
    if not s:
        return ""
    if s[:10] == today:
        return hm(s) or "today"
    try:
        d = dt.date.fromisoformat(s[:10])
        return ("%02d\u2011%s %s" % (d.day, MON[d.month - 1], hm(s))).strip()
    except Exception:                                                  # noqa: BLE001
        return s[:16]


def days_since(since):
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(since)[:10])).days
    except Exception:                                                  # noqa: BLE001
        return None


def tidy(text):
    """Typography only, never a figure: the estate's lines are written for a log (' -- ', 'day(s)', a setting's name in
    brackets); the owner reads them on a phone. '3 day(s)' -> '3 days', '1 day(s)' -> '1 day', ' -- ' -> ' — '."""
    t = str(text)
    t = re.sub(r"\s*\((?:after )?[a-z_]+\.[a-z_]+\)", "", t)                      # '(after purchase.scan_wait_days)'
    t = re.sub(r"(\d+)(\s+(?:[A-Za-z']+\s+){0,3}?[A-Za-z]+)\(s\)", lambda m: m.group(1) + m.group(2) + ("" if m.group(1) == "1" else "s"), t)
    t = t.replace("(s)", "s")
    t = re.sub(r"\b(\d{1,2})-([A-Z][a-z]{2}|\d{1,2})(?:-(\d{2,4}))?\b",                # a date never breaks across two lines
               lambda m: m.group(1) + "\u2011" + m.group(2) + (("\u2011" + m.group(3)) if m.group(3) else ""), t)
    return t.replace(" -- ", " — ").replace("X-ray", "X\u2011ray")


def L(dot, text, b=None, who=None, href=None, link=None, table=None, tlabel=None, sub=False, fill=None, why=None):
    d = dict(dot=dot, text=tidy(text))
    if table:
        table = dict(head=list(table.get("head") or []), rows=[[tidy(c) for c in r] for r in (table.get("rows") or [])])
    for k, v in (("b", b), ("who", tidy(who) if who else None), ("href", href), ("link", link), ("table", table), ("tlabel", tlabel),
                 ("fill", fill), ("why", why)):
        if v:
            d[k] = v
    if sub:
        d["sub"] = True
    return d


def unread(what, e):
    """One grey line in plain words; the technical reason travels in 'why' (kept in the reading, not drawn on the page)."""
    return L("n", "%s could not be read just now." % what, why="%s: %s" % (type(e).__name__, str(e)[:160]))


def piece(lines, what, fn):
    """One piece of a section: its lines, or one grey line saying it could not be read. A piece never takes its section down."""
    try:
        got = fn()
        if got:
            lines.extend(got if isinstance(got, list) else [got])
    except Exception as e:                                             # noqa: BLE001
        lines.append(unread(what, e))


def nlen(v):
    if isinstance(v, (list, tuple, dict, set)):
        return len(v)
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


FLAG_WORDS = {"not_filled": "the counter sheet is not filled", "total_diff": "the counter sheet and Docterz differ",
              "bank_extra": "money reached the bank with no Docterz entry", "no_docterz": "no Docterz export for the day",
              "not_in_bank": "a Docterz online payment has not reached the bank",
              "pos_diff": "the POS machine's UPI total differs from the bank's",                     # S512 (F-795)
              "mpr_missing": "the bank's daily statement (MPR) has not come",
              "mpr_rejected": "the bank's daily statement (MPR) could not be read"}
HEAD_WORDS = {"consult": "Consultation", "xray": "X-ray", "proc": "Procedures + dressing", "cash": "Cash", "upi": "UPI",
              "card": "Card"}
STATUS_WORDS = {"submitted": "filed, to approve", "draft": "draft, to approve", "approved": "approved", "locked": "locked",
                "closed_holiday": "closed (holiday)"}
TARGET_DOOR = {"days": "/finance/approvals", "returns": "/finance/approvals", "bank": "/finance/approvals",
               "porders": "/finance/porders", "stock": "/finance/stock/page/hub", "checks-kal": "/finance/darpan/kal",
               "checks-marg": "/finance/approvals"}


def flag_word(code, amount_p):
    w = FLAG_WORDS.get(code) or str(code or "flag").replace("_", " ")
    return w + ((" (%s)" % inr(amount_p)) if amount_p else "")


# ------------------------------------------------------------------------------------------- the duty map (D648)
def read_duties(copy_path):
    """Every duty of DUTY_MAP.json with its own due_sql run on the copy, read-only -- the same guard amir_day keeps
    (one SELECT/WITH, no ';'). late = due for allowed_days or more (or since unknown), exactly as amir_day raises it."""
    with open(DUTY_MAP, encoding="utf-8") as fh:
        m = json.load(fh)
    out = []
    ro = sqlite3.connect("file:%s?mode=ro" % copy_path, uri=True, timeout=5)
    try:
        for du in list(m.get("duties") or []):
            sql = str(du.get("due_sql") or "").strip().rstrip(";").strip()
            row = dict(id=du.get("id"), person=du.get("person"), duty=str(du.get("duty") or du.get("id") or ""),
                       tile=du.get("tile"), door=du.get("door"), n=0, since=None, days=None, late=False, err=None,
                       owner_line=du.get("owner_line"), who=str((m.get("people") or {}).get(du.get("person"), du.get("person") or "")))
            try:
                row["allowed"] = int(du.get("allowed_days") or 0)
            except (TypeError, ValueError):
                row["allowed"] = 0
            if not sql or not re.match(r"(?is)^(select|with)\b", sql) or ";" in sql:
                row["err"] = "no readable due_sql"
            else:
                try:
                    r = ro.execute(sql).fetchone()
                    row["n"] = int((r[0] if r else 0) or 0)
                    row["since"] = r[1] if (r is not None and len(r) > 1) else None
                except Exception as e:                                 # noqa: BLE001
                    row["err"] = str(e)[:90]
            if row["n"] > 0:
                row["days"] = days_since(row["since"]) if row["since"] else None
                row["late"] = row["days"] is None or row["days"] >= row["allowed"]
            out.append(row)
    finally:
        ro.close()
    return dict(version=m.get("version"), people=m.get("people") or {}, shared=m.get("shared") or {}, duties=out)


def dm(iso):
    """'2026-10-03...' -> '03-Oct'."""
    return dmy(iso)[4:] if re.match(r"\d{4}-\d{2}-\d{2}", str(iso or "")) else str(iso or "")[:10]


def duty_line(d, sub=True):
    """One due duty in the duty map's OWN owner's words (its owner_line, filled as amir_day fills it); where the map
    gives a duty no such line, the duty's own description with the count in front."""
    if d["err"]:
        return L("n", "Not read just now: %s" % d["duty"], sub=sub, why=d["err"])
    dot, link = ("b" if d["late"] else "w"), (d["tile"] or "open")
    if d.get("owner_line"):
        try:
            text = str(d["owner_line"]).format(n=d["n"], days=(d["days"] if d["days"] is not None else "?"),
                                               since=dm(d["since"]) if d["since"] else "-", person=d.get("who") or "")
            return L(dot, text, href=d["door"], link=link, sub=sub)
        except Exception:                                              # noqa: BLE001 -- a line the map cannot fill: its description
            pass
    tail = ""
    if d["since"]:
        tail = " · since %s" % dm(d["since"])
        if d["days"] is not None and d["days"] > 0:
            tail += " (%d day%s)" % (d["days"], "" if d["days"] == 1 else "s")
    return L(dot, d["duty"] + tail, b=str(d["n"]), href=d["door"], link=link, sub=sub)


# ------------------------------------------------------------------------------------------- attendance
def read_attendance(now):
    """att_core.compute_day for today (the attendance system's own engine and files, read only), and each person's USUAL
    first punch -- the median of the last 30 days that have one."""
    if ATT_DIR not in sys.path:
        sys.path.append(ATT_DIR)                                       # appended: the finance app's own modules win
    import att_core                                                    # noqa: PLC0415
    staff = att_core.load_staff()
    punches = att_core.load_punches()
    day = att_core.compute_day(now.date(), staff, punches)
    first = {}
    lo = now.date() - dt.timedelta(days=30)
    for uid, t in punches:
        d = t.date()
        if lo <= d < now.date():
            k = (uid, d)
            if k not in first or t < first[k]:
                first[k] = t
    mins = {}
    for (uid, _d), t in first.items():
        mins.setdefault(uid, []).append(t.hour * 60 + t.minute)
    usual = {}
    for uid, v in mins.items():
        if len(v) >= 3:
            v.sort()
            m = v[len(v) // 2]
            usual[uid] = (m, "%02d:%02d" % divmod(m, 60))
    return dict(day=day, usual=usual, staff=staff)


def punch_by_login(att, logins, now=None):
    """login -> that person's line of today, ONLY where exactly one active staff name carries the login as a word."""
    out = {}
    if not att:
        return out
    day, usual = att["day"], att["usual"]
    nowm = (now.hour * 60 + now.minute) if now is not None else None
    rows = [(r, True) for r in day["present"]] + [(r, False) for r in day["absent"]]
    for lg in logins:
        hit = [(r, here) for r, here in rows if lg.lower() in re.findall(r"[a-z]+", str(r.get("name") or "").lower())]
        if len(hit) != 1:
            continue
        r, here = hit[0]
        if here:
            out[lg] = "in %s" % r["first"].strftime("%H:%M") + ((" · %d min late" % r["late_min"]) if (r.get("late") and r.get("late_min")) else "")
        else:
            u = usual.get(r["uid"])
            past = bool(u and nowm is not None and nowm > u[0] + 30)       # well past the usual hour: 'today', not 'yet'
            out[lg] = ("no punch today" if past else "no punch yet") + ((" (usual %s)" % u[1]) if u else "")
    return out


# ------------------------------------------------------------------------------------------- the sections
def _sec_needs_map(con, cx):
    lines = []
    duties = cx.get("duties")
    if duties:
        allmine = [d for d in duties["duties"] if d["person"] == "manoj"]
        mine = [d for d in allmine if d["n"] > 0]
        mine.sort(key=lambda d: (0 if d["late"] else 1, -(d["days"] or 0)))
        for d in mine:
            ln = duty_line(d, sub=False)
            first = str(d.get("tile") or "").split(" ")[0].lower()
            if first and not d["err"] and not ln.get("b") and not ln["text"].lower().startswith(first):
                ln["b"], ln["text"] = "%s:" % d["tile"], " " + ln["text"]          # whose page the line belongs to
            try:
                if d["id"] == "manoj.slip_adjust":
                    import slip_adjust                                 # noqa: PLC0415
                    pend = slip_adjust.pending(con)
                    amt = any(a.get("amount_p") for a in pend)
                    rows = [[str(a.get("kind") or ""), "%s %s" % (str(a.get("series") or "").upper(), a.get("slip_no") or "")]
                            + ([inr(a.get("amount_p")) if a.get("amount_p") else "–"] if amt else [])
                            + [str(a.get("made_by") or ""), when(a.get("made_at"), cx["today"])] for a in pend]
                    if rows:
                        ln["table"] = dict(head=["Kind", "Slip"] + (["Amount"] if amt else []) + ["By", "When"], rows=rows[:40])
                        ln["tlabel"] = "see the %d" % len(rows)
                elif d["id"] == "manoj.clinic_flags":
                    import clinic_money                                # noqa: PLC0415
                    rows = [[dmy(q["business_date"]), flag_word(q["code"], q["amount_p"])]
                            for q in (dict(x) for x in clinic_money.owner_queue(con))]
                    if rows:
                        ln["table"] = dict(head=["Day", "What"], rows=rows[:40])
                        ln["tlabel"] = "see the %d" % len(rows)
                elif d["id"] == "manoj.cash_received":
                    rows = [[dmy(r[0]), inr(r[1]), str(r[2] or "").replace("dr_", "Dr ").title()] for r in con.execute(
                        "SELECT business_date, handed_p, handed_to FROM darpan_kal_day WHERE unit='medical' AND handed_p IS NOT NULL "
                        "AND received_at IS NULL ORDER BY business_date DESC LIMIT 40")]
                    if rows:
                        ln["table"] = dict(head=["Day", "Cash", "Handed to"], rows=rows)
                        ln["tlabel"] = "see the %d" % len(rows)
                elif d["id"] == "manoj.approve_days":
                    days = [dmy(r[0]) for r in con.execute(
                        "SELECT business_date FROM day_entry WHERE unit='medical' AND status IN ('submitted','draft') "
                        "ORDER BY business_date LIMIT 40")]
                    if days:
                        ln["who"] = ", ".join(days)
            except Exception:                                          # noqa: BLE001 -- the line stands without its detail
                pass
            lines.append(ln)
        n = len(mine)
        late = sum(1 for d in mine if d["late"])
        if not lines:
            lines.append(L("g", "Nothing is waiting for you."))
        errs = [d for d in allmine if d["err"]]
        if errs:
            lines.append(L("n", "%d of your own lines could not be checked just now." % len(errs),
                           why="; ".join("%s: %s" % (d["id"], d["err"]) for d in errs)[:400]))
    else:
        # the duty map could not be read: the approvals page's own lines, so the section is never silently empty
        lines.append(L("n", "The duty map could not be read just now; these are the approvals page's own lines instead.",
                       why=cx.get("duties_err") or "no map"))
        nn = [x for x in (cx.get("needs_you") or {}).get("lines") or [] if x.get("cls") in ("bad", "warn")]
        for x in nn:
            lines.append(L("b" if x.get("cls") == "bad" else "w", x.get("text") or "", href=TARGET_DOOR.get(x.get("target"), "/finance/approvals"),
                           link="open"))
        n, late = len(nn), sum(1 for x in nn if x.get("cls") == "bad")
    cx["tile"]["needs_n"] = n
    cx["tile"]["needs_late"] = late
    return dict(ok=True, name="Needs you", chip=str(n), cls=("b" if late else ("w" if n else "g")),
                word=("%d late" % late) if late else ("waiting" if n else "all clear"), open=bool(n), lines=lines)


def _needs_detail(con, cx, did, ln, aaj):
    """The rows behind one of the owner's lines -- never older than the floor the count itself stands on."""
    fl = aaj.get("floor") or "0000-00-00"
    if did == "manoj.slip_adjust":
        import slip_adjust                                             # noqa: PLC0415
        pend = slip_adjust.pending(con)
        amt = any(a.get("amount_p") for a in pend)
        rows = [[str(a.get("kind") or ""), "%s %s" % (str(a.get("series") or "").upper(), a.get("slip_no") or "")]
                + ([inr(a.get("amount_p")) if a.get("amount_p") else "–"] if amt else [])
                + [str(a.get("made_by") or ""), when(a.get("made_at"), cx["today"])] for a in pend]
        if rows:
            ln["table"] = dict(head=["Kind", "Slip"] + (["Amount"] if amt else []) + ["By", "When"], rows=[[tidy(c) for c in r] for r in rows[:40]])
            ln["tlabel"] = "see the %d" % len(rows)
    elif did == "manoj.clinic_flags":
        import clinic_money                                            # noqa: PLC0415
        f2 = (aaj.get("views") or {}).get("clinic_money_flag") or fl
        rows = [[dmy(q["business_date"]), flag_word(q["code"], q["amount_p"])]
                for q in (dict(x) for x in clinic_money.owner_queue(con)) if str(q["business_date"]) >= f2]
        if rows:
            ln["table"] = dict(head=["Day", "What"], rows=[[tidy(c) for c in r] for r in rows[:40]])
            ln["tlabel"] = "see the %d" % len(rows)
    elif did == "manoj.cash_received":
        rows = [[dmy(r[0]), inr(r[1]), str(r[2] or "").replace("dr_", "Dr ").title()] for r in con.execute(
            "SELECT business_date, handed_p, handed_to FROM darpan_kal_day WHERE unit='medical' AND handed_p IS NOT NULL "
            "AND received_at IS NULL ORDER BY business_date DESC LIMIT 40")]
        if rows:
            ln["table"] = dict(head=["Day", "Cash", "Handed to"], rows=[[tidy(c) for c in r] for r in rows])
            ln["tlabel"] = "see the %d" % len(rows)
    elif did == "manoj.approve_days":
        f2 = (aaj.get("views") or {}).get("day_entry") or fl
        days = [dmy(r[0]) for r in con.execute(
            "SELECT business_date FROM day_entry WHERE unit='medical' AND status IN ('submitted','draft') AND business_date >= ? "
            "ORDER BY business_date LIMIT 40", (f2,))]
        if days:
            ln["who"] = tidy(", ".join(days))


def sec_needs(con, cx):
    """1.1: the owner's own lines, cut from the same engine as the staff's lists (the floor laid under the map's SQL)."""
    aaj = cx.get("aaj")
    if not aaj:
        return _sec_needs_map(con, cx)
    lines = []
    allmine = [i for i in aaj["items"] if i["person"] == "manoj" and i["kind"] == "sql"]
    mine = sorted([i for i in allmine if i["n"] > 0 and not i["err"]], key=lambda i: (0 if i["late"] else 1, -(i["days"] or 0)))
    for i in mine:
        ln = L("b" if i["late"] else "w", i["en"], href=i["door"], link=i["tile"] or "open")
        first = str(i.get("tile") or "").split(" ")[0].lower()
        if first and not ln["text"].lower().startswith(first):
            ln["b"], ln["text"] = "%s:" % i["tile"], " " + ln["text"]              # whose page the line belongs to
        try:
            _needs_detail(con, cx, i["id"], ln, aaj)
        except Exception:                                              # noqa: BLE001 -- the line stands without its detail
            pass
        lines.append(ln)
    n, late = len(mine), sum(1 for i in mine if i["late"])
    if not lines:
        lines.append(L("g", "Nothing is waiting for you."))
    hidden = sum(max(0, int(i["n_all"]) - int(i["n"])) for i in allmine if not i["err"])
    if hidden:
        lines.append(L("n", "%d older item%s from before %s %s not shown here; %s own page still holds %s."
                       % (hidden, "" if hidden == 1 else "s", dm(aaj.get("floor")), "is" if hidden == 1 else "are",
                          "its" if hidden == 1 else "their", "it" if hidden == 1 else "them"),
                       why="; ".join("%s: %d of %d" % (i["id"], i["n"], i["n_all"]) for i in allmine if i["n_all"] > i["n"])[:300]))
    errs = [i for i in allmine if i["err"]]
    if errs:
        lines.append(L("n", "%d of your own lines could not be checked just now." % len(errs),
                       why="; ".join("%s: %s" % (i["id"], i["err"]) for i in errs)[:400]))
    cx["tile"]["needs_n"] = n
    cx["tile"]["needs_late"] = late
    return dict(ok=True, name="Needs you", chip=str(n), cls=("b" if late else ("w" if n else "g")),
                word=("%d late" % late) if late else ("waiting" if n else "all clear"), open=bool(n), lines=lines)


def sec_money(con, cx):
    import bank_mpr_status as BM                                       # noqa: PLC0415
    import clinic_money as CM                                          # noqa: PLC0415
    import clinic_register as CR                                       # noqa: PLC0415
    import darpan_kal as DK                                            # noqa: PLC0415
    import packs as PK                                                 # noqa: PLC0415
    import sanjeevni_cash as SC                                        # noqa: PLC0415
    D, S, today, T = cx["clinic_day"], cx["sanj_day"], cx["today"], cx["tile"]
    lines = []
    state = {"flags": 0, "bad": False}

    def clinic():
        m = CM.match_day(con, D)
        p1 = m.get("p1") or {}
        v = m.get("verdict")
        flags = m.get("flags") or []
        amt = int(p1.get("docterz_p") or 0) if m.get("doc_known") else (int(p1.get("counter_p") or 0) if m.get("filled") else None)
        word, dot = {"nothing_to_do": ("matched", "g"), "flags": ("%d flag%s" % (len(flags), "" if len(flags) == 1 else "s"), "w"),
                     "not_filled": ("counter sheet not filled", "b"), "waiting_docterz": ("waiting for the Docterz export", "w")
                     }.get(v, (str(v or "not read").replace("_", " "), "n"))
        state["flags"] += len(flags)
        state["bad"] = state["bad"] or dot == "b"
        who = []
        reg = CR.register_row(con, D)
        who.append(("counter sheet by %s %s" % (reg["entered_by"], when(reg["entered_at"], today))) if reg else "counter sheet not filled")
        ex = con.execute("SELECT rows, taken_at FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' "
                         "ORDER BY id DESC LIMIT 1", (D,)).fetchone()
        who.append(("Docterz export %s (%d rows)" % (when(ex["taken_at"], today), int(ex["rows"] or 0))) if ex else "no Docterz export yet")
        try:
            bs = BM.mpr_state(con, D, unit="clinic")
            if bs.get("state") == "applied":
                who.append("bank UPI %s in%s" % (inr(bs.get("total_p")), (" " + when(bs.get("applied_at"), today)) if bs.get("applied_at") else ""))
            else:
                who.append("bank file: %s" % str(bs.get("state") or "not known").replace("_", " "))
        except Exception:                                              # noqa: BLE001
            pass
        rows = []
        for k, ctr, doc, diff in list(m.get("p2") or []) + list(m.get("p3") or []):
            rows.append([HEAD_WORDS.get(k, str(k)), inr(ctr), inr(doc), inr(diff) if diff else "–"])
        if p1:
            rows.append(["Total", inr(p1.get("counter_p")), inr(p1.get("docterz_p")), inr(p1.get("diff_p")) if p1.get("diff_p") else "–"])
        out = [L(dot, " · %s · %s" % (dmy(D), word), b="Clinic %s" % (inr(amt) if amt is not None else "–"), who=" · ".join(who),
                 href="/finance/clinic/match", link="Morning match",
                 table=dict(head=["", "Counter", "Docterz", "Diff"], rows=rows) if rows else None, tlabel="by head and tender")]
        for f in flags:
            out.append(L("b" if f.get("owner") else "w", flag_word(f.get("code"), f.get("amount_p"))
                         + (" — reached you" if f.get("owner") else " — with the staff"), sub=True))
        T.update(clinic=inr(amt) if amt is not None else "–", clinic_word="Clinic %s · %s" % (dmy(D)[4:], word), clinic_cls=dot)
        return out

    def sanj():
        rows = (SC.days(con, S, S, "medical") or {}).get("rows") or []
        r = rows[0] if rows else None
        k = DK._row(con, S)
        if not r:
            T.update(sanj="–", sanj_word="Sanjeevni %s · not filed" % dmy(S)[4:], sanj_cls="w")
            return L("w", " · %s · no day filed yet" % dmy(S), b="Sanjeevni –", href="/finance/approvals", link="approvals")
        st = STATUS_WORDS.get(r.get("status"), str(r.get("status") or ""))
        who = ["UPI %s" % inr(r.get("upi_p")), "cash %s" % inr(r.get("cash_p"))]
        hand = "cash not handed yet"
        dot = "g" if r.get("status") in ("approved", "locked") else "w"
        if k and k.get("handed_p") is not None:
            hand = "%s handed to %s (Kal ka hisaab by %s %s)" % (inr(k["handed_p"]), str(k.get("handed_to") or "").replace("dr_", "Dr ").title(),
                                                                k.get("created_by") or "?", when(k.get("created_at"), today))
            hand += " · received ✓" if k.get("received_at") else " · not yet marked received"
            if k.get("state") == "needs_owner":
                hand += " · his word and the data differ"
                dot = "b"
        who.append(hand)
        T.update(sanj=inr(r.get("sale_p")), sanj_word="Sanjeevni %s · %s" % (dmy(S)[4:], st.split(",")[0]), sanj_cls=dot)
        return L(dot, " sale · %s · %s" % (dmy(S), st), b="Sanjeevni %s" % inr(r.get("sale_p")), who=" · ".join(who),
                 href="/finance/approvals", link="approvals")

    def physio():
        p = CR.physio_row(con, D)
        if not p:
            return L("n", "Physiotherapy · %s · nothing entered" % dmy(D), href="/finance/physio", link="physiotherapy")
        tot = int(p["cash_p"] or 0) + int(p["upi_p"] or 0)
        who = "entered by %s %s" % (p["entered_by"], when(p["entered_at"], today))
        who += " · cash %s, UPI %s" % (inr(p["cash_p"]), inr(p["upi_p"]))
        if tot:
            who += " · received ✓" if p["received_at"] else " · not yet marked received"
        return L("g" if (p["received_at"] or not tot) else "w", " · %s" % dmy(D), b="Physiotherapy %s" % inr(tot), who=who,
                 href="/finance/physio", link="physiotherapy")

    def month():
        ym = today[:7]
        c = con.execute("SELECT COALESCE(SUM(total_amount_p),0), COUNT(*) FROM clinic_day_revenue WHERE substr(business_date,1,7)=?",
                        (ym,)).fetchone()
        srows = (SC.days(con, ym + "-01", today, "medical") or {}).get("rows") or []
        s = sum(int(r.get("sale_p") or 0) for r in srows)
        ph = con.execute("SELECT COALESCE(SUM(cash_p+upi_p),0) FROM clinic_physio_day WHERE substr(business_date,1,7)=?", (ym,)).fetchone()[0]
        return L("n", "%s so far: clinic %s (%d days) · Sanjeevni %s (%d days) · physiotherapy %s"
                 % (MON[int(ym[5:7]) - 1], inr(c[0]), int(c[1]), inr(s), len(srows), inr(ph)),
                 href="/finance/clinic/day", link="Docterz Revenue")

    def shelf():
        out = []
        road = PK.statement_road(con)
        out.append(L({"ok": "g", "info": "n"}.get(road.get("state"), "w"), str(road.get("text") or "The statement road was not read."),
                     href="/finance/packs", link="packs"))
        first = dt.date.fromisoformat(today[:8] + "01")
        pm = (first - dt.timedelta(days=1)).isoformat()[:7]
        cells = PK.cells(con, pm)
        on = sum(1 for c in cells if c.get("state") != "empty")
        out.append(L("g" if on == len(cells) else "w", "%s statements: %d of %d on the shelf" % (MON[int(pm[5:7]) - 1], on, len(cells)),
                     href="/finance/packs", link="packs", sub=True))
        return out

    piece(lines, "The clinic's day", clinic)
    piece(lines, "Sanjeevni's day", sanj)
    piece(lines, "The physiotherapy day", physio)
    piece(lines, "The month so far", month)
    piece(lines, "The statement shelf", shelf)
    fl = state["flags"]
    return dict(ok=True, name="Money", chip=("%d flag%s" % (fl, "" if fl == 1 else "s")) if fl else T.get("clinic_word", "").split(" · ")[-1] or "read",
                cls="b" if state["bad"] else ("w" if fl else "g"), word="clinic %s · Sanjeevni %s" % (dmy(D)[4:], dmy(S)[4:]), lines=lines)


def _work_people_map(lines, cx):
    """1.0's reading of the map by person -- the fallback when the staff's list engine cannot be used."""
    duties = cx.get("duties")
    late_n = open_n = 0
    if duties:
        people, shared = duties["people"], duties["shared"]
        sharers = {}
        for a, b in shared.items():
            sharers.setdefault(b, []).append(a)
        punch = cx.get("punch") or {}
        for p in [k for k in people if k != "manoj"]:
            mine = [d for d in duties["duties"] if d["person"] == p]
            if not mine:
                continue
            due = [d for d in mine if d["n"] > 0]
            late = [d for d in due if d["late"]]
            late_n += len(late)
            open_n += len(due)
            name = str(people.get(p) or p)
            extra = [str(people.get(s) or s) for s in sharers.get(p, [])]
            pv = [("%s %s" % (str(people.get(x) or x), punch[x])) for x in [p] + sharers.get(p, []) if x in punch]
            who = ("%d open, %d late" % (len(due), len(late))) if due else "nothing open"
            who += " · %d dut%s watched" % (len(mine), "y" if len(mine) == 1 else "ies")
            if pv:
                who = " · ".join(pv) + " · " + who
            lines.append(L("b" if late else ("w" if due else "g"), (" (with %s)" % ", ".join(extra)) if extra else "", b=name, who=who))
            due.sort(key=lambda d: (0 if d["late"] else 1, -(d["days"] or 0)))
            for d in due:
                lines.append(duty_line(d))
            errs = [d for d in mine if d["err"]]
            if errs:
                lines.append(L("n", "%d of %s's duties could not be checked just now." % (len(errs), name), sub=True,
                               why="; ".join("%s: %s" % (d["id"], d["err"]) for d in errs)[:400]))
    else:
        lines.append(L("n", "The duty map could not be read just now, so the list by person is not shown.", why=cx.get("duties_err") or "no map"))
    return late_n, open_n


def list_blocks(aaj):
    """[(queues, [member logins])] -- one block per LIST: the logins that see exactly the same queues share a block (the
    desk's two people), and a login that sees only part of another's list (the desk's shared login) has no block of its own."""
    names, works = aaj["names"], aaj["works"]
    persons = []
    for i in aaj["items"]:
        if i["person"] and i["person"] != "manoj" and i["person"] not in persons:
            persons.append(i["person"])
    logins = list(dict.fromkeys(persons + [lg for lg in list(names) + list(works) if lg != "manoj"]))
    sets = {lg: tuple(works.get(lg) or [lg]) for lg in logins}
    blocks = []
    for lg in logins:
        qs = sets[lg]
        if not any(q in persons for q in qs) or any(set(qs) < set(o) for o in sets.values()):
            continue
        for b in blocks:
            if set(b[0]) == set(qs):
                b[1].append(lg)
                break
        else:
            blocks.append((qs, [lg]))
    blocks.sort(key=lambda b: min(persons.index(q) for q in b[0] if q in persons))
    return blocks


def _work_people_aaj(lines, cx, aaj):
    """1.1: list by list, exactly what the staff's own lists hold -- the open lines in the owner's English, what waits to
    be tapped, and what was tapped, by whom and when. The head line opens that list as its people see it."""
    names, punch = aaj["names"], (cx.get("punch") or {})
    late_n = open_n = 0
    for qs, members in list_blocks(aaj):
        mine = [i for i in aaj["items"] if i["person"] in qs and i["kind"] in ("sql", "tick") and not i.get("fact")]
        if not mine:
            continue
        sql = [i for i in mine if i["kind"] == "sql" and not i["err"]]
        due = sorted([i for i in sql if i["n"] > 0 and not i.get("soft")], key=lambda i: (0 if i["late"] else 1, -(i["days"] or 0)))
        soft = [i for i in sql if i["n"] > 0 and i.get("soft")]
        ticks = [i for i in mine if i["kind"] == "tick" and i.get("live")] if aaj.get("on") else []     # no tap exists until the lists are on
        topen, tdone = [i for i in ticks if not i.get("done")], [i for i in ticks if i.get("done")]
        late = [i for i in due if i["late"]] + [i for i in topen if i["late"]]
        late_n += len(late)
        open_n += len(due) + len(topen)
        head = " / ".join(str(names.get(w, w)) for w in members)
        extra = [str(names.get(q, q)) for q in qs if q not in members]
        pv = [("%s %s" % (str(names.get(w, w)), punch[w])) for w in members if w in punch]
        who = ("%d open, %d late" % (len(due) + len(topen), len(late))) if (due or topen) else "nothing open"
        who += " · %d line%s watched" % (len(mine), "" if len(mine) == 1 else "s")
        if pv:
            who = " · ".join(pv) + " · " + who
        lines.append(L("b" if late else ("w" if (due or topen) else "g"), (" (with the %s desk's lines)" % ", ".join(extra)) if extra else "",
                       b=head, who=who, href="/finance/aaj?as=%s" % members[0], link="%s's list" % str(names.get(members[0], members[0]))))
        for i in due:
            lines.append(L("b" if i["late"] else "w", i["en"], href=i["door"], link=i["tile"] or "open", sub=True))
        for i in soft:
            lines.append(L("n", i["en"], href=i["door"], link=i["tile"] or "open", sub=True))
        for i in topen:
            lines.append(L("b" if i["late"] else "w", "To be tapped: %s" % i["en"], sub=True))
        for i in tdone:
            lines.append(L("g", "Tapped done: %s — %s %s" % (i["en"], i["done"].get("by_name") or i["done"].get("by") or "?",
                                                             when(i["done"].get("at"), cx["today"])), sub=True))
        hidden = sum(max(0, int(i["n_all"]) - int(i["n"])) for i in sql)
        if hidden:                                                     # what the floor keeps off this list is said, never silent
            lines.append(L("n", "%d older item%s %s kept off this list (nothing before %s, or before a duty's own first day)."
                           % (hidden, "" if hidden == 1 else "s", "is" if hidden == 1 else "are", dm(aaj.get("floor"))), sub=True,
                           why="; ".join("%s: %d of %d" % (i["id"], i["n"], i["n_all"]) for i in sql if i["n_all"] > i["n"])[:300]))
        errs = [i for i in mine if i["kind"] == "sql" and i["err"]]
        if errs:
            lines.append(L("n", "%d of %s's lines could not be checked just now." % (len(errs), head), sub=True,
                           why="; ".join("%s: %s" % (i["id"], i["err"]) for i in errs)[:400]))
    return late_n, open_n


def read_panel(K, copy, now):
    """S512 (F-779): every person on his panel, their list as they see it (person_list in the owner's view) and their tasks."""
    rd = K.Reader(copy, now)
    try:
        out = []
        for key, doc in rd.people.items():
            if key == "manoj":
                continue
            lst = K.person_list(rd, doc, True)
            en = {ln["id"]: (ln.get("en") or ln.get("hi") or ln["id"]) for ln in doc["lines"]}
            rows = [dict(r, en=en.get(r["id"], r.get("text") or r["id"])) for sec in lst["sections"].values() for r in sec]
            out.append(dict(key=key, name=doc.get("name") or key, on=bool(doc.get("on")), list_on=bool(rd.on), rows=rows,
                            unread=lst.get("unread", 0), tasks=K.tasks_of_person(rd, key),
                            as_login=((K.SEED.VIEW_AS.get(key) if getattr(K, "SEED", None) is not None else None) or key)))
        return out
    finally:
        rd.close()


def _work_people_panel(lines, cx):
    """S512 (F-779): list by list, as his panel cuts them -- the open lines in his English, what waits to be tapped, what
    was tapped and by whom, the green 'done' rows, and each person's tasks with their answers."""
    open_n, today = 0, cx["today"]
    for p in cx["panel"]:
        if not p["on"] or not p["list_on"]:
            lines.append(L("n", "%s: the list is switched off" % p["name"], href="/finance/aaj?as=%s" % p["as_login"], link="the list"))
            continue
        job = [r for r in p["rows"] if r["kind"] == "job"]
        topen = [r for r in p["rows"] if r["kind"] == "tick" and not r.get("done") and not r.get("later")]
        tdone = [r for r in p["rows"] if r["kind"] == "tick" and r.get("done")]
        green = [r for r in p["rows"] if r["kind"] == "done"]
        fetch = [r for r in p["rows"] if r["kind"] == "fetch"]
        tasks = p["tasks"]
        t_open = [t for t in tasks if t["state"] == "open"]
        t_ans = [t for t in tasks if t["state"] in ("done", "cant")]
        n = len(job) + len(topen) + len(t_open)
        open_n += n
        lines.append(L("w" if n else "g", "", b=p["name"], who=("%d open" % n if n else "nothing open") + (" · %d task%s answered" % (len(t_ans), "" if len(t_ans) == 1 else "s") if t_ans else ""),
                       href="/finance/aaj?as=%s" % p["as_login"], link="%s's list" % p["name"]))
        for r in job:
            lines.append(L("w", r["en"], href=r.get("door"), link=r.get("tile") or "open", sub=True))
        for r in topen:
            lines.append(L("w", "To be tapped: %s" % r["en"], sub=True))
        for r in fetch:
            lines.append(L("n", "Shown only when something waits behind its page: %s" % r["en"], sub=True))
        for r in tdone:
            d = r["done"]
            lines.append(L("g", "Tapped done: %s — %s %s" % (r["en"], d.get("by_name") or d.get("by") or "?", when(d.get("at"), today)), sub=True))
        for r in green:
            lines.append(L("g", "Done: %s" % r["en"], sub=True))
        for t in t_open:
            lines.append(L("w", "Task: %s — given by %s %s" % (t["text"], t.get("by_name") or t.get("by_whom"), when(t.get("at"), today)), sub=True))
        for t in t_ans:
            last = (t.get("notes") or [{}])[-1]
            lines.append(L("g" if t["state"] == "done" else "b", "Task %s: %s — %s %s%s" % (
                "done" if t["state"] == "done" else "could not be done", t["text"], last.get("by_name") or t.get("state_by") or "?",
                when(t.get("state_at"), today), (": " + last["note"]) if last.get("note") else ""), href="/finance/aaj", link="close it", sub=True))
        if p.get("unread"):
            lines.append(L("n", "%d of %s's lines could not be read just now." % (p["unread"], p["name"]), sub=True))
    return 0, open_n


def sec_work(con, cx):
    today, D, S, T = cx["today"], cx["clinic_day"], cx["sanj_day"], cx["tile"]
    lines = []

    def exports():
        out = []
        for kind, label in (("consultation", "Consultation report"), ("followup", "Follow-up log")):
            r = con.execute("SELECT rows, taken_at, drive_id FROM docterz_export WHERE kind=? AND business_date=? AND status='current' "
                            "ORDER BY id DESC LIMIT 1", (kind, cx["lwd"])).fetchone()
            if r:
                road = "straight from the reception PC" if str(r["drive_id"] or "").startswith("reception:") else "through Drive"
                out.append(L("g", "Docterz %s of %s reached the server %s (%d rows, %s)" % (label, dmy(cx["lwd"]), when(r["taken_at"], today),
                                                                                         int(r["rows"] or 0), road)))
            else:
                out.append(L("b", "Docterz %s of %s has NOT reached the server" % (label, dmy(cx["lwd"])), who="reception exports it; "
                             "the Callback Tracker, the follow-up tracker and the revenue sheet wait on it", href="/finance/clinic/day",
                             link="Docterz Revenue"))
        return out

    def entries():
        out = []
        reg = con.execute("SELECT entered_by, entered_at FROM clinic_register_day WHERE business_date=?", (D,)).fetchone()
        out.append(L("g", "Docterz daily collection of %s entered by %s %s" % (dmy(D), reg["entered_by"], when(reg["entered_at"], today)))
                   if reg else L("b", "Docterz daily collection of %s is NOT entered" % dmy(D), href="/finance/clinic/register",
                                 link="daily collection"))
        e = con.execute("SELECT status, entered_by, entered_at, approved_by, approved_at FROM day_entry WHERE unit='medical' AND business_date=?",
                        (S,)).fetchone()
        if e:
            t = "Sanjeevni day of %s filed by %s %s" % (dmy(S), "the system" if e["entered_by"] == "auto" else e["entered_by"],
                                                         when(e["entered_at"], today))
            t += (" · approved by %s %s" % (e["approved_by"], when(e["approved_at"], today))) if e["approved_by"] else " · not approved yet"
            out.append(L("g" if e["approved_by"] else "w", t))
        else:
            out.append(L("w", "Sanjeevni day of %s is not filed yet" % dmy(S), href="/finance/reports/aaj", link="Aaj ki reports"))
        k = con.execute("SELECT created_by, created_at, handed_p FROM darpan_kal_day WHERE unit='medical' AND business_date=?", (S,)).fetchone()
        out.append(L("g", "Darpan's Kal ka hisaab of %s entered by %s %s" % (dmy(S), k["created_by"], when(k["created_at"], today)))
                   if k and k["handed_p"] is not None else L("w", "Darpan's Kal ka hisaab of %s is not entered yet" % dmy(S),
                                                              href="/finance/darpan/kal", link="Kal ka hisaab"))
        return out

    def marg():
        rows = con.execute("SELECT type, verdict, COUNT(*), MAX(received_at) FROM mi_file WHERE substr(received_at,1,10)=? "
                           "GROUP BY type, verdict ORDER BY 4", (today,)).fetchall()
        if not rows:
            return L("n", "No Marg report has reached the server today", href="/finance/reports/aaj", link="Aaj ki reports")
        good = ["%s %s" % (str(r[0] or "unnamed").replace("_", " ").lower(), hm(r[3])) for r in rows if r[1] == "VERIFIED"]
        bad = sum(int(r[2]) for r in rows if r[1] != "VERIFIED")
        return L("w" if bad else "g", "Marg reports today: " + (", ".join(good) if good else "none accepted")
                 + ((" · %d refused" % bad) if bad else ""), href="/finance/reports/aaj", link="Aaj ki reports")

    def petty():
        r = con.execute("SELECT by_whom, entry_date, at FROM petty_entry WHERE void_at='' ORDER BY at DESC LIMIT 1").fetchone()
        wait = con.execute("SELECT COUNT(*) FROM petty_entry WHERE void_at='' AND confirm_at='' AND kind IN ('receive','loan_out')").fetchone()[0]
        if not r:
            return L("n", "Petty book: no entry yet", href="/finance/petty", link="petty book")
        gap = days_since(r["entry_date"])
        t = "Petty book: last entry by %s, %s" % (r["by_whom"], when(r["at"], today))
        if wait:
            t += " · %d waiting for a confirmation" % wait
        return L("g" if (gap is not None and gap <= 1) else "w", t, href="/finance/petty", link="petty book")

    piece(lines, "The Docterz exports", exports)
    piece(lines, "The day's entries", entries)
    piece(lines, "The Marg reports", marg)
    piece(lines, "The petty book", petty)
    lines.append(L("n", "Staff register: reading…", href="/register/review", link="Staff Register", fill="reg"))
    not_done = sum(1 for x in lines if x.get("dot") == "b")

    aaj = cx.get("aaj")
    lines.append(L("n", "Staff lists: reading…", fill="aaj"))
    late_n, open_n = (_work_people_panel(lines, cx) if cx.get("panel") else                      # S512 (F-779)
                      _work_people_aaj(lines, cx, aaj) if aaj else _work_people_map(lines, cx))
    T.update(work_late=late_n, work_open=open_n, work_not_done=not_done)
    bad = late_n + not_done
    return dict(ok=True, name="Today's work", chip=("%d late" % bad) if bad else "up to date",
                cls="b" if not_done else ("w" if late_n else "g"), word="who did what, when · %d open" % open_n, lines=lines)


def sec_att(con, cx):
    att, today = cx.get("att"), cx["today"]
    T = cx["tile"]
    lines = []
    if not att:
        lines.append(L("n", "Today's punches could not be read just now.", why=cx.get("att_err") or "not read"))
        chip, cls, word = "not read", "n", ""
    else:
        day, usual = att["day"], att["usual"]
        nowm = cx["now"].hour * 60 + cx["now"].minute
        late = [r for r in day["present"] if r.get("late")]
        due_absent, later = [], []
        for r in day["absent"]:
            u = usual.get(r["uid"])
            (due_absent if (u is None or nowm > u[0] + 30) else later).append((r, u))
        T.update(att_in=day["present_count"], att_total=day["total"], att_late=len(late), att_absent=len(due_absent))
        if late:
            lines.append(L("w", "Late: " + ", ".join(("%s %s (%d min)" % (r["name"], r["first"].strftime("%H:%M"), r["late_min"])) if r.get("late_min")
                                                     else ("%s %s" % (r["name"], r["first"].strftime("%H:%M"))) for r in late)))
        if due_absent:
            lines.append(L("b", "No punch: " + ", ".join("%s%s" % (r["name"], (" (usual %s)" % u[1]) if u else "") for r, u in due_absent),
                           who="a leave marked in the staff register is not read here yet"))
        if later:
            lines.append(L("n", "Not due yet: " + ", ".join("%s (usual %s)" % (r["name"], u[1]) for r, u in later)))
        rows = [[r["name"], r["first"].strftime("%H:%M"), r["last"].strftime("%H:%M") if r["n"] >= 2 else "–",
                 ("%d min late" % r["late_min"]) if r.get("late") else ""] for r in day["present"]]
        lines.append(L("g", "In today: %d of %d" % (day["present_count"], day["total"]),
                       table=dict(head=["Name", "First", "Last", ""], rows=rows) if rows else None, tlabel="see who and when",
                       href="https://attendance.dr-manoj.in", link="attendance"))
        chip = "%d of %d in" % (day["present_count"], day["total"])
        cls = "b" if due_absent else ("w" if late else "g")
        word = " · ".join(x for x in (("%d late" % len(late)) if late else "", ("%d no punch" % len(due_absent)) if due_absent else "") if x)
    lines.append(L("n", "Staff register: reading…", href="/register/review", link="Staff Register", fill="reg"))

    def lock():
        first = dt.date.fromisoformat(today[:8] + "01")
        pm = (first - dt.timedelta(days=1)).isoformat()[:7]
        rc = sqlite3.connect("file:%s?mode=ro" % REGISTER_DB, uri=True, timeout=5)
        try:
            r = rc.execute("SELECT status, locked_by, locked_ts FROM locked_run WHERE ym=?", (pm,)).fetchone()
        finally:
            rc.close()
        mon = MON[int(pm[5:7]) - 1]
        if r and r[0] == "locked":
            return L("g", "%s salary month: locked by %s %s" % (mon, r[1], when(r[2], today)), href="/register/salary?ym=%s" % pm, link="the month")
        return L("w", "%s salary month: not locked yet" % mon, href="/register/salary?ym=%s" % pm, link="the month")

    piece(lines, "The salary month's lock", lock)
    return dict(ok=True, name="Attendance", chip=chip, cls=cls, word=word, lines=lines)


def sec_sanj(con, cx):
    ny = cx.get("needs_you")
    lines = []
    if not ny:
        return dict(ok=True, name="Sanjeevni", chip="not read", cls="n", word="",
                    lines=[L("n", "The approvals page's list could not be read just now.", why=cx.get("needs_you_err") or "not read")])
    rows = ny.get("lines") or []
    for x in rows:
        dot = {"bad": "b", "warn": "w", "info": "n", "ok": "g"}.get(x.get("cls"), "n")
        lines.append(L(dot, str(x.get("text") or ""), href=TARGET_DOOR.get(x.get("target"), "/finance/approvals"), link="open"))
    n = sum(1 for x in rows if x.get("cls") in ("bad", "warn"))
    if not rows:
        lines.append(L("g", "Nothing open on the approvals page."))
    if cx.get("darpan_err"):
        lines.append(L("n", "Darpan's own card could not be read here; the Kal ka hisaab page has it.",
                       href="/finance/darpan/kal", link="Kal ka hisaab", why=cx["darpan_err"]))
    cx["tile"]["sanj_open"] = n
    return dict(ok=True, name="Sanjeevni", chip=("%d open" % n) if n else "clear", cls="b" if any(x.get("cls") == "bad" for x in rows) else ("w" if n else "g"),
                word="%d line%s" % (len(rows), "" if len(rows) == 1 else "s"), lines=lines)


def sec_papers(con, cx):
    D = cx["clinic_day"]
    lines = []
    tot = {"n": 0}

    def lanes():
        ac = sqlite3.connect("file:%s?mode=ro" % ASSETS_DB, uri=True, timeout=5)
        try:
            n = ac.execute("SELECT COUNT(*) FROM bills b WHERE COALESCE(b.lane,'clinic')='clinic' AND b.status IN ('draft','approved') "
                           "AND b.dup_of IS NULL AND b.page_of IS NULL AND COALESCE(b.subgroup,'')=''").fetchone()[0]
        finally:
            ac.close()
        tot["n"] += int(n)
        return L("w" if n else "g", "%d clinic paper%s to sort into lanes" % (n, "" if n == 1 else "s"), href="/scanapp", link="Asset Register")

    def recs():
        import records                                                 # noqa: PLC0415
        text, n, _old = records.check_line(con)
        tot["n"] += int(n or 0)
        return L("w" if n else "g", str(text), href="/finance/checks", link="Check karein")

    def baaki():
        import slip_log                                                # noqa: PLC0415
        c = slip_log.pending_counts(con)
        n = int(c.get("blood") or 0) + int(c.get("xray") or 0)
        tot["n"] += n
        red = int(c.get("blood_red") or 0) + int(c.get("xray_red") or 0)
        t = "Report baaki: X-ray %d (%d late) · blood %d (%d late)" % (int(c.get("xray") or 0), int(c.get("xray_red") or 0),
                                                                      int(c.get("blood") or 0), int(c.get("blood_red") or 0))
        if c.get("orphans"):
            t += " · %d report%s with no slip" % (int(c["orphans"]), "" if int(c["orphans"]) == 1 else "s")
        if c.get("no_id"):
            t += " · %d without an ID" % int(c["no_id"])
        return L("b" if red else ("w" if n else "g"), t, href="/finance/slips/pending", link="Report baaki")

    def slips():
        import slip_log                                                # noqa: PLC0415
        m = slip_log.match_day(con, D)
        fl, orph = nlen(m.get("flags")), nlen(m.get("orphans"))
        t = "Slips of %s: %d OPD, %d X-ray / procedure" % (dmy(D), nlen(m.get("opd")), nlen(m.get("xp")))
        t += " · %d question%s" % (fl, "" if fl == 1 else "s") if fl else " · no question"
        if orph:
            t += " · %d Docterz line%s with no slip" % (orph, "" if orph == 1 else "s")
        return L("w" if (fl or orph) else "g", t, href="/finance/slips", link="slips")

    def xray():
        with open(BEAT, encoding="utf-8") as fh:
            x = ((json.load(fh).get("beat") or {}).get("xray") or {})
        w, c = int(x.get("inbox_waiting") or 0), int(x.get("check_waiting") or 0)
        return L("w" if (w or c) else "g", "X-ray pictures on the reception PC: %d waiting to be filed · %d to check" % (w, c))

    piece(lines, "The scanned papers", lanes)
    piece(lines, "The patient-record checks", recs)
    piece(lines, "Report baaki", baaki)
    piece(lines, "The day's slips", slips)
    piece(lines, "The reception PC's X-ray folder", xray)
    n = tot["n"]
    return dict(ok=True, name="Scans & papers", chip=str(n), cls="w" if n else "g", word="waiting" if n else "clear", lines=lines)


def sec_system(con, cx):
    lines = [L("n", "Health: reading…", href="/finance/health", link="health", fill="health")]
    T = cx["tile"]
    st = {"stale": 0, "bad": False}

    def fresh():
        with open(FRESH, encoding="utf-8") as fh:
            f = json.load(fh)
        c = f.get("counts") or {}
        legs = [x for x in (f.get("legs") or []) if str(x.get("verdict") or "").upper() not in ("OK", "PARKED")]
        st["stale"] = len(legs)
        try:                                                           # S512 (F-774): a reading has an age
            gen = dt.datetime.fromisoformat(str(f.get("generated_iso") or "")[:19])
            hours = (cx["now"] - gen).total_seconds() / 3600.0
        except ValueError:
            hours = None
        if hours is None or hours > 26:
            st["stale"] = max(st["stale"], 1)
            T.update(sys_word="the freshness check has not run since %s" % when(f.get("generated_iso"), cx["today"]), sys_cls="w")
            return [L("w", "The freshness check last ran %s — its %d of %d is too old to call anything fresh" % (
                when(f.get("generated_iso"), cx["today"]), int(c.get("ok") or 0), int(c.get("total") or 0)), href="/finance/freshness", link="freshness")]
        T.update(sys_word="%d of %d feeds fresh" % (int(c.get("ok") or 0), int(c.get("total") or 0)), sys_cls="w" if legs else "g")
        out = [L("w" if legs else "g", "%d of %d feeds fresh (as of %s, %d hour%s ago)" % (int(c.get("ok") or 0), int(c.get("total") or 0),
                                                                                      when(f.get("generated_iso"), cx["today"]), int(hours),
                                                                                      "" if int(hours) == 1 else "s"),
                 href="/finance/freshness", link="freshness")]
        for x in legs[:12]:
            out.append(L("w", "%s — %s, last %s" % (x.get("name"), str(x.get("verdict") or "").lower(), x.get("age_words") or "never"), sub=True))
        return out

    def beat():
        with open(BEAT, encoding="utf-8") as fh:
            h = json.load(fh)
        b = h.get("beat") or {}
        age = int(time.time() - int(h.get("received_ts") or 0)) // 60
        att = nlen(b.get("attention"))
        t = "Reception PC: last heard %s" % (("%d min ago" % age) if age < 120 else ("%d hours ago" % (age // 60)))
        why = "agent %s" % (b.get("agent_version") or "?")
        if age > 30:
            st["bad"] = True
            return L("w", t + " — it is off or offline", href="/finance/pcs", link="Clinic PCs", why=why)
        if b.get("pc_uptime_hours") is not None:
            t += " · on for %s hours" % b.get("pc_uptime_hours")
        t += (" · %d thing%s attention" % (att, " needs" if att == 1 else "s need")) if att else " · nothing needs attention"
        return L("w" if att else "g", t, href="/finance/pcs", link="Clinic PCs", why=why)

    piece(lines, "The freshness page", fresh)
    piece(lines, "The reception PC's heartbeat", beat)
    lines.append(L("n", "This reading took %s seconds." % cx.get("took", "?"),
                   why="duty map v%s · lists %s · %s" % ((cx.get("duties") or {}).get("version", "?"),
                                                          ("floor %s" % cx["aaj"].get("floor")) if cx.get("aaj") else ("fallback: %s" % cx.get("aaj_err")), VERSION)))
    chip = " · ".join(x for x in (("%d stale" % st["stale"]) if st["stale"] else "", "PC silent" if st["bad"] else "") if x) or "ok"
    return dict(ok=True, name="System", chip=chip, cls="w" if (st["stale"] or st["bad"]) else "g", word=T.get("sys_word", ""), lines=lines)


ORDER = (("needs", sec_needs), ("money", sec_money), ("work", sec_work), ("att", sec_att), ("sanj", sec_sanj),
         ("papers", sec_papers), ("system", sec_system))


def build(db_path, out_path):
    """Copy -> read -> one file. Returns the snapshot. The source database is opened read-only and never written."""
    t0 = time.time()
    now = dt.datetime.now()
    for old in os.listdir(tempfile.gettempdir()):                      # a copy left by a build that was killed
        if old.startswith("console_build_"):
            p = os.path.join(tempfile.gettempdir(), old)
            try:
                if time.time() - os.stat(p).st_mtime > LOCK_STALE + 60:
                    shutil.rmtree(p, ignore_errors=True)
            except OSError:
                pass
    tmp = tempfile.mkdtemp(prefix="console_build_")
    copy = os.path.join(tmp, "copy.db")
    con = None
    try:
        src = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=30)
        try:
            dst = sqlite3.connect(copy)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        os.environ["FINANCE_DB"] = copy                                # BEFORE any module of the app is imported
        if FIN not in sys.path:
            sys.path.insert(0, FIN)
        con = sqlite3.connect(copy, timeout=30)
        con.row_factory = sqlite3.Row
        today = now.date()
        yday = today - dt.timedelta(days=1)
        lwd = yday
        while lwd.weekday() == 6:                                      # Sunday: no counter day (docterz_pickup's own rule)
            lwd -= dt.timedelta(days=1)

        def has(sql, d):
            try:
                return con.execute(sql, (d.isoformat(),)).fetchone() is not None
            except Exception:                                          # noqa: BLE001
                return False
        clinic_day = yday if (yday.weekday() != 6 or has("SELECT 1 FROM clinic_day_revenue WHERE business_date=?", yday)) else lwd
        sanj_day = yday if (yday.weekday() != 6 or has("SELECT 1 FROM day_entry WHERE unit='medical' AND business_date=?", yday)) else lwd
        cx = dict(now=now, today=today.isoformat(), yday=yday.isoformat(), lwd=lwd.isoformat(), clinic_day=clinic_day.isoformat(),
                  sanj_day=sanj_day.isoformat(), tile={})
        # FIRST the owner's own Needs-you tree, as the approvals page builds it -- on the copy, inside a request of the builder's
        # own. It comes before the duty map because it refreshes figures some duties read (returns.pending_ok): read the other
        # way round, 'Needs you' would carry the count of the last time somebody opened the approvals page.
        try:
            import flask                                               # noqa: PLC0415
            import sanjeevni_approvals                                 # noqa: PLC0415
            try:
                import darpan_kal                                      # noqa: PLC0415
                darpan_kal._db = lambda: con                           # his card reads through the module's own door: the copy
                darpan_kal._require = lambda *a, **k: ({"user": "manoj", "role": "doctor", "roles": ["checker"]}, None)
            except Exception as e:                                     # noqa: BLE001
                cx["darpan_err"] = "%s: %s" % (type(e).__name__, str(e)[:80])
            with flask.Flask("owner_console_build").test_request_context("/finance/darpan/kal/api/owner"):
                # the tree swallows a fault in Darpan's card (its own fail-soft). Asked once here first, so that a card that
                # cannot be read through this door is SAID on the page instead of silently missing from the list.
                if not cx.get("darpan_err"):
                    try:
                        r = darpan_kal.api_owner()
                        j = r.get_json() if not isinstance(r, tuple) else None
                        if not (j and j.get("ok")):
                            cx["darpan_err"] = "the card answered %s" % (r[1] if isinstance(r, tuple) else "not ok")
                    except Exception as e:                             # noqa: BLE001
                        cx["darpan_err"] = "%s: %s" % (type(e).__name__, str(e)[:80])
                cx["needs_you"] = sanjeevni_approvals.needs_you(con)
        except Exception as e:                                         # noqa: BLE001
            cx["needs_you"], cx["needs_you_err"] = None, "%s: %s" % (type(e).__name__, str(e)[:100])
        try:
            con.commit()                                               # ON THE COPY: the duty map's own reader opens the file again
        except Exception:                                              # noqa: BLE001
            pass
        try:
            import aaj_kaam                                            # noqa: PLC0415 -- 1.1: the staff's own list engine, on the copy
            cx["aaj"] = aaj_kaam.build_all(copy, now)
            try:                                                       # S512 (F-779): the lists as his panel cuts them
                cx["panel"] = read_panel(aaj_kaam, copy, now)
            except Exception as e:                                     # noqa: BLE001 -- 1.1's reading stands in
                cx["panel"], cx["panel_err"] = None, "%s: %s" % (type(e).__name__, str(e)[:100])
            if cx["aaj"].get("map_err"):
                raise RuntimeError("the duty map: %s" % cx["aaj"]["map_err"])
            if cx["aaj"].get("extra_err"):                              # no duties file = no floor: never shown as if it were the list
                raise RuntimeError("the duties file: %s" % cx["aaj"]["extra_err"])
        except Exception as e:                                         # noqa: BLE001 -- 1.0's own reading of the map stands in
            cx["aaj"], cx["aaj_err"] = None, "%s: %s" % (type(e).__name__, str(e)[:100])
        try:
            cx["duties"] = read_duties(copy)
        except Exception as e:                                         # noqa: BLE001
            cx["duties"], cx["duties_err"] = None, "%s: %s" % (type(e).__name__, str(e)[:100])
        try:
            cx["att"] = read_attendance(now)
        except Exception as e:                                         # noqa: BLE001
            cx["att"], cx["att_err"] = None, "%s: %s" % (type(e).__name__, str(e)[:100])
        try:
            cx["punch"] = punch_by_login(cx["att"], list(((cx.get("aaj") or {}).get("names") or (cx.get("duties") or {}).get("people") or {}).keys()), now)
        except Exception:                                              # noqa: BLE001
            cx["punch"] = {}
        sections, failed = {}, []
        for key, fn in ORDER:
            cx["took"] = "%.1f" % (time.time() - t0)
            try:
                sections[key] = fn(con, cx)
            except Exception as e:                                     # noqa: BLE001 -- one section never takes the page down
                failed.append(key)
                sections[key] = dict(ok=False, name={"needs": "Needs you", "money": "Money", "work": "Today's work", "att": "Attendance",
                                                     "sanj": "Sanjeevni", "papers": "Scans & papers", "system": "System"}[key],
                                     chip="not read", cls="n", word="", lines=[unread("This section", e)])
                sections[key]["why"] = "%s: %s" % (type(e).__name__, str(e)[:160])
        T = cx["tile"]
        T["as_of_hm"] = now.strftime("%H:%M")
        fa = sys.modules.get("finance_app")                            # the guard, said in every reading: which database did the app's
        guard = dict(env_is_copy=os.environ.get("FINANCE_DB") == copy,  # own modules see? Only ever the copy.
                     app_loaded=fa is not None, app_db_is_copy=(getattr(fa, "DB_PATH", None) == copy) if fa is not None else None)
        lists = dict(engine=bool(cx.get("aaj")), err=cx.get("aaj_err"), floor=(cx.get("aaj") or {}).get("floor"), on=bool((cx.get("aaj") or {}).get("on")),
                     views=(cx.get("aaj") or {}).get("views"))
        snap = dict(ok=True, version=VERSION, guard=guard, lists=lists, built_epoch=time.time(), as_of=now.replace(microsecond=0).isoformat(),
                    as_of_hm=now.strftime("%H:%M"), day=cx["today"], day_words=dmy(cx["today"]), clinic_day=cx["clinic_day"],
                    sanj_day=cx["sanj_day"], lwd=cx["lwd"], order=[k for k, _f in ORDER], sections=sections, tile=T, failed=failed,
                    took_s=round(time.time() - t0, 2))
        if out_path:
            part = "%s.part%d" % (out_path, os.getpid())
            with open(part, "w", encoding="utf-8") as fh:
                json.dump(snap, fh, ensure_ascii=False)
            os.chmod(part, 0o600)
            os.replace(part, out_path)
        return snap
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:                                          # noqa: BLE001
                pass
        shutil.rmtree(tmp, ignore_errors=True)


def _cli(argv):
    def arg(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default
    db_path, out, lock = arg("--db"), arg("--out", SNAP), arg("--lock")
    errf = out + ".err"
    try:
        if not db_path:
            raise SystemExit("usage: owner_console.py --build --db <finance.db> [--out <snapshot.json>] [--lock <file>]")
        try:
            import signal                                              # noqa: PLC0415

            def _late(*_a):
                raise TimeoutError("the reading took longer than %d seconds and was stopped" % BUILD_LIMIT)

            def _asked(*_a):
                raise SystemExit(143)                                  # the service is restarting: leave no lock and no copy
            signal.signal(signal.SIGALRM, _late)
            signal.signal(signal.SIGTERM, _asked)
            signal.signal(signal.SIGHUP, _asked)
            signal.alarm(BUILD_LIMIT)                                  # a build that hangs ends itself, and says so
        except Exception:                                              # noqa: BLE001
            pass
        snap = build(db_path, out)
        try:
            os.unlink(errf)
        except OSError:
            pass
        print("console reading written: %s · %s s · sections not read: %s" % (snap["as_of"], snap["took_s"], ", ".join(snap["failed"]) or "none"))
        return 0
    except Exception as e:                                             # noqa: BLE001
        import traceback                                               # noqa: PLC0415
        traceback.print_exc()
        try:
            with open(errf, "w", encoding="utf-8") as fh:
                fh.write("%d|failed|%s -- %s: %s" % (int(time.time()), time.strftime("%H:%M"), type(e).__name__, str(e)[:200]))
            os.chmod(errf, 0o600)
        except OSError:
            pass
        return 1
    finally:
        if lock:
            try:
                os.unlink(lock)
            except OSError:
                pass


if __name__ == "__main__":
    if "--build" in sys.argv:
        sys.exit(_cli(sys.argv))
    raise SystemExit("owner_console.py is mounted by finance_app.py; by hand only: --build --db <finance.db> --out <file>")
