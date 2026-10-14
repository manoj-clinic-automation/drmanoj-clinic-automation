#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""physio_book.py -- kit S552_PHYSIO_REGISTER (session 313, 14-Oct-2026, D646). Bhati's physio register.

THE OWNER, 13-Oct 14:16-14:42 IST and 14-Oct 04:32:
  "Physiotherapist also wants to log his home visits in the physiotherapy section. And this he will be doing himself."
  "He keeps the money with himself. And it should not count in the monthly income for the accountants and stay as a separate
   report for the physiotherapy part. The usual charge per visit is 500 rupees. And instead of paisa mila, payment received is
   a better word. And for the clinic physiotherapy he is doing, now we should be able to expand it similarly to patient-wise."
  "I would like the reception not to be involved in this bookkeeping. They simply take the payment and issue the slip and
   physiotherapist then does this Parchi entry and his Parchi entry are then matched with the totals which the reception daily
   posts. And any differences are flagged."

  /finance/physio/book                Bhati's page (unit 'physiobook', maker or checker), Roman Hinglish. Two tabs:
                                      Clinic -- one row per numbered physio slip (slip no, patient, Rs 250, Cash / UPI), the
                                      day's match against reception's counter-sheet figures (clinic_physio_day, READ ONLY),
                                      missing slip numbers named; Ghar -- home-visit patients, a tap per visit (Rs 500),
                                      "Payment received", Rok do / Phir shuru / Band karo.
  /finance/physio/book/home/<id>      one home patient (the same unit and roles).
  /finance/physio/book/report         the owner's report (checker), English: day-wise, patient-wise, month and year; the switch.

  Append-only money: a correction is a void (with its reason) plus a new row, never an UPDATE of an amount.
  Switched OFF for the maker until the owner opens it (setting physio_book.on); a checker always sees everything.
  NOTHING here writes clinic_physio_day, packs, the day revenue or the morning match: home-visit money is Bhati's own and lives
  only on these pages. Every write goes through the app's audit helper. Tables on first request, never at import (F-303).
"""
import datetime as dt
import os
import re
from urllib.parse import quote

from flask import Blueprint, redirect, request

bp = Blueprint("physio_book", __name__)

APP_VERSION = "S552-PHYSIO-BOOK-1.0"
_db = None
_require = None
_audit = None
_unit = "physiobook"

ON_KEY = "physio_book.on"
CLINIC_RATE_KEY = "physio_book.clinic_rate_p"
HOME_RATE_KEY = "physio_book.home_rate_p"
CLINIC_RATE_P = 25000
HOME_RATE_P = 50000
BACK_DAYS = 7                    # a slip or a visit: today and the six days before it
SEARCH_DAYS = 365                # Docterz patients seen in the last year
MAX_P = 10000000                 # Rs 1,00,000 for one typed figure
VOID_WHY = (("amount", "galat amount"), ("patient", "galat patient"), ("twice", "do baar entry"))
OFF_LINE = "Yeh page abhi band hai — Dr Manoj ke kehne par khulega."

SCHEMA = """
CREATE TABLE IF NOT EXISTS physio_patient (
  id INTEGER PRIMARY KEY,
  clinic_id TEXT NOT NULL DEFAULT '',
  name TEXT NOT NULL,
  mobile TEXT NOT NULL DEFAULT '',
  created_by TEXT,
  created_at TEXT
);
CREATE TABLE IF NOT EXISTS physio_course (
  id INTEGER PRIMARY KEY,
  patient_id INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('clinic','home')),
  rate_p INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','paused','closed')),
  started TEXT,
  changed_at TEXT,
  changed_by TEXT
);
CREATE TABLE IF NOT EXISTS physio_session (
  id INTEGER PRIMARY KEY,
  course_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  slip_no INTEGER,
  amount_p INTEGER NOT NULL,
  mode TEXT NOT NULL DEFAULT '' CHECK(mode IN ('','cash','upi')),
  by_whom TEXT,
  at TEXT,
  voided_at TEXT NOT NULL DEFAULT '',
  voided_by TEXT NOT NULL DEFAULT '',
  void_why TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS physio_payment (
  id INTEGER PRIMARY KEY,
  course_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  amount_p INTEGER NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('cash','upi')),
  by_whom TEXT,
  at TEXT,
  voided_at TEXT NOT NULL DEFAULT '',
  voided_by TEXT NOT NULL DEFAULT '',
  void_why TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_physio_session_slip ON physio_session(slip_no) WHERE slip_no IS NOT NULL AND voided_at='';
CREATE INDEX IF NOT EXISTS ix_physio_session_course ON physio_session(course_id);
CREATE INDEX IF NOT EXISTS ix_physio_session_day ON physio_session(day);
CREATE INDEX IF NOT EXISTS ix_physio_payment_course ON physio_payment(course_id);
CREATE INDEX IF NOT EXISTS ix_physio_course_patient ON physio_course(patient_id);
"""

_schema_done = False


def init(app, db_getter, require_fn, audit_fn=None, unit="physiobook"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, _unit
    _db, _require, _audit, _unit = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    return bp


def _ensure(con):
    global _schema_done
    if _schema_done:
        return
    con.executescript(SCHEMA)
    con.commit()
    _schema_done = True


# ---------------------------------------------------------------- small helpers
def _now():
    """The box's clock is IST. PHYSIO_BOOK_NOW=<iso> pins it for the walk."""
    v = os.environ.get("PHYSIO_BOOK_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now().replace(microsecond=0)


def _today():
    return _now().date()


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def _r(p):
    return "₹ {:,}".format(int(round((p or 0) / 100.0)))


def _iso_ok(d):
    try:
        return dt.date(int(d[:4]), int(d[5:7]), int(d[8:10])).isoformat() == d
    except (ValueError, IndexError, TypeError):
        return False


def _human(iso):
    return dt.date.fromisoformat(iso).strftime("%d-%b-%Y") if _iso_ok(iso or "") else (iso or "—")


def _short(iso):
    return dt.date.fromisoformat(iso).strftime("%a %d-%b") if _iso_ok(iso or "") else (iso or "—")


def _paise(v):
    """A rupee figure typed by a person: blank or a non-number is refused, never a quiet 0."""
    s = str(v or "").replace(",", "").replace("₹", "").strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", s):
        return None
    p = int(round(float(s) * 100))
    return p if 0 < p <= MAX_P else None


def _mobile(v):
    d = re.sub(r"\D", "", str(v or ""))
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    if len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d if re.fullmatch(r"[6-9]\d{9}", d) else None


def _mask(m):
    m = str(m or "")
    return ("······" + m[-4:]) if len(m) >= 4 else ("—" if not m else "····")


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r[0] if r and r[0] not in (None, "") else default
    except Exception:                            # noqa: BLE001
        return default


def _int_setting(con, key, default):
    try:
        return int(_setting(con, key, str(default)))
    except (TypeError, ValueError):
        return default


def is_on(con):
    return str(_setting(con, ON_KEY, "0")).strip() == "1"


def _audit_safe(con, table, row_id, action, before, after, who):
    """As clinic_money does: the app's own audit helper; a fault there never loses the write."""
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)
        con.commit()
    except Exception:                            # noqa: BLE001
        pass


def _days_back():
    t = _today()
    return [(t - dt.timedelta(days=i)).isoformat() for i in range(BACK_DAYS)]


def _day_ok(d):
    return d in _days_back()


def _gate():
    """(user, roles, error_response). maker or checker of the unit; a maker only while the switch is on."""
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return None, set(), (_shell("Physio register", "<div class='card'><h2>Not permitted</h2><p>Yeh page physio register hai. "
                                    "Aapka login is par nahi hai. Galat lage to Dr Manoj se kahiye.</p></div>"), 403)
    return u, set(u.get("roles") or []), None


# ---------------------------------------------------------------- reading
def patient(con, pid):
    return con.execute("SELECT * FROM physio_patient WHERE id=?", (pid,)).fetchone()


def _course(con, cid):
    return con.execute("SELECT c.*, p.name, p.mobile, p.clinic_id FROM physio_course c JOIN physio_patient p ON p.id=c.patient_id "
                       "WHERE c.id=?", (cid,)).fetchone()


def next_slip(con):
    r = con.execute("SELECT MAX(slip_no) FROM physio_session WHERE slip_no IS NOT NULL AND voided_at=''").fetchone()
    return (r[0] or 0) + 1


def slip_owner(con, n):
    return con.execute("SELECT s.day, p.name, p.clinic_id FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                       "JOIN physio_patient p ON p.id=c.patient_id WHERE s.slip_no=? AND s.voided_at=''", (n,)).fetchone()


def search(con, q):
    """[(key, name, clinic_id, hint)] -- the register's own patients first, then Docterz's of the last year."""
    q = (q or "").strip()
    if len(q) < 2:
        return []
    like = "%" + q.replace("%", "").replace("_", "") + "%"
    out, have = [], set()
    for r in con.execute("SELECT id, name, clinic_id FROM physio_patient WHERE name LIKE ? OR clinic_id LIKE ? OR mobile LIKE ? "
                         "ORDER BY id DESC LIMIT 15", (like, like, like)):
        out.append(("p%d" % r["id"], r["name"], r["clinic_id"], "register"))
        if r["clinic_id"]:
            have.add(r["clinic_id"])
    try:
        since = (_today() - dt.timedelta(days=SEARCH_DAYS)).isoformat()
        for r in con.execute("SELECT clinic_id, patient, MAX(business_date) AS d FROM clinic_day_line WHERE business_date>=? "
                             "AND clinic_id<>'' AND (clinic_id LIKE ? OR patient LIKE ?) GROUP BY clinic_id ORDER BY d DESC LIMIT 20",
                             (since, like, like)):
            if r["clinic_id"] not in have:
                out.append(("c" + r["clinic_id"], r["patient"] or "?", r["clinic_id"], "Docterz %s" % _human(r["d"])))
    except Exception:                            # noqa: BLE001 -- no Docterz lines on this box: the register only
        pass
    return out[:25]


def pick_label(con, key):
    """(name, clinic_id) for a pick key, or None."""
    if not key:
        return None
    if key[0] == "p" and key[1:].isdigit():
        r = patient(con, int(key[1:]))
        return (r["name"], r["clinic_id"]) if r else None
    if key[0] == "c" and len(key) > 1:
        r = con.execute("SELECT patient FROM clinic_day_line WHERE clinic_id=? ORDER BY business_date DESC LIMIT 1", (key[1:],)).fetchone()
        p = con.execute("SELECT name FROM physio_patient WHERE clinic_id=? ORDER BY id LIMIT 1", (key[1:],)).fetchone()
        if p:
            return p["name"], key[1:]
        return (r["patient"], key[1:]) if r else None
    return None


def day_clinic(con, d):
    return list(con.execute("SELECT s.*, p.name, p.clinic_id, p.mobile FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                            "JOIN physio_patient p ON p.id=c.patient_id WHERE c.kind='clinic' AND s.day=? "
                            "ORDER BY (s.voided_at<>''), s.slip_no, s.id", (d,)))


def day_match(con, d):
    """Bhati's cash and UPI for the day beside reception's (clinic_physio_day, read only)."""
    b = {"cash": 0, "upi": 0}
    n = 0
    for r in con.execute("SELECT s.mode, s.amount_p FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                         "WHERE c.kind='clinic' AND s.day=? AND s.voided_at=''", (d,)):
        n += 1
        if r["mode"] in b:
            b[r["mode"]] += r["amount_p"]
    rec = None
    try:
        rec = con.execute("SELECT cash_p, upi_p FROM clinic_physio_day WHERE business_date=?", (d,)).fetchone()
    except Exception:                            # noqa: BLE001
        rec = None
    m = dict(day=d, n=n, b_cash=b["cash"], b_upi=b["upi"], has_r=rec is not None,
             r_cash=(rec["cash_p"] or 0) if rec else 0, r_upi=(rec["upi_p"] or 0) if rec else 0)
    m["agree"] = m["has_r"] and m["b_cash"] == m["r_cash"] and m["b_upi"] == m["r_upi"]
    m["differs"] = m["has_r"] and not m["agree"]
    return m


def first_clinic_day(con):
    r = con.execute("SELECT MIN(s.day) FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                    "WHERE c.kind='clinic' AND s.voided_at=''").fetchone()
    return r[0] if r else None


def differ_days(con, first, last):
    """Days from the register's first clinic entry on, up to today, where reception and Bhati differ."""
    floor = first_clinic_day(con)
    if not floor:
        return []
    lo, hi = max(first, floor), min(last, _today().isoformat())
    if lo > hi:
        return []
    days = set()
    for r in con.execute("SELECT DISTINCT business_date FROM clinic_physio_day WHERE business_date BETWEEN ? AND ?", (lo, hi)):
        days.add(r[0])
    out = []
    for d in sorted(days):
        m = day_match(con, d)
        if m["differs"]:
            out.append(m)
    return out


def missing_slips(con, d):
    """Slip numbers not entered: between the day's lowest and highest, and between the previous entered day's highest and
    this day's lowest. A number entered on any day (live) is never named."""
    nums = sorted(r[0] for r in con.execute("SELECT s.slip_no FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                                            "WHERE c.kind='clinic' AND s.day=? AND s.voided_at='' AND s.slip_no IS NOT NULL", (d,)))
    if not nums:
        return [], []
    live = set(nums)

    def taken(n):
        return n in live or con.execute("SELECT 1 FROM physio_session WHERE slip_no=? AND voided_at=''", (n,)).fetchone() is not None

    inside = [n for n in range(nums[0] + 1, nums[-1]) if n not in live and not taken(n)][:60]
    before = []
    pr = con.execute("SELECT MAX(s.day) FROM physio_session s JOIN physio_course c ON c.id=s.course_id WHERE c.kind='clinic' "
                     "AND s.day<? AND s.voided_at='' AND s.slip_no IS NOT NULL", (d,)).fetchone()
    if pr and pr[0]:
        pm = con.execute("SELECT MAX(s.slip_no) FROM physio_session s JOIN physio_course c ON c.id=s.course_id WHERE c.kind='clinic' "
                         "AND s.day=? AND s.voided_at=''", (pr[0],)).fetchone()[0]
        if pm is not None and pm + 1 < nums[0]:
            span = range(pm + 1, nums[0])
            if len(span) <= 200:
                before = [n for n in span if not taken(n)]
            else:
                before = ["%d … %d" % (pm + 1, nums[0] - 1)]
    return inside, before


def course_sums(con, cid, first=None, last=None):
    w, a = "", [cid]
    if first:
        w, a = " AND day BETWEEN ? AND ?", [cid, first, last]
    v = con.execute("SELECT COUNT(*), COALESCE(SUM(amount_p),0), MAX(day) FROM physio_session WHERE course_id=? AND voided_at=''" + w, a).fetchone()
    p = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM physio_payment WHERE course_id=? AND voided_at=''" + w, a).fetchone()
    return dict(visits=v[0], charged=v[1], last=v[2], received=p[0], due=v[1] - p[0])


def home_courses(con):
    return list(con.execute("SELECT c.*, p.name, p.mobile, p.clinic_id FROM physio_course c JOIN physio_patient p ON p.id=c.patient_id "
                            "WHERE c.kind='home' ORDER BY p.name COLLATE NOCASE, c.id"))


# ---------------------------------------------------------------- writing helpers
def _new_patient(con, name, mobile, clinic_id, who):
    cur = con.execute("INSERT INTO physio_patient (clinic_id, name, mobile, created_by, created_at) VALUES (?,?,?,?,?)",
                      (clinic_id or "", name, mobile or "", who, _stamp()))
    pid = cur.lastrowid
    _audit_safe(con, "physio_patient", pid, "insert", None, dict(clinic_id=clinic_id or "", name=name, mobile=_mask(mobile)), who)
    return pid


def _patient_from_form(con, f, who):
    """(patient_id, error_key). A pick (p<id> / c<clinic id>) or a new name and mobile."""
    key = (f.get("pick") or "").strip()
    if key:
        if key[0] == "p" and key[1:].isdigit():
            r = patient(con, int(key[1:]))
            return (r["id"], None) if r else (None, "patient")
        if key[0] == "c" and len(key) > 1:
            cid = key[1:]
            r = con.execute("SELECT id FROM physio_patient WHERE clinic_id=? ORDER BY id LIMIT 1", (cid,)).fetchone()
            if r:
                return r["id"], None
            d = con.execute("SELECT patient FROM clinic_day_line WHERE clinic_id=? ORDER BY business_date DESC LIMIT 1", (cid,)).fetchone()
            if not d:
                return None, "patient"
            return _new_patient(con, (d["patient"] or "?").strip(), "", cid, who), None
        return None, "patient"
    name = re.sub(r"\s+", " ", (f.get("name") or "")).strip()[:80]
    if len(name) < 2:
        return None, "patient"
    mob = _mobile(f.get("mobile"))
    if not mob:
        return None, "mobile"
    return _new_patient(con, name, mob, "", who), None


def _course_for(con, pid, kind, rate_p, who):
    r = con.execute("SELECT id FROM physio_course WHERE patient_id=? AND kind=? ORDER BY (status='closed'), id DESC LIMIT 1",
                    (pid, kind)).fetchone()
    if r:
        return r["id"]
    cur = con.execute("INSERT INTO physio_course (patient_id, kind, rate_p, status, started, changed_at, changed_by) VALUES (?,?,?,?,?,?,?)",
                      (pid, kind, rate_p, "active", _today().isoformat(), _stamp(), who))
    _audit_safe(con, "physio_course", cur.lastrowid, "insert", None, dict(patient_id=pid, kind=kind, rate_p=rate_p), who)
    return cur.lastrowid


def _back(path, **kw):
    q = "&".join("%s=%s" % (k, quote(str(v), safe="")) for k, v in kw.items() if v not in (None, ""))
    return redirect(path + ("?" + q if q else ""))


# ---------------------------------------------------------------- Bhati's page
MSG = {"saved": "✓ Slip likh di gayi", "voided": "✓ Entry hata di gayi", "visit": "✓ Visit likh diya", "paid": "✓ Payment received likh diya",
       "status": "✓ Badal diya", "newhome": "✓ Ghar ka patient jud gaya", "cid": "✓ Clinic ID jud gayi"}
ERR = {"slipno": "Slip number sahi likhiye (sirf ank).", "patient": "Patient chuniye, ya naya naam likhiye.",
       "mobile": "Mobile number 10 ank ka likhiye.", "amount": "Amount sahi likhiye.", "day": "Tareekh aaj ya pichhle 6 din mein se ho.",
       "pday": "Tareekh sahi likhiye (aage ki nahi).", "mode": "Cash ya UPI dabaiye.", "why": "Hatane ki wajah chuniye.",
       "off": OFF_LINE, "exists": "Is patient ka ghar ka hisaab pehle se hai — neeche list mein dekhiye.",
       "cidtaken": "Yeh Clinic ID kisi aur patient par lagi hai.", "cidset": "Clinic ID pehle se lagi hai, badli nahi ja sakti.",
       "cidbad": "Clinic ID sahi likhiye.", "gone": "Yeh entry nahi mili (shayad pehle hi hat chuki hai).", "notactive": "Pehle 'Phir shuru' dabaiye."}


@bp.route("/finance/physio/book")
def book_page():
    u, roles, err = _gate()
    if err:
        return err
    con = _db()
    _ensure(con)
    checker = "checker" in roles
    if not is_on(con) and not checker:
        return _shell("Physio register", "<div class='card'><h2>Physio register</h2><p class='big'>%s</p></div>" % OFF_LINE)
    a = request.args
    tab = "home" if a.get("tab") == "home" else "clinic"
    head = _head(con, tab, checker, a)
    body = _home_tab(con, a) if tab == "home" else _clinic_tab(con, a)
    return _shell("Physio register", head + body)


def _head(con, tab, checker, a):
    note = ""
    if checker and not is_on(con):
        note = ("<div class='bad'>Preview — this page is still closed for Bhati. Open it from "
                "<a href='/finance/physio/book/report'>the report</a>.</div>")
    msg = MSG.get(a.get("msg") or "", "")
    e = a.get("err") or ""
    etext = ERR.get(e, "")
    if e == "dup":
        n = a.get("n") or ""
        o = slip_owner(con, int(n)) if n.isdigit() else None
        etext = ("Slip %s pehle hi likhi hai — %s, %s." % (_esc(n), _human(o["day"]), _esc(o["name"]))) if o else "Yeh slip pehle hi likhi hai."
    flash = ("<div class='ok'>%s</div>" % msg if msg else "") + ("<div class='bad'>%s</div>" % etext if etext else "")
    tabs = ("<div class='tabs'><a class='tab%s' href='/finance/physio/book'>Clinic</a>"
            "<a class='tab%s' href='/finance/physio/book?tab=home'>Ghar (Home visit)</a>%s</div>" % (
                " on" if tab == "clinic" else "", " on" if tab == "home" else "",
                "<a class='tab' href='/finance/physio/book/report'>Report ›</a>" if checker else ""))
    return note + tabs + flash


def _pick_block(con, a, action_tab, day):
    """The search box, its results as taps, and the chosen patient."""
    q = (a.get("q") or "").strip()[:40]
    hid = "<input type='hidden' name='tab' value='%s'>" % action_tab + ("<input type='hidden' name='day' value='%s'>" % day if day else "")
    out = ["<form method='get' action='/finance/physio/book' class='row'>%s<input name='q' class='note' value='%s' "
           "placeholder='Clinic ID ya naam' autocomplete='off'><button type='submit' class='save'>Dhoondo</button></form>" % (hid, _esc(q))]
    if q:
        res = search(con, q)
        if not res:
            out.append("<p class='mut'>Koi nahi mila. Naya patient neeche likhiye.</p>")
        for key, name, cid, hint in res:
            out.append("<a class='pick' href='/finance/physio/book?tab=%s%s&pick=%s'><b>%s</b> %s <span class='mut'>%s</span></a>" % (
                action_tab, ("&day=" + day) if day else "", quote(key, safe=""), _esc(name), ("· " + _esc(cid)) if cid else "", _esc(hint)))
    return "".join(out)


def _day_bar(day):
    out = []
    for d in _days_back():
        out.append("<a class='dayb%s' href='/finance/physio/book?day=%s'>%s</a>" % (" on" if d == day else "", d, _short(d)))
    return "<div class='days'>%s</div>" % "".join(out)


def _clinic_tab(con, a):
    day = a.get("day") or _today().isoformat()
    if not _day_ok(day):
        day = _today().isoformat()
    rate = _int_setting(con, CLINIC_RATE_KEY, CLINIC_RATE_P)
    nxt = next_slip(con)
    out = [_day_bar(day)]
    key = (a.get("pick") or "").strip()
    lab = pick_label(con, key)
    common = ("<tr><th class='sec'>Slip number</th><td><input name='slip_no' class='amt' inputmode='numeric' value='%d'></td></tr>"
              "<tr><th class='sec'>Amount ₹</th><td><input name='amount' class='amt' inputmode='decimal' value='%s'></td></tr>" % (
                  nxt, "{:g}".format(rate / 100.0)))
    btns = ("<div class='two'><button type='submit' name='mode' value='cash' class='big cash'>Cash</button>"
            "<button type='submit' name='mode' value='upi' class='big upi'>UPI</button></div>")
    card = ["<div class='card'><h2>Slip likhiye — %s</h2>" % _human(day)]
    if lab:
        card.append("<form method='post' action='/finance/physio/book/slip' class='entry'><input type='hidden' name='day' value='%s'>"
                    "<input type='hidden' name='pick' value='%s'><table class='grid nums'><tbody>"
                    "<tr><th class='sec'>Patient</th><td><b>%s</b> %s <a href='/finance/physio/book?day=%s' class='mut'>badlo</a></td></tr>%s"
                    "</tbody></table>%s</form>" % (day, _esc(key), _esc(lab[0]), ("· " + _esc(lab[1])) if lab[1] else "", day, common, btns))
    else:
        card.append(_pick_block(con, a, "clinic", day))
        card.append("<details class='newp'><summary>Naya patient (naam, mobile)</summary><form method='post' action='/finance/physio/book/slip' "
                    "class='entry'><input type='hidden' name='day' value='%s'><table class='grid nums'><tbody>"
                    "<tr><th class='sec'>Naam</th><td><input name='name' class='note' maxlength='80'></td></tr>"
                    "<tr><th class='sec'>Mobile</th><td><input name='mobile' class='note' inputmode='tel' maxlength='14'></td></tr>%s"
                    "</tbody></table>%s</form></details>" % (day, common, btns))
    card.append("</div>")
    out.append("".join(card))
    # the day's slips
    rows = day_clinic(con, day)
    body = []
    for r in rows:
        if r["voided_at"]:
            body.append("<tr class='void'><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td><td>hata di (%s)</td></tr>" % (
                r["slip_no"] or "—", _esc(r["name"]), _r(r["amount_p"]), (r["mode"] or "").upper(), _esc(dict(VOID_WHY).get(r["void_why"], r["void_why"]))))
        else:
            body.append("<tr><td><b>%s</b></td><td>%s%s</td><td class='r'>%s</td><td>%s</td><td>%s</td></tr>" % (
                r["slip_no"] or "—", _esc(r["name"]), (" <span class='mut'>%s</span>" % _esc(r["clinic_id"])) if r["clinic_id"] else "",
                _r(r["amount_p"]), (r["mode"] or "").upper(), _void_form("session", r["id"], "/finance/physio/book?day=%s" % day)))
    out.append("<div class='card'><h2>Is din ki slips</h2>%s</div>" % (
        "<table class='grid'><thead><tr><th>Slip</th><th>Patient</th><th class='r'>Amount</th><th>Mode</th><th></th></tr></thead><tbody>%s</tbody></table>" % "".join(body)
        if body else "<p class='mut'>Abhi koi slip nahi.</p>"))
    out.append(_match_card(con, day))
    return "".join(out)


def _void_form(kind, rid, back):
    opts = "".join("<option value='%s'>%s</option>" % (k, w) for k, w in VOID_WHY)
    return ("<details class='vd'><summary>Galat entry hatao</summary><form method='post' action='/finance/physio/book/void'>"
            "<input type='hidden' name='kind' value='%s'><input type='hidden' name='id' value='%d'><input type='hidden' name='back' value='%s'>"
            "<select name='why' class='note'><option value=''>— wajah —</option>%s</select>"
            "<button type='submit' class='clear'>Hatao</button></form></details>" % (kind, rid, _esc(back), opts))


def _match_card(con, day):
    m = day_match(con, day)
    lines = ["<table class='grid'><thead><tr><th></th><th class='r'>Cash</th><th class='r'>UPI</th></tr></thead><tbody>"
             "<tr><th class='sec'>Bhati (slips)</th><td class='r'>%s</td><td class='r'>%s</td></tr>" % (_r(m["b_cash"]), _r(m["b_upi"]))]
    if m["has_r"]:
        lines.append("<tr><th class='sec'>Reception</th><td class='r'>%s</td><td class='r'>%s</td></tr>" % (_r(m["r_cash"]), _r(m["r_upi"])))
    lines.append("</tbody></table>")
    if not m["has_r"]:
        verdict = "<p class='verdict wait'>Reception ne abhi nahi likha</p>"
    elif m["agree"]:
        verdict = "<p class='verdict good'>✓ Reception se mil gaya</p>"
    else:
        verdict = "<p class='verdict badv'>Farq: Cash %s · UPI %s</p>" % (_r(abs(m["b_cash"] - m["r_cash"])), _r(abs(m["b_upi"] - m["r_upi"])))
    inside, before = missing_slips(con, day)
    miss = ""
    if inside or before:
        parts = []
        if inside:
            parts.append("is din ke beech: %s" % ", ".join(str(n) for n in inside))
        if before:
            parts.append("pichhle din ke baad: %s" % ", ".join(str(n) for n in before))
        miss = "<p class='bad'>Slip number chhoot gaye — %s</p>" % "; ".join(parts)
    lo = (_today() - dt.timedelta(days=BACK_DAYS - 1)).isoformat()
    other = [x for x in differ_days(con, lo, _today().isoformat()) if x["day"] != day]
    od = ("<p class='mut'>Farq wale aur din: %s</p>" % ", ".join("<a href='/finance/physio/book?day=%s'>%s</a>" % (x["day"], _short(x["day"])) for x in other)) if other else ""
    return "<div class='card'><h2>Milaan — %s</h2>%s%s%s%s</div>" % (_human(day), "".join(lines), verdict, miss, od)


def _home_tab(con, a):
    rate = _int_setting(con, HOME_RATE_KEY, HOME_RATE_P)
    out = []
    key = (a.get("pick") or "").strip()
    lab = pick_label(con, key)
    rt = "<tr><th class='sec'>Ek visit ₹</th><td><input name='rate' class='amt' inputmode='decimal' value='%s'></td></tr>" % "{:g}".format(rate / 100.0)
    card = ["<details class='card'%s><summary><b>+ Naya ghar patient</b></summary>" % (" open" if (key or a.get("q")) else "")]
    if lab:
        card.append("<form method='post' action='/finance/physio/book/home/new' class='entry'><input type='hidden' name='pick' value='%s'>"
                    "<table class='grid nums'><tbody><tr><th class='sec'>Patient</th><td><b>%s</b> %s</td></tr>"
                    "<tr><th class='sec'>Mobile</th><td><input name='mobile' class='note' inputmode='tel' maxlength='14' placeholder='agar register mein nahi'></td></tr>%s"
                    "</tbody></table><button type='submit' class='save'>Shuru karo</button></form>" % (
                        _esc(key), _esc(lab[0]), ("· " + _esc(lab[1])) if lab[1] else "", rt))
    else:
        card.append(_pick_block(con, a, "home", ""))
        card.append("<form method='post' action='/finance/physio/book/home/new' class='entry'><table class='grid nums'><tbody>"
                    "<tr><th class='sec'>Naam</th><td><input name='name' class='note' maxlength='80'></td></tr>"
                    "<tr><th class='sec'>Mobile</th><td><input name='mobile' class='note' inputmode='tel' maxlength='14'></td></tr>%s"
                    "</tbody></table><button type='submit' class='save'>Naya patient jodo</button></form>" % rt)
    card.append("</details>")
    out.append("".join(card))
    run, closed = [], []
    for c in home_courses(con):
        s = course_sums(con, c["id"])
        row = ("<tr><td><a href='/finance/physio/book/home/%d'><b>%s</b></a>%s<br><a href='tel:%s' class='mut'>%s</a></td><td>%s</td>"
               "<td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'><b>%s</b></td></tr>" % (
                   c["id"], _esc(c["name"]), " <span class='pill'>ruka</span>" if c["status"] == "paused" else "", _esc(c["mobile"]), _esc(c["mobile"] or "—"),
                   _short(s["last"]) if s["last"] else "—", s["visits"], _r(s["charged"]), _r(s["received"]), _r(s["due"])))
        (closed if c["status"] == "closed" else run).append(row)
    hd = ("<thead><tr><th>Patient</th><th>Aakhri visit</th><th class='r'>Visits</th><th class='r'>Charge</th><th class='r'>Mila</th>"
          "<th class='r'>Baaki</th></tr></thead>")
    out.append("<div class='card'><h2>Ghar ke patient</h2>%s</div>" % (
        "<table class='grid'>%s<tbody>%s</tbody></table>" % (hd, "".join(run)) if run else "<p class='mut'>Abhi koi nahi.</p>"))
    if closed:
        out.append("<details class='card'><summary>Band (%d)</summary><table class='grid'>%s<tbody>%s</tbody></table></details>" % (len(closed), hd, "".join(closed)))
    return "".join(out)


@bp.route("/finance/physio/book/home/<int:cid>")
def home_patient(cid):
    u, roles, err = _gate()
    if err:
        return err
    con = _db()
    _ensure(con)
    checker = "checker" in roles
    if not is_on(con) and not checker:
        return _shell("Physio register", "<div class='card'><h2>Physio register</h2><p class='big'>%s</p></div>" % OFF_LINE)
    c = _course(con, cid)
    if not c or c["kind"] != "home":
        return _back("/finance/physio/book", tab="home", err="gone")
    head = _head(con, "home", checker, request.args)
    s = course_sums(con, cid)
    back = "/finance/physio/book/home/%d" % cid
    out = [head, "<div class='card'><h2>%s</h2><p><a href='tel:%s' class='big'>%s</a></p>" % (_esc(c["name"]), _esc(c["mobile"]), _esc(c["mobile"] or "—"))]
    if c["clinic_id"]:
        out.append("<p>Clinic ID: <b>%s</b></p>" % _esc(c["clinic_id"]))
    else:
        out.append("<form method='post' action='/finance/physio/book/patient/cid' class='row'><input type='hidden' name='pid' value='%d'>"
                   "<input type='hidden' name='back' value='%s'><input name='clinic_id' class='note' placeholder='Clinic ID' maxlength='20'>"
                   "<button type='submit' class='save'>Clinic ID jodo</button></form>" % (c["patient_id"], back))
    st = {"active": "chal raha hai", "paused": "ruka hua", "closed": "band"}[c["status"]]
    out.append("<table class='grid'><tbody><tr><th class='sec'>Haal</th><td>%s</td></tr><tr><th class='sec'>Ek visit</th><td class='r'>%s</td></tr>"
               "<tr><th class='sec'>Visits</th><td class='r'>%d</td></tr><tr><th class='sec'>Charge</th><td class='r'>%s</td></tr>"
               "<tr><th class='sec'>Payment received</th><td class='r'>%s</td></tr><tr><th class='sec'>Baaki</th><td class='r'><b>%s</b></td></tr>"
               "</tbody></table></div>" % (st, _r(c["rate_p"]), s["visits"], _r(s["charged"]), _r(s["received"]), _r(s["due"])))
    days = "".join("<option value='%s'>%s</option>" % (d, _short(d)) for d in _days_back())
    if c["status"] == "active":
        out.append("<div class='card'><form method='post' action='/finance/physio/book/home/visit' class='entry'><input type='hidden' name='course' value='%d'>"
                   "<table class='grid nums'><tbody><tr><th class='sec'>Din</th><td><select name='day' class='note'>%s</select></td></tr>"
                   "<tr><th class='sec'>Amount ₹</th><td><input name='amount' class='amt' inputmode='decimal' value='%s'></td></tr></tbody></table>"
                   "<button type='submit' class='big cash'>Aaj visit hua ✓</button></form></div>" % (cid, days, "{:g}".format(c["rate_p"] / 100.0)))
    out.append("<div class='card'><form method='post' action='/finance/physio/book/home/pay' class='entry'><input type='hidden' name='course' value='%d'>"
               "<table class='grid nums'><tbody><tr><th class='sec'>Amount ₹</th><td><input name='amount' class='amt' inputmode='decimal' value='%s'></td></tr>"
               "<tr><th class='sec'>Tareekh</th><td><input type='date' name='day' class='note' value='%s' max='%s'></td></tr></tbody></table>"
               "<p><b>Payment received</b></p><div class='two'><button type='submit' name='mode' value='cash' class='big cash'>Cash</button>"
               "<button type='submit' name='mode' value='upi' class='big upi'>UPI</button></div></form></div>" % (
                   cid, ("{:g}".format(s["due"] / 100.0)) if s["due"] > 0 else "", _today().isoformat(), _today().isoformat()))
    sb = []
    if c["status"] == "active":
        sb.append(("paused", "Rok do"))
    if c["status"] in ("paused", "closed"):
        sb.append(("active", "Phir shuru"))
    if c["status"] != "closed":
        sb.append(("closed", "Band karo"))
    out.append("<div class='card'>%s</div>" % "".join(
        "<form method='post' action='/finance/physio/book/home/status' class='inline'><input type='hidden' name='course' value='%d'>"
        "<input type='hidden' name='status' value='%s'><button type='submit' class='%s'>%s</button></form>" % (
            cid, k, "clear" if k == "closed" else "save", w) for k, w in sb))
    hist = []
    for r in con.execute("SELECT 'session' AS k, id, day, amount_p, mode, voided_at, void_why FROM physio_session WHERE course_id=? "
                         "UNION ALL SELECT 'payment', id, day, amount_p, mode, voided_at, void_why FROM physio_payment WHERE course_id=? "
                         "ORDER BY day DESC, k, id DESC", (cid, cid)):
        what = "Visit" if r["k"] == "session" else "Payment received (%s)" % (r["mode"] or "").upper()
        if r["voided_at"]:
            hist.append("<tr class='void'><td>%s</td><td>%s</td><td class='r'>%s</td><td>hata di (%s)</td></tr>" % (
                _short(r["day"]), what, _r(r["amount_p"]), _esc(dict(VOID_WHY).get(r["void_why"], r["void_why"]))))
        else:
            hist.append("<tr><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td></tr>" % (
                _short(r["day"]), what, _r(r["amount_p"]), _void_form(r["k"], r["id"], back)))
    out.append("<div class='card'><h2>Hisaab</h2>%s<p><a class='btn' href='/finance/physio/book?tab=home'>‹ Ghar ke patient</a></p></div>" % (
        "<table class='grid'><tbody>%s</tbody></table>" % "".join(hist) if hist else "<p class='mut'>Abhi kuch nahi.</p>"))
    return _shell("Physio register", "".join(out))


# ---------------------------------------------------------------- writes
def _write_gate():
    """(user, who, con, error_redirect) for a POST: maker while on, checker always."""
    u, roles, err = _gate()
    if err:
        return None, "", None, err
    con = _db()
    _ensure(con)
    if not is_on(con) and "checker" not in roles:
        return None, "", None, _back("/finance/physio/book", err="off")
    return u, u.get("user", ""), con, None


@bp.route("/finance/physio/book/slip", methods=["POST"])
def post_slip():
    u, who, con, err = _write_gate()
    if err:
        return err
    f = request.form
    day = f.get("day") or ""
    keep = dict(day=day, pick=f.get("pick") or "")
    if not _day_ok(day):
        return _back("/finance/physio/book", err="day")
    n = (f.get("slip_no") or "").strip()
    if not n.isdigit() or not (0 < int(n) < 10 ** 9):
        return _back("/finance/physio/book", err="slipno", **keep)
    n = int(n)
    amt = _paise(f.get("amount"))
    if amt is None:
        return _back("/finance/physio/book", err="amount", **keep)
    mode = f.get("mode") or ""
    if mode not in ("cash", "upi"):
        return _back("/finance/physio/book", err="mode", **keep)
    if slip_owner(con, n):
        return _back("/finance/physio/book", err="dup", n=n, **keep)
    pid, e = _patient_from_form(con, f, who)
    if e:
        con.rollback()
        return _back("/finance/physio/book", err=e, **keep)
    cid = _course_for(con, pid, "clinic", _int_setting(con, CLINIC_RATE_KEY, CLINIC_RATE_P), who)
    try:
        cur = con.execute("INSERT INTO physio_session (course_id, day, slip_no, amount_p, mode, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                          (cid, day, n, amt, mode, who, _stamp()))
    except Exception:                            # noqa: BLE001 -- the unique index: another tap took the slip first
        con.rollback()
        return _back("/finance/physio/book", err="dup", n=n, **keep)
    con.commit()
    _audit_safe(con, "physio_session", cur.lastrowid, "insert", None, dict(course_id=cid, day=day, slip_no=n, amount_p=amt, mode=mode), who)
    return _back("/finance/physio/book", day=day, msg="saved")


@bp.route("/finance/physio/book/void", methods=["POST"])
def post_void():
    u, who, con, err = _write_gate()
    if err:
        return err
    f = request.form
    back = f.get("back") or "/finance/physio/book"
    if not back.startswith("/finance/physio/book"):
        back = "/finance/physio/book"
    sep = "&" if "?" in back else "?"
    kind, rid, why = f.get("kind"), f.get("id") or "", f.get("why") or ""
    table = {"session": "physio_session", "payment": "physio_payment"}.get(kind)
    if not table or not rid.isdigit():
        return redirect(back + sep + "err=gone")
    if why not in dict(VOID_WHY):
        return redirect(back + sep + "err=why")
    r = con.execute("SELECT * FROM %s WHERE id=? AND voided_at=''" % table, (int(rid),)).fetchone()
    if not r:
        return redirect(back + sep + "err=gone")
    con.execute("UPDATE %s SET voided_at=?, voided_by=?, void_why=? WHERE id=? AND voided_at=''" % table, (_stamp(), who, why, int(rid)))
    con.commit()
    _audit_safe(con, table, int(rid), "void", dict(day=r["day"], amount_p=r["amount_p"]), dict(why=why), who)
    return redirect(back + sep + "msg=voided")


@bp.route("/finance/physio/book/home/new", methods=["POST"])
def post_home_new():
    u, who, con, err = _write_gate()
    if err:
        return err
    f = request.form
    rate = _paise(f.get("rate"))
    if rate is None:
        return _back("/finance/physio/book", tab="home", err="amount", pick=f.get("pick") or "")
    key = (f.get("pick") or "").strip()
    pid, e = _patient_from_form(con, f, who)
    mob = _mobile(f.get("mobile")) if key and not e else None
    if mob:                                      # a picked patient with no mobile yet: the one typed here is kept (never changed once set)
        p = patient(con, pid)
        if p and not p["mobile"]:
            con.execute("UPDATE physio_patient SET mobile=? WHERE id=? AND mobile=''", (mob, pid))
            _audit_safe(con, "physio_patient", pid, "mobile", None, dict(mobile=_mask(mob)), who)
    if e:
        con.rollback()
        return _back("/finance/physio/book", tab="home", err=e, pick=key)
    have = con.execute("SELECT id FROM physio_course WHERE patient_id=? AND kind='home' AND status<>'closed'", (pid,)).fetchone()
    if have:
        con.commit()
        return _back("/finance/physio/book/home/%d" % have["id"], err="exists")
    cur = con.execute("INSERT INTO physio_course (patient_id, kind, rate_p, status, started, changed_at, changed_by) VALUES (?,?,?,?,?,?,?)",
                      (pid, "home", rate, "active", _today().isoformat(), _stamp(), who))
    con.commit()
    _audit_safe(con, "physio_course", cur.lastrowid, "insert", None, dict(patient_id=pid, kind="home", rate_p=rate), who)
    return _back("/finance/physio/book/home/%d" % cur.lastrowid, msg="newhome")


def _home_course(con, f):
    c = f.get("course") or ""
    if not c.isdigit():
        return None
    r = _course(con, int(c))
    return r if r and r["kind"] == "home" else None


@bp.route("/finance/physio/book/home/visit", methods=["POST"])
def post_home_visit():
    u, who, con, err = _write_gate()
    if err:
        return err
    f = request.form
    c = _home_course(con, f)
    if not c:
        return _back("/finance/physio/book", tab="home", err="gone")
    path = "/finance/physio/book/home/%d" % c["id"]
    if c["status"] != "active":
        return _back(path, err="notactive")
    day = f.get("day") or ""
    if not _day_ok(day):
        return _back(path, err="day")
    amt = _paise(f.get("amount"))
    if amt is None:
        return _back(path, err="amount")
    cur = con.execute("INSERT INTO physio_session (course_id, day, slip_no, amount_p, mode, by_whom, at) VALUES (?,?,NULL,?,'',?,?)",
                      (c["id"], day, amt, who, _stamp()))
    con.commit()
    _audit_safe(con, "physio_session", cur.lastrowid, "insert", None, dict(course_id=c["id"], day=day, amount_p=amt, home=1), who)
    return _back(path, msg="visit")


@bp.route("/finance/physio/book/home/pay", methods=["POST"])
def post_home_pay():
    u, who, con, err = _write_gate()
    if err:
        return err
    f = request.form
    c = _home_course(con, f)
    if not c:
        return _back("/finance/physio/book", tab="home", err="gone")
    path = "/finance/physio/book/home/%d" % c["id"]
    day = f.get("day") or ""
    if not _iso_ok(day) or day > _today().isoformat() or day < (_today() - dt.timedelta(days=366)).isoformat():
        return _back(path, err="pday")
    amt = _paise(f.get("amount"))
    if amt is None:
        return _back(path, err="amount")
    mode = f.get("mode") or ""
    if mode not in ("cash", "upi"):
        return _back(path, err="mode")
    cur = con.execute("INSERT INTO physio_payment (course_id, day, amount_p, mode, by_whom, at) VALUES (?,?,?,?,?,?)",
                      (c["id"], day, amt, mode, who, _stamp()))
    con.commit()
    _audit_safe(con, "physio_payment", cur.lastrowid, "insert", None, dict(course_id=c["id"], day=day, amount_p=amt, mode=mode), who)
    return _back(path, msg="paid")


@bp.route("/finance/physio/book/home/status", methods=["POST"])
def post_home_status():
    u, who, con, err = _write_gate()
    if err:
        return err
    f = request.form
    c = _home_course(con, f)
    if not c:
        return _back("/finance/physio/book", tab="home", err="gone")
    st = f.get("status") or ""
    path = "/finance/physio/book/home/%d" % c["id"]
    if st not in ("active", "paused", "closed") or st == c["status"]:
        return _back(path)
    con.execute("UPDATE physio_course SET status=?, changed_at=?, changed_by=? WHERE id=?", (st, _stamp(), who, c["id"]))
    con.commit()
    _audit_safe(con, "physio_course", c["id"], "status", dict(status=c["status"]), dict(status=st), who)
    return _back(path, msg="status")


@bp.route("/finance/physio/book/patient/cid", methods=["POST"])
def post_clinic_id():
    u, who, con, err = _write_gate()
    if err:
        return err
    f = request.form
    back = f.get("back") or "/finance/physio/book"
    if not back.startswith("/finance/physio/book"):
        back = "/finance/physio/book"
    sep = "&" if "?" in back else "?"
    pid = f.get("pid") or ""
    cid = re.sub(r"\s+", "", f.get("clinic_id") or "")[:20]
    p = patient(con, int(pid)) if pid.isdigit() else None
    if not p:
        return redirect(back + sep + "err=gone")
    if p["clinic_id"]:
        return redirect(back + sep + "err=cidset")
    if not re.fullmatch(r"[A-Za-z0-9/\-]{2,20}", cid):
        return redirect(back + sep + "err=cidbad")
    if con.execute("SELECT 1 FROM physio_patient WHERE clinic_id=? AND id<>?", (cid, p["id"])).fetchone():
        return redirect(back + sep + "err=cidtaken")
    con.execute("UPDATE physio_patient SET clinic_id=? WHERE id=? AND clinic_id=''", (cid, p["id"]))
    con.commit()
    _audit_safe(con, "physio_patient", p["id"], "clinic_id", None, dict(clinic_id=cid), who)
    return redirect(back + sep + "msg=cid")


# ---------------------------------------------------------------- the owner's report
def _month_bounds(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    return first.isoformat(), last.isoformat()


def month_days(con, first, last):
    """Day-wise rows of the month (any day with a slip, a reception figure, a home visit or a home payment)."""
    days = set()
    for sql in ("SELECT DISTINCT s.day FROM physio_session s WHERE s.voided_at='' AND s.day BETWEEN ? AND ?",
                "SELECT DISTINCT day FROM physio_payment WHERE voided_at='' AND day BETWEEN ? AND ?",
                "SELECT DISTINCT business_date FROM clinic_physio_day WHERE business_date BETWEEN ? AND ?"):
        try:
            days.update(r[0] for r in con.execute(sql, (first, last)))
        except Exception:                        # noqa: BLE001
            pass
    floor = first_clinic_day(con)
    out = []
    for d in sorted(days):
        m = day_match(con, d)
        h = con.execute("SELECT COUNT(*), COALESCE(SUM(s.amount_p),0) FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                        "WHERE c.kind='home' AND s.day=? AND s.voided_at=''", (d,)).fetchone()
        p = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM physio_payment WHERE day=? AND voided_at=''", (d,)).fetchone()
        m.update(h_n=h[0], h_p=h[1], h_rec=p[0], before=(not floor or d < floor))
        out.append(m)
    return out


def patient_rows(con, kind, first, last):
    out = []
    for c in con.execute("SELECT c.*, p.name, p.mobile, p.clinic_id FROM physio_course c JOIN physio_patient p ON p.id=c.patient_id "
                         "WHERE c.kind=? ORDER BY p.name COLLATE NOCASE", (kind,)):
        mo = course_sums(con, c["id"], first, last)
        al = course_sums(con, c["id"])
        if kind == "clinic":
            if not mo["visits"]:
                continue
            rec = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM physio_session WHERE course_id=? AND voided_at='' AND mode IN ('cash','upi') "
                              "AND day BETWEEN ? AND ?", (c["id"], first, last)).fetchone()[0]
            out.append(dict(name=c["name"], cid=c["clinic_id"], mobile=c["mobile"], status=c["status"], n=mo["visits"], charged=mo["charged"],
                            received=rec, due=mo["charged"] - rec, last=al["last"]))
        else:
            if not (mo["visits"] or mo["received"] or al["due"] or c["status"] != "closed"):
                continue
            out.append(dict(name=c["name"], cid=c["clinic_id"], mobile=c["mobile"], status=c["status"], n=mo["visits"], charged=mo["charged"],
                            received=mo["received"], due=al["due"], last=al["last"]))
    return out


@bp.route("/finance/physio/book/report")
def report_page():
    u, err = _require("checker", unit=_unit)
    if err:
        return _shell("Physio register — report", "<div class='card'><h2>Not permitted</h2><p>This report is for the doctors.</p></div>"), 403
    con = _db()
    _ensure(con)
    ym = request.args.get("m") or _today().strftime("%Y-%m")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", ym):
        ym = _today().strftime("%Y-%m")
    first, last = _month_bounds(ym)
    on = is_on(con)
    out = []
    msg = {"on": "✓ The register is open for Bhati.", "off": "✓ The register is closed for Bhati."}.get(request.args.get("msg") or "")
    if msg:
        out.append("<div class='ok'>%s</div>" % msg)
    out.append("<div class='card'><h2>Physio register — %s</h2><p>For Bhati the register is <b>%s</b>.</p>"
               "<form method='post' action='/finance/physio/book/switch' class='inline'><input type='hidden' name='on' value='%s'>"
               "<button type='submit' class='%s'>%s</button></form> <a class='btn' href='/finance/physio/book'>Bhati's page ›</a>"
               "<a class='btn' href='/finance/physio'>Reception's physiotherapy table ›</a></div>" % (
                   dt.date.fromisoformat(first).strftime("%B %Y"), "OPEN" if on else "CLOSED (only the doctors see it)",
                   "0" if on else "1", "clear" if on else "save", "Close it" if on else "Open the register for Bhati"))
    y0 = int(ym[:4])
    t = _today()
    keys = []
    for i in range(0, 14):
        yy, mn = t.year, t.month - i
        while mn <= 0:
            mn += 12
            yy -= 1
        keys.append("%04d-%02d" % (yy, mn))
    if ym not in keys:
        keys.insert(0, ym)
    opts = ["<option value='%s'%s>%s</option>" % (k, " selected" if k == ym else "", dt.date(int(k[:4]), int(k[5:7]), 1).strftime("%B %Y"))
            for k in keys]
    out.append("<form method='get' class='row'><select name='m' class='note'>%s</select><button type='submit' class='save'>Show</button></form>" % "".join(opts))
    diffs = differ_days(con, first, last)
    if diffs:
        out.append("<div class='bad'><b>%d %s — reception and Bhati</b><ul>%s</ul></div>" % (
            len(diffs), "day differs" if len(diffs) == 1 else "days differ", "".join(
                "<li>%s: Bhati cash %s, UPI %s · reception cash %s, UPI %s</li>" % (
                    _human(m["day"]), _r(m["b_cash"]), _r(m["b_upi"]), _r(m["r_cash"]), _r(m["r_upi"])) for m in diffs)))
    rows = month_days(con, first, last)
    tot = dict(n=0, bc=0, bu=0, rc=0, ru=0, hn=0, hp=0, hr=0)
    body = []
    for m in rows:
        if m["before"] and not m["n"]:
            match = "<span class='mut'>before the register</span>"
        elif not m["has_r"]:
            match = "reception not written"
        elif m["agree"]:
            match = "✓"
        else:
            match = "<b class='badv'>cash %s · UPI %s</b>" % (_r(m["b_cash"] - m["r_cash"]), _r(m["b_upi"] - m["r_upi"]))
        body.append("<tr><td class='d'>%s</td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td>"
                    "<td>%s</td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td></tr>" % (
                        _short(m["day"]), m["n"], _r(m["b_cash"]), _r(m["b_upi"]), _r(m["r_cash"]) if m["has_r"] else "—",
                        _r(m["r_upi"]) if m["has_r"] else "—", match, m["h_n"], _r(m["h_p"]), _r(m["h_rec"])))
        tot["n"] += m["n"]
        tot["bc"] += m["b_cash"]
        tot["bu"] += m["b_upi"]
        tot["rc"] += m["r_cash"]
        tot["ru"] += m["r_upi"]
        tot["hn"] += m["h_n"]
        tot["hp"] += m["h_p"]
        tot["hr"] += m["h_rec"]
    out.append("<div class='card'><h2>Day-wise</h2>%s</div>" % (
        "<table class='grid'><thead><tr><th>Day</th><th class='r'>Clinic sessions</th><th class='r'>Cash</th><th class='r'>UPI</th>"
        "<th class='r'>Reception cash</th><th class='r'>Reception UPI</th><th>Match</th><th class='r'>Home visits</th><th class='r'>Home charges</th>"
        "<th class='r'>Home received</th></tr></thead><tbody>%s</tbody><tfoot><tr><td>Month</td><td class='r'>%d</td><td class='r'>%s</td>"
        "<td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td><td></td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td></tr></tfoot></table>" % (
            "".join(body), tot["n"], _r(tot["bc"]), _r(tot["bu"]), _r(tot["rc"]), _r(tot["ru"]), tot["hn"], _r(tot["hp"]), _r(tot["hr"]))
        if body else "<p class='mut'>Nothing this month.</p>"))
    for kind, title in (("clinic", "Patient-wise — clinic"), ("home", "Patient-wise — home visits (Bhati's own money; not in the accountants' income)")):
        pr = patient_rows(con, kind, first, last)
        b = "".join("<tr><td><b>%s</b>%s<br><span class='mut'>%s</span></td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td>"
                    "<td class='r'><b>%s</b></td><td>%s</td></tr>" % (
                        _esc(r["name"]), (" · " + _esc(r["cid"])) if r["cid"] else "", _esc(_mask(r["mobile"])) + (" · %s" % r["status"] if kind == "home" else ""),
                        r["n"], _r(r["charged"]), _r(r["received"]), _r(r["due"]), _human(r["last"]) if r["last"] else "—") for r in pr)
        out.append("<div class='card'><h2>%s</h2>%s</div>" % (title, (
            "<table class='grid'><thead><tr><th>Patient</th><th class='r'>Sessions (month)</th><th class='r'>Charged (month)</th>"
            "<th class='r'>Received (month)</th><th class='r'>Due (to date)</th><th>Last visit</th></tr></thead><tbody>%s</tbody></table>" % b)
            if pr else "<p class='mut'>None this month.</p>"))
    yr = []
    ty = [0] * 6
    for mn in range(1, 13):
        k = "%04d-%02d" % (y0, mn)
        f1, l1 = _month_bounds(k)
        c = con.execute("SELECT COUNT(*), COALESCE(SUM(CASE WHEN s.mode='cash' THEN s.amount_p END),0), COALESCE(SUM(CASE WHEN s.mode='upi' THEN s.amount_p END),0) "
                        "FROM physio_session s JOIN physio_course c ON c.id=s.course_id WHERE c.kind='clinic' AND s.voided_at='' AND s.day BETWEEN ? AND ?", (f1, l1)).fetchone()
        h = con.execute("SELECT COUNT(*), COALESCE(SUM(s.amount_p),0) FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                        "WHERE c.kind='home' AND s.voided_at='' AND s.day BETWEEN ? AND ?", (f1, l1)).fetchone()
        p = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM physio_payment WHERE voided_at='' AND day BETWEEN ? AND ?", (f1, l1)).fetchone()
        vals = [c[0], c[1], c[2], h[0], h[1], p[0]]
        if any(vals):
            ty = [a + b for a, b in zip(ty, vals)]
            yr.append("<tr%s><td>%s</td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td></tr>" % (
                " class='cur'" if k == ym else "", dt.date(y0, mn, 1).strftime("%B"), vals[0], _r(vals[1]), _r(vals[2]), vals[3], _r(vals[4]), _r(vals[5])))
    out.append("<div class='card'><h2>Month totals — %d</h2>%s</div>" % (y0, (
        "<table class='grid'><thead><tr><th>Month</th><th class='r'>Clinic sessions</th><th class='r'>Clinic cash</th><th class='r'>Clinic UPI</th>"
        "<th class='r'>Home visits</th><th class='r'>Home charges</th><th class='r'>Home received</th></tr></thead><tbody>%s</tbody>"
        "<tfoot><tr><td>Year</td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%d</td><td class='r'>%s</td><td class='r'>%s</td></tr></tfoot></table>" % (
            "".join(yr), ty[0], _r(ty[1]), _r(ty[2]), ty[3], _r(ty[4]), _r(ty[5]))) if yr else "<p class='mut'>Nothing this year yet.</p>"))
    out.append("<p class='mut'>Home visits are Bhati's own money: they appear only here and on his page — never in the accountants' pack, "
               "the day revenue or the morning match. Reception's figures are read from the physiotherapy table (the counter sheet); this "
               "register never writes them.</p>")
    return _shell("Physio register — report", "".join(out), lang="en")


@bp.route("/finance/physio/book/switch", methods=["POST"])
def post_switch():
    u, err = _require("checker", unit=_unit)
    if err:
        return err
    con = _db()
    _ensure(con)
    want = "1" if request.form.get("on") == "1" else "0"
    before = _setting(con, ON_KEY, "0")
    who = u.get("user", "")
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                (ON_KEY, want, "S552: 1 = Bhati's physio register open for him; 0 = only the doctors see it"))
    con.commit()
    _audit_safe(con, "setting", 0, "physio_book.on", dict(value=before), dict(value=want), who)
    return redirect("/finance/physio/book/report?msg=%s" % ("on" if want == "1" else "off"))


# ---------------------------------------------------------------- shell
def _shell(title, body, lang="hi"):
    """The counter sheet's large-type, high-contrast look (as clinic_money's)."""
    return """<!doctype html><html lang="%s"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#3c464e;--line:#8a9aa6;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;--entry:#fffbe6}
*{box-sizing:border-box}
body{margin:0;padding:14px;background:var(--bg);color:var(--ink);font:19px/1.6 "Segoe UI",system-ui,-apple-system,sans-serif}
h1{font-size:23px;margin:0 0 12px;color:var(--accent);font-weight:700}
h2{font-size:21px;margin:0 0 10px;color:var(--accent)}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px;overflow-x:auto}
details.card summary,details summary{cursor:pointer;font-size:19px;color:var(--accent);font-weight:600}
.mut{color:var(--mut);font-size:16px}.big{font-size:22px;font-weight:600}
table.grid{width:100%%;border-collapse:collapse;font-size:18px}
.grid th,.grid td{border:2px solid var(--line);padding:9px;vertical-align:top}
.grid thead th{background:#cfdae3;font-size:16px}
.r{text-align:right;white-space:nowrap}.d{white-space:nowrap;font-weight:600}
.sec{text-align:left;background:#eef2f5;font-size:17px;white-space:normal;width:34%%}
tfoot td{background:#dff0d8;font-weight:700}
tr.void td{color:#7a858d;text-decoration:line-through}tr.cur td{background:#eef4fb}
input.amt{width:100%%;min-height:54px;font-size:24px;padding:8px 12px;border:2px solid #5b6b76;border-radius:8px;text-align:right;background:var(--entry)}
.note{width:100%%;min-height:50px;padding:9px;border:2px solid #5b6b76;border-radius:8px;font-size:19px;background:var(--entry)}
select.note{background:#fff}
.row{display:flex;gap:8px;align-items:center;margin:0 0 10px}.row .note{flex:1}
button.save{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:14px 22px;font-size:19px;font-weight:600;cursor:pointer;margin-top:6px}
button.clear{background:var(--paper);color:#8c2f2f;border:2px solid #8c2f2f;border-radius:9px;padding:11px 16px;font-size:17px;cursor:pointer;margin-top:6px}
.two{display:flex;gap:12px;margin-top:10px}
button.big{flex:1;min-height:70px;font-size:24px;font-weight:700;border:0;border-radius:12px;color:#fff;cursor:pointer;padding:10px 18px}
button.cash{background:#2c6e2f}button.upi{background:#5a3d8a}
.inline{display:inline-block;margin-right:10px}
a.btn{display:inline-block;border:2px solid var(--accent);color:var(--accent);border-radius:9px;padding:10px 14px;text-decoration:none;font-size:17px;margin:6px 8px 0 0;background:var(--paper)}
.tabs{display:flex;gap:8px;margin:0 0 14px;flex-wrap:wrap}
a.tab{flex:1;text-align:center;border:2px solid var(--accent);border-radius:10px;padding:12px;font-size:20px;font-weight:600;color:var(--accent);background:var(--paper);text-decoration:none}
a.tab.on{background:var(--accent);color:#fff}
.days{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 14px}
a.dayb{border:2px solid var(--line);border-radius:8px;padding:8px 10px;font-size:16px;color:var(--ink);background:var(--paper);text-decoration:none}
a.dayb.on{border-color:var(--accent);background:var(--accent);color:#fff}
a.pick{display:block;border:2px solid var(--line);border-radius:9px;padding:12px;margin:6px 0;color:var(--ink);background:#fff;text-decoration:none;font-size:19px}
.newp{margin-top:12px}
.vd summary{font-size:15px;color:#8c2f2f;font-weight:400}
.ok{background:#dff0d8;border-left:6px solid #2c6e2f;padding:12px 15px;margin-bottom:14px}
.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:12px 15px;margin-bottom:14px}
.verdict{font-weight:700;margin:12px 0 6px;font-size:21px}.good{color:#2c6e2f}.badv{color:#9c2a20}.wait{color:#8a5a00}
.pill{font-size:14px;padding:2px 9px;border-radius:12px;background:#e3e8eb;border:1px solid var(--line);white-space:nowrap}
@media (max-width:620px){body{padding:10px}.card{padding:12px}table.grid{font-size:16px}.grid th,.grid td{padding:6px 5px}.sec{font-size:15px}
 a.btn{display:block;text-align:center;margin:8px 0 0}.inline{display:block;margin:6px 0 0}}
</style></head><body><h1>Dr. Manoj Agarwal Clinic — %s</h1>
%s</body></html>""" % (lang, _esc(title), _esc(title), body)
