#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
petty_book.py -- S289 (17-Sep-2026). Manoj Bhati's petty book, and the doctors' check of it.

THE OWNER, 17-Sep-2026, in his own words, folded:
  * Manoj Bhati is NOT an employee, he is associated with the clinic: no biometric, no leave, no
    salary rows. "It would be a good way if we know whether he is available on that day or not."
  * Shavez and Darpan each keep a small diary for petty expenses. Bhati checks the diary and
    "whatever shortage is there he replenishes the amount with the money he is provided from me or
    Dr. Bhawna. So his work is to monitor and replenish. And periodically we also check these three."
  * "No entry of this part is there in any Sanjeevni or doctor's system. This is totally
    independent system." -- so this module reads and writes ONLY its own petty_* tables (plus a
    read-only look at the physiotherapy table for Bhati's daily tick).
  * "His flow should be minimum typing or no typing and only tapping and selecting. Typing should
    be in exceptional cases only." -- every payee, reason and person is a button; amounts come
    from the number pad; the only text box is the name of a payee who is not on the list.
  * He pays for the current renovation as and when required: Hari Om Ji (electrical contractor),
    Nanne (civil contractor), Bhavani (tiles contractor), Ilyas (carpentry contractor), Mittal
    Electric (electrical material), Raja (fabricator, iron work), others by name. AC technician
    removed. Cartage and small construction costs under the construction head.
  * Rahul, social media manager: Rs 5,000 every month.
  * Occasionally Bhati takes money for personal use as a loan.
  * Amounts to hold: Manoj Bhati Rs 10,000, Darpan Rs 3,000, Shavez Rs 3,000.
  * Bhati's flow as far as possible in Hindi; the owner's page in English.

WHO REACHES WHAT -- at the SERVER, never by hiding a tile (F-84). Its own unit, 'petty':
  maker   = the keeper (bhati)      -> his Hindi screens only
  checker = the doctors             -> the English check page, confirm money given, OK loans, counts
  viewer  = reception               -> ONE line: is Bhati available today
A login with no row in 'petty' is refused by finance_app's front gate before any route runs.

ARITHMETIC (paise, integers):
  Bhati in hand = money received - top-ups given - payments - loans taken + loans repaid
  He needs      = his amount to hold - in hand, when positive (shown, never a refusal)
  Loan owed     = loans taken - loans repaid (kept apart; never an expense)
  A cancelled entry counts nowhere and stays in the list, struck through, with who cancelled it.

S300 (17-Sep-2026 evening) -- THE OPENING BALANCE, the owner: "also need to add opening balance
of bhati, in his cash and loan sections".
  * table petty_opening: one row for 'cash' (what Bhati already held when the book started) and one
    for 'loan' (what he already owed). Created on first request like every petty table.
  * a DOCTOR sets or corrects either figure on the English page (zero allowed); Bhati sees both on
    his own page and cannot change them. Every set is audited with the figure before and after.
  * Bhati in hand = opening cash + money received - top-ups - payments - loans taken + loans repaid
    Loan owed    = opening loan + loans taken - loans repaid

S393 (24-Sep-2026) -- the owner: "maximum sections visible on a single screen without scrolling, as a collapsible
expandable system". Both pages are folds (details/summary, name='pb' = one open at a time, still no JavaScript): a
strip with the figures that matter is always on screen, each section shows its one-line figure, detail on a tap.
And the same entry by the same person within 10 minutes is refused (a 9,000 top-up had been saved three times).

NO JAVASCRIPT. Tables on first request, never at import (F-303). Every write audited.
"""
import datetime as dt
import os
import uuid

from flask import Blueprint, redirect, request, send_file

bp = Blueprint("petty_book", __name__)
_db = None
_require = None
_audit = None
UNIT = "petty"
APP_VERSION = "S393-PETTY-BOOK-1.2"
_schema_done = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS petty_holder (
    code      TEXT PRIMARY KEY,            -- bhati | darpan | shavez
    name      TEXT NOT NULL,
    hold_p    INTEGER NOT NULL,            -- the amount this person should hold
    keeper    INTEGER NOT NULL DEFAULT 0,  -- 1 = the one who replenishes the others
    sort      INTEGER NOT NULL DEFAULT 0,
    active    INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS petty_payee (
    code      TEXT PRIMARY KEY,
    name      TEXT NOT NULL,               -- as the owner said it
    what_hi   TEXT NOT NULL DEFAULT '',    -- Bhati's label (Hinglish)
    what_en   TEXT NOT NULL DEFAULT '',
    head      TEXT NOT NULL,               -- construction | monthly
    default_p INTEGER NOT NULL DEFAULT 0,  -- pre-filled amount (Rahul)
    sort      INTEGER NOT NULL DEFAULT 0,
    active    INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS petty_entry (
    id          INTEGER PRIMARY KEY,
    entry_date  TEXT NOT NULL,             -- the server's day
    kind        TEXT NOT NULL CHECK (kind IN ('receive','topup','pay','loan_out','loan_back')),
    party       TEXT NOT NULL DEFAULT '',  -- receive: manoj|bhawna · topup: darpan|shavez · pay: payee code or 'other'
    other_name  TEXT NOT NULL DEFAULT '',  -- pay to someone not on the list (the only typing)
    amount_p    INTEGER NOT NULL CHECK (amount_p > 0),
    photo       TEXT NOT NULL DEFAULT '',  -- stored file name under the upload folder
    by_whom     TEXT NOT NULL,
    at          TEXT NOT NULL,
    confirm_by  TEXT NOT NULL DEFAULT '',  -- receive: the doctor confirms · loan_out: the doctor OKs
    confirm_at  TEXT NOT NULL DEFAULT '',
    void_by     TEXT NOT NULL DEFAULT '',
    void_at     TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS petty_entry_date ON petty_entry(entry_date);
CREATE TABLE IF NOT EXISTS petty_count (
    id          INTEGER PRIMARY KEY,
    holder      TEXT NOT NULL,
    short_p     INTEGER NOT NULL DEFAULT 0,   -- 0 = matches
    by_whom     TEXT NOT NULL,
    at          TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS petty_available (
    day         TEXT PRIMARY KEY,
    status      TEXT NOT NULL CHECK (status IN ('yes','no')),
    by_whom     TEXT NOT NULL,
    at          TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS petty_opening (      -- S300: what Bhati held / owed when the book started
    what        TEXT PRIMARY KEY CHECK (what IN ('cash','loan')),
    amount_p    INTEGER NOT NULL CHECK (amount_p >= 0),
    by_whom     TEXT NOT NULL,
    at          TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS petty_physio_check (
    business_date TEXT PRIMARY KEY,
    by_whom     TEXT NOT NULL,
    at          TEXT NOT NULL
);
"""

HOLDERS = [("bhati", "Manoj Bhati", 1000000, 1, 1),
           ("darpan", "Darpan", 300000, 0, 2),
           ("shavez", "Shavez", 300000, 0, 3)]
PAYEES = [("hariom", "Hari Om Ji", "Bijli thekedaar", "Electrical contractor", "construction", 0, 1),
          ("nanne", "Nanne", "Civil thekedaar", "Civil contractor", "construction", 0, 2),
          ("bhavani", "Bhavani", "Tiles thekedaar", "Tiles contractor", "construction", 0, 3),
          ("ilyas", "Ilyas", "Carpenter thekedaar", "Carpentry contractor", "construction", 0, 4),
          ("mittal", "Mittal Electric", "Bijli ka saamaan", "Electrical material", "construction", 0, 5),
          ("raja", "Raja", "Fabricator (lohe ka kaam)", "Fabricator, iron work", "construction", 0, 6),
          ("cartage", "Cartage / chhota kharcha", "Dhulai, chhota kharcha", "Cartage, small costs", "construction", 0, 7),
          ("rahul", "Rahul", "Social media manager (mahina)", "Social media manager (monthly)", "monthly", 500000, 8)]
DOCTORS = [("manoj", "Dr Manoj"), ("bhawna", "Dr Bhawna")]
UPLOAD_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".pdf"}
UPLOAD_MAX = 12 * 1024 * 1024
DUP_MINUTES = 10          # S393


def _ensure(con):
    """On first use, inside a request -- never at import (F-303). Seeds are INSERT OR IGNORE, so a
    change the owner makes later to an amount or a payee is never overwritten."""
    global _schema_done
    if _schema_done:
        return
    con.executescript(SCHEMA)
    for h in HOLDERS:
        con.execute("INSERT OR IGNORE INTO petty_holder(code,name,hold_p,keeper,sort) VALUES (?,?,?,?,?)", h)
    for p in PAYEES:
        con.execute("INSERT OR IGNORE INTO petty_payee(code,name,what_hi,what_en,head,default_p,sort) "
                    "VALUES (?,?,?,?,?,?,?)", p)
    con.commit()
    _schema_done = True


def init(app, db_getter, require_fn, audit_fn=None, unit="petty", url_prefix=""):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ---------------------------------------------------------------- helpers
def _now():
    """The box's clock is IST. PETTY_NOW=<iso> pins it for the walk."""
    v = os.environ.get("PETTY_NOW", "")
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


def _r(p):
    return "{:,}".format(int(round((p or 0) / 100.0)))


def _human(iso):
    try:
        return dt.date.fromisoformat(iso[:10]).strftime("%d-%b")
    except (ValueError, TypeError):
        return iso or "—"


def _paise(v):
    """A number from the number pad: whole rupees or with paise; blank or not a number is refused."""
    s = str(v or "").replace(",", "").replace("₹", "").strip()
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if f <= 0 or f > 10_000_000:
        return None
    return int(round(f * 100))


def _paise0(v):
    """S300: an opening figure -- whole rupees or with paise; zero allowed; blank or not a number refused."""
    s = str(v if v is not None else "").replace(",", "").replace("₹", "").strip()
    if not s:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    if f < 0 or f > 10_000_000 or f != f:
        return None
    return int(round(f * 100))


def _audit_safe(con, row_id, action, before, after, who, table="petty_entry"):
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)
        con.commit()
    except Exception:                            # noqa: BLE001
        pass


def _upload_dir():
    d = os.environ.get("PETTY_UPLOAD_DIR", "")
    if not d:
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "petty_uploads")
    return d


def _save_photo(f):
    """The optional photo of a diary page or a bill. Returns (name, error)."""
    if f is None or not getattr(f, "filename", ""):
        return "", None
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in UPLOAD_EXT:
        return "", "photo type"
    data = f.read(UPLOAD_MAX + 1)
    if len(data) > UPLOAD_MAX:
        return "", "photo too large"
    if not data:
        return "", None
    sub = _now().strftime("%Y-%m")
    folder = os.path.join(_upload_dir(), sub)
    os.makedirs(folder, exist_ok=True)
    name = "%s/%s%s" % (sub, uuid.uuid4().hex, ext)
    with open(os.path.join(_upload_dir(), name), "wb") as fh:
        fh.write(data)
    return name, None


def _sum(con, where, args=()):
    r = con.execute("SELECT COALESCE(SUM(amount_p),0) s FROM petty_entry WHERE void_at='' AND " + where, args).fetchone()
    return int(r["s"] or 0)


def opening(con):
    """S300: {'cash': row or None, 'loan': row or None}."""
    out = {"cash": None, "loan": None}
    for r in con.execute("SELECT * FROM petty_opening"):
        out[r["what"]] = r
    return out


def figures(con):
    """The book's numbers: the opening figures (S300) plus the entries."""
    op = opening(con)
    ocash = int(op["cash"]["amount_p"]) if op["cash"] else 0
    oloan = int(op["loan"]["amount_p"]) if op["loan"] else 0
    recv = _sum(con, "kind='receive'")
    topup = _sum(con, "kind='topup'")
    pay = _sum(con, "kind='pay'")
    lout = _sum(con, "kind='loan_out'")
    lback = _sum(con, "kind='loan_back'")
    keeper = con.execute("SELECT * FROM petty_holder WHERE keeper=1 AND active=1 ORDER BY sort LIMIT 1").fetchone()
    hold = int(keeper["hold_p"]) if keeper else 0
    hand = ocash + recv - topup - pay - lout + lback
    loan = oloan + lout - lback
    return dict(hand_p=hand, hold_p=hold, need_p=max(0, hold - hand), loan_p=max(0, loan),
                loan_raw_p=loan, received_p=recv, topup_p=topup, paid_p=pay,
                open_cash_p=ocash, open_loan_p=oloan, open_cash_set=bool(op["cash"]), open_loan_set=bool(op["loan"]))


def availability(con, day):
    r = con.execute("SELECT * FROM petty_available WHERE day=?", (day,)).fetchone()
    return r["status"] if r else ""


def _roles(u):
    return set(u.get("roles") or [])


def _who(u):
    return (u or {}).get("user", "")


def _payees(con):
    return list(con.execute("SELECT * FROM petty_payee WHERE active=1 ORDER BY sort"))


def _holders(con):
    return list(con.execute("SELECT * FROM petty_holder WHERE active=1 ORDER BY sort"))


def _party_label(con, e, lang):
    k, p = e["kind"], e["party"]
    if k == "receive":
        return dict(DOCTORS).get(p, p) + (" se mila" if lang == "hi" else " gave")
    if k == "topup":
        h = con.execute("SELECT name FROM petty_holder WHERE code=?", (p,)).fetchone()
        return (h["name"] if h else p) + (" diary bhari" if lang == "hi" else " diary topped up")
    if k == "pay":
        if p == "other":
            return e["other_name"] or "—"
        y = con.execute("SELECT name FROM petty_payee WHERE code=?", (p,)).fetchone()
        return y["name"] if y else p
    if k == "loan_out":
        return "Loan liya" if lang == "hi" else "Loan taken by Bhati"
    return "Loan wapas" if lang == "hi" else "Loan repaid by Bhati"


# ---------------------------------------------------------------- routes
@bp.route("/finance/petty")
def home():
    u, err = _require("maker", "checker", "viewer", unit=UNIT)
    if err:
        return _shell("Petty book", _denied(), "en")
    con = _db()
    _ensure(con)
    roles = _roles(u)
    msg = request.args.get("msg") or ""
    if "checker" in roles:
        return _shell("Petty book", _owner_html(con, u, msg), "en")
    if "maker" in roles:
        return _shell("Kharcha book", _keeper_html(con, u, msg), "hi")
    return _shell("Bhati ji aaj", _viewer_html(con), "hi")


@bp.route("/finance/petty/available", methods=["POST"])
def post_available():
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    day, st = request.form.get("day", ""), request.form.get("status", "")
    today = _now().date()
    allowed = {(today + dt.timedelta(days=i)).isoformat() for i in range(0, 8)}
    if day not in allowed or st not in ("yes", "no"):
        return redirect("/finance/petty?msg=bad")
    con.execute("INSERT INTO petty_available(day,status,by_whom,at) VALUES (?,?,?,?) "
                "ON CONFLICT(day) DO UPDATE SET status=excluded.status, by_whom=excluded.by_whom, at=excluded.at",
                (day, st, _who(u), _stamp()))
    con.commit()
    _audit_safe(con, day, "available", None, dict(status=st), _who(u))
    return redirect("/finance/petty?msg=saved")


@bp.route("/finance/petty/new/<kind>/<party>")
def new_entry(kind, party):
    u, err = _require("maker", unit=UNIT)
    if err:
        return _shell("Kharcha book", _denied(), "hi")
    con = _db()
    _ensure(con)
    ok, label, hint, default_p, need_name = _entry_meta(con, kind, party)
    if not ok:
        return redirect("/finance/petty?msg=bad")
    return _shell("Kharcha book", _form_html(kind, party, label, hint, default_p, need_name,
                                             request.args.get("msg") or ""), "hi")


def _entry_meta(con, kind, party):
    """(ok, label, hint, default_p, need_name) for a button the keeper tapped."""
    if kind == "receive" and party in dict(DOCTORS):
        return True, dict(DOCTORS)[party] + " se paise mile", "Kitne mile?", 0, False
    if kind == "topup":
        h = con.execute("SELECT * FROM petty_holder WHERE code=? AND keeper=0 AND active=1", (party,)).fetchone()
        if h:
            return (True, "%s ki diary" % h["name"],
                    "Diary dekh kar kami poori ki — kitne diye? (poora ₹%s rehna chahiye)" % _r(h["hold_p"]), 0, False)
    if kind == "pay":
        if party == "other":
            return True, "Kisi aur ko diya", "Naam likhiye, phir rakam", 0, True
        y = con.execute("SELECT * FROM petty_payee WHERE code=? AND active=1", (party,)).fetchone()
        if y:
            return True, "%s — %s" % (y["name"], y["what_hi"]), "Kitna diya?", int(y["default_p"] or 0), False
    if kind in ("loan_out", "loan_back") and party == "self":
        return True, ("Apne liye loan liya" if kind == "loan_out" else "Loan wapas kiya"), "Kitna?", 0, False
    return False, "", "", 0, False


@bp.route("/finance/petty/save", methods=["POST"])
def save_entry():
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    kind, party = request.form.get("kind", ""), request.form.get("party", "")
    ok, _label, _hint, _d, need_name = _entry_meta(con, kind, party)
    back = "/finance/petty/new/%s/%s" % (kind, party)
    if not ok:
        return redirect("/finance/petty?msg=bad")
    amt = _paise(request.form.get("amount"))
    if amt is None:
        return redirect(back + "?msg=amount")
    other = (request.form.get("other_name") or "").strip()[:60] if need_name else ""
    if need_name and not other:
        return redirect(back + "?msg=name")
    # S393: the same entry by the same person within DUP_MINUTES is a repeated tap, not a second payment
    cut = (_now() - dt.timedelta(minutes=DUP_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    if con.execute("SELECT 1 FROM petty_entry WHERE void_at='' AND kind=? AND party=? AND other_name=? AND amount_p=? "
                   "AND by_whom=? AND at BETWEEN ? AND ? LIMIT 1", (kind, party, other, amt, _who(u), cut, _stamp())).fetchone():
        return redirect("/finance/petty?msg=dup")
    photo, perr = _save_photo(request.files.get("photo"))
    if perr:
        return redirect(back + "?msg=photo")
    cur = con.execute("INSERT INTO petty_entry(entry_date,kind,party,other_name,amount_p,photo,by_whom,at) "
                      "VALUES (?,?,?,?,?,?,?,?)",
                      (_today(), kind, party, other, amt, photo, _who(u), _stamp()))
    con.commit()
    _audit_safe(con, cur.lastrowid, "add", None,
                dict(kind=kind, party=party, other=other, amount_p=amt, photo=bool(photo)), _who(u))
    return redirect("/finance/petty?msg=saved")


@bp.route("/finance/petty/void/<int:eid>", methods=["POST"])
def void_entry(eid):
    """The keeper may cancel his own entry the same day; a doctor may cancel any."""
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    e = con.execute("SELECT * FROM petty_entry WHERE id=?", (eid,)).fetchone()
    roles = _roles(u)
    if e is None or e["void_at"]:
        return redirect("/finance/petty?msg=bad")
    if "checker" not in roles and not (e["by_whom"] == _who(u) and e["entry_date"] == _today()):
        return redirect("/finance/petty?msg=bad")
    con.execute("UPDATE petty_entry SET void_by=?, void_at=? WHERE id=?", (_who(u), _stamp(), eid))
    con.commit()
    _audit_safe(con, eid, "void", dict(amount_p=e["amount_p"], kind=e["kind"]), None, _who(u))
    return redirect("/finance/petty?msg=cancelled")


@bp.route("/finance/petty/confirm/<int:eid>", methods=["POST"])
def confirm_entry(eid):
    """A doctor confirms money he or she gave (receive) or OKs a loan (loan_out)."""
    u, err = _require("checker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    e = con.execute("SELECT * FROM petty_entry WHERE id=?", (eid,)).fetchone()
    if e is None or e["void_at"] or e["confirm_at"] or e["kind"] not in ("receive", "loan_out"):
        return redirect("/finance/petty?msg=bad")
    if e["kind"] == "receive" and e["party"] != _who(u):
        return redirect("/finance/petty?msg=notyours")
    con.execute("UPDATE petty_entry SET confirm_by=?, confirm_at=? WHERE id=?", (_who(u), _stamp(), eid))
    con.commit()
    _audit_safe(con, eid, "confirm", None, dict(by=_who(u)), _who(u))
    return redirect("/finance/petty?msg=confirmed")


@bp.route("/finance/petty/count", methods=["POST"])
def post_count():
    u, err = _require("checker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    holder = request.form.get("holder", "")
    if not con.execute("SELECT 1 FROM petty_holder WHERE code=? AND active=1", (holder,)).fetchone():
        return redirect("/finance/petty?msg=bad")
    if request.form.get("matches") == "1":
        short = 0
    else:
        short = _paise(request.form.get("short"))
        if short is None:
            return redirect("/finance/petty?msg=amount")
    cur = con.execute("INSERT INTO petty_count(holder,short_p,by_whom,at) VALUES (?,?,?,?)",
                      (holder, short, _who(u), _stamp()))
    con.commit()
    _audit_safe(con, cur.lastrowid, "count", None, dict(holder=holder, short_p=short), _who(u))
    return redirect("/finance/petty?msg=counted")


@bp.route("/finance/petty/opening", methods=["POST"])
def post_opening():
    """S300: a doctor sets or corrects Bhati's opening cash or opening loan. Zero allowed."""
    u, err = _require("checker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    what = request.form.get("what", "")
    if what not in ("cash", "loan"):
        return redirect("/finance/petty?msg=bad")
    amt = _paise0(request.form.get("amount"))
    if amt is None:
        return redirect("/finance/petty?msg=openamount")
    old = con.execute("SELECT amount_p FROM petty_opening WHERE what=?", (what,)).fetchone()
    con.execute("INSERT INTO petty_opening(what,amount_p,by_whom,at) VALUES (?,?,?,?) "
                "ON CONFLICT(what) DO UPDATE SET amount_p=excluded.amount_p, by_whom=excluded.by_whom, at=excluded.at",
                (what, amt, _who(u), _stamp()))
    con.commit()
    _audit_safe(con, what, "opening", dict(amount_p=old["amount_p"]) if old else None, dict(amount_p=amt),
                _who(u), table="petty_opening")
    return redirect("/finance/petty?msg=opening")


@bp.route("/finance/petty/physio/<date>", methods=["POST"])
def physio_tick(date):
    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    try:
        ok = dt.date.fromisoformat(date).isoformat() == date and date <= _today()
    except ValueError:
        ok = False
    if ok:
        con.execute("INSERT OR IGNORE INTO petty_physio_check(business_date,by_whom,at) VALUES (?,?,?)",
                    (date, _who(u), _stamp()))
        con.commit()
    return redirect("/finance/petty?msg=saved")


@bp.route("/finance/petty/photo/<int:eid>")
def photo(eid):
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    con = _db()
    _ensure(con)
    e = con.execute("SELECT photo FROM petty_entry WHERE id=?", (eid,)).fetchone()
    if e is None or not e["photo"] or ".." in e["photo"]:
        return "not found", 404
    path = os.path.join(_upload_dir(), e["photo"])
    if not os.path.isfile(path):
        return "not found", 404
    return send_file(path)


# ---------------------------------------------------------------- the keeper (Hinglish)
MSG_HI = {"saved": "✓ Save ho gaya", "cancelled": "✓ Cancel ho gaya", "bad": "Yeh nahi ho sakta",
          "dup": "Yeh entry abhi-abhi save ho chuki hai — dobara nahi likhi. Sach mein doosri baar diya ho to 10 minute baad likhiye.",
          "amount": "Rakam sahi likhiye", "name": "Naam likhiye", "photo": "Photo nahi lagi — sirf photo (jpg/png) ya pdf, 12 MB tak"}


def _physio_rows(con, since):
    """Read-only look at the physiotherapy table for Bhati's tick. Missing table -> nothing."""
    try:
        return list(con.execute(
            "SELECT p.business_date, p.cash_p, p.upi_p, c.by_whom AS ok_by FROM clinic_physio_day p "
            "LEFT JOIN petty_physio_check c ON c.business_date=p.business_date "
            "WHERE p.business_date>=? AND (p.cash_p>0 OR p.upi_p>0) ORDER BY p.business_date DESC", (since,)))
    except Exception:                            # noqa: BLE001
        return []


def _fold(title, summ, body, is_open=False):
    """S393: one section of the book as a fold -- the title and its one-line figure always visible,
    the detail on a tap. name='pb' makes the folds an accordion without JavaScript: opening one
    closes the other, so the whole book stays on one screen."""
    return ("<details class='card fold' name='pb'%s><summary><span class='ft'>%s</span><span class='fs'>%s</span></summary>"
            "<div class='fb'>%s</div></details>" % (" open" if is_open else "", title, summ, body))


def _keeper_html(con, u, msg):
    f = figures(con)
    today = _now().date()
    tom = today + dt.timedelta(days=1)
    out = []
    if msg:
        out.append("<div class='%s'>%s</div>" % ("ok" if msg in ("saved", "cancelled") else "bad", MSG_HI.get(msg, "")))
    st_today = availability(con, today.isoformat())
    word = {"yes": "✓ Available", "no": "✗ Nahi"}.get(st_today, "abhi nahi bataya")
    # the strip: always on screen
    out.append("<div class='strip'><span>Haath mein <b>₹ %s</b></span><span>Loan <b>₹ %s</b></span><span>Aaj: <b>%s</b></span></div>%s"
               % (_r(f["hand_p"]), _r(f["loan_p"]), word,
                  ("<div class='bad'>Aapko <b>₹ %s</b> chahiye — Dr Manoj / Dr Bhawna se lijiye.</div>" % _r(f["need_p"]))
                  if f["need_p"] else ""))

    def avail_row(d, label):
        st = availability(con, d.isoformat())
        cur = {"yes": "✓ Available", "no": "✗ Nahi"}.get(st, "abhi nahi bataya")
        return ("<div class='availrow'><b>%s</b> <span class='pill'>%s</span>"
                "<form method='post' action='/finance/petty/available' class='inline'>"
                "<input type='hidden' name='day' value='%s'><input type='hidden' name='status' value='yes'>"
                "<button class='big yes' type='submit'>Available</button></form>"
                "<form method='post' action='/finance/petty/available' class='inline'>"
                "<input type='hidden' name='day' value='%s'><input type='hidden' name='status' value='no'>"
                "<button class='big no' type='submit'>Nahi aaunga</button></form></div>"
                % (label, cur, d.isoformat(), d.isoformat()))
    out.append(_fold("Aaj aayenge?", {"yes": "✓ haan", "no": "✗ nahi"}.get(st_today, "batayein"),
                     avail_row(today, "Aaj %s" % today.strftime("%d-%b")) + avail_row(tom, "Kal %s" % tom.strftime("%d-%b"))))
    out.append(_fold("Paise mile", "doctor se", "<div class='btns'>%s</div>"
                     % "".join("<a class='tile' href='/finance/petty/new/receive/%s'>%s se mile</a>" % (c, n) for c, n in DOCTORS)))
    hol = [h for h in _holders(con) if not h["keeper"]]
    out.append(_fold("Diary kami poori", "%d diary" % len(hol), "<div class='btns'>%s</div>"
                     % "".join("<a class='tile' href='/finance/petty/new/topup/%s'>%s<br><span class='sm'>₹ %s rehna chahiye</span></a>"
                               % (h["code"], _esc(h["name"]), _r(h["hold_p"])) for h in hol)))
    pay = _payees(con)
    month = today.strftime("%Y-%m")

    def paid_this_month(code):
        return _sum(con, "kind='pay' AND party=? AND entry_date LIKE ?", (code, month + "%"))
    cons = [p for p in pay if p["head"] == "construction"]
    mon = [p for p in pay if p["head"] == "monthly"]
    out.append(_fold("Renovation", "%d + koi aur" % len(cons), "<div class='btns'>%s"
                     "<a class='tile other' href='/finance/petty/new/pay/other'>Koi aur<br><span class='sm'>naam likhna hoga</span></a></div>"
                     % "".join("<a class='tile' href='/finance/petty/new/pay/%s'>%s<br><span class='sm'>%s</span></a>"
                               % (p["code"], _esc(p["name"]), _esc(p["what_hi"])) for p in cons)))
    out.append(_fold("Har mahine", " · ".join("%s: %s" % (_esc(p["name"]), "de diya" if paid_this_month(p["code"]) else "baaki")
                                              for p in mon) or "—",
                     "<div class='btns'>%s</div>"
                     % "".join("<a class='tile' href='/finance/petty/new/pay/%s'>%s<br><span class='sm'>%s · ₹ %s · %s</span></a>"
                               % (p["code"], _esc(p["name"]), _esc(p["what_hi"]), _r(p["default_p"]),
                                  ("is mahine de diya" if paid_this_month(p["code"]) else "is mahine baaki"))
                               for p in mon)))
    out.append(_fold("Apna loan", "₹&nbsp;%s" % _r(f["loan_p"]),
                     "<p class='bignum'>Baaki ₹ %s</p>%s<div class='btns'>"
                     "<a class='tile' href='/finance/petty/new/loan_out/self'>Loan liya</a>"
                     "<a class='tile' href='/finance/petty/new/loan_back/self'>Loan wapas kiya</a></div>"
                     % (_r(f["loan_p"]),
                        ("<p class='mut'>Purana loan (opening): ₹ %s — isme jud gaya hai</p>" % _r(f["open_loan_p"]))
                        if f["open_loan_set"] else "<p class='mut'>Purana loan (opening) abhi doctor ne nahi likha</p>")))
    out.append(_fold("Haath mein — hisaab", "₹&nbsp;%s" % _r(f["hand_p"]),
                     "<p class='bignum'>₹ %s</p><p class='mut'>Rehna chahiye ₹ %s</p>%s"
                     "<p class='mut'>opening ₹ %s + mile ₹ %s − diary ₹ %s − diye ₹ %s − loan liya + loan wapas</p>%s"
                     % (_r(f["hand_p"]), _r(f["hold_p"]),
                        ("<p class='bad'>Aapko <b>₹ %s</b> chahiye — Dr Manoj / Dr Bhawna se lijiye.</p>" % _r(f["need_p"]))
                        if f["need_p"] else "<p class='ok'>Poora hai.</p>",
                        _r(f["open_cash_p"]), _r(f["received_p"]), _r(f["topup_p"]), _r(f["paid_p"]),
                        ("<p class='mut'>Shuru mein aapke paas the (opening): ₹ %s — isme jud gaya hai</p>" % _r(f["open_cash_p"]))
                        if f["open_cash_set"] else "<p class='mut'>Opening abhi doctor ne nahi likha</p>")))
    since = (today - dt.timedelta(days=14)).isoformat()
    rows = _physio_rows(con, since)
    if rows:
        body = []
        for r in rows:
            act = ("✓ theek" if r["ok_by"] else
                   "<form method='post' action='/finance/petty/physio/%s' class='inline'><button class='save' type='submit'>Theek hai</button></form>"
                   % r["business_date"])
            body.append("<tr><td>%s</td><td class='r'>%s</td><td class='r'>%s</td><td>%s</td></tr>"
                        % (_human(r["business_date"]), _r(r["cash_p"]), _r(r["upi_p"]), act))
        left = len([r for r in rows if not r["ok_by"]])
        out.append(_fold("Physio entry", ("%d dekhni" % left) if left else "theek ✓",
                         "<table class='grid'><thead><tr><th>Din</th><th class='r'>Cash</th><th class='r'>UPI</th><th></th></tr></thead>"
                         "<tbody>%s</tbody></table>" % "".join(body)))
    recent = list(con.execute("SELECT * FROM petty_entry WHERE entry_date>=? ORDER BY id DESC LIMIT 30",
                              ((today - dt.timedelta(days=7)).isoformat(),)))
    if recent:
        body = []
        for e in recent:
            can = (not e["void_at"]) and e["by_whom"] == _who(u) and e["entry_date"] == _today()
            state = ("<s>cancel</s>" if e["void_at"] else
                     ("<form method='post' action='/finance/petty/void/%d' class='inline'><button class='clear' type='submit'>Galti — cancel</button></form>" % e["id"]
                      if can else ""))
            body.append("<tr%s><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td></tr>"
                        % (" class='void'" if e["void_at"] else "", _human(e["entry_date"]),
                           _esc(_party_label(con, e, "hi")), _r(e["amount_p"]), state))
        out.append(_fold("Pichhle 7 din", "%d" % len([e for e in recent if not e["void_at"]]),
                         "<table class='grid'><tbody>%s</tbody></table>" % "".join(body)))
    return "".join(out)


def _form_html(kind, party, label, hint, default_p, need_name, msg):
    err = ("<div class='bad'>%s</div>" % MSG_HI.get(msg, "")) if msg else ""
    name_box = ("<p><input class='note' name='other_name' maxlength='60' required placeholder='Naam'></p>" if need_name else "")
    val = ("%d" % (default_p // 100)) if default_p else ""
    photo_hint = "Diary ke panne ki photo" if kind == "topup" else "Bill / parchi ki photo (agar ho)"
    return """%s<div class="card"><h2>%s</h2>
<form method="post" action="/finance/petty/save" enctype="multipart/form-data">
<input type="hidden" name="kind" value="%s"><input type="hidden" name="party" value="%s">
%s<p class="mut">%s</p>
<p><input class="amt" name="amount" type="number" inputmode="decimal" min="1" step="any" required value="%s" placeholder="₹"></p>
<p class="mut">%s</p><p><input type="file" name="photo" accept="image/*,application/pdf" capture="environment"></p>
<button class="save" type="submit">Save</button></form>
<p><a class="btn" href="/finance/petty">← Wapas</a></p></div>""" % (
        err, _esc(label), _esc(kind), _esc(party), name_box, _esc(hint), val, photo_hint)


def _viewer_html(con):
    st = availability(con, _today())
    line = {"yes": "✓ Bhati ji aaj available hain.", "no": "✗ Bhati ji aaj nahi aayenge."}.get(
        st, "Bhati ji ne aaj abhi nahi bataya.")
    return "<div class='card'><h2>%s</h2><p class='bignum'>%s</p></div>" % (_now().strftime("%d-%b-%Y"), line)


# ---------------------------------------------------------------- the doctors (English)
MSG_EN = {"confirmed": "Confirmed.", "counted": "Count recorded.", "cancelled": "Entry cancelled.",
          "opening": "Opening balance saved.", "openamount": "Enter the opening figure as a number (0 is allowed).",
          "bad": "That cannot be done.", "amount": "Enter the shortfall as a number.",
          "notyours": "Only the doctor who gave the money confirms it."}


def _owner_html(con, u, msg):
    f = figures(con)
    today = _now().date()
    month = today.strftime("%Y-%m")
    out = []
    if msg:
        out.append("<div class='%s'>%s</div>" % ("bad" if msg in ("bad", "amount", "notyours", "openamount") else "ok", MSG_EN.get(msg, "")))
    st = availability(con, today.isoformat())
    pend = list(con.execute("SELECT * FROM petty_entry WHERE void_at='' AND confirm_at='' AND kind IN ('receive','loan_out') ORDER BY id"))
    # S393: the strip -- always on screen
    out.append("<div class='strip'><span>Bhati today: <b>%s</b></span><span>In hand <b>₹ %s</b></span>"
               "<span>Loan <b>₹ %s</b></span>%s</div>"
               % ({"yes": "Available", "no": "Not available"}.get(st, "Not marked yet"), _r(f["hand_p"]), _r(f["loan_p"]),
                  ("<span class='hot'>%d need your tap</span>" % len(pend)) if pend else ""))
    if pend:
        body = []
        for e in pend:
            mine = e["kind"] == "loan_out" or e["party"] == _who(u)
            act = ("<form method='post' action='/finance/petty/confirm/%d' class='inline'><button class='save' type='submit'>%s</button></form>"
                   % (e["id"], "OK" if e["kind"] == "loan_out" else "Yes, I gave it") if mine
                   else "<span class='mut'>for %s</span>" % dict(DOCTORS).get(e["party"], e["party"]))
            body.append("<tr><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td></tr>"
                        % (_human(e["entry_date"]), _esc(_party_label(con, e, "en")), _r(e["amount_p"]), act))
        out.append(_fold("Needs your tap", "%d · ₹&nbsp;%s" % (len(pend), _r(sum(int(e["amount_p"]) for e in pend))),
                         "<table class='grid'><tbody>%s</tbody></table>" % "".join(body)))
    # the three
    last_top = {}
    for h in _holders(con):
        if h["keeper"]:
            continue
        r = con.execute("SELECT * FROM petty_entry WHERE void_at='' AND kind='topup' AND party=? ORDER BY id DESC LIMIT 1",
                        (h["code"],)).fetchone()
        last_top[h["code"]] = r
    rows, summ = [], []
    for h in _holders(con):
        lc = con.execute("SELECT * FROM petty_count WHERE holder=? ORDER BY id DESC LIMIT 1", (h["code"],)).fetchone()
        counted = ("matched %s" % _human(lc["at"]) if lc and not lc["short_p"]
                   else ("short ₹ %s on %s" % (_r(lc["short_p"]), _human(lc["at"])) if lc else "never counted"))
        if h["keeper"]:
            state = "in hand ₹ %s%s" % (_r(f["hand_p"]), (" · needs ₹ %s" % _r(f["need_p"])) if f["need_p"] else "")
        else:
            t = last_top.get(h["code"])
            month_top = _sum(con, "kind='topup' AND party=? AND entry_date LIKE ?", (h["code"], month + "%"))
            state = ("last topped up %s (₹ %s) · this month ₹ %s" % (_human(t["entry_date"]), _r(t["amount_p"]), _r(month_top))
                     if t else "not topped up yet")
            summ.append("%s&nbsp;₹&nbsp;%s" % (_esc(h["name"]), _r(month_top)))
        form = ("<form method='post' action='/finance/petty/count' class='inline'><input type='hidden' name='holder' value='%s'>"
                "<input type='hidden' name='matches' value='1'><button class='save' type='submit'>Counted — matches</button></form>"
                "<form method='post' action='/finance/petty/count' class='inline'><input type='hidden' name='holder' value='%s'>"
                "<input class='amts' name='short' type='number' inputmode='decimal' min='1' step='any' placeholder='short ₹'>"
                "<button class='clear' type='submit'>Short</button></form>") % (h["code"], h["code"])
        rows.append("<tr><td><b>%s</b><br><span class='mut'>holds ₹ %s</span></td><td>%s<br><span class='mut'>%s</span></td></tr>"
                    "<tr><td colspan='2' class='acts'>%s</td></tr>"
                    % (_esc(h["name"]), _r(h["hold_p"]), state, counted, form))
    out.append(_fold("Diaries", " · ".join(summ),
                     "<table class='grid three'><tbody>%s</tbody></table>" % "".join(rows)))
    op = opening(con)

    def open_form(what, label, row):
        now = ("₹ %s <span class='mut'>· set by %s on %s</span>" % (_r(row["amount_p"]), _esc(row["by_whom"]), _human(row["at"]))
               if row else "<b>not set yet</b>")
        return ("<tr><td>%s</td><td>%s</td></tr><tr><td colspan='2' class='acts'><form method='post' action='/finance/petty/opening' class='inline'>"
                "<input type='hidden' name='what' value='%s'>"
                "<input class='amts' name='amount' type='number' inputmode='decimal' min='0' step='any' required placeholder='₹'>"
                "<button class='save' type='submit'>%s</button></form></td></tr>"
                % (label, now, what, "Correct" if row else "Save"))
    out.append(_fold("Bhati's cash", "₹&nbsp;%s" % _r(f["hand_p"]),
                     "<p class='bignum'>₹ %s in hand</p>"
                     "<p class='mut'>opening ₹ %s + received ₹ %s − diaries ₹ %s − payments ₹ %s − loans out + loans back</p>"
                     "<table class='grid'><tbody>%s</tbody></table>"
                     % (_r(f["hand_p"]), _r(f["open_cash_p"]), _r(f["received_p"]), _r(f["topup_p"]), _r(f["paid_p"]),
                        open_form("cash", "Opening cash<br><span class='mut'>held at the start</span>", op["cash"]))))
    out.append(_fold("Bhati's loan", "₹&nbsp;%s" % _r(f["loan_p"]),
                     "<p class='bignum'>₹ %s owed</p>"
                     "<p class='mut'>opening ₹ %s + loans taken − loans repaid</p>"
                     "<table class='grid'><tbody>%s</tbody></table>"
                     % (_r(f["loan_p"]), _r(f["open_loan_p"]),
                        open_form("loan", "Opening loan<br><span class='mut'>owed at the start</span>", op["loan"]))))
    body = []
    for p in _payees(con):
        tot = _sum(con, "kind='pay' AND party=?", (p["code"],))
        mt = _sum(con, "kind='pay' AND party=? AND entry_date LIKE ?", (p["code"], month + "%"))
        extra = (" · <b>%s</b>" % ("paid this month" if mt else "NOT paid this month")) if p["head"] == "monthly" else ""
        body.append("<tr><td>%s<br><span class='mut'>%s%s</span></td><td class='r'>%s</td><td class='r'><b>%s</b></td></tr>"
                    % (_esc(p["name"]), _esc(p["what_en"]), extra, _r(mt), _r(tot)))
    oth = _sum(con, "kind='pay' AND party='other'")
    body.append("<tr><td>Others (named on each entry)</td><td class='r'>%s</td><td class='r'><b>%s</b></td></tr>"
                % (_r(_sum(con, "kind='pay' AND party='other' AND entry_date LIKE ?", (month + "%",))), _r(oth)))
    out.append(_fold("Payments", "%s ₹&nbsp;%s" % (today.strftime("%b"), _r(_sum(con, "kind='pay' AND entry_date LIKE ?", (month + "%",)))),
                     "<table class='grid'><thead><tr><th>To</th><th class='r'>%s</th><th class='r'>All time</th></tr></thead>"
                     "<tbody>%s</tbody></table>" % (today.strftime("%b %Y"), "".join(body))))
    ents = list(con.execute("SELECT * FROM petty_entry WHERE entry_date LIKE ? ORDER BY id DESC", (month + "%",)))
    body = []
    for e in ents:
        ph = ("<a href='/finance/petty/photo/%d'>photo</a>" % e["id"]) if e["photo"] else ""
        state = ("cancelled by %s" % _esc(e["void_by"]) if e["void_at"] else
                 "<form method='post' action='/finance/petty/void/%d' class='inline'><button class='clear' type='submit'>Cancel</button></form>" % e["id"])
        conf = (" ✓ %s" % _esc(e["confirm_by"])) if e["confirm_at"] else ""
        body.append("<tr%s><td>%s</td><td>%s%s</td><td class='r'>%s</td><td>%s</td><td>%s</td></tr>"
                    % (" class='void'" if e["void_at"] else "", _human(e["entry_date"]), _esc(_party_label(con, e, "en")), conf,
                       _r(e["amount_p"]), ph, state))
    nv = len([e for e in ents if e["void_at"]])
    out.append(_fold("Entries — %s" % today.strftime("%b"),
                     "%d%s" % (len(ents) - nv, (" + %d cut" % nv) if nv else ""),
                     "<table class='grid'><tbody>%s</tbody></table>" % ("".join(body) or "<tr><td>None yet.</td></tr>")))
    out.append("<p class='mut'>Separate from Sanjeevni and clinic money: nothing here reaches either.</p>")
    return "".join(out)


# ---------------------------------------------------------------- shells
def _denied():
    return """<div class="card"><h2>Not permitted</h2><p>Your login is not on the petty book.
      If that is wrong, ask Dr Manoj.</p></div>"""


def _shell(title, body, lang):
    return """<!doctype html><html lang="%s"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#3c464e;--line:#8a9aa6;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;--entry:#fffbe6}
*{box-sizing:border-box}
body{margin:0;padding:14px;background:var(--bg);color:var(--ink);font:18px/1.55 "Segoe UI",system-ui,-apple-system,sans-serif}
h1{font-size:22px;margin:0 0 12px;color:var(--accent)}h2{font-size:19px;margin:0 0 10px;color:var(--accent)}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:14px;margin:0 0 14px;overflow-x:auto}
details.card summary{cursor:pointer;color:var(--accent)}
.mut{color:var(--mut);font-size:16px}.sm{font-size:14px;color:var(--mut);font-weight:400}
.bignum{font-size:28px;font-weight:700;margin:4px 0}
.btns{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
a.tile{display:block;min-height:64px;padding:12px;border:2px solid var(--accent);border-radius:10px;background:#fff;color:var(--accent);
 text-decoration:none;font-weight:600;font-size:18px}
a.tile.other{border-style:dashed}
table.grid{width:100%%;border-collapse:collapse;font-size:16px}.grid th,.grid td{border:1px solid var(--line);padding:8px}
.r{text-align:right;white-space:nowrap}tr.void td{color:#888;text-decoration:line-through}
input.amt{width:100%%;min-height:58px;font-size:26px;padding:8px 12px;border:2px solid #5b6b76;border-radius:8px;text-align:right;background:var(--entry)}
input.amts{width:110px;min-height:44px;font-size:18px;padding:6px;border:2px solid #5b6b76;border-radius:8px}
.note{width:100%%;min-height:48px;padding:9px;border:2px solid #5b6b76;border-radius:8px;font-size:18px;background:var(--entry)}
button.save,button.big{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:13px 20px;font-size:18px;font-weight:600;cursor:pointer;margin:4px 6px 4px 0}
button.big.yes{background:#2c6e2f}button.big.no{background:#8c2f2f}
button.clear{background:var(--paper);color:#8c2f2f;border:2px solid #8c2f2f;border-radius:9px;padding:9px 12px;font-size:15px;cursor:pointer}
.inline{display:inline-block;margin:2px 6px 2px 0}.availrow{margin:6px 0 10px}
a.btn{display:inline-block;border:2px solid var(--accent);color:var(--accent);border-radius:9px;padding:10px 14px;text-decoration:none;margin-top:8px;background:var(--paper)}
.ok{background:#dff0d8;border-left:6px solid #2c6e2f;padding:10px 14px;margin-bottom:12px}
.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:10px 14px;margin-bottom:12px}
.pill{font-size:14px;padding:2px 9px;border-radius:12px;background:#e3e8eb;border:1px solid var(--line)}
.strip{display:flex;flex-wrap:wrap;gap:4px 16px;background:var(--paper);border:2px solid var(--accent);border-radius:10px;padding:8px 12px;margin:0 0 8px;font-size:17px;line-height:1.35}
.strip .hot{color:#8c2f2f;font-weight:700}
details.fold{padding:0;margin:0 0 6px}
details.fold>summary{list-style:none;display:flex;justify-content:space-between;align-items:center;gap:10px;padding:8px 12px;min-height:46px;font-weight:600;font-size:17px;line-height:1.3}
details.fold>summary::-webkit-details-marker{display:none}
details.fold>summary .ft{flex:1 0 38%%;min-width:0}
details.fold>summary .ft::before{content:"▸ "}
details.fold[open]>summary .ft::before{content:"▾ "}
details.fold>summary .fs{flex:0 1 auto;font-weight:700;color:var(--ink);text-align:right;font-size:16px}
td.acts{border-top:0;padding-top:0}
.three td:first-child{width:40%%}
details.fold[open]{border-color:var(--accent)}
details.fold .fb{padding:0 12px 12px}
@media (max-width:600px){body{padding:10px}h1{font-size:18px;margin:0 0 8px}}
</style></head><body><h1>Dr. Manoj Agarwal Clinic — %s</h1>
%s<p class="mut"><a href="/portal">← Portal</a></p></body></html>""" % (lang, _esc(title), _esc(title), body)
