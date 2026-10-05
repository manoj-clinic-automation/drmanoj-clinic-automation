#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aaj_kaam.py -- S487_AAJ_KA_KAAM (parent; session 294, 05-Oct-2026; D679). The staff's own daily list, 'Aaj ka kaam'.

The owner, 04/05-Oct-2026: "Currently there is no flow for these daily tasks in their apps, which should be prominent";
and on starting the build: "dont populate old stale data, use from current month only, and the leftovers of September".

WHAT A LIST IS. For one login: every duty of the duty map (claude_code_briefs/DUTY_MAP.json, D648) that is theirs, by the
map's OWN due_sql -- how many are open and since when -- with the map's own Hinglish line and its own door; plus the
parent's lines of aaj_duties.json that the map does not hold: a few more SELECTs (yesterday's Docterz exports), counts that
live behind another app's door (the staff register -- the page reads that door with the person's own login), and lines
with no state anywhere, which the person taps 'Ho gaya' (who and when are kept).

THE FLOOR (D679). Nothing before `from` (01-Sep-2026; setting duties.from) is shown or counted. It is laid UNDER the SQL:
this module's own read-only connection carries TEMP views that shadow the dated tables named in aaj_duties.json, so the
map's SQL runs unedited and sees only rows on or after the floor. A second plain connection gives the unfloored count, so
the owner's console can say how many older items are not shown.

HOW IT READS AND WRITES. Reading is plain SELECTs through a mode=ro connection to the database file -- no module function
is called, nothing can be written through it. Two writes exist, each through the service's own connection:
  a tap on a tick line -> one row in duty_tick (the table is made on the first tap; one row per duty and period, the first
  tap stands);  the owner's switch -> the setting aaj.staff_on (and, the first time, aaj.staff_first_on).
Both POST doors take a JSON body only. A staff login asking while the lists are off costs one read of one setting.
A LIST THAT IS NOT WHOLE SAYS SO: a line that cannot be read, a duty map or a duties file that cannot be read -- the page
shows a banner and neither it nor the home tile ever says 'Sab ho gaya'. Without the duties file there is no floor, and then
no line of the map is shown at all.
Until the owner turns the lists on, a staff login sees nothing (no tile, no list); the owner sees each person's list as
they will see it (/finance/aaj?as=<login>), where taps are off.

Doors (a signed-in login reaches its own list; the paths are in finance_app.IDENTITY_ONLY_PATHS):
  GET  /finance/aaj                 the page (aaj_kaam.html)
  GET  /finance/aaj/api/list        the list            (?as=<login> for the owner)
  GET  /finance/aaj/api/line        the home tile's line
  POST /finance/aaj/api/tick        id=<duty id>        (the person's own tick lines only)
  GET/POST /finance/aaj/api/switch  the staff switch    (POST: the owner only)
"""
import datetime as dt
import json
import os
import re
import sqlite3

VERSION = "S487 1.0"
FIN = os.path.dirname(os.path.abspath(__file__))


def _env(name, default):
    return os.environ.get(name) or default


DUTY_MAP = _env("DUTY_MAP_JSON", "/root/deploy/repo/claude_code_briefs/DUTY_MAP.json")
EXTRA = _env("AAJ_DUTIES_JSON", os.path.join(FIN, "aaj_duties.json"))
PAGE = os.path.join(FIN, "aaj_kaam.html")
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
GROUPS = (("first", "Sabse pehle", "First"), ("open", "Aaj ka kaam", "Open"), ("night", "Raat ko", "Tonight"),
          ("week", "Is hafte", "This week"), ("month", "Is mahine", "This month"))
NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
TICK_SQL = ("CREATE TABLE IF NOT EXISTS duty_tick (id INTEGER PRIMARY KEY, duty_id TEXT NOT NULL, period_key TEXT NOT NULL, "
            "by_whom TEXT NOT NULL, at TEXT NOT NULL, UNIQUE(duty_id, period_key))")


# ============================================================================================ the engine (read-only)
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
    return m, x


def floor_date(con, x):
    """The floor: the setting duties.from when it is a date, else the file's 'from', else 01-Sep-2026."""
    d = None
    try:
        r = con.execute("SELECT value FROM main.setting WHERE key='duties.from'").fetchone()
        d = (r[0] if r else None) or None
    except sqlite3.Error:
        d = None
    for cand in (d, x.get("from"), "2026-09-01"):
        try:
            return dt.date.fromisoformat(str(cand)[:10]).isoformat()
        except (TypeError, ValueError):
            continue
    return "2026-09-01"


def connect(db_path, x=None, floored=True):
    """A read-only connection to the database file. With floored=True it carries the TEMP views of the floor."""
    con = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    info = {"floor": None, "views": {}}
    if floored and x is not None:
        con.execute("PRAGMA temp_store=MEMORY")
        info["floor"] = floor_date(con, x)
        have = {r[0] for r in con.execute("SELECT name FROM main.sqlite_master WHERE type='table'")}
        for t, f in sorted((x.get("floor") or {}).items()):
            col = str((f or {}).get("col") or "")
            if not (NAME_RE.match(t) and NAME_RE.match(col)) or t not in have:
                continue
            d = info["floor"]
            fo = (f or {}).get("first_of")
            if fo and len(fo) == 2 and NAME_RE.match(str(fo[0])) and NAME_RE.match(str(fo[1])) and fo[0] in have:
                try:
                    first = con.execute("SELECT MIN(%s) FROM main.%s" % (fo[1], fo[0])).fetchone()[0]
                    if first and str(first)[:10] > d:
                        d = dt.date.fromisoformat(str(first)[:10]).isoformat()
                except (sqlite3.Error, ValueError):
                    pass
            con.execute("CREATE TEMP VIEW %s AS SELECT * FROM main.%s WHERE %s >= '%s'" % (t, t, col, d))
            info["views"][t] = d
    return con, info


def _door(v):
    """A door is a path on this site ('/...'), or nothing: what the files say is never trusted as a link."""
    v = str(v or "")
    return v if re.match(r"^/[A-Za-z0-9_~.-]", v) and "\\" not in v else None


def first_on(con, since):
    """The day the lists were FIRST turned on (setting aaj.staff_first_on), else `since`: turning them off and on again must
    not make this week's and this month's lines start over (review 8)."""
    try:
        r = con.execute("SELECT value FROM main.setting WHERE key='aaj.staff_first_on'").fetchone()
        v = str((r[0] if r else "") or "")
        dt.datetime.fromisoformat(v)
        return v
    except (sqlite3.Error, ValueError):
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
    try:
        r = con.execute("SELECT value FROM main.setting WHERE key='aaj.staff_on'").fetchone()
    except sqlite3.Error:
        r = None
    v = str((r[0] if r else "") or "")
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


def build_all(db_path, now=None, with_raw=True):
    """Every duty, evaluated once on the floor (and, for the owner's console, once without it: with_raw). Returns the pieces
    every list is cut from. WITHOUT THE DUTIES FILE THERE IS NO FLOOR, so no line of the map is evaluated at all: a list that
    cannot be floored is not shown as if it were one."""
    now = now or dt.datetime.now()
    today = now.date()
    m, x = load_defs()
    names, works = people_of(m, x)
    con, info = connect(db_path, x, floored=True)
    raw = connect(db_path, None, floored=False)[0] if with_raw else None
    floor = info["floor"]
    try:
        on, on_since, on_by = staff_switch(con)
        started = dt.date.fromisoformat(first_on(con, on_since)[:10]) if on else None
        items = []
        for du in ([] if x.get("_err") else list(m.get("duties") or [])):
            n, since, err = _one(con, du.get("due_sql"))
            n_all = _one(raw, du.get("due_sql"))[0] if raw is not None else n
            items.append(_sql_item(du, n, since, err, n_all, names, today, floor, kind="sql", group="open", from_map=True))
        for du in list(x.get("extra") or []):
            kind = du.get("kind")
            if kind == "sql":
                n, since, err = _one(con, du.get("sql"))
                n_all = _one(raw, du.get("sql"))[0] if raw is not None else n
                items.append(_sql_item(du, n, since, err, n_all, names, today, floor, kind="sql", group=du.get("group") or "open", from_map=False))
            elif kind == "tick":
                period = du.get("period") if du.get("period") in ("day", "week", "month") else "day"
                key = period_key(period, today)
                done = None
                try:
                    r = con.execute("SELECT by_whom, at FROM main.duty_tick WHERE duty_id=? AND period_key=?", (du.get("id"), key)).fetchone()
                    if r:
                        done = {"by": r[0], "at": r[1], "by_name": str(names.get(r[0], str(r[0]).title()))}
                except sqlite3.Error:
                    done = None                                        # no tap has ever been made: the table is not there yet
                ps = period_start(period, today)
                # NOTHING STALE: a weekly or monthly line begins with the first week / month that STARTS on or after the day
                # the owner turned the lists on (a daily line begins that day). Before the switch every line is shown, for his eye.
                live = (started is None) or (ps >= started) or period == "day"
                late_from = {"day": None, "week": ps + dt.timedelta(days=1), "month": ps + dt.timedelta(days=3)}[period]
                late = bool(done is None and started is not None and live and late_from is not None and today >= late_from)
                items.append(dict(id=du.get("id"), person=du.get("person"), also=list(du.get("also") or []), kind="tick", group=du.get("group") or "open",
                                  period=period, key=key, live=live, done=done, n=0 if done else 1, n_all=0, since=ps.isoformat(), days=None, late=late,
                                  soft=False, err=None, hi=tidy(du.get("hi") or ""), en=tidy(du.get("en") or du.get("hi") or ""),
                                  how_hi=tidy(du.get("how_hi") or ""), door=_door(du.get("door")), tile=du.get("tile"), from_map=False,
                                  ok_hi="", fact=False, behind=False))
            elif kind == "fetch":
                f = du.get("fetch") or {}
                if not _door(f.get("url")):
                    continue                                           # a count can only be read from a door of this site
                items.append(dict(id=du.get("id"), person=du.get("person"), also=list(du.get("also") or []), kind="fetch", group=du.get("group") or "open",
                                  n=0, n_all=0, since=None, days=None, late=False, soft=False, err=None, hi=tidy(du.get("hi") or ""),
                                  en=tidy(du.get("en") or ""), how_hi=tidy(du.get("how_hi") or ""), door=_door(du.get("door")), tile=du.get("tile"),
                                  fetch={"url": str(f.get("url") or ""), "field": str(f.get("field") or ""), "only_if": f.get("only_if"),
                                         "text_field": f.get("text_field")}, from_map=False, ok_hi="", fact=False, behind=False))
        return dict(now=now, today=today.isoformat(), floor=info["floor"], views=info["views"], on=on, on_since=on_since, on_by=on_by,
                    names=names, works=works, items=items, map_version=m.get("version"), extra_version=x.get("version"),
                    map_err=m.get("_err"), extra_err=x.get("_err"))
    finally:
        con.close()
        if raw is not None:
            raw.close()


def _sql_item(du, n, since, err, n_all, names, today, floor, kind, group, from_map):
    """One counted line. BEHIND THE FLOOR: when its oldest item is older than the floor (its table is not one the floor is laid
    under), the count and the day mix old with new -- so the list says the line WITHOUT a count, a day or a 'late', and the
    owner's line says that older items are in it. Nothing stale is counted to a person as theirs."""
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


def list_for(allp, login):
    """One login's list, cut from build_all(): its own queues and the lines that name it as well."""
    qs = queues(login, allp["works"])
    mine = [i for i in allp["items"] if i["person"] in qs or login in (i.get("also") or [])]
    out = {"first": [], "open": [], "night": [], "week": [], "month": [], "clear": []}
    unread = 0
    for i in mine:
        if i["kind"] == "sql":
            if i["err"]:
                unread += 1                                            # which line and why is the owner's to know; that the list is
                continue                                               # NOT WHOLE is the person's -- it never says 'all done' then
            (out[i["group"] if i["group"] in out else "open"] if i["n"] > 0 else out["clear"]).append(i)
        elif i["kind"] == "tick":
            if not i["live"]:
                continue
            out[i["group"] if i["group"] in out else "open"].append(i)
        else:
            out[i["group"] if i["group"] in out else "open"].append(i)
    for k in ("first", "open", "week", "month"):
        out[k].sort(key=lambda i: (1 if (i["kind"] == "tick" and i.get("done")) else 0, 0 if i["late"] else 1, -(i["days"] or 0)))
    todo = [i for k in ("first", "open", "night", "week", "month") for i in out[k]
            if (i["kind"] == "sql" and i["n"] > 0) or (i["kind"] == "tick" and not i.get("done"))]
    return dict(login=login, name=str(allp["names"].get(login, login)), queues=qs, sections=out, open=len(todo),
                late=sum(1 for i in todo if i["late"]), has=bool(mine), unread=unread)


def line_hi(lst):
    """The home tile's line."""
    if not lst["open"]:
        return "Sab ho gaya ✓"
    t = "%d kaam baaki" % lst["open"]
    if lst["late"]:
        t += " · %d late" % lst["late"]
    return t


def item_hi(i):
    """A line as the person reads it."""
    if i["kind"] == "sql":
        t = i["hi"]
        if i.get("behind"):
            return t                                                   # old and new mixed: no count, no day
        if i["n"] > 0 and i.get("single"):                             # one thing, done or not: its day, no count
            if i["since"] and not i.get("soft"):
                t += " (%s)" % dm(i["since"])
        elif i["n"] > 0:
            t += " — %d baaki" % i["n"]
            if i["since"] and not i.get("soft"):
                t += " (%s se)" % dm(i["since"])
        return t
    return i["hi"]


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
        con, _i = connect(p, None, floored=False)
        try:
            return staff_switch(con)
        finally:
            con.close()

    def _partial(allp, lst):
        return bool(allp.get("map_err") or allp.get("extra_err") or lst.get("unread"))

    def _body():
        """The JSON object of a POST, or None. A form post is not accepted: a page of another site cannot send JSON here."""
        b = request.get_json(silent=True) if request.is_json else None
        return b if isinstance(b, dict) else None

    def _view():
        """(the login whose list is asked for, view_as, allp, why not) -- one place decides who may see what, and decides it
        BEFORE the list is built: a staff login asking while the lists are off costs one read of one setting."""
        login, owner = _who()
        if not login:
            return None, False, None, ("not_signed_in", 401)
        p = _db_path()
        if not p:
            return None, False, None, ("no_database", 500)
        as_ = str(request.args.get("as") or "").strip().lower()
        if as_:
            if not owner:
                return None, False, None, ("owner_only", 403)
            if not NAME_RE.match(as_):
                return None, False, None, ("no_such_login", 404)
            return as_, True, build_all(p, with_raw=False), None
        if not owner and not _switch_now(p)[0]:
            return login, False, None, ("off", 200)
        return login, False, build_all(p, with_raw=False), None

    def _nostore(r):
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route("/finance/aaj")
    def aaj_page():
        login, owner = _who()
        if owner and not request.args.get("as"):
            return Response(DENIED_HI % "Dr Manoj: staff lists open from your console (each person's line has its own list)."
                            + "<p><a href='/finance/console'>Open the console</a></p>", status=200, mimetype="text/html")
        try:
            with open(PAGE, encoding="utf-8") as fh:
                html = fh.read()
        except OSError:
            return Response("Yeh page abhi nahin khul paaya. Thodi der mein dobara dekhiye.", status=500, mimetype="text/plain")
        return _nostore(Response(html, mimetype="text/html"))

    @bp.route("/finance/aaj/api/list")
    def aaj_list():
        who, view_as, allp, why = _view()
        if why:
            return _nostore(jsonify(ok=False, error=why[0])), why[1]
        lst = list_for(allp, who)
        secs = []
        for key, title_hi, _en in GROUPS:
            rows = [dict(id=i["id"], kind=i["kind"], text=item_hi(i), how=i.get("how_hi") or "", late=bool(i["late"]), soft=bool(i.get("soft")),
                         door=i.get("door"), tile=i.get("tile"), done=i.get("done"), fetch=i.get("fetch"), preview=bool(view_as and i["kind"] == "fetch"),
                         can_tick=bool(i["kind"] == "tick" and not i.get("done") and not view_as and allp["on"]))
                    for i in lst["sections"][key]]
            if rows:
                secs.append(dict(key=key, title=title_hi, rows=rows))
        clear = [dict(id=i["id"], text=i.get("ok_hi") or i["hi"], tile=i.get("tile")) for i in lst["sections"]["clear"]]
        return _nostore(jsonify(ok=True, version=VERSION, login=who, name=lst["name"], view_as=view_as, on=allp["on"], has=lst["has"],
                                as_of=allp["now"].strftime("%H:%M"), day=dm(allp["today"]), open=lst["open"], late=lst["late"],
                                line=line_hi(lst), sections=secs, clear=clear, today=allp["today"], partial=_partial(allp, lst)))

    @bp.route("/finance/aaj/api/line")
    def aaj_line():
        who, view_as, allp, why = _view()
        if why:
            return _nostore(jsonify(ok=False, show=False, error=why[0])), (why[1] if why[1] != 200 else 200)
        lst = list_for(allp, who)
        _login, owner = _who()
        partial = _partial(allp, lst)                                  # a list that could not be read whole never says 'all done'
        fetches = [i["fetch"] for k in ("first", "open", "night", "week", "month") for i in lst["sections"][k] if i["kind"] == "fetch"]
        return _nostore(jsonify(ok=True, show=bool(allp["on"] and lst["has"] and not owner), open=lst["open"], late=lst["late"], partial=partial, fetch=fetches,
                                text_hi=("List adhoori hai — kholkar dekhiye" if (partial and not lst["open"]) else line_hi(lst))))

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
        did = str(body.get("id") or "")
        allp = build_all(p, with_raw=False)
        lst = list_for(allp, login)
        hit = [i for k in ("first", "open", "night", "week", "month") for i in lst["sections"][k] if i["id"] == did and i["kind"] == "tick"]
        if not hit:
            return jsonify(ok=False, error="not_yours", message="Yeh kaam aapki list mein nahin hai."), 404
        i = hit[0]
        con = _db()
        con.execute(TICK_SQL)
        now = dt.datetime.now().replace(microsecond=0).isoformat(sep=" ")
        con.execute("INSERT OR IGNORE INTO duty_tick (duty_id, period_key, by_whom, at) VALUES (?,?,?,?)", (i["id"], i["key"], login, now))
        con.commit()
        r = con.execute("SELECT by_whom, at FROM duty_tick WHERE duty_id=? AND period_key=?", (i["id"], i["key"])).fetchone()
        return _nostore(jsonify(ok=True, id=i["id"], by=r[0], by_name=str(allp["names"].get(r[0], str(r[0]).title())), at=r[1], yours=(r[0] == login)))

    @bp.route("/finance/aaj/api/switch", methods=["GET", "POST"])
    def aaj_switch():
        login, owner = _who()
        if not login:
            return jsonify(ok=False, error="not_signed_in"), 401
        if request.method == "POST":
            if not owner:
                return jsonify(ok=False, error="owner_only"), 403
            body = _body()
            if body is None or body.get("on") not in (True, False, 0, 1):      # on or off must be SAID: an empty post changes nothing
                return jsonify(ok=False, error="bad_request"), 400
            want = bool(body.get("on"))
            con = _db()
            iso = dt.datetime.now().replace(microsecond=0).isoformat()

            def put(key, val, note):
                cur = con.execute("UPDATE setting SET value=? WHERE key=?", (val, key))
                if cur.rowcount == 0:
                    con.execute("INSERT INTO setting (key, value, note) VALUES (?, ?, ?)", (key, val, note))
            put("aaj.staff_on", ("%s|%s" % (iso, login)) if want else "",
                "S487: the staff's Aaj ka kaam lists -- '<since>|<by>' = on, empty = off (the owner's tap on his console)")
            if want and not con.execute("SELECT 1 FROM setting WHERE key='aaj.staff_first_on' AND COALESCE(value,'') <> ''").fetchone():
                put("aaj.staff_first_on", iso, "S487: when the lists were FIRST turned on -- a weekly / monthly tap line begins with the "
                                               "first week / month that starts on or after this day; off-and-on again does not move it")
            con.commit()
        if not owner:
            return jsonify(ok=False, error="owner_only"), 403
        p = _db_path()
        con, _i = connect(p, None, floored=False)
        try:
            on, since, by = staff_switch(con)
        finally:
            con.close()
        return _nostore(jsonify(ok=True, on=on, since=since, by=by))

    app.register_blueprint(bp)


if __name__ == "__main__":
    raise SystemExit("aaj_kaam.py is mounted by finance_app.py")
