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

S403 (D618, 26-Sep-2026): the day payload carries 'ortho_short' -- the orthotic shortages of the Purchase orders
screen (porders.shortage_summary, read in-process, fail-soft) -- for the card 'Orthotic kam hai -- N' on the page.

S496 (the owner, 07-Oct-2026 12:17; built by the PARENT chat with the Sanjeevni chat's agreement, a PLANNED line on
the board first): when the bank's statement for a day has not come after its time, Darpan's same form offers ONE
optional figure -- yesterday's UPI total, read from the POS machine.  It changes nothing until Dr Manoj confirms
it (on the approvals page's Kal ka hisaab card).  From then compute_day uses it in place of Marg's own non-cash
figure -- STILL online_provisional = 1, online_source = 'pos', marked "provisional — POS total, bank not in" -- and
the day is re-decided exactly as _refresh_if_needed re-decides it when the bank's file lands.  The bank's own
statement replaces it by itself (the statement row is read first, as before).  The store and its rules are
bank_standin.py (the parent's); every read of it here is fail-soft: without it this file behaves as c45bb343 did.
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
    try:                                           # S496: a POS total confirmed for this unit -> the day is decided again
        import bank_standin
        bank_standin.on_change(unit, _s496_changed)
    except Exception as ex:                        # noqa: BLE001 -- without it the page is as it was
        print("bank_standin not beside darpan_kal: %s" % ex)
    try:                                           # S365: the owner's day panel (sanjeevni_day.py)
        import sanjeevni_day
        sanjeevni_day.init(app, db_getter, require_fn, unit)
    except Exception as ex:                        # noqa: BLE001 -- the page falls back to the old panel
        print("sanjeevni_day not mounted: %s" % ex)
    try:                                           # S368: the approvals tree's read door (sanjeevni_approvals.py)
        import sanjeevni_approvals
        sanjeevni_approvals.init(app, db_getter, require_fn, unit)
    except Exception as ex:                        # noqa: BLE001 -- the page then says what it could not read
        print("sanjeevni_approvals not mounted: %s" % ex)
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
               home_p=0, proc_p=0, online_p=0, online_provisional=1, statement_in=False, adjust_p=0,
               online_source="marg", marg_online_p=None, standin=None,          # S496
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
        out["online_source"] = "bank"
    else:
        r = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM sale_item WHERE day_entry_id=? "
                        "AND service NOT LIKE '%return%' AND COALESCE(mode,'cash')<>'cash'",
                        (e["id"],)).fetchone()
        out["online_p"] = int(r[0] or 0)
        out["online_provisional"], out["statement_in"] = 1, False
        out["marg_online_p"] = out["online_p"]
        sp = _s496_standing(con, iso)              # S496: the owner-confirmed POS total, only while the bank is not in
        if sp is not None:
            out["online_p"] = int(sp["amount_p"])  # still provisional: the bank's own statement replaces it by itself
            out["online_source"] = "pos"
            out["standin"] = dict(amount_p=int(sp["amount_p"]), typed_by=sp["typed_by"], confirmed_by=sp["confirmed_by"],
                                  by_owner=bool(sp["by_owner"]), never=bool(sp["never"]), label=sp["label"])

    # S357 -- the ledger's own +/- column: a credit note on a home / procedure bill is put
    # back to the drawer there by day_resync (goods returned, no cash; the owner, 20-Sep).
    out["adjust_p"] = 0
    if _has(con, "cash_adjustment"):
        try:
            r = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM cash_adjustment WHERE day_entry_id=?",
                            (e["id"],)).fetchone()
            out["adjust_p"] = int(r[0] or 0)
        except sqlite3.OperationalError:
            out["adjust_p"] = 0
    out["expected_p"] = out["net_sale_p"] - out["home_p"] - out["proc_p"] - out["online_p"] + out["adjust_p"]
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
        _cover(con, "movement", ex["id"], iso, handed_p, who)
        return ex["id"]
    if _has(con, "cash_custody_event"):
        try:
            dup = con.execute("SELECT id FROM cash_custody_event WHERE unit=? AND amount_p=? "
                              "AND to_party=? AND event_date=?", (_unit, handed_p, party, iso)).fetchone()
            if dup:
                _audit(con, who, "landing_skipped_custody_dup", {"date": iso, "custody_id": dup["id"]})
                _cover(con, "custody", dup["id"], iso, handed_p, who)
                return None
        except sqlite3.OperationalError:
            pass
    cur = con.execute("INSERT INTO cash_movement (day_entry_id, direction, party, amount_p, reference) "
                      "VALUES (?,'out',?,?,?)", (eid, party, handed_p, ref))
    _cover(con, "movement", cur.lastrowid, iso, handed_p, who)
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
            (int(row.get("online_provisional") or 0) == 1 and calc["statement_in"]) or \
            (calc["applied"] and calc.get("online_source") == "pos" and row.get("state") != "waiting_report"
             and int(row.get("online_p") or 0) != int(calc["online_p"])):      # S496: decided before the POS total was confirmed
        _decide(con, iso, calc, row, who)
        con.commit()


def _orders_today_safe(con):
    """S410 (D626): 'Aaj ke order -- N (M bheja)' for Darpan's card, read from order_rules in-process; never breaks the page."""
    try:
        import order_rules                                   # noqa: PLC0415
        return order_rules.day_summary(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, n=0, sent=0, unsent=0, text="", error=str(e)[:80])


def _ortho_short_safe(con):
    """S403 (D618): 'Orthotic kam hai -- N' for Darpan's card, read from porders in-process; never breaks the page."""
    try:
        import porders                                       # noqa: PLC0415
        return porders.shortage_summary(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, n=0, items=[], error=str(e)[:80])


# ------------------------------------------------------------------ api: the day
def _day_payload(con, iso, who):
    _refresh_if_needed(con, iso)
    calc = compute_day(con, iso)
    row = _row(con, iso)
    tol = _int_setting(con, "darpan_kal.tolerance_p", 5000)
    return dict(ok=True, date=iso, unit=_unit, me=dict(kind=who[0], party=who[1]),
                tolerance_p=tol, calc=calc, day=row, checks=(_checks(con, iso) if row else []),
                returns=_returns_for(con, iso), owed=_owed(con), reasons=list(REASONS),
                return_answers=list(RETURN_ANSWERS), parties=list(PARTIES),
                ortho_short=_ortho_short_safe(con),            # S403 (D618)
                orders_today=_orders_today_safe(con),          # S410 (D626)
                amir_claims=_s446_claims(con),                 # S446 (D648): Amir's supplier claims -- Darpan's queue
                pos_total=_s496_day(con, iso),                 # S496: the one optional figure, only while the bank's report is missing
                order_sheet=_s454_sheet_safe(con))             # S454 (D666): his order sheet -- taken, or refused


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


# ------------------------------------------------------------------ api: cash received (S359)
# THE OWNER'S RULING (20-Sep-2026, 22:4x): Darpan hands the cash daily, to Dr Manoj or to
# Dr Bhawna, and BOTH must be able to log it -- he can, or they can.  The same row, the
# same landing, the same verdict as Darpan's own entry; the recipient's log is also the
# 'received' stamp.  The backlog is cleared the same way: every counter day since the
# log-from date with a filed report and no handover is listed with its expected cash,
# and the doctor logs it (one day, or all as expected).
MONTH_PAGE = os.path.join(HERE, "darpan_month.html")


def _log_from(con):
    return _setting(con, "darpan_kal.log_from", "2026-09-01")


def _covered_days(con):
    """S362: counter days already paid over, as the one calculation's cover records
    them (every August handover mapped at S361, every log from now on) -- never asked again."""
    if not _has(con, "cash_handover_cover"):
        return set()
    return {r[0] for r in con.execute("SELECT DISTINCT covers_date FROM cash_handover_cover WHERE unit=?",
                                      (_unit,))}


def _cover(con, src, hid, iso, amount_p, who):
    """S362: record which day a handover paid for, in the one calculation's register."""
    if hid is None or not _has(con, "cash_handover_cover"):
        return
    con.execute("DELETE FROM cash_handover_cover WHERE handover_src=? AND handover_id=?", (src, hid))
    con.execute("INSERT INTO cash_handover_cover (unit, handover_src, handover_id, covers_date, amount_p, "
                "note, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?)",
                (_unit, src, hid, iso, int(amount_p), "darpan_kal: the day this handover paid for", who, now_iso()))


def _pending_days(con, who):
    """Days the doctor may still log or stamp: unlogged counter days (a filed day_entry,
    no handover) and handovers typed but not yet received (the recipient sees only hers)."""
    since, until = _log_from(con), _yesterday()
    out = []
    covered = _covered_days(con)
    for r in con.execute("SELECT business_date, status FROM day_entry WHERE unit=? AND business_date BETWEEN ? AND ? "
                         "AND status <> 'closed_holiday' ORDER BY business_date", (_unit, since, until)):
        iso = r["business_date"]
        row = _row(con, iso)
        if (iso in covered or (r["status"] in ("approved", "locked") and iso >= _anchor_date(con))) and \
                not (row and row.get("handed_p") is not None and not row.get("received_at")):
            continue                                   # S363: paid over, or approved (= to the pool)
        if row and row.get("handed_p") is not None:
            if row.get("received_at"):
                continue
            if who[0] == "recipient" and row.get("handed_to") != who[1]:
                continue
            out.append(dict(date=iso, kind="unreceived", expected_p=row.get("expected_p"),
                            handed_p=int(row["handed_p"]), handed_to=row.get("handed_to"), state=row.get("state"),
                            typed_by=row.get("created_by")))
            continue
        calc = compute_day(con, iso)
        out.append(dict(date=iso, kind="unlogged", expected_p=calc["expected_p"], applied=calc["applied"],
                        online_provisional=calc["online_provisional"], filed_status=r["status"]))
    return out


@bp.route("/finance/darpan/kal/api/pending")
def api_pending():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("owner", "recipient"):
        return jsonify(ok=False, error="doctors_only"), 403
    days = _pending_days(con, who)
    return jsonify(ok=True, me=dict(kind=who[0], party=who[1] or ("dr_manoj" if who[0] == "owner" else None)),
                   log_from=_log_from(con), days=days,
                   unlogged=sum(1 for d in days if d["kind"] == "unlogged"),
                   unreceived=sum(1 for d in days if d["kind"] == "unreceived"),
                   expected_total_p=sum(int(d["expected_p"] or 0) for d in days if d["kind"] == "unlogged" and d.get("expected_p") is not None))


def _log_one(con, u, who, iso, amount_p, party):
    """One day: the handover row (typed by the doctor when Darpan has not), decided and
    landed exactly as Darpan's own entry, then stamped received by the doctor."""
    if iso > dt.date.today().isoformat():
        return dict(date=iso, ok=False, error="future_date")
    row = _row(con, iso)
    calc = compute_day(con, iso)
    if row and row.get("handed_p") is not None:
        if row.get("received_at"):
            return dict(date=iso, ok=False, error="already_received", received_by=row["received_by"])
        if who[0] == "recipient" and row.get("handed_to") != who[1]:
            return dict(date=iso, ok=False, error="not_yours")
        if amount_p is not None and int(amount_p) != int(row["handed_p"]):
            if who[0] != "owner":
                return dict(date=iso, ok=False, error="amount_differs", handed_p=int(row["handed_p"]),
                            message="Darpan typed a different amount; only the owner may change it")
            con.execute("UPDATE darpan_kal_day SET handed_p=?, handed_to=?, updated_at=? WHERE unit=? AND business_date=?",
                        (int(amount_p), party, now_iso(), _unit, iso))
            row = _row(con, iso)
            _decide(con, iso, calc, row, u["user"])
        elif row.get("landed_movement_id") is None or row.get("state") == "waiting_report":
            _decide(con, iso, calc, row, u["user"])      # a handover typed before the report: land it now
        typed = row.get("created_by")
    else:
        if not calc["applied"] and amount_p is None:
            return dict(date=iso, ok=False, error="no_report", message="Marg report not applied yet; type the amount")
        handed = int(amount_p) if amount_p is not None else int(calc["expected_p"] or 0)
        if handed < 0:
            return dict(date=iso, ok=False, error="bad_amount")
        con.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, state, created_by, created_at, "
                    " updated_at) VALUES (?,?,?,?,'open',?,?,?)",
                    (_unit, iso, handed, party, u["user"], now_iso(), now_iso()))
        row = _row(con, iso)
        _decide(con, iso, calc, row, u["user"])
        typed = u["user"]
    con.execute("UPDATE darpan_kal_day SET received_by=?, received_at=?, updated_at=? WHERE unit=? AND business_date=?",
                (u["user"], now_iso(), now_iso(), _unit, iso))
    row = _row(con, iso)
    _audit(con, u["user"], "cash_logged", {"date": iso, "handed_p": row["handed_p"], "to": row["handed_to"],
                                           "typed_by": typed, "state": row.get("state"), "diff_p": row.get("diff_p")})
    return dict(date=iso, ok=True, handed_p=int(row["handed_p"]), handed_to=row["handed_to"], state=row.get("state"),
                diff_p=row.get("diff_p"), expected_p=row.get("expected_p"), typed_by=typed)


@bp.route("/finance/darpan/kal/api/log", methods=["POST"])
def api_log():
    """{date, amount_p?, party?} for one day, or {dates:[...], as_expected:true, party?} for
    many.  A recipient logs only to herself; the owner may name either doctor."""
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("owner", "recipient"):
        return jsonify(ok=False, error="doctors_only"), 403
    b = request.get_json(silent=True) or {}
    party = str(b.get("party") or "").strip() or (who[1] or "dr_manoj")
    if who[0] == "recipient":
        party = who[1]
    if party not in PARTIES:
        return jsonify(ok=False, error="bad_party", parties=list(PARTIES)), 400
    dates = b.get("dates") if isinstance(b.get("dates"), list) else [b.get("date")]
    dates = [str(d or "").strip() for d in dates]
    if not dates or not all(_valid_date(d) for d in dates):
        return jsonify(ok=False, error="bad_date"), 400
    amount_p = None
    if len(dates) == 1 and b.get("amount_p") is not None:
        try:
            amount_p = int(b.get("amount_p"))
        except (TypeError, ValueError):
            return jsonify(ok=False, error="bad_amount"), 400
    results = [_log_one(con, u, who, d, amount_p, party) for d in dates]
    con.commit()
    return jsonify(ok=all(r["ok"] for r in results), party=party, results=results,
                   logged=sum(1 for r in results if r["ok"]))


# ------------------------------------------------------------------ the month (S359)
@bp.route("/finance/darpan/kal/month")
def page_month():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("owner", "recipient"):
        return jsonify(ok=False, error="doctors_only"), 403
    return send_file(MONTH_PAGE)


def _month_rows(con):
    """S362: the month table from the one calculation (sanjeevni_cash.month_rows) -- sale, UPI,
    cash, home, procedure, other, paid elsewhere, cash income -- with the handovers from BOTH
    registers after the counted anchor. The S359 arithmetic below stays as the fallback."""
    try:
        import sanjeevni_cash as _sjc
        a = _sjc.anchor(con, _unit)
    except Exception:                                      # noqa: BLE001
        _sjc, a = None, None
    if not a:
        return _month_rows_s359(con)
    old = {m["ym"]: m for m in _month_rows_s359(con)}
    hand = _sjc.month_moves(con, _unit)           # S363: every handover once, approved days to the pool, deposits
    out = []
    for m in _sjc.month_rows(con, _unit):
        o = old.get(m["ym"], {})
        r = dict(m, expense_p=o.get("expense_p", 0), adjust_p=o.get("adjust_p", 0), back_p=o.get("back_p", 0))
        r["net_cash_p"] = m["cash_income_p"] + r["adjust_p"]
        for k in ("to_manoj_p", "to_bhawna_p", "to_pool_p", "to_bank_p", "to_other_p"):
            r[k] = (hand.get(m["ym"], {}).get(k, 0) + (o.get(k, 0) if m["ym"] < a["anchor_date"][:7] else 0)
                    + (_pre_anchor_moves(con, m["ym"], a, k) if m["ym"] == a["anchor_date"][:7] else 0))
        r["handed_p"] = r["to_manoj_p"] + r["to_bhawna_p"] + r["to_pool_p"] + r["to_bank_p"] + r["to_other_p"]
        out.append(r)
    return out


def _pre_anchor_moves(con, ym, a, key):
    """In the anchor's own month: cash_movement handovers dated before the anchor day."""
    party = {"to_manoj_p": "dr_manoj", "to_bhawna_p": "dr_bhawna", "to_bank_p": "bank"}.get(key)
    q = ("SELECT COALESCE(SUM(m.amount_p),0) FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id "
         "WHERE e.unit=? AND m.direction='out' AND e.business_date LIKE ? AND e.business_date < ? ")
    if party:
        return int(con.execute(q + "AND m.party=?", (_unit, ym + "%", a["anchor_date"], party)).fetchone()[0])
    return int(con.execute(q + "AND m.party NOT IN ('dr_manoj','dr_bhawna','bank')",
                           (_unit, ym + "%", a["anchor_date"])).fetchone()[0])


def _month_rows_s359(con):
    """Per month: total sale, UPI, cash, less home / procedure / other, +/- adjustment,
    = net cash; handed to each doctor and to the bank; expenses.  All from the day books."""
    rows = {}
    for r in con.execute("SELECT substr(business_date,1,7) ym, SUM(revenue_p) sale, SUM(upi_in_p) upi, SUM(cash_in_p) cash, "
                         "SUM(expense_p) expense, SUM(adjust_p) adjust, COUNT(*) days FROM v_day_cash WHERE unit=? "
                         "GROUP BY ym ORDER BY ym", (_unit,)):
        rows[r["ym"]] = dict(ym=r["ym"], days=r["days"], sale_p=int(r["sale"] or 0), upi_p=int(r["upi"] or 0),
                             cash_p=int(r["cash"] or 0), expense_p=int(r["expense"] or 0), adjust_p=int(r["adjust"] or 0),
                             home_p=0, proc_p=0, other_p=0, to_manoj_p=0, to_bhawna_p=0, to_bank_p=0, to_other_p=0, back_p=0)
    for r in con.execute("SELECT substr(e.business_date,1,7) ym, b.head, SUM(b.amount_p) a FROM day_noncash_bill b "
                         "JOIN day_entry e ON e.id=b.day_entry_id WHERE b.unit=? GROUP BY ym, b.head", (_unit,)):
        if r["ym"] in rows:
            key = {"home_medicine": "home_p", "procedure_medicine": "proc_p"}.get(r["head"], "other_p")
            rows[r["ym"]][key] += int(r["a"] or 0)
    for r in con.execute("SELECT substr(e.business_date,1,7) ym, m.direction, m.party, SUM(m.amount_p) a FROM cash_movement m "
                         "JOIN day_entry e ON e.id=m.day_entry_id WHERE e.unit=? GROUP BY ym, m.direction, m.party", (_unit,)):
        if r["ym"] not in rows:
            continue
        if r["direction"] == "in":
            rows[r["ym"]]["back_p"] += int(r["a"] or 0)
        else:
            key = {"dr_manoj": "to_manoj_p", "dr_bhawna": "to_bhawna_p", "bank": "to_bank_p"}.get(r["party"], "to_other_p")
            rows[r["ym"]][key] += int(r["a"] or 0)
    for m in rows.values():
        m["net_cash_p"] = m["cash_p"] - m["home_p"] - m["proc_p"] - m["other_p"] + m["adjust_p"]
        m["handed_p"] = m["to_manoj_p"] + m["to_bhawna_p"] + m["to_bank_p"] + m["to_other_p"]
    return [rows[k] for k in sorted(rows)]


def _month_days(con, ym):
    """S362: a day's handover from the one calculation's cover records when it has one
    (so August reads handed, not '--'); else Darpan's / the doctors' kal row as before."""
    out = _month_days_s359(con, ym)
    if not _has(con, "cash_handover_cover"):
        return out
    rul = {}
    if _has(con, "cash_bill_ruling"):
        for d, amt in con.execute("SELECT business_date, SUM(amount_p) FROM cash_bill_ruling WHERE unit=? "
                                  "AND business_date LIKE ? GROUP BY business_date", (_unit, ym + "%")):
            rul[d] = int(amt or 0)
    cov = {}
    for d, src, hid, amt in con.execute("SELECT covers_date, handover_src, handover_id, amount_p FROM cash_handover_cover "
                                        "WHERE unit=? AND covers_date LIKE ?", (_unit, ym + "%")):
        if src == "movement":
            t = con.execute("SELECT party FROM cash_movement WHERE id=?", (hid,)).fetchone()
        else:
            t = con.execute("SELECT to_party FROM cash_custody_event WHERE id=?", (hid,)).fetchone()
        c = cov.setdefault(d, dict(p=0, to=set()))
        c["p"] += int(amt or 0)
        if t:
            c["to"].add(t[0])
    for x in out:
        x["received_elsewhere_p"] = rul.get(x["date"], 0)
        x["other_p"] -= x["received_elsewhere_p"]
        x["net_cash_p"] += x["received_elsewhere_p"]
        if x.get("handed_p") is None and x["date"] not in cov and x.get("status") in ("approved", "locked") \
                and x["date"] >= _anchor_date(con):
            x["handed_p"], x["handed_to"], x["received"] = x["net_cash_p"], "pool", True   # S363
        c = cov.get(x["date"])
        if c and x.get("handed_p") is None:
            x["handed_p"] = c["p"]
            x["handed_to"] = sorted(c["to"])[0] if len(c["to"]) == 1 else "split"
            x["handed_split"] = sorted(c["to"])
            x["received"] = True
    return out


def _anchor_date(con):
    """S363: the counted anchor's date, or a date nothing reaches when there is none."""
    if not _has(con, "cash_anchor"):
        return "9999-12-31"
    r = con.execute("SELECT MAX(anchor_date) FROM cash_anchor WHERE unit=?", (_unit,)).fetchone()
    return r[0] or "9999-12-31"


def _month_days_s359(con, ym):
    out = []
    handed = {r["business_date"]: dict(r) for r in con.execute(
        "SELECT business_date, handed_p, handed_to, received_at, state FROM darpan_kal_day WHERE unit=? AND business_date LIKE ?",
        (_unit, ym + "%"))}
    for r in con.execute("SELECT d.business_date, d.revenue_p, d.upi_in_p, d.cash_in_p, d.noncash_p, d.adjust_p, d.expense_p, "
                         "d.cash_out_p, e.status FROM v_day_cash d JOIN day_entry e ON e.id=d.day_entry_id "
                         "WHERE d.unit=? AND d.business_date LIKE ? ORDER BY d.business_date", (_unit, ym + "%")):
        iso = r["business_date"]
        heads = {"home_medicine": 0, "procedure_medicine": 0, "other": 0}
        for b in con.execute("SELECT b.head, SUM(b.amount_p) a FROM day_noncash_bill b JOIN day_entry e ON e.id=b.day_entry_id "
                             "WHERE e.unit=? AND e.business_date=? GROUP BY b.head", (_unit, iso)):
            heads[b["head"]] = int(b["a"] or 0)
        h = handed.get(iso) or {}
        out.append(dict(date=iso, status=r["status"], sale_p=int(r["revenue_p"] or 0), upi_p=int(r["upi_in_p"] or 0),
                        cash_p=int(r["cash_in_p"] or 0), home_p=heads["home_medicine"], proc_p=heads["procedure_medicine"],
                        other_p=heads["other"], adjust_p=int(r["adjust_p"] or 0),
                        net_cash_p=int(r["cash_in_p"] or 0) - int(r["noncash_p"] or 0) + int(r["adjust_p"] or 0),
                        handed_p=h.get("handed_p"), handed_to=h.get("handed_to"), received=bool(h.get("received_at")),
                        state=h.get("state")))
    return out


@bp.route("/finance/darpan/kal/api/month")
def api_month():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("owner", "recipient"):
        return jsonify(ok=False, error="doctors_only"), 403
    months = _month_rows(con)
    ym = str(request.args.get("ym") or "").strip()
    if not re.match(r"^\d{4}-\d{2}$", ym):
        ym = months[-1]["ym"] if months else dt.date.today().strftime("%Y-%m")
    return jsonify(ok=True, months=months, ym=ym, days=_month_days(con, ym))


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
    pos = _s496_owner(con, u, items)               # S496: POS totals waiting for his Confirm go to the TOP of the card
    con.commit()
    stats = con.execute("SELECT COUNT(*) n, SUM(state='complete') c, SUM(state='explained') e, "
                        "SUM(state='needs_owner') o FROM darpan_kal_day WHERE unit=? AND business_date>=? "
                        "AND handed_p IS NOT NULL", (_unit, since)).fetchone()
    return jsonify(ok=True, since=since, items=items, count=sum(1 for i in items if not i.get("amber")),
                   amber=len(unrec), owed_p=sum(o["amount_p"] for o in owed), pos=pos,
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


# ---- S446_AMIR_STAGES_BILLS (02-Oct-2026, D648): Amir's supplier claims reach Darpan -------------------------------------------------
# amir_claim (amir_day.py) is Darpan's queue -- "he raises a claim; he never chases one; chasing is Darpan's queue" -- yet no page
# Darpan opens read it (S444's duty map, finding 1). Kal ka hisaab now lists every open claim: supplier, bill, amount, raised when,
# with two taps and nothing to type: "Supplier se baat ho gayi" (state contacted) and "Credit / maal mil gaya" (settled).
S446_CLAIM_REASON_HI = {"short": "Kam maal aaya", "nodeal": "Deal nahi mili", "discount": "Discount kam", "other": "Aur koi baat"}
S446_CLAIM_ANSWERS = ("baat_hui", "mil_gaya")


def _s446_claims(con):
    try:
        if not _has(con, "amir_claim"):
            return []
        out = []
        for r in con.execute("SELECT id, supplier, bill_no, bill_date, amount_p, reason, raised_by, raised_at, state, contacted_note "
                             "FROM amir_claim WHERE state <> 'settled' ORDER BY raised_at, id").fetchall():
            out.append(dict(id=r[0], supplier=r[1] or "", bill_no=r[2] or "", bill_date=r[3] or "", amount_p=r[4], reason=r[5] or "",
                            reason_hi=S446_CLAIM_REASON_HI.get(r[5] or "", r[5] or ""), raised_by=r[6] or "", raised_at=(r[7] or "")[:16],
                            state=r[8] or "open", contacted=r[9] or ""))
        return out
    except Exception:                                          # noqa: BLE001
        return []


@bp.route("/finance/darpan/kal/api/claim-answer", methods=["POST"])
def api_s446_claim_answer():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    b = request.get_json(silent=True) or {}
    try:
        cid = int(b.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ans = str(b.get("answer") or "").strip()
    if ans not in S446_CLAIM_ANSWERS:
        return jsonify(ok=False, error="bad_request", answers=list(S446_CLAIM_ANSWERS)), 400
    if not _has(con, "amir_claim"):
        return jsonify(ok=False, error="not_found"), 404
    r = con.execute("SELECT state FROM amir_claim WHERE id=?", (cid,)).fetchone()
    if r is None:
        return jsonify(ok=False, error="not_found"), 404
    if r[0] == "settled":
        return jsonify(ok=False, error="already_settled", message="Yeh claim pehle hi band ho chuka hai."), 409
    if ans == "baat_hui":
        con.execute("UPDATE amir_claim SET state='contacted', contacted_note=? WHERE id=?",
                    ("%s: supplier se baat ho gayi (%s)" % (u["user"], now_iso()[:16]), cid))
    else:
        con.execute("UPDATE amir_claim SET state='settled', settled_outcome='darpan_received', settled_at=?, settled_by=? WHERE id=?",
                    (now_iso(), u["user"], cid))
    _audit(con, u["user"], "amir_claim_answer", {"id": cid, "answer": ans, "kit": "S446"})
    con.commit()
    return jsonify(ok=True, id=cid, answer=ans)
# ---- S446_AMIR_STAGES_BILLS end ----


# ------------------------------------------------------------------ S454 (D666): the order sheet on Darpan's card
def _s454_sheet_safe(con):
    """'Order sheet': when the newest came, how many medicines and suppliers, that it has reached reception -- or that the newest file was
    refused. Read from order_sheet in-process; never breaks the page."""
    try:
        import order_sheet                                   # noqa: PLC0415
        return order_sheet.darpan_card(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, error=str(e)[:80])


# ---- S485_DARPAN_ORDER_TAB (05-Oct-2026, D677): "आज का ऑर्डर" -- Darpan reviews the system's order list on his own page ------------------
# The engine's list (order_proposal, prepared 09:00 by order_rules.tick) was shown to nobody while Darpan's Marg sheet decided the order.
# On order.source = darpan it opens on this page's second tab from order.darpan_list_time (09:30); he holds a line, adds a medicine,
# changes a quantity and taps Pakka per supplier -- nothing typed but three letters of a name. A Pakka'd supplier (status darpan_ok)
# is what reception's "Order karna hai" cards show; everything after that is S454's, untouched. Nothing new is computed here: the lines
# are the engine's; a held line carries held=true and an added one added=true in the proposal's own `lines`; every tap is one row of
# order_darpan_edit. The tab fetches this API by itself -- the page's own day payload is not changed, and a failure here never breaks
# कल का हिसाब. On any other order.source the list is shown read-only and no tap is taken.
S485_ACTIONS = ("hold", "unhold", "qty", "add", "pakka")
S485_SHOWN = ("open", "darpan_ok", "sent")
_S485_INPUTS = {"key": None, "val": None}


def _s485_or():
    import order_rules                                       # noqa: PLC0415
    return order_rules


def _s485_source(con):
    try:
        import order_sheet                                   # noqa: PLC0415
        return order_sheet.source(con)
    except Exception:                                        # noqa: BLE001
        return "marg_sheet"


def _s485_hhmm(ts):
    s = str(ts or "")
    return s[11:16] if len(s) >= 16 else ""


def _s485_unit(l):
    return "strip" if str(l.get("unit") or "").startswith("strip") else "unit"


def _s485_shelf(l):
    """The shelf as Marg says it: strips:tabs for a strip item (236 of 1*10 -> '23:6'), the plain count otherwise; '' when not known."""
    try:
        oh = int(round(float(l.get("on_hand"))))
    except (TypeError, ValueError):
        return ""
    ps = int(l.get("pack_size") or 1)
    if _s485_unit(l) == "strip" and ps > 1:
        return "%d:%d" % (oh // ps, oh % ps) if oh >= 0 else str(oh)
    return str(oh)


def _s485_days_left(l):
    """About how many days the shelf lasts at the line's own pace (on_hand / per_day); None when there is no pace."""
    try:
        oh, pd = float(l.get("on_hand")), float(l.get("per_day"))
    except (TypeError, ValueError):
        return None
    if oh <= 0:
        return 0
    return int(round(oh / pd)) if pd > 0 else None


def _s485_line(pid, l):
    return dict(pid=pid, item=l.get("item") or "", packing=l.get("packing") or "", unit=_s485_unit(l), qty=int(l.get("qty") or 0),
                on_hand_text=_s485_shelf(l), cover_days=l.get("cover_days"), days_left=_s485_days_left(l),
                held=bool(l.get("held")), added=bool(l.get("added")), why=list(l.get("why") or []))


def _s485_rows(con, day, statuses=S485_SHOWN):
    out = []
    for p in con.execute("SELECT * FROM order_proposal WHERE day=? AND status IN (%s) ORDER BY vendor, kind DESC, id" % ",".join("?" * len(statuses)),
                         (day,) + tuple(statuses)).fetchall():
        p = dict(p)
        try:
            p["lines"] = json.loads(p["lines"] or "[]")
        except ValueError:
            p["lines"] = []
        out.append(p)
    return out


def _s485_pakka_at(con, day, sn):
    r = con.execute("SELECT at FROM order_darpan_edit WHERE day=? AND supplier_norm=? AND action='pakka' ORDER BY id DESC LIMIT 1", (day, sn)).fetchone()
    return r[0] if r else ""


def _s485_yesterday(con, today):
    """The previous order day's suppliers and what reception did: ordered (when), arrived or not; a Pakka'd supplier still not ordered."""
    t = today.isoformat()
    days = [r[0] for r in con.execute("SELECT MAX(substr(created_at,1,10)) FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') "
                                      "AND substr(created_at,1,10) < ?", (t,)) if r[0]] if _has(con, "purchase_order") else []
    days += [r[0] for r in con.execute("SELECT MAX(day) FROM order_darpan_edit WHERE action='pakka' AND day < ?", (t,)) if r[0]]
    if not days:
        return "", []
    d = max(days)
    OR = _s485_or()
    out, seen = [], set()
    if _has(con, "purchase_order"):
        for o in con.execute("SELECT vendor, supplier_norm, status, created_at, received_at FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') "
                             "AND substr(created_at,1,10)=? ORDER BY vendor, id", (d,)).fetchall():
            sn = o[1] or o[0]
            if sn in seen:
                continue
            seen.add(sn)
            out.append(dict(display=OR._short(o[0]), vendor=o[0], state="arrived" if o[2] == "received" else "ordered", at=_s485_hhmm(o[3])))
    for r in con.execute("SELECT DISTINCT p.supplier_norm, p.vendor FROM order_proposal p JOIN order_darpan_edit e ON e.day=p.day AND e.supplier_norm=p.supplier_norm "
                         "AND e.action='pakka' WHERE p.day=? AND p.status IN ('darpan_ok','merged') ORDER BY p.vendor", (d,)).fetchall():
        if r[0] in seen:
            continue
        seen.add(r[0])
        called = False
        try:
            called = bool(con.execute("SELECT 1 FROM purchase_audit WHERE action='s454_call' AND ref=? AND substr(at,1,10)=? LIMIT 1", (r[0], d)).fetchone())
        except sqlite3.Error:
            called = False
        out.append(dict(display=OR._short(r[1]), vendor=r[1], state="no_answer" if called else "not_ordered", at=""))
    return d, out


def _s485_payload(con, who):
    OR = _s485_or()
    today = OR._today()
    day = today.isoformat()
    src = _s485_source(con)
    lt = OR.darpan_list_time(con)
    opened = OR.darpan_list_open(con)
    frozen = bool(OR._frozen(con))
    by, order = {}, []
    if opened and not frozen:
        for p in _s485_rows(con, day):
            r = OR.rule_for(con, p["supplier_norm"])
            if int(r.get("paused") or 0):
                continue
            b = by.get(p["supplier_norm"])
            if b is None:
                b = by[p["supplier_norm"]] = dict(supplier_norm=p["supplier_norm"], vendor=p["vendor"], display=OR._short(p["vendor"]),
                                                  order_day=bool(OR.is_order_day(con, r, today)), status=p["status"], pakka_at="", sent_at="", lines=[])
                order.append(b)
            if p["status"] == "open":
                b["status"] = "open"                           # one of its rows still waits for him: the block is open
            elif p["status"] == "darpan_ok" and b["status"] == "sent":
                b["status"] = "darpan_ok"
            if p["status"] == "sent":
                b["sent_at"] = _s485_hhmm(p.get("sent_at"))
            b["lines"].extend(_s485_line(p["id"], l) for l in p["lines"])
        for b in order:
            b["pakka_at"] = _s485_hhmm(_s485_pakka_at(con, day, b["supplier_norm"]))
            b["n"] = sum(1 for l in b["lines"] if not l["held"])
    yd, ylist = _s485_yesterday(con, today)
    live = [l for b in order for l in b["lines"] if not l["held"]]
    return dict(ok=True, date=day, list_time=lt, opened=opened, source=src, frozen=frozen, me=who[0],
                editable=bool(src == "darpan" and who[0] in ("staff", "owner") and opened and not frozen),
                suppliers=order, n_suppliers=len(order), n_lines=len(live), order_day_names=[b["display"] for b in order if b["order_day"]],
                all_pakka=bool(order) and all(b["status"] != "open" for b in order), yesterday_date=yd, yesterday=ylist)


def _s485_edit(con, day, sn, item, action, qty, by):
    con.execute("INSERT INTO order_darpan_edit (day, supplier_norm, item, action, qty, at, by) VALUES (?,?,?,?,?,?,?)",
                (day, sn, item or "", action, qty, now_iso(), by or ""))


def _s485_gate():
    """(u, con, who, OR, err) for a tap: the page's own door; staff or owner; the list is Darpan's only on order.source = darpan, after
    its time, and while medicine ordering is not frozen."""
    u, con, who, err = _auth()
    if err:
        return None, None, None, None, err
    if who[0] not in ("staff", "owner"):
        return None, None, None, None, (jsonify(ok=False, error="not_permitted"), 403)
    OR = _s485_or()
    if _s485_source(con) != "darpan":
        return None, None, None, None, (jsonify(ok=False, error="not_darpan", message="अभी मार्ग की शीट से ऑर्डर हो रहा है"), 409)
    if OR._frozen(con):
        return None, None, None, None, (jsonify(ok=False, error="frozen", message="दवा का ऑर्डर अभी बंद है"), 423)
    if not OR.darpan_list_open(con):
        return None, None, None, None, (jsonify(ok=False, error="not_open", message="आज की सूची %s बजे आएगी।" % OR.darpan_list_time(con).lstrip("0")), 409)
    return u, con, who, OR, None


def _s485_find(con, day, pid, item):
    """(proposal row as dict with parsed lines, the line) of an OPEN proposal of today -- else (None, None)."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None, None
    p = con.execute("SELECT * FROM order_proposal WHERE id=? AND day=? AND status='open'", (pid, day)).fetchone()
    if not p:
        return None, None
    p = dict(p)
    try:
        p["lines"] = json.loads(p["lines"] or "[]")
    except ValueError:
        p["lines"] = []
    return p, next((l for l in p["lines"] if l.get("item") == item), None)


def _s485_save(con, p):
    total = sum(int(l.get("value_p") or 0) for l in p["lines"] if not l.get("held"))
    con.execute("UPDATE order_proposal SET lines=?, total_p=? WHERE id=?", (json.dumps(p["lines"], ensure_ascii=False), total, p["id"]))


def _s485_step(l, up):
    """− / + : 10 strips at 20 or more, else 5; 1 for a unit item; never below one step."""
    q = int(l.get("qty") or 0)
    if _s485_unit(l) != "strip":
        return max(1, q + (1 if up else -1))
    step = 10 if q >= 20 else 5
    return max(5, q + (step if up else -step))


@bp.route("/finance/darpan/kal/api/order")
def api_s485_order():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):                     # a cash recipient's view of this page has no order tab
        return jsonify(ok=False, error="not_permitted"), 403
    return jsonify(**_s485_payload(con, who))


@bp.route("/finance/darpan/kal/api/order/hold", methods=["POST"])
def api_s485_hold():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    day = OR._today().isoformat()
    item = str(b.get("item") or "")
    p, l = _s485_find(con, day, b.get("pid"), item)
    if not l:
        return jsonify(ok=False, error="gone", message="यह लाइन अब सूची में नहीं है।"), 409
    hold = bool(b.get("hold"))
    if hold:
        l["held"] = True
    else:
        l.pop("held", None)
    _s485_save(con, p)
    _s485_edit(con, day, p["supplier_norm"], item, "hold" if hold else "unhold", int(l.get("qty") or 0), u["user"])
    con.commit()
    return jsonify(**_s485_payload(con, who))


@bp.route("/finance/darpan/kal/api/order/qty", methods=["POST"])
def api_s485_qty():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    day = OR._today().isoformat()
    item = str(b.get("item") or "")
    p, l = _s485_find(con, day, b.get("pid"), item)
    if not l or l.get("held"):
        return jsonify(ok=False, error="gone", message="यह लाइन अब सूची में नहीं है।"), 409
    try:
        up = int(b.get("dir") or 0) > 0
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    q = _s485_step(l, up)
    l.setdefault("qty_engine", int(l.get("qty") or 0))         # the engine's own figure, kept beside his
    l["qty"] = q
    l["value_p"] = int(q * int(l.get("rate_p") or 0))
    _s485_save(con, p)
    _s485_edit(con, day, p["supplier_norm"], item, "qty", q, u["user"])
    con.commit()
    return jsonify(**_s485_payload(con, who))


def _s485_inputs(con, OR, today):
    """The engine's own inputs (order_rules._s470_inputs: the spine's purchase lines, the snapshot, the pace), kept two minutes."""
    import time                                              # noqa: PLC0415
    key = (today.isoformat(), int(time.time() // 120))
    if _S485_INPUTS["key"] != key:
        _S485_INPUTS["val"] = OR._s470_inputs(con, today)
        _S485_INPUTS["key"] = key
    return _S485_INPUTS["val"]


def _s485_known(con, OR, today, item):
    """What the engine knows of one item of Marg's list: (snapshot row, purchase facts or None, pace or None) -- (None, None, None) when
    the item is not in the newest stock list."""
    pa = OR._pa()
    k = pa.norm(item)
    try:
        _as_on, snap, pace, purch, _transit, _ortho = _s485_inputs(con, OR, today)
        s = snap.get(k)
        if s and s.get("item") == item:
            return s, purch.get(k), pace.get(k)
    except Exception:                                        # noqa: BLE001 -- the spine could not be read: Marg's list alone
        pass
    _a, snap2 = pa._latest_snapshot(con)
    s = snap2.get(k)
    if s and s.get("item") == item:
        return dict(item=s["item"], qty=s.get("qty"), packing=s.get("packing") or "", pack_size=max(1, int(s.get("pack_size") or OR._s470_pack(s.get("packing"))))), None, None
    return None, None, None


def _s485_usual(s, e):
    """(strip?, quantity) an added line starts with: the usual lot (in units) / pack size, rounded up to a strip -- or 10 strips / 1."""
    ps = max(1, int(s.get("pack_size") or 1))
    strip = ps > 1
    lot = (e or {}).get("lot")
    if lot:
        import math                                          # noqa: PLC0415
        return strip, max(1, int(math.ceil(float(lot) / ps)))
    return strip, (10 if strip else 1)


def _s485_chips(con, OR, day):
    """The suppliers Darpan may tap: those with a proposal today, then the other suppliers that have a rule, by name."""
    out, seen = [], set()
    for p in _s485_rows(con, day):
        if p["supplier_norm"] not in seen:
            seen.add(p["supplier_norm"])
            out.append(dict(supplier_norm=p["supplier_norm"], display=OR._short(p["vendor"]), today=True))
    for r in con.execute("SELECT supplier_norm, supplier FROM order_supplier_rule WHERE COALESCE(paused,0)=0 ORDER BY supplier_norm").fetchall():
        if r[0] not in seen and r[0] != OR._ortho_norm(con):
            seen.add(r[0])
            out.append(dict(supplier_norm=r[0], display=OR._short(r[1] or r[0]), today=False))
    return out


@bp.route("/finance/darpan/kal/api/order/items")
def api_s485_items():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    OR = _s485_or()
    q = str(request.args.get("q") or "").strip()
    today = OR._today()
    hits = []
    if len(q) >= 3:
        for h in OR.item_names(con, q):
            s, e, _p = _s485_known(con, OR, today, h["item"])
            strip, qty = _s485_usual(s or dict(pack_size=OR._s470_pack(h.get("packing"))), e)
            hits.append(dict(item=h["item"], packing=h.get("packing") or "", supplier_norm=(e or {}).get("vendor") or "",
                             supplier=OR._short((e or {}).get("vendor_disp") or (e or {}).get("vendor") or "") if (e or {}).get("vendor") else "",
                             unit="strip" if strip else "unit", qty=qty, usual=bool((e or {}).get("lot"))))
    return jsonify(ok=True, q=q, hits=hits, chips=_s485_chips(con, OR, today.isoformat()))


@bp.route("/finance/darpan/kal/api/order/add", methods=["POST"])
def api_s485_add():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    today = OR._today()
    day = today.isoformat()
    item = str(b.get("item") or "").strip()
    s, e, pace = _s485_known(con, OR, today, item)
    if not s:
        return jsonify(ok=False, error="unknown_item", message="यह नाम मार्ग की सूची में नहीं मिला।"), 404
    sn = (e or {}).get("vendor") or ""
    vendor = (e or {}).get("vendor_disp") or sn
    if not sn:                                               # never bought: the supplier is the one he tapped
        sn = str(b.get("supplier_norm") or "").strip()
        chip = next((c for c in _s485_chips(con, OR, day) if c["supplier_norm"] == sn), None)
        if not chip:
            return jsonify(ok=False, error="need_supplier", message="सप्लायर चुनिए"), 409
        r = con.execute("SELECT vendor FROM order_proposal WHERE day=? AND supplier_norm=? ORDER BY id LIMIT 1", (day, sn)).fetchone()
        r2 = con.execute("SELECT supplier FROM order_supplier_rule WHERE supplier_norm=?", (sn,)).fetchone()
        vendor = (r[0] if r else None) or (r2[0] if r2 and r2[0] else None) or sn
    if int(OR.rule_for(con, sn).get("paused") or 0):
        return jsonify(ok=False, error="paused", message="इस सप्लायर का ऑर्डर अभी रुका हुआ है।"), 409
    rows = [dict(r) for r in con.execute("SELECT * FROM order_proposal WHERE day=? AND supplier_norm=? AND status IN ('open','darpan_ok','sent') ORDER BY id", (day, sn))]
    for r in rows:
        try:
            r["lines"] = json.loads(r["lines"] or "[]")
        except ValueError:
            r["lines"] = []
    if any(l.get("item") == item for r in rows for l in r["lines"]):
        return jsonify(ok=False, error="already", message="यह दवा सूची में पहले से है।"), 409
    strip, qty = _s485_usual(s, e)
    ps = max(1, int(s.get("pack_size") or 1))
    rate_p = int((e or {}).get("rate_p") or 0)
    try:
        on_hand = int(round(float(s.get("qty"))))
    except (TypeError, ValueError):
        on_hand = None
    line = dict(item=item, on_hand=on_hand, qty=qty, unit="strip" if strip else "unit", pack_size=ps, packing=s.get("packing") or "", rate_p=rate_p,
                per_day=(round(float(pace["rate_per_day"]), 2) if pace and pace.get("rate_per_day") is not None else None), cover_after=None, cover_days=None,
                value_p=int(qty * rate_p), confirm=False, why=["Darpan ne joda"], vendor_norm=sn, added=True, lot=(e or {}).get("lot"), free=(e or {}).get("free"))
    tgt = next((r for r in rows if r["status"] == "open"), None)
    if tgt is not None:
        tgt["lines"].append(line)
        _s485_save(con, tgt)
    elif any(r["kind"] == "darpan" for r in rows):
        return jsonify(ok=False, error="closed", message="इस सप्लायर की सूची पक्की हो चुकी है।"), 409
    else:                                                    # no open list for this supplier today: one of his own
        con.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (day, sn, vendor, "darpan", "open", json.dumps([line], ensure_ascii=False), line["value_p"], "Darpan ne joda", now_iso()))
    _s485_edit(con, day, sn, item, "add", qty, u["user"])
    con.commit()
    return jsonify(**dict(_s485_payload(con, who), added=dict(item=item, supplier_norm=sn, qty=qty)))


@bp.route("/finance/darpan/kal/api/order/pakka", methods=["POST"])
def api_s485_pakka():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    day = OR._today().isoformat()
    if not OR._rules_ok(con):
        return jsonify(ok=False, error="rules_pending", message="डॉक्टर साहब के नियम अभी बाकी हैं।"), 403
    rows = [p for p in _s485_rows(con, day, ("open",)) if not int(OR.rule_for(con, p["supplier_norm"]).get("paused") or 0)]
    if not b.get("all"):
        sn = str(b.get("supplier_norm") or "")
        rows = [p for p in rows if p["supplier_norm"] == sn]
    if not rows:
        return jsonify(ok=False, error="nothing", message="पक्का करने को कुछ नहीं है।"), 409
    done = {}
    for p in rows:
        n = con.execute("UPDATE order_proposal SET status='darpan_ok' WHERE id=? AND status='open'", (p["id"],)).rowcount
        if n:
            done[p["supplier_norm"]] = done.get(p["supplier_norm"], 0) + sum(1 for l in p["lines"] if not l.get("held"))
    for sn, n in done.items():
        _s485_edit(con, day, sn, "", "pakka", n, u["user"])
    con.commit()
    return jsonify(**dict(_s485_payload(con, who), pakka=sorted(done)))
# ---- S485_DARPAN_ORDER_TAB end ----------------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------ S496: the POS total, when the bank's statement has not come
# The owner, 07-Oct-2026: "when Darpan posts 'Kal ka hisaab' and the bank's statement for that day is not in, his same
# form offers one optional figure -- yesterday's UPI total, read from the POS machine.  If the bank's statement is in,
# the option is not shown at all."  "A typed figure changes nothing until I confirm it."  The store, the confirmation
# and the rules are bank_standin.py; this file only asks it.  Every read is fail-soft.
S496_MSG = {"bank_in": "Bank ki report aa chuki hai -- ab POS total ki zaroorat nahin.",
            "not_due": "Bank ki report ka time abhi nahin nikla -- abhi kuch likhne ki zaroorat nahin.",
            "already_confirmed": "Is din ka POS total doctor sahab confirm kar chuke hain.",
            "future": "Yeh din abhi poora nahin hua.", "off": "Yeh box abhi band hai.",
            "bad_date": "Tareekh samajh nahin aayi.", "bad_amount": "POS total ka amount samajh nahin aaya."}


def _s496_bs():
    import bank_standin                                          # noqa: PLC0415
    return bank_standin


def _s496_standing(con, iso):
    """The owner-confirmed POS total standing in for the bank on this day, or None."""
    try:
        return _s496_bs().standing(con, _unit, iso)
    except Exception:                                            # noqa: BLE001
        return None


def _s496_changed(con, iso):
    """bank_standin's hook: a figure for this unit started standing, or the bank replaced it."""
    _refresh_if_needed(con, iso)


def _s496_slim(r):
    if r is None:
        return None
    return dict(id=r["id"], amount_p=int(r["amount_p"]), by=r["typed_by"], at=r["typed_at"], note=r.get("note") or "",
                by_owner=bool(r.get("by_owner")), decided_by=r.get("decided_by") or "")


def _s496_day(con, iso):
    """For the page: is the one optional field offered for this day, and what has been typed."""
    try:
        s = _s496_bs().day(con, _unit, iso)
        return dict(ok=True, show=bool(s["show"]), offer=bool(s["offer"]), bank_state=s["state"], expect=s["expect"],
                    typed=_s496_slim(s["typed"]), confirmed=_s496_slim(s["confirmed"]), rejected=_s496_slim(s["rejected"]),
                    never=bool(s["never"]), label=s["label"])
    except Exception as e:                                       # noqa: BLE001
        return dict(ok=False, show=False, offer=False, error=str(e)[:80])


def _s496_owner(con, u, items):
    """Adds this unit's POS-total lines to the owner's card (waiting ones first) and answers what his fold needs."""
    try:
        BS = _s496_bs()
        mine = [dict(it, pos=True) for it in BS.owner_items(con, [_unit])]
        items[0:0] = [i for i in mine if not i.get("amber")]
        items.extend(i for i in mine if i.get("amber"))
        return dict(ok=True, can_act=BS.is_owner(con, u), tolerance_rupees=BS.rupees(BS.tolerance_p(con)).replace(",", ""),
                    expect=BS.expect_text(con), on=BS.is_on(con), yesterday=_yesterday(), label=BS.LABEL_PROV,
                    days=[dict(iso=d, label=BS.human(d)) for d in BS.recent_days()])
    except Exception as e:                                       # noqa: BLE001
        return dict(ok=False, can_act=False, error=str(e)[:80])


@bp.route("/finance/darpan/kal/api/pos-total", methods=["POST"])
def api_s496_pos_total():
    """ONE number: the POS machine's UPI total for a day whose bank statement has not come.  Darpan's figure waits
    for the owner; the owner's own stands at once.  Writes one bank_standin row -- never a money row."""
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip() or _yesterday()
    if not _valid_date(iso):
        return jsonify(ok=False, error="bad_date", message=S496_MSG["bad_date"]), 400
    try:
        amount = int(b.get("amount_p"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount", message=S496_MSG["bad_amount"]), 400
    try:
        BS = _s496_bs()
        ok, code, row = BS.type_figure(con, _unit, iso, amount, u["user"], owner=(who[0] == "owner" and BS.is_owner(con, u)))
    except Exception:                                            # noqa: BLE001
        return jsonify(ok=False, error="standin_unavailable", message="POS total abhi nahin likha ja saka."), 500
    if not ok:
        return jsonify(ok=False, error=code, message=S496_MSG.get(code, "POS total nahin likha gaya.")), 409
    _audit(con, u["user"], "pos_total_" + code, {"date": iso, "amount_p": amount, "id": row["id"]})
    if code == "confirmed":
        _refresh_if_needed(con, iso, u["user"])
    con.commit()
    return jsonify(ok=True, date=iso, state=code, pos_total=_s496_day(con, iso))


@bp.route("/finance/darpan/kal/api/pos-total/decide", methods=["POST"])
def api_s496_decide():
    """The owner's word on one typed figure of this unit: confirm | reject | seen."""
    u, con, who, err = _auth()
    if err:
        return err
    try:
        BS = _s496_bs()
    except Exception:                                            # noqa: BLE001
        return jsonify(ok=False, error="standin_unavailable"), 500
    if who[0] != "owner" or not BS.is_owner(con, u):
        return jsonify(ok=False, error="owner_only", message="Only Dr Manoj's login confirms a POS total."), 403
    b = request.get_json(silent=True) or {}
    word = str(b.get("word") or "").strip()
    ok, code, row = BS.decide(con, b.get("id"), word, u["user"], note=str(b.get("note") or ""), units_allowed=[_unit])
    if not ok:
        return jsonify(ok=False, error=code, message={
            "bank_in": "The bank's statement for that day has arrived in the meantime — its own figure is used; nothing to confirm.",
            "not_waiting": "That line was already answered.", "not_found": "No such line.",
            "not_yours": "That line belongs to another page.", "bad_word": "confirm, reject or seen."}.get(code, code)), 409
    _audit(con, u["user"], "pos_total_" + code, {"id": row["id"], "date": row["business_date"], "amount_p": row["amount_p"]})
    if code == "confirmed":
        _refresh_if_needed(con, row["business_date"], u["user"])
    con.commit()
    return jsonify(ok=True, state=code, date=row["business_date"])


@bp.route("/finance/darpan/kal/api/pos-total/settings", methods=["POST"])
def api_s496_settings():
    """The two settings he changes on screen: the tolerance and the bank's expected arrival time."""
    u, con, who, err = _auth()
    if err:
        return err
    try:
        BS = _s496_bs()
    except Exception:                                            # noqa: BLE001
        return jsonify(ok=False, error="standin_unavailable"), 500
    if who[0] != "owner" or not BS.is_owner(con, u):
        return jsonify(ok=False, error="owner_only", message="Only Dr Manoj's login changes these."), 403
    b = request.get_json(silent=True) or {}
    ok, msg = BS.save_settings(con, b.get("tolerance"), b.get("expect"), None)
    if ok:
        _audit(con, u["user"], "pos_total_settings", {"tolerance": b.get("tolerance"), "expect": b.get("expect")})
        con.commit()
    return jsonify(ok=ok, message=msg), (200 if ok else 400)
