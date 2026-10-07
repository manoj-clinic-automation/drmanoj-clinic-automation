#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aaj_kaam.py -- S493_LISTS_2 (parent; session 298, 07-Oct-2026). The staff's own daily list, 'Aaj ka kaam', rebuilt.

It replaces S487's 1.0 whole. The owner read those lists and found them "confusing and complicated for the staff"; his rulings
of 06-Oct-2026, and the mock-up he then edited himself on 07-Oct (aaj_seed.py holds it exactly as he left it):
  * A SWITCH FOR EACH PERSON AND FOR EACH LINE. The old single switch (setting aaj.staff_on) stays as the one above them all:
    while it is off no staff login sees anything, whatever the panel says.
  * NOTHING BEFORE 01-OCT-2026 (setting aaj.from). The floor is laid UNDER the SQL, as in 1.0: this module's own read-only
    connection carries TEMP views that shadow the dated tables named in aaj_seed.FLOOR, so the duty map's SQL runs unedited
    and sees only rows on or after the floor (two duties whose table must NOT be shadowed carry the floor in their own
    SQL instead: aaj_seed.REWRITE). A table whose view could not be laid makes every line that reads it UNREAD --
    a line that cannot be floored is never shown as if it were. AND A SECOND GUARD, for work no view catches: a line whose
    oldest piece of work is dated before the floor is HELD BACK from staff and said on his panel (aaj_seed.NO_HOLD names
    the lines whose job is yesterday's, today's or this month's by nature). AND A THIRD: a view can hide the row that
    says a job is DONE (an order drafted on 30-Sep for a medicine listed on 2-Oct), so a line is due only when the
    unfloored books agree that something is there -- the floor can take work off a list, never put work on it.
  * WHAT HE SWITCHED OFF STAYS OFF. If his saved panel cannot be read (a locked database, a damaged row) nobody's list is
    shown until it can: the seed is the start, never the fallback.
  * ONE LINE = ONE JOB. A line is there when its work is due and gone when it is done. No count, no day, no 'late'. Its
    button opens the page of the job itself (the day of the oldest piece of that work, where the page takes a day).
  * HIS WORDING, HIS ORDER, HIS GROUPS -- the panel's, not this file's.
  * A TASK SECTION: work given from time to time, to one person or several, by him or by a login he names; the person
    answers on the same page (done / could not, with a note), he closes it or sends it back.
  * SEPTEMBER, FOR HIM ONLY: five things, on his panel.

WHAT A LIST IS NOW. For one login: the lines of its person's panel that are switched on, each decided by the duty (or duties)
aaj_seed.ENGINE names -- by default the duty of the same id in claude_code_briefs/DUTY_MAP.json (D648) or in the parent's
aaj_duties.json -- through that duty's own SQL on the floored connection; a count that lives behind another app's door is
asked by the page with the person's own login; a line with no state anywhere is tapped 'Ho gaya' (who and when are kept).

THE OWNER'S OWN LINES (person 'manoj') are NOT put on the new floor: they keep 1.0's (01-Sep-2026, setting duties.from, the
three tables of aaj_duties.json), except the two tables he ruled off for himself as well (aaj_seed.OWNER_DROP). His console
(owner_console.py) reads build_all() exactly as before and is not edited by this kit.

HOW IT READS AND WRITES. Reading is plain SELECTs through mode=ro connections to the database file. Writes go through the
service's own connection and are five small things, each to a table or setting of this module's own:
  a tap on a tick line  -> duty_tick (one row per line and period; the first tap stands)
  the owner's switch    -> setting aaj.staff_on (and, the first time, aaj.staff_first_on)
  the owner's panel     -> aaj_cfg (one JSON document per person: on/off, each line's on/off, wording, group, order)
  a task, and an answer -> aaj_task, aaj_task_note
Every POST takes a JSON body only. A staff login asking while the lists are off costs one read of one setting.
A LIST THAT IS NOT WHOLE SAYS SO: a line that cannot be read, a duty map or a duties file that cannot be read -- the page
shows a banner and neither it nor the home tile ever says 'Sab ho gaya'.

Doors -- the same five paths as 1.0 (they are in finance_app.IDENTITY_ONLY_PATHS; finance_app.py is not edited by this kit):
  GET  /finance/aaj                 staff: the list (aaj_kaam.html) · the owner: his panel (aaj_panel.html) · ?as=<login>: that list
  GET  /finance/aaj/api/list        the list and the tasks      (?as=<login> for the owner)
  GET  /finance/aaj/api/line        the home tile's line -- words only, no number
  POST /finance/aaj/api/tick        {id} a tap · {task, act, note} an answer on a task · {give:{to,text,due}} from a login he named
  GET  /finance/aaj/api/switch      the switch (?panel=1: everything the panel shows; the owner only)
  POST /finance/aaj/api/switch      {on} · {op:'person', key, doc} · {op:'assigners', logins} · {op:'task_add', ...} · {op:'task', ...}
"""
import copy
import datetime as dt
import json
import os
import re
import sqlite3

VERSION = "S493 2.0"
FIN = os.path.dirname(os.path.abspath(__file__))

try:
    import aaj_seed as SEED                                            # the owner's mock-up and the lines' working
    SEED_ERR = None
except Exception as _e:                                                # noqa: BLE001 -- without it there is no floor and no list
    SEED, SEED_ERR = None, "aaj_seed.py: %s: %s" % (type(_e).__name__, str(_e)[:100])


def _env(name, default):
    return os.environ.get(name) or default


DUTY_MAP = _env("DUTY_MAP_JSON", "/root/deploy/repo/claude_code_briefs/DUTY_MAP.json")
EXTRA = _env("AAJ_DUTIES_JSON", os.path.join(FIN, "aaj_duties.json"))
PAGE = os.path.join(FIN, "aaj_kaam.html")
PANEL = os.path.join(FIN, "aaj_panel.html")
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
WHEN = (("first", "Sabse pehle", "First thing in the morning"), ("day", "Aaj", "During the day"),
        ("comeup", "Jab aaye", "Only when it comes up"), ("night", "Jaane se pehle", "Before leaving"),
        ("week", "Is hafte", "Once a week"), ("month", "Is mahine", "Once a month"))
WHEN_KEYS = tuple(w[0] for w in WHEN)
NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
OWN_RE = re.compile(r"^own\.[a-z0-9]{1,16}$")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TICK_SQL = ("CREATE TABLE IF NOT EXISTS duty_tick (id INTEGER PRIMARY KEY, duty_id TEXT NOT NULL, period_key TEXT NOT NULL, "
            "by_whom TEXT NOT NULL, at TEXT NOT NULL, UNIQUE(duty_id, period_key))")
CFG_SQL = ("CREATE TABLE IF NOT EXISTS aaj_cfg (person TEXT PRIMARY KEY, doc TEXT NOT NULL, edited_at TEXT NOT NULL, "
           "edited_by TEXT NOT NULL)")
TASK_SQL = ("CREATE TABLE IF NOT EXISTS aaj_task (id INTEGER PRIMARY KEY, person TEXT NOT NULL, text TEXT NOT NULL, "
            "by_whom TEXT NOT NULL, at TEXT NOT NULL, due TEXT NOT NULL DEFAULT '', state TEXT NOT NULL DEFAULT 'open', "
            "state_at TEXT NOT NULL DEFAULT '', state_by TEXT NOT NULL DEFAULT '', src TEXT NOT NULL DEFAULT '')")
NOTE_SQL = ("CREATE TABLE IF NOT EXISTS aaj_task_note (id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL, by_whom TEXT NOT NULL, "
            "at TEXT NOT NULL, kind TEXT NOT NULL, note TEXT NOT NULL DEFAULT '')")
TEXT_MAX, NOTE_MAX, LINES_MAX, TASKS_AT_ONCE = 300, 500, 60, 40


# ============================================================================================ small things
def tidy(text):
    """Typography only: ' -- ' -> ' — ', 'day(s)' -> 'days' / 'day', a setting's name in brackets dropped, a date kept whole."""
    t = str(text)
    t = re.sub(r"\s*\((?:after )?[a-z_]+\.[a-z_]+\)", "", t)
    t = re.sub(r"(\d+)(\s+(?:[A-Za-z']+\s+){0,3}?[A-Za-z]+)\(s\)", lambda m: m.group(1) + m.group(2) + ("" if m.group(1) == "1" else "s"), t)
    t = t.replace("(s)", "s")
    t = re.sub(r"\b(\d{1,2})-([A-Z][a-z]{2}|\d{1,2})(?:-(\d{2,4}))?\b",
               lambda m: m.group(1) + "‑" + m.group(2) + (("‑" + m.group(3)) if m.group(3) else ""), t)
    return t.replace(" -- ", " — ").replace("X-ray", "X‑ray")


def dm(iso):
    """'2026-10-03...' -> '03‑Oct' (a hyphen that never breaks a line)."""
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return "%02d‑%s" % (d.day, MON[d.month - 1])
    except Exception:                                                  # noqa: BLE001
        return str(iso or "")[:10]


def clean(text, limit):
    """What a person typed, made safe to keep: one line, no control characters, cut to a length."""
    t = "".join(ch if (ch >= " " and ch != "\x7f") else " " for ch in str(text or ""))
    return " ".join(t.split())[:limit]


def _iso_day(v):
    try:
        return dt.date.fromisoformat(str(v)[:10]).isoformat()
    except (TypeError, ValueError):
        return None


def load_defs():
    """(the duty map, the parent's extra file). Either may be missing: the other still gives a list."""
    try:
        with open(DUTY_MAP, encoding="utf-8") as fh:
            m = json.load(fh)
    except Exception as e:                                             # noqa: BLE001
        m = {"duties": [], "people": {}, "shared": {}, "_err": "%s: %s" % (type(e).__name__, str(e)[:100])}
    try:
        with open(EXTRA, encoding="utf-8") as fh:
            x = json.load(fh)
    except Exception as e:                                             # noqa: BLE001
        x = {"extra": [], "floor": {}, "works": {}, "names": {}, "_err": "%s: %s" % (type(e).__name__, str(e)[:100])}
    if SEED is None and not x.get("_err"):
        x = dict(x, _err=SEED_ERR)                                     # no seed = no floor: said as 1.0 says a missing duties file
    return m, x


def _setting(con, key):
    try:
        r = con.execute("SELECT value FROM main.setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r else None) or None
    except sqlite3.Error:
        return None


def floor_date(con, x):
    """1.0's floor, kept for THE OWNER'S OWN LINES: the setting duties.from when it is a date, else the file's 'from', else 01-Sep-2026."""
    for cand in (_setting(con, "duties.from"), x.get("from"), "2026-09-01"):
        d = _iso_day(cand)
        if d:
            return d
    return "2026-09-01"


def staff_floor(con):
    """THE STAFF'S FLOOR: the setting aaj.from when it is a date, else the seed's (01-Oct-2026). A setting that cannot be
    READ is not a missing setting: the error is raised, and no list is cut on a guessed floor."""
    r = con.execute("SELECT value FROM main.setting WHERE key='aaj.from'").fetchone()
    for cand in ((r[0] if r else None), getattr(SEED, "FLOOR_DEFAULT", None), "2026-10-01"):
        d = _iso_day(cand)
        if d:
            return d
    return "2026-10-01"


def connect(db_path, x=None, mode=None):
    """A read-only connection to the database file. mode 'staff' lays the views of aaj_seed.FLOOR at the staff's floor;
    mode 'owner' lays 1.0's (the duties file's three tables at 1.0's floor) and aaj_seed.OWNER_DROP at the staff's floor.
    info: floor, views {table: day}, bad {table: why its view could not be laid}."""
    con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    info = {"floor": None, "views": {}, "bad": {}}
    if mode not in ("staff", "owner") or SEED is None:
        return con, info
    x = x or {}
    con.execute("PRAGMA temp_store=MEMORY")
    have = {r[0] for r in con.execute("SELECT name FROM main.sqlite_master WHERE type='table'")}
    sf = staff_floor(con)
    plan = {}
    if mode == "staff":
        info["floor"] = sf
        for t, expr in SEED.FLOOR.items():
            plan[t] = (str(expr), sf, SEED.FIRST_OF.get(t))
    else:
        of = floor_date(con, x)
        info["floor"] = of
        for t, f in (x.get("floor") or {}).items():
            col = str((f or {}).get("col") or "")
            if NAME_RE.match(col):
                plan[t] = (col, of, (f or {}).get("first_of"))
        for t in SEED.OWNER_DROP:
            if t in SEED.FLOOR:
                plan[t] = (str(SEED.FLOOR[t]), max(sf, of), None)
    for t, (expr, d, fo) in sorted(plan.items()):
        if not NAME_RE.match(t):
            continue
        if t not in have:
            info["bad"][t] = "no such table"
            continue
        if fo and len(fo) == 2 and NAME_RE.match(str(fo[0])) and NAME_RE.match(str(fo[1])) and fo[0] in have:
            try:
                first = con.execute("SELECT MIN(%s) FROM main.%s" % (fo[1], fo[0])).fetchone()[0]
                if first and str(first)[:10] > d:
                    d = dt.date.fromisoformat(str(first)[:10]).isoformat()
            except (sqlite3.Error, ValueError):
                pass
        try:
            con.execute("CREATE TEMP VIEW %s AS SELECT * FROM main.%s WHERE (%s) >= '%s'" % (t, t, expr, d))
            con.execute("SELECT 1 FROM temp.%s LIMIT 1" % t).fetchone()
            info["views"][t] = d
        except sqlite3.Error as e:
            try:
                con.execute("DROP VIEW IF EXISTS temp.%s" % t)
            except sqlite3.Error:
                pass
            info["bad"][t] = str(e)[:80]
    return con, info


def _door(v):
    """A door is a path on this site ('/...'), or nothing: what the files say is never trusted as a link."""
    v = str(v or "")
    return v if re.match(r"^/[A-Za-z0-9_~.-]", v) and "\\" not in v else None


def _fill(tpl, since):
    """A door that takes a day: '{since}' becomes the day of the oldest piece of the work; with no day, the page's own front."""
    tpl = str(tpl or "")
    if "{since}" not in tpl:
        return _door(tpl)
    s = str(since or "")[:10]
    if DAY_RE.match(s):
        return _door(tpl.replace("{since}", s))
    return _door(tpl.split("/{since}")[0])


def first_on(con, since):
    """The day the lists were FIRST turned on (setting aaj.staff_first_on), else `since`: turning them off and on again must
    not make this week's and this month's lines start over (S487 review 8)."""
    v = str(_setting(con, "aaj.staff_first_on") or "")
    try:
        dt.datetime.fromisoformat(v)
        return v
    except ValueError:
        return since


def _one(con, sql):
    """(n, since, err) of one read-only SELECT -- the same guard the duty map's own reader keeps."""
    sql = str(sql or "").strip().rstrip(";").strip()
    if not sql or not re.match(r"(?is)^(select|with)\b", sql) or ";" in sql:
        return 0, None, "no readable SQL"
    try:
        r = con.execute(sql).fetchone()
        return int((r[0] if r else 0) or 0), (r[1] if (r is not None and len(r) > 1) else None), None
    except Exception as e:                                             # noqa: BLE001
        return 0, None, str(e)[:90]


def period_key(period, today):
    if period == "week":
        y, w, _d = today.isocalendar()
        return "W%04d-%02d" % (y, w)
    if period == "month":
        return "M%04d-%02d" % (today.year, today.month)
    return "D" + today.isoformat()


def period_start(period, today):
    if period == "week":
        return today - dt.timedelta(days=today.weekday())
    if period == "month":
        return today.replace(day=1)
    return today


def staff_switch(con):
    """(on, since ISO, by) from the setting aaj.staff_on ('<iso>|<login>'; empty or absent = off)."""
    v = str(_setting(con, "aaj.staff_on") or "")
    if "|" not in v:
        return False, None, None
    since, by = v.split("|", 1)
    try:
        dt.datetime.fromisoformat(since)
    except ValueError:
        return False, None, None
    return True, since, by


def people_of(m, x):
    names = dict(m.get("people") or {})
    names.update(x.get("names") or {})
    works = {}
    for a, b in (m.get("shared") or {}).items():                       # the map: 'a' works b's queue
        works.setdefault(a, [a]).append(b) if b not in works.setdefault(a, [a]) else None
    for a, lst in (x.get("works") or {}).items():
        works[a] = list(dict.fromkeys(list(lst)))
    return names, works


def queues(login, works):
    return works.get(login) or [login]


def nm(names, login):
    """A login as the staff read it."""
    login = str(login or "")
    if login == "manoj":
        return "Dr Manoj"
    return str(names.get(login) or login.title())


# ============================================================================================ one duty, read once
def _reads(sql, table):
    return re.search(r"(?<![A-Za-z0-9_.])%s(?![A-Za-z0-9_])" % re.escape(table), str(sql or "")) is not None


def _sql_item(du, n, since, err, n_all, names, today, floor, kind, group, from_map):
    """One counted line (1.0's shape -- the owner's console reads it). BEHIND THE FLOOR: when its oldest item is older than
    the floor, the count and the day mix old with new, and the console's line says that older items are in it."""
    days = None
    if n > 0 and since:
        try:
            days = (today - dt.date.fromisoformat(str(since)[:10])).days
        except ValueError:
            days = None
    try:
        allowed = int(du.get("allowed_days") or 0)
    except (TypeError, ValueError):
        allowed = 0
    soft = bool(du.get("soft"))
    behind = bool(n > 0 and since and floor and str(since)[:10] < str(floor))
    late = bool(n > 0 and not soft and not behind and (days is None or days >= allowed))
    who = str(names.get(du.get("person"), du.get("person") or ""))
    line = du.get("owner_line") if from_map else du.get("en")
    en = None
    if line:
        try:
            en = tidy(str(line).format(n=n, days=(days if days is not None else "?"), since=dm(since) if since else "-", person=who))
        except Exception:                                              # noqa: BLE001 -- a line the map cannot fill: its description
            en = None
    if en and behind:
        en += " (includes items from before %s)" % dm(floor)
    hi = tidy(du.get("duty_hi") if from_map else (du.get("hi") or ""))
    return dict(id=du.get("id"), person=du.get("person"), also=list(du.get("also") or []), kind=kind, group=group, n=n, n_all=max(n, n_all),
                since=(str(since)[:10] if since else None), days=days, late=late, soft=soft, single=bool(du.get("single")), err=err, hi=hi,
                en=en or tidy("%s: %d" % (du.get("duty") or du.get("hi") or du.get("id"), n)), has_line=bool(en),
                how_hi=tidy(du.get("how_hi") or ""), door=_door(du.get("door")), tile=du.get("tile"), from_map=from_map, behind=behind,
                ok_hi=tidy(du.get("ok_hi") or ""), fact=(du.get("console") == "fact"))


def _item(src, du, con, bad, raw, names, today, floor, started, panel_when=None):
    """One duty of the map ('map') or of the duties file ('extra'), read on `con`. `bad` = the floored tables whose view could
    not be laid on that connection: a duty that reads one is UNREAD, never counted unfloored. `raw` = the unfloored
    connection: THE FLOOR NEVER MAKES WORK -- where the floored books show something and the whole books show nothing (a
    view hid the row that says it is done), nothing is due ('capped')."""
    kind = "sql" if src == "map" else du.get("kind")
    if kind == "sql":
        sql = (SEED.DUE.get(du.get("id")) if SEED is not None else None) or (du.get("due_sql") if src == "map" else du.get("sql"))
        whole, fit = sql, None                                         # `whole` is what the unfloored books are asked
        rw = (SEED.REWRITE.get(du.get("id")) if SEED is not None else None)
        if rw and du.get("person") != "manoj":                         # this duty is floored in its own SQL (aaj_seed.REWRITE)
            if DAY_RE.match(str(floor or "")) and str(sql or "").count(rw[0]) == 1:
                sql = str(sql).replace(rw[0], rw[1].replace("{floor}", floor))
            else:
                fit = "the floor's own piece of this duty's SQL no longer fits the duty map"
        n, since, err = (0, None, fit) if fit else _one(con, sql)
        if not err:
            hit = [t for t in sorted(bad) if _reads(sql, t)]
            if hit:
                n, since, err = 0, None, "the floor could not be laid on %s" % ", ".join(hit)
        n_all, capped = n, False
        if raw is not None:
            n_all, _s, rerr = _one(raw, whole)
            if n > 0 and not err and not rerr and n_all == 0:
                n, since, capped = 0, None, True
        it = _sql_item(du, n, since, err, n_all, names, today, floor, kind="sql",
                       group=("open" if src == "map" else (du.get("group") or "open")), from_map=(src == "map"))
        it["capped"] = capped
        return it
    if kind == "tick":
        period = du.get("period") if du.get("period") in ("day", "week", "month") else "day"
        w = (panel_when or {}).get(du.get("id"))                      # the panel's group is the line's rhythm (line_state says the same)
        if w:
            period = "week" if w == "week" else ("month" if w == "month" else "day")
        key = period_key(period, today)
        done = tick_done(con, du.get("id"), key, names)
        ps = period_start(period, today)
        # NOTHING STALE: a weekly or monthly line begins with the first week / month that STARTS on or after the day the
        # lists were first turned on (a daily line begins that day). Before the switch every line is shown, for his eye.
        live = (started is None) or (ps >= started) or period == "day"
        late_from = {"day": None, "week": ps + dt.timedelta(days=1), "month": ps + dt.timedelta(days=3)}[period]
        late = bool(done is None and started is not None and live and late_from is not None and today >= late_from)
        return dict(id=du.get("id"), person=du.get("person"), also=list(du.get("also") or []), kind="tick", group=du.get("group") or "open",
                    period=period, key=key, live=live, done=done, n=0 if done else 1, n_all=0, since=ps.isoformat(), days=None, late=late,
                    soft=False, err=None, hi=tidy(du.get("hi") or ""), en=tidy(du.get("en") or du.get("hi") or ""),
                    how_hi=tidy(du.get("how_hi") or ""), door=_door(du.get("door")), tile=du.get("tile"), from_map=False,
                    ok_hi="", fact=False, behind=False)
    if kind == "fetch":
        f = du.get("fetch") or {}
        if not _door(f.get("url")):
            return None                                                # a count can only be read from a door of this site
        return dict(id=du.get("id"), person=du.get("person"), also=list(du.get("also") or []), kind="fetch", group=du.get("group") or "open",
                    n=0, n_all=0, since=None, days=None, late=False, soft=False, err=None, hi=tidy(du.get("hi") or ""),
                    en=tidy(du.get("en") or ""), how_hi=tidy(du.get("how_hi") or ""), door=_door(du.get("door")), tile=du.get("tile"),
                    fetch={"url": str(f.get("url") or ""), "field": str(f.get("field") or ""), "only_if": f.get("only_if"),
                           "text_field": f.get("text_field")}, from_map=False, ok_hi="", fact=False, behind=False)
    return None


def tick_done(con, duty_id, key, names):
    try:
        r = con.execute("SELECT by_whom, at FROM main.duty_tick WHERE duty_id=? AND period_key=?", (duty_id, key)).fetchone()
    except sqlite3.Error:
        return None                                                    # no tap has ever been made: the table is not there yet
    return {"by": r[0], "at": r[1], "by_name": nm(names, r[0])} if r else None


def build_all(db_path, now=None, with_raw=True):
    """EVERY duty, read once -- what the owner's console is cut from (1.0's shape, key for key). The staff's lines are read on
    the staff's floor; the owner's own (person 'manoj') on 1.0's. `floor` is the staff's; `views` are the OWNER'S (his console
    cuts the detail of his own lines by them); `staff_views` and `floor_bad` say what the staff's floor stands on.
    WITHOUT THE DUTIES FILE OR THE SEED THERE IS NO FLOOR, so no line of the map is read at all."""
    now = now or dt.datetime.now()
    today = now.date()
    m, x = load_defs()
    names, works = people_of(m, x)
    con = ocon = raw = None
    try:
        con, info = connect(db_path, x, "staff")
        ocon, oinfo = connect(db_path, x, "owner")
        raw = connect(db_path, None, None)[0]                         # always: the cap needs the whole books (with_raw is 1.0's name)
        on, on_since, on_by = staff_switch(con)
        started = dt.date.fromisoformat(first_on(con, on_since)[:10]) if on else None
        try:
            panel_when = {ln["id"]: ln["when"] for p in cfg_load(con)[0].values() for ln in p["lines"]}
        except Exception:                                              # noqa: BLE001 -- the console's reading never fails for the panel
            panel_when = {}
        items = []
        for du in ([] if x.get("_err") else list(m.get("duties") or [])):
            mine = du.get("person") == "manoj"
            it = _item("map", du, (ocon if mine else con), (oinfo if mine else info)["bad"], raw, names, today,
                       (oinfo if mine else info)["floor"], started, panel_when)
            if it:
                items.append(it)
        for du in list(x.get("extra") or []):
            it = _item("extra", du, con, info["bad"], raw, names, today, info["floor"], started, panel_when)
            if it:
                items.append(it)
        return dict(now=now, today=today.isoformat(), floor=info["floor"], owner_floor=oinfo["floor"], views=oinfo["views"],
                    staff_views=info["views"], floor_bad=dict(info["bad"]), on=on, on_since=on_since, on_by=on_by,
                    names=names, works=works, items=items, map_version=m.get("version"), extra_version=x.get("version"),
                    map_err=m.get("_err"), extra_err=x.get("_err"))
    finally:
        for c in (con, ocon, raw):
            if c is not None:
                c.close()


# ============================================================================================ the panel's documents
def seed_people():
    return [copy.deepcopy(p) for p in (SEED.PEOPLE if SEED is not None else [])]


def _seed_line_ids():
    return {ln["id"] for p in (SEED.PEOPLE if SEED is not None else []) for ln in p["lines"]}


def clean_doc(seed, body, first_on=None):
    """What a save of one person's panel may hold -- and nothing else. A line the seed knows keeps its working from the seed
    (never from the page); a line the owner added is a tap line ('own.<id>'). Returns the document as it is stored."""
    body = body if isinstance(body, dict) else {}
    known = {ln["id"]: ln for ln in seed["lines"]}
    out, seen = [], set()
    for ln in (body.get("lines") if isinstance(body.get("lines"), list) else [])[:LINES_MAX]:
        if not isinstance(ln, dict):
            continue
        lid = str(ln.get("id") or "")
        if lid in seen or not (lid in known or OWN_RE.match(lid)):
            continue
        seen.add(lid)
        when = ln.get("when") if ln.get("when") in WHEN_KEYS else (known[lid]["when"] if lid in known else "day")
        out.append(dict(id=lid, hi=clean(ln.get("hi"), TEXT_MAX), en=clean(ln.get("en"), TEXT_MAX), when=when, on=bool(ln.get("on"))))
    removed = []
    for ln in (body.get("removed") if isinstance(body.get("removed"), list) else [])[:LINES_MAX]:
        if not isinstance(ln, dict):
            continue
        lid = str(ln.get("id") or "")
        if lid in seen or not (lid in known or OWN_RE.match(lid)):
            continue
        seen.add(lid)
        when = ln.get("when") if ln.get("when") in WHEN_KEYS else (known[lid]["when"] if lid in known else "day")
        removed.append(dict(id=lid, hi=clean(ln.get("hi"), TEXT_MAX), en=clean(ln.get("en"), TEXT_MAX), when=when, on=False))
    return dict(on=bool(body.get("on")), note=clean(body.get("note"), NOTE_MAX), first_on=_iso_day(first_on), lines=out, removed=removed)


def _merge(seed, st):
    """One person's panel: the seed with what the owner has changed laid over it. His order, his wording, his switches;
    a seed line he has never seen (a later kit's) is added at the end, switched OFF and marked new."""
    p = copy.deepcopy(seed)
    p.setdefault("removed", [])
    p["first_on"] = None
    p["edited"] = False
    if not isinstance(st, dict):
        return p
    known = {ln["id"]: ln for ln in seed["lines"]}
    doc = clean_doc(seed, st, first_on=st.get("first_on"))
    lines, seen = [], set()
    for ln in doc["lines"] + doc["removed"]:
        base = copy.deepcopy(known.get(ln["id"]) or {"id": ln["id"], "opens": "", "own": True})
        base.update(hi=ln["hi"], en=ln["en"] or base.get("en") or "", when=ln["when"], on=ln["on"])
        ln["_full"] = base
        seen.add(ln["id"])
    for ln in doc["lines"]:
        lines.append(ln["_full"])
    for lid, ln in known.items():
        if lid not in seen:
            new = copy.deepcopy(ln)
            new.update(on=False, new=True)
            lines.append(new)
    p.update(on=doc["on"], note=doc["note"], first_on=doc["first_on"], lines=lines, removed=[ln["_full"] for ln in doc["removed"]], edited=True)
    return p


def cfg_load(con):
    """({key: person's panel}, meta) from the seed and the table aaj_cfg (which is not there until his first change).
    WHAT HE SWITCHED OFF STAYS OFF: the seed stands in only where he has saved nothing. If the table is there and cannot be
    read, EVERY list is off (meta['err'] says why); a person whose saved document is damaged is off (meta['bad'] names them)."""
    stored, err, bad, stamps = {}, None, [], {}
    try:
        there = con.execute("SELECT 1 FROM main.sqlite_master WHERE type='table' AND name='aaj_cfg'").fetchone() is not None
        if there:
            for r in con.execute("SELECT person, doc, edited_at FROM main.aaj_cfg"):
                stamps[r[0]] = r[2]                                    # a damaged row keeps its stamp: his next save repairs it
                try:
                    d = json.loads(r[1])
                    if not isinstance(d, dict):
                        raise ValueError("not a document")
                    stored[r[0]] = d
                except (TypeError, ValueError):
                    bad.append(r[0])
    except sqlite3.Error as e:
        stored, err = {}, "%s: %s" % (type(e).__name__, str(e)[:80])
    people = {}
    for seed in seed_people():
        p = _merge(seed, stored.get(seed["key"]))
        p["edited_at"] = stamps.get(seed["key"])
        if err or seed["key"] in bad:
            p["on"] = False
        people[seed["key"]] = p
    meta = stored.get("_meta") if isinstance(stored.get("_meta"), dict) else {}
    assigners = [] if (err or "_meta" in bad) else [a for a in (meta.get("assigners") or []) if isinstance(a, str) and NAME_RE.match(a)][:12]
    return people, {"assigners": assigners, "err": err, "bad": bad}


def person_key(login, people):
    """The list a login works: its own, or the one aaj_seed.LOGINS names (the desk's two people work Reception's)."""
    k = (SEED.LOGINS.get(login) if SEED is not None else None) or login
    return k if k in people else None


# ============================================================================================ one person's list
class Reader:
    """One request's reading: the staff's floored connection, each duty read at most once."""

    def __init__(self, db_path, now=None):
        self.now = now or dt.datetime.now()
        self.today = self.now.date()
        self.m, self.x = load_defs()
        self.names, self.works = people_of(self.m, self.x)
        self.con, self.info = connect(db_path, self.x, "staff")
        self.raw = None
        try:
            self.raw = connect(db_path, None, None)[0]
            self.on, self.on_since, self.on_by = staff_switch(self.con)
            self.first = _iso_day(first_on(self.con, self.on_since)) if self.on else None
            self.idx = {}
            if not self.x.get("_err"):
                for du in self.m.get("duties") or []:
                    self.idx[du.get("id")] = ("map", du)
            for du in self.x.get("extra") or []:
                self.idx[du.get("id")] = ("extra", du)
            self.cache = {}
            self.people, self.meta = cfg_load(self.con)
        except Exception:
            self.close()
            raise

    def close(self):
        for c in (self.con, self.raw):
            if c is not None:
                c.close()

    def item(self, iid):
        if iid not in self.cache:
            hit = self.idx.get(iid)
            self.cache[iid] = _item(hit[0], hit[1], self.con, self.info["bad"], self.raw, self.names, self.today, self.info["floor"], None) if hit else None
        return self.cache[iid]

    def defs_err(self):
        return self.m.get("_err") or self.x.get("_err") or self.meta.get("err")

    def started(self, doc):
        """The day this person's list first reached them: the later of the first switch-on and their own."""
        if not self.first:
            return None
        ds = [d for d in (self.first, _iso_day(doc.get("first_on"))) if d]
        return dt.date.fromisoformat(max(ds))


def line_state(rd, ln):
    """How one line of a panel stands right now: kind, due, err, since, held, door, how, tile, period, fetch. kind is 'job'
    (the database decides), 'tick' (a tap decides), 'fetch' (another app's door decides, asked by the page), or None (not
    readable). `held` is the day of work that is there but dated BEFORE THE FLOOR: such work is never shown to staff. A tap
    line's period is its GROUP's -- once a week, once a month, else once a day -- so moving it on the panel moves its rhythm."""
    lid = ln["id"]
    period = "week" if ln["when"] == "week" else ("month" if ln["when"] == "month" else "day")
    if ln.get("own"):
        return dict(kind="tick", due=None, err=None, since=None, held=None, door=None, how="", tile=None, period=period, fetch=None)
    spec = (SEED.ENGINE.get(lid) or {}) if SEED is not None else {}
    ids = list(spec.get("src") or [lid])
    its = [rd.item(s) for s in ids]
    missing = [s for s, i in zip(ids, its) if i is None]
    its = [i for i in its if i is not None]
    if not its:
        return dict(kind=None, due=None, err="not in the duty files: %s" % ", ".join(missing), since=None, held=None, door=None, how="", tile=None,
                    period=None, fetch=None)
    kind = its[0]["kind"]
    how = tidy(spec["how"] if "how" in spec else (its[0].get("how_hi") or ""))
    tile = its[0].get("tile")
    if kind == "sql":
        errs = ["%s: %s" % (i["id"], i["err"]) for i in its if i["err"]] + ["%s: not in the duty files" % s for s in missing]
        floor = rd.info["floor"] or ""
        no_hold = SEED.NO_HOLD if SEED is not None else ()

        def old(i):                                                    # there, and dated before the floor
            d = str(i.get("since") or "")[:10]
            return bool(DAY_RE.match(d) and floor and d < floor and i["id"] not in no_hold)
        there = [i for i in its if not i["err"] and i["n"] > 0]
        due = [i for i in there if not old(i)]
        helds = sorted(str(i["since"])[:10] for i in there if old(i))
        sinces = sorted(str(i["since"])[:10] for i in due if DAY_RE.match(str(i.get("since") or "")[:10]))
        since = sinces[0] if sinces else None
        door = _fill(spec.get("door"), since) if spec.get("door") else next((i["door"] for i in (due or its) if i.get("door")), None)
        return dict(kind="job", due=bool(due), err="; ".join(errs) or None, since=since, held=(helds[0] if helds else None), door=door, how=how,
                    tile=tile, period=None, fetch=None)
    if kind == "tick":
        return dict(kind="tick", due=None, err=None, since=None, held=None, door=its[0].get("door"), how=how, tile=tile, period=period, fetch=None)
    return dict(kind="fetch", due=None, err=None, since=None, held=None, door=its[0].get("door"), how=how, tile=tile, period=None, fetch=its[0]["fetch"])


def person_list(rd, doc, view_as=False):
    """One person's list, cut to their panel: the lines that are switched on and whose work is there. In the owner's view
    (view_as) a weekly or monthly tap line that has not begun yet is shown too, marked."""
    secs = {k: [] for k in WHEN_KEYS}
    unread, open_n, fetches = 0, 0, []
    started = rd.started(doc)
    for ln in doc["lines"]:
        text = clean(ln.get("hi"), TEXT_MAX)
        if not ln.get("on") or not text:
            continue
        st = line_state(rd, ln)
        if st["kind"] is None:
            unread += 1
            continue
        when = ln["when"] if ln["when"] in WHEN_KEYS else "day"
        if st["kind"] == "job":
            if st["err"]:
                unread += 1                                            # which line and why is the owner's to know (his panel says it)
            if not st["due"]:
                continue                                               # nothing there -- or only work from before the floor (held)
            secs[when].append(dict(id=ln["id"], kind="job", text=text, how=st["how"], door=st["door"], tile=st["tile"], done=None))
            open_n += 1
        elif st["kind"] == "tick":
            ps = period_start(st["period"], rd.today)
            live = st["period"] == "day" or started is None or ps >= started
            if not live and not view_as:
                continue
            key = period_key(st["period"], rd.today)
            done = tick_done(rd.con, ln["id"], key, rd.names)
            secs[when].append(dict(id=ln["id"], kind="tick", text=text, how=st["how"], door=st["door"], tile=st["tile"], done=done,
                                   key=key, period=st["period"], later=(not live)))
            open_n += 0 if (done or not live) else 1
        else:
            secs[when].append(dict(id=ln["id"], kind="fetch", text=text, how=st["how"], door=st["door"], tile=st["tile"], done=None, fetch=st["fetch"]))
            fetches.append(st["fetch"])
    return dict(sections=secs, unread=unread, open=open_n, fetches=fetches, has=bool(doc["lines"]))


# ============================================================================================ tasks
def _tasks(con, where, args, names, limit=200):
    try:
        rows = [dict(r) for r in con.execute("SELECT id, person, text, by_whom, at, due, state, state_at, state_by FROM main.aaj_task WHERE %s "
                                             "ORDER BY id DESC LIMIT %d" % (where, int(limit)), args)]
    except sqlite3.Error:
        return []                                                      # no task has ever been given: the table is not there yet
    if not rows:
        return []
    notes = {}
    try:
        q = "SELECT task_id, by_whom, at, kind, note FROM main.aaj_task_note WHERE task_id IN (%s) ORDER BY id" % ",".join("?" * len(rows))
        for r in con.execute(q, [t["id"] for t in rows]):
            notes.setdefault(r[0], []).append(dict(by=r[1], by_name=nm(names, r[1]), at=r[2], kind=r[3], note=r[4]))
    except sqlite3.Error:
        notes = {}
    for t in rows:
        t["by_name"] = nm(names, t["by_whom"])
        t["notes"] = notes.get(t["id"], [])
    return rows


def tasks_of_person(rd, key):
    """What a person sees: what is open, what they answered and he has not closed yet (kept two days), newest first."""
    keep = (rd.now - dt.timedelta(days=2)).replace(microsecond=0).isoformat(sep=" ")
    return _tasks(rd.con, "person = ? AND (state = 'open' OR (state IN ('done','cant') AND state_at >= ?))", (key, keep), rd.names)


def tasks_given(rd, login=None):
    """What a giver sees: everything not closed, and what was closed in the last seven days. login None = every giver's (the owner)."""
    keep = (rd.now - dt.timedelta(days=7)).replace(microsecond=0).isoformat(sep=" ")
    if login is None:
        return _tasks(rd.con, "(state <> 'closed' OR state_at >= ?)", (keep,), rd.names)
    return _tasks(rd.con, "by_whom = ? AND (state <> 'closed' OR state_at >= ?)", (login, keep), rd.names)


def line_words(lst, tasks_open, partial):
    """The home tile's line: words only."""
    if lst["open"] or tasks_open:
        return "Kaam baaki hai — kholiye"
    if partial:
        return "List adhoori hai — kholiye"
    if lst["fetches"]:
        return "Aaj ki list dekhiye"
    return "Sab ho gaya ✓"


# ============================================================================================ the service's part
_db = None
_require = None
_user = None

DENIED_HI = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Aaj ka kaam</title>"
             "<body style='font:17px/1.55 \"Segoe UI\",system-ui,sans-serif;margin:30px 18px;background:#dfe5e9;color:#14181c'>"
             "<h2 style='color:#14456e'>%s</h2><p><a href='/portal'>Wapas Clinic app par</a></p>")


def init(app, db_getter, require_fn, current_user_fn):
    global _db, _require, _user
    from flask import Blueprint, Response, jsonify, request            # noqa: PLC0415
    _db, _require, _user = db_getter, require_fn, current_user_fn
    bp = Blueprint("aaj_kaam", __name__)

    def _db_path():
        try:
            for r in _db().execute("PRAGMA database_list").fetchall():
                if r[1] == "main":
                    return r[2] or ""
        except Exception:                                              # noqa: BLE001
            pass
        return ""

    def _who():
        """(login, is_owner). The owner is the checker of unit 'packs' -- the console's own gate."""
        u = _user() or {}
        login = str(u.get("user") or "").strip().lower()
        owner, _err = _require("checker", unit="packs")
        return login, bool(owner)

    def _switch_now(p):
        con, _i = connect(p, None, None)
        try:
            return staff_switch(con)
        finally:
            con.close()

    def _body():
        """The JSON object of a POST, or None. A form post is not accepted: a page of another site cannot send JSON here."""
        b = request.get_json(silent=True) if request.is_json else None
        return b if isinstance(b, dict) else None

    def _nostore(r):
        r.headers["Cache-Control"] = "no-store"
        return r

    def _now():
        return dt.datetime.now().replace(microsecond=0)

    def _view():
        """(login, the person's key or None, view_as, reader, why not) -- one place decides who may see what, and decides it
        BEFORE the list is read: a staff login asking while the lists are off costs one read of one setting."""
        login, owner = _who()
        if not login:
            return None, None, False, None, ("not_signed_in", 401)
        p = _db_path()
        if not p:
            return None, None, False, None, ("no_database", 500)
        as_ = str(request.args.get("as") or "").strip().lower()
        if as_:
            if not owner:
                return None, None, False, None, ("owner_only", 403)
            if not NAME_RE.match(as_):
                return None, None, False, None, ("no_such_login", 404)
            rd = Reader(p)
            return as_, person_key(as_, rd.people), True, rd, None
        if owner:
            return login, None, False, None, ("owner_panel", 200)
        if not _switch_now(p)[0]:
            return login, None, False, None, ("off", 200)
        rd = Reader(p)
        key = person_key(login, rd.people)
        if (key is None or not rd.people[key]["on"]) and login not in rd.meta["assigners"]:
            rd.close()
            return login, None, False, None, ("off", 200)
        if key is not None and not rd.people[key]["on"]:
            key = None                                                 # a giver whose own list is off: the giving part only
        return login, key, False, rd, None

    def _send(name):
        try:
            with open(name, encoding="utf-8") as fh:
                html = fh.read()
        except OSError:
            return Response("Yeh page abhi nahin khul paaya. Thodi der mein dobara dekhiye.", status=500, mimetype="text/plain")
        return _nostore(Response(html, mimetype="text/html"))

    @bp.route("/finance/aaj")
    def aaj_page():
        _login, owner = _who()
        if owner and not request.args.get("as"):
            return _send(PANEL)
        return _send(PAGE)

    def _task_out(t, login, key, view_as, giver=False):
        mine = (t["person"] == key)
        return dict(id=t["id"], text=t["text"], by_name=t["by_name"], at=t["at"], due=t["due"], state=t["state"], state_at=t["state_at"],
                    person=t["person"], notes=[dict(by_name=n["by_name"], at=n["at"], kind=n["kind"], note=n["note"]) for n in t["notes"]],
                    can_answer=bool(mine and not view_as and t["state"] != "closed"),
                    can_close=bool(giver and not view_as and t["by_whom"] == login and t["state"] != "closed"))

    @bp.route("/finance/aaj/api/list")
    def aaj_list():
        who, key, view_as, rd, why = _view()
        if why:
            return _nostore(jsonify(ok=False, error=why[0])), why[1]
        try:
            doc = rd.people.get(key) if key else None
            lst = person_list(rd, doc, view_as) if doc else dict(sections={k: [] for k in WHEN_KEYS}, unread=0, open=0, fetches=[], has=False)
            person_on = bool(doc and doc["on"])
            shown = bool(doc) and (view_as or person_on)
            secs = []
            for k, title, _en in WHEN:
                rows = [dict(id=r["id"], kind=r["kind"], text=r["text"], how=r.get("how") or "", door=r.get("door"), tile=r.get("tile"),
                             done=r.get("done"), fetch=r.get("fetch"), later=bool(r.get("later")),
                             preview=bool(view_as and r["kind"] == "fetch"),
                             can_tick=bool(r["kind"] == "tick" and not r.get("done") and not r.get("later") and not view_as and rd.on and person_on))
                        for r in (lst["sections"][k] if shown else [])]
                if rows:
                    secs.append(dict(key=k, title=title, rows=rows))
            giver = (not view_as) and who in rd.meta["assigners"]
            tasks = [_task_out(t, who, key, view_as) for t in tasks_of_person(rd, key)] if (doc and shown) else []
            given = [_task_out(t, who, key, view_as, True) for t in tasks_given(rd, who)] if giver else []
            partial = bool(rd.defs_err() or lst["unread"])
            t_open = sum(1 for t in tasks if t["state"] == "open")
            return _nostore(jsonify(
                ok=True, version=VERSION, login=who, name=(doc["name"] if doc else nm(rd.names, who)), who=(doc.get("who") if doc else ""),
                view_as=view_as, on=rd.on, person_on=person_on, has=bool(doc) and lst["has"], as_of=rd.now.strftime("%H:%M"),
                day=dm(rd.today.isoformat()), today=rd.today.isoformat(), floor=dm(rd.info["floor"]) if rd.info["floor"] else "",
                open=lst["open"] + t_open, sections=secs, tasks=tasks, given=given, can_give=giver,
                people=[dict(key=p["key"], name=p["name"], on=p["on"]) for p in rd.people.values()] if giver else [],
                line=line_words(lst, t_open, partial), partial=partial))
        finally:
            rd.close()

    @bp.route("/finance/aaj/api/line")
    def aaj_line():
        who, key, view_as, rd, why = _view()
        if why:
            return _nostore(jsonify(ok=False, show=False, error=why[0])), (why[1] if why[1] != 200 else 200)
        try:
            doc = rd.people.get(key) if key else None
            if not doc:                                                # a giver with no list of their own: the page is theirs, the tile is not
                return _nostore(jsonify(ok=True, show=bool(not view_as and who in rd.meta["assigners"]), open=0, late=0, partial=False, fetch=[],
                                        text_hi="Kaam dijiye / dekhiye"))
            lst = person_list(rd, doc, view_as)
            t_open = sum(1 for t in tasks_of_person(rd, key) if t["state"] == "open")
            partial = bool(rd.defs_err() or lst["unread"])
            # `open`, `late` and `fetch` stay in the answer because the home page's script (portal.py, S487) reads them: zero and
            # empty, so that script draws the words below and no number.
            return _nostore(jsonify(ok=True, show=bool(rd.on and doc["on"] and not view_as), open=0, late=0, partial=partial, fetch=[],
                                    text_hi=line_words(lst, t_open, partial)))
        finally:
            rd.close()

    # ------------------------------------------------------------------------------------------------ writes
    def _task_row(con, tid):
        """One task by its number. The number must BE a number: not true, not 1.9, not a figure too long to be one."""
        if isinstance(tid, bool) or not isinstance(tid, int) or not (0 < tid < 2 ** 53):
            return None
        try:
            r = con.execute("SELECT id, person, text, by_whom, state FROM aaj_task WHERE id=?", (tid,)).fetchone()
        except sqlite3.Error:
            return None
        return dict(id=r[0], person=r[1], text=r[2], by_whom=r[3], state=r[4]) if r else None

    def _task_act(con, t, login, act, note, as_giver):
        """One answer on one task. A person: done / cant / note. Its giver (or the owner): close / reopen / reply.
        A closed task takes one thing only: being sent back, with a word. A reply keeps the task in the person's sight."""
        now = _now().isoformat(sep=" ")
        note = clean(note, NOTE_MAX)
        if as_giver:
            if act not in ("close", "reopen", "reply"):
                return "bad_request"
            if act in ("reply", "reopen") and not note:
                return "say_something"
            if t["state"] == "closed" and act != "reopen":
                return "closed"
            new = {"close": "closed", "reopen": "open"}.get(act)
        else:
            if act not in ("done", "cant", "note"):
                return "bad_request"
            if act in ("cant", "note") and not note:
                return "say_something"
            if t["state"] == "closed":
                return "closed"
            new = {"done": "done", "cant": "cant"}.get(act)
        con.execute(NOTE_SQL)
        con.execute("INSERT INTO aaj_task_note (task_id, by_whom, at, kind, note) VALUES (?,?,?,?,?)", (t["id"], login, now, act, note))
        if new:
            con.execute("UPDATE aaj_task SET state=?, state_at=?, state_by=? WHERE id=?", (new, now, login, t["id"]))
        elif act == "reply":
            con.execute("UPDATE aaj_task SET state_at=? WHERE id=?", (now, t["id"]))
        con.commit()
        return None

    def _task_add(con, people, to, texts, due, login):
        """One task per person and per line of text -- only to a person whose list is switched on (nobody else would see it).
        Returns (how many were made, why not)."""
        to = [k for k in (to if isinstance(to, list) else []) if isinstance(k, str) and k in people and people[k]["on"]]
        texts = [t for t in (clean(x, TEXT_MAX) for x in (texts if isinstance(texts, list) else [])) if t][:TASKS_AT_ONCE]
        if not to:
            return 0, "no_person"
        if not texts:
            return 0, "say_something"
        due = _iso_day(due) or ""
        now = _now().isoformat(sep=" ")
        con.execute(TASK_SQL)
        con.execute(NOTE_SQL)
        n = 0
        for k in dict.fromkeys(to):
            for t in texts:
                con.execute("INSERT INTO aaj_task (person, text, by_whom, at, due, state, state_at, state_by) VALUES (?,?,?,?,?,'open',?,?)",
                            (k, t, login, now, due, now, login))
                n += 1
        con.commit()
        return n, None

    WHY_HI = {"bad_request": "Yeh nahin ho paaya. Dobara kijiye.", "say_something": "Pehle kuch likhiye.", "closed": "Yeh kaam band ho chuka hai.",
              "no_person": "Kisko dena hai, chuniye.", "not_yours": "Yeh kaam aapki list mein nahin hai."}

    @bp.route("/finance/aaj/api/tick", methods=["POST"])
    def aaj_tick():
        login, owner = _who()
        if not login:
            return jsonify(ok=False, error="not_signed_in"), 401
        p = _db_path()
        if not p:
            return jsonify(ok=False, error="no_database"), 500
        if owner or not _switch_now(p)[0]:
            return jsonify(ok=False, error="off", message="Yeh list abhi staff ke liye band hai."), 403
        body = _body()
        if body is None:
            return jsonify(ok=False, error="bad_request", message="Tick nahin lag paaya. Dobara kijiye."), 400
        rd = Reader(p)
        try:
            key = person_key(login, rd.people)
            doc = rd.people.get(key) if key else None
            if doc and not doc["on"]:
                doc, key = None, None
            giver = login in rd.meta["assigners"]
            if not doc and not giver:
                return jsonify(ok=False, error="off", message="Yeh list abhi staff ke liye band hai."), 403
            con = _db()
            if isinstance(body.get("give"), dict):                     # a login he named gives a task
                if not giver:
                    return jsonify(ok=False, error="not_yours", message="Aap kaam nahin de sakte."), 403
                g = body["give"]
                n, why = _task_add(con, rd.people, g.get("to"), [g.get("text")], g.get("due"), login)
                if why:
                    return jsonify(ok=False, error=why, message=WHY_HI.get(why, WHY_HI["bad_request"])), 400
                return _nostore(jsonify(ok=True, made=n))
            if body.get("task") is not None:                           # an answer on a task
                tid = body.get("task")
                t = _task_row(con, tid)
                act = str(body.get("act") or "")
                as_giver = act in ("close", "reopen", "reply")
                if not t or (as_giver and not (giver and t["by_whom"] == login)) or (not as_giver and (not key or t["person"] != key)):
                    return jsonify(ok=False, error="not_yours", message=WHY_HI["not_yours"]), 404
                why = _task_act(con, t, login, act, body.get("note"), as_giver)
                if why:
                    return jsonify(ok=False, error=why, message=WHY_HI.get(why, WHY_HI["bad_request"])), 400
                return _nostore(jsonify(ok=True, task=tid))
            did = str(body.get("id") or "")
            hit = None
            if doc:
                lst = person_list(rd, doc, False)
                hit = next((r for k in WHEN_KEYS for r in lst["sections"][k] if r["id"] == did and r["kind"] == "tick" and not r.get("later")), None)
            if not hit:
                return jsonify(ok=False, error="not_yours", message=WHY_HI["not_yours"]), 404
            con.execute(TICK_SQL)
            now = _now().isoformat(sep=" ")
            con.execute("INSERT OR IGNORE INTO duty_tick (duty_id, period_key, by_whom, at) VALUES (?,?,?,?)", (hit["id"], hit["key"], login, now))
            con.commit()
            r = con.execute("SELECT by_whom, at FROM duty_tick WHERE duty_id=? AND period_key=?", (hit["id"], hit["key"])).fetchone()
            return _nostore(jsonify(ok=True, id=hit["id"], by=r[0], by_name=nm(rd.names, r[0]), at=r[1], yours=(r[0] == login)))
        finally:
            rd.close()

    def _put_cfg(con, person, doc, iso, login):
        cur = con.execute("UPDATE aaj_cfg SET doc=?, edited_at=?, edited_by=? WHERE person=?", (doc, iso, login, person))
        if cur.rowcount == 0:
            con.execute("INSERT INTO aaj_cfg (person, doc, edited_at, edited_by) VALUES (?,?,?,?)", (person, doc, iso, login))

    def _put_setting(con, key, val, note):
        cur = con.execute("UPDATE setting SET value=? WHERE key=?", (val, key))
        if cur.rowcount == 0:
            con.execute("INSERT INTO setting (key, value, note) VALUES (?, ?, ?)", (key, val, note))

    def _panel(p):
        """Everything the owner's panel shows, read now."""
        rd = Reader(p)
        try:
            raw = connect(p, None, None)[0]
            try:
                sept, floor = [], rd.info["floor"] or staff_floor(rd.con)
                for s in (SEED.SEPT if SEED is not None else []):
                    if s.get("duty"):
                        hit = rd.idx.get(s["duty"])
                        sql = (hit[1].get("due_sql") if hit else None)
                    else:
                        sql = str(s.get("sql") or "").replace("{floor}", floor)
                    n, since, err = _one(raw, sql)
                    sept.append(dict(id=s["id"], text=s["en"], n=n, since=dm(since) if since else "", err=err, door=_door(s.get("door")), tile=s.get("tile")))
            finally:
                raw.close()
            people = []
            for doc in rd.people.values():
                d = dict(key=doc["key"], pos=doc["pos"], name=doc["name"], who=doc["who"], step=doc["step"], step_label=doc["step_label"],
                         on=doc["on"], note=doc["note"], edited=doc["edited"], edited_at=doc.get("edited_at"), first_on=doc.get("first_on"),
                         view_as=((SEED.VIEW_AS.get(doc["key"]) if SEED is not None else None) or doc["key"]), lines=[], removed=[])
                for part in ("lines", "removed"):
                    for ln in doc[part]:
                        st = line_state(rd, ln)
                        d[part].append(dict(id=ln["id"], hi=ln["hi"], en=ln.get("en") or "", when=ln["when"], on=bool(ln["on"]), opens=ln.get("opens") or "",
                                            why=ln.get("why") or "", own=bool(ln.get("own")), new=bool(ln.get("new")), kind=st["kind"], due=st["due"], how=st["how"],
                                            err=st["err"], door=st["door"], held=(dm(st["held"]) if st["held"] else "")))
                people.append(d)
            tasks = [dict(id=t["id"], person=t["person"], text=t["text"], by_name=t["by_name"], at=t["at"], due=t["due"], state=t["state"],
                          state_at=t["state_at"], notes=[dict(by_name=n["by_name"], at=n["at"], kind=n["kind"], note=n["note"]) for n in t["notes"]])
                     for t in tasks_given(rd, None)]
            return dict(version=VERSION, seed=(SEED.VERSION if SEED is not None else None), seed_err=SEED_ERR, defs_err=rd.defs_err(),
                        floor=rd.info["floor"], floor_words=dm(rd.info["floor"]) if rd.info["floor"] else "", floor_bad=rd.info["bad"],
                        today=rd.today.isoformat(), as_of=rd.now.strftime("%H:%M"), first_on=rd.first, people=people, sept=sept, tasks=tasks,
                        assigners=rd.meta["assigners"], cfg_err=rd.meta.get("err"), cfg_bad=rd.meta.get("bad") or [],
                        when=[dict(key=k, hi=h, en=e) for k, h, e in WHEN])
        finally:
            rd.close()

    @bp.route("/finance/aaj/api/switch", methods=["GET", "POST"])
    def aaj_switch():
        login, owner = _who()
        if not login:
            return jsonify(ok=False, error="not_signed_in"), 401
        if not owner:
            return jsonify(ok=False, error="owner_only"), 403
        p = _db_path()
        made = saved_at = None
        if request.method == "POST":
            body = _body()
            if body is None:
                return jsonify(ok=False, error="bad_request"), 400
            con = _db()
            iso = _now().isoformat()
            op = body.get("op")
            if op is None:                                             # the switch above them all (the console's button sends this)
                if body.get("on") not in (True, False, 0, 1):          # on or off must be SAID: an empty post changes nothing
                    return jsonify(ok=False, error="bad_request"), 400
                want = bool(body.get("on"))
                _put_setting(con, "aaj.staff_on", ("%s|%s" % (iso, login)) if want else "",
                             "S487: the staff's Aaj ka kaam lists -- '<since>|<by>' = on, empty = off (the owner's tap)")
                if want and not con.execute("SELECT 1 FROM setting WHERE key='aaj.staff_first_on' AND COALESCE(value,'') <> ''").fetchone():
                    _put_setting(con, "aaj.staff_first_on", iso, "S487: when the lists were FIRST turned on -- a weekly / monthly tap line begins "
                                                                 "with the first week / month that starts on or after this day")
                con.commit()
            elif op == "person":                                       # one person's panel, saved whole
                seed = next((s for s in seed_people() if s["key"] == body.get("key")), None)
                if seed is None or not isinstance(body.get("doc"), dict):
                    return jsonify(ok=False, error="bad_request"), 400
                con.execute(CFG_SQL)
                r = con.execute("SELECT doc, edited_at FROM aaj_cfg WHERE person=?", (seed["key"],)).fetchone()
                if (r[1] if r else None) != body.get("base"):          # saved from another screen since this one loaded it
                    con.commit()
                    return jsonify(ok=False, error="stale", edited_at=(r[1] if r else None)), 409
                try:
                    old = json.loads(r[0]) if r else {}
                except (TypeError, ValueError):
                    old = {}
                old = old if isinstance(old, dict) else {}
                # THE PERSON'S FIRST DAY ON. A person who was on from the start has none of their own (the lists' first day is
                # theirs). It is stamped the day he switches ON a person who was off, and kept from then; switching off a
                # person who never had one stamps the lists' own first day, so that off-and-on again starts nothing over.
                was_on = bool(old.get("on")) if r else bool(seed["on"])
                first = _iso_day(old.get("first_on"))
                want = bool(body["doc"].get("on"))
                if not first and want and not was_on:
                    first = iso[:10]
                elif not first and was_on and not want:
                    fr = con.execute("SELECT value FROM setting WHERE key='aaj.staff_first_on'").fetchone()
                    first = _iso_day(fr[0] if fr else None)
                doc = clean_doc(seed, body["doc"], first_on=first)
                saved_at = dt.datetime.now().isoformat()               # to the microsecond: it is also this save's own mark (`base`)
                _put_cfg(con, seed["key"], json.dumps(doc, ensure_ascii=False), saved_at, login)
                con.commit()
            elif op == "assigners":                                    # the logins that may give tasks
                logins = [a for a in (clean(x, 40).lower() for x in (body.get("logins") if isinstance(body.get("logins"), list) else []))
                          if NAME_RE.match(a)][:12]
                con.execute(CFG_SQL)
                _put_cfg(con, "_meta", json.dumps({"assigners": list(dict.fromkeys(logins))}), iso, login)
                con.commit()
            elif op == "task_add":
                rd = Reader(p)
                try:
                    people = rd.people
                finally:
                    rd.close()
                made, why = _task_add(con, people, body.get("to"), body.get("items"), body.get("due"), login)
                if why:
                    return jsonify(ok=False, error=why), 400
            elif op == "task":
                t = _task_row(con, body.get("id"))
                if not t:
                    return jsonify(ok=False, error="no_such_task"), 404
                why = _task_act(con, t, login, str(body.get("act") or ""), body.get("note"), True)
                if why:
                    return jsonify(ok=False, error=why), 400
            else:
                return jsonify(ok=False, error="bad_request"), 400
        con, _i = connect(p, None, None)
        try:
            on, since, by = staff_switch(con)
        finally:
            con.close()
        out = dict(ok=True, on=on, since=since, by=by)
        if made is not None:
            out["made"] = made
        if saved_at is not None:
            out["edited_at"] = saved_at
        if request.args.get("panel"):
            out["panel"] = _panel(p)
        return _nostore(jsonify(**out))

    app.register_blueprint(bp)


if __name__ == "__main__":
    raise SystemExit("aaj_kaam.py is mounted by finance_app.py")
