#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clinic_lists.py -- kit S689_CLINIC_LISTS (01-Nov-2026, the parent, session 373). D812: the owner's X-ray & procedures page.

THE OWNER'S RULINGS (01-Nov-2026, 00:08-00:29 IST, on mock-up v3 https://claude.ai/artifact/EbXFK5Zeb4eUo5ok9wb9T6), folded:
  1. ONE PAGE, FOR HIM ONLY (login manoj). "Separate page for Shavez and reception not required." Two tabs: Procedures and
     X-rays. Reached from a tile "X-ray & procedures" in the Patients folder of his portal home. The staff X-ray list inside the
     film log (xray_film.py, /finance/slips/film/list) is NOT touched.
  2. FROM 1-OCT-2026 (FROM below), month by month, grouped by day (newest first) with counts by kind; every row: date, slip
     no., clinic ID, patient, procedure / X-ray, side, kind (procedures) or film size and films (X-rays), paid, amount.
     Amounts (rate - discount, as written on the slip line) on every row, per day and per month: the page is his alone.
  3. A month picker, OR a From-To date range. An Excel download of exactly what is on the screen.
  4. A SEARCH BOX: patient name, clinic ID, slip number, procedure or X-ray name. With no From-To typed, a search looks through
     everything from 1-Oct to today, whatever month is picked.
  5. PROCEDURE KINDS: Casts & slabs = every fibre cast and fibre slab (the rate list's group "Cast / slab" whose name says cast
     or slab -- the clavicle bandage sits in that group but is NOT a cast or slab: Other). ILI = every line whose name starts
     with the word "ILI", the knee included (not "Ilizarov ...", not "iliac ...": cold review 1). Dressings = dressing. Other = clavicle bandage, stitch removal, glucometer, anything typed free.
  6. WHICH SLIP LINES: every X-ray (kind 'xray') or procedure (kind 'proc') line of an X-ray/Proc slip (series 'xp') in state
     'ok' -- cancelled, spoilt and void slips never show. S691 (the owner, 06:32-06:43 IST 01-Nov; D775): Paid is read from
     Docterz, never from the room's tick (retired 24-Oct): per patient, day and kind, the slip lines' total against that day's
     Docterz charges (xray_film.docterz_paid). Equal -> Docterz's mode (Cash, UPI, Card, "Paid (two ways)" -- never the words
     "split payment", his ruling of 13-Oct); different -> "Docterz Rs X for the day" (amber; that patient's total that day); that day's report in but no charge -> "Not in Docterz" (amber); no report for the day yet -> "Docterz not in
     yet"; a line whose rate minus discount is 0 -> Free. Every line is listed; none is hidden.
  7. DOCTERZ ONLY: a charge in that day's Docterz report (clinic_day_line, section 'proc' or 'xray', amount > 0) for a
     patient (clinic ID) with NO 'ok' X-ray/Proc slip line of that kind on that day is listed as "In Docterz only -- no slip",
     with Docterz's patient name, amount and mode; Docterz names no procedure, so the line has no kind until Shavez writes the
     slip (then it goes by itself). A Docterz X-ray charge of Rs 50 is the glucometer (clinic_money.HEAD_MOVES: Docterz bills it
     under X-ray, the counter under procedures): it is matched by a Rs 50 procedure line of that patient that day.
  8. X-RAY FILMS: each line's film size and films by the film log's own rule (xray_film.studies: the owner's per-study size and
     films; side B doubles unless the study is marked both-on-one or its name starts "Both"). If the film log is not mounted,
     size shows "-" and nothing else changes.

WHO REACHES WHAT -- at the server. /finance/slips/lists... is unit 'slips' by finance_app._unit_for_path; a login with no
slips row never gets past the front gate. Inside: ONLY the slips checker whose login is manoj; every other login (the other
checker bhawna, every maker) gets 403. Nothing is written anywhere: no table, no schema, no audit row, no file.
READ ONLY: slip, slip_item, owner_service, clinic_day_line, patient_ref (by slip_log.patient), xf_study (by xray_film.studies).
S842 (S467, 14-Nov-2026; D979 item 5): the X-rays tab carries a PHOTO column per patient and day -- Filed (opens the photo) /
Being filed / Issue / Pending (with its due day) / Not due yet / X-ray not done -- read from Check karein's own states
(check_screens.day_strip, S836; S834's due rule; a photo that day or the two after counts), never a copy of the rule; a 'Not
filed only' switch (?nf=1) and the Excel follow the screen. If those states cannot be read the column shows '-' and nothing
else changes. READ ONLY still (record_file and xray_filing are read through check_screens / one SELECT of record_file ids).
CLINICLISTS_NOW=<iso> pins the clock for the walk. No patient name, no number, no secret in this file (F-185).
"""
import datetime as dt
import os
import re
import urllib.parse

from flask import Blueprint, Response, redirect, request

bp = Blueprint("clinic_lists", __name__)
_db = None
_require = None
UNIT = "slips"
VERSION = "S842-CLINIC-LISTS-1.2"
BASE = "/finance/slips/lists"
OWNER = "manoj"
FROM = "2026-10-01"                                                 # the owner: "from 1-Oct-2026"
GLUCO_P = 5000                                                      # Rs 50: Docterz under X-ray, the slip under procedures
TABS = (("proc", "Procedures"), ("xray", "X-rays"))
KINDS = (("cast", "Casts & slabs"), ("ili", "ILI"), ("dress", "Dressings"), ("other", "Other"), ("dz", "Docterz only"))
KIND_LABEL = dict(KINDS)
KIND_SHORT = {"cast": "Cast/slab", "ili": "ILI", "dress": "Dressing", "other": "Other", "dz": "not on a slip"}
SIZE_LABEL = {"8x10": "8×10", "11x14": "11×14"}
SHEETS_XRAY = "/finance/clinic/sheets?kind=xray"                    # S691: his rate page, where a study's film size is set
YM_RE = re.compile(r"^(20\d\d)-(0[1-9]|1[0-2])$")
DAY_RE = re.compile(r"^20\d\d-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
MON = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
Q_MAX = 60


# ============================================================================================ mount
def init(app, db_getter, require_fn, audit_fn=None, unit="slips"):
    """Mount only; touches no database (F-303). audit_fn is accepted for the common mount shape and never used: nothing is written."""
    global _db, _require, UNIT
    _db, _require, UNIT = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


# ============================================================================================ small things
def _now():
    """IST, whatever the box's own zone (review 2); CLINICLISTS_NOW pins it for the walk."""
    v = os.environ.get("CLINICLISTS_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    try:
        from zoneinfo import ZoneInfo                                  # noqa: PLC0415
        return dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None, microsecond=0)
    except Exception:                                                  # noqa: BLE001
        return dt.datetime.now().replace(microsecond=0)


def _today():
    return _now().date()


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def _mark(text, q):
    """text escaped, with every case-blind match of q wrapped in <mark> (the match found on the raw text, each piece escaped)."""
    t = str(text if text is not None else "")
    if not q:
        return _esc(t)
    lo, ql, out, i = t.lower(), q.lower(), [], 0
    while True:
        j = lo.find(ql, i)
        if j < 0:
            out.append(_esc(t[i:]))
            break
        out.append(_esc(t[i:j]) + "<mark>" + _esc(t[j:j + len(q)]) + "</mark>")
        i = j + len(q)
    return "".join(out)


def _d(iso):
    return dt.date.fromisoformat(str(iso)[:10])


def dm(iso):
    try:
        d = _d(iso)
        return "%02d-%s" % (d.day, MON[d.month - 1])
    except (TypeError, ValueError):
        return str(iso or "")


def ddm(iso):
    try:
        d = _d(iso)
    except (TypeError, ValueError):
        return str(iso or "")
    return "%s %d %s %d" % (DAYS[d.weekday()], d.day, MON[d.month - 1], d.year)


def mname(ym):
    return "%s %d" % (MONTHS[int(ym[5:7]) - 1], int(ym[:4]))


def ym_shift(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) - 1 + k
    return "%04d-%02d" % (y + m // 12, m % 12 + 1)


def month_days(ym):
    first = dt.date(int(ym[:4]), int(ym[5:7]), 1)
    nxt = dt.date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    return first, nxt - dt.timedelta(days=1)


def rs(p):
    """paise -> 'Rs' text with Indian grouping, whole rupees (the slips hold whole rupees)."""
    v = int(round((p or 0) / 100.0))
    neg, v = v < 0, abs(v)
    s = str(v)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "₹" + s


def _has(con, table):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
    except Exception:                                                  # noqa: BLE001
        return False


def _owner():
    """The owner's login, or None. The page is his alone (the owner, 00:24 IST 01-Nov-2026)."""
    u, err = _require("checker", unit=UNIT)
    if err or str((u or {}).get("user") or "") != OWNER:
        return None
    return u


# ============================================================================================ the rules
def kind_of(name, grp):
    """The procedure's kind (ruling 5)."""
    n = (name or "").strip().lower()
    g = (grp or "").strip().lower()
    if re.match(r"ili\b", n):                                      # "ILI", "ILI (heel)", "ILI KNEE" -- never "Ilizarov", "iliac"
        return "ili"
    if g.startswith("cast") and ("cast" in n or "slab" in n):
        return "cast"
    if n == "dressing" or g == "dressing":
        return "dress"
    return "other"


def _marks(con, d0, d1):
    """Docterz's word per patient, day and kind (xray_film.docterz_paid); None when the film log module cannot be loaded."""
    try:
        import xray_film as XF                                         # noqa: PLC0415 -- the film log beside this app
        return XF.docterz_paid(con, d0, d1)
    except Exception:                                                  # noqa: BLE001
        return None


def _dzmode(m):
    """Docterz's mode in the page's words (xray_film.DZ_MODE): never the words "split payment" (his ruling of 13-Oct)."""
    m = (m or "").strip()
    try:
        import xray_film as XF                                         # noqa: PLC0415
        return XF.DZ_MODE.get(m.lower(), m.title())
    except Exception:                                                  # noqa: BLE001
        return "Paid (two ways)" if m.lower() == "split payment" else m.title()


def paid_of(mark, net_p):
    """(code, mode, docterz_p) for one slip line: 'free' when the line is 0; 'unk' when Docterz could not be read."""
    if net_p <= 0:
        return ("free", "", 0)
    return mark if mark else ("unk", "", 0)


def paid_text(e):
    """The Paid cell's words, and whether they are amber."""
    code, mode, p = e["pd"]
    if code == "ok":
        return mode or "Docterz", False
    if code == "free":
        return "Free", False
    if code == "differ":
        return "Docterz %s for the day" % rs(p), True
    if code == "none":
        return "Not in Docterz", True
    if code == "wait":
        return "Docterz not in yet", False
    return "—", False


def films_w(n):
    return "%d film" % n if n == 1 else "%d films" % n


def _studies(con):
    """The film log's own per-study size and films; {} (sizes shown as '-') when the film log is absent or fails."""
    try:
        import xray_film as XF                                         # noqa: PLC0415 -- the film log beside this app
        return XF.studies(con), True
    except Exception:                                                  # noqa: BLE001
        return {}, False


def films_of(st, service_id, sname, side):
    """(size, films) by the film log's rule (xray_film.slip_lines): side B doubles unless both-on-one or the name starts 'Both'."""
    size, films, b1 = st.get(service_id, ("", 1, 0)) if service_id is not None else ("", 1, 0)
    sd = (side or "").strip().upper()
    if sd in ("B", "BOTH") and not b1 and not (sname or "").strip().lower().startswith("both"):
        films *= 2
    return size, films


def _namer(con):
    cache = {}
    try:
        import slip_log as SL                                          # noqa: PLC0415 -- the slip book's own name rule
    except Exception:                                                  # noqa: BLE001
        SL = None

    def name(cid, seen):
        if seen:
            return seen
        if not cid or SL is None:
            return ""
        if cid not in cache:
            try:
                cache[cid] = (SL.patient(con, cid) or ("", ""))[0] or ""
            except Exception:                                          # noqa: BLE001
                cache[cid] = ""
        return cache[cid]
    return name


def slip_rows(con, tab, d0, d1):
    """Every line of kind tab ('proc' | 'xray') on an 'ok' X-ray/Proc slip from d0 to d1 (ruling 6), oldest first."""
    st, _ok = _studies(con) if tab == "xray" else ({}, False)
    nm = _namer(con)
    mk = _marks(con, d0, d1)
    q = ("SELECT s.id AS sid, s.day, s.slip_no, s.clinic_id, s.no_id_name, s.name_seen, s.paid_mode, i.service_id, "
         "i.name AS iname, i.side, COALESCE(i.price_p, 0) AS price_p, COALESCE(i.discount_p, 0) AS disc_p, "
         "o.name AS oname, o.grp AS ogrp FROM slip s JOIN slip_item i ON i.slip_id = s.id AND i.kind = ? "
         "LEFT JOIN owner_service o ON o.id = i.service_id "
         "WHERE s.series = 'xp' AND s.state = 'ok' AND s.day >= ? AND s.day <= ? ORDER BY s.day, s.slip_no, i.sort, i.id")
    out = []
    for r in con.execute(q, (tab, str(d0), str(d1))):
        item = r["oname"] or r["iname"] or ""
        price, disc = int(r["price_p"] or 0), int(r["disc_p"] or 0)
        net = price - disc
        cid = str(r["clinic_id"] or "").strip()
        e = dict(day=r["day"], no=r["slip_no"], cid=cid, name=nm(cid, (r["name_seen"] or r["no_id_name"] or "").strip()),
                 item=item, side=(r["side"] or "").strip(), amount_p=net, disc_p=disc if 0 < disc < price else 0,
                 dz=False, dmode="")
        e["pd"] = paid_of(None if mk is None else mk.get((r["day"], cid, tab), ("wait", "", 0)), net)
        e["paid"] = e["pd"][0]
        if tab == "proc":
            e["kind"] = kind_of(item, r["ogrp"] if r["service_id"] is not None else "")
        else:
            e["kind"] = "xray"
            e["size"], e["films"] = films_of(st, r["service_id"], item, r["side"])
        out.append(e)
    return out


def docterz_rows(con, tab, d0, d1):
    """Docterz charges of section tab with no 'ok' slip line of that kind for that patient that day (ruling 7)."""
    if not _has(con, "clinic_day_line"):
        return []
    have = set()
    for r in con.execute("SELECT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id = s.id AND i.kind = ? "
                         "WHERE s.series = 'xp' AND s.state = 'ok' AND s.day >= ? AND s.day <= ?", (tab, str(d0), str(d1))):
        have.add((r["day"], str(r["clinic_id"] or "").strip()))
    gluco = set()
    if tab == "xray":
        for r in con.execute("SELECT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id = s.id AND i.kind = 'proc' "
                             "WHERE s.series = 'xp' AND s.state = 'ok' AND s.day >= ? AND s.day <= ? "
                             "AND COALESCE(i.price_p, 0) = ?", (str(d0), str(d1), GLUCO_P)):
            gluco.add((r["day"], str(r["clinic_id"] or "").strip()))
    out = []
    for r in con.execute("SELECT business_date, sn, patient, clinic_id, amount_p, mode FROM clinic_day_line "
                         "WHERE section = ? AND amount_p > 0 AND business_date >= ? AND business_date <= ? "
                         "ORDER BY business_date, sn", (tab, str(d0), str(d1))):
        cid = str(r["clinic_id"] or "").strip()
        key = (r["business_date"], cid)
        if cid and key in have:
            continue
        if cid and tab == "xray" and int(r["amount_p"] or 0) == GLUCO_P and key in gluco:
            continue
        e = dict(day=r["business_date"], no="", cid=cid, name=(r["patient"] or "").strip(), item="In Docterz only — no slip",
                 side="", amount_p=int(r["amount_p"] or 0), disc_p=0, paid="dz", mode="", dz=True, dmode=_dzmode(r["mode"]),
                 kind="dz")
        if tab == "xray":
            e["size"], e["films"] = "", 0
        out.append(e)
    return out


def rows_for(con, tab, d0, d1, q=""):
    rows = slip_rows(con, tab, d0, d1) + docterz_rows(con, tab, d0, d1)
    if q:
        ql = q.lower()
        rows = [e for e in rows if ql in e["name"].lower() or ql in e["cid"].lower() or ql in str(e["no"]).lower()
                or (not e["dz"] and ql in e["item"].lower())]      # a Docterz-only row's words are ours, not a procedure (review 2)
    rows.sort(key=lambda e: (e["day"], 1 if e["dz"] else 0, str(e["no"]).zfill(9)))
    return rows


def summary(rows, tab):
    s = {"n": len(rows), "amt": sum(e["amount_p"] for e in rows), "free": sum(1 for e in rows if e["paid"] == "free"),
         "unpaid": sum(1 for e in rows if e["paid"] in ("differ", "none")), "days": len({e["day"] for e in rows})}
    if tab == "proc":
        s["kinds"] = {k: (sum(1 for e in rows if e["kind"] == k), sum(e["amount_p"] for e in rows if e["kind"] == k)) for k, _l in KINDS}
    else:
        s["films"] = {z: sum(e["films"] for e in rows if not e["dz"] and e["size"] == z) for z in SIZE_LABEL}
        s["nosize"] = sum(1 for e in rows if not e["dz"] and e["size"] not in SIZE_LABEL)
        s["dz"] = (sum(1 for e in rows if e["dz"]), sum(e["amount_p"] for e in rows if e["dz"]))
    return s


# ============================================================================================ S842: the photo of each X-ray
PHOTO_WORD = {"filed": "Filed", "filing": "Being filed", "issue": "Issue", "pending": "Pending", "notdue": "Not due yet",
              "notdone": "X-ray not done", "answered": "Answered"}
PHOTO_COUNT = {"filed": "filed", "filing": "being filed", "issue": "issue", "pending": "pending", "notdue": "not due yet",
               "notdone": "X-ray not done", "answered": "answered"}
RECORDS_FILE = "/finance/records/file/%d"                           # records.open_file: the photo itself
XRAY_CHECK = "/finance/records/xray-check"                          # his X-ray check page (S836)


def photo_map(con, d0, d1, today):
    """S842: {(day, clinic ID): [state, record_file id, due]} for the X-ray days d0..d1 -- the states Check karein's date strip
    gives (check_screens.day_strip, S836), never a copy of S834's due rule. None when they cannot be read."""
    try:
        import check_screens as CS                                     # noqa: PLC0415 -- beside this app
        CS._rec()
        days = (today - _d(d0)).days + 1
        if days < 1:
            return {}
        strip = CS.day_strip(con, min(days, 3000))
        due = CS._xray_days(con, d0, d1)
    except Exception:                                                  # noqa: BLE001 -- the sheet as it was
        return None
    out = {}
    for sd in strip:
        if d0 <= sd["day"] <= d1:
            for r_ in sd["x"]["rows"]:
                out[(sd["day"], r_["cid"])] = [r_["st"], 0, str(due.get((sd["day"], r_["cid"])) or "")]
    want = {}
    for (day, cid), v in out.items():
        if v[0] == "filed":
            want.setdefault(cid, []).append(day)
    if want:
        hi = (_d(d1) + dt.timedelta(days=2)).isoformat()
        for f in con.execute("SELECT id, clinic_id, day FROM record_file WHERE kind='xray' AND state='ok' AND day>=? AND day<=? "
                             "ORDER BY day, id", (d0, hi)):
            for day in want.get(f["clinic_id"], ()):
                v = out[(day, f["clinic_id"])]
                if not v[1] and day <= f["day"] <= (_d(day) + dt.timedelta(days=2)).isoformat():
                    v[1] = int(f["id"])
    return out


def photo_tag(rows, pm):
    """Each X-ray row gets e['ph'] = [state, file id, due] of its patient and day, or None (no clinic ID, or pm unreadable)."""
    for e in rows:
        e["ph"] = (pm or {}).get((e["day"], e["cid"])) if e["cid"] else None
    return rows


def photo_counts(rows):
    """Per patient and day (not per line): {state: n}."""
    seen = {}
    for e in rows:
        if e.get("ph"):
            seen[(e["day"], e["cid"])] = e["ph"][0]
    c = {}
    for st in seen.values():
        c[st] = c.get(st, 0) + 1
    return c


def not_filed(e):
    """'Not filed only': a row whose patient-day has a state other than filed / X-ray not done (a row with no clinic ID has none)."""
    return bool(e.get("ph")) and e["ph"][0] not in ("filed", "notdone")


def photo_cell(e):
    ph = e.get("ph")
    if not ph:
        return "—"
    st, fid, due = ph
    if st == "filed":
        return ("<a href='%s' target='_blank' rel='noopener'>Filed&nbsp;&#8599;</a>" % (RECORDS_FILE % fid)) if fid else "Filed"
    if st == "pending":
        return "<span class='red'>Pending</span>%s" % ((" <span class='sm'>due %s</span>" % dm(due)) if due else "")
    if st == "issue":
        return "<a class='amb' href='%s'>Issue</a>" % XRAY_CHECK
    if st in ("notdue", "filing", "answered", "notdone"):
        return "<span class='sm'>%s</span>" % PHOTO_WORD[st]
    return _esc(PHOTO_WORD.get(st, st))


def photo_text(e):
    ph = e.get("ph")
    if not ph:
        return ""
    return PHOTO_WORD.get(ph[0], ph[0]) + ((" (due %s)" % dm(ph[2])) if ph[0] == "pending" and ph[2] else "")


# ============================================================================================ the request
def _args(today):
    """(d0, d1, q, ym, how, bad): the range to show. A typed From-To wins; else a search spans 1-Oct to today; else the month."""
    q = (request.args.get("q") or "").strip()[:Q_MAX]
    f, t, m = (request.args.get("f") or "").strip(), (request.args.get("t") or "").strip(), (request.args.get("m") or "").strip()
    lo, hi = _d(FROM), today
    if hi < lo:
        hi = lo
    bad = ""
    if f or t:
        try:
            d0 = _d(f) if f else lo
            d1 = _d(t) if t else hi
            if not ((not f or DAY_RE.match(f)) and (not t or DAY_RE.match(t))):
                raise ValueError(f + t)
        except (TypeError, ValueError):
            d0 = d1 = None
            bad = "That date is not a date, so it was left out."
        if d0 is not None:
            if d0 > d1:
                d0, d1 = d1, d0
            d0, d1 = max(d0, lo), min(d1, hi)
            if d0 > d1:
                d0, d1 = lo, hi
                bad = "Those dates are outside 1 October to today. Showing 1 October to today."
            return d0, d1, q, "", "range", bad
    if q:
        return lo, hi, q, "", "search", bad
    ym = m if (m and YM_RE.match(m) and FROM[:7] <= m <= hi.isoformat()[:7]) else hi.isoformat()[:7]
    if m and ym != m and not bad:
        bad = "That month is outside 1 October to today. Showing %s." % mname(ym)
    first, last = month_days(ym)
    return max(first, lo), min(last, hi), q, ym, "month", bad


def _qs(**kw):
    return urllib.parse.urlencode([(k, v) for k, v in kw.items() if v])


def _deny():
    return _shell("Not permitted", "<div class='card'><h2>Not permitted</h2><p>This page is Dr Manoj's alone.</p></div>"), 403


@bp.route(BASE)
def hub():
    if _owner() is None:
        return _deny()
    return redirect(BASE + "/proc")


@bp.route(BASE + "/<tab>")
def page(tab):
    if tab not in ("proc", "xray"):
        return _deny() if _owner() is None else (redirect(BASE + "/proc"))
    if _owner() is None:
        return _deny()
    con = _db()
    today = _today()
    d0, d1, q, ym, how, bad = _args(today)
    rows = rows_for(con, tab, d0.isoformat(), d1.isoformat(), q)
    xr = tab == "xray"
    nf = xr and request.args.get("nf") == "1"                          # S842: 'Not filed only'
    pc, pm = {}, None
    if xr:
        pm = photo_map(con, d0.isoformat(), d1.isoformat(), today)
        photo_tag(rows, pm)
        pc = photo_counts(rows)
        if pm is None:
            nf = False                                                 # states unreadable: the switch does nothing
        if nf:
            rows = [e for e in rows if not_filed(e)]
    s = summary(rows, tab)
    word = "X-ray" if xr else "procedure"
    keep = dict(q=q, f=request.args.get("f", "") if how == "range" else "", t=request.args.get("t", "") if how == "range" else "",
                m=ym if how == "month" else "", nf="1" if nf else "")
    out = ["<p class='nav'><a class='back' href='/portal'>&larr; Portal</a>"]
    for k, label in TABS:
        out.append("<a class='btn%s' href='%s/%s%s'>%s</a>" % (" on" if k == tab else "", BASE, k, ("?" + _qs(**keep)) if _qs(**keep) else "", label))
    out.append("</p>")
    if bad:
        out.append("<div class='warn'>%s</div>" % _esc(bad))
    opts = []
    mm = FROM[:7]
    while mm <= today.isoformat()[:7]:
        opts.append("<option value='%s'%s>%s</option>" % (mm, " selected" if mm == (ym or today.isoformat()[:7]) else "", mname(mm)))
        mm = ym_shift(mm, 1)
    out.append(
        "<div class='card'><h2>%s — from 1 October 2026</h2>"
        "<p class='mut'>Every %s on an X-ray/Proc slip, day by day. It fills itself from the slips; nobody types it.</p>"
        "<form method='get' action='%s/%s'>"
        "<label class='ld' for='q'>Search patient, clinic ID, slip no. or %s<br>"
        "<input class='srch' id='q' type='search' name='q' value='%s' maxlength='%d' autocomplete='off' placeholder='%s'></label>"
        "<div class='row'><label for='m'>Month <select id='m' name='m'>%s</select></label>"
        "<label for='f'>or from <input id='f' type='date' name='f' value='%s' min='%s' max='%s'></label>"
        "<label for='t'>to <input id='t' type='date' name='t' value='%s' min='%s' max='%s'></label>"
        "<button class='mini' type='submit'>Show</button> <a class='btn' href='%s/%s.xlsx?%s'>Download Excel</a>"
        "%s</div></form></div>" % (
            "X-rays" if xr else "Procedures", word, BASE, tab, word, _esc(q), Q_MAX,
            "e.g. a name, clinic ID, slip no., knee" if xr else "e.g. a name, clinic ID, slip no., ILI, cast",
            "".join(opts), _esc(keep["f"]), FROM, today.isoformat(), _esc(keep["t"]), FROM, today.isoformat(),
            BASE, tab, _qs(**keep, a=d0.isoformat(), b=d1.isoformat()),
            (" <a class='btn' href='%s/%s'>Clear</a>" % (BASE, tab)) if (q or how == "range") else ""))
    # the summary
    if how == "search":
        head = "Search “%s” across 1 Oct 2026 – %s" % (_esc(q), dm(d1.isoformat()))
    elif how == "range":
        head = "%s to %s%s" % (ddm(d0.isoformat()), ddm(d1.isoformat()), (" · search “%s”" % _esc(q)) if q else "")
    else:
        head = mname(ym) + ((" (to %s)" % dm(d1.isoformat())) if d1 < month_days(ym)[1] else "")
    tiles = ["<div><b>%d</b><span>All %ss</span><em>%s</em></div>" % (s["n"], word, rs(s["amt"]))]
    if xr:
        for z, lab in SIZE_LABEL.items():
            tiles.append("<div><b>%d</b><span>%s films</span></div>" % (s["films"][z], lab))
        tiles.append("<div><b>%d</b><span><a href='%s'>Size not set</a></span></div>" % (s["nosize"], SHEETS_XRAY))
        tiles.append("<div><b>%d</b><span>Docterz only</span><em>%s</em></div>" % (s["dz"][0], rs(s["dz"][1])))
    else:
        for k, lab in KINDS:
            n, a = s["kinds"][k]
            tiles.append("<div><b>%d</b><span>%s</span><em>%s</em></div>" % (n, _esc(lab), rs(a)))
    extra = []
    if s["free"]:
        extra.append("%d free" % s["free"])
    if s["unpaid"]:
        extra.append("%d line%s not matching Docterz" % (s["unpaid"], "" if s["unpaid"] == 1 else "s"))
    photo = ""
    if xr:                                                             # S842: the photos, per patient and day
        nnf = sum(v for k, v in pc.items() if k not in ("filed", "notdone"))
        bits = ["<b>%d</b> %s" % (pc[k], PHOTO_COUNT[k]) for k in ("filed", "pending", "issue", "filing", "notdue", "notdone", "answered")
                if pc.get(k)]
        sw = dict(keep, nf="" if nf else "1")
        photo = "<p class='mut' style='margin-top:8px'>Photos: their states could not be read just now (the column shows —).</p>" if pm is None else (
            "<p class='mut' style='margin-top:8px'>Photos (per patient and day): %s %s</p>" % (
            " · ".join(bits) or "none yet",
            ("<a class='btn on' href='%s/xray?%s'>Show all</a>" % (BASE, _qs(**sw))) if nf else
            ("<a class='btn' href='%s/xray?%s'>Not filed only (%d)</a>" % (BASE, _qs(**sw), nnf))))
    out.append("<div class='card'><p class='mut'>%s · %d day%s%s</p><div class='sum'>%s</div>%s</div>" % (
        head, s["days"], "" if s["days"] == 1 else "s", (" · " + " · ".join(extra)) if extra else "", "".join(tiles), photo))
    # the table
    th = (["Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Side", "Film", "Films", "Photo", "Paid", "Amount"] if xr else
          ["Date", "Slip no.", "Clinic ID", "Patient", "Procedure", "Side", "Kind", "Paid", "Amount"])
    byday = {}
    for e in rows:
        byday.setdefault(e["day"], []).append(e)
    body = []
    for day in sorted(byday, reverse=True):
        es = byday[day]
        if xr:
            chips = "".join("<span class='chip'>%s: %s</span>" % (lab, films_w(sum(e["films"] for e in es if not e["dz"] and e["size"] == z)))
                            for z, lab in SIZE_LABEL.items())
            ndz = sum(1 for e in es if e["dz"])
            if ndz:
                chips += "<span class='chip dzc'>Docterz only: %d</span>" % ndz
        else:
            chips = "".join("<span class='chip%s'>%s: %d</span>" % (" dzc" if k == "dz" else "", _esc(lab), sum(1 for e in es if e["kind"] == k))
                            for k, lab in KINDS if any(e["kind"] == k for e in es))
        body.append("<tr class='dh'><td colspan='%d'><b>%s</b> · %d %s%s%s <span class='chip'>%s</span></td></tr>" % (
            len(th), ddm(day), len(es), word, "" if len(es) == 1 else "s", chips, rs(sum(e["amount_p"] for e in es))))
        for e in es:
            if e["dz"]:
                paid = "<span class='amb'>Docterz: %s</span>" % _esc(e["dmode"] or "—")
                amt = rs(e["amount_p"])
                item = "<span class='amb'>%s</span>" % _esc(e["item"])
            else:
                pw, amber = paid_text(e)
                paid = ("<span class='amb'>%s</span>" % _esc(pw)) if amber else _esc(pw)
                amt = ("0 <span class='sm'>free</span>" if e["paid"] == "free" else
                       rs(e["amount_p"]) + ((" <span class='sm'>(disc. %s)</span>" % rs(e["disc_p"])) if e["disc_p"] else ""))
                item = _mark(e["item"], q)
            cells = [dm(e["day"]), _mark(e["no"], q) if e["no"] != "" else "—", _mark(e["cid"], q) or "—", _mark(e["name"], q), item,
                     _esc(e["side"]) or "—"]
            if xr:
                cells += ["—" if e["dz"] else (SIZE_LABEL.get(e["size"]) or "<a href='%s'>size not set</a>" % SHEETS_XRAY),
                          ("%d" % e["films"]) if not e["dz"] else "—", photo_cell(e)]
            else:
                cells += ["<span class='amb'>not on a slip</span>" if e["dz"] else KIND_SHORT[e["kind"]]]
            cells += [paid, amt]
            body.append("<tr>%s</tr>" % "".join(
                "<td%s>%s</td>" % (" class='r'" if (i == len(cells) - 1 or (xr and i == 7)) else "", c) for i, c in enumerate(cells)))
    empty = ("Nothing matches “%s”." % _esc(q)) if q else (("Every X-ray in these days has its photo filed." if nf else "No %s in these days." % word))
    out.append("<div class='card'><table class='grid'><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
               "<p class='mut'>Filled from the X-ray/Proc slips (cancelled and void slips never show). <i>Docterz only</i>: "
               "charged in that day's Docterz report with no slip line for that patient — Docterz names no procedure; it moves "
               "into its kind once the slip is written.</p></div>" % (
                   "".join("<th%s>%s</th>" % (" class='r'" if (i == len(th) - 1 or (xr and h == "Films")) else "", h) for i, h in enumerate(th)),
                   "".join(body) or "<tr><td colspan='%d'>%s</td></tr>" % (len(th), empty)))
    return _shell("X-ray & procedures", "".join(out))


# ============================================================================================ the Excel
def _xlsx(name, title, head, rows, widths):
    import padwriter as PW                                             # noqa: PLC0415 -- the stdlib writer beside the finance app
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
    return PW.workbook_bytes_multi([(name, sh)])


@bp.route(BASE + "/<tab>.xlsx")
def xlsx(tab):
    if _owner() is None or tab not in ("proc", "xray"):
        return _deny()
    con = _db()
    today = _today()
    d0, d1, q, _ym, _how, _bad = _args(today)
    rows = rows_for(con, tab, d0.isoformat(), d1.isoformat(), q)
    xr = tab == "xray"
    if xr:                                                             # S842: the photo column, and 'Not filed only' as on the screen
        pm = photo_map(con, d0.isoformat(), d1.isoformat(), today)
        photo_tag(rows, pm)
        if pm is not None and request.args.get("nf") == "1":
            rows = [e for e in rows if not_filed(e)]
    data = []
    for e in rows:
        r = [e["day"], e["no"] if e["no"] != "" else "", e["cid"], e["name"], e["item"], e["side"]]
        if xr:
            r += ["" if e["dz"] else SIZE_LABEL.get(e["size"], "size not set"), "" if e["dz"] else e["films"], photo_text(e)]
        else:
            r += ["Docterz only" if e["dz"] else KIND_SHORT[e["kind"]]]
        r += [("Docterz: " + (e["dmode"] or "-")) if e["dz"] else paid_text(e)[0], e["amount_p"] / 100.0,
              e["disc_p"] / 100.0 if e["disc_p"] else ""]
        data.append(r)
    head = (["Date", "Slip no.", "Clinic ID", "Patient", "X-ray", "Side", "Film", "Films", "Photo", "Paid", "Amount (Rs)", "Discount (Rs)"] if xr
            else ["Date", "Slip no.", "Clinic ID", "Patient", "Procedure", "Side", "Kind", "Paid", "Amount (Rs)", "Discount (Rs)"])
    widths = [12, 9, 12, 28, 40, 6] + ([12, 7, 18] if xr else [14]) + [16, 12, 12]
    title = "%s — %s to %s%s" % ("X-rays" if xr else "Procedures", d0.isoformat(), d1.isoformat(), (" — search: %s" % q) if q else "")
    body = _xlsx("X-rays" if xr else "Procedures", title, head, data, widths)
    fname = "%s_%s_to_%s.xlsx" % ("Xrays" if xr else "Procedures", d0.isoformat(), d1.isoformat())
    return Response(body, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="%s"' % fname, "Cache-Control": "no-store"})


# ============================================================================================ the shell
def _shell(title, body):
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#3c464e;--line:#8a9aa6;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;--amb:#fff1cc;--ambk:#8a5a00;--hit:#ffe66d}
*{box-sizing:border-box}
body{margin:0 auto;padding:14px;background:var(--bg);color:var(--ink);font:17px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;max-width:1180px}
h2{font-size:20px;margin:0 0 6px;color:var(--accent)}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:12px;margin:0 0 12px;overflow-x:auto}
.mut{color:var(--mut);font-size:15px;margin:0 0 6px}.sm{font-size:13px;color:var(--mut)}
p.nav{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 10px}
a.back{display:inline-block;min-height:44px;line-height:44px;color:var(--accent);margin-right:6px}
a.btn{display:inline-block;min-height:44px;line-height:40px;border:2px solid var(--accent);color:var(--accent);border-radius:9px;padding:0 14px;text-decoration:none;background:var(--paper);font-size:16px}
a.btn.on{background:var(--accent);color:#fff}
label.ld{display:block;margin:6px 0 8px;font-size:15px;color:var(--mut)}
input.srch{width:100%%;min-height:50px;font-size:19px;padding:8px 12px;border:3px solid var(--accent);border-radius:9px;background:#fff;margin-top:4px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.row label{font-size:15px;color:var(--mut)}
select,input[type=date]{min-height:44px;font-size:16px;padding:4px 8px;border:2px solid #5b6b76;border-radius:8px;background:#fff}
button.mini{min-height:44px;min-width:70px;background:var(--accent);color:#fff;border:0;border-radius:8px;font-size:16px;padding:6px 14px;cursor:pointer}
.sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px}
.sum div{background:#eef2f5;border-radius:8px;padding:8px 10px}
.sum b{display:block;font-size:22px;font-variant-numeric:tabular-nums}.sum span{font-size:13px;color:var(--mut)}
.sum em{display:block;font-style:normal;font-size:14px;color:var(--accent);font-variant-numeric:tabular-nums}
table.grid{width:100%%;border-collapse:collapse;font-size:15px;min-width:820px;font-variant-numeric:tabular-nums}
.grid th,.grid td{border:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}
.grid th{font-size:13px;letter-spacing:.04em;color:var(--mut)}
tr.dh td{background:#eef2f5}
.chip{display:inline-block;padding:0 8px;border-radius:10px;background:#dde8f1;color:var(--accent);font-size:13px;margin-left:6px;white-space:nowrap}
.chip.dzc,.amb{color:var(--ambk)}.chip.dzc{background:var(--amb)}
.r{text-align:right!important;white-space:nowrap}
.red{color:#9c2a20;font-weight:600}
.warn{margin:0 0 10px;padding:8px 10px;background:var(--amb);border-left:6px solid var(--ambk)}
mark{background:var(--hit);color:inherit;border-radius:2px}
</style></head><body>%s</body></html>""" % (_esc(title), body)
    return Response(html, mimetype="text/html", headers={"Cache-Control": "no-store"})
