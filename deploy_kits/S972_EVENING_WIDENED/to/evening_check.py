#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evening_check.py -- kit S960_EVENING_CHECK (session S527, 26-Nov-2026; D1080, the Morning Match kit A). PARENT. NEW.
S972_EVENING_WIDENED (session S539, 27-Nov-2026; D1099, D1100 -- K1 of S537_MORNING_CHECK_FINAL_BUILD_PLAN): the evening also
compares the MONEY of each patient's X-ray / procedure slip lines with the same export (X-ray = Laboratory + Radiology, net =
amount - discount, as revenue.py), for patients who have a slip today, and names four Docterz shapes on the same push and the
same desk box -- the owner's words 14:31 27-Nov: "only same-day Docterz edits should be there":
    chhoot   Docterz billed the full rate, the slip carries a chhoot      -> "Docterz mein chhoot lagaiye"
    kam      the slip carries more than Docterz (not a repeated line)    -> "Docterz bill mein jodiye" (or, when Docterz holds a
             chhoot the slip does not, "chhoot sahi hai to parchi par bhi, nahi to Docterz mein hataiye")
    tdoc     Docterz billed one slip line twice                            -> "dono taraf hua tha?"  [Haan, parchi theek karo]
             (writes the slip's second line -- offered only for a line with no chhoot) / Nahi: Docterz se ek hataiye
    tslip    the slip carries a line twice, Docterz once (day_check's pdup) -> "dono taraf hua tha?"  [Nahi, parchi se ek hataiye]
             (removes exactly the repeat -- not when a chhoot waits on it) / Haan: Docterz mein doosra jodiye
    more     Docterz has more than the slip (or a kind the slip lacks)     -> "kaunsa sahi?" (Docterz, or Shavez's parchi)
A line clears by itself when the next export (or the slip) agrees -- every line is worked out afresh from the stored export and
the slips as they stand. Payment mode is NOT compared (D1099). A patient with a radd today, a pair already answered on his
"Slips not in Docterz" list (nid_mark), and a kind the export lacks altogether (the S960 missing line) are left out.
EVCHK_SHAPES=0 turns the four shapes off (the S960 check as it was). The table gains one additive column, shapes (keys, no names).

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
VERSION = "S972 1"
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
    try:                                                  # S972: one additive column, the shape keys of the export's lines
        cols = [r[1] for r in con.execute("PRAGMA table_info(evening_check_push)")]
        if "shapes" not in cols:
            con.execute("ALTER TABLE evening_check_push ADD COLUMN shapes TEXT NOT NULL DEFAULT ''")
    except sqlite3.Error:
        pass
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


def shapes_on():
    """S972: the four money shapes (EVCHK_SHAPES=0 -> the S960 check as it was)."""
    return cfg("EVCHK_SHAPES", "1").lower() not in ("0", "off", "no", "false")


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


def read_amounts(raw, day):
    """S972: {clinic_id: {'xray'|'proc': [net_p, gross_p, disc_p]}} -- the money of `day`'s rows, read as revenue.py reads it
    (X-ray = Laboratory + Radiology; net = amount - discount, never below 0 per row), in paise. The same rows read_export
    counts (a UID-shaped row of the day). None if not readable."""
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

    cols = (("xray", (("Laboratory Amount", "Laboratory Discount"), ("Radiology Amount", "Radiology Discount"))),
            ("proc", (("Procedure Amount", "Procedure Discount"),)))
    out = {}
    for r in rows[1:]:
        d = _parse_date(get(r, "Consultation Date"))
        if d is None or d.isoformat() != day:
            continue
        c = _cid(get(r, "Clinic Specific Id"))
        if not c or not UID_OK.fullmatch(str(get(r, "Patient UID") or "").strip()):
            continue
        for kind, pairs in cols:
            g = int(round(sum(_num(get(r, a)) for a, _b in pairs) * 100))
            dd = int(round(sum(_num(get(r, b)) for _a, b in pairs) * 100))
            if g <= 0 and dd <= 0:
                continue
            v = out.setdefault(c, {}).setdefault(kind, [0, 0, 0])
            v[0] += max(0, g - dd)
            v[1] += g
            v[2] += dd
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


SHAPES = ("chhoot", "kam", "tdoc", "tslip", "more", "head")


def _word(it):
    return ("%s %s" % (it.get("name") or "", it.get("side") or "")).strip()


def _twice(its, extra):
    """day_check._duplicate's rule: (slip, [items]) when lines written twice on the slip come to exactly `extra`."""
    seen, rep = set(), []
    for s, it in its:
        k = ((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())
        if k in seen:
            rep.append((s, it))
        seen.add(k)
    if not rep or extra <= 0:
        return None
    for s, it in rep:
        if it["expect_p"] == extra:
            return s, [it]
    if sum(it["expect_p"] for _s, it in rep) == extra:
        return rep[0][0], [it for _s, it in rep]
    return None


def shape_lines(con, day, carried, amounts):
    """S972: the day's money shapes, patient by patient and kind by kind, for patients with a slip of the day:
    [{key, shape, cid, name, kind, p, d, gross, disc, extra, slip_id, slip_no, items (ids), what, can}] -- `can` says whether
    the one slip-side write is offered (tdoc: the line has no chhoot and no adjustment; tslip: no adjustment on the repeat).
    The slip's money is day_check's: rate - chhoot, a REJECTED chhoot puts the full rate back (the newest entry not replaced)."""
    if not _has(con, "slip"):
        return []
    slips = [dict(r) for r in con.execute("SELECT * FROM slip WHERE state='ok' AND day=? ORDER BY series, slip_no", (day,))]
    slips = [s for s in slips if not s.get("no_id_name") and re.fullmatch(r"\d{1,12}", str(s.get("clinic_id") or "").strip())]
    if not slips:
        return []
    radd, marks, adj, its = set(), set(), {}, {}
    if _has(con, "slip_adjust"):
        radd = {r[0] for r in con.execute("SELECT slip_id FROM slip_adjust WHERE kind='cancel' AND state IN ('pending','approved')")}
    if _has(con, "nid_mark"):
        marks = {(r[0], r[1]) for r in con.execute("SELECT slip_id, kind FROM nid_mark WHERE state='live' AND day=?", (day,))}
    ids = [s["id"] for s in slips if s["series"] == "xp"]
    if ids and _has(con, "slip_item"):
        for it in con.execute("SELECT * FROM slip_item WHERE slip_id IN (%s) ORDER BY slip_id, sort, id" % ",".join("?" * len(ids)), ids):
            its.setdefault(it["slip_id"], []).append(dict(it))
        iids = [it["id"] for v in its.values() for it in v]
        if iids and _has(con, "slip_adjust"):
            for a in con.execute("SELECT * FROM slip_adjust WHERE item_id IN (%s) AND state<>'replaced' ORDER BY id"
                                 % ",".join("?" * len(iids)), iids):
                adj[a["item_id"]] = dict(a)
    by = {}
    for s in slips:
        c = str(s["clinic_id"]).strip()
        b = by.setdefault(c, dict(slips=[], radd=False, name=""))
        b["slips"].append(s)
        b["radd"] = b["radd"] or s["id"] in radd
        b["name"] = b["name"] or (s.get("name_seen") or "").strip()
    out = []
    for c in sorted(by, key=lambda x: (len(x), x)):
        b = by[c]
        if b["radd"]:                                     # a radd today: the morning matches its refund (S962)
            continue
        have = carried.get(c, set())
        money = amounts.get(c, {})
        lines_of = {}
        for kind in ("xray", "proc"):
            mine = []
            for s in b["slips"]:
                for it in its.get(s["id"], []):
                    if it["kind"] != kind:
                        continue
                    a = adj.get(it["id"])
                    disc = 0 if (a and a.get("state") == "rejected") else int(it.get("discount_p") or 0)
                    it = dict(it, expect_p=max(0, int(it.get("price_p") or 0) - disc), adjusted=a is not None)
                    mine.append((s, it))
            lines_of[kind] = mine
        if not any((s["id"], k) in marks for s in b["slips"] for k in ("xray", "proc")):
            pk = {k: sum(it["expect_p"] for _s, it in lines_of[k]) for k in ("xray", "proc")}
            dk = {k: (money.get(k, [0, 0, 0])[0] if k in have else 0) for k in ("xray", "proc")}
            reps = [((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower()) for k in ("xray", "proc") for _s, it in lines_of[k]]
            if sum(pk.values()) == sum(dk.values()) > 0 and pk != dk and len(reps) == len(set(reps)):   # re-look: not with a repeat
                # second look MUST: the money agrees, the head does not (an X-ray billed as a procedure, or the other way) --
                # ONE line, no tap; the per-kind lines would ask for a wrong edit or a phantom slip line
                s0 = (lines_of["xray"] or lines_of["proc"])[0][0] if (lines_of["xray"] or lines_of["proc"]) else b["slips"][0]
                out.append(dict(cid=c, name=b["name"], kind="both", shape="head", p=sum(pk.values()), d=sum(dk.values()), gross=0, disc=0,
                                extra=0, px=pk["xray"], pp=pk["proc"], dx=dk["xray"], dp=dk["proc"], slip_id=s0["id"], slip_no=s0["slip_no"],
                                series=s0["series"], items=[], what="", can=False, key="ev:head:%s:both" % c))
                continue
        for kind in ("xray", "proc"):
            if any((s["id"], kind) in marks for s in b["slips"]):
                continue                                  # already answered on his list
            mine = lines_of[kind]
            in_doc = kind in have
            if not in_doc:
                continue                                  # the S960 missing line (or nothing at all on either side)
            d, gross, ddisc = money.get(kind, [0, 0, 0])
            p = sum(it["expect_p"] for _s, it in mine)
            pg = sum(int(it.get("price_p") or 0) for _s, it in mine)
            if p == d or (not mine and d <= 0):
                continue
            s0 = mine[0][0] if mine else b["slips"][0]
            ln = dict(cid=c, name=b["name"], kind=kind, p=p, d=d, gross=gross, disc=ddisc, slip_id=s0["id"],
                      slip_no=s0["slip_no"], series=s0["series"], items=[], what=", ".join(_word(it) for _s, it in mine)[:120], can=False)
            if p > d:
                tw = _twice(mine, p - d)
                if tw is not None:
                    ln.update(shape="tslip", extra=p - d, slip_id=tw[0]["id"], slip_no=tw[0]["slip_no"],
                              items=[it["id"] for it in tw[1]], what=" + ".join(_word(it) for it in tw[1])[:120],
                              can=not any(it["adjusted"] for it in tw[1]) and all(it["slip_id"] == tw[0]["id"] for it in tw[1]))
                else:
                    ln.update(shape="kam", extra=p - d)
            elif mine and pg - p > 0 and d == pg:
                ln.update(shape="chhoot", extra=pg - p)
            else:
                once = []
                if mine:
                    cnt = {}
                    for _s, it in mine:
                        k = ((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())
                        cnt[k] = cnt.get(k, 0) + 1
                    once = [(s, it) for s, it in mine if it["expect_p"] == d - p and it["expect_p"] > 0
                            and cnt[((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())] == 1]
                if len(once) == 1:                      # cold review M1: two lines at the same price -> which one is unknown
                    s1, it1 = once[0]
                    ln.update(shape="tdoc", extra=d - p, slip_id=s1["id"], slip_no=s1["slip_no"], items=[it1["id"]], what=_word(it1)[:120],
                              can=(int(it1.get("discount_p") or 0) == 0 and not it1["adjusted"]
                                   and (it1.get("side") or "").strip().upper() in ("R", "L")))   # second look 3: the copy is the other side
                else:
                    ln.update(shape="more", extra=d - p)
            ln["key"] = "ev:%s:%s:%s" % (ln["shape"], c, kind)
            out.append(ln)
    for r in out:
        if not r["name"]:
            r["name"] = _name_of(con, r["cid"])
    return out


def _sk(kind, eng=False):
    return {"xray": "X-ray", "proc": "Procedure", "both": "X-ray/Procedure"}.get(kind, kind)


def shape_text(ln, eng=False):
    """One line's words: (the sentence, the instruction beside its button). No number but the money."""
    nm, k = ln["name"] or ("ID " + ln["cid"]), _sk(ln["kind"], eng)
    w = (" (%s)" % ln["what"]) if ln["what"] else ""
    P, Dz, X = _rs(ln["p"]), _rs(ln["d"]), _rs(ln["extra"])
    sh = ln["shape"]
    if sh == "head":
        return ((("%s: slip X-ray %s + Procedure %s, Docterz X-ray %s + Procedure %s — the total agrees, the head does not: "
                  "move it to the right head in Docterz" if eng else
                  "%s: parchi X-ray %s + Procedure %s, Docterz X-ray %s + Procedure %s — jod barabar, head galat: "
                  "Docterz mein sahi head mein daaliye") % (nm, _rs(ln["px"]), _rs(ln["pp"]), _rs(ln["dx"]), _rs(ln["dp"]))), "")
    if sh == "chhoot":
        return ((("%s: %s%s slip %s (discount %s), Docterz %s — apply the discount %s in Docterz" if eng else
                  "%s: %s%s parchi %s (chhoot %s), Docterz %s — Docterz mein chhoot %s lagaiye") % (nm, k, w, P, X, Dz, X)), "")
    if sh == "kam":
        if ln["disc"] > 0 and ln["gross"] >= ln["p"]:
            return ((("%s: %s%s slip %s, Docterz has a discount %s (%s) — if the discount is right, have it written on the slip too; "
                      "if not, remove it in Docterz" if eng else
                      "%s: %s%s parchi %s, Docterz mein chhoot %s (%s) — chhoot sahi hai to parchi par bhi likhwayein, "
                      "nahi to Docterz mein hataiye") % (nm, k, w, P, _rs(ln["disc"]), Dz)), "")
        return ((("%s: %s%s slip %s, Docterz %s — add %s to the Docterz bill" if eng else
                  "%s: %s%s parchi %s, Docterz %s — Docterz bill mein %s jodiye") % (nm, k, w, P, Dz, X)), "")
    if sh == "tdoc":
        if ln["can"]:
            return ((("%s: %s %s — twice in Docterz (%s), once on the slip (%s). Was the other side (R and L) done too?" if eng else
                      "%s: %s %s — Docterz mein do baar (%s), parchi par ek (%s). Doosri taraf (R aur L dono) bhi hua tha?") % (nm, k, ln["what"], Dz, P)),
                    ("No: remove one in Docterz, then export again." if eng else "Nahi: Docterz se ek hataiye, phir dobara export."))
        return ((("%s: %s %s — Docterz has %s more (%s), the slip one (%s). Done twice, or another view?" if eng else
                  "%s: %s %s — Docterz mein %s zyada (%s), parchi par ek (%s). Do baar / doosra view hua tha?") % (nm, k, ln["what"], X, Dz, P)),
                ("Yes: Shavez writes it on the slip. No: remove it in Docterz, then export again." if eng else
                 "Haan: Shavez parchi par likhein. Nahi: Docterz se hataiye, phir dobara export."))
    if sh == "tslip":
        return ((("%s: %s %s — twice on the slip (%s), once in Docterz (%s). Were both sides done?" if eng else
                  "%s: %s %s — parchi par do baar (%s), Docterz mein ek (%s). Dono taraf hua tha?") % (nm, k, ln["what"], P, Dz)),
                ("Yes: add the second in Docterz, then export again." if eng else "Haan: Docterz mein doosra jodiye, phir dobara export."))
    if ln["p"] <= 0:
        return ((("%s: Docterz %s %s, no %s on the slip — which is right?" if eng else
                  "%s: Docterz %s %s, parchi par %s nahi — kaunsa sahi?") % (nm, k, Dz, k)),
                ("Docterz wrong: correct it and export again. Slip wrong: Shavez writes the slip." if eng else
                 "Docterz galat: theek karke dobara export. Parchi galat: Shavez parchi likhein."))
    return ((("%s: %s%s Docterz %s, slip %s — which is right?" if eng else "%s: %s%s Docterz %s, parchi %s — kaunsa sahi?") % (nm, k, w, Dz, P)),
            ("Docterz wrong: correct it and export again. Slip wrong: Shavez corrects the slip." if eng else
             "Docterz galat: theek karke dobara export. Parchi galat: Shavez parchi theek karein."))


def _short(ln):
    """The push's few words for one line (Hindi; staff)."""
    k = _sk(ln["kind"])
    return {"chhoot": "%s chhoot %s lagaiye" % (k, _rs(ln["extra"])), "kam": "%s %s jodiye" % (k, _rs(ln["extra"])),
            "tdoc": "%s do baar — dono taraf?" % k, "tslip": "%s parchi par do baar — dono taraf?" % k,
            "more": "%s kaunsa sahi?" % k, "head": "head galat (jod barabar)"}.get(ln["shape"], k)


def check(con, day, export=None):
    """The day's answer, worked out now: None when no consultation report of the day is here; else {day, export_id,
    export_at (IST), taken_at, road, err, rows}."""
    e = export or current_export(con, day)
    if e is None:
        return None
    t = utc_to_ist(e.get("drive_mtime"))
    out = dict(day=day, export_id=e["id"], export_at=t.strftime("%H:%M") if t else "", taken_at=str(e.get("taken_at") or "")[11:16],
               road="direct" if str(e.get("drive_id") or "").startswith("reception:") else "drive", err="", rows=[], shapes=[])
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
    if shapes_on():                                       # S972: the four money shapes on the same export
        amounts = read_amounts(raw, day)
        out["shapes"] = shape_lines(con, day, carried, amounts or {}) if amounts is not None else []
        out["rows"], out["shapes"] = merge_lines(out["rows"], out["shapes"])
    return out


def merge_lines(rows, shapes):
    """One fault, one line (cold review 7, second look 1): a patient named 'head' leaves the missing list for X-ray / procedure;
    a 'more' with nothing on the slip for a patient on the missing list is not named twice; a patient still on the missing list
    gets no slip-side tap (its money is not settled yet)."""
    head = {x["cid"] for x in shapes if x["shape"] == "head"}
    rows = [r for r in rows if not (r["cid"] in head and r["kind"] in ("xray", "proc"))]
    miss = {r["cid"] for r in rows}
    shapes = [x for x in shapes if not (x["shape"] == "more" and x["p"] <= 0 and x["cid"] in miss)]
    for x in shapes:
        if x["cid"] in miss:
            x["can"] = False
    return rows, shapes


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
    shp = chk.get("shapes") or []                         # S972
    t_at = chk["export_at"] or at.strftime("%H:%M")
    title = body = ""
    if rows or shp:
        outcome = "missing"
        sl = " · ".join("%s: %s" % (x["name"] or ("ID " + x["cid"]), _short(x)) for x in shp[:4]) + ((" +%d" % (len(shp) - 4)) if len(shp) > 4 else "")
        if rows and not shp:
            title = "%d parchi Docterz mein nahi" % len(rows)
            body = "%s — abhi Docterz mein daalein, phir dobara export" % _names(rows)
        elif shp and not rows:
            title = "%d farq — Docterz aur parchi" % len(shp)
            body = "%s — desk par dekhein, theek karke dobara export" % sl
        else:
            title = "%d parchi Docterz mein nahi · %d farq" % (len(rows), len(shp))
            body = "%s — Docterz mein daalein · farq: %s — phir dobara export" % (_names(rows), sl)
    elif prev is None:
        outcome = "clean"
        title = ("✓ %s: Docterz aur parchi sab mile" if shapes_on() else "✓ %s: sab parchi Docterz mein") % dm(day)
        body = "Kuch nahi karna — PC band kar sakte hain" if at.time() >= closing(day) else "Kuch nahi karna"
    elif prev == "missing":
        outcome = "cleared"
        title = "✓ Docterz aur parchi sab mile" if shapes_on() else "✓ Sab parchi Docterz mein"
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
    con.execute("UPDATE evening_check_push SET outcome=?, missing=?, slips=?, sent=?, shapes=? WHERE export_id=?",
                (outcome, len(rows), ",".join("%d:%s" % (r["slip_id"], r["kind"]) for r in rows), sent,
                 ",".join("%s:%d:%s" % (x["shape"], x["slip_id"], x["kind"]) for x in shp), e["id"]))
    con.commit()
    return "%s %d shapes %d (%s)" % (outcome, len(rows), len(shp), sent or "nothing to send")


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
    elif not chk["rows"] and not chk.get("shapes"):
        head, color = (("✓ Every slip of today is in Docterz, the money agrees" if eng else "✓ Aaj ki sab parchi Docterz mein, paise mile")
                       if shapes_on() else ("✓ Every slip of today is in Docterz" if eng else "✓ Aaj ki sab parchi Docterz mein")), "#1f6b3a"
        body = '<p style="margin:4px 0">%s</p>' % ("Nothing to do — the PC can be switched off." if eng else
                                                  "Kuch nahi karna — PC band kar sakte hain.")
    elif not chk["rows"]:
        head, color = (("Docterz and the slips differ: %d" if eng else "Docterz aur parchi mein farq: %d") % len(chk["shapes"])), "#9c2a20"
        body = _shapes_html(chk["shapes"], eng)
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
        if chk.get("shapes"):                             # S972
            body += ('<div style="font-size:17px;font-weight:700;color:#9c2a20;margin-top:12px">%s</div>'
                     % E(("Docterz and the slips differ: %d" if eng else "Docterz aur parchi mein farq: %d") % len(chk["shapes"]))
                     + _shapes_html(chk["shapes"], eng))
    return ('<section id="s960" class="box" style="margin:0 0 10px;border:2px solid %s;border-radius:10px;padding:10px 12px">'
            '<div style="font-size:18px;font-weight:700;color:%s">%s</div><div style="font-size:13px;color:#3b4a55;margin-top:2px">%s</div>'
            '%s<div id="s960m" style="color:#9c2a20;font-weight:600"></div></section>'
            % (color, color, E(head), E(line), body))


def _shapes_html(shapes, eng=False):
    """S972: the money lines, each with its words and -- for tdoc / tslip -- its one slip-side tap."""
    E = _h.escape
    out = []
    for ln in shapes:
        txt, alt = shape_text(ln, eng)
        btn = ""
        if ln["shape"] == "tdoc" and ln["can"]:
            btn = ('<button type="button" class="s972a" data-key="%s" data-items="%s" data-act="addline" style="min-height:44px;padding:0 14px;border:1px solid #14456e;'
                   'border-radius:10px;background:#fff;color:#14456e;font-size:15px">%s</button>' % (E(ln["key"]), E(",".join(str(i) for i in ln["items"])),
                                                                                    "Yes, correct the slip" if eng else "Haan, parchi theek karo"))
        elif ln["shape"] == "tslip" and ln["can"]:
            btn = ('<button type="button" class="s972a" data-key="%s" data-items="%s" data-act="dropdup" style="min-height:44px;padding:0 14px;border:1px solid #14456e;'
                   'border-radius:10px;background:#fff;color:#14456e;font-size:15px">%s</button>' % (E(ln["key"]), E(",".join(str(i) for i in ln["items"])),
                                                                                    "No, remove one from the slip" if eng else "Nahi, parchi se ek hataiye"))
        out.append('<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 0;border-top:1px solid #e1e7eb">'
                   '<div style="flex:1 1 320px">%s%s</div>%s</div>'
                   % (E(txt), ('<div style="font-size:14px;color:#3b4a55;margin-top:2px">%s</div>' % E(alt)) if alt else "", btn))
    steps = ("Docterz is corrected the same evening; the line clears by itself about a minute after the export agrees." if eng else
             "Docterz aaj shaam hi theek karein; export milte hi lagbhag 1 minute mein line apne aap hat jayegi.")
    return "".join(out) + '<p style="margin:8px 0 0;font-size:14px;color:#3b4a55">%s</p>' % steps


SHAPE_JS = ('<script>(function(){var A=%s;document.addEventListener("click",function(ev){var b=ev.target&&ev.target.closest?ev.target.closest(".s972a"):null;'
            'if(!b)return;b.disabled=true;fetch(A+"/answer",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify({key:b.getAttribute("data-key"),act:b.getAttribute("data-act"),items:b.getAttribute("data-items")||""})})'
            '.then(function(r){return r.json();})'
            '.then(function(r){if(r.ok){if(window.s960load){window.s960load();}else{location.reload();}}else{b.disabled=false;var m=document.getElementById("s960m");if(m)m.textContent=r.err||"";}})'
            '.catch(function(){b.disabled=false;var m=document.getElementById("s960m");if(m)m.textContent="Nahi hua — dobara koshish karein.";});});})();</script>')


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
            'window.s960load=load;wire();vis();document.addEventListener("DOMContentLoaded",vis);setInterval(function(){load();vis();},30000);})();</script>')


def desk_box(con, eng=False, at=None):
    """What parchi_desk.page() puts at the top of the desk: the panel in its own wrapper (always there, so it can appear later);
    the page's own day picker decides whether it shows (today only) -- the box is always today's."""
    at = at or now_ist()
    return '<div id="s960w" data-today="%s">%s</div>%s%s' % (at.date().isoformat(), panel_html(con, eng, at),
                                                              PANEL_JS % (json.dumps(API), json.dumps(at.date().isoformat())),
                                                              SHAPE_JS % json.dumps(API))


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


def _audit_w(con, table, row_id, action, before, after, who):
    if _U["audit"]:
        try:
            _U["audit"](con, table, row_id, action, before=before, after=after, who=who)
        except Exception:                                 # noqa: BLE001 -- the audit never blocks the work
            pass


def answer(con, who, key, act, at=None, items=None):
    """S972: the slip-side answer of one money line of TODAY's evening list -- 'addline' (tdoc: both sides were done; the slip's
    second line is written, a copy of the first, no chhoot) or 'dropdup' (tslip: one side only; exactly the repeat is removed).
    Each row audited whole. Returns the words to show. `items` (the ids the box showed) must be the line's ids now (cold review 2);
    the check and the write run in ONE immediate transaction, so two taps cannot both write (cold review 3)."""
    con.commit()
    con.execute("BEGIN IMMEDIATE")
    try:
        return _answer(con, who, key, act, at, items)
    except BaseException:
        con.rollback()
        raise


def _answer(con, who, key, act, at=None, items=None):
    at = at or now_ist()
    day = at.date().isoformat()
    e = evening_export(con, day, at)
    chk = check(con, day, e) if e is not None else None
    ln = next((x for x in (chk or {}).get("shapes", []) if x["key"] == key), None)
    if ln is None:
        raise FreeError("Yeh line ab list mein nahi — page taaza hai.")
    want = {"addline": "tdoc", "dropdup": "tslip"}.get(act)
    if want is None or ln["shape"] != want or not ln["can"] or not ln["items"]:
        raise FreeError("Yeh jawab is line ke liye nahi.")
    if items is not None and sorted(str(i) for i in ln["items"]) != sorted(x for x in str(items).split(",") if x):
        raise FreeError("Parchi badal chuki — page taaza hai.")
    s = con.execute("SELECT * FROM slip WHERE id=? AND state='ok' AND day=?", (ln["slip_id"], day)).fetchone()
    if s is None:
        raise FreeError("Parchi badal chuki — page taaza hai.")
    stamp = _stamp(at)
    if act == "addline":
        it = con.execute("SELECT * FROM slip_item WHERE id=? AND slip_id=?", (ln["items"][0], s["id"])).fetchone()
        if it is None or int(it["discount_p"] or 0) != 0:
            raise FreeError("Yeh line badal chuki — page taaza hai.")
        it = dict(it)
        srt = con.execute("SELECT COALESCE(MAX(sort),0)+1 FROM slip_item WHERE slip_id=?", (s["id"],)).fetchone()[0]
        side = {"R": "L", "L": "R"}.get((it.get("side") or "").strip().upper())
        if side is None:
            raise FreeError("Is line par taraf (R/L) nahi — Shavez desk par theek karein.")
        cur = con.execute("INSERT INTO slip_item (slip_id, kind, service_id, name, side, price_p, sort, discount_p) VALUES (?,?,?,?,?,?,?,0)",
                          (s["id"], it["kind"], it.get("service_id"), it.get("name") or "", side, int(it["price_p"] or 0), srt))
        con.execute("UPDATE slip SET updated_by=?, updated_at=? WHERE id=?", (who, stamp, s["id"]))
        _audit_w(con, "slip_item", cur.lastrowid, "slip_item_added_evening_s972", None,
                 json.dumps({"slip": s["id"], "copy_of": it["id"], "side": side, "why": "the other side too (evening check)"}), who)
        con.commit()
        return "Parchi %d par doosri taraf (%s) likh di." % (int(s["slip_no"]), side)
    n = 0
    for iid in ln["items"]:
        row = con.execute("SELECT * FROM slip_item WHERE id=? AND slip_id=?", (iid, s["id"])).fetchone()
        if row is None:
            continue
        if _has(con, "slip_adjust") and con.execute("SELECT 1 FROM slip_adjust WHERE item_id=? AND state<>'replaced'", (iid,)).fetchone():
            raise FreeError("Is line par chhoot ki entry hai — Shavez desk par theek karein.")
        con.execute("DELETE FROM slip_item WHERE id=?", (iid,))
        _audit_w(con, "slip_item", iid, "slip_item_removed_duplicate_s972", json.dumps(dict(row)), None, who)
        n += 1
    if n != len(ln["items"]):
        raise FreeError("Pehle hi hat chuki — page taaza hai.")
    con.execute("UPDATE slip SET updated_by=?, updated_at=? WHERE id=?", (who, stamp, s["id"]))
    con.commit()
    return "Parchi %d se doosri line hata di." % int(s["slip_no"])


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

    def api_answer():                                     # S972: the money line's one slip-side tap
        u, err = _gate()
        if err:
            return jsonify(ok=False, err="not allowed"), 403
        j = request.get_json(silent=True) or {}
        key, act = str(j.get("key") or "")[:80], str(j.get("act") or "")
        if not key.startswith("ev:") or act not in ("addline", "dropdup"):
            return jsonify(ok=False, err="Samajh nahi aaya."), 200
        try:
            msg = answer(db_getter(), str((u or {}).get("user", "") or ""), key, act, items=str(j.get("items") or "")[:200])
        except FreeError as ex:
            return jsonify(ok=False, err=str(ex)), 200
        return jsonify(ok=True, msg=msg)

    app.add_url_rule(API, "s960_evening", api_evening, methods=["GET"])
    app.add_url_rule(API + "/free", "s960_evening_free", api_free, methods=["POST"])
    app.add_url_rule(API + "/answer", "s972_evening_answer", api_answer, methods=["POST"])
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
        print("EVENING %s %s: export %s (%s) taken %s; missing %d; shapes %d%s; pushes %d" % (
            VERSION, day, chk["export_at"], chk["road"], chk["taken_at"], len(chk["rows"]), len(chk.get("shapes") or []),
            (" -- " + chk["err"]) if chk["err"] else "", pushes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
