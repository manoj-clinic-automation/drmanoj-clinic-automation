#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""darpan_kal.py -- S243_DARPAN_KAL: Darpan's morning page, "Kal ka hisaab".

THE OWNER'S RULING (13-Sep-2026, the spec)
    Every morning the page opens on YESTERDAY, already filled from the sale
    report (auto-applied on arrival since S243_AUTOAPPLY):
        kal ki bikri  -  ghar/procedure ki dawa  -  online (UPI/card)  =  expected cash
    Darpan types ONLY two things: the cash he handed over, and to whom
    (Dr Manoj / Dr Bhawna).  Match -> the day is complete, nobody else involved.
    Short -> the rupee difference and a tap-list of reasons; the SERVER checks
    each reason against the data: confirmed / not confirmable (his word stands)
    / contradicted.  Only a contradiction, a repeat pattern, or a flagged return
    answered "other" reaches the owner's card.
    MORE cash than expected = his own calculation error: recorded as owed back
    to him, no reason asked, visible to him and the owner until returned.
    Second section: yesterday's sale returns as a count, only the FLAGGED ones
    opened, each with a tap-list answer.  No deterrent line anywhere.
    A "received" tap from the recipient may come later; unreceived = amber.

WHAT THIS FILE DELIBERATELY DOES NOT DO
    It never creates a day_entry (the D354 autofile does that; this rides on
    it).  It never edits Marg, sale_item, day_line or day_noncash_bill.  The
    handover lands as ONE cash_movement row on the day's own day_entry -- the
    same record api_handover writes today -- so cash position, the doctors'
    ledgers and v_cash_ledger stay one arithmetic.  Nothing here can fail the
    console: every read of a table another kit owns is fail-soft.

INSTALL: two lines in finance_app.py after the S241_AMIR_DAY mount, by
patch_finance_app_darpan_kal_s243.py.  Flask and the standard library only.
"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

from flask import Blueprint, jsonify, request, send_file

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

bp = Blueprint("darpan_kal", __name__)

_db = None
_require = None
_unit = "medical"

REASONS = ("none", "home_not_in_print", "online_not_on_pos", "return_cash", "carried", "other")
RETURN_ANSWERS = ("slip_checked", "wrong_bill", "exchange", "doctor_said", "other")
PARTIES = ("dr_manoj", "dr_bhawna")
MONEY_FLAGS = ("NEVER BOUGHT", "REFUNDED MORE THAN PAID",
               "RETURNED MORE THAN SOLD", "DISCOUNTED RETURN")
SCHEMA_FILE = os.path.join(HERE, "darpan_kal_schema.sql")
PAGE = os.path.join(HERE, "darpan_kal.html")

# English, for the owner's card; Hindi lives in the page.
REASON_EN = {"none": "within tolerance",
             "home_not_in_print": "home/procedure medicine not in the printout",
             "online_not_on_pos": "an online payment the POS did not show",
             "return_cash": "a return refunded in cash",
             "carried": "carried to the next day",
             "other": "other (his words)"}
ANSWER_EN = {"slip_checked": "patient's slip checked", "wrong_bill": "wrong bill picked",
             "exchange": "exchange, not a refund", "doctor_said": "doctor advised",
             "other": "other (his words)"}


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _yesterday():
    return (dt.date.today() - dt.timedelta(days=1)).isoformat()


def _valid_date(s):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", s or ""))


# ------------------------------------------------------------------ schema
def ensure_schema(con):
    """Idempotent; safe on every boot, safe twice.  The DDL lives in the .sql
    beside this file so the kit, the walk and the box run ONE text."""
    with open(SCHEMA_FILE, encoding="utf-8") as fh:
        con.executescript(fh.read())
    con.commit()


def _audit(con, who, action, detail):
    con.execute("INSERT INTO darpan_kal_audit (at, who, action, detail) VALUES (?,?,?,?)",
                (now_iso(), who, action, json.dumps(detail, ensure_ascii=False)[:600]))


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r else default) or default
    except sqlite3.OperationalError:
        return default


def _int_setting(con, key, default):
    try:
        return int(_setting(con, key, str(default)) or default)
    except (TypeError, ValueError):
        return default


def _has(con, name):
    try:
        return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') "
                                "AND name=?", (name,)).fetchone())
    except sqlite3.OperationalError:
        return False


def _recipients(con):
    """login -> party, from setting darpan_kal.recipients ('manoj:dr_manoj,bhawna:dr_bhawna')."""
    out = {}
    for part in _setting(con, "darpan_kal.recipients", "").split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            if v.strip() in PARTIES:
                out[k.strip().lower()] = v.strip()
    return out


def _who(con, u):
    """owner (checker) | staff (maker) | recipient (viewer named in the setting) | None."""
    roles = set(u.get("roles") or [])
    login = str(u.get("user") or "").lower()
    party = _recipients(con).get(login)
    if "checker" in roles:
        return "owner", party
    if "maker" in roles:
        return "staff", party
    if party:
        return "recipient", party
    return None, None


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


def _auth():
    u, err = _require("maker", "checker", "viewer")
    if err:
        return None, None, None, err
    con = _db()
    ensure_schema(con)
    kind, party = _who(con, u)
    if kind is None:
        return None, None, None, (jsonify(ok=False, error="not_permitted",
                                          message="Yeh page aapke naam par nahin hai."), 403)
    return u, con, (kind, party), None


# ------------------------------------------------------------------ pages
@bp.route("/finance/darpan/kal")
@bp.route("/finance/darpan/kal/<date_iso>")
def page_kal(date_iso=None):
    u, con, who, err = _auth()
    if err:
        return err
    return send_file(PAGE)


@bp.route("/finance/darpan/kal/api/healthz")
def api_healthz():
    return jsonify(ok=True, module="darpan_kal", unit=_unit)


# ------------------------------------------------------------------ arithmetic
def _proc_words(con):
    v = _setting(con, "procedure_customer_name", "")
    return [w.strip().lower() for w in v.split(",") if w.strip()]


def compute_day(con, iso):
    """Expected cash for one day from the books as they stand.  READ-ONLY.
    Every rupee is paise.  Fail-soft on every table another kit owns."""
    out = dict(date=iso, applied=False, day_entry_id=None, filed_status=None,
               gross_p=0, returns_p=0, review_p=0, net_sale_p=0,
               home_p=0, proc_p=0, online_p=0, online_provisional=1, statement_in=False,
               home_bills=[], proc_bills=[], online_txns=[], bills_n=0,
               expected_p=None, note="")
    e = con.execute("SELECT id, status FROM day_entry WHERE unit=? AND business_date=?",
                    (_unit, iso)).fetchone()
    if not e:
        out["note"] = "report not applied yet"
        return out
    out["applied"], out["day_entry_id"], out["filed_status"] = True, e["id"], e["status"]

    # 1 -- the printout's day sale: bills net of credit notes, plus parked review bills
    r = con.execute(
        "SELECT COALESCE(SUM(CASE WHEN service NOT LIKE '%return%' THEN amount_p END),0) sold, "
        " COALESCE(SUM(CASE WHEN service LIKE '%return%' THEN amount_p END),0) ret, "
        " COUNT(CASE WHEN service NOT LIKE '%return%' THEN 1 END) n "
        "FROM sale_item WHERE day_entry_id=?", (e["id"],)).fetchone()
    out["gross_p"], out["returns_p"], out["bills_n"] = int(r["sold"] or 0), int(r["ret"] or 0), int(r["n"] or 0)
    try:
        v = con.execute("SELECT in_review_p FROM v_day_attribution WHERE day_entry_id=?",
                        (e["id"],)).fetchone()
        out["review_p"] = int(v["in_review_p"] or 0) if v is not None else 0
    except sqlite3.OperationalError:
        out["review_p"] = 0
    out["net_sale_p"] = out["gross_p"] - out["returns_p"] + out["review_p"]

    # 2 -- home medicine: the ingest's own tag (S194) UNION the typed head (S179), by bill
    seen = set()
    home = []
    cols = {c[1] for c in con.execute("PRAGMA table_info(sale_item)")}
    if "home_med" in cols:
        for b in con.execute("SELECT source_ref bill, amount_p FROM sale_item WHERE day_entry_id=? "
                             "AND home_med=1 AND service NOT LIKE '%return%'", (e["id"],)):
            k = str(b["bill"] or "").upper()
            if k not in seen:
                seen.add(k)
                home.append(dict(bill=b["bill"], amount_p=int(b["amount_p"] or 0), src="marg"))
    proc = []
    words = _proc_words(con)
    if words:
        like = " OR ".join(["lower(description) LIKE ?"] * len(words))
        for b in con.execute("SELECT source_ref bill, amount_p FROM sale_item WHERE day_entry_id=? "
                             "AND service NOT LIKE '%return%' AND (" + like + ")",
                             [e["id"]] + ["%" + w + "%" for w in words]):
            k = str(b["bill"] or "").upper()
            if k not in seen:
                seen.add(k)
                proc.append(dict(bill=b["bill"], amount_p=int(b["amount_p"] or 0), src="marg"))
    try:
        for b in con.execute("SELECT head, bill_no, amount_p FROM day_noncash_bill WHERE day_entry_id=?",
                             (e["id"],)):
            k = str(b["bill_no"] or "").upper()
            if k in seen:
                continue
            seen.add(k)
            row = dict(bill=b["bill_no"], amount_p=int(b["amount_p"] or 0), src="typed")
            if b["head"] == "procedure_medicine":
                proc.append(row)
            elif b["head"] == "home_medicine":
                home.append(row)
    except sqlite3.OperationalError:
        pass
    out["home_bills"], out["proc_bills"] = home, proc
    out["home_p"] = sum(x["amount_p"] for x in home)
    out["proc_p"] = sum(x["amount_p"] for x in proc)

    # 3 -- online: the bank when its statement is in (all settled modes), else Marg's own modes
    stmt = None
    if _has(con, "upi_statement"):
        stmt = con.execute("SELECT 1 FROM upi_statement WHERE unit=? AND statement_date=?",
                           (_unit, iso)).fetchone()
    if stmt is not None and _has(con, "upi_txn"):
        txns = [dict(amount_p=int(t["amount_p"] or 0), mode=t["mode"], time=t["txn_time"])
                for t in con.execute("SELECT amount_p, mode, txn_time FROM upi_txn WHERE unit=? "
                                     "AND txn_date=? ORDER BY amount_p DESC", (_unit, iso))]
        out["online_txns"] = txns
        out["online_p"] = sum(t["amount_p"] for t in txns)
        out["online_provisional"], out["statement_in"] = 0, True
    else:
        r = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM sale_item WHERE day_entry_id=? "
                        "AND service NOT LIKE '%return%' AND COALESCE(mode,'cash')<>'cash'",
                        (e["id"],)).fetchone()
        out["online_p"] = int(r[0] or 0)
        out["online_provisional"], out["statement_in"] = 1, False

    out["expected_p"] = out["net_sale_p"] - out["home_p"] - out["proc_p"] - out["online_p"]
    return out


# ------------------------------------------------------------------ returns
def _returns_for(con, iso):
    """Yesterday's returns: count, and the FLAGGED ones with their flag.  Every
    source fail-soft.  Bill numbers only -- no name, no number (F-185)."""
    rows, flagged = [], []
    try:
        from finance_returns_audit import returns_for_day                  # noqa: PLC0415
        rows, _s = returns_for_day(con, iso, _unit)
    except Exception:                                                    # noqa: BLE001
        rows = []
    if not rows:
        try:
            rows = [dict(bill=r["source_ref"], amount_p=abs(int(r["amount_p"] or 0)), verdict="ok",
                         lines=[]) for r in con.execute(
                "SELECT s.source_ref, s.amount_p FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
                "WHERE e.unit=? AND e.business_date=? AND s.service LIKE '%return%'", (_unit, iso))]
        except sqlite3.OperationalError:
            rows = []
    large_p = _int_setting(con, "returns.large_p", 100000)
    act_from = _setting(con, "returns.act_from", "2026-09-02")
    desk_flags = {}
    if _has(con, "return_visit"):
        try:
            for v in con.execute("SELECT match_cn, flags, refund_p, closure FROM return_visit "
                                 "WHERE unit=? AND business_date=? AND flags<>'[]'", (_unit, iso)):
                if v["match_cn"]:
                    desk_flags[str(v["match_cn"]).upper()] = v["flags"]
        except sqlite3.OperationalError:
            pass
    answers = {}
    for a in con.execute("SELECT cn_bill, answer, note, answered_at FROM darpan_kal_return_answer "
                         "WHERE unit=? AND business_date=? ORDER BY id", (_unit, iso)):
        answers[str(a["cn_bill"]).upper()] = dict(answer=a["answer"], note=a["note"], at=a["answered_at"])
    for r in rows:
        bill = str(r.get("bill") or "")
        flag = None
        if iso >= act_from:
            if r.get("verdict") in MONEY_FLAGS:
                flag = r["verdict"]
            elif int(r.get("amount_p") or 0) >= large_p:
                flag = "LARGE RETURN"
            elif bill.upper() in desk_flags:
                flag = "DESK FLAG " + str(desk_flags[bill.upper()])[:60]
        if flag:
            lines = [dict(item=(l.get("item") or l.get("item_name") or ""), qty=(l.get("qty") or l.get("qty_raw") or ""))
                     for l in (r.get("lines") or []) if isinstance(l, dict)][:8]
            flagged.append(dict(bill=bill, amount_p=int(r.get("amount_p") or 0), flag=flag,
                                lines=lines, answered=answers.get(bill.upper())))
    return dict(count=len(rows), total_p=sum(int(r.get("amount_p") or 0) for r in rows), flagged=flagged)


# ------------------------------------------------------------------ the checks
def check_reason(con, iso, reason, diff_p, calc):
    """One reason -> (verdict, evidence).  diff_p is handed - expected (negative = short).
    confirmed: the data shows exactly this.  not_confirmable: the data cannot
    say (his word stands).  contradicted: the data shows the opposite."""
    tol = _int_setting(con, "darpan_kal.tolerance_p", 5000)
    gap = abs(int(diff_p))
    ev = dict(reason=reason, diff_p=int(diff_p), tolerance_p=tol)

    if reason == "none":
        return ("confirmed" if gap <= tol else "contradicted"), ev
    if reason == "other":
        return "not_confirmable", ev

    if reason == "home_not_in_print":
        bills = calc["home_bills"] + calc["proc_bills"]
        ev["bills"] = bills
        if not bills:
            # no home/procedure bill exists on this day at all
            ev["why"] = "no home/procedure bill on this day"
            return "contradicted", ev
        if any(abs(b["amount_p"] - gap) <= tol for b in bills) or abs(sum(b["amount_p"] for b in bills) - gap) <= tol:
            return "confirmed", ev
        return "not_confirmable", ev

    if reason == "online_not_on_pos":
        if diff_p > 0:
            ev["why"] = "an unseen online payment cannot produce a surplus"
            return "contradicted", ev
        if not calc["statement_in"]:
            ev["why"] = "bank statement not in yet"
            return "not_confirmable", ev
        cand = []
        if _has(con, "upi_match"):
            try:
                cand = [dict(bill=m["bill_no"], amount_p=int(m["txn_amount_p"] or 0), kind=m["status"])
                        for m in con.execute("SELECT bill_no, txn_amount_p, status FROM upi_match "
                                             "WHERE unit=? AND business_date=? AND status IN ('cash','bank_orphan')",
                                             (_unit, iso))]
            except sqlite3.OperationalError:
                cand = []
        if not cand:
            cand = [dict(bill=None, amount_p=t["amount_p"], kind="txn") for t in calc["online_txns"]]
        ev["candidates"] = cand[:20]
        if any(abs(c["amount_p"] - gap) <= tol for c in cand) or \
                (cand and abs(sum(c["amount_p"] for c in cand if c["kind"] == "cash") - gap) <= tol):
            return "confirmed", ev
        ev["why"] = "statement in; no settled payment of this size outside the bills rung online"
        return "contradicted", ev

    if reason == "return_cash":
        slips, cns = [], []
        if _has(con, "return_visit"):
            try:
                slips = [dict(slip=v["slip_no"], refund_p=int(v["refund_p"] or 0), cn=v["match_cn"])
                         for v in con.execute("SELECT slip_no, refund_p, match_cn FROM return_visit "
                                              "WHERE unit=? AND business_date=? AND closure='cash'", (_unit, iso))]
            except sqlite3.OperationalError:
                slips = []
        try:
            cns = [dict(bill=c["source_ref"], amount_p=abs(int(c["amount_p"] or 0)))
                   for c in con.execute("SELECT s.source_ref, s.amount_p FROM sale_item s "
                                        "JOIN day_entry e ON e.id=s.day_entry_id WHERE e.unit=? "
                                        "AND e.business_date=? AND s.service LIKE '%return%'", (_unit, iso))]
        except sqlite3.OperationalError:
            cns = []
        ev["slips"], ev["credit_notes"] = slips, cns
        if any(abs(s["refund_p"] - gap) <= tol for s in slips if not s["cn"]):
            return "confirmed", ev          # refunded in cash, CN not yet in Marg: exactly this
        if slips or cns:
            return "not_confirmable", ev
        if diff_p < 0:
            ev["why"] = "no refund slip and no credit note on this day"
            return "contradicted", ev
        return "not_confirmable", ev

    if reason == "carried":
        nxt = con.execute("SELECT business_date, diff_p FROM darpan_kal_day WHERE unit=? "
                          "AND business_date>? AND business_date<=date(?, '+2 day') AND diff_p IS NOT NULL "
                          "ORDER BY business_date", (_unit, iso, iso)).fetchall()
        ev["next_days"] = [dict(date=n["business_date"], diff_p=n["diff_p"]) for n in nxt]
        if any(abs(int(n["diff_p"] or 0) + int(diff_p)) <= tol for n in nxt):
            return "confirmed", ev
        try:
            late = dt.date.today() > dt.date.fromisoformat(iso) + dt.timedelta(days=2)
        except ValueError:
            late = False
        if late and nxt:
            ev["why"] = "two days passed; the following days do not return it"
            return "contradicted", ev
        return "not_confirmable", ev

    return "not_confirmable", ev


def patterns(con, as_of=None, days=30):
    """Repeat patterns over the window, each measured on the record itself."""
    as_of = as_of or dt.date.today().isoformat()
    since = (dt.date.fromisoformat(as_of) - dt.timedelta(days=days)).isoformat()
    rows = con.execute("SELECT business_date, diff_p, reason, state, verdict FROM darpan_kal_day "
                       "WHERE unit=? AND business_date BETWEEN ? AND ? AND handed_p IS NOT NULL "
                       "ORDER BY business_date", (_unit, since, as_of)).fetchall()
    out = []
    by_reason = {}
    for r in rows:
        if r["reason"] and r["reason"] != "none":
            by_reason.setdefault(r["reason"], []).append(r["business_date"])
    for reason, ds in by_reason.items():
        if len(ds) >= 3:
            out.append(dict(kind="same_reason", reason=reason, n=len(ds), dates=ds,
                            line="pattern: \"%s\" %d times in %d days" % (REASON_EN.get(reason, reason), len(ds), days)))
    tol = _int_setting(con, "darpan_kal.tolerance_p", 5000)
    nz = [r for r in rows if abs(int(r["diff_p"] or 0)) > tol][-10:]
    short = sum(1 for r in nz if int(r["diff_p"]) < 0)
    if len(nz) >= 5 and short >= 5 and short == len(nz):
        out.append(dict(kind="one_way", n=short, line="pattern: the last %d differences are all short" % short))
    carried = [r for r in rows if r["reason"] == "carried" and r["state"] not in ("complete",)
               and r["business_date"] <= (dt.date.fromisoformat(as_of) - dt.timedelta(days=2)).isoformat()]
    if carried:
        out.append(dict(kind="carried_open", n=len(carried), dates=[r["business_date"] for r in carried],
                        line="pattern: \"carried to tomorrow\" still open after 2 days (%d)" % len(carried)))
    cap = _int_setting(con, "darpan_kal.month_cap_p", 200000)
    tot = sum(abs(int(r["diff_p"] or 0)) for r in rows if int(r["diff_p"] or 0) < 0)
    if tot > cap:
        out.append(dict(kind="month_cap", amount_p=tot, cap_p=cap,
                        line="pattern: shortfalls total Rs %d in %d days (cap Rs %d)" % (tot // 100, days, cap // 100)))
    return out


# ------------------------------------------------------------------ landing
def _land_movement(con, iso, calc, handed_p, party, who):
    """One cash_movement on the day's own day_entry -- the record api_handover
    writes today.  A re-typed handover UPDATES the same row (reference '[kal] D').
    Refuses to double a custody event already recorded for the same date+party+amount."""
    if not calc["applied"] or handed_p <= 0:
        return None
    ref = "[kal] %s -> %s" % (iso, party)
    eid = calc["day_entry_id"]
    ex = con.execute("SELECT id FROM cash_movement WHERE day_entry_id=? AND reference LIKE ?",
                     (eid, "[kal] %s ->%%" % iso)).fetchone()
    if ex:
        con.execute("UPDATE cash_movement SET direction='out', party=?, amount_p=?, reference=? WHERE id=?",
                    (party, handed_p, ref, ex["id"]))
        return ex["id"]
    if _has(con, "cash_custody_event"):
        try:
            dup = con.execute("SELECT id FROM cash_custody_event WHERE unit=? AND amount_p=? "
                              "AND to_party=? AND event_date=?", (_unit, handed_p, party, iso)).fetchone()
            if dup:
                _audit(con, who, "landing_skipped_custody_dup", {"date": iso, "custody_id": dup["id"]})
                return None
        except sqlite3.OperationalError:
            pass
    cur = con.execute("INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference) "
                      "VALUES (?,'out',?,?,?)", (eid, party, handed_p, ref))
    return cur.lastrowid


def _row(con, iso):
    r = con.execute("SELECT * FROM darpan_kal_day WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
    return dict(r) if r else None


def _checks(con, iso):
    return [dict(reason=c["reason"], verdict=c["verdict"], at=c["checked_at"],
                 evidence=json.loads(c["evidence_json"] or "{}"))
            for c in con.execute("SELECT reason, verdict, evidence_json, checked_at FROM darpan_kal_check "
                                 "WHERE unit=? AND business_date=? ORDER BY id DESC LIMIT 6", (_unit, iso))]


def _owed(con, iso=None):
    q = "SELECT * FROM darpan_kal_owed WHERE unit=? AND status='open'"
    args = [_unit]
    if iso:
        q += " AND business_date=?"
        args.append(iso)
    return [dict(r) for r in con.execute(q + " ORDER BY business_date DESC", args)]


def _decide(con, iso, calc, row, who):
    """Re-derive diff/verdict/state for a stored handover from the current books
    (used when the bank statement lands after the claim, and on every save)."""
    tol = _int_setting(con, "darpan_kal.tolerance_p", 5000)
    handed = int(row["handed_p"])
    if not calc["applied"]:
        con.execute("UPDATE darpan_kal_day SET state='waiting_report', updated_at=? WHERE unit=? AND business_date=?",
                    (now_iso(), _unit, iso))
        return dict(state="waiting_report", diff_p=None, verdict=None)
    diff = handed - int(calc["expected_p"])
    reason = row.get("reason")
    verdict, state = None, "open"
    if abs(diff) <= tol:
        reason, verdict, state = "none", "confirmed", "complete"
    elif diff > 0:
        # MORE than expected: his own calculation error -- owed back, no reason asked
        reason, verdict, state = "none", "confirmed", "complete"
    elif reason and reason != "none":
        verdict, ev = check_reason(con, iso, reason, diff, calc)
        con.execute("INSERT INTO darpan_kal_check (unit, business_date, reason, verdict, evidence_json, checked_at) "
                    "VALUES (?,?,?,?,?,?)", (_unit, iso, reason, verdict, json.dumps(ev, ensure_ascii=False)[:4000], now_iso()))
        state = {"confirmed": "complete", "not_confirmable": "explained", "contradicted": "needs_owner"}[verdict]
    else:
        reason, verdict, state = None, None, "open"           # short, no reason yet
    mid = _land_movement(con, iso, calc, handed, row["handed_to"], who)
    con.execute("UPDATE darpan_kal_day SET net_sale_p=?, home_p=?, proc_p=?, online_p=?, online_provisional=?, "
                "expected_p=?, diff_p=?, reason=?, verdict=?, state=?, decided_by=?, decided_at=?, "
                "landed_movement_id=COALESCE(?, landed_movement_id), updated_at=? WHERE unit=? AND business_date=?",
                (calc["net_sale_p"], calc["home_p"], calc["proc_p"], calc["online_p"], calc["online_provisional"],
                 calc["expected_p"], diff, reason, verdict, state, "system", now_iso(), mid, now_iso(), _unit, iso))
    # owed back to him: keep exactly one open row per day, sized to the verified excess
    if diff > tol:
        con.execute("INSERT INTO darpan_kal_owed (unit, business_date, amount_p, provisional, created_at) "
                    "VALUES (?,?,?,?,?) ON CONFLICT(unit, business_date) DO UPDATE SET "
                    "amount_p=CASE WHEN darpan_kal_owed.status='open' THEN excluded.amount_p ELSE darpan_kal_owed.amount_p END, "
                    "provisional=excluded.provisional",
                    (_unit, iso, diff, calc["online_provisional"], now_iso()))
    else:
        con.execute("UPDATE darpan_kal_owed SET status='withdrawn' WHERE unit=? AND business_date=? AND status='open'",
                    (_unit, iso))
    return dict(state=state, diff_p=diff, verdict=verdict, reason=reason)


def _refresh_if_needed(con, iso, who="system"):
    """A day decided on Marg's modes is re-decided once the bank statement lands."""
    row = _row(con, iso)
    if not row or row.get("handed_p") is None:
        return
    calc = compute_day(con, iso)
    if (row.get("state") == "waiting_report" and calc["applied"]) or \
            (int(row.get("online_provisional") or 0) == 1 and calc["statement_in"]):
        _decide(con, iso, calc, row, who)
        con.commit()


# ------------------------------------------------------------------ api: the day
def _day_payload(con, iso, who):
    _refresh_if_needed(con, iso)
    calc = compute_day(con, iso)
    row = _row(con, iso)
    tol = _int_setting(con, "darpan_kal.tolerance_p", 5000)
    return dict(ok=True, date=iso, unit=_unit, me=dict(kind=who[0], party=who[1]),
                tolerance_p=tol, calc=calc, day=row, checks=(_checks(con, iso) if row else []),
                returns=_returns_for(con, iso), owed=_owed(con), reasons=list(REASONS),
                return_answers=list(RETURN_ANSWERS), parties=list(PARTIES))


@bp.route("/finance/darpan/kal/api/day")
def api_day():
    u, con, who, err = _auth()
    if err:
        return err
    iso = str(request.args.get("date") or "").strip() or _yesterday()
    if not _valid_date(iso):
        return jsonify(ok=False, error="bad_date"), 400
    if who[0] == "recipient":
        row = _row(con, iso)
        if not row or row.get("handed_to") != who[1]:
            return jsonify(ok=False, error="not_yours", message="Yeh din aapko nahin diya gaya."), 403
    return jsonify(**_day_payload(con, iso, who))


@bp.route("/finance/darpan/kal/api/handover", methods=["POST"])
def api_handover():
    """The two inputs (+ a reason when short).  Re-typing before the owner has
    decided corrects the same row; every version is in darpan_kal_audit."""
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip() or _yesterday()
    if not _valid_date(iso):
        return jsonify(ok=False, error="bad_date"), 400
    if iso > dt.date.today().isoformat():
        return jsonify(ok=False, error="future_date", message="Aane wala din nahin likha ja sakta."), 400
    try:
        handed = int(b.get("handed_p"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount", message="Cash ka amount samajh nahin aaya."), 400
    party = str(b.get("handed_to") or "").strip()
    if handed < 0 or party not in PARTIES:
        return jsonify(ok=False, error="bad_request", message="Kisko diya -- Dr Manoj ya Dr Bhawna?"), 400
    reason = str(b.get("reason") or "").strip() or None
    note = str(b.get("reason_note") or "").strip()[:200]
    if reason is not None and reason not in REASONS:
        return jsonify(ok=False, error="bad_reason", reasons=list(REASONS)), 400
    if reason == "other" and not note:
        return jsonify(ok=False, error="note_required", message="Do shabd likhiye -- kya hua?"), 400
    row = _row(con, iso)
    if row and row.get("owner_decision") in ("accept", "reject"):
        return jsonify(ok=False, error="owner_decided",
                       message="Is din par doctor sahab ka faisla ho gaya hai."), 409
    if row and row.get("received_at") and who[0] != "owner":
        return jsonify(ok=False, error="already_received",
                       message="Yeh cash mil chuka hai -- ab badla nahin ja sakta."), 409
    con.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, reason, reason_note, "
                " state, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,'open',?,?,?) "
                "ON CONFLICT(unit, business_date) DO UPDATE SET handed_p=excluded.handed_p, "
                " handed_to=excluded.handed_to, reason=excluded.reason, reason_note=excluded.reason_note, "
                " updated_at=excluded.updated_at",
                (_unit, iso, handed, party, reason, note or None, u["user"], now_iso(), now_iso()))
    row = _row(con, iso)
    calc = compute_day(con, iso)
    res = _decide(con, iso, calc, row, u["user"])
    _audit(con, u["user"], "handover", {"date": iso, "handed_p": handed, "to": party, "reason": reason,
                                        "note": note, "result": res})
    con.commit()
    return jsonify(ok=True, date=iso, **res, needs_reason=(res["state"] == "open"),
                   expected_p=calc["expected_p"], day=_row(con, iso), checks=_checks(con, iso),
                   owed=_owed(con, iso))


@bp.route("/finance/darpan/kal/api/return-answer", methods=["POST"])
def api_return_answer():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    bill = str(b.get("cn_bill") or "").strip().upper()
    ans = str(b.get("answer") or "").strip()
    note = str(b.get("note") or "").strip()[:200]
    flag = str(b.get("flag") or "").strip()[:80]
    if not _valid_date(iso) or not bill or ans not in RETURN_ANSWERS:
        return jsonify(ok=False, error="bad_request", answers=list(RETURN_ANSWERS)), 400
    if ans == "other" and not note:
        return jsonify(ok=False, error="note_required", message="Do shabd likhiye."), 400
    con.execute("INSERT INTO darpan_kal_return_answer (unit, business_date, cn_bill, flag, answer, note, "
                "answered_by, answered_at) VALUES (?,?,?,?,?,?,?,?)",
                (_unit, iso, bill, flag or None, ans, note or None, u["user"], now_iso()))
    # a MONEY flag answered "other", or "slip checked" against NEVER BOUGHT, is the owner's
    if ans == "other" or (flag == "NEVER BOUGHT" and ans == "slip_checked"):
        con.execute("INSERT INTO darpan_kal_day (unit, business_date, state, created_by, created_at, updated_at) "
                    "VALUES (?,?,'needs_owner',?,?,?) ON CONFLICT(unit, business_date) DO UPDATE SET "
                    "state=CASE WHEN darpan_kal_day.state IN ('complete','explained','open','waiting_report') "
                    "THEN 'needs_owner' ELSE darpan_kal_day.state END, updated_at=excluded.updated_at",
                    (_unit, iso, u["user"], now_iso(), now_iso()))
    _audit(con, u["user"], "return_answer", {"date": iso, "bill": bill, "answer": ans, "note": note, "flag": flag})
    con.commit()
    return jsonify(ok=True, date=iso, cn_bill=bill, answer=ans)


# ------------------------------------------------------------------ api: recipient
@bp.route("/finance/darpan/kal/api/mine")
def api_mine():
    """The days handed to THIS login (Dr Bhawna's list; the owner's too)."""
    u, con, who, err = _auth()
    if err:
        return err
    party = who[1]
    if who[0] == "owner" and not party:
        party = "dr_manoj"
    if not party:
        return jsonify(ok=False, error="not_recipient"), 403
    rows = [dict(r) for r in con.execute(
        "SELECT business_date, handed_p, handed_to, expected_p, diff_p, state, received_by, received_at "
        "FROM darpan_kal_day WHERE unit=? AND handed_to=? AND handed_p IS NOT NULL "
        "ORDER BY business_date DESC LIMIT 60", (_unit, party))]
    return jsonify(ok=True, party=party, days=rows,
                   unreceived=sum(1 for r in rows if not r["received_at"]))


@bp.route("/finance/darpan/kal/api/received", methods=["POST"])
def api_received():
    """The recipient's tap: 'mila'.  The physical copy is the proof; this may come
    late.  Only the named recipient, or the owner, can stamp it."""
    u, con, who, err = _auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    if not _valid_date(iso):
        return jsonify(ok=False, error="bad_date"), 400
    row = _row(con, iso)
    if not row or row.get("handed_p") is None:
        return jsonify(ok=False, error="not_found"), 404
    if who[0] != "owner" and row.get("handed_to") != who[1]:
        return jsonify(ok=False, error="not_yours", message="Yeh din aapko nahin diya gaya."), 403
    if row.get("received_at"):
        return jsonify(ok=False, error="already_received", received_by=row["received_by"]), 409
    con.execute("UPDATE darpan_kal_day SET received_by=?, received_at=?, updated_at=? WHERE unit=? AND business_date=?",
                (u["user"], now_iso(), now_iso(), _unit, iso))
    _audit(con, u["user"], "received", {"date": iso, "handed_p": row["handed_p"], "to": row["handed_to"]})
    con.commit()
    return jsonify(ok=True, date=iso, received_by=u["user"])


# ------------------------------------------------------------------ api: owner
def _en_line(r):
    diff = int(r.get("diff_p") or 0)
    word = "short" if diff < 0 else "over"
    line = "%s · %s Rs %d" % (r["business_date"], word, abs(diff) // 100)
    if r.get("reason") and r["reason"] != "none":
        line += " · said \"%s\"" % REASON_EN.get(r["reason"], r["reason"])
    if r.get("verdict"):
        line += " · %s" % r["verdict"].replace("_", " ")
    return line


@bp.route("/finance/darpan/kal/api/owner")
def api_owner():
    """The owner's card: ONE line per item, English.  Only what needs him:
    contradictions, repeat patterns, flagged returns he should see, cash owed
    back to Darpan, handovers not yet received, a report still not applied."""
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    days = min(int(request.args.get("days", "30") or 30), 120)
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    for r in con.execute("SELECT business_date FROM darpan_kal_day WHERE unit=? AND business_date>=? "
                         "AND (online_provisional=1 OR state='waiting_report')", (_unit, since)):
        _refresh_if_needed(con, r["business_date"])
    items = []
    for r in con.execute("SELECT * FROM darpan_kal_day WHERE unit=? AND business_date>=? AND state='needs_owner' "
                         "AND owner_decision IS NULL ORDER BY business_date DESC", (_unit, since)):
        r = dict(r)
        ev = [c for c in _checks(con, r["business_date"])][:1]
        why = (ev[0]["evidence"].get("why") if ev and isinstance(ev[0].get("evidence"), dict) else None)
        items.append(dict(kind="day", date=r["business_date"], line=_en_line(r) + ((" — " + why) if why else ""),
                          diff_p=r["diff_p"], reason=r["reason"], note=r["reason_note"], verdict=r["verdict"],
                          link="/finance/darpan/kal/%s?view=owner" % r["business_date"]))
    for p in patterns(con, days=30):
        items.append(dict(kind="pattern", line=p["line"], detail=p))
    for a in con.execute("SELECT * FROM darpan_kal_return_answer WHERE unit=? AND business_date>=? "
                         "AND (answer='other' OR flag IN ('NEVER BOUGHT','REFUNDED MORE THAN PAID','RETURNED MORE THAN SOLD')) "
                         "ORDER BY id DESC LIMIT 40", (_unit, since)):
        items.append(dict(kind="return", date=a["business_date"], bill=a["cn_bill"],
                          line="%s · return %s · %s · Darpan: %s%s" % (
                              a["business_date"], a["cn_bill"], a["flag"] or "flagged",
                              ANSWER_EN.get(a["answer"], a["answer"]), (" — " + a["note"]) if a["note"] else ""),
                          link="/finance/darpan/kal/%s?view=owner" % a["business_date"]))
    owed = _owed(con)
    for o in owed:
        items.append(dict(kind="owed", date=o["business_date"], id=o["id"], amount_p=o["amount_p"],
                          line="%s · Rs %d owed back to Darpan%s" % (o["business_date"], o["amount_p"] // 100,
                                                                     " (bank not in yet)" if o["provisional"] else "")))
    unrec = [dict(r) for r in con.execute(
        "SELECT business_date, handed_p, handed_to FROM darpan_kal_day WHERE unit=? AND business_date>=? "
        "AND handed_p IS NOT NULL AND received_at IS NULL ORDER BY business_date DESC", (_unit, since))]
    for r in unrec:
        items.append(dict(kind="unreceived", date=r["business_date"], amber=True,
                          line="%s · Rs %d to %s · not yet marked received" % (
                              r["business_date"], int(r["handed_p"]) // 100, r["handed_to"].replace("dr_", "Dr ").title())))
    y = _yesterday()
    if not compute_day(con, y)["applied"] and dt.datetime.now().hour >= 11:
        items.append(dict(kind="late_report", date=y, line="%s · sale report not applied yet" % y))
    con.commit()
    stats = con.execute("SELECT COUNT(*) n, SUM(state='complete') c, SUM(state='explained') e, "
                        "SUM(state='needs_owner') o FROM darpan_kal_day WHERE unit=? AND business_date>=? "
                        "AND handed_p IS NOT NULL", (_unit, since)).fetchone()
    return jsonify(ok=True, since=since, items=items, count=sum(1 for i in items if not i.get("amber")),
                   amber=len(unrec), owed_p=sum(o["amount_p"] for o in owed),
                   days=dict(n=stats["n"] or 0, complete=stats["c"] or 0, explained=stats["e"] or 0,
                             needs_owner=stats["o"] or 0))


@bp.route("/finance/darpan/kal/api/owner/decide", methods=["POST"])
def api_owner_decide():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    dec = str(b.get("decision") or "").strip()
    note = str(b.get("note") or "").strip()[:300]
    if not _valid_date(iso) or dec not in ("accept", "reject", "ask"):
        return jsonify(ok=False, error="bad_request"), 400
    if dec in ("reject", "ask") and not note:
        return jsonify(ok=False, error="note_required", message="say why, or what to ask"), 400
    if not _row(con, iso):
        return jsonify(ok=False, error="not_found"), 404
    new_state = {"accept": "explained", "reject": "needs_owner", "ask": "open"}[dec]
    con.execute("UPDATE darpan_kal_day SET owner_decision=?, owner_note=?, owner_by=?, owner_at=?, state=?, "
                "updated_at=? WHERE unit=? AND business_date=?",
                (dec, note or None, u["user"], now_iso(), new_state, now_iso(), _unit, iso))
    _audit(con, u["user"], "owner_" + dec, {"date": iso, "note": note})
    con.commit()
    return jsonify(ok=True, date=iso, decision=dec, state=new_state)


@bp.route("/finance/darpan/kal/api/owed/returned", methods=["POST"])
def api_owed_returned():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    try:
        oid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        oid = 0
    r = con.execute("SELECT id, status FROM darpan_kal_owed WHERE id=? AND unit=?", (oid, _unit)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found"), 404
    if r["status"] != "open":
        return jsonify(ok=False, error="not_open", status=r["status"]), 409
    con.execute("UPDATE darpan_kal_owed SET status='returned', returned_by=?, returned_at=?, note=? WHERE id=?",
                (u["user"], now_iso(), str(b.get("note") or "")[:200] or None, oid))
    _audit(con, u["user"], "owed_returned", {"id": oid})
    con.commit()
    return jsonify(ok=True, id=oid, status="returned")
