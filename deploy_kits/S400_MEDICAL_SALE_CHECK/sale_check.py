#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  sale_check.py  ·  v1.0  ·  kit S400_MEDICAL_SALE_CHECK  ·  Session 283 (Sanjeevni)  ·  D616
#
#  BHATI CHECKS THE PHARMACY DAYS (the owner, 25-Sep-2026, his words):
#      next morning he gets the days NOT YET APPROVED, checks Darpan's physical copy and the
#      Marg sale sheet against what the system shows -- "as I do right now". Whether Darpan did
#      his job or not is flagged. Bhati enters ONLY the amount of cash Darpan handed over; it goes
#      to Dr Bhawna by default, one tap for Dr Manoj; the date is the sale date, fixed. A wrong
#      day: minimum typing, maximum drop-downs. He must NOT see month totals or any other cash
#      part. The owner stays the approver and can do all of it himself exactly as today.
#
#  WHAT THIS FILE IS
#    * Bhati's page  GET /finance/salecheck            (Hindi, Roman script, phone-first; sale_check.html)
#    * its API       GET /finance/salecheck/api/days    the unapproved pharmacy days, oldest first
#                    GET /finance/salecheck/api/day/<iso>   ONE day's figures (the owner's day panel's
#                                                        own numbers, sanjeevni_day.day_view) + his marks
#                    POST .../api/verdict   {date}                       "Sahi hai"
#                    POST .../api/issue     {date, bill, problem, note}  "Galti hai" (drop-downs)
#                    POST .../api/issue/remove {id}
#                    POST .../api/cash      {date, amount_p, party}      the cash Darpan handed
#                    POST .../api/owner/move {date, party?, new_date?}   the owner only
#    * three read helpers the owner's pages call in-process, every one fail-soft:
#                    owner_marks(con)   owner_checks(con, iso)   days_with_mistakes(con)
#
#  WHAT IT WRITES
#    sale_check_day, sale_check_issue, sale_check_cash (its own three tables, created on first use).
#    Bhati's cash goes through darpan_kal's OWN path -- the darpan_kal_day row, _decide(), and the ONE
#    cash_movement _land_movement() keeps per day (a re-save updates the same row) -- never a second
#    register: the one cash calculation (sanjeevni_cash) reads it as it reads Darpan's own entry.
#    Every write is audited in darpan_kal_audit.
#
#  ACCESS
#    Its own server unit 'salecheck' (unit_role): bhati is its maker, the owner its checker. Bhati holds
#    NO medical row, so every other pharmacy address refuses him at finance_app's front gate. A maker
#    reaches only an UNAPPROVED day here; an approved day answers 403 to him and 200 to the owner.
#
#  NEVER SHOWN TO A MAKER: drawer, pool, where the cash went, deposits, banks, month table, other
#  days' totals, returns approval. The day payload is built from named fields only.
# =============================================================================
import datetime as dt
import json
import os
import re
import sqlite3
import sys

from flask import Blueprint, jsonify, request, send_file

VERSION = "1.0"
KIT = "S400_MEDICAL_SALE_CHECK"
bp = Blueprint("sale_check", __name__)
_db = _require = None
_unit = "medical"                 # the pharmacy days it checks
ACCESS_UNIT = "salecheck"         # the server unit that gates the page (unit_role)
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
PAGE = os.path.join(HERE, "sale_check.html")
DAY_BILL = "DAY"                  # "Poora din" in the Kaunsa bill drop-down
PARTIES = ("dr_manoj", "dr_bhawna")
PARTY_HI = {"dr_manoj": "Dr Manoj", "dr_bhawna": "Dr Bhawna"}
PARTY_EN = {"dr_manoj": "you", "dr_bhawna": "Dr Bhawna"}
PROBLEMS = ("amount_differs", "missing_in_marg", "missing_on_paper", "noncash_not_marked", "mode_wrong", "other")
PROBLEM_HI = {"amount_differs": "Amount alag hai", "missing_in_marg": "Marg mein bill nahi",
              "missing_on_paper": "Kaagaz par bill nahi", "noncash_not_marked": "Home/Procedure nahi laga",
              "mode_wrong": "Cash/UPI galat", "other": "Aur kuch"}
PROBLEM_EN = {"amount_differs": "amount differs", "missing_in_marg": "not in Marg",
              "missing_on_paper": "not on the paper copy", "noncash_not_marked": "home/procedure not deducted",
              "mode_wrong": "cash/UPI wrong", "other": "other"}
WEEKDAY_HI = ["Som", "Mangal", "Budh", "Guru", "Shukra", "Shani", "Ravi"]
HOME_DEFAULT = "HOME MEDI"
PROC_DEFAULT = "PROSIJ,PROSEJ,PROCIJ,PROCED,PROSED,PRUSIJ"
DDL = (
    "CREATE TABLE IF NOT EXISTS sale_check_day ("
    " unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " verdict TEXT NOT NULL CHECK (verdict IN ('ok','wrong')),"
    " checked_by TEXT NOT NULL, checked_at TEXT NOT NULL, updated_at TEXT,"
    " PRIMARY KEY (unit, business_date))",
    "CREATE TABLE IF NOT EXISTS sale_check_issue ("
    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " bill_no TEXT NOT NULL, problem TEXT NOT NULL CHECK (problem IN"
    " ('amount_differs','missing_in_marg','missing_on_paper','noncash_not_marked','mode_wrong','other')),"
    " note TEXT, added_by TEXT NOT NULL, added_at TEXT NOT NULL, removed_by TEXT, removed_at TEXT)",
    "CREATE INDEX IF NOT EXISTS ix_sale_check_issue_day ON sale_check_issue(unit, business_date)",
    "CREATE TABLE IF NOT EXISTS sale_check_cash ("
    " unit TEXT NOT NULL, business_date TEXT NOT NULL,"
    " amount_p INTEGER NOT NULL CHECK (amount_p >= 0),"
    " party TEXT NOT NULL CHECK (party IN ('dr_manoj','dr_bhawna')),"
    " darpan_p INTEGER, darpan_to TEXT,"
    " entered_by TEXT NOT NULL, entered_at TEXT NOT NULL, updated_at TEXT, moved_from TEXT,"
    " PRIMARY KEY (unit, business_date))",
)


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def ensure_schema(con):
    for ddl in DDL:
        con.execute(ddl)


def _valid_date(s):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", s or ""))


def rs(p):
    """Indian grouping, whole rupees (the same as the owner's pages)."""
    if p is None:
        return None
    neg, v = p < 0, abs(int(round(p / 100.0)))
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
    return ("-" if neg else "") + s


def _hm(iso):
    """'2026-09-25T09:40:12' -> '09:40 25-Sep'."""
    try:
        return dt.datetime.fromisoformat(str(iso)[:19]).strftime("%H:%M %d-%b")
    except (TypeError, ValueError):
        return str(iso or "")


def _dmy(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%d-%b")
    except (TypeError, ValueError):
        return iso


def _setting(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r and (r[0] or "").strip() else default)
    except sqlite3.OperationalError:
        return default


def _words(con, key, default):
    return [w.strip().upper() for w in _setting(con, key, default).split(",") if w.strip()]


def _log_from(con):
    return _setting(con, "darpan_kal.log_from", "2026-08-17")


def _audit(con, who, action, detail):
    try:
        import darpan_kal
        darpan_kal._audit(con, who, action, detail)
    except Exception:  # noqa: BLE001 -- the record is the row itself; the table is darpan_kal's
        pass


# ------------------------------------------------------------------ the day, its books
def _entry(con, iso):
    r = con.execute("SELECT id, status FROM day_entry WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
    return (r[0], r[1]) if r else (None, None)


def _open(status):
    return status in ("submitted", "draft")


def _kal_row(con, iso):
    if not _has(con, "darpan_kal_day"):
        return None
    r = con.execute("SELECT * FROM darpan_kal_day WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
    return dict(zip([c[0] for c in con.execute("SELECT * FROM darpan_kal_day LIMIT 0").description], tuple(r))) if r else None


def _check_row(con, iso):
    r = con.execute("SELECT verdict, checked_by, checked_at FROM sale_check_day WHERE unit=? AND business_date=?",
                    (_unit, iso)).fetchone()
    return dict(verdict=r[0], by=r[1], at=r[2]) if r else None


def _issues(con, iso):
    return [dict(id=r[0], bill=r[1], problem=r[2], problem_hi=PROBLEM_HI.get(r[2], r[2]),
                 problem_en=PROBLEM_EN.get(r[2], r[2]), note=r[3] or "", by=r[4], at=r[5])
            for r in con.execute("SELECT id, bill_no, problem, note, added_by, added_at FROM sale_check_issue "
                                 "WHERE unit=? AND business_date=? AND removed_at IS NULL ORDER BY id", (_unit, iso))]


def _cash_row(con, iso):
    r = con.execute("SELECT amount_p, party, darpan_p, darpan_to, entered_by, entered_at, updated_at, moved_from "
                    "FROM sale_check_cash WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
    if not r:
        return None
    return dict(amount_p=int(r[0]), party=r[1], darpan_p=(int(r[2]) if r[2] is not None else None), darpan_to=r[3],
                by=r[4], at=r[6] or r[5], moved_from=r[7],
                diff_p=((int(r[0]) - int(r[2])) if r[2] is not None else None))


def _label_bills_missing(con, eid, iso):
    """Bills of the day whose customer text is one of Darpan's labels (HOME MEDI / PROSIJ..., the
    setting word lists day_resync uses) that carry NO day_noncash_bill deduction and no ruling.
    Read from the review queue and the two identity tables the ingest keeps the bill text in."""
    home_w, proc_w = _words(con, "noncash.home_words", HOME_DEFAULT), _words(con, "noncash.proc_words", PROC_DEFAULT)

    def head_for(text):
        t = " ".join((text or "").upper().split())
        if any(w in t for w in home_w):
            return "HOME"
        if any(w in t for w in proc_w):
            return "PROCEDURE"
        return None
    found = {}
    if _has(con, "sale_item_review"):
        for raw, guess in con.execute("SELECT raw_text, guess_name FROM sale_item_review WHERE day_entry_id=?", (eid,)):
            try:
                j = json.loads(raw or "{}")
            except ValueError:
                j = {}
            h = head_for(guess or j.get("patient_name") or j.get("description") or "")
            b = str(j.get("bill_no") or "").strip()
            if h and b:
                found.setdefault(b, h)
    for tbl in ("identity_resolution", "identity_dispute"):
        if _has(con, tbl):
            for b, nm in con.execute("SELECT bill_no, bill_name FROM %s WHERE unit=? AND business_date=?" % tbl, (_unit, iso)):
                h = head_for(nm)
                b = str(b or "").strip()
                if h and b:
                    found.setdefault(b, h)
    out = []
    for b, h in sorted(found.items()):
        if con.execute("SELECT 1 FROM day_noncash_bill WHERE unit=? AND bill_no=?", (_unit, b)).fetchone():
            continue
        if _has(con, "cash_bill_ruling") and con.execute("SELECT 1 FROM cash_bill_ruling WHERE unit=? AND bill_no=?",
                                                         (_unit, b)).fetchone():
            continue
        out.append((b, h))
    return out


def _darpan(kal, cash):
    """What DARPAN recorded as handed (amount, to whom), or None when he recorded nothing. Once Bhati has
    saved, Darpan's original figure is the one kept in sale_check_cash.darpan_p."""
    if cash:
        if cash["darpan_p"] is None:
            return None
        return dict(handed_p=cash["darpan_p"], handed=rs(cash["darpan_p"]), to=cash["darpan_to"],
                    to_hi=PARTY_HI.get(cash["darpan_to"], cash["darpan_to"]), by="darpan", at="")
    if kal and kal.get("handed_p") is not None:
        return dict(handed_p=int(kal["handed_p"]), handed=rs(int(kal["handed_p"])), to=kal.get("handed_to"),
                    to_hi=PARTY_HI.get(kal.get("handed_to"), kal.get("handed_to")), by=kal.get("created_by"),
                    at=_hm(kal.get("created_at")))
    return None


def _flags(con, eid, iso, v, kal, cash):
    """The red flags, computed and never typed, each one Hindi line."""
    out = []
    darpan = _darpan(kal, cash)
    handed = cash["amount_p"] if cash else (darpan["handed_p"] if darpan else None)
    if darpan is None:
        out.append("Darpan ne cash ka hisaab nahi likha")
    if handed is not None and v.get("cash_received_p") is not None and handed != int(v["cash_received_p"]):
        d = handed - int(v["cash_received_p"])
        out.append("Diya cash ₹%s, hona chahiye ₹%s — %s ₹%s" % (
            rs(handed), rs(v["cash_received_p"]), "zyada" if d > 0 else "kam", rs(abs(d))))
    if v.get("source") != "marg":
        out.append("Marg ki sale report abhi nahi aayi")
    unnamed = [b for b in (v.get("sale", {}).get("list") or []) if not b.get("name")]
    if unnamed:
        out.append("%d bill par naam nahi hai (%s)" % (len(unnamed), ", ".join(str(b["bill"]) for b in unnamed[:6])))
    for b, h in _label_bills_missing(con, eid, iso):
        out.append("Bill %s %s hai, par kata nahi" % (b, h))
    return out


def _view(con, iso):
    import sanjeevni_day
    return sanjeevni_day.day_view(con, iso, _unit)


def _chip(chk, issues):
    if issues:
        return dict(kind="wrong", text="Galti — %d" % len(issues))
    if chk and chk["verdict"] == "ok":
        return dict(kind="ok", text="Sahi hai ✓")
    return dict(kind="pending", text="Jaanch baaki")


def day_payload(con, iso, kind):
    """ONE day for Bhati: the owner's day panel's own figures for that day, his marks, the flags.
    Built from named fields only -- nothing about the drawer, the pool, banks or other days."""
    eid, status = _entry(con, iso)
    if not eid:
        return None
    v = _view(con, iso)
    if not v.get("ok") or not v.get("filed"):
        return None
    kal, cash, chk, issues = _kal_row(con, iso), _cash_row(con, iso), _check_row(con, iso), _issues(con, iso)
    sales = [dict(bill=b["bill"], name=b.get("name") or "", amount=b["amount"],
                  items=[dict(item=i.get("item"), pack=i.get("pack") or "", qty=i.get("qty") or "", amount=i.get("amount"))
                         for i in (b.get("items") or [])])
             for b in (v["sale"]["list"] or [])]
    rets = [dict(bill=b["bill"], name=b.get("name") or "", amount=b["amount"],
                 items=[dict(item=i.get("item"), qty=i.get("qty") or "", amount=i.get("amount")) for i in (b.get("items") or [])])
            for b in (v["returns"]["list"] or [])]
    darpan = _darpan(kal, cash)
    wd = dt.date.fromisoformat(iso).weekday()
    return dict(ok=True, date=iso, day=_dmy(iso), weekday=WEEKDAY_HI[wd], status=status, open=_open(status),
                me=kind, kit=KIT,
                sale=dict(total=v["sale"]["total"], bills=v["sale"]["bills"], list=sales),
                returns=dict(total=v["returns"]["total"], count=v["returns"]["count"], list=rets),
                upi=dict(total=v["upi"]["total"], bank_total=v["upi"].get("bank_total"),
                         payments=[dict(time=p.get("time"), amount=p.get("amount"), ref=p.get("ref")) for p in (v["upi"]["payments"] or [])]),
                without_cash=dict(total=v["without_cash"]["total"],
                                  list=[dict(bill=x["bill"], head=x["head"], note=x.get("note") or "", amount=x["amount"])
                                        for x in (v["without_cash"]["list"] or [])]),
                cash_received=v["cash_received"], cash_received_p=v["cash_received_p"],
                darpan=darpan,
                cash=(dict(amount_p=cash["amount_p"], amount=rs(cash["amount_p"]), to=cash["party"],
                           to_hi=PARTY_HI.get(cash["party"]), by=cash["by"], at=_hm(cash["at"]),
                           darpan_p=cash["darpan_p"], darpan=rs(cash["darpan_p"]), diff_p=cash["diff_p"],
                           diff=rs(abs(cash["diff_p"])) if cash["diff_p"] else None) if cash else None),
                check=(dict(verdict=chk["verdict"], by=chk["by"], at=_hm(chk["at"])) if chk else None),
                issues=issues, chip=_chip(chk, issues),
                flags=_flags(con, eid, iso, v, kal, cash),
                bills=[str(b["bill"]) for b in sales] + [str(b["bill"]) for b in rets],
                problems=[dict(key=k, hi=PROBLEM_HI[k]) for k in PROBLEMS], parties=list(PARTIES))


def _unapproved(con):
    return [r[0] for r in con.execute("SELECT business_date FROM day_entry WHERE unit=? AND status IN ('submitted','draft') "
                                      "AND business_date>=? ORDER BY business_date", (_unit, _log_from(con)))]


def day_lines(con):
    """The list: the unapproved pharmacy days, oldest first, one card each."""
    out = []
    for iso in _unapproved(con):
        eid, status = _entry(con, iso)
        try:
            v = _view(con, iso)
        except Exception:  # noqa: BLE001
            v = {}
        if not v.get("ok") or not v.get("filed"):
            continue
        kal, cash, chk, issues = _kal_row(con, iso), _cash_row(con, iso), _check_row(con, iso), _issues(con, iso)
        out.append(dict(date=iso, day=_dmy(iso), weekday=WEEKDAY_HI[dt.date.fromisoformat(iso).weekday()],
                        bills=v["sale"]["bills"], sale=v["sale"]["total"], chip=_chip(chk, issues),
                        flags=_flags(con, eid, iso, v, kal, cash)))
    return out


# ------------------------------------------------------------------ auth
def _auth():
    u, err = _require("maker", "checker", unit=ACCESS_UNIT)
    if err:
        return None, None, None, err
    con = _db()
    ensure_schema(con)
    kind = "owner" if "checker" in (u.get("roles") or []) else "staff"
    return u, con, kind, None


def _day_for(con, kind, iso):
    """(eid, status, err): a filed pharmacy day; a maker reaches only an unapproved one."""
    if not _valid_date(iso):
        return None, None, (jsonify(ok=False, error="bad_date"), 400)
    eid, status = _entry(con, iso)
    if not eid:
        return None, None, (jsonify(ok=False, error="not_filed", message="Yeh din abhi system mein nahi aaya."), 404)
    if kind != "owner" and not _open(status):
        return None, None, (jsonify(ok=False, error="approved_day", message="Yeh din approve ho chuka hai."), 403)
    return eid, status, None


# ------------------------------------------------------------------ routes: read
@bp.route("/finance/salecheck")
def page():
    u, con, kind, err = _auth()
    if err:
        return err
    return send_file(PAGE)


@bp.route("/finance/salecheck/api/healthz")
def api_healthz():
    u, con, kind, err = _auth()
    if err:
        return err
    return jsonify(ok=True, module="sale_check", version=VERSION, kit=KIT)


@bp.route("/finance/salecheck/api/days")
def api_days():
    u, con, kind, err = _auth()
    if err:
        return err
    return jsonify(ok=True, me=kind, days=day_lines(con), log_from=_log_from(con))


@bp.route("/finance/salecheck/api/day/<iso>")
def api_day(iso):
    u, con, kind, err = _auth()
    if err:
        return err
    eid, status, err = _day_for(con, kind, iso)
    if err:
        return err
    p = day_payload(con, iso, kind)
    if not p:
        return jsonify(ok=False, error="not_filed", message="Yeh din abhi system mein nahi aaya."), 404
    return jsonify(**p)


# ------------------------------------------------------------------ routes: Bhati writes
@bp.route("/finance/salecheck/api/verdict", methods=["POST"])
def api_verdict():
    """Sahi hai -- one tap. Stored once; a second tap answers 'already' and writes nothing."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    eid, status, err = _day_for(con, kind, iso)
    if err:
        return err
    if _issues(con, iso):
        return jsonify(ok=False, error="has_issues", message="Is din par galti likhi hai — pehle use hataiye."), 409
    chk = _check_row(con, iso)
    if chk and chk["verdict"] == "ok":
        return jsonify(ok=True, already=True, date=iso, day=_dmy(iso), at=_hm(chk["at"]), by=chk["by"],
                       message="Yeh din pehle hi 'Sahi hai' likha ja chuka hai.")
    now = now_iso()
    con.execute("INSERT INTO sale_check_day (unit, business_date, verdict, checked_by, checked_at, updated_at) "
                "VALUES (?,?,'ok',?,?,?) ON CONFLICT(unit, business_date) DO UPDATE SET verdict='ok', "
                "checked_by=excluded.checked_by, checked_at=excluded.checked_at, updated_at=excluded.updated_at",
                (_unit, iso, u["user"], now, now))
    _audit(con, u["user"], "salecheck_ok", {"date": iso})
    con.commit()
    return jsonify(ok=True, already=False, date=iso, day=_dmy(iso), at=_hm(now), by=u["user"])


@bp.route("/finance/salecheck/api/issue", methods=["POST"])
def api_issue():
    """Galti hai -> Kaunsa bill -> Kya galti (-> note only for 'Aur kuch') -> Jodo."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    eid, status, err = _day_for(con, kind, iso)
    if err:
        return err
    bill = str(b.get("bill") or "").strip()
    problem = str(b.get("problem") or "").strip()
    note = str(b.get("note") or "").strip()[:200]
    if problem not in PROBLEMS:
        return jsonify(ok=False, error="bad_problem", problems=list(PROBLEMS)), 400
    if problem == "other" and not note:
        return jsonify(ok=False, error="note_required", message="'Aur kuch' ke saath do shabd likhiye."), 400
    p = day_payload(con, iso, kind)
    if not bill or (bill != DAY_BILL and bill not in p["bills"] and problem != "missing_in_marg"):
        return jsonify(ok=False, error="bad_bill", message="Kaunsa bill? List mein se chuniye."), 400
    if con.execute("SELECT 1 FROM sale_check_issue WHERE unit=? AND business_date=? AND bill_no=? AND problem=? "
                   "AND removed_at IS NULL", (_unit, iso, bill, problem)).fetchone():
        return jsonify(ok=False, error="already", already=True,
                       message="Yeh galti pehle hi likhi ja chuki hai — dobara nahi likhi."), 409
    now = now_iso()
    cur = con.execute("INSERT INTO sale_check_issue (unit, business_date, bill_no, problem, note, added_by, added_at) "
                      "VALUES (?,?,?,?,?,?,?)", (_unit, iso, bill, problem, note or None, u["user"], now))
    con.execute("INSERT INTO sale_check_day (unit, business_date, verdict, checked_by, checked_at, updated_at) "
                "VALUES (?,?,'wrong',?,?,?) ON CONFLICT(unit, business_date) DO UPDATE SET verdict='wrong', "
                "checked_by=excluded.checked_by, checked_at=excluded.checked_at, updated_at=excluded.updated_at",
                (_unit, iso, u["user"], now, now))
    _audit(con, u["user"], "salecheck_issue", {"date": iso, "id": cur.lastrowid, "bill": bill, "problem": problem, "note": note})
    con.commit()
    return jsonify(ok=True, id=cur.lastrowid, date=iso, day=_dmy(iso), bill=("Poora din" if bill == DAY_BILL else bill),
                   problem=problem, problem_hi=PROBLEM_HI[problem], note=note, at=_hm(now), issues=_issues(con, iso))


@bp.route("/finance/salecheck/api/issue/remove", methods=["POST"])
def api_issue_remove():
    """Bhati removes his own galti while the day is unapproved; the owner may remove any."""
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        iid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        iid = 0
    r = con.execute("SELECT business_date, bill_no, problem, added_by FROM sale_check_issue WHERE id=? AND unit=? "
                    "AND removed_at IS NULL", (iid, _unit)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found"), 404
    iso = r[0]
    eid, status, err = _day_for(con, kind, iso)
    if err:
        return err
    if kind != "owner" and r[3] != u["user"]:
        return jsonify(ok=False, error="not_yours", message="Yeh galti kisi aur ne likhi thi."), 403
    now = now_iso()
    con.execute("UPDATE sale_check_issue SET removed_by=?, removed_at=? WHERE id=?", (u["user"], now, iid))
    if not _issues(con, iso):
        con.execute("DELETE FROM sale_check_day WHERE unit=? AND business_date=? AND verdict='wrong'", (_unit, iso))
    _audit(con, u["user"], "salecheck_issue_removed", {"date": iso, "id": iid, "bill": r[1], "problem": r[2]})
    con.commit()
    return jsonify(ok=True, id=iid, date=iso, issues=_issues(con, iso))


@bp.route("/finance/salecheck/api/cash", methods=["POST"])
def api_cash():
    """The cash Darpan handed, as Bhati counted it: ONE amount, Dr Bhawna by default / Dr Manoj by one
    tap, the date = the sale date. Lands through darpan_kal's own path (the darpan_kal_day row, _decide,
    the one cash_movement per day). A re-save updates the same row. If Darpan had recorded a different
    amount, Bhati's figure is kept as the checked figure and the difference is shown -- the owner
    decides on his page, as he does today for a short handover."""
    import darpan_kal
    u, con, kind, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    eid, status, err = _day_for(con, kind, iso)
    if err:
        return err
    try:
        amount = int(b.get("amount_p"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount", message="Cash ka amount samajh nahi aaya."), 400
    party = str(b.get("party") or "dr_bhawna").strip()
    if amount < 0 or party not in PARTIES:
        return jsonify(ok=False, error="bad_request", message="Kisko diya — Dr Bhawna ya Dr Manoj?"), 400
    kal = _kal_row(con, iso)
    if kal and kal.get("owner_decision") in ("accept", "reject"):
        return jsonify(ok=False, error="owner_decided", message="Is din par doctor sahab ka faisla ho gaya hai."), 409
    if kal and kal.get("received_at") and kind != "owner":
        return jsonify(ok=False, error="already_received", message="Yeh cash mil chuka hai — ab badla nahi ja sakta."), 409
    prev = _cash_row(con, iso)
    if prev:
        darpan_p, darpan_to = prev["darpan_p"], prev["darpan_to"]
    elif kal and kal.get("handed_p") is not None and kal.get("created_by") != u["user"]:
        darpan_p, darpan_to = int(kal["handed_p"]), kal.get("handed_to")
    else:
        darpan_p, darpan_to = None, None
    now = now_iso()
    if kal:
        con.execute("UPDATE darpan_kal_day SET handed_p=?, handed_to=?, updated_at=? WHERE unit=? AND business_date=?",
                    (amount, party, now, _unit, iso))
    else:
        con.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, state, created_by, created_at, "
                    "updated_at) VALUES (?,?,?,?,'open',?,?,?)", (_unit, iso, amount, party, u["user"], now, now))
    row = darpan_kal._row(con, iso)
    calc = darpan_kal.compute_day(con, iso)
    res = darpan_kal._decide(con, iso, calc, row, u["user"])
    con.execute("INSERT INTO sale_check_cash (unit, business_date, amount_p, party, darpan_p, darpan_to, entered_by, "
                "entered_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(unit, business_date) DO UPDATE SET "
                "amount_p=excluded.amount_p, party=excluded.party, darpan_p=excluded.darpan_p, darpan_to=excluded.darpan_to, "
                "updated_at=excluded.updated_at", (_unit, iso, amount, party, darpan_p, darpan_to, u["user"], now, now))
    _audit(con, u["user"], "salecheck_cash", {"date": iso, "amount_p": amount, "to": party, "darpan_p": darpan_p,
                                              "result": res, "movement": darpan_kal._row(con, iso).get("landed_movement_id")})
    con.commit()
    c = _cash_row(con, iso)
    return jsonify(ok=True, date=iso, day=_dmy(iso), amount_p=amount, amount=rs(amount), to=party, to_hi=PARTY_HI[party],
                   at=_hm(now), darpan_p=darpan_p, darpan=rs(darpan_p), diff_p=c["diff_p"],
                   diff=(rs(abs(c["diff_p"])) if c["diff_p"] else None), state=res.get("state"),
                   movement_id=darpan_kal._row(con, iso).get("landed_movement_id"))


# ------------------------------------------------------------------ routes: the owner
@bp.route("/finance/salecheck/api/owner/move", methods=["POST"])
def api_owner_move():
    """The owner changes the PERSON and/or the DATE of a cash entry Bhati made. A date move is allowed
    only onto another unapproved day that has no handover yet; every change is audited."""
    import darpan_kal
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    party = str(b.get("party") or "").strip() or None
    new = str(b.get("new_date") or "").strip() or None
    if not _valid_date(iso) or (party and party not in PARTIES) or (new and not _valid_date(new)):
        return jsonify(ok=False, error="bad_request"), 400
    sc = _cash_row(con, iso)
    if not sc:
        return jsonify(ok=False, error="not_found", message="Bhati has not entered cash for this day."), 404
    kal = _kal_row(con, iso)
    if not kal:
        return jsonify(ok=False, error="not_found"), 404
    if kal.get("received_at"):
        return jsonify(ok=False, error="already_received", message="this cash is already marked received"), 409
    if kal.get("owner_decision") in ("accept", "reject"):
        return jsonify(ok=False, error="owner_decided"), 409
    now = now_iso()
    if new and new != iso:
        eid2, st2 = _entry(con, new)
        if not eid2 or not _open(st2):
            return jsonify(ok=False, error="not_open", message="the cash can move only to another unapproved day"), 409
        if kal.get("created_by") != sc["by"]:
            return jsonify(ok=False, error="darpan_row", message="Darpan recorded this day himself; change it on his page"), 409
        k2 = _kal_row(con, new)
        if k2 and k2.get("handed_p") is not None:
            return jsonify(ok=False, error="target_has_handover", message="%s already has a handover" % _dmy(new)), 409
        party = party or sc["party"]
        mid = kal.get("landed_movement_id")
        if mid is None:
            r = con.execute("SELECT id FROM cash_movement WHERE day_entry_id=(SELECT id FROM day_entry WHERE unit=? AND "
                            "business_date=?) AND reference LIKE ?", (_unit, iso, "[kal] %s ->%%" % iso)).fetchone()
            mid = r[0] if r else None
        if mid is not None:
            if _has(con, "cash_handover_cover"):
                con.execute("DELETE FROM cash_handover_cover WHERE handover_src='movement' AND handover_id=?", (mid,))
            con.execute("DELETE FROM cash_movement WHERE id=?", (mid,))
        if _has(con, "darpan_kal_owed"):
            con.execute("UPDATE darpan_kal_owed SET status='withdrawn' WHERE unit=? AND business_date=? AND status='open'", (_unit, iso))
        con.execute("DELETE FROM darpan_kal_day WHERE unit=? AND business_date=?", (_unit, iso))
        if k2:
            con.execute("UPDATE darpan_kal_day SET handed_p=?, handed_to=?, updated_at=? WHERE unit=? AND business_date=?",
                        (sc["amount_p"], party, now, _unit, new))
        else:
            con.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, state, created_by, created_at, "
                        "updated_at) VALUES (?,?,?,?,'open',?,?,?)", (_unit, new, sc["amount_p"], party, sc["by"], now, now))
        con.execute("DELETE FROM sale_check_cash WHERE unit=? AND business_date=?", (_unit, iso))
        con.execute("INSERT INTO sale_check_cash (unit, business_date, amount_p, party, darpan_p, darpan_to, entered_by, "
                    "entered_at, updated_at, moved_from) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (_unit, new, sc["amount_p"], party, sc["darpan_p"], sc["darpan_to"], sc["by"], sc["at"], now, iso))
        row = darpan_kal._row(con, new)
        res = darpan_kal._decide(con, new, darpan_kal.compute_day(con, new), row, u["user"])
        _audit(con, u["user"], "salecheck_owner_move", {"from": iso, "to": new, "amount_p": sc["amount_p"], "party": party,
                                                        "old_movement": mid, "result": res})
        con.commit()
        return jsonify(ok=True, date=new, moved_from=iso, party=party, amount=rs(sc["amount_p"]))
    if not party or party == sc["party"]:
        return jsonify(ok=False, error="nothing_to_change"), 400
    con.execute("UPDATE darpan_kal_day SET handed_to=?, updated_at=? WHERE unit=? AND business_date=?", (party, now, _unit, iso))
    row = darpan_kal._row(con, iso)
    res = darpan_kal._decide(con, iso, darpan_kal.compute_day(con, iso), row, u["user"])
    con.execute("UPDATE sale_check_cash SET party=?, updated_at=? WHERE unit=? AND business_date=?", (party, now, _unit, iso))
    _audit(con, u["user"], "salecheck_owner_party", {"date": iso, "from": sc["party"], "to": party, "result": res})
    con.commit()
    return jsonify(ok=True, date=iso, party=party, amount=rs(sc["amount_p"]))


# ------------------------------------------------------------------ the owner's pages read these
def owner_marks(con):
    """business_date -> Bhati's mark for the approvals page: verdict, time, the galti list, his cash entry.
    Fail-soft: an empty dict when the tables are not there yet."""
    out = {}
    try:
        if not _has(con, "sale_check_day"):
            return out
        for d, v, by, at in con.execute("SELECT business_date, verdict, checked_by, checked_at FROM sale_check_day WHERE unit=?", (_unit,)):
            out[d] = dict(verdict=v, by=by, at=_hm(at), n=0, issues=[], cash=None,
                          text=("Bhati ✓ %s" % _hm(at)) if v == "ok" else "")
        for d, bill, prob, note in con.execute("SELECT business_date, bill_no, problem, note FROM sale_check_issue WHERE unit=? "
                                               "AND removed_at IS NULL ORDER BY id", (_unit,)):
            m = out.setdefault(d, dict(verdict="wrong", by="", at="", n=0, issues=[], cash=None, text=""))
            m["n"] += 1
            m["issues"].append(dict(bill=("whole day" if bill == DAY_BILL else bill), problem=PROBLEM_EN.get(prob, prob), note=note or ""))
        for d in list(out):
            if out[d]["n"]:
                out[d]["text"] = "Bhati: %d mistake%s" % (out[d]["n"], "" if out[d]["n"] == 1 else "s")
        for d, amt, party, dp, dto, by, at, up in con.execute("SELECT business_date, amount_p, party, darpan_p, darpan_to, entered_by, "
                                                               "entered_at, updated_at FROM sale_check_cash WHERE unit=?", (_unit,)):
            m = out.setdefault(d, dict(verdict=None, by="", at="", n=0, issues=[], cash=None, text=""))
            diff = (int(amt) - int(dp)) if dp is not None else 0
            m["cash"] = dict(amount=rs(int(amt)), amount_p=int(amt), to=PARTY_EN.get(party, party), party=party, by=by,
                             at=_hm(up or at), darpan=(rs(int(dp)) if dp is not None else None), darpan_to=dto, diff_p=diff,
                             diff=(rs(abs(diff)) if diff else None))
    except Exception:  # noqa: BLE001
        return {}
    return out


def owner_checks(con, iso):
    """The day panel's Checks, in words: Bhati's verdict, his galti list, his cash entry (S400)."""
    try:
        m = owner_marks(con).get(iso)
    except Exception:  # noqa: BLE001
        return []
    if not m:
        return []
    out = []
    if m["n"]:
        out.append(dict(ok=False, text="Bhati found %d mistake%s: %s" % (
            m["n"], "" if m["n"] == 1 else "s",
            "; ".join("%s -- %s%s" % (i["bill"], i["problem"], (" (" + i["note"] + ")") if i["note"] else "") for i in m["issues"]))))
    elif m["verdict"] == "ok":
        out.append(dict(ok=True, text="Bhati checked this day against the paper copy and Marg at %s: correct" % m["at"]))
    c = m.get("cash")
    if c:
        t = "Bhati entered the cash Darpan handed: %s to %s (%s)" % (c["amount"], c["to"], c["at"])
        if c["diff_p"]:
            t += " -- Darpan had recorded %s, %s %s" % (c["darpan"], rs(abs(c["diff_p"])), "more" if c["diff_p"] > 0 else "less")
        out.append(dict(ok=(None if c["diff_p"] else True), text=t))
    return out


def days_with_mistakes(con):
    """How many UNAPPROVED pharmacy days carry a galti of Bhati's (Needs you)."""
    try:
        if not _has(con, "sale_check_issue"):
            return 0
        return int(con.execute("SELECT COUNT(DISTINCT i.business_date) FROM sale_check_issue i JOIN day_entry e "
                               "ON e.unit=i.unit AND e.business_date=i.business_date WHERE i.unit=? AND i.removed_at IS NULL "
                               "AND e.status IN ('submitted','draft')", (_unit,)).fetchone()[0] or 0)
    except Exception:  # noqa: BLE001
        return 0
