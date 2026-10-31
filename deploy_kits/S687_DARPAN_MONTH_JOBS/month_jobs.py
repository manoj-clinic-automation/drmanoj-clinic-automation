#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""month_jobs.py -- kit S687_DARPAN_MONTH_JOBS (31-Oct-2026, the parent, session 372). Darpan's monthly jobs.

THE OWNER'S RULINGS (31-Oct-2026, with his mock-up "Darpan monthly jobs"), folded:
  1. HOME MEDICINES. The owner keeps the list (name, unit, needed per month, active or retired); it starts EMPTY and only he
     adds, edits or retires an item. At month end the count is for the COMING month: in the last 7 days of month M it is the
     count for M+1 (so the month counted is always the month of today + 7 days). "BACHI HAI" is typed, "MANGWANA" =
     max(0, needed - left) is worked out here, never typed. Darpan OR the owner may save it; a later save for the same month
     supersedes the earlier one and the earlier one is kept (append-only: mj_home_count / mj_home_line).
  2. GAADI KI JAANCH. The vehicles (seeded Scooty, Bike, Kia, Wagon R, Vento; stepney and jack aur paana only on Wagon R and
     Vento) -- the owner adds or retires one and says whether it has the spare items. At month end each item is Hai / Nahi,
     one Save for the month; a "Nahi" is on the owner's page. The owner enters each paper's expiry date (pollution,
     insurance, RC); a new date replaces the old one, the old one is kept (mj_paper, append-only). Reminder lead times are
     settings (pollution 7 days, insurance 1 month, RC 45 days). Darpan sees the reminder; he cannot enter a date.
  3. EXPIRY KI SAFAI. READ ONLY from Sanjeevni's expiry watch: the 'expired' lines of the newest good run
     (stock_expiry_run ok=1, the same run expiry_watch.newest() reads). For each line Darpan says what was done:
     "Supplier ko wapas", "Nasht kiya", or "Shelf par nahi mila". The outcome is kept in mj_expiry_outcome, keyed by the item
     (the spine's 20-character key k20), the batch and the expiry -- a later answer for the same key supersedes, the earlier
     is kept.
  4. NO RUPEE AMOUNT ANYWHERE. Darpan's screens are Roman Hinglish, phone-first, every target at least 44 px; the owner's
     page is English. Every save opens on the "Saved" card (the petty book's pattern).

WHO REACHES WHAT -- at the server. The paths /finance/monthjobs/... belong to unit 'medical' (finance_app._unit_for_path's
default): darpan is its maker, the doctor (manoj) its only checker; the viewers (shavez, bhawna, amir) pass the front gate
and are REFUSED here (403) -- there is no viewer's job on these pages. A login with no medical row never gets past the gate.
  maker   (darpan) -> the hub, the count, the vehicle check, the paper reminders, the expiry outcomes (Hinglish)
  checker (manoj)  -> the same pages in English, AND the owner's page: the lists, vehicles, paper dates, lead times, floors

THE AAJ LINES (aaj_duties.json, kind sql; aaj_seed.PEOPLE['darpan']) read these tables READ-ONLY with the same rules as
home_month() / check_month() below:
  darpan.home_meds      due when today >= start of month X - 7 days, X = the month of today + 7 days, X >= the floor
                        (setting home.floor, first count November 2026), an active item exists, and no count for X is saved
  darpan.vehicle_check  due from the LAST day of month M until a check for M is saved, M = the latest month whose last day
                        is today or before, M >= setting vehicle.floor (October 2026)
  darpan.expiry_clear   from the last day of M (setting expiry.floor, October 2026) while an expired line of the newest run
                        has no outcome
  darpan.paper_renewal  n = the papers whose reminder date (expiry + the lead time) is today or before, since = the earliest

TABLES (finance.db, all new, all mj_*; no existing table is changed): made on the first request (F-303), never at import --
and by the kit's data step, so the Aaj lines can be read before anyone opens these pages. Settings are append-only rows
(mj_setting; the newest row of a key is the setting). Every owner change is audited (audit_log).
MONTHJOBS_NOW=<iso> pins the clock for the walk.
"""
import datetime as dt
import hashlib
import os
import re

from flask import Blueprint, redirect, request

bp = Blueprint("month_jobs", __name__)
_db = None
_require = None
_audit = None
UNIT = "medical"
VERSION = "S687-MONTH-JOBS-1.0"
_schema_done = False
BASE = "/finance/monthjobs"

SCHEMA = """
CREATE TABLE IF NOT EXISTS mj_setting (
  id INTEGER PRIMARY KEY, key TEXT NOT NULL, value TEXT NOT NULL, set_at TEXT NOT NULL, set_by TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS mj_setting_key ON mj_setting(key, id);
CREATE TABLE IF NOT EXISTS mj_home_item (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, unit TEXT NOT NULL, need REAL NOT NULL, active INTEGER NOT NULL DEFAULT 1,
  added_at TEXT NOT NULL, added_by TEXT NOT NULL, changed_at TEXT NOT NULL DEFAULT '', changed_by TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS mj_home_count (
  id INTEGER PRIMARY KEY, month TEXT NOT NULL, saved_at TEXT NOT NULL, saved_by TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS mj_home_count_month ON mj_home_count(month, id);
CREATE TABLE IF NOT EXISTS mj_home_line (
  id INTEGER PRIMARY KEY, count_id INTEGER NOT NULL, item_id INTEGER NOT NULL, name TEXT NOT NULL, unit TEXT NOT NULL,
  need REAL NOT NULL, left_qty REAL NOT NULL, order_qty REAL NOT NULL);
CREATE INDEX IF NOT EXISTS mj_home_line_count ON mj_home_line(count_id);
CREATE TABLE IF NOT EXISTS mj_vehicle (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, has_spare INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  pos INTEGER NOT NULL DEFAULT 0, added_at TEXT NOT NULL, added_by TEXT NOT NULL,
  changed_at TEXT NOT NULL DEFAULT '', changed_by TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS mj_vehicle_check (
  id INTEGER PRIMARY KEY, month TEXT NOT NULL, saved_at TEXT NOT NULL, saved_by TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS mj_vehicle_check_month ON mj_vehicle_check(month, id);
CREATE TABLE IF NOT EXISTS mj_vehicle_check_line (
  id INTEGER PRIMARY KEY, check_id INTEGER NOT NULL, vehicle_id INTEGER NOT NULL, vehicle TEXT NOT NULL, item TEXT NOT NULL,
  present INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS mj_vehicle_check_line_check ON mj_vehicle_check_line(check_id);
CREATE TABLE IF NOT EXISTS mj_paper (
  id INTEGER PRIMARY KEY, vehicle_id INTEGER NOT NULL, paper TEXT NOT NULL, expiry TEXT NOT NULL, entered_at TEXT NOT NULL,
  entered_by TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS mj_paper_key ON mj_paper(vehicle_id, paper, id);
CREATE TABLE IF NOT EXISTS mj_expiry_outcome (
  id INTEGER PRIMARY KEY, k20 TEXT NOT NULL, batch TEXT NOT NULL, expiry TEXT NOT NULL, item TEXT NOT NULL,
  outcome TEXT NOT NULL, run_id INTEGER, saved_at TEXT NOT NULL, saved_by TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS mj_expiry_outcome_key ON mj_expiry_outcome(k20, batch, expiry, id);
"""
TABLES = ("mj_setting", "mj_home_item", "mj_home_count", "mj_home_line", "mj_vehicle", "mj_vehicle_check",
          "mj_vehicle_check_line", "mj_paper", "mj_expiry_outcome")

# Seeded once, when mj_vehicle is first made (the owner, 31-Oct-2026). Spare items only on Wagon R and Vento.
VEHICLES = (("Scooty", 0), ("Bike", 0), ("Kia", 0), ("Wagon R", 1), ("Vento", 1))
PAPERS = (("pollution", "Pollution kaagaz", "Pollution"), ("insurance", "Insurance kaagaz", "Insurance"), ("rc", "RC", "RC"))
SPARES = (("stepney", "Stepney", "Stepney"), ("jack", "Jack aur paana", "Jack and spanner"))
OUTCOMES = (("wapas", "Supplier ko wapas", "Returned to the supplier"),
            ("nasht", "Nasht kiya", "Destroyed"),
            ("nahi_mila", "Shelf par nahi mila", "Not found on the shelf"))
DEFAULTS = {"home.floor": "2026-11", "vehicle.floor": "2026-10", "expiry.floor": "2026-10",
            "lead.pollution": "-7 days", "lead.insurance": "-1 month", "lead.rc": "-45 days"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")
MON = tuple(m[:3] for m in MONTHS)
YM_RE = re.compile(r"^(20\d\d)-(0[1-9]|1[0-2])$")
DAY_RE = re.compile(r"^20\d\d-\d\d-\d\d$")
LEAD_RE = re.compile(r"^-(\d{1,3}) (day|days|month|months)$")
QTY_RE = re.compile(r"^\d{1,4}(\.\d{1,2})?$")


# ============================================================================================ mount and schema
def init(app, db_getter, require_fn, audit_fn=None, unit="medical"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    return bp


def ensure(con):
    """The mj_* tables (CREATE ... IF NOT EXISTS) and, the first time mj_vehicle is made, its five vehicles. Called on the
    first request, and by the kit's data step (cfg_s687.py) so the Aaj lines can be read at once."""
    had = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='mj_vehicle'").fetchone() is not None
    con.executescript(SCHEMA)
    if not had and con.execute("SELECT COUNT(*) FROM mj_vehicle").fetchone()[0] == 0:
        at = _stamp()
        for i, (name, spare) in enumerate(VEHICLES):
            con.execute("INSERT INTO mj_vehicle (name, has_spare, active, pos, added_at, added_by) VALUES (?,?,1,?,?,?)",
                        (name, spare, i + 1, at, "S687 seed"))
    con.commit()


def _ensure(con):
    global _schema_done
    if _schema_done:
        return
    ensure(con)
    _schema_done = True


# ============================================================================================ small things
def _now():
    v = os.environ.get("MONTHJOBS_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now().replace(microsecond=0)


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return _now().date()


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def _first(ym):
    return dt.date(int(ym[:4]), int(ym[5:7]), 1)


def _ym(d):
    return "%04d-%02d" % (d.year, d.month)


def _last(ym):
    f = _first(ym)
    n = dt.date(f.year + (f.month == 12), (f.month % 12) + 1, 1)
    return n - dt.timedelta(days=1)


def _prev(ym):
    return _ym(_first(ym) - dt.timedelta(days=1))


def home_month(today):
    """The month a home-medicines count is for: in the last 7 days of a month, the next one; else this one."""
    return _ym(today + dt.timedelta(days=7))


def home_due_from(ym):
    return _first(ym) - dt.timedelta(days=7)


def check_month(today):
    """The month whose month-end check is open: the latest month whose LAST day is today or before."""
    tomorrow = today + dt.timedelta(days=1)
    return _ym(tomorrow.replace(day=1) - dt.timedelta(days=1))


def mname(ym, lang="en", year=False):
    try:
        f = _first(ym)
    except (TypeError, ValueError):
        return str(ym)
    return MONTHS[f.month - 1] + ((" %d" % f.year) if year else "")


def dm(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return "%02d-%s" % (d.day, MON[d.month - 1])
    except (TypeError, ValueError):
        return _esc(iso or "—")


def dmy(iso):
    try:
        d = dt.date.fromisoformat(str(iso)[:10])
        return "%02d-%s-%d" % (d.day, MON[d.month - 1], d.year)
    except (TypeError, ValueError):
        return _esc(iso or "—")


def when(stamp):
    s = str(stamp or "")
    return "%s %s" % (dm(s[:10]), s[11:16]) if len(s) >= 16 else dm(s)


def qty(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    return ("%d" % f) if abs(f - round(f)) < 1e-9 else ("%.2f" % f).rstrip("0").rstrip(".")


def need_order(need, left):
    """MANGWANA = max(0, needed - left), to two places."""
    return max(0.0, round(float(need) - float(left), 2))


def name_of(login):
    login = str(login or "")
    return {"manoj": "Dr Manoj", "darpan": "Darpan"}.get(login, login.title())


def setting(con, key):
    r = con.execute("SELECT value FROM mj_setting WHERE key=? ORDER BY id DESC LIMIT 1", (key,)).fetchone()
    v = (r[0] if r else "") or ""
    return v if v else DEFAULTS.get(key, "")


def _set(con, key, value, who):
    con.execute("INSERT INTO mj_setting (key, value, set_at, set_by) VALUES (?,?,?,?)", (key, value, _stamp(), who))


def lead_split(v):
    m = LEAD_RE.match(str(v or ""))
    if not m:
        return 0, "days"
    return int(m.group(1)), ("months" if m.group(2).startswith("month") else "days")


def lead_words(v, lang="en"):
    n, u = lead_split(v)
    if u == "months":
        return ("%d month" % n) + ("" if n == 1 else "s")
    return ("%d day" % n) + ("" if n == 1 else "s")


def _audit_safe(con, table, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)
        con.commit()
    except Exception:                                                  # noqa: BLE001
        pass


# ============================================================================================ who
def _user(*roles):
    """(user dict, lang) or (None, None). roles: which unit roles may pass."""
    u, err = _require(*roles, unit=UNIT)
    if err:
        return None, None
    have = set(u.get("roles") or [])
    return u, ("en" if "checker" in have else "hi")


def _who(u):
    return str((u or {}).get("user") or "")


def _denied(lang):
    if lang == "en":
        body = "<div class='card'><h2>Not permitted</h2><p>Your login has no job on these pages.</p></div>"
    else:
        body = "<div class='card'><h2>Yeh page aapke liye nahin hai</h2><p>Galti lage to Dr Manoj se kahiye.</p></div>"
    return _shell("Monthly jobs", body, lang), 403


# ============================================================================================ reading
def home_items(con, active_only=True):
    q = "SELECT * FROM mj_home_item" + (" WHERE active=1" if active_only else "") + " ORDER BY active DESC, id"
    return list(con.execute(q))


def home_count(con, ym):
    """The latest count for a month: (row, {item_id: line}) or (None, {})."""
    c = con.execute("SELECT * FROM mj_home_count WHERE month=? ORDER BY id DESC LIMIT 1", (ym,)).fetchone()
    if c is None:
        return None, {}
    return c, {r["item_id"]: r for r in con.execute("SELECT * FROM mj_home_line WHERE count_id=? ORDER BY id", (c["id"],))}


def order_summary(lines, lang="hi"):
    """'2 dawai · 4 patta · 1 shishi' -- what is to be ordered, by unit. No rupees."""
    by_unit, n = {}, 0
    for ln in lines:
        q = float(ln["order_qty"])
        if q > 0:
            n += 1
            by_unit[ln["unit"]] = by_unit.get(ln["unit"], 0.0) + q
    if not n:
        return "kuch nahin" if lang == "hi" else "nothing"
    head = ("%d dawai" % n) if lang == "hi" else ("%d medicine%s" % (n, "" if n == 1 else "s"))
    return " · ".join([head] + ["%s %s" % (qty(q), _esc(u)) for u, q in by_unit.items()])


def home_state(con, today):
    ym = home_month(today)
    floor = setting(con, "home.floor")
    items = home_items(con)
    c, lines = home_count(con, ym)
    st = dict(month=ym, floor=floor, items=items, count=c, lines=lines, due_from=home_due_from(ym).isoformat())
    st["open"] = bool(ym >= floor)
    st["due"] = bool(st["open"] and items and c is None)
    if not st["open"]:
        st["next"] = home_due_from(floor).isoformat()
    return st


def vehicles(con, active_only=True):
    q = "SELECT * FROM mj_vehicle" + (" WHERE active=1" if active_only else "") + " ORDER BY active DESC, pos, id"
    return list(con.execute(q))


def items_of(v):
    out = [(k, hi, en) for k, hi, en in PAPERS]
    if v["has_spare"]:
        out += [(k, hi, en) for k, hi, en in SPARES]
    return out


def vehicle_check(con, ym):
    c = con.execute("SELECT * FROM mj_vehicle_check WHERE month=? ORDER BY id DESC LIMIT 1", (ym,)).fetchone()
    if c is None:
        return None, {}
    return c, {(r["vehicle_id"], r["item"]): r for r in
               con.execute("SELECT * FROM mj_vehicle_check_line WHERE check_id=? ORDER BY id", (c["id"],))}


def missing_of(lines):
    """[(vehicle, item key)] of every 'Nahi' in a saved check -- what the owner's page shows."""
    return [(ln["vehicle"], ln["item"]) for ln in lines.values() if not ln["present"]]


def item_label(key, lang):
    for k, hi, en in PAPERS + SPARES:
        if k == key:
            return hi if lang == "hi" else en
    return key


def vehicle_state(con, today):
    ym = check_month(today)
    floor = setting(con, "vehicle.floor")
    vs = vehicles(con)
    c, lines = vehicle_check(con, ym) if ym >= floor else (None, {})
    st = dict(month=ym, floor=floor, vehicles=vs, check=c, lines=lines, due_from=_last(ym).isoformat())
    st["open"] = bool(ym >= floor)
    st["due"] = bool(st["open"] and vs and c is None)
    if not st["open"]:
        st["next"] = _last(floor).isoformat()
    return st


def remind_day(con, expiry, lead):
    """The reminder day of a paper: expiry minus the lead time. A lead in MONTHS is clamped so the reminder is never later than
    that many calendar months before the expiry (SQLite rolls 31-Mar minus 1 month over to 03-Mar; the clamp makes it 28-Feb).
    The same expression as the duty darpan.paper_renewal's SQL."""
    return con.execute("SELECT CASE WHEN ? LIKE '%month%' THEN MIN(date(?, ?), date(?, 'start of month', ?, '+1 month', '-1 day')) "
                       "ELSE date(?, ?) END", (lead, expiry, lead, expiry, lead, expiry, lead)).fetchone()[0]


def paper_rows(con, today):
    """For each active vehicle and paper: the current date (newest entered), its reminder date, due / expired."""
    out = []
    for v in vehicles(con):
        for k, hi, en in PAPERS:
            r = con.execute("SELECT * FROM mj_paper WHERE vehicle_id=? AND paper=? ORDER BY id DESC LIMIT 1", (v["id"], k)).fetchone()
            row = dict(vehicle=v, paper=k, hi=hi, en=en, cur=r, expiry=None, remind=None, due=False, gone=False)
            if r is not None and DAY_RE.match(r["expiry"] or ""):
                rem = remind_day(con, r["expiry"], setting(con, "lead." + k))
                row.update(expiry=r["expiry"], remind=rem, due=bool(rem and rem <= today.isoformat()),
                           gone=bool(r["expiry"] < today.isoformat()))
            out.append(row)
    return out


def okey(ln):
    """A line's key on the form: its item (k20), batch and expiry -- never its row id, which a new expiry run replaces."""
    raw = "\x1f".join(str(ln[c] or "") for c in ("k20", "batch", "expiry"))
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


def expiry_run(con, ym):
    """The newest good run of Sanjeevni's expiry watch and its 'expired' lines that are this month-end's job: units on the
    shelf (> 0, as expiry_watch counts them) and an expiry month in or before `ym`, the month whose last day has come (the
    watch lists a batch from the 1st of its expiry month; that batch is next month-end's job, not this one's)."""
    try:
        r = con.execute("SELECT * FROM stock_expiry_run WHERE ok=1 ORDER BY id DESC LIMIT 1").fetchone()
    except Exception:                                                  # noqa: BLE001 -- Sanjeevni's table not there
        return None, []
    if r is None:
        return None, []
    lines = list(con.execute("SELECT * FROM stock_expiry_line WHERE run_id=? AND section='expired' AND COALESCE(units, 0) > 0 "
                             "AND substr(COALESCE(expiry, ''), 1, 7) <= ? ORDER BY seq, id", (r["id"], ym)))
    return r, lines


def outcome_of(con, ln):
    return con.execute("SELECT * FROM mj_expiry_outcome WHERE k20=? AND batch=? AND expiry=? ORDER BY id DESC LIMIT 1",
                       (ln["k20"] or "", ln["batch"] or "", ln["expiry"] or "")).fetchone()


def expiry_state(con, today):
    ym = check_month(today)
    floor = setting(con, "expiry.floor")
    run, lines = expiry_run(con, ym)
    rows = [dict(line=ln, outcome=outcome_of(con, ln)) for ln in lines]
    st = dict(month=ym, floor=floor, run=run, rows=rows, due_from=_last(ym).isoformat())
    st["open"] = bool(ym >= floor)
    st["waiting"] = sum(1 for r in rows if r["outcome"] is None)
    st["due"] = bool(st["open"] and st["waiting"])
    if not st["open"]:
        st["next"] = _last(floor).isoformat()
    return st


def outcome_label(key, lang):
    for k, hi, en in OUTCOMES:
        if k == key:
            return hi if lang == "hi" else en
    return key


def exp_mmyy(v):
    s = str(v or "")
    return ("%s/%s" % (s[5:7], s[:4])) if re.match(r"^\d{4}-\d{2}", s) else _esc(s or "—")


# ============================================================================================ the saved card
def _saved(lang, rows):
    head = "✓ Saved — सेव हो गया" if lang == "hi" else "✓ Saved"
    t = "".join("<tr><td>%s</td><td><b>%s</b></td></tr>" % (a, b) for a, b in rows)
    return "<div class='saved'><div class='sv1'>%s</div>%s</div>" % (head, ("<table class='svt'><tbody>%s</tbody></table>" % t) if t else "")


def _msg(lang):
    m = request.args.get("msg") or ""
    bad = {"blank": ("Har line bhariye, phir Save kijiye.", "Fill every line, then Save."),
           "bad": ("Kuch galat likha gaya — dobara dekhiye.", "Something was not right -- please check and try again."),
           "none": ("Kuch chuna nahin gaya.", "Nothing was chosen."),
           "empty": ("List khaali hai — Dr Manoj dawai jodenge.", "The list is empty -- add a medicine first."),
           "closed": ("Is mahine ki ginti abhi nahin.", "That month is not open."),
           "stale": ("List badal gayi hai — jo dawai ab list mein nahin, unka jawab nahin likha. Dobara dekhiye.",
                     "The expiry list changed -- answers for lines no longer on it were not kept. Please check again.")}
    if m in bad:
        return "<div class='bad'>%s</div>" % (bad[m][0] if lang == "hi" else bad[m][1])
    return ""


def _rid():
    try:
        return int(request.args.get("id") or 0)
    except ValueError:
        return 0


# ============================================================================================ Darpan's hub
@bp.route(BASE)
def hub():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    if lang == "en":
        return redirect(BASE + "/owner")
    con = _db()
    _ensure(con)
    today = _today()
    h, v, e = home_state(con, today), vehicle_state(con, today), expiry_state(con, today)
    p = [r for r in paper_rows(con, today) if r["due"]]

    def card(title, sub, state, href):
        chip = {"due": "<span class='chip due'>Baaki</span>", "done": "<span class='chip done'>Ho gaya</span>",
                "later": "<span class='chip'>Abhi nahin</span>"}[state]
        return ("<a class='job' href='%s'><span class='jt'>%s %s</span><span class='js'>%s</span></a>" % (href, _esc(title), chip, sub))

    out = ["<p class='mut'><a class='back' href='/finance/aaj'>← Aaj ka kaam</a></p>", "<div class='sec'>IS MAHINE KA KAAM</div>"]
    out.append(card("Home medicines — ginti", "%s ke liye · mahine ke aakhri hafte se · ghar mein kitni bachi hai, likhiye" % mname(h["month"]),
                    "due" if h["due"] else ("done" if h["count"] is not None else "later"), BASE + "/home"))
    out.append(card("Gaadi ki jaanch", "%s · kaagaz, stepney, jack aur paana" % mname(v["month"]),
                    "due" if v["due"] else ("done" if v["check"] is not None else "later"), BASE + "/gaadi"))
    out.append(card("Expiry ki safai", "har dawai par: supplier ko wapas / nasht",
                    "due" if e["due"] else ("done" if (e["open"] and e["rows"]) else "later"), BASE + "/expiry"))
    out.append("<div class='sec'>KAAGAZ KI YAAD</div>")
    out.append(card("Kaagaz ki yaad", ("%d kaagaz khatm ho rahe hain" % len(p)) if p else "abhi koi kaagaz khatm nahin ho raha",
                    "due" if p else "done", BASE + "/kaagaz"))
    return _shell("Mahine ka kaam — Darpan", "".join(out), "hi")


# ============================================================================================ 1 · home medicines
def _home_month_arg(con, today):
    """The month asked for (?m= or the form's m): from the floor up to the month open now; else None."""
    st = home_state(con, today)
    m = (request.values.get("m") or "").strip()
    if not m:
        return st["month"] if st["open"] else None
    if not YM_RE.match(m) or m < st["floor"] or m > st["month"]:
        return None
    return m


@bp.route(BASE + "/home")
def home_page():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    today = _today()
    st = home_state(con, today)
    ym = _home_month_arg(con, today)
    hi = lang == "hi"
    back = ("<p class='mut'><a class='back' href='/finance/aaj'>← Aaj ka kaam</a></p>" if hi else
            "<p class='mut'><a class='back' href='%s/owner'>← Monthly jobs</a></p>" % BASE)
    out = [back]
    if (request.args.get("msg") == "saved"):
        c = con.execute("SELECT * FROM mj_home_count WHERE id=?", (_rid(),)).fetchone()
        if c is not None and c["saved_by"] == _who(u):
            lines = list(con.execute("SELECT * FROM mj_home_line WHERE count_id=?", (c["id"],)))
            out.append(_saved(lang, [("Kya" if hi else "What", "Home medicines — %s" % mname(c["month"])),
                                     ("Mangwana" if hi else "To order", order_summary(lines, lang)),
                                     ("Kab" if hi else "When", when(c["saved_at"]))]))
    out.append(_msg(lang))
    if ym is None:
        nxt = st.get("next") or st["due_from"]
        out.append("<div class='card'><h2>Home medicines</h2><p>%s</p></div>" % (
            ("Pehli ginti %s ke liye — %s se." % (mname(st["floor"]), dm(nxt))) if hi else
            ("The first count is for %s -- from %s." % (mname(st["floor"], year=True), dmy(nxt)))))
        return _shell("Home medicines", "".join(out), lang)
    items = home_items(con)
    c, lines = home_count(con, ym)
    out.append("<h2 class='pt'>Home medicines — %s %s</h2>" % (mname(ym), "ke liye" if hi else "(the count for that month)"))
    out.append("<p class='mut'>%s</p>" % ("Ghar mein kitni bachi hai, woh likhiye. Kitni mangwani hai, system bata dega." if hi else
                                         "Enter what is left at home; the page works out what to order: needed − left."))
    if c is not None:
        out.append("<p class='mut'>%s %s · %s</p>" % ("Pichhli ginti:" if hi else "Saved count:", _esc(name_of(c["saved_by"])),
                                                      when(c["saved_at"])))
    if not items:
        out.append("<div class='card'><p>%s</p></div>" % ("List abhi khaali hai — Dr Manoj dawai jodenge." if hi else
                                                           "The list is empty. Add the medicines on your page first."))
        return _shell("Home medicines", "".join(out), lang)
    rows = []
    for it in items:
        prev = lines.get(it["id"])
        val = qty(prev["left_qty"]) if prev is not None else ""
        oq = qty(need_order(it["need"], prev["left_qty"])) if prev is not None else "—"
        rows.append("<tr data-need='%s' data-unit='%s'><td><b>%s</b><div class='sm'>%s %s %s</div></td>"
                    "<td><input class='num' type='text' inputmode='decimal' name='left_%d' value='%s' aria-label='%s %s' autocomplete='off'></td>"
                    "<td class='r mg'>%s</td></tr>"
                    % (qty(it["need"]), _esc(it["unit"]), _esc(it["name"]), "zaroorat" if hi else "needed", qty(it["need"]),
                       _esc(it["unit"]), it["id"], _esc(val), _esc(it["name"]), "bachi hai" if hi else "left", oq))
    foot = order_summary(lines.values(), lang) if c is not None else "—"
    out.append("<form method='post' action='%s/home'><input type='hidden' name='m' value='%s'>"
               "<table class='grid hm'><thead><tr><th>%s</th><th>%s</th><th class='r'>%s</th></tr></thead><tbody>%s</tbody></table>"
               "<p class='mut'>%s</p>"
               "<div class='foot'>%s <b id='mgt'>%s</b></div>"
               "<button class='save' type='submit'>Save</button></form>"
               % (BASE, ym, "DAWAI · mahine ki zaroorat" if hi else "MEDICINE · needed / month", "BACHI HAI" if hi else "LEFT",
                  "MANGWANA" if hi else "TO ORDER", "".join(rows),
                  ("List aur zaroorat Dr Manoj settings mein rakhte hain. Ginti Dr Manoj ya Darpan, koi bhi bhar sakta hai." if hi else
                   "Darpan or you may fill it; a later save for the same month replaces this one (the earlier is kept)."),
                  "Mangwana hai:" if hi else "To order:", foot))
    out.append(_HOME_JS % ("dawai" if hi else "medicine(s)", "kuch nahin" if hi else "nothing"))
    return _shell("Home medicines", "".join(out), lang)


_HOME_JS = """<script>
(function(){var t=document.querySelector('table.hm');if(!t)return;var WORD='%s',NONE='%s';
function q(v){v=Math.round(v*100)/100;return (Math.abs(v-Math.round(v))<1e-9)?String(Math.round(v)):String(v);}
function run(){var n=0,by={},order=[];t.querySelectorAll('tbody tr').forEach(function(tr){
 var i=tr.querySelector('input'),c=tr.querySelector('.mg'),need=parseFloat(tr.dataset.need),s=(i.value||'').trim();
 if(s===''||!/^\\d{1,4}(\\.\\d{1,2})?$/.test(s)){c.textContent='\u2014';return;}
 var m=Math.max(0,Math.round((need-parseFloat(s))*100)/100);c.textContent=q(m);
 if(m>0){n++;var u=tr.dataset.unit;if(!(u in by)){by[u]=0;order.push(u);}by[u]+=m;}});
 var o=document.getElementById('mgt');if(!n){o.textContent=NONE;return;}
 o.textContent=[n+' '+WORD].concat(order.map(function(u){return q(by[u])+' '+u;})).join(' \u00b7 ');}
t.addEventListener('input',run);})();
</script>"""


@bp.route(BASE + "/home", methods=["POST"])
def home_save():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    today = _today()
    ym = _home_month_arg(con, today)
    if ym is None:
        return redirect(BASE + "/home?msg=closed")
    items = home_items(con)
    if not items:
        return redirect(BASE + "/home?m=%s&msg=empty" % ym)
    vals = []
    for it in items:
        s = (request.form.get("left_%d" % it["id"]) or "").strip()
        if s == "":
            return redirect(BASE + "/home?m=%s&msg=blank" % ym)
        if not QTY_RE.match(s):
            return redirect(BASE + "/home?m=%s&msg=bad" % ym)
        vals.append((it, float(s)))
    at, who = _stamp(), _who(u)
    cur = con.execute("INSERT INTO mj_home_count (month, saved_at, saved_by) VALUES (?,?,?)", (ym, at, who))
    cid = cur.lastrowid
    for it, left in vals:
        con.execute("INSERT INTO mj_home_line (count_id, item_id, name, unit, need, left_qty, order_qty) VALUES (?,?,?,?,?,?,?)",
                    (cid, it["id"], it["name"], it["unit"], float(it["need"]), left, need_order(it["need"], left)))
    con.commit()
    _audit_safe(con, "mj_home_count", cid, "count_saved", None, dict(month=ym, lines=len(vals)), who)
    return redirect(BASE + "/home?m=%s&msg=saved&id=%d" % (ym, cid))


# ============================================================================================ 2 · gaadi ki jaanch
def _check_month_arg(con, today):
    st = vehicle_state(con, today)
    m = (request.values.get("m") or "").strip()
    if not m:
        return st["month"] if st["open"] else None
    if not YM_RE.match(m) or m < st["floor"] or m > st["month"]:
        return None
    return m


@bp.route(BASE + "/gaadi")
def gaadi_page():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    today = _today()
    hi = lang == "hi"
    st = vehicle_state(con, today)
    ym = _check_month_arg(con, today)
    out = ["<p class='mut'><a class='back' href='%s'>%s</a></p>" % (("/finance/aaj", "← Aaj ka kaam") if hi else (BASE + "/owner", "← Monthly jobs"))]
    if request.args.get("msg") == "saved":
        c = con.execute("SELECT * FROM mj_vehicle_check WHERE id=?", (_rid(),)).fetchone()
        if c is not None and c["saved_by"] == _who(u):
            ls = list(con.execute("SELECT * FROM mj_vehicle_check_line WHERE check_id=?", (c["id"],)))
            miss = [ln for ln in ls if not ln["present"]]
            out.append(_saved(lang, [("Kya" if hi else "What", "Gaadi ki jaanch — %s" % mname(c["month"])),
                                     ("Nahi mila" if hi else "Missing", ", ".join("%s: %s" % (_esc(m["vehicle"]), item_label(m["item"], lang)) for m in miss)
                                      or ("sab theek" if hi else "nothing")),
                                     ("Kab" if hi else "When", when(c["saved_at"]))]))
    out.append(_msg(lang))
    if ym is None:
        out.append("<div class='card'><h2>Gaadi ki jaanch</h2><p>%s</p></div>" % (
            ("Pehli jaanch %s ko." % dm(st.get("next"))) if hi else ("The first check is on %s." % dmy(st.get("next")))))
        return _shell("Gaadi ki jaanch", "".join(out), lang)
    c, lines = vehicle_check(con, ym)
    papers = {(r["vehicle"]["id"], r["paper"]): r for r in paper_rows(con, today)}
    out.append("<h2 class='pt'>Gaadi ki jaanch — %s</h2>" % mname(ym))
    out.append("<p class='mut'>%s</p>" % ('Har gaadi mein dekhiye. Jo nahi mila, us par "Nahi" dabaiye.' if hi else
                                         "Each vehicle: is each item there? Mark what is missing."))
    if c is not None:
        out.append("<p class='mut'>%s %s · %s</p>" % ("Pichhli jaanch:" if hi else "Saved check:", _esc(name_of(c["saved_by"])), when(c["saved_at"])))
    cards = []
    for v in vehicles(con):
        rows = []
        for k, lhi, len_ in items_of(v):
            prev = lines.get((v["id"], k))
            yes = prev is not None and prev["present"] == 1
            no = prev is not None and prev["present"] == 0
            rows.append("<div class='hn'><span class='hl'>%s</span>"
                        "<label class='opt'><input type='radio' name='v%d_%s' value='1'%s><span>%s</span></label>"
                        "<label class='opt no'><input type='radio' name='v%d_%s' value='0'%s><span>%s</span></label></div>"
                        % (lhi if hi else len_, v["id"], k, " checked" if yes else "", "Hai" if hi else "Yes",
                           v["id"], k, " checked" if no else "", "Nahi" if hi else "No"))
        warn = []
        for k, lhi, len_ in PAPERS:
            p = papers.get((v["id"], k))
            if p and p["due"]:
                warn.append("<div class='warn'>%s %s %s</div>" % (
                    (lhi.replace(" kaagaz", "") if hi else len_), dmy(p["expiry"]),
                    "ko khatm — naya kaagaz banwa kar Dr Manoj ko dijiye" if hi else "expires -- renew"))
        cards.append("<div class='card veh'><h3>%s</h3>%s%s</div>" % (_esc(v["name"]), "".join(rows), "".join(warn)))
    out.append("<form method='post' action='%s/gaadi'><input type='hidden' name='m' value='%s'>%s"
               "<button class='save' type='submit'>Save</button></form>" % (BASE, ym, "".join(cards)))
    return _shell("Gaadi ki jaanch", "".join(out), lang)


@bp.route(BASE + "/gaadi", methods=["POST"])
def gaadi_save():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    ym = _check_month_arg(con, _today())
    if ym is None:
        return redirect(BASE + "/gaadi?msg=closed")
    vals = []
    for v in vehicles(con):
        for k, _h, _e in items_of(v):
            s = request.form.get("v%d_%s" % (v["id"], k))
            if s not in ("0", "1"):
                return redirect(BASE + "/gaadi?m=%s&msg=blank" % ym)
            vals.append((v, k, int(s)))
    if not vals:
        return redirect(BASE + "/gaadi?m=%s&msg=empty" % ym)
    at, who = _stamp(), _who(u)
    cid = con.execute("INSERT INTO mj_vehicle_check (month, saved_at, saved_by) VALUES (?,?,?)", (ym, at, who)).lastrowid
    for v, k, present in vals:
        con.execute("INSERT INTO mj_vehicle_check_line (check_id, vehicle_id, vehicle, item, present) VALUES (?,?,?,?,?)",
                    (cid, v["id"], v["name"], k, present))
    con.commit()
    _audit_safe(con, "mj_vehicle_check", cid, "check_saved", None,
                dict(month=ym, missing=["%s:%s" % (v["name"], k) for v, k, p in vals if not p]), who)
    return redirect(BASE + "/gaadi?m=%s&msg=saved&id=%d" % (ym, cid))


# ============================================================================================ 2b · kaagaz ki yaad
@bp.route(BASE + "/kaagaz")
def kaagaz_page():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    today = _today()
    hi = lang == "hi"
    rows = paper_rows(con, today)
    due = sorted([r for r in rows if r["due"]], key=lambda r: r["remind"])
    out = ["<p class='mut'><a class='back' href='%s'>%s</a></p>" % (("/finance/aaj", "← Aaj ka kaam") if hi else (BASE + "/owner", "← Monthly jobs")),
           "<h2 class='pt'>%s</h2>" % ("Kaagaz ki yaad" if hi else "Vehicle papers")]
    if due:
        for r in due:
            pl = r["en"] if not hi else r["hi"].replace(" kaagaz", "").lower().replace("rc", "RC")
            out.append("<div class='card remind'><div class='rt'>%s — %s %s %s</div><div class='sm'>%s</div></div>" % (
                _esc(r["vehicle"]["name"]), _esc(pl), dmy(r["expiry"]),
                ("ko khatm" if not r["gone"] else "ko khatm ho gaya") if hi else ("expires" if not r["gone"] else "expired"),
                "Naya kaagaz banwa kar Dr Manoj ko dijiye — nayi date likhne tak yeh line rahegi." if hi else
                "Darpan sees this until you enter the new date on your page."))
    else:
        out.append("<div class='card'><p>%s</p></div>" % ("Abhi koi kaagaz khatm nahin ho raha." if hi else "No paper is due for renewal."))
    head = "".join("<th>%s</th>" % (h if hi else e) for _k, h, e in PAPERS)
    body = []
    for v in vehicles(con):
        cells = []
        for k, _h, _e in PAPERS:
            r = next((x for x in rows if x["vehicle"]["id"] == v["id"] and x["paper"] == k), None)
            cells.append("<td%s>%s</td>" % (" class='amb'" if r and r["due"] else "", dmy(r["expiry"]) if r and r["expiry"] else "—"))
        body.append("<tr><td><b>%s</b></td>%s</tr>" % (_esc(v["name"]), "".join(cells)))
    out.append("<table class='grid'><thead><tr><th>%s</th>%s</tr></thead><tbody>%s</tbody></table>"
               % ("Gaadi" if hi else "Vehicle", head, "".join(body)))
    if hi:
        out.append("<p class='mut'>Tareekh sirf Dr Manoj likhte hain.</p>")
    return _shell("Kaagaz ki yaad", "".join(out), lang)


# ============================================================================================ 3 · expiry ki safai
@bp.route(BASE + "/expiry")
def expiry_page():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    today = _today()
    hi = lang == "hi"
    st = expiry_state(con, today)
    out = ["<p class='mut'><a class='back' href='%s'>%s</a></p>" % (("/finance/aaj", "← Aaj ka kaam") if hi else (BASE + "/owner", "← Monthly jobs"))]
    if request.args.get("msg") == "saved":
        r = con.execute("SELECT * FROM mj_expiry_outcome WHERE id=?", (_rid(),)).fetchone()
        try:
            n = max(1, min(999, int(request.args.get("n") or 1)))
        except ValueError:
            n = 1
        if r is not None and r["saved_by"] == _who(u):
            out.append(_saved(lang, [("Kya" if hi else "What", "Expiry ki safai" if hi else "Expiry clear-out"),
                                     ("Kitni dawai" if hi else "Lines", str(n)), ("Kab" if hi else "When", when(r["saved_at"]))]
                              + ([("Dhyan dijiye" if hi else "Note", ("%d dawai ab list mein nahin — unka jawab nahin likha" if hi else
                                                                      "%d line(s) no longer on the list -- not kept") % _stale())] if _stale() else [])))
    out.append(_msg(lang))
    out.append("<h2 class='pt'>%s</h2>" % ("Expiry ki safai" if hi else "Expiry clear-out"))
    out.append("<p class='mut'>%s</p>" % ("Expiry wali dawai shelf se hataiye — har ek par likhiye: supplier ko wapas, ya nasht kiya." if hi else
                                         "The expired lines of Sanjeevni's newest expiry list; for each, what was done."))
    if st["run"] is None or not st["rows"]:
        out.append("<div class='card'><p>%s</p></div>" % ("Abhi expiry ki koi dawai list mein nahin." if hi else "No expired line on the newest list."))
        return _shell("Expiry ki safai", "".join(out), lang)
    out.append("<p class='mut'>%s %s</p>" % ("Marg ki list:" if hi else "Marg's list as on", dmy(st["run"]["export_as_on"] or st["run"]["today"])))
    cards = []
    for r in st["rows"]:
        ln, o = r["line"], r["outcome"]
        opts = "".join("<label class='opt%s'><input type='radio' name='o_%s' value='%s'%s><span>%s</span></label>"
                       % (" no" if k == "nasht" else "", okey(ln), k, " checked" if (o is not None and o["outcome"] == k) else "",
                          lhi if hi else len_) for k, lhi, len_ in OUTCOMES)
        done = ("<div class='sm'>%s %s · %s</div>" % ("Likha:" if hi else "Answered by", _esc(name_of(o["saved_by"])), when(o["saved_at"]))
                if o is not None else "")
        cards.append("<div class='card ex'><div><b>%s</b></div><div class='sm'>Batch %s · Exp %s · %s %s</div>"
                     "<div class='opts'>%s</div>%s</div>"
                     % (_esc(ln["item"]), _esc(ln["batch"] or "—"), exp_mmyy(ln["expiry"]), "Matra" if hi else "Units",
                        _esc(ln["units"]), opts, done))
    out.append("<form method='post' action='%s/expiry'>%s<button class='save' type='submit'>Save</button></form>" % (BASE, "".join(cards)))
    return _shell("Expiry ki safai", "".join(out), lang)


@bp.route(BASE + "/expiry", methods=["POST"])
def expiry_save():
    u, lang = _user("maker", "checker")
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    run, lines = expiry_run(con, check_month(_today()))
    keys = {k for k, _h, _e in OUTCOMES}
    at, who, first, n = _stamp(), _who(u), 0, 0
    have = {okey(ln) for ln in lines}
    stale = sum(1 for f, v in request.form.items() if f.startswith("o_") and v and f[2:] not in have)
    for ln in lines:
        v = request.form.get("o_%s" % okey(ln))
        if v is None or v == "":
            continue
        if v not in keys:
            return redirect(BASE + "/expiry?msg=bad")
        o = outcome_of(con, ln)
        if o is not None and o["outcome"] == v:
            continue                                                   # the same answer again: nothing new to keep
        rid = con.execute("INSERT INTO mj_expiry_outcome (k20, batch, expiry, item, outcome, run_id, saved_at, saved_by) "
                          "VALUES (?,?,?,?,?,?,?,?)", (ln["k20"] or "", ln["batch"] or "", ln["expiry"] or "", ln["item"] or "",
                                                       v, run["id"], at, who)).lastrowid
        first = first or rid
        n += 1
    con.commit()
    if not n:
        return redirect(BASE + ("/expiry?msg=stale&s=%d" % min(stale, 999) if stale else "/expiry?msg=none"))
    _audit_safe(con, "mj_expiry_outcome", first, "outcomes_saved", None, dict(lines=n, run=run["id"], not_on_list=stale), who)
    return redirect(BASE + "/expiry?msg=saved&id=%d&n=%d%s" % (first, n, ("&s=%d" % min(stale, 999)) if stale else ""))


def _stale():
    try:
        return max(0, min(999, int(request.args.get("s") or 0)))
    except ValueError:
        return 0


# ============================================================================================ 5 · the owner's page
def _owner():
    u, _lang = _user("checker")
    return u


@bp.route(BASE + "/owner")
def owner_page():
    u = _owner()
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    today = _today()
    h, v, e = home_state(con, today), vehicle_state(con, today), expiry_state(con, today)
    prow = paper_rows(con, today)
    out = []
    if request.args.get("msg") == "saved":
        what = {"item": "Home medicine list", "vehicle": "Vehicles", "paper": "Paper date", "settings": "Settings"}.get(
            request.args.get("what") or "", "")
        out.append(_saved("en", [("What", what)] if what else []))
    out.append(_msg("en"))
    out.append("<p class='mut'>%s · what is done, what is waiting</p>" % dmy(today.isoformat()))

    # ---- this month
    t = []
    if h["count"] is not None:
        hs = "<span class='okc'>Saved</span> %s by %s · to order: %s" % (when(h["count"]["saved_at"]), _esc(name_of(h["count"]["saved_by"])),
                                                                         order_summary(h["lines"].values(), "en"))
    elif not h["open"]:
        hs = "Not open yet -- the first count is for %s, from %s" % (mname(h["floor"], year=True), dmy(h["next"]))
    elif not h["items"]:
        hs = "<span class='ambc'>No medicines on the list yet</span> -- add them below"
    else:
        hs = "<span class='ambc'>Waiting</span> since %s" % dmy(h["due_from"])
    t.append(("Home medicines — %s" % mname(h["month"], year=True), hs, "<a class='btn' href='%s/home?m=%s'>Enter %s's count</a>"
              % (BASE, h["month"], mname(h["month"])) if h["open"] and h["items"] else ""))
    if v["check"] is not None:
        miss = missing_of(v["lines"])
        vs = "<span class='okc'>Saved</span> %s by %s" % (when(v["check"]["saved_at"]), _esc(name_of(v["check"]["saved_by"])))
        vs += (" · " + "; ".join("<span class='nahi'>%s: no %s</span>" % (_esc(a), item_label(b, "en").lower()) for a, b in miss)) if miss \
            else " · everything present"
    elif not v["open"]:
        vs = "Not open yet -- the first check is on %s" % dmy(v["next"])
    else:
        vs = "<span class='ambc'>Waiting</span> since %s" % dmy(v["due_from"])
    t.append(("Vehicle check — %s" % mname(v["month"], year=True), vs, "<a class='btn' href='%s/gaadi'>Open</a>" % BASE if v["open"] else ""))
    if not e["open"]:
        es = "Not open yet -- from %s" % dmy(e["next"])
    elif not e["rows"]:
        es = "No expired line on the newest list"
    elif e["waiting"]:
        es = "<span class='ambc'>Waiting</span>: %d of %d line(s) without an outcome (since %s)" % (e["waiting"], len(e["rows"]), dmy(e["due_from"]))
    else:
        es = "<span class='okc'>Done</span>: all %d line(s) answered" % len(e["rows"])
    t.append(("Expiry clear-out (month end)", es, "<a class='btn' href='%s/expiry'>Open</a>" % BASE))
    pd = [r for r in prow if r["due"]]
    ps = ("<span class='ambc'>%d due</span>: " % len(pd) + "; ".join("%s %s %s" % (_esc(r["vehicle"]["name"]), r["en"].lower() if r["paper"] != "rc" else "RC",
                                                                     dmy(r["expiry"])) for r in pd)) if pd else "None due"
    t.append(("Paper reminders", ps, ""))
    out.append("<div class='card'><div class='sec'>THIS MONTH</div><table class='grid tm'><tbody>%s</tbody></table></div>"
               % "".join("<tr><td><b>%s</b></td><td>%s</td><td class='r'>%s</td></tr>" % r for r in t))

    # ---- settings: home medicines
    rows = []
    for it in home_items(con, active_only=False):
        rows.append("<tr%s><td colspan='3'><form method='post' action='%s/owner/item' class='row'>"
                    "<input type='hidden' name='id' value='%d'>"
                    "<input class='tx' name='name' value='%s' maxlength='60' aria-label='name'>"
                    "<input class='tx sm2' name='unit' value='%s' maxlength='20' aria-label='unit'>"
                    "<input class='tx sm2' name='need' value='%s' inputmode='decimal' aria-label='needed per month'>"
                    "<button class='mini' name='op' value='edit'>Save</button>"
                    "<button class='mini' name='op' value='%s'>%s</button></form></td></tr>"
                    % ("" if it["active"] else " class='off'", BASE, it["id"], _esc(it["name"]), _esc(it["unit"]), qty(it["need"]),
                       "retire" if it["active"] else "restore", "Retire" if it["active"] else "Restore"))
    hist = []
    for c in con.execute("SELECT * FROM mj_home_count WHERE id IN (SELECT MAX(id) FROM mj_home_count GROUP BY month) ORDER BY month DESC LIMIT 6"):
        ls = list(con.execute("SELECT * FROM mj_home_line WHERE count_id=?", (c["id"],)))
        earlier = con.execute("SELECT COUNT(*) FROM mj_home_count WHERE month=? AND id<?", (c["month"], c["id"])).fetchone()[0]
        hist.append("<li>%s: counted by %s %s · to order: %s%s</li>" % (mname(c["month"], year=True), _esc(name_of(c["saved_by"])),
                                                                         when(c["saved_at"]), order_summary(ls, "en"),
                                                                         (" (%d earlier save(s) kept)" % earlier) if earlier else ""))
    out.append("<details class='card' open><summary><b>SETTINGS · HOME MEDICINES</b> <span class='sm'>you keep this list</span></summary>"
               "<p class='sm'>Name · unit · needed per month</p><table class='grid'><tbody>%s</tbody></table>"
               "<form method='post' action='%s/owner/item' class='row add'><input class='tx' name='name' maxlength='60' placeholder='Medicine name'>"
               "<input class='tx sm2' name='unit' maxlength='20' placeholder='unit (strips)'>"
               "<input class='tx sm2' name='need' inputmode='decimal' placeholder='per month'>"
               "<button class='mini' name='op' value='add'>+ Add a medicine</button></form>"
               "<p class='sm'>MONTH-END COUNT — you or Darpan. Enter what is left at home; the page shows what to order: needed − left.</p>"
               "<ul class='hist'>%s</ul></details>"
               % ("".join(rows) or "<tr><td class='sm'>No medicines yet.</td></tr>", BASE, "".join(hist) or "<li>No count saved yet.</li>"))

    # ---- vehicles and papers
    grid = []
    for vv in vehicles(con):
        cells = []
        for k, _h, en in PAPERS:
            r = next((x for x in prow if x["vehicle"]["id"] == vv["id"] and x["paper"] == k), None)
            tag = (" <span class='due'>due</span>" if r and r["due"] else "")
            cells.append("<td%s><div>%s%s</div><form method='post' action='%s/owner/paper' class='pd'>"
                         "<input type='hidden' name='vehicle_id' value='%d'><input type='hidden' name='paper' value='%s'>"
                         "<input type='date' name='expiry' value='%s' aria-label='%s %s expiry'><button class='mini'>Save</button></form></td>"
                         % (" class='amb'" if r and r["due"] else "", dmy(r["expiry"]) if r and r["expiry"] else "—", tag, BASE, vv["id"], k,
                            (r["expiry"] or "") if r else "", _esc(vv["name"]), en))
        grid.append("<tr><td><b>%s</b></td>%s</tr>" % (_esc(vv["name"]), "".join(cells)))
    vrows = []
    for vv in vehicles(con, active_only=False):
        vrows.append("<tr%s><td><form method='post' action='%s/owner/vehicle' class='row'><input type='hidden' name='id' value='%d'>"
                     "<input class='tx' name='name' value='%s' maxlength='40' aria-label='vehicle name'>"
                     "<label class='ck'><input type='checkbox' name='has_spare' value='1'%s> stepney, jack and spanner</label>"
                     "<button class='mini' name='op' value='edit'>Save</button>"
                     "<button class='mini' name='op' value='%s'>%s</button></form></td></tr>"
                     % ("" if vv["active"] else " class='off'", BASE, vv["id"], _esc(vv["name"]), " checked" if vv["has_spare"] else "",
                        "retire" if vv["active"] else "restore", "Retire" if vv["active"] else "Restore"))
    vh = []
    for c in con.execute("SELECT * FROM mj_vehicle_check WHERE id IN (SELECT MAX(id) FROM mj_vehicle_check GROUP BY month) ORDER BY month DESC LIMIT 6"):
        miss = missing_of({ln["id"]: ln for ln in con.execute("SELECT * FROM mj_vehicle_check_line WHERE check_id=?", (c["id"],))})
        vh.append("<li>%s: checked by %s %s · %s</li>" % (mname(c["month"], year=True), _esc(name_of(c["saved_by"])), when(c["saved_at"]),
                                                          "; ".join("<span class='nahi'>%s: no %s</span>" % (_esc(va), item_label(it, "en").lower())
                                                                    for va, it in miss) or "everything present"))
    ph = []
    for r in con.execute("SELECT p.*, v.name AS vname FROM mj_paper p JOIN mj_vehicle v ON v.id=p.vehicle_id ORDER BY p.id DESC LIMIT 30"):
        ph.append("<li>%s · %s: %s (entered by %s %s)</li>" % (_esc(r["vname"]), item_label(r["paper"], "en"), dmy(r["expiry"]),
                                                              _esc(name_of(r["entered_by"])), when(r["entered_at"])))
    out.append("<details class='card' open><summary><b>VEHICLE PAPERS · REMINDERS</b></summary>"
               "<p class='sm'>On Darpan's list and yours: pollution %s before, insurance %s before, RC %s before — until you enter the new date. "
               "A new date replaces the old one; the old one is kept below.</p>"
               "<table class='grid pg'><thead><tr><th></th><th>Pollution</th><th>Insurance</th><th>RC</th></tr></thead><tbody>%s</tbody></table>"
               "<details><summary class='sm'>Paper date history</summary><ul class='hist'>%s</ul></details>"
               "<div class='sec'>VEHICLES</div><table class='grid'><tbody>%s</tbody></table>"
               "<form method='post' action='%s/owner/vehicle' class='row add'><input class='tx' name='name' maxlength='40' placeholder='Vehicle name'>"
               "<label class='ck'><input type='checkbox' name='has_spare' value='1'> stepney, jack and spanner</label>"
               "<button class='mini' name='op' value='add'>+ Add a vehicle</button></form>"
               "<div class='sec'>VEHICLE CHECKS</div><ul class='hist'>%s</ul></details>"
               % (lead_words(setting(con, "lead.pollution")), lead_words(setting(con, "lead.insurance")), lead_words(setting(con, "lead.rc")),
                  "".join(grid), "".join(ph) or "<li>No date entered yet.</li>", "".join(vrows), BASE, "".join(vh) or "<li>No check saved yet.</li>"))

    # ---- lead times and floors
    def lead_in(k, label):
        n, unit = lead_split(setting(con, "lead." + k))
        return ("<label class='ld'>%s <input class='tx sm2' name='lead_%s_n' value='%d' inputmode='numeric'>"
                "<select name='lead_%s_u'><option value='days'%s>days</option><option value='months'%s>months</option></select> before</label>"
                % (label, k, n, k, " selected" if unit == "days" else "", " selected" if unit == "months" else ""))
    out.append("<details class='card'><summary><b>LEAD TIMES · FIRST MONTHS</b></summary><form method='post' action='%s/owner/settings'>"
               "%s%s%s"
               "<label class='ld'>Home medicines: first count for <input class='tx sm2' name='home_floor' value='%s'></label>"
               "<label class='ld'>Vehicle check: first month <input class='tx sm2' name='vehicle_floor' value='%s'></label>"
               "<label class='ld'>Expiry clear-out: first month <input class='tx sm2' name='expiry_floor' value='%s'></label>"
               "<p class='sm'>Months as YYYY-MM.</p><button class='mini' type='submit'>Save settings</button></form></details>"
               % (BASE, lead_in("pollution", "Pollution"), lead_in("insurance", "Insurance"), lead_in("rc", "RC"),
                  _esc(setting(con, "home.floor")), _esc(setting(con, "vehicle.floor")), _esc(setting(con, "expiry.floor"))))

    # ---- expiry outcomes
    er = []
    for r in e["rows"]:
        ln, o = r["line"], r["outcome"]
        er.append("<tr><td>%s<div class='sm'>Batch %s · Exp %s</div></td><td>%s</td></tr>"
                  % (_esc(ln["item"]), _esc(ln["batch"] or "—"), exp_mmyy(ln["expiry"]),
                     ("%s <span class='sm'>by %s %s</span>" % (outcome_label(o["outcome"], "en"), _esc(name_of(o["saved_by"])), when(o["saved_at"])))
                     if o is not None else "<span class='ambc'>waiting</span>"))
    oh = []
    for o in con.execute("SELECT * FROM mj_expiry_outcome ORDER BY id DESC LIMIT 40"):
        oh.append("<li>%s · batch %s · exp %s: %s (%s %s)</li>" % (_esc(o["item"]), _esc(o["batch"] or "—"), exp_mmyy(o["expiry"]),
                                                                   outcome_label(o["outcome"], "en"), _esc(name_of(o["saved_by"])), when(o["saved_at"])))
    out.append("<details class='card' open><summary><b>EXPIRY OUTCOMES</b> <span class='sm'>the newest expiry list%s</span></summary>"
               "<table class='grid'><tbody>%s</tbody></table><details><summary class='sm'>All outcomes</summary><ul class='hist'>%s</ul></details></details>"
               % ((" as on %s" % dmy(e["run"]["export_as_on"] or e["run"]["today"])) if e["run"] is not None else "",
                  "".join(er) or "<tr><td class='sm'>No expired line.</td></tr>", "".join(oh) or "<li>None yet.</li>"))
    return _shell("Darpan — monthly jobs", "".join(out), "en")


def _owner_post(what):
    return redirect(BASE + "/owner?msg=saved&what=%s" % what)


@bp.route(BASE + "/owner/item", methods=["POST"])
def owner_item():
    u = _owner()
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    op, who, at = request.form.get("op") or "", _who(u), _stamp()
    name = " ".join((request.form.get("name") or "").split())[:60]
    unit = " ".join((request.form.get("unit") or "").split())[:20]
    need = (request.form.get("need") or "").strip()
    if op in ("add", "edit") and (not name or not unit or not QTY_RE.match(need) or float(need) <= 0):
        return redirect(BASE + "/owner?msg=bad")
    if op == "add":
        rid = con.execute("INSERT INTO mj_home_item (name, unit, need, active, added_at, added_by) VALUES (?,?,?,1,?,?)",
                          (name, unit, float(need), at, who)).lastrowid
        con.commit()
        _audit_safe(con, "mj_home_item", rid, "add", None, dict(name=name, unit=unit, need=float(need)), who)
        return _owner_post("item")
    try:
        iid = int(request.form.get("id") or 0)
    except ValueError:
        iid = 0
    it = con.execute("SELECT * FROM mj_home_item WHERE id=?", (iid,)).fetchone()
    if it is None or op not in ("edit", "retire", "restore"):
        return redirect(BASE + "/owner?msg=bad")
    before = dict(name=it["name"], unit=it["unit"], need=it["need"], active=it["active"])
    if op == "edit":
        con.execute("UPDATE mj_home_item SET name=?, unit=?, need=?, changed_at=?, changed_by=? WHERE id=?", (name, unit, float(need), at, who, iid))
        after = dict(before, name=name, unit=unit, need=float(need))
    else:
        act = 0 if op == "retire" else 1
        con.execute("UPDATE mj_home_item SET active=?, changed_at=?, changed_by=? WHERE id=?", (act, at, who, iid))
        after = dict(before, active=act)
    con.commit()
    _audit_safe(con, "mj_home_item", iid, op, before, after, who)
    return _owner_post("item")


@bp.route(BASE + "/owner/vehicle", methods=["POST"])
def owner_vehicle():
    u = _owner()
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    op, who, at = request.form.get("op") or "", _who(u), _stamp()
    name = " ".join((request.form.get("name") or "").split())[:40]
    spare = 1 if request.form.get("has_spare") == "1" else 0
    if op in ("add", "edit") and not name:
        return redirect(BASE + "/owner?msg=bad")
    if op == "add":
        pos = (con.execute("SELECT COALESCE(MAX(pos),0) FROM mj_vehicle").fetchone()[0] or 0) + 1
        rid = con.execute("INSERT INTO mj_vehicle (name, has_spare, active, pos, added_at, added_by) VALUES (?,?,1,?,?,?)",
                          (name, spare, pos, at, who)).lastrowid
        con.commit()
        _audit_safe(con, "mj_vehicle", rid, "add", None, dict(name=name, has_spare=spare), who)
        return _owner_post("vehicle")
    try:
        vid = int(request.form.get("id") or 0)
    except ValueError:
        vid = 0
    v = con.execute("SELECT * FROM mj_vehicle WHERE id=?", (vid,)).fetchone()
    if v is None or op not in ("edit", "retire", "restore"):
        return redirect(BASE + "/owner?msg=bad")
    before = dict(name=v["name"], has_spare=v["has_spare"], active=v["active"])
    if op == "edit":
        con.execute("UPDATE mj_vehicle SET name=?, has_spare=?, changed_at=?, changed_by=? WHERE id=?", (name, spare, at, who, vid))
        after = dict(before, name=name, has_spare=spare)
    else:
        act = 0 if op == "retire" else 1
        con.execute("UPDATE mj_vehicle SET active=?, changed_at=?, changed_by=? WHERE id=?", (act, at, who, vid))
        after = dict(before, active=act)
    con.commit()
    _audit_safe(con, "mj_vehicle", vid, op, before, after, who)
    return _owner_post("vehicle")


@bp.route(BASE + "/owner/paper", methods=["POST"])
def owner_paper():
    u = _owner()
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    who = _who(u)
    try:
        vid = int(request.form.get("vehicle_id") or 0)
    except ValueError:
        vid = 0
    paper = request.form.get("paper") or ""
    exp = (request.form.get("expiry") or "").strip()
    v = con.execute("SELECT * FROM mj_vehicle WHERE id=?", (vid,)).fetchone()
    try:
        ok = bool(DAY_RE.match(exp)) and dt.date.fromisoformat(exp).year < 2100
    except ValueError:
        ok = False
    if v is None or paper not in [k for k, _h, _e in PAPERS] or not ok:
        return redirect(BASE + "/owner?msg=bad")
    prev = con.execute("SELECT expiry FROM mj_paper WHERE vehicle_id=? AND paper=? ORDER BY id DESC LIMIT 1", (vid, paper)).fetchone()
    rid = con.execute("INSERT INTO mj_paper (vehicle_id, paper, expiry, entered_at, entered_by) VALUES (?,?,?,?,?)",
                      (vid, paper, exp, _stamp(), who)).lastrowid
    con.commit()
    _audit_safe(con, "mj_paper", rid, "date", dict(expiry=prev[0]) if prev else None, dict(vehicle=v["name"], paper=paper, expiry=exp), who)
    return _owner_post("paper")


@bp.route(BASE + "/owner/settings", methods=["POST"])
def owner_settings():
    u = _owner()
    if u is None:
        return _denied("hi")
    con = _db()
    _ensure(con)
    who, new = _who(u), {}
    for k in ("pollution", "insurance", "rc"):
        n = (request.form.get("lead_%s_n" % k) or "").strip()
        unit = request.form.get("lead_%s_u" % k) or "days"
        if not re.match(r"^\d{1,3}$", n) or unit not in ("days", "months") or int(n) > (365 if unit == "days" else 12):
            return redirect(BASE + "/owner?msg=bad")
        new["lead." + k] = "-%d %s" % (int(n), ("month" if int(n) == 1 else "months") if unit == "months" else "days")
    for k in ("home", "vehicle", "expiry"):
        m = (request.form.get("%s_floor" % k) or "").strip()
        if not YM_RE.match(m):
            return redirect(BASE + "/owner?msg=bad")
        new[k + ".floor"] = m
    changed = {}
    for k, val in new.items():
        old = setting(con, k)
        if val != old:
            _set(con, k, val, who)
            changed[k] = (old, val)
    con.commit()
    if changed:
        _audit_safe(con, "mj_setting", None, "settings", {k: a for k, (a, _b) in changed.items()}, {k: b for k, (_a, b) in changed.items()}, who)
    return _owner_post("settings")


# ============================================================================================ the shell
def _shell(title, body, lang):
    return """<!doctype html><html lang="%s"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#3c464e;--line:#8a9aa6;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;--entry:#fffbe6;--amb:#fff1cc;--ambk:#8a5a00;--red:#8c2f2f;--grn:#2c6e2f}
*{box-sizing:border-box}
body{margin:0;padding:14px;background:var(--bg);color:var(--ink);font:18px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;max-width:860px;margin:0 auto}
h1{font-size:21px;margin:0 0 10px;color:var(--accent)}h2{font-size:20px;margin:0 0 8px;color:var(--accent)}h3{margin:0 0 8px;font-size:19px}
h2.pt{margin:6px 0 6px}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:12px;margin:0 0 12px;overflow-x:auto}
details.card>summary{cursor:pointer;min-height:44px;padding:6px 0}
.mut{color:var(--mut);font-size:16px}.sm{font-size:14px;color:var(--mut);font-weight:400}
.sec{font-size:14px;font-weight:700;letter-spacing:.06em;color:var(--mut);margin:14px 0 6px}
a.back{display:inline-block;min-height:44px;line-height:44px;color:var(--accent)}
a.job{display:block;min-height:64px;padding:12px;margin:0 0 10px;border:2px solid var(--accent);border-radius:10px;background:#fff;color:var(--ink);text-decoration:none}
a.job .jt{display:flex;justify-content:space-between;gap:8px;font-weight:700;font-size:19px}a.job .js{display:block;font-size:15px;color:var(--mut)}
.chip{font-size:14px;padding:2px 10px;border-radius:12px;background:#e3e8eb;border:1px solid var(--line);white-space:nowrap}
.chip.due{background:var(--amb);border-color:var(--ambk);color:var(--ambk)}.chip.done{background:#dff0d8;border-color:var(--grn);color:var(--grn)}
table.grid{width:100%%;border-collapse:collapse;font-size:16px;background:var(--paper)}.grid th,.grid td{border:1px solid var(--line);padding:8px;vertical-align:top;text-align:left}
.grid th{font-size:13px;letter-spacing:.04em;color:var(--mut)}
.r{text-align:right!important;white-space:nowrap}
td.mg{font-size:22px;font-weight:700}
input.num{width:100%%;min-width:70px;min-height:52px;font-size:24px;padding:6px 10px;border:2px solid #5b6b76;border-radius:8px;text-align:right;background:var(--entry)}
input.tx,select{min-height:44px;font-size:17px;padding:6px 8px;border:2px solid #5b6b76;border-radius:8px;background:var(--entry);max-width:100%%}
input.tx{width:220px}input.tx.sm2{width:110px}input[type=date]{min-height:44px;font-size:16px;border:2px solid #5b6b76;border-radius:8px;padding:4px}
.foot{font-size:20px;margin:10px 0}
button.save{width:100%%;min-height:56px;background:var(--accent);color:#fff;border:0;border-radius:10px;font-size:20px;font-weight:700;cursor:pointer;margin:6px 0 10px}
button.mini{min-height:44px;min-width:64px;background:var(--paper);color:var(--accent);border:2px solid var(--accent);border-radius:8px;font-size:16px;padding:6px 10px;cursor:pointer}
a.btn{display:inline-block;min-height:44px;line-height:40px;border:2px solid var(--accent);color:var(--accent);border-radius:9px;padding:0 12px;text-decoration:none;background:var(--paper);font-size:16px}
form.row{display:flex;flex-wrap:wrap;gap:6px;align-items:center}form.row.add{margin-top:10px}
form.pd{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.hn{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:6px 0;border-top:1px solid #d6dde2}.hn .hl{flex:1 0 140px;font-weight:600}
label.opt{position:relative;display:inline-block}label.opt input{position:absolute;opacity:0;width:1px;height:1px}
label.opt span{display:inline-block;min-width:76px;min-height:48px;line-height:44px;text-align:center;padding:0 14px;border:2px solid var(--grn);border-radius:10px;color:var(--grn);background:#fff;font-weight:700;cursor:pointer}
label.opt.no span{border-color:var(--red);color:var(--red)}
label.opt input:checked+span{background:var(--grn);color:#fff}label.opt.no input:checked+span{background:var(--red);color:#fff}
label.opt input:focus-visible+span{outline:3px solid #1f5fad;outline-offset:2px}
.opts{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.warn{margin-top:8px;padding:8px 10px;background:var(--amb);border-left:6px solid var(--ambk);font-size:16px}
.card.remind{border-color:var(--ambk);background:var(--amb)}.card.remind .rt{font-weight:700;font-size:19px}
td.amb{background:var(--amb)}span.due,span.ambc{color:var(--ambk);font-weight:700}span.due{background:var(--amb);border:1px solid var(--ambk);border-radius:10px;padding:0 8px;font-size:13px}
span.okc{color:var(--grn);font-weight:700}span.nahi{color:var(--red);font-weight:700}
tr.off td{opacity:.6}label.ck{min-height:44px;display:inline-flex;align-items:center;gap:6px;font-size:15px}
label.ck input{width:22px;height:22px}label.ld{display:block;margin:8px 0}
ul.hist{margin:6px 0 0 18px;padding:0;font-size:15px}
.saved{background:#dff0d8;border:3px solid var(--grn);border-radius:12px;padding:12px 14px;margin:0 0 10px;font-size:18px}
.saved .sv1{font-size:24px;font-weight:800;color:#1e5a22;margin:0 0 6px}
.svt{border-collapse:collapse}.svt td{padding:3px 14px 3px 0;vertical-align:top}.svt td:first-child{color:var(--mut)}
.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:10px 14px;margin-bottom:12px}
@media (max-width:600px){body{padding:10px 16px}h1{font-size:18px}.grid td,.grid th{padding:6px}input.tx{width:100%%}}
</style></head><body><h1>%s</h1>
%s</body></html>""" % (lang, _esc(title), _esc(title), body)
