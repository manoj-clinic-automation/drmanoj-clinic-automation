#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xray_film.py -- kit S688_XRAY_FILM_LOG (31-Oct-2026, the parent, session 372). The X-ray film log.

THE OWNER'S RULINGS (31-Oct-2026, with his mock-up "X-ray film log"), folded:
  1. TWO FILM SIZES, 8x10 and 11x14. Each box loaded into the Fuji printer holds 150 films (setting box.films).
  2. THE MORNING COUNT (the owner, 20:23 IST 31-Oct-2026: the Fuji machine's screen shows the FILMS LEFT in the loaded box, per
     size). Each morning reception types "Machine mein kitni film bachi hain" for each size, 0 to 150; Shavez fills it when
     reception is away. One Save for the day (both sizes), then the Saved card. A later save the same day supersedes (the
     earlier is kept: xf_count is append-only). Staff are refused a figure above a box's films (150), and a figure HIGHER than
     the last count unless that count was 20 or less (setting load.max_left) and "Haan, naya box lagaya gaya" is ticked -- a
     typo one film up must never become a box load ("Pichhli ginti mein X film bachi thi -- badhi kaise? Dr Manoj se confirm
     karaiye"). The owner may save either: above 150 with a note; a higher figure with the tick or a note. (The old 200-used
     rule is gone: with these two rules staff can never reach it.) The owner corrects, voids or un-voids any past morning (append-only,
     audited, the old figure kept; a voided morning joins the next count); every figure is worked out again from the figures.
     The count is to be taken before the first X-ray of the morning (the page says so).
  3. FILMS LEFT = the newest figure. FILMS USED between two counts: previous - today when today is not higher; when today is
     HIGHER a new box went in between -- ONE automatic box load on that day ("naya box (machine se pata chala)") and used =
     previous + (150 - today). A missed morning is not typed later -- the next count spans the days in between ("joined to
     the next count"). There is no box tap and no counter: the machine's own figure says it all. A count saved at or after 11:00
     (a stand-in, after X-rays started) is shown with the next span as ONE ("der se ginti -- do din milake"); a box load across
     more than 3 uncounted days says "check" on the owner's page (two boxes could have gone in).
     Days left = films left / the average daily use over the last 30 days of counts (at least 3 days between the
     first and the last count of that window; less is "too little data", and then no number and no order line).
  4. THE FILM LOG (one page): per day, the machine's films per size against the films on that day's PAID X-ray slips per
     size, and the gap -- shown to every one who has the page, never with a reason asked. Staff read it in Roman Hinglish,
     the owner in English. Monthly: days with a gap, mornings not counted. Excel of the month.
  5. FILMS PER STUDY: the owner's rate list (owner_service, kind 'xray') keeps no film size, only his own tag "(11 x 14)" in
     some names. xf_study holds each study's size and films, seeded ONCE from his words: 11x14 where the name carries his tag
     or names a wrist, pelvis both hips, femur or the frog-leg view; Knee studies (K/S) two 8x10 films; a one-part "AP &
     Lateral" study one 8x10 film ("AP and lateral are usually ONE film"); EVERY OTHER study "size not set" -- never guessed.
     He changes any of them on his page. A slip line with no study (typed free) is "size not set". A slip line with side B
     (both sides) takes twice the study's films, unless he marked the study "both sides on one film"; a study whose name
     itself starts with "Both" never doubles.
  6. THE ORDER LINE. When a size's days left fall under 10 (setting order.days, one for both sizes), "<size> film mangwaiye --
     1 box" is on Shavez's Aaj list and on the owner's page and console, with a WhatsApp link (wa.me, the message
     prefilled: clinic, size, 1 box) to the contact marked "films supplier" (a mobile) -- while no SPARE box is on the shelf.
     Spare boxes per size from a start day (default: the install day): the opening boxes the owner sets, + every box billed on
     or after that day (a bill of N boxes counts N), - one per box load the figures show -- NOT floored: below 0 is "N box load
     hua, bill abhi nahi aaya", and a later bill first pays for those. The line is due while days left < 10 and spare <= 0; a
     box load clears it too (films left back up). A film bill with no size is listed for the owner, who says 8x10 / 11x14 / not
     film in one tap. A film bill whose lines name no size is
     "size unknown" (the Scan App's "small film" group holds 8x10 AND 10x12): shown on the owner's page, counts nothing. A
     film bill kept on a machine record that is also on the desk (xray_costs' own match) counts once, on the desk.
  7. CONTACTS: name, firm, role (films supplier / Fuji service engineer / Fuji support / other), phone, email; the owner
     edits, staff see and tap Call / WhatsApp / Email. Seeded with ONE row and no number: Nigam, Jugnu Medicos (Fuji), films
     supplier. Numbers are typed on the page and live in the database only (F-185); a number never rides in a URL --
     posts carry it in the body; tel: and wa.me links in the page are the only places it is shown. +91 goes only in front of
     a ten-digit mobile (6-9); any other number is dialled as typed (a leading 0 or 1800 kept) and has no WhatsApp button.
  8. THE X-RAY LIST from 1-Oct-2026 (setting list.from): every paid X-ray slip line, day by day -- date, slip number, clinic
     ID, patient (as the slip book shows the name), study, film size, films, paid mode. Month picker and Excel. It replaces the
     manual Excel; the old Excel is left alone.

WHO REACHES WHAT -- at the server. /finance/slips/film/... is unit 'slips' by finance_app._unit_for_path (its own prefix).
  makers shavez, alisha, shivani (and the shared login 'reception' if it is ever given a slips row) -> the Hinglish pages
  the slips checkers (manoj, bhawna)  -> the English pages; ONLY the owner (manoj) changes contacts, settings, sizes, box taps
  other slips makers (awdhesh, bhati) and the viewer (sukhveer) -> 403 here (no job on these pages); a login with no slips
  row never gets past the front gate (302).

READ ONLY, NEVER WRITTEN: slip, slip_item, owner_service (finance.db) and the Scan App's assets.db (opened mode=ro). The
purchase rule cannot be read by an Aaj line (its SQL sees finance.db only), so every page of this module copies the film
bills it finds in assets.db into xf_purchase (src-keyed; a bill gone from the desk is marked gone, a re-read size, date or
box count updated) -- the order line reads that. Reception's morning page loads every morning, so the copy is at most a day
old. The Scan App's columns read: bills (id, created_at, vendor, bill_date, subgroup, status, dup_of), bill_items (bill_id,
item_name, quantity), xray_film_line (id, asset_id, asset_created_at, size, boxes, voided_at), assets (id, created_at,
purchase_date, vendor). Its own tables xf_* are made on the first request (F-303) and by the kit's data step. Every save adds an audit_log row.
XRAYFILM_NOW=<iso> pins the clock for the walk; ASSETS_DB names the Scan App's database (default /root/assetapp/assets.db).
No patient name, no number, no secret in this file (F-185).
"""
import datetime as dt
import io
import os
import re
import sqlite3
import urllib.parse

from flask import Blueprint, Response, redirect, request

bp = Blueprint("xray_film", __name__)
_db = None
_require = None
_audit = None
UNIT = "slips"
VERSION = "S688-XRAY-FILM-1.0"
_schema_done = False
BASE = "/finance/slips/film"
OWNER = "manoj"                                                     # the only login that changes contacts, settings, sizes
STAFF = ("shavez", "alisha", "shivani", "reception")                # the slips makers with this job
SIZES = (("8x10", "8×10"), ("11x14", "11×14"))
SIZE_KEYS = tuple(s[0] for s in SIZES)
SIZE_LABEL = dict(SIZES)
ROLES = (("films_supplier", "Films supplier"), ("fuji_service", "Fuji service engineer"), ("fuji_support", "Fuji support"),
         ("other", "Other"))
ROLE_LABEL = dict(ROLES)
DEFAULTS = {"order.days": "10", "box.films": "150", "standin.after": "11:00", "count.from": "2026-11-01", "list.from": "2026-10-01",
            "spare.from": "2026-11-01", "spare.open.8x10": "0", "spare.open.11x14": "0", "load.max_left": "20",
            "bill.max_boxes": "10"}
WINDOW_DAYS = 30                                                    # the average: the last 30 days of counts
MIN_SPAN = 3                                                        # ... over at least 3 days, else "too little data"
PEND_HI = "der se ginti — kal ki ginti ke saath judegi"         # the newest late count, until the next count joins it
CHECK_GAP_DAYS = 3                                                  # a box load across more than 3 uncounted days: "check" (two boxes?)
SURE_TIMES, SURE_MIN = 3, 30                                        # staff confirm a fall of more than 3x the average AND more than 30
CLINIC = "Dr Manoj Agarwal Clinic, Bareilly"
SEED_CONTACT = ("Nigam", "Jugnu Medicos (Fuji)", "films_supplier")
FILM_SUBS = ("xray_small", "xray_11x14", "xray")                    # the Scan App's X-ray film groups (sorting_desk "xray")
SIZE_RE = re.compile(r"(\d{1,2})\s*(?:\*|x|X|×)\s*(\d{1,2})")      # as xray_costs.size_of
YM_RE = re.compile(r"^(20\d\d)-(0[1-9]|1[0-2])$")
DAY_RE = re.compile(r"^20\d\d-\d\d-\d\d$")
HM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
CNT_RE = re.compile(r"^\d{1,3}$")                                    # films left on the machine: 0..999 (staff: up to box.films)
EMAIL_RE = re.compile(r"^[^@\s<>'\"]{1,64}@[^@\s<>'\"]{1,120}\.[A-Za-z]{2,12}$")
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")
DAYS_EN = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
DAYS_HI = ("Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar", "Itvaar")
MON_HI = ("Janvari", "Farvari", "March", "April", "Mai", "June", "July", "Agast", "Sitambar", "Oktoober", "Navambar", "Disambar")

SCHEMA = """
CREATE TABLE IF NOT EXISTS xf_setting (id INTEGER PRIMARY KEY, key TEXT NOT NULL, value TEXT NOT NULL DEFAULT '',
  set_at TEXT NOT NULL, set_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS xf_save (id INTEGER PRIMARY KEY, day TEXT NOT NULL, saved_at TEXT NOT NULL, saved_by TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'count', note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS xf_count (id INTEGER PRIMARY KEY, save_id INTEGER NOT NULL, day TEXT NOT NULL,
  size TEXT NOT NULL CHECK (size IN ('8x10','11x14')), remaining INTEGER NOT NULL, saved_at TEXT NOT NULL, saved_by TEXT NOT NULL,
  void INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS xf_count_size_day ON xf_count (size, day);
CREATE TABLE IF NOT EXISTS xf_purchase (id INTEGER PRIMARY KEY, src TEXT NOT NULL UNIQUE, size TEXT NOT NULL DEFAULT '',
  bill_day TEXT NOT NULL DEFAULT '', boxes REAL, vendor TEXT NOT NULL DEFAULT '', seen_at TEXT NOT NULL, gone_at TEXT NOT NULL DEFAULT '',
  held INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS xf_bill_qty (id INTEGER PRIMARY KEY, src TEXT NOT NULL, boxes REAL NOT NULL, set_at TEXT NOT NULL,
  set_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS xf_bill_size (id INTEGER PRIMARY KEY, src TEXT NOT NULL, size TEXT NOT NULL CHECK (size IN ('8x10','11x14','none')),
  set_at TEXT NOT NULL, set_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS xf_study (id INTEGER PRIMARY KEY, service_id INTEGER NOT NULL, size TEXT NOT NULL DEFAULT '',
  films INTEGER NOT NULL DEFAULT 1, both_one INTEGER NOT NULL DEFAULT 0, set_at TEXT NOT NULL, set_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS xf_contact (id INTEGER PRIMARY KEY, name TEXT NOT NULL, firm TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL DEFAULT 'other', phone TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1,
  added_at TEXT NOT NULL, added_by TEXT NOT NULL, changed_at TEXT NOT NULL DEFAULT '', changed_by TEXT NOT NULL DEFAULT '');
"""
TABLES = ("xf_setting", "xf_save", "xf_count", "xf_purchase", "xf_bill_size", "xf_bill_qty", "xf_study", "xf_contact")


# ============================================================================================ mount and schema
def init(app, db_getter, require_fn, audit_fn=None, unit="slips"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    return bp


def study_rule(name, code):
    """The seed's size and films for one X-ray study of the owner's rate list, from his words only: (size, films)."""
    n = " ".join(str(name or "").lower().split())
    c = str(code or "").upper()
    if re.search(r"\b11\s*[x*×]\s*14\b", n) or any(k in n for k in ("wrist", "pelvis both hips", "femur", "frog")):
        return "11x14", 1
    if c == "KS" or "knee studies" in n or "(k/s)" in n:
        return "8x10", 2
    if "both" not in n and re.search(r"\bap\s*(?:&|and)\s*lateral\b", n):
        return "8x10", 1
    return "", 1


def ensure(con):
    """The xf_* tables (CREATE ... IF NOT EXISTS); the first time xf_study is made, the seed of each X-ray study; the first
    time xf_contact is made, the one supplier row (no number). Called on the first request and by the data step (cfg_s688)."""
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.executescript(SCHEMA)
    if "held" not in {r[1] for r in con.execute("PRAGMA table_info(xf_purchase)")}:
        con.execute("ALTER TABLE xf_purchase ADD COLUMN held INTEGER NOT NULL DEFAULT 0")     # a copy made before the quantity hold
    at = _stamp()
    if "xf_study" not in have and con.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0] == 0:
        try:
            rows = list(con.execute("SELECT id, name, code FROM owner_service WHERE kind='xray' ORDER BY id"))
        except sqlite3.Error:
            rows = []
        for r in rows:
            size, films = study_rule(r[1], r[2])
            con.execute("INSERT INTO xf_study (service_id, size, films, set_at, set_by) VALUES (?,?,?,?,?)",
                        (r[0], size, films, at, "S688 seed"))
    if not con.execute("SELECT 1 FROM xf_setting WHERE key='spare.from'").fetchone():
        # the spare-box stock starts counting on the install day (the owner moves it, and sets the opening boxes, on his page)
        con.execute("INSERT INTO xf_setting (key, value, set_at, set_by) VALUES ('spare.from', ?, ?, 'S688 install')", (_today().isoformat(), at))
    if "xf_contact" not in have and con.execute("SELECT COUNT(*) FROM xf_contact").fetchone()[0] == 0:
        con.execute("INSERT INTO xf_contact (name, firm, role, phone, email, active, added_at, added_by) VALUES (?,?,?,'','',1,?,?)",
                    (SEED_CONTACT[0], SEED_CONTACT[1], SEED_CONTACT[2], at, "S688 seed"))
    con.commit()


def _ensure(con):
    global _schema_done
    if _schema_done:
        return
    ensure(con)
    _schema_done = True


# ============================================================================================ small things
def _now():
    v = os.environ.get("XRAYFILM_NOW", "")
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


def _d(iso):
    return dt.date.fromisoformat(str(iso)[:10])


def dm(iso):
    try:
        d = _d(iso)
        return "%02d-%s" % (d.day, MON[d.month - 1])
    except (TypeError, ValueError):
        return str(iso or "")


def ddm(iso, lang="en"):
    try:
        d = _d(iso)
    except (TypeError, ValueError):
        return str(iso or "")
    return "%s %02d-%s" % ((DAYS_EN if lang == "en" else DAYS_HI)[d.weekday()][:3 if lang == "en" else 99], d.day, MON[d.month - 1])


def when(stamp):
    s = str(stamp or "")
    return ("%s %s" % (dm(s[:10]), s[11:16])) if len(s) >= 16 else s


def mname(ym, lang="en"):
    y, m = int(ym[:4]), int(ym[5:7])
    return "%s %d" % ((MONTHS if lang == "en" else MON_HI)[m - 1], y)


def ym_shift(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) - 1 + k
    return "%04d-%02d" % (y + m // 12, m % 12 + 1)


def month_days(ym):
    first = dt.date(int(ym[:4]), int(ym[5:7]), 1)
    nxt = dt.date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    return first, nxt - dt.timedelta(days=1)


def name_of(login):
    login = str(login or "")
    return {"manoj": "Dr Manoj", "bhawna": "Dr Bhawna"}.get(login, login.title())


def size_of(text):
    """'DHL 8*10 150SH' -> '8x10'; '11 x 14' -> '11x14'; '' when no size is written."""
    m = SIZE_RE.search(str(text or ""))
    if not m:
        return ""
    a, b = sorted((int(m.group(1)), int(m.group(2))))
    return "%dx%d" % (a, b)


def setting(con, key):
    r = con.execute("SELECT value FROM xf_setting WHERE key=? AND value <> '' ORDER BY id DESC LIMIT 1", (key,)).fetchone()
    return (r[0] if r else "") or DEFAULTS.get(key, "")


def _num_setting(con, key):
    try:
        return float(setting(con, key))
    except ValueError:
        return float(DEFAULTS[key])


def _audit_safe(con, table, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)
        con.commit()
    except Exception:                                                  # noqa: BLE001
        pass


def phone_digits(v):
    """A typed phone number -> its digits as typed (8 to 13; a leading 0 or 1800 kept), or '' when it is not one. A mobile typed
    with +91 / 91 in front is kept as its ten digits."""
    s = str(v or "").strip()
    if not re.match(r"^\+?[\d\s\-()]{6,24}$", s):
        return ""
    d = re.sub(r"\D", "", s)
    if len(d) == 12 and d.startswith("91") and d[2] in "6789":
        d = d[2:]
    return d if 8 <= len(d) <= 13 else ""


def is_mobile(d):
    """An Indian mobile: ten digits starting 6, 7, 8 or 9."""
    d = str(d or "")
    return len(d) == 10 and d.isdigit() and d[0] in "6789"


def tel_href(d):
    """+91 only in front of a ten-digit mobile; every other number dialled as typed (digits only)."""
    return ("tel:+91" + d) if is_mobile(d) else ("tel:" + str(d or ""))


def wa_href(d):
    """WhatsApp only for a ten-digit mobile (wa.me/91...); None for any other number."""
    return ("https://wa.me/91" + d) if is_mobile(d) else None


# ============================================================================================ who
def _user():
    """(user, lang, owner) or (None, None, None). Staff with this job read Hinglish; the slips checkers English."""
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return None, None, None
    have = set(u.get("roles") or [])
    who = str(u.get("user") or "")
    if "checker" in have:
        return u, "en", who == OWNER
    if who in STAFF:
        return u, "hi", False
    return None, None, None


def _who(u):
    return str((u or {}).get("user") or "")


def _denied(lang="hi"):
    if lang == "en":
        body = "<div class='card'><h2>Not permitted</h2><p>Your login has no job on these pages.</p></div>"
    else:
        body = "<div class='card'><h2>Yeh page aapke liye nahin hai</h2><p>Galti lage to Dr Manoj se kahiye.</p></div>"
    return _shell("X-ray film", body, lang), 403


# ============================================================================================ the films-left figures
def readings(con, size, upto):
    """The current figure of each counted morning -- the FILMS LEFT on the machine's screen (the newest save of that day, a
    voided day none) -- oldest first, up to `upto`: [{day, left, used, load, by, at}]. used = the previous figure - today's when
    today's is not higher; when today's is HIGHER a new box went in between (load=True: ONE box load, on this day) and used =
    previous + (box films - today), never below 0."""
    pb = int(_num_setting(con, "box.films"))
    rows = con.execute("SELECT c.day, c.remaining, c.saved_by, c.saved_at FROM xf_count c WHERE c.size=? AND c.day<=? AND c.void=0 AND c.id = "
                       "(SELECT MAX(q.id) FROM xf_count q WHERE q.size=c.size AND q.day=c.day) ORDER BY c.day", (size, str(upto))).fetchall()
    out, prev = [], None
    for r in rows:
        v = int(r[1])
        load = prev is not None and v > prev
        if prev is None:
            used = None
        elif not load:
            used = prev - v
        else:
            used = max(0, prev + pb - v)
        out.append(dict(day=r[0], left=v, used=used, load=load, by=r[2], at=r[3]))
        prev = v
    return out


def used_if(con, size, day, v):
    """(used, load) if `v` were the figure of `day` -- against the last counted morning before it; (None, False) when none."""
    prev = [r for r in readings(con, size, day) if r["day"] < str(day)]
    if not prev:
        return None, False
    p, pb = prev[-1]["left"], int(_num_setting(con, "box.films"))
    return ((p - v), False) if v <= p else (max(0, p + pb - v), True)


def needs_sure(con, size, day, v):
    """A staff figure that means MORE films used since the last count than 3x the 30-day average (as of the day before) AND
    more than 30 -- a typo too low (118 typed as 18) looks just like this: staff tick 'Haan, machine par yahi dikh raha hai'
    before it saves (never refused). No average yet: no check."""
    used, _ld = used_if(con, size, day, v)
    if used is None or used <= SURE_MIN:
        return False
    avg = size_state(con, size, _d(day) - dt.timedelta(days=1))["avg"]
    return avg is not None and used > SURE_TIMES * avg


def purchases_from(con, size, day):
    return list(con.execute("SELECT * FROM xf_purchase WHERE size=? AND gone_at='' AND bill_day >= ? ORDER BY bill_day, id", (size, day)))


def spare_boxes(con, size, upto):
    """The spare boxes of this size: the opening boxes (setting spare.open.<size>) + every box of a film bill of this size dated
    on or after the start day (setting spare.from; a bill of N boxes counts N, no quantity read counts 1) - one for every box
    load the figures show on or after it. NOT floored: below 0 means boxes loaded whose bills are not in yet -- a later bill
    first pays for those, and only a stock of 1 or more is a spare on the shelf (the order line errs toward asking)."""
    d0 = setting(con, "spare.from")
    try:
        s = float(setting(con, "spare.open." + size))
    except ValueError:
        s = 0.0
    billed = sum(float(r[0]) if r[0] is not None else 1.0 for r in con.execute(
        "SELECT boxes FROM xf_purchase WHERE size=? AND gone_at='' AND held=0 AND bill_day>=? AND bill_day<=?", (size, d0, str(upto))))
    loads = sum(1 for r in readings(con, size, upto) if r["load"] and r["day"] >= d0)
    return s + billed - loads


def spare_words(spare, lang):
    if spare < 0:
        n = int(round(-spare))
        return (("%d box ka bill abhi nahi aaya — pehle bill scan karaiye, phir order dekhiye" % n) if lang == "hi"
                else ("%d box(es) loaded with no bill yet — scan the bill first, then see about the order" % n))
    return "spare: %g box" % spare


def opening_set(con, size):
    """Has the owner saved the opening spare boxes of this size (a row of its own, even a 0)? Until then the spare stock
    starts from 0 and his page and the order card say so."""
    return con.execute("SELECT 1 FROM xf_setting WHERE key=? AND value<>'' LIMIT 1", ("spare.open." + size,)).fetchone() is not None


def day_reading(con, size, day):
    """The newest row of one size and day: (films left, void) or None."""
    r = con.execute("SELECT remaining, void FROM xf_count WHERE size=? AND day=? ORDER BY id DESC LIMIT 1", (size, str(day))).fetchone()
    return (r[0], r[1]) if r is not None else None


def size_state(con, size, today):
    """Everything the pages and the order line say about one size, by the same rule as the order duty's SQL (make_s688)."""
    rs = readings(con, size, today)
    nd = _num_setting(con, "order.days")
    st = dict(size=size, label=SIZE_LABEL[size], readings=rs, last=(rs[-1] if rs else None), left=None, avg=None, days=None, why="",
              due=False, bought=[], spare=0.0, loads=[r["day"] for r in rs if r["load"]], nd=nd, order_days=nd)
    if rs:
        st["left"] = float(rs[-1]["left"])                             # films left = the newest figure typed from the screen
    st["bought"] = purchases_from(con, size, setting(con, "spare.from"))
    st["spare"] = spare_boxes(con, size, today)
    lo = (today - dt.timedelta(days=WINDOW_DAYS)).isoformat()
    win = [r for r in rs if r["day"] >= lo]
    if win:
        d0 = win[0]["day"]
        after = [r for r in win if r["day"] > d0 and r["used"] is not None]
        if after:
            span = (_d(after[-1]["day"]) - _d(d0)).days
            if span >= MIN_SPAN:
                st["avg"] = sum(r["used"] for r in after) * 1.0 / span
    if st["avg"] is None:
        st["why"] = "little"
    elif st["avg"] <= 0:
        st["why"] = "nouse"
    if not rs:
        st["why"] = "nocount"
    if st["left"] is not None and st["avg"] is not None and st["avg"] > 0:
        st["days"] = st["left"] / st["avg"]
        st["due"] = bool(st["left"] < st["avg"] * nd and st["spare"] <= 0)
    return st


def supplier(con):
    """The first active contact marked films supplier: (row, digits) -- digits '' when no number is typed yet."""
    r = con.execute("SELECT * FROM xf_contact WHERE active=1 AND role='films_supplier' ORDER BY (phone='') , id LIMIT 1").fetchone()
    return r, (r["phone"] if r is not None else "")


def wa_order_link(con, size):
    r, ph = supplier(con)
    if r is None or not wa_href(ph):
        return None, r
    msg = "Namaste %s ji, %s se: X-ray film %s — 1 box bhej dijiye. Dhanyavaad." % (r["name"], CLINIC, SIZE_LABEL[size])
    return "%s?text=%s" % (wa_href(ph), urllib.parse.quote(msg)), r


# ============================================================================================ the Scan App's film bills (READ ONLY)
def _assets_path():
    return os.environ.get("ASSETS_DB", "/root/assetapp/assets.db")


def sync_purchases(con):
    """Copies the Scan App's X-ray film bills into xf_purchase, READ ONLY on assets.db (mode=ro). One row per bill and size
    (src 'bill:<id>:<created_at>:<size>'), and one per film line typed on a machine record (src 'line:<id>'). A row the desk no
    longer lists (rejected, a second scan, a voided line) is marked gone. Returns (ok, words)."""
    p = _assets_path()
    if not p or not os.path.exists(p):
        return False, "the Scan App's database is not reachable"
    try:
        a = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=2)
    except sqlite3.Error as e:
        return False, "the Scan App's database could not be opened (%s)" % str(e)[:60]
    a.row_factory = sqlite3.Row
    found = {}
    ov = {r[0]: r[1] for r in con.execute("SELECT b.src, b.size FROM xf_bill_size b WHERE b.id = (SELECT MAX(q.id) FROM xf_bill_size q WHERE q.src = b.src)")}
    qov = {r[0]: r[1] for r in con.execute("SELECT b.src, b.boxes FROM xf_bill_qty b WHERE b.id = (SELECT MAX(q.id) FROM xf_bill_qty q WHERE q.src = b.src)")}
    try:
        qmax = float(setting(con, "bill.max_boxes"))
    except ValueError:
        qmax = 10.0
    try:
        bcols = {r[1] for r in a.execute("PRAGMA table_info(bills)")}
        if "subgroup" not in bcols:
            return False, "the Scan App has no film groups yet"
        where = "subgroup IN (%s) AND COALESCE(status,'') <> 'rejected'" % ",".join("?" * len(FILM_SUBS))
        if "dup_of" in bcols:
            where += " AND dup_of IS NULL"
        desk = a.execute("SELECT id, created_at, vendor, bill_date, subgroup, total_amount FROM bills WHERE " + where, FILM_SUBS).fetchall()
        for b in desk:
            per = {}
            for it in a.execute("SELECT item_name, quantity FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)).fetchall():
                sz = size_of(it["item_name"])
                if sz in SIZE_KEYS:
                    q = it["quantity"]
                    per[sz] = (per.get(sz) or 0.0) + (float(q) if q is not None and float(q) > 0 else 1.0)
            if not per:
                # no size on its lines: only the 11 x 14 group names one size; "small film" holds 8x10 AND 10x12 -> size unknown
                sz = {"xray_11x14": "11x14"}.get(b["subgroup"] or "", "")
                per[sz] = None
            bd = str(b["bill_date"] or "")[:10]
            if not DAY_RE.match(bd):
                bd = str(b["created_at"] or "")[:10]
            for sz, q in per.items():
                src = "bill:%d:%s:%s" % (b["id"], b["created_at"] or "", sz or "-")
                found[src] = (ov.get(src, sz) if not sz else sz, bd, q, b["vendor"] or "")   # the owner's word on a bill with no size
        tabs = {r[0] for r in a.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "xray_film_line" in tabs:
            acols = {r[1] for r in a.execute("PRAGMA table_info(assets)")}
            lines = a.execute("SELECT l.id, l.asset_id, l.size, l.boxes, l.amount, a.purchase_date, a.vendor, a.price%s FROM xray_film_line l "
                              "JOIN assets a ON a.id=l.asset_id AND COALESCE(a.created_at,'')=l.asset_created_at WHERE l.voided_at=''"
                              % (", a.bill_id" if "bill_id" in acols else ", NULL AS bill_id")).fetchall()
            amt = {}
            for l in lines:
                amt[l["asset_id"]] = amt.get(l["asset_id"], 0.0) + float(l["amount"] or 0)
            for l in lines:
                if desk_twin(desk, l, amt[l["asset_id"]]):
                    continue                                           # the same bill is on the desk: its boxes count there, once
                found["line:%d" % l["id"]] = (size_of(l["size"]), str(l["purchase_date"] or "")[:10], l["boxes"], l["vendor"] or "")
    except sqlite3.Error as e:
        return False, "the Scan App's film bills could not be read (%s)" % str(e)[:60]
    finally:
        a.close()
    at = _stamp()
    have = {r[0]: (r[1], r[2], r[3], r[4], r[5]) for r in con.execute("SELECT src, gone_at, size, bill_day, boxes, held FROM xf_purchase")}
    new = 0
    for src, (sz, bd, q, v) in found.items():
        # the quantity: the owner's word on it wins; a read above bill.max_boxes (a sheet count read as boxes?) is HELD -- not
        # counted in the spare stock until he confirms or corrects it on his page
        if src in qov:
            q, hd = qov[src], 0
        else:
            hd = 1 if (q is not None and float(q) > qmax) else 0
        if src not in have:
            con.execute("INSERT OR IGNORE INTO xf_purchase (src, size, bill_day, boxes, vendor, seen_at, held) VALUES (?,?,?,?,?,?,?)",
                        (src, sz, bd, q, v[:60], at, hd))
            new += 1
        elif have[src] != ("", sz, bd, q, hd):                         # gone and back, or its size, date, boxes or hold re-read
            con.execute("UPDATE xf_purchase SET gone_at='', size=?, bill_day=?, boxes=?, held=? WHERE src=?", (sz, bd, q, hd, src))
    for src, (gone, _sz, _bd, _q, _h) in have.items():
        if src not in found and not gone:
            con.execute("UPDATE xf_purchase SET gone_at=? WHERE src=?", (at, src))
    con.commit()
    return True, "%d film bill(s) read from the Scan App, %d new" % (len(found), new)


def _sup1(v):
    """A supplier's first word, as the asset app matches it (batteries.sup1 / _supplier_key's own fallback)."""
    w = [x for x in re.sub(r"[^a-z0-9 ]", " ", str(v or "").lower().replace("-", "").replace(".", "")).split()
         if x not in ("the", "ms", "m", "s", "pvt", "ltd", "p", "co", "and", "&")]
    if w and w[0].startswith("blcomputer"):
        return "bl"
    return w[0] if w else ""


def desk_twin(desk, line, amount):
    """True when a film bill kept on a machine record IS a film paper on the desk (xray_costs._desk_twin's match): first the
    record's own bill link; else the same supplier (first word), the same date, and the paper's total within 1 of the record's
    typed lines or its price. Such a bill is counted on the desk only."""
    bid = line["bill_id"]
    if bid and any(b["id"] == bid for b in desk):
        return True
    k = _sup1(line["vendor"])
    amts = [x for x in (amount, line["price"]) if x is not None]
    for b in desk:
        if (k and _sup1(b["vendor"]) == k and str(b["bill_date"] or "")[:10] == str(line["purchase_date"] or "")[:10]
                and b["total_amount"] is not None and any(abs(float(b["total_amount"]) - float(x)) < 1 for x in amts)):
            return True
    return False


# ============================================================================================ the slips (READ ONLY)
def studies(con):
    """{service_id: (size, films, both_one)} -- the newest xf_study row of each study."""
    out = {}
    for r in con.execute("SELECT s.service_id, s.size, s.films, s.both_one FROM xf_study s WHERE s.id = (SELECT MAX(q.id) FROM xf_study q "
                         "WHERE q.service_id = s.service_id)"):
        out[r[0]] = (r[1] or "", int(r[2] or 1), int(r[3] or 0))
    return out


def slip_lines(con, d0, d1, names=False):
    """Every X-ray line of a PAID X-ray slip (series xp, state ok, paid cash or UPI) from day d0 to d1: [{day, slip_id, no, cid,
    name, study, size, films, paid}] (the name only when asked: the X-ray list). Side B (both sides) takes twice the study's
    films, unless the owner marked that study "both sides on one film", or its name itself starts with "Both"."""
    st = studies(con)
    q = ("SELECT s.id, s.day, s.slip_no, s.clinic_id, s.no_id_name, s.name_seen, s.paid_mode, i.service_id, i.name AS iname, "
         "i.side, o.name AS oname FROM slip s JOIN slip_item i ON i.slip_id=s.id AND i.kind='xray' LEFT JOIN owner_service o ON o.id=i.service_id "
         "WHERE s.series='xp' AND s.state='ok' AND s.paid_mode IN ('cash','upi') AND s.day>=? AND s.day<=? ORDER BY s.day, s.slip_no, i.sort, i.id")
    SL = None
    if names:
        try:
            import slip_log as SL                                          # noqa: PLC0415 -- the slip book's own name rule
        except Exception:                                              # noqa: BLE001
            SL = None
    out = []
    for r in con.execute(q, (str(d0), str(d1))):
        size, films, b1 = st.get(r["service_id"], ("", 1, 0)) if r["service_id"] is not None else ("", 1, 0)
        sname = r["oname"] or r["iname"] or ""
        side = (r["side"] or "").strip().upper()
        if side in ("B", "BOTH") and not b1 and not sname.strip().lower().startswith("both"):
            films *= 2
        e = dict(day=r["day"], slip_id=r["id"], no=r["slip_no"], cid=r["clinic_id"] or "", study=sname,
                 side=r["side"] or "", size=size, films=films, paid=r["paid_mode"])
        if names:
            nm = r["name_seen"] or r["no_id_name"] or ""
            if not nm and r["clinic_id"] and SL is not None:
                try:
                    nm = (SL.patient(con, r["clinic_id"]) or ("", ""))[0]
                except Exception:                                      # noqa: BLE001
                    nm = ""
            e["name"] = nm
        out.append(e)
    return out


def slip_films(con, d0, d1):
    """{size or '': films} on the paid X-ray slips from d0 to d1."""
    t = {k: 0 for k in SIZE_KEYS}
    t[""] = 0
    for e in slip_lines(con, d0, d1):
        t[e["size"] if e["size"] in SIZE_KEYS else ""] += e["films"]
    return t


# ============================================================================================ the log
def spans(con, upto):
    """The counted mornings as spans: each morning q after a morning p gives the films the machine used from p to the day
    before q. [{p, q, end, machine{size}, slips{size, ''}, gap{size}, load{size}, by, at}] oldest first."""
    days = {}
    for size in SIZE_KEYS:
        for r in readings(con, size, upto):
            days.setdefault(r["day"], {})[size] = r
    ds = sorted(d for d, v in days.items() if all(k in v for k in SIZE_KEYS))
    out = []
    for p, q in zip(ds, ds[1:]):
        end = (_d(q) - dt.timedelta(days=1)).isoformat()
        sl = slip_films(con, p, end)
        # the used of each size between p and q, from the two figures themselves (a size counted in between does not split it)
        mach, load = {}, {}
        for k in SIZE_KEYS:
            a, b = days[p][k]["left"], days[q][k]["left"]
            load[k] = b > a
            mach[k] = (a - b) if b <= a else max(0, a + int(_num_setting(con, "box.films")) - b)
        gap = {k: mach[k] - sl[k] for k in SIZE_KEYS}
        out.append(dict(p=p, q=q, end=end, machine=mach, slips=sl, gap=gap, load=load, by=days[q][SIZE_KEYS[0]]["by"],
                        at=days[q][SIZE_KEYS[0]]["at"]))
    return out, ds


def late_count(con, day):
    """The day's count was LATE: its FIRST staff save (xf_save kind 'count') was at or after the stand-in hour (setting
    standin.after, 11:00) -- after X-rays have usually started. Never the time of an owner's correction, void or un-void
    (those are stamped when he makes them, often in the evening). No count save that day: not late."""
    r = con.execute("SELECT saved_at FROM xf_save WHERE day=? AND kind='count' ORDER BY id LIMIT 1", (str(day),)).fetchone()
    return r is not None and str(r[0] or "")[11:16] >= setting(con, "standin.after")


def log_spans(con, upto):
    """The spans as the log shows them: a LATE count (the day's first staff save at or after 11:00) splits the day's films
    wrongly between its two spans, so the span ending at it and the span after it are shown as ONE ('der se ginti -- do din
    milake'); the NEWEST late count, with no next count yet, is 'pending' ('der se ginti -- kal ki ginti ke saath judegi'): its
    gap is held back from staff and from the gap days until it joins; and a span with a box load across more than 3 days
    carries 'check' (two boxes could have gone in)."""
    sp, ds = spans(con, upto)
    lt = {}
    for x in sp:
        x["late"] = x["pending"] = False
        x["check"] = any(x["load"].values()) and (_d(x["q"]) - _d(x["p"])).days > CHECK_GAP_DAYS
        lt[x["q"]] = late_count(con, x["q"])
    out, i = [], 0
    while i < len(sp):
        cur = dict(sp[i])
        while lt[cur["q"]] and i + 1 < len(sp):
            nx = sp[i + 1]
            mach = {k: cur["machine"][k] + nx["machine"][k] for k in SIZE_KEYS}
            sl = {k: cur["slips"][k] + nx["slips"][k] for k in list(SIZE_KEYS) + [""]}
            cur = dict(p=cur["p"], q=nx["q"], end=nx["end"], machine=mach, slips=sl, gap={k: mach[k] - sl[k] for k in SIZE_KEYS},
                       load={k: cur["load"][k] or nx["load"][k] for k in SIZE_KEYS}, by=nx["by"], at=nx["at"], late=True,
                       check=cur["check"] or nx["check"], pending=False)
            i += 1
        if lt[cur["q"]] and i + 1 >= len(sp):
            cur["late"] = cur["pending"] = True                        # joins the next count when it comes
        out.append(cur)
        i += 1
    return out, ds


def month_log(con, ym, today):
    """The month's rows, newest day first: a counted span ends on its row's day; a day inside a longer span says so."""
    first, last = month_days(ym)
    sp, ds = log_spans(con, today)
    by_end = {s["end"]: s for s in sp}
    inside = {}
    for s in sp:
        d = _d(s["p"])
        while d < _d(s["end"]):
            inside[d.isoformat()] = s
            d += dt.timedelta(days=1)
    start = _d(setting(con, "count.from"))
    rows, gapdays, missed = [], 0, 0
    d = min(last, today)
    while d >= first:
        k = d.isoformat()
        if k in by_end:
            s = by_end[k]
            g = any(s["gap"][z] not in (None, 0) for z in SIZE_KEYS) and not s.get("pending")
            gapdays += 1 if g else 0
            rows.append(dict(day=k, kind="span", s=s, gap=g))
        elif k in inside:
            rows.append(dict(day=k, kind="joined", s=inside[k]))
        elif ds and k >= ds[-1]:
            rows.append(dict(day=k, kind="waiting"))
        else:
            rows.append(dict(day=k, kind="none"))
        d -= dt.timedelta(days=1)
    d = max(first, start)
    while d < min(today, last + dt.timedelta(days=1)):
        if d.weekday() != 6 and d.isoformat() not in ds:
            missed += 1
        d += dt.timedelta(days=1)
    return dict(rows=rows, gapdays=gapdays, missed=missed)


def counted_today(con, today):
    return con.execute("SELECT COUNT(DISTINCT c.size) FROM xf_count c WHERE c.day=? AND c.void=0 AND c.id = (SELECT MAX(q.id) FROM xf_count q "
                       "WHERE q.size=c.size AND q.day=c.day)", (today.isoformat(),)).fetchone()[0] >= 2


# ============================================================================================ the saved card and messages
def _saved(lang, rows):
    head = "✓ Saved — सेव हो गया" if lang == "hi" else "✓ Saved"
    t = "".join("<tr><td>%s</td><td><b>%s</b></td></tr>" % (a, b) for a, b in rows)
    return "<div class='saved'><div class='sv1'>%s</div>%s</div>" % (head, ("<table class='svt'><tbody>%s</tbody></table>" % t) if t else "")


def _msg(lang):
    m = request.args.get("msg") or ""
    bad = {"blank": ("Dono size ki bachi film likhiye, phir Save kijiye.", "Type both figures, then Save."),
           "bad": ("Kuch galat likha gaya — dobara dekhiye.", "Something was not right -- please check and try again."),
           "over": ("Ek box mein 150 se zyada film nahi hoti — machine ki screen dobara dekhiye. Sahi hai to Dr Manoj se confirm karaiye.",
                    "More than a box holds -- type a note to save it."),
           "note": ("Note likhiye.", "A figure above a box's films needs a note -- type one and Save again."),
           "risenote": ("Pichhli ginti se zyada film? Naya box ho to tick kijiye, warna note likhiye.",
                        "A figure higher than the last count means a new box: tick it (last count 20 or less) or type a note."),
           "notvoid": ("Us din ki ginti void nahi hai.", "That day's count is not voided."),
           "nocount": ("Us din ki ginti nahi hai.", "There is no count on that day to correct."),
           "owner": ("Yeh sirf Dr Manoj badal sakte hain.", "Only the owner changes this.")}
    if m in bad:
        return "<div class='bad'>%s</div>" % (bad[m][0] if lang == "hi" else bad[m][1])
    return ""


def _rid():
    try:
        return max(0, min(10 ** 7, int(request.args.get("id") or 0)))
    except ValueError:
        return 0


def _nav(lang, here):
    items = (("subah", "Subah ki ginti", "Morning count"), ("log", "Film log", "Film log"), ("list", "X-ray list", "X-ray list"))
    out = ["<a class='back' href='/finance/aaj'>← Aaj ka kaam</a>" if lang == "hi" else "<a class='back' href='/finance/aaj'>← Today</a>"]
    for k, hi, en in items:
        out.append("<a class='btn%s' href='%s/%s'>%s</a>" % (" on" if k == here else "", BASE, k, hi if lang == "hi" else en))
    return "<p class='nav'>%s</p>" % " ".join(out)


def _box_words(st, lang):
    if st["left"] is None:
        return ("Subah ki ginti ke baad yahan bachi film dikhegi." if lang == "hi"
                else "No count yet -- films left show from the first morning count.")
    left = int(round(st["left"]))
    if st["days"] is None:
        tail = {"little": ("din: abhi kam ginti hai", "days: too little data yet"),
                "nouse": ("din: 30 din mein koi film nahi lagi", "days: no film used in 30 days")}.get(st["why"], ("", ""))
        return ("Machine mein %d film bachi · %s" % (left, tail[0]) if lang == "hi"
                else "about %d films left · %s" % (left, tail[1]))
    days = int(st["days"])
    return ("Machine mein %d film bachi · lagbhag %d din" % (left, days) if lang == "hi"
            else "about %d films · %d days" % (left, days))


@bp.route(BASE)
def hub():
    u, lang, _own = _user()
    if u is None:
        return _denied()
    return redirect(BASE + ("/log" if lang == "en" else "/subah"))


# ============================================================================================ 1 · the morning count
@bp.route(BASE + "/subah")
def subah():
    u, lang, own = _user()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    sync_purchases(con)
    today = _today()
    hi = lang == "hi"
    out = [_nav(lang, "subah")]
    if (request.args.get("msg") or "") == "saved":
        sv = con.execute("SELECT * FROM xf_save WHERE id=?", (_rid(),)).fetchone()
        if sv is not None:
            rows = []
            sp, _ds = log_spans(con, _d(sv["day"]))
            last = sp[-1] if sp and sp[-1]["q"] == sv["day"] else None
            for k in SIZE_KEYS:
                c = con.execute("SELECT remaining FROM xf_count WHERE save_id=? AND size=?", (sv["id"], k)).fetchone()
                w = ("bachi %s" if hi else "left %s") % (c[0] if c else "?")
                if last is not None and last.get("pending") and hi:
                    w += " · %s" % PEND_HI                       # a late count: its gap waits for the next count
                elif last is not None:
                    w += (" · kal lagi %s · parchi par %s" if hi else " · used %s · on slips %s") % (last["machine"][k], last["slips"][k])
                    if last["load"][k]:
                        w += " · naya box (machine se pata chala)"
                    if last.get("pending"):
                        w += " · late count — joins the next count"
                rows.append((SIZE_LABEL[k], w))
            rows.append(("Kisne" if hi else "By", "%s, %s" % (name_of(sv["saved_by"]), when(sv["saved_at"]))))
            out.append(_saved(lang, rows))
    out.append(_msg(lang))
    mk_, wk = request.args.get("msg") or "", request.args.get("what") or ""
    pre = {k: (request.args.get("v_" + k) or "") for k in SIZE_KEYS} if mk_ == "sure" else {}
    pre = {k: int(v) for k, v in pre.items() if CNT_RE.match(v)}
    if mk_ in ("risen", "tick") and wk in SIZE_KEYS:
        x = last_before(con, wk, today.isoformat())
        if mk_ == "risen":
            t = ("%s: Pichhli ginti mein %s film bachi thi — badhi kaise? Dr Manoj se confirm karaiye." if hi
                 else "%s: the last count had %s films left -- a higher figure needs a note.") % (SIZE_LABEL[wk], x)
        else:
            t = ("%s: bachi film badh gayi — naya box laga ho to 'Haan, naya box lagaya gaya' par tick kijiye, phir Save." if hi
                 else "%s: the figure went up -- tick 'Yes, a new box went in', then Save.") % SIZE_LABEL[wk]
        out.append("<div class='bad'>%s</div>" % _esc(t))
    if mk_ == "sure" and wk in SIZE_KEYS:
        x = last_before(con, wk, today.isoformat())
        t = ("%s: pichhli ginti mein %s film bachi thi — itni film ek saath aam taur par nahi lagti. Machine ki screen dobara dekhiye; "
             "sahi ho to 'Haan, machine par yahi dikh raha hai' par tick karke Save kijiye." if hi
             else "%s: the last count had %s films left -- far more used than usual. Check the screen; if right, tick 'Yes, the machine "
             "shows this' and Save.") % (SIZE_LABEL[wk], x)
        out.append("<div class='bad'>%s</div>" % _esc(t))
    out.append("<p class='mut'>%s, %s · %s</p>" % (DAYS_HI[today.weekday()] if hi else DAYS_EN[today.weekday()], dm(today),
                                                  "Machine ki screen par jitni film bachi dikh rahi hain, wahi likhiye." if hi
                                                  else "Type the films left that the Fuji machine's screen shows, for each size."))
    sp, _ds = log_spans(con, today)
    lastspan = sp[-1] if sp else None
    if counted_today(con, today):
        r = con.execute("SELECT saved_by, saved_at FROM xf_save WHERE day=? ORDER BY id DESC LIMIT 1", (today.isoformat(),)).fetchone()
        out.append("<div class='okbar'>%s</div>" % ((("Aaj ki ginti ho gayi — %s, %s. Badalni ho to naya number likh kar Save kijiye.")
                                                     if hi else "Today's count is saved — %s, %s. To correct it, type the new number and Save.")
                                                    % (name_of(r[0]), when(r[1]))))
    for k in SIZE_KEYS:
        st = size_state(con, k, today)
        dr = day_reading(con, k, today.isoformat())
        cur = dr[0] if dr is not None and not dr[1] else ""
        if k in pre:
            cur = pre[k]                                               # the figure typed before the confirm question
        prev = [r for r in st["readings"] if r["day"] < today.isoformat()]
        c = ["<div class='card'><div class='ch'><b class='sz'>%s film</b></div>" % SIZE_LABEL[k],
             "<p class='mut'>%s</p>" % _esc(_box_words(st, lang))]
        if st["due"]:
            c.append("<div class='warn'>%s</div>" % ("%s film mangwaiye — 1 box (Shavez ki list par)" % SIZE_LABEL[k] if hi
                                                    else "Order %s film — 1 box (on Shavez's list and yours)" % SIZE_LABEL[k]))
        c.append("<label class='ld'>%s<input class='num' name='c_%s' form='cf' inputmode='numeric' autocomplete='off' value='%s'></label>"
                 % ("Machine mein kitni film bachi hain" if hi else "Films left on the machine now", k, cur))
        if own or (prev and prev[-1]["left"] <= _num_setting(con, "load.max_left")):
            c.append("<label class='ck'><input type='checkbox' name='newbox_%s' value='1' form='cf'%s> %s</label>"
                     % (k, " checked" if (request.args.get("nb_" + k) == "1" and k in pre) else "",
                        "Haan, naya box lagaya gaya" if hi else "Yes, a new box went in"))
        if not own and k in pre and needs_sure(con, k, today.isoformat(), pre[k]):
            c.append("<label class='ck'><input type='checkbox' name='sure_%s' value='1' form='cf'> %s</label>"
                     % (k, "Haan, machine par yahi dikh raha hai" if hi else "Yes, the machine shows this"))
        if prev:
            pv = prev[-1]
            line = ("Pichhli ginti (%s): %d bachi thi" if hi else "Last count (%s): %d left") % (dm(pv["day"]), pv["left"])
            if lastspan is not None and lastspan.get("pending") and hi:
                line = _esc(line + " · " + PEND_HI)                    # a late count: its gap waits for the next count
            elif lastspan is not None:
                g = lastspan["gap"][k]
                line += (" · %s lagi: %s · parchi par: %s" if hi else " · used %s: %s · on slips: %s") % (
                    dm(lastspan["end"]), lastspan["machine"][k], lastspan["slips"][k])
                if lastspan["load"][k]:
                    line += " · naya box (machine se pata chala)"
                gw = ("<div class='okc'>%s</div>" % ("Theek hai — koi farq nahi" if hi else "Fine — no gap") if g == 0 else
                      "<div class='gapc'>%s</div>" % (("%d film ka farq — sabko dikhega" if hi else "Gap of %d film(s) — everyone sees it") % abs(g)))
                line = _esc(line) + gw
            else:
                line = _esc(line)
            c.append("<div class='mut'>%s</div>" % line)
        c.append("</div>")
        out.append("".join(c))
    nt = ("<label class='ld'>Note (needed for a figure above %d) <input class='tx' name='note' form='cf'></label>" % int(_num_setting(con, "box.films"))
          if own else "")
    out.append("<form id='cf' method='post' action='%s/subah'>%s<button class='save' type='submit'>Save</button></form>" % (BASE, nt))
    out.append("<p class='mut'>%s</p>" % ("Ginti subah pehla X-ray hone se pehle kijiye — X-ray shuru hone ke baad ki ginti mein us subah ki film bhi "
                                          "jud jaati hai." if hi else "Take the count before the first X-ray: a count saved after X-rays have "
                                          "started includes that morning's prints."))
    out.append("<p class='mut'>%s</p>" % ("Box khatam hone par naya box lagaiye — machine ki bachi film badh jaayegi, system khud samajh lega. "
                                          "Farq ka koi kaaran nahi poochha jaata. Reception na ho to Shavez yeh bharte hain." if hi
                                          else "A new box shows as the figure going UP -- the system records the box load by itself. "
                                          "No reason is asked for a gap. Shavez fills this when reception is away."))
    return _shell("X-ray film — subah ki ginti" if hi else "X-ray film — morning count", "".join(out), lang)


def last_before(con, size, day):
    """The films left of the last counted morning before `day`, or None."""
    prev = [r for r in readings(con, size, day) if r["day"] < str(day)]
    return prev[-1]["left"] if prev else None


def _figures(con, own, day, form):
    """The two figures of a form, checked: (({size: films left}, note), None, None) or (None, msg, size). Staff: at most a box's
    films (150); a figure HIGHER than the last count (a new box) only when the last count was 20 or less (setting load.max_left)
    AND 'Haan, naya box lagaya gaya' is ticked -- a typo one film up must never become a box load; a figure that means more
    films used than 3x the 30-day average AND more than 30 (a typo too low) needs 'Haan, machine par yahi dikh raha hai' ticked
    (never refused). The owner may save either: above 150 with a note; a higher figure with the tick (last count 20 or less) or
    a note."""
    pb = int(_num_setting(con, "box.films"))
    lm = _num_setting(con, "load.max_left")
    vals = {}
    for k in SIZE_KEYS:
        v = (form.get("c_%s" % k) or "").strip()
        if v == "":
            return None, "blank", None
        if not CNT_RE.match(v):
            return None, "bad", None
        vals[k] = int(v)
    note = " ".join((form.get("note") or "").split())[:200]
    for k in SIZE_KEYS:
        if vals[k] > pb:
            if not own:
                return None, "over", k
            if not note:
                return None, "note", k
        prev = last_before(con, k, day)
        if prev is not None and vals[k] > prev:
            tick = (form.get("newbox_%s" % k) or "") == "1"
            if own:
                if not (note or (prev <= lm and tick)):
                    return None, "risenote", k
            else:
                if prev > lm:
                    return None, "risen", k
                if not tick:
                    return None, "tick", k
        if not own and (form.get("sure_%s" % k) or "") != "1" and needs_sure(con, k, day, vals[k]):
            return None, "sure", k
    return (vals, note), None, None


@bp.route(BASE + "/subah", methods=["POST"])
def subah_save():
    u, lang, own = _user()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    today = _today()
    got, msg, what = _figures(con, own, today.isoformat(), request.form)
    if msg:
        keep = ""
        if msg == "sure":                                              # the typed figures (films left: 3 digits at most) come back
            for k in SIZE_KEYS:
                v = (request.form.get("c_" + k) or "").strip()
                keep += ("&v_%s=%s" % (k, v)) if CNT_RE.match(v) else ""
                keep += ("&nb_%s=1" % k) if request.form.get("newbox_" + k) == "1" else ""
        return redirect(BASE + "/subah?msg=%s%s%s" % (msg, ("&what=" + what) if what else "", keep))
    vals, note = got
    at, who = _stamp(), _who(u)
    sid = con.execute("INSERT INTO xf_save (day, saved_at, saved_by, kind, note) VALUES (?,?,?,'count',?)", (today.isoformat(), at, who, note)).lastrowid
    for k in SIZE_KEYS:
        con.execute("INSERT INTO xf_count (save_id, day, size, remaining, saved_at, saved_by) VALUES (?,?,?,?,?,?)",
                    (sid, today.isoformat(), k, vals[k], at, who))
    con.commit()
    _audit_safe(con, "xf_save", sid, "film_count", None, dict(day=today.isoformat(), left=vals, note=note), who)
    return redirect(BASE + "/subah?msg=saved&id=%d" % sid)


# ============================================================================================ 2 · the film log
def _month_arg(con, today):
    lo = setting(con, "list.from")[:7]
    this = today.isoformat()[:7]
    m = (request.args.get("m") or "").strip()
    if not m:
        return this
    if not YM_RE.match(m) or m < lo or m > this:
        return None
    return m


def _cell(v):
    return "—" if v is None else str(v)


def _gapw(s, lang):
    parts = []
    for k in SIZE_KEYS:
        g = s["gap"][k]
        if g not in (None, 0):
            parts.append("%s %s%d" % (SIZE_LABEL[k], "+" if g > 0 else "−", abs(g)))
    if not parts:
        return "<span class='okc'>%s</span>" % ("Koi farq nahi" if lang == "hi" else "None")
    return "<span class='gapc'>%s</span>" % " · ".join(parts)


@bp.route(BASE + "/log")
def log_page():
    u, lang, own = _user()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    ok_sync, sync_words = sync_purchases(con)
    today = _today()
    ym = _month_arg(con, today)
    if ym is None:
        return redirect(BASE + "/log?msg=bad")
    hi = lang == "hi"
    out = [_nav(lang, "log")]
    if (request.args.get("msg") or "") == "saved":
        what = {"contact": "Contact", "settings": "Settings", "study": "Film size of a study", "billsize": "Film bill size",
                "billqty": "Film bill quantity", "count": "Morning count correction"}.get(
            request.args.get("what") or "", "Change")
        out.append(_saved(lang, [(what, "saved")]))
    out.append(_msg(lang))
    lo = setting(con, "list.from")[:7]
    pm, nm_ = ym_shift(ym, -1), ym_shift(ym, 1)
    navm = []
    if pm >= lo:
        navm.append("<a class='btn' href='%s/log?m=%s'>← %s</a>" % (BASE, pm, mname(pm, lang).split()[0]))
    if nm_ <= today.isoformat()[:7]:
        navm.append("<a class='btn' href='%s/log?m=%s'>%s →</a>" % (BASE, nm_, mname(nm_, lang).split()[0]))
    navm.append("<a class='btn' href='%s/log.xlsx?m=%s'>%s</a>" % (BASE, ym, "Excel download" if hi else "Download Excel"))
    out.append("<h2 class='pt'>%s — %s</h2><p class='mut'>%s</p><p class='nav'>%s</p>" % (
        "X-ray film log" if not hi else "X-ray film ka hisaab", mname(ym, lang),
        "Machine ki bachi film se nikli lagi hui film, aur paid parchi par jitni film — size ke hisaab se. Farq sabko dikhta hai; koi kaaran nahi poochha jaata."
        if hi else "Films used, from the machine's films-left figures, against films on the paid slips, by size. A gap is shown to everyone; no reason is asked.",
        " ".join(navm)))
    sts = {k: size_state(con, k, today) for k in SIZE_KEYS}
    boxes = []
    for k in SIZE_KEYS:
        st = sts[k]
        b = ["<div class='card%s'><h3>%s — %s</h3><p>%s</p>" % (" remind" if st["due"] else "", SIZE_LABEL[k],
                                                               "printer ka box" if hi else "box in the printer", _esc(_box_words(st, lang)))]
        if st["loads"]:
            b.append("<p class='mut'>%s %s</p>" % ("Naya box (machine se pata chala):" if hi else "Last new box (naya box, machine se pata chala):",
                                                   dm(st["loads"][-1])))
        b.append("<p><b>%s</b></p>" % _esc(spare_words(st["spare"], lang)))
        if st["due"]:
            link, sup = wa_order_link(con, k)
            b.append("<div class='warn'><b>%s</b></div>" % ("%s film mangwaiye — 1 box" % SIZE_LABEL[k] if hi
                                                          else "Order now — under %d days (on Shavez's list and yours)" % int(st["nd"])))
            if not opening_set(con, k):
                b.append("<p class='mut'>%s</p>" % ("(Dr Manoj ne shuru ka stock abhi nahi bhara)" if hi
                                                    else "(opening boxes not set yet — set them in Settings)"))
            if link:
                b.append("<p><a class='btn wa' href='%s' target='_blank' rel='noopener'>%s</a></p>" % (
                    _esc(link), ("%s ko WhatsApp par order bhejiye" if hi else "Send order to %s on WhatsApp") % _esc(
                        "%s (%s)" % (sup["name"], sup["firm"]) if sup["firm"] else sup["name"])))
            elif sup is not None and sup["phone"]:
                b.append("<p class='mut'>%s</p>" % ("Films supplier ka number mobile nahi hai — call kijiye." if hi
                                                    else "The films supplier's number is not a mobile: no WhatsApp — call."))
            else:
                b.append("<p class='mut'>%s</p>" % ("Films supplier ka number Dr Manoj daalenge." if hi
                                                    else "Type the films supplier's number in Contacts below for the WhatsApp button."))
        elif st["spare"] >= 1:
            b.append("<p class='okc'>%s</p>" % (("%g box rakha hai — order nahi chahiye" if hi else "%g spare box(es) on the shelf — no order needed")
                                               % st["spare"]))
        elif st["days"] is not None:
            b.append("<p class='okc'>%s</p>" % ("Theek hai — %d din se kam par order aayega" % int(st["nd"]) if hi
                                               else "Fine — the order comes up under %d days" % int(st["nd"])))
        b.append("</div>")
        boxes.append("".join(b))
    out.append("<div class='two'>%s</div>" % "".join(boxes))
    if lang == "en":
        unk = list(con.execute("SELECT * FROM xf_purchase WHERE gone_at='' AND size='' ORDER BY bill_day DESC, id DESC LIMIT 20"))
        if unk:
            li = []
            for x in unk:
                btn = ""
                if own:
                    btn = "".join("<form class='inl' method='post' action='%s/owner/billsize'><input type='hidden' name='src' value='%s'>"
                                  "<input type='hidden' name='size' value='%s'><button class='mini' type='submit'>%s</button></form> "
                                  % (BASE, _esc(x["src"]), v, t) for v, t in (("8x10", "8×10"), ("11x14", "11×14"), ("none", "not film")))
                li.append("<li>%s — %s%s · size not read %s</li>" % (dm(x["bill_day"]), _esc(x["vendor"] or "film bill"),
                                                                  (" × %g box" % x["boxes"]) if x["boxes"] else "", btn))
            out.append("<div class='card remind'><h3>FILM BILLS WITH NO SIZE</h3><p class='mut'>Counted for no size until you say which "
                       "(one tap; audited).</p><ul class='hist'>%s</ul></div>" % "".join(li))
        held = list(con.execute("SELECT * FROM xf_purchase WHERE gone_at='' AND held=1 ORDER BY bill_day DESC, id DESC LIMIT 20"))
        if held:
            li = []
            for x in held:
                btn = ""
                if own:
                    btn = ("<form class='inl' method='post' action='%s/owner/billqty'><input type='hidden' name='src' value='%s'>"
                           "<button class='mini' name='op' value='confirm' type='submit'>Confirm %g</button></form> "
                           "<form class='inl' method='post' action='%s/owner/billqty'><input type='hidden' name='src' value='%s'>"
                           "<input class='tx sm2' name='boxes' inputmode='numeric' placeholder='boxes'>"
                           "<button class='mini' name='op' value='fix' type='submit'>Correct</button></form>"
                           % (BASE, _esc(x["src"]), x["boxes"], BASE, _esc(x["src"])))
                li.append("<li>%s — %s · %s × %g box read · check quantity %s</li>" % (
                    dm(x["bill_day"]), _esc(x["vendor"] or "film bill"), SIZE_LABEL.get(x["size"], "size not read"), x["boxes"], btn))
            out.append("<div class='card remind'><h3>FILM BILLS: CHECK QUANTITY</h3><p class='mut'>Read as more than %s boxes: NOT counted "
                       "in the spare stock until you confirm or correct it (one tap; audited).</p><ul class='hist'>%s</ul></div>"
                       % (_esc(setting(con, "bill.max_boxes")), "".join(li)))
    ml = month_log(con, ym, today)
    avgw = " · ".join("%s %s" % (SIZE_LABEL[k], ("about %.0f a day" % sts[k]["avg"]) if sts[k]["avg"] else ("abhi kam data" if hi else "too little data"))
                      for k in SIZE_KEYS)
    out.append("<div class='card'><h3>%s</h3><p>%s <b>%d</b> · %s <b>%d</b></p><p class='mut'>%s %s</p></div>" % (
        "Is mahine" if hi else "This month", "Farq wale din:" if hi else "Days with a gap:", ml["gapdays"],
        "Subah ginti nahi hui:" if hi else "Mornings not counted:", ml["missed"], "Roz ki khapat:" if hi else "Use:", _esc(avgw)))
    out.append(_contacts_card(con, lang, own))
    th = (("Din", "8×10: machine", "8×10: parchi", "11×14: machine", "11×14: parchi", "Size nahi", "Farq", "Kisne gina") if hi else
          ("Day", "8×10: machine", "8×10: slips", "11×14: machine", "11×14: slips", "Size not set", "Gap", "Counted by"))
    rows = []
    for r in ml["rows"]:
        lab = ddm(r["day"], lang)
        if r["kind"] == "span" and r["s"].get("pending") and hi:
            # the newest late count: its gap is held back from staff until the next count joins it
            rows.append("<tr class='off'><td>%s</td><td colspan='6'>%s</td><td>%s</td></tr>" % (
                lab, PEND_HI, "%s, %s" % (name_of(r["s"]["by"]), when(r["s"]["at"]))))
        elif r["kind"] == "span":
            s = r["s"]
            span = "" if s["p"] == s["end"] else (" <span class='sm'>(%s–%s)</span>" % (dm(s["p"]), dm(s["end"])))
            rows.append("<tr%s><td>%s%s</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
                        "<td class='r'>%s</td><td>%s</td><td>%s</td></tr>" % (
                            " class='gp'" if r["gap"] else "", lab, span, _cell(s["machine"]["8x10"]), s["slips"]["8x10"],
                            _cell(s["machine"]["11x14"]), s["slips"]["11x14"], s["slips"][""] or "", _gapw(s, lang)
                            + "".join(" <span class='sm'>· %s: naya box (machine se pata chala)</span>" % SIZE_LABEL[z] for z in SIZE_KEYS if s["load"][z])
                            + ((" <span class='sm'>· %s</span>" % ("late count — joins the next count" if s.get("pending") else
                                                                   "der se ginti — do din milake" if hi else "late count — two days combined"))
                               if s.get("late") else "")
                            + ((" <span class='gapc'>· check: several days uncounted — the films used may be off by a box</span>")
                               if (s.get("check") and not hi) else ""),
                            "%s, %s" % (name_of(s["by"]), when(s["at"]))))
        else:
            w = {"joined": ("Agli subah ginti nahi hui — agli ginti mein joda gaya", "Not counted next morning — joined to the next count"),
                 "waiting": ("Agli subah ki ginti ka intezaar", "Waiting for the next morning's count"),
                 "none": ("Ginti nahi", "Not counted")}[r["kind"]]
            rows.append("<tr class='off'><td>%s</td><td colspan='7'>%s</td></tr>" % (lab, w[0] if hi else w[1]))
    out.append("<div class='card'><table class='grid'><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
               "<p class='mut'>%s</p></div>" % ("".join("<th>%s</th>" % h for h in th), "".join(rows) or "<tr><td colspan='8'>—</td></tr>",
                                                "Machine = pichhli ginti ki bachi film minus aaj ki bachi film (naya box laga ho to: pichhli bachi + 150 minus aaj). "
                                                "Parchi = us din ki paid X-ray parchi ki film (knee studies K/S do film)."
                                                if hi else "Machine = the last count's films left minus today's (a new box in between: last + 150 minus today). "
                                                "Slips = films on that day's paid X-ray slips (Knee studies K/S count two)."))
    if lang == "en":
        out.append(_owner_parts(con, own, today, sts, ok_sync, sync_words))
    return _shell("X-ray film log" if not hi else "X-ray film ka hisaab", "".join(out), lang)


def _contacts_card(con, lang, own):
    hi = lang == "hi"
    rows = list(con.execute("SELECT * FROM xf_contact WHERE active=1 ORDER BY CASE role WHEN 'films_supplier' THEN 0 WHEN 'fuji_service' THEN 1 "
                            "WHEN 'fuji_support' THEN 2 ELSE 3 END, id"))
    out = ["<div class='card'><h3>%s</h3>" % ("Contacts — film, Fuji service aur support" if hi else "Contacts — films, Fuji service and support")]
    for r in rows:
        btn = []
        if r["phone"]:
            btn.append("<a class='btn' href='%s'>Call</a>" % tel_href(r["phone"]))
            if wa_href(r["phone"]):
                btn.append("<a class='btn wa' href='%s' target='_blank' rel='noopener'>WhatsApp</a>" % wa_href(r["phone"]))
        if r["email"]:
            btn.append("<a class='btn' href='mailto:%s'>Email</a>" % _esc(r["email"]))
        out.append("<div class='hn'><div class='hl'>%s%s <span class='sm'>%s</span><br><span class='sm'>%s%s</span></div>%s</div>" % (
            _esc(r["name"]), (" — " + _esc(r["firm"])) if r["firm"] else "", _esc(ROLE_LABEL.get(r["role"], r["role"])),
            _esc(r["phone"]) if r["phone"] else ("number abhi nahi" if hi else "no number yet"),
            (" · " + _esc(r["email"])) if r["email"] else "", " ".join(btn)))
        if own:
            out.append(_contact_form(r))
    if own:
        out.append("<details><summary class='sm'>+ Add contact</summary>%s</details>" % _contact_form(None))
        out.append("<p class='mut'>You edit this list; Shavez and reception can see it and tap to call.</p>")
    out.append("</div>")
    return "".join(out)


def _contact_form(r):
    sel = "".join("<option value='%s'%s>%s</option>" % (k, " selected" if r is not None and r["role"] == k else "", v) for k, v in ROLES)
    if r is None:
        return ("<form class='row add' method='post' action='%s/owner/contact'><input type='hidden' name='op' value='add'>"
                "<input class='tx' name='name' placeholder='Name'><input class='tx' name='firm' placeholder='Firm'><select name='role'>%s</select>"
                "<input class='tx' name='phone' inputmode='tel' placeholder='Phone'><input class='tx' name='email' placeholder='Email'>"
                "<button class='mini' type='submit'>Add</button></form>" % (BASE, sel))
    return ("<details class='ed'><summary class='sm'>Edit</summary><form class='row' method='post' action='%s/owner/contact'>"
            "<input type='hidden' name='op' value='edit'><input type='hidden' name='id' value='%d'>"
            "<input class='tx' name='name' value='%s'><input class='tx' name='firm' value='%s'><select name='role'>%s</select>"
            "<input class='tx' name='phone' inputmode='tel' value='%s'><input class='tx' name='email' value='%s'>"
            "<button class='mini' type='submit'>Save</button></form>"
            "<form class='row' method='post' action='%s/owner/contact'><input type='hidden' name='op' value='retire'>"
            "<input type='hidden' name='id' value='%d'><button class='mini' type='submit'>Remove</button></form></details>"
            % (BASE, r["id"], _esc(r["name"]), _esc(r["firm"]), sel, _esc(r["phone"]), _esc(r["email"]), BASE, r["id"]))


def _owner_parts(con, own, today, sts, ok_sync, sync_words):
    out = []
    unset = [SIZE_LABEL[k] for k in SIZE_KEYS if not opening_set(con, k)]
    if unset:
        out.append("<div class='card remind'><h3>Opening boxes not set — set them so ordering is right</h3><p class='mut'>%s: the spare "
                   "boxes on the shelf on the start day are taken as 0 until you save them in Settings below (0 is an answer too).</p></div>"
                   % " and ".join(unset))
    bills = list(con.execute("SELECT * FROM xf_purchase WHERE gone_at='' ORDER BY bill_day DESC, id DESC LIMIT 12"))
    li = "".join("<li>%s — %s%s%s%s</li>" % (dm(b["bill_day"]), SIZE_LABEL.get(b["size"], "size not read"),
                                              (" × %g box" % b["boxes"]) if b["boxes"] else "", (" · " + _esc(b["vendor"])) if b["vendor"] else "",
                                              " · <span class='gapc'>held: check quantity</span>" if b["held"] else "")
                 for b in bills)
    out.append("<div class='card'><h3>FILM BILLS IN THE SCAN APP</h3><p class='mut'>%s</p><ul class='hist'>%s</ul></div>" % (
        _esc(sync_words if ok_sync else "Not read now: " + sync_words), li or "<li>none yet</li>"))
    ld = []
    for k in SIZE_KEYS:
        rs_ = sts[k]["readings"]
        for i_, r_ in enumerate(rs_):
            if r_["load"]:
                ld.append((r_["day"], k, (_d(r_["day"]) - _d(rs_[i_ - 1]["day"])).days > CHECK_GAP_DAYS))
    ld = sorted(ld, reverse=True)[:12]
    bl = ["<li>%s — %s · naya box (machine se pata chala)%s</li>" % (dm(d), SIZE_LABEL[k], " · <span class='gapc'>check: several days "
                                                                    "uncounted — the films used may be off by a box</span>" if c_ else "")
          for d, k, c_ in ld]
    out.append("<div class='card'><h3>NEW BOXES LOADED</h3><p class='mut'>Seen from the films-left figure going up; a correction of a "
               "count moves them.</p><ul class='hist'>%s</ul></div>" % ("".join(bl) or "<li>none yet</li>"))
    if own:
        out.append("<div class='card'><h3>CORRECT A MORNING COUNT</h3><form class='row' method='post' action='%s/owner/count'>"
                   "<label class='ld'>Day <input type='date' name='day' value='%s'></label>"
                   "<label class='ld'>8×10 films left <input class='tx sm2' name='c_8x10' inputmode='numeric'></label>"
                   "<label class='ld'>11×14 films left <input class='tx sm2' name='c_11x14' inputmode='numeric'></label>"
                   "<label class='ld'>Note <input class='tx' name='note'></label>"
                   "<label class='ck'><input type='checkbox' name='newbox_8x10' value='1'> 8×10 new box</label>"
                   "<label class='ck'><input type='checkbox' name='newbox_11x14' value='1'> 11×14 new box</label>"
                   "<button class='mini' name='op' value='edit' type='submit'>Save correction</button>"
                   "<button class='mini' name='op' value='void' type='submit'>Void that day's count</button>"
                   "<button class='mini' name='op' value='unvoid' type='submit'>Un-void that day</button></form>"
                   "<p class='mut'>The old figure is kept; a voided morning joins the next count; un-void puts it back.</p></div>" % (BASE, today.isoformat()))
    hist = list(con.execute("SELECT * FROM xf_save ORDER BY id DESC LIMIT 12"))
    hl = []
    for h in hist:
        cs = {r[0]: r[1] for r in con.execute("SELECT size, remaining FROM xf_count WHERE save_id=?", (h["id"],))}
        hl.append("<li>%s — %s: %s · %s, %s%s</li>" % (dm(h["day"]), {"count": "count", "edit": "corrected", "void": "voided",
                                                                        "unvoid": "un-voided"}.get(h["kind"], h["kind"]),
                                                       " · ".join("%s %s left" % (SIZE_LABEL[k], cs.get(k, "—")) for k in SIZE_KEYS),
                                                       name_of(h["saved_by"]), when(h["saved_at"]), (" · note: " + _esc(h["note"])) if h["note"] else ""))
    out.append("<div class='card'><h3>MORNING COUNTS SAVED</h3><ul class='hist'>%s</ul></div>" % ("".join(hl) or "<li>none yet</li>"))
    if own:
        out.append("<div class='card'><h3>SETTINGS</h3><form class='row' method='post' action='%s/owner/settings'>"
                   "<label class='ld'>Order line under <input class='tx sm2' name='order_days' value='%s' inputmode='numeric'> days left (both sizes)</label>"
                   "<label class='ld'>Shavez stands in from <input class='tx sm2' name='standin_after' value='%s'> (HH:MM) if the count is not saved</label>"
                   "<label class='ld'>Morning count due from <input type='date' name='count_from' value='%s'></label>"
                   "<label class='ld'>Spare boxes counted from <input type='date' name='spare_from' value='%s'></label>"
                   "<label class='ld'>Spare boxes on that day: 8×10 <input class='tx sm2' name='open_8x10' value='%s' placeholder='not set' inputmode='numeric'> "
                   "11×14 <input class='tx sm2' name='open_11x14' value='%s' placeholder='not set' inputmode='numeric'></label>"
                   "<label class='ld'>Hold a film bill read above <input class='tx sm2' name='max_boxes' value='%s' inputmode='numeric'> boxes "
                   "(check quantity)</label>"
                   "<button class='mini' type='submit'>Save settings</button></form></div>" % (
                       BASE, _esc(setting(con, "order.days")), _esc(setting(con, "standin.after")), _esc(setting(con, "count.from")),
                       _esc(setting(con, "spare.from")), _esc(setting(con, "spare.open.8x10")) if opening_set(con, "8x10") else "",
                       _esc(setting(con, "spare.open.11x14")) if opening_set(con, "11x14") else "", _esc(setting(con, "bill.max_boxes"))))
    st = studies(con)
    rows = []
    try:
        svc = list(con.execute("SELECT id, name FROM owner_service WHERE kind='xray' AND active=1 ORDER BY id"))
    except sqlite3.Error:
        svc = []
    for r in svc:
        size, films, b1 = st.get(r[0], ("", 1, 0))
        both_name = str(r[1] or "").strip().lower().startswith("both")
        if own:
            opts = "".join("<option value='%s'%s>%s</option>" % (k, " selected" if size == k else "", v)
                           for k, v in (("8x10", "8×10"), ("11x14", "11×14"), ("", "size not set")))
            fo = "".join("<option%s>%d</option>" % (" selected" if films == n else "", n) for n in (1, 2, 3, 4))
            bo = "".join("<option value='%s'%s>%s</option>" % (k, " selected" if b1 == int(k) else "", v)
                         for k, v in (("0", "both sides: twice the films"), ("1", "both sides on one film")))
            ctl = ("<form class='row' method='post' action='%s/owner/study'><input type='hidden' name='service_id' value='%d'>"
                   "<select name='size'>%s</select><select name='films'>%s</select>%s<button class='mini' type='submit'>Save</button></form>"
                   % (BASE, r[0], opts, fo, ("<input type='hidden' name='both_one' value='0'><span class='sm'>a 'Both' study: side B never doubles</span>"
                                             if both_name else "<select name='both_one'>%s</select>" % bo)))
        else:
            ctl = "%s · %d%s" % (SIZE_LABEL.get(size, "size not set"), films, " · both sides on one film" if b1 and not both_name else "")
        rows.append("<tr><td>%s</td><td>%s</td></tr>" % (_esc(r[1]), ctl))
    out.append("<details class='card'><summary><b>FILM SIZE AND FILMS PER STUDY</b> <span class='sm'>(your rate list's X-rays)</span></summary>"
               "<table class='grid'><tbody>%s</tbody></table></details>" % "".join(rows))
    return "".join(out)


# ============================================================================================ 3 · the X-ray list
@bp.route(BASE + "/list")
def list_page():
    u, lang, _own = _user()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    today = _today()
    ym = _month_arg(con, today)
    if ym is None:
        return redirect(BASE + "/list?msg=bad")
    hi = lang == "hi"
    lo = setting(con, "list.from")
    first, last = month_days(ym)
    d0 = max(first.isoformat(), lo)
    lines = slip_lines(con, d0, min(last, today).isoformat(), names=True)
    out = [_nav(lang, "list"), _msg(lang)]
    opts = []
    m = lo[:7]
    while m <= today.isoformat()[:7]:
        opts.append("<option value='%s'%s>%s</option>" % (m, " selected" if m == ym else "", mname(m, lang)))
        m = ym_shift(m, 1)
    out.append("<h2 class='pt'>%s</h2><p class='mut'>%s</p>"
               "<form class='row' method='get' action='%s/list'><label>%s <select name='m'>%s</select></label>"
               "<button class='mini' type='submit'>%s</button> <a class='btn' href='%s/list.xlsx?m=%s'>%s</a></form>" % (
                   "X-ray list — %s se" % dm(lo) if hi else "X-ray list — from %d %s" % (_d(lo).day, MONTHS[_d(lo).month - 1]),
                   "Har paid X-ray parchi, din ke hisaab se. Purani Excel jaisi hai waisi rahegi." if hi
                   else "Every paid X-ray slip, day by day. It replaces the X-ray Excel; the old Excel stays as it is.",
                   BASE, "Mahina" if hi else "Month", "".join(opts), "Dikhaiye" if hi else "Show", BASE, ym,
                   "Excel download" if hi else "Download Excel"))
    th = (("Tareekh", "Parchi no.", "Clinic ID", "Mareez", "X-ray", "Film", "Films", "Paid") if hi else
          ("Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Film", "Films", "Paid"))
    byday = {}
    for e in lines:
        byday.setdefault(e["day"], []).append(e)
    body = []
    for day in sorted(byday, reverse=True):
        es = byday[day]
        tot = {k: sum(e["films"] for e in es if e["size"] == k) for k in SIZE_KEYS}
        ns = sum(e["films"] for e in es if e["size"] not in SIZE_KEYS)
        body.append("<tr class='dh'><td colspan='8'><b>%s</b> · %d X-ray · 8×10: %d film · 11×14: %d film%s</td></tr>" % (
            ddm(day, lang), len(es), tot["8x10"], tot["11x14"], (" · %s: %d" % ("size nahi" if hi else "size not set", ns)) if ns else ""))
        for e in es:
            body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s%s</td><td>%s</td><td class='r'>%d</td><td>%s</td></tr>" % (
                dm(e["day"]), e["no"], _esc(e["cid"]), _esc(e["name"]), _esc(e["study"]), (" (%s)" % _esc(e["side"])) if e["side"] else "",
                SIZE_LABEL.get(e["size"], "size not set"), e["films"], e["paid"].upper() if e["paid"] == "upi" else e["paid"].title()))
    out.append("<div class='card'><table class='grid'><thead><tr>%s</tr></thead><tbody>%s</tbody></table><p class='mut'>%s</p></div>" % (
        "".join("<th>%s</th>" % h for h in th), "".join(body) or "<tr><td colspan='8'>%s</td></tr>" % ("Is mahine koi paid X-ray nahi" if hi else "No paid X-ray this month"),
        "Shavez ki paid parchi se bhari — koi type nahi karta. Din ka total film log mein jaata hai." if hi
        else "Filled from the paid slips Shavez enters — nobody types this list. Day totals feed the film log."))
    return _shell("X-ray list", "".join(out), lang)


# ============================================================================================ the Excel files
def _xlsx(sheets):
    import padwriter as PW                                             # noqa: PLC0415 -- the stdlib writer beside the finance app
    out = []
    for name, title, head, rows, widths in sheets:
        sh = PW.Sheet()
        sh.text(1, 0, title, PW.TITLE)
        for c, h in enumerate(head):
            sh.text(3, c, h, PW.HEADER)
        for i, row in enumerate(rows):
            for c, v in enumerate(row):
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    sh.num(4 + i, c, v, PW.BOX)
                else:
                    sh.text(4 + i, c, v, PW.BOX)
        for c, w in enumerate(widths):
            sh.widths[c] = w
        sh.freeze = "A4"
        out.append((name, sh))
    return PW.workbook_bytes_multi(out)


def _xlsx_resp(data, fname):
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="%s"' % fname, "Cache-Control": "no-store"})


@bp.route(BASE + "/log.xlsx")
def log_xlsx():
    u, lang, _own = _user()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    today = _today()
    ym = _month_arg(con, today)
    if ym is None:
        return redirect(BASE + "/log?msg=bad")
    ml = month_log(con, ym, today)
    rows = []
    for r in sorted(ml["rows"], key=lambda x: x["day"]):
        if r["kind"] == "span":
            s = r["s"]
            g = s["gap"]
            lw = ("late count — joins the next count" if s.get("pending") else "late count — two days combined") if s.get("late") else ""
            if s.get("pending") and lang == "hi":
                rows.append([r["day"], ("%s to %s" % (s["p"], s["end"])) if s["p"] != s["end"] else "", "", "", "", "", "", "", "", lw,
                             "%s %s" % (name_of(s["by"]), s["at"])])
                continue
            rows.append([r["day"], ("%s to %s" % (s["p"], s["end"])) if s["p"] != s["end"] else "", _num(s["machine"]["8x10"]), s["slips"]["8x10"],
                         _num(g["8x10"]), _num(s["machine"]["11x14"]), s["slips"]["11x14"], _num(g["11x14"]), s["slips"][""],
                         " ".join(["%s: naya box (machine se pata chala)" % SIZE_LABEL[z] for z in SIZE_KEYS if s["load"][z]] + ([lw] if lw else [])),
                         "%s %s" % (name_of(s["by"]), s["at"])])
        else:
            rows.append([r["day"], {"joined": "joined to the next count", "waiting": "waiting for the next count", "none": "not counted"}[r["kind"]],
                         "", "", "", "", "", "", "", "", ""])
    sts = {k: size_state(con, k, today) for k in SIZE_KEYS}
    summ = [["Days with a gap", ml["gapdays"]], ["Mornings not counted", ml["missed"]]]
    for k in SIZE_KEYS:
        st = sts[k]
        summ.append(["%s films left (the machine's screen)" % SIZE_LABEL[k], _num(int(round(st["left"])) if st["left"] is not None else None)])
        summ.append(["%s spare boxes" % SIZE_LABEL[k], _num(st["spare"])])
        summ.append(["%s days left" % SIZE_LABEL[k], _num(int(st["days"]) if st["days"] is not None else None)])
        summ.append(["%s average films a day (30 days)" % SIZE_LABEL[k], _num(round(st["avg"], 1) if st["avg"] is not None else None)])
    data = _xlsx([("Film log", "X-ray film log — %s" % mname(ym), ["Day", "Span", "8x10 machine", "8x10 slips", "8x10 gap", "11x14 machine",
                                                                    "11x14 slips", "11x14 gap", "Size not set", "New box", "Counted by"], rows,
                   [12, 26, 13, 11, 10, 13, 11, 10, 12, 30, 28]),
                  ("Summary", "X-ray film log — %s — summary" % mname(ym), ["What", "Figure"], summ, [40, 12])])
    return _xlsx_resp(data, "Xray_film_log_%s.xlsx" % ym)


def _num(v):
    return "" if v is None else v


@bp.route(BASE + "/list.xlsx")
def list_xlsx():
    u, lang, _own = _user()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    today = _today()
    ym = _month_arg(con, today)
    if ym is None:
        return redirect(BASE + "/list?msg=bad")
    lo = setting(con, "list.from")
    first, last = month_days(ym)
    lines = slip_lines(con, max(first.isoformat(), lo), min(last, today).isoformat(), names=True)
    rows = [[e["day"], e["no"], e["cid"], e["name"], e["study"] + ((" (%s)" % e["side"]) if e["side"] else ""),
             SIZE_LABEL.get(e["size"], "size not set"), e["films"], e["paid"].upper()] for e in lines]
    data = _xlsx([("X-ray list", "X-ray list — %s" % mname(ym), ["Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Film", "Films", "Paid"],
                   rows, [12, 9, 12, 28, 40, 12, 7, 7])])
    return _xlsx_resp(data, "Xray_list_%s.xlsx" % ym)


# ============================================================================================ 4 · the owner's changes
def _owner():
    u, lang, own = _user()
    return u if own else None


def _owner_post(what):
    return redirect(BASE + "/log?msg=saved&what=%s" % what)


@bp.route(BASE + "/owner/contact", methods=["POST"])
def owner_contact():
    u = _owner()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    op, who, at = request.form.get("op") or "", _who(u), _stamp()
    name = " ".join((request.form.get("name") or "").split())[:60]
    firm = " ".join((request.form.get("firm") or "").split())[:60]
    role = request.form.get("role") or ""
    raw_ph = (request.form.get("phone") or "").strip()
    phone = phone_digits(raw_ph)
    email = (request.form.get("email") or "").strip()[:120]
    if op in ("add", "edit"):
        if not name or role not in ROLE_LABEL or (raw_ph and not phone) or (email and not EMAIL_RE.match(email)):
            return redirect(BASE + "/log?msg=bad")
    if op == "add":
        rid = con.execute("INSERT INTO xf_contact (name, firm, role, phone, email, active, added_at, added_by) VALUES (?,?,?,?,?,1,?,?)",
                          (name, firm, role, phone, email, at, who)).lastrowid
        con.commit()
        _audit_safe(con, "xf_contact", rid, "add", None, dict(name=name, firm=firm, role=role, phone=bool(phone), email=bool(email)), who)
        return _owner_post("contact")
    try:
        cid = int(request.form.get("id") or 0)
    except ValueError:
        cid = 0
    r = con.execute("SELECT * FROM xf_contact WHERE id=?", (cid,)).fetchone()
    if r is None or op not in ("edit", "retire", "restore"):
        return redirect(BASE + "/log?msg=bad")
    if op == "edit":
        con.execute("UPDATE xf_contact SET name=?, firm=?, role=?, phone=?, email=?, changed_at=?, changed_by=? WHERE id=?",
                    (name, firm, role, phone, email, at, who, cid))
    else:
        con.execute("UPDATE xf_contact SET active=?, changed_at=?, changed_by=? WHERE id=?", (0 if op == "retire" else 1, at, who, cid))
    con.commit()
    _audit_safe(con, "xf_contact", cid, op, dict(name=r["name"], role=r["role"], active=r["active"]), dict(name=name or r["name"], op=op), who)
    return _owner_post("contact")


@bp.route(BASE + "/owner/settings", methods=["POST"])
def owner_settings():
    u = _owner()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    f = request.form
    od = (f.get("order_days") or setting(con, "order.days")).strip()
    sa = (f.get("standin_after") or setting(con, "standin.after")).strip()
    cf = (f.get("count_from") or setting(con, "count.from")).strip()
    sf = (f.get("spare_from") or setting(con, "spare.from")).strip()
    mb = (f.get("max_boxes") or setting(con, "bill.max_boxes")).strip()
    opens = []
    for k in SIZE_KEYS:                                                # typed (a 0 too) = set; left blank = as it was
        v = (f.get("open_" + k) or "").strip()
        if v and not re.match(r"^\d{1,2}$", v):
            return redirect(BASE + "/log?msg=bad")
        if v:
            opens.append(("spare.open." + k, v))
    if (not re.match(r"^\d{1,2}$", od) or not (1 <= int(od) <= 60) or not HM_RE.match(sa) or not DAY_RE.match(cf) or not DAY_RE.match(sf)
            or not re.match(r"^\d{1,2}$", mb) or not (1 <= int(mb) <= 99)):
        return redirect(BASE + "/log?msg=bad")
    who, at = _who(u), _stamp()
    for k, v in [("order.days", od), ("standin.after", sa), ("count.from", cf), ("spare.from", sf), ("bill.max_boxes", mb)] + opens:
        if setting(con, k) != v or (k.startswith("spare.open.") and not opening_set(con, k[len("spare.open."):])):
            rid = con.execute("INSERT INTO xf_setting (key, value, set_at, set_by) VALUES (?,?,?,?)", (k, v, at, who)).lastrowid
            con.commit()
            _audit_safe(con, "xf_setting", rid, "set", None, {k: v}, who)
    return _owner_post("settings")


@bp.route(BASE + "/owner/study", methods=["POST"])
def owner_study():
    u = _owner()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    try:
        sid = int(request.form.get("service_id") or 0)
        films = int(request.form.get("films") or 0)
    except ValueError:
        return redirect(BASE + "/log?msg=bad")
    size = request.form.get("size") or ""
    b1 = request.form.get("both_one") or "0"
    ok = con.execute("SELECT 1 FROM owner_service WHERE id=? AND kind='xray'", (sid,)).fetchone()
    if not ok or size not in SIZE_KEYS + ("",) or not (1 <= films <= 4) or b1 not in ("0", "1"):
        return redirect(BASE + "/log?msg=bad")
    who = _who(u)
    rid = con.execute("INSERT INTO xf_study (service_id, size, films, both_one, set_at, set_by) VALUES (?,?,?,?,?,?)",
                      (sid, size, films, int(b1), _stamp(), who)).lastrowid
    con.commit()
    _audit_safe(con, "xf_study", rid, "set", None, dict(service_id=sid, size=size, films=films, both_one=int(b1)), who)
    return _owner_post("study")


@bp.route(BASE + "/owner/billsize", methods=["POST"])
def owner_billsize():
    """The owner says what a film bill with no size on its lines is: 8x10, 11x14 or not film. Kept (append-only, audited) and
    laid over the Scan App's copy at once; the bill then counts in that size's spare stock (or nowhere)."""
    u = _owner()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    src = (request.form.get("src") or "").strip()[:200]
    size = request.form.get("size") or ""
    if size not in ("8x10", "11x14", "none") or not con.execute("SELECT 1 FROM xf_purchase WHERE src=? AND src LIKE 'bill:%:-'", (src,)).fetchone():
        return redirect(BASE + "/log?msg=bad")
    who = _who(u)
    rid = con.execute("INSERT INTO xf_bill_size (src, size, set_at, set_by) VALUES (?,?,?,?)", (src, size, _stamp(), who)).lastrowid
    con.commit()
    _audit_safe(con, "xf_bill_size", rid, "set", None, dict(src=src, size=size), who)
    sync_purchases(con)
    return _owner_post("billsize")


@bp.route(BASE + "/owner/billqty", methods=["POST"])
def owner_billqty():
    """The owner's word on a film bill's quantity: 'confirm' the boxes read, or 'fix' them (1-999). Kept (append-only, audited)
    and laid over the Scan App's copy at once; a held bill then counts in the spare stock."""
    u = _owner()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    src = (request.form.get("src") or "").strip()[:200]
    op = request.form.get("op") or ""
    row = con.execute("SELECT boxes, held FROM xf_purchase WHERE src=?", (src,)).fetchone()
    if row is None or op not in ("confirm", "fix"):
        return redirect(BASE + "/log?msg=bad")
    if op == "confirm":
        if row[0] is None:
            return redirect(BASE + "/log?msg=bad")
        q = float(row[0])
    else:
        v = (request.form.get("boxes") or "").strip()
        if not re.match(r"^\d{1,3}$", v) or int(v) < 1:
            return redirect(BASE + "/log?msg=bad")
        q = float(v)
    who = _who(u)
    rid = con.execute("INSERT INTO xf_bill_qty (src, boxes, set_at, set_by) VALUES (?,?,?,?)", (src, q, _stamp(), who)).lastrowid
    con.commit()
    _audit_safe(con, "xf_bill_qty", rid, op, dict(src=src, boxes=row[0], held=row[1]), dict(src=src, boxes=q), who)
    sync_purchases(con)
    return _owner_post("billqty")


@bp.route(BASE + "/owner/count", methods=["POST"])
def owner_count():
    """The owner corrects, voids or un-voids a morning's count -- any day up to today. Append-only: new xf_save / xf_count rows,
    the old rows kept; audited with the old and the new figures. A voided morning has no reading (the next count spans it); an
    un-void writes the voided figures back as the day's reading. Every figure after it -- used, box loads, the gap, the average,
    the spare stock -- is worked out again from the figures, so it all moves with the correction."""
    u = _owner()
    if u is None:
        return _denied()
    con = _db()
    _ensure(con)
    day = (request.form.get("day") or "").strip()
    op = request.form.get("op") or ""
    if not DAY_RE.match(day) or day > _today().isoformat() or op not in ("edit", "void", "unvoid"):
        return redirect(BASE + "/log?msg=bad")
    old = {k: day_reading(con, k, day) for k in SIZE_KEYS}
    if any(v is None for v in old.values()):
        return redirect(BASE + "/log?msg=nocount")
    if op == "unvoid" and not all(v[1] for v in old.values()):
        return redirect(BASE + "/log?msg=notvoid")
    if op != "unvoid" and any(v[1] for v in old.values()):
        return redirect(BASE + "/log?msg=nocount")
    vals, note = {k: old[k][0] for k in SIZE_KEYS}, ""
    if op == "edit":
        got, msg, _what = _figures(con, True, day, request.form)
        if msg:
            return redirect(BASE + "/log?msg=" + msg)
        vals, note = got
    at, who = _stamp(), _who(u)
    sid = con.execute("INSERT INTO xf_save (day, saved_at, saved_by, kind, note) VALUES (?,?,?,?,?)", (day, at, who, op, note)).lastrowid
    for k in SIZE_KEYS:
        con.execute("INSERT INTO xf_count (save_id, day, size, remaining, saved_at, saved_by, void) VALUES (?,?,?,?,?,?,?)",
                    (sid, day, k, vals[k], at, who, 1 if op == "void" else 0))
    con.commit()
    _audit_safe(con, "xf_save", sid, "count_" + op, ({k: old[k][0] for k in SIZE_KEYS} if op != "unvoid" else "void"),
                (vals if op != "void" else "void"), who)
    return _owner_post("count")


# ============================================================================================ the shell
def _shell(title, body, lang):
    return """<!doctype html><html lang="%s"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#3c464e;--line:#8a9aa6;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;--entry:#fffbe6;--amb:#fff1cc;--ambk:#8a5a00;--red:#8c2f2f;--grn:#2c6e2f}
*{box-sizing:border-box}
body{margin:0;padding:14px;background:var(--bg);color:var(--ink);font:18px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;max-width:1100px;margin:0 auto}
h1{font-size:21px;margin:0 0 10px;color:var(--accent)}h2{font-size:20px;margin:0 0 8px;color:var(--accent)}h3{margin:0 0 8px;font-size:18px}
h2.pt{margin:6px 0 6px}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:12px;margin:0 0 12px;overflow-x:auto}
details.card>summary,details>summary{cursor:pointer;min-height:44px;padding:6px 0}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:0 12px}
.mut{color:var(--mut);font-size:16px}.sm{font-size:14px;color:var(--mut);font-weight:400}
p.nav{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
a.back{display:inline-block;min-height:44px;line-height:44px;color:var(--accent);margin-right:6px}
.ch{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}.sz{font-size:21px}
table.grid{width:100%%;border-collapse:collapse;font-size:16px;background:var(--paper)}.grid th,.grid td{border:1px solid var(--line);padding:8px;vertical-align:top;text-align:left}
.grid th{font-size:13px;letter-spacing:.04em;color:var(--mut)}
tr.dh td{background:#eef2f5}tr.gp td{background:#fff7e0}tr.off td{opacity:.7;font-size:15px}
.r{text-align:right!important;white-space:nowrap}
input.num{width:100%%;min-width:70px;min-height:56px;font-size:26px;padding:6px 10px;border:2px solid #5b6b76;border-radius:8px;text-align:right;background:var(--entry)}
input.tx,select{min-height:44px;font-size:17px;padding:6px 8px;border:2px solid #5b6b76;border-radius:8px;background:var(--entry);max-width:100%%}
input.tx{width:200px}input.tx.sm2{width:90px}input[type=date]{min-height:44px;font-size:16px;border:2px solid #5b6b76;border-radius:8px;padding:4px}
button.save{width:100%%;min-height:56px;background:var(--accent);color:#fff;border:0;border-radius:10px;font-size:20px;font-weight:700;cursor:pointer;margin:6px 0 10px}
button.mini{min-height:44px;min-width:64px;background:var(--paper);color:var(--accent);border:2px solid var(--accent);border-radius:8px;font-size:16px;padding:6px 12px;cursor:pointer}
a.btn{display:inline-block;min-height:44px;line-height:40px;border:2px solid var(--accent);color:var(--accent);border-radius:9px;padding:0 12px;text-decoration:none;background:var(--paper);font-size:16px}
summary.mini{display:inline-block;min-height:44px;line-height:28px;background:var(--paper);color:var(--accent);border:2px solid var(--accent);border-radius:8px;font-size:16px;padding:6px 12px;cursor:pointer}
details.bx[open]{flex-basis:100%%}
a.btn.on{background:var(--accent);color:#fff}a.btn.wa{border-color:var(--grn);color:var(--grn)}
form.row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0}form.inl{display:inline}
.hn{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:8px 0;border-top:1px solid #d6dde2}.hn .hl{flex:1 0 200px;font-weight:600}
label.ck{min-height:44px;display:inline-flex;align-items:center;gap:6px;font-size:15px}label.ck input{width:22px;height:22px}
label.ld{display:block;margin:8px 0}
.warn{margin-top:8px;padding:8px 10px;background:var(--amb);border-left:6px solid var(--ambk);font-size:17px}
.card.remind{border-color:var(--ambk);background:var(--amb)}
.okc{color:var(--grn);font-weight:700}.gapc{color:var(--red);font-weight:700}
.okbar{background:#dff0d8;border-left:6px solid var(--grn);padding:8px 12px;margin:0 0 10px;font-size:16px}
ul.hist{margin:6px 0 0 18px;padding:0;font-size:15px}ul.hist li{min-height:44px}
.saved{background:#dff0d8;border:3px solid var(--grn);border-radius:12px;padding:12px 14px;margin:0 0 10px;font-size:18px}
.saved .sv1{font-size:24px;font-weight:800;color:#1e5a22;margin:0 0 6px}
.svt{border-collapse:collapse}.svt td{padding:3px 14px 3px 0;vertical-align:top}.svt td:first-child{color:var(--mut)}
.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:10px 14px;margin-bottom:12px}
@media (max-width:600px){body{padding:10px 16px}h1{font-size:18px}.grid td,.grid th{padding:6px}input.tx{width:100%%}}
</style></head><body><h1>%s</h1>
%s</body></html>""" % (lang, _esc(title), _esc(title), body)
