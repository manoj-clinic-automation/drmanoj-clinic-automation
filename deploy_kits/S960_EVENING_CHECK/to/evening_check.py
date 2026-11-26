#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evening_check.py -- kit S960_EVENING_CHECK (session S527, 26-Nov-2026; D1080, the Morning Match kit A). PARENT. NEW.

THE OWNER, 26-Nov-2026 (12:21, 12:30, his "ok" 12:58 IST on the Morning Match mock-up v2.1): at closing, reception AND Shavez are
told in the least time which slips of the day Docterz does not carry, and again when a corrected export clears them -- "15 minutes
is too much at closing"; "a all good notification also if 1st export has no issues".

WHAT IT DOES. The moment a consultation report of TODAY is taken by docterz_pickup.take() -- either road: the reception PC's direct
upload (reception_door.py) or the Drive pickup -- take() starts this file in its own process (it never waits for it, and nothing
here can fail the take). It reads the stored export itself (never through the tracker's 180-second quiet, its runner or
docterz_ingest -- that chain takes half an hour) and finds the day's slips Docterz does not carry:
    an OPD slip whose clinic ID has no row in the export;  an X-ray / procedure slip whose clinic ID has no row of that kind
    (X-ray = Laboratory + Radiology, as the tracker's revenue.py reads it; procedure = Procedure amount or discount)
-- the same rules as the owner's "Slips not in Docterz" list (not_in_docterz.rows): state ok, a clinic ID of digits, no radd, no
name-only slip, a free line left out, and a slip he (or the desk) has already answered there left out.
It then pushes ONCE PER EXPORT to the logins in EVCHK_TO (shavez, reception) through the call-back clock's own road
(callback_clock.send: the portal's Web Push; ntfy for a login with no device, when a staff topic is set):
    slips missing          -> "N parchi Docterz mein nahi" + the names
    the day's first export clean            -> "<day>: sab parchi Docterz mein" -- "PC band kar sakte hain"
    a later export clears a list it named    -> "Sab parchi Docterz mein" -- "kaam poora"
    a later clean export after a clean one   -> nothing (already told)
Only an export of TODAY taken from EVCHK_FROM (17:00; Sunday EVCHK_SUN_FROM 12:00) is judged ("PC band kar sakte hain" only after
the closing, EVCHK_CLOSE 20:30 / Sunday 14:30) -- a morning catch-up of an
earlier day, or an afternoon export, is left alone. Pushes go out only when the database is the live one (EVCHK_LIVE_DB): a
walk or a rehearsal on a made-up database records its answer and pushes nothing.

THE DESK. parchi_desk.page() shows panel_html() at the top of the slip desk (today, after an evening export): each slip, its
clinic ID and number, what, the amount, and "Paise nahi liye" (the owner's answer 'free' on the same nid_mark row his list
uses -- the row then leaves his list and this one). The panel re-reads itself every 30 seconds, so it clears by itself about a
minute after a corrected export. Its two doors (GET /finance/slips/desk/api/evening, POST .../evening/free) carry the desk's
own gate (unit slips, maker / checker).

ONE TABLE OF ITS OWN, created on first use (F-303 -- the readers never create it):
    evening_check_push  export_id (the docterz_export row), day, at, missing, outcome (claimed | missing | clean | cleared |
                        quiet | unread | off), slips (slip_id:kind, no names), sent
It reads docterz_export (and the stored file it names), slip, slip_item, slip_adjust, nid_mark, dx_visit, clinic_day_line
(the usual fee), patient_ref. It writes evening_check_push, and nid_mark only through "Paise nahi liye" (audited).
No patient name, no number, no secret in this file (F-185).

    /root/wa/venv/bin/python3 -B /root/finance/evening_check.py --export ID [--db PATH]    (started by docterz_pickup.take)
    /root/wa/venv/bin/python3 -B /root/finance/evening_check.py --status [--day YYYY-MM-DD] (counts only)
"""
import csv
import datetime as dt
import fcntl
import html as _h
import io
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "S960 1"
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
LIVE_DB = os.environ.get("EVCHK_LIVE_DB", "/root/finance/finance.db")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
TO_DEFAULT = "shavez,reception"
DESK_URL = "/finance/slips/desk"
HOME_URL = "/portal"
DESK_LOGINS = ("shavez", "bhati", "manoj")                # logins the desk admits (unit slips); any other lands on the portal
FROM_DEFAULT = "17:00"
SUN_FROM_DEFAULT = "12:00"
API = "/finance/slips/desk/api/evening"
KIND_EN = {"opd": "OPD consultation", "xray": "X-ray", "proc": "Procedure"}
KIND_HI = {"opd": "OPD consultation", "xray": "X-ray", "proc": "Procedure"}
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
UID_OK = re.compile(r"[A-Z0-9]{8,14}")
CLOSE_DEFAULT = "20:30"                                   # the clinic's closing (callback_clock's CLOSE_HM); Sunday 14:30
SUN_CLOSE_DEFAULT = "14:30"
PUSHER = None                                             # the walk hands in a stub (login, payload) -> (ok, failed)
CC_MOD = None                                             # the walk may hand in a callback_clock module
_U = {"db": None, "require": None, "audit": None, "unit": "slips"}

DDL = """
CREATE TABLE IF NOT EXISTS evening_check_push (
  export_id  INTEGER PRIMARY KEY,
  day        TEXT NOT NULL,
  at         TEXT NOT NULL,
  missing    INTEGER NOT NULL DEFAULT 0,
  outcome    TEXT NOT NULL DEFAULT 'claimed',
  slips      TEXT NOT NULL DEFAULT '',
  sent       TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_evening_check_push_day ON evening_check_push(day);
"""


# ---------------------------------------------------------------------------------------------------------------- basics
def now_ist():
    """The IST clock; EVCHK_NOW=<iso> pins it for the walk."""
    v = os.environ.get("EVCHK_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)


def _stamp(t=None):
    return (t or now_ist()).strftime("%Y-%m-%d %H:%M:%S")


def _has(con, table):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
    except sqlite3.Error:
        return False


def ensure(con):
    con.executescript(DDL)
    con.commit()


def _cc():
    """The call-back clock (its settings reader and its send road), or None."""
    if CC_MOD is not None:
        return CC_MOD
    try:
        if PORTAL_DIR not in sys.path:
            sys.path.insert(0, PORTAL_DIR)
        import callback_clock as cc                       # noqa: PLC0415
        return cc
    except Exception:                                     # noqa: BLE001
        return None


def cfg(name, default=""):
    """As the portal reads a setting (portal_config.py, then the environment) -- through the clock's own reader."""
    cc = _cc()
    if cc is not None:
        try:
            return cc.cfg(name, default)
        except Exception:                                 # noqa: BLE001
            pass
    v = os.environ.get(name, "").strip()
    return v or default


def _hm(s, default):
    """'HH:MM' -> a time; a bad setting falls back to the default, never to an error."""
    for v in (s, default):
        m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", str(v or ""))
        if m and int(m.group(1)) < 24 and int(m.group(2)) < 60:
            return dt.time(int(m.group(1)), int(m.group(2)))
    return dt.time(17, 0)


def evening_from(day_iso):
    d = dt.date.fromisoformat(day_iso)
    if d.weekday() == 6:
        return _hm(cfg("EVCHK_SUN_FROM", SUN_FROM_DEFAULT), SUN_FROM_DEFAULT)
    return _hm(cfg("EVCHK_FROM", FROM_DEFAULT), FROM_DEFAULT)


def closing(day_iso):
    d = dt.date.fromisoformat(day_iso)
    if d.weekday() == 6:
        return _hm(cfg("EVCHK_SUN_CLOSE", SUN_CLOSE_DEFAULT), SUN_CLOSE_DEFAULT)
    return _hm(cfg("EVCHK_CLOSE", CLOSE_DEFAULT), CLOSE_DEFAULT)


def is_on():
    return cfg("EVCHK_ON", "1").lower() not in ("0", "off", "no", "false")


def _num(x):
    try:
        return float(str(x or "").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def _cid(x):
    s = str(x or "").strip()
    if not s or s.lower() == "nan":
        return ""
    try:
        return str(int(float(s)))
    except (ValueError, OverflowError):
        return s if re.fullmatch(r"\d{1,12}", s) else ""


def _parse_date(s):
    s = str(s or "").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def utc_to_ist(s):
    """A Drive / reception time ('2026-11-26T15:40:12.000Z') -> an IST datetime, or None."""
    try:
        u = dt.datetime.strptime(str(s or "")[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None
    return u + dt.timedelta(hours=5, minutes=30)


def dm(day_iso):
    try:
        return dt.date.fromisoformat(day_iso).strftime("%d-%b")
    except ValueError:
        return day_iso


# ---------------------------------------------------------------------------------------------------------------- the export
def read_export(raw, day):
    """{clinic_id: {'opd', 'xray', 'proc'}} -- the patients of `day` the consultation report carries. None if not readable."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            return None
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return None
    if not rows:
        return None
    idx = {h.strip(): i for i, h in enumerate(rows[0])}
    if "Consultation Date" not in idx or "Clinic Specific Id" not in idx:
        return None

    def get(r, k):
        i = idx.get(k)
        return r[i] if i is not None and len(r) > i else ""

    out = {}
    for r in rows[1:]:
        d = _parse_date(get(r, "Consultation Date"))
        if d is None or d.isoformat() != day:
            continue
        c = _cid(get(r, "Clinic Specific Id"))
        if not c or not UID_OK.fullmatch(str(get(r, "Patient UID") or "").strip()):
            continue                                      # revenue.py's guard: only a UID-shaped row is a patient
        k = out.setdefault(c, set())
        k.add("opd")
        if _num(get(r, "Laboratory Amount")) + _num(get(r, "Radiology Amount")) > 0:   # revenue.py: Xray > 0
            k.add("xray")
        if _num(get(r, "Procedure Amount")) > 0 or _num(get(r, "Procedure Discount")) > 0:
            k.add("proc")
    return out


def current_export(con, day):
    if not _has(con, "docterz_export"):
        return None
    r = con.execute("SELECT * FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' "
                    "ORDER BY id DESC LIMIT 1", (day,)).fetchone()
    return dict(r) if r is not None else None


def _usual_fee(con, day):
    """slip_log.usual_fee, read here (no Flask in this process): the consultation amount billed most often in 60 days."""
    since = (dt.date.fromisoformat(day) - dt.timedelta(days=60)).isoformat()
    try:
        r = con.execute("SELECT amount_p, COUNT(*) n FROM clinic_day_line WHERE section='consult' AND business_date BETWEEN ? AND ? "
                        "AND amount_p>0 GROUP BY amount_p ORDER BY n DESC LIMIT 1", (since, day)).fetchone()
    except sqlite3.Error:
        return 0
    return int(r[0]) if r else 0


def _name_of(con, cid):
    try:
        r = con.execute("SELECT name FROM patient_ref WHERE clinic_id=? AND (merged_into IS NULL OR merged_into='') ORDER BY id LIMIT 1",
                        (cid,)).fetchone()
        return (r[0] or "") if r else ""
    except sqlite3.Error:
        return ""


def missing_slips(con, day, carried):
    """The day's slips the export does not carry -- not_in_docterz.rows' rules, read against `carried` (read_export's answer),
    leaving out every slip already answered on nid_mark. [{slip_id, series, slip_no, cid, kind, what, amount_p, name}]"""
    if not _has(con, "slip"):
        return []
    slips = [dict(r) for r in con.execute("SELECT * FROM slip WHERE state='ok' AND day=? ORDER BY series, slip_no", (day,))]
    radd, marks, rejected, its, dx = set(), set(), set(), {}, set()
    if _has(con, "slip_adjust"):
        radd = {r[0] for r in con.execute("SELECT slip_id FROM slip_adjust WHERE kind='cancel' AND state IN ('pending','approved')")}
    if _has(con, "nid_mark"):
        marks = {(r[0], r[1]) for r in con.execute("SELECT slip_id, kind FROM nid_mark WHERE state='live' AND day=?", (day,))}
    ids = [s["id"] for s in slips if s["series"] != "opd"]
    if ids and _has(con, "slip_item"):
        for it in con.execute("SELECT * FROM slip_item WHERE slip_id IN (%s) ORDER BY slip_id, sort" % ",".join("?" * len(ids)), ids):
            its.setdefault(it["slip_id"], []).append(dict(it))
        iids = [it["id"] for v in its.values() for it in v]
        if iids and _has(con, "slip_adjust"):
            rejected = {r[0] for r in con.execute("SELECT item_id FROM slip_adjust WHERE state='rejected' AND item_id IN (%s)"
                                                  % ",".join("?" * len(iids)), iids)}
    if _has(con, "dx_visit"):
        dx = {str(r[0] or "").strip() for r in con.execute("SELECT clinic_id FROM dx_visit WHERE substr(visit_date,1,10)=?", (day,))}
    fee = None
    out = []
    for s in slips:
        sid = s["id"]
        c = str(s.get("clinic_id") or "").strip()
        if sid in radd or s.get("no_id_name") or not c or not re.fullmatch(r"\d{1,12}", c):
            continue
        have = carried.get(c, set())
        name = (s.get("name_seen") or "").strip()
        if s["series"] == "opd":
            if have or c in dx or (sid, "opd") in marks:
                continue
            if fee is None:
                fee = _usual_fee(con, day)
            out.append(dict(slip_id=sid, series="opd", slip_no=s["slip_no"], cid=c, kind="opd", what=KIND_EN["opd"],
                            amount_p=fee, name=name))
            continue
        for kind in ("xray", "proc"):
            mine = [it for it in its.get(sid, []) if it["kind"] == kind]
            if not mine or kind in have or (sid, kind) in marks:
                continue
            net = sum(max(0, int(it["price_p"] or 0) - (0 if it["id"] in rejected else int(it.get("discount_p") or 0))) for it in mine)
            if net <= 0:
                continue
            what = "%s: %s" % (KIND_EN[kind], ", ".join(("%s %s" % (it["name"] or "", it.get("side") or "")).strip() for it in mine)[:120])
            out.append(dict(slip_id=sid, series=s["series"], slip_no=s["slip_no"], cid=c, kind=kind, what=what, amount_p=net, name=name))
    for r in out:
        if not r["name"]:
            r["name"] = _name_of(con, r["cid"])
    return out


def check(con, day, export=None):
    """The day's answer, worked out now: None when no consultation report of the day is here; else {day, export_id,
    export_at (IST), taken_at, road, err, rows}."""
    e = export or current_export(con, day)
    if e is None:
        return None
    t = utc_to_ist(e.get("drive_mtime"))
    out = dict(day=day, export_id=e["id"], export_at=t.strftime("%H:%M") if t else "", taken_at=str(e.get("taken_at") or "")[11:16],
               road="direct" if str(e.get("drive_id") or "").startswith("reception:") else "drive", err="", rows=[])
    raw = None
    try:
        with open(e.get("stored") or "", "rb") as fh:
            raw = fh.read()
    except OSError:
        raw = None
    carried = read_export(raw, day) if raw is not None else None
    if carried is None:
        out["err"] = "the stored export could not be read"
        return out
    out["rows"] = missing_slips(con, day, carried)
    return out


def evening_export(con, day, at=None):
    """The current consultation report of `day`, when `day` is today and it was taken in the evening window -- else None."""
    at = at or now_ist()
    if day != at.date().isoformat():
        return None
    e = current_export(con, day)
    if e is None:
        return None
    try:
        taken = dt.datetime.strptime(str(e.get("taken_at") or "")[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    if taken.date().isoformat() != day or taken.time() < evening_from(day):
        return None
    return e


# ---------------------------------------------------------------------------------------------------------------- the push
def _names(rows, n=5):
    seen = []
    for r in rows:
        w = r["name"] or ("ID " + r["cid"])
        if w not in seen:
            seen.append(w)
    more = len(seen) - n
    return " · ".join(seen[:n]) + ((" +%d" % more) if more > 0 else "")


def _live(con):
    try:
        path = con.execute("PRAGMA database_list").fetchone()[2]
        return bool(path) and os.path.realpath(path) == os.path.realpath(LIVE_DB)
    except Exception:                                     # noqa: BLE001
        return False


def _send(who, title, body, tag):
    """(sent, failed, ntfy) through callback_clock.send -- or a word on why nothing went."""
    cc = _cc()
    if cc is None:
        return None, "the call-back clock is not here"
    try:
        pusher = cc.get_pusher(PUSHER)
        url = (lambda w: DESK_URL if w in DESK_LOGINS else HOME_URL)
        return cc.send(pusher, who, title, body, url, tag), ""
    except Exception as ex:                               # noqa: BLE001
        return None, "send: %s" % str(ex)[:100]


def _day_lock(con):
    """One check at a time on this database (cold review, S960): two exports close together are judged in turn, so the second
    sees the first's outcome, and a check whose export was replaced meanwhile never pushes."""
    try:
        path = con.execute("PRAGMA database_list").fetchone()[2]
    except Exception:                                     # noqa: BLE001
        path = ""
    fh = open(os.path.join(os.path.dirname(path) if path else HERE, ".evening_check.lock"), "a")
    fcntl.flock(fh, fcntl.LOCK_EX)
    return fh


def on_export(con, export_id, push=True, at=None):
    """Judge one taken export, once (one at a time). Returns the outcome word."""
    lk = _day_lock(con)
    try:
        return _on_export(con, export_id, push, at)
    finally:
        try:
            fcntl.flock(lk, fcntl.LOCK_UN)
            lk.close()
        except Exception:                                 # noqa: BLE001
            pass


def _on_export(con, export_id, push=True, at=None):
    at = at or now_ist()
    if not _has(con, "docterz_export"):
        return "skip: no docterz_export"
    e = con.execute("SELECT * FROM docterz_export WHERE id=?", (int(export_id),)).fetchone()
    if e is None:
        return "skip: no such export"
    e = dict(e)
    if e["kind"] != "consultation" or e["status"] != "current":
        return "skip: not the current consultation report"
    day = e["business_date"]
    ev = evening_export(con, day, at)
    if ev is None or ev["id"] != e["id"]:
        return "skip: not today's evening export"
    ensure(con)
    cur = con.execute("INSERT OR IGNORE INTO evening_check_push (export_id, day, at) VALUES (?,?,?)", (e["id"], day, _stamp(at)))
    con.commit()
    if cur.rowcount == 0:
        return "skip: already judged"
    if not is_on():
        con.execute("UPDATE evening_check_push SET outcome='off' WHERE export_id=?", (e["id"],))
        con.commit()
        return "off"
    prev = con.execute("SELECT outcome FROM evening_check_push WHERE day=? AND export_id<>? AND outcome IN ('missing','clean','cleared','quiet') "
                       "ORDER BY export_id DESC LIMIT 1", (day, e["id"])).fetchone()
    prev = prev[0] if prev else None
    chk = check(con, day, e)
    if chk is None or chk["err"]:
        con.execute("UPDATE evening_check_push SET outcome='unread', sent=? WHERE export_id=?", ((chk or {}).get("err", "no export"), e["id"]))
        con.commit()
        return "unread"
    rows = chk["rows"]
    t_at = chk["export_at"] or at.strftime("%H:%M")
    title = body = ""
    if rows:
        outcome = "missing"
        title = "%d parchi Docterz mein nahi" % len(rows)
        body = "%s — abhi Docterz mein daalein, phir dobara export" % _names(rows)
    elif prev is None:
        outcome = "clean"
        title = "✓ %s: sab parchi Docterz mein" % dm(day)
        body = "Kuch nahi karna — PC band kar sakte hain" if at.time() >= closing(day) else "Kuch nahi karna"
    elif prev == "missing":
        outcome = "cleared"
        title = "✓ Sab parchi Docterz mein"
        body = ("Dobara export %s — kaam poora, PC band kar sakte hain" if at.time() >= closing(day) else "Dobara export %s — kaam poora") % t_at
    else:
        outcome = "quiet"
    sent = ""
    now_cur = current_export(con, day)
    if outcome != "quiet" and (now_cur is None or now_cur["id"] != e["id"]):
        outcome, sent = "superseded", "not pushed (a newer export came during the check)"
    if outcome not in ("quiet", "superseded"):
        who = [w.strip() for w in cfg("EVCHK_TO", TO_DEFAULT).split(",") if w.strip()]
        if not push:
            sent = "not pushed (asked not to)"
        elif not _live(con):
            sent = "not pushed (not the live database)"
        elif not who:
            sent = "not pushed (no login in EVCHK_TO)"
        else:
            res, why = _send(who, title, body, "evening-" + day)
            sent = ("sent %d, failed %d, ntfy %d" % tuple(res)) if res else ("not pushed (%s)" % why)
    con.execute("UPDATE evening_check_push SET outcome=?, missing=?, slips=?, sent=? WHERE export_id=?",
                (outcome, len(rows), ",".join("%d:%s" % (r["slip_id"], r["kind"]) for r in rows), sent, e["id"]))
    con.commit()
    return "%s %d (%s)" % (outcome, len(rows), sent or "nothing to send")


def sweep(con, push=True, at=None):
    """The every-minute safety net at closing: today's current evening export judged if no check judged it (the spawn failed, or
    the check died). Under the same lock as every check, so a 'claimed' row seen here belongs to a check that is gone (a live one
    holds the lock from its claim to its answer). '' when there was nothing to do."""
    at = at or now_ist()
    day = at.date().isoformat()
    if evening_export(con, day, at) is None:
        return ""
    lk = _day_lock(con)
    try:
        e = evening_export(con, day, at)
        if e is None:
            return ""
        if _has(con, "evening_check_push"):
            r = con.execute("SELECT outcome FROM evening_check_push WHERE export_id=?", (e["id"],)).fetchone()
            if r is not None:
                if r[0] != "claimed":
                    return ""
                con.execute("DELETE FROM evening_check_push WHERE export_id=? AND outcome='claimed'", (e["id"],))
                con.commit()
        return "swept: " + _on_export(con, e["id"], push, at)
    finally:
        try:
            fcntl.flock(lk, fcntl.LOCK_UN)
            lk.close()
        except Exception:                                 # noqa: BLE001
            pass


# ---------------------------------------------------------------------------------------------------------------- the desk
def _rs(p):
    return "₹{:,}".format(int(p or 0) // 100)


def panel_html(con, eng=False, at=None):
    """The slip desk's evening box -- '' when there is nothing to show (no evening export of today yet)."""
    at = at or now_ist()
    day = at.date().isoformat()
    e = evening_export(con, day, at)
    if e is None:
        return ""
    chk = check(con, day, e)
    if chk is None:
        return ""
    E = _h.escape
    road = ("direct" if chk["road"] == "direct" else "via Drive") if eng else ("seedha server par" if chk["road"] == "direct" else "Drive se")
    line = ("Docterz export %s · reached the server %s (%s) · checked %s" if eng else
            "Docterz export %s · server par %s (%s) · check %s") % (chk["export_at"] or "?", chk["taken_at"] or "?", road, at.strftime("%H:%M"))
    if chk["err"]:
        body = '<p style="color:#9c2a20;font-weight:600">%s</p>' % (
            "The export could not be read -- export the consultation report again." if eng else
            "Export padha nahi gaya — consultation report dobara export karein.")
        head, color = ("Evening check" if eng else "Shaam ka check"), "#9c2a20"
    elif not chk["rows"]:
        head, color = (("✓ Every slip of today is in Docterz" if eng else "✓ Aaj ki sab parchi Docterz mein")), "#1f6b3a"
        body = '<p style="margin:4px 0">%s</p>' % ("Nothing to do — the PC can be switched off." if eng else
                                                  "Kuch nahi karna — PC band kar sakte hain.")
    else:
        rows = chk["rows"]
        tot = sum(r["amount_p"] for r in rows)
        head, color = (("Slips of today not in Docterz: %d · %s" if eng else "Aaj ki parchi jo Docterz mein nahi: %d · %s")
                       % (len(rows), _rs(tot))), "#9c2a20"
        trs = []
        for r in rows:
            trs.append(
                '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 0;border-top:1px solid #e1e7eb">'
                '<div style="flex:1 1 220px"><b>%s</b> &middot; ID %s &middot; %s %d</div><div style="flex:1 1 200px">%s</div>'
                '<div style="min-width:70px;font-weight:700">%s</div>'
                '<button type="button" class="s960f" data-sid="%d" data-kind="%s" style="min-height:44px;padding:0 14px;border:1px solid #14456e;'
                'border-radius:10px;background:#fff;color:#14456e;font-size:15px">%s</button></div>'
                % (E(r["name"] or "?"), E(r["cid"]), "slip" if eng else "parchi", int(r["slip_no"] or 0), E(r["what"]), _rs(r["amount_p"]),
                   int(r["slip_id"]), E(r["kind"]), "Money not taken" if eng else "Paise nahi liye"))
        steps = ("1 · Enter them in Docterz on today's date. 2 · Reception exports today's consultation report again. 3 · This list clears "
                 "by itself about a minute later, and everyone is told." if eng else
                 "1 · Docterz mein aaj ki tareekh par daalein. 2 · Reception: aaj ka consultation report dobara export. "
                 "3 · Lagbhag 1 minute mein list apne aap saaf, aur sabko notification.")
        body = "".join(trs) + '<p style="margin:8px 0 0;font-size:14px;color:#3b4a55">%s</p>' % steps
    return ('<section id="s960" class="box" style="margin:0 0 10px;border:2px solid %s;border-radius:10px;padding:10px 12px">'
            '<div style="font-size:18px;font-weight:700;color:%s">%s</div><div style="font-size:13px;color:#3b4a55;margin-top:2px">%s</div>'
            '%s<div id="s960m" style="color:#9c2a20;font-weight:600"></div></section>'
            % (color, color, E(head), E(line), body))


PANEL_JS = ('<script>(function(){var A=%s,T=%s;function wire(){[].forEach.call(document.querySelectorAll(".s960f"),function(b){b.onclick=function(){'
            'b.disabled=true;fetch(A+"/free",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify({slip_id:+b.getAttribute("data-sid"),kind:b.getAttribute("data-kind")})}).then(function(r){return r.json();})'
            '.then(function(r){if(r.ok){load();}else{b.disabled=false;var m=document.getElementById("s960m");if(m)m.textContent=r.err||"";}})'
            '.catch(function(){b.disabled=false;});};});}'
            'function load(){fetch(A,{credentials:"same-origin"}).then(function(r){return r.json();}).then(function(r){if(!r||!r.ok)return;'
            'if(r.today)T=r.today;var w=document.getElementById("s960w");if(w){w.innerHTML=r.html||"";wire();vis();}}).catch(function(){});}'
            'function vis(){var s=document.getElementById("day"),w=document.getElementById("s960w");if(!w)return;'
            'w.style.display=(s&&s.value&&T&&s.value!==T)?"none":"";}'
            'var sd=document.getElementById("day");if(sd)sd.addEventListener("change",vis);'
            'wire();vis();document.addEventListener("DOMContentLoaded",vis);setInterval(function(){load();vis();},30000);})();</script>')


def desk_box(con, eng=False, at=None):
    """What parchi_desk.page() puts at the top of the desk: the panel in its own wrapper (always there, so it can appear later);
    the page's own day picker decides whether it shows (today only) -- the box is always today's."""
    at = at or now_ist()
    return '<div id="s960w" data-today="%s">%s</div>%s' % (at.date().isoformat(), panel_html(con, eng, at),
                                                            PANEL_JS % (json.dumps(API), json.dumps(at.date().isoformat())))


class FreeError(Exception):
    pass


def mark_free(con, who, slip_id, kind, at=None):
    """'Paise nahi liye' -- the answer 'free' on nid_mark, for a slip on TODAY's evening list only. Returns the new mark's id."""
    at = at or now_ist()
    day = at.date().isoformat()
    e = evening_export(con, day, at)
    chk = check(con, day, e) if e is not None else None
    r = next((x for x in (chk or {}).get("rows", []) if x["slip_id"] == int(slip_id) and x["kind"] == kind), None)
    if r is None:
        raise FreeError("Yeh parchi ab list mein nahi — page taaza hai.")
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import not_in_docterz as nid                          # noqa: PLC0415 -- its table, its schema
    nid.ensure(con)
    try:
        cur = con.execute("INSERT INTO nid_mark (slip_id, kind, act, amount_p, day, who, at) VALUES (?,?,?,?,?,?,?)",
                          (int(slip_id), kind, "free", int(r["amount_p"] or 0), day, who, _stamp(at)))
    except sqlite3.IntegrityError:
        con.rollback()
        raise FreeError("Pehle hi jawab diya ja chuka hai.")
    if _U["audit"]:
        try:
            _U["audit"](con, "nid_mark", cur.lastrowid, "nid_mark", before=None,
                        after=json.dumps({"slip": int(slip_id), "kind": kind, "act": "free", "by": "evening desk"}), who=who)
        except Exception:                                 # noqa: BLE001 -- the audit never blocks the work
            pass
    con.commit()
    return cur.lastrowid


def init(app, db_getter, require_fn, audit_fn=None, unit="slips"):
    """Mount the desk's two doors (called by parchi_desk.init); touches no database (F-303). Flask is imported only here."""
    from flask import jsonify, request                    # noqa: PLC0415

    _U.update(db=db_getter, require=require_fn, audit=audit_fn, unit=unit)

    def _gate():
        return require_fn("maker", "checker", unit=_U["unit"])

    def _eng(u):
        rs = set((u or {}).get("roles") or [])
        return "checker" in rs and "maker" not in rs

    def api_evening():
        u, err = _gate()
        if err:
            return jsonify(ok=False, err="not allowed"), 403
        try:
            return jsonify(ok=True, html=panel_html(db_getter(), _eng(u)), today=now_ist().date().isoformat())
        except Exception:                                 # noqa: BLE001
            return jsonify(ok=False, err="could not be read"), 200

    def api_free():
        u, err = _gate()
        if err:
            return jsonify(ok=False, err="not allowed"), 403
        j = request.get_json(silent=True) or {}
        kind = str(j.get("kind") or "")
        try:
            sid = int(j.get("slip_id") or 0)
        except (TypeError, ValueError):
            sid = 0
        if kind not in KIND_EN or sid <= 0:
            return jsonify(ok=False, err="Samajh nahi aaya."), 200
        try:
            mark_free(db_getter(), str((u or {}).get("user", "") or ""), sid, kind)
        except FreeError as ex:
            return jsonify(ok=False, err=str(ex)), 200
        return jsonify(ok=True)

    app.add_url_rule(API, "s960_evening", api_evening, methods=["GET"])
    app.add_url_rule(API + "/free", "s960_evening_free", api_free, methods=["POST"])
    return True


# ---------------------------------------------------------------------------------------------------------------- command line
def main(argv=None):
    import argparse                                       # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--export", type=int)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--day")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args(argv)
    con = sqlite3.connect(a.db, timeout=30)
    con.row_factory = sqlite3.Row
    t = now_ist()
    if a.sweep:
        w = sweep(con, push=not a.no_push, at=t)
        if w:                                             # silent when there was nothing to do (it runs every minute)
            print("%s evening_check %s %s" % (_stamp(t), VERSION, w))
        return 0
    if a.export:
        print("%s evening_check %s export %d: %s" % (_stamp(t), VERSION, a.export, on_export(con, a.export, push=not a.no_push, at=t)))
        return 0
    day = a.day or t.date().isoformat()
    chk = check(con, day)
    pushes = con.execute("SELECT COUNT(*) FROM evening_check_push WHERE day=?", (day,)).fetchone()[0] if _has(con, "evening_check_push") else 0
    if chk is None:
        print("EVENING %s %s: no consultation report of the day; pushes %d" % (VERSION, day, pushes))
    else:
        print("EVENING %s %s: export %s (%s) taken %s; missing %d%s; pushes %d" % (VERSION, day, chk["export_at"], chk["road"], chk["taken_at"],
                                                                               len(chk["rows"]), (" -- " + chk["err"]) if chk["err"] else "", pushes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
