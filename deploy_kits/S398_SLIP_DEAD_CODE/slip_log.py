#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""slip_log.py -- S324 (session 271, 19-Sep-2026), S325/S326/S327 fixes the same day; S328 adds the X-ray EMR upload list; S329: the tile opens a menu, one tap per X-ray upload; S330: blood tests: new = above the highest ID issued before the day. S383 (24-Sep-2026): the name on a lab report checked against the clinic ID's name; the doctors' counts. S382 (24-Sep-2026): "Report baaki" -- blood and X-ray reports pending, tap when mailed, mismatches flagged. S379 (23-Sep-2026): the Docterz upload screen retired (X-rays are filed by themselves now), a new patient's name filled from the overnight Docterz report, a discount on a procedure. The OPD & X-ray/Proc slip tile, and the night
cross-match report that runs ALONGSIDE the current end-of-day report.

THE OWNER, 19-Sep-2026 (the plan he approved in his own words, "Chamber Slip Log"):
  * the chamber assistant (Shavez; rarely Alisha, Shivani, Bhati) logs the slip number and the
    clinic ID of every slip as it reaches the chamber; the tile PROMPTS the next number of the
    running series (OPD book at reception 19201-19600, X-ray & procedure book in his chamber
    1001-1400);
  * a known patient autofills; an ID the patient master does not know yet is saved as
    "new today" with the slip number and ID only -- the name comes from the Docterz export at night;
  * a person with NO clinic ID (an attendant who wants an X-ray) -- rare, and it happened recently --
    is logged by name alone;
  * X-ray and procedure lists are SEPARATE dropdowns read from his own rate page (owner_service),
    several X-rays and up to three procedures a slip, "Other" with or without a name;
  * the room (Awdhesh; Shavez or Bhati) ticks Paid (UPI / cash) and Done whenever convenient --
    nothing ever waits on it; what stays open shows as a short reminder, never a block;
  * the report: slip-number order, OPD and X-ray/Proc sections apart, like the reception register,
    problems first. It runs beside the old report until he says replace it.
  * the screen has a Back button to the portal at the top, its sections stay collapsed and only the
    top one is open, so a flow completes on one screen without scrolling (the problem Manoj Bhati
    has on his own page).

WHAT IT WRITES. Three tables of its own, created on first request (F-303):
    slip_book   one row per series: the book's range and the number to start from
    slip        one row per slip number: series, number, day, clinic ID (or a name), state,
                the room's two ticks, who and when for every change
    slip_item   the X-rays / procedures on an X-ray/Proc slip, with the price read at logging time
It READS clinic_day_line / clinic_day_revenue (Docterz), patient_ref (the patient master) and
owner_service (his rate page). It writes none of them. No money, no ledger, no stock.

WHO. Its own unit 'slips' (seeded by the kit): maker = shavez, alisha, shivani, bhati, awdhesh;
checker = manoj, bhawna. A login with no row there is refused at the front gate.

Flask and the standard library only. No patient name, no number, no secret in this file (F-185).
"""
import datetime as dt
import json
import os
import re

from flask import Blueprint, jsonify, redirect, request

bp = Blueprint("slip_log", __name__)

_db = None
_require = None
_audit = None
UNIT = "slips"
_schema_done = False

SERIES = (("opd", "OPD"), ("xp", "X-ray / Proc"))
SERIES_NAME = dict(SERIES)
# The owner's two books as he stated them on 19-Sep-2026. Only the RANGES are seeded; the number to
# start from is asked on first use, because the day the kit is installed is not the day he spoke.
BOOKS = {"opd": (19201, 19600), "xp": (1001, 1400)}
MAX_XRAY = 6
MAX_PROC = 3
GAP_LIMIT = 25            # a jump bigger than this is a typing slip until the person confirms it
ID_JUMP = 60              # an ID this far above the highest known one asks for a re-check

SCHEMA = """
CREATE TABLE IF NOT EXISTS slip_book (
  series    TEXT PRIMARY KEY CHECK (series IN ('opd','xp')),
  first_no  INTEGER NOT NULL,
  last_no   INTEGER NOT NULL,
  start_no  INTEGER,
  set_by    TEXT NOT NULL DEFAULT '',
  set_at    TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS slip (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  series      TEXT NOT NULL CHECK (series IN ('opd','xp')),
  slip_no     INTEGER NOT NULL,
  day         TEXT NOT NULL,
  clinic_id   TEXT NOT NULL DEFAULT '',
  no_id_name  TEXT NOT NULL DEFAULT '',
  is_new      INTEGER NOT NULL DEFAULT 0,
  name_seen   TEXT NOT NULL DEFAULT '',
  state       TEXT NOT NULL DEFAULT 'ok'
              CHECK (state IN ('ok','missing','cancelled','spoilt','void')),
  note        TEXT NOT NULL DEFAULT '',
  paid_mode   TEXT NOT NULL DEFAULT '' CHECK (paid_mode IN ('','upi','cash')),
  paid_by     TEXT NOT NULL DEFAULT '',
  paid_at     TEXT NOT NULL DEFAULT '',
  done_by     TEXT NOT NULL DEFAULT '',
  done_at     TEXT NOT NULL DEFAULT '',
  logged_by   TEXT NOT NULL DEFAULT '',
  logged_at   TEXT NOT NULL DEFAULT '',
  updated_by  TEXT NOT NULL DEFAULT '',
  updated_at  TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS slip_live_no ON slip(series, slip_no) WHERE state <> 'void';
CREATE INDEX IF NOT EXISTS slip_day ON slip(day, series);
CREATE TABLE IF NOT EXISTS slip_item (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slip_id     INTEGER NOT NULL REFERENCES slip(id),
  kind        TEXT NOT NULL CHECK (kind IN ('xray','proc')),
  service_id  INTEGER,
  name        TEXT NOT NULL DEFAULT '',
  side        TEXT NOT NULL DEFAULT '',
  price_p     INTEGER NOT NULL DEFAULT 0,
  sort        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS slip_item_slip ON slip_item(slip_id);
"""


def init(app, db_getter, require_fn, audit_fn=None, unit="slips", url_prefix=""):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


def ensure(con):
    global _schema_done
    if _schema_done:
        return
    con.executescript(SCHEMA)
    try:                                                  # S379: a procedure can carry a discount (the owner)
        if "discount_p" not in {r[1] for r in con.execute("PRAGMA table_info(slip_item)")}:
            con.execute("ALTER TABLE slip_item ADD COLUMN discount_p INTEGER NOT NULL DEFAULT 0")
    except Exception:                                    # noqa: BLE001 -- the slip still saves without it
        pass
    for s, (a, b) in BOOKS.items():
        con.execute("INSERT OR IGNORE INTO slip_book(series, first_no, last_no, start_no, set_by, set_at) "
                    "VALUES (?,?,?,NULL,'seed',?)", (s, a, b, _stamp()))
    con.commit()
    _schema_done = True


# ---------------------------------------------------------------- helpers
def _now():
    """The box's clock is IST. SLIP_NOW=<iso> pins it for the walk."""
    v = os.environ.get("SLIP_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now().replace(microsecond=0)


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return _now().date().isoformat()


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _rs(p):
    return "₹{:,}".format(int(round((p or 0) / 100.0)))


def _dmy(iso):
    try:
        return dt.date.fromisoformat(iso[:10]).strftime("%d-%b-%Y")
    except (ValueError, TypeError):
        return iso or "—"


def _iso_ok(s):
    try:
        return dt.date.fromisoformat(s).isoformat() == s
    except (ValueError, TypeError):
        return False


def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _roles(u):
    return set(u.get("roles") or [])


def _who(u):
    return (u or {}).get("user", "")


def _clean_id(v):
    v = re.sub(r"\s+", "", str(v or ""))
    return v[:12] if re.fullmatch(r"[0-9A-Za-z\-/]{1,12}", v or "") else ""


def _audit_safe(con, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, "slip", row_id, action, before=before, after=after, who=who)
    except Exception:                                    # noqa: BLE001 -- the audit never blocks the work
        pass


def _cols(con, table):
    return {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}


# ---------------------------------------------------------------- the patient master
def patient(con, clinic_id):
    """(name, last4) from patient_ref, or None. Read-only."""
    if not clinic_id:
        return None
    try:
        r = con.execute("SELECT name, phone_last4 FROM patient_ref WHERE clinic_id=? "
                        "AND (merged_into IS NULL OR merged_into='') ORDER BY id LIMIT 1",
                        (clinic_id,)).fetchone()
    except Exception:                                    # noqa: BLE001 -- a missing master is 'unknown'
        return None
    if r:
        return (r["name"] or "", r["phone_last4"] or "")
    try:                                                 # S325: the master lacks some old IDs -- Docterz's own day lines know them
        d = con.execute("SELECT patient FROM clinic_day_line WHERE clinic_id=? AND patient<>'' "
                        "ORDER BY business_date DESC LIMIT 1", (clinic_id,)).fetchone()
    except Exception:                                    # noqa: BLE001
        d = None
    return (d["patient"], "") if d else None


def is_new_id(con, clinic_id, day=None):
    """S325 -- the owner's rule, 19-Sep-2026: "system knows till which number the clinic id exist".
    NEW means ABOVE the highest ID issued BEFORE that day. An ID at or below it is an old patient even
    when the master has no row for him (2681 was read as NAYA on the first live morning).
    S326 -- the same morning a real new patient read "Purana mareez": the master carries one stray row
    far ahead of the series (never seen in a visit), so the ceiling sat above every new ID. The
    ceiling is now the highest ID that actually came through Docterz or a visit before the day."""
    n = _int(clinic_id)
    hi = highest_id(con, day)
    if n is None or not hi:
        return True
    return n > hi


def highest_id(con, day=None):
    """S326: the highest clinic ID ISSUED before `day` (default today) -- from Docterz's day lines, the
    visit table, and master rows that have actually been seen. A master row never seen in a visit (a
    typed-ahead or stray number) does not move the ceiling."""
    day = day or _today()
    best = 0
    for q in ("SELECT MAX(CAST(clinic_id AS INTEGER)) FROM clinic_day_line WHERE clinic_id GLOB '[0-9]*' AND business_date<?",
              "SELECT MAX(CAST(clinic_id AS INTEGER)) FROM patient_visit WHERE clinic_id GLOB '[0-9]*' AND visit_date<?",
              "SELECT MAX(CAST(clinic_id AS INTEGER)) FROM patient_ref WHERE clinic_id GLOB '[0-9]*' "
              "AND last_seen IS NOT NULL AND last_seen<>'' AND last_seen<?"):
        try:
            v = con.execute(q, (day,)).fetchone()[0]
        except Exception:                                # noqa: BLE001 -- a missing table adds nothing
            v = None
        if v and int(v) > best:
            best = int(v)
    return best


# ---------------------------------------------------------------- his rate page, read-only
def services(con):
    """Active, not-rejected lines of owner_service, X-ray and procedure apart. Nothing is written."""
    try:
        have = _cols(con, "owner_service")
    except Exception:                                    # noqa: BLE001
        have = set()
    if not have:
        return [], []
    side = "side" if "side" in have else "'' AS side"
    status = "status" if "status" in have else "'approved' AS status"
    rows = con.execute("SELECT id, kind, name, price_p, %s, %s FROM owner_service WHERE active=1 "
                       "ORDER BY kind, id" % (side, status)).fetchall()
    out = {"xray": [], "proc": []}
    for r in rows:
        if (r["status"] or "") == "rejected" or r["kind"] not in out:
            continue
        out[r["kind"]].append({"id": r["id"], "name": r["name"], "price_p": int(r["price_p"] or 0),
                               "side": (r["side"] or "") == "ask"})
    return out["xray"], out["proc"]


# ---------------------------------------------------------------- the books and the next number
def book(con, series):
    return con.execute("SELECT * FROM slip_book WHERE series=?", (series,)).fetchone()


def next_no(con, series):
    """The number the tile expects next: one past the highest live number in the current book,
    else the start number he gave. None when the book has no start yet or has run out."""
    b = book(con, series)
    if not b:
        return None
    r = con.execute("SELECT MAX(slip_no) m FROM slip WHERE series=? AND state<>'void' "
                    "AND slip_no BETWEEN ? AND ?", (series, b["first_no"], b["last_no"])).fetchone()
    if r["m"] is not None:
        n = int(r["m"]) + 1
    elif b["start_no"] is not None:
        n = int(b["start_no"])
    else:
        return None
    return n if n <= b["last_no"] else None


def _live(con, series, no):
    return con.execute("SELECT * FROM slip WHERE series=? AND slip_no=? AND state<>'void'",
                       (series, no)).fetchone()


# ---------------------------------------------------------------- writing a slip
class SlipError(Exception):
    pass


def log_slip(con, who, series, slip_no, clinic_id, no_id_name, items, confirm_gap=False):
    """Save one slip. Returns (slip_id, note). Raises SlipError with a staff-readable message."""
    b = book(con, series)
    if not b:
        raise SlipError("Book set nahi hai.")
    if slip_no is None:
        raise SlipError("Parchi number likhein.")
    if not (b["first_no"] <= slip_no <= b["last_no"]):
        raise SlipError("%d is book (%d–%d) ka number nahi hai. Book badli ho to neeche "
                        "'Book' mein naya range likhein." % (slip_no, b["first_no"], b["last_no"]))
    if not clinic_id and not no_id_name:
        raise SlipError("Clinic ID likhein — ya 'ID nahi hai' chun kar naam likhein.")
    if series == "xp" and not items:
        raise SlipError("Kam se kam ek X-ray ya procedure chunein.")
    cur = _live(con, series, slip_no)
    if cur is not None and cur["state"] != "missing":
        raise SlipError("Parchi %d pehle se likhi hai (%s, %s). Galat ho to 'Aaj ki list' se hatayein."
                        % (slip_no, cur["logged_by"] or "?", (cur["logged_at"] or "")[11:16]))
    exp = next_no(con, series)
    gap = []
    if exp is not None and slip_no > exp:
        gap = list(range(exp, slip_no))
        if len(gap) > GAP_LIMIT and not confirm_gap:
            raise SlipError("Agla number %d hona chahiye tha, aapne %d likha — %d number beech mein "
                            "chhoot rahe hain. Number dobara dekhein; sahi ho to 'Haan, yahi number' "
                            "chun kar Save karein." % (exp, slip_no, len(gap)))
    day, now = _today(), _stamp()
    name_seen, is_new = "", 0
    if clinic_id:
        p = patient(con, clinic_id)
        if p:
            name_seen = p[0]
        if is_new_id(con, clinic_id):                     # S326: new is decided by the number, not by the name
            is_new = 1
    if cur is not None:                                   # a number that was left as missing, now filled
        con.execute("UPDATE slip SET day=?, clinic_id=?, no_id_name=?, is_new=?, name_seen=?, state='ok', "
                    "note='', logged_by=?, logged_at=?, updated_by=?, updated_at=? WHERE id=?",
                    (day if cur["day"] == day else cur["day"], clinic_id, no_id_name, is_new, name_seen,
                     who, now, who, now, cur["id"]))
        sid = cur["id"]
    else:
        c = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, no_id_name, is_new, name_seen, "
                        "state, logged_by, logged_at, updated_by, updated_at) VALUES (?,?,?,?,?,?,?,'ok',?,?,?,?)",
                        (series, slip_no, day, clinic_id, no_id_name, is_new, name_seen, who, now, who, now))
        sid = c.lastrowid
    for i, it in enumerate(items):
        con.execute("INSERT INTO slip_item(slip_id, kind, service_id, name, side, price_p, sort, discount_p) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (sid, it["kind"], it.get("service_id"), it["name"], it.get("side", ""),
                     int(it.get("price_p") or 0), i, int(it.get("discount_p") or 0)))
    # S327, the owner: every skipped number needs its reason (Radd / Kharab / Baad mein) from the person
    # using the tile -- a confirmed big jump still leaves each number in between to be answered.
    for g in gap:
        if _live(con, series, g) is None:
            con.execute("INSERT INTO slip(series, slip_no, day, state, note, logged_by, logged_at, "
                        "updated_by, updated_at) VALUES (?,?,?,'missing','',?,?,?,?)",
                        (series, g, day, who, now, who, now))
    _audit_safe(con, sid, "slip_log", None,
                json.dumps({"series": series, "no": slip_no, "items": len(items), "gap": len(gap)}), who)
    con.commit()
    note = ""
    if gap:
        note = ("Number %s chhoot gaya — 'Aaj ki list' mein batayein: radd / kharab / baad mein."
                % ", ".join(str(g) for g in gap[:6]) + (" …" if len(gap) > 6 else ""))
    return sid, note


def items_from_form(con, form):
    """Read the X-ray and procedure rows off the form against his rate page."""
    xr, pr = services(con)
    byid = {s["id"]: s for s in xr + pr}
    out = []
    for kind, n in (("xray", MAX_XRAY), ("proc", MAX_PROC)):
        for i in range(n):
            v = (form.get("%s%d" % (kind, i)) or "").strip()
            if not v:
                continue
            side = (form.get("%s%d_side" % (kind, i)) or "").strip()
            side = side if side in ("R", "L", "B") else ""
            if v == "other":
                nm = (form.get("%s%d_other" % (kind, i)) or "").strip()[:60]
                out.append({"kind": kind, "service_id": None, "name": ("Other: " + nm) if nm else "Other",
                            "side": side, "price_p": 0})
                continue
            s = byid.get(_int(v))
            if s is None or (s in xr) != (kind == "xray"):
                raise SlipError("List mein se chunein.")
            disc = 0
            if kind == "proc":                            # S379: "procedures get a discount sometimes" (the owner)
                dv = (form.get("%s%d_disc" % (kind, i)) or "").strip().replace(",", "")
                if dv:
                    d = _int(dv)
                    if d is None or d < 0:
                        raise SlipError("Chhoot mein sirf rupaye likhein.")
                    disc = d * 100
                    if s["price_p"] and disc > s["price_p"]:
                        raise SlipError("%s: chhoot %s rate %s se zyada nahi ho sakti." % (s["name"], _rs(disc), _rs(s["price_p"])))
            out.append({"kind": kind, "service_id": s["id"], "name": s["name"], "side": side,
                        "price_p": s["price_p"], "discount_p": disc})
    return out


# ---------------------------------------------------------------- reading a day
def day_slips(con, day, series=None):
    q = "SELECT * FROM slip WHERE day=? AND state<>'void'"
    a = [day]
    if series:
        q += " AND series=?"
        a.append(series)
    rows = [dict(r) for r in con.execute(q + " ORDER BY series, slip_no", a)]
    if rows:
        ids = [r["id"] for r in rows]
        its = {}
        for it in con.execute("SELECT * FROM slip_item WHERE slip_id IN (%s) ORDER BY slip_id, sort"
                              % ",".join("?" * len(ids)), ids):
            its.setdefault(it["slip_id"], []).append(dict(it))
        for r in rows:
            r["items"] = its.get(r["id"], [])
    return rows


def room_open(con, before_day=None, days=7):
    """X-ray/Proc slips whose Paid or Done tick is still open, newest last."""
    since = (_now().date() - dt.timedelta(days=days)).isoformat()
    q = ("SELECT * FROM slip WHERE series='xp' AND state='ok' AND day>=? AND (paid_mode='' OR done_at='')")
    a = [since]
    if before_day:
        q += " AND day<?"
        a.append(before_day)
    return [dict(r) for r in con.execute(q + " ORDER BY day, slip_no", a)]


def fill_new_names(con):
    """S379, the owner 23-Sep-2026: "for the Naya Mareez, the overnight report gives you the name of that patient".
    A new patient's slip carries the ID only; once the Docterz export of that day has arrived, the name it gives
    for that ID is written into the slip (name_seen), once. The slip table only; never a guess."""
    try:
        rows = con.execute("SELECT id, clinic_id, day FROM slip WHERE is_new=1 AND name_seen='' AND clinic_id<>'' "
                           "AND state='ok'").fetchall()
        n = 0
        for r in rows:
            d = con.execute("SELECT patient FROM clinic_day_line WHERE clinic_id=? AND patient<>'' "
                            "ORDER BY (business_date=?) DESC, business_date DESC LIMIT 1", (r["clinic_id"], r["day"])).fetchone()
            if d and (d["patient"] or "").strip():
                con.execute("UPDATE slip SET name_seen=? WHERE id=? AND name_seen=''", (d["patient"].strip()[:80], r["id"]))
                n += 1
        if n:
            con.commit()
        return n
    except Exception:                                    # noqa: BLE001 -- no Docterz table: the ID alone, as before
        return 0


def _who_label(r):
    if r.get("no_id_name"):
        return "%s (ID nahi)" % r["no_id_name"]
    if r.get("name_seen") and r.get("is_new"):
        return "%s · %s · naya" % (r["clinic_id"], r["name_seen"])
    if r.get("name_seen"):
        return "%s · %s" % (r["clinic_id"], r["name_seen"])
    if r.get("is_new"):
        return "%s · naya" % r["clinic_id"]
    return r.get("clinic_id") or "—"


def _items_label(items):
    out = []
    for it in items:
        s = it["name"] + ((" " + it["side"]) if it.get("side") else "")
        if int(it.get("discount_p") or 0):                # S379
            s += " (chhoot %s)" % _rs(it["discount_p"])
        out.append(s)
    return ", ".join(out)


# ================================================================ the Docterz cross-match (report)
def _docterz(con, day):
    try:
        arrived = con.execute("SELECT taken_at FROM clinic_day_revenue WHERE business_date=?",
                              (day,)).fetchone()
        lines = [dict(r) for r in con.execute(
            "SELECT section, sn, patient, clinic_id, amount_p, mode FROM clinic_day_line "
            "WHERE business_date=? ORDER BY section, sn", (day,))]
    except Exception:                                    # noqa: BLE001
        return None, []
    return (arrived["taken_at"] if arrived else None), lines


def usual_fee(con, day):
    """The consultation amount billed most often over the 60 days before this one."""
    since = (dt.date.fromisoformat(day) - dt.timedelta(days=60)).isoformat()
    try:
        r = con.execute("SELECT amount_p, COUNT(*) n FROM clinic_day_line WHERE section='consult' "
                        "AND business_date BETWEEN ? AND ? AND amount_p>0 GROUP BY amount_p "
                        "ORDER BY n DESC LIMIT 1", (since, day)).fetchone()
    except Exception:                                    # noqa: BLE001
        return 0
    return int(r["amount_p"]) if r else 0


def _mode_word(m):
    m = (m or "").lower()
    if "cash" in m:
        return "cash"
    if m:
        return "upi"
    return ""


def match_day(con, day):
    """The report's content. Pure read; returns a dict the page renders."""
    arrived, lines = _docterz(con, day)
    slips = day_slips(con, day)
    opd = [s for s in slips if s["series"] == "opd"]
    xp = [s for s in slips if s["series"] == "xp"]
    fee = usual_fee(con, day)
    by_id = {}
    for ln in lines:
        by_id.setdefault(str(ln["clinic_id"] or ""), []).append(ln)
    names = {}
    for ln in lines:
        if ln["clinic_id"] and ln["patient"]:
            names.setdefault(str(ln["clinic_id"]), ln["patient"])
    flags = []

    def nm(s):
        if s.get("no_id_name"):
            return s["no_id_name"]
        return s.get("name_seen") or names.get(s["clinic_id"]) or \
            ((patient(con, s["clinic_id"]) or ("", ""))[0]) or ""

    xp_ids = {s["clinic_id"] for s in xp if s["state"] == "ok" and s["clinic_id"]}
    used = set()                                          # (section, sn) of Docterz lines a slip explains
    opd_rows = []
    for s in opd:
        row = {"slip": s, "name": nm(s), "docterz": "", "verdict": "", "why": []}
        if s["state"] != "ok":
            row["verdict"] = s["state"]
            if s["state"] == "missing":
                flags.append("OPD slip %d: number skipped, no reason given" % s["slip_no"])
            opd_rows.append(row)
            continue
        if s["no_id_name"]:
            row["verdict"] = "check"
            row["why"].append("no clinic ID — match by hand")
            flags.append("OPD slip %d: no clinic ID (%s)" % (s["slip_no"], s["no_id_name"]))
            opd_rows.append(row)
            continue
        if arrived is None:
            row["verdict"] = "waiting"
            opd_rows.append(row)
            continue
        mine = by_id.get(s["clinic_id"], [])
        cons = [ln for ln in mine if ln["section"] == "consult" and (ln["section"], ln["sn"]) not in used]
        free = [ln for ln in mine if ln["section"] in ("revisit", "concession")]
        if cons:
            ln = cons[0]
            used.add((ln["section"], ln["sn"]))
            row["docterz"] = "%s %s" % (_rs(ln["amount_p"]), _mode_word(ln["mode"]))
            row["verdict"] = "matched"
            if fee and ln["amount_p"] != fee:
                row["verdict"] = "check"
                extra = ln["amount_p"] - fee
                w = "consultation %s, usual %s" % (_rs(ln["amount_p"]), _rs(fee))
                has_xp_line = any(x["section"] in ("xray", "proc") for x in mine)
                if extra > 0 and s["clinic_id"] in xp_ids and not has_xp_line:
                    w += " — the %s extra looks like the X-ray/procedure money booked as consultation" % _rs(extra)
                row["why"].append(w)
                flags.append("OPD slip %d (%s): %s" % (s["slip_no"], row["name"] or s["clinic_id"], w))
        elif free:
            row["docterz"] = "free (%s)" % free[0]["section"]
            row["verdict"] = "check"
            row["why"].append("slip says paid, Docterz has it free")
            flags.append("OPD slip %d (%s): Docterz shows a free %s" % (s["slip_no"], row["name"] or s["clinic_id"],
                                                                         free[0]["section"]))
        else:
            row["verdict"] = "check"
            row["why"].append("no Docterz entry")
            flags.append("OPD slip %d (%s): no Docterz entry" % (s["slip_no"], row["name"] or s["clinic_id"]))
        if s["is_new"] and not s["name_seen"] and row["name"]:
            row["why"].append("new patient — name from Docterz")
        elif s["is_new"] and not row["name"]:
            row["verdict"] = "check"
            row["why"].append("new ID not in the Docterz export")
            flags.append("OPD slip %d: new ID %s is not in the Docterz export" % (s["slip_no"], s["clinic_id"]))
        opd_rows.append(row)

    # X-ray / Proc: per patient, the slips' items against the Docterz X-ray and procedure lines
    xp_rows = []
    per_pat = {}
    for s in xp:
        if s["state"] == "ok" and s["clinic_id"]:
            per_pat.setdefault(s["clinic_id"], []).append(s)
    pat_verdict = {}
    if arrived is not None:
        for cid, ss in per_pat.items():
            mine = by_id.get(cid, [])
            dx = [ln for ln in mine if ln["section"] == "xray"]
            dp = [ln for ln in mine if ln["section"] == "proc"]
            for ln in dx + dp:
                used.add((ln["section"], ln["sn"]))
            items = [it for s in ss for it in s["items"]]
            sx = [it for it in items if it["kind"] == "xray"]
            sp = [it for it in items if it["kind"] == "proc"]
            why = []
            if sx and not dx:
                why.append("X-ray not in Docterz")
            if sp and not dp:
                why.append("procedure not in Docterz")
            if dx and not sx:
                why.append("Docterz has an X-ray the slip does not")
            if dp and not sp:
                why.append("Docterz has a procedure the slip does not")
            if sx and dx and all(it["price_p"] > 0 for it in sx):
                want = sum(it["price_p"] for it in sx)
                got = sum(ln["amount_p"] for ln in dx)
                if want != got:
                    why.append("X-ray: slip rates %s, Docterz %s" % (_rs(want), _rs(got)))
            if sp and dp and all(it["price_p"] > 0 for it in sp):        # S379: procedures, after any discount
                disc = sum(int(it.get("discount_p") or 0) for it in sp)
                want = sum(it["price_p"] for it in sp) - disc
                got = sum(ln["amount_p"] for ln in dp)
                if want != got:
                    why.append("procedure: slip %s%s, Docterz %s" % (
                        _rs(want), (" after %s discount" % _rs(disc)) if disc else "", _rs(got)))
            dm = {_mode_word(ln["mode"]) for ln in dx + dp} - {""}
            for s in ss:
                if s["paid_mode"] and dm and s["paid_mode"] not in dm:
                    why.append("room ticked %s, Docterz says %s" % (s["paid_mode"].upper(),
                                                                    "/".join(sorted(m.upper() for m in dm))))
                    break
            got_txt = " + ".join("%s %s" % (_rs(ln["amount_p"]), ln["section"]) for ln in dx + dp)
            pat_verdict[cid] = (why, got_txt)
    for s in xp:
        row = {"slip": s, "name": nm(s), "docterz": "", "verdict": "", "why": []}
        if s["state"] != "ok":
            row["verdict"] = s["state"]
            if s["state"] == "missing":
                flags.append("X-ray/Proc slip %d: number skipped, no reason given" % s["slip_no"])
            xp_rows.append(row)
            continue
        if not s["paid_mode"] or not s["done_at"]:
            miss = [w for w, ok in (("Paid", s["paid_mode"]), ("Done", s["done_at"])) if not ok]
            row["why"].append("room did not tick " + " / ".join(miss))
            flags.append("X-ray/Proc slip %d: room did not tick %s" % (s["slip_no"], " / ".join(miss)))
        if s["no_id_name"]:
            row["verdict"] = "check"
            row["why"].append("no clinic ID — match by hand")
            flags.append("X-ray/Proc slip %d: no clinic ID (%s)" % (s["slip_no"], s["no_id_name"]))
        elif arrived is None:
            row["verdict"] = "waiting"
        else:
            why, got_txt = pat_verdict.get(s["clinic_id"], ([], ""))
            row["docterz"] = got_txt
            if why:
                row["why"].extend(why)
                for w in why:
                    flags.append("X-ray/Proc slip %d (%s): %s" % (s["slip_no"], row["name"] or s["clinic_id"], w))
            row["verdict"] = "check" if row["why"] else "matched"
        if row["why"] and row["verdict"] not in ("check", "waiting"):
            row["verdict"] = "check"
        xp_rows.append(row)

    orphans = []
    if arrived is not None:
        opd_ids = {s["clinic_id"] for s in opd if s["state"] == "ok"}
        for ln in lines:
            if ln["section"] not in ("consult", "xray", "proc") or (ln["section"], ln["sn"]) in used:
                continue
            if ln["section"] == "consult" and ln["clinic_id"] in opd_ids:
                continue
            orphans.append(ln)
            flags.append("Docterz %s %s (%s, ID %s): no slip logged" % (
                {"consult": "consultation", "xray": "X-ray", "proc": "procedure"}[ln["section"]],
                _rs(ln["amount_p"]), ln["patient"] or "?", ln["clinic_id"] or "?"))
    # de-duplicate flags, keep order
    seen, fl = set(), []
    for f in flags:
        if f not in seen:
            seen.add(f)
            fl.append(f)
    return {"day": day, "arrived": arrived, "fee": fee, "opd": opd_rows, "xp": xp_rows,
            "orphans": orphans, "flags": fl}


# ================================================================ routes
def _form_err(msg, sec=None):
    return redirect("/finance/slips?s=" + _q(sec or request.form.get("sec") or "") + "&err=" + _q(msg), code=303)


def _q(s):
    from urllib.parse import quote
    return quote(s or "", safe="")


@bp.route("/finance/slips")
def home():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return _shell("Slips", _denied(), "en")
    con = _db()
    ensure(con)
    fill_new_names(con)                                   # S379
    if "checker" in _roles(u) and "maker" not in _roles(u) and not request.args.get("tile"):
        return redirect("/finance/slips/report", code=302)
    want = request.args.get("s") or ""
    if want in _SCREENS:
        return _shell(_SCREENS[want], _tile_html(con, u), "hi", back="/finance/slips", back_label="\u2190 Menu")
    return _shell("Parchi", _tile_html(con, u), "hi")


@bp.route("/finance/slips/api/patient")
def api_patient():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    con = _db()
    ensure(con)
    cid = _clean_id(request.args.get("id"))
    if not cid:
        return jsonify(ok=False)
    p = patient(con, cid)
    new = is_new_id(con, cid)
    if p:
        return jsonify(ok=True, known=True, name=p[0], last4=p[1], new=new)
    hi = highest_id(con)
    n = _int(cid)
    far = bool(hi and n is not None and n > hi + ID_JUMP)
    return jsonify(ok=True, known=False, far=far, highest=hi, old=not new)


@bp.route("/finance/slips/save", methods=["POST"])
def save():
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    ensure(con)
    f = request.form
    series = f.get("series") if f.get("series") in SERIES_NAME else ""
    if not series:
        return _form_err("Galat form.")
    noid = f.get("noid") == "1"
    cid = "" if noid else _clean_id(f.get("clinic_id") or f.get("pick"))
    nm = (f.get("no_id_name") or "").strip()[:60] if noid else ""
    if not noid and (f.get("clinic_id") or "").strip() and not cid:
        return _form_err("Clinic ID mein sirf number likhein.")
    if cid and not patient(con, cid) and f.get("id_ok") != "1":
        hi, n = highest_id(con), _int(cid)
        if hi and n is not None and n > hi + ID_JUMP:
            return _form_err("ID %s sabse bade ID %d se bahut aage hai — dobara dekhein; sahi ho to "
                             "'ID sahi hai' chun kar Save karein." % (cid, hi))
    try:
        items = items_from_form(con, f) if series == "xp" else []
        sid, note = log_slip(con, _who(u), series, _int(f.get("slip_no")), cid, nm, items,
                             confirm_gap=f.get("gap_ok") == "1")
    except SlipError as ex:
        return _form_err(str(ex))
    r = con.execute("SELECT slip_no FROM slip WHERE id=?", (sid,)).fetchone()
    msg = "Parchi %d save ho gayi." % r["slip_no"] + ((" " + note) if note else "")
    return redirect("/finance/slips?s=" + series + "&ok=" + _q(msg), code=303)


@bp.route("/finance/slips/room/<int:sid>", methods=["POST"])
def room(sid):
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    ensure(con)
    s = con.execute("SELECT * FROM slip WHERE id=? AND series='xp' AND state='ok'", (sid,)).fetchone()
    if not s:
        return _form_err("Parchi nahi mili.")
    act, now, who = request.form.get("act"), _stamp(), _who(u)
    before = json.dumps({"paid": s["paid_mode"], "done": s["done_at"]})
    if act in ("upi", "cash"):
        con.execute("UPDATE slip SET paid_mode=?, paid_by=?, paid_at=?, updated_by=?, updated_at=? WHERE id=?",
                    (act, who, now, who, now, sid))
    elif act == "unpaid":
        con.execute("UPDATE slip SET paid_mode='', paid_by='', paid_at='', updated_by=?, updated_at=? WHERE id=?",
                    (who, now, sid))
    elif act == "done":
        con.execute("UPDATE slip SET done_by=?, done_at=?, updated_by=?, updated_at=? WHERE id=?",
                    (who, now, who, now, sid))
    elif act == "undone":
        con.execute("UPDATE slip SET done_by='', done_at='', updated_by=?, updated_at=? WHERE id=?",
                    (who, now, sid))
    else:
        return _form_err("Galat button.", "room")
    _audit_safe(con, sid, "slip_room_" + act, before, None, who)
    con.commit()
    return redirect("/finance/slips?s=room", code=303)


@bp.route("/finance/slips/state/<int:sid>", methods=["POST"])
def set_state(sid):
    """A skipped number: cancelled / spoilt / later. Or a wrong entry taken off (void)."""
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    ensure(con)
    s = con.execute("SELECT * FROM slip WHERE id=? AND state<>'void'", (sid,)).fetchone()
    if not s:
        return _form_err("Parchi nahi mili.")
    act, who, now = request.form.get("act"), _who(u), _stamp()
    why = (request.form.get("why") or "").strip()[:120]
    if act in ("cancelled", "spoilt", "missing"):
        if s["state"] not in ("missing", "cancelled", "spoilt"):
            return _form_err("Yeh parchi likhi hui hai; ise hatane ke liye 'Hatao' dabayein.")
        con.execute("UPDATE slip SET state=?, updated_by=?, updated_at=? WHERE id=?", (act, who, now, sid))
    elif act == "void":
        if s["state"] != "ok":
            return _form_err("Sirf likhi hui parchi hat sakti hai.")
        same = s["logged_by"] == who and s["day"] == _today()
        if not same and not why:
            return _form_err("Parchi %d hatane ki wajah likhein." % s["slip_no"])
        con.execute("UPDATE slip SET state='void', note=?, updated_by=?, updated_at=? WHERE id=?",
                    (why or "same-day correction", who, now, sid))
    else:
        return _form_err("Galat button.")
    _audit_safe(con, sid, "slip_" + act, json.dumps({"state": s["state"]}), json.dumps({"state": act, "why": why}), who)
    con.commit()
    return redirect("/finance/slips?s=list&ok=" + _q("Parchi %d: theek kar diya." % s["slip_no"]), code=303)


@bp.route("/finance/slips/book", methods=["POST"])
def set_book():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    con = _db()
    ensure(con)
    f = request.form
    series = f.get("series") if f.get("series") in SERIES_NAME else ""
    a, b, st = _int(f.get("first_no")), _int(f.get("last_no")), _int(f.get("start_no"))
    if not series or a is None or b is None or st is None or not (0 < a <= st <= b) or b - a > 5000:
        return _form_err("Book ke teenon number sahi likhein: pehla ≤ aaj ka pehla ≤ aakhri.")
    old = book(con, series)
    con.execute("UPDATE slip_book SET first_no=?, last_no=?, start_no=?, set_by=?, set_at=? WHERE series=?",
                (a, b, st, _who(u), _stamp(), series))
    _audit_safe(con, 0, "slip_book", json.dumps(dict(old) if old else None),
                json.dumps({"series": series, "first": a, "last": b, "start": st}), _who(u))
    con.commit()
    return redirect("/finance/slips?s=" + series + "&ok=" + _q("%s book: %d–%d, agla number %d."
                                              % (SERIES_NAME[series], a, b, next_no(con, series) or st))
                    , code=303)


@bp.route("/finance/slips/report")
@bp.route("/finance/slips/report/<day>")
def report(day=None):
    u, err = _require("checker", "maker", unit=UNIT)
    if err:
        return _shell("Slip report", _denied(), "en")
    con = _db()
    ensure(con)
    if day is None:
        r = con.execute("SELECT MAX(day) d FROM slip WHERE state<>'void'").fetchone()
        day = r["d"] or _today()
    if not _iso_ok(day):
        return redirect("/finance/slips/report", code=302)
    fill_new_names(con)                                   # S379
    return _shell("Slip report — %s" % _dmy(day), _report_html(con, match_day(con, day), u), "en")


# ================================================================ pages
def _denied():
    return """<div class="card"><h2>Not permitted</h2><p>Your login is not on the slip tile.
      If that is wrong, ask Dr Manoj.</p></div>"""


def _opts(rows, placeholder):
    o = ['<option value="">%s</option>' % placeholder]
    for s in rows:
        o.append('<option value="%d" data-side="%d">%s%s</option>' % (
            s["id"], 1 if s["side"] else 0, _esc(s["name"]),
            (" · %s" % _rs(s["price_p"])) if s["price_p"] else ""))
    o.append('<option value="other">Other</option>')
    return "".join(o)


def _item_rows(kind, rows, n, label):
    out = []
    for i in range(n):
        out.append(
            '<div class="irow" data-kind="%s"%s><select name="%s%d" class="svc">%s</select>'
            '<select name="%s%d_side" class="side" hidden><option value="">side</option>'
            '<option value="R">R</option><option value="L">L</option><option value="B">Both</option></select>'
            '<input name="%s%d_other" class="oth" placeholder="naam (zaroori nahi)" maxlength="60" hidden>%s</div>'
            % (kind, "" if i == 0 else " hidden", kind, i, _opts(rows, label), kind, i, kind, i,
               ('<input name="%s%d_disc" class="disc" inputmode="numeric" placeholder="chhoot ₹ (ho to)" '
                'maxlength="6" hidden>' % (kind, i)) if kind == "proc" else ""))
    return "".join(out)


def _book_line(con, series):
    b = book(con, series)
    nx = next_no(con, series)
    return b, nx


def _entry_head(con, series):
    """The slip-number line of a form, or the book form when the number cannot be prompted."""
    b, nx = _book_line(con, series)
    if nx is None:
        why = ("Book khatam — naye book ka range likhein." if b and b["start_no"] is not None
               else "Pehli baar: aaj ki pehli parchi ka number likhein.")
        return None, _book_form(con, series, why)
    return nx, ('<div class="row"><label>Parchi no.<input name="slip_no" inputmode="numeric" class="no" '
                'value="%d" required></label><span class="sm">book %d–%d</span></div>'
                % (nx, b["first_no"], b["last_no"]))


def _book_form(con, series, why):
    b = book(con, series)
    a, z = (b["first_no"], b["last_no"]) if b else BOOKS[series]
    return ('<form method="post" action="/finance/slips/book" class="bookf"><input type="hidden" name="series" value="%s">'
            '<input type="hidden" name="sec" value="%s"><p class="warn">%s</p>'
            '<div class="row"><label>Book pehla<input name="first_no" inputmode="numeric" value="%d"></label>'
            '<label>Book aakhri<input name="last_no" inputmode="numeric" value="%d"></label></div>'
            '<div class="row"><label>Aaj / agla number<input name="start_no" inputmode="numeric" required></label>'
            '<button class="go">Theek</button></div></form>' % (series, series, _esc(why), a, z))


def _patient_block(today_opd, with_pick):
    pick = ""
    if with_pick and today_opd:
        o = ['<option value="">— aaj ke OPD se chunein —</option>']
        seen = set()
        for s in reversed(today_opd):
            if s["state"] != "ok" or not s["clinic_id"] or s["clinic_id"] in seen:
                continue
            seen.add(s["clinic_id"])
            o.append('<option value="%s">%s</option>' % (_esc(s["clinic_id"]), _esc(_who_label(s))))
        pick = '<select name="pick" class="pick">%s</select><span class="or">ya</span>' % "".join(o)
    return ('<div class="row pat">%s<label class="cid">Clinic ID<input name="clinic_id" inputmode="numeric" '
            'autocomplete="off" class="cidin"></label></div>'
            '<div class="who" aria-live="polite"></div>'
            '<div class="row small"><label class="chk"><input type="checkbox" name="noid" value="1" class="noid"> ID nahi hai'
            '</label><input name="no_id_name" class="nonm" placeholder="naam (saath aaya vyakti)" maxlength="60" hidden>'
            '<label class="chk idok" hidden><input type="checkbox" name="id_ok" value="1"> ID sahi hai</label></div>'
            % pick)


def _tile_html(con, u):
    today = _today()
    msg_ok, msg_err = request.args.get("ok") or "", request.args.get("err") or ""
    xr, pr = services(con)
    slips = day_slips(con, today)
    opd = [s for s in slips if s["series"] == "opd"]
    xp = [s for s in slips if s["series"] == "xp"]
    open_old = room_open(con, before_day=today)
    open_today = [s for s in xp if s["state"] == "ok" and (not s["paid_mode"] or not s["done_at"])]
    missing = [s for s in slips if s["state"] == "missing"]
    user = _who(u).lower()
    room_first = user == "awdhesh"

    parts = []
    if msg_ok:
        parts.append('<div class="ok">%s</div>' % _esc(msg_ok))
    if msg_err:
        parts.append('<div class="bad">%s</div>' % _esc(msg_err))
    rem = []
    if open_old:
        rem.append("%d purani X-ray/Proc parchi mein Paid/Done baaki: %s" % (
            len(open_old), ", ".join(str(s["slip_no"]) for s in open_old[:8]) + (" …" if len(open_old) > 8 else "")))
    if missing:
        rem.append("Chhoote number: %s — 'Aaj ki list' mein batayein" % ", ".join(str(s["slip_no"]) for s in missing[:8]))
    if rem:
        parts.append('<div class="rem">%s</div>' % "<br>".join(_esc(x) for x in rem))

    # --- OPD
    nx, head = _entry_head(con, "opd")
    if nx is None:
        opd_body = head
    else:
        opd_body = ('<form method="post" action="/finance/slips/save" class="slipf">'
                    '<input type="hidden" name="series" value="opd"><input type="hidden" name="sec" value="opd">'
                    + head + _patient_block([], False) + _gap_ok() +
                    '<button class="go">Save</button></form>')
    sec_opd = _sec("opd", "OPD parchi", "agla %s" % (nx if nx else "—"), opd_body)

    # --- X-ray / Proc
    nx2, head2 = _entry_head(con, "xp")
    if nx2 is None:
        xp_body = head2
    else:
        xp_body = ('<form method="post" action="/finance/slips/save" class="slipf">'
                   '<input type="hidden" name="series" value="xp"><input type="hidden" name="sec" value="xp">'
                   + head2 + _patient_block(opd, True) +
                   '<div class="lists"><div class="lst"><b>X-ray</b>' + _item_rows("xray", xr, MAX_XRAY, "X-ray chunein") +
                   '<button type="button" class="more" data-kind="xray">+ aur X-ray</button></div>'
                   '<div class="lst"><b>Procedure</b>' + _item_rows("proc", pr, MAX_PROC, "Procedure chunein") +
                   '<button type="button" class="more" data-kind="proc">+ aur procedure</button></div></div>'
                   + _gap_ok() + '<button class="go">Save</button></form>')
    sec_xp = _sec("xp", "X-ray / Proc parchi", "agla %s" % (nx2 if nx2 else "—"), xp_body)

    # --- Room
    rows = []
    for s in open_old + [s for s in xp if s["state"] == "ok"]:
        paid = s["paid_mode"]
        rows.append(
            '<div class="rrow%s"><div class="rl"><span class="no">%d</span> %s<br><span class="sm">%s%s</span></div>'
            '<span class="amt">%s</span>'
            '<form method="post" action="/finance/slips/room/%d" class="rb">'
            '<button name="act" value="%s" class="t%s">UPI</button>'
            '<button name="act" value="%s" class="t%s">Cash</button>'
            '<button name="act" value="%s" class="t%s">Done</button></form></div>' % (
                " old" if s["day"] != today else "", s["slip_no"], _esc(_who_label(s)),
                _esc(_items_label(s.get("items") or _items_of(con, s["id"]))),
                (" · %s" % _dmy(s["day"])[:6]) if s["day"] != today else "",
                _amount_label(s.get("items") or _items_of(con, s["id"])),
                s["id"],
                "unpaid" if paid == "upi" else "upi", " on" if paid == "upi" else "",
                "unpaid" if paid == "cash" else "cash", " on" if paid == "cash" else "",
                "undone" if s["done_at"] else "done", " on" if s["done_at"] else ""))
    room_body = "".join(rows) or '<p class="sm">Aaj abhi koi X-ray/Proc parchi nahi.</p>'
    room_body += '<p class="sm">Sirf sign ki hui, paid parchi par kaam. Tick jab chahein karein — kuch rukta nahi.</p>'
    sec_room = _sec("room", "X-ray room work", "%d baaki" % (len(open_old) + len(open_today)), room_body)

    # --- Today's list
    li = []
    for series, label in SERIES:
        ss = [s for s in slips if s["series"] == series]
        li.append('<h3>%s · %d</h3>' % (label, len([s for s in ss if s["state"] == "ok"])))
        for s in ss:
            if s["state"] == "ok":
                li.append('<div class="lrow"><span class="no">%d</span> %s <span class="sm">%s</span>'
                          '<form method="post" action="/finance/slips/state/%d" class="vf">'
                          '<input name="why" placeholder="wajah" maxlength="120"><button name="act" value="void" '
                          'class="x">Hatao</button></form></div>' % (
                              s["slip_no"], _esc(_who_label(s)), _esc(_items_label(s["items"])), s["id"]))
            else:
                word = {"missing": "chhoota", "cancelled": "radd", "spoilt": "kharab"}[s["state"]]
                li.append('<div class="lrow miss"><span class="no">%d</span> <b>%s</b>'
                          '<form method="post" action="/finance/slips/state/%d" class="vf">'
                          '<button name="act" value="cancelled">Radd</button>'
                          '<button name="act" value="spoilt">Kharab</button>'
                          '<button name="act" value="missing">Baad mein</button></form>'
                          '<span class="sm">baad mein likhni ho to upar usi number se Save karein</span></div>'
                          % (s["slip_no"], word, s["id"]))
    sec_list = _sec("list", "Aaj ki list", "%d parchi" % len([s for s in slips if s["state"] == "ok"]), "".join(li))

    # --- Books
    bl = ['<p class="sm">Book khatam hone par hi: naye book ka pehla aur aakhri number likhein.</p>']
    for series, label in SERIES:
        b, nx_ = _book_line(con, series)
        bl.append('<p><b>%s</b>: abhi book %d\u2013%d \u00b7 agla %s</p>' % (label, b["first_no"], b["last_no"], nx_ or "\u2014"))
        bl.append('<details><summary class="sm">%s \u2014 naya book shuru karein</summary>%s</details>'
                  % (label, _book_form(con, series, "Naya book: pehla number, aakhri number, aur pehli parchi")))
    if "checker" in _roles(u):
        bl.append('<p><a href="/finance/slips/report">Report (English)</a></p>')
    sec_book = _sec("book", "Start new book", "", "".join(bl))

    secs = {"opd": sec_opd, "xp": sec_xp, "room": sec_room, "list": sec_list, "book": sec_book}
    want = request.args.get("s") or ""
    if want in secs:                                      # S329: one screen at a time, opened from the menu
        return "".join(parts) + secs[want].replace('<details class="sec"', '<details class="sec" open', 1) + _TILE_JS
    if want != "all":
        return "".join(parts) + _menu_html(con, u, nx, nx2, len(open_old) + len(open_today),
                                           len([x for x in slips if x["state"] == "ok"]), len(missing))
    order = [sec_room, sec_opd, sec_xp, sec_list, sec_book] if room_first else \
        [sec_opd, sec_xp, sec_room, sec_list, sec_book]
    # only the top section open (the owner, 19-Sep-2026)
    order[0] = order[0].replace("<details class=\"sec\"", "<details class=\"sec\" open", 1)
    return "".join(parts) + "".join(order) + _TILE_JS


def _amount_label(items):
    """S327: the slip's amount, read-only, from the rates copied at logging. An unpriced line is said so."""
    tot = sum(int(it.get("price_p") or 0) - int(it.get("discount_p") or 0) for it in items)   # S379: after discount
    unpriced = [it for it in items if not int(it.get("price_p") or 0)]
    if not items:
        return "\u2014"
    if tot and unpriced:
        return "%s + %d rate nahi" % (_rs(tot), len(unpriced))
    if not tot:
        return "rate nahi"
    return _rs(tot)


_SCREENS = {"opd": "OPD parchi", "xp": "X-ray / Proc parchi", "room": "X-ray room work",
            "list": "Aaj ki list", "book": "Start new book", "all": "Parchi \u2014 sab"}


def _menu_html(con, u, nx, nx2, room_n, today_n, miss_n):
    """S329, the owner: "a tile is clicked and then the submenu appears" -- one screen per job."""
    try:                                                  # S379: the Docterz upload screen is retired (the owner);
        blood_n = len([o for o in blood_state(con)[0] if not o["outcome"]])   # its blood questions live on Blood test
    except Exception:                                    # noqa: BLE001
        blood_n = 0
    user = _who(u).lower()
    items = {
        "opd": ('<a class="mi" href="/finance/slips?s=opd"><b>OPD parchi</b><span>agla %s</span></a>' % (nx or "\u2014")),
        "xp": ('<a class="mi" href="/finance/slips?s=xp"><b>X-ray / Proc parchi</b><span>agla %s</span></a>' % (nx2 or "\u2014")),
        "room": ('<a class="mi" href="/finance/slips?s=room"><b>X-ray room work</b><span class="%s">%d baaki</span></a>'
                 % ("hot" if room_n else "", room_n)),
        "blood": ('<a class="mi" href="/finance/slips/blood"><b>Blood test</b><span class="%s">%s</span></a>'
                  % ("hot" if blood_n else "", ("%d report nahi aaye" % blood_n) if blood_n else "chamber se")),
        "pend": '<a class="mi" href="/finance/slips/pending"><b>Report baaki</b><span>blood \u00b7 X-ray</span></a>',
        "list": ('<a class="mi" href="/finance/slips?s=list"><b>Aaj ki list</b><span class="%s">%d parchi%s</span></a>'
                 % ("hot" if miss_n else "", today_n, (" \u00b7 %d chhoote" % miss_n) if miss_n else "")),
    }
    if user == "awdhesh":
        order = ["room", "xp", "opd", "blood", "pend", "list"]
    elif user in ("alisha", "shivani"):
        order = ["opd", "xp", "blood", "pend", "room", "list"]
    else:
        order = ["opd", "xp", "blood", "room", "pend", "list"]
    out = ['<nav class="menu">'] + [items[k] for k in order]
    if "checker" in _roles(u) or user == "shavez":
        out.append('<a class="mi" href="/finance/slips/report"><b>Report</b><span>Docterz se milaan</span></a>')
    out.append('<a class="mi small" href="/finance/slips?s=book"><b>Start new book</b><span>book khatam hone par</span></a></nav>')
    return "".join(out)


def _items_of(con, sid):
    return [dict(r) for r in con.execute("SELECT * FROM slip_item WHERE slip_id=? ORDER BY sort", (sid,))]


def _gap_ok():
    return ('<label class="chk gapok" hidden><input type="checkbox" name="gap_ok" value="1"> Haan, yahi number</label>')


def _sec(key, title, badge, body):
    return ('<details class="sec" name="sec" id="%s"><summary><span>%s</span><span class="badge">%s</span></summary>'
            '<div class="body">%s</div></details>' % (key, _esc(title), _esc(badge), body))


_TILE_JS = r"""<script>
(function(){
  var secs=[].slice.call(document.querySelectorAll('details.sec'));
  secs.forEach(function(d){d.addEventListener('toggle',function(){
    if(d.open){secs.forEach(function(o){if(o!==d)o.open=false;});}});});
  var h=location.hash.replace('#','');
  if(h){var t=document.getElementById(h);if(t&&t.tagName==='DETAILS'){t.open=true;}}
  var err=document.querySelector('.bad');
  if(err){var m=err.textContent;
    if(/Haan, yahi number/.test(m)){[].forEach.call(document.querySelectorAll('.gapok'),function(e){e.hidden=false;});}
    if(/ID sahi hai/.test(m)){[].forEach.call(document.querySelectorAll('.idok'),function(e){e.hidden=false;});}}
  [].forEach.call(document.querySelectorAll('form.slipf'),function(f){
    var cid=f.querySelector('.cidin'),who=f.querySelector('.who'),noid=f.querySelector('.noid'),
        nm=f.querySelector('.nonm'),pick=f.querySelector('.pick'),timer;
    function look(){var v=(cid.value||'').trim();who.textContent='';who.className='who';
      if(!v)return;
      fetch('/finance/slips/api/patient?id='+encodeURIComponent(v),{credentials:'same-origin'})
      .then(function(r){return r.json();}).then(function(j){
        if(!j.ok)return;
        if(j.known){who.textContent=j.name+(j.last4?'  · ••••'+j.last4:'')+(j.new?'  · NAYA':'');who.className=j.new?'who new':'who known';}
        else if(j.far){who.textContent='Yeh ID bahut aage hai (sabse bada '+j.highest+') — dobara dekhein';who.className='who far';}
        else if(j.old){who.textContent='Purana mareez \u2014 naam raat ko Docterz se aayega';who.className='who known';}
        else{who.textContent='NAYA — aaj ka naya mareez (naam raat ko aayega)';who.className='who new';}
      }).catch(function(){});}
    if(cid){cid.addEventListener('input',function(){clearTimeout(timer);timer=setTimeout(look,350);});
      if(pick){cid.addEventListener('input',function(){if(cid.value)pick.value='';});}}
    if(pick){pick.addEventListener('change',function(){if(pick.value){cid.value='';who.textContent='';}});}
    if(noid){noid.addEventListener('change',function(){nm.hidden=!noid.checked;
      if(cid)cid.disabled=noid.checked;if(pick)pick.disabled=noid.checked;if(noid.checked)nm.focus();});}
    [].forEach.call(f.querySelectorAll('.irow'),function(r){
      var s=r.querySelector('.svc'),sd=r.querySelector('.side'),o=r.querySelector('.oth'),ds=r.querySelector('.disc');
      s.addEventListener('change',function(){var op=s.options[s.selectedIndex];
        if(ds){ds.hidden=(!s.value||s.value==='other');if(ds.hidden)ds.value='';}
        sd.hidden=!(op&&(op.getAttribute('data-side')==='1'||s.value==='other'));
        o.hidden=(s.value!=='other');if(sd.hidden)sd.value='';});});
    [].forEach.call(f.querySelectorAll('.more'),function(b){b.addEventListener('click',function(){
      var nxt=f.querySelector('.irow[data-kind="'+b.getAttribute('data-kind')+'"][hidden]');
      if(nxt){nxt.hidden=false;}if(!f.querySelector('.irow[data-kind="'+b.getAttribute('data-kind')+'"][hidden]'))b.hidden=true;});});
  });
  [].forEach.call(document.querySelectorAll('form.vf'),function(f){f.addEventListener('submit',function(e){
    var b=e.submitter;if(b&&b.value==='void'&&!confirm('Yeh parchi hatayein?'))e.preventDefault();});});
})();
</script>"""


def _report_html(con, m, u):
    day = m["day"]
    prev = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    nxt = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
    out = ['<p class="nav"><a href="/finance/slips/report/%s">← %s</a> · <b>%s</b> · '
           '<a href="/finance/slips/report/%s">%s →</a> · <a href="/finance/slips?tile=1">open the tile</a></p>'
           % (prev, _dmy(prev)[:6], _dmy(day), nxt, _dmy(nxt)[:6])]
    try:
        orders = blood_state(con)[0]
        nt = [dict(r) for r in con.execute("SELECT * FROM blood_order WHERE state='ok' AND outcome='not_tested' "
                                            "AND day>=? ORDER BY day", ((dt.date.fromisoformat(_today()) - dt.timedelta(days=14)).isoformat(),))]
    except Exception:                                    # noqa: BLE001
        orders, nt = [], []
    lm = [o for o in orders if o["outcome"] == "lab_missed"]
    un = [o for o in orders if not o["outcome"]]
    if nt or lm or un:
        def li(o):
            return "<li>%s \u00b7 %s %s</li>" % (_dmy(o["day"])[:6], _esc(o["clinic_id"]),
                                                 _esc(o.get("name") or o.get("name_seen") or ""))
        body = ""
        if nt:
            body += "<p><b>Took the blood-test slip, never got tested</b> (last 14 days)</p><ul>%s</ul>" % "".join(li(o) for o in nt)
        if lm:
            body += "<p><b>Sample given, the lab has not e-mailed the report</b></p><ul>%s</ul>" % "".join(li(o) for o in lm)
        if un:
            body += "<p><b>No report yet, reception has not answered</b></p><ul>%s</ul>" % "".join(li(o) for o in un)
        out.append('<details class="sec"><summary><span>Blood tests to follow up</span><span class="badge red">%d</span>'
                   '</summary><div class="body">%s</div></details>' % (len(nt) + len(lm) + len(un), body))
    if m["arrived"] is None:
        out.append('<div class="rem">The Docterz export for %s has not arrived yet. Slips are listed; '
                   'the match runs as soon as it does.</div>' % _dmy(day))
    else:
        out.append('<p class="sm">Docterz export taken %s. Usual consultation fee: %s. This report runs '
                   'alongside the current end-of-day report.</p>' % (_esc(m["arrived"]), _rs(m["fee"])))
    fl = m["flags"]
    out.append('<details class="sec" open><summary><span>Needs a look</span><span class="badge%s">%d</span></summary>'
               '<div class="body">%s</div></details>' % (
                   " red" if fl else "", len(fl),
                   "<ul>%s</ul>" % "".join("<li>%s</li>" % _esc(f) for f in fl) if fl else
                   '<p>Nothing — every slip matches Docterz.</p>'))

    def table(rows, xp):
        h = ['<div class="tw"><table class="grid"><tr><th>Slip</th><th>ID</th><th>Name</th>%s<th>Docterz</th>'
             '%s<th></th></tr>' % ("<th>Items</th>" if xp else "", "<th>Room</th>" if xp else "")]
        for r in rows:
            s = r["slip"]
            if s["state"] != "ok":
                h.append('<tr class="dim"><td>%d</td><td colspan="%d">%s</td></tr>'
                         % (s["slip_no"], 6 if xp else 4, {"missing": "skipped — no reason given",
                                                          "cancelled": "cancelled", "spoilt": "spoilt"}[s["state"]]))
                continue
            chip = {"matched": '<span class="chip ok">MATCHED</span>', "check": '<span class="chip ck">CHECK</span>',
                    "waiting": '<span class="chip wt">WAITING</span>'}.get(r["verdict"], "")
            newc = ' <span class="chip nw">NEW</span>' if s["is_new"] else ""
            room = ""
            if xp:
                room = "<td>%s · %s</td>" % ((s["paid_mode"] or "—").upper(), "done" if s["done_at"] else "—")
            h.append('<tr><td>%d</td><td>%s</td><td>%s%s</td>%s<td>%s</td>%s<td>%s%s</td></tr>' % (
                s["slip_no"], _esc(s["clinic_id"] or "—"), _esc(r["name"] or "—"), newc,
                ("<td>%s</td>" % _esc(_items_label(s["items"]))) if xp else "", _esc(r["docterz"] or "—"),
                room, chip, ("<br><span class=\"sm\">%s</span>" % _esc("; ".join(r["why"]))) if r["why"] else ""))
        h.append("</table></div>")
        return "".join(h)

    out.append('<details class="sec"><summary><span>OPD — slip order</span><span class="badge">%d</span></summary>'
               '<div class="body">%s</div></details>' % (len(m["opd"]), table(m["opd"], False) if m["opd"] else
                                                          '<p class="sm">No OPD slips.</p>'))
    out.append('<details class="sec"><summary><span>X-ray &amp; Procedures — slip order</span><span class="badge">%d</span>'
               '</summary><div class="body">%s</div></details>' % (len(m["xp"]), table(m["xp"], True) if m["xp"] else
                                                                    '<p class="sm">No X-ray/procedure slips.</p>'))
    if m["orphans"]:
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            _esc(ln["section"]), _esc(ln["clinic_id"] or "—"), _esc(ln["patient"] or "—"),
            _rs(ln["amount_p"]), _esc(_mode_word(ln["mode"]))) for ln in m["orphans"])
        out.append('<details class="sec"><summary><span>Docterz entries with no slip</span><span class="badge red">%d</span>'
                   '</summary><div class="body"><div class="tw"><table class="grid"><tr><th>Head</th><th>ID</th><th>Name</th>'
                   '<th>Amount</th><th>Mode</th></tr>%s</table></div></div></details>' % (len(m["orphans"]), rows))
    out.append(_TILE_JS.replace("form.slipf", "form.none"))
    return "".join(out)


def _shell(title, body, lang, back="/portal", back_label="\u2190 Portal"):
    return """<!doctype html><html lang="%s"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#46525b;--line:#9fb0bb;--accent:#14456e;--paper:#fff;--bg:#e4eaee;--entry:#fffbe6;
 --ok:#2c6e2f;--okbg:#dff0d8;--bad:#9c2a20;--badbg:#fadbd8;--warn:#8a5a00;--warnbg:#fdf0d5}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.45 "Segoe UI",system-ui,-apple-system,sans-serif}
.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:10px;background:var(--accent);color:#fff;
 padding:8px 12px;padding-top:calc(8px + env(safe-area-inset-top,0px))}
.top a.back{color:#fff;text-decoration:none;font-weight:600;border:2px solid #fff;border-radius:8px;padding:8px 12px;white-space:nowrap;min-height:44px;display:inline-flex;align-items:center}
.top h1{font-size:17px;margin:0;line-height:1.2;flex:1}.top .d{font-size:14px;opacity:.85;white-space:nowrap}
main{padding:10px 10px 24px;max-width:760px;margin:0 auto}
details.sec{background:var(--paper);border:2px solid var(--line);border-radius:10px;margin:0 0 8px}
details.sec>summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;
 padding:10px 12px;font-weight:700;color:var(--accent);font-size:17px}
details.sec>summary::-webkit-details-marker{display:none}
details.sec>summary::after{content:"\\25BE";margin-left:8px}details.sec[open]>summary::after{content:"\\25B4"}
details.sec[open]>summary{border-bottom:1px solid var(--line)}
.body{padding:10px 12px}
.badge:empty{display:none}.badge{font-size:13px;font-weight:600;color:var(--mut);background:#eef2f4;border-radius:12px;padding:2px 9px;margin-left:auto}
.badge.red{color:#fff;background:var(--bad)}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin:0 0 8px}
.row label{display:flex;flex-direction:column;font-size:13px;color:var(--mut);gap:2px;flex:1;min-width:120px}
input,select{font:inherit;font-size:17px;min-height:44px;padding:6px 8px;border:2px solid #6b7b86;border-radius:8px;background:var(--entry);max-width:100%%}
input.no{font-weight:700;color:var(--accent);font-size:20px;width:100%%}
.pick{flex:1 1 100%%}.or{font-size:13px;color:var(--mut);flex:1 1 100%%;margin:-4px 0 -4px}.pat .cid{flex:1 1 100%%}
.small{align-items:center}.chk{flex-direction:row!important;align-items:center;gap:6px!important;font-size:15px!important;color:var(--ink)!important;flex:0 0 auto!important;min-width:0!important}
.chk{min-height:44px}.chk input{min-height:0;width:24px;height:24px}
.nonm{flex:1}
.who:empty{display:none}.who{font-weight:600;font-size:15px;margin:-2px 0 6px}.who.known{color:var(--ok)}.who.new{color:var(--warn)}.who.far{color:var(--bad)}
.lists{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}
@media(max-width:520px){.lists{grid-template-columns:1fr}}
.lst b{display:block;font-size:14px;color:var(--mut);margin-bottom:3px}
.irow{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px}.irow .svc{flex:1;min-width:0}.irow .side{width:78px}.irow .oth{flex:1 1 100%%}
button{font:inherit;cursor:pointer}
button.go{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:11px 24px;font-size:18px;font-weight:700;width:100%%}
button.more{background:none;border:1px dashed var(--accent);color:var(--accent);border-radius:8px;padding:8px 12px;font-size:15px;min-height:40px}
.rrow{display:flex;gap:8px;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid #e1e7eb}
.rrow.old .rl{color:var(--warn)}.rl{flex:1;min-width:0}.amt{font-weight:700;white-space:nowrap;font-size:15px;color:var(--ink);background:#eef2f4;border-radius:7px;padding:4px 8px}.rl{font-size:15px}.rb{display:flex;gap:4px;flex:0 0 auto}
.rb button{min-width:56px;min-height:44px;border:2px solid var(--accent);background:#fff;color:var(--accent);border-radius:8px;font-size:14px;font-weight:600}
.rb button.on{background:var(--ok);border-color:var(--ok);color:#fff}
.lrow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:6px 0;border-bottom:1px solid #e1e7eb;font-size:15px}
.lrow.miss{background:var(--warnbg)}.vf{display:flex;gap:4px;margin-left:auto}.vf input{min-height:34px;width:90px;font-size:14px}
.vf button{border:1px solid var(--line);background:#fff;border-radius:7px;padding:8px 10px;font-size:14px;min-height:40px}.vf button.x{color:var(--bad);border-color:var(--bad)}
.no{font-family:ui-monospace,Consolas,monospace;font-weight:700;color:var(--accent)}
h3{font-size:15px;margin:8px 0 2px;color:var(--mut)}
.sm{font-size:13px;color:var(--mut)}
.ok{background:var(--okbg);border-left:6px solid var(--ok);padding:8px 12px;margin-bottom:8px;border-radius:6px}
.bad{background:var(--badbg);border-left:6px solid var(--bad);padding:8px 12px;margin-bottom:8px;border-radius:6px}
.rem{background:var(--warnbg);border-left:6px solid var(--warn);padding:8px 12px;margin-bottom:8px;border-radius:6px;font-size:15px}
.warn{color:var(--warn);font-weight:600;margin:0 0 6px}
.bookf .row label{min-width:100px}.bookf button.go{width:auto}
.tw{overflow-x:auto}table.grid{border-collapse:collapse;width:100%%;font-size:14px}
.grid th,.grid td{border:1px solid #cbd6dd;padding:5px 7px;text-align:left;vertical-align:top}.grid th{background:#eef2f4}
tr.dim td{color:#7b8790;font-style:italic}
.chip{font-size:11px;font-weight:700;padding:2px 6px;border-radius:9px;white-space:nowrap}
.chip.ok{background:var(--okbg);color:var(--ok)}.chip.ck{background:var(--badbg);color:var(--bad)}.chip.wt{background:#eef2f4;color:var(--mut)}
.chip.nw{background:var(--warnbg);color:var(--warn)}
.nav{font-size:15px}
.menu{display:flex;flex-direction:column;gap:10px}
a.mi{display:flex;justify-content:space-between;align-items:center;gap:10px;min-height:64px;padding:12px 16px;background:var(--paper);
 border:2px solid var(--accent);border-radius:12px;color:var(--accent);text-decoration:none;font-size:19px}
a.mi span{font-size:14px;color:var(--mut);font-weight:600;white-space:nowrap}a.mi span.hot{color:#fff;background:var(--bad);border-radius:12px;padding:3px 10px}
a.mi.small{min-height:48px;font-size:16px;border-style:dashed}ul{margin:0;padding-left:1.2em}li{margin:3px 0}
</style></head><body><header class="top"><a class="back" href="%s">%s</a><h1>%s</h1><span class="d">%s</span></header>
<main>%s</main></body></html>""" % (lang, _esc(title), _esc(back), _esc(back_label), _esc(title), _dmy(_today())[:6], body)


# ================================================================ S328 -- the EMR upload list (reception)
# THE OWNER, 19-Sep-2026: every X-ray is saved on the X-ray PC and carried by pen drive to the reception
# PC, where reception opens the patient in the doctor's EMR (Docterz) and uploads it into that patient's
# record. The next afternoon they upload the previous evening's and that morning's X-rays; any backlog
# must stay visible. "So everybody knows which are pending and which are done."
# Pathology reports (from the in-house lab, by e-mail) join this same list later as kind 'path'.
EMR_FROM = os.environ.get("EMR_UPLOAD_FROM", "2026-09-18")
EMR_SCHEMA = """
CREATE TABLE IF NOT EXISTS emr_upload (
  key          TEXT PRIMARY KEY,
  kind         TEXT NOT NULL DEFAULT 'xray' CHECK (kind IN ('xray','path')),
  day          TEXT NOT NULL,
  clinic_id    TEXT NOT NULL DEFAULT '',
  uploaded_by  TEXT NOT NULL DEFAULT '',
  uploaded_at  TEXT NOT NULL DEFAULT '',
  note         TEXT NOT NULL DEFAULT ''
);
"""
_emr_done = False


def emr_ensure(con):
    global _emr_done
    if not _emr_done:
        con.executescript(EMR_SCHEMA)
        con.commit()
        _emr_done = True


def _session_of(hhmm):
    try:
        return "Subah" if int((hhmm or "00")[:2]) < 15 else "Shaam"
    except ValueError:
        return ""


@bp.route("/finance/slips/emr")
def emr_page():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return _shell("EMR upload", _denied(), "en")
    return redirect("/finance/slips/blood", code=303)     # S379: retired -- X-rays are filed by themselves (S374)


@bp.route("/finance/slips/emr/mark", methods=["POST"])
def emr_mark():
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    return redirect("/finance/slips", code=303)           # S379: retired


def _blood_open_html(orders):
    """S330: orders from before today with no report -- answered once, at upload time, never during OPD."""
    if not orders:
        return ""
    ask = [o for o in orders if not o["outcome"]]
    rows = []
    for o in orders:
        if o["outcome"] == "lab_missed":
            act = ('<span class="sm">lab ko email bhejne ko kahein</span><form method="post" action="/finance/slips/blood/outcome" '
                   'class="vf"><input type="hidden" name="id" value="%d"><button name="act" value="undo" class="x">wapas</button></form>' % o["id"])
        else:
            act = ('<form method="post" action="/finance/slips/blood/outcome" class="rb"><input type="hidden" name="id" value="%d">'
                   '<button name="act" value="not_tested">Test nahi karaya</button>'
                   '<button name="act" value="lab_missed">Sample diya, email nahi aaya</button></form>' % o["id"])
        rows.append('<div class="lrow"><div class="rl"><span class="no">%s</span> %s<br><span class="sm">blood test \u00b7 %s</span></div>%s</div>'
                    % (_esc(o["clinic_id"]), _esc(o["name"] or ""), _dmy(o["day"])[:6], act))
    sec = _sec("blood", "Blood report nahi aaya", "%d" % len(ask) if ask else "%d lab" % len(orders),
               '<p class="sm">Pathology register dekh kar batayein.</p>' + "".join(rows))
    if ask:
        sec = sec.replace('<details class="sec"', '<details class="sec" open', 1).replace('class="badge"', 'class="badge red"', 1)
    return sec


# ================================================================ S330 -- blood tests (owner, 19-Sep-2026)
# THE FLOW HE SET. The chamber logs "blood test ordered" for a patient -- two taps, no test names. The
# in-house lab (NK Pathology) e-mails each report to the clinic Gmail with the clinic ID in the subject
# ("Your Report  MRS. <name> ( 8118)"); a small Apps Script in that mailbox tells this server "report for
# ID 8118 arrived" -- the ID and the time only, never the name or the file. The report then sits in
# reception's upload list beside the X-rays. NOTHING is asked of reception during patient flow: at
# upload time (the next afternoon) an order with no report shows two buttons -- "Test nahi karaya"
# (the patient took the slip and never got tested) or "Sample diya, email nahi aaya" (the lab missed
# sending it; the lab sends by hand from its software). A report that arrives later closes it by itself.
import hmac as _hmac

BLOOD_SCHEMA = """
CREATE TABLE IF NOT EXISTS blood_order (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  day         TEXT NOT NULL,
  clinic_id   TEXT NOT NULL,
  name_seen   TEXT NOT NULL DEFAULT '',
  state       TEXT NOT NULL DEFAULT 'ok' CHECK (state IN ('ok','void')),
  outcome     TEXT NOT NULL DEFAULT '' CHECK (outcome IN ('','not_tested','lab_missed')),
  outcome_by  TEXT NOT NULL DEFAULT '',
  outcome_at  TEXT NOT NULL DEFAULT '',
  logged_by   TEXT NOT NULL DEFAULT '',
  logged_at   TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS blood_order_live ON blood_order(day, clinic_id) WHERE state='ok';
CREATE TABLE IF NOT EXISTS lab_report (
  msg_id      TEXT PRIMARY KEY,
  clinic_id   TEXT NOT NULL,
  received_at TEXT NOT NULL,
  pushed_at   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS lab_report_cid ON lab_report(clinic_id, received_at);
"""
_blood_done = False
LAB_WINDOW_DAYS = 7


def blood_ensure(con):
    global _blood_done
    if not _blood_done:
        con.executescript(BLOOD_SCHEMA)
        con.commit()
        _blood_done = True


def _report_for(con, cid, day):
    """The first lab report for this ID on or after the order day (within a week), or None."""
    end = (dt.date.fromisoformat(day) + dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat() + " 23:59:59"
    return con.execute("SELECT * FROM lab_report WHERE clinic_id=? AND received_at>=? AND received_at<=? "
                       "ORDER BY received_at LIMIT 1", (cid, day, end)).fetchone()


def blood_state(con):
    """(open_orders, lab_items): orders from before today with no report, and one upload line per
    patient per report-day (a report the lab re-sends is still one upload)."""
    ensure(con)
    blood_ensure(con)
    today = _today()
    orders = []
    for o in con.execute("SELECT * FROM blood_order WHERE state='ok' AND day>=? ORDER BY day, id", (EMR_FROM,)):
        o = dict(o)
        o["report"] = _report_for(con, o["clinic_id"], o["day"]) is not None
        o["name"] = o["name_seen"] or ((patient(con, o["clinic_id"]) or ("", ""))[0])
        if not o["report"] and o["day"] < today and o["outcome"] != "not_tested":
            orders.append(o)
    done = {r["key"]: dict(r) for r in con.execute("SELECT * FROM emr_upload WHERE kind='path'")}
    items = []
    for r in con.execute("SELECT clinic_id, substr(received_at,1,10) d, MIN(received_at) t, COUNT(*) n FROM lab_report "
                         "WHERE substr(received_at,1,10)>=? GROUP BY clinic_id, substr(received_at,1,10) ORDER BY d",
                         (EMR_FROM,)):
        key = "lr:%s:%s" % (r["d"], r["clinic_id"])
        items.append({"key": key, "done_key": key if done.get(key) else "", "kind": "path", "day": r["d"],
                      "session": _session_of((r["t"] or "")[11:13]), "clinic_id": r["clinic_id"],
                      "name": (patient(con, r["clinic_id"]) or ("", ""))[0], "what": "Blood report",
                      "slip_no": None, "done": done.get(key)})
    return orders, items


@bp.route("/finance/slips/blood", methods=["GET", "POST"])
def blood_page():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return _shell("Blood test", _denied(), "en")
    con = _db()
    ensure(con)
    blood_ensure(con)
    msg_ok, msg_err = "", ""
    if request.method == "POST":
        if "maker" not in _roles(u):
            return jsonify(ok=False, error="not_permitted"), 403
        f = request.form
        if f.get("act") == "void":
            oid = _int(f.get("id"))
            r = con.execute("SELECT * FROM blood_order WHERE id=? AND state='ok'", (oid,)).fetchone()
            if r:
                con.execute("UPDATE blood_order SET state='void' WHERE id=?", (oid,))
                _audit_safe(con, oid, "blood_void", None, None, _who(u))
                con.commit()
                msg_ok = "Hata diya."
        else:
            cid = _clean_id(f.get("clinic_id") or f.get("pick"))
            if not cid:
                msg_err = "Mareez chunein ya clinic ID likhein."
            else:
                day = _today()
                if con.execute("SELECT 1 FROM blood_order WHERE day=? AND clinic_id=? AND state='ok'", (day, cid)).fetchone():
                    msg_err = "ID %s ka blood test aaj pehle se likha hai." % cid
                else:
                    p = patient(con, cid)
                    c = con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                                    (day, cid, p[0] if p else "", _who(u), _stamp()))
                    _audit_safe(con, c.lastrowid, "blood_order", None, json.dumps({"cid": cid}), _who(u))
                    con.commit()
                    msg_ok = "Blood test likh diya: %s%s" % (cid, (" · " + p[0]) if p else "")
    today = _today()
    opd = [s for s in day_slips(con, today, "opd") if s["state"] == "ok" and s["clinic_id"]]
    mine = [dict(r) for r in con.execute("SELECT * FROM blood_order WHERE day=? AND state='ok' ORDER BY id", (today,))]
    got = {r["clinic_id"] for r in mine}
    o = ['<option value="">— aaj ke OPD se chunein —</option>']
    seen = set()
    for s in reversed(opd):
        if s["clinic_id"] in seen or s["clinic_id"] in got:
            continue
        seen.add(s["clinic_id"])
        o.append('<option value="%s">%s</option>' % (_esc(s["clinic_id"]), _esc(_who_label(s))))
    body = []
    if msg_ok:
        body.append('<div class="ok">%s</div>' % _esc(msg_ok))
    if msg_err:
        body.append('<div class="bad">%s</div>' % _esc(msg_err))
    body.append('<form method="post" action="/finance/slips/blood" class="slipf"><div class="row pat">'
                '<select name="pick" class="pick">%s</select><span class="or">ya</span>'
                '<label class="cid">Clinic ID<input name="clinic_id" inputmode="numeric" autocomplete="off" class="cidin"></label></div>'
                '<div class="who" aria-live="polite"></div><button class="go">Blood test likhein</button></form>' % "".join(o))
    li = "".join('<div class="lrow"><span class="no">%s</span> %s <span class="sm">%s</span>'
                 '<form method="post" action="/finance/slips/blood" class="vf"><input type="hidden" name="id" value="%d">'
                 '<button name="act" value="void" class="x">Hatao</button></form></div>'
                 % (_esc(r["clinic_id"]), _esc(r["name_seen"] or ""), _esc((r["logged_at"] or "")[11:16]), r["id"]) for r in mine)
    body.append(_sec("bl", "Aaj ke blood test", "%d" % len(mine), li or '<p class="sm">Abhi koi nahi.</p>'))
    try:                                                  # S379: moved here from the retired Docterz upload screen
        body.append(_blood_open_html(blood_state(con)[0]))
    except Exception:                                    # noqa: BLE001
        pass
    body.append(_TILE_JS)
    return _shell("Blood test", "".join(body), "hi", back="/finance/slips", back_label="← Menu")


@bp.route("/finance/slips/blood/outcome", methods=["POST"])
def blood_outcome():
    """At UPLOAD time only (the owner): an order with no report is answered once."""
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    ensure(con)
    blood_ensure(con)
    oid, act = _int(request.form.get("id")), request.form.get("act")
    r = con.execute("SELECT * FROM blood_order WHERE id=? AND state='ok'", (oid,)).fetchone()
    if r and act in ("not_tested", "lab_missed", "undo"):
        val = "" if act == "undo" else act
        con.execute("UPDATE blood_order SET outcome=?, outcome_by=?, outcome_at=? WHERE id=?",
                    (val, _who(u) if val else "", _stamp() if val else "", oid))
        _audit_safe(con, oid, "blood_outcome_" + act, json.dumps({"was": r["outcome"]}), None, _who(u))
        con.commit()
    return redirect("/finance/slips/blood", code=303)     # S379: the questions live on Blood test now


@bp.route("/finance/slips/api/lab-report", methods=["POST"])
def api_lab_report():
    """The clinic mailbox's Apps Script tells us a lab report arrived: message id, clinic ID, time.
    Key-checked with the same cron token the other Gmail pushes use (FINANCE_CRON_TOKEN)."""
    tok = os.environ.get("FINANCE_CRON_TOKEN", "")
    given = request.headers.get("X-Finance-Cron", "")
    if not (tok and given and _hmac.compare_digest(str(given), str(tok))):
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    rows = j.get("reports") if isinstance(j.get("reports"), list) else [j]
    con = _db()
    ensure(con)
    blood_ensure(con)
    n = 0
    for x in rows[:200]:
        mid = str(x.get("msg_id") or "")[:64]
        cid = _clean_id(x.get("clinic_id"))
        at = str(x.get("received_at") or "")[:19]
        if not (mid and cid and re.fullmatch(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?", at)):
            continue
        n += con.execute("INSERT OR IGNORE INTO lab_report(msg_id, clinic_id, received_at, pushed_at) VALUES (?,?,?,?)",
                         (mid, cid, at.replace("T", " "), _stamp())).rowcount
    con.commit()
    return jsonify(ok=True, stored=n)


# ================================================================ S382 -- "Report baaki": blood and X-ray reports pending
# THE OWNER, 24-Sep-2026: "There are many pathology reports which are not being mailed from the pathology desk, so we
# need a system for this to be tracked and a list ... where they can see what all reports are pending -- the date,
# clinic ID and patient name, three fields compulsory ... Sukhveer ... this tile ... the same tile with both the
# receptionists and Shavez ... similar flow for the X-ray work ... they tap when they mail ... any discrepancy is
# also flagged." His rulings on the plan: a blood report is late at the end of the same day (next morning for a test
# taken after 5 pm); "+ Naya" (a walk-in test) is reception's; Sukhveer is already on the staff list.
#
# Nothing new is typed except a missing name. Everything else is a tap, and a report that ARRIVES clears its own line
# (the lab's e-mail is caught by the mailbox script, the X-ray photo is filed by it). The taps also answer the same
# item in Check karein (record_check), so reception is never asked the same thing twice.
PEND_XRAY_FROM = os.environ.get("PEND_XRAY_FROM", "2026-09-23")    # the X-ray live filing began (S374)
PEND_BLOOD_DAYS = 14          # a blood order older than this leaves the list (Check karein keeps asking)
MAIL_WAIT_HOURS = 3           # after "Mail kar diya", this long for the e-mail to arrive
XRAY_WAIT_MIN = 60            # after "File daal di", this long for the mailbox run to file it
ORPHAN_DAYS = 7               # a report with no order is shown this many days
_pend_done = False


def pend_ensure(con):
    global _pend_done
    ensure(con)
    blood_ensure(con)
    if _pend_done:
        return
    have = {r[1] for r in con.execute("PRAGMA table_info(blood_order)")}
    for col in ("mailed_by", "mailed_at", "later_until", "name_by"):
        if col not in have:
            con.execute("ALTER TABLE blood_order ADD COLUMN %s TEXT NOT NULL DEFAULT ''" % col)
    con.executescript("""
CREATE TABLE IF NOT EXISTS pend_mark (
  key       TEXT PRIMARY KEY,
  kind      TEXT NOT NULL,
  clinic_id TEXT NOT NULL DEFAULT '',
  day       TEXT NOT NULL DEFAULT '',
  act       TEXT NOT NULL DEFAULT '',
  by_user   TEXT NOT NULL DEFAULT '',
  at        TEXT NOT NULL DEFAULT ''
);""")
    con.commit()
    _pend_done = True


def _dtp(s):
    try:
        return dt.datetime.fromisoformat((s or "").replace("T", " ")[:19])
    except ValueError:
        return None


def blood_due(o):
    """The owner: late at the end of the same day; a test taken after 5 pm is late the next morning."""
    t = _dtp(o.get("logged_at")) or _dtp((o.get("day") or "") + " 12:00:00")
    if t is None:
        return None
    if t.hour >= 17:
        return dt.datetime.combine(t.date() + dt.timedelta(days=1), dt.time(11, 0))
    return dt.datetime.combine(t.date(), dt.time(23, 59))


def mail_wait(mailed_at):
    t = _dtp(mailed_at)
    if t is None:
        return None
    if t.hour >= 18:
        return dt.datetime.combine(t.date() + dt.timedelta(days=1), dt.time(11, 0))
    return t + dt.timedelta(hours=MAIL_WAIT_HOURS)


def _name_for(con, cid, seen=""):
    if seen:
        return seen
    p = patient(con, cid)
    return (p[0] if p else "") or ""


def _record_answer(con, key, kind, cid, answer, who, note=""):
    """Close (or quiet) the same item in Check karein -- records.py's table, same database. Never blocks."""
    try:
        con.execute("INSERT OR REPLACE INTO record_check(key, kind, clinic_id, answer, note, answered_by, answered_at) "
                    "VALUES (?,?,?,?,?,?,?)", (key, kind, cid, answer, note[:200], who, _stamp()))
    except Exception:                                    # noqa: BLE001 -- no records table on this box
        pass


def blood_pending(con):
    """(pending, arrived_recently, orphans). Each pending row: the three fields and its state in words."""
    pend_ensure(con)
    try:
        noid_sweep(con)                                  # S391
    except Exception:                                    # noqa: BLE001 -- never blocks the list
        pass
    now = _now()
    since = (now.date() - dt.timedelta(days=PEND_BLOOD_DAYS)).isoformat()
    pend, got = [], []
    for o in con.execute("SELECT * FROM blood_order WHERE state='ok' AND day>=? ORDER BY day, id", (since,)):
        o = dict(o)
        o["name"] = _name_for(con, o["clinic_id"], o.get("name_seen") or "")
        rep = _report_for(con, o["clinic_id"], o["day"])
        if rep is not None:
            o["received_at"] = rep["received_at"]
            o["msg_id"] = rep["msg_id"]
            got.append(o)
            continue
        if o["outcome"] == "not_tested":
            continue
        lu = o.get("later_until") or ""
        due = blood_due(o)
        st, word = "wait", "baaki"
        if lu and lu > now.date().isoformat():
            st, word = "later", "baad mein — %s tak" % _dmy(lu)[:6]
        elif o.get("mailed_at"):
            w = mail_wait(o["mailed_at"])
            if w and now > w:
                st, word = "nomail", "mail bheja %s, nahi aaya — dobara bhejein" % _hm(o["mailed_at"])
            else:
                st, word = "mailed", "mail bheja %s — aane ka intezaar" % _hm(o["mailed_at"])
        elif due and now > due:
            st, word = "late", "der ho gayi"
        o["st"], o["word"] = st, word
        pend.append(o)
    order = {"nomail": 0, "late": 1, "wait": 2, "mailed": 3, "later": 4}
    pend.sort(key=lambda o: (order[o["st"]], o["day"], o["id"]))
    # a report that arrived for an ID nobody wrote a test for -- walk-in, or a wrong ID on the report
    orphans = []
    rs = (now.date() - dt.timedelta(days=ORPHAN_DAYS)).isoformat()
    for r in con.execute("SELECT clinic_id, MIN(received_at) t FROM lab_report WHERE received_at>=? "
                         "GROUP BY clinic_id, substr(received_at,1,10) ORDER BY t", (rs,)):
        d = r["t"][:10]
        lo = (dt.date.fromisoformat(d) - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
        if con.execute("SELECT 1 FROM blood_order WHERE clinic_id=? AND state='ok' AND day BETWEEN ? AND ? LIMIT 1",
                       (r["clinic_id"], lo, d)).fetchone():
            continue
        key = "orph:%s:%s" % (d, r["clinic_id"])
        if con.execute("SELECT 1 FROM pend_mark WHERE key=?", (key,)).fetchone():
            continue
        orphans.append({"key": key, "day": d, "clinic_id": r["clinic_id"], "name": _name_for(con, r["clinic_id"]),
                        "t": r["t"]})
    got.sort(key=lambda o: o.get("received_at") or "", reverse=True)
    return pend, got, orphans


def xray_pending(con):
    """X-ray/Proc slips carrying an X-ray, from the live-filing day on, with no photo filed on the patient."""
    pend_ensure(con)
    now = _now()
    marks = {r["key"]: dict(r) for r in con.execute("SELECT * FROM pend_mark WHERE kind='xray'")}
    out = []
    for s in con.execute("SELECT * FROM slip WHERE series='xp' AND state='ok' AND day>=? AND clinic_id<>'' "
                         "ORDER BY day, slip_no", (PEND_XRAY_FROM,)):
        s = dict(s)
        its = [it for it in _items_of(con, s["id"]) if it["kind"] == "xray"]
        if not its:
            continue
        cid, day = s["clinic_id"], s["day"]
        try:
            if con.execute("SELECT 1 FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? AND day=? LIMIT 1",
                           (cid, day)).fetchone():
                continue
        except Exception:                                # noqa: BLE001 -- no records table: nothing is filed
            pass
        key = "xm:%s:%s" % (day, cid)
        m = marks.get(key)
        if m and m["act"] == "not_done":
            continue
        infold = False
        try:
            infold = bool(con.execute("SELECT 1 FROM xray_filing WHERE clinic_id=? AND day=? AND state IN ('planned','check') "
                                      "LIMIT 1", (cid, day)).fetchone())
        except Exception:                                # noqa: BLE001
            pass
        due = dt.datetime.combine(dt.date.fromisoformat(day) + dt.timedelta(days=1), dt.time(12, 0))
        st, word = "wait", "photo baaki"
        if infold:
            st, word = "mailed", "photo mil gayi — file ho rahi hai"
        elif m and m["act"] == "put":
            t = _dtp(m["at"])
            if t and now > t + dt.timedelta(minutes=XRAY_WAIT_MIN):
                st, word = "nomail", "%s ko daali, file nahi hui — naam / folder dekhein" % _hm(m["at"])
            else:
                st, word = "mailed", "%s ko daali — file hone ka intezaar" % _hm(m["at"])
        elif now > due:
            st, word = "late", "der ho gayi"
        if any(x["key"] == key for x in out):
            continue
        out.append({"key": key, "day": day, "clinic_id": cid, "slip_no": s["slip_no"],
                    "name": s.get("name_seen") or _name_for(con, cid), "what": _items_label(its), "st": st, "word": word})
    order = {"nomail": 0, "late": 1, "wait": 2, "mailed": 3}
    out.sort(key=lambda o: (order[o["st"]], o["day"], o["slip_no"]))
    return out


def _hm(s):
    return (s or "")[11:16]


# ---------------------------------------------------------------- S383: the name on the report against the ID's name
_NAME_STOP = {"mr", "mrs", "smt", "shri", "sri", "ms", "miss", "master", "baby", "dr", "km", "kumari", "md", "mohd",
              "mohammad", "mohammed", "devi", "kumar", "singh", "bee", "begum", "khan", "lal", "ram", "prasad", "chand", "kr"}


def _name_tokens(n):
    return [w for w in re.findall(r"[a-z]+", (n or "").lower()) if w not in _NAME_STOP and len(w) >= 3]


def same_name(a, b):
    """Generous on purpose: spelling varies (Hindi names written by two desks). Different only when no word of one
    is close to any word of the other and the whole names are not alike."""
    ta, tb = _name_tokens(a), _name_tokens(b)
    if not ta or not tb:
        return True
    for x in ta:
        for y in tb:
            if x == y or x[:4] == y[:4] or x in y or y in x:
                return True
    import difflib
    return difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio() >= 0.8


def name_mismatches(con):
    """Lab reports of the last week whose name (from the lab's e-mail subject, in the file name) is not the clinic ID's
    name -- the likeliest sign of a wrong ID on the report. One line per report file, until reception answers it."""
    pend_ensure(con)
    since = (_now().date() - dt.timedelta(days=ORPHAN_DAYS)).isoformat()
    out = []
    try:
        rows = con.execute("SELECT id, clinic_id, day, file_name FROM record_file WHERE kind='blood' AND state='ok' AND day>=? "
                           "ORDER BY day, id", (since,)).fetchall()
    except Exception:                                    # noqa: BLE001 -- no records table
        return out
    for r in rows:
        parts = [p.strip() for p in (r["file_name"] or "").split("\u00b7")]
        rep_name = parts[2] if len(parts) >= 4 else ""
        ours = _name_for(con, r["clinic_id"])
        if not rep_name or not ours or same_name(rep_name, ours):
            continue
        key = "nm:%d" % r["id"]
        if con.execute("SELECT 1 FROM pend_mark WHERE key=?", (key,)).fetchone():
            continue
        out.append({"key": key, "day": r["day"], "clinic_id": r["clinic_id"], "report_name": rep_name, "our_name": ours})
    return out


# ---------------------------------------------------------------- S391: a lab report e-mailed with NO clinic ID
# The lab's subject is normally "Your Report  MRS. <name> ( 8118)". When the ID is left out, the mailbox runs could not
# tell whose report it was and skipped it -- the line stayed "mail bheja" for ever and the PDF was never filed.
# Now the mailbox asks here: the report is joined to the ONE open blood order with the same name (a mailed one wins a
# tie; a re-send follows the first), and anything still unsure is shown to reception to pick. Never guessed.
_noid_done = False


def noid_ensure(con):
    global _noid_done
    pend_ensure(con)
    if _noid_done:
        return
    con.executescript("""
CREATE TABLE IF NOT EXISTS lab_noid (
  msg_id      TEXT PRIMARY KEY,
  name        TEXT NOT NULL DEFAULT '',
  received_at TEXT NOT NULL,
  clinic_id   TEXT NOT NULL DEFAULT '',
  how         TEXT NOT NULL DEFAULT '',
  by_user     TEXT NOT NULL DEFAULT '',
  at          TEXT NOT NULL DEFAULT '',
  pushed_at   TEXT NOT NULL DEFAULT ''
);""")
    con.commit()
    _noid_done = True


def _norm_name(n):
    return " ".join(_name_tokens(n))


def _name_hit(a, b):
    """Stricter than same_name (which forgives a shared first four letters, so SUNITA ~ Sunil): here a word of one must
    equal a word of the other, or be spelt nearly the same (Kavita/Kavitha). A name with no usable word matches nobody."""
    import difflib
    for x in _name_tokens(a):
        for y in _name_tokens(b):
            if x == y or (min(len(x), len(y)) >= 4 and difflib.SequenceMatcher(None, x, y).ratio() >= 0.8):
                return True
    return False


def open_orders_for(con, received_at):
    """Blood orders still waiting that a report received then could close (on or before that day, within the lab
    window _report_for uses), not 'test nahi hua'."""
    d = (received_at or "")[:10]
    lo = (dt.date.fromisoformat(d) - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
    out = []
    for o in con.execute("SELECT * FROM blood_order WHERE state='ok' AND day BETWEEN ? AND ? ORDER BY day, id", (lo, d)):
        o = dict(o)
        if o["outcome"] == "not_tested" or _report_for(con, o["clinic_id"], o["day"]) is not None:
            continue
        o["name"] = _name_for(con, o["clinic_id"], o.get("name_seen") or "")
        out.append(o)
    return out


def noid_match(con, name, received_at):
    """The clinic ID this ID-less report belongs to, or '' when it is not certain."""
    cands = [o for o in open_orders_for(con, received_at) if _name_hit(name, o["name"])]
    if len(cands) > 1:
        m = [o for o in cands if o.get("mailed_at")]
        if m:
            cands = m
    if len(cands) > 1:
        e = [o for o in cands if _norm_name(o["name"]) == _norm_name(name)]
        if e:
            cands = e
    if len({o["clinic_id"] for o in cands}) == 1:
        return cands[0]["clinic_id"]
    if not cands and _norm_name(name):
        # the same report sent more than once: follow the copy that found its patient -- EARLIER OR LATER (S392: the
        # mailbox reads newest first, so a resend can take the order before the original is looked at)
        d0 = dt.date.fromisoformat(received_at[:10])
        lo = (d0 - dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat()
        hi = (d0 + dt.timedelta(days=LAB_WINDOW_DAYS)).isoformat() + " 23:59:59"
        prev = {r["clinic_id"] for r in con.execute(
            "SELECT name, clinic_id FROM lab_noid WHERE clinic_id<>'' AND received_at>=? AND received_at<=?", (lo, hi))
            if _norm_name(r["name"]) == _norm_name(name)}
        if len(prev) == 1:
            return prev.pop()
    return ""


def noid_resolve(con, msg_id, cid, how, who=""):
    r = con.execute("SELECT received_at FROM lab_noid WHERE msg_id=?", (msg_id,)).fetchone()
    con.execute("UPDATE lab_noid SET clinic_id=?, how=?, by_user=?, at=? WHERE msg_id=?", (cid, how, who, _stamp(), msg_id))
    con.execute("INSERT OR IGNORE INTO lab_report(msg_id, clinic_id, received_at, pushed_at) VALUES (?,?,?,?)",
                (msg_id, cid, r["received_at"], _stamp()))


def noid_sweep(con):
    """Try again every ID-less report of the last week that is not placed yet (an order may have been written since)."""
    noid_ensure(con)
    since = (_now().date() - dt.timedelta(days=ORPHAN_DAYS)).isoformat()
    n = 0
    for r in con.execute("SELECT * FROM lab_noid WHERE clinic_id='' AND how='' AND received_at>=? ORDER BY received_at",
                         (since,)).fetchall():
        cid = noid_match(con, r["name"], r["received_at"])
        if cid:
            noid_resolve(con, r["msg_id"], cid, "auto")
            n += 1
    if n:
        con.commit()
    return n


def noid_pending(con):
    """ID-less reports of the last week that nobody could place yet -- reception picks."""
    noid_ensure(con)
    since = (_now().date() - dt.timedelta(days=ORPHAN_DAYS)).isoformat()
    return [dict(r) for r in con.execute("SELECT * FROM lab_noid WHERE clinic_id='' AND how='' AND received_at>=? "
                                          "ORDER BY received_at", (since,))]


def pending_counts(con):
    """For the doctors' one line: (blood pending, blood red, x-ray pending, x-ray red, reports with no order)."""
    try:
        b, _g, orph = blood_pending(con)
        x = xray_pending(con)
    except Exception:                                    # noqa: BLE001
        return None
    red = ("late", "nomail")
    try:
        nm = len(name_mismatches(con))
    except Exception:                                    # noqa: BLE001
        nm = 0
    try:
        nx = len(noid_pending(con))                      # S391
    except Exception:                                    # noqa: BLE001
        nx = 0
    return {"blood": len([o for o in b if o["st"] != "later"]), "blood_red": len([o for o in b if o["st"] in red]),
            "xray": len(x), "xray_red": len([o for o in x if o["st"] in red]), "orphans": len(orph), "name_mismatch": nm, "no_id": nx}


def _chip(st, word):
    cls = {"late": "ck", "nomail": "ck", "mailed": "wt", "later": "wt", "wait": "wt"}.get(st, "wt")
    return '<span class="chip %s">%s</span>' % (cls, _esc(word))


def _pend_blood_html(con, u, pend, got, orphans):
    roles = _roles(u)
    can_tap = bool(roles & {"maker", "viewer"})
    is_maker = "maker" in roles
    out = []
    rows = []
    for o in pend:
        three = '<span class="no">%s</span> <b>%s</b> <span class="sm">%s</span>' % (
            _esc(o["clinic_id"]), _esc(o["name"]) if o["name"] else '<span class="chip ck">naam nahi</span>', _dmy(o["day"])[:6])
        act = ""
        if can_tap:
            if not o["name"]:
                act += ('<form method="post" action="/finance/slips/pending/act" class="vf"><input type="hidden" name="key" value="b:%d">'
                        '<input name="name" placeholder="naam likhein" maxlength="60" required><button name="act" value="name">Save</button></form>'
                        % o["id"])
            else:
                act += ('<form method="post" action="/finance/slips/pending/act" class="rb"><input type="hidden" name="key" value="b:%d">'
                        '<button name="act" value="mailed">%s</button>'
                        '<button name="act" value="not_tested">Test nahi hua</button>'
                        '<button name="act" value="later">Baad mein</button></form>'
                        % (o["id"], "Dobara bheja" if o["st"] == "nomail" else "Mail kar diya"))
        rows.append('<div class="lrow%s"><div class="rl">%s<br>%s</div>%s</div>'
                    % (" miss" if o["st"] in ("late", "nomail") else "", three, _chip(o["st"], o["word"]), act))
    red = len([o for o in pend if o["st"] in ("late", "nomail")])
    hint = ('<p class="sm">Lab ko mail karte waqt naam ke baad clinic ID zaroor likhein, jaise <b>SITA ( 1234 )</b> — '
            'ID ho to report aate hi line yahan se apne aap hat jaati hai.</p>') if can_tap else ""
    sec = _sec("bp", "Blood report baaki", "%d%s" % (len(pend), (" · %d der" % red) if red else ""),
               hint + ("".join(rows) or '<p class="sm">Koi report baaki nahi. ✔</p>'))
    out.append(sec.replace('<details class="sec"', '<details class="sec" open', 1)
               .replace('class="badge"', 'class="badge red"' if red else 'class="badge"', 1))
    if is_maker:
        out.append(_sec("bn", "+ Naya blood test (bina chamber parchi)", "",
                        '<form method="post" action="/finance/slips/pending/new" class="slipf"><div class="row pat">'
                        '<label class="cid">Clinic ID<input name="clinic_id" inputmode="numeric" autocomplete="off" class="cidin" required></label></div>'
                        '<div class="who" aria-live="polite"></div>'
                        '<div class="row"><label>Naam (ID se na aaye to)<input name="name" maxlength="60"></label></div>'
                        '<button class="go">Likhein</button></form>'))
    try:
        nxs = noid_pending(con)                          # S391
    except Exception:                                    # noqa: BLE001
        nxs = []
    if nxs:
        li = []
        for r in nxs:
            act = ""
            if can_tap:
                oo = open_orders_for(con, r["received_at"])
                oo.sort(key=lambda o: (not same_name(r["name"], o["name"]) or not _name_tokens(o["name"]), o["day"], o["id"]))
                opts = "".join('<option value="%s">%s · %s · %s</option>' % (_esc(o["clinic_id"]), _esc(o["clinic_id"]),
                               _esc(o["name"] or "—"), _dmy(o["day"])[:6]) for o in oo)
                act = ('<form method="post" action="/finance/slips/pending/act" class="rb"><input type="hidden" name="key" value="nx:%s">'
                       '<select name="cid"><option value="">— kaun hai? —</option>%s</select>'
                       '<input name="cid2" inputmode="numeric" maxlength="12" placeholder="ya ID likhein">'
                       '<button name="act" value="noid_pick">Yahi hai</button>'
                       '<button name="act" value="noid_gone">Hamara nahi</button></form>' % (_esc(r["msg_id"]), opts))
            li.append('<div class="lrow miss"><div class="rl"><b>%s</b> <span class="sm">report %s</span>'
                      '<br><span class="chip ck">ID nahi likha</span></div>%s</div>'
                      % (_esc(r["name"] or "—"), _esc(_dmy(r["received_at"][:10])[:6] + " " + _hm(r["received_at"])), act))
        out.append(_sec("bx", "Report aayi, ID nahi likha", "%d" % len(nxs),
                        '<p class="sm">Lab ne mail mein clinic ID nahi likha, aur naam se pakka nahi hua. Mareez chunein — '
                        'report us line par jud jayegi.</p>' + "".join(li)).replace('class="badge"', 'class="badge red"', 1))
    if orphans and (roles & {"maker", "checker"}):
        li = "".join('<div class="lrow"><div class="rl"><span class="no">%s</span> %s <span class="sm">report %s</span></div>%s</div>'
                     % (_esc(r["clinic_id"]), _esc(r["name"] or "—"), _dmy(r["day"])[:6],
                        ('<form method="post" action="/finance/slips/pending/act" class="rb"><input type="hidden" name="key" value="%s">'
                         '<button name="act" value="orph_ok">Test hua tha</button><button name="act" value="orph_bad">ID galat</button></form>'
                         % _esc(r["key"])) if is_maker else "") for r in orphans)
        out.append(_sec("bo", "Report aayi, test likha nahi tha", "%d" % len(orphans),
                        '<p class="sm">Walk-in tha to "Test hua tha"; report par ID galat ho to "ID galat" (Check karein mein theek karein).</p>' + li)
                   .replace('class="badge"', 'class="badge red"', 1))
    try:
        nms = name_mismatches(con) if (roles & {"maker", "checker"}) else []
    except Exception:                                    # noqa: BLE001
        nms = []
    if nms:
        li = "".join('<div class="lrow"><div class="rl"><span class="no">%s</span> <b>%s</b> <span class="sm">%s</span>'
                     '<br><span class="sm">report par: %s</span></div>%s</div>'
                     % (_esc(r["clinic_id"]), _esc(r["our_name"]), _dmy(r["day"])[:6], _esc(r["report_name"]),
                        ('<form method="post" action="/finance/slips/pending/act" class="rb"><input type="hidden" name="key" value="%s">'
                         '<button name="act" value="nm_ok">Wahi mareez</button><button name="act" value="nm_bad">ID galat</button></form>'
                         % _esc(r["key"])) if is_maker else "") for r in nms)
        out.append(_sec("bm", "Report par naam alag", "%d" % len(nms),
                        '<p class="sm">Lab ki report par naam, is ID ke naam se nahi milta. Wahi mareez ho to "Wahi mareez"; '
                        'nahi to "ID galat" aur lab ko sahi ID batayein.</p>' + li).replace('class="badge"', 'class="badge red"', 1))
    today = _today()
    gt = [o for o in got if (o.get("received_at") or "")[:10] >= (dt.date.fromisoformat(today) - dt.timedelta(days=1)).isoformat()]
    if gt:
        try:
            byname = {r[0] for r in con.execute("SELECT msg_id FROM lab_noid WHERE clinic_id<>''")}    # S391
        except Exception:                                # noqa: BLE001
            byname = set()
        out.append(_sec("bg", "Aa gayi (kal aur aaj)", "%d" % len(gt), "".join(
            '<div class="lrow"><span class="no">%s</span> %s <span class="sm">✔ %s%s</span></div>'
            % (_esc(o["clinic_id"]), _esc(o["name"]), _esc((o.get("received_at") or "")[5:16]),
               " · naam se juda" if o.get("msg_id") in byname else "") for o in gt)))
    return "".join(out)


def _pend_xray_html(con, u, xs):
    is_maker = "maker" in _roles(u)
    rows = []
    for o in xs:
        act = ""
        if is_maker:
            act = ('<form method="post" action="/finance/slips/pending/act" class="rb"><input type="hidden" name="key" value="%s">'
                   '<button name="act" value="put">%s</button><button name="act" value="not_done">X-ray nahi hua</button></form>'
                   % (_esc(o["key"]), "Dobara daali" if o["st"] == "nomail" else "Photo daal di"))
        rows.append('<div class="lrow%s"><div class="rl"><span class="no">%s</span> <b>%s</b> <span class="sm">%s · parchi %d</span>'
                    '<br><span class="sm">%s</span> %s</div>%s</div>'
                    % (" miss" if o["st"] in ("late", "nomail") else "", _esc(o["clinic_id"]), _esc(o["name"] or "—"),
                       _dmy(o["day"])[:6], o["slip_no"], _esc(o["what"]), _chip(o["st"], o["word"]), act))
    red = len([o for o in xs if o["st"] in ("late", "nomail")])
    sec = _sec("xp", "X-ray photo baaki", "%d%s" % (len(xs), (" · %d der" % red) if red else ""),
               '<p class="sm">Photo "X-ray test" folder mein, naam mein clinic ID ke saath.</p>' +
               ("".join(rows) or '<p class="sm">Koi photo baaki nahi. ✔</p>'))
    return sec.replace('<details class="sec"', '<details class="sec" open', 1)


@bp.route("/finance/slips/pending")
def pending_page():
    u, err = _require("maker", "checker", "viewer", unit=UNIT)
    if err:
        return _shell("Report baaki", _denied(), "hi")
    con = _db()
    pend_ensure(con)
    fill_new_names(con)
    roles = _roles(u)
    tabs = [("blood", "Blood")]
    if roles & {"maker", "checker"}:
        tabs.append(("xray", "X-ray"))
    t = request.args.get("t") or "blood"
    if t not in dict(tabs):
        t = "blood"
    msg_ok, msg_err = request.args.get("ok") or "", request.args.get("err") or ""
    b, g, orph = blood_pending(con)
    xs = xray_pending(con) if len(tabs) > 1 else []
    nav = ['<nav class="menu tabs">']
    for k, lab in tabs:
        n = len(b) if k == "blood" else len(xs)
        nav.append('<a class="mi%s" href="/finance/slips/pending?t=%s"><b>%s</b><span class="%s">%d baaki</span></a>'
                   % (" on" if k == t else "", k, lab, "hot" if n else "", n))
    nav.append("</nav>")
    parts = []
    if msg_ok:
        parts.append('<div class="ok">%s</div>' % _esc(msg_ok))
    if msg_err:
        parts.append('<div class="bad">%s</div>' % _esc(msg_err))
    body = _pend_blood_html(con, u, b, g, orph) if t == "blood" else _pend_xray_html(con, u, xs)
    return _shell("Report baaki", "".join(parts) + "".join(nav) + body + _PEND_CSS + _TILE_JS, "hi")


_PEND_CSS = ("<style>.tabs{display:flex;gap:6px;margin:0 0 8px}.tabs .mi{flex:1}.tabs .mi.on{outline:3px solid var(--accent)}"
             ".lrow.miss .rl b{color:var(--bad)}.lrow .rl{flex:1 1 60%}</style>")


def _pend_back(t, ok="", err=""):
    return redirect("/finance/slips/pending?t=%s%s%s" % (t, ("&ok=" + _q(ok)) if ok else "", ("&err=" + _q(err)) if err else ""),
                    code=303)


@bp.route("/finance/slips/pending/act", methods=["POST"])
def pending_act():
    u, err = _require("maker", "viewer", unit=UNIT)
    if err:
        return err
    con = _db()
    pend_ensure(con)
    who, now = _who(u), _stamp()
    key, act = (request.form.get("key") or "").strip(), request.form.get("act") or ""
    roles = _roles(u)
    m = re.fullmatch(r"b:(\d+)", key)
    if m:
        o = con.execute("SELECT * FROM blood_order WHERE id=? AND state='ok'", (int(m.group(1)),)).fetchone()
        if not o:
            return _pend_back("blood", err="Line nahi mili.")
        bkey = "bo:%s:%s" % (o["day"], o["clinic_id"])
        if act == "mailed":
            con.execute("UPDATE blood_order SET mailed_by=?, mailed_at=?, later_until='' WHERE id=?", (who, now, o["id"]))
            _record_answer(con, bkey, "blood", o["clinic_id"], "asked", who, "mail bheja (Report baaki)")
            msg = "%s: mail likh diya. Report aate hi line hat jayegi." % o["clinic_id"]
        elif act == "not_tested":
            con.execute("UPDATE blood_order SET outcome='not_tested', outcome_by=?, outcome_at=? WHERE id=?", (who, now, o["id"]))
            msg = "%s: test nahi hua — band." % o["clinic_id"]
        elif act == "later":
            lu = (dt.date.fromisoformat(_today()) + dt.timedelta(days=3)).isoformat()
            con.execute("UPDATE blood_order SET later_until=? WHERE id=?", (lu, o["id"]))
            _record_answer(con, bkey, "blood", o["clinic_id"], "asked", who, "baad mein aayegi (Report baaki)")
            msg = "%s: %s tak chup, phir wapas aayegi." % (o["clinic_id"], _dmy(lu)[:6])
        elif act == "name":
            nm = " ".join((request.form.get("name") or "").split())[:60]
            if len(nm) < 2:
                return _pend_back("blood", err="Naam likhein.")
            con.execute("UPDATE blood_order SET name_seen=?, name_by=? WHERE id=?", (nm, who, o["id"]))
            msg = "Naam save."
        else:
            return _pend_back("blood", err="Galat button.")
        _audit_safe(con, o["id"], "pend_blood_" + act, None, json.dumps({"cid": o["clinic_id"], "day": o["day"]}), who)
        con.commit()
        return _pend_back("blood", ok=msg)
    m = re.fullmatch(r"orph:(\d{4}-\d{2}-\d{2}):([0-9A-Za-z\-/]{1,12})", key)
    if m:
        if "maker" not in roles:
            return _pend_back("blood", err="Yeh reception ka kaam hai.")
        d, cid = m.group(1), m.group(2)
        if act == "orph_ok":
            try:
                con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                            (d, cid, _name_for(con, cid), who, now))
            except Exception:                            # noqa: BLE001 -- already an order that day: nothing to add
                pass
            msg = "%s: test likh diya (walk-in)." % cid
        elif act == "orph_bad":
            msg = "%s: Check karein mein ID theek karein." % cid
        else:
            return _pend_back("blood", err="Galat button.")
        con.execute("INSERT OR REPLACE INTO pend_mark(key, kind, clinic_id, day, act, by_user, at) VALUES (?,?,?,?,?,?,?)",
                    (key, "orphan", cid, d, act, who, now))
        _audit_safe(con, 0, "pend_" + act, None, json.dumps({"cid": cid, "day": d}), who)
        con.commit()
        return _pend_back("blood", ok=msg)
    m = re.fullmatch(r"nm:(\d+)", key)
    if m:
        if "maker" not in roles or act not in ("nm_ok", "nm_bad"):
            return _pend_back("blood", err="Yeh reception ka kaam hai.")
        f = con.execute("SELECT clinic_id, day FROM record_file WHERE id=?", (int(m.group(1)),)).fetchone()
        if not f:
            return _pend_back("blood", err="Report nahi mili.")
        con.execute("INSERT OR REPLACE INTO pend_mark(key, kind, clinic_id, day, act, by_user, at) VALUES (?,?,?,?,?,?,?)",
                    (key, "name", f["clinic_id"], f["day"], act, who, now))
        _audit_safe(con, 0, "pend_" + act, None, json.dumps({"cid": f["clinic_id"], "day": f["day"]}), who)
        con.commit()
        return _pend_back("blood", ok=("%s: theek, wahi mareez." % f["clinic_id"]) if act == "nm_ok"
                          else ("%s: lab ko sahi ID batayein; Check karein mein report ka ID theek karein." % f["clinic_id"]))
    m = re.fullmatch(r"nx:([0-9A-Za-z_\-]{1,64})", key)
    if m:                                                # S391: the report the lab mailed with no ID
        noid_ensure(con)
        r = con.execute("SELECT * FROM lab_noid WHERE msg_id=?", (m.group(1),)).fetchone()
        if not r:
            return _pend_back("blood", err="Report nahi mili.")
        if r["clinic_id"] or r["how"]:
            return _pend_back("blood", ok="Yeh report pehle hi jud chuki hai.")
        if act == "noid_pick":
            cid = _clean_id(request.form.get("cid2")) or _clean_id(request.form.get("cid"))
            if not cid:
                return _pend_back("blood", err="Mareez chunein ya clinic ID likhein.")
            noid_resolve(con, r["msg_id"], cid, "pick", who)
            has = con.execute("SELECT 1 FROM blood_order WHERE clinic_id=? AND state='ok' LIMIT 1", (cid,)).fetchone()
            msg = ("%s: report jud gayi ✔" % cid) if has else ("%s: report jud gayi — is ID ka test likha nahi tha, "
                                                                "reception dekhe." % cid)
        elif act == "noid_gone":
            con.execute("UPDATE lab_noid SET how='gone', by_user=?, at=? WHERE msg_id=?", (who, now, r["msg_id"]))
            msg = "Theek — yeh report list se hata di."
        else:
            return _pend_back("blood", err="Galat button.")
        _audit_safe(con, 0, "pend_" + act, None, json.dumps({"msg": r["msg_id"]}), who)
        con.commit()
        return _pend_back("blood", ok=msg)
    m = re.fullmatch(r"xm:(\d{4}-\d{2}-\d{2}):([0-9A-Za-z\-/]{1,12})", key)
    if m:
        if "maker" not in roles:
            return _pend_back("blood", err="Yeh X-ray ka kaam hai.")
        d, cid = m.group(1), m.group(2)
        if act not in ("put", "not_done"):
            return _pend_back("xray", err="Galat button.")
        con.execute("INSERT OR REPLACE INTO pend_mark(key, kind, clinic_id, day, act, by_user, at) VALUES (?,?,?,?,?,?,?)",
                    (key, "xray", cid, d, act, who, now))
        _record_answer(con, key, "xray_missing", cid, "asked" if act == "put" else "not_done", who, "Report baaki")
        _audit_safe(con, 0, "pend_xray_" + act, None, json.dumps({"cid": cid, "day": d}), who)
        con.commit()
        return _pend_back("xray", ok=("%s: photo likh diya, file hone ka intezaar." % cid) if act == "put"
                          else ("%s: X-ray nahi hua — band." % cid))
    return _pend_back("blood", err="Line nahi mili.")


@bp.route("/finance/slips/pending/new", methods=["POST"])
def pending_new():
    """Reception's walk-in blood test (the owner: sampling and payment are at reception)."""
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    pend_ensure(con)
    cid = _clean_id(request.form.get("clinic_id"))
    if not cid:
        return _pend_back("blood", err="Clinic ID likhein.")
    nm = _name_for(con, cid) or " ".join((request.form.get("name") or "").split())[:60]
    if len(nm) < 2:
        return _pend_back("blood", err="ID %s ka naam nahi mila — naam likhein." % cid)
    day = _today()
    if con.execute("SELECT 1 FROM blood_order WHERE day=? AND clinic_id=? AND state='ok'", (day, cid)).fetchone():
        return _pend_back("blood", err="ID %s ka blood test aaj pehle se likha hai." % cid)
    c = con.execute("INSERT INTO blood_order(day, clinic_id, name_seen, logged_by, logged_at) VALUES (?,?,?,?,?)",
                    (day, cid, nm, _who(u), _stamp()))
    _audit_safe(con, c.lastrowid, "pend_blood_new", None, json.dumps({"cid": cid}), _who(u))
    con.commit()
    return _pend_back("blood", ok="Blood test likh diya: %s · %s" % (cid, nm))


@bp.route("/finance/slips/api/lab-noid", methods=["POST"])
def api_lab_noid():
    """S391. The clinic mailbox's Apps Script found a lab report with no clinic ID in the subject: message id, the name
    in the subject, time received. Answers the clinic ID when it is certain (then the report is counted at once), ''
    while it is not -- the mailbox asks again next run and files the PDF when an ID comes back. Same token as lab-report."""
    tok = os.environ.get("FINANCE_CRON_TOKEN", "")
    given = request.headers.get("X-Finance-Cron", "")
    if not (tok and given and _hmac.compare_digest(str(given), str(tok))):
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    rows = j.get("reports") if isinstance(j.get("reports"), list) else [j]
    con = _db()
    ensure(con)
    blood_ensure(con)
    noid_ensure(con)
    good = []
    for x in rows[:200]:
        mid = str(x.get("msg_id") or "")[:64]
        at = str(x.get("received_at") or "")[:19].replace("T", " ")
        if re.fullmatch(r"[0-9A-Za-z_\-]{1,64}", mid) and re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?", at):
            good.append((at, mid, " ".join(str(x.get("name") or "").split())[:60]))
    out = []
    for at, mid, nm in sorted(good):
        con.execute("INSERT OR IGNORE INTO lab_noid(msg_id, name, received_at, pushed_at) VALUES (?,?,?,?)",
                    (mid, nm, at, _stamp()))
        r = con.execute("SELECT clinic_id, how FROM lab_noid WHERE msg_id=?", (mid,)).fetchone()
        cid = r["clinic_id"]
        if not cid and not r["how"]:
            cid = noid_match(con, nm, at)
            if cid:
                noid_resolve(con, mid, cid, "auto")
        out.append({"msg_id": mid, "clinic_id": cid, "gone": r["how"] == "gone"})
    con.commit()
    return jsonify(ok=True, reports=out)


@bp.route("/finance/slips/api/pending-counts")
def api_pending_counts():
    """The doctors' one line (the Gist tile): counts only, no name."""
    u, err = _require("checker", unit=UNIT)
    if err:
        return err
    return jsonify(ok=True, **(pending_counts(_db()) or {}))
