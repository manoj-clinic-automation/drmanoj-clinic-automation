#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""slip_log.py -- S324 (session 271, 19-Sep-2026), S325/S326/S327 fixes the same day: new = above the highest ID issued before the day. The OPD & X-ray/Proc slip tile, and the night
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
        con.execute("INSERT INTO slip_item(slip_id, kind, service_id, name, side, price_p, sort) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (sid, it["kind"], it.get("service_id"), it["name"], it.get("side", ""),
                     int(it.get("price_p") or 0), i))
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
            out.append({"kind": kind, "service_id": s["id"], "name": s["name"], "side": side,
                        "price_p": s["price_p"]})
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


def _who_label(r):
    if r.get("no_id_name"):
        return "%s (ID nahi)" % r["no_id_name"]
    if r.get("name_seen"):
        return "%s · %s" % (r["clinic_id"], r["name_seen"])
    if r.get("is_new"):
        return "%s · naya" % r["clinic_id"]
    return r.get("clinic_id") or "—"


def _items_label(items):
    out = []
    for it in items:
        s = it["name"] + ((" " + it["side"]) if it.get("side") else "")
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
def _form_err(msg):
    return redirect("/finance/slips?err=" + _q(msg) + "#" + (request.form.get("sec") or ""), code=303)


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
    if "checker" in _roles(u) and "maker" not in _roles(u) and not request.args.get("tile"):
        return redirect("/finance/slips/report", code=302)
    return _shell("OPD & X-ray/Proc parchi", _tile_html(con, u), "hi")


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
    return redirect("/finance/slips?ok=" + _q(msg) + "#" + series, code=303)


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
        return _form_err("Galat button.")
    _audit_safe(con, sid, "slip_room_" + act, before, None, who)
    con.commit()
    return redirect("/finance/slips#room", code=303)


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
    return redirect("/finance/slips?ok=" + _q("Parchi %d: theek kar diya." % s["slip_no"]) + "#list", code=303)


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
    return redirect("/finance/slips?ok=" + _q("%s book: %d–%d, agla number %d."
                                              % (SERIES_NAME[series], a, b, next_no(con, series) or st))
                    + "#" + series, code=303)


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
            '<input name="%s%d_other" class="oth" placeholder="naam (zaroori nahi)" maxlength="60" hidden></div>'
            % (kind, "" if i == 0 else " hidden", kind, i, _opts(rows, label), kind, i, kind, i))
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

    order = [sec_room, sec_opd, sec_xp, sec_list, sec_book] if room_first else \
        [sec_opd, sec_xp, sec_room, sec_list, sec_book]
    # only the top section open (the owner, 19-Sep-2026)
    order[0] = order[0].replace("<details class=\"sec\"", "<details class=\"sec\" open", 1)
    return "".join(parts) + "".join(order) + _TILE_JS


def _amount_label(items):
    """S327: the slip's amount, read-only, from the rates copied at logging. An unpriced line is said so."""
    tot = sum(int(it.get("price_p") or 0) for it in items)
    unpriced = [it for it in items if not int(it.get("price_p") or 0)]
    if not items:
        return "\u2014"
    if tot and unpriced:
        return "%s + %d rate nahi" % (_rs(tot), len(unpriced))
    if not tot:
        return "rate nahi"
    return _rs(tot)


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
      var s=r.querySelector('.svc'),sd=r.querySelector('.side'),o=r.querySelector('.oth');
      s.addEventListener('change',function(){var op=s.options[s.selectedIndex];
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


def _shell(title, body, lang):
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
.nav{font-size:15px}ul{margin:0;padding-left:1.2em}li{margin:3px 0}
</style></head><body><header class="top"><a class="back" href="/portal">← Portal</a><h1>%s</h1><span class="d">%s</span></header>
<main>%s</main></body></html>""" % (lang, _esc(title), _esc(title), _dmy(_today())[:6], body)
